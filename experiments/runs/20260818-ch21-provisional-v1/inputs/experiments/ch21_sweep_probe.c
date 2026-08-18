/* Chapter 21 focused executable discriminators; build only in exact-pin archive. */
#include "tu_cmodel/tu_cmodel.h"
#include "tu_cmodel/tu_core.h"
#include "tu_cmodel/tu_precision.h"
#include "tu_cmodel/rounding.h"
#include "tu_cmodel/compute/dataflow/dataflow_registry.h"
#include "tu_cmodel/infra/tu_context.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int failures=0;
static void need(int ok,const char *what){if(!ok){fprintf(stderr,"FAIL %s\n",what);failures++;}}
static uint64_t fnv16(const uint16_t *v,size_t n){uint64_t h=1469598103934665603ULL;for(size_t i=0;i<n;i++){h^=v[i]&255;h*=1099511628211ULL;h^=v[i]>>8;h*=1099511628211ULL;}return h;}
static void run_route(tu_core_t *c,const char *tag,uint64_t want){
 float wf[6]={1,2,3,4,5,6},af[6]={7,8,9,10,11,12},o[4]={0};fp16_t w[6],a[6];
 for(int i=0;i<6;i++){w[i]=tu_fp32_to_fp16(wf[i]);a[i]=tu_fp32_to_fp16(af[i]);}tu_sram_write_bulk(&c->state.sram_o,0,o,sizeof(o));
 tu_core_dma_load_w(c,w,0,sizeof(w));tu_core_dma_load_a(c,a,0,sizeof(a));
 uint64_t before=c->state.estimated_cycles;tu_core_mma(c,2,2,3,0,0,0,false);uint64_t delta=c->state.estimated_cycles-before;
 tu_core_dma_store_o(c,o,0,sizeof(o));need(delta==want,"route-cycles");need(o[0]==58&&o[1]==64&&o[2]==139&&o[3]==154,"route-output");
 printf("DATAFLOW_EXEC tag=%s active=%s delta=%llu output=58,64,139,154\n",tag,c->state.dataflow->name,(unsigned long long)delta);
}
static uint64_t context_case(tu_core_t *core,tu_ctx_save_scope_t scope,uint32_t bw,uint64_t *saved){
 tu_runtime_config_t rt=core->state.rt_cfg;tu_ctx_manager_config_t cfg={.max_contexts=2,.sched_policy=TU_CTX_SCHED_ROUND_ROBIN,.switch_overhead=100,.save_scope=scope,.live_w_bytes=rt.sram_w_size/4,.live_a_bytes=rt.sram_a_size/4,.live_o_bytes=rt.sram_o_size/4,.state_bytes_per_cycle=bw};
 tu_ctx_manager_t *m=tu_ctx_manager_create(core,&cfg);need(m!=NULL,"ctx-create");need(tu_ctx_alloc(m)>=0&&tu_ctx_alloc(m)>=0,"ctx-alloc");need(tu_ctx_switch(m,1)==0,"ctx-switch");*saved=tu_ctx_get(m,1)->saved_sram_bytes;uint64_t cy=tu_ctx_get_switch_overhead(m);tu_ctx_manager_destroy(m);return cy;
}
int main(void){
 tu_runtime_config_t cfg=tu_runtime_config_default();tu_core_t *core=tu_core_create(&cfg);need(core!=NULL,"core-create");
 int snap0=core->state.dataflow->id;need(tu_set_dataflow(TU_DATAFLOW_OUTPUT_STATIONARY)==0,"set-os");int global=g_tu.dataflow->id;tu_core_sync(core);int snap1=core->state.dataflow->id;
 printf("DATAFLOW_ROUTE requested_label=output_stationary process_global_before=%d core_snapshot_before=%d core_snapshot_after=%d effective_core=%s\n",global,snap0,snap1,core->state.dataflow->name);need(global==1&&snap0==0&&snap1==0,"core-route-override");
 run_route(core,"labeled_os",67);core->state.dataflow=tu_dataflow_lookup(TU_DATAFLOW_OUTPUT_STATIONARY);run_route(core,"active_os",4);core->state.dataflow=tu_dataflow_lookup(TU_DATAFLOW_ROW_STATIONARY);run_route(core,"active_rs",36);
 float x=1.0007f;uint16_t a[64],b[64],c[64];tu_set_rounding_mode(TU_ROUND_RNE);uint16_t rne=tu_fp32_to_fp16(x);tu_set_rounding_mode(TU_ROUND_RTZ);uint16_t rtz=tu_fp32_to_fp16(x);tu_set_rounding_mode(TU_ROUND_STOCHASTIC);tu_stochastic_set_seed(12345);for(int i=0;i<64;i++)a[i]=tu_fp32_to_fp16(x);tu_stochastic_set_seed(12345);for(int i=0;i<64;i++)b[i]=tu_fp32_to_fp16(x);tu_stochastic_set_seed(54321);for(int i=0;i<64;i++)c[i]=tu_fp32_to_fp16(x);
 int same=!memcmp(a,b,sizeof(a)),changed=memcmp(a,c,sizeof(a))!=0;printf("ROUNDING_AXIS value=1.0007 rne=0x%04x rtz=0x%04x same_seed_equal=%d changed_seed_diff=%d seed12345_fnv=%016llx seed54321_fnv=%016llx\n",rne,rtz,same,changed,(unsigned long long)fnv16(a,64),(unsigned long long)fnv16(c,64));need(rne==0x3c01&&rtz==0x3c00&&same&&changed,"round-axis");need(fnv16(a,64)==0x99a9ff040fc80ca3ULL&&fnv16(c,64)==0x283bd184c961bcc2ULL,"round-vector");
 printf("RANDOMNESS_SCOPE fixed_seed_replay=1 changed_seed_vector=1 independent_application_samples=0 application_accuracy=0\n");
 tu_core_destroy(core);core=tu_core_create(&cfg);uint64_t saved=0;uint64_t full=context_case(core,TU_CTX_SAVE_FULL_SRAM,32,&saved);need(saved==262144&&full==16484,"ctx-full");uint64_t live=context_case(core,TU_CTX_SAVE_LIVE_SRAM,32,&saved);need(saved==65536&&live==4196,"ctx-live");uint64_t control=context_case(core,TU_CTX_SAVE_CONTROL_ONLY,32,&saved);need(saved==0&&control==100,"ctx-control");uint64_t bw16=context_case(core,TU_CTX_SAVE_FULL_SRAM,16,&saved);uint64_t bw64=context_case(core,TU_CTX_SAVE_FULL_SRAM,64,&saved);need(bw16==32868&&bw64==8292,"ctx-bandwidth");printf("CONTEXT_EXEC full256=16484 live25_256=4196 control256=100 full256_bw16=32868 full256_bw64=8292 producer=linked_estimator\n");
 tu_core_destroy(core);printf("CH21_SWEEP_PROBE SUMMARY failures=%d\n",failures);return failures?1:0;
}
