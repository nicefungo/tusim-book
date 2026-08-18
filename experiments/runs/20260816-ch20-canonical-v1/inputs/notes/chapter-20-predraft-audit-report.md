# Chapter 20 — Predraft Audit Report

- Date: 2026-08-16
- Status: **audit implementation prepared; canonical pre-review seal pending**
- Tusim pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Ledger: [`chapter-20-source-and-claim-ledger.md`](chapter-20-source-and-claim-ledger.md)
- Framing: [`chapter-20-framing-and-evidence-plan.md`](chapter-20-framing-and-evidence-plan.md)

## Audit question

For each green unit, aggregate, CI, report, debug/replay, DPI, or Python result, what exact claim boundary was reached, which targeted failure could it discriminate, where did process status travel, and which stronger interpretation remains unauthorized?

## Evidence architecture

The audit is intentionally relation-based rather than a test-directory catalogue:

1. hash and predicate the source, Make, workflow, CI, report, oracle, config, debug/replay, DPI, and Python surfaces;
2. reconstruct source→rule→aggregate→CI membership without conflating prerequisites with recipe compilation or execution;
3. build only a static archive in a disposable exact-pin extraction;
4. run an exact-value C probe at `-O0`, `-O2`, and ASan/UBSan;
5. pair baseline green suites with semantic mutations: debug byte count, reached failure injection, and golden equation;
6. challenge report status using a counted failure plus trailing PASS;
7. challenge binding orientation using nonsymmetric matrices and an independently recomputed result;
8. retain source/input mutations, inner/outer manifests, optimization-safe validation, and unconditional source-state checks.

Fixed host-global `/tmp` Make/CI paths remain static-only. The binding shared object is linked directly and exclusively from the freshly built disposable static archive; it is not selected through `-L. -ltucmodel` and cannot pick up a stale host library.

## Exact planned findings

The probe is expected to establish these discriminators:

```text
ORACLE_NAN shared_accept=1 strict_accept=0 shared_pass=1 shared_fail=0
CONFIG_EFFECT parse_rc=0 parsed_df=1 rt_rows=8 rt_cols=4 active=weight_stationary
DUMP_SIZE reported=0 actual=338
REPLAY_NOOP arbitrary_opcode=0xFE mismatches_equal=0 mismatches_mutated=1 output_bytes=69
BOUNDS_WRAP wrapped_accept=1 ordinary_accept=0
CH20_PROBE SUMMARY failures=0
```

The exact byte counts are pin/toolchain observations, not general API constants. `DUMP_SIZE` demonstrates that the text producer writes while returning zero. `REPLAY_NOOP` demonstrates checksum checking without instruction issue. The bounds fixture demonstrates unsigned wrap in a direct helper, not a whole-system exploit or runtime reachability claim.

## Baseline/mutation matrix

| Surface | Positive control | Semantic mutation | Authorized conclusion |
|---|---|---|---|
| source audit | 19 hashes, 37 predicates, 57 checks | mutate hashed `tu_debug.c` | source drift is rejected; predicate semantics still require review |
| shared comparator | finite expected vs NaN actual | independent finite-checking comparator | repository helper is unsafe for exceptional-value authorization |
| golden quick | 11/11 | local scalar reference `sum + 1` → 2/11, nonzero | tested equations discriminate the mutation; bounded domain only |
| debug focused | 25/25 | replace two vacuous `n >= 0` checks by `n > 0` → 23/25, nonzero | baseline count does not authorize text/JSON byte-return correctness |
| error focused | 9/9 | require requested injection to occur → 8/9, nonzero | injection case is non-discriminating despite a green suite |
| report parser | ordinary parser import | earlier counted FAIL + trailing PASS | report status can diverge from counted failures and lacks exit status |
| Python binding | nonsymmetric 2×2 exact result | change one independent expected value | one cross-language value/orientation case is executable and mutation-sensitive |
| validator | normal and `python -O` body validation | append real `assert(False)` | validator source assertions are rejected in both modes |

## Safety boundary

- The live Tusim checkout is used only for state checks, hashes, and `git archive`.
- Builds, tests, mutations, shared binding bridge, and sanitizer execution occur only under a disposable run-owned tree.
- Source state is checked after both success and failure through an unconditional trap.
- No `make clean`, `test-asm`, `test-full`, compiler target, or CI runner is executed.
- No Chapter 20 manuscript is created.
- No Chapter 17 metric taxonomy, Chapter 21 sweep method, Chapter 23 extension procedure, Chapter 19 transform semantics, or ONNX/compiler/runtime composition is imported as Chapter 20 evidence.

## Interpretation rule

A green producer is safe only when every relation needed by the claim is itself gated. A source file can exist without a target; a target can exist outside an aggregate; CI can select a subset; a shell can suppress status; a parser can reinterpret text; an oracle can share the defect or ignore NaN; a replay file can round-trip without replaying behavior; and an external wrapper can pass a symmetric smoke while hiding orientation. The safe conclusion is always the strongest statement that survives all of those challenges—not the broadest label printed by the repository.

## Seal policy

The first successful canonical run is **pre-review and provisional**. Skeptical review must independently inspect pinned source and recompute the discriminators rather than trusting the transcript. Any accepted finding changes a claim-bearing input and therefore requires a new immutable run ID. Earlier runs remain retained. Drafting is authorized only by the final post-review seal and its reconciled dispositions.
