"""Strict, non-interpolating configuration and environment validation."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from src.infrastructure.di.inject import inject

_CONFIG_DIR = Path(__file__).resolve().parents[2] / "host" / "res"


class _StrictSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _App(_StrictSettings):
    name: str = Field(min_length=1, max_length=80)
    version: str = Field(min_length=1, max_length=40)


class _Server(_StrictSettings):
    host: str
    port: int = Field(ge=1, le=65535)

    @field_validator("host")
    @classmethod
    def check_host(cls, value: str) -> str:
        if value != "127.0.0.1":
            raise ValueError("server binds only to loopback before deployment approval")
        return value


class _Api(_StrictSettings):
    prefix: str

    @field_validator("prefix")
    @classmethod
    def check_prefix(cls, value: str) -> str:
        if not value.startswith("/") or value == "/" or value.endswith("/") or "//" in value or not value.replace("/", "").replace("_", "").isalnum():
            raise ValueError("invalid API prefix")
        return value


class _Security(_StrictSettings):
    deny_external_egress: bool

    @field_validator("deny_external_egress")
    @classmethod
    def check_egress(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("external egress must be denied")
        return value


class Settings(_StrictSettings):
    app: _App
    server: _Server
    api: _Api
    security: _Security


@inject
class ConfigReader:
    __di_singleton__ = True

    def __init__(self) -> None:
        env = os.getenv("TES_ENVIRONMENT", "development")
        if env not in ("development", "staging", "production"):
            raise ValueError("CONFIG_INVALID_ENVIRONMENT")
        self.environment = env
        filename = "appsettings.development.yaml" if env == "development" else "appsettings.yaml"
        try:
            data = yaml.safe_load((_CONFIG_DIR / filename).read_text(encoding="utf-8"))
            self.settings = Settings.model_validate(data)
        except (OSError, yaml.YAMLError, ValidationError, TypeError):
            raise ValueError("CONFIG_INVALID") from None

    def get(self, path: str) -> object:
        current: object = self.settings.model_dump()
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                raise KeyError("CONFIG_KEY_UNKNOWN")
            current = current[key]
        return current

    def get_api_prefix(self) -> str:
        return self.settings.api.prefix
