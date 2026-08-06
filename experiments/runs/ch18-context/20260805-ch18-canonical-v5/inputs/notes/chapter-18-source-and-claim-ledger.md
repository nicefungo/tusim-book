# Chapter 18 — Source and Claim Ledger

**Title:** Runtime Context Retention and Preemption Boundaries

**Edition pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25` (read-only)

**Status vocabulary:** verified / qualified / rejected / blocked

**Predraft status:** post-review inputs complete; drafting is authorized only by the final canonical seal and both manifest layers passing.

## Reader decision and evidence boundary

- **C18.1 (verified):** The reader decision is made at a named legal preemption boundary: choose which state is retained, who supplies the safe-point and live-prefix contract, and which isolation and switch-cost claims follow. FULL, LIVE-prefix, and CONTROL-only are materially different architecture alternatives rather than quality levels of one universally best design.
- **C18.2 (rejected):** The pin does not establish autonomous or arbitrary-boundary preemption. The manager has no non-test caller; command/cycle notifications are caller-fed; slice expiry is only a query; and `tu_ctx_request_switch()` switches immediately rather than recording a deferred synchronization-point request.
- **C18.3 (qualified):** Focused 15/15 and the context sweep certify bounded standalone behavior. They do not prove integration, safe-point legality, queue/DMA drain completeness, fairness, calibrated latency, or complete isolation. Context descriptors snapshot selected `tu_state_t` fields only; outer `tu_core_t` identity/initialization/ICC ownership is shared and not retained per descriptor.

## Public surface, ownership, and lifecycle

- **C18.4 (verified):** `tu_context.h` declares exactly 19 public `tu_ctx_*` operations. The source audit derives the set from the header and finds zero external non-test callers outside the implementation/header, tests, and docs.
- **C18.5 (qualified):** `active_count` is intended and used as an allocated-descriptor count, not an ACTIVE-owner count, but the IDLE-free defect can corrupt even that interpretation. Correct ownership requires the tuple `(active_ctx_id, every descriptor state, active_count)`; the implementation does not enforce exactly one ACTIVE descriptor.
- **C18.6 (rejected):** Direct `tu_ctx_restore()` is not a safe context-switch operation while another descriptor is ACTIVE. It activates a READY target and changes `active_ctx_id` without demoting the old ACTIVE descriptor, producing two ACTIVE descriptors.
- **C18.7 (rejected):** Rejected `tu_ctx_switch()` is not failure-atomic. The function saves and demotes the outgoing ACTIVE descriptor before validating/restoring the target. Invalid, IDLE, or BLOCKED targets return failure with no ACTIVE descriptor, a stale `active_ctx_id`, and retained `pending_save_bytes`.
- **C18.8 (qualified):** A self-target switch succeeds: the active context is saved to READY and immediately restored, one switch is counted, and fixed/traffic overhead is charged. The API does not reject the no-op architectural request.
- **C18.9 (rejected):** Freeing the ACTIVE context does not transfer ownership. It saves then frees the descriptor, decrements `active_count`, leaves `active_ctx_id` stale, and leaves no ACTIVE descriptor.
- **C18.10 (rejected):** Freeing an already-IDLE slot is not a no-op when another context is allocated. `tu_ctx_free()` clears the slot and decrements `active_count` for every non-ACTIVE state, so an IDLE free can report zero allocated contexts while one descriptor remains ACTIVE.
- **C18.10a (rejected):** Reusing the freed active slot does not recover ownership when another descriptor remains allocated. Because `active_count` is nonzero, allocation returns slot 0 as READY; the result is two READY descriptors, zero ACTIVE descriptors, and stale `active_ctx_id=0`.
- **C18.11 (qualified):** READY, BLOCKED, COMPLETED, and IDLE descriptors can all be freed despite header prose saying IDLE or COMPLETED. `TU_CTX_COMPLETED` is printable and schedulable as a vocabulary value, but no pinned implementation path produces it.
- **C18.12 (qualified):** `tu_ctx_block_current()` saves the active context then marks it BLOCKED, leaving no ACTIVE descriptor and stale manager ownership until the caller schedules/restores another context. `tu_ctx_unblock()` returns success for any in-range state and changes only BLOCKED to READY.

## Scheduling, notifications, and accounting

- **C18.13 (verified):** Round-robin selects the first READY descriptor after `active_ctx_id`, wrapping by slot index. It is deterministic slot traversal, not a fairness or service guarantee.
- **C18.14 (qualified):** Priority scheduling selects the first READY descriptor with strictly greater priority than a `best_prio=0` sentinel. Equal positive priorities tie by lowest slot index; READY priority-zero contexts are never selected. Repeated selection therefore has starvation risks and no aging.
- **C18.15 (qualified):** Slice expiry uses inclusive thresholds (`>=`) independently for caller-fed cycles and commands. Zero disables that threshold. The manager does not trigger a switch automatically. The unsigned counters are unchecked: incrementing their maxima wraps both to zero and can make an expired slice appear fresh.
- **C18.16 (rejected):** Notification accounting is not per-context execution accounting. `tu_ctx_notify_command()` and `tu_ctx_notify_cycles()` update only manager slice counters, even when no descriptor is ACTIVE. `total_commands` has no producer; `total_cycles` changes only on save from an unsigned difference of legacy core `estimated_cycles` and `last_switch_cycle`, with no monotonicity check or saturation. The first allocated descriptor has a zero `last_switch_cycle`, so its first save attributes all pre-allocation core history to that context. The probe separately observes `5-10` wrap to `18446744073709551611`.
- **C18.16a (qualified):** Allocation is cloning, not blank independent initialization: every allocation snapshots the current shared core image. A later READY context can inherit the active context's bytes, counters, runtime configuration, and shared pointers at allocation time; isolation begins only after that inherited snapshot and correctly bounded subsequent switches.
- **C18.17 (qualified):** `total_cycles_stolen` is a manager-local analytical ledger. Restore adds fixed cost plus `ceil((pending outgoing bytes + incoming saved bytes)/state_bytes_per_cycle)` when bandwidth is nonzero. A zero bandwidth suppresses the transfer term entirely rather than rejecting the config or representing infinite latency. The ledger does not advance legacy core time, command-queue time, global DMA time, SRAM-bank time, or Chapter 17 producers.
- **C18.18 (qualified):** Direct restore can charge incoming bytes without an outgoing save; failed switches leave outgoing `pending_save_bytes` for a later restore. The ledger therefore describes call history, not necessarily one atomic hardware handoff.

## Retained SRAM alternatives

- **C18.19 (verified):** FULL deep-copies each region's complete `banks.size`; LIVE deep-copies exactly one configured W/A/O prefix; CONTROL copies zero SRAM bytes. LIVE extents are validated only against region sizes and are caller-supplied—no compiler/liveness bridge exists.
- **C18.20 (qualified):** LIVE restores retained prefixes while non-live tails remain from the intervening core image. Isolation is valid only for the retained prefixes plus an external safe-point/reload contract; stale tails are deliberate behavior, not transparent context isolation.
- **C18.21 (qualified):** CONTROL reports zero retained SRAM and fixed-only switch cost, but software reload, backing-store traffic, dependencies, contention, and end-to-end resume latency are omitted. Its smallest model row is not proof of lowest latency or energy.
- **C18.22 (qualified):** Save/restore explicitly copies bank capacity/geometry, aggregate access/conflict/stall counters, bandwidth-policy scalars, region cycle, and name, but deliberately drops saved `bw_banks`. It also fails to save region `total_size` before restoring it from the zero-initialized saved object. Aggregate metadata, region metadata, and live per-bank arbitration state can therefore come from different contexts.
- **C18.23 (rejected):** Double-buffer ownership is not context-retained. Restore sets every live region `db=NULL` without serializing or freeing the displaced object; active-role identity is lost and a live allocation can leak. The bounded Chapter 18 probe avoids executing that leaking trajectory; Chapter 16's sealed evidence remains authoritative for it.

## Queue, DMA, synchronization, plugin, and precision state

- **C18.24 (rejected):** Header/docs and implementation-comment claims of command-queue snapshot/recreation are false. Save stores only the queue pointer; restore deliberately keeps the live pointer and does not restore commands, dependencies, signals, indices, counts, or queue clock. The probe preserves discriminating live queue sentinels across a context switch.
- **C18.25 (qualified):** `tu_core_sync()` swaps the selected core state into `g_tu`, calls only `tu_cmdq_sync_all()`, and swaps back. Command-queue sync returns immediately for synchronous queues; for asynchronous queues it loops until `count==0` with no timeout or deadlock escape. It does not flush descriptor DMA or prove every copied/dropped subsystem quiescent.
- **C18.26 (rejected):** The copied `tu_state_t.dma` is not the operative descriptor engine. `tu_init_with_config()` initializes process-global `g_tu_dma`; ordinary descriptor APIs consume that global; `tu_state_t.dma` starts as a separate embedded struct. Context save/restore copies the embedded struct, including shallow descriptor pointers if populated, but does not own or drain `g_tu_dma`.
- **C18.27 (verified):** A safely bounded pending global descriptor remains queued across `tu_ctx_switch()`. Its queue depth and pointer identity are unchanged while the target's embedded DMA snapshot is restored independently.
- **C18.28 (qualified):** Context save/restore copies the selected dataflow plugin pointer. The registry and plugin objects are process-global and mutable (`total_flops`, `total_tiles`, `total_cycles`, and `impl_data`); pointer restoration does not isolate plugin internals.
- **C18.29 (rejected):** Precision-state snapshot claims are false for process-global rounding mode, xorshift PRNG state, subnormal mode, and error mode. They continue globally across context switches; none is in `tu_state_t` or the context manager. The probe discriminates rounding, PRNG continuation, and subnormal mode; error mode is hash-locked and structurally classified.
- **C18.30 (verified):** The implementation copies five legacy core ledgers (`total_dma_bytes`, MMA calls/tiles/FLOPs, `estimated_cycles`), runtime config, selected dataflow pointer, embedded DMA struct, and `initialized`. It does not thereby retain every Chapter 17 counter/trace/power producer.

## Configuration, dead controls, and failure behavior

- **C18.31 (verified):** Context policy is C-API-only. Shipped JSON/YAML and global config parsing/runtime conversion contain no context-manager block. Linkage and focused Make rules do not create runtime reachability.
- **C18.32 (rejected):** `save_dram_state` is declared but never copied into the manager or consumed. No DRAM model is a `tu_state_t` member; standalone DRAM objects are separately constructed and caller-owned. `has_config_override`, `config_override`, and `user_data` remain descriptor metadata with no switching/scheduling effect.
- **C18.33 (qualified):** Config validation rejects null core/config, zero slots, invalid policy/scope, and LIVE extents above capacity. It does not bound `max_contexts`, fixed cost, bandwidth, time slices, or priorities beyond their C types.
- **C18.34 (verified):** The source contains exactly three retained-copy calls. The malloc wrapper records exact ordinals and requested sizes: injected first/second/third 64-byte failures return `-1`, leave the slot IDLE and `active_count=0`, and free every partial retained allocation.
- **C18.35 (rejected):** Re-saving an existing context is not failure-atomic. The implementation frees the previous W/A/O snapshot before copying the replacement. An injected later-copy failure can leave the descriptor ACTIVE but destroy all or part of its prior restorable snapshot; no rollback exists.
- **C18.36 (blocked):** A real `calloc` failure in manager construction is structurally handled, but the canonical probe does not globally wrap `calloc` because doing so would also perturb core/plugin/queue setup. This remains a structural claim rather than an executable allocation-failure result.
- **C18.37 (blocked):** Restore has no normal allocation or explicit failure point after READY validation. Safely forcing an invalid retained pointer/length would invoke undefined behavior rather than test a supported failure path; target-restore failure atomicity beyond state validation remains unsupported.

## Sweep and architecture trade-offs

- **C18.38 (verified):** For 256 KiB total SRAM, 100 fixed cycles, and 32 B/cycle, the executable sweep gives FULL `262144 B / 16484 cycles`, LIVE25 `65536 B / 4196 cycles`, and CONTROL `0 B / 100 cycles`. These equal fixed plus two-way retained-byte traffic under the source equation.
- **C18.39 (qualified):** Sweep cycles are deterministic model ledger values, not wall-clock memcpy measurements or calibrated preemption latency. They omit context-store allocation/area, queueing, reload, DRAM contention, setup, ECC, dirty scans, and synchronization latency.
- **C18.40 (qualified):** Alternatives are regime-specific: FULL offers the strongest modeled SRAM isolation at backing-store/traffic cost; LIVE reduces traffic but requires trustworthy prefix extents and safe points; CONTROL minimizes retained bytes but shifts correctness and latency to software reload. Priority versus round-robin changes selection policy but not state completeness. Wider context-store bandwidth lowers the analytical transfer term but implies unmodeled area/power/frequency cost.

## Predraft gate

Drafting is authorized only when the 39-hash/171-predicate/210-check source audit, focused mutation, field-complete transition surfaces, sweep recomputation, bounded static-link runs, sanitizer gate, optimization-safe validator, completed skeptical dispositions, exact retained inventory, finalization binding, and inner/outer manifests all pass for the final post-review seal. Any later bundled-input change requires another seal; older runs remain immutable history.
