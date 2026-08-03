/* Chapter 5 ownership/lifecycle probe for Tusim snapshot e918c80.
 * Build this only against an isolated archive of the pinned source tree. */
#include "tu_cmodel/tu_cmodel.h"
#include "tu_cmodel/tu_core.h"
#include "tu_cmodel/dma_descriptor.h"
#include "tu_cmodel/tu_status.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int failures = 0;
#define CHECK(cond, msg) do { if (!(cond)) { fprintf(stderr, "FAIL: %s\n", msg); failures++; } } while (0)

int main(void) {
    tu_runtime_config_t cfg = tu_runtime_config_default();

    /* Global reinitialization replaces the queue but has no public shutdown path. */
    tu_init_with_config(&cfg);
    tu_command_queue_t *first_q = g_tu.cmdq;
    tu_init_with_config(&cfg);
    tu_command_queue_t *second_q = g_tu.cmdq;
    printf("global_reinit: first_cmdq=%p second_cmdq=%p replaced=%s initialized=%s\n",
           (void *)first_q, (void *)second_q,
           first_q != second_q ? "true" : "false",
           g_tu.initialized ? "true" : "false");
    CHECK(first_q != NULL && second_q != NULL, "global init must allocate queues");
    CHECK(first_q != second_q, "reinit should expose replacement queue in this run");

    /* A standalone asynchronous queue completes commands but never retires count. */
    tu_command_queue_t *async_q = tu_cmdq_create(4, false);
    uint32_t id = 0;
    int submit_rc = tu_cmdq_submit(async_q, TU_CMD_NOP, NULL, 0, NULL, &id);
    tu_cmd_status_t status = tu_cmdq_get_status(async_q, id);
    uint32_t depth_after_completed = tu_cmdq_get_depth(async_q);
    printf("async_queue: submit_rc=%d id=%u status=%d depth_after_completed=%u\n",
           submit_rc, id, (int)status, depth_after_completed);
    CHECK(submit_rc > 0 && status == TU_CMD_COMPLETED,
          "async NOP should complete after submit auto-tick");
    CHECK(depth_after_completed == 1,
          "probe expects completed command to remain counted in pinned implementation");
    tu_cmdq_destroy(async_q);

    /* Core SRAM/counters are copied per instance, but DMA execution is process-global. */
    tu_core_t *c1 = tu_core_create_with_id(1, &cfg);
    tu_core_t *c2 = tu_core_create_with_id(2, &cfg);
    CHECK(c1 && c2, "core creation failed");
    printf("global_after_core_create: initialized=%s cmdq=%p\n",
           g_tu.initialized ? "true" : "false", (void *)g_tu.cmdq);
    CHECK(!g_tu.initialized && g_tu.cmdq == NULL,
          "core creation is expected to clear the legacy global state at this commit");
    fp16_t one = tu_fp32_to_fp16(1.0f);
    uint64_t global_dma_before = g_tu_dma.total_bytes;
    tu_core_dma_load_w(c1, &one, 0, sizeof(one));
    uint64_t global_dma_mid = g_tu_dma.total_bytes;
    tu_core_dma_load_w(c2, &one, 0, sizeof(one));
    uint64_t global_dma_after = g_tu_dma.total_bytes;
    printf("core_ownership: separate_sram=%s c1_state_bytes=%lu c2_state_bytes=%lu "
           "c1_embedded_dma_bytes=%lu c2_embedded_dma_bytes=%lu global_dma_delta=%lu/%lu\n",
           c1->state.sram_w.banks.data != c2->state.sram_w.banks.data ? "true" : "false",
           (unsigned long)c1->state.total_dma_bytes,
           (unsigned long)c2->state.total_dma_bytes,
           (unsigned long)c1->state.dma.total_bytes,
           (unsigned long)c2->state.dma.total_bytes,
           (unsigned long)(global_dma_mid - global_dma_before),
           (unsigned long)(global_dma_after - global_dma_before));
    CHECK(c1->state.sram_w.banks.data != c2->state.sram_w.banks.data,
          "core SRAM must be distinct");
    CHECK(c1->state.total_dma_bytes == sizeof(one) && c2->state.total_dma_bytes == sizeof(one),
          "per-core wrapper byte counters should be copied back");
    CHECK(c1->state.dma.total_bytes == 0 && c2->state.dma.total_bytes == 0,
          "embedded DMA snapshots are expected to remain dormant at this commit");
    CHECK(global_dma_after - global_dma_before == 2 * sizeof(one),
          "both core transfers should hit the process-global DMA engine");

    /* Core ASM wraps the global interpreter, whose tu_run_asm() calls tu_init(). */
    tu_runtime_config_t custom = cfg;
    custom.pe_rows = 4;
    custom.pe_cols = 8;
    tu_core_t *asm_core = tu_core_create_with_id(3, &custom);
    CHECK(asm_core, "ASM core creation failed");
    uint8_t marker = 0x5a;
    tu_sram_write_bulk(&asm_core->state.sram_w, 0, &marker, 1);
    int asm_rc = tu_core_execute_asm_text(asm_core, "", NULL, 0);
    uint8_t marker_after = 0xff;
    tu_sram_read_bulk(&asm_core->state.sram_w, 0, &marker_after, 1);
    printf("core_asm_lifecycle: rc=%d pe_before=4x8 pe_after=%ux%u marker_after=0x%02x\n",
           asm_rc, asm_core->state.rt_cfg.pe_rows, asm_core->state.rt_cfg.pe_cols,
           marker_after);
    CHECK(asm_rc == 0, "empty ASM program should parse");
    CHECK(asm_core->state.rt_cfg.pe_rows == cfg.pe_rows &&
          asm_core->state.rt_cfg.pe_cols == cfg.pe_cols,
          "core ASM is expected to reset to global defaults at this commit");
    CHECK(marker_after == 0, "core ASM is expected to replace/zero SRAM state");

    /* Void error paths record status but cannot prevent wrapper accounting. */
    tu_init();
    tu_clear_error();
    uint64_t bytes_before = g_tu.total_dma_bytes;
    uint32_t oversized = g_tu.sram_w.total_size + 1;
    tu_dma_load_w(&one, 0, oversized);
    const tu_error_t *err = tu_get_last_error();
    uint64_t accounted = g_tu.total_dma_bytes - bytes_before;
    printf("void_error_path: last_error=%d accounted_bytes=%lu requested_bytes=%u\n",
           err ? (int)err->code : -1, (unsigned long)accounted, oversized);
    CHECK(err && err->code == TU_ERR_DMA_OVERFLOW,
          "nested DMA bounds failure should leave DMA overflow as last error");
    CHECK(accounted == oversized,
          "wrapper is expected to account rejected bytes at this commit");

    tu_core_destroy(c1);
    tu_core_destroy(c2);
    tu_core_destroy(asm_core);

    printf("probe: %s\n", failures ? "FAIL" : "PASS");
    return failures ? 1 : 0;
}
