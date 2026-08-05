# Chapter 16 — Predraft Source Audit Report

**Edition pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`  
**Evidence class:** pinned-source executable and analytical audit  
**Status:** provisional until canonical retained run and skeptical review close

## 1. Audit question

Can Chapter 16 explain legal overlap without presenting standalone ping-pong SRAM state, descriptor DMA, and the pipeline controller as one validated ordinary execution path?

The initial answer is **yes only if the chapter centers swap legality and producer identity**. The source contains a bridge candidate, but its byte behavior rejects the intended fresh-shadow interpretation.

## 2. Standalone state machine

The equal-sized shadow allocation and index-driven pointer selection are executable. Generic SRAM read/write/bulk/raw-pointer APIs follow the active pointer. However:

- a clean swap is accepted and makes zero-initialized shadow bytes active;
- `shadow_dirty` is cleared by every swap but is not a precondition;
- getting or writing the shadow pointer does not itself mark dirty;
- notification changes only caller-supplied ledgers and accepts byte counts larger than capacity;
- active and shadow allocations share one bank-meter/cycle/counter state;
- disable preserves index-1 active data by copying it to primary, while destroy frees both allocations.

Thus `shadow_dirty` is neither a valid bit nor a completion token. A legal protocol must be imposed by a caller and verified separately.

## 3. Descriptor and pipeline bridge

The controller attempts to redirect a host-to-TU descriptor by setting both `dst_region` and `dst_host=shadow`. Descriptor execution gives precedence to the non-null region and resolves it through `tu_sram_raw_ptr()`, which is the current active role. On completion the controller swaps and only then notifies the new shadow.

The bounded local probe reproduced the exact result for primary `0x11`, shadow `0x22`, and source `0x7a`:

```text
PIPE_BEFORE tid=0 stage=1 active=11 shadow=22 dst_region=1 dst_host_shadow=1 pipe_cycle=0 dma_cycle=0
PIPE_AFTER stage=2 completed=1 desc_cycles=53 pipe_cycle=0 dma_cycle=1 active=22 shadow=7a swapped=1 dirty=1
```

Fresh DMA bytes landed in the old active allocation and became shadow; stale `0x22` became active. This is an executable negative bridge, not valid overlap.

`cmd_id` is stored but never dispatched. Compute is represented only by a caller-provided cycle deadline. The controller's load/store overlap fields are analytical credits based on descriptor bytes and active-count conditions; its cycle, DMA cycle, descriptor cycle estimate, SRAM cycle, and manually recorded double-buffer overlap are separate.

## 4. Lifecycle and reachability

- Double buffering is API-only: JSON/YAML/runtime conversion has no selector for enabled regions.
- The hierarchy's `double_buffered` field is declared/defaulted but does not call the standalone enable API.
- Context save/restore explicitly drops every `db` pointer and does not preserve shadow bytes, index, dirty state, swaps, or ledgers.
- `double_buffer.o` and `pipeline_controller.o` are archive members.
- `test-double` is `.PHONY`/clean-only: no Makefile recipe and no aggregate membership. Direct static compilation yields 10/10.
- `test-pipeline` has a rule and aggregate membership, but its four-channel setup exceeds the fixed three-entry DMA channel array. It is retained as source evidence and is not executed; the one-channel bounded probe replaces only the Chapter 16 claim surface, not the whole suite.
- The pipeline implementation is the only non-test `tu_cmodel` caller of double-buffer mutation APIs; no non-test `tu_cmodel` caller invokes the pipeline public API.

## 5. Historical analytical report recomputation

For `M=N=128`, `K=256`, 16x16 PEs, depth 2, 32 B/cycle, and the report's ideal independent-port overlap equation, all table rows recompute exactly:

| O role capacity | M chunks | Sequential | Ideal overlap | Ideal DB total | Recomputed TOPS | Ideal speedup |
|---:|---|---:|---:|---:|---:|---:|
| 16 KiB | 32/32/32/32 | 28,752 | 9,216 | 19,536 | 0.429 | 1.472x |
| 24 KiB | 48/48/32 | 26,688 | 6,912 | 19,776 | 0.424 | 1.350x |
| 32–56 KiB | two chunks | 24,624 | 4,096 | 20,528 | 0.409 | 1.200x |
| >=64 KiB | one chunk | 22,560 | 0 | 22,560 | 0.372 | 1.000x |

The arithmetic is internally consistent, but several conclusions exceed it:

1. A 16 KiB **role** uses 32 KiB of physical data allocation when doubled. Relative to a 64 KiB single buffer, the physical O-buffer saving is 2x, not 4x. Any W/A shadow allocations must be added when the schedule requires them.
2. The 15.3% ideal throughput comparison is one workload/formula result, not executable pipeline behavior or a universal compiler rule.
3. The “512 bytes/cycle” claim is dimensionally inconsistent with its own premise of 256 PEs x two FP16 operands: independent per-PE reads would be 1,024 B/cycle. A systolic boundary-injection/reuse model would produce a different count and must be derived explicitly.
4. The ~3% banking-area statement has no pinned physical source or calibration.
5. “always beneficial,” “single highest-leverage,” and ONNX compiler recommendations are rejected at this edition.

## 6. Architecture alternatives and regimes

| Alternative | Useful regime | Potential gain | Capacity/area/energy cost | Control and verification burden |
|---|---|---|---|---|
| Single buffer | capacity-bound workloads; no legal concurrent producer | maximum usable working set per byte; simplest path | no duplicate data array | serialize preload/compute; minimal ownership proof |
| Equal ping-pong | repeated similarly sized tiles with a producer completion protocol and independent access resources | can hide up to `min(D,C)` after startup and before drain | 2x data allocation per buffered region; extra leakage/dynamic traffic | active/shadow ownership, valid/completion event, swap ordering, reset/context state |
| Bank/partition schedule | workloads whose current and next tiles map to disjoint banks/ports | partial overlap without duplicating full capacity | banking/port logic and fragmentation | mapping/arbitration proof and conflict-sensitive tests |
| Triple/ring | variable producer/consumer latency or deeper queues | more slack and reduced bubbles | >=3x slots or partitioned capacity | head/tail generations, reclamation, backpressure, reset |
| Event/queue-backed integrated pipeline | system-level timing and correctness questions | explicit legal completion and composable schedule | controller, queues/events, metadata, possible buffering | largest state space; failure, cancellation, ownership, and clock-domain verification |

No alternative is universally fastest. The selected design depends on working-set fit, `D/C` balance, ports/banks, startup/tail fraction, area/energy budget, and the strength of the completion protocol.

## 7. Required seal gates

The canonical bundle must retain source hashes, source predicates, archive membership, direct 10/10 focused test, a failing focused mutation, exact bounded-probe lines, GDB inferior-exit evidence, recomputation output, static linkage, source/book pre/post provenance, and exact manifests. Skeptical review must independently hand-derive the state/ledger lines and audit every blanket lifecycle/integration claim before drafting.
