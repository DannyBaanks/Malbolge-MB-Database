"""Block-level control-flow tracer for the CMP_LT image.

Usage:
    python3 vm_malbolge/tools/lt_trace2.py <hex-input> [max_steps] [--from=N] [--dedup]

Uses the .dbg LABELS section: each label (HeLL block start / .CODE template)
gets an address; sorted label addresses give PC ranges per block. Prints one
line per block entry plus any step where a labeled cell value changes
(flag arm/consume events show as LABEL changes).
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import oracle_classic as oc

MB = REPO / "vm_malbolge/src/mbir_cmp_lt.mb"
DBG = REPO / "vm_malbolge/src/mbir_cmp_lt.dbg"


def load_labels():
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
    return labels


def main():
    hexin = sys.argv[1]
    max_steps = int(sys.argv[2]) if len(sys.argv) > 2 else 90000
    start_from = 0
    dedup = "--dedup" in sys.argv
    for arg in sys.argv[3:]:
        if arg.startswith("--from="):
            start_from = int(arg.split("=")[1])
    labels = load_labels()
    addrs = sorted(labels)
    # PC -> block name via range
    import bisect
    mem = oc.load_memory(MB.read_text())
    a = c = d = 0
    out = []
    stdin_iter = iter(bytes.fromhex(hexin).decode("latin-1"))
    steps = 0
    prev_block = None
    prev_vals = {addr: mem[addr] for addr in addrs}
    ops = {4: "jmp", 5: "OUT", 23: "IN", 39: "rot", 40: "movd", 62: "crazy", 49: "nop"}
    while steps < max_steps:
        cell = mem[c]
        op = (cell + c) % 94
        steps += 1
        i = bisect.bisect_right(addrs, c) - 1
        block = labels[addrs[i]] if i >= 0 else "?"
        changed = []
        for addr in addrs:
            v = mem[addr]
            if v != prev_vals[addr]:
                changed.append(f"{labels[addr]}:{v}")
                prev_vals[addr] = v
        if steps >= start_from:
            if (block != prev_block or changed) and not (dedup and block == prev_block and not changed):
                print(f"{steps:7d} {block:>24s} {ops.get(op, str(op)):>5s} A={a:5d} " +
                      (" ".join(changed) if changed else ""))
            prev_block = block
        if op == 4 and steps >= start_from:
            t = mem[d]
            j = bisect.bisect_right(addrs, t) - 1
            print(f"{steps:7d} {'JMP->':>24s} {labels[addrs[j]] if j >= 0 else t} @ {t}")
        if op == 40 and steps >= start_from:
            t = mem[d]
            j = bisect.bisect_right(addrs, t) - 1
            print(f"{steps:7d} {'MOVD->d':>24s} {labels[addrs[j]] if j >= 0 else t} (d={t})")
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
        elif op == 81:
            print(f"{steps:7d} {'HALT':>24s} out={bytes(out)!r}")
            return
        if jumped:
            c = c_target
        if 33 <= mem[c] <= 126:
            mem[c] = oc._ENC[mem[c]]
        c = (c + 1) % oc.MEM_SIZE
        d = (d + 1) % oc.MEM_SIZE
    print(f"== HALT@{steps} out={bytes(out)!r}", file=sys.stderr)


if __name__ == "__main__":
    main()
