"""Stage09 isolated worker lifecycle tests: no PostgreSQL, GPU or confidential text."""
from __future__ import annotations

import asyncio
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.core.services.text_evaluation.evaluation_worker_service import (
    EvaluationWorkerService, WorkerPolicy, WorkerResult,
    WorkerRetryableError, WorkerTerminalError,
)
from src.infrastructure.models.text_evaluation import CriterionResult
from src.infrastructure.repositories.text_evaluation.evaluation_repository import (
    WorkerEvaluationContext,
)
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.di.inject import resolve
from src.host.evaluation_worker import _load_worker_policy, main


def policy(**updates):
    values = dict(
        lease_seconds=0.3, heartbeat_seconds=0.04,
        execution_timeout_seconds=0.15,
        max_attempts=3, retry_base_seconds=0,
        retry_cap_seconds=0.1, max_inflight=2,
        max_queue_depth=1, poll_seconds=0.01,
        recovery_batch_size=10, drain_seconds=0.1,
    )
    values.update(updates)
    return WorkerPolicy(**values)


class FakeJobs:
    def __init__(self):
        self.claimed = 0
        self.heartbeats = 0
        self.failed = []
        self.recovered = 0
        self.max_jobs = 1
        self.healthy = True

    async def claim_next_async(self, **_):
        if self.claimed >= self.max_jobs:
            return None
        self.claimed += 1
        return SimpleNamespace(
            id=uuid4(), evaluation_id=uuid4(), attempts=self.claimed,
            attempt_token=uuid4(), fencing_generation=self.claimed,
        )

    async def heartbeat_async(self, **_):
        self.heartbeats += 1
        return self.healthy

    async def fail_attempt_async(self, **kwargs):
        self.failed.append(kwargs)
        return True

    async def queue_metrics_async(self, **_):
        return SimpleNamespace(ready=1, delayed=0, processing=0)

    async def recover_expired_async(self, **_):
        self.recovered += 1
        return 0


class FakeEvaluations:
    def __init__(self):
        self.finished = []
        self.lease_ok = True

    async def worker_context_async(self, **kwargs):
        if not self.lease_ok:
            return None
        return WorkerEvaluationContext(
            evaluation_id=uuid4(), job_id=kwargs["job_id"],
            organization_id=kwargs["organization_id"],
            owner_id="synthetic-owner", evaluation_type="speech",
            rubric_version_id=uuid4(), protected_text_ref=uuid4(),
        )

    async def finalize_with_results_async(self, **kwargs):
        self.finished.append(kwargs)
        return True


def encrypted_result(ctx):
    return WorkerResult(
        criterion_results=(CriterionResult(
            evaluation_id=ctx.evaluation_id, organization_id=ctx.organization_id,
            criterion_code="speech_clarity", status="assessed", score=4,
            encrypted_details=b"SYNTHETIC_TEST_ONLY_CIPHERTEXT",
        ),),
        coverage=0.8, model_revision="synthetic-revision",
        prompt_version="synthetic-prompt", result_status="needs_human_review",
    )


def run_once(jobs, evaluations, executor, pol=None):
    async def run():
        return await EvaluationWorkerService(jobs, evaluations).process_once_async(
            organization_id="synthetic-org", worker_id="synthetic-worker",
            policy=pol or policy(), executor=executor,
        )
    return asyncio.run(run())


def test_di_and_host_default_fail_closed_without_model_or_db():
    bootstrap_di()
    assert isinstance(resolve(EvaluationWorkerService), EvaluationWorkerService)
    with pytest.raises(SystemExit, match="WORKER_DISABLED"):
        main()
    with pytest.raises(ValueError, match="WORKER_DISABLED"):
        _load_worker_policy(resolve(__import__(
            "src.infrastructure.utils.config_reader", fromlist=["ConfigReader"],
        ).ConfigReader))


@pytest.mark.parametrize("override", [
    {"lease_seconds": 0}, {"heartbeat_seconds": 0.15},
    {"max_attempts": 0}, {"max_inflight": 0},
    {"max_queue_depth": 0}, {"retry_base_seconds": 4, "retry_cap_seconds": 2},
    {"max_inflight": True}, {"execution_timeout_seconds": float("nan")},
    {"recovery_batch_size": 200},
])
def test_invalid_worker_policy_rejected(override):
    with pytest.raises(ValueError, match="WORKER_POLICY_INVALID"):
        policy(**override)


def test_worker_success_never_publishes_official_score():
    jobs, ev = FakeJobs(), FakeEvaluations()
    async def executor(ctx):
        return encrypted_result(ctx)
    assert run_once(jobs, ev, executor) == "completed_review"
    assert len(ev.finished) == 1
    assert ev.finished[0]["overall_score"] is None
    assert ev.finished[0]["result_status"] == "needs_human_review"
    assert ev.finished[0]["coverage"] == 0.8
    assert not jobs.failed


def test_retryable_failure_is_redacted_and_backoff_is_bounded():
    jobs, ev = FakeJobs(), FakeEvaluations()
    async def executor(_):
        raise WorkerRetryableError("RAW SECRET MUST NEVER BE STORED")
    assert run_once(jobs, ev, executor) == "retry_scheduled"
    assert jobs.failed[0]["error_code"] == "RESOURCE_UNAVAILABLE"
    assert "RAW SECRET" not in str(jobs.failed[0])
    assert jobs.failed[0]["retryable"] is True
    assert policy(retry_base_seconds=3, retry_cap_seconds=5).retry_delay(31) == timedelta(seconds=5)


def test_terminal_poison_and_invalid_completion_are_never_retried():
    jobs, ev = FakeJobs(), FakeEvaluations()
    async def poison(_):
        raise RuntimeError("SYNTHETIC_PRIVATE_TEXT")
    assert run_once(jobs, ev, poison) == "terminal"
    assert jobs.failed[0]["error_code"] == "EXECUTION_FAILED"
    assert jobs.failed[0]["retryable"] is False
    assert "PRIVATE_TEXT" not in str(jobs.failed[0])
    assert not ev.finished

    jobs2, ev2 = FakeJobs(), FakeEvaluations()
    async def malformed(ctx):
        return WorkerResult(
            criterion_results=(CriterionResult(
                evaluation_id=uuid4(), organization_id=ctx.organization_id,
                criterion_code="speech_clarity", status="assessed",
                score=5, encrypted_details=b"SYNTHETIC",
            ),),
            coverage=1, model_revision="synthetic", prompt_version="synthetic",
        )
    assert run_once(jobs2, ev2, malformed) == "terminal"
    assert jobs2.failed[0]["error_code"] == "RESULT_REJECTED"


def test_max_attempts_and_deadline_transition_to_terminal():
    jobs, ev = FakeJobs(), FakeEvaluations()
    async def slow(_):
        await asyncio.sleep(0.08)
    assert run_once(jobs, ev, slow, policy(
        lease_seconds=0.3, heartbeat_seconds=0.02,
        execution_timeout_seconds=0.01, max_attempts=1,
    )) == "terminal"
    assert jobs.failed[0]["error_code"] == "INFERENCE_TIMEOUT"


def test_missing_worker_context_never_invokes_executor():
    jobs, ev = FakeJobs(), FakeEvaluations()
    ev.lease_ok = False
    async def should_not_run(_):
        pytest.fail("Executor must not run with invalid lease context")
    assert run_once(jobs, ev, should_not_run) == "lost_lease"


def test_lost_heartbeat_cancels_executor_without_result_commit():
    jobs, ev = FakeJobs(), FakeEvaluations()
    jobs.healthy = False
    cancelled = []
    async def wait_forever(_):
        try:
            await asyncio.sleep(1)
        finally:
            cancelled.append(True)
    result = run_once(jobs, ev, wait_forever, policy(
        lease_seconds=0.3, heartbeat_seconds=0.02, execution_timeout_seconds=0.2,
    ))
    assert result == "lost_lease"
    assert cancelled and jobs.heartbeats >= 1
    assert not ev.finished


def test_queue_backpressure_and_recovery_policy():
    jobs, ev = FakeJobs(), FakeEvaluations()
    service = EvaluationWorkerService(jobs, ev)
    async def exercise():
        assert not await service.can_accept_async(
            organization_id="synthetic-org", policy=policy(max_queue_depth=1),
        )
        assert await service.can_accept_async(
            organization_id="synthetic-org", policy=policy(max_queue_depth=2),
        )
        assert await service.recover_async(
            organization_id="synthetic-org", policy=policy(),
        ) == 0
    asyncio.run(exercise())
    assert jobs.recovered == 1


def test_cooperative_shutdown_drains_inflight_and_caps_concurrency():
    jobs, ev = FakeJobs(), FakeEvaluations()
    jobs.max_jobs = 3
    stop = asyncio.Event()
    active = [0]
    peak = [0]
    async def executor(ctx):
        active[0] += 1
        peak[0] = max(active[0], peak[0])
        await asyncio.sleep(0.02)
        active[0] -= 1
        if len(ev.finished) >= 1:
            stop.set()
        return encrypted_result(ctx)
    async def run():
        await EvaluationWorkerService(jobs, ev).run_until_stopped_async(
            organization_id="synthetic-org", worker_id="synthetic-main",
            policy=policy(max_inflight=2), executor=executor, stop_event=stop,
        )
    asyncio.run(run())
    assert 1 <= peak[0] <= 2
    assert all(item["overall_score"] is None for item in ev.finished)
