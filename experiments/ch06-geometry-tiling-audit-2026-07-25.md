# Chapter 6 Geometry and Tiling Audit — 2026-07-25

- **Tusim edition:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Book workspace:** `/home/zxy/Workplace/books/tusim-book`
- **Execution tree:** disposable `git archive` extraction at `/tmp/tusim-ch06-audit`
- **Calibration:** none; cycle values are deterministic C-model estimates, not RTL or silicon measurements

## Questions

1. What matrix orientation and accumulation contract does `tu_mma()` execute?
2. How are `M`, `N`, and `K` split by runtime PE rows and columns?
3. Do edge tiles preserve numerical correctness and update counters as source predicts?
4. How do array shape and size change a clearly defined slot-utilization proxy?
5. Which whole-operand capacities constrain a call despite internal compute tiling?
6. Which historical exploration formulas agree with the pinned executable path, and which do not?

## Source inputs and enforced hashes

`experiments/ch06_tiling_audit.py` rejects revision-argument or hash drift. It checks:

| Input | SHA-256 |
|---|---|
| `tu_cmodel/tu_cmodel.c` | `542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059` |
| `tu_cmodel/compute/dataflow/dataflow_dispatcher.c` | `f09af46670bc8a3bee49be6c639bc27a432a085109684e0f4f73b4f471b9a6f4` |
| `tu_cmodel/compute/dataflow/weight_stationary.c` | `c421bd0845da1847b4e48a97c55f45dbbb058dc3a5af0e448d5fab422bd5b7e8` |
| `tu_cmodel/tu_cmodel.h` | `416a0d20776825498217ff5d4382f07ccb2ac9689bbe6c70cacd1bf13e7725af` |
| `tu_cmodel/tu_config.h` | `129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d` |
| `tests/test_cmodel.c` | `a7609fe22a113c0d9f2807ab3b76c7be29bbc2ed3822a3cfea82c2109862b36c` |
| `tests/test_dataflow.c` | `c26b74c35e50e5231c193835f4d3ccc00146bc08548e3e52d6a50f50f6c9db43` |
| `scripts/sweep_aspect_ratio.py` | `7e4f8207c3ec3854f3efb3a3caa02bbd48856d9ea5608198f596c11d79948db2` |

## Reproduction

From the pinned Tusim checkout:

```bash
rm -rf /tmp/tusim-ch06-audit
mkdir -p /tmp/tusim-ch06-audit
git archive e918c80b6fce833cd1fcae97730fa841c2176f25 | tar -x -C /tmp/tusim-ch06-audit
```

```bash
python3 /home/zxy/Workplace/books/tusim-book/experiments/ch06_tiling_audit.py \
  /tmp/tusim-ch06-audit \
  e918c80b6fce833cd1fcae97730fa841c2176f25
cd /tmp/tusim-ch06-audit
make clean
make -j2 libtucmodel.a
make test-cmodel
make test-dataflow
make test-golden
cc -O2 -Wall -Wextra -std=c11 -fPIC -I. -Itu_cmodel \
  -o test-random-quick tests/test_random.c -L. -ltucmodel -lm
./test-random-quick --quick
cp /home/zxy/Workplace/books/tusim-book/experiments/ch06_geometry_probe.c .
cc -std=c11 -O2 -Wall -Wextra -I. -Itu_cmodel \
  -o ch06_geometry_probe ch06_geometry_probe.c -L. -ltucmodel -lm
./ch06_geometry_probe
```

The original Tusim checkout was not built or modified.

## Observed output

The enforced Python audit printed:

```text
pin: e918c80b6fce833cd1fcae97730fa841c2176f25
source_hashes: PASS (8/8)
case M N K rows cols tiles ws_cycles slot_util
case 9 9 9 4 8 12 342 0.237305
case 9 9 9 16 16 1 73 0.177979
case 4 32 16 8 8 8 320 0.500000
case 4 32 16 4 16 2 112 1.000000
case 9 9 8 8 8 4 160 0.316406
case 9 9 8 16 16 1 72 0.158203
case 16 16 16 16 16 1 80 1.000000
case 16 16 16 32 32 1 144 0.125000
case 16 16 16 64 64 1 272 0.015625
case 31 17 23 16 16 8 604 0.369904
capacity M N K W_bytes A_bytes O_fp32_bytes bias_fp16_payload_bytes
capacity 2 3 2 8 12 24 12
capacity 31 17 23 1426 782 2108 1054
capacity 128 128 128 32768 32768 65536 32768
capacity 256 256 256 131072 131072 262144 131072
enforced_invariants: PASS
```

The probe's stdout was:

```text
semantics: orientation=O[M,N]+=W[M,K]*A[K,N] accumulation=PASS bias_fp16_expand=PASS
subnormal: canonical=0x1p-24 mma=0x1p-14 ratio=1024 defect_reproduced=PASS
geometry: mma=9x9x9 pe=4x8 tiles=12 cycles=342 util=0.237305
geometry: mma=9x9x9 pe=16x16 tiles=1 cycles=73 util=0.177979
aspect: mma=4x32x16 pe=8x8 tiles=8 cycles=320 util=0.500000
aspect: mma=4x32x16 pe=4x16 tiles=2 cycles=112 util=1.000000
larger-array: mma=9x9x8 pe=8x8 util=0.316406 pe=16x16 util=0.158203
underfilled-larger: mma=16x16x16 pe=16x16 cycles=80 util=1.000000 pe=32x32 cycles=144 util=0.125000 pe=64x64 cycles=272 util=0.015625
SUMMARY: PASS
```

Initialization INFO logs were emitted on stderr for each reinitialization; they are not included in the stdout block above. The clean library build passed with two pre-existing warnings: unused `comp_names` in `infra/logging.c` and unused `parse_opt_uint` in `infra/config.c`.

Focused results:

```text
test-cmodel:   19/19 tests passed
test-dataflow: 9 passed, 0 failed
test-golden:   11/11 tests passed, including edge, non-square, prime, scalar, vector, bias, and 50 bulk-random cases
test-random --quick: 500/500 FP16 MMA and 200/200 BF16 MMA iterations; 9/9 categories passed
chapter probe: SUMMARY: PASS
```

The random-suite line is an abridged summary of a 1,645-line combined stdout/stderr log, dominated by repeated initialization INFO messages. It also included a passing `31×17×23` prime-dimension case, 100/100 elementwise cases, and 50/50 softmax cases. The full non-quick `make test-random` target was not run.

`test-cmodel` also emitted seven missing-`label`-initializer warnings. No warning changed the exit status.

## Derivations reproduced

For runtime geometry `R × C`, the pinned MMA dispatcher uses:

```text
T_M = ceil(M/R)
T_N = ceil(N/C)
T_K = ceil(K/C)
tiles = T_M T_N T_K
useful MACs = M N K
reported FLOPs = 2 M N K
```

For the active weight-stationary plug-in, its implementation-local pipeline depth remains zero-initialized and its helpers fall back to `p=2`. Fill and drain are charged inside the K-tile loop using full configured tile dimensions, while compute uses actual `k_count`. Therefore the reproduced MMA-only estimate is:

```text
cycles_WS = T_M T_N [T_K (2C + 2R) + K]
```

This is an exact reconstruction of the pinned path for these probes, not a physical systolic-array timing law.

The chapter's analytical slot-utilization proxy is:

```text
U_slot = M N K / (T_M T_N T_K R C²)
```

It factors into output-edge occupancy `MN/[(T_M R)(T_N C)]` and K-slot occupancy `K/(T_K C)`. These are analytical mapping metrics, not runtime active-cycle counters.

It treats one configured tile as `R × C` PEs over `C` reduction slots. Tusim does not expose this metric; the functional loops execute only valid edge elements.

## Capacity findings

The current call requires whole logical operands to be addressable in their SRAM regions:

```text
w_offset + 2 M K <= W capacity
 a_offset + 2 K N <= A capacity
 o_offset + 4 M N <= O capacity
```

Bias has a packed FP16 payload of `2MN` bytes at `o_offset`, but `tu_mma()` expands it in place to an FP32 `4MN` accumulator image in reverse element order. Therefore bias payload fit is insufficient; the final FP32 extent must fit.

At default capacities (W 128 KiB, A 64 KiB, O 64 KiB), a `128×128×128` call needs 32 KiB W, 32 KiB A, and exactly 64 KiB O. A `256³` call needs 128 KiB W, 128 KiB A, and 256 KiB O: W fits exactly, A and O do not. Internal PE tiling does not stream or spill those larger operands.

## Source and documentation challenges

1. `tu_cmodel.h` says tiling processes 16×16 tiles and constrains dimensions to multiples of 16 or a “final tile”; runtime source actually accepts arbitrary dimensions and runtime geometry.
2. `tu_print_stats()` labels `total_mma_flops` both “FLOPS” and “FP16 MACs”; source increments two per useful MAC. It is an operation count under the book's convention, not a MAC count.
3. The header overview says output is FP16 and rounded on store, but direct `tu_dma_store_o()` copies the FP32 O-region bytes. Conversion is a separate helper; direct capacity and traffic use four bytes per output element.
4. Runtime `pe_rows`/`pe_cols` affect tiling. Runtime `pe_pipeline_depth` is not part of `tu_runtime_config_t`; full-config parsing retains it elsewhere but the global MMA path passes compile-time `TU_PE_PIPELINE_DEPTH`, and WS helper state never consumes even that argument. The observed value is the helper fallback `2`.
5. The dispatcher charges fill and drain per K tile, not once per spatial output tile. Historical reports disagree about which formula is intended and must remain **historical/analytical**, not executable evidence for the pinned path.
6. `scripts/sweep_aspect_ratio.py` is standalone analytics, not a C-model runner. It omits K-tile multiplicity from its tile count, uses global fill/drain formulas unlike the dispatcher, and uses two bytes for the O traffic term even though direct MMA accumulators and `tu_dma_store_o` are FP32. Its tables were not accepted as current executable evidence.
7. Bounds helpers report and return locally, but callers continue. This audit tests exact-fit and feasible cases only; it does not execute known unsafe overflow paths.
8. Geometry values passed directly through `tu_init_with_config()` are not validated here. Zero rows or columns would make tile division undefined.
9. Several products and offset sums use 32-bit arithmetic, so maximal `uint16_t` dimensions are not a safe implied operating range.
10. `docs/TU_CMODEL.md` reverses M/N relative to the executable header and indices and describes unenforced W-buffer workspace policy.
11. Byte offsets are not checked for FP16/FP32 alignment before typed pointer casts.
12. WS/OS/RS duplicate a local FP16 converter that decodes subnormals incorrectly. The probe reproduced `0x0001` as `2^-14` in MMA instead of canonical `2^-24`.
13. W/A/store DMA estimates accumulate in global `g_tu_dma`, while wrappers inspect `g_tu.dma`; `tu_dma_load_o()` uses a third direct formula. `g_tu.estimated_cycles` is not a coherent end-to-end DMA-plus-MMA domain.
14. `test_golden` uses an in-process FP32 oracle and does not parse the committed JSON fixtures suggested by its comments.
15. Aggregate `make test` includes cmodel, golden, dataflow, performance, and config tests but excludes sweeps and `test-random`; `test-quick` is narrower, and geometry sweeps are not CI gates.

## Independent review and disposition

Three read-only reviews examined pinned source/test surfaces and primary-source claim boundaries. Their findings were checked against live source or the revised executable probe before acceptance.

1. **Accepted — orientation drift:** live indices and the nonsymmetric probe establish `[M][N]`; stale `docs/TU_CMODEL.md` uses `[N][M]`. Added to prose and source audit.
2. **Accepted — compute tiling versus capacity tiling:** whole dense operands remain resident and contiguous; internal tiles do not stream, pack, or spill. Kept explicit throughout.
3. **Accepted — K coupling and nominal edge timing:** PE columns set both N and K tile extents; fill/drain callbacks receive configured R/C rather than valid edge counts.
4. **Accepted — effective pipeline depth and per-K fill/drain:** executable formula and historical-formula disagreement were already reproduced; wording was tightened.
5. **Accepted — underfilled larger-array regime:** added executable `16³` cases at 16², 32², and 64², reproducing 80/144/272 MMA cycles and 100%/12.5%/1.5625% slot utilization.
6. **Accepted — test-surface qualification:** documented aggregate/CI omissions and clarified that `test_golden` does not consume committed JSON fixtures.
7. **Accepted — bounds, size-wrap, and requested-event counters:** retained warning-only failure caveat and added alignment/counter wording; unsafe overflow probes remain deliberately unexecuted.
8. **Accepted and executable — FP16 subnormal defect:** revised probe reproduced canonical `2^-24` versus MMA `2^-14` for raw `0x0001`.
9. **Accepted — DMA cycle-object split:** source proves wrapper/engine state divergence; all chapter tables remain explicitly MMA-only.
10. **Accepted — bias semantics:** full M-by-N packed FP16 image, reverse in-place expansion, and FP32 extent are now distinguished from vector broadcast.
11. **Accepted — terminology boundaries:** geometry, MMA semantics, dataflow, edge occupancy, and timing remain separate; output-edge and K-slot factors were added.
12. **Accepted — bibliography scope:** existing verified Kung, Jouppi, Eyeriss, SCALE-Sim, Timeloop, MAESTRO, Gemmini, and Roofline entries already supply the needed conservative backbone. Unverified Kung–Leiserson metadata and optional preprints were not added.

## Evidence classification

| Claim | Classification | Boundary |
|---|---|---|
| row-major `O += W × A` numerical result | executable functional model | FP16 inputs converted to FP32; not a PE waveform |
| runtime geometry changes tile count | integrated and executable | direct/global path at pinned commit |
| WS cycle equation above | executable deterministic estimate | sequential tile sum; no overlap, physical routing, frequency, or calibration |
| slot utilization | analytical | derived from configured slots; not a Tusim counter |
| full-operand capacity inequalities | source-proven and executable for fitting cases | overflow rejection is not safe/failure-atomic |
| historical sweep throughput/optimality | historical/estimated | formulas and capacity assumptions differ from current path |

## Safe interpretation

The audit proves functional orientation, accumulation, bias conversion, edge correctness, runtime geometry consumption, and exact counter/cycle behavior for selected cases. It does not prove that the cycle estimate matches RTL, that unused slots toggle or consume full dynamic energy, that a wider or larger array meets frequency, or that one geometry is physically optimal. Those conclusions need explicit mapping, memory traffic, overlap, area/power, timing, and calibration models.
