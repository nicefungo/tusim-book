# Chapter 21 — Framing and Required Evidence Plan

- Date: 2026-08-18
- Status: **framing gate closed; required evidence plan complete; drafting blocked**
- Tusim source pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Governing plan: [`../PLAN.md`](../PLAN.md)
- Chapter 20 closure: [`handoffs/2026-08-18-chapter-20.md`](handoffs/2026-08-18-chapter-20.md)
- Post-Chapter-20 coverage checkpoint: [`whole-book-coverage-review-2026-08-18-after-ch20.md`](whole-book-coverage-review-2026-08-18-after-ch20.md)
- Reproduction script: [`../experiments/ch21_framing_recon.py`](../experiments/ch21_framing_recon.py)
- Retained reproduction: [`chapter-21-framing-reproduction.log`](chapter-21-framing-reproduction.log)
- Review dispositions: [`chapter-21-framing-review-dispositions.md`](chapter-21-framing-review-dispositions.md)

## Gate question

Given a set of architecture alternatives and a desired comparison, **how should a reader construct a sweep whose varied axis reaches the intended mechanism, whose metric has a named producer and valid comparison domain, and whose controls, sensitivity analysis, counterexamples, and retained provenance justify the stated decision boundary?**

This is a sweep-construction decision, not a catalogue of Tusim reports and not a synthesis of which architecture is best.

## Opening architecture question

**When does a table of many configurations become a trustworthy experiment rather than a deterministic spreadsheet, mislabeled route, or executable program that cannot falsify its own conclusion?**

## Reader decision

For a proposed sweep, the reader must be able to:

1. state one falsifiable architecture question and the decision the sweep is meant to inform;
2. define realistic alternatives, a baseline, controlled variables, workload coverage, and explicit exclusions;
3. prove that every varied axis reaches the intended parser, runtime state, model, estimator, or formula;
4. name the metric producer, interval, units, clock/reset assumptions, comparison domain, and fidelity rung;
5. choose positive, negative, mutation, seed/order, and boundary controls that can disprove an invalid comparison;
6. test sensitivity and construct counterexamples around thresholds, rankings, and claimed regimes;
7. separate executable behavior, linked analytical estimators, standalone formulas, and report prose;
8. retain the pin, inputs, parameter matrix, commands, outputs, manifests, toolchain, and claim limitations needed for reproduction;
9. state the strongest local decision the sweep supports without turning it into a portfolio-wide conclusion.

## Preconditions corrected before reconnaissance

`PLAN.md` was corrected before opening new Chapter 21 research. It now:

- marks Chapter 20 complete in both the status table and architecture;
- records the completed Part VI checkpoint and curated publication tip `1fd98da`;
- removes the obsolete Chapter 15 “local closure only, publication pending approval” status;
- makes Chapter 21 explicitly next and states the Chapter 21/22 ownership boundary.

## Fresh read-only whole-tree reconnaissance

The framing reproduction read the detached clean Tusim checkout statically and used `git archive` for all builds and executions. It verified the source as detached, clean, and pinned both before and after. The final script hash is recorded in the log; all selected Make recipes were dry-run first and contained no fixed host-global `/tmp` paths.

### Comparable inventory

At the pin:

- 21 tracked C sources have `sweep` in the filename;
- 20 have source-linked Make rules; `tests/test_int8_sweep.c` has no Make rule and was compiled manually in the disposable archive;
- `tests/test_conv_pool_cascade.c` self-identifies as a sweep despite lacking the filename token, and `tests/test_benchmark.c` is the adjacent comparative benchmark harness; both have focused Make rules;
- none of these 22 source-linked sweep/exploration targets is a prerequisite of aggregate `make test`;
- the source contains 46 tracked exploration reports, excluding `IMPLEMENTATION_BACKLOG.md`;
- 35 reports mechanically expose a question heading, 30 expose a hypothesis heading, and 30 expose a method/methodology/cycle-model/harness heading;
- only 13 reports name an explicit C sweep or Python sweep-harness path, and 16 contain a reproducible-looking `make test-*` or `python scripts/...` command; references to `scripts/gen_config.py` are configuration-generation provenance, not sweep-harness provenance;
- no tracked source path contains `manifest`, and none of the 46 report bodies uses the word “manifest”;
- `scripts/sweep_aspect_ratio.py` is the only tracked Python filename with a `sweep` token.

These are relation-specific counts. A filename token is not a semantic producer class; a Make rule is not aggregate or CI ownership; a question heading is not a falsifiable hypothesis; and an exit-zero program is not a trustworthy sweep.

### Producer and reachability surfaces

A mechanical call inventory partitions the 21 C sweep-token sources plus the two adjacent C exploration harnesses into:

- 19 that call at least one externally defined `tu_*` function; and
- four local-formula programs with no external `tu_*` call: INT8 throughput, interconnect switching, interconnect topology, and fused-activation overhead.

The 19-source group is still heterogeneous. It includes functional engines, stateful lifecycle APIs, static transforms, codecs, and analytical estimator APIs. “Cmodel-linked” therefore does not imply that the swept axis reaches an ordinary runtime workload or that the printed quantity is elapsed model time. The four local-formula programs can be reproducible and useful, but they cannot be relabeled as cmodel execution.

The later evidence audit must classify every selected result by this chain:

```text
question and decision
  → alternatives and controlled matrix
  → axis declaration
  → effective consumer or equation input
  → workload route and state transition
  → metric producer / interval / units / fidelity
  → output row and status
  → sensitivity, boundary, and counterexample controls
  → manifest-bound claim and limitation
```

### Bounded live reachability

In one disposable exact-pin archive:

- the literal 22-pair source→target relation set matched, and a count-preserving benchmark/cascade prerequisite swap was rejected;
- `make all` exited zero;
- all 22 source-linked sweep/exploration targets built, ran, and exited zero;
- the manually compiled INT8 sweep exited zero;
- the Python aspect-ratio harness exited zero and printed its declared 120-configuration matrix;
- a real disposable-source mutation changed the declared matrix size to 119, and the framing observation predicate rejected it;
- a separately injected inventory-predicate failure exited nonzero with the intended diagnostic while the `finally` path still emitted one pinned, detached, clean `SOURCE_STATE after` marker;
- the final status vector contains 24 zero statuses (22 Make targets, manual INT8, and Python aspect-ratio);
- output digests, line counts, and bounded tails are retained in the framing log.

This establishes build/runtime reachability, not correctness. Several sources return zero after printing conclusions without turning mismatches or failed rows into process failure. For example, the dataflow sweep's comparison result changes only printed text before unconditional `return 0`, while the normalization sweep prints a `FAILED` row and continues to unconditional success. Chapter 20 owns why such a green gate cannot authorize a claim; Chapter 21 owns how a sweep must be redesigned so controls and status are part of the experiment.

### Immediate methodological counterexamples

1. **Axis labels can outrun effective state.** `test_dataflow_sweep.c` labels three core runs WS/OS/RS and calls `tu_set_dataflow()` after creating each core. Prior executable Chapter 7 evidence shows core swap-in can restore the core snapshot's dataflow; Chapter 21 must freshly trace and discriminate effective selection instead of trusting labels.
2. **A linked program can print a separate formula portfolio.** The dataflow sweep combines functional comparisons with handwritten timing equations. The executable values and analytical rows need separate producers and separate claims.
3. **A report can be reproducible only in part.** The aspect-ratio Python script reproduces a 120-row matrix, but the report does not cite the script path, and its narrative validation points to `test-bench` rather than a retained command/output manifest.
4. **A zero status can be non-falsifying.** Many sweep programs always return zero; status must be coupled to claim-critical controls and mutated to prove failure propagation.
5. **A large matrix can still have one effective sample.** Fixed seeds, a single workload family, one formula, or a repeated deterministic vector set do not establish ranking stability or sensitivity.
6. **No source manifest closes report provenance.** Reproduction currently depends on source paths and prose commands rather than a pin-locked parameter/output/claim bundle.

## Ranked scope candidates

| Rank | Candidate | Reader decision | Evidence density and continuity | Principal cost/risk |
|---:|---|---|---|---|
| **1** | **Sweep chain of custody: from falsifiable question to bounded decision** | Decide whether an architecture comparison is controlled, reached, sensitivity-tested, counterexample-resistant, and reproducible enough to support one stated decision | Highest. Uses all producer classes, report/harness gaps, executable route discriminators, analytical recomputation, manifests, and prior chapter boundaries without making portfolio conclusions | Broad scope can become a checklist or report catalogue unless one decision chain organizes every section |
| **2** | Executable versus analytical reconciliation | Decide whether rows labeled from one experiment actually come from the cmodel, a linked estimator, a local formula, or prose-only arithmetic | Very strong negative evidence and a clean fidelity story; directly addresses 19 linked-call versus four local-formula sources in the 23-source exploration inventory | Too narrow: under-teaches controls, workload design, sensitivity, counterexamples, and reproducibility |
| **3** | Sensitivity and crossover experiments | Decide whether a threshold, ranking, or regime survives nearby parameters, alternative workloads, and counterexamples | Strong report portfolio with PE, bus, K, memory, topology, precision, and lifecycle axes; pedagogically concrete | Drifts into Chapter 22 conclusions and can silently inherit unverified producers |
| **4** | Reproducible exploration bundles | Decide whether a report can be regenerated from a pin-locked matrix, executable command, output, validator, and manifest | Strong contrast: 46 reports, sparse harness links, no source manifests; connects naturally to book evidence practice | Too procedural by itself and risks repeating Chapter 20 evidence-preservation architecture |

## Scope decision

**Select Candidate 1: Sweep chain of custody from a falsifiable question to a bounded reader decision.**

It is the only candidate that covers construction, controls, sensitivity, counterexamples, fidelity, and reproducibility while preserving Chapter 22 for portfolio conclusions. Candidate 2 becomes the producer/fidelity stage of the chain. Candidate 3 becomes the sensitivity and counterexample stage. Candidate 4 becomes the retained-provenance stage rather than the chapter spine.

The chapter's decision template is:

```text
What decision will this sweep inform?
  → What result would falsify the hypothesis?
  → Which alternatives and workloads are realistic?
  → Which variables are controlled and which are swept?
  → Does each axis reach the intended mechanism?
  → Who produces each metric, in what domain and fidelity rung?
  → Which controls expose label, route, status, seed, and formula defects?
  → Does the ranking survive sensitivity and counterexamples?
  → Can a clean exact-pin archive reproduce the claimed rows?
  → What local decision is authorized, and what broader conclusion is not?
```

## Inclusions

- falsifiable question, hypothesis, and predeclared reader decision;
- realistic architectural alternatives rather than one presumed fastest design;
- baselines, controlled variables, workload matrices, boundary points, and counterexamples;
- axis declaration-to-effective-consumer reachability;
- executable functional/stateful paths, linked estimators, local analytical harnesses, and report-only arithmetic as separate evidence classes;
- producer, interval, units, clock/reset, formula, and fidelity metadata imported from Chapter 17;
- positive, negative, mutation, seed/order, and failure-propagation controls imported as authorization requirements from Chapter 20;
- sensitivity of rankings, crossovers, and claimed regimes;
- exact-pin archives, canonical parameter matrices, raw outputs, hashes, manifests, validators, toolchain, and limitation registers;
- trade-offs across performance, area/power, accuracy, control complexity, compiler/runtime implications, verification cost, and fidelity when supported by the selected sweep question.

## Explicit exclusions

- no portfolio-wide claim about the best PE geometry, dataflow, memory, precision, topology, retention mode, or operator composition; Chapter 22 owns reconciled conclusions;
- no new metric-producer taxonomy, counter semantics, cycle-domain composition, or calibration claim; Chapter 17 remains authoritative;
- no general tutorial on why evidence is or is not authorized; Chapter 20 remains authoritative for claim boundaries, controls, status propagation, and retained provenance;
- no reopening of Chapters 19–20 or the Chapters 8/10/14 supplement backlog;
- no composed ONNX/compiler/scheduler/allocator/queue/runtime path from shared types, report intent, labels, archive membership, or passing sweeps;
- no implication that “cmodel-linked,” `return 0`, many rows, or a report date establishes integration, sensitivity, or reproducibility;
- no manuscript drafting before the source/claim ledger, fail-closed audit, skeptical predraft review, and post-review evidence seal close.

## Ownership boundaries

- **Chapter 17:** owns producer identity, interval, units, clocks, reset, denominator, and fidelity. Chapter 21 imports those fields into every sweep row.
- **Chapter 20:** owns evidence authorization, discriminating controls, unsafe-green interpretation, status propagation, and retained provenance. Chapter 21 applies those requirements to experiment construction.
- **Chapter 21:** owns sweep questions, alternatives, controls, axis reachability, workload matrices, sensitivity, counterexamples, comparison validity, fidelity-aware construction, and reproducibility.
- **Chapter 22:** owns what the reconciled exploration portfolio teaches across domains. Chapter 21 may use bounded worked examples but may not promote them to portfolio conclusions.
- **Chapter 23:** owns how to add or extend a setting/module/opcode/binding. Chapter 21 may detect unreachable axes but does not teach extension procedure.

## Required predraft evidence plan

Drafting remains blocked until all evidence families below are complete, independently challenged, and sealed after review.

### E21.1 — Complete sweep/report relation inventory

Create a fail-closed machine-readable inventory of:

- all 21 C sweep-token sources plus semantic sweep programs without that token;
- source → Make rule → aggregate/CI membership → actual executed command;
- report → question/hypothesis → parameter matrix → harness/equation → output rows → stated conclusion;
- report/harness links, command presence, source hashes, and manifest presence;
- exact producer class for every selected worked row.

The gate must encode the literal source→target pair set for all 20 Make-linked sweep-token sources and both adjacent exploration harnesses, retain the manual no-rule INT8 source as a separate exact singleton, and reject a count-preserving source/target rewire.

### E21.2 — Falsifiable question and decision schema

For every worked sweep, record:

- architecture question and null/counter hypothesis;
- decision the result may inform;
- alternatives retained and alternatives excluded;
- independent variable, controlled variables, workloads, boundary points, and sample/seed policy;
- predeclared disproof condition;
- safe local conclusion and unsafe broader conclusion.

A large matrix without a disproof condition is rejected.

### E21.3 — Axis reachability and composition discriminators

Trace declaration → parser/generator if any → runtime conversion/state → consumer/equation input → observable effect. Required focused cases:

1. **Dataflow label/effective-route discriminator:** distinguish process-global selection, core snapshot swap-in, functional output, and handwritten analytical rows. Use nonsymmetric data and an observable active-plugin/state discriminator; do not infer execution from labels.
2. **Rounding/seed discriminator:** prove which conversion or arithmetic stage the mode and stochastic seed affect; repeat fixed and changed seeds; separate deterministic replay from independent samples and from application accuracy.
3. **Context/retention estimator discriminator:** hand-recompute representative FULL/LIVE/CONTROL and bandwidth rows from the pinned equation while preserving Chapter 18's legal-boundary limitations.
4. **Analytical-script discriminator:** reproduce the aspect-ratio matrix from the tracked Python harness, compare report-critical rows and formulas, and mutate an axis/formula so the validator rejects stale output.
5. **Negative compiler/runtime composition check:** require zero unsupported bridge claims even when report prose proposes compiler action.

### E21.4 — Metric and fidelity register

For every quantitative row selected for the manuscript, bind:

- exact producer and source path;
- interval and reset/state assumptions;
- numerator, denominator, units, and clock;
- executable effect versus analytical estimate;
- modeled and omitted costs;
- calibration rung and uncertainty/safe comparison domain.

No heterogeneous cycle domains may be added. A linked estimator and a functional call in the same process remain separate producers unless a direct common-timeline relation is proved.

### E21.5 — Controls and fail-closed status

The canonical evidence must include:

- baseline and positive control;
- negative or boundary control that changes the expected relation;
- axis mutation proving the intended consumer matters;
- output/status mutation proving a failed row makes the runner nonzero;
- order/permutation control where mutable global state can leak between rows;
- fixed-seed replay plus changed-seed or independent-vector control where randomness is claimed;
- exact output completion marker and absence of claim-critical `FAIL`, `ERROR`, or stale-row acceptance.

At least one existing unconditional-success sweep must be mutated into a discriminating failure and rejected by the outer runner.

### E21.6 — Sensitivity, crossover, and counterexample plan

For each threshold or ranking used pedagogically:

- sweep both sides of the boundary and include the exact transition point;
- perturb at least one workload dimension and one architecture parameter not used to derive the conclusion;
- report ties and reversals rather than smoothing them away;
- construct one counterexample that defeats the naive global recommendation;
- distinguish a stable regime from a single-grid observation;
- retain materially distinct alternatives and state performance, area/power, accuracy, complexity, compiler/runtime, verification, and fidelity costs where evidence exists.

The result is a method demonstration, not Chapter 22 synthesis.

### E21.7 — Reproducibility and manifest closure

The canonical runner must:

- verify the exact Tusim pin and source hashes;
- build only in a disposable archive and verify source state in `finally`;
- record compiler, make, Python, architecture, locale, commands, parameter matrices, seeds, and environment overrides;
- retain raw output separately from parsed tables;
- bind every retained file in an inner manifest and bind the complete bundle in an outer manifest;
- require one literal, unique member set containing the relation inventory, source audit, focused probes, mutations, runner, validator, canonical parameter matrices, bundled input copies, raw outputs, parsed tables, formula recomputations, source-and-claim ledger, limitation register, skeptical-review disposition, source hashes/pin, commands, environment/toolchain record, and finalization/validation logs;
- reject missing, extra, duplicate, or externally referenced mutable inputs and checksum-verify both manifest layers;
- reject missing, extra, changed, reordered where order is semantic, and stale report rows;
- rerun the validator under normal and optimized Python with real assertion-source mutation;
- negative-control an early inventory failure and later manifest and validator failures; each must exit nonzero with the intended diagnostic while a unique `SOURCE_STATE after ... detached=1 dirty_entries=0` marker proves the pinned checkout was still checked in the failure path;
- preserve failed/superseded runs rather than rewriting evidence.

### E21.8 — Literature and foundations plan

Before drafting, add verified primary-source support for:

- experimental design and sensitivity analysis for computer architecture;
- design-space exploration methodology and multi-objective/Pareto reasoning;
- benchmark/workload representativeness and measurement pitfalls;
- reproducible computational experiments and artifact manifests;
- where useful, primary tooling papers for calibrated cross-model comparisons.

Repository reports remain evidence about Tusim's historical exploration, not the sole authority for general methodology.

## Predraft claim families

The source-and-claim ledger must at minimum cover:

1. sweep taxonomy and actual build/runtime reachability;
2. question/hypothesis/decision alignment;
3. alternative and control completeness;
4. axis effectiveness and negative reachability;
5. metric producer/units/fidelity;
6. workload and seed representativeness;
7. sensitivity and crossover stability;
8. counterexamples and ranking reversals;
9. fail-closed status and mutation evidence;
10. report-to-harness reconciliation;
11. reproducibility manifests and toolchain;
12. explicit Chapter 17/20/22 and compiler/runtime boundaries.

Every claim requires `verified`, `qualified`, `rejected`, or `blocked` status and verbatim limitation wording before sealing.

## Risk-register disposition

- **Chapter 21/22 repetition — triggered and resolved by ownership:** Chapter 21 teaches construction and validation; Chapter 22 alone synthesizes portfolio conclusions.
- **Broad synthesis becoming a catalogue — triggered and resolved provisionally:** one chain-of-custody reader decision organizes the chapter; directories, reports, and sweep families are bounded examples.
- **Chapter 17 overlap — triggered and resolved by import:** producer/interval/unit/fidelity fields are mandatory inputs, not retaught semantics.
- **Chapter 20 overlap — triggered and resolved by application:** Chapter 20's evidence rules are applied to sweeps; the verification taxonomy and unsafe-green tutorial are not repeated.
- **Broken compiler path — triggered by report recommendations and resolved negatively:** no compiler/runtime composition is admitted without a repository-contained nontrivial lowering that links, runs, and verifies output.
- **Source-edition drift — not triggered:** `edition.yaml` and the live source remain at `e918c80`.
- **Stable numbering — not triggered:** retain Chapter 21 and the 23-chapter architecture.
- **Completed-chapter supplements — reviewed, not triggered:** Chapters 8/10/14 remain a separate governed work unit after Chapters 21–23 unless a proven prerequisite changes the plan.

## Framing gate

Framing can close only when all are true:

- [x] book `main` and Tusim detached pin/cleanliness verified live;
- [x] stale Chapter 20/15/21 `PLAN.md` entries corrected before research;
- [x] fresh whole-tree inventory covers executable sweeps, analytical harnesses, reports, manifests, producer classes, and build/runtime reachability;
- [x] all source execution occurred in a disposable exact-pin archive and source state was verified before and after;
- [x] at least three evidence-backed candidates were ranked before selection;
- [x] selected scope has one reader decision, explicit inclusions/exclusions, and ownership boundaries;
- [x] required predraft evidence families and focused discriminators are explicit;
- [x] plan risks are resolved or explicitly deferred;
- [x] reproduction script and complete combined log are retained;
- [x] independent skeptical framing review completed and all valid findings reconciled;
- [x] final reproduction rerun after review amendments;
- [x] framing governance/status committed as the coherent Chapter 21 framing checkpoint.

Even after this framing gate closes, **manuscript drafting remains blocked**. The next work unit must create the Chapter 21 source-and-claim ledger, implement the fail-closed audit and focused probes/mutations, conduct skeptical predraft review, and issue a post-review evidence seal before writing chapter prose.
