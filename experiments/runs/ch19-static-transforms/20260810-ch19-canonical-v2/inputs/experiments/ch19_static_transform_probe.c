#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "tu_cmodel/isa/tu_isa.h"
#include "tu_cmodel/isa/tu_scheduler.h"
#include "tu_cmodel/isa/tu_liveness.h"

static int failures;
#define CHECK(c, m) do { if (!(c)) { printf("CHECK_FAIL %s\n", (m)); failures++; } } while (0)

static tu_instruction_t I(tu_isa_opcode_t op, uint16_t d0, uint16_t d1,
                          uint16_t d2, uint8_t flags, uint32_t imm) {
    tu_instruction_t x;
    memset(&x, 0, sizeof(x));
    x.opcode = op; x.dim0 = d0; x.dim1 = d1; x.dim2 = d2;
    x.flags = flags; x.immediates = imm;
    return x;
}

static void free_graphs(tu_liveness_result_t *r) {
    free(r->graph_w.interference);
    free(r->graph_a.interference);
    free(r->graph_o.interference);
    r->graph_w.interference = NULL;
    r->graph_a.interference = NULL;
    r->graph_o.interference = NULL;
}

static unsigned edge_count(const tu_interference_graph_t *g) {
    unsigned n = 0;
    if (!g || !g->interference) return 0;
    for (uint32_t i = 0; i < g->num_vregs; ++i)
        for (uint32_t j = i + 1; j < g->num_vregs; ++j)
            if (g->interference[i * g->num_vregs + j]) ++n;
    return n;
}

static void print_ops(const char *tag, const tu_instruction_t *x, uint32_t n) {
    printf("OPS %s n=%u", tag, n);
    for (uint32_t i = 0; i < n; ++i)
        printf(" %u:%s/%u/%u/%u/0x%08x", i,
               tu_isa_opcode_name((tu_isa_opcode_t)x[i].opcode),
               x[i].dim0, x[i].dim1, x[i].dim2, x[i].immediates);
    putchar('\n');
}

static void test_scheduler_policy_and_barrier(void) {
    tu_instruction_t independent[] = {
        I(TU_ISA_NOP, 0, 0, 0, 0, 0),
        I(TU_ISA_DMA_LOAD, 64, 16, 0, 0, 0),
    };
    tu_sched_result_t a, l, b;
    tu_sched_config_t cfg = tu_sched_config_default;
    cfg.insert_barriers = false; cfg.hoist_dma = false;
    cfg.policy = TU_SCHED_POLICY_ASAP; CHECK(tu_sched_run(independent, 2, &cfg, &a) == 0, "ASAP run");
    cfg.policy = TU_SCHED_POLICY_ALAP; CHECK(tu_sched_run(independent, 2, &cfg, &l) == 0, "ALAP run");
    cfg.policy = TU_SCHED_POLICY_BALANCED; CHECK(tu_sched_run(independent, 2, &cfg, &b) == 0, "balanced run");
    printf("SCHED_POLICY asap=%s,%s alap=%s,%s balanced=%s,%s cycles=%u/%u/%u\n",
           tu_isa_opcode_name((tu_isa_opcode_t)a.instructions[0].opcode),
           tu_isa_opcode_name((tu_isa_opcode_t)a.instructions[1].opcode),
           tu_isa_opcode_name((tu_isa_opcode_t)l.instructions[0].opcode),
           tu_isa_opcode_name((tu_isa_opcode_t)l.instructions[1].opcode),
           tu_isa_opcode_name((tu_isa_opcode_t)b.instructions[0].opcode),
           tu_isa_opcode_name((tu_isa_opcode_t)b.instructions[1].opcode),
           a.estimated_cycles, l.estimated_cycles, b.estimated_cycles);
    CHECK(a.instructions[0].opcode == TU_ISA_NOP && l.instructions[0].opcode == TU_ISA_NOP,
          "ASAP/ALAP original-ID tie");
    CHECK(b.instructions[0].opcode == TU_ISA_DMA_LOAD, "balanced DMA priority");
    CHECK(a.estimated_cycles == 5 && l.estimated_cycles == 5 && b.estimated_cycles == 5,
          "serial policy cycle sum");

    tu_instruction_t crossing[] = {
        I(TU_ISA_NOP, 0, 0, 0, 0, 0),
        I(TU_ISA_BARRIER, 0, 0, 0, 0, 0),
        I(TU_ISA_DMA_LOAD, 64, 16, 0, 0, 0),
    };
    cfg = tu_sched_config_default;
    cfg.policy = TU_SCHED_POLICY_BALANCED;
    tu_sched_result_t out;
    CHECK(tu_sched_run(crossing, 3, &cfg, &out) == 0, "barrier crossing run");
    print_ops("barrier_crossing", out.instructions, out.num_instructions);
    CHECK(out.instructions[0].opcode == TU_ISA_DMA_LOAD &&
          out.instructions[1].opcode == TU_ISA_NOP &&
          out.instructions[2].opcode == TU_ISA_BARRIER,
          "later DMA crosses scheduler barrier");
}

static void test_scheduler_analysis_and_validation(void) {
    tu_instruction_t seq[] = {
        I(TU_ISA_DMA_STORE, 0, 16, 1, 2, 0x11111111),
        I(TU_ISA_RELU, 0, 4, 2, 0, 0x22222222),
    };
    tu_sched_graph_t g;
    tu_sched_config_t cfg = tu_sched_config_default;
    CHECK(tu_sched_build_dag(&g, seq, 2, &cfg) == 0, "analysis DAG");
    int direct = tu_sched_insert_barriers(&g);
    tu_sched_result_t explicit_default, null_default;
    CHECK(tu_sched_run(seq, 2, &cfg, &explicit_default) == 0, "explicit default run");
    CHECK(tu_sched_run(seq, 2, NULL, &null_default) == 0, "null default run");
    printf("SCHED_NAMED direct_barriers=%d explicit=%u null=%u order_equal=%d\n",
           direct, explicit_default.num_barriers_inserted,
           null_default.num_barriers_inserted,
           memcmp(explicit_default.instructions, null_default.instructions,
                  2 * sizeof(tu_instruction_t)) == 0);
    CHECK(direct == 1 && explicit_default.num_barriers_inserted == 0 &&
          null_default.num_barriers_inserted == 0,
          "named barrier count erased");

    tu_instruction_t duplicate[] = {
        I(TU_ISA_DMA_LOAD, 0, 16, 1, 0, 0x11111111),
        I(TU_ISA_DMA_LOAD, 0, 16, 2, 0, 0x22222222),
    };
    CHECK(tu_sched_build_dag(&g, duplicate, 2, &cfg) == 0, "duplicate DAG");
    CHECK(g.nodes[1].num_preds == 1, "duplicate WAW edge");
    g.nodes[0].scheduled = true; g.nodes[1].scheduled = true;
    tu_sched_result_t reversed;
    memset(&reversed, 0, sizeof(reversed));
    reversed.valid = true; reversed.num_instructions = 2;
    reversed.instructions[0] = duplicate[1];
    reversed.instructions[1] = duplicate[0];
    bool accepted = tu_sched_validate(&reversed, &g);
    printf("SCHED_VALIDATE reversed_dependency accepted=%d omitted_dim2=%u,%u omitted_imm=0x%08x,0x%08x\n",
           accepted, duplicate[0].dim2, duplicate[1].dim2,
           duplicate[0].immediates, duplicate[1].immediates);
    CHECK(accepted, "weak identity accepts reversed dependency");

    tu_instruction_t dense[18];
    for (int i = 0; i < 17; ++i) dense[i] = I(TU_ISA_NOP, (uint16_t)i, 0, 0, 0, 0);
    dense[17] = I(TU_ISA_BARRIER, 0, 0, 0, 0, 0);
    CHECK(tu_sched_build_dag(&g, dense, 18, &cfg) == 0, "dense DAG");
    printf("SCHED_DENSE intended=17 retained=%u built=%d\n",
           g.nodes[17].num_preds, g.built);
    CHECK(g.nodes[17].num_preds == 16 && g.built, "dense truncation");
}

static void test_scheduler_additional_boundaries(void) {
    tu_sched_config_t cfg = tu_sched_config_default;
    cfg.policy = TU_SCHED_POLICY_BALANCED;
    tu_sched_result_t out;

    tu_instruction_t halt_crossing[] = {
        I(TU_ISA_NOP, 0, 0, 0, 0, 0),
        I(TU_ISA_HALT, 0, 0, 0, 0, 0),
        I(TU_ISA_DMA_LOAD, 64, 16, 0, 0, 0),
    };
    CHECK(tu_sched_run(halt_crossing, 3, &cfg, &out) == 0, "HALT crossing run");
    print_ops("halt_crossing", out.instructions, out.num_instructions);
    CHECK(out.instructions[0].opcode == TU_ISA_DMA_LOAD &&
          out.instructions[2].opcode == TU_ISA_HALT,
          "later DMA crosses scheduler HALT");

    tu_instruction_t fanout[18];
    fanout[0] = I(TU_ISA_DMA_STORE, 0, UINT16_MAX, 0, 0, 0);
    for (uint32_t i = 1; i < 18; ++i)
        fanout[i] = I(TU_ISA_DMA_LOAD, (uint16_t)(i * 16), 8, 0, 0, 0);
    tu_sched_graph_t g;
    CHECK(tu_sched_build_dag(&g, fanout, 18, &cfg) == 0, "successor-cap DAG");
    CHECK(tu_sched_run(fanout, 18, &cfg, &out) == 0, "successor-cap run");
    printf("SCHED_FANOUT intended=17 producer_succs=%u last_preds=%u first=%s\n",
           g.nodes[0].num_succs, g.nodes[17].num_preds,
           tu_isa_opcode_name((tu_isa_opcode_t)out.instructions[0].opcode));
    CHECK(g.nodes[0].num_succs == 16 && g.nodes[17].num_preds == 0,
          "successor-cap drops reciprocal edge");
    CHECK(out.instructions[0].opcode == TU_ISA_DMA_LOAD && out.instructions[0].dim0 == 17 * 16,
          "dropped 17th consumer crosses producer");

    tu_instruction_t dep[] = {
        I(TU_ISA_DMA_LOAD, 0, 16, 0, 0, 0),
        I(TU_ISA_MMA, 0, 1, 1, 0, 0),
    };
    CHECK(tu_sched_build_dag(&g, dep, 2, &cfg) == 0, "unmatched validator DAG");
    tu_sched_result_t fake;
    memset(&fake, 0, sizeof(fake));
    fake.valid = true; fake.num_instructions = 2;
    fake.instructions[0] = I(TU_ISA_NOP, 0, 0, 0, 0, 0);
    fake.instructions[1] = I(TU_ISA_NOP, 1, 0, 0, 0, 0);
    bool unmatched = tu_sched_validate(&fake, &g);
    printf("SCHED_VALIDATE unmatched accepted=%d graph_nodes=%u result_nodes=%u\n",
           unmatched, g.num_nodes, fake.num_instructions);
    CHECK(unmatched, "validator accepts completely unmatched result");

    tu_instruction_t hoist[] = {
        I(TU_ISA_DMA_STORE, 0, 16, 0, 0, 0),
        I(TU_ISA_NOP, 0, 0, 0, 0, 0),
        I(TU_ISA_DMA_STORE, 0, 16, 0, 0, 0),
        I(TU_ISA_DMA_LOAD, 0, 16, 0, 0, 0),
    };
    CHECK(tu_sched_build_dag(&g, hoist, 4, &cfg) == 0, "latest-predecessor DAG");
    int hoisted = tu_sched_hoist_dma(&g);
    printf("SCHED_HOIST preds=%u ids=%u,%u reported=%d\n",
           g.nodes[3].num_preds, g.nodes[3].preds[0], g.nodes[3].preds[1], hoisted);
    CHECK(g.nodes[3].num_preds == 2 && hoisted == 1,
          "hoist report uses earliest rather than latest predecessor");

    tu_instruction_t independent[] = {
        I(TU_ISA_NOP, 0, 0, 0, 0, 0),
        I(TU_ISA_DMA_LOAD, 64, 16, 0, 0, 0),
    };
    cfg.policy = (tu_sched_policy_t)99;
    CHECK(tu_sched_run(independent, 2, &cfg, &out) == 0, "invalid policy run");
    printf("SCHED_INVALID_POLICY rc=0 first=%s\n",
           tu_isa_opcode_name((tu_isa_opcode_t)out.instructions[0].opcode));
    CHECK(out.instructions[0].opcode == TU_ISA_DMA_LOAD,
          "invalid policy silently falls back to balanced");

    struct { tu_isa_opcode_t op; const char *name; } census[] = {
        {TU_ISA_ELEMENTWISE, "ELEMENTWISE"}, {TU_ISA_SCALE, "SCALE"},
        {TU_ISA_GROUP_NORM, "GROUP_NORM"}, {TU_ISA_DECOMPRESS, "DECOMPRESS"},
        {TU_ISA_COMPRESS, "COMPRESS"},
    };
    printf("SCHED_ACCESS_CENSUS");
    for (size_t i = 0; i < sizeof(census) / sizeof(census[0]); ++i) {
        tu_sram_access_t a;
        tu_instruction_t x = I(census[i].op, 1, 2, 3, 0, 0);
        tu_sched_analyze_access(&x, &a);
        unsigned effects = 0;
        for (int r = 0; r < TU_SRAM_REGION_COUNT; ++r)
            effects += a.reads[r] + a.writes[r];
        printf(" %s=%u", census[i].name, effects);
        unsigned expected = (census[i].op == TU_ISA_ELEMENTWISE ||
                             census[i].op == TU_ISA_SCALE) ? 2u : 0u;
        CHECK(effects == expected, "scheduler opcode access census");
    }
    putchar('\n');

    tu_sram_access_t a;
    tu_instruction_t zero = I(TU_ISA_DMA_LOAD, 100, 0, 0, TU_FLAG_PREC_FP32, 0);
    tu_sched_analyze_access(&zero, &a);
    printf("SCHED_DMA_FIELDS flags=0x%x writesW=%d writesA=%d rangeA=%u:%u\n",
           zero.flags, a.writes[TU_SRAM_W], a.writes[TU_SRAM_A],
           a.write_offsets[TU_SRAM_A][0], a.write_offsets[TU_SRAM_A][1]);
    CHECK(a.writes[TU_SRAM_A] && a.write_offsets[TU_SRAM_A][0] == 100 &&
          a.write_offsets[TU_SRAM_A][1] == 101,
          "precision flag doubles as channel and zero size becomes one byte");
}

static void test_cross_pass_access(void) {
    tu_instruction_t attn = I(TU_ISA_ATTENTION, 32, 4, 0, 0, 0x00400000);
    tu_sram_access_t acc;
    tu_sched_analyze_access(&attn, &acc);
    tu_liveness_result_t lr;
    CHECK(tu_live_analyze(&attn, 1, &lr) == 0, "attention liveness");
    printf("CROSS_ACCESS attention sched_readA=%d sched_writeO=%d live_vregs=%u",
           acc.reads[TU_SRAM_A], acc.writes[TU_SRAM_O], lr.num_vregs);
    for (uint32_t i = 0; i < lr.num_vregs; ++i)
        printf(" v%u=%d/%d/%d/%u", i, lr.vregs[i].region,
               lr.vregs[i].first_def, lr.vregs[i].last_use,
               lr.vregs[i].size_bytes);
    putchar('\n');
    CHECK(acc.reads[TU_SRAM_A] && acc.writes[TU_SRAM_O], "scheduler attention effects");
    CHECK(lr.num_vregs == 1 && lr.vregs[0].region == TU_VREG_O,
          "liveness omits attention A use");
}

static void test_liveness_binding_and_limits(void) {
    tu_instruction_t seq[] = {
        I(TU_ISA_DMA_LOAD, 0, 16, 0, 0, 0),
        I(TU_ISA_DMA_LOAD, 100, 16, 0, 0, 0),
        I(TU_ISA_MMA, 0, 1, 1, 0, 0),
    };
    tu_liveness_result_t r;
    CHECK(tu_live_analyze(seq, 3, &r) == 0, "range-binding analysis");
    tu_live_build_interference(&r);
    printf("LIVE_BIND vregs=%u w_nodes=%u w_edges=%u", r.num_vregs,
           r.graph_w.num_vregs, edge_count(&r.graph_w));
    for (uint32_t i = 0; i < r.num_vregs; ++i)
        printf(" v%u=%d/%d/%d/%u", i, r.vregs[i].region,
               r.vregs[i].first_def, r.vregs[i].last_use, r.vregs[i].size_bytes);
    putchar('\n');
    CHECK(r.num_vregs == 6, "two W, repeated implicit A, O definitions");
    CHECK(r.vregs[0].last_use == 0 && r.vregs[2].last_use == 2,
          "MMA W use attaches newest disjoint W definition");
    CHECK(edge_count(&r.graph_w) == 0, "range-binding prevents intended W overlap");
    free_graphs(&r);

    tu_instruction_t *many = calloc(129, sizeof(*many));
    CHECK(many != NULL, "many allocation");
    for (uint32_t i = 0; i < 129; ++i)
        many[i] = I(TU_ISA_DMA_LOAD, (uint16_t)i, 1, 0, 0, 0);
    CHECK(tu_live_analyze(many, 129, &r) == 0, "129-vreg analysis returns success");
    printf("LIVE_VREG_LIMIT input_defs=129 rc=0 retained=%u\n", r.num_vregs);
    CHECK(r.num_vregs == TU_LIVE_MAX_VREGS, "vreg truncation at 128");
    free(many);
}

static void test_capacity_and_spill(void) {
    tu_instruction_t one = I(TU_ISA_DMA_LOAD, 0, 100, 0, 0, 0);
    tu_live_config_t cfg = tu_live_config_default;
    cfg.w_capacity = 16; cfg.safety_margin = 32; cfg.enable_spilling = false;
    tu_allocated_sequence_t out;
    CHECK(tu_live_allocate(&one, 1, &cfg, &out) == 0, "underflow allocation");
    printf("LIVE_CAP_UNDERFLOW capacity=%u margin=%u valid=%d peak=%u out_n=%u off=%u\n",
           cfg.w_capacity, cfg.safety_margin, out.valid, out.peak_w_usage,
           out.num_instructions, out.instructions[0].dim0);
    CHECK(out.valid && out.peak_w_usage == 100, "underflow creates apparent capacity");

    tu_instruction_t spill_seq[] = {
        I(TU_ISA_DMA_LOAD, 0, 16, 0, 0, 0),
        I(TU_ISA_DMA_STORE, 0, 16, 0, 0, 0),
    };
    cfg = tu_live_config_default;
    cfg.w_capacity = 8; cfg.safety_margin = 0; cfg.enable_spilling = true;
    CHECK(tu_live_allocate(spill_seq, 2, &cfg, &out) == 0, "spill sequence allocation");
    print_ops("spill_sequence", out.instructions, out.num_instructions);
    CHECK(out.valid && out.num_instructions == 4, "spill sequence length");
    CHECK(out.instructions[1].opcode == TU_ISA_DMA_LOAD && out.instructions[1].dim0 == UINT16_MAX,
          "fill uses unassigned offset");
    CHECK(out.instructions[3].opcode == TU_ISA_DMA_STORE && out.instructions[3].dim0 == UINT16_MAX,
          "spill occurs after last use with unassigned offset");

    tu_instruction_t attention = I(TU_ISA_ATTENTION, 0, 1, 0, 0, 0);
    cfg.o_capacity = 8;
    CHECK(tu_live_allocate(&attention, 1, &cfg, &out) == 0, "attention spill allocation");
    print_ops("attention_size_truncation", out.instructions, out.num_instructions);
    CHECK(out.num_instructions == 2 && out.instructions[1].opcode == TU_ISA_DMA_STORE &&
          out.instructions[1].dim0 == UINT16_MAX && out.instructions[1].dim1 == 0,
          "65536-byte spill truncates to zero");
}

static void test_no_spill_alias_and_patch(void) {
    tu_liveness_result_t r;
    memset(&r, 0, sizeof(r));
    r.num_vregs = 2;
    for (uint32_t i = 0; i < 2; ++i) {
        r.vregs[i].id = i + 1; r.vregs[i].region = TU_VREG_W;
        r.vregs[i].size_bytes = 16; r.vregs[i].first_def = (int32_t)i;
        r.vregs[i].last_use = 2; r.vregs[i].physical_offset = UINT32_MAX;
        r.graph_w.vregs[i] = &r.vregs[i];
    }
    r.graph_w.num_vregs = 2;
    r.graph_w.interference = calloc(4, sizeof(bool));
    CHECK(r.graph_w.interference != NULL, "manual graph allocation");
    r.graph_w.interference[1] = true; r.graph_w.interference[2] = true;
    tu_live_config_t cfg = tu_live_config_default;
    cfg.w_capacity = 16; cfg.safety_margin = 0; cfg.enable_spilling = false;
    tu_live_color(&r, &cfg);
    printf("LIVE_NO_SPILL offsets=%u,%u colored=%d spills=%u\n",
           r.vregs[0].physical_offset, r.vregs[1].physical_offset,
           r.graph_w.colored, r.num_spills);
    CHECK(r.vregs[0].physical_offset == 0 && r.vregs[1].physical_offset == 0 &&
          r.graph_w.colored && r.num_spills == 0,
          "no-spill force aliases but reports colored");
    free_graphs(&r);

    tu_instruction_t seq[] = {
        I(TU_ISA_DMA_LOAD, 0, 16, 0, 0, 0),
        I(TU_ISA_DMA_LOAD, 100, 16, 0, 0, 0),
        I(TU_ISA_MMA, 0, 1, 1, 0, 0),
    };
    CHECK(tu_live_analyze(seq, 3, &r) == 0, "patch analysis");
    r.vregs[0].physical_offset = 32;
    r.vregs[1].physical_offset = 64;
    for (uint32_t i = 2; i < r.num_vregs; ++i)
        r.vregs[i].physical_offset = 96 + 16 * i;
    tu_allocated_sequence_t out;
    CHECK(tu_live_apply(&r, seq, 3, &cfg, &out) == 0, "manual patch apply");
    print_ops("wrong_value_patch", out.instructions, out.num_instructions);
    CHECK(out.instructions[2].opcode == TU_ISA_MMA && out.instructions[2].dim0 == 128,
          "MMA W operand patched to newest disjoint value");
}

static void test_output_truncation(void) {
    const uint32_t n = 301;
    tu_instruction_t *seq = calloc(n, sizeof(*seq));
    CHECK(seq != NULL, "long sequence allocation");
    seq[0] = I(TU_ISA_DMA_LOAD, 0, 16, 0, 0, 0);
    for (uint32_t i = 1; i + 1 < n; ++i) seq[i] = I(TU_ISA_NOP, (uint16_t)i, 0, 0, 0, 0);
    seq[n - 1] = I(TU_ISA_DMA_STORE, 0, 16, 0, 0, 0);
    tu_live_config_t cfg = tu_live_config_default;
    cfg.w_capacity = 8; cfg.safety_margin = 0; cfg.enable_spilling = true;
    tu_allocated_sequence_t out;
    int rc = tu_live_allocate(seq, n, &cfg, &out);
    printf("LIVE_OUTPUT_LIMIT input=%u rc=%d valid=%d output=%u last_opcode=%s last_dim0=%u\n",
           n, rc, out.valid, out.num_instructions,
           out.num_instructions ? tu_isa_opcode_name((tu_isa_opcode_t)out.instructions[out.num_instructions - 1].opcode) : "NONE",
           out.num_instructions ? out.instructions[out.num_instructions - 1].dim0 : 0);
    CHECK(rc == 0 && out.valid && out.num_instructions == TU_SCHED_MAX_INSTRS * 2,
          "output cap returns valid");
    CHECK(out.instructions[out.num_instructions - 1].opcode == TU_ISA_NOP,
          "input suffix and final store omitted");
    free(seq);
}

int main(void) {
    test_scheduler_policy_and_barrier();
    test_scheduler_analysis_and_validation();
    test_scheduler_additional_boundaries();
    test_cross_pass_access();
    test_liveness_binding_and_limits();
    test_capacity_and_spill();
    test_no_spill_alias_and_patch();
    test_output_truncation();
    printf("CH19_PROBE SUMMARY failures=%d\n", failures);
    return failures ? 1 : 0;
}
