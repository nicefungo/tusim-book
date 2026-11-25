# Public evidence summaries

These are summaries, not links to raw logs. Each entry identifies the observation, its owner and its limit. “Public run” means execution at the public simulator pin, not measurement on hardware. Raw transcripts, most probe inputs, binaries and internal review files are not part of this edition. See [progress through S16](progress.md) for comparison counts and exclusions; [return to contents](README.md).

## Chapter 1

[Chapter 1 — Architecture Questions Before RTL](manuscript/part-1-foundations/01-architecture-questions-before-rtl.md) · **Derivation** · S15 / S16 arithmetic

Count MACs and compulsory bytes at a stated boundary; 32 B/cycle is a budget in the example. **Limit:** The roof is not achieved bandwidth or latency.

At a notional 1 GHz, 512 GOPS and 32 B/cycle, the lower roofs for 128³, 16³ and 16×128×128 are 512, 128 and 4096/11 GOPS respectively. The last shape uses 524,288 operations and 45,056 compulsory bytes.

## Chapter 2

[Chapter 2 — How an Executable Model Earns Trust](manuscript/part-1-foundations/02-how-an-executable-model-earns-trust.md) · **First-edition run** · V1 only

The helper reported 2,619 cycles for its own event sequence. **Limit:** A mode name does not establish a shared clock, RTL agreement or a repeat at the new pin.

## Chapter 3

[Chapter 3 — Repository Tour and First Execution](manuscript/part-1-foundations/03-repository-tour-and-first-execution.md) · **Public run** · S4 / S15 / S16 reader run

The 4×4 OS example gives output rows (58, 64) and (139, 154); the MMA counter advances by 4. **Limit:** The matrix alone cannot identify OS. The four named smoke targets are not either aggregate test goal.

Reader inputs: [source](examples/first-run.c) and [configuration](examples/first-run.json). S16 matched the selected smoke completions and the output, active mode and four-cycle MMA delta.

## Chapter 4

[Chapter 4 — Configuration as the Architecture Contract](manuscript/part-2-core/04-configuration-as-the-architecture-contract.md) · **Public run** · S4 / S16 early

At 4×8 and depth 7, the OS file reaches the OS callback. A 64→256-bit width change takes the 33-byte O copy from 5 to 2 global cycles and its separate descriptor control from 22 to 19 engine cycles. **Limit:** Agreement for these fields does not imply that queue depth or rounding follows the same route.

## Chapter 5

[Chapter 5 — State, Lifecycle, and Public APIs](manuscript/part-2-core/05-state-lifecycle-and-public-apis.md) · **Public run** · S7 / S16 middle

Eight bytes from old O-SRAM reach the pending transfer’s host destination during reinitialization. The idle destination keeps its sentinel. **Limit:** Draining accepted work is not cancellation, rollback or ownership of the caller’s descriptor.

## Chapter 6

[Chapter 6 — PE Arrays, MMA Semantics, and Tiling](manuscript/part-2-core/06-pe-arrays-mma-semantics-and-tiling.md) · **Public run + derivation** · S5 / S16 early

At 4×8, WS and depth 2, twelve visits for 9³ cost 234 model cycles; twelve full-tile visits cost 384. **Limit:** Visit count alone misses partial tiles. Do not add the separate DMA counter as elapsed time.

## Chapter 7

[Chapter 7 — Pluggable Dataflows](manuscript/part-2-core/07-pluggable-dataflows.md) · **Public run** · S4 / S16 early

For 9×10×9, WS/OS/RS return matching output bits but charge 246/72/162 model cycles. Alternating sequential calls checks each core’s saved selection. **Limit:** Neither concurrent execution nor physical operand traffic was measured.

## Chapter 8

[Chapter 8 — Floating-Point Foundations](manuscript/part-2-core/08-floating-point-foundations.md) · **Public run** · S5 / S16 early

Each of three callbacks gives the expected FP32 word for all 63,486 finite nonzero binary16 inputs multiplied by +1 at K=1. **Limit:** Signed zeros, NaNs, infinities, narrowing and longer accumulations are outside this test.

## Chapter 9

[Chapter 9 — Memory Hierarchy and Banked Scratchpads](manuscript/part-2-core/09-memory-hierarchy-and-banked-scratchpads.md) · **Public run** · S6 / S16 early

A four-byte copy starting at offset 2 touches two four-byte words. The second same-tick call costs 4 penalty cycles with address-span metering versus 2 with size-only metering. **Limit:** The copy still moves four bytes. Grant consumption is not requester arbitration.

## Chapter 10

[Chapter 10 — DMA Descriptor Contracts and Tick-Driven Execution](manuscript/part-2-core/10-dma-descriptor-contracts-and-tick-driven-execution.md) · **Public runs** · S7–S8 / S16 middle

130 descriptors cover 1,548 bytes once. Explicit vs round-robin binding changes last retirement on independent paths (6,647 vs 1,700 model cycles), but not on the shared serial control. **Limit:** Constructing a chain, executing its copies and retiring queued slots are distinct tests.

## Chapter 11

[Chapter 11 — Instruction Surfaces and Command-Queue Ordering](manuscript/part-2-core/11-instruction-surfaces-and-command-queue-ordering.md) · **First-edition run** · V1 only

The native opcode table, text interpreter and queue dispatcher have different consumers. The lifecycle probe follows a command beyond admission. **Limit:** The old dependency and retirement observations are not new-pin fence tests.

## Chapter 12

[Chapter 12 — Multi-Core Clusters and Interconnect Heuristic Estimates](manuscript/part-2-core/12-multi-core-clusters-and-interconnect-heuristics.md) · **Public run + construction** · S12 / S16 late

On the 4×4 XY example, the route score is 158 cycles; a legal schedule in the stated model takes 133. **Limit:** A score above a feasible time cannot be a lower bound on the optimum. A guarded endpoint is not collective-wide admission.

## Chapter 13

[Chapter 13 — Weight Streams: Quantization, Structured Sparsity, and Compression](manuscript/part-2-core/13-weight-streams-quantization-sparsity-compression.md) · **First-edition codecs; public estimator** · V1 codecs; S15 / S16 reader estimator

At 512×16×512, changing the configured decoder rate from 1 to 16 groups per cycle reduces the standalone decode estimate from 65,536 to 4,096 cycles. The reported sparse DMA term stays 11,776. **Limit:** Reading a field in a full-config estimator does not connect compressed weights to ordinary MMA.

## Chapter 14

[Chapter 14 — Operator Compute Engines: Functional Semantics and Engine Metrics](manuscript/part-2-core/14-operator-compute-engines-functional-semantics-and-engine-metrics.md) · **Public runs** · S10–S11 / S16 late

With four equal scores and unequal value pairs, whole-row and two-tile attention both return ½. Standalone normalization counts read and write stalls; LOG retains the small negative winner at gap 20. **Limit:** A feasible tile need not minimize bytes. The BatchNorm label does not implement the per-channel reference.

## Chapter 15

[Chapter 15 — DRAM Service Models and Bandwidth Claims](manuscript/part-2-core/15-dram-service-models-and-bandwidth-claims.md) · **Public run** · S9 / S16 middle

Open vs closed page charges 220 vs 280 on repeated reads and 340 vs 280 on same-bank alternation with the stated replacement cost. **Limit:** These are service charges for four reads at one issue tick, not elapsed DRAM time.

## Chapter 16

[Chapter 16 — Double Buffering and Legal Overlap](manuscript/part-2-core/16-double-buffering-and-legal-overlap.md) · **Public run** · S8 / S16 middle

Four channels initialize, but at the controller swap the old active allocation contains the tile and the new active still contains its sentinel. **Limit:** The controller’s 2.05× score cannot establish legal overlap; check bytes at first use.

## Chapter 17

[Chapter 17 — Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy](manuscript/part-2-core/17-measurement-surfaces-counters-tracing-cycle-models-and-energy.md) · **Public runs** · S9 / S16 middle

At 1 GHz over 128 supplied ticks, 96 useful bytes give 0.75 GB/s even when the interface accounts for 192 occupied bytes. The fixed-process power comparison holds event counts constant. **Limit:** Neither rate is saturated device bandwidth; fixed-count model energy is not measured electrical power.

## Chapter 18

[Chapter 18 — Runtime Context Retention and Preemption Boundaries](manuscript/part-2-core/18-runtime-context-retention-and-preemption-boundaries.md) · **Public run** · S6 / S16 early

After FULL restore with a five-tick peer advance, the second same-region access costs 0 instead of 2. The bank keeps its grant while the region clock is restored. **Limit:** Copying region contents does not restore every physical bank field or qualify arbitrary preemption.

## Chapter 19

[Chapter 19 — Static Scheduling and Scratchpad Allocation](manuscript/part-2-core/19-static-scheduling-and-scratchpad-allocation.md) · **First-edition analysis** · V1 only

Compare value identity, live spans and emitted storage after the static rewrite. A schedule with plausible length can still omit a required relation. **Limit:** No new scheduler/allocator composition run or runtime spill/fill contract follows.

## Chapter 20

[Chapter 20 — Verification as an Architectural Feature](manuscript/part-2-core/20-verification-as-an-architectural-feature.md) · **Public run** · S13 / S16 late (selected only)

`test` launches 58 distinct named C test sources, `test-quick` 34. Together they reach 60 of 120; neither launches the two dataflow sweeps. **Limit:** These sets overlap. A successful exit is not line coverage or proof that every oracle detects errors.

S13 actually ran the two aggregates. S16 checked the live graph (60/36 members; 34 common) and compared the earlier launch receipts (61/37 top-level launches); it did not launch either aggregate.

## Chapter 21

[Chapter 21 — Designing a Trustworthy Sweep](manuscript/part-2-core/21-designing-a-trustworthy-sweep.md) · **Public run + negative controls** · S4 and S13 / S16 early and late

An OS-labelled WS route fails the identity check before MMA; a one-bit expected-output change fails after MMA. On a fixed edge shape, changing depth reverses the OS/RS estimated ordering. **Limit:** Peer equality can preserve a shared mistake. Estimated ordering says nothing by itself about traffic.

## Chapter 22

[Chapter 22 — Lessons from the Exploration Portfolio](manuscript/part-2-core/22-lessons-from-the-exploration-portfolio.md) · **Cross-edition comparison** · S14 / S16 register check

The first edition classified 249 claims across 46 reports. The new route and attention checks revise two reasons for rejecting evidence, not the historical classifications. **Limit:** No rerun of the portfolio and no hardware winner; the underlying design decisions remain open.

## Chapter 23

[Chapter 23 — Extending Tusim Without Breaking Its Contract](manuscript/part-3-practice/23-extending-tusim-without-breaking-its-contract.md) · **Cross-edition comparison** · S14 / S16 register check

File WS/OS, a direct RS setter and per-core selection have separate evidence. A rejected setter leaves the prior valid selection active in the control. **Limit:** No dynamic plug-in ABI, generated-program execution or compiler-to-runtime bridge follows.
