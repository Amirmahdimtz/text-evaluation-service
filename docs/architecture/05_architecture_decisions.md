# Stage 02 — Architecture Decisions and Technical Gates

> Record date: 2026-10-21 | ADR scope: Stage 02 design only | Decision authority: D-001..D-015 in Stage 01
>
> Status semantics: CONFIRMED فقط برای دستور صریح/معماری مرجع و تصمیم‌های تأییدشده قبلی است. PROPOSED نیازمند Validation فنی یا تصمیم مالک است؛ CANDIDATE نیازمند Benchmark؛ OPEN فاقد جواب معتبر. هیچ ADR جدید به‌صورت مصنوعی CONFIRMED نشده است.

## 1. Decision register / ADR summary

| ADR | Subject | Status | Driver / linked D- and OD- |
|---|---|---|---|
| ADR-01 | Four-layer convention and DI | CONFIRMED as mandated pattern; runtime UNVERIFIABLE | D-003, NFR-14 |
| ADR-02 | Atomic multi-entity transactions without modifying BaseRepository | PROPOSED | D-003, FR-01/07, OD-10 |
| ADR-03 | Durable job queue | PROPOSED PostgreSQL candidate | D-005, OD-10/12 |
| ADR-04 | Local inference and candidate runtime/model | CONFIRMED internal boundary; runtime/model CANDIDATE | D-002/D-006/D-007, OD-13/14 |
| ADR-05 | Scoped authorization and data retention | CONFIRMED deny-by-default goal; exact model OPEN | D-002/D-009/D-010, OD-07/08 |
| ADR-06 | Offset and evidence coordinate system | PROPOSED | OD-11, FR-04/11 |
| ADR-07 | Rubric policy, scoring and version provenance | CONFIRMED deterministic Python requirement; operational settings OPEN | D-008, OD-03/04/14/15 |
| ADR-08 | Versioned API v1 contract | PROPOSED_CONTRACT | OD-01/05/06/07/10/15 |
| ADR-09 | Discovery failure controls and Stage 02 verification status | PROPOSED guard; runtime gate BLOCKED | D-003, R-09/R-14 |
| ADR-10 | Employer sign-off timing | CONFIRMED D-015 | D-015, OD-16 |

## 2. Detailed ADR decisions

### ADR-01 — Reference architecture / constructor DI

- Context: current main has no executable src/ files. Reference mandates Host → Application → Core → Infrastructure, concrete @inject, Provider scan order infrastructure/core/application, WebService Controller discovery, Pydantic DTO, BaseRepository SQLAlchemy Async, Alembic.
- Decision: follow this prescribed architecture exactly. No additional Domain/usecase/interface abstraction; use feature folder text_evaluation and individual cohesive services only when necessary.
- Alternatives rejected: rewrite to DDD/CQRS/hexagonal or another DI framework without request (violates D-003); manual provider registration (violates conventions).
- Evidence: Guide contract, NOT a successful runtime review. Stage 04 imports/bootstrapping and Stage 10 route discovery are required to prove compatibility.

### ADR-02 — Atomic transactions crossing Repository responsibilities

- Problem: Guide BaseRepository performs independent Session/Commit per CRUD operation; Evaluation+Job and Result+Job status need one transaction.
- Proposal: use specialized compound methods in EvaluationRepository with one context-managed AsyncSession + session.begin(), all writes and conditional status transition in same DB transaction. Keep general BaseRepository per-CRUD operation independent. No open transaction across awaited inference/heartbeat.
- Alternative 1: shared transaction across repositories through optional caller-supplied AsyncSession. Benefit: reuse; drawback: session ownership leaks into Core or introduces plumbing, possible implicit commit. Allow only after Stage 05 source and test prove it necessary. Minimal optional extension preserving legacy behavior required.
- Alternative 2: separate commits + best-effort compensation. Rejected: risk of orphan jobs, partial results and double-completed state.
- Database-level invariant: finalization requires matching job/attempt/fencing generation, processing status AND unexpired lease, and unique result version; update must affect one row or fail with no writes. Unique scoped idempotency key/fingerprint prevents races. Actual SQL/constraint details deferred to Stage 05.
- Tests required: fault injection between inserts, rollback, concurrent same-key submissions, stale/expired lease, second finalization, commit failure, leaked session; no test can pass now.

### ADR-03 — Queue persistence, failure and backpressure

- Proposed default D-005: PostgreSQL durable queue with SKIP LOCKED, short claim transaction, monotonically incremented attempt/fence, lease_until, heartbeat CAS, bounded exponential backoff with jitter, crash/reclaim and terminal failure policy.
- Alternatives: approved internal broker (better isolation/scale but adds operational surface); synchronous request processing (rejected due FR-07); in-memory queue (rejected for restart durability).
- Decision before implementation: approve tested transaction/concurrency behavior and actual capacity; timings, max attempts, queue bounds and deadline values remain OD-10/12 OPEN. If PostgreSQL approach fails load goals, revisit instead of silently adopting an alternate queue.

### ADR-04 — Internal AI/provider and artifact trust

- CONFIRMED: no confidential content leaves authorized on-premise environment, no external inference provider, no outbound telemetry/model download dependency, no model tools/SQL/execution.
- CANDIDATE only: vLLM runtime and Qwen3-14B; compare against at least one alternate model in Stage 03 with authorized synthetic/approved dataset, hardware capacity, artifact/license provenance and quality metrics.
- Alternatives: external AI API is excluded by D-002; internal CPU/other runtime depends on empirical model/hardware evaluation. No installed API shape, context limit, package version or GPU is assumed.
- Validation: Stage 04 packet/DNS egress tests; Stage 07 local transport/schema/timeout; Stage 11 security/quality integration. Until then no No-Egress PASS claim.

### ADR-05 — Auth scope, IAM and protected data

- CONFIRMED baseline: default deny, verified Auth Context, owner+org scope in repository WHERE and use-case, strict field permissions, confidentiality of raw text and derived evidence.
- OPEN: real IdP claims, role matrix, cross-unit delegation, 403/404 response, encryption implementation, retention, legal hold, backup/audit policy, gateway placement (OD-07/08/13).
- Alternatives: trusting owner_id in JSON or checking only path UUID are rejected (IDOR). Shared-global session/cache of raw text across tenants rejected.
- Operational blocker: never use real protected samples before authorization/security controls, even when project-manager Stage gate is not awaiting employer sign-off.

### ADR-06 — Unicode/source evidence contract

- Proposal: exact Python Unicode code-point offsets, zero-based and half-open over unmodified original string; chunk/normalized spans must map reversibly back to original, verified by string slice equality.
- Alternatives: UTF-8 byte offsets (portable to byte storage but incompatible with direct Python str indexing); normalized-text offsets (high mismatch risk in Persian/ZWNJ); ambiguous offset units (rejected).
- OPEN: OD-11 technical/business contract and research corpus provenance. Corpus evidence must use separate revision, document and local offsets, with explicit authorization. Stage 08 tests must include combining marks, emoji, ZWNJ, different normalization, repeated quotes and empty spans.

### ADR-07 — Scoring, rubrics and reproducibility

- CONFIRMED: final score computed deterministically in Python, model output untrusted, strict evidence/schema validation, not_assessed has null score, all Rubrics versioned/pinned, no invented novelty or externally verified references.
- PROPOSED: scale 0..5 with 18 Stage 01 candidate criteria, Decimal arithmetic and source fingerprint; final policy version and rounding, applicability denominator, coverage threshold and required criterion triggers remain OD-03/04/14 OPEN.
- Alternatives: LLM-produced final score rejected; converting abstention to zero rejected; silent rubric mutation rejected. Published Rubric treated immutable and its snapshot/checksum retained; Stage 06 schema and Stage 08 golden tests.
- D-015 means engineering tests using clearly marked candidate-0.1 are permitted with safe synthetic data; official scoring/real data use still gated.

### ADR-08 — HTTP routes and error contract

- Proposal: /api/v1/text_evaluation with POST evaluations, GET evaluation, GET jobs/{job_id}, GET criteria, authorized rubric list/version, feedback creation (and feedback history conditionally).
- Versions: response schema_version, stable typed errors, request Idempotency-Key per scoped unique constraint; strict field-level scope; no text leakage. See [API Contract](03_api_and_contracts.md).
- Alternatives: custom ad-hoc endpoints across features (violates discovery); exposing SQLAlchemy entities or raw model JSON (violates DTO/security); unbounded lists (reject pending pagination policy).
- OPEN: status vocabulary, page limits, size, role/endpoint scope and API details OD-01/02/05/06/07/10/15. All remain PROPOSED_CONTRACT.

### ADR-09 — Bootstrap/import errors and verified gate

- Known from Guide: provider discovery can skip module import error; this can make endpoints silently missing. Actual reflection implementation does not exist on main.
- Proposal: Stage 04/10 test import/discovery deterministically and fail process startup when a required module/controller/provider is missing; no manual registration of individual services.
- Alternative: pass a fake smoke test with copied/mocked framework source in Stage 02 (rejected). A written design is NOT import/test evidence.
- Consequence: Stage 02 is BLOCKED for any mandatory gate requiring smoke proof of real WebService, inject, bootstrap and BaseRepository. Work independent of runtime (all five docs and static contracts) can be completed.

### ADR-10 — Formal customer acceptance timing

- CONFIRMED as user instruction D-015: business/SME consolidated external sign-off occurs in Stage 12, not after every engineering stage.
- Technical test Gates, internal data permissions, secret/change authorization, offline network validation and Production operational approvals remain mandatory. No unapproved OD is magically confirmed.

## 3. Decision requests, owner and impact

| Decision request | Options and tradeoffs | Owner/verification stage | Status |
|---|---|---|---|
| OD-07 IAM | in-place enterprise SSO token verification vs trusted internal gateway with secured claims; gateway simplifies API but needs strict trust/authenticity | IAM/Security, Stage 04/10 | OPEN |
| OD-08 storage/retention | encrypted DB + approved KMS vs alternate approved encrypted storage; access isolation vs operational complexity; audit DB vs internal sink | Security/Data Steward/SRE, Stage 04/05/12 | OPEN |
| OD-10 queue/idempotency | Postgres queue (minimal ops, DB coupling) vs approved broker (ops overhead, capacity separation); key window/retry/backpressure unknown | Architect/SRE, Stage 05/09 | OPEN |
| OD-11 offsets | code points (native Python) vs UTF-8 bytes (byte-native); normalization map required for Persian | Technical Lead/AI Lead, Stage 08 | OPEN |
| OD-03/04/09 Rubric policy | all-applicable denominator vs excluding explicit non-applicable criteria; abstention vs partial score; rounding and reviewer triggers need approval | SMEs/PO/AI Lead, Stage 06/08/12 | OPEN |
| OD-12/13 capacity/platform | tested PostgreSQL/GPU/network topology, local approved runtime/model; no numerical SLA before measurements | SRE/Infrastructure, Stage 03/04/09/11 | OPEN |
| OD-14 model quality | several internal models and golden protocol; comparison cost vs evidence needed for approval | AI Lead/SMEs, Stage 03/11 | OPEN |
| OD-15 result contract | embedded criteria vs separate paginated criteria; security fields and status/version semantics | PO/Security, Stage 10 | OPEN |
| OD-16 formal acceptance | final identified approvers/signature workflow only in Stage 12 | Employer/PO, Stage 12 | OPEN |

Stage 01 D-005 remains PROPOSED and D-006/007 remain CANDIDATE. D-008 weights remain PROPOSED. D-009..014 remain OPEN. No new authoritative value is supplied for any of them.

## 4. Stage 02 gate and executable-evidence classification

| Gate | Design assessment | Evidence status |
|---|---|---|
| Latest main/review requirements | PASS | connector HEAD and five blobs inspected |
| Existing vs missing APIs/dependencies | PASS_REVIEW | Original path probes + complete 11-entry tracked-tree enumeration supplied from the user's clean local Git checkout (snapshot `84b5d557`); runtime absent |
| Four-layer/DI conventions documented | PASS_DESIGN_ONLY | Guide aligned; runtime not available |
| Transaction/session/worker/fencing contract | PASS_DESIGN_ONLY | explicit boundaries/alternatives; no integration execution |
| API/DTO/error/auth and evidence contract | PASS_DESIGN_ONLY | proposed, not OpenAPI runtime |
| On-prem/no external AI and scope isolation | PASS_DESIGN_ONLY | no deployed network proof |
| Five architecture docs and FR/NFR matrix | PASS_DOCUMENTATION_QA | GitHub-stored documents: 31/31 focused static checks PASS on 2026-10-21; NOT runtime source verification |
| Import/discovery/bootstrap runtime | BLOCKED / NOT_RUN | no source/dependency manifests |
| PostgreSQL/Migration/Worker/API runtime tests | NOT_RUN | not implemented |
| GPU/model, no-egress, load, restore, internal E2E | PENDING_SERVER | authorized environment unavailable |
| Formal external sign-off | NOT_REQUIRED_STAGE_02 | D-015; Stage 12 only |

**Stage 02 status: BLOCKED (technical verification gate), despite completed independent design output.** This is not an assertion that another stage has started. Resume verification when reference-compliant executable platform exists, or request explicit user-authorized conditional progression documented with remaining risks. No stage advancement authorized by this ADR itself.

### STAGE02_GATE_DECOMPOSITION — test ownership without circular dependencies

The Implementation Plan Stage 02 check says **"Import/Discovery/Bootstrap smoke test executed in an existing development environment OR blocker documented"**. The documented blocker fulfills only its **disclosure** alternative, not a PASS for import execution. A distinct Stage 02 criterion, compatibility with the **actual** WebService/@inject, is not provable when no implementation exists. The subsequent plan explicitly assigns the runtime source and its tests to Stage 04 (DI/bootstrap), Stage 05 (DB/transaction) and Stage 10 (HTTP discovery). Building mock runtime in Stage 02 would be a false gate pass and violate the stage scope.

| Stage 02 acceptance question | Current evidence | Status | Owner of executable re-test |
|---|---|---|---|
| Required architecture docs and static contract checks | Five docs and traceable candidate contracts | PASS_DOCUMENTATION_ONLY | Stage 02 |
| Missing runtime and import smoke disclosed | Missing exact source paths with HTTP 404; reason documented | PASS_BLOCKER_DISCLOSURE, NOT_RUN_EXECUTION | Stage 02 records; Stage 04 executes |
| Matches real @inject/bootstrap/provider scanning | Guide design only, no actual modules | BLOCKED / NOT_VERIFIED | Stage 04 |
| AsyncSession/atomic multi-entity transaction compatibility | Proposed repository methods only | NOT_RUN / NOT_VERIFIED | Stage 05 |
| Feature HTTP route discovery and DTO runtime | Proposed paths only | NOT_RUN / NOT_VERIFIED | Stage 10 |
| Exhaustive tracked Git tree review | User-supplied full `git ls-tree -r --name-only HEAD` for `84b5d557`, 11 entries; local `18/18` documentation QA and clean tree | VERIFIED_USER_LOCAL (tracked files only) | Stage 02; re-run on changes |
| Stage 03 model benchmark preconditions | On-prem GPU and authorized synthetic/data not yet observed | PENDING_SERVER | Stage 03, before protected execution |

**2026-10-21 evidence update:** The user provided the full local 11-path tracked Git tree and an executed `18/18 PASS` report from `scripts/verification/check_stage02_docs.py` on commit `84b5d5575a29024fa8a1858526c4e6f78c0f870f`, plus empty `git status --short`. These close the tree-enumeration and local documentation-QA evidence gaps for that snapshot. They do not alter the `BLOCKED` DI/WebService compatibility gate, and are not import, DB, GPU or inference tests. See [Repository Review](01_existing_repository_review.md). This update records received user evidence; new follow-up modifications should be checked separately.

**Gate interpretation (proposal, not an approval):** Keep Stage 02 `BLOCKED` while mandatory actual-compatibility evidence is missing. A user-authorized conditional exception could permit beginning Stage 03's **independent** benchmark activities without claiming that Stage 02 tests passed; it must explicitly preserve deferred test owners, infrastructure/data permissions, risk acceptance, and Stage 03's own gate. This exception is **NOT_APPROVED** by this document or by a generic request to repair Stage 02 docs. Formal business acceptance remains Stage 12 per D-015. Never relabel `NOT_RUN` or `PENDING_SERVER` as `PASS`.

## 5. Stage progression and traceability

- Stage 03 cannot be declared started or complete through this design; it needs a distinct user request, authorized GPU/data and a valid Stage 02 technical gate or explicit conditional exception.
- Stage 04/05/09/10 own real runtime DI/DB/worker/API verification; their tests cannot be credited to Stage 02 retroactively without execution.
- Public repository documentation must be screened for secrets, sensitive organization data, internal infrastructure addresses and user content before commit.
- Reference links: [Review](01_existing_repository_review.md) · [Design](02_detailed_design.md) · [API](03_api_and_contracts.md) · [Matrix](04_file_change_matrix.md) · [Stage 01 Decisions](../requirements/05_open_decisions.md).


### Recorded Stage 02 static validation (2026-10-21)

After all five architecture files were committed on main, a 31-check validation of the actual GitHub-stored content passed: file paths, documentation references, four-layer/DI constraints, atomic session/lease/fencing design, proposed HTTP/auth/idempotency contracts, synthetic JSON parsing, exact Unicode evidence offset, 56-row ten-column future-stage matrix with FR/NFR coverage, ADR states, Markdown links and code-fence balance, and high-confidence secret-pattern heuristics. GitHub compare against baseline showed only these five added files plus the Stage 01 Decision Log/Tracker update. These results are documentation QA, never unit/integration/import/network proof; runtime verification stays BLOCKED/NOT_RUN and protected-server tests PENDING_SERVER.

## 6. Subsequent Stage 03 conditional authorization (2026-10-21)

After the historical Stage 02 record above, the user **explicitly authorized conditional Stage 03 entry** via D-016, notwithstanding unresolved Stage 02 executable compatibility. This prospective exception supersedes older text saying such entry was not authorized, **without retroactively passing any Stage 02 gate**. Stage 02 remains BLOCKED; DI/Bootstrap, DB/transaction and WebService discovery tests remain NOT_RUN with owners Stage 04/05/10. Stage 03 is IN_PROGRESS with GPU, data, runtime compatibility and benchmark metrics PENDING_SERVER/UNVERIFIED, as recorded in [Stage 03 documents](../ai/01_model_selection.md) and [Decision Log / Progress Tracker](../requirements/05_open_decisions.md). No protected-data or Production permission follows from the exception.

## 7. D-017 superseding Stage 02 gate interpretation (2026-10-24)

The earlier `BLOCKED` Stage 02 runtime compatibility check was **historical**, under the former gate timing. Under user-confirmed Implementation Plan v1.1.0/D-017, Stage 02 is `DONE / LOCAL_GATE_PASS` for repository inspection and detailed architecture. Five architecture artifacts exist, the actual Git tree was inspected, and 19/19 documentation QA plus 9/9 verifier regressions were user-executed. Missing future executable source is disclosed, not called an import PASS or a Stage 02 design failure. Mandatory real DI/Bootstrap smoke tests remain `NOT_RUN` until local Stage 04; DB/transaction/migration tests remain `NOT_RUN` until local Stage 05; WebService/HTTP discovery remains `NOT_RUN` until local Stage 10. Company GPU/model/No-Egress/quality/E2E are `DEFERRED_TO_STAGE_11`, not PASSED. See [Decision Log](../requirements/05_open_decisions.md) and [Stage 11 Ledger](../ai/03_benchmark_results.md#12-d-017-deferred-on-premise-test-ledger).
