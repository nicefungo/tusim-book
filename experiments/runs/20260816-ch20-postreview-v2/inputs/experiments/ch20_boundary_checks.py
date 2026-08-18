#!/usr/bin/env python3
"""Executable report/binding boundary discriminators for Chapter 20."""
from __future__ import annotations
import importlib.util
import math
import os
from pathlib import Path
import sys
import tempfile


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: ch20_boundary_checks.py ARCHIVE", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    report = load("ch20_report", root / "tools/test_report.py")
    with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
        f.write("  case_a  FAIL\ncleanup PASS\n")
        log = Path(f.name)
    try:
        parsed = report.parse_test_log(str(log))
    finally:
        log.unlink()
    print(f"REPORT_FALSE_GREEN status={parsed['status']} passed={parsed['passed']} failed={parsed['failed']} exit_code={parsed['exit_code']}")
    if not (parsed["status"] == "PASS" and parsed["failed"] == 1 and parsed["exit_code"] == -1):
        return 3

    prior = Path.cwd()
    try:
        os.chdir(root)
        binding = load("ch20_binding", root / "bindings/python/tu_bindings.py")
        left = [[1.0, 2.0], [3.0, 4.0]]
        right = [[5.0, 6.0], [7.0, 8.0]]
        observed = binding.quick_gemm(left, right)
    finally:
        os.chdir(prior)
    expected = [[19.0, 22.0], [43.0, 50.0]]
    if os.environ.get("CH20_MUTATE_BINDING_EXPECTED") == "1":
        expected[0][0] += 1.0
    shape_ok = len(observed) == 2 and all(len(row) == 2 for row in observed)
    finite = shape_ok and all(math.isfinite(x) for row in observed for x in row)
    residual = max(abs(observed[i][j] - expected[i][j]) for i in range(2) for j in range(2)) if shape_ok else math.inf
    print(f"BINDING_NONSYMMETRIC shape_ok={int(shape_ok)} finite={int(finite)} max_abs={residual:.9g} observed={observed}")
    if not (shape_ok and finite and residual <= 1e-6):
        print("CH20_BOUNDARY_CHECKS REJECT")
        return 4
    print("CH20_BOUNDARY_CHECKS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
