# Chapter 19 — Static Scheduling and Scratchpad Allocation

A static transform is easy to recognize by its shape: take an instruction array, analyze it, and return another instruction array. That shape is not a correctness proof. A legal transform needs a chain of relations that agree on operand meaning, dependence, value identity, storage capacity, physical placement, and output completeness.

This chapter asks one practical question:

> Given an in-process `tu_instruction_t` sequence, what evidence is required before a scheduler-produced order or allocator-produced rewrite may be treated as a legal program rather than a structurally plausible array of C objects?

At the pinned Tusim revision, the scheduler and liveness allocator are real, executable C components. Both belong to `libtucmodel.a`; their focused suites report `14/14` and `12/12`. They also share the packed `tu_instruction_t` representation. These facts establish two standalone static transforms. They do **not** establish an ONNX-to-scheduler-to-allocator-to-runtime pipeline, a portable binary encoding, or semantic equivalence between input and output.

The key discipline is to authorize each relation separately:

```text
instruction interpretation
    → dependence capture
    → order selection
    → order validation
    → live-value construction
    → interference and capacity
    → physical placement
    → spill/fill rewriting
    → output closure
```

A final `valid=true` cannot repair an earlier relation that was incomplete or inconsistent.

## Learning objectives

After completing this chapter, the reader should be able to:

1. separate representation adjacency from an integrated compiler/runtime path;
2. audit scheduler access extraction, finite dependency storage, list-order selection, fixed cycle estimates, and transformed-order validation as independent relations;
3. distinguish live-value identity from interval overlap and physical placement;
4. detect unsigned capacity errors, silent no-spill aliasing, incomplete spill contracts, partial operand rewriting, and output truncation;
5. interpret focused tests, static linkage, bounded probes, local `valid` flags, and documentation as different evidence rungs;
6. compare conservative ordering, complete dynamic graphs, range-aware value IRs, no-spill rejection, explicit backing-store spilling, live-range splitting, and larger scratchpads across performance, storage, area/power, software, verification, and fidelity costs.

## Prerequisite graph

```text
Chapter 9: SRAM capacity, addressing, banks, and direct use
                      ┐
Chapter 10: DMA descriptors, ownership, and transfer lifecycle
                      ├──→ Chapter 19: static-transform legality
Chapter 11: packed objects, scheduler boundary, and queue lifecycle
                      ┤
Chapter 16: buffering and legal overlap
                      ┘

Chapter 18: runtime context LIVE prefixes
        └── contrast only; no allocator-to-runtime bridge exists
```

The reader needs half-open byte ranges, RAW/WAR/WAW vocabulary, finite graph storage, and the distinction between analytical estimates and calibrated timing. Chapter 11's queue state machine is imported as a boundary rather than retaught.

## Opening architecture question

Suppose a compiler model returns a reordered instruction array with `valid=true`, then an allocator returns a rewritten array with another `valid=true`. Which facts must be established before the second array may be consumed?

A weak answer checks only return codes and output length. A strong answer requires common operand semantics, a complete dependence graph, a legal order, correct reaching definitions, complete interference, checked capacity, disjoint physical placement, a defined backing-store protocol for inserted records, provenance binding, and exact output closure. The chapter develops and tests that stronger answer.

---

## 19.1 Scope: adjacent transforms are not an integrated pipeline

The scheduler and allocator are adjacent static transforms over the same ABI-local instruction objects. Adjacency does not establish common operand meaning, pass composition, or a deployment path. This chapter therefore audits each transform separately and treats every cross-pass experiment as an explicit bounded composition rather than repository integration.

Chapter 11 remains authoritative for expanded-ISA metadata, text assembly, command-queue admission and lifecycle, barriers, completion, signaling, reclamation, and reset. Chapter 19 owns the additional static-transform question: whether order, value, placement, and rewrite relations are internally strong enough to authorize an output array.

This boundary also separates Chapter 19 from Chapter 18. Allocator live intervals are instruction-index intervals over inferred virtual values. Chapter 18's LIVE retention controls are caller-supplied W/A/O byte prefixes at a runtime context boundary. No bridge converts one representation into the other.

## 19.2 Theory: legality is a conjunction, not one flag

Let an input sequence be

\[
I = (i_0, i_1, \ldots, i_{n-1}),
\]

and let a static transform return

\[
T(I) = (i'_0, i'_1, \ldots, i'_{m-1}).
\]

A useful authorization model is:

\[
\operatorname{Legal}(T(I)) =
R_{\text{repr}}
\land R_{\text{dep}}
\land R_{\text{order}}
\land R_{\text{value}}
\land R_{\text{capacity}}
\land R_{\text{placement}}
\land R_{\text{rewrite}}
\land R_{\text{closure}}.
\]

Each term answers a different question:

- **Representation:** Do all passes interpret opcode and operand fields consistently?
- **Dependence:** Are all relevant RAW, WAR, WAW, control, and memory relations represented?
- **Order:** Does the emitted order respect the complete intended graph?
- **Value:** Does each use refer to the definition that produced its bytes?
- **Capacity:** Is every assigned interval within the effective W/A/O storage bound?
- **Placement:** Do simultaneously live values occupy disjoint physical ranges?
- **Rewrite:** Are all affected operands and inserted operations complete and correctly bound?
- **Closure:** Are all required input effects represented exactly once, with no silent suffix loss?

A local success flag usually proves less. `graph->built` says that graph construction reached its final assignment. `result->valid` in list scheduling compares emitted count with retained graph-node count. `output->valid` in allocation is assigned after an output loop. None of these fields independently proves the full conjunction.

### Dependence and list scheduling

A scheduler commonly constructs a directed acyclic graph \(G=(V,E)\), where each instruction is a node and each required precedence relation is an edge. A list scheduler repeatedly selects a ready node whose predecessors have all been emitted. A policy changes the choice among ready nodes; it must not weaken \(E\).

Tusim tracks W/A/O read and write ranges. Two half-open byte ranges overlap when

\[
[a_0,a_1) \cap [b_0,b_1) \neq \varnothing
\quad\Longleftrightarrow\quad
 a_0 < b_1 \land b_0 < a_1.
\]

That test is only as meaningful as the operand-to-range mapping that produced the endpoints.

### Liveness and interference

For a virtual value \(v\), the allocator records a definition index and a final-use index. Its implementation treats two non-implicit values as interfering when their inclusive instruction intervals overlap:

\[
[d_i,u_i] \cap [d_j,u_j] \neq \varnothing.
\]

Interference then constrains physical placement. If value \(i\) is assigned byte interval \([p_i,p_i+s_i)\), every interfering pair must satisfy:

\[
[p_i,p_i+s_i) \cap [p_j,p_j+s_j) = \varnothing.
\]

Correct graph coloring cannot repair a use that was attached to the wrong definition. Value identity precedes interference.

### Capacity and rewriting

For region \(r\), Tusim computes an effective capacity as

\[
C_{\text{eff},r}=C_r-M,
\]

where \(M\) is a shared safety margin. In unsigned arithmetic this equation is valid only after proving \(M\le C_r\). Placement also needs width checks for every range-end addition and every field used to encode a rewritten offset or size.

A spill transform adds a stronger obligation. It must define backing-store identity, save timing, reload timing, and which uses consume the reloaded value. Merely inserting instructions named `DMA_LOAD` and `DMA_STORE` does not supply those contracts.

## 19.3 Source map and public surfaces

The scheduler and allocator share this in-process C object:

```c
typedef struct __attribute__((packed)) {
    uint8_t  opcode;
    uint8_t  flags;
    uint16_t dim0;
    uint16_t dim1;
    uint16_t dim2;
    uint32_t immediates;
} tu_instruction_t;
```

The scheduler accepts an array of these objects and emits a reordered array. The allocator accepts an array, constructs virtual values and interference graphs, assigns offsets, and emits a rewritten array that can contain synthetic DMA operations. The shared type proves representation adjacency only.

The source surfaces are deliberately separated:

| Evidence role | Repository-relative surface | Safe use in this chapter |
|---|---|---|
| shared ABI-local representation | `tu_cmodel/isa/tu_isa.h` | field layout and opcode vocabulary, not portable encoding |
| scheduler public contract and implementation | `tu_cmodel/isa/tu_scheduler.h`, `tu_cmodel/isa/tu_scheduler.c` | API inventory, access relations, graph/order/validation behavior |
| allocator public contract and implementation | `tu_cmodel/isa/tu_liveness.h`, `tu_cmodel/isa/tu_liveness.c` | VReg, interference, placement, spill/rewrite, and closure behavior |
| focused executable evidence | `tests/test_scheduler.c`, `tests/test_liveness.c` | named assertions and focused counts, not semantic equivalence |
| analytical report | `tests/test_scheduler_sweep.c` | retained policy rows under its own formulas, not a fail-closed gate |
| build and aggregate membership | `Makefile` | archive membership, focused rules, and `make test` reachability |
| historical/design-intent documentation | `docs/compiler-scheduling-pass.md`, `docs/liveness-allocation.md` | intended pipeline concepts only where reconciled with source |
| bounded Chapter 19 evidence | `experiments/ch19_static_transform_probe.c`, `experiments/runs/ch19-static-transforms/20260810-ch19-postreview-v3/` | exact pin-specific probe rows, manifests, controls, and provenance |

Whole-tree caller and configuration analysis at the edition pin finds:

```text
scheduler public APIs: 9; external non-test callers: 0
liveness public APIs: 7; external non-test callers: 0
scheduler → liveness call bridge: absent
shipped JSON/YAML controls for either pass: absent
```

No repository caller invokes both passes and then lowers the result into the command queue or another executable consumer. The documentation contains illustrative pass-pipeline snippets, but those snippets are not live call paths.

The scheduler header declares nine public functions:

- access analysis;
- DAG construction;
- mobility computation;
- DMA-hoist analysis;
- barrier-insertion analysis;
- full scheduling;
- transformed-order validation;
- result printing;
- graph printing.

The liveness header declares seven:

- liveness analysis;
- interference construction;
- coloring;
- allocation application;
- the four-stage convenience wrapper;
- result printing;
- interference printing.

The configuration surfaces are direct C structures. Scheduler policy, `hoist_dma`, `insert_barriers`, and `max_hoist_distance` have implementation consumers. `pipeline_tiles`, `max_window`, and scheduler `verbose` are declared and defaulted but inert in `tu_scheduler.c`. Allocator capacities, margin, placement enum, spill enum, and `enable_spilling` reach implementation logic; allocator `verbose` is inert.

Passing a null scheduler configuration is not internally identical to passing `tu_sched_config_default`. DAG construction substitutes defaults, but the full wrapper invokes named hoist and barrier analyses only when the caller supplied a non-null pointer. At this pin, those named helpers only count candidates and list scheduling later clears both counts, so the retained probe finds equal output arrays and zero final counts. This is an observed equality at the pin, not a general API equivalence guarantee.

The evidence rungs remain distinct:

| Observation | What it establishes | What it does not establish |
|---|---|---|
| object is in `libtucmodel.a` | build reachability | production caller or runtime use |
| focused suite passes | named examples meet their assertions | complete semantic preservation |
| shared packed type | ABI-local representation adjacency | common operand semantics or wire format |
| documentation diagram | design intent | executable call path |
| final `valid=true` | implementation reached its local success assignment | complete legality chain |
| exact bounded probe | one pin-specific behavior | universal behavior or calibrated performance |

## 19.4 Implementation walk-through: scheduler access relations and graph completeness

### Operand interpretation is opcode-specific

`tu_sched_analyze_access()` maps selected opcodes into W/A/O ranges. DMA, MMA, attention, pooling, convolution, elementwise, and normalization families use different field formulas. Some use fixed 64-KiB spans or `UINT32_MAX` sentinels. Unknown, control, and several layout/sparsity operations have no SRAM relation.

One compact example shows why field ownership must be explicit:

```text
SCHED_DMA_FIELDS flags=0x1 writesW=0 writesA=1 rangeA=100:101
```

The global ISA header names low flag bits as precision controls, but the scheduler's basic DMA path also uses low bits as a region channel. `TU_FLAG_PREC_FP32` therefore selects A-SRAM in this analysis, and a zero DMA size is converted to one byte. This is the scheduler's pinned interpretation, not a normative cross-component contract.

The scheduler and allocator also disagree on strided DMA. With flags equal to four, the scheduler takes region bits from `flags[3:2]`, while liveness takes `flags[1:0]` for the definition and also reaches a broad use classifier:

```text
CROSS_STRIDED sched_writes=0/1/0 live_vregs=2
  v0=0/0/0/16 v1=1/-1/0/64
```

The same C object means an A-region write to the scheduler, a W-region definition to the allocator, and an additional implicit A-region use. A shared struct cannot authorize a pass chain when adjacent stages disagree at the first relation.

The canonical probe records all 128 numeric opcode values. For each value it retains the scheduler access mask and allocator-created VRegs. This census bounds every per-op statement in this chapter to the edition pin. It is not a normative ISA table and does not make undefined numeric gaps supported operations.

### Finite edge storage weakens the intended graph

Each scheduler node stores at most 16 predecessors and 16 successors. The builder silently skips an edge when either endpoint's corresponding array is full. It still sets `graph->built=true`.

A barrier after 17 prior ordinary instructions records only 16 predecessors:

```text
SCHED_DENSE intended=17 retained=16 built=1
```

The reciprocal-edge case is more consequential. One producer with 17 intended consumers fills its successor array. The seventeenth consumer receives no predecessor and can become ready immediately:

```text
SCHED_FANOUT intended=17 producer_succs=16 last_preds=0 first=DMA.LOAD
```

DAG construction succeeds, list scheduling emits all 18 nodes, and the local result-validity count succeeds. The omitted relation is already gone before either check runs.

Finite edge storage is a legitimate implementation choice; silent weakening is not the only choice. Alternatives include rejecting graph construction, allocating edges dynamically, splitting scheduling windows with explicit boundary contracts, or conservatively serializing dense regions. Each trades memory and compiler complexity against optimization opportunity and proof strength.

### A barrier constrains earlier nodes, not all later nodes

A scheduler barrier receives retained predecessor edges from prior non-barrier nodes. Later ordinary instructions do not receive a predecessor merely because a barrier appears earlier in source order. BALANCED policy can therefore move a later ready DMA load before both the earlier NOP and the barrier:

```text
OPS barrier_crossing n=3
  0:DMA.LOAD/64/16/0/0x00000000
  1:NOP/0/0/0/0x00000000
  2:BARRIER/0/0/0/0x00000000
```

A later DMA similarly crosses `HALT` in the bounded case. These are scheduler-graph observations. They do not import or modify Chapter 11's separate command-queue barrier behavior.

## 19.5 Policy selection, named helpers, cycles, and validation

### Policy can change order without changing the cycle sum

For one independent NOP and DMA load, the exact result is:

```text
SCHED_POLICY
  asap=NOP,DMA.LOAD
  alap=NOP,DMA.LOAD
  balanced=DMA.LOAD,NOP
  cycles=5/5/5
```

ASAP and ALAP tie-break by original ID in this fixture. BALANCED gives a DMA load higher priority. All three totals remain five because the implementation adds one for a DMA-class emitted node and four for every other emitted node:

\[
C_{\text{sched}}=\sum_{v\in\text{emitted}}
\begin{cases}
1,&v\text{ is DMA-class}\
4,&\text{otherwise.}
\end{cases}
\]

This is a serial source-local estimate. It is not a DAG critical path, queue ticks, engine service time, modeled overlap, RTL cycles, or measured hardware time.

The shipped five-topology sweep prints identical cycles, candidate counts, and lengths for ASAP, ALAP, and BALANCED. It does not print exact order, check every run return value, or fail its `main()` when a row is wrong. The canonical bundle retains it as a report, while order-sensitive conclusions come from the dedicated probe.

### Named transformation helpers count candidates

`tu_sched_hoist_dma()` scans for selected DMA candidates and increments a count. It does not move graph nodes or attach priority metadata. Its source chooses the minimum predecessor ID although the nearby comment says the latest predecessor.

`tu_sched_insert_barriers()` scans a narrow DMA-store-to-later-compute successor relation and increments a count. It emits no barrier instruction. The paired probe records:

```text
SCHED_BARRIER_DIRECTION store_then_compute=1 compute_then_store=0
```

The common earlier-compute-write followed by DMA-store-read direction produces zero. Full scheduling later resets both candidate fields. Therefore the safe interpretation is “count-only source heuristics,” not “hoisted DMA” or “inserted barriers.”

### Validation does not prove a bijection

`tu_sched_validate()` maps emitted instructions back to graph nodes using opcode, `dim0`, `dim1`, and flags. It omits `dim2` and `immediates`. Near-duplicate instructions can therefore map to the wrong original node. The probe reverses a required relation between two instructions that differ only in omitted fields and obtains:

```text
SCHED_VALIDATE reversed_dependency accepted=1
  omitted_dim2=1,2
  omitted_imm=0x11111111,0x22222222
```

Unmatched graph nodes are skipped. A completely unrelated same-length result with its `valid` bit set is accepted:

```text
SCHED_VALIDATE unmatched accepted=1 graph_nodes=2 result_nodes=2
```

A stronger validator needs complete instruction identity or stable origin IDs, a bijection between input nodes and output positions, graph/result provenance, explicit rejection of unmatched nodes, and validation against the intended—not truncated—dependence relation.

## 19.6 Value construction and interference

### Uses bind to the newest same-region definition

The allocator extracts byte ranges for definitions and uses, but `find_or_create_vreg()` explicitly discards use `start` and `end`. For a use, it scans backward and extends the most recent VReg in the same W/A/O region.

Consider two W loads at disjoint offsets followed by an MMA whose W operand refers to the first range. The retained analysis reports six VRegs because broad opcode classification also creates repeated implicit A records and an O definition. The W use extends the newest disjoint W value:

```text
LIVE_BIND vregs=6 w_nodes=2 w_edges=0
  v0=0/0/0/16
  v2=0/1/2/16
```

The first W value dies at instruction zero; the second extends through the MMA. The resulting interference graph is deterministic for the constructed values, but the value relation is wrong before interference begins.

A production value model needs a stable identity. Possibilities include explicit virtual IDs, exact region-plus-range lookup with versioning, SSA-like definition IDs, or a memory-SSA relation for partial overlaps. Range lookup alone still needs alias and partial-write rules.

### Implicit values and the global VReg bound

A use without a prior definition creates a VReg with `first_def=-1`. Later uses skip implicit records, so repeated uses can create repeated implicit values rather than extend one source.

The result table contains 128 VRegs total across W, A, and O. When creation reaches that bound, the helper returns null, but the analysis loop ignores the return and eventually returns success:

```text
LIVE_VREG_LIMIT input_defs=129 rc=0 retained=128
```

The implemented limit is global even though comments can be read as per-region. A fail-closed design should propagate the first failed creation, identify the rejected instruction/value, and leave no partially authorized result.

### Interference construction is not idempotent

The public interference builder appends pointers to each per-region graph without resetting `num_vregs`. It then allocates a new matrix without freeing the old one. Calling it twice on one result changes the relation:

```text
LIVE_REBUILD nodes=2->4 matrix_replaced=1 edges=2
```

A low-level API should either consume a fresh result exactly once, clear and rebuild safely, or expose ownership and destruction explicitly. Repeated calls should not silently duplicate graph nodes.

### Inclusive intervals are a policy choice

For non-implicit definitions, Tusim considers `[first_def,last_use]` inclusive. Two values defined/used at the same instruction therefore interfere. This can be conservative and easy to explain, but it may miss reuse opportunities when a machine contract allows a read and a replacement write in a safe order within one instruction boundary.

Changing endpoint policy is not a free optimization. It requires a precise execution model for read-before-write behavior, instruction expansion, and multi-result operations. At this pin, inclusive overlap is an executable allocator rule, not a hardware timing claim.

## 19.7 Capacity and placement

### The safety margin can underflow

The allocator subtracts the same unsigned safety margin from each region capacity without first checking the relation. With `capacity=16`, `margin=32`, spilling disabled, and one 100-byte W value, subtraction wraps to a large apparent capacity:

```text
LIVE_CAP_UNDERFLOW
  capacity=16 margin=32 valid=1 peak=100 out_n=1 off=0
```

The required order is:

1. validate the configuration enum and region;
2. require `margin <= capacity`;
3. compute `effective = capacity - margin`;
4. perform overflow-checked range-end arithmetic;
5. reject any value that cannot be placed under the selected policy.

### Three placement names implement fewer distinct searches

The header names FIRST_FIT, BEST_FIT, and WORST_FIT. The implementation sorts values by `first_def` and scans ascending offsets:

- BEST_FIT initially steps by four bytes and, when spilling is enabled, retries byte by byte;
- FIRST_FIT steps by 16 bytes;
- WORST_FIT also steps by 16 bytes.

No branch computes free-gap sizes or chooses the largest remaining gap. The enum names describe intended alternatives; the pinned implementation provides an ascending coarse search and a finer BEST_FIT path.

This distinction matters in design-space exploration. A strategy label should correspond to an observable placement policy. Fragmentation-sensitive tests need exact value sizes, lifetimes, gap layouts, offsets, and rejection behavior—not only a successful return.

### Disabling spilling does not make capacity fail closed

Two interfering 16-byte W values under a 16-byte capacity cannot both occupy legal disjoint ranges. With spilling disabled, the second unplaced value is forced to offset zero:

```text
LIVE_NO_SPILL offsets=0,0 colored=1 spills=0
```

The graph is then reported colored. This combines a capacity miss, physical alias, and local success state.

A no-spill production policy should reject allocation and return a structured explanation: region, required size, available capacity, conflicting values, and perhaps a minimum extra-capacity estimate. Rejection preserves semantics; silent aliasing does not.

### Peak fields are summaries, not occupancy proofs

`peak_w_usage`, `peak_a_usage`, and `peak_o_usage` track high-water offset-plus-size values with simplified reclamation. W usage is never reclaimed. A and O usage reset to zero whenever any corresponding non-spilled value dies. These counters do not reconstruct simultaneous live occupancy and do not prove that every interfering pair is physically disjoint.

## 19.8 Spill accounting, rewriting, and output closure

### Spill statistics count events and can count one value twice

Victim selection skips already placed values. In a one-value case that cannot fit, the current unplaced value can be selected as its own victim and counted. Placement is retried without freeing any occupied range. When it still fails, the same value is marked and counted again:

```text
LIVE_SPILL_ACCOUNTING
  spilled=1 num_spills=2 spill_bytes=32 colored=0 offset=4294967295
```

One 16-byte value therefore produces two count events and 32 reported bytes. These fields are not counts of distinct values, transfer operations, or successfully preserved bytes.

### Synthetic DMA names do not provide a backing-store contract

A spilled VReg can retain `physical_offset=UINT32_MAX`. Synthetic fill/store helpers truncate offset and size to 16 bits. The bounded probe observes:

```text
OPS spill_sequence n=4
  ... DMA.LOAD dim0=65535 ... DMA.STORE dim0=65535 ...
```

A 65,536-byte value produces a synthetic size field of zero. The instruction carries no unique spill-slot or backing address. `TU_LIVE_MAX_SPILL_SLOTS` is declared, but the allocator does not assign and encode distinct slots.

The apply loop inserts a fill before every instruction strictly after the definition through `last_use`, whether or not that instruction reads the value. It retains the original defining instruction and emits a store after the last use. This is not a conventional save-before-eviction and reload-before-use protocol.

A complete spill contract needs:

- a unique backing location and lifetime;
- a physical SRAM destination for each reload;
- a save point after the value is produced and before its SRAM bytes are overwritten;
- reloads only where demanded by use and residency state;
- dependency edges and completion/error propagation;
- checked field widths or a richer descriptor;
- accounting derived from actual inserted transfers.

Chapter 10 remains authoritative for real DMA descriptor ownership and transfer lifecycle. A shared opcode name cannot import that contract.

### Operand rewriting can select a different value

The patcher rewrites selected DMA loads, selected O-producing forms, and selected MMA fields. Other opcodes recognized during definition/use extraction are not necessarily patched.

For MMA reads, the patch loop scans every VReg whose interval contains the instruction. It does not compare the original virtual range. Each matching W or A record overwrites the field, so a later same-region VReg can win. The retained manual-offset case records:

```text
OPS wrong_value_patch ...
  MMA dim0=128 ...
```

The MMA's W field is rewritten to the newest disjoint value rather than the original range's value. This is the rewrite manifestation of the earlier identity error.

### Low-level result provenance is unchecked

`tu_live_apply()` accepts an analysis result and a separate instruction array. It does not prove that they came from the same input. An analysis of one DMA load can be applied to an unrelated RELU sequence:

```text
LIVE_PROVENANCE rc=0 valid=1 opcode=RELU dim0=77
```

Likewise, scheduler validation accepts caller-provided graph and result objects without a common-origin token. Robust low-level APIs can bind results to an immutable input hash, sequence ID, generation, or opaque analysis object whose internals cannot be paired arbitrarily.

### Fixed output capacity can drop an input suffix

The allocated output has room for `2 * TU_SCHED_MAX_INSTRS`, or 512 instructions. The apply loop stops when that capacity is reached and then unconditionally sets `output.valid=true`.

A 301-instruction case with repeated fills reaches the cap before the final input store:

```text
LIVE_OUTPUT_LIMIT input=301 rc=0 valid=1 output=512 last_opcode=NOP
```

The input suffix is omitted. Output closure should instead precompute or incrementally check required capacity, return the needed size, and reject without authorizing a partial sequence.

## 19.9 Worked reproducible authorization ledger

Consider this conceptual three-instruction sequence:

```text
0: DMA_LOAD W[0:16)
1: DMA_LOAD W[100:116)
2: MMA reads W[0:2), reads A, writes O
```

A relation-by-relation ledger prevents one local pass result from hiding another failure:

| Gate | Scheduler observation | Allocator observation | Authorization |
|---|---|---|---|
| representation | fields are decoded by scheduler-specific formulas | fields are decoded by allocator-specific formulas | not globally authorized |
| dependence | scheduler may construct a W relation from its ranges | allocator does not consume scheduler graph | separate only |
| order | policy emits an order over retained edges | allocator accepts caller order | only scheduler-local |
| validation | near-duplicate identity omits fields | no scheduler-validation input is required | incomplete |
| value | not represented as VReg identity | MMA W use attaches to newest same-region definition | rejected |
| interference | not a scheduler output | graph is consistent with the wrong VReg binding | insufficient |
| capacity | not checked | placement can proceed | insufficient |
| rewrite | scheduler copies instructions | MMA field can be rewritten to wrong W offset | rejected |
| closure | scheduler count may match graph count | allocator can report valid | neither repairs value identity |

The transferable lesson is not that every static transform must use one representation. It is that each representation boundary needs a checked relation and a provenance-preserving handoff.

## 19.10 Architecture alternatives and multi-objective trade-offs

There is no universally best scheduler or scratchpad allocator. The right choice depends on the intended fidelity, workload, memory size, compiler budget, and runtime contract.

| Direction | Performance and traffic | SRAM / area / power | Compiler and runtime cost | Verification burden | Best-fit regime |
|---|---|---|---|---|---|
| preserve source order | gives up ready-node reordering and some overlap opportunities | may lengthen live ranges and raise peak SRAM | minimal scheduler complexity | smallest ordering state space | functional model or early bring-up |
| fixed-edge conservative list scheduling | bounded compile time; may serialize dense graphs | fixed graph storage | simple deterministic implementation | must reject overflow and validate exact bijection | small static windows with known edge bounds |
| dynamic complete dependence graph | more scheduling freedom on dense workloads | host memory grows with edges; no modeled hardware area unless lowered | dynamic allocation and richer diagnostics | complete-edge and cycle tests, deterministic tie rules | compiler studies where schedule quality matters |
| range/value-aware scheduling IR | can remove false dependencies and improve overlap | metadata grows with values, aliases, and subranges | requires canonical operand semantics | differential semantics and alias corpus | mature compiler frontend with stable value IDs |
| no-spill allocation with rejection | avoids spill traffic and backing-state complexity | may require larger SRAM or smaller tiles | clear failure path; compiler must retile/recompute | comparatively simple capacity proof | predictable accelerators and bounded models |
| explicit backing-store spilling | supports workloads above SRAM capacity at traffic cost | can reduce SRAM size but adds DMA/control activity | slot assignment, residency, dependencies, recovery | save/reload semantic oracle and fault cases | constrained SRAM with a real DMA/runtime bridge |
| live-range splitting / rematerialization | may reduce long-lived occupancy and transfer bytes | trades storage for recomputation | substantially richer compiler | value-version and recomputation equivalence | compute-cheap, bandwidth-limited workloads |
| larger or partitioned scratchpads | reduces allocation pressure and spills | increases area, leakage, banking, and access cost | simpler allocation but layout constraints remain | bank/port/fragmentation validation | workloads with stable large resident tiles |
| interval/SSA allocator with stable IDs | precise binding and auditable provenance | more metadata, not necessarily modeled hardware | frontend must provide definitions and uses | strongest compiler proof obligations | production compiler path |
| current ABI-local array as analysis-only surface | fast experimentation and easy C tests | no added modeled hardware | no deployment artifact | must preserve strict non-integration wording | architecture exploration, not deployment |

The table deliberately preserves materially distinct choices. A larger scratchpad can simplify compilation but cost area and leakage. Spilling can reduce minimum capacity but add traffic, latency, control state, and failure modes. Conservative order can reduce proof risk while increasing live ranges. More precise analysis can improve placement and overlap while expanding compiler and validation complexity.

## 19.11 Verification evidence and canonical authority

The sole predraft authority is:

```text
experiments/runs/ch19-static-transforms/20260810-ch19-postreview-v3/
```

It binds input commit:

```text
8d2e459257a6b340ad98f66c82a396a430d69441
```

and source pin:

```text
e918c80b6fce833cd1fcae97730fa841c2176f25
```

The source audit reports:

```text
CH19_SOURCE_AUDIT PASS
  hashes=24 predicates=158 checks=182
```

The bundle retains:

- wrong-pin and changed-copied-source rejection followed by restored-source recovery;
- exact archive membership and direct focused-binary linkage evidence;
- focused scheduler `14/14` and liveness `12/12`;
- the scheduler sweep as a non-authoritative report;
- a zero-failure static-transform probe with 128 numeric-opcode rows;
- bounded scheduler and liveness signed-arithmetic diagnostics;
- five transform/test negative controls;
- validator self-check controls under normal and optimized Python;
- exact input-to-commit comparison;
- a 46-entry body manifest and five-entry outer bundle manifest;
- finalization binding and exact run inventory;
- final validation under normal and optimized Python.

To verify the retained bundle:

```bash
cd /home/zxy/Workplace/books/tusim-book
CH19_RUN_ID=20260810-ch19-postreview-v3 \
CH19_VALIDATION_STAGE=final \
python3 experiments/ch19_predraft_validate.py

CH19_RUN_ID=20260810-ch19-postreview-v3 \
CH19_VALIDATION_STAGE=final \
python3 -O experiments/ch19_predraft_validate.py
```

The validator prints `PASS` only for the exact manifests, finalization binding, expected probe rows, exact closure inventory, and the committed input set. The failed and superseded runs remain retained as audit history; they are not drafting authorities.

## 19.12 Common failure modes and safety boundaries

1. **Shared type means shared semantics.** Scheduler and allocator can disagree on the same fields.
2. **Graph built means intended graph complete.** Edge arrays can truncate before `built=true`.
3. **Barrier name means complete fence.** Scheduler barriers constrain retained predecessors but not every later node.
4. **Hoist or insertion count means transformation.** The named helpers count candidates and emit nothing.
5. **Cycle number means performance.** The scheduler total is a fixed serial source sum.
6. **Validation means equivalence.** Identity is incomplete, unmatched nodes are skipped, and provenance is absent.
7. **Interval graph means correct liveness.** Interference can be exact for values that were constructed incorrectly.
8. **No spilling means safe allocation.** The current no-spill branch can force overlapping offset-zero placement.
9. **Spill count means transferred values or bytes.** One value can be counted twice without a backing slot.
10. **Synthetic DMA means executable transfer.** Descriptor ownership, backing location, dependencies, and runtime consumption are absent.
11. **Peak below capacity means legal placement.** Peak fields are simplified summaries, not pairwise overlap proofs.
12. **Output valid means output complete.** The fixed output array can omit a suffix and still report valid.
13. **Documentation diagram means integration.** A repository caller and effect-level test are required.
14. **Allocator liveness means runtime LIVE retention.** Chapter 18 uses a different representation and has no bridge.

The executable probes are bounded. They avoid uncontrolled memory access and do not require a failure to become a process crash. Source evidence is sufficient for unchecked allocation, ownership, and width boundaries that do not have a safe deterministic executable fixture.

## 19.13 Fidelity box

**Executable at the pinned revision**

- scheduler and liveness public C APIs;
- scheduler DAG construction, mobility, list scheduling, validation, and candidate counts;
- liveness VReg construction, interference, coloring, application, and convenience wrapper;
- focused suites and the exact bounded Chapter 19 probes.

**Executable local composition**

- each transform's own public convenience wrapper;
- direct archive linkage and focused execution in the canonical evidence runner.

**Representation adjacency only**

- shared use of ABI-local `tu_instruction_t` objects, without a verified pass-to-pass semantic handoff.

**Analytical or estimated**

- scheduler fixed-cost totals;
- policy-sweep rows;
- allocator peak-usage summaries;
- any inferred overlap, utilization, traffic reduction, or schedule-quality benefit.

**Not established**

- ONNX/ASM-to-scheduler-to-allocator-to-runtime integration;
- an external production/runtime caller for either pass or a scheduler-to-allocator call bridge;
- portable binary encoding or decoder;
- semantic equivalence between original and transformed sequences;
- runtime execution of synthetic spill/fill operations;
- calibrated latency, throughput, bandwidth, energy, or area;
- compiler-generated Chapter 18 LIVE-prefix values;
- complete memory effects for all numeric opcodes.

**Known snapshot boundaries**

- finite dependency edges can be silently omitted;
- barriers do not order all later operations;
- named hoist/barrier helpers are count-only;
- validation identity and provenance are incomplete;
- range-insensitive use binding can select a disjoint value;
- VReg overflow returns a truncated success;
- repeated interference construction duplicates graph membership;
- capacity subtraction can underflow;
- no-spill placement can alias at zero;
- invalid enums are accepted through default branches;
- one spilled value can be counted twice;
- synthetic offsets/sizes truncate and lack backing identity;
- operand rewriting is partial and range-insensitive;
- output truncation can still report valid.

## Development questions

1. Should instructions carry stable value IDs, or should a separate SSA/memory-SSA IR precede packing?
2. Should dependency overflow reject, allocate dynamically, split windows, or conservatively serialize?
3. What exact before/after relation should scheduler barriers enforce?
4. Should policy and placement enums reject every out-of-range value at API entry?
5. How should scheduler results and allocator analyses bind to their originating sequence?
6. Is no-spill allocation failure a compile error, a retiling request, or a request for a different architecture configuration?
7. What backing-store descriptor and ownership model should a spill slot use?
8. Which opcodes form the first bounded subset with an independent semantic oracle?
9. What measurements or RTL traces could calibrate schedule costs without conflating queue and engine time domains?
10. Can a future compiler prove Chapter 18 live-prefix requirements, or is a richer interval/dirty representation required?

## Summary

Tusim's scheduler and scratchpad allocator are executable standalone static transforms, not an integrated deployment pipeline. They share a C object but not a verified cross-pass operand contract.

The scheduler constructs range-based dependencies, chooses among ready nodes, and reports a serial fixed-cost total. Its finite edge arrays can weaken the graph, later work can cross barriers, named hoist/barrier helpers count without transforming, and validation lacks complete identity, bijection, and provenance.

The allocator constructs virtual values, inclusive intervals, interference graphs, offsets, and rewritten output. Its use binding ignores byte ranges; VReg overflow truncates; repeated graph building accumulates state; capacity arithmetic can underflow; no-spill placement can alias; spill accounting can count one value twice; synthetic DMA lacks backing identity; operand rewriting can select a disjoint value; and output capacity can omit a suffix while reporting valid.

The transferable method is relation-by-relation authorization. Representation, dependence, order, value, capacity, placement, rewrite, and closure need independent evidence. This method supports realistic alternatives instead of forcing one design: conservative order, complete dynamic graphs, range-aware value IRs, explicit no-spill rejection, true backing-store spilling, live-range splitting, and larger scratchpads each serve different regimes and carry different performance, area/power, software, and verification costs.

## Review questions

1. Why does sharing `tu_instruction_t` not establish scheduler-to-allocator compatibility?
2. How can `graph->built=true` coexist with a missing intended dependency?
3. Why can a later DMA load cross a scheduler barrier?
4. Why do different policies produce the same estimated cycle sum in the two-node example?
5. What is incomplete about `tu_sched_validate()` identity and mapping?
6. Why can a correct interval-overlap calculation still describe incorrect liveness?
7. What happens when the safety margin exceeds unsigned region capacity?
8. Why is one `spilled` VReg reported as two spills and 32 bytes in the 16-byte example?
9. Why do synthetic DMA opcodes not establish a legal backing-store protocol?
10. Which checks must run before `output.valid=true` can authorize an allocated sequence?

### Review-question answer key

1. The passes use different opcode/field formulas, have no composed caller, and lack a shared semantic handoff contract.
2. The fixed predecessor/successor arrays silently skip edges at 16; the builder then marks the retained graph built.
3. The barrier receives prior predecessors, but later ordinary nodes receive no barrier predecessor solely from source position.
4. The implementation sums one per DMA node and four per other emitted node; order does not change the multiset.
5. Matching omits `dim2` and immediates, unmatched nodes are skipped, mapping need not be bijective, and graph/result provenance is unchecked.
6. Uses can bind to the newest same-region definition while ignoring byte range; the graph is then exact for the wrong values.
7. Unsigned subtraction wraps to a large apparent effective capacity unless `margin <= capacity` is checked first.
8. The current unplaced value can be selected and counted as its own victim, then counted again after the retry fails.
9. They lack backing address/slot identity, dependency and completion contracts, checked widths, and a runtime consumer.
10. Common representation semantics, complete intended dependencies, a legal order with bijective validation, correct reaching definitions, complete interference, checked capacity and widths, disjoint physical placement, complete operand and inserted-operation rewriting, analysis/input provenance binding, and exact output closure with no suffix loss.

## Design exercises

1. **Stable origin IDs.** Extend scheduler nodes and emitted instructions with an origin relation that supports duplicate opcodes and operands. Specify bijection checks.
2. **Dense graph policy.** Compare rejection, dynamic edges, generation barriers, and conservative window serialization for a node with 64 dependencies.
3. **Barrier contract.** Define separate ordering contracts for prior issue, prior completion, SRAM visibility, and host visibility. Identify which belong in a static scheduler.
4. **Range-aware values.** Design VReg identity for exact ranges, partial overlaps, redefinitions, and implicit inputs.
5. **Fail-closed allocation.** Define a structured error for capacity, enum, width, and output-size failures. Make partial outputs unobservable.
6. **Fragmentation corpus.** Construct values and intervals that produce different legal placements under true first-fit, best-fit, and worst-fit policies.
7. **Backing-store spills.** Design a slot allocator, save/reload placement, residency state, and exact byte accounting for two simultaneously spilled values.
8. **Semantic subset.** Choose a small set of operations with an independent interpreter. Differentially execute original and transformed sequences.
9. **Cost calibration.** Propose an RTL or hardware trace that separates dependency-ready time, issue, service, completion, and data movement.
10. **Runtime retention bridge.** State the proof required to convert compiler value liveness into Chapter 18 W/A/O retention extents.

### Exercise answer sketches

1. Store an immutable origin ID outside ambiguous packed operands, require each input origin exactly once in output unless a documented expansion relation applies, and reject duplicates/missing origins.
2. Rejection is simplest and safest; dynamic edges preserve freedom with host-memory cost; generations compress all-prior relations; serialization reduces proof and schedule quality.
3. Static scheduling can establish relative instruction order. Completion and visibility require runtime/engine contracts and cannot be inferred from array position alone.
4. Use versioned region/range definitions, split partial overlaps, make implicit inputs explicit parameters, and bind each use to one reaching definition or a defined merge.
5. Validate before mutation, compute required output size, stage assignments in temporary storage, and publish only after every relation succeeds.
6. Use unequal sizes, non-overlapping lifetimes, and holes whose smallest fitting gap differs from the lowest and largest gaps; compare exact offsets and remaining gaps.
7. Give each value a unique slot and generation, save after definition before eviction, reload before actual use, track residency, and derive bytes from emitted descriptors.
8. NOP, bounded DMA-to-local-array operations, and one elementwise operation can form a start if operand semantics and memory ownership are explicit.
9. Timestamp admission, dependency-ready, issue, service start/end, visibility, and completion separately; compare distributions and error rather than one total.
10. Prove value-to-byte layout, legal suspension point, dead-tail or reload behavior, dynamic-shape bounds, alias handling, shared-state drainage, and runtime ownership.

## Primary references

- [BAN02](../../references/foundations.md#ban02-scratchpad-memory) Banakar et al., “Scratchpad Memory: A Design Alternative for Cache On-Chip Memory in Embedded Systems,” 2002, [DOI 10.1109/CODES.2002.1003604](https://doi.org/10.1109/CODES.2002.1003604). Software-managed storage motivates explicit placement and compiler responsibility; its old-node quantitative results are not transferred here.
- [SHA14](../../references/foundations.md#sha14-aladdin) Shao et al., “Aladdin: A Pre-RTL, Power-Performance Accelerator Simulator Enabling Large Design Space Exploration of Customized Architectures,” 2014, [DOI 10.1109/ISCA.2014.6853196](https://doi.org/10.1109/ISCA.2014.6853196). Dependence/resource models motivate static analysis but do not validate Tusim automatically.
- [TOM67](../../references/foundations.md#tom67-dependency-driven-scheduling) Tomasulo, “An Efficient Algorithm for Exploiting Multiple Arithmetic Units,” 1967, [DOI 10.1147/rd.111.0025](https://doi.org/10.1147/rd.111.0025). Operand readiness illustrates that dependence satisfaction and issue are separate from completion and retirement; Tusim is not claimed to implement Tomasulo scheduling.
- [CHE18](../../references/foundations.md#che18-tvm) Chen et al., “TVM: An Automated End-to-End Optimizing Compiler for Deep Learning,” 2018. End-to-end compilation provides a contrast: graph transformations, scheduling, code generation, and runtime integration require explicit connected contracts.
- [GEN21](../../references/foundations.md#gen21-gemmini) Genc et al., “Gemmini: Enabling Systematic Deep-Learning Architecture Evaluation via Full-Stack Integration,” 2021, [DOI 10.1109/DAC18074.2021.9586216](https://doi.org/10.1109/DAC18074.2021.9586216). Full-stack evidence is a useful comparison, not proof that Tusim's currently uncomposed passes form such a stack.

Full verified metadata and conservative safe-use scopes are maintained in [`../../references/foundations.md`](../../references/foundations.md).
