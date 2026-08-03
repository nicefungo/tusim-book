# Chapter 12 — Multi-Core Clusters and Interconnect Heuristic Estimates

Tusim edition commit: `e918c80b6fce833cd1fcae97730fa841c2176f25`

## Learning objectives

After this chapter, you should be able to:

1. distinguish core snapshots, functional endpoint communication, isolated transfer estimates, simultaneous-traffic heuristic scores, additive counters, and calibrated hardware predictions;
2. trace multicore and inter-core communication (ICC) configuration from full JSON through runtime conversion to explicit cluster construction;
3. derive Tusim's ring/mesh distance and legacy/cut-through/store-and-forward equations under named assumptions;
4. explain why shared-link heuristic scores expose route-load concentration without simulating queues or arbitration;
5. compare ring/mesh and XY/YX alternatives by traffic regime rather than selecting a universal winner;
6. classify broadcast, all-reduce, barrier, and single program, multiple data (SPMD) according to their actual functional and timing contracts;
7. audit counter producers and intervals before combining metrics; and
8. design fail-closed, bounded experiments that preserve unsupported safety and calibration boundaries.

## Prerequisite graph

This chapter assumes:

- Chapter 2's evidence ladder and snapshot-conformance discipline;
- Chapter 4's distinction among declared, parsed, converted, consumed, and effective configuration;
- Chapter 5's ownership and process-global-state vocabulary;
- Chapter 9's W/A/O SRAM regions and capacity boundaries;
- Chapter 10's separation of functional transfer, service estimates, timestamps, and completion; and
- Chapter 11's lesson that shared names do not prove an integrated execution stack.

```text
Chapter 2 evidence discipline
          │
          ├──── Chapter 4 configuration contracts
          ├──── Chapter 5 state and ownership
          ├──── Chapter 9 SRAM boundaries
          ├──── Chapter 10 transfer lifecycles
          └──── Chapter 11 reachability discipline
                         │
                         ▼
          Chapter 12 multicore/interconnect heuristic estimates
```

This chapter does not reopen MMA arithmetic, SRAM banking, DMA descriptor ownership, or command-queue dependency semantics. It asks how several core snapshots communicate functionally and how Tusim's analytical interconnect surfaces can support bounded architecture comparisons.

## Opening architecture question: when does a topology estimate distinguish a design?

A compiler team has mapped sixteen tensor-unit partitions onto sixteen cores. The placement has three attractive properties: each core fits its local SRAM budget, the compute tiles are balanced, and the final partial results can be reduced to one destination. The remaining architecture question sounds simple:

> Should the machine connect those cores with a ring or a mesh?

A hop-count table appears to answer immediately. A square mesh has a smaller diameter than a ring, so the mesh seems better. That conclusion is premature. The answer changes when the traffic changes. At Tusim's pinned snapshot, the linked simultaneous-traffic sweep gives these cut-through, shared-link heuristic scores for sixteen cores and 4 KiB messages:

| Traffic | Ring | 4×4 mesh | Smaller heuristic score for this mapping |
|---|---:|---:|---|
| neighbor sequence `i→(i+1) mod 16` | 261 cycles | 286 cycles | ring |
| hotspot fan-in to core 0 | 2,088 cycles | 3,102 cycles | ring |
| all-to-all | 9,256 cycles | 4,126 cycles | mesh |

For all-to-all, the mesh score is 55.4% lower. For this hotspot mapping, the mesh score is 48.6% higher. The reversal is not noise. A ring splits shortest-path traffic in two directions; deterministic mesh routing can concentrate fan-in on one directed link. More links help distributed traffic, but more links do not automatically help every placement.

Even these numbers answer only a restricted question. They are deterministic outputs of one route-load heuristic under simultaneous injection. They do not come from router queues, arbitration, virtual channels, backpressure, physical wires, or calibrated hardware. In the same source tree, a point-to-point send copies bytes immediately on the host, an all-reduce computes on the host without interconnect-cycle accounting, and a barrier only adds an estimate. Treating all of those operations as one coherent network simulation would collapse several different fidelity levels into one misleading number.

This chapter develops a disciplined alternative. It shows how to decide:

1. which multi-core behavior Tusim executes functionally;
2. which configuration reaches the cluster that is actually constructed;
3. whether a reported cycle count is an isolated estimate, a simultaneous-traffic heuristic score, an additive counter, or absent;
4. which ring, mesh, switching, contention, and route alternatives remain plausible in different regimes; and
5. what additional evidence is required before any of those alternatives becomes a physical network-on-chip (NoC) recommendation.

The source basis is the frozen edition commit `e918c80b6fce833cd1fcae97730fa841c2176f25`. Exact commands, source hashes, mutation controls, logs, and retained manifests are recorded in the [Chapter 12 audit](../../experiments/ch12-multicore-interconnect-audit-2026-07-28.md).

### Source map

| Contract | Exact pinned source or test |
|---|---|
| core snapshots and global compatibility swaps | `tu_cmodel/tu_core.{h,c}`, `tu_cmodel/tu_cmodel.{h,c}` |
| cluster construction, topology, transfer equations, traffic heuristic | `tu_cmodel/tu_cluster.{h,c}` |
| send, broadcast, all-reduce, barrier, and SPMD helpers | `tu_cmodel/tu_cluster.c` |
| full-config parse, validation, and runtime conversion | `tu_cmodel/infra/config.{h,c}`, `tu_cmodel/tu_config.h`, `config/tu_config.json` |
| generated compile-time configuration | `scripts/gen_config.py`, `config/tu_config.yaml` |
| focused multicore regression | `tests/test_multicore.c` |
| linked traffic and routing sweeps | `tests/test_interconnect_contention_sweep.c`, `tests/test_interconnect_routing_sweep.c` |

All paths in this table refer to the edition commit above. The audit record gives exact hashes and reachability predicates rather than treating filenames as evidence by themselves.

---

## 12.1 The decision begins with four different contracts

“Does the model support multi-core?” is too coarse to be useful. Tusim exposes at least four contracts that must be audited separately.

| Contract | Question it can answer | What it cannot establish |
|---|---|---|
| **core-state facade** | Can several core snapshots retain source-observable private state and be invoked through compatibility wrappers? | complete W/A/O isolation, concurrent host safety, independent process-global execution |
| **functional communication** | Do endpoint bytes change as specified by send, broadcast, or all-reduce? | routed transport, overlap, queue service, physical latency |
| **analytical interconnect model** | Under named topology and traffic assumptions, what deterministic isolated estimate or shared-link heuristic score is returned? | a legal schedule, a makespan bound, cycle-accurate router behavior, sustained throughput, fairness |
| **calibration contract** | Does a modeled quantity predict RTL, FPGA, or silicon under a stated mapping? | nothing here—the selected evidence contains no such calibration |

The distinction matters because the contracts have different producers. `tu_cluster_send()` performs a host copy and adds one isolated estimate. `tu_cluster_estimate_traffic_cycles()` analyzes a simultaneous message set but moves no payload. `tu_cluster_allreduce_sum_f32()` changes output bytes but bypasses both send and the traffic estimator. A correct chapter must preserve these seams rather than smoothing them into a single “NoC latency” story.

A useful evidence ladder is:

```text
source declaration
    -> parsed value
    -> converted runtime field
    -> constructed consumer
    -> functional byte effect
    -> isolated estimate
    -> simultaneous-traffic heuristic score
    -> queued/arbitrated network
    -> calibrated hardware prediction
```

Tusim reaches different rungs for different APIs. A claim may move up the ladder only when its own producer and test justify the move.

---

## 12.2 A cluster owns snapshots, not concurrent hardware instances

The public types suggest a clean hierarchy: `tu_cluster_t` owns an array of `tu_core_t *`, and each core contains a `tu_state_t` snapshot plus a core identifier, ICC buffer declaration, and local counters. Cluster construction creates one core at a time with `tu_core_create_with_id()` and copies the base runtime configuration into each creation path.

The compatibility mechanism is the important part. The legacy cmodel still operates through process-global `g_tu` state. Core creation initializes that legacy state, copies it into the new core's snapshot, and clears the global object. Core wrapper operations later:

1. swap the selected snapshot into `g_tu`;
2. call the legacy DMA, MMA, command-queue, or ASM function;
3. copy the resulting state back to the core; and
4. clear or restore the global compatibility state as implemented.

This supports caller-sequenced use of several snapshots. It does not establish that multiple host threads can enter different cores simultaneously. There is no core-side thread launch and no cluster-wide locking contract around the global swap. The focused test directly observes distinct W-SRAM backing pointers and retained different W values. Source allocation suggests separately owned A/O storage, but the audited probes do not establish complete W/A/O pointer-and-value isolation. The safe term is therefore **global-state-swapping facade, exercised sequentially**, not “serialized core implementation” or a proof of reentrant execution.

This is a recurring cmodel design trade-off.

| Design | Gain | Cost and risk |
|---|---|---|
| snapshot plus global compatibility swap | reuses mature single-core implementation; small integration change | caller-sequenced use; aliasing and ownership scrutiny; no automatic thread safety |
| explicit context parameter through every subsystem | reentrant ownership is representable; dependencies become visible | broad API migration and verification burden |
| one process per modeled core | strong address-space isolation; simple legacy reuse | IPC overhead; harder synchronized timing and shared statistics |

Tusim implements the first alternative at this pin. It is reasonable for functional exploration when the caller serializes access. It is the wrong evidence for host-thread parallel speedup.

### Construction validation is partial

`tu_cluster_create()` rejects zero cores, more than 256 cores, and a mesh with zero rows. For values whose numerator does not overflow `uint32_t`, it computes mesh columns by ceiling division:

```text
mesh_cols = ceil(num_cores / mesh_rows)
```

The source uses `(num_cores + mesh_rows - 1) / mesh_rows`, not the overflow-safe equivalent `1 + (num_cores - 1) / mesh_rows`. A sufficiently large nonzero `mesh_rows` can wrap the numerator, produce zero columns, and make later division or modulo unsafe. Callers must bound `mesh_rows` so `num_cores + mesh_rows - 1 <= UINT32_MAX`; the audit does not execute the hazardous downstream case.

The constructor also does not reject an out-of-range topology enum. Callers must therefore provide one of the named values: NONE, RING, or MESH. A valid full configuration does not make an arbitrary hand-built runtime structure valid.

---

## 12.3 Configuration has two ladders, not one

The full configuration contains a `tu.multicore` section. Three fields describe a requested deployment shape:

- `multicore_enabled`;
- `num_cores`;
- `interconnect_mode`.

Five additional fields parameterize the interconnect estimator:

- `icc_switching_mode`;
- `icc_contention_mode`;
- `icc_mesh_routing_mode`;
- `icc_link_bytes_per_cycle`;
- `icc_router_latency_cycles`.

All eight can be declared and parsed in the full configuration. They do not all follow the same path.

| Field group | Parsed in full config | Retained by `tu_config_to_runtime()` | Retained in cluster state |
|---|---:|---:|---:|
| enable, core count, topology request | yes | no | no; count and topology are explicit constructor arguments |
| switching, contention, route order, link width, router latency | yes | yes | yes |

The canonical probe deliberately parses an enabled eight-core mesh request, converts it, and then explicitly constructs a four-core ring. The resulting observation is:

```text
CONFIG parsed_enabled=1 parsed_cores=8 parsed_topology=2 cluster_cores=4 cluster_topology=1 sw=2 contention=1 route=1 link=32 router=7
```

The first three values survive in the full configuration object but do not instantiate a cluster. The explicit constructor arguments choose four cores and a ring. The five ICC fields cross the converter and become cluster state. Separate equation and routing probes discriminate their direct consumers; the sealed evidence does not perform a one-field-at-a-time parse→convert→construct→effect A/B chain. Retention and effect are therefore separate claims.

This distinction changes how a compiler or runtime should use the configuration:

- a deployment layer must translate the requested enable/count/topology fields into an explicit cluster-construction call;
- the cmodel does not perform that orchestration merely because JSON says `multicore_enabled: true`;
- direct tests that hand-build `tu_runtime_config_t` bypass some full-config validation; and
- a topology result is not tied to the shipped configuration unless the exact constructor call is also known.

At the pinned edition, the shipped JSON selects disabled, one core, topology NONE, legacy hop-only switching, ideal-parallel contention, XY routing, 16 bytes/cycle, and five router cycles. The shipped YAML agrees on the audited multicore/ICC values. `scripts/gen_config.py` consumes the YAML fields into compile-time macros, including enable, count, topology, switching, contention, route order, link width, and router latency. That generated-header ladder is distinct from the parsed JSON/full-config ladder, and its enable/count/topology macros still do not instantiate a runtime cluster.

### Configuration-test qualification

The exact focused config source contains an ICC parsing and validation case. In the canonical build that case prints PASS. The process later aborts during a different TU-init/MMA case with process status 134, so the suite is not a passing 20/20 gate in this environment. Historical exploration reports that say 20/20 are not substituted for the observed process result. Runtime retention and direct-consumer effects are established by separate bounded custom-probe observations instead.

That is fail-closed evidence practice: retain the useful passing sub-observation, retain the later failure, and avoid inventing a root cause that this chapter did not isolate.

---

## 12.4 Topology supplies geometry, not a router

Tusim represents three topology choices.

### NONE

NONE describes isolated cores. A route between distinct endpoints is unreachable. This is useful for batch or tenant isolation studies where no inter-core communication should occur.

### RING

For `N` cores, ring distance is the shorter of clockwise and counter-clockwise distance:

```text
h_ring(s,d) = min((d-s) mod N, (s-d) mod N)
```

The traffic estimator chooses clockwise when both directions are equally short. That tie rule is deterministic and affects directed-link load. It is not an arbitration policy.

### MESH

A mesh maps core identifier `i` to:

```text
row = floor(i / mesh_cols)
col = i mod mesh_cols
```

Distance is Manhattan distance:

```text
h_mesh(s,d) = |row_s-row_d| + |col_s-col_d|
```

The last row may be partially populated. Neighbor enumeration checks whether candidate identifiers exist. The distance formula and deterministic route enumeration remain abstract: there is no modeled wire length, router radix delay, or clock closure penalty for adding mesh ports.

### What topology comparison can say

Topology determines:

- endpoint adjacency;
- minimum hop count;
- deterministic path occupancy under the selected route rule; and
- the number and placement of modeled directed links.

Topology does not determine by itself:

- queue depth or packet service order;
- router pipeline stages;
- flit width, headers, or credits;
- physical wire delay;
- area and power; or
- a collective algorithm.

On-chip network design normally requires explicit flow-control, buffering, routing, and physical assumptions; hop count alone is not a complete network model [DT01](../../references/foundations.md#dt01-on-chip-interconnection-networks).

---

## 12.5 Three isolated transfer equations preserve three architecture alternatives

Tusim's isolated transfer estimator takes payload bytes `B`, route length `h`, link payload width `W` in bytes/cycle, and router latency `L` in cycles/hop. Its branch order matters. A null cluster or unreachable/invalid route returns `UINT64_MAX`. Next, `h == 0` or `B == 0` returns zero before switching mode or link width is inspected. For the remaining `h > 0`, `B > 0` case, legacy mode returns `hL`; non-legacy modes return `UINT64_MAX` when `W == 0`; cut-through and store-and-forward use the equations below; and an unsupported mode returns `UINT64_MAX`. Define serialization service:

```text
S = ceil(B / W)
```

The implemented modes are:

```text
legacy hop-only:     T_legacy = hL
cut-through:         T_cut    = hL + S
store-and-forward:   T_store  = h(L + S)
```

For 1 KiB, three hops, 16 bytes/cycle, and five cycles/router:

```text
S = 64
T_legacy = 15
T_cut = 79
T_store = 207
```

The canonical probe reproduces exactly:

```text
EQUATIONS legacy=15 cut=79 store=207
```

### Why retain all three modes?

They represent materially different exploration regimes.

| Mode | Useful regime | Gain | Sacrifice |
|---|---|---|---|
| legacy hop-only | compatibility and functional studies that intentionally disable payload service | stable old results; isolates topology latency term | physically optimistic; bandwidth has no effect |
| cut-through | early study of pipelined multi-hop payloads | serialization paid once; long routes can be much cheaper | implies buffering/flow-control obligations not implemented here |
| store-and-forward | simple packet-level bridge or full-packet forwarding hypothesis | easy conceptual service rule | full serialization at every hop; potentially large buffers and energy |

Cut-through is not “free store-and-forward improvement.” A physical cut-through or wormhole network needs buffer, credit, virtual-channel, deadlock, and backpressure contracts. Store-and-forward may simplify control but needs complete-packet storage at intermediate stages. Tusim quantifies neither implementation cost.

### One hop is a useful sanity check

At one hop, cut-through and store-and-forward are identical in this estimator:

```text
L + S = 1 × (L + S)
```

The switching choice matters only when a message crosses more than one hop. This is a good example of a discriminating experiment: a one-hop test can validate arithmetic but cannot distinguish the two architecture alternatives.

### Additive estimates are not elapsed time

Point-to-point sends add their isolated estimates into `total_icc_cycles` and into the destination core's `estimated_cycles`. Repeated sends therefore accumulate estimates. The sum is not automatically a wall-clock schedule because overlap, injection time, and resource service order are absent.

---

## 12.6 Point-to-point send is immediate endpoint behavior

`tu_cluster_send()` operates only on O-SRAM at this pin. For a nonzero message it:

1. validates core identifiers and compares 32-bit offset-plus-size expressions with SRAM capacity;
2. allocates a host temporary buffer;
3. reads source O-SRAM into that buffer;
4. writes the buffer immediately into destination O-SRAM;
5. computes an isolated transfer estimate;
6. increments message, byte, and cycle statistics; and
7. adds the estimate to the destination core.

The canonical probe uses `blocking=false`, `tag=77`, and caller `latency_cycles=999`. After the call, the bytes match and all three descriptor fields remain unchanged:

```text
SEND blocking=0 descriptor_latency=999 stats_messages=1 stats_bytes=16 stats_cycles=15 dst_delta=15
```

This proves several negative contracts:

- `blocking` does not cause waiting behavior;
- `tag` does not perform matching or ordering;
- caller `latency_cycles` is not consumed or overwritten;
- the byte copy completes before return; and
- only the destination core receives the isolated cycle increment.

The API is useful as a functional endpoint-transfer primitive. It is not a packet injection API.

### Bounds are a caller obligation too

The send helper compares `offset + size` with SRAM capacity using 32-bit arithmetic, but it does not detect wraparound before that comparison. A wrapped sum can therefore appear in range. The canonical probe uses small, in-range values. Trusted callers must establish both `size <= capacity` and `offset <= capacity - size` for source and destination before entry.

Executing an overflow or out-of-range case merely to “see what happens” would test undefined or unsafe behavior, not an architecture contract. Static source review is the appropriate evidence for this limitation.

---

## 12.7 Simultaneous traffic adds a route-load heuristic

The traffic-matrix API accepts an array of messages interpreted as simultaneous. It does not call send and does not alter endpoint bytes. For each message, it computes the isolated estimate and enumerates directed links along the deterministic route.

For each directed link `ell`, define its service-cycle load by rounding each routed message separately, as the implementation does:

```text
C_ell = sum over messages i using ell of ceil(B_i / W)
```

This is not generally equal to `ceil(sum_i B_i / W)` when messages are not width-aligned. Two aggregate values then matter:

```text
T_ideal = max_i(T_isolated,i)
```

and, in shared-link mode:

```text
T_shared = max(
    T_ideal,
    max_ell(C_ell) + max_i(h_i L)
)
```

The bottleneck serialization term is a necessary service term for the busiest modeled directed link. The maximum isolated term is also a useful independent floor under the model's assumptions. The implemented equation then adds the **global** maximum route-latency term to the bottleneck-link term, even when those maxima come from unrelated, disjoint flows. That final sum is a deterministic heuristic score, not a proved service bound or makespan bound. It does not construct a legal packet schedule or account for service dependencies across multiple links.

### A discriminating two-message example

Two one-hop 1 KiB cut-through messages have isolated estimate:

```text
5 + ceil(1024/16) = 69 cycles
```

If both use directed link `0→1`, the link service is the sum of the two separately rounded 1 KiB services. Here the messages are width-aligned, so this also equals the aggregate-payload ceiling:

```text
ceil(2048/16) = 128 cycles
T_shared = max(69, 128 + 5) = 133 cycles
```

If they use disjoint directed links, each link serves only 1 KiB and the returned score remains 69. Ideal-parallel mode also remains 69 even for the overlapping pair. The canonical observation is:

```text
TRAFFIC same=133 disjoint=69 ideal=69 bottleneck=128 link=0->1
```

That four-number result distinguishes three things:

- isolated per-message latency;
- finite-width link sharing; and
- ideal overlap policy.

It still cannot identify which packet waits, when it waits, or whether downstream queues block upstream routers.

### Why the combined score is not a lower bound

A real shared-link fabric must provide at least the busiest-link serialization service under the stated payload mapping, and it cannot complete faster than its longest isolated message under the same abstract assumptions. Those two statements do **not** justify adding a route maximum from one flow to a bottleneck service maximum from another.

The skeptical review reproduced a counterexample on a 4×4 XY mesh. Two messages share `0→1`, while an unrelated six-hop message uses disjoint links. Tusim reports:

```text
HEURISTIC_COUNTEREXAMPLE isolated=94 bottleneck=128 estimated=158 shared_pair_term=133 link=0->1
```

The shared pair's natural service expression completes by 133 while the disjoint long route can overlap it. The implemented 158 therefore exceeds that feasible schedule and cannot be called a makespan lower bound. Exact outputs such as 133, 606, and 222 remain valid snapshots of the implemented equation, but their classification is **heuristic estimate**.

A real fabric may take longer than either necessary term because of:

- staggered or bursty injection;
- packet headers and flit rounding;
- arbitration;
- finite buffers;
- backpressure;
- virtual-channel interactions;
- head-of-line blocking; and
- router pipeline occupancy.

Calling the result “contention latency” or “lower bound” would imply a schedule or proof the model does not contain. “Deterministic route-load heuristic score” states exactly what the evidence supports.

Each per-message service and `message_count` is 32-bit, so one directed-link accumulator cannot overflow `uint64_t` from values representable by the declared API widths alone: `UINT32_MAX × UINT32_MAX < UINT64_MAX`. The later addition of `bottleneck_link_cycles + max_route_cycles` is unchecked and can wrap for extreme topology/latency inputs. Trusted callers must bound that final sum; the audit records the path statically and does not execute an unsafe overflow case.

---

## 12.8 Route order couples placement to the bottleneck

For a mesh, Tusim retains two deterministic minimal route orders:

- **XY:** move in the column/X dimension first, then row/Y;
- **YX:** move in the row/Y dimension first, then column/X.

Both have the same Manhattan hop count. They can produce different directed-link occupancy.

The canonical 4×4 custom probe uses nine 1 KiB messages per pattern. Pattern A is the Cartesian endpoint set `{1,2,3} × {4,8,12}`: top-row sources excluding core 0 send to left-column destinations excluding core 0. Pattern B is `{0,4,8} × {13,14,15}`: left-column sources excluding core 12 send to bottom-row destinations excluding core 12. Pattern B is a 90-degree counterclockwise rotation of pattern A, not its coordinate transpose. The exact result is:

```text
ROUTES patternA_XY=606 patternA_YX=222 patternB_XY=222 patternB_YX=606
```

YX lowers pattern A's heuristic score by 63.4%; XY provides the equal benefit after the 90-degree rotation to pattern B. Neither is universally better.

This supports three architecture conclusions.

1. **Placement and routing are one decision.** A compiler that knows fixed XY routing should avoid mappings that funnel traffic through one XY corner.
2. **Runtime-selectable XY/YX has a cost.** It can improve mapping flexibility but adds an architectural mode, control state, and verification combinations. A physical implementation may instead hard-wire one order.
3. **Deterministic does not mean deadlock-free by observation.** Deadlock freedom depends on channel dependencies and flow control, not merely on one successful path enumeration. Dimension-order routing has classical proofs under specified channel assumptions [DS87](../../references/foundations.md#ds87-deadlock-free-routing); those proofs are not automatically inherited by this queue-free estimator.

Adaptive routing remains outside the chapter. It would require queue state, path selection, arbitration, liveness, and fairness evidence that XY/YX selection does not provide.

---

## 12.9 Ring versus mesh is a traffic-regime decision

The linked sweep makes the central lesson concrete.

### Neighbor traffic

For the sweep's neighbor sequence `i→(i+1) mod N`, the sixteen-core ring reports 261 cycles and the 4×4 mesh 286. The identifier wrap `15→0` is one ring hop but six mesh hops. The result is about mapping plus topology, not inherent ring superiority for all local traffic.

### Hotspot fan-in

For fifteen sources targeting core 0, the ring reports 2,088 and the mesh 3,102. Ring shortest paths split around two directions. Fixed XY mesh routes concentrate service on directed link `4→0`.

A compiler can respond by changing the reduction root, using a tree, spreading routes, or changing placement. Tusim does not implement those collective alternatives in this API, but the bottleneck endpoint is useful diagnostic evidence.

### All-to-all

For 240 directed messages, the ring reports 9,256 and the mesh 4,126. The mesh's larger link set distributes all-to-all service more effectively under this route mapping.

### Decision matrix

| Alternative | Performance regime | Area/power expectation | Control and verification | Accuracy effect |
|---|---|---|---|---|
| ring | simple/local traffic; some split fan-in; small core counts | fewer ports and links; may need wider/faster global links | simple shortest-path rule; equal-distance tie still matters | none; transport/timing only |
| mesh | distributed all-to-all; shorter diameter; spatial placements aligned with grid | more ports, links, and clocked state; shorter logical routes may reduce some activity | route order and hotspot verification; physical layout more complex | none |
| wider links | serialization-dominated payloads | more wires, buffers, mux width, and switching energy | width and packetization verification | none |
| lower router latency | short packets or many hops | usually harder pipeline/clock target | timing closure and bypass/control burden | none |

Tusim quantifies the first column only through named analytical assumptions. It does not quantify the other costs. A defensible design review should retain both ring and mesh until physical, power, and queue evidence narrows the choice.

---

## 12.10 Collectives do not share one timing contract

The public names broadcast, all-reduce, barrier, and SPMD invite a conventional distributed-systems interpretation. Their implementations differ materially.

### Broadcast is repeated immediate send

Broadcast loops over every destination other than the source and calls point-to-point send sequentially. On four ring cores with an 8-byte payload, the canonical probe observes:

```text
broadcast_messages=3 broadcast_bytes=24 broadcast_cycles=23
```

For bounded, in-range inputs and a successful call, this is three endpoint copies and the sum of three isolated estimates. It is not a multicast tree, simultaneous fan-out, or one injected packet replicated by routers. The loop is non-transactional: if a later destination fails, earlier destinations and their counter updates are not rolled back.

### All-reduce is host-orchestrated FP32 computation

`tu_cluster_allreduce_sum_f32()`:

1. allocates host accumulation and temporary buffers;
2. reads each core's source O-SRAM;
3. adds FP32 values in ascending core-index order; and
4. writes the result to every core's destination O-SRAM.

For bounded, in-range inputs and a successful call, it increments `N-1` messages and gather-byte counts. It does not call send, add cluster ICC cycles, or add per-core estimated cycles. The four-core, three-element probe observes:

```text
allreduce_message_delta=3 allreduce_byte_delta=36 allreduce_cycle_delta=0
```

The zero cycle delta means **timing is absent**, not that hardware all-reduce costs zero cycles. The byte count also describes only the modeled gather side; result distribution is not represented in those statistics.

Real collective design compares ring, recursive doubling/halving, trees, topology-aware schedules, and bandwidth-optimal algorithms under specific network assumptions. The literature can supply that algorithmic vocabulary [PY09](../../references/foundations.md#py09-bandwidth-optimal-all-reduce), but it does not validate Tusim's host helper as a routed collective.

The helper also multiplies element count by `sizeof(float)` in a 32-bit value and performs no explicit region-span checks before reading every core and writing every destination. Trusted callers must provide small, in-range extents. The underlying SRAM bounds helper reports violations but does not return failure or stop the subsequent bulk `memcpy`, so a logged error is not a containment boundary.

### Barrier is an estimate, not rendezvous

Barrier increments `stats.total_barriers` and evaluates:

```text
2 × hop_latency
```

for every core. The multiplication occurs in 32-bit unsigned arithmetic before assignment to the 64-bit delta. It equals the mathematical product only when `hop_latency <= UINT32_MAX / 2`; larger hand-built runtime values wrap before widening. The controlled probe uses `hop_latency = 5`. The helper does not record which cores arrived, block early arrivals, or depend on topology. The separately declared `barrier_counter` remains zero. The canonical probe observes:

```text
barrier_delta=10 barrier_state=0
```

A historical topology report said mesh hop reduction could improve barrier overhead. That implication is not reachable through this implementation because the barrier estimate is topology-independent.

### SPMD is implementation-only and serial

The SPMD helper loops over cores and calls the legacy text interpreter for each core in sequence. There is no host-thread launch or common start event. More importantly, the audited exact C-call inventory contains only the implementation itself. The focused test's function named “SPMD execution” directly calls per-core MMA and does not invoke `tu_cluster_spmd_execute()`.

The safe claim is therefore:

> Tusim contains an implementation-only serial SPMD API loop at this pin.

The unsafe claims are simultaneous start, concurrent launch, barrier-synchronized SPMD execution, or focused SPMD API coverage.

---

## 12.11 Counters must name their producer and interval

Cluster statistics include total ICC messages, bytes, cycles, barriers, and a printed bandwidth quantity. These values do not all describe one interval.

| Quantity | Producer | Meaning at the pin |
|---|---|---|
| `total_icc_messages` | send; broadcast through send; partial all-reduce update | additive operation count with API-specific semantics |
| `total_icc_bytes` | same producers | endpoint bytes counted by each API, not routed-link byte-hops |
| `total_icc_cycles` | send/broadcast isolated estimates | sum of per-send estimates; not elapsed matrix time |
| traffic `estimated_cycles` | traffic-matrix estimator result | one ideal-parallel maximum or shared-link heuristic score for the supplied simultaneous set |
| core `estimated_cycles` | send destination update; barrier update; other core operations | additive core-local estimate from multiple domains |
| `stats.total_barriers` | barrier call | number of barrier API calls |
| `barrier_counter` | no update in audited barrier | unused lifecycle field for this operation |
| printed ICC bandwidth | derived from total bytes/cycles | implicit 1 GHz bytes/cycle conversion, not measured link throughput |

The declared `icc_bandwidth_gbps` field is not assigned by the audited implementation. Printed bandwidth is recomputed from aggregate byte and cycle sums under an implicit clock conversion. It should not be combined with traffic-matrix latency or called measured GB/s.

A disciplined report should write statements such as:

- “The send API accumulated 15 isolated estimate cycles.”
- “The simultaneous shared-link heuristic score was 133 cycles.”
- “All-reduce changed bytes but added no interconnect-cycle estimate.”

It should not write “the network took 148 cycles” by summing incompatible producers.

---

## 12.12 What the test suite proves—and what it does not

The focused multicore source invokes sixteen named test functions and returns nonzero when a recorded failure exists. In the canonical static build it reports:

```text
=== Results: 16/16 passed, 0 failed ===
```

A fail-closed audit cannot stop at that positive result. The canonical runner changes the legacy expected transfer value from 15 to 14 in a disposable copy, recompiles, and requires the mutated test to return nonzero with 15/16. It also appends one byte to the disposable `tu_cluster.c`, requires the source hash audit to fail, restores the source, and requires the audit to pass again.

The replacement canonical-v5 evidence retains:

- 28 exact source, configuration, generator, SRAM, test, and report hashes;
- 155 structural and reachability predicates, 183 checks including hashes;
- static archive membership for `tu_core.o`, `tu_cluster.o`, and `config.o`;
- static-link gates for the probe, focused multicore test, config test, and linked sweeps;
- a clean detached Tusim checkout at the exact pin before and after;
- unchanged ignored-file inventory;
- zero book remotes;
- run-relative SHA-256 manifests; and
- pre-draft validation against the exact frozen input commit.

The custom probe also seals the adversarial disjoint-route observation `isolated=94 bottleneck=128 estimated=158 shared_pair_term=133`, preventing the disproved makespan-bound label from returning unnoticed.

A fresh run uses a new identifier so the sealed canonical directory is never overwritten:

```bash
CH12_RUN_ID="repro-$(date -u +%Y%m%dT%H%M%SZ)"
CH12_RUN_ID="$CH12_RUN_ID" experiments/run_ch12_multicore_interconnect_audit.sh
cd "experiments/runs/ch12-multicore-interconnect/$CH12_RUN_ID"
sha256sum -c sha256-retained.txt
```

The successful runner verdict is `CH12_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS`: snapshot conformance, not a green physical-correctness certificate.

The contention and routing sweeps call the cmodel traffic estimator. The topology, switching, and multicore-scaling sweeps duplicate standalone formulas. All may be useful, but they do not carry the same reachability weight.

### Historical document drift

The pinned multicore guide says cores never share mutable state, SPMD programs start simultaneously, and barriers synchronize. Public header comments additionally suggest stronger rendezvous, blocking, descriptor-latency-result, and bound contracts than the implementation supplies. The implementation and exact C-call audit do not support those claims. Source and executable evidence take precedence.

Likewise, historical sweep summaries report earlier focused-test denominators and a passing config suite. The chapter uses the exact current source inventory and observed canonical process results instead.

---

## 12.13 An architecture workflow for using the model safely

The following workflow turns Tusim's abstractions into an exploration tool without promoting them beyond their evidence.

### Step 1 — State the communication contract

Write down:

- source and destination cores;
- source and destination O-SRAM extents;
- payload size;
- whether the need is functional copy, broadcast, reduction, barrier, or traffic analysis;
- whether all messages are assumed simultaneous; and
- whether timing or only bytes matter.

Do not use all-reduce timing if the question requires a routed collective; that timing is absent.

### Step 2 — Establish the constructor path

Record the explicit core count, topology, and mesh rows passed to `tu_cluster_create()`. Then record the five ICC runtime fields. Do not infer construction from the full config's enable/count/topology request.

### Step 3 — Choose the fidelity rung

| Question | Minimum useful mode |
|---|---|
| Do endpoint bytes arrive? | functional send/broadcast/all-reduce probe |
| How does route length affect one transfer? | isolated switching estimator |
| Can simultaneous messages concentrate modeled service on one directed link? | shared-link route-load heuristic |
| Which packet waits, and for how long? | unsupported; add queue/arbitration model |
| Will RTL or silicon meet a target? | unsupported; calibrate against implementation evidence |

### Step 4 — Sweep alternatives, not just integers

Retain materially different hypotheses:

- ring and mesh;
- legacy, cut-through, and store-and-forward;
- ideal-parallel and shared-link;
- XY and YX;
- alternate placements, roots, and traffic matrices.

For each alternative, report performance regime, area/power expectation, accuracy effect, control complexity, and verification burden. A smaller heuristic score is not a complete architecture recommendation.

### Step 5 — Use discriminating traffic

At minimum include:

- one-hop traffic, where cut-through and store-and-forward coincide;
- multi-hop payloads, where switching differs;
- disjoint links versus shared links;
- neighbor, hotspot, and all-to-all patterns;
- an asymmetric mesh pattern and its 90-degree counterclockwise rotation; and
- a symmetric pattern where XY and YX should agree.

A test that cannot make alternatives disagree is a weak architecture test even if it passes.

### Step 6 — Report producer-qualified results

A compact report might say:

```text
topology=mesh 4x4
switching=cut_through
contention=shared_link
route=YX
payload=4096 B/message
injection=simultaneous
result=798 cycles
classification=deterministic shared-link heuristic estimate
bottleneck=1->5, 768 serialization cycles
omissions=queues, arbitration, VCs, backpressure, headers, wire timing
```

That statement is reproducible and difficult to misread.

### Step 7 — Know when to extend the model

Add a finite network model only when the decision depends on:

- queue depth;
- arbitration policy;
- burst timing;
- backpressure;
- head-of-line blocking;
- virtual-channel allocation;
- adaptive path selection; or
- deadlock/liveness behavior.

At that point, the implementation needs explicit injection timestamps, packet/flit structure, finite queues, per-cycle service, and invariants. It should be calibrated separately rather than silently changing the meaning of existing heuristic counters.

---

## 12.14 Fidelity box: what remains unknown

The pinned evidence does not establish:

- physical NoC area, energy, leakage, frequency, or wire delay;
- packet headers, flit size, router stages, queue depth, or buffer traffic;
- arbitration, fairness, backpressure, virtual channels, or head-of-line blocking;
- adaptive routing, deadlock freedom, or liveness;
- concurrent host-call safety for global state swaps;
- coherent end-to-end parallel execution time or speedup;
- routed multicast, all-reduce, or barrier algorithms;
- numerical reproducibility beyond the tested host-order FP32 sum;
- a universal ring/mesh, switching, contention, or route winner; or
- prediction error against RTL, FPGA, or silicon.

These are not minor disclaimers. They identify the next model boundaries. A queue-accurate interconnect chapter would need trace-driven injection, a service discipline, finite resources, and calibration. A collective chapter would need explicit algorithms and communication schedules. A physical chapter would need synthesis, layout, clock, and power evidence.

Tusim's current model remains valuable precisely because its boundary can be stated sharply. It supports byte-observable cluster experiments, deterministic topology and switching comparisons, and simultaneous directed-link heuristic scores. It can reject universal topology claims and expose placement hotspots before RTL. It cannot decide the router microarchitecture by itself.

---

## 12.15 Closing checklist

Before using a Tusim multicore/interconnect result in an architecture decision, ask:

1. **Which API produced the result?** Send, traffic estimator, broadcast, all-reduce, barrier, and SPMD have different contracts.
2. **What was functional?** Name the endpoint byte effect separately from timing.
3. **Which configuration reached the constructed cluster?** Separate full-config deployment requests from the five retained ICC fields.
4. **Which timing class applies?** Isolated estimate, shared-link heuristic score, additive counter, or absent.
5. **What traffic was assumed?** Payloads, endpoints, simultaneity, topology, and route order must be explicit.
6. **What alternatives were retained?** Ring/mesh, switching, contention, route, placement, and collective choices should remain visible.
7. **What costs are unquantified?** Area, power, accuracy, control, and verification trade-offs must be reported even when the model quantifies only cycles.
8. **What evidence is linked?** Distinguish cmodel-linked sweeps from standalone formulas and historical reports.
9. **What failed?** Preserve the non-passing config process and any known reachability gaps.
10. **What would change the decision?** Queue, arbitration, physical, or calibration evidence should have a named next experiment.

The correct answer to “ring or mesh?” is not a topology name. It is a regime-qualified argument:

> For this placement, traffic matrix, switching assumption, route policy, and heuristic-estimate fidelity, one alternative reduces the modeled score; its physical cost and queue behavior remain unquantified.

That is a useful pre-spec conclusion. It narrows the design space without pretending that a deterministic cmodel has already built the network.

---

## Summary

Chapter 12 established five separations that keep multicore exploration honest:

1. a `tu_core_t` is a stored state snapshot operated through process-global swaps, not proof of concurrent host-safe cores;
2. deployment requests and generated compile-time macros are distinct from runtime conversion and explicit cluster construction;
3. endpoint communication, isolated transfer equations, simultaneous traffic heuristics, additive counters, and calibration are different evidence classes;
4. the shared-link equation is a deterministic route-load score, not a proved makespan bound; and
5. broadcast, all-reduce, barrier, and SPMD are adjacent APIs at different evidence rungs, not one routed collective stack.

Within that boundary, Tusim can still answer useful architecture questions. There is no single integrated NoC model at this pin, but the adjacent surfaces can expose topology distance, route-order concentration, switching-equation sensitivity, and traffic-regime ranking reversals. They can show that a ring or mesh result depends on mapping and traffic rather than topology names alone. The correct output is a regime-qualified comparison with explicit omissions and a named next experiment.

## Review questions

1. Why does storing one `tu_state_t` per core not establish concurrent core execution?
2. Which multicore configuration fields reach runtime cluster state, and which remain deployment requests?
3. How do legacy, cut-through, and store-and-forward estimates differ?
4. Why is `total_icc_cycles` not a cluster makespan?
5. What property does `bottleneck_link_cycles` measure?
6. Why does the disjoint-route counterexample invalidate the lower-bound label for the combined score?
7. What does immediate point-to-point send model, and what does it omit?
8. Why are broadcast and all-reduce not evidence for a routed collective implementation?
9. What does the barrier add, and what synchronization state is absent?
10. What evidence would be required before using Tusim to predict physical NoC latency?

### Review-question answer key

1. Operations swap snapshots through process-global `g_tu`; no lock, host-thread launch, or simultaneous execution contract is established.
2. Switching, contention, route order, link width, and router latency cross runtime conversion and are retained. Enable, core count, and topology request do not; constructor arguments choose count and topology explicitly.
3. Legacy charges only hop latency, cut-through adds one payload serialization term, and store-and-forward charges serialization plus router latency at every hop.
4. It sums successful per-send estimates. It has neither overlapping intervals nor an elapsed cluster timeline.
5. It sums serialization service assigned to the busiest modeled directed link for one hypothetical simultaneous message set.
6. The implementation can add a bottleneck maximum and route maximum from disjoint flows that can overlap, producing a score above a feasible schedule.
7. It models an immediate host-mediated O-SRAM byte copy, statistics updates, and a destination estimate. It omits packets, injection, queues, arbitration, and backpressure.
8. Broadcast repeats send sequentially; all-reduce performs host-order FP32 reads, summation, and writes while adding no routed-cycle estimate.
9. For `router_latency <= UINT32_MAX / 2`, it adds the mathematical `2 * router_latency` product to every core and increments `stats.total_barriers`; larger direct runtime values wrap in 32-bit arithmetic before widening. It records no arrivals, waiting, or release condition.
10. At minimum: explicit injection traces, packet/flit structure, finite queues, arbitration and flow control, per-cycle service, clock-domain assumptions, and comparison against RTL/FPGA/silicon under fixed mappings.

## Design exercises

1. **Traffic-regime matrix.** Define neighbor, all-to-all, and hotspot traffic for 8 and 16 cores. Compare ring and mesh heuristic scores, then list the area, wiring, power, and verification costs the score omits.
2. **Counterexample family.** Generalize the 4×4 disjoint-route case. Construct message sets where the busiest-link service and longest route arise from different connected components, and characterize the gap between the heuristic and a feasible overlap schedule.
3. **Configuration integration.** Design a deployment adapter that turns enable/count/topology requests into explicit cluster construction while preserving the five ICC runtime fields. Specify validation and failure-atomicity rules.
4. **Transactional broadcast.** Propose a broadcast API with preflight span validation and all-or-nothing endpoint effects. Compare temporary-storage, rollback, and verification costs.
5. **Routed all-reduce.** Replace the host helper conceptually with ring and tree schedules. State message counts, bytes, dependency steps, and the network assumptions needed to estimate time.
6. **Barrier state machine.** Define arrival, generation, release, and timeout state for a reusable barrier. Explain how topology affects only an explicit communication schedule, not rendezvous semantics by itself.
7. **Queue-model escalation.** Add injection timestamps, finite per-link queues, and round-robin arbitration to the route-load model. Identify which old counters must be renamed rather than silently reinterpreted.
8. **Calibration plan.** Choose one RTL or FPGA interconnect. Define identical payloads, routes, injection traces, clocks, and measured intervals, then specify error metrics and acceptance thresholds.

## Primary references

- Dally and Towles, “Route Packets, Not Wires: On-Chip Interconnection Networks” [DT01](../../references/foundations.md#dt01-on-chip-interconnection-networks).
- Dally and Seitz, “Deadlock-Free Message Routing in Multiprocessor Interconnection Networks” [DS87](../../references/foundations.md#ds87-deadlock-free-routing).
- Patarasuk and Yuan, bandwidth-optimal all-reduce algorithms [PY09](../../references/foundations.md#py09-bandwidth-optimal-all-reduce).
