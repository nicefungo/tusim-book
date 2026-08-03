#!/usr/bin/env python3
"""Fail-closed source/reachability audit for Chapter 13 at the frozen Tusim pin."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
PREDICATES = 0
HASHES = {
    "Makefile": "5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
    "tu_cmodel/tu_int_quant.h": "d513d63750c44fb2e07fa0a6d281ad76d43220beb0758399744538595c6fe600",
    "tu_cmodel/tu_int_quant.c": "7b20c382d4acb886ea59d82b539dec862e9f4d108e965550d3e98972fe38ba33",
    "tu_cmodel/sparsity/structured_2of4.h": "0eeaceb51cd43d6d751e783cc35b7ff016a9798e76706c8908eb4d955ca3c7c4",
    "tu_cmodel/sparsity/structured_2of4.c": "4111f8439780b83b312b6c80c83d1471d4e7e8d741defb3a671b83c8d0e83a05",
    "tu_cmodel/memory/weight_compress.h": "441d3ec539cfc88ef98367494d5d50350dd8af5ee44fcec37541e46565b94fcb",
    "tu_cmodel/memory/weight_compress.c": "26fa554d8b8a4e39b09ae27b6bb93720cc432e07a50f7936181eb7eab210c3eb",
    "tu_cmodel/infra/config.h": "723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
    "tu_cmodel/infra/config.c": "17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
    "tu_cmodel/tu_config.h": "129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
    "tu_cmodel/tu_cmodel.c": "542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
    "config/tu_config.json": "6f9d292696b1ca5fa38ad3298e7f3a04c43095c0950f71dbe0c3c68b1f15f4db",
    "config/tu_config.yaml": "9fb4d87753139a5857107a6fdf56006fcb5adbe95ad30e9f8430c2e5c145910e",
    "tests/test_int_quant.c": "6359be5c6141f869c6143a21a106967e94a70adeb6fd3dd3481df121d293b7ef",
    "tests/test_sparsity.c": "8d2e8a8e4fc17cea0abf569ecb49649cdf34abda763c635cd7955a8444d0c0af",
    "tests/test_compress.c": "3da4de233bf2b7f87e69eb529d6162064e1aa3f9bc2575e320b78c1b47478cac",
    "tests/test_weight_compression_sweep.c": "755ee98ba22775a8481e5ed60b4978e575e45d8a1882861a563e528d2f3065bd",
    "tests/test_sparsity_sweep.c": "15a3804334b5fb9cc108598b971d9dec897dc27e0db89d21cd541334ce7c21f4",
    "tests/test_int8_sweep.c": "fa4db1454b4fd24dc2c36d30b1268805d97216f55cb2641924cf0cded3ab2bf2",
    "tests/test_framework.h": "a8bf7f5e2e5ce9c317f1e089bc28338b4bd298a8bec6c08f40c6a5f12bb979ef",
    "docs/exploration/weight-decoder-throughput.md": "8300413868c6418ebdb4742b0c7e4ad8d39dea0680f00b969d38ddc60807357e",
    "docs/exploration/bitmap-weight-compression.md": "5232b44ae6089b8da5e56c90a91747e38ba609edeef2c0e9567bf481526bfc84",
    "docs/exploration/structured-2of4-sweep.md": "25299480d42a360b1ea20371d220b3bd2536d576fe573e36fbed65c0098dde28",
    "docs/exploration/weight-compression-rle-sweep.md": "71fcaa2b2ce6079622309a3a7d2b3a1b7d43a6fe8e27779dd49d21da002267b0",
    "docs/exploration/int8-quantization-throughput.md": "f647f7a2b260133cd789bc049f3076c04a8a05ee2171a795385781a42f001958",
}


def must(text: str, needle: str, label: str) -> None:
    global PREDICATES
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")
    PREDICATES += 1
    print(f"PREDICATE PASS {label}")


def must_not(text: str, needle: str, label: str) -> None:
    global PREDICATES
    if needle in text:
        raise AssertionError(f"{label}: unexpectedly found {needle!r}")
    PREDICATES += 1
    print(f"PREDICATE PASS {label}")


def pass_pred(label: str) -> None:
    global PREDICATES
    PREDICATES += 1
    print(f"PREDICATE PASS {label}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("pin")
    args = ap.parse_args()
    if args.pin != PIN:
        raise AssertionError(f"pin mismatch: {args.pin}")
    root = args.root.resolve()

    texts: dict[str, str] = {}
    for rel, expected in HASHES.items():
        data = (root / rel).read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise AssertionError(f"hash mismatch {rel}: {actual}")
        texts[rel] = data.decode("utf-8")
        print(f"HASH PASS {rel} {actual}")

    mk = texts["Makefile"]
    iq = texts["tu_cmodel/tu_int_quant.c"]
    iq_h = texts["tu_cmodel/tu_int_quant.h"]
    s24 = texts["tu_cmodel/sparsity/structured_2of4.c"]
    s24_h = texts["tu_cmodel/sparsity/structured_2of4.h"]
    wc = texts["tu_cmodel/memory/weight_compress.c"]
    wc_h = texts["tu_cmodel/memory/weight_compress.h"]
    full_cfg = texts["tu_cmodel/infra/config.c"]
    cfg_h = texts["tu_cmodel/infra/config.h"]
    runtime_cfg = texts["tu_cmodel/tu_config.h"]
    shipped_json = texts["config/tu_config.json"]
    shipped_yaml = texts["config/tu_config.yaml"]
    test_iq = texts["tests/test_int_quant.c"]
    test_s24 = texts["tests/test_sparsity.c"]
    test_wc = texts["tests/test_compress.c"]
    sweep_wc = texts["tests/test_weight_compression_sweep.c"]
    sweep_s24 = texts["tests/test_sparsity_sweep.c"]
    sweep_i8 = texts["tests/test_int8_sweep.c"]
    decoder_doc = texts["docs/exploration/weight-decoder-throughput.md"]
    bitmap_doc = texts["docs/exploration/bitmap-weight-compression.md"]
    s24_doc = texts["docs/exploration/structured-2of4-sweep.md"]
    rle_doc = texts["docs/exploration/weight-compression-rle-sweep.md"]
    i8_doc = texts["docs/exploration/int8-quantization-throughput.md"]

    # ---- Archive membership and Makefile targets ----
    for obj in ["tu_int_quant.o", "sparsity/structured_2of4.o", "memory/weight_compress.o"]:
        must(mk, obj, f"archive-member-{obj.replace('/', '-')}")
    for target in ["test-int-quant:", "test-sparsity:", "test-compress:",
                   "test-weight-compression-sweep:", "test-sparsity-sweep:"]:
        must(mk, target, f"focused-target-{target.rstrip(':')}")
    aggregate = mk[mk.index("test: test-cmodel"):mk.index("test-quick:")]
    must(aggregate, "test-int-quant", "aggregate-includes-int-quant")
    must(aggregate, "test-sparsity", "aggregate-includes-sparsity")
    must_not(aggregate, "test-compress", "aggregate-excludes-compress")
    must_not(aggregate, "test-weight-compression-sweep", "aggregate-excludes-weight-sweep")
    must_not(aggregate, "test-sparsity-sweep", "aggregate-excludes-sparsity-sweep")
    must_not(aggregate, "test-int8-sweep", "aggregate-excludes-int8-sweep")
    must_not(mk, "test-int8-sweep:", "no-makefile-target-for-int8-sweep")

    # ---- INT/UINT quantization ----
    must(iq_h, "typedef int8_t   int8_t_t;", "quant-int8-type")
    must(iq_h, "low nibble first", "quant-uint4-nibble-order")
    must(iq_h, "real_value = (q - zero_point) * scale", "quant-affine-formula")
    must(iq_h, "#define TU_INT8_QMAX         127", "quant-int8-range")
    must(iq_h, "#define TU_UINT4_QMAX        15", "quant-uint4-range")
    must(iq_h, "0.007874016f", "quant-int8-default-scale")
    must(iq_h, "0.06666667f", "quant-uint4-default-scale")
    must(iq_h, "tu_int8_mma_tile", "quant-mma-tile-declared")
    must(iq, "roundf(v / qp->scale) + (float)qp->zero_point", "quant-int8-round-then-shift")
    must(iq, "clamp_i32((int32_t)scaled, qp->qmin, qp->qmax)", "quant-int8-clamp")
    must(iq, "amax / 127.0f", "quant-symmetric-scale-amax-over-127")
    must(iq, "amax = 1.0f; /* all zeros", "quant-all-zero-guard")
    must(iq, "(index % 2 == 0) ? (byte & 0x0F) : ((byte >> 4) & 0x0F)", "quant-nibble-unpack")
    must(iq, "packed[bi] = (packed[bi] & 0xF0) | (nibble & 0x0F);", "quant-nibble-pack-low")
    must(iq, "packed[bi] = (packed[bi] & 0x0F) | ((nibble & 0x0F) << 4);", "quant-nibble-pack-high")
    must_not(iq, "tu_config_to_runtime", "quant-standalone-no-runtime-conversion")
    must_not(iq, "tu_sparsity_2of4", "quant-standalone-no-sparsity")

    # ---- Structured 2:4 ----
    must(s24_h, "exactly 2 are non-zero", "sparsity-2of4-contract")
    must(s24_h, "#define TU_2OF4_GROUP_SIZE       4", "sparsity-group-size")
    must(s24_h, "#define TU_2OF4_NONZEROS         2", "sparsity-nonzeros")
    must(s24_h, "TU_2OF4_NUM_VALID_MASKS  6", "sparsity-six-valid-masks")
    must(s24_h, "tu_sparsity_2of4_mask_is_valid", "sparsity-mask-validity")
    must(s24_h, "tu_sparsity_2of4_mma_fp16", "sparsity-mma-declared")
    must(s24_h, "tu_sparsity_2of4_estimate_cycles", "sparsity-estimator-declared")
    must(s24_h, "DMA and compute are\n * serialized; metadata decode overlaps sparse compute", "sparsity-overlap-assumption")
    est = s24[s24.index("bool tu_sparsity_2of4_estimate_cycles"):s24.index("bool tu_sparsity_2of4_verify_pattern")]
    for needle, label in [
        ("K % TU_2OF4_GROUP_SIZE != 0", "sparsity-estimator-k-divisible"),
        ("cfg->sparsity_decoder_groups_per_cycle == 0", "sparsity-estimator-zero-decoder-guard"),
        ("cfg->pe_rows == 0", "sparsity-estimator-pe-guard"),
        ("stats->sparse_macs = stats->dense_macs / 2u;", "sparsity-halved-macs"),
        ("stats->sparse_weight_bytes = groups * (2u * sizeof(fp16_t) + 1u);", "sparsity-packed-weight-bytes"),
        ("stats->sparse_decode_cycles = ceil_div_u64(\n        groups, cfg->sparsity_decoder_groups_per_cycle);", "sparsity-decode-cycles"),
        ("stats->sparse_total_cycles = stats->sparse_dma_cycles + sparse_core;", "sparsity-total-with-overlap-core"),
        ("stats->selected_2of4 = cfg->sparsity_enabled && cfg->sparsity_2of4;", "sparsity-selection-flag"),
    ]:
        must(est, needle, label)
    must_not(est, "queue", "sparsity-estimator-no-queues")

    # ---- Weight compression ----
    must(wc_h, "TU_WEIGHT_FRAME_MAGIC       UINT32_C(0x54555743)", "compress-frame-magic")
    must(wc_h, "TU_WEIGHT_FRAME_VERSION     1u", "compress-frame-version")
    must(wc_h, "TU_WEIGHT_FRAME_HEADER_BYTES 16u", "compress-frame-header-bytes")
    must(wc_h, "TU_COMPRESS_RLE          = 1", "compress-rle-enum")
    must(wc_h, "TU_COMPRESS_BITMAP       = 3", "compress-bitmap-enum")
    must(wc_h, "TU_COMPRESS_ADAPTIVE     = 4", "compress-adaptive-enum")
    must(wc_h, "padding never enters the stream", "compress-rle-no-padding")
    must(wc_h, "element_count:u32, nonzero_count:u32", "compress-bitmap-header")
    must(wc_h, "raw wins\n * ties", "compress-adaptive-raw-ties")
    must(wc_h, "tu_compress_config_from_tu_config", "compress-config-mapper")
    must(wc_h, "tu_compress_estimate_cycles", "compress-estimator-declared")
    must(wc_h, "decoder_bound", "compress-decoder-bound-field")
    est_wc = wc[wc.index("int tu_compress_estimate_cycles"):]
    must(est_wc, "dma_bus_width_bits % 8u != 0", "compress-estimator-bus-width-guard")
    must(est_wc, "stats->dma_cycles = ceil_div_u64(size, dma_bus_width_bits / 8u);", "compress-payload-dma-cycles")
    must(est_wc, "stats->decode_cycles = output > metadata ? output : metadata;", "compress-decode-max")
    must(est_wc, "stats->decoder_bound = stats->decode_cycles > stats->dma_cycles;", "compress-decoder-bound-classifier")
    must(est_wc, "stats->total_cycles = cfg->decoder_overlap_dma ?", "compress-overlap-total")
    must(est_wc, "stats->dma_cycles + stats->decode_cycles;", "compress-serial-total")
    validate = wc[wc.index("bool tu_compress_validate("):wc.index("bool tu_compress_bitmap_validate")]
    must(validate, "size == 8u + runs * TU_RLE_RUN_BYTES", "compress-validate-exact-size")
    must(validate, "runs > n", "compress-validate-runs-bound")

    # ---- Configuration plumbing ----
    for field, label in [
        ("compression_enabled", "config-full-declares-compression-enabled"),
        ("compression_type", "config-full-declares-compression-type"),
        ("compression_decoder_elements_per_cycle", "config-full-declares-decoder-width"),
        ("sparsity_enabled", "config-full-declares-sparsity-enabled"),
        ("sparsity_2of4", "config-full-declares-sparsity-2of4"),
        ("sparsity_decoder_groups_per_cycle", "config-full-declares-sparsity-decoder"),
    ]:
        must(cfg_h, field, label)
    for field, label in [
        ("compression_enabled", "runtime-config-excludes-compression-enabled"),
        ("compression_type", "runtime-config-excludes-compression-type"),
        ("sparsity_enabled", "runtime-config-excludes-sparsity-enabled"),
        ("sparsity_2of4", "runtime-config-excludes-sparsity-2of4"),
    ]:
        must_not(runtime_cfg, field, label)
    converter = full_cfg[full_cfg.index("tu_runtime_config_t tu_config_to_runtime"):full_cfg.index("/* ---- Load from JSON string ----")]
    for field in ["compression_enabled", "compression_type", "sparsity_enabled", "sparsity_2of4",
                  "sparsity_decoder_groups_per_cycle"]:
        must_not(converter, field, f"runtime-converter-drops-{field}")
    for field in ["pe_rows", "pe_cols", "icc_switching_mode", "icc_router_latency_cycles"]:
        must(converter, f"rt.{field}", f"runtime-converter-retains-{field}")
    must(full_cfg, 'parse_opt_bool(wc, "enabled", &cfg->compression_enabled);', "config-parses-compression-enabled")
    must(full_cfg, 'strcmp(s, "adaptive") == 0) cfg->compression_type = 4;', "config-parses-adaptive-type")
    must(full_cfg, 'parse_opt_bool(sp, "enabled", &cfg->sparsity_enabled);', "config-parses-sparsity-enabled")
    must(full_cfg, 'parse_opt_bool(sp, "structured_2of4", &cfg->sparsity_2of4);', "config-parses-sparsity-2of4")
    for needle, label in [
        ("weight compression type must be none, rle, adaptive_rle, bitmap, or adaptive", "config-validates-compression-type"),
        ("unstructured sparsity is not implemented", "config-validates-unstructured-rejected"),
        ("enabled sparsity requires structured_2of4=true", "config-validates-enabled-requires-2of4"),
        ("structured_2of4 requires sparsity enabled", "config-validates-2of4-requires-enabled"),
        ("sparsity decoder_groups_per_cycle must be > 0", "config-validates-decoder-nonzero"),
    ]:
        must(full_cfg, needle, label)
    wc_block = json.loads(shipped_json)["tu"]["weight_compression"]
    if wc_block != {"enabled": False, "type": "none", "rle_epsilon": 0.0,
                    "decoder_enabled": False, "decoder_overlap_dma": True,
                    "decoder_elements_per_cycle": 1, "rle_runs_per_cycle": 1,
                    "bitmap_elements_per_cycle": 1}:
        raise AssertionError(f"shipped JSON weight_compression mismatch: {wc_block}")
    pass_pred("json-complete-weight-compression-defaults")
    sp_block = json.loads(shipped_json)["tu"]["sparsity"]
    if sp_block != {"enabled": False, "structured_2of4": False, "unstructured": False,
                    "metadata_format": "bitmask", "decoder_groups_per_cycle": 1}:
        raise AssertionError(f"shipped JSON sparsity mismatch: {sp_block}")
    pass_pred("json-complete-sparsity-defaults")
    for line in ["enabled: false", "structured_2of4: false",
                 "decoder_groups_per_cycle: 1"]:
        must(shipped_yaml, line, f"yaml-weight-path-{line.split(':', 1)[0].strip()}")
    must_not(shipped_yaml, "weight_compression", "yaml-omits-weight-compression-block")

    # ---- Focused tests: fail-closed exits and discriminating assertions ----
    must(test_iq, "return (tests_pass == tests_run) ? 0 : 1;", "int-quant-fail-closed-exit")
    must(test_iq, "test_int8_mma_tile();", "int-quant-exercises-mma-tile")
    iq_calls = re.findall(r"^    (test_[a-z0-9_]+)\(\);$", test_iq, re.MULTILINE)
    if len(iq_calls) != 14 or len(set(iq_calls)) != 14:
        raise AssertionError(f"int-quant main test calls: {iq_calls}")
    pass_pred("int-quant-14-distinct-test-calls")
    must(test_s24, "return tests_failed > 0 ? 1 : 0;", "sparsity-fail-closed-exit")
    must(test_s24, "tu_sparsity_2of4_estimate_cycles", "sparsity-test-exercises-estimator")
    must(test_s24, "tu_sparsity_2of4_mma_fp16", "sparsity-test-exercises-mma")
    s24_calls = re.findall(r'TEST\("[^"]+"\)', test_s24)
    if len(s24_calls) != 27 or len(set(s24_calls)) != 27:
        raise AssertionError(f"sparsity TEST names: {s24_calls}")
    pass_pred("sparsity-27-distinct-tests")
    must(test_wc, "return test_exit();", "compress-fail-closed-exit")
    wc_calls = re.findall(r'TEST\("[^"]+"\)', test_wc)
    if len(wc_calls) != 24 or len(set(wc_calls)) != 24:
        raise AssertionError(f"compress TEST names: {wc_calls}")
    pass_pred("compress-24-distinct-tests")
    for needle, label in [
        ("test_adaptive_all_selects_realistic_modes();", "compress-adaptive-all-modes-test"),
        ("test_decoder_cycle_profiles();", "compress-decoder-profiles-test"),
        ("test_bitmap_and_adaptive_cycle_model();", "compress-bitmap-adaptive-cycles-test"),
    ]:
        must(test_wc, needle, label)

    # ---- Sweeps: linkage classification ----
    must(sweep_wc, '#include "tu_cmodel/memory/weight_compress.h"', "weight-sweep-links-codec")
    must(sweep_wc, "tu_compress_estimate_cycles", "weight-sweep-calls-estimator")
    must(sweep_s24, '#include "tu_cmodel/sparsity/structured_2of4.h"', "sparsity-sweep-links-module")
    must(sweep_s24, "tu_sparsity_2of4_estimate_cycles", "sparsity-sweep-calls-estimator")
    must_not(sweep_i8, "#include \"tu_cmodel", "int8-sweep-no-cmodel-include")
    must_not(sweep_i8, "tu_cmodel", "int8-sweep-no-cmodel-dependency")
    must(i8_doc, "Analytical cycle model", "int8-doc-analytical-label")
    must(decoder_doc, "payload-only measurements overstate compression speedups", "decoder-doc-payload-only-overstates")
    must(decoder_doc, "matching that width should at best recover raw latency", "decoder-doc-bus-width-breaks-even")
    must(bitmap_doc, "placement-independent metadata", "bitmap-doc-placement-independent")
    must(s24_doc, "metadata decoder", "sparsity-doc-decoder-requirement")
    must(rle_doc, "adaptive", "rle-doc-adaptive-framing")

    # ---- Exact C caller inventories ----
    def c_callers(pattern: str) -> set[str]:
        rx = re.compile(pattern)
        def without_comments(body: str) -> str:
            body = re.sub(r"/\*.*?\*/", "", body, flags=re.DOTALL)
            return re.sub(r"//.*", "", body)
        return {
            p.relative_to(root).as_posix()
            for p in root.rglob("*.c")
            if rx.search(without_comments(p.read_text(encoding="utf-8")))
        }

    inventories = [
        (r"tu_compress_estimate_cycles\(", {
            "tu_cmodel/memory/weight_compress.c", "tests/test_compress.c",
            "tests/test_weight_compression_sweep.c"},
         "exact-c-callers-compress-estimator"),
        (r"tu_sparsity_2of4_estimate_cycles\(", {
            "tu_cmodel/sparsity/structured_2of4.c", "tests/test_sparsity.c",
            "tests/test_sparsity_sweep.c"},
         "exact-c-callers-sparsity-estimator"),
        (r"tu_compress_config_from_tu_config\(", {
            "tu_cmodel/memory/weight_compress.c", "tests/test_compress.c"},
         "exact-c-callers-compress-config-mapper"),
        (r"tu_int8_mma_tile\(", {
            "tu_cmodel/tu_int_quant.c", "tests/test_int_quant.c"},
         "exact-c-callers-int8-mma-tile"),
        (r"tu_int8_dot_product\(", {
            "tu_cmodel/tu_int_quant.c", "tests/test_int_quant.c"},
         "exact-c-callers-int8-dot-product"),
        (r"tu_sparsity_2of4_mma_fp16\(", {
            "tu_cmodel/sparsity/structured_2of4.c", "tests/test_sparsity.c"},
         "exact-c-callers-sparsity-mma"),
        (r"tu_compress_for_dma\(", {
            "tu_cmodel/memory/weight_compress.c", "tests/test_compress.c"},
         "exact-c-callers-compress-for-dma"),
    ]
    for pattern, expected, label in inventories:
        actual = c_callers(pattern)
        if actual != expected:
            raise AssertionError(f"{label}: expected={sorted(expected)} actual={sorted(actual)}")
        pass_pred(label)

    # Direct MMA path must not call any weight-stream helper.
    direct = texts["tu_cmodel/tu_cmodel.c"]
    for needle in ["tu_compress_", "tu_sparsity_2of4_", "tu_int8_", "tu_fp32_to_int8"]:
        must_not(direct, needle, f"direct-mma-avoids-{needle.rstrip('_')}")

    print(f"CH13_SOURCE_AUDIT PASS pin={PIN} hashes={len(HASHES)} predicates={PREDICATES} checks={len(HASHES) + PREDICATES}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"CH13_SOURCE_AUDIT FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
