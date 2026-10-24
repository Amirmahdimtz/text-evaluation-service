"""Secret references resolve only from injected runtime environment variables."""

import os
import re

from src.infrastructure.di.inject import inject


@inject
class SecretResolver:
    __di_singleton__ = True

    def resolve_reference(self, reference: str) -> str:
        if not isinstance(reference, str) or re.fullmatch(r"env://[A-Z][A-Z0-9_]{0,127}", reference) is None:
            raise ValueError("SECRET_REFERENCE_INVALID")
        value = os.environ.get(reference[6:])
        if not value:
            raise ValueError("SECRET_UNAVAILABLE")
        return value
