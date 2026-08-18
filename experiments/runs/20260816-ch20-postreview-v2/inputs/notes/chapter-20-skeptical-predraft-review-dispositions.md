# Chapter 20 skeptical predraft review dispositions

- Date: 2026-08-16
- Source pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Reviewed provisional run: `experiments/runs/20260816-ch20-canonical-v1`
- Reviewed book commit: `ed67f181dd6b51f733907408689ea1e7c2e72fc1`
- Review method: two independent read-only reviews using the skeptical review playbook; both hand-recomputed probe values from pinned source and audited the audit rather than trusting green markers.
- Initial verdict: **BLOCK**
- Current disposition: **open pending post-review v2 seal**

The provisional v1 run remains immutable and cannot authorize drafting. Every accepted finding below is a claim-bearing input to the post-review run.

## R1 — Fail-open body pipeline

- Severity: BLOCKER.
- Finding: parent `set +e` disabled effective fail-fast behavior inside `body()`, allowing an early failed gate to be overwritten by a later success.
- Disposition: **accepted**.
- Required closure: run `body()` in a subshell with explicit `set -euo pipefail`; retain a deliberate early-failure control proving nonzero status, no survivor/completion marker, and exact clean/detached source state afterward; keep trap-time source checking active through closure.

## R2 — Exact membership sets and same-cardinality mutation

- Severity: HIGH.
- Finding: counts were correct, but most complete source/rule/aggregate/quick/CI sets were not asserted; the only mutation challenged a source hash.
- Disposition: **accepted**.
- Required closure: literal exact 64-source set, complete source→target relation, exact 31 aggregate targets, exact four quick targets, exact CI quick/full sets, exact five prerequisite omissions, and exact 13 non-sweep aggregate omissions; swap one aggregate member while preserving cardinality and require the semantic set predicate to fail after rebinding the mutated Make hash.

## R3 — Configuration routes were conflated

- Severity: HIGH.
- Finding: the probe showed one OS parse followed by WS effect, not the ledger’s promised A/B; it then silently called `tu_core_init()`, replacing the created 8×4 instance with default 16×16 state. `tu_cmodel.c`, `tu_core.c`, and `tu_config.h` were not hash-bound.
- Disposition: **accepted**.
- Required closure: hash and predicate all three files; run WS/OS JSON A/B cases, show both converted routes select WS, retain a direct OS setter positive control, and gate `created=8x4 reinitialized=16x16`; mutate the initialization consumer and require rejection.
- Authorized wording: parsing stores dataflow, conversion drops it, top-level initialization selects compile-time WS; separately, `tu_core_init()` discards the created instance geometry and reinstates compile-time 16×16 defaults.

## R4 — Oracle independence excludes exceptional values

- Severity: MEDIUM.
- Finding: `test_golden.c` has an independent finite scalar equation but duplicates the NaN-blind maximum-error pattern.
- Disposition: **accepted qualification**.
- Required closure: predicate the local comparator and its tolerance gate; state that equation independence for finite normal inputs is not exceptional-value-oracle independence.

## R5 — Debug dump byte provenance

- Severity: MEDIUM.
- Finding: `actual=338` is the default 16×16 dump after reinitialization, not the earlier 8×4 created-core dump.
- Disposition: **accepted qualification**.
- Required closure: gate the 8×4→16×16 lifecycle transition and label the exact byte observation accordingly.

## R6 — Deterministic random duplication

- Severity: HIGH.
- Finding: `make test-random` already executes the binary; CI calls that target as “compilation” and then executes the same fixed-seed streams a second time. Two processes do not provide two independent vector sets.
- Disposition: **accepted new claim**.
- Required closure: predicate exact Make execution, second CI invocation, and seed set `{42,99,777,888}`; change one seed under a rebound source hash and require the semantic census to reject.

## R7 — DPI and Python boundary precision

- Severity: HIGH.
- Finding: the Python nonsymmetric case is valid, but `tests/test_dpi.c` is native C-to-C wrapper evidence, not an HDL simulator boundary; identity GEMM is orientation-insensitive, and async/LayerNorm cases do not verify far-boundary numerical output. The Python no-owner check was too weak.
- Disposition: **accepted**.
- Required closure: predicates for native producer, identity operands, no simulator invocation, async no-output-check, LayerNorm no-output-check, and exact absence of binding identifiers across Make/CI/workflow.

## R8 — Ungated reader-visible structural claims

- Severity: HIGH.
- Finding: CI compile fallback suppression, tile checks ignoring PE dimensions, separate power/performance stubs, and static-only dry-run evidence lacked matching gates.
- Disposition: **accepted**.
- Required closure: named structural predicates; executable oversized-tile discriminator; synthetic CI fallback status control; separate stub predicates; retained dry-run expansion for selected safe and forbidden fixed-path targets without executing them.

## R9 — Failure-path preservation and sanitizer scope

- Severity: HIGH.
- Finding: success-path source preservation did not establish failure-path preservation. The sanitizer probe linked an archive built without sanitizer instrumentation.
- Disposition: **accepted**.
- Required closure: R1 failure control; rebuild the complete disposable archive with ASan/UBSan flags before linking the sanitizer probe, or retain an explicit unsanitized-library limitation. The selected closure is full archive instrumentation, with leak checking excluded only because the global singleton has no teardown route.

## R10 — Optimized validation and trust hierarchy

- Severity: MEDIUM.
- Finding: only body-mode optimized validation was retained; default/outer optimized results were live-only. `bundle-sha256.txt`, `bundle-check.log`, and closure logs are not recursively manifest-bound.
- Disposition: **accepted**.
- Required closure: retain normal/optimized body and pre-outer validation; run normal/optimized outer closure; document inner manifest → outer root → derived checks → exact Git sealing commit. Do not call derived closure logs manifest-sealed.

## R11 — Input and sealing-commit binding

- Severity: MEDIUM.
- Finding: frozen inputs match `input_commit`, but validator did not verify that a sealing commit’s first parent is the input commit and that only the intended run directory changed.
- Disposition: **accepted**.
- Required closure: post-commit validation mode taking an exact seal OID; require commit type, first-parent equality, exact run-only changed paths, and run-tree equality. Record this post-seal result in the handoff rather than rewriting the sealed run.

## R12 — Status drift

- Severity: MEDIUM.
- Finding: report/ledger status lagged the existing provisional v1, while C20.20 was marked verified despite requiring review and post-review reseal.
- Disposition: **accepted**.
- Required closure: mark v1 sealed but provisional/superseded; mark governance policy separately from drafting authority; close checklist items only after evidence exists.

## R13 — Findings that survived review unchanged

- Disposition: **resolved/no amendment beyond preservation**.
- Surviving boundaries: exact NaN arithmetic; replay as checksum comparison without behavioral issue; unsigned bounds wrap; unreachable failure-injection negative conclusion; Chapter 17/21/23 ownership; Chapter 19 closure; refusal to infer ONNX/compiler/runtime composition; v1 frozen-input and manifest authenticity.

## Reconciliation state

All accepted R1–R12 findings are implemented across the ledger, audit report, source audit, probe, runner, and validator. Disposable-clone run `preflight-postreview-v6` passed normal and optimized outer validation. This is implementation preflight only: the exact-current book inputs still require a committed input checkpoint, canonical post-review run, direct-child run-only seal commit, and `--sealed-at` verification before drafting can be authorized.

## Closure criteria

This review reaches `CLOSED-PASS` only when:

- [ ] all accepted predicates, probes, mutations, wording qualifications, and runner controls are committed;
- [ ] a clean-input post-review v2 run is sealed under a new immutable run ID;
- [ ] normal and optimized validation pass in all retained modes;
- [ ] post-seal parent/path/tree validation passes against the exact run commit;
- [ ] the live Tusim checkout remains detached, clean, read-only, and exactly pinned;
- [ ] no Chapter 20 manuscript exists.
