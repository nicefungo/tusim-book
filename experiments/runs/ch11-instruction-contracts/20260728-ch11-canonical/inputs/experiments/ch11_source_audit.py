#!/usr/bin/env python3
"""Fail-closed source/reachability audit for Chapter 11 at the frozen Tusim pin."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
PREDICATES = 0
HASHES = {
    "Makefile": "5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
    "tu_cmodel/command_queue.c": "e8e24987b1cadb61d23bee76085ca7f11b37b7d387eb075033a1651f8a72a389",
    "tu_cmodel/command_queue.h": "cf1f06164d7b3353158c3b70c0667d29b6e94a2ca90a08620232546023363135",
    "tu_cmodel/tu_cmodel.c": "542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
    "tu_cmodel/tu_cmodel.h": "416a0d20776825498217ff5d4382f07ccb2ac9689bbe6c70cacd1bf13e7725af",
    "tu_cmodel/tu_config.h": "129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
    "tu_cmodel/infra/config.c": "17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
    "tu_cmodel/infra/config.h": "723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
    "config/tu_config.json": "6f9d292696b1ca5fa38ad3298e7f3a04c43095c0950f71dbe0c3c68b1f15f4db",
    "tu_cmodel/tu_asm.c": "7d509822dd585bf9f445c96a7be03882a1019d42c39b19f9d14a5b8c5603daee",
    "tu_cmodel/tu_core.c": "0e4b3c6e206465748ae2d3d2e9871f3a6542a61cd1ddcddfff6886b9ed1f0eeb",
    "tu_cmodel/tu_cluster.c": "7c968e95ba0a88fcc27f803be6aa337161bfa691505cdd39b01146252fa77b36",
    "tu_cmodel/bindings/tu_dpi.c": "51ccaa58f226ed4d67f8b6c96b35a8ce77237980503de93e88335a0077d74b8a",
    "tu_cmodel/compute/elementwise_pipeline.c": "e46a698f48bb69ac577b11ff866b4c34953a2ca03e2194bee85558cea4f656e2",
    "tu_cmodel/isa/tu_isa.c": "53bdf44cd720a933da174da55ab1180f8056de9fb2aaa5b9b534adb7af4c387f",
    "tu_cmodel/isa/tu_isa.h": "8efd760c3485492de68b6093d9fa617cdebc2f75de3453310ed3f207b4d16456",
    "tu_cmodel/isa/tu_scheduler.c": "b76afa350cc6229fe981e4c188bdc7b8026df4ae74725b3106c624afee9c8893",
    "tu_cmodel/isa/tu_scheduler.h": "d0af2cfa650f704b8abefadea0f1bb0bb02029c0d2168b7b608505b0fe1a3426",
    "tests/test_command_queue.c": "f15c088772c5ac1eeedd25ceeeb8592f60f6b5386f5a854b5394f1d65e934237",
    "tests/test_isa.c": "1f20a476d30d73485473adf532848d7af3d372167b969d40f9fce9279d93d2d0",
    "tests/test_asm.c": "c76512bc7ad8246c8d5dc747239c2bc1dd1b4872fb44e05bea0432ad660fc024",
    "tests/test_scheduler.c": "c35fa60e174b338d9dfbd6e94fa40941820c2d5076b44e3a0ccf1f9cc1db71d0",
    "tests/test_scheduler_sweep.c": "9a56f263e42dcd7e5573868e388849a4ced6c65576b8f437aaff12f51be9e940",
    "tests/test_config.c": "e2bf7d9a1bbac06863e3b8c372fa1cb854927fc1aeb73a08c79e08cd3f1db821",
    "tests/test_elementwise.c": "5346cc195d6a728990030cb372633ff6343de7c67c6991ce226b4b20ea015317",
    "compiler/onnx_to_tu.py": "9308a86a6c7a986c9fa6cfae6f1b147724de5a78cabaf34656e15de4e4713e2b",
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
    cq = texts["tu_cmodel/command_queue.c"]
    cqh = texts["tu_cmodel/command_queue.h"]
    core = texts["tu_cmodel/tu_cmodel.c"]
    compile_cfg = texts["tu_cmodel/tu_config.h"]
    full_cfg = texts["tu_cmodel/infra/config.c"]
    shipped_cfg = texts["config/tu_config.json"]
    asm = texts["tu_cmodel/tu_asm.c"]
    core_wrapper = texts["tu_cmodel/tu_core.c"]
    dpi = texts["tu_cmodel/bindings/tu_dpi.c"]
    ew = texts["tu_cmodel/compute/elementwise_pipeline.c"]
    isa = texts["tu_cmodel/isa/tu_isa.h"]
    isa_impl = texts["tu_cmodel/isa/tu_isa.c"]
    sched_h = texts["tu_cmodel/isa/tu_scheduler.h"]
    sched = texts["tu_cmodel/isa/tu_scheduler.c"]
    compiler = texts["compiler/onnx_to_tu.py"]

    for obj in ["tu_asm.o", "command_queue.o", "isa/tu_isa.o", "isa/tu_scheduler.o"]:
        must(mk, obj, f"archive-member-{obj}")
    for target in ["test-cmdq", "test-isa", "test-asm", "test-scheduler"]:
        must(mk, target, f"focused-target-{target}")
    must(mk, "test-quick: test-cmodel test-cmdq test-dma test-asm", "quick-includes-cmdq-asm-not-isa")
    must(mk, "test-scheduler test-liveness test-dpi", "aggregate-includes-scheduler")

    must(isa, "_Static_assert(sizeof(tu_instruction_t) == 12", "96-bit-object-size")
    explicit_ops = re.findall(r"^\s*TU_ISA_[A-Z0-9_]+\s*=\s*0x[0-9A-Fa-f]+", isa, re.MULTILINE)
    if len(explicit_ops) != 59:
        raise AssertionError(f"explicit operation enumerator count: {len(explicit_ops)}")
    pass_pred("59-explicit-operation-enumerators")
    name_table = isa_impl[isa_impl.index("opcode_names"):isa_impl.index("const char *tu_isa_opcode_name")]
    named_slots = re.findall(r"^\s*\[[^\]]+\]\s*=", name_table, re.MULTILINE)
    if len(named_slots) != 68:
        raise AssertionError(f"named opcode table slots: {len(named_slots)}")
    pass_pred("68-named-and-60-unknown-catalog-slots")
    must_not(isa, "tu_isa_encode", "no-binary-encoder-api")
    must_not(isa, "tu_isa_decode_instruction", "no-binary-decoder-api")
    must(cqh, "typedef tu_isa_opcode_t tu_cmd_opcode_t", "queue-opcode-alias")
    must(cqh, "union {\n        tu_cmd_dma_desc_t  dma;\n        tu_cmd_mma_desc_t  mma;\n        tu_cmd_ew_desc_t   ew;", "queue-three-operand-forms")

    for case in ["case TU_CMD_NOP:", "case TU_CMD_DMA_LOAD:", "case TU_CMD_DMA_STORE:",
                 "case TU_CMD_MMA:", "case TU_CMD_SYNC:", "case TU_CMD_BARRIER:",
                 "case TU_CMD_HALT:", "case TU_CMD_ELEMENTWISE:"]:
        must(cq, case, f"queue-dispatch-{case.split()[-1].rstrip(':')}")
    must(cq, "default:\n        fprintf(stderr, \"TU CMDQ: unknown opcode", "unsupported-opcode-fault")
    must(cq, "return (int)cmd->cmd_id", "submit-returns-id")
    must(cqh, "Returns 0 on success, -1 if queue is full", "header-return-contract-conflict")
    must(cq, "if (!found) continue;", "missing-dependency-assumed-complete")
    must(cq, "cmd->cycle_submitted = cq->current_cycle;", "submitted-timestamp-written-at-execution")
    must(cq, "if (cq->synchronous) {\n        execute_command(cq, cmd);", "sync-bypasses-dependency-check")
    must(cq, "tu_cmdq_tick(cq);", "async-submit-auto-tick")
    must(cq, "if (cq->synchronous) {\n            cmd->cmd_id = 0", "retirement-guard-inverted")
    must(cq, "return TU_CMD_COMPLETED; /* Not found = already retired */", "unknown-status-completed")
    must(cq, "/* Command already retired, treat as completed */\n            return 0;", "unknown-wait-success")
    must(cq, "cmd->signal_id = cq->next_signal_id++;", "signal-id-assigned")
    must_not(cq, "cq->signal_count++", "signal-registry-never-populated")
    must(cq, "if (cq->synchronous) return; /* Nothing to do */", "sync-drain-no-op")
    reset_block = cq[cq.index("void tu_cmdq_reset"):cq.index("int tu_cmdq_submit")]
    must(reset_block, "cq->next_cmd_id = 1;", "reset-restarts-command-id")
    must_not(reset_block, "next_signal_id", "reset-does-not-restart-signal-id")

    must(core, "desc.num_ops     = num_ops;\n    if (num_ops > 8) num_ops = 8;", "public-ew-count-stored-before-local-clamp")
    must(cq, "tu_ew_apply_fused(sram, cmd->op.ew.sram_offset,\n                          cmd->op.ew.elem_count, ops, cmd->op.ew.num_ops);", "queue-ew-forwards-unclamped-stored-count")
    must(ew, "if (num_ops > TU_EW_MAX_OPS)", "fused-elementwise-rejects-count-above-eight")
    must(ew, "return 0;\n    }\n    memcpy(desc.ops, ops, num_ops * sizeof(tu_ew_op_t));", "fused-elementwise-rejects-before-copy")
    must(core, "tu_cmdq_create(TU_ISA_QUEUE_DEPTH, TU_CYCLE_MODEL == TU_CYCLE_MODEL_FUNCTIONAL)", "compile-time-queue-init")
    must(compile_cfg, "#define TU_ISA_QUEUE_DEPTH      16", "compiled-queue-depth-16")
    must(compile_cfg, "#define TU_ISA_DEP_CHECKING     0", "compiled-dependency-checking-off")
    must(compile_cfg, "#define TU_CYCLE_MODEL               0", "compiled-functional-mode-default")
    must(full_cfg, "cfg->isa_queue_depth     = 16;", "full-config-default-queue-depth-16")
    must(full_cfg, "cfg->isa_dep_checking    = false;", "full-config-default-dependency-off")
    must(full_cfg, "cfg->cycle_model         = 2;", "full-config-default-cycle-model-2")
    must(full_cfg, "parse_opt_bool(isa, \"dependency_checking\", &cfg->isa_dep_checking);", "full-config-parses-dependency-switch")
    must(full_cfg, "if (parse_opt_int64(isa, \"instruction_width_bits\", &iv)) cfg->isa_instr_width_bits", "full-config-parses-instruction-width")
    must(full_cfg, "if (parse_opt_int64(isa, \"queue_depth\", &iv)) cfg->isa_queue_depth", "full-config-parses-queue-depth")
    must(full_cfg, "cfg->cycle_model = parse_cycle_model_str", "full-config-parses-cycle-model")
    converter = full_cfg[full_cfg.index("tu_runtime_config_t tu_config_to_runtime"):full_cfg.index("/* ---- Load from JSON string ----") ]
    for field in ["isa_instr_width_bits", "isa_queue_depth", "isa_dep_checking", "cycle_model"]:
        must_not(converter, field, f"runtime-converter-drops-{field}")
    must(shipped_cfg, '"instruction_width_bits": 96', "shipped-config-instruction-width-96")
    must(shipped_cfg, '"cycle_model": "cycle_accurate"', "shipped-config-cycle-model-label")
    must_not(core, "isa_queue_depth", "parsed-queue-depth-not-consumed-by-core")
    must_not(core, "isa_dep_checking", "parsed-dependency-switch-not-consumed-by-core")

    for mnemonic in ["LOAD_W", "LOAD_A", "LOAD_O", "STORE_O", "MMA", "SYNC"]:
        must(asm, f'"{mnemonic}"', f"legacy-asm-{mnemonic}")
    must_not(asm, '"BARRIER"', "legacy-asm-no-barrier")
    must(asm, "tu_init();", "asm-reinitializes-global-state")
    must_not(asm, "tu_cmdq_submit", "asm-bypasses-command-queue")
    must_not(asm, "tu_sched_", "asm-bypasses-scheduler")
    must_not(asm, "tu_instruction_t", "asm-does-not-construct-packed-instructions")
    must(asm, "tu_asm_find_buffer(s, name, NULL)", "asm-discards-host-buffer-size")
    must(core_wrapper, "int result = tu_run_asm(program, buffers, n_buffers);", "core-wrapper-reaches-legacy-asm")
    must(dpi, "tu_cmdq_submit_mma", "dpi-reaches-queue-mma-wrapper")
    must(dpi, "tu_cmdq_submit_barrier", "dpi-reaches-queue-barrier-wrapper")

    must_not(compiler, "tu_instruction_t", "compiler-does-not-emit-binary-isa")
    must_not(compiler, "tu_sched_run", "compiler-does-not-run-scheduler")

    must(sched, "if (config && config->hoist_dma)", "null-default-disables-hoist")
    must(sched, "if (config && config->insert_barriers)", "null-default-disables-insertion")
    must(sched, "result->num_barriers_inserted = 0;", "list-schedule-clears-barrier-count")
    must(sched, "result->num_dma_hoisted = 0;", "list-schedule-clears-hoist-count")
    must(sched, "return barriers_inserted;", "insertion-only-counts")
    must_not(sched, "graph->num_nodes++", "insertion-does-not-add-node")
    must(sched, "hoisted++;", "dma-hoist-only-counts-candidate")
    must(sched_h, "#define TU_SCHED_MAX_DEPS          16", "scheduler-edge-capacity-16")
    must(sched, "if (producer->num_succs >= TU_SCHED_MAX_DEPS\n                    || consumer->num_preds >= TU_SCHED_MAX_DEPS) continue;", "scheduler-silently-drops-excess-edges")
    must(sched, "if (producer->is_barrier) continue;", "scheduler-skips-barrier-as-later-predecessor")
    if sched.count("pipeline_tiles") != 1:
        raise AssertionError("pipeline_tiles must appear only in the default initializer")
    pass_pred("pipeline-tiles-config-not-consumed")
    if sched.count("max_window") != 1:
        raise AssertionError("max_window must appear only in the default initializer")
    pass_pred("max-window-config-not-consumed")
    must(sched, "result->estimated_cycles += (node->is_dma ? 1 : 4);", "serial-fixed-cost-estimate")

    def c_callers(pattern: str) -> set[str]:
        rx = re.compile(pattern)
        return {
            p.relative_to(root).as_posix()
            for p in root.rglob("*.c")
            if rx.search(p.read_text(encoding="utf-8"))
        }

    inventories = [
        (r"tu_sched_[A-Za-z0-9_]+\(", {
            "tu_cmodel/isa/tu_scheduler.c", "tests/test_scheduler.c", "tests/test_scheduler_sweep.c"},
         "whole-tree-scheduler-call-surface"),
        (r"tu_core_execute_asm_text|tu_run_asm\(", {
            "tu_cmodel/tu_asm.c", "tu_cmodel/tu_core.c", "tu_cmodel/tu_cluster.c", "tests/test_asm.c"},
         "whole-tree-legacy-asm-call-surface"),
        (r"tu_cmdq_submit(?:_mma|_dma_load|_dma_store|_elementwise)?\(|tu_cmdq_barrier\(", {
            "tu_cmodel/command_queue.c", "tu_cmodel/tu_cmodel.c", "tu_cmodel/bindings/tu_dpi.c",
            "tests/test_command_queue.c", "tests/test_elementwise.c"},
         "whole-tree-command-queue-call-surface"),
    ]
    for pattern, expected, label in inventories:
        actual = c_callers(pattern)
        if actual != expected:
            raise AssertionError(f"{label}: expected={sorted(expected)} actual={sorted(actual)}")
        pass_pred(label)

    print(f"CH11_SOURCE_AUDIT PASS pin={PIN} hashes={len(HASHES)} predicates={PREDICATES} checks={len(HASHES) + PREDICATES}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"CH11_SOURCE_AUDIT FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
