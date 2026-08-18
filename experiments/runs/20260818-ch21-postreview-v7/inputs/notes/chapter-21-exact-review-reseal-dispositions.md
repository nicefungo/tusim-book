# Chapter 21 — Exact-Commit Review Reseal Dispositions

- Date: 2026-08-18
- Reviewed claim commit: `f6d3c771449a9182c65a32e7e315944327a111ae`
- Review batch: `deleg_5de0a4a0`
- Reviewed authority: `experiments/runs/20260818-ch21-postreview-v6/`
- Initial verdicts: technical **REVISE** (3 major); editorial **REVISE** (1 major, 2 minor); reproducibility **REVISE** (1 block, 1 major, 1 minor)
- Reseal decision: **v6 remains immutable but is superseded for Chapter 21 closure; corrected evidence requires a fresh postreview-v7 seal before re-review.**

## Technical findings

1. **Historical post-seal command shown as current-tree command — RESOLVED in the v7 manuscript candidate.** `--postseal` is valid only at the direct-child sealing commit. Current-tree reproduction now uses bundle-local `--outer`; the historical post-seal receipt is explicitly attributed to the seal commit and verified structurally by the manuscript validator.
2. **Metric/fidelity register formulas and linked-producer attribution — RESOLVED for v7.** The sweep-local OS and RS equations now match `test_dataflow_sweep.c`; the report-local equations now distinguish one shape-level fill/drain from tiled compute; and the linked producer is the dispatcher composition of plugin `get_fill_cycles`, `execute_tile` returned cycles, and `get_drain_cycles`, not a nonexistent `estimate_cycles` callback. The predraft validator requires these exact records.
3. **Decision-schema axis roles — RESOLVED for v7.** Every worked case now distinguishes primary-matrix independent variables, primary-matrix controls, and secondary sensitivity variables. Dataflow PE geometry and aspect pipeline/bus perturbations are explicitly secondary sensitivity axes. The predraft validator requires the exact role assignments.

## Editorial findings

1. **Controlled versus sensitivity axes — RESOLVED by the schema correction above and matching manuscript wording.**
2. **Copyable pre-run contract omits decision-policy fields — RESOLVED.** The manuscript template now includes objectives/directions, constraints/feasibility, aggregation/baseline/normalization, missing-case policy, tie handling, and multiobjective status.
3. **Retention terminology and capacity wording — RESOLVED.** The manuscript defines `LIVE25` as the 25% LIVE-prefix fixture and `CONTROL` as the CONTROL-only fixture, uses “total SRAM capacity,” and the binding C21.5 wording uses the same aliases consistently.

## Reproducibility findings

1. **Occurrence-incomplete manuscript mutations — RESOLVED in the v7 manuscript validator candidate.** Quantitative phrase gates now carry exact occurrence counts and mutate every occurrence independently, including the output vector, inventory counts, 120-row statements, delta 67, context tie, summary, fidelity-box, worked-case, and answer-key surfaces.
2. **Runner accepts trailing review arguments — RESOLVED.** The runner now accepts exactly zero arguments or exactly one `--review`; all other arities return usage and status 2.
3. **External citation destinations not bound — RESOLVED.** Deterministic validation now requires the exact DOI/RFC destination set and occurrence counts; it does not depend on live network availability.

## Authority rule

This file records the immutable first exact-review findings and their v7 correction intent. It does not itself assert final Chapter 21 PASS. Final technical/editorial/reproducibility re-review must bind a later exact clean claim commit whose manuscript, validator, and runner all match the corrected v7 evidence.