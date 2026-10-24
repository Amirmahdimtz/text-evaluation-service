# Stage 03 — انتخاب مدل و ثبت تصمیم فنی

> وضعیت: `CANDIDATE_REVIEW / NO_MODEL_SELECTED` · تاریخ: 2026-10-21 · ردیابی: FR-04/06/10/11/12، NFR-05/08/11/12. این سند **بررسی اولیه منابع عمومی** است، نه Benchmark واقعی یا تأیید حقوقی سازمان.

> **وضعیت پس از D-017:** Stage 03 `DONE / LOCAL_GATE_PASS`؛ انتخاب واقعی مدل و ظرفیت همچنان `NO_MODEL_SELECTED / DEFERRED_TO_STAGE_11`. گزاره‌های تاریخی `IN_PROGRESS` مربوط به Gate قبلی هستند و انتخاب دو کاندید را قطعی نمی‌کنند.

## ۱. وضعیت مبنا و حدود مجوز

- آخرین Commit قبل از شروع این مرحله در `main` برابر `6f650728e80849f65f46b50c81ab2da500ac6d53` بود. در Tree واقعی Repository فقط اسناد مراحل ۰۱ و ۰۲ و اسکریپت QA مرحله ۰۲ مشاهده شد؛ `src/`، مدل دانلودشده، Inference Server، فایل Dependencies و CI موجود نبودند.
- کاربر ورود **مشروط** به Stage 03 را تأیید کرده است (`D-016`)، اما Stage 02 همچنان `BLOCKED` است؛ آزمون‌های DI/Bootstrap در Stage 04، Database در Stage 05 و WebService در Stage 10 با وضعیت `NOT_RUN` باقی می‌مانند.
- الزام مدل کاملاً داخلی و منع ارسال متن محرمانه به Provider خارجی (`D-002`) قطعی است. `vLLM` (`D-006`) و `Qwen3-14B` (`D-007`) **CANDIDATE** هستند؛ وزن‌ها و Rubric نیز `PROPOSED` هستند.
- فقط نسخه آزمایشی `candidate-0.1` برای Benchmark داخلی با داده Synthetic/مجاز به کار می‌رود؛ این نسخه `Published` یا Business-Approved نیست.

## ۲. مدل‌های پیشنهادی برای آزمایش مقایسه‌ای

| ویژگی | مدل Baseline: Qwen2.5-7B-Instruct | مدل Candidate: Qwen3-14B |
|---|---|---|
| Model ID | `Qwen/Qwen2.5-7B-Instruct` | `Qwen/Qwen3-14B` |
| نوع | Instruction-tuned، چندزبانه | Instruction-tuned، با حالت‌های Thinking/Non-thinking |
| تعداد پارامتر اعلام‌شده | حدود 7.62B | حدود 14.8B |
| License در Metadata رسمی | Apache-2.0 | Apache-2.0 |
| مجوز سازمانی/تجاری برای Artifact واقعی | `PENDING_ORG_LEGAL_REVIEW` | `PENDING_ORG_LEGAL_REVIEW` |
| Context اعلام‌شده | حداکثر 131,072 با تنظیمات معتبر؛ ظرفیت عملی ناشناخته | 32,768 بومی؛ حداکثر 131,072 با YaRN و احتمال تغییر کیفیت |
| کیفیت زبان فارسی در سه حوزه | `UNVERIFIED` | `UNVERIFIED` |
| Structured Output واقعی | `PENDING_SERVER` | `PENDING_SERVER` |
| سازگاری نسخه نصب‌شده vLLM/Tokenizer | `PENDING_SERVER` | `PENDING_SERVER` |
| Revision ثابت مدل، Tokenizer و SHA-256 | `UNVERIFIED` | `UNVERIFIED` |
| Latency، VRAM، Throughput واقعی | `PENDING_SERVER` | `PENDING_SERVER` |
| نقش | `BASELINE_CANDIDATE` | `PRIMARY_BENCHMARK_CANDIDATE` |

پشتیبانی عمومی مدل‌ها از چند زبان به‌معنای اثبات کیفیت فارسی، سنجش بی‌طرفانه Rubric، تشخیص ادعاهای بدون منبع یا تولید JSON معتبر نیست. بدون اجرای هر دو گزینه روی Dataset مشترک، **هیچ رتبه‌بندی کیفیتی** ثبت نمی‌شود. اگر سخت‌افزار سازمان مدل بزرگ‌تر را پشتیبانی نکند، جایگزین باید با Decision Request روشن به تأیید AI Lead برسد.

### منابع عمومی بررسی‌شده؛ بدون دریافت وزن مدل

- Qwen3-14B: https://huggingface.co/Qwen/Qwen3-14B و https://huggingface.co/Qwen/Qwen3-14B/tree/main
- Qwen2.5-7B-Instruct: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct و https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/tree/main
- مستند Structured Output در vLLM: https://docs.vllm.ai/en/latest/features/structured_outputs.html

اطلاعات فوق از Model Card و مستندات رسمی استخراج شده‌اند؛ `main` در مخزن مدل **Revision تغییرناپذیر نیست** و صرف نمایش Apache-2.0 به‌معنای تکمیل تأیید حقوقی سازمان نیست. در نسخه‌های جدید vLLM، فیلد قدیمی `guided_json` حذف شده و باید قابلیت واقعی نسخه نصب‌شده، از جمله `structured_outputs` یا `response_format`، آزمایش شود.

## ۳. پروتکل تأیید License، Provenance و Artifact

برای **هر مدل و هر Quantization** موارد زیر باید پیش از اجرای Benchmark در محیط مجاز مستند شوند:

1. تأیید مسیر قانونی واردکردن Artifact به Storage داخلی، سیاست Air-Gap، نوع داده مجاز و مسئول امنیت/زیرساخت.
2. ثبت Commit SHA غیرقابل‌تغییر upstream، Model Card و License متناظر همان Revision، تاریخ و مسئول Import، شناسه Registry داخلی و Noticeهای لازم.
3. محاسبه و تطبیق SHA-256 برای **تمام** فایل‌های وزن، Config، Tokenizer و Chat Template؛ مستندکردن Hash Manifest در Storage مجاز.
4. ثبت Runtime/Container/Driver/CUDA/Dependency Versions؛ بررسی نیاز احتمالی به `trust_remote_code` و ممنوعیت اجرای کد بررسی‌نشده.
5. آزمایش Tokenizer، Prompt Template، Parsing حالت Thinking، محدودیت Context، خروجی JSON و محرمانگی Logها.
6. بررسی حقوقی استفاده سازمانی/تجاری از **Artifact و Dependencyهای دقیق**. نبود تأیید به معنی `BLOCKED` برای ورود Artifact به محیط واقعی است.

هیچ مسیر دانلود خودکار، ارسال متن به بیرون یا Provider جایگزین خارجی مجاز نیست.

## ۴. معیارهای انتخاب و Comparison Matrix

| معیار تصمیم | نحوه استناد | وضعیت |
|---|---|---|
| Quality فارسی و توافق با متخصصان | MAE، توافق ارزیاب‌ها، اختلاف سه حوزه و بازه اطمینان | `NOT_MEASURABLE` بدون Golden Labels |
| Evidence و Hallucination | تطبیق Quote/Offset، ارتباط شاهد، ادعاهای بدون پشتوانه | `PENDING_SERVER` |
| Abstention و Coverage | تطبیق `not_assessed` با مرجع کارشناسی | `PENDING_SERVER` |
| Structured Output و Stability | Validator مستقل، تکرار آزمایش و ثبت Failure | `PENDING_SERVER` |
| Performance و Capacity | Latency P50/P95، VRAM، Tokens/s، Concurrent Throughput و OOM | `PENDING_SERVER` |
| License، Security و Provenance | مجوز، Hash Manifest، بررسی No-Egress و محرمانگی | `PARTIAL_DESK_REVIEW / PENDING_ORG` |
| هزینه و پیچیدگی عملیات | نیاز واقعی GPU، سرویس‌دهی داخلی، پایش و نگهداری | `UNVERIFIED` |

انتخاب باید به‌صورت تجمیعی و بر اساس Dataset، روش ارزیابی و حد پذیرش مصوب انجام شود؛ تعداد پارامتر یا محبوبیت مدل معیار تصمیم نیست.

## ۵. تصمیم فعلی

**تصمیم انتخاب مدل: `BLOCKED`؛ وضعیت فعالیت Stage 03: `IN_PROGRESS`.** ترکیب `Qwen3-14B + vLLM` فقط اولویت بررسی مشروط است، نه `SELECTED_CONDITIONALLY`. بعد از آزمایش واقعی دو Candidate، سنجش ظرفیت و دریافت تصمیم‌های لازم، نتیجه نهایی باید یکی از `SELECTED_CONDITIONALLY`، `BLOCKED` یا `REASSESSMENT_REQUIRED` باشد.

تصمیم‌های باز: `OD-13` برای GPU، Import و شبکه داخلی (Infrastructure/Security/AI Lead)؛ `OD-14` برای Dataset، Expert Labels و Thresholdها (AI Lead/SMEs/PO/Data Steward)؛ `OD-02/12` برای اندازه متن و Workload؛ `OD-03/04/11` برای Rubric، Evidence و Coverage.

ارجاع: [پروتکل](02_benchmark_protocol.md) · [نتایج](03_benchmark_results.md) · [منابع](04_inference_resource_plan.md) · [Decision Log](../requirements/05_open_decisions.md).

## ۶. D-017 — تفکیک انتخاب کاندید از تأیید مدل

Gate آفلاین Stage 03 شامل Desk Review دو مدل، مقایسه مفروضات، پروتکل آزمون و تست Validator است. مدل/Runtime و License واقعی Artifact و Capacity Baseline تنها در Stage 11 و پس از اجرای دو مدل با Corpus/مجوز معتبر مشخص می‌شوند؛ تا آن زمان `DEFERRED_TO_STAGE_11` و تصمیم انتخاب مدل `BLOCKED/NO_MODEL_SELECTED` می‌ماند. [Deferred Test Ledger](03_benchmark_results.md#12-d-017-deferred-on-premise-test-ledger).
