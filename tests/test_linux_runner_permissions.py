"""Ensure temporary Linux test images expose check inputs to the non-root runner."""

from pathlib import Path


def test_runner_security_guard_inputs_are_visible_to_non_root():
    script = (Path(__file__).resolve().parents[1] / 'scripts/verification/run_stage04_linux_container_tests.sh').read_text(encoding='utf-8')
    allowed = '.gitignore requirements.txt requirements-dev.txt scripts tests'
    names = '/app/.gitignore /app/requirements.txt /app/requirements-dev.txt'
    assert f'git archive HEAD {allowed} |' in script
    assert 'COPY .gitignore requirements.txt requirements-dev.txt ./' in script
    assert f'chgrp 65532 {names}' in script
    assert f'chmod 0640 {names}' in script
    assert script.index(f'chmod 0640 {names}') < script.index('USER 65532:65532')
    assert '--network none' in script
    assert '--read-only' in script
    assert '--user 65532:65532' in script
    assert 'chmod 777' not in script
