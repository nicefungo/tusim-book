# Chapter 5 — State, Lifecycle, and Public APIs

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-5)

A host asks Tusim to copy eight bytes from its output SRAM, then reconfigures the model before issuing a single DMA tick. When initialization returns, the replacement SRAM contains zeros. What should the host see in its destination: the old bytes, zeros, or the sentinel it put there before submission?

At public simulator `7a094ff6c5527eff8e4318de676f0c0221c448b4`, a valid, accepted descriptor in this experiment copied the **old bytes**. The zeros belong to the next run. Reinitialization did not rewind the host process: it finished work that still referred to the old run, then replaced the resources it owned. This distinction matters whenever two architecture configurations run back to back in one process.

## 5.1 A vocabulary for C-model state

Chapter 4 followed a request into the active configuration. Here we follow pointers in the other direction: from an operation back to the owner that keeps its operands alive. Three questions guide the chapter: **Who may release this object? Until when may another object refer to it? Which observation would distinguish release from merely losing the pointer?**

| Object | Owner and lifetime | Consequence for the caller |
|---|---|---|
| W, A and O backing storage | The live TU state owns its regions. | A raw SRAM pointer is a view into *this* run. Obtain a new view after replacement. |
| Command queue | The state owns the queue; the queue owns command slots, their copied dependency lists and the signal registry. | A command can have executed while its record and dependency list still occupy storage. |
| Accepted linear descriptor | In the top-level drain path below, the global DMA engine holds references; the caller releases the completed descriptor. | Keep the descriptor and its external endpoints alive. Release after completion, not after submission. |
| Host destination | Caller-owned across the entire transfer. | Inspect it after reinit: it survives even when the old model does not. |
| Selected dataflow | The state holds a pointer to a registry-owned plug-in. | A per-core selection is not a private copy of plug-in state. |

Ownership is not isolation. An object can be private to one handle even though the routine that operates on it uses a shared global. Neither arrangement, on its own, establishes thread safety.

## 5.2 Source map

The useful starting point is not the word *reset* in an API name. Read the following paths at the edition commit, in call order:

1. `tu_cmodel/tu_cmodel.[ch]`: `tu_init()`, `tu_init_with_config()` and `tu_shutdown()` establish the top-level ownership boundary.
2. `tu_cmodel/dma_descriptor.c`: `tu_dma_submit_desc()`, `tu_dma_flush_channel()` and `tu_dma_destroy()` explain what happens to an accepted reference. `tu_cmodel/command_queue.c` implements a **different** queue, with a nested destructor.
3. `tu_cmodel/tu_asm.c`, `tu_core.c` and `tu_cluster.c` (the latter two also under `tu_cmodel/`): trace wrappers back to the state on which they execute.

## 5.3 The legacy singleton lifecycle

`g_tu` holds the direct model's architectural state and wrapper counters. The live descriptor engine is another global, `g_tu_dma`. For the valid, separately stored runtime configurations used here, `tu_init_with_config(&new_cfg)` follows this order:

```text
old g_tu and g_tu_dma live
    flush accepted descriptors against OLD SRAM and live host endpoints
    destroy the now-drained DMA engine
    destroy the old command queue, including its children
    destroy W/A/O; clear g_tu
    copy new_cfg; initialize new SRAM, DMA, command queue and selection
replacement marked initialized
```

The order is part of the result. Clearing the engine first would lose the pending reference. Replacing SRAM first would remove the data needed by the transfer. `tu_shutdown()` performs the teardown portion and may be called again after it has finished. It does not reset every process-global object; the dataflow registry, for example, has its own lifetime.

### A paired test in which the destination outlives the model

Start each arm in its own process, with a 4×8 weight-stationary configuration and one asynchronous descriptor channel. Put `32 43 54 65 76 87 98 a9` at O offset 16. Mark W and A as well, and submit two NOPs to the **synchronous command queue**, the second with a copied dependency on the first. Its depth and completion count are now both two. Thus *idle* below means **DMA idle**, not “the old state was pristine.”

In both arms the caller keeps a ten-byte array alive: a left guard `e1`, eight `cc` bytes and a right guard `e2`. Only in the pending arm, submit one linear O-to-host descriptor targeting the eight interior bytes. Check the returned ID, channel references and completion bit before replacement. There is no `tick`, explicit flush or `sync` between submission and the second initialization.

| Observable | DMA idle | One accepted pending descriptor |
|---|---|---|
| Just before reinit | Depth 0, no active descriptor; interior `cc` × 8 | Depth 1, no active descriptor, not completed; same sentinels |
| Same host array on return | `e1 cc cc cc cc cc cc cc cc e2` | `e1 32 43 54 65 76 87 98 a9 e2`; descriptor completed |
| Old queue ownership during replacement | Release observed for queue, slots, dependency copy and signals | Same four releases; no release of the caller's descriptor |
| Replacement before first use | 8×4, output-stationary, two empty DMA channels; W/A/O each 2 KiB and all zero | Identical |
| Replacement after first command | ID 1 completed; W bytes around offset 3: `00 de ad be ef 00` | Identical |

Two observations that look similar answer different questions. An empty **new** queue proves that old commands are not visible; it does not show that their memory was released. Here a link-time observer watched the four live queue allocations at the `free` boundary, dropped each watch before forwarding the call, and did not read the old queue after reinit. The completed descriptor remained caller-owned and was destroyed separately. Nothing in the argument depends on whether the allocator reused an address.

The fresh queue started with zero submitted and completed commands and next ID 1. Its first command loaded four new bytes into W; the guards there stayed zero, and the fresh wrapper byte count went from 0 to 4. Both explicit shutdown calls left the initialized flag clear, queue and backing pointers null, and the engine with zero channels. A cleared counter alone would have missed a destination left unchanged; a completed bit alone would have missed a copy from the wrong image.

### Drain is not cancellation

A **drain** lets accepted work take effect before the resources it references go away. A **cancellation** would require a contract for when work stops, which writes may already be visible, and how the caller learns its terminal status. A **rollback** would additionally have to undo visible writes. The pending arm excludes silent discard here: the old payload reached the host. It does not demonstrate cancellation, rollback, rejection of a busy reset, or a timed hardware reset handshake. The reconfiguration call returned only after the copy. No reset latency was measured.

## 5.4 Direct calls and command-queue calls

A direct call names operations on `g_tu`. A queued command copies scalar operands into a slot; host pointers in those operands still refer to caller storage. Execution dispatches back into the direct functions. The queue is not another independent tensor unit.

Separate four events: **submission** accepts a record; **execution** does the work; **completion** marks the result; **retirement** makes capacity reusable. The two old NOPs demonstrate completion without disappearance of the records. Destroying those records on reinit is not evidence that an arbitrary deferred command queue progresses or that its barriers order descriptor DMA. `tu_cmdq_sync()` returns immediately in synchronous mode. Do not substitute it for the specific descriptor flush in §5.3. Chapter 10 follows the descriptor path; command ordering belongs to Chapter 11.

## 5.5 ASM is a fresh-run wrapper

`tu_run_asm()` builds parser state for a program and borrows the supplied host-buffer entries. It calls `tu_init()` before reading instructions. Passing an empty program therefore does not mean “leave the model alone.” In v1's historical probe an empty ASM run through a core wrapper replaced the core's 4×8 configuration with the 16×16 default and erased its W marker. That number is not a new measurement; the v2 source still shows the reset inside the interpreter. Choose a run-oriented interface for a self-contained program, not for an operation that must preserve staged operands.

## 5.7 Cluster ownership and SPMD scope

A cluster owns its array of core pointers and destroys the cores it contains. Point-to-point communication can address their O regions directly. The cluster SPMD text wrapper instead iterates over those cores and calls the per-core ASM wrapper. One program applied to several snapshots is not evidence of simultaneous execution or a common hardware clock. Topology and communication cost are separate questions from storage ownership.

## Review questions

1. Why is the host array a better witness of the old run than a raw pointer into old O-SRAM?
2. Could a replacement pass the fresh-queue checks and still leak the old dependency list? Which observation distinguishes those outcomes?
3. Which pre-reinit checks rule out the explanation “the copy already happened at submit”?
4. Would changing the core's selected plug-in prove it owns the registry? Trace the selection and the object separately.

**Design exercise.** Specify a cancel-on-reset alternative. Give the caller a way to distinguish “never issued,” “completed,” and “may have written.” Decide when it may release its destination. Compare those obligations with the simpler rule measured here: keep accepted work and its endpoints alive until the drain returns.

[Next: Chapter 6 — PE Arrays, MMA Semantics, and Tiling](06-pe-arrays-mma-semantics-and-tiling.md)
