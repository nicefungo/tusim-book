# Chapter 16 — Source and Claim Ledger

**Title:** Double Buffering and Legal Overlap  
**Edition pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25` (read-only)  
**Status vocabulary:** verified / qualified / rejected / blocked  
**Predraft status:** provisional; claims require canonical seal plus skeptical review.

## Standalone ownership and lifecycle

- **C16.1 (verified):** `tu_sram_enable_double_buffer()` allocates one zeroed shadow allocation equal to `r->total_size`, starts with primary active (`active_idx=0`), and doubles allocated data bytes while leaving each active role's usable capacity unchanged (`double_buffer.c:17-50`).
- **C16.2 (qualified):** enable is idempotent only when `r->db && enabled`; it checks non-null region and nonzero `total_size` but does not require an initialized primary allocation. The documented call-order precondition (after `tu_sram_init`) is not enforced.
- **C16.3 (verified):** active/shadow identity is index-driven: active is primary at index 0 and shadow allocation at index 1; shadow is always the opposite pointer (`double_buffer.c:70-95`). Generic SRAM read/write/bulk/raw-pointer paths route bytes through the current active pointer (`tu_sram.c:138-209`).
- **C16.4 (rejected):** swaps are not legality-checked. `tu_sram_swap_buffers()` toggles `active_idx`, increments `swap_count`, and clears `shadow_dirty` without requiring dirty/fresh/complete bytes. A clean initial shadow can become active.
- **C16.5 (qualified):** `shadow_dirty` is caller-supplied notification state, not a valid bit, freshness proof, byte-count bound, descriptor binding, or completion token. `tu_sram_get_shadow_ptr()` does not mark dirty despite the header claim; only `tu_sram_notify_shadow_write()` does. Swap legality must be imposed and verified by a caller.
- **C16.6 (verified):** notification and overlap APIs are additive manual ledgers: bytes, DMA cycles, and overlap cycles are accepted from the caller and persist across swaps; no clock or byte effect is derived from them (`double_buffer.c:97-155`).
- **C16.7 (verified):** disabling preserves the currently active bytes by copying shadow to primary only when index 1 is active, then frees state; when primary is active it discards shadow. Direct SRAM destroy frees both allocations and all double-buffer state (`double_buffer.c:53-64`, `tu_sram.c:85-94`).
- **C16.8 (qualified):** active and shadow bytes are distinct, but bank meters, read/write counters, refill cycle, and stall state live once in `r->banks` and follow whichever role is active. The model does not represent independent per-buffer ports/banks merely because two allocations exist.

## Descriptor DMA and bridge candidate

- **C16.9 (verified):** ordinary host-to-TU descriptor execution resolves `dst_region` through `tu_sram_raw_ptr(dst_region) + dst_base`; `dst_host` is used only when `dst_region` is null (`dma_descriptor.c:446-463`). Descriptor DMA therefore targets the currently active region by default, not the shadow role.
- **C16.10 (verified):** the pipeline controller is a real source-level caller of double-buffer and descriptor APIs, but no non-test library caller invokes the pipeline controller itself. This establishes a standalone bridge implementation, not ordinary-operation reachability.
- **C16.11 (rejected pending canonical reproduction):** the controller's attempted host-to-TU redirect sets `load_desc->dst_region = buffer_region` and also sets `dst_host = shadow`; descriptor execution prioritizes the non-null region, writes the current active buffer, then the controller swaps. The intended fresh bytes become the new shadow and stale bytes become active. This is not valid DMA-to-shadow overlap.
- **C16.12 (qualified):** on preload completion the controller swaps first and then calls `tu_sram_notify_shadow_write()`. The dirty mark therefore applies to the post-swap shadow (old active), not the newly active stale buffer; dirty state cannot repair the byte-visibility defect.
- **C16.13 (qualified):** descriptor `completed` is an executor outcome and the controller advances on it; descriptor `cycles_completed`, `g_tu_dma.current_cycle`, controller `current_cycle`, SRAM bank cycle, and manually supplied double-buffer cycles are distinct quantities and clocks.

## Pipeline-controller semantics

- **C16.14 (verified):** slots follow IDLE/DMA_PRELOAD/COMPUTE/DMA_STORE/DONE and depth clamps to 1..8. The controller owns a caller-advanced `current_cycle` and invokes `tu_dma_tick()` once per advance (`pipeline_controller.c`).
- **C16.15 (rejected):** `cmd_id` is stored in a tile but never submitted to or queried from the command queue. The COMPUTE stage is a deadline (`cycle_expected = current_cycle + compute_cycles`), not execution of an operator or command.
- **C16.16 (qualified):** overlap values are analytical ledger credits. `overlapped_load_cycles` is credited from `total_bytes / 32` when `active_count >= 2`, independent of actual simultaneous compute byte effects; store credit follows a similar active-count condition. `tu_sram_record_overlapped_cycles()` is never called by the controller.
- **C16.17 (qualified):** the sequential ledger uses floor division by 32 for descriptor bytes and defaults each absent load/store to one cycle. The pipeline total is total compute plus non-overlapped ledgers; it is not `g_tu_pipeline.current_cycle`, a queued completion time, or a calibrated latency.
- **C16.17a (rejected):** reported controller speedup is not proof of overlap. A depth-1, three-cycle compute-only tile reports sequential 5, pipelined 3, speedup `1.666667x` while both overlap credits and saved cycles are zero; the baseline alone charges absent DMA operations. A depth-2, five-cycle first tile that starts directly in COMPUTE skips `total_compute_cycles`, yielding sequential 7, pipelined 0, and infinite speedup. The one-load probe similarly reports 8/7 (`1.142857x`) with `saved=0`.
- **C16.18 (verified):** `tu_pipeline_reset()` destroys/flushed state and saves depth/config but does not call init or reallocate slots; after reset the controller is uninitialized/idle. The test's idle/counter assertions do not prove continued usability.
- **C16.19 (qualified):** the unmodified pipeline suite is unsafe evidence at the pin because `setup_dma()` requests four channels while descriptor-engine fixed storage has three entries (Chapter 10 established this boundary). It is aggregate-listed, but Chapter 16 must use a bounded one-channel probe instead of executing it.

## Configuration, context, and reachability

- **C16.20 (verified):** standalone double buffering is API-only at the pin: no JSON/YAML/runtime field selects regions or enables the state. The PE `pipeline_depth` setting is a different concept and must not be treated as controller depth.
- **C16.21 (qualified):** `tu_mem_level_config_t.double_buffered` is declared and defaults local SPAD true, but hierarchy construction does not consume it to call `tu_sram_enable_double_buffer()`. It is decorative for this state machine.
- **C16.22 (rejected):** context save/restore is incompatible with a live double-buffer owner. Save retains only scoped primary bytes. Restore overwrites the live `db` pointer with `NULL` without freeing it, leaking shadow/state allocations and discarding active role, shadow bytes, dirty state, swaps, and ledgers. Context switching is not an integration bridge.
- **C16.23 (verified):** both `double_buffer.o` and `pipeline_controller.o` are `TU_OBJS` archive members. `test-pipeline` has a recipe and is in aggregate `make test`; `test-double` appears in `.PHONY`/clean only, has no recipe, and is absent from aggregate `test`. Chapter 16 compiles the double-buffer suite directly.

## Documents, reports, and trade-offs

- **C16.24 (rejected):** `docs/TU_DOUBLE_BUFFER.md` and `docs/software-pipelining.md` describe valid DMA/compute integration, command-queue orchestration, and hardware overlap as if established. Pinned execution does not support those blanket claims; the documents are historical intent/analytical explanation where they exceed source behavior.
- **C16.25 (qualified):** `double-buffer-mtiling-recovery.md` is an ideal analytical model using independent SRAM ports/shadow allocations and source-formula cycles. Its rows may support arithmetic under those assumptions after recomputation, not executable or calibrated speedup.
- **C16.26 (qualified):** the report's equal-size double-buffer model carries a 2x data-allocation cost for each buffered region. Claims that a 16 KiB O-buffer saves SRAM must compare physical allocation (32 KiB when doubled) against the chosen 64 KiB single-buffer alternative and include any W/A buffering required by the overlap schedule.
- **C16.27 (rejected pending recomputation):** general recommendations such as “single highest-leverage,” “always beneficial,” fixed ~3% banking-area cost, and compiler preference are not established by one analytical workload, no calibrated port/contention model, and a broken compiler path.
- **C16.28 (qualified):** meaningful alternatives are regime-specific: (a) single buffer—maximum usable capacity per byte and simplest ownership, no same-region preload/compute overlap; (b) equal ping-pong—simple role swap and potential hiding, 2x allocation plus validity/control burden; (c) bank/partition scheduling—potential partial overlap with less duplication, greater arbitration/mapping proof; (d) triple/ring buffering—more queue slack, still more capacity/state/reclamation; (e) event/queue-backed integration—strong completion legality, highest control and verification cost.
- **C16.28a (rejected):** the report's stated `m_tile >= 20` threshold does not follow from its tile-dependent equation. Continuous algebra gives `18.285714...`; ceiling-aware systolic timing first passes at `m=17` because compute jumps at the 16-row boundary.
- **C16.28b (qualified):** pipeline configuration is only partly behavioral. Load/store overlap flags are read; `enable_triple_overlap` and `tile_timeout_cycles` are not consumed, `cmd_id` is stored but never dispatched, and `model_stalls` guards manual overlap credit rather than a modeled wait.
- **C16.28c (rejected):** a depth-1 tile with no load descriptor still enters PRELOAD and swaps an enabled region on the first advance, exposing unwritten shadow bytes and marking the opposite role dirty.
- **C16.28d (qualified):** the scheduler's “double-buffered tile pipeline” test is a separate instruction-order/address-range model. It calls neither the standalone double-buffer API nor the pipeline controller and is not an integration bridge.

## Required canonical evidence and closure status

- **C16.29 (blocked):** exact standalone transition and bridge byte observations require the Chapter 16 focused probe and immutable retained run.
- **C16.30 (blocked):** source-hash, archive membership, static-link, focused-test mutation, config/caller/lifecycle predicates, and repository-provenance gates require the fail-closed audit.
- **C16.31 (blocked):** report equations/conclusions require independent recomputation and explicit assumption guards.
- **C16.32 (blocked):** drafting remains prohibited until a skeptical reviewer hand-recomputes the probe and closes integration, lifecycle, arithmetic, and audit-coverage challenges against a post-review canonical seal.
