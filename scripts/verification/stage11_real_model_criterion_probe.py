"""Stage11 opt-in, low-load real local-vLLM criterion smoke test.

Runs one *unforced* candidate rubric criterion in each domain, sequentially.
It never touches PostgreSQL, Docker, shared service lifecycle, or real data.
No prompts, evidence quotes, model explanations or secret values are printed.
This is NOT a model quality benchmark, no-egress proof or release gate.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
import json
import os
from pathlib import Path
import time

from src.core.services.text_evaluation.criterion_evaluation_service import (
    CriterionEvaluationService,
)
from src.core.services.text_evaluation.rubric_schema import RubricSnapshot
from src.infrastructure.providers.llm.local_llm_provider import (
    LlmProviderError, LocalLlmProvider,
)
from src.infrastructure.security.secrets import SecretResolver
from scripts.verification.stage11_vllm_diagnostics import (
    DiagnosticLocalLlmProvider, UnconstrainedDiagnosticLocalLlmProvider,
    metrics_delta, read_metrics,
)
from src.infrastructure.utils.config_reader import ConfigReader

_ROOT = Path(__file__).resolve().parents[2]
_RUBRICS = _ROOT / "tests/fixtures/stage06_candidate_rubrics.json"
_ENDPOINT = "http://127.0.0.1:8000/v1"
_MODEL_ID = "shared-llm"
_ALLOWED_ERRORS = frozenset({
    "LLM_NOT_CONFIGURED", "LLM_CONFIG_INVALID", "LLM_CONFIG_INCOMPLETE",
    "LLM_ENDPOINT_DENIED", "LLM_MODEL_UNAVAILABLE", "LLM_HTTP_REJECTED",
    "LLM_TRANSIENT_HTTP", "LLM_RETRY_EXHAUSTED", "LLM_CIRCUIT_OPEN",
    "LLM_ADMISSION_TIMEOUT", "LLM_SCHEMA_REJECTED", "LLM_INVALID_RESPONSE",
    "LLM_RESPONSE_TOO_LARGE", "LLM_INCOMPLETE_GENERATION",
    "LLM_INPUT_REJECTED", "LLM_PROVIDER_CLOSED", "LLM_REDIRECT_DENIED",
})


@dataclass(frozen=True)
class SyntheticCase:
    domain: str
    criterion_code: str
    original_text: str


CASES = (
    SyntheticCase(
        "speech", "speech_clarity",
        "دوستان عزیز، امروز درباره اهمیت مطالعه صحبت می‌کنم. "
        "مطالعه به ما کمک می‌کند واژه‌های تازه یاد بگیریم. "
        "در پایان پیشنهاد می‌کنم هر روز ده دقیقه کتاب بخوانیم.",
    ),
    SyntheticCase(
        "media", "media_message_clarity",
        "امروز کتابخانه فرضی محله برنامه امانت کتاب برای کودکان را آغاز کرد. "
        "بر اساس اطلاعیه ساختگی این آزمایش، ثبت‌نام از فردا انجام می‌شود. "
        "این خبر فقط یک نمونه آزمایشی است و رویداد واقعی نیست.",
    ),
    SyntheticCase(
        "research", "research_academic_writing",
        "هدف این مطالعه فرضی بررسی رابطه زمان مطالعه و یادآوری واژه‌هاست. "
        "در یک تمرین ساختگی، دو گروه با زمان‌های مطالعه متفاوت مقایسه شدند. "
        "این متن فاقد داده واقعی و نتیجه قابل تعمیم است.",
    ),
)


def _load_selected_rubrics() -> tuple[tuple[SyntheticCase, object, str], ...]:
    raw = json.loads(_RUBRICS.read_text(encoding="utf-8"))
    selected = []
    for case in CASES:
        snapshot = RubricSnapshot.model_validate(raw[case.domain])
        matches = [
            criterion for criterion in snapshot.criteria
            if criterion.criterion_code == case.criterion_code
        ]
        if (len(matches) != 1 or snapshot.evaluation_type != case.domain
                or len(case.original_text) > 2048
                or len(case.original_text) < 32):
            raise ValueError("STAGE11_SYNTHETIC_CASE_INVALID")
        selected.append((case, matches[0], snapshot.fingerprint()))
    return tuple(selected)


def _require_safe_environment() -> None:
    if (os.getenv("TES_ENVIRONMENT", "development") != "development"
            or any(os.environ.get(key) for key in (
                "TES_STAGE11_SETTINGS_FILE",
                "TES_STAGE05_DATABASE_URL",
                "TES_STAGE11_PROCESS_E2E",
            ))):
        raise ValueError("STAGE11_PROBE_ENVIRONMENT_REFUSED")


async def _run_cases(evaluator: CriterionEvaluationService, *, domain: str | None = None) -> dict:
    cases = tuple(x for x in _load_selected_rubrics() if domain is None or x[0].domain == domain)
    if not cases:
        raise ValueError("STAGE11_PROBE_DOMAIN_INVALID")
    details = []
    circuit_opened = False
    for case, criterion, checksum in cases:
        start = time.perf_counter()
        try:
            outcome = await evaluator.evaluate_criterion_async(
                criterion=criterion, original_text=case.original_text,
                rubric_checksum=checksum,
            )
            if (outcome.criterion_code != case.criterion_code
                    or outcome.status not in ("assessed", "not_assessed")
                    or (outcome.status == "assessed" and (
                        type(outcome.score) is not int
                        or not 0 <= outcome.score <= 5
                        or not outcome.evidence))
                    or (outcome.status == "not_assessed" and (
                        outcome.score is not None or outcome.evidence))):
                raise ValueError("STAGE11_MODEL_CONTRACT_INVALID")
            for quote, begin, end in outcome.evidence:
                if (type(begin) is not int or type(end) is not int
                        or not 0 <= begin < end <= len(case.original_text)
                        or case.original_text[begin:end] != quote):
                    raise ValueError("STAGE11_EVIDENCE_MISMATCH")
            details.append({
                "domain": case.domain, "criterion_code": case.criterion_code,
                "contract": "valid", "status": outcome.status,
                "score": outcome.score,
                "evidence_count": len(outcome.evidence),
                "duration_ms": round((time.perf_counter() - start) * 1000),
            })
        except Exception as exc:
            # Strict allowlist: never print upstream exception, model text, or URL.
            code = str(exc) if isinstance(exc, LlmProviderError) else ""
            error = {
                "domain": case.domain, "criterion_code": case.criterion_code,
                "contract": "failed", "error_code": (
                    code if code in _ALLOWED_ERRORS else "STAGE11_MODEL_PROBE_FAILED"
                ),
                "duration_ms": round((time.perf_counter() - start) * 1000),
            }
            if isinstance(exc, LlmProviderError) and code in (
                "LLM_CIRCUIT_OPEN", "LLM_RETRY_EXHAUSTED",
            ):
                allowed_kinds = {
                    "REQUEST_TIMEOUT", "TRANSPORT_ERROR", "HTTP_429",
                    "HTTP_500", "HTTP_502", "HTTP_503", "HTTP_504",
                }
                error["failure_kind"] = (
                    exc.failure_kind if exc.failure_kind in allowed_kinds
                    else "UNAVAILABLE"
                )
            details.append(error)
            if code == "LLM_CIRCUIT_OPEN":
                # Do not attempt remaining criteria when the circuit is open.
                circuit_opened = True
                break
    return {
        "status": ("REAL_MODEL_THREE_DOMAIN_CONTRACT_PASS"
                   if all(row["contract"] == "valid" for row in details)
                   else "REAL_MODEL_THREE_DOMAIN_CONTRACT_PARTIAL_FAILURE"),
        "model_api_id": _MODEL_ID,
        "model_revision_verified": False,
        "requests_planned": len(cases),
        # Counts Python criterion attempts, not proven upstream HTTP calls.
        "requests_attempted": len(details),
        "requests_not_attempted": len(cases) - len(details),
        "stopped_after_circuit_open": circuit_opened,
        "max_concurrent_requests": 1,
        "retries": 0,
        "synthetic_only": True,
        "official_score": False,
        "quality_benchmark": False,
        "results": details,
    }


async def _run_live(
    *, domain: str | None = None, disable_thinking: bool = False,
    diagnostics: bool = False, max_output_tokens: int = 512,
    comparison_unconstrained: bool = False,
) -> dict:
    if (diagnostics and domain is None
            or max_output_tokens not in (256, 512)
            or (max_output_tokens != 512 and not diagnostics)
            or (comparison_unconstrained and (
                not diagnostics or domain != "media" or max_output_tokens != 256
                or not disable_thinking))):
        raise ValueError("STAGE11_DIAGNOSTICS_SCOPE_INVALID")
    _require_safe_environment()
    config = ConfigReader()
    if not config.settings.security.deny_external_egress:
        raise ValueError("STAGE11_PROBE_CONFIG_INVALID")
    llm_settings = config.settings.llm.__class__.model_validate({
        "enabled": True,
        "endpoint": _ENDPOINT,
        "model_id": _MODEL_ID,
        # A declared placeholder, explicitly NOT a proven model revision.
        "model_revision": "unverified",
        "max_input_characters": 2048, "max_context_tokens": 8192,
        "max_output_tokens": max_output_tokens, "timeout_seconds": 45,
        "max_concurrency": 1, "max_attempts": 1,
        "retry_backoff_seconds": 0, "circuit_failures": 1,
        "circuit_reset_seconds": 10, "temperature": 0,
        "thinking_mode": "disabled" if disable_thinking else "runtime_default",
    })
    config.settings = config.settings.model_copy(update={"llm": llm_settings})
    before = await read_metrics() if diagnostics else None
    provider = (
        UnconstrainedDiagnosticLocalLlmProvider(config, SecretResolver())
        if comparison_unconstrained
        else DiagnosticLocalLlmProvider(config, SecretResolver())
        if diagnostics else LocalLlmProvider(config, SecretResolver())
    )
    evaluator = CriterionEvaluationService(provider)
    try:
        report = await _run_cases(evaluator, domain=domain)
    finally:
        try:
            after = await read_metrics() if diagnostics else None
        finally:
            await evaluator.close_async()
    report["thinking_mode_requested"] = llm_settings.thinking_mode
    if diagnostics:
        status, deltas = metrics_delta(before, after)
        report["diagnostics"] = {
            "max_output_tokens": max_output_tokens,
            "decoding_mode": (
                "unconstrained" if comparison_unconstrained else "json_schema"
            ),
            "response": provider.response_diagnostic or {
                "finish_reason": "UNAVAILABLE",
                "json_syntax": "UNAVAILABLE",
                "reported_usage": None,
            },
            "metrics_status": status,
            "shared_metrics_delta": deltas,
            "metrics_attribution": "SHARED_SERVICE_UNATTRIBUTED",
        }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-live", action="store_true",
                        help="Make exactly three sequential synthetic requests to the shared local vLLM.")
    parser.add_argument("--domain", choices=("speech", "media", "research"),
                        help="Use only one selected rubric criterion during diagnosis.")
    parser.add_argument("--disable-thinking", action="store_true",
                        help="Opt-in Qwen3 non-thinking mode for one selected domain.")
    parser.add_argument("--diagnostics", action="store_true",
                        help="Collect only sanitized response and bounded shared metrics.")
    parser.add_argument("--max-output-tokens", type=int, choices=(256, 512),
                        default=512, help="Opt-in reduced cap only with diagnostics.")
    args = parser.parse_args(argv)
    if args.disable_thinking and args.domain is None:
        parser.error("--disable-thinking requires --domain")
    if args.diagnostics and args.domain is None:
        parser.error("--diagnostics requires --domain")
    if args.max_output_tokens != 512 and not args.diagnostics:
        parser.error("reduced --max-output-tokens requires --diagnostics")
    if not args.execute_live:
        try:
            choices = tuple(x for x in _load_selected_rubrics()
                            if args.domain is None or x[0].domain == args.domain)
            print(json.dumps({
                "status": "DRY_RUN_NO_NETWORK",
                "model_api_id": _MODEL_ID,
                "requests_planned": len(choices),
                "criteria": [item[0].criterion_code for item in choices],
                "requires": "--execute-live",
                "diagnostics_requested": args.diagnostics,
                "max_output_tokens": args.max_output_tokens,
                "thinking_mode_requested": (
                    "disabled" if args.disable_thinking else "runtime_default"
                ),
            }, sort_keys=True))
            return 0
        except Exception:
            print(json.dumps({"status": "STAGE11_PROBE_PREPARATION_FAILED"}))
            return 2
    try:
        results = asyncio.run(_run_live(
            domain=args.domain, disable_thinking=args.disable_thinking,
            diagnostics=args.diagnostics, max_output_tokens=args.max_output_tokens,
        ))
        print(json.dumps(results, ensure_ascii=False, sort_keys=True))
        return 0 if results["status"] == "REAL_MODEL_THREE_DOMAIN_CONTRACT_PASS" else 2
    except Exception:
        print(json.dumps({
            "status": "STAGE11_PROBE_ABORTED",
            "error_code": "STAGE11_SAFE_RUNTIME_REQUIRED",
        }))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
