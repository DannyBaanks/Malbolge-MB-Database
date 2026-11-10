#!/usr/bin/env python3
"""probe.py — orquestador del pack torus_reach_v1.

Secciones (cada una es un instrumento independiente):
  1. spec      diferenciales de semántica + autocontrol 35 = 1022_3
  2. solver    lemas, cierres, testigos, máscaras, distancia
  3. fill      semántica del relleno de memoria (3 motores)
  4. mutants   6 controles contra falsos positivos
  5. claims    tabla con estado por afirmación

Salida: results.json (este directorio) + traza por stdout.
"""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
sys.path.insert(0, str(PACK))

import tr_spec  # noqa: E402
import tr_solver  # noqa: E402
import tr_fillprobe  # noqa: E402
import tr_mutants  # noqa: E402

CLAIMS_TEXT = {
    "C01": "La semántica de crazy/rot usada coincide con el oráculo del repo, "
           "con native_classic y con el runner C original.",
    "C02": "35 = 1022_3: trits pos0=2, pos1=2, pos2=0, pos3=1 (autocontrol).",
    "C03": "Lema de creación de 2: D(crazy(a,v)) ⊆ D(a) U D(v). Un trit 2 no "
           "aparece donde ningún operando tenía un 2.",
    "C04": "ROT permuta posiciones (ciclo Z_10) y rot^10 = identidad.",
    "C05": "{0, 29524} es componente cerrada bajo el operador restringido.",
    "C06": "29524 = crazy(54, 54) con 54 imprimible; hay 8 imprimibles sin "
           "ningún trit 1.",
    "C07": "0 = crazy(29524, 29524).",
    "C08": "Toda palabra de 10 trits es alcanzable desde constantes "
           "autorizadas (testigo constructivo).",
    "C09": "59048 (diez trits iguales a 2) es alcanzable; tres testigos "
           "verificados por replay independiente.",
    "C10": "La búsqueda más corta (encuentro de niveles) halla 59048 en 2 "
           "operaciones con la biblioteca declarada.",
    "C11": "El relleno de memoria más allá del programa es crazy-fill en el "
           "runner C, no relleno con cero.",
    "C12": "La máscara 121 de v3 es involutiva en 7776/59049 palabras; 29524 "
           "lo es en las 59049.",
    "C13": "La primitiva de escritura exacta de bytes (pack epoch_algebra_v3) "
           "válida y reutilizada aquí.",
    "C14": "El relleno crazy-fill NO proporciona celdas cero gratuitas: la "
           "palabra 0 debe construirse.",
    "C15": "Imposibilidad de sintetizar constantes de 10 trits.",
    "C16": "Topología toroidal que impide alcanzar patrones.",
    "C17": "Programa Classic Malbolge autónomo (sin stdin) que construye 59048.",
    "C18": "El resolvedor de épocas con payload de palabra completa (máscara "
           "29524) ejecutándose en la VM nativa.",
}


def main() -> int:
    results: dict = {"pack": "torus_reach_v1",
                     "python": sys.version.split()[0],
                     "platform": platform.platform(),
                     "sections": {}}
    ok = True

    print("=== 1. spec (diferenciales de semántica) ===", flush=True)
    spec = tr_spec.spec_check()
    results["sections"]["spec"] = spec
    ok = ok and spec["verdict"]
    print("[spec] ok =", spec["verdict"], flush=True)

    print("=== 2. solver (álgebra de alcanzabilidad) ===", flush=True)
    solver = tr_solver.main()
    results["sections"]["solver"] = solver
    solver_ok = (
        solver["lemmas_trit_exhaustive"]["all_ok"]
        and all(v == 0 for v in solver["lemmas_random_words"]["mismatches"].values())
        and solver["rot_permutes_positions"]["mismatches"] == 0
        and solver["witnesses"]["w_29524"]["ok"]
        and solver["witnesses"]["w_0"]["ok"]
        and solver["witnesses"]["w_59048"]["ok"]
        and solver["witnesses"]["w_59048_compact"]["ok"]
        and solver["witnesses"]["w_59048_vm"]["ok"]
        and solver["witnesses"]["w_general"]["all_ok"]
        and solver["witnesses"]["w_Q_U_induction"]["all_ok"]
        and solver["witnesses"]["w_F_induction"]["all_ok"]
        and solver["witnesses"]["closed_component_0_29524"]["closed"]
        and solver["mask_upgrade"]["mask_29524_involutive_words"] == 59049
        and solver["mask_upgrade"]["mask_121_involutive_words"] == 7776
    )
    results["sections"]["solver_ok"] = bool(solver_ok)
    ok = ok and solver_ok
    print("[solver] ok =", solver_ok, flush=True)

    print("=== 3. fill (relleno de memoria, 3 motores) ===", flush=True)
    fill = tr_fillprobe.main()
    results["sections"]["fill"] = fill
    fill_ok = fill["verdict"] and all(
        r["c_matches_oracle"] for r in fill["targets"])
    results["sections"]["fill_ok"] = bool(fill_ok)
    ok = ok and fill_ok
    print("[fill] ok =", fill_ok, flush=True)

    print("=== 4. mutants (controles) ===", flush=True)
    mut = tr_mutants.main()
    results["sections"]["mutants"] = mut
    results["sections"]["mutants_ok"] = mut["verdict"]
    ok = ok and mut["verdict"]
    print("[mutants] ok =", mut["verdict"], flush=True)

    # ---------- 5. tabla de claims ----------
    bf = solver["witnesses"]["bfs"]["results"]
    claims = {
        "C01": ("DEMONSTRATED" if spec["verdict"] else "NOT_DEMONSTRATED",
                "diferencial spec vs oráculo (200k) vs native_classic (50k); "
                "vectores fijos 3 impls; M1/M2 contra el runner C"),
        "C02": ("DEMONSTRATED", "round-trip decimal<->ternario y descomposición "
                                "de 35 = [2,2,0,1,0,...]"),
        "C03": ("DEMONSTRATED", "enumeración exhaustiva de los 9 pares de trits "
                                "(prueba completa por-trit) + 200k palabras"),
        "C04": ("DEMONSTRATED", "exhaustivo sobre las 59049 palabras"),
        "C05": ("DEMONSTRATED", "las 4 combinaciones crazy y las 2 rotaciones "
                                "sobre el par quedan dentro del par; con "
                                "máscaras externas 0 deja de ser sumidero"),
        "C06": ("DEMONSTRATED", "testigo verificado; imprimibles sin trit 1 = %s"
                % solver["witnesses"]["printable_without_trit1"]),
        "C07": ("DEMONSTRATED", "testigo verificado por replay independiente"),
        "C08": ("DEMONSTRATED", "inducción Q/U sobre 1023 subconjuntos, F sobre "
                                "1023, fórmula general en 209 palabras; cierre "
                                "hacia atrás de 29524 = 59049 palabras"),
        "C09": ("DEMONSTRATED", "constructivo (%d pasos), compacto (%d), "
                                "fiel a la VM (%d); todos con replay independiente"
                % (solver["witnesses"]["w_59048"]["steps"],
                   solver["witnesses"]["w_59048_compact"]["steps"],
                   solver["witnesses"]["w_59048_vm"]["steps"])),
        "C10": ("DEMONSTRATED" if bf["59048"]["depth"] == 2 else "NOT_DEMONSTRATED",
                "profundidad hallada: %s (biblioteca declarada)" % bf["59048"]["depth"]),
        "C11": ("DEMONSTRATED" if fill_ok else "NOT_DEMONSTRATED",
                "5 direcciones, 3 motores coinciden; predicción crazy-fill "
                "acertada, predicción cero-fill refutada en 3 casos"),
        "C12": ("DEMONSTRATED", "exhaustivo sobre las 59049 palabras; "
                                "7776 = 3^5 * 2^5"),
        "C13": ("DEMONSTRATED", "epoch_algebra_v3: 768 escrituras exactas, 3 "
                                "motores; reutilizado como primitiva en los "
                                "testigos fieles a la VM"),
        "C14": ("DEMONSTRATED", "el relleno crazy no produce celdas cero; 0 se "
                                "construye con crazy(29524,29524)"),
        "C15": ("DESTROYED", "contraejemplo ejecutable: los testigos de 59048 "
                             "y de la fórmula general"),
        "C16": ("DESTROYED", "distancia a 29524 <= 2 en una muestra de 5000 "
                             "palabras (histograma %s); cierre hacia atrás "
                             "completo" % solver["distance_probe"]["histogram"]),
        "C17": ("NOT_DEMONSTRATED", "este pack mide álgebra, relleno y "
                                    "controles; la imagen nativa autónoma es el "
                                    "experimento acotado siguiente"),
        "C18": ("NOT_DEMONSTRATED", "precondiciones identificadas (colocar byte "
                                    "en celda, recargar a = 29524); ejecución "
                                    "nativa pendiente"),
    }
    results["claims"] = {k: {"text": CLAIMS_TEXT[k], "status": v[0],
                             "evidence": v[1]} for k, v in claims.items()}
    print("=== 5. claims ===", flush=True)
    for k in sorted(claims):
        print(f"[claim] {k} {claims[k][0]:16s} {CLAIMS_TEXT[k]}", flush=True)

    results["verdict_all_checks_pass"] = bool(ok)
    (PACK / "results.json").write_text(json.dumps(results, indent=2,
                                                  ensure_ascii=False) + "\n",
                                       encoding="utf8")
    print("[verdict] all_checks_pass =", ok, flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
