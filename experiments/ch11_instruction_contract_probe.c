#include "tu_cmodel/tu_cmodel.h"
#include "tu_cmodel/isa/tu_isa.h"
#include "tu_cmodel/isa/tu_scheduler.h"

#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int failures;

#define CHECK(cond, label) do { \
    if (!(cond)) { \
        fprintf(stderr, "CHECK FAIL: %s\n", label); \
        failures++; \
    } else { \
        printf("CHECK PASS: %s\n", label); \
    } \
} while (0)

static tu_instruction_t instr(tu_isa_opcode_t op, uint16_t d0,
                              uint16_t d1, uint16_t d2,
                              uint8_t flags, uint32_t imm) {
    tu_instruction_t x;
    memset(&x, 0, sizeof(x));
    x.opcode = (uint8_t)op;
    x.flags = flags;
    x.dim0 = d0;
    x.dim1 = d1;
    x.dim2 = d2;
    x.immediates = imm;
    return x;
}

static void probe_isa_surface(void) {
    unsigned named = 0, unknown = 0;
    for (int i = 0; i < TU_ISA_OPCODE_COUNT; i++) {
        const char *n = tu_isa_opcode_name((tu_isa_opcode_t)i);
        if (strcmp(n, "UNKNOWN") == 0) unknown++;
        else named++;
    }

    tu_instruction_t x = instr(TU_ISA_MMA, 0x1122, 0x3344, 0x5566,
                               0xa5, 0x778899aaU);
    const uint8_t *b = (const uint8_t *)&x;
    printf("ISA sizeof=%zu opcode_count_sentinel=%d named_slots=%u unknown_slots=%u\n",
           sizeof(x), TU_ISA_OPCODE_COUNT, named, unknown);
    printf("ISA native_bytes=");
    for (size_t i = 0; i < sizeof(x); i++) printf("%02x%s", b[i], i + 1 == sizeof(x) ? "\n" : " ");

    CHECK(sizeof(x) == 12, "instruction object is 12 bytes");
    CHECK(TU_ISA_OPCODE_COUNT == 128 && named == 68 && unknown == 60,
          "catalog has exact 128-slot sentinel, 68 named slots, and 60 unknown slots");
    static const uint8_t expected_le[] = {
        0x10, 0xa5, 0x22, 0x11, 0x44, 0x33,
        0x66, 0x55, 0xaa, 0x99, 0x88, 0x77,
    };
    const uint16_t endian_probe = 1;
    CHECK(*(const uint8_t *)&endian_probe == 1, "audit host is little-endian");
    CHECK(memcmp(b, expected_le, sizeof(expected_le)) == 0,
          "native packed-object bytes match the audited little-endian ABI snapshot");
    CHECK(tu_isa_opcode_category((tu_isa_opcode_t)0x0f) == TU_ISA_CAT_UNKNOWN,
          "reserved control-range slot 0x0f is category UNKNOWN");
    CHECK(tu_isa_has_sram_operands((tu_isa_opcode_t)0x0f),
          "generic SRAM query defaults reserved slot 0x0f to true");
}

static void probe_sync_queue(void) {
    tu_command_queue_t *cq = tu_cmdq_create(4, true);
    CHECK(cq != NULL && cq->capacity == 4, "synchronous queue created at requested capacity");
    if (!cq) return;

    uint32_t missing_dep = 9999, id1 = 0, id2 = 0;
    int rc1 = tu_cmdq_submit(cq, TU_CMD_NOP, NULL, 1, &missing_dep, &id1);
    CHECK(rc1 == (int)id1 && rc1 > 0, "submit returns command ID rather than documented zero");
    CHECK(tu_cmdq_get_status(cq, id1) == TU_CMD_COMPLETED,
          "synchronous submit executes despite missing dependency");
    CHECK(cq->count == 1 && tu_cmdq_get_depth(cq) == 1,
          "completed synchronous command remains counted in queue depth");
    CHECK(cq->signal_count == 0 && cq->commands[0].signal_id > 0,
          "command gets signal ID but signal registry remains empty");

    int rc2 = tu_cmdq_submit(cq, TU_ISA_CONV2D, NULL, 0, NULL, &id2);
    CHECK(rc2 == (int)id2 && tu_cmdq_get_status(cq, id2) == TU_CMD_FAULTED,
          "declared CONV2D faults in command-queue dispatcher");
    CHECK(cq->total_faulted == 1 && cq->total_completed == 1,
          "faulted command is separate from completed counter");

    CHECK(tu_cmdq_get_status(cq, 0xfeedU) == TU_CMD_COMPLETED,
          "unknown command status is reported as COMPLETED");
    CHECK(tu_cmdq_wait(cq, 0xfeedU, 1) == 0,
          "wait on unknown command reports success");

    uint32_t id3 = 0, id4 = 0;
    CHECK(tu_cmdq_submit(cq, TU_CMD_NOP, NULL, 0, NULL, &id3) > 0,
          "third synchronous command accepted");
    CHECK(tu_cmdq_submit(cq, TU_CMD_NOP, NULL, 0, NULL, &id4) > 0,
          "fourth synchronous command accepted");
    CHECK(tu_cmdq_submit(cq, TU_CMD_NOP, NULL, 0, NULL, NULL) == -1,
          "queue rejects after lifetime submissions reach capacity");
    tu_cmdq_sync(cq);
    CHECK(cq->count == 4, "synchronous sync is a no-op and does not retire completed commands");

    printf("SYNC_QUEUE count=%u submitted=%" PRIu64 " completed=%" PRIu64
           " faulted=%" PRIu64 " signal_count=%u current_cycle=%" PRIu64 "\n",
           cq->count, cq->total_submitted, cq->total_completed,
           cq->total_faulted, cq->signal_count, cq->current_cycle);

    uint32_t first_signal = cq->commands[0].signal_id, reset_id = 0;
    tu_cmdq_reset(cq);
    CHECK(tu_cmdq_submit(cq, TU_CMD_NOP, NULL, 0, NULL, &reset_id) > 0 && reset_id == 1,
          "reset reuses command ID 1");
    CHECK(cq->commands[0].signal_id > first_signal,
          "reset does not restart next signal ID");
    CHECK(tu_cmdq_get_status(cq, id1) == TU_CMD_COMPLETED,
          "stale pre-reset command ID aliases the new command with reused ID");
    printf("RESET_IDS old_cmd=%u new_cmd=%u old_signal=%u new_signal=%u\n",
           id1, reset_id, first_signal, cq->commands[0].signal_id);
    tu_cmdq_destroy(cq);
}

static void probe_async_queue(void) {
    tu_command_queue_t *cq = tu_cmdq_create(4, false);
    CHECK(cq != NULL && !cq->synchronous, "tick-driven queue created");
    if (!cq) return;

    uint32_t id1 = 0, id2 = 0, missing_dep = 123456;
    int rc1 = tu_cmdq_submit(cq, TU_CMD_NOP, NULL, 0, NULL, &id1);
    CHECK(rc1 == (int)id1 && tu_cmdq_get_status(cq, id1) == TU_CMD_COMPLETED,
          "tick-driven submit auto-ticks and completes ready NOP in submit call");
    CHECK(cq->current_cycle == 1 && cq->count == 1,
          "auto-tick advances one cycle but does not retire queue storage");
    CHECK(tu_cmdq_tick(cq) == 0 && cq->count == 1,
          "later tick reports no execution and still does not retire completed command");

    int rc2 = tu_cmdq_submit(cq, TU_CMD_NOP, NULL, 1, &missing_dep, &id2);
    CHECK(rc2 == (int)id2 && tu_cmdq_get_status(cq, id2) == TU_CMD_COMPLETED,
          "missing dependency is assumed already completed in tick-driven mode");
    CHECK(cq->commands[0].cycle_completed == 1 && cq->commands[1].cycle_completed == 3,
          "completion timestamp is the executor tick, with no service duration");
    CHECK(cq->signal_count == 0, "tick-driven completion signal registry also remains empty");

    printf("ASYNC_QUEUE count=%u submitted=%" PRIu64 " completed=%" PRIu64
           " faulted=%" PRIu64 " signal_count=%u current_cycle=%" PRIu64 "\n",
           cq->count, cq->total_submitted, cq->total_completed,
           cq->total_faulted, cq->signal_count, cq->current_cycle);
    tu_cmdq_destroy(cq);
}

static void probe_queue_barrier(void) {
    tu_command_queue_t *cq = tu_cmdq_create(8, false);
    CHECK(cq != NULL, "barrier probe queue created");
    if (!cq) return;

    uint32_t fault_id = 0, pre_id = 0, barrier_id = 0, post_id = 0;
    CHECK(tu_cmdq_submit(cq, TU_ISA_CONV2D, NULL, 0, NULL, &fault_id) > 0 &&
          tu_cmdq_get_status(cq, fault_id) == TU_CMD_FAULTED,
          "barrier probe creates retained faulted predecessor");
    CHECK(tu_cmdq_submit(cq, TU_CMD_NOP, NULL, 1, &fault_id, &pre_id) > 0 &&
          tu_cmdq_get_status(cq, pre_id) == TU_CMD_PENDING,
          "command before barrier remains pending on faulted dependency");
    CHECK(tu_cmdq_wait(cq, pre_id, 2) == -1 &&
          tu_cmdq_get_status(cq, pre_id) == TU_CMD_PENDING,
          "bounded wait times out on retained fault dependency");
    CHECK(tu_cmdq_barrier(cq) > 0, "barrier submission succeeds");
    barrier_id = cq->last_barrier_id;
    CHECK(tu_cmdq_get_status(cq, barrier_id) == TU_CMD_COMPLETED &&
          tu_cmdq_get_status(cq, pre_id) == TU_CMD_PENDING,
          "barrier completes while an earlier command remains pending");
    CHECK(tu_cmdq_submit(cq, TU_CMD_NOP, NULL, 0, NULL, &post_id) > 0 &&
          tu_cmdq_get_status(cq, post_id) == TU_CMD_COMPLETED &&
          tu_cmdq_get_status(cq, pre_id) == TU_CMD_PENDING,
          "post-barrier command completes before earlier pending command");
    printf("ASYNC_BARRIER fault=%d pre=%d barrier=%d post=%d count=%u cycle=%" PRIu64 "\n",
           tu_cmdq_get_status(cq, fault_id), tu_cmdq_get_status(cq, pre_id),
           tu_cmdq_get_status(cq, barrier_id), tu_cmdq_get_status(cq, post_id),
           cq->count, cq->current_cycle);
    tu_cmdq_destroy(cq);
}

static void probe_elementwise_count_boundary(void) {
    tu_command_queue_t *cq = tu_cmdq_create(4, true);
    CHECK(cq != NULL, "elementwise boundary queue created");
    if (!cq) return;

    tu_cmd_ew_desc_t ew;
    memset(&ew, 0, sizeof(ew));
    ew.elem_count = 1;
    ew.num_ops = 9;
    uint32_t id = 0;
    CHECK(tu_cmdq_submit(cq, TU_CMD_ELEMENTWISE, &ew, 0, NULL, &id) > 0,
          "nine-operation elementwise descriptor is admitted");
    CHECK(tu_cmdq_get_status(cq, id) == TU_CMD_COMPLETED &&
          cq->total_completed == 1 && cq->total_faulted == 0,
          "downstream fused helper rejects count above eight but queue still reports COMPLETED");
    printf("ELEMENTWISE_BOUNDARY count=%u status=%d completed=%" PRIu64
           " faulted=%" PRIu64 "\n",
           ew.num_ops, tu_cmdq_get_status(cq, id),
           cq->total_completed, cq->total_faulted);
    tu_cmdq_destroy(cq);
}

static void probe_scheduler_boundary(void) {
    tu_instruction_t seq[] = {
        instr(TU_ISA_NOP, 0, 0, 0, 0, 0),
        instr(TU_ISA_BARRIER, 0, 0, 0, 0, 0),
        instr(TU_ISA_DMA_LOAD, 0, 16, 0, 0, 0),
    };
    tu_sched_config_t cfg = tu_sched_config_default;
    tu_sched_result_t result;
    memset(&result, 0, sizeof(result));
    int rc = tu_sched_run(seq, 3, &cfg, &result);
    CHECK(rc == 0 && result.num_instructions == 3, "scheduler emits all three instructions");
    printf("SCHED_BARRIER output=%s,%s,%s valid=%d hoisted=%u inserted=%u cycles=%u\n",
           tu_isa_opcode_name((tu_isa_opcode_t)result.instructions[0].opcode),
           tu_isa_opcode_name((tu_isa_opcode_t)result.instructions[1].opcode),
           tu_isa_opcode_name((tu_isa_opcode_t)result.instructions[2].opcode),
           result.valid, result.num_dma_hoisted,
           result.num_barriers_inserted, result.estimated_cycles);
    CHECK(result.instructions[0].opcode == TU_ISA_DMA_LOAD &&
          result.instructions[2].opcode == TU_ISA_BARRIER,
          "post-barrier independent DMA can be emitted before barrier");
    CHECK(result.num_dma_hoisted == 0 && result.num_barriers_inserted == 0,
          "list scheduler clears reported hoist and insertion counts");

    tu_sched_graph_t graph;
    memset(&graph, 0, sizeof(graph));
    tu_instruction_t pipeline[] = {
        instr(TU_ISA_DMA_LOAD, 0, 64, 0, 0, 0),
        instr(TU_ISA_MMA, 16, 16, 16, 0, 0),
        instr(TU_ISA_DMA_STORE, 0, 64, 0, 2, 0),
    };
    CHECK(tu_sched_build_dag(&graph, pipeline, 3, &cfg) == 0,
          "scheduler DAG builds for DMA-MMA-store sequence");
    int counted = tu_sched_insert_barriers(&graph);
    printf("SCHED_INSERT_ANALYSIS counted=%d graph_nodes=%u\n", counted, graph.num_nodes);
    CHECK(graph.num_nodes == 3, "barrier insertion analysis does not insert an instruction");

    tu_instruction_t positive_barrier[] = {
        instr(TU_ISA_DMA_STORE, 0, 64, 0, 2, 0),
        instr(TU_ISA_ELEMENTWISE, 0, 16, 0, 0, 0),
    };
    memset(&graph, 0, sizeof(graph));
    CHECK(tu_sched_build_dag(&graph, positive_barrier, 2, &cfg) == 0,
          "positive barrier-analysis graph builds");
    counted = tu_sched_insert_barriers(&graph);
    CHECK(counted == 1 && graph.num_nodes == 2,
          "barrier analysis reports one hazard without inserting a node");
    memset(&result, 0, sizeof(result));
    CHECK(tu_sched_run(positive_barrier, 2, &cfg, &result) == 0 &&
          result.num_barriers_inserted == 0 && result.num_instructions == 2,
          "full scheduler erases positive barrier-analysis report and emits no added instruction");
    printf("SCHED_POSITIVE_INSERT direct=%d run=%u input_nodes=2 output_nodes=%u\n",
           counted, result.num_barriers_inserted, result.num_instructions);

    tu_instruction_t positive_hoist[] = {
        instr(TU_ISA_MMA, 0, 16, 16, 0, 0),
        instr(TU_ISA_NOP, 0, 0, 0, 0, 0),
        instr(TU_ISA_DMA_LOAD, 0, 64, 0, 0, 0),
    };
    memset(&graph, 0, sizeof(graph));
    CHECK(tu_sched_build_dag(&graph, positive_hoist, 3, &cfg) == 0,
          "positive DMA-hoist analysis graph builds");
    int hoisted = tu_sched_hoist_dma(&graph);
    CHECK(hoisted == 1 && graph.nodes[2].id == 2,
          "DMA-hoist analysis reports one candidate without moving graph nodes");
    memset(&result, 0, sizeof(result));
    CHECK(tu_sched_run(positive_hoist, 3, &cfg, &result) == 0 &&
          result.num_dma_hoisted == 0 && result.num_instructions == 3,
          "full scheduler erases positive DMA-hoist report");
    printf("SCHED_POSITIVE_HOIST direct=%d run=%u input_nodes=3 output_nodes=%u\n",
           hoisted, result.num_dma_hoisted, result.num_instructions);

    tu_instruction_t dense[18];
    for (unsigned i = 0; i < 17; i++)
        dense[i] = instr(TU_ISA_NOP, 0, 0, 0, 0, 0);
    dense[17] = instr(TU_ISA_BARRIER, 0, 0, 0, 0, 0);
    memset(&graph, 0, sizeof(graph));
    CHECK(tu_sched_build_dag(&graph, dense, 18, &cfg) == 0,
          "17-predecessor barrier graph builds without rejection");
    CHECK(graph.nodes[17].num_preds == TU_SCHED_MAX_DEPS &&
          TU_SCHED_MAX_DEPS == 16,
          "barrier silently retains only 16 of 17 required predecessor edges");
    printf("SCHED_DENSE_BARRIER prior=17 retained_preds=%u max_deps=%u\n",
           graph.nodes[17].num_preds, TU_SCHED_MAX_DEPS);
}

static void probe_asm_surface(void) {
    static const char unsupported[] = "BARRIER\n";
    int rc = tu_run_asm(unsupported, NULL, 0);
    printf("ASM expanded_mnemonic_rc=%d\n", rc);
    CHECK(rc == -1, "legacy text interpreter rejects expanded BARRIER mnemonic");
}

int main(void) {
    probe_isa_surface();
    probe_sync_queue();
    probe_async_queue();
    probe_queue_barrier();
    probe_elementwise_count_boundary();
    probe_scheduler_boundary();
    probe_asm_surface();
    printf("CH11_PROBE SUMMARY failures=%d\n", failures);
    return failures ? 1 : 0;
}
