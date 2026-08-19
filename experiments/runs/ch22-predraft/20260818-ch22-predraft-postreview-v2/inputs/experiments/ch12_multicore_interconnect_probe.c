#include "tu_cmodel/tu_cluster.h"
#include "tu_cmodel/infra/config.h"
#include "tu_cmodel/tu_sram.h"

#include <inttypes.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int failures;

#define CHECK(cond, label) do { \
    if (!(cond)) { fprintf(stderr, "CHECK FAIL: %s\n", label); failures++; } \
    else { printf("CHECK PASS: %s\n", label); } \
} while (0)

static void probe_config(void) {
    const char *json =
        "{\"tu\":{\"multicore\":{\"enabled\":true,\"num_cores\":8,"
        "\"interconnect\":\"mesh\",\"switching\":\"store_and_forward\","
        "\"contention\":\"shared_link\",\"mesh_routing\":\"yx\","
        "\"link_bytes_per_cycle\":32,\"router_latency_cycles\":7}}}";
    tu_config_t full;
    memset(&full, 0, sizeof(full));
    char error[256] = {0};
    int rc = tu_config_load_string(json, &full, error, sizeof(error));
    CHECK(rc == 0, "full multicore JSON parses and validates");
    if (rc != 0) {
        fprintf(stderr, "config parse error: %s\n", error);
        return;
    }
    tu_runtime_config_t rt = tu_config_to_runtime(&full);
    CHECK(full.multicore_enabled && full.num_cores == 8 && full.interconnect_mode == 2,
          "full config retains enable, count, and mesh request");
    CHECK(rt.icc_switching_mode == TU_ICC_SWITCH_STORE_FORWARD &&
          rt.icc_contention_mode == TU_ICC_CONTENTION_SHARED_LINK &&
          rt.icc_mesh_routing_mode == TU_ICC_MESH_ROUTE_YX &&
          rt.icc_link_bytes_per_cycle == 32 && rt.icc_router_latency_cycles == 7,
          "runtime converter retains five ICC fields");

    tu_cluster_t *cl = tu_cluster_create(4, TU_TOPOLOGY_RING, 0, &rt);
    CHECK(cl && cl->num_cores == 4 && cl->topology == TU_TOPOLOGY_RING,
          "cluster count and topology come from explicit constructor arguments");
    CHECK(cl && cl->switching_mode == TU_ICC_SWITCH_STORE_FORWARD &&
          cl->contention_mode == TU_ICC_CONTENTION_SHARED_LINK &&
          cl->mesh_routing_mode == TU_ICC_MESH_ROUTE_YX &&
          cl->link_bytes_per_cycle == 32 && cl->hop_latency == 7,
          "cluster consumes five converted ICC fields");
    printf("CONFIG parsed_enabled=%d parsed_cores=%u parsed_topology=%d "
           "cluster_cores=%u cluster_topology=%d sw=%d contention=%d route=%d link=%u router=%u\n",
           full.multicore_enabled, full.num_cores, full.interconnect_mode,
           cl ? cl->num_cores : 0, cl ? (int)cl->topology : -1,
           cl ? cl->switching_mode : -1, cl ? cl->contention_mode : -1,
           cl ? cl->mesh_routing_mode : -1, cl ? cl->link_bytes_per_cycle : 0,
           cl ? cl->hop_latency : 0);
    tu_cluster_destroy(cl);
}

static void probe_equations(void) {
    tu_cluster_t c;
    memset(&c, 0, sizeof(c));
    c.num_cores = 6; c.topology = TU_TOPOLOGY_MESH;
    c.mesh_rows = 2; c.mesh_cols = 3; c.hop_latency = 5;
    c.link_bytes_per_cycle = 16;
    c.switching_mode = TU_ICC_SWITCH_LEGACY_HOP_ONLY;
    uint64_t legacy = tu_cluster_estimate_transfer_cycles(&c, 0, 5, 1024);
    c.switching_mode = TU_ICC_SWITCH_CUT_THROUGH;
    uint64_t cut = tu_cluster_estimate_transfer_cycles(&c, 0, 5, 1024);
    c.switching_mode = TU_ICC_SWITCH_STORE_FORWARD;
    uint64_t store = tu_cluster_estimate_transfer_cycles(&c, 0, 5, 1024);
    CHECK(legacy == 15 && cut == 79 && store == 207,
          "three switching equations match exact three-hop values");
    CHECK(tu_cluster_estimate_transfer_cycles(&c, 0, 5, 0) == 0,
          "zero-byte estimate is zero");
    c.switching_mode = TU_ICC_SWITCH_CUT_THROUGH;
    c.link_bytes_per_cycle = 0;
    CHECK(tu_cluster_estimate_transfer_cycles(&c, 0, 5, 1024) == UINT64_MAX,
          "hand-built zero link width is retained and rejected by estimator");
    printf("EQUATIONS legacy=%" PRIu64 " cut=%" PRIu64 " store=%" PRIu64 "\n",
           legacy, cut, store);
}

static void probe_send(void) {
    tu_runtime_config_t rt = tu_runtime_config_default();
    rt.icc_switching_mode = TU_ICC_SWITCH_CUT_THROUGH;
    rt.icc_link_bytes_per_cycle = 32;
    rt.icc_router_latency_cycles = 7;
    tu_cluster_t *cl = tu_cluster_create(4, TU_TOPOLOGY_RING, 0, &rt);
    CHECK(cl != NULL, "send cluster created");
    if (!cl) return;

    const uint32_t data[4] = {0x11223344U, 0x55667788U, 0x99aabbccU, 0xddeeff00U};
    uint32_t out[4] = {0};
    tu_sram_write_bulk(tu_core_get_sram_o(cl->cores[0]), 32, data, sizeof(data));
    uint64_t before[4];
    for (int i = 0; i < 4; ++i) before[i] = cl->cores[i]->state.estimated_cycles;
    tu_icc_message_t msg = {.src_core_id=0, .dst_core_id=2, .src_offset=32,
        .dst_offset=64, .size_bytes=sizeof(data), .tag=0xa5a5U,
        .blocking=false, .latency_cycles=999};
    tu_icc_message_t original = msg;
    int rc = tu_cluster_send(cl, &msg);
    tu_sram_read_bulk(tu_core_get_sram_o(cl->cores[2]), 64, out, sizeof(out));
    CHECK(rc == 0 && memcmp(data, out, sizeof(data)) == 0,
          "send performs immediate byte-identical O-SRAM copy");
    CHECK(msg.src_core_id == original.src_core_id &&
          msg.dst_core_id == original.dst_core_id &&
          msg.src_offset == original.src_offset &&
          msg.dst_offset == original.dst_offset &&
          msg.size_bytes == original.size_bytes &&
          msg.tag == original.tag && msg.blocking == original.blocking &&
          msg.latency_cycles == original.latency_cycles,
          "send leaves tag, false blocking flag, and latency field unchanged");
    CHECK(cl->stats.total_icc_messages == 1 && cl->stats.total_icc_bytes == 16 &&
          cl->stats.total_icc_cycles == 15,
          "send accumulates exact message byte and isolated-cycle stats");
    CHECK(cl->cores[0]->state.estimated_cycles == before[0] &&
          cl->cores[1]->state.estimated_cycles == before[1] &&
          cl->cores[2]->state.estimated_cycles == before[2] + 15 &&
          cl->cores[3]->state.estimated_cycles == before[3],
          "send adds estimate only to destination core");
    printf("SEND blocking=%d descriptor_latency=%" PRIu64
           " stats_messages=%" PRIu64 " stats_bytes=%" PRIu64
           " stats_cycles=%" PRIu64 " dst_delta=%" PRIu64 "\n",
           msg.blocking, msg.latency_cycles, cl->stats.total_icc_messages,
           cl->stats.total_icc_bytes, cl->stats.total_icc_cycles,
           cl->cores[2]->state.estimated_cycles - before[2]);
    tu_cluster_destroy(cl);
}

static void probe_traffic(void) {
    tu_cluster_t c;
    memset(&c, 0, sizeof(c));
    c.num_cores=4; c.topology=TU_TOPOLOGY_MESH; c.mesh_rows=2; c.mesh_cols=2;
    c.hop_latency=5; c.switching_mode=TU_ICC_SWITCH_CUT_THROUGH;
    c.link_bytes_per_cycle=16; c.contention_mode=TU_ICC_CONTENTION_SHARED_LINK;
    tu_icc_message_t same[2] = {{.src_core_id=0,.dst_core_id=1,.size_bytes=1024},
                                {.src_core_id=0,.dst_core_id=1,.size_bytes=1024}};
    tu_icc_message_t disjoint[2] = {{.src_core_id=0,.dst_core_id=1,.size_bytes=1024},
                                    {.src_core_id=2,.dst_core_id=3,.size_bytes=1024}};
    tu_icc_traffic_stats_t s, d, i;
    CHECK(tu_cluster_estimate_traffic_cycles(&c, same, 2, &s) == 0 &&
          s.isolated_cycles == 69 && s.bottleneck_link_cycles == 128 &&
          s.estimated_cycles == 133 && s.bottleneck_src == 0 && s.bottleneck_dst == 1,
          "same directed link exposes shared serialization heuristic");
    CHECK(tu_cluster_estimate_traffic_cycles(&c, disjoint, 2, &d) == 0 &&
          d.estimated_cycles == 69,
          "disjoint directed links retain isolated maximum");
    c.contention_mode=TU_ICC_CONTENTION_IDEAL_PARALLEL;
    CHECK(tu_cluster_estimate_traffic_cycles(&c, same, 2, &i) == 0 &&
          i.estimated_cycles == 69,
          "ideal-parallel ignores shared-link accumulation");
    printf("TRAFFIC same=%" PRIu64 " disjoint=%" PRIu64 " ideal=%" PRIu64
           " bottleneck=%" PRIu64 " link=%u->%u\n",
           s.estimated_cycles,d.estimated_cycles,i.estimated_cycles,
           s.bottleneck_link_cycles,s.bottleneck_src,s.bottleneck_dst);

    tu_cluster_t x;
    memset(&x, 0, sizeof(x));
    x.num_cores=16; x.topology=TU_TOPOLOGY_MESH; x.mesh_rows=4; x.mesh_cols=4;
    x.hop_latency=5; x.switching_mode=TU_ICC_SWITCH_CUT_THROUGH;
    x.link_bytes_per_cycle=16; x.contention_mode=TU_ICC_CONTENTION_SHARED_LINK;
    x.mesh_routing_mode=TU_ICC_MESH_ROUTE_XY;
    tu_icc_message_t mixed[3] = {
        {.src_core_id=0,.dst_core_id=1,.size_bytes=1024},
        {.src_core_id=0,.dst_core_id=1,.size_bytes=1024},
        {.src_core_id=12,.dst_core_id=3,.size_bytes=1024},
    };
    tu_icc_traffic_stats_t h;
    int hrc=tu_cluster_estimate_traffic_cycles(&x,mixed,3,&h);
    CHECK(hrc==0 && h.isolated_cycles==94 && h.bottleneck_link_cycles==128 &&
          h.estimated_cycles==158 && h.bottleneck_src==0 && h.bottleneck_dst==1,
          "disjoint long route proves combined global-max sum is only a heuristic");
    printf("HEURISTIC_COUNTEREXAMPLE isolated=%" PRIu64 " bottleneck=%" PRIu64
           " estimated=%" PRIu64 " shared_pair_term=133 link=%u->%u\n",
           h.isolated_cycles,h.bottleneck_link_cycles,h.estimated_cycles,
           h.bottleneck_src,h.bottleneck_dst);
}

static uint32_t asymmetric(tu_icc_message_t *m, bool rotate_ccw) {
    uint32_t count=0;
    if (!rotate_ccw) {
        for (uint32_t sc=1; sc<4; ++sc) for (uint32_t dr=1; dr<4; ++dr)
            m[count++] = (tu_icc_message_t){.src_core_id=sc,.dst_core_id=dr*4,.size_bytes=1024};
    } else {
        for (uint32_t sr=0; sr<3; ++sr) for (uint32_t dc=1; dc<4; ++dc)
            m[count++] = (tu_icc_message_t){.src_core_id=sr*4,.dst_core_id=12+dc,.size_bytes=1024};
    }
    return count;
}

static void probe_routes(void) {
    tu_cluster_t c; memset(&c,0,sizeof(c));
    c.num_cores=16; c.topology=TU_TOPOLOGY_MESH; c.mesh_rows=4; c.mesh_cols=4;
    c.hop_latency=5; c.switching_mode=TU_ICC_SWITCH_CUT_THROUGH;
    c.link_bytes_per_cycle=16; c.contention_mode=TU_ICC_CONTENTION_SHARED_LINK;
    tu_icc_message_t m[9]; tu_icc_traffic_stats_t axy, ayx, bxy, byx;
    uint32_t n=asymmetric(m,false);
    c.mesh_routing_mode=TU_ICC_MESH_ROUTE_XY; CHECK(tu_cluster_estimate_traffic_cycles(&c,m,n,&axy)==0,"XY first pattern estimated");
    c.mesh_routing_mode=TU_ICC_MESH_ROUTE_YX; CHECK(tu_cluster_estimate_traffic_cycles(&c,m,n,&ayx)==0,"YX first pattern estimated");
    n=asymmetric(m,true);
    c.mesh_routing_mode=TU_ICC_MESH_ROUTE_XY; CHECK(tu_cluster_estimate_traffic_cycles(&c,m,n,&bxy)==0,"XY rotated pattern estimated");
    c.mesh_routing_mode=TU_ICC_MESH_ROUTE_YX; CHECK(tu_cluster_estimate_traffic_cycles(&c,m,n,&byx)==0,"YX rotated pattern estimated");
    CHECK(axy.estimated_cycles==606 && ayx.estimated_cycles==222 &&
          bxy.estimated_cycles==222 && byx.estimated_cycles==606,
          "90-degree counterclockwise rotation reverses deterministic route-order winner");
    printf("ROUTES patternA_XY=%" PRIu64 " patternA_YX=%" PRIu64
           " patternB_XY=%" PRIu64 " patternB_YX=%" PRIu64 "\n",
           axy.estimated_cycles,ayx.estimated_cycles,bxy.estimated_cycles,byx.estimated_cycles);
}

static void probe_collectives(void) {
    tu_runtime_config_t rt=tu_runtime_config_default();
    rt.icc_switching_mode=TU_ICC_SWITCH_CUT_THROUGH;
    rt.icc_link_bytes_per_cycle=16; rt.icc_router_latency_cycles=5;
    tu_cluster_t *cl=tu_cluster_create(4,TU_TOPOLOGY_RING,0,&rt);
    CHECK(cl!=NULL,"collective cluster created"); if(!cl)return;
    float b[2]={7,8}, out[2]={0};
    tu_sram_write_bulk(tu_core_get_sram_o(cl->cores[0]),0,b,sizeof(b));
    CHECK(tu_cluster_broadcast(cl,0,0,32,sizeof(b))==0,"broadcast returns success");
    for(int c=1;c<4;c++){tu_sram_read_bulk(tu_core_get_sram_o(cl->cores[c]),32,out,sizeof(out));CHECK(out[0]==7&&out[1]==8,"broadcast bytes reach destination");}
    CHECK(cl->stats.total_icc_messages==3 && cl->stats.total_icc_bytes==24 && cl->stats.total_icc_cycles==23,
          "broadcast stats sum three immediate sends");

    for(int c=0;c<4;c++){float x[3]={(float)c,(float)c+1,(float)c+2};tu_sram_write_bulk(tu_core_get_sram_o(cl->cores[c]),64,x,sizeof(x));}
    uint64_t msgs=cl->stats.total_icc_messages, bytes=cl->stats.total_icc_bytes, cyc=cl->stats.total_icc_cycles;
    uint64_t corecyc[4]; for(int c=0;c<4;c++)corecyc[c]=cl->cores[c]->state.estimated_cycles;
    CHECK(tu_cluster_allreduce_sum_f32(cl,64,128,3)==0,"all-reduce returns success");
    for(int c=0;c<4;c++){float x[3];tu_sram_read_bulk(tu_core_get_sram_o(cl->cores[c]),128,x,sizeof(x));CHECK(x[0]==6&&x[1]==10&&x[2]==14,"all-reduce host sum written to each core");}
    CHECK(cl->stats.total_icc_messages-msgs==3 && cl->stats.total_icc_bytes-bytes==36 && cl->stats.total_icc_cycles==cyc,
          "all-reduce counts gather messages/bytes but no cycles");
    bool unchanged=true;for(int c=0;c<4;c++)unchanged &= cl->cores[c]->state.estimated_cycles==corecyc[c];
    CHECK(unchanged,"all-reduce adds no per-core estimated cycles");

    CHECK(tu_cluster_barrier(cl)==0,"barrier returns success");
    bool delta10=true;for(int c=0;c<4;c++)delta10 &= cl->cores[c]->state.estimated_cycles==corecyc[c]+10;
    CHECK(delta10 && cl->stats.total_barriers==1 && cl->barrier_counter==0,
          "barrier adds fixed twice-router-latency, updates stats, and leaves lifecycle counter zero");
    printf("COLLECTIVES broadcast_messages=3 broadcast_bytes=24 broadcast_cycles=23 "
           "allreduce_message_delta=%" PRIu64 " allreduce_byte_delta=%" PRIu64
           " allreduce_cycle_delta=%" PRIu64 " barrier_delta=10 barrier_state=0\n",
           cl->stats.total_icc_messages-msgs,cl->stats.total_icc_bytes-bytes,
           cl->stats.total_icc_cycles-cyc);
    tu_cluster_destroy(cl);
}

int main(void) {
    probe_config(); probe_equations(); probe_send(); probe_traffic();
    probe_routes(); probe_collectives();
    printf("CH12_PROBE SUMMARY failures=%d\n", failures);
    return failures ? 1 : 0;
}
