# Chapter 22 — Lessons from the Exploration Portfolio

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-22)

A portfolio of exploration reports is not a leaderboard. It is a collection of bounded observations produced by different equations, executable paths, state machines, workloads, and historical assumptions. The useful synthesis is therefore not “which configuration wins?” but “which constraint appears to bind, which alternative should be tested next, and what evidence would reverse that choice?”

This chapter asks one architecture question:

> Given a workload, a correctness or continuation contract, and reconciled evidence, which modeled constraint binds, which materially distinct alternative is the next justified hypothesis, and what reversal condition would change that judgment?

At Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25`, the evidence base contains **46 pinned exploration reports** and **249 independently reviewed semantic claims**. Those claims use five dispositions—`retained`, `qualified`, `superseded`, `rejected`, and `blocked`—and occupy **eleven noncomposable metric domains**. The review identified **seven recurring mechanism families**, **eleven mandatory contradiction classes**, and **six reconciliation axes and eight producer/units/state rows**. These cardinalities establish completeness of the reviewed inventory. They do not create a common score.

Read the decision cards on two pins. The counts and every `C22R-` disposition belong to that historical register. At the v2 public pin `7a094ff6c5527eff8e4318de676f0c0221c448b4`, two questions can be asked again: did the requested dataflow run (§22.8), and did attention compute the right output for the tested tile layout (§22.10)? A new observation can change the next experiment without changing a single historical row.

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

## 22.1 Theory: constraint-first synthesis

### A binding constraint is producer-relative

Let an evidence row be

$$
e=(w,a,p,m,u,s,f),
$$

where $w$ is workload, $a$ is the alternative, $p$ the producer, $m$ the metric definition, $u$ the units, $s$ the relevant state/history, and $f$ the fidelity boundary. A statement that constraint $c$ binds is safe only inside that tuple:

$$
\operatorname{Binds}(c\mid e).
$$

It does not imply that the same constraint binds in hardware, in another report, or under another initial state. For example, the GBUF report's weight-footprint arithmetic is exact under its named equation, but the minimum tested capacity is not always the arithmetic boundary: K=64 is floor-censored at the sweep's 64 KiB minimum. Neither quantity proves that a physical SRAM is latency-optimal, area-efficient, or connected to the ordinary MMA route.

The same discipline applies to “balance.” A local equation may compare compute terms with payload-transfer terms. Roofline reasoning supports naming a compute/supply boundary when the byte boundary and assumptions are explicit, but it does not turn unrelated Tusim counters into one latency model (Williams, Waterman, and Patterson 2009 (DOI `10.1145/1498765.1498785`)).

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

A local dominance claim requires common alternatives, producer, workload, units, objective directions, constraints, and no decisive unknown. Multiobjective methods make the separation between nondominated alternatives and later preference selection explicit (Deb et al. 2002 (DOI `10.1109/4235.996017`)). Here that method is used as a guardrail: **All 249 decisions remain open**, and all 249 claims are local-dominance-ineligible. **No portfolio-wide Pareto frontier exists** in the authorized evidence.

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

**[Cross-family threshold analogy: `gbuf-sizing-sweep.md`; claim `C22R-gbuf-weight-fit-threshold`; canonically `qualified` in M7 producer/metric hazards.]** For $M=N=256$, FP16 weights, and the report’s standalone formula, this exact arithmetic illustrates the cliff but is not reassigned to M2:

$$
B_W=K\times256\times2.
$$

The historical report gives eight rows:

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

$$
T_{sparse}=T_{payload}+\max(T_{decode},T_{compute})
$$

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

An architecture ranking can reverse when a dimension crosses a tile boundary, when a route’s fixed term is amortized, or when placement changes which resource is exercised. Workload representativeness therefore requires explicit shapes and phases, not a single “typical” matrix (Eeckhout et al. 2003 (DOI `10.1109/MC.2003.1178050`)).

**[Report: `aspect-ratio-alignment-sweep.md`; claim `C22R-aspect-m200-near-aligned`; qualified.]** Under its Python formula with K=128, a 16×16 WS array, and fixed N, M=200 has 96.2% useful-slot utilization: only 3.8% local slot waste. This counters the simplistic rule that every nonmultiple should be padded to a multiple of 16. Another N, PE shape, or edge-execution policy may reverse the result.

**[Cross-family route-state break case: `C22R-dfcomp-negligible-k256`; `rejected`, M7.]** The v1 geometry log contains two different experiments. For M=N=128, K=256 and a 16×16×16 tile, the linked WS/OS/RS estimates were 81,920/20,480/50,176 cycles. On a tiny execution fixture, the process-global OS request did not change the core snapshot: the OS-labelled run used WS (delta 67), explicit OS gave 4, and RS gave 36. All three returned **58,64,139,154**. Equal outputs could not tell which route ran. Neither experiment validates the report's handwritten sub-1% overhead claim.

On the public pin, follow the request to the point of use. For a 5×9×10 GEMM on a 4×8 array at depth seven, matched WS and OS JSON files produced mode 0 (WS) and mode 1 (OS) through parsing, conversion and active selection. All 45 FP32 words per call matched the integer oracle; the estimated MMA deltas were 432 and 52. The loader names WS, OS and RS as legal; the reserved and misspelled mode values returned −1 before MMA. A post-init setter selected RS (ID 2, delta 384) while the stored request remained OS; IDs 3 and 99 returned −1 without changing RS. That third delta is not a third matched file-ingress run.

Core retention needs a different check. The public three-core sweep checked the selected modes and byte equality between peers on four workloads; it printed deltas, but did not assert them against an independent prediction. In the separate two-core and direct-state probe, alternating snapshots and direct state gave 15 calls with 846 independently expected FP32 words. The 9×10×9 edge gave WS/OS/RS deltas of 246/72/162. These are sequential calls, not simultaneous cores. Neither equal matrices nor a green aggregate test substitutes for an identity check: the wrong-route control failed before MMA; its printed zero is not a timing. The one-bit oracle control reached MMA and failed *after* 468 estimated cycles.

**[Report: `rs-pipeline-depth-sweep.md`; `C22R-rspd-switch-os-deep`, `rejected`; `C22R-rspd-ranking-invariant`, `superseded`.]** The historical report cannot select a physical route. The public single-state sweep does answer a narrower question: for the same 31×19×17 edge on a 16×16 array, RS rises from 68 estimated MMA cycles at depth one to 276 at depth two; OS stays at 88. If the objective is this one counter, RS ranks ahead of OS at one depth and behind it at the other. Nothing here prices data movement, software dispatch or physical frequency. The depth recommendation remains open.

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

A reversal is not an inconvenient outlier to average away. It is often the most decision-relevant row. Mytkowicz et al. show why uncontrolled environmental state can change experimental results without an obvious code change; here, route state and invocation order are explicit architecture-level instances of that concern (Mytkowicz et al. 2009 (DOI `10.1145/1508244.1508275`)).

## 22.9 Worked family 6: retained or buffered state shifts obligations

Keeping more state can reduce future reload, but consumes capacity and complicates save/restore. Keeping less state can make one local metric small by moving work beyond its boundary. Buffering can expose overlap, but only when lifecycle, dirty state, and accounting agree.

The rule is to follow the displaced obligation. A locally smaller number is not a global improvement if correctness, reload, or cleanup work has crossed the producer boundary.

## 22.10 Worked family 7: producer and metric-dialect hazards

The final family is a precondition for all others: a number can be internally consistent yet answer the wrong question. The portfolio’s strongest lessons often come from disagreement between labels, producers, and prose.

**[Report: `attention-engine-sweep.md`; `C22R-O1.7`, `blocked`.]** “OS dataflow wins universally” was a prescription about attention workloads, not a test of a single MMA. On the v1 pin, four-byte accesses could corrupt adjacent two-byte FP16 staging entries. The three historical repeats each detected deviation (`deviates=1`, `scales_equal=1`); their golden errors were 1.511, 2.001 and 0.536 in run order. A passing probe here meant that it detected the defect.

On the public pin, the four-arm attention probe asks whether four keys contribute to one normalized output. With zero queries, each key should have weight ¼, whether processed as one tile of four or two tiles of two. Constant V=¼ produced `0x3400` (¼) in both output lanes for both partitions. That check alone would also pass if the engine kept just the last tile. Giving the first two keys value ¼ and the last two ¾ makes the correct output ½, not ¾: both partitions returned `0x3800` in both lanes. The tagged K transpose, packed halfwords and adjacent output guards matched too. The staging matrix and KV partition matrix reported zero failures in 720 and 2,565 cases respectively. These outputs rebut a blanket claim that staging is broken; they do not certify arbitrary inputs or compare elapsed time across dataflows.

Feasibility is a separate objective. For (Q length, KV length, head dimension) = (16,512,64), the auto-tile rows select 15×512 on the default SRAMs and charge 266,240 logical DMA bytes. An explicit 16×256 fits and charges 135,168. The default found a legal tile, not a traffic minimum. Neither this example nor the repaired output changes the original 45 accepted out of 105 configurations (`C22R-O1.1`, `qualified`) or replays that matrix. To revisit the 5–36% OS claim (`C22R-O1.3`, `blocked`) or the universal default, compare verified active routes on matched decode and prefill workloads, capacities, masks and partitions, check outputs independently, and declare a common timing interval. Until then WS, OS and RS remain alternatives.

The v1 operator log also demonstrates metric dialects on a fresh 40-element census:

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

[Next: Chapter 23 — Extending Tusim Without Breaking Its Contract](../part-3-practice/23-extending-tusim-without-breaking-its-contract.md)
