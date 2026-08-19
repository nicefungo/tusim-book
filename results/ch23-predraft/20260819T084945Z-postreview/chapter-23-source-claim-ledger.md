# Chapter 23 Source–Claim Ledger

Pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`

Claim states: **allow** = supported for framing; **qualified** = usable only with the listed limit; **block** = must not appear as a positive manuscript claim.

| ID | Proposed claim | Whole-path primary evidence | Counterevidence / stop edge | State |
|---|---|---|---|---|
| C23-01 | Extension readiness is conjunctive across declaration, ingress, retention, consumer, observable, verification, ownership, and docs. | Cross-path comparison below; exact-pin runner emits every class and its weakest edge. | This is the chapter's analytical rule, not a repository-provided guarantee. | allow |
| C23-02 | Core geometry has a live config-to-runtime conversion path. | `tu_cmodel/infra/config.h`; `tu_cmodel/infra/config.c` `tu_config_to_runtime()`; `tu_cmodel/tu_cmodel.c` initialization. | Canonical disposable `make test-config` aborts with stack smashing, while independent layouts have passed; root cause is unresolved and layout-sensitive. | qualified |
| C23-03 | A parsed config field is not necessarily an effective runtime knob. | `infra/config.c` parses dataflow, pipeline depth, and DMA width; `tu_config_to_runtime()` omits them. | Defaults/direct APIs can still affect some corresponding behavior through other ingress paths. | allow |
| C23-04 | WS, OS, and RS are linked, registered, selectable by direct API, and consumed through `tu_dataflow_execute_mma()` and the selected vtable. | `Makefile` TU_OBJS/rules; three call sites across `tu_cmodel.c` and `attention_engine.c`; registry/dispatcher and three implementations; fresh focused 9 passed/0 failed. | Global registry/core ownership; selection by JSON config is dropped; core wrappers can restore snapshot selection. | qualified |
| C23-05 | NLR is an integrated dataflow plugin. | Enum/docs mention ID 3 and NLR. | No NLR constructor, Make object, registration, or focused implementation; selecting the ID falls back to WS and returns success. | block |
| C23-06 | The registry is an open dynamic plugin ABI. | Registry API and eight-slot array. | Implementations are statically linked/registered; ownership is global; duplicate registration retains the first stable pointer and frees the newly created instance; capacity overflow returns silently without freeing the submitted pointer or reporting status. | block |
| C23-07 | The expanded ISA header defines 59 explicit assigned opcode members. | `tu_cmodel/isa/tu_isa.h`; hash-pinned regex count; `tu_isa.c`; `tests/test_isa.c`. | `TU_ISA_OPCODE_COUNT` is not counted; declaration/metadata is not execution. | qualified |
| C23-08 | The command queue executes eight distinct `TU_CMD_*` cases. | `tu_cmodel/command_queue.c` `execute_command()`; `tests/test_command_queue.c`; fresh 9/9. | Header aliases include operations such as pool that lack an execution case; other engines may be callable outside the queue. | allow |
| C23-09 | Every declared/aliased ISA opcode is executable through the command queue. | Header aliases and catalog may suggest breadth. | Eight dispatch cases versus 59 explicit enum members; default faults unknown opcodes. | block |
| C23-10 | Cycle-model source presence means production runtime integration. | `tu_cmodel/perf/cycle_model.[ch]`, `tests/test_cycle_model.c`. | Absent from `TU_OBJS`, no Make rule/test target, no demonstrated production consumer. | block |
| C23-11 | Python exposes a direct ctypes route to selected core operations. | `bindings/python/tu_bindings.py`: library load, signatures, DMA/MMA/sync, `quick_gemm`; fresh identity GEMM smoke passes. | The smoke does not exercise `config_path` or report stubs; no Make/CI owner. | qualified |
| C23-12 | Python `config_path` configures the C model. | Parameter and `_config_path` assignment. | Constructor calls `tu_init()` and never passes the path or calls `tu_init_from_file`. | block |
| C23-13 | Python performance and power reports are live bindings. | Methods exist. | Both return advisory stub strings. | block |
| C23-14 | Documentation accurately states all runtime and dataflow support. | Runtime/config, dataflow, ISA, and binding docs are hash pinned. | “all parameters,” four-mode dataflow, expanded ISA, and “production-grade” labels exceed live paths. | block |
| C23-15 | The repository demonstrates a nontrivial ONNX compile-link-run-oracle path. | Compiler and two ONNX fixtures exist; Make has `test-compiler`/`test-full`. | `test-full` suppresses build/run failures with `|| true`; no contained far-boundary oracle; active compiler smoke cannot start without NumPy. | block |
| C23-16 | Chapter 23 may discuss compiler/runtime/ONNX integration positively. | None sufficient at this pin. | Trigger requires a contained nontrivial model to compile, generated output to link and run without suppressed status, and far-boundary results to match an independent oracle. | block |
| C23-17 | A dedicated sweep target and printed comparison are sufficient promotion evidence. | `tests/test_dataflow_sweep.c`; `Makefile` target; exploration documentation; fresh target execution. | Fixed workload/seeds; all three labeled core runs effectively restore WS; local formulas; absent aggregate owner; mismatch checks never propagate to exit status. | block |

## Promotion triggers

| Surface | Minimum new evidence needed to strengthen the current claim |
|---|---|
| Configuration | Green fresh config test plus a probe showing the named field changes the intended downstream consumer/observable, not merely the parsed struct. |
| Dataflow NLR | Implementation, build owner, registration, direct and config ingress, differential observable, focused tests, and lifecycle/ownership evidence. |
| Opcode | Encode/parse or submission ingress, descriptor retention, queue/runtime dispatch, observable semantics, negative/error behavior, and differential verification. |
| Module | Production archive/target owner, production caller, lifecycle contract, observable behavior, and integration test. |
| Sweep | Parameter manifest, mechanism-reachability control, independent oracle/invariants, mismatch-to-status propagation, aggregate/CI owner, retained raw rows, and documentation tied to the exact run. |
| Python binding | Config path passed to a live C initializer; callable signatures for reports; packaged test owner; independent numeric check. |
| Compiler/runtime/ONNX | One contained nontrivial fixture whose compile, generated-code build, execution, and independent far-boundary comparison all fail closed. |

## Exact evidence inputs

The canonical runner hashes 34 source/doc/model inputs. Key line anchors are:

- `tu_cmodel/infra/config.c`: parsing helpers and `tu_config_to_runtime()`;
- `tu_cmodel/tu_cmodel.c:23-29,97-101`: constructors, registration, initial selection;
- `tu_cmodel/compute/dataflow/dataflow_registry.c`: eight slots and ownership behavior;
- `tu_cmodel/compute/dataflow/dataflow_dispatcher.c`: vtable consumer and stats;
- `tu_cmodel/isa/tu_isa.h:44-123`: catalog;
- `tu_cmodel/command_queue.c:53-151`: executable dispatch and default fault;
- `Makefile:16-48,159-173,503-551`: archive ownership, plugin objects, compiler targets/status suppression;
- `tests/test_dataflow_sweep.c:34-70,73-192`: fixed inputs, direct mechanism path, comparison checks, local formulas, printed findings, and unconditional success;
- `compiler/onnx_to_tu.py:612-625,673-688`: host fallback emission and stubs;
- `bindings/python/tu_bindings.py:255-274,410-418`: stored config path, initializer, report stubs.

Machine output is authoritative over this prose for counts and fresh result status. Any source-hash drift invalidates the ledger until reconnaissance is rerun and reviewed.
