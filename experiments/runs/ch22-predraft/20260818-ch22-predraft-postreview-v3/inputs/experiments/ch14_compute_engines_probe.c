/*
 * Chapter 14 — Operator Compute Engines probe (edition pin e918c80).
 *
 * Prints KEY=value findings for the six operator engines + pipeline
 * controller. Every printed value is hand-derived from the pinned source
 * equations (see notes/chapter-14-source-and-claim-ledger.md); the canonical
 * runner greps each line verbatim, so a drifted value fails the run.
 *
 * Sections: CONV, SOFTMAX, NORM, EW, POOL, ATTN (composition + defect),
 * PIPE (controller state machine).
 */
#include "tu_cmodel/tu_config.h"
#include "tu_cmodel/tu_sram.h"
#include "tu_cmodel/tu_cmodel.h"
#include "tu_cmodel/tu_precision.h"
#include "tu_cmodel/compute/convolution_engine.h"
#include "tu_cmodel/compute/softmax_engine.h"
#include "tu_cmodel/compute/normalization_engine.h"
#include "tu_cmodel/compute/pooling_engine.h"
#include "tu_cmodel/compute/elementwise_pipeline.h"
#include "tu_cmodel/compute/attention_engine.h"
#include "tu_cmodel/compute/pipeline_controller.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

static int g_failures = 0;
#define CHECK(cond, msg) do { if (!(cond)) { printf("PROBE FAIL %s\n", msg); g_failures++; } } while (0)

/* Stage FP32 input WITHOUT consuming the SRAM bandwidth budget (raw pointer),
 * so the returned stall counts reflect the engine equations on fresh banks
 * (see ledger C14.3). Staging via tu_sram_write would pre-exhaust banks and
 * inflate every engine's stall return by 2 per pre-touched bank. */
static void stage_f32(tu_sram_region_t *s, uint32_t off, const float *v, uint32_t n) {
    memcpy(tu_sram_raw_ptr(s) + off, v, n * sizeof(float));
}
static void read_f32(tu_sram_region_t *s, uint32_t off, float *v, uint32_t n) {
    for (uint32_t i = 0; i < n; i++) tu_sram_read(s, off + i * 4, &v[i]);
}

/* ---- CONV ---- */
static void conv_section(void) {
    tu_conv_desc_t desc = {
        .batch = 1, .in_channels = 3, .in_height = 3, .in_width = 3,
        .out_channels = 2, .kernel_h = 1, .kernel_w = 1,
        .stride_h = 1, .stride_w = 1,
        .pad_t = 0, .pad_b = 0, .pad_l = 0, .pad_r = 0,
        .dilation_h = 1, .dilation_w = 1, .groups = 1,
        .input_format = TU_CONV_FORMAT_NCHW, .has_bias = false,
    };
    int rc = tu_conv_compute_dims(&desc);
    CHECK(rc == 0, "conv compute_dims rc");
    printf("CONV dims oh=%u ow=%u im2col_rows=%u im2col_cols=%u\n",
           desc.out_height, desc.out_width, desc.im2col_rows, desc.im2col_cols);

    float input[27], weight[6], out1[18], out2[18];
    float im2col_buf[32];
    for (int i = 0; i < 27; i++) input[i] = 1.0f;
    for (int i = 0; i < 6; i++) weight[i] = (float)((i % 3) + 1); /* w[k][c]=c+1 */
    tu_conv2d_direct_nchw_fp32(input, weight, NULL, out1, &desc);
    tu_conv2d_im2col_gemm(input, weight, NULL, out2, &desc, im2col_buf, 4);
    printf("CONV direct out00=%.6f out01=%.6f out10=%.6f out11=%.6f\n",
           out1[0], out1[1], out1[9], out1[10]);
    printf("CONV im2col_gemm out00=%.6f out01=%.6f out10=%.6f out11=%.6f\n",
           out2[0], out2[1], out2[9], out2[10]);
    CHECK(fabsf(out1[0] - 6.0f) < 1e-6f && fabsf(out2[0] - 6.0f) < 1e-6f, "conv values");
    uint64_t est = tu_conv_estimate_cycles(&desc, 16, 16);
    printf("CONV estimate_cycles=%llu\n", (unsigned long long)est);
    CHECK(est == 69, "conv estimate 69");
}

/* ---- SOFTMAX ---- */
static void softmax_section(void) {
    tu_sram_region_t s;
    tu_sram_init(&s, 4096, "sm");
    float zeros[4] = {0, 0, 0, 0};
    stage_f32(&s, 0, zeros, 4);
    float mx = -1.0f;
    tu_softmax_desc_t d = {.mode = TU_SOFTMAX_STANDARD, .data_sram = &s,
                           .data_offset = 0, .elem_count = 4, .axis_dim = 0,
                           .mask = NULL, .mask_is_additive = true,
                           .mask_fill = 0.0f, .scale = 0.0f, .in_place = true,
                           .out_offset = 0, .max_out = &mx, .sum_out = NULL};
    uint64_t st = tu_softmax_execute(&d);
    float o[4];
    read_f32(&s, 0, o, 4);
    printf("SOFTMAX zeros %.6f %.6f %.6f %.6f max=%.6f stall=%llu\n",
           o[0], o[1], o[2], o[3], mx, (unsigned long long)st);
    CHECK(fabsf(o[0] - 0.25f) < 1e-6f && fabsf(mx - 0.0f) < 1e-6f && st == 8, "softmax zeros");

    /* census: 40-element row on a FRESH region (bank budget must be fresh:
     * the zeros case above exhausted banks 0..3, which would inflate this) */
    tu_sram_region_t s2;
    tu_sram_init(&s2, 4096, "sm2");
    float c40[40];
    for (int i = 0; i < 40; i++) c40[i] = (float)(i - 20);
    stage_f32(&s2, 0, c40, 40);
    tu_softmax_desc_t d2 = {.mode = TU_SOFTMAX_STANDARD, .data_sram = &s2,
                            .data_offset = 0, .elem_count = 40, .axis_dim = 0,
                            .mask = NULL, .mask_fill = 0.0f, .scale = 0.0f,
                            .in_place = true, .out_offset = 0};
    uint64_t st40 = tu_softmax_execute(&d2);
    printf("SOFTMAX census40 stall=%llu\n", (unsigned long long)st40);
    CHECK(st40 == 96, "softmax census 96");
    tu_sram_destroy(&s2);

    tu_softmax_desc_t bad = {.mode = TU_SOFTMAX_STANDARD, .data_sram = NULL,
                             .data_offset = 0, .elem_count = 4, .axis_dim = 0,
                             .in_place = true};
    uint64_t stbad = tu_softmax_execute(&bad);
    printf("SOFTMAX invalid=%llu\n", (unsigned long long)stbad);
    CHECK(stbad == UINT64_MAX, "softmax invalid");
    tu_sram_destroy(&s);
}

/* ---- NORM ---- */
static void norm_section(void) {
    tu_sram_region_t s;
    tu_sram_init(&s, 4096, "nm");
    float ones[4] = {1, 1, 1, 1};
    stage_f32(&s, 0, ones, 4);
    float mean = 0, var = 0;
    tu_norm_desc_t d = {.mode = TU_NORM_LAYER_NORM, .data_sram = &s,
                        .data_offset = 0, .elem_count = 4,
                        .gamma_sram = NULL, .beta_sram = NULL,
                        .epsilon = 1e-5f, .norm_axis_dim = 0,
                        .in_place = true, .out_offset = 0,
                        .mean_out = &mean, .var_out = &var};
    uint64_t st = tu_norm_execute(&d);
    float o[4];
    read_f32(&s, 0, o, 4);
    printf("NORM layernorm %.6f %.6f %.6f %.6f mean=%.6f var=%.6f stall=%llu\n",
           o[0], o[1], o[2], o[3], mean, var, (unsigned long long)st);
    CHECK(fabsf(o[0]) < 1e-6f && fabsf(mean - 1.0f) < 1e-6f && fabsf(var) < 1e-9f && st == 8,
          "norm layernorm");

    stage_f32(&s, 0, ones, 4);
    var = 0;
    tu_norm_desc_t d2 = {.mode = TU_NORM_RMS_NORM, .data_sram = &s,
                         .data_offset = 0, .elem_count = 4,
                         .gamma_sram = NULL, .beta_sram = NULL,
                         .epsilon = 1e-5f, .norm_axis_dim = 0,
                         .in_place = true, .out_offset = 0,
                         .mean_out = NULL, .var_out = &var};
    uint64_t st2 = tu_norm_execute(&d2);
    read_f32(&s, 0, o, 4);
    printf("NORM rmsnorm %.6f %.6f %.6f %.6f var=%.6f stall=%llu\n",
           o[0], o[1], o[2], o[3], var, (unsigned long long)st2);
    CHECK(fabsf(o[0] - 0.999995f) < 1e-6f && fabsf(var - 1.0f) < 1e-6f && st2 == 8,
          "norm rmsnorm");

    float c40[40];
    for (int i = 0; i < 40; i++) c40[i] = (float)(i - 20);
    stage_f32(&s, 0, c40, 40);
    tu_norm_desc_t d3 = {.mode = TU_NORM_LAYER_NORM, .data_sram = &s,
                         .data_offset = 0, .elem_count = 40,
                         .epsilon = 1e-5f, .norm_axis_dim = 0,
                         .in_place = true, .out_offset = 0};
    uint64_t st40 = tu_norm_execute(&d3);
    printf("NORM census40 stall=%llu\n", (unsigned long long)st40);
    CHECK(st40 == 80, "norm census 80");
    tu_sram_destroy(&s);
}

/* ---- ELEMENTWISE ---- */
static void ew_section(void) {
    tu_sram_region_t s;
    tu_sram_init(&s, 4096, "ew");
    float in[3] = {-3, 1, 5};
    stage_f32(&s, 0, in, 3);
    tu_ew_desc_t d = {.sram_region = &s, .sram_offset = 0, .elem_count = 3,
                      .in_place = true, .out_offset = 0, .num_ops = 2};
    d.ops[0].opcode = TU_EW_ADD; d.ops[0].has_scalar = true; d.ops[0].scalar = 2.0f;
    d.ops[1].opcode = TU_EW_RELU; d.ops[1].has_scalar = false;
    uint64_t st = tu_ew_execute(&d);
    float o[3];
    read_f32(&s, 0, o, 3);
    printf("EW chain %.6f %.6f %.6f stall=%llu\n", o[0], o[1], o[2],
           (unsigned long long)st);
    CHECK(fabsf(o[0]) < 1e-6f && fabsf(o[1] - 3.0f) < 1e-6f && fabsf(o[2] - 7.0f) < 1e-6f
          && st == 2, "ew chain");

    float c40[40];
    for (int i = 0; i < 40; i++) c40[i] = (float)(i - 20);
    stage_f32(&s, 0, c40, 40);
    tu_ew_desc_t d2 = {.sram_region = &s, .sram_offset = 0, .elem_count = 40,
                       .in_place = true, .out_offset = 0, .num_ops = 1};
    d2.ops[0].opcode = TU_EW_NEG; d2.ops[0].has_scalar = false;
    uint64_t st40 = tu_ew_execute(&d2);
    printf("EW census40 stall=%llu\n", (unsigned long long)st40);
    CHECK(st40 == 40, "ew census 40");
    tu_sram_destroy(&s);
}

/* ---- POOL ---- */
static void pool_section(void) {
    tu_sram_region_t src, dst;
    tu_sram_init(&src, 4096, "ps");
    tu_sram_init(&dst, 4096, "pd");
    float in[16];
    for (int i = 0; i < 16; i++) in[i] = (float)(i + 1);
    for (int i = 0; i < 16; i++) tu_sram_write(&src, i * 4, &in[i]);

    tu_pool_desc_t m = {.pool_type = TU_POOL_MAX, .batch = 1, .channels = 1,
                        .ih = 4, .iw = 4, .kh = 2, .kw = 2, .sh = 2, .sw = 2,
                        .ph = 0, .pw = 0, .elem_size = 4, .is_float = true,
                        .src_region = &src, .src_offset = 0,
                        .dst_region = &dst, .dst_offset = 0};
    int64_t rc = tu_pool_execute(&m);
    float o[4];
    for (int i = 0; i < 4; i++) tu_sram_read(&dst, i * 4, &o[i]);
    printf("POOL max %.6f %.6f %.6f %.6f cycles=%lld\n",
           o[0], o[1], o[2], o[3], (long long)rc);
    CHECK(o[0] == 6.0f && o[1] == 8.0f && o[2] == 14.0f && o[3] == 16.0f && rc == 18,
          "pool max");

    tu_pool_desc_t a = m;
    a.pool_type = TU_POOL_AVG;
    rc = tu_pool_execute(&a);
    for (int i = 0; i < 4; i++) tu_sram_read(&dst, i * 4, &o[i]);
    printf("POOL avg %.6f %.6f %.6f %.6f cycles=%lld\n",
           o[0], o[1], o[2], o[3], (long long)rc);
    CHECK(o[0] == 3.5f && o[1] == 5.5f && o[2] == 11.5f && o[3] == 13.5f && rc == 34,
          "pool avg");
    tu_sram_destroy(&src);
    tu_sram_destroy(&dst);
}

/* ---- Attention: composition, stats, defect ---- */

static void softmax_row_ref(float *row, uint32_t n) {
    float m = row[0];
    for (uint32_t i = 1; i < n; i++) if (row[i] > m) m = row[i];
    float s = 0;
    for (uint32_t i = 0; i < n; i++) { row[i] = expf(row[i] - m); s += row[i]; }
    for (uint32_t i = 0; i < n; i++) row[i] /= s;
}
static void golden_attn(const fp16_t *Q, const fp16_t *K, const fp16_t *V,
                        fp16_t *O, uint32_t M, uint32_t N, uint32_t d, float scale) {
    float *S = malloc(M * N * sizeof(float)), *P = malloc(M * N * sizeof(float));
    float *O32 = calloc(M * d, sizeof(float));
    for (uint32_t i = 0; i < M; i++) for (uint32_t j = 0; j < N; j++) {
        float s = 0;
        for (uint32_t k = 0; k < d; k++)
            s += tu_fp16_to_fp32(Q[i * d + k]) * tu_fp16_to_fp32(K[j * d + k]);
        S[i * N + j] = s * scale;
    }
    for (uint32_t i = 0; i < M; i++) { memcpy(P + i * N, S + i * N, N * 4); softmax_row_ref(P + i * N, N); }
    for (uint32_t i = 0; i < M; i++) for (uint32_t j = 0; j < d; j++)
        for (uint32_t k = 0; k < N; k++)
            O32[i * d + j] += P[i * N + k] * tu_fp16_to_fp32(V[k * d + j]);
    for (uint32_t i = 0; i < M * d; i++) O[i] = tu_fp32_to_fp16(O32[i]);
    free(S); free(P); free(O32);
}
static void fill_rand(fp16_t *b, uint32_t n, uint32_t a, uint32_t c) {
    for (uint32_t i = 0; i < n; i++)
        b[i] = tu_fp32_to_fp16(((i * a + c) % 100) / 100.0f - 0.5f);
}
static float maxerr_fp16(const fp16_t *x, const fp16_t *y, uint32_t n) {
    float e = 0;
    for (uint32_t i = 0; i < n; i++) {
        float d = fabsf(tu_fp16_to_fp32(x[i]) - tu_fp16_to_fp32(y[i]));
        if (d > e) e = d;
    }
    return e;
}

static void attn_section(void) {
    /* (a) tiny correct case: M=1,N=1,d=2 */
    tu_init();
    fp16_t Q[2] = {tu_fp32_to_fp16(1.0f), tu_fp32_to_fp16(0.0f)};
    fp16_t K[2] = {tu_fp32_to_fp16(1.0f), tu_fp32_to_fp16(0.0f)};
    fp16_t V[2] = {tu_fp32_to_fp16(0.1f), tu_fp32_to_fp16(0.2f)};
    fp16_t out[2];
    tu_attention_desc_t td = {.Q = Q, .K = K, .V = V, .output = out,
                              .batch_size = 1, .num_heads = 1,
                              .seq_len_q = 1, .seq_len_kv = 1, .head_dim = 2,
                              .softmax_scale = 1.0f, .mask_type = TU_ATTN_MASK_NONE,
                              .mask = NULL, .mask_fill = -1e9f,
                              .tile_m = 0, .tile_n = 0, .dataflow = -1};
    tu_attention_auto_tile(&td);
    tu_attention_stats_t ts = {0};
    int trc = tu_attention_execute(&td, &ts);
    printf("ATTN tiny rc=%d out=%.6f %.6f dma=%llu tiles=%llu flops=%llu "
           "cc=%llu dc=%llu tc=%llu u=%.4f\n", trc,
           tu_fp16_to_fp32(out[0]), tu_fp16_to_fp32(out[1]),
           (unsigned long long)ts.dma_bytes, (unsigned long long)ts.mma_tiles,
           (unsigned long long)ts.mma_flops, (unsigned long long)ts.compute_cycles,
           (unsigned long long)ts.dma_cycles, (unsigned long long)ts.total_cycles,
           ts.utilization);
    CHECK(trc == 0 && fabsf(tu_fp16_to_fp32(out[0]) - 0.1f) < 1e-4f &&
          fabsf(tu_fp16_to_fp32(out[1]) - 0.2f) < 1e-4f &&
          ts.dma_bytes == 16 && ts.mma_tiles == 2 && ts.mma_flops == 8,
          "attn tiny");

    /* (b) isolated fp32->fp16 in-place conversion defect */
    tu_sram_region_t s;
    tu_sram_init(&s, 1024, "conv");
    float data[6] = {1, 2, 3, 4, 5, 6};
    for (int i = 0; i < 6; i++) tu_sram_write(&s, i * 4, &data[i]);
    uint64_t cstall = 0;
    for (uint32_t i = 1; i <= 6; i++) {
        uint32_t idx = 6 - i;
        fp32_t val;
        cstall += tu_sram_read(&s, idx * 4, &val);
        fp16_t h = tu_fp32_to_fp16(val);
        cstall += tu_sram_write(&s, idx * 2, &h);
    }
    float after[6];
    fp16_t hbuf[6];
    for (int i = 0; i < 6; i++) tu_sram_read(&s, i * 2, &hbuf[i]);
    for (int i = 0; i < 6; i++) after[i] = tu_fp16_to_fp32(hbuf[i]);
    printf("ATTN corrupt %.6f %.6f %.6f %.6f %.6f %.6f\n",
           after[0], after[1], after[2], after[3], after[4], after[5]);
    CHECK(after[0] == 0.0f && after[1] == 0.0f && after[2] == 0.0f &&
          after[3] == 0.0f && after[4] == 0.0f && after[5] == 0.0f,
          "attn corrupt zeroed");
    tu_sram_destroy(&s);

    /* (c) differential: scale-test workload vs golden, and scales equality */
    uint32_t M = 2, N = 3, d = 8;
    fp16_t *q = malloc(M * d * 2), *k = malloc(N * d * 2), *v = malloc(N * d * 2);
    fp16_t *o1 = malloc(M * d * 2), *o2 = malloc(M * d * 2), *g = malloc(M * d * 2);
    fill_rand(q, M * d, 7, 3); fill_rand(k, N * d, 13, 5);
    for (uint32_t j = 0; j < d; j++) {
        v[0 * d + j] = tu_fp32_to_fp16(0.1f);
        v[1 * d + j] = tu_fp32_to_fp16(0.5f);
        v[2 * d + j] = tu_fp32_to_fp16(0.9f);
    }
    tu_attention_simple(q, k, v, o1, M, N, d, 0.5f, false);
    tu_attention_simple(q, k, v, o2, M, N, d, 2.0f, false);
    golden_attn(q, k, v, g, M, N, d, 0.5f);
    float ge = maxerr_fp16(o1, g, M * d);
    float se = maxerr_fp16(o1, o2, M * d);
    /* The corrupted magnitudes are UB-dependent (stack garbage in the 4-byte
     * SRAM copies); only robust properties are gated: deviation from the
     * golden well beyond the suite's 0.25 tolerance, and byte-identical
     * outputs across scales (the failure test_scale records). */
    printf("ATTN diff golden_err=%.3f deviates=1 scales_equal=1\n", ge);
    CHECK(ge > 0.2f && se == 0.0f, "attn corrupts outputs");
    free(q); free(k); free(v); free(o1); free(o2); free(g);
}

/* ---- PIPELINE ---- */
static void pipe_section(void) {
    /* depth 1: sequential baseline, no overlap */
    tu_pipeline_config_t cfg = tu_pipeline_config_default();
    cfg.max_depth = 1;
    tu_pipeline_init(1, &cfg);
    tu_pipeline_submit_tile(NULL, NULL, 100, 1, NULL);
    tu_pipeline_submit_tile(NULL, NULL, 100, 2, NULL);
    int guard = 0;
    while (g_tu_pipeline.active_count > 0 && guard++ < 100000) tu_pipeline_advance();
    tu_pipeline_sync();
    tu_pipeline_stats_t st1;
    tu_pipeline_get_stats(&st1);
    uint64_t saved1 = tu_pipeline_get_saved_cycles();
    printf("PIPE depth1 sequential_total=%llu saved=%llu stalls=%u\n",
           (unsigned long long)st1.sequential_total,
           (unsigned long long)saved1, st1.total_stalls);
    CHECK(st1.sequential_total == 204 && saved1 == 0 && st1.total_stalls == 0,
          "pipe depth1");

    /* depth 2 with load overlap: positive saved cycles requires tiles that
     * carry load descriptors (overlap = load window overlapping another
     * tile's compute; descriptor-free tiles accrue none). Load = 3200 B /
     * 32 B/cycle = 100 cycles, compute = 100. */
    tu_init();
    tu_pipeline_config_t cfg2 = tu_pipeline_config_default();
    cfg2.max_depth = 2;
    cfg2.enable_load_overlap = true;
    cfg2.enable_store_overlap = false;
    cfg2.enable_triple_overlap = false;
    tu_pipeline_init(2, &cfg2);
    uint8_t hostbuf[3200] = {0};
    tu_dma_descriptor_t *ld0 = tu_dma_desc_create_linear(
        1, TU_DMA_DIR_HOST_TO_TU, &g_tu.sram_a, 0, hostbuf, 1, 3200);
    tu_dma_descriptor_t *ld1 = tu_dma_desc_create_linear(
        1, TU_DMA_DIR_HOST_TO_TU, &g_tu.sram_a, 0, hostbuf, 1, 3200);
    tu_pipeline_submit_tile(ld0, NULL, 100, 1, NULL);
    tu_pipeline_submit_tile(ld1, NULL, 100, 2, NULL);
    guard = 0;
    while (g_tu_pipeline.active_count > 0 && guard++ < 100000) tu_pipeline_advance();
    tu_pipeline_stats_t st2;
    tu_pipeline_get_stats(&st2);
    uint64_t saved2 = tu_pipeline_get_saved_cycles();
    printf("PIPE depth2 sequential_total=%llu saved=%llu stalls=%u active=0\n",
           (unsigned long long)st2.sequential_total,
           (unsigned long long)saved2, st2.total_stalls);
    /* Both tile transitions (preload->compute) occur while active_count==2,
     * so the load window (3200 B / 32 = 100 cycles) is credited twice:
     * saved = 200. sequential_total = 2 x (100 load + 100 compute + 1
     * default store) = 402. */
    CHECK(st2.sequential_total == 402 && saved2 == 200 && st2.total_stalls == 0,
          "pipe depth2 saved");
    tu_pipeline_destroy();
}

int main(void) {
    printf("CH14_PROBE start\n");
    conv_section();
    softmax_section();
    norm_section();
    ew_section();
    pool_section();
    attn_section();
    pipe_section();
    printf("CH14_PROBE SUMMARY failures=%d\n", g_failures);
    return g_failures == 0 ? 0 : 1;
}
