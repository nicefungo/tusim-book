# Chapter 4 — Configuration as the Architecture Contract

> **Edition basis:** Tusim stable-main snapshot `e918c80`  
> **Evidence status:** source-audited and executable at the pinned commit; not calibrated against RTL or silicon

## Learning objectives

After this chapter, you should be able to:

1. distinguish a configuration file from an effective architecture contract;
2. trace a setting through declaration, parsing, validation, conversion, retention, consumption, and observable effect;
3. explain the different roles of Tusim's YAML, JSON, generated header, full C structure, compatibility structure, and generated reference;
4. identify settings that are runtime-effective in the global CModel path and settings that remain compile-time or specialized-path controls;
5. design tests that detect a documented no-op rather than merely confirming that a parser accepted a value;
6. interpret validation and test-suite success without promoting them to integration or fidelity evidence;
7. record enough configuration provenance to reproduce an architecture experiment;
8. compare configuration-system designs across performance, complexity, safety, and verification cost.

## Prerequisite graph

```text
Chapter 1: architecture questions before RTL
                    │
                    ▼
Chapter 2: evidence and fidelity labels
                    │
                    ▼
Chapter 3: checkout → build → link → execute
                    │
                    ▼
Chapter 4: request → parse → validate → propagate → consume → observe
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
      Chapter 5  Chapter 6  Chapter 9
      lifecycle   PE/MMA      SRAM
```

You should already be comfortable building the pinned checkout and distinguishing source presence, linkage, runtime reachability, and test coverage. Chapter 4 applies the same discipline to individual architecture settings.

---

## 4.1 Opening architecture question: what did the experiment actually configure?

Suppose an exploration report says:

> We changed the tensor unit from a 256-bit DMA interface to a 64-bit interface, selected output-stationary execution, increased pipeline depth from two to seven, and reduced the command queue from sixteen entries to three.

The supplied JSON contains exactly those values. The loader returns success. A configuration dump prints them. The configuration suite passes 20 out of 20 tests.

Did the architecture change?

Not necessarily.

A configuration file is a **request**. An architecture contract exists only when the request reaches the state and consumers whose behavior it is supposed to control. If a conversion drops the field, an initializer substitutes a macro, or a subsystem is constructed through a different API, the experiment may execute a hybrid architecture:

```text
runtime PE dimensions + runtime SRAM capacities
+ compile-time dataflow + compile-time banking
+ compile-time DMA accounting + compile-time queue policy
```

That hybrid can still produce numerically correct matrix multiplication. It can still print the requested full structure. It can still pass parser tests. Those facts do not answer the architecture question.

The central rule of this chapter is therefore:

> **Configuration is a claim about causality. Prove it at the consumer and at an observable effect, not only at the file or parser.**

This is especially important in a pre-spec model. Architecture exploration compares plausible alternatives. If two experiment labels differ while the executable consumer does not, the sweep is not merely imprecise—it is comparing names rather than architectures.

---

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

## 4.3 Tusim's configuration surfaces

The pinned snapshot has several surfaces, each with a distinct role. Calling any one of them “the configuration” hides important boundaries.

### 4.3.1 Source map

| Surface | Pinned role | What it does not prove |
|---|---|---|
| `config/tu_config.yaml` | declared input to `scripts/gen_config.py` | that the tracked header was generated from it unchanged |
| `scripts/gen_config.py` | minimal YAML parser and C-header emitter | that it covers later hand-added macros and fields |
| `tu_cmodel/tu_config.h` | tracked compile-time constants and compatibility runtime structure | that JSON values replace every macro |
| `config/tu_config.json` | shipped runtime request | that every key reaches initialization or a consumer |
| `tu_cmodel/infra/config.h` | 76-field full in-memory configuration structure | that all 76 fields cross the global initialization boundary |
| `tu_cmodel/infra/config.c` | C defaults, JSON parser, validation, conversion, dump, docs emitter | that a parsed field is consumed |
| `docs/CONFIG_REFERENCE.md` | generated view of C defaults | that values came from shipped JSON or that fields are integrated |
| `tests/test_config.c` | parser and selected configuration tests | complete knob-by-knob behavioral coverage |

The comments themselves express competing “single source” stories:

- the YAML says all hardware parameters are configured there and read through a generated header;
- the runtime documentation calls JSON canonical;
- `config.h` calls `tu_config_t` canonical for an instance;
- API documentation describes the C structure as the source of generated reference text;
- the build compiles the tracked header directly and does not regenerate it.

The executable snapshot therefore has a **plural contract**, not one synchronized schema.

### 4.3.2 YAML: declared compile-time input

The YAML groups settings into compute, memory, DMA, ISA, multicore, performance, power, precision, sparsity, and verification sections. It is attractive as an architecture document because comments can explain units and allowed names.

But the generator is deliberately small. `load_yaml_simple()` implements only the subset the project needs. It strips comments, handles indentation with a stack, parses bracketed lists, booleans, integers, and simple floating-point forms, and otherwise stores strings. It is not a general YAML implementation.

The subset has an executable edge case: YAML's `output_file: ""` becomes an empty string after quote stripping, which the parser then treats as a nested-mapping placeholder. A syntactically present YAML key can be lost before header emission even when indentation is valid. The source-aware Chapter 4 audit reports 66 textual YAML leaves and 75 JSON leaves, with nine genuinely JSON-only leaves; it separately reports that Tusim's parser sees only 65 YAML leaves and misclassifies this one path.

More importantly, generation is not part of the default build dependency graph. `make` sees `tu_cmodel/tu_config.h` as an input. It does not infer that changing YAML should rebuild the header.

Thus the YAML has two boundaries:

1. syntax accepted by the custom parser;
2. fields and mappings emitted by `generate_header()`.

A key can pass the first and disappear at the second.

### 4.3.3 The tracked header: effective compile-time contract

At the pinned commit, the tracked `tu_config.h` is 280 lines. A fresh generation from YAML produces 200 lines and a different hash. The generated result omits or changes later additions, including:

- NLR and plugin-dispatch dataflow controls;
- FP8 format distinctions and integer-quantization switches;
- memory-hierarchy, SRAM-bandwidth, and DRAM macros;
- logging and trace controls;
- stochastic rounding;
- compatibility naming of the default-runtime function.

It also emits sparsity disabled from YAML, while the tracked header has compile-time sparsity enabled.

Therefore, for this edition:

> **The tracked header—not a freshly generated replacement—is the effective compile-time contract.**

Regeneration is an audit operation that must target a temporary file. Overwriting the tracked header would not be a neutral refresh; it would remove required definitions and alter compiled behavior.

### 4.3.4 JSON and the full C structure: runtime request and staging area

The runtime loader initializes a `tu_config_t`, parses JSON into it, and validates selected constraints. The structure is broad: the Chapter 4 mechanical audit detects 76 members across compute, precision, memory, DMA, compression, ISA, multicore, performance, sparsity, verification, and logging.

Breadth does not imply parser coverage. Fifteen members are not populated by the runtime parser, and the canonical JSON contains additional unsupported keys such as maximum tile dimensions, accumulator precision, SRAM read/write latency, DRAM clock, cache coherence, trace format, and power controls. Because unknown keys are ignored, their presence is not evidence that a corresponding C field was written.

This is a useful staging representation. It supports documentation, specialized APIs, and future integration. But a staging structure is not automatically instance state.

The crucial global path is:

```text
JSON
  │
  ▼
tu_config_t                  full, 76 detected fields
  │
  │ tu_config_to_runtime()
  ▼
tu_runtime_config_t          compact compatibility structure
  │
  │ tu_init_with_config()
  ▼
g_tu and constructed subsystems
```

The mechanical audit finds that only 16 full-structure fields are sourced by the conversion function. Sixty do not cross this boundary. This count does not mean all sixty are unused everywhere: some specialized routines accept `tu_config_t` directly. It means the global `tu_init_from_config()` path cannot propagate them through this conversion.

That distinction prevents an opposite error. We should not call a field globally integrated because a specialized sparsity estimator consumes it, nor call it universally dead because the compatibility structure drops it.

### 4.3.5 Generated reference: values and descriptions, not a schema

`make config-docs` compiles a tiny C program, calls `tu_config_default()`, and passes that structure to `tu_config_emit_docs()`. It does not load `config/tu_config.json`.

Consequently, the reference reports C defaults. It shows cycle-model value 2 even though the tracked header's global queue default is functional mode 0. It lists 71 of the 76 detected full-structure fields, omitting DRAM read/write latency, global-buffer bank width, log level, and trace file.

Its derived DMA-bandwidth row also fails dimensional analysis. The emitter divides bus width in bits by eight, but does not multiply by a frequency, even though the description says it does. The result has units of bytes per transfer or cycle under an unstated assumption—not `GB/s` without a clock. The separate `dram_bandwidth_gbps` name versus the reference's `GB/s` label adds a bits-versus-bytes ambiguity.

The output is valuable, but its contract is narrower than its title suggests:

- it is not an input schema;
- it does not show JSON paths;
- it does not show validation rules;
- it does not show conversion or consumers;
- it does not identify runtime-effective fields;
- it does not prove calibration.

A stronger generated appendix would add columns for source path, default authority, validation, consumer, focused test, and calibration.

---

## 4.4 Major parameter groups and their architectural questions

A field catalog is most useful when organized by the decisions it controls.

### 4.4.1 Compute geometry

Representative settings:

- PE rows and columns;
- pipeline depth;
- MAC units per PE;
- dataflow;
- maximum tile dimensions;
- supported and accumulator precision.

These knobs ask: how much spatial parallelism exists, how is reuse organized, what latency is hidden or exposed, and what workloads fit efficiently?

The pinned global path makes PE rows and columns runtime-effective. Pipeline depth, issue width, dataflow selection, and several precision declarations do not follow the same path. A sweep must not treat this group as uniformly configurable.

### 4.4.2 On-chip memory

Representative settings:

- W/A/O capacities;
- bank count and bank width;
- arbitration and conflict policy;
- words per cycle and refill window;
- global-buffer size and banking.

Capacity and bandwidth are different contracts. Runtime W/A/O byte capacities determine allocation and bounds in the global CModel. Bank geometry and bandwidth controls remain compile-time in the basic initializer.

This split matters. Reducing SRAM capacity can cause a real bounds or tiling effect while changing bank count in the same JSON may only change the printed full structure. Reporting both as one “memory configuration” obscures which architectural dimension was exercised.

### 4.4.3 DRAM and DMA

Representative settings:

- DRAM family, bandwidth, channels, latency, and row-conflict policy;
- DMA bus width, burst size, channels, outstanding work, async mode, and multicast.

These should control transport granularity, latency, concurrency, and queuing. In the pinned global path, however, the basic CModel still uses compile-time DMA width and async mode. DRAM models and compression/sparsity estimators have additional specialized interfaces.

A valid report must name the path:

> “The structured-sparsity estimator consumed `dma_bus_width_bits` from `tu_config_t`”

is stronger and safer than:

> “Tusim ran with a 64-bit DMA engine.”

### 4.4.4 ISA and command queue

Representative settings:

- instruction width;
- queue depth;
- dependency checking;
- cycle-model mode.

These settings should define encoding capacity, buffered work, dependency semantics, and synchronous versus deferred execution. The global queue constructor instead reads compile-time `TU_ISA_QUEUE_DEPTH` and `TU_CYCLE_MODEL`.

A parser assertion on queue depth therefore tests configuration syntax, not queue architecture. A behavioral test should inspect capacity or submit enough commands to reach the requested limit.

### 4.4.5 Multicore and interconnect

Representative settings:

- multicore enable and count;
- topology;
- switching and contention models;
- deterministic XY/YX routing;
- link bytes per cycle and router latency.

Five interconnect timing controls cross into the compatibility structure. Focused config tests assert conversion for four—switching, contention, routing, and link width—while router-latency conversion is source-proven but not asserted. Retention in `tu_runtime_config_t` is not evidence that the single global TU initializer constructs a cluster or routes packets. Chapter 12 audits those specialized consumers and the remaining construction boundary.

This is a useful example of staged claims: **converted** is stronger than **parsed**, but weaker than **consumed**.

### 4.4.6 Performance, tracing, and power

Representative settings:

- cycle-model selector;
- counters and detailed stalls;
- trace enable, format, path, and capacity;
- power-model enable and model family.

These are observability and fidelity controls, not only architecture controls. They require special care because their names can be mistaken for evidence. A `cycle_accurate` string selects an intended mode; it does not establish cycle accuracy. A power-model enable bit does not establish energy calibration.

In this snapshot, the JSON cycle-model value is parsed but does not select the global command-queue construction mode. The power section present in YAML is not part of the runtime parser shown here.

### 4.4.7 Numerics, sparsity, and compression

Representative settings:

- supported precision flags;
- rounding and subnormal behavior;
- integer quantization policy;
- structured and unstructured sparsity;
- metadata format and decoder rate;
- compression method and decompressor throughput.

These settings can change correctness as well as performance. A no-op precision setting is more dangerous than a mislabeled counter because readers may infer numerical equivalence that was never exercised.

The global initializer does not set the separate rounding module's global mode from `cfg.rounding_mode`. Dedicated rounding APIs and tests are executable, but that is a different path. Compression and structured-sparsity modules consume selected full-config values in specialized estimation paths, while the compatibility conversion drops them.

### 4.4.8 Verification policy

Representative settings:

- golden backend;
- random iterations;
- error tolerance.

These are test-harness policy, not hardware architecture. Mixing them into the same structure is convenient but can blur ownership. The compatibility conversion retains a verification-enabled flag and tolerance, yet initialization does not automatically run a golden comparison.

A reproducibility manifest should separate:

```text
architecture under test
measurement/model controls
verification policy
```

That separation makes it harder to mistake a looser tolerance for a more accurate design.

---

## 4.5 Two complete paths and five severed paths

The most reliable way to learn the system is to trace concrete settings.

### 4.5.1 PE rows and columns: an integrated runtime setting

The complete path is:

```text
compute.pe_array.rows / cols
          │
          ▼
parse_opt_uint16()
          │
          ▼
tu_config_validate(): [1,1024]
          │
          ▼
tu_config_to_runtime()
          │
          ▼
g_tu.rt_cfg.pe_rows / pe_cols
          │
          ├──► MMA tile counts
          ├──► attention tiling
          └──► reports/debug state
```

The Chapter 4 probe requests 4×8. The initialized state remains 4×8. It then performs a controlled A/B test: the same 9×9×9 all-one MMA runs at 4×8 and 16×16, produces identical numeric output, and records 12 versus 1 tiles respectively. Geometry therefore reaches retention, source-level consumption, and an architecture-sensitive observable effect.

Its validation still has a subtlety: zero is replaced by a fallback before validation, so a JSON value of zero becomes sixteen and succeeds. The final state is legal, but the request was not rejected. Whether normalization is acceptable is a policy decision; silent normalization is hazardous in architecture sweeps because two distinct inputs can execute the same design.

### 4.5.2 W/A/O capacities: integrated with a unit conversion

The JSON expresses capacities in KiB-like `*_kb` fields. Conversion multiplies each by 1024 and stores bytes in the compatibility structure. Initialization allocates regions with those sizes. The probe requests 8, 12, and 16 KiB and observes exactly those allocations.

This path contains an important contract boundary:

```text
configuration unit: KiB value
runtime storage unit: bytes
```

A test should assert both sides. Otherwise a missing multiplication could pass a parser test and fail only under large workloads.

### 4.5.3 Dataflow: parsed but severed

The probe requests output-stationary. Parsing produces mode 1. Conversion does not copy dataflow. Initialization calls:

```c
tu_set_dataflow(TU_DATAFLOW_MODE);
```

The active plugin is weight-stationary, selected by the tracked header.

The public `tu_set_dataflow()` API still allows runtime selection after initialization. Therefore the accurate statement is not “OS is unsupported.” It is:

> **The JSON-to-global-initialization path does not select OS at the pinned snapshot; explicit post-init selection is a separate executable path.**

### 4.5.4 SRAM banking: validated but severed

The request uses four banks, each eight bytes wide. The full config contains those values and validates the width and count. The compatibility structure has no bank fields. The basic `tu_sram_init()` path uses compile-time constants. The initialized W region reports 32 banks × 4 bytes.

This is the canonical example of why validation is not integration.

### 4.5.5 DMA width: validated but behavior remains compile-time

The request uses a 64-bit bus. That width passes the power-of-two range check. The global path drops it. Basic output-load accounting uses the compiled 256-bit width.

For 33 bytes:

```text
requested 64-bit bus: ceil(33 / 8)  = 5 transfers
compiled 256-bit bus: ceil(33 / 32) = 2 transfers
observed basic estimate:              2 cycles
```

The workload was chosen deliberately. A 32-byte transfer would not distinguish 64 and 256 bits if the implementation added other fixed costs or rounded unexpectedly. Good tests maximize diagnostic separation.

### 4.5.6 Queue and cycle model: parsed labels, compile-time construction

The request asks for depth 3 and estimated mode. The full config reports both. The queue is constructed with capacity 16 and synchronous execution because the initializer reads tracked-header macros.

This also exposes a cross-surface conflict:

- YAML requests `functional`;
- JSON requests `cycle_accurate`;
- `tu_config_default()` uses numeric 2;
- the tracked header selects numeric 0 for the global queue;
- the Chapter 4 request asks for numeric 1;
- the initialized queue remains synchronous.

A single version string cannot disambiguate these layers.

### 4.5.7 Pipeline depth and rounding: separate compile/global controls

The request's pipeline depth is seven. Sync timing uses compiled depth two. With eight runtime columns, the observed sync delta is 16 cycles rather than 56.

The request's rounding mode is RTZ. The separate rounding module remains in global RNE because initialization does not call its setter.

These two fields illustrate different severed designs:

- pipeline depth is consumed through a compile-time macro;
- rounding is controlled by a separate mutable global API.

Both need explicit integration if JSON is meant to own them.

---

## 4.6 Worked reproducible example

The durable request and probe live in the book workspace:

```text
experiments/ch04_runtime_request.json
experiments/ch04_config_propagation_probe.c
```

### 4.6.1 Set portable roots

```bash
export TUSIM_ROOT=/home/zxy/Workplace/projects/tusim
export BOOK_ROOT=/home/zxy/Workplace/books/tusim-book
```

### 4.6.2 Build from clean source

```bash
cd "$TUSIM_ROOT"
make clean
make -j2
```

Because this checkout tracks historical object files, finish all builds and tests before restoring those tracked artifacts. Chapter 3 explains the stale-archive hazard.

### 4.6.3 Build with explicit static linkage

```bash
gcc -O2 -Wall -Wextra -std=c11 \
  -I. -Itu_cmodel \
  -o /tmp/tusim-ch04-config-probe \
  "$BOOK_ROOT/experiments/ch04_config_propagation_probe.c" \
  ./libtucmodel.a -lm
```

Explicit `./libtucmodel.a` linkage avoids shared-library discovery and library-selection ambiguity.

### 4.6.4 Run

```bash
/tmp/tusim-ch04-config-probe \
  "$BOOK_ROOT/experiments/ch04_runtime_request.json"
```

Abridged observed output:

```text
parsed: pe=4x8 pipeline=7 macs_per_pe=2 dataflow=1
parsed: sram_kb=8/12/16 banks=4 width=8
parsed: dma_bus=64 queue=3 cycle_model=1 rounding=1
active: pe=4x8 sram_kb=8/12/16 dataflow=weight_stationary
active: banks=32 width=4 queue=16 synchronous=true rounding=0
effect: dma_33B_cycles=2 requested_64b_expectation=5 compile_256b_expectation=2
effect: sync_delta=16 requested_pipeline_expectation=56 compile_pipeline_expectation=16
fallback: rows=16 pipeline=16 dataflow=0 dram=0 cycle=2 rounding=0
effect: mma_9x9x9_tiles_4x8=12 tiles_16x16=1 outputs_identical=true
probe: PASS
```

The example intentionally prints both the parsed and active surfaces. Printing only `tu_config_t` would conceal the severed paths. Printing only active state would conceal that parsing succeeded.

### 4.6.5 Reproduce the surface audit

```bash
cd "$BOOK_ROOT"
python3 experiments/ch04_config_surface_audit.py "$TUSIM_ROOT" --check
```

This script compares source-aware YAML and JSON leaves, exposes the custom parser's empty-string loss, counts full-structure fields and conversion sources, checks documentation coverage, generates a temporary header, and compares hashes. `--check` verifies the commit, pinned input hashes, exact field sets/counts, and the expected header mismatch; unexpected drift returns nonzero. Even enforced mechanical checks are not substitutes for semantic consumer inspection.

---

## 4.7 Validation: necessary, local, and inconsistent

### 4.7.1 What the validator proves

The pinned validator checks selected constraints, including:

- PE dimensions in [1, 1024] after parser normalization;
- nonzero W/A/O capacities;
- bank widths of 1, 2, 4, or 8 bytes;
- bank count in [1, 1024];
- DMA width as a power of two in [32, 1024] bits;
- nonzero command-queue depth;
- selected interconnect enum/range rules;
- compression method, epsilon, and decoder throughput;
- selected sparsity combinations.

These checks prevent some invalid local states.

They also leave an unsigned-conversion hazard: negative JSON SRAM capacities become large `uint32_t` values and pass the nonzero-only validator. The Chapter 4 experiment does not initialize such a request because it could cause an enormous allocation; the defect is source-proven and belongs in an allocation-isolated negative test.

### 4.7.2 What it silently normalizes

The probe shows that invalid values in several groups do not produce errors:

- zero PE rows become 16;
- zero pipeline depth becomes 16, even though the normal default is 2;
- unknown dataflow becomes WS;
- unknown DRAM type becomes ideal;
- unknown cycle model becomes numeric 2;
- unknown rounding becomes RNE;
- unknown keys are ignored by documented policy.

Other enums, such as interconnect switching, set `-1` and fail validation. The error policy is inconsistent.

For forward compatibility, ignoring unknown keys can be deliberate. For reproducible architecture work, it creates a typo hazard:

```json
{"dma": {"bus_width_bit": 64}}
```

may execute with the default because the misspelled key is unknown. A strict mode should reject unknown fields for experiments while a permissive mode remains available for rolling compatibility.

### 4.7.3 Cross-field and physical validation

A local validator does not prove physical plausibility. Stronger checks could include:

- multiplication overflow before converting capacities or computing PE totals;
- queue and dependency-policy compatibility;
- enabled precision versus selected operation format;
- tile dimensions versus W/A/O capacity;
- bank geometry versus word size and port assumptions;
- multicore enable/count/topology consistency;
- trace enabled versus nonempty supported output format;
- compression enabled versus non-`none` method and decoder placement;
- cycle-model choice versus constructed subsystem support.

Some constraints belong at parse time; others require workload or subsystem context. The design should say where each invariant is enforced.

---

## 4.8 Detecting documented no-op settings

### 4.8.1 Static consumer tracing

For each field, search for:

1. declaration in input and C structure;
2. parser assignment;
3. validator reference;
4. conversion or constructor argument;
5. instance-state member;
6. reads outside dumps/docs/tests;
7. compile-time macros that bypass it.

Exclude false consumers. A field read only by a dump function is observable metadata, not an architecture effect. A field read only by the docs generator is documentation, not execution.

### 4.8.2 Metamorphic A/B tests

A no-op detector compares two configurations differing in one field:

```text
same source + same workload + same seed + one changed field
```

Then require a predicted invariant or delta.

| Field | Choose this stimulus | Require this observation |
|---|---|---|
| PE rows | M spans one geometry but not the other | tile count or cycles change; result remains equal |
| SRAM capacity | allocation or workload near boundary | region size/bounds outcome changes |
| dataflow | shape with different reuse regimes | active plugin changes; functional result remains equal |
| DMA width | non-multiple byte count | transfer-cycle count changes by formula |
| queue depth | submit beyond smaller depth | acceptance/full boundary changes |
| rounding | halfway representable values | exact encoded result differs as specified |
| trace enable | one named operation | trace artifact existence/content changes |

A field can legitimately produce no delta for a particular workload. That is why the expected sensitivity must be stated before the run.

### 4.8.3 Mutation testing for configuration

A useful extension is to deliberately sever a mapping or replace a consumer with a default and confirm that the test fails. If a test still passes after the field is ignored, it was not enforcing propagation.

This is particularly important for tests like “init with 8×8 and run an 8×8 MMA.” Functional correctness alone may not distinguish 8×8 from a larger compiled array. The test should assert an architecture-sensitive state or counter as well.

---

## 4.9 Reading the 20/20 configuration suite correctly

The focused suite contains twenty tests in the pinned snapshot:

- nine JSON parser tests;
- selected defaults and file/string loads;
- selected validation failures;
- interconnect parsing and compatibility conversion;
- one general conversion test;
- one initialization plus MMA test.

It is an executable and valuable suite. It is also narrower than the field catalog.

The suite demonstrates that:

- the parser handles its tested JSON forms;
- selected values enter `tu_config_t`;
- selected invalid values fail;
- PE geometry and capacities cross part of the compatibility path;
- one numerically correct MMA runs after changing geometry.

It does not demonstrate runtime effect for every parsed group. In particular, the Chapter 4 probe finds gaps for dataflow, banking, DMA width, queue depth, cycle model, pipeline depth, and rounding.

`test-config` is named in the comprehensive `make test` recipe but omitted from `test-quick`. This is an aggregate-coverage fact, not a fidelity upgrade. If the focused test checks parsing only, aggregate execution still checks parsing only.

The runtime-configuration document's “18 tests” inventory is stale; the executable currently reports 20. Interconnect evidence is split between parsing/conversion and separate multicore behavior tests, with no JSON-to-cluster end-to-end gate. Compression has strong dedicated focused coverage, but `test-compress` is omitted from aggregate `make test`. Aggregate claims must therefore be made per field or subsystem, not per target name.

---

## 4.10 Runtime versus compile-time configuration

Neither runtime nor compile-time configuration is universally superior.

| Design | Benefits | Costs and risks | Best regime |
|---|---|---|---|
| Compile-time constants | optimizer visibility; simple data layout; impossible per-instance mismatch after build | rebuilds; binary/config provenance burden; hidden stale artifacts; weak sweep ergonomics | fixed structural choices, generated models, small trusted design sets |
| Global runtime compatibility struct | low migration cost; preserves old APIs; easy geometry/capacity overrides | field bottleneck; global state; split authority; accidental macro fallback | incremental retrofit of a legacy singleton model |
| Full per-instance runtime config | clean ownership; multi-instance sweeps; direct consumer access | larger constructors; validation complexity; state lifetime and thread-safety work | architecture exploration and heterogeneous instances |
| Generated typed schema | synchronized defaults/docs/validation; strict tooling | generator maintenance; migration/versioning discipline; generated-code review | broad stable field catalog with many consumers |
| Hybrid structural/runtime split | compile structural layout, vary operating modes | must classify every field; combinatorial build manifests | fields whose storage/layout truly require compilation |

The problem in the pinned snapshot is not that a hybrid exists. Hybrid systems are often appropriate. The problem is that the boundary is not consistently represented in the files, docs, and tests.

A robust hybrid would label each field:

```text
compile-time structural
runtime per-instance
runtime global
test-harness only
specialized-model input
reserved/future
```

Then tooling could reject a runtime request for a compile-time-only field or report the compiled value beside it.

---

## 4.11 Versioning and reproducible experiments

### 4.11.1 Why `2.0-dev` is insufficient

Both shipped configuration files contain a version string, but the runtime loader does not use it as a schema gate. Unknown keys are ignored. The same version label can therefore accompany different tracked headers, parser mappings, and consumers.

A reproducible record must bind together:

```text
source revision
+ exact config bytes
+ effective compile-time header
+ build/toolchain
+ workload
+ execution path
+ observed output
```

### 4.11.2 Minimum manifest

For the Chapter 4 experiment, record:

- full commit `e918c80b6fce833cd1fcae97730fa841c2176f25`;
- SHA-256 of YAML, JSON, tracked header, and generated docs;
- exact request JSON stored with the book;
- clean-build command and compiler flags;
- explicit static-library linkage;
- probe source and command;
- parsed and active values;
- test targets and observed counts;
- known compile-time survivors;
- calibration state: none.

### 4.11.3 Schema evolution

A mature schema should define:

- schema identifier and revision;
- required and optional fields;
- unknown-key policy;
- aliases and deprecation windows;
- unit semantics;
- enum vocabulary;
- defaults and their authority;
- migration rules;
- consumer/version compatibility.

A loader should distinguish:

```text
missing field → documented default
unknown future field → strict error or explicit compatibility warning
invalid known value → error
renamed deprecated field → warning plus deterministic migration
unsupported consumer capability → error before execution
```

Silent fallback is convenient for applications but dangerous for experiments unless recorded prominently.

---

## 4.12 Trade-offs for repairing the contract

The pinned model can evolve along several realistic paths.

| Alternative | Performance/area modeling | Software complexity | Compiler/runtime impact | Verification cost | Main risk |
|---|---|---|---|---|---|
| Expand `tu_runtime_config_t` and keep global initializer | preserves existing architecture; modest runtime overhead | low-to-medium | minimal API churn | mapping tests for every added field | compatibility struct grows into duplicate schema |
| Store full `tu_config_t` in each TU/core | enables per-instance consumers and sweeps | medium; ownership/lifetime changes | constructors and wrappers must accept full config | broad subsystem propagation tests | global helpers still bypass instance state |
| Generate all C types/defaults/docs/validators from one schema | no direct hardware effect; strongest consistency | high initial tooling work | build and release workflow changes | generator golden tests and migration tests | generator becomes a critical single point of failure |
| Preserve hybrid and add explicit capability report | no behavior change; exposes actual architecture | low-to-medium | experiment harness reads compiled/runtime capability map | effect tests for reported capabilities | does not itself integrate missing knobs |
| Remove unsupported runtime keys | honest smaller contract | low code, higher user migration cost | sweeps must rebuild or use dedicated APIs | fewer but stronger tests | loses planned interface surface |

For a pre-spec exploration tool, the strongest long-term regime is usually a full per-instance configuration plus generated metadata. But migration cost matters. A staged repair can first emit an **effective configuration report** that lists requested, normalized, compiled, and active values. This prevents mislabeled experiments before all knobs are integrated.

Any recommendation must include physical and organizational costs. More runtime variability can increase state, constructor complexity, test combinations, and thread-safety burden. Compile-time specialization can improve simplicity and optimization but multiplies binaries and provenance requirements.

---

## 4.13 Verification strategy

### 4.13.1 Verification matrix for the pinned snapshot

| Setting | Parse | Validate | Convert | Global effect | Focused config evidence | Calibration |
|---|---:|---:|---:|---:|---:|---:|
| PE rows/cols | yes | yes | yes | yes (12-vs-1 tile A/B) | state + insensitive suite MMA; Chapter 4 effect probe | no |
| W/A/O capacities | yes | nonzero | yes | allocation/bounds | partial | no |
| dataflow | yes | silent fallback | no | compile-time default | parse only | no |
| pipeline depth | yes | no | no | compile-time timing | none | no |
| SRAM bank geometry | yes | yes | no | compile-time initializer | parse only | no |
| DMA width | yes | yes | no | compile-time basic accounting | parse only | no |
| queue depth | yes | nonzero | no | compile-time constructor | none | no |
| cycle model | yes | silent fallback | no | compile-time constructor | default only | no |
| rounding | yes | silent fallback | no | separate global API | none | no |
| DRAM request | yes | weak | no | specialized paths | none in config suite | no |
| interconnect timing fields | yes | yes | yes | specialized/retained | four of five mappings asserted; router latency source-only | no |
| compression/sparsity | yes | selected rules | no | specialized APIs | dedicated tests vary | no |

“No” in global effect does not claim universal absence. It identifies the path audited in this chapter.

### 4.13.2 Closure checks

This chapter's executable evidence includes:

```text
clean static/shared build: pass
focused test-config: 20/20
enforced pinned surface audit (--check): pass
temporary YAML→header generation and diff: mismatch reproduced
custom propagation probe: pass
```

The source checkout must be restored after all builds. Since it tracks historical object files, restoration is the final source-tree operation; no later Make invocation is safe without another clean rebuild.

---

## Fidelity box — what configuration evidence can and cannot establish

> **Executable:** JSON parsing, selected validation, full-to-legacy conversion, runtime PE geometry and capacities, and the Chapter 4 observations were run at `e918c80`.
>
> **Integrated in the audited global path:** PE rows/columns and W/A/O capacities. Several counter, trace, tolerance, and interconnect fields are retained, but retention alone is not promoted to a behavioral claim.
>
> **Compile-time in the audited global path:** default dataflow, basic SRAM banking, basic DMA width/mode, command-queue depth/mode, and pipeline-depth timing uses demonstrated here.
>
> **Specialized-path caution:** full-config consumers in sparsity, compression, power, or cluster code do not imply propagation through global `tu_init_from_config()`.
>
> **Estimated:** cycle outputs in the probe are source-defined CModel accounting. They are not calibrated latency.
>
> **Not established:** RTL equivalence, silicon timing, area, energy, physical feasibility, or complete interaction coverage across 76 fields.
>
> **Unsafe conclusion:** “The JSON describes the architecture that ran.” The safe statement lists each field's strongest proven propagation stage.

---

## 4.14 Common failure modes

### Failure 1: treating a loaded value as an active value

**Signal:** config dump changes, subsystem behavior does not.  
**Cause:** conversion or constructor ignores the field.  
**Remedy:** print requested, normalized, compiled, and active values separately.

### Failure 2: regenerating a tracked header destructively

**Signal:** missing macros, changed masks, compile failures, or altered defaults.  
**Cause:** generator lags hand-maintained header additions.  
**Remedy:** generate to a temporary path, diff, compile-check, and only update through reviewed source changes.

### Failure 3: validating syntax but not architecture

**Signal:** invalid combinations initialize and fail later—or execute a fallback.  
**Cause:** validator checks local ranges only.  
**Remedy:** add cross-field and consumer capability checks.

### Failure 4: silent typo compatibility

**Signal:** experiment label changes but effective state remains default.  
**Cause:** unknown keys are ignored.  
**Remedy:** strict experiment mode with unknown-key errors.

### Failure 5: insensitive test workload

**Signal:** test passes even when mapping is removed.  
**Cause:** workload does not distinguish configurations.  
**Remedy:** choose boundary cases and mutation-test the assertion.

### Failure 6: confusing generated docs with generated behavior

**Signal:** field appears in reference but has no consumer.  
**Cause:** docs emitter enumerates structure members.  
**Remedy:** generate consumer and test columns from auditable metadata.

### Failure 7: version-only provenance

**Signal:** same `2.0-dev` experiment cannot be reproduced.  
**Cause:** source/header/config drift beneath a static label.  
**Remedy:** record commit and artifact hashes.

### Failure 8: mixing architecture and verification policy

**Signal:** tolerance or backend changes are described as hardware alternatives.  
**Cause:** one structure combines both domains.  
**Remedy:** report architecture, model controls, and verification settings separately.

### Failure 9: stale object rearchiving

**Signal:** clean Git status but ABI-incoherent library after restoring tracked objects and invoking Make.  
**Cause:** historical object timestamps satisfy incremental dependencies.  
**Remedy:** clean-build, finish all probes, restore tracked objects last, then stop building.

---

## 4.15 Implications for Tusim development

The audit exposes architecture-development questions rather than a generic completion checklist.

1. **Effective-config reporting:** every run should be able to emit requested, normalized, compiled, and active values.
2. **Per-instance ownership:** fields intended for heterogeneous cores should live in owned instance state, not mutable globals or compile macros.
3. **Schema unification:** one typed source could generate examples, C definitions, defaults, validation tables, docs, and migration metadata.
4. **Strict experiment mode:** reject unknown keys and silent enum fallback when reproducibility matters.
5. **Consumer metadata:** generated docs should identify constructor/consumer, test, and fidelity status.
6. **Metamorphic regression:** each architecture field should have at least one predicted behavioral or state delta.
7. **Compile-time capability manifest:** if structural options remain compiled, binaries should expose their values and hashes.
8. **Separation of concerns:** architecture, performance-model policy, tracing, and verification policy should be distinguishable even if stored together.

The goal is not to maximize the number of runtime knobs. It is to ensure that every advertised alternative has a clear regime, a real consumer, explicit costs, and enforceable evidence.

---

## 4.16 Summary

- A configuration file is a request; an architecture contract requires propagation to a consumer and an observable effect.
- Tusim's pinned snapshot has several partially independent configuration authorities: YAML, JSON, the tracked header, full C defaults, a compatibility structure, and generated docs.
- Fresh YAML generation does not reproduce the tracked header and would omit material definitions.
- The full `tu_config_t` has 76 mechanically detected fields, while the global compatibility conversion sources 16; this boundary drops many settings from `tu_init_from_config()`.
- PE geometry and W/A/O capacities are runtime-effective in the audited global path.
- Dataflow, pipeline depth, SRAM banking, basic DMA width, queue construction, cycle mode, and rounding remain compile-time or separately controlled in the demonstrated path.
- Validation is useful but inconsistent: some bad enums fail, while others silently normalize; unknown keys are ignored.
- The 20/20 suite proves parser and selected propagation behavior, not complete knob integration.
- Reproducibility requires the source commit, exact config, effective header hash, build, workload, path, output, and calibration status.
- A trustworthy configuration system makes compile-time, runtime, specialized, and verification-only controls explicit and tests predicted effects.

---

## Review questions

1. Why is successful JSON loading weaker evidence than runtime retention?
2. What additional evidence distinguishes retention from consumption?
3. Why can a numerically correct MMA fail to test PE geometry?
4. Which configuration surfaces are effective compile-time and runtime authorities in the pinned snapshot?
5. Why is temporary header generation safer than overwriting `tu_config.h`?
6. What does `tu_config_to_runtime()` do to the strength of a configuration claim?
7. Why does validating SRAM bank width not prove that runtime banking changed?
8. How does the 33-byte DMA probe distinguish a 64-bit request from a 256-bit compiled width?
9. Why is the `cycle_accurate` string not evidence of cycle accuracy?
10. What is hazardous about silently mapping an unknown enum to a default?
11. When can ignoring unknown keys be useful, and when is strict rejection preferable?
12. Why should architecture and verification-policy settings be reported separately?
13. What additional columns should a generated configuration reference contain?
14. Why does aggregate `make test` inclusion not upgrade a parse-only assertion?
15. What information beyond `2.0-dev` is needed to reproduce an experiment?

## Design exercises

### Exercise 1 — Build a field ledger

Choose ten `tu_config_t` fields from at least four groups. For each, record declaration, JSON path, parser line, validation rule, conversion, initialized-state owner, consumer, focused test, aggregate gate, and calibration status. Mark unknown stages rather than inferring them.

### Exercise 2 — Design a dataflow propagation test

Write a test that loads OS from JSON, initializes the global model, and requires the active plugin to be OS. First run it against the pinned snapshot and explain the failure. Then propose the smallest integration change without implementing it in the source checkout.

### Exercise 3 — Strict loader mode

Design an API that supports both permissive forward compatibility and strict reproducible experiments. Specify diagnostics for unknown keys, deprecated aliases, unknown enum values, normalized values, and unsupported consumers.

### Exercise 4 — Queue-depth metamorphic test

Construct two configurations with depths 3 and 16. Specify a submission sequence that must distinguish them, the expected return/status behavior, and how synchronous versus deferred modes alter the test.

### Exercise 5 — Reproducibility manifest

Create a machine-readable manifest for the Chapter 4 probe containing commit, config/header hashes, compiler flags, linked library form, request path, expected active values, observed deltas, test targets, and calibration status.

### Exercise 6 — Schema design trade-off

Compare expanding `tu_runtime_config_t`, storing full `tu_config_t` per instance, and generating both from a schema. Evaluate runtime overhead, ownership, ABI stability, compiler integration, test burden, migration risk, and support for heterogeneous multicore designs.

---

## Primary references

All repository references below are from Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25`.

1. `config/tu_config.yaml:1-124` — declared YAML architecture input, groups, units, defaults, and allowed-name comments.
2. `config/tu_config.json:1-134` — shipped runtime request, JSON-only compression/multicast leaves, and the trace path that the custom YAML parser misclassifies.
3. `scripts/gen_config.py:14-91,94-360,365-376` — minimal YAML parser, header mappings, and generator CLI.
4. `tu_cmodel/tu_config.h:21-230,232-274` — effective tracked compile-time constants and compatibility runtime structure/default.
5. `tu_cmodel/infra/config.h:37-140,146-200` — full configuration structure and loader/validation/conversion/docs contracts.
6. `tu_cmodel/infra/config.c:148-262,266-508,523-640,689-908` — C defaults, conversion bottleneck, parser, validation, and docs generator.
7. `tu_cmodel/tu_cmodel.c:35-109,111-310,381-402` — lifecycle, initialization choices, runtime geometry/capacity consumers, compile-time dataflow/timing uses, and explicit post-init dataflow API.
8. `tu_cmodel/tu_sram.c:50-83,146-260` and `tu_cmodel/tu_sram.h:37-99` — compile-time bank construction, active bank/region state, and bulk-access effects used by the probe.
9. `tu_cmodel/command_queue.h:128-160` — observable queue capacity and synchronous-mode state.
10. `tu_cmodel/rounding.c:38-90,222-242`, `tu_cmodel/rounding.h:28-41`, and `tu_cmodel/tu_precision.c:15-62,172-178` — separate global rounding/subnormal state and precision consumers.
11. `tu_cmodel/memory/weight_compress.c:15-31`, `tu_cmodel/sparsity/structured_2of4.c:489-528`, and `tu_cmodel/tu_cluster.c:22-52` — specialized full-config compression, sparsity, and cluster paths.
12. `tests/test_config.c:29-143,147-340` — nine parser tests plus focused defaults, parse, validation, conversion, interconnect, and MMA coverage.
13. `tests/test_multicore.c:355-475` and `tests/test_compress.c:311-336,428-445,523-619` — split specialized behavioral coverage and strong compression-focused tests.
14. `Makefile:419-422,494-497,522-537,566-571` — focused/aggregate test membership, compression omission, and default-based configuration-reference generation.
15. `docs/CONFIG_REFERENCE.md:1-135` — generated default-value reference and derived metrics.
16. `docs/runtime-configuration.md:1-137` — intended runtime configuration architecture and claims checked against executable source.
17. `experiments/ch04-configuration-contract-audit-2026-07-25.md` — exact commands, hashes, outputs, evidence matrix, and safe claim boundaries for this chapter.
