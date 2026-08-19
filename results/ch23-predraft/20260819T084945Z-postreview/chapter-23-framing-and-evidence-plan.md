# Chapter 23 Framing and Predraft Evidence Plan

Status: framing only; **manuscript drafting is forbidden until the post-review predraft seal passes**.

## Reader decision

After this chapter, a reader deciding whether to extend Tusim should be able to answer one constraint-first question:

> **What contract am I promising, and which weakest missing edge prevents me from calling the extension integrated?**

The selected lens is an eight-edge **extension contract card**:

1. declaration and identity;
2. ingress (configuration, API, encoded instruction, or binding);
3. retention and ownership;
4. production consumer/dispatch;
5. observable effect;
6. focused and integration verification;
7. build/release owner;
8. documentation that matches live behavior.

An integrated claim is conjunctive. One missing required edge blocks promotion. This is deliberately stricter than counting source files, enum members, tests, or documentation pages.

## Scope ranking

| Rank | Candidate scope | Reader utility | Exact-pin evidence | Principal risk | Decision |
|---|---|---:|---:|---|---|
| 1 | **Extension contracts: trace the weakest edge from declaration to owned evidence** | Very high | Very high across config, dataflow, opcode, module, binding, docs/build | Could become a taxonomy unless every class is anchored to a whole path | **Selected** |
| 2 | Configuration as an extension surface | High | High; parsing and `tu_config_to_runtime()` are inspectable and testable | Too narrow; cannot explain registered plugins, unlinked modules, or ISA/queue splits | Reject as chapter-wide scope; retain as first worked path |
| 3 | Pluggable dataflow as the canonical extension mechanism | High | High for WS/OS/RS and the registry/dispatcher | Overstates uniformity; NLR is declared/documented but unregistered, and config selection is dropped | Reject as canonical model; retain as a contrasting path |
| 4 | ISA/opcode growth from enum to execution | Medium-high | High for declaration, metadata, aliases, queue dispatch, tests | Risks drifting into compiler/runtime/ONNX claims not supported by an end-to-end oracle | Retain as a negative promotion example only |
| 5 | Bindings and experiment harnesses as integration/release surfaces | Medium | Medium; static source and Make ownership are inspectable | Broadens into packaging and user API design before the core extension rule is established | Defer except as boundary checks |

### Why rank 1 wins

The reader's binding constraint is not “how do I add a source file?” It is “what evidence permits a stronger integration claim?” The exact pin contains materially different states: runtime geometry that reaches a consumer, parsed fields dropped during conversion, three registered dataflow implementations alongside a declared fourth ID, a 59-member explicit ISA catalog with eight command-queue dispatch cases, a cycle-model source/test set outside the production archive, and a Python surface that stores but does not consume `config_path`. A weakest-edge rule makes these differences legible without flattening them into one fastest or best architecture.

## Fresh exact-pin reconnaissance summary

Pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`, detached and tracked-clean before and after the disposable run.

| Path | Declaration → ingress → retention → consumer → observable → verification/build/docs | Classification |
|---|---|---|
| Runtime geometry | `tu_config_t` fields → JSON/default → `tu_config_to_runtime()` → `tu_runtime_config_t` → `tu_init_with_config()` | **Partial/qualified**: propagation reaches the runtime, but the canonical fresh verification edge aborts with stack smashing; root cause is open and no discriminating green downstream observable supports promotion |
| Dataflow selection | config parser accepts mode → conversion omits mode; direct `tu_set_dataflow()` selects from global registry → production `tu_mma()` and attention call `tu_dataflow_execute_mma()` → dispatcher invokes the selected vtable → plugin stats/tests | Direct-API integrated for WS/OS/RS; config ingress is a no-op path; NLR is declared/documented but unregistered, and selecting an unregistered ID silently falls back to WS with success status |
| Expanded ISA / command queue | 59 explicit enum values → aliases/descriptors/metadata → queue submission → eight execution cases → queue counters/tests; scheduler/liveness consume adjacent metadata | Catalog and analysis surfaces exceed executable queue surface; aliases or static-analysis consumption do not prove execution or composition |
| Cycle model | source/header/test → no production archive member, no Make rule; exhaustive tracked C/H scan finds no external non-test `tu_cycle_*` caller | Standalone source island, not a linked runtime extension |
| Dataflow sweep | fixed workload/seeds → labels WS/OS/RS around core-wrapper calls → all three core snapshots effectively route WS → local formulas/printed comparison → dedicated Make target and exploration doc | Standalone, non-aggregate harness; labels do not prove effective routing and mismatch text does not change process status |
| Python binding | module/import → ctypes library → direct core API; identity GEMM smoke passes; `config_path` retained in Python only → `tu_init()` | Standalone partial integration; green identity does not exercise config path or report stubs; no Make/CI owner |
| ONNX/compiler boundary | two contained ONNX files → generator → `test-full` compile/run statuses suppressed with `|| true`; no contained far-boundary oracle | **Negative boundary preserved**: no nontrivial compile-link-run-oracle trigger at this pin; Chapter 23 must not claim compiler/runtime/ONNX integration |

Primary evidence is enumerated in `notes/chapter-23-source-claim-ledger.md`. Machine-checkable reconnaissance is `experiments/ch23_extension_recon.py`.

## Planned chapter argument (not prose)

1. **Start with the promise, not the hook.** Define integrated, standalone, partial, and no-op extension states using the contract card.
2. **Trace one complete-enough path.** Use runtime geometry to show parsing, conversion, initialization, and observable structure while retaining the red fresh focused test result.
3. **Contrast a split path.** Dataflow works through direct API and registry/dispatcher for WS/OS/RS while configuration ingress and the declared NLR ID stop earlier.
4. **Show why declaration counts mislead.** Compare the expanded ISA catalog with command-queue execution cases and aliases.
5. **Make ownership a first-class edge.** Use cycle-model and Python-binding surfaces to distinguish source presence from production/release ownership.
6. **Apply the promotion rule.** The weakest missing required edge sets the strongest defensible claim.
7. **Close at the boundary.** State the exact trigger that would permit compiler/runtime/ONNX discussion; it is not satisfied at this pin.

## Claim discipline

Allowed after a green post-review seal:

- explain the contract card and the four extension states;
- report exact-pin path classifications;
- report source/documentation divergence as divergence, not as intent;
- report the fresh dynamic results, including the red configuration test and environment-blocked compiler smoke;
- recommend fail-closed promotion criteria.

Forbidden without new sealed evidence:

- claiming all configuration fields affect runtime behavior;
- calling every declared dataflow or opcode executable;
- treating focused metadata tests as end-to-end execution proof;
- treating source/test presence as production linkage or release ownership;
- claiming the Python binding consumes a config file or provides live reports;
- claiming nontrivial ONNX → generated C → linked executable → runtime result correctness;
- using “production-grade,” “complete,” or equivalent labels from comments/docstrings as evidence.

## Predraft gates

Drafting may begin only when all are true:

- [x] source pin, detached state, tracked cleanliness, and selected file hashes are machine checked;
- [x] at least three plausible scopes are ranked and one reader decision is selected;
- [x] whole paths are traced across seven extension families, including one sweep source→target→output→documentation path;
- [x] source/documentation conflicts and negative findings remain visible;
- [x] disposable archive build and focused probes run without writing Tusim;
- [x] provisional seal is generated from the exact inputs;
- [ ] independent skeptical review is retained;
- [ ] review findings are reconciled into this plan and ledger;
- [ ] post-review predraft seal passes with reviewer/reconciliation hashes;

Until the final three boxes are checked, `manuscript/part-3-practice/23-*.md` must not exist.

## Evidence limitations to carry into drafting

- The canonical `test-config` build aborts after initialization with a stack-smashing diagnostic, while independent archive/build variants have also passed 20/20. The layout-sensitive root cause remains open; promotion requires root-cause resolution and a discriminating repeated-build/path matrix, not one green rerun.
- The compiler smoke is environment-blocked by missing NumPy in the active interpreter. That observation neither proves nor clears the source-level compiler trigger.
- Registry ownership is global: duplicate IDs retain the first pointer and free the newly supplied duplicate; capacity overflow returns silently without freeing the submitted pointer or reporting status. This is not an unconstrained plugin ABI.
- Duplicate plugin IDs keep the first stable registry pointer and free the newly created duplicate; an over-capacity registration returns silently without freeing the submitted pointer or reporting status. Both are ownership/status constraints, not dynamic replacement semantics.
- Unregistered dataflow IDs—including the declared but absent NLR ID—fall back to WS and return success; this must be presented as a documented no-op/fallback hazard, not successful support.
- The audited dataflow sweep is useful evidence only when its rows and status semantics are interpreted explicitly: its local formula is not runtime timing and its mismatch checks do not fail the process.
- The sweep's three labeled core executions all restore WS from their core snapshots; WS/OS/RS labels therefore do not establish three effective runtime routes.
- Documentation is a claim source to audit, not behavioral proof.
- Counts are exact only for this pin and this script's syntactic definitions.
