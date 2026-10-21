# Text Evaluation Service — Product Requirements (Stage 01)

> **Document status:** DRAFT_FOR_INTERNAL_REVIEW · external employer acceptance deferred to Stage 12 (`D-015`)  
> **Date:** 2026-10-21  
> **Baseline:** `Text_Evaluation_Service_Implementation_Plan_FA.md` v1.0.0, §§1, 4–7, 10/Stage 01, 11, 13–14; `Service_Architecture_Guide_FA.md`.  
> **Change control:** This specification is NOT employer-approved. Under confirmed execution policy `D-015`, formal external acceptance occurs at Stage 12. Prior stages may document and technically test versioned **provisional** decisions with permitted synthetic data; no unknown numeric requirement becomes approved or an official score. Specific permissions/security prerequisites remain mandatory before protected-data or Production operations. See [Decision Log](05_open_decisions.md).

## 1. Purpose, stakeholders and hard constraints

هدف، ارزیابی قابل‌ممیزی **متن فارسی** در سه حوزه `speech`, `media`, `research` با Rubric نسخه‌دار، شواهد قابل‌تطبیق، امتیازدهی قطعی Python و ثبت نتایج است. محصول نهایی سازمانی، Production-Grade، درون‌سازمانی و Confidential-by-Design است؛ MVP نیست.

**Confirmed constraints:** `D-001` محصول سازمانی، `D-002` Inference تماماً داخلی و عدم ارسال متن به AI Provider خارجی، `D-003` استاندارد چهارلایه `Host → Application → Core → Infrastructure`، `D-004` پیشروی مرحله‌ای و عبور از Gate. برای هر Component آتی، Constructor DI/`@inject`، Thin Controller، Service Layer، Repository Pattern، SQLAlchemy Async، `BaseRepository` و Alembic طبق سند مرجع رعایت خواهد شد. این سند هیچ کد یا API موجودی را فرض نمی‌کند.

**Stakeholders / approval roles (organizational identities OPEN):** Employer/Product Owner (scope and acceptance), Speech Subject Matter Expert (SME), Media SME, Research SME, Security/Privacy Officer, Identity/IAM Owner, Infrastructure/SRE Owner, AI Quality Lead, Data Steward/Legal, Authorized Reviewer. این عناوین نقش تصمیم هستند، نه کاربران یا سمت‌های سازمانیِ تأییدشده.

## 2. Domain scope and boundaries

| Domain | Input/material under analysis | Meaningful intended assessment | Prohibited overclaim | Business metadata candidates, not approved |
|---|---|---|---|---|
| `speech` | متن سخنرانی آماده‌شده یا پیاده‌سازی‌شده | انسجام، ساختار، وضوح، نگارش، استدلال، تناسب با مخاطب | صدا، مکث، لحن صوتی، اجرا، زبان بدن | purpose, target_audience, source_is_transcript, transcript_quality |
| `media` | متن روابط عمومی، اطلاعیه یا پست شبکه اجتماعی | لحن متنی، وضوح پیام، نگارش، ساختار، مخاطب‌محوری و شاخص‌های متنی اثربخشی | نرخ تعامل، تأثیر واقعی بر مخاطب و دسترسی واقعی | channel, purpose, target_audience, brand_style_guide_reference |
| `research` | متن مقاله یا گزارش پژوهشی | انسجام علمی، شفافیت روش، استدلال، نگارش علمی، نحوه استناد و نوآوری **مشروط** | صحت علمی، اصالت منابع، نوآوری واقعی بدون Corpus/verification | discipline, document_type, citation_style, approved_reference_corpus |

**In scope — confirmed business capability:** دریافت متن، ارزیابی سه حوزه با Rubric مجزا، معیار و شواهد، امتیاز و Coverage، عدم‌ارزیابی/ارجاع انسانی، پردازش غیرهم‌زمان پایدار، بازیابی امن، بازخورد کارشناسی/Audit، Inference داخلی، متن بلند و ردیابی نسخه‌ها (`FR-01..FR-12`).  
**Not approved as in scope:** ingest مستقیم PDF/DOCX، صوت/STT در سرویس، OCR، اتصال اینترنت، راستی‌آزمایی اینترنتی، ترجمه، تولید متن، تشخیص عقیده/گرایش سیاسی، انتشار خودکار محتوا، سنجش اثر واقعی رسانه، plagiarism/originality certification، مدیریت کامل Admin/Export/Cancel/Delete/Re-evaluation؛ این موارد باید در `OD-01`, `OD-05`, `OD-06` تعیین شوند. عدم تصویب به معنی رد دائمی نیست.

**Input contract — proposed for business review:** `text` (original string), `evaluation_type` (یکی از سه مقدار)، context metadata از allowlist مصوب، identity/org scope حاصل از Auth نه بدنه غیرقابل‌اعتماد، rubric version resolve شده. نوع فایل، encoding validation، زبان‌های غیرفارسی و mixed-language، حداقل/حداکثر کاراکتر/توکن/بایت، نوع metadata اجباری و محدودیت هر کانال هنوز `OPEN` هستند (`OD-01/02`). متن ورودی غیرقابل‌اعتماد و صرفاً موضوع ارزیابی است.

### Input requirements matrix — explicit candidate contract, NOT business-approved

The following is a **design input to Stage 02**, not a statement that employer-provided constraints are confirmed. Fields marked OPEN MUST remain configurable/versioned or blocked from official production use until their actual policy is known. Domain/type must be explicit; a model may not silently choose the business domain.

| Field / policy | `speech` | `media` | `research` | Candidate validation, unresolved policy and decision |
|---|---|---|---|---|
| `evaluation_type` | `speech` | `media` | `research` | Required, exact allowed enum; invalid/mismatch rejected, FR-01/02 |
| `text` | Prepared or transcribed speech text | PR/news/social media written text | Article or research report text | Required, nonempty Unicode text; allowed MIME/encoding, byte/token/character min/max all OPEN (`OD-01/02`); never silently truncate |
| `source_format` | Plain text candidate; transcript provenance is context | Plain text candidate; channel is context | Plain text candidate; long document sections possible | Direct PDF/DOCX, STT, OCR and other ingest **not in approved scope**; `OD-01/05` for future capability |
| `purpose` | Speech objective (optional candidate) | Message objective (optional candidate) | Research objective (optional candidate) | Optional candidate, structured allowlist, max length/content policy OPEN (`OD-01/02`) |
| `target_audience` | Needed for audience-fit assessment if available | Needed for audience-focus assessment if available | Intended scholarly audience (optional candidate) | Optional input candidate; missing context must not cause invented audience claims; mark affected criteria `not_assessed` if appropriate |
| `source_is_transcript` / `transcript_quality` | Optional candidate provenance and input-quality indicator | N/A | N/A | Source transcription uncertainty is separate from speaking performance; no scoring audio delivery |
| `channel` / `brand_style_guide_reference` | N/A | Optional candidate media channel / authorized internal style-guide ID | N/A | No unrestricted URL fetching; reference existence/authorization require validation (`OD-01/08/11`) |
| `discipline` / `document_type` / `citation_style` | N/A | N/A | Optional candidate research context | Accepted values / requiredness OPEN (`OD-01/03/11`); citation formatting ≠ reference authenticity |
| `approved_reference_corpus` | N/A | N/A | Authorized corpus identifier only, **not arbitrary path/URL** | Corpus selection/access/provenance OPEN (`OD-08/11/14`); absent trusted corpus ⇒ real novelty `not_assessed` |
| Language / mixed scripts | Persian written text required by product brief | Persian written text required by product brief | Persian written text required by product brief | Support/rejection of Arabic script variants, English segments, mixed-language, Unicode normalization, ZWNJ and RTL metadata OPEN (`OD-01/11`) |
| Length and sections | Limits OPEN | Limits OPEN | Higher long-document/context need; exact limits OPEN | Record chars/UTF-8 bytes/token estimates; no assumed cap, no unconditional acceptance of arbitrarily long text (`OD-02/12`) |
| Ownership / tenant / identity | Derived server-side | Derived server-side | Derived server-side | Never accept authenticated owner/org from client metadata; SSO, Role Matrix and cross-unit access OPEN (`OD-07`) |
| Idempotency / reuse | Candidate per-scope idempotency key | Same | Same | Window, collision response, deduplication semantics OPEN (`OD-10`); never deduplicate across organizational scopes |

**Stage 02 design boundary:** DTO and API examples may use clearly labeled synthetic, versioned provisional allowlists. They must not silently hardcode unapproved size/retention/role policies or treat candidate domain metadata as universally mandatory. For final delivery, each OPEN policy must be resolved, explicitly rejected as out-of-scope, or represented by a justified protective behavior without pretending it has employer approval.

## 3. User workflows and role boundaries (logical, proposed)

1. **Submitter / authorized internal client:** احراز هویت ← انتخاب حوزه و ارسال متن و زمینه مجاز ← کنترل ورودی/مجوز/محدودیت ← ثبت Evaluation و Job با نسخه Rubric ثابت ← دریافت شناسه پیگیری بدون افشای متن در Log.
2. **Internal worker:** Claim امن Job ← پردازش متن و استخراج شواهد ← ارزیابی معیارها با Runtime داخلی ← Schema/Evidence/Applicability Validation ← محاسبه نمره Python ← ذخیره اتمیک گزارش و وضعیت ← Audit فاقد متن خام.
3. **Owner / permitted reader:** دریافت وضعیت و گزارش فقط در Scope مجاز؛ فیلدهای قابل‌مشاهده براساس سیاست Classification.
4. **Expert reviewer:** مشاهده مورد ارجاع‌شده در Scope مجاز؛ ثبت نظر، اصلاح کارشناسی و دلیل، بدون حذف تاریخچه AI؛ دسترسی به متن اصلی فقط در صورت مجوز.
5. **Rubric administrator / approver (role not approved):** ایجاد پیش‌نویس، بررسی و انتشار نسخه جدید فقط در Scope تصویب‌شده؛ انتشار باید Audit و Immutability داشته باشد.
6. **Security/SRE auditor:** مشاهده رویدادهای حداقلی و Metrics فاقد داده متنی؛ حق خواندن متن از نقش عملیاتی به‌طور ضمنی حاصل نمی‌شود.

Permission Matrix نهایی و نحوه تخصیص نقش‌ها `OPEN` است (`OD-07`). هیچ کاربری با دانستن UUID مجاز به خواندن نتیجه دیگری نیست.

## 4. Functional requirements — normative intent; unresolved decisions identified

### FR-01 — Valid text submission and allowed context
- **Business objective:** دریافت امن و یک‌شکل محتوای موردارزیابی بدون نشت یا خطای حوزه.
- **Expected behavior / user story:** به‌عنوان Submitter مجاز، متن و `evaluation_type` و metadata در allowlist را ثبت می‌کنم؛ سرویس Auth، Scope، Validation و idempotency را اعمال کرده و ارزیابی قابل‌پیگیری ایجاد می‌کند.
- **Success:** ورودی فارسی معتبر برای `speech` پذیرفته، owner/scope معتبر server-side ثبت و شناسه یکتا برگردانده می‌شود.
- **Error:** متن خالی، نوع ناشناخته، بایت/توکن بیش از سقف تصویب‌شده، metadata غیرمجاز یا identity نامعتبر با خطای امن رد می‌شود؛ Job ناقص ایجاد نمی‌شود.
- **Constraints:** حدها، encoding policy، language policy، idempotency window و metadata `OPEN` (`OD-01/02/10`). متن در Error/Log بازتاب داده نشود.
- **Acceptance:** `AC-FR-01-A/B/C` در سند 03.

### FR-02 — Domain-specific rubric selection
- **Objective:** جلوگیری از ارزیابی غلط بین سه نوع متن.
- **Expected:** هر `evaluation_type` دقیقاً به Rubric معتبر همان حوزه Resolve شود.
- **Success:** `research` فقط Criteria مصوب Research را به کار می‌برد.
- **Error:** نبود نسخه Published یا Type mismatch منجر به خطای کنترل‌شده/عدم شروع ارزیابی می‌شود.
- **Constraints:** Rubricهای سند 02 هنوز پیشنهادی‌اند؛ توسعه و تست داخلی با Rubric کاندید و داده مجاز ممکن است؛ **انتشار به‌عنوان معیار رسمی سازمانی** نیازمند پذیرش نهایی در Stage 12 است (`D-015`, `OD-03`).
- **Acceptance:** `AC-FR-02-A/B`.

### FR-03 — Immutable versioned rubric
- **Objective:** امکان دفاع، ممیزی و مقایسه ارزیابی‌ها در زمان.
- **Expected:** هر درخواست به Snapshot/Checksum نسخه Published شامل anchors/weights/instructions متصل شود؛ نسخه Published قابل تغییر درجا نباشد.
- **Success:** انتشار نسخه جدید نتیجه تاریخی را تغییر نمی‌دهد.
- **Error:** تغییر نسخه Published یا version ناقص رد و ثبت Audit می‌شود.
- **Constraints:** Draft/Publish/Retire permission و approval workflow `OPEN` (`OD-06`).
- **Acceptance:** `AC-FR-03-A/B`.

### FR-04 — Per-criterion structured evaluation
- **Objective:** گزارش توضیح‌پذیر و قابل‌اقدام، فراتر از یک عدد.
- **Expected:** برای معیار Assessed، score integer 0..5، reason، strengths، weaknesses، evidence واقعی و recommendations نگهداری شوند؛ اجزای LLM Untrusted هستند.
- **Success:** نقل‌قول و offset مطابق Original Text معتبر و Reason مرتبط با anchor است.
- **Error:** JSON/Schema اشتباه، score نامعتبر، quote ساختگی یا ادعای بدون پشتوانه رد/بازپردازش محدود یا Unassessed می‌شود.
- **Constraints:** Contract دقیق offset/Unicode و evidence relevance `OPEN` (`OD-11`).
- **Acceptance:** `AC-FR-04-A/B`.

### FR-05 — Deterministic aggregate score and coverage
- **Objective:** نمره شفاف، قابل محاسبه مجدد و مستقل از قضاوت جمع‌بندی LLM.
- **Expected:** `final_score = 100 * sum(w_i*s_i/5 for assessed applicable i) / sum(w_i for assessed applicable i)`; `coverage = sum(w_i for assessed applicable i) / sum(w_i for all applicable i)`. همه اعداد از ورودی‌های اعتبارسنجی‌شده و Python به‌دست آیند.
- **Success:** محاسبه مجدد با همان Snapshot/criterion scores دقیقاً نتیجه ذخیره‌شده را تولید می‌کند.
- **Error:** مجموعه Assessed خالی، وزن نامعتبر، score خارج از 0..5 یا مخرج صفر => وضعیت کنترل‌شده، نه نمایش امتیاز ظاهراً معتبر.
- **Constraints:** rounding/precision، coverage threshold، policy required و applicability باید تصویب شوند (`OD-04`).
- **Acceptance:** `AC-FR-05-A/B/C`.

### FR-06 — Honest abstention and human review
- **Objective:** جلوگیری از یقین ساختگی و امتیاز نادرست.
- **Expected:** `not_assessed` با reason، نبود score و شرایط روشن برای `partial` / `needs_human_review`. معیار Required بدون شواهد یا coverage ناکافی ارجاع شود.
- **Success:** نوآوری واقعی مقاله فاقد Corpus معتبر، بدون score و با Review Flag ثبت می‌شود.
- **Error:** تبدیل `not_assessed` به 0 یا انتشار Score نهایی به‌عنوان Complete برخلاف Policy رد می‌شود.
- **Constraints:** owner و SLA بررسی انسانی، آستانه‌ها و publishability `OPEN` (`OD-04/09`).
- **Acceptance:** `AC-FR-06-A/B`.

### FR-07 — Durable asynchronous evaluation
- **Objective:** تحمل قطع سرویس و درخواست‌های سنگین.
- **Expected:** ثبت Job پایدار، پاسخ سریع درخواست، Claim اتمیک، Lease/Fencing، Heartbeat، Retry محدود/Backoff، Backpressure و Commit اتمیک Result/Status.
- **Success:** پس از Crash/Restart، Job معتبر قابل بازیابی است و هیچ نتیجه‌ای دو بار نهایی نمی‌شود.
- **Error:** timeout، GPU OOM یا Worker قدیمی، داده را خراب یا نتیجه جدیدتر را Overwrite نمی‌کند.
- **Constraints:** PostgreSQL queue پیشنهادی `D-005` است، تأیید معماری/ظرفیت بعداً؛ retry/deadline numbers `OPEN` (`OD-10/12`).
- **Acceptance:** `AC-FR-07-A/B/C`.

### FR-08 — Secure status and report retrieval
- **Objective:** گزارش قابل‌دسترسی برای مالک/فرد مجاز و غیرقابل‌دسترسی برای سایرین.
- **Expected:** status/history/report در Auth Scope با Field Filtering مناسب و سازگاری وضعیت Job.
- **Success:** Owner مجاز گزارش خود را همراه domain, rubric/model/prompt versions دریافت می‌کند.
- **Error:** درخواست بدون Auth یا Cross-owner/Cross-unit ID حدس‌زده‌شده رد، بدون افشای وجود منبع.
- **Constraints:** visibility matrix و 403/404 privacy policy `OPEN` (`OD-07`).
- **Acceptance:** `AC-FR-08-A/B`.

### FR-09 — Expert feedback and audit trail
- **Objective:** امکان داوری انسانی و پیگیری منشأ تغییرات.
- **Expected:** بازخورد/تصحیح با actor, timestamp, criterion scope, justification, version و original AI output غیرقابل‌حذف/قابل‌تفکیک نگهداری و Audit ایجاد شود.
- **Success:** Reviewer مجاز نظر می‌دهد و سابقه تغییرات قابل ردیابی است.
- **Error:** فرد فاقد مجوز یا input مخرب بازخورد را ثبت نمی‌کند؛ raw text به Audit وارد نمی‌شود.
- **Constraints:** workflow و حقوق اصلاح/حذف بازخورد و retention `OPEN` (`OD-06/07/08/09`).
- **Acceptance:** `AC-FR-09-A/B`.

### FR-10 — Fully internal AI inference
- **Objective:** حفظ محرمانگی داده سازمانی در تمام مراحل inference.
- **Expected:** API/Worker تنها به Inference Server داخلی تأییدشده وصل شوند؛ مدل/Tokenizer Artifact محلی و No-Egress enforced و tested؛ بدون external tools/AI calls.
- **Success:** با Egress deny-by-default، یک ارزیابی Synthetic مجاز بدون خروج داده انجام می‌شود.
- **Error:** endpoint بیرونی، دانلود خودکار، telemetry حاوی متن یا نشت Prompt/Response در Log، Gate امنیتی را Fail می‌کند.
- **Constraints:** vLLM/Qwen صرفاً Candidate؛ مکان Data Center و Network Approval `OPEN` (`OD-13`).
- **Acceptance:** `AC-FR-10-A/B/C`.

### FR-11 — Long-document handling
- **Objective:** ارزیابی سند طولانی با حفظ انسجام بین بخش‌ها.
- **Expected:** chunk بر پایه ساختار، نگاشت معتبر به Original Text، ارزیابی cross-section و محدودیت context؛ partial failure کنترل‌شده.
- **Success:** تحلیل سند بلند شامل کیفیت انسجام کل سند و شواهد با offset اصل متن است.
- **Error:** truncation خاموش، offset نامعتبر و حذف بخش‌ها به نام نتیجه کامل پذیرفته نیست.
- **Constraints:** حد طول/تعداد بخش، tolerance کیفیت و SLA متن بلند `OPEN` (`OD-02/12/14`).
- **Acceptance:** `AC-FR-11-A/B`.

### FR-12 — Reproducibility and controlled change
- **Objective:** Audit، AI regression و تحلیل drift.
- **Expected:** persist immutable rubric snapshot/checksum, model/artifact revision/hash, prompt version, runtime, effective inference settings, processing/scoring version و زمان‌ها.
- **Success:** گزارش مشخصات اجرایی برای بررسی یا بازاجرای کنترل‌شده همان داده را نشان می‌دهد.
- **Error:** مدل/Prompt/Rubric ناشناخته یا version mismatch باعث خروجی بدون provenance معتبر نمی‌شود.
- **Constraints:** bitwise LLM determinism تضمین نشده؛ تفاوت rerun با stability metric سنجیده شود. retention و replay permissions `OPEN`.
- **Acceptance:** `AC-FR-12-A/B`.

## 5. Non-functional requirements (separate from FRs)

| ID | Requirement, expected validation | Numerical policy / owner | Related FR |
|---|---|---|---|
| NFR-01 | Confidentiality: no external inference/data egress, protected logs/metrics | Mandatory zero prohibited transmissions; Security Officer | FR-01/10 |
| NFR-02 | IAM: SSO/token validation, RBAC and resource ownership, deny-by-default | Role matrix OPEN; IAM + Security | FR-08/09 |
| NFR-03 | Data protection: at-rest/in-transit/backup encryption, key management | cipher/key/retention details OPEN; Security + Data Steward | FR-01/08 |
| NFR-04 | Availability/SLO and graceful degradation | uptime, error budget OPEN; Product Owner + SRE | FR-07/08 |
| NFR-05 | Performance: intake latency, job P50/P95, queue wait, throughput | thresholds OPEN; Product Owner + SRE | FR-07/11 |
| NFR-06 | Capacity: requests/day, peak concurrent users/jobs, tokens, GPU VRAM | numbers OPEN; Product Owner + Infrastructure | FR-07/11 |
| NFR-07 | Recovery: backup/restore, RPO/RTO and tested restore runbooks | numeric targets OPEN; SRE + Security | FR-07/08 |
| NFR-08 | AI quality in Persian: expert agreement, MAE, evidence relevance, stability, abstention | thresholds OPEN; Domain SMEs + AI Quality Lead | FR-02/04/05/06 |
| NFR-09 | Auditability: authorized actor, correlation IDs, version provenance, no raw text logs | retention and audit sink OPEN; Security + Compliance | FR-09/12 |
| NFR-10 | Scalability/reliability: backpressure, bounded retries, concurrency and no duplicate commit | limits OPEN; SRE + Architect | FR-07 |
| NFR-11 | Supply chain & isolation: vetted artifacts/licenses/checksums, offline startup, no external runtime dependency | approved process OPEN; Security + Infrastructure | FR-10 |
| NFR-12 | Data quality and linguistic robustness: Unicode Persian, ZWNJ, mixed scripts, reproducible offsets | supported languages/limits OPEN; SMEs + AI Quality | FR-01/04/11 |
| NFR-13 | Fairness: evaluate textual quality, not political alignment or speaker identity | evaluation protocol OPEN; SMEs + AI Quality | FR-02/04 |
| NFR-14 | Maintainability: adhere to architecture guide and CI/automated regression before release | review/gate policy OPEN; Technical Lead | all |

### Operational sizing questionnaire (no fabricated values)

| Item | Needed evidence | Approval owner | Decision |
|---|---|---|---|
| Daily requests and burst profile; growth horizon | 30/90-day forecast, peak distribution | Product Owner | OD-12 |
| Concurrent active users and concurrent GPU jobs | operational peak workload | Product Owner + SRE | OD-12 |
| Text lengths by domain; byte/token/file constraints | representative classified histogram | Domain SMEs + Product Owner | OD-02 |
| Synchronous acknowledgment and completion P95 | critical user journeys and business deadlines | Product Owner + SRE | OD-12 |
| GPU count, VRAM, utilization, capacity | inventory plus authorized benchmark | Infrastructure + AI Lead | OD-13 |
| SLA/SLO/error budget | service criticality and calendar | Product Owner + SRE | OD-12 |
| RPO/RTO, backup frequency, restore authority | business impact analysis | Business Owner + Security + SRE | OD-08/12 |
| Persian quality, MAE, stability, evidence accuracy | Golden Dataset validation | Domain SMEs + AI Lead | OD-14 |

## 6. Golden Dataset & expert adjudication plan — proposed

1. Data Steward legal/classification review; create authorized synthetic/de-identified sample pool **without putting confidential texts in Git**.
2. Stratify all three domains by quality bands, length, style, formality, difficulty, ambiguous applicability and controversial topics; sample counts `OPEN` (`OD-14`).
3. Develop a provisional annotation guide from versioned candidate Rubrics; expert feedback is used when available, and missing expert labels are recorded as a quality limitation. Formal rubric approval remains a Stage 12 acceptance condition; multiple independent domain experts must eventually rate criteria and mark `not_assessed`, evidence quote/span and reasons before accuracy can be claimed.
4. Measure inter-rater agreement, resolve differences with designated adjudicator, preserve dissent and label provenance without unnecessary identity disclosure.
5. Freeze calibration/development data and isolated untouched holdout, with leakage checks and versioned hashes. No repeated prompt tuning on holdout.
6. Benchmark per domain and criterion: MAE, expert agreement, evidence validity/relevance, Stability across repeated runs, abstention correctness, coverage, unsupported claims, schema validity, latency P50/P95 and throughput.
7. Thresholds, sample-size adequacy, split protocol, adjudicator and sign-off owners require approval; real model/GPU tests are **PENDING_SERVER** and belong to Stage 03/11.

## 7. Traceability, risks and decisions

- Detailed AC IDs: [03_acceptance_criteria.md](03_acceptance_criteria.md); rubric candidates: [02_evaluation_rubrics.md](02_evaluation_rubrics.md); security: [04_security_and_data_policy.md](04_security_and_data_policy.md); decisions/tracker: [05_open_decisions.md](05_open_decisions.md).
- Initial cross-stage mapping: FR-01 → Stage 02/10; FR-02 → 06/08; FR-03 → 05/06; FR-04 → 03/07/08; FR-05 → 06/08; FR-06 → 06/08/10; FR-07 → 05/09; FR-08 → 04/05/10; FR-09 → 05/10; FR-10 → 03/04/07; FR-11 → 03/08/09; FR-12 → 05/06/07/08/12; all → Stage 11 verification.
- Tracked risks from baseline: R-01..R-12. Highest current documentation risks: R-01 (AI quality), R-03 (egress), R-07 (IDOR), R-08 (unsupported novelty), R-11 (dataset permission); mitigations require actual Stage 03–11 evidence.
- **Gate:** Stage 01's internal **documentation/traceability review is complete (DONE)**: input-domain matrix, candidate rubrics, synthetic report JSON and reference-evidence boundaries have been added and verified; see the current [Decision Log](05_open_decisions.md) and [Acceptance Matrix](03_acceptance_criteria.md). This is **not** business approval, AI quality validation or operational security proof. Formal Product Owner/domain SME/Security acceptance is deferred to Stage 12 (`D-015`). Stage 02 may begin **only on the user's explicit request**, with unresolved design/organization specifics remaining OPEN and no unauthorized protected-data operations.
