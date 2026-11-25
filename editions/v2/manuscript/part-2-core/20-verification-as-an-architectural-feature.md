# Chapter 20 — Verification as an Architectural Feature

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-20)

`make test` finished with “All tests complete.” Did it run the assembler test? **Yes**, even though `tests/test_asm.c` appears in no rule's prerequisites. Did it run the dataflow sweep? **No**, even though the sweep has a working target and the aggregate ran a different dataflow test. Did the configuration test select output-stationary? That last question cannot be answered by counting targets. We have to look inside the running model. These are the S13 launch records. S16 checked static membership live, not these aggregate executions.

These questions distinguish three kinds of evidence: **membership** in a build graph, **execution** of a particular command, and **sensitivity** to a defect. By the end of this chapter you should be able to reconstruct all three, decide which one a result is missing, and design a control that would expose the gap. All present-tense Tusim results below refer to public commit `7a094ff6c5527eff8e4318de676f0c0221c448b4`. The reproduction guide identifies the source bytes, exact commands, raw outputs and exit statuses.

## 20.1 What would make the claim false?

Suppose a change always chooses weight-stationary, whatever the JSON file requests. A GEMM using that implementation may still return the correct matrix: the choice of dataflow is not supposed to change the mathematical operation. Adding more correct matrix examples need not expose the defect. An active plug-in ID would distinguish the two choices, but an ID alone could describe a plug-in that was never called. A useful test checks both the selected object in the state that will execute and an observable consequence of its use.

This is a design constraint. The model must expose enough state to distinguish its implementations; the test must bracket the operation that uses that state; and the runner must carry a failure back to the caller. A practical test contract fits in one sentence: *on this input, through this entry point, this observation must agree with this reference; otherwise this command fails*. Write the sentence before choosing a test. “GEMM works” does not tell us which operands to choose, where to read the answer, or whether a transpose should fail.

## 20.2 Count relations, not files with similar names

Start with a repeatable source universe. Here it is the **120** regular files matching `tests/test_*.c`. There are **132** C files immediately under `tests/`; the other twelve include exploration programs and a fault fixture. They remain in the inventory, outside the named-test denominator. Scripts, headers, golden data and tests elsewhere are not missing C programs under this definition.

| Inspect the public Makefile | Count | Unit being counted |
|---|---:|---|
| Explicit rule heads named `test` or beginning `test-` | 124 | Distinct targets, including the two aggregates; 123 if the bare `test` is excluded. |
| Targets with a named C test prerequisite | 118 | Targets, **not** distinct source files. |
| Named C test sources on those prerequisite lists | 116 | Distinct paths among the 120. |
| Targets whose compiler recipe takes a named C test source | 119 | Compiler actions owned by distinct targets, whether selected or not. |
| Distinct named C test sources in those compiler recipes | 117 | After resolving the first prerequisite (`$<`) and literal recipe inputs. |

Four sources account for the gap between 120 and 116: `tests/test_asm.c`, `tests/test_cycle_model.c`, `tests/test_double_buffer.c` and `tests/test_int8_sweep.c`. The assembler recipe names its input literally, links `test-asm-bin`, then runs `./test-asm-bin`. The other three have no such compiler recipe in the root Makefile. `test-double` appears in `.PHONY`, but has no explicit rule body: asking Make for that name is not a double-buffer test. Conversely, two explicit rules can compile the **same** source. `test-softmax-exp-policy-internal` compiles the same file as `test-softmax-exp-policy` with `-DTU_TEST_EXP_INTERNAL`. Both belong in a target census; the source belongs in a file census once.

## 20.3 From selected members to completed commands

The prerequisites of `test` do not all appear on the long `test:` line. Seven members come from earlier rules headed `test test-quick:`. We collected the union across all the rules and checked it against GNU Make's expanded database. Then we **ran** each aggregate, serially, forcing rebuilds so an up-to-date binary could not masquerade as a new execution. A recording recipe shell invoked `/bin/sh`, preserved each command's streams and exit status, and let Make apply its usual failure rules. For every launched C test we matched the binary name to a successful compiler command from that same run. The Python generation test has its own entry; its internal compiler, probes and generator subprocesses are not extra top-level test launches.

| Observed in separate runs | `test` | `test-quick` |
|---|---:|---:|
| Direct member targets selected / reached | 60 / 60 | 36 / 36 |
| Selected members not reached | 0 | 0 |
| Top-level test commands completed (C launches + Python test) | 60 + 1 | 36 + 1 |
| Distinct named C test sources behind those launches | 58 | 34 |
| Named C test sources **not** launched by this aggregate | 62 | 86 |
| Make exit status | 0 | 0 |

There were 60 selected member targets but 61 top-level invocations: one member launched twice. The distinct C-source count is lower because one member runs Python and two members compile the same softmax source. A dry run supplies none of the completion evidence.

The shorter aggregate is not a subset. Together the two runs reached 62 distinct member targets and 60 distinct named C sources. Neither launched either dataflow sweep. Omission means not launched by these commands, not broken or unbuildable.

## 20.4 Did the requested configuration reach the MMA?

[Chapter 4](04-configuration-as-the-architecture-contract.md) supplies a matched pair that differs in one JSON value: `weight_stationary` versus `output_stationary`. Session 13 rebuilt the unchanged Session 4 probe against the public static archive and replayed both files. The probe first loads and converts the request, then initializes from the file, checks the live plug-in ID and name, and issues `tu_mma`. A third arm starts from the OS file and calls `tu_set_dataflow(2)` **after** initialization. It does not load an RS file.

| Route into the same 5×9×10 MMA | Parsed → converted ID | Active plug-in at MMA | Output words checked | MMA estimated-cycle delta: observed / predicted |
|---|---|---|---:|---:|
| WS file | 0 → 0 | 0, weight-stationary | 45 | 432 / 432 |
| OS file | 1 → 1 | 1, output-stationary | 45 | 52 / 52 |
| OS file, then direct RS setter | 1 → 1 (stored request remains 1) | 2, row-stationary | 45 | 384 / 384 |

The PE array is 4×8, pipeline depth seven. All three runs use the same small signed operands, specified as literal half words. The reference multiplies and accumulates their integer values independently, converts each exact sum to FP32, and compares the bits of **every** output. Equal matrices are the expected functional result; they are not how we identify the active dataflow. See the WS, OS and setter records.

For a separate check, split the work into valid extents `m ∈ (4,1)`, `n ∈ (8,1)`, `k ∈ (8,2)`; their Cartesian product gives eight callbacks. At this depth the expected contribution of each is `7(m+n)+k` for WS, `k+ceil(k/4)` for OS, and `6(m+n)+1+k` for RS. Summing over *valid* extents gives the last column. The measured delta is the change in the model's `g_tu.estimated_cycles` across the MMA alone, not a timer around loading, synchronizing and reading back. The oracle checks a model equation; it is not independent validation of physical cycles or operand traffic. [Chapter 17](17-measurement-surfaces-counters-tracing-cycle-models-and-energy.md) explains why interval, producer, units and calibration all matter.

## 20.6 Where did the observation end?

A trace round-trip can preserve entry fields without executing an instruction. Read `tu_debug_replay_execute` in `tu_cmodel/infra/tu_debug.c`: it computes the pre-checksum, reads dimensions, and computes the post-checksum; there is no instruction issue between the two. A stronger replay test would start from known state, record a state-changing operation, issue it through the real consumer on a fresh instance, wait for completion, and compare the changed destination. A recorded opcode, unchanged memory and two matching checksums cannot replace that transition. No debug replay process was counted in the aggregate.

The same distinction applies across language boundaries. `test-dpi` **did** run under `test`: 13 cases passed, zero failed. Its native C caller invokes the C wrapper; no HDL simulator participates. Identity matrices test a useful data path, but transposing identity leaves it unchanged. For orientation, use unequal nonsymmetric inputs and recompute the whole output on the far side of the boundary. The first edition's Python `quick_gemm` case checked `[[19,22],[43,50]]` through ctypes on its own revision. It was **not** a Python test in this aggregate and was not replayed here. Neither test establishes a compiler-to-runtime pipeline, full binding coverage or physical fidelity.

## 20.8 Which evidence should survive an edition change?

Keep the question and disproof condition between editions; recompute membership and reachability when the revision changes. The live S16 census did not rerun either aggregate.

Choose evidence according to what the decision needs. To change a comparator, use a small table with ordinary and exceptional values; it is cheap and exposes exactly which branch accepted a word. To expose a lost configuration field, pay for the route from file to consumer and compare a direct setter: a parser unit test costs less but cannot answer that question. To release a regression suite, retain exact selection and negative-control status on top of those component tests. None substitutes for a calibrated external reference if the decision is about hardware time. Chapter 21 takes up workload choice and sensitivity; the task here is to establish which producer and which checks actually ran.

[Next: Chapter 21 — Designing a Trustworthy Sweep](21-designing-a-trustworthy-sweep.md)
