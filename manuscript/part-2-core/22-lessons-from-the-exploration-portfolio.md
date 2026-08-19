# Chapter 22 — Lessons from the Exploration Portfolio

A portfolio of exploration reports is not a leaderboard. It is a collection of bounded observations produced by different equations, executable paths, state machines, workloads, and historical assumptions. The useful synthesis is therefore not “which configuration wins?” but “which constraint appears to bind, which alternative should be tested next, and what evidence would reverse that choice?”

This chapter asks one architecture question:

> Given a workload, a correctness or continuation contract, and reconciled evidence, which modeled constraint binds, which materially distinct alternative is the next justified hypothesis, and what reversal condition would change that judgment?

At Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25`, the evidence base contains **46 pinned exploration reports** and **249 independently reviewed semantic claims**. Those claims use five dispositions—`retained`, `qualified`, `superseded`, `rejected`, and `blocked`—and occupy **eleven noncomposable metric domains**. The review identified **seven recurring mechanism families**, **eleven mandatory contradiction classes**, and **six reconciliation axes and eight producer/units/state rows**. These cardinalities establish completeness of the reviewed inventory. They do not create a common score. The evidence input is book commit `16ab0c21f6cca2d6c6a87589e034acb82f5dafd8`; the corrected sealed bundle is commit `0a3355c2cf88da4c2694d6691f55fc8cdfdd2a73`.

The synthesis rule is constraint-first:

```text
workload + correctness/continuation contract
  → feasible alternatives
  → producer, units, state, and metric domain
  → binding modeled constraint
  → disposition-filtered observation
  → gain and sacrifice of each live alternative
  → open decision
  → explicit reversal condition
```

The dispositions are filters, not the chapter’s organization. A retained claim may still leave the decision open because a decisive objective is unknown. A rejected report recommendation may preserve a useful counterexample. A blocked recommendation may identify exactly which implementation experiment should come next.

## Learning objectives

After completing this chapter, the reader should be able to:

1. distinguish portfolio completeness from metric comparability;
2. identify a binding modeled constraint without treating it as a calibrated physical bottleneck;
3. use the five dispositions as evidence filters rather than a ranking scale;
4. preserve producer, units, workload, and state/history boundaries while comparing mechanisms by analogy;
5. recognize fixed-cost amortization, resource cliffs, compute/supply balance, placement effects, shape-dependent reversals, retained-state obligations, and producer hazards;
6. keep materially distinct alternatives live when latency, area, power, energy, accuracy, software, or verification dimensions are unknown;
7. state a local gain, its sacrifice, the open decision, and a concrete reversal condition;
8. use negative evidence—ineffective selectors, incorrect outputs, history-sensitive counters, and insensitive metrics—to narrow claims;
9. reproduce the sealed portfolio evidence without rerunning or rewriting historical reports; and
10. avoid a global Pareto frontier, incompatible metric composition, uncalibrated physical inference, and unsupported compiler/runtime/ONNX composition.

## Prerequisite graph

```text
Chapter 6: geometry, tiling, and PE-array work decomposition
Chapter 7: dataflow routes and plugin-local estimates
Chapter 8: precision conversion and stochastic state
Chapter 9: capacity, banks, and scratchpad boundaries
Chapters 12–19: topology, codecs, operators, DRAM, overlap,
                metrics, contexts, and static scheduling
Chapter 20: claim boundary and discriminating evidence
Chapter 21: controlled sweep construction and provenance
                              │
                              ▼
Chapter 22: constraint-first portfolio synthesis
```

Chapter 17 remains authoritative for metric provenance. Chapter 20 remains authoritative for what a test authorizes. Chapter 21 remains authoritative for constructing a trustworthy sweep. This chapter does not repeat that tutorial; it starts after the reports, semantic manifests, focused probes, skeptical review, and immutable seal already exist.

## Opening architecture question

Suppose three reports recommend a wider array, a larger buffer, and a different dataflow. A tempting response is to normalize their percentages and rank the recommendations. That response is invalid unless all three results share a producer, workload, units, state, constraints, and complete objective vector. In this portfolio they generally do not.

The architect should instead ask:

- Is the result a linked executable effect, a linked estimator, a local formula, a functional observation, or historical prose?
- What exact resource or obligation produces the knee?
- Is the proposed alternative feasible under the correctness and continuation contract?
- What improves within the producer’s own metric domain?
- Which cost moves elsewhere—capacity, traffic, decode work, control, state reload, or verification burden?
- Which decisive dimensions remain unknown?
- What observation would reverse the next hypothesis?

This produces a research queue rather than a winner. That is not indecision. It is a stronger architecture result than a false optimum.

---

## 22.1 Theory: constraint-first synthesis

### A binding constraint is producer-relative

Let an evidence row be

\[
e=(w,a,p,m,u,s,f),
\]

where \(w\) is workload, \(a\) is the alternative, \(p\) the producer, \(m\) the metric definition, \(u\) the units, \(s\) the relevant state/history, and \(f\) the fidelity boundary. A statement that constraint \(c\) binds is safe only inside that tuple:

\[
\operatorname{Binds}(c\mid e).
\]

It does not imply that the same constraint binds in hardware, in another report, or under another initial state. For example, the GBUF report's weight-footprint arithmetic is exact under its named equation, but the minimum tested capacity is not always the arithmetic boundary: K=64 is floor-censored at the sweep's 64 KiB minimum. Neither quantity proves that a physical SRAM is latency-optimal, area-efficient, or connected to the ordinary MMA route.

The same discipline applies to “balance.” A local equation may compare compute terms with payload-transfer terms. Roofline reasoning supports naming a compute/supply boundary when the byte boundary and assumptions are explicit, but it does not turn unrelated Tusim counters into one latency model ([Williams, Waterman, and Patterson 2009](https://doi.org/10.1145/1498765.1498785)).

### Dispositions are evidence filters

The five canonical dispositions answer a narrow question: how may the reviewed statement enter reasoning?

| Disposition | Permitted use | What it does not mean |
|---|---|---|
| `retained` | The statement survives within its exact producer, workload, and limitation. | A design winner or physically calibrated fact. |
| `qualified` | A narrower replacement survives; omitted dimensions remain binding. | “Mostly true” outside the qualification. |
| `superseded` | A newer owner or executable result replaces the historical interpretation. | The old row should be averaged with the new one. |
| `rejected` | The affirmative conclusion is not authorized; counterevidence may remain useful. | The whole report is worthless. |
| `blocked` | A required correctness, integration, calibration, or objective dimension is absent. | The alternative is impossible. |

Across the **249 claims**, the final register contains 18 retained, 113 qualified, 8 superseded, 76 rejected, and 34 blocked statements. These counts are audit metadata, not a vote. Ten qualified claims do not outweigh one executable correctness failure.

### Comparison requires a complete local domain

A local dominance claim requires common alternatives, producer, workload, units, objective directions, constraints, and no decisive unknown. Multiobjective methods make the separation between nondominated alternatives and later preference selection explicit ([Deb et al. 2002](https://doi.org/10.1109/4235.996017)). Here that method is used as a guardrail: **All 249 decisions remain open**, and all 249 claims are local-dominance-ineligible. **No portfolio-wide Pareto frontier exists** in the authorized evidence.

The **11 noncomposable metric domains** are:

1. `codec_byte_and_estimator_cycles`;
2. `context_ledger_cycles`;
3. `db_ideal_overlap_formula_cycles`;
4. `linked_plugin_cycles`;
5. `local_formula_cycles`;
6. `noncycle_functional_or_structure`;
7. `operator_analytical_cycles`;
8. `precision_conversion_error_metric`;
9. `scheduler_serial_dag_estimate`—a retained registry name whose current producer is a serial source-local estimate, not a DAG critical path;
10. `sram_stall_returns`; and
11. `traffic_heuristic_cycles`.

A word such as “cycles” does not make two domains additive. The producer, interval, state, and omitted costs decide comparability.

### Seven recurring mechanisms, not seven universal laws

The semantic review found the following seven families:

1. fixed-cost amortization;
2. resource thresholds and discrete cliffs;
3. bandwidth/compute balance;
4. distribution or placement rather than a scalar rate;
5. shape- or placement-dependent reversals;
6. retained or buffered state scope shifting obligations; and
7. producer and metric-dialect hazards.

Each family spans at least two independent portfolio domains. The family is an analogy: a fixed cost can be amortized in both a grouped-convolution formula and an operator-fusion hypothesis, but their values cannot be added. Likewise, a capacity cliff and a decoder-width crossover share a threshold structure without sharing units or implementation.

## 22.2 Source map and evidence layers

The reviewed report universe is complete and exact:

| Portfolio domain | Reports | Claims | Representative report labels |
|---|---:|---:|---|
| geometry/balance | 12 | 58 | `aspect-ratio-alignment-sweep.md`, `dataflow-pe-interaction.md`, `pipeline-depth-*.md`, `workload-scaling-pe-optimal.md` |
| memory/movement | 9 | 52 | `dma-channel-queue-sweep.md`, `dram-type-clock-sweep.md`, `gbuf-sizing-sweep.md`, `sram-*-sweep.md` |
| numerics/representation | 7 | 42 | `structured-2of4-sweep.md`, `precision-sweep-gemm128.md`, `rounding-mode-accuracy-sweep.md`, codec reports |
| operators | 10 | 48 | attention, convolution, pooling, normalization, softmax, and fused-activation reports |
| sharing/topology | 6 | 38 | broadcast, contention, routing-order, switching-mode, topology, and multicore reports |
| runtime/static policy | 2 | 11 | `context-switch-state-scope.md`, `scheduler-policy-sweep.md` |
| **Total** | **46** | **249** | zero reports have zero reviewed claims |

Three independently reviewed manifests preserve source labels and exact report context:

- `notes/chapter-22-reviewed-claim-manifest-geometry-memory.md` covers 21 reports;
- `notes/chapter-22-reviewed-claim-manifest-numerics-operators.md` covers 17 reports; and
- `notes/chapter-22-reviewed-claim-manifest-sharing-policy.md` covers 8 reports.

`notes/chapter-22-claim-register.json` indexes the exact reviewed rows. `notes/chapter-22-predraft-registers.json` binds recurring regimes, alternatives, limitations, negative evidence, contradiction closure, and reconciliation. Neither generated JSON invents a claim universe; the frozen semantic manifests are the authority.

The focused reconciliation has **eight producer/units/state metadata rows** over **six reconciliation axes**:

| Evidence label | Producer | Units/state | Safe interpretation |
|---|---|---|---|
| `RX-geometry` | linked WS/OS/RS estimators plus active core route | linked estimated cycles; creation-time route state | route-specific estimates, no PPA or physical timing |
| `RX-memory-capacity` | report-local \(K\times N\times2\) threshold arithmetic | bytes and minimum KiB; stateless | exact footprint arithmetic; seven grid-exposed thresholds plus one K=64 floor-censored row |
| `RX-memory-overlap` | linked double-buffer controller probe | cycles, bytes, lifecycle flags; bank/context state | controller behavior, not physical ports/backpressure |
| `RX-numerics-representation` | linked codec and 2:4 decoder probe | bytes and estimated cycles; decoder-width regimes | local payload/decoder crossover |
| `RX-numerics-rounding` | linked rounding discriminator | conversion outputs; seed and invocation order | local conversion behavior, not application accuracy |
| `RX-operators` | linked attention/compute-engine probe | golden error and report-local counters; three repeats | correctness discriminator and local counters |
| `RX-sharing` | deterministic route/contention heuristic | heuristic scores; route order and traffic transpose | local route score, not queued makespan |
| `RX-runtime-policy` | context equation plus scheduler matrix | ledger cycles, bytes, serial counts; scope/topology state | local context cost and scheduler negative result |

The canonical immutable package is `experiments/runs/ch22-predraft/20260818-ch22-predraft-postreview-v3/`. It binds the exact pin, reviewed manifests, probes, raw logs, generated registers, mutation controls, and two-level manifests. Packaging establishes identity and reproducibility, not physical accuracy ([Sandve et al. 2013](https://doi.org/10.1371/journal.pcbi.1003285); [RFC 8493](https://www.rfc-editor.org/rfc/rfc8493)).

### Portfolio evidence gate

The gate passed only after exact report membership, independent semantic extraction, contradiction closure, focused executable reconciliation, source-state preservation, and mutation testing agreed. A passing gate authorizes this bounded synthesis; it does not promote report prose into executable evidence or merge the evidence classes.

## 22.3 How to read a worked mechanism family

Each worked family below uses the same decision card:

- **binding constraint**—inside one named producer and workload;
- **disposition**—the evidence filter applied to the cited claim;
- **producer/metric boundary**—what may and may not be compared;
- **alternatives with gains and sacrifices**—kept materially distinct;
- **open decision**—what cannot yet be selected; and
- **reversal condition**—the evidence that would change the next hypothesis.

The repeated card is not a sweep-construction recipe. It is a synthesis discipline applied after evidence closure.

### A practical decision worksheet

Before promoting any portfolio observation into an architecture hypothesis, write one short worksheet. The worksheet should be answerable from one reviewed claim row and its inherited report context; if it requires borrowing a denominator or objective from another report, stop.

```text
Workload and correctness/continuation contract:
Evidence label and exact claim ID:
Producer, metric domain, units, and initial state:
Binding modeled constraint:
Canonical disposition and safe replacement:
Alternative A — local gain / sacrifice:
Alternative B — local gain / sacrifice:
Decisive unknown dimensions:
Open decision:
Reversal condition and next discriminating producer:
```

The order matters. Correctness and continuation determine feasibility before performance is considered. Producer and state come before the constraint label, because a “capacity” or “bandwidth” observation has no portable meaning without the mechanism that generated it. The safe replacement, not the historical quotation, is the statement available to the architect. Alternatives must include a sacrifice even when the current report does not quantify it; the sacrifice can be marked unknown rather than replaced by a proxy.

The final two lines prevent an open decision from becoming vague future work. “Need more data” is not a reversal condition. “Reopen when an executable fused path produces correct outputs and a common elapsed counter for matched separate and fused cases” is. It names the missing producer and the observation capable of changing the judgment. Conversely, if no plausible result could reverse a preferred alternative, the worksheet has probably embedded the preference in its framing.

This worksheet also separates two kinds of uncertainty. **Parameter uncertainty** asks where a threshold lies inside an accepted producer. **Model-form uncertainty** asks whether the producer represents the intended mechanism at all. More sweep points can narrow the first; they cannot repair the second. The ineffective dataflow label, the serial scheduler estimate described as a DAG critical path, and attention counters attached to incorrect outputs are model-form failures. Their next step is a discriminating implementation or producer correction, not a denser matrix.

## 22.4 Worked family 1: fixed-cost amortization

A fixed cost matters most when useful work is small or fragmented. As useful work grows, its fraction can fall. This familiar pattern is often turned too quickly into “make the operation larger,” “fuse it,” or “deepen the pipeline.” The portfolio shows why the mechanism and the prescription must be separated.

**[Report: `pipeline-depth-dataflow-interaction.md`; claim `C22R-pddf-keep-depth-low`; qualified.]** The report’s local formula varies WS/OS and depth 1/2/4/8 for GEMM 128×128×256 on a 16×16 array. Its prescription is to keep depth “as low as the physical design allows.” The safe replacement is narrower: at fixed clock, lower depth reduces the overhead term in that formula. Frequency and timing closure are missing.

**[Report: `conv-group-sweep.md`; claim `C22R-O2.3`; qualified.]** The analytical `tu_conv_estimate_cycles` study correctly calls omitted per-group effects a modeling blind spot, but does not quantify them. As groups increase, a fixed launch, flush, indexing, or movement obligation could dominate even if the current equation omits it.

**[Report: `mma-fused-activation-overhead.md`; claim `C22R-O5.5`; blocked.]** Its claim that fusion saves 2–7× comes from standalone formulas explicitly described as having no cmodel dependency. The actual elementwise path returns a distinct post-refill event count, not a common elapsed timeline. Fusion remains a plausible hypothesis, but no speedup is authorized.

| Decision-card field | Family-1 result |
|---|---|
| Workload and correctness/continuation contract | GEMM 128×128×256 on a 16×16 array; WS and OS must produce matched outputs. Compare only the report's fixed-clock depth formula. |
| Local objective | Minimize that producer's estimated cycles without asserting an unmodeled clock-frequency gain. |
| Exact evidence label | `C22R-pddf-keep-depth-low` from `pipeline-depth-dataflow-interaction.md`. |
| Producer, metric, units, and initial state | `local_formula_cycles`; estimated cycles; fresh report-local fixture. |
| Binding modeled constraint | The formula's fixed depth term grows while workload and fixed clock remain constant. |
| Canonical disposition | `qualified`. |
| Alternatives | Depth 1, 2, 4, or 8; a materially distinct deeper design remains live if it enables a higher physical frequency. |
| Gains and sacrifices | Shallow depth lowers the formula term but may sacrifice timing closure; deeper depth adds modeled overhead but may enable frequency or layout gains absent from this producer. |
| Decisive unknowns | Depth-to-frequency/PPA relation and matched route-specific physical timing. |
| Open outcome | Keep depth low only as the next fixed-clock formula hypothesis; no physical pipeline depth is selected. |
| Reversal condition | A matched depth-frequency producer showing a deeper design wins common elapsed time while preserving correctness. |

The architectural lesson is not “always amortize.” It is to identify who pays the fixed cost and whether eliminating it merely moves an obligation into frequency, buffering, control, or correctness verification.

## 22.5 Worked family 2: resource thresholds and discrete cliffs

Many architecture effects are discontinuous. A tensor either fits or does not; a decoder either keeps pace or does not; a buffer crossing one byte boundary can change tile count. Smooth percentage reasoning can obscure these cliffs.

**[Cross-family threshold analogy: `gbuf-sizing-sweep.md`; claim `C22R-gbuf-weight-fit-threshold`; canonically `qualified` in M7 producer/metric hazards.]** For \(M=N=256\), FP16 weights, and the report’s standalone formula, this exact arithmetic illustrates the cliff but is not reassigned to M2:

\[
B_W=K\times256\times2.
\]

The sealed `memory_capacity.log` retains all **eight exact reported rows**:

| K | Weight footprint | Minimum reported GBUF |
|---:|---:|---:|
| 64 | 32,768 B | 64 KiB |
| 128 | 65,536 B | 64 KiB |
| 256 | 131,072 B | 128 KiB |
| 512 | 262,144 B | 256 KiB |
| 1,024 | 524,288 B | 512 KiB |
| 2,048 | 1,048,576 B | 1,024 KiB |
| 4,096 | 2,097,152 B | 2,048 KiB |
| 8,192 | 4,194,304 B | 4,096 KiB |

These are exact report rows, not eight independently observed fit thresholds. For K=64, the 32 KiB arithmetic footprint falls below the sweep's 64 KiB floor, so that row is floor-censored: 64 KiB is the smallest tested capacity, not the exact arithmetic fit boundary. The remaining seven rows directly expose the footprint threshold in the tested matrix. None proves ordinary hierarchy integration.

In the two adjacent boundary cases, **K=128 requires 64 KiB while K=256 requires 128 KiB**. The step is evidence for this footprint equation, not a universal sizing rule.

**[Report: `sram-obuffer-tiling-threshold.md`; claim `C22R-obuf-threshold64`; qualified.]** A 128×128 FP32 output occupies exactly 65,536 bytes, so 64 KiB is an arithmetic boundary. The report’s M-tiling is hypothetical because the direct MMA path requires whole images and does not establish this streaming capacity route.

**[Report: `dram-type-clock-sweep.md`; claim `C22R-dram-crossover-map`; qualified.]** DDR4 0.8, DDR5 1.6, and HBM2 8.0 GHz are thresholds of a printed bandwidth-only formula. The report does not call `dram_model.c`; sustained physical bandwidth, access latency, row/window state, and device cost are absent.

| Decision-card field | Family-2 result |
|---|---|
| Workload and correctness/continuation contract | Produce a 128×128 FP32 output through a legal whole-image or executable tiled route; output values must match. |
| Local objective | Find the minimum output-buffer capacity that avoids the report-local M-tiling boundary. |
| Exact evidence label | `C22R-obuf-threshold64` from `sram-obuffer-tiling-threshold.md`. |
| Producer, metric, units, and initial state | `local_formula_cycles` plus exact output bytes; cycles and bytes; fresh 128×128 fixture. |
| Binding modeled constraint | The 65,536-byte output lands exactly on the 64 KiB arithmetic threshold. |
| Canonical disposition | `qualified`. |
| Alternatives | Below 64 KiB with a proved streaming tiler; exactly 64 KiB whole-image storage; above 64 KiB for other reuse. |
| Gains and sacrifices | Below-fit capacity saves storage but requires an unproved route; at-fit capacity satisfies this fixture; above-fit capacity costs space but may serve other tensors or contexts. |
| Decisive unknowns | Whether the direct MMA route supports legal streaming tiles and whether other resident state competes for the buffer. |
| Open outcome | Treat 64 KiB as an exact boundary case, not a physical minimum recommendation. |
| Reversal condition | An executable tiler or integrated hierarchy showing matched correctness and common elapsed benefit below or above the boundary. |

A threshold supplies a boundary case for the next experiment. It does not supply a universal minimum, because the object that must fit and the route that benefits must both be executable.

## 22.6 Worked family 3: bandwidth/compute balance

A compute resource helps only while another obligation does not dominate the named producer. The portfolio repeatedly shows diminishing gains as payload supply, decoding, or queue service becomes the larger local term. It also shows that “bandwidth-bound” is unsafe when the compared terms do not share a timeline.

**[Cross-family balance break case: `CH13_WEIGHT_STREAM_PROBE`; claims `C22R-N5.1` (`retained`, M6), `C22R-N5.2` (`qualified`, M4), and `C22R-N5.3` (`qualified`, M7).]** For the 128-shaped fixture, the probe prints **160 encoded bytes and 7,811 linked estimated cycles** for the sparse case, versus dense total 12,291. Under a narrow decoder regime it prints dense 34,307 and sparse 77,312: the ordering reverses. `N5.1` owns the 5-versus-8-byte fact, `N5.2` the estimator rows and crossover, and `N5.3` the conclusion that sparse is not universally faster. The observation is used here only as a balance break case; none of the three claims is reassigned to M3.

The local sparse estimate can be understood schematically as

\[
T_{sparse}=T_{payload}+\max(T_{decode},T_{compute})
\]

under the report’s serialized-DMA and decode-overlaps-compute assumptions. The dense and sparse estimates are comparable inside this linked estimator. They are not measured latency and do not prove a direct compressed-domain MMA feed.

**[Report: `dma-channel-queue-sweep.md`; claim `C22R-dmaq-third-channel-zero`; qualified.]** A third DMA channel has zero benefit in the report’s local formula for a named case. That is evidence that the formula has exhausted its represented concurrency, not proof that a third hardware channel is useless under other traffic, queue depth, or arbitration.

**[Cross-family objective break case: `workload-scaling-pe-optimal.md`; claim `C22R-wlpe-objective-split`; canonically `retained` in M6 state/scope obligations.]** In its table, the 8×8 array wins the utilization objective while 64×64 wins absolute formula TOPS for every row. This is a real objective conflict inside the report. Unknown area and power prevent a physical preference. It remains an analogy rather than an M3 claim assignment.

| Decision-card field | Family-3 result |
|---|---|
| Workload and correctness/continuation contract | The named DMA queue fixture must transfer its W/A/O traffic completely with identical payloads and queue semantics. |
| Local objective | Reduce the fixture's local formula cycles by choosing channel count and queue depth. |
| Exact evidence label | `C22R-dmaq-third-channel-zero` from `dma-channel-queue-sweep.md`. |
| Producer, metric, units, and initial state | `local_formula_cycles`; estimated cycles; fresh queue state under the report's traffic assignment. |
| Binding modeled constraint | The represented concurrency is already exhausted before a third channel can reduce the maximum local term. |
| Canonical disposition | `qualified`. |
| Alternatives | Two channels at the tested depth; three channels; a different traffic-to-channel mapping or deeper queue. |
| Gains and sacrifices | Two channels avoid extra control; a third may expose concurrency under other traffic but adds queues, arbitration, and verification; deeper queues add storage and do not create bandwidth. |
| Decisive unknowns | Representative traces, backpressure, arbitration, and whether traffic can actually use the third channel. |
| Open outcome | Do not add a third channel for this formula row; hardware channel count remains open. |
| Reversal condition | A linked traffic producer where the third channel lowers common elapsed time under matched transfers and correctness. |

The safe question is “which represented term dominates this producer?” The unsafe question is “is the architecture bandwidth-bound?” without a calibrated, common elapsed model.

## 22.7 Worked family 4: distribution or placement, not a scalar rate

Total bytes or average bandwidth can remain constant while placement changes contention, route overlap, metadata, or saved-state obligations. Distribution is therefore an architecture axis, not noise around a scalar.

**[Cross-family break case: `CH12_PROBE`; claim `C22R-R1`; canonically `qualified` in M7 producer/metric hazards.]** The linked deterministic route heuristic evaluates two traffic patterns under XY and YX order. It is used here only to expose a placement reversal; it is not reassigned to M4:

```text
pattern A: XY=606, YX=222
pattern B: XY=222, YX=606
```

A 90-degree traffic transpose reverses the route-order winner. The probe also prints a heuristic counterexample: isolated=94, bottleneck=128, estimated=158. The estimated score is not queued makespan; finite buffers and physical NoC timing are omitted.

**[Report: `interconnect-topology-sweep.md`; claim `C22R-T7`; canonically `superseded`.]** The historical claim that mesh reduces barrier overhead by 50–68% is superseded by the executable barrier owner. Under that owner, the old mesh-dependent inference is rejected because `tu_cluster_barrier()` adds topology-independent `2×hop_latency` rather than routing through the compared hop table.

| Decision-card field | Family-4 result |
|---|---|
| Workload and correctness/continuation contract | A 3×3 or 4×4 cluster barrier must rendezvous all participating cores correctly under the named hop latency. |
| Local objective | Decide whether topology-specific routing should replace the current topology-independent barrier formula. |
| Exact evidence label | `C22R-T7` from `interconnect-topology-sweep.md`. |
| Producer, metric, units, and initial state | Anchored historical producer: standalone topology report formula `hops × (latency + payload/BW)` in `traffic_heuristic_cycles`, with report-local cycles/speedup and topology/traffic state. Superseding current owner: `tu_cluster_barrier()` analytical cycles on a fresh barrier with all participants. |
| Binding modeled constraint | The current owner contributes `2×hop_latency` independent of the route table, so historical mesh hop reductions cannot affect it. |
| Canonical disposition | `superseded`. |
| Alternatives | Keep the topology-independent barrier; implement a routed tree/rendezvous; use another collective with explicit traffic placement. |
| Gains and sacrifices | The current formula is simple but topology-insensitive; a routed collective may exploit placement but adds protocol, queueing, liveness, and verification obligations. |
| Decisive unknowns | Executable routed collective, finite-buffer traffic, deadlock/liveness proof, and common elapsed timing. |
| Open outcome | Do not choose topology from the old barrier claim; whether to implement a routed barrier remains open. |
| Reversal condition | A correct routed barrier whose common elapsed producer distinguishes topology and placement on representative collectives. |

The broad lesson is local: preserve distributions and placement maps. It is not a literature-backed universal NoC or sparse-placement law; this chapter makes only pinned Tusim-local observations.

## 22.8 Worked family 5: shape- or placement-dependent reversals

An architecture ranking can reverse when a dimension crosses a tile boundary, when a route’s fixed term is amortized, or when placement changes which resource is exercised. Workload representativeness therefore requires explicit shapes and phases, not a single “typical” matrix ([Eeckhout et al. 2003](https://doi.org/10.1109/MC.2003.1178050)).

**[Report: `aspect-ratio-alignment-sweep.md`; claim `C22R-aspect-m200-near-aligned`; qualified.]** Under its Python formula with K=128, a 16×16 WS array, and fixed N, M=200 has 96.2% useful-slot utilization: only 3.8% local slot waste. This counters the simplistic rule that every nonmultiple should be padded to a multiple of 16. Another N, PE shape, or edge-execution policy may reverse the result.

**[Cross-family route-state break case: `DATAFLOW_LINKED_EXEC`; historical claim `C22R-dfcomp-negligible-k256`; canonically `rejected` in M7 producer/metric hazards.]** The sealed linked estimates for M=N=128, K=256, tile 16×16×16 are WS=81,920, OS=20,480, and RS=50,176 cycles. The creation-time route discriminator also shows that a requested OS label can leave the core snapshot at weight stationary: the mislabeled execution has delta 67, while an explicitly active OS execution has delta 4 and RS has delta 36 on the tiny fixture. All three paths preserve the checked output tuple **58,64,139,154**. The historical handwritten claim that dataflow overhead is negligible at K=256 is rejected as current executable evidence; the probe is a reversal analogy here, not an M5 reassignment.

**[Report: `rs-pipeline-depth-sweep.md`; claim `C22R-rspd-switch-os-deep`; rejected.]** “If pipeline depth cannot be kept shallow, switch to OS” is not authorized because the extrapolated formula lacks an effective-selector and comparable physical costs. Its alternatives—deep RS/WS and OS—remain live.

| Decision-card field | Family-5 result |
|---|---|
| Workload and correctness/continuation contract | GEMM with M=200, K=128, fixed N, and a 16×16 WS array; edge and padded routes must produce matched outputs. |
| Local objective | Maximize useful-slot utilization without silently changing the workload shape. |
| Exact evidence label | `C22R-aspect-m200-near-aligned` from `aspect-ratio-alignment-sweep.md`. |
| Producer, metric, units, and initial state | `local_formula_cycles` with useful-slot utilization; percent and estimated cycles; fresh fixture. |
| Binding modeled constraint | M=200 leaves only a partial edge tile and retains 96.2% useful-slot utilization under this formula. |
| Canonical disposition | `qualified`. |
| Alternatives | Execute the edge tile; pad M to 208; choose another PE shape or dispatch route. |
| Gains and sacrifices | Edge execution avoids added work but may waste slots; padding regularizes control but adds work/storage; another shape may fit M but alter N/K behavior and hardware cost. |
| Decisive unknowns | Executable edge behavior, representative nonsymmetric shapes, selector effectiveness, and physical cost. |
| Open outcome | Do not pad M=200 by rule; retain edge execution and padding as local hypotheses. |
| Reversal condition | Matched executable traces showing padding or another shape wins the declared objective on representative workloads. |

A reversal is not an inconvenient outlier to average away. It is often the most decision-relevant row. Mytkowicz et al. show why uncontrolled environmental state can change experimental results without an obvious code change; here, route state and invocation order are explicit architecture-level instances of that concern ([Mytkowicz et al. 2009](https://doi.org/10.1145/1508244.1508275)).

## 22.9 Worked family 6: retained or buffered state shifts obligations

Keeping more state can reduce future reload, but consumes capacity and complicates save/restore. Keeping less state can make one local metric small by moving work beyond its boundary. Buffering can expose overlap, but only when lifecycle, dirty state, and accounting agree.

**[Probe: `CH16_PROBE`; double-buffer contradiction class `MC-03`; rejected historical speedup interpretation.]** The linked controller prints:

```text
PIPE_LEDGER        seq=8 piped=7 saved=0 speedup=1.142857
PIPE_DEPTH1_LEDGER seq=5 piped=3 saved=0 speedup=1.666667
PIPE_EMPTY         seq=7 piped=0 saved=0 speedup=inf
```

A reported ratio can coexist with `saved=0`, and an empty case can print infinity. The values expose a formula/accounting boundary; they do not establish physical overlap speedup. The same probe shows lifecycle obligations: a notify-only operation marks dirty state without changing shadow bytes, SRAM reinitialization loses the double-buffer wrapper, and context restore does not restore it.

**[Report: `gbuf-sizing-sweep.md`; claim `C22R-gbuf-oversize-zero-benefit`; rejected beyond local formula.]** Once the named weight fits, the standalone fixture sees no additional weight-reload reduction. Calling extra capacity “wasted silicon” is rejected because other data, contexts, and physical area are not modeled.

**[Cross-family displaced-obligation analogy: `context-switch-state-scope.md`; claims `C22R-X2` (`retained`, M7), `C22R-X3` (`qualified`, M7), and `C22R-X6` (`qualified`, M4).]** At 256 KiB total state and 32 B/cycle, the linked equation prints FULL=16,484, LIVE25=4,196, and CONTROL=100 ledger cycles (`X2`). At 16 and 64 B/cycle, FULL becomes 32,868 and 8,292 (`X3`). CONTROL's 100 cycles cover only the manager fixed term; reload, dependency, and legal continuation move to the caller (`X6`). The manuscript uses these only as an M6 analogy and does not reassign any sealed claim.

**[Cross-family qualification: `softmax-mode-comparison.md`; claims `C22R-O10.1` (`qualified`, M6) and `C22R-O10.2` (`rejected`, M2).]** `O10.1` owns the fixture-local equality among Standard, Log, and Online retained SRAM-stall rows. The current API returns stalls, not total compute cycles. Fresh-state focused probes give 4 elements→8 stalls and 40 elements→96; `O10.2` owns rejection of the report's universal \(4N\) formula. O10.2 remains assigned to M2 and is used here only as a cross-family qualification; it is not reassigned to M6. State history changes the return.

| Decision-card field | Family-6 result |
|---|---|
| Workload and correctness/continuation contract | Fresh-state softmax on the report fixture; Standard, Log, and Online modes must preserve their declared numerical result and state semantics. |
| Local objective | Compare retained SRAM-stall returns without relabeling them as total compute cycles. |
| Exact evidence label | `C22R-O10.1` from `softmax-mode-comparison.md`. |
| Producer, metric, units, and initial state | `sram_stall_returns`; stalls; explicitly fresh SRAM/model state. |
| Binding modeled constraint | The current API exposes state-sensitive SRAM stalls while compute and application numerical quality remain outside the interval. |
| Canonical disposition | `qualified`. |
| Alternatives | Standard, Log, and Online softmax; or a new state-complete elapsed producer before selecting among them. |
| Gains and sacrifices | Existing modes preserve separate algorithms but expose only partial timing; a common producer adds implementation and verification work while making the decision meaningful. |
| Decisive unknowns | Matched output accuracy, total compute time, state history, and application requirements. |
| Open outcome | No softmax mode winner is selected from equal retained stall rows. |
| Reversal condition | State-complete common elapsed and numerical evidence that distinguishes modes under matched workloads and outputs. |

The rule is to follow the displaced obligation. A locally smaller number is not a global improvement if correctness, reload, or cleanup work has crossed the producer boundary.

## 22.10 Worked family 7: producer and metric-dialect hazards

The final family is a precondition for all others: a number can be internally consistent yet answer the wrong question. The portfolio’s strongest lessons often come from disagreement between labels, producers, and prose.

**[Probe: `CH14_PROBE`; claim `C22R-O1.7`; blocked.]** The attention report says “OS dataflow wins universally.” At the pin, arbitrary-input FP16 attention correctness is blocked because 4-byte SRAM accesses corrupt 2-byte staging. Across **three operator repeats**, every required invariant passes independently, but golden-error magnitudes are retained rather than averaged: 1.511, 2.001, and 0.536. Each repeat has `deviates=1` and `scales_equal=1`. A performance default cannot be selected while output correctness is broken.

The same log demonstrates metric dialects on a fresh 40-element census:

```text
softmax stall return       96
normalization stall return 80
 elementwise return         40
```

The compact census is **96/80/40** for softmax, normalization, and elementwise respectively. These are path-specific returns, not three components of one operator pipeline latency. The attention, normalization, and softmax reports that divide one by another are rejected.

**[Probe: scheduler 5×3 matrix; claim `C22R-P1`; retained negative result.]** ASAP, ALAP, and BALANCED print identical cycles, barrier count, hoist count, and length for all five synthetic topologies. The exact rows are:

| Topology | cycles | barrier | hoist | length | policies |
|---|---:|---:|---:|---:|---|
| All-Independent | 16 | 0 | 0 | 4 | ASAP = ALAP = BALANCED |
| Serial-Chain | 10 | 0 | 0 | 4 | ASAP = ALAP = BALANCED |
| Fan-Out | 21 | 0 | 0 | 6 | ASAP = ALAP = BALANCED |
| Fan-In | 12 | 0 | 0 | 6 | ASAP = ALAP = BALANCED |
| Pipeline-Tiles | 28 | 0 | 0 | 13 | ASAP = ALAP = BALANCED |

That is the complete matrix of **five topologies by three policies**, not evidence that policies are semantically equivalent. The current cycles field is a serial source-local sum, not the report’s claimed DAG critical path. Policies may reorder output while the printed metric remains insensitive.

**[Probe: `ROUNDING_AXIS` and `ROUNDING_ORDER`; precision contradiction class `MC-06`; rejected causal generalization.]** For value 1.0007, RNE produces FP16 bits `0x3c01` and RTZ `0x3c00`. Same-seed replay is equal and changed seeds differ, but one-seed permutation differs while a stable reseeded case is equal. The result depends on exact conversion stage, seed, and invocation order; no application-accuracy conclusion follows.

| Decision-card field | Family-7 result |
|---|---|
| Workload and correctness/continuation contract | Five named synthetic dependency topologies; ASAP, ALAP, and BALANCED must preserve dependencies and identical operation completion. |
| Local objective | Determine whether policy changes an order-sensitive schedule objective, not merely a serial source-local sum. |
| Exact evidence label | `C22R-P1` from `scheduler-policy-sweep.md`. |
| Producer, metric, units, and initial state | `scheduler_serial_dag_estimate`; printed cycles/barriers/hoists/length; fresh scheduler state. |
| Binding modeled constraint | The current cycles field is a serial sum insensitive to legal reorderings, so equal rows cannot identify a policy winner. |
| Canonical disposition | `retained` as a negative sensitivity result. |
| Alternatives | Keep ASAP, ALAP, or BALANCED; or add peak-live-storage/critical-path objectives that can distinguish their legal orderings. |
| Gains and sacrifices | Existing policies retain implementation choices at little evidence cost; a discriminating producer adds state tracking and verification but enables selection. |
| Decisive unknowns | A topology and declared objective whose value changes under legal policy reorderings while outputs remain equivalent. |
| Open outcome | No scheduler policy winner is selected. |
| Reversal condition | An order-sensitive validated producer that distinguishes at least two policies under matched dependencies and outputs. |

Producer hazards are not editorial details. They are architecture findings: they reveal where observability, selection, or model ownership is insufficient for the intended decision.

## 22.11 Alternatives and trade-offs across the mechanism families

The families support a research-priority table, not a ranking:

| Mechanism family | Potential local gain | Typical sacrifice or shifted obligation | Minimum next evidence |
|---|---|---|---|
| fixed-cost amortization | lower overhead fraction | frequency, buffering, fusion control, verification | common producer plus matched correctness |
| resource thresholds | avoid reload or extra tiles | capacity, cost, other use conflicts | executable fit/tiling path |
| bandwidth/compute balance | spend resources on the represented dominant term | decoder, channels, array underutilization, control | linked end-to-end route and sensitivity |
| distribution/placement | reduce shared-link or saved-state traffic | alternate hotspots, reload, metadata | representative distributions and legal continuation |
| shape-dependent reversals | choose per-shape mapping | dispatch complexity and verification matrix | effective selectors and boundary workloads |
| retained/buffered state | reuse or overlap | capacity, lifecycle, save/restore, cleanup | state-complete elapsed accounting |
| producer/metric hazards | prevent false decisions | instrumentation and model-maintenance effort | discriminating producer-specific controls |

Area, power, energy, physical frequency, silicon latency, and application accuracy are not filled with estimates from this portfolio. Their absence keeps decisions open; it is not permission to assign proxies silently. Likewise, no compiler/runtime/ONNX bridge composes these alternatives into an end-to-end execution path.

## 22.12 Reproducible evidence walk-through

The reader-facing reproduction starts from a clean book checkout and the detached, clean Tusim pin. It verifies the already sealed package; it does not modify the source repository or regenerate historical reports.

```bash
cd /path/to/tusim-book
./experiments/run_ch22_predraft_evidence_audit.sh \
  verify 20260818-ch22-predraft-postreview-v3
```

The verifier checks exact membership and hashes, then reopens the semantic registers and focused reconciliation. A passing result establishes these bounded facts:

- all 46 reports are represented by 249 exact reviewed claims;
- the five canonical dispositions and 11 noncomposable metric domains are intact;
- all seven mechanism families span at least two portfolio domains;
- all 11 contradiction classes have nonaffirmative closure;
- all six reconciliation axes and eight metadata rows pass;
- the 5×3 scheduler matrix is complete;
- exactly three operator repeats satisfy every invariant independently;
- all 28 mutation cases are detected under normal and optimized Python;
- before/after Tusim state is identical, including ignored inventory; and
- the injected early-failure path still records and preserves source state.

Representative retained observations can be inspected without computing a composite score:

```bash
run=experiments/runs/ch22-predraft/20260818-ch22-predraft-postreview-v3

grep '^DATAFLOW_LINKED_EXEC' "$run/geometry.log"
grep '^GBUF_THRESHOLD' "$run/memory_capacity.log"
grep '^SPARSITY est' "$run/numerics_representation.log"
grep '^ROUTES\|^HEURISTIC_COUNTEREXAMPLE' "$run/sharing_topology.log"
grep '^  All-Independent\|^  Serial-Chain\|^  Fan-Out\|^  Fan-In\|^  Pipeline-Tiles' \
  "$run/runtime_static_policy.log"
```

The expected source-labeled results include WS/OS/RS 81,920/20,480/50,176 linked estimated cycles; eight GBUF reported rows, with K=64 floor-censored by the 64 KiB sweep minimum; sparse 7,811 versus dense 12,291 in one regime and sparse 77,312 versus dense 34,307 in the narrow regime; the 606/222 route reversal; and all 15 scheduler policy rows. These values remain in their own domains.

For the operator evidence, inspect each repeat rather than averaging:

```bash
grep '^=== repeat\|^ATTN diff\|^CH14_PROBE SUMMARY' "$run/operators.log"
```

The safe conclusion is that all three repeats independently detect deviation and satisfy the probe invariants. The unsafe conclusion is a mean error, a stable error distribution, or a physical accuracy estimate.

## 22.13 Verification evidence and contradiction closure

The predraft seal closes **11 mandatory contradiction classes**:

1. dataflow route and arithmetic;
2. DRAM arithmetic and device recommendation;
3. double-buffer lifecycle and speedup;
4. GBUF threshold versus universal sizing;
5. inert SRAM-arbitration selector;
6. precision and rounding causality;
7. fused-activation model;
8. operator metric and correctness;
9. broadcast/topology story;
10. context scope versus continuation; and
11. scheduler serial estimate versus DAG/compiler semantics.

“Closed” means that the stale affirmative conclusion no longer enters the chapter as true. Every class remains `open` as a design decision. For example, rejecting “OS wins universally” does not establish WS. Rejecting “extra GBUF is wasted silicon” does not establish oversizing. Superseding a mesh barrier estimate does not establish ring superiority.

The seal also exercises **28 semantic mutations**. These are semantic changes, not only checksum corruption: count-preserving membership/domain changes, missing claims, stale conclusion reaffirmation, altered reconciliation rows, incomplete scheduler matrices, repeat-integrity changes, and assertion-source mutation must fail. Both normal and `python -O` validation agree. The real assertion-mutated validator is rejected in both modes.

This is verification of the evidence package and its boundaries. It is not calibration. A hash proves which bytes were reviewed. It cannot prove that a local equation represents silicon.

### Fidelity box

> **What Chapter 22 establishes**
>
> **Established:** a complete reviewed inventory of 46 pinned reports and 249 semantic claims; five canonical dispositions; 11 separated metric domains; seven cross-domain mechanism analogies; focused exact-pin observations; 11 nonaffirmative contradiction closures; reproducible immutable evidence with 28 mutation controls.
>
> **Not established:** a portfolio-wide optimum or Pareto frontier; addition, division, normalization, or averaging across metric domains; calibrated silicon timing, area, power, energy, or frequency; application-level accuracy; physical NoC makespan; direct compressed-domain MMA feed; legal end-to-end fused operators; or compiler/runtime/ONNX composition.
>
> **Safe use:** select the next local hypothesis and its disproof condition.
>
> **Unsafe use:** turn report percentages into a hardware product recommendation.

## 22.14 Stale conclusions and negative evidence

The contradiction register preserves stale affirmative conclusions only so that they cannot silently re-enter the synthesis. The dataflow label that failed to change the active route, the double-buffer ratio with `saved=0`, the GBUF oversizing prescription, the topology-dependent barrier story, the attention default attached to incorrect output, and the policy-insensitive scheduler metric are negative evidence. They narrow the claim surface and specify the next discriminating producer. They do not select the opposite alternative.

## 22.15 Common failure modes

### Treating disposition as a score

Retained is not “five stars,” and blocked is not “zero.” A retained negative result can show metric insensitivity. A blocked fusion claim can still nominate the implementation needed to test it.

### Calling a modeled knee a physical bottleneck

The GBUF footprint boundary is exact under its byte equation, but a minimum reported capacity can be floor-censored, as K=64 is in this sweep. A DRAM crossover is exact only under its bandwidth-only formula. Neither includes calibrated physical cost or proves integration.

### Composing identical unit strings

Two producers may both print cycles while describing a serial formula, a stall return, an overlap ledger, or a route heuristic. Unit spelling is insufficient; producer and interval must match.

### Averaging away a reversal or unstable magnitude

The sparse narrow-decoder reversal and XY/YX traffic transpose are the result, not outliers. The three retained attention-error magnitudes are deliberately not averaged. Aggregation cannot repair uncontrolled or semantically distinct observations ([Fleming and Wallace 1986](https://doi.org/10.1145/5666.5673)).

### Treating equal printed metrics as semantic equivalence

The scheduler’s 5×3 rows are equal in cycles, barrier, hoist, and length, but the metric is policy-insensitive and the policies may reorder output. Softmax modes can share stall returns while differing in compute and numerical behavior.

### Ignoring displaced obligations

CONTROL_ONLY context retention makes the manager ledger small by shifting reload and continuation proof outward. Fusion may remove a pass while adding precision and control complexity. Larger buffers may reduce one reload while consuming capacity needed elsewhere.

### Rehabilitating an incorrect producer with performance counters

The attention path’s incorrect output blocks its performance prescription. Repeated local counter stability cannot make a corrupted result architecture evidence.

### Inventing an integration bridge

A report can mention compiler optimization, runtime policy, or ONNX. Mention is not an executable bridge. **No compiler/runtime/ONNX composition is established** at this pin; the chapter does not compose compiler, runtime, scheduler, or operators into an end-to-end result.

### Building a global frontier from missing objectives

The portfolio lacks a common producer and complete objectives for physical area, power, energy, accuracy, and software cost. A global frontier would encode arbitrary normalization rather than evidence.

## 22.16 Development questions

1. Which current open decision would benefit most from replacing a local formula with a linked executable producer, and why?
2. Where should a new calibrated area or energy objective attach without changing Chapter 17's ownership of metric semantics?
3. Which retained negative result is most likely to expose an ineffective selector rather than a genuinely insensitive mechanism?
4. How should an architect prioritize a correctness repair, a model-form repair, and a wider sensitivity sweep when all three are needed?

These are development questions rather than review questions because the sealed portfolio does not determine one answer. A useful response must name the target claim, preserve its present disposition, identify the new producer or objective, and state what evidence would trigger a disposition change.

## 22.17 Summary

The exploration portfolio teaches a disciplined form of architectural synthesis:

1. Start from the workload and correctness or continuation contract.
2. Keep each observation inside its producer, units, state, and fidelity boundary.
3. Identify a modeled binding constraint, not a universal physical bottleneck.
4. Use `retained`, `qualified`, `superseded`, `rejected`, and `blocked` as filters.
5. Recognize seven recurring mechanisms while keeping their metrics noncomposable.
6. Preserve alternatives with explicit gains, sacrifices, and missing dimensions.
7. Treat reversals, insensitive metrics, and correctness failures as high-value evidence.
8. End each worked case with an open decision and a reversal condition.
9. Verify the exact evidence package and all 28 mutation controls.
10. Do not construct a global Pareto frontier or infer silicon, application accuracy, or unsupported integration.

The portfolio’s strongest result is not a configuration. It is a map of which questions are ready for a bounded next experiment and which conclusions remain unauthorized.

## 22.18 Review questions

1. Why do the 46-report and 249-claim counts establish completeness but not comparability?
2. Explain why a `qualified` claim is not simply a lower-confidence `retained` claim.
3. List the fields that must match before two observations can support a local dominance statement.
4. The GBUF fixture says K=1,024 needs 512 KiB. What exactly is proved, and what remains unknown?
5. Why does the sparse estimator’s 12,291/7,811 row not contradict its 34,307/77,312 row?
6. Explain why the route scores 606/222 and 222/606 are more useful than their average.
7. Why can the scheduler’s 15 equal policy rows be a retained result without proving policy equivalence?
8. What obligation moves outside the context-manager ledger under CONTROL_ONLY retention?
9. Why are softmax=96, normalization=80, and elementwise=40 invalid as a summed pipeline time?
10. What does the attention probe’s three-repeat policy preserve that an average golden error would hide?

## 22.19 Review-question answer key

1. The counts prove exact inventory coverage; they do not align producer, workload, units, state, or objectives.
2. `qualified` authorizes a specific narrower replacement. It is a semantic boundary, not a confidence score.
3. Alternatives, workload, producer, metric definition, units, state/history, objective directions, constraints, and decisive unknowns must be common and complete.
4. The named FP16 weight footprint crosses the report-local 512 KiB fit threshold. Physical integration, latency, area, energy, contention, and uses by other objects remain unknown.
5. Decoder width changes the dominant local term. Both rows belong to the same linked estimator but represent different declared regimes.
6. Averaging destroys the traffic-transpose reversal, which is the evidence that route order depends on placement.
7. Equality is retained as evidence that the printed metric is insensitive. The policies may still differ in ordering or semantics that the producer does not measure.
8. Reload, dependency reconstruction, and legal continuation move to the caller or surrounding runtime.
9. They are path-specific return dialects with different intervals; a common elapsed producer has not been established.
10. It proves every repeat independently detects incorrect attention output while preserving each magnitude and invariant, without manufacturing a stable distribution.

## 22.20 Design exercises

1. Choose one fixed-cost hypothesis. Write its binding constraint, alternatives, gain, sacrifice, and reversal condition.
2. Design an executable test that distinguishes GBUF “fit” from useful integrated reuse. Name the producer and failure condition.
3. Extend the sparse decoder study with a second workload axis. Which results may remain in one metric domain?
4. Propose a finite-queue NoC experiment for the XY/YX reversal. Which current heuristic claims would it supersede rather than combine?
5. Design an order-sensitive scheduler objective that could distinguish ASAP, ALAP, and BALANCED while preserving semantic correctness.
6. For a proposed fused activation, enumerate the correctness, elapsed-time, control, precision, and verification evidence required before claiming speedup.
7. Construct a local multiobjective comparison for two alternatives with one complete producer. State objectives, directions, constraints, and why it still does not join a portfolio-wide frontier.
8. Identify one claim that should remain blocked even if its report arithmetic is repaired. Explain the missing bridge or objective.

## 22.21 Exercise answer sketches

1. A valid card might compare shallow and deep pipelines in one fixed-clock formula, name frequency/timing closure as the sacrifice, keep the choice open, and reopen it only when a depth-frequency producer exists.
2. Route both at-fit and above-fit capacities through the same executable hierarchy and tiler. Hold workload, initial state, and correctness fixed; fail the “useful reuse” hypothesis if reload or common elapsed behavior is unchanged.
3. Add decoder width or matrix shape while preserving the same linked dense/sparse estimator, byte boundary, and assumptions. Do not combine application accuracy or physical energy unless a new common producer supplies them.
4. Inject both transposed traffic patterns into the same finite-buffer network, record queue occupancy and completion time, and preserve correctness. The new producer may supersede the heuristic ordering for those fixtures, but its elapsed values must not be added to old heuristic scores.
5. Use a dependency graph where legal reorderings change a declared order-sensitive objective—such as peak live storage or a modeled critical path—then verify output equivalence. Equal serial sums alone are not discriminating.
6. Require bitwise or tolerance-bounded output equivalence, one common elapsed interval, matched initial state, explicit movement, control and precision costs, and negative controls that can detect an ineffective fusion selector.
7. Declare one producer and complete local objectives, for example linked estimated cycles and bytes under fixed correctness. Compute only local nondominance; do not import area, energy, or software scores from another domain.
8. Attention performance remains blocked after arithmetic repair until arbitrary-input output correctness is restored. Compiler/runtime/ONNX composition also remains blocked until an executable bridge—not report prose—owns it.

## Primary references

- Deb, K., Pratap, A., Agarwal, S., and Meyarivan, T. “A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II.” *IEEE Transactions on Evolutionary Computation* 6(2), 2002. [https://doi.org/10.1109/4235.996017](https://doi.org/10.1109/4235.996017).
- Eeckhout, L., Vandierendonck, H., and De Bosschere, K. “Designing Computer Architecture Research Workloads.” *Computer* 36(2), 2003. [https://doi.org/10.1109/MC.2003.1178050](https://doi.org/10.1109/MC.2003.1178050).
- Fleming, P. J., and Wallace, J. J. “How Not to Lie with Statistics: The Correct Way to Summarize Benchmark Results.” *Communications of the ACM* 29(3), 1986. [https://doi.org/10.1145/5666.5673](https://doi.org/10.1145/5666.5673).
- Mytkowicz, T., Diwan, A., Hauswirth, M., and Sweeney, P. F. “Producing Wrong Data Without Doing Anything Obviously Wrong!” *ASPLOS XIV*, 2009. [https://doi.org/10.1145/1508244.1508275](https://doi.org/10.1145/1508244.1508275).
- Williams, S., Waterman, A., and Patterson, D. “Roofline: An Insightful Visual Performance Model for Multicore Architectures.” *Communications of the ACM* 52(4), 2009. [https://doi.org/10.1145/1498765.1498785](https://doi.org/10.1145/1498765.1498785).
- Sandve, G. K., Nekrutenko, A., Taylor, J., and Hovig, E. “Ten Simple Rules for Reproducible Computational Research.” *PLoS Computational Biology* 9(10), 2013. [https://doi.org/10.1371/journal.pcbi.1003285](https://doi.org/10.1371/journal.pcbi.1003285).
- RFC 8493. “The BagIt File Packaging Format (V1.0).” Internet Engineering Task Force, 2018. [https://www.rfc-editor.org/rfc/rfc8493](https://www.rfc-editor.org/rfc/rfc8493).

### Primary repository evidence

All repository evidence is pinned to Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25`.

- [`notes/chapter-22-claim-register.json`](../../notes/chapter-22-claim-register.json) — 249 exact reviewed semantic claims over 46 reports.
- [`notes/chapter-22-predraft-registers.json`](../../notes/chapter-22-predraft-registers.json) — mechanism, alternatives, limitation, contradiction, negative-evidence, and reconciliation registers.
- [`notes/chapter-22-reviewed-claim-manifest-geometry-memory.md`](../../notes/chapter-22-reviewed-claim-manifest-geometry-memory.md) — geometry/balance and memory/movement source labels.
- [`notes/chapter-22-reviewed-claim-manifest-numerics-operators.md`](../../notes/chapter-22-reviewed-claim-manifest-numerics-operators.md) — numerics/representation and operator source labels.
- [`notes/chapter-22-reviewed-claim-manifest-sharing-policy.md`](../../notes/chapter-22-reviewed-claim-manifest-sharing-policy.md) — sharing/topology and runtime/static-policy source labels.
- [`notes/chapter-22-skeptical-review-dispositions.md`](../../notes/chapter-22-skeptical-review-dispositions.md) — complete predraft review resolution.
- [`run-manifest.json`](../../experiments/runs/ch22-predraft/20260818-ch22-predraft-postreview-v3/run-manifest.json) — immutable final evidence identity; the adjacent run directory contains raw logs, manifests, reconciliation, and mutation results.
- [`references/ch22-predraft-method-primary-sources.md`](../../references/ch22-predraft-method-primary-sources.md) — verified method-source scope and limitations.
