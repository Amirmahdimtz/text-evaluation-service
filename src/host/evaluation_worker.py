"""Stage09 worker composition root; no implicit access to confidential text.

Runtime processing requires an explicitly provided approved encrypted-source
executor. Merely running this module cannot access a database or inference.
"""
from __future__ import annotations

import asyncio
import signal
from collections.abc import Awaitable, Callable
from uuid import uuid4

from src.core.services.text_evaluation.evaluation_worker_service import (
    EvaluationWorkerService, JobExecutor, WorkerPolicy,
)
from src.core.services.text_evaluation.protected_evaluation_executor import ProtectedEvaluationExecutor
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.di.inject import resolve
from src.infrastructure.utils.config_reader import ConfigReader
from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext


def _load_worker_policy(config: ConfigReader) -> tuple[str, WorkerPolicy]:
    """Requires explicit measured policy and only development DB isolation."""
    setting = config.settings.worker
    if not setting.enabled:
        raise ValueError("WORKER_DISABLED")
    if config.environment != "development":
        raise ValueError("WORKER_APPROVAL_REQUIRED")
    fields = (
        "lease_seconds", "heartbeat_seconds", "execution_timeout_seconds",
        "max_attempts", "retry_base_seconds", "retry_cap_seconds",
        "max_inflight", "max_queue_depth", "poll_seconds",
        "recovery_batch_size", "drain_seconds",
    )
    if (not setting.organization_id or any(
        getattr(setting, field) is None for field in fields
    )):
        raise ValueError("WORKER_CONFIG_INCOMPLETE")
    policy = WorkerPolicy(**{key: getattr(setting, key) for key in fields})
    return setting.organization_id, policy


async def run_with_approved_executor(executor: JobExecutor) -> None:
    """Valid approved execution adapter must be bound by Stage10/11 deployment."""
    if not callable(executor):
        raise ValueError("WORKER_EXECUTOR_REQUIRED")
    bootstrap_di()
    config = resolve(ConfigReader)
    organization_id, policy = _load_worker_policy(config)
    db = resolve(PsqlDbContext)
    stop = asyncio.Event()
    running_loop = asyncio.get_running_loop()
    for flag in (signal.SIGINT, signal.SIGTERM):
        try:
            running_loop.add_signal_handler(flag, stop.set)
        except (NotImplementedError, RuntimeError):
            pass
    try:
        await resolve(EvaluationWorkerService).run_until_stopped_async(
            organization_id=organization_id,
            worker_id="tes-worker-" + uuid4().hex,
            policy=policy, executor=executor, stop_event=stop,
        )
    finally:
        try:
            if isinstance(executor, ProtectedEvaluationExecutor):
                await executor.aclose()
        finally:
            await db.close()


def main() -> None:
    """No unsecured plaintext resolver, synthetic bypass or automatic download."""
    bootstrap_di()
    config = resolve(ConfigReader)
    if not config.settings.worker.enabled:
        raise SystemExit("WORKER_DISABLED")
    # Only the isolated development database and explicitly enabled internal
    # services may execute. This is not a production deployment entrypoint.
    if (config.environment != "development"
            or not config.settings.http_security.enabled
            or not config.settings.llm.enabled):
        raise SystemExit("WORKER_SECURE_EXECUTOR_NOT_CONFIGURED")
    asyncio.run(run_with_approved_executor(resolve(ProtectedEvaluationExecutor)))


if __name__ == "__main__":
    main()
