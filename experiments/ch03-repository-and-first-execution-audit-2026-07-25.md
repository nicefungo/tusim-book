# Chapter 3 Experiment — Repository and First Execution Audit

## Purpose

Re-audit the build, smoke tests, selected unit/config path, compiler demonstration, documentation generation, and a minimal public C API execution at Tusim snapshot `e918c80b6fce833cd1fcae97730fa841c2176f25`.

This record distinguishes command exit status from demonstrated behavior. It is not a claim that all modules or tests were exercised.

## Environment

```text
Architecture: aarch64
Compiler: cc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0
Make: GNU Make 4.3
Python: 3.11.15
NumPy: 2.4.6
ONNX: 1.21.0
Doxygen: absent
Graphviz dot: absent
```

Tusim checkout: `/home/zxy/Workplace/projects/tusim`

Book workspace: `/home/zxy/Workplace/books/tusim-book`

## 1. Snapshot and workspace checks

```bash
cd /home/zxy/Workplace/projects/tusim
git rev-parse HEAD
git status --short
```

Observed before build:

```text
e918c80b6fce833cd1fcae97730fa841c2176f25
```

The status output was empty. The book workspace was separately initialized as a local-only Git repository after user authorization; it has no remote.

## 2. Clean normal build

```bash
make clean
make -j2
```

Observed:

```text
clean: exit 0
build: exit 0
libtucmodel.a: 458128 bytes
libtucmodel.so: 298752 bytes
```

The build emitted two source warnings:

```text
tu_cmodel/infra/logging.c:229:17: warning: unused variable ‘comp_names’
tu_cmodel/infra/config.c:62:13: warning: ‘parse_opt_uint’ defined but not used
```

Both libraries use the 44 entries in `TU_OBJS`. Archive inspection found:

```text
tu_cmodel.o       PRESENT
row_stationary.o  PRESENT
tu_dpi.o          PRESENT
cycle_model.o     ABSENT
```

After building, `git status --short` reported:

```text
 M tu_cmodel/tu_cmodel.o
```

`tu_cmodel/tu_cmodel.o` is tracked even though `.gitignore` includes `*.o`.

## 3. Quick smoke suite

```bash
LD_LIBRARY_PATH="$PWD${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" make test-quick
```

The original audit shell already had a trailing empty `LD_LIBRARY_PATH` component, so the first plain invocation returned `0`. The explicit form above was rerun during review and also returned `0`; it is the self-contained command readers should use.

Observed suite summaries:

```text
CModel:       19/19 tests passed
Command queue: 9/9 tests passed
DMA:          10/10 tests passed
ASM:          self-contained identity smoke test PASS
Quick smoke test passed
```

This target covers only `test-cmodel`, `test-cmdq`, `test-dma`, and `test-asm`.

Most corresponding recipes use:

```text
-L. -ltucmodel
```

`readelf -d test-cmodel` showed a dependency on `libtucmodel.so`. The active `LD_LIBRARY_PATH` ended with `:`, which makes the current directory searchable in this shell. Therefore this run selected the newly rebuilt local shared library. That fact is environment-specific; a stale shared library can be selected if only the archive is rebuilt and a local `.so` remains.

## 4. Focused JSON/config suite

```bash
make test-config
```

Observed exit status: `0`.

```text
20/20 tests passed
```

The suite covered JSON primitives/containers, defaults, nested field loading, validation failures, runtime conversion, file loading, and configured MMA. Compilation emitted many instances of:

```text
warning: ‘return’ with no value, in function returning non-void
```

because `CHECK` expands to a bare `return` inside `int main(void)`.

## 5. Minimal public C API execution

Preserved sources:

- [`ch03_first_execution.c`](ch03_first_execution.c)
- [`ch03_minimal_config.json`](ch03_minimal_config.json)

The JSON config requests a 4×4 PE array, output-stationary dataflow, and 8 KiB each for W, A, and O SRAM. The program asserts that geometry and capacities propagated, records the active dataflow, and computes:

```text
W = [[1,2,3], [4,5,6]]
A = [[7,8], [9,10], [11,12]]
O = W × A
```

Build with explicit static linkage:

```bash
cc -O2 -Wall -Wextra -std=c11 \
  -I/home/zxy/Workplace/projects/tusim \
  -o /tmp/tusim-ch03-first-execution \
  /home/zxy/Workplace/books/tusim-book/experiments/ch03_first_execution.c \
  /home/zxy/Workplace/projects/tusim/libtucmodel.a -lm
```

Run:

```bash
/tmp/tusim-ch03-first-execution \
  /home/zxy/Workplace/books/tusim-book/experiments/ch03_minimal_config.json
```

Observed build and run status: `0`, `0`.

Observed relevant result after the revised review probe:

```text
requested dataflow = output_stationary; active dataflow = weight_stationary
O = [[58, 64], [139, 154]]
```

Abridged, normalized report fields (`tu_print_stats` emits separate W/A/O lines):

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

Sanity checks:

- transfer bytes = 12 + 12 + 16 = 40 B;
- useful arithmetic = 2×2×3 = 12 MACs = 24 FLOPs under a two-FLOP MAC convention;
- output equals the exact FP32 reference for these integer-valued FP16 inputs.
- `g_tu` reports 4×4 geometry and 8192-byte W/A/O capacities, satisfying the executable assertions.

Unsafe interpretations:

- `24` is not simultaneously 24 FLOPs and 24 MACs;
- `(16 MACs)` means 16 configured PE/MAC lanes, not 16 executed operations or measured utilization;
- 4×4×4 tile geometry does not imply 64 useful MACs for this edge workload;
- 19 aggregate estimated cycles and 153 DMA cycles are not shown to share a composable accounting boundary;
- zero SRAM access counters do not mean SRAM was unused.
- JSON `output_stationary` is parsed but not copied by `tu_config_to_runtime`; active runtime dataflow remains compile-time-default `weight_stationary`.

## 6. Compiler demonstration

### Make target

```bash
make test-compiler
```

Observed exit status: `0`.

`examples/gpt_block.onnx` is tracked as mode `120000` and points to `../../onnx-playground/GPT-block/gpt_block.onnx`. The target existed on this host, but a fresh Tusim checkout alone cannot reproduce it. With that external sibling-workspace prerequisite present:

```text
Nodes: 133
TU ops: 0, Host ops: 133
W-buffer: 0/131072 bytes
Wrote: /tmp/gpt_block_tu.c
98718 /tmp/gpt_block_tu.c
```

This demonstrates ONNX loading/checking, graph analysis, and C text emission only.

### Full target

```bash
make test-full
```

Observed exit status: `0`, but generated-code linkage failed:

```text
undefined reference to `host_gemm'
collect2: error: ld returned 1 exit status
/bin/sh: 1: /tmp/gpt_block_tu: not found
```

The Makefile appends `|| true` to both generated-code compile and execution, so the target's success status is a false positive.

### Repository-contained models

Commands:

```bash
python3 compiler/onnx_to_tu.py examples/single_linear.onnx \
  -o /tmp/single_linear_tu.c -n single_linear
cc -O2 -Wall -Wextra -std=c11 -I. \
  -o /tmp/single_linear_tu /tmp/single_linear_tu.c ./libtucmodel.a -lm

python3 compiler/onnx_to_tu.py examples/tiny_mlp.onnx \
  -o /tmp/tiny_mlp_tu.c -n tiny_mlp
cc -O2 -Wall -Wextra -std=c11 -I. \
  -o /tmp/tiny_mlp_tu /tmp/tiny_mlp_tu.c ./libtucmodel.a -lm
```

Observed:

```text
single_linear: frontend 0; TU ops 0, Host ops 1; C link 1; undefined host_gemm
tiny_mlp:      frontend 0; TU ops 0, Host ops 3; C link 1; undefined host_gemm
```

The two repository-contained examples and the locally resolved external GPT model all fail the end-to-end generated-program criterion at this snapshot.

## 7. Documentation generation

### Config reference

```bash
make config-docs
git diff --exit-code -- docs/CONFIG_REFERENCE.md
```

Observed statuses: `0`, `0`. The generated reference matched the tracked file exactly.

### Doxygen API

```bash
make docs-api
```

Observed status: `2` from Make after the recipe reported:

```text
doxygen not found. Install: sudo apt install doxygen graphviz
```

No `docs/api/html/index.html` was produced. This execution result is a missing-prerequisite result, not proof that Doxygen itself fails under a complete environment. Source inspection nevertheless shows that the recipe pipes Doxygen through `grep ... || true`, unconditionally prints success, does not preflight `dot`, and does not verify the HTML index. The target is therefore not an enforceable generation gate even when tools are present.

## 8. CI wrapper

```bash
bash tools/ci_runner.sh --quick
```

Observed status: `1`.

```text
Cleaning previous build artifacts...
build/ci_reports/logs/build_lib.log: No such file or directory
build/ci_reports/summary_...md: No such file or directory
```

The script creates `build/ci_reports` and `logs` before its build phase, then calls `make clean`. The Makefile clean target removes `build/ci_reports`, so subsequent redirection fails. The run never reached the intended strict build or tests.

The GitHub workflow invokes this wrapper. Static inspection found downstream defects beyond the reproduced first blocker: `BUILD_ONLY` is unused by the Makefile so “compile only” targets run; fallback failures are suppressed; quick CI selects `test-golden` rather than Makefile quick's `test-asm`; quick golden's `|| true`/`$?` condition can report a false pass; and full-mode compiler integration stops after C emission. This local audit does not claim the current status of any remote Actions run.

## 9. Repository composition snapshot

Command:

```bash
pygount --format=summary \
  --folders-to-skip='.git,build,docs/api,__pycache__' .
```

Selected output:

```text
C:          152 files, 27737 code, 8590 comment
Python:       6 files,  1584 code,  351 comment
Markdown:   101 files,     0 code, 9436 comment
All:        292 files, 41608 code, 18632 comment
```

Pygount classifies Markdown as comments and these counts are descriptive, not an architectural completeness metric.

## 10. Evidence classification

| Check | Result | What it establishes |
|---|---|---|
| clean default build | pass with warnings | both libraries compile from `TU_OBJS` |
| quick smoke | pass | four named paths execute |
| config suite | 20/20 | named parser/conversion checks; does not prove dataflow runtime propagation |
| minimal C example | pass/mixed | geometry/capacities propagate; dataflow request does not; DMA→MMA→store output is exact |
| config docs | pass, identical | generator is reproducible here |
| Doxygen | blocked + source gate defect | prerequisites absent; recipe also suppresses downstream failure |
| compiler frontend | pass | two contained and one externally resolved ONNX model accepted; C emitted |
| generated compiler program | fail | no audited end-to-end runnable output |
| `test-full` exit status | false positive | target does not enforce its advertised pipeline |
| shell CI quick | fail before build | wrapper's artifact-directory ordering is broken |

## 11. Cleanup and final verification

The review exposed an additional build-hygiene hazard. After an earlier closure restored the tracked historical `tu_cmodel.o`, a later `make test-quick` saw that restored object's newer modification time and rearchived it beside freshly built objects. The revised static probe then aborted in `tu_init_from_config` with stack-canary corruption. Hashing the archive member confirmed that it matched the restored tracked object. A clean rebuild eliminated the ABI mismatch.

The authoritative final sequence was therefore:

```bash
make clean
make -j2
LD_LIBRARY_PATH="$PWD${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" make test-quick
make test-config
cc -O2 -Wall -Wextra -std=c11 \
  -I/home/zxy/Workplace/projects/tusim \
  -o /tmp/tusim-ch03-first-execution-reviewed \
  /home/zxy/Workplace/books/tusim-book/experiments/ch03_first_execution.c \
  /home/zxy/Workplace/projects/tusim/libtucmodel.a -lm
/tmp/tusim-ch03-first-execution-reviewed \
  /home/zxy/Workplace/books/tusim-book/experiments/ch03_minimal_config.json
git restore --source=HEAD -- tu_cmodel/tu_cmodel.o
git status --short
```

Observed:

```text
review clean build: exit 0
explicit-loader quick smoke: exit 0
config suite: exit 0, 20/20
reviewed C build: exit 0
reviewed C run: exit 0
requested dataflow = output_stationary; active dataflow = weight_stationary
O = [[58, 64], [139, 154]]
final git status --short: empty
```

The restore was the final source-tree operation. The tracked object is again the edition snapshot version, while ignored libraries retain the verified clean-build content. Any future Make invocation must begin with `make clean` to prevent the restored tracked object from being rearchived. No Tusim commit or push was performed.

Book evidence remains outside the Tusim source repository.