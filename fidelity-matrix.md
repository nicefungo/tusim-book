# Tusim Fidelity Matrix

## How to use this matrix

A model is useful only when its abstraction matches the question. “More detailed” is not automatically “more correct,” and a correct functional result does not validate a timing prediction. This matrix defines the safe scope of the first textbook edition.

| Domain | What Tusim can support | Principal omissions/risks | Safe conclusion | Unsafe conclusion |
|---|---|---|---|---|
| MMA functional semantics | tiled W×A accumulation, edge dimensions, FP accumulator behavior, audited WS/OS/RS normal-value equivalence | MMA-local FP16 subnormals are defective; not RTL signal timing | result/layout and arithmetic behavior for the tested value domain and modes | arbitrary binary16 correctness or bit/cycle equivalence to unspecified RTL |
| PE-array timing | fill/compute/drain estimates parameterized by geometry and dataflow | arbitration, detailed pipeline hazards, physical clock closure | relative trends within the same formula and assumptions | tape-out frequency or exact silicon latency |
| SRAM | W/A/O allocated byte capacity; executable aligned generic-bank mapping and budget/refill; standalone hierarchy access; separate source-present cycle-bank model | direct MMA uses raw pointers; failure-open bounds; parsed banking dropped; hierarchy/cycle bank models are disconnected and incompatible; unsafe custom GBuf geometry/tails; utilization interval defect; no queues or physical calibration | exact allocations and deterministic behavior for a named API, aligned sequence, and explicit clock/reset domain | enforced direct-MMA capacity, direct-MMA bank traffic, cross-model conflict equivalence, queued latency, physical utilization, or SRAM area/energy |
| DMA | in-bounds linear/strided/scatter-gather/multicast functional semantics; synchronous and explicit-tick channel state; legacy W/A-load and O-store wrappers; source-defined service estimates | chain and queue share `next`; completion counters are outcome-blind; borrowed lifetimes and reclamation vary by path; reinit is destructive; active config drops parsed DMA fields; fixed three-entry channel storage; descriptor path does not call the DRAM model; cycle/accounting state is split | named descriptor bytes, lifecycle states, and uncalibrated service estimates within the independent one-node safe subset and explicit counter domain | coherent dependency readiness, safe general chaining, physical concurrency/throughput, calibrated DMA latency, or coherent end-to-end DMA+MMA time |
| DRAM | configured bandwidth/latency/preset effects | controller scheduling and full DRAM timing fidelity depend on mode | sensitivity to explicit bandwidth/latency assumptions | exact DDR/HBM performance without validation |
| Dataflow | compiled WS/OS/RS functional plug-ins, direct global selection, and distinct deterministic cycle formulas | identical scalar movement behavior; no dataflow-specific traffic/storage model; config/core selection gaps; uncalibrated timing | direct-path functional equivalence and exact source-formula behavior at the pinned revision | physical reuse/bandwidth benefit, coherent end-to-end latency, or universally optimal dataflow |
| Numerics | canonical FP16 widening, BF16/FP8/TF32 conversion APIs, rounding setters, registry, and FP16-input/FP32-accumulate direct MMA | full FP16 narrowing and local subnormal defects; E4M3/FP8-tie and signaling-NaN disagreements; precision config dropped; host arithmetic semantics; no generic multi-precision MMA | exact behavior for the named path, raw encodings, mode, host toolchain, and tested boundary | one unified IEEE/OCP policy, registry-driven engine support, or application accuracy from conversion/kernel tests |
| Compute engines | functional operator models and engine-specific metrics | integration and timing domain differ by engine | tested operator semantics and explicitly named returned metric | summing heterogeneous return values into total latency |
| Double buffering/pipeline | standalone double-buffer state and bounded pipeline-controller mechanics | canonical bounded DMA-to-shadow sequence exposes stale active data after swap; unmodified pipeline suite is unsafe at four channels; no validated dependency/overlap path | standalone state transitions and explicitly named bounded observations | valid compute/DMA overlap, overlap speedup, replacement coverage for the skipped suite, or guaranteed hardware overlap efficiency |
| Compiler/ISA/queue | expanded-ISA metadata/native object layout; executable legacy ASM subset; executable eight-class queue dispatcher; scheduler/liveness models; demonstration ONNX lowering | no portable binary stream or integrated compiler→scheduler→queue path; missing IDs fail open; faults can strand dependents; completion does not imply effect/signaling/reclamation; barrier is not a full fence; command IDs alias across reset; scheduler edges truncate at 16 | named surface behavior, exact queue lifecycle observations, and fixed scheduler estimates at the pinned revision | arbitrary ONNX support, full opcode execution, portable encoding, generation-safe handles, conventional event/fence/retirement semantics, physical overlap, or calibrated timing |
| Multi-core/interconnect | sequentially exercised core snapshots; immediate O-SRAM send/broadcast copies; host FP32 all-reduce; topology, isolated-transfer, route-load, and fixed-barrier estimates | process-global swaps; no concurrent safety; adjacent APIs do not form one transport; unchecked arithmetic/spans; no queues, arbitration, injection timing, adaptive routing, or physical NoC calibration | bounded functional effects and exact deterministic equation/heuristic comparisons for named APIs, topology, traffic matrix, and interval | one integrated NoC, proved traffic makespan bound, concurrent execution, exact latency, routed collective timing, rendezvous, or universal mesh/ring preference |
| Context switch | retained-state byte model and save/restore semantics | reload traffic and dirty/live-range realism depend on traces | cost sensitivity to retention scope and state bandwidth | complete preemption cost for arbitrary workloads |
| Performance counters | explicit counters and derived metrics where wired | mixed plug-in intervals; standalone producer hard-codes WS, lacks RS storage, and diff/merge omit dataflow buckets; no unified timeline | values from the named counter source, field, interval, and scope | combining all counters as one coherent cycle ledger or trusting dataflow labels without producer audit |
| Power/energy | configured/table-based estimates and relative decomposition | technology, voltage, activity, physical layout calibration | comparative sensitivity under fixed assumptions | sign-off power or energy per inference |
| Exploration reports | reproducible sweeps and regime discovery | formula/model bias, limited workloads, stale docs | conditional hypotheses and design questions | proof that one architecture is best |

## Validation ladder

The book uses the following ladder, from weakest to strongest external confidence:

1. formula inspection;
2. unit/property test;
3. differential golden comparison;
4. integration test through public configuration/API;
5. cross-model comparison with identical workload and mapping assumptions;
6. RTL/FPGA comparison;
7. silicon calibration across representative workloads.

Tusim has strong evidence at levels 1–4 for many functional paths. This initial audit does not establish general levels 6–7 calibration. Every quantitative chapter must state its achieved rung.

## Development implications

Literature comparison and textbook derivations may expose useful improvements, especially:

- a unified definition of cycle domains;
- machine-readable fidelity metadata per metric;
- configuration propagation tests generated from the schema;
- calibrated cross-model workloads with fixed mappings;
- explicit uncertainty intervals or error bounds;
- trace-driven context and interconnect models;
- integration tests that prove precision/dataflow settings reach every advertised engine.

These are research questions, not automatic feature commitments.
