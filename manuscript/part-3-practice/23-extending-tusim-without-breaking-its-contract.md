# Chapter 23 — Extending Tusim Without Breaking Its Contract

Adding a field, enum, source file, plug-in, test, or binding method is easy to mistake for extending a system. Each artifact can be real while the promised behavior remains unreachable. A parser can retain a value that runtime conversion drops. A registered plug-in can work through a direct API while configuration still selects the default. An ISA catalog can grow far beyond the command queue that executes it. A source file and focused test can remain outside the production archive. Documentation can name a mode that silently falls back to another implementation.

This chapter asks one architecture question:

> Given a proposed extension, what contract is being promised, and which weakest missing edge prevents calling it integrated?

At Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25`, seven extension families make that question concrete: runtime configuration, dataflow/plugin selection, ISA/command queue, cycle-model module, dataflow sweep, Python binding, and compiler/runtime/ONNX. The final predraft authority is `results/ch23-predraft/20260819T084945Z-postreview`; its retained-manifest SHA-256 is `598ec9ace364d75be687c255526ddb49c7158bd2043741b94a19806a33da1fb9`. The bundle seals 34 exact-pin source, test, build, documentation, and model input hashes, an exact 19-member non-symlink closure, normal and optimized validation, and 13 mutation families.

The chapter's rule is deliberately strict:

```text
declaration and identity
  → ingress
  → retention and ownership
  → production consumption
  → observable effect
  → discriminating verification
  → build and release ownership
  → documentation that matches behavior
```

An integrated claim is a conjunction. A missing required edge cannot be compensated for by extra documentation, more enum members, a larger test count, or a stronger adjective. The weakest edge sets the strongest defensible classification.

## Learning objectives

After completing this chapter, the reader should be able to:

1. state an extension as a promised behavioral contract rather than a code edit;
2. trace declaration/identity, ingress, retention with lifetime/ownership, production consumption/dispatch, observable effect, fail-closed verification, build/CI/package/release ownership, and behavior-matching documentation as eight separate edges;
3. distinguish integrated, partial/qualified, standalone, and no-op/fallback extension states;
4. identify the weakest missing edge without turning readiness into a weighted score;
5. distinguish direct-API reachability from configuration reachability;
6. reason about registry duplicate, overflow, and lifetime behavior precisely;
7. separate ISA declaration, metadata, static analysis, queue dispatch, and observed execution;
8. distinguish source/test presence from library linkage and production callers;
9. require a sweep label to reach the intended mechanism and propagate mismatches to process status;
10. require bindings to consume their advertised inputs and own packaged verification;
11. preserve a negative compiler/runtime/ONNX boundary until compile, link, run, and independent-oracle stages all fail closed; and
12. design promotion experiments that name the missing producer, observable, status path, and owner.

## Prerequisite graph

```text
Chapter 4: declaration → parser → runtime conversion → consumer
Chapter 7: dataflow registry, direct selectors, and active routes
Chapter 11: ISA metadata, command queue, and scheduler boundary
Chapter 17: producer, interval, units, state, and fidelity
Chapter 19: scheduler/liveness as adjacent static transforms
Chapter 20: claim boundary, controls, status, and provenance
Chapter 21: effective sweep axes and fail-closed experiments
Chapter 22: evidence-filtered architecture hypotheses
                              │
                              ▼
Chapter 23: extension contract and weakest missing edge
```

Chapter 4 remains authoritative for the existing configuration surface. Chapter 7 owns dataflow semantics. Chapter 11 owns the command queue and ISA lifecycle. Chapters 17 and 20 define metric provenance and evidence authority. Chapter 21 owns sweep construction; Chapter 22 remains closed and owns portfolio synthesis. This chapter does not reopen any of them. It asks how a future change crosses their established boundaries without inventing a bridge.

## Opening architecture question

Suppose a developer proposes four changes:

- add a `no_local_reuse` enum value;
- parse `pipeline_depth` from JSON;
- add a cycle-model source file and unit test;
- expose `config_path` in Python.

All four changes can compile. All four can appear in documentation. None is thereby integrated.

For each proposal, the architect should ask:

- What identity is stable, and can aliases collide?
- Which user or producer supplies the value?
- Which object retains it, for how long, and who owns cleanup?
- Which production call consumes it?
- What discriminating effect proves that the intended mechanism ran?
- Can the test fail for a realistic wrong implementation?
- Which build, aggregate, CI, package, or release target owns it?
- Does documentation describe observed behavior, including fallbacks and omissions?

These questions prevent two opposite errors. The first is **promotion by presence**: calling a declaration or source file integrated. The second is **demotion by adjacency**: overlooking a valid direct route merely because a different ingress is broken. Tusim's WS/OS/RS plug-ins illustrate both. Their direct API and production consumers are real; their JSON selection path is not. A precise extension review preserves both facts.

---

## 23.1 Theory: extension readiness is a conjunctive contract

Let an extension claim be \(E\). Define eight relations:

- \(D\): the declaration and identity are unambiguous;
- \(I\): a named ingress accepts or creates the extension;
- \(R\): state is retained with explicit lifetime and ownership;
- \(C\): a production consumer or dispatcher reaches it;
- \(O\): a discriminating observable changes as promised;
- \(V\): verification reaches the route, compares an adequate oracle or invariant, and fails closed;
- \(B\): build, aggregate, CI, packaging, and release ownership are explicit; and
- \(M\): documentation matches the live behavior and limitations.

Then an integrated claim requires

\[
\operatorname{Integrated}(E)=D\land I\land R\land C\land O\land V\land B\land M.
\]

The equation is a review discipline, not an API supplied by Tusim. It does not imply that every extension needs the same implementation shape. A compile-time module may not need a runtime parser. A direct C API may not need JSON. A report generator may not belong in the production archive. The card must first name the promised contract; only then can it decide which edges are required.

### Four extension states

This chapter uses four states.

**Integrated** means every edge required by the stated promise is present and the evidence is discriminating. It is scoped: “direct-API integrated for WS/OS/RS” is meaningful, while “the dataflow system is integrated” hides the broken config route and unsupported NLR ID.

**Partial/qualified** means a real path exists but one required edge is red, ambiguous, or narrower than the advertisement. The safe narrower statement must be explicit. Runtime geometry reaches the runtime structure, but unresolved layout-sensitive verification prevents promotion of the whole advertised path.

**Standalone** means a source, API, test, or harness works in isolation but lacks production reachability or release ownership promised by a broader claim. Standalone is not an insult. It can be the correct design for an analytical tool, provided its documentation does not imply runtime integration.

**No-op/fallback** means ingress appears to accept a request but the intended behavior is dropped, overwritten, stubbed, or silently replaced. Success status is especially dangerous here because it can make unsupported behavior look integrated.

A blocked claim is not a fifth implementation state. It is an evidence disposition: current evidence forbids the positive statement.

### The weakest-edge promotion rule

The weakest edge is not necessarily the earliest edge. A path may parse, retain, dispatch, and print a result while verification remains non-discriminating. Another may pass a focused test but have no production consumer. A third may execute correctly through a direct API while documentation overstates configuration support.

Promotion therefore follows this order:

1. state the exact promise;
2. mark which edges that promise requires;
3. record positive and negative evidence per edge;
4. classify the current path at its weakest required edge;
5. name one minimum promotion experiment;
6. refuse stronger wording until that experiment passes and is owned.

This is stronger than a maturity score. Scores allow one strong dimension to compensate for a missing safety or correctness edge. A conjunction does not.

## 23.2 Source map and evidence layers

The seven retained families span different extension mechanisms. They should not be forced into one implementation template.

| Family | Declaration/ingress surface | Retention/consumer surface | Observable and ownership surface | Current classification |
|---|---|---|---|---|
| runtime configuration | `tu_config_t`, JSON/default parser | `tu_config_to_runtime()`, `tu_runtime_config_t`, initialization | focused config run and downstream structure/effect | partial/qualified for geometry; no-op/fallback for selected runtime-conversion fields |
| dataflow/plugin | enum, direct setter, config string | global registry pointer, core snapshot, dispatcher, vtable | output, active name, plug-in statistics, linked objects/tests | integrated for direct WS/OS/RS; no-op/fallback for config ingress and NLR/unknown selection |
| ISA/command queue | explicit opcode enum, aliases, metadata | submitted command descriptor and `execute_command()` | eight source dispatch cases, queue status/tests | partial/qualified bounded queue; tested subset only; unsupported aliases fault rather than fall back |
| cycle-model module | source/header/API | isolated caller-created object | focused source exists; no archive member, Make rule, or production caller | standalone source island |
| dataflow sweep | fixed workload/seed and WS/OS/RS labels | core-wrapper calls plus local formulas | printed rows, dedicated target, exploration prose | standalone and fail-open; effective WS/WS/WS routes |
| Python binding | Python constructor and ctypes signatures | Python `_config_path`, C library handle, direct operations | identity GEMM, stub reports, no Make/CI owner | standalone bounded direct ctypes route; no-op/fallback constructor config/report promises; supported-package promise partial/qualified |
| compiler/runtime/ONNX | two contained models and generator | generated C and host fallbacks | suppressed build/run statuses; no far-boundary oracle | standalone generator/model components; no-op/fallback `test-full` failure handling; positive composition claim remains ledger-blocked |

The claim ledger [`notes/chapter-23-source-claim-ledger.md`](../../notes/chapter-23-source-claim-ledger.md) assigns IDs `C23-01` through `C23-17`. The framing plan, independent review, and reconciliation are bound into the immutable postreview authority. The source evidence remains pinned to the edition commit. Documentation is treated as a claim source to compare against behavior, never as behavioral proof.

The evidence order matters:

1. exact-pin reproduced behavior;
2. focused tests and discriminating probes;
3. production caller and build reachability;
4. headers and declared contracts;
5. current documentation;
6. historical intent.

A lower layer can propose a contract. It cannot override contradictory higher-layer behavior.

## 23.3 How to use an extension contract card

Each worked family uses the same card:

| Field | Question |
|---|---|
| Promised contract | What exact user-visible or developer-visible behavior is claimed? |
| Current classification | Integrated, partial/qualified, standalone, or no-op/fallback? |
| Exact claim IDs | Which sealed ledger rows authorize the statement? |
| Weakest required edge | Which missing or red relation blocks promotion? |
| Positive evidence | What exact path or observable is live? |
| Stop evidence | What contradiction, omission, or status defect narrows the claim? |
| Alternatives and trade-offs | Which materially distinct implementation choices remain plausible? |
| Promotion trigger | What minimum new fail-closed evidence could strengthen the claim? |

The card separates **path truth** from **architecture choice**. The current source can establish that direct selection reaches a dispatcher. It cannot choose global versus per-core ownership for a future plug-in system. That choice must compare throughput or latency implications where applicable, memory and ownership cost, control complexity, compiler/runtime burden, verification surface, and model fidelity.

The promotion trigger should be executable and discriminating. “Add more tests” is not enough. “Set OS through JSON, prove the converted runtime state changes, execute a nonsymmetric workload through the intended core, observe active OS identity and an OS-specific linked-cycle delta, and require mismatch to return nonzero” names the route and the failure.

## 23.4 Contract card 1: runtime configuration

| Field | Chapter 23 result |
|---|---|
| Promised contract | A named JSON/default setting reaches the intended runtime consumer and changes a discriminating downstream observable. |
| Current classification | **Partial/qualified** for geometry; **no-op/fallback** at runtime conversion for the audited dataflow, pipeline-depth, and DMA-width requests. |
| Exact claim IDs | `C23-02`, `C23-03` |
| Weakest required edge | Verification for geometry; retention/conversion for the dropped fields. |
| Positive evidence | Geometry fields cross `tu_config_to_runtime()` into `tu_runtime_config_t` and reach initialization. |
| Stop evidence | Canonical `test-config` aborts with stack smashing; other independent layouts have passed. Dataflow, pipeline depth, and DMA width are parsed but omitted by conversion. |
| Alternatives and trade-offs | Extend the compact runtime struct; let specialized consumers read the full config; or remove/deprecate ineffective fields. |
| Promotion trigger | In fresh processes, run literal JSON A/B configs `{"tu":{"compute":{"pe_array":{"rows":8,"cols":16}}}}` and `{"tu":{"compute":{"pe_array":{"rows":16,"cols":16}}}}` on `M×N×K=17×16×16`, with zero-based `A[i,k]=((7i+3k+1) mod 11)-5` and `B[k,j]=((5k+2j+3) mod 13)-6`; require active geometries `8×16` and `16×16`, exact tile counts 3 and 2, outputs equal to an independent integer-loop oracle, and nonzero status if either geometry or tile receipt differs. |

The central distinction is between **parse acceptance** and **effective control**. The parser can validate a string or integer, store it in `tu_config_t`, and print it later. That proves ingress and perhaps retention in the full config object. It does not prove that `tu_config_to_runtime()` preserves it or that initialization consumes it.

Geometry supplies a positive path: selected dimensions reach the compact runtime configuration and initialization. Yet the sealed canonical focused run reports `rc=2`, a stack-smashing diagnostic, and an unresolved layout-sensitive result. One clean variant cannot erase the red sealing configuration. Conversely, the red result does not prove that conversion is absent. The exact safe statement is that propagation reaches runtime but full promotion remains qualified until root-cause resolution and a repeated discriminating matrix are green.

The dropped fields have a different weakest edge. Dataflow, pipeline depth, and DMA width parse but do not cross runtime conversion. Direct setters or compile-time defaults can still affect adjacent behavior. Therefore “the feature does not exist” would be too broad; “this configuration ingress does not make the named runtime behavior effective” is precise.

Three extension strategies remain plausible:

1. **Expand `tu_runtime_config_t`.** This creates one explicit conversion contract and enables generated propagation tests. It increases ABI/state surface and requires lifecycle/default compatibility.
2. **Pass the full config to specialized consumers.** This avoids duplicating every field in a compact structure but increases coupling and can create multiple authority paths.
3. **Delete or deprecate unsupported fields.** This narrows the promise and verification burden but sacrifices forward-looking configuration compatibility.

The right choice depends on ownership, not field count. Whichever route is chosen must reject or report unsupported values rather than accepting a documented no-op.

## 23.5 Contract card 2: dataflow plug-ins and registry ownership

| Field | Chapter 23 result |
|---|---|
| Promised contract | A requested dataflow identity reaches a retained implementation, production dispatcher, observable route, and owned lifecycle. |
| Current classification | **Integrated** for direct WS/OS/RS; **no-op/fallback** for config ingress and NLR/unknown selection, whose active route becomes WS while status remains success. |
| Exact claim IDs | `C23-04`, `C23-05`, `C23-06` |
| Weakest required edge | Config retention for JSON selection; implementation/build/registration for NLR; status and ownership contract for an open dynamic ABI. |
| Positive evidence | WS, OS, and RS are linked and registered; direct selection reaches `tu_mma()` and attention through `tu_dataflow_execute_mma()` and the selected vtable. |
| Stop evidence | Config conversion drops the mode; core snapshots can overwrite global selection; unregistered IDs fall back to WS while returning success. |
| Alternatives and trade-offs | Static built-ins, a checked global registry, per-core immutable plug-ins, or a versioned dynamic ABI. |
| Promotion trigger | Run three fresh `17×13×11` cores over zero-based `A[i,k]=((7i+3k+1) mod 11)-5`, `B[k,j]=((5k+2j+3) mod 13)-6`: direct WS baseline, direct OS, and literal JSON `{"tu":{"compute":{"pe_array":{"rows":16,"cols":16,"dataflow":"output_stationary"}}}}`; require active names `weight_stationary/output_stationary/output_stationary`, both OS vtable pointers equal `tu_dataflow_lookup(OS)` and differ from `tu_dataflow_lookup(WS)`, all outputs equal an independent integer-loop oracle, and an NLR request or any identity/vtable mismatch to return nonzero. |

This family demonstrates why scope matters. The direct route is real: three implementations are linked, registered, selected, and consumed at two production files and three dispatcher call sites. A statement that “dataflow selection never works” would discard valid evidence.

The JSON route is different. Parsing recognizes a mode, but conversion omits it. A core wrapper can also restore its snapshot after process-global selection. The requested label and active implementation can therefore diverge. The correct contract should expose both identities or make divergence impossible.

NLR is still earlier in the chain. It is declared and documented, but no constructor, linked object, registration, or focused implementation exists. Selecting NLR—or another unregistered ID—falls back to WS and returns success. This is not degraded NLR execution. It is successful execution of another mechanism under the requested label.

Ownership is equally specific. The registry has eight slots. Duplicate IDs keep the first pointer and free the new duplicate. Capacity overflow returns silently without freeing the submitted pointer or reporting status. Those are two different lifetime outcomes. Summarizing both as a generic “replacement hazard” would hide which object remains live and who leaks on overflow.

Materially distinct future designs include:

- **Static built-ins with closed IDs.** Small ownership surface and deterministic release contents, but no runtime extensibility.
- **Checked global registry.** Minimal dispatch overhead and simple lookup, but process-global lifetime complicates cores, contexts, concurrency, and replacement.
- **Per-core immutable plug-in table.** Stronger isolation and reproducibility, at the cost of larger snapshots and explicit construction.
- **Versioned dynamic ABI.** Maximum external extensibility, but requires symbol/version negotiation, error-returning registration, ownership transfer rules, unload safety, packaging, and much broader verification.

None is universally best. The current evidence supports a static built-in interpretation more strongly than an open dynamic ABI.

## 23.6 Contract card 3: ISA catalog and command-queue execution

| Field | Chapter 23 result |
|---|---|
| Promised contract | A declared operation has ingress, retained operands, dispatch semantics, observable effects, errors, and differential verification. |
| Current classification | **Partial/qualified** for bounded queue execution: eight source cases exist, but complete per-case behavioral evidence does not. Unsupported aliases such as pool are rejected/faulted (`tu_cmdq_wait()=-3`), not fallback execution. |
| Exact claim IDs | `C23-07`, `C23-08`, `C23-09` |
| Weakest required edge | Queue/runtime dispatch and per-case behavioral verification for most declared opcodes. |
| Positive evidence | The ISA header has 59 explicit assigned opcode members; queue source contains eight distinct `TU_CMD_*` dispatch cases, and the focused suite exercises a bounded subset. |
| Stop evidence | Aliases and metadata do not create queue cases. Unknown commands fault; scheduler/liveness are adjacent analysis consumers, not composed execution. |
| Alternatives and trade-offs | Keep separate metadata and queue vocabularies; define a checked lowering table; or create one versioned executable instruction contract. |
| Promotion trigger | First reconcile `tu_cmdq_submit()` to the explicit assigned-positive-ID contract implemented at this pin. Add `tu_cmd_pool_desc_t {input_offset,output_offset,input_h,input_w,channels,kernel_h,kernel_w,stride_h,stride_w,pool_type}` and a retained `pool` union member; on a fresh synchronous queue submit A-SRAM offset 0→O-SRAM offset 0, `3×4×1`, kernel `2×2`, stride `1×1`, `TU_POOL_MAX`, and `[[1,7,2,0],[3,4,9,5],[-1,6,8,2]]`. Require submit return = captured ID = 1, retained fields byte-equal the descriptor, pool-dispatch count 1, `wait(captured,0)=0`, captured status `TU_CMD_COMPLETED`, and output `[[7,9,9],[6,9,9]]`; replacing captured ID with reserved 0, removing retention/handler, or using `kernel_h=4>input_h=3` must make the governed process nonzero even if the underlying not-found wait/status APIs report completion. |

A declaration census answers only a declaration question. At the pin, the expanded ISA contains **59 explicit members**, while `execute_command()` contains **eight queue cases**: barrier, DMA load, DMA store, elementwise, halt, MMA, NOP, and sync. A pool alias, for example, does not manufacture a queue execution path.

Static-analysis consumption also has a distinct contract. Scheduler and liveness code can inspect adjacent metadata or instruction objects without producing a queue-executable program. Chapter 19 established that these analyses are uncomposed at this pin. Chapter 23 preserves that negative bridge rather than drawing an attractive but unsupported compiler arrow.

Three architecture choices remain:

1. **Separate vocabularies with explicit lowering.** Metadata can describe more operations than one runtime supports. This is flexible, but the lowering table and unsupported-result status become mandatory evidence.
2. **One executable enum.** Simpler consistency checks and fewer aliases, but it couples tools and runtime release cadence and can overconstrain analytical passes.
3. **Versioned descriptors/capabilities.** Producers query supported operations and operand schemas. This improves negotiation but adds compatibility, serialization, and negative-path testing.

The minimum unit of promotion is one operation, not the catalog. A good fixture uses nonsymmetric operands or state so the wrong handler cannot pass, checks observable output and lifecycle status, injects an unsupported or malformed case, and verifies that failure propagates.

The RISC-V specification is useful vocabulary for exact fields and scoped semantics, but it cannot fill Tusim's missing encoder, decoder, queue, visibility, or fence edges ([RISC-V unprivileged ISA](../../references/foundations.md#riscv26-risc-v-unprivileged-isa)). Likewise, OpenCL's queued/submitted/running/complete distinctions illuminate lifecycle questions without transferring OpenCL semantics to Tusim ([OpenCL command-queue contract](../../references/foundations.md#ocl311-opencl-command-queue-contract)).

## 23.7 Contract card 4: a cycle-model source island

| Field | Chapter 23 result |
|---|---|
| Promised contract | A cycle-model module contributes to ordinary production execution and its results are observable through an owned interface. |
| Current classification | Standalone source island. |
| Exact claim IDs | `C23-10` |
| Weakest required edge | Production build ownership and non-test caller reachability. |
| Positive evidence | `tu_cmodel/perf/cycle_model.[ch]` and a focused test source exist. |
| Stop evidence | The module is absent from `TU_OBJS`, has no Make rule, and exhaustive tracked C/H scanning finds no external non-test `tu_cycle_*` caller. |
| Alternatives and trade-offs | Keep it as an explicit standalone analytical tool; link it as an optional provider; or integrate it behind a production metric interface. |
| Promotion trigger | Link one production-owned caller to a tracker of capacity 4; call `tu_cycle_pipeline_issue()` at cycle 0 first with tile `(0,16,0,16,0,16)`, sources `{100,200}`, destination `{300}`, then with tile `(1,16,1,16,1,16)`, sources `{300,400}`, destination `{500}`; require stalls `0,96`, `total_issues=2`, `total_stall_cycles=96`, utilization `0.5`, reset to all zeros, and nonzero test status when the second source is mutated from 300 to 301 and the required 96-cycle RAW receipt disappears. |

This path is not a failed runtime plug-in. It may be a legitimate experiment whose contract is standalone. The defect appears only when source and test presence are used to imply library or workload integration.

A standalone analytical tool has advantages: low coupling, rapid experimentation, and no risk of silently changing ordinary runtime estimates. Its costs are duplicated state, weaker discoverability, and no evidence that ordinary operations exercise it. Linking it optionally can preserve separation while making packaging explicit. Full integration can give one consumer path, but it risks creating another incompatible cycle dialect unless Chapter 17's producer, interval, units, reset, and fidelity contract is adopted.

A new Make target alone would improve ownership but would not close production reachability. A new caller alone could still leave release packaging accidental. Both edges, plus a discriminating integration test, are required for the broader promise.

## 23.8 Contract card 5: a sweep as an extension surface

| Field | Chapter 23 result |
|---|---|
| Promised contract | Labeled alternatives reach distinct mechanisms, rows use owned producers, and mismatches fail the governed process. |
| Current classification | Standalone non-aggregate harness with fail-open mismatch semantics. |
| Exact claim IDs | `C23-17` |
| Weakest required edge | Effective mechanism routing and status propagation. |
| Positive evidence | A dedicated Make target runs a fixed workload and seed and prints WS/OS/RS comparisons documented by an exploration report. |
| Stop evidence | Core snapshot restoration makes the three labeled executions effectively WS/WS/WS; local formulas are separate producers; mismatch text does not change exit status. |
| Alternatives and trade-offs | Repair the existing C harness; split functional route and analytical formula tools; or generate a manifest-driven governed experiment. |
| Promotion trigger | Run fresh WS, OS, and RS cores at default `16×16` on `128×128×256`. Generate row-major W then A with separate unsigned-32 states seeded 42 and 99: emit the post-transition state after `x^=x<<13; x^=x>>17; x^=x<<5`, masking to 32 bits after each left shift; map `q=(x&2047)-1024` to exact binary16 `q/1024` using round-to-nearest, ties-to-even and store little-endian. The first W/A words are `00ad4528,a90a34ac,1c67af03,d970c3c0` / `01806cc5,8f0193e9,12e147b7,78e0ed3c`; require W/A byte hashes `0b322defeb00b00648e0e1523df10566b5835684bdadc47b332d1a3130dce359` / `9efef3fcb57e9f8a888f8fe40c74205c1266a43d0cdf9567d1642749220a11bc`. Require active names `weight_stationary/output_stationary/row_stationary`, selected vtable pointers equal their lookups and pairwise differ, every output to match an independent exact-integer-sum oracle rounded once to little-endian binary32 whose hash is `164c2afd507482c03584910fcabe08d32b99ca920561dfc89dc7baa013c8e0fe`, retained raw rows, and nonzero status for any WS restoration or hash/identity/oracle mismatch. |

Chapter 21 explained how to construct a trustworthy sweep. Here the sweep is examined as a repository extension: who owns it, what it promises, and whether future readers can distinguish its mechanism from its labels.

The source has a target and runs successfully, but zero status is not enough. The three labels do not produce three active core routes. Local formulas can still be internally interesting, but they are not measurements of the mislabeled executions. Documentation that says the sweep validates dataflows therefore exceeds the live path.

The smallest repair is not to add more shapes. It is to make the existing axis effective and the status fail closed. A route discriminator should record requested and active identities, execute nonsymmetric data, and require route-specific state or linked-cycle differences in addition to common functional output. Formula rows should be marked analytical and tested against their own equations. The outer owner should reject missing rows, contradictory text, timeout, stale output, and any process mismatch.

A manifest-driven experiment costs more engineering than a standalone exploratory source, but it pays for exact parameters, relation ownership, raw rows, status, and reproducibility. A split design—one route test and one analytical calculator—may be simpler and more honest than forcing both into one executable label.

## 23.9 Contract card 6: Python binding promises

| Field | Chapter 23 result |
|---|---|
| Promised contract | Python arguments reach live C behavior, callable reports return model data, and packaging/CI owns the boundary. |
| Current classification | **Standalone** for the bounded direct ctypes route; constructor config/report promises are **no-op/fallback**; the supported-package promise is **partial/qualified**. |
| Exact claim IDs | `C23-11`, `C23-12`, `C23-13` |
| Weakest required edge | Input consumption and report implementation; build/CI ownership. |
| Positive evidence | ctypes loading and direct core operations work; a fresh identity GEMM smoke passes. |
| Stop evidence | `config_path` is stored only in Python and constructor calls `tu_init()`; performance and power report methods return advisory stub strings; no Make/CI owner exists. |
| Alternatives and trade-offs | Minimal thin binding; configuration-owning facade; generated ABI binding; or a packaged high-level API. |
| Promotion trigger | Install the package in a clean environment and construct two fresh instances with literal JSON F `{"tu":{"compute":{"pe_array":{"rows":8,"cols":16}},"performance":{"counters":{"enabled":false}}}}` and T `{"tu":{"compute":{"pe_array":{"rows":8,"cols":16}},"performance":{"counters":{"enabled":true}}}}`. Multiply `[[1,2,3],[4,5,6]]` by `[[7,8],[9,10],[11,12]]` once per instance; require both active geometries `8×16` and output `[[58,64],[139,154]]` from an independent Python-loop oracle. F must report `enabled=false` and zero counter/power deltas matching a direct C snapshot; T must report `enabled=true`, `total_macs=12`, `total_flops=24`, `op_mma_fp16=1`, power fields in pJ, and `energy_total_pj` equal to the component sum, all field-for-field equal to its direct C snapshot. A dropped/misnested counter field, old stub string, report/C mismatch, or numeric mismatch must return nonzero. |

The passing identity GEMM is useful but narrow. It proves library loading, selected signatures, memory movement, MMA invocation, and output return for one easy fixture. Identity data is weak against transposition, indexing, and fallback errors because many incorrect paths can preserve it. A nonsymmetric matrix and independent Python calculation provide a stronger far-boundary check.

The `config_path` parameter is a documented promise with no live C consumer. Storing it on the Python object is not retention by the runtime. The report methods are even clearer: method presence is not report integration when the result is a stub string.

A thin binding can intentionally expose only direct C APIs. That reduces policy and packaging burden, but it should remove unsupported constructor/report promises. A configuration-owning facade is friendlier but must define file errors, lifetime, global-state interactions, and version compatibility. Generated bindings reduce signature drift but do not create semantic tests. A high-level packaged API can own all of these, at substantial release and verification cost.

The environment-blocked compiler smoke does not transfer to this binding. The Python identity path ran without exercising the ONNX compiler. Boundaries must be tested separately even when they share a language.

## 23.10 Contract card 7: compiler/runtime/ONNX remains a negative boundary

| Field | Chapter 23 result |
|---|---|
| Promised contract | A contained nontrivial model compiles, generated code links, the executable runs, and far-boundary output matches an independent oracle with unsuppressed status. |
| Current classification | Generator/model components are **standalone**; governed `test-full` failure handling is **no-op/fallback**; the positive composition claim remains ledger-`block`. |
| Exact claim IDs | `C23-15`, `C23-16` |
| Weakest required edge | A contained fail-closed compile→link→run→independent-oracle chain. |
| Positive evidence | A generator and two contained ONNX files exist; Make targets name compiler flows. |
| Stop evidence | `test-full` suppresses generated build/run failures with `|| true`; no contained far-boundary oracle exists; the active compiler smoke is blocked by missing NumPy. |
| Alternatives and trade-offs | Repair one bounded end-to-end fixture; keep compiler demonstration-only; or define an explicit intermediate contract before runtime integration. |
| Promotion trigger | Add one contained `ch23_linear_1x4.onnx` fixture computing `[2,-1,3,4] × [[1,-1],[-2,4],[3,0],[0.5,2]] = [15,2]`; require generated TU work rather than host fallback, unsuppressed compile/link/run statuses, exact independent-oracle output, retained logs, and nonzero status when the TU operation is removed or the output is changed. |

This card closes the chapter at the strongest important absence. Declarations, examples, generated C, host fallbacks, and Make labels can all exist while end-to-end behavior remains unproved. A missing dependency in the active interpreter is an environment observation, not proof that the source would succeed or fail after installation. The static negative evidence remains: the current governed target can suppress failures and has no independent far-boundary oracle.

A bounded repair should begin with one contained model, not “support ONNX.” The model must be nontrivial enough to distinguish host fallback, missing TU work, indexing errors, and constant output. Generation must return nonzero on unsupported lowering. The emitted program must link without ignored status, run without ignored status, and compare final outputs against an oracle that does not call the same generated implementation.

Full-stack accelerator systems such as Gemmini show why compiler, runtime, operating-system, and hardware choices can interact, but that literature is context rather than transferred evidence ([Gemmini](../../references/foundations.md#gen21-gemmini)). TVM demonstrates that graph transforms, scheduling, target code generation, and search are distinct compiler obligations; its existence does not fill Tusim's missing chain ([TVM](../../references/foundations.md#che18-tvm)).

Keeping the compiler demonstration-only is also a legitimate choice if the documentation and build status say so. The unsafe choice is a broad integration label backed by a target that converts failure into green.

## 23.11 Alternatives and trade-offs in extension architecture

The contract cards expose recurring design choices rather than one preferred extension mechanism.

| Strategy | Local benefit | Principal cost or risk | Best fit |
|---|---|---|---|
| closed static extension | deterministic contents, simple ownership, low dispatch overhead | rebuild required; limited external experimentation | core built-ins with stable release cadence |
| checked runtime registry | selectable implementations and rapid experimentation | lifetime, duplicate/overflow status, global state, concurrency | controlled in-process research plug-ins |
| per-instance immutable configuration | reproducible ownership and isolation | larger state and explicit construction/migration | multi-core/context-sensitive execution |
| full-config direct consumption | avoids lossy conversion copies | tight coupling and multiple authority paths | specialized modules with one clear owner |
| compact runtime schema | explicit supported subset and smaller state | conversion drift and duplicated defaults | stable public runtime contract with generated tests |
| standalone analytical tool | low coupling and fast model iteration | no production reachability; separate fidelity domain | estimates and design exploration |
| integrated production provider | one owned route and observability | larger regression surface; risks mixed timelines | behavior required by ordinary workloads |
| thin language binding | small API and maintenance burden | fewer policies, weak packaging, easy promise drift | expert direct-C parity |
| high-level packaged binding | usability and stronger release ownership | compatibility, lifecycle, and oracle burden | supported external users |
| broad catalog plus checked lowering | decouples tool vocabulary from one runtime | capability negotiation and unsupported paths | evolving compiler/runtime pairs |
| one shared executable ISA | simpler semantic census | release coupling and reduced analytical flexibility | tightly controlled stack |

The trade-offs span more than performance. A global registry may add negligible dispatch time yet impose high verification and lifecycle cost. A compact runtime config may reduce state but create silent no-ops if conversion tests are incomplete. A source-island model may be architecturally useful precisely because it does not perturb ordinary execution, but it needs explicit analytical labeling. A high-level binding improves usability while increasing compatibility and packaging obligations.

The extension contract card prevents these costs from being hidden behind “modularity.” It requires the chosen strategy to state ownership, error behavior, observables, and release scope.

## 23.12 Reproducible evidence walk-through

From a clean book checkout, the reader can verify the immutable authority without modifying Tusim:

```bash
cd /path/to/tusim-book
run=results/ch23-predraft/20260819T084945Z-postreview
python3 "$run/verify_ch23_predraft_seal.py" --run-dir "$run"
python3 -O "$run/verify_ch23_predraft_seal.py" --run-dir "$run"
```

Expected receipts are:

```text
CH23_SEAL_VERIFY PASS mode=postreview members=19 boundary=negative
CH23_SEAL_VERIFY PASS mode=postreview members=19 boundary=negative
```

The retained reconnaissance can then be inspected:

```bash
grep '^PATH_\|^FOCUSED \|^COMPILER_\|^SOURCE_STATE' "$run/recon.log"
```

The binding observations are:

- source state is detached and tracked-clean at the exact pin before and after;
- runtime geometry reaches runtime, while dataflow, pipeline, and DMA width are parsed then dropped;
- four dataflow IDs are declared and three are linked/registered/consumed;
- production dispatch enters from two files and three call sites;
- unregistered selection falls back to WS with success;
- the ISA has 59 explicit members and the queue eight dispatch cases;
- the cycle model has no library membership, Make rule, production reachability, or external non-test call file;
- the sweep's labeled routes are WS/OS/RS but effective routes are WS/WS/WS;
- Python stores but does not consume config path and leaves two report stubs;
- compiler promotion remains `compile=0 link=0 run=0 independent_oracle=0 full=0`;
- the canonical config focus is red and layout-sensitive, while dataflow, ISA, command queue, sweep process, and binding smoke return green within their stated scopes.

The package passed 13 mutation families. They include extra files/directories, byte-identical symlink substitution, retained-manifest and seal changes, compiler-boundary promotion, review-binding collision, missing reconciliation rows, and fully resealed plan/ledger reversals. These controls prove that the package detects named evidence changes. They do not prove that every future extension is correct or that the model is calibrated.

## 23.13 Verification: promotion evidence must attack the missing edge

A useful extension test suite is layered.

### Declaration and identity controls

Require exact accepted IDs, reject duplicates or define replacement precisely, and test unknown values. Aliases must resolve to one intended semantic object, not merely one integer. Count-preserving identity swaps should fail when identity is claim-bearing.

### Ingress and retention controls

Set a value that differs from every default. Inspect the receiving object after each lifecycle transition: parse, conversion, construction, core swap, reset, context save/restore, and reinitialization. A field that is correct immediately after parsing can still be dropped or overwritten later.

### Consumer and observable controls

Trace an actual production call, not an include or symbol name. Use a discriminating fixture. For equivalent dataflows, functional equality alone may be expected, so active identity and route-specific linked state are additional observables. For an opcode, choose operands whose wrong handler or no-op cannot accidentally pass.

### Ownership and failure atomicity

Exercise duplicate, capacity, invalid-ID, allocation-failure, and teardown paths. Verify both pointer ownership and returned status after each branch. A path that frees the new duplicate and a path that leaks the overflow submission require different caller behavior.

### Status propagation

Every stage must preserve nonzero failure: generator, compiler, linker, executable, parser, oracle, and wrapper. Printed `FAIL` with zero status is non-pass. `|| true` is incompatible with a promotion gate.

### Build and release ownership

Check source→rule→aggregate→CI→package relations literally. A dedicated target can be intentional, but documentation must not imply aggregate coverage. A binding intended for users needs package/import verification in a clean environment, not only execution from the source tree.

### Documentation convergence

Documentation should state requested identity, active identity, fallback/error behavior, ownership, producer/fidelity, and known omissions. Mutation-test at least one overpromotion: change “standalone” to “integrated” or reverse the negative compiler boundary and require validation to fail.

## 23.14 Fidelity box

> **What Chapter 23 establishes**
>
> **Established:** a reviewed eight-edge extension contract; seven exact-pin whole-path families; 34 source, test, build, documentation, and model input hashes; direct WS/OS/RS production consumption; exact registry duplicate and overflow behavior; 59 explicit ISA members versus eight queue cases; source-island, sweep, binding, and compiler boundaries; an exact 19-member non-symlink postreview closure; normal/optimized verification; and 13 mutation families.
>
> **Qualified:** runtime geometry propagation reaches initialization, but canonical verification aborts with a layout-sensitive stack-smashing result whose root cause remains open; direct dataflow selection works for WS/OS/RS, but JSON selection does not; Python direct operations work for a bounded identity smoke, but constructor configuration, reports, packaging, and broad numeric correctness are not established.
>
> **Not established:** NLR execution; an open dynamic plug-in ABI; execution of every declared ISA opcode; scheduler/liveness-to-queue composition; cycle-model production integration; three effective routes in the shipped dataflow sweep; live Python config/report support; or compiler/runtime/ONNX composition.
>
> **Safe use:** classify a proposed extension at its weakest required edge and design the minimum discriminating promotion experiment.
>
> **Unsafe use:** treat declarations, parser acceptance, source/test presence, successful fallback, printed rows, stub methods, or suppressed build status as integrated behavior.

## 23.15 Binding claim-boundary register

The following statements control any broader-sounding exposition in this chapter.

1. `C23-01`: extension readiness is a chapter-defined conjunction, not a repository guarantee or weighted maturity score.
2. `C23-02`: runtime geometry propagation is partial/qualified until the layout-sensitive stack-smashing failure is root-caused and a repeated discriminating downstream observable is green.
3. `C23-03`: parsed dataflow, pipeline-depth, and DMA-width values are omitted by the audited runtime conversion path; other direct or compile-time ingress paths remain separate.
4. `C23-04`: direct WS/OS/RS selection is production-consumed, but global registry/core ownership and config-selection gaps bound the claim.
5. `C23-05`: NLR is declared but unregistered; selection falls back to WS while returning success and is not NLR execution.
6. `C23-06`: duplicate registry IDs retain the first pointer and free the new duplicate; capacity overflow silently returns without freeing the submitted pointer or reporting status.
7. `C23-07`: 59 is the exact count of explicit assigned opcode members under the sealed syntactic definition; it is not an execution count.
8. `C23-08`: the command queue has eight source dispatch cases; focused execution covers its bounded suite, not the expanded ISA catalog.
9. `C23-09`: aliases, metadata, and adjacent static-analysis consumers do not prove queue/runtime execution or compiler composition.
10. `C23-10`: cycle-model source and focused-test presence do not establish archive linkage, release ownership, or production reachability.
11. `C23-11`: the Python identity GEMM smoke supports a bounded direct ctypes path only; it does not exercise constructor configuration, reports, packaging, or general numeric correctness.
12. `C23-12`: Python stores `config_path` but does not pass it to a live C initializer at this pin.
13. `C23-13`: Python performance and power report methods are advisory stubs, not live report bindings.
14. `C23-14`: documentation is an audited claim source and cannot override contradictory executable behavior.
15. `C23-15`: source models, a generator, and named Make targets do not establish a nontrivial compile-link-run-oracle path when statuses are suppressed and the far-boundary oracle is absent.
16. `C23-16`: compiler/runtime/ONNX integration remains blocked until one contained nontrivial fixture fails closed through compile, link, run, and independent comparison.
17. `C23-17`: the shipped dataflow sweep is standalone and fail-open on mismatch; its WS/OS/RS labels effectively execute WS/WS/WS and its local formulas are separate producers.

## 23.16 Common failure modes

### Counting artifacts instead of tracing relations

A field count, enum count, source count, or test count can be exact and still answer the wrong question. Trace exact identities through required edges.

### Treating parse success as runtime effect

Stored full-config state can disappear at conversion or initialization. Use nondefault A/B effects at the intended consumer.

### Collapsing direct and configured ingress

A working setter does not repair a dropped JSON path. A broken config path does not erase a working direct route. State both scopes.

### Reading fallback success as requested execution

NLR-to-WS fallback returns success. Status without active identity can preserve the wrong label.

### Using generic ownership language

“Replacement hazard” hides whether the old or new object survives. “Overflow risk” hides whether ownership transfers or leaks. Record exact pointer and status behavior.

### Equating metadata with execution

ISA declarations, aliases, scheduler reads, and liveness reads can all be useful while queue execution is absent. Require the dispatch and observable.

### Calling a focused source production-owned

A source and test file can remain outside `TU_OBJS`, without a Make rule, package, or non-test caller.

### Accepting a green fail-open sweep

A program that prints a mismatch and returns zero is not a promotion gate. Effective route and status both matter.

### Testing only identity data at a binding boundary

Identity matrices can hide transposition, indexing, and fallback defects. Use nonsymmetric data and an independent oracle.

### Transferring an environment blocker across boundaries

Missing NumPy blocks the active compiler smoke. It says nothing about the independent direct ctypes smoke that already ran.

### Letting documentation complete a missing path

Documentation can define the intended promise and reveal drift. It cannot serve as the consumer, observable, or test.

### Reviving the compiler stack from adjacency

A model file, generator, static analyses, queue, and runtime can coexist without a contained executable composition. Every transition needs a real producer and fail-closed status.

## Development questions

1. Should `tu_config_to_runtime()` be generated from a machine-readable supported-field schema?
2. Should unsupported configuration keys fail parsing, fail conversion, or be reported as inactive capabilities?
3. Should requested and active dataflow identities be separate public fields?
4. What registry API can express ownership transfer, duplicate rejection, capacity failure, and unload safety without process-global ambiguity?
5. Should plug-ins be immutable per core or shared through versioned global descriptors?
6. How should supported ISA/queue capabilities be queried by compiler and binding producers?
7. Which operation is the smallest useful encode→submit→dispatch→oracle fixture?
8. Should the cycle model remain a standalone analytical provider or become an optional linked metric source?
9. What result schema would keep sweep functional outputs, linked estimates, and local formulas separate?
10. Which package and clean-environment checks are required before calling the Python API supported?
11. What is the smallest contained ONNX model that defeats host fallback and constant-output false greens?
12. How should extension cards be generated and checked in CI without turning every experimental module into production code?

## Summary

An extension is a promise, not an artifact. The promise must name its required declaration/identity, ingress, retention with lifetime/ownership, production consumer, observable effect, fail-closed verification, build/release ownership, and behavior-matching documentation. Integration is conjunctive, so the weakest missing edge determines the strongest safe claim.

Tusim's runtime geometry reaches initialization but remains partial/qualified because canonical verification is layout-sensitive and red. Parsed dataflow, pipeline-depth, and DMA-width settings stop at conversion. Direct WS/OS/RS selection reaches production consumers, while NLR and unknown IDs fall back to WS with success.

Registry semantics must be exact: duplicates keep the first pointer and free the new one; overflow silently returns without freeing the submitted pointer or reporting status. These behaviors constrain any claim of an open dynamic ABI.

The 59-member explicit ISA catalog and eight-case command queue are different surfaces. Scheduler and liveness are adjacent analysis consumers, not an execution bridge. The cycle model is a standalone source island. The dataflow sweep is owned by a dedicated target but effectively routes WS/WS/WS and fails open on mismatches. The Python binding has a bounded direct path but stores rather than consumes `config_path` and returns report stubs.

Finally, no compiler/runtime/ONNX composition is established. Promotion requires one contained nontrivial fixture whose compile, link, run, and independent comparison all fail closed. Until then, source presence, documentation, and suppressed targets remain evidence of intent and gaps—not integration.

## Review questions

1. Why is extension readiness modeled as a conjunction rather than a score?
2. What distinguishes a partial/qualified path from a standalone module?
3. Why does geometry propagation remain qualified despite reaching runtime initialization?
4. Why does a parsed dataflow value not prove configured dataflow behavior?
5. What does direct WS/OS/RS integration establish, and what does it not establish?
6. What exactly happens on duplicate registry ID and on registry overflow?
7. Why do 59 explicit ISA members not imply 59 queue operations?
8. Why are scheduler and liveness consumers not a compiler/runtime execution bridge?
9. Which edges make the cycle model a source island?
10. Why is the dataflow sweep's zero status insufficient?
11. What does the Python identity GEMM prove, and what remains unproved?
12. Why must the compiler smoke and direct binding smoke be assessed separately?
13. What four stages define the minimum compiler/runtime/ONNX promotion trigger?
14. Why can documentation be a claim source but not behavioral proof?
15. How should a promotion test attack the weakest edge rather than merely add coverage?

## Review-question answer key

1. A score permits strong documentation or test count to compensate for a missing consumer, correctness, ownership, or status edge; a conjunction does not.
2. Partial/qualified has a real portion of the promised path but a missing/red required edge. Standalone has an intentionally isolated executable or analytical contract without the broader production reachability claim.
3. The canonical focused run aborts with stack smashing and independent layouts disagree; root cause and a repeated discriminating downstream matrix are still missing.
4. The full config retains the parsed value, but `tu_config_to_runtime()` omits it and initialization therefore does not consume that ingress.
5. It establishes linked registration and direct production dispatch for three implementations. It does not establish JSON selection, per-core/global lifecycle coherence, NLR, physical movement, or calibration.
6. A duplicate keeps the first pointer and frees the new duplicate. Overflow returns silently without freeing the submitted pointer or returning failure status.
7. Declarations and metadata do not manufacture operand retention, dispatch cases, semantic effects, negative behavior, or differential tests.
8. They consume adjacent representations for analysis but no source path composes their output into queue/runtime execution.
9. It is absent from `TU_OBJS`, has no Make rule, and has no external non-test caller, despite source/header/focused-test presence.
10. Its labeled core routes are effectively WS/WS/WS, and mismatch text does not change process status.
11. It proves a bounded ctypes/library/direct-operation route for one easy fixture. It does not prove config consumption, live reports, packaging, broad ABI compatibility, or general numeric correctness.
12. Missing NumPy affects the compiler import path; the direct binding smoke is a different route and ran independently.
13. Unsuppressed compile, generated-code link, execution, and independent far-boundary output comparison for one contained nontrivial fixture.
14. Documentation can state intended behavior and expose divergence, but it does not execute, retain state, produce an observable, or propagate status.
15. Set a nondefault or malformed case that distinguishes the intended mechanism, observe the exact consumer/effect, and require the specific wrong path to return nonzero.

## Design exercises

1. **Configuration promotion.** Choose one dropped field and design a parser→conversion→consumer→observable A/B test with lifecycle checks.
2. **Registry API.** Specify ownership and statuses for insert, duplicate, replace, capacity, lookup, and teardown.
3. **NLR extension.** Fill all eight contract-card edges for a plausible no-local-reuse implementation and name its local gain and sacrifices.
4. **Opcode promotion.** Select one declared but undispatched operation and design encode/submission, operand, dispatch, oracle, and error fixtures.
5. **Module ownership.** Compare keeping the cycle model standalone with linking it as an optional provider; include fidelity and release costs.
6. **Sweep repair.** Rewrite the dataflow sweep's evidence contract so requested identity, active route, producer, rows, and status cannot diverge silently.
7. **Binding discriminator.** Replace identity GEMM with a nonsymmetric fixture and define an independent far-boundary oracle.
8. **Compiler trigger.** Design one contained model that can detect host fallback, missing TU work, link suppression, and constant output.
9. **Documentation mutation.** Change one standalone/qualified label to integrated and design a validator gate that rejects the coherent overpromotion.
10. **Trade-off review.** Compare static built-ins, per-core immutable plug-ins, and a versioned dynamic ABI across latency, state, ownership, compiler/runtime burden, and verification.

## Exercise answer sketches

1. Use a value unlike every default, check the full and compact structs, run the intended consumer before and after reset/reinit, and require a discriminating effect; a print-only check is insufficient.
2. Return explicit success/duplicate/capacity/invalid statuses, state whether ownership transfers on each result, preserve the old pointer on rejection, and test every branch with leak and double-free controls.
3. Require a unique ID, direct and configured ingress, per-core or global lifetime, linked dispatcher consumption, route identity, differential traffic/state evidence, negative fallback tests, build/package ownership, and behavior-matching docs. Potential reuse/traffic gains must be balanced against local storage, bandwidth, control, and verification costs.
4. Use nonsymmetric operands, retain all descriptor fields, assert the exact handler and effect, reject malformed/unsupported operands, and compare with an independent reference.
5. Standalone preserves model isolation and rapid iteration; optional linkage improves discoverability and ordinary-call reachability but requires one metric contract, lifecycle, reset, packaging, and regression ownership.
6. Record requested and active routes, separate functional and analytical producers, use route-specific observables, fail on every mismatch, retain raw rows, and add aggregate/CI ownership only if the release promise requires it.
7. Use distinct non-square values so transpose, indexing, constant, and fallback paths diverge; compare Python output with an independently computed matrix product.
8. Include at least one supported TU operation and one value pattern that host fallback or zero TU work cannot mimic; fail each stage separately and retain the oracle comparison.
9. Gate exact claim IDs and classifications in a complete claim matrix, then coherently mutate the manuscript label while keeping hashes valid in a disposable copy; review mode must reject the semantic contradiction.
10. Static built-ins minimize ownership and dispatch complexity; per-core tables improve isolation at state cost; a dynamic ABI maximizes extensibility but adds negotiation, lifetime, packaging, and broad negative testing. No single choice dominates every regime.

## Primary references

- [Chapter 23 framing and evidence plan](../../notes/chapter-23-framing-and-evidence-plan.md) — reader decision, path matrix, and drafting boundaries.
- [Chapter 23 source–claim ledger](../../notes/chapter-23-source-claim-ledger.md) — exact claim IDs, states, evidence, and promotion triggers.
- [Independent Chapter 23 predraft review](../../notes/chapter-23-independent-predraft-review.md) and [reconciliation](../../notes/chapter-23-predraft-review-reconciliation.md) — candidate binding and resolved findings.
- [Final Chapter 23 postreview authority](../../results/ch23-predraft/20260819T084945Z-postreview/seal.json) — exact source pin, decision, boundary, manifest digest, and validation state; the adjacent run directory retains recon, controls, manifests, review, and validators.
- [RISC-V Unprivileged ISA](../../references/foundations.md#riscv26-risc-v-unprivileged-isa) — normative instruction-contract vocabulary; not evidence of Tusim encoding or execution.
- [OpenCL command-queue contract](../../references/foundations.md#ocl311-opencl-command-queue-contract) — lifecycle vocabulary; not transferable Tusim semantics.
- Genc et al., “Gemmini: Enabling Systematic Deep-Learning Architecture Evaluation via Full-Stack Integration,” DAC 2021. [DOI 10.1109/DAC18074.2021.9586216](https://doi.org/10.1109/DAC18074.2021.9586216).
- Chen et al., “TVM: An Automated End-to-End Optimizing Compiler for Deep Learning,” OSDI 2018. [Official publication](https://www.usenix.org/conference/osdi18/presentation/chen).
