# Chapter 20 — Predraft Audit Report

- Date: 2026-08-16
- Status: **canonical pre-review v1 sealed at book commit `ed67f181dd6b51f733907408689ea1e7c2e72fc1`; skeptical review blocked v1; post-review v2 amendments prepared but unsealed**
- Tusim pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Ledger: [`chapter-20-source-and-claim-ledger.md`](chapter-20-source-and-claim-ledger.md)
- Review dispositions: [`chapter-20-skeptical-predraft-review-dispositions.md`](chapter-20-skeptical-predraft-review-dispositions.md)

## Audit question

For each green unit, aggregate, CI, report, debug/replay, DPI, or Python result, what exact claim boundary was reached, which targeted failure could it discriminate, where did process status travel, and which stronger interpretation remains unauthorized?

## Evidence architecture

The post-review audit is relation-based rather than a test-directory catalogue:

1. hash 22 source files and evaluate 52 predicates, including literal complete source→target, aggregate, quick, CI, omission, config-consumer, random-seed, DPI, binding-owner, fallback, tile, and stub relations;
2. challenge a source hash, same-cardinality aggregate membership, and fixed-seed census independently;
3. retain safe and forbidden `make -n` expansions while never executing host-global fixed-`/tmp` recipes;
4. build only a static archive in the main disposable extraction, link probes explicitly to it, and reject dynamic cmodel resolution;
5. run an exact-value C probe at `-O0` and `-O2`, then rebuild the entire archive plus probe with ASan/UBSan;
6. pair baseline green suites with semantic mutations: configuration consumer, debug byte count, reached failure injection, and golden equation;
7. challenge report status using a counted failure plus trailing PASS;
8. challenge binding orientation using nonsymmetric matrices and an independently recomputed result;
9. force a fail-fast scaffold error and require nonzero status, no survivor, and exact clean source state afterward;
10. mutate a frozen input and the validator AST, validate under normal and optimized Python, and retain inner/outer trust layers.

The binding shared object is linked directly and exclusively with `--whole-archive` from the freshly built disposable static archive; a link map and archive/shared hashes are retained. No `-L. -ltucmodel` selection can pick up a stale host library.

## Exact post-review discriminators

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

The byte counts are pin/toolchain observations, not API constants. The 336-byte dump belongs to the created 8×4 core; 338 belongs to the default 16×16 core after `tu_core_init()`. The text producer writes while returning zero. Replay compares checksums without issuing the instruction. Bounds wrap is unsigned modular arithmetic. The oversized tile is accepted because PE dimensions are ignored.

## Baseline/mutation matrix

| Surface | Positive control | Semantic mutation | Authorized conclusion |
|---|---|---|---|
| fail-fast runner | successful post-review body | deliberate early `false` in identical subshell scaffold | nonzero, no survivor, source checked after failure |
| source identity | 22 exact hashes | append to `tu_debug.c` | source drift is rejected |
| inventory semantics | literal 31-member aggregate | replace `test-dpi` with omitted `test-debug`, preserve count and rebind Make hash | set semantics, not cardinality, gate the claim |
| random census | exact seeds 42/99/777/888 | 42→43 with rebound file hash | deterministic vector census is semantically gated |
| configuration | WS/OS A/B, direct OS setter, 8×4→16×16 lifecycle | force initialization consumer to OS | parse/conversion/consumer distinctions are discriminating |
| shared comparator | finite expected vs NaN actual | independent finite-checking comparator | shared helper is unsafe for exceptional-value authorization |
| golden quick | 11/11 | local scalar reference `sum + 1` → 2/11, nonzero | finite tested equations discriminate the mutation; comparator remains NaN-blind |
| debug focused | 25/25 | replace two vacuous `n >= 0` checks by `n > 0` → 23/25, nonzero | baseline count does not authorize text/JSON byte-return correctness |
| error focused | 9/9 | require requested injection to occur → 8/9, nonzero | injection case is non-discriminating despite green suite |
| report parser | ordinary parser import | earlier counted FAIL + trailing PASS | report status can diverge from failures and lacks exit status |
| Python binding | nonsymmetric 2×2 exact result | change one independently expected value | one cross-language orientation/value case is mutation-sensitive |
| frozen input | committed/frozen equality | alter frozen ledger | validator rejects provenance drift under normal and optimized Python |
| validator AST | no `assert` nodes | append real `assert(False)` | normal and optimized validators reject optimization-sensitive assertions |

## Static-only findings

- `make test` has exactly 31 prerequisite targets; source presence, prerequisite ownership, aggregate selection, CI selection, process execution, and report status remain distinct relations.
- CI random mode executes one fixed-seed vector set twice: first inside `make test-random`, then as `./test-random`.
- CI compile fallback can suppress the transformed-target failure without recording failure or setting `OVERALL_EXIT`; this is static fail-open evidence, not a successful binary-execution claim.
- `tests/test_dpi.c` is native C-to-C wrapper evidence, not an HDL simulator boundary. Identity GEMM is orientation-insensitive; async and LayerNorm do not check far-boundary output.
- Python performance and power report methods are separate stubs; `config_path` is not loaded; Make/CI/workflow contain none of the binding owner identifiers.

## Safety boundary

- The live Tusim checkout is used only for state checks and `git archive` and remains detached, clean, read-only, and exactly pinned.
- Builds, tests, mutations, private shared bridge, and sanitizers occur only in disposable archive extractions.
- The deliberate failure control checks source state after failure; the main trap stays active through manifest and closure validation.
- `test-asm`, `test-full`, `test-compiler`, `clean`, and `tools/ci_runner.sh` are not executed.
- No Chapter 20 manuscript is created.
- Chapter 17 retains metrics, Chapter 21 sweep construction, Chapter 23 extension procedure, and Chapter 19 remains closed. No ONNX/compiler/runtime composition is inferred.

## Trust and seal policy

The trust hierarchy is explicit:

1. `sha256-retained.txt` binds retained inputs and evidence;
2. `bundle-sha256.txt` is the outer root binding the inner manifest, its check, finalization, and normal/optimized pre-outer validations;
3. bundle and normal/optimized closure logs are derived checks and are not described as recursively manifest-sealed;
4. the exact Git seal commit binds the complete run tree.

After the post-review run is committed as the direct child of its recorded input commit, `--sealed-at <OID>` must verify commit type, first parent, run-only changed paths, exact member set, and every run blob. Only that post-seal result can close the evidence gate; it still does not draft Chapter 20.
