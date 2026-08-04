#!/usr/bin/env python3
"""Fail-closed Chapter 15 source audit for Tusim DRAM service models."""
import hashlib
import sys
from pathlib import Path

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
HASHES = {
    "Makefile": "5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
    "tu_cmodel/memory/dram_model.c": "c5ce405dbf30d96ffb166895c1df6a871c9aa3198dda15dc903ad6d346de5ed3",
    "tu_cmodel/memory/dram_model.h": "4acdec93bc83a0f8d7cf267a55ea5c29e863f20b9024e83a709ba28acbb17602",
    "tu_cmodel/memory/memory_hierarchy.c": "3f5d4a71e0bf107e0b5e7581d5d0cf3f7b2a56ec02e4cc39bcf7923b1901c286",
    "tu_cmodel/memory/memory_hierarchy.h": "8df3d23ee14b77433cac070bb541e2efb0ce80d5d1ff9fabb886fff8bac20fe8",
    "tu_cmodel/infra/config.c": "17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
    "tu_cmodel/infra/config.h": "723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
    "tu_cmodel/tu_config.h": "129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
    "tu_cmodel/dma_descriptor.c": "2434c254eef9615b864106de0c453328e64aa6ec49f1e1aff2da5d7e49c8404e",
    "tests/test_dram.c": "9dd3c2c52a0e93ea4aebdac11010323c6b3572359d794a9772b61f1c86147b72",
    "tests/test_memory_hierarchy.c": "88589f3e92ffe78b8525f60e6067ebbeba2c4c1f83362bfdb018a9f37f6f64ff",
    "config/tu_config.json": "6f9d292696b1ca5fa38ad3298e7f3a04c43095c0950f71dbe0c3c68b1f15f4db",
    "config/tu_config.yaml": "9fb4d87753139a5857107a6fdf56006fcb5adbe95ad30e9f8430c2e5c145910e",
    "docs/dram-model.md": "867e3cb32f777955f0b33eb35945ae0ce5fa9921f7f25e3bb37353f550032cf0",
    "docs/exploration/dram-type-clock-sweep.md": "5b706f0146bbd9323776b8273922b8ee64158727f91d68fa25e954e148780065",
    "docs/bandwidth-modeling.md": "004cf897a64f008dd98d4d1c76912513cba4b02916a6549ecc0b39eb0de8c1b3",
    "scripts/gen_config.py": "5eab235067eaf6d5785352e48ef00417a18f5b0d05b25f40a82719e11bf8634a",
    "tests/test_config.c": "e2bf7d9a1bbac06863e3b8c372fa1cb854927fc1aeb73a08c79e08cd3f1db821",
    "tests/test_cycle_model.c": "606e4325ca31e71c19cc05101ccf76db95a2be95d1bbb57fef7e19ca9d398ca9",
    "tests/test_power_model.c": "0d96adfa610df06a3dff15fcd692acb61c9a348b85ca660e4c4c764bc2c61ba6",
    "tu_cmodel/perf/cycle_model.c": "b197a6ab411f5ab2d152a99ae233bb25abb2d1912d1f4fa8a94a88e7e1879fec",
    "tu_cmodel/perf/cycle_model.h": "0f0301d824be11f2fb4cfc96fd53ae9b64db841de6fb15d989e4f42d846b7101",
    "tu_cmodel/perf/power_model.c": "5cba597200fba469eb6b21a8d0bbb5c542a5a61538d886f74aa0aa74e076325d",
}

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    if len(sys.argv) != 3:
        print("usage: ch15_source_audit.py <WORK> <PIN>")
        return 2
    work = Path(sys.argv[1]); pin = sys.argv[2]
    if pin != PIN:
        print(f"PIN MISMATCH expected={PIN} got={pin}")
        return 1
    checks = 0; predicates = 0
    for rel, expected in HASHES.items():
        p = work / rel
        if not p.is_file():
            print(f"MISSING FILE {rel}"); return 1
        if digest(p) != expected:
            print(f"hash mismatch {rel}"); return 1
        checks += 1

    def has(rel, needle, label):
        nonlocal checks, predicates
        predicates += 1; checks += 1
        ok = needle in (work / rel).read_text()
        if not ok: print(f"predicate fail {label}: {needle!r} not found in {rel}")
        return ok
    def lacks(rel, needle, label):
        nonlocal checks, predicates
        predicates += 1; checks += 1
        ok = needle not in (work / rel).read_text()
        if not ok: print(f"predicate fail {label}: unexpected {needle!r} in {rel}")
        return ok

    required = [
        ("tu_cmodel/memory/dram_model.c", "tu_dram_create(tu_dram_type_t type)", "create"),
        ("tu_cmodel/memory/dram_model.c", "tu_dram_estimate_transfer", "estimate"),
        ("tu_cmodel/memory/dram_model.c", "tu_dram_read", "read"),
        ("tu_cmodel/memory/dram_model.c", "tu_dram_write", "write"),
        ("tu_cmodel/memory/dram_model.c", "tu_dram_tick", "tick"),
        ("tu_cmodel/memory/dram_model.c", "tu_dram_get_stats", "stats"),
        ("tu_cmodel/memory/dram_model.c", "tu_dram_peak_bw_per_cycle", "peak-helper"),
        ("tu_cmodel/memory/dram_model.c", "tu_dram_set_core_clock", "clock-setter"),
        ("tu_cmodel/memory/dram_model.c", "bw_window_size_cycles = 1000", "fixed-window"),
        ("tu_cmodel/memory/dram_model.c", "double core_cycles_per_sec = 1.0e9", "meter-one-ghz"),
        ("tu_cmodel/memory/dram_model.c", "stall += dram->bw_window_size_cycles", "budget-stall"),
        ("tu_cmodel/memory/dram_model.c", "pending_read_bytes + dram->pending_write_bytes + num_bytes", "pending-plus-request"),
        ("tu_cmodel/memory/dram_model.c", "dram->bandwidth_available > num_bytes", "remaining-budget-decrement"),
        ("tu_cmodel/memory/dram_model.c", "base_latency += 10", "flat-row-penalty"),
        ("tu_cmodel/memory/dram_model.c", "dram->stats.total_row_conflicts++", "flat-conflict-counter"),
        ("tu_cmodel/memory/dram_model.c", "(void)clock_ghz", "clock-noop"),
        ("tu_cmodel/memory/dram_model.c", "ceil(num_bytes / bw_bytes_per_cycle)", "estimate-ceil"),
        ("tu_cmodel/memory/memory_hierarchy.c", "tu_dram_create(TU_DRAM_HBM2)", "hier-fixed-hbm2"),
        ("tu_cmodel/memory/memory_hierarchy.c", "tu_dram_read(h->dram, addr, bytes, &cyc, &st)", "hier-read-call"),
        ("tu_cmodel/memory/memory_hierarchy.c", "stall = st", "hier-stall-only"),
        ("tu_cmodel/memory/memory_hierarchy.c", "tu_dram_tick(h->dram)", "hier-explicit-tick"),
        ("tu_cmodel/infra/config.c", "cfg->dram_type = parse_dram_type_str", "parse-type"),
        ("tu_cmodel/infra/config.c", "parse_opt_double(dram, \"bandwidth_gbps\"", "parse-bandwidth"),
        ("tu_cmodel/infra/config.c", "parse_opt_bool(dram, \"model_row_conflicts\"", "parse-row"),
        ("tu_cmodel/infra/config.c", "parse_opt_double(lat, \"dram_read\"", "parse-read-latency"),
        ("tu_cmodel/infra/config.c", "parse_opt_double(lat, \"dram_write\"", "parse-write-latency"),
        ("config/tu_config.json", "\"core_clock_ghz\": 1.0", "json-clock-declared"),
        ("config/tu_config.yaml", "core_clock_ghz: 1.0", "yaml-clock-declared"),
        ("scripts/gen_config.py", "TU_LATENCY_DRAM_READ", "yaml-generator-read-latency"),
        ("scripts/gen_config.py", "TU_LATENCY_DRAM_WRITE", "yaml-generator-write-latency"),
        ("tu_cmodel/perf/power_model.c", "config->dram_bandwidth_gbps > 500.0", "full-config-power-consumer"),
        ("tests/test_power_model.c", "test_power_config_integration", "power-config-focused-test"),
        ("tu_cmodel/perf/cycle_model.c", "uint64_t tu_dram_access", "second-dram-entry-point"),
        ("tu_cmodel/perf/cycle_model.c", "bank->open_row == row", "second-dram-row-hit-state"),
        ("tu_cmodel/perf/cycle_model.c", "cm->dram_channel", "cycle-model-dram-owner"),
        ("tu_cmodel/perf/cycle_model.c", "tu_perf_compute_record_mma", "cycle-model-counter-consumer"),
        ("tests/test_cycle_model.c", "Tests: %d run, %d passed, %d failed", "cycle-model-focused-summary"),
        ("docs/bandwidth-modeling.md", "# TU CModel — SRAM Bandwidth Modeling", "sram-doc-title"),
        ("docs/bandwidth-modeling.md", "tu_sram_advance_cycle", "sram-doc-owning-api"),
        ("docs/dram-model.md", "Not yet integrated with DMA engine", "doc-admits-no-dma"),
        ("docs/exploration/dram-type-clock-sweep.md", "analytical cycle model", "sweep-analytical"),
    ]
    for rel, needle, label in required:
        if not has(rel, needle, label): return 1

    forbidden = [
        ("tu_cmodel/dma_descriptor.c", "tu_dram_", "descriptor-no-dram-call"),
        ("tu_cmodel/infra/config.c", "core_clock_ghz", "parser-ignores-core-clock"),
    ]
    for rel, needle, label in forbidden:
        if not lacks(rel, needle, label): return 1

    reset = (work / "tu_cmodel/memory/dram_model.c").read_text().split("void tu_dram_reset", 1)[1].split("/* ---- Internal", 1)[0]
    for field in ("bw_window_size_cycles", "bw_window_start"):
        predicates += 1; checks += 1
        if field in reset:
            print(f"predicate fail reset-leaves-{field}"); return 1

    custom = (work / "tu_cmodel/memory/dram_model.c").read_text().split("tu_dram_create_custom", 1)[1].split("void tu_dram_destroy", 1)[0]
    for validation in ("params->channels == 0", "params->burst_length == 0"):
        predicates += 1; checks += 1
        if validation in custom:
            print(f"predicate fail custom-validation-absent-{validation}"); return 1

    hierarchy_callers = []
    for source in (work / "tu_cmodel").rglob("*.c"):
        if source.name == "memory_hierarchy.c": continue
        body = source.read_text()
        if any(token in body for token in ("tu_mem_hierarchy_init(", "tu_mem_hierarchy_read(",
                                            "tu_mem_hierarchy_write(", "tu_mem_hierarchy_tick(")):
            hierarchy_callers.append(source.relative_to(work).as_posix())
    predicates += 1; checks += 1
    if hierarchy_callers:
        print(f"predicate fail non-test-hierarchy-callers={hierarchy_callers}"); return 1

    generator = (work / "scripts/gen_config.py").read_text()
    for omitted in ("TU_DRAM_TYPE", "TU_DRAM_BANDWIDTH", "TU_DRAM_CHANNELS", "TU_DRAM_MODEL_ROW"):
        predicates += 1; checks += 1
        if omitted in generator:
            print(f"predicate fail yaml-generator-omission-{omitted}"); return 1

    predicates += 1; checks += 1
    if "dram" in (work / "tests/test_config.c").read_text().lower():
        print("predicate fail config-suite-unexpected-dram-coverage"); return 1

    cfg = (work / "tu_cmodel/infra/config.c").read_text()
    conv = cfg.split("tu_config_to_runtime")[1].split("/* ---- Load from JSON string ---- */")[0]
    for field in ["dram_type", "dram_bandwidth_gbps", "dram_channels",
                  "dram_model_row_conflicts", "dram_latency_read", "dram_latency_write"]:
        predicates += 1; checks += 1
        if field in conv:
            print(f"predicate fail runtime-converter-drops-{field}"); return 1

    make = (work / "Makefile").read_text()
    agg = make.split("test: test-cmodel")[1].split("\n\n")[0].replace("\\\n", " ").replace("\n", " ")
    for label, ok in [
        ("dram-target", "\ntest-dram:" in make),
        ("dram-aggregate", "test-dram" in agg),
        ("cycle-model-absent-tu-objs", "cycle_model.o" not in make.split("TU_OBJS =",1)[1].split("\n\n",1)[0]),
    ]:
        predicates += 1; checks += 1
        print(f"MEMBERSHIP {label}={str(ok).lower()}")
        if not ok: print(f"predicate fail {label}"); return 1

    print(f"CH15_SOURCE_AUDIT PASS pin={pin} hashes={len(HASHES)} predicates={predicates} checks={checks}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
