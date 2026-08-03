# Chapter 12 Multi-Core and Interconnect Audit — 2026-07-28

- **Chapter:** Multi-Core Clusters and Interconnect Heuristic Estimates
- **Tusim pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Canonical runner:** `experiments/run_ch12_multicore_interconnect_audit.sh`
- **Canonical retained run:** `experiments/runs/ch12-multicore-interconnect/20260728-ch12-canonical-v5/`
- **Verdict vocabulary:** source predicates and executable observations match the pinned snapshot; this is not RTL or silicon validation

## Question

Given core-local state, a point-to-point or collective operation, and a traffic matrix, what does pinned Tusim execute functionally, which configuration reaches that behavior, and which cycle quantity is an isolated estimate, a simultaneous shared-link heuristic estimate, an additive counter, or absent?

The audit deliberately does not ask whether Tusim is a cycle-accurate NoC. No packet, queue, arbitration, backpressure, virtual-channel, or calibrated physical-link model was found in the selected implementation.

## Scope decision

Fresh whole-book reconnaissance compared multicore/interconnect, vector and reduction engines, standalone DRAM, counters, contexts, liveness, and operator engines. Three independent reviewers preferred three different next chapters: interconnect, vector/reduction engines, and DRAM. Interconnect was retained because it uniquely combines:

- byte-observable functional public APIs;
- exact runtime consumers for five ICC configuration fields;
- isolated switching equations;
- linked traffic-matrix contention and route-order analysis;
- discriminating focused tests;
- a precise deterministic-heuristic-estimate fidelity label.

The dissent remains documented in `notes/chapter-12-framing-and-evidence-plan.md`. DRAM and vector/reduction engines are deferred work units, not rejected models.

## Provenance and containment

The canonical runner must:

1. require the Tusim checkout to be detached, tracked/untracked clean, and exactly at the edition pin;
2. require the book input commit to be clean and to have zero remotes;
3. hash the ignored Tusim inventory before and after;
4. create a disposable source tree with `git archive`;
5. build only `libtucmodel.a` in that extraction;
6. compile every audited binary explicitly against the archive and reject dynamic `libtucmodel` dependencies;
7. bound every executable with `timeout` and disable core files for the known non-passing config suite;
8. preserve source/input hashes, complete logs, transcript, copied book-side inputs, and a run-relative SHA-256 manifest;
9. verify that Tusim and all book inputs are unchanged after execution.

The pinned Makefile's `clean` recipe is never invoked because it removes process-global `/tmp` names outside the disposable extraction.

An initial sealed execution at `20260728-ch12-canonical` completed the source, build, mutation, test, sweep, probe, provenance, and manifest gates, but exposed a false-negative in the pre-draft validator. Canonical-v2 fixed that validator and sealed the expected outputs. A later independent skeptical review disproved the manuscript's classification of the combined global-max equation as a makespan lower bound and identified omitted generator/SRAM evidence. Canonical-v3 corrected those findings, but independent manuscript/reproducibility review then found arithmetic qualifications, stale anchors, and bundle-closure defects. Canonical-v4 completed the audit body and inner finalization, then its retained pre-draft validator failed on an overly specific disposition-phrase assertion; it has no outer bundle seal. All earlier runs remain immutable historical evidence; canonical-v5 is the pending replacement seal.

## Static source gate

`experiments/ch12_source_audit.py` accepts only the exact edition pin and enforces:

- 28 exact source/config/generator/SRAM/test/report hashes;
- archive and target membership;
- core swap-in/swap-out reachability through legacy global APIs;
- cluster construction and topology equations;
- exact consumers for switching, contention, route order, link width, and router latency;
- send, broadcast, all-reduce, barrier, and SPMD implementation boundaries;
- configuration conversion omissions and retained ICC fields;
- the exact 16-call focused multicore test inventory and fail-closed exit;
- exact C-call caller sets for individual cluster methods, construction, transfer estimation, and traffic estimation;
- static arithmetic boundaries for send-span wraparound, mesh-column numerator wraparound, the 32-bit-width-bounded per-link accumulator, and the unchecked final shared-score addition;
- linked traffic sweeps versus standalone duplicated-formula sweeps.

At the canonical-v5 audit-input snapshot this is 155 structural/reachability predicates, for 183 source checks including hashes. The canonical transcript must contain:

```text
CH12_SOURCE_AUDIT PASS pin=e918c80b6fce833cd1fcae97730fa841c2176f25 hashes=28 predicates=155 checks=183
```

A mutation control appends one byte to the disposable `tu_cluster.c`, requires a hash-mismatch failure, restores the file, and requires the audit to pass again before building.

## Functional and analytical findings

### Core ownership is a serialized facade

`tu_core_t` stores a `tu_state_t`, identity/lifecycle fields, and declared ICC-buffer fields. Creation initializes process-global `g_tu`, copies the result into the core, and clears `g_tu`. Operation wrappers copy a selected core state into `g_tu`, call an existing global API, copy state back, and restore the prior global snapshot.

This supports stored per-core SRAM/state observations under serialized calls. It does not establish simultaneous host execution, thread safety, or isolation of every process-global subsystem.

### Configuration splits at cluster construction

The custom probe parses a full config requesting enabled multicore, eight cores, mesh topology, store-and-forward, shared-link contention, YX routing, 32 bytes/cycle, and seven router cycles. Conversion retains the last five timing/routing fields. An explicit `tu_cluster_create(4, RING, ...)` then creates four ring cores while consuming those five fields.

Expected compact observation:

```text
CONFIG parsed_enabled=1 parsed_cores=8 parsed_topology=2 cluster_cores=4 cluster_topology=1 sw=2 contention=1 route=1 link=32 router=7
```

Therefore:

- `multicore_enabled`, `num_cores`, and `interconnect_mode` are parsed and validated full-config declarations but are dropped by `tu_config_to_runtime()`;
- core count and topology remain explicit constructor arguments;
- switching, contention, route order, link width, and router latency cross conversion and are consumed by the cluster.

No selected field has external calibration evidence. The constructor validates core count and nonzero mesh rows but does not reject an out-of-range topology enum; callers must supply NONE, RING, or MESH.

### Point-to-point equations are isolated estimates

For three mesh hops, 1,024 bytes, 16 bytes/cycle, and five router cycles:

```text
legacy = 3 * 5 = 15
cut-through = 3 * 5 + ceil(1024 / 16) = 79
store-forward = 3 * (5 + ceil(1024 / 16)) = 207
```

Expected observation:

```text
EQUATIONS legacy=15 cut=79 store=207
```

Zero-byte and same-core estimates are zero. Invalid/unreachable routes and non-legacy transfers with zero link width return `UINT64_MAX`. These are deterministic implementation equations, not network execution traces.

### Send couples an immediate byte effect to additive accounting

The probe writes 16 bytes to core 0 O-SRAM and sends them two ring hops to core 2 with `blocking=false`, a nonzero tag, and descriptor `latency_cycles=999`. The destination bytes match immediately. The caller descriptor is unchanged. The transfer adds 15 to cluster `total_icc_cycles` and destination core `estimated_cycles`; source and unrelated core cycle fields do not change.

Expected observation:

```text
SEND blocking=0 descriptor_latency=999 stats_messages=1 stats_bytes=16 stats_cycles=15 dst_delta=15
```

Thus `blocking`, `tag`, and descriptor `latency_cycles` do not supply nonblocking transport, tagging behavior, or an output-result contract at this pin. `total_icc_cycles` is a sum over successful sends, not cluster elapsed time.

The source performs offset checks with 32-bit addition. Integer-wrap cases remain a static trusted-caller precondition and are intentionally not executed.

### Traffic estimation is a simultaneous route-load heuristic

Two identical one-hop 1 KiB messages on one directed link, at 16 bytes/cycle and five router cycles, have an isolated estimate of 69 cycles. Shared-link service accumulates 128 serialization cycles and adds the maximum route term, yielding 133. Disjoint links and ideal-parallel mode remain at 69.

Expected observations:

```text
TRAFFIC same=133 disjoint=69 ideal=69 bottleneck=128 link=0->1
HEURISTIC_COUNTEREXAMPLE isolated=94 bottleneck=128 estimated=158 shared_pair_term=133 link=0->1
```

The shared equation is:

```text
max(max isolated transfer,
    maximum directed-link serialization load + global maximum route latency)
```

The second observation is the critical counterexample. Two 1 KiB messages share `0→1`; an unrelated six-hop `12→3` message uses disjoint links. The implementation adds the long route's 30-cycle term to the busy link's 128-cycle service term. Because the disjoint groups can overlap, 158 can exceed a feasible schedule. The equation is therefore a deterministic heuristic score, not a proved makespan lower bound. It also has no injection times, arbitration, finite buffers, virtual channels, credit flow, head-of-line blocking, or queue schedule.

### Route order is traffic-specific

For a 4x4 mesh, pattern A is the nine-message Cartesian set `{1,2,3} × {4,8,12}` and pattern B is its 90-degree counterclockwise rotation, `{0,4,8} × {13,14,15}`. The two patterns reverse which deterministic route order concentrates traffic. Expected custom-probe observation:

```text
ROUTES patternA_XY=606 patternA_YX=222 patternB_XY=222 patternB_YX=606
```

The linked 4 KiB sweep gives the same ranking reversal at a different payload, while symmetric all-to-all gives equal XY/YX heuristic scores. This supports traffic-regime comparison, not a universal route-order winner.

Ring routing uses shortest paths and chooses clockwise on equal-distance ties. The audit does not infer deadlock freedom because the selected model has no finite channel/flow-control implementation.

### Collectives have different contracts

Broadcast loops over destinations and calls point-to-point send. On a four-core ring with an 8-byte payload it performs three immediate copies and accumulates 24 bytes and 23 send-estimate cycles.

FP32 all-reduce reads each core through host operations, sums in ascending core order, and writes the result to every core. It increments only `N-1` message and gather-byte counts. It does not call send, add cluster ICC cycles, or add per-core estimated cycles. Its observed zero cycle delta means absent timing accounting, not zero-cost hardware. The helper also forms a 32-bit byte count and performs no explicit SRAM-span validation; the executable probe therefore uses only small, in-range extents.

Barrier increments `stats.total_barriers` and evaluates `hop_latency * 2` in 32-bit arithmetic before widening for each core. This equals the mathematical double only for `hop_latency <= UINT32_MAX / 2`; the controlled probe uses 5. The helper has no arrival, wait, or topology-dependent rendezvous state; the separate `barrier_counter` field remains zero.

Expected observation:

```text
COLLECTIVES broadcast_messages=3 broadcast_bytes=24 broadcast_cycles=23 allreduce_message_delta=3 allreduce_byte_delta=36 allreduce_cycle_delta=0 barrier_delta=10 barrier_state=0
```

The SPMD method similarly loops over cores and invokes legacy text execution serially. Its exact C-call inventory contains only the implementation itself. The focused test's SPMD-named case calls per-core MMA directly and does not execute this API. Header words such as “concurrently” and “all cores must reach” are not promoted over implementation evidence.

## Test qualification

### Focused multicore suite

The exact focused source invokes 16 distinct named tests and returns nonzero when `tests_failed` is nonzero. The canonical build must report:

```text
=== Results: 16/16 passed, 0 failed ===
```

A disposable mutation changes the legacy expected value from 15 to 14. The mutated binary must return nonzero and report 15/16, demonstrating that the exact equation is gating rather than merely printed.

This remains a pinned regression snapshot, not certification of physical multicore behavior. In particular, the SPMD-named test does not call the SPMD API.

### Configuration suite

The exact-pin configuration binary is not accepted as a passing suite. In development execution it printed PASS for the selected ICC parse/validation case and then aborted during a later TU-init/MMA case. The canonical runner preserves the nonzero return and log but does not diagnose that later failure in this chapter.

The selected configuration claims instead gate on exact source conversion plus the custom parse→convert→construct→effect probe.

### Linked and standalone sweeps

The contention and route-order sweeps call `tu_cluster_estimate_traffic_cycles()` and are compiled against the static archive. Their tables remain analytical heuristic observations.

The topology and switching sweeps compile standalone formulas without the cmodel archive. Historical reports based on them are orientation and drift evidence, not runtime-integration proof. The multicore-scaling report is also not promoted into a new speedup claim.

### Document drift that must not enter the chapter as implementation fact

The pinned multicore guide says cores never share mutable state, SPMD programs start simultaneously, and barriers synchronize. The implementation instead swaps a process-global state sequentially, has no C caller of the serial SPMD helper beyond its own definition, and implements barrier as a statistics/cycle update without arrival or wait state. Source and reachability therefore override those guide claims.

The standalone topology report also says that changing to mesh would reduce barrier overhead. Its formula is not the implementation of `tu_cluster_barrier()`: the latter adds `2 * hop_latency` regardless of topology. The report's corrected traffic-aware topology discussion remains useful orientation, but its barrier implication is rejected.

The linked switching, contention, and routing reports record historical `test-config` 20/20 results. In the present bounded build, the ICC parse/validation case prints PASS before a later case aborts. The current process result is preserved rather than silently replaced by the older summary.

## Evidence classification

| Surface | Classification |
|---|---|
| per-core SRAM snapshots and immediate send/broadcast bytes | executable functional behavior under serialized calls |
| host FP32 all-reduce | executable functional helper, not routed collective |
| switching equations | isolated deterministic estimates |
| traffic matrix | deterministic simultaneous heuristic estimate |
| cluster/core cycle fields | additive estimated counters with named producers |
| enabled/count/topology full-config fields | parsed/validated declarations, not runtime cluster construction |
| five ICC timing/routing fields | parsed, converted, and retained; direct consumers separately effect-tested, without one sealed full-path one-field A/B test |
| NoC queues/arbitration/backpressure/deadlock/area/power | not modeled by selected implementation |
| RTL/FPGA/silicon comparison | not established |

External references [DT01], [DS87], and [PY09] provide network and collective vocabulary. They do not validate Tusim or fill missing implementation rungs.

## Reproduction

From a clean book input commit with no book remotes and the Tusim checkout detached/clean at the exact pin:

```bash
cd /home/zxy/Workplace/books/tusim-book
CH12_RUN_ID="repro-$(date -u +%Y%m%dT%H%M%SZ)" \
  bash experiments/run_ch12_multicore_interconnect_audit.sh
```

A reproduction creates a new run directory and never overwrites the canonical bundle. Verify a completed run with:

```bash
cd experiments/runs/ch12-multicore-interconnect/<run-id>
sha256sum -c sha256-retained.txt
sha256sum -c bundle-sha256.txt
```

The inner retained manifest uses only run-relative paths and includes the complete transcript. The outer manifest covers the inner manifest, `finalization.log`, and the retained `predraft-validation.log`; the later local evidence-seal commit authenticates that outer trust root. No source archive, extracted source tree, object file, binary, or core file is retained as evidence.

## Verdict

**Canonical-v5 completed with runner exit 0.** It retained a passing pre-draft validation and a verified outer bundle manifest over the inner manifest, finalization record, and validation log. The corrected evidence supports a chapter about **adjacent functional cluster helpers, isolated equations, and deterministic route-load heuristic scores**. It does not support one integrated NoC model, concurrent cores, packet transport, a proved traffic makespan bound, complete collective timing, cycle-accurate behavior, or calibrated multicore speedup.
