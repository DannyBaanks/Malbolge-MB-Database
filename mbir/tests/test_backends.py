from dataclasses import dataclass

import pytest

from mbir.backends import BackendCatalog, BackendResult


@dataclass
class FakeBackend:
    backend_id: str = "fake"

    def execute(self, blob: bytes, stdin: bytes = b"") -> BackendResult:
        return BackendResult(self.backend_id, "OK", blob + stdin, exit_code=0)


def test_catalog_registers_and_dispatches_without_owning_execution():
    catalog = BackendCatalog()
    backend = FakeBackend()
    catalog.register(backend)

    assert catalog.ids() == ("fake",)
    assert catalog.get("fake").execute(b"A", b"B").stdout == b"AB"


def test_catalog_rejects_duplicate_and_unknown_backends():
    catalog = BackendCatalog()
    catalog.register(FakeBackend())
    with pytest.raises(ValueError):
        catalog.register(FakeBackend())
    with pytest.raises(KeyError):
        catalog.get("missing")
