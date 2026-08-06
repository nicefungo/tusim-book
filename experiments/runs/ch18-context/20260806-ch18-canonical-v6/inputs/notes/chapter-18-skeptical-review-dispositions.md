# Chapter 18 — Skeptical Review Dispositions

**Date:** 2026-08-05
**Source pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
**Reviewed provisional bundle:** `20260805-ch18-canonical-v4` at book commit `8642451f8a32d983f589bef8f4eea15eb086ad0f`
Review state: **complete**
Drafting verdict: **PASS** — effective only when the post-review canonical bundle passes normal and optimized validation and both manifests verify. Canonical v4 remains immutable provisional history and is superseded for drafting.

## Review provenance

Three hostile review workstreams independently checked: (1) lifecycle/ownership/scheduling/accounting, (2) field and machine-state completeness, and (3) runner/validator/determinism/bundle closure. Full artifacts are retained in the Hermes delegation records `deleg_9fce3ff2` and `deleg_95db6277`. Reviewers rebuilt or inspected the exact pin read-only and made no source changes.

## Dispositions

1. **Global subnormal mode omitted — RESOLVED.** `tu_precision.c/.h` are hash-locked; source predicates classify `g_subnormal_mode`; the probe demonstrates global continuation; C18.29 also classifies the process-global error mode.
2. **First-context cycle baseline and allocation cloning omitted — RESOLVED.** `allocation_clone` records two inherited core snapshots and zero cycle baselines. C18.16/16a state that the first save charges pre-allocation history and that allocation clones the current shared image.
3. **Transition/field completeness overclaim — RESOLVED.** PRE/POST `SURFACE` records now enumerate all W/A/O bytes and aggregate/per-bank fields, all runtime fields, all required manager/descriptor fields, config-override digest and saved ownership, complete queue scalars/nested registries, DMA domains, plugin/public state, precision controls, and outer-core ownership. Added COMPLETED free, already-ACTIVE switch, repeated ties, under/exact/over thresholds, wrap, and ACTIVE/BLOCKED/READY/IDLE/COMPLETED unblock trajectories. Opaque/global or unstable-address surfaces are structurally classified and explicitly bounded rather than misrepresented.
4. **Notification wrap omitted — RESOLVED.** The probe observes command and cycle maxima wrapping to zero; source predicates and C18.15 qualify expiry at type limits.
5. **`active_count` wording too strong — RESOLVED.** C18.5 says it is intended as allocated-descriptor count but becomes unreliable after accepted invalid-state frees.
6. **Live double-buffer ownership loss/leak understated — RESOLVED.** C18.23 and the report import Chapter 16's stronger ownership/leak/active-role consequence and state that Chapter 18 deliberately avoids executing the leaking path.
7. **Queue/synchronization evidence overstated — RESOLVED/QUALIFIED.** The queue census and digest now include all scalar, command, dependency, and signal fields. The sentinel is explicitly described as fabricated but memory-safe evidence of non-restoration, not legal async drainage. The report preserves the synchronous early-return, asynchronous unbounded-loop, and no-global-DMA-drain limits.
8. **Plugin audit incomplete — RESOLVED/QUALIFIED.** All three plugin implementations and the dispatcher are hash-locked; source predicates classify global registry and opaque mutable `impl_data`. Executable evidence remains pointer/public-counter discrimination only, as stated.
9. **Outer core and DRAM ownership absent — RESOLVED.** The ledger/report classify outer `tu_core_t` identity/init/ICC fields as unretained and standalone DRAM as separately constructed/caller-owned; DRAM implementation/header are hash-locked.
10. **Outer bundle/finalization bypass — RESOLVED.** The validator parses exact unique inner and outer sets, verifies every digest, binds finalization to run/commit/transcript digest, and rejects extra files through exact inventory comparison. Historical validation compares frozen inputs to `git show <input_commit>:<path>` rather than current HEAD.
11. **Probe teardown leaks and hidden stderr — RESOLVED.** Probe teardown destroys queue internals and registry state exactly once before core destruction. Canonical execution retains stderr and adds an ASan/UBSan leak gate; local post-fix sanitizer execution reported no sanitizer errors.
12. **Unsequenced `printf` mutation — RESOLVED.** Slice notifications and resets execute in separate statements before printing saved results. Under/exact/over command and cycle outcomes are checked explicitly.
13. **Optimization/determinism wording too broad; processes unbounded — RESOLVED.** Every executable is timeout-bounded and diagnostics retained. The marker now says only `probe_translation_unit_O0_O2_match`; it does not claim full-library or cross-compiler invariance.
14. **Malloc ordinal not call-site-specific — RESOLVED.** The wrapper records call count and sizes; rows require exact 64-byte ordinals; the source audit requires exactly three retained-copy calls.
15. **SRAM `total_size` omission finding — REVIEW CORRECTION, RESOLVED.** A post-v5 hostile review found that the earlier predicate inspected only `ctx_copy_sram_data()` and missed the assignments in `ctx_save_full_state()`. The pinned source saves W/A/O `total_size` and restores all three values. The source gate now enforces the complete save-and-restore path; C18.22 and the audit report preserve only the real aggregate-versus-per-bank split. Canonical v5 is superseded for drafting by the post-correction seal; pinned source remains read-only.

## Surviving architecture conclusions

- Exactly 19 public context APIs exist and there is no external non-test caller at the pin.
- FULL/LIVE/CONTROL costs recompute to `16484/4196/100` for the cited 256-KiB sweep.
- Direct restore can create two ACTIVE descriptors; rejected switches and frees can violate ownership and accounting invariants.
- Queue, operative DMA, plugin internals, precision controls, outer-core/ICC, and DRAM are not isolated by descriptor save/restore.
- The switch ledger is an analytical manager-local model, not calibrated latency or a legal arbitrary preemption mechanism.

## Gate decision

The amendments are accepted. Drafting may begin only from the later committed post-review seal that contains this file and passes the fail-closed canonical runner, normal and optimized validation, retained hashes, finalization binding, exact inventory, and outer bundle hashes. Any input change after that seal reopens the gate.
