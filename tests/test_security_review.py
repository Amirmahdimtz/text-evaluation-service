"""Stage 04 regression tests for findings from independent security review."""
import io
import json
import logging

import pytest
from src.infrastructure.security.policy import Identity, ResourceScope, is_allowed, validate_internal_endpoint
from src.infrastructure.security.safe_logging import configure_logging


def test_privileged_permissions_fail_closed_without_resource_or_tenant_scope():
    admin = Identity("admin", "org-one", frozenset({"rubric:manage", "metrics:read"}), True)
    local = ResourceScope("rubric-01", "other-user", "org-one")
    foreign = ResourceScope("rubric-02", "other-user", "org-two")
    empty = ResourceScope("rubric-03", "other-user", "")
    for action in ("rubric:manage", "metrics:read"):
        assert not is_allowed(admin, action)
        assert not is_allowed(admin, action, foreign)
        assert not is_allowed(admin, action, empty)
        assert is_allowed(admin, action, local)


@pytest.mark.parametrize("url", [
    "https://10.1.2.3:443/\r\nHost: attacker.example",
    "https://10.1.2.3:443/\nexample",
    "https://10.1.2.3:443\\@outside.example",
    " https://10.1.2.3:443",
    "https://10.1.2.3:443/#fragment",
])
def test_endpoint_rejects_control_and_ambiguous_characters(url):
    with pytest.raises(ValueError, match="^ENDPOINT_NOT_ALLOWED$"):
        validate_internal_endpoint(url, environment="production")


def test_logging_cannot_leak_through_preexisting_handler():
    target = logging.getLogger("text_evaluation_service")
    previous = list(target.handlers)
    previous_level, previous_propagate = target.level, target.propagate
    stream = io.StringIO()
    unsafe = logging.StreamHandler(stream)
    unsafe.setFormatter(logging.Formatter("%(message)s %(exc_text)s"))
    try:
        for handler in previous:
            target.removeHandler(handler)
        target.addHandler(unsafe)
        logger = configure_logging()
        try:
            raise RuntimeError("synthetic-credential-never-log")
        except RuntimeError:
            logger.exception("raw private text synthetic-credential-never-log")
        payload = stream.getvalue()
        assert "synthetic-credential-never-log" not in payload
        assert "raw private text" not in payload
        assert json.loads(payload)["event_code"] == "UNCLASSIFIED_EVENT"
    finally:
        target.removeHandler(unsafe)
        for handler in previous:
            target.addHandler(handler)
        target.setLevel(previous_level)
        target.propagate = previous_propagate
