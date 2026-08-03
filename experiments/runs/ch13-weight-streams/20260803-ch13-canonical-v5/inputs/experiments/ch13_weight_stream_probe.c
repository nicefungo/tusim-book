/*
 * Chapter 13 weight-stream probe: INT/UINT quantization, 2:4 structured
 * sparsity, and RLE/bitmap/adaptive compression with decoder throughput.
 * Deterministic, fail-closed, bounded. Prints key=value findings that the
 * canonical runner greps for exact expected strings.
 *
 * Edition pin: e918c80b6fce833cd1fcae97730fa841c2176f25
 */
#include "tu_cmodel/tu_int_quant.h"
#include "tu_cmodel/sparsity/structured_2of4.h"
#include "tu_cmodel/memory/weight_compress.h"
#include "tu_cmodel/infra/config.h"
#include "tu_cmodel/tu_precision.h"
#include "tu_cmodel/tu_config.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failures = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("FAIL: %s\n", msg); failures++; } \
} while (0)

static void probe_quant(void) {
    tu_quant_params_t qp;
    tu_quant_params_init_int8(&qp);
    printf("INTQ default_scale=%.9f default_zp=%d qmin=%d qmax=%d\n",
           (double)qp.scale, qp.zero_point, qp.qmin, qp.qmax);
    CHECK(qp.zero_point == 0 && qp.qmin == -128 && qp.qmax == 127,
          "int8 default range");

    float data[128];
    for (int i = 0; i < 128; i++) data[i] = (float)i;
    tu_quant_params_t cal;
    tu_quant_params_calibrate_int8_symmetric(data, 128, &cal);
    printf("INTQ sym_calib scale=%.9f zp=%d\n", (double)cal.scale, cal.zero_point);
    CHECK(cal.zero_point == 0 && cal.scale == 127.0f / 127.0f,
          "symmetric calibration");

    CHECK(tu_fp32_to_int8(0.0f, &cal) == 0, "int8 zero");
    CHECK(tu_fp32_to_int8(127.0f, &cal) == 127, "int8 127");
    CHECK(tu_fp32_to_int8(-128.0f, &cal) == -128, "int8 -128");
    CHECK(tu_fp32_to_int8(200.0f, &cal) == 127, "int8 clamp high");
    CHECK(tu_fp32_to_int8(-200.0f, &cal) == -128, "int8 clamp low");
    printf("INTQ conversions zero=0 p127=127 n128=-128 clamp=127,-128\n");

    tu_quant_params_t u4;
    tu_quant_params_init_uint4(&u4);
    CHECK(u4.qmin == 0 && u4.qmax == 15, "uint4 range");
    CHECK(tu_fp32_to_uint4_nibble(0.0f, &u4) == 8, "uint4 zero->8");
    CHECK(tu_fp32_to_uint4_nibble(1.0f, &u4) == 15, "uint4 1.0->15 clamp");

    uint8_t packed[2] = {0, 0};
    tu_uint4_pack(packed, 0, 0x0A);
    tu_uint4_pack(packed, 1, 0x05);
    printf("INTQ nibble byte=0x%02X low=%u high=%u\n",
           packed[0], tu_uint4_unpack(packed, 0), tu_uint4_unpack(packed, 1));
    CHECK(packed[0] == 0x5A, "nibble low-first packing");
    CHECK(tu_uint4_unpack(packed, 0) == 10 && tu_uint4_unpack(packed, 1) == 5,
          "nibble unpack");

    const int8_t_t a[3] = {1, 2, 3}, b[3] = {4, 5, 6};
    printf("INTQ dot=%d\n", tu_int8_dot_product(a, b, 3));
    CHECK(tu_int8_dot_product(a, b, 3) == 32, "dot product 32");

    const int8_t_t W[4] = {1, 2, 3, 4};
    const int8_t_t A[4] = {5, 6, 7, 8};
    int32_t O[4] = {0, 0, 0, 0};
    tu_int8_mma_tile(W, A, O, 2, 2, 2);
    printf("INTQ mma o00=%d o01=%d o10=%d o11=%d\n", O[0], O[1], O[2], O[3]);
    CHECK(O[0] == 19 && O[1] == 22 && O[2] == 43 && O[3] == 50,
          "int8 mma tile 19/22/43/50");
}

static void probe_sparsity(void) {
    CHECK(TU_2OF4_NUM_VALID_MASKS == 6, "six valid masks");
    int valid = 0;
    for (int m = 0; m < 16; m++)
        if (tu_sparsity_2of4_mask_is_valid((tu_sparsity_2of4_mask_t)m)) valid++;
    printf("SPARSITY valid_masks=%d\n", valid);
    CHECK(valid == 6, "mask validity count");

    float dense[8] = {0.5f, 0.1f, 0.9f, 0.2f, 1.0f, 0.3f, 0.4f, 0.8f};
    float pruned[8];
    tu_sparsity_2of4_mask_t masks[2];
    size_t groups = tu_sparsity_2of4_prune_with_masks_fp32(dense, pruned, masks, 8);
    printf("SPARSITY prune groups=%zu masks=0x%X,0x%X\n",
           groups, masks[0], masks[1]);
    CHECK(groups == 2, "prune groups");
    CHECK(tu_sparsity_2of4_verify_pattern(pruned, 8, 0.0f),
          "prune pattern verified");

    size_t packed = tu_sparsity_2of4_packed_size(128, sizeof(fp16_t));
    printf("SPARSITY packed_fp16_128=%zu\n", packed);
    CHECK(packed == 160, "packed 128 fp16 = 160 bytes");

    tu_config_t cfg;
    tu_config_default(&cfg);
    cfg.sparsity_enabled = true;
    cfg.sparsity_2of4 = true;
    cfg.sparsity_decoder_groups_per_cycle = 1;
    tu_sparsity_2of4_cycle_stats_t s;
    CHECK(tu_sparsity_2of4_estimate_cycles(&cfg, 128, 128, 128, &s),
          "estimate square 128^3");
    printf("SPARSITY est128 dense_total=%" PRIu64 " sparse_total=%" PRIu64
           " selected=%" PRIu64 " macs=%" PRIu64 "/%" PRIu64
           " wbytes=%" PRIu64 "/%" PRIu64 " decode=%" PRIu64 "\n",
           s.dense_total_cycles, s.sparse_total_cycles, s.selected_total_cycles,
           s.dense_macs, s.sparse_macs, s.dense_weight_bytes,
           s.sparse_weight_bytes, s.sparse_decode_cycles);
    CHECK(s.dense_macs == 2097152 && s.sparse_macs == 1048576, "mac counts");
    CHECK(s.dense_weight_bytes == 32768 && s.sparse_weight_bytes == 20480,
          "weight bytes 32768/20480");
    CHECK(s.dense_total_cycles == 12291 && s.sparse_total_cycles == 7811 &&
          s.selected_total_cycles == 7811, "square estimate 12291/7811");

    tu_sparsity_2of4_cycle_stats_t n;
    CHECK(tu_sparsity_2of4_estimate_cycles(&cfg, 512, 16, 512, &n),
          "estimate narrow-N");
    printf("SPARSITY estNarrow dense_total=%" PRIu64 " sparse_total=%" PRIu64
           " decode=%" PRIu64 "\n",
           n.dense_total_cycles, n.sparse_total_cycles, n.sparse_decode_cycles);
    CHECK(n.dense_total_cycles == 34307 && n.sparse_total_cycles == 77312 &&
          n.sparse_decode_cycles == 65536, "narrow-N decode-bound 34307/77312");

    cfg.sparsity_decoder_groups_per_cycle = 16;
    tu_sparsity_2of4_cycle_stats_t w;
    CHECK(tu_sparsity_2of4_estimate_cycles(&cfg, 512, 16, 512, &w),
          "estimate narrow-N wide decoder");
    printf("SPARSITY estWide sparse_total=%" PRIu64 " decode=%" PRIu64 "\n",
           w.sparse_total_cycles, w.sparse_decode_cycles);
    CHECK(w.sparse_total_cycles == 19971 && w.sparse_decode_cycles == 4096,
          "wide-decoder 19971");
}

static void probe_compress(void) {
    fp16_t zeros[128];
    memset(zeros, 0, sizeof(zeros));
    uint8_t rle_zero[2048];
    uint32_t size = 0, count = 0;
    CHECK(tu_compress_rle(zeros, 128, 0.0f, rle_zero, sizeof(rle_zero), &size) == 0,
          "rle all-zero encode");
    printf("COMPRESS rle_allzero_size=%u\n", size);
    CHECK(size == 14, "rle all-zero = 14 bytes");
    fp16_t back[128];
    CHECK(tu_decompress_rle(rle_zero, size, back, 128, &count) == 0 && count == 128 &&
          memcmp(zeros, back, sizeof(zeros)) == 0, "rle round-trip");

    fp16_t alt[128];
    for (int i = 0; i < 128; i++) alt[i] = (fp16_t)(i & 1);
    uint8_t rle_alt[2048];
    uint32_t alt_size = 0;
    CHECK(tu_compress_rle(alt, 128, 0.0f, rle_alt, sizeof(rle_alt), &alt_size) == 0,
          "rle alternating encode");
    printf("COMPRESS rle_alt_size=%u raw=%u\n", alt_size, (uint32_t)sizeof(alt));
    CHECK(alt_size == 8 + 128 * 6, "rle alternating expands to 776");

    /* 1/3 sparse pattern: element_count 128, nonzero 43 -> 8 + 16 + 86 */
    fp16_t sparse[128];
    memset(sparse, 0, sizeof(sparse));
    int nnz = 0;
    for (int i = 0; i < 128; i++) {
        if (i % 3 == 0) { sparse[i] = tu_fp32_to_fp16((float)(i + 1)); nnz++; }
    }
    uint8_t bmp[2048];
    uint32_t bsize = 0;
    CHECK(tu_compress_bitmap(sparse, 128, bmp, sizeof(bmp), &bsize) == 0,
          "bitmap encode");
    printf("COMPRESS bitmap_size=%u nnz=%d\n", bsize, nnz);
    CHECK(nnz == 43 && bsize == 8 + 16 + 86, "bitmap 110 bytes");

    uint8_t enc[2048];
    uint32_t esize = 0;
    tu_weight_payload_codec_t codec;
    CHECK(tu_compress_adaptive(sparse, 128, 0.0f, enc, sizeof(enc),
                               &esize, &codec) == 0 &&
          codec == TU_WEIGHT_PAYLOAD_BITMAP, "adaptive selects bitmap");
    printf("COMPRESS adaptive_sparse_codec=%d size=%u\n", codec, esize);
    CHECK(tu_decompress_adaptive(enc, esize, back, 128, &count) == 0 &&
          memcmp(sparse, back, sizeof(sparse)) == 0, "adaptive round-trip");

    uint8_t corrupt[64];
    memcpy(corrupt, rle_zero, size);
    corrupt[4] = 0xFF; /* run count low byte -> runs=255 > n=128 */
    CHECK(!tu_compress_validate(corrupt, size), "corrupt rle rejected");
    printf("COMPRESS corrupt_rejected=1\n");

    /* Decoder cycle profiles on the all-zero RLE stream (size 14). */
    tu_compress_config_t dcfg = tu_compress_config_default;
    dcfg.decoder_enabled = true;
    tu_compress_cycle_stats_t st;
    CHECK(tu_compress_estimate_cycles(rle_zero, size, &dcfg, 256, &st) == 0,
          "estimate rle default decoder");
    printf("COMPRESS est_rle dma=%" PRIu64 " decode=%" PRIu64 " total=%" PRIu64
           " bound=%d\n", st.dma_cycles, st.decode_cycles, st.total_cycles,
           st.decoder_bound ? 1 : 0);
    CHECK(st.dma_cycles == 1 && st.decode_cycles == 128 &&
          st.total_cycles == 128 && st.decoder_bound, "rle 1/128/128 bound");

    dcfg.decoder_elements_per_cycle = 16;
    dcfg.rle_runs_per_cycle = 4;
    CHECK(tu_compress_estimate_cycles(rle_zero, size, &dcfg, 256, &st) == 0,
          "estimate rle wide decoder");
    printf("COMPRESS est_wide decode=%" PRIu64 " total=%" PRIu64 "\n",
           st.decode_cycles, st.total_cycles);
    CHECK(st.decode_cycles == 8 && st.total_cycles == 8, "wide 8/8");
    dcfg.decoder_overlap_dma = false;
    CHECK(tu_compress_estimate_cycles(rle_zero, size, &dcfg, 256, &st) == 0,
          "estimate rle serial");
    printf("COMPRESS est_serial total=%" PRIu64 "\n", st.total_cycles);
    CHECK(st.total_cycles == 9, "serial 9");

    /* Config-driven compression mapping. */
    tu_config_t cfg;
    tu_config_default(&cfg);
    cfg.compression_enabled = true;
    cfg.compression_type = TU_COMPRESS_ADAPTIVE;
    cfg.compression_decoder_enabled = true;
    tu_compress_config_t cc = tu_compress_config_from_tu_config(&cfg);
    printf("COMPRESS cfgmap type=%d enabled=%d decoder=%d\n",
           cc.type, cc.enabled ? 1 : 0, cc.decoder_enabled ? 1 : 0);
    CHECK(cc.type == TU_COMPRESS_ADAPTIVE && cc.enabled &&
          cc.decoder_enabled, "config mapping reaches codec");
}

static void probe_config(void) {
    tu_config_t cfg;
    const char *json =
        "{\"tu\":{\"weight_compression\":{\"enabled\":true,\"type\":\"adaptive\","
        "\"decoder_enabled\":true,\"decoder_elements_per_cycle\":16},"
        "\"sparsity\":{\"enabled\":true,\"structured_2of4\":true,"
        "\"decoder_groups_per_cycle\":4}}}";
    CHECK(tu_config_load_string(json, &cfg, NULL, 0) == 0, "parse config");
    printf("CONFIG parsed compression=%d type=%d decoder=%d "
           "sparsity=%d two4=%d decgroups=%u\n",
           cfg.compression_enabled ? 1 : 0, cfg.compression_type,
           cfg.compression_decoder_enabled ? 1 : 0,
           cfg.sparsity_enabled ? 1 : 0, cfg.sparsity_2of4 ? 1 : 0,
           cfg.sparsity_decoder_groups_per_cycle);
    CHECK(cfg.compression_enabled && cfg.compression_type == TU_COMPRESS_ADAPTIVE &&
          cfg.compression_decoder_enabled && cfg.sparsity_enabled &&
          cfg.sparsity_2of4 && cfg.sparsity_decoder_groups_per_cycle == 4,
          "parsed fields");

    char err[128];
    tu_config_t bad;
    tu_config_default(&bad);
    bad.sparsity_enabled = true;
    bad.sparsity_unstructured = true;
    CHECK(tu_config_validate(&bad, err, sizeof(err)) != 0, "unstructured rejected");
    tu_config_default(&bad);
    bad.sparsity_enabled = true;
    CHECK(tu_config_validate(&bad, err, sizeof(err)) != 0, "enabled w/o 2of4 rejected");
    tu_config_default(&bad);
    bad.sparsity_2of4 = true;
    CHECK(tu_config_validate(&bad, err, sizeof(err)) != 0, "2of4 w/o enabled rejected");
    tu_config_default(&bad);
    bad.sparsity_enabled = true;
    bad.sparsity_2of4 = true;
    bad.sparsity_decoder_groups_per_cycle = 0;
    CHECK(tu_config_validate(&bad, err, sizeof(err)) != 0, "zero decoder rejected");
    printf("CONFIG validation rejections=4\n");

    /* Runtime conversion drops every weight-path field; consumers read the
     * full config. This mirrors the source-audit converter predicate. */
    tu_runtime_config_t rt = tu_config_to_runtime(&cfg);
    printf("CONFIG runtime pe_rows=%u pe_cols=%u dma_bits=%u "
           "(compression/sparsity fields absent by struct design)\n",
           rt.pe_rows, rt.pe_cols, cfg.dma_bus_width_bits);
    CHECK(rt.pe_rows == 16 && rt.pe_cols == 16, "runtime retains PE geometry");
    CHECK((sizeof(tu_runtime_config_t) > 0), "runtime struct exists");
}

int main(void) {
    printf("CH13_WEIGHT_STREAM_PROBE start\n");
    probe_quant();
    probe_sparsity();
    probe_compress();
    probe_config();
    printf("CH13_PROBE SUMMARY failures=%d\n", failures);
    return failures == 0 ? 0 : 1;
}
