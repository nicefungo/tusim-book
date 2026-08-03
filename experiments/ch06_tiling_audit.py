#!/usr/bin/env python3
"""Enforced geometry/capacity audit for Tusim book Chapter 6.

Run with a clean archived Tusim tree as the only argument. This script checks the
pinned revision and source hashes, then emits analytical tile/capacity cases.
The slot-utilization metric is a book derivation, not a Tusim runtime counter.
"""
from __future__ import annotations

import hashlib
import math
import pathlib
import sys

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
HASHES = {
    "tu_cmodel/tu_cmodel.c": "542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
    "tu_cmodel/compute/dataflow/dataflow_dispatcher.c": "f09af46670bc8a3bee49be6c639bc27a432a085109684e0f4f73b4f471b9a6f4",
    "tu_cmodel/compute/dataflow/weight_stationary.c": "c421bd0845da1847b4e48a97c55f45dbbb058dc3a5af0e448d5fab422bd5b7e8",
    "tu_cmodel/tu_cmodel.h": "416a0d20776825498217ff5d4382f07ccb2ac9689bbe6c70cacd1bf13e7725af",
    "tu_cmodel/tu_config.h": "129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
    "tests/test_cmodel.c": "a7609fe22a113c0d9f2807ab3b76c7be29bbc2ed3822a3cfea82c2109862b36c",
    "tests/test_dataflow.c": "c26b74c35e50e5231c193835f4d3ccc00146bc08548e3e52d6a50f50f6c9db43",
    "scripts/sweep_aspect_ratio.py": "7e4f8207c3ec3854f3efb3a3caa02bbd48856d9ea5608198f596c11d79948db2",
}


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tile_case(M: int, N: int, K: int, rows: int, cols: int) -> tuple[int, int, float]:
    mt, nt, kt = math.ceil(M / rows), math.ceil(N / cols), math.ceil(K / cols)
    tiles = mt * nt * kt
    # Pinned WS plug-in defaults to pd=2. The dispatcher charges configured
    # tile_n/tile_m for edge fill/drain and actual k_count for compute.
    cycles = mt * nt * (kt * (2 * cols + 2 * rows) + K)
    slot_util = (M * N * K) / (tiles * rows * cols * cols)
    return tiles, cycles, slot_util


def capacities(M: int, N: int, K: int) -> tuple[int, int, int, int]:
    return 2 * M * K, 2 * K * N, 4 * M * N, 2 * M * N


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} /path/to/archived-tusim COMMIT", file=sys.stderr)
        return 2
    root = pathlib.Path(sys.argv[1]).resolve()
    head = sys.argv[2]
    if head != PIN:
        raise SystemExit(f"revision argument drift: {head} != {PIN}")
    for rel, expected in HASHES.items():
        actual = digest(root / rel)
        if actual != expected:
            raise SystemExit(f"hash drift: {rel}: {actual} != {expected}")
    print(f"pin: {head}")
    print(f"source_hashes: PASS ({len(HASHES)}/{len(HASHES)})")

    cases = [
        (9, 9, 9, 4, 8),
        (9, 9, 9, 16, 16),
        (4, 32, 16, 8, 8),
        (4, 32, 16, 4, 16),
        (9, 9, 8, 8, 8),
        (9, 9, 8, 16, 16),
        (16, 16, 16, 16, 16),
        (16, 16, 16, 32, 32),
        (16, 16, 16, 64, 64),
        (31, 17, 23, 16, 16),
    ]
    print("case M N K rows cols tiles ws_cycles slot_util")
    for case in cases:
        tiles, cycles, util = tile_case(*case)
        print("case", *case, tiles, cycles, f"{util:.6f}")

    print("capacity M N K W_bytes A_bytes O_fp32_bytes bias_fp16_payload_bytes")
    for M, N, K in [(2, 3, 2), (31, 17, 23), (128, 128, 128), (256, 256, 256)]:
        print("capacity", M, N, K, *capacities(M, N, K))

    # Default capacities are W=128 KiB, A=64 KiB, O=64 KiB. Whole operands,
    # not individual tiles, must be resident in the current tu_mma path.
    default = (128 * 1024, 64 * 1024, 64 * 1024)
    feasible_128 = capacities(128, 128, 128)
    infeasible_256 = capacities(256, 256, 256)
    assert feasible_128[0] <= default[0] and feasible_128[1] <= default[1] and feasible_128[2] <= default[2]
    assert infeasible_256[0] <= default[0] and infeasible_256[1] > default[1] and infeasible_256[2] > default[2]
    assert tile_case(4, 32, 16, 4, 16)[2] > tile_case(4, 32, 16, 8, 8)[2]
    assert tile_case(9, 9, 8, 16, 16)[2] < tile_case(9, 9, 8, 8, 8)[2]
    assert tile_case(16, 16, 16, 16, 16)[1] < tile_case(16, 16, 16, 32, 32)[1] < tile_case(16, 16, 16, 64, 64)[1]
    print("enforced_invariants: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
