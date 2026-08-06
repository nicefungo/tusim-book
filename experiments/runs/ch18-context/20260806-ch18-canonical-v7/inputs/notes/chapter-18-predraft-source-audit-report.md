# Chapter 18 — Predraft Source Audit Report

## Scope and authority

This report audits runtime context retention and preemption boundaries at Tusim pin `e918c80b6fce833cd1fcae97730fa841c2176f25`. It separates descriptor lifecycle, retained core state, the live command queue, embedded and process-global DMA, outer-core/DRAM ownership, global precision controls, shared plugin objects, and manager-local accounting. No result is promoted to arbitrary preemption, calibrated latency, fairness, or complete tenant isolation.

The framing split is closed: Chapter 18 owns runtime retention and preemption; compiler scheduling and liveness legality remain Chapter 19. Drafting gate is open only for a committed post-review bundle that passes this report's canonical validator in normal and optimized Python and whose inner and outer manifests verify.

## Pin-locked source gate

`experiments/ch18_source_audit.py` pins **39 implementation**, header, test, Makefile, config, and document hashes. It derives all 19 `tu_ctx_*` operations from the public header and enforces **171 structural** predicates and **210 checks** covering lifecycle, state fields, configuration, build provenance, documentation drift, and callers.

```text
CH18_PUBLIC_APIS count=19 names=tu_ctx_alloc,tu_ctx_block_current,tu_ctx_free,tu_ctx_get,tu_ctx_get_switch_count,tu_ctx_get_switch_overhead,tu_ctx_manager_config_validate,tu_ctx_manager_create,tu_ctx_manager_destroy,tu_ctx_notify_command,tu_ctx_notify_cycles,tu_ctx_print_status,tu_ctx_request_switch,tu_ctx_restore,tu_ctx_save,tu_ctx_schedule_next,tu_ctx_slice_expired,tu_ctx_switch,tu_ctx_unblock
CH18_CALLERS external_nontest=none
CH18_SOURCE_AUDIT PASS pin=e918c80b6fce833cd1fcae97730fa841c2176f25 hashes=39 predicates=171 checks=210
```

The context manager and sweep have focused Makefile rules and `tu_context.o` is archived, but neither target is an aggregate `make test` prerequisite. No production caller exists at the pin.

## Executable gate

The canonical runner exports the exact pin into a disposable tree, builds `libtucmodel.a`, and statically links the focused suite, mutation, sweep, and three probe variants. Every executable is bounded by a timeout. It retains stderr instead of discarding diagnostics and requires:

- focused suite `15/15`;
- real focused assertion mutation `14/15` with nonzero status;
- all 12 sweep rows;
- wrong-pin and source-hash mutations that fail closed;
- probe `failures=0`;
- byte-identical output when only the probe translation unit is built at O0 and O2;
- a leak-clean ASan/UBSan probe execution;
- validator AST mutation rejected under normal Python and `python -O`.

The O0/O2 marker is intentionally narrow: the pinned archive is built once. It does not claim whole-library optimization or cross-compiler invariance.

## Field-complete transition evidence

Every applicable transition row has deterministic PRE/POST records. The primary `ROW` vector records the complete manager ownership/accounting tuple and all descriptor lifecycle/accounting/control fields. Companion `SURFACE` records include:

- all bytes and aggregate metadata for W, A, and O;
- every member of every instantiated per-bank bandwidth record;
- all runtime-config fields;
- all queue scalar fields, full command/dependency and signal registries, nested-state digest, and stable pointer-presence/equality classifications;
- embedded and process-global DMA summaries;
- complete config-override byte digests, saved W/A/O ownership, saved queue/dataflow pointer relationships;
- five legacy core ledgers, core clock, selected plugin/public mutable counters, rounding and subnormal modes, and outer-core identity/ICC ownership.

Opaque plugin `impl_data`, process-global PRNG internals, error mode, independently caller-owned DRAM, and raw pointer addresses are structurally classified rather than dereferenced or printed as unstable addresses. The stochastic PRNG is tested with a deterministic continuation discriminator. Queue non-restoration uses an intentionally fabricated but memory-safe sentinel image; it proves copying behavior, not legal asynchronous drainage. `tu_core_sync()` calls queue synchronization only: synchronous queues return immediately; asynchronous queues can loop without timeout; neither path flushes process-global descriptor DMA.

The transition set covers NULL APIs; rejected configurations; allocation, cloning, exhaustion, and invalid get; ACTIVE/READY/BLOCKED/COMPLETED/IDLE frees and slot reuse; save/direct restore; direct restore while another descriptor is ACTIVE; self, invalid, IDLE, BLOCKED, and already-ACTIVE switch targets; immediate request-switch; round-robin; repeated equal-priority ties; priority zero; under/exact/over slice thresholds and counter wrap; notification without an owner; block; unblock in ACTIVE/BLOCKED/READY/IDLE/COMPLETED/invalid states; first/second/third retained-copy failures; destructive re-save failure; all three save scopes; zero transfer bandwidth; core/runtime retention; cycle underflow; queue/DMA/plugin/precision/global boundaries; and dead controls.

Key outcomes include:

- direct restore can create two ACTIVE descriptors;
- rejected switches are not failure-atomic, and the already-ACTIVE case can leave `active_ctx_id` inconsistent with the remaining ACTIVE descriptor;
- ACTIVE free leaves no owner; IDLE free corrupts `active_count`; reuse does not restore ownership;
- allocation clones the current shared core image, while the first descriptor's zero cycle baseline attributes pre-allocation core history on first save;
- priority ties repeat the lowest slot; priority-zero READY descriptors are unschedulable;
- command/cycle counters accept under, exact, and over thresholds but wrap to zero at their type limits, potentially clearing expiry;
- LIVE restores prefixes and leaves stale tails; CONTROL restores no bytes;
- zero `state_bytes_per_cycle` suppresses rather than rejects transfer cost;
- queue state and global DMA survive globally rather than being restored per context;
- rounding, stochastic PRNG, subnormal mode, and error mode are process-global;
- injected initial-copy failures clean up, but re-save failure destroys the prior snapshot without rollback.

## Retained-state and ownership boundary

The switch ledger is:

```text
fixed_control_cost
+ ceil((outgoing_saved_bytes + incoming_saved_bytes)
       / state_bytes_per_cycle)
```

It updates only manager `total_cycles_stolen`. It does not advance core, queue, DMA, SRAM-bank, or Chapter 17 clocks. The 256-KiB sweep rows `16484`, `4196`, and `100` are exact model values, not host measurements.

Save/restore copies selected `tu_state_t` state, not complete machine ownership. `core_id`, outer initialization, ICC buffers, and independently created DRAM models are outside the descriptor. The operative `g_tu_dma`, plugin registry and `impl_data`, rounding/PRNG/subnormal/error controls, and queue remain shared. Double-buffer restore nulls live pointers without serializing or freeing the displaced object: ownership and active-role identity are lost and the live allocation can leak, as Chapter 16 established.

The source audit verifies that SRAM save and restore both carry region `total_size` together with explicit aggregate bank fields and region names. The retained image still is not a transparent whole-object snapshot: saved `bw_banks` is deliberately dropped, so live per-bank arbitration state remains outside the descriptor even while region and aggregate metadata are restored.

## Drafting boundary

Chapter 18 may compare FULL, LIVE-prefix, and CONTROL-only alternatives only with explicit safe-point, ownership, retained-byte, omitted-state, cost, and verification contracts. It may not claim arbitrary preemption, automatic scheduling, complete queue/DMA/precision isolation, fairness, calibrated QoS, or universal performance/area superiority.
