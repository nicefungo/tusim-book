#!/usr/bin/env python3
import hashlib,re,sys
from pathlib import Path
PIN="e918c80b6fce833cd1fcae97730fa841c2176f25"
HASHES={
"Makefile":"5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
"tu_cmodel/tu_cmodel.c":"542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
"tu_cmodel/tu_cmodel.h":"416a0d20776825498217ff5d4382f07ccb2ac9689bbe6c70cacd1bf13e7725af",
"tu_cmodel/tu_core.c":"0e4b3c6e206465748ae2d3d2e9871f3a6542a61cd1ddcddfff6886b9ed1f0eeb",
"tu_cmodel/tu_core.h":"dc5c22065fb65be4353585ccbfd3bec6c9b9d70e976a51e87169bac79dd164e9",
"tu_cmodel/tu_config.h":"129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
"tu_cmodel/infra/config.c":"17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
"tu_cmodel/infra/config.h":"723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
"tu_cmodel/infra/logging.c":"feac7a4de99b1d89fc0b795d55684b3b286a60d4c6cce366caff881244fdbef5",
"tu_cmodel/infra/logging.h":"1aef7ae8c6552d172b7d1a0bb221baaba5234a2fce26fd335e05c27d88108853",
"tu_cmodel/perf/performance_counters.c":"f7d9a5ec33c873cb4c900902d3c8d168622be782a8979cc6a822211c471807f2",
"tu_cmodel/perf/performance_counters.h":"5d323e9af226f2012c71eb4cc5fe917edc9a5cdd314782affeb9de3e21fdf6b5",
"tu_cmodel/perf/event_trace.c":"6a9dd3d9b8ca18e0626416556414d0d4ef1fb9e047124014161c4bf00c8f81b2",
"tu_cmodel/perf/event_trace.h":"bdcc5c881ea0bb44ced2482bb0fc31325245ed7dc30319816913169ad5e54854",
"tu_cmodel/perf/cycle_model.c":"b197a6ab411f5ab2d152a99ae233bb25abb2d1912d1f4fa8a94a88e7e1879fec",
"tu_cmodel/perf/cycle_model.h":"0f0301d824be11f2fb4cfc96fd53ae9b64db841de6fb15d989e4f42d846b7101",
"tu_cmodel/perf/power_model.c":"5cba597200fba469eb6b21a8d0bbb5c542a5a61538d886f74aa0aa74e076325d",
"tu_cmodel/perf/power_model.h":"5ab29337c7ace216bbf182a8003a46f24f6b98e7cad535dd6ac94b32c48fe6e1",
"tests/test_perf_counters.c":"683433104a629398061794a9f69b4d56ca5b491dadb18cdd57e53057196870c9",
"tests/test_trace.c":"061556c45d43a49090ed28384faf9561a1cf97348d443c9eac91fc5f7fa67f53",
"tests/test_logging.c":"d6c34d5b2e79fa873747be11b6661ef4172191849f529d957dafb54a3e6d90dc",
"tests/test_cycle_model.c":"606e4325ca31e71c19cc05101ccf76db95a2be95d1bbb57fef7e19ca9d398ca9",
"tests/test_power_model.c":"0d96adfa610df06a3dff15fcd692acb61c9a348b85ca660e4c4c764bc2c61ba6",
"tests/test_benchmark.c":"23d9ec53903850fe52cb6316894ade2aa159491b1f1b9744f147403639aac2d3",
"tests/test_config.c":"e2bf7d9a1bbac06863e3b8c372fa1cb854927fc1aeb73a08c79e08cd3f1db821",
"config/tu_config.json":"6f9d292696b1ca5fa38ad3298e7f3a04c43095c0950f71dbe0c3c68b1f15f4db",
"config/tu_config.yaml":"9fb4d87753139a5857107a6fdf56006fcb5adbe95ad30e9f8430c2e5c145910e",
"docs/performance-counters.md":"1a96cc4e556c38ebb7e0b534f110acba1cb40d24eac005af0086576cc6475011",
"docs/event-tracing-vcd.md":"4c86320d967efd7b793f94fb046880ca21bb3e4995c7d3f0d2ebd8b88a7bd48a",
"docs/power-energy-model.md":"56f64daa74a3294bd9749bd086bff833f0d7a67a587565bc84fa8d6f18dedc29",
"docs/cycle-accurate-model.md":"8e565e8ca36880bb4b45f97e423afb2bcd139f19b2f60b2f9eeb97086ec7bb31",
}
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd(); pin=sys.argv[2] if len(sys.argv)>2 else PIN
if pin!=PIN: print(f"CH17_SOURCE_AUDIT FAIL pin expected={PIN} got={pin}"); raise SystemExit(1)
texts={}; errors=[]
for rel,expected in HASHES.items():
 p=root/rel
 if not p.is_file(): errors.append(f"missing {rel}"); continue
 b=p.read_bytes(); got=hashlib.sha256(b).hexdigest()
 if got!=expected: errors.append(f"hash mismatch {rel} expected={expected} got={got}")
 texts[rel]=b.decode('utf-8',errors='replace')
preds=[]
def pred(label,cond):
 preds.append(label)
 if not cond: errors.append(f"predicate failed {label}")
def section(t,start,end):
 a=t.index(start); b=t.index(end,a+len(start)); return t[a:b]
mk=texts.get('Makefile',''); perf=texts.get('tu_cmodel/perf/performance_counters.c',''); ph=texts.get('tu_cmodel/perf/performance_counters.h','')
ev=texts.get('tu_cmodel/perf/event_trace.c',''); log=texts.get('tu_cmodel/infra/logging.c',''); cyc=texts.get('tu_cmodel/perf/cycle_model.c',''); power=texts.get('tu_cmodel/perf/power_model.c','')
cfg=texts.get('tu_cmodel/infra/config.c',''); cfgh=texts.get('tu_cmodel/infra/config.h',''); bench=texts.get('tests/test_benchmark.c','')
cfg_json=texts.get('config/tu_config.json',''); cfg_yaml=texts.get('config/tu_config.yaml','')
# Linkage/test classification
pred('perf-archive-member','$(TU_DIR)/perf/performance_counters.o' in mk)
pred('event-trace-archive-member','$(TU_DIR)/perf/event_trace.o' in mk)
pred('power-archive-member','$(TU_DIR)/perf/power_model.o' in mk)
pred('cycle-not-archive-member','cycle_model.o' not in section(mk,'TU_OBJS =','libtucmodel.a:'))
for name in ['test-perf','test-trace','test-logging','test-power','test-bench']:
 pred(f'{name}-has-rule',re.search(rf'(?m)^{re.escape(name)}:',mk) is not None)
pred('cycle-has-no-rule',re.search(r'(?m)^test-cycle[^:]*:',mk) is None)
flat=mk.replace('\\\n',' '); mt=re.search(r'(?m)^test:\s*(.*?)(?:\n\t|\n[^ \t])',flat,re.S); agg=mt.group(1) if mt else ''
for name in ['test-perf','test-trace','test-logging']: pred(f'{name}-aggregate',name in agg)
for name in ['test-power','test-bench']: pred(f'{name}-not-aggregate',name not in agg)
# Perf semantics
for needle in ['tu_perf_dma_record_read','tu_perf_dma_record_write','tu_perf_compute_record_mma','tu_perf_compute_record_op','tu_perf_compute_record_idle']:
 pred(f'{needle}-ticks','tu_perf_tick' in section(perf,f'void {needle}','\n}') if f'void {needle}' in perf else False)
pred('spad-ticks-stall','tu_perf_tick(c, stall_cycles)' in section(perf,'void tu_perf_mem_record_spad_access','void tu_perf_mem_record_gbuf_access'))
pred('gbuf-does-not-tick','tu_perf_tick' not in section(perf,'void tu_perf_mem_record_gbuf_access','void tu_perf_mem_record_dram_access'))
pred('dram-ticks-stall','tu_perf_tick(c, stall_cycles)' in section(perf,'void tu_perf_mem_record_dram_access','void tu_perf_mem_record_reqfile_access'))
pred('reqfile-does-not-tick','tu_perf_tick' not in section(perf,'void tu_perf_mem_record_reqfile_access','/* ================================================================\n * Power Counter API'))
pred('pipeline-bubble-does-not-tick','tu_perf_tick' not in section(perf,'void tu_perf_compute_record_pipeline_bubble','/* ================================================================\n * Memory Counter API'))
pred('wall-clock-derived','c->wall_clock_ns = (uint64_t)((double)c->total_cycles / c->clock_freq_mhz * 1000.0)' in perf)
pred('dataflow-binary-only','if (dataflow_mode == 0) c->compute.df_ws_cycles' in perf and 'else                     c->compute.df_os_cycles' in perf)
pred('diff-omits-dataflow','diff.compute.df_ws_cycles' not in perf and 'diff.compute.df_os_cycles' not in perf)
pred('diff-omits-row-state','diff.memory.mem_dram_row_hits' not in perf and 'diff.memory.mem_dram_row_misses' not in perf)
pred('diff-omits-gbuf-conflicts','diff.memory.mem_gbuf_bank_conflicts' not in perf)
pred('diff-omits-bandwidth-utilization',all('diff.memory.'+x not in perf for x in ['spad_bw_utilization','gbuf_bw_utilization','dram_bw_utilization']))
pred('diff-omits-wall-clock','diff.wall_clock_ns' not in perf)
pred('diff-omits-energy-params',all('diff.power.'+x not in perf for x in ['pj_per_mac','pj_per_sram_read','pj_per_sram_write','pj_per_dram_access','pj_per_dma_byte','pj_leakage_per_cycle','power_modeling_enabled']))
pred('merge-omits-dataflow','dst->compute.df_ws_cycles' not in perf and 'dst->compute.df_os_cycles' not in perf)
pred('merge-omits-row-state','dst->memory.mem_dram_row_hits' not in perf and 'dst->memory.mem_dram_row_misses' not in perf)
pred('merge-omits-gbuf-conflicts','dst->memory.mem_gbuf_bank_conflicts' not in perf)
pred('merge-omits-bandwidth-utilization',all('dst->memory.'+x not in perf for x in ['spad_bw_utilization','gbuf_bw_utilization','dram_bw_utilization']))
pred('merge-omits-wall-clock','dst->wall_clock_ns' not in perf)
pred('merge-omits-energy-params',all('dst->power.'+x not in perf for x in ['pj_per_mac','pj_per_sram_read','pj_per_sram_write','pj_per_dram_access','pj_per_dma_byte','pj_leakage_per_cycle','power_modeling_enabled']))
pred('merge-omits-energy-total','dst->power.energy_total_pj' not in perf)
pred('reset-preserves-whole-power','tu_power_counters_t saved_power = c->power' in perf and 'c->power = saved_power' in perf)
pred('metrics-use-compiled-geometry','TU_PE_ROWS * TU_PE_COLS' in section(perf,'tu_perf_metrics_t tu_perf_compute_metrics','/* ================================================================\n * Reporting'))
pred('descriptor-header-overclaims','Called by tu_dma_execute_desc() and friends' in ph)
# Benchmark
pred('benchmark-manual-dma','tu_perf_dma_record_read(&ctx->counters' in bench and 'tu_core_dma_load_w' in bench)
pred('benchmark-double-tick',bench.index('tu_perf_compute_record_mma') < bench.index('tu_perf_tick(&ctx->counters, cycles)'))
pred('benchmark-no-fail-closed-summary','=== Results:' not in bench and 'return failures' not in bench and 'g_result_count++' in bench)
# Event trace
pred('event-first-tick-drops-delta','write_vcd_header(trace);' in ev and 'return;  /* header includes #0 timestamp */' in ev)
pred('event-fixed-timescale','$timescale 1 ns $end' in ev)
pred('event-private-disabled','static bool g_trace_enabled = false' in ev and 'g_trace_enabled =' not in ev.replace('static bool g_trace_enabled = false',''))
pred('event-api-does-not-gate','tu_trace_is_enabled' not in section(ev,'tu_event_trace_t *tu_trace_create','/* ---- Global toggle'))
pred('event-close-no-eof-marker','$dumpoff' not in section(ev,'void tu_trace_close','int tu_trace_add_signal'))
# Logging trace
pred('logging-fixed-buffer','g_trace_buffer[TU_TRACE_MAX_EVENTS]' in log)
pred('logging-overflow-silent','if (g_trace_count >= TU_TRACE_MAX_EVENTS) return' in log)
pred('logging-clear-resets-cycle','g_trace_cycle = 0' in section(log,'void tu_trace_clear','uint64_t tu_trace_get_cycle'))
pred('logging-event-ungated','trace_enabled' not in section(log,'void tu_trace_event','const tu_trace_event_t *tu_trace_get_buffer'))
pred('ordinary-mma-traces','tu_trace_event(' in texts.get('tu_cmodel/tu_cmodel.c',''))
# Cycle model
pred('cycle-explicit-mode','cm->mode = mode' in cyc)
pred('cycle-estimated-equation','uint64_t total = fill + compute + drain' in cyc)
pred('cycle-write-recorded-read','tu_perf_dma_record_read(cm->perf' in section(cyc,'uint64_t tu_cycle_model_dma_transfer','uint64_t tu_cycle_model_dma_arbitrate'))
pred('cycle-attached-perf-ticks','tu_perf_compute_record_mma(cm->perf' in cyc and 'if (cm->perf) tu_perf_tick(cm->perf, cycles)' in cyc)
pred('cycle-bank-address-modulo','w_sram_addr % cm->bank_model->num_banks' in cyc)
pred('cycle-top-level-completes-in-call','tu_cycle_pipeline_complete(cm->pipeline, cm->current_cycle)' in cyc)
conv=section(cfg,'tu_runtime_config_t tu_config_to_runtime','return rt;') if 'tu_runtime_config_t tu_config_to_runtime' in cfg else ''
parse=section(cfg,'int tu_config_load_string','int tu_config_load(')
pred('runtime-converter-drops-cycle-model','cycle_model' not in conv)
pred('shipped-power-blocks-decorative','"power"' in cfg_json and 'power:' in cfg_yaml and 'tu_json_get(tu, "power")' not in parse)
pred('trace-format-decorative','"format"' in cfg_json and 'format:' in cfg_yaml and 'parse_opt_string(trc, "format"' not in parse)
pred('trace-max-events-default-only','cfg->trace_max_events    = 65536' in cfg and 'trace_max_events' not in parse and 'trace_max_events' not in conv and all('trace_max_events' not in p.read_text(errors='replace') for p in (root/'tu_cmodel').rglob('*.c') if p.name!='config.c'))
pred('detailed-stalls-retained-no-consumer','parse_opt_bool(cnt, "detailed_stalls", &cfg->detailed_stalls)' in parse and 'rt.detailed_stalls  = cfg->detailed_stalls' in conv and all('detailed_stalls' not in p.read_text(errors='replace') for p in (root/'tu_cmodel').rglob('*.c') if p.name!='config.c'))
# Power
pred('power-table-hardcoded','static const tu_tech_node_energy_t tech_node_table[]' in power)
pred('power-claims-calibration','calibrated against published silicon data' in power and 'CACTI-Derived' in power)
pred('power-64b-transactions','uint64_t transactions = (bytes + 63) / 64' in power)
pred('power-area-30pct','* 1.30' in power)
pred('power-diff-unsigned-subtract','diff.total_cycles    = a->total_cycles - b->total_cycles' in power)
pred('power-config-heuristic','config->pe_rows >= 128' in power and 'config->dram_bandwidth_gbps > 500.0' in power)
pred('power-enabled-by-counters','pm->enabled = config->counters_enabled' in power)
pred('power-total-is-cached','if (total == 0.0)' in section(power,'double tu_power_get_avg_power_mw','double tu_power_get_energy_per_mac'))
pred('power-unused-table-fields',all(x not in power[power.index('/* ================================================================\n * Energy Recording'): ] for x in ['dram_idle_power_mw','pj_per_noc_hop','pj_per_pe_regfile_access','pj_leakage_per_byte_per_cycle']))
# Caller inventories
allc=list((root/'tu_cmodel').rglob('*.c'))
def callers(pattern,exclude):
 out=[]
 for p in allc:
  rel=p.relative_to(root).as_posix(); t=p.read_text(errors='replace')
  if rel!=exclude and re.search(pattern,t): out.append(rel)
 return sorted(out)
perf_call=callers(r'\btu_perf_(?:init|dma_record|compute_record|mem_record|from_dma_descriptor)\w*\s*\(','tu_cmodel/perf/performance_counters.c')
ev_call=callers(r'\btu_trace_(?:create|add_signal|signal|tick)\s*\(','tu_cmodel/perf/event_trace.c')
power_call=callers(r'\btu_power_(?:model_from_config|model_init|record_|tick)\w*\s*\(','tu_cmodel/perf/power_model.c')
cycle_call=callers(r'\btu_cycle_model_(?:create|execute_tile|dma_transfer|advance)\s*\(','tu_cmodel/perf/cycle_model.c')
pred('perf-only-cycle-nontest-caller',perf_call==['tu_cmodel/perf/cycle_model.c'])
pred('event-no-nontest-caller',ev_call==[])
pred('power-no-nontest-caller',power_call==[])
pred('cycle-no-nontest-caller',cycle_call==[])
checks=len(HASHES)+len(preds)
if errors:
 for e in errors: print('CH17_SOURCE_AUDIT ERROR',e)
 print(f'CH17_SOURCE_AUDIT FAIL pin={PIN} hashes={len(HASHES)} predicates={len(preds)} checks={checks}')
 raise SystemExit(1)
print('CH17_CALLERS perf='+(','.join(perf_call) or 'none')+' event='+(','.join(ev_call) or 'none')+' power='+(','.join(power_call) or 'none')+' cycle='+(','.join(cycle_call) or 'none'))
print(f'CH17_SOURCE_AUDIT PASS pin={PIN} hashes={len(HASHES)} predicates={len(preds)} checks={checks}')
