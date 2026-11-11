#!/usr/bin/env python3
"""Adición 2026-11-11 (auditoría de epoch_xlat2_phase_census_v1): modelo de ventana relajado.

GATES.md del censo exige L celdas CONSECUTIVAS. Aquí se quita esa condición: las L celdas
de la operación X pueden estar separadas, y los huecos se llenan con celdas de relleno que
son inocuas en todas las vueltas (NOP u opcode no válido en todos los valores de su ciclo).
Sólo calcula; no construye ni ejecuta ninguna imagen.
Uso: python3 -I relaxed_window_check.py
"""
X2 = ("5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X"
      "~xDl}REokN:#?G\"i@")
ENC = {33 + i: ord(c) for i, c in enumerate(X2)}
VALID = {4, 5, 23, 39, 40, 62, 68, 81}
HARMLESS = (set(range(94)) - VALID) | {68}
TARGETS = {"OUT": 5, "IN": 23, "ROT": 39, "DLOAD": 40, "CRAZY": 62}

seen, cycles = set(), []
for v in range(33, 127):
    if v in seen:
        continue
    c, x = [], v
    while x not in seen:
        seen.add(x); c.append(x); x = ENC[x]
    cycles.append(c)


def ops(c, s):
    return {(v + s) % 94 for v in c}


filler = [r for r in range(94) if any(ops(c, r) <= HARMLESS for c in cycles)]
print("ciclos:", sorted(len(c) for c in cycles))
print("residuos con relleno inocuo:", len(filler), "/ 94")
for name, X in TARGETS.items():
    best = None
    for c in cycles:
        L = len(c)
        G = [s for s in range(94) if X in ops(c, s) and ops(c, s) - {X} <= HARMLESS]
        for start in G:
            pos, ok = [start], True
            while len(pos) < L:
                nxt = pos[-1] + 1
                while nxt % 94 not in G:
                    nxt += 1
                if any(q % 94 not in filler for q in range(pos[-1] + 1, nxt)):
                    ok = False
                    break
                pos.append(nxt)
            if ok:
                span = pos[-1] - pos[0] + 1
                if best is None or (span, L) < (best[1], best[0]):
                    best = (L, span, [p % 94 for p in pos])
    print(name, "-> bloque mínimo: ciclo L=%s, %s celdas, residuos de las celdas X=%s"
          % best if best else "-> sin bloque")
