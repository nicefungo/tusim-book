# Chapter 22 — Framing Review Dispositions

- Date: 2026-08-18
- Review batch: `deleg_a389eddd`
- Initial verdict: **REVISE**; no BLOCK-level defect in the constraint-first framing
- Reconciliation status: **all seven findings accepted and amended; final exact re-review PASS**
- Tusim pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`

## Review authority

The reviewer independently inventoried all 46 reports, verified the 13/8/7/10/6/2 domain partition, checked all 18 initial report/evidence anchors, reran the original reproduction twice, and kept Tusim detached/clean. It accepted the empirical/synthetic scope and its Chapter 21, metric-composition, global-Pareto, and compiler/runtime boundaries, but found six MAJOR fail-closed/provenance gaps and one MINOR catalogue-control gap.

## Findings and dispositions

### F22-R1 — Evidence surfaces were substring-bound, not revision-bound

- Severity: **MAJOR**
- Disposition: **accepted and resolved**
- Amendment:
  - `experiments/ch22_framing_recon.py` now pins SHA-256 for eleven book evidence surfaces;
  - every initial disposition carries an exact `D22Fxx` claim ID, structured evidence reference, unique report anchor, and unique evidence anchor;
  - the script enforces book `main` at the clean tracked evidence base `9cfedfad3d78190972f6481857ad56d9019fbf19` and source detached/clean at `e918c80`;
  - the portfolio records an ordered filename+file-hash aggregate `07b35ff12a606889e20bf8fb96180bb55ef4727085b7b351b4589f9bfbdf9196`.
- Anchor corrections:
  - FP8 throughput rejection now cites `source-audit#32` (`direct MMA hardcodes FP16 W/A and FP32 psum/O`), not “no BF16 MMA”;
  - compression cites `C13.20`, not the generic “Encoded bytes” heading;
  - double-buffer claims cite `C16.27`, not a filename;
  - pipeline-depth “hardware-accurate” wording is rejected against current linked WS timing ownership rather than treated as validated by a K-tile implementation detail.

### F22-R2 — Compound status vocabulary hid mixed claims

- Severity: **MAJOR**
- Disposition: **accepted and resolved**
- Amendment:
  - exact canonical vocabulary is now `retained / qualified / superseded / rejected / blocked`;
  - all 18 framing rows describe one anchored claim and one reason;
  - broadcast's current hard-requirement claim is `rejected`, while future multicast remains outside that disposition;
  - softmax pipeline percentage is `rejected`, with incompatible metrics as its reason;
  - the framing sample explicitly reports `complete_claim_register=0`; E22.1 must enumerate and split every high-salience claim before predraft closure.

### F22-R3 — Recurring regimes were cardinality-gated and semantically weak

- Severity: **MAJOR**
- Disposition: **accepted and resolved**
- Amendment:
  - all seven regime candidates now span at least two inventory domains;
  - every candidate has an exact member set, producer-boundary sentence, and break case;
  - `state_scope_shifts_cost` was replaced with the narrower retained-or-buffered-state obligation pattern; DMA-channel and SRAM-arbitration reports were removed;
  - traffic/geometry was reframed as a shape-or-placement reversal; broadcast was removed because it does not demonstrate a placement winner reversal;
  - distribution was broadened carefully to sparse placement and NoC message placement while explicitly prohibiting comparable rates/costs.

### F22-R4 — Cycle-domain register was incomplete and cardinality-only

- Severity: **MAJOR**
- Disposition: **accepted and resolved**
- Amendment:
  - the register now has thirteen exact metric domains, including ideal overlap formulas, controller ledgers, scheduler serial/DAG estimates, codec byte/estimator outputs, numerical error, and non-cycle structural evidence;
  - all 18 sample claims have an exact claim→domain mapping;
  - `composition_allowed=0` remains explicit;
  - E22.8 requires the complete predraft claim set to carry the same exact mapping and a prohibited-composition mutation.

### F22-R5 — Compiler/runtime risk marker undercounted the portfolio

- Severity: **MAJOR**
- Disposition: **accepted and resolved**
- Amendment:
  - the narrow four-phrase expression was replaced by literal case-insensitive `compiler`, `runtime`, or `ONNX` inventory;
  - exact count is now 22 and the full member list is emitted;
  - plan wording names the broad definition and retains the negative no-composition boundary.

### F22-R6 — Claim completeness and local-Pareto eligibility did not fail closed

- Severity: **MAJOR**
- Disposition: **accepted and resolved in the required predraft contract**
- Amendment: E22.8 now mutation-tests:
  - each report's exact high-salience claim-member set;
  - canonical status/reason and evidence hash/reference;
  - quantified/directional/unknown objective tags;
  - objective and producer comparability;
  - local-dominance eligibility;
  - missing decisive dimensions and mandatory `open` results;
  - local-versus-global Pareto scope;
  - exact regime domain/boundary/break-case fields and forbidden composition.
- Boundary: these are predraft evidence requirements, not claims that the framing sample is already complete.

### F22-R7 — Catalogue prevention was editorial rather than enforceable

- Severity: **MINOR**
- Disposition: **accepted and resolved**
- Amendment:
  - the complete register is a companion artifact;
  - the manuscript is bounded to five-to-seven constraint-first worked families plus a short gate opening, alternatives synthesis, stale/negative synthesis, and next-hypothesis checklist;
  - the manuscript validator must enforce the worked-family bound and every decision-card field;
  - filename/report chronology is prohibited as section organization.

## Additional independent framing input reconciled

The earlier three-way read-only reconnaissance (`deleg_de14834f`) independently reviewed all 46 reports, built stale-conclusion mappings, and preferred a constraint-first reader decision: identify the binding constraint, next justified architecture hypothesis, and reversal condition. The selected scope was amended from a disposition-led preference frame to **constraint-first evidence-reconciled preference rules**. Disposition remains the evidence filter, not the manuscript spine.

That review also surfaced stale high-value conclusions now made explicit in E22.5: SRAM arbitration despite inert `arb_mode`, GBuf sizing despite disconnected hierarchy/direct MMA, fused-activation speedups without a fused path/common elapsed-time domain, and ideal double-buffer area/threshold/compiler claims.

## Post-amendment reproduction

- Script SHA-256: `cbbd112fea8e581af9db048bdc84a516d41c1140c17297150f225d84c5990ad7`
- Retained log SHA-256: `9a331e5237600e8d7ff1f5b23c8f5a79c7af49cf6ef69a3c98bb3198425db206`
- Result: `CH22_FRAMING_RECON PASS`
- Two consecutive runs: byte-identical
- Injected inventory predicate: rejected with source-after state present exactly once
- Tusim after run: detached and clean at `e918c80`

## Final exact re-review

Review batch `deleg_1c9d0a89` returned **PASS** with no BLOCK, MAJOR, MINOR, or NIT issue. It independently verified all seven amendments, reran the script twice to disposable outputs, matched both outputs to the retained log, exercised the direct failure path, checked hashes/anchors/counts/links/AST/whitespace, and confirmed both repository states. Reviewed hashes were:

- script: `cbbd112fea8e581af9db048bdc84a516d41c1140c17297150f225d84c5990ad7`;
- retained log: `9a331e5237600e8d7ff1f5b23c8f5a79c7af49cf6ef69a3c98bb3198425db206`;
- framing plan: `93b0be3ee695dd324e9d362714585c9e3be98b424e136a1dd38ba28a4970162e`;
- pre-PASS disposition record: `9e5b8e69a65b3c72141748fa0b037cc1732ff9b02aec8b1bed3949744a49dc38`.

## Remaining closure gate

1. update `PLAN.md`, `README.md`, and durable handoff;
2. validate links, diff, repository state, and committed artifact hashes;
3. commit the coherent framing checkpoint.

Manuscript drafting remains blocked after framing closure pending the complete claim-level register, executable reconciliation evidence, skeptical predraft review, and post-review evidence seal.
