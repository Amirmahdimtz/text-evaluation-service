# Stage 11 — AI Quality and Calibration Report

**State:** `NO_MEASUREMENTS / PENDING_SERVER`; no model selected. Prepared 2026-10-28. This is a prospective report, **not** actual benchmark results.

## Candidate comparison (NOT measured)

| Candidate | Role | Revision/hash/license | Real JSON/schema, Persian accuracy, inference | Decision |
|---|---|---|---|---|
| `Qwen/Qwen2.5-7B-Instruct` | Baseline candidate | `UNVERIFIED` artifact/license approval | `PENDING_SERVER` | `CANDIDATE` |
| `Qwen/Qwen3-14B` | Primary benchmark candidate | `UNVERIFIED` artifact/license approval | `PENDING_SERVER` | `CANDIDATE` |
| `vLLM` | Candidate internal serving runtime | Deployed exact version not verified | `PENDING_SERVER` | `CANDIDATE` |

Source: [Model selection](../ai/01_model_selection.md), [protocol](../ai/02_benchmark_protocol.md), [Stage03 deferred ledger](../ai/03_benchmark_results.md).

## Data governance and comparison protocol

Approve legal source provenance and expert labeling for `speech`, `media` and `research`; group-disjoint development/calibration/blind holdout; domain-specific `candidate-0.1` temporary rubric (not business-approved), stable checksum and fixed criterion anchors; pinned prompt, schema, model, tokenizer, chat template, decoding/thinking configuration, quantization and runtime. Keep all genuine text, reference labels, dataset hashes and sensitive manifest metadata in authorized private storage. Do not optimize repeatedly on blind holdout.

Independently validate JSON schema, evidence quote exactly matching original Unicode code-point half-open offsets, correct `not_assessed` and lack of unsupported scientific/novelty claims. The model must not compute or publish overall official scores; backend deterministic scoring remains subject to OD-03/04/11. No tools, external data exfiltration or model-supplied instructions may change the rubric.

## Metrics awaiting real measurement

| Metric | Required evidence | Current |
|---|---|---|
| MAE and expert agreement | Expert/adjudicated scores, sample counts and breakdown per criterion/domain; confidence intervals when meaningful | `NOT_MEASURABLE` |
| Evidence exact match and relevance | Valid source spans / all spans and separately expert-relevant spans / all evaluated | `NOT_MEASURABLE` |
| Unsupported factual claims/hallucination | Checked claims denominator, adjudication and domain-specific failure categories | `NOT_MEASURABLE` |
| Coverage, correct abstention, required criterion gaps | Per-domain denominators and expert-insufficient-evidence labels | `NOT_MEASURABLE` |
| JSON/schema validity, retry, terminal failure | All attempted outputs, not just accepted outputs | `NOT_MEASURABLE` |
| Stability, political neutrality, drift, long-document synthesis | Repeated fixed-revision runs, balanced topic/style/length fixtures and reference labels | `NOT_MEASURABLE` |

**Numeric thresholds** `OD-14`, corpus rights `OD-08/13`, workload `OD-12`, evidence rules `OD-11`, and rubric/scoring policies `OD-03/04/09` remain `OPEN`; do not invent acceptable values. Golden dataset/model execution IDs `S11-AI-01..10`, `S08-S11-01..05` remain `PENDING_SERVER`.

**Model selection:** `BLOCKED / NO_MODEL_SELECTED`. Final selection requires side-by-side real evidence, legal/security reviews and organization-approved thresholds. Stage12 commercial acceptance is separate.

## Preliminary real-model connectivity signal — synthetic one-shot, 2026-10-28

One operator-reported live Simorgh request using source commit `0ba42a2` completed with HTTP 200, `finish_reason=stop`, and an exactly valid **one-field synthetic JSON-schema** completion. This indicates limited structured-output feasibility for the **currently advertised model** only. The served model ID is deliberately redacted and not linked to a pinned weights/tokenizer revision, approved license, or model comparison. The payload was not a `CriterionInference` object and had **no rubric, evidence offsets, groundedness or quality reference label**. Consequently the result is `PASS_AUXILIARY_SYNTHETIC_SMOKE`, **not** an AI-quality metric, nor evidence of compatibility with all JSON Schema constraints.

The required 2-model, 3-domain golden benchmark with expert adjudication, MAE, supported claims, abstention, fairness and confidence intervals remains `NOT_MEASURED` / `PENDING_SERVER`. **Do not update numerical quality thresholds or select a model from this observation**. The one-shot permission has been consumed; real benchmark requires independent owner approval, licensed artifacts and gold data. [Recorded evidence](09_stage11_single_inference_smoke.md).

## Full criterion structured output failed to verify — real Simorgh synthetic observation, 2026-10-31

One opt-in synthetic request on the actual on-prem inference endpoint returned HTTP `200` in a single observed `6047 ms` request-to-headers timing but was rejected as `CRITERION_CONTRACT_UNVERIFIED`. The transcript deliberately omitted the generated response and model identity. Thus **full CriterionInference schema, assessed status and grounded quote/offset compliance were not demonstrated**. The specific failure type is **unknown**, not proven to be truncation, invalid quotes, unsupported schema, or legitimate abstention. This is not a benchmark and cannot justify selecting/rejecting a model solely on quality.

Engineering patched the test harness to report non-sensitive static failure categories in future without changing the strict validator; CI mocked/offline run `41181109595` **90 passed**. The previous single-field JSON `ack` success remains auxiliary and distinct. The expert-adjudicated three-domain, two-model benchmark is still `NOT_MEASURED`, and all related mandatory acceptance IDs remain `PENDING_SERVER`. See [runbook](10_stage11_criterion_contract_smoke.md).

## Real second synthetic CriterionInference result — groundedness failure, 2026-10-31

A second, explicitly opted-in live Simorgh inference returned HTTP `200` with `QUOTE_OFFSET_MISMATCH` in the strict evidence verifier: `completion_tokens=113` of the requested 320, `prompt_tokens=166`, `total_tokens=279`, `elapsed_ms=6010`. No raw output or private model ID was published. This is **not** success at evidence-backed quality or model selection: at least one quote failed `source_text[start:end] == quote`. Without response content, we cannot tell whether the quote itself was not verbatim or the offsets were incorrect.

An offline-only follow-up `fd072f1` clarified offsets and keeps invalid evidence rejected; parser errors are now classified as `LLM_QUOTE_NOT_FOUND` vs `LLM_QUOTE_OFFSET_INVALID` and prompt version advances to `stage08-prompt-candidate-0.2`. Relevant GitHub Actions passed on mocked/synthetic code, but **there has been no real-model retest after this correction**. The previously achieved simple `ack` JSON schema smoke remains narrower; the real two-model/three-domain expert-labeled AI benchmark remains `NOT_MEASURED`, Stage11 `BLOCKED`. [Full details](10_stage11_criterion_contract_smoke.md).

## First full on-prem grounded synthetic criterion contract PASS — 2026-10-31

The operator provided a redacted real vLLM contract smoke with `PASS_SYNTHETIC_CRITERION_CONTRACT`, `assessment_status=assessed`, `criterion_schema_valid=true`, `grounded_evidence_valid=true`, `evidence_count=1`, `HTTP 200`, `elapsed_ms=6449`, and usage `206` prompt/`116` completion/`322` total tokens, with no retries. It is the **first observed fully grounded single-criterion real model contract success** after the prompt's Python Unicode offset instructions. The earlier one-shot quote-offset error remains historical negative evidence.

This is only **one short synthetic clarity criterion**: no labeled rubric accuracy assessment, comparison across two pinned models, `speech`/`media`/`research` dataset evaluation, confidence interval, repeatability, fairness, latency distribution or model selection. Treat it as `AUXILIARY_CONTRACT_COMPATIBILITY_PASS` and **not** as a measured quality KPI. The model artifact/license/pin remains unverified. All required model quality/benchmark items are `PENDING_SERVER`; `Stage11=BLOCKED`. [Details](10_stage11_criterion_contract_smoke.md).

## Stage11 bounded real Persian candidate-model evaluation harness — 2026-10-31

The user requested qualitative inspection of actual Persian text assessments (criterion-by-criterion scores, reasons, strengths, weaknesses, improvement suggestions and overall summary) with the **already running shared vLLM instance**. The prepared `scripts/verification/stage11_persian_domain_smoke.py` is an **operator-only, explicit opt-in** harness. It uses the existing `TextEvaluationService`, `CriterionEvaluationService`, `LocalLlmProvider`, `ScoringService`, and pinned proposed Stage06 candidate rubric fixture, instead of inventing a second scoring implementation. Inputs are **three fixed, public synthetic Persian passages**, one per domain: `speech`, `media`, `research`. Each command evaluates **only one domain**. All six domain criteria get separate decisions, but `research_novelty` correctly abstains with no model request (no trusted comparison corpus). The weighted overall score is **provisional, deterministically calculated by Python** and flagged `needs_human_review` and `official_score=false`.

**Operational bounds:** default CLI outputs `DRY_RUN_NO_NETWORK`; only `--execute-approved` contacts `127.0.0.1:8000`. One bounded `GET /v1/models`; at most **6 serial POSTs**, **no retries**, max `640` completion tokens/request, timeout 45 seconds/request, mandatory 3-second spacing, only short built-in synthetic texts, stop at first model/contract failure. Application YAML, enabled Worker/HTTP, other project services, GPU weights and DB are left untouched. The model ID and actual model output are **not committed**; the command prints per-criterion assessments of **synthetic** texts locally to the operator. Model revision is explicitly `unverified`; no claim about legal/provenance approval. No global multi-client quota or proof of non-interference is implied by the local serialization.

**Test execution:** Offline suite and protected CI must be checked separately before PASS classification. Real server inference is **`PENDING_OPERATOR_SIMORGH`** and not authorized as an unbounded unattended benchmark. First run only `speech` in a coordinated low-impact window and review actual other projects' latency/errors/queues before considering separate `media` and `research` runs. Without qualified expert annotations, semantic correctness and AI quality scores remain `NOT_MEASURABLE`. All 56 original enterprise Stage11 tests remain `PENDING_SERVER`, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.

## CI-verified Stage11 Persian-domain harness — 2026-10-31

The bounded three-domain text-assessment harness was tested in [offline workflow 41197301347](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41197301347): **98 tests passed** including the harness's three fixture-domain engine tests and budget/dry-run/config negative checks. Code commit `12c4017`. This establishes **functional test harness readiness**, not that the live shared model has judged the three texts correctly. Planned first real operator run: `--domain speech --execute-approved`, once, in an approved quiet window with owner observation. Afterwards inspect every criterion's grounded quote offsets, score, strengths, weaknesses and recommendations; the final provisional score is Python-derived. Real `media` and `research` runs and expert labeled quality review remain pending.

## First real Persian six-criterion test blocked at first model request — 2026-10-31

The user-operated `speech` shared-vLLM test **failed** with `LLM_CIRCUIT_OPEN` after **one attempted** criterion inference; zero retries and no subsequent criteria were executed. The GPU0 snapshot before the call was `18847 MiB` used and `89%` instantaneous activity. This was a real runtime **failure**, not a model scoring result. No score, strengths, weaknesses, recommendations, grounded evidence or Python aggregate was produced; therefore this attempt supplies **no information about Persian evaluation accuracy**. Under the previous fail-closed `circuit_failures=1` profile, transient upstream `429/5xx` and timeout/network errors are indistinguishable in the CLI. The safe categorical diagnostic improvement is offline-only until the next separately approved runtime check; no re-inference was performed. Do not use the prior simple single-criterion PASS to claim the six-criterion engine benchmark PASS. Proceed only after the shared service owner confirms a low-impact window and the actual cause/category is known.

## Offline recovery of error observability, not model quality — 2026-10-31

Following the failed on-prem `speech` attempt, categorical redaction of first-failure `LLM_CIRCUIT_OPEN` was verified by [Stage11 offline CI 41198491123](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41198491123): `103 passed`. The Provider's safe-error regression suite also passed [Stage07 offline CI 41198491064](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41198491064): `63 passed`. **No renewed model run, no six-criterion scores, no AI quality evidence** resulted from this corrective test pass. Competing-project impact and whether the old error was HTTP busy or timeout remain unknown until a separately authorized monitored run. Original 56 enterprise IDs remain `PENDING_SERVER`.

## First actual guided real criterion contract and unforced three-domain probe — 2026-11-03

**New, limited observed real-model result (not quality):** Simorgh operator ran a single synthetic text request using the project's `CriterionInference` JSON Schema and `decode_criterion_response` validator against `shared-llm` (Qwen3-8B-AWQ). Result `HTTP 200`, `FULL_CRITERION_CONTRACT_PASS`, guided score `3`, one validated exact source quote/offset, `225` total tokens. The score and quote were explicitly specified in the prompt, so **this is not evidence of autonomous rating validity, evidence relevance or expert agreement**.

**Ready for operator execution, not yet a measured result:** a minimal three-domain sequential live adapter probe now uses the actual app's `LocalLlmProvider` and `CriterionEvaluationService`, candidate rubric weight/anchors and *no preselected score or quote*. It performs exactly one synthetic criterion per domain and records only contract validity, optional criterion score, status, evidence count and elapsed duration. It is **not** a full three-domain benchmark; even 3 successful schemas cannot establish quantitative AI quality. `model_revision_verified=False`; the source revision is not attested.

**Offline test evidence:** [CI `41639035765`](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41639035765) `SUCCESS`, 12 new probe contract/guard tests passed, Stage11 offline suite 59 passed. Live three-domain result `PENDING_SERVER_OPERATOR`. All real expert MAE/relevance/abstention assessments and two-model comparison remain `NOT_MEASURABLE` / `PENDING_SERVER`.

## First unforced real three-domain criterion probe: observed partial failure — 2026-11-03

The operator actually ran the new Stage11 `--execute-live` code on Simorgh at source `a35fd3a`. It used three static synthetic Persian texts, one selected candidate rubric criterion per domain, no fixed answer, one-at-a-time inference and zero retries. Summary output:

- `speech_clarity`: **typed-valid `not_assessed`**, score null, evidence count zero, 1738 ms. Not a scoring accuracy/coverage success.
- `media_message_clarity`: **`LLM_CIRCUIT_OPEN`**, 45007 ms. The configured 45s timeout makes a timeout plausible, but actual failure kind was not in the emitted report; `429/5xx` or other transport failures cannot be ruled out from this output alone.
- `research_academic_writing`: **`LLM_CIRCUIT_OPEN`**, 1 ms, likely rejected without external inference due to the previous open circuit.

Overall `REAL_MODEL_THREE_DOMAIN_CONTRACT_PARTIAL_FAILURE`. The `requests_attempted=3` field denotes attempts at evaluation in Python, not three successfully dispatched model requests. Model revision remains unverified; quality benchmark remains false. This is **not** three successful domain assessments or AI accuracy evidence. A valid abstention is intentionally preferred over fabricated scoring and is a separate future calibration metric.

**Mandatory next work:** redacted first-failure classification, fail-fast circuit handling under the shared-GPU low-impact policy, re-run only with approved owner/limits, then collect representative expert reference labels and repeat a version-pinned multi-domain benchmark. Keep quality status `NOT_MEASURABLE` and Stage11 gate `BLOCKED`.

## Stage11 media-only live diagnostic confirms request timeout — 2026-11-03

One real synthetic `media_message_clarity` inference in an operator-authorized shared-vLLM run ended after 45,050 ms with `LLM_CIRCUIT_OPEN` and a redacted **`REQUEST_TIMEOUT`** failure category. The criterion did **not** complete, and no model score or quote was accepted. This is a real failure and cannot be counted as AI model quality evidence. Differentiate configured 45-second request deadline from root cause: it may include queueing, prefill, constrained decoding or competing traffic; none has been established. Prior guided one-criterion contract success remains limited and `speech` abstention remains separate. The next check should be read-only host/GPU and vLLM queue telemetry, without reading or publishing potentially sensitive request logs. Stage11 BLOCKED.


## Stage11 real media criterion with non-thinking still timed out — 2026-11-03

Operator ran source `46cd148` (fast-forward `d7222b2..46cd148`), confirmed the new `--domain media --disable-thinking` dry-run produced `DRY_RUN_NO_NETWORK` and `thinking_mode_requested=disabled`, then opted into one synthetic `--execute-live --domain media --disable-thinking` probe on existing shared `shared-llm`.

**Actual result:** `media_message_clarity` **FAILED** after 45054 ms with `LLM_CIRCUIT_OPEN`, `failure_kind=REQUEST_TIMEOUT`, one attempted Python criterion evaluation, no retries, no accepted score or evidence. The whole report remained `REAL_MODEL_THREE_DOMAIN_CONTRACT_PARTIAL_FAILURE`, `model_revision_verified=false`, `quality_benchmark=false`. The prior default-thinking media run also failed at 45093 ms. Comparing these two censored timeout durations **does not measure model inference speed** or establish that the Qwen3 request-level thinking switch was effective in this vLLM deployment. It only establishes that the explicitly requested switch did not resolve the observed 45s timeout.

Prior operator concurrent metrics while `media` was running: `num_requests_running=1`, `num_requests_waiting=0`, KV-cache fraction approximately 0.006→0.011. This supports on-engine execution during the prior run, but no new in-flight telemetry was collected for the disabled-thinking run. No new actual model quality measurements, validated score, quote or expert agreement exist. Next: read-only vLLM v0.10.2 token and completion counters, confirm serving/chat-template configuration through approved metadata only, then design a single bounded, time-correlated synthetic profiling run **only if separately authorized**. No need to increase timeouts or modify a shared vLLM container without root-cause evidence. Stage11 `BLOCKED`; Stage12 `NOT_STARTED`.

## Simorgh real 256-token diagnostic — 2026-11-03

One real synthetic `media_message_clarity` criterion was submitted with opt-in non-thinking mode and output cap 256. The model returned a complete HTTP envelope with `usage.completion_tokens=256` and `finish_reason=length`, but its response content was **invalid JSON**. The existing strict Provider correctly rejected it as `LLM_INCOMPLETE_GENERATION` after 23.427s. This is **not** successful model assessment. The result includes no accepted score/evidence; no expert-labeled accuracy or rubric semantic quality was established. A previous shorter synthetic schema example that passed does not supersede this failure. Keep AI quality `NOT_MEASURABLE`, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.


## Stage11 candidate Prompt 0.3: actual quality pending — 2026-11-03

The new version `stage08-prompt-candidate-0.3` requests concise
Persian comments and preserves every original rubric evidence rule,
JSON field and abstention. No score or evidence validator changed.

[Offline CI 41662617861](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41662617861)
passed 41 Engine and 520 regression tests (11 skipped).
No live model result, reduced completion-token count or expert-validated
Persian quality claim exists for this version. The previous 256-token
incomplete JSON and 512-token timeout remain failed observations.
Stage11 BLOCKED.


## Stage11 prompt version 0.3 real media test failed timeout — 2026-11-03

The Simorgh operator evaluated one synthetic `media_message_clarity` criterion with `stage08-prompt-candidate-0.3`, request-level `thinking_mode=disabled`, 512 max output tokens and a fixed 45s deadline. The provider returned `LLM_CIRCUIT_OPEN` with `failure_kind=REQUEST_TIMEOUT` after 45.034s. No HTTP completion metadata arrived: `finish_reason=UNAVAILABLE`, `json_syntax=UNAVAILABLE`, `reported_usage=null`. The contract **FAILED**; no score, evidence or quality measure was accepted.

During the shared-server observation window, read-only aggregated Prometheus counters changed by `+401` generated tokens and `+44.876778s` of inter-token latencies, but the values cannot be attributed to this request alone. This does not prove a 512-token `length` stop; the actual finish reason is unobserved. Compared with prior `v0.2` tests, no improvement in complete validated output has been demonstrated. The new wording preserves schema/rubric rules in offline tests, but its **effectiveness and Persian semantic quality remain unverified**. Do not claim official quality, breakthrough, acceptable accuracy or a complete model contract. Stage11 `BLOCKED`; Stage12 `NOT_STARTED`.


## Stage11 compact JSON contract tests vs actual rubric quality — 2026-11-03

The offline compression comparison constructs six synthetic examples and proves
that JSON whitespace elimination preserves their complete typed
`CriterionInference` values and exact quote-offset equality. It does NOT
prove that a single evidence span meets any expert rubric's semantic
evidence requirements, that model-generated explanation quality is
unchanged, or that Qwen's token count falls by the same byte ratio.

The isolated Stage11 decoder A/B is prepared and mock-tested: one
structured JSON-schema arm and one unconstrained arm share all other
request fields, and both continue to use strict Pydantic/evidence
validation. An unconstrained output must never bypass the production
contract, score validator, human review or No-Egress safeguards.
The real-model test remains `PENDING_SERVER`. No expert accuracy metric
is measurable from the synthetic samples; Stage11 BLOCKED.

## 2026-11-04 — shared GPU one-pair decoder experiment observed

The real model completed two HTTP envelopes for an operator-authorized
synthetic media criterion comparison. Structured `json_schema`:
29,118ms, 635 input + 256 output tokens, `finish_reason=length`,
invalid JSON, failed strict contract. Unconstrained mode: 2,327ms,
identical reported token counts, `finish_reason=length`, invalid
JSON, failed strict contract. No criterion score/evidence is accepted
from either response. The much faster unconstrained arm is NOT a
valid output mode for this application and does not establish
semantic quality or expert agreement. Model quality remains
`NOT_MEASURABLE`; Stage11 `BLOCKED`.
