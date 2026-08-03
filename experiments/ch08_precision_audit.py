#!/usr/bin/env python3
"""Fail-closed source/linkage/config audit for Tusim Chapter 8 at e918c80."""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
HASHES = {
    "tu_cmodel/tu_precision.c": "d3180406590791d775911ea16960d54974b43abfee1f3b63a6c12a00066d50c7",
    "tu_cmodel/tu_precision.h": "937a20c3ac818ed81a72a60c53d34f524ac8aceccf8b7a2f6a51b9f634e8c60f",
    "tu_cmodel/rounding.c": "585fa23d2e7ec80499f2607fc4c389001e5dc1d84c818b651c74b1ed65388128",
    "tu_cmodel/rounding.h": "2b23801dd064620401a3a3fbc7cf702adb45374c225cdcca1a845cfde546a849",
    "tu_cmodel/fp8.c": "56871582464a671b2c05ecb5af4df23e5f00a123161220371a534cb3733ac393",
    "tu_cmodel/fp8.h": "ce141649283622e5cc6a6d9a54cd8683bc112673252448c41ac48af51d54250b",
    "tu_cmodel/tf32.c": "7145c1d97513325061ac284398be68544915f27ec068ae6e69f146f21d93ad57",
    "tu_cmodel/tf32.h": "534f5515a4b12a0d45e24ee5a949f454a05a0345a646324dafd521e634ba4533",
    "tu_cmodel/compute/dataflow/weight_stationary.c": "c421bd0845da1847b4e48a97c55f45dbbb058dc3a5af0e448d5fab422bd5b7e8",
    "tu_cmodel/compute/dataflow/output_stationary.c": "fa3a00c9b649b69dc8e92d562f044c49b129096c753ba169a855ba2e075dfaa0",
    "tu_cmodel/compute/dataflow/row_stationary.c": "ea86233c36fa1f076e0852204880f8d903bf546728478816df66b091e56feeaf",
    "tu_cmodel/infra/config.c": "17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
    "tests/test_bf16_subnormal.c": "e634470041ec234e0a709b179f84058e473c1bccc02b2307f9e7e52aa6e50934",
    "tests/test_rounding.c": "8dfed668645ba39ac1f35ed9363a8e99715d5c5767091833a51e14f81b14345e",
    "tests/test_fp8.c": "53cde9d9f839c7f65206a543e2be0a1eb1ce91f3761be1554acca0733752e949",
    "tests/test_tf32.c": "6b673613e60e0690137dfb319308fac3611338d4bc2ba81e123b76e9785e2134",
    "Makefile": "5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def text(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def main() -> None:
    require(len(sys.argv) == 3, "usage: ch08_precision_audit.py TREE REVISION")
    root = Path(sys.argv[1]).resolve()
    revision = sys.argv[2]
    require(revision == PIN, f"wrong revision argument: {revision}")
    marker = root / ".chapter-source-revision"
    require(marker.is_file() and marker.read_text().strip() == PIN, "missing/wrong extraction marker")

    for rel, expected in HASHES.items():
        data = (root / rel).read_bytes()
        got = hashlib.sha256(data).hexdigest()
        require(got == expected, f"hash drift {rel}: {got}")

    make = text(root, "Makefile")
    objs = re.search(r"TU_OBJS\s*=.*?(?=\n\n)", make, re.S)
    require(objs is not None, "TU_OBJS block missing")
    for obj in ("tu_precision.o", "rounding.o", "fp8.o", "tf32.o"):
        require(obj in objs.group(0), f"{obj} absent from library")

    aggregate = re.search(r"^test:.*?(?=\n\n)", make, re.M | re.S)
    require(aggregate is not None, "aggregate test target missing")
    for target in ("test-bf16", "test-rounding", "test-fp8"):
        require(target in aggregate.group(0), f"{target} absent from aggregate test")
    require("test-tf32" not in aggregate.group(0), "expected pinned omission of test-tf32 changed")
    test_full = re.search(r"^test-full:.*?(?=\n\n)", make, re.M | re.S)
    require(test_full is not None, "test-full target missing")
    require("test-compiler" in test_full.group(0) and "test-cmodel" not in test_full.group(0),
            "expected non-superset test-full contract changed")
    require(test_full.group(0).count("|| true") >= 2,
            "expected non-gating generated-code stages changed")

    config = text(root, "tu_cmodel/infra/config.c")
    for parsed in ("cfg->rounding_mode", "cfg->subnormal_flush", "cfg->fp16_enabled",
                   "cfg->bf16_enabled", "cfg->fp8_e4m3_enabled", "cfg->fp8_e5m2_enabled"):
        require(parsed in config, f"canonical parse field missing: {parsed}")
    conversion = re.search(r"tu_runtime_config_t tu_config_to_runtime.*?^}", config, re.M | re.S)
    require(conversion is not None, "config-to-runtime function missing")
    for dropped in ("rounding_mode", "subnormal_flush", "fp16_enabled", "bf16_enabled",
                    "fp8_e4m3_enabled", "fp8_e5m2_enabled", "saturate"):
        require(dropped not in conversion.group(0), f"expected dropped field now propagates: {dropped}")

    precision = text(root, "tu_cmodel/tu_precision.c")
    require("g_subnormal_mode = TU_SUBNORMAL_FLUSH" in precision, "FP16 default FTZ changed")
    require("{ TU_PREC_TF32, 4, \"tf32\"" in precision, "registry ordering changed")
    require("if (e <= 0)" in precision and "*(uint16_t *)dst = sign << 15" in precision,
            "BF16 subnormal flush path changed")
    require("if (prec < TU_PREC_COUNT) return &builtin_precisions[prec];" in precision,
            "expected negative precision-enum guard gap changed")

    fp8 = text(root, "tu_cmodel/fp8.c")
    require("if (exp == 0x0F)" in fp8 and "if (absv >= 240.0f)" in fp8,
            "E4M3 finite-range policy changed")
    require("(m_float + 0.5f)" in fp8, "FP8 tie-away implementation changed")
    require("if (im > 7) im = 7" in fp8 and "if (im > 3) im = 3" in fp8,
            "FP8 subnormal/normal clamp contract changed")

    local_files = [
        "tu_c_model/compute/dataflow/weight_stationary.c".replace("tu_c_model", "tu_cmodel"),
        "tu_cmodel/compute/dataflow/output_stationary.c",
        "tu_cmodel/compute/dataflow/row_stationary.c",
    ]
    helper_hits = 0
    for rel in local_files:
        src = text(root, rel)
        require("__builtin_clz(mantissa) - 21" in src, f"local subnormal converter changed: {rel}")
        require("float psum = 0.0f" in src and "O_fp32" in src, f"FP32 accumulation/storage contract changed: {rel}")
        helper_hits += 1
    require(helper_hits == 3, "expected exactly three audited engine-local converters")

    interface = text(root, "tu_cmodel/compute/dataflow/dataflow_interface.h")
    require("tu_dataflow_fp16_to_fp32" in interface and "tu_dataflow_fp32_to_fp16" in interface,
            "declared shared dataflow conversion seam changed")
    definitions = sum(text(root, rel).count("tu_dataflow_fp16_to_fp32") for rel in local_files)
    require(definitions == 0, "declared canonical dataflow decoder is now locally consumed")

    cmodel = text(root, "tu_cmodel/tu_cmodel.c")
    require("sizeof(fp16_t)" in cmodel and "sizeof(fp32_t)" in cmodel,
            "MMA W/A/O storage widths changed")

    print(f"SOURCE_AUDIT: PASS ({len(HASHES)}/{len(HASHES)} hashes)")
    print("LIBRARY: precision+rounding+fp8+tf32 objects present")
    print("AGGREGATE: bf16+rounding+fp8 included; tf32 omitted; test-full non-superset/non-gating")
    print("CONFIG: precision fields parse canonically but are dropped before runtime")
    print("ENGINE_LOCAL: 3 duplicated FP16 converters; declared shared seam unused; FP16 inputs and FP32 psum/O")


if __name__ == "__main__":
    main()
