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
