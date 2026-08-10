# Chapter 11 — Instruction Surfaces and Command-Queue Ordering

Tusim edition commit: `e918c80b6fce833cd1fcae97730fa841c2176f25`

## Learning objectives

After this chapter, you should be able to:

1. distinguish an opcode declaration from portable encoding, parsing, dispatch, execution, retirement, reclamation, and handle-invalidation contracts;
2. identify Tusim's expanded ISA, legacy text ASM, command queue, scheduler, compiler, and configuration surfaces without collapsing them into a fictional stack;
3. trace a queue command from admission through dependency checking, execution, completion, signaling, and storage reclamation;
4. explain why missing IDs, faulted dependencies, barriers, and reset epochs are architectural contract decisions rather than implementation trivia;
5. interpret scheduler counts and cycle totals as bounded model outputs rather than evidence of queue execution or physical overlap;
6. design fail-closed tests that discriminate lifecycle states without entering unsafe or nonterminating paths; and
7. compare stronger instruction-transport designs across performance, storage, control, compiler, and verification costs.

## Prerequisite graph

This chapter assumes:

- Chapter 2's evidence ladder and snapshot-conformance discipline;
- Chapter 4's separation of declared, parsed, propagated, and consumed configuration;
- Chapter 5's ownership, reset, and process-global-state vocabulary;
- Chapter 6's W/A/O operand orientation and MMA entry points;
- Chapter 9's distinction among independent memory surfaces; and
- Chapter 10's separation of admission, eligibility, execution, outcome, timestamps, and reclamation.

Chapter 10 analyzed descriptor-DMA queues. This chapter does **not** reopen that transfer geometry. It asks a different question: when source files use words such as *instruction*, *queue*, *dependency*, *barrier*, *completed*, and *scheduler*, which concrete contract does each word name?

## Opening architecture question: when is an instruction an instruction?

Suppose a compiler emits a value named `CONV2D`. The expanded ISA gives it an opcode and a printable name. A queue accepts an opcode-sized field. Documentation describes scheduling and barriers. Can we conclude that a binary instruction stream can carry `CONV2D` through decode, issue, execution, completion, and retirement?

No. Every arrow in that sentence needs separate evidence.

An architecture can expose several instruction-adjacent surfaces for good reasons. A metadata catalog supports tools and design exploration. A text interpreter supports readable tests. A command queue supports host-side submission. A graph scheduler supports compiler experiments. The mistake is not having multiple surfaces. The mistake is inferring integration from shared names.

The reader decision for this chapter is therefore:

> Given an operation sequence and an ordering requirement, which Tusim surface represents or executes it, and what does that surface prove about encoding, transport, dependencies, barriers, completion, signaling, capacity, reclamation, and order?

The answer is rarely one label. It is a path through explicit contracts.

## 11.1 A lifecycle vocabulary that prevents false integration

A useful evidence ladder is:

```text
declared opcode
    != portable binary encoding
    != parseable text instruction
    != queue-submittable operation
    != dispatched operation
    != dependency-ready operation
    != completed operation
    != signaled operation
    != retired entry
    != reclaimed storage
    != invalidated handle
```

Each transition asks a different question.

- **Declaration:** Does a type assign a symbolic value and metadata?
- **Encoding:** Are bit positions, byte order, validity rules, and versioning defined independently of one compiler ABI?
- **Parsing or decoding:** Can bytes or text be converted into the internal operation form?
- **Admission:** Does a transport reserve storage and return a handle?
- **Readiness:** Have prerequisites reached the state required by policy?
- **Dispatch:** Does an executor recognize the operation and call an implementation?
- **Completion:** Has the executor recorded a terminal outcome?
- **Signaling:** Can another component observe that outcome through a defined event mechanism?
- **Retirement:** Has the command left the ordering or liveness structure that governs active work?
- **Reclamation:** Has its transport storage become reusable?
- **Invalidation:** Can an old external handle no longer resolve to live work?

Smith and Sohi use related distinctions when describing superscalar pipelines [SS95](../../references/foundations.md#ss95-superscalar-lifecycle-vocabulary). Tomasulo's algorithm shows why operand readiness and issue are separate decisions [TOM67](../../references/foundations.md#tom67-dependency-driven-scheduling). OpenCL makes queued, submitted, running, complete, event, and barrier contracts explicit [OCL311](../../references/foundations.md#ocl311-opencl-command-queue-contract). These sources provide vocabulary, not evidence that Tusim implements those machines or APIs.

The terminology also prevents a common C-model error: treating a status enum as a hardware pipeline. A model can change a record directly from `PENDING` to `COMPLETED` in one function call. That is a valid functional abstraction if documented. It does not reproduce issue queues, execution latency, writeback arbitration, precise exceptions, or in-order retirement.

## 11.2 Source map: adjacent surfaces, not one stack

The chapter's selected queue-ordering surfaces are:

| Surface | Primary files | What the evidence establishes | What it does not establish |
|---|---|---|---|
| expanded ISA | `tu_cmodel/isa/tu_isa.{h,c}` | packed C object, opcode declarations, names, categories, queries | portable byte stream, decoder, runtime dispatch |
| legacy text ASM | `tu_cmodel/tu_asm.{h,c}` | parsing and direct execution of a small mnemonic set | decoding the packed object, queue dependencies, expanded catalog coverage |
| command queue | `tu_cmodel/command_queue.{h,c}` | admission, IDs, dependencies, dispatch subset, status, capacity | full expanded ISA execution, conventional retirement, full-fence barriers |
| public wrappers | `tu_cmodel/tu_cmodel.{h,c}` | process-global submission entry points and queue construction | consumption of every full-config field |
| graph scheduler | `tu_cmodel/isa/tu_scheduler.{h,c}` | DAG analysis, list scheduling, candidate counts, cycle estimates | queue issue, runtime completion, physical overlap |
| liveness allocator (qualified adjacent surface) | `tu_cmodel/isa/tu_liveness.{h,c}` | consumes and rewrites packed instruction sequences, including spill/fill insertion | queue runtime, binary decode, or a compiler-to-queue bridge; allocator semantics are deferred |
| ONNX demonstration compiler | `compiler/onnx_to_tu.py` | source-level C emission for its supported demonstration path | binary expanded ISA emission or scheduler invocation |
| full configuration | `tu_cmodel/infra/config.{h,c}`, `config/tu_config.json` | declarations, defaults, parsing, partial conversion | automatic control of the global queue or scheduler |

A repository-wide C caller inventory sharpens the boundaries. Scheduler calls occur in the scheduler implementation and scheduler tests/sweep. Legacy ASM also reaches core and cluster wrappers. Queue APIs also reach public core/DPI wrappers and elementwise tests. No audited call edge joins the ONNX compiler to the C scheduler, or a packed instruction byte stream to a runtime binary consumer.

This table is intentionally not a complete audit of every compiler-side pass. The linked liveness allocator is an actual producer and consumer of `tu_instruction_t` sequences, which further shows that packed instructions can serve as an in-process analysis IR. Chapter 11 records that adjacency but defers its spill/fill and allocation contracts; the canonical 26-hash Chapter 11 audit does not claim liveness coverage.

This is a pin-bounded conclusion. It does not say that no future branch could integrate the surfaces. It says that the current chapter must not draw arrows that the audited revision does not contain.

## 11.3 The expanded ISA defines packed representation and metadata, not a runtime binary

The expanded header defines a packed instruction object with fields for opcode, flags, dimensions, and an immediate. The canonical probe reports:

```text
ISA sizeof=12 opcode_count_sentinel=128 named_slots=68 unknown_slots=60
ISA native_bytes=10 a5 22 11 44 33 66 55 aa 99 88 77
```

The object is 12 bytes—96 bits—on the audited AArch64, little-endian ABI. The byte line is an exact native-memory snapshot for one initialized object. It is useful because it catches field-layout drift. It is **not** a portable encoding specification.

A portable instruction format needs more than `__attribute__((packed))`. At minimum, it needs:

- field widths and bit positions independent of C layout;
- byte order;
- legal and reserved encodings;
- version and compatibility rules;
- an encoder and decoder with malformed-input behavior;
- stream alignment and framing; and
- a consumer that acts on the decoded representation.

RISC-V is a useful contrast because its unprivileged specification defines instruction fields and fence predecessor/successor sets normatively [RISCV26](../../references/foundations.md#riscv26-risc-v-unprivileged-isa). Tusim's packed object is local C representation evidence. The chapter therefore labels it **source-present metadata**, not a validated wire ISA.

Counts need similar care. Mechanical enumeration finds 59 explicit operation enumerators. The name table contains 68 non-`UNKNOWN` slots because nine reserved numeric slots also receive names. The remaining 60 slots below the 128-entry sentinel report `UNKNOWN`. None of these counts equals the number of queue-dispatched operations.

The metadata queries have defaults too. For example, an unassigned control-range slot can report category `UNKNOWN` while a generic query defaults it to touching SRAM. Such defaults can be conservative for analysis, but they are not execution evidence.

## 11.4 Legacy text ASM is a separate direct interpreter

The text interpreter recognizes a small mnemonic set centered on direct movement and matrix multiplication:

```text
LOAD_W
LOAD_A
LOAD_O
STORE_O
MMA
SYNC
```

It initializes global C-model state and calls direct operation APIs. It does not construct `tu_instruction_t`, submit queue entries, or invoke the graph scheduler. The canonical probe passes the expanded `BARRIER` mnemonic to the text interpreter and observes rejection:

```text
ASM expanded_mnemonic_rc=-1
```

That single negative case is pedagogically valuable. A name present in an expanded catalog is not automatically parseable text. Conversely, a parseable text command does not imply an equivalent packed binary representation.

The interpreter is still executable evidence within its boundary. The focused identity smoke test passes. Core and cluster wrappers can reach it. But its bindings discard host-buffer extents before execution, and a fixed binding table creates additional static preconditions. Those properties make the interpreter suitable for controlled demonstrations, not a proof of a hardened production command processor.

## 11.5 The command queue is an opcode-alias transport with a small dispatcher

The queue command type aliases expanded ISA opcode constants. That reuse avoids duplicate numeric assignments, but it does not import the whole catalog into dispatch.

The audited executor handles eight operation classes:

```text
NOP
DMA.LOAD
DMA.STORE
MMA
SYNC
BARRIER
HALT
ELEMENTWISE
```

A cataloged `CONV2D` value reaches the default branch and becomes `FAULTED`. The queue therefore proves a command transport for a subset, not a universal expanded ISA execution engine.

Descriptors also matter. Queue entries hold an opcode and a union of command-specific descriptors. That representation is not simply the three generic operands in `tu_instruction_t`. A true end-to-end ISA path would need a lowering or decode contract between those forms. Shared opcodes alone do not supply one.

Submission returns a positive command ID even though one header comment describes zero as success. The executable contract controls the chapter's examples, while the comment conflict is recorded as a documentation defect.

### Admission is not readiness

A successful submission reserves a record, copies dependency IDs, assigns a command ID, and may assign a signal ID. What happens next depends on queue mode.

- In **synchronous mode**, submission executes immediately. It does not check dependencies first.
- In **tick-driven mode**, submission invokes one automatic queue tick. That tick scans for pending entries whose dependencies satisfy the queue's policy.

Thus *synchronous* does not mean “wait until dependencies are satisfied.” At this pin, it means “execute in the submission call.” A missing dependency cannot delay synchronous work because the check is bypassed.

## 11.6 Dependency IDs: absent, faulted, and reset are different cases

The queue resolves dependencies by looking up command IDs and asking whether each found command equals `COMPLETED`.

Three cases must remain separate:

1. **Known completed ID:** readiness succeeds.
2. **Missing ID:** lookup treats it as already completed.
3. **Known faulted ID:** the record is found but is not equal to `COMPLETED`, so readiness never succeeds.

The missing-ID rule is fail-open. It may simplify external prerequisites, but it also means an unknown number does not prove that a real command existed and finished.

The faulted-ID rule is fail-stuck. The adversarial probe first submits unsupported `CONV2D`, which faults. A following NOP depends on that faulted ID and remains pending. A bounded two-cycle wait returns timeout, and the dependent remains pending. This is not exception propagation: the dependent does not become faulted because its prerequisite faulted. It simply never becomes ready.

Two other unknown-ID APIs fail open independently of dependency lookup. Asking status for an unknown command ID returns `COMPLETED`, and waiting on an unknown ID reports success. These outcomes do not prove that a command was ever admitted, executed, retired, reclaimed, or invalidated; they are lookup defaults. A caller that needs provenance must validate the handle and its queue epoch separately.

A hardware or runtime design has alternatives:

| Dependency-failure policy | Advantage | Cost or risk |
|---|---|---|
| treat missing as complete | simple external-prerequisite convention | stale or mistyped IDs become false success |
| reject missing at admission | catches handle errors early | requires complete registry/epoch knowledge |
| keep dependents pending after fault | preserves “only completed satisfies” rule | deadlock unless cancellation or timeout exists |
| propagate fault/cancel | bounded terminal behavior | more status states and fan-out traversal |
| allow explicit dependency predicates | expressive workflows | larger descriptors and verification state space |

For Tusim, the safe current conclusion is descriptive: absent IDs satisfy; retained faults do not; bounded waiting can time out. The chapter does not silently choose a replacement policy.

## 11.7 Completion, signaling, and reclamation are independent contracts

The queue exposes `PENDING`, `ISSUED`, `COMPLETED`, and `FAULTED` states. In the observed execution path, a ready command is marked issued, its handler is called, and then it is marked completed unless dispatch itself reports failure. No externally persistent issued interval is demonstrated. The queue increments `current_cycle` once per tick and completes a ready command within that executor call; it does not apply the scheduler's node costs or model operation service duration.

But three tempting inferences fail.

### Completion does not prove successful effects

The elementwise path demonstrates this directly. A public wrapper stores the caller's original `num_ops` in the descriptor, then clamps only a local loop variable. Queue execution forwards the stored count. The fused helper checks the count before copying operations or touching SRAM and safely rejects values above eight. The queue ignores that helper result and still marks the command completed:

```text
ELEMENTWISE_BOUNDARY count=9 status=2 completed=1 faulted=0
```

The earlier hypothesis of an operation-array overread was wrong and was rejected after deeper source tracing. The remaining defect is outcome propagation: queue `COMPLETED` does not mean the elementwise effect occurred.

### Signal allocation does not prove observation

Commands can receive increasing signal IDs, yet the audited registry remains unpopulated. The canonical records report `signal_count=0` in both synchronous and tick-driven probes. ID allocation therefore proves only an assigned number. It does not prove registration, firing, waiting, or delivery to another component.

This signal surface also does not bridge Chapter 10's descriptor DMA into command readiness. Descriptor-DMA records expose a separate signal-adjacent ID, but the audited call inventory finds no path from descriptor completion into command-queue dependency satisfaction or queue signal observation. Similar names across those two queue systems do not create a shared event fabric.

### Completion does not reclaim capacity

Completed and faulted records remain counted in queue depth. The focused queue suite's overflow test fills a synchronous queue with commands that have already completed and expects the next submission to fail. That is retained-lifetime capacity, not pending-only backpressure.

The normal tick-driven path likewise leaves completed records in place. Source contains a decrement branch guarded by synchronous mode, but synchronous submission has already executed entries before an ordinary tick can reclaim them. Consequently, an unbounded “sync until count reaches zero” operation is not a safe canonical probe under retained completed depth.

Retirement, reclamation, and invalidation are separate even when an implementation performs them together. This distinction is central:

```text
handler returned
    -> status recorded
    -> optional observer notified
    -> architectural effects made visible
    -> entry retired
    -> storage reusable
    -> old handle invalidated
```

Tusim demonstrates only selected arrows. It does not establish a reorder buffer or in-order retirement like the processors discussed by Smith and Sohi [SS95](../../references/foundations.md#ss95-superscalar-lifecycle-vocabulary).

## 11.8 A barrier name does not create fence semantics

A conventional fence contract defines which earlier and later operations are ordered and what *ordered* means—issue order, completion order, visibility, or all of them. RISC-V fences name predecessor and successor classes [RISCV26]. OpenCL queue barriers define event and queue behavior [OCL311]. These contracts cannot be imported into Tusim by terminology.

Submitting a barrier records its own ID as `last_barrier_id`, but gives the barrier no implicit dependencies on prior commands. Later command IDs are held only while a retained barrier remains incomplete. The adversarial sequence is:

```text
unsupported CONV2D       -> FAULTED
NOP depends on CONV2D    -> PENDING
bounded wait             -> timeout; NOP still PENDING
BARRIER                   -> COMPLETED
independent NOP after it -> COMPLETED
```

The retained summary is:

```text
ASYNC_BARRIER fault=3 pre=0 barrier=2 post=2 count=4 cycle=6
```

The barrier and later ready work complete while earlier work remains pending. Therefore this barrier is not a full fence over prior queue contents. In synchronous mode it executes immediately as a no-op.

A stronger barrier design would need an explicit contract. Options include:

- snapshot all prior live command IDs as dependencies;
- maintain a generation counter and prevent later generations from issuing;
- track an ordered queue head independent of command readiness;
- propagate prior faults into the barrier; or
- distinguish an execution barrier from a memory-visibility fence.

Each option costs storage, dependency fan-in, control complexity, or parallelism. The correct choice depends on whether the model is exploring runtime APIs, compiler schedules, or hardware issue structures.

## 11.9 Reset creates a new state but not a complete ID epoch

Reset clears entries, dependency storage, queue count, cycle state, counters, and barrier state. It restarts command IDs at one. It does **not** restart the next signal ID.

The probe records:

```text
RESET_IDS old_cmd=1 new_cmd=1 old_signal=1 new_signal=5
```

After reset, a stale pre-reset command handle with numeric ID one aliases the new command with ID one. Queue status lookup has no epoch component with which to distinguish them.

This is a general API lesson. Clearing storage and resetting an integer counter are different from invalidating external capabilities. Robust alternatives include:

- never reusing IDs within process lifetime;
- pairing IDs with an epoch or queue generation;
- returning opaque handles containing an index and generation;
- explicitly documenting that every reset invalidates all external handles; or
- retaining tombstones long enough to reject stale references.

The first alternative eventually faces integer wraparound; the others add bits, state, or caller obligations. Tusim's current command IDs should be treated as queue-epoch-local numbers, not globally unique identities.

## 11.10 The compiler scheduler is a separate analytical surface

The scheduler constructs a DAG from SRAM-region access summaries, computes mobility, and emits a list-scheduled operation sequence with fixed per-class node costs: one for DMA and four for every other emitted node. It is executable and has passing focused tests. It is not the command queue's runtime issue engine.

Several names overstate what their functions do.

### Barrier insertion counts hazards but inserts no node

A direct two-node hazard produces:

```text
SCHED_POSITIVE_INSERT direct=1 run=0 input_nodes=2 output_nodes=2
```

The analysis reports one candidate. It does not add an instruction to the graph. The full scheduling function later clears the reported insertion count.

### DMA hoisting counts candidates but does not move graph nodes

A three-node case produces:

```text
SCHED_POSITIVE_HOIST direct=1 run=0 input_nodes=3 output_nodes=3
```

The named hoist pass returns one, while graph IDs remain in their original positions. Actual output reordering can still occur because the list scheduler chooses among ready nodes with a DMA-priority rule. The precise claim is therefore: the named hoist function is report-only; list scheduling may reorder ready operations.

### Dependency fan-in is finite and silently truncated

Each scheduler node retains at most 16 predecessors and 16 successors. A barrier after 17 ordinary nodes builds successfully but keeps only 16 predecessor IDs:

```text
SCHED_DENSE_BARRIER prior=17 retained_preds=16 max_deps=16
```

The graph builder does not reject the missing edge. Finite fan-in is realistic, but silent truncation is dangerous because validation sees the truncated graph, not the intended full relation. Alternatives include rejecting construction, dynamically allocating edges, using barrier generations, or conservatively serializing dense regions.

### Cycle totals are estimates

The audited example emits:

```text
SCHED_BARRIER output=DMA.LOAD,NOP,BARRIER valid=1 hoisted=0 inserted=0 cycles=9
```

The total comes from fixed source costs accumulated by the list scheduler. It does not measure queue ticks, engine service, calibrated hardware cycles, or physical overlap. No equation in this chapter converts it into silicon time.

## 11.11 Configuration names do not prove active control

The full config declares and parses instruction width, queue depth, dependency checking, and cycle-model selection. Shipped JSON contains a 96-bit instruction width and a `cycle_accurate` label. Yet `tu_config_to_runtime()` omits these four fields, and top-level queue construction uses compile-time constants:

- queue depth: 16;
- dependency checking: disabled;
- queue mode: functional/synchronous at the tracked defaults.

This repeats Chapter 4's path rule:

```text
declared != defaulted != parsed != converted != consumed != effective
```

A queue-depth field can equal the compiled depth by coincidence. Matching values do not prove propagation. A future test must choose a discriminating value and observe the actual consumer.

Scheduler config has a related boundary. Default construction enables DMA hoisting and barrier analysis, while a null config disables them. Some fields, such as `pipeline_tiles` and `max_window`, appear in defaults, declarations, and tests but are not consumed by scheduling logic in `tu_scheduler.c` at this pin. The claim is deliberately file- and pin-bounded.

## 11.12 Worked lifecycle trace and reproducible evidence

This chapter uses a deliberate closing order: the worked trace and canonical verification establish concrete constraints before the alternatives table; operational failure modes then feed the compact fidelity synthesis. That evidence-first order is more useful here than asking the reader to compare transports before seeing which lifecycle predicates the current queue actually satisfies.

A compact trace makes the lifecycle vocabulary concrete. The canonical tick-driven probe starts with an empty queue, submits a ready NOP, ticks once more, and then submits a second NOP with a missing dependency ID. Submission itself performs the automatic ticks shown below.

| Step | Admission and dependency result | Status/effect | Queue cycle and storage | Signal/handle interpretation |
|---|---|---|---|---|
| create queue | no command admitted | no status | `current_cycle=0`, `count=0` | no handle |
| submit NOP with no dependencies | ID 1 admitted; vacuously ready | transiently `ISSUED`, then `COMPLETED` in the automatic tick | cycle 1, `count=1` | signal ID assigned; registry still empty |
| explicit tick | no pending ready entry | no new execution | cycle 2, completed entry still counted | ID 1 still resolves; storage not reclaimed |
| submit NOP depending on absent ID 999999 | ID 2 admitted; absent prerequisite defaults to complete | transiently `ISSUED`, then `COMPLETED` | cycle 3, `count=2` | another signal ID may be allocated; registry still empty |

The retained summary is:

```text
ASYNC_QUEUE count=2 submitted=2 completed=2 faulted=0 signal_count=0 current_cycle=3
```

This one trace crosses admission, readiness, issue, completion, signal allocation, lookup, and capacity. It also shows what is *not* present: no modeled service-duration interval, no observable signal event, no retirement, no reclamation, and no handle invalidation. A completed entry remains a live consumer of queue capacity. The separate fault/barrier trace in Section 11.8 changes only the dependency outcome and exposes the fail-stuck case.

The canonical retained run is:

```text
experiments/runs/ch11-instruction-contracts/20260728-ch11-canonical/
```

It was executed from input commit `2e9130b3ee12f1f90c24b8ba02b8424ad12bd208` and committed as evidence in `1f2c8b2dbc6912da29b462ccef5191ba5f59883d`.

To verify the retained bundle:

```bash
cd /home/zxy/Workplace/books/tusim-book/experiments/runs/ch11-instruction-contracts/20260728-ch11-canonical
sha256sum -c sha256-retained.txt
```

To execute a new isolated reproduction, keep the Tusim checkout detached and tracked/untracked-clean at the pinned commit and choose a fresh run ID. The runner refuses to overwrite the committed canonical directory:

```bash
cd /home/zxy/Workplace/books/tusim-book
CH11_RUN_ID="repro-$(date -u +%Y%m%dT%H%M%SZ)" \
  bash experiments/run_ch11_instruction_contract_audit.sh
```

The runner applies external 30-second timeouts to every audited executable. A reproduction creates a new retained directory; it does not rewrite the historical canonical run.

To rerun the pre-draft checks from the book root:

```bash
cd /home/zxy/Workplace/books/tusim-book
python3 experiments/ch11_predraft_validate.py
```

The canonical source audit reports:

```text
CH11_SOURCE_AUDIT PASS pin=e918c80b6fce833cd1fcae97730fa841c2176f25 hashes=26 predicates=96 checks=122
```

The retained evidence table is:

| Evidence | Observed result | Safe interpretation |
|---|---|---|
| command queue focused suite | 9/9 reported passed | named smoke cases pass; adversarial lifecycle still needs the probe |
| ISA focused suite | 9/9 reported passed | local size/name/query contract passes |
| ASM identity smoke | PASS | supported direct text path executes |
| scheduler focused suite | 14/14 reported passed | named DAG/list-schedule cases pass |
| custom probe | zero failures | exact expected defects and boundaries match the pinned snapshot |
| static linkage | five binaries checked | tests and probe use the rebuilt archive, not a stale shared library |
| retained manifest | 19 entries verify | copied inputs, logs, archive digest, and closed transcript are intact |

The runner uses a detached clean source at the exact pin, exports it into disposable storage, rebuilds the static archive, imposes external timeouts, copies all claim-critical inputs into the run, and verifies repository state after execution. Its terminal marker is intentionally:

```text
CH11_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS
```

That wording matters. Some expected findings are defects or missing contracts. Reproducing them is snapshot conformance, not a green correctness certificate.

## 11.13 Multi-objective instruction-transport choices

Tusim's adjacent surfaces can be interpreted as exploration points rather than one incomplete monolith. Several production directions are plausible.

| Direction | Performance/traffic | Area and power | Compiler/runtime | Verification |
|---|---|---|---|---|
| keep direct text ASM for tests | human-readable; parsing overhead irrelevant for small tests | minimal modeled hardware meaning | easiest debugging; poor binary deployment story | small grammar, but binding safety still matters |
| define a portable 96-bit binary ISA | compact fixed-width transport and simple indexing | decoder and validation logic required | stable encoder/decoder and compatibility policy | malformed streams, endianness, reserved fields, versions |
| use typed host descriptors only | rich operation-specific data without bit packing | software structure size can grow | convenient C API; ABI/version coupling | ownership, copying, pointer/extent validation |
| strengthen dependency/event queue | more asynchronous overlap and observability | ID tables, event state, fan-out, cancellation | explicit futures and failure propagation | state-space growth, reset epochs, deadlock tests |
| ordered ring with in-order retirement | simple in-order capacity reclamation; stale handles still need an explicit generation/reuse policy | head/tail and reorder constraints | predictable submission semantics | easier invariants, less out-of-order flexibility |
| graph scheduler emits queue descriptors | reuses offline dependency analysis | transport conversion and ID materialization | clearer compiler/runtime bridge | differential schedule-to-runtime tests |
| scheduler emits binary stream | compact deployment artifact | decoder plus runtime dependency machinery | strongest ISA/toolchain coupling | end-to-end encoding, decode, effects, and fault corpus |

Decoupled access/execute work illustrates why finite queues and synchronization can limit otherwise useful decoupling [SMI84](../../references/foundations.md#smi84-decoupled-accessexecute). Gemmini is a contrasting example of evaluating a deliberately connected full stack [GEN21](../../references/foundations.md#gen21-gemmini). Neither source proves that Tusim implements those contracts; they identify integration questions and evidence types for future variants.

There is no universally best choice.

- A research C model prioritizing fast architecture iteration may retain typed descriptors and separate analytical scheduling.
- A driver/runtime prototype benefits from opaque generation-tagged handles, explicit failure propagation, and bounded reclamation.
- RTL co-design requires a normative encoding, finite-resource policies, and visibility semantics.
- A compiler study may prefer an explicit intermediate representation and only lower into queue descriptors at a late boundary.

The decision must name the fidelity target. Adding a decoder does not automatically improve timing fidelity. Adding event states can improve software-contract realism while increasing control state and verification cost. Enforcing in-order retirement simplifies capacity but may hide useful out-of-order execution regimes. Retain materially different variants when they answer different architecture questions.

## 11.14 Failure modes and safety boundaries

### False-integration failure modes

1. Counting opcode names and calling the count “supported instructions.”
2. Treating a packed C object as a wire format.
3. Calling text ASM a decoder for the packed object.
4. Treating shared opcode numbers as a complete lowering contract.
5. Calling the compiler scheduler the queue's issue engine.
6. Treating a `BARRIER` label as proof of fence semantics.
7. Treating `COMPLETED` as proof of successful effects, notification, and reclamation.
8. Treating a parsed config value as an effective runtime control.
9. Treating fixed estimated cycles as measured time.
10. Treating reset as safe handle invalidation merely because storage was cleared.

### Static safety boundaries

The canonical run deliberately avoids cases that are uncontrolled or potentially nonterminating:

- low-level submission with `num_deps > 0` and `dep_ids == NULL`;
- unchecked allocation-failure branches;
- legacy ASM's 17th binding/weight path;
- host-buffer accesses after extent information has been discarded; and
- unbounded queue draining while completed records remain counted.

These are source findings, not executable demonstrations. A sanitizer-only crash is not required to justify a caller precondition when static control flow already exposes undefined access.

### Designing better probes

A discriminating probe should:

1. force a state the ordinary tests do not cover;
2. use a bounded loop or external timeout;
3. assert exact state, count, and order—not merely print them;
4. avoid adding cleanup calls that erase the state under study;
5. distinguish a safe rejection from a successful effect;
6. retain source and artifact hashes; and
7. phrase success as matching an expected snapshot, especially when reproducing a defect.

The elementwise correction is a model example. Initial source inspection suggested an overread. Following the complete call chain found an early bounds rejection. The probe then targeted the real boundary: rejected effect but completed queue status.

## 11.15 Fidelity box

**Executable at the pinned revision**

- expanded ISA metadata helpers and native object layout;
- legacy ASM's supported direct-operation grammar;
- the command queue's eight-operation dispatch subset;
- synchronous and tick-driven queue transitions exercised here;
- scheduler DAG/list-schedule APIs and fixed-cost outputs.

**Integrated only within named paths**

- core/cluster wrappers to legacy ASM;
- core/DPI wrappers to selected queue submissions;
- command dispatch to selected direct C-model operations.

**Analytical or estimated**

- scheduler fixed cycle totals;
- any inferred overlap or priority benefit absent calibrated timing.

**Not established**

- portable binary encoding or runtime binary stream;
- compiler-to-scheduler-to-queue integration;
- full expanded-opcode execution coverage;
- conventional fence, event, or retirement semantics;
- generation-safe command handles;
- full-config control of global queue construction;
- RTL, FPGA, or silicon timing calibration.

**Known snapshot defects/boundaries**

- missing IDs satisfy dependencies;
- faulted dependencies leave consumers pending;
- unknown status/wait is fail-open;
- completion does not reclaim capacity;
- signal registry remains empty;
- barrier is weaker than a full fence;
- command IDs alias across reset;
- elementwise rejection is recorded as queue completion;
- scheduler candidate counts are cleared and dense edges truncate at 16.

## Development questions

1. Should queue handles include a generation field, and what wraparound policy is acceptable?
2. Should a fault cancel dependents, propagate failure, or require an explicit predicate?
3. Which visibility domain should a queue barrier order: command issue, command completion, SRAM effects, host memory, or signals?
4. Should completion status carry handler-specific errors rather than a binary completed/faulted dispatch result?
5. Is the 96-bit object intended to become a portable ISA, or should it remain an in-process IR?
6. Should the scheduler emit queue descriptors, a binary stream, or only analysis reports?
7. Should dense dependency overflow reject, allocate dynamically, or lower into barrier generations?
8. Which config object is authoritative for queue and scheduler construction?
9. What external reference—RTL, FPGA, or another simulator—should calibrate cycle costs?
10. Which end-to-end test can prove encode/lower, transport, execute, signal, retire, reclaim, and invalidate as separate gates?

## Summary

Tusim's instruction-related code is not one pipeline. The expanded ISA provides a packed in-process representation and metadata that compiler-side analyses such as scheduling and liveness can consume; the legacy ASM is a small direct text interpreter; the command queue is a subset dispatcher with its own lifecycle; and the scheduler is a separate analytical graph tool. Shared names do not prove runtime integration.

The queue makes lifecycle distinctions concrete. Synchronous submission bypasses dependencies. Missing IDs are treated as complete, while retained faults leave dependents pending. Completion does not imply successful effects, signal delivery, retirement, or storage reclamation. The barrier does not order all prior work, and reset reuses command IDs without an epoch.

The scheduler reinforces the same evidence discipline. Candidate-count functions do not perform the transformations implied by their names, fixed cycle totals are estimates, and dependency storage silently truncates beyond 16 edges.

The transferable method is to audit every arrow: representation, encoding, parser, admission, readiness, dispatch, effect, completion, notification, and reclamation. Only after those contracts exist should a diagram connect the surfaces.

## Review questions

1. Why does a 12-byte packed `tu_instruction_t` not establish a portable 96-bit binary ISA?
2. Why are 59 explicit operation enumerators, 68 named slots, and eight queue-dispatched classes all valid but different counts?
3. How does synchronous submission differ from dependency-ready tick-driven execution?
4. What is the behavioral difference between a missing dependency ID and a retained faulted dependency ID?
5. Why does the nine-operation elementwise probe disprove “completed means effect succeeded” without proving an overread?
6. Which contracts and evidence would be needed before calling Tusim's queue barrier a full fence?
7. How can reset create stale-handle aliasing even though queue storage is cleared?
8. What do the positive barrier-insertion and DMA-hoist probes reveal about scheduler API names?
9. Why can a 16-edge cap invalidate an intended barrier even when graph validation passes?
10. What evidence would be required to connect the ONNX compiler, expanded ISA, scheduler, queue, and operation implementations into one supported path?

### Review-question answer key

1. C packing is ABI-local; a portable ISA also requires normative fields, byte order, legality, versioning, encoder/decoder behavior, stream framing, and a consumer.
2. They count enum declarations, non-unknown name-table entries including reserved names, and implemented dispatcher cases. They measure different surfaces.
3. Synchronous submission calls execution immediately and skips dependency checks. Tick-driven mode admits the entry and uses ticks to evaluate readiness.
4. Missing IDs are treated as already completed. A found `FAULTED` entry is not equal to `COMPLETED`, so its dependent remains pending.
5. The fused helper rejects above eight before copying or SRAM access, but the queue ignores the return and records completion. It proves status/effect mismatch, not memory unsafety in that path.
6. The contract must define the ordered predecessor/successor sets and whether ordering applies to issue, completion, visibility, signaling, or reclamation, then implement and test that relation.
7. Reset restarts command numbering at one. A stale numeric ID can therefore resolve to a new command unless the handle includes or implies an epoch.
8. Both direct functions can return positive candidate counts without modifying the graph, and the full scheduler clears those counts. Names must not substitute for output comparison.
9. The 17th intended predecessor is silently absent from the stored graph, so validation checks a weaker relation than the caller requested.
10. It would require explicit lowering/encoding, decode or descriptor construction, exact call edges, dependency and error contracts, end-to-end tests for effects/status/signals/reclamation, and versioned artifact rules.

## Design exercises

1. **Generation-tagged handles.** Design a 32-bit handle partitioned between slot and generation. Analyze queue depth, wraparound time, comparison logic, reset behavior, and stale-handle tests.
2. **Fault propagation.** Specify three policies for a command whose dependency faults. Compare deadlock risk, cancellation traffic, deterministic replay, software ergonomics, and hardware state.
3. **Fence taxonomy.** Define separate issue, completion, SRAM-visibility, and host-visibility barriers. State predecessor/successor sets and construct one litmus test for each.
4. **Portable encoding.** Convert the local 12-byte object into a normative 96-bit format. Define endianness, reserved encodings, malformed-stream behavior, and forward compatibility.
5. **Outcome propagation.** Redesign elementwise dispatch so helper rejection reaches queue status. Decide whether status stores a generic fault, operation-specific code, or both.
6. **Capacity and retirement.** Compare retained-lifetime records, in-order ring retirement, reference-counted events, and explicit release. Quantify storage and identify observability lost by each policy.
7. **Dense scheduler graph.** Replace silent 16-edge truncation with rejection, dynamic edges, or generation barriers. Evaluate complexity, memory, schedule quality, and verification burden.
8. **Compiler/runtime bridge.** Define an IR-to-queue lowering contract for MMA, DMA, and elementwise operations. Include descriptor ownership, dependency IDs, reset epochs, and unsupported-op handling.
9. **Configuration propagation test.** Choose non-default queue depth and dependency-checking values. Design a source→parser→converter→constructor→effect test that cannot pass by value coincidence.
10. **Calibration plan.** Propose an RTL or FPGA trace interface that could calibrate scheduler costs and queue ticks without assuming that their current cycle domains are compatible.

## Primary references

- [RISCV26](../../references/foundations.md#riscv26-risc-v-unprivileged-isa) RISC-V International, *The RISC-V Instruction Set Manual, Volume I: Unprivileged Architecture*, ratified snapshot `20260120`.
- [SS95](../../references/foundations.md#ss95-superscalar-lifecycle-vocabulary) James E. Smith and Gurindar S. Sohi, “The Microarchitecture of Superscalar Processors,” 1995, [DOI 10.1109/5.476078](https://doi.org/10.1109/5.476078).
- [TOM67](../../references/foundations.md#tom67-dependency-driven-scheduling) Robert M. Tomasulo, “An Efficient Algorithm for Exploiting Multiple Arithmetic Units,” 1967, [DOI 10.1147/rd.111.0025](https://doi.org/10.1147/rd.111.0025).
- [OCL311](../../references/foundations.md#ocl311-opencl-command-queue-contract) Khronos OpenCL Working Group, *The OpenCL Specification*, version 3.1.1.
- [SMI84](../../references/foundations.md#smi84-decoupled-accessexecute) James E. Smith, “Decoupled Access/Execute Computer Architectures,” 1984, [DOI 10.1145/357401.357403](https://doi.org/10.1145/357401.357403).
- [GEN21](../../references/foundations.md#gen21-gemmini) Hasan Genc et al., “Gemmini: Enabling Systematic Deep-Learning Architecture Evaluation via Full-Stack Integration,” 2021, [DOI 10.1109/DAC18074.2021.9586216](https://doi.org/10.1109/DAC18074.2021.9586216).

Full verified metadata and conservative safe-use scopes are maintained in [`../../references/foundations.md`](../../references/foundations.md).
