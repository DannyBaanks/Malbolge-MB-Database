"""Backend-neutral MBIR execution boundary.

This module deliberately provides a registry and result envelope, not a VM.
Concrete adapters may invoke a local interpreter, a native Malbolge runner, or
another compatible substrate without becoming part of the MBIR contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BackendResult:
    """Normalized result returned by an MBIR backend adapter."""

    backend_id: str
    status: str
    stdout: bytes = b""
    stderr: bytes = b""
    exit_code: int | None = None


class BackendAdapter(Protocol):
    """Minimum adapter surface; execution semantics stay backend-owned."""

    backend_id: str

    def execute(self, blob: bytes, stdin: bytes = b"") -> BackendResult:
        ...


class BackendCatalog:
    """Explicit, in-process catalog of available backend adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, BackendAdapter] = {}

    def register(self, adapter: BackendAdapter) -> None:
        backend_id = adapter.backend_id
        if not backend_id or backend_id in self._adapters:
            raise ValueError("backend_id must be non-empty and unique")
        self._adapters[backend_id] = adapter

    def get(self, backend_id: str) -> BackendAdapter:
        try:
            return self._adapters[backend_id]
        except KeyError as exc:
            raise KeyError("unknown MBIR backend: %s" % backend_id) from exc

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))
