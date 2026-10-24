"""Deterministic fail-closed provider discovery in the source tree."""

from importlib import import_module
from inspect import getmembers, isclass
from pathlib import Path

from src.infrastructure.di.inject import DependencyError, register

_EXCLUDED = frozenset({"di", "dtos", "models", "scripts", "alembic", "versions", "res", "sso", "__pycache__"})
_SRC_ROOT = Path(__file__).resolve().parents[2]


def bootstrap_packages() -> None:
    for package in ("infrastructure", "core", "application"):
        folder = _SRC_ROOT / package
        if not folder.is_dir():
            continue
        modules = sorted(p for p in folder.rglob("*.py") if not any(part in _EXCLUDED for part in p.relative_to(folder).parts))
        for path in modules:
            module_name = "src." + ".".join(path.relative_to(_SRC_ROOT).with_suffix("").parts)
            try:
                module = import_module(module_name)
            except Exception:
                # Import errors must never silently hide security providers.
                raise DependencyError("DI_MODULE_IMPORT_FAILED") from None
            for _, cls in getmembers(module, isclass):
                if cls.__module__ == module_name and cls.__dict__.get("__di_inject__", False):
                    register(cls)
