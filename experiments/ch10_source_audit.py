#!/usr/bin/env python3
"""Fail-closed source/reachability audit for Tusim Chapter 10.

Usage: ch10_source_audit.py TUSIM_TREE
The tree must be a clean archive extraction of the pinned commit.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
EXPECTED = {
    "Makefile": "5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
    "config/tu_config.yaml": "9fb4d87753139a5857107a6fdf56006fcb5adbe95ad30e9f8430c2e5c145910e",
    "config/tu_config.json": "6f9d292696b1ca5fa38ad3298e7f3a04c43095c0950f71dbe0c3c68b1f15f4db",
    "tu_cmodel/tu_config.h": "129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
    "tu_cmodel/tu_cmodel.c": "542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
    "tu_cmodel/tu_cmodel.h": "416a0d20776825498217ff5d4382f07ccb2ac9689bbe6c70cacd1bf13e7725af",
    "tu_cmodel/tu_dma.c": "bc1fe789efee140436d411b46298e6960e824796736b8032796d70165d5760cd",
    "tu_cmodel/tu_dma.h": "5b58b2d72e84c7943d99fd33466ea719cf11ad721fc4fb8dbd1b6cb0e3f92bb1",
    "tu_cmodel/command_queue.c": "e8e24987b1cadb61d23bee76085ca7f11b37b7d387eb075033a1651f8a72a389",
    "tu_cmodel/command_queue.h": "cf1f06164d7b3353158c3b70c0667d29b6e94a2ca90a08620232546023363135",
    "tu_cmodel/dma_descriptor.c": "2434c254eef9615b864106de0c453328e64aa6ec49f1e1aff2da5d7e49c8404e",
    "tu_cmodel/dma_descriptor.h": "84d6808d7bdbeba9f638d4cd5eb05b15315f2c09225597bec7e996110f144bbb",
    "tu_cmodel/memory/address_generator.c": "1911a71c84eab77e225d29c4481bbb480e506e863b96fee68bf971a2a55216a3",
    "tu_cmodel/memory/address_generator.h": "7f5f20114bd1b9dbccc156423053f107c83f029da900c00e54b9cf72463199c1",
    "tu_cmodel/memory/double_buffer.c": "94d5ac4d1974ec577cb51af7d132c6bf2e7cf405d0eb5626159430555fcdb07a",
    "tu_cmodel/memory/double_buffer.h": "c72ae87cc19da132c6ee74ea239099d6056a64ecd266ee944697bf938d141d62",
    "tu_cmodel/memory/dram_model.c": "c5ce405dbf30d96ffb166895c1df6a871c9aa3198dda15dc903ad6d346de5ed3",
    "tu_cmodel/memory/dram_model.h": "4acdec93bc83a0f8d7cf267a55ea5c29e863f20b9024e83a709ba28acbb17602",
    "tu_cmodel/memory/memory_hierarchy.c": "3f5d4a71e0bf107e0b5e7581d5d0cf3f7b2a56ec02e4cc39bcf7923b1901c286",
    "tu_cmodel/memory/memory_hierarchy.h": "8df3d23ee14b77433cac070bb541e2efb0ce80d5d1ff9fabb886fff8bac20fe8",
    "tu_cmodel/compute/pipeline_controller.c": "165522ae3a7853189ed0f6ea114f3e5079487593fb1c06b42a877df53fa1b493",
    "tu_cmodel/compute/pipeline_controller.h": "39dc3e73b07b2be30aed4d5569d8064ecba6c1956dfaf52bc428f474904ade21",
    "tu_cmodel/infra/config.c": "17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
    "tu_cmodel/infra/config.h": "723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
    "tests/test_cmodel.c": "a7609fe22a113c0d9f2807ab3b76c7be29bbc2ed3822a3cfea82c2109862b36c",
    "tests/test_command_queue.c": "f15c088772c5ac1eeedd25ceeeb8592f60f6b5386f5a854b5394f1d65e934237",
    "tests/test_dma.c": "a95a944714341377adf8ba305dfdb549999e7e4fa15b2607280279c746557373",
    "tests/test_address_gen.c": "73138bcbf727bb34b87b3d6d057917eef9a0becdfcdcf179475bfa04d57c9961",
    "tests/test_double_buffer.c": "721a79c0d8013ae48e6852d93536b8bd4b7eb2f09bb6ceafaefa6ac976b932a5",
    "tests/test_pipeline.c": "d07d97354191db0189bc7adb6ec2c26554f374a8b9bae6a0595eea3dc8257d63",
    "tests/test_multicast.c": "b336753fd45581f4a2dccfc4b75635186ff4c68c05e9833f61c74e2d49a71724",
    "tests/test_scatter_gather.c": "36b5e4006e255e9f0bbffec0761f90f6f5220ffc506b1bbe0a270eb84e0dc39a",
    "tests/test_config.c": "e2bf7d9a1bbac06863e3b8c372fa1cb854927fc1aeb73a08c79e08cd3f1db821",
}

root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else None
if not root or not root.is_dir():
    raise SystemExit("usage: ch10_source_audit.py TUSIM_TREE")
checks = 0

def check(cond: bool, label: str) -> None:
    global checks
    if not cond:
        raise AssertionError(label)
    checks += 1
    print(f"SOURCE_CHECK PASS {label}")

def text(rel: str) -> str:
    return (root / rel).read_text()

for rel, expected in EXPECTED.items():
    actual = hashlib.sha256((root / rel).read_bytes()).hexdigest()
    check(actual == expected, f"sha256 {rel}")

make = text("Makefile")
dma = text("tu_cmodel/dma_descriptor.c")
dmah = text("tu_cmodel/dma_descriptor.h")
top = text("tu_cmodel/tu_cmodel.c")
cmdq = text("tu_cmodel/command_queue.c")
pipe = text("tu_cmodel/compute/pipeline_controller.c")
agen = text("tu_cmodel/memory/address_generator.c")
config = text("tu_cmodel/infra/config.c")
runtime_h = text("tu_cmodel/tu_config.h")
pipeline_test = text("tests/test_pipeline.c")
all_c = {p.relative_to(root).as_posix(): p.read_text()
         for p in (root / "tu_cmodel").rglob("*.c")}

# Exact integration/reachability contracts, protected by the hashes above.
check(top.count("tu_dma_load(") == 2 and top.count("tu_dma_store(") == 1 and
      "void tu_dma_load_o" in top and "tu_sram_write_bulk(&g_tu.sram_o" in top,
      "public wrappers use legacy DMA for W/A loads and O store; O load bypasses it")
check(cmdq.count("tu_dma_load_") == 3 and cmdq.count("tu_dma_store_o") == 2,
      "command queue fixed operations route through public wrappers")
check(pipe.count("tu_dma_submit_desc(") == 2,
      "standalone pipeline is sole non-test descriptor-submit consumer")
check(agen.count("tu_agen_desc_chain_from_iterator(") == 1,
      "address-generator descriptor-chain helper has definition only")
submit_files = {rel for rel, body in all_c.items() if "tu_dma_submit_desc(" in body}
check(submit_files == {"tu_cmodel/dma_descriptor.c",
                       "tu_cmodel/compute/pipeline_controller.c"},
      "exact non-test descriptor-submit file set")
execute_files = {rel for rel, body in all_c.items() if "tu_dma_execute_desc(" in body}
check(execute_files == {"tu_cmodel/dma_descriptor.c"},
      "descriptor executor has no external non-test caller")
agen_chain_files = {rel for rel, body in all_c.items()
                    if "tu_agen_desc_chain_from_iterator(" in body}
check(agen_chain_files == {"tu_cmodel/memory/address_generator.c"},
      "address-generator chain helper exact non-test file set")
check("tu_dram_read(" not in dma and "tu_dram_write(" not in dma and
      "tu_dram_estimate_transfer(" not in dma,
      "descriptor engine has no standalone DRAM-model call")
check("cycles_issued =" not in dma and "cycles_issued=" not in dma,
      "cycles_issued has no assignment in descriptor engine")
check("desc->priority" not in dma and "desc->signal_id" not in dma,
      "descriptor priority and signal_id have no engine consumer")
check(re.search(r"tu_dma_channel_state_t\s+channels\[TU_DMA_CHANNELS\]", dmah) is not None and
      "if (g_tu_dma.num_channels > 8)" in dma and
      "tu_dma_init_full(true, 4, 32)" in pipeline_test,
      "pipeline harness requests 4 channels against 3-entry engine array")
init_full = dma[dma.index("void tu_dma_init_full"):dma.index("void tu_dma_init(bool")]
check("memset(&g_tu_dma, 0, sizeof(g_tu_dma));" in init_full and
      "tu_dma_destroy" not in init_full,
      "reinitialization overwrites engine state without descriptor teardown")
check("num_channels > 0 ? num_channels : TU_DMA_CHANNELS" in init_full,
      "zero channel request maps to compiled channel count")
check("if (g_tu_dma.num_channels > 8) g_tu_dma.num_channels = 8;" in init_full and
      "g_tu_dma.num_channels > TU_DMA_CHANNELS" not in init_full,
      "initializer clamps at eight rather than fixed channel-array bound")

# Config is parsed but omitted from the runtime structure/conversion.
convert_start = config.index("tu_runtime_config_t tu_config_to_runtime")
convert_end = config.index("/* ---- Load from JSON string ---- */", convert_start)
convert = config[convert_start:convert_end]
for field in ("dma_bus_width_bits", "dma_max_burst_bytes", "dma_num_channels",
              "dma_max_outstanding", "dma_async_mode", "dma_multicast_enabled"):
    check(field not in convert, f"runtime conversion omits DMA field {field}")
runtime_match = re.search(r"typedef struct\s*\{([^{}]*)\}\s*tu_runtime_config_t;", runtime_h, re.S)
check(runtime_match is not None, "runtime config structure located")
runtime_struct = runtime_match.group(1)
check("dma" not in runtime_struct.lower(), "runtime config structure has no DMA field")
check("tu_dma_init(TU_DMA_ASYNC_MODE ? true : false)" in top and
      "tu_dma_init_full(async, TU_DMA_CHANNELS, TU_DMA_MAX_OUTSTANDING)" in dma,
      "top-level initialization uses compile-time DMA constants")

# Ownership/linkage hazards are exact structural facts.
check(dmah.count("tu_dma_descriptor_t *next;") == 1,
      "one next pointer serves both chain and queue linkage")
check("ch->tail->next = desc" in dma and "ch->tail = desc" in dma,
      "enqueue tail tracks submitted head rather than chain tail")
check("tu_dma_desc_destroy(desc);" in dma[dma.index("uint32_t tu_dma_submit_desc"):dma.index("int tu_dma_tick")],
      "rejected submission destroys caller descriptor chain")
check("free(desc);" in dma[dma.index("void tu_dma_destroy"):dma.index("tu_dma_descriptor_t *tu_dma_desc_create_linear")],
      "engine destroy raw-frees pending nodes")

# Build membership and target boundary.
for obj in ("/dma_descriptor.o", "/memory/address_generator.o",
            "/memory/double_buffer.o", "/compute/pipeline_controller.o"):
    check(obj in make, f"archive object listed {obj}")
check("test-double-buffer:" not in make and "tests/test_double_buffer.c" not in make,
      "double-buffer focused test is absent from Makefile targets")

print(f"SOURCE_AUDIT PASS pin={PIN} checks={checks} hashes={len(EXPECTED)}")
