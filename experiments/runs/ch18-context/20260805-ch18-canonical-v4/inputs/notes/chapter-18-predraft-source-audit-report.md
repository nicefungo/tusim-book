# Chapter 18 — Predraft Source Audit Report

## Scope and authority

This report audits runtime context retention and preemption boundaries at Tusim pin `e918c80b6fce833cd1fcae97730fa841c2176f25`. It keeps descriptor lifecycle, retained core state, live command-queue state, embedded and process-global DMA, global rounding/PRNG, shared plugin objects, and manager-local switch accounting separate. No result is promoted to autonomous preemption, calibrated latency, fairness, or complete tenant isolation.

The framing split is already closed. Chapter 18 owns runtime retention/preemption; scheduler and liveness legality remain Chapter 19. Drafting remains blocked until a skeptical review is incorporated and a final post-review canonical bundle is sealed.

## Pin-locked source gate

`experiments/ch18_source_audit.py` pins 32 implementation, header, test, Makefile, config, and document hashes. It derives all 19 `tu_ctx_*` operations from the public header and enforces 147 structural, lifecycle, field-census, configuration, build, documentation, and whole-tree caller predicates: 179 checks total.

Expected authority lines:

```text
CH18_PUBLIC_APIS count=19 names=tu_ctx_alloc,tu_ctx_block_current,tu_ctx_free,tu_ctx_get,tu_ctx_get_switch_count,tu_ctx_get_switch_overhead,tu_ctx_manager_config_validate,tu_ctx_manager_create,tu_ctx_manager_destroy,tu_ctx_notify_command,tu_ctx_notify_cycles,tu_ctx_print_status,tu_ctx_request_switch,tu_ctx_restore,tu_ctx_save,tu_ctx_schedule_next,tu_ctx_slice_expired,tu_ctx_switch,tu_ctx_unblock
CH18_CALLERS external_nontest=none
CH18_SOURCE_AUDIT PASS pin=e918c80b6fce833cd1fcae97730fa841c2176f25 hashes=32 predicates=147 checks=179
```

The manager and sweep have Makefile rules and `tu_context.o` is an archive member, but neither context target is an aggregate `make test` prerequisite. Linkage and focused tests do not establish a production caller.

## Focused control and mutation

The canonical runner exports the exact pin into a disposable tree, builds only `libtucmodel.a`, statically links the focused suite and custom probe, and rejects a dynamic `libtucmodel` dependency. It requires:

- unmodified context suite: `15/15 tests passed`;
- a real focused assertion mutation: `14/15 tests passed` with nonzero inferior status;
- unmodified context sweep rows and bandwidth sensitivity;
- wrong-pin and source-hash mutations that fail closed;
- custom probe summary `failures=0`;
- validator source mutation rejected under normal Python and `python -O`.

The green focused suite remains bounded. It omits direct-restore double ownership, invalid-target non-atomicity, active/IDLE free defects, priority zero/ties, global DMA, queue retention, rounding/PRNG, plugin internals, and allocation-failure trajectories.

## Field-complete transition evidence

`experiments/ch18_context_probe.c` prints a deterministic before/after vector for each applicable lifecycle row. The vector records manager ownership/accounting, every descriptor's lifecycle/accounting/control fields, legacy core ledgers/runtime config, selected plugin counters, representative retained/tail bytes, aggregate and per-bank SRAM state, queue counters/content digest, embedded DMA, process-global DMA, and rounding mode. Dedicated rows add deterministic stochastic-PRNG and status/getter evidence.

The probe covers:

- config validation, manager creation, first allocation, exhaustion, invalid get;
- active/READY/BLOCKED/IDLE free and slot reuse implications;
- manual save, direct restore with and without a prior save, self switch, invalid/IDLE/BLOCKED targets, and immediate request-switch;
- round-robin, equal positive-priority ties, priority-zero starvation, exact slice thresholds, notifications without an ACTIVE owner, block, and all relevant unblock states;
- injected first/second/third SRAM-copy failures and destructive re-save failure;
- FULL/LIVE/CONTROL retained-byte and cost behavior with intentionally stale tails;
- queue non-restoration, global pending DMA survival versus embedded DMA restore, global rounding/PRNG continuation, shared plugin mutable state, aggregate/per-bank split, dropped double-buffer ownership, and dead controls.

The discriminating outcomes include:

- direct restore while context 0 is ACTIVE produces two ACTIVE descriptors;
- invalid, IDLE, and BLOCKED switch targets return failure only after demoting the outgoing owner, leaving zero ACTIVE descriptors and `pending_save_bytes=192` in the bounded 64-byte-per-region setup;
- freeing IDLE slot 3 changes `active_count 1→0` while context 0 remains ACTIVE;
- priority ties select slot 1, while two READY priority-zero contexts produce `-1`;
- LIVE restores byte 0 but leaves byte 8 from the intervening context; CONTROL restores neither;
- manager cost is 10 cycles per LIVE switch in the bounded setup (`7 + ceil(24/8)`) and 7 per CONTROL switch;
- the pending global descriptor remains queued while target embedded DMA resets to its independent snapshot;
- aggregate W reads/cycle restore `21/22→11/12`, while per-bank sentinels remain `words=2, reads=23`;
- stochastic outputs continue across a switch exactly as the unswitched seed-123 sequence, and the post-switch global rounding mode remains RTZ;
- injected initial-copy failures clean up, but an injected re-save failure destroys the previous retained buffers without rollback.

## Retained-state and cost boundary

The source-defined switch ledger is:

```text
fixed_control_cost
+ ceil((outgoing_saved_bytes + incoming_saved_bytes)
       / state_bytes_per_cycle)
```

It updates only `total_cycles_stolen`. It does not advance core `estimated_cycles`, command-queue `current_cycle`, global DMA `current_cycle`, SRAM-bank time, or Chapter 17 producers. The context sweep's 256-KiB rows (`16484`, `4196`, `100`) are exact model values, not host measurements or calibrated hardware latency.

FULL deep-copies all three regions. LIVE deep-copies caller-declared prefixes and deliberately leaves stale tails. CONTROL copies no SRAM. Save/restore copies aggregate bank metadata but not `bw_banks`, drops double-buffer state, keeps the live command queue, copies the embedded `tu_state_t.dma` rather than operative `g_tu_dma`, restores a shared plugin pointer rather than plugin internals, and does not own global rounding/PRNG.

## Drafting boundary

The chapter may compare transparent bulk retention, compiler/runtime-declared live-prefix retention, and software-reload control-only switching. Every alternative must name its safe-point contract, retained bytes, omitted state, cost owner, and verification burden. It may not claim arbitrary preemption, automatic scheduling, complete command/DMA/precision isolation, fairness, calibrated QoS, or lowest area/power/latency from the current model.
