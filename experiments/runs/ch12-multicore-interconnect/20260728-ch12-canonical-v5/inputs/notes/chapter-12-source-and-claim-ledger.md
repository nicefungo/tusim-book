# Chapter 12 Source and Claim Ledger — Multi-Core Clusters and Interconnect Heuristic Estimates

- **Pinned source:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Canonical run:** `experiments/runs/ch12-multicore-interconnect/20260728-ch12-canonical-v5/`
- **Status vocabulary:** `verified`, `qualified`, `rejected`, `blocked`
- **Draft gate:** reopened after independent manuscript/reproducibility review; canonical-v5 pending

## Claim ledger

| ID | Claim | Evidence required | Status | Required wording / limitation |
|---|---|---|---|---|
| C12.1 | `tu_core_t` stores one `tu_state_t`, identity, lifecycle flag, and ICC-buffer fields. | core header hash/source audit | verified | stored state object, not a hardware core |
| C12.2 | Core operation wrappers swap the selected state through process-global `g_tu`, execute a legacy direct API, and copy state back. | `tu_core.c`; call inventory | verified | global-state-swapping facade exercised sequentially; no lock, thread-safety, or simultaneous execution claim |
| C12.3 | Core creation calls global initialization, copies `g_tu`, then clears `g_tu`; cluster creation repeats this for every core. | core/cluster source | verified | explicit lifecycle interaction; avoid “all mutable state is core-local” |
| C12.4 | The focused test observes distinct W-SRAM backing pointers and retained different W values across two core snapshots. | focused multicore test | verified | source allocation suggests separate A/O storage, but this is not a complete W/A/O or singleton-isolation proof |
| C12.5 | Cluster construction accepts 1–256 cores and explicit NONE/RING/MESH topology; a mesh requires nonzero rows and derives columns with `(num_cores + mesh_rows - 1) / mesh_rows`. | cluster source/probe | qualified | callers must prevent numerator wrap; use `mesh_rows <= UINT32_MAX - (num_cores - 1)`; unsafe zero-column downstream behavior was not executed |
| C12.6 | Ring distance is shortest bidirectional distance; mesh distance is Manhattan distance over the derived rectangular layout; NONE is unreachable between different cores. | source; 16-case focused test | verified | graph-distance function, not routed latency by itself |
| C12.7 | Legacy transfer estimate is `hops * router_latency`; cut-through adds one `ceil(bytes/link_width)` term; store-forward charges router plus serialization at every hop. | source audit; exact probe | verified | deterministic estimated cycles, no queues or calibration |
| C12.8 | Zero-byte and same-core estimates return zero; invalid/unreachable routes return `UINT64_MAX`. | source; focused/probe | verified | API sentinel, not a completed message event |
| C12.9 | Point-to-point send copies bytes immediately from source O-SRAM to destination O-SRAM through a host temporary buffer. | source; byte probe | verified | functional copy, not packet/flit traversal |
| C12.10 | Send checks core IDs and in-range end offsets using 32-bit addition. Potential addition overflow is not safely executed. | static source audit | qualified | trusted caller must prevent wraparound; do not claim hardened bounds |
| C12.11 | `tag`, `blocking`, and descriptor `latency_cycles` are declared but not consumed by `tu_cluster_send`; the caller descriptor is `const` and remains unchanged. | exact caller/source audit; false-blocking probe | verified | no async/nonblocking or descriptor-result contract |
| C12.12 | Successful send increments cluster message/byte/cycle sums and adds the isolated estimate only to the destination core's `estimated_cycles`. | source; before/after probe | verified | additive accounting is not cluster elapsed time or source occupancy |
| C12.13 | `total_icc_cycles` is a sum over sends; broadcast loops over destinations and uses sequential immediate sends. | source; broadcast probe | verified | do not interpret as a parallel broadcast makespan |
| C12.14 | The traffic estimator interprets all input messages as simultaneous, computes maximum isolated latency, and in shared mode combines bottleneck-link service with a global maximum route term. | source; linked sweep/probe | verified | deterministic heuristic score, not a queue schedule or proved makespan bound |
| C12.15 | Ring routes use shortest paths and choose clockwise on equal-distance ties. Mesh routes use selected deterministic XY or YX minimal dimension order. | source audit; route probe | verified | no adaptive routing or alternative tie policy |
| C12.16 | Ideal-parallel returns the maximum isolated message estimate; shared-link returns `max(isolated, bottleneck serialization + maximum route latency)`. | source; exact probe | verified | the two maxima may come from disjoint flows; the sum is a heuristic score, not a proved bound |
| C12.17 | Two same-link 1 KiB cut-through messages at 16 B/cycle and 5 cycles/router produce 133 cycles; disjoint links and ideal-parallel produce 69. | focused test/canonical probe | verified | exact pinned snapshot |
| C12.18 | On the selected asymmetric 4x4 traffic, XY and YX produce different bottlenecks and exact heuristic estimates; the transposed pattern reverses the winner. | route sweep/custom probe | verified | traffic-specific, not universal route recommendation |
| C12.19 | For bounded, in-range inputs and successful calls, broadcast copies source bytes to every other core through N-1 sequential sends. | source; focused/probe | qualified | no multicast tree; non-transactional partial effects can precede a later failure |
| C12.20 | For bounded, in-range inputs and successful calls, FP32 all-reduce reads every core on the host, sums in core-index order, and writes the result to every core. | source; focused/probe | qualified | host reduction; no routed collective algorithm; caller validates spans and arithmetic |
| C12.21 | On the bounded successful probe, all-reduce increments only N-1 message and gather-byte counts and adds no ICC cycles or per-core estimated cycles. | source; counter-delta probe | verified | reported traffic is incomplete for gather+broadcast |
| C12.22 | Barrier increments `stats.total_barriers` and adds exactly `2 * hop_latency` to every core without recording arrival or waiting state; the separately declared `barrier_counter` is not updated. | source; one-ring counter probe | verified | topology independence is source-established, not a cross-topology executable probe |
| C12.23 | SPMD execution is implementation-only in the audited exact C-call inventory; its implementation loops over cores sequentially and calls the text interpreter without host threads or a common start event. | source and exact caller audit | verified | “SPMD API loop,” not concurrent launch; no executable API probe at this pin |
| C12.24 | The focused multicore source invokes 16 named test functions and exits nonzero on recorded failure. Its SPMD-named case directly calls per-core MMA and does not call `tu_cluster_spmd_execute()`. | test source; forced-failure mutation in disposable archive; canonical run | verified | 16/16 is a regression snapshot for covered assertions, not SPMD API coverage or multicore certification |
| C12.25 | `tu_core.o` and `tu_cluster.o` are static-library members and `test-multicore` is in aggregate `make test` but not `test-quick`. | Makefile/archive audit | verified | aggregate inclusion is not external calibration |
| C12.26 | Linked contention/routing sweeps call `tu_cluster_estimate_traffic_cycles`; topology and switching sweeps duplicate standalone formulas without linking the cluster model. | Makefile/caller inventory | verified | classify every table by its producer |
| C12.27 | Full config declares/parses/validates `multicore_enabled`, `num_cores`, and `interconnect_mode`, but `tu_config_to_runtime()` drops them. | config source/hash audit | verified | parsing does not instantiate a cluster or select topology |
| C12.28 | Full config parses and converts switching, contention, mesh routing, link bytes/cycle, and router latency; cluster creation retains those runtime fields, whose direct consumers are separately probed. | config/cluster source; retention probe; direct effect probes | qualified | no single parse→convert→construct one-field A/B path is sealed through canonical-v5 |
| C12.29 | Full config validation rejects named unsupported modes and zero link width, but `tu_cluster_create()` itself does not revalidate every direct runtime field. | source audit/probe with safe invalid estimator | verified | full-config validity is not guaranteed for hand-built runtime structs |
| C12.30 | Shipped JSON requests multicore disabled/one core/none and legacy/ideal/XY/16 B per cycle/5 cycles per router. YAML agrees for these fields. | pinned config hashes | verified | declarations only until an explicit cluster is constructed |
| C12.31 | Historical topology/all-reduce and multicore-scaling scripts are analytical reports with formulas that are not the functional collective or current traffic estimator. | scripts/docs audit | qualified | retain architecture questions; do not import speedup recommendations |
| C12.32 | Current linked traffic evidence can reverse ring/mesh or XY/YX ranking by traffic shape. | canonical linked sweeps | verified | no universal topology winner; report exact workload and assumptions |
| C12.33 | `icc_bandwidth_gbps` is a declared cluster-stat field without an update assignment in the audited source; printed bandwidth is recomputed from byte/cycle sums under an implicit 1 GHz conversion. | source audit | verified | printed value is an uncalibrated derived bytes/cycle quantity, not measured GB/s |
| C12.34 | Cluster timing, traffic, barrier, and core `estimated_cycles` values are not externally calibrated against RTL, FPGA, or silicon in the audited evidence. | source/audit/status review | verified | label estimated or deterministic heuristic estimate |
| C12.35 | Finite router queues, arbitration, backpressure, virtual channels, head-of-line blocking, deadlock behavior, adaptive routing, physical area/power, and coherent end-to-end parallel timing are established. | absent model/calibration | rejected | explicitly outside supported claims |
| C12.36 | Functional byte equality validates timing, concurrency, routing, or collective transport. | evidence ladder | rejected | numerical/byte effect and timing require separate evidence |
| C12.37 | The exact-pin config test reaches and prints PASS for its ICC parse/validation case, then aborts during a later TU-init/MMA case under the canonical compiler/runtime; the process is not a passing configuration-suite gate. | bounded development and canonical config-test log | qualified | use the custom config-consumer probe for selected-field effects; preserve the later failure without attributing its root cause in this chapter |
| C12.38 | `tu_cluster_create()` validates core count and nonzero mesh rows but does not reject an out-of-range topology enum; topology helpers later classify it as unreachable/default. | source audit | qualified | callers must pass NONE, RING, or MESH; do not claim constructor-wide enum validation |
| C12.39 | All-reduce forms `num_elements * sizeof(float)` and accesses every source/destination offset without explicit region bounds or overflow checks in the collective function. | static source audit | qualified | canonical probe uses small in-range extents; trusted callers must validate spans before entry |
| C12.40 | `barrier_counter` remains zero across a barrier while `stats.total_barriers` increments. | source and canonical counter probe | verified | distinguish the unused lifecycle field from the statistics count |
| C12.41 | The current multicore guide's claims that cores never share mutable state, SPMD programs start simultaneously, and barriers synchronize are stronger than the pinned implementation supports. | guide-versus-source/caller audit | rejected | describe a global-state-swapping facade exercised sequentially, implementation-only serial SPMD loop, and no-wait barrier estimate |
| C12.42 | The standalone topology report's implication that mesh hop reduction improves cluster barrier overhead is not reachable through `tu_cluster_barrier()`, whose estimate is topology-independent. | report/source conflict audit | rejected | retain the report only as historical formula orientation; do not transfer its topology conclusion to barrier execution |
| C12.43 | The combined shared-link equation can exceed a feasible schedule when bottleneck service and maximum route latency come from disjoint flows. | source; adversarial 4×4 XY counterexample; canonical-v5 | verified | exact observation `isolated=94 bottleneck=128 estimated=158`; not a makespan bound |
| C12.44 | A directed-link service accumulator cannot overflow `uint64_t` from the declared 32-bit message count and per-message size widths alone, but the final `bottleneck_link_cycles + max_route_cycles` addition is unchecked. | static type/arithmetic source audit | qualified | trusted callers bound the final sum; do not execute unsafe overflow cases |
| C12.45 | Header comments promise rendezvous, concurrent SPMD, and message-field behavior not supplied by the implementation. | exact header-versus-source audit | rejected | public prose is a contradiction finding, not confirming evidence |
| C12.46 | The config generator consumes YAML multicore/ICC fields into compile-time header definitions, but generated enable/count/topology macros do not instantiate a runtime cluster. | generator hash/source audit; canonical-v5 | qualified | generated declarations are distinct from runtime cluster construction |
| C12.47 | The canonical bundle has an inner retained-file manifest plus an outer Git-pinned bundle manifest covering the inner manifest, finalization record, and retained pre-draft validation result. | runner; manifests; fresh-clone validation | blocked | canonical-v5 must seal and verify the outer manifest; it is authenticated by the later local evidence-seal commit, not by self-hashing |

## Counter and interval vocabulary

| Quantity | Producer and interval | Safe interpretation |
|---|---|---|
| `tu_cluster_estimate_transfer_cycles` | one hypothetical point-to-point message | deterministic isolated estimate for named topology/switch mode |
| `isolated_cycles` | maximum isolated estimate across one simultaneous message array | ideal-parallel maximum; an independent necessary term under the abstract assumptions |
| `bottleneck_link_cycles` | sum of serialization service on busiest directed route edge | link-load term, not elapsed link trace |
| `estimated_cycles` in traffic stats | max of isolated and bottleneck service plus global max route term | deterministic traffic-matrix heuristic score; not a proved makespan bound |
| cluster `total_icc_cycles` | sum of successful point-to-point send estimates since creation | additive work-like counter, not makespan |
| destination core `estimated_cycles` delta | point-to-point send estimate added to destination only | local accumulated estimate, not source or fabric occupancy |
| barrier delta | fixed `2 * hop_latency` added to every core per call | synchronization estimate with no arrival model |
| all-reduce cycle delta | none at the pin | absence of timing accounting, not zero-cost hardware |

## Configuration/reachability matrix

| Field family | Declared/parsed | Converted to runtime | Retained/consumed by cluster | Discriminating effect | Calibration |
|---|---:|---:|---:|---:|---:|
| enabled / core count / topology | yes | no | explicit API arguments instead | no automatic effect | no |
| switching mode | yes | yes | yes | isolated equation | no |
| link bytes/cycle | yes | yes | yes | serialization ceiling | no |
| router latency | yes | yes | yes | per-hop term and barrier | no |
| contention mode | yes | yes | yes | traffic-matrix heuristic equation | no |
| mesh route order | yes | yes | yes | directed-link occupancy | no |
| message tag / blocking / latency result field | declaration only | n/a | not consumed by send | none | no |

## Evidence labels

- **Executable:** core/cluster lifecycle, byte copies, FP32 host reduction, topology helpers, estimates, and focused tests at the pin.
- **Integrated:** public C cluster methods consume explicit runtime config for five ICC timing/routing fields; full-config enable/count/topology do not auto-create a cluster.
- **Functional model:** immediate O-SRAM point-to-point/broadcast copies and host all-reduce semantics.
- **Analytical model / deterministic heuristic estimate:** isolated switching equations, shared-link traffic estimate, barrier constant, and historical sweeps.
- **Estimated:** additive cluster/core cycle fields.
- **Calibrated:** none for the selected multicore/interconnect behavior.

## Current disposition

The selected chapter is not a claim that Tusim has a concurrent NoC simulator. It teaches a decision ladder:

```text
core state stored -> API called -> bytes changed -> isolated estimate attached
-> simultaneous traffic heuristic estimate -> queued/arbitrated network -> calibrated behavior
```

Tusim reaches different rungs for point-to-point send, traffic analysis, broadcast, all-reduce, barrier, and SPMD. Closure is reopened pending canonical-v5; the initial canonical run, v2, v3, and failed v4 are retained as superseded historical evidence.
