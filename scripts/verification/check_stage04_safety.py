"""Fail-closed static guardrails for the Stage 04-only runtime."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = frozenset({"requests", "httpx", "aiohttp", "urllib.request", "huggingface_hub", "boto3", "subprocess"})
SECRET_PATTERNS = (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
                   re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[^\s'\"]+"))


def _pinned_versions(path: Path) -> dict[str, str]:
    pins = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line == "-r requirements.txt":
            continue
        if not re.fullmatch(r"[A-Za-z0-9_.-]+==[0-9][A-Za-z0-9_.+-]*", line):
            raise SystemExit(f"FAIL: unpinned dependency in {path.name}")
        package, version = line.split("==", 1)
        pins[package.lower().replace("_", "-")] = version
    return pins


def main() -> int:
    files = sorted((ROOT / "src").rglob("*.py"))
    if not files:
        raise SystemExit("FAIL: Missing application source")
    for path in files:
        contents = path.read_text(encoding="utf-8")
        tree = ast.parse(contents, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(name in FORBIDDEN or name.split(".")[0] in FORBIDDEN for name in names):
                raise SystemExit(f"FAIL: unapproved network/command dependency in {path.relative_to(ROOT)}")
        if any(p.search(contents) for p in SECRET_PATTERNS):
            raise SystemExit(f"FAIL: suspicious credential in {path.relative_to(ROOT)}")
    runtime = _pinned_versions(ROOT / "requirements.txt")
    dev = _pinned_versions(ROOT / "requirements-dev.txt")
    try:
        starlette = tuple(int(x) for x in runtime["starlette"].split("."))
    except (KeyError, ValueError):
        raise SystemExit("FAIL: explicit patched Starlette pin required") from None
    if starlette < (1, 3, 1):
        raise SystemExit("FAIL: known vulnerable Starlette version (CVE-2026-54283)")
    if "fastapi" not in runtime:
        raise SystemExit("FAIL: missing FastAPI pin")
    try:
        pytest_version = tuple(int(x) for x in dev["pytest"].split("."))
    except (KeyError, ValueError):
        raise SystemExit("FAIL: patched pytest pin required") from None
    if pytest_version < (9, 0, 3):
        raise SystemExit("FAIL: known vulnerable pytest version (CVE-2025-71176)")
    patterns = (ROOT / ".gitignore").read_text(encoding="utf-8")
    if not all(item in patterns for item in (".env", "*.key", "*.pem", "*.log")):
        raise SystemExit("FAIL: .gitignore missing essential secret protections")
    print(f"PASS: {len(files)} runtime source files; dependency pins; patched Starlette baseline; credential patterns; ignored secrets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
