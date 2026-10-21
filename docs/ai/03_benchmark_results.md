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

گزارش `19/19 PASS` برای QA اسناد Stage 02 مطابق اعلام کاربر ثبت شده است؛ این شواهد **User Local** است، نه اجرای دستیار یا مدل زبانی، و Gate اجرایی Stage 02 همچنان `BLOCKED` می‌ماند.

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
- این نتیجه تنها Unit Test ابزار مستقل است، **نه** آزمایش روی مدل، تأیید Accuracy، Relevance، No-Egress، GPU Capacity یا License. اجرای مجدد روی Clone واقعی کاربر باید جداگانه گزارش شود و فعلاً `PENDING_USER_LOCAL` است.

## ۶. نتیجه و محدودیت تصمیم

**Model Selection: `BLOCKED`؛ Stage 03: `IN_PROGRESS`.** تا فراهم‌شدن GPU مجاز، Artifactهای نسخه‌دار، Dataset و Expert Labels، اجرای حداقل دو مدل و ثبت Latency/VRAM/Quality/Evidence هیچ برنده یا Capacity Baseline علمی قابل دفاعی وجود ندارد. Qwen3-14B + vLLM همچنان فقط Candidate است. Stage 02 نیز `BLOCKED` می‌ماند؛ این سند مجوز ورود به Stage 04 نیست.

ارجاع: [انتخاب مدل](01_model_selection.md) · [پروتکل](02_benchmark_protocol.md) · [منابع](04_inference_resource_plan.md) · [Decision Log](../requirements/05_open_decisions.md).

## ۷. QA پس از Push و کنترل محدوده Diff

- پس از انتشار چهار سند فارسی و دو Script، دستیار **GitHub HEAD** را با Commit `b2e52c7f03f3300acdb3aaad050b99cfc833c46d` تطبیق داد؛ Recursive Tree کامل و ۱۷ فایل Track‌شده بررسی شدند. مقایسه با Baseline `6f650728e80849f65f46b50c81ab2da500ac6d53` دقیقاً ۸ مسیر مرتبط با Stage 03 را نشان داد (۴ سند AI جدید، ۲ Script جدید، ۲ سند Decision/Tracker اصلاح‌شده). تغییری در `src/`، DB، API یا Production رخ نداد.
- کنترل محتوای واقعی GitHub پس از Push: **40/40 static/documentation checks PASS** شامل وجود مسیرها، ارجاع Markdown، بسته‌شدن Code Fenceها، زبان فارسی اسناد، پوشش سه حوزه، وضعیت‌های صادقانه Gate، کدهای Benchmark Validator و الگوهای آشکار Secret. این بررسی Security Certification یا Runtime Test نیست.
- دستورهای اجراشده در Sandbox دستیار: `python -m py_compile scripts/benchmark/validate_stage03_outputs.py scripts/benchmark/test_validate_stage03_outputs.py` → PASS؛ `python -m unittest discover -s scripts/benchmark -p 'test_*.py' -v` → **11/11 PASS**؛ اجرای `python scripts/benchmark/validate_stage03_outputs.py --input <synthetic-test-jsonl>` با یک رکورد Synthetic → `PASS`, `valid=1`, `invalid=0`. Validator فقط Schema و Exact Offset را می‌سنجد.
- دستور `nvidia-smi` در Sandbox دستیار موجود نبود؛ این مشاهده **هیچ اطلاعاتی درباره GPU سازمانی اثبات نمی‌کند**. Inventory سازمان `UNVERIFIED` است. مدل، vLLM، GPU Benchmark، Dataset کارشناسی، Quality و No-Egress همچنان `PENDING_SERVER`/`NOT_MEASURABLE` هستند.
