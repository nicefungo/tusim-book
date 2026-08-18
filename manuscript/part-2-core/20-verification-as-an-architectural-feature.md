# Chapter 20 — Verification as an Architectural Feature

A green result is not a property of a subsystem. It is the outcome of one producer, over one route, with one oracle, one set of inputs, and one rule for propagating failure. The same result may strongly support a bounded functional claim and provide almost no evidence for integration, exceptional values, timing, or complete repository coverage.

This chapter asks one practical question:

> Given a green unit, aggregate, CI, report, replay, or binding gate, what is the strongest architectural claim that result authorizes—and which missing relation makes a stronger interpretation unsafe?

At the pinned Tusim revision, the answer cannot be read from target names or pass counts alone. Sixty-four C test sources exist, while the `make test` aggregate selects exactly 31 prerequisite targets. A shared tensor comparator accepts one discriminating NaN mismatch. JSON parsing records a dataflow request that the examined runtime-conversion route drops. A replay routine compares checksums without issuing the recorded instruction. A report parser can retain a counted failure yet assign `status=PASS` from later text. Conversely, a nonsymmetric Python-to-C matrix case crosses a real language boundary and exactly matches an independently recomputed result—but only for that one bounded case.

The unifying discipline is **claim-to-evidence authorization**:

```text
claim boundary
    → disproof condition
    → discriminating oracle or invariant
    → exercised route and state
    → positive + negative + mutation controls
    → aggregation and status propagation
    → immutable provenance + independent review
    → safe conclusion / unsafe stronger conclusion
```

Every arrow is an architectural relation. Verification is therefore not a box checked after the design. It is part of the design contract: it determines which states are observable, which failures can be distinguished, which boundaries are exercised, and which conclusions remain unavailable.

## Learning objectives

After completing this chapter, the reader should be able to:

1. define a verification claim by its boundary and targeted disproof condition;
2. distinguish source presence, Make prerequisite ownership, recipe compilation, target existence, aggregate selection, CI selection, process execution, and report status;
3. select an oracle or invariant whose independence and value domain are sufficient for the claim;
4. prove configuration effect through declaration, parsing, conversion, consumer selection, and observable A/B behavior rather than parsing alone;
5. use negative and semantic mutation controls to determine whether a green gate can reject the intended defect;
6. separate serialization, checksum comparison, native wrappers, and language bindings from stronger replay or integration claims;
7. audit process-status propagation and explicit denominators across Make, CI, and report layers;
8. preserve exact inputs, outputs, manifests, validator behavior, and review provenance without treating reproducibility as semantic correctness;
9. import Chapter 17’s producer/interval/unit/fidelity contract for quantitative claims without redefining or combining metric producers;
10. compare verification architectures by defect sensitivity, execution cost, isolation, maintenance burden, and evidentiary strength.

## Prerequisite graph

```text
Chapter 2: model contracts, verification, validation, calibration
                         ┐
Chapter 4: declaration → parser → runtime → consumer
                         ├──→ Chapter 20: claim-to-evidence authorization
Chapter 5: lifecycle, ownership, and failure boundaries
                         ┤
Chapter 17: producer, interval, units, clock, reset, fidelity
                         ┘

Chapter 18: lifecycle counterexamples only; retained-state modes stay closed
Chapter 19: relation-complete authorization example only; transforms stay closed

Chapter 20 ──→ Chapter 21: evidence requirements only
               (Chapter 21 owns sweep construction and sensitivity method)
            └→ Chapter 23: verification gaps only
               (Chapter 23 owns extension procedure)
```

The reader should already distinguish verification from validation and calibration, and should understand that linked code, reachable execution, observed effects, and physical fidelity are separate evidence rungs. Chapter 17 remains authoritative whenever a claim contains cycles, rates, power, energy, utilization, or another quantitative producer. This chapter asks whether evidence authorizes such a claim; it does not create a common timeline or calibrate any producer.

## Opening architecture question

Suppose a CI report says `PASS`. What had to happen for that word to authorize “the architecture contract survived”?

A strong answer needs more than a test binary somewhere in the repository. The relevant source must belong to an intended target; the intended target must be selected; its recipe must execute the relevant code; the input must force the threatened relation to matter; the oracle must notice the wrong outcome; failure must reach the process status; every wrapper must preserve that status; the report must not reinterpret later text as success; and the retained evidence must identify exactly which revision and commands produced the result.

If any relation is missing, the conclusion narrows. A green target may still prove a useful local property. It simply cannot serve as a subsystem-wide certificate.

---

## 20.1 Theory: evidence authority is an intersection

Let a proposed claim be \(C\). Define these authorization relations:

- \(R_b\): the claim boundary is explicit;
- \(R_d\): a concrete disproof condition is named;
- \(R_o\): the oracle or invariant distinguishes that condition over the tested domain;
- \(R_r\): the advertised execution route is actually reached;
- \(R_c\): positive, negative, and mutation controls behave meaningfully;
- \(R_s\): selection, denominator, and process status remain intact;
- \(R_p\): inputs, commands, outputs, and review provenance are bound.

Then a useful authorization rule is

\[
\operatorname{Authorized}(C)=
R_b\land R_d\land R_o\land R_r\land R_c\land R_s\land R_p.
\]

This is not a numerical confidence score. One missing relation cannot be averaged away by many passing examples elsewhere. A thousand executions of a non-discriminating identity case do not establish orientation. A cryptographic hash of a mistaken predicate reproduces the mistake exactly. A complete source inventory does not prove that all members executed. A strong oracle cannot validate a configuration branch that the route never selected.

### Claim boundary and disproof condition

A claim should identify both what is inside and what would make it false. Compare:

- weak: “the binding works”;
- bounded: “for finite normal values in one nonsymmetric `2×2` case, archived Python `quick_gemm()` crosses ctypes into the archive-derived C bridge and returns the independently recomputed matrix exactly.”

The bounded claim identifies language boundary, operation, shape, value domain, route, and expected output. Its disproof conditions include wrong orientation, wrong values, non-finite output, process failure, or missing completion. It does **not** claim full API coverage, configuration loading, lifetime/error semantics, exceptional-value behavior, CI ownership, or a compiler/runtime composition.

### Oracle adequacy has at least three dimensions

An oracle is not “independent” in the abstract. Its authority depends on:

1. **equation independence**—whether expected values come from a distinct computation;
2. **implementation independence**—whether code, conversion helpers, tolerances, and state are shared;
3. **domain independence**—whether the comparison remains meaningful for the claimed values, including exceptional values.

A local scalar GEMM can supply a structurally distinct equation for finite normal inputs while using the same NaN-blind maximum-error pattern as the implementation-side framework. Its finite-domain evidence survives; exceptional-value authorization does not.

### Controls ask whether the gate can fail for the right reason

A positive control proves the ordinary fixture can pass. A negative control puts a known bad state at the boundary. A semantic mutation changes the claimed relation while preserving as much scaffolding as possible. Together they answer different questions:

- can the harness run?
- can it observe a bad outcome?
- can it reject the specific defect the claim excludes?
- does rejection propagate to the process and report?

A source-hash mutation proves drift detection. It does not prove that an exact membership predicate is correct. For that, a stronger control preserves the aggregate count while swapping one member and requires the set predicate to reject the change.

## 20.2 Source map: producers, selectors, interpreters, and preserved evidence

Chapter 20 is organized by evidence relations, not by test directories. The main source surfaces at Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25` are:

| Evidence role | Repository-relative surface | Safe use in this chapter |
|---|---|---|
| build and aggregate selection | `Makefile` | exact prerequisite, recipe, aggregate, and dry-run relations |
| CI selection and fallback | `.github/workflows/ci.yml`, `tools/ci_runner.sh` | static selection and status mechanics; not a live GitHub Actions run |
| report interpretation | `tools/test_report.py` | executable parser semantics for a synthetic discriminating log |
| shared comparison helpers | `tests/test_framework.h` | exact comparator behavior, including the NaN limitation |
| local and repository golden paths | `tests/test_golden.c`, `tests/test_random.c` | finite equation and shared-helper boundaries |
| configuration route | `tu_cmodel/infra/config.[ch]`, `tu_cmodel/tu_cmodel.c`, `tu_cmodel/tu_core.c`, `tu_cmodel/tu_config.h` | parsing, conversion, initialization, direct setter, and reinitialization as separate routes |
| debug, checksum, assertion, and replay | `tu_cmodel/infra/tu_debug.[ch]`, `tests/test_debug.c`, `tests/test_error_handling.c` | exact local behavior and negative boundaries |
| native wrapper | `tu_cmodel/bindings/tu_dpi.[ch]`, `tests/test_dpi.c` | native C-to-C evidence only; no HDL simulator boundary |
| Python binding | `bindings/python/tu_bindings.py` | one bounded ctypes case plus static stub/config/ownership findings |
| sealed Chapter 20 evidence | `experiments/runs/20260816-ch20-postreview-v2/` | exact source identity, probes, mutations, manifests, and validation |

The evidence producer, selector, and interpreter must remain separate. A C source file is a potential producer. A Make rule may compile or execute it. An aggregate selects targets. CI selects another set. A report parser interprets text after execution. None of these relations implies the next.

The canonical source audit binds 22 source files, checks the source pin, and evaluates 52 structural predicates, for 75 total checks. These numbers describe the Chapter 20 audit’s own bounded inventory. They are not a timeless property of future Tusim revisions.

## 20.3 Coverage is a relation, not a count

At the pinned revision, the exact inventory is:

```text
C test source programs                     64
sources named by Make rule prerequisites   59
make test prerequisite targets             31
make test-quick prerequisite targets         4
CI quick selected targets                    4
CI full selected targets                    14
source-to-prerequisite omissions             5
```

These denominators answer different questions.

### Source presence versus rule ownership

Five C test sources are omitted from the mechanical source-to-prerequisite relation. That statement must not be broadened to “five tests have no executable target.” In particular, `tests/test_asm.c` is compiled inside the `test-asm` recipe even though the source is not named as a rule prerequisite. The other named omissions need their own target analysis.

A prerequisite map describes declared dependencies. Recipe compilation describes commands inside the rule body. Aggregate membership describes which targets another target selects. Execution describes what a recipe actually launches. Conflating these relations turns a reproducible inventory into a false coverage claim.

### The 31-target aggregate denominator

`make test` has exactly 31 prerequisite targets. Its success can authorize only those selected targets, subject to each target recipe’s own status behavior. It cannot authorize all 64 source-present programs, and it says nothing about source-present checks outside that dependency relation.

The distinction matters even when counts appear stable. The canonical audit mutation replaces selected `test-dpi` with omitted `test-debug`, preserves the count at 31, rebinds the changed Makefile hash, and still requires rejection. This establishes that complete literal membership—not cardinality alone—gates the conclusion.

### CI is another selector, not an automatic superset

The workflow delegates quick, full, extended, and coverage behavior to `tools/ci_runner.sh`. The runner’s exact unit lists select four quick or 14 full targets. This is narrower than the 31-target Make aggregate and does not recover all source-present omissions.

This is static selection evidence. It is not evidence that a particular hosted runner had the expected toolchain, environment, filesystem state, or successful GitHub Actions execution. A live CI claim would need that additional provenance.

### Filename partitions are not semantic classes

The framing inventory found 43 filenames without the token `sweep` and 21 with it. That is a lexical partition only. A source such as `test_conv_pool_cascade.c` may describe itself as a sweep without carrying the token. Chapter 21 owns sweep construction and methodology; Chapter 20 uses this case only to show that a filename classifier cannot silently become a producer taxonomy.

## 20.4 Oracle independence: finite equations and exceptional values

A passing “golden” test is useful only after the expected-value path and comparator are audited.

### A finite-domain independent equation

`tests/test_golden.c` contains a local scalar FP32 GEMM equation distinct from cmodel execution. Its quick suite reports `11/11`. The Chapter 20 semantic mutation changes the local reference to `sum + 1`; the suite then reports `2/11` and exits nonzero. For the tested finite normal inputs, this establishes that the local equation can distinguish the injected arithmetic defect.

The safe conclusion is narrow: the tested finite equations discriminate that mutation. It does not establish arbitrary binary16 behavior, exceptional values, orientation, or agreement with an external framework.

`tests/test_random.c` has a different independence profile. It imports repository `tu_golden_*` helpers and shares repository conversions and mathematical assumptions. Randomized inputs can broaden sampled cases while remaining coupled to the same oracle family. Randomness does not automatically create implementation independence.

### The NaN-blind comparator

The shared `max_abs_error()` computes an absolute difference and updates `max_err` when the new value is larger. If `fabsf(expected-actual)` is NaN, the comparison does not update `max_err`. A zero tolerance can therefore accept a mismatch such as `expected=1` and `actual=NaN`.

The exact discriminator reports:

```text
ORACLE_NAN shared_accept=1 strict_accept=0 shared_pass=1 shared_fail=0
```

A finite-checking independent comparator rejects the same pair. This disproves exceptional-value coverage through the shared comparator. It does not invalidate finite-domain passes that independently exclude non-finite values.

The local comparator in `test_golden.c` duplicates the same maximum-error pattern. Its scalar equation is structurally distinct for finite normal inputs, but equation independence does not establish an independent exceptional-value oracle.

### Repeated deterministic execution is not independent sampling

In CI random mode, `make test-random` compiles and executes the binary; the CI runner then executes `./test-random` again. Fixed seeds `42`, `99`, `777`, and `888` make the second process repeat the same vector streams.

The source audit gates the exact Make execution relation, the second CI invocation, and the seed set. A seed mutation from 42 to 43, with the changed source hash rebound, must be rejected. The authorized interpretation is:

> two process invocations exercise one deterministic vector set per fixed seed; invocation count is not independent sample count.

This chapter does not turn that observation into a sweep-design prescription. Choosing distributions, alternatives, sensitivity, and sampling strategy belongs to Chapter 21.

## 20.5 Configuration effect requires route-complete evidence

A configuration claim needs a chain:

```text
declaration → parser → conversion → consumer → observable effect
```

A green parser test establishes only the relations it exercises.

### Parsed dataflow versus effective dataflow

The Chapter 20 A/B case parses weight-stationary and output-stationary JSON inputs. The parser records both requests. Runtime conversion preserves discriminating `8×4` geometry but drops dataflow. Through that converted initialization route, both cases become compile-time weight-stationary. A separate direct setter remains effective for output-stationary.

The exact line is:

```text
CONFIG_AB ws_parse=0 os_parse=0 ws_df=0 os_df=1 rt_rows=8 rt_cols=4 ws_active=weight_stationary os_active=weight_stationary direct_os=output_stationary
```

The safe interpretation preserves all three route distinctions:

1. parsing records the requested dataflow;
2. the examined runtime conversion drops it, and converted initialization selects compile-time weight-stationary;
3. direct `tu_set_dataflow(OS)` is a separate effective route.

“Output-stationary parsed” must not be rewritten as “output-stationary executed.” Conversely, the dropped converted route does not prove that the direct setter is ineffective.

### Creation versus reinitialization

`tu_core_create(&rt)` initially preserves the converted `8×4` geometry. A later `tu_core_init()` discards that instance configuration and reinstates compile-time `16×16` defaults:

```text
CORE_REINIT_GEOMETRY created_8x4=1 reinitialized_16x16=1 created_bytes=336 reinitialized_bytes=338
```

The byte observations help bind fixture identity. The 336-byte text/counters dump belongs to the created `8×4` core; the 338-byte dump belongs to the default `16×16` core after reinitialization. These are pin/toolchain observations, not API constants.

A semantic mutation forces the initialization consumer to output-stationary. Both converted A/B routes then become output-stationary, and the Chapter 20 gate rejects the changed relation. This is stronger than checking that configuration text was parsed or that a field existed in a structure.

## 20.6 Vacuous assertions, reached failures, and lifecycle invariants

A check can be syntactically present yet unable to reject the threatened behavior.

### Debug dump size: bytes written, zero returned

Text and JSON `tu_debug_dump_state()` write bytes but return zero because `total` is never advanced. Two focused tests use unsigned `n >= 0`, which is true for every value of `n`. The baseline suite reports `25/25`.

The exact post-reinitialization observation is:

```text
DUMP_SIZE fixture=post_reinit_16x16 reported=0 actual=338
```

Replacing the two vacuous conditions with meaningful `n > 0` checks yields `23/25` and a nonzero process status. The safe conclusion is that the baseline count does not authorize text/JSON byte-return correctness. Binary dump size and full-report content have separate stronger tests; they are not invalidated by this finding.

### A tautology proves only that the call returned

The condition

```c
cs != 0 || cs == 0
```

is exhaustive. It cannot validate checksum semantics. At most, that initial-checksum case proves that the call returned. Adjacent change and idempotence tests provide bounded stronger evidence, but the tautology cannot authorize a particular CRC, state completeness, collision resistance, or cross-version stability.

### Requested error injection must be reached

The baseline error suite reports `9/9`, although its requested injection is documented not to match and is disabled. Requiring that requested error to occur produces `8/9` and a nonzero status.

Other error macros and direct reporting tests remain meaningful. The rejected claim is narrower: this injection case does not authorize one-shot injected-failure behavior because the requested failure never reached the boundary.

### Local helper success is not automatic internal enforcement

Debug assertion helpers are directly executable and focused-tested, but whole-tree lexical analysis finds zero external non-test callers at the pin. Their direct behavior therefore cannot be presented as automatic internal enforcement.

Two discriminators expose further limits:

```text
BOUNDS_WRAP wrapped_accept=1 ordinary_accept=0
TILE_PE_IGNORED oversized_accept=1 zero_reject=1
```

Unsigned bounds addition can wrap, while an ordinary out-of-bounds case is rejected. Tile checks reject zero but ignore PE dimensions, so an oversized tile is accepted. These observations authorize exact helper behavior for the fixtures. They do not establish overflow-safe bounds or PE-fit validation throughout the cmodel.

## 20.7 Serialization is not behavioral replay

A debug trace can preserve useful evidence without implementing behavioral replay.

The focused suite exercises recording, entry fields, serialization round-trip, and capacity. It does not call `tu_debug_replay_execute()`. The replay routine itself computes and compares checksums without issuing the recorded instruction.

The bounded arbitrary-opcode fixture reports:

```text
REPLAY_NOOP arbitrary_opcode=0xFE mismatches_equal=0 mismatches_mutated=1 output_bytes=69
```

With unchanged state, checksum comparison reports no mismatch even though the arbitrary instruction was never issued. Mutating the compared checksum is detected. The 69-byte output observation is fixture-specific.

The focused suite separately establishes serialization round-trip. For the bounded arbitrary-opcode fixture, recording an in-memory entry and invoking checksum-comparison replay are executable, while deterministic instruction re-execution and behavioral replay are rejected.

This distinction generalizes. A round-trip test establishes encode/decode consistency under the tested schema. It does not prove that the schema captures all behaviorally relevant state. A checksum comparison establishes equality under the checksum relation. It does not prove that a transition occurred.

## 20.8 External boundaries need discriminating values and far-boundary checks

A wrapper can execute real code while leaving the central boundary under-tested.

### Native DPI wrapper evidence

`tests/test_dpi.c` is native C-to-C wrapper evidence. No HDL simulator boundary is exercised. Its identity GEMM operands are invariant under many orientation or transposition mistakes. The async and LayerNorm cases exercise calls but do not verify far-boundary numerical output.

The safe use is therefore lifecycle/data-path smoke evidence for the named native wrapper calls. It cannot alone authorize orientation, HDL integration, or far-boundary numerical correctness.

### One bounded Python/C discriminator

The archived Python `quick_gemm()` case crosses ctypes into an exact archive-derived shared bridge. It uses nonsymmetric matrices and independently recomputes:

```text
[[19, 22],
 [43, 50]]
```

The retained check reports:

```text
BINDING_NONSYMMETRIC shape_ok=1 finite=1 max_abs=0 observed=[[19.0, 22.0], [43.0, 50.0]]
```

Changing one independently expected value is rejected. This is real bounded evidence for value and orientation across one Python/C route.

It remains one normal-value `2×2` case. It does not establish full API coverage, configuration-file use, error or lifetime semantics, exceptional values, performance, power, or CI ownership. The Python module stores `config_path` without loading a configuration; performance and power report methods are separate stubs; no Make/CI owner is identified for the binding.

Most importantly, source adjacency does not create a larger stack. Python source, native wrappers, compiler output, scheduler and liveness tests, archive membership, and runtime code remain separate surfaces. No ONNX/compiler/scheduler/allocator/queue/runtime composition is authorized. Chapter 19 remains closed.

## 20.9 Regression delivery: how failure becomes green

Even a discriminating test loses authority if failure status is suppressed or reinterpreted.

### Fail-open recipes and fallbacks

Static inspection at the pin establishes that `test-full`, quick-golden, coverage, and selected CI fallback paths can suppress or ignore failing process status. The CI compile fallback can turn a failed producer status into a propagated zero without setting the expected overall failure state.

This is static evidence about status mechanics. It is not a claim about the outcome of a particular historical CI job.

Several pinned recipes use fixed host-global paths such as `/tmp/test_asm` and `/tmp/gpt_block_tu*`; `clean` and the CI runner also affect fixed paths or report directories. Those recipes were retained as dry-run expansions but not executed merely to demonstrate unsafe isolation. Future live execution would first need every output redirected into run-owned storage.

This limitation matters methodologically: verification must not damage unrelated host state in order to prove that a recipe is unsafe. Static hash-bound evidence is the correct rung when a safe isolated execution path has not been constructed.

### A report can disagree with its own failure count

For a synthetic log containing a counted failure followed by trailing `PASS`, `tools/test_report.py` reports:

```text
REPORT_FALSE_GREEN status=PASS passed=0 failed=1 exit_code=-1
```

The parser retains `failed=1`, assigns `status=PASS`, and never receives producer exit status. This demonstrates parser semantics for the discriminating fixture. It does not establish the status of any historical CI report.

A fail-closed report architecture should preserve at least:

- producer identity;
- producer exit status;
- selected target and command;
- explicit pass/fail counts with defined parsing rules;
- parser status;
- disagreement handling;
- incomplete or missing-output handling.

A trailing token should not overrule a nonzero producer status or a counted failure without an explicit, reviewed policy.

### Runner fail-fast behavior is itself a verification claim

The provisional Chapter 20 evidence run was blocked because parent shell state disabled effective fail-fast behavior inside the body pipeline. An early failure could be overwritten by a later success. The post-review runner executes the body in an explicit `set -euo pipefail` subshell and retains a deliberate early-failure control.

That control requires:

- nonzero status;
- no survivor or completion marker;
- a source-state check even on failure;
- exact detached, clean, pinned source state afterward.

The lesson is recursive: the audit runner and validator are part of the architecture of evidence. Their status and cleanup behavior need positive and negative controls just as the modeled component does.

## 20.10 Worked claim-authorization ledgers

A compact ledger prevents evidence from expanding beyond its boundary.

### Case A: “the output-stationary JSON setting works”

| Relation | Observation | Authorization |
|---|---|---|
| boundary | JSON → parser → runtime conversion → initialization → active dataflow | route named |
| disproof | WS and OS requests produce the same active mode | discriminating A/B defined |
| parser | WS and OS values are recorded | parsing verified |
| conversion | geometry crosses; dataflow does not | dataflow effect not authorized |
| consumer | both converted routes select compile-time WS | requested OS rejected on this route |
| positive control | direct setter selects OS | OS implementation is separately reachable |
| lifecycle | create preserves `8×4`; reinit restores `16×16` | creation and reinit separated |
| mutation | force consumer to OS; gate rejects | consumer relation is discriminating |

Safe conclusion: parsing records the request, but the examined converted initialization route drops it and selects compile-time WS; the direct setter is separately effective.

Unsafe conclusion: “OS JSON config reaches execution,” or the opposite overgeneralization, “OS is never selectable.”

### Case B: “CI random mode doubles coverage”

| Relation | Observation | Authorization |
|---|---|---|
| target recipe | `make test-random` builds and runs | first process execution established structurally |
| CI action | runner invokes the binary again | second invocation established structurally |
| vectors | fixed seeds 42, 99, 777, 888 | deterministic streams identified |
| mutation | 42→43 is rejected under rebound hash | seed census is gated |
| independence | same fixed-seed streams recur | no second independent vector set |

Safe conclusion: two process invocations repeat one deterministic vector set per fixed seed.

Unsafe conclusion: “twice as many independent random samples.”

### Case C: “the report is green”

| Relation | Observation | Authorization |
|---|---|---|
| fixture | earlier counted failure plus trailing PASS | conflicting evidence constructed |
| producer status | unavailable to parser (`-1`) | process success not known |
| parsed count | one failure retained | failure evidence present |
| parsed status | PASS | parser can produce unsafe green |

Safe conclusion: the parser can label this discriminating log PASS despite a counted failure and absent producer status.

Unsafe conclusion: any claim about a particular historical CI job without its exact producer evidence.

## 20.11 Quantitative claims import Chapter 17’s contract

Chapter 20 does not create a new metric taxonomy. If a verification result contains “cycles,” “utilization,” “TOPS,” “power,” “energy,” or another quantitative field, evidence selection must import Chapter 17’s complete contract:

```text
producer + action/event + interval + units + clock owner
+ reset boundary + formula + fidelity/calibration rung
```

A test return, counter name, or field label authorizes no physical timing conclusion on its own. A mutation-sensitive formula test can establish the exact source-defined result for a named input. It cannot turn an analytical estimate into elapsed hardware time or make two incompatible cycle domains additive.

Thus Chapter 20 can ask whether a quantitative claim has a discriminating oracle, reached producer, denominator, and status path. Chapter 17 remains authoritative for what the producer means. No producer census is reopened here, and no counter or estimate is combined into a fictional common timeline.

## 20.12 Preserving evidence: immutable does not mean correct

Reproducibility is necessary because a claim without exact inputs cannot be challenged reliably. It is insufficient because a perfectly preserved predicate can still encode the wrong relation.

The Chapter 20 post-review authority uses four trust layers:

1. `sha256-retained.txt` binds retained inputs and body evidence;
2. `bundle-sha256.txt` binds the inner manifest, its check, finalization, and normal/optimized pre-outer validations;
3. bundle and closure logs are derived checks and are not described as recursively manifest-sealed;
4. exact Git seal commit `c37c49a73180de2b435f345a2cc963c924403c22` binds the complete run tree.

The seal’s first parent is exactly input commit `e5dd99715300c78d9e08d9b1df4bec909bc03982`. Post-seal validation checks that every changed path is under the intended run directory, the committed and live member sets are identical, and every run blob matches.

### Why review precedes drafting authority

The provisional v1 run was hash-clean and green, but skeptical review found that its body pipeline was fail-open and that inventory cardinalities were not complete membership gates. It remains immutable evidence of what that runner did; it is superseded as drafting authority.

The post-review v2 seal includes the review dispositions as a hashed input and adds:

- explicit fail-fast subshell execution;
- failure-path source preservation;
- literal complete membership sets;
- same-cardinality membership mutation;
- fixed-seed mutation;
- route-separated configuration probes;
- full archive sanitizer instrumentation for the bounded probe;
- normal and optimized validation at body, pre-outer, outer, closure, and post-seal stages.

This demonstrates the difference between provenance and correctness. Hashes answer “are these the same bytes?” Review and discriminating controls answer “do these bytes test the relation the claim names?”

### Validators need controls too

The predraft validator is run under normal Python and `python -O`. A frozen-input mutation must be rejected in both modes. A disposable validator copy containing a real `assert(False)` must be rejected by the validator’s AST self-check in both modes. These controls prevent optimization-sensitive Python assertions from silently weakening release validation.

The evidence remains bounded. A post-review green seal authorizes only the ledger’s claim and limitation wording. It does not convert static-only findings into execution, supply HDL simulation, establish compiler/runtime composition, or calibrate physical behavior.

## 20.13 Verification architecture alternatives and trade-offs

There is no universally strongest practical gate. Evidence should be matched to defect class, development stage, cost, and decision risk.

| Verification architecture | Defect sensitivity and reach | Runtime / infrastructure cost | Design and maintenance cost | Best-fit regime | Unsafe use |
|---|---|---|---|---|---|
| local unit/property test | strong for named local relation and boundary values | low | fixtures and assertions | fast component development | subsystem integration certificate |
| independent finite oracle | catches arithmetic/layout defects within its domain | low to moderate | maintain a distinct equation/path | deterministic kernels with bounded values | exceptional-value or full-stack proof without domain checks |
| exceptional-value comparator | catches NaN/Inf and tolerance path defects | low | explicit policy and bit/value cases | numerical interfaces | arbitrary application-accuracy claim |
| negative lifecycle/invariant fixture | catches illegal transitions and failure-atomicity defects | moderate | state setup and teardown | queues, DMA, contexts, ownership | performance or calibration claim |
| semantic mutation | proves a gate rejects one targeted defect | moderate to high | mutation design and expected failure | claim-critical release gates | universal mutation adequacy |
| configuration A/B effect test | reaches parser-to-consumer behavior | moderate | discriminating configurations and observables | user-visible knobs | all config fields or all routes from one case |
| nonsymmetric external-boundary case | catches common orientation/value mistakes | moderate | bridge isolation and independent expected result | wrappers and bindings | full API, lifetime, HDL, or CI ownership claim |
| exact aggregate/CI inventory | prevents silent selection omissions | low execution, moderate analysis | parser maintenance as build files evolve | release coverage governance | proof that every selected recipe is fail-closed |
| fail-closed status chain | prevents suppressed failures and parser reinterpretation | moderate | wrapper/report schema discipline | CI and release delivery | semantic correctness without adequate tests |
| sanitizer-instrumented bounded run | catches selected memory/undefined behavior in reached code | high | toolchain, cleanup, false-positive control | risky C paths and lifecycle probes | whole-library dynamic/path coverage from a narrow fixture |
| immutable bundle + exact review binding | makes evidence replayable and auditable | storage and validation cost | manifests, validators, review process | chapter/release authority | semantic correctness by hash alone |
| RTL/FPGA/silicon comparison | can validate lower-level or physical claims under named conditions | highest | interfaces, calibration, lab/flow ownership | high-risk timing/energy/sign-off decisions | automatic generalization beyond workload and platform |

The alternatives are complementary rather than one ladder that every change must climb completely. A local unit test may be the best fast gate for a pure helper. A configuration feature requires route-complete A/B evidence. A release claim needs exact selection and status propagation. A physical latency claim eventually needs an appropriate external reference and Chapter 17’s producer contract.

Stronger evidence also changes architecture cost. More independent oracles duplicate logic intentionally and can drift. Mutation suites increase execution time and maintenance. Full isolation requires controlled temporary paths and cleanup. Immutable bundles consume storage and need schema governance. External simulation and hardware comparison offer stronger physical evidence but increase turnaround time and calibration burden.

The design objective is not “maximum testing.” It is the minimum evidence chain that can actually disprove the claim at the required risk level, plus enough provenance to review that decision.

## 20.14 Verification evidence and canonical authority

The sole Chapter 20 predraft authority is:

```text
experiments/runs/20260816-ch20-postreview-v2/
```

It binds source pin:

```text
e918c80b6fce833cd1fcae97730fa841c2176f25
```

input commit:

```text
e5dd99715300c78d9e08d9b1df4bec909bc03982
```

and seal commit:

```text
c37c49a73180de2b435f345a2cc963c924403c22
```

The retained source audit reports:

```text
CH20_SOURCE_AUDIT PASS pin=e918c80b6fce833cd1fcae97730fa841c2176f25 hashes=22 predicates=52 checks=75
```

The exact probe reports:

```text
ORACLE_NAN shared_accept=1 strict_accept=0 shared_pass=1 shared_fail=0
CONFIG_AB ws_parse=0 os_parse=0 ws_df=0 os_df=1 rt_rows=8 rt_cols=4 ws_active=weight_stationary os_active=weight_stationary direct_os=output_stationary
CORE_REINIT_GEOMETRY created_8x4=1 reinitialized_16x16=1 created_bytes=336 reinitialized_bytes=338
DUMP_SIZE fixture=post_reinit_16x16 reported=0 actual=338
REPLAY_NOOP arbitrary_opcode=0xFE mismatches_equal=0 mismatches_mutated=1 output_bytes=69
BOUNDS_WRAP wrapped_accept=1 ordinary_accept=0
TILE_PE_IGNORED oversized_accept=1 zero_reject=1
CH20_PROBE SUMMARY failures=0
```

The bundle also retains:

- source-hash, same-cardinality membership, and fixed-seed mutations;
- safe and forbidden Make dry-run expansions without executing fixed-host-path recipes;
- byte-identical `-O0` and `-O2` probe output;
- a fully ASan/UBSan-instrumented archive plus probe, with leak checking excluded for the global singleton lacking a teardown route;
- debug `25/25` versus meaningful-size mutation `23/25`;
- error `9/9` versus reached-injection requirement `8/9`;
- golden `11/11` versus local-equation mutation `2/11`;
- report false-green and nonsymmetric binding discriminators;
- normal and optimized frozen-input and validator-AST mutation rejection;
- inner and outer manifests, finalization, closure validation, and exact post-seal Git binding.

To recheck the exact seal from a clean book tree:

```bash
cd /home/zxy/Workplace/books/tusim-book
CH20_RUN_ID=20260816-ch20-postreview-v2 \
  python3 experiments/ch20_predraft_validate.py \
  --sealed-at c37c49a73180de2b435f345a2cc963c924403c22

CH20_RUN_ID=20260816-ch20-postreview-v2 \
  python3 -O experiments/ch20_predraft_validate.py \
  --sealed-at c37c49a73180de2b435f345a2cc963c924403c22
```

Both are expected to print the exact `CH20_POSTSEAL_VALIDATION PASS` line recorded in `notes/chapter-20-postseal-validation.md`. The pre-review v1 run remains immutable but superseded for drafting.

## 20.15 Common failure modes

1. **Green means subsystem-correct.** A green result supports a named relation, not a subsystem-wide certificate.
2. **Source presence means execution.** Source, prerequisite, recipe, target, aggregate, CI, process, and report are distinct relations.
3. **Aggregate pass means all tests passed.** `make test` has a 31-target denominator, not a 64-source denominator.
4. **Stable count means stable coverage.** A same-cardinality member swap can change the tested set.
5. **Golden means independent.** Equations, helpers, conversions, comparator, and value domain can remain coupled.
6. **Finite pass covers NaN.** Both the shared comparator and local golden comparator are NaN-blind.
7. **More invocations mean more samples.** Fixed seeds can repeat identical vector streams.
8. **Parsed means effective.** The examined route parses dataflow and drops it during runtime conversion.
9. **Creation config survives reinit.** `tu_core_init()` restores default `16×16` geometry in the bounded case.
10. **Nonnegative unsigned check validates size.** `n >= 0` is vacuous for unsigned `n`.
11. **Checksum tautology validates checksum.** `cs != 0 || cs == 0` proves only that the call returned.
12. **Requested failure was tested.** A disabled, unmatched injection cannot authorize reached-failure behavior.
13. **Helper tests imply automatic enforcement.** The assertion helpers have no direct external non-test callers at the pin.
14. **Round-trip means replay.** Serialization and checksum comparison do not issue instructions.
15. **DPI name means HDL simulation.** The focused DPI test is native C-to-C wrapper evidence.
16. **Identity GEMM proves orientation.** Symmetric identity values are insensitive to many transposition defects.
17. **One Python case proves full bindings.** The nonsymmetric `2×2` case is bounded; stubs, unused `config_path`, and absent Make/CI ownership remain.
18. **Trailing PASS means producer success.** The parser can report PASS with one counted failure and absent exit status.
19. **Hash-clean means semantically correct.** Hashes preserve bytes, including mistaken predicates.
20. **Pre-review seal is final.** Review can expose missing relations and require a new immutable authority.
21. **Verification adjacency means system composition.** No ONNX/compiler/runtime composition is authorized.
22. **A cycle field means physical time.** Chapter 17’s producer, interval, units, reset, clock, formula, and fidelity contract still applies.

## 20.16 Fidelity box

**Verified at the pinned revision**

- exact 64-source, 59 source-to-prerequisite, 31 aggregate, four quick, four CI-quick, 14 CI-full, and five relation-omission inventories;
- static status-suppression and fixed-host-path mechanics for the hash-bound pinned recipes;
- report-parser behavior for the synthetic fail-then-pass fixture;
- finite-domain local golden-equation mutation sensitivity;
- shared and local comparator NaN-blindness;
- exact configuration A/B, direct-setter, creation, and reinitialization observations;
- exact debug return/stream-position, replay/checksum, bounds-wrap, and tile-dimension fixtures;
- reached-injection mutation behavior;
- native wrapper limitations established by source and focused-test structure;
- one exact nonsymmetric Python/C `2×2` value/orientation case;
- post-review fail-fast, mutation, manifest, normal/optimized validator, and exact-seal controls.

**Qualified**

- local scalar GEMM is equation-distinct for finite normal inputs, not an exceptional-value or arbitrary-binary16 oracle;
- random tests execute deterministic fixed-seed vectors and share repository oracle components;
- assertion helpers are executable directly but not established as automatic internal enforcement;
- native DPI tests are lifecycle/data-path smokes, not HDL or orientation evidence;
- Python binding evidence covers one convenience route and bounded input only;
- byte counts are pin/toolchain fixture observations, not API constants;
- static recipe findings establish mechanics, not historical hosted-CI outcomes.

**Blocked for direct execution in this evidence set**

- pinned recipes using fixed host-global `/tmp` or report paths, until outputs are redirected into run-owned storage;
- HDL simulator boundary evidence;
- physical timing, power, energy, or calibration beyond Chapter 17’s existing authorities.

**Rejected**

- aggregate green as complete repository verification;
- checksum tautology as checksum correctness;
- recorded trace round-trip as behavioral instruction replay;
- identity GEMM alone as orientation proof;
- source presence or one convenience function as production-grade/full-API/CI-owned binding evidence;
- invocation count as independent random-sample count;
- any ONNX/compiler/scheduler/allocator/queue/runtime composition at this pin.

**Governance boundary**

- Chapter 17 owns metric producer, interval, units, reset, clock, formula, and fidelity;
- Chapter 21 owns trustworthy sweep construction and sensitivity methodology;
- Chapter 23 owns extension procedure;
- Chapter 19 remains closed.

## 20.17 Sealed limitation register

The exposition above explains and applies the ledger boundaries. The following register preserves the binding `Limitation wording` for every sealed claim verbatim. It is an audit surface, not a second chapter outline: if an explanatory sentence appears broader than its mapped row, this register controls the interpretation.

| Claim | Binding limitation wording |
|---|---|
| C20.1 | a green result is evidence for a named relation, not a subsystem-wide certificate. |
| C20.2 | the five omissions are omissions from the source-prerequisite relation; `test_asm.c` is nevertheless compiled inside the `test-asm` recipe. |
| C20.3 | aggregate success is not complete repository verification and says nothing about source-present tests outside its dependency relation. |
| C20.4 | this is selection evidence, not a live GitHub Actions execution or environment-conformance claim. |
| C20.5 | static inspection establishes fail-open status mechanics; fixed host-global `/tmp` recipes remain unexecuted unless redirected into run-owned storage. |
| C20.6 | this demonstrates parser semantics for the discriminating fixture, not the status of any particular historical CI job. |
| C20.7 | hash stability proves input identity and predicate reproducibility, not semantic correctness of a mistaken predicate. |
| C20.8 | the local scalar GEMM equation is structurally distinct for finite normal inputs, but its locally duplicated maximum-error comparator is also NaN-blind. Independent equation does not establish an independent exceptional-value oracle, arbitrary binary16, orientation, or external-framework agreement. |
| C20.9 | this disproves exceptional-value coverage through this comparator; it does not invalidate finite-domain passes that independently exclude non-finite values. |
| C20.10 | these are two distinct routes. Parsing is not effect, converted initialization is not direct setter behavior, and instance creation is not `tu_core_init()` preservation. |
| C20.11 | `actual=338` is the text/counters dump of the default 16×16 core after `tu_core_init()`, not the earlier 8×4 created core. Binary dump size and full-report content have separate stronger tests. |
| C20.12 | the initial-checksum case proves only that the call returned; it cannot authorize a specific CRC value, completeness, collision resistance, or cross-version stability. |
| C20.13 | serialization and checksum comparison are executable; deterministic instruction re-execution and behavioral replay are rejected. |
| C20.14 | direct helper behavior is executable; automatic internal enforcement, overflow-safe bounds, and PE-fit validation are not established. |
| C20.15 | other error macros and direct reporting tests remain meaningful; the injection case does not authorize one-shot injected-failure behavior. |
| C20.16 | one normal-value 2×2 case does not establish full API coverage, config-file use, error/lifetime semantics, exceptional values, CI ownership, or an ONNX/compiler/runtime composition. |
| C20.17 | `tests/test_dpi.c` is native C-to-C wrapper evidence; no HDL simulator boundary is exercised. Its identity GEMM is orientation-insensitive, and its async and LayerNorm cases do not verify far-boundary numerical output. Identity tests remain lifecycle/data-path smokes, not orientation discriminators. |
| C20.18 | source presence and one working convenience function do not authorize production-grade/full-API/CI-owned binding claims. |
| C20.19 | Chapter 20 selects evidence for a quantitative claim but does not redefine, combine, or calibrate metric producers. |
| C20.20 | a pre-review green seal is provisional; it cannot authorize drafting after review changes evidence or claim wording. |
| C20.21 | do not execute those pinned recipes merely to demonstrate unsafe isolation; redirect every output into run-owned storage before any future live test. |
| C20.22 | adjacent executable surfaces remain separate until a repository-contained nontrivial bridge links, runs, propagates failures, and verifies far-boundary output. |
| C20.23 | two process executions are one deterministic vector set per fixed seed; invocation count must not be reported as independent sample count. |

## Development questions

1. Should every test target publish a machine-readable claim ID, source set, execution command, and explicit denominator?
2. Should Make and CI derive their target lists from one declarative inventory, or should independent lists be retained as a cross-check?
3. How should the report schema preserve producer exit status and reject contradictions between status text and counted failures?
4. Which functional paths need an oracle independent of repository conversion helpers and tolerance code?
5. Should comparison helpers reject all non-finite mismatches by default and require explicit exceptional-value policy?
6. How should deterministic random tests report unique seeds, vectors, and repeated process invocations?
7. Can configuration tests be generated from a declaration→parser→conversion→consumer map without turning Chapter 23’s extension procedure into hidden test logic?
8. Which lifecycle APIs need failure-atomicity and invariant checks after every rejected operation?
9. What exact state schema would be necessary before debug trace replay could claim behavioral re-execution?
10. Which native wrapper cases need nonsymmetric values and far-boundary output checks before an HDL testbench is introduced?
11. Should binding ownership become an explicit Make/CI target with error, lifetime, configuration, and exceptional-value cases?
12. How can fixed host-global temporary paths be replaced by run-owned paths without changing the pinned-edition evidence retroactively?
13. Which semantic mutations should be mandatory for release-critical claims, and how should mutation drift be reviewed?
14. Can evidence manifests carry claim-to-file and claim-to-control relations rather than only hashes?
15. What external reference would be appropriate for any future RTL, FPGA, or silicon validation claim, and which Chapter 17 producer would it compare?

## Summary

Verification evidence is claim-relative. A green result authorizes only the architectural relation it can discriminate through the route actually exercised, under an adequate oracle, meaningful controls, intact status propagation, an explicit denominator, and immutable reviewable provenance.

Tusim’s pinned verification surfaces make the distinction concrete. Sixty-four C test sources do not become one denominator: 59 are named by rule prerequisites, `make test` selects 31 targets, and CI selects four quick or 14 full targets. Counts alone are insufficient; a same-cardinality membership swap must be rejected. A local scalar golden equation catches a finite arithmetic mutation, yet its comparator remains NaN-blind. Two fixed-seed random invocations repeat streams rather than add independent samples.

Configuration evidence must reach effect. The examined JSON route parses output-stationary, drops it during runtime conversion, and initializes as compile-time weight-stationary, while the direct setter remains separately effective. Core creation preserves `8×4`; `tu_core_init()` restores default `16×16`. These route and lifecycle distinctions cannot be collapsed.

Negative controls expose green gates that cannot reject their advertised failure. Unsigned size assertions are vacuous; a checksum condition is tautological; the requested error injection is not reached; bounds can wrap; tile checks ignore PE dimensions. Recorded trace round-trip and checksum comparison are executable, but behavioral replay is not. Native DPI calls are C-to-C evidence, and one nonsymmetric Python/C case proves only its bounded value/orientation relation.

Regression delivery is itself an architecture. Target selection, process status, wrappers, and reports must preserve failure. The pinned report parser can retain one failure and still label a trailing-PASS fixture green without producer exit status. The Chapter 20 runner therefore verifies its own fail-fast and failure-cleanup behavior.

Finally, immutable provenance is necessary but insufficient. The provisional seal preserved a fail-open runner exactly. Skeptical review forced a new post-review seal with relation-complete membership gates, semantic mutations, failure-path preservation, normal/optimized validation, and exact Git binding. Hashes establish identity; discriminating evidence and review establish authority.

No result in this chapter composes an ONNX/compiler/runtime path. Chapter 19 remains closed. Chapter 17 retains quantitative-producer semantics, Chapter 21 sweep construction, and Chapter 23 extension procedure.

## Review questions

1. Why is a green result not intrinsically strong or weak?
2. Which relations separate a source file from a green CI report?
3. Why can `make test` not authorize all 64 C test sources?
4. What does the same-cardinality aggregate mutation prove that a count check does not?
5. In what sense is the local golden GEMM independent, and in what sense is it not?
6. Why does a repeated fixed-seed process invocation not add an independent sample set?
7. What route distinctions are required to interpret the WS/OS configuration case?
8. Why do `25/25` debug tests not establish that text/JSON dump returns a meaningful size?
9. What does the replay fixture execute, and what does it not execute?
10. Why is identity GEMM weak orientation evidence?
11. What exactly does the nonsymmetric Python/C case authorize?
12. How can a report contain a failure and still become green?
13. Why must an audit runner have a negative control for its own failure path?
14. What does an immutable manifest prove, and what does it not prove?
15. Which chapter owns the interpretation of a field labeled in cycles, and what must be named?

### Review-question answer key

1. Strength is relative to a claim boundary and threatened defect; the same producer can support one narrow relation and miss a stronger one.
2. Source presence, Make prerequisite ownership, recipe compilation, target existence, aggregate selection, CI selection, process execution, status propagation, and report interpretation.
3. The aggregate selects exactly 31 prerequisite targets; sources outside that relation are not covered, and selected recipes still have individual status semantics.
4. It proves literal set membership is gated rather than merely the number of members.
5. Its scalar equation is distinct from cmodel execution for tested finite normal inputs; its maximum-error comparator duplicates the NaN-blind pattern and does not establish exceptional-value independence.
6. Seeds 42, 99, 777, and 888 recreate the same deterministic vector streams in both processes.
7. Parsing, runtime conversion, converted initialization, direct setter behavior, creation geometry, and reinitialization must remain separate.
8. Two checks use unsigned `n >= 0`; replacing them with `n > 0` changes the result to `23/25` because the producer writes bytes but returns zero.
9. It records an in-memory trace entry and invokes checksum-comparison replay; it does not serialize that fixture or issue the recorded arbitrary instruction. Serialization round-trip is separate focused-suite evidence.
10. An identity matrix is invariant under many transposition or orientation errors.
11. One finite normal-value `2×2` ctypes route has exact independently recomputed value and orientation; broader API, config, lifetime, exceptional, performance, power, CI, and composition claims remain unsupported.
12. The parser can let trailing PASS text determine status, retain `failed=1`, and lack producer exit status.
13. Otherwise an early failed gate may be overwritten by later success, and cleanup/source preservation may be proven only on the passing path.
14. It proves byte identity and reproducibility of the bound artifacts, not semantic correctness of their predicates or claims.
15. Chapter 17; producer, event/action, interval, units, clock owner, reset boundary, formula, and fidelity/calibration rung must be named.

## Design exercises

1. **Claim contract.** Choose one focused Tusim test and write its claim boundary, one disproof condition, oracle, route, controls, denominator, status path, and safe/unsafe conclusions.
2. **Inventory schema.** Design a machine-readable relation table that distinguishes source, prerequisite, recipe, target, aggregate, CI, execution, and report ownership.
3. **Exceptional-value oracle.** Specify a comparator policy for NaN, infinities, signed zero, finite tolerance, and raw-bit equivalence. Provide one mutation per policy branch.
4. **Configuration effect.** Design an A/B test for a configuration field that has two possible consumers. State how the fixture proves which consumer ran.
5. **Lifecycle invariant.** For a queue or context API, define one global invariant and test it after success, invalid input, full capacity, and repeated reset.
6. **Replay contract.** Define the minimum state, instruction, ordering, and output relations needed to upgrade checksum comparison into behavioral replay.
7. **Boundary discriminator.** Replace an identity external-boundary test with a nonsymmetric case that detects transpose, row/column swap, and stale-output defects.
8. **Status pipeline.** Design a report schema that resolves nonzero exit, missing log, counted failure, trailing PASS text, timeout, and parser exception without unsafe green states.
9. **Semantic aggregate mutation.** Preserve aggregate cardinality while changing one claim-critical member. Explain why hash rebinding is required to reach the membership predicate.
10. **Evidence bundle.** Specify inner manifest, outer binding, validator controls, exact-review marker, and post-seal checks for one release-critical claim.
11. **Cost trade-off.** Compare local unit, semantic mutation, sanitizer, full integration, and RTL comparison for a bounds-check claim. Name defect coverage, runtime, infrastructure, and maintenance costs.
12. **Quantitative gate.** Take one cycle-like field and write the Chapter 17 producer contract plus the Chapter 20 evidence needed to authorize one bounded equation claim.

### Exercise answer sketches

1. Keep every field claim-specific; a source path or pass count is not a substitute for the route or disproof condition.
2. Use explicit many-to-many edges and record whether each edge is declared, compiled, selected, executed, or interpreted; do not infer one relation from another.
3. Reject non-finite mismatches explicitly, compare matched infinities by sign, state signed-zero policy, define finite absolute/relative tolerance, and use raw bits only where the numerical contract requires them.
4. Select inputs whose consumers produce different observable outputs, gate both branches, and mutate the consumer selection while preserving parsing.
5. Examples include exactly one active owner, bounded occupancy, unchanged ownership on rejection, and reset restoring a named state; verify after every call, not only at suite end.
6. Bind complete initial state, issue each recorded instruction through the real consumer, define visibility/completion, compare far-boundary state, and reject corruption, truncation, unsupported opcodes, and checksum-only no-ops.
7. Use unequal nonsymmetric operands and verify the full output independently at the far boundary; add a one-value mutation and a stale-buffer negative.
8. Treat any nonzero, timeout, missing required output, counted failure, or parser error as non-pass; preserve producer and parser statuses separately and reject contradictions.
9. Rebinding bypasses the identity gate so the semantic set gate itself is exercised; otherwise rejection proves only hash drift.
10. Bind exact inputs and body evidence, bind the manifest and validation layers, mutation-test the validator under normal and optimized execution, review an exact commit, and verify the sealing commit’s parent, paths, member set, and blobs.
11. Unit and mutation controls are cheap and targeted; sanitizers catch reached C memory/UB defects; integration reaches more contracts; RTL comparison addresses lower-level implementation correspondence at much higher cost. None replaces a mismatched claim boundary.
12. Name producer, action, interval, units, clock, reset, formula, and fidelity first; then prove route, input, expected equation, semantic mutation, status, denominator, and provenance without composing incompatible producers.

## Primary references

- [SHA14](../../references/foundations.md#sha14-aladdin) Shao et al., “Aladdin: A Pre-RTL, Power-Performance Accelerator Simulator Enabling Large Design Space Exploration of Customized Architectures,” 2014, [DOI 10.1109/ISCA.2014.6853196](https://doi.org/10.1109/ISCA.2014.6853196). The work demonstrates that a pre-RTL model can be validated against named references; its reported validation does not transfer automatically to Tusim.
- [SAM18](../../references/foundations.md#sam18-scale-sim) Samajdar et al., “SCALE-Sim: Systolic CNN Accelerator Simulator,” 2018, [arXiv:1811.02883v2](https://arxiv.org/abs/1811.02883v2). Its configurable simulator evidence provides a comparison point for explicit workload/model scope, not proof of Tusim correctness or cycle equivalence.
- [PAR19](../../references/foundations.md#par19-timeloop) Parashar et al., “Timeloop: A Systematic Approach to DNN Accelerator Evaluation,” 2019, [DOI 10.1109/ISPASS.2019.00042](https://doi.org/10.1109/ISPASS.2019.00042). Separating workload, architecture, mapping, and constraints motivates relation-explicit evidence; Timeloop results do not validate Tusim.
- [GEN21](../../references/foundations.md#gen21-gemmini) Genc et al., “Gemmini: Enabling Systematic Deep-Learning Architecture Evaluation via Full-Stack Integration,” 2021, [DOI 10.1109/DAC18074.2021.9586216](https://doi.org/10.1109/DAC18074.2021.9586216). Its full-stack evaluation is a useful contrast: connected software, RTL, and system evidence must be demonstrated, not inferred from adjacent Tusim surfaces.
- [CHE18](../../references/foundations.md#che18-tvm) Chen et al., “TVM: An Automated End-to-End Optimizing Compiler for Deep Learning,” 2018. The end-to-end system is cited only as a contrast for explicit connected contracts; it does not authorize an ONNX/compiler/runtime composition in Tusim.

Full verified metadata and conservative safe-use scopes are maintained in [`../../references/foundations.md`](../../references/foundations.md).
