#!/usr/bin/env python3
"""plan.py — mini-planificador de imágenes Classic Malbolge con placement absoluto.

Recorre `d` instrucción a instrucción mientras emite el código, de modo que todas
las aserciones son en vivo (no hay que adivinar el recorrido y verificarlo después).

Reglas que implementa (semántica = tools/oracle_classic.py y el runner C):

  * `d` arranca en 0 y avanza +1 por instrucción ejecutada.
  * DLOAD: `d = mem[d]` y luego `d += 1`.  La celda leída es la que `d` está
    señalando, y su valor debe ser un byte imprimible (33..126): por eso every
    hop sólo puede apuntar a direcciones <= 127.
  * CRAZY: `mem[d] = crazy(a, mem[d])`, `a = mem[d]`.
  * ROT:   `mem[d] = rot(mem[d])`, `a = mem[d]`.
  * JMP:   `c = mem[d]`; la ejecución continúa en `c + 1`.  No toca `d`.

Zonas (el PC nunca ejecuta una celda de dato):

    zona A (código)   : pc 0..40          (41 ranuras; la última es el JMP)
    zona D (dato)     : 41..127           (máscaras, celdas de salto)
    zona B (código)   : pc 128..          (tras el JMP)

El planificador lanza una excepción en cuanto una celda de salto necesitaría dos
valores distintos: eso es exactamente el conflicto de rutado que el diseño manual
provocaba.
"""
from __future__ import annotations

from pathlib import Path

import sys

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
sys.path[:0] = [str(ROOT / "tools")]
import oracle_classic as oc  # noqa: E402

OPS = {"JMP": 4, "OUT": 5, "IN": 23, "ROT": 39, "DLOAD": 40,
       "CRAZY": 62, "NOP": 68, "END": 81}

ZONE_A_HI = 39          # última ranura de código antes del salto a la zona B
DATA_LO, DATA_HI = 41, 126
ZONE_B_LO = 127
MAX_HOP = DATA_HI       # un hop sólo puede valer <= 126 (byte imprimible)


def enc(addr: int, op: int) -> int:
    return 33 + ((op - 33 - addr) % 94)


class PlanError(RuntimeError):
    pass


class Planner:
    def __init__(self) -> None:
        self.mem: dict[int, int] = {}       # semillas de IMAGEN (imprimibles)
        self.sim: dict[int, int] = {}       # valores en runtime (simulados)
        self.hop_used: dict[int, int] = {}  # celdas de salto ya comprometidas
        self.code: list[tuple[int, str, object]] = []
        self.pc = 0
        self.d = 0
        self.a = 0
        self.a_sim = 0
        self.log: list[dict] = []

    # ---------- siembra ----------
    def seed(self, addr: int, value: int) -> None:
        if addr in self.mem and self.mem[addr] != value:
            raise PlanError(f"celda {addr}: semilla {self.mem[addr]} vs {value}")
        if not (33 <= value <= 126):
            raise PlanError(f"semilla no imprimible en {addr}: {value}")
        self.mem[addr] = value
        self.sim[addr] = value

    def seed_free(self, addr: int, value: int) -> None:
        """Una celda que debe estar libre (no usada como máscara ni hop)."""
        if addr in self.mem:
            raise PlanError(f"celda {addr} ya sembrada ({self.mem[addr]})")
        self.seed(addr, value)

    # ---------- emisión ----------
    def _d_cell_free(self) -> bool:
        """La celda que d señala está libre para el JMP de zona."""
        return self.d not in self.mem and self.d not in self.hop_used

    def jmp(self) -> None:
        """JMP con destino dinámico: c = mem[d] y la ejecución sigue en c+1.

        No puede predecirse en el planificador (depende de un valor de runtime);
        sólo emite la instrucción y avanza d en 1.
        """
        self._emit("JMP_DYN")
        self.d += 1

    def _raw_emit(self, name: str, arg: object = None) -> None:
        """Emite sin preparación de frontera (uso interno)."""
        self.code.append((self.pc, name, arg))
        self.log.append({"pc": self.pc, "op": name, "arg": arg,
                         "d": self.d, "a": self.a})
        self.pc += 1

    def _prepare_boundary(self) -> None:
        """Acerca `d` a una celda libre antes de que se agote la zona A.

        El JMP de zona lee mem[d], así que necesita una celda libre; con dos
        ranuras de antelación se esquivan con NOPs las celdas comprometidas.
        """
        while (ZONE_A_HI - 2 <= self.pc <= ZONE_A_HI - 1
               and not self._d_cell_free()):
            if self.pc == ZONE_A_HI - 1:
                self._raw_emit("NOP")
                self.d += 1
                if not self._d_cell_free():
                    raise PlanError(
                        f"sin margen para el JMP de zona: d={self.d} comprometida")
                return
            self._raw_emit("NOP")
            self.d += 1

    def park(self) -> None:
        """Avanza con NOPs hasta que la celda que señala d esté libre."""
        while not self._d_cell_free():
            if self.d > DATA_HI - 8:
                raise PlanError(f"sin celdas libres cerca de d={self.d}")
            self._raw_emit("NOP")
            self.d += 1

    def zone_jump(self) -> None:
        """JMP explícito de la zona A a la zona B leyendo mem[d]."""
        if self.pc > ZONE_A_HI:
            raise PlanError("la zona A ya se agotó")
        if not self._d_cell_free():
            raise PlanError(f"JMP de zona con d={self.d} comprometida; llama park()")
        self.seed_free(self.d, ZONE_B_LO - 1)
        self.hop_used[self.d] = ZONE_B_LO
        self._raw_emit("JMP", ZONE_B_LO)
        self.pc = ZONE_B_LO
        self.d += 1        # toda instrucción ejecutada avanza d en 1, JMP incluido
        self.log[-1]["jump_to"] = ZONE_B_LO

    def _emit(self, name: str, arg: object = None) -> None:
        self._prepare_boundary()
        if self.pc == ZONE_A_HI:
            # La última ranura de la zona A la ocupa el JMP a la zona B: el PC
            # nunca ejecuta celdas de dato, así que el código se parte en dos.
            addr = self.d
            if not (DATA_LO <= addr <= DATA_HI):
                raise PlanError(f"JMP de zona con d={addr} fuera de la zona de dato")
            if addr in self.hop_used and self.hop_used[addr] != ZONE_B_LO:
                raise PlanError(f"celda {addr} comprometida a {self.hop_used[addr]}")
            self.hop_used[addr] = ZONE_B_LO
            self.seed_free(addr, ZONE_B_LO - 1)
            self.code.append((self.pc, "JMP", ZONE_B_LO))
            self.log.append({"pc": self.pc, "op": "JMP", "arg": ZONE_B_LO,
                             "d": self.d, "a": self.a, "jump_to": ZONE_B_LO})
            self.pc = ZONE_B_LO
        if self.pc > ZONE_A_HI and self.pc < ZONE_B_LO:
            raise PlanError(f"pc {self.pc} cae en la zona de dato")
        self.code.append((self.pc, name, arg))
        self.log.append({"pc": self.pc, "op": name, "arg": arg,
                         "d": self.d, "a": self.a})
        self.pc += 1

    def nop(self, n: int = 1) -> None:
        for _ in range(n):
            self._emit("NOP")
            self.d += 1

    def _hop(self, target: int) -> None:
        """Emite un DLOAD que lee mem[d] y aterriza en `target`."""
        if target > MAX_HOP:
            raise PlanError(f"hop a {target} > {MAX_HOP}: valor no imprimible")
        addr = self.d
        if not (DATA_LO <= addr <= DATA_HI):
            raise PlanError(f"celda de salto {addr} fuera de la zona de dato")
        if addr in self.hop_used:
            if self.hop_used[addr] != target:
                raise PlanError(
                    f"conflicto de rutado: celda {addr} usada para "
                    f"{self.hop_used[addr]} y ahora para {target}")
            # reutilización legítima (p. ej. el bucle de ROT): mismo valor
        else:
            if addr in self.mem:
                # la celda ya estaba sembrada (p. ej. el sucesor de época):
                # sólo es reutilizable si su valor ya apunta a Target
                self.seed(addr, target - 1)
            else:
                self.seed_free(addr, target - 1)
        self.hop_used[addr] = target
        self._emit("DLOAD", target)
        self.d = target

    def ensure_d(self, target: int) -> None:
        if self.d == target:
            return
        # Si la celda que d señala ya está comprometida a otro destino, avanza
        # con NOPs hasta una celda libre (rutado automático; antes esto era el
        # conflicto que había que resolver a mano).
        while self.d in self.mem and self.mem[self.d] != target - 1:
            if self.d > DATA_HI - 8:
                raise PlanError(f"d={self.d} demasiado alto para alcanzar {target}")
            self.nop(1)
        self._hop(target)

    def crazy(self, target: int) -> None:
        assert self.d == target, f"d={self.d} != {target}"
        old = self.sim.get(target, enc(target, OPS["NOP"]))
        self._emit("CRAZY", target)
        new = oc.crazy_op(self.a, old)
        self.sim[target] = new
        self.a = new
        self.d += 1

    def rot(self, target: int) -> None:
        assert self.d == target, f"d={self.d} != {target}"
        old = self.sim.get(target, enc(target, OPS["NOP"]))
        self._emit("ROT", target)
        new = (old // 3) + (old % 3) * 19683
        self.sim[target] = new
        self.a = new
        self.d += 1

    def inn(self) -> None:
        self._emit("IN")
        self.d += 1

    def out(self) -> None:
        self._emit("OUT")
        self.d += 1

    def end(self) -> None:
        self._emit("END")
        self.d += 1

    # ---------- imagen ----------
    def to_bytes(self) -> bytes:
        last = max(list(self.mem) + [c[0] for c in self.code])
        out = bytearray()
        for a in range(last + 1):
            code = {c[0]: c for c in self.code}
            if a in code:
                op = code[a][1]
                out.append(enc(a, OPS["JMP"] if op == "JMP_DYN" else OPS[op]))
            elif a in self.mem:
                out.append(self.mem[a])
            else:
                out.append(enc(a, OPS["NOP"]))
        return bytes(out)

    def summary(self) -> dict:
        return {"instructions": len(self.code), "pc_end": self.pc,
                "seeds": len(self.mem), "hops": len(self.hop_used),
                "final_d": self.d, "final_a": self.a_sim,
                "final_sim": {str(k): v for k, v in sorted(self.sim.items())},
                "hops_detail": {str(k): v for k, v in sorted(self.hop_used.items())}}
