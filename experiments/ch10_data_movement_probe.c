#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "tu_cmodel/tu_cmodel.h"
#include "tu_cmodel/dma_descriptor.h"
#include "tu_cmodel/memory/address_generator.h"
#include "tu_cmodel/memory/double_buffer.h"
#include "tu_cmodel/compute/pipeline_controller.h"

static int failures = 0;

#define CHECK(cond, label) do { \
    printf("CHECK %-44s %s\n", (label), (cond) ? "PASS" : "FAIL"); \
    if (!(cond)) failures++; \
} while (0)

static tu_dma_descriptor_t *linear_desc(uint8_t ch, tu_sram_region_t *r,
                                        uint32_t off, const void *src,
                                        uint32_t bytes) {
    return tu_dma_desc_create_linear(ch, TU_DMA_DIR_HOST_TO_TU,
                                     r, off, (void *)src, 1, bytes);
}

static void probe_async_visibility(void) {
    printf("\n[async_visibility]\n");
    tu_dma_init_full(true, 2, 4);
    tu_sram_region_t r;
    tu_sram_init(&r, 4096, "async");
    tu_sram_set_bw_modeling(&r, false);

    uint8_t src[64], *dst = (uint8_t *)tu_sram_raw_ptr(&r);
    memset(src, 0x5a, sizeof(src));
    memset(dst, 0, sizeof(src));
    tu_dma_descriptor_t *d = linear_desc(0, &r, 0, src, sizeof(src));
    uint32_t id = tu_dma_submit_desc(d);
    printf("after_submit id=%u engine_cycle=%" PRIu64 " queue=%u active=%d data=%u completed=%d cycles_completed=%" PRIu64 "\n",
           id, g_tu_dma.current_cycle, g_tu_dma.channels[0].queue_depth,
           g_tu_dma.channels[0].active != NULL, dst[0], d->completed,
           d->cycles_completed);
    CHECK(id != 0 && dst[0] == 0 && !d->completed,
          "submit defers bytes and completion");

    int retired = tu_dma_tick();
    printf("after_tick1 retired=%d engine_cycle=%" PRIu64 " queue=%u active=%d data=%u completed=%d cycles_completed=%" PRIu64 " channel_completed=%" PRIu64 "\n",
           retired, g_tu_dma.current_cycle, g_tu_dma.channels[0].queue_depth,
           g_tu_dma.channels[0].active != NULL, dst[0], d->completed,
           d->cycles_completed, g_tu_dma.channels[0].total_completed);
    CHECK(dst[0] == 0x5a && d->completed &&
          d->cycles_completed > g_tu_dma.current_cycle &&
          g_tu_dma.channels[0].active == d &&
          g_tu_dma.channels[0].total_completed == 0,
          "visibility precedes channel retirement");

    while (g_tu_dma.channels[0].active && g_tu_dma.current_cycle < 10000)
        tu_dma_tick();
    printf("after_retire engine_cycle=%" PRIu64 " active=%d channel_completed=%" PRIu64 "\n",
           g_tu_dma.current_cycle, g_tu_dma.channels[0].active != NULL,
           g_tu_dma.channels[0].total_completed);
    CHECK(g_tu_dma.current_cycle == d->cycles_completed &&
          g_tu_dma.channels[0].total_completed == 1,
          "retirement occurs at cycles_completed");

    tu_dma_desc_destroy(d);
    tu_sram_destroy(&r);
    tu_dma_destroy();
}

static void probe_channel_and_queue_state(void) {
    printf("\n[channel_and_queue]\n");
    tu_dma_init_full(true, 2, 2);
    tu_sram_region_t r;
    tu_sram_init(&r, 4096, "channels");
    tu_sram_set_bw_modeling(&r, false);
    uint8_t a[32], b[32];
    memset(a, 0xa1, sizeof(a));
    memset(b, 0xb2, sizeof(b));
    tu_dma_descriptor_t *d0 = linear_desc(0, &r, 0, a, sizeof(a));
    tu_dma_descriptor_t *d1 = linear_desc(1, &r, 64, b, sizeof(b));
    tu_dma_submit_desc(d0);
    tu_dma_submit_desc(d1);
    tu_dma_tick();
    printf("cross_channel tick=%" PRIu64 " ch0_active=%d ch1_active=%d d0_done=%d d1_done=%d c0=%" PRIu64 " c1=%" PRIu64 "\n",
           g_tu_dma.current_cycle,
           g_tu_dma.channels[0].active != NULL,
           g_tu_dma.channels[1].active != NULL,
           d0->completed, d1->completed,
           d0->cycles_completed, d1->cycles_completed);
    CHECK(d0->completed && d1->completed &&
          d0->cycles_completed == d1->cycles_completed,
          "two channels dispatch in one tick");
    tu_dma_flush_all();
    tu_dma_desc_destroy(d0);
    tu_dma_desc_destroy(d1);
    tu_sram_destroy(&r);
    tu_dma_destroy();

    tu_dma_init_full(true, 1, 2);
    tu_sram_init(&r, 4096, "queue");
    tu_sram_set_bw_modeling(&r, false);
    tu_dma_descriptor_t *q0 = linear_desc(0, &r, 0, a, sizeof(a));
    tu_dma_descriptor_t *q1 = linear_desc(0, &r, 64, b, sizeof(b));
    tu_dma_descriptor_t *q2 = linear_desc(0, &r, 128, a, sizeof(a));
    uint32_t i0 = tu_dma_submit_desc(q0);
    uint32_t i1 = tu_dma_submit_desc(q1);
    uint32_t i2 = tu_dma_submit_desc(q2); /* rejected descriptor is freed by API */
    printf("queue_capacity ids=%u,%u,%u depth=%u submitted=%" PRIu64 "\n",
           i0, i1, i2, g_tu_dma.channels[0].queue_depth,
           g_tu_dma.channels[0].total_submitted);
    CHECK(i0 && i1 && !i2 && g_tu_dma.channels[0].queue_depth == 2,
          "queue admission is fail-closed at max depth");
    tu_dma_flush_all();
    tu_dma_desc_destroy(q0);
    tu_sram_destroy(&r);
    tu_dma_destroy();

    tu_dma_init_full(false, 1, 8);
    tu_sram_init(&r, 4096, "sync-chain");
    tu_sram_set_bw_modeling(&r, false);
    tu_dma_descriptor_t *s0 = linear_desc(0, &r, 0, a, sizeof(a));
    tu_dma_descriptor_t *s1 = linear_desc(0, &r, 64, b, sizeof(b));
    tu_dma_descriptor_t *s2 = linear_desc(0, &r, 128, a, sizeof(a));
    tu_dma_desc_chain(s0, s1);
    tu_dma_desc_chain(s1, s2);
    uint32_t si = tu_dma_submit_desc(s0);
    printf("sync_chain id=%u depth=%u submitted=%" PRIu64 " completed=%" PRIu64 " transfers=%" PRIu64 "\n",
           si, g_tu_dma.channels[0].queue_depth,
           g_tu_dma.channels[0].total_submitted,
           g_tu_dma.channels[0].total_completed,
           g_tu_dma.total_transfers);
    CHECK(si && g_tu_dma.channels[0].queue_depth == UINT32_MAX - 1u &&
          g_tu_dma.channels[0].total_submitted == 1 &&
          g_tu_dma.channels[0].total_completed == 3,
          "sync chain underflows queued-head depth");
    tu_dma_desc_destroy(s0);
    tu_sram_destroy(&r);
    tu_dma_destroy();

    tu_dma_init_full(true, 1, 1);
    tu_sram_init(&r, 4096, "chain");
    tu_sram_set_bw_modeling(&r, false);
    tu_dma_descriptor_t *c0 = linear_desc(0, &r, 0, a, sizeof(a));
    tu_dma_descriptor_t *c1 = linear_desc(0, &r, 64, b, sizeof(b));
    tu_dma_desc_chain(c0, c1);
    uint32_t ci = tu_dma_submit_desc(c0);
    printf("chain_submit id=%u depth=%u head_is_first=%d tail_is_first=%d next_present=%d\n",
           ci, g_tu_dma.channels[0].queue_depth,
           g_tu_dma.channels[0].head == c0,
           g_tu_dma.channels[0].tail == c0,
           c0->next == c1);
    CHECK(ci && g_tu_dma.channels[0].queue_depth == 1 &&
          g_tu_dma.channels[0].tail == c0,
          "chain counts one queued head");
    tu_dma_tick();
    printf("chain_tick1 depth=%u head_is_second=%d active_is_first=%d\n",
           g_tu_dma.channels[0].queue_depth,
           g_tu_dma.channels[0].head == c1,
           g_tu_dma.channels[0].active == c0);
    CHECK(g_tu_dma.channels[0].queue_depth == 0 &&
          g_tu_dma.channels[0].head == c1,
          "queued chain node remains while depth is zero");
    tu_dma_flush_all();
    tu_dma_desc_destroy(c0); /* destroys c1 through next */
    tu_sram_destroy(&r);
    tu_dma_destroy();
}

static void probe_address_ranges(void) {
    printf("\n[address_ranges]\n");
    tu_agen_iterator_t it;
    tu_agen_2d_config_t cfg = {4, 2, 8};
    int rc = tu_agen_iterator_init(&it, TU_AGEN_MODE_STRIDED_2D,
                                   0x100, &cfg);
    uint32_t addrs[8];
    uint32_t count = tu_agen_generate_all(&it, addrs, 8);
    printf("strided2d rc=%d count=%u addrs=", rc, count);
    for (uint32_t i = 0; i < count; i++) printf("%s0x%x", i ? "," : "", addrs[i]);
    printf("\n");
    CHECK(rc == 0 && count == 8 && addrs[2] == 0x120 && addrs[7] == 0x164,
          "strided iterator uses element stride");

    tu_agen_range_t ranges[2];
    memset(ranges, 0, sizeof(ranges));
    uint32_t logical = tu_agen_generate_ranges(&it, ranges, 2);
    printf("range_truncation logical=%u capacity=2 r0={0x%x,%u} r1={0x%x,%u}\n",
           logical, ranges[0].base_addr, ranges[0].total_bytes,
           ranges[1].base_addr, ranges[1].total_bytes);
    CHECK(logical == 4 && ranges[0].total_bytes == 8 && ranges[1].total_bytes == 8,
          "range API returns logical count beyond capacity");

    tu_agen_im2col_t im = {
        .input_h=2, .input_w=2, .input_c=1,
        .kernel_h=3, .kernel_w=3,
        .pad_h=1, .pad_w=1,
        .stride_h=1, .stride_w=1,
        .dilation_h=1, .dilation_w=1,
        .elem_size=4
    };
    uint32_t single = tu_agen_addr_im2col(&im, 0, 0, 0, 0, 0, 0);
    tu_agen_iterator_init(&it, TU_AGEN_MODE_IM2COL, 0, &im);
    uint32_t iter = tu_agen_next(&it);
    printf("im2col_padding single=0x%08x iterator=0x%08x\n", single, iter);
    CHECK(single == UINT32_MAX && iter == 0xFFFFFF00u,
          "im2col padding sentinels differ by API");
}

static void probe_double_buffer_pipeline(void) {
    printf("\n[double_buffer_pipeline]\n");
    tu_dma_init_full(true, 1, 8);
    tu_sram_region_t r;
    tu_sram_init(&r, 4096, "pipeline");
    tu_sram_set_bw_modeling(&r, false);
    tu_sram_enable_double_buffer(&r);
    uint8_t *active0 = tu_sram_get_active_ptr(&r);
    uint8_t *shadow0 = tu_sram_get_shadow_ptr(&r);
    memset(active0, 0x11, 64);
    memset(shadow0, 0x22, 64);
    uint8_t src[64];
    memset(src, 0x7a, sizeof(src));

    tu_pipeline_init(2, NULL);
    tu_dma_descriptor_t *d = linear_desc(0, &r, 0, src, sizeof(src));
    int tid = tu_pipeline_submit_tile(d, NULL, 5, 99, &r);
    printf("before_advance tid=%d stage=%d active=%02x shadow=%02x dst_host_is_shadow=%d\n",
           tid, g_tu_pipeline.slots[0].stage,
           tu_sram_get_active_ptr(&r)[0], tu_sram_get_shadow_ptr(&r)[0],
           d->dst_host == shadow0);
    tu_pipeline_advance();
    printf("after_advance stage=%d pipe_cycle=%" PRIu64 " dma_cycle=%" PRIu64
           " desc_completed=%d desc_cycles_completed=%" PRIu64
           " active=%02x shadow=%02x swapped=%d\n",
           g_tu_pipeline.slots[0].stage,
           g_tu_pipeline.current_cycle, g_tu_dma.current_cycle,
           d->completed, d->cycles_completed,
           tu_sram_get_active_ptr(&r)[0], tu_sram_get_shadow_ptr(&r)[0],
           g_tu_pipeline.slots[0].swapped);
    CHECK(d->dst_host == shadow0 && d->completed &&
          g_tu_pipeline.slots[0].stage == TU_PIPE_STAGE_COMPUTE &&
          d->cycles_completed > g_tu_dma.current_cycle,
          "pipeline advances on executor completion flag");
    CHECK(tu_sram_get_active_ptr(&r)[0] == 0x22 &&
          tu_sram_get_shadow_ptr(&r)[0] == 0x7a,
          "load wrote old active then swap hid new bytes");

    tu_pipeline_sync();
    while (g_tu_dma.channels[0].active && g_tu_dma.current_cycle < 10000)
        tu_dma_tick();
    tu_pipeline_stats_t stats;
    tu_pipeline_get_stats(&stats);
    printf("pipeline_stats tiles=%u load=%" PRIu64 " compute=%" PRIu64
           " seq=%" PRIu64 " piped=%" PRIu64 " speedup=%.6f pipe_cycle=%" PRIu64 "\n",
           stats.total_tiles, stats.total_load_cycles, stats.total_compute_cycles,
           stats.sequential_total, stats.pipelined_total, stats.speedup,
           g_tu_pipeline.current_cycle);
    CHECK(stats.sequential_total == 8 && stats.pipelined_total == 7,
          "single-tile totals use separate formula fields");

    tu_pipeline_destroy();
    tu_dma_desc_destroy(d);
    tu_sram_destroy(&r);
    tu_dma_destroy();
}

static void probe_counter_domains(void) {
    printf("\n[counter_domains]\n");
    tu_init();
    uint8_t src[64];
    memset(src, 0xcc, sizeof(src));
    uint64_t ge0 = g_tu_dma.estimated_cycles;
    uint64_t ee0 = g_tu.estimated_cycles;
    uint64_t emb0 = g_tu.dma.estimated_cycles;
    tu_dma_load_w(src, 0, sizeof(src));
    printf("direct_load global_dma_delta=%" PRIu64 " embedded_dma_delta=%" PRIu64
           " tu_estimated_delta=%" PRIu64 " tu_bytes=%" PRIu64 "\n",
           g_tu_dma.estimated_cycles - ge0,
           g_tu.dma.estimated_cycles - emb0,
           g_tu.estimated_cycles - ee0,
           g_tu.total_dma_bytes);
    CHECK(g_tu_dma.estimated_cycles > ge0 &&
          g_tu.dma.estimated_cycles == emb0 &&
          g_tu.estimated_cycles == ee0,
          "direct wrapper samples inactive embedded DMA state");
}

int main(void) {
    probe_async_visibility();
    probe_channel_and_queue_state();
    probe_address_ranges();
    probe_double_buffer_pipeline();
    probe_counter_domains();
    printf("\nSUMMARY failures=%d\n", failures);
    return failures ? 1 : 0;
}
