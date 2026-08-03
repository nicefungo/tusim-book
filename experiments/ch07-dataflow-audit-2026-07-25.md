# Chapter 7 Pluggable-Dataflow Audit — 2026-07-25

- **Tusim edition:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Book workspace:** `/home/zxy/Workplace/books/tusim-book`
- **Execution tree:** disposable verified `git archive` extraction at `/tmp/tusim-ch07-reproduction`
- **Calibration:** none; cycle values are deterministic source-defined estimates
- **Cycle boundary:** MMA plug-in only; legacy W/A/store cycles land in process-global `g_tu_dma` but contribute zero to `g_tu.estimated_cycles`, while O-load uses a separate direct term

## Audit questions

1. Are WS, OS, and RS compiled, registered, selectable, and numerically equivalent?
2. What logical dataflow behavior is actually executed, rather than described in comments?
3. Which timing callbacks drive `g_tu.estimated_cycles`, and what exact formulas result?
4. Does JSON configuration select the requested plug-in at runtime?
5. Do process-global and `tu_core_t` selection affect the same state?
6. Which statistics persist, reset, or remain inaccessible?
7. Do existing focused and sweep tests discriminate the active plug-in and pinned timing path?

## Enforced source inputs

`experiments/ch07_reproduce.sh` hashes the complete deterministic source archive before extracting it. The archive SHA-256 is `fb023fe79a0e7dafbf334848756e44127101f5fdb75c1004e2ed2712318b708f`. Inside that verified tree, `experiments/ch07_dataflow_audit.py` rejects a wrong provenance marker, revision argument, or drift in the 15 claim-critical files below. The archive hash pins every compiled source/header and other tracked input; the 15-file hashes make the chapter's direct claim inputs individually inspectable.

| Input | SHA-256 |
|---|---|
| `tu_cmodel/compute/dataflow/dataflow_interface.h` | `141bdd26c5e436d38095296e824a93761ac4b74edaed9b7482ef7c8eca5ebf77` |
| `tu_cmodel/compute/dataflow/dataflow_registry.c` | `56b4fcab5e736eb1fd55a02cdeaefd20504a708a7cea6012c8c819e25bc24d27` |
| `tu_cmodel/compute/dataflow/dataflow_dispatcher.c` | `f09af46670bc8a3bee49be6c639bc27a432a085109684e0f4f73b4f471b9a6f4` |
| `tu_cmodel/compute/dataflow/weight_stationary.c` | `c421bd0845da1847b4e48a97c55f45dbbb058dc3a5af0e448d5fab422bd5b7e8` |
| `tu_cmodel/compute/dataflow/output_stationary.c` | `fa3a00c9b649b69dc8e92d562f044c49b129096c753ba169a855ba2e075dfaa0` |
| `tu_cmodel/compute/dataflow/row_stationary.c` | `ea86233c36fa1f076e0852204880f8d903bf546728478816df66b091e56feeaf` |
| `tu_cmodel/tu_cmodel.c` | `542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059` |
| `tu_cmodel/tu_config.h` | `129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d` |
| `tu_cmodel/infra/config.c` | `17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a` |
| `tu_cmodel/tu_core.c` | `0e4b3c6e206465748ae2d3d2e9871f3a6542a61cd1ddcddfff6886b9ed1f0eeb` |
| `tu_cmodel/perf/performance_counters.c` | `f7d9a5ec33c873cb4c900902d3c8d168622be782a8979cc6a822211c471807f2` |
| `tu_cmodel/perf/performance_counters.h` | `5d323e9af226f2012c71eb4cc5fe917edc9a5cdd314782affeb9de3e21fdf6b5` |
| `tests/test_dataflow.c` | `c26b74c35e50e5231c193835f4d3ccc00146bc08548e3e52d6a50f50f6c9db43` |
| `tests/test_dataflow_sweep.c` | `4b3dc2da732f4efa25ec250bfb76e3507bd07168a73a703350150228077f57e6` |
| `Makefile` | `5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2` |

## Reproduction

From the book repository, run the fail-closed reproducer:

```bash
cd /home/zxy/Workplace/books/tusim-book
bash experiments/ch07_reproduce.sh
```

The script verifies the source checkout's exact revision and clean status, hashes the complete archive, extracts that same tar, records GCC/Make/glibc/Python/kernel identity, builds from clean state, runs every command, preserves combined stdout/stderr, checks that no audited binary resolves `libtucmodel.so`, hashes scripts/archive/library/binaries, and rechecks the source checkout. The complete transcript is [`ch07-reproduction-2026-07-25.log`](ch07-reproduction-2026-07-25.log). The chapter probe links `./libtucmodel.a` explicitly. The Make targets use `-L. -ltucmodel`, but clean-state removal plus `ldd` gates prove archive linkage in this run.

## Observed gates

- complete source archive SHA-256 and marker: pass;
- enforced claim-source/formula audit: `PASS (15/15)`;
- clean static-library build: pass with the two previously recorded unused-symbol warnings;
- `test-dataflow`: 9 passed, 0 failed;
- `test-config`: 20/20 passed, with pre-existing `return`-without-value warnings in the test macro;
- `test-multicore`: 16/16 passed;
- `test-dpi`: 13 passed, 0 failed;
- existing `test-dataflow-sweep`: completed with exit 0, but it is non-gating and its functional/analytical conclusions are not discriminating evidence for the pinned path;
- Chapter 7 probe: `SUMMARY: PASS failures=0`.
- dynamic dependency gates: all six audited binaries have no `libtucmodel.so` dependency;
- complete transcript final line: `REPRODUCTION: PASS`.

## Probe stdout

Initialization logs were emitted on stderr. The compact stdout was:

```text
selection registry_count=3 duplicate_addresses=stable json_requested=row_stationary active_after_init=weight_stationary unknown_name=weight_stationary nlr_fallback=weight_stationary dpi_summary=NLR dpi_active=weight_stationary
core_selection process_global=output_stationary core_snapshot=weight_stationary selection_scope=separate
case=nonsymmetric shape=2x3x2 pe=4x8 tiles=1 flops=24 cycles_ws=26 cycles_os=3 cycles_rs=15 equivalent=PASS oracle=PASS plugin_tile_flop_stats=cleared
case=edge-k-boundary shape=9x10x9 pe=4x8 tiles=12 flops=1620 cycles_ws=342 cycles_os=72 cycles_rs=210 equivalent=PASS oracle=PASS plugin_tile_flop_stats=cleared
case=multi-k shape=5x17x19 pe=4x8 tiles=18 flops=3230 cycles_ws=546 cycles_os=144 cycles_rs=348 equivalent=PASS oracle=PASS plugin_tile_flop_stats=cleared
subnormal canonical=0x1p-24 ws=0x1p-14 os=0x1p-14 rs=0x1p-14 ratio=1024 shared_defect=PASS
SUMMARY: PASS failures=0
```

Normal values are deterministic binary16 normals, including signs and nonsymmetric patterns. Equality is bitwise over FP32 outputs, and each plug-in also matches an independent in-probe oracle that uses the canonical converter with the same FP32 reduction grouping. The shared subnormal result is equivalence of a defect, not correctness.

## Four separate contracts

### 1. Geometry

All plug-ins receive the Chapter 6 dispatcher decomposition:

```text
tile_m = R
tile_n = C
tile_k = C
T_M = ceil(M/R), T_N = ceil(N/C), T_K = ceil(K/C)
```

Geometry is shared; selecting a dataflow does not change tile shape or iteration order in the dispatcher.

### 2. MMA semantics

All three implementations execute the same scalar nest and the same FP32 partial-sum grouping:

```text
for m in valid tile rows
  for n in valid tile columns
    psum = 0
    for k in valid reduction positions
      psum += fp16(W[m,k]) * fp16(A[k,n])
    O[m,n] += psum
```

The files use different local converter names but duplicate the same code. Therefore bitwise equality for the tested normal values is expected. It does not prove different physical schedules.

### 3. Logical dataflow

The source comments describe stationary operands and streams, but the executable functional loops do not implement PE-local storage, broadcasts, neighbor transfers, stream timing, SRAM arbitration, or distinct host-memory access traces. WS, OS, and RS all reread W and A from the same arrays inside the same `m,n,k` loop order.

RS alone updates opaque reuse fields using shape-derived arithmetic. It does not avoid the corresponding C loads, and it exposes no public accessor. The local `w_reads` variable is incremented but otherwise unused. OS claims simultaneous W/A streaming and bandwidth limitation, but no bus-width or SRAM-port model drives its return value.

The safe label is therefore **logical/intended mapping metadata plus distinct deterministic timing formulas**, not cycle-executed physical dataflow.

### 4. Timing

For each K tile, the dispatcher adds `fill + execute_tile return + drain`. It never calls the interface's `get_compute_cycles` callback. Pipeline depth is parsed into canonical configuration, dropped by runtime conversion, replaced by compile-time depth in the operation descriptor, and then ignored by WS/RS private state. Both use fallback depth two.

Let `k_q` be the valid K count of K tile `q`. For one spatial M/N tile:

```text
WS_q = 2C + k_q + 2R
OS_q = k_q + ceil(k_q/4)
RS_q = C + 1 + k_q + R
```

Summed over all spatial tiles:

```text
C_WS = T_M T_N [T_K(2C + 2R) + K]
C_OS = T_M T_N [K + sum_q ceil(k_q/4)]
C_RS = T_M T_N [T_K(C + 1 + R) + K]
```

Fill/drain use full configured `R,C` even on M/N edges and are charged once per K tile. OS's extra term is an implementation-local `ceil(k_count/4)` constant; despite comments, it is independent of M, N, bus width, SRAM ports, and measured traffic. RS's reduced fill/drain is likewise an uncalibrated source formula.

These equations explain the executable 4×8 results exactly. They do not establish physical bandwidth, reuse, overlap, frequency, area, power, or energy.

## Selection and ownership findings

1. WS, OS, and RS objects are compiled into `libtucmodel.a`, registered globally, and directly selectable with `tu_set_dataflow(0..2)`.
2. Duplicate registration keeps existing object addresses and frees any new object with the same ID without checking semantic equivalence. The probe confirms stable addresses across reinitialization; this protects snapshots from pointer churn but silently forbids replacement.
3. The interface declares NLR ID 3 and comments call it supported, but no NLR object is compiled or registered. Selecting 3 logs a warning, falls back to WS, and still returns success.
4. Unknown JSON dataflow strings silently become WS. Recognized WS/OS/RS/NLR reaches canonical `cfg.dataflow_mode`, but `tu_config_to_runtime()` omits the field and `tu_init_with_config()` selects compile-time `TU_DATAFLOW_MODE`. The canonical `dataflow_via_plugin` field also does not control execution; `TU_DATAFLOW_DISPATCH_VIA_PLUGIN` is compile-time and pinned to one. The probe reproduces misspelling-to-WS and parsed-RS-to-active-WS as separate failures.
5. `tu_set_dataflow()` modifies process-global `g_tu.dataflow`. `tu_core_mma()` swaps `core->state` into `g_tu`, so a process-global selection made outside the core does not change the core snapshot. The probe observed requested global OS while the core remained WS.
6. The registry assumes ownership despite constructor comments saying the caller owns returned objects. Its global destroy API is not integrated into ordinary teardown, so objects normally persist for process lifetime. Individual or global destruction while snapshots survive would leave dangling pointers.
7. The registry and generic plug-in counters are global and not thread-safe. Core snapshots share plug-in addresses, so plug-in-local mutable state is not core-local.
8. DPI accepts requested NLR, reports success, and retains `DF=NLR` in its summary while its active-name API and execution use fallback WS. The probe reproduces the requested-versus-active split.

## Counter findings

- `plugin->total_cycles` is cumulative and is not reset by `tu_mma()` or plug-in `init()`.
- `plugin->total_tiles` and `plugin->total_flops` are accumulated by the dispatcher, copied into `g_tu`, and then reset to zero by `tu_mma()`. Despite interface comments calling them totals, they behave as per-call scratch on the public path.
- RS `init()` resets reuse hits/misses on every high-level dispatch because the dispatcher calls `init()` for every MMA. Multi-call cumulative RS reuse is therefore unavailable even internally.
- No public per-dataflow traffic, reuse, fill, drain, or stall counters are exposed by this path.
- `tu_perf_counters_t` contains only WS/OS fields and is not wired into `g_tu`; its recorder maps every nonzero ID to OS, its sole cycle-model producer hard-codes ID 0, and diff/merge omit both fields.

## Existing-test challenge

### Focused `test-dataflow`

The nine-test suite passes and does directly select each global plug-in for identity and pairwise equivalence cases. However:

- identity and current pseudo-random construction do not assert cycle deltas;
- the edge test compares WS and OS, not RS;
- no test covers raw subnormals, config propagation, NLR fallback, plug-in statistics, or core-local selection;
- equality alone cannot prove physical data movement because all three scalar nests are the same.

### Existing `test-dataflow-sweep`

The program completes with exit zero, but this is not a test pass: comparison failures affect printed text only and `main()` returns zero unconditionally. Three further defects prevent its headline comparison from validating the pinned path.

1. `run_mma_and_capture()` calls process-global `tu_set_dataflow(df_id)`, then invokes `tu_core_mma(core,...)`. Core swap-in replaces that global pointer with the core's default WS pointer. Thus its three functional runs all execute WS while being labeled WS/OS/RS.
2. Its separate analytical formulas charge fill/drain once per spatial tile and use the full K in one compute term. The pinned dispatcher invokes plug-ins for every K tile. For `128×128×256` on 16×16, the sweep prints approximately 20,480/16,384/18,496 cycles for WS/OS/RS, while the pinned executable formulas give 81,920/20,480/50,176 MMA cycles.
3. It never samples the active plug-in or executable cycle delta, and it cannot return failure for those mismatches.

The sweep also adds an analytical DMA term to analytical MMA values. Executable W/A-load and O-store cycles accumulate in process-global `g_tu_dma`, while wrappers read unrelated `g_tu.dma` and therefore add zero to `g_tu.estimated_cycles`; O-load adds a third direct byte/bus term. Its output remains **historical analytical evidence**, not a current executable comparison.

## Multi-objective interpretation

| Dataflow regime | Potential physical benefit | Costs or risks omitted by Tusim |
|---|---|---|
| WS | weight reuse can reduce repeated weight movement | weight preload/storage, activation and partial-sum network, edge mapping, refill policy |
| OS | local FP32 accumulation can reduce partial-sum traffic | simultaneous W/A delivery bandwidth, accumulator area, reduction length, spill behavior |
| RS | convolution mappings can combine filter, activation, and partial-sum reuse | convolution-to-GEMM correspondence, PE-local capacity, multicast, mapping search, irregular layers |

The pinned cycle ranking always structurally favors OS over RS over WS for positive geometry because of hard-coded overhead terms. That is a property of the formulas, not a discovered workload-dependent architecture result. A realistic comparison needs explicit traffic events, storage levels, bandwidth/ports, overlap, topology, mapping, area/energy assumptions, and calibration.

## Fidelity classification

| Claim | Classification | Boundary |
|---|---|---|
| WS/OS/RS normal-value output equivalence | executable functional model | tested shapes and normal binary16 values; same scalar reduction grouping |
| shared subnormal output | executable defect | all three return `2^-14` for raw `0x0001 × 1`; canonical value is `2^-24` |
| direct selection 0/1/2 | integrated and executable | process-global path after explicit `tu_set_dataflow()` |
| config-selected dataflow | parsed but not integrated | field is dropped before runtime and init uses compile-time default |
| stationary operand movement | intended/logical description | no PE-local storage or transfer trace executes |
| WS/OS/RS equations above | executable deterministic estimate | uncalibrated, full nominal edge overhead, per-K invocation |
| existing sweep ranking | historical analytical | formulas and core selection differ from pinned execution |
| end-to-end DMA+MMA latency | rejected | legacy W/A/store cycles are omitted from `g_tu.estimated_cycles`, O-load uses a separate term, and no coherent overlap/sum exists |

## Development questions exposed

1. Should dataflow be a field of `tu_runtime_config_t` and each `tu_core_t`, with an API that selects on a named core?
2. Should unsupported IDs fail rather than silently fall back while returning success?
3. Should one canonical FP16 converter serve every plug-in, with subnormal vectors in aggregate tests?
4. Should the interface distinguish functional kernel, logical mapping descriptor, traffic model, and timing model?
5. Should fill/compute/drain receive valid edge dimensions and explicit persistent pipeline state?
6. Should timing consume pipeline depth from the operation descriptor, and should `get_compute_cycles` be removed or used?
7. Which memory levels, event counts, multicast/broadcast behavior, and overlap are required before reuse claims affect performance or energy?
8. Should plug-in statistics be per-core snapshots with explicit reset/snapshot APIs?
9. Should the existing sweep be replaced with a direct-global discriminating harness and pinned formula checks?
10. What compiler mapping contract selects WS/OS/RS based on shape, layout, residency, and traffic rather than enum name?

## Review dispositions

Three independent read-only reviews were checked against the pinned source and the rerun evidence. Their findings were resolved as follows.

1. **Accepted — DMA scope:** expanded the finding from generic non-coherence to the exact `g_tu_dma`/`g_tu.dma` omission and separate O-load path.
2. **Accepted — pipeline propagation:** documented canonical parse loss, compile-time descriptor substitution, and WS/RS private-state non-consumption as distinct breaks.
3. **Accepted — unknown names:** added silent misspelling-to-WS behavior and an executable probe assertion.
4. **Accepted — DPI NLR metadata:** added requested `DF=NLR` versus active `weight_stationary` evidence and a probe assertion.
5. **Accepted — parallel performance counters:** added producer hard-coding plus missing RS storage and diff/merge fields.
6. **Accepted — duplicate semantics:** replaced “equivalent new object” with any same-ID object and stated that replacement is forbidden without equivalence checking.
7. **Accepted — registry lifecycle:** clarified process-lifetime persistence and otherwise-unintegrated global destruction.
8. **Accepted — complete provenance:** added the complete deterministic archive SHA-256 and required extraction marker; retained 15 individual claim-source hashes.
9. **Accepted — fail-closed probe:** prerequisite and assertion failures now terminate before any success label; configuration objects are initialized.
10. **Accepted — sweep status:** changed “successful target” language to non-gating completion with unconditional zero exit.
11. **Accepted — linkage:** the reproduction script rejects any audited binary resolving `libtucmodel.so`.
12. **Accepted — durable evidence:** preserved full combined build/test output, toolchain identity, linkage output, return behavior, and artifact hashes in a committed transcript.
13. **Qualified — numerical breadth:** a canonical normal-value oracle had already been added while review ran; the probe remains deliberately scoped to selected normals plus one defect vector. Broad special-value semantics are deferred to Chapter 8 and no broader claim is made.
14. **Accepted — probe failure paths:** converted accumulated failures to immediate fatal exits and initialized parsed configuration storage.
15. **Accepted — trade-off dimensions:** separated latency/throughput, named-boundary traffic, area/energy, numerical behavior, and fidelity/evidence cost.
16. **Accepted — RS scope:** replaced vague “balanced movement” latency language with a conditional named-event mechanism.
17. **Accepted — review questions:** converted implementation-recall questions into diagnosis and counterfactual reasoning.
18. **Accepted — objective scope:** changed “normal FP16 values” to audited normal binary16 vectors.
19. **Accepted — tile terminology and ladder:** renamed counts as plug-in invocations and corrected direct-path integration wording.
20. **Qualified — opening order:** retained the motivating quantitative hook because the immediately preceding list already defines reuse interval, movement boundary, resources, schedule, and objective; no correctness or scope issue remained.

No reviewer modified either repository. All accepted changes were made in the book workspace and then re-executed through the full reproducer.

## Safe conclusion

At the pinned revision, Tusim has a real compiled registry and three directly executable functional plug-ins. They agree bitwise on the audited normal cases and share the same MMA-local subnormal defect. Their physical dataflow distinctions are not executed as movement schedules; their observable differences are names, RS-private shape arithmetic, and hard-coded deterministic timing terms. Direct runtime selection works, but unknown-name parsing, JSON-to-runtime propagation, process-global-to-core selection, and DPI requested-versus-active reporting are defective. Legacy W/A/store DMA cycles are omitted from `g_tu.estimated_cycles`, O-load follows a separate path, and no end-to-end DMA-plus-MMA latency comparison is defensible.