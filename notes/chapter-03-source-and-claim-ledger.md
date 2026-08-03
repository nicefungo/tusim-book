# Chapter 3 Source and Claim Ledger

## Edition boundary

- Tusim checkout: `/home/zxy/Workplace/projects/tusim`
- Commit: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Audit date: 2026-07-25
- Host: AArch64, GCC 11.4.0, GNU Make 4.3, Python 3.11.15
- Book evidence: [`../experiments/ch03-repository-and-first-execution-audit-2026-07-25.md`](../experiments/ch03-repository-and-first-execution-audit-2026-07-25.md)

## Claim ledger

| Claim | Evidence | Classification | Safe wording | Limit |
|---|---|---|---|---|
| The checkout is the edition snapshot | `git rev-parse HEAD` returned the full pinned hash | reproduced source state | The chapter describes snapshot `e918c80` | No formal release tag is implied |
| Normal build emits static and shared libraries | clean `make -j2`; `Makefile:13,50–54` | compiled | The default target built `libtucmodel.a` and `libtucmodel.so` from one 44-object list | Build success does not prove every source file is a member |
| The standalone cycle model is outside the normal library | `TU_OBJS`; `ar t libtucmodel.a` | source/link audit | `cycle_model.o` is absent from the archive | Its source and manually runnable focused tests still exist |
| Core, RS dataflow, and DPI objects are library members | `ar t libtucmodel.a` | linked | `tu_cmodel.o`, `row_stationary.o`, and `tu_dpi.o` are present | Membership alone does not prove runtime reachability or semantic coverage |
| The quick Make smoke suite passes | explicit local `LD_LIBRARY_PATH` + `make test-quick` | executable focused evidence | CModel 19/19, command queue 9/9, DMA 10/10, ASM pass | It covers four targets, not all tests; binaries need local shared-library discovery |
| JSON config path passes a focused suite | `make test-config` | executable focused evidence | 20/20 parser, validation, conversion, and configured-MMA checks passed | Compile warnings weaken CI strictness; the suite does not verify dataflow propagation |
| A minimal direct/configured C execution works | preserved C/JSON; explicit static link; observed output | executable + integrated for named path | geometry and 8 KiB capacities propagate; DMA → MMA → store produced `[[58,64],[139,154]]` | Requested output-stationary dataflow does not propagate; functional result does not validate timing/counters |
| The report is heterogeneous evidence | minimal run output and source | observed output + source interpretation | Values must be read by named counter and boundary | `Est. cycles`, DMA cycles, SRAM counters, FLOP/MAC labels are not one coherent calibrated timeline |
| `config-docs` is reproducible here | `make config-docs`; zero Git diff | generated-document check | The target regenerated the tracked file byte-for-byte | It writes into the source checkout and requires a clean-state check |
| Doxygen API docs are configured but not generated here | blocked run plus `Makefile:558–564` | environment + source gate audit | prerequisites are absent locally; recipe also suppresses downstream Doxygen failure and never verifies the HTML index | Do not call the missing tools a Doxyfile failure; do not call the target an enforced gate |
| Python compiler frontend accepts audited ONNX files | direct runs on two contained models and one resolved external symlink target | frontend execution only | ONNX load/check/analyze/code-emission completed | GPT-block requires a sibling workspace; this is not a working compiler pipeline |
| Audited compiler models do not produce runnable generated programs | compiler logs and explicit static builds | reproduced failure | all three reported 0 TU ops; generated C failed to link on undefined `host_gemm` | only two model files are repository-contained; failure is after frontend acceptance |
| `make test-full` is a false-positive success gate | target output and `Makefile:545–551` | build-system defect | The target returned zero despite generated-code link failure and missing executable because both steps use `|| true` | Its exit status cannot be cited as end-to-end success |
| The shell CI runner is not currently an enforceable gate | reproduced quick failure plus source inspection | executable + source build-system audit | clean deletes report directories before build; downstream compile-only, quick-golden, and compiler phases are false/incomplete gates | Remote Actions status was not audited |
| Shared-library staleness is a local workflow risk | test link commands, `readelf`, environment | source/toolchain analysis | Most test recipes use `-L. -ltucmodel`; selection depends on artifacts and loader path | Clean build or explicit archive linkage avoids ambiguity |
| Build changes a tracked object | pre/post `git status`; `.gitignore`; tracked `tu_cmodel/tu_cmodel.o`; review-time stale rearchive reproduction | repository-hygiene and build-correctness fact | the tracked object must be restored only after all experiments; any later build requires `make clean` | Make can rearchive the restored older-ABI object based on mtime even when Git status is clean |

## Source map

| Path | Role in Chapter 3 | Audit note |
|---|---|---|
| `Makefile` | build graph, library membership, test/document targets | authoritative for default local build; aggregate targets have different scopes |
| `README.md` | advertised quick start and top-level map | useful orientation; several directory labels are conceptual rather than literal paths |
| `tu_cmodel/tu_cmodel.h` | broad compatibility/public entry header | contains stale fixed-16×16 introductory prose and a duplicate function declaration |
| `tu_cmodel/tu_cmodel.c` | lifecycle, config bridge, DMA wrappers, MMA, aggregate stats | direct example reaches this path |
| `tu_cmodel/infra/config.*` | JSON parsing, validation, runtime conversion, docs emission | dataflow parses but is omitted from runtime conversion; geometry/capacities propagate |
| `tests/test_cmodel.c` | parameterized functional core checks | 19/19 in quick smoke run |
| `tests/test_command_queue.c` | command queue checks | 9/9 in quick smoke run |
| `tests/test_dma.c` | DMA descriptor checks | 10/10 in quick smoke run |
| `tests/test_config.c` | JSON and runtime-config path | 20/20; emits many return-type warnings |
| `tests/test_asm.c` | self-contained ASM smoke path | passes via `test-quick` |
| `compiler/onnx_to_tu.py` | demonstration ONNX frontend/code generator | fallback emits unresolved `host_<op>` calls; Gemm/MatMul fallback omission also leaves `host_gemm` undefined |
| `examples/*.onnx` | compiler inputs | two files are contained; GPT-block is an external symlink; all observed as 0 TU ops |
| `tools/ci_runner.sh` | CI wrapper | report directory deleted by its own clean phase; additional downstream false/incomplete gates |
| `.github/workflows/ci.yml` | hosted CI intent | invokes the failing shell wrapper; live GitHub run status was not audited here |
| `Doxyfile` and `docs-api` recipe | API-doc configuration/generation | excludes several core `.c` files; tools absent locally; recipe suppresses generator failure |
| `docs/CONFIG_REFERENCE.md` | generated config reference | exactly reproduced |
| `.gitignore` | artifact policy | ignores objects/libraries/tests, but one object is already tracked |

## Repository-tour corrections

The README diagram is an architectural summary, not a literal directory tree:

- precision sources are mostly at `tu_cmodel/` root, not `tu_cmodel/precision/`;
- dataflow sources are under `tu_cmodel/compute/dataflow/`, not a top-level `tu_cmodel/dataflow/`;
- DMA sources are mostly at the root, not `tu_cmodel/dma/`;
- event tracing lives under `tu_cmodel/perf/`, while logging/config/debug live under `infra/`;
- `cycle_model.c` is present under `perf/` but absent from `TU_OBJS`.

## Counter semantics from the minimal run

Observed workload: `W[2][3] × A[3][2]`, 4×4 configured PE array, 8 KiB each W/A/O SRAM, JSON-requested OS but active compile-time-default WS.

- host transfers: 12 B W + 12 B A + 16 B O = 40 B, matching `DMA bytes`;
- arithmetic: 2×2×3 = 12 MACs = 24 scalar FLOPs under the two-operations-per-MAC convention;
- the report prints `MMA FLOPS: 24 (FP16 MACs)`, mixing those terms;
- `PE Array: 4×4 (16 MACs)` describes configured lanes, not executed MAC operations or utilization;
- `MMA tiles: 1 (4×4×4 per tile)` reports configured tile geometry, not 64 useful MACs;
- aggregate `Est. cycles` is 19 while the DMA subsystem prints 153 cycles;
- all three SRAM regions print zero reads/writes despite completed data movement and compute.

Safe interpretation: the functional result and selected event counts are reproducible, but the report is not a calibrated, internally unified end-to-end performance account.

## Development questions—not Chapter 3 repair work

1. Should default `make` and tests force static linkage, add an rpath, or separate static/shared test targets?
2. Should `test-full` fail on generated-code compile or runtime failure?
3. Should compiler fallback emit compilable stubs for every fallback call, including Gemm/MatMul, or reject unsupported graphs before C emission?
4. Why does graph analysis classify supplied Gemm/MatMul examples as host fallback despite embedded weights?
5. Should the CI runner recreate report directories after `make clean`?
6. Should tracked object files be removed from version control in a separately reviewed source change?
7. Should `tu_print_stats` define MAC/FLOP terminology and counter domains explicitly?
8. Should Doxygen exclude core implementation files while enabling call graphs?

No Tusim source change is made by this chapter.