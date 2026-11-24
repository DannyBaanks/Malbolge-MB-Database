#!/usr/bin/env python3
"""Ternary model for Brainfuck 2-cell tape movement and swap loop.

Establishes formal algebra for two decoupled tape cells (cell0, cell1)
and the EOF discriminator on cell1.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import sys

# Constants
ONE = 29524
TWO = 59048
LOW = sum(3**i for i in range(6))
HIGH = ONE - LOW

def crazy(a: int, b: int) -> int:
    """Ternary crazy operation: TBL[cell][accumulator]."""
    res = 0
    p = 1
    for _ in range(10):
        t_a = a % 3
        t_b = b % 3
        tbl = (
            (1, 0, 0),
            (1, 0, 2),
            (2, 2, 1),
        )
        res += tbl[t_b][t_a] * p
        a //= 3
        b //= 3
        p *= 3
    return res

def rot(x: int) -> int:
    """Rotate ternary word 1 trit right."""
    return (x // 3) + ((x % 3) * (3**9))

def left(x: int, n: int) -> int:
    for _ in range((10 - n) % 10):
        x = rot(x)
    return x

def eq2_or(x: int, mask: int) -> int:
    g = crazy(mask, x)
    return crazy(g, x)

def and_or(x: int, y: int, mask: int) -> int:
    g1 = crazy(TWO, x)
    g2 = crazy(g1, y)
    g3 = crazy(mask, g2)
    return crazy(g3, g3)

def is_eof(x: int) -> bool:
    """Discriminator for Olmstead EOF (59048) vs byte values (0..255).

    The chain `crazy(58324, eq2_or(x, HIGH))` followed by
    `and_or`/`left` does NOT separate EOF from bytes: it yields 58680 for
    59048 and for every byte 0..255 (measured). It is therefore not usable as
    a discriminator; the only correct test is direct equality with TWO.
    See `probe_eof_chain()` below for the exhaustive check.
    """
    return x == TWO


def probe_eof_chain() -> dict:
    """Exhaustively confirm the crazy-chain EOF candidate is non-discriminating."""
    def chain(x: int) -> int:
        p = eq2_or(x, HIGH)
        for k in (1, 2, 4):
            p = and_or(p, left(p, k), HIGH)
        return crazy(8, crazy(58324, p))

    byte_values = {chain(x) for x in range(256)}
    eof_value = chain(TWO)
    return {
        "distinct_byte_outputs": len(byte_values),
        "eof_output": eof_value,
        "eof_collides_with_bytes": eof_value in byte_values,
        "discriminates": eof_value not in byte_values,
    }

def tape_swap_oracle(cell0: int, cell1: int) -> tuple[int, int]:
    """Positive 2-cell tape model: cell0 and cell1 are distinct storage locations."""
    return cell1, cell0

def single_cell_fake_oracle(cell0: int, cell1: int) -> tuple[int, int]:
    """Negative control: single cell overwriting without tape addressing."""
    # When '>' has no effect and writes overwrite the same cell:
    cell = cell0
    cell = cell1  # overwritten
    return cell, cell

def main():
    # Verify tape swap across all distinct byte pairs
    distinct_pairs = [(i, (i + 42) % 256) for i in range(256)]
    pos_results = [tape_swap_oracle(c0, c1) for c0, c1 in distinct_pairs]
    fake_results = [single_cell_fake_oracle(c0, c1) for c0, c1 in distinct_pairs]

    fake_mismatches = sum(p != f for p, f in zip(pos_results, fake_results))
    assert fake_mismatches == 256, f"Fake single-cell must fail all 256 pairs: {fake_mismatches}"

    info = {
        "scope": "host ternary tape algebra and negative control oracle",
        "eof_chain_probe": probe_eof_chain(),
        "distinct_pairs_tested": len(distinct_pairs),
        "positive_all_swapped": all(pos == (c1, c0) for (c0, c1), pos in zip(distinct_pairs, pos_results)),
        "negative_fake_mismatches": fake_mismatches,
        "negative_control_passed": fake_mismatches == len(distinct_pairs),
        "source_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
    }
    print(json.dumps(info, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
