# Chapter 11 Source and Claim Ledger — Instruction Surfaces and Command-Queue Ordering

- **Pinned source:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Canonical run target:** `experiments/runs/ch11-instruction-contracts/20260728-ch11-canonical/`
- **Status vocabulary:** `verified`, `qualified`, `rejected`, `blocked`
- **Draft gate:** blocked pending independent pre-draft review and evidence sealing

## Claim ledger

| ID | Claim | Evidence | Status | Required wording / limitation |
|---|---|---|---|---|
| C11.1 | `tu_instruction_t` is a packed 12-byte C object with opcode, flags, three 16-bit dimensions, and one 32-bit immediate field. | `tu_isa.h`; ISA test; custom byte probe | verified | “96-bit object layout,” not portable binary stream |
| C11.2 | The enum has 59 explicit operation enumerators, while the name table returns 68 non-`UNKNOWN` slots because `0x07`–`0x0f` receive reserved labels; 60 slots below the 128 sentinel return `UNKNOWN`. | enum extraction; custom probe; `tu_isa.c` | verified | do not call 68 operations executable |
| C11.3 | No binary encoder/decoder API or runtime binary-stream consumer was found in the exact pinned files and whole-tree producer/consumer inventory audited for this chapter. | fail-closed source audit; whole-tree call inventory | qualified | this is a bounded repository-negative claim, not proof about uninspected external consumers; native bytes are host-layout evidence only |
| C11.4 | Opcode names, categories, compute/DMA predicates, SRAM predicates, and flag extraction are executable metadata queries. | `tu_isa.c`; 9/9 ISA test | verified | metadata is not operation semantics or dispatch |
| C11.5 | Reserved slot `0x0f` has category `UNKNOWN` but `has_sram_operands()` returns true through its default branch. | custom probe | verified | query families do not define one total unknown-op policy |
| C11.6 | The command queue aliases ISA opcode values but embeds operand storage only for fixed DMA, MMA, and elementwise descriptors. | `command_queue.h`; source audit | verified | aliasing does not make every ISA descriptor queue-compatible |
| C11.7 | Queue execution handles exactly NOP, fixed DMA load/store, MMA, SYNC, BARRIER, HALT, and generic ELEMENTWISE switch cases; other cataloged opcodes fault. | `command_queue.c`; source audit; CONV2D probe | verified | eight switch families, not full ISA execution |
| C11.8 | A queue submission returns the positive command ID, contradicting the low-level header prose that says zero on success. | source; custom probe | verified | callers must use the implementation/public-wrapper contract at this pin |
| C11.9 | In synchronous mode, submission invokes the executor immediately without checking dependency IDs or barrier readiness. | source audit; nonexistent-dependency probe | verified | “dependency fields retained” is not dependency enforcement |
| C11.10 | In tick-driven mode, every submission calls one queue tick; a ready command can execute and become `COMPLETED` inside the submit call. | source; custom probe | verified | deferred mode is auto-advanced, not passive admission |
| C11.11 | A dependency ID absent from all queue slots is assumed already complete. | `deps_satisfied`; sync/async probes | verified | unknown dependency handling is fail-open |
| C11.12 | `cycle_submitted` is assigned when `execute_command()` begins, not when the command is admitted. | source audit | verified | field name must not be used as admission timestamp |
| C11.13 | Ready queue commands complete in one host executor call at the queue's current tick; queue time does not model operation service duration. | source; async timestamp probe | verified | no physical issue/completion latency inference |
| C11.14 | Completed and faulted commands remain counted in queue depth after normal synchronous submission and tick-driven execution. | source; custom probe | verified | `count` is not current live work after execution |
| C11.15 | Normal submission paths do not retire slots; the only decrement branch is inside `tu_cmdq_tick()` when `synchronous` is true, while synchronous submit does not call that tick. | source audit | verified | capacity becomes a lifetime-submission limit until reset |
| C11.16 | `tu_cmdq_sync()` is a no-op in synchronous mode and can fail to terminate in tick-driven mode once `count>0` contains only non-pending commands. | source; bounded probe avoids async call | verified | tick-driven nontermination is static, not executed |
| C11.17 | Unknown command status returns `COMPLETED`, and waiting for an unknown ID returns success. | source; custom probe | verified | neither API proves that the ID was ever submitted |
| C11.18 | Commands receive increasing signal IDs within the bounded probe and across reset, but the signal registry is never populated because `signal_count` is never incremented. | source audit; custom probe | verified | signal firing/observation is not established; no wraparound claim |
| C11.19 | Faulted unsupported opcodes increment the fault counter and remain retained in queue storage. | CONV2D probe | verified | fault is observable by retained status, not retired/reclaimed |
| C11.20 | A synchronous four-entry queue rejects the fifth lifetime submission even after prior commands completed/faulted. | custom probe | verified | observed capacity case, not generalized concurrency |
| C11.21 | The focused command-queue suite reports 9/9. Its overflow case repeatedly submits synchronous MMAs until completed work fills the queue and treats rejection as the expected pass; it does not challenge missing dependencies, signal registry population, unknown IDs, or tick-driven drain. | test audit; custom probe | qualified | suite is a passing snapshot observation and confirms lifetime-capacity behavior; it is not lifecycle certification |
| C11.22 | The shipped/full config parses instruction width, queue depth, dependency checking, and cycle-model fields, but `tu_config_to_runtime()` drops all four and global queue creation uses compile-time depth and cycle mode with no dependency-enable consumer. | shipped JSON; config/core source audit; Chapter 4 evidence | verified | parsed request is not active queue policy; the parsed 96-bit label does not validate the packed object or a decoder |
| C11.23 | The legacy text interpreter recognizes LOAD_W, LOAD_A, LOAD_O, MMA, STORE_O, and SYNC and executes direct global wrappers. | `tu_asm.c`; ASM smoke | verified | six text mnemonics; directives are separate |
| C11.24 | Legacy text ASM bypasses the command queue, expanded ISA object, and scheduler; expanded `BARRIER` is rejected. | source audit; custom probe | verified | text execution does not inherit queue ordering |
| C11.25 | Text ASM calls `tu_init()` at entry and ignores declared host-buffer sizes when executing transfers. | `tu_asm.c`; source audit | verified | global reinitialization and bounds risks apply; unsafe overflow not executed |
| C11.26 | The compiler does not emit `tu_instruction_t` binary objects or call `tu_sched_run()` on the audited path. | compiler source audit | verified | generated C/direct APIs remain a separate surface |
| C11.27 | Scheduler, ISA, ASM, and queue objects are all static-library members and have focused targets; linkage alone does not connect their runtime paths. | Makefile/archive/source audit | verified | library-linked is not integrated |
| C11.28 | With explicit default scheduler config, `NOP; BARRIER; DMA.LOAD` can emit as `DMA.LOAD; NOP; BARRIER`. | custom scheduler probe | verified | barrier does not order a later independent node in this DAG |
| C11.29 | Scheduler “barrier insertion” can report a positive hazard count but does not add instruction nodes; the full run then returns zero inserted barriers. | source audit; positive-count graph/run probe | verified | never say barriers are inserted into output |
| C11.30 | Scheduler hoist/insertion counts are reset in list scheduling before return, including inputs for which the direct analysis functions return one. | source audit; positive hoist/insertion probes | verified | returned zeros do not prove no analysis event occurred |
| C11.31 | Passing `NULL` config builds a graph with defaults but skips the main entry point's hoist/insertion calls. | source audit | verified | `NULL = default` is only partial behavior |
| C11.32 | Within `tu_scheduler.c`, `pipeline_tiles` and `max_window` each occur only in the default initializer and have no implementation consumer; their declarations and tests remain separate occurrences. | exact implementation-file occurrence audit | verified | declared knobs are inert in the scheduler implementation at the pin |
| C11.33 | Scheduler `estimated_cycles` serially adds one per DMA node and four per other emitted node. | source; custom result | verified | analytical fixed-cost sum, not overlap or calibrated time |
| C11.34 | The scheduler test reports 14/14 but accepts nonnegative barrier counts, does not assert an inserted barrier, and does not execute scheduled output through queue/ASM. | test audit | qualified | local graph/order evidence only |
| C11.35 | Physical overlap, out-of-order execution/retirement, interrupts, portable binary decode, and full compiler-to-runtime ISA execution are established. | absent integration/calibration | rejected | explicitly unavailable from Chapter 11 evidence |
| C11.36 | In tick-driven mode, a barrier can complete while an earlier command remains pending on a faulted dependency; a later ready command can then complete before that earlier command. | retained fault/pending/barrier/post command probe; `barrier_clear()` source | verified | the queue barrier neither waits for all prior commands nor keeps later commands behind prior unfinished work |
| C11.37 | The edition's compiled constants create the global 16-entry queue in synchronous functional mode, while full-config defaults independently say cycle model 2; public fixed wrappers submit without dependencies. | `tu_config.h`; `config.c`; `tu_cmodel.c`; source audit | verified | standalone tick-driven probes characterize a supported queue mode, but the shipped global default is synchronous and fills after 16 lifetime submissions until reset |
| C11.38 | The public elementwise wrapper stores the caller's `num_ops` before clamping only its local copy loop to eight; queue execution forwards the stored count, and `tu_ew_apply_fused()` rejects counts above eight before copying or accessing SRAM. The queue nevertheless marks that rejected/no-op operation `COMPLETED`. | wrapper/queue/fused-helper source audit; nine-op bounded probe | verified | require `num_ops <= 8` for useful work; `COMPLETED` does not prove the elementwise operation executed |
| C11.39 | Reset restarts command IDs at one but does not restart `next_signal_id`; after reset, stale command ID 1 can resolve to a new command while its signal ID continues from the prior lifetime. | `tu_cmdq_reset()` source; reset-ID probe | verified | reset invalidates all handles; command IDs are queue-epoch-local and no epoch is encoded |
| C11.40 | Scheduler nodes retain at most 16 predecessor/successor IDs; a barrier after 17 ordinary nodes builds successfully while retaining only 16 predecessor edges. | scheduler source audit; dense-barrier probe | verified | DAG construction silently truncates dense ordering constraints rather than rejecting them |
| C11.41 | `tu_sched_hoist_dma()` reports a candidate count but does not move graph nodes; actual output reordering comes from list-scheduler priority selection, and the full result clears the count. | scheduler source audit; positive-hoist probe | verified | do not describe the named hoist pass itself as a transformation |
| C11.42 | Whole-tree C call inventories find scheduler consumers only in its implementation and scheduler tests/sweep; legacy ASM additionally reaches core/cluster wrappers; queue wrappers additionally reach DPI and elementwise tests. | exact pinned whole-tree call inventory | verified | runtime reachability is surface-specific; absence of compiler→scheduler remains bounded to the audited pin |
| C11.43 | Low-level queue submission with `num_deps > 0` and `dep_ids == NULL`, unchecked allocation failures, and legacy ASM's 17th-weight/buffer-extent paths are unsafe static preconditions. | pinned source inspection; skeptical review | qualified | do not execute these uncontrolled cases in the canonical runner; trusted callers must reject them before entry |

## Lifecycle vocabulary

| Predicate | Operational meaning at the pin |
|---|---|
| represented | enum/object/text/queue surface can name the operation |
| admitted | submit copied the supported operand form into a slot and returned an ID |
| dependency-ready | queue lookup found every retained dependency `COMPLETED`, or failed open because an ID was absent |
| issued label | executor set status to `ISSUED`; no externally persistent interval is demonstrated |
| executor returned | direct C operation returned, including unsupported-op fault path |
| command completed | executor set `COMPLETED` and incremented queue completion count |
| command faulted | unsupported queue opcode set `FAULTED` and incremented fault count |
| signal fired | registry entry with matching signal ID was updated; no entry is created at the pin |
| wait succeeded | known command was completed or requested ID was absent; not proof of identity/admission |
| storage retired | slot ID cleared and queue count decremented; normal submit/tick path does not establish this |
| reusable capacity | a new submission can claim a slot; bounded by retained `count`, not completed work |
| reset | command slots/dependencies, count, queue cycle, counters, barrier state, and next command ID reset; next signal ID does not, and reused command IDs can alias stale handles |

## Surface/reachability matrix

| Surface | Representation | Execution | Ordering/lifecycle | Integration classification |
|---|---|---|---|---|
| expanded ISA | 59 explicit operation enums; packed object; metadata helpers | no generic binary decode/dispatch | none | executable metadata, not generic instruction runtime |
| command queue | ISA opcode alias plus DMA/MMA/EW operand union | eight switch families | flawed dependencies, barriers, signals, depth/retirement | public/runtime reachable for fixed wrappers |
| legacy text ASM | six instruction mnemonics | direct global wrappers | source order plus direct SYNC only | executable, bypasses queue/expanded ISA/scheduler |
| standalone scheduler | packed instruction arrays | produces reordered arrays only | source-derived DAG and fixed-cost report | library-linked/focused-tested, not runtime consumed |
| compiler | ONNX to generated C/direct calls | generated path has separate Chapter 3 limits | no packed ISA/scheduler call | demonstration frontend, not ISA producer |

## Evidence labels

- **Executable:** named metadata queries, fixed queue dispatch paths, legacy text smoke, scheduler transformations, and custom bounded cases.
- **Integrated:** public fixed queue wrappers and legacy text direct wrappers are separately reachable; no unified compiler→binary ISA→scheduler→queue path exists.
- **Functional model:** named direct C operations and queue executor effects; no hardware issue/retirement timing.
- **Analytical model / Estimated:** scheduler's 1/4 fixed node-cost sum is uncalibrated and serial.
- **Calibration:** none for decode, queue timing, overlap, interrupts, or hardware ordering.

## Current disposition

The initial evidence rejects a chapter organized as an opcode catalog. The central lesson is the execution ladder:

```text
declared → named/classified → serialized/parsed → decoded → dispatched
→ dependency-ready → executed → outcome observed → signaled → retired
```

Tusim reaches different rungs on different surfaces. The skeptical reviews have been incorporated; drafting remains blocked until the corrected execution inputs are committed and the canonical retained-evidence bundle is sealed and validated.
