#!/usr/bin/env python3
"""plan.py — planificador absoluto y simulador de las tres imágenes de
`epoch_rearm_cost_v1`.

Semántica = `tools/oracle_classic.py` y el runner C original:

  * `d` arranca en 0 y avanza +1 por instrucción ejecutada.
  * `DLOAD`: `d = mem[d]` y luego `d += 1`; la celda leída debe ser imprimible
    (33..126), por eso un hop sólo apunta a direcciones <= 127.
  * `ROT`: `mem[d] = rot(mem[d])`, `a = mem[d]`.
  * `CRAZY`: `mem[d] = crazy(a, mem[d])`, `a = mem[d]`; la orientación es
    `crazy(a, w) = TBL[w_trit][a_trit]` (trampa T24: el orden importa).
  * `JMP`: `c = mem[d]`, cifra `mem[c]` si es imprimible, y continúa en `c+1`.
  * Toda celda ejecutada se cifra después (`_ENC`) si es imprimible.

Las constantes de diseño NO se escriben a mano: `derive()` busca, en orden
lexicográfico, la primera palabra de control materializable como
`crazy(rot(v1), v2)` con `v1, v2` imprimibles. El pack reporta las que salgan.
"""
from __future__ import annotations

import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools")]
import oracle_classic as oc  # noqa: E402

MEM = 3 ** 10
OPS = {"JMP": 4, "OUT": 5, "IN": 23, "ROT": 39, "DLOAD": 40,
       "CRAZY": 62, "NOP": 68, "END": 81}
OPNAME = {v: k for k, v in OPS.items()}
ENC = oc._ENC
TBL = ((1, 0, 0), (1, 0, 2), (2, 2, 1))

X = 44          # celda de código que se restaura y re-ejecuta
V = 55          # valor original de X: (V + X) % 94 == 5 (OUT)
NEXT = X + 1    # celda de caída: NOP en la visita 1, END en la visita 2
NEXT_SEED = 43  # (43 + 45) % 94 == 88 (NOP); ENC[43] = 36 -> (36+45)%94 == 81


class PlanError(RuntimeError):
    pass


def trits(v: int) -> list[int]:
    return [(v // 3 ** i) % 3 for i in range(10)]


def rot(v: int) -> int:
    return v // 3 + (v % 3) * 19683


def enc(addr: int, op: int) -> int:
    return 33 + ((op - 33 - addr) % 94)


def ctrls(v: int, w: int) -> list[int]:
    """Todas las `a` con crazy(a, w) = v (por trit, exhaustivo)."""
    per = []
    for i in range(10):
        cand = [a for a in range(3) if TBL[trits(w)[i]][a] == trits(v)[i]]
        if not cand:
            return []
        per.append(cand)
    res = [0]
    for i, cand in enumerate(per):
        res = [r + a * 3 ** i for r in res for a in cand]
    return sorted(res)


def materialize(ctrl: int) -> tuple[int, int] | None:
    """Primer (v1, v2) imprimible con crazy(rot(v1), v2) = ctrl."""
    for v1 in range(33, 127):
        r = rot(v1)
        for v2 in range(33, 127):
            if oc.crazy_op(r, v2) == ctrl:
                return v1, v2
    return None


def derive(v: int, w: int) -> tuple[int, int, int]:
    """Primera palabra de control materializable para crazy(ctrl, w) = v."""
    for ctrl in ctrls(v, w):
        pair = materialize(ctrl)
        if pair is not None:
            return ctrl, pair[0], pair[1]
    raise PlanError(f"sin palabra de control materializable para {w} -> {v}")


class Plan:
    def __init__(self) -> None:
        self.mem: dict[int, int] = {}
        self.code: dict[int, str] = {}
        self.seeds: dict[int, int] = {}
        self.a = 0
        self.c = 0
        self.d = 0
        self.out: list[int] = []
        self.log: list[dict] = []
        self.status = "RUNNING"

    # ---- estado --------------------------------------------------------
    def cell(self, addr: int) -> int:
        if addr not in self.mem:
            raise PlanError(f"celda {addr} sin valor")
        return self.mem[addr]

    def seed(self, addr: int, value: int) -> None:
        if not (33 <= value <= 126):
            raise PlanError(f"semilla no imprimible {value} en {addr}")
        if addr in self.seeds and self.seeds[addr] != value:
            raise PlanError(f"semilla {addr}: {self.seeds[addr]} vs {value}")
        if addr in self.code and addr not in self.seeds:
            raise PlanError(f"{addr} ya es código ({self.code[addr]})")
        self.seeds[addr] = value
        self.mem[addr] = value

    def free(self, addr: int) -> bool:
        return addr not in self.seeds and addr not in self.code

    # ---- ejecución -----------------------------------------------------
    def _run(self, op: str) -> None:
        addr = self.c
        rec = {"pc": addr, "op": op, "d": self.d, "a": self.a}
        if op == "JMP":
            tgt = self.cell(self.d)
            rec["jump_to"] = tgt + 1
            if 33 <= self.mem[tgt] <= 126:
                rec["enc_cell"] = tgt
                self.mem[tgt] = ENC[self.mem[tgt]]
            self.c = (tgt + 1) % MEM
            self.d = (self.d + 1) % MEM
            self.log.append(rec)
            return
        if op == "OUT":
            self.out.append(self.a % 256)
            rec["emitted"] = self.a % 256
        elif op == "ROT":
            self.mem[self.d] = rot(self.cell(self.d))
            self.a = self.mem[self.d]
            rec["wrote"] = self.d
            rec["new"] = self.a
        elif op == "DLOAD":
            self.d = self.cell(self.d)
            rec["d_after_read"] = self.d
        elif op == "CRAZY":
            old = self.cell(self.d)
            self.mem[self.d] = oc.crazy_op(self.a, old)
            self.a = self.mem[self.d]
            rec["wrote"] = self.d
            rec["old"] = old
            rec["new"] = self.a
        elif op == "END":
            self.status = "HALTED"
            rec["halt"] = True
        if 33 <= self.mem[addr] <= 126:
            rec["enc_cell"] = addr
            self.mem[addr] = ENC[self.mem[addr]]
        self.c = (addr + 1) % MEM
        self.d = (self.d + 1) % MEM
        self.log.append(rec)

    def put(self, op: str) -> None:
        """Escribe la instrucción en pc con la codificación canónica y la ejecuta."""
        addr = self.c
        if addr in self.seeds:
            raise PlanError(f"{addr}: es semilla ({self.seeds[addr]})")
        if addr in self.code and self.code[addr] != op:
            raise PlanError(f"{addr}: ya hay {self.code[addr]}, no {op}")
        self.code[addr] = op
        self.mem[addr] = enc(addr, OPS[op])
        self._run(op)

    def run_here(self) -> None:
        """Ejecuta lo que la celda en pc ya contiene (semilla o código)."""
        addr = self.c
        opcode = (self.cell(addr) + addr) % 94
        name = OPNAME.get(opcode, "NOP")
        if addr not in self.code:
            self.code[addr] = name
        self._run(name)

    # ---- rutado --------------------------------------------------------
    def hop_to(self, cell_addr: int) -> None:
        guard = 0
        while self.d != cell_addr:
            guard += 1
            if guard > 500:
                raise PlanError(f"hop a {cell_addr} no converge (d={self.d})")
            want = cell_addr - 1
            if not (33 <= want <= 126):
                raise PlanError(f"hop imposible: {cell_addr}-1 no imprimible")
            if self.d in self.seeds and self.seeds[self.d] == want:
                self.put("DLOAD")
            elif self.free(self.d):
                self.seed(self.d, want)
                self.put("DLOAD")
            else:
                self.put("NOP")

    # ---- imagen --------------------------------------------------------
    def dump(self, fill: int = 33) -> bytes:
        last = max(list(self.mem) + list(self.code))
        out = bytearray()
        for a in range(last + 1):
            if a in self.seeds:
                out.append(self.seeds[a])
            elif a in self.code:
                out.append(enc(a, OPS[self.code[a]]))
            else:
                out.append(fill)
        return bytes(out)


def _bootstrap(p: Plan) -> None:
    p.put("DLOAD")   # 0: mem[0]=40 -> d=41
    p.put("DLOAD")   # 1: mem[41]=35 -> d=36
    p.put("ROT")     # 2: a = rot(126) = 42
    p.put("DLOAD")   # 3: mem[37]=37 -> d=38
    p.put("NOP")     # 4
    p.put("DLOAD")   # 5: mem[39]=42 -> d=43
    p.put("JMP")     # 6: mem[43]=43 -> c=44
    p.put("OUT")     # 44: X
    p.run_here()     # 45: semilla 43 -> opcode 88 (NOP); cifra a 36


def _routine(p: Plan, ctrl: int, v1: int, v2: int, restore: bool,
             back: int) -> None:
    p.put("DLOAD")   # 46: mem[46]=88 -> d=89
    p.put("DLOAD")   # 47: mem[89]=99 -> d=100
    p.put("ROT")     # 48: mem[100]=v1 -> a=rot(v1)
    p.put("DLOAD")   # 49: mem[101]=102 -> d=103
    p.put("CRAZY")   # 50: mem[103]=v2 -> a=ctrl
    assert p.a == ctrl, (p.a, ctrl)
    p.put("DLOAD")   # 51: mem[104]=43 -> d=44
    p.put("CRAZY" if restore else "NOP")   # 52: restaura X o no
    p.put("DLOAD")   # 53: mem[45]=36 -> d=37
    p.put("DLOAD")   # 54: mem[37]=37 -> d=38
    p.put("JMP")     # 55: mem[38]=back-1 -> c=back


def build(restore: bool = True, rearm: bool = False) -> tuple[Plan, dict]:
    ctrl, v1, v2 = derive(V, ENC[V])
    seeds = {
        36: 126, 37: 37, 38: 43 if not rearm else 55, 39: 42, 41: 35,
        43: 43, 45: NEXT_SEED,
        89: 99, 100: v1, 101: 102, 103: v2, 104: 43,
    }
    info = {"ctrl": ctrl, "v1": v1, "v2": v2, "ctrl2": None,
            "w1": None, "w2": None}
    if rearm:
        ctrl2, w1, w2 = derive(v2, ctrl)
        seeds.update({90: w1, 92: w2})
        info.update({"ctrl2": ctrl2, "w1": w1, "w2": w2})
    p = Plan()
    for addr, value in seeds.items():
        p.seed(addr, value)
    _bootstrap(p)
    _routine(p, ctrl, v1, v2, restore, back=56 if rearm else X)
    if rearm:
        assert p.c == 56, p.c
        p.hop_to(90)
        p.put("ROT")     # 58: mem[90]=w1 -> a=rot(w1)
        p.hop_to(92)
        p.put("CRAZY")   # 60: mem[92]=w2 -> a=ctrl2
        assert p.a == ctrl2, (p.a, ctrl2)
        p.hop_to(103)
        p.put("CRAZY")   # 62: mem[103]: ctrl -> v2
        p.hop_to(104)
        p.put("DLOAD")   # 63: mem[104]=43 -> d=43
        p.put("END")     # 64
    return p, info


def images() -> list[tuple[str, Plan, dict]]:
    return [("restore", *build(True, False)),
            ("no_restore", *build(False, False)),
            ("rearm", *build(True, True))]
