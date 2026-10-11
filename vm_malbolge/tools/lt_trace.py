"""Source-line step tracer for the CMP_LT image (debug aid for LT_STATUS work).

Usage:
    python3 vm_malbolge/tools/lt_trace.py <hex-input> [max_steps] [--from=N] [--dedup]

Parses vm_malbolge/src/mbir_cmp_lt.dbg (:SOURCEPOSITIONS: addr -> HeLL line),
runs tools/oracle_classic semantics with instrumentation, and prints one line
per executed cell that maps to a HeLL source line: step, line number, line
text, A and the four stack cells. --dedup collapses repeated lines.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import oracle_classic as oc

MB = REPO / "vm_malbolge/src/mbir_cmp_lt.mb"
DBG = REPO / "vm_malbolge/src/mbir_cmp_lt.dbg"
HELL = REPO / "vm_malbolge/src/mbir_cmp_lt.hell"

CELL_LABELS = ("stack_scratch", "stack_top", "stack_scratch_1", "stack_top_1")


def load_dbg():
    addr2line = {}
    labels = {}
    section = None
    for raw in DBG.read_text().splitlines():
        if raw.startswith(":"):
            section = raw.strip(":")
            continue
        if section == "LABELS" and ": " in raw:
            name, rest = raw.split(":", 1)
            parts = rest.split()
            if parts and parts[-1].isdigit():
                labels[int(parts[-1])] = name
        elif section == "SOURCEPOSITIONS":
            addr, rest = raw.split(":", 1)
            start = rest.split()[1]  # e.g. 155:2
            line = int(start.split(":")[0])
            addr2line[int(addr)] = line
    return addr2line, labels


def line_to_block(hell_lines):
    """Map 1-based hell line -> enclosing label (line ending with ':')."""
    blocks = {}
    current = "?"
    for i, raw in enumerate(hell_lines, 1):
        s = raw.strip()
        if s.endswith(":") and not s.startswith("//") and not s.startswith("*"):
            current = s[:-1]
        blocks[i] = current
    return blocks


def main():
    hexin = sys.argv[1]
    max_steps = int(sys.argv[2]) if len(sys.argv) > 2 else 90000
    start_from = 0
    dedup = "--dedup" in sys.argv
    for arg in sys.argv[3:]:
        if arg.startswith("--from="):
            start_from = int(arg.split("=")[1])
    addr2line, labels = load_dbg()
    addr_of = {name: addr for addr, name in labels.items()}
    hell = HELL.read_text().splitlines()
    blocks = line_to_block(hell)
    mem = oc.load_memory(MB.read_text())
    a = c = d = 0
    out = []
    stdin_iter = iter(bytes.fromhex(hexin).decode("latin-1"))
    steps = 0
    prev_line = None
    while steps < max_steps:
        steps += 1
        line = addr2line.get(c)
        if line is not None and steps >= start_from:
            if not (dedup and line == prev_line):
                text = hell[line - 1].strip()
                vals = " ".join(f"{w}={mem[addr_of[w]]}"
                                for w in CELL_LABELS if w in addr_of)
                print(f"{steps:7d} {blocks[line]:>24s} L{line:3d} {text:34s} "
                      f"A={a:5d} {vals}")
            prev_line = line
        cell = mem[c]
        op = (cell + c) % 94
        jumped = False
        c_target = 0
        if op == 4:
            c_target = mem[d]
            jumped = True
        elif op == 5:
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
            print(f"{steps:7d} HALT out={''.join(chr(x) for x in out)!r}")
            return
        if jumped:
            c = c_target
        if 33 <= mem[c] <= 126:
            mem[c] = oc._ENC[mem[c]]
        c = (c + 1) % oc.MEM_SIZE
        d = (d + 1) % oc.MEM_SIZE
    print(f"{steps:7d} MAX_STEPS out={''.join(chr(x) for x in out)[:8]!r}...")


if __name__ == "__main__":
    main()
