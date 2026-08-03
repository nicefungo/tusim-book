/* Chapter 9 memory hierarchy/banked SRAM probe for Tusim e918c80.
 * Build only in an isolated git-archive extraction.
 */
#include "tu_cmodel/tu_cmodel.h"
#include "tu_cmodel/tu_sram.h"
#include "tu_cmodel/memory/memory_hierarchy.h"
#include "tu_cmodel/infra/config.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void check(int ok, const char *msg) {
    if (!ok) { fprintf(stderr, "FAIL: %s\n", msg); exit(1); }
}

static void audit_sram_budget(void) {
    tu_sram_region_t r;
    uint32_t a = 0x11111111u, b = 0x22222222u, c = 0x33333333u, out = 0;
    tu_sram_init_bw(&r, 1024, "probe", 1, TU_SRAM_ARB_ROUND_ROBIN, 3, 4);
    check(r.banks.bank_count == 32 && r.banks.bank_width == 4, "compiled SRAM geometry changed");
    uint64_t s0 = tu_sram_write(&r, 0, &a);
    uint64_t s1 = tu_sram_write(&r, 0, &b);
    uint64_t s2 = tu_sram_write(&r, 4, &c);
    check(s0 == 0 && s1 == 3 && s2 == 0, "bank budget/stall sequence mismatch");
    tu_sram_read_bulk(&r, 0, &out, sizeof(out));
    check(out == b, "stalled write did not copy immediately");
    check(r.banks.conflicts == 0, "conflict counter unexpectedly active");
    uint64_t s3 = tu_sram_write(&r, 0, &a);
    tu_sram_advance_cycle(&r, 3);
    uint64_t s4 = tu_sram_write(&r, 0, &a);
    tu_sram_advance_cycle(&r, 1);
    uint64_t s5 = tu_sram_write(&r, 0, &a);
    check(s3 == 3 && s4 == 3 && s5 == 0, "explicit refill boundary mismatch");
    uint64_t reads0 = r.banks.reads, writes0 = r.banks.writes, stalls0 = r.banks.stall_cycles;
    ((uint32_t *)tu_sram_raw_ptr(&r))[8] = 0xabcdef01u;
    check(r.banks.reads == reads0 && r.banks.writes == writes0 && r.banks.stall_cycles == stalls0,
          "raw pointer unexpectedly accounted");
    uint64_t br=0,bw=0,brs=0,bws=0; float bu=0.0f;
    tu_sram_get_bank_bw_stats(&r, 0, &br, &bw, &brs, &bws, &bu);
    check(bu == 1.0f && br + bw > 1, "expected clipped initial-window utilization snapshot");
    printf("SRAM_BUDGET bank_count=%u bank_width=%u sequence=%lu,%lu,%lu "
           "refill=%lu,%lu,%lu stalled_copy=%08x conflicts=%lu raw_bypass=PASS\n",
           r.banks.bank_count, r.banks.bank_width,
           (unsigned long)s0, (unsigned long)s1, (unsigned long)s2,
           (unsigned long)s3, (unsigned long)s4, (unsigned long)s5, out,
           (unsigned long)r.banks.conflicts);
    printf("UTILIZATION bank0_served=%lu reported=%.1f initial_window_omitted_and_clipped=yes\n",
           (unsigned long)(br+bw), (double)bu);
    tu_sram_destroy(&r);
}

static uint64_t arbitration_sequence(uint8_t mode) {
    tu_sram_region_t r; uint32_t x = 1;
    tu_sram_init_bw(&r, 256, "arb", 1, mode, 5, 4);
    uint64_t sum = tu_sram_write(&r, 0, &x) + tu_sram_write(&r, 0, &x) +
                   tu_sram_read(&r, 0, &x);
    tu_sram_destroy(&r); return sum;
}

static void audit_arbitration(void) {
    uint64_t none = arbitration_sequence(TU_SRAM_ARB_NONE);
    uint64_t rr = arbitration_sequence(TU_SRAM_ARB_ROUND_ROBIN);
    uint64_t pri = arbitration_sequence(TU_SRAM_ARB_PRIORITY);
    check(none == rr && rr == pri && rr == 10, "arbitration enum changed behavior");
    printf("ARBITRATION none=%lu round_robin=%lu priority=%lu behavior=identical\n",
           (unsigned long)none, (unsigned long)rr, (unsigned long)pri);
}

static void audit_hierarchy(void) {
    tu_memory_hierarchy_t h;
    memset(&h, 0, sizeof(h));
    tu_mem_level_config_t custom = {
        TU_MEM_GLOBAL_BUF, "custom", 2048, 2, 4, 9, 9, 2, 2, 7, false
    };
    tu_mem_hierarchy_set_level_config(&h, TU_MEM_GLOBAL_BUF, &custom);
    tu_mem_hierarchy_init(&h);
    check(h.level_configs[TU_MEM_GLOBAL_BUF].size_bytes == TU_MEM_GBUF_SIZE,
          "pre-init override unexpectedly survived");
    check(h.gbuf.config.bank_count == TU_MEM_GBUF_BANKS &&
          h.gbuf.sram.banks.bank_width == TU_MEM_GBUF_BANK_WIDTH,
          "GBuf compiled geometry mismatch");

    uint64_t v = 0x1122334455667788ull, out = ~0ull, stall = 0;
    check(tu_mem_hierarchy_write(&h, TU_MEM_GLOBAL_BUF, NULL, 0, &v, 8, &stall) == 0 && stall == 0,
          "GBuf first write mismatch");
    check(tu_mem_hierarchy_write(&h, TU_MEM_GLOBAL_BUF, NULL, 0, &v, 8, &stall) == 0 && stall == 2,
          "GBuf second write should stall");
    tu_mem_hierarchy_tick(&h, 4);
    check(tu_mem_hierarchy_write(&h, TU_MEM_GLOBAL_BUF, NULL, 0, &v, 8, &stall) == 0 && stall == 2,
          "hierarchy tick unexpectedly refilled GBuf");
    tu_sram_advance_cycle(tu_gbuf_get_sram(&h.gbuf), 4);
    check(tu_mem_hierarchy_write(&h, TU_MEM_GLOBAL_BUF, NULL, 0, &v, 8, &stall) == 0 && stall == 0,
          "direct GBuf advance did not refill");

    check(tu_mem_hierarchy_write(&h, TU_MEM_REGFILE, NULL, 0, &v, 8, &stall) == 0,
          "RegFile write failed");
    check(tu_mem_hierarchy_read(&h, TU_MEM_REGFILE, NULL, 0, &out, 8, &stall) == 0,
          "RegFile read failed");
    check(out == 0, "RegFile unexpectedly retained data");
    uint64_t gcycle = tu_sram_get_cycle(tu_gbuf_get_sram(&h.gbuf));
    int32_t gwords = tu_gbuf_get_sram(&h.gbuf)->banks.bw_banks[0].words_available;
    tu_mem_hierarchy_reset(&h);
    check(h.current_cycle == 0 &&
          tu_sram_get_cycle(tu_gbuf_get_sram(&h.gbuf)) == gcycle &&
          tu_gbuf_get_sram(&h.gbuf)->banks.bw_banks[0].words_available == gwords,
          "hierarchy reset unexpectedly reset GBuf refill state");
    printf("HIERARCHY preinit_override=erased gbuf=%uB/%ubanks/%uBword "
           "tick_refill=no direct_refill=yes reset_refill_state=preserved regfile_storage=no hits_before_reset=4\n",
           h.gbuf.config.size_bytes, h.gbuf.config.bank_count, h.gbuf.config.bank_width);
    tu_mem_hierarchy_destroy(&h);
}

static void audit_config_and_mma_bypass(void) {
    const char *json = "{\"tu\":{\"compute\":{\"pe_array\":{\"rows\":4,\"cols\":8}},"
                       "\"memory\":{\"sram\":{\"w_buffer_kb\":16,\"a_buffer_kb\":8,\"o_buffer_kb\":12},"
                       "\"banking\":{\"banks\":8,\"bank_width_bytes\":8}}}}";
    tu_config_t cfg; char err[256] = {0};
    check(tu_config_load_string(json, &cfg, err, sizeof(err)) == 0, "memory config parse failed");
    check(cfg.sram_num_banks == 8 && cfg.sram_bank_width == 8, "banking request not parsed");
    tu_runtime_config_t rt = tu_config_to_runtime(&cfg);
    check(rt.sram_w_size == 16u*1024 && rt.sram_a_size == 8u*1024 && rt.sram_o_size == 12u*1024,
          "SRAM capacities not propagated");
    check(tu_init_from_config(&cfg) == 0, "init from memory config failed");
    check(g_tu.sram_w.total_size == 16u*1024 && g_tu.sram_w.banks.bank_count == TU_SRAM_BANKS &&
          g_tu.sram_w.banks.bank_width == TU_SRAM_BANK_WIDTH, "active W SRAM contract mismatch");

    fp16_t one = fp32_to_fp16(1.0f); fp32_t zero = 0.0f;
    tu_dma_load_w(&one, 0, sizeof(one));
    tu_dma_load_a(&one, 0, sizeof(one));
    tu_dma_load_o(&zero, 0, sizeof(zero));
    uint64_t wr = g_tu.sram_w.banks.reads, ww = g_tu.sram_w.banks.writes;
    uint64_t ar = g_tu.sram_a.banks.reads, aw = g_tu.sram_a.banks.writes;
    uint64_t orr = g_tu.sram_o.banks.reads, ow = g_tu.sram_o.banks.writes;
    tu_mma(1, 1, 1, 0, 0, 0, false);
    check(g_tu.sram_w.banks.reads == wr && g_tu.sram_w.banks.writes == ww &&
          g_tu.sram_a.banks.reads == ar && g_tu.sram_a.banks.writes == aw &&
          g_tu.sram_o.banks.reads == orr && g_tu.sram_o.banks.writes == ow,
          "MMA unexpectedly used accounted SRAM APIs");
    printf("CONFIG requested_banks=8x8B active_banks=%ux%uB capacities=%u/%u/%u "
           "mma_sram_counter_delta=0/0/0 hierarchy_integration=absent\n",
           g_tu.sram_w.banks.bank_count, g_tu.sram_w.banks.bank_width,
           g_tu.sram_w.total_size, g_tu.sram_a.total_size, g_tu.sram_o.total_size);
}

int main(void) {
    audit_sram_budget();
    audit_arbitration();
    audit_hierarchy();
    audit_config_and_mma_bypass();
    printf("SUMMARY: PASS failures=0\n");
    return 0;
}
