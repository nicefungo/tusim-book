# Chapter 20 — Source and Claim Ledger

- Date: 2026-08-16
- Status: **predraft evidence in progress; manuscript drafting blocked**
- Tusim pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Framing authority: [`chapter-20-framing-and-evidence-plan.md`](chapter-20-framing-and-evidence-plan.md)
- Claim vocabulary: **verified / qualified / rejected / blocked**

## Authorization rule

A green result authorizes only the intersection of: the named claim boundary, a discriminating disproof condition, an independent-enough oracle or invariant, the route actually reached, meaningful positive/negative/mutation controls, propagated process status, an explicit denominator, and immutable provenance. Missing one relation narrows the conclusion; it does not become evidence by proximity, naming, archive membership, or a trailing `PASS` marker.

This ledger owns evidence selection and unsafe-green interpretation. Chapter 17 retains metric producer/interval/unit/fidelity ownership; Chapter 21 retains sweep construction; Chapter 23 retains extension procedure. Chapter 19 remains closed. No claim below composes ONNX, compiler, scheduler, allocator, queue, runtime, DPI, or Python surfaces absent an executable bridge.

## Claims

### C20.1 — Verification evidence is claim-relative

- **Status:** verified.
- **Claim:** no repository result is intrinsically “strong”; its authority is bounded by the architectural relation it discriminates.
- **Required evidence:** at least one paired case where the same green producer safely supports a narrow claim but fails a stronger interpretation.
- **Evidence:** C20.4–C20.18 and the exact-value probe.
- **Limitation wording:** a green result is evidence for a named relation, not a subsystem-wide certificate.

### C20.2 — Inventory relations are not interchangeable

- **Status:** verified.
- **Claim:** source presence, Make prerequisite, recipe compilation, target existence, aggregate membership, CI selection, process execution, and report status are distinct relations.
- **Required evidence:** flattened Make parsing; exact source/target/aggregate/CI membership sets; recipe inspection.
- **Evidence:** 64 C test sources, 59 named by rule prerequisites, 31 aggregate prerequisites, four quick prerequisites, four CI-quick and 14 CI-full targets; five source-to-prerequisite omissions.
- **Limitation wording:** the five omissions are omissions from the source-prerequisite relation; `test_asm.c` is nevertheless compiled inside the `test-asm` recipe.

### C20.3 — Aggregate green has an explicit denominator

- **Status:** verified.
- **Claim:** `make test` can authorize only the 31 selected prerequisite targets, subject to each recipe’s own status behavior; it cannot authorize all 64 source-present programs.
- **Required evidence:** exact aggregate membership plus omitted membership set and status propagation.
- **Limitation wording:** aggregate success is not complete repository verification and says nothing about source-present tests outside its dependency relation.

### C20.4 — CI selection is narrower than the Make aggregate

- **Status:** verified.
- **Claim:** the workflow delegates quick/full/extended/coverage behavior to `tools/ci_runner.sh`; its unit lists select four quick or 14 full targets rather than recovering all aggregate omissions.
- **Required evidence:** workflow call inventory and exact CI runner arrays.
- **Limitation wording:** this is selection evidence, not a live GitHub Actions execution or environment-conformance claim.

### C20.5 — Producer status can be suppressed before reporting

- **Status:** verified.
- **Claim:** pinned `test-full`, quick-golden, coverage, and selected CI fallback paths can suppress or ignore failing process status.
- **Required evidence:** hash-bound recipe predicates and a negative status-propagation control.
- **Limitation wording:** static inspection establishes fail-open status mechanics; fixed host-global `/tmp` recipes remain unexecuted unless redirected into run-owned storage.

### C20.6 — A report parser can produce an unsafe green

- **Status:** verified.
- **Claim:** `tools/test_report.py` can classify a log with a counted failure and trailing `PASS` as `status=PASS`; it never receives producer exit status (`exit_code=-1`).
- **Required evidence:** executable synthetic fail-then-pass log and exact parsed fields.
- **Expected evidence line:** `REPORT_FALSE_GREEN status=PASS passed=0 failed=1 exit_code=-1`.
- **Limitation wording:** this demonstrates parser semantics for the discriminating fixture, not the status of any particular historical CI job.

### C20.7 — Counts printed beside predicates are not gates

- **Status:** verified.
- **Claim:** inventory counts authorize conclusions only when exact counts and membership sets are asserted and mutation-tested.
- **Required evidence:** fail-closed source audit, one tracked-source hash mutation, nonzero rejection, restoration, and rerun.
- **Limitation wording:** hash stability proves input identity and predicate reproducibility, not semantic correctness of a mistaken predicate.

### C20.8 — Repository golden paths have bounded independence

- **Status:** qualified.
- **Claim:** `tests/test_golden.c` contains a local scalar FP32 GEMM equation distinct from the cmodel execution path and rejects a +1 oracle mutation; `tests/test_random.c` instead imports repository `tu_golden_*` helpers and shares repository conversions/math.
- **Required evidence:** exact source producer map, 11/11 quick run, forced oracle mutation with nonzero 2/11 result.
- **Limitation wording:** the tested normal-value shapes/tolerances do not establish arbitrary binary16, exceptional-value, orientation, or external-framework agreement.

### C20.9 — The shared tensor comparator is NaN-blind

- **Status:** verified.
- **Claim:** `max_abs_error()` leaves `max_err` unchanged when `fabsf(a-b)` is NaN, allowing `compare_tensors()` to print PASS for a NaN mismatch.
- **Required evidence:** exact `expected=1`, `actual=NaN`, zero-tolerance fixture plus a finite-checking independent comparator.
- **Expected evidence line:** `ORACLE_NAN shared_accept=1 strict_accept=0 shared_pass=1 shared_fail=0`.
- **Limitation wording:** this disproves exceptional-value coverage through this comparator; it does not invalidate finite-domain passes that independently exclude non-finite values.

### C20.10 — Parsing is not configuration effect

- **Status:** verified.
- **Claim:** JSON parsing records output-stationary and runtime conversion preserves the discriminating 8×4 geometry, but drops dataflow; initialization from the converted runtime structure remains weight-stationary.
- **Required evidence:** declaration→parser→conversion predicates and executable A/B-observable state.
- **Expected evidence line:** `CONFIG_EFFECT parse_rc=0 parsed_df=1 rt_rows=8 rt_cols=4 active=weight_stationary`.
- **Limitation wording:** this claim is limited to the top-level conversion/initialization route; direct `tu_set_dataflow()` is a separate effective API.

### C20.11 — Green debug dump tests contain vacuous size checks

- **Status:** verified.
- **Claim:** text/JSON `tu_debug_dump_state()` writes bytes but returns zero because `total` is never advanced; two focused checks use unsigned `n >= 0` and therefore pass.
- **Required evidence:** exact reported and actual stream positions, 25/25 baseline, replacement by meaningful `n > 0`, and nonzero 23/25 mutant.
- **Expected evidence line:** `DUMP_SIZE reported=0 actual=338`.
- **Limitation wording:** binary dump size and full-report content have separate stronger tests; this finding applies to text/JSON byte-count authorization.

### C20.12 — A checksum tautology authorizes only non-crash

- **Status:** rejected for checksum correctness.
- **Claim rejected:** `cs != 0 || cs == 0` validates checksum semantics.
- **Evidence:** the condition is exhaustive; adjacent change/idempotence tests provide bounded stronger evidence.
- **Limitation wording:** the initial-checksum case proves only that the call returned; it cannot authorize a specific CRC value, completeness, collision resistance, or cross-version stability.

### C20.13 — Recorded trace round-trip is not behavioral replay

- **Status:** verified as a negative boundary.
- **Claim:** the focused suite tests recording, entry fields, serialization round-trip, and capacity, but never calls `tu_debug_replay_execute()`; replay execution computes checksums without issuing the instruction.
- **Required evidence:** whole-tree caller inventory and an arbitrary-opcode trace whose unchanged checksum passes, followed by a checksum-delta mutation that is detected.
- **Expected evidence line:** `REPLAY_NOOP arbitrary_opcode=0xFE mismatches_equal=0 mismatches_mutated=1 output_bytes=69`.
- **Limitation wording:** serialization and checksum comparison are executable; deterministic instruction re-execution and behavioral replay are rejected.

### C20.14 — A passing assertion helper need not enforce its advertised invariant

- **Status:** qualified.
- **Claim:** debug assertion helpers are focused-tested but have zero external non-test callers at the pin; bounds addition can wrap and tile checks ignore PE dimensions.
- **Required evidence:** caller inventory, source predicates, overflow discriminator, ordinary negative control.
- **Expected evidence line:** `BOUNDS_WRAP wrapped_accept=1 ordinary_accept=0`.
- **Limitation wording:** direct helper behavior is executable; automatic internal enforcement, overflow-safe bounds, and PE-fit validation are not established.

### C20.15 — Failure injection must be reached

- **Status:** verified as an unsafe green.
- **Claim:** the baseline error suite passes 9/9 even though its requested injection is documented not to match and is disabled; requiring the requested error yields a nonzero 8/9 mutant.
- **Required evidence:** baseline and reached-injection requirement mutation.
- **Limitation wording:** other error macros and direct reporting tests remain meaningful; the injection case does not authorize one-shot injected-failure behavior.

### C20.16 — External-boundary evidence needs a nonsymmetric discriminator

- **Status:** verified for one bounded Python/C path.
- **Claim:** archived Python `quick_gemm()` crosses ctypes into an exact archive-derived shared bridge and returns independently recomputed `[[19,22],[43,50]]`; changing one expected value is rejected.
- **Required evidence:** shape, finite values, exact residual, process status, completion marker, and mutation.
- **Limitation wording:** one normal-value 2×2 case does not establish full API coverage, config-file use, error/lifetime semantics, exceptional values, CI ownership, or an ONNX/compiler/runtime composition.

### C20.17 — Symmetric identity tests can miss orientation defects

- **Status:** qualified.
- **Claim:** DPI and Python CLI identity GEMMs exercise real calls but are invariant under many orientation/transposition mistakes; they must not alone authorize orientation.
- **Required evidence:** source inspection plus C20.16 nonsymmetric cross-boundary case.
- **Limitation wording:** identity tests remain useful lifecycle/data-path smokes; they are not orientation discriminators.

### C20.18 — Binding documentation exceeds executable coverage

- **Status:** qualified.
- **Claim:** the Python module claims “full TU core API,” but performance/power reports are stubs, `config_path` is stored without loading a configuration, and no Make/CI owner exists.
- **Required evidence:** hash-bound source predicates and bounded direct execution.
- **Limitation wording:** source presence and one working convenience function do not authorize production-grade/full-API/CI-owned binding claims.

### C20.19 — Quantitative results import Chapter 17’s contract

- **Status:** verified as governance.
- **Claim:** a test return, counter name, or field label authorizes no physical timing conclusion unless producer, interval, units, reset, clock, formula, and fidelity are named.
- **Required evidence:** Chapter 17 sealed authority; no new producer census in Chapter 20.
- **Limitation wording:** Chapter 20 selects evidence for a quantitative claim but does not redefine, combine, or calibrate metric producers.

### C20.20 — Immutable provenance is necessary but insufficient

- **Status:** verified.
- **Claim:** the drafting authority must bind exact source pin, hashed inputs, commands, outputs, mutations, manifests, validator behavior under normal/optimized Python, and skeptical review.
- **Required evidence:** inner retained manifest, outer bundle manifest, source/input mutations, validator assertion mutation, clean exact-pin before/after state, and post-review reseal.
- **Limitation wording:** a pre-review green seal is provisional; it cannot authorize drafting after review changes evidence or claim wording.

### C20.21 — Fixed host-global recipe paths are static-only evidence

- **Status:** blocked for direct execution; verified statically.
- **Claim:** `test-asm`, `test-full`, `test-compiler`, `clean`, and the CI runner touch fixed `/tmp/test_asm`, `/tmp/gpt_block_tu*`, or report paths affected by clean.
- **Required evidence:** hash-bound recipes and dry-run expansion.
- **Limitation wording:** do not execute those pinned recipes merely to demonstrate unsafe isolation; redirect every output into run-owned storage before any future live test.

### C20.22 — No end-to-end compiler/runtime claim is authorized

- **Status:** rejected.
- **Claim rejected:** archive membership, compiler output, focused scheduler/liveness tests, DPI, or Python source compose an ONNX→compiler→runtime path.
- **Evidence:** Chapter 19 closed negative boundary and C20.2/C20.5/C20.18.
- **Limitation wording:** adjacent executable surfaces remain separate until a repository-contained nontrivial bridge links, runs, propagates failures, and verifies far-boundary output.

## Predraft closure gate

Drafting remains blocked until all are true:

- [ ] canonical pre-review evidence is sealed;
- [ ] skeptical correctness review independently recomputes exact probe values and challenges every claim/evidence relation;
- [ ] all valid findings are reconciled across ledger, audit, probe, runner, and validator;
- [ ] review dispositions are durable;
- [ ] a new immutable post-review seal includes the review/dispositions inputs;
- [ ] normal and optimized post-review validation pass from clean committed state;
- [ ] Tusim remains detached, clean, and exactly pinned.

Only the final post-review seal may become Chapter 20 drafting authority.
