#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "tu_cmodel/isa/tu_isa.h"
#include "tu_cmodel/isa/tu_scheduler.h"
#include "tu_cmodel/isa/tu_liveness.h"

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    tu_instruction_t x;
    memset(&x, 0, sizeof(x));
    x.opcode = TU_ISA_MMA;
    x.dim0 = UINT16_MAX;
    x.dim1 = UINT16_MAX;
    x.dim2 = UINT16_MAX;
    if (strcmp(argv[1], "scheduler") == 0) {
        tu_sram_access_t a;
        tu_sched_analyze_access(&x, &a);
        printf("scheduler_end=%u\n", a.read_offsets[TU_SRAM_W][1]);
        return 0;
    }
    if (strcmp(argv[1], "liveness") == 0) {
        tu_liveness_result_t r;
        int rc = tu_live_analyze(&x, 1, &r);
        printf("liveness_rc=%d vregs=%u\n", rc, r.num_vregs);
        return 0;
    }
    return 2;
}
