#!/usr/bin/env python3
"""Manifiesto del pack: hashes de cada fichero, estado de cada puerta y alcance.

No reescribe evidencia previa: solo lee lo que hay en el pack y resume su
estado. El manifiesto se regenera al final; los ficheros que lista conservan
sus hashes (el propio manifiesto se excluye).
"""
import hashlib, json, pathlib, platform, subprocess, sys

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
sha = lambda b: hashlib.sha256(b).hexdigest()


def load(name):
    p = P / name
    return json.loads(p.read_text()) if p.exists() else None


def files():
    out = []
    for p in sorted(P.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(P).as_posix()
        if rel == "manifest.json":
            continue
        b = p.read_bytes()
        out.append({"path": rel, "bytes": len(b), "sha256": sha(b)})
    return out


echo = load("verify_echo.results.json")
cycle = load("eof_cycle.results.json")
syn = load("synthesis.results.json")
alg = load("crazy_algebra.results.json")
bud = load("budget_bound.results.json")
fun = load("reference_functional.results.json")
repro = load("reproduce_check.json")

gates = {
    "G0_imagen_estricta_aceptada": {
        "status": "PASS",
        "evidence": "candidate.mb aceptado por el cargador de 1998 (Olmstead); "
                    "imagen y hash en manifest",
    },
    "G1_instalacion_unica_sin_eco_previo": {
        "status": "PASS",
        "evidence": "verify_echo.results.json (prefijo de instalacion + handoff)",
    },
    "G2_eco_10000_bytes_multimotor": {
        "status": "PASS" if (echo and echo.get("all_checks")) else "NOT_DEMONSTRATED",
        "evidence": "verify_echo.results.json",
    },
    "G3_halt_limpio_en_EOF_bajo_Olmstead": {
        "status": "NOT_DEMONSTRATED",
        "evidence": "verify_echo.results.json (eof_clean) + eof_cycle.results.json "
                    "(ciclo de periodo 180 que emite 0xa8) + crazy_algebra.results.json "
                    "(obstruccion de estabilidad de mascaras) + budget_bound.results.json "
                    "(techo de celdas destino)",
        "why": "el eco funciona pero el IN de EOF devuelve 59048 y el bucle sigue "
               "iterando; la rama EOF exige una cadena CRAZY estable por vuelta "
               "y ninguna de las cadenas medidas lo es",
    },
    "G4_controles_negativos_y_semantica_EOF": {
        "status": "PARTIAL",
        "evidence": "controles de escritura alterada (ctrl_writer_*.mb) y "
                    "reference_functional.results.json (controles de cargador y "
                    "de EOF roto)",
        "why": "los controles del pack cubren la escritura alterada; el matiz de "
               "semantica EOF entre motores queda documentado en el veredicto "
               "pero la rama EOF de la variante relocalizada no existe todavia",
    },
}

claims = [
    {"claim": "la imagen candidata candidate.mb es aceptada por el cargador "
              "estricto de Olmstead",
     "status": "PASS", "evidence": "verify_echo.results.json + manifest"},
    {"claim": "la instalacion relocalizada ocurre en una sola ejecucion nativa, "
              "sin IN/OUT previos",
     "status": "PASS", "evidence": "verify_echo.results.json"},
    {"claim": "10 000 bytes binarios variables se reproducen identicos en varios "
              "motores, una lectura y una escritura por vuelta",
     "status": "PASS", "evidence": "verify_echo.results.json"},
    {"claim": "el eco se detiene en EOF sin bytes adicionales bajo Olmstead "
              "(G3 de la variante relocalizada)",
     "status": "NOT_DEMONSTRATED",
     "evidence": "eof_cycle.results.json: ciclo de periodo 180 que emite 0xa8"},
    {"claim": "existe una imagen unica, aceptada por el cargador de 1998, que "
              "instala el eco binario y se detiene en EOF sin bytes extra "
              "(requisito funcional de UNIECO, referencia ajena a la "
              "relocalizacion)",
     "status": "PASS" if (fun and fun["summary"]["olmstead_echo_exact_all_cases"]
                           and fun["summary"]["loader_control_rejected"]) else "NOT_DEMONSTRATED",
     "evidence": "reference_functional.results.json (6 motores x 5 entradas + "
                 "2 controles negativos)"},
    {"claim": "la orientacion CRAZY del motor es fila=trit de celda, "
              "columna=trit del acumulador",
     "status": "PASS" if (alg and alg["parity_engine"]["mismatches"] == 0)
     else "NOT_DEMONSTRATED",
     "evidence": "crazy_algebra.results.json: 4000 muestras contra el motor "
                 "scratch sin discrepancias"},
    {"claim": "ninguna fila de CRAZY es constante, luego un unico CRAZY no puede "
              "producir un destino independiente del byte",
     "status": "PASS" if (alg and not alg["single_crazy_can_be_byte_independent"])
     else "NOT_DEMONSTRATED",
     "evidence": "crazy_algebra.results.json: imagenes de las tres filas"},
    {"claim": "una cadena CRAZY dentro de un bucle no es estable entre vueltas "
              "(la mascara de la vuelta n+1 es la salida de la vuelta n)",
     "status": "PASS" if (alg and not alg["collapse_chain_in_loop"]
                           ["output_stable_across_rounds"]) else "NOT_DEMONSTRATED",
     "evidence": "crazy_algebra.results.json: la cadena de colapso de 3 pasos "
                 "oscila entre 59048 y 29524 en el flujo medido"},
    {"claim": "el techo de celdas destino de la variante relocalizada con halt "
              "en EOF",
     "status": "PASS" if bud else "NOT_DEMONSTRATED",
     "evidence": "budget_bound.results.json: %d celdas con la region de plan "
                 "actual, %d con la region maxima admisible"
                 % (bud["bounds"]["max_target_cells_current_region"],
                    bud["bounds"]["max_target_cells_max_region"])
     if bud else "-"},
    {"claim": "la verificacion de las puertas es reproducible (re-ejecucion "
              "aislada, campos deterministas identicos)",
     "status": "PASS" if (repro and repro["identical_deterministic_fields"])
     else "NOT_DEMONSTRATED",
     "evidence": "reproduce_check.json"},
]

not_demonstrated = []
if bud:
    not_demonstrated.extend(bud["not_demonstrated"])
not_demonstrated.extend([
    "que la variante relocalizada candidate.mb se detenga en EOF: G3 sigue "
    "abierto y no se afirma lo contrario",
    "un cuerpo compacto con deteccion de EOF por debajo del techo medido de "
    "%d celdas destino" % bud["bounds"]["max_target_cells_max_region"]
    if bud else "un cuerpo compacto con deteccion de EOF dentro del techo medido",
    "que el planificador de BolgeForge pueda sintetizar la tabla de despacho de "
    "256 entradas: solo se midio su coste en ops",
])

report = {
    "pack": "unieco_strict_relocation_v1",
    "purpose": "instalar el bucle compacto IN/DLOAD/OUT en memoria alta y "
               "cerrar el eco binario con halt limpio en EOF",
    "generated_by": "make_manifest.py",
    "environment": {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "repo": "MALBOLGE-MB-DATABASE (repo hermano; el pack vive en vm_malbolge/evidence/)",
        "git_head": subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                   capture_output=True, text=True).stdout.strip(),
    },
    "gates": gates,
    "claims": claims,
    "not_demonstrated": not_demonstrated,
    "scope": (
        "Este pack demuestra la instalacion relocalizada del bucle compacto y su "
        "eco binario exacto en 10 000 bytes (G0, G1, G2), y demuestra por separado "
        "el requisito funcional de UNIECO (imagen unica, cargador de 1998, eco "
        "binario, halt limpio en EOF sin bytes extra) sobre una imagen de "
        "referencia construida en otro pack. NO demuestra que la variante "
        "relocalizada tenga deteccion de EOF: G3 sigue abierto."),
    "construction_separation": (
        "candidate.mb (bucle compacto de 150 celdas relocalizado) y "
        "reference_cat_functional.mb (referencia PureEpoch de 7972 celdas) son "
        "construcciones distintas; no hay composicion de codigo demostrada entre "
        "ellas y no se afirma ninguna."),
    "key_numbers": {
        "candidate_bytes": len((P / "candidate.mb").read_bytes())
        if (P / "candidate.mb").exists() else None,
        "plan_length_ops": syn["plan_length"] if syn else None,
        "target_cells": syn["target_cells"] if syn else None,
        "ops_per_target_cell": bud["measured"]["ops_per_target_cell"] if bud else None,
        "max_target_cells_current_region":
            bud["bounds"]["max_target_cells_current_region"] if bud else None,
        "max_target_cells_max_region":
            bud["bounds"]["max_target_cells_max_region"] if bud else None,
        "eof_cycle_period": cycle["repeat"]["period"] if cycle else None,
        "eof_cycle_all_output_a8": cycle.get("all_output_a8") if cycle else None,
        "eof_cycle_output_bytes": cycle.get("output_len") if cycle else None,
    },
    "files": files(),
}

(P / "manifest.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
print(json.dumps({"files": len(report["files"]),
                  "gates": {k: v["status"] for k, v in gates.items()},
                  "claims": {i: c["status"] for i, c in enumerate(claims)}},
                 indent=2, sort_keys=True))
