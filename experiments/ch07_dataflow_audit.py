#!/usr/bin/env python3
"""Enforced source/formula audit for Chapter 7 at Tusim e918c80."""
from __future__ import annotations
import hashlib
import math
import pathlib
import re
import sys

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
ARCHIVE_SHA256 = "fb023fe79a0e7dafbf334848756e44127101f5fdb75c1004e2ed2712318b708f"
HASHES = {
    "tu_cmodel/compute/dataflow/dataflow_interface.h": "141bdd26c5e436d38095296e824a93761ac4b74edaed9b7482ef7c8eca5ebf77",
    "tu_cmodel/compute/dataflow/dataflow_registry.c": "56b4fcab5e736eb1fd55a02cdeaefd20504a708a7cea6012c8c819e25bc24d27",
    "tu_cmodel/compute/dataflow/dataflow_dispatcher.c": "f09af46670bc8a3bee49be6c639bc27a432a085109684e0f4f73b4f471b9a6f4",
    "tu_cmodel/compute/dataflow/weight_stationary.c": "c421bd0845da1847b4e48a97c55f45dbbb058dc3a5af0e448d5fab422bd5b7e8",
    "tu_cmodel/compute/dataflow/output_stationary.c": "fa3a00c9b649b69dc8e92d562f044c49b129096c753ba169a855ba2e075dfaa0",
    "tu_cmodel/compute/dataflow/row_stationary.c": "ea86233c36fa1f076e0852204880f8d903bf546728478816df66b091e56feeaf",
    "tu_cmodel/tu_cmodel.c": "542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
    "tu_cmodel/tu_config.h": "129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
    "tu_cmodel/infra/config.c": "17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
    "tu_cmodel/tu_core.c": "0e4b3c6e206465748ae2d3d2e9871f3a6542a61cd1ddcddfff6886b9ed1f0eeb",
    "tu_cmodel/perf/performance_counters.c": "f7d9a5ec33c873cb4c900902d3c8d168622be782a8979cc6a822211c471807f2",
    "tu_cmodel/perf/performance_counters.h": "5d323e9af226f2012c71eb4cc5fe917edc9a5cdd314782affeb9de3e21fdf6b5",
    "tests/test_dataflow.c": "c26b74c35e50e5231c193835f4d3ccc00146bc08548e3e52d6a50f50f6c9db43",
    "tests/test_dataflow_sweep.c": "4b3dc2da732f4efa25ec250bfb76e3507bd07168a73a703350150228077f57e6",
    "Makefile": "5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
}

def require(text: str, pattern: str, label: str) -> None:
    if not re.search(pattern, text, re.MULTILINE | re.DOTALL):
        raise SystemExit(f"contract check failed: {label}")

def cycles(df: str, m: int, n: int, k: int, r: int, c: int) -> int:
    mt, nt, kt = math.ceil(m / r), math.ceil(n / c), math.ceil(k / c)
    total = 0
    for ki in range(kt):
        kc = min(c, k - ki * c)
        if df == "WS": total += 2*c + kc + 2*r
        elif df == "OS": total += kc + math.ceil(kc / 4)
        else: total += c + 1 + kc + r
    return mt * nt * total

def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: ch07_dataflow_audit.py TUSIM_ARCHIVE PIN")
    root = pathlib.Path(sys.argv[1]).resolve()
    if sys.argv[2] != PIN:
        raise SystemExit(f"pin mismatch: expected {PIN}")
    marker = root / ".tusim-archive-sha256"
    if not marker.is_file() or marker.read_text().strip() != ARCHIVE_SHA256:
        raise SystemExit("missing or incorrect complete source-archive provenance marker")
    for rel, expected in HASHES.items():
        got = hashlib.sha256((root / rel).read_bytes()).hexdigest()
        if got != expected:
            raise SystemExit(f"hash mismatch {rel}: {got}")

    iface = (root / "tu_cmodel/compute/dataflow/dataflow_interface.h").read_text()
    disp = (root / "tu_cmodel/compute/dataflow/dataflow_dispatcher.c").read_text()
    ws = (root / "tu_cmodel/compute/dataflow/weight_stationary.c").read_text()
    os_ = (root / "tu_cmodel/compute/dataflow/output_stationary.c").read_text()
    rs = (root / "tu_cmodel/compute/dataflow/row_stationary.c").read_text()
    model = (root / "tu_cmodel/tu_cmodel.c").read_text()
    compile_config = (root / "tu_cmodel/tu_config.h").read_text()
    config = (root / "tu_cmodel/infra/config.c").read_text()
    core = (root / "tu_cmodel/tu_core.c").read_text()
    perf = (root / "tu_cmodel/perf/performance_counters.c").read_text()
    make = (root / "Makefile").read_text()

    require(iface, r"TU_DATAFLOW_NO_LOCAL_REUSE\s*=\s*3", "NLR declared")
    require(model, r"register\(tu_dataflow_ws_create\(\)\).*register\(tu_dataflow_os_create\(\)\).*register\(tu_dataflow_rs_create\(\)\)", "only WS/OS/RS registered")
    require(model, r"tu_set_dataflow\(TU_DATAFLOW_MODE\)", "init selects compile-time mode")
    require(compile_config, r"TU_DATAFLOW_MODE\s+TU_DATAFLOW_MODE_WS", "compile-time default is WS")
    require(compile_config, r"TU_DATAFLOW_DISPATCH_VIA_PLUGIN\s+1", "plugin dispatch is compile-time enabled")
    require(config, r"cfg->dataflow_mode\s*=\s*parse_dataflow_str", "JSON parses dataflow")
    conversion = re.search(r"tu_config_to_runtime.*?return rt;", config, re.DOTALL)
    if not conversion or "dataflow_mode" in conversion.group(0):
        raise SystemExit("contract check failed: dataflow unexpectedly reaches runtime config")
    require(disp, r"get_fill_cycles.*?execute_tile.*?get_drain_cycles", "dispatcher timing order")
    if "get_compute_cycles(plugin" in disp:
        raise SystemExit("contract check failed: dispatcher unexpectedly calls compute callback")
    require(ws, r"return \(uint64_t\)k_count", "WS execute return")
    require(os_, r"return \(uint64_t\)k_count \+ \(k_count \+ 3\) / 4", "OS execute return")
    require(rs, r"return \(uint64_t\)k_count", "RS execute return")
    for text, name in [(ws, "WS"), (os_, "OS"), (rs, "RS")]:
        require(text, r"__builtin_clz\(mantissa\) - 21", f"{name} local subnormal converter")
    require(core, r"tu_core_mma.*?core_swap_in\(core.*?tu_mma", "core swap overrides process-global state")
    require(perf, r"if \(dataflow_mode == 0\).*?df_ws_cycles.*?else.*?df_os_cycles", "standalone perf collapses non-WS modes into OS")
    require(make, r"test-dataflow:.*?libtucmodel\.a.*?-L\. -ltucmodel", "focused target link mode")
    require(make, r"test:.*?test-dataflow", "focused suite in aggregate test")
    aggregate = re.search(r"^test:.*?(?=^\S|\Z)", make, re.MULTILINE | re.DOTALL)
    if aggregate and "test-dataflow-sweep" in aggregate.group(0):
        raise SystemExit("contract check failed: sweep unexpectedly in aggregate test")

    print(f"pin: {PIN}")
    print(f"source_archive_sha256: PASS ({ARCHIVE_SHA256})")
    print(f"source_hashes: PASS ({len(HASHES)}/{len(HASHES)})")
    print("shape pe tiles flops ws_cycles os_cycles rs_cycles")
    for m,n,k,r,c in [(2,3,2,4,8),(9,10,9,4,8),(5,17,19,4,8),(31,31,17,16,16)]:
        tiles = math.ceil(m/r)*math.ceil(n/c)*math.ceil(k/c)
        print(f"{m}x{n}x{k} {r}x{c} {tiles} {2*m*n*k} "
              f"{cycles('WS',m,n,k,r,c)} {cycles('OS',m,n,k,r,c)} {cycles('RS',m,n,k,r,c)}")
    print("contracts: PASS")

if __name__ == "__main__":
    main()
