"""AES-256-GCM authenticated encryption; raw text never stored or logged."""
from __future__ import annotations

import base64
import os
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.infrastructure.di.inject import inject
from src.infrastructure.security.secrets import SecretResolver
from src.infrastructure.utils.config_reader import ConfigReader


@inject
class EncryptedContentService:
    def __init__(self, config_reader: ConfigReader, secret_resolver: SecretResolver):
        self._config = config_reader
        self._secrets = secret_resolver

    def _key(self) -> bytes:
        auth = self._config.settings.http_security
        if not auth.enabled or not auth.encryption_key_ref or not auth.key_id:
            raise ValueError("ENCRYPTION_UNAVAILABLE")
        try:
            raw = base64.b64decode(
                self._secrets.resolve_reference(auth.encryption_key_ref),
                validate=True,
            )
        except (ValueError, TypeError):
            raise ValueError("ENCRYPTION_UNAVAILABLE") from None
        if len(raw) != 32:
            raise ValueError("ENCRYPTION_UNAVAILABLE")
        return raw

    def encrypt(self, *, value: str, organization_id: str,
                owner_id: str, resource_id: UUID, kind: str) -> bytes:
        if (not isinstance(value, str) or not value or not organization_id
                or not owner_id or not isinstance(resource_id, UUID)
                or kind not in ("original", "feedback", "criterion")):
            raise ValueError("ENCRYPTION_INPUT_INVALID")
        aad = self._aad(organization_id, owner_id, resource_id, kind)
        nonce = os.urandom(12)
        try:
            return b"\x01" + nonce + AESGCM(self._key()).encrypt(
                nonce, value.encode("utf-8"), aad,
            )
        except UnicodeError:
            raise ValueError("ENCRYPTION_INPUT_INVALID") from None

    def decrypt(self, *, ciphertext: bytes, organization_id: str,
                owner_id: str, resource_id: UUID, kind: str) -> str:
        if not isinstance(ciphertext, bytes) or len(ciphertext) < 30 or ciphertext[:1] != b"\x01":
            raise ValueError("ENCRYPTION_INTEGRITY_FAILED")
        try:
            plain = AESGCM(self._key()).decrypt(
                ciphertext[1:13], ciphertext[13:],
                self._aad(organization_id, owner_id, resource_id, kind),
            )
            return plain.decode("utf-8")
        except Exception:
            raise ValueError("ENCRYPTION_INTEGRITY_FAILED") from None

    @staticmethod
    def _aad(org: str, owner: str, resource_id: UUID, kind: str) -> bytes:
        if (not isinstance(org, str) or not org or not isinstance(owner, str)
                or not owner or not isinstance(resource_id, UUID)
                or kind not in ("original", "feedback", "criterion")):
            raise ValueError("ENCRYPTION_SCOPE_INVALID")
        return (f"tes:v1:{kind}:{org}:{owner}:{resource_id}").encode("utf-8")
