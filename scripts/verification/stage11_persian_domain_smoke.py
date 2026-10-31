"""Stage11 bounded synthetic Persian evaluation using the existing on-prem vLLM.

One domain/text per explicit opt-in, at most six sequential criterion POSTs,
no retries, no DB or server configuration changes. Default mode is offline.
Output contains only fixed synthetic input and its generated assessment.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path
from uuid import UUID

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.core.services.text_evaluation.criterion_evaluation_service import (
    CriterionEvaluationService,
)
from src.core.services.text_evaluation.rubric_schema import RubricSnapshot
from src.core.services.text_evaluation.rubric_service import RubricBinding
from src.core.services.text_evaluation.scoring_service import ScoringService
from src.core.services.text_evaluation.text_evaluation_service import TextEvaluationService
from src.core.services.text_evaluation.text_preprocessing_service import (
    TextPreprocessingService,
)
from src.infrastructure.providers.llm.local_llm_provider import (
    LlmProviderError, LocalLlmProvider,
)
from src.infrastructure.security.secrets import SecretResolver
from src.infrastructure.utils.config_reader import ConfigReader, Settings
from scripts.verification.stage11_synthetic_inference_smoke import _query_one_model

_FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "stage06_candidate_rubrics.json"
_MAX_POSTS = 6
_PAUSE_SECONDS = 3.0
_MAX_COMPLETION_TOKENS = 640
_EXAMPLES = {
    "speech": (
        "همکاران گرامی، امروز درباره کاهش مصرف آب صحبت می‌کنیم. "
        "در ماه گذشته مصرف ساختمان ما افزایش یافت و این موضوع هزینه‌ها را بیشتر کرد. "
        "پیشنهاد می‌کنم شیرهای خراب را گزارش کنیم و هنگام شستن دست‌ها آب را بیهوده باز نگذاریم. "
        "اگر هر واحد هر هفته میزان مصرف خود را بررسی کند، می‌توانیم نتیجه این اقدام‌ها را ماه آینده بسنجیم. "
        "بیایید از همین امروز مسئولانه عمل کنیم."
    ),
    "media": (
        "اطلاعیه: برنامه آموزشی نوشتن فارسی روز سه‌شنبه در سالن اجتماعات برگزار می‌شود. "
        "ساعت شروع و روش ثبت‌نام هنوز مشخص نشده است. "
        "همه علاقه‌مندان می‌توانند شرکت کنند. "
        "برگزارکنندگان ادعا می‌کنند این برنامه بهترین دوره سال است، اما معیاری برای این ادعا ارائه نکرده‌اند."
    ),
    "research": (
        "هدف این مطالعه بررسی ارتباط زمان مطالعه با یادگیری واژگان فارسی بود. "
        "پژوهشگران از شرکت‌کنندگان خواستند طی دو هفته روزانه متن کوتاهی بخوانند. "
        "در پایان، نمره آزمون واژگان با نمره آغاز دوره مقایسه شد. "
        "تعداد شرکت‌کنندگان، روش نمونه‌گیری و میزان تغییر نمره‌ها در این چکیده گزارش نشده است. "
        "بنابراین نتیجه‌گیری علّی از این اطلاعات ممکن نیست."
    ),
}


class BoundedProvider:
    """Local test-harness admission guard; never a global vLLM quota."""

    def __init__(self, provider: LocalLlmProvider, *, pause_seconds: float = _PAUSE_SECONDS):
        self._provider = provider
        self._pause_seconds = pause_seconds
        self.calls = 0

    def declared_configuration(self) -> dict[str, object]:
        return self._provider.declared_configuration()

    async def evaluate_async(self, **kwargs):
        if self.calls >= _MAX_POSTS:
            raise LlmProviderError("STAGE11_REQUEST_BUDGET_EXCEEDED")
        if self.calls:
            await asyncio.sleep(self._pause_seconds)
        # Count before invocation, including attempts that fail or time out.
        self.calls += 1
        return await self._provider.evaluate_async(**kwargs)

    async def aclose(self) -> None:
        await self._provider.aclose()


def _local_config(model_id: str) -> ConfigReader:
    """Override disabled application defaults in memory, for this process only."""
    if os.getenv("TES_ENVIRONMENT", "development") != "development":
        raise ValueError("STAGE11_DEV_ONLY")
    if (not isinstance(model_id, str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,127}", model_id) is None
            or ".." in model_id):
        raise ValueError("STAGE11_MODEL_ID_INCOMPATIBLE")
    reader = ConfigReader()
    values = reader.settings.model_dump()
    values["llm"] = {
        "enabled": True,
        "endpoint": "http://127.0.0.1:8000/v1",
        "model_id": model_id,
        "model_revision": "unverified-existing-runtime",
        "credential_ref": None,
        "max_input_characters": 2048,
        "max_context_tokens": 8192,
        "max_output_tokens": _MAX_COMPLETION_TOKENS,
        "timeout_seconds": 45.0,
        "max_concurrency": 1,
        "max_attempts": 1,
        "retry_backoff_seconds": 0.0,
        "circuit_failures": 1,
        "circuit_reset_seconds": 120.0,
        "temperature": 0.0,
        "thinking_mode": "runtime_default",
        "contract_version": "openai-chat-json-schema-v1",
    }
    reader.settings = Settings.model_validate(values)
    return reader


def _rubric(domain: str) -> RubricBinding:
    fixtures = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    snapshot = RubricSnapshot.model_validate(fixtures[domain])
    if len(snapshot.criteria) != 6:
        raise ValueError("STAGE11_RUBRIC_CRITERIA_CHANGED")
    return RubricBinding(
        rubric_version_id=UUID("00000000-0000-4000-8000-000000000011"),
        organization_id="stage11-synthetic-only",
        evaluation_type=domain,
        code=snapshot.code,
        version=snapshot.version,
        checksum=snapshot.fingerprint(),
        snapshot=snapshot,
    )


async def _evaluate(domain: str, provider: BoundedProvider) -> dict:
    source = _EXAMPLES[domain]
    rubric = _rubric(domain)
    engine = TextEvaluationService(
        TextPreprocessingService(),
        CriterionEvaluationService(provider),
        ScoringService(),
    )
    started = time.monotonic()
    try:
        report = await engine.evaluate_async(
            original_text=source, rubric=rubric,
            chunk_char_limit=1024, max_inference_characters=2048,
        )
        return {
            "status": "PASS_SYNTHETIC_DOMAIN_EVALUATION",
            "domain": domain,
            "source_text": source,
            "rubric_version": report.rubric_version,
            "model_revision_verified": False,
            "criteria": [{
                "code": item.criterion_code,
                "name": criterion.name,
                "status": item.status,
                "score_0_5": item.score,
                "reason": item.reason,
                "strengths": list(item.strengths),
                "weaknesses": list(item.weaknesses),
                "recommendations": list(item.recommendations),
                "evidence": [{
                    "quote": quote, "start_offset": start, "end_offset": end,
                } for quote, start, end in item.evidence],
            } for item, criterion in zip(report.criteria, rubric.snapshot.criteria)],
            "summary": {
                "provisional_score_0_100": (
                    str(report.provisional_score_0_100)
                    if report.provisional_score_0_100 is not None else None
                ),
                "coverage": str(report.coverage_fraction),
                "result_status": report.result_status,
                "needs_human_review": report.needs_human_review,
                "official_score": False,
                "strengths": list(dict.fromkeys(
                    point for item in report.criteria for point in item.strengths
                ))[:20],
                "weaknesses": list(dict.fromkeys(
                    point for item in report.criteria for point in item.weaknesses
                ))[:20],
                "recommendations": list(dict.fromkeys(
                    point for item in report.criteria for point in item.recommendations
                ))[:20],
            },
            "elapsed_ms": int((time.monotonic() - started) * 1000),
            "inference_requests_attempted": provider.calls,
            "request_budget": _MAX_POSTS,
            "max_concurrency": 1,
            "retries": 0,
            "stage11_gate": "BLOCKED",
        }
    finally:
        await engine.close_async()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", required=True, choices=tuple(_EXAMPLES))
    parser.add_argument("--execute-approved", action="store_true",
                        help="Opt in to at most six real sequential local model POSTs.")
    args = parser.parse_args(argv)
    if not args.execute_approved:
        print(json.dumps({
            "status": "DRY_RUN_NO_NETWORK",
            "domain": args.domain,
            "source_text": _EXAMPLES[args.domain],
            "criterion_count": 6,
            "max_inference_requests": _MAX_POSTS,
            "max_concurrency": 1,
            "retries": 0,
            "stage11_gate": "BLOCKED",
        }, ensure_ascii=False, indent=2))
        return 0
    if os.getenv("TES_ENVIRONMENT", "development") != "development":
        print(json.dumps({"status": "FAIL_DEV_ONLY"}))
        return 1

    model_id, problem = _query_one_model(port=8000)
    if problem is not None or model_id is None:
        print(json.dumps({"status": "FAIL_MODEL_METADATA_UNVERIFIED"}))
        return 1
    bounded = None
    try:
        bounded = BoundedProvider(LocalLlmProvider(
            _local_config(model_id), SecretResolver(),
        ))
        result = asyncio.run(_evaluate(args.domain, bounded))
    except (LlmProviderError, ValueError, OSError, TimeoutError) as exc:
        # Only fixed error codes from trusted code paths; never raw model content.
        code = str(exc)
        safe = code if re.fullmatch(r"[A-Z][A-Z0-9_]{2,80}", code) else "EVALUATION_FAILED"
        print(json.dumps({
            "status": "FAIL", "error_code": safe,
            "inference_requests_attempted": bounded.calls if bounded else 0,
            "max_inference_requests": _MAX_POSTS,
            "retries": 0,
            "stage11_gate": "BLOCKED",
        }))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
