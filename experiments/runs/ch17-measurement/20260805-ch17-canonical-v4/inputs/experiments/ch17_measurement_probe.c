#include "tu_cmodel/tu_cmodel.h"
#include "tu_cmodel/infra/logging.h"
#include "tu_cmodel/perf/performance_counters.h"
#include "tu_cmodel/perf/event_trace.h"
#include "tu_cmodel/perf/cycle_model.h"
#include "tu_cmodel/perf/power_model.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failures;
#define CHECK(c) do { if (!(c)) { fprintf(stderr,"CHECK_FAIL line=%d expr=%s\n",__LINE__,#c); failures++; } } while (0)
static int near(double a,double b,double e){ return fabs(a-b)<=e; }

int main(void) {
    tu_perf_counters_t p;
    tu_perf_init(&p, 1000.0);
    tu_perf_dma_record_read(&p,64,10,2,1,0);
    tu_perf_compute_record_mma(&p,8,2,2,2,1,0,5,1,1,0);
    printf("PERF_ADDITIVE total=%lu wall_ns=%lu dma_read=%lu dma_stall=%lu compute=%lu macs=%lu leak=%.3f\n",
      (unsigned long)p.total_cycles,(unsigned long)p.wall_clock_ns,(unsigned long)p.dma.dma_read_bytes,
      (unsigned long)p.dma.dma_stall_cycles,(unsigned long)p.compute.compute_total_cycles,
      (unsigned long)p.compute.total_macs,p.power.energy_leakage_pj);
    CHECK(p.total_cycles==18 && p.wall_clock_ns==18 && p.compute.compute_total_cycles==6);
    tu_perf_tick(&p,6);
    printf("PERF_DUPLICATE after_explicit_tick=%lu compute=%lu\n",(unsigned long)p.total_cycles,(unsigned long)p.compute.compute_total_cycles);
    CHECK(p.total_cycles==24 && p.compute.compute_total_cycles==6);

    tu_perf_counters_t tm; tu_perf_init(&tm,1000.0);
    tu_perf_compute_record_op(&tm,2,4,1,8); tu_perf_compute_record_idle(&tm,2);
    tu_perf_mem_record_spad_access(&tm,false,1,1,3); tu_perf_mem_record_dram_access(&tm,false,64,true,4);
    tu_perf_dma_record_internal(&tm,16,2,0);
    uint64_t timed=tm.total_cycles;
    tu_perf_mem_record_gbuf_access(&tm,false,1,1); tu_perf_mem_record_reqfile_access(&tm,false,1);
    tu_perf_compute_record_pipeline_bubble(&tm,1);
    tu_perf_counters_t desc; tu_perf_init(&desc,1000.0);
    tu_perf_from_dma_descriptor(&desc,1024,0,0,true,10,2,1);
    printf("PERF_TIME_MAP op=5 idle=2 spad=3 dram=4 internal=2 timed=%lu after_no_time=%lu descriptor=13\n",
      (unsigned long)timed,(unsigned long)tm.total_cycles);
    CHECK(timed==16 && tm.total_cycles==16 && desc.total_cycles==13);

    tu_perf_counters_t r;
    tu_perf_init(&r,1000.0);
    r.compute.df_ws_cycles=7; r.compute.df_os_cycles=8; r.memory.mem_gbuf_bank_conflicts=9;
    r.memory.mem_dram_row_hits=11; r.memory.mem_dram_row_misses=12;
    r.memory.spad_bw_utilization=.2f; r.memory.gbuf_bw_utilization=.3f; r.memory.dram_bw_utilization=.4f;
    r.wall_clock_ns=14; r.power.energy_total_pj=13.0;
    tu_perf_power_config(&r,71,72,73,74,75,76); r.power.power_modeling_enabled=false;
    tu_perf_snapshot_t b=tu_perf_snapshot(&r);
    r.compute.df_ws_cycles=17; r.compute.df_os_cycles=18; r.memory.mem_gbuf_bank_conflicts=19;
    r.memory.mem_dram_row_hits=21; r.memory.mem_dram_row_misses=22;
    r.memory.spad_bw_utilization=.5f; r.memory.gbuf_bw_utilization=.6f; r.memory.dram_bw_utilization=.7f;
    r.wall_clock_ns=24; r.power.energy_total_pj=23.0;
    tu_perf_power_config(&r,81,82,83,84,85,86); r.power.power_modeling_enabled=true;
    tu_perf_snapshot_t a=tu_perf_snapshot(&r);
    tu_perf_counters_t d=tu_perf_diff(&b,&a);
    r.clock_freq_mhz=500.0; r.enabled=true;
    tu_perf_counters_t m; tu_perf_init(&m,1000.0); m.enabled=false; m.power.power_modeling_enabled=false; tu_perf_merge(&m,&r);
    printf("PERF_DIFF_OMISSIONS ws=%lu os=%lu gbuf=%lu hits=%lu misses=%lu bw=%.1f/%.1f/%.1f wall=%lu params=%.0f/%.0f/%.0f/%.0f/%.0f/%.0f enabled=%d\n",
      (unsigned long)d.compute.df_ws_cycles,(unsigned long)d.compute.df_os_cycles,
      (unsigned long)d.memory.mem_gbuf_bank_conflicts,(unsigned long)d.memory.mem_dram_row_hits,
      (unsigned long)d.memory.mem_dram_row_misses,d.memory.spad_bw_utilization,d.memory.gbuf_bw_utilization,
      d.memory.dram_bw_utilization,(unsigned long)d.wall_clock_ns,d.power.pj_per_mac,d.power.pj_per_sram_read,
      d.power.pj_per_sram_write,d.power.pj_per_dram_access,d.power.pj_per_dma_byte,d.power.pj_leakage_per_cycle,
      d.power.power_modeling_enabled);
    printf("PERF_MERGE_OMISSIONS ws=%lu os=%lu gbuf=%lu hits=%lu misses=%lu bw=%.1f/%.1f/%.1f wall=%lu total=%.1f params=%.2f/%.2f/%.2f/%.1f/%.3f/%.3f power_enabled=%d freq=%.0f enabled=%d\n",
      (unsigned long)m.compute.df_ws_cycles,(unsigned long)m.compute.df_os_cycles,
      (unsigned long)m.memory.mem_gbuf_bank_conflicts,(unsigned long)m.memory.mem_dram_row_hits,
      (unsigned long)m.memory.mem_dram_row_misses,m.memory.spad_bw_utilization,m.memory.gbuf_bw_utilization,
      m.memory.dram_bw_utilization,(unsigned long)m.wall_clock_ns,m.power.energy_total_pj,m.power.pj_per_mac,
      m.power.pj_per_sram_read,m.power.pj_per_sram_write,m.power.pj_per_dram_access,m.power.pj_per_dma_byte,
      m.power.pj_leakage_per_cycle,m.power.power_modeling_enabled,m.clock_freq_mhz,m.enabled);
    CHECK(d.compute.df_ws_cycles==0 && d.compute.df_os_cycles==0 && d.memory.mem_gbuf_bank_conflicts==0);
    CHECK(d.memory.mem_dram_row_hits==0 && d.memory.mem_dram_row_misses==0 && d.memory.spad_bw_utilization==0);
    CHECK(d.memory.gbuf_bw_utilization==0 && d.memory.dram_bw_utilization==0 && d.wall_clock_ns==0);
    CHECK(d.power.pj_per_mac==0 && d.power.pj_per_sram_read==0 && d.power.pj_per_sram_write==0);
    CHECK(d.power.pj_per_dram_access==0 && d.power.pj_per_dma_byte==0 && d.power.pj_leakage_per_cycle==0);
    CHECK(!d.power.power_modeling_enabled);
    CHECK(m.compute.df_ws_cycles==0 && m.compute.df_os_cycles==0 && m.memory.mem_gbuf_bank_conflicts==0);
    CHECK(m.memory.mem_dram_row_hits==0 && m.memory.mem_dram_row_misses==0 && m.memory.spad_bw_utilization==0);
    CHECK(m.memory.gbuf_bw_utilization==0 && m.memory.dram_bw_utilization==0 && m.wall_clock_ns==0 && m.power.energy_total_pj==0);
    CHECK(m.power.pj_per_mac==1.0 && m.power.pj_per_sram_read==.5 && m.power.pj_per_sram_write==.5);
    CHECK(m.power.pj_per_dram_access==20 && m.power.pj_per_dma_byte==.05 && m.power.pj_leakage_per_cycle==.001);
    CHECK(!m.power.power_modeling_enabled && m.clock_freq_mhz==1000.0 && !m.enabled);
    r.power.energy_mac_pj=99.0; r.clock_freq_mhz=777.0; r.enabled=false; tu_perf_reset(&r);
    printf("PERF_RESET enabled=%d freq=%.0f energy_mac=%.1f total=%lu\n",r.enabled,r.clock_freq_mhz,r.power.energy_mac_pj,(unsigned long)r.total_cycles);
    CHECK(r.enabled && r.clock_freq_mhz==777.0 && r.power.energy_mac_pj==99.0 && r.total_cycles==0);

    tu_perf_counters_t metric; tu_perf_init(&metric,1000.0); metric.total_cycles=10; metric.dma.dma_read_bytes=100; metric.compute.total_macs=10;
    metric.compute.compute_total_cycles=10; metric.compute.compute_active_cycles=5; metric.compute.compute_utilization=.5f;
    tu_perf_metrics_t mm=tu_perf_compute_metrics(&metric);
    printf("PERF_METRICS dma_gbps=%.3f tops=%.6f efficiency=%.9f util=%.3f hit=%.3f\n",mm.dma_bandwidth_gbps,mm.mac_throughput_tops,mm.mac_efficiency,mm.compute_utilization,mm.spad_hit_rate);
    CHECK(near(mm.dma_bandwidth_gbps,10.0,1e-6) && near(mm.mac_throughput_tops,.001,1e-8));
    tu_perf_counters_t pathological; tu_perf_init(&pathological,1000.0);
    pathological.total_cycles=1; pathological.compute.total_macs=512;
    pathological.memory.mem_spad_reads=1; pathological.memory.mem_spad_bank_conflicts=2;
    pathological.power.energy_mac_pj=1.0;
    tu_perf_metrics_t pmx=tu_perf_compute_metrics(&pathological);
    printf("PERF_UNBOUNDED efficiency=%.1f hit=%.1f reported_power_mw=%.1f physical_power_mw=1.0 cached_total=%.1f\n",
      pmx.mac_efficiency,pmx.spad_hit_rate,pmx.power_mw,pathological.power.energy_total_pj);
    CHECK(near(pmx.mac_efficiency,2.0,1e-6) && near(pmx.spad_hit_rate,-1.0,1e-6) && near(pmx.power_mw,1000.0,1e-3));
    CHECK(pathological.power.energy_total_pj==0.0);

    tu_cycle_model_t *est=tu_cycle_model_create(TU_CYCLE_MODEL_ESTIMATED,NULL);
    uint64_t ec=tu_cycle_model_execute_tile(est,0,2,0,3,0,4,0,0,0);
    printf("CYCLE_EST tile=%lu current=%lu\n",(unsigned long)ec,(unsigned long)est->current_cycle);
    CHECK(ec==14 && est->current_cycle==14); tu_cycle_model_destroy(est);

    tu_perf_counters_t cp; tu_perf_init(&cp,1000.0);
    tu_cycle_model_t *cm=tu_cycle_model_create(TU_CYCLE_MODEL_CYCLE_ACCURATE,&cp);
    uint64_t wc=tu_cycle_model_dma_transfer(cm,0,32,false,0,0);
    printf("CYCLE_WRITE cycles=%lu cm=%lu perf=%lu read_bytes=%lu write_bytes=%lu read_cycles=%lu write_cycles=%lu\n",
      (unsigned long)wc,(unsigned long)cm->current_cycle,(unsigned long)cp.total_cycles,
      (unsigned long)cp.dma.dma_read_bytes,(unsigned long)cp.dma.dma_write_bytes,
      (unsigned long)cp.dma.dma_read_cycles,(unsigned long)cp.dma.dma_write_cycles);
    CHECK(cp.dma.dma_read_bytes==32 && cp.dma.dma_write_bytes==0 && cp.total_cycles==wc);
    tu_cycle_model_advance(cm,5);
    printf("CYCLE_BRIDGE cm=%lu perf=%lu\n",(unsigned long)cm->current_cycle,(unsigned long)cp.total_cycles);
    CHECK(cm->current_cycle==wc+5 && cp.total_cycles==wc+5); tu_cycle_model_destroy(cm);
    tu_bank_model_t bank; tu_bank_model_init(&bank,1,4,1,2,2);
    uint32_t bst=tu_bank_model_access(&bank,0,false,1,0); uint64_t br,bw,bs,bc; double bu;
    tu_bank_model_get_stats(&bank,&br,&bw,&bs,&bc,&bu);
    printf("CYCLE_BANK isolated_stall=%u reads=%lu conflicts=%lu utilization=%.3f\n",bst,(unsigned long)br,(unsigned long)bc,bu);
    CHECK(bst==0 && br==1 && bc==1); tu_bank_model_destroy(&bank);
    tu_perf_counters_t rdperf,wrperf; tu_perf_init(&rdperf,1000); tu_perf_init(&wrperf,1000);
    tu_cycle_model_t *rd=tu_cycle_model_create(TU_CYCLE_MODEL_CYCLE_ACCURATE,&rdperf);
    tu_cycle_dram_destroy(rd->dram_channel); tu_dram_channel_init(rd->dram_channel,TU_DRAM_HBM2,1000,32);
    uint64_t rdcy=tu_cycle_model_dma_transfer(rd,0,4,true,4096,0);
    tu_cycle_model_t *wr=tu_cycle_model_create(TU_CYCLE_MODEL_CYCLE_ACCURATE,&wrperf);
    tu_cycle_dram_destroy(wr->dram_channel); tu_dram_channel_init(wr->dram_channel,TU_DRAM_HBM2,1000,32);
    uint64_t wrcy=tu_cycle_model_dma_transfer(wr,0,4,false,4096,0);
    printf("CYCLE_DMA_DIRECTION read_arg=%lu write_arg=%lu write_perf_read=%lu write_perf_write=%lu\n",
      (unsigned long)rdcy,(unsigned long)wrcy,(unsigned long)wrperf.dma.dma_read_bytes,(unsigned long)wrperf.dma.dma_write_bytes);
    CHECK(rdcy==21 && wrcy==28 && wrperf.dma.dma_read_bytes==4 && wrperf.dma.dma_write_bytes==0);
    tu_cycle_model_destroy(rd); tu_cycle_model_destroy(wr);

    const char *ev="/tmp/ch17-event.vcd";
    tu_event_trace_t *tr=tu_trace_create(ev,1); int si=tu_trace_add_signal(tr,"!","probe",TU_TRACE_SIG_1BIT);
    tu_trace_signal(tr,si,1); tu_trace_tick(tr,7);
    printf("TRACE_CONTEXT first_cycle=%lu dirty=%d enabled=%d\n",(unsigned long)tr->current_cycle,tr->signals[0].dirty,tu_trace_is_enabled());
    CHECK(tr->current_cycle==0 && tr->signals[0].dirty && !tu_trace_is_enabled());
    tu_trace_tick(tr,3); printf("TRACE_CONTEXT second_cycle=%lu dirty=%d\n",(unsigned long)tr->current_cycle,tr->signals[0].dirty);
    CHECK(tr->current_cycle==3 && !tr->signals[0].dirty); tu_trace_close(tr); remove(ev);

    tu_trace_clear(); tu_trace_event(TU_COMP_MMA,1,2,3,4,5); tu_trace_set_cycle(9); tu_trace_event(TU_COMP_DMA,2,3,4,5,6);
    uint32_t cnt=0; const tu_trace_event_t *tb=tu_trace_get_buffer(&cnt);
    printf("TRACE_LOG count=%u first=%lu second=%lu global=%lu\n",cnt,(unsigned long)tb[0].cycle,(unsigned long)tb[1].cycle,(unsigned long)tu_trace_get_cycle());
    CHECK(cnt==2 && tb[0].cycle==0 && tb[1].cycle==9);

    tu_power_model_t pm; tu_power_model_init(&pm,TU_TECH_NODE_7NM,1000.0);
    double area=tu_power_estimate_area(&pm,16,16,65536,262144);
    tu_power_record_mac(&pm,10,0); tu_power_record_spad_access(&pm,false,4);
    tu_power_record_dram_access(&pm,false,64,false); tu_power_record_dma(&pm,64); tu_power_tick(&pm,10); tu_power_compute_total(&pm);
    printf("POWER_TABLE area=%.6f mac=%.3f spad=%.3f dram=%.3f dma=%.3f clock=%.3f leak=%.4f total=%.4f avg_mw=%.4f\n",
      area,pm.energy_mac_pj,pm.energy_spad_read_pj,pm.energy_dram_read_pj+pm.energy_dram_activate_pj,
      pm.energy_dma_pj,pm.energy_clock_pj,pm.energy_leakage_pj,pm.energy_total_pj,tu_power_get_avg_power_mw(&pm));
    CHECK(near(area,1.051648,1e-9) && near(pm.energy_total_pj,425.7224,1e-4) && near(tu_power_get_avg_power_mw(&pm),42.57224,1e-5));
    tu_power_snapshot_t pb=tu_power_snapshot(&pm); tu_power_model_reset(&pm); tu_power_snapshot_t pa=tu_power_snapshot(&pm);
    tu_power_model_t pd=tu_power_diff(&pb,&pa);
    printf("POWER_DECREASING_DIFF cycles=%lu macs=%lu energy_mac=%.3f\n",(unsigned long)pd.total_cycles,(unsigned long)pd.total_macs,pd.energy_mac_pj);
    CHECK(pd.total_cycles>1000000ULL && pd.total_macs>1000000ULL && pd.energy_mac_pj<0.0);

    printf("CH17_PROBE SUMMARY failures=%d\n",failures);
    return failures ? 1 : 0;
}
