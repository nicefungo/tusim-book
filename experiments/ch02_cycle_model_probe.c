#include <stdio.h>
#include <stdint.h>
#include "tu_cmodel/perf/cycle_model.h"

int main(void) {
    const uint32_t modes[] = {
        TU_CYCLE_MODEL_FUNCTIONAL,
        TU_CYCLE_MODEL_ESTIMATED,
        TU_CYCLE_MODEL_CYCLE_ACCURATE
    };
    const char *names[] = {"functional", "estimated", "named-cycle-accurate"};

    printf("constants: pe=%ux%u depth=%u banks=%u bank_width=%u words_per_cycle=%u window=%u penalty=%u\n",
           TU_PE_ROWS, TU_PE_COLS, TU_PE_PIPELINE_DEPTH,
           TU_SRAM_BANKS, TU_SRAM_BANK_WIDTH, TU_SRAM_WORDS_PER_CYCLE,
           TU_SRAM_BW_WINDOW_CYCLES, TU_SRAM_BW_STALL_PENALTY);

    for (unsigned i = 0; i < 3; ++i) {
        tu_cycle_model_t *cm = tu_cycle_model_create(modes[i], NULL);
        uint64_t cycles = tu_cycle_model_execute_tile(
            cm, 0, 16, 0, 16, 0, 64, 0x100, 0x200, 0x300);
        printf("mode=%s returned_cycles=%llu current_cycle=%llu",
               names[i], (unsigned long long)cycles,
               (unsigned long long)cm->current_cycle);
        if (cm->bank_model) {
            uint64_t reads = 0, writes = 0, stalls = 0, conflicts = 0;
            double util = 0.0;
            tu_bank_model_get_stats(cm->bank_model, &reads, &writes,
                                    &stalls, &conflicts, &util);
            printf(" bank_reads=%llu bank_writes=%llu shortfall_words=%llu conflicts=%llu reported_util=%.3f",
                   (unsigned long long)reads, (unsigned long long)writes,
                   (unsigned long long)stalls, (unsigned long long)conflicts,
                   util);
        }
        putchar('\n');
        tu_cycle_model_destroy(cm);
    }
    return 0;
}
