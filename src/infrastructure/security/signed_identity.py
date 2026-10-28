"""Offline RS256 identity verification; never trust X-User/X-Org headers."""
from __future__ import annotations

import re

import jwt
from jwt.exceptions import PyJWTError

from src.infrastructure.di.inject import inject
from src.infrastructure.security.policy import Identity
from src.infrastructure.security.secrets import SecretResolver
from src.infrastructure.utils.config_reader import ConfigReader

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}$")
_ALLOWED = frozenset({
    "evaluation:submit", "evaluation:read", "feedback:create", "rubric:manage",
})


class AuthenticationError(ValueError):
    pass


@inject
class SignedIdentityVerifier:
    def __init__(self, config_reader: ConfigReader, secret_resolver: SecretResolver):
        self._config = config_reader
        self._secrets = secret_resolver

    def verify(self, bearer: str) -> Identity:
        settings = self._config.settings.http_security
        if not settings.enabled or not settings.issuer or not settings.audience or not settings.public_key_ref:
            raise AuthenticationError("AUTH_NOT_CONFIGURED")
        if not isinstance(bearer, str) or len(bearer) > 8192:
            raise AuthenticationError("AUTH_INVALID")
        try:
            public_pem = self._secrets.resolve_reference(settings.public_key_ref)
            claims = jwt.decode(
                bearer, public_pem, algorithms=["RS256"],
                audience=settings.audience, issuer=settings.issuer,
                options={"require": ["sub", "org", "iss", "aud", "iat", "nbf", "exp", "jti"]},
                leeway=0,
            )
            user = claims["sub"]
            org = claims["org"]
            jti = claims["jti"]
            permissions = claims.get("permissions")
            assigned = claims.get("assigned_resource_ids", [])
            if (not isinstance(user, str) or not _ID.fullmatch(user)
                    or not isinstance(org, str) or not _ID.fullmatch(org)
                    or not isinstance(jti, str) or not _ID.fullmatch(jti)
                    or type(claims["iat"]) is not int or type(claims["nbf"]) is not int
                    or type(claims["exp"]) is not int
                    or not isinstance(permissions, list) or len(permissions) > 16
                    or any(type(p) is not str or p not in _ALLOWED for p in permissions)
                    or len(set(permissions)) != len(permissions)
                    or not isinstance(assigned, list) or len(assigned) > 100
                    or any(not isinstance(v, str) or not re.fullmatch(
                        r"[0-9a-fA-F]{8}-[0-9a-fA-F-]{28,36}", v,
                    ) for v in assigned)):
                raise AuthenticationError("AUTH_INVALID")
            return Identity(
                user_id=user, organization_id=org, is_authenticated=True,
                permissions=frozenset(permissions),
                assigned_resource_ids=frozenset(assigned),
            )
        except (PyJWTError, ValueError, KeyError, TypeError):
            raise AuthenticationError("AUTH_INVALID") from None
