#include "tu_cmodel/tu_cmodel.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s CONFIG.json\n", argv[0]);
        return 2;
    }

    char error[256] = {0};
    if (tu_init_from_file(argv[1], error, sizeof(error)) != 0) {
        fprintf(stderr, "configuration error: %s\n", error);
        return 3;
    }

    if (g_tu.rt_cfg.pe_rows != 4 || g_tu.rt_cfg.pe_cols != 4 ||
        g_tu.sram_w.total_size != 8 * 1024 ||
        g_tu.sram_a.total_size != 8 * 1024 ||
        g_tu.sram_o.total_size != 8 * 1024) {
        fprintf(stderr, "geometry or SRAM capacity did not propagate\n");
        return 4;
    }

    const char *active_dataflow = tu_get_dataflow_name();
    printf("requested dataflow = output_stationary; active dataflow = %s\n",
           active_dataflow);
    if (strcmp(active_dataflow, "output_stationary") != 0) {
        fprintf(stderr, "edition drift: expected JSON-selected OS\n");
        return 5;
    }

    /* W[2][3] x A[3][2] = O[2][2]. */
    const fp16_t w[] = {
        0x3c00, 0x4000, 0x4200, /* 1, 2, 3 */
        0x4400, 0x4500, 0x4600  /* 4, 5, 6 */
    };
    const fp16_t a[] = {
        0x4700, 0x4800, /* 7, 8 */
        0x4880, 0x4900, /* 9, 10 */
        0x4980, 0x4a00  /* 11, 12 */
    };
    const float expected[] = {58.0f, 64.0f, 139.0f, 154.0f};
    float output[4] = {0};

    tu_dma_load_w(w, 0, sizeof(w));
    tu_dma_load_a(a, 0, sizeof(a));
    uint64_t before = g_tu.estimated_cycles;
    tu_mma(2, 2, 3, 0, 0, 0, false);
    uint64_t delta = g_tu.estimated_cycles - before;
    printf("MMA-only model cycles = %llu (expected 4)\n", (unsigned long long)delta);
    if (delta != 4) return 7;
    tu_dma_store_o(output, 0, sizeof(output));

    for (int i = 0; i < 4; ++i) {
        if (memcmp(&output[i], &expected[i], sizeof(float)) != 0) {
            fprintf(stderr, "mismatch at %d: got %.3f, expected %.3f\n",
                    i, output[i], expected[i]);
            return 6;
        }
    }

    printf("O = [[%.0f, %.0f], [%.0f, %.0f]]\n",
           output[0], output[1], output[2], output[3]);
    tu_print_stats();
    return 0;
}
