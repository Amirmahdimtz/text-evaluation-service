"""Idempotent thread-safe composition bootstrap."""

from threading import RLock

from src.infrastructure.di.inject import mark_ready
from src.infrastructure.di.reflection import bootstrap_packages

_lock = RLock()
_bootstrapped = False


def bootstrap_di() -> None:
    global _bootstrapped
    with _lock:
        if _bootstrapped:
            return
        bootstrap_packages()
        mark_ready()
        _bootstrapped = True


def reset_bootstrap_for_tests() -> None:
    global _bootstrapped
    from src.infrastructure.di.inject import reset_for_tests
    with _lock:
        reset_for_tests()
        _bootstrapped = False
