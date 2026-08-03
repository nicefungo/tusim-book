#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

#include "tu_cmodel/tu_cmodel.h"
#include "tu_cmodel/dma_descriptor.h"
#include "tu_cmodel/infra/config.h"

static int failures;
#define CHECK(c, n) do { bool ok_ = (c); printf("CHECK %-48s %s\n", (n), ok_ ? "PASS" : "FAIL"); if (!ok_) failures++; } while (0)

static tu_dma_descriptor_t *load_desc(uint8_t ch, tu_sram_region_t *r,
                                      uint32_t off, void *host, uint32_t n) {
    return tu_dma_desc_create_linear(ch, TU_DMA_DIR_HOST_TO_TU,
                                     r, off, host, 1, n);
}

static void timing_boundaries(void) {
    printf("\n[timing_boundaries]\n");
    const uint32_t sizes[] = {0, 1, 31, 32, 33, 64, 65};
    for (size_t i = 0; i < sizeof(sizes)/sizeof(sizes[0]); i++) {
        uint32_t n = sizes[i];
        tu_dma_init_full(false, 1, 8);
        tu_sram_region_t r;
        tu_sram_init(&r, 512, "timing");
        tu_sram_set_bw_modeling(&r, false);
        uint8_t src[80]; memset(src, 0x40 + (int)i, sizeof(src));
        tu_dma_descriptor_t *d = load_desc(0, &r, 0, src, n);
        uint64_t expected = TU_LATENCY_DRAM_READ +
            (n + TU_DMA_BUS_WIDTH_BYTES - 1) / TU_DMA_BUS_WIDTH_BYTES;
        tu_dma_submit_desc(d);
        printf("timing size=%u formula=%u+ceil(%u/%u) expected=%" PRIu64
               " observed=%" PRIu64 " issued=%" PRIu64 "\n",
               n, TU_LATENCY_DRAM_READ, n, TU_DMA_BUS_WIDTH_BYTES,
               expected, d->cycles_completed, d->cycles_issued);
        CHECK(d->cycles_completed == expected && d->cycles_issued == 0,
              "service formula and inert issue timestamp");
        tu_dma_desc_destroy(d); tu_sram_destroy(&r); tu_dma_destroy();
    }

    tu_dma_init_full(false, 1, 8);
    tu_sram_region_t r; tu_sram_init(&r, 512, "directions");
    tu_sram_set_bw_modeling(&r, false);
    uint8_t out[64] = {0};
    tu_dma_descriptor_t *store = tu_dma_desc_create_linear(
        0, TU_DMA_DIR_TU_TO_HOST, &r, 0, out, 1, sizeof(out));
    tu_dma_submit_desc(store);
    printf("descriptor_store size=64 macro=TU_LATENCY_DRAM_READ value=%u observed=%" PRIu64 "\n",
           TU_LATENCY_DRAM_READ, store->cycles_completed);
    CHECK(store->cycles_completed == TU_LATENCY_DRAM_READ + 2,
          "descriptor store uses read-latency macro");
    tu_dma_desc_destroy(store); tu_sram_destroy(&r); tu_dma_destroy();
}

static void geometry_oracles(void) {
    printf("\n[geometry_oracles]\n");
    tu_dma_init_full(false, 1, 16);
    tu_sram_region_t r; tu_sram_init(&r, 256, "geometry");
    tu_sram_set_bw_modeling(&r, false);
    uint8_t *mem = tu_sram_raw_ptr(&r); memset(mem, 0xcc, 256);
    uint8_t host[128]; for (uint32_t i=0;i<128;i++) host[i]=(uint8_t)i;

    tu_dma_descriptor_t *d2 = tu_dma_desc_create_strided_2d(
        0, TU_DMA_DIR_HOST_TO_TU, &r, 5, host,
        13, 11, 2, 2, 3);
    tu_dma_submit_desc(d2);
    bool rows2 = !memcmp(mem+5, host, 6) && !memcmp(mem+18, host+11, 6);
    bool canary2 = mem[4]==0xcc && mem[11]==0xcc && mem[17]==0xcc && mem[24]==0xcc;
    printf("geom2d payload=%u src_span=%u dst_span=%u rows_ok=%d canaries_ok=%d\n",
           d2->total_bytes, 11+6, 13+6, rows2, canary2);
    CHECK(d2->total_bytes==12 && rows2 && canary2,
          "2D nonsymmetric strides match independent oracle");
    tu_dma_desc_destroy(d2);

    memset(mem, 0xcc, 256);
    tu_dma_descriptor_t *d3 = tu_dma_desc_create_strided_3d(
        0, TU_DMA_DIR_HOST_TO_TU, &r, 4, host,
        7, 20, 5, 13, 1, 2, 2, 3);
    tu_dma_submit_desc(d3);
    bool rows3 = !memcmp(mem+4,host,3) && !memcmp(mem+11,host+5,3) &&
                 !memcmp(mem+24,host+13,3) && !memcmp(mem+31,host+18,3);
    bool canary3 = mem[3]==0xcc && mem[7]==0xcc && mem[10]==0xcc &&
                   mem[14]==0xcc && mem[23]==0xcc && mem[34]==0xcc;
    printf("geom3d payload=%u src_span=%u dst_span=%u rows_ok=%d canaries_ok=%d\n",
           d3->total_bytes, 13+5+3, 20+7+3, rows3, canary3);
    CHECK(d3->total_bytes==12 && rows3 && canary3,
          "3D nonsymmetric strides match independent oracle");
    tu_dma_desc_destroy(d3);

    memset(mem, 0, 256);
    uint8_t values[3]={0xa1,0xb2,0xc3}; uint32_t idx[3]={4,4,8};
    tu_dma_descriptor_t *sc = tu_dma_desc_create_scatter(0,&r,values,idx,3,1);
    tu_dma_submit_desc(sc);
    printf("scatter accounted=%u events=3 unique_offsets=2 final4=%02x final8=%02x\n",
           sc->total_bytes, mem[4], mem[8]);
    CHECK(sc->total_bytes==3 && mem[4]==0xb2 && mem[8]==0xc3,
          "duplicate scatter separates events from unique bytes");
    tu_dma_desc_destroy(sc);

    tu_sram_region_t r2; tu_sram_init(&r2,256,"geometry2");
    tu_sram_set_bw_modeling(&r2,false); memset(mem,0,256);
    memset(tu_sram_raw_ptr(&r2),0,256);
    tu_sram_region_t *regions[2]={&r,&r2}; uint32_t offs[2]={7,9};
    uint8_t fan[4]={1,2,3,4};
    tu_dma_descriptor_t *mc=tu_dma_desc_create_multicast(0,fan,regions,offs,2,1,4);
    tu_dma_submit_desc(mc);
    printf("multicast source_payload=4 requested_fanout=%u delivered=8\n",mc->total_bytes);
    CHECK(mc->total_bytes==8 && !memcmp(mem+7,fan,4) &&
          !memcmp(tu_sram_raw_ptr(&r2)+9,fan,4),
          "multicast distinguishes source and fanout bytes");
    tu_dma_desc_destroy(mc);
    tu_sram_destroy(&r2); tu_sram_destroy(&r); tu_dma_destroy();
}

static void borrowed_state(void) {
    printf("\n[borrowed_state]\n");
    tu_dma_init_full(false,1,8);
    tu_sram_region_t r; tu_sram_init(&r,64,"borrowed"); tu_sram_set_bw_modeling(&r,false);
    uint8_t src[2]={0x11,0x22}; uint32_t idx[2]={1,2};
    tu_dma_descriptor_t *d=tu_dma_desc_create_scatter(0,&r,src,idx,2,1);
    src[0]=0xa5; idx[0]=5;
    tu_dma_submit_desc(d);
    uint8_t *m=tu_sram_raw_ptr(&r);
    printf("borrowed mutated_src=%02x mutated_index=%u observed_at5=%02x old_at1=%02x\n",
           src[0],idx[0],m[5],m[1]);
    CHECK(m[5]==0xa5 && m[1]==0,
          "source and index list are borrowed until execution");
    tu_dma_desc_destroy(d); tu_sram_destroy(&r); tu_dma_destroy();
}

static void chain_then_head_child(void) {
    uint8_t src[4]={1,2,3,4}; tu_sram_region_t r;
    tu_dma_init_full(true,1,8); tu_sram_init(&r,128,"q1");
    tu_dma_descriptor_t *a0=load_desc(0,&r,0,src,1), *a1=load_desc(0,&r,8,src,1);
    tu_dma_descriptor_t *q=load_desc(0,&r,16,src,1); tu_dma_desc_chain(a0,a1);
    tu_dma_submit_desc(a0); tu_dma_submit_desc(q);
    printf("chain_then_head a0_next_is_q=%d a1_disconnected=%d head_a0=%d tail_q=%d depth=%u\n",
           a0->next==q,a1!=a0->next,g_tu_dma.channels[0].head==a0,
           g_tu_dma.channels[0].tail==q,g_tu_dma.channels[0].queue_depth);
    CHECK(a0->next==q && a1!=a0->next,
          "later head overwrites first chain linkage");
    /* Process exit reclaims this isolated corrupted graph without invoking the
       unsafe engine reinitializer, traversal, flush, or descriptor destroy. */
}

static void submit_while_active_child(void) {
    uint8_t src[4]={1,2,3,4};
    tu_dma_init_full(true,1,8);
    tu_sram_region_t r2; tu_sram_init(&r2,128,"q2");
    tu_dma_descriptor_t *b0=load_desc(0,&r2,0,src,1), *b1=load_desc(0,&r2,8,src,1);
    tu_dma_descriptor_t *q2=load_desc(0,&r2,16,src,1); tu_dma_desc_chain(b0,b1);
    tu_dma_submit_desc(b0); tu_dma_tick(); tu_dma_submit_desc(q2);
    printf("submit_while_active active_b0=%d head_b1=%d b0_next_q=%d q_reachable_from_head=%d depth=%u\n",
           g_tu_dma.channels[0].active==b0,g_tu_dma.channels[0].head==b1,
           b0->next==q2,b1->next==q2,g_tu_dma.channels[0].queue_depth);
    CHECK(b0->next==q2 && b1->next!=q2,
          "stale tail makes new head unreachable from pending head");
}

static void run_corruption_child(void (*body)(void), const char *name) {
    fflush(NULL);
    pid_t pid=fork();
    if (pid<0) {
        CHECK(false, "fork isolated corruption case");
        return;
    }
    if (pid==0) {
        int before=failures;
        body();
        fflush(NULL);
        _exit(failures==before ? 0 : 1);
    }
    CHECK(true, "fork isolated corruption case");
    int status=0;
    CHECK(waitpid(pid,&status,0)==pid && WIFEXITED(status) && WEXITSTATUS(status)==0,
          name);
}

static void queue_link_corruption(void) {
    printf("\n[queue_link_corruption]\n");
    run_corruption_child(chain_then_head_child,
                         "isolated chain-then-head corruption observation");
    run_corruption_child(submit_while_active_child,
                         "isolated active-plus-pending corruption observation");
}

static void bandwidth_order(void) {
    printf("\n[bandwidth_resource_sweep]\n");
    uint8_t a[1024],b[1024]; memset(a,1,sizeof(a)); memset(b,2,sizeof(b));

    tu_dma_init_full(true,2,8);
    tu_sram_region_t shared; tu_sram_init(&shared,4096,"shared");
    tu_sram_set_bw_modeling(&shared,true);
    tu_dma_descriptor_t *d0=load_desc(0,&shared,0,a,sizeof(a));
    tu_dma_descriptor_t *d1=load_desc(1,&shared,2048,b,sizeof(b));
    tu_dma_submit_desc(d0); tu_dma_submit_desc(d1); tu_dma_tick();
    uint64_t shared0=d0->cycles_completed-1, shared1=d1->cycles_completed-1;
    printf("bw_on shared_region ch0_service=%" PRIu64 " ch1_service=%" PRIu64 " delta=%" PRIu64 "\n",
           shared0,shared1,shared1-shared0);
    CHECK(shared0==shared1, "shared-region same-tick estimates are equal");
    while(g_tu_dma.channels[0].active||g_tu_dma.channels[1].active) tu_dma_tick();
    tu_dma_desc_destroy(d0); tu_dma_desc_destroy(d1); tu_sram_destroy(&shared); tu_dma_destroy();

    tu_dma_init_full(true,2,8);
    tu_sram_region_t r0,r1; tu_sram_init(&r0,4096,"r0"); tu_sram_init(&r1,4096,"r1");
    tu_sram_set_bw_modeling(&r0,true); tu_sram_set_bw_modeling(&r1,true);
    d0=load_desc(0,&r0,0,a,sizeof(a)); d1=load_desc(1,&r1,0,b,sizeof(b));
    tu_dma_submit_desc(d0); tu_dma_submit_desc(d1); tu_dma_tick();
    uint64_t separate0=d0->cycles_completed-1, separate1=d1->cycles_completed-1;
    printf("bw_on separate_regions ch0_service=%" PRIu64 " ch1_service=%" PRIu64 "\n",
           separate0,separate1);
    CHECK(separate0==shared0 && separate1==shared1,
          "separate regions match shared-region service estimate");
    while(g_tu_dma.channels[0].active||g_tu_dma.channels[1].active) tu_dma_tick();
    tu_dma_desc_destroy(d0); tu_dma_desc_destroy(d1); tu_sram_destroy(&r0); tu_sram_destroy(&r1); tu_dma_destroy();

    tu_dma_init_full(true,2,8); tu_sram_init(&shared,4096,"off");
    tu_sram_set_bw_modeling(&shared,false);
    d0=load_desc(0,&shared,0,a,sizeof(a)); d1=load_desc(1,&shared,2048,b,sizeof(b));
    tu_dma_submit_desc(d0); tu_dma_submit_desc(d1); tu_dma_tick();
    uint64_t off0=d0->cycles_completed-1, off1=d1->cycles_completed-1;
    printf("bw_off shared_region ch0_service=%" PRIu64 " ch1_service=%" PRIu64 " expected=%u\n",
           off0,off1,TU_LATENCY_DRAM_READ+1024/TU_DMA_BUS_WIDTH_BYTES);
    CHECK(off0==82 && off1==82 && shared0>off0,
          "bandwidth switch changes estimate but not channel equality");
    while(g_tu_dma.channels[0].active||g_tu_dma.channels[1].active) tu_dma_tick();
    tu_dma_desc_destroy(d0); tu_dma_desc_destroy(d1); tu_sram_destroy(&shared); tu_dma_destroy();
}

static void error_lifecycle(void) {
    printf("\n[error_lifecycle]\n");
    uint8_t src[8]; memset(src,0xee,sizeof(src));
    tu_sram_region_t r;

    tu_dma_init_full(false,1,8); tu_sram_init(&r,64,"sync-error");
    tu_dma_descriptor_t *d=load_desc(0,&r,60,src,sizeof(src));
    uint32_t id=tu_dma_submit_desc(d);
    printf("sync_error id=%u flag=%d timestamp=%" PRIu64
           " channel_completed=%" PRIu64 " transfers=%" PRIu64 " depth=%u\n",
           id,d->completed,d->cycles_completed,g_tu_dma.channels[0].total_completed,
           g_tu_dma.total_transfers,g_tu_dma.channels[0].queue_depth);
    CHECK(id!=0 && !d->completed && d->cycles_completed==0 &&
          g_tu_dma.channels[0].total_completed==1 && g_tu_dma.total_transfers==0,
          "sync failed executor still increments channel completion");
    tu_dma_desc_destroy(d); tu_sram_destroy(&r); tu_dma_destroy();

    tu_dma_init_full(true,1,8); tu_sram_init(&r,64,"async-error");
    d=load_desc(0,&r,60,src,sizeof(src)); tu_dma_submit_desc(d);
    tu_dma_tick();
    printf("async_error_after_select flag=%d timestamp=%" PRIu64 " active=%d completed_count=%" PRIu64 "\n",
           d->completed,d->cycles_completed,g_tu_dma.channels[0].active==d,
           g_tu_dma.channels[0].total_completed);
    CHECK(!d->completed && d->cycles_completed==0 && g_tu_dma.channels[0].active==d,
          "async failed executor leaves zero-timestamp active descriptor");
    tu_dma_tick();
    printf("async_error_after_next_tick active=%d completed_count=%" PRIu64 " transfers=%" PRIu64 "\n",
           g_tu_dma.channels[0].active!=NULL,g_tu_dma.channels[0].total_completed,
           g_tu_dma.total_transfers);
    CHECK(!g_tu_dma.channels[0].active && g_tu_dma.channels[0].total_completed==1 &&
          !d->completed && g_tu_dma.total_transfers==0,
          "async failed executor retires as channel-completed next tick");
    tu_dma_desc_destroy(d); tu_sram_destroy(&r); tu_dma_destroy();

    tu_dma_init_full(true,1,8); tu_sram_init(&r,64,"flush-error");
    d=load_desc(0,&r,60,src,sizeof(src)); tu_dma_submit_desc(d); tu_dma_flush_all();
    printf("flush_error flag=%d timestamp=%" PRIu64 " completed_count=%" PRIu64 " transfers=%" PRIu64 "\n",
           d->completed,d->cycles_completed,g_tu_dma.channels[0].total_completed,
           g_tu_dma.total_transfers);
    CHECK(!d->completed && d->cycles_completed==0 &&
          g_tu_dma.channels[0].total_completed==1 && g_tu_dma.total_transfers==0,
          "flush failed executor still increments channel completion");
    tu_dma_desc_destroy(d); tu_sram_destroy(&r); tu_dma_destroy();
}

static void config_ab(void) {
    printf("\n[config_ab]\n");
    const char *json = "{\"tu\":{\"dma\":{\"bus_width_bits\":128,"
                       "\"max_burst_bytes\":32,\"channels\":1,"
                       "\"max_outstanding\":2,\"async_mode\":true,"
                       "\"multicast_enabled\":false}}}";
    tu_config_t cfg; char err[256] = {0};
    int parse_rc=tu_config_load_string(json,&cfg,err,sizeof(err));
    printf("json_parse rc=%d bus_bits=%u burst=%u channels=%u depth=%u async=%d multicast=%d\n",
           parse_rc,cfg.dma_bus_width_bits,cfg.dma_max_burst_bytes,
           cfg.dma_num_channels,cfg.dma_max_outstanding,cfg.dma_async_mode,
           cfg.dma_multicast_enabled);
    CHECK(parse_rc==0 && cfg.dma_bus_width_bits==128 &&
          cfg.dma_max_burst_bytes==32 && cfg.dma_num_channels==1 &&
          cfg.dma_max_outstanding==2 && cfg.dma_async_mode &&
          !cfg.dma_multicast_enabled,
          "JSON parser stores nondefault DMA fields");
    int rc=tu_init_from_config(&cfg);
    printf("config_path rc=%d requested_async=1 active_async=%d requested_channels=1 active_channels=%u requested_depth=2 active_depth=%u requested_bus_bits=128 compile_bus_bits=%u\n",
           rc,g_tu_dma.async_mode,g_tu_dma.num_channels,g_tu_dma.channels[0].max_depth,
           TU_DMA_BUS_WIDTH_BITS);
    CHECK(rc==0 && !g_tu_dma.async_mode && g_tu_dma.num_channels==TU_DMA_CHANNELS &&
          g_tu_dma.channels[0].max_depth==TU_DMA_MAX_OUTSTANDING && TU_DMA_BUS_WIDTH_BITS==256,
          "top-level config path omits nondefault DMA fields");
    tu_dma_destroy();
    tu_dma_init_full(true,1,2);
    printf("direct_path active_async=%d active_channels=%u active_depth=%u\n",
           g_tu_dma.async_mode,g_tu_dma.num_channels,g_tu_dma.channels[0].max_depth);
    CHECK(g_tu_dma.async_mode && g_tu_dma.num_channels==1 &&
          g_tu_dma.channels[0].max_depth==2,
          "direct initializer activates async/channel/depth values");
    tu_dma_destroy();
}

int main(void) {
    timing_boundaries(); geometry_oracles(); borrowed_state();
    queue_link_corruption(); bandwidth_order(); error_lifecycle(); config_ab();
    printf("\nEXTENDED_SUMMARY failures=%d\n", failures);
    return failures ? 1 : 0;
}
