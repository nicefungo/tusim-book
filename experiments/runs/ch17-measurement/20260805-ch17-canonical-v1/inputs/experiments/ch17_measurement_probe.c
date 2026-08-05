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

    tu_perf_counters_t r;
    tu_perf_init(&r,1000.0);
    r.compute.df_ws_cycles=7; r.memory.mem_gbuf_bank_conflicts=9; r.memory.mem_dram_row_hits=11;
    r.power.energy_total_pj=13.0;
    tu_perf_snapshot_t b=tu_perf_snapshot(&r);
    r.compute.df_ws_cycles=17; r.memory.mem_gbuf_bank_conflicts=19; r.memory.mem_dram_row_hits=21;
    r.power.energy_total_pj=23.0;
    tu_perf_snapshot_t a=tu_perf_snapshot(&r);
    tu_perf_counters_t d=tu_perf_diff(&b,&a);
    tu_perf_counters_t m; tu_perf_init(&m,1000.0); tu_perf_merge(&m,&r);
    printf("PERF_OMISSIONS diff_ws=%lu diff_gbuf_conf=%lu diff_row_hits=%lu merge_ws=%lu merge_gbuf_conf=%lu merge_row_hits=%lu merge_energy_total=%.1f\n",
      (unsigned long)d.compute.df_ws_cycles,(unsigned long)d.memory.mem_gbuf_bank_conflicts,
      (unsigned long)d.memory.mem_dram_row_hits,(unsigned long)m.compute.df_ws_cycles,
      (unsigned long)m.memory.mem_gbuf_bank_conflicts,(unsigned long)m.memory.mem_dram_row_hits,m.power.energy_total_pj);
    CHECK(d.compute.df_ws_cycles==0 && d.memory.mem_gbuf_bank_conflicts==0 && d.memory.mem_dram_row_hits==0);
    CHECK(m.compute.df_ws_cycles==0 && m.memory.mem_gbuf_bank_conflicts==0 && m.memory.mem_dram_row_hits==0 && m.power.energy_total_pj==0.0);
    r.power.energy_mac_pj=99.0; tu_perf_reset(&r);
    printf("PERF_RESET energy_mac=%.1f total=%lu\n",r.power.energy_mac_pj,(unsigned long)r.total_cycles);
    CHECK(r.power.energy_mac_pj==99.0 && r.total_cycles==0);

    tu_perf_counters_t metric; tu_perf_init(&metric,1000.0); metric.total_cycles=10; metric.dma.dma_read_bytes=100; metric.compute.total_macs=10;
    metric.compute.compute_total_cycles=10; metric.compute.compute_active_cycles=5; metric.compute.compute_utilization=.5f;
    tu_perf_metrics_t mm=tu_perf_compute_metrics(&metric);
    printf("PERF_METRICS dma_gbps=%.3f tops=%.6f efficiency=%.9f util=%.3f hit=%.3f\n",mm.dma_bandwidth_gbps,mm.mac_throughput_tops,mm.mac_efficiency,mm.compute_utilization,mm.spad_hit_rate);
    CHECK(near(mm.dma_bandwidth_gbps,10.0,1e-6) && near(mm.mac_throughput_tops,.001,1e-8));

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
