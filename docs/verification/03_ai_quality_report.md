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
