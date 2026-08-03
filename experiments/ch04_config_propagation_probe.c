#include "tu_cmodel/tu_cmodel.h"
#include "tu_cmodel/infra/config.h"
#include "tu_cmodel/rounding.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>

static uint64_t run_geometry_case(tu_config_t cfg, uint16_t rows, uint16_t cols) {
    enum { DIM = 9, ELEMS = DIM * DIM };
    fp16_t w[ELEMS];
    fp16_t a[ELEMS];
    fp32_t zero[ELEMS] = {0};

    for (size_t i = 0; i < ELEMS; ++i) {
        w[i] = 0x3c00; /* IEEE binary16 1.0 */
        a[i] = 0x3c00;
    }

    cfg.pe_rows = rows;
    cfg.pe_cols = cols;
    assert(tu_init_from_config(&cfg) == 0);
    (void)tu_sram_write_bulk(&g_tu.sram_w, 0, w, sizeof(w));
    (void)tu_sram_write_bulk(&g_tu.sram_a, 0, a, sizeof(a));
    (void)tu_sram_write_bulk(&g_tu.sram_o, 0, zero, sizeof(zero));
    tu_mma(DIM, DIM, DIM, 0, 0, 0, false);

    const fp32_t *out = (const fp32_t *)tu_sram_raw_ptr(&g_tu.sram_o);
    for (size_t i = 0; i < ELEMS; ++i) assert(out[i] == 9.0f);
    return g_tu.total_mma_tiles;
}

int main(int argc, char **argv) {
    const char *path = argc > 1 ? argv[1] : "experiments/ch04_runtime_request.json";
    char error[256] = {0};
    tu_config_t cfg;

    assert(tu_config_load(path, &cfg, error, sizeof(error)) == 0);

    printf("parsed: pe=%ux%u pipeline=%u macs_per_pe=%u dataflow=%d\n",
           cfg.pe_rows, cfg.pe_cols, cfg.pe_pipeline_depth,
           cfg.mac_units_per_pe, cfg.dataflow_mode);
    printf("parsed: sram_kb=%u/%u/%u banks=%u width=%u\n",
           cfg.sram_w_size_kb, cfg.sram_a_size_kb, cfg.sram_o_size_kb,
           cfg.sram_num_banks, cfg.sram_bank_width);
    printf("parsed: dma_bus=%u queue=%u cycle_model=%d rounding=%d\n",
           cfg.dma_bus_width_bits, cfg.isa_queue_depth,
           cfg.cycle_model, cfg.rounding_mode);

    assert(cfg.pe_rows == 4 && cfg.pe_cols == 8);
    assert(cfg.pe_pipeline_depth == 7 && cfg.mac_units_per_pe == 2);
    assert(cfg.dataflow_mode == TU_DATAFLOW_MODE_OS);
    assert(cfg.sram_w_size_kb == 8 && cfg.sram_a_size_kb == 12 && cfg.sram_o_size_kb == 16);
    assert(cfg.sram_num_banks == 4 && cfg.sram_bank_width == 8);
    assert(cfg.dma_bus_width_bits == 64 && cfg.isa_queue_depth == 3);
    assert(cfg.cycle_model == TU_CYCLE_MODEL_ESTIMATED);
    assert(cfg.rounding_mode == TU_ROUND_RTZ);

    assert(tu_init_from_config(&cfg) == 0);

    printf("active: pe=%ux%u sram_kb=%u/%u/%u dataflow=%s\n",
           g_tu.rt_cfg.pe_rows, g_tu.rt_cfg.pe_cols,
           g_tu.sram_w.total_size / 1024,
           g_tu.sram_a.total_size / 1024,
           g_tu.sram_o.total_size / 1024,
           tu_get_dataflow_name());
    printf("active: banks=%u width=%u queue=%u synchronous=%s rounding=%d\n",
           g_tu.sram_w.banks.bank_count,
           g_tu.sram_w.banks.bank_width,
           g_tu.cmdq->capacity,
           g_tu.cmdq->synchronous ? "true" : "false",
           (int)tu_get_rounding_mode());

    assert(g_tu.rt_cfg.pe_rows == 4 && g_tu.rt_cfg.pe_cols == 8);
    assert(g_tu.sram_w.total_size == 8 * 1024);
    assert(g_tu.sram_a.total_size == 12 * 1024);
    assert(g_tu.sram_o.total_size == 16 * 1024);
    assert(g_tu.sram_w.banks.bank_count == TU_SRAM_BANKS);
    assert(g_tu.sram_w.banks.bank_width == TU_SRAM_BANK_WIDTH);
    assert(g_tu.cmdq->capacity == TU_ISA_QUEUE_DEPTH);
    assert(g_tu.cmdq->synchronous == (TU_CYCLE_MODEL == TU_CYCLE_MODEL_FUNCTIONAL));
    assert(tu_get_rounding_mode() == TU_ROUND_RNE);
    assert(cfg.dataflow_mode == TU_DATAFLOW_MODE_OS);
    assert(tu_get_dataflow_name()[0] == 'w');

    uint8_t bytes[33] = {0};
    tu_dma_load_o(bytes, 0, sizeof(bytes));
    uint64_t after_dma = g_tu.estimated_cycles;
    tu_sync();
    uint64_t after_sync = g_tu.estimated_cycles;

    printf("effect: dma_33B_cycles=%lu requested_64b_expectation=5 compile_256b_expectation=2\n",
           (unsigned long)after_dma);
    printf("effect: sync_delta=%lu requested_pipeline_expectation=56 compile_pipeline_expectation=16\n",
           (unsigned long)(after_sync - after_dma));

    assert(after_dma == 2);
    assert(after_sync - after_dma == (uint64_t)TU_PE_PIPELINE_DEPTH * cfg.pe_cols);

    const char *fallback_json =
        "{\"tu\":{\"compute\":{\"pe_array\":{"
        "\"rows\":0,\"pipeline_depth\":0,\"dataflow\":\"teleport\"}},"
        "\"memory\":{\"dram\":{\"type\":\"magic\"}},"
        "\"performance\":{\"cycle_model\":\"magic\"},"
        "\"precision\":{\"fp16\":{\"rounding\":\"magic\"}},"
        "\"unknown_future_key\":123}}";
    tu_config_t fallback;
    assert(tu_config_load_string(fallback_json, &fallback, error, sizeof(error)) == 0);
    printf("fallback: rows=%u pipeline=%u dataflow=%d dram=%d cycle=%d rounding=%d\n",
           fallback.pe_rows, fallback.pe_pipeline_depth, fallback.dataflow_mode,
           fallback.dram_type, fallback.cycle_model, fallback.rounding_mode);
    assert(fallback.pe_rows == 16);
    assert(fallback.pe_pipeline_depth == 16);
    assert(fallback.dataflow_mode == TU_DATAFLOW_MODE_WS);
    assert(fallback.dram_type == TU_DRAM_IDEAL);
    assert(fallback.cycle_model == TU_CYCLE_MODEL_CYCLE_ACCURATE);
    assert(fallback.rounding_mode == TU_ROUND_RNE);

    uint64_t tiles_4x8 = run_geometry_case(cfg, 4, 8);
    uint64_t tiles_16x16 = run_geometry_case(cfg, 16, 16);
    printf("effect: mma_9x9x9_tiles_4x8=%lu tiles_16x16=%lu outputs_identical=true\n",
           (unsigned long)tiles_4x8, (unsigned long)tiles_16x16);
    assert(tiles_4x8 == 12);
    assert(tiles_16x16 == 1);

    puts("probe: PASS");
    return 0;
}
