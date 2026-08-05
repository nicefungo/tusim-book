#!/usr/bin/env python3
import hashlib
import re
import sys
from pathlib import Path

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
HASHES = {
"Makefile":"5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
"tu_cmodel/tu_sram.c":"5a6ffcdd3f63c9c015bd628b5c44ded951785a128685b413b6db680f5d1753c0",
"tu_cmodel/tu_sram.h":"aa62a942c83bfded4644c26eabf37acb815b7ac2883b53f6b3b8a585df4123d5",
"tu_cmodel/memory/double_buffer.c":"94d5ac4d1974ec577cb51af7d132c6bf2e7cf405d0eb5626159430555fcdb07a",
"tu_cmodel/memory/double_buffer.h":"c72ae87cc19da132c6ee74ea239099d6056a64ecd266ee944697bf938d141d62",
"tests/test_double_buffer.c":"721a79c0d8013ae48e6852d93536b8bd4b7eb2f09bb6ceafaefa6ac976b932a5",
"tu_cmodel/dma_descriptor.c":"2434c254eef9615b864106de0c453328e64aa6ec49f1e1aff2da5d7e49c8404e",
"tu_cmodel/dma_descriptor.h":"84d6808d7bdbeba9f638d4cd5eb05b15315f2c09225597bec7e996110f144bbb",
"tu_cmodel/compute/pipeline_controller.c":"165522ae3a7853189ed0f6ea114f3e5079487593fb1c06b42a877df53fa1b493",
"tu_cmodel/compute/pipeline_controller.h":"39dc3e73b07b2be30aed4d5569d8064ecba6c1956dfaf52bc428f474904ade21",
"tests/test_pipeline.c":"d07d97354191db0189bc7adb6ec2c26554f374a8b9bae6a0595eea3dc8257d63",
"tu_cmodel/infra/tu_context.c":"ecd0f8258183a9dca0649ca8ed446bee23978571a201fa3464317f31a46762b0",
"tu_cmodel/infra/tu_context.h":"9479cf3a9883ff4b0dbe0e7c7482a9bdad99f2558bd840838e94519e7fa1af28",
"tu_cmodel/memory/memory_hierarchy.c":"3f5d4a71e0bf107e0b5e7581d5d0cf3f7b2a56ec02e4cc39bcf7923b1901c286",
"tu_cmodel/memory/memory_hierarchy.h":"8df3d23ee14b77433cac070bb541e2efb0ce80d5d1ff9fabb886fff8bac20fe8",
"tu_cmodel/infra/config.c":"17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
"tu_cmodel/infra/config.h":"723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
"tu_cmodel/tu_config.h":"129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
"config/tu_config.json":"6f9d292696b1ca5fa38ad3298e7f3a04c43095c0950f71dbe0c3c68b1f15f4db",
"config/tu_config.yaml":"9fb4d87753139a5857107a6fdf56006fcb5adbe95ad30e9f8430c2e5c145910e",
"docs/TU_DOUBLE_BUFFER.md":"287308f70b061e9914740ad879485060d1afddc812ff2858cfb0d4bd8b87c00d",
"docs/software-pipelining.md":"331ee99e658d3ae7189943168b6b1155e8ac48974a9ffd14684daab9af20dd70",
"docs/exploration/double-buffer-mtiling-recovery.md":"19b3a5b97e3b0dcc869f353e3b2e16fbf2e712643b8bbed372f977cfbb16b9a1",
"docs/exploration/sram-wa-buffer-sizing.md":"ff8de6c0ace93c6f0dd82c7b090238aa2038b5aa1982d3f72a1cfbd780027527",
"docs/exploration/sram-obuffer-tiling-threshold.md":"b55a3418a7f2913b7d64089c6b4c6869fb3266f34c5532cbce59214f634e502d",
"tu_cmodel/tu_cmodel.c":"542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
"tu_cmodel/isa/tu_scheduler.c":"b76afa350cc6229fe981e4c188bdc7b8026df4ae74725b3106c624afee9c8893",
"tu_cmodel/isa/tu_scheduler.h":"d0af2cfa650f704b8abefadea0f1bb0bb02029c0d2168b7b608505b0fe1a3426",
"tests/test_scheduler.c":"c35fa60e174b338d9dfbd6e94fa40941820c2d5076b44e3a0ccf1f9cc1db71d0",
"docs/exploration/db-pe-size-goldilocks.md":"81a9f6edc4e6bb2405470d3ff07215fa768dae399dca9419e66b2bf86a3c4b02",
"docs/exploration/pipeline-depth-workload-interaction.md":"57ab0041897ccb1be487a9b0dbaa5a5cd961063e313833bfb5e8dcf99063d9a1",
}

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
pin = sys.argv[2] if len(sys.argv) > 2 else PIN
if pin != PIN:
    print(f"CH16_SOURCE_AUDIT FAIL pin expected={PIN} got={pin}")
    raise SystemExit(1)

texts = {}
errors = []
for rel, expected in HASHES.items():
    p = root / rel
    if not p.is_file():
        errors.append(f"missing {rel}")
        continue
    b = p.read_bytes()
    got = hashlib.sha256(b).hexdigest()
    if got != expected:
        errors.append(f"hash mismatch {rel} expected={expected} got={got}")
    texts[rel] = b.decode("utf-8")

predicates = []
def pred(label, cond):
    predicates.append(label)
    if not cond: errors.append(f"predicate failed {label}")
def body(text, name, next_name):
    a=text.index(name); b=text.index(next_name,a+len(name)); return text[a:b]

db=texts.get("tu_cmodel/memory/double_buffer.c","")
sram=texts.get("tu_cmodel/tu_sram.c","")
dma=texts.get("tu_cmodel/dma_descriptor.c","")
dmah=texts.get("tu_cmodel/dma_descriptor.h","")
pipe=texts.get("tu_cmodel/compute/pipeline_controller.c","")
ctx=texts.get("tu_cmodel/infra/tu_context.c","")
hier=texts.get("tu_cmodel/memory/memory_hierarchy.c","")
hierh=texts.get("tu_cmodel/memory/memory_hierarchy.h","")
mk=texts.get("Makefile","")
json_cfg=texts.get("config/tu_config.json","")
yaml_cfg=texts.get("config/tu_config.yaml","")
configc=texts.get("tu_cmodel/infra/config.c","")

pred("equal-shadow-allocation", "calloc(1, r->total_size)" in db and "buffer_size = r->total_size" in db)
pred("active-starts-primary", "active_idx  = 0" in db)
pred("swap-toggle", "active_idx = (r->db->active_idx == 0) ? 1 : 0" in db)
swap = body(db,"uint64_t tu_sram_swap_buffers","uint8_t *tu_sram_get_active_ptr") if db else ""
pred("swap-no-dirty-precondition", "shadow_dirty" in swap and "if (r->db->shadow_dirty" not in swap and "if (!r->db->shadow_dirty" not in swap)
pred("swap-clears-dirty", "shadow_dirty = false" in swap)
notify = body(db,"void tu_sram_notify_shadow_write","bool tu_sram_is_shadow_dirty") if db else ""
pred("notify-accounting-only", "dma_to_shadow_bytes  += bytes" in notify and "memcpy" not in notify)
pred("notify-no-size-validation", "buffer_size" not in notify and "total_size" not in notify)
pred("disable-preserves-index1", "active_idx == 1" in db and "memcpy(r->banks.data, r->db->shadow_data, r->total_size)" in db)
pred("destroy-frees-db", "free(r->db->shadow_data)" in sram and "free(r->db)" in sram)
init_body = body(sram,"void tu_sram_init_bw","void tu_sram_destroy") if sram else ""
pred("live-reinit-overwrites-before-free", "memset(r, 0, sizeof(*r))" in init_body and "free(" not in init_body)
pred("sram-range-check-can-wrap", "if (addr + size > r->total_size)" in sram)
pred("active-aware-word-access", "memcpy(out, sram_data_ptr(r) + addr" in sram and "memcpy(sram_data_ptr(r) + addr" in sram)
pred("active-aware-bulk-access", "memcpy(out, sram_data_ptr(r) + addr, bytes)" in sram and "memcpy(sram_data_ptr(r) + addr, data, bytes)" in sram)
pred("one-shared-bank-meter", sram.count("bw_banks =") >= 1 and "shadow_data" not in sram[sram.index("static uint64_t sram_bw_consume"):sram.index("/* ---- Lifecycle ----")])
pred("dma-region-precedes-host", "if (desc->dst_region)" in dma and "dst_ptr = tu_sram_raw_ptr(desc->dst_region)" in dma and "dst_ptr = (uint8_t *)desc->dst_host" in dma)
pred("dma-destination-bound-can-wrap", "desc->dst_base + desc->total_bytes > desc->dst_region->total_size" in dma)
pred("dma-source-bound-can-wrap", "desc->src_base + desc->total_bytes > desc->src_region->total_size" in dma)
pred("dma-fixed-channel-array", "channels[TU_DMA_CHANNELS]" in dmah and re.search(r"#define\s+TU_DMA_CHANNELS\s+3\b", texts.get("tu_cmodel/tu_config.h","")) is not None)
pred("pipeline-test-requests-four", "tu_dma_init_full(true, 4, 32)" in texts.get("tests/test_pipeline.c",""))
pred("pipeline-attempts-shadow-redirect", "uint8_t *shadow = tu_sram_get_shadow_ptr" in pipe and "load_desc->dst_host = shadow" in pipe and "load_desc->dst_region = buffer_region" in pipe)
pred("pipeline-swaps-before-notify", pipe.index("tu_sram_swap_buffers") < pipe.index("tu_sram_notify_shadow_write"))
pred("pipeline-ticks-dma", "tu_dma_tick();" in pipe)
pred("pipeline-stores-cmd-id", "tile->cmd_id = cmd_id" in pipe)
pred("pipeline-does-not-dispatch-command", "tu_cmdq_" not in pipe and "tu_command" not in pipe)
pred("pipeline-compute-is-deadline", "cycle_expected = p->current_cycle + tile->compute_cycles" in pipe)
pred("pipeline-overlap-byte-ledger", "overlapped_load_cycles += load_cycles" in pipe and "total_bytes / TU_DMA_BUS_WIDTH_BYTES" in pipe)
pred("pipeline-never-records-db-overlap", "tu_sram_record_overlapped_cycles" not in pipe)
pred("pipeline-reset-destroys", "tu_pipeline_destroy();" in body(pipe,"void tu_pipeline_reset","/* ---- Pipeline slot management ----") and "tu_pipeline_init" not in body(pipe,"void tu_pipeline_reset","/* ---- Pipeline slot management ----"))
pred("context-save-drops-db", "Double-buffer state: skip for now" in ctx and ctx.count("->db = NULL") >= 6)
restore_body = body(ctx,"static int ctx_restore_full_state","/* ================================================================") if ctx else ""
pred("context-restore-nulls-live-db", restore_body.count("->db = NULL") == 3)
pred("context-restore-does-not-free-db", "tu_sram_disable_double_buffer" not in restore_body and "free(" not in restore_body)
pred("hierarchy-declares-db-field", "bool            double_buffered" in hierh)
pred("hierarchy-defaults-local-db-true", '"LocalSPAD",  65536,  8,  4,  2,  2,  2,  4,  2, true' in hier)
pred("hierarchy-retains-field-only", "h->level_configs[level] = *config" in hier and "double_buffered" not in hier)
pred("hierarchy-does-not-enable-db", "tu_sram_enable_double_buffer" not in hier)
pred("json-no-db-config", "double_buffer" not in json_cfg.lower())
pred("yaml-no-db-config", "double_buffer" not in yaml_cfg.lower())
pred("parser-no-db-config", "double_buffer" not in configc.lower())
normal=texts["tu_cmodel/tu_cmodel.c"]
sched=texts["tu_cmodel/isa/tu_scheduler.c"]+texts["tests/test_scheduler.c"]
pred("ordinary-cmodel-does-not-call-pipeline", "tu_pipeline_" not in normal)
pred("ordinary-cmodel-does-not-enable-db", "tu_sram_enable_double_buffer" not in normal)
pred("scheduler-double-buffer-name-only", "double-buffered tile pipeline scheduling" in sched)
pred("scheduler-does-not-call-db", "tu_sram_enable_double_buffer" not in sched and "tu_sram_swap_buffers" not in sched)
pred("scheduler-does-not-call-pipeline-controller", "tu_pipeline_submit_tile" not in sched)
pred("controller-triple-overlap-decorative", pipe.count("enable_triple_overlap") == 1)
pred("controller-timeout-decorative", pipe.count("tile_timeout_cycles") == 1)
pred("controller-absent-dma-baseline-asymmetric", "uint64_t load_cycles = load_desc ?" in pipe and "uint64_t store_cycles = store_desc ?" in pipe and "if (load_desc)" in pipe and "p->total_load_cycles += load_cycles" in pipe and "if (tile->store_desc)" in pipe and "p->total_store_cycles += tile->store_desc->total_bytes" in pipe)
pred("pe-report-analytical", "analytical cycle model" in texts["docs/exploration/db-pe-size-goldilocks.md"])
pred("depth-report-is-separate", "pipeline depth" in texts["docs/exploration/pipeline-depth-workload-interaction.md"].lower())
pred("archive-double-member", "$(TU_DIR)/memory/double_buffer.o" in mk)
pred("archive-pipeline-member", "$(TU_DIR)/compute/pipeline_controller.o" in mk)
pred("pipeline-has-rule", re.search(r"(?m)^test-pipeline:",mk) is not None)
pred("double-has-no-rule", re.search(r"(?m)^test-double:",mk) is None)
flat=mk.replace("\\\n"," ")
test_match=re.search(r"(?m)^test:\s*(.*?)(?:\n\t|\n[^ \t])",flat,re.S)
agg=test_match.group(1) if test_match else ""
pred("pipeline-in-aggregate", "test-pipeline" in agg)
pred("double-not-in-aggregate", "test-double" not in agg)
pred("double-focused-ten-tests", texts.get("tests/test_double_buffer.c","").count("static void test_") == 10)
pred("docs-claim-integration", "DMA/Compute Overlap Model" in texts.get("docs/TU_DOUBLE_BUFFER.md","") and "coordinates double-buffered scratchpads" in texts.get("docs/software-pipelining.md",""))
pred("report-labels-ideal", "enabled (ideal)" in texts.get("docs/exploration/double-buffer-mtiling-recovery.md","") and "Ideal overlap assumption" in texts.get("docs/exploration/double-buffer-mtiling-recovery.md",""))
pred("report-names-one-workload", "M=128, N=128, K=256" in texts.get("docs/exploration/double-buffer-mtiling-recovery.md",""))

# Real caller inventory: source implementation is the only non-test caller of DB mutation APIs;
# no other tu_cmodel C file calls pipeline public APIs.
all_c = list((root/"tu_cmodel").rglob("*.c"))
db_callers=[]; pipe_callers=[]
for p in all_c:
    rel=p.relative_to(root).as_posix(); t=p.read_text(errors="replace")
    if rel != "tu_cmodel/memory/double_buffer.c" and re.search(r"tu_sram_(enable_double_buffer|swap_buffers|notify_shadow_write|record_overlapped_cycles)\s*\(",t): db_callers.append(rel)
    if rel != "tu_cmodel/compute/pipeline_controller.c" and re.search(r"tu_pipeline_(init|submit_tile|advance|sync|get_stats|reset)\s*\(",t): pipe_callers.append(rel)
pred("db-nontest-caller-only-pipeline", db_callers == ["tu_cmodel/compute/pipeline_controller.c"])
pred("pipeline-no-nontest-caller", pipe_callers == [])

checks=len(HASHES)+len(predicates)
if errors:
    for e in errors: print("CH16_SOURCE_AUDIT ERROR",e)
    print(f"CH16_SOURCE_AUDIT FAIL pin={PIN} hashes={len(HASHES)} predicates={len(predicates)} checks={checks}")
    raise SystemExit(1)
print(f"CH16_CALLERS db={','.join(db_callers)} pipeline={'none' if not pipe_callers else ','.join(pipe_callers)}")
print(f"CH16_SOURCE_AUDIT PASS pin={PIN} hashes={len(HASHES)} predicates={len(predicates)} checks={checks}")
