"""Constructor dependency injection; provider discovery performs registration."""

from __future__ import annotations

from contextvars import ContextVar
from functools import wraps
from inspect import signature
from threading import RLock
from typing import get_type_hints


class DependencyError(RuntimeError):
    """A sanitized dependency configuration/creation failure."""


_registry: dict[type, type] = {}
_singletons: dict[type, object] = {}
_lock = RLock()
_resolution_path: ContextVar[tuple[type, ...]] = ContextVar("di_path", default=())
_ready = False


def inject(cls: type) -> type:
    """Mark a class as injectable and fill required typed constructor parameters."""
    original = cls.__init__
    init_signature = signature(original)
    cls.__di_inject__ = True

    @wraps(original)
    def init(self: object, *args: object, **kwargs: object) -> None:
        bound = init_signature.bind_partial(self, *args, **kwargs)
        try:
            hints = get_type_hints(original, localns={cls.__name__: cls})
        except (NameError, TypeError) as exc:
            raise DependencyError("DI_INVALID_ANNOTATION") from None
        for name, param in list(init_signature.parameters.items())[1:]:
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD) or name in bound.arguments or param.default is not param.empty:
                continue
            dep = hints.get(name)
            if not isinstance(dep, type):
                raise DependencyError("DI_INVALID_ANNOTATION")
            bound.arguments[name] = resolve(dep)
        original(*bound.args, **bound.kwargs)

    cls.__init__ = init
    return cls


def register(cls: type) -> None:
    if not getattr(cls, "__di_inject__", False):
        raise DependencyError("DI_UNMARKED_PROVIDER")
    with _lock:
        if cls in _registry and _registry[cls] is not cls:
            raise DependencyError("DI_DUPLICATE_PROVIDER")
        _registry[cls] = cls


def mark_ready() -> None:
    global _ready
    with _lock:
        _ready = True


def resolve(dependency: type) -> object:
    with _lock:
        if not _ready:
            raise DependencyError("DI_NOT_BOOTSTRAPPED")
        implementation = _registry.get(dependency)
        if implementation is None:
            raise DependencyError("DI_UNKNOWN_PROVIDER")
        path = _resolution_path.get()
        if implementation in path:
            raise DependencyError("DI_CIRCULAR_DEPENDENCY")
        if implementation.__dict__.get("__di_singleton__", False) and implementation in _singletons:
            return _singletons[implementation]
        token = _resolution_path.set((*path, implementation))
        try:
            instance = implementation()
            if implementation.__dict__.get("__di_singleton__", False):
                _singletons[implementation] = instance
            return instance
        finally:
            _resolution_path.reset(token)


def reset_for_tests() -> None:
    """Clear DI state between isolated tests; never invoke from application code."""
    global _ready
    with _lock:
        _registry.clear()
        _singletons.clear()
        _ready = False
