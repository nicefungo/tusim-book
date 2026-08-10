#!/usr/bin/env python3
import hashlib
import re
import sys
from pathlib import Path

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
HASHES = {
    "Makefile": "5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
    "tu_cmodel/isa/tu_isa.h": "8efd760c3485492de68b6093d9fa617cdebc2f75de3453310ed3f207b4d16456",
    "tu_cmodel/isa/tu_isa.c": "53bdf44cd720a933da174da55ab1180f8056de9fb2aaa5b9b534adb7af4c387f",
    "tu_cmodel/isa/tu_scheduler.h": "d0af2cfa650f704b8abefadea0f1bb0bb02029c0d2168b7b608505b0fe1a3426",
    "tu_cmodel/isa/tu_scheduler.c": "b76afa350cc6229fe981e4c188bdc7b8026df4ae74725b3106c624afee9c8893",
    "tu_cmodel/isa/tu_liveness.h": "a3f7759b0ade75bb85cd45584895687318e1355c692d39f001e2893ef87a4dfd",
    "tu_cmodel/isa/tu_liveness.c": "78949f02c43c3c7711033644cb87c5e0441edff0f4d1931d47ba104a67e9b239",
    "tests/test_scheduler.c": "c35fa60e174b338d9dfbd6e94fa40941820c2d5076b44e3a0ccf1f9cc1db71d0",
    "tests/test_scheduler_sweep.c": "9a56f263e42dcd7e5573868e388849a4ced6c65576b8f437aaff12f51be9e940",
    "tests/test_liveness.c": "598a4e8731af6a28ebf6f5224d27effd7f1296eba133b762f90eff75ffcf5f58",
    "docs/compiler-scheduling-pass.md": "10ace1ef7bbdcfcecf042dc4e06b3a6470ecb5cb75688a0cc7af5bc762cd5ee2",
    "docs/liveness-allocation.md": "3a69f2215dcf869e851224aa6f4328a4a9bad24666f634b3ecf72540e0efa33e",
    "docs/exploration/scheduler-policy-sweep.md": "5709e70e2b0100c30b164503413b002b6e58b1631597d47880d449cbbc0e3baa",
    "docs/expanded-isa.md": "046be507f11d82ba26f262c7a69ce9d662f636fbfe0c20e1762871ae38db0107",
    "docs/api-documentation.md": "feab6e0088bcfc2cb7d9423904cb36735c1b62d6f254ff0a4699d1b1757d6c18",
    "compiler/onnx_to_tu.py": "9308a86a6c7a986c9fa6cfae6f1b147724de5a78cabaf34656e15de4e4713e2b",
    "tu_cmodel/command_queue.c": "e8e24987b1cadb61d23bee76085ca7f11b37b7d387eb075033a1651f8a72a389",
    "tu_cmodel/command_queue.h": "cf1f06164d7b3353158c3b70c0667d29b6e94a2ca90a08620232546023363135",
    "tu_cmodel/tu_asm.c": "7d509822dd585bf9f445c96a7be03882a1019d42c39b19f9d14a5b8c5603daee",
    "tu_cmodel/tu_config.h": "129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
    "tu_cmodel/infra/config.c": "17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
    "tu_cmodel/infra/config.h": "723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
    "config/tu_config.json": "6f9d292696b1ca5fa38ad3298e7f3a04c43095c0950f71dbe0c3c68b1f15f4db",
    "config/tu_config.yaml": "9fb4d87753139a5857107a6fdf56006fcb5adbe95ad30e9f8430c2e5c145910e",
}

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
pin = sys.argv[2] if len(sys.argv) > 2 else PIN
if pin != PIN:
    print(f"CH19_SOURCE_AUDIT FAIL pin expected={PIN} got={pin}")
    raise SystemExit(1)

texts = {}
errors = []
for rel, expected in HASHES.items():
    p = root / rel
    if not p.is_file():
        errors.append(f"missing {rel}")
        continue
    data = p.read_bytes()
    got = hashlib.sha256(data).hexdigest()
    if got != expected:
        errors.append(f"hash mismatch {rel} expected={expected} got={got}")
    texts[rel] = data.decode("utf-8", errors="replace")

preds = []
def pred(label, condition):
    preds.append(label)
    if not condition:
        errors.append(f"predicate failed {label}")

def section(text, start, end):
    try:
        a = text.index(start)
        b = text.index(end, a + len(start))
        return text[a:b]
    except ValueError:
        return ""

mk = texts.get("Makefile", "")
sh = texts.get("tu_cmodel/isa/tu_scheduler.h", "")
sc = texts.get("tu_cmodel/isa/tu_scheduler.c", "")
lh = texts.get("tu_cmodel/isa/tu_liveness.h", "")
lc = texts.get("tu_cmodel/isa/tu_liveness.c", "")
isa = texts.get("tu_cmodel/isa/tu_isa.h", "")
stest = texts.get("tests/test_scheduler.c", "")
lsweep = texts.get("tests/test_scheduler_sweep.c", "")
ltest = texts.get("tests/test_liveness.c", "")
sdoc = texts.get("docs/compiler-scheduling-pass.md", "")
ldoc = texts.get("docs/liveness-allocation.md", "")
sweepdoc = texts.get("docs/exploration/scheduler-policy-sweep.md", "")

# Public API and direct configuration census.
expected_sched = {
    "tu_sched_analyze_access", "tu_sched_build_dag", "tu_sched_compute_mobility",
    "tu_sched_hoist_dma", "tu_sched_insert_barriers", "tu_sched_run",
    "tu_sched_print_result", "tu_sched_print_graph", "tu_sched_validate",
}
expected_live = {
    "tu_live_analyze", "tu_live_build_interference", "tu_live_color",
    "tu_live_apply", "tu_live_allocate", "tu_live_print_result",
    "tu_live_print_interference",
}
sched_api = set(re.findall(r"\b(tu_sched_[A-Za-z0-9_]+)\s*\(", sh))
live_api = set(re.findall(r"\b(tu_live_[A-Za-z0-9_]+)\s*\(", lh))
pred("scheduler-public-api-exact-9", sched_api == expected_sched)
pred("liveness-public-api-exact-7", live_api == expected_live)
for name in sorted(expected_sched):
    pred("scheduler-defined-" + name, re.search(rf"\b{re.escape(name)}\s*\(", sc) is not None)
for name in sorted(expected_live):
    pred("liveness-defined-" + name, re.search(rf"\b{re.escape(name)}\s*\(", lc) is not None)
for field in ["policy", "hoist_dma", "insert_barriers", "pipeline_tiles", "max_hoist_distance", "max_window", "verbose"]:
    pred("scheduler-config-field-" + field, re.search(rf"\b{field}\s*;", sh) is not None)
for field in ["w_capacity", "a_capacity", "o_capacity", "alloc_strategy", "spill_strategy", "safety_margin", "enable_spilling", "verbose"]:
    pred("liveness-config-field-" + field, re.search(rf"\b{field}\s*;", lh) is not None)
pred("scheduler-pipeline-tiles-inert", sc.count("pipeline_tiles") == 1)
pred("scheduler-max-window-inert", sc.count("max_window") == 1)
pred("scheduler-verbose-inert", sc.count("verbose") == 1)
pred("liveness-spill-slot-unassigned", "spill_slot =" not in lc and "spill_slot      =" in lc)
pred("liveness-verbose-inert", lc.count("verbose") == 1)

# Build and focused-test provenance.
archive = section(mk, "TU_OBJS =", "libtucmodel.a:")
pred("scheduler-archive-member", "$(TU_DIR)/isa/tu_scheduler.o" in archive)
pred("liveness-archive-member", "$(TU_DIR)/isa/tu_liveness.o" in archive)
pred("scheduler-test-rule", re.search(r"(?m)^test-scheduler:", mk) is not None)
pred("scheduler-sweep-rule", re.search(r"(?m)^test-scheduler-sweep:", mk) is not None)
pred("liveness-test-rule", re.search(r"(?m)^test-liveness:", mk) is not None)
flat = mk.replace("\\\n", " ")
mt = re.search(r"(?m)^test:\s*(.*?)(?:\n\t|\n[^ \t])", flat, re.S)
agg = mt.group(1) if mt else ""
pred("scheduler-aggregate-member", "test-scheduler" in agg)
pred("liveness-aggregate-member", "test-liveness" in agg)
pred("scheduler-sweep-not-aggregate", "test-scheduler-sweep" not in agg)
pred("scheduler-focused-14", stest.count("TEST(") == 15)  # macro definition + 14 calls
pred("liveness-focused-12", ltest.count("TEST(") == 13)   # macro definition + 12 calls
pred("scheduler-sweep-five-topologies", lsweep.count("/* --- Workload") == 5)
pred("focused-recipes-link-by-search-name", mk.count("-L. -ltucmodel") >= 2)
pred("scheduler-sweep-ignores-run-status", lsweep.count("run_one(") >= 16 and "if (run_one(" not in lsweep)
pred("scheduler-sweep-main-always-success", re.search(r"int main\(void\).*return 0;\n}", lsweep, re.S) is not None)

# Whole-tree exact caller inventory and absent composition/config surfaces.
def external_callers(api, own):
    pat = re.compile(r"\b(?:" + "|".join(re.escape(x) for x in sorted(api)) + r")\s*\(")
    hits = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in {".c", ".h", ".cc", ".cpp", ".py"}:
            continue
        rel = p.relative_to(root).as_posix()
        if rel in own or rel.startswith(("tests/", "docs/")):
            continue
        if pat.search(p.read_text(errors="replace")):
            hits.append(rel)
    return sorted(hits)

sched_hits = external_callers(expected_sched, {"tu_cmodel/isa/tu_scheduler.c", "tu_cmodel/isa/tu_scheduler.h"})
live_hits = external_callers(expected_live, {"tu_cmodel/isa/tu_liveness.c", "tu_cmodel/isa/tu_liveness.h"})
pred("scheduler-zero-external-nontest-callers", sched_hits == [])
pred("liveness-zero-external-nontest-callers", live_hits == [])
pred("scheduler-does-not-call-liveness", not re.search(r"\btu_live_[A-Za-z0-9_]+\s*\(", sc))
pred("liveness-does-not-call-scheduler", not re.search(r"\btu_sched_[A-Za-z0-9_]+\s*\(", lc))
json_yaml = (texts.get("config/tu_config.json", "") + texts.get("config/tu_config.yaml", "")).lower()
pred("shipped-config-no-passes", not re.search(r"scheduler|liveness|alloc_strategy|spill_strategy|max_hoist|max_window|pipeline_tiles", json_yaml))
cfg = texts.get("tu_cmodel/infra/config.c", "")
pred("global-config-no-pass-construction", "tu_sched_config" not in cfg and "tu_live_config" not in cfg)

# Scheduler access, DAG, named transforms, scheduling, cycles, and validation.
pred("scheduler-max-instructions-256", "#define TU_SCHED_MAX_INSTRS       256" in sh)
pred("scheduler-max-deps-16", "#define TU_SCHED_MAX_DEPS          16" in sh)
pred("scheduler-three-regions", "TU_SRAM_REGION_COUNT = 3" in sh)
opcode_pairs = re.findall(r"(?m)^\s*(TU_ISA_[A-Z0-9_]+)\s*=\s*0x([0-9A-Fa-f]+)", isa)
opcode_values = [int(v, 16) for _, v in opcode_pairs]
pred("isa-explicit-opcode-census-59", len(opcode_pairs) == 59 and len(set(opcode_values)) == 59)
pred("isa-numeric-opcode-domain-0-through-127", min(opcode_values, default=-1) == 0 and max(opcode_values, default=-1) == 127 and "TU_ISA_OPCODE_COUNT" in isa)
pred("scheduler-dma-range-dim0-dim1", "uint32_t offset = instr->dim0" in sc and "uint32_t size   = instr->dim1 ? instr->dim1 : 1" in sc)
pred("scheduler-zero-dma-size-becomes-one", "instr->dim1 ? instr->dim1 : 1" in sc)
pred("scheduler-flags-double-as-channel", "channel = instr->flags & 0x3" in sc and "TU_FLAG_PREC_FP32" in isa)
pred("scheduler-mma-prewiden-signed-product", "instr->dim2 * instr->dim1 * 2" in sc)
pred("scheduler-fixed-64k-approximations", sc.count("+ 65536") >= 4)
pred("scheduler-full-region-approximations", sc.count("UINT32_MAX") >= 5)
pred("scheduler-unknown-no-access", "Unknown op: no SRAM access" in sc)
build = section(sc, "int tu_sched_build_dag", "/* ================================================================\n * ASAP / ALAP")
pred("scheduler-edge-overflow-silent", build.count("continue;") >= 3 and "TU_SCHED_MAX_DEPS" in build)
pred("scheduler-built-despite-edge-skips", "graph->built = true" in build)
pred("scheduler-barrier-prior-only", "Barriers depend on all prior non-barrier instructions" in build and "consumer->is_barrier" in build)
pred("scheduler-no-later-barrier-edge-rule", "producer->is_barrier) continue" in build)
mob = section(sc, "void tu_sched_compute_mobility", "/* ================================================================\n * DMA hoisting")
pred("scheduler-mobility-fixed-costs", mob.count("pred->is_dma ? 1 : 4") == 1 and mob.count("node->is_dma ? 1 : 4") == 1)
hoist = section(sc, "int tu_sched_hoist_dma", "/* ================================================================\n * Barrier insertion")
barrier = section(sc, "int tu_sched_insert_barriers", "/* ================================================================\n * List scheduling")
pred("scheduler-hoist-count-only", "hoisted++" in hoist and "node->instr" not in hoist and "memmove" not in hoist)
pred("scheduler-hoist-minimum-predecessor", "if (pred_id < earliest_pos) earliest_pos = pred_id" in hoist)
pred("scheduler-barrier-count-only", "barriers_inserted++" in barrier and "TU_ISA_SYNC" not in barrier and "TU_ISA_BARRIER" not in barrier)
pred("scheduler-barrier-dma-store-successor-direction", "if (!is_store) continue" in barrier and "node->succs[s]" in barrier)
run = section(sc, "int tu_sched_run", "/* ================================================================\n * Validation")
pred("scheduler-null-default-gate-difference", "if (config && config->hoist_dma)" in run and "if (config && config->insert_barriers)" in run)
listing = section(sc, "static int list_schedule", "/* ================================================================\n * Main entry point")
pred("scheduler-list-resets-counts", "result->num_barriers_inserted = 0" in listing and "result->num_dma_hoisted = 0" in listing)
pred("scheduler-serial-emission-cost", "result->estimated_cycles += (node->is_dma ? 1 : 4)" in listing)
pred("scheduler-valid-count-only", "result->valid = (result->num_instructions == graph->num_nodes)" in listing)
validate = section(sc, "bool tu_sched_validate", "/* ================================================================\n * Debug output")
pred("scheduler-validator-weak-identity", all(x in validate for x in ["si->opcode == oi->opcode", "si->dim0 == oi->dim0", "si->dim1 == oi->dim1", "si->flags == oi->flags"]) and "si->dim2" not in validate and "si->immediates" not in validate)
pred("scheduler-validator-skips-unmatched", "if (pos_i < 0) continue" in validate and "if (pos_s >= 0" in validate)
pred("scheduler-validator-trusts-valid-bit", "if (!result->valid) return false" in validate)
pred("scheduler-invalid-policy-balanced-default", "case TU_SCHED_POLICY_BALANCED:\n                default:" in listing)
pred("scheduler-access-elementwise-scale-generic", "case TU_ISA_ELEMENTWISE" in sc and "case TU_ISA_SCALE" in sc)
pred("scheduler-access-groupnorm-unreachable", "case TU_ISA_GROUP_NORM" in sc and "op <= TU_ISA_BATCH_NORM" in sc)
pred("scheduler-sweep-report-critical-path-claim", "critical path of the dependency DAG" in sweepdoc)
pred("scheduler-source-serial-not-critical-path", "result->estimated_cycles +=" in sc and "max_asap" not in listing)

# Liveness construction and finite bounds.
pred("liveness-max-vregs-128", "#define TU_LIVE_MAX_VREGS       128" in lh)
pred("liveness-max-spill-slots-16", "#define TU_LIVE_MAX_SPILL_SLOTS  16" in lh)
pred("liveness-output-capacity-512", "TU_SCHED_MAX_INSTRS * 2" in lh)
pred("liveness-mma-prewiden-signed-product", "instr->dim0 * instr->dim1 * 4" in lc and "instr->dim2 * instr->dim1 * 2" in lc)
find_vreg = section(lc, "static tu_vreg_t *find_or_create_vreg", "/* ================================================================\n * Liveness Analysis")
pred("liveness-discards-use-ranges", "(void)start; (void)end" in find_vreg)
pred("liveness-most-recent-region", "most recent definition in this region" in find_vreg and "if (v->region != region) continue" in find_vreg)
pred("liveness-implicit-definition", "v->first_def       = -1" in find_vreg)
uses = section(lc, "static int extract_vreg_uses", "static tu_vreg_t *find_or_create_vreg")
pred("liveness-unbounded-layernorm-use-range", "instr->opcode >= TU_ISA_LAYER_NORM" in uses and "TU_ISA_BATCH_NORM" not in uses)
pred("liveness-implicit-defs-skipped-on-reuse", "if (v->first_def < 0) continue" in find_vreg)
analyze = section(lc, "int tu_live_analyze", "/* ================================================================\n * Interference Graph Construction")
pred("liveness-ignores-vreg-creation-result", analyze.count("find_or_create_vreg(") == 2 and "= find_or_create_vreg" not in analyze)
pred("liveness-analysis-returns-success", analyze.rstrip().endswith("return 0;\n}"))
interference = section(lc, "void tu_live_build_interference", "/* ================================================================\n * Greedy Coloring")
pred("liveness-calloc-unchecked", "g->interference = calloc" in interference and "if (!g->interference" not in interference)
pred("liveness-rebuild-appends-without-reset", "g->num_vregs < TU_LIVE_MAX_VREGS" in interference and "g->num_vregs = 0" not in interference)
pred("liveness-rebuild-replaces-without-free", "g->interference = calloc" in interference and "free(g->interference)" not in interference)
pred("liveness-inclusive-interval-overlap", "vi->first_def <= vj->last_use" in interference and "vj->first_def <= vi->last_use" in interference)
pred("liveness-implicit-defs-no-interference", "vi->first_def >= 0 && vj->first_def >= 0" in interference)

# Capacity, placement, spill selection.
color = section(lc, "void tu_live_color", "/* ================================================================\n * Apply Allocation")
pred("liveness-unsigned-capacity-subtraction", "region_capacity(config, (tu_vreg_region_t)r)\n                          - config->safety_margin" in color)
pred("liveness-first-worst-same-step", "uint32_t step = (config->alloc_strategy == TU_ALLOC_BEST_FIT) ? 4 : 16" in color)
pred("liveness-best-fit-byte-retry", "off += 1" in color)
pred("liveness-no-spill-force-zero", "Without spilling, force placement" in color and "v->physical_offset = 0" in color)
select = section(lc, "static uint32_t select_spill_victim", "void tu_live_color")
pred("liveness-victim-skips-placed", "v->physical_offset != UINT32_MAX" in select)
pred("liveness-victim-default-zero", "uint32_t victim = 0" in select)
pred("liveness-mark-victim-no-free", "g->vregs[victim]->spilled = true" in color and "g->vregs[victim]->physical_offset = UINT32_MAX" not in color)
pred("liveness-current-may-also-spill", "v->spilled = true" in color)
pred("liveness-spill-statistics-can-count-same-current-twice", color.count("result->num_spills++") == 2 and color.count("result->spill_bytes +=") == 2)
pred("liveness-invalid-allocation-enum-not-rejected", "config->alloc_strategy >= TU_ALLOC_COUNT" not in color and "config->alloc_strategy == TU_ALLOC_BEST_FIT" in color)
pred("liveness-invalid-spill-enum-not-rejected", "strategy >= TU_SPILL_COUNT" not in select and "default:" in select)
pred("liveness-colored-only-current-spill-count", "g->colored = (spilled == 0)" in color)

# Rewriting, synthetic spill/fill, and output closure.
patch = section(lc, "static void patch_instruction", "/*\n * Insert a spill DMA instruction")
pred("liveness-patch-selected-opcodes", "TU_ISA_MMA_FUSED" in patch and "TU_ISA_RELU" in patch and "is_load_op" in patch)
pred("liveness-mma-overwrites-all-live-regions", "for (uint32_t i = 0; i < result->num_vregs; i++)" in patch and "v->first_def <= instr_idx && instr_idx <= v->last_use" in patch and "instr->dim0 = v->physical_offset" in patch)
pred("liveness-patch-no-range-identity", "start" not in patch and "end" not in patch)
spill_make = section(lc, "static tu_instruction_t make_spill_instr", "int tu_live_apply")
pred("liveness-synthetic-dma-16bit-truncation", spill_make.count("(uint16_t)(sram_offset & 0xFFFF)") == 2 and spill_make.count("(uint16_t)(size & 0xFFFF)") == 2)
apply = section(lc, "int tu_live_apply", "/* ================================================================\n * Full Allocation Pass")
pred("liveness-fill-every-interval-instruction", "vr->first_def < (int32_t)i && i <= (uint32_t)vr->last_use" in apply)
pred("liveness-original-definition-retained", "output->instructions[out_idx++] = instr" in apply)
pred("liveness-store-after-last-use", apply.index("output->instructions[out_idx++] = instr") < apply.index("If a VReg is spilled, insert spill DMA before it dies") and "vr->last_use == (int32_t)i" in apply)
pred("liveness-output-loop-truncates", "i < n_input && out_idx < TU_SCHED_MAX_INSTRS * 2" in apply)
pred("liveness-output-valid-unconditional", "output->valid = true" in apply and "output->valid = false" in apply)
pred("liveness-a-o-usage-reset-zero", "a_usage = 0" in apply and "o_usage = 0" in apply)
pred("liveness-w-never-reclaimed", "don't reclaim W" in apply)
pred("liveness-spill-slot-never-encoded", "spill_slot" not in apply and "immediates" not in spill_make)

# Test strength and documentation contradictions.
for needle in ["ASSERT_TRUE(output.valid", "at least 4 instructions output", "MMA present in output", "peak W usage within capacity"]:
    pred("liveness-focused-presence-" + re.sub(r"\W+", "-", needle).strip("-"), needle in ltest)
for absent in ["TU_LIVE_MAX_VREGS", "TU_LIVE_MAX_SPILL_SLOTS", "safety_margin =", "65535", "semantic", "memcmp"]:
    pred("liveness-focused-omits-" + re.sub(r"\W+", "-", absent).strip("-"), absent not in ltest)
pred("scheduler-doc-overlap-percent", "Up to 90%" in sdoc and "~70-85%" in sdoc)
pred("liveness-doc-utilization-percent", "~85-95%" in ldoc)
pred("scheduler-doc-fictitious-core-snippet", "tu_core_execute_asm_text" in sdoc and "tu_sched_run(instrs" in sdoc)
pred("liveness-doc-fictitious-pass-pipeline", "Scheduler (C2) → Liveness Allocator (C3)" in ldoc and "tu_live_allocate(scheduled.instructions" in ldoc)
pred("liveness-doc-admits-no-integration", "does not yet coordinate with the liveness-based scratchpad allocator" in sdoc)
pred("onnx-no-pass-calls", "tu_sched_" not in texts.get("compiler/onnx_to_tu.py", "") and "tu_live_" not in texts.get("compiler/onnx_to_tu.py", ""))
pred("asm-no-packed-pass-calls", "tu_sched_" not in texts.get("tu_cmodel/tu_asm.c", "") and "tu_live_" not in texts.get("tu_cmodel/tu_asm.c", ""))
pred("queue-no-pass-calls", "tu_sched_" not in texts.get("tu_cmodel/command_queue.c", "") and "tu_live_" not in texts.get("tu_cmodel/command_queue.c", ""))

# Cross-pass disagreement anchors.
pred("cross-pass-shared-isa-type", "tu_instruction_t" in sh and "tu_instruction_t" in lh)
pred("cross-pass-scheduler-attention-read-a", "case TU_ISA_ATTENTION" in sc and "acc->reads[TU_SRAM_A] = true" in sc)
pred("cross-pass-liveness-attention-no-use-case", "TU_ISA_ATTENTION" not in section(lc, "static int extract_vreg_uses", "static tu_vreg_t *find_or_create_vreg"))
pred("cross-pass-scheduler-elementwise-add-mul", "case TU_ISA_ADD" in sc and "case TU_ISA_MUL" in sc)
pred("cross-pass-liveness-def-add-through-exp", "instr->opcode >= TU_ISA_ADD && instr->opcode <= TU_ISA_EXP" in lc)
pred("cross-pass-liveness-use-relu-through-exp", "instr->opcode >= TU_ISA_RELU && instr->opcode <= TU_ISA_EXP" in lc)
pred("cross-pass-scheduler-strided-channel-high-bits", "instr->opcode == TU_ISA_DMA_LOAD_STRIDED" in sc and "channel = (instr->flags >> 2) & 0x3" in sc)
pred("cross-pass-liveness-strided-channel-low-bits", "TU_ISA_DMA_LOAD_STRIDED" in lc and "uint8_t ch = instr->flags & 0x3" in lc)
pred("cross-pass-no-runtime-consumer", sched_hits == [] and live_hits == [])

checks = len(HASHES) + len(preds)
if errors:
    for e in errors:
        print("CH19_SOURCE_AUDIT ERROR", e)
    print(f"CH19_SOURCE_AUDIT FAIL pin={PIN} hashes={len(HASHES)} predicates={len(preds)} checks={checks}")
    raise SystemExit(1)

print("CH19_SCHED_PUBLIC_APIS count=" + str(len(sched_api)) + " names=" + ",".join(sorted(sched_api)))
print("CH19_LIVE_PUBLIC_APIS count=" + str(len(live_api)) + " names=" + ",".join(sorted(live_api)))
print("CH19_CALLERS scheduler=" + (",".join(sched_hits) or "none") + " liveness=" + (",".join(live_hits) or "none"))
print(f"CH19_SOURCE_AUDIT PASS pin={PIN} hashes={len(HASHES)} predicates={len(preds)} checks={checks}")
