# Open Decisions, Decision Log and Stage 01 Progress

> **Date:** 2026-10-21 · **Status:** `BLOCKED_FOR_APPROVAL` (Stage Progress Tracker equivalent `BLOCKED` after draft preparation).  
> **No invented approvals:** OPEN/PROPOSED/CANDIDATE are not CONFIRMED. Generic roles below are proposed approval responsibilities, not verified employer identities.  
> **Sources:** Implementation Plan §§0,3,4,6,7,10/Stage 01,13–14; Architecture Guide; explicit project instructions.

## 1. Decisions inherited from approved/proposed baseline (D-001..D-014)

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

**Important:** D-004 is a confirmed **process rule**, not business approval of proposed rubric or topology. This catalog makes no further D-XXX item CONFIRMED.

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
| `OD-16` | P1 | Stage 01 formal sign-off | چه فرد/گروهی اسناد Requirements، هر Rubric، سیاست محرمانگی، AC و decision ownership را به‌صورت رسمی امضا می‌کند؟ | Employer/Product Owner + SMEs + Security Officer | Stage 01 Gate; Stage 02 not authorized until written approval | `OPEN` |

Priority definitions: **P0** gates a reliable/secure specification or official scoring; **P1** impacts optional scope or implementation specifics and must be resolved before implementing the affected capability. P0 does not mean all draft-writing work must halt. The actual employer sign-off gate is `OD-16`.

## 3. Required approval package and decision recording

**Product Owner:** sign exact input/business scope (`OD-01/02/05/06/15`), workload targets (`OD-12`) and final baseline (`OD-16`).  
**Three domain SMEs:** review all 18 rubric definitions/weights/anchors and `required` statuses, applicability and abstention (`OD-03/04/09`).  
**Security/IAM/Data Steward:** approve roles/scope, data classification, retention/deletion/encryption, no-egress architecture and dataset access (`OD-07/08/13/14`).  
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
| 01 | Requirements & Acceptance | `BLOCKED` / `BLOCKED_FOR_APPROVAL` | Draft specifications in `docs/requirements/01_..05_`; formal employer/SME/Security sign-off missing. Technical document checks are recorded in Stage report, not implied by file existence. |
| 02 | Repository & Detailed Architecture | `NOT_STARTED` | Not authorized as a stage |
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

**Stage 01 technical deliverables:** [Product FR/NFR](01_product_requirements.md) · [Candidate Rubrics](02_evaluation_rubrics.md) · [Acceptance Matrix](03_acceptance_criteria.md) · [Security/Data Policy](04_security_and_data_policy.md) · this file (Decision Log/Tracker). The Stage 01 validation report must distinguish structural document tests from product test execution. Stage 01 is **not DONE**.

**Acceptance Gate:** Written sign-off of Requirements Baseline + approval responsibility for all Open Decisions is still outstanding. No Stage 02 implementation is authorized merely by writing these documents. If official approval is missing, report `BLOCKED_FOR_APPROVAL`.

## 6. Stage 01 tracking record (provisional, updated upon validation)

- Date: 2026-10-21
- Source documents reviewed: `Service_Architecture_Guide_FA.md`, `Text_Evaluation_Service_Implementation_Plan_FA.md` v1.0.0 (provided in Project Sources; not edited there).
- GitHub repository at start: public, empty, `main` without initial commit; confirmed via GitHub API 409. Documentation-only initialization performed as separate Conventional Commits.
- Files: five `docs/requirements/*.md` Stage 01 artifacts; no application code, migration, secrets or production changes.
- Tests: automated Stage 01 document coverage/link/consistency/security scan to be recorded after actual execution. Product/GPU/security runtime tests `NOT_RUN` / `PENDING_SERVER`.
- Approval: `OD-16 OPEN`. Remaining values OPEN and candidates not Published.
- Project Sources synchronization: Source document's original Progress Tracker remains `NOT_STARTED` unless independently updated; GitHub file here is the evidence-backed Stage 01 update. **Manual synchronization or authoritative pointer change is needed.**
- Next stage: none without explicit user request and stage gate sign-off.

## 7. Approval questions for the employer (prioritized)

1. Who formally approves Product Requirements, the three domain Rubrics and Security/Privacy rules (`OD-16`)?
2. Will the three SME representatives approve each criterion/weight/anchor/`required`, or provide annotated changes (`OD-03`)?
3. What threshold/rounding/abstention and human-review policy must govern official scores (`OD-04/09`)?
4. Which organization IAM, org boundary, classification/retention/deletion and encryption policy is authoritative (`OD-07/08`)?
5. Which text/file/language scope, volume, SLO/RPO/RTO and hardware/inference boundary can be approved (`OD-01/02/12/13`)?
6. Who owns the Golden Dataset, adjudication, holdout access and AI quality acceptance thresholds (`OD-14`)?

Further detail and rationale: [01_product_requirements.md](01_product_requirements.md), [02_evaluation_rubrics.md](02_evaluation_rubrics.md), [03_acceptance_criteria.md](03_acceptance_criteria.md), [04_security_and_data_policy.md](04_security_and_data_policy.md).
