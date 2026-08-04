# Chapter 14 Operator Compute Engines Audit — 2026-08-04

- **Chapter:** Operator Compute Engines: Functional Semantics and Engine Metrics
- **Tusim pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Canonical runner:** `experiments/run_ch14_compute_engines_audit.sh`
- **Canonical retained run:** named at closure (seal wording below); retained runs live under `experiments/runs/ch14-compute-engines/`
- **Verdict vocabulary:** source predicates and executable observations match the pinned snapshot; this is not RTL or silicon validation

## Question

For each operator engine in the pinned tree — convolution, softmax, attention, normalization, pooling, elementwise, and the pipeline controller — what does Tusim actually execute, what does each engine's return value mean (stall cycles vs analytical cycle count vs stats struct vs status code), and how is each engine reachable from non-test code? The audit deliberately does not ask whether the engines form one integrated operator dispatch path, whether any engine metric is calibrated, or whether cross-engine cycle sums are meaningful; none of those claims is supported at the pin.

## Scope decision

Fresh whole-book reconnaissance compared operator compute engines, the DRAM model, power/energy, context switching, perf counters/trace, and double buffering. The operator compute engine family was selected because it is the largest uncovered functional surface at the pin: 7 modules (~3,060 lines), 7 focused suites (~3,070 lines), 10 sweeps, and 7 design docs — with a chapter-defining integration finding (only elementwise is queue-reachable; conv/attention/pooling/pipeline have no non-test library caller) and a metric census that grounds the fidelity matrix's "never sum heterogeneous return values" rule in real per-engine accounting paths. It is not a Chapter 13 deferred topic.

The canonical seal is the run whose retained input hashes matched the book inputs at the sealing commit; the bundled copies under `inputs/` remain the binding evidence and verify against that commit. Post-seal amendments to the audit report, framing plan, and claim ledger (sketched in the skeptical-review dispositions and applied after the seal) are recorded in git history; they do not alter the sealed evidence copies. All earlier attempts, complete or failed, are retained as immutable history, and any reseal supersedes the prior seal only through the same fail-closed gates. The runner may be re-executed with a new `CH14_RUN_ID`; earlier runs are immutable historical evidence. Toolchain recorded for the seal: aarch64 host, `cc` GCC 11.4.0, Make 4.3, Python 3.11.15, coreutils 8.32; `TUSIM_ROOT` is machine-specific and overridable via the environment.

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

`experiments/ch14_source_audit.py` accepts only the exact edition pin and enforces:

- 28 exact source/test/config hashes (7 engine modules + 7 headers + 7 test files + Makefile, `tu_config.h`, `tu_sram.c/h`, `tu_cmodel.c`, `command_queue.c`, `tu_dpi.c`);
- archive membership for all seven engine members (bare names);
- entry-point predicates per module (`tu_conv_compute_dims`/`tu_conv2d_im2col_gemm`/`tu_conv_estimate_cycles`; `tu_softmax_execute` and both row passes; `tu_attention_execute`/`tu_attention_auto_tile`/`fp32_to_fp16_in_sram`/`transpose_fp16_in_sram`; `tu_norm_execute`/`normalize_row`; `tu_pool_execute`/`tu_pool_max_2d`; `tu_ew_execute`/`ew_gelu_tanh_approx`; `tu_pipeline_submit_tile`/`tu_pipeline_advance`/`tu_pipeline_get_stats`);
- stats-struct predicates (7 attention fields + pipeline `cycles_saved`/`total_stalls`);
- SRAM access-width defect markers (FP16 reads/writes through the 4-byte `tu_sram_read/write` API);
- stall-accounting asymmetry markers (norm discards the read return; softmax counts both; elementwise bypasses and labels all events as writes);
- reachability predicates (command queue → elementwise; DPI → softmax + elementwise; `normalization_engine.h` include-only in DPI; the negative case is its own predicate);
- `make test` membership predicates (six engine suites aggregated; `test-softmax` standalone-only — a false-positive aggregate membership fails the gate);
- mutation control proves the hash gate is live (nonzero rc + `hash mismatch` line on append).

## Executable evidence plan

The canonical runner builds the archive and then executes, with static-link gates:

1. `test-elementwise` — expects `16/16 tests passed`;
2. `test-normalization` — expects `11/11 tests passed`;
3. `test-convolution` — expects `12/12 tests passed`;
4. `test-pooling` — expects `14/14 tests passed`;
5. `test-pipeline` — expects `Results: 11/11 passed`;
6. `test-attention` — **qualified, never green**: expects rc=1 with `6/9`–`8/9 tests passed` (observed range across builds; the gate accepts any `1/9`–`8/9` count), at least one `FAIL` line, and never `9/9`. The SRAM access-width defect corrupts FP16 staging with UB-dependent magnitudes (stack garbage varies per build), so the exact failing subset varies (observed `test_scale` at 8/9; `test_deterministic_small` + `test_causal` at 7/9; all three at 6/9). The runner labels `ATTENTIONSUITEQUALIFIED PASS` with the observed summary and the `failing_subset_ub_dependent=yes` flag;
7. `test-softmax` — standalone Makefile target only (excluded from `make test`); expects `=== Results: 15/15 passed, 0 failed ===`;
8. a forced mutation of one softmax expected-value comparison (`0.25f → 0.5f` in the zero-input test) — expects `=== Results: 14/15 passed, 1 failed ===` and a nonzero exit, proving the harness gate;
9. the custom probe with exact findings:
   - convolution: `dims oh=3 ow=3 im2col_rows=3 im2col_cols=9`; direct vs im2col+GEMM agree at `6.000000`; `estimate_cycles=69`;
   - softmax: zeros row → uniform `0.25`, `max=0.0`, stalls `8`; 40-element census `96`; invalid desc → `UINT64_MAX`;
   - normalization: LayerNorm `[1,1,1,1]` → `[0,0,0,0]`, `mean=1.0 var=0.0`, stalls `8`; RMSNorm → `0.999995` each, `var=1.0`, stalls `8`; census `80` (load stalls discarded);
   - elementwise: `[ADD 2, RELU]` on `[-3,1,5]` → `[0,3,7]`, stalls `2`; census `40`;
   - pooling: 4×4 max 2×2/2 → `[6,8;14,16]`, cycles `18`; avg → `[3.5,5.5;11.5,13.5]`, cycles `34`;
   - attention: tiny M=1,N=1,d=2 → `dma=16 B, tiles=2, flops=8, compute=145, dma_cycles=2, total=147, util=0.9864`; isolated in-place FP32→FP16 conversion `[1..6]` → all zeros; differential vs golden: `deviates=1 scales_equal=1` (magnitude UB-dependent, flags robust);
   - pipeline: depth-1 `sequential_total=204 saved=0 stalls=0`; depth-2 with 3200-B loads `sequential_total=402 saved=200 stalls=0` (overlap credit byte-proportional to load descriptors);
   - `CH14_PROBE SUMMARY failures=0`.

## Fidelity labels carried into the manuscript

- Functional operator semantics (softmax/norm/ew/pool/conv values) are executable byte effects at the pin.
- Stall returns, pooling cycle counts, conv `estimate_cycles`, and attention stats are deterministic analytical estimates from pinned equations — never measured latency, never summed across engines.
- Attention FP16 correctness is rejected as a claim at this pin (SRAM access-width defect, C14.9/C14.10).
- No engine metric is calibrated against RTL, FPGA, or silicon.
- The engines are adjacent surfaces with a partial integration map (queue → elementwise; DPI → softmax/elementwise; attention internal composition; conv/pooling/pipeline standalone), not one configured operator dispatch path.
