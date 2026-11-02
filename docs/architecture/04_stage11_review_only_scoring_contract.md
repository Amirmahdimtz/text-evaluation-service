# Stage11 — Review-only aggregate-score response contract (D-008 / OD-04 OPEN)

**Decision type:** confirmed **current implementation behavior**, not a
business approval of rubric weights, applicability, rounding or an official final
score. Source reviewed 2026-11-02.

## Transport contract for GET /api/v1/text_evaluation/evaluations/{evaluation_id}

- `criteria[].status = assessed`: numeric integer `score` in 0..5, with
  source-anchored evidence in the encrypted, scope-protected details. An
  `assessed` score without valid evidence is rejected by the protected executor.
- `criteria[].status = not_assessed`: `score = null` and a nonempty reason
  code; missing evidence must **not** silently become score 0.
- `coverage`: measured assessed Rubric weight divided by the 100 total
  candidate weights; stored and returned for a finished report. Missing and
  pending reports may have `coverage=null`. Coverage is **not** a quality score.
- `provisional_score`: when a completed review-only result contains the **full
  pinned criterion set**, the API reconstructs the **candidate aggregate**
  deterministically via `ScoringService.calculate` and returns its
  high-precision `Decimal` value. It is `null` for pending, failed,
  incomplete/legacy criterion sets, and zero-assessed results.
  **This value is not an official published grade.** The historical
  `Evaluation.overall_score` remains `NULL`: the Worker intentionally
  writes `overall_score=None` until OD-04 approves rounding and publication.
  No model output is accepted as a final score.
- `needs_human_review`: `true` for `partial` and
  `needs_human_review` reporting states. An actual published official
  score is unsupported; `publishable_as_official_score=false` on this API.
- `status`: currently the persisted evaluation lifecycle/result state,
  not the Stage02 proposed pair of `processing_status` and
  `result_status`. Do not claim those proposed fields exist on the API.

## Internal calculation (not an official persisted grade)

`ScoringService.calculate` produces
`provisional_score_0_100: Decimal | None` (high-precision candidate value),
`coverage_fraction`, `exact_score_ratio` and
`exact_coverage_ratio` from the pinned Rubric and criterion scores.
Its formula renormalizes the assessed weights to 0..100; unassessed criteria
contribute **zero coverage**, not a zero score. An empty assessed set yields
`None`, not zero. A missing required criterion or a partial assessment
requires explicit human review. It also sets
`publishable_as_official_score = false`.

This provisional calculation **does not define** approved precision,
applicability/denominator, an expert-accepted Rubric or the permission to
publish an overall grade. The current Evaluation table has
`overall_score Numeric(6, 3)`; blindly writing the unrounded
64-digit Decimal into that column would silently round values.
**Do not change the persistence restriction or expose a rounded numeric
aggregate without deciding OD-04.**

## Acceptance criteria before implementing numeric overall-score delivery

1. The product owner / domain SMEs decide whether to expose an explicitly
   labeled **unofficial candidate aggregate** for partial and fully assessed
   outputs, or only a signed-off official grade. Document purpose and UI label.
2. Approve whether missing required criteria or non-applicability suppress
   the numerical aggregate; define coverage threshold and human-review rules.
3. Choose documented rounding/precision and a versioned Scoring Policy; adapt
   `overall_score` storage (or a separately typed provisional field) and
   migrations as needed, with historical report immutability preserved.
4. Test deterministic scoring with real immutable Rubric snapshots, both
   `assessed` and `not_assessed`, exact ratios and relevant cross-tenant
   encrypted results; test null behavior for pending/failed/review states.
5. Evaluate actual model quality before accepting any generated criterion score
   as business-grade.

**Current status:** candidate numeric aggregate is available **only on an
authorized completed-report read** and never persisted as an official grade.
The immutable snapshot and stored per-criterion scores are used for deterministic
reconstruction. Numeric overall-score publication/rounding policy
**OPEN_OD04**, Stage11
`BLOCKED`, Stage12 `NOT_STARTED`. This document does **not** make an
unapproved rubric official.
