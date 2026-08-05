#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "tu_cmodel/tu_sram.h"
#include "tu_cmodel/memory/double_buffer.h"
#include "tu_cmodel/dma_descriptor.h"
#include "tu_cmodel/compute/pipeline_controller.h"

static int failures = 0;
#define CHECK(c, msg) do { if (!(c)) { printf("CHECK_FAIL %s\n", msg); failures++; } } while (0)

static tu_dma_descriptor_t *linear_desc(tu_sram_region_t *r, void *host, uint32_t bytes) {
    return tu_dma_desc_create_linear(0, TU_DMA_DIR_HOST_TO_TU, r, 0, host, 1, bytes);
}

static void standalone_state(void) {
    tu_sram_region_t r;
    tu_sram_init(&r, 64, "db-probe");
    tu_sram_set_bw_modeling(&r, false);
    CHECK(tu_sram_enable_double_buffer(&r) == 0, "enable");
    uint8_t *primary = r.banks.data;
    uint8_t *shadow_alloc = r.db->shadow_data;
    memset(primary, 0x11, 64);
    printf("DB_INIT active_idx=%u active=%02x shadow=%02x dirty=%d swaps=%" PRIu64 " size=%u\n",
           r.db->active_idx, tu_sram_get_active_ptr(&r)[0],
           tu_sram_get_shadow_ptr(&r)[0], tu_sram_is_shadow_dirty(&r),
           r.db->swap_count, r.db->buffer_size);

    uint64_t c1 = tu_sram_swap_buffers(&r);
    printf("DB_CLEAN_SWAP count=%" PRIu64 " active_idx=%u active=%02x shadow=%02x dirty=%d\n",
           c1, r.db->active_idx, tu_sram_get_active_ptr(&r)[0],
           tu_sram_get_shadow_ptr(&r)[0], tu_sram_is_shadow_dirty(&r));
    CHECK(tu_sram_get_active_ptr(&r) == shadow_alloc && tu_sram_get_active_ptr(&r)[0] == 0,
          "clean swap makes zero shadow active");

    memset(tu_sram_get_shadow_ptr(&r), 0x33, 16);
    tu_sram_notify_shadow_write(&r, 16, 5);
    uint64_t c2 = tu_sram_swap_buffers(&r);
    tu_db_stats_t s;
    tu_sram_get_db_stats(&r, &s);
    printf("DB_WRITTEN_SWAP count=%" PRIu64 " active_idx=%u active=%02x shadow=%02x dirty=%d bytes=%" PRIu64 " dma_cycles=%" PRIu64 "\n",
           c2, r.db->active_idx, tu_sram_get_active_ptr(&r)[0],
           tu_sram_get_shadow_ptr(&r)[0], tu_sram_is_shadow_dirty(&r),
           s.dma_to_shadow_bytes, s.dma_to_shadow_cycles);
    CHECK(tu_sram_get_active_ptr(&r) == primary && tu_sram_get_active_ptr(&r)[0] == 0x33,
          "written old primary active after second swap");

    uint8_t before = tu_sram_get_shadow_ptr(&r)[0];
    tu_sram_notify_shadow_write(&r, 1000, 77);
    printf("DB_NOTIFY_ONLY shadow_before=%02x shadow_after=%02x dirty=%d bytes=%" PRIu64 " dma_cycles=%" PRIu64 "\n",
           before, tu_sram_get_shadow_ptr(&r)[0], tu_sram_is_shadow_dirty(&r),
           r.db->dma_to_shadow_bytes, r.db->dma_to_shadow_cycles);
    CHECK(before == tu_sram_get_shadow_ptr(&r)[0], "notify has no byte effect");
    CHECK(r.db->dma_to_shadow_bytes == 1016, "notify accepts oversized byte count");
    tu_sram_destroy(&r);
}

static void shared_bank_meter(void) {
    tu_sram_region_t r;
    tu_sram_init(&r, 128, "meter");
    CHECK(tu_sram_enable_double_buffer(&r) == 0, "meter enable");
    uint32_t v = 0x12345678, out = 0;
    uint64_t first = tu_sram_write(&r, 0, &v);
    tu_sram_swap_buffers(&r);
    uint64_t second = tu_sram_read(&r, 0, &out);
    printf("DB_SHARED_METER first=%" PRIu64 " second=%" PRIu64 " active_value=%08x bank0_words=%d\n",
           first, second, out, r.banks.bw_banks[0].words_available);
    CHECK(first == 0 && second == TU_SRAM_BW_STALL_PENALTY,
          "roles share bank budget");
    tu_sram_destroy(&r);
}

static void disable_preserves_active(void) {
    tu_sram_region_t r;
    tu_sram_init(&r, 64, "disable");
    tu_sram_set_bw_modeling(&r, false);
    CHECK(tu_sram_enable_double_buffer(&r) == 0, "disable enable");
    memset(r.banks.data, 0x11, 64);
    memset(r.db->shadow_data, 0x44, 64);
    tu_sram_swap_buffers(&r);
    tu_sram_disable_double_buffer(&r);
    printf("DB_DISABLE enabled=%d primary=%02x db_null=%d\n",
           tu_sram_is_double_buffered(&r), r.banks.data[0], r.db == NULL);
    CHECK(r.banks.data[0] == 0x44 && r.db == NULL, "disable copies active shadow");
    tu_sram_destroy(&r);
}

static void pipeline_bridge(void) {
    tu_dma_init_full(true, 1, 8);
    tu_sram_region_t r;
    tu_sram_init(&r, 4096, "pipeline");
    tu_sram_set_bw_modeling(&r, false);
    CHECK(tu_sram_enable_double_buffer(&r) == 0, "pipeline enable");
    uint8_t *active0 = tu_sram_get_active_ptr(&r);
    uint8_t *shadow0 = tu_sram_get_shadow_ptr(&r);
    memset(active0, 0x11, 64);
    memset(shadow0, 0x22, 64);
    uint8_t src[64];
    memset(src, 0x7a, sizeof(src));

    tu_pipeline_init(2, NULL);
    tu_dma_descriptor_t *d = linear_desc(&r, src, sizeof(src));
    int tid = tu_pipeline_submit_tile(d, NULL, 5, 99, &r);
    printf("PIPE_BEFORE tid=%d stage=%d active=%02x shadow=%02x dst_region=%d dst_host_shadow=%d pipe_cycle=%" PRIu64 " dma_cycle=%" PRIu64 "\n",
           tid, g_tu_pipeline.slots[0].stage, active0[0], shadow0[0],
           d->dst_region == &r, d->dst_host == shadow0,
           g_tu_pipeline.current_cycle, g_tu_dma.current_cycle);
    tu_pipeline_advance();
    printf("PIPE_AFTER stage=%d completed=%d desc_cycles=%" PRIu64 " pipe_cycle=%" PRIu64 " dma_cycle=%" PRIu64 " active=%02x shadow=%02x swapped=%d dirty=%d\n",
           g_tu_pipeline.slots[0].stage, d->completed, d->cycles_completed,
           g_tu_pipeline.current_cycle, g_tu_dma.current_cycle,
           tu_sram_get_active_ptr(&r)[0], tu_sram_get_shadow_ptr(&r)[0],
           g_tu_pipeline.slots[0].swapped, tu_sram_is_shadow_dirty(&r));
    CHECK(d->dst_region == &r && d->dst_host == shadow0, "both destinations retained");
    CHECK(tu_sram_get_active_ptr(&r)[0] == 0x22 && tu_sram_get_shadow_ptr(&r)[0] == 0x7a,
          "descriptor wrote active then swap exposed stale shadow");
    CHECK(tu_sram_is_shadow_dirty(&r), "post-swap notify marks old active shadow dirty");

    tu_pipeline_sync();
    tu_pipeline_stats_t ps;
    tu_pipeline_get_stats(&ps);
    printf("PIPE_LEDGER tiles=%u load=%" PRIu64 " compute=%" PRIu64 " seq=%" PRIu64 " piped=%" PRIu64 " saved=%" PRIu64 " speedup=%.6f pipe_cycle=%" PRIu64 "\n",
           ps.total_tiles, ps.total_load_cycles, ps.total_compute_cycles,
           ps.sequential_total, ps.pipelined_total, tu_pipeline_get_saved_cycles(),
           ps.speedup, g_tu_pipeline.current_cycle);
    CHECK(ps.sequential_total == 8 && ps.pipelined_total == 7 && ps.total_tiles == 1,
          "single tile ledger");

    tu_pipeline_destroy();
    tu_dma_desc_destroy(d);
    tu_sram_destroy(&r);
    tu_dma_destroy();
}

static void reset_contract(void) {
    tu_pipeline_init(2, NULL);
    tu_pipeline_reset();
    printf("PIPE_RESET initialized=%d depth=%u slots_null=%d free_slots=%d\n",
           g_tu_pipeline.initialized, g_tu_pipeline.depth,
           g_tu_pipeline.slots == NULL, tu_pipeline_free_slots());
    CHECK(!g_tu_pipeline.initialized && g_tu_pipeline.depth == 2 &&
          g_tu_pipeline.slots == NULL && tu_pipeline_free_slots() == 1,
          "reset destroys without reinit");
    int tid = tu_pipeline_submit_tile(NULL, NULL, 1, 123, NULL);
    printf("PIPE_AFTER_RESET_SUBMIT tid=%d depth=%u initialized=%d stored_cmd=%u\n",
           tid, g_tu_pipeline.depth, g_tu_pipeline.initialized,
           g_tu_pipeline.slots[0].cmd_id);
    CHECK(tid == 0 && g_tu_pipeline.depth == 1 && g_tu_pipeline.slots[0].cmd_id == 123,
          "submit auto-inits depth one and stores cmd only");
    tu_pipeline_destroy();
}

int main(void) {
    standalone_state();
    shared_bank_meter();
    disable_preserves_active();
    pipeline_bridge();
    reset_contract();
    printf("CH16_PROBE SUMMARY failures=%d\n", failures);
    return failures ? 1 : 0;
}
