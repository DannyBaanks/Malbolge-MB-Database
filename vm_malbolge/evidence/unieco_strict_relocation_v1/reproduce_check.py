#!/usr/bin/env python3
"""Compara la verificacion almacenada con una re-ejecucion aislada.

Uso: python3 reproduce_check.py <fresh_verify_echo.results.json>

La re-ejecucion se hace en una copia del pack fuera del repositorio (con
enlaces simbolicos al resto del arbol) para no reescribir la evidencia previa.
Se comparan solo los campos deterministas; la captura acotada del proceso
Olmstead depende del reloj (cuantos bytes post-EOF se capturaron antes del
limite de 15 s) y se declara aparte.
"""
import hashlib, json, pathlib, sys

P = pathlib.Path(__file__).resolve().parent
stored = json.loads((P / "verify_echo.results.json").read_text())
fresh = json.loads(pathlib.Path(sys.argv[1]).read_text())


def pick(d, *keys):
    out = {}
    for k in keys:
        v = d
        for part in k.split("."):
            v = v[part]
        out[k] = v
    return out


deterministic = [
    "cap", "stream_sha256", "expected_output_sha256",
    "trace.status", "trace.steps", "trace.input_consumed", "trace.output_bytes",
    "trace.rounds", "trace.d_starts", "trace.jmp_destinations", "trace.pre_io",
    "trace.memory_sha256", "trace.registers",
    "engines.scratch.status", "engines.scratch.steps", "engines.scratch.memory_sha256",
    "engines.independent.status", "engines.independent.steps",
    "engines.independent.memory_sha256",
    "engines.oracle.status", "engines.oracle.steps",
    "engines.runner.output_sha256",
    "control.status", "control.steps", "control.rounds", "control.output_bytes",
    "control.output_sha256", "control.mutated_pc",
    "checks", "all_checks", "eof_clean",
]

a = pick(stored, *deterministic)
b = pick(fresh, *deterministic)
diffs = {k: {"stored": a[k], "fresh": b[k]} for k in deterministic if a[k] != b[k]}

timing = {
    "field": "olmstead_bounded",
    "stored": {k: stored["olmstead_bounded"][k]
               for k in ("stdout_bytes", "prefix_equal", "post_eof_bytes_first16",
                         "terminated_by_harness", "returncode")},
    "fresh": {k: fresh["olmstead_bounded"][k]
              for k in ("stdout_bytes", "prefix_equal", "post_eof_bytes_first16",
                        "terminated_by_harness", "returncode")},
    "note": ("la longitud de la captura post-EOF depende del reloj; el prefijo "
             "igual a la entrada, la presencia de bytes post-EOF y el estado "
             "HALTED/terminado si son deterministas"),
}

report = {
    "purpose": "reproducibilidad de las puertas G0-G2 y del ciclo EOF",
    "method": ("re-ejecucion de verify_echo.py en una copia del pack fuera del "
               "repositorio; la evidencia almacenada no se modifica"),
    "compared_fields": deterministic,
    "identical_deterministic_fields": not diffs,
    "differences": diffs,
    "timing_dependent": timing,
    "verdict": ("reproducible" if not diffs else "NO reproducible en los campos listados"),
}
(P / "reproduce_check.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
sys.exit(0 if not diffs else 1)
