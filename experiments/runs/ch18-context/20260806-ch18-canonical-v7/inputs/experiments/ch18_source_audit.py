#!/usr/bin/env python3
import hashlib,re,sys
from pathlib import Path
PIN="e918c80b6fce833cd1fcae97730fa841c2176f25"
HASHES={
"Makefile":"5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
"tu_cmodel/infra/tu_context.c":"ecd0f8258183a9dca0649ca8ed446bee23978571a201fa3464317f31a46762b0",
"tu_cmodel/infra/tu_context.h":"9479cf3a9883ff4b0dbe0e7c7482a9bdad99f2558bd840838e94519e7fa1af28",
"tu_cmodel/tu_core.c":"0e4b3c6e206465748ae2d3d2e9871f3a6542a61cd1ddcddfff6886b9ed1f0eeb",
"tu_cmodel/tu_core.h":"dc5c22065fb65be4353585ccbfd3bec6c9b9d70e976a51e87169bac79dd164e9",
"tu_cmodel/tu_cmodel.c":"542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
"tu_cmodel/tu_cmodel.h":"416a0d20776825498217ff5d4382f07ccb2ac9689bbe6c70cacd1bf13e7725af",
"tu_cmodel/tu_sram.c":"5a6ffcdd3f63c9c015bd628b5c44ded951785a128685b413b6db680f5d1753c0",
"tu_cmodel/tu_sram.h":"aa62a942c83bfded4644c26eabf37acb815b7ac2883b53f6b3b8a585df4123d5",
"tu_cmodel/memory/double_buffer.c":"94d5ac4d1974ec577cb51af7d132c6bf2e7cf405d0eb5626159430555fcdb07a",
"tu_cmodel/memory/double_buffer.h":"c72ae87cc19da132c6ee74ea239099d6056a64ecd266ee944697bf938d141d62",
"tu_cmodel/memory/dram_model.c":"c5ce405dbf30d96ffb166895c1df6a871c9aa3198dda15dc903ad6d346de5ed3",
"tu_cmodel/memory/dram_model.h":"4acdec93bc83a0f8d7cf267a55ea5c29e863f20b9024e83a709ba28acbb17602",
"tu_cmodel/dma_descriptor.c":"2434c254eef9615b864106de0c453328e64aa6ec49f1e1aff2da5d7e49c8404e",
"tu_cmodel/dma_descriptor.h":"84d6808d7bdbeba9f638d4cd5eb05b15315f2c09225597bec7e996110f144bbb",
"tu_cmodel/command_queue.c":"e8e24987b1cadb61d23bee76085ca7f11b37b7d387eb075033a1651f8a72a389",
"tu_cmodel/command_queue.h":"cf1f06164d7b3353158c3b70c0667d29b6e94a2ca90a08620232546023363135",
"tu_cmodel/rounding.c":"585fa23d2e7ec80499f2607fc4c389001e5dc1d84c818b651c74b1ed65388128",
"tu_cmodel/rounding.h":"2b23801dd064620401a3a3fbc7cf702adb45374c225cdcca1a845cfde546a849",
"tu_cmodel/compute/dataflow/dataflow_interface.h":"141bdd26c5e436d38095296e824a93761ac4b74edaed9b7482ef7c8eca5ebf77",
"tu_cmodel/compute/dataflow/dataflow_registry.c":"56b4fcab5e736eb1fd55a02cdeaefd20504a708a7cea6012c8c819e25bc24d27",
"tu_cmodel/compute/dataflow/dataflow_registry.h":"a0a8f186fe53d78275b7ed45418a7e9254fbe08b436c51dbd0ae3a3d3a4c06f7",
"tu_cmodel/compute/dataflow/weight_stationary.c":"c421bd0845da1847b4e48a97c55f45dbbb058dc3a5af0e448d5fab422bd5b7e8",
"tu_cmodel/compute/dataflow/output_stationary.c":"fa3a00c9b649b69dc8e92d562f044c49b129096c753ba169a855ba2e075dfaa0",
"tu_cmodel/compute/dataflow/row_stationary.c":"ea86233c36fa1f076e0852204880f8d903bf546728478816df66b091e56feeaf",
"tu_cmodel/compute/dataflow/dataflow_dispatcher.c":"f09af46670bc8a3bee49be6c639bc27a432a085109684e0f4f73b4f471b9a6f4",
"tu_cmodel/tu_status.c":"f26666b88b32484faf7e8473b1a8a2ddc09da08b472d90a2d200cb582fd11cfb",
"tu_cmodel/tu_status.h":"fe1ec4fadc2044b00e79afc4afbeb5ca90fc75ad97d371a2eff3cca6605392a0",
"tu_cmodel/infra/config.c":"17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
"tu_cmodel/infra/config.h":"723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
"tu_cmodel/tu_config.h":"129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
"tu_cmodel/tu_precision.c":"d3180406590791d775911ea16960d54974b43abfee1f3b63a6c12a00066d50c7",
"tu_cmodel/tu_precision.h":"937a20c3ac818ed81a72a60c53d34f524ac8aceccf8b7a2f6a51b9f634e8c60f",
"tests/test_context.c":"e364e9187b1795174de10992ac60aff2f5c852aeebcc1cd9a95605e1e07bf1a3",
"tests/test_context_switch_sweep.c":"a6c50ea702490df03dcbe653b3f82601fc05807cbee8b5d068fb03c0dccae76a",
"docs/multi-context-execution.md":"778138aededdc4704701156ecf785c24ac6dd0c8ebbb1a4aef1e6a92ad1827e8",
"docs/exploration/context-switch-state-scope.md":"ae8b49e3b31e0172f69869d406c70996609f295f584357107847186259c80230",
"config/tu_config.json":"6f9d292696b1ca5fa38ad3298e7f3a04c43095c0950f71dbe0c3c68b1f15f4db",
"config/tu_config.yaml":"9fb4d87753139a5857107a6fdf56006fcb5adbe95ad30e9f8430c2e5c145910e",
}
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()
pin=sys.argv[2] if len(sys.argv)>2 else PIN
if pin!=PIN: print(f"CH18_SOURCE_AUDIT FAIL pin expected={PIN} got={pin}"); raise SystemExit(1)
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
 try: a=t.index(start); b=t.index(end,a+len(start)); return t[a:b]
 except ValueError: return ''
ctx=texts.get('tu_cmodel/infra/tu_context.c',''); h=texts.get('tu_cmodel/infra/tu_context.h','')
core=texts.get('tu_cmodel/tu_core.c',''); model=texts.get('tu_cmodel/tu_cmodel.c',''); modelh=texts.get('tu_cmodel/tu_cmodel.h','')
mk=texts.get('Makefile',''); dma=texts.get('tu_cmodel/dma_descriptor.c',''); dmah=texts.get('tu_cmodel/dma_descriptor.h',''); cmd=texts.get('tu_cmodel/command_queue.c','')
cmdh=texts.get('tu_cmodel/command_queue.h',''); rnd=texts.get('tu_cmodel/rounding.c',''); df=texts.get('tu_cmodel/compute/dataflow/dataflow_registry.c','')
prec=texts.get('tu_cmodel/tu_precision.c',''); status=texts.get('tu_cmodel/tu_status.c',''); sramh=texts.get('tu_cmodel/tu_sram.h','')
doc=texts.get('docs/multi-context-execution.md',''); sweepdoc=texts.get('docs/exploration/context-switch-state-scope.md','')
# Exact API and field census.
expected_api={'tu_ctx_alloc','tu_ctx_block_current','tu_ctx_free','tu_ctx_get','tu_ctx_get_switch_count','tu_ctx_get_switch_overhead','tu_ctx_manager_config_validate','tu_ctx_manager_create','tu_ctx_manager_destroy','tu_ctx_notify_command','tu_ctx_notify_cycles','tu_ctx_print_status','tu_ctx_request_switch','tu_ctx_restore','tu_ctx_save','tu_ctx_schedule_next','tu_ctx_slice_expired','tu_ctx_switch','tu_ctx_unblock'}
api=set(re.findall(r'\b(tu_ctx_[A-Za-z0-9_]+)\s*\(',h))
pred('public-api-exact-19',api==expected_api)
for name in sorted(expected_api): pred('api-defined-'+name,re.search(rf'\b{re.escape(name)}\s*\(',ctx) is not None)
desc_fields={'ctx_id','state','priority','hw_state','total_cycles','total_commands','switch_count','last_switch_cycle','saved_sram_bytes','saved_w_bytes','saved_a_bytes','saved_o_bytes','has_config_override','config_override','user_data'}
mgr_fields={'core','max_contexts','contexts','active_count','active_ctx_id','sched_policy','time_slice_cycles','time_slice_cmds','slice_cycles_used','slice_cmds_used','total_switches','total_cycles_stolen','switch_fixed_cycles','state_bytes_per_cycle','save_scope','live_w_bytes','live_a_bytes','live_o_bytes','pending_save_bytes'}
for f in sorted(desc_fields|mgr_fields): pred('header-field-'+f,re.search(rf'\b{re.escape(f)}\s*(?:;|\[)',h) is not None)
# Build/test provenance.
pred('context-archive-member','$(TU_DIR)/infra/tu_context.o' in section(mk,'TU_OBJS =','libtucmodel.a:'))
pred('context-test-rule',re.search(r'(?m)^test-context:',mk) is not None)
pred('context-sweep-rule',re.search(r'(?m)^test-context-switch-sweep:',mk) is not None)
flat=mk.replace('\\\n',' '); mt=re.search(r'(?m)^test:\s*(.*?)(?:\n\t|\n[^ \t])',flat,re.S); agg=mt.group(1) if mt else ''
pred('context-not-aggregate','test-context' not in agg)
pred('context-sweep-not-aggregate','test-context-switch-sweep' not in agg)
# Configuration and reachability.
json=texts.get('config/tu_config.json',''); yaml=texts.get('config/tu_config.yaml',''); cfg=texts.get('tu_cmodel/infra/config.c','')
pred('context-c-api-only','context' not in json.lower() and 'context' not in yaml.lower())
pred('global-config-no-context',all(x not in cfg for x in ['max_contexts','save_scope','state_bytes_per_cycle','time_slice_cycles']))
create=section(ctx,'tu_ctx_manager_t *tu_ctx_manager_create','int tu_ctx_manager_config_validate')
pred('save-dram-dead','save_dram_state' not in ctx)
pred('dram-not-tu-state-owned','tu_dram' not in modelh and 'dram_model' not in modelh)
pred('dram-separately-constructed','tu_dram_create' in texts.get('tu_cmodel/memory/dram_model.c','') and 'calloc' in texts.get('tu_cmodel/memory/dram_model.c',''))
pred('override-dead','has_config_override' not in ctx and 'config_override' not in ctx)
pred('user-data-dead','user_data' not in ctx)
# Retention scopes and byte accounting.
pred('full-uses-capacity','if (scope == TU_CTX_SAVE_FULL_SRAM) return capacity' in ctx)
pred('live-uses-prefix','if (scope == TU_CTX_SAVE_LIVE_SRAM) return live' in ctx)
pred('control-zero','return 0;' in section(ctx,'static uint32_t ctx_scope_bytes','static int ctx_save_full_state'))
pred('live-bounds-validated',all(x in ctx for x in ['cfg->live_w_bytes > core->state.sram_w.banks.size','cfg->live_a_bytes > core->state.sram_a.banks.size','cfg->live_o_bytes > core->state.sram_o.banks.size']))
pred('cost-save-plus-restore','mgr->pending_save_bytes + ctx->saved_sram_bytes' in ctx)
pred('cost-ceil-divide','transfer_bytes + mgr->state_bytes_per_cycle - 1' in ctx)
pred('cost-manager-only','total_cycles_stolen' in ctx and 'estimated_cycles +=' not in section(ctx,'int tu_ctx_restore','int tu_ctx_switch'))
# Saved state field census.
for f in ['total_dma_bytes','total_mma_calls','total_mma_tiles','total_mma_flops','estimated_cycles','rt_cfg','initialized']:
 pred('save-restore-'+f,ctx.count('hw_state.'+f)>=2)
pred('runtime-config-field-census',all(x in texts.get('tu_cmodel/tu_config.h','') for x in ['pe_rows;','pe_cols;','sram_w_size;','sram_a_size;','sram_o_size;','counters_enabled;','detailed_stalls;','trace_enabled;','trace_file[256];','verify_enabled;','verify_tolerance;','icc_switching_mode;','icc_contention_mode;','icc_mesh_routing_mode;','icc_link_bytes_per_cycle;','icc_router_latency_cycles;']))
pred('sram-prefix-deep-copy','malloc(copy_bytes)' in ctx and 'memcpy(dst->banks.data, src->banks.data, copy_bytes)' in ctx)
for f in ['size','bank_count','bank_width','reads','writes','conflicts','stall_cycles','bw_modeling','words_per_cycle','arb_mode','stall_penalty','bw_refill_window','current_cycle']:
 pred('bank-metadata-'+f,ctx.count('banks.'+f)>=2)
pred('per-bank-state-dropped','dst->banks.bw_banks = NULL' in ctx and 'rw->banks.bw_banks' not in ctx and 'ra->banks.bw_banks' not in ctx and 'ro->banks.bw_banks' not in ctx)
pred('double-buffer-dropped',ctx.count('->db = NULL')>=6)
pred('embedded-dma-memcpy',ctx.count('hw_state.dma')>=2 and 'sizeof(tu_dma_engine_t)' in ctx)
pred('cmdq-pointer-saved','ctx->hw_state.cmdq = state->cmdq' in ctx)
pred('cmdq-not-restored','state->cmdq stays as-is' in ctx and 'ctx->hw_state.cmdq' not in section(ctx,'static int ctx_restore_full_state','/* ================================================================\n * Public API'))
pred('dataflow-pointer-only','state->dataflow = ctx->hw_state.dataflow' in ctx)
pred('sram-bank-field-census',all(x in sramh for x in ['*data','size;','bank_count;','bank_width;','reads;','writes;','conflicts;','stall_cycles;','*bw_banks','bw_refill_window;','current_cycle;','words_per_cycle;','arb_mode;','stall_penalty;','bw_modeling;']))
pred('sram-per-bank-field-census',all(x in sramh for x in ['words_available;','last_refill_cycle;','reads_served;','writes_served;','read_stalls;','write_stalls;','total_cycles_used;']))
pred('sram-region-field-census',all(x in sramh for x in ['banks;','total_size;','*name;','*db;']))
restore_surface=section(ctx,'static int ctx_restore_full_state','/* ================================================================\n * Public API')
copy_surface=section(ctx,'static int ctx_copy_sram_data','static void ctx_free_sram_data')
pred('sram-explicit-save-restore-matrix',all(copy_surface.count('dst->banks.'+x)>=1 and copy_surface.count('src->banks.'+x)>=1 and restore_surface.count('->banks.'+x)>=6 for x in ['size','bank_count','bank_width','reads','writes','conflicts','stall_cycles','bw_modeling','words_per_cycle','arb_mode','stall_penalty','bw_refill_window','current_cycle']))
pred('sram-total-size-save-restore',all(x in ctx for x in ['dw->total_size = sw->total_size','da->total_size = sa->total_size','d_o->total_size = so->total_size']) and all(x in restore_surface for x in ['rw->total_size = sw->total_size','ra->total_size = sa->total_size','ro->total_size = so->total_size']))
pred('stale-top-drain-comment','flush DMA, sync command queue' in ctx)
pred('stale-per-bank-recreate-comment','per-bank bw_banks (recreated on restore)' in ctx)
pred('stale-cmdq-recreate-comment','will be recreated on restore via tu_cmdq_create' in ctx)
pred('stale-plugin-reselect-comment','restore will re-select by name' in ctx)
# Operative global DMA and sync boundary.
pred('dma-process-global','tu_dma_engine_t g_tu_dma = {0}' in dma)
pred('dma-struct-has-pointers',all(x in dmah for x in ['*head','*tail','*active']))
pred('init-dma-global','tu_dma_init(' in section(model,'void tu_init_with_config','void tu_print_stats'))
pred('init-does-not-fill-embedded-dma','g_tu.dma' not in section(model,'void tu_init_with_config','void tu_print_stats'))
sync=section(core,'void tu_core_sync','/* ---- Subsystem Access')
pred('core-sync-only-cmdq','tu_cmdq_sync_all()' in sync and 'tu_dma_' not in sync)
cmdsync=section(cmd,'void tu_cmdq_sync','int tu_cmdq_tick')
pred('cmdq-sync-mode-and-no-timeout','if (cq->synchronous) return' in cmdsync and 'while (cq->count > 0)' in cmdsync and 'timeout' not in cmdsync)
pred('global-dma-not-context-owned','g_tu_dma' not in ctx)
# Global rounding and plugin mutable state.
pred('rounding-global-mode','static tu_rounding_mode_t g_rounding_mode' in rnd)
pred('rounding-global-prng','static uint64_t g_prng_state[2]' in rnd)
pred('rounding-not-context-owned','tu_get_rounding_mode' not in ctx and 'tu_set_rounding_mode' not in ctx and 'stochastic' not in ctx)
pred('subnormal-global-mode','static tu_subnormal_mode_t g_subnormal_mode' in prec)
pred('subnormal-not-context-owned','tu_get_subnormal_mode' not in ctx and 'tu_set_subnormal_mode' not in ctx)
pred('error-mode-global','static tu_error_mode_t g_error_mode' in status)
pred('error-mode-not-context-owned','tu_set_error_mode' not in ctx and 'tu_get_error_mode' not in ctx)
pred('plugin-registry-global','static tu_dataflow_plugin_t *g_registry' in df)
pred('plugin-has-mutable-counters',all(x in texts.get('tu_cmodel/compute/dataflow/dataflow_interface.h','') for x in ['total_flops','total_tiles','total_cycles','impl_data']))
pred('all-plugin-impl-data',all('impl_data' in texts.get(x,'') for x in ['tu_cmodel/compute/dataflow/weight_stationary.c','tu_cmodel/compute/dataflow/output_stationary.c','tu_cmodel/compute/dataflow/row_stationary.c']))
descblock=section(h,'typedef struct tu_context_desc_t','} tu_context_desc_t;')
pred('outer-core-not-context-owned',all(x not in descblock for x in ['core_id','icc_buffer','icc_buffer_size']) and re.search(r'tu_core_t\s+\*core;',h) is not None)
# Lifecycle, ownership, scheduling, and failure atomicity.
free=section(ctx,'void tu_ctx_free','tu_context_desc_t *tu_ctx_get')
pred('free-active-saves','ctx->state == TU_CTX_ACTIVE' in free and 'tu_ctx_save(mgr)' in free)
pred('free-any-nonactive','if (ctx->state == TU_CTX_ACTIVE) return' in free and 'active_count--' in free)
pred('free-idle-decrements','ctx->state == TU_CTX_IDLE' not in free and 'active_count--' in free)
save=section(ctx,'int tu_ctx_save','int tu_ctx_restore')
restore=section(ctx,'int tu_ctx_restore','int tu_ctx_switch')
switch=section(ctx,'int tu_ctx_switch','int tu_ctx_request_switch')
pred('save-demotes-active','ctx->state = TU_CTX_READY' in save)
pred('save-no-owner-clear',re.search(r'active_ctx_id\s*=',save) is None)
pred('restore-requires-ready','ctx->state != TU_CTX_READY' in restore)
pred('restore-does-not-demote-old','ctx->state = TU_CTX_ACTIVE' in restore and 'state = TU_CTX_READY' not in restore)
pred('switch-validates-after-save',switch.index('tu_ctx_save') < switch.index('tu_ctx_restore'))
pred('self-switch-not-rejected','ctx_id == active_id' not in switch)
pred('request-switch-immediate','return tu_ctx_switch' in section(ctx,'int tu_ctx_request_switch','/* ================================================================\n * Scheduling'))
pred('completion-unproduced','state = TU_CTX_COMPLETED' not in ctx)
prio=section(ctx,'case TU_CTX_SCHED_PRIORITY','default:')
pred('priority-zero-starves','uint8_t best_prio = 0' in prio and 'priority > best_prio' in prio)
pred('priority-tie-first','priority > best_prio' in prio and 'priority >= best_prio' not in prio)
pred('round-robin-ready-only','contexts[id].state == TU_CTX_READY' in ctx)
pred('slice-inclusive-threshold',ctx.count('slice_cycles_used >= mgr->time_slice_cycles')==1 and ctx.count('slice_cmds_used >= mgr->time_slice_cmds')==1)
pred('notify-manager-only','mgr->slice_cmds_used++' in ctx and 'total_commands++' not in ctx and 'mgr->slice_cycles_used += cycles' in ctx)
pred('notify-overflow-unchecked','UINT64_MAX' not in ctx and 'slice_cmds_used++' in ctx and 'slice_cycles_used += cycles' in ctx)
pred('cycle-delta-unsigned-unclamped','ctx->total_cycles += mgr->core->state.estimated_cycles - ctx->last_switch_cycle' in ctx and 'estimated_cycles >=' not in save)
pred('unblock-nonblocked-success','if (mgr->contexts[ctx_id].state == TU_CTX_BLOCKED)' in ctx and section(ctx,'int tu_ctx_unblock','void tu_ctx_notify_command').rstrip().endswith('return 0;\n}'))
# Allocation rollback versus destructive re-save.
pred('save-frees-old-before-copy',ctx.index('ctx_free_sram_data(dw)') < ctx.index('ctx_copy_sram_data(dw,'))
pred('partial-copy-cleanup',all(x in ctx for x in ['ctx_free_sram_data(dw); return -1','ctx_free_sram_data(dw); ctx_free_sram_data(da); return -1']))
pred('alloc-failure-idle','ctx->state = TU_CTX_IDLE' in section(ctx,'int tu_ctx_alloc','void tu_ctx_free'))
pred('resave-failure-no-rollback','ctx_save_full_state(mgr, ctx' in save and 'return ret' in save and 'rollback' not in save.lower())
alloc=section(ctx,'int tu_ctx_alloc','void tu_ctx_free')
pred('allocation-clones-current-core','ctx_save_full_state(mgr, ctx' in alloc)
pred('allocation-cycle-baseline-zero','memset(ctx, 0, sizeof(tu_context_desc_t))' in alloc and 'last_switch_cycle =' not in alloc)
save_full=section(ctx,'static int ctx_save_full_state','static int ctx_restore_full_state')
pred('save-three-copy-calls',save_full.count('ctx_copy_sram_data(')==3 and all(x in save_full for x in ['ctx_copy_sram_data(dw, sw, ctx->saved_w_bytes)','ctx_copy_sram_data(da, sa, ctx->saved_a_bytes)','ctx_copy_sram_data(d_o, so, ctx->saved_o_bytes)']) and ctx.count('malloc(copy_bytes)')==1)
# Focused tests and docs limitations.
test=texts.get('tests/test_context.c','')
for needle in ['15/15','test_save_scope_and_cost','test_full_and_control_cost','test_context_config_validation']:
 pred('focused-source-'+re.sub(r'\W+','-',needle),needle in test or (needle=='15/15' and test.count('TEST("ctx_')==15))
for absent in ['priority = 0','TU_CTX_COMPLETED','has_config_override','g_tu_dma','tu_get_rounding_mode','malloc']:
 pred('focused-omits-'+re.sub(r'\W+','-',absent),absent not in test)
pred('doc-stale-count','Status:** Complete (12/12 tests passing)' in doc)
pred('doc-overclaims-full-snapshot','command queue state' in doc and 'precision/rounding modes' in doc)
pred('doc-overclaims-preemption','High-priority contexts can interrupt lower-priority ones at sync points' in doc)
pred('sweep-cost-equation','outgoing_saved_bytes + incoming_saved_bytes' in sweepdoc)
pred('sweep-qualifies-model-cycles','model cycles, not wall-clock memcpy measurements' in sweepdoc)
pred('sweep-qualifies-omissions','not DRAM contention, DMA setup, ECC, dirty-map scans, or context-store queueing' in sweepdoc)
# Exact whole-tree non-test caller inventory from the complete header-derived API set.
hits=[]
pat=re.compile(r'\b(?:'+ '|'.join(re.escape(x) for x in sorted(expected_api)) +r')\s*\(')
for p in root.rglob('*'):
 if not p.is_file() or p.suffix not in {'.c','.h','.cc','.cpp'}: continue
 rel=p.relative_to(root).as_posix()
 if rel in {'tu_cmodel/infra/tu_context.c','tu_cmodel/infra/tu_context.h'} or rel.startswith(('tests/','docs/')): continue
 if pat.search(p.read_text(errors='replace')): hits.append(rel)
pred('zero-external-nontest-callers',hits==[])
checks=len(HASHES)+len(preds)
if errors:
 for e in errors: print('CH18_SOURCE_AUDIT ERROR',e)
 print(f'CH18_SOURCE_AUDIT FAIL pin={PIN} hashes={len(HASHES)} predicates={len(preds)} checks={checks}')
 raise SystemExit(1)
print('CH18_PUBLIC_APIS count='+str(len(api))+' names='+','.join(sorted(api)))
print('CH18_CALLERS external_nontest='+(','.join(hits) or 'none'))
print(f'CH18_SOURCE_AUDIT PASS pin={PIN} hashes={len(HASHES)} predicates={len(preds)} checks={checks}')
