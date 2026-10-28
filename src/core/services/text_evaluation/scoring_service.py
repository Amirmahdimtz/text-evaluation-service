"""Deterministic exact-Decimal candidate scoring; never publish unapproved policy."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from src.core.services.text_evaluation.rubric_schema import RubricSnapshot
from src.infrastructure.di.inject import inject

D5 = Decimal(5)
D100 = Decimal(100)


@dataclass(frozen=True)
class CriterionScore:
    criterion_code: str
    status: str
    score: int | None
    reason_code: str | None = None


@dataclass(frozen=True)
class ScoringOutcome:
    provisional_score_0_100: Decimal | None
    coverage_fraction: Decimal
    result_status: str
    needs_human_review: bool
    publishable_as_official_score: bool
    rounding_policy: str
    required_missing: tuple[str, ...]
    exact_score_ratio: tuple[int, int] | None
    exact_coverage_ratio: tuple[int, int]


@inject
class ScoringService:
    def calculate(self, *, rubric: RubricSnapshot,
                  outcomes: tuple[CriterionScore, ...]) -> ScoringOutcome:
        if not isinstance(rubric, RubricSnapshot):
            raise ValueError("SCORING_RUBRIC_INVALID")
        by_code = {o.criterion_code: o for o in outcomes
                   if isinstance(o, CriterionScore)}
        if len(outcomes) != len(rubric.criteria) or len(by_code) != len(rubric.criteria):
            raise ValueError("SCORING_CRITERIA_MISMATCH")
        expected = {item.criterion_code for item in rubric.criteria}
        if set(by_code) != expected:
            raise ValueError("SCORING_CRITERIA_MISMATCH")
        denominator = sum((Decimal(c.weight) for c in rubric.criteria), Decimal(0))
        if denominator != D100:
            raise ValueError("SCORING_WEIGHT_INVALID")
        assessed_weight = Decimal(0)
        weighted_score = Decimal(0)
        required_missing: list[str] = []
        for criterion in rubric.criteria:
            outcome = by_code[criterion.criterion_code]
            if outcome.status == "assessed":
                if type(outcome.score) is not int or not 0 <= outcome.score <= 5:
                    raise ValueError("SCORING_SCORE_INVALID")
                assessed_weight += Decimal(criterion.weight)
                weighted_score += Decimal(criterion.weight) * Decimal(outcome.score)
            elif outcome.status == "not_assessed":
                if outcome.score is not None or not outcome.reason_code:
                    raise ValueError("SCORING_ABSTENTION_INVALID")
                if criterion.required:
                    required_missing.append(criterion.criterion_code)
            else:
                raise ValueError("SCORING_STATUS_INVALID")
        coverage = assessed_weight / denominator
        if not assessed_weight:
            return ScoringOutcome(
                provisional_score_0_100=None, coverage_fraction=Decimal(0),
                result_status="not_assessed", needs_human_review=True,
                publishable_as_official_score=False,
                rounding_policy="UNAPPROVED_DECIMAL_64_DIGITS",
                required_missing=tuple(required_missing),
                exact_score_ratio=None, exact_coverage_ratio=(0, 100),
            )
        # Exact rational computation via Decimal; NO implicit business rounding.
        # Fraction is preserved as integer ratio; a recurring decimal is NOT exact.\n        numerator = int(D100 * weighted_score)\n        denominator_score = int(D5 * assessed_weight)\n        with localcontext() as ctx:\n            ctx.prec = 64\n            raw = Decimal(numerator) / Decimal(denominator_score)
        # The Stage01 candidate threshold and rounding policy remain OPEN.
        return ScoringOutcome(
            provisional_score_0_100=raw, coverage_fraction=coverage,
            result_status="needs_human_review" if assessed_weight == denominator
                          else "partial",
            needs_human_review=True, publishable_as_official_score=False,
            rounding_policy="UNAPPROVED_DECIMAL_64_DIGITS",
            required_missing=tuple(required_missing),
            exact_score_ratio=(numerator, denominator_score),
            exact_coverage_ratio=(int(assessed_weight), int(denominator)),
        )
