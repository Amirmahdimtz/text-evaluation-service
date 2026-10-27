"""Compatibility imports; single SQLAlchemy metadata source is text_evaluation.py.

The old alternative draft contained plaintext text columns and non-scoped
foreign keys. No migration for that draft was ever applied. All callers must
use the canonical reviewed models below.
"""
from src.infrastructure.models.text_evaluation import (
    AuditEvent, CriterionResult, Evaluation, EvaluationFeedback, EvaluationJob, RubricVersion,
)
__all__ = ("AuditEvent", "CriterionResult", "Evaluation", "EvaluationFeedback", "EvaluationJob", "RubricVersion")
