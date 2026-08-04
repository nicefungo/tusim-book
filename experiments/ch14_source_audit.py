#!/usr/bin/env python3
"""Chapter 14 fail-closed source audit for the Tusim operator compute engines.

Pin: e918c80b6fce833cd1fcae97730fa841c2176f25 (stable-main snapshot).
Run:  python3 ch14_source_audit.py <WORK> <PIN>
Returns nonzero on any drift: hash mismatch, missing symbol, reachability or
test-membership predicate violation. Prints the canonical PASS line:
  CH14_SOURCE_AUDIT PASS pin=... hashes=N predicates=M checks=K
"""
import hashlib
import re
import sys
from pathlib import Path

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"

# --- Pin-locked SHA-256 (computed at seal time from the pinned tree) ---
HASHES = {
    "tu_cmodel/compute/convolution_engine.c": "abaab2bfc6fce099420d7bcb1b5edf2ae2ddbeebdd4578f64239bc2e818163c2",
    "tu_cmodel/compute/softmax_engine.c": "ea49a0786ed7522591ec90f135e87027ae57db91cfabc030eccc3fb0407a6e67",
    "tu_cmodel/compute/attention_engine.c": "73f291d886fe9bfe730a71c7af9ea913789003cea28be75464e42ff55c87b74e",
    "tu_cmodel/compute/normalization_engine.c": "4ac8bb8fa4414fc9f3d976b48c5df2a28137cc791948e7f8ab69ee5830902955",
    "tu_cmodel/compute/pooling_engine.c": "c172ad9e8aa00769b2a27471f1698ad72ae16834b1d833489a5a43f48c439be9",
    "tu_cmodel/compute/elementwise_pipeline.c": "e46a698f48bb69ac577b11ff866b4c34953a2ca03e2194bee85558cea4f656e2",
    "tu_cmodel/compute/pipeline_controller.c": "165522ae3a7853189ed0f6ea114f3e5079487593fb1c06b42a877df53fa1b493",
    "tu_cmodel/compute/convolution_engine.h": "2f92817dfc322d15f592743f00df339e54d613949d37659eee329baaddb8e8a5",
    "tu_cmodel/compute/softmax_engine.h": "229303e46fd97ede8e6a9c7ed10ae50eb1261a4bfd0e5c31ed230f84e2697f5d",
    "tu_cmodel/compute/attention_engine.h": "17f20ebd6896db25a6f6dd73449c6f826da976b203d87cfb1d3323ee8eb36b22",
    "tu_cmodel/compute/normalization_engine.h": "afeb902f7d567d77b7e576fd5c4048a7440a1d5d0f8e66d7a7ca45cb52c34ad8",
    "tu_cmodel/compute/pooling_engine.h": "cd03f0b3de65e067e51778a9002b1ef509251bee7d09a2c81aa4817e1b2c6ff0",
    "tu_cmodel/compute/elementwise_pipeline.h": "35cfaa8d163fd32dc8cdc31b64e340fb36e7baeff8ed6a4af6fc0cbb62ac2add",
    "tu_cmodel/compute/pipeline_controller.h": "39dc3e73b07b2be30aed4d5569d8064ecba6c1956dfaf52bc428f474904ade21",
    "tests/test_convolution.c": "07240b2680c63f1f18462568d54fe11856a318baa6965c0721fcfd1dbb474cf2",
    "tests/test_softmax.c": "f03990db3b547432ee27b2447711dd05987b0fb29bf6fa3c0ab5154199cdb044",
    "tests/test_attention.c": "c2f666e737976d4481bddd94684a1b1473d45c9117ac4464f7b334be319def17",
    "tests/test_normalization.c": "05a9e2f0b4730caa8e90a6596e5da566b455de9ee3d25540a09e3bb4b0baac81",
    "tests/test_pooling.c": "31af13ba9ef26ab6e8d36089ac12037f680ecec98bef38744dc506c97de122d4",
    "tests/test_elementwise.c": "5346cc195d6a728990030cb372633ff6343de7c67c6991ce226b4b20ea015317",
    "tests/test_pipeline.c": "d07d97354191db0189bc7adb6ec2c26554f374a8b9bae6a0595eea3dc8257d63",
    "Makefile": "5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
    "tu_cmodel/tu_config.h": "129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
    "tu_cmodel/tu_sram.c": "5a6ffcdd3f63c9c015bd628b5c44ded951785a128685b413b6db680f5d1753c0",
    "tu_cmodel/tu_sram.h": "aa62a942c83bfded4644c26eabf37acb815b7ac2883b53f6b3b8a585df4123d5",
    "tu_cmodel/tu_cmodel.c": "542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
    "tu_cmodel/command_queue.c": "e8e24987b1cadb61d23bee76085ca7f11b37b7d387eb075033a1651f8a72a389",
    "tu_cmodel/bindings/tu_dpi.c": "51ccaa58f226ed4d67f8b6c96b35a8ce77237980503de93e88335a0077d74b8a",
}

ENGINE_MODULES = [
    "tu_cmodel/compute/convolution_engine.c",
    "tu_cmodel/compute/softmax_engine.c",
    "tu_cmodel/compute/attention_engine.c",
    "tu_cmodel/compute/normalization_engine.c",
    "tu_cmodel/compute/pooling_engine.c",
    "tu_cmodel/compute/elementwise_pipeline.c",
    "tu_cmodel/compute/pipeline_controller.c",
]
ENGINE_HEADERS = [
    "tu_cmodel/compute/convolution_engine.h",
    "tu_cmodel/compute/softmax_engine.h",
    "tu_cmodel/compute/attention_engine.h",
    "tu_cmodel/compute/normalization_engine.h",
    "tu_cmodel/compute/pooling_engine.h",
    "tu_cmodel/compute/elementwise_pipeline.h",
    "tu_cmodel/compute/pipeline_controller.h",
]
ENGINE_TESTS = [
    "tests/test_convolution.c",
    "tests/test_softmax.c",
    "tests/test_attention.c",
    "tests/test_normalization.c",
    "tests/test_pooling.c",
    "tests/test_elementwise.c",
    "tests/test_pipeline.c",
]
OTHER_FILES = [
    "Makefile",
    "tu_cmodel/tu_config.h",
    "tu_cmodel/tu_sram.c",
    "tu_cmodel/tu_sram.h",
    "tu_cmodel/tu_cmodel.c",
    "tu_cmodel/command_queue.c",
    "tu_cmodel/bindings/tu_dpi.c",
]
HASHED_FILES = ENGINE_MODULES + ENGINE_HEADERS + ENGINE_TESTS + OTHER_FILES


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) != 3:
        print("usage: ch14_source_audit.py <WORK> <PIN>")
        return 2
    work = Path(sys.argv[1])
    pin = sys.argv[2]
    if pin != PIN:
        print(f"PIN MISMATCH expected={PIN} got={pin}")
        return 1

    checks = 0
    predicates = 0

    # 1. Hash gates
    for rel in HASHED_FILES:
        path = work / rel
        if not path.is_file():
            print(f"MISSING FILE {rel}")
            return 1
        if rel not in HASHES:
            print(f"UNPINNED FILE {rel}")
            return 1
        got = sha256_of(path)
        if got != HASHES[rel]:
            print(f"hash mismatch {rel}")
            return 1
        checks += 1

    def has(rel, needle, label):
        nonlocal checks, predicates
        predicates += 1
        text = (work / rel).read_text()
        ok = needle in text
        checks += 1
        if not ok:
            print(f"predicate fail {label}: {needle!r} not found in {rel}")
        return ok

    # 2. Entry-point predicates (public API per module)
    entry_preds = [
        ("tu_cmodel/compute/convolution_engine.c", "tu_conv_compute_dims", "conv-compute-dims"),
        ("tu_cmodel/compute/convolution_engine.c", "tu_conv2d_im2col_gemm", "conv-im2col-gemm"),
        ("tu_cmodel/compute/convolution_engine.c", "tu_conv_estimate_cycles", "conv-estimate-cycles"),
        ("tu_cmodel/compute/softmax_engine.c", "tu_softmax_execute", "softmax-execute"),
        ("tu_cmodel/compute/softmax_engine.c", "softmax_row_two_pass", "softmax-two-pass"),
        ("tu_cmodel/compute/softmax_engine.c", "softmax_row_online", "softmax-online"),
        ("tu_cmodel/compute/attention_engine.c", "tu_attention_execute", "attention-execute"),
        ("tu_cmodel/compute/attention_engine.c", "tu_attention_auto_tile", "attention-auto-tile"),
        ("tu_cmodel/compute/attention_engine.c", "fp32_to_fp16_in_sram", "attention-fp32-fp16-conv"),
        ("tu_cmodel/compute/attention_engine.c", "transpose_fp16_in_sram", "attention-transpose"),
        ("tu_cmodel/compute/normalization_engine.c", "tu_norm_execute", "norm-execute"),
        ("tu_cmodel/compute/normalization_engine.c", "normalize_row", "norm-row"),
        ("tu_cmodel/compute/pooling_engine.c", "tu_pool_execute", "pool-execute"),
        ("tu_cmodel/compute/pooling_engine.c", "tu_pool_max_2d", "pool-max"),
        ("tu_cmodel/compute/elementwise_pipeline.c", "tu_ew_execute", "ew-execute"),
        ("tu_cmodel/compute/elementwise_pipeline.c", "ew_gelu_tanh_approx", "ew-gelu"),
        ("tu_cmodel/compute/pipeline_controller.c", "tu_pipeline_submit_tile", "pipeline-submit"),
        ("tu_cmodel/compute/pipeline_controller.c", "tu_pipeline_advance", "pipeline-advance"),
        ("tu_cmodel/compute/pipeline_controller.c", "tu_pipeline_get_stats", "pipeline-stats"),
    ]
    for rel, needle, label in entry_preds:
        if not has(rel, needle, label):
            return 1

    # 3. Stats-struct predicates (metric census)
    stats_preds = [
        ("tu_cmodel/compute/attention_engine.h", "dma_bytes", "attn-stats-dma"),
        ("tu_cmodel/compute/attention_engine.h", "mma_tiles", "attn-stats-tiles"),
        ("tu_cmodel/compute/attention_engine.h", "mma_flops", "attn-stats-flops"),
        ("tu_cmodel/compute/attention_engine.h", "compute_cycles", "attn-stats-compute"),
        ("tu_cmodel/compute/attention_engine.h", "dma_cycles", "attn-stats-dma-cycles"),
        ("tu_cmodel/compute/attention_engine.h", "total_cycles", "attn-stats-total"),
        ("tu_cmodel/compute/attention_engine.h", "utilization", "attn-stats-util"),
        ("tu_cmodel/compute/pipeline_controller.h", "cycles_saved", "pipe-stats-saved"),
        ("tu_cmodel/compute/pipeline_controller.h", "total_stalls", "pipe-stats-stalls"),
    ]
    for rel, needle, label in stats_preds:
        if not has(rel, needle, label):
            return 1

    # 4. SRAM access-width defect markers (fp16 read/write through 4-byte API)
    defect_preds = [
        ("tu_cmodel/compute/attention_engine.c", "tu_sram_read(sram, src_addr, &val)", "fp16-read-4byte"),
        ("tu_cmodel/compute/attention_engine.c", "tu_sram_write(sram, dst_addr, &h)", "fp16-write-4byte"),
        ("tu_cmodel/compute/attention_engine.c", "tu_sram_write(sram, dst_addr, &val)", "fp16-transpose-write"),
    ]
    for rel, needle, label in defect_preds:
        if not has(rel, needle, label):
            return 1

    # 5. Stall-accounting asymmetry markers
    asym_preds = [
        ("tu_cmodel/compute/normalization_engine.c", "uint64_t s = 0;\n        tu_sram_read", "norm-read-stall-discard"),
        ("tu_cmodel/compute/softmax_engine.c", "stall += tu_sram_read", "softmax-read-stall-count"),
        ("tu_cmodel/compute/elementwise_pipeline.c", "tu_sram_advance_cycle(sram, elem_count)", "ew-advance-cycle"),
        ("tu_cmodel/compute/elementwise_pipeline.c", "bw_b->writes_served++", "ew-write-labeled"),
    ]
    for rel, needle, label in asym_preds:
        if not has(rel, needle, label):
            return 1

    # 6. Reachability predicates (non-test library callers)
    cmdq = (work / "tu_cmodel/command_queue.c").read_text()
    dpi = (work / "tu_cmodel/bindings/tu_dpi.c").read_text()
    cq_has_ew = "tu_ew_" in cmdq
    dpi_has_softmax = "tu_dpi_softmax" in dpi
    dpi_has_ew = "tu_dpi_elementwise" in dpi
    dpi_norm_include_only = ("normalization_engine.h" in dpi) and ("tu_norm" not in dpi)
    for ok, label in [
        (cq_has_ew, "reach-cmdq-elementwise"),
        (dpi_has_softmax, "reach-dpi-softmax"),
        (dpi_has_ew, "reach-dpi-elementwise"),
        (dpi_norm_include_only, "reach-dpi-norm-include-only"),
    ]:
        predicates += 1
        checks += 1
        if not ok:
            print(f"predicate fail {label}")
            return 1

    # 7. Test-membership predicates (make test aggregate)
    makefile = (work / "Makefile").read_text()
    agg_block = makefile.split("test: test-cmodel")[1].split("\n\n")[0]
    test_agg = agg_block.replace("\\\n", " ").replace("\n", " ")
    agg_members = {
        "test-elementwise": "test-elementwise" in test_agg,
        "test-norm": "test-norm " in test_agg or test_agg.rstrip().endswith("test-norm"),
        "test-conv": "test-conv " in test_agg,
        "test-attention": "test-attention" in test_agg,
        "test-pool": "test-pool " in test_agg,
        "test-pipeline": "test-pipeline" in test_agg,
        "test-softmax": "test-softmax" in test_agg,
    }
    for label, ok in agg_members.items():
        predicates += 1
        checks += 1
        print(f"TEST_MEMBERSHIP {label}={str(ok).lower()}")
        if label == "test-softmax" and ok:
            print("predicate fail test-membership: test-softmax must have no Makefile rule (source-present-no-target)")
            return 1
        if label != "test-softmax" and not ok:
            print(f"predicate fail test-membership: {label} missing from make test")
            return 1

    print(f"CH14_SOURCE_AUDIT PASS pin={pin} hashes={len(HASHED_FILES)} "
          f"predicates={predicates} checks={checks}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
