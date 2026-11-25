# Chapter 4 — Configuration as the Architecture Contract

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-4)

> **Edition basis:** Public Tusim snapshot `7a094ff6c5527eff8e4318de676f0c0221c448b4` (November 18, 2026)
> **Evidence status:** clean build, file-ingress comparisons and path-specific model counters at this pin; not calibrated against RTL or silicon

## 4.1 What did the experiment actually configure?

The same JSON file asks for an output-stationary array, a 64-bit DMA bus and a three-entry command queue. The loader accepts it. After initialization the active plug-in is output-stationary and the descriptor engine has an eight-byte bus. The queue has **sixteen** entries. All three observations can be correct: three subsystems constructed from one file need not take their settings from the same place.

Treat a configuration file as a set of requests. To decide whether to include a field in an architecture sweep, follow that field as far as the operation you will measure. A dump of the parsed file cannot tell you which constructor ran. A correct matrix product cannot tell you which dataflow computed it. Even a change in a cycle counter needs an owner: a DMA engine's service charge and a global helper's copy charge answer different questions.

## 4.2 A staged model of configuration evidence

A useful configuration system has more than two states. “Supported” and “unsupported” are too coarse.

### 4.2.1 The propagation ladder

For one field, ask the following questions in order:

| Stage | Question | Example evidence |
|---|---|---|
| Declared | Is the setting named in a file, header, or structure? | JSON key, YAML key, C member |
| Parsed | Does the loader recognize the key and type? | loaded value differs from default |
| Validated | Are illegal values or combinations rejected? | negative test and diagnostic |
| Converted | Does the value cross each API/compatibility boundary? | field mapping assertion |
| Retained | Does initialized state own the value with a defined lifetime? | instance-state inspection |
| Consumed | Does the intended subsystem read it? | source path or instrumentation |
| Effective | Does changing only this field cause the predicted state/output/counter change? | controlled A/B probe |
| Focus-tested | Does a focused test enforce the contract? | named unit/integration test |
| Aggregate-gated | Does routine CI or an aggregate target run that focused test and propagate failure? | recipe/workflow audit |
| Calibrated | Has the modeled effect been compared against a named reference? | error report versus RTL/silicon |

These stages are not interchangeable.

- Parsing is not validation.
- Validation is not propagation.
- Retention is not consumption.
- Consumption is not necessarily an observable effect if the workload does not exercise the branch.
- An effect is not calibration.
- Aggregate inclusion does not strengthen a weak assertion inside the focused test.

### 4.2.2 Three tests for every architecture knob

A practical minimum is:

1. **bad-value test** — illegal input is rejected rather than silently becoming another design;
2. **state-propagation test** — the initialized subsystem contains the requested value;
3. **behavioral-delta test** — changing only that value produces the predicted difference under a workload chosen to expose it.

For PE rows, a behavioral delta might be a changed tile count on a matrix taller than one configuration but not the other. For DMA width, choose a byte count that is not divisible by both widths. For queue depth, submit enough commands to distinguish capacities. For rounding, use values whose FP16 representation differs under RNE and RTZ.

A test that changes a knob but uses an insensitive workload is a disguised no-op test.

---

## 4.3 Two routes into the model

| Starting point | Route | What to inspect |
|---|---|---|
| Build-time defaults | `config/tu_config.yaml` → `scripts/gen_config.py` → `tu_cmodel/tu_config.h` → compiled constructors | Compare a fresh header with the tracked one. Compile a changed header to test a different default. |
| Runtime file | `config/tu_config.json` or a smaller request → `tu_config_load` → `tu_config_t` → `tu_config_to_runtime` → `tu_init_with_config` | Compare the parsed and converted values, then inspect the live subsystem and execute an operation. |
| Direct C control | A caller supplies a runtime structure or calls a setter after initialization | Check the active object immediately before use. A successful setter bypasses the file loader. |

The full C structure (`tu_cmodel/infra/config.h`) is a staging area. The compatibility structure (`tu_cmodel/tu_config.h`) is what the global initializer receives. Some consumers outside that route take the full configuration directly. For example, changing a full-config decoder-rate input to a weight estimator would not by itself change ordinary MMA. Conversely, a field copied into the runtime structure can still be ignored at construction; the bank-width example below does exactly that.

The generated reference has another audience. The `config-docs` recipe calls the C defaults and emits documentation; it does not execute your JSON file. Use a reference table to discover a parameter's name and units, not to establish its active value. Units matter even when the values agree: 256 bits gives 32 bytes per full-width beat, not 32 GB/s without a beat rate and a clock.

## 4.4 Establish a baseline before changing it

Load the shipped `config/tu_config.json` once. The observed active array was 16×16, WS (weight-stationary), depth 2. Its W, A and O regions were 128, 64 and 64 KiB; the DMA engine reported three channels and 32 bytes per beat (256 bits). The shipped SRAM metering policy is `size_only`. These are the baseline for a *shipped file*, not the workload used to compare WS with OS (output-stationary).

The worked request is the original book fixture, [runtime-request.json](../../examples/runtime-request.json). It asks for 4×8/OS, depth 7, 8/12/16 KiB SRAM, a 64-bit bus and one channel. It also asks for queue depth 3, estimated cycle mode and round-toward-zero. Comparing this entire file against the shipped file would change too many variables to explain a single counter difference. Instead, use it as the starting point for several pairs. In each pair change just the mode name, depth, bus width or spelling of a key.

Keep three categories apart when reading either file. PE geometry, storage capacity and bus width describe the proposed architecture. Cycle estimates, counters and tracing describe how the model observes it. Golden backends, iteration counts and error tolerances describe how the experiment judges it. Changing an error tolerance cannot make a design more accurate.

The Chapter 3 first-run fixture is a smaller control: its 4×4 OS request selects OS and returns `[[58,64],[139,154]]` in four MMA-only cycles. Keep that as a reader setup check. It has no matched WS run, so it cannot replace the comparison below.

## 4.5 Follow the request into initialized state

`tu_init_from_file` loads and validates the file, then calls `tu_init_from_config`. The latter converts the full configuration and passes the result to `tu_init_with_config`, which retains a copy in `g_tu.rt_cfg` and constructs the subsystems. In `tu_cmodel/infra/config.c`, begin with `tu_config_to_runtime` (line 539). In `tu_cmodel/tu_cmodel.c`, start at `tu_init_from_file` (line 60) and compare the queue constructor at line 167 with the dataflow selection at line 174.

| Field in the worked request | What crosses the boundary | What the probe finds |
|---|---|---|
| PE rows/columns `4/8`; W/A/O `8/12/16` KiB | Dimensions unchanged; sizes multiplied by 1024 | Active 4×8; allocations 8192/12288/16384 bytes. The matrix below spans eight tile visits. |
| `dataflow: output_stationary`, depth `7` | Mode 1 and depth 7 | Registry selection gives OS, ID 1. Depth reaches the tile callbacks, but not every timing expression uses it. |
| Four banks, eight bytes per bank word | Both values copied | The W region has four banks of **four** bytes. The constructor passes the runtime count but `TU_SRAM_BANK_WIDTH` for width. |
| DMA width `64`, channels `1` | Both values copied | Descriptor engine reports eight bytes per beat and one channel. A width sweep below tests consumption. |
| Queue depth `3`, cycle mode `estimated` | The queue constructor takes compiled depth and mode | Queue capacity 16, synchronous. This is a capacity readback, not a queue-full or dependency test. |
| FP16 rounding `round_toward_zero` | The file parser records RTZ | In a fresh process the separate rounding module still reports RNE. The integer-valued MMA below cannot distinguish these rounding rules. |

The bank-width row illustrates why a conversion assertion is worth keeping even when it is insufficient. It locates the break *after* conversion; changing the parser would not fix it. Similarly, a plug-in pointer and a retained mode are different pieces of state. They agree immediately after valid file initialization. A direct setter can subsequently change the pointer without rewriting the retained request (§4.7).

## 4.6 A matched WS/OS experiment

Use [matched-ws.json](../../examples/matched-ws.json) and the worked OS request. The only changed token is the mode name. Run the same `tu_mma(5, 9, 10, 0, 0, 0, false)` after each initialization. W has shape 5×10, A is 10×9 and O is 5×9. Populate SRAM before starting the counter interval. Read the plug-in ID and name in the same global state that executes the multiply; difference `g_tu.estimated_cycles` immediately across that call.

**How to judge the output.** Encode small integers −2 through +2 with the five known binary16 bit patterns. The probe chooses inputs by row, column and reduction index; its reference multiplies the corresponding *integers*, sums over K, then compares each expected FP32 bit pattern with SRAM. It never calls the simulator's decoder, MMA, or cycle routine for the reference. For example, O[0,1] must be −20 (`c1a00000`); O[2,2] must be +20 (`41a00000`). All 45 entries must pass, not just these two. Integer products and partial sums here are exactly representable: this is a data-placement and arithmetic control, not a general FP16 rounding test.

**How to predict the cycles.** Let `(m,n,k)` be the *valid* dimensions of one tile visit and `d` the runtime pipeline depth. For WS the model charges `d*n + k + d*m` for fill, compute and drain. For OS the combined charge is `k + ceil(k/4)`. With 4×8 PEs, M splits into 4+1, N into 8+1 and K into 8+2. Each of the four M,N pairs visits both K tiles. Summing gives `40 + 56*d` for WS: 40 inner steps and 56 units of depth-dependent fill/drain. OS gives `4*((8+2)+(2+1)) = 52`. Do not substitute the nominal array dimensions on edge tiles.

| File mode | Parsed → converted → selected ID | Depth | Expected MMA cycles | Observed MMA delta | FP32 words matched |
|---|---|---:|---:|---:|---:|
| WS | 0 → 0 → 0 | 7 | 432 | 432 | 45/45 |
| OS | 1 → 1 → 1 | 7 | 52 | 52 | 45/45 |
| WS | 0 → 0 → 0 | 2 | 152 | 152 | 45/45 |
| OS | 1 → 1 → 1 | 2 | 52 | 52 | 45/45 |

Read across the first pair to test selection. Read down within each mode to test depth. OS has no depth term in this formula: its unchanged delta is the expected control, not evidence that the parser lost the field. An idle `tu_sync()` is another consumer altogether. With eight columns it added 16 global cycles at **both** depths: the drain expression uses compiled `TU_PE_PIPELINE_DEPTH` (2) times runtime columns. The 432 and 52 values are plug-in accounting for the same multiply, not measurements of systolic traffic, host time or silicon speed. Chapter 7 treats selection across core switches; this comparison uses only the global file path.

## 4.7 Rejecting a mode is not the same as ignoring a key

Three inputs that look like “typos” to a human take different paths in C:

| Input | Entry point | Observed result |
|---|---|---|
| `no_local_reuse` in `tu.compute.pe_array.dataflow` | JSON loader | −1, rejected: a reserved name is not an executable plug-in. |
| `wieght_stationary` in the same field | JSON loader | −1, rejected: the key exists but the value is unknown. Neither failed file was used to initialize the model. |
| `bus_width_bit` instead of `bus_width_bits` under `tu.dma` | JSON loader | Unknown key ignored; the **256-bit default**, not the accompanying 64, reached execution. |

The first two produce the same diagnostic: `dataflow must be weight_stationary, output_stationary, or row_stationary`. The third is an intentional negative control, **not** a supported way to request a width. On the typo run the initialized engine had 32 bytes per beat and the 33-byte copy behaved like the explicit 256-bit control. Successful loading here is exactly what makes the error hard to notice.

For comparison, initialize with OS and then call `tu_set_dataflow(2)` directly. This succeeds and the active object is RS (row-stationary): the same 45 output words pass and MMA charges 384 cycles at depth 7. Subsequent setter calls with reserved ID 3 and unregistered ID 99 each return −1 and leave RS selected. The retained file-mode value is still 1. The setter performs a registry lookup, not JSON validation. A post-init setter must not be inserted into the file-ingress pair; doing so could hide a broken initializer.

## 4.8 A 33-byte transfer has two different counter owners

Change only `tu.dma.bus_width_bits` from 64 to 256 in the worked OS file. Copy the same 33 nonzero bytes to two distinct, in-bounds O-buffer offsets. Read back and check all bytes on each path. At eight bytes per beat the last byte requires a fifth beat; at 32 bytes per beat it requires a second. The number of useful bytes never changes.

| JSON width | Engine width | Direct `tu_dma_load_o`: global delta | Linear descriptor: engine service delta |
|---:|---:|---:|---:|
| 64 bits | 8 B | 5 | 22 |
| 256 bits | 32 B | 2 | 19 |

For the direct helper, inspect `tu_cmodel/tu_cmodel.c:257`: it writes SRAM and increments the global estimate for payload and read burst issue. Issue cost is zero here. It does not submit a descriptor or include descriptor base latency. Its use of the initialized width was tested directly; the descriptor result alone would not establish this.

For the descriptor, submit one linear, host-to-TU load on channel 0 and flush; check completion and the destination before destroying the descriptor. Difference **`g_tu_dma.estimated_cycles`**, not the global MMA counter. The transfer has base read latency 7 plus the payload beats. Its SRAM accounting also visits nine four-byte words across four banks. With one grant per bank in this service step, five unserved requests add two model cycles each. Thus `7+5+10=22` or `7+2+10=19`. A prediction of 12 or 9 forgets the bank term. The common three-cycle change identifies the width effect; the absolute totals identify which costs the two helpers own. Neither is wall time or a general DMA bandwidth measurement. Chapter 10 separates descriptor admission, scheduling and retirement.

## 4.9 Generation and runtime parsing are separate tests

At the edition pin, generating a temporary header from the shipped YAML produces **byte-for-byte the tracked header**. `test-config-generation` also changes selected YAML defaults, compiles and runs a C consumer of the alternative header, and checks that invalid generation inputs fail. This repairs a first-edition discrepancy. It does not mean that a fresh JSON request regenerates the header, that every YAML key has a runtime spelling, or that every compiled feature has been exercised.

Run both public controls. In this clean extraction `make test-config-generation` reported `generated configuration identity, alternatives, compile, rejection: PASS`; `make test-config` reported `31/31 tests passed`. The latter exercises parser, validation, selected conversion and initialization cases. It does not test 31 architecture knobs end to end. Inspect what each assertion reads: an equality on `cfg.dataflow_mode` is a different test from checking the plug-in used inside MMA. Neither count establishes calibration.

## 4.12 Choosing an architecture contract

| Alternative | Performance/area modeling | Software complexity | Compiler/runtime impact | Verification cost | Main risk |
|---|---|---|---|---|---|
| Expand `tu_runtime_config_t` and keep global initializer | preserves existing interfaces; modest runtime overhead | low-to-medium | minimal API churn | mapping tests for every added field | compatibility struct grows into duplicate schema |
| Store full `tu_config_t` in each TU/core | enables per-instance consumers and sweeps | medium; ownership/lifetime changes | constructors and wrappers must accept full config | broad subsystem propagation tests | global helpers still bypass instance state |
| Generate all C types/defaults/docs/validators from one schema | no direct hardware effect; strongest consistency | high initial tooling work | build and release workflow changes | generator golden tests and migration tests | generator becomes a critical single point of failure |
| Preserve hybrid and add explicit capability report | no behavior change; exposes actual architecture | low-to-medium | experiment harness reads compiled/runtime capability map | effect tests for reported capabilities | does not itself integrate missing knobs |
| Remove unsupported runtime keys | honest smaller contract | low code, higher user migration cost | sweeps must rebuild or use dedicated APIs | fewer but stronger tests | loses planned interface surface |

A per-instance structure makes heterogeneous cores easier to describe, but only if code that executes on a core reads that structure rather than a singleton. A generated schema reduces drift between declarations and defaults but cannot discover which hardware model a handwritten kernel calls. An effective-configuration report is cheaper: at minimum, show requested, normalized, retained and selected values, and mark the field's owner. That would expose the difference between the retained OS request and the direct RS selection without requiring a new schema.

## 4.13 Designing the next effect test

Start by identifying a plausible wrong implementation that could pass the existing test. If the initializer always selected WS, a parser test would still pass. Even a correct 5×9 answer from OS-labelled JSON would pass. In §4.6 the selected-ID assertion and the 52-cycle expectation would both fail. If both plug-ins made the same indexing mistake, comparing their outputs to each other might still pass; the integer reference would not. If the cycle accounting alone were correct but no data were copied, the byte comparison in §4.8 would fail.

For a new field, design the stimulus at the consumer. Use a matrix just over a tile boundary to test geometry, an address near the end of a region to test capacity, a halfway representable value to test rounding. For a queue-depth experiment, first establish whether accepted commands remain pending: a synchronously retired command may release its slot before the next submission. Distinguish a proposed effect test from one that has actually run.

## 4.14 Common failure modes

| Symptom | Likely mistake | Discriminating check |
|---|---|---|
| Both dataflow runs report the right matrix | Equality mistaken for selection | Check ID/name before MMA and predict different callback totals. |
| Both depths give 52 cycles on OS | Insensitive consumer chosen for a depth test | Repeat on WS; keep the OS pair as an invariance control. |
| An unrecognized mode seems to use WS | Old results or the wrong entry point | Inspect the file-loader return and diagnostic before initialization. |
| A “64-bit” run gives 256-bit results | Misspelled key; default silently retained | Compare the parsed width and engine bytes per beat with the intentional typo file. |
| The predicted descriptor delta is too small | Payload and base counted, bank penalty omitted | Derive the word count from *active* bank width and the per-bank grant. |
| Identical source produces conflicting reports | Stale build or different consumer/library | Clean a disposable extraction, link the named archive, record hashes. |

## 4.15 What an experiment should report

For each field, name the authority, the consumer and the strongest check performed. “Queue depth 3 parsed; active queue capacity 16” is more useful than “queue configuration supported.” “At depth 7 the selected WS callback charged 432 cycles for this MMA” is more useful than “OS is faster.” The latter would require a workload distribution and evidence about actual movement and service, quite apart from model calibration. Chapters 20 and 21 return to this distinction when evaluating test coverage and sweep claims.

## 4.16 Summary and fidelity boundary

The public file path retains valid WS/OS requests and pipeline depth. The controlled multiply distinguishes the two plug-ins while both satisfy the same independent output oracle. A descriptor and a direct load both respond to runtime bus width here, but count different work; a queue, bank-width constructor, idle sync and rounding module retain separate authorities. Validation rejects an invalid mode value yet ignores the misspelled width key. Generation checks agreement between YAML and the compiled header, not JSON consumption.

These are executable claims about the pinned C model. They do not establish per-core isolation, accurate physical timing, SRAM port arbitration, DMA/compute overlap, general floating-point conformance, or silicon speedup.

[Next: Chapter 5 — State, Lifecycle, and Public APIs](05-state-lifecycle-and-public-apis.md)
