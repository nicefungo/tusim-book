#!/usr/bin/env python3
"""Fail-closed source/reachability audit for Chapter 12 at the frozen Tusim pin."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
PREDICATES = 0
HASHES = {
    "Makefile": "5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
    "tu_cmodel/tu_core.c": "0e4b3c6e206465748ae2d3d2e9871f3a6542a61cd1ddcddfff6886b9ed1f0eeb",
    "tu_cmodel/tu_core.h": "dc5c22065fb65be4353585ccbfd3bec6c9b9d70e976a51e87169bac79dd164e9",
    "tu_cmodel/tu_cluster.c": "7c968e95ba0a88fcc27f803be6aa337161bfa691505cdd39b01146252fa77b36",
    "tu_cmodel/tu_cluster.h": "1d8749ce994058c0d23804f365a62c57ceda23eebc721bc62797542e165bebf5",
    "tu_cmodel/tu_cmodel.c": "542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
    "tu_cmodel/tu_cmodel.h": "416a0d20776825498217ff5d4382f07ccb2ac9689bbe6c70cacd1bf13e7725af",
    "tu_cmodel/tu_config.h": "129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
    "tu_cmodel/tu_sram.c": "5a6ffcdd3f63c9c015bd628b5c44ded951785a128685b413b6db680f5d1753c0",
    "tu_cmodel/tu_sram.h": "aa62a942c83bfded4644c26eabf37acb815b7ac2883b53f6b3b8a585df4123d5",
    "tu_cmodel/infra/config.c": "17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
    "tu_cmodel/infra/config.h": "723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
    "config/tu_config.json": "6f9d292696b1ca5fa38ad3298e7f3a04c43095c0950f71dbe0c3c68b1f15f4db",
    "config/tu_config.yaml": "9fb4d87753139a5857107a6fdf56006fcb5adbe95ad30e9f8430c2e5c145910e",
    "scripts/gen_config.py": "5eab235067eaf6d5785352e48ef00417a18f5b0d05b25f40a82719e11bf8634a",
    "tests/test_multicore.c": "aaf516bb2f7080ea057ee4cd75405478fc84dbb571d490bdda605dbb8ae3dd4e",
    "tests/test_config.c": "e2bf7d9a1bbac06863e3b8c372fa1cb854927fc1aeb73a08c79e08cd3f1db821",
    "tests/test_interconnect_contention_sweep.c": "1380fe1284b8a3a8c11104c160538d6ef95ea18f6eac168be08aeedd2de3567a",
    "tests/test_interconnect_routing_sweep.c": "75179c70b04bc98b65ed9b647aaa36e847f415c90ee94e62b9b435492baefba4",
    "tests/test_interconnect_topology_sweep.c": "1222f166b8bf45248e8ed8ca57cbd47452471dad994bda754558089b4bdb24ee",
    "tests/test_interconnect_switching_sweep.c": "bd19e7762e5514122e1d7cdf5c79cf918f658a1c1b2caeb7e97b45de66cbdc01",
    "tests/test_multicore_scaling_sweep.c": "c164c20c9fed6fa8f9c873131438cccb470a53e3c6d0149f3fd9db1be6b66259",
    "docs/multicore-cluster.md": "6612f4cd499a0c9ac2e28ede0d88fdfa842bea9dd793c55ec86a561cd9adb3d4",
    "docs/exploration/interconnect-contention-traffic-matrix.md": "6e20ca4908446609dbcc265d15c702e3bfa441a812022e24fede2f36b34e629c",
    "docs/exploration/interconnect-mesh-routing-order.md": "fdf869c066d27c77f005d42cc6680ff90e7d9ca4597cadc8b68cac100c585ae6",
    "docs/exploration/interconnect-switching-modes.md": "c2a28844527aca8c6afed9111da810e54a6825f82f1362b2b1369f8507dd529b",
    "docs/exploration/interconnect-topology-sweep.md": "60754c76d3655835e52869d5da05305a5c8a8dfb185cb0bc4eed396222310315",
    "docs/exploration/multicore-scaling-gemm256.md": "7bdf0ddac330db3734df92824106c21976f3e95d192972bb0c8aeb49fcef4682",
}


def must(text: str, needle: str, label: str) -> None:
    global PREDICATES
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")
    PREDICATES += 1
    print(f"PREDICATE PASS {label}")


def must_not(text: str, needle: str, label: str) -> None:
    global PREDICATES
    if needle in text:
        raise AssertionError(f"{label}: unexpectedly found {needle!r}")
    PREDICATES += 1
    print(f"PREDICATE PASS {label}")


def pass_pred(label: str) -> None:
    global PREDICATES
    PREDICATES += 1
    print(f"PREDICATE PASS {label}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("pin")
    args = ap.parse_args()
    if args.pin != PIN:
        raise AssertionError(f"pin mismatch: {args.pin}")
    root = args.root.resolve()

    texts: dict[str, str] = {}
    for rel, expected in HASHES.items():
        data = (root / rel).read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise AssertionError(f"hash mismatch {rel}: {actual}")
        texts[rel] = data.decode("utf-8")
        print(f"HASH PASS {rel} {actual}")

    mk = texts["Makefile"]
    core = texts["tu_cmodel/tu_core.c"]
    core_h = texts["tu_cmodel/tu_core.h"]
    cluster = texts["tu_cmodel/tu_cluster.c"]
    cluster_h = texts["tu_cmodel/tu_cluster.h"]
    full_cfg = texts["tu_cmodel/infra/config.c"]
    runtime_cfg = texts["tu_cmodel/tu_config.h"]
    sram = texts["tu_cmodel/tu_sram.c"]
    generator = texts["scripts/gen_config.py"]
    test_mc = texts["tests/test_multicore.c"]
    shipped_json = texts["config/tu_config.json"]
    shipped_yaml = texts["config/tu_config.yaml"]
    multicore_doc = texts["docs/multicore-cluster.md"]
    topology_doc = texts["docs/exploration/interconnect-topology-sweep.md"]

    for obj in ["tu_core.o", "tu_cluster.o", "infra/config.o"]:
        must(mk, obj, f"archive-member-{obj}")
    for target in ["test-multicore:", "test-config:", "test-interconnect-contention-sweep:",
                   "test-interconnect-routing-sweep:"]:
        must(mk, target, f"focused-target-{target.rstrip(':')}")
    must(mk, "test-agen test-multicore", "aggregate-includes-multicore")
    must(mk, "test-trace test-config", "aggregate-includes-config")
    quick = mk[mk.index("test-quick:"):mk.index("# Extended random")]
    must_not(quick, "test-multicore", "quick-excludes-multicore")
    must_not(quick, "test-config", "quick-excludes-config")

    must(core_h, "tu_state_t      state;", "core-stores-state-snapshot")
    must(core_h, "void           *icc_buffer;", "core-declares-icc-buffer")
    must(core, "tu_core_t *g_default_core = NULL;", "core-default-singleton")
    must(core, "tu_init_with_config(cfg);", "core-create-reuses-global-init")
    must(core, "memcpy(&core->state, &g_tu, sizeof(tu_state_t));", "core-copies-global-state")
    must(core, "memset(&g_tu, 0, sizeof(tu_state_t));", "core-clears-global-state")
    must(core, "static void core_swap_in", "global-state-swap-in-helper")
    must(core, "static void core_swap_out", "global-state-swap-out-helper")
    for call in ["tu_run_asm", "tu_cmdq_sync_all", "tu_dma_load_w", "tu_dma_load_a", "tu_dma_store_o", "tu_mma"]:
        must(core, f"{call}(", f"core-wrapper-reaches-{call}")
    must_not(core, "pthread_", "no-core-thread-launch")
    must(multicore_doc, "Cores never share mutable state", "doc-claims-no-shared-mutable-state")
    must(multicore_doc, "all programs start simultaneously", "doc-claims-simultaneous-spmd-start")
    must(multicore_doc, "barriers synchronize across cores", "doc-claims-barrier-rendezvous")
    must(topology_doc, "reduce barrier overhead", "standalone-report-implies-topology-barrier-effect")

    must(cluster, "if (num_cores == 0 || num_cores > 256)", "cluster-count-range")
    constructor = cluster[cluster.index("tu_cluster_t *tu_cluster_create"):cluster.index("void tu_cluster_destroy")]
    must_not(constructor, "topology <", "constructor-no-topology-lower-bound-check")
    must_not(constructor, "topology >", "constructor-no-topology-upper-bound-check")
    must(cluster, "cluster->mesh_cols = (num_cores + mesh_rows - 1) / mesh_rows;", "mesh-ceiling-columns")
    must_not(constructor, "mesh_rows >", "constructor-no-mesh-rows-upper-bound")
    must_not(constructor, "1 + (num_cores - 1) / mesh_rows", "constructor-no-overflow-safe-mesh-ceiling")
    must(cluster, "tu_core_create_with_id(i, &cfg)", "cluster-creates-core-snapshots")
    for field in ["icc_switching_mode", "icc_contention_mode", "icc_mesh_routing_mode",
                  "icc_link_bytes_per_cycle", "icc_router_latency_cycles"]:
        must(runtime_cfg, field, f"runtime-declares-{field}")
        must(cluster, f"base_config->{field}", f"cluster-consumes-{field}")
    must(cluster, "forward < backward ? forward : backward", "ring-shortest-distance")
    must(cluster, "tu_abs_diff(src_row, dst_row) + tu_abs_diff(src_col, dst_col)", "mesh-manhattan-distance")
    must(cluster, "return route_cycles + serialization;", "cut-through-equation")
    must(cluster, "return (uint64_t)hops * (cluster->hop_latency + serialization);", "store-forward-equation")
    must(cluster, "bool clockwise = forward <= backward;", "ring-clockwise-tie")
    must(cluster, "bool x_first = cluster->mesh_routing_mode == TU_ICC_MESH_ROUTE_XY;", "mesh-route-order")
    must(cluster_h, "deterministic-routing\n * lower bound", "stale-header-lower-bound-claim")
    must(cluster_h, "true = wait for completion", "stale-header-blocking-claim")
    must(cluster_h, "Simulated interconnect latency", "stale-header-latency-result-claim")
    must(cluster_h, "all cores must reach this point before any proceeds", "stale-header-rendezvous-claim")
    must(cluster, "uint64_t shared_bound = stats->bottleneck_link_cycles + max_route_cycles;", "shared-link-heuristic-equation")
    traffic = cluster[cluster.index("int tu_cluster_estimate_traffic_cycles"):cluster.index("int tu_cluster_send")]
    must_not(traffic, "UINT64_MAX - max_route_cycles", "shared-score-no-overflow-guard")
    link_accum = cluster[cluster.index("static void add_link_service"):cluster.index("static int add_route_service")]
    must(link_accum, "links[(uint64_t)src * n + dst] += service;", "link-service-unchecked-addition")
    must(cluster_h, "uint32_t    size_bytes;", "message-size-u32-bounds-link-load")
    must(cluster, "uint32_t message_count,", "message-count-u32-bounds-link-load")

    send = cluster[cluster.index("int tu_cluster_send"):cluster.index("int tu_cluster_broadcast")]
    must(send, "void *tmp = malloc(msg->size_bytes);", "send-host-temporary")
    must(send, "tu_sram_read_bulk", "send-immediate-read")
    must(send, "tu_sram_write_bulk", "send-immediate-write")
    must(send, "dst_core->state.estimated_cycles += latency;", "send-destination-cycle-update")
    for unused in ["msg->tag", "msg->blocking", "msg->latency_cycles"]:
        must_not(send, unused, f"send-does-not-consume-{unused[5:]}")
    must(send, "msg->src_offset + msg->size_bytes", "send-32bit-offset-addition")
    must_not(send, "msg->src_offset > src_sram->total_size - msg->size_bytes", "send-no-overflow-safe-source-span-check")
    must_not(send, "msg->dst_offset > dst_sram->total_size - msg->size_bytes", "send-no-overflow-safe-destination-span-check")
    must(send, "cluster->stats.total_icc_cycles += latency;", "send-additive-cycle-sum")

    broadcast = cluster[cluster.index("int tu_cluster_broadcast"):cluster.index("int tu_cluster_allreduce_sum_f32")]
    must(broadcast, "for (uint32_t dst = 0; dst < cluster->num_cores; dst++)", "broadcast-sequential-loop")
    must(broadcast, "tu_cluster_send(cluster, &msg)", "broadcast-reuses-send")
    allreduce = cluster[cluster.index("int tu_cluster_allreduce_sum_f32"):cluster.index("/* ---- Synchronization ----")]
    must(allreduce, "uint32_t size_bytes = num_elements * sizeof(float);", "allreduce-32bit-size-product")
    must_not(allreduce, "total_size", "allreduce-no-explicit-region-bounds")
    must(allreduce, "accumulator[i] += tmp[i];", "allreduce-host-core-order-sum")
    must(allreduce, "tu_sram_write_bulk", "allreduce-host-writeback")
    must_not(allreduce, "tu_cluster_send", "allreduce-bypasses-send")
    must_not(allreduce, "total_icc_cycles", "allreduce-no-cycle-accounting")
    must(allreduce, "total_icc_messages += cluster->num_cores - 1", "allreduce-gather-message-count")
    barrier = cluster[cluster.index("int tu_cluster_barrier"):cluster.index("/* ---- SPMD Execution ----")]
    must(barrier, "uint64_t barrier_cycles = cluster->hop_latency * 2", "barrier-fixed-roundtrip")
    must(barrier, "cluster->stats.total_barriers++", "barrier-updates-stat-count")
    must_not(barrier, "barrier_counter", "barrier-lifecycle-counter-unused")
    must_not(barrier, "hop_distance", "barrier-topology-independent")
    spmd = cluster[cluster.index("int tu_cluster_spmd_execute"):cluster.index("/* ---- Statistics ----")]
    must(spmd, "for (uint32_t i = 0; i < cluster->num_cores; i++)", "spmd-serial-loop")
    must(spmd, "tu_core_execute_asm_text", "spmd-reaches-legacy-asm")
    must_not(spmd, "pthread_", "spmd-no-thread-launch")
    must(cluster_h, "Execute the same ASM program on all cores concurrently", "header-concurrency-claim-present")
    must(cluster, "(cluster->stats.total_icc_cycles * 1e-9);  /* rough */", "printed-bandwidth-implicit-1ghz")
    if cluster.count("icc_bandwidth_gbps") != 0:
        raise AssertionError("icc_bandwidth_gbps unexpectedly used in implementation")
    pass_pred("declared-bandwidth-field-unused-in-implementation")

    for field, parser_text in [
        ("multicore_enabled", 'parse_opt_bool(mc, "enabled", &cfg->multicore_enabled);'),
        ("num_cores", 'parse_opt_int64(mc, "num_cores", &iv)'),
        ("interconnect_mode", 'cfg->interconnect_mode = 2;'),
    ]:
        must(full_cfg, parser_text, f"full-config-parser-assigns-{field}")
    converter = full_cfg[full_cfg.index("tu_runtime_config_t tu_config_to_runtime"):full_cfg.index("/* ---- Load from JSON string ----")]
    for field in ["multicore_enabled", "num_cores", "interconnect_mode"]:
        must_not(converter, field, f"runtime-converter-drops-{field}")
    for field in ["icc_switching_mode", "icc_contention_mode", "icc_mesh_routing_mode",
                  "icc_link_bytes_per_cycle", "icc_router_latency_cycles"]:
        must(converter, f"rt.{field} = cfg->{field};", f"runtime-converter-retains-{field}")
    must(full_cfg, "interconnect link_bytes_per_cycle must be > 0", "full-config-validates-link-width")
    must(full_cfg, "interconnect mesh_routing must be xy or yx", "full-config-validates-route-order")
    expected_shipped = {
        "enabled": False, "num_cores": 1, "interconnect": "none",
        "switching": "legacy_hop_only", "contention": "ideal_parallel",
        "mesh_routing": "xy", "link_bytes_per_cycle": 16,
        "router_latency_cycles": 5, "cache_coherence": False,
    }
    actual_json = json.loads(shipped_json)["tu"]["multicore"]
    if actual_json != expected_shipped:
        raise AssertionError(f"shipped JSON multicore mismatch: {actual_json}")
    pass_pred("json-complete-multicore-values")
    for line in [
        "enabled: false", "num_cores: 1", 'interconnect: "none"',
        'switching: "legacy_hop_only"', 'contention: "ideal_parallel"',
        'mesh_routing: "xy"', "link_bytes_per_cycle: 16",
        "router_latency_cycles: 5", "cache_coherence: false",
    ]:
        must(shipped_yaml, line, f"yaml-multicore-{line.split(':', 1)[0]}")

    for needle, label in [
        ("mc = c['multicore']", "generator-reads-multicore-map"),
        ('TU_MULTICORE_ENABLED    {1 if mc["enabled"] else 0}', "generator-emits-enabled"),
        ('TU_NUM_CORES            {mc["num_cores"]}', "generator-emits-core-count"),
        ('TU_INTERCONNECT_MODE    {ic_map[mc["interconnect"]]}', "generator-emits-topology"),
        ('TU_ICC_SWITCHING_MODE          {switch_map[mc["switching"]]}', "generator-emits-switching"),
        ('TU_ICC_CONTENTION_MODE           {contention_map[mc["contention"]]}', "generator-emits-contention"),
        ('TU_ICC_MESH_ROUTING_MODE         {mesh_route_map[mc["mesh_routing"]]}', "generator-emits-route-order"),
        ('TU_ICC_LINK_BYTES_PER_CYCLE    {mc["link_bytes_per_cycle"]}', "generator-emits-link-width"),
        ('TU_ICC_ROUTER_LATENCY_CYCLES   {mc["router_latency_cycles"]}', "generator-emits-router-latency"),
    ]:
        must(generator, needle, label)

    bounds = sram[sram.index("static void bounds_check"):sram.index("uint64_t tu_sram_read")]
    must(bounds, "fprintf(stderr", "sram-bounds-only-reports")
    must_not(bounds, "abort(", "sram-bounds-does-not-abort")
    must_not(bounds, "return -1", "sram-bounds-does-not-return-status")
    read_bulk = sram[sram.index("uint64_t tu_sram_read_bulk"):sram.index("uint64_t tu_sram_write_bulk")]
    write_bulk = sram[sram.index("uint64_t tu_sram_write_bulk"):]
    must(read_bulk, "bounds_check(r, addr, bytes);", "bulk-read-calls-reporting-check")
    must(read_bulk, "memcpy(out, sram_data_ptr(r) + addr, bytes);", "bulk-read-proceeds-to-memcpy")
    must(write_bulk, "bounds_check(r, addr, bytes);", "bulk-write-calls-reporting-check")
    must(write_bulk, "memcpy(sram_data_ptr(r) + addr, data, bytes);", "bulk-write-proceeds-to-memcpy")

    test_calls = re.findall(r"^\s{4}(test_[a-z0-9_]+)\(\);$", test_mc, re.MULTILINE)
    if len(test_calls) != 16 or len(set(test_calls)) != 16:
        raise AssertionError(f"multicore main test calls: {test_calls}")
    pass_pred("focused-multicore-16-distinct-test-calls")
    must(test_mc, "return tests_failed ? 1 : 0;", "focused-multicore-fail-closed-exit")
    spmd_test = test_mc[test_mc.index("static void test_spmd_execution"):test_mc.index("/* ---- Main ----")]
    must(spmd_test, "tu_core_mma(", "spmd-named-test-uses-direct-mma")
    must_not(spmd_test, "tu_cluster_spmd_execute", "spmd-named-test-does-not-call-spmd-api")
    for finding in ["== 15", "== 79", "== 207", "== 133", "== 606 && yx.estimated_cycles == 222"]:
        must(test_mc, finding, f"focused-discriminating-{finding.replace(' ', '')}")

    def c_callers(pattern: str) -> set[str]:
        rx = re.compile(pattern)
        def without_comments(body: str) -> str:
            body = re.sub(r"/\*.*?\*/", "", body, flags=re.DOTALL)
            return re.sub(r"//.*", "", body)
        return {
            p.relative_to(root).as_posix()
            for p in root.rglob("*.c")
            if rx.search(without_comments(p.read_text(encoding="utf-8")))
        }

    inventories = [
        (r"tu_cluster_estimate_traffic_cycles\(", {
            "tu_cmodel/tu_cluster.c", "tests/test_multicore.c",
            "tests/test_interconnect_contention_sweep.c", "tests/test_interconnect_routing_sweep.c"},
         "exact-c-callers-traffic-estimator"),
        (r"tu_cluster_estimate_transfer_cycles\(", {
            "tu_cmodel/tu_cluster.c", "tests/test_multicore.c"},
         "exact-c-callers-transfer-estimator"),
        (r"tu_cluster_hop_distance\(", {
            "tu_cmodel/tu_cluster.c", "tests/test_multicore.c"},
         "exact-c-callers-hop-distance"),
        (r"tu_cluster_send\(", {"tu_cmodel/tu_cluster.c", "tests/test_multicore.c"},
         "exact-c-callers-send"),
        (r"tu_cluster_broadcast\(", {"tu_cmodel/tu_cluster.c", "tests/test_multicore.c"},
         "exact-c-callers-broadcast"),
        (r"tu_cluster_allreduce_sum_f32\(", {"tu_cmodel/tu_cluster.c", "tests/test_multicore.c"},
         "exact-c-callers-allreduce"),
        (r"tu_cluster_barrier\(", {"tu_cmodel/tu_cluster.c", "tests/test_multicore.c"},
         "exact-c-callers-barrier"),
        (r"tu_cluster_spmd_execute\(", {"tu_cmodel/tu_cluster.c"},
         "exact-c-callers-spmd-implementation-only"),
        (r"tu_cluster_create\(", {"tu_cmodel/tu_cluster.c", "tests/test_multicore.c"},
         "exact-c-callers-cluster-constructor"),
    ]
    for pattern, expected, label in inventories:
        actual = c_callers(pattern)
        if actual != expected:
            raise AssertionError(f"{label}: expected={sorted(expected)} actual={sorted(actual)}")
        pass_pred(label)

    standalone = ["tests/test_interconnect_topology_sweep.c", "tests/test_interconnect_switching_sweep.c"]
    for rel in standalone:
        body = texts[rel]
        must_not(body, '#include "tu_cmodel/', f"standalone-sweep-does-not-include-cmodel-{Path(rel).stem}")
        must_not(body, "tu_cluster_estimate_transfer_cycles(&", f"standalone-sweep-does-not-call-cluster-{Path(rel).stem}")
    for rel in ["tests/test_interconnect_contention_sweep.c", "tests/test_interconnect_routing_sweep.c"]:
        must(texts[rel], "tu_cluster_estimate_traffic_cycles", f"linked-sweep-calls-estimator-{Path(rel).stem}")

    print(f"CH12_SOURCE_AUDIT PASS pin={PIN} hashes={len(HASHES)} predicates={PREDICATES} checks={len(HASHES) + PREDICATES}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"CH12_SOURCE_AUDIT FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
