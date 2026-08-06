#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "tu_cmodel/tu_cmodel.h"
#include "tu_cmodel/tu_core.h"
#include "tu_cmodel/infra/tu_context.h"
#include "tu_cmodel/command_queue.h"
#include "tu_cmodel/dma_descriptor.h"
#include "tu_cmodel/memory/double_buffer.h"
#include "tu_cmodel/compute/dataflow/dataflow_interface.h"
#include "tu_cmodel/compute/dataflow/dataflow_registry.h"
#include "tu_cmodel/rounding.h"

static int failures;
#define CHECK(c, m) do { if (!(c)) { printf("CHECK_FAIL %s\n", (m)); failures++; } } while (0)

/* Link with -Wl,--wrap=malloc. This injects failures only into the three
 * context-save malloc calls; setup uses calloc and runs while disarmed. */
void *__real_malloc(size_t);
static int malloc_armed;
static int malloc_fail_at;
static int malloc_seen;
static size_t malloc_sizes[8];
void *__wrap_malloc(size_t n) {
    if (malloc_armed) {
        ++malloc_seen;
        if (malloc_seen <= 8) malloc_sizes[malloc_seen - 1] = n;
        if (malloc_seen == malloc_fail_at) return NULL;
    }
    return __real_malloc(n);
}
static void arm_malloc_failure(int ordinal) {
    malloc_seen = 0;
    malloc_fail_at = ordinal;
    memset(malloc_sizes, 0, sizeof(malloc_sizes));
    malloc_armed = 1;
}
static void disarm_malloc_failure(void) { malloc_armed = 0; }

typedef struct {
    tu_core_t *core;
    tu_ctx_manager_t *mgr;
} env_t;

static tu_runtime_config_t tiny_runtime(void) {
    tu_runtime_config_t rt = tu_runtime_config_default();
    rt.sram_w_size = 64;
    rt.sram_a_size = 64;
    rt.sram_o_size = 64;
    return rt;
}

static tu_ctx_manager_config_t base_cfg(void) {
    tu_ctx_manager_config_t c;
    memset(&c, 0, sizeof(c));
    c.max_contexts = 4;
    c.sched_policy = TU_CTX_SCHED_ROUND_ROBIN;
    c.switch_overhead = 7;
    c.save_scope = TU_CTX_SAVE_FULL_SRAM;
    c.state_bytes_per_cycle = 32;
    return c;
}

static env_t env_make(const tu_ctx_manager_config_t *cfg) {
    env_t e = {0};
    tu_runtime_config_t rt = tiny_runtime();
    e.core = tu_core_create(&rt);
    e.mgr = tu_ctx_manager_create(e.core, cfg);
    CHECK(e.core != NULL && e.mgr != NULL, "environment creation");
    return e;
}

static void env_drop(env_t *e) {
    disarm_malloc_failure();
    if (e->mgr) tu_ctx_manager_destroy(e->mgr);
    if (e->core && e->core->state.cmdq) {
        tu_cmdq_destroy(e->core->state.cmdq);
        e->core->state.cmdq = NULL;
    }
    tu_dma_destroy();
    tu_dataflow_registry_destroy();
    if (e->core) tu_core_destroy(e->core);
    e->mgr = NULL;
    e->core = NULL;
}

static unsigned active_descriptors(const tu_ctx_manager_t *m) {
    unsigned n = 0;
    if (!m) return 0;
    for (uint32_t i = 0; i < m->max_contexts; ++i)
        if (m->contexts[i].state == TU_CTX_ACTIVE) ++n;
    return n;
}

static uint64_t mix_u64(uint64_t h, uint64_t v) {
    h ^= v; return h * UINT64_C(1099511628211);
}

static uint64_t bytes_digest(const void *ptr,size_t n) {
    const unsigned char *p=ptr; uint64_t h=UINT64_C(1469598103934665603);
    for (size_t i=0;i<n;i++) h=mix_u64(h,p[i]);
    return h;
}

static uint64_t command_digest(const tu_command_queue_t *q) {
    uint64_t h = UINT64_C(1469598103934665603);
    if (!q) return 0;
    for (uint32_t i = 0; i < q->capacity; ++i) {
        const tu_command_t *c = &q->commands[i];
        const uint64_t vals[] = {c->cmd_id, c->opcode, c->status, c->num_deps,
                                 c->max_deps, c->signal_id, c->cycle_submitted,
                                 c->cycle_completed, c->is_barrier,
                                 c->op.dma.channel, c->op.dma.is_store,
                                 c->op.dma.sram_offset, c->op.dma.size_bytes,
                                 c->op.dma.host_ptr != NULL};
        for (size_t j = 0; j < sizeof(vals)/sizeof(vals[0]); ++j) h=mix_u64(h,vals[j]);
        for (uint32_t j=0; j<c->num_deps; ++j) h=mix_u64(h,c->dep_ids[j]);
    }
    for (uint32_t i=0; i<q->signal_capacity; ++i) {
        h=mix_u64(h,q->signals[i].signal_id);
        h=mix_u64(h,q->signals[i].fired);
        h=mix_u64(h,q->signals[i].cycle_completed);
    }
    return h;
}

static void print_runtime_surface(const char *row, const char *phase, const char *tag,
                                  const tu_runtime_config_t *r) {
    printf("SURFACE %s %s %s=%u,%u,%u,%u,%u,%d,%d,%d,%s,%d,%.17g,%d,%d,%d,%u,%u\n",
           row,phase,tag,r->pe_rows,r->pe_cols,r->sram_w_size,r->sram_a_size,r->sram_o_size,
           r->counters_enabled,r->detailed_stalls,r->trace_enabled,r->trace_file,
           r->verify_enabled,r->verify_tolerance,r->icc_switching_mode,
           r->icc_contention_mode,r->icc_mesh_routing_mode,
           r->icc_link_bytes_per_cycle,r->icc_router_latency_cycles);
}

static void print_region_surface(const char *row, const char *phase, const char *tag,
                                 const tu_sram_region_t *r) {
    const tu_sram_bank_t *b=&r->banks;
    printf("SURFACE %s %s %s meta=%u,%u,%u,%" PRIu64 ",%" PRIu64 ",%" PRIu64
           ",%" PRIu64 ",%d,%u,%u,%u,%" PRIu64 ",%" PRIu64 ",%u,%s,%d data=",
           row,phase,tag,b->size,b->bank_count,b->bank_width,b->reads,b->writes,b->conflicts,
           b->stall_cycles,b->bw_modeling,b->words_per_cycle,b->arb_mode,b->stall_penalty,
           b->bw_refill_window,b->current_cycle,r->total_size,r->name?r->name:"-",r->db!=NULL);
    for (uint32_t i=0;i<b->size;i++) printf("%02x",b->data?b->data[i]:0);
    for (uint32_t i=0;i<b->bank_count;i++) {
        const tu_sram_bw_bank_t *x=b->bw_banks?&b->bw_banks[i]:NULL;
        printf(" b%u=%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64,
               i,x?x->words_available:-999,x?x->last_refill_cycle:0,x?x->reads_served:0,
               x?x->writes_served:0,x?x->read_stalls:0,x?x->write_stalls:0,
               x?x->total_cycles_used:0);
    }
    putchar('\n');
}

static void print_queue_surface(const char *row,const char *phase,const tu_command_queue_t *q) {
    printf("SURFACE %s %s queue ptrs=%d,%d scalars=%u,%u,%u,%u,%u,%u,%" PRIu64
           ",%" PRIu64 ",%" PRIu64 ",%u,%u,%u,%" PRIu64 ",%d digest=%" PRIu64,
           row,phase,q&&q->commands,q&&q->signals,q?q->capacity:0,q?q->head:0,q?q->tail:0,
           q?q->count:0,q?q->next_cmd_id:0,q?q->next_signal_id:0,q?q->total_submitted:0,
           q?q->total_completed:0,q?q->total_faulted:0,q?q->signal_capacity:0,
           q?q->signal_count:0,q?q->last_barrier_id:0,q?q->current_cycle:0,q?q->synchronous:0,
           command_digest(q));
    if (q) for (uint32_t i=0;i<q->capacity;i++) {
        const tu_command_t *c=&q->commands[i];
        printf(" c%u=%u,%d,%d,%u,%u,%d,%u,%" PRIu64 ",%" PRIu64 ",%d",
               i,c->cmd_id,c->opcode,c->status,c->num_deps,c->max_deps,c->dep_ids!=NULL,
               c->signal_id,c->cycle_submitted,c->cycle_completed,c->is_barrier);
        for (uint32_t j=0;j<c->num_deps;j++) printf(".d%u=%u",j,c->dep_ids[j]);
    }
    if (q) for (uint32_t i=0;i<q->signal_capacity;i++)
        printf(" s%u=%u,%d,%" PRIu64,i,q->signals[i].signal_id,q->signals[i].fired,
               q->signals[i].cycle_completed);
    putchar('\n');
}

static void print_vec(const char *row, const char *phase, const env_t *e, int rc) {
    const tu_ctx_manager_t *m = e->mgr;
    const tu_state_t *s = &e->core->state;
    const tu_command_queue_t *q = s->cmdq;
    const tu_sram_region_t *w = &s->sram_w;
    const tu_sram_bw_bank_t *b0 = w->banks.bw_banks;
    printf("ROW %s %s rc=%d mgr=%u/%u/%u/%u slice=%" PRIu64 "/%u pending=%" PRIu64
           " switches=%" PRIu64 "/%" PRIu64 " scope=%d live=%u/%u/%u fixed=%" PRIu64 "/%u",
           row, phase, rc, m->active_count, m->active_ctx_id,
           active_descriptors(m), m->max_contexts, m->slice_cycles_used,
           m->slice_cmds_used, m->pending_save_bytes, m->total_switches,
           m->total_cycles_stolen, (int)m->save_scope, m->live_w_bytes,
           m->live_a_bytes, m->live_o_bytes, m->switch_fixed_cycles,
           m->state_bytes_per_cycle);
    for (uint32_t i = 0; i < m->max_contexts; ++i) {
        const tu_context_desc_t *c = &m->contexts[i];
        printf(" c%u=%d,%u,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
               ",%" PRIu64 ",%u,%u,%u,%d,%u,%d,%d",
               i, (int)c->state, c->priority, c->total_cycles,
               c->total_commands, c->switch_count, c->last_switch_cycle,
               c->saved_sram_bytes, c->saved_w_bytes, c->saved_a_bytes,
               c->saved_o_bytes, c->has_config_override,
               c->config_override.pe_rows, c->user_data != NULL,
               c->hw_state.sram_w.banks.data != NULL);
    }
    printf(" core=%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
           " rt=%u,%u,%u,%u df=%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64
           " W=%02x/%02x,%u,%u,%u,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%d,%u,%u,%u,%" PRIu64 ",%d",
           s->initialized, s->total_dma_bytes, s->total_mma_calls,
           s->total_mma_tiles, s->total_mma_flops, s->estimated_cycles,
           s->rt_cfg.pe_rows, s->rt_cfg.pe_cols, s->rt_cfg.sram_w_size,
           s->rt_cfg.sram_a_size, s->dataflow ? (int)s->dataflow->id : -1,
           s->dataflow ? s->dataflow->total_flops : 0,
           s->dataflow ? s->dataflow->total_tiles : 0,
           s->dataflow ? s->dataflow->total_cycles : 0,
           w->banks.data ? w->banks.data[0] : 0,
           w->banks.data ? w->banks.data[8] : 0, w->banks.size,
           w->banks.bank_count, w->banks.bank_width, w->banks.reads,
           w->banks.writes, w->banks.conflicts, w->banks.bw_modeling,
           w->banks.words_per_cycle, w->banks.arb_mode,
           w->banks.stall_penalty, w->banks.current_cycle, w->db != NULL);
    printf(" bank0=%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
           " q=%u,%u,%u,%u,%u,%u,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%u,%" PRIu64 ",%d,%" PRIu64,
           b0 ? b0[0].words_available : -999,
           b0 ? b0[0].last_refill_cycle : 0,
           b0 ? b0[0].reads_served : 0, b0 ? b0[0].writes_served : 0,
           b0 ? b0[0].read_stalls : 0, b0 ? b0[0].write_stalls : 0,
           q ? q->capacity : 0, q ? q->head : 0, q ? q->tail : 0,
           q ? q->count : 0, q ? q->next_cmd_id : 0,
           q ? q->next_signal_id : 0, q ? q->total_submitted : 0,
           q ? q->total_completed : 0, q ? q->total_faulted : 0,
           q ? q->signal_count : 0, q ? q->current_cycle : 0,
           q ? q->synchronous : 0, command_digest(q));
    printf(" edma=%u,%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%u",
           s->dma.num_channels, s->dma.async_mode, s->dma.current_cycle,
           s->dma.total_bytes, s->dma.total_transfers, s->dma.estimated_cycles,
           s->dma.channels[0].queue_depth);
    printf(" gdma=%u,%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
           ",%u round=%d subnormal=%d outer=%u,%d,%d,%u\n",
           g_tu_dma.num_channels, g_tu_dma.async_mode, g_tu_dma.current_cycle,
           g_tu_dma.total_bytes, g_tu_dma.total_transfers,
           g_tu_dma.estimated_cycles, g_tu_dma.channels[0].queue_depth,
           (int)tu_get_rounding_mode(),(int)tu_get_subnormal_mode(),e->core->core_id,
           e->core->initialized,e->core->icc_buffer!=NULL,e->core->icc_buffer_size);
    print_runtime_surface(row,phase,"runtime",&s->rt_cfg);
    print_region_surface(row,phase,"W",&s->sram_w);
    print_region_surface(row,phase,"A",&s->sram_a);
    print_region_surface(row,phase,"O",&s->sram_o);
    print_queue_surface(row,phase,q);
    for (uint32_t i=0;i<m->max_contexts;i++) {
        const tu_context_desc_t *c=&m->contexts[i];
        printf("SURFACE %s %s c%u_identity=%u override_hash=%" PRIu64
               " owner=%d,%d,%d cmdq_same=%d dataflow_same=%d\n",
               row,phase,i,c->ctx_id,bytes_digest(&c->config_override,sizeof(c->config_override)),
               c->hw_state.sram_w.banks.data!=NULL,
               c->hw_state.sram_a.banks.data!=NULL,c->hw_state.sram_o.banks.data!=NULL,
               c->hw_state.cmdq==q,c->hw_state.dataflow==s->dataflow);
    }
}

static void fill_runtime(tu_runtime_config_t *rt, unsigned tag) {
    memset(rt, 0, sizeof(*rt));
    rt->pe_rows = (uint16_t)(10 + tag);
    rt->pe_cols = (uint16_t)(20 + tag);
    rt->sram_w_size = 100 + tag;
    rt->sram_a_size = 200 + tag;
    rt->sram_o_size = 300 + tag;
    rt->counters_enabled = (tag & 1u) != 0;
    rt->detailed_stalls = (tag & 2u) != 0;
    rt->trace_enabled = true;
    snprintf(rt->trace_file, sizeof(rt->trace_file), "context-%u.trace", tag);
    rt->verify_enabled = true;
    rt->verify_tolerance = (double)tag / 16.0;
    rt->icc_switching_mode = (int)(tag + 1);
    rt->icc_contention_mode = (int)(tag + 2);
    rt->icc_mesh_routing_mode = (int)(tag + 3);
    rt->icc_link_bytes_per_cycle = 400 + tag;
    rt->icc_router_latency_cycles = 500 + tag;
}

static void test_null_api(void) {
    tu_ctx_manager_config_t c = base_cfg();
    int alloc=tu_ctx_alloc(NULL), save=tu_ctx_save(NULL), restore=tu_ctx_restore(NULL,0);
    int sw=tu_ctx_switch(NULL,0), req=tu_ctx_request_switch(NULL), sched=tu_ctx_schedule_next(NULL);
    int block=tu_ctx_block_current(NULL), unblock=tu_ctx_unblock(NULL,0);
    bool expired=tu_ctx_slice_expired(NULL); tu_ctx_free(NULL,0); tu_ctx_notify_command(NULL);
    tu_ctx_notify_cycles(NULL,1); tu_ctx_print_status(NULL,NULL); tu_ctx_manager_destroy(NULL);
    printf("ROW null_api RESULT create=%d alloc=%d get=%d save=%d restore=%d switch=%d request=%d schedule=%d slice=%d block=%d unblock=%d getters=%" PRIu64 "/%" PRIu64 "\n",
           tu_ctx_manager_create(NULL,&c)!=NULL,alloc,tu_ctx_get(NULL,0)!=NULL,save,restore,sw,req,sched,
           expired,block,unblock,tu_ctx_get_switch_count(NULL),tu_ctx_get_switch_overhead(NULL));
    CHECK(tu_ctx_manager_create(NULL,&c)==NULL && alloc==-1 && tu_ctx_get(NULL,0)==NULL &&
          save==-1 && restore==-1 && sw==-1 && req==-1 && sched==-1 && !expired &&
          block==-1 && unblock==-1,"null API behavior");
}

static void test_config_and_allocation(void) {
    tu_runtime_config_t rt = tiny_runtime();
    tu_core_t *core = tu_core_create(&rt);
    tu_ctx_manager_config_t c = base_cfg(), bad;
    int valid = tu_ctx_manager_config_validate(core, &c);
    bad = c; bad.max_contexts = 0;
    int zero = tu_ctx_manager_config_validate(core, &bad);
    bad = c; bad.sched_policy = TU_CTX_SCHED_COUNT;
    int policy = tu_ctx_manager_config_validate(core, &bad);
    bad = c; bad.save_scope = TU_CTX_SAVE_SCOPE_COUNT;
    int scope = tu_ctx_manager_config_validate(core, &bad);
    bad = c; bad.save_scope = TU_CTX_SAVE_LIVE_SRAM; bad.live_w_bytes = 65;
    int live = tu_ctx_manager_config_validate(core, &bad);
    printf("ROW create_invalid RESULT valid=%d null_core=%d null_cfg=%d zero=%d policy=%d scope=%d live=%d\n",
           valid, tu_ctx_manager_config_validate(NULL, &c),
           tu_ctx_manager_config_validate(core, NULL), zero, policy, scope, live);
    CHECK(valid == 0 && zero != 0 && policy != 0 && scope != 0 && live != 0,
          "config validation");
    if (core->state.cmdq) { tu_cmdq_destroy(core->state.cmdq); core->state.cmdq=NULL; }
    tu_dma_destroy(); tu_dataflow_registry_destroy(); tu_core_destroy(core);

    env_t e = env_make(&c);
    print_vec("alloc_first", "PRE", &e, 0);
    int a0 = tu_ctx_alloc(e.mgr);
    print_vec("alloc_first", "POST", &e, a0);
    CHECK(a0 == 0 && active_descriptors(e.mgr) == 1, "first allocation ownership");
    tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    print_vec("alloc_exhaustion", "PRE", &e, 0);
    int ax = tu_ctx_alloc(e.mgr);
    print_vec("alloc_exhaustion", "POST", &e, ax);
    CHECK(ax == -1 && tu_ctx_get(e.mgr, 9) == NULL, "allocation exhaustion/get invalid");
    env_drop(&e);
}

static void test_allocation_clone(void) {
    tu_ctx_manager_config_t c=base_cfg(); env_t e=env_make(&c);
    e.core->state.sram_w.banks.data[0]=0x31; e.core->state.total_dma_bytes=31;
    e.core->state.estimated_cycles=100;
    int a=tu_ctx_alloc(e.mgr);
    e.core->state.sram_w.banks.data[0]=0x42; e.core->state.total_dma_bytes=42;
    e.core->state.estimated_cycles=105;
    int b=tu_ctx_alloc(e.mgr);
    tu_context_desc_t *c0=&e.mgr->contexts[0], *c1=&e.mgr->contexts[1];
    printf("ROW allocation_clone RESULT ids=%d/%d bytes=%02x/%02x dma=%" PRIu64 "/%" PRIu64
           " estimated=%" PRIu64 "/%" PRIu64 " last=%" PRIu64 "/%" PRIu64 "\n",
           a,b,c0->hw_state.sram_w.banks.data[0],c1->hw_state.sram_w.banks.data[0],
           c0->hw_state.total_dma_bytes,c1->hw_state.total_dma_bytes,
           c0->hw_state.estimated_cycles,c1->hw_state.estimated_cycles,
           c0->last_switch_cycle,c1->last_switch_cycle);
    CHECK(a==0 && b==1 && c0->hw_state.sram_w.banks.data[0]==0x31 &&
          c1->hw_state.sram_w.banks.data[0]==0x42 &&
          c0->hw_state.total_dma_bytes==31 && c1->hw_state.total_dma_bytes==42 &&
          c0->last_switch_cycle==0 && c1->last_switch_cycle==0,
          "allocations clone the current core but leave cycle baselines zero");
    env_drop(&e);
}

static void test_free_lifecycle(void) {
    tu_ctx_manager_config_t c = base_cfg();
    env_t e = env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    print_vec("free_active", "PRE", &e, 0); tu_ctx_free(e.mgr, 0); print_vec("free_active", "POST", &e, 0);
    CHECK(e.mgr->active_count == 1 && active_descriptors(e.mgr) == 0 && e.mgr->active_ctx_id == 0,
          "active free leaves stale owner/no active"); env_drop(&e);

    e = env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    print_vec("free_ready", "PRE", &e, 0); tu_ctx_free(e.mgr, 1); print_vec("free_ready", "POST", &e, 0);
    CHECK(e.mgr->active_count == 1 && active_descriptors(e.mgr) == 1, "ready free"); env_drop(&e);

    e = env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr); tu_ctx_block_current(e.mgr);
    print_vec("free_blocked", "PRE", &e, 0); tu_ctx_free(e.mgr, 0); print_vec("free_blocked", "POST", &e, 0);
    CHECK(e.mgr->active_count == 1 && e.mgr->contexts[0].state == TU_CTX_IDLE, "blocked free"); env_drop(&e);

    e = env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr); e.mgr->contexts[1].state=TU_CTX_COMPLETED;
    print_vec("free_completed", "PRE", &e, 0); tu_ctx_free(e.mgr, 1); print_vec("free_completed", "POST", &e, 0);
    CHECK(e.mgr->active_count==1 && e.mgr->contexts[1].state==TU_CTX_IDLE,"completed free"); env_drop(&e);

    e = env_make(&c); tu_ctx_alloc(e.mgr); unsigned before=e.mgr->active_count;
    print_vec("free_idle", "PRE", &e, 0); tu_ctx_free(e.mgr, 3); print_vec("free_idle", "POST", &e, 0);
    CHECK(before == 1 && e.mgr->active_count == 0 && active_descriptors(e.mgr) == 1,
          "idle free corrupts active_count"); env_drop(&e);

    e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr); tu_ctx_free(e.mgr,0);
    print_vec("reuse_after_active_free","PRE",&e,0); int reused=tu_ctx_alloc(e.mgr); print_vec("reuse_after_active_free","POST",&e,reused);
    CHECK(reused==0 && e.mgr->active_count==2 && active_descriptors(e.mgr)==0 &&
          e.mgr->active_ctx_id==0 && e.mgr->contexts[0].state==TU_CTX_READY,
          "slot reuse after active free preserves ownerless state"); env_drop(&e);
}

static void test_switch_ownership(void) {
    tu_ctx_manager_config_t c = base_cfg();
    env_t e = env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    print_vec("save_active", "PRE", &e, 0); int rc=tu_ctx_save(e.mgr); print_vec("save_active", "POST", &e, rc);
    CHECK(rc==0 && active_descriptors(e.mgr)==0 && e.mgr->contexts[0].state==TU_CTX_READY, "manual save no active");
    print_vec("restore_direct", "PRE", &e, 0); rc=tu_ctx_restore(e.mgr,1); print_vec("restore_direct", "POST", &e, rc);
    CHECK(rc==0 && active_descriptors(e.mgr)==1 && e.mgr->active_ctx_id==1, "restore after explicit save"); env_drop(&e);

    e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    print_vec("restore_direct", "PRE", &e, 0); rc=tu_ctx_restore(e.mgr,1); print_vec("restore_direct", "POST", &e, rc);
    CHECK(rc==0 && active_descriptors(e.mgr)==2 && e.mgr->active_ctx_id==1, "direct restore creates two active");
    print_vec("switch_already_active","PRE",&e,0); rc=tu_ctx_switch(e.mgr,0); print_vec("switch_already_active","POST",&e,rc);
    CHECK(rc!=0 && active_descriptors(e.mgr)==1 && e.mgr->contexts[0].state==TU_CTX_ACTIVE &&
          e.mgr->contexts[1].state==TU_CTX_READY && e.mgr->active_ctx_id==1,
          "already-active target rejection leaves stale manager owner"); env_drop(&e);

    e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    print_vec("switch_self", "PRE", &e, 0); rc=tu_ctx_switch(e.mgr,0); print_vec("switch_self", "POST", &e, rc);
    CHECK(rc==0 && e.mgr->total_switches==1 && active_descriptors(e.mgr)==1, "self switch charged"); env_drop(&e);

    const char *names[] = {"switch_invalid","switch_idle","switch_blocked"};
    for (int k=0;k<3;k++) {
        e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
        uint32_t target = k==0 ? 99u : (k==1 ? 3u : 1u);
        if (k==2) e.mgr->contexts[1].state=TU_CTX_BLOCKED;
        print_vec(names[k], "PRE", &e, 0); rc=tu_ctx_switch(e.mgr,target); print_vec(names[k], "POST", &e, rc);
        CHECK(rc!=0 && active_descriptors(e.mgr)==0 && e.mgr->active_ctx_id==0 && e.mgr->pending_save_bytes==192,
              "failed switch is non-atomic"); env_drop(&e);
    }

    e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    print_vec("request_switch", "PRE", &e, 0); rc=tu_ctx_request_switch(e.mgr); print_vec("request_switch", "POST", &e, rc);
    CHECK(rc==0 && e.mgr->active_ctx_id==1 && active_descriptors(e.mgr)==1,
          "request switch is immediate"); env_drop(&e);
}

static void test_scheduling_and_notifications(void) {
    tu_ctx_manager_config_t c=base_cfg(); env_t e=env_make(&c);
    tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    print_vec("schedule_rr","PRE",&e,0); int n=tu_ctx_schedule_next(e.mgr); print_vec("schedule_rr","POST",&e,n);
    CHECK(n==1,"round robin next"); env_drop(&e);

    c.sched_policy=TU_CTX_SCHED_PRIORITY; e=env_make(&c);
    tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    e.mgr->contexts[1].priority=7; e.mgr->contexts[2].priority=7;
    print_vec("schedule_priority_tie","PRE",&e,0); n=tu_ctx_schedule_next(e.mgr); print_vec("schedule_priority_tie","POST",&e,n);
    CHECK(n==1,"priority tie picks first id");
    int n2=tu_ctx_schedule_next(e.mgr); printf("ROW schedule_priority_repeat RESULT first=%d second=%d\n",n,n2);
    CHECK(n2==1,"repeated equal-priority selection repeats first id");
    e.mgr->contexts[1].priority=0; e.mgr->contexts[2].priority=0;
    print_vec("priority_zero","PRE",&e,0); n=tu_ctx_schedule_next(e.mgr); print_vec("priority_zero","POST",&e,n);
    CHECK(n==-1,"priority zero starves"); env_drop(&e);

    c=base_cfg(); c.time_slice_cycles=10; c.time_slice_cmds=3; e=env_make(&c); tu_ctx_alloc(e.mgr);
    int initial=tu_ctx_slice_expired(e.mgr);
    tu_ctx_notify_cycles(e.mgr,9); int c9=tu_ctx_slice_expired(e.mgr);
    tu_ctx_notify_cycles(e.mgr,1); int c10=tu_ctx_slice_expired(e.mgr);
    tu_ctx_notify_cycles(e.mgr,1); int c11=tu_ctx_slice_expired(e.mgr);
    e.mgr->slice_cycles_used=0; e.mgr->slice_cmds_used=0; int reset=tu_ctx_slice_expired(e.mgr);
    tu_ctx_notify_command(e.mgr); tu_ctx_notify_command(e.mgr); int m2=tu_ctx_slice_expired(e.mgr);
    tu_ctx_notify_command(e.mgr); int m3=tu_ctx_slice_expired(e.mgr);
    tu_ctx_notify_command(e.mgr); int m4=tu_ctx_slice_expired(e.mgr);
    printf("ROW slice_thresholds RESULT initial=%d c9=%d c10=%d c11=%d reset=%d m2=%d m3=%d m4=%d\n",
           initial,c9,c10,c11,reset,m2,m3,m4);
    CHECK(!initial && !c9 && c10 && c11 && !reset && !m2 && m3 && m4,"slice under/exact/over thresholds");
    tu_ctx_save(e.mgr); uint64_t tc=e.mgr->contexts[0].total_commands;
    print_vec("notify_without_active","PRE",&e,0); tu_ctx_notify_command(e.mgr); tu_ctx_notify_cycles(e.mgr,5); print_vec("notify_without_active","POST",&e,0);
    CHECK(e.mgr->slice_cmds_used==5 && e.mgr->slice_cycles_used==5 && tc==0 && e.mgr->contexts[0].total_commands==0,
          "notifications manager-only and accept no active"); env_drop(&e);

    c=base_cfg(); e=env_make(&c); e.mgr->slice_cmds_used=UINT32_MAX;
    e.mgr->slice_cycles_used=UINT64_MAX; tu_ctx_notify_command(e.mgr); tu_ctx_notify_cycles(e.mgr,1);
    printf("ROW notify_wrap RESULT cmds=%" PRIu32 " cycles=%" PRIu64 " expired=%d\n",
           e.mgr->slice_cmds_used,e.mgr->slice_cycles_used,tu_ctx_slice_expired(e.mgr));
    CHECK(e.mgr->slice_cmds_used==0 && e.mgr->slice_cycles_used==0 && !tu_ctx_slice_expired(e.mgr),
          "notification counters wrap without saturation"); env_drop(&e);

    c=base_cfg(); e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    print_vec("block_current","PRE",&e,0); int rc=tu_ctx_block_current(e.mgr); print_vec("block_current","POST",&e,rc);
    CHECK(rc==0 && active_descriptors(e.mgr)==0 && e.mgr->contexts[0].state==TU_CTX_BLOCKED,"block leaves no active");
    print_vec("unblock_states","PRE",&e,0); int r0=tu_ctx_unblock(e.mgr,0), r1=tu_ctx_unblock(e.mgr,1), rx=tu_ctx_unblock(e.mgr,99); print_vec("unblock_states","POST",&e,r0);
    CHECK(r0==0 && r1==0 && rx!=0 && e.mgr->contexts[0].state==TU_CTX_READY && e.mgr->contexts[1].state==TU_CTX_READY,
          "unblock accepts nonblocked unchanged"); env_drop(&e);

    e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    e.mgr->contexts[1].state=TU_CTX_BLOCKED; e.mgr->contexts[3].state=TU_CTX_COMPLETED;
    print_vec("unblock_all_states","PRE",&e,0);
    int ua=tu_ctx_unblock(e.mgr,0), ub=tu_ctx_unblock(e.mgr,1), ur=tu_ctx_unblock(e.mgr,1);
    int ui=tu_ctx_unblock(e.mgr,2), uc=tu_ctx_unblock(e.mgr,3), ux=tu_ctx_unblock(e.mgr,99);
    print_vec("unblock_all_states","POST",&e,ub);
    printf("ROW unblock_all_states RESULT active=%d blocked=%d ready=%d idle=%d completed=%d invalid=%d\n",
           ua,ub,ur,ui,uc,ux);
    CHECK(ua==0 && ub==0 && ur==0 && ui==0 && uc==0 && ux!=0 &&
          e.mgr->contexts[0].state==TU_CTX_ACTIVE && e.mgr->contexts[1].state==TU_CTX_READY &&
          e.mgr->contexts[2].state==TU_CTX_IDLE && e.mgr->contexts[3].state==TU_CTX_COMPLETED,
          "unblock returns success for every in-range state and only changes blocked"); env_drop(&e);
}

static void test_malloc_failures(void) {
    const char *names[]={"malloc_fail_w","malloc_fail_a","malloc_fail_o"};
    tu_ctx_manager_config_t c=base_cfg();
    for (int k=1;k<=3;k++) {
        env_t e=env_make(&c); print_vec(names[k-1],"PRE",&e,0);
        arm_malloc_failure(k); int rc=tu_ctx_alloc(e.mgr); disarm_malloc_failure();
        print_vec(names[k-1],"POST",&e,rc);
        printf("ROW %s RESULT calls=%d sizes=%zu/%zu/%zu\n", names[k-1], malloc_seen,
               malloc_sizes[0], malloc_sizes[1], malloc_sizes[2]);
        CHECK(rc==-1 && e.mgr->active_count==0 && e.mgr->contexts[0].state==TU_CTX_IDLE &&
              e.mgr->contexts[0].hw_state.sram_w.banks.data==NULL &&
              e.mgr->contexts[0].hw_state.sram_a.banks.data==NULL &&
              e.mgr->contexts[0].hw_state.sram_o.banks.data==NULL,
              "allocation failure is clean");
        CHECK(malloc_seen==k, "allocation failure reached requested ordinal");
        for (int i=0;i<k;i++) CHECK(malloc_sizes[i]==64, "allocation failure size");
        env_drop(&e);
    }
    env_t e=env_make(&c); tu_ctx_alloc(e.mgr);
    print_vec("malloc_fail_resave","PRE",&e,0); arm_malloc_failure(2); int rc=tu_ctx_save(e.mgr); disarm_malloc_failure(); print_vec("malloc_fail_resave","POST",&e,rc);
    printf("ROW malloc_fail_resave RESULT calls=%d sizes=%zu/%zu/%zu\n",
           malloc_seen, malloc_sizes[0], malloc_sizes[1], malloc_sizes[2]);
    CHECK(rc==-1 && e.mgr->contexts[0].state==TU_CTX_ACTIVE &&
          e.mgr->contexts[0].hw_state.sram_w.banks.data==NULL &&
          e.mgr->contexts[0].hw_state.sram_a.banks.data==NULL &&
          e.mgr->contexts[0].hw_state.sram_o.banks.data==NULL,
          "resave failure destroys prior snapshot non-atomically");
    CHECK(malloc_seen==2 && malloc_sizes[0]==64 && malloc_sizes[1]==64,
          "resave failure ordinal and sizes"); env_drop(&e);
}

static void test_retention_scopes(void) {
    const char *names[]={"live_scope","control_scope"};
    for (int mode=TU_CTX_SAVE_LIVE_SRAM; mode<=TU_CTX_SAVE_CONTROL_ONLY; ++mode) {
        tu_ctx_manager_config_t c=base_cfg(); c.save_scope=(tu_ctx_save_scope_t)mode;
        c.live_w_bytes=c.live_a_bytes=c.live_o_bytes=4; c.state_bytes_per_cycle=8;
        env_t e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
        memset(e.core->state.sram_w.banks.data,0x11,64);
        tu_ctx_switch(e.mgr,1); memset(e.core->state.sram_w.banks.data,0x22,64);
        print_vec(names[mode-TU_CTX_SAVE_LIVE_SRAM],"PRE",&e,0); int rc=tu_ctx_switch(e.mgr,0); print_vec(names[mode-TU_CTX_SAVE_LIVE_SRAM],"POST",&e,rc);
        if (mode==TU_CTX_SAVE_LIVE_SRAM) {
            CHECK(e.core->state.sram_w.banks.data[0]==0x11 && e.core->state.sram_w.banks.data[8]==0x22 &&
                  e.mgr->contexts[0].saved_sram_bytes==12 && e.mgr->total_cycles_stolen==20,
                  "live prefix and two switch costs");
        } else {
            CHECK(e.core->state.sram_w.banks.data[0]==0x22 && e.mgr->contexts[0].saved_sram_bytes==0 &&
                  e.mgr->total_cycles_stolen==14,"control retains no bytes");
        }
        env_drop(&e);
    }

    tu_ctx_manager_config_t c=base_cfg(); c.state_bytes_per_cycle=0;
    env_t e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr); tu_ctx_switch(e.mgr,1);
    print_vec("zero_bandwidth","PRE",&e,0); int rc=tu_ctx_switch(e.mgr,0); print_vec("zero_bandwidth","POST",&e,rc);
    CHECK(rc==0 && e.mgr->contexts[0].saved_sram_bytes==192 && e.mgr->total_cycles_stolen==14,
          "zero bandwidth suppresses transfer cost"); env_drop(&e);
}

static void test_core_state_retention(void) {
    tu_ctx_manager_config_t c=base_cfg(); env_t e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    tu_runtime_config_t expected; fill_runtime(&expected,1); e.core->state.rt_cfg=expected;
    e.core->state.total_dma_bytes=101; e.core->state.total_mma_calls=102;
    e.core->state.total_mma_tiles=103; e.core->state.total_mma_flops=104;
    e.core->state.estimated_cycles=105; e.core->state.initialized=true;
    tu_ctx_switch(e.mgr,1); fill_runtime(&e.core->state.rt_cfg,2);
    e.core->state.total_dma_bytes=201; e.core->state.total_mma_calls=202;
    e.core->state.total_mma_tiles=203; e.core->state.total_mma_flops=204;
    e.core->state.estimated_cycles=205; e.core->state.initialized=false;
    print_vec("core_state_retained","PRE",&e,0); int rc=tu_ctx_switch(e.mgr,0); print_vec("core_state_retained","POST",&e,rc);
    CHECK(rc==0 && e.core->state.total_dma_bytes==101 && e.core->state.total_mma_calls==102 &&
          e.core->state.total_mma_tiles==103 && e.core->state.total_mma_flops==104 &&
          e.core->state.estimated_cycles==105 && e.core->state.initialized &&
          memcmp(&e.core->state.rt_cfg,&expected,sizeof(expected))==0,
          "legacy core scalars and complete runtime config retained"); env_drop(&e);

    e=env_make(&c); tu_ctx_alloc(e.mgr); e.mgr->contexts[0].last_switch_cycle=10;
    e.core->state.estimated_cycles=5; print_vec("cycle_underflow","PRE",&e,0);
    rc=tu_ctx_save(e.mgr); print_vec("cycle_underflow","POST",&e,rc);
    CHECK(rc==0 && e.mgr->contexts[0].total_cycles==UINT64_MAX-4,
          "unsigned context cycle delta underflows"); env_drop(&e);
}

static void test_adjacent_state(void) {
    tu_ctx_manager_config_t c=base_cfg(); env_t e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    tu_command_queue_t *q=e.core->state.cmdq;
    q->head=3; q->tail=1; q->count=2; q->next_cmd_id=77; q->next_signal_id=88;
    q->total_submitted=9; q->total_completed=4; q->total_faulted=2; q->signal_count=1; q->current_cycle=55;
    q->commands[0].cmd_id=42; q->commands[0].status=TU_CMD_PENDING; q->signals[0].signal_id=9; q->signals[0].fired=true;
    print_vec("queue_not_retained","PRE",&e,0); int rc=tu_ctx_switch(e.mgr,1); print_vec("queue_not_retained","POST",&e,rc);
    CHECK(rc==0 && e.core->state.cmdq==q && q->head==3 && q->count==2 && q->commands[0].cmd_id==42,
          "queue live contents survive rather than context restore"); env_drop(&e);

    e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    e.core->state.dma.current_cycle=111; e.core->state.dma.total_bytes=222; e.core->state.dma.channels[0].queue_depth=3;
    uint8_t src[4]={1,2,3,4}; tu_dma_init_full(true,1,4);
    tu_dma_descriptor_t *d=tu_dma_desc_create_linear(0,TU_DMA_DIR_HOST_TO_TU,&e.core->state.sram_w,0,src,1,4);
    tu_dma_submit_desc(d); unsigned qd=g_tu_dma.channels[0].queue_depth;
    print_vec("dma_domains","PRE",&e,0); rc=tu_ctx_switch(e.mgr,1); print_vec("dma_domains","POST",&e,rc);
    CHECK(rc==0 && qd==1 && g_tu_dma.channels[0].queue_depth==1 && g_tu_dma.channels[0].head==d &&
          e.core->state.dma.current_cycle==0 && e.core->state.dma.total_bytes==0,
          "global pending DMA not drained; embedded snapshot separate"); env_drop(&e);

    e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    tu_set_rounding_mode(TU_ROUND_STOCHASTIC); tu_stochastic_set_seed(123);
    tu_set_subnormal_mode(TU_SUBNORMAL_FULL);
    double a=tu_stochastic_uniform(); tu_ctx_switch(e.mgr,1); tu_set_rounding_mode(TU_ROUND_RTZ); double b=tu_stochastic_uniform();
    tu_stochastic_set_seed(123); double ra=tu_stochastic_uniform(), rb=tu_stochastic_uniform();
    printf("ROW rounding_prng_global RESULT a=%.17g b=%.17g ref=%.17g/%.17g mode=%d subnormal=%d\n",a,b,ra,rb,(int)tu_get_rounding_mode(),(int)tu_get_subnormal_mode());
    CHECK(a==ra && b==rb && tu_get_rounding_mode()==TU_ROUND_RTZ &&
          tu_get_subnormal_mode()==TU_SUBNORMAL_FULL,"rounding, PRNG, and subnormal mode global"); env_drop(&e);

    e=env_make(&c); tu_dataflow_plugin_t *p=e.core->state.dataflow;
    p->total_flops=111; p->total_tiles=3; p->total_cycles=9; tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    p->total_flops=222; p->total_tiles=4; p->total_cycles=10;
    print_vec("plugin_global","PRE",&e,0); rc=tu_ctx_switch(e.mgr,1); print_vec("plugin_global","POST",&e,rc);
    CHECK(rc==0 && e.core->state.dataflow==p && e.mgr->contexts[0].hw_state.dataflow==p && p->total_flops==222,
          "plugin pointer retained but mutable registry object shared"); env_drop(&e);
}

static void test_bank_and_dead_controls(void) {
    tu_ctx_manager_config_t c=base_cfg(); c.save_dram_state=true;
    env_t e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    tu_sram_region_t *w=&e.core->state.sram_w;
    w->banks.reads=11; w->banks.current_cycle=12; w->banks.bw_banks[0].words_available=1; w->banks.bw_banks[0].reads_served=13;
    CHECK(tu_sram_enable_double_buffer(w)==0,"enable db control");
    tu_double_buffer_t *db=w->db; tu_ctx_save(e.mgr); tu_sram_disable_double_buffer(w); CHECK(w->db==NULL && db!=NULL,"disable db before restore");
    tu_ctx_restore(e.mgr,1); w->banks.reads=21; w->banks.current_cycle=22; w->banks.bw_banks[0].words_available=2; w->banks.bw_banks[0].reads_served=23;
    tu_ctx_save(e.mgr);
    print_vec("bank_split","PRE",&e,0); int rc=tu_ctx_restore(e.mgr,0); print_vec("bank_split","POST",&e,rc);
    CHECK(rc==0 && w->banks.reads==11 && w->banks.current_cycle==12 &&
          w->banks.bw_banks[0].words_available==2 && w->banks.bw_banks[0].reads_served==23 && w->db==NULL,
          "aggregate bank metadata restored; per-bank and db not retained"); env_drop(&e);

    e=env_make(&c); tu_ctx_alloc(e.mgr); tu_ctx_alloc(e.mgr);
    e.mgr->contexts[1].has_config_override=true; e.mgr->contexts[1].config_override.pe_rows=99; e.mgr->contexts[1].user_data=(void *)(uintptr_t)1;
    uint16_t before=e.core->state.rt_cfg.pe_rows;
    print_vec("dead_controls","PRE",&e,0); rc=tu_ctx_switch(e.mgr,1); print_vec("dead_controls","POST",&e,rc);
    CHECK(rc==0 && before==e.core->state.rt_cfg.pe_rows && e.mgr->contexts[1].config_override.pe_rows==99 &&
          e.mgr->contexts[1].user_data==(void *)(uintptr_t)1,"save_dram/override/user data no switch effect"); env_drop(&e);
}

static void test_status_and_getters(void) {
    tu_ctx_manager_config_t c=base_cfg(); env_t e=env_make(&c); tu_ctx_alloc(e.mgr);
    FILE *f=tmpfile(); tu_ctx_print_status(e.mgr,f); long n=ftell(f); fclose(f);
    printf("ROW getters_status RESULT count=%" PRIu64 " overhead=%" PRIu64 " null=%" PRIu64 "/%" PRIu64 " status_bytes=%ld\n",
           tu_ctx_get_switch_count(e.mgr),tu_ctx_get_switch_overhead(e.mgr),
           tu_ctx_get_switch_count(NULL),tu_ctx_get_switch_overhead(NULL),n);
    CHECK(n>0 && tu_ctx_get_switch_count(NULL)==0 && tu_ctx_get_switch_overhead(NULL)==0,"getters/status"); env_drop(&e);
}

int main(void) {
    test_null_api();
    test_config_and_allocation();
    test_allocation_clone();
    test_free_lifecycle();
    test_switch_ownership();
    test_scheduling_and_notifications();
    test_malloc_failures();
    test_retention_scopes();
    test_core_state_retention();
    test_adjacent_state();
    test_bank_and_dead_controls();
    test_status_and_getters();
    printf("CH18_PROBE SUMMARY failures=%d\n", failures);
    return failures ? 1 : 0;
}
