"""Slot-state probe for the CMP_LT image (debug aid for LT_STATUS work).

Usage:
    python3 vm_malbolge/tools/lt_slotprobe.py [mb_path] [dbg_path]

Runs the 9 ordered CMP_LT pairs on the oracle semantics and snapshots the
stack-slot cells at every REAL OUT (opcode 5): step, A, Slot0/Slot1 values
and the two slot-choice flags, plus the final printed bytes.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import oracle_classic as oc

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lt_trace

MB = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "vm_malbolge/src/mbir_cmp_lt.mb"
DBG = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "vm_malbolge/src/mbir_cmp_lt.dbg"
lt_trace.DBG = DBG

CELLS = ("stack_top", "stack_top_1", "SLOT0_FLAG", "SLOT1_FLAG", "LT_B1")


def probe(hexin, mem_template, addr_of):
    mem = list(mem_template)
    a = c = d = 0
    out = []
    stdin_iter = iter(bytes.fromhex(hexin).decode("latin-1"))
    events = []
    steps = 0
    while steps < 2000000:
        steps += 1
        cell = mem[c]
        op = (cell + c) % 94
        jumped = False
        c_target = 0
        if op == 4:
            c_target = mem[d]
            jumped = True
        elif op == 5:
            vals = {w: mem[addr_of[w]] for w in CELLS if w in addr_of}
            events.append((steps, a, vals))
            out.append(a % 256)
        elif op == 23:
            ch = next(stdin_iter, None)
            a = -1 if ch is None else ord(ch)
        elif op == 39:
            v = mem[d]
            mem[d] = (v // 3) + (v % 3) * (3 ** 9)
            a = mem[d]
        elif op == 40:
            d = mem[d]
        elif op == 62:
            mem[d] = oc.crazy_op(a, mem[d])
            a = mem[d]
        elif op == 68:
            pass
        elif op == 81:
            break
        if jumped:
            c = c_target
        if 33 <= mem[c] <= 126:
            mem[c] = oc._ENC[mem[c]]
        c = (c + 1) % oc.MEM_SIZE
        d = (d + 1) % oc.MEM_SIZE
    return out, steps, events


def main():
    addr2line, labels = lt_trace.load_dbg()
    addr_of = {name: addr for addr, name in labels.items()}
    mem_template = oc.load_memory(MB.read_text())
    print(f"# image: {MB}")
    for b in range(3):
        for a_ in range(3):
            hexin = f"01{a_:02x}01{b:02x}021000"
            want = "01" if a_ < b else "00"
            out, steps, events = probe(hexin, mem_template, addr_of)
            got = "".join(f"{x:02x}" for x in out)
            mark = "PASS" if got == want else "FAIL"
            print(f"({a_},{b})->{want}: got={got} [{mark}] steps={steps}")
            for st, av, vals in events:
                v = " ".join(f"{k}={vals[k]}" for k in CELLS if k in vals)
                print(f"    OUT@{st:6d} A={av} {v}")


if __name__ == "__main__":
    main()
