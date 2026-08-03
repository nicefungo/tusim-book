# Chapter 5 — State, Lifecycle, and Public APIs

> **Edition scope.** This chapter describes Tusim at commit `e918c80b6fce833cd1fcae97730fa841c2176f25`. “Public” means declared in a shipped header; it does not by itself mean thread-safe, instance-pure, failure-atomic, or stable across future releases.
>
> **Status.** Ownership/lifecycle audit, focused execution, discriminating probe, independent skeptical review, and leak-sanitizer reproduction are complete for this first-draft chapter.

## Learning objectives

After this chapter, you should be able to:

1. distinguish process-global, instance-owned, registry-owned, caller-owned, and borrowed state;
2. trace initialization, reinitialization, execution, reset, and destruction paths without assuming that similarly named APIs share one lifecycle;
3. choose among the direct, command-queue, ASM, core, and cluster surfaces for a stated execution regime;
4. explain why `tu_core_t` gives useful SRAM isolation without making the whole library reentrant;
5. separate error detection, error recording, error propagation, and recovery;
6. design tests that distinguish a wrapper around global state from an independently owned instance.

## Prerequisite graph

```text
Chapter 3: build and direct execution
              |
              v
Chapter 4: requested config -> active state
              |
              v
C object lifetime -> ownership -> lifecycle state machine
              |                         |
              v                         v
API layering -----------------> errors and concurrency
              |
              v
Chapter 6: MMA semantics and tiling
Chapter 12: multicore clusters, compatibility-state swaps, and interconnect heuristics
```

## Opening architecture question: what does an API handle own?

Suppose a compiler runtime wants two independent tensor-unit models in one process. It creates two `tu_core_t *` handles, loads different weights into each, and observes different SRAM contents. Is the library now multi-instance?

Not necessarily. A handle can own some resources while still borrowing a process-global executor. That distinction affects parallel simulation, fault containment, reproducibility, and the meaning of counters. The decisive questions are not “Is there a struct?” or “Did the two-buffer test pass?” They are:

- Which allocations are reachable only through this handle?
- Which mutable objects are shared by all handles?
- Does every operation take the handle explicitly, or does a wrapper swap it into a global?
- Can constructing one handle invalidate another API mode?
- Who destroys every allocation, and when?
- Where can an error travel after it is detected?

The live audit in this chapter finds three overlapping ownership domains in Tusim: the legacy singleton `g_tu`, heap-allocated `tu_core_t` snapshots, and `tu_cluster_t` collections. These are useful interfaces, but they are not interchangeable concurrency contracts.

## 5.1 A vocabulary for C-model state

An accelerator C model typically contains several kinds of state:

- **Architectural state:** SRAM contents, register-like control settings, active dataflow, queue contents, and completion state.
- **Accounting state:** bytes, operations, tiles, estimated cycles, stalls, traces, and errors.
- **Control state:** initialized flags, queue heads, parser cursors, plugin registries, and logging modes.
- **External references:** host buffers, callbacks, filenames, and configuration objects supplied by the caller.

Ownership answers who must release a resource. Lifetime answers how long a pointer remains valid. Isolation answers whether one instance's operation can mutate another instance's state. Thread safety answers whether concurrent calls have defined synchronization and race-free results. None of these properties implies the others.

For this chapter, use five labels:

| Label | Meaning | Typical obligation |
|---|---|---|
| process-global | one mutable object for the process | serialize access; define global shutdown |
| instance-owned | allocation is reached and destroyed through one handle | destroy exactly once after all users stop |
| registry-owned | stable shared object managed by a registry | handles borrow; registry outlives borrowers |
| caller-owned | library never frees the object | caller preserves it for the documented interval |
| borrowed view | pointer aliases another owner's storage | invalid after owner reset or destruction |

A pointer field is not proof of ownership. `tu_state_t.cmdq` points to a heap queue and is intended to own it, while `tu_state_t.dataflow` points to a plugin owned by the global registry. `tu_host_buffer_t.data` is caller-owned and borrowed by the ASM interpreter. These three pointers require three different cleanup rules.

## 5.2 Source map

The material ownership paths are concentrated in:

| Surface | Primary source at `e918c80` | Role |
|---|---|---|
| legacy singleton | `tu_cmodel/tu_cmodel.[ch]` | `g_tu`, direct DMA/MMA, config init, queue wrappers |
| command queue | `tu_cmodel/command_queue.[ch]` | command descriptors, dependencies, completion and drain |
| ASM | `tu_cmodel/tu_asm.c` | parser-local weights and borrowed host buffers |
| core wrapper | `tu_cmodel/tu_core.[ch]` | heap handle containing a copied `tu_state_t` |
| cluster wrapper | `tu_cmodel/tu_cluster.[ch]` | owns core-pointer array and cores |
| DMA engine | `tu_cmodel/dma_descriptor.[ch]` | separate process-global `g_tu_dma` |
| dataflow registry | `tu_cmodel/compute/dataflow/dataflow_registry.[ch]` | process-global plugin ownership |
| status | `tu_cmodel/tu_status.[ch]` | process-global mode, last error, injection sites |

The executable record is preserved in [`experiments/ch05-ownership-lifecycle-audit-2026-07-25.md`](../../experiments/ch05-ownership-lifecycle-audit-2026-07-25.md), with probe source in [`experiments/ch05_lifecycle_probe.c`](../../experiments/ch05_lifecycle_probe.c).

## 5.3 The legacy singleton lifecycle

`g_tu` is defined as a zero-initialized `tu_state_t`. `tu_init()` obtains compile-time-derived runtime defaults and forwards to `tu_init_with_config()`. File and full-config initialization eventually converge on the same function.

The intended transition is:

```text
zero state --tu_init*--> initialized state --tu_init*--> replacement initialized state
```

The implementation's actual resource transition is narrower:

```text
if initialized:
    destroy W/A/O SRAM
memset entire g_tu to zero
copy runtime config
allocate W/A/O SRAM
initialize process-global DMA
allocate a command queue
register/select shared dataflow plugins
mark initialized
```

This path resets architectural contents and counters, so repeated initialization appears successful in functional tests. It does not destroy the previous command queue before erasing its pointer. There is also no `tu_shutdown()` in the public legacy API. Process exit reclaims memory, but an embedded simulator that repeatedly reconfigures the model has a different lifecycle requirement from a short command-line test.

Initialization is also not failure-atomic. `tu_sram_init()` and `tu_cmdq_create()` allocate memory, but `tu_init_with_config()` returns `void` and does not check allocation results before setting `initialized=true`. A production alternative would build a temporary state, validate every allocation, and publish it only after complete success.

### Trade-off: singleton simplicity versus embeddability

| Design | Advantage | Cost |
|---|---|---|
| process-global singleton | smallest call signatures; easy generated C | one active model; difficult teardown and concurrency |
| opaque heap handle | explicit ownership; multiple configurations | API migration and handle plumbing |
| caller-provided state | deterministic allocation policy | larger ABI and more initialization burden |

For a single-threaded compiler demonstration, the singleton is convenient. For a simulator service running many jobs, explicit handles and complete destruction are the safer regime.

## 5.4 Direct calls and command-queue calls

The direct API mutates `g_tu`: loads and stores access its SRAM regions, `tu_mma()` updates its counters, and `tu_sync()` drains the global DMA engine. The queue convenience API does not introduce a second execution domain. It stores descriptors in `g_tu.cmdq`, and `execute_command()` calls the same global direct functions.

Command descriptors copy scalar fields but retain raw host pointers. In synchronous mode, execution occurs during submission, so the host pointer need only survive the call. In asynchronous mode, it must remain valid until execution and completion. The public wrappers do not encode that lifetime in the type system.

The queue's documentation describes `count` as commands “in flight.” At the pinned commit, completion and retirement diverge in both modes. Synchronous submission executes without freeing capacity; asynchronous execution also fails to decrement because `tu_cmdq_tick()` guards retirement with `if (cq->synchronous)`. The probe therefore observes status `2` (`COMPLETED`) with depth `1`. Because `tu_cmdq_sync()` loops while `count > 0`, invoking it on this state would not terminate. The focused 9/9 suite uses the synchronous default and codifies eventual saturation as its overflow behavior rather than testing capacity reuse.

Other contracts drift too: generic submit is documented to return zero but returns the positive command ID; wait documents `-2` for an unknown ID while implementation treats unknown or retired IDs as successful completion; status lookup likewise maps unknown IDs to `COMPLETED`. A low-level fault reported by a void direct API does not make the queue command `FAULTED`. Queue metadata can be independently allocated, but its executor still targets global `g_tu`.

This is a general verification lesson: a state machine needs assertions on transitions, not only final numerical output.

```text
PENDING -> ISSUED -> COMPLETED -> RETIRED
                         |            |
                         |            +-- frees queue capacity
                         +-- result is available
```

Treating `COMPLETED` and `RETIRED` as synonyms can make a queue appear correct until it saturates or a drain waits forever.

## 5.5 ASM is a fresh-run wrapper

`tu_run_asm()` creates parser state on the stack. Embedded weight bytes are allocated while parsing and freed on success or failure. Host buffer entries are borrowed for the call. This is a clear local ownership story.

Its architectural lifecycle is more surprising: `tu_run_asm()` calls `tu_init()` before interpreting any instruction. A standalone ASM program therefore starts from default, zeroed state. That is defensible for a run-oriented API, but it becomes observable when the core wrapper delegates to it.

`tu_core_execute_asm_text()` swaps a core's state into `g_tu`, calls `tu_run_asm()`, and swaps the result back. The inner `tu_init()` destroys the swapped-in SRAM and replaces the custom state with defaults. In the controlled probe, an empty ASM program changed a 4x8 core to 16x16 and erased a marker in W-SRAM. Thus “execute ASM on this core” currently means “replace this core with a fresh default legacy instance, then execute.”

The safe API contract should choose one of two semantics explicitly:

1. **fresh program:** reset state, but preserve the handle's runtime configuration; or
2. **in-place program:** execute against existing state, with reset requested separately.

Combining reset and execution hides a lifecycle transition inside an operation method.

## 5.6 What `tu_core_t` owns—and what it does not

`tu_core_t` contains a `tu_state_t` by value. Creation initializes `g_tu`, copies the struct into the core, and clears `g_tu`. Operations use `core_swap_in()` and `core_swap_out()` around legacy calls. This creates real separation for heap pointers contained in each snapshot, especially SRAM and the command queue.

The probe confirmed distinct W-SRAM allocations and independent wrapper byte counters for two cores. This is **executable partial isolation**.

However, the implementation also has mutable globals outside `tu_state_t`:

- `g_tu_dma` in `dma_descriptor.c`;
- the dataflow registry;
- logging configuration and trace state;
- error mode, last error, and injection sites;
- the legacy `g_tu` used during every swapped operation;
- default-core singleton state.

DMA is the clearest discriminating case. `tu_core_get_dma()` returns `&core->state.dma`, but legacy DMA execution updates `g_tu_dma`. After one transfer on each of two cores, both embedded DMA snapshots still reported zero bytes while the global DMA total increased by four bytes. The core's top-level `total_dma_bytes` did update because it lives in the swapped `g_tu`.

Core creation also does not coexist transparently with an already initialized legacy singleton. It calls `tu_init_with_config()`, which tears down the current global SRAM, copies the replacement into the core, and clears `g_tu`. The probe observed `g_tu.initialized=false` and a null command-queue pointer after creating cores. `tu_core_init()` further discards the creation configuration by calling default `tu_init()`. Both reinit and destruction use raw `free(cmdq)` instead of the recursive queue destructor; reinit also frees `icc_buffer` without clearing it, leaving a later double-free risk. Applications should therefore treat legacy mode and core mode as mutually interfering at this snapshot.

No lock protects the swap window. Concurrent operations on two cores can overwrite `g_tu`, and nested/reentrant calls have the same structural hazard. `tu_core_t` is best described as a serialized compatibility wrapper with isolated SRAM snapshots—not an independently executable thread-safe core.

## 5.7 Cluster ownership and SPMD scope

A cluster allocates its own struct, an array of core pointers, and each core. `tu_cluster_destroy()` destroys every core, then the array and cluster. This is the most explicit top-level ownership path in the current API.

Cluster communication directly accesses each core's O-SRAM, so point-to-point copies do not require the global swap. Cluster ASM execution, by contrast, loops over cores sequentially and invokes the swap-based core ASM wrapper. It is named SPMD but is not concurrent execution, and the source promises neither host threads nor lockstep timing.

The focused multicore suite passes 16/16 and gives useful evidence for core construction, SRAM separation, topology helpers, copies, and analytical interconnect modes. Its test named “SPMD execution” does not call `tu_cluster_spmd_execute`; it executes two direct `tu_core_mma()` calls. Consequently, aggregate success does not gate the public SPMD wrapper or its ASM-reset semantics.

## 5.8 Error detection is not error propagation

Tusim's status framework defines structured codes and records file, line, function, and message. That is valuable observability. But the header's broad design statement—functions that can fail return `tu_status_t`—does not describe most legacy public operations, which return `void`.

The direct DMA wrapper illustrates four distinct stages:

```text
bounds condition detected
 -> last-error side channel updated
 -> nested DMA function returns locally
 -> outer void wrapper continues accounting
```

For an intentionally oversized W-buffer load, the probe observed `TU_ERR_DMA_OVERFLOW`, no out-of-bounds copy, and a 131,073-byte increase in the wrapper's accounting even though the transfer was rejected. Logging the failure did not propagate control back through the outer function.

The status header says the last-error API is thread-safe and uses thread-local storage. The implementation uses a process-global `g_last_error`; repository inspection found no thread-local declaration, mutex, or atomic synchronization. `tu_status_str()` also checks only `code < TU_ERR_COUNT`, so a negative enum value can index before the string table. The safe claim is therefore: last-error inspection works for serialized callers using valid codes, while concurrent and negative-input semantics are unsupported.

The direct-DMA probe's nested transfer returns before copying, but this does not validate the general bounds architecture. `tu_mma()` performs three report-only helper checks and then forms raw pointers; low-level SRAM read/write functions likewise continue after their helper returns. Those paths remain source-proven out-of-bounds hazards, including arithmetic-wrap cases.

A composable error API should return status from the operation that failed, avoid updating success counters on failure, and define whether partial state changes are rolled back. A separate diagnostic record can enrich the return code but should not replace it.

## 5.9 API selection guide

| Need | Best current surface | Required caution |
|---|---|---|
| one short, serialized functional run | direct API | no legacy shutdown; reinit cleanup incomplete |
| generated ordered operations in default functional mode | command queue | host-pointer lifetime; async retirement defect |
| self-contained textual program | `tu_run_asm` | always resets to defaults |
| multiple serialized SRAM snapshots | `tu_core_t` | global swap and shared DMA/status/logging |
| topology and explicit O-SRAM communication | `tu_cluster_t` | sequential SPMD wrapper; partial isolation |
| concurrent independent models | none at pinned commit | requires instance-pure refactor and synchronization contract |

## 5.10 Verification and fidelity box

**Reproduced:** clean static/shared build; direct 19/19; command queue 9/9; ASM identity; multicore 16/16; status 9/9; and the chapter lifecycle probe. Execution occurred in clean archives, not the source checkout. A separate fresh archive under LeakSanitizer reported `23584 byte(s) leaked in 33 allocation(s)` from repeated direct initialization; the enclosing Make invocation still returned zero, so exit status alone was not a leak gate.

**Functional-model evidence:** SRAM contents, API state transitions, counters, and status observations are executable software behavior.

**Not established:** thread safety, failure atomicity under allocation failure, leak quantity, ABI stability, concurrent SPMD timing, RTL equivalence, or silicon calibration.

**Safe interpretation:** use the APIs to explore serialized functional behavior while treating instance/concurrency boundaries as model-development questions. Do not infer that `tu_core_t` maps one-to-one to a physically independent hardware core merely because it contains a `tu_state_t`.

## 5.11 Failure modes to carry forward

1. A reset hidden inside an execution wrapper erases caller-prepared state.
2. A struct copy appears instance-local while external globals remain shared.
3. A completed command is not retired, exhausting capacity or blocking drain.
4. A void helper reports an error but its caller continues success accounting.
5. A header claims thread-local behavior that the implementation does not provide.
6. A passing test name overstates coverage because it does not call the named public path.
7. Reinitialization clears visible state but leaks resources whose pointers were erased.
8. Borrowed host pointers outlive their buffers when execution mode changes from synchronous to asynchronous.

## 5.12 Implications for Tusim development

A robust evolution path is to make one opaque instance the sole owner of SRAM, DMA, queue, counters, status, logging/tracing context, and selected plugin state. Direct functions would accept that instance; legacy names could forward to a default singleton. ASM would accept a reset policy, and cluster execution would operate on handles without swapping globals. Destruction would be idempotent, initialization would publish only fully constructed state, and every fallible public operation would return a status.

That refactor has costs: wider call signatures, migration work in generated code, and new tests for partial construction and concurrency. The benefit is not abstract software cleanliness. It is the ability to compare multiple architecture configurations in one process without cross-run counters, hidden resets, or serialization assumptions contaminating the experiment.

## Summary

Tusim's public surface is layered over a legacy singleton. The direct API owns process-global architectural state; the command queue dispatches back into it; ASM starts a fresh default run; core handles preserve important per-instance snapshots through global swapping; and clusters own arrays of those handles. SRAM isolation is real, but whole-engine instance purity is not. DMA, status, logging, registries, and execution swapping remain shared.

The central method is an ownership audit: list every mutable object, identify its owner and borrowers, trace construction and destruction, then use discriminating probes for coexistence, reset, completion/retirement, and error propagation. API names and passing happy-path tests are not enough to establish lifecycle guarantees.

## Review questions

1. Why does distinct SRAM storage not prove whole-core isolation?
2. Which resources are lost when `g_tu` is zeroed during reinitialization?
3. How do completion and retirement differ in a command queue?
4. Why does a raw host pointer require different lifetimes in synchronous and asynchronous modes?
5. What makes `tu_run_asm()` a fresh-run API at this commit?
6. Why is a process-global last-error record incompatible with the header's thread-local claim?
7. Which multicore operations avoid `g_tu`, and which still require the swap wrapper?
8. What evidence would be required before calling `tu_core_t` thread-safe?

## Design exercises

1. Draw a lifecycle state machine for an opaque `tu_instance_t` with failure-atomic creation, reset, and idempotent destruction. Mark which transitions may allocate.
2. Redesign the DMA API so a core owns its engine and rejected transfers cannot update success counters. State the migration path for legacy callers.
3. Write a concurrency test that would distinguish process-global last-error state from true thread-local storage without relying on timing luck.
4. Extend the chapter probe to verify a corrected async queue: every completed command must retire, capacity must be reusable, and `sync` must terminate.

## Primary repository references

- `tu_cmodel/tu_cmodel.h:74-131,180-281`
- `tu_cmodel/tu_cmodel.c:31-109,151-189,193-200,313-402`
- `tu_cmodel/command_queue.h:101-228`
- `tu_cmodel/command_queue.c:157-184,200-272,285-359`
- `tu_cmodel/tu_asm.c:21-41,86-123,198-271`
- `tu_cmodel/tu_core.h:32-142`
- `tu_cmodel/tu_core.c:11-117,121-224`
- `tu_cmodel/tu_cluster.h:74-131,183-198`
- `tu_cmodel/tu_cluster.c:20-114,339-510`
- `tu_cmodel/dma_descriptor.h:49-133,175-188`
- `tu_cmodel/dma_descriptor.c:19-64,580-725`
- `tu_cmodel/tu_status.h:11-17,122-147`
- `tu_cmodel/tu_status.c:55-76,82-172`
- `tests/test_command_queue.c:25-285`
- `tests/test_multicore.c:52-201,563-632`
- `tests/test_error_handling.c:53-97,183-245`
- `Makefile:214-227,339-347,489-535`
