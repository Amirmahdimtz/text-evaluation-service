"""Stage09 durable job processing with short fenced PostgreSQL transactions.

Executor is an explicitly authorized per-job callback. In Stage09 the only
exercised executor is synthetic; confidential-text loading/crypto is NOT wired.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import timedelta
from typing import Awaitable, Callable
from uuid import UUID, uuid4

from src.infrastructure.di.inject import inject
from src.infrastructure.providers.llm.local_llm_provider import LlmProviderError
from src.infrastructure.models.text_evaluation import CriterionResult
from src.infrastructure.repositories.text_evaluation.evaluation_job_repository import (
    EvaluationJobRepository, QueueMetrics,
)
from src.infrastructure.repositories.text_evaluation.evaluation_repository import (
    EvaluationRepository, WorkerEvaluationContext,
)


@dataclass(frozen=True)
class WorkerPolicy:
    lease_seconds: float
    heartbeat_seconds: float
    execution_timeout_seconds: float
    max_attempts: int
    retry_base_seconds: float
    retry_cap_seconds: float
    max_inflight: int
    max_queue_depth: int
    poll_seconds: float
    recovery_batch_size: int
    drain_seconds: float

    def __post_init__(self) -> None:
        numbers = (self.lease_seconds, self.heartbeat_seconds,
                   self.execution_timeout_seconds, self.poll_seconds,
                   self.drain_seconds)
        if (any(type(n) not in (int, float) or not 0 < n <= 3600 for n in numbers)
                or self.heartbeat_seconds * 2 >= self.lease_seconds
                or any(type(n) not in (int, float) or not 0 <= n <= 3600 for n in
                       (self.retry_base_seconds, self.retry_cap_seconds))
                or self.retry_cap_seconds < self.retry_base_seconds
                or type(self.max_attempts) is not int or not 1 <= self.max_attempts <= 32767
                or type(self.max_inflight) is not int or not 1 <= self.max_inflight <= 128
                or type(self.max_queue_depth) is not int or not 1 <= self.max_queue_depth <= 100000
                or type(self.recovery_batch_size) is not int or not 1 <= self.recovery_batch_size <= 100):
            raise ValueError("WORKER_POLICY_INVALID")

    def retry_delay(self, attempt: int) -> timedelta:
        if type(attempt) is not int or attempt < 1:
            raise ValueError("WORKER_ATTEMPT_INVALID")
        return timedelta(seconds=min(
            self.retry_cap_seconds,
            self.retry_base_seconds * (2 ** min(attempt - 1, 20)),
        ))


@dataclass(frozen=True)
class WorkerResult:
    """Upstream must supply approved encrypted criterion details, NEVER plaintext."""
    criterion_results: tuple[CriterionResult, ...]
    coverage: float
    model_revision: str
    prompt_version: str
    result_status: str = "needs_human_review"

    def __post_init__(self) -> None:
        if (self.result_status not in ("needs_human_review", "partial")
                or not self.criterion_results
                or type(self.coverage) not in (float, int)
                or not 0 <= self.coverage <= 1
                or not isinstance(self.model_revision, str) or not self.model_revision
                or not isinstance(self.prompt_version, str) or not self.prompt_version):
            raise ValueError("WORKER_RESULT_INVALID")


class WorkerRetryableError(Exception):
    """A safe classification, not source text or underlying provider exception."""


class WorkerTerminalError(Exception):
    """Permanent failure; call with only a static approved error code."""


JobExecutor = Callable[[WorkerEvaluationContext], Awaitable[WorkerResult]]


@inject
class EvaluationWorkerService:
    def __init__(
        self, job_repository: EvaluationJobRepository,
        evaluation_repository: EvaluationRepository,
    ) -> None:
        self._jobs = job_repository
        self._evaluations = evaluation_repository
        self._last_processing_seconds: float | None = None
        self._last_error_code: str | None = None

    @property
    def last_processing_seconds(self) -> float | None:
        return self._last_processing_seconds

    @property
    def last_error_code(self) -> str | None:
        return self._last_error_code

    async def metrics_async(self, *, organization_id: str) -> QueueMetrics:
        return await self._jobs.queue_metrics_async(organization_id=organization_id)

    async def can_accept_async(self, *, organization_id: str, policy: WorkerPolicy) -> bool:
        metrics = await self.metrics_async(organization_id=organization_id)
        return (metrics.ready + metrics.delayed + metrics.processing
                < policy.max_queue_depth)

    async def recover_async(self, *, organization_id: str, policy: WorkerPolicy) -> int:
        return await self._jobs.recover_expired_async(
            organization_id=organization_id, max_attempts=policy.max_attempts,
            retry_delay=policy.retry_delay(1), batch_size=policy.recovery_batch_size,
        )

    async def process_once_async(
        self, *, organization_id: str, worker_id: str,
        policy: WorkerPolicy, executor: JobExecutor,
    ) -> str:
        if (not organization_id or not worker_id or len(worker_id) > 128
                or not isinstance(policy, WorkerPolicy) or not callable(executor)):
            raise ValueError("WORKER_CONFIGURATION_INVALID")
        try:
            job = await self._jobs.claim_next_async(
                organization_id=organization_id, worker_id=worker_id,
                lease_duration=timedelta(seconds=policy.lease_seconds),
                max_attempts=policy.max_attempts,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            self._last_error_code = "WORKER_DATABASE_UNAVAILABLE"
            return "claim_unavailable"
        if job is None:
            return "idle"
        try:
            context = await self._evaluations.worker_context_async(
                organization_id=organization_id, job_id=job.id,
                worker_id=worker_id, attempt_token=job.attempt_token,
                fencing_generation=job.fencing_generation,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            self._last_error_code = "WORKER_DATABASE_UNAVAILABLE"
            # The held lease will expire and be recovered with fencing.
            return "context_unavailable"
        if context is None:
            return "lost_lease"
        stop_heartbeat = asyncio.Event()
        lease_lost = asyncio.Event()
        started = time.monotonic()
        execution = asyncio.create_task(executor(context))

        async def heartbeat() -> None:
            while not stop_heartbeat.is_set():
                try:
                    await asyncio.wait_for(
                        stop_heartbeat.wait(), timeout=policy.heartbeat_seconds,
                    )
                    return
                except asyncio.TimeoutError:
                    pass
                try:
                    alive = await self._jobs.heartbeat_async(
                        organization_id=organization_id, job_id=job.id,
                        worker_id=worker_id, attempt_token=job.attempt_token,
                        fencing_generation=job.fencing_generation,
                        lease_duration=timedelta(seconds=policy.lease_seconds),
                    )
                except asyncio.CancelledError:
                    raise
                except Exception:
                    # Fail closed if database is unreachable; never assume lease.
                    alive = False
                if not alive:
                    lease_lost.set()
                    execution.cancel()
                    return

        monitor = asyncio.create_task(heartbeat())
        try:
            try:
                result = await asyncio.wait_for(
                    execution, timeout=policy.execution_timeout_seconds,
                )
                if lease_lost.is_set():
                    return "lost_lease"
                if not isinstance(result, WorkerResult):
                    raise WorkerTerminalError("RESULT_REJECTED")
                if any(
                    not isinstance(row, CriterionResult)
                    or row.evaluation_id != context.evaluation_id
                    or row.organization_id != organization_id
                    or not row.encrypted_details
                    or row.status not in ("assessed", "not_assessed")
                    or (row.status == "not_assessed" and row.score is not None)
                    for row in result.criterion_results
                ):
                    raise WorkerTerminalError("RESULT_REJECTED")
                # No official score until policy/SME gates pass. Stage05 can
                # persist provisional criterion details in review-only state.
                return "completed_review" if await self._evaluations.finalize_with_results_async(
                    organization_id=organization_id, owner_id=context.owner_id,
                    evaluation_id=context.evaluation_id, job_id=job.id,
                    worker_id=worker_id, attempt_token=job.attempt_token,
                    fencing_generation=job.fencing_generation,
                    results=list(result.criterion_results), overall_score=None,
                    coverage=result.coverage, model_revision=result.model_revision,
                    prompt_version=result.prompt_version,
                    result_status=result.result_status, correlation_id=uuid4(),
                ) else "lost_lease"
            except asyncio.CancelledError:
                if lease_lost.is_set():
                    return "lost_lease"
                raise
            except WorkerTerminalError:
                retryable, error_code = False, "RESULT_REJECTED"
            except (asyncio.TimeoutError, TimeoutError):
                retryable, error_code = True, "INFERENCE_TIMEOUT"
            except LlmProviderError as exc:
                if str(exc) in (
                    "LLM_RETRY_EXHAUSTED", "LLM_CIRCUIT_OPEN",
                    "LLM_ADMISSION_TIMEOUT",
                ):
                    retryable, error_code = True, "INFERENCE_TRANSIENT"
                else:
                    retryable, error_code = False, "INFERENCE_INVALID"
            except (WorkerRetryableError, MemoryError):
                retryable, error_code = True, "RESOURCE_UNAVAILABLE"
            except Exception:
                # Unknown failures may be permanent/security-sensitive.
                # Never retry arbitrary poisoned work indefinitely.
                retryable, error_code = False, "EXECUTION_FAILED"
            try:
                applied = await self._jobs.fail_attempt_async(
                    organization_id=organization_id, job_id=job.id,
                    worker_id=worker_id, attempt_token=job.attempt_token,
                    fencing_generation=job.fencing_generation,
                    max_attempts=policy.max_attempts, retryable=retryable,
                    error_code=error_code, retry_delay=policy.retry_delay(job.attempts),
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                self._last_error_code = "WORKER_DATABASE_UNAVAILABLE"
                return "failure_persist_unavailable"
            return ("retry_scheduled" if retryable and job.attempts < policy.max_attempts
                    else "terminal") if applied else "lost_lease"
        finally:
            self._last_processing_seconds = max(0.0, time.monotonic() - started)
            stop_heartbeat.set()
            if not execution.done():
                execution.cancel()
            if not monitor.done():
                monitor.cancel()
            await asyncio.gather(execution, monitor, return_exceptions=True)

    async def run_until_stopped_async(
        self, *, organization_id: str, worker_id: str, policy: WorkerPolicy,
        executor: JobExecutor, stop_event: asyncio.Event,
    ) -> None:
        """Bounded concurrency, cooperative drain, and lease-expiry crash recovery."""
        if (not isinstance(stop_event, asyncio.Event) or not isinstance(worker_id, str)
                or not 1 <= len(worker_id) <= 112 or not organization_id):
            raise ValueError("WORKER_STOP_EVENT_REQUIRED")
        tasks: set[asyncio.Task] = set()
        try:
            while not stop_event.is_set():
                try:
                    await self.recover_async(organization_id=organization_id, policy=policy)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    self._last_error_code = "WORKER_DATABASE_UNAVAILABLE"
                    try:
                        await asyncio.wait_for(stop_event.wait(), policy.poll_seconds)
                    except asyncio.TimeoutError:
                        pass
                    continue
                finished = {task for task in tasks if task.done()}
                for task in finished:
                    try:
                        task.result()
                    except asyncio.CancelledError:
                        pass
                    except Exception:
                        raise RuntimeError("WORKER_TASK_FAILED") from None
                tasks.difference_update(finished)
                while len(tasks) < policy.max_inflight and not stop_event.is_set():
                    index = len(tasks)
                    task = asyncio.create_task(self.process_once_async(
                        organization_id=organization_id,
                        worker_id=f"{worker_id}-{index}",
                        policy=policy, executor=executor,
                    ))
                    tasks.add(task)
                if tasks:
                    await asyncio.wait(tasks, timeout=policy.poll_seconds,
                                       return_when=asyncio.FIRST_COMPLETED)
                # Throttle empty queue and failure loops; still react promptly
                # to shutdown rather than hammering the database.
                if not stop_event.is_set():
                    try:
                        await asyncio.wait_for(stop_event.wait(), policy.poll_seconds)
                    except asyncio.TimeoutError:
                        pass
        finally:
            if tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=policy.drain_seconds,
                    )
                except asyncio.TimeoutError:
                    for task in tasks:
                        task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
