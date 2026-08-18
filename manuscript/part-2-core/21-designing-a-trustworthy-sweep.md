# Chapter 21 — Designing a Trustworthy Sweep

A sweep is not trustworthy because it prints many rows. It becomes useful when every row belongs to an experiment whose question, varied axes, effective consumers, metric producers, controls, sensitivity range, failure status, and provenance are explicit. Without that chain, an executable program can compare labels rather than mechanisms, a linked model can print an unrelated handwritten equation, and a reproducible table can preserve a stale conclusion perfectly.

This chapter asks one architecture question:

> When does a table of configurations become a controlled experiment that can inform one bounded design decision rather than a deterministic spreadsheet, a mislabeled route, or an overextended report?

At Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25`, the answer is concrete. The tree contains 21 C files with `sweep` in the filename, two adjacent semantic or comparative harnesses, 22 literal source-to-Make-target relations, one no-rule singleton, 46 exploration reports, and one sweep-named Python script. Those counts describe different relations. They do not say which alternatives actually execute, whether a result is functional or analytical, whether a program can fail, or whether a report can be regenerated.

The discipline developed here is a **sweep chain of custody**:

```text
local decision and falsifiable question
  → realistic alternatives, workloads, and controls
  → declared axis and effective consumer
  → producer, interval, units, state, and fidelity
  → raw row and fail-closed status
  → sensitivity, boundary, and counterexample cases
  → exact-pin reproduction package
  → safe local conclusion and unsafe broader conclusion
```

Every arrow is part of the experiment. No number of rows repairs a missing arrow.

## Learning objectives

After completing this chapter, the reader should be able to:

1. state one falsifiable architecture question and the local decision a sweep may inform;
2. distinguish lexical sweep names, Make ownership, aggregate selection, process execution, and trustworthy experiment status;
3. select realistic alternatives, controlled variables, workload cases, boundary points, and explicit exclusions;
4. trace a varied axis from declaration through state to an observable effective consumer;
5. keep executable effects, linked estimators, local formulas, and report prose as separate evidence classes;
6. import producer, interval, units, clock, reset, formula, and fidelity from Chapter 17 without inventing a common timeline;
7. apply Chapter 20’s positive, negative, mutation, order, seed, and status controls to sweep construction;
8. test both workload and architecture sensitivity, including ties, reversals, and counterexamples;
9. preserve per-case rows and state aggregation, normalization, missing-case, and tie policies explicitly;
10. retain an exact-pin evidence package whose manifests, validator, failure paths, and review state are themselves checked;
11. state a bounded conclusion without selecting a portfolio-wide optimum or composing unsupported compiler/runtime paths.

## Prerequisite graph

```text
Chapter 4: declaration → parser → runtime → consumer
Chapter 7: direct dataflow routes and plugin-local estimates
Chapter 8: conversion modes and stochastic state
Chapter 17: producer + interval + units + clock/reset + fidelity
Chapter 18: retained-state modes and linked switch estimator
Chapter 20: claim boundary + controls + status + provenance
                                  │
                                  ▼
                    Chapter 21: sweep construction
                                  │
                                  ▼
                    Chapter 22: portfolio synthesis
```

Chapter 17 remains authoritative for what a metric means. Chapter 20 defines what evidence is required to authorize a claim. Chapter 21 applies those contracts while constructing a comparison. Chapter 22 alone owns preference rules, Pareto selection, and conclusions across the exploration portfolio. Chapters 19 and 20 remain closed; this chapter does not revive an ONNX-to-runtime narrative.

## Opening architecture question

Suppose a report contains three rows labeled WS, OS, and RS. Before asking which row is smallest, an architect must ask:

- Did each label select a different implementation at the point of execution?
- Is the reported value produced by that implementation, by another linked estimator, by a local formula, or only by prose arithmetic?
- Are the rows in one comparison domain?
- Which workload and architecture variables were held constant?
- What outcome would disprove the proposed recommendation?
- Does the ordering survive nearby shapes and architecture parameters?
- Would a mismatch make the governed run nonzero?
- Can another clean checkout reproduce the exact rows and limitations?

If the answer to the first question is no, sensitivity and statistics cannot rescue the comparison. If the answer to the producer question is unknown, even correct arithmetic may be assigned the wrong fidelity. If no result can fail, the sweep is a table generator rather than a decision gate.

---

## 21.1 Theory: a sweep authorizes a decision, not an architecture

Let a proposed local decision be \(D\). Define the following relations:

- \(Q\): the question and counter-hypothesis are falsifiable;
- \(A\): alternatives, exclusions, workloads, and controls are explicit;
- \(R\): each varied axis reaches its intended state or equation input;
- \(M\): each metric has a named producer and valid comparison domain;
- \(F\): failed, stale, or incomplete rows propagate nonzero status;
- \(S\): boundaries, sensitivity, ties, reversals, and counterexamples are retained;
- \(P\): pin, inputs, commands, outputs, manifests, toolchain, and limitations are bound.

Then the sweep can support \(D\) only when

\[
\operatorname{SweepAuthorized}(D)=Q\land A\land R\land M\land F\land S\land P.
\]

This is a conjunction, not a score. A large matrix cannot compensate for an ineffective axis. Exact manifests cannot make incompatible cycle domains additive. A passing executable route cannot validate a separate report formula. One failed relation narrows or blocks the decision.

### Start from the decision and disproof condition

A useful question is not “what happens if every knob changes?” It names the decision and what would defeat the intended interpretation. Compare:

- descriptive: “sweep dataflows over several K values”;
- falsifiable: “for a fixed \(M=N=128\) formula family, does WS-versus-OS ordering remain under selected K and array-shape perturbations, and do the labels reach distinct executable routes?”

The second form separates two claims: formula sensitivity and route effectiveness. A labeled row whose active plugin differs from its label disproves an executable comparison even when its arithmetic table is internally consistent.

The Chapter 21 decision schema records, for each worked case, question, counter-hypothesis, decision, alternatives, exclusions, independent and controlled variables, workloads, boundary points, seed policy, disproof condition, safe conclusion, unsafe conclusion, objective direction, constraints, feasibility, aggregation, baseline, normalization, missing-case policy, tie policy, and multiobjective status.

A sweep should make these choices before looking at the preferred row. Otherwise, the experiment can quietly redefine its denominator, omit losing workloads, or move a threshold after observing results.

### Alternatives must be realistic and materially distinct

A comparison should preserve alternatives that represent plausible implementation choices in different regimes. That does not mean every declared enum or report label belongs in the matrix. An alternative needs a reachable producer and a stated cost surface. Depending on the question, that surface may include performance, area or power implications, accuracy, control complexity, compiler/runtime burden, verification cost, and fidelity.

An unavailable alternative can still be listed as excluded or future work. It must not be silently treated as executed. Similarly, the apparent winner under an analytical equation is not a physical recommendation when queueing, routing, calibration, or continuation costs are omitted.

### Keep per-case evidence before aggregation

A sweep matrix is many observations, not automatically one score. Per-workload rows should be retained before any summary. Aggregation needs a named baseline, normalization, weighting, denominator, missing-case rule, objective direction, and tie policy. Fleming and Wallace show why normalized benchmark ratios can be misleading when summarized with an inappropriate mean; no universal aggregation rule replaces metric-specific reasoning ([Fleming and Wallace 1986](https://doi.org/10.1145/5666.5673)).

The worked Chapter 21 cases deliberately use no portfolio aggregation. Rows remain per workload and configuration, missing cases fail closed, and exact ties are reported. Multiobjective and Pareto methodology is introduced as a reason to retain conflicting objectives, but no nondominated portfolio is computed here. NSGA-II is evidence that a diverse nondominated set and a separate preference rule are legitimate methodological objects, not evidence that any Tusim point is accurate or feasible ([Deb et al. 2002](https://doi.org/10.1109/4235.996017)).

## 21.2 Source map: sweep producers and evidence roles

The relevant source surfaces are:

| Role | Repository-relative surface | Safe use here |
|---|---|---|
| build and relation inventory | `Makefile` | literal source→target and aggregate relations |
| labeled dataflow sweep | `tests/test_dataflow_sweep.c` | functional calls and sweep-local handwritten equations, kept separate |
| direct dataflow execution | `tu_cmodel/tu_core.c`, `tu_cmodel/compute/dataflow/*.c` | effective core route, output, and plugin-local estimates |
| rounding sweep and conversion | `tests/test_rounding_sweep.c`, `tu_cmodel/tu_precision.c`, `tu_cmodel/rounding.c` | conversion-code and seed/order discriminators |
| context sweep and estimator | `tests/test_context_switch_sweep.c`, `tu_cmodel/infra/tu_context.c` | linked retained-state equation under Chapter 18 limits |
| aspect-ratio harness | `scripts/sweep_aspect_ratio.py` | deterministic local formulas and a 120-row matrix |
| historical interpretation | `docs/exploration/*.md` | report prose and report-local equations, not execution by themselves |
| canonical evidence | `experiments/runs/20260818-ch21-postreview-v8/` | exact corrected inputs, outputs, mutations, manifests, and validation |

The whole-tree inventory found:

```text
C sources with “sweep” in filename            21
adjacent semantic/comparative C harnesses       2
literal source→Make-target pairs               22
exact no-rule singleton                         1
exploration reports                            46
reports with question heading                  35
reports with hypothesis heading                30
reports with method-like heading               30
reports naming an explicit harness             13
reports with reproducible-looking command      16
reports using “manifest”                        0
```

The no-rule singleton is `tests/test_int8_sweep.c`. None of the 22 source-linked exploration targets is a prerequisite of aggregate `make test`. A disposable exact-pin archive built and ran all 22 targets, manually compiled and ran the singleton, and ran the Python aspect harness. This establishes bounded process reachability, not correctness or ordinary-runtime integration.

The inventory also distinguishes semantic sweeps without the filename token. `tests/test_conv_pool_cascade.c` identifies itself as a sweep, while `tests/test_benchmark.c` is an adjacent comparative harness. A lexical classifier would miss both. Conversely, a file containing `sweep` can still be a local formula program. Of the 23 C exploration sources, 19 call at least one externally defined `tu_*` function and four use local formulas without an external `tu_*` call. Even the 19 are heterogeneous: they include functional engines, lifecycle APIs, static transforms, codecs, and linked analytical estimators.

The inventory therefore supplies candidate relations, not a trust label. Its exact literal source-target set is mutation-tested with a count-preserving rewire. Cardinality stays 22; the gate still rejects the changed relation.

## 21.3 Construct the question, alternatives, and matrix

A compact pre-run contract can be written as:

```text
Decision:
Question:
Counter-hypothesis:
Alternatives / excluded alternatives:
Primary-matrix independent variables:
Primary-matrix controlled variables:
Secondary sensitivity variables:
Workloads and boundaries:
Seed/order policy:
Metric producer and comparison domain:
Disproof condition:
Safe local conclusion:
Unsafe broader conclusion:
Objectives and directions:
Constraints and feasibility rule:
Aggregation, baseline, and normalization:
Missing-case and tie policy:
Multiobjective method/status:
```

Four worked families instantiate that contract.

### Dataflow route versus formula

The alternatives are WS, OS, and RS; NLR and physical RTL dataflows are excluded. The route discriminator uses a nonsymmetric \(2\times3\) by \(3\times2\) multiplication, while the primary formula matrix uses \(128\times128\times K\) at a fixed \(16\times16\) array. Requested label and K are primary-matrix variables; M, N, PE geometry, bus width, and pipeline depth are primary controls. A separate report-local sensitivity subexperiment varies PE rows and columns together across 8, 16, and 32. The disproof condition is any labeled row whose effective core route differs from its label, or any formula row presented as executable output.

### Rounding mode and seed

The alternatives are RNE, RTZ, stochastic seed 12345, and stochastic seed 54321. The workload is 64 conversions of 1.0007 under an explicit seed/order policy. Application inference accuracy and training convergence are excluded. The experiment fails if RNE equals RTZ on the discriminator, same-seed replay drifts, or a changed seed cannot alter the vector.

### Retention estimator

The alternatives are `FULL`, `LIVE25`, and `CONTROL`: `LIVE25` is the 25% LIVE-prefix fixture and `CONTROL` is the CONTROL-only fixture from Chapter 18. Total SRAM capacity varies across 128, 256, and 512 KiB, while bandwidth varies across 16, 32, and 64 B per modeled cycle. The 100-cycle fixed term, two-context switch, and caller-established legal boundary are controlled. Arbitrary dirty-block policies and a physical context-store implementation are excluded. Any row that disagrees with the linked equation is a failure; a claim that `CONTROL` is end-to-end fastest is outside the experiment.

### Aspect-ratio formula

The alternatives are aligned, remainder-4, remainder-8, and near-aligned shapes. M and N vary in the primary matrix, while \(K=128\), a \(16\times16\) PE array, pipeline depth 2, and 32 B/cycle are primary controls. A secondary sensitivity subexperiment varies pipeline depth across 1, 2, and 4 and bus width across 16, 32, and 64 B/cycle. Runtime execution and compiler padding policy are excluded. Independent recomputation disagreement or a retained row that violates the report’s global prose bound disproves the broad recommendation.

These cases demonstrate method rather than portfolio selection. Workload selection should reflect behavioral diversity and state its represented dimensions; established suites can still be redundant or imbalanced ([Eeckhout et al. 2003](https://doi.org/10.1109/MC.2003.1178050); [Phansalkar et al. 2007](https://doi.org/10.1145/1250662.1250713)). A sweep of many nearby shapes can still represent one narrow behavior family.

## 21.4 Prove that each axis reaches an effective consumer

A varied parameter is evidence only when its effect is traced:

```text
declaration → parser/generator → stored state → effective consumer
            → discriminating observable
```

For a local formula, the consumer is an equation input. For a linked model, it may be a callback or state transition. For a runtime route, labels and stored fields are insufficient; the observable must distinguish which implementation ran.

### Dataflow labels versus the core snapshot

`test_dataflow_sweep.c` requests a dataflow through process-global `tu_set_dataflow(df_id)` after creating each core. Later `tu_core_*` operations swap the core snapshot into global state. Newly initialized cores retain weight-stationary state. The canonical discriminator records:

```text
DATAFLOW_ROUTE requested_label=output_stationary process_global_before=1 core_snapshot_before=0 core_snapshot_after=0 effective_core=weight_stationary
DATAFLOW_EXEC tag=labeled_os active=weight_stationary delta=67 output=58,64,139,154
DATAFLOW_EXEC tag=active_os active=output_stationary delta=4 output=58,64,139,154
DATAFLOW_EXEC tag=active_rs active=row_stationary delta=36 output=58,64,139,154
```

All three direct routes produce `[58,64,139,154]` for the bounded normal-value matrix, but active plugin identity and linked-plugin cycle delta differ. Functional equality does not prove route equality. The row labeled OS in the original sweep executes WS after the core swap-in.

A real route mutation changes effective selection and must be rejected. This is stronger than checking that all three names appear or that `tu_set_dataflow()` returns success.

### Rounding reaches conversion, not each accumulation

For the bounded case, rounding mode reaches FP32-to-FP16 W/A conversion. The MMA plugins decode FP16 and accumulate FP32. The historical explanation that mode applies to each accumulation or an FP16 accumulator store is unsupported on this route.

The discriminator reports:

```text
ROUNDING_AXIS value=1.0007 rne=0x3c01 rtz=0x3c00 same_seed_equal=1 changed_seed_diff=1 seed12345_fnv=99a9ff040fc80ca3 seed54321_fnv=283bd184c961bcc2
RANDOMNESS_SCOPE fixed_seed_replay=1 changed_seed_vector=1 independent_application_samples=0 application_accuracy=0
ROUNDING_ORDER stable_case_seed_permutation_equal=1 single_seed_permutation_diff=1 stable_fnv=33c857eecbbc9f2f
```

Explicitly reseeding each case makes forward and reverse order agree. Carrying one seed through a permutation allows global PRNG history to change case outputs. The first stochastic row in the original sweep is not explicitly seeded and inherits prior global state. Order control is therefore part of the experiment, not a cosmetic rerun.

### Context scope and bandwidth reach a linked estimator

The linked context manager uses

\[
T_{switch}=T_{fixed}+\left\lceil
\frac{B_{save,out}+B_{restore,in}}{BW_{state}}
\right\rceil .
\]

For the retained 256-KiB cases at 32 B/cycle, the exact rows are:

```text
FULL      16,484 model cycles
LIVE25     4,196 model cycles
CONTROL      100 model cycles
```

At 16 and 64 B/cycle, FULL becomes 32,868 and 8,292. These observations prove equation sensitivity in the linked model. They do not create physical switch time.

### Aspect axes reach a Python equation

The tracked Python harness declares 12 M values, 10 N values, and \(K=128\), producing exactly 120 rows. Its main-row equations are local formulas:

\[
U=\frac{MNK}{\lceil M/R\rceil\lceil N/C\rceil RCK},
\]

\[
T_{local}=T_{fill}+T_{compute}+T_{drain}+T_{dma}.
\]

The axis mutation changes the declared matrix or formula and the outer gate rejects stale output. This establishes formula execution and row identity, not a Tusim runtime workload.

## 21.5 Bind producer, units, interval, and fidelity before comparison

Four evidence classes appear in the worked examples:

1. **executable** effects, such as active plugin identity, matrix output, or FP16 conversion codes;
2. **linked estimators**, such as plugin callbacks and the context manager’s switch equation;
3. **local formulas**, such as equations embedded in a C sweep or Python script;
4. **report prose**, including historical equations and conclusions.

A row’s minimum record is:

```text
producer class + exact producer + source path + formula/action
+ interval + reset/state + numerator + denominator + units
+ clock assumption + omissions + calibration/fidelity
+ aggregation + objective direction + tie handling + safe use
```

Chapter 17 owns these semantics. Chapter 21 uses them to decide which rows can be compared.

### Three dataflow cycle families

For \(M=N=128\), \(K=256\), three distinct producers yield:

| Producer | WS | OS | RS | Comparison boundary |
|---|---:|---:|---:|---|
| sweep-local equations | 26,624 | 22,528 | 24,640 | includes the sweep’s local DMA term |
| historical report equations | 21,536 | 21,504 | not reported | report-local arithmetic |
| linked plugin estimators | 81,920 | 20,480 | 50,176 | plugin-local estimates; no sweep-local DMA term |

These are not three measurements of one elapsed time. They differ in equations, included terms, and producer. The historical report’s WS-versus-OS delta remains 32 across retained K points, and its fractional difference decreases as K increases. That is a property of that report formula, not proof that OS executes or is physically faster.

The dataflow sweep’s field labeled `mTOPS` is also dimensionally unsafe as printed. Its expression computes MAC/cycle. At an assumed 1 GHz, a value of 204.8 corresponds to 0.2048 TMAC/s, or 0.4096 TOPS under two operations per MAC. A source label does not override units.

### Context cycles stay inside their estimator

The fixed and transfer terms belong to one linked context equation, so they may be added within that producer. They may not be added to plugin-local dataflow cycles or local aspect cycles. The modeled unit is a context-estimator cycle under a configured bytes-per-cycle parameter; no physical clock calibration is present.

### Throughput derived from the aspect formula

The Python harness derives

\[
P_{formula}=\frac{2MNK}{T_{local}/10^9}\frac{1}{10^{12}}
\quad\text{TOPS},
\]

under an explicit hypothetical 1 GHz clock and two operations per MAC. For \(M=N=16\), \(K=128\), `T_local=404`, so the formula gives approximately 0.1622 TOPS. This is a derived local-formula value, not measured throughput.

## 21.6 Controls and fail-closed status are part of the sweep

A trustworthy sweep needs controls that attack the chain rather than merely rerun the same rows.

| Control | Question answered | Chapter 21 instance |
|---|---|---|
| baseline/positive | can the intended route or formula run? | direct WS, expected formula rows |
| negative/boundary | does a discriminating alternative change the relation? | direct OS/RS, alignment remainder, RNE/RTZ |
| semantic route mutation | does effective selection matter? | altered dataflow route rejected |
| relation mutation | is literal membership gated? | count-preserving source-target swap rejected |
| formula/axis mutation | can stale rows survive changed inputs? | aspect matrix/formula change rejected |
| status mutation | does a printed mismatch reach outer status? | upstream zero-status mismatch rejected |
| order control | does mutable global state leak between cases? | forward/reverse stochastic permutation |
| seed control | is replay distinct from a changed vector? | same seed equal; changed seed differs |
| completion control | did the governed output finish? | exact PASS/summary markers required |
| provenance mutation | do manifests and validator fail closed? | digest, member, symlink, path, and AST controls |

The original dataflow sweep can print a comparison failure and still return zero. The outer runner therefore does not trust its exit status alone. It requires exact observations and mutates a real upstream success/mismatch path so that a failed row must make the governed run nonzero.

A claim-bearing runner must reject at least:

- source hash drift;
- a count-preserving relation rewire;
- changed or stale formulas and rows;
- route-label/effective-route disagreement when execution is claimed;
- printed `FAILED`, `ERROR`, or missing completion;
- missing, extra, duplicate, reordered-when-semantic, symlinked, escaping, or checksum-mismatched manifest members;
- optimizer-removable validator assertions;
- a pre-review or unresolved-review authority state.

Mytkowicz et al. demonstrate that environment and ordering can alter performance results without an obvious source change; deterministic models do not inherit every software benchmark hazard, but hidden mutable state still requires explicit order and reset controls ([Mytkowicz et al. 2009](https://doi.org/10.1145/1508244.1508275)).

## 21.7 Sensitivity must cross the claimed boundary

Sensitivity is not “more points.” The matrix must test the relation that supports the conclusion.

### Workload and architecture axes

A two-axis plan perturbs at least one workload dimension and one architecture parameter not used to derive the preferred statement:

- dataflow report formulas vary K across `1,16,32,64,256,1024` and array rows across `8,16,32`;
- aspect formulas vary M across `16,17,20,24,31,32`, then pipeline depth and bus width across `(1,32),(2,32),(4,32),(2,16),(2,64)`;
- retention varies saved bytes or scope across 128, 256, and 512 KiB, then state bandwidth across 16, 32, and 64 B/cycle.

This does not establish statistical representativeness or a physical optimum. It proves that the retained statement was challenged along two named dimensions.

### Exact transitions, ties, and reversals

The aspect workload totals for M `16,17,20,24,31,32` at the retained N and architecture are:

```text
404, 543, 570, 606, 669, 678
```

The matrix retains an exact useful-throughput tie for M=16 and M=24 under the same local formula—both are approximately 0.1622 TOPS under the hypothetical 1 GHz conversion—rather than breaking it arbitrarily. It also retains a reversal: padding M=20 to M=32 reduces useful throughput within the same local formula, despite removing underutilized tiles, because additional work and traffic outweigh the utilization change.

For the context model, a 10,000-cycle FULL budget is crossed between 52 and 53 B/cycle: the retained values are 10,183 and 9,993. FULL at 128 B/cycle ties LIVE25 at 32 B/cycle at 4,196 model cycles. A CONTROL ordering reverses if omitted reload cost exceeds 16,384 cycles. The reversal is a counter-hypothesis, not a modeled result, because reload is absent from the producer.

### Counterexamples defeat global recommendations

The historical aspect report states a global “≤3.8% overhead for any non-zero remainder” conclusion. Its own utilization formula gives M=40, N=16 on a 16×16 array:

\[
U=\frac{40}{\lceil 40/16\rceil16}=rac{40}{48}=0.8333,
\]

so waste is 16.7% for remainder 8. One retained point disproves the global bound. It does not imply that every report row is wrong; tested-grid arithmetic can remain useful after the broad conclusion is rejected.

The tracked script contains another internal discriminator. For M=20, N=48, the canonical main-row total is 1,382. A duplicate “worst edge utilization” section substitutes `2*pipeline_depth` for shape-dependent fill plus drain and gives 1,376. Reproducibility of both numbers exposes inconsistent formulas; it does not reconcile them.

Predictive-model DSE work motivates sampling, held-out validation, interaction analysis, and sensitivity, but its reported errors are study-specific and do not calibrate Tusim ([İpek et al. 2008](https://doi.org/10.1145/1328195.1328196); [Lee and Brooks 2006](https://doi.org/10.1145/1168857.1168881)). A surrogate can guide which points to test; it does not replace effective-route, boundary, and counterexample evidence.

## 21.8 Worked chain-of-custody decisions

### Case A: can the labeled dataflow sweep compare executable routes?

| Stage | Observation | Decision effect |
|---|---|---|
| question | do WS/OS/RS labels execute distinct routes? | falsifiable route claim |
| alternatives | WS, OS, RS; NLR excluded | bounded set |
| declared axis | `tu_set_dataflow(df_id)` | request exists |
| lifecycle | core swap-in restores snapshot | request may be overwritten |
| observable | labeled OS is active WS, delta 67 | executable labeled comparison rejected |
| positive control | direct OS active, delta 4 | OS separately reachable |
| second alternative | direct RS active, delta 36 | RS separately reachable |
| functional output | all yield `58,64,139,154` | bounded normal-value equivalence only |
| formulas | three producer families differ | separate analytical claims |
| mutation | effective route change rejected | route gate is discriminating |

Safe local conclusion: direct WS/OS/RS paths are separately reachable and produce the same bounded output, but the original labeled core rows do not establish three executed routes; each formula family must be analyzed on its own terms.

Unsafe conclusion: one dataflow is physically fastest or the labeled sweep measures its plugin cycles.

### Case B: does stochastic seed produce independent accuracy evidence?

| Stage | Observation | Decision effect |
|---|---|---|
| route | mode reaches FP32→FP16 conversion | conversion claim authorized |
| RNE/RTZ | `0x3c01` versus `0x3c00` | mode is effective for 1.0007 |
| same seed | exact vector replay | deterministic identity |
| changed seed | different vector digest | seed reaches conversion |
| order | reseed-per-case is permutation-stable | reset policy identified |
| scope | one 64-value conversion vector | no application distribution |

Safe local conclusion: mode and seed affect the bounded conversion vector reproducibly.

Unsafe conclusion: stochastic rounding is unbiased, improves training, or improves application accuracy.

### Case C: which retained-state alternative has lower modeled interruption?

Within the linked equation and the named legal boundary, `FULL`, `LIVE25` (the 25% LIVE-prefix fixture), and `CONTROL` (the CONTROL-only fixture) can be compared for exact saved-byte and bandwidth assumptions. `FULL` and `LIVE25` model different retained scopes; `CONTROL` omits bulk SRAM copy. The 100-cycle `CONTROL` value is therefore a lower equation result, not a complete continuation result. Reload, backing store, drainage, queue state, legal live-set production, and correctness after continuation remain outside the model.

The safe decision is conditional: if the caller can legally provide the retained-state semantics and if only this estimator’s terms matter, the rows show exact scope/bandwidth sensitivity. The unsafe decision is to deploy CONTROL because it is “fastest.”

### Case D: does aspect alignment justify compiler padding?

The formula supports exact utilization and local-cycle arithmetic for its declared rows. It also supplies its own counterexample to a global remainder bound and a padding reversal. No compiler is invoked, no transformed program runs, and no far-boundary result is checked. The safe conclusion is that alignment effects are non-monotonic inside this formula. The compiler recommendation is rejected.

## 21.9 Reproducibility requires layered closure

Reproducible computational research requires exact program versions, parameters, seeds, intermediate results, and claim-to-result links ([Sandve et al. 2013](https://doi.org/10.1371/journal.pcbi.1003285)). Availability of data and code still does not establish mechanism reachability or correct interpretation ([Stodden et al. 2016](https://doi.org/10.1126/science.aah6168)).

The Chapter 21 evidence package records:

- Tusim source pin and 21 selected source hashes;
- exact input commit and bundled input copies;
- commands, host architecture, compiler, Make, Python, locale, and environment;
- decision schema, metric register, seeds, and matrices;
- raw probe and aspect output separately from parsed JSON/CSV;
- source, relation, route, report-role, boundary, formula, and status mutations;
- source-state checks on success and injected failure;
- exact inner retained member list and checksums;
- outer manifest roots and derived validation receipts;
- normal and optimized validator executions;
- real validator-AST and frozen-input mutations;
- skeptical-review dispositions and the final Git seal shape.

The canonical run has 61 retained payload members. Its inner manifest binds those members plus `retained-files.txt`. The outer manifest binds five roots: the inner checksum file, its verification log, finalization log, and normal/optimized predraft-validation logs. Closure logs are derived receipts; the Git sealing commit binds the complete 71-file final run tree. These layers should not be described as a recursively self-checksummed manifest.

RFC 8493’s BagIt model usefully distinguishes payload manifests, tag manifests, completeness, and validity. It checks opaque bytes, not scientific correctness, provenance semantics, or resistance to every active attack ([RFC 8493](https://www.rfc-editor.org/rfc/rfc8493.html)). Chapter 21 therefore combines exact member sets with semantic mutations and independent review.

### Failure paths must preserve the source

All builds and execution occur in a disposable `git archive` of the pin. A `finally`-style source check records detached, clean, pinned state after the body and after injected early failure. The failure proof requires exactly one state line and the intended diagnostic. A source check only on the green path would not establish read-only behavior when a gate, manifest, or validator fails.

### Review changes authority

The provisional seal was green but skeptical review found producer conflation, incomplete metric records, missing semantic controls, weak manifest/path handling, unparsed governance state, and overstated Pareto and closure wording. Five failed post-review attempts are retained. Postreview-v6 later passed, but exact manuscript review found three semantic defects in its metric register and decision schema. Postreview-v7 corrected those defects, but final exact re-review found a false audit-report attribution and a self-confirming linked-plugin check. Both runs remain immutable history but are superseded. Only corrected postreview-v8 is the Chapter 21 authority.

This separation matters: a hash proves identity; a mutation proves one gate can reject one changed relation; a review challenges whether the chosen relation matches the claim. None substitutes for the others.

## 21.10 Alternatives and trade-offs in sweep architecture

There is no single sweep design that is cheapest and strongest for every decision.

| Sweep architecture | Strength | Principal cost | Best regime | Unsafe interpretation |
|---|---|---|---|---|
| exhaustive small grid | exact coverage of declared finite grid | scales combinatorially | small discrete spaces and boundaries | coverage outside the grid |
| one-factor-at-a-time | simple local effect attribution | misses interactions and order effects | debugging one effective knob | global sensitivity or causal independence |
| factorial or interaction-aware sample | exposes interactions | more rows and analysis | several reachable discrete/continuous axes | physical fidelity without calibration |
| random/space-filling sample | broader sampled domain | seed policy and coverage uncertainty | large spaces and surrogate training | independent samples from repeated fixed seeds |
| predictive surrogate | efficient interpolation and ranking proposals | fitting, held-out validation, extrapolation risk | costly producers with validated samples | mechanism reachability or causal proof |
| boundary/counterexample suite | strong falsification near claims | requires theory and targeted fixture design | thresholds and safety envelopes | representative portfolio by itself |
| linked-estimator sweep | uses maintained source equations | model-local omissions and calibration | equation sensitivity | elapsed physical time |
| local-formula harness | transparent and easy to reproduce | can drift from runtime implementation | analytical hypotheses | cmodel execution |
| exact manifest package | preserves identities and reruns | storage and governance overhead | release/chapter authority | semantic correctness by checksum |
| calibrated external comparison | stronger physical relevance | RTL/hardware access and mapping effort | high-risk performance/energy decisions | universal transfer beyond calibrated cases |

A production exploration system is modular: matrix generation, route execution, metric capture, row validation, sensitivity analysis, and packaging should be replaceable components with explicit interfaces. That modularity allows an architect to replace a local equation with a linked model or calibrated reference without pretending that old and new rows share a producer.

The objective is not maximum row count. It is the smallest experiment that can falsify the proposed local decision at the required risk level, plus enough neighboring and counterexample cases to define where the conclusion stops.

## 21.11 Verification evidence and canonical authority

The sole Chapter 21 predraft authority is:

```text
experiments/runs/20260818-ch21-postreview-v8/
```

It binds source pin:

```text
e918c80b6fce833cd1fcae97730fa841c2176f25
```

seal input commit:

```text
3e8ec2bbf64f9a85b8ffbfd9ca12ce2ccdef3379
```

and seal commit:

```text
f37e8582746f4159a2ed418b7f3eceba9e0847eb
```

The corrected retained source audit reports:

```text
CH21_SOURCE_AUDIT PASS pin=e918c80b6fce833cd1fcae97730fa841c2176f25 hashes=21 predicates=26 checks=48
```

The exact probe concludes:

```text
CH21_SWEEP_PROBE SUMMARY failures=0
```

That probe executes the linked WS, OS, and RS plugins at `M=128, N=128, K=256` in both O0 and O2 builds and requires `81,920`, `20,480`, and `50,176` model cycles. The source audit independently digest-binds the dispatcher and all three plugin implementations, while the formula probe derives the same totals from their per-tile fill, execute, and drain contracts rather than returning constants.

The formula gate concludes:

```text
CH21_FORMULA_PROBE PASS
```

The bundle retains byte-identical O0/O2 probe output, exact source-target and report inventories, four complete decision cases, nine singular metric records, normal and optimized body/outer validation, six normal plus six optimized manifest-hierarchy rejection cases, source-state proof on every retained failure path, and exact direct-child run-only Git sealing.

To validate the sealed evidence from the current clean book tree, use the bundle-local outer mode:

```bash
cd /home/zxy/Workplace/books/tusim-book
CH21_RUN_ID=20260818-ch21-postreview-v8 \
  python3 experiments/ch21_predraft_validate.py --outer
CH21_RUN_ID=20260818-ch21-postreview-v8 \
  python3 -O experiments/ch21_predraft_validate.py --outer
```

Both print a `CH21_PREDRAFT_VALIDATION PASS` line for postreview-v8. The historical post-seal receipts were run at the direct-child sealing commit `f37e8582746f4159a2ed418b7f3eceba9e0847eb`; `--postseal` is intentionally not a current-tree command after later chapter commits. Those receipts were:

```text
CH21_POSTSEAL PASS run=20260818-ch21-postreview-v8 head=f37e8582746f4159a2ed418b7f3eceba9e0847eb parent=3e8ec2bbf64f9a85b8ffbfd9ca12ce2ccdef3379 changed=71
```

## 21.12 Common failure modes

1. **Many rows mean strong evidence.** Matrix size does not establish a falsifiable question, effective axis, or representative workload set.
2. **A sweep filename defines a producer.** Lexical names miss semantic harnesses and include heterogeneous implementations.
3. **A Make rule means aggregate or CI ownership.** Rule, aggregate, CI, and execution are distinct relations.
4. **A linked program means every printed row comes from linked execution.** Linked calls and handwritten equations can coexist in one process.
5. **A label proves route selection.** Core swap-in can overwrite process-global dataflow selection.
6. **Equal output proves equal route.** The bounded WS/OS/RS fixture has equal output but distinct active plugin IDs and estimates.
7. **All cycle columns share elapsed time.** Sweep-local, report-local, and plugin-local dataflow equations are incompatible producers.
8. **A field name fixes its units.** The dataflow `mTOPS` expression is MAC/cycle and requires explicit conversion.
9. **Rounding applies everywhere.** The examined mode reaches input conversion, not each FP32 accumulation.
10. **Changed seed means independent sample.** It is one changed conversion vector, not a workload distribution.
11. **Reversing row order is enough.** Stateful randomness needs explicit per-case reset before permutation becomes a stable control.
12. **The smallest context row is end-to-end fastest.** CONTROL omits essential continuation costs.
13. **A Python script is a runtime workload.** The aspect harness executes standalone formulas.
14. **A report’s duplicate formulas must agree.** The two aspect sections produce 1,382 and 1,376 for the same shape.
15. **A tested grid proves a universal regime.** The remainder-8 counterexample rejects the report’s global 3.8% claim.
16. **Removing underutilization always helps.** Padding can reverse useful throughput in the same formula.
17. **Zero exit proves all rows passed.** Unconditional-success sweeps need outer observation and status gates.
18. **A manifest proves correctness.** It proves identity and exact membership, not semantics.
19. **A provisional green seal authorizes prose.** Skeptical review can require a new immutable authority.
20. **Pareto vocabulary selects a portfolio.** Objectives, constraints, feasibility, and preference rules must be exercised; Chapter 22 owns that work.
21. **A report recommendation creates a compiler bridge.** No executable compiler/runtime composition is present.

## 21.13 Fidelity box

**Verified at the pinned revision**

- exact 21 lexical C sweep sources, two adjacent harnesses, 22 literal source-target pairs, and one no-rule singleton;
- absence of all 22 exploration targets from aggregate `make test`;
- exact 46-report inventory and report-field counts;
- bounded process reachability in a disposable archive;
- effective dataflow route discrimination and direct WS/OS/RS controls;
- exact bounded matrix output `[58,64,139,154]` and plugin deltas 67/4/36;
- RNE/RTZ conversion codes, fixed-seed replay, changed-seed vector, and order/reset behavior;
- linked context equation rows and bandwidth sensitivity;
- 120-row aspect matrix, local formulas, duplicate-section discrepancy, alignment counterexample, ties, and reversal;
- exact producer separation, status mutation, manifest hierarchy controls, source preservation, and post-review seal.

**Qualified**

- linked plugin and context cycles are exact pin-specific model outputs but uncalibrated;
- formula sensitivities are exact within their equations and retained grids;
- workload/architecture perturbations challenge selected boundaries but do not establish statistical representativeness;
- methodological primary-source entries verified through publisher metadata/abstract remain qualified where full primary text was not inspected;
- multiobjective/Pareto concepts motivate retaining alternatives but are not exercised.

**Rejected**

- labeled dataflow rows as three executed routes in the original sweep;
- any addition across heterogeneous cycle producers;
- `mTOPS` as a literal unit for the source expression;
- stochastic conversion vectors as application accuracy or independent sampling;
- CONTROL’s 100 cycles as complete continuation latency;
- aspect formulas as Tusim runtime execution;
- the report’s global nonzero-remainder bound and compiler-padding recommendation;
- any portfolio-wide or calibrated hardware recommendation.

**Blocked**

- preference rules, nondominated portfolio selection, and portfolio ranking until Chapter 22;
- ONNX/compiler/scheduler/allocator/queue/runtime composition at this pin;
- physical timing, power, energy, or accuracy conclusions without an appropriate producer and calibration path.

## 21.14 Sealed limitation register

The exposition explains the sealed claims, but the following sentences are the binding drafting bounds. Each appears exactly once. If broader-sounding prose conflicts with a row, the row controls.

| Claim | Binding limitation wording |
|---|---|
| C21.1 | filename tokens, Make rules, aggregate membership, and execution are different relations; none alone identifies a trustworthy sweep. |
| C21.2 | a large parameter matrix without a predeclared disproof condition remains descriptive output, not decision evidence. |
| C21.3 | the sweep’s functional rows, effective core route, and handwritten cycle rows have separate producers and may not be presented as one dataflow execution. |
| C21.4 | fixed-seed replay is one deterministic conversion vector; changed-seed output is not an independent workload sample, an unbiasedness proof, training evidence, or application-accuracy validation. |
| C21.5 | context rows are uncalibrated model cycles at a caller-established legal boundary; `CONTROL` (the CONTROL-only fixture) has 100 cycles but omits reload, backing-store, queueing, drainage, and continuation correctness. |
| C21.6 | the aspect-ratio rows execute Python formulas, not Tusim runtime workloads, and their two output sections use different fill/drain expressions. |
| C21.7 | tested-grid rows may support local arithmetic; they do not support the report’s global nonzero-remainder bound or its compiler-padding recommendation. |
| C21.8 | a stable ordering on the retained grid is a grid-local result, not proof of a universal regime or physical optimum. |
| C21.9 | no result combines heterogeneous producer classes or cycle domains into one elapsed-time claim without a proved common timeline. |
| C21.10 | a zero exit status proves only the gated observations that the outer runner checks; printed `FAILED`, stale rows, or missing completion must make the governed run nonzero. |
| C21.11 | a pre-review green seal is provisional and cannot authorize drafting; only the immutable post-review seal may do so. |
| C21.12 | no Chapter 21 worked example is a portfolio-wide recommendation, calibrated hardware result, or ONNX/compiler/scheduler/allocator/queue/runtime composition. |

## Development questions

1. Should sweep harnesses consume a machine-readable decision schema rather than duplicate axes in source and prose?
2. Should every row carry producer class, source path, units, reset state, fidelity, and omission fields directly?
3. How should route identity be exposed without relying on process-global state or labels?
4. Which sweep axes should have automatically generated declaration-to-consumer A/B tests?
5. How should stochastic sweeps report unique seeds, unique vectors, repeated invocations, and order controls?
6. Which workload-characterization dimensions best represent Tusim’s intended architecture questions?
7. When is exhaustive boundary enumeration preferable to random or space-filling samples?
8. How should surrogate prediction error and extrapolation distance be represented beside predicted rows?
9. Can a common result schema preserve incompatible producers without encouraging cross-domain aggregation?
10. Which status schema should distinguish producer failure, row mismatch, missing output, parser failure, and incomplete execution?
11. How should exact ties and near-ties be reported when estimates are uncalibrated?
12. What preference information must Chapter 22 declare before selecting among nondominated alternatives?
13. Which report recommendations should be converted into explicit counter-hypotheses rather than preserved as conclusions?
14. Can manifests bind claim-to-row and claim-to-control relations in addition to file hashes?
15. What external reference and mapping contract would be required to calibrate a selected sweep family?

## Summary

A trustworthy sweep begins with one decision and one disproof condition, not with a loop over every available knob. It preserves realistic alternatives and exclusions, distinguishes workload from architecture axes, and states controlled state, seed policy, aggregation, missing-case, and tie rules before interpreting results.

Every varied axis must reach an effective consumer. The pinned dataflow sweep demonstrates why: process-global selection is overwritten by core snapshot swap-in, so an OS-labeled row executes WS. Direct WS, OS, and RS routes remain separately reachable and produce the same bounded matrix output, but route identity and plugin-local estimates distinguish them.

Producer identity precedes comparison. Sweep-local dataflow equations, historical report equations, and linked plugin estimators yield 26,624/22,528/24,640; 21,536/21,504; and 81,920/20,480/50,176 for the named case. Those families cannot be combined. Context rows are linked equation outputs, aspect rows are local Python formulas, and report conclusions remain prose until reconciled.

Controls must attack labels, routes, relations, formulas, status, seed/order state, and provenance. The outer runner rejects a count-preserving relation swap, effective-route mutation, stale formula rows, upstream zero-status mismatch, source drift, malformed or escaping manifests, and optimizer-removable validator assertions.

Sensitivity crosses named boundaries. The retained cases perturb workload and architecture axes, preserve ties and reversals, locate a context budget transition, and retain the aspect report’s remainder-8 counterexample. These results define local equation behavior; they do not rank Tusim’s portfolio.

Finally, reproducibility is layered. Exact inputs, raw and parsed outputs, manifests, validation receipts, review dispositions, and Git seal make the evidence inspectable. They do not make it semantically correct by themselves. The provisional seal, postreview-v6, and postreview-v7 were superseded after independent review; only corrected postreview-v8 authorizes this chapter.

Chapter 17 retains metric semantics, Chapter 20 evidence authorization, Chapter 21 sweep construction, and Chapter 22 portfolio preference and synthesis. No compiler/runtime composition or calibrated physical result is created by adjacency, labels, or a large matrix.

## Review questions

1. Why is a large parameter matrix not automatically decision evidence?
2. Which relations separate a sweep-named source file from an executed, trustworthy comparison?
3. Why does the original OS-labeled dataflow row execute WS?
4. What does equal WS/OS/RS functional output prove, and what does it not prove?
5. Why are the three dataflow cycle families incomparable?
6. What exactly does the RNE-versus-RTZ case establish?
7. Why is a changed stochastic seed not an independent workload sample?
8. What reset policy makes the stochastic order control meaningful?
9. How are the context rows recomputed, and which costs are omitted?
10. Why do 1,382 and 1,376 both appear for M=20, N=48?
11. How does M=40, N=16 disprove the report’s global remainder bound?
12. What does a count-preserving source-target mutation prove?
13. Why must a zero-status sweep still be wrapped by observation gates?
14. Which fields are required before aggregating multiple workload rows?
15. What do exact manifests and a post-review seal prove, and what remains unproved?

### Review-question answer key

1. Matrix size does not supply a falsifiable decision, effective consumer, adequate producer, failure path, sensitivity boundary, or provenance.
2. Filename, source-to-rule ownership, aggregate/CI selection, actual execution, effective route, producer identity, row validation, status propagation, and retained provenance are separate.
3. The sweep sets process-global state, then a core operation swaps in the newly initialized core snapshot, whose dataflow remains WS.
4. It proves bounded normal-value functional equality for `[58,64,139,154]`; active route, modeled cycles, movement, and physical performance remain separate.
5. Sweep-local, historical-report, and linked-plugin equations use different producers and included terms, including different DMA treatment.
6. For input 1.0007 on the named conversion route, mode reaches FP32-to-FP16 conversion and produces `0x3c01` versus `0x3c00`.
7. It is one different deterministic conversion vector, not a sampled application, distribution, or independent accuracy trial.
8. Explicitly reseed every case before both forward and reverse permutations; otherwise global PRNG history makes order itself change the inputs.
9. Use `100 + ceil((outgoing_saved_bytes + incoming_saved_bytes)/Bpc)`; reload, backing store, queues, drainage, and continuation correctness are omitted.
10. The canonical main row uses shape-dependent fill plus drain; a duplicate section substitutes `2*pipeline_depth`, producing an inconsistent total.
11. Utilization is `40/48=83.3%`, so waste is 16.7% for remainder 8, exceeding 3.8%.
12. It proves the literal relation set, not only its cardinality, is gated.
13. The inner program may print a mismatch and return zero; the outer gate must parse required observations, reject failure text, require completion, and propagate nonzero.
14. Producer, interval, units, state/reset, denominator, baseline, normalization, weights, missing-case policy, objective direction, tie handling, fidelity, and omissions.
15. They prove exact byte identity, member completeness, validation behavior, and reviewed authority for the bounded package; they do not prove semantic correctness, calibration, representativeness, or portfolio optimality.

## Design exercises

1. **Decision contract.** Choose one Tusim exploration report and write its question, counter-hypothesis, alternatives, controls, disproof condition, and safe/unsafe conclusions.
2. **Relation inventory.** Build a source→rule→aggregate→CI→command table for one sweep family and design a count-preserving mutation.
3. **Route discriminator.** Design an input and observable that distinguish two implementations even when their functional outputs should match.
4. **Producer register.** Take one cycle-like table and record producer, formula, interval, reset, units, clock, omissions, calibration, and safe comparison domain.
5. **Seed and order control.** Specify fixed replay, changed seed, forward/reverse order, and per-case reset for a stochastic sweep.
6. **Boundary matrix.** For a tiled equation, include both sides and the exact point of one alignment or capacity transition.
7. **Counterexample.** Turn a global report recommendation into a bounded claim by finding one defeating configuration and revising its scope.
8. **Status propagation.** Wrap an unconditional-success sweep so a printed mismatch, stale row, missing completion, timeout, or parser error fails closed.
9. **Aggregation policy.** Define baseline, normalization, weights, denominator, missing-case rule, objective direction, and tie policy for a multi-workload comparison.
10. **Multiobjective boundary.** Define objectives and feasibility constraints for three alternatives, but stop before applying a preference rule; explain why the nondominated set is matrix-local.
11. **Manifest package.** Specify payload members, outer roots, derived receipts, path/symlink checks, and one semantic mutation.
12. **Calibration plan.** Design an external-reference experiment that could upgrade one linked estimate while preserving mapping, workload, units, and uncertainty.

### Exercise answer sketches

1. Keep the decision local and name what result would falsify it; a report heading or preferred row is not a disproof condition.
2. Represent every relation literally and mutate one member while preserving count so the semantic set gate, not only a hash or cardinality gate, is exercised.
3. Use nonsymmetric data, active implementation identity, implementation-specific state or counters, and a direct positive control; equal output alone is insufficient.
4. Do not accept a field name as units or fidelity; compare only rows with the same producer contract or a proved common timeline.
5. Reseed each case, require same-seed identity, changed-seed difference, and forward/reverse equality under per-case reset; report unique vectors separately from invocations.
6. Include below, exact, and above-boundary points and perturb one second architecture parameter so a single-axis formula cannot define the entire conclusion.
7. Preserve the counterexample, narrow the conclusion to the tested grid or equation, and remove downstream recommendations that require an unexercised compiler/runtime route.
8. Preserve producer status and parsed observations separately; any nonzero, mismatch, missing output, timeout, or contradiction is non-pass.
9. Retain per-workload rows first; use only a mathematically appropriate summary, disclose all exclusions, and preserve exact ties instead of hidden tie-breaking.
10. Nondominance depends on the declared matrix, objectives, constraints, workloads, and fidelity; preference and portfolio ranking remain a separate decision.
11. Require exact regular contained members, reject missing/extra/duplicate/symlink/traversal cases, verify hashes, mutation-test the validator, and bind the reviewed final tree.
12. Use the same workload and mapping, name both producers and clocks, define synchronization and uncertainty, test several regimes, and report error rather than transferring calibration globally.

## Primary references

- [Chapter 21 method source map](../../references/ch21-sweep-method-primary-sources.md) contains verified metadata, inspected surfaces, safe methodological uses, and limitations for all sources cited here.
- İpek et al., “Efficient architectural design space exploration via predictive modeling,” 2008, [DOI 10.1145/1328195.1328196](https://doi.org/10.1145/1328195.1328196).
- Lee and Brooks, “Accurate and efficient regression modeling for microarchitectural performance and power prediction,” 2006, [DOI 10.1145/1168857.1168881](https://doi.org/10.1145/1168857.1168881).
- Deb et al., “A fast and elitist multiobjective genetic algorithm: NSGA-II,” 2002, [DOI 10.1109/4235.996017](https://doi.org/10.1109/4235.996017).
- Eeckhout, Vandierendonck, and De Bosschere, “Designing computer architecture research workloads,” 2003, [DOI 10.1109/MC.2003.1178050](https://doi.org/10.1109/MC.2003.1178050).
- Phansalkar, Joshi, and John, “Analysis of redundancy and application balance in the SPEC CPU2006 benchmark suite,” 2007, [DOI 10.1145/1250662.1250713](https://doi.org/10.1145/1250662.1250713).
- Fleming and Wallace, “How not to lie with statistics: the correct way to summarize benchmark results,” 1986, [DOI 10.1145/5666.5673](https://doi.org/10.1145/5666.5673).
- Mytkowicz et al., “Producing wrong data without doing anything obviously wrong!” 2009, [DOI 10.1145/1508244.1508275](https://doi.org/10.1145/1508244.1508275).
- Sandve et al., “Ten Simple Rules for Reproducible Computational Research,” 2013, [DOI 10.1371/journal.pcbi.1003285](https://doi.org/10.1371/journal.pcbi.1003285).
- Stodden et al., “Enhancing reproducibility for computational methods,” 2016, [DOI 10.1126/science.aah6168](https://doi.org/10.1126/science.aah6168).
- Kunze et al., “The BagIt File Packaging Format (V1.0),” RFC 8493, 2018, [DOI 10.17487/RFC8493](https://doi.org/10.17487/RFC8493).
