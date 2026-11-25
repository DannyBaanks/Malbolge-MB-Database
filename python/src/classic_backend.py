"""Native Classic emitter: sparse pointer banks, numeric returns, one-shot instances."""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from classic_frontend import Call, CompileError, Print, Program

C1 = 29524
MAIN = 20000
HANDOFF = 58000


def repository_root():
    return (
        Path(os.environ["MALBOLGE_MB_DATABASE_ROOT"])
        if "MALBOLGE_MB_DATABASE_ROOT" in os.environ
        else Path(__file__).resolve().parents[2]
    )


@lru_cache(maxsize=4)
def forge_module(root):
    path = Path(root) / "tools/resynthesize.py"
    if not path.is_file():
        raise CompileError("no se encontró BolgeForge; configura BOLGEFORGE_ROOT")
    spec = importlib.util.spec_from_file_location("classic_native_resynthesize", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass
class Artifact:
    image: bytes
    mapping: dict


class Emitter:
    def __init__(self, program):
        self.program = program
        self.code = {}
        self.data = {HANDOFF: MAIN - 1, HANDOFF + 1: HANDOFF - 1}
        self.cells = {HANDOFF: ("handoff", MAIN - 1)}
        self.next_cell = 40020
        self.pc = MAIN
        self.d = HANDOFF + 1
        self.markers = {}
        self.slot_pairs = {}
        self.byte_cells = {}
        self.instances = {}
        self.calls = {}
        self.mask = self.cell("C1", C1)

    def cell(self, name, value):
        if self.next_cell + 63 >= HANDOFF:
            raise CompileError(
                "el programa supera la memoria de datos Classic disponible"
            )
        address = self.next_cell
        self.next_cell += 64
        self.cells[address] = (name, value)
        self.data[address] = value
        self.data[address + 1] = address - 1
        return address

    def mark(self, kind, **fields):
        self.markers.setdefault(str(self.pc), []).append({"kind": kind, **fields})

    def write_instruction(self, opcode):
        if self.pc >= 39930:
            raise CompileError(
                "el programa supera la zona de código Classic disponible"
            )
        assert self.pc not in self.code
        self.code[self.pc] = 33 + ((opcode - self.pc - 33) % 94)
        self.pc += 1

    def op(self, opcode):
        self.write_instruction(opcode)
        self.d = (self.d + 1) % 59049

    def pad(self):
        self.write_instruction(68)

    def set_d(self, target):
        if self.d == target:
            return
        bank = next((b for b in self.cells if b < self.d <= b + 63), None)
        if bank is None:
            raise CompileError("el emisor perdió el contexto del puntero de datos")
        positions = [
            a for a in range(self.d, bank + 64) if self.data.get(a) == target - 1
        ]
        if positions:
            position = positions[0]
        else:
            position = next(
                (
                    a
                    for a in range(max(self.d, bank + 2), bank + 64)
                    if a not in self.data
                ),
                None,
            )
            if position is None:
                raise CompileError(
                    "una cabecera de punteros agotó su capacidad Classic"
                )
            self.data[position] = target - 1
        while self.d < position:
            self.op(68)
        self.op(40)
        self.d = target

    def read(self, cell, count=10):
        for _ in range(count):
            self.set_d(cell)
            self.op(39)

    def reset(self, cell):
        self.read(self.mask, 1)
        for _ in range(2):
            self.set_d(cell)
            self.op(62)

    def slots(self, depth):
        if depth not in self.slot_pairs:
            self.slot_pairs[depth] = (
                self.cell(f"return_slot_{depth}", C1),
                self.cell(f"journal_{depth}", C1),
            )
        return self.slot_pairs[depth]

    def emit_body(self, body):
        for statement in body:
            if isinstance(statement, Print):
                for value in statement.data:
                    if value not in self.byte_cells:
                        self.byte_cells[value] = self.cell(f"byte_{value}", value)
                    self.read(self.byte_cells[value])
                    self.mark(
                        "print",
                        line=statement.line,
                        column=statement.column,
                        byte=value,
                    )
                    self.op(5)
            elif isinstance(statement, Call):
                self.emit_call(statement)
            else:
                raise TypeError(type(statement))

    def emit_call(self, invocation):
        slot, journal = self.slots(invocation.depth)
        source = self.cell(f"return_address_{invocation.identifier}", 0)
        pointer = self.cell(f"call_address_{invocation.identifier}", 0)
        self.reset(slot)
        self.reset(journal)
        self.read(source)
        self.set_d(journal)
        self.op(62)
        self.set_d(slot)
        self.op(62)
        self.set_d(pointer)
        call_pc = self.pc
        self.mark(
            "call",
            instance=invocation.identifier,
            name=invocation.name,
            depth=invocation.depth,
            slot=slot,
            journal=journal,
        )
        self.op(4)
        self.pad()
        continuation = self.pc
        self.data[source] = continuation - 1
        self.calls[invocation.identifier] = {
            "call_pc": call_pc,
            "continuation": continuation,
            "return_source": source,
            "call_pointer": pointer,
            "slot": slot,
            "journal": journal,
        }
        self.d = slot + 1
        self.mark(
            "continuation",
            instance=invocation.identifier,
            depth=invocation.depth,
            slot=slot,
        )
        self.reset(slot)
        self.reset(journal)

    def emit(self):
        self.mark("main_entry")
        self.emit_body(self.program.body)
        self.mark("main_halt")
        self.op(81)
        for invocation in self.program.instances:
            self.pad()
            entry = self.pc
            call = self.calls[invocation.identifier]
            self.data[call["call_pointer"]] = entry - 1
            self.d = call["call_pointer"] + 1
            self.mark(
                "function_entry",
                instance=invocation.identifier,
                name=invocation.name,
                depth=invocation.depth,
            )
            self.emit_body(invocation.body)
            self.read(call["slot"])
            self.set_d(call["slot"])
            ret_pc = self.pc
            self.mark(
                "return",
                instance=invocation.identifier,
                depth=invocation.depth,
                slot=call["slot"],
            )
            self.op(4)
            self.instances[invocation.identifier] = {
                "id": invocation.identifier,
                "name": invocation.name,
                "depth": invocation.depth,
                "line": invocation.line,
                "column": invocation.column,
                "entry": entry,
                "end": self.pc,
                "return_pc": ret_pc,
                **call,
            }
        self.data[HANDOFF] = MAIN - 1
        return self


def compile_program(program: Program, forge_root=None) -> Artifact:
    emitter = Emitter(program).emit()
    root = Path(
        forge_root
        or os.environ.get("BOLGEFORGE_ROOT", repository_root().parent / "BolgeForge")
    ).resolve()
    forge = forge_module(str(root))
    template = [
        x
        for x in (root / "reference/malbolge_org/cat.mal").read_bytes()
        if 33 <= x <= 126
    ]
    length = len(template) + 94 * 325
    if length != 39932:
        raise CompileError(
            "la plantilla Classic cambió; requiere verificar de nuevo el bootstrap"
        )
    clean = template + [33] * (length - len(template))
    try:
        ops = forge.synthesize_preamble_ops(
            clean,
            emitter.data,
            HANDOFF,
            9003,
            0,
            template_clean=template,
            boot="original",
        )
    except (ValueError, RuntimeError) as error:
        raise CompileError("falló la síntesis del bootstrap: " + str(error)) from None
    preamble_end = 99 + len(ops)
    if preamble_end >= MAIN:
        raise CompileError(
            f"el inicializador requiere {preamble_end} celdas; el límite de esta disposición es {MAIN - 1}"
        )
    image = bytearray(template[:99])
    image.extend(
        33 + ((forge.XLAT1.index(ch) - i) % 94) for i, ch in enumerate(ops, 99)
    )
    while len(image) < length - 2:
        image.append(33 + ((forge.XLAT1.index("o") - len(image)) % 94))
    image.extend(template[-2:])
    for pc, word in emitter.code.items():
        image[pc] = word
    if not all(
        33 <= word <= 126 and (word + i) % 94 in {4, 5, 23, 39, 40, 62, 68, 81}
        for i, word in enumerate(image)
    ):
        raise CompileError("la imagen no satisface el cargador Classic estricto")
    mapping = {
        "schema": "python_literal_classic_v0",
        "source_sha256": program.source_sha256,
        "strategy": "one-shot-call-instances",
        "source_length": length,
        "preamble_end": preamble_end,
        "main_entry": MAIN,
        "expanded_output_bytes": program.output_bytes,
        "instances": [emitter.instances[i] for i in sorted(emitter.instances)],
        "slots": {
            str(d): {"slot": s, "journal": j}
            for d, (s, j) in emitter.slot_pairs.items()
        },
        "markers": emitter.markers,
        "cells": {
            str(a): {"name": n, "initial": emitter.data[a]}
            for a, (n, _) in emitter.cells.items()
        },
    }
    return Artifact(bytes(image), mapping)
