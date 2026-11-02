"""Stage11 isolated-development configuration preflight; NO DB, HTTP or inference.

Requires explicit opt-in external Settings and a loopback-only isolated test DB.
Validates static runtime wiring and local secret references without starting
API/Worker, opening sockets, performing migrations or contacting the model.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from src.host.evaluation_worker import _load_worker_policy
from src.infrastructure.context.sql_db.psql_dbcontext import get_test_database_url
from src.infrastructure.providers.llm.local_llm_provider import LocalLlmProvider
from src.infrastructure.security.encrypted_content import EncryptedContentService
from src.infrastructure.security.secrets import SecretResolver
from src.infrastructure.utils.config_reader import ConfigReader


def verify_isolated_configuration() -> dict[str, object]:
    """Return safe evidence only; never return a DSN, key, model ID or URL."""
    if os.environ.get("TES_ENVIRONMENT", "development") != "development":
        raise ValueError("STAGE11_PREFLIGHT_DEV_ONLY")
    if not os.environ.get("TES_STAGE11_SETTINGS_FILE"):
        raise ValueError("STAGE11_PREFLIGHT_PRIVATE_SETTINGS_REQUIRED")

    config = ConfigReader()
    settings = config.settings
    if not (settings.http_security.enabled and settings.worker.enabled
            and settings.llm.enabled and settings.security.deny_external_egress):
        raise ValueError("STAGE11_PREFLIGHT_COMPONENT_DISABLED")

    # Validates a loopback async PostgreSQL test DSN and the tes_stage05_ prefix.
    # No database connection or migration occurs.
    get_test_database_url()

    org_id, policy = _load_worker_policy(config)
    if not org_id or policy.max_inflight != 1:
        raise ValueError("STAGE11_PREFLIGHT_WORKER_POLICY_INVALID")

    # The real provider validator applies the literal-private-IP/loopback policy
    # without opening a connection. Do not infer actual model availability.
    secret_resolver = SecretResolver()
    provider = LocalLlmProvider(config, secret_resolver)
    provider.declared_configuration()
    endpoint = urlsplit(settings.llm.endpoint)
    if (endpoint.port is None or endpoint.port == settings.server.port
            or settings.llm.max_concurrency != 1
            or settings.llm.max_attempts != 1):
        raise ValueError("STAGE11_PREFLIGHT_INFERENCE_POLICY_INVALID")

    auth = settings.http_security
    if (not auth.issuer or not auth.audience or not auth.key_id
            or not auth.public_key_ref or not auth.encryption_key_ref
            or not auth.max_request_bytes or not auth.max_text_characters
            or not auth.max_active_jobs or not auth.max_requests_per_minute):
        raise ValueError("STAGE11_PREFLIGHT_HTTP_POLICY_INVALID")

    try:
        public = load_pem_public_key(
            secret_resolver.resolve_reference(auth.public_key_ref).encode("utf-8")
        )
        if not isinstance(public, RSAPublicKey):
            raise ValueError("STAGE11_PREFLIGHT_PUBLIC_KEY_INVALID")
        # Existing encryption checks actual base64/32-byte key and AEAD path.
        ciphertext = EncryptedContentService(config, secret_resolver).encrypt(
            value="synthetic-preflight-only", organization_id=org_id,
            owner_id="synthetic-preflight", resource_id=__import__("uuid").uuid4(),
            kind="original",
        )
        if len(ciphertext) < 30:
            raise ValueError("STAGE11_PREFLIGHT_ENCRYPTION_INVALID")
        if settings.llm.credential_ref:
            token = secret_resolver.resolve_reference(settings.llm.credential_ref)
            if not token.strip() or "\n" in token or "\r" in token:
                raise ValueError("STAGE11_PREFLIGHT_MODEL_CREDENTIAL_INVALID")
    except (ValueError, TypeError):
        raise ValueError("STAGE11_PREFLIGHT_SECRET_INVALID") from None

    return {
        "status": "CONFIG_VALIDATED_NO_NETWORK",
        "environment": "development",
        "database": "ISOLATED_DSN_FORMAT_ONLY",
        "http": "SIGNED_JWT_AND_ENCRYPTION_CONFIGURED",
        "worker": "SINGLE_INFLIGHT_POLICY_CONFIGURED",
        "inference": "LOCAL_ENDPOINT_FORMAT_ONLY",
        "network_calls": 0,
        "inference_requests": 0,
        "migrations": 0,
        "gate": "PENDING_SERVER",
    }


def main() -> int:
    try:
        result = verify_isolated_configuration()
    except Exception:
        # No exception details: errors may include private configuration values.
        print(json.dumps({"status": "PREFLIGHT_FAILED",
                          "error_code": "STAGE11_ISOLATED_CONFIG_INVALID",
                          "network_calls": 0}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
