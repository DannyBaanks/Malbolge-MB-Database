"""Small bridge from Python process exits into the MBIR result envelope."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .backends import BackendResult


def run_with_exit_hook(
    callback: Callable[..., Any], *args: Any, **kwargs: Any
) -> BackendResult:
    """Run ``callback`` without letting ``sys.exit`` escape the adapter.

    This is intentionally a local wrapper, not a global monkey-patch of
    ``sys.exit``. Normal returns become ``RETURNED``; ``SystemExit`` becomes
    ``EXIT`` with its conventional integer exit code.
    """
    try:
        value = callback(*args, **kwargs)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        return BackendResult("python-exit-hook", "EXIT", exit_code=code)
    return BackendResult("python-exit-hook", "RETURNED", exit_code=0,
                         stdout=b"" if value is None else str(value).encode())
