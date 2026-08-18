# Chapter 21 — Final Exact Re-review and v8 Reseal Dispositions

- Date: 2026-08-18
- Reviewed claim commit: `f641ccba8d58c482c0e9fa3814ba824ffd513391`
- Review batch: `deleg_53e8dfc5`
- Editorial verdict: **PASS**
- Technical verdict: **BLOCKED pending corrected immutable evidence**
- Reproducibility verdict: **REVISE pending fail-closed coverage corrections**
- Current disposition: **all findings accepted for correction in a new postreview-v8 evidence run; v7 remains immutable historical evidence**

## Technical findings

### T1 — false aspect-ratio metric attribution

**Accepted.** The v7 audit report incorrectly assigned the dataflow sweep's source-labelled `mTOPS` defect to the aspect-ratio producer. The corrected report identifies the aspect script's source-labelled `TOPS` conversion as dimensionally correct under its stated 1 GHz assumption. The dataflow sweep remains the owner of the mislabeled `mTOPS` field.

### T2 — linked-plugin producer evidence was self-confirming

**Accepted.** The v7 formula probe returned the linked totals as constants, while the source audit bound only the generic dispatcher. The v8 correction:

1. digest-binds `weight_stationary.c`, `output_stationary.c`, and `row_stationary.c`;
2. checks each plugin's exact fill/execute/drain cycle contract;
3. derives `81,920 / 20,480 / 50,176` by iterating the dispatcher tile geometry and source equations rather than returning constants; and
4. executes all three linked plugins at `M=128, N=128, K=256`, independently requiring those cycle totals in both `-O0` and `-O2` probes.

### T3 — governance status contradicted the manuscript

**Accepted.** The input authorities identify v8 as a pending correction rather than claiming v7 closure. After v8 is sealed, live governance and plan state must be updated to name the actual v8 input/seal commits, while the frozen input copies retain their historically correct pre-seal status.

## Reproducibility findings

### R1 — bounded-equality summary mutation survived

**Accepted.** The manuscript validator must require the exact sentence fragment `produce the same bounded matrix output` at its exact occurrence count and independently mutate it to `produce different bounded matrix output` under normal and optimized Python.

### R2 — one empty runner argument entered release mode

**Accepted.** `run_ch21_manuscript_validation.sh ""` must return usage status 2. Release mode accepts exactly zero arguments; review mode accepts exactly one `--review` argument.

## Editorial disposition

The exact-commit editorial review passed without findings. The v8 changes are evidence, governance, and fail-closed validation corrections; they do not alter the chapter's pedagogical contract.

## Closure rule

Do not create the reviewed-snapshot marker or publish Chapter 21 until the v8 seal is immutable, the manuscript points exclusively to v8, normal and optimized validators pass, and focused exact-commit technical and reproducibility re-review return PASS.
