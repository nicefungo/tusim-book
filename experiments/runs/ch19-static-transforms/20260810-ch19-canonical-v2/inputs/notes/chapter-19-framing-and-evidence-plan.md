# Chapter 19 framing and evidence plan — static scheduling and scratchpad allocation

- Date: 2026-08-06
- Edition pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Planned title: **Static Scheduling and Scratchpad Allocation**
- Stage: framing only
- Scope decision: **joint legality chapter with two adjacent but explicitly uncomposed transforms**
- Drafting status: **blocked** pending a source/claim ledger, fail-closed executable audit, mutation proof, skeptical predraft review, and post-review seal
- Reproduction: [`../experiments/ch19_framing_reproduce.sh`](../experiments/ch19_framing_reproduce.sh)
- Retained output: [`chapter-19-framing-reproduction.log`](chapter-19-framing-reproduction.log)

## 1. Reader decision and opening question

Chapter 19 answers:

> Given an in-process `tu_instruction_t` sequence, what evidence is required before a scheduler-produced order or liveness-allocator-produced rewrite may be treated as a legal program rather than a structurally plausible array of C objects?

The decision is not “which policy is fastest?” The pinned scheduler has no calibrated timing path, and the allocator has no executable semantic-equivalence oracle. The chapter must instead gate a chain of obligations:

```text
instruction interpretation
    -> dependence capture
    -> order selection
    -> order validation
    -> live-value construction
    -> interference and capacity
    -> physical placement
    -> spill/fill rewriting
    -> transformed-sequence legality
```

Every arrow is independent. A green `valid` flag at the end cannot repair an unsound earlier relation.

## 2. Global-plan risk scan

### Triggered risks

- **Broken compiler path prematurely revived — triggered and bounded.** The source contains no non-test scheduler or liveness caller, no scheduler-to-liveness call, no shipped JSON/YAML controls for either pass, and no verified ONNX/ASM-to-pass-to-queue/runtime path. Chapter 19 must keep the in-process transform boundary.
- **Broad synthesis becoming a catalogue — triggered and resolved by one legality decision.** The chapter is organized by authorization gates, not by listing the sixteen public APIs or retelling both source files independently.
- **Chapter 11 overlap — triggered and resolved by import.** Chapter 11 remains authoritative for expanded-ISA metadata, text ASM, command-queue admission/readiness/dispatch/completion/barrier/reset semantics, and the scheduler findings it already sealed. Chapter 19 imports those findings and audits only the additional static-transform legality needed to connect scheduling with allocation as adjacent evidence surfaces.
- **Chapter 18 overload — not reopened.** Runtime context retention remains closed in Chapter 18. No allocator result is presented as a producer for context live-prefix state.
- **Source-edition drift — not triggered.** Live Tusim is detached and clean at the edition pin.

### Plan disposition

No chapter merge, split, reorder, or renumbering is justified by the fresh framing evidence. `PLAN.md` already assigns this exact reader decision to Chapter 19, so this framing record does not amend the global architecture.

The completed-chapter supplement backlog for Chapters 8, 10, and 14 remains deferred to the checkpoint after Chapter 20. The mandatory Part V review remains due only after Chapter 19 closes, not during this framing pass.

## 3. Fresh evidence inventory

The reproduction exports the exact source pin to disposable storage, rebuilds the static library, runs the focused suites and scheduler sweep, checks archive and aggregate-test membership, derives complete public-API sets from the headers, inventories non-test callers, checks the cross-pass call bridge, checks shipped configuration, and re-verifies the source checkout.

Observed framing results:

```text
scheduler focused suite: 14/14
liveness focused suite: 12/12
scheduler policies: identical rows on all five shipped topologies
pipeline-tiles row: cycles=28 barriers=0 hoists=0 length=13
scheduler public APIs: 9; external non-test callers: 0
liveness public APIs: 7; external non-test callers: 0
scheduler -> liveness call bridge: absent
shipped JSON/YAML scheduler/liveness controls: none
both objects: static-archive members and aggregate make-test prerequisites
source before/after: detached, clean, exact pin
```

| Surface | Input | Output/effect | Build/test evidence | Integration evidence | Framing classification |
|---|---|---|---|---|---|
| scheduler | caller-owned `tu_instruction_t[]` | copied and reordered `tu_instruction_t[]`, graph metadata, candidate counts, serial fixed-cost total | linked in `libtucmodel.a`; 14/14 focused; scheduler sweep | no external non-test caller; no shipped config controls | executable standalone static transform with analytical metadata |
| liveness allocator | caller-owned `tu_instruction_t[]`, documented as already scheduled | rewritten `tu_instruction_t[]`, physical offsets, synthetic DMA spill/fill records, usage fields | linked in `libtucmodel.a`; 12/12 focused | no external non-test caller; no scheduler call; no shipped config controls | executable standalone static transform whose semantic legality is unproved |
| scheduler sweep | five hand-authored instruction topologies | policy-labelled rows | runnable Make target; all policies identical on every row | no runtime consumer | historical/cmodel-linked analytical report, not schedule-quality proof |
| Chapter 11 surfaces | metadata ISA, text ASM, command queue, scheduler boundary | separate representation and lifecycle effects | sealed Chapter 11 evidence | no full compiler-to-runtime stack | prerequisite boundary, not Chapter 19 scope to reteach |
| ONNX demonstration compiler | Python model frontend | emitted C demonstration | previously audited negative path | no call into either C pass | contrast evidence only; end-to-end narrative rejected |

## 4. Ranked scope candidates

### Rank 1 — selected: one transformed-sequence legality chapter, two uncomposed passes

**Reader decision.** Decide whether each relation in the dependence/order/liveness/capacity/placement/rewrite chain is strong enough to authorize the resulting in-process instruction sequence.

**Include.** Scheduler access extraction and DAG completeness; finite-edge handling; policy order; named-pass effects versus counters; order-validation identity; liveness definition/use binding; interval construction; interference; capacity arithmetic; placement-strategy distinctness; spill selection; operand patching; output bounds; transformed-sequence legality; build/caller/config reachability; documentation contradictions; and multi-objective alternatives.

**Continuity.** Import Chapter 11’s fixed-cost scheduler and missing queue/ISA bridge findings. Use Chapter 9 for SRAM capacity/address vocabulary and Chapter 10 for DMA descriptor/lifecycle ownership. Use Chapter 16 only to contrast real buffering/overlap requirements. Do not reopen their state machines.

**Benefits.** One fail-closed authorization question spans both passes without claiming composition. The same adversarial instruction fixtures can be submitted independently to scheduler and allocator, making disagreements visible while retaining separate verdicts. The chapter closes the allocator semantics explicitly deferred by Chapter 11.

**Costs.** The chapter must maintain two source maps and must say “scheduler output followed by allocator input” only in hypothetical test composition unless a caller is added. A single worked example needs separate scheduler-only, allocator-only, and deliberately composed experimental rows.

### Rank 2 — rejected: allocator-first chapter with scheduler reduced to one prerequisite page

**Reader decision.** Given a fixed instruction order, determine whether liveness, placement, and spill/fill rewriting preserve semantics within W/A/O capacity.

**Benefits.** Minimizes Chapter 11 duplication and concentrates audit depth on the less-covered allocator, where preliminary defects are denser.

**Costs and reason rejected.** Order determines live intervals and interference, while Chapter 11 did not audit scheduler-to-allocator compatibility, schedule validation identity, or whether scheduler access extraction and allocator use extraction agree. Omitting those adjacency checks would leave the reader unable to decide whether the allocator’s assumed order is trustworthy. Scheduler details should be imported compactly, but the cross-surface disagreement matrix belongs in Chapter 19.

### Rank 3 — rejected: split scheduling legality and allocation legality into two chapters

**Reader decisions.** First authorize a reordered sequence; then authorize physical placement and spill/fill rewriting.

**Benefits.** Maximum audit depth and completely separate evidence seals. It avoids any visual implication that the two passes compose.

**Costs and reason rejected.** Scheduler foundations and major defects are already owned by Chapter 11. A new scheduler-only chapter would duplicate a completed chapter, while the two static passes share the same in-process instruction type and one coherent final legality question. The absence of a call bridge can be taught as a boundary inside one chapter; it does not by itself justify another chapter number.

### Rank 4 — rejected: end-to-end compiler pipeline from ONNX/ASM through queue execution

**Reader decision.** Compile a model, schedule it, allocate scratchpad, encode/submit it, and verify runtime outputs.

**Benefit.** This would be the most pedagogically conventional full-stack narrative if the implementation existed.

**Reason rejected.** The pin has no repository-contained nontrivial path that invokes both passes and then lowers their result into the command queue or a portable binary consumer. Existing docs show illustrative `tu_core.c` snippets that are not present as executable call paths. Chapters 3 and 11 already establish the negative compiler/runtime boundary. Repeating an aspirational diagram would manufacture integration.

## 5. Selected boundary

### Include

1. `tu_scheduler.{h,c}` and `tu_liveness.{h,c}` public contracts and complete implementation paths.
2. `tu_isa.h` only as the local in-process object/field contract needed to interpret operands.
3. Focused scheduler/liveness tests and the scheduler policy sweep, with assertions classified by strength.
4. Makefile archive membership, test recipes, aggregate membership, and static-link hygiene.
5. Whole-tree caller and include inventories; shipped JSON/YAML and direct C config surfaces.
6. Scheduler-versus-allocator access-extraction comparison by opcode and operand field.
7. The legality of output order, offsets, capacities, spill/fill placement, field widths, output length, and result flags.
8. Alternatives across schedule quality, SRAM footprint/traffic, control/compiler complexity, verification cost, and model fidelity.

### Import without reteaching

- Chapter 11’s representation/encoding/parser/queue lifecycle boundary.
- Its findings that hoist/barrier APIs count candidates without transforming the graph, full scheduling clears those counts, dependency fan-in silently truncates at 16, `pipeline_tiles` and `max_window` are inert, and fixed costs are uncalibrated.
- Chapter 9’s distinction between allocated capacity, addresses, bank behavior, and direct runtime use.
- Chapter 10’s distinction between a synthetic DMA opcode and an executable descriptor-transfer contract.
- Chapter 16’s proof that naming pipeline tiles or overlap does not establish buffering legality.

### Exclude

- command-queue admission, readiness, completion, signaling, barrier, retirement, reclamation, and reset details already owned by Chapter 11;
- portable ISA encoding or a binary decoder;
- ONNX operator coverage and generated-C repair;
- runtime context save/restore or a liveness-to-live-prefix bridge;
- calibrated cycle, bandwidth, energy, area, or physical-overlap claims;
- redesigning Tusim source during the chapter audit;
- claiming a scheduler→allocator→runtime pipeline from header comments, include edges, or documentation snippets.

## 6. Preliminary audit findings to gate, not yet manuscript authority

These findings come from pinned source tracing and define the next audit’s discriminators. They remain hypotheses until the Chapter 19 ledger, executable probes, mutations, and skeptical review close them.

### Scheduler

1. **Pass adjacency is absent.** `tu_liveness.h/.c` includes scheduler definitions but calls no `tu_sched_*` API; neither pass has a non-test external caller.
2. **Null-default behavior needs a dedicated gate.** DAG construction substitutes `tu_sched_config_default` for `NULL`, but `tu_sched_run()` invokes named hoist/barrier analyses only when the caller supplied a non-null config. “NULL = default” may therefore differ from explicitly passing the default object.
3. **Named transformations are report-only.** Hoist and barrier functions count candidates; they do not mutate nodes or emit inserted instructions. Full list scheduling resets both result counters before emission.
4. **Dependency overflow weakens the intended graph.** Predecessor and successor arrays silently stop at sixteen. Validation then checks only retained edges.
5. **Order validation uses weak instruction identity.** It matches output to graph nodes by opcode, `dim0`, `dim1`, and flags, omitting `dim2` and immediates; unmatched nodes are skipped. Duplicate or near-duplicate instructions may let a violated relation escape.
6. **Barriers and later instructions need separate order probes.** A barrier depends on prior non-barrier nodes, but ordinary later nodes are not automatically made successors of that barrier. The output policy, not a complete fence relation, can determine their relative position.
7. **Access extraction is partial and opcode-specific.** Unknown/control/layout operations receive no SRAM relation; several operators use fixed 64-KiB or full-region approximations. Scheduler and allocator recognize different opcode subsets and field formulas.
8. **Estimated cycles are a serial source sum.** Emission adds one per DMA-class node and four per every other node. It is not measured elapsed time, a queue tick domain, or calibrated overlap. The sweep report’s “critical path” explanation must be reconciled against the implementation.
9. **Policy evidence is weak.** The shipped sweep gives identical cycle/count/length rows for ASAP, ALAP, and BALANCED on all five topologies. Exact output orders and a topology that discriminates policies must be audited separately.
10. **Declared controls need per-field consumption.** `pipeline_tiles` and `max_window` are inert in the implementation; `max_hoist_distance`, policy, and booleans require exact direct-consumer and effect gates.

### Liveness and allocation

1. **Use binding ignores byte ranges.** The helper explicitly discards `start` and `end`; every use attaches to the most recent definition in the same W/A/O region, even when the ranges differ.
2. **Definition and overflow failures may not propagate.** Every write creates a new VReg, but a failed VReg creation at the 128-entry bound is ignored by the analysis loop; successful return therefore may describe a truncated value set.
3. **Interference is interval-only after weak value binding.** The graph ignores physical virtual-range identity once values are constructed. Sound interval coloring cannot repair a use attached to the wrong value.
4. **Capacity subtraction can underflow.** `capacity - safety_margin` uses unsigned arithmetic without first proving `margin <= capacity`.
5. **Three placement names may encode only two searches.** BEST_FIT changes step size and retries bytewise; FIRST_FIT and WORST_FIT appear to use the same ascending 16-byte search. None computes actual gaps as their names imply.
6. **No-spill failure force-places at zero.** Capacity failure with spilling disabled does not fail closed; it assigns offset zero and continues.
7. **Victim selection does not clearly evict placed interference.** Candidate selection skips already placed values. Marking an unplaced victim spilled does not free an occupied range for the current value.
8. **Spilled values retain an unassigned offset.** Synthetic DMA helpers truncate offset and size into 16-bit fields; `UINT32_MAX` can become `0xffff`, and allocations/sizes beyond 16 bits require explicit rejection or semantics.
9. **Fill/store placement contradicts normal spill semantics.** A fill is emitted before every instruction inside a spilled interval, not only actual uses; a store is emitted after the recorded last use. The original defining instruction is also retained. Data source, backing address, and transfer ownership are absent.
10. **Operand rewriting is partial and order-dependent.** Only selected opcodes/fields are patched. MMA reads are overwritten by every live W/A value encountered, so the final iteration can select a value unrelated to the original virtual range.
11. **Output truncation may still report success.** Emission stops at a fixed doubled capacity while `output.valid` is set true unconditionally after the loop. Input suffixes or synthetic DMA records can be omitted.
12. **Usage fields are not a complete occupancy proof.** Peak values follow high-water offsets plus simplified resets; W is never reclaimed, while A/O usage can reset to zero when any value dies. They need not equal simultaneous live physical occupancy.
13. **Focused tests are presence-oriented.** Many assertions require return success, `valid=true`, nonzero usage, bounded-looking peaks, or opcode presence. They do not execute original and transformed sequences against the same data and compare effects.
14. **Documentation overclaims integration and outcomes.** The docs show scheduler→allocator→execute snippets that are not live callers and quote utilization/overlap improvements without retained calibrated evidence. Treat them as intent/contrast, not executable proof.

## 7. Required predraft evidence architecture

The next stage must create `notes/chapter-19-source-and-claim-ledger.md` before any manuscript prose. The ledger and audit must gate these families independently:

| Gate family | Required evidence | Unsafe shortcut to reject |
|---|---|---|
| representation | exact opcode/field interpretation used by each pass | shared `tu_instruction_t` type implies shared semantics |
| dependence | opcode-by-opcode read/write/range matrix; dense-edge overflow | `built=true` means intended DAG complete |
| scheduling | exact order under all policies and null/explicit defaults | candidate counts or serial cycles prove transformations |
| schedule validation | duplicate-identity adversaries and missing-map rejection | `tu_sched_validate=true` proves semantic equivalence |
| liveness | exact def/use binding, implicit definitions, redefinitions, range aliases, VReg overflow | interval endpoints look plausible |
| capacity | zero/tiny/exact/underflow margins, three regions, width limits | peak field below nominal capacity |
| placement | strategy-distinguishing fragmented layouts and overlap census | enum iteration plus `valid=true` proves distinct strategies |
| spilling | victim identity, backing-store identity, exact store/fill positions, widths, repeated uses | synthetic DMA opcode implies valid spill transport |
| rewriting | every supported opcode/operand form; wrong-value discriminators | output retains expected opcode names |
| output closure | exact multiset/order/length, overflow rejection, no dropped suffix | unconditional `valid=true` authorizes output |
| composition | separate scheduler-only and allocator-only results plus an explicitly experimental composition | include edge or documentation diagram proves a pass pipeline |
| runtime boundary | no queue/binary/runtime claim without a repository-contained consumer and effect oracle | Chapter 11 names or shared opcodes create execution |

### Minimum executable discriminator set

1. Rebuild and statically link both focused suites from a disposable archive; inject real test mutations and require nonzero failure.
2. Enumerate all nine scheduler and seven liveness public APIs from headers and all external callers from the whole tree.
3. Compare access extraction across both passes for every opcode family each recognizes; include mismatched fields, zero sizes, wraparound, and unsupported opcodes.
4. Distinguish `NULL` config from an explicit default scheduler config and independently toggle every consumed/inert field.
5. Construct duplicate instructions differing only in omitted validator identity fields; force an order violation and require rejection.
6. Cross the 16-edge scheduler bound with barriers and data hazards; require truncation to be visible and never call the weakened graph complete.
7. Create policy-discriminating ready sets and record exact output order, not only counts and estimated cycles.
8. Exercise range-separated redefinitions and uses so “most recent region” and “matching byte range” predict different values.
9. Cross the 128-VReg limit and every output-capacity boundary; require no silent truncation.
10. Test capacity/margin cases where capacity is below, equal to, and above the safety margin.
11. Build a fragmented placement case that should distinguish FIRST/BEST/WORST; compare exact offsets and reject decorative strategy claims.
12. Exercise spilling with known data provenance, multiple uses, 16-bit boundary values, and a deterministic backing-store oracle; record every emitted instruction.
13. Execute a bounded supported subset before and after rewriting against an independent semantic oracle, or mark equivalence blocked where no runtime decoder exists.
14. Mutation-test dependence extraction, range-aware use binding, capacity rejection, output-bound rejection, and transformed-sequence legality separately.
15. Run the predraft validator under normal and optimized Python and prove a real source assertion mutation is rejected in both modes.

## 8. Evidence and prose rules

- Label scheduler cycles and policy-sweep rows **analytical/estimated**, never measured or calibrated.
- Label both pass implementations **executable standalone static transforms** because they are archive-linked and focused-tested; do not label them integrated.
- Treat `valid=true`, green focused suites, archive membership, includes, shared types, and docs as different evidence rungs.
- Present placement and spill policies as materially distinct alternatives only after exact effects prove they differ. Otherwise preserve the declared alternatives as design intent and identify decorative implementations.
- Keep transformed-program correctness separate from storage footprint, instruction count, estimated traffic, compile cost, and runtime performance.
- Compare alternatives across latency/throughput opportunity, SRAM capacity and spill traffic, area/power implications, compiler complexity, runtime requirements, and verification cost; no “best” policy without a regime.
- Do not claim liveness output supplies Chapter 18’s live-prefix contract. The representations and ownership contracts differ, and no bridge exists.

## 9. Framing closure and exact next action

This framing selects scope but does not authorize drafting or claim closure. No manuscript, source/claim ledger, canonical audit, or Chapter 19 handoff is created in this stage.

Next action:

1. create the Chapter 19 source/claim ledger from the gate matrix above;
2. design a pin-locked source audit and focused C probe in disposable storage;
3. resolve or qualify each preliminary finding with exact source predicates and executable discriminators;
4. submit the frozen predraft evidence to skeptical review;
5. seal a post-review canonical run before manuscript drafting.

Repository constraints remain: work only on full-history book `main`; keep Tusim detached, clean, and read-only at the edition pin; do not build in the pinned checkout; do not push, publish, rebuild the curated branch, or modify Tusim during framing.
