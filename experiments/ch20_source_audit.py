#!/usr/bin/env python3
"""Fail-closed Chapter 20 source audit for claim-to-evidence authorization."""
from __future__ import annotations
import hashlib, re, sys
from pathlib import Path
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
EXPECTED_HASHES = {
    ".github/workflows/ci.yml": "0919e0f56293b270d3f4dfd4547840aeec1d300d08d45700b8976b86cf043d85",
    "Makefile": "5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
    "bindings/python/tu_bindings.py": "74562a1c19a47ab8c16e5d92c363a3c3a885c566250eb2fa29434a20851e6740",
    "docs/differential-testing.md": "89e650cd8fa993429020ca53c589c7624a34e52326d70df5e5b7057e774d941f",
    "tests/test_debug.c": "7412ff49960fa6e1b1aac0329362494f2a0dd6631a61667f777d96ea3b94d9eb",
    "tests/test_dpi.c": "0909af36397c2cfecc9be04ca27753a2e8af228e327071af350d5dedfc30ae05",
    "tests/test_error_handling.c": "1c203189c5fc5d55d101bd8834d531b6e504bc04f4744ffd3dd16aa21bbd867a",
    "tests/test_framework.h": "a8bf7f5e2e5ce9c317f1e089bc28338b4bd298a8bec6c08f40c6a5f12bb979ef",
    "tests/test_golden.c": "3399574368c8d25ba3ec0d908402cc8d34936d49f9ef52504b30da9a78558422",
    "tests/test_random.c": "704c1dbd4a2aa648784f00bda8e69ab7efc4e2bf7aec364721c0cc9baa6e41f3",
    "tools/ci_runner.sh": "288f429d8e9fc567269b490c5fe6f41f81ea76b6278da817188fd56894dce0ba",
    "tools/test_report.py": "efe1f995f0fa4f0167e570712a7c945176402487396fed0b6e58a637e45c9851",
    "tu_cmodel/bindings/tu_dpi.c": "51ccaa58f226ed4d67f8b6c96b35a8ce77237980503de93e88335a0077d74b8a",
    "tu_cmodel/bindings/tu_dpi.h": "2d322616199ac02d49265c37b5b95d4c1be9920cd4db018cf9d6744c012e8495",
    "tu_cmodel/infra/config.c": "17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
    "tu_cmodel/infra/config.h": "723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
    "tu_cmodel/infra/random_tensor.h": "ac1e4a55059a0058716b8c91a90eb081540dd22f9776dcbefab0dbb7fe2d98ff",
    "tu_cmodel/infra/tu_debug.c": "20001ec404295e4a4a2ef497a0ace0bb63c8415d4a58858d3172bcb19213dd8d",
    "tu_cmodel/infra/tu_debug.h": "81b32d8051fd1eea1c8aa93c530c8b780f395e778ffdbb350d0040767fbfaca4",
    "tu_cmodel/tu_cmodel.c": "542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
    "tu_cmodel/tu_core.c": "0e4b3c6e206465748ae2d3d2e9871f3a6542a61cd1ddcddfff6886b9ed1f0eeb",
    "tu_cmodel/tu_config.h": "129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d"
}
EXPECTED_SOURCES = ['test_address_gen.c', 'test_asm.c', 'test_attention.c', 'test_attention_sweep.c', 'test_benchmark.c', 'test_bf16_subnormal.c', 'test_cmodel.c', 'test_command_queue.c', 'test_compress.c', 'test_config.c', 'test_context.c', 'test_context_switch_sweep.c', 'test_conv_groups_sweep.c', 'test_conv_pool_cascade.c', 'test_conv_sweep.c', 'test_convolution.c', 'test_cycle_model.c', 'test_dataflow.c', 'test_dataflow_sweep.c', 'test_debug.c', 'test_dma.c', 'test_double_buffer.c', 'test_dpi.c', 'test_dram.c', 'test_elementwise.c', 'test_error_handling.c', 'test_fp8.c', 'test_golden.c', 'test_int8_sweep.c', 'test_int_quant.c', 'test_interconnect_contention_sweep.c', 'test_interconnect_routing_sweep.c', 'test_interconnect_switching_sweep.c', 'test_interconnect_topology_sweep.c', 'test_isa.c', 'test_liveness.c', 'test_logging.c', 'test_memory_hierarchy.c', 'test_mma_activation_sweep.c', 'test_multicast.c', 'test_multicore.c', 'test_multicore_scaling_sweep.c', 'test_norm_attention_sweep.c', 'test_norm_sweep.c', 'test_normalization.c', 'test_perf_counters.c', 'test_pipeline.c', 'test_pooling.c', 'test_pooling_sweep.c', 'test_power_model.c', 'test_random.c', 'test_rounding.c', 'test_rounding_sweep.c', 'test_scatter_gather.c', 'test_scheduler.c', 'test_scheduler_sweep.c', 'test_softmax.c', 'test_softmax_attention_sweep.c', 'test_softmax_sweep.c', 'test_sparsity.c', 'test_sparsity_sweep.c', 'test_tf32.c', 'test_trace.c', 'test_weight_compression_sweep.c']
EXPECTED_RELATION = {'test_address_gen.c': ['test-agen'], 'test_attention.c': ['test-attention'], 'test_attention_sweep.c': ['test-attention-sweep'], 'test_benchmark.c': ['test-bench'], 'test_bf16_subnormal.c': ['test-bf16'], 'test_cmodel.c': ['test-cmodel'], 'test_command_queue.c': ['test-cmdq'], 'test_compress.c': ['test-compress'], 'test_config.c': ['test-config'], 'test_context.c': ['test-context'], 'test_context_switch_sweep.c': ['test-context-switch-sweep'], 'test_conv_groups_sweep.c': ['test-conv-groups-sweep'], 'test_conv_pool_cascade.c': ['test-conv-pool-cascade'], 'test_conv_sweep.c': ['test-conv-sweep'], 'test_convolution.c': ['test-conv'], 'test_dataflow.c': ['test-dataflow'], 'test_dataflow_sweep.c': ['test-dataflow-sweep'], 'test_debug.c': ['test-debug'], 'test_dma.c': ['test-dma'], 'test_dpi.c': ['test-dpi'], 'test_dram.c': ['test-dram'], 'test_elementwise.c': ['test-elementwise'], 'test_error_handling.c': ['test-errors'], 'test_fp8.c': ['test-fp8'], 'test_golden.c': ['test-golden', 'test-golden-full'], 'test_int_quant.c': ['test-int-quant'], 'test_interconnect_contention_sweep.c': ['test-interconnect-contention-sweep'], 'test_interconnect_routing_sweep.c': ['test-interconnect-routing-sweep'], 'test_interconnect_switching_sweep.c': ['test-interconnect-switching-sweep'], 'test_interconnect_topology_sweep.c': ['test-interconnect-topology-sweep'], 'test_isa.c': ['test-isa'], 'test_liveness.c': ['test-liveness'], 'test_logging.c': ['test-logging'], 'test_memory_hierarchy.c': ['test-memhier'], 'test_mma_activation_sweep.c': ['test-mma-activation-sweep'], 'test_multicast.c': ['test-multicast'], 'test_multicore.c': ['test-multicore'], 'test_multicore_scaling_sweep.c': ['test-multicore-sweep'], 'test_norm_attention_sweep.c': ['test-norm-attention-sweep'], 'test_norm_sweep.c': ['test-norm-sweep'], 'test_normalization.c': ['test-norm'], 'test_perf_counters.c': ['test-perf'], 'test_pipeline.c': ['test-pipeline'], 'test_pooling.c': ['test-pool'], 'test_pooling_sweep.c': ['test-pooling-sweep'], 'test_power_model.c': ['test-power'], 'test_random.c': ['test-random'], 'test_rounding.c': ['test-rounding'], 'test_rounding_sweep.c': ['test-rounding-sweep'], 'test_scatter_gather.c': ['test-scatter-gather'], 'test_scheduler.c': ['test-scheduler'], 'test_scheduler_sweep.c': ['test-scheduler-sweep'], 'test_softmax_attention_sweep.c': ['test-softmax-attention-sweep'], 'test_softmax_sweep.c': ['test-softmax-sweep'], 'test_sparsity.c': ['test-sparsity'], 'test_sparsity_sweep.c': ['test-sparsity-sweep'], 'test_tf32.c': ['test-tf32'], 'test_trace.c': ['test-trace'], 'test_weight_compression_sweep.c': ['test-weight-compression-sweep']}
EXPECTED_AGG = ['test-cmodel', 'test-cmdq', 'test-dma', 'test-dram', 'test-isa', 'test-golden', 'test-elementwise', 'test-bf16', 'test-memhier', 'test-norm', 'test-dataflow', 'test-logging', 'test-int-quant', 'test-conv', 'test-asm', 'test-rounding', 'test-fp8', 'test-attention', 'test-perf', 'test-pool', 'test-pipeline', 'test-agen', 'test-multicore', 'test-multicast', 'test-scatter-gather', 'test-trace', 'test-config', 'test-sparsity', 'test-scheduler', 'test-liveness', 'test-dpi']
EXPECTED_QUICK = ['test-cmodel', 'test-cmdq', 'test-dma', 'test-asm']
EXPECTED_CI_QUICK = ['test-cmodel', 'test-cmdq', 'test-dma', 'test-golden']
EXPECTED_CI_FULL = ['test-cmodel', 'test-cmdq', 'test-dma', 'test-dram', 'test-isa', 'test-golden', 'test-elementwise', 'test-bf16', 'test-memhier', 'test-norm', 'test-dataflow', 'test-logging', 'test-int-quant', 'test-conv']
EXPECTED_NON_SWEEP_AGG_OMISSIONS = ['test_asm.c', 'test_benchmark.c', 'test_compress.c', 'test_context.c', 'test_conv_pool_cascade.c', 'test_cycle_model.c', 'test_debug.c', 'test_double_buffer.c', 'test_error_handling.c', 'test_power_model.c', 'test_random.c', 'test_softmax.c', 'test_tf32.c']

def check(name: str, ok: bool, failures: list[str]) -> None:
    print(f"CHECK {name}={'PASS' if ok else 'FAIL'}")
    if not ok: failures.append(name)

def rules(text: str) -> dict[str,str]:
    flat=text.replace("\\\n", " ")
    return {m.group(1):m.group(2).strip() for m in re.finditer(r"(?m)^([A-Za-z0-9_.-]+)\s*:\s*([^\n]*)$", flat)}

def main() -> int:
    if len(sys.argv)!=3:
        print("usage: ch20_source_audit.py ARCHIVE PIN", file=sys.stderr); return 2
    root=Path(sys.argv[1]); pin=sys.argv[2]; failures=[]; checks=0
    check("pin", pin==PIN, failures); checks+=1
    for rel,want in EXPECTED_HASHES.items():
        p=root/rel; got=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "MISSING"
        check("hash:"+rel, got==want, failures); checks+=1
    make=(root/'Makefile').read_text(); ci=(root/'tools/ci_runner.sh').read_text(); report=(root/'tools/test_report.py').read_text()
    framework=(root/'tests/test_framework.h').read_text(); golden=(root/'tests/test_golden.c').read_text(); random=(root/'tests/test_random.c').read_text()
    debug_t=(root/'tests/test_debug.c').read_text(); err_t=(root/'tests/test_error_handling.c').read_text(); dpi_t=(root/'tests/test_dpi.c').read_text()
    dbg=(root/'tu_cmodel/infra/tu_debug.c').read_text(); dbgh=(root/'tu_cmodel/infra/tu_debug.h').read_text(); cfg=(root/'tu_cmodel/infra/config.c').read_text(); bind=(root/'bindings/python/tu_bindings.py').read_text(); workflow=(root/'.github/workflows/ci.yml').read_text(); rt=(root/'tu_cmodel/infra/random_tensor.h').read_text()
    cmodel=(root/'tu_cmodel/tu_cmodel.c').read_text(); core=(root/'tu_cmodel/tu_core.c').read_text(); tuconfig=(root/'tu_cmodel/tu_config.h').read_text()
    rr=rules(make); test_sources=sorted(p.name for p in (root/'tests').glob('test_*.c'))
    source_to_targets={}
    for target,dep in rr.items():
        for s in re.findall(r"tests/(test_[A-Za-z0-9_]+\.c)",dep): source_to_targets.setdefault(s,[]).append(target)
    source_to_targets={key:sorted(value) for key,value in sorted(source_to_targets.items())}
    agg=[x for x in rr['test'].split() if x.startswith('test-')]; quick=[x for x in rr['test-quick'].split() if x.startswith('test-')]
    no_rule=[s for s in test_sources if s not in source_to_targets]
    aggregate_sources={s for s,targets in source_to_targets.items() if set(targets)&set(agg)}
    non_sweep_agg_omissions=sorted(s for s in test_sources if 'sweep' not in s and s not in aggregate_sources)
    ciq=re.search(r'if \[ "\$QUICK_MODE" = true \]; then\s*TEST_TARGETS=\((.*?)\)\s*else',ci,re.S)
    cif=re.search(r'else\s*TEST_TARGETS=\((.*?)\)\s*fi',ci,re.S)
    ci_quick=re.findall(r'"(test-[A-Za-z0-9-]+):',ciq.group(1)); ci_full=re.findall(r'"(test-[A-Za-z0-9-]+):',cif.group(1))
    workflow_calls=re.findall(r'run: bash tools/ci_runner\.sh([^\n]*)',workflow)
    random_seeds=sorted(int(x) for x in re.findall(r'tu_random_seed\(&rng, (\d+)\);',random))
    config_conversion=cfg[cfg.index('tu_config_to_runtime'):cfg.index('/* ---- Load from JSON string ---- */')]
    dpi_layer=dpi_t[dpi_t.index('static void test_layernorm'):dpi_t.index('/* ---- Test 8:')]
    dpi_async=dpi_t[dpi_t.index('static void test_async_cmd'):dpi_t.index('/* ---- Test 11:')]
    owner_text='\n'.join((make,ci,workflow))
    predicates={
      'inventory-exact-64-sources':test_sources==EXPECTED_SOURCES,
      'inventory-exact-59-source-target-relation':source_to_targets==EXPECTED_RELATION,
      'inventory-exact-31-aggregate':agg==EXPECTED_AGG,
      'inventory-exact-4-quick':quick==EXPECTED_QUICK,
      'inventory-five-relation-omissions':no_rule==['test_asm.c','test_cycle_model.c','test_double_buffer.c','test_int8_sweep.c','test_softmax.c'],
      'inventory-exact-13-nonsweep-aggregate-omissions':non_sweep_agg_omissions==EXPECTED_NON_SWEEP_AGG_OMISSIONS,
      'ci-exact-quick-set':ci_quick==EXPECTED_CI_QUICK,
      'ci-exact-full-set':ci_full==EXPECTED_CI_FULL,
      'workflow-exact-runner-calls':workflow_calls==[' --quick','',' --random --valgrind',' --coverage'],
      'make-suppresses-generated-compile':'/tmp/gpt_block_tu.c -I. -L. -ltucmodel $(LDFLAGS) 2>&1 || true' in make,
      'make-suppresses-generated-run':'/tmp/gpt_block_tu 2>&1 || true' in make,
      'fixed-host-global-paths':'-o /tmp/test_asm' in make and '/tmp/gpt_block_tu.c' in make and 'rm -f /tmp/gpt_block_tu /tmp/gpt_block_tu.c /tmp/test_asm' in make,
      'ci-clean-after-report-dir':ci.index('mkdir -p "$REPORT_DIR" "$LOG_DIR"') < ci.index('make clean'),
      'clean-removes-report-dir':'rm -rf build/ci_reports' in make,
      'ci-compile-fallback-status-suppressed':'make CC="$CC" CFLAGS="$CFLAGS_BASE" "$(echo $target | sed \'s/test-//\')" > /dev/null 2>&1 || true' in ci and 'OVERALL_EXIT=1' not in ci[ci.index('# Try with explicit compile'):ci.index('done',ci.index('# Try with explicit compile'))],
      'quick-golden-status-suppressed':'test-golden > "$local_log" 2>&1 || true' in ci,
      'quick-golden-text-authority':'grep -q "PASS" "$local_log"' in ci,
      'coverage-status-suppressed':'gcov -r tu_cmodel/*.c tu_cmodel/*/*.c > "$LOG_DIR/coverage.log" 2>&1 || true' in ci,
      'coverage-forced-pass':'record_result "Coverage report" "PASS"' in ci,
      'report-exit-absent':'"exit_code": -1' in report and 'result["exit_code"] =' not in report,
      'report-tail-can-override-failure':'if "PASS" in content[-200:] or "passed" in content[-200:].lower()' in report,
      'shared-comparator-nan-blind':'float err = fabsf(a[i] - b[i]);' in framework and 'if (err > max_err) max_err = err;' in framework,
      'golden-local-oracle':'static void compute_fp32_reference' in golden and 'O[m * N + n] = sum;' in golden,
      'golden-local-comparator-nan-blind':'float err = fabsf(a[i] - b[i]);' in golden and 'if (err > max_err) max_err = err;' in golden and 'max_err <= tolerance' in golden,
      'random-repository-oracle':'tu_golden_gemm_fp32' in random and 'tu_golden_softmax' in random and 'tu_golden_gemm_fp32' in rt,
      'random-make-target-compiles-and-runs':'test-random: tests/test_random.c libtucmodel.a' in make and '\n\t./test-random\n' in make,
      'random-ci-runs-target-then-binary':'make CC="$CC" CFLAGS="$CFLAGS_BASE" test-random' in ci and './test-random > "$LOG_DIR/test_random.log"' in ci,
      'random-exact-fixed-seeds':random_seeds==[42,99,777,888],
      'config-parses-dataflow':'cfg->dataflow_mode = parse_dataflow_str' in cfg,
      'runtime-conversion-drops-dataflow':'rt.pe_rows' in config_conversion and 'dataflow' not in config_conversion,
      'initialization-selects-compiletime-dataflow':'tu_set_dataflow(TU_DATAFLOW_MODE);' in cmodel and re.search(r'#define\s+TU_DATAFLOW_MODE\s+TU_DATAFLOW_MODE_WS',tuconfig) is not None,
      'core-reinit-uses-default-config':'void tu_core_init(tu_core_t *core)' in core and 'tu_init();' in core[core.index('void tu_core_init'):core.index('void tu_core_destroy')],
      'debug-text-json-return-zero':'size_t total = 0;' in dbg and 'return total;' in dbg,
      'debug-tests-use-vacuous-size':debug_t.count('CHECK(n >= 0, "dump returned negative")')==2,
      'debug-checksum-tautology':'CHECK(cs != 0 || cs == 0' in debug_t,
      'replay-header-claims-reissue':'Each instruction is re-issued in order' in dbgh,
      'replay-executes-no-op':'(void)M; (void)N; (void)K;' in dbg and 'Execute the instruction via the core' in dbg,
      'replay-not-tested-execute':'tu_debug_replay_execute' not in debug_t,
      'bounds-addition-can-wrap':'if (addr + size <= limit) return true;' in dbg,
      'tile-check-ignores-pe-dimensions':'(void)pe_rows; (void)pe_cols;' in dbg and 'if (tile_M > 0 && tile_N > 0) return true;' in dbg,
      'error-injection-never-reached':"this won't match" in err_t and 'tu_error_inject_disable_all();' in err_t,
      'dpi-native-identity-producer':'GEMM identity matrix via DPI' in dpi_t and 'tu_dpi_gemm' in dpi_t and 'W[i * N + i] = fp16_one();' in dpi_t,
      'dpi-no-hdl-simulator-owner':not any(x in owner_text.lower() for x in ('iverilog','verilator','questa','modelsim','vcs ')),
      'dpi-layernorm-no-output-check':'tu_dpi_layernorm' in dpi_layer and 'tu_dpi_sram_read' not in dpi_layer,
      'dpi-async-no-output-check':'tu_dpi_submit_gemm' in dpi_async and 'tu_dpi_sram_read' not in dpi_async,
      'binding-nonsymmetric-capable':'def quick_gemm' in bind,
      'binding-no-make-ci-owner':all(x not in owner_text for x in ('bindings/python/tu_bindings.py','tu_bindings','quick_gemm')),
      'binding-full-api-overclaim':'exposes the full TU core API' in bind,
      'binding-performance-stub':'# For now, return stub' in bind and 'Performance counters: use C API tu_print_stats()' in bind,
      'binding-power-stub':'return "Power model: use C API tu_power_print_report()"' in bind,
      'binding-config-path-unused':'self._config_path = config_path' in bind and 'tu_config_load' not in bind,
    }
    external=[]
    for p in root.rglob('*.c'):
        rel=p.relative_to(root).as_posix()
        if rel in ('tu_cmodel/infra/tu_debug.c','tests/test_debug.c'): continue
        txt=p.read_text(errors='replace')
        if any(x in txt for x in ('tu_debug_record_instr(','tu_debug_replay_execute(','tu_debug_assert_range(','tu_debug_assert_alignment(','tu_debug_assert_bounds(','tu_debug_assert_tile_dims(','tu_debug_assert_dataflow(')): external.append(rel)
    predicates['debug-replay-invariant-direct-external-callers-zero']=external==[]
    for name,ok in predicates.items(): check('predicate:'+name,ok,failures); checks+=1
    print(f"CH20_SOURCE_AUDIT {'PASS' if not failures else 'FAIL'} pin={pin} hashes={len(EXPECTED_HASHES)} predicates={len(predicates)} checks={checks}")
    if failures: print('FAILURES '+' '.join(failures))
    return 0 if not failures else 1
if __name__=='__main__': raise SystemExit(main())
