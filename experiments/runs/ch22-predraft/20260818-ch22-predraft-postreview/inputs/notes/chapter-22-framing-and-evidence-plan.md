# Chapter 22 — Framing and Required Evidence Plan

- Date: 2026-08-18
- Status: **framing gate closed; Chapter 22 predraft evidence next; manuscript drafting blocked**
- Tusim source pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Governing plan: [`../PLAN.md`](../PLAN.md)
- Chapter 21 closure: [`handoffs/2026-08-18-chapter-21.md`](handoffs/2026-08-18-chapter-21.md)
- Reproduction script: [`../experiments/ch22_framing_recon.py`](../experiments/ch22_framing_recon.py)
- Retained reproduction: [`chapter-22-framing-reproduction.log`](chapter-22-framing-reproduction.log)

## Gate question

Given a workload, correctness/continuation contract, and reconciled Tusim evidence, **which constraint currently binds the local architecture choice, which materially distinct alternative is justified as the next design hypothesis, and what boundary or omitted cost could reverse that preference?**

Every historical conclusion must pass an evidence disposition before it can support that decision. This is a constraint-first, evidence-reconciled portfolio decision. It is not another tutorial on constructing sweeps, not a ranking of incomparable cycle producers, and not a compiler/runtime integration narrative.

## Opening architecture question

**After every attractive “sweet spot,” “winner,” and crossover is checked against the executable model, which lessons remain useful—and which become local hypotheses, superseded formulas, rejected recommendations, or blocked decisions?**

## Reader decision

For a workload and local architecture choice, the reader must be able to:

1. identify the historical report claim, alternatives, workload, varied parameters, and stated objective;
2. bind the claim to its actual producer and to the strongest current executable evidence;
3. assign one disposition: `retained`, `qualified`, `superseded`, `rejected`, or `blocked`;
4. identify the currently binding modeled constraint and distinguish it from a blind or omitted constraint;
5. name the exact regime boundary or counterexample that limits the conclusion;
6. preserve materially distinct alternatives and their performance, area/power, accuracy, control, software-contract, verification, and fidelity costs where evidence exists;
7. distinguish a comparable domain-local trade-off from a merely recurring structural pattern across domains;
8. refuse to add, normalize, or Pareto-rank incompatible cycle and metric domains;
9. state the next bounded design hypothesis and its reversal condition, or explain why the decision remains open.

## Fresh read-only portfolio reconnaissance

The fail-closed framing reproduction reads all 46 pinned reports under `docs/exploration/` except `IMPLEMENTATION_BACKLOG.md`, checks their exact one-to-one partition and ordered aggregate hash, binds 18 initial claim-level dispositions to eleven hash-locked book evidence surfaces with structured claim references, records thirteen incompatible metric domains with an exact sample-claim mapping, and verifies both the detached clean source and clean tracked book evidence base before execution. It also verifies source preservation after an injected early failure.

### Exact domain partition

| Portfolio domain | Reports | Role in Chapter 22 |
|---|---:|---|
| Geometry and balance | 13 | array shape/size, dataflow, pipeline depth, bus width, MAC density, and K/workload balance |
| Memory and movement | 8 | capacity cliffs, tiling, channels, DRAM, arbitration, and ideal versus executable overlap |
| Numerics and weight representation | 7 | precision/rounding, INT8, 2:4, RLE/bitmap/adaptive codecs, and decoder provisioning |
| Operator irregularity | 10 | convolution/pooling, attention, softmax/normalization, and elementwise composition claims |
| Sharing and topology | 6 | multicore traffic, broadcast, topology, switching, route order, and contention |
| Runtime/static policy | 2 | retained-state scope and scheduler-policy observability |

The partition is an inventory, not a chapter outline. Organizing the manuscript as six directory-like mini-chapters would reproduce the catalogue risk that the global plan forbids.

### Recurring mechanisms found across the portfolio

Seven semantically gated, cross-domain candidate mechanisms provide a synthetic spine without combining their quantities. Every candidate names its producer boundary and one break case:

1. **Fixed-cost amortization:** setup, fill/drain, output passes, or transfer terms dominate below a workload-dependent amount of useful work.
2. **Resource thresholds and discrete cliffs:** capacity-induced pass counts and decoder-provision knees change discontinuously, but remain different equations and units.
3. **Bandwidth/compute balance:** wider movement or more compute shifts a local knee, but neither establishes a physical optimum without cost and calibration.
4. **Distribution or placement, not a scalar rate:** codec/sparse usefulness and NoC contention depend on where zeros or messages occur, not only aggregate sparsity or injection rate.
5. **Shape- or placement-dependent reversals:** geometry and topology/routing preferences can reverse with workload shape or endpoint mapping, while retaining separate producers and objectives.
6. **Retained or buffered state scope shifts obligations:** retaining or duplicating less/more state moves reload, ownership, validity, and verification obligations; DMA channel count alone is not this regime.
7. **Producer and metric-dialect hazards:** identical labels such as cycles, utilization, throughput, or overhead can denote linked estimators, report-local formulas, ideal overlap equations, controller ledgers, stall returns, operator equations, caller-ticked DRAM, traffic heuristics, context ledgers, scheduler estimates, codec estimates, numerical error, or non-cycle functional evidence.

These are structural recurrences only. The chapter may compare the *shape of a decision*—for example, a threshold or reversal—but may not add or normalize the underlying values across domains.

### Immediate reconciliation results

The framing reproduction deliberately samples claims that can change the chapter spine:

- **Dataflow:** three report formula families disagree with each other and with direct linked WS/OS/RS estimators; labels in the old core sweep do not prove the effective route. Physical “OS wins” or “dataflow is irrelevant” recommendations are rejected.
- **DRAM:** the type/clock report contains recomputed arithmetic and conclusion contradictions; retain the bandwidth-balance question, not its device recommendation.
- **Double buffering:** ideal curves remain hypotheses, but the executable controller exposes stale active data and lacks ordinary-operation reachability. “Highest leverage” and compiler scheduling recommendations are rejected or blocked.
- **Precision and rounding:** element-width spreadsheets do not create precision-specific MMA paths. The rounding fixture reaches W/A conversion, not accumulator-store/per-accumulation rounding; training/inference generalization is unsupported.
- **Weights:** exact encoded bytes, round trips, and source equations survive. Useful alternatives remain distribution- and decoder-dependent; bytes do not directly imply latency or energy, and no codec→decoder→MMA feed exists.
- **Operators:** attention trend conclusions remain blocked by the FP16 SRAM staging defect. Softmax/normalization stall returns cannot be divided by or added to attention/conv/pool analytical totals as one pipeline time.
- **Sharing:** the old universal mesh story is superseded by linked traffic-shape reversals, but the current score is still a deterministic heuristic rather than a queued makespan. Broadcast is sequential immediate copying, not one multicast transfer.
- **State and scheduling:** FULL/LIVE/CONTROL remain useful retention alternatives at a caller-established legal boundary; scheduler policies can reorder output while the chosen serial metric remains unchanged. Neither result implies compiler/runtime composition.

The 46-report inventory mechanically finds high-recommendation vocabulary in 41 reports and any literal `compiler`, `runtime`, or `ONNX` vocabulary in 22. Those counts are triage signals, not automatic rejections. The framing reproduction's 18 rows are explicitly an initial claim-level sample (`complete_claim_register=0`), each using only the five canonical dispositions. The complete predraft register must split mixed conclusions and inspect every high-salience claim.

## Ranked scope candidates

| Rank | Candidate | Reader decision | Evidence and continuity | Principal risk |
|---:|---|---|---|---|
| **1** | **Constraint-first evidence-reconciled preference rules** | Given a workload and contract, identify the binding modeled constraint, select the next justified architecture hypothesis, and name what could reverse it | Best fit to the planned chapter and independent framing review; uses all report domains, completed audits, stale conclusions, reversals, and trade-offs without repeating sweep construction | Broad unless one constraint/disposition/alternative decision card governs every example |
| **2** | Recurring constraint regimes without a disposition gate | Recognize amortization knees, capacity cliffs, balance points, distribution sensitivity, traffic reversals, and state-scope shifts across architecture domains | Strong synthesis and reusable architecture intuition; avoids report-by-report chronology | Structural analogy can erase producer ownership, preserve stale premises, or tempt cross-domain normalization |
| **3** | Portfolio disposition atlas | Determine which of the 46 reports are current, qualified, superseded, rejected, or blocked | Maximum provenance clarity and direct stale-report cleanup value | Becomes a forensic catalogue, can overemphasize negative findings, and under-teaches how to choose the next architecture hypothesis |
| **4** | Multiobjective/Pareto portfolio | Choose non-dominated alternatives under performance, area/power, accuracy, complexity, software, verification, and fidelity objectives | Preserves realistic alternatives and directly serves architects | Most dimensions are directional or unquantified; reports span incompatible producers, so one portfolio-wide Pareto frontier would be false precision |

## Scope decision

**Select Candidate 1: constraint-first evidence-reconciled preference rules.**

Candidate 2 supplies the recurring-regime vocabulary. Candidate 3 is an evidence filter and complete disposition register, not the manuscript spine. Candidate 4 supplies a disciplined alternatives/trade-off lens only within comparable local decision families; Chapter 22 will explicitly reject a single global Pareto ranking.

Every worked family must use one decision card:

```text
workload, correctness/continuation contract, and local objective
  → historical conclusion, alternatives, producer, and assumptions
  → strongest executable evidence and evidence disposition
  → currently binding modeled constraint; blind or omitted constraints
  → regime boundary, reversal, or counterexample
  → materially distinct alternatives and sacrifices
  → next bounded design hypothesis and reversal condition, or an explicit open decision
```

This card imports Chapter 21's sealed evidence where relevant but does not reteach how to construct or package a sweep.

### Manuscript macrostructure guard

The complete 46-report/claim disposition register remains a companion evidence artifact, not 46 reader-facing subsections. The manuscript is bounded to:

1. one short portfolio-evidence and disposition-gate opening;
2. **five to seven** constraint-first worked families selected to span the seven candidate mechanisms and all five disposition states without claiming exhaustive reader-facing coverage;
3. one alternatives/trade-off synthesis that preserves local objectives and unknowns;
4. one stale-conclusion/negative-evidence synthesis;
5. one bounded next-hypothesis checklist.

No worked family may be organized primarily by report filename or repeat Chapter 21's sweep-construction sequence. A manuscript validator must reject more than seven top-level worked families and must require each to include binding constraint, evidence disposition, alternatives, reversal condition, and metric-domain boundary.

## Inclusions

- exact inventory and domain classification of all 46 exploration reports;
- complete claim-level disposition register for their high-salience conclusions;
- recurring regimes across geometry, memory balance, data movement, numerics/representation, operators, sharing, and state policy;
- executable rechecks for representative retained, qualified, superseded, rejected, and blocked cases;
- report formulas recomputed against current source equations where they remain decision-relevant;
- useful alternatives, regime boundaries, ties, reversals, and counterexamples;
- local multiobjective trade-offs across performance, area/power, accuracy, control complexity, software obligations, verification cost, and fidelity;
- negative lessons when a stale conclusion reveals a missing integration bridge, ineffective selector, incompatible metric, or correctness defect;
- bounded implications for future architecture-model work, clearly separated from implemented behavior.

## Explicit exclusions

- no repeat of Chapter 21's question/matrix/control/mutation/manifest construction tutorial;
- no report chronology or directory-by-directory catalogue as the manuscript spine;
- no sum, ratio, normalization, or global Pareto ranking across incompatible cycle/metric domains;
- no calibrated physical-performance, area, power, energy, accuracy, or technology recommendation absent named evidence;
- no claim that a local formula, linked estimator, functional result, or historical report is ordinary runtime execution;
- no compiler/runtime composition from report prose, shared types, standalone APIs, or adjacent modules;
- no universal “best” PE array, dataflow, memory size, precision, codec, operator composition, topology, or context mode;
- no reopening of Chapter 21 or the Chapters 8/10/14 supplement backlog;
- no manuscript drafting before a complete claim ledger, executable reconciliation audit, skeptical review, and post-review seal.

## Ownership boundaries

- **Chapter 17:** owns producer, interval, units, reset, clock, denominator, and fidelity semantics.
- **Chapter 20:** owns what evidence authorizes and why unsafe green is insufficient.
- **Chapter 21:** owns sweep construction, controls, sensitivity, counterexamples, and reproducibility procedure.
- **Chapter 22:** owns disposition of portfolio conclusions, recurring regimes, retained alternatives, and bounded preference rules after executable reconciliation.
- **Chapter 23:** owns how to implement an extension through declaration, parser, runtime, consumer, observability, tests, and documentation.

## Required predraft evidence plan

Drafting remains blocked until the following evidence is complete, independently challenged, and sealed after review.

### E22.1 — Complete portfolio and conclusion register

Create a machine-readable record for all 46 reports containing:

- exact path/hash and domain;
- question, alternatives, workload, axes, controlled assumptions, and producer class;
- every high-salience quantitative or prescriptive conclusion, not merely one phrase per report;
- current evidence owner and exact claim/probe reference;
- status `retained`, `qualified`, `superseded`, `rejected`, or `blocked`;
- verbatim safe replacement and limitation wording;
- whether the report remains useful as current evidence, bounded arithmetic, historical rationale, a negative case, or only a future question.

Mutation-test the exact 46-member set, domain assignment, evidence link, status, and limitation. A report-level status must not hide mixed dispositions among its claims.

### E22.2 — Executable reconciliation matrix

Refresh representative evidence in a disposable exact-pin archive rather than trusting old prose alone:

1. **Geometry/dataflow:** direct active-route discriminator and current linked WS/OS/RS equations, kept separate from report formulas.
2. **Memory/overlap:** capacity-threshold arithmetic plus executable double-buffer byte-visibility/ownership negative bridge; no common clock unless proved.
3. **Weights/representation:** exact codec/2:4 bytes, round trip, decoder-width sensitivity, and integration-negative caller inventory.
4. **Numerics:** rounding-stage/seed discriminator and negative precision-dispatch inventory; do not claim application accuracy.
5. **Operators:** metric-dialect census, representative operator formulas, and attention correctness blocker.
6. **Sharing:** linked XY/YX or ring/mesh traffic-shape reversal, exact heuristic equation, and negative queue/makespan boundary.
7. **State/static policy:** FULL/LIVE/CONTROL source-equation rows and scheduler order-versus-metric discriminator.

Every row must name producer, units, state/history, evidence rung, modeled costs, omitted costs, and whether the result is executable behavior or an analytical estimate.

### E22.3 — Recurring-regime synthesis register

For each proposed cross-domain lesson:

- list at least two independent domains that exhibit the structure;
- state only the common decision pattern, not a common numerical scale;
- identify one domain where the analogy breaks;
- bind each example to its own producer and limitation;
- prohibit cross-domain sums, ratios, normalized speedups, or shared cycle axes;
- require a counterexample to any universal wording.

The seven framing regimes are candidates, not pre-approved manuscript claims.

### E22.4 — Alternatives and local preference rules

For each worked family:

- preserve every materially distinct plausible alternative;
- record the regime where each can be rational;
- state gains and sacrifices across supported performance, capacity/traffic, area/power direction, numerical accuracy, control, software contract, verification, and fidelity dimensions;
- separate quantified evidence from directional reasoning and unknowns;
- construct a local dominance/partial-order result only when objectives and producers are comparable;
- emit `open` rather than inventing a winner when decisive dimensions are absent.

A single global Pareto frontier across the portfolio is forbidden.

### E22.5 — Stale-conclusion and supersession audit

At minimum, close the framing's high-value contradictions:

- mislabeled/effectively WS dataflow rows and conflicting formula families;
- aspect-ratio duplicate formula and global-bound counterexample;
- DRAM type/clock arithmetic contradictions;
- ideal double-buffer speedups, area claims, generalized optimum formula, and compiler prescriptions versus stale-data executable behavior and the exact discrete threshold evidence;
- SRAM arbitration recommendations despite `arb_mode` having no live effect;
- GBuf weight-fit speedups and silicon-sizing recommendations despite the standalone hierarchy being disconnected from direct MMA and lacking cache allocation/replacement;
- precision/rounding path and causality overclaims;
- attention performance claims under a correctness defect;
- fused-activation “2–7×” and accumulator-path prescriptions despite no fused implementation or common elapsed-time domain;
- softmax/normalization/attention metric-domain composition;
- broadcast/all-reduce/topology stories versus actual sequential copies and heuristic traffic scores;
- context CONTROL/FULL/LIVE rows versus omitted continuation costs;
- scheduler policy equality in a metric that is insensitive to policy order.

Search every report and live book surface for stale affirmative wording after disposition changes. Historical sealed copies remain immutable.

### E22.6 — Preference robustness and counterevidence

A retained or qualified preference must include:

- exact objective and compared alternatives;
- boundary points, tie/reversal cases, and one disconfirming workload or architecture perturbation;
- evidence that the selector/axis reaches the intended consumer where execution is claimed;
- an explicit unknowns vector;
- a stronger alternative conclusion that was considered and rejected;
- a statement of what new evidence would change the disposition.

### E22.7 — Literature and foundations plan

Add verified primary-source support for:

- robust and multiobjective architecture design-space exploration;
- Pareto dominance with incomplete or incommensurate objectives;
- workload representativeness and sensitivity of architecture conclusions;
- operational intensity/balance reasoning without importing a calibrated roofline claim into Tusim;
- sparse/irregular workload distribution effects and NoC traffic-shape dependence where used.

General literature supplies reasoning vocabulary, not validation of Tusim's implementation or report numbers.

### E22.8 — Fail-closed seal and review

The canonical runner must:

- pin source and book evidence hashes;
- execute only from a disposable exact-pin source archive;
- retain the exact portfolio register, reconciliation matrix, raw outputs, parsed tables, independent recomputations, limitation register, review dispositions, toolchain, and commands;
- define exact inner and outer manifest member sets and reject missing, extra, duplicate, traversal, symlink, or mutable external inputs;
- mutation-test report membership, each report's exact high-salience claim-member set, canonical claim status/reason, evidence hash/reference, formula, regime domain/boundary/break case, alternative set, limitation, and a prohibited cross-domain composition;
- mutation-test objective tags (`quantified` / `directional` / `unknown`), objective and producer comparability, local-dominance eligibility, missing decisive dimensions, mandatory `open` outcomes, and local-versus-global Pareto scope;
- mutation-test the five-to-seven worked-family manuscript bound and every decision-card field;
- run validators under normal and optimized Python with a real assertion-source mutation;
- prove source preservation after early inventory, build/probe, manifest, and validator failures;
- retain failed and superseded runs unchanged;
- reseal after skeptical review before drafting authority is granted.

## Predraft claim families

The source-and-claim ledger must at minimum cover:

1. exact portfolio/domain inventory;
2. report claim and producer ownership;
3. recurring regime definitions and break cases;
4. geometry/balance preferences;
5. capacity and movement thresholds;
6. representation, density, decoder, and accuracy alternatives;
7. operator irregularity and metric-domain boundaries;
8. topology, route, traffic-shape, and sharing alternatives;
9. state-retention and static-policy alternatives;
10. retained, qualified, superseded, rejected, and blocked dispositions;
11. local multiobjective preference rules and open decisions;
12. no heterogeneous cycle composition and no compiler/runtime composition;
13. exact reproducibility and review authority.

Every claim requires status, evidence, disproof condition, safe wording, and verbatim limitation before sealing.

## Risk-register disposition

- **Chapter 21/22 repetition — triggered and resolved provisionally:** Chapter 22 begins with report conclusions and ends with bounded preferences; it imports rather than reteaches sweep construction.
- **Broad synthesis becoming a catalogue — triggered and resolved provisionally:** the constraint/disposition/alternative decision card is the spine; the six-domain inventory and complete register remain companion evidence, while the manuscript is limited to five-to-seven worked families.
- **Incompatible cycle/metric domains — triggered and fail-closed:** thirteen exact domains are registered with `composition_allowed=0`, and all 18 initial claim rows have an exact mapping; predraft evidence must expand that mapping to every claim and mutation-test forbidden composition.
- **Broken compiler path — triggered by 22 reports with literal `compiler`, `runtime`, or `ONNX` language and resolved negatively:** prose recommendations remain hypotheses unless a repository-contained executable bridge exists; none is implied here.
- **Source-edition drift — not triggered:** source remains detached and clean at `e918c80`.
- **Stable numbering — not triggered:** retain Chapter 22 in the 23-chapter architecture.
- **Completed-chapter supplements — reviewed, not triggered:** Chapters 8/10/14 supplements remain a later governed work unit; Chapter 22 may cite existing sealed evidence but cannot silently broaden it.
- **Global Pareto false precision — newly explicit:** objectives and producers are not globally commensurate; only domain-local partial orders are permitted.

## Framing gate

Framing closes only when all are true:

- [x] book `main` and Tusim detached pin/cleanliness verified live before research;
- [x] all 46 reports classified exactly once into an explicit coverage inventory;
- [x] recurring regime candidates have cross-domain membership, producer boundaries, and break cases; all initial claims have exact noncomposable metric-domain mappings;
- [x] at least three evidence-backed scopes ranked before selection;
- [x] selected scope has one reader decision, decision-card spine, five-to-seven-family macrostructure, inclusions, exclusions, and ownership boundaries;
- [x] 18 initial claim-level dispositions use the exact five-state vocabulary and bind report anchors to hash-locked structured evidence references;
- [x] required predraft evidence families, claim-completeness/local-dominance mutations, and focused reconciliation probes are explicit;
- [x] plan risks are resolved, fail-closed, or explicitly deferred;
- [x] reproduction script passes, injected failure preserves source state, and two consecutive outputs are byte-identical;
- [x] independent skeptical framing review completed and all valid findings reconciled;
- [x] final reproduction rerun after review amendments;
- [x] final exact re-review passes;
- [x] `PLAN.md`, `README.md`, status/handoff, and framing governance prepared as one coherent Chapter 22 framing checkpoint.

Even after framing closes, **manuscript drafting remains blocked**. The next work unit must build the complete claim-level portfolio register, source-and-claim ledger, executable reconciliation audit, limitation register, skeptical predraft review, and post-review evidence seal.
