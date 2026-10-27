"""Stage 04 Linux supply-chain runner fail-closed preflight and scope checks."""

from pathlib import Path
import os
import subprocess

RUNNER = Path(__file__).resolve().parents[1] / "scripts/verification/run_stage04_linux_supply_chain.sh"


def test_linux_supply_chain_runner_syntax():
    subprocess.run(["bash", "-n", str(RUNNER)], check=True)


def test_linux_supply_chain_runner_limits_shared_host_side_effects():
    source = RUNNER.read_text(encoding="utf-8")
    for required in (
        "git status --porcelain", "git diff --quiet", "docker image inspect",
        "BASE_ID=sha256:", "docker build --pull=false --network default",
        "docker run --network bridge", "--network none",
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
    """Simulate Git preflight without requiring git in the runtime image.

    The real runner executes on the Git-equipped host; the test container
    intentionally does not install OS Git or expand its supply-chain scope.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    # The Linux test container may mount /tmp with noexec. Source a readable
    # non-executable Bash function instead of executing a stub from /tmp.
    # BASH_ENV is loaded by the non-interactive Bash process running RUNNER.
    git_functions = tmp_path / "git-preflight-functions.bash"
    git_functions.write_text(
        "git() {\n"
        "  case \"$1 $2\" in\n"
        "    \"rev-parse --show-toplevel\") printf '%s\\n' \"$STUB_REPO\" ;;\n"
        "    \"branch --show-current\") printf '%s\\n' \"$STUB_BRANCH\" ;;\n"
        "    \"status --porcelain\") if [ \"$STUB_DIRTY\" = 1 ]; then printf '?? dirty.txt\\n'; fi ;;\n"
        "    \"cat-file -e\") return 1 ;;\n"
        "    *) printf 'unexpected git invocation\\n' >&2; return 2 ;;\n"
        "  esac\n"
        "}\n",
        encoding="utf-8",
    )
    git_functions.chmod(0o400)


    def invoke(*, branch: str, dirty: bool):
        environment = os.environ.copy()
        environment.update({
            "BASH_ENV": str(git_functions),
            "STUB_REPO": str(repo),
            "STUB_BRANCH": branch,
            "STUB_DIRTY": "1" if dirty else "0",
        })
        return subprocess.run(
            ["bash", str(RUNNER)],
            cwd=repo,
            env=environment,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )

    for branch, dirty, expected in (
        ("main", True, "clean main checkout required"),
        ("not-main", False, "clean main checkout required"),
        ("main", False, "installed application/dependency pins differ"),
    ):
        result = invoke(branch=branch, dirty=dirty)
        assert result.returncode != 0
        assert expected in result.stderr
