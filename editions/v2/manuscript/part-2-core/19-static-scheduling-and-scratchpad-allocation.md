# Chapter 19 — Static Scheduling and Scratchpad Allocation

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-19)

A static transform is easy to recognize by its shape: take an instruction array, analyze it, and return another instruction array. That shape is not a correctness proof. A legal transform needs a chain of relations that agree on operand meaning, dependence, value identity, storage capacity, physical placement, and output completeness.

This chapter asks one practical question:

> Given an in-process `tu_instruction_t` sequence, what evidence is required before a scheduler-produced order or allocator-produced rewrite may be treated as a legal program rather than a structurally plausible array of C objects?

**Historical case study (August 10, 2026).** At the July 25 Tusim source pin `e918c80`, the scheduler and liveness allocator are real, executable C components. Both belong to `libtucmodel.a`; their focused suites report `14/14` and `12/12`. They also share the packed `tu_instruction_t` representation. These facts establish two standalone static transforms. They do **not** establish an ONNX-to-scheduler-to-allocator-to-runtime pipeline, a portable binary encoding, or semantic equivalence between input and output.

The focused totals and rewrite observations were not retested at `7a094ff`. Iterator-to-DMA bounds do not prove a compiler rewrite legal or create a runtime bridge.

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

$$
I = (i_0, i_1, \ldots, i_{n-1}),
$$

and let a static transform return

$$
T(I) = (i'_0, i'_1, \ldots, i'_{m-1}).
$$

A useful authorization model is:

$$
\operatorname{Legal}(T(I)) =
R_{\text{repr}}
\land R_{\text{dep}}
\land R_{\text{order}}
\land R_{\text{value}}
\land R_{\text{capacity}}
\land R_{\text{placement}}
\land R_{\text{rewrite}}
\land R_{\text{closure}}.
$$

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

A scheduler commonly constructs a directed acyclic graph $G=(V,E)$, where each instruction is a node and each required precedence relation is an edge. A list scheduler repeatedly selects a ready node whose predecessors have all been emitted. A policy changes the choice among ready nodes; it must not weaken $E$.

Tusim tracks W/A/O read and write ranges. Two half-open byte ranges overlap when

$$
[a_0,a_1) \cap [b_0,b_1) \neq \varnothing
\quad\Longleftrightarrow\quad
 a_0 < b_1 \land b_0 < a_1.
$$

That test is only as meaningful as the operand-to-range mapping that produced the endpoints.

### Liveness and interference

For a virtual value $v$, the allocator records a definition index and a final-use index. Its implementation treats two non-implicit values as interfering when their inclusive instruction intervals overlap:

$$
[d_i,u_i] \cap [d_j,u_j] \neq \varnothing.
$$

Interference then constrains physical placement. If value $i$ is assigned byte interval $[p_i,p_i+s_i)$, every interfering pair must satisfy:

$$
[p_i,p_i+s_i) \cap [p_j,p_j+s_j) = \varnothing.
$$

Correct graph coloring cannot repair a use that was attached to the wrong definition. Value identity precedes interference.

### Capacity and rewriting

For region $r$, Tusim computes an effective capacity as

$$
C_{\text{eff},r}=C_r-M,
$$

where $M$ is a shared safety margin. In unsigned arithmetic this equation is valid only after proving $M\le C_r$. Placement also needs width checks for every range-end addition and every field used to encode a rewritten offset or size.

A spill transform adds a stronger obligation. It must define backing-store identity, save timing, reload timing, and which uses consume the reloaded value. Merely inserting instructions named `DMA_LOAD` and `DMA_STORE` does not supply those contracts.

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

[Next: Chapter 20 — Verification as an Architectural Feature](20-verification-as-an-architectural-feature.md)
