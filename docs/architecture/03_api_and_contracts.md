# Stage 02 — API v1 and Data Contracts

> Contract status: PROPOSED_CONTRACT only | Date: 2026-10-21 | No endpoints/classes currently exist on main.
>
> Route base طبق Architecture Guide: /api/v1/text_evaluation در صورت api.prefix برابر /api/v1. ثبت مسیرها در TextEvaluationController.api() با APIRouter(prefix="") انجام می‌شود. API v1 stable نام‌گذاری *پیشنهادی* است؛ انتشار OpenAPI و اثبات اتصال در Stage 10.

## 1. Cross-cutting HTTP contract

- Content-Type: application/json؛ UTF-8. JSON object تنها شکل درخواست پیشنهادی Stage 02 است؛ Upload/PDF/DOCX/OCR/STT در Scope مصوب نیست (OD-01/05).
- AuthN: identity معتبر از Gateway/IdP داخلی مورد تأیید سازمان؛ اعتبارسنجی server-side issuer, audience, signature, expiry, revocation طبق OD-07. نبود Auth => 401. Auth Context شامل user_id و authorized org/unit scopes و permissions که از داده احرازشده استخراج می‌شوند؛ هیچ owner_id, org_id, role در body قابل اعتماد نیست.
- AuthZ: default deny؛ روی هر resource read/create/feedback/rubric query و حتی وجودشناسی/lookup idempotency اجرا شود. سیاست hiding با 404 در برابر 403 در OD-07 OPEN است؛ برای resource خارج از scope، پاسخ privacy-preserving 404 یک PROPOSAL است.
- Request/response schema_version در response و versioned OpenAPI ضروری است. Breaking changes نیازمند new major URL یا version contract مجزا، nonbreaking optional fields در v1، عدم تغییر معنی/status fieldهای موجود.
- No prompt/input echo در errors، logs یا trace. متن کامل فقط در authorized endpoints و فقط در صورت اجازه field-level (OD-07/08)، نه به صورت default report.
- Request size/byte/token, language support, metadata allowlist, quotas, max page size, throttling, retention, timeouts و SLO: OPEN (OD-01/02/07/08/10/12). Safe fail-closed/configuration gate؛ هیچ عدد ساختگی برای Production ثبت نشده است.
- IDs به صورت UUID پیشنهادی‌اند؛ schema UUID/DB PK نهایی Stage 05. Time fields ISO 8601 UTC با timezone؛ ترتیب و consistency در DB تثبیت خواهد شد.
- Public clients فقط versioned API responses مصرف کنند؛ SQLAlchemy Model یا internal prompt/raw provider payload به HTTP بازگردانده نشود.

## 2. Proposed endpoints and DTO inventory

Status همه ردیف‌ها PROPOSED_CONTRACT است. DTOها در src/application/text_evaluation/dtos/text_evaluation_dto.py قرار می‌گیرند (یا تقسیم حداقلی فقط در صورت پیچیدگی واقعی).

| Method / path below base | Proposed Request DTO (R required / O optional) | Proposed Response DTO; status | AuthZ / idempotency / pagination |
|---|---|---|---|
| POST /evaluations | CreateEvaluationDto: R text:string nonempty; R evaluation_type enum speech/media/research; O rubric_version:string; O context:allowlisted object. R Idempotency-Key header (candidate) | EvaluationAcceptedDto: evaluation_id, job_id, processing_status, rubric code/version, schema_version, status_url; 202 | scope permission evaluate:create; key unique inside org+principal+operation; same fingerprint returns same IDs, mismatch 409; no pagination |
| GET /jobs/{job_id} | JobStatusQueryDto: R UUID path | EvaluationJobStatusDto: job_id, evaluation_id, status, safe_error_code?, retryable?, submitted_at, updated_at, completed_at?; 200 | evaluate:read with owner/unit scope; 404 invisible; no pagination |
| GET /evaluations/{evaluation_id} | EvaluationIdQueryDto: R UUID path | EvaluationReportDto: domain, rubric metadata, processing_status, result_status?, final_score?, coverage?, needs_human_review, criteria, provenance, times; 200 when accessible, including pending representation | evaluate:read scoped; no pagination for one result; default excludes source_text |
| GET /evaluations/{evaluation_id}/criteria | CriterionResultsQueryDto: R UUID path; O cursor:string and limit:positive int (limits OPEN) | CriterionPageDto: criteria[], next_cursor?, schema_version; 200 | evaluate:read scoped; cursor opaque/scoped and stable sort (criterion ordering fixed by snapshot); pagination only if criteria collection requires it |
| GET /rubrics | RubricListQueryDto: O evaluation_type enum; O cursor/limit | RubricPageDto: published authorized rubric summaries, next_cursor?; 200 | rubric:read permission scoped; no unapproved Draft visibility; cursor for genuine collections |
| GET /rubrics/{rubric_version_id} | RubricVersionQueryDto: R UUID path | RubricVersionResponseDto: code, version, checksum, published_at, allowed criteria/anchors and coverage policy; 200 | rubric:read and scope; only authorized immutable Published snapshots; 404 otherwise |
| POST /evaluations/{evaluation_id}/feedback | CreateFeedbackDto: R decision:string from approved enum (OPEN); R reason:string nonempty; O criterion_code:string; O correction object (schema OPEN); O expected_result_revision; R evaluation_id UUID path | FeedbackResponseDto: feedback_id, evaluation_id, feedback_revision, recorded_at; 201 | reviewer:feedback only within explicit assignment; append-only and audit; duplicate feedback idempotency scope OD-10; 409 stale version |
| GET /evaluations/{evaluation_id}/feedback | FeedbackPageQueryDto: R UUID path; O cursor/limit | FeedbackPageDto: authorized redacted feedback[], next_cursor?; 200 | proposed only if OD-06 approves feedback history/read; not assumed in Stage 10 baseline |

**Scope boundary:** The four baseline endpoints from Implementation Plan are POST /evaluations, GET /evaluations/{id}, GET /rubrics and POST /evaluations/{id}/feedback; additional job/criteria/version paths above are explicit Stage 02 proposals to satisfy FR-04/07/08. They must be rechecked against OD-05/06/07 before implementation. Admin publish/retire, export, cancel, delete, re-evaluate are NOT approved and have NO invented route.

## 3. Data shapes and validation rules

### CreateEvaluationDto

- Required text: original, nonempty Unicode string. Reject invalid JSON/encoding/control policy; no silent trimming, normalization overwrite, truncation or external URI fetch. Limits are configured from approved policy later (OD-02), not hardcoded here.
- Required evaluation_type: strict enum of speech, media, research; reject case/unknown type rather than silently reroute.
- Optional rubric_version: published, authorized, matching evaluation_type; when omitted resolve authorized latest published deterministically and persist specific snapshot/checksum. No actual published rubric exists yet; candidate-0.1 is NOT official.
- Optional context: only explicit approved type-specific keys (purpose, target_audience, transcript flags, media channel, research discipline and authorized corpus ID are PROPOSED, not a fixed allowlist). Reject unknown or untrusted foreign refs, identities, executable instructions as policy.
- Idempotency-Key: client-generated opaque token in request header; exact length/charset/window OPEN OD-10. Server scopes by authorized principal + org + route; protects simultaneous create via unique constraints; key reuse with different canonical payload => 409, same payload => replay same IDs (202). Do not store raw text as a dedup key or in error logs.

### EvaluationAcceptedDto / JobStatusDto

- Required evaluation_id, job_id, processing_status, schema_version; rubric pinned version fields required once evaluation is created.
- Candidate `processing_status` (Job lifecycle) values: `pending`, `processing`, `completed`, `failed_retryable`, `failed_terminal`. These describe transport/execution only; a job can complete successfully even if evaluation evidence is insufficient.
- Candidate `result_status` (evaluation outcome) values: `assessed`, `partial`, `not_assessed`. It is absent/null while no result exists and is present after a completed evaluation. `needs_human_review` is an independent boolean; it does NOT replace either status. A completed job with no assessed criteria has `processing_status=completed`, `result_status=not_assessed`, `needs_human_review=true` under this synthetic conservative fixture. Exact official result taxonomy and review policy remain OD-04/09/15 OPEN.
- Optional safe_error_code; never include raw prompt, model exception or stack trace. 404 for unauthorized/missing resource. 503 if dependency unavailable according to fail-closed policy. No positive promise of completion time before benchmarks.

### EvaluationReportDto / CriterionResultDto

- Required evaluation_id, evaluation_type, processing_status, rubric code/version/checksum and schema_version; result_status and needs_human_review are required only once a result is available (null/omitted while pending); optional final_score_0_100, coverage_fraction, criteria[], provenance, completed_at.
- Criterion requires criterion_code from pinned rubric, applicability (applicable/not_applicable/undetermined), status assessed/not_assessed, score integer 0..5 ONLY if assessed, otherwise null, max_score=5 only under candidate scoring policy D-008, reason/reason_code, strengths, weaknesses, recommendations and evidence[].
- Validation: assessed => exact valid numerical score + accepted evidence/anchor-based rationale; not_assessed => score null and reason_code required. Required criterion unassessed triggers policy-based review. No evaluated criteria => final score null (do not divide by zero).
- coverage_fraction = assessed applicable weight / all applicable weight, in [0,1] if denominator defined; final_score_0_100 calculated in Python from pinned rubric, not model. Decimal precision/rounding/applicability/threshold policy OD-04 OPEN; report carries policy version, no fabricated threshold.
- Report must not expose original text by default; criterion quotes are intrinsically confidential and only returned to explicitly authorized reader (OD-07/08). Read scope includes any linked evidence source and corpus permission.

### RubricVersionResponseDto and Feedback

- Rubric version includes immutable criteria snapshot, weight, anchors, applicability, evidence requirements, checksum and published_at. No in-place edit after publish; source candidate-0.1 is not Published.
- Explicit environment separation: Stage 03 benchmarks may use version-pinned `candidate-0.1` ONLY as an internal benchmark fixture with synthetic/authorized data; internal Stage 06–11 software tests may load it only in an isolated non-production test scope. Public/production `/rubrics` discovery, default rubric resolution and official scoring require a separately authorized Published snapshot and must fail closed if none exists. An internal candidate does not become Published by being used in benchmarks. Exact publication approvals/workflow remain OD-03/06/07/15 OPEN.
- Feedback is an append-only record of reviewer identity from Auth Context, action/decision, reason, optional criterion and versioned correction. Original AI result must remain intact for audit. Approval-required decision enum, reviewer workflow and correction model OD-06/09/15 OPEN.
- Pagination, if applicable: stable order + opaque cursor scoped to principal/filter/org; verify cursor tampering and no cross-scope skip. page limit upper bound is not assumed; malformed cursor => 400.

## 4. Structured result & evidence provenance contract

**Synthetic illustration only (not generated by an LLM, not an existing API response):**

    {
      "schema_version": "candidate-api-v1.0",
      "evaluation_id": "00000000-0000-4000-8000-000000000001",
      "job_id": "00000000-0000-4000-8000-000000000002",
      "evaluation_type": "speech",
      "processing_status": "completed",
      "result_status": "not_assessed",
      "rubric": {
        "code": "speech",
        "version": "candidate-0.1",
        "checksum": "synthetic-nonproduction-checksum"
      },
      "final_score_0_100": null,
      "coverage_fraction": null,
      "needs_human_review": true,
      "criteria": [
        {
          "criterion_code": "speech_clarity",
          "status": "not_assessed",
          "applicability": "undetermined",
          "score": null,
          "max_score": 5,
          "reason_code": "INSUFFICIENT_TEXT",
          "reason": "شواهد کافی برای ارزیابی معتبر وجود ندارد.",
          "evidence": []
        }
      ],
      "provenance": {
        "model_revision": "candidate-not-selected",
        "prompt_version": "candidate-prompt-unset",
        "scoring_policy_version": "candidate-undecided"
      },
      "publishable_as_official_score": false
    }

The fixture above illustrates a successful job with an unassessed evaluation, not an officially Published rubric or a deployable response. It cannot be returned from the authorized Published-rubric API without an approved rubric publication workflow. No numeric result is emitted in this synthetic abstention example. coverage is null because no full authorized rubric snapshot/applicability denominator is supplied. Real completed result must carry all pinned revision metadata and a fully validated criterion set.

**Synthetic text-span illustration**, where original Python text is «متن کوتاه»:

    {
      "source_kind": "original_submission",
      "quote": "متن",
      "start_offset": 0,
      "end_offset": 3
    }

- Candidate OD-11: code-point index, zero-based half-open [start_offset,end_offset), exact match against original Python str substring; never offsets into normalized/chunked text. The above span [0,3) points exactly to «متن». This is a proposed standard, not CONFIRMED.
- Original evidence: source_kind=original_submission, quote, original offsets; optionally immutable source hash used internally; caller must be authorized for content.
- Research corpus evidence: source_kind=approved_reference_corpus plus authorized corpus_id, corpus_revision/hash, document_id, corpus-local offsets, verification_method and access_scope. An internal corpus document must exist at its pinned revision; verify its quote independently. A textual citation from original_submission is NOT proof that its cited paper exists.
- No trusted corpus/authorized lookup or failed span validation => not_assessed with safe reason such as UNVERIFIED_SOURCE or EVIDENCE_UNVERIFIABLE; no external browsing or arbitrary file path/URL retrieval.
- Model structured result must be revalidated server-side. Reason codes (candidate): INSUFFICIENT_TEXT, MISSING_CONTEXT, NOT_APPLICABLE, UNVERIFIED_SOURCE, EVIDENCE_UNVERIFIABLE, MODEL_UNCERTAIN, INPUT_QUALITY_LIMITATION. Vocabulary is from provisional rubric baseline; official code set remains versioned.

## 5. Uniform HTTP error taxonomy (proposed)

ErrorDto (required): schema_version, error.code (stable uppercase machine code), error.message (safe localized/general wording), correlation_id. Optional retryable:boolean and details of **field names only**, never text values, token, hostname, SQL, prompt or stack.

| HTTP | Proposed code | Example trigger | Idempotency/security behavior |
|---|---|---|---|
| 400 | BAD_REQUEST / INVALID_CURSOR | malformed header/cursor/business rule | no job created |
| 401 | UNAUTHENTICATED | missing/invalid verified credential | no resource lookup |
| 403 | FORBIDDEN | permission denied when disclosure is safe | policy OD-07 |
| 404 | RESOURCE_NOT_FOUND | missing or out-of-scope resource | indistinguishable under privacy policy |
| 409 | IDEMPOTENCY_CONFLICT / VERSION_CONFLICT | same key different payload, stale feedback revision, immutable rubric collision | no partial commit |
| 413 | PAYLOAD_TOO_LARGE | exceeds approved policy | threshold OD-02 OPEN |
| 422 | VALIDATION_ERROR | invalid enum, missing required DTO, bad schema | no sensitive input reflection |
| 429 | RATE_LIMITED | authenticated capacity/quotas | retry metadata only if safe/approved |
| 503 | SERVICE_UNAVAILABLE | DB/internal model unavailable or admission closed | safe and retryable as applicable |
| 500 | INTERNAL_ERROR | unexpected internal fault | only correlation_id; sanitized audit |

Pending job/report may return HTTP 200 with processing_status=pending and no score, or 202 for status fetch; this policy is proposed **200** to keep read polling uniform. No fabricated HTTP endpoint is considered deployed. Trace IDs must never include user text.

## 6. Versioning, audit and error boundary

- Version triplet: API schema_version + pinned rubric code/version/checksum + model artifact/revision/hash and prompt version/hash. Preserve processing_status (transport), result_status (assessment outcome), needs_human_review (workflow flag) as distinct fields in DTOs, persistence and any versioned report contract. Store runtime version, preprocessing/scoring policy version, generation parameters, corpus revision and result revision where applicable.
- Audit successful and rejected transitions without source text; feedback append/revision and authorized resource read are audit-relevant. Database/outbox sink vs approved internal log sink remains OD-08.
- Python computes and persists score; explainability/revision data reflect exactly what was scored. Historical reports remain based on the original pinned rubric/model/policy, never silently recomputed with latest.
- HTTP Controller converts typed Core failures to statuses; Core is HTTP-agnostic; Infrastructure errors normalized without leaking SQL/details.
- Open decision gates: OD-01/02 for size/metadata, OD-04 for rounding/thresholds, OD-07 for roles/privacy, OD-08 for protected fields, OD-10 for idempotency/limits, OD-11 for offsets, OD-15 for report fields. Formal business sign-off Stage 12 D-015.

## 7. Stage 10 contract verification obligations

OpenAPI/docs generated from real Pydantic DTOs; schema validation of all synthetic examples; 202 replay and 409 collision concurrency; 401/403/404/413/422/429/503; IDOR and cross-org isolation; evidence quote exactness including Unicode/ZWNJ; no data leakage in errors/metrics; offset mapping tests, optional pagination cursor security; route discovery smoke and field-level authorization. All are NOT_RUN now because code is absent.

Cross references: [Detailed Design](02_detailed_design.md) · [File Matrix](04_file_change_matrix.md) · [ADR](05_architecture_decisions.md) · [Stage 01 Decisions](../requirements/05_open_decisions.md).
