# Chapter 3 — Repository Tour and First Execution

> **Edition boundary.** This chapter describes Tusim snapshot `e918c80b6fce833cd1fcae97730fa841c2176f25`, an untagged `2.0-dev` main-branch snapshot. Commands and outputs were reproduced on AArch64 with GCC 11.4.0 and GNU Make 4.3. A filename, target name, or successful command is evidence only for the boundary it actually exercises.

## Learning objectives

After this chapter, you should be able to:

1. navigate the Tusim checkout by responsibility rather than by filename alone;
2. distinguish source presence, compilation, library membership, linkage, runtime reachability, and test coverage;
3. reproduce a clean static and shared library build;
4. select a smoke or focused test without mistaking it for complete regression evidence;
5. compile and run a minimal JSON-configured C program through the public lifecycle, DMA, and MMA path;
6. interpret the resulting functional output and counters without inventing a unified timing model;
7. assess the actual status of the ONNX compiler, documentation generators, and CI wrapper at this snapshot;
8. leave the source checkout clean after an experiment.

## Prerequisite graph

```text
Chapter 1: architecture question and evidence boundary
             │
             ▼
Chapter 2: model contract, fidelity, and claim audit
             │
             ├──────────────┐
             ▼              ▼
       C build basics   GEMM convention
             │              │
             └──────┬───────┘
                    ▼
       Chapter 3: find, build, link, execute,
                  verify, and clean
                    │
             ┌──────┴──────┐
             ▼             ▼
 Chapter 4: config   Chapter 5: lifecycle/API
```

Chapter 1 asked what architectural decision a model should inform. Chapter 2 asked what evidence would make an answer trustworthy. This chapter adds a practical question: **what, exactly, did you execute?**

---

## 3.1 Opening architecture question: what path did the experiment exercise?

Suppose an exploration report says:

> “Tusim built successfully, the test passed, and the simulator reported 19 cycles.”

That sentence can conceal several different situations:

- a source file exists but is not compiled;
- an object is archived but no executable references it;
- an executable links a stale shared library;
- a unit test calls an internal helper that the public runtime never reaches;
- a frontend writes C text, but the text does not link;
- a target returns success after suppressing a failed command;
- a functional result is correct, while its printed counters come from incompatible accounting paths.

None of these possibilities makes the repository useless. They make the execution boundary important.

The architectural question for this chapter is therefore:

> **How do we establish a reproducible path from the pinned source snapshot to a named behavior, while preserving the distinctions among built, linked, reachable, tested, and validated?**

The answer is not “run every target.” A repository with many models, tests, generators, and experiments needs a staged inspection method. The useful result is a chain of evidence that can be repeated and challenged.

---

## 3.2 The execution ladder

A binary feature does not become real in one step. Use the following ladder.

| Level | Question | Typical evidence |
|---|---|---|
| **Present** | Does the source or declaration exist? | tracked file, symbol declaration |
| **Compiled** | Does the source compile under the selected flags? | object file, successful compile command |
| **Library member** | Is the object included in the named library? | `ar t`, shared-link command |
| **Linked** | Does the executable resolve the symbol from that library? | linker command, `readelf`, `nm` |
| **Reachable** | Can the public/config/runtime path invoke it? | call path, configured integration run |
| **Focused-tested** | Does a targeted test exercise its contract? | named test and assertions |
| **Aggregate-tested** | Is that test enforced by a broader target or CI gate? | dependency graph and nonzero failure propagation |
| **Validated** | Does behavior match an independent reference at the claimed boundary? | golden, RTL, FPGA, or silicon comparison |

These levels are cumulative only when evidence connects them. A source file can be compiled manually yet excluded from the normal library. A library member can remain unreachable. A focused test can pass while an aggregate target omits it. A target can print a linker failure and still return zero.

This ladder operationalizes Chapter 2's integration ledger. It also changes how to read a repository tour: directories tell you where to look, but build and execution evidence tell you what happened.

---

## 3.3 A responsibility-oriented source map

The top level of the checkout contains the following major responsibilities.

| Path | Responsibility | First question to ask |
|---|---|---|
| `tu_cmodel/` | C model, public headers, engines, infrastructure, bindings | Which objects enter the normal libraries? |
| `config/` | shipped JSON/YAML architecture descriptions | Which fields are parsed, propagated, consumed, and tested? |
| `tests/` | focused tests, sweeps, and integration harnesses | Which aggregate target, if any, enforces each test? |
| `compiler/` | demonstration ONNX-to-C frontend | Does emitted code compile and execute? |
| `examples/` | two repository-contained ONNX inputs plus an externally resolved GPT-block symlink | Which operators lower to the TU rather than host fallback, and which inputs require sibling workspaces? |
| `tools/` | CI and report scripts | Does failure propagate to the shell exit status? |
| `scripts/` | generators and exploration utilities | What tracked files can they overwrite? |
| `docs/` | design notes, generated reference, exploration reports | Is a document current, generated, historical, or aspirational? |
| `bindings/` and `tu_cmodel/bindings/` | language/simulator integration surfaces | Are they built, loaded, and exercised? |
| `.github/workflows/` | hosted CI intent | What local script and target does the workflow actually invoke? |

### 3.3.1 The C model tree

Within `tu_cmodel/`, the root holds the compatibility-facing lifecycle and core facilities:

- `tu_cmodel.[ch]`: global state, initialization, configuration bridge, DMA wrappers, MMA, stats, command helpers, and ASM entry;
- `tu_config.h`: compile-time defaults and runtime configuration structure;
- `tu_precision.[ch]`, `rounding.[ch]`, `fp8.[ch]`, and `tf32.[ch]`: numerical formats and conversion support;
- `tu_sram.[ch]`, `tu_dma.[ch]`, and `dma_descriptor.[ch]`: local storage and data movement;
- `command_queue.[ch]`: submitted command execution;
- `tu_core.[ch]` and `tu_cluster.[ch]`: multi-core wrappers;
- `tu_status.[ch]`: status and error infrastructure.

Subdirectories group additional responsibilities:

```text
tu_cmodel/
├── compute/            operator engines and pipeline controller
│   └── dataflow/       WS, OS, RS plugins, registry, dispatcher
├── memory/             DRAM, hierarchy, double buffer, address generation,
│                       weight compression
├── isa/                ISA, scheduler, liveness allocator
├── infra/              JSON/config, logging, context, debug
├── perf/               counters, event trace, power, standalone cycle model
├── sparsity/           structured 2:4 model
└── bindings/           DPI-C integration
```

The README's diagram is an architectural summary, not a literal directory listing. For example, precision sources and DMA sources are mostly at the root, dataflows live under `compute/dataflow/`, and event tracing lives under `perf/`. Use the diagram to understand responsibilities, then use the live tree and Makefile to locate implementation.

### 3.3.2 The public header is a compatibility surface, not a complete truth table

`tu_cmodel/tu_cmodel.h` is the broad entry header used by tests and generated code. It exposes initialization, direct DMA and MMA calls, command-queue helpers, dataflow selection, ASM execution, state, and compatibility aliases.

Its preamble still describes the historical fixed 16×16 TinyTU model, while the live implementation supports runtime PE dimensions and registers three dataflow plugins. It also contains a duplicate declaration of `tu_fp32_to_fp16_buffer` with equivalent parameter types written differently. These facts do not prevent the minimal program in this chapter from compiling. They do mean that header prose and declaration presence should not replace call-path evidence.

---

## 3.4 Building the two libraries

At the pinned snapshot, the default target is:

```make
all: libtucmodel.a libtucmodel.so
```

Both libraries are built from the same `TU_OBJS` list. A clean reproduction used:

```bash
cd /home/zxy/Workplace/projects/tusim
make clean
make -j2
```

Observed result:

```text
clean: exit 0
build: exit 0
libtucmodel.a: 458128 bytes
libtucmodel.so: 298752 bytes
```

GCC emitted two nonfatal source warnings: an unused `comp_names` variable in `infra/logging.c` and an unused `parse_opt_uint` helper in `infra/config.c`.

### 3.4.1 Static and shared do not mean two implementations

`libtucmodel.a` is an archive of relocatable objects. When an executable links an archive explicitly, the linker copies required object content into the executable. `libtucmodel.so` is loaded at runtime and can be shared among processes. The two forms here use the same object list, so they should represent the same compiled source state after one clean default build.

The operational difference matters during iterative work. Many test recipes use:

```text
-L. -ltucmodel
```

A linker normally prefers a matching shared library when both forms are available. If a developer rebuilds only `libtucmodel.a` while an older `libtucmodel.so` remains, the test may link the older shared object. Whether that executable later loads the local library also depends on rpath, loader configuration, and `LD_LIBRARY_PATH`.

For textbook reproduction, choose one of two safe patterns:

1. run `make clean && make` before targets that use `-ltucmodel`; or
2. link a small experiment explicitly with `./libtucmodel.a`.

The first tests the normal build. The second removes library-selection ambiguity for a standalone probe.

### 3.4.2 Audit library membership directly

The reproduced static archive contained 44 members. Selected observations were:

```text
tu_cmodel.o       present
row_stationary.o  present
tu_dpi.o          present
cycle_model.o     absent
```

This establishes that the core, RS plugin, and DPI implementation are normal library members. It also confirms Chapter 2's result: `perf/cycle_model.c` exists, but `cycle_model.o` is not in `TU_OBJS`.

The important pattern is general:

```bash
ar t libtucmodel.a
nm -D --defined-only libtucmodel.so
```

Use archive membership to answer “what was packaged?” and exported symbols to answer “what can a dynamically linked caller resolve?” Neither proves that a runtime configuration reaches the mechanism.

---

## 3.5 Select tests by the claim you need

Tusim's Makefile contains focused unit tests, cross-engine tests, sweeps, benchmarks, and aggregate targets. Their names do not imply identical scope.

### 3.5.1 Quick smoke

The advertised pre-commit smoke target is shown below. Its binaries dynamically depend on `libtucmodel.so` and have no rpath, so make the local library directory explicit rather than relying on the audit host's trailing empty `LD_LIBRARY_PATH` component:

```bash
LD_LIBRARY_PATH="$PWD${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" make test-quick
```

At the pinned snapshot it depends on four paths and reproduced:

```text
Parameterized CModel: 19/19 passed
Command queue:          9/9 passed
DMA descriptor engine: 10/10 passed
ASM identity smoke:     PASS
```

This is useful evidence that the freshly built core, command queue, DMA descriptor path, and ASM interpreter execute. It is not evidence that every object in the 44-member library was exercised. In particular, it does not cover every precision, engine, multicore, observability, power, compiler, or sweep target.

### 3.5.2 Focused configuration path

Because this chapter will initialize from JSON, the relevant focused target is:

```bash
make test-config
```

It reproduced `20/20` passing checks for parser primitives, nested configuration, defaults, rejection of invalid values, file loading, runtime conversion, and configured MMA.

Its compile step emitted many warnings because a `CHECK` macro expands to `return;` inside `int main(void)`. The test executable returned success, so the assertions passed in this run. The warnings still matter: a strict `-Werror` build would reject this translation unit, and a failing `CHECK` has an invalid return form. Passing runtime checks and warning-clean compilation are separate quality gates.

### 3.5.3 Aggregate names require source inspection

The Makefile has at least three broad-looking interfaces:

- `test-quick`: four smoke paths;
- `test`: a larger but still selected set of unit/integration targets;
- `test-full`: an ONNX code-generation pipeline, not a superset of `test`.

Therefore “full” does not mean “all repository tests.” Always inspect dependencies and recipes. The shell CI wrapper defines yet another selected list.

---

## 3.6 First execution through the public C API

A useful first program should be small enough to verify by inspection but broad enough to prove a public path. The preserved example uses:

```text
JSON file
   │
   ▼
tu_init_from_file
   │ parse, validate, convert, initialize
   ▼
tu_dma_load_w + tu_dma_load_a
   │
   ▼
tu_mma(2, 2, 3, ...)
   │
   ▼
tu_dma_store_o
   │
   ├──► exact functional check
   └──► tu_print_stats
```

The complete source is [`ch03_first_execution.c`](../../experiments/ch03_first_execution.c), and its configuration is [`ch03_minimal_config.json`](../../experiments/ch03_minimal_config.json).

### 3.6.1 Workload and orientation

The API defines:

\[
O_{M\times N} \mathrel{+}= W_{M\times K} A_{K\times N}.
\]

The example uses:

\[
W = \begin{bmatrix}1&2&3\\4&5&6\end{bmatrix},\qquad
A = \begin{bmatrix}7&8\\9&10\\11&12\end{bmatrix}.
\]

Therefore:

\[
O = \begin{bmatrix}
1\cdot7+2\cdot9+3\cdot11 & 1\cdot8+2\cdot10+3\cdot12\\
4\cdot7+5\cdot9+6\cdot11 & 4\cdot8+5\cdot10+6\cdot12
\end{bmatrix}
= \begin{bmatrix}58&64\\139&154\end{bmatrix}.
\]

These integer values are exactly representable in FP16 inputs and FP32 accumulation, so a tolerance of `0.001` is conservative for this example.

### 3.6.2 Minimal JSON contract

The configuration requests a 4×4 PE array, output-stationary dataflow, and three 8 KiB SRAM regions:

```json
{
  "tu": {
    "compute": {
      "pe_array": {
        "rows": 4,
        "cols": 4,
        "dataflow": "output_stationary"
      }
    },
    "memory": {
      "sram": {
        "w_buffer_kb": 8,
        "a_buffer_kb": 8,
        "o_buffer_kb": 8
      }
    }
  }
}
```

This is deliberately narrow. The executable checks that file loading changes the initialized geometry and all three capacities. It also exposes a negative result: the parser stores the requested output-stationary mode, but `tu_config_to_runtime` does not copy `dataflow_mode`, and `tu_init_with_config` selects compile-time `TU_DATAFLOW_MODE`. The active mode therefore remains weight-stationary. Chapter 4 audits that propagation gap field by field.

### 3.6.3 Compile with explicit archive linkage

First build the archive, then define checkout roots. This is the portable form of the absolute-path command used in the audit:

```bash
export TUSIM_ROOT=/path/to/tusim
export BOOK_ROOT=/path/to/tusim-book
make -C "$TUSIM_ROOT" libtucmodel.a
cc -O2 -Wall -Wextra -std=c11 \
  -I"$TUSIM_ROOT" \
  -o /tmp/tusim-ch03-first-execution \
  "$BOOK_ROOT/experiments/ch03_first_execution.c" \
  "$TUSIM_ROOT/libtucmodel.a" -lm
```

Then run:

```bash
/tmp/tusim-ch03-first-execution \
  "$BOOK_ROOT/experiments/ch03_minimal_config.json"
```

The build and run both returned zero. The relevant output was:

```text
requested dataflow = output_stationary; active dataflow = weight_stationary
O = [[58, 64], [139, 154]]
```

This is **executable and integrated evidence for the named path**: the public file initializer reached parsing, conversion, runtime initialization, propagated geometry and SRAM capacities, public DMA wrappers, direct MMA, and output store. It is simultaneously executable evidence that JSON dataflow selection does not propagate at this snapshot. It is not a claim that all JSON fields or all command interfaces are integrated.

---

## 3.7 Reading the first report without over-interpreting it

An abridged, normalized excerpt of the same run is:

```text
PE Array    : 4×4 (16 MACs)
Dataflow    : weight_stationary
DMA bytes   : 40
MMA calls   : 1
MMA tiles   : 1 (4×4×4 per tile)
MMA FLOPS   : 24 (FP16 MACs)
Est. cycles : 19
SRAM W/A/O  : each reported reads=0 writes=0 conflicts=0 stalls=0 bw_util=0.0%
DMA         : 40 bytes, 3 transfers, 153 cycles
```

The source computes `(16 MACs)` as `pe_rows × pe_cols`: 16 configured PE/MAC lanes under the one-MAC-per-PE assumption. It is capacity, not 16 executed operations, measured throughput, or utilization.

Some fields pass immediate conservation checks:

- W input: `2×3×2 = 12` B;
- A input: `3×2×2 = 12` B;
- O output: `2×2×4 = 16` B;
- total transferred: `12+12+16 = 40` B;
- MMA calls: one;
- useful arithmetic: `M×N×K = 12` MACs.

Under the common convention that one multiply and one addition count as two floating-point operations, 12 MACs equal 24 FLOPs. The line `MMA FLOPS: 24 (FP16 MACs)` mixes those terms: the number matches FLOPs, while the parenthetical names MACs. Quote the number only with its formula and caveat.

The tile line also needs care. One edge tile is correct, but `(4×4×4 per tile)` states configured geometry. It does not mean this `2×2×3` workload performed 64 useful MACs.

Most importantly, aggregate `Est. cycles` is 19 while the DMA subsystem prints 153 cycles. The three SRAM regions report no reads or writes despite completed transfers and compute. These observations show that the report combines partially wired accounting surfaces. They do not justify adding, subtracting, or selecting one cycle total as measured latency.

> **Fidelity box — first execution**
>
> **Established:** exact functional output for one FP16-input/FP32-accumulate GEMM; JSON-selected 4×4 geometry and three 8 KiB capacities; observed non-propagation of the requested output-stationary mode; 40 B through named DMA wrappers; one MMA call; clean explicit static linkage.
>
> **Not established:** calibrated hardware latency, one unified cycle domain, complete SRAM traffic accounting, physical utilization, energy, concurrency, or arbitrary configuration propagation.
>
> **Safe label:** executable functional path with heterogeneous estimated/event counters.

---

## 3.8 The compiler demonstration: emission is not execution

The Makefile's compiler target runs:

```bash
make test-compiler
```

`examples/gpt_block.onnx` is not a repository-contained model. Git tracks it as a symbolic link to `../../onnx-playground/GPT-block/gpt_block.onnx`; the link resolved on the audit host because that sibling workspace existed. A fresh Tusim checkout alone cannot reproduce this target. With that external prerequisite present, the Python frontend loaded and checked the model, analyzed 133 nodes, and wrote a 98,718-line C file. It also reported:

```text
TU ops: 0, Host ops: 133
W-buffer: 0/131072 bytes
```

That is a successful **frontend/code-emission** result. It is not a TU execution. Every graph node was classified as host work in that run.

The nominal pipeline target is:

```bash
make test-full
```

Its generated C failed to link because calls to `host_gemm` were unresolved. No executable was produced, so the subsequent run reported that `/tmp/gpt_block_tu` did not exist. Yet Make returned success because both commands end in `|| true`.

The two repository-contained ONNX examples behaved similarly when tested directly:

| Model | Frontend | Reported lowering | Generated C |
|---|---:|---|---|
| `single_linear.onnx` | pass | 0 TU, 1 host | link failure: `host_gemm` |
| `tiny_mlp.onnx` | pass | 0 TU, 3 host | link failure: `host_gemm` |
| external `gpt_block.onnx` symlink target | pass | 0 TU, 133 host | link failure: `host_gemm` |

The generator emits fallback function definitions only for operators outside `Gemm` and `MatMul`, while a failed Gemm/MatMul lowering can still emit a `host_gemm` call. This explains the unresolved symbol at the C boundary. The deeper reason the supplied linear layers fall back is a Chapter 23 compiler question.

A defensible characterization is:

> At snapshot `e918c80`, the demonstration compiler accepts and analyzes the two repository-contained examples and the locally resolved external GPT-block model, and emits C text. None produced a runnable generated program in this audit. The `test-full` target masks this failure and is not an enforceable end-to-end success gate; it also has an undeclared sibling-workspace prerequisite.

---

## 3.9 Documentation generation has two different states

### 3.9.1 Generated configuration reference

The target:

```bash
make config-docs
```

builds a temporary program against `libtucmodel.a`, calls `tu_config_emit_docs`, and overwrites `docs/CONFIG_REFERENCE.md`. In this environment it returned zero, and a Git diff check showed that the regenerated file exactly matched the tracked version.

This is strong reproducibility evidence for that generated document at the pinned snapshot. It is also a reminder that a documentation target can modify tracked source-tree files. Run it only with a known-clean tree and inspect the diff.

### 3.9.2 Doxygen API output

The target:

```bash
make docs-api
```

checks for Doxygen, creates `docs/api`, and invokes the repository `Doxyfile`. Doxygen and Graphviz `dot` were absent in the verification environment, so the target failed before generation. No `docs/api/html/index.html` was produced.

The correct reproduced conclusion is **blocked by missing local prerequisites**, not “the Doxyfile is broken.” Static inspection reveals a second limitation: the recipe pipes Doxygen through `grep ... || true`, then unconditionally prints success without checking `docs/api/html/index.html`. It also does not preflight Graphviz `dot`. Thus even a provisioned `make docs-api` is not an enforceable generation gate. The Doxyfile additionally excludes several core implementation `.c` files, including `tu_cmodel.c`, while including headers and many other directories.

---

## 3.10 CI intent versus an executable gate

`.github/workflows/ci.yml` defines quick, regression, nightly, and coverage jobs. Those jobs invoke `tools/ci_runner.sh`. A local run of:

```bash
bash tools/ci_runner.sh --quick
```

failed before the strict build. The script creates `build/ci_reports/logs`, then calls `make clean`; the Makefile clean recipe removes `build/ci_reports`. The next redirection therefore fails because its target directory no longer exists.

Static inspection establishes additional downstream gate defects that remain after fixing that first blocker:

- the “compile only” phase invokes Make targets that compile **and run** because the Makefile does not consume `BUILD_ONLY`; fallback failures are suppressed;
- CI quick mode selects `test-golden`, whereas Makefile `test-quick` selects `test-asm`;
- quick golden execution uses `|| true`, followed by a condition whose `$?` alternative makes the result pass even without a `PASS` match;
- full-mode compiler integration marks success after Python C emission and never compiles or runs the generated program.

This audit establishes executable evidence for the first wrapper defect and source evidence for the downstream defects. It does not establish the current status of a remote GitHub Actions run, which was outside this chapter's live-source scope.

The broader lesson is that CI YAML is intent. The executable gate includes:

1. workflow trigger;
2. installed dependencies;
3. wrapper script;
4. build flags;
5. selected tests;
6. failure propagation;
7. artifact/report handling.

A green-looking target name cannot substitute for checking this chain.

---

## 3.11 Repository hygiene is part of reproducibility

Tusim ignores objects, libraries, test binaries, build output, and `libtucmodel.so`. However, `tu_cmodel/tu_cmodel.o` is already tracked. Git ignore rules do not apply retroactively to tracked files, so a normal build modifies it in the working tree.

A careful experiment therefore has both an execution phase and a closure phase:

```bash
# Before
 git rev-parse HEAD
 git status --short

# Execute named build/tests
 make clean
 make
 LD_LIBRARY_PATH="$PWD${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" make test-quick

# After recording evidence
 git restore --source=HEAD -- tu_cmodel/tu_cmodel.o
 git status --short
```

Do not use a blanket reset when unrelated work may exist. Record the pre-state, identify exactly which tracked path the experiment changed, restore only that path, and verify the final status. Restoration must be the **last** source-tree operation. During review, running Make after restoring the tracked historical object caused Make to rearchive that newer-mtime but ABI-stale object beside freshly built objects; the resulting static probe aborted with stack corruption. A subsequent `make clean && make` removed the mismatch. Never resume building from the cosmetically clean restored state without another clean rebuild.

Generated compiler C and binaries belong in `/tmp`. Book probes and experiment records belong in the standalone book workspace, not the Tusim repository. Source changes, commits, and pushes are not part of running the book example.

---

## 3.12 Verification matrix

| Claim | Evidence class | Status | Limit |
|---|---|---|---|
| Default static and shared build | executable | pass | two source warnings; tracked object hygiene issue |
| Quick core/cmdq/DMA/ASM paths | executable | pass with explicit local loader path | selected smoke paths, not all library objects |
| JSON parse and selected runtime propagation | source + executable | mixed | geometry/capacities propagate; requested dataflow does not |
| Minimal GEMM result | executable + analytical oracle | pass | one exact small workload |
| Printed performance report | executable observation | partial | heterogeneous counters; no unified calibrated timing claim |
| Repository-contained ONNX examples | executable frontend and C-link check | frontend pass, generated link fail | zero TU operations; undefined `host_gemm` |
| GPT-block Make target | environment-dependent executable | same link failure when sibling model exists | tracked symlink target is external to Tusim |
| Config-reference generator | executable + Git diff | pass | one generated document |
| Doxygen API generator | source audit + blocked execution | not enforced | missing tools here; recipe suppresses downstream failures |
| Shell CI wrapper | executable + source audit | fail | first blocker plus downstream false/incomplete gates |
| Hardware correspondence | none in this chapter | not claimed | requires RTL/FPGA/silicon evidence |

This matrix is the closure point for the chapter's opening question. Each status names what was run or inspected and keeps its boundary visible.

---

## 3.13 Trade-offs in first-execution workflows

| Approach | Benefit | Cost/risk | Best regime |
|---|---|---|---|
| Incremental `make` | fast iteration | stale object/shared-library ambiguity | local development after a known clean baseline |
| Clean default build | validates normal static+shared graph | slower; changes tracked object | edition reproduction and release checks |
| Explicit static probe | deterministic library selection, portable command record | bypasses shared-library loading path | textbook examples and focused diagnosis |
| Quick smoke suite | fast, broad enough for core regressions | omits many subsystems | pre-commit core confidence |
| Focused test | precise contract and failures | does not prove public integration or CI inclusion | subsystem development and claim support |
| Large aggregate target | catches interactions when correctly enforced | long, can hide omissions or suppressed failures | regression after dependency/failure audit |
| Generated docs | stays close to executable schema/API | can overwrite tracked files; needs tools | clean-tree release/document validation |
| Compiler code emission | exposes lowering decisions and generated interface | emitted text may not compile or run | compiler diagnostics before end-to-end claims |

No single workflow is universally best. A fast incremental build is valuable during development; a clean explicit probe is stronger for a book result. A smoke suite optimizes feedback latency; focused tests optimize causal localization. The correct choice follows the claim.

---

## 3.14 Common failure modes

### Failure mode 1: treating the README diagram as the filesystem

**Symptom:** searching for a literal `tu_cmodel/precision/` directory.

**Correction:** use the diagram for architectural categories, then inspect tracked paths and build rules.

### Failure mode 2: treating source presence as integration

**Symptom:** calling the standalone cycle model part of `libtucmodel`.

**Correction:** inspect `TU_OBJS` and archive membership.

### Failure mode 3: rebuilding only the archive while tests select the shared library

**Symptom:** a source edit appears to have no effect.

**Correction:** clean-build both libraries or link the archive explicitly.

### Failure mode 4: interpreting `test-quick` as complete validation

**Symptom:** claiming all 44 library objects are tested.

**Correction:** name the four smoke paths and add focused targets as needed.

### Failure mode 5: trusting target exit status without reading output

**Symptom:** calling `test-full` successful despite linker errors.

**Correction:** inspect recipes for `|| true`, capture generated artifact existence, and run it.

### Failure mode 6: equating emitted C with a working compiler

**Symptom:** counting generated lines as end-to-end execution evidence.

**Correction:** require frontend acceptance, nontrivial TU lowering, C compilation, runtime execution, and output verification separately.

### Failure mode 7: adding every printed cycle value

**Symptom:** combining 19 aggregate estimated cycles and 153 DMA cycles.

**Correction:** demand matching boundaries, clocks, overlap rules, and attribution before composition.

### Failure mode 8: assuming zero counters mean zero activity

**Symptom:** concluding that SRAM was bypassed because its printed reads/writes are zero.

**Correction:** inspect whether the executed bulk paths increment those counters.

### Failure mode 9: trusting a generated-doc target's success banner

**Symptom:** accepting “Documentation generated” after the recipe suppresses Doxygen's exit status.

**Correction:** capture the generator's real status and verify the expected HTML index.

### Failure mode 10: running generators in a dirty tree

**Symptom:** losing track of whether a documentation diff is generated or pre-existing.

**Correction:** record status before generation and inspect only intended paths afterward.

### Failure mode 11: believing ignored means untracked

**Symptom:** a build unexpectedly changes `tu_cmodel.o`, or a later Make run rearchives the restored historical object and produces ABI-inconsistent behavior.

**Correction:** check `git ls-files`; ignore rules do not remove tracked artifacts. Restore the object only after every build/run step, and use `make clean` before any later build.

---

## 3.15 Implications for Tusim development

This audit exposes development questions, not automatic source changes.

1. **Build determinism:** tests could link the archive explicitly or define separate static/shared validation targets.
2. **End-to-end enforcement:** `test-full` should fail when generated code does not compile or run.
3. **Compiler contracts:** unsupported lowering could fail early with a structured diagnostic, or generated host fallbacks could be complete and linkable.
4. **CI artifact ordering:** the report directory should be created after the clean phase.
5. **Repository hygiene:** tracked object files could be removed in a reviewed source change.
6. **Metric contracts:** stats should distinguish useful MACs, FLOPs, configured tile capacity, cycle domains, and counter coverage.
7. **Documentation enforcement:** Doxygen failures and expected output existence should be checked; generated API documentation should state excluded implementation paths.

Each proposal has costs. Forcing static linkage simplifies reproducibility but stops testing shared loading. Rejecting unsupported ONNX graphs gives honest failure but reduces partial-code-generation flexibility. Wiring every SRAM path into detailed counters increases fidelity and verification burden. Chapter 1's rule still applies: choose improvements according to an architecture or workflow decision, not because a gap list exists.

---

## Summary

1. A repository tour should follow responsibilities and executable paths, not filenames alone.
2. Present, compiled, library-member, linked, reachable, focused-tested, aggregate-tested, and validated are distinct states.
3. The pinned checkout cleanly builds `libtucmodel.a` and `libtucmodel.so` from a 44-object list, with warnings.
4. The standalone cycle model remains outside that normal object list.
5. `make test-quick` reproduces 19/19 core, 9/9 command-queue, 10/10 DMA, and one ASM smoke pass; it is not the entire suite.
6. `make test-config` reproduces 20/20 checks for the named parser/config/runtime path, with compile warnings.
7. The preserved direct example proves JSON initialization, geometry/capacity propagation, DMA, MMA, and output store by producing `[[58,64],[139,154]]`; it also proves the requested output-stationary mode does not propagate.
8. Its counters are heterogeneous: 40 transfer bytes and one call are interpretable, while MAC/FLOP terminology, SRAM coverage, and cycle totals require qualification.
9. The ONNX frontend emits C for two contained examples and an externally resolved GPT symlink target, but all observed zero TU operations and generated programs failed to link; `test-full` masks the failure.
10. Config-reference generation is reproducible. Doxygen execution is blocked here and its recipe suppresses downstream failures. The shell CI wrapper fails before build and contains additional false/incomplete gate logic.
11. Reproducibility ends with repository cleanup and a verified status, not with the program's last line.

## Review questions

1. What additional evidence separates a compiled source from an integrated feature?
2. Why can an object be a library member yet remain untested?
3. What does `ar t libtucmodel.a` establish, and what does it not establish?
4. Why can `-L. -ltucmodel` produce stale-code confusion?
5. Which four paths does `test-quick` exercise at this snapshot?
6. Why is `test-full` not a superset of `test`?
7. What public path does the minimal example establish?
8. Derive the minimal example's 40 transferred bytes.
9. Distinguish its 12 useful MACs from 24 FLOPs and a 4×4×4 configured tile.
10. Why may 19 estimated cycles not be combined with 153 DMA cycles?
11. What does zero SRAM counter activity fail to prove?
12. Which stages are required before emitted compiler C counts as end-to-end success?
13. Why is the Doxygen result “blocked” rather than “failed source validation”?
14. How does the CI wrapper delete its own output directory?
15. Why can a `.gitignore` entry fail to protect a tracked object?

## Design exercises

### Exercise 1 — Integration ladder

Choose one Tusim module outside the quick smoke set. Record source presence, object compilation, archive membership, exported API, public reachability, focused test, aggregate target, and external validation as separate fields.

### Exercise 2 — Static versus shared experiment

Build a probe once with `./libtucmodel.a` and once with `-L. -ltucmodel`. Use binary metadata to record dependencies. Change only one library form in a disposable checkout and demonstrate the stale-selection risk without modifying the canonical repository.

### Exercise 3 — Counter dictionary

For every field printed by `tu_print_stats` in the minimal run, define unit, increment event, scope, reset behavior, cycle domain, legal range, and composition rule. Mark fields whose current implementation cannot satisfy the proposed contract.

### Exercise 4 — Honest compiler gate

Design acceptance criteria for `test-full`: minimum TU-lowered operations, generated-C warning policy, successful linkage, executable existence, runtime exit status, and numerical output comparison. Explain which unsupported graphs should be rejected versus emitted with host fallbacks.

### Exercise 5 — CI repair plan

Without changing source, write a minimal patch plan for the report-directory ordering defect. Include a failing regression test, expected shell exit status, and artifact checks. Then identify why warning-clean CI may uncover additional failures after the first defect is fixed.

### Exercise 6 — Hygiene protocol

Design an experiment protocol that preserves pre-existing tracked and untracked work. Include status capture, temporary artifact placement, exact restoration, and final verification. Explain why `git reset --hard` is unsafe as a generic cleanup step.

---

## Primary repository references

- Tusim `Makefile:14–127, 210–236, 503–572`, snapshot `e918c80`.
- Tusim `README.md:1–111`, snapshot `e918c80`.
- Tusim `.github/workflows/ci.yml:18–114`, snapshot `e918c80`.
- Tusim `tools/ci_runner.sh:140–291`, snapshot `e918c80`.
- Tusim `Doxyfile:39–59, 73–79, 106–125`, snapshot `e918c80`.
- Tusim `tu_cmodel/tu_cmodel.h:1–317` and `tu_cmodel/tu_cmodel.c:42–303`, snapshot `e918c80`.
- Tusim `tu_cmodel/infra/config.c:241–316`, snapshot `e918c80`.
- Tusim `tests/test_cmodel.c`, `tests/test_command_queue.c`, `tests/test_dma.c`, `tests/test_config.c:163–199, 292–339`, and `tests/test_asm.c`, snapshot `e918c80`.
- Tusim `compiler/onnx_to_tu.py:532–791`; `examples/single_linear.onnx`; `examples/tiny_mlp.onnx`; and external symlink `examples/gpt_block.onnx`, snapshot `e918c80`.
- [Chapter 3 experiment record](../../experiments/ch03-repository-and-first-execution-audit-2026-07-25.md).
- [Chapter 3 source and claim ledger](../../notes/chapter-03-source-and-claim-ledger.md).
