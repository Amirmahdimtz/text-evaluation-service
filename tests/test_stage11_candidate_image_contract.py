"""Stage11 image candidate contract checks: offline text-only, no Docker actions."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "Dockerfile.stage11-candidate"


def _instructions() -> list[str]:
    content = IMAGE.read_text(encoding="utf-8")
    return [
        line.lstrip() for line in content.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def test_candidate_image_requires_nonroot_and_restricted_copy():
    content = IMAGE.read_text(encoding="utf-8")
    instructions = _instructions()
    assert "FROM python:3.12.12-slim-bookworm" in instructions
    assert "COPY requirements.txt ./requirements.txt" in instructions
    assert "COPY src/ ./src/" in instructions
    assert "USER 10001:10001" in instructions
    assert 'ENTRYPOINT ["python", "-m", "src.host.app"]' in instructions
    assert "PYTHONDONTWRITEBYTECODE=1" in content
    assert "--only-binary=:all:" in content
    assert "python -m pip check" in content
    assert not any(line.startswith(("COPY . ", "ADD ", "EXPOSE "))
                   for line in instructions)


def test_candidate_image_has_no_production_enablement_or_sensitive_files():
    instructions = _instructions()
    assert all(not x.startswith(("RUN curl", "RUN wget", "ARG ", "VOLUME "))
               for x in instructions)
    full = "\n".join(instructions)
    assert not any(
        name in full for name in (
            "COPY .env", "COPY secrets", "COPY *.pem",
            "COPY models", "COPY data/", "TES_STAGE11_SETTINGS_FILE=",
            "TES_STAGE05_DATABASE_URL=", "TES_ENVIRONMENT=production",
        )
    )
    assert "worker.enabled=true" not in full.lower()
    assert "llm.enabled=true" not in full.lower()
