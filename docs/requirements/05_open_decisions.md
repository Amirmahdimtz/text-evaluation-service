# Open Decisions, Decision Log and Stage 01 Progress

> **Date:** 2026-10-21 · **Stage 01 status:** `DONE` (internal documentation gates PASSED; cleared for Stage 02 on explicit user request). Employer acceptance deferred to Stage 12 under `D-015`.  
> **No invented approvals:** OPEN/PROPOSED/CANDIDATE are not CONFIRMED. Generic roles below are proposed approval responsibilities, not verified employer identities.  
> **Sources:** Implementation Plan §§0,3,4,6,7,10/Stage 01,13–14; Architecture Guide; explicit project instructions.

## 1. Decision Log (D-001..D-017)

| Decision ID | Topic | Status | Grounded source/reason |
|---|---|---|---|
| `D-001` | Production-Grade, not MVP | `CONFIRMED` | Explicit employer requirement |
| `D-002` | Confidential text, fully internal AI inference; no external AI providers | `CONFIRMED` | Explicit employer requirement |
| `D-003` | Architecture Guide mandatory | `CONFIRMED` | User-supplied normative guide |
| `D-004` | 12 stages and enforce acceptance gates | `CONFIRMED` | Project execution contract |
| `D-005` | PostgreSQL-backed durable queue | `PROPOSED` | Validate transactions/capacity; OD-10/12 |
| `D-006` | vLLM runtime | `CANDIDATE` | Benchmark Stage 03; OD-13 |
| `D-007` | Qwen3-14B base model | `CANDIDATE` | Benchmark licensing, Persian quality and hardware; OD-13/14 |
| `D-008` | 0..5 scale and initial rubric weights | `PROPOSED` | All anchors/weights/required flags require SME sign-off; OD-03/04 |
| `D-009` | SSO and identity model | `OPEN` | OD-07 |
| `D-010` | Retention/deletion/backup/data classification | `OPEN` | OD-08 |
| `D-011` | SLO/throughput/concurrency/RPO/RTO | `OPEN` | OD-12 |
| `D-012` | Admin/Export/Cancel feature scope | `OPEN` | OD-05/06 |
| `D-013` | Production platform Docker/K8s/VM | `OPEN` | OD-13 |
| `D-014` | AI quantitative acceptance metrics | `OPEN` | OD-14 |
| `D-015` | Employer/customer and formal domain sign-off occurs at **final project acceptance (Stage 12)**, not after each implementation stage | `CONFIRMED` (project execution instruction from user, 2026-10-21) | Supersedes the Implementation Plan's intermediate external-approval gates; keeps internal technical/security gates and controlled-access prerequisites |
| `D-016` | Conditional entry into Stage 03 with Stage 02 executable gates still open | `CONFIRMED` (explicit user Stage 03 instruction, 2026-10-21) | Allows independent Stage 03 preflight, offline documents and future **authorized** internal benchmark only; Stage 02 remains BLOCKED, DI/Bootstrap/DB/WebService NOT_RUN with 04/05/10 owners; does not approve protected data, model transfer, secret/network changes or Production |
| `D-017` | Real company-server/GPU/model/network-dependent verification takes place at Stage 11, not in Stages 01–10 | `CONFIRMED` (explicit user direction 2026-10-24; Implementation Plan v1.1.0) | Keeps all mandatory stage-local/unit/contract/test-DB checks; requires detailed Stage 11 deferred ledger. No server test is PASSED and Stage 12 still requires actual proof. |

**Important:** D-004 and D-015 are confirmed **project execution rules**, not business approval of any rubric, policy, topology or numerical target. All other previously unconfirmed choices remain OPEN/PROPOSED/CANDIDATE.

### Approval timing — binding project execution amendment (`D-015`)

- **Stages 01–11:** No employer/customer signature or formal SME approval is required merely to close a *stage*. Close a stage only when its applicable **internal technical deliverables, executable verification, security gates and known-risk records** are complete. Unimplemented or untested work must not be marked `PASSED` or `DONE`.
- **Stage 12 (final delivery):** Seek consolidated formal employer/authorized SME acceptance of business scope, Rubrics, measurable quality, security/privacy documentation and the final product, after real evidence from prior stages is available. Do not call the product `Production-Ready` without final Gates and sign-off.
- **Unresolved business settings:** Keep each OPEN with a proposed, versioned, clearly non-final design path. Implement/test candidates using permitted synthetic data where feasible; do not represent provisional weights, thresholds, scope or decisions as approved, or publish official enterprise grades before final acceptance.
- **Irreducible safety/permission prerequisites:** Authorization to use real confidential data, security controls, use of protected infrastructure, secret changes, destructive operations and Production deployment remain mandatory **before those specific actions**. These are not customer acceptance sign-offs for ordinary stage completion.
- **Progression:** Each next stage still needs a new explicit user request. Under D-017, missing source for future DI/DB/HTTP implementation is not a Stage 02 design failure; the local tests are mandatory in their actual implementation stages. Company-server tests are mandatory only in Stage 11. Previous BLOCKED descriptions remain historical.
- **Source precedence:** This user-confirmed amendment supersedes the *intermediate formal sign-off timing* in `Text_Evaluation_Service_Implementation_Plan_FA.md` (§§0, 4.2, 10/Stage 01, Stage 06, 12). All other baseline engineering/security requirements continue to apply. Original Project Sources remain unchanged and need synchronization with this decision.

## 2. Employer decision requests (ALL OPEN)

| ID | Priority | Topic | Question / decision required | Proposed approval responsibility | Impact and downstream stage | Status |
|---|---|---|---|---|---|---|
| `OD-01` | P0 | داده ورودی و زبان | فقط متن تایپی؟ file/PDF/DOCX/STT ورودی محصول هستند؟ چه زبان‌ها، کانال‌ها و metadata اجباری/اختیاری مجاز است؟ | Product Owner + Speech/Media/Research SMEs | FR-01,FR-02,NFR-12; DTO/input/parser scope; Stage 02/10 | `OPEN` |
| `OD-02` | P0 | طول و سقف ورودی | حداقل/حداکثر char/byte/token هر حوزه و متن بلند؛ اندازه پژوهش، Unicode/Encoding و رشد تقاضا؟ | Product Owner + Domain SMEs + SRE | FR-01/11; chunking and capacity; Stage 03/08/10 | `OPEN` |
| `OD-03` | P0 | تصویب Rubric | تعریف، مجموعه معیارها، وزن‌های 100تایی، anchors 0..5 و required flag هر سه حوزه تأیید یا اصلاح می‌شوند؟ | Speech SME + Media SME + Research SME + Product Owner | FR-02/03/04; Stage 03/06/08; mandatory approval | `OPEN` |
| `OD-04` | P0 | Scoring/Coverage Policy | threshold پوشش، applicability denominator، required missing، rounding/precision، انتشار score ناقص و human-review trigger دقیق چیست؟ | Domain SMEs + Product Owner + AI Quality Lead | FR-05/06; Stage 06/08/10; blocking valid official scores | `OPEN` |
| `OD-05` | P1 | دامنه توسعه محصول | تاریخچه، دریافت فایل، export، delete، re-evaluate، cancel، share و report format جزو Scope هستند؟ | Product Owner | FR-01/08/12; Stage 02/10 | `OPEN` |
| `OD-06` | P1 | Rubric/Feedback administration | Draft/Validate/Publish/Retire و reviewer feedback، edit/appeal/escalation چه workflow و مجوزی دارند؟ | Product Owner + Rubric Curators + Reviewer Lead | FR-03/09; Stage 06/10 | `OPEN` |
| `OD-07` | P0 | هویت، واحد، Role | SSO/IdP موجود چیست؟ User/Org hierarchy، delegated reviewer roles، service accounts، 403 vs 404 و cross-unit scope؟ | IAM Owner + Security Officer + Product Owner | FR-01/08/09; Stage 04/10 | `OPEN` |
| `OD-08` | P0 | سیاست داده و حفاظت | طبقه‌بندی، متن اصلی/نتیجه در چه Storage، مدت retention، legal hold، delete، audit retention، encryption/KMS، backup و key rotation؟ | Security/Privacy Officer + Data Steward/Legal + SRE | FR-01/08/09/10; Stage 04/05/12 | `OPEN` |
| `OD-09` | P0 | بررسی انسانی | چه موارد ارجاع اجباری است؟ چه Reviewer/مهلت و روش override/adjudication، version و اعلان به کاربر؟ | Domain SMEs + Reviewer Lead + Product Owner | FR-06/09; Stage 08/10/11 | `OPEN` |
| `OD-10` | P1 | Job/Retry/Idempotency | سیاست timeout، retry، max attempt، backoff، lease، duplicate submit window، cancel و backpressure؟ | SRE + Architect + Product Owner | FR-01/07; Stage 02/05/09 | `OPEN` |
| `OD-11` | P0 | Evidence/Unicode Contract | واحد offset (codepoint vs UTF-8 byte)، half-open range، normalization/ZWNJ mapping، relevancy decision و source reliability؟ | Technical Lead + AI Quality Lead + Domain SMEs | FR-04/11; Stage 02/08 | `OPEN` |
| `OD-12` | P0 | ظرفیت/SLO/DR | requests/day، burst peak، concurrent users/jobs، latency P50/P95، SLO/SLA، RPO/RTO، failure tolerance، growth horizon؟ | Product Owner + SRE + Business Continuity Owner | FR-07/11; Stage 03/04/09/11 | `OPEN` |
| `OD-13` | P0 | محیط AI داخلی | GPU count/VRAM و Datacenter، network/egress isolation، artifact transfer/legal license، approved identity/TLS؛ vLLM/Qwen candidates؟ | Infrastructure Owner + Security Officer + AI Lead | FR-10/11; Stage 03/04/07 | `OPEN` |
| `OD-14` | P0 | AI Quality & Golden Dataset | dataset قانونی، نمونه هر حوزه، SME raters، adjudicator، calibration/holdout split، MAE/evidence/stability/coverage/abstention thresholds، neutrality review؟ | AI Quality Lead + Domain SMEs + Product Owner + Data Steward | FR-04/06/11/12; Stage 03/08/11 | `OPEN` |
| `OD-15` | P1 | Business result contract | Business JSON/report example، status naming (completed/partial/review)، exportable fields، explainability policy و version display؟ | Product Owner + Domain SMEs + Security | FR-04/05/06/08/12; Stage 02/10 | `OPEN` |
| `OD-16` | P0 | Final product acceptance/sign-off ownership | چه شخص/گروهی در **Stage 12** خروجی نهایی، Rubricها، سیاست محرمانگی، کیفیت AI، معیارهای پذیرش و Release را رسماً می‌پذیرد؟ | Employer/Product Owner + SMEs + Security Officer | Stage 12 formal external gate; **not a Stage 01/02 blocker** | `OPEN` |

Priority definitions: **P0** requires a decision before the **relevant action/gate** (e.g., official scoring, sensitive-data access or final release), not automatically before Stage 02; **P1** impacts optional scope or implementation specifics. `OD-16` is the **Stage 12 external-acceptance gate**, while routine stages use internal technical gates.

## 3. Required approval package and decision recording

**Product Owner:** provide available scope/workload information if obtainable, but record unresolved details as OPEN; consolidated **formal sign-off is due at Stage 12** (`OD-16`), not each earlier stage.  
**Three domain SMEs:** supply consultation/calibration when available; retain provisional rubric weights/anchors and `required` statuses as NOT APPROVED until the **final acceptance** (`OD-03/04/09/16`).  
**Security/IAM/Data Steward:** define safeguards and provide any **mandatory operational authorization** before real confidential data access, credential changes or production activity; formal customer acceptance of the final security policy is at Stage 12 (`OD-07/08/13/14/16`).  
**AI Quality Lead:** approve annotation protocol, evidence offsets, benchmark metrics and quality thresholds (`OD-11/14`).  
**SRE/Infrastructure:** approve hardware, latency/capacity/recovery and operating controls (`OD-10/12/13`).

For every future approval, record **ID, decision value, scope, approver/role, date/time, evidence link, effective version and impacted FR/AC/stages**; only then transition its status to `CONFIRMED`. If rejected, record `REJECTED` with rationale; if changed, perform traceability update. No signature, owner assignment or numeric threshold is inferred from this document.

## 4. Risk log additions (to original R-01..R-12)

| ID | Risk | Impact | Mitigation | State |
|---|---|---|---|---|
| R-13 | GitHub repository is **public**; internal requirements/data could leak through commits | Confidentiality violation | Only generic specifications in Git; no real data, secrets, internal network addresses, service identity, restricted docs; review before each push; consider private repository per Security policy | OPEN (Security sign-off OD-08) |
| R-14 | No previous commit/architecture implementation exists in GitHub | Cannot validate source patterns or run software tests in Stage 01 | Limit changes to documentation; Stage 02 will inspect what actually exists then | DOCUMENTED |
| R-15 | Premature official score from unapproved rubric and thresholds | Misleading business/AI outcomes | Keep `candidate-0.1` NOT published; block official scoring until OD-03/04/14 | OPEN |
| R-16 | Unspecified role/tenant boundary | Cross-unit privacy failure | Define role matrix and query-scope checks before data persistence/API exposure | OPEN |

## 5. Progress Tracker (evidence-based)

| Stage | Name | Status | Evidence |
|---:|---|---|---|
| 01 | Requirements & Acceptance | `DONE` | Five candidate baseline specifications, domain input matrix, validated synthetic business-report JSON, rubric calibration and evidence provenance added. **25/25 latest GitHub-stored-file documentation checks PASS**. Formal customer sign-off deferred to Stage 12 (`D-015`); **Stage 02 executed as a documentation/inspection stage; technical runtime verification BLOCKED.** |
| 02 | Repository & Detailed Architecture | `DONE` | D-017 local design gate: five documents, verified source tree, 19/19 user-local documentation QA and 9/9 checker regressions PASS. DI/Bootstrap tests mandatory in Stage 04, DB transactions/Migrations in Stage 05, WebService discovery in Stage 10: currently NOT_RUN, not PASSED. Historical BLOCKED status superseded only for Stage 02 design gate. |
| 03 | Model Feasibility & Offline Benchmark Design | `DONE` | D-017 local gate: four AI documents, two candidate models, three-domain benchmark/dataset protocol, validated offline JSON/offset tool and theoretical resources. User-local compile and 38/38 Stage 03 tests PASS on `663c1db`; clean tree. [12 deferred tests](../ai/03_benchmark_results.md#12-d-017-deferred-on-premise-test-ledger) remain `DEFERRED_TO_STAGE_11`; model selection, GPU, AI accuracy and no-egress NOT VERIFIED. |
| 04 | Infrastructure & Security | `IN_PROGRESS` | D-017: implementation and four core security/deployment documents committed. Isolated Python 3.13.5: 26/26 Stage 04 tests PASS, Uvicorn health HTTP 200. **User-local Windows Python 3.12 (transcript, 2026-10-24): 26/26 Stage 04 tests, 19/19 Stage 02 documentation checks, 12/12 Stage 02 regressions, 38/38 Stage 03 regressions, compile/static and `pip check` PASS**. User-local Uvicorn **STARTUP/BIND PASS** at new development `127.0.0.1:18080` (after prior 8000/8001 conflicts); **26/26 Stage 04 tests again PASS** after port change, **Windows HTTP health PASS_USER_LOCAL**: `/health/live` → `alive`, `/health/ready` → `ready` on port 18080 (observed PowerShell `Invoke-RestMethod`). **New dependencies installed successfully on user-local Windows Python 3.12; `pip check` PASS; full tests **37/37 PASS after the route test fix** (user Windows Python 3.12, fresh upgraded dependency venv); `pip check` PASS. Ephemeral Uvicorn `127.0.0.1:50165` startup/bind PASS; HTTP GETs `/health/live` → `alive` and `/health/ready` → `ready` **PASS_USER_LOCAL** on the same port. New Stage 04 evidence tooling verified **52/52 full tests PASS on user-local Windows** after pulling audit scripts; one-off RemoteSigned collector started and pip check PASS; next step FAILED_TARGET_SITE_PACKAGES due to PowerShell native quote stripping; corrected and retest PENDING_USER_LOCAL. Real CVE scan, CycloneDX SBOM, PyPI wheel SHA256 and reviewed package licenses remain NOT_RUN / OPEN. Stage 05 entry NOT_APPROVED.** Corporate SSO/Vault/No-Egress DEFERRED_TO_STAGE_11, not PASSED. [Validation](../verification/04_stage04_security_validation.md) / [deferred ledger](../verification/04_stage04_deferred_stage11_ledger.md). |
| 05 | Database & Migration | `NOT_STARTED` | No DB/migration changes |
| 06 | Rubric Management | `NOT_STARTED` | No published rubric or code |
| 07 | Local LLM Provider | `NOT_STARTED` | No model/inference integration |
| 08 | Evaluation Engine | `NOT_STARTED` | No scoring code |
| 09 | Durable Worker & Queue | `NOT_STARTED` | No worker/queue code |
| 10 | API & Authorization | `NOT_STARTED` | No HTTP endpoints or Auth integrations |
| 11 | On-Premise Server Verification & Calibration | `NOT_STARTED` | Stage 03 ledger has 12 deferred tests and Stage 04 ledger adds 10 security/infrastructure verification entries (`DEFERRED_TO_STAGE_11`, not PASSED; some test domains overlap). Controlled infrastructure/permissions still required. |
| 12 | Production Release & Handover | `NOT_STARTED` | No production operations |

**Stage 01 technical deliverables:** [Product FR/NFR](01_product_requirements.md) · [Candidate Rubrics](02_evaluation_rubrics.md) · [Acceptance Matrix](03_acceptance_criteria.md) · [Security/Data Policy](04_security_and_data_policy.md) · this file (Decision Log/Tracker). The Stage 01 validation report distinguishes documentation tests from product tests. **Stage 01 is DONE under the revised internal gate (`D-015`); no formal employer sign-off or operational model validation is implied.**

**Acceptance Gate: `PASS` — Stage 01 `DONE`.** All five mandatory artifacts exist; requirements/AC linkage, three rubric catalogs, proposed input/report contracts, calibration/evidence boundaries, security/no-egress constraints, OPEN decisions and risks have been documented; 25/25 focused verification checks passed on stored files. Formal Product Owner/SME acceptance is **Stage 12** only (`D-015`); unapproved Rubric/quality/SLO/settings remain non-official. **Stage 02 subsequently started by explicit request; see its BLOCKED technical gate and evidence below.**

## 6. Stage 01 tracking record (internally verified; stage completed)

- Date: 2026-10-21
- Source documents reviewed: `Service_Architecture_Guide_FA.md`, `Text_Evaluation_Service_Implementation_Plan_FA.md` v1.0.0 (provided in Project Sources; not edited there).
- GitHub repository at start: public, empty, `main` without initial commit; confirmed via GitHub API 409. Documentation-only initialization performed as separate Conventional Commits.
- Files: five `docs/requirements/*.md` Stage 01 artifacts; no application code, migration, secrets or production changes.
- Tests: **2026-10-21**, initial GitHub-stored-file validation `18/18 PASS`; after remediating documentation gaps, an **independent 25/25 PASS** verification of GitHub-stored Markdown/JSON was executed. The latter checked five file paths, FR/AC links, 28 unique FR cases, 14 NFR/AC links, 18 Rubric criteria with 9 required fields and anchors 0..5, domain weights/flags, provisional input matrix, calibration/abstention policy, research source provenance, valid synthetic JSON, deterministic score 71.25 and coverage 0.80, quote/offset exactness, unapproved/Stage 12 policy, 16 decision requests, relative links, tables, code fences, escaped backticks and high-confidence secret patterns. **This is documentation-only QA**, not executed application/model/security testing. Product/API/DB/migrations `NOT_RUN`; real GPU/no-egress/load/recovery/AI benchmark `PENDING_SERVER`. No full DLP or security certification is implied.
- Formal customer sign-off: **DEFERRED_TO_STAGE_12** under confirmed process decision `D-015` (approver `OD-16` remains OPEN). Other proposed settings remain unapproved, and official rubrics are not yet Published.
- Project Sources synchronization: Source document's original Progress Tracker remains `NOT_STARTED` unless independently updated; GitHub file here is the evidence-backed Stage 01 update. **Manual synchronization or authoritative pointer change is needed.**
- Next stage: **Stage 02 entry approved by internal Stage 01 gate**; Stage 02 explicitly requested and its design artifacts delivered; runtime compatibility gate remains BLOCKED. No per-stage external signature is required.

### Verified Stage 01 validation evidence (2026-10-21)

| Evidence | Real result | Interpretation |
|---|---|---|
| GitHub repository/file tree | `main` contains only five `docs/requirements/*.md` artifacts | Stage 01 documentation-only change scope verified |
| Document structural check | Initial `18 PASS / 0 FAIL`; remediation review `25 PASS / 0 FAIL` | Five docs, coverage/traceability, rubric field+anchor structure, synthetic JSON arithmetic/span checks, security/decisions and markdown hygiene verified on fetched `main` |
| Rubric validation | 18 unique candidate Criteria; all have 9 required fields and score anchors 0–5 | Syntactic/structural, **not** expert approval |
| Traceability | 12 FRs, 28 unique FR ACs; 14 NFR ACs | Test plans specified; **not** product-test execution |
| Security scan (heuristic) | No high-confidence private-key/API-token patterns detected | Does **not** replace human DLP/security review |
| Product/API/DB/Migrations/Model tests | `NOT_RUN` | No Application source existed at Stage 01; not claims of software quality |
| GPU/Inference/AI quality/Load/No-Egress/Backup restore | `PENDING_SERVER` | Requires authorized organizational infrastructure in Stage 03/04/11 |
| Business/SME formal acceptance | `DEFERRED_TO_STAGE_12` | Not a Stage 01 gate; candidate requirements/rubrics remain unapproved for official business scoring, but internal Stage 01 = `DONE` |

**GitHub validation evidence:** Original Stage 01 document commits are preserved in Git history; later `docs:` commits implement external-signoff deferral (`D-015`) and documentation QA remediation. All Stage 01 writes are confined to the five files under `docs/requirements/`. The final Stage 01 gate commit and HEAD SHA are verified in GitHub separately before reporting to the user.

## 7. Questions to resolve as evidence becomes available (formal acceptance at Stage 12)

1. Who will formally accept Product Requirements, the three domain Rubrics and Security/Privacy rules at final Stage 12 delivery (`OD-16`)?
2. What evidence or expert feedback can be collected to calibrate each criterion/weight/anchor/`required` before the final business acceptance (`OD-03`)?
3. What threshold/rounding/abstention and human-review policy must govern official scores (`OD-04/09`)?
4. Which organization IAM, org boundary, classification/retention/deletion and encryption policy is authoritative (`OD-07/08`)?
5. Which text/file/language scope, volume, SLO/RPO/RTO and hardware/inference boundary can be approved (`OD-01/02/12/13`)?
6. Who owns the Golden Dataset, adjudication, holdout access and AI quality acceptance thresholds (`OD-14`)?

Further detail and rationale: [01_product_requirements.md](01_product_requirements.md), [02_evaluation_rubrics.md](02_evaluation_rubrics.md), [03_acceptance_criteria.md](03_acceptance_criteria.md), [04_security_and_data_policy.md](04_security_and_data_policy.md).

## 8. Stage 02 inspection/design result (2026-10-21)

- **Stage:** 02 — Repository Inspection & Detailed Architecture.
- **Status:** BLOCKED for technical compatibility gate, despite completion of independent documentation deliverables. D-015 formal employer/SME sign-off is not a Stage 02 gate.
- **Baseline:** main HEAD at initial inspection 924fd3c91f680b00c27533bae9fc0c59e70c6e8c. Public repo; GitHub connector pull/push verified. Sandbox git ls-remote failed because github.com DNS resolution unavailable; authenticated connector reads/writes were used instead.
- **Observed:** five docs/requirements files retrieved; representative src/host, application/web, infrastructure/di, PsqlDbContext, BaseRepository, Alembic and dependency/build files returned GitHub API 404. Python/FastAPI/SQLAlchemy/Pydantic versions, actual DI behavior, CI and other unknown custom paths UNVERIFIABLE. Complete recursive Git tree enumeration NOT_VERIFIED.
- **New documents:** [Repository Review](../architecture/01_existing_repository_review.md), [Detailed Design](../architecture/02_detailed_design.md), [API Contracts](../architecture/03_api_and_contracts.md), [File Matrix](../architecture/04_file_change_matrix.md), [Architecture ADRs](../architecture/05_architecture_decisions.md).
- **Design decisions:** Architecture Guide enforced; atomic Evaluation+Job and Result+Completion via proposed single-repository compound transaction, no BaseRepository modification now; scoped idempotency, lease/fencing and worker recovery proposed; code-point source offsets proposed; internal inference mandatory; vLLM/Qwen CANDIDATE and PostgreSQL queue PROPOSED. No OPEN decision marked CONFIRMED.
- **Tests executed (actual GitHub-stored documents):** 31/31 focused static QA PASS: file existence, baseline and missing-path evidence, layer/DI naming, session boundary, atomic create/finalize, fencing/retry, internal-only AI, deterministic score/evidence provenance, API/status/idempotency/auth, synthetic JSON parse and Unicode quote verification, 56-row/10-column matrix, Stage 03–12 coverage, FR-01..12 / NFR-01..14 traceability, ADR states, Markdown local links/fences and high-confidence secret heuristics. Earlier literal-text matching checks were revised to inspect the actual contract rather than incorrectly treat synonymous wording as a failing architecture gate. This is documentation validation, NOT runtime/source integration testing.
- **Runtime checks:** Import/DI/Controller discovery/bootstrap, SQLAlchemy transaction, API, migration and worker tests NOT_RUN (no executable src nor runtime manifests). Actual compatibility Gate BLOCKED / NOT_VERIFIED.
- **Server tests:** real inference/GPU, model accuracy, long-doc capacity/load, Network No-Egress, internal DB integration/restore and E2E = PENDING_SERVER (no authorized internal environment used).
- **Other gates:** review/design/contract/matrix/ADR, provisional policy, security/no-external-LLM and documentation QA PASS_DESIGN_ONLY; actual deployment security, role matrix, SLO, approved Rubric and production operations NOT_VERIFIED and reserved for the owning stages.
- **External acceptance:** Stage 12 only under D-015. Authorization for real confidential data, secrets and Production remains independently mandatory.
- **GitHub commit sequence for Stage 02 architecture files (as confirmed on main):** d0a82987e1da2f0dd032867ae5cbb988499190fd; 0520c5f071d2f9f1a53fdbbc14ef1f092bd81537; e76199447dd7030fc05b1e7b6d3480ff1c0eaaf3; 5bf4b12d06f7980328a4d3b36e002da004b20fc0; 1f5d2f03f8be319b250cf591be3c9dae6cee10ce. Tracker update commit SHA to be independently verified in GitHub history.
- **Next stage:** Stage 03 NOT_STARTED. Proceed only by separate user instruction and technically satisfied Stage 02 gate, or an explicit user-authorized conditional continuation with documented risks; GPU/approved dataset and relevant operational permissions remain prerequisites.

## 9. Stage 02 targeted defect remediation (2026-10-21)

**Scope:** Stage 02 design/docs correction only. There was no Runtime, DB, inference or Stage 03 implementation. Stage 01 remains `DONE`; Stage 03 remains `NOT_STARTED`. This is not approval of unpublished rubric settings or formal business acceptance.

| Defect / risk | Corrective artifact | Verification and remaining status |
|---|---|---|
| P1: `processing_status` conflated with business result | [API contract](../architecture/03_api_and_contracts.md) and [Stage 01 synthetic report](03_acceptance_criteria.md) | Corrected independent `processing_status`, `result_status`, `needs_human_review`; both stored JSON fixtures parsed and validated. `PASS_DOCUMENTATION_ONLY`; OD-04/09/15 official vocabulary remains `OPEN` |
| P1: Stage 02 test evidence cyclically depended on Stage 04/05/10 runtime | [Architecture ADRs / STAGE02_GATE_DECOMPOSITION](../architecture/05_architecture_decisions.md) | Disclosure alternative to Stage 02 smoke-test checklist is documented, **not** an actual import/DI PASS. Executable compatibility still `BLOCKED`; Stage 04 owns DI/bootstrap, Stage 05 database transactions and Stage 10 route discovery. Conditional entry exception `NOT_APPROVED` |
| P2: incomplete recursive repository tree enumeration | [Repository review](../architecture/01_existing_repository_review.md) | `VERIFIED_USER_LOCAL` at `84b5d557`: user supplied all 11 tracked paths from `git ls-tree -r --name-only HEAD`, matching local Git HEAD and clean working tree; no executable `src/` or dependency manifest in that snapshot. This does not prove any runtime behavior |
| P2: Candidate Rubric mistaken for Published snapshot | [Detailed design](../architecture/02_detailed_design.md), [API contract](../architecture/03_api_and_contracts.md) | Clearly isolated internal Stage 03 benchmark/Stage 06–11 tests; official API requires authorized Published snapshot; final release policy still `OPEN` |
| P3: documentation checks not reproducible | [Standalone Python QA](../../scripts/verification/check_stage02_docs.py) | **18/18 PASS actually executed by the user on their local clone at `84b5d557`**, with output provided in conversation. Subsequently the QA script gained a 19th check for canonical DTO field names; the new version has NOT_RUN locally until retested. Historical independent 18/18 GitHub document assertions remain separately reported, not confused with runtime/CI tests |

**Post-remediation QA evidence:** On 2026-10-21 the GitHub connector fetched the committed architecture, Stage 01 acceptance and Progress Tracker files plus the new checker. Independent read-only validation returned **18 PASS / 0 FAIL** for expected files, DI/four-layer terms, recorded blocker and owners, test-only rubric policy, status field taxonomy, both valid JSON fixtures and numeric/null consistency, six exact Persian source quotes, Unicode offsets, 56-row ten-column future-stage matrix, full FR/NFR names, Stage 02/03 status, balanced Markdown code fences, matching relative links and high-confidence key-pattern heuristics. These are **documentation checks only**, not evidence of passing Python runtime, real model, GPU, security/no-egress or DB tests. The Python script itself requires execution in a real clone to produce its own independent report.

**Local verification on Windows PowerShell, after `git pull --ff-only origin main`:**

```powershell
git status --short
git log -1 --format="%H %s"
git ls-tree -r --name-only HEAD
git ls-files "src/**" "tests/**" ".github/**" "pyproject.toml" "requirements.txt" "Dockerfile"
python scripts/verification/check_stage02_docs.py
```

**Retained acceptance boundary:** Stage 02 `BLOCKED` until the actual DI/WebService compatibility Gate has valid executable evidence, or a separately explicit user-approved conditional progression is recorded without changing failed/unexecuted Gate states to `PASS`. No permission to use real confidential text, GPU/network, secrets or Production is implied. Stage 03 `NOT_STARTED`; server benchmarks `PENDING_SERVER`. Tracked-tree enumeration and original local 18/18 documentation QA are evidenced for commit `84b5d557`; updated 19-check script requires a separate local run after the next pull.

## 10. Follow-up review corrections (2026-10-21)

- **P2 API contract field naming:** In [API Contracts](../architecture/03_api_and_contracts.md), `EvaluationJobStatusDto` now uses canonical `processing_status` rather than ambiguous `status`; `EvaluationReportDto` now uses `evaluation_type` rather than `domain`. The same naming is applied consistently to prose, the request DTO and synthetic fixtures. The job lifecycle, assessment result and independent human-review boolean remain distinct. These are **PROPOSED_CONTRACT** changes; no endpoint exists or has been exercised.
- **P2 inspection evidence:** User-provided PowerShell output on the pre-follow-up commit `84b5d5575a29024fa8a1858526c4e6f78c0f870f` is sufficient to verify an 11-entry tracked-tree snapshot and absence of `src/`, tests, CI, Dockerfile and dependency manifests **from that tracked tree**. This updates Stage 02 inspection evidence without implying verification of untracked files, installed dependency versions or running services. The user additionally provided `git status --short` (empty) and a completed `18/18 PASS` execution of the original local docs checker. See [Repository Review](../architecture/01_existing_repository_review.md) and [Architecture ADRs](../architecture/05_architecture_decisions.md).
- **Regression guard:** [Stage 02 documentation checker](../../scripts/verification/check_stage02_docs.py) now checks the *response DTO table cells* for the canonical two field names and absence of legacy standalone `status`/`domain` names. This increases the local test from **18 to 19 checks** when Git is available. The user subsequently executed the 19-check script and reported **18/19**, with only `uncertainty disclosed` failing due to its stale `NOT_VERIFIED` string assertion; see Section 11 for the correction. A complete **19/19 PASS** has not yet been observed after that fix. Static GitHub source inspection can verify the proposed field names independently but is not execution of the Python script.
- **Unchanged gates:** Stage 02 `BLOCKED` for executable DI/WebService compatibility. Stage 03 `NOT_STARTED`; no authorized conditional entry, no server/GPU benchmark, no runtime/migration or Production operation.

**Local re-check (PowerShell):** `git pull --ff-only origin main`, then `python scripts/verification/check_stage02_docs.py`, `git ls-tree -r --name-only HEAD` and `git status --short`. Preserve original output as test evidence before considering any later Gate-status change.

## 11. Stage 02 documentation-check regression correction (2026-10-21)

- **User-executed evidence:** On HEAD `fba626c20c196e3a694f4e4ad7c6da1203a97664`, the user supplied `git pull --ff-only origin main`, the matching `git log -1`, a clean `git status --short`, and actual `python scripts/verification/check_stage02_docs.py` JSON: **18 PASS / 19 total**, exactly one FAIL: `uncertainty disclosed`. The script itself reported `Git tree entries: 11`, with its existing tracked-tree check PASS.
- **Root cause:** The previous QA predicate required both `UNVERIFIABLE` and `NOT_VERIFIED` to appear anywhere in [Repository Review](../architecture/01_existing_repository_review.md). The latter obsolete status was correctly removed when the user's full tracked-tree inspection was recorded as `VERIFIED_USER_LOCAL`. The failure was an outdated literal-string assertion, not missing runtime evidence or a failed architectural check.
- **Correction:** [QA script](../../scripts/verification/check_stage02_docs.py) now requires (a) the dependency/environment `UNVERIFIABLE` disclosure, (b) the explicit `Python import/discovery/bootstrap | NOT_RUN` row, and (c) the explicit `Actual Git recursive tree retrieval | VERIFIED_USER_LOCAL` row. This tests **two separate evidence states**, without incorrectly demanding a stale `NOT_VERIFIED` tree marker.
- **Tests actually run:** Isolated Python regex regression tests **PASS** for a valid disclosure fixture and for two negative cases (wrong runtime PASS label and regressed tree NOT_VERIFIED label). GitHub read-back verified the stored predicate. Full on-repository Python script re-execution after this commit has **not been performed here** because the GitHub checkout is not mounted in the assistant runtime; current full-suite status `PENDING_USER_LOCAL`, not PASS.
- **Retest:** In the user local clone, `git pull --ff-only origin main` then `python scripts/verification/check_stage02_docs.py`. Expect 19 checks if the documented artifacts are unchanged; report actual output, not the expectation, as evidence.
- **Unchanged Gate:** Stage 02 overall `BLOCKED`; DI/Discovery/Bootstrap, DB/API/Worker execution `NOT_RUN`; GPU/model/security checks `PENDING_SERVER`; Stage 03 `NOT_STARTED` and no conditional progression approved.

## 12. Stage 03 conditional entry and open technical gate (2026-10-21)

- **Explicit authorization:** D-016 allows independent Stage 03 preflight and static candidate/protocol work notwithstanding Stage 02 BLOCKED technical compatibility. It is not a waiver of Stage 02 executable tests, real benchmark acceptance, protected-network permissions or Stage 04 entry.
- **Baseline:** GitHub main 6f650728e80849f65f46b50c81ab2da500ac6d53. Recursive source tree: no src/ implementation, model, benchmark dataset, lockfile or GPU evidence.
- **Independent deliverables:** [Model Selection](../ai/01_model_selection.md), [Benchmark Protocol](../ai/02_benchmark_protocol.md), [Results ledger](../ai/03_benchmark_results.md), [Inference Resource Plan](../ai/04_inference_resource_plan.md).
- **Candidate-only:** D-006 vLLM and D-007 Qwen3-14B stay CANDIDATE; Qwen2.5-7B-Instruct added as benchmark baseline. D-008 rubric remains PROPOSED and candidate-0.1 unpublished. No selected model, business score or approved numeric threshold.
- **Pending gates:** GPU/driver/RAM/storage and air-gap inventory (OD-13, Infrastructure/Security), legal/artifact checksum manifest (Security/Legal/MLOps), three-domain synthetic/approved golden dataset and raters (OD-14, AI Lead/SMEs/Data Steward), throughput and latency SLO targets (OD-02/12, PO/SRE), actual vLLM/schema/quote/OOM/latency/quality measurements (PENDING_SERVER). Expert MAE currently NOT_MEASURABLE. Risk severity: critical for data egress/artifact integrity, high for missing hardware/quality baseline.
- **Stage 02 owners unchanged:** DI/Bootstrap tests Stage 04 NOT_RUN; PostgreSQL/transaction Stage 05 NOT_RUN; WebService discovery Stage 10 NOT_RUN. Stage 03 cannot use unverified runtime as a passing dependency.
- **Stage 03 acceptance:** BLOCKED until permitted internal execution has measured two model candidates in speech/media/research, quality, evidence, abstention, schema and VRAM/throughput/latency with reproducible manifests and approved decisions. Documentation QA alone is not empirical proof.
- **Next authorized stage:** none beyond Stage 03. Stage 04 requires a separate explicit user request and applicable gates/approvals.

- **Stage 03 offline validator:** The two `scripts/benchmark/*.py` files were tested in assistant sandbox with `py_compile` and 11/11 synthetic `unittest` cases PASS; this is NOT a benchmark, security/no-egress certification or real model compatibility test. See [Benchmark Protocol](../ai/02_benchmark_protocol.md) and [Result Ledger](../ai/03_benchmark_results.md).

### Stage 03 post-push evidence (2026-10-21)

- Post-push GitHub inspection and scope diff: **40/40** static/document checks PASS; baseline-to-head comparison reviewed **8 Stage 03 paths** (4 AI docs, 2 benchmark scripts, Decision Log/Tracker and Stage 02 ADR addendum). No `src/`, API, DB or production changes. This is documentation/source review, not integration or performance proof.
- Assistant isolated sandbox: `python -m py_compile` PASS; `unittest discover` 11/11 PASS (synthetic), validator CLI one synthetic record PASS with zero invalid. Committed GitHub source re-execution on user machine is `PENDING_USER_LOCAL`; server model benchmark remains `PENDING_SERVER`.

## 13. Stage 03 user-local QA results and Stage 02 checker regression (2026-10-21)

- **Verified user report on commit `88d56fdca17019fa7e85e9caf86171a4b1d3d486`:** successful `git pull --ff-only origin main`, matching `git rev-parse HEAD`, `python -m py_compile` without errors and `python -m unittest discover -s scripts/benchmark -p 'test_*.py' -v`: **11/11 PASS** (`Ran 11 tests in 1.691s`, `OK`). This is actual user-local validator code testing, not model quality or server performance proof.
- **Stage 02 checker (user-local on the same commit):** **18/19 PASS**. Only `stage tracker preserved` was `FAIL`. Confirmed root cause in `scripts/verification/check_stage02_docs.py`: the check still required Stage 03 `NOT_STARTED`, whereas explicit conditional authorization `D-016` legitimately made it `IN_PROGRESS`. Stage 02 `BLOCKED` is correct and unchanged.
- **Minimal remediation:** accept Stage 03 `IN_PROGRESS`/`BLOCKED`/`DONE` in the Stage 02 documentation checker **only when a confirmed D-016 decision row exists**, while preserving the required actual Stage 02 `BLOCKED` row. Retain historical `NOT_STARTED` support. Nine isolated synthetic regression tests of the new predicate passed; the full Stage 02 19-check Python suite on the post-fix user clone is `PENDING_USER_LOCAL` until actually rerun.
- **Working-tree note:** User-local `git status --short` showed only the untracked `scripts/benchmark/__pycache__/` created by Python compile/unittest. A root `.gitignore` now excludes Python bytecode/cache files; it does not delete local files or affect source/data.
- **Unchanged gate:** Stage 01 `DONE`; Stage 02 `BLOCKED` pending executable Stage 04/05/10 verification; Stage 03 `IN_PROGRESS` pending authorized GPU/dataset/model benchmark. No Stage 04 implementation authorized.

## 14. Stage 03 validator remediation and latest local QA (2026-10-24)

- **Latest user-local evidence (Git HEAD `f3c32c3043a63c4a304162f0834a716cb659dc60`):** `git pull --ff-only` fast-forwarded; `git rev-parse HEAD` matched; Stage 02 regression unit tests **9/9 PASS**, Stage 02 documentation checker **19/19 PASS**, Stage 03 synthetic validator tests **11/11 PASS**, and `git status --short` clean. This supersedes older `PENDING_USER_LOCAL` statements only for these specific tests and commit.
- **Post-audit Stage 03 fix:** Reject duplicate JSON properties, NaN/Infinity, float overflow and overly deep JSON with sanitized error codes. Enforce known synthetic case/domain alignment and fail closed on numerical `research_novelty` without verified corpus. Optional `--manifest` checks case/domain, exact UTF-8 text SHA-256 and disjoint group/source splits; it **does not certify** dataset authorization, expert validity or no-egress.
- **Assistant offline regression evidence:** 31/31 synthetic tests PASS in a sandbox for equivalent staged validator/test code, plus syntax compilation. GitHub-stored code is pushed and will be checked via GitHub read-back; full execution from the final user clone remains `PENDING_USER_LOCAL` until user runs commands and supplies results.
- **Decision status unchanged:** D-016 remains CONFIRMED conditional Stage 03 entry; D-006/007 model/runtime remain CANDIDATE, D-008 Rubric PROPOSED. Stage 02 BLOCKED due to DI/DB/WebService `NOT_RUN`, Stage 03 IN_PROGRESS and model choice BLOCKED pending authorized server benchmarks. Stage 04 not authorized.


## 15. Final Stage 03 review and evidence gate (2026-10-24)

- **User-local evidence on d1920bf98d519fbd9e19e494b249d1c1738d191d:** successful fast-forward, matching HEAD, Python compilation, Stage 03 validator 31/31 PASS, Stage 02 regression 9/9 PASS, Stage 02 document checker 19/19 PASS, and clean Git working tree. Total 59/59 checks, all `VERIFIED_USER_LOCAL` (not server AI benchmark).
- **Offline security remediation:** Confirm valid UTF-8 for user-supplied text fields and Manifest metadata to reject unpaired Unicode surrogates. Bound in-memory per-invocation manifest/attempt tracking at 100000 entries; fail closed with structured error. Seven new synthetic regression tests increased the Stage 03 suite to 38 tests, passing in isolated assistant runtime. Final user-local retest is `PENDING_USER_LOCAL`.
- **Stage 03 formal gate verdict: BLOCKED, not DONE.** No authorized GPU, on-prem model runs, measured three-domain quality, real expert annotations, capacity/VRAM/concurrency, verified artifact provenance or no-egress evidence. No approval to enter Stage 04. D-016 authorizes Stage 03 conditionally only; it does not waive Stage 03 gate. Keep Stage 02 BLOCKED; Stage 03 IN_PROGRESS with a BLOCKED acceptance gate.
- **Authorization boundary:** Stage 04 remains NOT_STARTED; do not start work without explicit request and satisfied applicable acceptance gates or a separately documented user-authorized conditional exception.

## 16. User-local verification of final Stage 03 offline fixes (2026-10-24)

- **Evidence source:** Actual user-provided PowerShell transcript for Git HEAD `663c1dbf211f51b29925d8f6c40d15f2605424fd`. `git pull --ff-only origin main` succeeded; `git rev-parse HEAD` matched the full SHA.
- **Executed tests — VERIFIED_USER_LOCAL:** `python -m py_compile` returned without error; `python -m unittest discover -s scripts/benchmark -p "test_*.py" -v` **38/38 PASS** (`Ran 38 tests in 3.923s`); `python -m unittest discover -s scripts/verification -p "test_*.py" -v` **9/9 PASS** (`Ran 9 tests in 0.395s`); `python scripts/verification/check_stage02_docs.py` **19/19 PASS** (`scope: Stage 02 documentation only`). Total **66/66 passed local checks** on this exact code snapshot.
- **Working tree:** `git status --short` yielded no output. The earlier `PENDING_USER_LOCAL` entries reflect historical snapshots and are superseded **for the named tests on this exact commit** by these actual results. A subsequent documentation-only evidence commit is not itself a second user-local execution.
- **Acceptance interpretation:** These tests prove only the covered offline validator behaviors and documentation checks. They **do not** establish AI accuracy, expert agreement, GPU/VRAM/latency/throughput, internal inference, license approval, data authorization or No-Egress. Stage 02 stays `BLOCKED` (deferred executable gates in Stage 04/05/10); Stage 03 stays `IN_PROGRESS` with acceptance `BLOCKED` and `PENDING_SERVER`; Stage 04 entry remains `NOT_APPROVED`. D-016 conditions unchanged.

## 17. Retrospective gate reassessment under D-017 (2026-10-24)

- **Normative basis:** revised Implementation Plan v1.1.0 §0.5, §9, §10 Stages 01–04 and D-015/D-017. Previous dated BLOCKED, IN_PROGRESS or NOT_APPROVED reports describe the historical gate and are superseded for current stage timing; their original observations are not deleted.
- **Stage 01 DONE / LOCAL_GATE_PASS:** Five mandatory baseline requirement/rubric/acceptance/security/decision artifacts exist, 25/25 documentation checks previously PASS; unresolved business approvals remain OPEN/PROPOSED, not fabricated.
- **Stage 02 DONE / LOCAL_GATE_PASS:** Five detailed architecture artifacts; repository source absence honestly documented; user-local Stage 02 documentation QA 19/19 PASS and checker regressions 9/9 PASS. DI/bootstrap remains a mandatory **local Stage 04** check, database/migration **Stage 05**, WebService discovery **Stage 10**; each remains NOT_RUN before implementation.
- **Stage 03 DONE / LOCAL_GATE_PASS:** Four AI documents and validator tests, candidate baseline/alternative, three-domain protocol, manifest, theoretical capacity plan. User-local Stage 03 unit/negative/regression 38/38 PASS plus compile PASS on `663c1dbf211f51b29925d8f6c40d15f2605424fd`. Unrun real inference/GPU/AI-quality/security work recorded in [Stage 11 Ledger](../ai/03_benchmark_results.md#12-d-017-deferred-on-premise-test-ledger), all DEFERRED_TO_STAGE_11, never PASSED.
- **Stage 04 entry APPROVED_FOR_REQUEST, but NOT_STARTED:** Separate explicit user instruction is required to begin Stage 04. No access to confidential data, server/Secrets/production is granted by this gate. Stage 11 real tests and Stage 12 release remain mandatory.
- **Verification boundary:** Existing local test evidence refers to code snapshot `663c1db`; documentation/checker changes made for D-017 need their own local retest before claiming tests run on the amended HEAD.

## 18. D-017 final local post-push regression evidence (2026-10-24)

- **VERIFIED_USER_LOCAL on exact commit `e9d6f1eb35a05c32ae6240733b9a3a5a8bda9c38`:** user PowerShell transcript confirms `git pull --ff-only origin main` fast-forward, matching `git rev-parse HEAD`, Stage 02 D-017 tracker regression suite **12/12 PASS** (`Ran 12 tests in 0.916s`), Stage 02 documentation checker **19/19 PASS**, and Stage 03 validator unit/negative/regression suite **38/38 PASS** (`Ran 38 tests in 3.072s`). Total **69/69 local checks PASS** and empty `git status --short`.
- **Stage gate verdict unchanged:** Stage 01 `DONE`, Stage 02 `DONE`, Stage 03 `DONE` under binding D-017 local-only gates. Stage 04 is `NOT_STARTED`, with **entry APPROVED_FOR_REQUEST** but *not execution authorized until a separate explicit request*. Stage 11 real on-premise test ledger remains `DEFERRED_TO_STAGE_11`, not `PASSED`.
- **Evidence boundary:** This report documents a user-executed test of **commit `e9d6f1e`**; this documentation-only follow-up commit is not claimed to have been rerun locally. No Python code, production system, or protected infrastructure was changed.


## Stage 04 — Infrastructure and Security Foundation (2026-10-24)

- **Actual GitHub baseline:** `4e14c2db36dcd7ac771c3ee554367fd9e3a34b88`, `main` public; source tree independently enumerated and confirmed to contain **no** production runtime, dependency manifest, DI, FastAPI or Vault implementation before the stage.
- **Status: `IN_PROGRESS`**, pending genuine local regression verification and a full transitive package vulnerability/license/SBOM/integrity audit. Local application foundation is operational, but this is not a production security certificate or organization IAM approval.
- **Implementation:** `src/host/app.py`, `src/application/web.py`, `src/infrastructure/{di,utils,security}/`, two appsettings files, exact-version dependency manifests, `tests/test_foundation.py` and stage-local static checker. No Stage 05–10 product, schema, repository, inference or worker features implemented.
- **Documentation:** [Threat Model](../security/01_threat_model.md), [Access Matrix](../security/02_access_matrix.md), [Environment Topology](../deployment/01_environment_topology.md), [Network and Secrets](../deployment/02_network_and_secrets.md), [Security Validation Report](../verification/04_stage04_security_validation.md), [Stage 11 Test Ledger](../verification/04_stage04_deferred_stage11_ledger.md).
- **Actual local checks (sandbox Python 3.13.5):** `PYTHONPATH=. python -m pytest -q tests/test_foundation.py` → `26 passed`; `PYTHONPATH=. python -m compileall -q src tests scripts` → PASS; `python scripts/verification/check_stage04_safety.py` → PASS for 9 runtime Python files / pins / selected secret patterns. Original Stage 02/03 tests **NOT_RUN** because checkout of existing GitHub scripts/docs was unavailable in isolated runtime; `python -m pip check` reported a preexisting shared-environment moviepy/Pillow conflict not specific to this repository.
- **Open:** `D-009..D-014` remain OPEN where applicable; SSO/claim mapping `OD-07`, encryption/Vault/audit/retention `OD-08`, SLO/DR `OD-12`, platform/network/model artifact `OD-13`, approval/licensing (Security/MLOps/Legal). Runtime pinning without transitive hash-locked provenance is incomplete.
- **Stage 11:** 10 separately owned server-only cases `S04-S11-01..10` are `DEFERRED_TO_STAGE_11`, with reason, required infrastructure/authorization and acceptance oracle. Stage 04 unexecuted local checks do **not** inherit this status.
- **Next stage:** Stage 05 not started and not automatically authorized while Stage 04 gate is open.


### Stage 04 follow-up: user-local regression evidence and port collision (2026-10-24)

PowerShell transcript after fast-forward to `ce2d389` shows a new Python 3.12 venv with successful install: **26/26** foundation pytest PASS (one non-fatal Starlette/AnyIO deprecation), **19/19** Stage 02 document checks PASS, **12/12** Stage 02 checker regressions PASS, **38/38** Stage 03 regressions PASS, Python compile PASS, Stage 04 static safety PASS and `pip check` PASS. These are **user-executed results**, not assistant-run results. The configured Windows port `127.0.0.1:8000` failed with `WinError 10048` after ASGI startup due to local port occupation; `APP_STOP` was observed and no Windows HTTP route verification occurred. Stage 04 status remains **IN_PROGRESS**, not DONE, because full transitive vulnerability/license/SBOM/integrity checks remain **NOT_RUN**. No stage later than 04 started. Details in [verification report](../verification/04_stage04_security_validation.md).


### Stage 04 follow-up: development port changed after two Windows bind conflicts (2026-10-24)

User evidence: port `8000` held by `com.docker.backend` PID `5552`; attempted `8001` also failed to bind (`WinError 10048`, owner unknown). Changed only **development** `src/host/res/appsettings.development.yaml` from `127.0.0.1:8000` to `127.0.0.1:18080`, updated development topology and ConfigReader regression assertion. Staging/production `appsettings.yaml` port `8000` unchanged, no real infrastructure changes. **Windows port 18080 bind/HTTP and rerun of modified test remain NOT_RUN** until user verification; do not infer PASS from earlier 8000 or 8001 failures. Full transitive vulnerability/SBOM/license/provenance gate remains OPEN; Stage 04 **IN_PROGRESS**, Stage 05 not authorized.


### Stage 04 follow-up: Windows development Uvicorn startup verified (2026-10-24)

User transcript after `git pull --ff-only origin main` fast-forward `ce2d389..f391461`: Python 3.12 development configuration now uses loopback port `18080`; `pytest -q tests/test_foundation.py` **26/26 PASSED** (one non-fatal deprecated alias warning); `python -m src.host.app` logged **APP_START**, **Application startup complete** and **Uvicorn running on http://127.0.0.1:18080** (PID 8896), with **no bind error**. Port 8000 previously held by Docker; 8001 bind also failed; neither was terminated or changed. The actual Windows GET requests to health endpoints are **NOT_RUN / awaiting user evidence**; earlier isolated assistant sandbox did receive HTTP 200, separately recorded. Supply-chain SBOM/license/vulnerability/provenance gate remains **NOT_RUN**, Stage 04 **IN_PROGRESS**, no Stage 05 action. See [Stage 04 validation](../verification/04_stage04_security_validation.md).

### Stage 04 follow-up: Windows development HTTP health confirmed (2026-10-24)

**Independent user-executed evidence:** From a separate PowerShell at the user's local project location while Uvicorn was listening on `127.0.0.1:18080`, `Invoke-RestMethod http://127.0.0.1:18080/health/live` returned `status: alive` and `Invoke-RestMethod http://127.0.0.1:18080/health/ready` returned `status: ready` (both without PowerShell HTTP errors). This closes the **Windows local bind + real HTTP health smoke verification** after the development-port correction. The response transcript did not independently include numeric HTTP status codes or production dependency checks; do not misrepresent readiness as DB/model/worker availability. No additional code changes or rerun are claimed. Full dependency SBOM, vulnerability/license approval and artifact integrity/provenance review remain **NOT_RUN** and are still a Stage 04 local acceptance gate. Stage 04 remains **IN_PROGRESS** and Stage 05 remains **NOT_STARTED**. See [Stage 04 security validation](../verification/04_stage04_security_validation.md).


### Stage 04 independent readiness review and remediation (2026-10-24)

Reviewed mandatory architecture guide and implementation plan Stage 04, plus complete current `main` tracked tree and runtime sources. **Gate verdict: NO_GO_STAGE_05; Stage 04 stays IN_PROGRESS.** Findings: prior FastAPI 0.128.2 resolved known-vulnerable Starlette 0.50.0 (CVE-2026-54283, HIGH); `is_allowed` permitted organization-admin and metrics actions without ResourceScope; `configure_logging` trusted preexisting unsafe handler formatters; URL parser accepted control characters after normalization; no auditable local installed dependency inventory. Remediated Stage 04 only: direct pinned `fastapi==0.148.0`, `starlette==1.9.0`, test-only `httpx2==2.16.0`; tenant-scoped permission checks; all app logger handlers have SafeFormatter; strict internal endpoint lexical validation; offline installed RECORD SHA256 and license-metadata inventory with review-required statuses; regression test and CVE pin guard. **11/11 new isolated local tests PASS**; compile and static guard PASS on only modified source subset. **Full original 26 tests and updated dependency resolution smoke NOT_RUN after upgrade**; prior Windows 26 tests, health checks and Stage 02/03 regressions remain historic evidence on old dependency graph. No SCA, license clearance, upstream artifact hash/provenance or CycloneDX SBOM approval performed. Corporate-only tests remain Stage 11 per D-017; Stage 05 not started. See [independent review](../verification/04_stage04_independent_review.md).


### Stage 04 follow-up: FastAPI 0.148 route-tree test compatibility (2026-10-24)

Actual user-executed fresh Windows 3.12 install of `fastapi==0.148.0`, `starlette==1.9.0`, `httpx2==2.16.0` succeeded; `pip check` PASS. Full pytest: **35/37 PASS, 2 FAIL** because two previous tests accessed `app.routes[*].path` (no longer valid with `_IncludedRouter`). Compilation and safety checks PASS, Stage 02 docs 19/19 PASS, Stage 02 checker unit tests 12/12 PASS, Stage 03 benchmark tests 38/38 PASS; 27 installed dependency components inventoried (metadata only; no accepted CVE/license/approved SBOM). Modified **only** `tests/test_foundation.py` to check absent routes and synthetic discovered nested controller via `TestClient` rather than internal `.path`; **post-commit upgraded full suite NOT_RUN** until fresh user-local evidence. An attempted second Uvicorn bind on 18080 failed `WinError 10048`, owner not identified in this run; prior health HTTP success belongs to an earlier run. Supply chain acceptance gate remains OPEN and Stage 04 `IN_PROGRESS`. See [security validation](../verification/04_stage04_security_validation.md).


### Stage 04 follow-up: all 37 updated tests PASS and OS-assigned port startup (2026-10-24)

**User-executed Windows Python 3.12 evidence on latest main (`e16c5d642850ec06c17596176ca003cbf2fdd924`):** `git pull --ff-only origin main` returned `Already up to date`; in an existing `.venv-review` where FastAPI 0.148.0 / Starlette 1.9.0 / httpx2 2.16.0 were previously installed, `python -m pytest -q tests` returned **37 passed, 0 failed, 0 skipped in 10.21s** and `python -m pip check` returned **No broken requirements found**. This **closes the prior two route compatibility regressions** through direct user-local evidence. No assistant-side rerun of the complete upgraded environment is claimed.

Port investigation: `Get-NetTCPConnection -LocalPort 18080 -State Listen` returned PID **8896**, process `python` (previously observed app process 8896; command line still not independently inspected). No process was terminated. Running `python -m uvicorn src.host.app:app --host 127.0.0.1 --port 0 --no-access-log` started PID **13500** and logged `APP_START`, `Application startup complete`, `Uvicorn running on http://127.0.0.1:50165`; **PASS_USER_LOCAL ephemeral bind/startup**. User has not supplied `GET /health/live` or `GET /health/ready` response for **50165**; mark **NOT_RUN_ON_EPHEMERAL_PORT**. Previous real Windows HTTP health checks on development port 18080 were already PASS and remain valid for that earlier run, not necessarily for the new venv.

**Remaining local Gate:** inventory of 27 installed Python packages is metadata-only; independent vulnerability/advisory audit, SPDX/CycloneDX SBOM, package wheel checksum/provenance verification and license policy review remain incomplete / **NOT_RUN**. Stage 04 stays **IN_PROGRESS** and Stage 05 **NOT_APPROVED / NOT_STARTED**. Under D-017 real corporate network / SSO / Vault security cases remain **DEFERRED_TO_STAGE_11**. No production action or Stage 05 code was executed.


### Stage 04 follow-up: real HTTP endpoints confirmed on upgraded dependency environment (2026-10-24)

**User-provided independent Windows PowerShell evidence** from the locally running Uvicorn process on `127.0.0.1:50165` (previously logged as Python PID 13500, `.venv-review`, FastAPI 0.148.0 and Starlette 1.9.0):

```powershell
Invoke-RestMethod http://127.0.0.1:50165/health/live
# status: alive
Invoke-RestMethod http://127.0.0.1:50165/health/ready
# status: ready
```

Both completed without PowerShell errors. **LIVE_HTTP_HEALTH = PASS_USER_LOCAL**, supplementing earlier **37/37 pytest PASS**, `pip check` PASS and Uvicorn bind/startup on the same local environment. Numeric HTTP status values were not directly included in the PowerShell formatting; no other endpoints are claimed verified. Static readiness tests only the Stage 04 FastAPI bootstrap/lifespan, not Database, Worker or inference. **Full dependency vulnerability scan, approved license analysis, standardized SBOM, upstream artifact integrity and provenance remain NOT_RUN/OPEN**; Stage 04 stays `IN_PROGRESS` and Stage 05 `NOT_STARTED / NOT_APPROVED`. Corporate security and infrastructure tests remain `DEFERRED_TO_STAGE_11` under D-017. No business content or protected infrastructure was used.


### Stage 04 supply-chain evidence tooling completion attempt (2026-10-24)

**Scope restricted to Stage 04** by explicit user request; no DB/migration, model provider, worker, real corporate network or Stage 05 feature. New files: `requirements-audit.txt` (dedicated pinned auditor tools), `scripts/verification/review_stage04_supply_chain.py` (offline deterministic evidence validator and exact dependency closure/wheel manifest), `scripts/verification/run_stage04_supply_chain.ps1` (Windows target-environment evidence collector), `tests/test_review_stage04_supply_chain.py` (synthetic negative tests), `docs/verification/04_stage04_supply_chain_runbook.md` (security runbook); updated `.gitignore` and security/architecture documentation. 

**Actually executed in assistant isolated Python 3.13.5 runtime:** **15/15 new tests PASS**, `compileall` PASS, synthetic fail-closed checks for reported CVEs, partial CVE audit, missing/wrong SBOM, missing licenses/reviewer/license expression, wheel tampering/duplicates, PyPI SHA mismatch and no-network freeze; existing unrelated 37/37 Windows pytest and health PASS remain separately evidenced on commit `e16c5d6`. This runner cannot reach PyPI and uses old FastAPI, so **full new Windows combined suite NOT_RUN**, actual `pip-audit` scan `NOT_RUN`, target-venv CycloneDX `NOT_RUN`, 27 downloaded wheel hashes + public PyPI digests `NOT_RUN`, manual license review `OPEN`. No complete supply-chain Gate PASS is claimed. NVD desk review confirms prior Starlette CVE affects versions below 1.3.1; currently selected 1.9.0 is outside its declared affected range, **not** a whole-closure vulnerability scan.

**Result:** Foundation local security/test gates remain previously PASS, with newly tested evidence tooling; missing external advisory/approved-wheel/license evidence means Stage 04 `IN_PROGRESS`, **Stage 05 entry NOT_APPROVED**. Real company-only security tests continue `DEFERRED_TO_STAGE_11` per D-017 and formal employer sign-off remains Stage 12 under D-015. Next Windows step is the audited, opt-in public-package-metadata-only procedure in [Stage 04 supply-chain runbook](../verification/04_stage04_supply_chain_runbook.md). The user must expressly request Stage 05 after the Gate closes.


### Stage 04 user-local 52-test proof and PowerShell collector policy block — 2026-10-24

User-supplied PowerShell after `git pull --ff-only origin main` fast-forward `e16c5d6..684f486`: `.\\.venv-review\\Scripts\\python.exe -m pytest -q tests` **52 passed in 35.24s**, confirming 15 newly added supply-chain validator tests plus previously verified 37 Stage 04 tests in one Windows Python 3.12 environment. The attempt to invoke `run_stage04_supply_chain.ps1` with `-VerifyPublicPyPIDigests` failed *before script execution* due to system script execution policy (`PSSecurityException`). This is **BLOCKED_EXECUTION_POLICY**, not a Python/runtime failure; **actual CVE scan, approved SBOM, upstream wheel integrity/digest evidence and license decisions are NOT_RUN**, with no generated successful artifact claimed. [Runbook](../verification/04_stage04_supply_chain_runbook.md#windows-powershell-executionpolicy-preflight-2026-10-24) includes a nonpersistent `RemoteSigned` invocation only where local organizational policy permits it. Stage 04 remains `IN_PROGRESS`, Stage 05 entry `NOT_APPROVED`. Stage 11 server tests still deferred per D-017.


### Stage 04 follow-up: PowerShell site-packages argument quoting defect corrected (2026-10-24)

The user's `Get-ExecutionPolicy -List` showed **all Undefined**, and the one-off `RemoteSigned` process launched `run_stage04_supply_chain.ps1`. **`pip check` PASS**, then native argument handling turned `sysconfig.get_paths()["purelib"]` into an expression with undefined name `purelib`; the script exited with **NameError** prior to the dependency audit, SBOM, package wheel, PyPI digest or license review. Engineering corrected the collector to get target interpreter purelib via a dedicated `review_stage04_supply_chain.py site-packages` subcommand and to create the evidence directory after successful preflight. **17/17 isolated supply-chain Python tests PASS**, Python compile PASS; Windows rerun **PENDING_USER_LOCAL**. The prior evidence directory must be preserved; use a new unused suffix. Full 52/52 user-local suite PASS is from the previous commit, **not** this latest change. Supply-chain acceptance **NOT_RUN / OPEN**, Stage 04 **IN_PROGRESS**, Stage 05 **NOT_STARTED / NOT_APPROVED**, internal server cases **DEFERRED_TO_STAGE_11**.
