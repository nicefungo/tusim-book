# Chapter 11 — Instruction Surfaces and Command-Queue Ordering

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-11)

> **Historical case study.** Native layout, queue, barrier, scheduler and test observations below are from the July 28, 2026 audit at the July 25 source pin `e918c80b6fce833cd1fcae97730fa841c2176f25`. They were not re-established at `7a094ff`. Descriptor DMA scheduling is not a queue fence contract.

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

Smith and Sohi use related distinctions when describing superscalar pipelines [SS95](../../../../references/foundations.md#ss95-superscalar-lifecycle-vocabulary). Tomasulo's algorithm shows why operand readiness and issue are separate decisions [TOM67](../../../../references/foundations.md#tom67-dependency-driven-scheduling). OpenCL makes queued, submitted, running, complete, event, and barrier contracts explicit [OCL311](../../../../references/foundations.md#ocl311-opencl-command-queue-contract). These sources provide vocabulary, not evidence that Tusim implements those machines or APIs.

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

RISC-V is a useful contrast because its unprivileged specification defines instruction fields and fence predecessor/successor sets normatively [RISCV26](../../../../references/foundations.md#riscv26-risc-v-unprivileged-isa). Tusim's packed object is local C representation evidence. The chapter therefore labels it **source-present metadata**, not a validated wire ISA.

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

Decoupled access/execute work illustrates why finite queues and synchronization can limit otherwise useful decoupling [SMI84](../../../../references/foundations.md#smi84-decoupled-accessexecute). Gemmini is a contrasting example of evaluating a deliberately connected full stack [GEN21](../../../../references/foundations.md#gen21-gemmini). Neither source proves that Tusim implements those contracts; they identify integration questions and evidence types for future variants.

There is no universally best choice.

- A research C model prioritizing fast architecture iteration may retain typed descriptors and separate analytical scheduling.
- A driver/runtime prototype benefits from opaque generation-tagged handles, explicit failure propagation, and bounded reclamation.
- RTL co-design requires a normative encoding, finite-resource policies, and visibility semantics.
- A compiler study may prefer an explicit intermediate representation and only lower into queue descriptors at a late boundary.

The decision must name the fidelity target. Adding a decoder does not automatically improve timing fidelity. Adding event states can improve software-contract realism while increasing control state and verification cost. Enforcing in-order retirement simplifies capacity but may hide useful out-of-order execution regimes. Retain materially different variants when they answer different architecture questions.

[Next: Chapter 12 — Multi-Core Clusters and Interconnect Heuristic Estimates](12-multi-core-clusters-and-interconnect-heuristics.md)
