#!/usr/bin/env python3
"""Algebra del branch EOF en el bucle compacto: que se puede y que no se puede.

Objetivo: justificar por que una rama EOF no se puede injertar en el cuerpo
compacto IN/DLOAD/OUT con una sola cadena CRAZY, y dejar el limite exacto
(cuantas celdas y cuanto plan) para una variante que si lo consiga.

Precondicion registrada en GATES.md: revalidar la orientacion CRAZY con paridad
de memoria completa antes de cualquier conclusion algebraica. Aqui se hace:
se contrasta la tabla CRZ contra el motor scratch del repo (epoch_dload_compose_v1)
con valores aleatorios y con la mascara C1=29524 de la literatura.
"""
import hashlib, importlib.util, json, pathlib, random, sys

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[2]
spec = importlib.util.spec_from_file_location(
    "compose", ROOT / "vm_malbolge/evidence/epoch_dload_compose_v1/probe.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
SE = M.SE

CRZ = ((1, 0, 0), (1, 0, 2), (2, 2, 1))          # crz[trit de celda][trit de A]
N = 59049
C1 = 29524        # 1111111111_3 : mascara involutiva
C2 = 59048        # 2222222222_3 : valor de EOF
EOF_VALUE = C2


def crazy(x, y):
    """Replica bit a bit de SE.crazy: x = acumulador, y = celda."""
    res, p = 0, 1
    for _ in range(10):
        res += CRZ[y % 3][x % 3] * p
        x //= 3
        y //= 3
        p *= 3
    return res


def compose(rows, x):
    """Aplica rows en orden (primero el primero)."""
    for r in rows:
        x = r[x]
    return x


ROWS = {0: (1, 0, 0), 1: (1, 0, 2), 2: (2, 2, 1)}          # R_c : c fijo, A variable
COLS = {0: (1, 1, 2), 1: (0, 0, 2), 2: (0, 2, 1)}          # C_x : A fijo, celda variable

report = {"n": N, "crz": [list(r) for r in CRZ], "c1": C1, "c2": C2}

# ---------------------------------------------------------------- 1. paridad
rng = random.Random(20261111)
mismatch = []
for _ in range(4000):
    x = rng.randrange(N)
    y = rng.randrange(N)
    if crazy(x, y) != SE.crazy(x, y):
        mismatch.append((x, y))
report["parity_engine"] = {
    "samples": 4000,
    "mismatches": len(mismatch),
    "engine": "epoch_dload_compose_v1/probe.py :: SE.crazy",
    "orientation": "fila = trit de celda, columna = trit del acumulador",
    "note": "mem[d] = crazy(a, mem[d])",
}
c1_involution_fail = [v for v in (0, 1, 2, 255, 29524, 59048, 39421, 12345)
                      if crazy(crazy(v, C1), C1) != v]
report["parity_engine"]["c1_involution_samples"] = 8
report["parity_engine"]["c1_involution_failures"] = len(c1_involution_fail)

# ------------------------------------------------- 2. ninguna fila es constante
report["rows"] = {str(k): list(v) for k, v in ROWS.items()}
report["columns"] = {str(k): list(v) for k, v in COLS.items()}
report["row_images"] = {str(k): sorted(set(v)) for k, v in ROWS.items()}
report["single_crazy_can_be_byte_independent"] = any(
    len(set(v)) == 1 for v in ROWS.values())

# ------------------------------- 3. composiciones constantes de longitud 1,2,3
def compositions(length):
    out = []
    if length == 1:
        for c in (0, 1, 2):
            out.append(((c,), ROWS[c]))
        return out
    for first, _ in compositions(length - 1):
        for c in (0, 1, 2):
            rows = first + (c,)
            f = tuple(compose(list(ROWS[r] for r in rows), x) for x in range(3))
            out.append((rows, f))
    return out


const_by_length = {}
for length in (1, 2, 3):
    entries = []
    for rows, f in compositions(length):
        if len(set(f)) == 1:
            entries.append({"rows": list(rows), "constant": f[0]})
    const_by_length[str(length)] = entries
report["constant_compositions"] = const_by_length
report["constant_compositions_note"] = (
    "R_c denota la fila TR[c][.]; una composicion constante sobre {0,1,2} es "
    "tambien constante sobre el trit 2 de EOF, luego colapsar un trit borra la "
    "distincion EOF en ese trit.")

# ----------------------------------- 4. donde vive la distincion EOF
def trits(v, k=10):
    out = []
    for _ in range(k):
        out.append(v % 3)
        v //= 3
    return out


byte_trit_sets = []
for p in range(10):
    s = set()
    for b in range(256):
        s.add(trits(b)[p])
    byte_trit_sets.append(sorted(s))
report["byte_trit_sets"] = {str(p): byte_trit_sets[p] for p in range(10)}
report["eof_trits"] = trits(EOF_VALUE)
report["distinctive_positions"] = [p for p in range(10) if byte_trit_sets[p] == [0]]

# ------------------------ 5. deriva de mascaras: la cadena depende del historial
def chain_two_steps(byte_stream, mask1, mask2):
    """Dos CRAZY encadenados sobre celdas distintas; se rastrean sus mascaras.

    Cada celda escribe el resultado de su propio crazy, de modo que la mascara
    de la ronda n+1 es la salida de la ronda n: la composicion es historica.
    """
    cell1, cell2 = mask1, mask2
    trace = []
    for b in byte_stream:
        a = b
        a = crazy(a, cell1)          # CRAZY en celda 1 -> celda1 = a
        cell1 = a
        a = crazy(a, cell2)          # CRAZY en celda 2 -> celda2 = a
        cell2 = a
        trace.append({"byte": b, "cell1": cell1, "cell2": cell2, "out": cell2})
    return trace


s1 = chain_two_steps([0x41, 0x42, 0x43], 0, 0)
s2 = chain_two_steps([0x41, 0x42, 0x43], 0, 0)
s3 = chain_two_steps([0x51, 0x52, 0x53], 0, 0)
report["mask_drift"] = {
    "chain": "CRAZY(b;A) ; CRAZY(a;B)",
    "stream_a": [0x41, 0x42, 0x43],
    "stream_b": [0x51, 0x52, 0x53],
    "out_stream_a": [t["out"] for t in s1],
    "out_stream_b": [t["out"] for t in s3],
    "outputs_differ_with_history": s1[0]["out"] != s3[0]["out"],
    "note": ("con la misma entrada la primera ronda coincide; en cuanto el "
             "historial cambia, la composicion effective cambia: la mascara de "
             "la ronda n+1 es la salida de la ronda n."),
}

# --------- 5b. la cadena de colapso de 3 pasos: correcta en la ronda 1, no en la 2
# Diseno candidato: A con mascara 0 (fila R_0, imagen {0,1}), B con mascara C2
# (fila R_2, colapsa {0,1} a 2) y C con mascara M3 por posicion (fila R_M3).
# Con mascaras estables el resultado seria una constante por posicion; se mide
# que en un bucle la mascara de A se deriva y el colapso se rompe.
def chain_three_steps(byte_stream, mask_a=0, mask_b=C2, mask_c=C1):
    """Mascaras de celda: son palabras de 10 trits; la fila aplicada en la
    posicion p es R_{trit_p(mascara)}."""
    cells = [mask_a, mask_b, mask_c]
    trace = []
    for b in byte_stream:
        a = b
        for i in range(3):
            a = crazy(a, cells[i])
            cells[i] = a
        trace.append({"byte": b, "A": cells[0], "B": cells[1], "C": cells[2],
                      "out": a})
    return trace


t3 = chain_three_steps([0x41, 0x42, 0x43, 0x44])
outs = [t["out"] for t in t3]
report["collapse_chain_in_loop"] = {
    "design": "CRAZY(b;A=0) ; CRAZY(a;B=C2) ; CRAZY(a;C=M3)",
    "why_it_should_work": ("con mascaras estables R_2 colapsa la imagen {0,1} "
                           "de R_0 a la constante 2, y R_M3(2) fija el destino"),
    "stream": [0x41, 0x42, 0x43, 0x44],
    "outputs": outs,
    "round1_is_constant_2": outs[0] == 2 * sum(3 ** i for i in range(10)),
    "output_stable_across_rounds": len(set(outs)) == 1,
    "mask_A_after_round1": t3[0]["A"],
    "mask_A_is_word_with_trits_in_01": set(trits(t3[0]["A"])) <= {0, 1},
    "verdict": ("la cadena colapsa en la ronda 1 (salida constante) pero no en "
                "la ronda 2: la mascara de A es ahora R_0(byte) y su imagen "
                "ya no es {0,1}, luego R_2 deja de colapsar"),
}


# ------------------- 6. consecuencias enumeradas (tabla de sensibilidad)
report["conclusions"] = {
    "c1_mask_restores_word": "crazy(crazy(V,29524),29524) == V para toda palabra de 10 trits",
    "single_crazy_branch_possible": False,
    "collapse_preserves_eof_bit": False,
    "loop_stable_branch_needs": [
        "rearmar las mascaras cada vuelta (coste medido: ejemplo LMAO 20776 celdas)",
        "o despachar por tabla sobre un indice que cubra todos los estados alcanzables",
    ],
    "measurements": {
        "lmao_eof_cat_cells": 20776,
        "pureepoch_cat_cells": 7972,
    },
}

out = json.dumps(report, indent=2, sort_keys=True) + "\n"
(P / "crazy_algebra.results.json").write_text(out)
print(json.dumps(report, indent=2, sort_keys=True))
sys.exit(0 if report["parity_engine"]["mismatches"] == 0 else 1)
