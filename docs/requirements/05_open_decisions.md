# Open Decisions, Decision Log and Stage 01 Progress

> **Date:** 2026-10-21 · **Stage 01 status:** `DONE` (internal documentation gates PASSED; cleared for Stage 02 on explicit user request). Employer acceptance deferred to Stage 12 under `D-015`.  
> **No invented approvals:** OPEN/PROPOSED/CANDIDATE are not CONFIRMED. Generic roles below are proposed approval responsibilities, not verified employer identities.  
> **Sources:** Implementation Plan §§0,3,4,6,7,10/Stage 01,13–14; Architecture Guide; explicit project instructions.

## 1. Decision Log (D-001..D-015)

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

**Important:** D-004 and D-015 are confirmed **project execution rules**, not business approval of any rubric, policy, topology or numerical target. All other previously unconfirmed choices remain OPEN/PROPOSED/CANDIDATE.

### Approval timing — binding project execution amendment (`D-015`)

- **Stages 01–11:** No employer/customer signature or formal SME approval is required merely to close a *stage*. Close a stage only when its applicable **internal technical deliverables, executable verification, security gates and known-risk records** are complete. Unimplemented or untested work must not be marked `PASSED` or `DONE`.
- **Stage 12 (final delivery):** Seek consolidated formal employer/authorized SME acceptance of business scope, Rubrics, measurable quality, security/privacy documentation and the final product, after real evidence from prior stages is available. Do not call the product `Production-Ready` without final Gates and sign-off.
- **Unresolved business settings:** Keep each OPEN with a proposed, versioned, clearly non-final design path. Implement/test candidates using permitted synthetic data where feasible; do not represent provisional weights, thresholds, scope or decisions as approved, or publish official enterprise grades before final acceptance.
- **Irreducible safety/permission prerequisites:** Authorization to use real confidential data, security controls, use of protected infrastructure, secret changes, destructive operations and Production deployment remain mandatory **before those specific actions**. These are not customer acceptance sign-offs for ordinary stage completion.
- **Progression:** Each next stage still requires a **new explicit request from the user** and a satisfied internal gate. Stage 01's internal documentation gaps were remedied and validated (`DONE`); missing employer signature is **not** a gate. Stage 02 has started on explicit user request; architecture documents are prepared, but the technical compatibility gate is **BLOCKED** because no executable repository source exists.
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
| 02 | Repository & Detailed Architecture | `BLOCKED` | Five design documents and API contracts validated; tracked Git tree (11 entries) verified from user local output. Original docs QA 18/18 PASS; after adding DTO field test, user reported 18/19 with only `uncertainty disclosed` FAIL caused by obsolete `NOT_VERIFIED` string assertion. The checker has been fixed to distinguish `VERIFIED_USER_LOCAL` Git tree from `NOT_RUN` import/bootstrap and `UNVERIFIABLE` dependency versions. Full 19/19 rerun on the corrected commit PENDING_USER_LOCAL. Runtime DI/Bootstrap compatibility BLOCKED/NOT_RUN; Stage 03 not authorized. |
| 03 | Local Model Benchmark | `NOT_STARTED` | `PENDING_SERVER` for real model/GPU tests; no benchmark claim |
| 04 | Infrastructure & Security | `NOT_STARTED` | No egress/recovery tests performed |
| 05 | Database & Migration | `NOT_STARTED` | No DB/migration changes |
| 06 | Rubric Management | `NOT_STARTED` | No published rubric or code |
| 07 | Local LLM Provider | `NOT_STARTED` | No model/inference integration |
| 08 | Evaluation Engine | `NOT_STARTED` | No scoring code |
| 09 | Durable Worker & Queue | `NOT_STARTED` | No worker/queue code |
| 10 | API & Authorization | `NOT_STARTED` | No HTTP endpoints or Auth integrations |
| 11 | Full Verification & Calibration | `NOT_STARTED` | `PENDING_SERVER` for AI/Load/Security/Recovery tests |
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
