"""Offline Stage 02 documentation verification. Python 3.9+; no third-party packages."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


FILES = (
    "docs/architecture/01_existing_repository_review.md",
    "docs/architecture/02_detailed_design.md",
    "docs/architecture/03_api_and_contracts.md",
    "docs/architecture/04_file_change_matrix.md",
    "docs/architecture/05_architecture_decisions.md",
    "docs/requirements/03_acceptance_criteria.md",
    "docs/requirements/05_open_decisions.md",
)


def indented_json(text: str, heading: str) -> dict:
    section = text.split(heading, 1)[1]
    match = re.search(r"(?m)^    \{\n(?:^    .*\n)*?^    \}", section)
    if match is None:
        raise ValueError("No synthetic indented JSON after " + heading)
    return json.loads("\n".join(line[4:] for line in match.group().splitlines()))


def fenced_json(text: str, heading: str) -> dict:
    section = text.split(heading, 1)[1]
    fence = chr(96) * 3
    match = re.search(re.escape(fence) + r"json\s*\n(.*?)\n" + re.escape(fence),
                      section, re.DOTALL)
    if match is None:
        raise ValueError("No synthetic fenced JSON after " + heading)
    return json.loads(match.group(1))


def check(root: Path) -> tuple[list[tuple[str, bool]], list[str]]:
    results: list[tuple[str, bool]] = []
    notes: list[str] = []
    def record(label: str, passed: bool) -> None:
        results.append((label, bool(passed)))

    missing = [f for f in FILES if not (root / f).is_file()]
    record("required document paths", not missing)
    if missing:
        return results, ["Missing: " + ", ".join(missing)]
    review, design, api, matrix, adrs, criteria, decisions = (
        (root / f).read_text(encoding="utf-8") for f in FILES
    )
    record("four-layer design and DI", all(x in design for x in
           ("Host (", "Application (", "Core/services", "Infrastructure (",
            "@inject", "bootstrap_di")))
    record("uncertainty disclosed", "UNVERIFIABLE" in review and "NOT_VERIFIED" in review)
    record("gate ownership recorded", "STAGE02_GATE_DECOMPOSITION" in adrs
           and "Stage 04" in adrs and "Stage 05" in adrs
           and "NOT_APPROVED" in adrs)
    record("stage tracker preserved", bool(re.search(r"\| 02 \|[^\n]*BLOCKED", decisions))
           and bool(re.search(r"\| 03 \|[^\n]*NOT_STARTED", decisions)))
    record("candidate rubric isolated", "non-production test scope" in api
           and "candidate-0.1" in api and "fail closed" in api)
    record("status fields specified separately", all(x in api for x in
           ("processing_status", "result_status", "needs_human_review")))
    def table_response(route: str) -> str:
        row = next((line for line in api.splitlines()
                    if line.startswith("| " + route + " |")), "")
        cells = row.split("|")
        return cells[3].strip() if len(cells) == 6 else ""

    job_response = table_response("GET /jobs/{job_id}")
    evaluation_response = table_response("GET /evaluations/{evaluation_id}")
    record("canonical job/report DTO field names",
           bool(job_response and evaluation_response)
           and "EvaluationJobStatusDto:" in job_response
           and "processing_status" in job_response
           and re.search(r"\bstatus\b", job_response) is None
           and "EvaluationReportDto:" in evaluation_response
           and "evaluation_type" in evaluation_response
           and re.search(r"\bdomain\b", evaluation_response) is None)
    try:
        report = indented_json(api, "**Synthetic illustration only")
        record("Stage 02 result example", report.get("processing_status") == "completed"
               and report.get("result_status") == "not_assessed"
               and report.get("needs_human_review") is True
               and report.get("final_score_0_100") is None
               and report["criteria"][0]["score"] is None)
    except (IndexError, KeyError, ValueError, TypeError) as exc:
        record("Stage 02 result example", False)
        notes.append(str(exc))
    try:
        report = fenced_json(criteria, "## 5. Synthetic full business-report JSON")
        record("Stage 01 result example", report.get("processing_status") == "completed"
               and report.get("result_status") == "partial"
               and report.get("needs_human_review") is True)
        original = report["source_text"]
        quotes = [e for c in report["criteria"] for e in c.get("evidence", [])
                  if e.get("source_kind") == "original_submission"]
        record("Stage 01 original quote offsets", bool(quotes) and all(
               original[e["start_offset"]:e["end_offset"]] == e["quote"] for e in quotes))
    except (IndexError, KeyError, ValueError, TypeError) as exc:
        record("Stage 01 report and quote offsets", False)
        notes.append(str(exc))
    try:
        span = indented_json(api, "**Synthetic text-span illustration**")
        record("Stage 02 original quote offsets",
               "متن کوتاه"[span["start_offset"]:span["end_offset"]] == span["quote"])
    except (IndexError, KeyError, ValueError, TypeError) as exc:
        record("Stage 02 original quote offsets", False)
        notes.append(str(exc))
    rows = [line for line in matrix.splitlines() if
            line.startswith(("| src/", "| docs/", "| requirements.txt", "| Dockerfile"))]
    record("56-path 10-column future file matrix", len(rows) == 56 and all(
           len(row.split("|")) == 12 for row in rows))
    record("requirement traceability", all(f"FR-{n:02}" in matrix for n in range(1, 13))
           and all(f"NFR-{n:02}" in matrix for n in range(1, 15)))
    record("ADR states", all(s in adrs for s in
           ("CONFIRMED", "PROPOSED", "CANDIDATE", "OPEN", "BLOCKED")))
    docs = [(root / f).read_text(encoding="utf-8") for f in FILES]
    secrets = re.compile(r"-----BEGIN [^-]*PRIVATE KEY-----|ghp_[A-Za-z0-9]{32,}")
    record("high-confidence secret heuristic", all(not secrets.search(s) for s in docs))
    fence = chr(96) * 3
    record("balanced Markdown code fences", all(
           sum(line.startswith(fence) for line in s.splitlines()) % 2 == 0 for s in docs))
    broken = []
    for f in FILES[:5]:
        for url in re.findall(r"\[[^\]]*\]\(([^)]+)\)", (root / f).read_text(encoding="utf-8")):
            if "://" in url or url.startswith("#"):
                continue
            target = ((root / f).parent / url.split("#", 1)[0]).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file():
                broken.append(f + ": " + url)
    record("relative links", not broken)
    notes.extend(broken)
    try:
        proc = subprocess.run(["git", "ls-tree", "-r", "--name-only", "HEAD"],
                              cwd=root, check=True, capture_output=True, text=True, timeout=10)
        tree = set(proc.stdout.splitlines())
        record("Git tracked tree includes five architecture docs",
               all(f in tree for f in FILES[:5]))
        notes.append(f"Git tree entries: {len(tree)}; inspect full tree output separately")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        notes.append("SKIP: Git tree inspection unavailable outside local clone")
    return results, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    results, notes = check(args.repo.resolve())
    print(json.dumps({
        "scope": "Stage 02 documentation only",
        "passed": sum(passed for _, passed in results),
        "total": len(results),
        "checks": [{"check": label, "status": "PASS" if passed else "FAIL"}
                   for label, passed in results],
        "notes": notes
    }, indent=2, ensure_ascii=False))
    return 1 if any(not passed for _, passed in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
