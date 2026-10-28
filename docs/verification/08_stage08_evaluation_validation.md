# Stage08 — Evaluation Engine local acceptance record

Date: 2026-10-28. Stage: 08. **Verdict: DONE_LOCAL for synthetic technical gates; NOT a business-approved scoring engine or deployed model.**

## Implementation scope

- `src/core/services/text_evaluation/text_preprocessing_service.py`: original Unicode retained, constrained Persian character normalization, reversible per-character original-offset map including CRLF, lossless deterministic paragraph/section chunking, SHA256 fingerprint. Input validation rejects empty/oversized/surrogate/null data.
- `src/core/services/text_evaluation/criterion_evaluation_service.py`: rubric-bound per-criterion prompts include operational definition, applicability, exact 0..5 anchors and evidence requirements. Original text remains untrusted; no tool, lookup or external source. All structured LLM results independently checked before scoring. For invalid source quotes, abstain without numeric score.
- `src/core/services/text_evaluation/scoring_service.py`: Python-only weighted score per Implementation Plan section 4.4; exact integer numerator and denominator preserved plus explicit Decimal precision 64 for provisional display. Coverage is assessed applicable candidate weight / all six candidate weights (all-applicable **provisional denominator**). Zero assessed yields NULL score, zero coverage and mandatory review; not_assessed is never silently zero. No approved rounding or coverage threshold has been invented.
- `src/core/services/text_evaluation/text_evaluation_service.py`: constructor DI orchestration; exact RubricBinding checksum/type/version/tenant assertions, model and prompt revision metadata, input limits tied to provider's declared maximum, report with criteria, offsets, strengths/weaknesses/recommendations, score ratio, coverage, provisional status and needs_human_review. No DB writes/Controller/Worker (Stage09/10).
- Existing Stage07 LocalLlmProvider now exposes `declared_configuration` metadata (non-secret model ID, configured revision, model limits and runtime sampling). Revision remains **unverified** until corporate artifact attestation. Provider retains disabled-by-default policy.

## Conservative long-document policy

Text is chunked WITHOUT losing characters; each chunk contains its exact original start/end and can be individually validated. When source is larger than the trusted provider input limit, a bounded two-pass synthetic evidence-synthesis pathway evaluates all relevant chunks for eligible local-text criteria; exact global quote offsets are revalidated. Combined excerpts are NOT equivalent to full-source model access: every provisional synthesis is marked `DOCUMENT_SYNTHESIS_UNVERIFIED` and human review is required.

Coherence, structure, reasoning and novelty requiring global or authorized external knowledge are explicitly `not_assessed` when whole-document conditions cannot be verified. Unsupported chunks, mismatched maps, more than 32 chunks, or synthesis packet above the provider limit lead to fail-closed `not_assessed` (no score). There is **no undisclosed arithmetic average of chunk scores** and no silent truncation.

The 32-chunk cap is a conservative engineering safety limit, NOT an approved organizational workload SLA. Business-approved hierarchical synthesis/whole-document criteria, tokenizer-based capacity and real model accuracy remain OPEN / Stage11 integration. Long-text reliability should not be described as fully clinically/business validated.

## Actual executed CI acceptance evidence

GitHub Actions [run 40646409387](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40646409387) against code SHA `4ead605b93119c5751a48faa6cd1ccd1939ef9ae`: **completed / success**. Ubuntu 24.04, Python 3.12, purely synthetic in-process provider fixtures; no real vLLM/GPU, network inference or organization database was accessed.

| Gate | Observed result |
|---|---|
| Stage08 scoped tests: 3 domains, candidate weights/anchors, offsets, input/long-text and provenance | **37 passed in 0.71s** |
| Entire Python non-PostgreSQL test suite (includes 37 Stage08) | **196 passed in 2.45s** |
| Stage03 unittest | **38 PASS** |
| Stage02 unittest | **12 PASS** |
| Stage04 dependency/network/secret static guard | **PASS (28 runtime files)** |
| Pinned Python dependencies | **pip check PASS** |
| Model-generated quality / reference evidence truth, enterprise IAM/TLS/KMS/No-Egress/GPU and complete deployed model integration | **PENDING_SERVER — NOT_RUN** |

Negative regression tests cover corrupt or repeated criteria, out-of-range and bool score, invalid reason-code/abstention, zero coverage, exact rational/Decimal calculation, SHA mismatch, prompt injection attempt that cannot change bound Rubric, Unicode ZWNJ/combining marks/CRLF, empty/oversize/long text, bad synthetic evidence, two-pass offset map, bypass of provider limit, and proper synthetic model revision recording.

Earlier runs were not silently treated as successful: Stage08 40645842199 (workflow validation failed before jobs), 40645915611 (escaped comment caused NameError), 40646373385 (oversize synthetic 2-pass fixture) failed. These were corrected and the latest run above **passed**. This report relies on the last actual CI result only.

## Acceptance and unresolved restrictions

Stage08 local design/validation/scoring/abstention/evidence/segmentation gates: PASS_CI_SYNTHETIC. The output is ALWAYS a candidate/provisional score with `publishable_as_official_score=false`, `needs_human_review=true`. Human semantic relevance and unsupported explanations are **not machine-proven**; assessed criteria carry `SEMANTIC_REVIEW_REQUIRED`. Missing original-source evidence is never published as verified.

OD-03/04/09/11: official scoring rounding, denominator/applicability, human review/coverage and Unicode contract remain OPEN or PROPOSED. No official policy assumed. D-017 model quality, expert agreement, actual long-context throughput, corpus authorization, live tokenizer/model revision and network/security require Stage11; D-015 final formal rubric acceptance in Stage12.

Stage08: **DONE_LOCAL**, Stage09: **NOT_STARTED** until explicit request. See `docs/verification/08_stage08_deferred_stage11_ledger.md`.

## Independent user-local tests (safe, no PostgreSQL, inference server, GPU)

    cd /srv/projects/text-evaluation-service
    git pull --ff-only origin main
    .venv/bin/python -m pip check
    .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage08_engine.py
    .venv/bin/python -m pytest -q -p no:cacheprovider tests --ignore=tests/test_stage05_postgres.py --ignore=tests/test_stage06_rubric_postgres.py

These Simorgh tests remain NOT_RUN until an operator supplies actual shell output. Do not touch shared Simorgh PostgreSQL, Docker, vLLM/GPU or corporate Secrets.

## 2026-10-28 — Independent Simorgh Stage08 local test evidence

**Source:** Operator-provided terminal transcript from `/srv/projects/text-evaluation-service` on Simorgh. `git pull --ff-only origin main` succeeded as a fast-forward from `7f5f122` to `272bfe7` (reviewed Stage08 code). Existing `.venv` was reused; no dependency installation, PostgreSQL migration, vLLM invocation or GPU operation was shown.

| Command | Actual observed result | Classification |
|---|---|---|
| `.venv/bin/python -m pip check` | `No broken requirements found.` | `PASS_USER_SERVER_REPORTED_DEPENDENCY_CONSISTENCY` (not a security/provenance audit) |
| `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage08_engine.py` | `37 passed in 0.69s` | `PASS_USER_SERVER_REPORTED_STAGE08_37_OF_37` |
| `.venv/bin/python -m pytest -q -p no:cacheprovider tests --ignore=tests/test_stage05_postgres.py --ignore=tests/test_stage06_rubric_postgres.py` | `196 passed in 2.03s` | `PASS_USER_SERVER_REPORTED_NON_DB_196_OF_196` |

The 37 focused tests are a **subset** of the 196 non-database tests, not an additional disjoint set. Neither PostgreSQL integration module was run on Simorgh in this invocation. CI [run 40646409387](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40646409387) separately passed 37/37 and 196/196 on Python 3.12 with synthetic fixtures. This operator run independently confirms the same counts without a live LLM.

**Trust and release boundary:** These are synthetic validation/algorithm tests; they do not verify AI quality, trusted corpus, real inference, model revision, company-network No-Egress, tenant IAM, TLS, GPU or PostgreSQL integration. Stage11 S08-S11-01..06 are still `PENDING_SERVER`; unresolved OD-03/04/09/11 and Stage12 final business signoff are unchanged. No official scoring approval or authorization for protected customer data is implied.

**Stage status:** Stage08 `DONE` for local gates; Stage09 `NOT_STARTED`. This entry records **user-executed terminal evidence** only. The assistant did not execute these tests on Simorgh and this documentation-only update did not modify program code, model, secrets or database.
