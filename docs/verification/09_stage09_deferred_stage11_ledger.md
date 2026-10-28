# Stage09 D-017 — Deferred real-server Worker / Queue Acceptance Ledger

All entries below are PENDING_SERVER / DEFERRED_TO_STAGE_11 unless assigned to Stage10 implementation first, NEVER PASSED by in-process simulation. The isolated GitHub Actions PostgreSQL 17 [run 40651492153](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40651492153) already passed mandatory local transactional gates (5 real Stage09 PG tests, 229 total pytest).

| ID | Test owner | Prerequisite | Actual acceptance oracle |
|---|---|---|---|
| S09-S11-01 | DBA + SRE | Authorized organization staging DB and schema/backup policies, test-only org accounts | Crash and multiple independent worker processes recover expired leases; no lost job, duplicate result, stale writer or connection leak over long-lived run |
| S09-S11-02 | AI/MLOps + SRE | Real internal vLLM, GPU capacity and approved synthetic load | Controlled backpressure, token admission, timeout, retry/circuit, max attempts and graceful shutdown measured at actual p95/p99 SLA; no uncontrolled OOM or GPU oversubscription |
| S09-S11-03 | Security + Data Steward + Platform | Approved authenticated protected-text/KMS resolver and scoped service identity integrated in Stage10 | Worker cannot load other tenants' data; all raw text and criterion evidence only handled under approved encrypted memory/storage policy, never in logs, metrics or external services |
| S09-S11-04 | SRE + DBA + Observability | Internal metrics sink, owned on-call alert thresholds and synthetic fault-window authorization | Queue age/depth/retry/stuck/terminal, processing durations/worker liveness meet approved alert and retention policies; poison triage audited with actor authority, no unsafe automatic replay |
| S09-S11-05 | IAM + Security + AI Lead | Approved Stage10 submission API, reviewer policy and signed Rubric | Completed job cannot publish provisional model score; customer authorization, idempotency across replicas and exact immutable rubric/result metadata fully checked end-to-end |
| S09-S11-06 | SRE + Security | Production-representative signed images, service secrets, network No-Egress and failure injection window | Hard worker kill, DB disconnect/reconnect, process restart, cancellation/drain, TLS expiration, model outage and on-prem backup/recovery measured with no data leakage or unbounded duplicate attempts |

The Stage09 local CI does NOT establish a deployed worker, authorized KMS/text resolver, real GPU inference, company IAM/No-Egress, official rubric scoring or business acceptance. D-015 formal organization acceptance deferred to Stage12. Stage10 NOT_STARTED.
