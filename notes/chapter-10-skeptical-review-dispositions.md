# Chapter 10 Skeptical-Review Dispositions

- **First review:** 2026-07-27, three independent read-only reviewers
- **First verdict:** blocked
- **Baseline seal commit:** `ce5ed2d` (`book: seal Chapter 10 pre-draft evidence`)
- **Revised canonical run:** `experiments/runs/ch10-dma-contracts/20260727T223000Z-hashguard/`
- **Draft status:** blocked pending independent re-review

## Architecture/methodology findings

| Finding | First severity | Disposition | Revised evidence |
|---|---|---|---|
| Chain and queue linkage are not composable | critical | accepted; elevated to first-class unsafe contract | structural probes for chain-then-head and submit-while-active; C10.15–C10.16; state diagram in audit |
| Ownership is contradictory; destroy can double-free aliases | critical | accepted; unsafe path kept static | source-audit predicates; ownership matrix; C10.17 |
| Lifecycle terms were ambiguous | high | accepted | exact operational predicates; “selected” replaces sub-tick “issued”; direct-host-observation scope |
| Timing domains were conflated | high | accepted | service formula, wait/occupancy/sum separation; boundary sweep; resource A/B |
| Byte taxonomy and span were incomplete | high | accepted | 2D/3D equations; canaries; duplicate scatter; multicast source/fanout |
| Queue/counter denominators differed | high | accepted | counter-unit table; ratios prohibited for chains |
| Multi-objective regimes were only a list | medium | accepted | decisions narrowed to representability, lifetime, span safety, head capacity, synchronization, verification |
| `AUDIT_PASS` implied correctness | medium | accepted | renamed `AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS`; focused families reported separately |

## Repository/reproducibility findings

| Finding | First severity | Disposition | Revised evidence |
|---|---|---|---|
| Static reachability audit only printed observations | high | accepted | `ch10_source_audit.py`: 33 exact hashes + 32 structural predicates; exact non-test call-site sets |
| Probe/runner unpinned | high | accepted | baseline bundle committed at `ce5ed2d`; revised run records its committed execution-input HEAD and is committed before final review |
| Config-effect experiment absent | high | accepted | non-default config versus direct-init A/B probe |
| Existing harness fail-closed claim unsupported | high | accepted | existing harnesses reclassified as observations; only source audit/custom probes gate snapshot result |
| Runner cleanup/collision weakness | medium | accepted | provenance before durable run; PID/time exclusive directory; EXIT cleanup trap |
| Pipeline skip only textual | medium | accepted | exact hash and structural predicate enforce request/array/initializer mismatch |
| Ownership language too broad | medium | accepted | rejection/success/retirement/destroy outcomes separated |

## Editorial/evidence findings

| Finding | First severity | Disposition | Revised evidence |
|---|---|---|---|
| Contradictory gate status and all claims `planned` | major | accepted | claims individually `verified`, `qualified`, `rejected`, or `blocked`; status consistently pending re-review |
| Pinned source audit observational | major | accepted | fail-closed 65-check audit |
| Before/after provenance incomplete | major | accepted | book status/remotes and Tusim ordinary/ignored inventories recorded before/after |
| Conclusions exceeded probes | major | accepted | timing, geometry, borrowed state, bandwidth, config, and structural probes added; remaining claims narrowed |
| `completed` and payload overgeneralized | major | accepted | path-specific lifecycle and transfer-specific byte taxonomy |
| Title insufficiently authoritative | major | accepted | ranked four candidates; selected “DMA Descriptor Contracts and Tick-Driven Execution” |
| Formula context incomplete | moderate | accepted | constants, producer, units, formulas, and uncalibrated label co-located |
| Checksum manifest not self-verifying | moderate | accepted | all retained paths verify with `sha256sum -c`; deleted tar digest labeled recorded only |
| Evidence labels drifted | moderate | accepted | style-guide labels used verbatim |
| Aggregate result mislabeled | moderate | accepted | heterogeneous families separated; known failure and skip visible |
| AMD metadata incompletely verified | moderate | accepted | removed from the claim-bearing source map and foundations; no Chapter 10 claim depends on it |
| Prerequisite graph/reader decision weak | minor | accepted | prerequisite graph added; reader decision narrowed to caller-managed ordering |

## Second re-review findings

The first revised bundle changed while reviewers were reading it. Those verdicts remain blocked and are treated as findings, not approval. The final run name is fixed before execution so the next review can inspect an immutable bundle.

| Finding | Severity | Disposition in final bundle |
|---|---|---|
| Runner verified an older hard-coded run and transcript hash was post-hoc | high | runner now performs two-phase transcript finalization and verifies the exact run it just created; report has one-command reproduction |
| Upstream `make clean` can remove global `/tmp` files | high | runner does not invoke it; only archived `*.o`, `*.a`, and `*.so` paths are removed beneath the disposable extraction |
| Book provenance was report-only | medium | runner enforces unchanged HEAD, branch, remotes, input hashes, and status outside the new run directory |
| Config predicates named non-authoritative fields | medium | exact `tu_config_t` names enforced; probe parses six non-default JSON DMA fields before demonstrating conversion/init severance |
| Error lifecycle and outcome-blind channel completion omitted | high | controlled safe bounds-error probes cover synchronous, tick-driven, and flush paths; C10.11/C10.33 and report distinguish failed executor return from success |
| Zero-domain equations and `n` definition incomplete | medium | variables defined; zero-column and empty-index guards added; `uint32_t` overflow assumption explicit |
| 530-cycle producer/formula missing | high | complete bank-word budget and stall-penalty reconstruction added with units, producer, omissions, and calibration status |
| Fidelity labels invented | medium | only style-guide labels retained; non-integration and absent calibration are prose qualifications |
| Prerequisite chapters misidentified | high | graph corrected to Chapters 4 configuration, 5 API/ownership/lifecycle, 6 MMA/tiling, and 9 storage semantics |
| AMD date key unsupported | medium | AMD entry removed; no Chapter 10 claim depends on it |
| Review snapshot changed concurrently | high | final canonical directory predeclared as `20260727T203000Z-final`; artifacts are frozen after its successful run until re-review |

## Final frozen-review findings before drafting

The editorial gate passed. Architecture and repository reviewers identified three remaining high-severity items, all accepted:

| Finding | Disposition |
|---|---|
| Bundle absent from Git history | baseline frozen bundle committed locally at `ce5ed2d`; revised execution runs from a committed input revision and the resulting canonical directory is committed before re-review |
| Destructive reinitialization omitted | C10.34, lifecycle predicate, ownership row, safe-subset prohibition, report warning, source-audit predicate, and validator requirement added |
| Public channel-array invariant treated only as a test skip | C10.35 and the safe subset now require effective count `<= TU_DMA_CHANNELS`; zero maps to three and requests 4–8 are source-audited as unsafe |
| Corruption probe contradicted the reinitialization prohibition | each corrupted graph now runs in an isolated child process that initializes once before submission and exits without reinit/traversal/flush/destroy; validator enforces the call order and process-isolation structure |
| Validator did not reject unsafe cleanup regressions in corruption children | validator now forbids DMA flush, descriptor/engine destruction, and loops in each child; bounds the sole tick before the corrupting submission; and requires `body()` to flow through `fflush(NULL)` to `_exit()` in the fork child branch |
| Guard still admitted `for`/`do`, extra first-child ticks, and runner cleanup | validator pins the complete extended probe SHA-256, forbids all C loop forms in corruption children, requires zero/one ticks in the first/second child, and exact-matches the complete fork child branch |

## Unsafe cases deliberately not executed

- unmodified four-channel pipeline harness;
- any direct initializer request for 4–8 channels;
- reinitialization while pending or active descriptors exist;
- public-wrapper out-of-bounds and arithmetic-overflow/index-overflow cases whose void bounds path may continue to memory access;
- traversal, flush, or destruction of corrupted chain/queue graphs;
- active-chain engine-destruction double-free path;
- over-capacity address-generator chain creation.

These are source-audited findings, not executable demonstrations.

## Re-review gate

Independent reviewers must verify that:

1. each accepted disposition is present in the revised artifact cited above;
2. the retained manifest verifies;
3. no revised conclusion exceeds the canonical logs or pinned source;
4. the title and scope remain one coherent reader decision;
5. no new critical/major blocker remains.

Only then may Chapter 10 prose be drafted.
