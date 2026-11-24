#!/usr/bin/env python3
"""Verifica el sub-pack G5b P5b y escribe manifest + hashes."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

PACK = pathlib.Path(__file__).resolve().parent
P5 = PACK.parent / "g5b_flag_return_v5"

SITE = 38058
VAR = 40006
EXPECTED_CONT = [15000, 15004, 15008, 15012, 15016]
EXPECTED_CALLS_POS = [39999, 12130, 21990, 7534, 21990]
EXPECTED_OUTPUT_POS = [98, 230, 110, 230, 110]
EXPECTED_OUTPUT_CTL = [98]
PRESERVED = ("steps", "output_bytes", "peak_position", "writebacks",
             "representation_changes", "state_digest_before", "state_digest_after")


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    pos = json.loads((PACK / "positive.json").read_text())
    ctl = json.loads((PACK / "control.json").read_text())
    old = json.loads((P5 / "rea_summary.json").read_text())

    failures: list[str] = []

    def check(cond: bool, label: str) -> None:
        print(f"  [{'OK ' if cond else 'FAIL'}] {label}")
        if not cond:
            failures.append(label)

    print("== equivalencia de la ventana con la corrida completa ==")
    for name, doc in (("positivo", pos), ("control", ctl)):
        eq = doc["equivalence"]
        check(all(eq.values()), f"{name}: status/pasos/salida/digests idénticos")
        check(doc["window_is_suffix_of_run"],
              f"{name}: la ventana llega hasta el último paso")

    print("== cobertura por eventos (positivo) ==")
    w = pos["windowed"]
    check(w["site_calls"] == 5, f"5 llamadas al sitio (hay {w['site_calls']})")
    check(w["site_values_a"] == EXPECTED_CALLS_POS,
          f"valores a en el sitio = {w['site_values_a']}")
    check(w["site_d_values"] == [VAR], f"d={VAR} en todas las llamadas")
    check(w["continuation_visits"] == EXPECTED_CONT,
          f"retornos = {w['continuation_visits']}")
    check(w["output_bytes"] == EXPECTED_OUTPUT_POS, "salida 62e66ee66e")

    print("== control negativo ==")
    c = ctl["windowed"]
    check(c["site_calls"] == 1, f"1 sola llamada (hay {c['site_calls']})")
    check(c["continuation_visits"] == [15016], "retorno terminal 15016")
    check(c["output_bytes"] == EXPECTED_OUTPUT_CTL, "salida 62")

    print("== el prefijo de 4096 reproduce el NOT_DEMONSTRATED original ==")
    check(pos["baseline_prefix_only"]["site_calls"] == 0, "positivo: 0 llamadas en el prefijo")
    check(ctl["baseline_prefix_only"]["site_calls"] == 0, "control: 0 llamadas en el prefijo")

    print("== preservación de los valores medidos en P5 ==")
    for name, doc, run in (("positivo", pos, old["runs"][0]),
                           ("control", ctl, old["runs"][1])):
        for field in PRESERVED:
            check(doc["windowed"][field] == run[field],
                  f"{name}: {field} sin cambios")

    if failures:
        print(f"\nFALLOS ({len(failures)}):")
        for f in failures:
            print("  -", f)
        return 1

    verification = {
        "schema": "g5b_p5b_verification_v1",
        "result": "PASS",
        "site_event_coverage": "DEMONSTRATED",
        "positive_site_calls": w["site_calls"],
        "positive_continuations": w["continuation_visits"],
        "control_site_calls": c["site_calls"],
        "control_continuations": c["continuation_visits"],
        "p5_values_preserved": True,
        "window_equivalence": True,
        "deterministic": True,
        "gates": {"window_equivalence": "PASS", "site_coverage": "PASS",
                  "continuation_order": "PASS", "negative_control": "PASS",
                  "p5_preservation": "PASS"},
    }
    (PACK / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")

    artifacts = []
    for path in sorted(PACK.rglob("*")):
        if not path.is_file() or path.name in {"manifest.json", "hashes.sha256"}:
            continue
        artifacts.append({"path": path.relative_to(PACK).as_posix(),
                          "bytes": path.stat().st_size,
                          "sha256": sha256(path)})
    (PACK / "manifest.json").write_text(json.dumps({
        "schema": "g5b_p5b_manifest_v1",
        "pack": "G5b P5b — ventana REA tardía",
        "extends": "g5b_flag_return_v5",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }, indent=2) + "\n")

    rows = [f"{sha256(p)}  {p.relative_to(PACK).as_posix()}"
            for p in sorted(PACK.rglob("*"))
            if p.is_file() and p.name != "hashes.sha256"]
    (PACK / "hashes.sha256").write_text("\n".join(rows) + "\n")

    print("\n== PASS: cobertura por eventos REA DEMONSTRATED ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
