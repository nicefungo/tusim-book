/* Chapter 8 conformance checks plus pinned known-defect snapshot. */
#include <float.h>
#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "tu_cmodel/tu_precision.h"
#include "tu_cmodel/rounding.h"
#include "tu_cmodel/fp8.h"
#include "tu_cmodel/tf32.h"
#include "tu_cmodel/compute/dataflow/dataflow_interface.h"
#include "tu_cmodel/infra/config.h"
#include "tu_cmodel/tu_cmodel.h"

_Static_assert(sizeof(float) == 4, "probe requires 32-bit C float storage");
_Static_assert(FLT_RADIX == 2 && FLT_MANT_DIG == 24 && FLT_MAX_EXP == 128,
               "probe requires IEEE-binary32-like C float");

extern tu_dataflow_plugin_t *tu_dataflow_ws_create(void);
extern tu_dataflow_plugin_t *tu_dataflow_os_create(void);
extern tu_dataflow_plugin_t *tu_dataflow_rs_create(void);
extern void tu_dataflow_ws_destroy(tu_dataflow_plugin_t *);
extern void tu_dataflow_os_destroy(tu_dataflow_plugin_t *);
extern void tu_dataflow_rs_destroy(tu_dataflow_plugin_t *);

static unsigned failures;

static void fail_u64(const char *name, uint64_t got, uint64_t expected) {
    fprintf(stderr, "FAIL %s got=0x%" PRIx64 " expected=0x%" PRIx64 "\n",
            name, got, expected);
    failures++;
}

#define CHECK_EQ(name, got, expected) do { \
    uint64_t g_ = (uint64_t)(got), e_ = (uint64_t)(expected); \
    if (g_ != e_) fail_u64((name), g_, e_); \
} while (0)

#define CHECK_TRUE(name, cond) do { \
    if (!(cond)) { fprintf(stderr, "FAIL %s\n", (name)); failures++; } \
} while (0)

static float f32_from_bits(uint32_t u) {
    float f;
    memcpy(&f, &u, sizeof(f));
    return f;
}

static uint32_t f32_bits(float f) {
    uint32_t u;
    memcpy(&u, &f, sizeof(u));
    return u;
}

static uint64_t fnv1a_u32(uint64_t hash, uint32_t value) {
    for (unsigned i = 0; i < 4; i++) {
        hash ^= (uint8_t)(value >> (8 * i));
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

/* Independent exact binary16-to-binary32 representation oracle. */
static uint32_t fp16_decode_oracle_bits(uint16_t h) {
    uint32_t sign = (uint32_t)(h & 0x8000u) << 16;
    uint32_t exp = (h >> 10) & 0x1fu;
    uint32_t frac = h & 0x03ffu;
    if (exp == 0) {
        if (frac == 0) return sign;
        int e = -14;
        while ((frac & 0x0400u) == 0) { frac <<= 1; e--; }
        frac &= 0x03ffu;
        return sign | ((uint32_t)(e + 127) << 23) | (frac << 13);
    }
    if (exp == 0x1fu) return sign | 0x7f800000u | (frac << 13);
    return sign | ((exp + 112u) << 23) | (frac << 13);
}

static int fp16_is_finite_nonzero(uint16_t h) {
    return (h & 0x7fffu) != 0 && (h & 0x7c00u) != 0x7c00u;
}

static void probe_fp16_decode(void) {
    uint32_t canonical_mismatches = 0;
    for (uint32_t h = 0; h <= 0xffffu; h++) {
        uint32_t got = f32_bits(tu_fp16_to_fp32((uint16_t)h));
        uint32_t expected = fp16_decode_oracle_bits((uint16_t)h);
        if (got != expected) canonical_mismatches++;
    }
    CHECK_EQ("canonical fp16 exhaustive decode mismatches", canonical_mismatches, 0);
    printf("FP16_DECODE canonical_exhaustive=65536 mismatches=%u ", canonical_mismatches);
    printf("pos_zero=%08x neg_zero=%08x min_sub=%08x max_sub=%08x min_norm=%08x max_norm=%08x pos_inf=%08x qnan=%08x snan=%08x\n",
           f32_bits(tu_fp16_to_fp32(0x0000)), f32_bits(tu_fp16_to_fp32(0x8000)),
           f32_bits(tu_fp16_to_fp32(0x0001)), f32_bits(tu_fp16_to_fp32(0x03ff)),
           f32_bits(tu_fp16_to_fp32(0x0400)), f32_bits(tu_fp16_to_fp32(0x7bff)),
           f32_bits(tu_fp16_to_fp32(0x7c00)), f32_bits(tu_fp16_to_fp32(0x7e00)),
           f32_bits(tu_fp16_to_fp32(0x7d00)));
}

static void probe_one_dataflow(const char *name, tu_dataflow_plugin_t *p,
                               void (*destroy)(tu_dataflow_plugin_t *)) {
    enum { CHUNK = 32768 };
    uint16_t *a = malloc(CHUNK * sizeof(*a));
    float *o = malloc(CHUNK * sizeof(*o));
    uint16_t w = 0x3c00;
    CHECK_TRUE("dataflow allocations", a && o && p && p->execute_tile);
    if (!a || !o || !p || !p->execute_tile) exit(2);

    uint32_t finite_mismatches = 0, subnormal_mismatches = 0, normal_mismatches = 0;
    uint64_t snapshot_digest = UINT64_C(14695981039346656037);
    uint32_t first_sub_got = 0, second_sub_got = 0;
    for (uint32_t base = 0; base < 65536; base += CHUNK) {
        for (uint32_t i = 0; i < CHUNK; i++) { a[i] = (uint16_t)(base + i); o[i] = 0.0f; }
        tu_mma_op_t op = {
            .W = { &w, 1, 1, 2, 2 },
            .A = { a, 1, CHUNK, CHUNK * 2u, 2 },
            .O = { o, 1, CHUNK, CHUNK * 4u, 4 },
            .tile_m = 1, .tile_n = CHUNK, .tile_k = 1, .pipeline_depth = 2
        };
        p->execute_tile(p, &op, 0, 1, 0, CHUNK, 0, 1);
        for (uint32_t i = 0; i < CHUNK; i++) {
            uint16_t h = (uint16_t)(base + i);
            if (!fp16_is_finite_nonzero(h)) continue;
            uint32_t got = f32_bits(o[i]);
            uint32_t expected = fp16_decode_oracle_bits(h);
            snapshot_digest = fnv1a_u32(snapshot_digest, h);
            snapshot_digest = fnv1a_u32(snapshot_digest, got);
            snapshot_digest = fnv1a_u32(snapshot_digest, expected);
            if (got != expected) {
                finite_mismatches++;
                if ((h & 0x7c00u) == 0) {
                    subnormal_mismatches++;
                    if (!first_sub_got && h == 1) first_sub_got = got;
                    if (!second_sub_got && h == 2) second_sub_got = got;
                } else normal_mismatches++;
            }
        }
    }
    CHECK_EQ("engine local finite mismatch count", finite_mismatches, 1982);
    CHECK_EQ("engine local subnormal mismatch count", subnormal_mismatches, 1982);
    CHECK_EQ("engine local normal mismatch count", normal_mismatches, 0);
    CHECK_EQ("engine local min-subnormal decode", first_sub_got, 0x38800000u);
    CHECK_EQ("engine local second-subnormal decode", second_sub_got, 0x38000000u);
    CHECK_EQ("engine local full finite snapshot digest", snapshot_digest, UINT64_C(0xd56431612d444f4d));
    printf("KNOWN_DEFECT_SNAPSHOT name=%s finite_vectors=63486 mismatches=%u subnormal_mismatches=%u normal_mismatches=%u min_sub_got=%08x second_sub_got=%08x min_sub_expected=33800000 second_sub_expected=34000000 nonmonotonic=1 digest=%016" PRIx64 "\n",
           name, finite_mismatches, subnormal_mismatches, normal_mismatches,
           first_sub_got, second_sub_got, snapshot_digest);
    free(a); free(o); destroy(p);
}

static void probe_fp16_encode(void) {
    tu_set_rounding_mode(TU_ROUND_RNE);
    tu_set_subnormal_mode(TU_SUBNORMAL_FLUSH);
    CHECK_EQ("fp16 +0", tu_fp32_to_fp16(f32_from_bits(0x00000000)), 0x0000);
    CHECK_EQ("fp16 -0", tu_fp32_to_fp16(f32_from_bits(0x80000000)), 0x8000);
    CHECK_EQ("fp16 +inf", tu_fp32_to_fp16(INFINITY), 0x7c00);
    CHECK_EQ("fp16 -inf", tu_fp32_to_fp16(-INFINITY), 0xfc00);
    CHECK_EQ("fp16 positive qnan canonical", tu_fp32_to_fp16(f32_from_bits(0x7fc12345)), 0x7e00);
    CHECK_EQ("fp16 negative qnan sign discarded", tu_fp32_to_fp16(f32_from_bits(0xffc12345)), 0x7e00);
    CHECK_EQ("fp16 FTZ min subnormal", tu_fp32_to_fp16(ldexpf(1.0f, -24)), 0x0000);
    CHECK_EQ("fp16 FTZ max subnormal", tu_fp32_to_fp16(ldexpf(1.0f, -14) - ldexpf(1.0f, -24)), 0x0000);
    CHECK_EQ("fp16 min normal", tu_fp32_to_fp16(ldexpf(1.0f, -14)), 0x0400);
    CHECK_EQ("fp16 RNE tie even", tu_fp32_to_fp16(1.0f + ldexpf(1.0f, -11)), 0x3c00);
    CHECK_EQ("fp16 RNE odd-lower tie rounds to even upper", tu_fp32_to_fp16(1.0f + 3.0f * ldexpf(1.0f, -11)), 0x3c02);
    CHECK_EQ("fp16 RNE overflow tie", tu_fp32_to_fp16(65520.0f), 0x7c00);

    tu_set_subnormal_mode(TU_SUBNORMAL_FULL);
    uint16_t full_min = tu_fp32_to_fp16(ldexpf(1.0f, -24));
    uint16_t full_max = tu_fp32_to_fp16(ldexpf(1.0f, -14) - ldexpf(1.0f, -24));
    uint16_t full_half_min = tu_fp32_to_fp16(f32_from_bits(0x33000000));
    uint16_t full_above_half = tu_fp32_to_fp16(f32_from_bits(0x33000001));
    uint16_t full_below_normal_mid = tu_fp32_to_fp16(f32_from_bits(0x387fdfff));
    uint16_t full_mid_normal = tu_fp32_to_fp16(f32_from_bits(0x387fe000));
    uint16_t full_above_normal_mid = tu_fp32_to_fp16(f32_from_bits(0x387fe001));
    CHECK_EQ("fp16 full min subnormal observed defect", full_min, 0x0200);
    CHECK_EQ("fp16 full max subnormal observed defect", full_max, 0x0200);
    CHECK_EQ("fp16 full half-min tie observed defect", full_half_min, 0x0200);
    CHECK_EQ("fp16 full above-half observed defect", full_above_half, 0x0200);
    CHECK_EQ("fp16 full below-normal-mid observed defect", full_below_normal_mid, 0x0200);
    CHECK_EQ("fp16 full normal-boundary midpoint observed defect", full_mid_normal, 0x0200);
    CHECK_EQ("fp16 full above-normal-mid observed defect", full_above_normal_mid, 0x0200);

    tu_set_subnormal_mode(TU_SUBNORMAL_FLUSH);
    CHECK_EQ("fp16 FTZ below normal-boundary midpoint", tu_fp32_to_fp16(f32_from_bits(0x387fdfff)), 0x0000);
    CHECK_EQ("fp16 FTZ pre-round normal-boundary midpoint", tu_fp32_to_fp16(f32_from_bits(0x387fe000)), 0x0000);
    CHECK_EQ("fp16 FTZ above normal-boundary midpoint", tu_fp32_to_fp16(f32_from_bits(0x387fe001)), 0x0000);

    tu_set_rounding_mode(TU_ROUND_RTZ);
    CHECK_EQ("fp16 RTZ finite above max exponent", tu_fp32_to_fp16(70000.0f), 0x7c00);
    tu_set_rounding_mode(TU_ROUND_RNE);
    uint16_t rne_tie = tu_fp32_to_fp16(1.0f + ldexpf(1.0f, -11));
    uint16_t overflow_tie = tu_fp32_to_fp16(65520.0f);
    tu_set_rounding_mode(TU_ROUND_RTZ);
    printf("FP16_ENCODE rne_tie=%04x overflow_tie=%04x full_min_sub=%04x full_max_sub=%04x full_half_min=%04x full_above_half=%04x full_below_normal_mid=%04x full_mid_normal=%04x full_above_normal_mid=%04x ftz_mid_normal=%04x rtz_70000=%04x neg_nan=%04x\n",
           rne_tie, overflow_tie, full_min, full_max, full_half_min, full_above_half,
           full_below_normal_mid, full_mid_normal, full_above_normal_mid,
           tu_fp32_to_fp16(f32_from_bits(0x387fe000)),
           tu_fp32_to_fp16(70000.0f), tu_fp32_to_fp16(f32_from_bits(0xffc12345)));
}

static void probe_bf16(void) {
    tu_set_rounding_mode(TU_ROUND_RNE);
    CHECK_EQ("bf16 decode min subnormal", f32_bits(tu_bf16_to_fp32(0x0001)), 0x00010000u);
    CHECK_EQ("bf16 encode +0", tu_fp32_to_bf16(f32_from_bits(0)), 0x0000);
    CHECK_EQ("bf16 encode -0", tu_fp32_to_bf16(f32_from_bits(0x80000000)), 0x8000);
    CHECK_EQ("bf16 RNE tie even", tu_fp32_to_bf16(1.0f + ldexpf(1.0f, -8)), 0x3f80);
    CHECK_EQ("bf16 RNE odd-lower tie rounds to even upper", tu_fp32_to_bf16(1.0f + 3.0f * ldexpf(1.0f, -8)), 0x3f82);
    CHECK_EQ("bf16 representable min subnormal flushed", tu_fp32_to_bf16(f32_from_bits(0x00010000)), 0x0000);
    CHECK_EQ("bf16 normal-boundary midpoint carries to normal", tu_fp32_to_bf16(f32_from_bits(0x007f8000)), 0x0080);
    CHECK_EQ("bf16 qnan", tu_fp32_to_bf16(f32_from_bits(0x7fc00000)), 0x7fc0);
    CHECK_EQ("bf16 low-payload snan becomes infinity", tu_fp32_to_bf16(f32_from_bits(0x7f800001)), 0x7f80);
    printf("BF16 decode_min_sub=%08x encode_min_sub=%04x boundary_mid=%04x tie=%04x qnan=%04x low_payload_snan=%04x\n",
           f32_bits(tu_bf16_to_fp32(0x0001)), tu_fp32_to_bf16(f32_from_bits(0x00010000)),
           tu_fp32_to_bf16(f32_from_bits(0x007f8000)),
           tu_fp32_to_bf16(1.0f + ldexpf(1.0f, -8)), tu_fp32_to_bf16(f32_from_bits(0x7fc00000)),
           tu_fp32_to_bf16(f32_from_bits(0x7f800001)));
}

static uint32_t fp8_e4m3_ofp8_oracle_bits(uint8_t v) {
    uint32_t sign = (uint32_t)(v >> 7) << 31;
    uint32_t exp = (v >> 3) & 0x0fu, frac = v & 7u;
    float s = (v & 0x80u) ? -1.0f : 1.0f;
    if (exp == 0) return frac ? f32_bits(s * ldexpf((float)frac, -9)) : sign;
    if (exp == 15 && frac == 7) return sign | 0x7fc00000u;
    return f32_bits(s * ldexpf(1.0f + (float)frac / 8.0f, (int)exp - 7));
}

static uint32_t fp8_e5m2_oracle_bits(uint8_t v) {
    uint32_t sign = (uint32_t)(v >> 7) << 31;
    uint32_t exp = (v >> 2) & 0x1fu, frac = v & 3u;
    float s = (v & 0x80u) ? -1.0f : 1.0f;
    if (exp == 0) return frac ? f32_bits(s * ldexpf((float)frac, -16)) : sign;
    if (exp == 31) return frac ? sign | 0x7fc00000u : sign | 0x7f800000u;
    return f32_bits(s * ldexpf(1.0f + (float)frac / 4.0f, (int)exp - 15));
}

static int same_bits_or_nan(uint32_t a, uint32_t b) {
    uint32_t aa = a & 0x7fffffffu, bb = b & 0x7fffffffu;
    int an = aa > 0x7f800000u, bn = bb > 0x7f800000u;
    return (an && bn) || a == b;
}

static void probe_fp8(void) {
    tu_set_rounding_mode(TU_ROUND_RNE);
    uint32_t e4_ofp8_decode_mismatches = 0, e5_decode_mismatches = 0;
    for (uint32_t raw = 0; raw < 256; raw++) {
        uint32_t e4_got = f32_bits(tu_fp8_e4m3_to_fp32((uint8_t)raw));
        uint32_t e5_got = f32_bits(tu_fp8_e5m2_to_fp32((uint8_t)raw));
        if (!same_bits_or_nan(e4_got, fp8_e4m3_ofp8_oracle_bits((uint8_t)raw))) e4_ofp8_decode_mismatches++;
        if (!same_bits_or_nan(e5_got, fp8_e5m2_oracle_bits((uint8_t)raw))) e5_decode_mismatches++;
    }
    CHECK_EQ("E4M3 exhaustive OFP8 decode disagreement count", e4_ofp8_decode_mismatches, 14);
    CHECK_EQ("E5M2 exhaustive decode mismatches", e5_decode_mismatches, 0);
    CHECK_EQ("e4m3 -zero", tu_fp32_to_fp8_e4m3(-0.0f), 0x80);
    CHECK_TRUE("e4m3 0x78 decoded NaN", isnan(tu_fp8_e4m3_to_fp32(0x78)));
    CHECK_EQ("e4m3 exact 240 unencodable", tu_fp32_to_fp8_e4m3(240.0f), 0x7f);
    CHECK_EQ("e4m3 448 overflow", tu_fp32_to_fp8_e4m3(448.0f), 0x7f);
    CHECK_EQ("e4m3 RNE tie is away not even", tu_fp32_to_fp8_e4m3(1.0625f), 0x39);
    CHECK_EQ("e4m3 min subnormal", tu_fp32_to_fp8_e4m3(ldexpf(1.0f, -9)), 0x01);
    CHECK_EQ("e4m3 half min subnormal tie rounds up", tu_fp32_to_fp8_e4m3(ldexpf(1.0f, -10)), 0x01);
    CHECK_EQ("e4m3 subnormal-normal midpoint clamps down", tu_fp32_to_fp8_e4m3(15.0f / 1024.0f), 0x07);

    CHECK_EQ("e5m2 +inf", tu_fp32_to_fp8_e5m2(INFINITY), 0x7c);
    CHECK_EQ("e5m2 exact max normal", tu_fp32_to_fp8_e5m2(57344.0f), 0x7b);
    CHECK_EQ("e5m2 overflow", tu_fp32_to_fp8_e5m2(60000.0f), 0x7c);
    CHECK_EQ("e5m2 RNE tie is away not even", tu_fp32_to_fp8_e5m2(1.125f), 0x3d);
    CHECK_EQ("e5m2 min subnormal", tu_fp32_to_fp8_e5m2(ldexpf(1.0f, -16)), 0x01);
    CHECK_EQ("e5m2 half min subnormal tie rounds up", tu_fp32_to_fp8_e5m2(ldexpf(1.0f, -17)), 0x01);
    CHECK_EQ("e5m2 subnormal-normal midpoint clamps down", tu_fp32_to_fp8_e5m2(7.0f / 131072.0f), 0x03);
    tu_set_rounding_mode(TU_ROUND_RTZ);
    uint8_t e5_rtz_overflow = tu_fp32_to_fp8_e5m2(60000.0f);
    CHECK_EQ("e5m2 RTZ overflow ignores mode", e5_rtz_overflow, 0x7c);
    tu_set_rounding_mode(TU_ROUND_RNE);
    printf("FP8 exhaustive_raw=256 e4_ofp8_decode_mismatches=%u e5_decode_mismatches=%u e4_decode_78_isnan=%d e4_encode_240=%02x e4_encode_448=%02x e4_tie=%02x e4_half_min=%02x e4_subnormal_normal_mid=%02x e5_max=%02x e5_overflow=%02x e5_rtz_overflow=%02x e5_tie=%02x e5_half_min=%02x e5_subnormal_normal_mid=%02x\n",
           e4_ofp8_decode_mismatches, e5_decode_mismatches,
           isnan(tu_fp8_e4m3_to_fp32(0x78)), tu_fp32_to_fp8_e4m3(240.0f),
           tu_fp32_to_fp8_e4m3(448.0f), tu_fp32_to_fp8_e4m3(1.0625f),
           tu_fp32_to_fp8_e4m3(ldexpf(1.0f, -10)), tu_fp32_to_fp8_e4m3(15.0f / 1024.0f),
           tu_fp32_to_fp8_e5m2(57344.0f), tu_fp32_to_fp8_e5m2(60000.0f),
           e5_rtz_overflow, tu_fp32_to_fp8_e5m2(1.125f),
           tu_fp32_to_fp8_e5m2(ldexpf(1.0f, -17)),
           tu_fp32_to_fp8_e5m2(7.0f / 131072.0f));
}

static void probe_tf32(void) {
    tu_set_rounding_mode(TU_ROUND_RNE);
    CHECK_EQ("tf32 -zero", tu_fp32_to_tf32(-0.0f), 0x80000000u);
    CHECK_EQ("tf32 tie even", tu_fp32_to_tf32(1.0f + ldexpf(1.0f, -11)), 0x3f800000u);
    CHECK_EQ("tf32 odd-lower tie rounds to even upper", tu_fp32_to_tf32(f32_from_bits(0x3f803000)), 0x3f804000u);
    CHECK_EQ("tf32 minimum stored subnormal", tu_fp32_to_tf32(f32_from_bits(0x00002000)), 0x00002000u);
    CHECK_EQ("tf32 half minimum tie to zero", tu_fp32_to_tf32(f32_from_bits(0x00001000)), 0x00000000u);
    CHECK_EQ("tf32 qnan", tu_fp32_to_tf32(f32_from_bits(0x7fc00000)), 0x7fc00000u);
    CHECK_EQ("tf32 low-payload snan becomes infinity", tu_fp32_to_tf32(f32_from_bits(0x7f800001)), 0x7f800000u);
    CHECK_EQ("tf32 decode masks nonstorage bits", f32_bits(tu_tf32_to_fp32(0x3f801fffu)), 0x3f800000u);
    printf("TF32 neg_zero=%08x tie=%08x min_sub=%08x half_min=%08x qnan=%08x low_payload_snan=%08x masked_decode=%08x\n",
           tu_fp32_to_tf32(-0.0f), tu_fp32_to_tf32(1.0f + ldexpf(1.0f, -11)),
           tu_fp32_to_tf32(f32_from_bits(0x00002000)), tu_fp32_to_tf32(f32_from_bits(0x00001000)),
           tu_fp32_to_tf32(f32_from_bits(0x7fc00000)), tu_fp32_to_tf32(f32_from_bits(0x7f800001)),
           f32_bits(tu_tf32_to_fp32(0x3f801fffu)));
}

static void probe_registry(void) {
    const char *expected[] = {"fp16", "fp32", "bf16", "fp8_e4m3", "fp8_e5m2", "int8", "int4", "tf32"};
    for (int i = 0; i < TU_PREC_COUNT; i++) {
        const tu_precision_desc_t *d = tu_precision_get((tu_precision_t)i);
        CHECK_TRUE("precision registry entry", d && d->type == (tu_precision_t)i && strcmp(d->name, expected[i]) == 0);
    }
    CHECK_TRUE("precision registry rejects count", tu_precision_get(TU_PREC_COUNT) == NULL);
    printf("REGISTRY builtin_count=%d ordered_entries=PASS execution_dispatch_not_implied=1\n", TU_PREC_COUNT);
}

static void probe_config_propagation(void) {
    const char *json = "{\"tu\":{\"compute\":{\"supported_precisions\":[\"bf16\",\"fp8_e5m2\"]},\"precision\":{\"fp16\":{\"rounding\":\"round_toward_zero\",\"subnormal\":\"full\",\"saturate\":true}}}}";
    tu_config_t cfg;
    char err[256] = {0};
    CHECK_EQ("precision config parses", tu_config_load_string(json, &cfg, err, sizeof(err)), 0);
    CHECK_EQ("config fp16 disabled", cfg.fp16_enabled, 0);
    CHECK_EQ("config bf16 enabled", cfg.bf16_enabled, 1);
    CHECK_EQ("config fp8 e4m3 disabled", cfg.fp8_e4m3_enabled, 0);
    CHECK_EQ("config fp8 e5m2 enabled", cfg.fp8_e5m2_enabled, 1);
    CHECK_EQ("config rounding RTZ", cfg.rounding_mode, 1);
    CHECK_EQ("config subnormal full", cfg.subnormal_flush, 0);
    CHECK_EQ("config saturate true", cfg.saturate, 1);

    tu_runtime_config_t rt = tu_config_to_runtime(&cfg);
    tu_set_rounding_mode(TU_ROUND_RNE);
    tu_set_subnormal_mode(TU_SUBNORMAL_FLUSH);
    tu_init_with_config(&rt);
    CHECK_EQ("runtime init drops requested RTZ", tu_get_rounding_mode(), TU_ROUND_RNE);
    CHECK_EQ("runtime init drops requested full subnormal", tu_get_subnormal_mode(), TU_SUBNORMAL_FLUSH);
    printf("CONFIG_EXEC parsed_bf16=1 parsed_fp8_e5m2=1 parsed_rounding=RTZ parsed_subnormal=FULL parsed_saturate=1 runtime_rounding=RNE runtime_subnormal=FLUSH precision_dispatch_absent=1\n");
}

int main(void) {
    probe_fp16_decode();
    probe_one_dataflow("weight_stationary", tu_dataflow_ws_create(), tu_dataflow_ws_destroy);
    probe_one_dataflow("output_stationary", tu_dataflow_os_create(), tu_dataflow_os_destroy);
    probe_one_dataflow("row_stationary", tu_dataflow_rs_create(), tu_dataflow_rs_destroy);
    probe_fp16_encode();
    probe_bf16();
    probe_fp8();
    probe_tf32();
    probe_registry();
    probe_config_propagation();
    if (failures) {
        fprintf(stderr, "SUMMARY: FAIL failures=%u\n", failures);
        return 1;
    }
    printf("SUMMARY: PASS failures=0\n");
    return 0;
}
