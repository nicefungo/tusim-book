/* Chapter 7 executable WS/OS/RS audit for Tusim e918c80.
 * Build only in an isolated git-archive extraction:
 *   cc -O2 -Wall -Wextra -std=c11 -I. -Itu_cmodel \
 *      -o ch07_dataflow_probe ch07_dataflow_probe.c ./libtucmodel.a -lm
 */
#include "tu_cmodel/tu_cmodel.h"
#include "tu_cmodel/tu_core.h"
#include "tu_cmodel/bindings/tu_dpi.h"
#include "tu_cmodel/infra/config.h"
#include "tu_cmodel/compute/dataflow/dataflow_interface.h"
#include "tu_cmodel/compute/dataflow/dataflow_registry.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ELEMS 2048

static float outputs[3][MAX_ELEMS];

typedef struct {
    uint64_t cycles;
    uint64_t tiles;
    uint64_t flops;
    uint64_t plugin_cycles;
    uint64_t plugin_tiles;
    uint64_t plugin_flops;
} result_t;

static void check(int ok, const char *msg) {
    if (!ok) {
        fprintf(stderr, "FAIL: %s\n", msg);
        exit(1);
    }
}

static uint16_t normal_pattern(unsigned i, unsigned salt) {
    /* Positive and negative normal binary16 values; avoid NaN/Inf/subnormals. */
    static const uint16_t p[] = {
        0x3c00, 0x4000, 0x4200, 0x4400, 0x3800, 0x3a00,
        0xbc00, 0xc000, 0xb800, 0x3400, 0x4500, 0xba00
    };
    return p[(i * 5u + salt * 3u) % (sizeof(p) / sizeof(p[0]))];
}

static result_t run_case(int df, uint16_t M, uint16_t N, uint16_t K,
                         uint16_t rows, uint16_t cols, int subnormal,
                         float *out) {
    tu_runtime_config_t cfg = tu_runtime_config_default();
    cfg.pe_rows = rows;
    cfg.pe_cols = cols;
    tu_init_with_config(&cfg);
    check(tu_set_dataflow(df) == 0, "valid dataflow selection failed");
    check(g_tu.dataflow && g_tu.dataflow->id == (tu_dataflow_id_t)df,
          "active dataflow ID mismatch");

    uint16_t *W = (uint16_t *)tu_sram_raw_ptr(&g_tu.sram_w);
    uint16_t *A = (uint16_t *)tu_sram_raw_ptr(&g_tu.sram_a);
    float *O = (float *)tu_sram_raw_ptr(&g_tu.sram_o);
    check((uint32_t)M * N <= MAX_ELEMS, "output exceeds probe buffer");

    for (uint32_t i = 0; i < (uint32_t)M * K; i++)
        W[i] = subnormal ? 0x0001 : normal_pattern(i, 1);
    for (uint32_t i = 0; i < (uint32_t)K * N; i++)
        A[i] = subnormal ? 0x3c00 : normal_pattern(i, 2);
    memset(O, 0, (size_t)M * N * sizeof(float));

    tu_dataflow_plugin_t *p = g_tu.dataflow;
    uint64_t c0 = g_tu.estimated_cycles;
    uint64_t t0 = g_tu.total_mma_tiles;
    uint64_t f0 = g_tu.total_mma_flops;
    uint64_t pc0 = p->total_cycles;
    uint64_t pt0 = p->total_tiles;
    uint64_t pf0 = p->total_flops;
    tu_mma(M, N, K, 0, 0, 0, false);

    memcpy(out, O, (size_t)M * N * sizeof(float));
    result_t r = {
        g_tu.estimated_cycles - c0,
        g_tu.total_mma_tiles - t0,
        g_tu.total_mma_flops - f0,
        p->total_cycles - pc0,
        p->total_tiles - pt0,
        p->total_flops - pf0,
    };
    return r;
}

static int bit_equal(const float *a, const float *b, size_t n) {
    return memcmp(a, b, n * sizeof(float)) == 0;
}

static uint64_t ceil_div(uint64_t a, uint64_t b) { return (a + b - 1) / b; }

static uint64_t expected_cycles(int df, uint16_t M, uint16_t N, uint16_t K,
                                uint16_t R, uint16_t C) {
    uint64_t mt = ceil_div(M, R), nt = ceil_div(N, C), kt = ceil_div(K, C);
    uint64_t per_spatial = 0;
    for (uint64_t ki = 0; ki < kt; ki++) {
        uint64_t kc = ((ki + 1) * C <= K) ? C : K - ki * C;
        if (df == TU_DATAFLOW_WEIGHT_STATIONARY)
            per_spatial += 2u * C + kc + 2u * R;
        else if (df == TU_DATAFLOW_OUTPUT_STATIONARY)
            per_spatial += kc + ceil_div(kc, 4);
        else
            per_spatial += (uint64_t)C + 1u + kc + R;
    }
    return mt * nt * per_spatial;
}

static void audit_case(const char *name, uint16_t M, uint16_t N, uint16_t K,
                       uint16_t R, uint16_t C) {
    result_t r[3];
    float oracle[MAX_ELEMS] = {0};
    for (uint16_t m = 0; m < M; m++)
        for (uint16_t n = 0; n < N; n++) {
            for (uint16_t ks = 0; ks < K; ks += C) {
                uint16_t kc = (uint16_t)(((uint32_t)ks + C <= K) ? C : K - ks);
                float psum = 0.0f;
                for (uint16_t k = 0; k < kc; k++)
                    psum += fp16_to_fp32(normal_pattern((uint32_t)m * K + ks + k, 1)) *
                            fp16_to_fp32(normal_pattern((uint32_t)(ks + k) * N + n, 2));
                oracle[(uint32_t)m * N + n] += psum;
            }
        }
    for (int df = 0; df < 3; df++)
        r[df] = run_case(df, M, N, K, R, C, 0, outputs[df]);

    size_t n = (size_t)M * N;
    check(bit_equal(outputs[0], outputs[1], n), "WS/OS normal outputs not bit-identical");
    check(bit_equal(outputs[0], outputs[2], n), "WS/RS normal outputs not bit-identical");
    for (int df = 0; df < 3; df++)
        check(bit_equal(outputs[df], oracle, n), "dataflow output differs from canonical normal oracle");
    for (int df = 0; df < 3; df++) {
        uint64_t exp_tiles = ceil_div(M, R) * ceil_div(N, C) * ceil_div(K, C);
        uint64_t exp_flops = 2ull * M * N * K;
        check(r[df].tiles == exp_tiles, "global tile delta mismatch");
        check(r[df].flops == exp_flops, "global FLOP delta mismatch");
        check(r[df].cycles == expected_cycles(df, M, N, K, R, C),
              "global cycle delta mismatch");
        check(r[df].plugin_cycles == r[df].cycles, "plugin/global cycle delta mismatch");
        /* tu_mma consumes and then clears plugin tile/FLOP fields.  They are
         * per-call scratch despite the interface calling them total stats. */
        check(r[df].plugin_tiles == 0, "plugin tile field was not cleared after tu_mma");
        check(r[df].plugin_flops == 0, "plugin FLOP field was not cleared after tu_mma");
    }

    printf("case=%s shape=%ux%ux%u pe=%ux%u tiles=%lu flops=%lu "
           "cycles_ws=%lu cycles_os=%lu cycles_rs=%lu equivalent=PASS oracle=PASS plugin_tile_flop_stats=cleared\n",
           name, M, N, K, R, C, (unsigned long)r[0].tiles,
           (unsigned long)r[0].flops, (unsigned long)r[0].cycles,
           (unsigned long)r[1].cycles, (unsigned long)r[2].cycles);
}

static void audit_subnormal(void) {
    result_t r[3];
    for (int df = 0; df < 3; df++)
        r[df] = run_case(df, 1, 1, 1, 4, 8, 1, outputs[df]);
    float canonical = ldexpf(1.0f, -24);
    float observed = outputs[0][0];
    check(bit_equal(outputs[0], outputs[1], 1) && bit_equal(outputs[0], outputs[2], 1),
          "subnormal defect differs across plugins");
    check(observed == ldexpf(1.0f, -14), "MMA-local subnormal defect not reproduced");
    check(observed / canonical == 1024.0f, "subnormal defect ratio mismatch");
    printf("subnormal canonical=%a ws=%a os=%a rs=%a ratio=%.0f shared_defect=PASS\n",
           canonical, outputs[0][0], outputs[1][0], outputs[2][0],
           (double)(observed / canonical));
    (void)r;
}

static void audit_selection_and_registry(void) {
    tu_runtime_config_t rt = tu_runtime_config_default();
    tu_init_with_config(&rt);
    tu_dataflow_plugin_t *first[3] = {
        tu_dataflow_lookup(TU_DATAFLOW_WEIGHT_STATIONARY),
        tu_dataflow_lookup(TU_DATAFLOW_OUTPUT_STATIONARY),
        tu_dataflow_lookup(TU_DATAFLOW_ROW_STATIONARY)
    };
    check(tu_dataflow_registry_count() == 3, "registry count is not three");
    tu_init_with_config(&rt);
    for (int i = 0; i < 3; i++)
        check(first[i] == tu_dataflow_lookup((tu_dataflow_id_t)i),
              "duplicate registration changed stable plugin address");

    check(tu_set_dataflow(TU_DATAFLOW_NO_LOCAL_REUSE) == 0,
          "unregistered NLR fallback did not return success");
    check(g_tu.dataflow && g_tu.dataflow->id == TU_DATAFLOW_WEIGHT_STATIONARY,
          "unregistered NLR did not fall back to WS");

    const char *json = "{\"tu\":{\"compute\":{\"pe_array\":{"
                       "\"rows\":4,\"cols\":8,\"dataflow\":\"row_stationary\"}}}}";
    tu_config_t cfg = {0};
    char err[256] = {0};
    check(tu_config_load_string(json, &cfg, err, sizeof(err)) == 0,
          "JSON config parse failed");
    check(cfg.dataflow_mode == TU_DATAFLOW_ROW_STATIONARY,
          "JSON did not parse row_stationary");
    check(tu_init_from_config(&cfg) == 0, "init from parsed config failed");
    check(g_tu.dataflow && g_tu.dataflow->id == TU_DATAFLOW_WEIGHT_STATIONARY,
          "expected disconnected config selection to leave WS active");

    tu_config_t bad_cfg = {0};
    const char *bad_json = "{\"tu\":{\"compute\":{\"pe_array\":{"
                           "\"dataflow\":\"row_statoinary\"}}}}";
    check(tu_config_load_string(bad_json, &bad_cfg, err, sizeof(err)) == 0,
          "unknown-name JSON parse failed");
    check(bad_cfg.dataflow_mode == TU_DATAFLOW_WEIGHT_STATIONARY,
          "unknown dataflow name did not silently canonicalize to WS");

    int dpi = tu_dpi_init(4, 8, 256, 3);
    check(dpi > 0, "DPI NLR initialization failed");
    char summary[256] = {0};
    char active[64] = {0};
    check(tu_dpi_get_summary(dpi, summary, sizeof(summary)) == TU_DPI_OK,
          "DPI summary failed");
    check(tu_dpi_get_dataflow_name(dpi, active, sizeof(active)) == TU_DPI_OK,
          "DPI active-name query failed");
    check(strstr(summary, "DF=NLR") != NULL, "DPI summary did not retain requested NLR");
    check(strcmp(active, "weight_stationary") == 0, "DPI NLR did not execute fallback WS");
    check(tu_dpi_destroy(dpi) == TU_DPI_OK, "DPI destroy failed");

    printf("selection registry_count=%d duplicate_addresses=stable "
           "json_requested=row_stationary active_after_init=%s "
           "unknown_name=weight_stationary nlr_fallback=weight_stationary "
           "dpi_summary=NLR dpi_active=weight_stationary\n",
           tu_dataflow_registry_count(), tu_get_dataflow_name());
}

static void audit_core_selection_scope(void) {
    tu_runtime_config_t cfg = tu_runtime_config_default();
    tu_core_t *core = tu_core_create(&cfg);
    check(core != NULL, "core creation failed");

    check(core->state.dataflow &&
          core->state.dataflow->id == TU_DATAFLOW_WEIGHT_STATIONARY,
          "new core did not start in WS");
    check(tu_set_dataflow(TU_DATAFLOW_OUTPUT_STATIONARY) == 0,
          "process-global OS selection failed");
    check(g_tu.dataflow &&
          g_tu.dataflow->id == TU_DATAFLOW_OUTPUT_STATIONARY,
          "process-global selection is not OS");
    check(core->state.dataflow &&
          core->state.dataflow->id == TU_DATAFLOW_WEIGHT_STATIONARY,
          "process-global selection unexpectedly changed core snapshot");
    printf("core_selection process_global=output_stationary core_snapshot=%s "
           "selection_scope=separate\n", core->state.dataflow->name);
    tu_core_destroy(core);
    memset(&g_tu, 0, sizeof(g_tu));
}

int main(void) {
    audit_selection_and_registry();
    audit_core_selection_scope();
    audit_case("nonsymmetric", 2, 3, 2, 4, 8);
    audit_case("edge-k-boundary", 9, 10, 9, 4, 8);
    audit_case("multi-k", 5, 17, 19, 4, 8);
    audit_subnormal();
    printf("SUMMARY: PASS failures=0\n");
    return 0;
}
