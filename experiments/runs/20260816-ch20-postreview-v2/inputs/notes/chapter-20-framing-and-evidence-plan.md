# Chapter 20 — Framing and Evidence Plan

- Date: 2026-08-16
- Status: **framing scope selected; drafting remains blocked**
- Tusim source pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Governing plan: [`../PLAN.md`](../PLAN.md)
- Part V checkpoint: [`whole-book-coverage-review-2026-08-10-after-ch19.md`](whole-book-coverage-review-2026-08-10-after-ch19.md)
- Reproduction script: [`../experiments/ch20_framing_recon.py`](../experiments/ch20_framing_recon.py)
- Successful reproduction: [`chapter-20-framing-reproduction.log`](chapter-20-framing-reproduction.log)
- Retained failed attempt: [`chapter-20-framing-reproduction-failed-v1.log`](chapter-20-framing-reproduction-failed-v1.log)

## Gate question

Given a green unit test, aggregate target, CI job, generated report, replay artifact, or language/binding smoke test, **what architectural claim does that evidence actually authorize, and what missing relation makes the same green result unsafe?**

This is a claim-to-evidence decision, not a catalogue of Tusim test files. The chapter should let a reader construct the minimum discriminating evidence set for a claim and reject gates whose scope, oracle, reachability, failure propagation, provenance, or independence is insufficient.

## Opening architecture question

**When does “green” mean that an architectural contract survived a realistic boundary, rather than only that one harness printed PASS or returned zero?**

## Reader decision

For a proposed Tusim claim, the reader must be able to:

1. name the claim boundary and failure that would disprove it;
2. select an oracle or invariant independent enough to discriminate that failure;
3. prove that the tested route reaches the advertised configuration, consumer, state transition, or external binding;
4. choose positive, negative, mutation, and integration controls appropriate to the claim;
5. audit aggregation and status propagation so omitted or failed evidence cannot become green;
6. retain pin, inputs, commands, outputs, and review provenance sufficient to replay the decision;
7. state the strongest safe conclusion and the unsafe stronger interpretation.

## Fresh whole-tree reconnaissance

The framing reproduction used the detached clean source checkout only for `git archive` and static reads. All builds and executions occurred in a disposable exact-pin archive. It hashed 12 governing verification surfaces and verified the source before and after as detached, clean, and pinned.

### Comparable inventory

At the pin:

- 64 C test programs exist: 43 filenames without a `sweep` token and 21 with one. This is only a reproducible filename partition: `test_conv_pool_cascade.c`, for example, describes itself as a sweep despite lacking that token;
- Makefile rules reference 59 of those source files;
- aggregate `make test` has 31 prerequisites; `make test-quick` has four;
- five test sources have no source-linked Makefile rule: `test_asm.c` is compiled by a rule without a source prerequisite, while `test_cycle_model.c`, `test_double_buffer.c`, `test_int8_sweep.c`, and `test_softmax.c` have no rule that names them;
- 13 source filenames without a `sweep` token are omitted from aggregate `make test`, including benchmark, compression, context, cycle-model, debug, double-buffer, error, power, random, softmax, and TF32 surfaces (the ASM source is also absent from source-to-rule mapping even though `test-asm` executes it). This is not a semantic claim that all 13 are non-sweep tests;
- the CI runner's quick list contains four targets and its full list contains 14, much less than the 31-target Make aggregate and the 43-source filename partition;
- the GitHub workflow delegates all jobs to that runner rather than independently recovering omitted target status.

These counts classify producers separately: source presence, Make rule, aggregate membership, CI membership, and execution are not interchangeable evidence.

### Bounded live observations from the disposable archive

The framing run observed:

- archive-local build: exit 0;
- the three archive-local quick components (`test-cmodel`, `test-cmdq`, and `test-dma`): exit 0; aggregate `test-quick` was deliberately not invoked because its `test-asm` prerequisite writes fixed `/tmp/test_asm`;
- `make test-debug`: 25/25, exit 0;
- `make test-errors`: 9/9, exit 0;
- `make test-dpi`: 13 passed, exit 0;
- `make test-random`: 9/9 suite groups, exit 0, with the documented deterministic error summary;
- Python binding nonsymmetric `2×2` GEMM discriminator: independently recomputed `[[19,22],[43,50]]`, exact at the retained precision; no Make/CI rule owns the binding and advertised performance/power methods remain stubs;
- `test-full`, `test-compiler`, `test-asm`, `clean`, and `tools/ci_runner.sh` were intentionally static-only: pinned recipes write or delete fixed host-global `/tmp/test_asm` and `/tmp/gpt_block_tu*` names, so invoking them would violate disposable isolation. Static recipe inspection establishes the compiler/run status suppression and the CI report-directory ordering defect without executing those paths;
- a synthetic log containing an earlier failure and a trailing PASS was classified PASS by `tools/test_report.py`; the parser retained `failed=1` but has no process exit status (`exit_code=-1`).

### Unsafe-green mechanisms established at framing

1. **Coverage omission:** aggregate and CI membership cover only subsets of source-present verification surfaces.
2. **Suppressed status:** `test-full` suppresses generated compile and execution failures; the coverage path suppresses `gcov` status and then records PASS.
3. **Report reinterpretation:** the report parser can label a log PASS from trailing text despite an earlier counted failure and never receives the producer's exit status.
4. **Vacuous assertions:** debug tests contain unsigned `n >= 0` checks and `cs != 0 || cs == 0`; those green results do not validate output content or checksum semantics.
5. **Non-discriminating failure injection:** the error-injection test explicitly notes that its requested injection does not match, disables injection, and still passes.
6. **Binding discriminator versus contract:** the nonsymmetric GEMM crosses the Python/C boundary and is independently recomputed, but one case does not validate advertised full-API coverage, configuration use, error propagation, broader numerical domains, or CI ownership.
7. **Oracle coupling:** golden/random tests are valuable executable evidence, but several paths reuse repository conversion or host-reference helpers; their independence and tested value domain must be stated rather than inferred from the word “golden.”

## Ranked scope candidates

| Rank | Candidate | Reader decision | Evidence density | Continuity and overlap | Principal cost/risk |
|---:|---|---|---|---|---|
| **1** | **Claim-to-evidence authorization: interpreting green gates safely** | Given a claim, choose the minimum discriminating evidence chain and decide the strongest conclusion a green result permits | Highest: unit/invariant, golden/random, config reachability, mutation, integration, aggregation/CI, reports, replay/debug, DPI/Python binding, and Chapters 1–19 seals all contribute without becoming the outline | Directly fulfills `PLAN.md`; imports Chapter 17's producer/unit discipline but owns evidence selection and failure interpretation; prepares Chapter 21's sweep methodology without teaching sweep design | Broad scope can become a catalogue unless every section is organized by claim relation and unsafe interpretation |
| **2** | Regression delivery as architecture: source → target → aggregate → CI → report | Decide whether a repository-level regression gate is complete and fail-closed | Very strong concrete negative evidence: 64/59/31/14 inventory, runner cleanup defect, suppressed statuses, report false green | Clean, narrow narrative and strong runnable examples; minimal Chapter 17 overlap | Too narrow for historical Plan 26: under-teaches oracle choice, mutation, reachability, replay, and external-boundary evidence |
| **3** | Oracle diversity and challenge testing: invariants, golden, differential, random, and mutation | Decide whether functional evidence can distinguish a targeted defect from correlated agreement | Strong focused sources and executable random/golden suites; prior chapter mutation practices add mature counterexamples | Pedagogically coherent after Chapters 1–19 and before sweep design | Risks repeating numerical Chapters 6–8/14 and leaves CI, binding, configuration propagation, provenance, and integration unsafe greens peripheral |
| **4** | Verification interfaces: debug/replay, DPI, and Python binding | Decide whether observability and external interfaces preserve a contract across a boundary | Concrete debug 25/25, error 9/9, DPI 13/13, Python smoke, plus weak/vacuous cases | Useful bridge to Chapter 23 extension paths | Overlaps Chapter 17 observability and Chapter 23 bindings/extensions; evidence is too narrow to own the verification chapter |

## Scope decision

**Select Candidate 1: Claim-to-evidence authorization and safe interpretation of green gates.**

It is the only candidate that answers the planned Chapter 20 reader decision without reducing verification to either test taxonomy or CI mechanics. Candidate 2 becomes a major worked evidence chain inside the selected scope. Candidate 3 supplies the oracle/challenge layer. Candidate 4 supplies external-boundary and replay examples, not the chapter spine.

The organizing relation is:

```text
claim boundary
  → disproof condition
  → discriminating oracle/invariant
  → exercised route and state
  → positive + negative + mutation controls
  → aggregate/status propagation
  → retained provenance + independent review
  → safe conclusion / unsafe stronger conclusion
```

## Planned evidence-selection matrix

The predraft gate must populate, hash, predicate, and challenge at least these claim classes:

| Claim class | Minimum evidence relation | Candidate Tusim surfaces | Unsafe green interpretation to reject |
|---|---|---|---|
| Functional value | independent-enough oracle, discriminating values, tolerance/domain, output closure, mutation | `test_golden.c`, `test_random.c`, focused engine tests, shared test framework | “golden/random passed” proves arbitrary data types, edge values, or independent implementation |
| Configuration effect | declaration → parser/generator → runtime conversion → consumer → observable A/B effect | config tests and Chapters 4/7/13/15 findings | parsed or validated means selected behavior reached execution |
| Lifecycle and failure | transition inventory, global invariant, negative target, failure atomicity, reached injection | queue/DMA/context/error/debug surfaces | happy-path count or non-crash check proves ownership, retirement, recovery, or rejected-call atomicity |
| Quantitative/timing | named producer, interval, units, clock, reset, formula, calibration rung | import Chapter 17 taxonomy and relevant prior seals | a test return or field label is elapsed/calibrated hardware time |
| Integration/binding | actual caller, data/control crossing, ABI/lifetime/error semantics, effect at the far boundary | DPI, Python binding, ONNX negative boundary | archive membership, include, wrapper smoke, or generated text proves end-to-end composition |
| Regression/release | exhaustive inventory, fail-closed target/status propagation, mutation, immutable inputs/manifests, exact review binding | Makefile, CI workflow/runner, report generator, Chapters 12–19 validators | aggregate/CI/report green means every source-present or claim-critical check ran and passed |
| Replay/debug evidence | content schema, completeness, deterministic replay relation, corruption/truncation negatives | `tu_debug` dump/checksum/record surfaces | serialization round-trip or non-empty output proves state completeness or behavioral replay |

## Inclusions

- evidence selection by claim and explicit disproof condition;
- unit/property/invariant, golden/differential/random, negative, mutation, integration, and regression evidence as distinct roles;
- configuration propagation and consumer-effect evidence;
- Make/CI/report status propagation and coverage inventory;
- replay/debug/error evidence only as verification contracts;
- DPI and Python binding examples only as external-boundary evidence;
- immutable manifests, exact-pin execution, optimization-safe validators, exact-commit review, and reviewed-snapshot binding as evidence-preservation architecture;
- unsafe green-gate interpretations and the cost/trade-off of stronger evidence.

## Explicit exclusions

- no Chapter 17 metric-producer catalogue, unified timeline, or new metric semantics;
- no reopening of Chapter 18 retained-state semantics or Chapter 19 scheduler/liveness legality;
- no composed ONNX/compiler/scheduler/allocator/queue/runtime path;
- no claim that Python source presence or DPI archive membership establishes an end-to-end compiler/runtime system;
- no sweep-design tutorial or portfolio synthesis (Chapters 21 and 22);
- no extension tutorial (Chapter 23);
- no repetition of every prior audit log; prior chapters contribute bounded counterexamples selected by claim class;
- no Chapter 20 manuscript until the source/claim ledger, fail-closed audit, skeptical review, and post-review evidence seal close.

## Continuity boundaries

- **From Chapter 17:** import the rule that every quantitative claim names producer, interval, units, reset, clock, and fidelity. Chapter 20 asks which evidence authorizes the claim; it does not redefine the producers.
- **From Chapter 18:** import lifecycle and failure-atomicity counterexamples only. Do not reteach retained-state modes.
- **From Chapter 19:** import transform authorization as an example of relation-complete evidence. Do not reteach scheduler or allocator semantics and do not infer a runtime bridge.
- **To Chapter 21:** Chapter 20 establishes what evidence can authorize a claim. Chapter 21 will design controlled sweeps that produce such evidence; it owns alternatives, sensitivity, and sweep methodology.
- **To Chapter 23:** Chapter 20 may identify binding/config verification gaps, but Chapter 23 owns how to carry an extension through every contract surface.

## Risk-register disposition

- **Chapter 17/20 overlap — triggered and resolved by boundary:** Chapter 17 owns producer/interval/unit/fidelity; Chapter 20 owns claim/evidence selection, challenge controls, and green-gate interpretation.
- **Broad synthesis becoming a catalogue — triggered and resolved provisionally:** the selected spine is the claim-authorization relation. Directories and test classes are evidence examples, never top-level organization.
- **Completed-chapter supplement backlog — reviewed, not triggered for execution:** Chapters 8/10/14 supplements remain deferred to the mandatory post-Chapter-20 checkpoint. Framing examples may cite gaps but may not reopen those chapters.
- **Source-edition drift — not triggered:** `edition.yaml` and live source remain at `e918c80`.
- **Broken compiler path — triggered by `test-full`, resolved negatively:** static inspection shows both generated compile and execution status are suppressed; the path was not executed because its fixed host-global `/tmp/gpt_block_tu*` names violate isolation. This evidence does not authorize a composed compiler/runtime story.
- **Disposable isolation — triggered and resolved:** `test-quick`, `test-full`, `test-compiler`, `test-asm`, `clean`, and the CI runner can write or delete fixed host-global `/tmp` names. Canonical framing execution excludes them; every selected Make invocation is first dry-run and rejected if its expanded recipe mentions `/tmp`.
- **Chapter 21/22 repetition — not yet triggered:** Chapter 20 excludes sweep construction and portfolio conclusions.
- **Stable numbering — not triggered:** retain Chapter 20 and the 23-chapter architecture.

## Framing evidence gate

Framing can close only when all are true:

- [x] live book, remote, and source states verified;
- [x] source detached, clean, and pinned before and after;
- [x] fresh whole-tree inventory separates source, rule, aggregate, CI, and execution membership;
- [x] at least three evidence-backed candidates ranked before selection;
- [x] selected scope has one reader decision, explicit inclusions/exclusions, and continuity boundaries;
- [x] plan risks are resolved or deferred explicitly;
- [x] reproduction script and complete combined log are retained;
- [x] independent skeptical framing review completed and dispositions reconciled;
- [x] final framing reproduction rerun after any review amendments;
- [x] framing governance/status committed from a clean tree.

Even after this framing gate closes, **drafting remains blocked**. The next session must create the Chapter 20 source-and-claim ledger, build the fail-closed exact-pin audit and discriminating probes/mutations, conduct skeptical pre-draft review, and seal post-review evidence before writing manuscript prose.
