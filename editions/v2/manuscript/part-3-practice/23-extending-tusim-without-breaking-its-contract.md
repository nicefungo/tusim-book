# Chapter 23 — Extending Tusim Without Breaking Its Contract

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-23)

Adding a field, enum, source file, plug-in, test, or binding method is easy to mistake for extending a system. Each artifact can be real while the promised behavior remains unreachable. A parser can retain a value that runtime conversion drops. A registered plug-in can work through a direct API while configuration still selects the default. An ISA catalog can grow far beyond the command queue that executes it. A source file and focused test can remain outside the production archive. Documentation can name a mode that silently falls back to another implementation.

This chapter asks one architecture question:

> Given a proposed extension, what contract is being promised, and which weakest missing edge prevents calling it integrated?

At Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25`, seven extension families make that question concrete: runtime configuration, dataflow/plugin selection, ISA/command queue, cycle-model module, dataflow sweep, Python binding, and compiler/runtime/ONNX.

Three contracts have new evidence: configuration, plug-in selection and the sweep. The remaining four families retain their v1 evidence, not new public-pin test results.

## 23.1 Theory: extension readiness is a conjunctive contract

Let an extension claim be $E$. Define eight relations:

- $D$: the declaration and identity are unambiguous;
- $I$: a named ingress accepts or creates the extension;
- $R$: state is retained with explicit lifetime and ownership;
- $C$: a production consumer or dispatcher reaches it;
- $O$: a discriminating observable changes as promised;
- $V$: verification reaches the route, compares an adequate oracle or invariant, and fails closed;
- $B$: build, aggregate, CI, packaging, and release ownership are explicit; and
- $M$: documentation matches the live behavior and limitations.

Then an integrated claim requires

$$
\operatorname{Integrated}(E)=D\land I\land R\land C\land O\land V\land B\land M.
$$

The equation is a review discipline, not an API supplied by Tusim. It does not imply that every extension needs the same implementation shape. A compile-time module may not need a runtime parser. A direct C API may not need JSON. A report generator may not belong in the production archive. The card must first name the promised contract; only then can it decide which edges are required.

### Four extension states

This chapter uses four states.

**Integrated** means every edge required by the stated promise is present and the evidence is discriminating. It is scoped: “direct-API integrated for WS/OS/RS” is meaningful, while “the dataflow system is integrated” leaves the ingress, owner, and unsupported NLR ID unspecified.

**Partial/qualified** means a real path exists but one required edge is red, ambiguous, or narrower than the advertisement. The safe narrower statement must be explicit. A verified geometry and mode do not establish that a queue-depth request in the same file reaches the queue.

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

## 23.4 Contract card 1: runtime configuration (public pin)

| Field | Chapter 23 result |
|---|---|
| Promised contract | A named JSON/default setting reaches the intended runtime consumer and changes a discriminating downstream observable. |
| Current classification | Effective for the tested file→runtime→consumer paths; **partial/qualified** for the promise that every setting controls execution. |
| Exact claim IDs | `C23-02` (geometry), `C23-03` (parsed versus effective fields). |
| Weakest required edge | For an unproved field, identify its actual consumer. For a misspelled key, the first missing edge can be detection at ingress. |
| Positive evidence | A nondefault 4×8 geometry survives conversion and initialization. Mode and depth affect selected MMA estimates; width affects two separately bracketed DMA estimates. |
| Stop evidence | Requested queue depth 3 is active as 16; requested rounding value 1 is active as 0. An unknown width **key** can be ignored even though an unknown mode **value** is rejected. |
| Alternatives and trade-offs | Extend the compact schema, let a specialized consumer read the full config, or reject settings the runtime cannot honor. |
| Promotion trigger | To claim queue depth is configurable, hold the workload fixed, change only the key, check the active capacity and its effect at the full-queue boundary, and require a default-restoring mutation to fail. |

The probe and run ledger distinguish expected rejection from process failure. The loader returned `-1` for both `no_local_reuse` and `wieght_stationary`; their checker exited 0 **because** it observed the rejection. A different control supplied a valid OS file but expected WS. That checker exited 1 at the parsed-field comparison, before checking the converted fields or running MMA. It tests the checker's ability to detect a wrong label, not a failure to load OS.

Three extension strategies remain plausible:

1. **Expand `tu_runtime_config_t`.** This creates one explicit conversion contract and enables generated propagation tests. It increases ABI/state surface and requires lifecycle/default compatibility.
2. **Pass the full config to specialized consumers.** This avoids duplicating every field in a compact structure but increases coupling and can create multiple authority paths.
3. **Delete or deprecate unsupported fields.** This narrows the promise and verification burden but sacrifices forward-looking configuration compatibility.

The right choice depends on ownership, not field count. Whichever route is chosen must reject or report unsupported values rather than accepting a documented no-op.

## 23.5 Who owns a plug-in selection?

Follow the owner of the selection rather than the printed label:

- **File.** The accepted spellings `weight_stationary`, `output_stationary`, and `row_stationary` map to IDs 0, 1, and 2. The matched S4 file-to-MMA pair exercised WS and OS. Do not count a later RS setter as a third matched file run.
- **Direct state.** After initialization from the OS file, `tu_set_dataflow(2)` returned 0. The active RS route produced the same 45 words but a delta of 384 instead of 52. Requests for IDs 3 and 99 returned `-1`; RS remained active and the retained file request was still 1. See the actual setter sequence.
- **Core state.** Pair `tu_core_set_dataflow(core,id)` with `tu_core_mma(core,...)`. The wrapper installs the core snapshot for the call, writes it back, then restores the surrounding direct state. In the alternating-core probe, core 0 entered its second edge MMA at 258 and returned at 330 (OS delta 72). The idle peer kept its ID and counter; the direct and core setters each rejected NLR without changing that owner's selection. These checks do not cover arbitrary unchecked runtime structs. The objects are shared; the selections are not.

Attention provides a useful limit on the word *consumer*. Its two MMA call sites use the active dispatcher; `desc.dataflow` does not select either backend. The S10 whole-row and split-KV probe returned FP16 `3400` (¼) for both uniform arms and `3800` (½) for both tagged arms. That distinguishes whole-row normalization from adding independently normalized tiles. It does not establish a descriptor-controlled route, physical movement, or overlap.

Materially distinct future designs include:

- **Static built-ins with closed IDs.** Small ownership surface and deterministic release contents, but no runtime extensibility.
- **Checked global registry.** Minimal dispatch overhead and simple lookup, but process-global lifetime complicates cores, contexts, concurrency, and replacement.
- **Per-core immutable plug-in table.** Stronger isolation and reproducibility, at the cost of larger snapshots and explicit construction.
- **Versioned dynamic ABI.** Maximum external extensibility, but requires symbol/version negotiation, error-returning registration, ownership transfer rules, unload safety, packaging, and much broader verification.

None is universally best. The current evidence supports a static built-in interpretation more strongly than an open dynamic ABI.

## 23.8 Contract card 5: a sweep as an extension surface (public pin)

| Field | Chapter 23 result |
|---|---|
| Promised contract | Labeled alternatives reach distinct mechanisms, rows use owned producers, and mismatches fail the governed process. |
| Current classification | Two **standalone, focused targets**. The single-state sweep fails closed on the tested identity and output mutations. The three-core sweep checks selection and peer equality, a narrower contract. |
| Exact claim ID | `C23-17` (what a dedicated target and printed rows authorize). |
| Weakest required edge | For the three-core numerical claim: an independent expected output and an in-process cycle check. For aggregate coverage: an actual owning aggregate and launch receipt. |
| Positive evidence | 21 single-state rows gate active ID/name, output bits, and bracketed MMA estimate. Four three-core workloads check retained modes and byte-identical peer outputs. |
| Stop evidence | The single-state oracle shares the simulator's FP16 conversion. Three equal peers can share an error. The three-core executable prints its cycle columns without asserting them. |
| Alternatives and trade-offs | Keep the targets separate and label what each gates, or add independent per-core word and cycle checks to support the stronger claim. |
| Promotion trigger | To claim aggregate-owned heterogeneous verification, give the core test an independent expected result, make a common wrong result and a wrong cycle delta each return nonzero, then show that the named aggregate actually launched it. |

On v1 the WS/OS/RS labels effectively ran WS/WS/WS; a mismatch could print without changing exit status. The public single-state executable starts each row from a runtime struct, not a file. For a 31×19×17 edge on 16×16 PEs at depth two, WS/OS/RS give 468/88/276 estimated cycles; at depth one they give 268/88/68. The smallest estimate changes from OS to RS without any change in the required output. The three-core executable prints the same depth-two triple. Independent arithmetic can check those printed values after the fact; it cannot make that executable reject a bad cycle column.

Two controls pinpoint different failures. In S13's wrong-route run, one OS-labelled depth-four row actually initialized WS. The active-identity check rejected it **before** MMA (child exit 1); the row's zero is an untouched report field, not a cycle measurement. In the S4 output control, WS *did* execute. Flipping one expected bit gave `3fa10000` versus `3fa10001` after 468 estimated cycles, and the executable exited 1. Neither control is the wrong-file-expectation check in §23.4.

The separate S4 probe compared 846 FP32 words over 15 MMA calls with a reference independent of simulator conversion. Those checks strengthen the evidence for those calls, not the oracle inside either shipped sweep. The S13 launch census found neither sweep in `test` or `test-quick`, although both aggregates exited zero. A dedicated target can own a useful local experiment without owning a release decision.

## 23.15 Binding claim-boundary register

The 17 entries below summarize the historical v1 register. The table after them identifies the public-pin revisions; a later check does not silently replace a historical ruling.

1. `C23-01`: extension readiness is a chapter-defined conjunction, not a repository guarantee or weighted maturity score.
2. `C23-02`: the historical runtime-geometry result was qualified by an unresolved process failure; it did not establish reliable downstream propagation.
3. `C23-03`: parsed dataflow, pipeline-depth, and DMA-width values are omitted by the audited runtime conversion path; other direct or compile-time ingress paths remain separate.
4. `C23-04`: direct WS/OS/RS selection is production-consumed, but global registry/core ownership and config-selection gaps bound the claim.
5. `C23-05`: NLR is declared but unregistered; selection falls back to WS while returning success and is not NLR execution.
6. `C23-06`: the historical registry did not give callers a complete contract for ownership and failure at capacity.
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

**Public-pin rulings on the same IDs**

| Historical ID | What the public evidence now permits | Where to stop |
|---|---|---|
| `C23-02` | The tested nondefault geometry reached initialization and an eight-tile MMA; `test-config` completed 31/31. | No retrospective diagnosis of the v1 stack failure. |
| `C23-03` | Mode, depth and DMA width are retained and consumed on the tested routes. OS is depth-insensitive in this estimate. | A parsed queue depth or rounding mode need not be effective. |
| `C23-04` | Valid names map to WS/OS/RS; matched WS/OS file runs, a post-init RS setter and separate alternating core calls distinguish the owners. | Direct state and saved core state can differ. Neither attention descriptor selection nor concurrency follows. |
| `C23-05` | NLR remains blocked as an executable mode. Invalid mode strings fail loading; invalid direct IDs return `-1` without replacing the active object. Core NLR rejection preserves the core selection. | Do not describe those checked requests as successful WS fallback or extend the result to unchecked initializers. |
| `C23-06` | Static registration and stable pointers support the built-in routes. | An eight-slot registry with silent capacity failure is not an open, versioned ABI. |
| `C23-14` | Read documentation against the exact consumer and test at its pin. | A repaired C path does not validate every advertised interface. |
| `C23-17` | The single-state sweep rejects wrong identity and a wrong expected word. The three-core sweep checks retained modes and peer equality. | The original proposition that a target and printed rows suffice is still blocked. Neither aggregate owns either sweep; printed multicore cycles are not gated there. |

[Return to contents](../../README.md)
