# Chapter 4 Configuration-Contract Audit — 2026-07-25

## Scope and provenance

- Tusim checkout: `/home/zxy/Workplace/projects/tusim`
- Pinned commit: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Book workspace: `/home/zxy/Workplace/books/tusim-book`
- Host: AArch64 Linux; GCC 11.4.0; GNU Make 4.3; Python 3.11.15
- Claim boundary: pinned source and locally reproduced behavior only; no RTL or silicon calibration is claimed.

This audit treats configuration as a staged evidence problem:

```text
present → parsed → validated → converted → retained → consumed → observable effect
                                      ↘ focused test → aggregate gate → calibration
```

A field is not called runtime-configurable merely because it is present in JSON or in `tu_config_t`.

## Durable artifacts

- `experiments/ch04_config_surface_audit.py`
- `experiments/ch04_runtime_request.json`
- `experiments/ch04_config_propagation_probe.c`
- this record

Raw transient logs are under `/tmp/tusim-ch04-audit-20260725/`.

## Source surfaces inspected

Primary configuration surfaces:

- `config/tu_config.yaml`
- `config/tu_config.json`
- `scripts/gen_config.py`
- `tu_cmodel/tu_config.h`
- `tu_cmodel/infra/config.[ch]`
- `tu_cmodel/tu_cmodel.[ch]`
- `tu_cmodel/tu_sram.[ch]`
- `tu_cmodel/command_queue.h`
- `tu_cmodel/rounding.[ch]`
- `docs/CONFIG_REFERENCE.md`
- `docs/runtime-configuration.md`
- `tests/test_config.c`
- `Makefile`

Targeted consumer searches also covered the CModel tree for full-config fields, `g_tu.rt_cfg`, and compile-time `TU_*` macros.

## 1. Clean build and focused suite

From the Tusim root:

```bash
make clean
make -j2
LD_LIBRARY_PATH="$PWD${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" make test-config
```

Observed:

```text
clean: exit 0
build: exit 0
library warnings:
  unused comp_names in infra/logging.c
  unused parse_opt_uint in infra/config.c
test-config: exit 0, 20/20
```

`tests/test_config.c` still emits repeated warnings because `CHECK` expands to a bare `return` inside `int main(void)`.

`test-config` belongs to the comprehensive `make test` target (`Makefile:494-497, 522-528`) but not the quick smoke target (`Makefile:534-537`).

## 2. Mechanical surface audit

Reproduction:

```bash
cd /home/zxy/Workplace/books/tusim-book
python3 experiments/ch04_config_surface_audit.py \
  /home/zxy/Workplace/projects/tusim --check
```

Observed summary:

```text
source_commit=e918c80b6fce833cd1fcae97730fa841c2176f25
yaml_parser_visible_leaf_fields=65
yaml_textual_leaf_fields=66
yaml_parser_empty_mappings=1
yaml_quoted_empty_scalars=1
json_leaf_fields=75
yaml_only=0
json_only=9
different_shared_values=1
tu_config_t_fields=76
conversion_source_fields=16
dropped_before_tu_runtime_config=60
documented_struct_fields=71
undocumented_struct_fields=5
generated_header_matches_tracked=False
generated_vs_tracked_diff_lines=181
check_status=PASS
```

`--check` pins the source commit and seven input hashes, checks the exact JSON-only, undocumented, empty-string-defect, and shared-value-conflict sets, enforces field/conversion/documentation counts, and expects the known 181-line generated-header mismatch. Unexpected snapshot or extraction drift returns nonzero; this is not merely a report that always succeeds.

### YAML/JSON drift and an empty-string parser defect

The source-aware comparison reports nine JSON-only leaves:

```text
tu.dma.multicast_enabled
tu.weight_compression.enabled
tu.weight_compression.type
tu.weight_compression.rle_epsilon
tu.weight_compression.decoder_enabled
tu.weight_compression.decoder_overlap_dma
tu.weight_compression.decoder_elements_per_cycle
tu.weight_compression.rle_runs_per_cycle
tu.weight_compression.bitmap_elements_per_cycle
```

The nine are multicast plus the eight weight-compression leaves. `tu.performance.tracing.output_file` exists in both files. YAML line 91 contains `output_file: ""`, but `load_yaml_simple()` strips the quotes, treats the resulting empty value as a nested-mapping placeholder, and returns an empty dictionary. The audit reports both the parser-visible count (65) and the source-aware textual count (66), and enforces this known parser defect explicitly.

The shared value conflict is:

```text
YAML: tu.performance.cycle_model = functional
JSON: tu.performance.cycle_model = cycle_accurate
```

This conflict matters because the tracked header and global initialization path use compile-time functional mode, while the runtime loader defaults the full config to numeric mode 2. A request can therefore be reported as cycle-accurate in `tu_config_t` but initialize a synchronous command queue selected by compile-time functional mode.

### Full-to-legacy conversion bottleneck

`tu_config_t` has 76 mechanically detected scalar/array fields. `tu_config_to_runtime()` sources only 16 of them. Sixty fields do not cross this conversion boundary, including:

- dataflow, pipeline depth, MACs per PE;
- SRAM banking and bandwidth controls;
- DRAM settings;
- DMA width, burst, channels, outstanding count, async mode, multicast;
- ISA width, queue depth, dependency checking;
- cycle-model selector;
- supported precision flags and rounding/subnormal/saturation controls;
- sparsity and compression controls;
- most multicore identity/topology fields;
- test iteration count, log level, and trace capacity.

This count is a mechanical property of this conversion function, not a claim that all 60 fields are unused everywhere. Some full-config consumers exist outside the global `tu_init_from_config()` path, for example structured-sparsity estimators and power-model helpers. The safe conclusion is narrower: those fields do not reach `tu_init_with_config()` through this global initialization path.

Fifteen full-structure fields are not populated by the runtime parser at all: `dataflow_via_plugin`, `int8_enabled`, `int4_enabled`, five SRAM bandwidth-model controls, three global-buffer fields, `dram_channels`, `trace_max_events`, `sparsity_metadata_format`, and `log_level`. The canonical JSON also contains unsupported keys such as maximum tile dimensions, accumulator precision, SRAM read/write latency, DRAM core clock, cache coherence, tracing format, and power settings. Unknown-key tolerance makes these look accepted even when no full-structure field is written.

### Documentation omissions

The generated configuration reference lists 71 of the 76 detected `tu_config_t` fields. It omits:

```text
dram_latency_read
dram_latency_write
gbuf_bank_width
log_level
trace_file
```

The reference is generated from `tu_config_default()`, not from `config/tu_config.json`; its values therefore describe C defaults, not necessarily the shipped JSON request. A standalone emitter linked explicitly to the freshly built static archive produced `/tmp/ch04_CONFIG_REFERENCE.md`; it matched the tracked reference byte-for-byte with SHA-256 `040b4918247e9a98a3c10ca44f3b32b1c9893ce741f93f6a4d78863b6c921ecc`.

Its derived DMA row is dimensionally unsafe. `config.c:902-903` divides `dma_bus_width_bits` by eight but labels the result `GB/s` and describes multiplication by frequency; no frequency participates in the expression. The numeric result is bytes per transfer/cycle under an unstated one-transfer assumption, not bandwidth per second without a clock. The separate field name `dram_bandwidth_gbps` is also ambiguous because the emitter labels it `GB/s`.

## 3. Header-generation drift

Reproduction without modifying the tracked header:

```bash
cd /home/zxy/Workplace/projects/tusim
python3 scripts/gen_config.py config/tu_config.yaml \
  -o /tmp/ch04-generated-tu_config.h
diff -u /tmp/ch04-generated-tu_config.h tu_cmodel/tu_config.h \
  > /tmp/ch04-tu-config-header.diff
```

Observed:

```text
diff exit: 1
tracked header lines: 280
generated header lines: 200
diff lines: 182 in the saved direct diff
```

Hashes:

```text
9fb4d87753139a5857107a6fdf56006fcb5adbe95ad30e9f8430c2e5c145910e  config/tu_config.yaml
6f9d292696b1ca5fa38ad3298e7f3a04c43095c0950f71dbe0c3c68b1f15f4db  config/tu_config.json
129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d  tu_cmodel/tu_config.h
e41dcf622c43a7898d0e21d83d870d884f3e781bd207fa8828f8788e7cf1051a  generated header
040b4918247e9a98a3c10ca44f3b32b1c9893ce741f93f6a4d78863b6c921ecc  docs/CONFIG_REFERENCE.md
```

Material differences include:

- different dataflow macro names and omission of plugin dispatch/NLR support;
- shifted FP8/INT8/INT4 masks and omission of INT quantization controls;
- omission of memory-hierarchy, SRAM-bandwidth, and DRAM definitions;
- omission of logging/tracing controls;
- omission of stochastic rounding;
- YAML-derived sparsity disabled versus tracked-header sparsity enabled;
- generated function name `tu_config_default()` versus the tracked compatibility name `tu_runtime_config_default()`.

The Makefile compiles directly against the tracked header and contains no dependency that regenerates it from YAML. Therefore:

- YAML is the declared generator input;
- the tracked header is the effective compile-time contract for the pinned build;
- the generator is stale relative to the tracked header and must not overwrite it in this snapshot.

## 4. End-to-end propagation probe

Build and run from the Tusim root after the clean build:

```bash
gcc -O2 -Wall -Wextra -std=c11 -I. -Itu_cmodel \
  -o /tmp/tusim-ch04-config-probe \
  /home/zxy/Workplace/books/tusim-book/experiments/ch04_config_propagation_probe.c \
  ./libtucmodel.a -lm

/tmp/tusim-ch04-config-probe \
  /home/zxy/Workplace/books/tusim-book/experiments/ch04_runtime_request.json
```

The request deliberately differs from compile-time defaults:

```text
PE 4×8; pipeline 7; two MAC units/PE; output-stationary
SRAM 8/12/16 KiB; 4 banks × 8 bytes
64-bit DMA bus
queue depth 3; estimated cycle model
round-toward-zero
```

Abridged observed output (the literal combined stream also contains initialization log lines):

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

### Proven runtime effects

- `pe_rows` and `pe_cols`: parsed, validated, converted, retained in `g_tu.rt_cfg`, and consumed by MMA tiling/reporting. The A/B case runs identical 9×9×9 all-one MMAs at 4×8 and 16×16 geometry, verifies identical numeric output, and observes the source-predicted 12-versus-1 tile delta.
- W/A/O capacities: parsed, validated, converted from KiB to bytes, and used for actual allocation/bounds.
- counters/tracing/tolerance and five interconnect controls cross the compatibility struct, though this probe does not claim that each causes a global-path behavioral effect.

### Proven compile-time survivors

- requested OS remains active WS because `tu_init_with_config()` calls `tu_set_dataflow(TU_DATAFLOW_MODE)`;
- requested 4×8-byte banking remains 32×4 because `tu_sram_init()` uses compile-time defaults;
- requested queue depth 3 remains 16 and estimated mode remains synchronous because queue construction uses `TU_ISA_QUEUE_DEPTH` and `TU_CYCLE_MODEL`;
- requested RTZ remains global RNE because initialization never calls `tu_set_rounding_mode()`;
- 33 output bytes cost 2 basic estimated cycles, matching the compiled 256-bit/32-byte width, not the requested 64-bit/8-byte width (which would require 5 transfers);
- sync adds 16 cycles, matching compiled pipeline depth 2 × runtime 8 columns, not requested depth 7 × 8 = 56.

These are executable observations of the global CModel path. They do not prove that the full fields have no specialized consumers elsewhere.

## 5. Validation behavior

The probe also loads deliberately invalid or unknown values. The loader succeeds and reports:

```text
rows=16 pipeline=16 dataflow=0 dram=0 cycle=2 rounding=0
```

Source behavior explains the result:

- row value 0 silently falls back to 16 before validation;
- pipeline depth 0 silently falls back to **16**, not its ordinary default 2;
- unknown dataflow, DRAM, cycle-model, and rounding strings map to defaults;
- unknown keys are intentionally ignored.

Other enum families, such as interconnect switching/contention/routing and compression type, instead map bad strings to `-1` and are rejected by validation. The policy is therefore inconsistent across field groups.

Validation proves selected local constraints, not architectural consistency. It checks PE ranges, nonzero SRAM capacities, bank width/count, DMA bus width, nonzero queue depth, selected interconnect/compression/sparsity rules, and a few throughput fields. It does not generally prove that a parsed setting reaches a consumer, that buffers fit a workload, that modes are supported together, or that performance values are calibrated.

The unsigned SRAM-capacity path is especially hazardous: negative JSON integers are cast into `uint32_t`, pass the nonzero-only validator, and can become enormous allocation requests. This audit does not initialize such a request; the conclusion is source-proven and the safe test belongs in an allocation-isolated harness.

## 6. Focused-test interpretation

`tests/test_config.c` mixes nine JSON-parser cases with eleven configuration cases, yielding 20/20 total. It establishes:

- parser basics;
- selected defaults;
- selected parsing and validation;
- selected full-to-legacy conversion;
- one 8×8 MMA after changing PE geometry.

It does **not** establish runtime effects for the requested OS dataflow, banking, DMA width/mode, queue depth, cycle model, rounding, DRAM model, precision enablement, sparsity, compression, or verification controls. In its end-to-end MMA case, the modified 8×8 geometry is checked in `g_tu.rt_cfg`, but numerical correctness of a single 8×8 result would also pass under many compile-time choices.

Interconnect coverage is split: the config suite asserts four of the five compatibility mappings but omits a runtime assertion for router latency, while multicore tests exercise cluster behavior separately. Compression has strong dedicated tests (`24/24` in the independent audit) but `test-compress` is omitted from aggregate `make test`. The runtime-configuration document's “18 tests” inventory is stale relative to the current `20/20` executable.

## 7. Field evidence matrix

Legend: Y = directly established in the global path; P = partial/retained or specialized path only; N = absent at that stage; — = not assessed here.

| Setting | Parse | Validate | Convert | Global consumer | Observable runtime effect | Focused config test | Aggregate `make test` | Calibration |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PE rows/cols | Y | Y | Y | Y | Y (Chapter 4 A/B probe) | P (state + insensitive numeric test) | P (same assertions) | N |
| W/A/O capacity | Y | Y | Y | Y | Y | P | P (same assertions) | N |
| dataflow mode | Y | N (fallback) | N | compile-time | N | parse only | P (parse only) | N |
| pipeline depth | Y | N | N | compile-time | N | N | N | N |
| SRAM banks/width | Y | Y | N | compile-time | N | parse only | P (parse only) | N |
| DMA bus width | Y | Y | N | compile-time in global DMA accounting | N | parse only | P (parse only) | N |
| ISA queue depth | Y | Y | N | compile-time | N | N | N | N |
| cycle model | Y | N (fallback) | N | compile-time | N | default only | P (default only) | N |
| FP16 rounding | Y | N (fallback) | N | separate global API | N | N | N | N |
| DRAM type/bandwidth | Y | weak/none | N | specialized models only | N in global init | N | N | N |
| counters enabled | Y | N | Y | retained/debug | P | default only | P (default only) | N |
| trace output path | Y | N | Y | retained | P | N | N | N |
| error tolerance | Y | N | Y | retained | P | N | N | N |
| interconnect timing controls | Y | Y | Y | retained/specialized cluster paths | P | P (four of five conversion fields) | P (same assertions) | N |
| compression/sparsity | Y | selected rules | N | specialized APIs | N in global init | partial dedicated tests | varies | N |

Aggregate entries describe field-specific assertions, not merely target membership. `make test` naming `test-config` does not upgrade a parse-only, default-only, partial, or absent assertion into field-contract coverage.

## 8. Reproducibility contract

For the pinned snapshot, a reproducible configuration record needs at least:

1. full source commit;
2. exact experiment JSON, not only a reference to the shipped default;
3. tracked-header hash and confirmation that it was not regenerated;
4. clean-build command and compiler flags;
5. probe/workload source and input shapes;
6. explicit list of runtime-effective versus compile-time settings;
7. output and cycle-domain interpretation;
8. test targets actually run;
9. calibration state (`not calibrated` here).

The string `2.0-dev` is metadata, not schema enforcement. The loader does not parse or reject `tu.version`, and unknown fields are ignored. Hashes plus the pinned commit are therefore stronger reproducibility identifiers than the version string alone.

## 9. Safe and unsafe conclusions

Safe:

- JSON loading and selected validation are executable.
- Runtime PE geometry and W/A/O capacities affect the global CModel path.
- many other fields parse into the full struct but are lost at the compatibility conversion boundary.
- the shipped YAML, JSON, tracked header, and generated documentation are not one synchronized source of truth.
- focused tests pass while leaving significant consumption/effect gaps.

Unsafe:

- “all hardware parameters are runtime-configurable”;
- “20/20 config tests prove every knob works”;
- “cycle_accurate” in JSON proves cycle accuracy or even selects the global command-queue mode;
- “generated header” means regeneration is safe;
- a documented field has a modeled performance effect;
- a version string alone reproduces an experiment.

## 10. Independent skeptical-review disposition

The independent review returned nine findings. All were verified against pinned source or executable evidence and resolved:

1. added a discriminating PE-geometry A/B probe (12 versus 1 tiles, identical output);
2. separated 65 parser-visible from 66 textual YAML leaves and corrected genuinely JSON-only leaves from ten to nine;
3. added enforced `--check` mode with commit, hash, set, count, and expected-drift assertions;
4. corrected aggregate coverage entries to field-specific partial/absent evidence;
5. labeled displayed probe output abridged because initialization logs are omitted;
6. documented the generated DMA bandwidth row's dimensional defect;
7. deferred source-tree cleanliness until the final post-build restoration operation;
8. qualified interconnect coverage as four asserted mappings plus source-only router latency;
9. expanded primary source ranges for parser tests, explicit dataflow control, bank effects, numerical globals, and specialized consumers.

Additional parallel-audit findings were incorporated: fifteen unparsed struct fields, unsupported canonical JSON keys, negative-capacity unsigned conversion, stale 18-test documentation, split cluster coverage, and aggregate omission of compression tests.

## 11. Source-tree closure requirement

The checkout tracks six historical object files. `make clean` removes them, and restoring them before a later Make invocation can rearchive stale objects. Final closure must therefore:

1. finish every build, test, and probe;
2. perform no more Make invocations;
3. restore tracked object files as the last Tusim source-tree operation;
4. verify `git status --short` is empty.
