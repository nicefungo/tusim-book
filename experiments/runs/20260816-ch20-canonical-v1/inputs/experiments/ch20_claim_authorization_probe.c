#include "tu_cmodel/tu_cmodel.h"
#include "tu_cmodel/infra/config.h"
#include "tu_cmodel/infra/tu_debug.h"
#include "tu_cmodel/tu_core.h"
#include "tests/test_framework.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

tu_test_stats_t g_test_stats = {0};
static int failures = 0;
#define CHECK_EQ(name, got, want) do { long long g=(long long)(got), w=(long long)(want); printf("CHECK %s got=%lld want=%lld %s\n",name,g,w,g==w?"PASS":"FAIL"); if(g!=w) failures++; } while(0)

static int strict_finite_compare(const float *a,const float *b,size_t n,float tol){
  for(size_t i=0;i<n;i++) if(!isfinite(a[i])||!isfinite(b[i])||fabsf(a[i]-b[i])>tol) return 0;
  return 1;
}
int main(void){
  float expected[1]={1.0f}, actual_nan[1]={NAN};
  test_stats_init();
  int shared=compare_tensors("nan discriminator",expected,actual_nan,1,0.0f);
  int strict=strict_finite_compare(expected,actual_nan,1,0.0f);
  printf("ORACLE_NAN shared_accept=%d strict_accept=%d shared_pass=%d shared_fail=%d\n",shared,strict,g_test_stats.tests_pass,g_test_stats.tests_fail);
  CHECK_EQ("shared_nan_accept",shared,1); CHECK_EQ("strict_nan_reject",strict,0);

  tu_config_t cfg; char err[128]={0};
  const char *json="{\"tu\":{\"compute\":{\"pe_array\":{\"rows\":8,\"cols\":4,\"dataflow\":\"output_stationary\"}}}}";
  int prc=tu_config_load_string(json,&cfg,err,sizeof(err));
  tu_runtime_config_t rt=tu_config_to_runtime(&cfg);
  tu_init_with_config(&rt);
  const char *active=tu_get_dataflow_name();
  printf("CONFIG_EFFECT parse_rc=%d parsed_df=%d rt_rows=%u rt_cols=%u active=%s\n",prc,cfg.dataflow_mode,rt.pe_rows,rt.pe_cols,active);
  CHECK_EQ("config_parse",prc,0); CHECK_EQ("config_parsed_os",cfg.dataflow_mode,TU_DATAFLOW_MODE_OS);
  CHECK_EQ("config_rt_rows",rt.pe_rows,8); CHECK_EQ("config_rt_cols",rt.pe_cols,4);
  CHECK_EQ("config_active_ws",strcmp(active,"weight_stationary"),0);

  tu_core_t *core=tu_core_create(&rt); CHECK_EQ("core_create",core!=NULL,1); if(!core) return 1; tu_core_init(core);
  FILE *f=tmpfile(); size_t reported=tu_debug_dump_state(core,f,TU_DUMP_TEXT,TU_DUMP_COUNTERS); long actual_bytes=ftell(f);
  printf("DUMP_SIZE reported=%zu actual=%ld\n",reported,actual_bytes); CHECK_EQ("dump_reported_zero",reported,0); CHECK_EQ("dump_actual_positive",actual_bytes>0,1); fclose(f);

  uint32_t csum=tu_debug_checksum_sram(core); tu_replay_trace_t tr={0};
  CHECK_EQ("replay_start",tu_debug_record_start(&tr,1),0);
  CHECK_EQ("replay_record",tu_debug_record_instr(&tr,7,0xFE,0,3,4,5,0x11223344,csum,csum),0); tu_debug_record_stop(&tr);
  FILE *rf=tmpfile(); int mm0=tu_debug_replay_execute(core,&tr,rf); long replay_bytes=ftell(rf); fclose(rf);
  tr.entries[0].checksum_delta=1; rf=tmpfile(); int mm1=tu_debug_replay_execute(core,&tr,rf); fclose(rf);
  printf("REPLAY_NOOP arbitrary_opcode=0xFE mismatches_equal=%d mismatches_mutated=%d output_bytes=%ld\n",mm0,mm1,replay_bytes);
  CHECK_EQ("replay_noop_accept",mm0,0); CHECK_EQ("replay_mutation_detect",mm1,1); tu_debug_record_destroy(&tr);

  int wrapped=tu_debug_assert_bounds(UINT32_MAX-3u,8u,16u,"wrap");
  int ordinary=tu_debug_assert_bounds(15u,2u,16u,"ordinary");
  printf("BOUNDS_WRAP wrapped_accept=%d ordinary_accept=%d\n",wrapped,ordinary);
  CHECK_EQ("bounds_wrap_unsafe_green",wrapped,1); CHECK_EQ("bounds_ordinary_reject",ordinary,0);
  tu_core_destroy(core);
  printf("CH20_PROBE SUMMARY failures=%d\n",failures); return failures?1:0;
}
