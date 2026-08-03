# Chapter 12 Skeptical Review Dispositions

- **Chapter boundary:** Multi-Core Clusters and Interconnect Heuristic Estimates
- **Tusim pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Review stage:** pre-draft evidence/scope gate
- **Method:** adversarial source, caller, configuration, test, report, and bounded-probe review
- **Canonical run:** `experiments/runs/ch12-multicore-interconnect/20260728-ch12-canonical-v2`

## Gate question

Can a skeptical reader use the planned evidence to distinguish byte-observable cluster behavior, isolated transfer estimates, simultaneous-traffic heuristic estimates, additive counters, and unsupported physical-NoC implications without silently importing stronger claims from headers or exploration reports?

## Dispositions

### R1 — “Self-contained cores” can imply isolation the implementation does not provide

**Finding:** The guide says cores never share mutable state, but core creation and operations reuse legacy process-global state through snapshot copy and swap helpers. No thread-safety contract or lock makes overlapping host calls safe.

**Disposition:** **Resolved.** The chapter boundary calls this a serialized compatibility facade. The source audit requires the copy, clear, swap-in, and swap-out evidence and absence of core-side thread launch. Concurrent host execution is treated statically and is never attempted by the executable probe.

### R2 — Functional multicore behavior and topology timing are separate APIs

**Finding:** A successful send could be misread as evidence that routed links, queues, or simultaneous transfer were executed.

**Disposition:** **Resolved.** Point-to-point send is tested as an immediate O-SRAM byte copy plus isolated timing/statistics update. Traffic-matrix estimation is tested separately and has no payload effect. Functional equality is never accepted as timing or calibration evidence.

### R3 — Message descriptor names overstate their consumers

**Finding:** `blocking`, `tag`, and caller-provided `latency_cycles` suggest synchronization, matching, and consumed latency semantics.

**Disposition:** **Resolved.** The source audit and custom probe require that send ignore all three, leave the caller descriptor unchanged, and use only the cluster's isolated estimate for destination cycles and statistics.

### R4 — Bounds logic is incomplete and unsafe cases must not be executed

**Finding:** Point-to-point send validates only 32-bit offset-plus-size arithmetic; this is not an explicit SRAM-capacity proof. All-reduce forms a 32-bit byte count and does not perform explicit region-span checks.

**Disposition:** **Resolved by qualification.** The ledger assigns region and overflow validation to trusted callers. The canonical probe uses small, in-range extents only. Undefined-behavior and out-of-range “tests” are forbidden.

### R5 — Configuration declarations are not equivalent to cluster-constructor inputs

**Finding:** `multicore_enabled`, `num_cores`, and `interconnect_mode` parse and survive conversion, but cluster construction still receives core count and topology explicitly. A source-only declaration audit could overstate runtime effect.

**Disposition:** **Resolved.** The config probe contrasts parsed `8/mesh` with an explicitly created `4/ring` cluster while proving that switching, contention, route order, link width, and router latency reach that cluster. The chapter must show this field-level split.

### R6 — Constructor validation is narrower than the public enum suggests

**Finding:** Core count and nonzero mesh rows are checked, but an out-of-range topology enum is not rejected by the constructor.

**Disposition:** **Resolved by qualification.** Callers are required to pass NONE, RING, or MESH. No constructor-wide enum-validation claim is permitted.

### R7 — Isolated switching equations are deterministic, not physical timing

**Finding:** Legacy, cut-through, and store-and-forward equations can reproduce exact integers while omitting injection, headers, queues, arbitration, flow control, and wire timing.

**Disposition:** **Resolved.** The probe requires the exact `15/79/207` snapshot for a 3-hop 1-KiB transfer and labels it an isolated model. External NoC references supply vocabulary and design obligations only; they do not calibrate Tusim.

### R8 — Shared-link mode is a heuristic estimate, not a contention simulator or proved bound

**Finding:** “Shared-link contention” can sound queue-accurate. The implementation accumulates directed-link serialization and combines one bottleneck service term with the maximum route term.

**Disposition:** **Superseded after independent review.** The initial disposition still overclaimed the result by treating the implemented global-max sum as a bound. Exact values `133`, `69`, and `69` remain snapshot outputs. The chapter now calls the quantity a deterministic route-load heuristic score and includes the disjoint-route counterexample that disproves the stronger makespan-bound label.

### R9 — Route choice is a placement interaction, not a universal winner

**Finding:** A single asymmetric XY/YX result could be promoted into a global route recommendation.

**Disposition:** **Resolved.** The probe uses a traffic pattern and its transpose, requiring exact reversal (`606/222` and `222/606`). The chapter retains both deterministic orders, identifies symmetric equality as a separate regime, and leaves adaptive routing unsupported.

### R10 — Ring/mesh selection needs regime-specific gains and costs

**Finding:** The standalone topology report historically presented mesh as universally preferable beyond a crossover.

**Disposition:** **Resolved.** The chapter must compare at least neighbor, all-to-all, and hotspot/fan-in regimes. It must identify mesh link/port cost and ring simplicity qualitatively while marking physical area, power, wire delay, and queue service unquantified. No single topology is selected globally.

### R11 — Broadcast timing is sequential send accumulation

**Finding:** “Broadcast” may imply multicast replication or overlap.

**Disposition:** **Resolved.** The canonical counter probe requires three point-to-point copies on four cores, 24 endpoint bytes, and 23 accumulated isolated-send cycles. No multicast fabric, route tree, or overlap claim is permitted.

### R12 — All-reduce accounting is not a routed collective model

**Finding:** FP32 all-reduce computes bytes correctly but bypasses send and traffic estimation. Its `N-1` message count and gather bytes omit result distribution, and its cycle delta is zero.

**Disposition:** **Resolved.** The chapter calls it host-orchestrated functional reduction. Zero cycle delta is explicitly interpreted as absent timing accounting, not zero-cost hardware. The Rabenseifner reference provides collective-algorithm vocabulary, not validation of this helper.

### R13 — Barrier names and fields imply synchronization that is absent

**Finding:** The guide says barriers synchronize, and the cluster declares `barrier_counter`. The implementation does not record arrivals or wait state.

**Disposition:** **Resolved.** The probe requires `stats.total_barriers` to increment, every core to receive `2 * hop_latency`, and `barrier_counter` to remain zero. The chapter calls this a barrier estimate/no-op, never a rendezvous simulation.

### R14 — The topology report's barrier conclusion is not runtime-reachable

**Finding:** The standalone topology report says mesh hop reduction would reduce barrier overhead, but `tu_cluster_barrier()` is topology-independent.

**Disposition:** **Resolved as rejected.** That report remains historical formula orientation only. Its topology-to-barrier implication is explicitly excluded.

### R15 — SPMD is not executable evidence at this pin

**Finding:** The implementation loops serially, its exact C-call inventory contains only the implementation itself, and the focused test's SPMD-named case calls per-core MMA directly.

**Disposition:** **Resolved.** The chapter may describe an implementation-only serial API loop. It must not claim simultaneous start, concurrent launch, or focused SPMD API coverage.

### R16 — Focused test denominators need semantic qualification and a negative control

**Finding:** `16/16` could be treated as broad multicore certification, and a copied output could be mistaken for a gating assertion.

**Disposition:** **Resolved.** The canonical run must statically count 16 distinct named test calls, preserve the nonzero failure exit, pass 16/16, then mutate the legacy expected cycle value from 15 to 14 and require a 15/16 nonzero result.

### R17 — The config test is not a passing canonical suite gate

**Finding:** In bounded development execution, the ICC parse/validation case prints PASS, but the process later aborts during TU init/MMA. Historical reports state 20/20.

**Disposition:** **Resolved by fail-closed preservation.** The canonical runner requires a nonzero config process, the earlier ICC PASS line, and the later test-start line. It does not infer a root cause or report suite success. Selected config behavior is established by the custom probe instead.

### R18 — Linked and standalone sweeps have different evidentiary strength

**Finding:** A Make target can look integrated even when its source duplicates equations and never links the cmodel.

**Disposition:** **Resolved.** Exact caller inventories and static-link gates classify contention/routing sweeps as linked analytical evidence and topology/switching/scaling sweeps as standalone orientation. Historical tables are not promoted into new runtime claims.

### R19 — Source acceptance and focused assertions must fail closed

**Finding:** A positive run alone does not show that source drift or assertion drift would stop the audit.

**Disposition:** **Resolved.** The canonical runner mutates the disposable `tu_cluster.c` and requires a source-audit failure, restores it and requires recovery, then forces one focused equation failure and requires the test binary to fail.

### R20 — Whole-book scope selection needs a real alternative comparison

**Finding:** Interconnect could have been selected merely because it was next in a roadmap.

**Disposition:** **Resolved.** Independent candidate reviews considered DRAM and vector/reduction engines as serious alternatives. Interconnect remains selected because it uniquely combines an uncovered reader decision, byte-observable effects, five exact cluster consumers, and discriminating linked traffic probes. The alternatives remain deferred rather than dismissed.

### R21 — The edition's older navigation already assigned Chapter 12 to SRAM

**Finding:** Chapter 4's prerequisite diagram named Chapter 12 as SRAM even though Chapter 9 now covers SRAM.

**Disposition:** **Resolved.** The diagram now points to Chapter 9. This editorial correction does not alter Chapter 4's technical claims.

## Remaining exclusions

The evidence cannot establish:

- physical NoC frequency, wire delay, area, power, or energy;
- packet/flit/header overhead, queue depth, arbitration, fairness, backpressure, or head-of-line blocking;
- virtual-channel design, adaptive routing, deadlock freedom, or liveness;
- coherent end-to-end parallel speedup or concurrent host-call safety;
- routed broadcast/all-reduce/barrier algorithms;
- numerical reproducibility beyond the exact host-order FP32 probe;
- a universal ring/mesh, switching-mode, or route-order winner.

## Independent skeptical batch received after canonical-v2

The two independent reviewers returned **BLOCK** verdicts after canonical-v2 had already been sealed. Their findings reopen this gate; canonical-v2 remains immutable historical evidence but is superseded for Chapter 12 closure.

### R22 — The combined shared-link expression is not a makespan lower bound

**Finding:** `max(max_isolated, max_link_service + global_max_route_cycles)` may add maxima from disjoint flows. A reproduced 4×4 XY case reports `isolated=94 bottleneck=128 estimated=158`, although the unrelated long route can overlap the shared-link pair and the natural shared-pair expression completes by 133.

**Disposition:** **Correction required and applied to prose; executable regression pending.** Rename the chapter and every shared-link result as a heuristic score. Preserve the two constituent necessary terms but do not call their implemented sum a bound. Add the counterexample to the probe and audit transcript.

### R23 — The chapter boundary joins adjacent, disconnected mechanisms

**Finding:** send copies bytes and calls only the isolated estimator; the traffic estimator consumes hypothetical messages; all-reduce bypasses both; barrier adds a constant; SPMD is serial.

**Disposition:** **Resolved in framing/manuscript.** The central teaching boundary is now adjacent APIs at different evidence rungs, not one integrated NoC model.

### R24 — W/A/O isolation was overstated

**Finding:** the focused test directly discriminates W-SRAM pointers and values, but the retained probe does not prove full W/A/O pointer-and-value isolation.

**Disposition:** **Resolved by qualification.** The ledger and manuscript retain only the observed W-SRAM claim; source allocation of A/O is not promoted into complete isolation evidence.

### R25 — Successful collective examples need bounded-input and transactional qualifications

**Finding:** all-reduce has unchecked 32-bit byte multiplication and no explicit region-span check; broadcast can leave partial effects after a later failure.

**Disposition:** **Resolved in claim wording; source enforcement pending.** Functional claims now require bounded, in-range inputs and successful return. Broadcast is explicitly sequential and non-transactional. Unsafe boundary executions remain excluded.

### R26 — “Serialized facade” implied enforcement

**Finding:** no lock or serialization primitive exists around process-global swaps.

**Disposition:** **Resolved.** Use “global-state-swapping facade, exercised sequentially” and keep thread safety unsupported.

### R27 — Generated config and SRAM safety sources were omitted from hashes

**Finding:** `scripts/gen_config.py` and `tu_cmodel/tu_sram.[ch]` materially affect compile-time configuration, allocation, and bounds behavior.

**Disposition:** **Open for canonical-v3.** Add exact hashes and scoped predicates. Parse complete shipped JSON/YAML multicore/ICC values rather than checking selected literals.

### R28 — Caller inventories need narrower labels and per-API sets

**Finding:** inventories covered C call expressions, not every language/document surface; several public APIs were grouped.

**Disposition:** **Open for canonical-v3.** Label them exact C-call inventories and split transfer, send, broadcast, all-reduce, barrier, and SPMD sets.

### R29 — Config retention is not an end-to-end A/B effect proof

**Finding:** the probe retained five parsed fields in cluster state, while equation/route probes separately assigned fields.

**Disposition:** **Qualified.** Retention and direct consumer behavior remain separate claims unless canonical-v3 adds one-field-at-a-time parse→convert→construct→effect checks.

### R30 — Public header contracts contradict implementation

**Finding:** comments promise rendezvous, concurrent SPMD, and message-field behavior absent from implementation.

**Disposition:** **Resolved editorially; source checks pending.** Treat these as stale public-contract contradictions, never confirming evidence.

### R31 — Probe implementation has avoidable robustness defects

**Finding:** descriptor equality used `memcmp` over possible padding; config-dependent work continued after parse failure.

**Disposition:** **Open for canonical-v3.** Compare descriptor fields individually, initialize config state, and stop dependent checks after parse failure.

### R32 — Extreme traffic accumulation can overflow

**Finding:** directed-link service accumulation uses unchecked `uint64_t` addition.

**Disposition:** **Open for static qualification.** Do not execute extreme cases; record a trusted-caller bound and add a source predicate.

## Gate decision

**Current verdict:** **BLOCK.** Canonical-v2 is a valid immutable record of the exact outputs it captured, but its pre-draft framing used an invalid lower-bound classification and its audit omitted claim-critical surfaces. Drafting and closure are reopened pending canonical-v3, updated manifests, and a passing post-v3 pre-draft validator.
