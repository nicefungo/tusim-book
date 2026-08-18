#include "tu_cmodel/tu_cmodel.h"
#include "tu_cmodel/infra/config.h"
#include "tu_cmodel/infra/tu_debug.h"
#include "tu_cmodel/tu_core.h"
#include "tests/test_framework.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

tu_test_stats_t g_test_stats = {0};
static int failures = 0;
#define CHECK_EQ(name, got, want) do { long long g=(long long)(got), w=(long long)(want); printf("CHECK %s got=%lld want=%lld %s\n",name,g,w,g==w?"PASS":"FAIL"); if(g!=w) failures++; } while(0)

static int strict_finite_compare(const float *a,const float *b,size_t n,float tol){
  for(size_t i=0;i<n;i++) if(!isfinite(a[i])||!isfinite(b[i])||fabsf(a[i]-b[i])>tol) return 0;
  return 1;
}

static int dump_contains(tu_core_t *core,const char *needle,long *byte_count){
  FILE *f=tmpfile(); if(!f) return 0;
  (void)tu_debug_dump_state(core,f,TU_DUMP_TEXT,TU_DUMP_COUNTERS);
  long n=ftell(f); if(byte_count) *byte_count=n;
  if(n<0 || fseek(f,0,SEEK_SET)!=0){ fclose(f); return 0; }
  char *buf=calloc((size_t)n+1,1); if(!buf){ fclose(f); return 0; }
  size_t got=fread(buf,1,(size_t)n,f); int found=(got==(size_t)n && strstr(buf,needle)!=NULL);
  free(buf); fclose(f); return found;
}

static int load_case(const char *dataflow,tu_config_t *cfg,tu_runtime_config_t *rt,char active[32]){
  char json[192],err[128]={0};
  snprintf(json,sizeof(json),"{\"tu\":{\"compute\":{\"pe_array\":{\"rows\":8,\"cols\":4,\"dataflow\":\"%s\"}}}}",dataflow);
  int rc=tu_config_load_string(json,cfg,err,sizeof(err));
  *rt=tu_config_to_runtime(cfg); tu_init_with_config(rt);
  snprintf(active,32,"%s",tu_get_dataflow_name()); return rc;
}

int main(void){
  float expected[1]={1.0f}, actual_nan[1]={NAN};
  test_stats_init();
  int shared=compare_tensors("nan discriminator",expected,actual_nan,1,0.0f);
  int strict=strict_finite_compare(expected,actual_nan,1,0.0f);
  printf("ORACLE_NAN shared_accept=%d strict_accept=%d shared_pass=%d shared_fail=%d\n",shared,strict,g_test_stats.tests_pass,g_test_stats.tests_fail);
  CHECK_EQ("shared_nan_accept",shared,1); CHECK_EQ("strict_nan_reject",strict,0);

  tu_config_t cfg_ws,cfg_os; tu_runtime_config_t rt_ws,rt_os; char active_ws[32],active_os[32],direct_os[32];
  int ws_rc=load_case("weight_stationary",&cfg_ws,&rt_ws,active_ws);
  int os_rc=load_case("output_stationary",&cfg_os,&rt_os,active_os);
  CHECK_EQ("config_ws_parse",ws_rc,0); CHECK_EQ("config_os_parse",os_rc,0);
  CHECK_EQ("config_parsed_ws",cfg_ws.dataflow_mode,TU_DATAFLOW_MODE_WS); CHECK_EQ("config_parsed_os",cfg_os.dataflow_mode,TU_DATAFLOW_MODE_OS);
  CHECK_EQ("config_rt_rows",rt_os.pe_rows,8); CHECK_EQ("config_rt_cols",rt_os.pe_cols,4);
  CHECK_EQ("config_ws_input_active_ws",strcmp(active_ws,"weight_stationary"),0); CHECK_EQ("config_os_input_active_ws",strcmp(active_os,"weight_stationary"),0);
  CHECK_EQ("direct_set_os",tu_set_dataflow(TU_DATAFLOW_MODE_OS),0); snprintf(direct_os,sizeof(direct_os),"%s",tu_get_dataflow_name());
  CHECK_EQ("direct_os_active",strcmp(direct_os,"output_stationary"),0);
  printf("CONFIG_AB ws_parse=%d os_parse=%d ws_df=%d os_df=%d rt_rows=%u rt_cols=%u ws_active=%s os_active=%s direct_os=%s\n",ws_rc,os_rc,cfg_ws.dataflow_mode,cfg_os.dataflow_mode,rt_os.pe_rows,rt_os.pe_cols,active_ws,active_os,direct_os);

  tu_core_t *core=tu_core_create(&rt_os); CHECK_EQ("core_create",core!=NULL,1); if(!core) return 1;
  long created_bytes=0,reinit_bytes=0; int created_8x4=dump_contains(core,"PE array: 8×4",&created_bytes);
  tu_core_init(core); int reinitialized_16x16=dump_contains(core,"PE array: 16×16",&reinit_bytes);
  printf("CORE_REINIT_GEOMETRY created_8x4=%d reinitialized_16x16=%d created_bytes=%ld reinitialized_bytes=%ld\n",created_8x4,reinitialized_16x16,created_bytes,reinit_bytes);
  CHECK_EQ("core_created_8x4",created_8x4,1); CHECK_EQ("core_reinitialized_16x16",reinitialized_16x16,1);

  FILE *f=tmpfile(); CHECK_EQ("dump_tmpfile",f!=NULL,1); if(!f){ tu_core_destroy(core); return 1; }
  size_t reported=tu_debug_dump_state(core,f,TU_DUMP_TEXT,TU_DUMP_COUNTERS); long actual_bytes=ftell(f);
  printf("DUMP_SIZE fixture=post_reinit_16x16 reported=%zu actual=%ld\n",reported,actual_bytes); CHECK_EQ("dump_reported_zero",reported,0); CHECK_EQ("dump_actual_338",actual_bytes,338); fclose(f);

  uint32_t csum=tu_debug_checksum_sram(core); tu_replay_trace_t tr={0};
  CHECK_EQ("replay_start",tu_debug_record_start(&tr,1),0);
  CHECK_EQ("replay_record",tu_debug_record_instr(&tr,7,0xFE,0,3,4,5,0x11223344,csum,csum),0); tu_debug_record_stop(&tr);
  FILE *rf=tmpfile(); CHECK_EQ("replay_tmpfile",rf!=NULL,1); if(!rf){ tu_debug_record_destroy(&tr); tu_core_destroy(core); return 1; }
  int mm0=tu_debug_replay_execute(core,&tr,rf); long replay_bytes=ftell(rf); fclose(rf);
  tr.entries[0].checksum_delta=1; rf=tmpfile(); CHECK_EQ("replay_mut_tmpfile",rf!=NULL,1); if(!rf){ tu_debug_record_destroy(&tr); tu_core_destroy(core); return 1; }
  int mm1=tu_debug_replay_execute(core,&tr,rf); fclose(rf);
  printf("REPLAY_NOOP arbitrary_opcode=0xFE mismatches_equal=%d mismatches_mutated=%d output_bytes=%ld\n",mm0,mm1,replay_bytes);
  CHECK_EQ("replay_noop_accept",mm0,0); CHECK_EQ("replay_mutation_detect",mm1,1); tu_debug_record_destroy(&tr);

  int wrapped=tu_debug_assert_bounds(UINT32_MAX-3u,8u,16u,"wrap");
  int ordinary=tu_debug_assert_bounds(15u,2u,16u,"ordinary");
  printf("BOUNDS_WRAP wrapped_accept=%d ordinary_accept=%d\n",wrapped,ordinary);
  CHECK_EQ("bounds_wrap_unsafe_green",wrapped,1); CHECK_EQ("bounds_ordinary_reject",ordinary,0);
  int oversized=tu_debug_assert_tile_dims(32,32,8,8,"oversized"); int zero=tu_debug_assert_tile_dims(0,1,8,8,"zero");
  printf("TILE_PE_IGNORED oversized_accept=%d zero_reject=%d\n",oversized,!zero);
  CHECK_EQ("tile_oversized_accept",oversized,1); CHECK_EQ("tile_zero_reject",zero,0);
  tu_core_destroy(core);
  printf("CH20_PROBE SUMMARY failures=%d\n",failures); return failures?1:0;
}
