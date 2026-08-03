# Chapter 11 Audit — Instruction Surfaces and Command-Queue Ordering

- **Date:** 2026-07-28
- **Tusim pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Canonical run:** `experiments/runs/ch11-instruction-contracts/20260728-ch11-canonical/`
- **Result:** `CH11_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS`
- **Interpretation:** pinned snapshot conformance, not a correctness, integration, ordering, portability, performance, or calibration certificate

## Reproduction
To reproduce the executable audit, use a **fresh run ID**. The runner intentionally refuses to overwrite any existing directory, including the committed canonical run:

```bash
cd /home/zxy/Workplace/books/tusim-book
CH11_RUN_ID="repro-$(date -u +%Y%m%dT%H%M%SZ)" \
  bash experiments/run_ch11_instruction_contract_audit.sh
```

This requires `/home/zxy/Workplace/projects/tusim` to remain a detached, tracked/untracked-clean checkout at the pinned commit. The runner supplies external timeouts and creates the new retained directory under `experiments/runs/ch11-instruction-contracts/`.

To verify the already committed historical canonical run without rerunning it:

```bash
cd /home/zxy/Workplace/books/tusim-book/experiments/runs/ch11-instruction-contracts/20260728-ch11-canonical
sha256sum -c sha256-retained.txt
```

## Provenance and gates

The canonical run requires and records:

- detached, tracked/untracked-clean Tusim at the exact pin before and after;
- unchanged ignored-source inventory;
- unchanged book HEAD, branch, execution inputs, and status outside the new run directory;
- zero book remotes;
- a deterministic source-archive SHA-256 before automatic deletion;
- **26 exact source/test/compiler/config hashes** and **96 structural/reachability predicates**, totaling **122** source-audit checks;
- static archive membership for `command_queue.o`, `tu_asm.o`, `tu_isa.o`, and `tu_scheduler.o`;
- no retained archive extraction, source tar, or linked binary;
- a relative-path manifest covering inputs, family logs, source audit, archive inventory, archive digest, and the closed transcript.

## Focused harness observations

These are pinned observations, not independent certification of the claims their names suggest.

| Family | Reported result | Qualification |
|---|---:|---|
| command queue | 9/9 | its overflow case fills the synchronous queue with completed MMAs and expects rejection; it does not distinguish completion from retirement |
| expanded ISA | 9/9 | object size, names, categories, flags, aliases, and descriptor sizes; no binary encoder/decoder or generic executor |
| legacy text ASM | identity smoke PASS | one self-contained six-mnemonic-path smoke; no expanded-ISA or queue integration |
| scheduler | 14/14 | local DAG/order checks; barrier insertion merely requires a nonnegative count and scheduled output is not executed |

## Representation result

The packed instruction object is 12 bytes:

```text
byte 0       opcode
byte 1       flags
bytes 2..3   dim0
bytes 4..5   dim1
bytes 6..7   dim2
bytes 8..11  immediates
```

On the audited AArch64 little-endian host, a deliberately nonsymmetric MMA object produced:

```text
10 a5 22 11 44 33 66 55 aa 99 88 77
```

This is native packed-object evidence. The source audit finds no binary instruction encoder or decoder, byte-order policy, stream version, malformed-stream handling, or runtime binary-stream consumer. Therefore the chapter calls it a **96-bit C object layout**, not a portable instruction wire format.

A mechanical enum extraction finds 59 explicit operation enumerators. Iterating all 128 catalog slots finds 68 non-`UNKNOWN` names and 60 `UNKNOWN` slots because nine reserved control values, `0x07` through `0x0f`, receive `RESERVED_*` names. “68 named slots” must not become “68 executable operations.” Metadata queries also do not share one unknown policy: reserved slot `0x0f` reports category `UNKNOWN` while the generic SRAM-operand query defaults it to true.

## Reachability result

The pin exposes four distinct instruction-like surfaces:

| Surface | What it carries | What consumes it | What it does not establish |
|---|---|---|---|
| expanded ISA | packed object, enum, names, flags, categories, operand descriptors | metadata, scheduler, liveness analyses | binary parsing or generic operation execution |
| command queue | ISA-valued opcode plus DMA/MMA/elementwise union | fixed queue executor switch | full expanded-ISA operands or semantics |
| legacy text ASM | six instruction mnemonics plus directives | direct global wrappers | packed ISA, queue dependencies/barriers, or scheduler output |
| scheduler | arrays of packed instruction objects | standalone transform/report API | runtime issue, queue execution, or compiler integration |

All four object files are linked into `libtucmodel.a`, and all four have focused targets. Archive co-membership is not a call edge. The audited ONNX compiler emits generated C/direct operations; it does not emit packed instruction objects or call the scheduler.

## Command-dispatch result

The queue aliases ISA opcode values, but its operand union contains only:

- fixed DMA;
- fixed MMA;
- generic elementwise.

Its executor switch handles eight opcode families:

```text
NOP, DMA.LOAD, DMA.STORE, MMA, SYNC, BARRIER, HALT, ELEMENTWISE
```

A cataloged `CONV2D` submission reached the queue's default branch, printed an unknown-opcode diagnostic, became `FAULTED`, and incremented the fault count. Presence in the enum, name table, queue alias block, or static archive therefore does not prove queue execution.

The public elementwise wrapper has a separate contract boundary. It stores caller `num_ops` into the descriptor before clamping only its local copy loop to eight. Queue execution builds an eight-entry local array and passes the original stored count to the fused helper. The helper rejects counts above eight before copying its input or accessing SRAM, so the bounded nine-operation probe was safe. The queue nevertheless marked the rejected/no-op command `COMPLETED`:

```text
ELEMENTWISE_BOUNDARY count=9 status=2 completed=1 faulted=0
```

Thus `num_ops <= 8` is required for useful elementwise work, while queue completion alone does not prove that the helper performed the operation.

## Submission and timestamp result

Low-level header prose says submission returns zero on success. The implementation and custom probe return the positive command ID. The header's status and tick comments also describe retirement behavior that the implementation does not provide.

In a synchronous four-entry queue, a NOP carrying nonexistent dependency ID 9999:

- returned its positive ID;
- executed immediately despite the dependency;
- became `COMPLETED` at queue cycle zero;
- remained counted in depth.

Synchronous submit calls the executor directly. Dependency readiness and barrier state are not checked first.

In a tick-driven queue, submit itself calls one tick. A ready NOP therefore completed inside the submit call at queue cycle one. A later explicit tick advanced to cycle two but retired nothing. Submitting another NOP with nonexistent dependency ID 123456 auto-ticked at cycle three and completed because a dependency absent from all slots is assumed already complete.

`cycle_submitted` is written at executor entry, not admission. `cycle_completed` is written when that same host executor call returns. Those fields do not expose queue waiting separately from issue, do not model service duration, and are not physical timestamps.

## Dependency and barrier result

Dependency lookup has two fail-open/fail-stuck cases:

- missing ID: treated as already complete;
- retained `FAULTED` ID: found but never equal to `COMPLETED`, so its dependent remains pending.

The bounded barrier probe used the second case. A two-cycle bounded wait returned timeout while the dependent stayed pending, after which the probe continued:

```text
1. submit unsupported CONV2D       -> FAULTED
2. submit NOP depending on step 1 -> PENDING
3. submit BARRIER                  -> COMPLETED
4. submit independent NOP         -> COMPLETED
5. step-2 NOP                     -> still PENDING
```

The retained status line was:

```text
ASYNC_BARRIER fault=3 pre=0 barrier=2 post=2 count=4 cycle=6
```

Thus the barrier can complete while earlier work remains pending, and later work can complete before that earlier work. It is not a fence over all prior commands. In synchronous mode it is simply executed immediately as a no-op.

## Completion, signal, wait, and retirement result

The probe separates five predicates that the declarations blur:

1. executor status became `COMPLETED`;
2. queue completion counter incremented;
3. signal registry entry fired;
4. wait returned success;
5. slot storage retired and capacity became reusable.

Only the first two occurred for ordinary successful commands. Each command received a positive signal ID, but `signal_count` remained zero because no registry insertion exists. Unknown command status returns `COMPLETED`; waiting on an unknown ID returns success despite header prose promising “not found.” Neither proves prior admission.

In synchronous mode after three completed NOPs and one faulted CONV2D:

```text
SYNC_QUEUE count=4 submitted=4 completed=3 faulted=1
           signal_count=0 current_cycle=0
```

The fifth submission was rejected. `tu_cmdq_sync()` returned immediately and retained count four.

In tick-driven mode after two completed NOPs:

```text
ASYNC_QUEUE count=2 submitted=2 completed=2 faulted=0
            signal_count=0 current_cycle=3
```

Normal tick-driven execution did not clear IDs or decrement count. The decrement branch is guarded by `cq->synchronous` inside the tick function, while synchronous submit has already made its commands non-pending and does not call that tick. Therefore neither normal mode retires completed storage. The global shipped queue has compiled capacity 16 and synchronous functional mode, so it reaches rejection after 16 lifetime submissions until reset. A tick-driven `tu_cmdq_sync()` can fail to terminate when count is nonzero but no pending command can change state; the audit keeps that path static rather than executing it.

Reset adds an identity hazard rather than an epoch. After four submissions, reset restarted the next command ID at one but left the next signal ID advancing. The next command therefore produced:

```text
RESET_IDS old_cmd=1 new_cmd=1 old_signal=1 new_signal=5
```

A stale command handle can alias a different post-reset command; no queue epoch is encoded.

## Configuration result

Three declarations must remain separate:

| Producer | Queue depth | Dependency switch | Cycle mode |
|---|---:|---:|---:|
| compiled `tu_config.h` | 16 | 0 | 0, functional |
| full `tu_config_default()` | 16 | false | 2, cycle-accurate label |
| global queue construction | compiled depth | no switch consumed | synchronous iff compiled mode is functional |

The shipped JSON and full parser store instruction width, queue depth, dependency-checking, and cycle-model requests. `tu_config_to_runtime()` drops all four. The active global queue constructor uses compiled constants instead, and public fixed queue wrappers submit without dependency arrays. A parsed “96-bit” or “cycle-accurate” request therefore validates neither a binary codec nor a calibrated/tick-driven queue at this pin.

## Legacy text-ASM result

The interpreter recognizes six instruction mnemonics:

```text
LOAD_W, LOAD_A, LOAD_O, MMA, STORE_O, SYNC
```

It calls `tu_init()` at entry and executes direct global wrappers. It never submits to the command queue, constructs a packed instruction object, or invokes the scheduler. Separate core and cluster wrappers can call this same legacy interpreter. The expanded mnemonic `BARRIER` was rejected with return `-1`.

The interpreter looks up registered buffer pointers while discarding their declared sizes on transfer instructions. The audit does not execute an out-of-bounds case. Trusted scripts must supply in-range offsets/extents and keep all registered storage live; text parsing is not a safety boundary.

## Scheduler result

The scheduler consumes packed instruction arrays, builds a local access/dependency graph, and returns another array. It does not execute that array.

For:

```text
NOP; BARRIER; DMA.LOAD
```

the default balanced policy returned:

```text
DMA.LOAD; NOP; BARRIER
valid=1, hoisted=0, inserted=0, estimated_cycles=9
```

A later independent DMA node is not made dependent on the barrier. The scheduler's own validator can still call the result valid because it checks the graph it built.

“Barrier insertion” counts selected graph patterns but never increments graph nodes or creates an instruction. A discriminating input produced a direct count of one, retained two graph nodes, and returned zero inserted barriers from the full scheduler. Likewise, `tu_sched_hoist_dma()` reported one candidate without moving graph nodes, while the full run returned zero. Actual order changes come from list-scheduler priority selection, not from either named analysis pass:

```text
SCHED_POSITIVE_INSERT direct=1 run=0 input_nodes=2 output_nodes=2
SCHED_POSITIVE_HOIST direct=1 run=0 input_nodes=3 output_nodes=3
```

Each scheduler node stores at most 16 predecessor and successor IDs. A barrier after 17 ordinary nodes built successfully but retained only 16 predecessor edges:

```text
SCHED_DENSE_BARRIER prior=17 retained_preds=16 max_deps=16
```

Passing `NULL` config builds with defaults but skips the entry point's hoist/insertion calls. Within `tu_scheduler.c`, `pipeline_tiles` and `max_window` occur only in the default initializer; declarations and tests do not constitute implementation consumption.

The cycle report serially adds one for every DMA node and four for every other emitted node. The observed nine is therefore `1 + 4 + 4`. It is an uncalibrated **Analytical model / Estimated** fixed-cost sum, not overlap, issue, occupancy, or elapsed time.

## Safe interpretation and caller subset

For the pinned snapshot:

- use expanded ISA helpers as metadata and analysis interfaces, not as proof of binary or executable support;
- treat native object bytes as host-layout observations only;
- treat queue support as the exact fixed dispatch subset;
- require valid, already-known dependency IDs and do not rely on missing-ID rejection;
- do not use the queue barrier as a fence;
- do not use signal IDs, unknown-ID status, or unknown-ID wait success as completion evidence;
- bound total submissions between resets by queue capacity; do not call tick-driven drain after retained completed/faulted work;
- require elementwise `num_ops <= 8` and independently prove all operation/storage bounds;
- keep DMA host buffers alive until the executor has actually returned;
- use legacy ASM only for trusted six-mnemonic scripts with externally proven extents;
- treat scheduler output as a standalone analytical artifact and revalidate any desired ordering independently before execution.

The exact pinned whole-tree C call inventory further bounds integration: scheduler calls occur only in its implementation and scheduler test/sweep files; queue wrappers additionally reach DPI and elementwise tests; legacy ASM additionally reaches core and cluster wrappers. These are exact-pinned repository observations, not claims about external consumers.

Reset clears slots, dependencies, count, queue cycle, counters, and barrier state, then restarts command IDs at one. It does not restart the next signal ID. The probe observed old/new command IDs both equal to one while signal IDs advanced from one to five; a stale pre-reset command handle therefore aliased the new command. Reset is not a substitute for proving that borrowed pointers are no longer in use on a genuinely deferred implementation, and every pre-reset handle must be invalidated by the caller.

## Evidence boundaries

The audit establishes executable metadata, bounded queue state transitions, fixed dispatch effects, text-parser reachability, and standalone scheduler transformations. It rejects:

- a portable binary ISA pipeline;
- full 59-operation queue execution;
- correct dependency rejection;
- barrier/fence ordering;
- functioning completion signals;
- ordinary storage retirement;
- a terminating tick-driven drain for retained completed/faulted work;
- compiler→packed ISA→scheduler→queue integration;
- physical overlap, calibrated timing, out-of-order retirement, interrupts, or hardware memory-order semantics.

The snapshot result means that all expected declarations, focused observations, adversarial findings, safety skips, and provenance gates reproduced. It is deliberately not named `AUDIT_PASS`.
