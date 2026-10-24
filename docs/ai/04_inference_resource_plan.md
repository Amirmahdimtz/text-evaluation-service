# Stage 03 — برنامه مشروط منابع Inference داخلی

> وضعیت: `UNVERIFIED_HARDWARE / NO_CAPACITY_BASELINE` · 2026-10-21. محاسبات این سند **برآورد تحلیلی** هستند، نه اندازه‌گیری GPU، مشخصات خرید سخت‌افزار یا مجوز Deployment.

## ۱. مشخصات واقعی موردنیاز از سرور داخلی

| مؤلفه | مقدار تأییدشده | مالک بررسی |
|---|---|---|
| GPU Model، تعداد، VRAM و Topology | `UNVERIFIED` | Infrastructure/SRE |
| CPU Model/Cores و RAM | `UNVERIFIED` | Infrastructure |
| Storage آزاد، سرعت دیسک و محل Artifact | `UNVERIFIED` | Infrastructure/MLOps |
| Driver، CUDA، PyTorch و vLLM Version | `UNVERIFIED` | SRE/MLOps |
| OS، Container و Package Restrictions | `UNVERIFIED` | SRE/Security |
| Internal Network، Egress، Air-Gap، TLS و IAM | `UNVERIFIED` | Security/Network |
| Tokenizer، Model Revision و Artifact SHA-256 | `UNVERIFIED` | MLOps/Supply Chain |
| Input Length، Workload، Concurrency و SLO | `OPEN / OD-02/12` | Product Owner/SRE |
| ظرفیت توسعه و Headroom مجاز | `UNVERIFIED` | Infrastructure/SRE |

بدون Inventory واقعی، انتخاب قطعی GPU، تعداد Instance، Concurrency، Timeout یا Quantization ممکن نیست.

## ۲. محاسبه نظری حافظه — نه اندازه‌گیری

حافظه تقریبی وزن‌های Unquantized از رابطه `parameters × bytes_per_parameter` حاصل می‌شود. BF16/FP16 به‌صورت نظری ۲ بایت برای هر پارامتر استفاده می‌کنند؛ Memory مربوط به Kernel، Activation، Allocator، Temporary Buffer، Alignment و Runtime جداست.

| Candidate | پارامتر اعلام‌شده | BF16 Weight-only تخمینی | Context اعلام‌شده |
|---|---:|---:|---|
| Qwen2.5-7B-Instruct | ~7.62B | ~15.24 GB ده‌دهی (~14.19 GiB) | تا 131,072 با تنظیمات مناسب؛ تأیید عملی ندارد |
| Qwen3-14B | ~14.8B | ~29.60 GB ده‌دهی (~27.57 GiB) | 32,768 بومی؛ YaRN برای Context بالاتر مشروط |

### KV Cache

برای GQA ساده و Cache با BF16، تخمین حافظه از فرمول زیر به دست می‌آید:

`KV_bytes = 2 × num_layers × num_kv_heads × head_dim × bytes_per_element × cached_tokens × concurrent_sequences`

- برای Qwen2.5-7B-Instruct با ۲۸ لایه، ۴ KV Head و Head Dimension برابر ۱۲۸، برآورد ۵۷٬۳۴۴ بایت به‌ازای هر Token (حدود 56 KiB) است. برای یک Sequence با 32,768 Token حدود **1.75 GiB KV** می‌شود.
- برای Qwen3-14B با ۴۰ لایه، ۸ KV Head و Head Dimension برابر ۱۲۸، برآورد ۱۶۳٬۸۴۰ بایت به‌ازای هر Token (حدود 160 KiB) است. برای یک Sequence با 32,768 Token حدود **5.00 GiB KV** می‌شود.
- مجموع Weight+KV برای Qwen3-14B با یک Sequence مذکور، حدود **32.57 GiB نظری** و **بدون سربار اجرایی و Headroom** است. این عدد **حداقل VRAM سخت‌افزار تضمین‌شده نیست**.
- Formula با فرض Cache دو‌بایتی، Context کامل و یک Sequence محاسبه شده؛ Paged KV، Tensor Parallelism، Prefix Caching، Quantization، Fragmentation، Scheduler، Block Allocation و Concurrency می‌توانند مصرف واقعی را تغییر دهند.
- Quantization را نباید صرفاً با تقسیم حافظه وزن‌ها انتخاب کرد؛ اثر آن بر کیفیت فارسی، KV Dtype، Kernel و سازگاری Runtime باید مستقل Benchmark شود.

**برآورد Throughput یا Concurrency واقعی از تعداد پارامتر قابل اتکا نیست.** پیشنهاد اجرای ایمن: ابتدا Concurrency=1 و متن کوتاه، سپس افزایش مرحله‌ای طبق Limits تصویب‌شده، با سنجش Peak VRAM/Latency و توقف در شرایط خطر OOM. Context 8k، 16k، 32k و بلندتر فقط در صورت توان عملی و سیاست مجاز آزموده شود. YaRN ممکن است کیفیت Context کوتاه را هم تحت تأثیر قرار دهد.

## ۳. دستورات Inventory روی سرور سازمانی

فقط پس از دریافت مجوز و **داخل سرور داخلی** اجرا شود؛ خروجی در Storage مجاز ثبت گردد. این دستورات به‌خودی‌خود Benchmark نیستند.

```bash
nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.free --format=csv
uname -a
lscpu
free -h
df -h
python --version
python -m pip show vllm torch transformers
vllm --version
```

اگر ابزار نصب نیست، نتیجه `UNVERIFIED` ثبت شود؛ نباید عدد یا سازگاری Driver حدس زده شود. License، Tokenizer، Source Revision و Checksum Artifact باید **از همان فایل‌های انتقال‌یافته** در شبکه سازمان بررسی شوند.

## ۴. نمونه Runbook مشروط برای vLLM آفلاین

پیش از اجرا، نسخه واقعی CLI و پرچم‌های سازگار با مدل و Structured Output را با `vllm serve --help` بررسی کنید. کد زیر صرفاً **فرم پیشنهادی آزمایش روی محیط مجاز** است، نه دستور اجرای آماده Production:

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export MODEL_DIR="/approved/internal/model-directory"
export MAX_MODEL_LEN="8192"
test -d "$MODEL_DIR" || exit 1
test -f "$MODEL_DIR/config.json" || exit 1
vllm serve "$MODEL_DIR" --host 127.0.0.1 --port 8000 --max-model-len "$MAX_MODEL_LEN"
```

`MODEL_DIR` باید به مسیر **واقعی تأییدشده** سازمان تغییر کند. مقدار `8192` فقط Tier اولیه آزمایش و بدون تأیید ظرفیت/کیفیت است. Binding به Localhost برای Probe اولیه مناسب است؛ هیچ آدرس عمومی، دریافت Artifact از اینترنت یا ثبت Prompt خام مجاز نیست. تنظیمات Reasoning/Parser و Constrained JSON پس از تأیید نسخه واقعی Runtime اعمال شوند.

در هر Run، پارامترها و Token Budget ثابت شوند؛ Latency P50/P95، Generated Tokens/s، Concurrent Throughput، Prompt/Completion Tokens، GPU Utilization، Peak VRAM، Failure/Timeout/OOM و Context Limit به‌صورت واقعی ثبت شود. همه نتایج باید در [Benchmark Results](03_benchmark_results.md) همراه Dataset، Sample Count و Manifest بیایند.

## ۵. Risk Register و تصمیم‌های باز

| ریسک | شدت و اثر | مالک / تصمیم لازم |
|---|---|---|
| GPU یا VRAM ناشناخته/ناکافی | HIGH؛ نبود ظرفیت اثبات‌شده | Infrastructure/SRE، `OD-13` |
| License یا Artifact Provenance تأییدنشده | CRITICAL؛ خطر Legal/Supply Chain | Legal/Security/MLOps |
| Egress، Telemetry یا Log حاوی متن خام | CRITICAL؛ نقض محرمانگی | Security/Network، کنترل No-Egress |
| Dataset/Expert Labels ناموجود | HIGH؛ انتخاب مدل بدون شواهد | AI Lead/SMEs/PO، `OD-14` |
| Context بلند، OOM یا افت دقت | HIGH؛ کاهش کیفیت و ظرفیت | MLOps/SRE/AI Lead |
| SLO/Workload/Concurrency نامعلوم | HIGH؛ خطای ظرفیت‌سنجی | Product Owner/SRE، `OD-02/12` |
| Quantization تأییدنشده | MEDIUM/HIGH؛ افت پنهان Accuracy | MLOps/AI Lead |

**نتیجه فعلی Capacity Plan: `UNVERIFIED`؛ تصمیم انتخاب مدل/Runtime: `BLOCKED`.** بدون Measurement، تجویز قطعی GPU با ظرفیت ۲۴/۴۸/۸۰ GB، خرید یا افزایش منابع توجیه فنی معتبر ندارد. عملیات Production، انتقال Artifact و تغییر شبکه به مجوز جداگانه نیاز دارند.

ارجاع: [انتخاب مدل](01_model_selection.md) · [پروتکل](02_benchmark_protocol.md) · [نتایج](03_benchmark_results.md).

## ۶. D-017 — جایگاه Resource Plan در مراحل پروژه

Memory/Weight/KV Cache و Runbook این سند خروجی نظری Stage 03 هستند، نه اندازه‌گیری واقعی. GPU/VRAM/Latency/Throughput/Capacity و اجرای vLLM در Stage 11 و با مجوز سازمانی تست می‌شوند (`DEFERRED_TO_STAGE_11`) و تا آن زمان PASSED نیستند. نبود Inventory سرور مانع Gate آفلاین Stage 03 نیست؛ هیچ تصمیم Procurement/Production بر پایه اعداد نظری قطعی نمی‌شود. [Ledger](03_benchmark_results.md#12-d-017-deferred-on-premise-test-ledger).
