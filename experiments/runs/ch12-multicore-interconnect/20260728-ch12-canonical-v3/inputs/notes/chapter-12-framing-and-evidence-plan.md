# Chapter 12 Framing and Evidence Plan — Multi-Core Clusters and Interconnect Heuristic Estimates

- **Edition:** Tusim `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Book workspace:** `/home/zxy/Workplace/books/tusim-book`
- **Source workspace:** `/home/zxy/Workplace/projects/tusim` (detached, clean, read-only)
- **Status:** scope selected from fresh whole-tree reconnaissance; drafting blocked pending claim audit, canonical execution, skeptical review, and gate closure

## Fresh reconnaissance basis

The selection started from the complete current book status, not Chapter 11's deferred list. The audit compared uncovered pinned surfaces after Chapters 1–11 using six questions:

1. What reader decision would the chapter enable?
2. Can the boundary teach adjacent cluster mechanisms without implying one integrated execution/timing domain?
3. Which declarations reach a library, test, public/runtime path, and discriminating effect?
4. Which configuration fields propagate to the selected consumer?
5. Can the principal claims be tested safely in a disposable archive?
6. Would combining adjacent modules blur functional effects, counter intervals, or calibration scope?

## Ranked candidate boundaries

| Rank | Candidate | Reader decision and evidence | Principal risk | Disposition |
|---:|---|---|---|---|
| 1 | **Multi-Core Clusters and Interconnect Heuristic Estimates** | decide whether a placement/traffic pattern is functionally represented and which topology/switching/contention/routing estimate is safe; linked core/cluster code, 16-case focused test, config propagation, and discriminating traffic probes share one cluster boundary | easy to mistake immediate host copies and heuristic-estimate equations for a concurrent NoC | **selected** |
| 2 | Performance Counters and Metric Provenance | decide which named counter, interval, and producer can support a metric; rich linked/tested counter API exposes disconnected producers and mixed clocks | would require reopening several compute, DMA, memory, and power domains at once; one chapter could encourage invalid aggregation | defer until after remaining producer chapters |
| 3 | DRAM Interfaces and Timing Abstractions | choose between the linked hierarchy DRAM model and source-present cycle-model DRAM channel; both have clear tests and conflicting semantics | Chapter 9 already established the three-memory-surface boundary; a full chapter needs a separate calibration/source study | defer |
| 4 | Operator Engines and Heterogeneous Return Metrics | select convolution, pooling, normalization, softmax, or attention API and interpret its return/statistics contract | too many numerical kernels and incompatible return meanings for one coherent evidence domain | split into later operator-family chapters |
| 5 | Multi-Context Save/Restore and Preemption Estimates | choose retention scope and scheduling policy; linked focused tests and a retained-state byte model are available | narrower systems topic and less foundational than cluster topology/traffic before multicore exploration | defer |
| 6 | Liveness Allocation and Spill/Fill IR | choose compiler-side allocation capacity and understand inserted analysis-IR operations | adjacent to Chapter 11 but not runtime-integrated; selecting it now would over-weight narrative momentum | defer; not rejected |

### Independent scope-panel disposition

Three independent exact-pin reviews did not converge by narrative momentum. One selected interconnect, one selected FP32 elementwise/softmax/normalization engines, and one selected the standalone DRAM service model. The dissent is material:

- the operator candidate has strong numerical executability but mixes host computation with SRAM-stall return values and lacks one canonical configuration path;
- the DRAM candidate has one clean local clock but overlaps Chapter 9 and remains disconnected from ordinary descriptor DMA and direct MMA;
- the interconnect candidate must separate cluster ownership from topology analysis, yet uniquely combines byte-observable public effects, five configuration fields with exact runtime consumers, linked traffic-matrix heuristic estimates, and route/contention probes.

Interconnect therefore remains selected. The disagreement is retained as evidence that Chapter 12 was chosen from whole-book gaps rather than Chapter 11's deferred list. Vector/reduction engines and DRAM remain leading later work units, not rejected architecture options.

The selected boundary is evidence-derived because it is the strongest substantial uncovered surface with: explicit runtime consumers for five ICC fields, byte-observable functional operations, linked topology/traffic equations, fail-closed focused tests, and historical reports that can be challenged rather than copied.

## Reader decision

> Given core-local state, a point-to-point or collective communication need, and a traffic matrix, which pinned Tusim API produces a functional byte effect, which fields configure the cluster actually created, which quantity is an isolated estimate, a shared-link heuristic estimate, a per-destination additive counter, or no timing result at all, and what must remain unknown without queues, arbitration, backpressure, calibrated links, and concurrent execution?

The reader must be able to reject these substitutions:

1. several `tu_core_t` allocations do not prove thread-safe or physically concurrent cores;
2. an immediate byte copy with an attached estimate is not packet transport;
3. a simultaneous traffic-matrix heuristic estimate is not a finite-router schedule;
4. a functional collective is not automatically routed or timed;
5. parsed `enabled`, `num_cores`, and `interconnect` declarations do not automatically instantiate a cluster.

## In scope

1. `tu_core_t` as a stored `tu_state_t` snapshot operated through global-state swap-in/swap-out wrappers exercised sequentially.
2. Cluster construction, ring/mesh/none topology, mesh shape, neighbor and hop-distance functions.
3. Point-to-point O-SRAM send semantics, bounds, immediate copy, stats, and destination-core estimated-cycle update.
4. The exact isolated equations for legacy hop-only, cut-through, and store-and-forward modes.
5. Simultaneous traffic-matrix accounting for ideal-parallel and shared-directed-link modes, including ring tie-breaking and deterministic XY/YX mesh routes.
6. Functional broadcast and FP32 all-reduce, plus barrier and SPMD implementation boundaries, with explicit separation from routed/concurrent implementations and explicit absence of an SPMD API caller/test.
7. Field-level configuration ladder for multicore declarations and the five ICC fields retained in `tu_runtime_config_t` and consumed by `tu_cluster_create()`.
8. Focused and aggregate inclusion, linked versus standalone sweeps, historical-report conflicts, static-link evidence, and calibrated-status limits.

## Explicitly deferred

- Finite injection queues, packet/flit format, headers, credits, virtual channels, arbitration, backpressure, head-of-line blocking, deadlock/livelock, adaptive routing, and coherence.
- Physical wire length, router/link area, frequency closure, dynamic/leakage energy, thermal behavior, and calibrated NoC throughput or latency.
- General thread safety or parallel host execution of `tu_core_t` operations.
- Repair of global state, DMA singleton, dataflow registry, or pointer-lifetime design.
- A complete collective library, reduction trees, reduce-scatter/allgather implementation, numerical reproducibility across reduction orders, or network-timed collectives.
- New multicore GEMM scaling predictions from historical analytical scripts.
- Performance-counter unification, context switching, DRAM calibration, liveness allocation, and advanced operator engines.

## Source map

| Surface | Authoritative pinned files | Safe question |
|---|---|---|
| core facade | `tu_cmodel/tu_core.[ch]`, `tu_cmodel/tu_cmodel.[ch]` | what state is copied, swapped, and executed through global paths? |
| cluster and ICC | `tu_cmodel/tu_cluster.[ch]` | what bytes move, which estimate is returned or accumulated, and which fields are ignored? |
| compile/runtime config | `tu_cmodel/tu_config.h`, `tu_cmodel/infra/config.[ch]`, shipped JSON/YAML | which declarations parse, validate, convert, retain, and reach cluster construction? |
| focused verification | `tests/test_multicore.c`, `tests/test_config.c` | which multicore assertions gate nonzero, which SPMD-named test bypasses the SPMD API, and which ICC config case prints PASS before the config process later aborts? |
| linked traffic sweeps | `tests/test_interconnect_contention_sweep.c`, `tests/test_interconnect_routing_sweep.c` | how do traffic shape and route order affect the implemented heuristic estimate? |
| standalone analytical sweeps | `tests/test_interconnect_topology_sweep.c`, `tests/test_interconnect_switching_sweep.c`, `tests/test_multicore_scaling_sweep.c` | which formulas are independent reports rather than cluster execution? |
| historical/current docs | `docs/multicore-cluster.md`, `docs/exploration/interconnect-*.md`, `docs/exploration/multicore-scaling-gemm256.md` | rationale, prior claims, corrections, and known drift only |
| external foundations | [DT01](../references/foundations.md#dt01-on-chip-interconnection-networks), [DS87](../references/foundations.md#ds87-deadlock-free-routing), [PY09](../references/foundations.md#py09-bandwidth-optimal-all-reduce) | vocabulary and design obligations, never validation of Tusim |

## Evidence ladders

### Core/cluster reachability

```text
source present -> TU_OBJS member -> static archive member -> focused-tested
-> public C API reachable -> operation effect observed -> aggregate target included
```

### Configuration effect

```text
declared -> parsed -> validated -> converted -> retained by cluster
-> consumed by estimator -> discriminating effect -> focused-tested -> calibrated
```

The five timing/routing fields are expected to reach runtime retention and separately identified direct consumers. Canonical-v2 did not seal one parse→convert→construct one-field-at-a-time A/B chain, so retention and direct effect remain separate claims. `multicore_enabled`, `num_cores`, and `interconnect_mode` stop before runtime conversion and cluster instantiation, although the YAML generator emits compile-time macros for them. No selected field reaches external calibration.

### Communication semantics

```text
descriptor field -> checked -> consumed -> byte effect -> timing estimate
-> traffic interaction -> queued execution -> calibrated behavior
```

Fields such as `tag`, `blocking`, and descriptor `latency_cycles` must not be promoted beyond declaration without a consumer.

## Initial executable evidence plan

Canonical runner: `experiments/run_ch12_multicore_interconnect_audit.sh`

Canonical run target: `experiments/runs/ch12-multicore-interconnect/20260728-ch12-canonical-v3/`

### Fail-closed gates

1. Require exact Tusim pin, detached/clean tracked state, unchanged ignored inventory, clean book input commit, zero book remotes, and no run-ID collision.
2. Extract the exact pin with `git archive`; never build or write in the Tusim checkout and never invoke its globally scoped `clean` recipe.
3. Hash every inspected source, config, test, build, report, plan, ledger, review, validator, runner, probe, and reference input.
4. Require `tu_core.o`, `tu_cluster.o`, and configuration/core dependencies in the static archive.
5. Compile the custom probe, focused multicore test, config test, and linked traffic sweeps explicitly against `libtucmodel.a`; reject unexpected `libtucmodel.so` resolution.
6. Preserve exact focused denominators, compact probe output, sweep output, archive member list, source archive digest, complete transcript, and run-relative manifest.
7. Use only bounded, in-range communication probes. Treat integer-overflow bounds concerns and thread-safety claims statically; do not execute undefined behavior or concurrent global swaps.
8. Mutation-test source-hash acceptance and one focused exact-equation assertion; structurally validate that unsafe overflow and concurrent-global-swap probes remain absent.

### Discriminating probes

- Requested runtime switching/link/router/routing/contention values retained in a real cluster; direct consumer equations are discriminated separately.
- Legacy, cut-through, and store-forward point-to-point equations at identical hops/payload.
- Byte-identical send with `blocking=false`, unchanged caller descriptor, destination-only cycle delta, and exact stats.
- Same-link versus disjoint-link traffic; ideal-parallel versus shared-link heuristic scores; disjoint-long-route counterexample to the bound label.
- XY/YX reversal under transposed asymmetric traffic and equality for symmetric all-to-all.
- Bounded, in-range broadcast byte effects, sum-of-sequential-send stats, and the non-transactional failure boundary.
- Bounded, in-range all-reduce byte correctness with zero routed-cycle increment and explicit overflow/span exclusions.
- Barrier's fixed `2 * hop_latency` increment in one ring probe, with topology independence established statically.
- Configuration parse/conversion split: five ICC timing/routing fields propagate to retained state and separately probed consumers; cluster-enable/count/topology do not reach runtime conversion.

## Skeptical-review gates

### Architecture/methodology

- Are stored core snapshots distinguished from independently running cores?
- Does every cycle number name its producer, interval, and aggregation rule?
- Are isolated transfer, traffic heuristic estimate, destination-core accumulation, and elapsed time kept distinct?
- Are functional collectives prevented from inheriting point-to-point timing?
- Are historical topology recommendations challenged by current linked traffic evidence?

### Repository/reachability

- Do exact call inventories show which APIs consume config and which bypass the route model?
- Does every focused binary use the archived static library?
- Are standalone sweeps labeled analytical and excluded from runtime-integration evidence?
- Does the source audit fail on changed hashes, predicates, caller sets, and expected formulas?

### Editorial/evidence

- Is “heuristic estimate” repeated wherever shared-link results appear?
- Are topology/route alternatives evaluated by traffic regime and implementation cost rather than ranked universally?
- Are byte-exact effects separated from timing and calibration?
- Are `blocking`, `tag`, `latency_cycles`, barrier, and SPMD names prevented from implying absent behavior?

Drafting remains blocked until the framing and ledger are reviewed, the execution inputs are committed, a canonical run is sealed in a second commit, skeptical findings are dispositioned, and the pre-draft validator passes.
