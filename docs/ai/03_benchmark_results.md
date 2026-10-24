# Stage 03 — نتایج Benchmark و دفتر شواهد

> وضعیت: `PENDING_SERVER / NO_MEASUREMENTS` · 2026-10-21. دستیار به هیچ سرور GPU/Inference سازمانی یا Golden Dataset کارشناسی دسترسی نداشته و هیچ Model Benchmark واقعی اجرا نکرده است. جدول‌ها صرفاً **وضعیت اندازه‌گیری** هستند، نه مقادیر صفر یا نتیجه تخمینی.

## ۱. نتایج واقعی Preflight

| بررسی | شواهد | وضعیت |
|---|---|---|
| بررسی Repository و Commit مبنا | GitHub `main` در آغاز Stage 03: `6f650728e80849f65f46b50c81ab2da500ac6d53` | `PASS_REPOSITORY_INSPECTION` |
| Tree واقعی Git | ۱۱ فایل مستندات Stage 01/02 و Checker مرحله ۰۲؛ بدون `src/`، مدل یا Server | `PASS_REPOSITORY_INSPECTION` |
| آزمون DI/Bootstrap/WebService مرحله ۰۲ | سورس اجرایی وجود ندارد؛ Stage 04/10 مالک اجرا هستند | `NOT_RUN`، Stage 02 `BLOCKED` |
| GPU، VRAM، Driver، RAM، Storage و Network سازمان | هیچ Inventory تأییدشده دریافت نشده است | `UNVERIFIED` |
| Model Artifact/Tokenizer و Checksum | Artifact داخلی مشاهده یا Import نشده است | `UNVERIFIED` |
| Dataset مجاز و برچسب کارشناسی سه حوزه | نمونه اجرایی/مرجع کارشناسی ارائه نشده است | `UNVERIFIED` |
| Model Card و License Metadata عمومی | بررسی Read-only دو Model ID از منابع رسمی | `PASS_DESK_REVIEW_ONLY`، نه تأیید قانونی |
| GPU Benchmark، No-Egress و Inference واقعی | محیط مجاز سازمان در دسترس نیست | `PENDING_SERVER` |

خروجی قبلی کاربر روی Commit `88d56fd` برابر **`18/19 PASS`** بود و شکست تنها مربوط به شرط منسوخ `stage tracker preserved` بود. پس از اصلاح، کاربر روی Commit `f3c32c3043a63c4a304162f0834a716cb659dc60` نتایج واقعی **`19/19 PASS`** برای Stage 02 Documentation QA، **`9/9 PASS`** برای Regressionهای Stage 02 و **`11/11 PASS`** برای تست‌های Stage 03 را ارائه کرد؛ `git status --short` نیز خالی بود. این شواهد، Gate اجرایی Stage 02 را پاس نمی‌کنند؛ مرحله همچنان `BLOCKED` است.

در اجرای جدید کاربر روی Commit `d1920bf98d519fbd9e19e494b249d1c1738d191d`، **۳۱/۳۱ تست Stage 03**، **۹/۹ Regression Stage 02** و **۱۹/۱۹ بررسی مستندات Stage 02** با موفقیت اجرا شدند، Compile بدون خطا بود و `git status --short` خروجی نداشت. این ۵۹ بررسی، `VERIFIED_USER_LOCAL` هستند، نه مدل Benchmark یا Acceptance Gate.

## ۲. Quality Metrics واقعی

| Metric | speech | media | research | علت |
|---|---|---|---|---|
| MAE / Inter-rater Agreement | `NOT_MEASURABLE` | `NOT_MEASURABLE` | `NOT_MEASURABLE` | Expert Labels نداریم |
| Evidence Accuracy / Relevance | `PENDING_SERVER` | `PENDING_SERVER` | `PENDING_SERVER` | خروجی مدل و متن مجاز نداریم |
| Hallucination / Unsupported Claims | `PENDING_SERVER` | `PENDING_SERVER` | `PENDING_SERVER` | پاسخ داوری‌شده نداریم |
| Schema Validity | `PENDING_SERVER` | `PENDING_SERVER` | `PENDING_SERVER` | Generation اجرا نشده است |
| Correct Abstention / Coverage | `PENDING_SERVER` | `PENDING_SERVER` | `PENDING_SERVER` | ارزیابی کارشناسی اجرا نشده است |
| Stability و تکرارپذیری | `PENDING_SERVER` | `PENDING_SERVER` | `PENDING_SERVER` | مدل و Runtime ثابت نداریم |
| Persian / Long Text / Fairness | `PENDING_SERVER` | `PENDING_SERVER` | `PENDING_SERVER` | Dataset اجراشده نداریم |

**هیچ مقدار عددی، Confidence Interval، حجم نمونه ارزیابی‌شده یا رتبه‌بندی مدل وجود ندارد.** مقدار صفر برای Metricهای بالا نیز غیرواقعی خواهد بود.

## ۳. Resource Metrics واقعی

| Metric | Qwen2.5-7B-Instruct | Qwen3-14B |
|---|---|---|
| Latency P50/P95 | `PENDING_SERVER` | `PENDING_SERVER` |
| Prompt/Completion Tokens و Tokens/s | `PENDING_SERVER` | `PENDING_SERVER` |
| Throughput با Concurrency مشخص | `PENDING_SERVER` | `PENDING_SERVER` |
| Peak VRAM / GPU Utilization | `PENDING_SERVER` | `PENDING_SERVER` |
| Context Limit، OOM، Timeout و Failure Rate | `PENDING_SERVER` | `PENDING_SERVER` |
| سازگاری Structured Output در Runtime واقعی | `PENDING_SERVER` | `PENDING_SERVER` |

محاسبات نظری Memory فقط در [Resource Plan](04_inference_resource_plan.md) قرار دارند؛ هیچ عدد تخمینی به‌عنوان VRAM یا Throughput اندازه‌گیری‌شده ثبت نشده است.

## ۴. Manifest شواهد لازم برای Runهای بعدی

برای هر Attempt باید `run_id`، `timestamp_utc`، `model_id/revision`، `artifact_sha256_manifest`، `tokenizer_revision`، `runtime_version`، `hardware_inventory_id`، `dataset_version/split`، `sample_count`، `rubric/prompt/schema_revision`، `sampling_config`، `quantization`، `latency_ms`، `prompt_tokens`، `completion_tokens`، `gpu_vram_peak_bytes`، `error_class`، `schema_valid`، `evidence_valid` و مرجع محل امن Raw Result ثبت شود.

Failure Classes لازم: `INVALID_JSON`، `INVALID_SCORE`، `QUOTE_MISMATCH`، `UNSUPPORTED_CLAIM`، `INCORRECT_ABSTENTION`، `PROMPT_INJECTION_FOLLOWED`، `LONG_CONTEXT_TRUNCATED`، `TIMEOUT`، `OOM`، `TRANSPORT_ERROR` و `ARTIFACT_OR_LICENSE_REJECTED`. نرخ واقعی این خطاها فعلاً `NOT_MEASURABLE` است.

## ۵. تست‌های واقعی مستقل از مدل

- در 2026-10-21 دستیار روی Sandbox خودش دستور `python -m py_compile` برای دو فایل Python مربوط به Benchmark Validator و دستور `python -m unittest -v test_validate_stage03_outputs.py` را اجرا کرده است: **۱۱ تست از ۱۱ تست PASS** با ورودی‌های صرفاً Synthetic.
- پوشش تست: Strict Schema، امتیاز Bool نامعتبر، Quote/Unicode/Offset، `not_assessed` و `score=null`، Criterion اشتباه یا Unhashable، Corpus بدون تأیید، JSON مخدوش، Attempt تکراری و فایل خالی.
- این نتیجه تنها Unit Test ابزار مستقل است، **نه** آزمایش روی مدل، تأیید Accuracy، Relevance، No-Egress، GPU Capacity یا License. اجرای همان ۱۱ تست روی Clone واقعی کاربر نیز با شواهد PowerShell ثبت شده و `11/11 PASS` بوده است؛ آزمایش مدل واقعی همچنان `PENDING_SERVER` است.

## ۶. نتیجه و محدودیت تصمیم

**Model Selection: `BLOCKED / NO_MODEL_SELECTED`؛ Stage 03: `DONE / LOCAL_GATE_PASS` طبق D-017.** چهار سند و Validator آفلاین آماده‌اند و تست‌های محلی مرتبط موفق بوده‌اند. اجرای مدل واقعی، License/Artifact، Dataset کارشناسی، Accuracy، GPU/Capacity و No-Egress با وضعیت `DEFERRED_TO_STAGE_11` ثبت شده‌اند، نه `PASSED`. Stage 02 با Gate طراحی جدید `DONE` است، ولی DI/DB/WebService به‌ترتیب در Stages 04/05/10 تست محلی لازم دارند. ورود Stage 04 فقط `APPROVED_FOR_REQUEST` است.

ارجاع: [انتخاب مدل](01_model_selection.md) · [پروتکل](02_benchmark_protocol.md) · [منابع](04_inference_resource_plan.md) · [Decision Log](../requirements/05_open_decisions.md).

## ۷. QA پس از Push و کنترل محدوده Diff

- پس از انتشار چهار سند فارسی و دو Script، دستیار **GitHub HEAD** را با Commit `b2e52c7f03f3300acdb3aaad050b99cfc833c46d` تطبیق داد؛ Recursive Tree کامل و ۱۷ فایل Track‌شده بررسی شدند. مقایسه با Baseline `6f650728e80849f65f46b50c81ab2da500ac6d53` دقیقاً ۸ مسیر مرتبط با Stage 03 را نشان داد (۴ سند AI جدید، ۲ Script جدید، ۲ سند Decision/Tracker اصلاح‌شده). تغییری در `src/`، DB، API یا Production رخ نداد.
- کنترل محتوای واقعی GitHub پس از Push: **40/40 static/documentation checks PASS** شامل وجود مسیرها، ارجاع Markdown، بسته‌شدن Code Fenceها، زبان فارسی اسناد، پوشش سه حوزه، وضعیت‌های صادقانه Gate، کدهای Benchmark Validator و الگوهای آشکار Secret. این بررسی Security Certification یا Runtime Test نیست.
- دستورهای اجراشده در Sandbox دستیار: `python -m py_compile scripts/benchmark/validate_stage03_outputs.py scripts/benchmark/test_validate_stage03_outputs.py` → PASS؛ `python -m unittest discover -s scripts/benchmark -p 'test_*.py' -v` → **11/11 PASS**؛ اجرای `python scripts/benchmark/validate_stage03_outputs.py --input <synthetic-test-jsonl>` با یک رکورد Synthetic → `PASS`, `valid=1`, `invalid=0`. Validator فقط Schema و Exact Offset را می‌سنجد.
- دستور `nvidia-smi` در Sandbox دستیار موجود نبود؛ این مشاهده **هیچ اطلاعاتی درباره GPU سازمانی اثبات نمی‌کند**. Inventory سازمان `UNVERIFIED` است. مدل، vLLM، GPU Benchmark، Dataset کارشناسی، Quality و No-Egress همچنان `PENDING_SERVER`/`NOT_MEASURABLE` هستند.

## ۸. شواهد جدید اجرای تست روی سیستم کاربر — 2026-10-21

- روی Git HEAD `88d56fdca17019fa7e85e9caf86171a4b1d3d486`، کاربر نتیجه اجرای واقعی PowerShell را ارائه کرد: `python -m py_compile` بدون خطا و `python -m unittest discover -s scripts/benchmark -p 'test_*.py' -v` با **11/11 PASS** و `Ran 11 tests in 1.691s`.
- اجرای `python scripts/verification/check_stage02_docs.py` نتیجه **18/19 PASS** داد؛ تنها شرط `stage tracker preserved` به دلیل انتظار قدیمی `NOT_STARTED` در برابر ورود مشروط تأییدشده `D-016` شکست خورد. این خطا از Benchmark مدل یا تست Validator نیست. Regression Fix و Test مستقل برای شرط جدید اضافه شد؛ تکرار کامل Checker روی Commit اصلاح‌شده هنوز `PENDING_USER_LOCAL` است.
- `git status --short` فقط `scripts/benchmark/__pycache__/` را Untracked نشان داد؛ Root `.gitignore` برای بی‌اثرکردن Cache خودکار Python اضافه شد و هیچ داده‌ای حذف نشد.
- این شواهد همچنان به معنی اندازه‌گیری GPU، Accuracy فارسی، Evidence Relevance یا Quality مدل نیستند؛ آن آزمون‌ها `PENDING_SERVER` و MAE مرجع کارشناسی `NOT_MEASURABLE` باقی می‌مانند.


## ۹. اصلاحات مستقل Stage 03 پس از ممیزی (2026-10-24)

- ضعف Parser در پذیرش Duplicate JSON Key، `NaN`/`Infinity` و خطای کنترل‌نشده ناشی از JSON بسیار تودرتو برطرف شد؛ Overflow Float و Unicode Scalar نامعتبر نیز به‌صورت Fail Closed کنترل می‌شوند.
- عدم تطبیق سناریوی مستند Synthetic با Domain رد می‌شود. برای Dataset واقعی گزینه `--manifest` اضافه شد تا JSONL Manifest ساختار نسخه‌دار، Hash دقیق UTF-8 متن، Domain و `case_id` را بررسی کند. ممنوعیت Group/Source تکراری بین Splitها کنترل می‌شود؛ Near-Duplicate، مجوز Data Steward و اعتبار رسمی Provenance خارج از این Validator هستند.
- معیار `research_novelty` بدون Corpus و داوری علمی معتبر نمی‌تواند نمره عددی بگیرد. `not_assessed` و `score=null` مجازند؛ ادعای Published Rubric یا تأیید مجوز از این تغییر حاصل نمی‌شود.
- دستیار روی **نسخه متناظر و مستقل در Sandbox** دستور `python -m py_compile` و **۳۱ تست Synthetic Unit/Regression از ۳۱ تست — PASS** را اجرا کرد. Source و Test روی GitHub منتشر شده‌اند؛ اجرای مجدد **Commit نهایی روی Clone کاربر** هنوز `PENDING_USER_LOCAL` است و نباید با اجرای Sandbox یکی فرض شود.
- **وضعیت Gate بدون تغییر:** GPU، هر دو مدل Inference، Dataset و Expert Labels واقعی، Quality، Evidence Relevance، No-Egress، Latency، VRAM و Capacity `PENDING_SERVER`/در موارد بدون برچسب `NOT_MEASURABLE` هستند. Stage 03 `IN_PROGRESS` و Model Selection `BLOCKED` است.


## ۱۰. ممیزی نهایی آمادگی Gate و رفع نقص Validation (2026-10-24)

- **Source audit:** دو سند الزام‌آور پروژه و GitHub `main`، چهار خروجی Stage 03 و واحدهای تست موجود بررسی شدند. Gate رسمی Stage 03 انتخاب مدل/Runtime مشروط با اندازه‌گیری سه حوزه، Benchmark کیفیت و ظرفیت، No-Egress، مدل Artifact مجاز و Expert Labels را الزامی می‌داند؛ این شواهد وجود ندارند. **Gate: BLOCKED؛ مجوز ورود به Stage 04: NOT_APPROVED**. این تصمیم به‌معنای تغییر Decisionهای فنی باز به CONFIRMED نیست.
- **نقص جدید ورودی:** فیلدهای متنی غیرمعتبر با Unicode lone surrogate در Identifier/Reason/فهرست‌ها/Metadata Manifest قبلاً ممکن بود پذیرفته شوند. با بررسی قابلیت Encode شدن UTF-8 و تست‌های منفی اصلاح شدند؛ این اسکریپت Parser اصلی مدل یا صحت معنایی را تضمین نمی‌کند.
- **Resource-safety:** برای جلوگیری از Tracking State بی‌کران، `MAX_RECORDS=100000` در هر invocation اعمال شد. Manifest اضافی Fail Closed و نتیجه اضافی دارای `RECORD_LIMIT_EXCEEDED` و `FAIL` است؛ هیچ Run ناقصی نباید مبنای Metric شود. این عدد Limit ایمنی ابزار است و **هیچ ربطی به حد پذیرش AI یا تعداد Dataset مصوب ندارد**.
- **Offline synthetic tests:** مجموعه ۳۱ تست موجود همراه ۷ Regression جدید روی نسخه معادل در Sandbox دستیار **۳۸/۳۸ PASS**؛ `py_compile` PASS. GitHub commit read-back و بررسی Diff مستقل انجام می‌شود. اجرای Commit نهایی بر Clone شخصی کاربر هنوز `PENDING_USER_LOCAL` است.
- **هنوز بسته نشده:** مجوز و Inventory سخت‌افزار/شبکه، Model Revision و Checksum، Golden Dataset برچسب‌دار سه حوزه، Inference داخلی دو کاندید، Metricهای Quality/Evidence/Abstention/Fairness/Latency/Peak VRAM/Throughput و No-Egress `PENDING_SERVER` یا `NOT_MEASURABLE` باقی‌اند. سندها برنامه‌اند نه اثبات انتخاب مدل یا Capacity Baseline.

## ۱۱. تأیید اجرای محلی نسخه نهایی Validator توسط کاربر (2026-10-24)

- کاربر اجرای واقعی PowerShell روی `git rev-parse HEAD = 663c1dbf211f51b29925d8f6c40d15f2605424fd` را ارائه کرد؛ `git pull --ff-only origin main` موفق بود و `python -m py_compile` بدون خطا اجرا شد.
- تست Validator مرحله سوم: **`38/38 PASS`**، مدت گزارش‌شده `3.923s`. Regression مرحله دوم: **`9/9 PASS`**، مدت `0.395s`. بررسی مستندات Stage 02: **`19/19 PASS`**. مجموع: **`66/66 PASS`** در تست‌ها و بررسی‌های محلی ارائه‌شده با وضعیت `VERIFIED_USER_LOCAL`.
- خروجی `git status --short` خالی است؛ Working Tree در زمان اجرای تست‌ها Clean بوده است. موارد تاریخی `PENDING_USER_LOCAL` برای همین تست‌ها و همین Commit با این شواهد بسته شده‌اند؛ Commit ثبت این شواهد صرفاً تغییر Documentation است و اجرای محلی تازه‌ای برای آن ادعا نمی‌شود.
- **Gate مرحله سوم هنوز `BLOCKED` است.** Inference واقعی دو مدل، داده کارشناسی و آزمون سه حوزه، No-Egress، GPU/VRAM/Latency/Throughput و انتخاب مدل و Capacity Baseline همچنان `PENDING_SERVER` یا `NOT_MEASURABLE` هستند. هیچ تأیید ورود به Stage 04 صادر نشده است.

## ۱۲. D-017 Deferred On-Premise Test Ledger

تمام این آزمون‌ها بدون شواهد سرور واقعی، وضعیت `DEFERRED_TO_STAGE_11` دارند؛ نه `PASS`. مالک‌ها نقش پیشنهادی‌اند و عددهای پذیرش تا تصمیم OD-12/14 `OPEN` می‌مانند. مجوز استفاده از Artifact، Dataset و شبکه واقعی پیش از اجرا الزامی است.

| Test ID | Implementation owner → Stage 11 executor | Why company server | Required input/permission | Measurable success evidence | Status |
|---|---|---|---|---|---|
| `S11-AI-01` | Stage 03 resource plan → Infrastructure/SRE | Real GPU/driver inventory | Authorized server access and resource limits | Pinned hardware/driver/runtime inventory and capacity probe | `DEFERRED_TO_STAGE_11` |
| `S11-AI-02` | Stage 03 artifact protocol → MLOps/Legal/Security | Actual internal weights and license | Legal permission, internal registry, pinned revisions | Artifact SHA-256/license/supply-chain acceptance | `DEFERRED_TO_STAGE_11` |
| `S11-AI-03` | Stage 03 candidates/Stage 07 provider → AI Lead/MLOps | Live Qwen2.5 inference | Approved baseline, vLLM and GPU | Offline startup, tokenizer/schema contract measured | `DEFERRED_TO_STAGE_11` |
| `S11-AI-04` | Stage 03 candidates/Stage 07 provider → AI Lead/MLOps | Live Qwen3 inference | Approved candidate, vLLM and GPU | Same model/schema tests and fixed configuration | `DEFERRED_TO_STAGE_11` |
| `S11-AI-05` | Stage 03 dataset/Stage 08 → Data Steward/SMEs | Expert golden dataset | Approved data, rater labels, group-disjoint splits | Three-domain versioned manifest and adjudicated labels | `DEFERRED_TO_STAGE_11` |
| `S11-AI-06` | Stage 03 validator/Stage 07–08 → AI Quality Lead | Actual generation quality | Pinned prompts/schema and approved model runs | Structured-output validity and exact source quotes/offsets | `DEFERRED_TO_STAGE_11` |
| `S11-AI-07` | Stage 03 metrics/Stage 08 → AI Lead/SMEs | Model-vs-human rating | Adjudicated labels, thresholds OD-14 | Per-domain MAE, agreement and CI with sample counts | `DEFERRED_TO_STAGE_11` |
| `S11-AI-08` | Stage 03 evidence/Stage 08 → AI Quality/SMEs | Evidence relevance, hallucinations | Human annotation/corpus permission | Unsupported claims, relevance and abstention metrics | `DEFERRED_TO_STAGE_11` |
| `S11-AI-09` | Stage 03 scenarios/Stage 08 → AI Quality/Security | Real prompt injection and long-context cases | Approved adversarial fixtures and limits | Fairness, stability, injection and context metrics | `DEFERRED_TO_STAGE_11` |
| `S11-AI-10` | Stage 03 resource/Stage 09 → SRE/MLOps | Real GPU load and VRAM | Approved SLO/workload OD-12 | P50/P95, throughput, peak VRAM, OOM, soak data | `DEFERRED_TO_STAGE_11` |
| `S11-SEC-11` | Stage 03 no-egress plan/Stage 04–07 → Network/Security | Company firewall/DNS/logging | Written security authorization and network isolation | No forbidden egress or sensitive log leakage; TLS/IAM proof | `DEFERRED_TO_STAGE_11` |
| `S11-E2E-12` | Stage 03 ledger/Stage 09–10 → QA/SRE | Deployed internal end-to-end chain | Stage 04–10 local gates complete, approved staging | Measured API/Worker/DB/LLM E2E, recovery and auth tests | `DEFERRED_TO_STAGE_11` |

**Gate verdict:** Stage 03 `DONE / LOCAL_GATE_PASS` only. Model, Performance, License and No-Egress acceptance remain unresolved until Stage 11; all local validation gates remain mandatory in their owning implementation stage.
