"""Stage 04 Linux supply-chain runner fail-closed preflight and scope checks."""

from pathlib import Path
import subprocess

RUNNER = Path(__file__).resolve().parents[1] / "scripts/verification/run_stage04_linux_supply_chain.sh"


def test_linux_supply_chain_runner_syntax():
    subprocess.run(["bash", "-n", str(RUNNER)], check=True)


def test_linux_supply_chain_runner_limits_shared_host_side_effects():
    source = RUNNER.read_text(encoding="utf-8")
    for required in (
        "git status --porcelain", "git diff --quiet", "docker image inspect",
        "BASE_ID=sha256:", "--pull=false", "--network none", "--network bridge",
        "--read-only", "--cap-drop ALL", "--security-opt no-new-privileges",
        "--user 65532:65532", "--pids-limit", "--memory", "--cpus",
        "--no-deps", "--only-binary=:all:", "--vulnerability-service osv",
        "audit-status", "verify-pypi", "license-template", "REVIEW_REQUIRED",
    ):
        # Some guard messages reference approval, while the real review decision
        # is intentionally left to the authorized reviewer.
        if required == "REVIEW_REQUIRED":
            assert "license approval" in source
        else:
            assert required in source
    for forbidden in ("docker compose", "docker system prune", "docker rm -f", "--network host", "--privileged", "--force", "--publish", "-p 8000:8000"):
        assert forbidden not in source


def test_linux_supply_chain_runner_rejects_dirty_or_wrong_branch_without_docker(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Synthetic Test"], cwd=repo, check=True)
    (repo / "marker.txt").write_text("synthetic", encoding="utf-8")
    subprocess.run(["git", "add", "marker.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "test"], cwd=repo, check=True)

    # This script is not committed in the synthetic repo: its content remains
    # immutable, and its preflight must refuse to touch Docker.
    (repo / "dirty.txt").write_text("dirty", encoding="utf-8")
    run = subprocess.run(["bash", str(RUNNER)], cwd=repo, text=True, capture_output=True, timeout=10)
    assert run.returncode != 0 and "clean main checkout required" in run.stderr
    (repo / "dirty.txt").unlink()

    subprocess.run(["git", "checkout", "-q", "-b", "not-main"], cwd=repo, check=True)
    run = subprocess.run(["bash", str(RUNNER)], cwd=repo, text=True, capture_output=True, timeout=10)
    assert run.returncode != 0 and "clean main checkout required" in run.stderr

    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    run = subprocess.run(["bash", str(RUNNER)], cwd=repo, text=True, capture_output=True, timeout=10)
    assert run.returncode != 0 and "installed application/dependency pins differ" in run.stderr
