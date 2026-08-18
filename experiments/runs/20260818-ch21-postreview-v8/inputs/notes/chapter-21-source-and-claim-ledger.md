# Chapter 21 — Source and Claim Ledger

- Date: 2026-08-18
- Status: **exact manuscript review reopened v7 producer evidence; corrected v8 reseal pending**
- Tusim pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Claim vocabulary: **verified / qualified / rejected / blocked**

## Authority boundary

Chapter 21 owns sweep construction: question, alternatives, controls, effective axes, workload/seed matrices, sensitivity, counterexamples, producer-aware comparison, and reproduction. Chapter 17 retains metric-producer semantics. Chapter 20 retains evidence authorization. Chapter 22 retains portfolio conclusions. No claim composes ONNX, compiler, scheduler, allocator, queue, or runtime without an executable bridge.

## Claims

### C21.1 — Sweep inventory relations are exact, not lexical
- **Status:** verified.
- **Claim:** the pin contains 21 sweep-token C sources, two adjacent semantic/comparative harnesses, 22 literal source→Make-target pairs, and one exact no-rule singleton (`tests/test_int8_sweep.c`); none of the 22 targets belongs to `make test`.
- **Required evidence:** hash-locked inventory, literal pair set, same-cardinality pair mutation, aggregate set.
- **Limitation wording:** filename tokens, Make rules, aggregate membership, and execution are different relations; none alone identifies a trustworthy sweep.

### C21.2 — A sweep begins with a falsifiable local decision
- **Status:** qualified.
- **Claim:** each worked comparison declares a question, null/counter hypothesis, alternatives, controlled variables, boundary points, disproof condition, safe local conclusion, and unsafe broader conclusion.
- **Required evidence:** canonical decision schema and exact worked-case matrix.
- **Limitation wording:** a large parameter matrix without a predeclared disproof condition remains descriptive output, not decision evidence.

### C21.3 — Dataflow labels do not prove the effective route
- **Status:** verified.
- **Claim:** `test_dataflow_sweep.c` calls process-global `tu_set_dataflow(df_id)` but subsequent `tu_core_*` operations swap in the core snapshot; newly initialized cores retain WS, so rows labeled OS/RS execute the core snapshot while separate handwritten formulas use their labels. A 2×3 by 3×2 nonsymmetric probe yields `[58,64,139,154]` on WS/OS/RS but discriminates linked plugin estimates as 67/4/36 cycles. Three distinct 128×128×256 producers remain separate: sweep-local equations yield 26,624/22,528/24,640 including the sweep's DMA term; historical report equations yield 21,536/21,504 for WS/OS; the linked dispatcher composes plugin fill, tile-execution, and drain cycle methods to yield 81,920/20,480/50,176 and excludes the sweep-local DMA term.
- **Required evidence:** source trace, active-state probe, direct global setter positive control, route mutation.
- **Limitation wording:** the sweep’s functional rows, effective core route, and handwritten cycle rows have separate producers and may not be presented as one dataflow execution.

### C21.4 — Rounding and seed reach conversion, not application accuracy
- **Status:** qualified.
- **Claim:** the mode reaches FP32→FP16 W/A input conversion; MMA plugins decode FP16 and accumulate FP32, so the report’s accumulator-store and per-accumulation rounding explanations are unsupported. Fixed stochastic seeds reproduce one exact conversion vector and changed seeds can change that vector. The first stochastic sweep row inherits global PRNG history because it is not explicitly seeded.
- **Required evidence:** source trace; RNE/RTZ discriminator; same-seed replay; changed-seed vector.
- **Limitation wording:** fixed-seed replay is one deterministic conversion vector; changed-seed output is not an independent workload sample, an unbiasedness proof, training evidence, or application-accuracy validation.

### C21.5 — Context-switch rows are linked analytical estimates
- **Status:** verified.
- **Claim:** the context sweep executes the linked manager and reports `fixed + ceil((outgoing_saved_bytes + incoming_saved_bytes)/Bpc)` for `FULL`, `LIVE25` (the 25% LIVE-prefix fixture), and `CONTROL` (the CONTROL-only fixture); representative 256-KiB-total-capacity rows are 16,484/4,196/100 cycles at 32 B/cycle.
- **Required evidence:** source equation, live sweep, independent recomputation, bandwidth sensitivity.
- **Limitation wording:** context rows are uncalibrated model cycles at a caller-established legal boundary; `CONTROL` (the CONTROL-only fixture) has 100 cycles but omits reload, backing-store, queueing, drainage, and continuation correctness.

### C21.6 — The aspect-ratio matrix is a standalone formula
- **Status:** qualified.
- **Claim:** the tracked Python harness deterministically emits 120 rows from declared M/N/K axes and local fill/compute/drain/DMA equations. Its “worst edge utilization” section substitutes `2*pipeline_depth` for shape-dependent fill+drain; for 20×48 the canonical total is 1,382 and the duplicate-section total is 1,376, which explains the stale report row.
- **Required evidence:** exact row set, raw output, independent recomputation, formula mutation.
- **Limitation wording:** the aspect-ratio rows execute Python formulas, not Tusim runtime workloads, and their two output sections use different fill/drain expressions.

### C21.7 — Historical aspect prose contains a counterexample
- **Status:** rejected.
- **Claim rejected:** “≤3.8% overhead for any non-zero remainder.”
- **Evidence:** the same formula gives M=40, N=16 utilization 83.3%, hence 16.7% waste for remainder 8.
- **Limitation wording:** tested-grid rows may support local arithmetic; they do not support the report’s global nonzero-remainder bound or its compiler-padding recommendation.

### C21.8 — Sensitivity must cross the claimed boundary
- **Status:** verified.
- **Claim:** retained cases include both sides and the exact transition where defined, perturb at least one workload and one architecture parameter, report ties/reversals, and preserve a counterexample.
- **Required evidence:** K sensitivity, retention bandwidth/scope sensitivity, alignment boundary rows, report counterexample.
- **Limitation wording:** a stable ordering on the retained grid is a grid-local result, not proof of a universal regime or physical optimum.

### C21.9 — Producer classes remain separate
- **Status:** verified.
- **Claim:** executable effects, linked estimators, local formulas, and report prose are separately tagged and never summed merely because they occur in one process or report.
- **Required evidence:** metric/fidelity register and producer-class gates.
- **Limitation wording:** no result combines heterogeneous producer classes or cycle domains into one elapsed-time claim without a proved common timeline.

### C21.10 — Failure status is part of sweep construction
- **Status:** verified.
- **Claim:** the outer runner rejects source drift, same-count relation rewires, formula/axis changes, failed rows, and incomplete output; existing unconditional-success behavior is not accepted as claim evidence.
- **Required evidence:** source mutation, relation mutation, formula mutation, output/status mutation, exact completion/absence gates.
- **Limitation wording:** a zero exit status proves only the gated observations that the outer runner checks; printed `FAILED`, stale rows, or missing completion must make the governed run nonzero.

### C21.11 — Reproduction requires exact manifest closure
- **Status:** verified.
- **Claim:** drafting authority binds pin, source hashes, commands, matrices, seeds, toolchain/environment, raw outputs, parsed tables, formula recomputation, ledger, limitations, review dispositions, validator behavior, and exact inner/outer member sets.
- **Required evidence:** provisional seal, skeptical review, post-review reseal, normal/optimized validation, assertion mutation, early/manifest/validator failure preservation.
- **Limitation wording:** a pre-review green seal is provisional and cannot authorize drafting; only the immutable post-review seal may do so.

### C21.12 — The decision remains bounded
- **Status:** verified.
- **Claim:** Chapter 21 may authorize one local comparison after chain-of-custody closure, but cannot choose the best portfolio architecture or revive a compiler/runtime composition.
- **Required evidence:** ownership predicates and exact negative-boundary search.
- **Limitation wording:** no Chapter 21 worked example is a portfolio-wide recommendation, calibrated hardware result, or ONNX/compiler/scheduler/allocator/queue/runtime composition.

## Predraft gate

The post-review runner and validator must reproduce this authorization before it is effective. Every manuscript claim must preserve the verbatim limitation sentences in `chapter-21-limitation-register.md`; any failed or absent post-review seal reverts drafting authority to blocked.
