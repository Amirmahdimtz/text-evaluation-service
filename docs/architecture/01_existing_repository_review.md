# Stage 02 — Existing Repository Inspection

> Inspection date: 2026-10-21 | Branch: main | Evidence baseline: 924fd3c91f680b00c27533bae9fc0c59e70c6e8c | Status: VERIFIED_DOCUMENTS_ONLY
>
> این سند بازتاب بازرسی واقعی GitHub در زمان اجرا است؛ Architecture Guide یک مرجع طراحی است، نه مجموعه فایل‌های مشاهده‌شده. Repository عمومی است. هیچ اطلاعات سازمانی محرمانه در این سند درج نشده است.

## 1. Access, history and evidence

- Repository: https://github.com/Amirmahdimtz/text-evaluation-service ؛ default/target branch: main؛ visibility: public؛ connector permissions: pull/push/admin reported true.
- HEAD مستقل از Baseline کاربر از طریق جست‌وجوی Commitهای اخیر GitHub بررسی شد و 924fd3c91f680b00c27533bae9fc0c59e70c6e8c تأیید شد؛ پیام آن: docs: close stage 1 internal gate and authorize stage 2 entry.
- تاریخچه مرتبط به ترتیب جدید به قدیم: 924fd3c (close Stage 01 gate)، 5ac8641 (25-check documentation gate)، a997ebe (Stage 01 documentation completion)، 074a524 (input matrix formatting)، b4604f8 (synthetic report contract). نسخه‌های کامل SHA در GitHub History قابل بازیابی است.
- فایل‌های پنج‌گانه docs/requirements با GitHub fetch_file روی main دریافت شدند و blob SHAهایشان مشاهده شد. HEAD شامل مدارک Stage 01 است. بررسی مستقل Git tree recursive از این محیط در دسترس نبود؛ در نتیجه ادعای ممیزی بایت‌به‌بایت همه مسیرهای مخفی یا ناشناخته مطرح نمی‌شود.
- Clone/ls-remote در sandbox به علت DNS failure برای github.com ممکن نبود؛ دسترسی تأییدشده از GitHub connector است. نتیجه بررسی Sourceهای شاخص زیر از GitHub API: Not Found 404.

## 2. Verified repository inventory

در این بازرسی مسیرهای موجود به صورت زیر تأیید شدند:

| Path | State | Evidence |
|---|---|---|
| docs/requirements/01_product_requirements.md | EXISTS_AND_REVIEWED | FR-01..FR-12 و NFR-01..NFR-14؛ candidate input matrix |
| docs/requirements/02_evaluation_rubrics.md | EXISTS_AND_REVIEWED | سه مجموعه پیشنهادی speech/media/research، 18 معیار، شواهد |
| docs/requirements/03_acceptance_criteria.md | EXISTS_AND_REVIEWED | FR/NFR acceptance و synthetic JSON report |
| docs/requirements/04_security_and_data_policy.md | EXISTS_AND_REVIEWED | Security controls و threat tests صرفاً مستند |
| docs/requirements/05_open_decisions.md | EXISTS_AND_REVIEWED | D-001..D-015، OD-01..OD-16، Stage 01 DONE و Stage 02 NOT_STARTED در Baseline |

این لیست، مسیرهای مشاهده‌شده است، نه ادعای احصای کامل Tree از API در صورت وجود فایل‌های ناشناخته.

## 3. Runtime and tooling inspection

| Capability / path | State | Actual evidence / implication |
|---|---|---|
| src/host/app.py | MISSING | 404؛ FastAPI startup قابل بازرسی نیست |
| src/application/web.py | MISSING | 404؛ WebService/discovery runtime قابل بازرسی نیست |
| src/infrastructure/di/inject.py | MISSING | 404؛ decorator و resolver واقعی وجودِ تأییدشده ندارند |
| src/infrastructure/di/reflection.py | MISSING | 404؛ exception handling/exclusion behavior قابل آزمون نیست |
| src/infrastructure/di/bootstrap.py | MISSING | 404؛ bootstrap_di موجود فرض نمی‌شود |
| src/infrastructure/context/sql_db/psql_dbcontext.py | MISSING | 404؛ engine/session factory واقعی وجود ندارد |
| src/infrastructure/repositories/base/base_repository.py | MISSING | 404؛ CRUD/commit واقعی قابل بررسی نیست |
| src/infrastructure/alembic/env.py | MISSING | 404؛ metadata/migration wiring موجود نیست |
| requirements.txt | MISSING | 404؛ dependency versions تعیین نشده |
| pyproject.toml | MISSING | 404؛ Python constraint/build config تعیین نشده |
| poetry.lock / uv.lock | MISSING | 404؛ dependency lock قابل مشاهده نیست |
| Dockerfile | MISSING | 404؛ container entrypoint/config قابل مشاهده نیست |
| .gitlab-ci.yml / .github/workflows/ci.yml | MISSING | 404؛ این مسیرهای مرسوم CI موجود نیستند |
| README.md | MISSING | 404 |
| docs/architecture/01_existing_repository_review.md at inspection start | MISSING | 404؛ Stage 02 output جدید |
| Python/FastAPI/SQLAlchemy/Pydantic installed versions | UNVERIFIABLE | نه dependency manifest و نه environment اجرایی پروژه مشاهده شد |
| Other CI, health, auth, logging, vault, tests, custom configs | UNVERIFIABLE | مسیرهای شناخته‌شده یا manifest مرجع غایب؛ تمام نام‌های احتمالی آزموده نشده‌اند |
| PsqlDbContext/BaseRepository method implementations | UNVERIFIABLE | در مرجع مستند شده‌اند، نه در سورس این Repository |
| Controller import/discovery/bootstrap smoke tests | UNVERIFIABLE | Source/runtime واقعی وجود ندارد |

در این سند «MISSING» درباره مسیرهای دقیق probeشده به‌کار می‌رود؛ وضعیت سایر نام‌های بالقوه که probe نشده‌اند «UNVERIFIABLE» است. هیچ Version یا Dependency خاصی به‌عنوان نصب‌شده اعلام نشده است.

## 4. Reference architecture versus actual implementation

| Architecture Guide contract | Observed on main | Future validation |
|---|---|---|
| Host → Application → Core → Infrastructure | Contract در راهنمای مرجع، NOT IMPLEMENTED/VERIFIED | Layer/static dependency checks پس از Stage 04 |
| Constructor DI / @inject / singleton policy | Guide-only | Stage 04: import, typing, lifecycle, singleton and missing-dependency tests |
| bootstrap_di() and provider scan infrastructure → core → application | Guide-only | Stage 04: deterministic scan/error reporting tests |
| WebService mounting feature Controller with api() | Guide-only | Stage 10: route discovery, prefix, collision, auth tests |
| BaseRepository CRUD and operation-level AsyncSession | Guide-only | Stage 05: transactional consistency/rollback tests |
| PsqlDbContext + SQLAlchemy Async + Alembic | Guide-only | Stage 05: migration metadata and DB integration |
| Internal inference, durable worker | Candidate product design only | Stages 03/07/09 and server gates |

**Collision to solve:** Guide default هر operation در BaseRepository session/commit مستقل دارد؛ اما Evaluation + Job و Result + Job completion تراکنش اتمیک چند-Repository لازم دارند. بدون مشاهده Source، جایگزینی یا تغییر BaseRepository مجاز نیست. ADR-02 یک extension حداقلی مشروط تعریف می‌کند.

**Discovery risk:** در مرجع، خطای import ممکن است باعث skip ماژول شود. نام فایل و کلاس، @inject، api() و ترتیب bootstrap باید با contract سازگار باشند؛ fail-fast/logging تست‌شده به‌عنوان بهبود پیشنهادی ثبت می‌شود و رفتار Runtime واقعی ادعا نمی‌گردد.

## 5. Security, constraints and unresolved topics

- R-13: public GitHub؛ فقط توضیحات عمومی، شناسه‌های مصنوعی و قراردادهای غیرحساس Commit شوند.
- R-14/R-09: نبود Source و احتمال silent discovery failure؛ import/API/DB smoke test = NOT_RUN؛ تطبیق Runtime = BLOCKED.
- D-015: پذیرش رسمی کارفرما/SME Stage 12 است؛ technical gates و مجوز دسترسی به داده محرمانه پابرجا هستند.
- D-005 PostgreSQL-backed queue = PROPOSED؛ D-006 vLLM و D-007 Qwen3-14B = CANDIDATE.
- OD-07/08/10/11/12/13/14/15 پیش از نهایی‌کردن Identity، داده، ظرفیت، evidence و AI acceptance نیازمند تصمیم یا آزمون هستند.
- متن واقعی سازمان، Secrets، آدرس داخلی، توکن، تنظیمات Production و benchmark data هیچ‌کدام بازرسی یا کپی نشده‌اند.

## 6. Inspection conclusion and test classification

بر اساس شواهد فعلی، تنها Baseline مستندات مرحله ۱ قابل اتکاست و معماری تفصیلی باید از صفر، اما دقیقاً منطبق با استاندارد reference، به‌صورت PROPOSED طراحی شود.

| Check | Result | Explanation |
|---|---|---|
| Fetch GitHub repo metadata + main recent history | PASS | Live connector response; HEAD matched baseline |
| Fetch five Stage 01 requirement documents | PASS | All five returned successfully |
| Probe representative runtime/build/CI paths | PASS | Missing paths recorded by 404; no false existing claims |
| Actual Git recursive tree retrieval | NOT_VERIFIED | Tree enumeration unavailable via connected operations |
| Python import/discovery/bootstrap | NOT_RUN | No source or project dependency environment |
| API, unit, DB, migrations, worker tests | NOT_RUN | Implementation absent |
| Real GPU, vLLM, no-egress, load, recovery/E2E | PENDING_SERVER | Requires authorized internal infrastructure |

Related design artifacts: [Detailed Design](02_detailed_design.md), [API Contracts](03_api_and_contracts.md), [File Matrix](04_file_change_matrix.md), [Architecture Decisions](05_architecture_decisions.md). Source of Stage 01 tracking: [Open Decisions](../requirements/05_open_decisions.md).
