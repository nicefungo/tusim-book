/* Chapter 15 DRAM service-model probe; edition pin e918c80. */
#include "tu_cmodel/memory/dram_model.h"
#include "tu_cmodel/memory/memory_hierarchy.h"
#include "tu_cmodel/infra/config.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int failures = 0;
#define CHECK(c, m) do { if (!(c)) { printf("PROBE FAIL %s\n", m); failures++; } } while (0)

int main(void) {
    printf("CH15_PROBE start\n");

    tu_dram_model_t *h2 = tu_dram_create(TU_DRAM_TYPE_HBM2);
    tu_dram_model_t *h3 = tu_dram_create(TU_DRAM_TYPE_HBM3);
    CHECK(h2 && h3, "preset create");
    printf("PRESET hbm2 bw=%.1f channels=%u burst=%u rlat=%u hbm3_bw=%.1f hbm3_channels=%u\n",
           h2->params.bandwidth_gbps, h2->num_channels, h2->params.burst_length,
           h2->params.read_latency_cycles, h3->params.bandwidth_gbps, h3->num_channels);
    uint64_t e64 = tu_dram_estimate_transfer(h2, 64, true);
    uint64_t e819 = tu_dram_estimate_transfer(h3, 819, true);
    printf("ESTIMATE hbm2_read64=%llu hbm3_read819=%llu\n",
           (unsigned long long)e64, (unsigned long long)e819);
    CHECK(e64 == 51 && e819 == 41, "estimates");

    printf("INITIAL cycle=%llu window=%llu budget=%llu\n",
           (unsigned long long)h2->current_cycle,
           (unsigned long long)h2->bw_window_size_cycles,
           (unsigned long long)h2->bandwidth_available);
    uint64_t cyc = 0, st = 0;
    tu_dram_read(h2, 0, 64, &cyc, &st);
    printf("ACCESS first cycles=%llu stall=%llu current=%llu budget=%llu pending_r=%llu ch0_avail=%llu\n",
           (unsigned long long)cyc, (unsigned long long)st,
           (unsigned long long)h2->current_cycle,
           (unsigned long long)h2->bandwidth_available,
           (unsigned long long)h2->pending_read_bytes,
           (unsigned long long)h2->channel_available_cycle[0]);
    CHECK(cyc == 50 && st == 1000 && h2->current_cycle == 0, "first access");

    tu_dram_read(h2, 0, 64, &cyc, &st);
    printf("ACCESS same_channel cycles=%llu stall=%llu current=%llu\n",
           (unsigned long long)cyc, (unsigned long long)st,
           (unsigned long long)h2->current_cycle);
    CHECK(cyc == 50 && st == 1050, "same channel");
    tu_dram_read(h2, 64, 64, &cyc, &st);
    printf("ACCESS next_channel cycles=%llu stall=%llu current=%llu ch1_avail=%llu\n",
           (unsigned long long)cyc, (unsigned long long)st,
           (unsigned long long)h2->current_cycle,
           (unsigned long long)h2->channel_available_cycle[1]);
    CHECK(cyc == 50 && st == 1000, "next channel");

    for (int i = 0; i < 1000; i++) tu_dram_tick(h2);
    tu_dram_read(h2, 128, 64, &cyc, &st);
    printf("REFILL cycle=%llu cycles=%llu stall=%llu budget=%llu pending_r=%llu\n",
           (unsigned long long)h2->current_cycle, (unsigned long long)cyc,
           (unsigned long long)st, (unsigned long long)h2->bandwidth_available,
           (unsigned long long)h2->pending_read_bytes);
    CHECK(h2->current_cycle == 1000 && cyc == 50 && st == 0 &&
          h2->bandwidth_available == 255936 && h2->pending_read_bytes == 64,
          "refill");

    tu_dram_model_t *row = tu_dram_create(TU_DRAM_TYPE_HBM2);
    tu_dram_set_row_modeling(row, true);
    tu_dram_read(row, 0, 64, &cyc, &st);
    uint64_t read_cyc = cyc, read_st = st;
    tu_dram_write(row, 0, 64, &cyc, &st);
    printf("ROW read_cycles=%llu read_stall=%llu write_cycles=%llu write_stall=%llu conflicts=%llu\n",
           (unsigned long long)read_cyc, (unsigned long long)read_st,
           (unsigned long long)cyc, (unsigned long long)st,
           (unsigned long long)row->stats.total_row_conflicts);
    CHECK(read_cyc == 60 && read_st == 1000 && cyc == 50 && st == 1060 &&
          row->stats.total_row_conflicts == 1, "row asymmetry");

    tu_dram_model_t *statsm = tu_dram_create(TU_DRAM_TYPE_HBM2);
    tu_dram_read(statsm, 0, 1024, &cyc, &st);
    tu_dram_stats_t s = {0};
    tu_dram_get_stats(statsm, &s);
    printf("STATS cycle=%llu read_bw=%.1f util=%.1f peak=%.1f\n",
           (unsigned long long)statsm->current_cycle,
           s.effective_read_bandwidth, s.utilization, statsm->params.bandwidth_gbps);
    CHECK(fabs(s.effective_read_bandwidth - 1024.0) < 1e-9 &&
          fabs(s.utilization - 4.0) < 1e-9, "stats over peak");

    uint64_t before = tu_dram_estimate_transfer(h2, 64, true);
    tu_dram_set_core_clock(h2, 2.0);
    uint64_t after = tu_dram_estimate_transfer(h2, 64, true);
    printf("CLOCK peak1=%llu peak2=%llu estimate_before=%llu estimate_after=%llu\n",
           (unsigned long long)tu_dram_peak_bw_per_cycle(h2, 1.0),
           (unsigned long long)tu_dram_peak_bw_per_cycle(h2, 2.0),
           (unsigned long long)before, (unsigned long long)after);
    CHECK(before == after && before == 51 &&
          tu_dram_peak_bw_per_cycle(h2, 1.0) == 256 &&
          tu_dram_peak_bw_per_cycle(h2, 2.0) == 128, "clock no-op");

    tu_memory_hierarchy_t mh;
    tu_mem_hierarchy_init(&mh);
    unsigned char marker = 0x5a;
    uint64_t hstall = 0;
    int hrc = tu_mem_hierarchy_read(&mh, TU_MEM_DRAM, NULL, 0, &marker, 64, &hstall);
    printf("HIER type=%d rc=%d stall=%llu marker=0x%02x dram_cycle=%llu\n",
           mh.dram ? (int)mh.dram->type : -1, hrc, (unsigned long long)hstall,
           marker, mh.dram ? (unsigned long long)mh.dram->current_cycle : 0ULL);
    CHECK(mh.dram && mh.dram->type == TU_DRAM_TYPE_HBM2 && hrc == 0 &&
          hstall == 1000 && marker == 0x5a && mh.dram->current_cycle == 0,
          "hierarchy boundary");
    tu_mem_hierarchy_destroy(&mh);

    const char *json = "{\"memory\":{\"dram\":{\"type\":\"hbm3\",\"bandwidth_gbps\":777.0,\"model_row_conflicts\":true,\"core_clock_ghz\":2.0},\"latency\":{\"dram_read\":33,\"dram_write\":44}}}";
    tu_config_t cfg;
    char err[256] = {0};
    int crc = tu_config_load_string(json, &cfg, err, sizeof(err));
    tu_dram_model_t *manual = tu_dram_create((tu_dram_type_t)cfg.dram_type);
    printf("CONFIG rc=%d type=%d bw=%.1f row=%d rlat=%.0f wlat=%.0f manual_bw=%.1f manual_row=%d\n",
           crc, cfg.dram_type, cfg.dram_bandwidth_gbps,
           cfg.dram_model_row_conflicts ? 1 : 0, cfg.dram_latency_read,
           cfg.dram_latency_write, manual ? manual->params.bandwidth_gbps : -1.0,
           manual && manual->params.model_row_conflicts ? 1 : 0);
    CHECK(crc == 0 && cfg.dram_type == 3 && cfg.dram_bandwidth_gbps == 777.0 &&
          cfg.dram_model_row_conflicts && cfg.dram_latency_read == 33 &&
          cfg.dram_latency_write == 44 && manual &&
          manual->params.bandwidth_gbps == 819.0 && !manual->params.model_row_conflicts,
          "config manual boundary");

    tu_dram_destroy(manual);
    tu_dram_destroy(statsm);
    tu_dram_destroy(row);
    tu_dram_destroy(h3);
    tu_dram_destroy(h2);
    printf("CH15_PROBE SUMMARY failures=%d\n", failures);
    return failures == 0 ? 0 : 1;
}
