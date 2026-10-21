# Evaluation Rubrics — Stage 01

> **Status: PROVISIONAL_FOR_INTERNAL_TESTING** · 2026-10-21 · Baseline: Implementation Plan §§1.2,4,6,7,10/Stage 01; execution override `D-015`. Weights and anchors are NOT business-approved. Candidate rubric identifier: `candidate-0.1` (not an officially Published rubric). **Formal SME/employer acceptance is deferred to Stage 12**, not required to mark each engineering stage complete.

## Common contract and interpretation

Each `rubric_version` must ultimately store `code`, `version`, `status`, `criteria`, `coverage_policy`, `checksum`; a Published snapshot cannot be edited (FR-03). All 18 candidates below define `criterion_code`, `name`, `operational_definition`, `weight`, `required`, `scoring_anchors` 0..5, `evaluation_instructions`, `evidence_requirements`, `applicability_rules`.

- `assessed`: score **integer 0..5** after evidence/schema checks; 0 means demonstrated poor quality, NOT no evidence.
- `not_assessed`: **score null** plus reason; possible reason codes: `INSUFFICIENT_TEXT`, `MISSING_CONTEXT`, `NOT_APPLICABLE`, `UNVERIFIED_SOURCE`, `EVIDENCE_UNVERIFIABLE`, `MODEL_UNCERTAIN`, `INPUT_QUALITY_LIMITATION` (code vocabulary PROPOSED). Missing required criterion triggers review/partial per policy.
- `coverage`: applicable assessed weight / all applicable weight. `final_score`: 100 × Σ(weight × score/5) / Σ(assessed applicable weights), computed by Python, not LLM. Nonpositive weights, zero denominator, empty assessed set and score outside range are errors. Rounding/threshold/denominator applicability are `OD-04` OPEN.
- `needs_human_review`: when required evidence absent, approved coverage gate not met, epistemic limitation/ambiguous reference or conflicting evidence. Business taxonomy (flag and/or result status), workflow owner and publication policy `OD-04/09` OPEN.
- Evidence proposal: `quote`, `start_offset`, `end_offset`, exact mapping to **original text**; quote must support finding. Offset unit and Unicode/ZWNJ normalization policy `OD-11` OPEN. Invalid or absent evidence must not create a fabricated score.
- Every criterion's `required` flag and weight here is a **proposal**. Applicability metadata must distinguish inapplicable criteria from evidence failure. Applicability affects Coverage denominator only according to approved deterministic rules.
- No grading audio/body language for speech, measured reach/engagement for media, factual truth/real citation/novelty without trusted corpus for research. No political-alignment grading.

## Candidate weights

| Domain | Criterion code | Weight | Required candidate |
|---|---|---:|---|
| `speech` | `speech_coherence` | 25 | true |
| `speech` | `speech_structure` | 20 | true |
| `speech` | `speech_clarity` | 20 | true |
| `speech` | `speech_writing` | 15 | true |
| `speech` | `speech_reasoning` | 10 | false |
| `speech` | `speech_audience_fit` | 10 | false |
| `media` | `media_tone` | 25 | true |
| `media` | `media_message_clarity` | 20 | true |
| `media` | `media_writing` | 20 | true |
| `media` | `media_structure` | 15 | true |
| `media` | `media_audience_focus` | 10 | false |
| `media` | `media_text_effectiveness` | 10 | false |
| `research` | `research_coherence` | 20 | true |
| `research` | `research_methodology` | 20 | false |
| `research` | `research_reasoning` | 20 | true |
| `research` | `research_academic_writing` | 15 | true |
| `research` | `research_citations` | 15 | false |
| `research` | `research_novelty` | 10 | false |

**Weight sum:** speech = 100, media = 100, research = 100; all PROPOSED from Implementation Plan §4.2.

## SPEECH rubric

### `speech_coherence` — انسجام منطقی

- `criterion_code`: `speech_coherence`
- `name`: انسجام منطقی
- `operational_definition`: اتصال منطقی مقدمه، ادعاها، گذارها و نتیجه
- `weight`: 25 / 100 (**PROPOSED**)
- `required`: true (**PROPOSED**)
- `evaluation_instructions`: رابطه منطقی بندها را بسنج؛ موضع سیاسی را ملاک قرار نده
- `evidence_requirements`: نقل‌قول از گذار/ادعا و نتیجه، offset متن اصلی; quote + original offsets
- `applicability_rules`: در متن چندبخشی؛ بریده بدون زمینه not_assessed
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | گسست/تناقض فراگیر |
| 1 | گسست‌های عمده |
| 2 | پرش‌های منطقی متعدد |
| 3 | خط اصلی روشن با چند شکاف |
| 4 | گذارهای عمدتاً دقیق |
| 5 | پیوندها و نتیجه‌گیری کاملاً منسجم |

### `speech_structure` — ساختار

- `criterion_code`: `speech_structure`
- `name`: ساختار
- `operational_definition`: وجود آغاز، بسط و پایان متناسب
- `weight`: 20 / 100 (**PROPOSED**)
- `required`: true (**PROPOSED**)
- `evaluation_instructions`: وظیفه و ترتیب بخش‌ها را بررسی کن
- `evidence_requirements`: شاهد آغاز/بسط/پایان یا فقدان آن; quote + original offsets
- `applicability_rules`: فقط برای متن کامل؛ قطعه ناقص not_assessed
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | فاقد هر ساختار |
| 1 | چیدمان آشفته |
| 2 | ساختار ناقص و مخدوش |
| 3 | ساختار قابل‌تشخیص با نقص |
| 4 | ساختار منظم با ضعف محدود |
| 5 | ساختار بسیار روشن و متناسب |

### `speech_clarity` — وضوح متنی

- `criterion_code`: `speech_clarity`
- `name`: وضوح متنی
- `operational_definition`: درک‌پذیری جمله‌ها و ارجاعات
- `weight`: 20 / 100 (**PROPOSED**)
- `required`: true (**PROPOSED**)
- `evaluation_instructions`: ابهام واژگانی، ضمیر و تراکم جمله را بسنج، نه اجرای صوتی
- `evidence_requirements`: نقل‌قول جمله مبهم/واضح با offset; quote + original offsets
- `applicability_rules`: متن کافی؛ خطای احتمالی STT جدا گزارش شود
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | پیام نامفهوم |
| 1 | ابهام غالب |
| 2 | ابهام زیاد |
| 3 | پیام عمدتاً روشن |
| 4 | ابهام اندک |
| 5 | کاملاً روشن و دقیق |

### `speech_writing` — نگارش

- `criterion_code`: `speech_writing`
- `name`: نگارش
- `operational_definition`: دستور، املا، نشانه‌گذاری و انتخاب واژگان فارسی
- `weight`: 15 / 100 (**PROPOSED**)
- `required`: true (**PROPOSED**)
- `evaluation_instructions`: سبک محاوره/رسمی معلوم را رعایت کن
- `evidence_requirements`: نمونه واقعی خطا و موقعیت آن; quote + original offsets
- `applicability_rules`: گویش و خطای STT را خودکار ضعف متن نشمار
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | مانع خواندن |
| 1 | خطای بسیار زیاد |
| 2 | خطای مکرر |
| 3 | خطاهای متوسط |
| 4 | خطاهای جزئی |
| 5 | نگارش سازگار و دقیق |

### `speech_reasoning` — استدلال

- `criterion_code`: `speech_reasoning`
- `name`: استدلال
- `operational_definition`: وضوح نسبت ادعا و دلایل ارائه‌شده
- `weight`: 10 / 100 (**PROPOSED**)
- `required`: false (**PROPOSED**)
- `evaluation_instructions`: استدلال متنی را بسنج نه حقیقت بیرونی بدون منبع
- `evidence_requirements`: ادعا و دلیل/فقدان دلیل در متن; quote + original offsets
- `applicability_rules`: سخنرانی غیر‌استدلالی: not_assessed
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | تناقض و بی‌دلیلی شدید |
| 1 | پشتیبانی بسیار ضعیف |
| 2 | دلایل ناکافی مکرر |
| 3 | برخی دلایل کافی |
| 4 | اغلب ادعاها مستدل |
| 5 | تمام ادعاهای اصلی منطقی و مستدل در متن |

### `speech_audience_fit` — تناسب با مخاطب

- `criterion_code`: `speech_audience_fit`
- `name`: تناسب با مخاطب
- `operational_definition`: سازگاری توضیحات و سطح زبان با مخاطب معرفی‌شده
- `weight`: 10 / 100 (**PROPOSED**)
- `required`: false (**PROPOSED**)
- `evaluation_instructions`: به metadata مخاطب تکیه کن، آن را حدس نزن
- `evidence_requirements`: عبارت‌های تخصصی/خطاب با context مخاطب; quote + original offsets
- `applicability_rules`: بدون target_audience مصوب: not_assessed
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | کاملاً ناسازگار |
| 1 | اغلب نامناسب |
| 2 | عدم تناسب متعدد |
| 3 | تناسب متوسط |
| 4 | مناسب با نقص جزئی |
| 5 | کاملاً مناسب مخاطب معلوم |

## MEDIA rubric

### `media_tone` — لحن

- `criterion_code`: `media_tone`
- `name`: لحن
- `operational_definition`: یکدستی و تناسب لحن نوشتاری با هدف معلوم
- `weight`: 25 / 100 (**PROPOSED**)
- `required`: true (**PROPOSED**)
- `evaluation_instructions`: از نشانگرهای زبانی استدلال کن؛ قضاوت سیاسی نکن
- `evidence_requirements`: عبارت‌های شاخص لحن و هدف تأییدشده; quote + original offsets
- `applicability_rules`: بدون راهنمای لحن فقط یکدستی قابل‌سنجش؛ تناسب سازمانی not_assessed
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | لحن متناقض/مخدوش |
| 1 | ناسازگاری فراگیر |
| 2 | نوسان زیاد |
| 3 | غالباً یکدست |
| 4 | لحن متناسب با ضعف جزئی |
| 5 | یکدست و دقیقاً مطابق هدف معلوم |

### `media_message_clarity` — وضوح پیام

- `criterion_code`: `media_message_clarity`
- `name`: وضوح پیام
- `operational_definition`: آشکار بودن موضوع و پیام کلیدی
- `weight`: 20 / 100 (**PROPOSED**)
- `required`: true (**PROPOSED**)
- `evaluation_instructions`: وجود پیام اصلی را بسنج؛ CTA را فقط در صورت الزام بررسی کن
- `evidence_requirements`: شاهد پیام اصلی/ابهام در نقل‌قول; quote + original offsets
- `applicability_rules`: متن کامل؛ بریده نامعلوم: not_assessed
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | پیام نامعلوم |
| 1 | پیام بسیار گنگ |
| 2 | پیام مبهم |
| 3 | پیام اصلی قابل‌فهم |
| 4 | پیام روشن |
| 5 | پیام دقیق و متمرکز |

### `media_writing` — نگارش

- `criterion_code`: `media_writing`
- `name`: نگارش
- `operational_definition`: املا، دستور و خوانایی متن رسانه‌ای
- `weight`: 20 / 100 (**PROPOSED**)
- `required`: true (**PROPOSED**)
- `evaluation_instructions`: سبک کانال مشخص را در نظر بگیر
- `evidence_requirements`: نقل‌قول خطای واقعی با offsets; quote + original offsets
- `applicability_rules`: در نبود سبک مصوب قضاوت قالبی نکن
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | خطاهای مانع فهم |
| 1 | خطاهای فراگیر |
| 2 | چند خطای شدید |
| 3 | خطای محدود |
| 4 | بسیار کم‌اشکال |
| 5 | نگارش دقیق و متناسب |

### `media_structure` — ساختار

- `criterion_code`: `media_structure`
- `name`: ساختار
- `operational_definition`: ترتیب ارائه پیام و بخش‌بندی
- `weight`: 15 / 100 (**PROPOSED**)
- `required`: true (**PROPOSED**)
- `evaluation_instructions`: چیدمان اطلاعات در متن را بررسی کن
- `evidence_requirements`: شواهد ترتیب اطلاعات/تیتر در صورت کاربرد; quote + original offsets
- `applicability_rules`: شرط‌های پلتفرم فقط با channel مصوب
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | آشفتگی کامل |
| 1 | ساختار بسیار مخدوش |
| 2 | نقص‌های عمده |
| 3 | ساختار قابل‌قبول |
| 4 | ساختار منظم |
| 5 | ترتیب بسیار روشن و مناسب |

### `media_audience_focus` — مخاطب‌محوری

- `criterion_code`: `media_audience_focus`
- `name`: مخاطب‌محوری
- `operational_definition`: تناسب زبان و اطلاعات با مخاطب مشخص
- `weight`: 10 / 100 (**PROPOSED**)
- `required`: false (**PROPOSED**)
- `evaluation_instructions`: نیاز مخاطب را از metadata معتبر بگیر
- `evidence_requirements`: شاهد خطاب/سطح توضیح در متن; quote + original offsets
- `applicability_rules`: بدون target_audience: not_assessed
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | بی‌ارتباط |
| 1 | اغلب نامناسب |
| 2 | تناسب ضعیف |
| 3 | متوسط |
| 4 | متناسب |
| 5 | بسیار متناسب با مخاطب معلوم |

### `media_text_effectiveness` — شاخص اثربخشی متنی

- `criterion_code`: `media_text_effectiveness`
- `name`: شاخص اثربخشی متنی
- `operational_definition`: ویژگی متنی یاریگر هدف ارتباطی؛ نه اثر واقعی
- `weight`: 10 / 100 (**PROPOSED**)
- `required`: false (**PROPOSED**)
- `evaluation_instructions`: فقط تمرکز، برجستگی پیام و CTA لازم را بسنج، نه engagement
- `evidence_requirements`: شواهد پیام/CTA مرتبط با purpose; quote + original offsets
- `applicability_rules`: بدون purpose معتبر: not_assessed؛ textual_proxy اجباری
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | متن علیه هدف اعلام‌شده |
| 1 | نشانگرهای هدف غایب |
| 2 | پشتیبانی ضعیف |
| 3 | پشتیبانی متوسط |
| 4 | پشتیبانی قوی |
| 5 | پشتیبانی متنی بسیار دقیق؛ بدون ادعای اثر واقعی |

## RESEARCH rubric

### `research_coherence` — انسجام علمی

- `criterion_code`: `research_coherence`
- `name`: انسجام علمی
- `operational_definition`: هم‌راستایی سؤال، بحث، نتیجه و حدود استنتاج
- `weight`: 20 / 100 (**PROPOSED**)
- `required`: true (**PROPOSED**)
- `evaluation_instructions`: رابطه بخش‌ها را بررسی کن نه حقیقت ادعا را
- `evidence_requirements`: شواهد سؤال/هدف و نتیجه; quote + original offsets
- `applicability_rules`: بخش‌های ناکافی: not_assessed
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | ناسازگاری شدید |
| 1 | ناهم‌خوانی عمده |
| 2 | شکاف‌های مهم |
| 3 | انسجام نسبی |
| 4 | انسجام بالا |
| 5 | هماهنگی کامل در محدوده متن |

### `research_methodology` — شفافیت روش‌شناسی

- `criterion_code`: `research_methodology`
- `name`: شفافیت روش‌شناسی
- `operational_definition`: وضوح گزارش طراحی، داده و روش؛ نه تصدیق اعتبار روش
- `weight`: 20 / 100 (**PROPOSED**)
- `required`: false (**PROPOSED**)
- `evaluation_instructions`: مراحل قابل ردیابی و محدودیت‌ها را بررسی کن
- `evidence_requirements`: نقل‌قول توصیف روش/داده یا فقدان آن; quote + original offsets
- `applicability_rules`: برای نوع پژوهش نیازمند روش؛ نوشته نظری با روش غیرتجربی مستقل بررسی شود
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | روش مبهم/متناقض |
| 1 | اجزای اصلی غایب |
| 2 | ابهام گسترده |
| 3 | روش تا حدی روشن |
| 4 | روش روشن |
| 5 | روش بسیار شفاف و قابل پیگیری |

### `research_reasoning` — استدلال علمی

- `criterion_code`: `research_reasoning`
- `name`: استدلال علمی
- `operational_definition`: رابطه ادعا، داده ارائه‌شده و نتیجه
- `weight`: 20 / 100 (**PROPOSED**)
- `required`: true (**PROPOSED**)
- `evaluation_instructions`: ادعا و دلیل را جدا کن؛ حقیقت بیرونی را تأیید نکن
- `evidence_requirements`: شواهد ادعا و دلیل/نتیجه در متن; quote + original offsets
- `applicability_rules`: متن استدلالی کافی؛ قطعه ناکافی not_assessed
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | نتیجه‌گیری متناقض |
| 1 | بدون پشتیبانی کافی |
| 2 | شکاف‌های جدی |
| 3 | استدلال متوسط |
| 4 | استدلال قوی |
| 5 | استنتاج‌های دقیق و محدود به شواهد |

### `research_academic_writing` — نگارش علمی

- `criterion_code`: `research_academic_writing`
- `name`: نگارش علمی
- `operational_definition`: دقت اصطلاحات، دستور و وضوح بیان علمی
- `weight`: 15 / 100 (**PROPOSED**)
- `required`: true (**PROPOSED**)
- `evaluation_instructions`: سبک رشته معتبر را لحاظ کن
- `evidence_requirements`: عبارات تعریف‌نشده/مبهم یا صحیح; quote + original offsets
- `applicability_rules`: بدون discipline تخصصی ادعای خطای اصطلاح نکن
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | نگارش مانع فهم |
| 1 | ابهام فراگیر |
| 2 | ابهام مکرر |
| 3 | قابل‌قبول |
| 4 | دقیق با اشکال اندک |
| 5 | بیان علمی دقیق و سازگار |

### `research_citations` — شیوه استناد

- `criterion_code`: `research_citations`
- `name`: شیوه استناد
- `operational_definition`: سازگاری ارجاع درون متن و فهرست منابع، نه اصالت منبع
- `weight`: 15 / 100 (**PROPOSED**)
- `required`: false (**PROPOSED**)
- `evaluation_instructions`: تطبیق ارجاعات ظاهری؛ بدون منبع معتبر ادعای وجود منبع نکن
- `evidence_requirements`: نقل‌قول ارجاع و مدخل منابع مرتبط; quote + original offsets
- `applicability_rules`: در متن مستلزم ارجاع؛ در غیراین‌صورت not_assessed
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | ارجاعات کاملاً مخدوش |
| 1 | نقص بسیار شدید |
| 2 | ناسازگاری فراوان |
| 3 | نقص‌های محدود |
| 4 | ارجاعات عمدتاً سازگار |
| 5 | ارجاعات ظاهراً سازگار؛ اصالت تأییدنشده |

### `research_novelty` — نوآوری قابل‌بررسی

- `criterion_code`: `research_novelty`
- `name`: نوآوری قابل‌بررسی
- `operational_definition`: تمایز در محدوده Corpus معتبر و روش داوری مصوب
- `weight`: 10 / 100 (**PROPOSED**)
- `required`: false (**PROPOSED**)
- `evaluation_instructions`: بدون Corpus و روش معتبر حتماً not_assessed؛ novelty مطلق ادعا نکن
- `evidence_requirements`: ادعای نویسنده + اسناد Corpus و مقایسه قابل ارجاع; quote + original offsets
- `applicability_rules`: تنها با Corpus مجاز، پوشش کافی و پروتکل/داوری مصوب
- `scoring_anchors` (proposed):

| Score | Observable anchor |
|---:|---|
| 0 | مقایسه معتبر ادعا را رد می‌کند |
| 1 | تمایز بسیار ضعیف |
| 2 | تمایز جزئی |
| 3 | تمایز محدود ولی مستند |
| 4 | تمایز قابل‌توجه |
| 5 | تمایز قوی در Corpus مصوب، نه اثبات مطلق |

## Evaluation abstention / worked boundaries

1. `research_novelty` without authorized comparative Corpus + approved method → `not_assessed`, `score=null`, `needs_human_review=true`; mere novelty language does not constitute evidence.
2. `research_citations` scores visible *format/consistency*, never real-world existence of sources without verification.
3. `media_text_effectiveness` is a **textual proxy** conditional on purpose; never assert actual engagement or conversion.
4. `speech_audience_fit` without approved audience metadata → `not_assessed`; STT-origin uncertainty recorded separately; no grading oral delivery.
5. Fully missing assessable set → **no final numeric score**; no division by zero; required failures trigger human review according to approved policy.
6. The six anchors describe observable rubric-specific behavior, but SMEs must calibrate borderline examples and check inter-rater agreement before publication.

## Approval and traceability

**Business acceptance is deferred, not waived:** all weights, anchors, scope, required flags, applicability, acceptable evidence examples and thresholds remain OPEN (`OD-03/04/11/14`) for formal final Stage 12 acceptance under `D-015`. Internal Stage 03/06/08/11 engineering and benchmarking may use identified, frozen **candidate versions** and permitted synthetic data, explicitly labeled non-official. No unapproved rubric may generate a purportedly official enterprise score; no final Production release without real domain expert review and quality gates. FR-02..06, FR-11; Stage 03 benchmark, Stage 06 version management, Stage 08 engine, Stage 11 AI regression. See [product](01_product_requirements.md), [acceptance](03_acceptance_criteria.md), [decisions](05_open_decisions.md).
