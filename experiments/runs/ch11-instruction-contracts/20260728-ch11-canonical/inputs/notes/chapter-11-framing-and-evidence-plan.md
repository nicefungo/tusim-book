# Chapter 11 Framing and Evidence Plan — Instruction Surfaces and Command-Queue Ordering

- **Edition:** Tusim `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Book workspace:** `/home/zxy/Workplace/books/tusim-book`
- **Source workspace:** `/home/zxy/Workplace/projects/tusim` (detached, clean, read-only)
- **Status:** skeptical findings incorporated; drafting blocked pending execution-input commit, canonical evidence sealing, and pre-draft validation

## Why this chapter follows Chapter 10

Chapter 10 separated descriptor representation, admission, executor outcome, observation, and retirement. The next prerequisite is not another memory subsystem: it is the control contract that is supposed to name operations and order them.

```text
Chapter 4: declared configuration versus active control state
        ↓
Chapter 5: global ownership, lifecycle, and reset
        ↓
Chapters 6–10: executable compute, numerical, storage, and transfer contracts
        ↓
Chapter 11: instruction representation → executable surface → ordering → observation
```

The chapter asks whether an operation's presence in an opcode catalog, text language, queue alias, scheduler model, or public wrapper actually provides one coherent executable instruction contract.

## Ranked candidate boundaries

| Rank | Candidate | Reader-decision coherence | Evidence cohesion | Disposition |
|---:|---|---|---|---|
| 1 | **Instruction Surfaces and Command-Queue Ordering** | choose the actual executable surface and state only the ordering/lifecycle guarantees it demonstrates | expanded ISA, legacy ASM, command queue, wrappers, and scheduler all meet at the representation→execution boundary | **selected** |
| 2 | Expanded ISA and Binary Encoding | narrower, but the pin has a packed C object and metadata rather than a binary encoder/decoder or runtime binary consumer | strong declaration evidence but weak execution story | rejected as too declarative; retained as one surface |
| 3 | Command Queues, Dependencies, and Barriers | coherent queue lifecycle decision | would hide the independent ASM and scheduler surfaces that make “ISA support” ambiguous | rejected as too narrow |
| 4 | Compiler Scheduling and Automatic Overlap | asks policy/performance questions unsupported by the executable path | scheduler is library-linked and focused-tested but not fed by the compiler/ASM/queue; overlap is not established | deferred |
| 5 | DRAM, Address Generation, or Double Buffering | each is a separate memory/performance decision | Chapter 10 explicitly found incompatible consumers and clocks | deferred |

## Reader decision

> Given an operation and an ordering requirement, which pinned Tusim surface—expanded ISA metadata, legacy text ASM, command queue, public wrapper, or standalone scheduler—can represent it, which surface actually executes it, and what do command IDs, dependencies, barriers, signals, queue depth, timestamps, and completion status prove before storage may be reused?

The reader must be able to reject three common substitutions:

1. an enum entry is not an executable instruction;
2. a completed command is not necessarily retired from queue storage;
3. a valid scheduled sequence is not automatically consumed by the runtime.

## In scope

1. The 96-bit packed `tu_instruction_t` object, opcode catalog, flags, category/query metadata, and native byte layout.
2. Exact distinction among explicit operation enumerators, named table slots, reserved labels, and unknown slots.
3. Absence of a binary encoder/decoder and absence of a runtime binary-instruction consumer.
4. The legacy six-mnemonic text ASM parser and its direct global-wrapper execution path.
5. The command queue's exact operand union and executable switch cases.
6. Command construction, submission return, pending/issued/completed/faulted labels, dependency lookup, barrier state, signal allocation, waiting, queue depth, reset, and destruction.
7. Synchronous versus auto-ticked mode, including the distinction between execution and storage retirement.
8. Parsed queue/cycle/dependency configuration versus compile-time initialization.
9. Standalone scheduler reachability and bounded correctness claims: access analysis, DAG output, barrier ordering, reported counts, and fixed-cost estimates.
10. Focused and aggregate test coverage, fail-closed probe results, static linkage, and safe caller subsets.

## Explicitly deferred

- Scheduler/liveness redesign or compiler integration.
- Physical issue width, functional-unit occupancy, overlap, out-of-order retirement, interrupts, coherence, or calibrated timing.
- Complete semantics of convolution, attention, normalization, sparsity, and other cataloged operation families.
- Binary wire-format portability, endianness policy, versioning, malformed-stream security, and RTL decode.
- DRAM calibration, address-generator mathematics, double buffering, and valid DMA/compute overlap.
- Production ONNX lowering, host fallback, and generated-program repair.

Boundary probes can reject unsupported claims without promoting deferred subsystems into the chapter.

## Source map

| Surface | Authoritative pinned files | Safe question |
|---|---|---|
| Expanded ISA object/catalog | `tu_cmodel/isa/tu_isa.[ch]` | what values, fields, names, and metadata are declared? |
| Queue types and executor | `tu_cmodel/command_queue.[ch]` | what operand forms and opcodes execute, and what lifecycle state changes? |
| Public queue/global wrappers | `tu_cmodel/tu_cmodel.[ch]`, `tu_cmodel/bindings/tu_dpi.c` | what is runtime/DPI-reachable and how is queue mode selected? |
| Legacy text ASM | `tu_cmodel/tu_asm.c`, `tu_cmodel/tu_core.c`, `tu_cmodel/tu_cluster.c`, `tests/test_asm.c`, `docs/TU_ASM.md` | what text actually parses and which direct/core/cluster wrappers execute? |
| Scheduler | `tu_cmodel/isa/tu_scheduler.[ch]`, `tests/test_scheduler.c`, `tests/test_scheduler_sweep.c` | what sequence transformation/report is locally modeled, and is it consumed? |
| Full config | `tu_cmodel/infra/config.[ch]`, shipped JSON/YAML | what queue/ISA fields parse, validate, convert, and activate? |
| Compiler | `compiler/onnx_to_tu.py` | whether binary ISA or scheduler output is emitted/consumed |
| Build/tests | `Makefile`, four focused tests | archive membership, focused/aggregate/quick gates, and linkage risk |

External sources motivate separation of architectural naming, dependency readiness, ordering, and full-stack integration. They do not validate Tusim behavior. A verified compact source map will be added after metadata review.

## Initial executable evidence plan

Canonical runner: `experiments/run_ch11_instruction_contract_audit.sh`

Canonical run target: `experiments/runs/ch11-instruction-contracts/20260728-ch11-canonical/`

The earlier development run was removed after review because it no longer sealed the corrected inputs and must not be treated as evidence.

### Fail-closed gates

1. Require exact Tusim pin, detached/clean source, zero book remotes, and unchanged source state before/after.
2. Build only a `git archive` extraction.
3. Enforce 26 exact source/test/compiler/config hashes plus a mechanically counted structural/reachability predicate set (96 in the current audit), totaling 122 checks.
4. Require `command_queue.o`, `tu_asm.o`, `tu_isa.o`, and `tu_scheduler.o` in the static archive.
5. Compile the custom probe and focused command-queue, ISA, ASM, and scheduler tests explicitly against `libtucmodel.a`.
6. Reject any audited binary that resolves `libtucmodel.so`.
7. Preserve literal family logs, complete transcript, archive digest, and retained hashes.
8. Do not call the known nonterminating tick-driven `tu_cmdq_sync()` path after completed commands remain counted.
9. Copy every claim-critical book-side input into the retained bundle and verify a run-relative post-close manifest.
10. Run each bounded executable under an external timeout.

### Discriminating probes

- Exact ISA object size, native byte sequence, named/unknown slot counts, and reserved-slot metadata behavior.
- Synchronous submission with a nonexistent dependency.
- Tick-driven submission auto-tick and nonexistent-dependency behavior.
- Completion versus queue-depth retention in both modes.
- Signal ID allocation versus empty signal registry.
- A retained fault, an earlier command pending on that fault, a barrier, and a later command: the barrier and later command complete while the earlier command remains pending.
- Unknown command status/wait behavior.
- Unsupported cataloged `CONV2D` fault through queue dispatch.
- Lifetime-capacity saturation after completed/faulted commands.
- Scheduler sequence containing `NOP; BARRIER; DMA.LOAD`.
- Scheduler report-count reset and non-inserting barrier analysis.
- Positive direct barrier-analysis and DMA-hoist counts versus zeroed full-run reports.
- A 17-predecessor scheduler barrier that silently retains only 16 edges.
- Nine-operation elementwise admission, downstream bounded rejection, and queue `COMPLETED` status.
- Legacy text-ASM rejection of expanded `BARRIER`.

## Skeptical-review gates

### Architecture/methodology

- Are declaration, serialization, parsing, decode, dispatch, execution, completion, and retirement separate?
- Is every ordering term operationally defined?
- Are missing dependencies and unknown IDs treated fail-closed or fail-open?
- Do barriers order both prior and subsequent operations on every claimed path?
- Does queue capacity count live work, retained history, or lifetime submissions?
- Are signal creation, registry insertion, firing, observation, and reclamation separately proven?

### Repository/reachability

- Are operation counts and executable subsets derived mechanically from the pin?
- Which compiler/ASM/queue/scheduler surfaces actually call one another?
- Are config fields traced to queue construction rather than merely parsed?
- Do focused tests distinguish the defects exposed by the custom probe?
- Is every execution isolated from the pinned source checkout and statically linked?

### Editorial/evidence

- Does “96-bit instruction” avoid implying a portable byte-stream encoder?
- Does “68 named slots” avoid becoming “68 executable operations”?
- Are `COMPLETED`, signal-fired, wait-success, and storage-retired kept distinct?
- Are scheduler cycle sums labeled fixed-cost analytical values, not overlap timing?
- Are known nontermination and unsafe paths kept static or bounded?

The two independent pre-draft reviews returned `BLOCK`; their findings are resolved or bounded in `notes/chapter-11-skeptical-review-dispositions.md`. Drafting remains blocked until the corrected inputs are committed, the canonical run is sealed, and the pre-draft validator passes.
