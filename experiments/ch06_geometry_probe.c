/* Chapter 6 executable audit for Tusim e918c80.
 * Build against a clean git-archive tree; do not build in the source checkout.
 */
#include "tu_cmodel/tu_cmodel.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    uint64_t tiles;
    uint64_t cycles;
    double slot_util;
} run_result_t;

static int failures = 0;

#define CHECK(cond, fmt, ...) do { \
    if (!(cond)) { fprintf(stderr, "FAIL: " fmt "\n", ##__VA_ARGS__); failures++; } \
} while (0)

static uint64_t ceil_div_u64(uint64_t x, uint64_t y) {
    return (x + y - 1) / y;
}

static run_result_t run_ones(uint16_t M, uint16_t N, uint16_t K,
                             uint16_t rows, uint16_t cols) {
    tu_runtime_config_t cfg = tu_runtime_config_default();
    cfg.pe_rows = rows;
    cfg.pe_cols = cols;
    tu_init_with_config(&cfg);

    size_t wc = (size_t)M * K, ac = (size_t)K * N, oc = (size_t)M * N;
    fp16_t *W = calloc(wc, sizeof(*W));
    fp16_t *A = calloc(ac, sizeof(*A));
    fp32_t *O = calloc(oc, sizeof(*O));
    CHECK(W && A && O, "allocation failed");
    for (size_t i = 0; i < wc; i++) W[i] = fp32_to_fp16(1.0f);
    for (size_t i = 0; i < ac; i++) A[i] = fp32_to_fp16(1.0f);

    tu_dma_load_w(W, 0, (uint32_t)(wc * sizeof(*W)));
    tu_dma_load_a(A, 0, (uint32_t)(ac * sizeof(*A)));
    uint64_t before = g_tu.estimated_cycles;
    tu_mma(M, N, K, 0, 0, 0, false);
    uint64_t delta = g_tu.estimated_cycles - before;
    tu_dma_store_o(O, 0, (uint32_t)(oc * sizeof(*O)));

    for (size_t i = 0; i < oc; i++)
        CHECK(fabsf(O[i] - (float)K) < 1e-5f,
              "ones result[%zu]=%g expected=%u", i, O[i], K);

    uint64_t mt = ceil_div_u64(M, rows);
    uint64_t nt = ceil_div_u64(N, cols);
    uint64_t kt = ceil_div_u64(K, cols);
    uint64_t expected_tiles = mt * nt * kt;
    /* Pinned WS plugin: default pd=2; full configured tile dimensions are
       charged for fill/drain, while sum(k_count) over K tiles is K. */
    uint64_t expected_cycles = mt * nt * (kt * (2 * cols + 2 * rows) + K);
    CHECK(g_tu.total_mma_tiles == expected_tiles,
          "%ux%ux%u on %ux%u: tiles=%lu expected=%lu",
          M, N, K, rows, cols, (unsigned long)g_tu.total_mma_tiles,
          (unsigned long)expected_tiles);
    CHECK(delta == expected_cycles,
          "%ux%ux%u on %ux%u: cycles=%lu expected=%lu",
          M, N, K, rows, cols, (unsigned long)delta,
          (unsigned long)expected_cycles);
    CHECK(g_tu.total_mma_flops == (uint64_t)M * N * K * 2,
          "effective FLOPs mismatch");

    double capacity_macs = (double)expected_tiles * rows * cols * cols;
    run_result_t r = {expected_tiles, delta, ((double)M * N * K) / capacity_macs};
    free(W); free(A); free(O);
    return r;
}

static void test_orientation_accumulation_and_bias(void) {
    const uint16_t M = 2, N = 3, K = 2;
    const float wf[] = {1, 2, 3, 4};
    const float af[] = {5, 6, 7, 8, 9, 10};
    const float product[] = {21, 24, 27, 47, 54, 61};
    fp16_t W[4], A[6], bias[6];
    fp32_t seed[] = {1, 2, 3, 4, 5, 6};
    fp32_t O[6];
    for (int i = 0; i < 4; i++) W[i] = fp32_to_fp16(wf[i]);
    for (int i = 0; i < 6; i++) {
        A[i] = fp32_to_fp16(af[i]);
        bias[i] = fp32_to_fp16(0.5f * (i + 1));
    }

    tu_runtime_config_t cfg = tu_runtime_config_default();
    cfg.pe_rows = 2; cfg.pe_cols = 2;
    tu_init_with_config(&cfg);
    tu_dma_load_w(W, 0, sizeof(W));
    tu_dma_load_a(A, 0, sizeof(A));
    tu_dma_load_o(seed, 0, sizeof(seed));
    tu_mma(M, N, K, 0, 0, 0, false);
    tu_dma_store_o(O, 0, sizeof(O));
    for (int i = 0; i < 6; i++)
        CHECK(fabsf(O[i] - (seed[i] + product[i])) < 1e-5f,
              "O += W*A mismatch at %d: %g", i, O[i]);

    tu_mma(M, N, K, 0, 0, 0, false);
    tu_dma_store_o(O, 0, sizeof(O));
    for (int i = 0; i < 6; i++)
        CHECK(fabsf(O[i] - (seed[i] + 2 * product[i])) < 1e-5f,
              "second accumulation mismatch at %d: %g", i, O[i]);

    tu_init_with_config(&cfg);
    tu_dma_load_w(W, 0, sizeof(W));
    tu_dma_load_a(A, 0, sizeof(A));
    tu_dma_load_o(bias, 0, sizeof(bias));
    tu_mma(M, N, K, 0, 0, 0, true);
    tu_dma_store_o(O, 0, sizeof(O));
    for (int i = 0; i < 6; i++) {
        float expected = product[i] + 0.5f * (i + 1);
        CHECK(fabsf(O[i] - expected) < 1e-5f,
              "packed FP16 bias expansion mismatch at %d: %g expected=%g",
              i, O[i], expected);
    }
    printf("semantics: orientation=O[M,N]+=W[M,K]*A[K,N] accumulation=PASS bias_fp16_expand=PASS\n");
}

static void test_subnormal_plugin_divergence(void) {
    tu_runtime_config_t cfg = tu_runtime_config_default();
    cfg.pe_rows = 1; cfg.pe_cols = 1;
    tu_init_with_config(&cfg);

    fp16_t W = 0x0001; /* smallest positive binary16 subnormal = 2^-24 */
    fp16_t A = fp32_to_fp16(1.0f);
    fp32_t O = 0.0f;
    tu_dma_load_w(&W, 0, sizeof(W));
    tu_dma_load_a(&A, 0, sizeof(A));
    tu_mma(1, 1, 1, 0, 0, 0, false);
    tu_dma_store_o(&O, 0, sizeof(O));

    float canonical = fp16_to_fp32(W);
    float expected = ldexpf(1.0f, -24);
    float wrong_plugin_value = ldexpf(1.0f, -14);
    CHECK(canonical == expected, "canonical subnormal=%g expected=%g", canonical, expected);
    CHECK(O == wrong_plugin_value, "plugin subnormal=%g expected pinned defect=%g", O, wrong_plugin_value);
    printf("subnormal: canonical=%a mma=%a ratio=%.0f defect_reproduced=PASS\n",
           canonical, O, O / canonical);
}

int main(void) {
    test_orientation_accumulation_and_bias();
    test_subnormal_plugin_divergence();

    run_result_t g48 = run_ones(9, 9, 9, 4, 8);
    run_result_t g16 = run_ones(9, 9, 9, 16, 16);
    printf("geometry: mma=9x9x9 pe=4x8 tiles=%lu cycles=%lu util=%.6f\n",
           (unsigned long)g48.tiles, (unsigned long)g48.cycles, g48.slot_util);
    printf("geometry: mma=9x9x9 pe=16x16 tiles=%lu cycles=%lu util=%.6f\n",
           (unsigned long)g16.tiles, (unsigned long)g16.cycles, g16.slot_util);

    run_result_t square = run_ones(4, 32, 16, 8, 8);
    run_result_t wide = run_ones(4, 32, 16, 4, 16);
    printf("aspect: mma=4x32x16 pe=8x8 tiles=%lu cycles=%lu util=%.6f\n",
           (unsigned long)square.tiles, (unsigned long)square.cycles, square.slot_util);
    printf("aspect: mma=4x32x16 pe=4x16 tiles=%lu cycles=%lu util=%.6f\n",
           (unsigned long)wide.tiles, (unsigned long)wide.cycles, wide.slot_util);
    CHECK(wide.slot_util > square.slot_util, "workload-matched aspect ratio should improve slot utilization");

    run_result_t p8 = run_ones(9, 9, 8, 8, 8);
    run_result_t p16 = run_ones(9, 9, 8, 16, 16);
    printf("larger-array: mma=9x9x8 pe=8x8 util=%.6f pe=16x16 util=%.6f\n",
           p8.slot_util, p16.slot_util);
    CHECK(p16.slot_util < p8.slot_util, "larger array should reduce slot utilization for this edge regime");

    run_result_t exact16 = run_ones(16, 16, 16, 16, 16);
    run_result_t exact32 = run_ones(16, 16, 16, 32, 32);
    run_result_t exact64 = run_ones(16, 16, 16, 64, 64);
    printf("underfilled-larger: mma=16x16x16 pe=16x16 cycles=%lu util=%.6f pe=32x32 cycles=%lu util=%.6f pe=64x64 cycles=%lu util=%.6f\n",
           (unsigned long)exact16.cycles, exact16.slot_util,
           (unsigned long)exact32.cycles, exact32.slot_util,
           (unsigned long)exact64.cycles, exact64.slot_util);
    CHECK(exact16.cycles < exact32.cycles && exact32.cycles < exact64.cycles,
          "full-dimension fill/drain should make oversized arrays slower in this pinned regime");

    if (failures) {
        printf("SUMMARY: FAIL (%d checks)\n", failures);
        return 1;
    }
    printf("SUMMARY: PASS\n");
    return 0;
}
