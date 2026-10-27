"""Stage06 schema and deterministic identity tests (no PostgreSQL required)."""
from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.core.services.text_evaluation.rubric_schema import (
    RubricSnapshot, validated_persisted_snapshot,
)
from src.core.services.text_evaluation.rubric_service import RubricService
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.di.inject import resolve

FIXTURES = Path(__file__).resolve().parent / "fixtures/stage06_candidate_rubrics.json"


@pytest.fixture
def raw_candidates():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


@pytest.mark.parametrize("domain", ["speech", "media", "research"])
def test_stage06_three_proposed_domains_have_all_anchors_and_weights(raw_candidates, domain):
    candidate = RubricSnapshot.model_validate(raw_candidates[domain])
    assert candidate.approval_status == "PROPOSED"
    assert candidate.version == "candidate-0.1"
    assert len(candidate.criteria) == 6
    assert sum(c.weight for c in candidate.criteria) == 100
    assert all(set(c.scoring_anchors) == set("012345") for c in candidate.criteria)
    assert all(c.evidence_requirements and c.applicability_rules for c in candidate.criteria)
    assert len(candidate.fingerprint()) == 64
    assert RubricSnapshot.model_validate(candidate.canonical_dict()) == candidate


@pytest.mark.parametrize("change", [
    lambda d: d["criteria"][0].update(weight=99),
    lambda d: d["criteria"][1].update(criterion_code=d["criteria"][0]["criterion_code"]),
    lambda d: d["criteria"][0].update(criterion_code="media_wrong"),
    lambda d: d["criteria"][0]["scoring_anchors"].pop("5"),
    lambda d: d["criteria"][0]["scoring_anchors"].update({"6": "out of range"}),
    lambda d: d["criteria"][0].update(weight=True),
    lambda d: d["criteria"][0].update(required="true"),
    lambda d: d["criteria"][0].update(evaluation_instructions=""),
    lambda d: d.update(version="official-1.0"),
    lambda d: d.update(approval_status="APPROVED"),
    lambda d: d.update(coverage_policy={"status": "APPROVED"}),
    lambda d: d["criteria"].pop(),
    lambda d: d.update(surprise_field="unexpected"),
])
def test_stage06_invalid_candidates_fail_closed(raw_candidates, change):
    data = copy.deepcopy(raw_candidates["speech"])
    change(data)
    with pytest.raises(ValidationError):
        RubricSnapshot.model_validate(data)


def test_stage06_canonical_hash_independent_of_json_key_order(raw_candidates):
    data = raw_candidates["speech"]
    original = RubricSnapshot.model_validate(data)
    reversed_json = json.loads(json.dumps(data, ensure_ascii=False, sort_keys=True))
    assert original.fingerprint() == RubricSnapshot.model_validate(reversed_json).fingerprint()
    changed = copy.deepcopy(data)
    changed["criteria"][0]["scoring_anchors"]["3"] += " modified"
    assert original.fingerprint() != RubricSnapshot.model_validate(changed).fingerprint()


def test_stage06_rejects_wrong_status_checksum_and_scope_on_persisted_snapshot(raw_candidates):
    candidate = RubricSnapshot.model_validate(raw_candidates["research"])
    record = SimpleNamespace(
        id=uuid4(), organization_id="fixture-org", evaluation_type="research",
        code=candidate.code, version=candidate.version, status="published",
        criteria_snapshot=candidate.canonical_dict(), checksum=candidate.fingerprint(),
    )
    assert validated_persisted_snapshot(record) == candidate
    record.status = "draft"
    with pytest.raises(ValueError, match="RUBRIC_NOT_PUBLISHED"):
        validated_persisted_snapshot(record)
    record.status = "published"
    record.checksum = "0" * 64
    with pytest.raises(ValueError, match="RUBRIC_SNAPSHOT_INTEGRITY"):
        validated_persisted_snapshot(record)


def test_stage06_auto_discovery_resolves_service_without_database_connection():
    bootstrap_di()
    instance = resolve(RubricService)
    assert isinstance(instance, RubricService)


def test_stage06_service_resolves_only_exact_published_integrity_checked_version(raw_candidates):
    candidate = RubricSnapshot.model_validate(raw_candidates["media"])
    row = SimpleNamespace(
        id=uuid4(), organization_id="synthetic-org", evaluation_type="media",
        code=candidate.code, version=candidate.version, status="published",
        criteria_snapshot=candidate.canonical_dict(), checksum=candidate.fingerprint(),
    )
    class FakeRepository:
        async def get_published_async(self, **kwargs):
            if kwargs["organization_id"] == row.organization_id and kwargs["code"] == row.code:
                if kwargs["version"] is None or kwargs["version"] == row.version:
                    return row
            return None

    service = RubricService(FakeRepository())
    async def exercise():
        resolved = await service.resolve_published_async(
            organization_id="synthetic-org", evaluation_type="media",
            code=candidate.code, version=candidate.version,
        )
        assert resolved.rubric_version_id == row.id
        assert resolved.checksum == candidate.fingerprint()
        assert resolved.snapshot == candidate
        with pytest.raises(ValueError, match="RUBRIC_PUBLISHED_VERSION_NOT_FOUND"):
            await service.resolve_published_async(
                organization_id="other-org", evaluation_type="media",
                code=candidate.code, version=candidate.version,
            )
        with pytest.raises(ValueError, match="RUBRIC_PUBLISHED_VERSION_NOT_FOUND"):
            await service.resolve_published_async(
                organization_id="synthetic-org", evaluation_type="media",
                code=candidate.code, version="candidate-99.0",
            )
    asyncio.run(exercise())
