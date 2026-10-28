# Stage09 — Durable Worker Operational / Dead-Letter Runbook

Status: documented-only organizational deployment; Stage09 local synthetic/isolated PG gates passed in [CI 40651492153](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40651492153). This document is NOT authorization to operate the shared Simorgh PostgreSQL or vLLM.

## Enablement and least privilege

1. Stage09 Host entrypoint imports and bootstraps constructor DI, but running python -m src.host.evaluation_worker with default settings fails fast: WORKER_DISABLED. An explicit worker setting alone cannot bypass the missing approved protected-text/KMS executor; the process exits WORKER_SECURE_EXECUTOR_NOT_CONFIGURED. This is intentional until Stage10/11 application wiring is authorized.
2. Obtain written Infrastructure, IAM, Security and Data Steward approval for a scoped, authenticated internal protected-text loader, encryption/serialization of criterion evidence, reference to an approved immutable Rubric snapshot, test-only database and trusted model endpoint. Never use shared Simorgh database as a test sandbox.
3. Configure exactly one organization scope per worker process; require explicit tenant, max attempts, lease/heartbeat interval, max inflight, execution deadline, retry base/cap, max queue depth, poll interval, recovery batch and drain interval. Test bounds in WorkerPolicy. No production capacity/SLO values are hardcoded or preapproved. Use capacity planning from Stage11.
4. Stage05 PsqlDbContext currently only accepts TES_ENVIRONMENT=development and a postgresql+asyncpg loopback DSN whose database starts tes_stage05_. Production use requires a separately approved controlled deployment revision: do NOT remove the guard ad hoc.
5. The optional read-only can_accept_async queue depth is advisory. All Stage10 writes must call atomic create_with_job_async(max_active_jobs=approved_limit) to enforce the org-wide cap with transaction-scoped advisory lock and idempotent replay.
6. No job Session remains open while an authorized executor processes a protected text reference. Results must be ciphertext and scope-verified; Stage09 stores review-only results with overall_score NULL until official scoring policy is signed off.

## Worker states, recovery and poison handling

- Creation: pending Evaluation + pending Job + submission audit in one transaction; same org/owner/idempotency fingerprint replays existing pair.
- Claim: SKIP LOCKED, worker ID, increment attempts/fencing generation, random attempt token, lease deadline committed before inference; per-instance concurrency cap.
- Heartbeat: uses same worker ID + token + generation and valid, unexpired lease. No stale or expired attempt may renew.
- Failure: known retryable inference/network problems and resource exhaustion schedule failed_retryable with bounded exponential delay; invalid result or unknown execution error become failed_terminal. A max-attempt exhausted job becomes failed_terminal. Store only allowlisted error codes, never exception messages or source.
- Crash/restart: expired processing lease selected with SKIP LOCKED and DB time; invalidated token and increased fencing generation, synchronized Evaluation/Job statuses, audited metadata; retry only within max attempts. Attempts exhausted become terminal.
- Completion: fenced short DB transaction creates all encrypted CriterionResult rows, review-only Evaluation status, job completed and audit event atomically. Late/duplicate attempts cannot mutate committed results. No automatic publication of numeric official scores.
- Poison/dead-letter: use existing failed_terminal job with error_code as the initial review queue; no separate queue/table was introduced because the Stage05 schema already supports terminal state. Never auto-replay a poison item. Operator must obtain verified role, preserve immutable case/timestamp/audit and evidence, investigate sanitized error/status, and request authorized manual resubmission rather than directly rewriting protected rows.
- Graceful shutdown: set stop event on SIGTERM/SIGINT; stop claiming, drain bounded inflight tasks; after deadline cancel and let lease expiry recovery occur. DB and provider are closed. Do not kill another worker or reset shared queues.

## Metrics and alert handoff

Existing tenant-scoped QueueMetrics: ready, delayed, processing, expired_leases, terminal, jobs_with_retries and oldest_ready_age_seconds. Worker exposes last_processing_seconds and last_error_code safe status per process. Actual alert thresholds and retention targets are NOT approved; Stage11 SRE must set queue-age, stuck lease, retry-fraction, terminal-rate, p95 processing-duration, pool saturation and GPU admission thresholds based on a measured load profile. Never publish raw prompt/score/evidence, user IDs or access tokens in metrics labels.

## Incident response and rollback

- On abnormal duplicates: block new submissions through approved API admission, capture job IDs/generations and sanitized audit chronology, check active lease ownership, isolate only authorized synthetic accounts, avoid force-resetting production records.
- On persistent DB outage: do not run inference without a valid claim. Poll with bounded rate, emit only static error category. After DB restoration, lease recovery resumes under fencing and max attempts. Escalate observed unbounded queue growth under pre-agreed SRE alerts.
- On model OOM/timeouts: classify bounded retryable if safe; inspect resource metrics with approved operators; no unapproved model/artifact download or external fallback.
- On shutdown: take the worker out of traffic, wait the configured drain window and terminate remaining tasks; other workers recover only after actual DB lease expiration.
- All source modifications and releases follow conventional commits and reviewed migration policies. This document does not authorize database downgrade, force-push, secret rotation or shared network changes.

## Safe local verification

    cd /srv/projects/text-evaluation-service
    git pull --ff-only origin main
    .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage09_worker.py
    .venv/bin/python -m pytest -q -p no:cacheprovider tests --ignore=tests/test_stage05_postgres.py --ignore=tests/test_stage06_rubric_postgres.py --ignore=tests/test_stage09_postgres.py

Enterprise integration/soak: PENDING_SERVER per docs/verification/09_stage09_deferred_stage11_ledger.md.
