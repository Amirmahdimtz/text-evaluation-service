# Acceptance Criteria and Verification Matrix — Stage 01

> **Status: DRAFT_FOR_INTERNAL_VERIFICATION** · 2026-10-21. These are **test specifications**, not executed product tests. Numeric performance/AI quality thresholds remain OPEN. Under `D-015`, formal employer/SME acceptance is sought at Stage 12 only. Baseline: Implementation Plan §§1.3,4,6,7,10/Stage 01,11,13, amended by [Decision Log](05_open_decisions.md).

## 1. Acceptance contract

Each criterion uses stable ID `AC-FR-NN-X` or `AC-NFR-NN`, scenario/fixture, observable outcome, proposed implementation/verification stages and accountable **approval role**. No organizational individual is assigned. `DRAFT` means specified but not approved; execution state of all future software/model/server tests is `NOT_RUN` or `PENDING_SERVER`, never PASSED. Tests in this Stage validate Markdown/document coverage only.

**Definition of stage verification vs final acceptance:** Internal technical review, executed tests, security controls and recorded decisions determine each engineering stage's gate. Employer/SME **formal sign-off is not a prerequisite for Stage 01–11 completion**; consolidated external acceptance occurs at Stage 12 (`D-015`). Unresolved business limits remain OPEN, and candidate Rubrics must never be presented as officially approved. Release claims require Stage 11+12 real evidence. Authorization for real confidential data, destructive changes and Production operations remains mandatory before those particular actions.

### FR-01..FR-12 verification

| Acceptance ID | Verification scenario / synthetic input | Expected result / test oracle | Stage(s) | Approval owner | State |
|---|---|---|---|---|---|
| `AC-FR-01-A` | متن معتبر با evaluation_type مجاز و identity سازمانی معتبر | درخواست پذیرفته و evaluation/job قابل پیگیری ایجاد شود؛ scope از Auth نه متن تعیین شود | 10 | Product Owner / IAM | DRAFT / NOT_RUN |
| `AC-FR-01-B` | text تهی، type نامعتبر، metadata نامجاز، طول بیش از حد مصوب | خطای کنترل‌شده بدون ایجاد Job/نشت متن؛ boundary cases در DTO تست شوند | 10 | Product Owner | DRAFT / NOT_RUN |
| `AC-FR-01-C` | ارسال تکراری key در scope یکسان و آزمایش cross-scope | رفتار idempotent طبق policy مصوب؛ Cross-scope هرگز merge نمی‌شود | 10 | Product Owner / Security | DRAFT / NOT_RUN |
| `AC-FR-02-A` | برای هر speech/media/research درخواست ساخته شود | Criterion set فقط با Rubric مربوط تطبیق کند؛ هیچ criterion حوزه دیگر حضور ندارد | 06,08 | Domain SMEs | DRAFT / NOT_RUN |
| `AC-FR-02-B` | Rubric Published حوزه وجود ندارد یا mismatch دارد | ارزیابی نامعتبر شروع نشود؛ خطای امن و قابل ردیابی ایجاد شود | 06,08 | Product Owner | DRAFT / NOT_RUN |
| `AC-FR-03-A` | Evaluation قدیمی پس از Publish نسخه تازه مشاهده شود | Checksum/criteria/weights/anchors نسخه قدیمی ثابت و قابل بازیابی بماند | 05,06 | SMEs / Architect | DRAFT / NOT_RUN |
| `AC-FR-03-B` | تلاش برای ویرایش Published Rubric یا duplicate version | رد تغییر، Audit و عدم تغییر ارزیابی‌های سابق | 06 | SMEs / Security | DRAFT / NOT_RUN |
| `AC-FR-04-A` | متن Synthetic با evidence شناخته‌شده و rubric معتبر | در assessed همه فیلدها، score 0..5، quote و offset معتبر و استدلال مرتبط باشند | 08 | AI Quality Lead | DRAFT / NOT_RUN |
| `AC-FR-04-B` | schema خطا، quote جعلی، offset خارج محدوده، ادعای بی‌پشتوانه | Validator رد/abstain یا retry محدود می‌کند؛ نتیجه ساختگی ذخیره نمی‌شود | 07,08 | AI Quality / Security | DRAFT / NOT_RUN |
| `AC-FR-05-A` | Score/weightهای معتبر با Rubric snapshot ثابت | Python final_score و coverage عیناً با محاسبه مستقل برابر شوند؛ تکرار پایدار | 08 | Technical Lead | DRAFT / NOT_RUN |
| `AC-FR-05-B` | یک معیار غیرقابل ارزیابی همراه معیارهای assessed | نمره آن معیار null، نه 0؛ coverage مستقل و درست باشد | 08 | SMEs / AI Quality | DRAFT / NOT_RUN |
| `AC-FR-05-C` | وزن صفر/منفی، score خارج از دامنه، denominator صفر/empty set | بدون خروجی numeric معتبر، خطای کنترل‌شده و تست شده | 06,08 | Technical Lead | DRAFT / NOT_RUN |
| `AC-FR-06-A` | research novelty بدون Corpus معتبر و مقایسه مصوب | not_assessed با reason، score null، needs_human_review طبق سیاست محافظه‌کارانه | 08 | Research SME | DRAFT / NOT_RUN |
| `AC-FR-06-B` | required unassessed یا coverage کمتر از threshold مصوب | عدم گزارش completed/full score؛ partial/review طبق policy مصوب | 08,10 | SMEs / Product Owner | DRAFT / NOT_RUN |
| `AC-FR-07-A` | ارسال Job و توقف/راه‌اندازی مجدد Worker | HTTP منتظر inference نمی‌ماند؛ Job پایدار دوباره بازیابی می‌شود | 09 | SRE | DRAFT / NOT_RUN |
| `AC-FR-07-B` | دو Worker مدعی Job، lease expiry و late completion | حداکثر یک Commit معتبر؛ Worker منقضی‌شده overwrite نمی‌کند | 05,09 | Technical Lead / SRE | DRAFT / NOT_RUN |
| `AC-FR-07-C` | timeout/GPU OOM/queue saturation و exhausted retries | retry محدود؛ terminal state و HTTP backpressure مطابق policy؛ no lost jobs | 09,11 | SRE | DRAFT / NOT_RUN |
| `AC-FR-08-A` | Owner/Reviewer مجاز گزارش معتبر را می‌خواند | status/score/coverage/versions با scope و field permissions درست بازگردد | 10 | Product Owner / IAM | DRAFT / NOT_RUN |
| `AC-FR-08-B` | کاربر ناشناس و مالک دیگر/واحد دیگر با UUID شناخته‌شده | عدم دسترسی، بدون افشای متن یا وجود منبع در error | 04,10 | Security | DRAFT / NOT_RUN |
| `AC-FR-09-A` | Reviewer مجاز بازخورد به یک criterion ثبت کند | Actor، زمان، علت، نسخه/تغییر و AI baseline بدون جایگزینی تاریخچه ثبت شوند | 10 | Review Lead | DRAFT / NOT_RUN |
| `AC-FR-09-B` | Reviewer بدون حق و payload دارای متن حساس برای audit | رد دسترسی و sanitization log/audit؛ audit فاقد raw text | 04,10 | Security | DRAFT / NOT_RUN |
| `AC-FR-10-A` | ارزیابی Synthetic با egress deny-by-default و DNS/TCP tracing | فقط endpoint داخلی مجاز؛ هیچ خروجی به AI Provider/telemetry بیرونی | 04,07 | Security / Infrastructure | DRAFT / NOT_RUN |
| `AC-FR-10-B` | Startup مدل با اینترنت مسدود و registry داخلی | بدون دانلود خارجی مدل/Tokenizer؛ hash/version قابل تأیید | 03,04,07 | Infrastructure / AI Lead | DRAFT / NOT_RUN |
| `AC-FR-10-C` | خطا و timeout مدل با Prompt آزمایشی حساس‌نما | Prompt، Response، header Secret در app/model/gateway logs دیده نشوند | 04,07,11 | Security | DRAFT / NOT_RUN |
| `AC-FR-11-A` | متن بلند Synthetic دارای ارجاع cross-section | chunking بدون گم‌شدن بخش/نتیجه کل سند؛ offsets original صحیح | 03,08 | AI Quality / Research SME | DRAFT / NOT_RUN |
| `AC-FR-11-B` | متن > Context و خطای chunk در میانه پردازش | عدم truncation خاموش؛ partial/failure طبق policy و بدون گزارش کامل‌نما | 08,09 | Technical Lead | DRAFT / NOT_RUN |
| `AC-FR-12-A` | ثبت/بازیابی Result یک Job | Rubric snapshot/checksum, model hash/revision, prompt, runtime, scoring, settings ذخیره شده | 05,08 | AI Lead / Architect | DRAFT / NOT_RUN |
| `AC-FR-12-B` | تغییر model/prompt/rubric و بازاجرای dataset کنترل‌شده | تغییر قابل تشخیص، test regression و مقایسه version-bound، بدون overwrite history | 08,11,12 | AI Quality Lead | DRAFT / NOT_RUN |

## 2. NFR acceptance matrix

| Acceptance ID | Evidence / method | Observable gate or missing threshold | Test stage(s) | Approval owner | State |
|---|---|---|---|---|---|
| `AC-NFR-01` | egress deny-by-default + packet/DNS tests + grep log | هیچ انتقال متن/Prompt به مقصد غیرمجاز؛ عدد عملکردی لازم ندارد | 04,07,11 | Security | DRAFT / NOT_RUN |
| `AC-NFR-02` | IAM/token validation, IDOR matrix across endpoints/data queries | هر دسترسی خارج scope رد؛ Role Matrix نیازمند approval | 04,10,11 | IAM / Security | DRAFT / NOT_RUN |
| `AC-NFR-03` | verify TLS endpoints, encrypted DB/media/backup and key procedures | طبق cryptographic policy سازمان؛ standard OPEN | 04,11 | Security | DRAFT / NOT_RUN |
| `AC-NFR-04` | measure SLO window, error budget, graceful failure | threshold OPEN (OD-12) | 09,11 | SRE / Product Owner | DRAFT / NOT_RUN |
| `AC-NFR-05` | P50/P95 request acknowledgment, job completion, queue wait under representative load | threshold OPEN (OD-12) | 03,09,11 | SRE | DRAFT / NOT_RUN |
| `AC-NFR-06` | requests/day, peak user/job concurrency, VRAM and headroom | threshold OPEN (OD-02/12/13) | 03,09,11 | Infrastructure | DRAFT / NOT_RUN |
| `AC-NFR-07` | encrypted backup, isolated restore drill, observed RPO/RTO | RPO/RTO targets OPEN (OD-08/12) | 04,11,12 | SRE / Security | DRAFT / NOT_RUN |
| `AC-NFR-08` | holdout MAE per criterion, evidence accuracy, stability, coverage, supported claims | threshold and sample size OPEN (OD-14) | 03,11 | AI Lead / SMEs | DRAFT / NOT_RUN |
| `AC-NFR-09` | event schema and log leakage/retention reviews | minimum audit fields; retention OPEN (OD-08) | 04,11 | Security / Compliance | DRAFT / NOT_RUN |
| `AC-NFR-10` | race, crash, recovery and duplicate commit tests | zero invalid duplicate commits; retry limits OPEN | 09,11 | SRE / Architect | DRAFT / NOT_RUN |
| `AC-NFR-11` | artifact license, checksum, SBOM/dependency scan, offline runtime | approved artifact process OPEN (OD-13) | 03,04,11 | Security / AI Lead | DRAFT / NOT_RUN |
| `AC-NFR-12` | ZWNJ/Persian normalization/mixed language original span mapping tests | language support/offset convention OPEN (OD-01/11) | 08,11 | Technical Lead | DRAFT / NOT_RUN |
| `AC-NFR-13` | balanced test texts differing only in political position | acceptance review threshold OPEN (OD-14) | 03,11 | SMEs / AI Lead | DRAFT / NOT_RUN |
| `AC-NFR-14` | DI/discovery import, test suite, no unnecessary layers; docs review | conforms to Architecture Guide; CI workflow decided Stage 02 | 02,11 | Technical Lead | DRAFT / NOT_RUN |

## 3. Metrics and measurement protocol (proposed)

| Metric | Definition / denominator | Report granularity | Approval dependency |
|---|---|---|---|
| MAE | `mean(abs(model_score - adjudicated_expert_score))` over **assessed aligned cases**; additionally report abstention cases separately to prevent biased selection | per domain/criterion, holdout and sample n | OD-14: allowed MAE, n, confidence intervals |
| Evidence Match Rate | exact original quote/span agreement / evidence spans returned | per domain/criterion; zero spans reported distinctly | OD-11 offset unit and parser |
| Evidence Accuracy | independently expert-judged *text-present AND relevant to asserted claim* spans / all proposed evidence spans; invalid/unverifiable count as failures, not dropped | domain/criterion with confidence interval | OD-14 expert protocol, threshold |
| Stability | per-item score agreement or `mean(abs(score_run_a-score_run_b))` across fixed-version repeated runs; publish run count, seed/settings and variance | domain, criterion, length | OD-14 limits and repetitions |
| Coverage | `sum(weights of assessed applicable criteria)/sum(weights of all applicable criteria)`; report missing required and eligibility independently | per evaluation and group distribution | OD-04 denominator and minimum |
| Correct Abstention | TP/FP/FN against expert-defined insufficient-evidence label; report rates to avoid gaming coverage | per criterion and domain | OD-14 labeling and targets |
| Unsupported Claim Rate | unsupported factual assertions in conclusions / checked factual assertions; state `undefined` if none | per domain/claim class | OD-14 and reference corpus |
| Schema Validity | valid structured outputs after independent backend validation / attempted outputs; also retries and terminal failures | per version/runtime | OD-14 threshold |
| Throughput / Queue | completed valid jobs per time, queue depth/wait, P50/P95, concurrency and VRAM with fixed workload | length/type and load profile | OD-12/13 thresholds |
| Expert agreement | inter-rater Weighted Kappa/Spearman as appropriate, plus disagreements and adjudication | domain/criterion; label provenance | OD-14 expert plan |

When the denominator is zero, show metric as `undefined` with sample size; never present fabricated 100%. Specify handling of not_assessed and incomplete jobs in published quality reports. Repeated tuning on independent holdout is prohibited.

## 4. Golden Dataset acceptance plan

1. Approval of authorized Synthetic/de-identified corpus acquisition and classification by Data Steward/Security; no real confidential data leaves internal secure boundary (`OD-08/14`).
2. Domain SMEs define diversity strata: speech prepared vs STT transcript, media format/channel, research discipline/methodology, length, quality bands, uncertainty, contradictory and sensitive-topic cases.
3. Multiple independent SME raters score all rubric criteria with evidence; adjudication protocol preserves disagreement; calibration vs frozen independent holdout, no leakage.
4. Record dataset lineage/license, rubric/model/prompt revisions and split hashes in authorized storage; never store raw confidential samples in public Git.
5. Define and version **provisional** sample sizes, inter-rater reliability protocol and MAE/Evidence Accuracy/Stability/Coverage/Abstention/Hallucination targets for Stage 03/11 diagnostic work. Record unknown/unverifiable targets as OPEN; no unsupported quality PASS is allowed. Formal employer/SME approval of the final acceptance thresholds is deferred to **Stage 12** (`D-015`).
6. Perform actual internal GPU/inference/benchmark tests at Stage 03/11; current status: `PENDING_SERVER`, not PASSED.

## 5. Synthetic full business-report JSON contract example (PROPOSED, not an executed model result)

This is a **synthetic schema example** to trace FR-01/02/04/05/06/08/12 and `OD-15`. It was assembled for document verification, **not** generated by any LLM, not signed off, and not a frozen production DTO/API. The `source_text` is artificial and may appear only in this non-confidential documentation example. A real secure API would return the original text **only when the requesting identity has explicit field permission**; this example must not be interpreted as default data exposure.

**Candidate arithmetic:** assessed criteria have weights `25+20+20+15=80`, weight-adjusted points `25×4/5+20×3/5+20×4/5+15×3/5=57`, hence `final_score=100×57/80=71.25`, `coverage=80/100=0.80`. The two remaining criteria have `score=null`, never zero. For this example **only**, all six criteria are declared applicable; `OD-04` must determine the official applicability/denominator/release policy. No coverage threshold is fabricated. `partial` and `needs_human_review` are conservative **candidate** outputs, not approved status names.

**Offset illustration:** For this example's Persian BMP characters, offsets are zero-based, half-open Unicode code-point indices and happen to equal JavaScript string indices. The authoritative UTF-8-byte vs code-point policy and normalization behavior remain **`OD-11 OPEN`**. All quoted spans below must exactly match the provided `source_text`; avoid any implicit normalized-text offsets.

```json
{
  "schema_version": "synthetic-business-report-candidate-0.1",
  "report_kind": "SYNTHETIC_EXAMPLE_ONLY",
  "evaluation_id": "EXAMPLE_ONLY_NOT_REAL_ID",
  "evaluation_type": "speech",
  "source_text": "سلام دوستان. امروز درباره مدیریت زمان صحبت می‌کنیم. ابتدا اولویت‌ها را تعیین می‌کنیم. سپس کارهای مهم را برنامه‌ریزی می‌کنیم. در پایان، هر روز پیشرفت را مرور می‌کنیم.",
  "processing_status": "partial",
  "needs_human_review": true,
  "publishable_as_official_score": false,
  "final_score_0_100": 71.25,
  "coverage_fraction": 0.8,
  "coverage_weight_assessed": 80,
  "coverage_weight_candidate_total": 100,
  "coverage_denominator_assumption": "ALL_SIX_CANDIDATE_CRITERIA_APPLICABLE_EXAMPLE_ONLY",
  "rubric": {
    "code": "speech",
    "version": "candidate-0.1",
    "status": "candidate_not_published"
  },
  "provenance": {
    "model_revision": null,
    "prompt_version": null,
    "scoring_formula_version": "illustrative-stage-01",
    "model_executed": false
  },
  "criteria": [
    {
      "criterion_code": "speech_coherence",
      "applicability": "applicable",
      "status": "assessed",
      "score": 4,
      "max_score": 5,
      "reason": "توالی بخش‌ها روشن است اما پیوند استدلالی کامل نیست.",
      "strengths": [
        "توالی منطقی ارائه شده است."
      ],
      "weaknesses": [
        "چرایی این توالی توضیح داده نشده است."
      ],
      "evidence": [
        {
          "source_kind": "original_submission",
          "quote": "ابتدا اولویت‌ها را تعیین می‌کنیم.",
          "start_offset": 52,
          "end_offset": 85
        },
        {
          "source_kind": "original_submission",
          "quote": "در پایان، هر روز پیشرفت را مرور می‌کنیم.",
          "start_offset": 125,
          "end_offset": 165
        }
      ],
      "recommendations": [
        "یک جمله گذارِ استدلالی اضافه شود."
      ]
    },
    {
      "criterion_code": "speech_structure",
      "applicability": "applicable",
      "status": "assessed",
      "score": 3,
      "max_score": 5,
      "reason": "آغاز، بدنه و پایان دیده می‌شود، اما تفکیک بخش‌ها کم‌جزئیات است.",
      "strengths": [
        "آغاز و پایان مشخص است."
      ],
      "weaknesses": [
        "بخش میانی مختصر است."
      ],
      "evidence": [
        {
          "source_kind": "original_submission",
          "quote": "سلام دوستان.",
          "start_offset": 0,
          "end_offset": 12
        },
        {
          "source_kind": "original_submission",
          "quote": "در پایان، هر روز پیشرفت را مرور می‌کنیم.",
          "start_offset": 125,
          "end_offset": 165
        }
      ],
      "recommendations": [
        "تیترها یا نشانه‌های بخش‌بندی دقیق‌تر اضافه شود."
      ]
    },
    {
      "criterion_code": "speech_clarity",
      "applicability": "applicable",
      "status": "assessed",
      "score": 4,
      "max_score": 5,
      "reason": "موضوع اصلی و هدف روشن بیان شده‌اند.",
      "strengths": [
        "موضوع از ابتدا روشن است."
      ],
      "weaknesses": [
        "معیار زمانی جزئی ندارد."
      ],
      "evidence": [
        {
          "source_kind": "original_submission",
          "quote": "امروز درباره مدیریت زمان صحبت می‌کنیم.",
          "start_offset": 13,
          "end_offset": 51
        }
      ],
      "recommendations": [
        "برای مخاطب موردنظر یک مثال کوتاه آورده شود."
      ]
    },
    {
      "criterion_code": "speech_writing",
      "applicability": "applicable",
      "status": "assessed",
      "score": 3,
      "max_score": 5,
      "reason": "زبان قابل فهم است ولی تنوع بیان محدود است.",
      "strengths": [
        "زبان مستقیم و محترمانه است."
      ],
      "weaknesses": [
        "تنوع شروع جمله‌ها کم است."
      ],
      "evidence": [
        {
          "source_kind": "original_submission",
          "quote": "سلام دوستان.",
          "start_offset": 0,
          "end_offset": 12
        }
      ],
      "recommendations": [
        "ساختار جمله‌ها تنوع بیشتری پیدا کند."
      ]
    },
    {
      "criterion_code": "speech_reasoning",
      "applicability": "applicable",
      "status": "not_assessed",
      "score": null,
      "max_score": 5,
      "not_assessed_reason": "INSUFFICIENT_TEXT",
      "reason": "شواهد یا زمینه کافی برای نمره قابل دفاع وجود ندارد.",
      "strengths": [],
      "weaknesses": [],
      "evidence": [],
      "recommendations": [
        "برای ارزیابی معتبر، زمینه یا متن تکمیلی مجاز فراهم شود."
      ]
    },
    {
      "criterion_code": "speech_audience_fit",
      "applicability": "applicable",
      "status": "not_assessed",
      "score": null,
      "max_score": 5,
      "not_assessed_reason": "MISSING_CONTEXT",
      "reason": "شواهد یا زمینه کافی برای نمره قابل دفاع وجود ندارد.",
      "strengths": [],
      "weaknesses": [],
      "evidence": [],
      "recommendations": [
        "برای ارزیابی معتبر، زمینه یا متن تکمیلی مجاز فراهم شود."
      ]
    }
  ]
}
```

**Not yet agreed (`OD-04/07/11/15`):** official response-field visibility, report status enum, final score precision, denominator applicability, reason-code taxonomy, quote/offset unit, authentication and field-level redaction. This provisional example cannot be used as official acceptance evidence or a published business score.

## 5. Stage 01 documentation gates

| Gate | Check | Current approval state |
|---|---|---|
| S1-G01 | All FR-01..FR-12 explicitly defined, success/error/constraints and AC cross-referenced | **PASS** — 12/12 FR and 28 unique FR acceptance cases verified in GitHub, 2026-10-21 |
| S1-G02 | Three independent rubric catalogs with 0..5 anchors, proposed weights and epistemic limits | PASS — structural/candidate-only; no SME sign-off |
| S1-G03 | No external inference, security classification and explicit IAM/data governance requirements | PASS — documented controls only, not operationally tested |
| S1-G04 | Traceable FR/NFR → AC → responsible role → future stage | **PASS** — 12 FR and 14 NFR linked to acceptance scenarios; changes remain subject to repeat verification |
| S1-G05 | All uncertain numerical values/policies recorded OPEN, no proposed rule marked CONFIRMED | PASS — decision status review; `D-015` is only a confirmed process change |
| S1-G06 | Internal completeness review: business report/JSON sample, per-domain input validation matrix, rubric anchoring/calibration and evidence-source clarity | **PASS** — synthetic JSON schema parsed, 6/6 criterion items, score 71.25 and coverage 0.80 independently verified; exact quote spans, domain inputs, calibration and provenance documented |

**Stage 01 internal gate verdict: `DONE` / cleared for Stage 02 entry, not Stage 02 started.** Verified on GitHub-stored documents on 2026-10-21: **25/25 focused structural, traceability, rubric, math, JSON, original-span, policy, link/Markdown and secret-pattern checks PASS**; only documentation checks were exercised. Employer/SME approval remains **DEFERRED_TO_STAGE_12** (`D-015`/`OD-16`). These documents do **not** prove product correctness or real AI quality: HTTP/API/DB/migration tests are `NOT_RUN` because no application exists; internal GPU/no-egress/load/recovery/AI benchmark tests are `PENDING_SERVER`. Remaining scope/parameter decisions are explicitly OPEN and subject to later verified implementation/acceptance. Stage 02 requires the user's explicit start request. Refer to [product requirements](01_product_requirements.md), [rubrics](02_evaluation_rubrics.md), [security](04_security_and_data_policy.md), [decisions](05_open_decisions.md).
