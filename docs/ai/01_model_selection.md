# Stage 03 — Model Selection and Decision Record

> Status: CANDIDATE_REVIEW / NO_MODEL_SELECTED · 2026-10-21 · Requirement: FR-04, FR-06, FR-10, FR-11, FR-12; NFR-05/08/11/12. This document contains a desk review, **not** a comparative inference benchmark or organizational legal approval.

## 1. Preflight and authority

- Baseline GitHub `main`: `6f650728e80849f65f46b50c81ab2da500ac6d53` (2026-10-21). Recursive tree contained five Stage 01 docs, five Stage 02 docs and a Stage 02 documentation QA script; no `src/`, inference endpoint, model weights, requirements/lockfile, CI or deployed application.
- Explicit user exception permits **conditional entry** into Stage 03 while Stage 02 stays `BLOCKED` for executable DI/Bootstrap/DB/WebService checks. Those tests remain `NOT_RUN` with Stage 04/05/10 ownership.
- `D-002` and `D-003` CONFIRMED: internal-only inference, no external submission of text, and mandatory reference architecture. `D-006` (vLLM) and `D-007` (Qwen3-14B) remain `CANDIDATE`. `D-008` (rubric parameters) remains `PROPOSED`. `OD-02/03/04/11/12/13/14` remain OPEN.
- Benchmark-only rubric `candidate-0.1` must never be presented as Published or approved for official grading.

## 2. Initial candidate matrix (static/public documentation only)

| Dimension | Baseline: Qwen2.5-7B-Instruct | Candidate: Qwen3-14B |
|---|---|---|
| Canonical model ID | `Qwen/Qwen2.5-7B-Instruct` | `Qwen/Qwen3-14B` |
| Model family | Qwen2.5 instruction-tuned | Qwen3 instruction-tuned, thinking/non-thinking modes |
| Upstream metadata license | Apache-2.0 reported | Apache-2.0 reported |
| Enterprise/commercial clearance | `PENDING_ORG_LEGAL_REVIEW` (license notice and redistribution conditions) | `PENDING_ORG_LEGAL_REVIEW` |
| Public model parameters | ~7.62B | ~14.8B |
| Context advertised | 131,072 with documented long-context configuration; effective usable limit untested | 32,768 native; up to 131,072 via YaRN with configuration and degradation risks; effective usable limit untested |
| Persian ability | `UNVERIFIED` on the required domains; generic multilingual model documentation is not evidence | `UNVERIFIED` on the required domains; claims of multilingual coverage are not Persian benchmark results |
| Structured rubric JSON validity | `PENDING_SERVER` | `PENDING_SERVER` |
| vLLM runtime compatibility | `PENDING_SERVER` for installed version and tokenizer | `PENDING_SERVER` for installed version, tokenizer and thinking parser |
| GPU/KV memory and speed | Formula-based estimate only; no measurement | Formula-based estimate only; no measurement |
| Reproducibility | Exact model revision and tokenizer/checksums `UNVERIFIED` | Exact model revision and tokenizer/checksums `UNVERIFIED` |
| Status | BASELINE_CANDIDATE | PRIMARY_BENCHMARK_CANDIDATE |

These are **two choices for an experiment**, not two experimentally compared models. No Persian win/loss, latency or accuracy ranking is asserted. If actual hardware cannot fit 14.8B, the AI lead must propose a lower-capacity alternative and register the changed comparison; no silent substitution.

### Public sources checked (read-only; not model artifacts imported)

- Qwen3-14B official upstream model card and repository: https://huggingface.co/Qwen/Qwen3-14B and https://huggingface.co/Qwen/Qwen3-14B/tree/main
- Qwen2.5-7B-Instruct official upstream model card and repository: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct and https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/tree/main
- Upstream license must be read from the **same pinned revision** ultimately imported, with license/notice record and legal sign-off. The mutable `main` model refs are NOT acceptable reproducible revision identifiers.
- vLLM structured-output docs: https://docs.vllm.ai/en/latest/features/structured_outputs.html ; the correct API depends on the **installed** version (legacy `guided_json` removed in v0.12.0 according to upstream project docs).

## 3. Artifact admission checklist (per model; all presently PENDING)

1. Security + Infrastructure approve internal model storage, import pathway, network and license use **before** artifact transfer.
2. Record immutable upstream commit SHA, source URI, responsible importer, time, model card/license/notices; store an internal manifest and SHA-256 for **every** weight shard, config and tokenizer file.
3. Verify obtained bytes and tokenizer/chat template against approved manifest in the internal environment. No `trust_remote_code` override unless separately reviewed; inspect model/config for unexpected executable code.
4. Pin Python/runtime/container revisions and structured-output implementation; test behavior with source of truth from the installed `vllm --version`.
5. Confirm prompt-template compliance, output parsing, sensitive logging disabled, network deny-by-default and no tool/SQL/remote calls available to models.
6. Confirm legal authorization of commercial/organizational deployment of the **specific** artifact and its dependencies. Metadata license is preliminary, not a completed legal review.

## 4. Comparison and decision

Decision dimensions: (1) expert MAE and inter-rater ceiling, (2) validated quote/source relevance, hallucination and correct abstention, (3) Persian quality and fairness per domain, (4) schema/JSON validity and stability, (5) latency/capacity and OOM, (6) license/provenance/security, (7) operational complexity. Use the same frozen Benchmark Protocol and report uncertainty/coverage for each metric; **do not rank unmeasured cells**.

**Current decision: `BLOCKED` for selection (Stage 03 `IN_PROGRESS`).** The Qwen3-14B + vLLM pairing remains only a *conditional investigation priority*, not `SELECTED_CONDITIONALLY`. A final comparison requires two actually executed candidates, expert labels, authorized inference and measured capacity. If quality, security or hardware fails, record `REASSESSMENT_REQUIRED` after real evidence rather than declaring deployment readiness.

**Decision requests:** `OD-13` (GPU, isolated network, permitted artifact import and software), `OD-14` (golden dataset, expert raters, acceptance thresholds), `OD-02/12` (document length and workload), `OD-03/04/11` (rubric/evidence policy). Owners: Infrastructure/Security/AI Lead; AI Quality Lead/SMEs/Product Owner; Technical Lead respectively.

Traceability: [Protocol](02_benchmark_protocol.md) · [No measurements / results](03_benchmark_results.md) · [Resource plan](04_inference_resource_plan.md) · [Decision Log](../requirements/05_open_decisions.md).
