# Stage 02 — File Change Matrix (future stages only)

> Status: PROPOSED_FILE_PLAN | Date: 2026-10-21 | Source baseline: GitHub main 924fd3c91f680b00c27533bae9fc0c59e70c6e8c
>
> این سند تغییر هیچ‌کدام از مراحل 03 تا 12 را اجرا نمی‌کند. تمام pathهای Runtime فهرست‌شده Target هستند، نه سورس مشاهده‌شده. ردیف‌های «NO» به معنی مسیر proposed/not found in inspected main است، نه آنکه تمامی دایرکتوری‌های احتمالی جهان از Git tree به‌طور کامل Enumerate شده باشند.

## Matrix and execution sequence

| Path | Layer | Responsibility | Exists? | Create/Modify | Dependencies | Related Stage | Related FR/NFR | Risk | Test Strategy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/ai/01_model_selection.md | Docs | model/license candidate comparison | NO | Create | approved benchmark inputs | 03 | FR-10 NFR-08/11 | unlicensed model | license/selection peer review |
| docs/ai/02_benchmark_protocol.md | Docs | synthetic/authorized dataset and metrics protocol | NO | Create | OD-03/14 | 03 | FR-02/04 NFR-08/13 | data leakage | protocol/holdout review |
| docs/ai/03_benchmark_results.md | Docs | actual metric evidence | NO | Create | internal GPU/dataset | 03 | FR-04/11 NFR-05/08 | unsupported accuracy | real benchmark PENDING_SERVER |
| docs/ai/04_inference_resource_plan.md | Docs | capacity measured plan | NO | Create | OD-12/13 model candidate | 03 | FR-07/10/11 NFR-06 | GPU undersizing | GPU/throughput results |
| src/host/app.py | Host | FastAPI startup and graceful shutdown | NO | Create | bootstrap DI + WebService | 04 | FR-01/08 NFR-14 | startup failure | import/lifespan smoke |
| src/host/res/appsettings.yaml | Host | production-agnostic non-secret settings | NO | Create | ConfigReader; OD-13 | 04 | FR-10 NFR-01/11 | secret/config leak | config schema/no secret scan |
| src/host/res/appsettings.development.yaml | Host | safe local development settings | NO | Create | ConfigReader; synthetic env | 04 | FR-01/10 NFR-11 | credential commit | config scan |
| src/application/web.py | Application | WebService feature route discovery | NO | Create | ConfigReader + DI | 04 | FR-01/08 NFR-14 | route skip/collision | discovery/route smoke |
| src/infrastructure/di/inject.py | Infrastructure | @inject constructor resolver | NO | Create | DI contract reference guide | 04 | FR-01/07 NFR-14 | incorrect scope | inject/signature tests |
| src/infrastructure/di/reflection.py | Infrastructure | provider package scan and exclusion | NO | Create | inject bootstrap | 04 | FR-01 NFR-14 | silent missing provider | missing-module/failure tests |
| src/infrastructure/di/bootstrap.py | Infrastructure | bootstrap_di ordered scan | NO | Create | inject/reflection | 04 | FR-01/07 NFR-14 | bootstrap race | idempotent bootstrap test |
| src/infrastructure/utils/config_reader.py | Infrastructure | typed settings provider | NO | Create | host appsettings | 04 | FR-10 NFR-01/11 | unsafe defaults | config resolution tests |
| src/infrastructure/context/vault/vault_service.py | Infrastructure | approved internal secret resolution | NO | Create conditionally | OD-08/13 available Vault | 04 | FR-10 NFR-03 | credential disclosure | secret/redaction tests |
| requirements.txt | Build | runtime dependency declarations and pins | NO | Create (format subject to tooling decision) | actual chosen Python/runtime | 04 | FR-01/10 NFR-11/14 | unvetted dependencies | lock/install/SCA tests |
| Dockerfile | Deploy | approved build packaging candidate | NO | Create conditionally | OD-13 deployment choice | 04 | FR-10 NFR-11 | unsafe image | offline startup/scan |
| docs/security/01_threat_model.md | Docs | network trust and threat analysis | NO | Create | OD-07/08/13 | 04 | FR-08/10 NFR-01/02 | missing trust edge | security review |
| docs/security/02_access_matrix.md | Docs | approved/conditional identity scope roles | NO | Create | OD-07 | 04 | FR-08/09 NFR-02 | IDOR | role matrix review |
| docs/deployment/01_environment_topology.md | Docs | verified approved infrastructure | NO | Create | OD-13 | 04 | FR-10 NFR-01/11 | wrong boundary | network review |
| docs/deployment/02_network_and_secrets.md | Docs | network no-egress and secret policy | NO | Create | OD-08/13 | 04 | FR-10 NFR-01/03 | egress | PENDING_SERVER packet checks |
| src/infrastructure/context/sql_db/psql_dbcontext.py | Infrastructure | shared engine/session factory | NO | Create | SQLAlchemy async, ConfigReader | 05 | FR-03/07 NFR-10/14 | session leakage | integration/session lifecycle |
| src/infrastructure/repositories/base/base_repository.py | Infrastructure | generic per-operation CRUD | NO | Create | PsqlDbContext | 05 | FR-03/08 NFR-14 | implicit early commit | rollback CRUD tests |
| src/infrastructure/models/evaluation.py | Infrastructure | scoped evaluation data and revisions | NO | Create | SQLAlchemy Base and OD-08 | 05 | FR-01/08/12 NFR-02/03 | cross-org exposure | FK/scope integration |
| src/infrastructure/models/evaluation_job.py | Infrastructure | job lease/fence/attempt state | NO | Create | evaluation model | 05 | FR-07 NFR-10 | stale worker write | constraints/CAS tests |
| src/infrastructure/models/rubric_version.py | Infrastructure | immutable rubric snapshots | NO | Create | SQLAlchemy Base | 05 | FR-02/03 NFR-09 | in-place mutation | immutability tests |
| src/infrastructure/models/criterion_result.py | Infrastructure | per-criterion score/evidence persistence | NO | Create | evaluation + rubric | 05 | FR-04/05/06 NFR-09 | duplicate result | unique/FK/integrity tests |
| src/infrastructure/models/evaluation_feedback.py | Infrastructure | reviewer corrections and revisions | NO | Create | evaluation + identity scope | 05 | FR-09 NFR-02/09 | unauthorized revision | append audit tests |
| src/infrastructure/models/audit_event.py | Infrastructure | sanitized audit row only if DB sink approved | NO | Create conditionally | OD-08 audit sink choice | 05 | FR-09/12 NFR-09 | raw content in audit | sensitive-field tests |
| src/infrastructure/repositories/text_evaluation/evaluation_repository.py | Infrastructure | scoped queries and atomic create/finalize | NO | Create | models + DB context | 05 | FR-01/04/07/08 NFR-02/10 | non-atomic write | transaction/race tests |
| src/infrastructure/repositories/text_evaluation/evaluation_job_repository.py | Infrastructure | claim/heartbeat/reclaim and fence | NO | Create | job model, D-005 decision | 05/09 | FR-07 NFR-10 | duplicate commit | multi-worker integration |
| src/infrastructure/repositories/text_evaluation/rubric_repository.py | Infrastructure | published rubric select and locking | NO | Create | rubric model | 05/06 | FR-02/03 NFR-09 | wrong version | version/scope tests |
| src/infrastructure/repositories/text_evaluation/feedback_repository.py | Infrastructure | append scoped feedback if necessary | NO | Create conditionally | feedback model, OD-06 | 05/10 | FR-09 NFR-02 | audit gaps | scoped insert tests |
| src/infrastructure/alembic/env.py | Infrastructure | register all model metadata | NO | Create | DB context and models | 05 | FR-03/07 NFR-14 | missing metadata | migration smoke |
| src/infrastructure/alembic/versions/<revision>_*.py | Infrastructure | versioned schema evolution placeholder pattern only | NO | Create concrete filename only after migration generation | alembic env/models | 05 | FR-03/07 NFR-14 | unsafe migration | upgrade on empty/test DB |
| src/infrastructure/scripts/run_migrations.py | Infrastructure | controlled nonproduction migration runner | NO | Create if reference runner adopted | alembic, OD-13 | 05 | FR-03 NFR-14 | accidental production migration | safe args/smoke |
| src/core/services/text_evaluation/rubric_service.py | Core | resolve and publish scoped immutable rubric | NO | Create | RubricRepository + OD-03 | 06 | FR-02/03 NFR-09 | rubric drift | published snapshot tests |
| src/infrastructure/providers/llm/local_llm_provider.py | Infrastructure | internal-only inference transport | NO | Create | Stage03 runtime selection; Stage04 security | 07 | FR-10/11 NFR-01/11 | egress/timeout | local contract and leak tests |
| src/core/services/text_evaluation/text_preprocessing_service.py | Core | Persian Unicode mapping/long text sections | NO | Create | OD-02/11 | 08 | FR-11/04 NFR-12 | span offset corruption | Unicode/ZWNJ tests |
| src/core/services/text_evaluation/criterion_evaluation_service.py | Core | rubric-aware criterion evaluation + evidence | NO | Create | RubricService + LocalLlmProvider | 08 | FR-04/06 NFR-08 | fabricated quote | schema/quote tests |
| src/core/services/text_evaluation/scoring_service.py | Core | Decimal Python score and coverage | NO | Create | OD-04 policy | 08 | FR-05/06 NFR-08 | invalid final score | property-based scoring tests |
| src/core/services/text_evaluation/text_evaluation_service.py | Core | evaluate submit/report use-case boundary | NO | Create | evaluation/rubric repositories | 08/10 | FR-01/08/12 NFR-02 | authorization bypass | service flow tests |
| src/core/services/text_evaluation/evaluation_worker_service.py | Core | job processor, retry, fenced finalize | NO | Create | EvaluationJobRepository + scoring | 09 | FR-07/12 NFR-10 | crash recovery | lease/fencing tests |
| src/host/evaluation_worker.py | Host | worker process composition root | NO | Create | bootstrap DI + worker service | 09 | FR-07 NFR-10 | stuck shutdown | startup/drain smoke |
| src/application/text_evaluation/text_evaluation_controller.py | Application | thin FastAPI endpoints | NO | Create | TextEvaluationService, @inject | 10 | FR-01/08/09 NFR-02 | IDOR/route collision | HTTP/auth smoke |
| src/application/text_evaluation/dtos/text_evaluation_dto.py | Application | Pydantic request/report/error DTOs | NO | Create | Stage02 contracts, approved policies | 10 | FR-01/04/06/08 NFR-12 | invalid data leaks | schema/validation tests |
| docs/verification/01_test_strategy_and_traceability.md | Docs | FR/NFR complete test evidence | NO | Create | stages 03..10 | 11 | FR-01..12 NFR-01..14 | coverage gaps | traceability audit |
| docs/verification/02_software_test_results.md | Docs | unit/integration/migration/E2E results | NO | Create | app code and tests | 11 | FR-01/07/08 NFR-10/14 | untested code | CI artefact evidence |
| docs/verification/03_ai_quality_report.md | Docs | holdout domain quality evidence | NO | Create | golden dataset authorized | 11 | FR-02/04/06 NFR-08/13 | quality overclaim | PENDING_SERVER benchmark |
| docs/verification/04_security_and_privacy_report.md | Docs | IAM/IDOR/no-egress evidence | NO | Create | Stages04/10 | 11 | FR-08/10 NFR-01/02 | data exfiltration | PENDING_SERVER security |
| docs/verification/05_performance_and_recovery_report.md | Docs | load/restore/GPU and queue results | NO | Create | Stage03/09 infrastructure | 11 | FR-07/11 NFR-04/05/07 | lost data | PENDING_SERVER soak/restore |
| docs/verification/06_release_blockers.md | Docs | open critical defects and risk acceptance | NO | Create | verification results | 11 | FR-12 NFR-14 | hidden blockers | gate review |
| docs/release/01_release_manifest.md | Docs | versioned exact approved artifact list | NO | Create | Stage11 pass and approvals | 12 | FR-12 NFR-11 | unreproducible release | checksum verification |
| docs/release/02_deployment_and_rollback.md | Docs | authorized rollout/rollback | NO | Create | OD-08/12/13 | 12 | FR-07/12 NFR-07 | production outage | staging rehearsal |
| docs/operations/01_runbook.md | Docs | incident/stuck job/model failure playbooks | NO | Create | Stage09/11 evidence | 12 | FR-07 NFR-04/07 | unrecoverable service | runbook drill |
| docs/operations/02_monitoring_and_alerting.md | Docs | safe metrics/alerts and ownership | NO | Create | OD-12 SLO | 12 | FR-07 NFR-04/09 | sensitive telemetry | alert simulation |
| docs/operations/03_backup_restore_and_retention.md | Docs | approved data/backup lifecycle | NO | Create | OD-08/12 | 12 | FR-08/09 NFR-03/07 | data loss | restore drill |
| docs/handover/01_production_acceptance.md | Docs | final SME/customer signoff D-015 | NO | Create | all gates and OD-16 | 12 | FR-01..12 NFR-01..14 | premature release | signed acceptance review |

## Dependencies, scope constraints and verification

- Stage 03 فقط Benchmark در زیرساخت **مجاز** با داده synthetic/approved است؛ نتایج Performance یا Quality فعلاً PENDING_SERVER.
- Stage 04 باید minimum platform foundation + DI/Discovery واقعی را بر اساس reference ایجاد و Smoke Test کند. لیست src/infrastructure/di با فایل‌های فعلی در GitHub اشتباه گرفته نشود؛ آن‌ها غایب‌اند.
- Stage 05 ابتدا DB context/BaseRepository و سپس Model/Repository/Migration را می‌سازد؛ transaction extension تنها پس از مشاهده کد و تست/ADR. نام revision Alembic تا زمان generation واقعی معلوم نیست؛ الگوی <revision>_* نام فایل واقعی نیست.
- Stage 06/07/08/09/10 به‌ترتیب Versioned Rubric، Provider داخلی، Engine، Worker، API را می‌سازند. هیچ‌یک در Stage 02 پیاده نشده است.
- Stage 11 و Stage 12 شامل اسناد تست و تحویل هستند؛ تمام تست‌های واقعی باید در Stage مالک اجرا شوند؛ نتیجه سند جایگزین آزمون نمی‌شود.
- R-13: مخزن عمومی است؛ Deployment/Threat Models/AI artifacts باید قبل از commit از نظر محرمانگی بررسی شوند. مسیرهای conditional تنها پس از تعیین OD-07/08/13 یا معماری آزموده‌شده قابل تثبیت‌اند.
- Test files از ابتدا در Stageهای مالک Feature لازم‌اند، ولی چون **هیچ Test Framework موجودی مشاهده نشده** مسیر قطعی tests/ به‌عنوان Exists یا standard فعلی تعیین نمی‌شود؛ Stage 04/05 convention را تعریف و بعد مسیرهای واقعی تست به Matrix اضافه می‌کند.
- CI path نیز هنوز تأیید نشده؛ انتخاب .gitlab-ci.yml یا .github/workflows/... فقط پس از بررسی محیط/توافق خواهد بود، نه به‌عنوان فایل ساخته‌شده.
- تمامی مسیرها تحت استاندارد src.* imports، feature naming، @inject، controller api(), BaseRepository reuse و Alembic metadata registration هستند؛ Admin/Export/Delete/Cancel بدون OD-05/06 در Matrix برنامه build ندارند.

## FR/NFR traceability crosswalk

| Requirements | Planned components / stages | Verification gate |
|---|---|---|
| FR-01 FR-02 FR-03 | API DTO/Controller, RubricService, models; 05/06/10 | validation, immutable snapshot |
| FR-04 FR-05 FR-06 | CriterionEvaluationService, ScoringService, DTO; 08/10 | evidence, abstention, score properties |
| FR-07 | job model/repository, worker; 05/09 | concurrent claims, crash/retry/fencing |
| FR-08 FR-09 | scoped repo, Controller, feedback, audit; 05/10 | IDOR/auth/audit tests |
| FR-10 FR-11 FR-12 | LocalLlmProvider, text processing, release metadata; 03/04/07/08/12 | no-egress, Unicode, provenance |
| NFR-01..NFR-03 NFR-11 | security/topology/config/provider; 04/07/11 | isolation, secrets, TLS, supply-chain |
| NFR-04..NFR-07 NFR-10 | worker, throughput, DR docs; 03/09/11/12 | soak, SLO, backup recovery |
| NFR-08 NFR-12 NFR-13 | rubric, engine, AI quality docs; 03/08/11 | human holdout, Persian and neutrality |
| NFR-09 NFR-14 | version/audit/DI/CI/release; 04/05/11/12 | source audit, conventions, CI gate |

See [Review](01_existing_repository_review.md), [Design](02_detailed_design.md), [Contracts](03_api_and_contracts.md), [Decisions](05_architecture_decisions.md), [Source decisions](../requirements/05_open_decisions.md).


## Stage 04 observed paths (2026-10-24; evidence addendum)

The original `Exists? NO` cells above are historical Stage 02 observations, not current inventory. The following were **created** in Stage 04 at the GitHub baseline `4e14c2db36dcd7ac771c3ee554367fd9e3a34b88`: `src/host/app.py`, `src/host/res/appsettings.yaml`, `src/host/res/appsettings.development.yaml`, `src/application/web.py`, `src/infrastructure/di/inject.py`, `src/infrastructure/di/reflection.py`, `src/infrastructure/di/bootstrap.py`, `src/infrastructure/utils/config_reader.py`, `src/infrastructure/security/{policy,secrets,safe_logging}.py`, `requirements.txt`, `requirements-dev.txt`, `tests/test_foundation.py`, `scripts/verification/check_stage04_safety.py`, four security/deployment documents and two Stage 04 verification ledgers. `.gitignore` was modified. `src/infrastructure/context/vault/vault_service.py` was **NOT CREATED**, because OD-08 is OPEN; the env-based `SecretResolver` is Stage 04 only and does not pretend to be the corporate Vault implementation. `src/infrastructure/context/sql_db`, `BaseRepository`, migrations, inference, worker and product API remain **MISSING / FUTURE STAGES**. Local verification: 22/22 pytest PASS; remaining dependency audit and previous regression rerun NOT_RUN (Stage 04 IN_PROGRESS).
