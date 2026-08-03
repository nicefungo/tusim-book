# Chapter 13 Weight-Stream Audit — 2026-08-03

- **Chapter:** Weight Streams: Quantization, Structured Sparsity, and Compression
- **Tusim pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Canonical runner:** `experiments/run_ch13_weight_stream_audit.sh`
- **Canonical retained run:** `experiments/runs/ch13-weight-streams/20260803-ch13-canonical-v8/`
- **Verdict vocabulary:** source predicates and executable observations match the pinned snapshot; this is not RTL or silicon validation

## Question

Given a weight tensor, a target traffic budget, and an accuracy constraint, what does pinned Tusim actually execute across the weight-path family — INT8/UINT4 quantization, 2:4 structured sparsity, and RLE/bitmap/adaptive compression — which configuration fields reach which consumer, and which reported cycle quantity is a byte-derived estimate, a decoder-throughput assumption, or no executable claim at all?

The audit deliberately does not ask whether Tusim is a calibrated weight-compression ASIC. No decoder FIFO, SRAM-conflict, ISA-auto-dispatch, physical area/power, or silicon calibration model was found in the selected implementation.

## Scope decision

Fresh whole-book reconnaissance compared weight streams, operator engines, performance counters, DRAM, contexts, and the cycle model. The weight-stream family was selected because it is the largest substantial uncovered surface with: three library-linked modules in `TU_OBJS`, parsed and validated `weight_compression` and `sparsity` configuration blocks with exact full-config consumers, a portable 16-byte frame format, focused tests, linked sweeps, and exploration reports that can be challenged rather than copied. It is not a Chapter 12 deferred topic.

The canonical seal is the run whose retained input hashes matched the book inputs at the sealing commit (`20260803-ch13-canonical-v8`, sealed at book commit `ff0bdc10`); the bundled copies under `inputs/` remain the binding evidence and verify against that commit today. Post-seal amendments to the audit report, framing plan, and claim ledger (sketched in the skeptical-review dispositions and applied after the seal) are recorded in git history; they do not alter the sealed evidence copies. All earlier attempts, complete or failed, are retained as immutable history, and any reseal supersedes the prior seal only through the same fail-closed gates. The runner may be re-executed with a new `CH13_RUN_ID`; earlier runs are immutable historical evidence. Toolchain recorded for the seal: aarch64 host, `cc` GCC 11.4.0, Make 4.3, Python 3.11.15, coreutils 8.32; `TUSIM_ROOT` is machine-specific and overridable via the environment.

## Provenance and containment

The canonical runner must:

1. require the Tusim checkout to be detached, tracked/untracked clean, and exactly at the edition pin;
2. require the book input commit to be clean, on branch `main`, with a configured `origin` pointing at `github.com-tusim:tusim-book.git` that is verified unchanged before and after (the run performs no push);
3. hash the ignored Tusim inventory before and after;
4. create a disposable source tree with `git archive`;
5. build only `libtucmodel.a` in that extraction;
6. compile every audited binary explicitly against the archive and reject dynamic `libtucmodel` dependencies;
7. bound every executable with `timeout`;
8. preserve source/input hashes, complete logs, transcript, copied book-side inputs, and a run-relative SHA-256 manifest;
9. verify that Tusim, the book inputs, the branch, the remote set, and the ignored inventory are unchanged after execution.

The pinned Makefile's `clean` recipe is never invoked because it removes process-global `/tmp` names outside the disposable extraction.

## Static source gate

`experiments/ch13_source_audit.py` accepts only the exact edition pin and enforces:

- 25 exact source/config/test/report hashes;
- archive membership for `tu_int_quant.o`, `sparsity/structured_2of4.o`, and `memory/weight_compress.o`;
- Makefile target and aggregate-membership predicates (`test-int-quant` and `test-sparsity` in `make test`; `test-compress` and the sweeps standalone; `test_int8_sweep.c` source-present with no target);
- quantization contract predicates (affine formula, INT8/UINT4 ranges, nibble packing, calibration, dot product, MMA tile);
- 2:4 predicates (mask set, pruning, packed size, estimator guards and equations);
- compression predicates (frame magic/version/header, RLE and bitmap wire formats, adaptive raw-tie rule, estimator equations, decoder-bound and overlap logic, validation);
- configuration predicates (field parse, validation rejections, the exact `tu_config_to_runtime()` drop of every compression/sparsity field, YAML omission of the `weight_compression` block, shipped JSON defaults);
- focused-test shape (14 int-quant calls, 27 sparsity tests, 24 compress tests, fail-closed exits);
- exact C-caller inventories for the estimator, config mapper, MMA tile, dot product, sparse MMA, and DMA encode entry points;
- a negative gate proving the direct MMA path (`tu_cmodel/tu_cmodel.c`) calls none of the weight-stream helpers.

## Executable evidence plan

The canonical runner builds the archive and then executes, with static-link gates:

1. `test-int-quant` — expects `14/14 tests passed`;
2. `test-sparsity` — expects `Tests: 27 run, 27 passed, 0 failed`;
3. `test-compress` — expects `24/24 tests passed`;
4. a forced mutation of the sparsity decoder-bottleneck assertion — expects `26/27` and a nonzero exit, proving the harness gate;
5. linked sweeps — weight-compression sweep header plus alternating row; sparsity sweep header plus small-projection row;
6. the custom probe with exact findings:
   - INT8 defaults `scale=0.007874016 zp=0 qmin=-128 qmax=127`; symmetric calibration `scale=1.0 zp=0`; conversions and clamps; nibble byte `0x5A` low-first; dot `32`; MMA tile `19/22/43/50`;
   - 2:4 masks `6` valid; prune `2` groups with masks `0x5,0x9`; FP16 packed `160` bytes for 128 elements;
   - 2:4 estimator on default config (16×16 PE, 256-bit DMA): square 128³ `dense_total=12291 sparse_total=7811` with `macs=2097152/1048576 wbytes=32768/20480 decode=4096`; narrow-N 512×16×512 decode-bound `34307/77312` at rate 1 and `19971` at rate 16;
   - compression: RLE all-zero `14` bytes; alternating expansion `776` vs raw `256`; bitmap 1/3-sparse `110` bytes; adaptive selects bitmap (`codec=2`, `size=126`); corrupt RLE rejected;
   - decoder cycles: default `dma=1 decode=128 total=128 bound=1`; wide decoder `decode=8 total=8`; serial `total=9`; config mapping `type=4 enabled=1 decoder=1`;
   - config parse `compression=1 type=4 decoder=1 sparsity=1 two4=1 decgroups=4`; validation `rejections=4`; runtime conversion retains PE geometry while compression/sparsity fields are absent by struct design;
   - `CH13_PROBE SUMMARY failures=0`.

## Fidelity labels carried into the manuscript

- Encoded sizes and round-trip equality are byte effects.
- Payload DMA cycles, decode cycles, and totals are deterministic analytical estimates under named config assumptions.
- Decoder-bound classification is an estimate-property, not a physical bottleneck proof.
- No weight-path quantity is calibrated against RTL, FPGA, or silicon.
- The codecs, the 2:4 module, and the quantizer are adjacent surfaces, not one integrated pipeline; dense reconstruction versus direct compressed-domain compute is BLOCKED in the implementation backlog.
