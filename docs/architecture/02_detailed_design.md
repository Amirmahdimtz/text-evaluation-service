# Stage 02 — Detailed Architecture Design

> Status: PROPOSED_DESIGN, not executable implementation | 2026-10-21 | Architecture source: Service_Architecture_Guide_FA.md | Scope: FR-01..FR-12 / NFR-01..NFR-14
>
> تمامی اجزای زیر Target Design هستند. در snapshot مرحله ۲ هیچ‌یک از کلاس‌های Runtime در GitHub تأیید نشدند. قراردادهای OPEN وابسته به تصمیم‌های Stage 01 باقی می‌مانند.

## 1. Architecture and trust boundaries

معماری مرجع بدون لایه‌سازی اضافی:

    Host (app entry, startup, worker entry, process lifecycle)
       → Application (FastAPI WebService, discovery, controllers, Pydantic DTO)
       → Core/services (use-case, rubric, evidence, Python scoring, workflow)
       → Infrastructure (repositories, SQLAlchemy models, PsqlDbContext,
          internal LLM provider, Vault/config, Alembic)

- Dependency direction در workflow از Controller به Service و از Service به Repository/Provider است؛ return data می‌تواند در جهت عکس جریان یابد. مدل persistence در Infrastructure باقی می‌ماند.
- No DDD/CQRS/hexagonal/use-case layer، no per-service interfaces و no manual DI registration؛ concrete constructor injection با @inject.
- سه حوزه speech/media/research از یک Evaluation pipeline نسخه‌دار استفاده می‌کنند؛ منطق اختصاصی از Rubric/criterion rules می‌آید، نه سه fork جداگانه ناهم‌سو.
- API، Worker، PostgreSQL، inference و audit/logs همگی در trust boundary داخلی سازمان اجرا می‌شوند؛ deployment topology فقط پس از OD-13 نهایی می‌شود. مدولار بودن Code به معنی وجود microservice جداگانه نیست.

## 2. Component responsibility map

| Component (proposed) | Layer | Responsibility and invariant |
|---|---|---|
| host/app.py and application/web.py | Host / Application | process startup, bootstrap_di first, discover feature controllers, route prefix; lifespan and sanitized error handlers |
| TextEvaluationController | Application | Auth Context extraction, DTO validation, status codes, HTTP exception mapping, response redaction; no SQL/LLM |
| TextEvaluationService | Core | submit/status/report orchestration; scope checks; rubric selection; idempotency decisions; never call database directly |
| RubricService | Core | resolve published immutable snapshot by domain/authorized scope; validate version and checksum |
| TextPreprocessingService | Core | original-text preservation; Persian normalization with reversible offset map; sections/chunks; long-document synthesis |
| CriterionEvaluationService | Core | build fixed rubric-aware instructions, process untrusted internal inference output, reason/score/evidence checks |
| EvidenceValidationService (only if justified by complexity) | Core | confirm exact spans and authorized reference corpus provenance; otherwise a private helper inside CriterionEvaluationService |
| ScoringService | Core | deterministic Decimal arithmetic, applicability/required/coverage and partial/review policy; no numeric score for empty assessed set |
| EvaluationWorkerService | Core | claim orchestration, execute AI outside transaction, version tracking, retry classification and conditional completion |
| EvaluationRepository | Infrastructure | evaluation CRUD and scoped reads; specialized atomic create-with-job and finalize-with-results writes |
| EvaluationJobRepository | Infrastructure | claim/renew/recover leases; compare-and-swap fencing; queue metrics; bounded transition persistence |
| RubricRepository | Infrastructure | published version retrieval, immutable publication and version lookup |
| Feedback repository (when required) | Infrastructure | append reviewer feedback with original result immutable and safe actor attribution |
| LocalLlmProvider | Infrastructure | ONLY internal endpoint, connection pooling/timeout/cancellation, resource limits and structured parsing; no external provider fallback |
| PsqlDbContext | Infrastructure | singleton engine and async_sessionmaker, transaction contexts, graceful close; per-operation AsyncSession |
| SQLAlchemy Models / Alembic | Infrastructure | scoped persistence, indexes/constraints, schema migrations and metadata registration |
| Audit persistence (approved DB or internal sink) | Infrastructure | append safe metadata events; never original text, prompts, evidence quotes, credentials |

All names are target class/file proposals, not observed source. Separate EvidenceValidationService, FeedbackRepository or AuditRepository must be created only when real responsibilities justify them (matrix labels conditional).

## 3. Dependency graph and DI contract

    TextEvaluationController (@inject)
      └─ TextEvaluationService (@inject)
         ├─ EvaluationRepository (@inject)
         ├─ RubricService (@inject) ─ RubricRepository (@inject)
         └─ (for report/status) EvaluationJobRepository (@inject)

    EvaluationWorkerService (@inject)
      ├─ EvaluationJobRepository (@inject)
      ├─ EvaluationRepository (@inject)
      ├─ TextPreprocessingService (@inject)
      ├─ RubricService (@inject)
      ├─ CriterionEvaluationService (@inject) ─ LocalLlmProvider (@inject)
      └─ ScoringService (@inject)

    Infrastructure repositories (@inject) ─ PsqlDbContext (@inject, singleton)
    PsqlDbContext ─ ConfigReader/VaultService (singleton in reference convention)

Provider discovery is defined by guide: infrastructure → core → application; scan only @inject-marked provider classes; directories di, dtos, models, scripts, alembic, versions, res, sso excluded as described by the reference. Do not register each service by hand. bootstrap_di() must run BEFORE resolve(WebService) or worker-service creation; worker requires an explicit supported composition root, not HTTP server initialization. Actual discovery logic is missing; verification must occur after introducing framework source in Stage 04.

Controller auto-discovery requires src/application/text_evaluation/text_evaluation_controller.py with TextEvaluationController.api() returning APIRouter(prefix="") and route suffixes only; WebService mounts /api/v1/text_evaluation assuming config prefix is /api/v1. Controller must not duplicate text_evaluation. Async methods end in _async. HTTP status/error contracts do not propagate into Core.

Singleton ONLY for safe shared infrastructure services (config, vault, DB factory; HTTP client/provider lifecycle assessed separately). A singleton AsyncSession is forbidden. Discovery must fail visible startup checks if a required module/import is missing; skip-on-import-error is a known risk of the guide implementation, not verified in this repository.

## 4. End-to-end data flow and ownership

    Internal Client
      → internal Gateway / verify AuthN (issuer, signature, audience, expiry)
      → TextEvaluationController (validated input, Idempotency-Key)
      → TextEvaluationService (server-derived principal + org/unit/role)
      → RubricRepository (authorized published version snapshot)
      → EvaluationRepository.create_with_job_async (single DB transaction)
      → HTTP 202 with opaque evaluation_id / job_id
      → EvaluationJobRepository claim (short atomic transaction)
      → EvaluationWorkerService
      → TextPreprocessingService
      → LocalLlmProvider (internal inference only, no DB transaction)
      → schema and Evidence Validation
      → ScoringService (deterministic Python)
      → EvaluationRepository.finalize_with_results_async (fenced single commit)
      → authorized status/report read / feedback / audit

Identity/org scope is obtained ONLY from verified Auth Context. Never copy scope from request payload, arbitrary URL, unverified JWT claims or text itself. Tenant authorization is enforced in Service decisions AND every repository query, update, feedback and idempotency lookup; opaque UUID alone is insufficient. No cross-unit access without explicit delegated scope. Reviewer permissions and 403/404 privacy semantics = OD-07 OPEN; fail-closed now.

Data classification: original text, chunks, derived reasons, model requests/responses, evidence quotes and feedback remain confidential. Encrypt in transit/at rest/backup per approved policy. No external model/API/tool calls or web retrieval. Research external evidence may only use an authorized, version-pinned internal corpus.

## 5. Transaction design: no global session, no engine per request

**Problem:** reference BaseRepository may open+commit one AsyncSession PER method. Sequential insert_async(evaluation), insert_async(job) therefore is NOT an atomic multi-repository workflow. Same for result persistence and completed Job state.

**Conservative proposed solution without modifying BaseRepository:** implement single-purpose persistence methods in EvaluationRepository (not the Service), such as create_with_job_async and finalize_with_results_async. Each owns ONE db_context.session() + explicit session.begin() and performs all related SQLAlchemy writes in one transaction, including Job state, criterion rows and outbox/audit metadata if in same DB. Underlying generic BaseRepository stays for single-entity CRUD only. Do not call its auto-commit CRUD methods from inside the compound transaction.

If code inspection in Stage 05 demonstrates an existing shared transaction API, reuse it. Only if necessary, propose an optional caller-supplied AsyncSession context to BaseRepository methods with no implicit commit for caller-managed sessions; maintain backward compatible operation-local transaction defaults, assert no nested accidental commits and test rollback. This is a conditional proposal, NOT approved modification.

Transaction boundaries:

| Operation | Atomic boundary | Critical constraints |
|---|---|---|
| submit | lock/validate rubric snapshot as needed; insert Evaluation + Job + idempotency record together | Unique(org, principal/scope, idempotency key) and request fingerprint; same-key/same-payload replays return same identifiers; divergent payload = safe 409 |
| claim | short transaction claim candidate ordered eligible jobs and assign attempt/fencing generation + expiry | PostgreSQL SKIP LOCKED is PROPOSED D-005; no network/LLM call before commit |
| heartbeat | short compare-and-swap update | match job_id + attempt generation + worker identity + non-expired lease + processing state; fencing protects renewals |
| finalize | one transaction persist validated criterion results, version metadata and terminal state + safe audit | check current live lease, state and fencing token; one final result version; unique constraints; stale worker performs zero writes |
| retry / terminal failure | one transaction update attempt, retry_at, classified safe error code, audit | max attempts/deadlines configurable, no raw text in error |
| feedback | scoped append and audit in same transaction where stored together | authorized actor, immutable AI result; reviewer feedback versioned |

An idempotency key is scope-bound; store only a server-side fingerprint of canonical validated payload and pinned rubric inputs, not raw text inside a lookup key/log. Concurrent insertion races use DB unique constraints and conflict-safe lookup/recheck within scope. Security of fingerprint selection and key expiry = OD-10/08. Do not cache decrypted text across tenants.

DbContext singleton creates AsyncEngine + async_sessionmaker once per process; each independent operation has its own AsyncSession. Transaction/session lifetime never crosses awaiting GPU inference or sleeps/retries. SQLA AsyncSession is not concurrency-shareable: one task owns its session; no session passed concurrently to parallel criteria. Explicit rollback on exception and close on all paths. Engine disposal only at process shutdown.

## 6. Worker/queue concurrency, recovery and overload

D-005 queue is PROPOSED; design adapter is the existing EvaluationJobRepository, not a new abstract broker framework. PostgreSQL candidate: SELECT FOR UPDATE SKIP LOCKED over eligible pending/retryable jobs with minimal transaction, status→processing, lease_until and monotonically increasing generation. Indices + uniqueness planned in Stage 05 after real migration inspection.

- Claimers may duplicate expensive computation only under crash/lease expiry, but never duplicate *valid result commit*. A stale worker must fail finalization even if newer worker has not yet committed (lease expiry checked).
- Heartbeat uses independently scoped short sessions, not the inference-call session. Lease duration, heartbeat rate, clock source/DB UTC, max attempt, deadline and backoff jitter require OD-10 + Stage 09 tests; no numeric constants approved.
- Network/LLM timeout and cancellation cannot leave DB locks open. A result that arrives late is validated but discarded if fencing fails. Explicit stop/drain on shutdown, recover expired attempts, avoid poison infinite loops.
- Terminal errors include unavailable rubric, invalid persistent schema, unauthorized scope, invalid evidence after bounded correction, or exhausted retry according to policy. Retryable errors include transient DB/model/network saturation only if operation is safely idempotent.
- Enforce admission control: queue depth/age limits, bounded in-flight GPU calls, per-scope quotas (OD-10/12/13); return sanitized 429/503 when configured rather than unbounded growth.
- Alternative if PostgreSQL queue fails capacity benchmarks: approved internal broker with same durable lease/fence/idempotent semantics; decision must be recorded, not silently activated.

## 7. Rubric, evidence and deterministic scoring

- Evaluation fixes published Rubric version ID + immutable snapshot checksum before enqueue, and verifies consistency at start and finish. Candidate-0.1 remains non-official until Stage 12 acceptance D-015.
- Model output is UNTRUSTED. Strict Pydantic schema validation; approved criterion codes only; score integer 0..5 when assessed; not_assessed => score null, reason required; malformed output never becomes a valid zero.
- Candidate OD-11 offset convention: zero-based, half-open Unicode code-point indices over exact original Python str (NOT normalized text); assert original[start:end] == quote. Any chunk-local offset must be mapped to global original span; invalid or ambiguous map => abstain/reject. This is PROPOSED pending sign-off, not an approved standard.
- Research evidence source kinds: original_submission (text claim) versus approved_reference_corpus (pinned internal document + authorized scope + corpus revision + independent offsets); never call external URL or treat model-generated references as verified.
- Compute final_score = 100 * sum(weight * score / 5 for assessed applicable) / sum(weight for assessed applicable); coverage = sum(assessed applicable weights) / sum(all applicable weights). Python Decimal, explicit recorded formula/rounding policy (OD-04). No assessed criteria => numeric final_score null; missing required evidence or inadequate coverage => partial/review according to versioned policy, never silent full grade.
- Preserve model artifact checksum/revision, runtime, prompt version/hash, parameter set, schema version, preprocessing/offset mapping version, rubric checksum, corpus version where used, timestamp, policy version and scores for reproducibility. Exact bitwise reproducibility of stochastic model runs is NOT claimed without tests.

### Assessment state and experimental rubric boundary

The Job transport lifecycle `processing_status` (`pending`, `processing`, `completed`, `failed_retryable`, `failed_terminal`) is distinct from the evaluation `result_status` (`assessed`, `partial`, `not_assessed`, all candidate labels) and the independent `needs_human_review` flag. A transport-completed job may have `result_status=not_assessed` with null numeric score; it must never be stored as `processing_status=needs_human_review` or `processing_status=partial`. Pin all three consistently across API DTO, domain service and persistence implementation when their owning stages begin; official enum policy remains OD-04/09/15 OPEN.

`candidate-0.1` is valid only as a version-pinned **internal non-production fixture** for Stage 03 benchmark or isolated Stage 06–11 tests with authorized synthetic data. It is **not** a Published rubric, must not be discoverable through the Published-rubric API, and cannot be used for organizational official scoring. Release requires an authorized immutable Published snapshot and a separately approved policy (OD-03/06/07/15); fail closed if missing. Inferred model or SME approval is prohibited.

## 8. Error, observability, security and testability

| Boundary | Policy |
|---|---|
| Input/Auth | 401 when unauthenticated, default deny scope, safe 404/403 candidate; validate Unicode/allowlist/size using approved limits |
| Business/Repository | typed internal error codes for missing rubric, scope, version mismatch, idempotency conflict, failed fencing; no FastAPI imports inside Core |
| Model | timeout, unavailable, invalid structured response and overload distinct; bounded retry only per explicit policy |
| Output | schema failure/invalid evidence/low coverage cannot publish completed grade; sanitize client errors |
| Logs | correlation ID, hashed/pseudonymous identifiers if approved, status, durations and safe codes only; no text/quote/prompt/header |
| Metrics | request and queue latency, age/depth, rate, attempts/expired leases, fail-fast discovery, schema/evidence invalidity, GPU saturation |
| Security | deny-by-default egress (enforced later), offline model artifacts, TLS and service auth, RBAC+owner scope, secret redaction, internal audit |
| Verification | pure Core scoring unit tests, fake internal provider unit tests with synthetic text, isolated PostgreSQL integration, multi-worker CAS/recovery, DTO/HTTP/IDOR, real internal inference, No-Egress and benchmark gated separately |

**Stage allocation:** Stage 03 benchmark model candidates; 04 composition root/security/logging/DI infrastructure; 05 DB/migrations; 06 rubric; 07 provider; 08 engine/scoring; 09 job processing; 10 HTTP+auth; 11 comprehensive verification; 12 authorized release. Stage 02 designs only.

**Unverified gate:** Since src/application/web.py, inject.py, bootstrap.py and PsqlDbContext do not exist, neither DI/discovery compatibility nor transaction behavior can be smoke-tested against real source. This is BLOCKED/NOT_RUN, not PASS; record Gate status in [Architecture Decisions](05_architecture_decisions.md).

Sources: [Repository Review](01_existing_repository_review.md) · [API/Contracts](03_api_and_contracts.md) · [File Matrix](04_file_change_matrix.md) · [Decision Log](../requirements/05_open_decisions.md).
