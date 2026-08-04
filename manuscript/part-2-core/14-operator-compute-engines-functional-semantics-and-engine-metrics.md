# Chapter 14 — Operator Compute Engines: Functional Semantics and Engine Metrics

Tusim edition commit: `e918c80b6fce833cd1fcae97730fa841c2176f25`

## Learning objectives

After this chapter, you should be able to:

1. distinguish an engine's functional byte effects (exact operator outputs) from its returned metric, and name the metric's cycle domain before using it;
2. read each of the four return-value dialects — SRAM stall cycles, a post-hoc bandwidth estimate, an analytical cycle count, and a stats struct — and explain why they must never be summed;
3. derive the 40-element census numbers (softmax 96, normalization 80, elementwise 40) from the pinned SRAM budget model, including which engine discards its read stalls;
4. state the attention engine's composition graph and hand-derive its tiny-case stats (`dma=16 B, tiles=2, flops=8, compute=145, dma=2, total=147, util=0.9864`);
5. explain the attention FP16 SRAM staging defect (4-byte copies on 2-byte elements), why its corrupted magnitudes are undefined-behavior-dependent, and which attention claims must be rejected at this pin;
6. explain why pipeline overlap is byte-proportional to load descriptors and why `enable_load_overlap` alone is a configured-but-ineffective state;
7. map which engines are reachable from non-test code (queue → elementwise; DPI → softmax + elementwise) and which are standalone; and
8. audit aggregate test membership before quoting any engine suite result.

## Prerequisite graph

This chapter assumes:

- Chapter 2's evidence ladder and snapshot-conformance discipline;
- Chapter 6's MMA semantics, MAC counting, and tiling vocabulary;
- Chapter 8's FP16/FP32 representation vocabulary (needed to read the attention staging defect);
- Chapter 9's banked-SRAM model (bank width, bank index, budget/refill, stall penalty);
- Chapter 10's separation of byte effects, service estimates, and elapsed time; and
- Chapter 12's lesson that adjacent APIs at different evidence rungs must not be merged.

```text
Chapter 2 evidence discipline
          │
          ├──── Chapter 6 MMA and MAC semantics
          ├──── Chapter 8 FP16/FP32 representation
          ├──── Chapter 9 banked SRAM model
          ├──── Chapter 10 byte effects vs estimates
          └──── Chapter 12 adjacent-surface discipline
                         │
                         ▼
          Chapter 14 operator compute engines
```

This chapter does not reopen MMA arithmetic, SRAM banking internals, or DMA descriptor ownership. It asks what each operator engine computes, what its return value means, and how the engine is integrated — or not — into a running system.

## Opening architecture question: when can you trust an operator engine's return value?

A performance team measures the same 40-element in-place operator workload on the same SRAM region model and records three numbers: softmax returns 96, normalization returns 80, elementwise returns 40. The natural move is to write them into one column and compare:

> Softmax costs 96 cycles, normalization 80, elementwise 40. Elementwise is the cheapest operator, and the fused pipeline should use it everywhere.

That conclusion is unsupported. The three numbers are not three measurements of one thing; they are three different accounting dialects over the same underlying SRAM budget model. Softmax's 96 counts read stalls **and** write stalls through the banked-SRAM API. Normalization's 80 counts only write stalls, because its load helper discards the read return — yet the reads still consume bank budget, so the 80 is not "the same as softmax minus reads" in any clean sense. Elementwise's 40 never touches the SRAM API for accounting at all: it refills every bank budget, meters a subset of elements post-hoc, labels every accounted event as a *write*, and returns the count. None of the three is a latency.

The other engines speak still other dialects. Pooling returns an analytical cycle count (18 for a 4×4→2×2 max pool), convolution exposes a **separate** estimate API (69 for the chapter's probe case), and attention fills a seven-field stats struct (`dma_bytes`, `mma_tiles`, `mma_flops`, `compute_cycles`, `dma_cycles`, `total_cycles`, `utilization`) while returning only 0/-1 status. The fidelity matrix's "Compute engines" row already warned: *never sum heterogeneous return values into total latency*. This chapter makes that rule operational by showing exactly what each engine returns and why.

The disciplined question for a reader is therefore not "how fast is softmax?" but:

1. what functional output does the engine produce for a named workload (the byte effect);
2. what does the engine's return value count, in which cycle domain;
3. how is the engine reached from non-test code, if at all;
4. which returned quantities are deterministic analytical estimates, which are UB-dependent, and which are calibrated (none); and
5. what additional evidence is required before any engine metric becomes a physical design recommendation.

The source basis is the frozen edition commit `e918c80b6fce833cd1fcae97730fa841c2176f25`. Exact commands, source hashes, mutation controls, logs, and retained manifests are recorded in the [Chapter 14 audit](../../experiments/ch14-compute-engines-audit-2026-08-04.md), and the sealed evidence run is `experiments/runs/ch14-compute-engines/20260804-ch14-canonical-v3/`.

### Source map

| Contract | Exact pinned source or test |
|---|---|
| Convolution engine (dims, direct references, im2col+GEMM, estimate API) | `tu_cmodel/compute/convolution_engine.{h,c}` |
| Softmax engine (two-pass/online, stall return) | `tu_cmodel/compute/softmax_engine.{h,c}` |
| Attention engine (composition, stats, FP16 staging defect) | `tu_cmodel/compute/attention_engine.{h,c}` |
| Normalization engine (LayerNorm/RMSNorm, discarded read return) | `tu_cmodel/compute/normalization_engine.{h,c}` |
| Pooling engine (max/avg, analytical cycle return) | `tu_cmodel/compute/pooling_engine.{h,c}` |
| Elementwise pipeline (fused ops, post-hoc accounting) | `tu_cmodel/compute/elementwise_pipeline.{h,c}` |
| Pipeline controller (tile state machine, overlap stats) | `tu_cmodel/compute/pipeline_controller.{h,c}` |
| Banked SRAM budget model (bank width, index, refill, penalty) | `tu_cmodel/tu_sram.{h,c}` |
| Integration points (command queue, DPI) | `tu_cmodel/command_queue.c`, `tu_cmodel/bindings/tu_dpi.c`, `tu_cmodel/tu_cmodel.c` |
| Focused suites | `tests/test_{convolution,softmax,attention,normalization,pooling,elementwise,pipeline}.c` |
| MMA dataflow plugins | `tu_cmodel/compute/dataflow/*.c` |
| Historical exploration | `docs/attention-engine.md`, `docs/convolution-engine.md`, `docs/normalization-engine.md`, `docs/pooling-engine.md`, `docs/elementwise-pipeline.md`, `docs/software-pipelining.md`, `docs/TU_SOFTMAX.md`, `docs/exploration/` sweep reports |

All paths refer to the edition commit above. The audit record gives exact hashes and reachability predicates rather than treating filenames as evidence by themselves.

---

## 14.1 Seven engines, four return-value dialects

“Does Tusim support convolution?” is too coarse to be useful. The operator surface exposes seven modules and at least four mutually incompatible ways of reporting cost. A reader must first classify the return value, then decide what — if anything — it may be compared with.

| Engine | Entry point | Functional contract | Return value | Return domain |
|---|---|---|---|---|
| Softmax | `tu_softmax_execute` | standard two-pass or online row softmax on an SRAM region | `uint64_t` stall cycles, `UINT64_MAX` on invalid descriptor | SRAM read+write stalls |
| Normalization | `tu_norm_execute` | LayerNorm or RMSNorm on an SRAM region | `uint64_t` stall cycles, `UINT64_MAX` on invalid descriptor | SRAM write stalls only (read return discarded) |
| Elementwise | `tu_ew_execute` | fused chain of ≤8 ops over an SRAM region | `uint64_t` post-hoc event-count estimate (served + stalled write-labeled events after a budget refill) | refilled-budget event counter, not API stalls |
| Pooling | `tu_pool_execute` | MaxPool2D/AvgPool2D over source→destination regions | `int64_t`: non-negative analytical cycle count on success, `−1` on invalid descriptor | analytical equation, not SRAM stalls |
| Convolution | `tu_conv2d_direct_nchw_fp32`, `tu_conv2d_im2col_gemm` | direct or im2col+GEMM FP32 convolution | no cycle return (functional only); `tu_conv_estimate_cycles` is a separate API | analytical estimate equation |
| Attention | `tu_attention_execute` | tiled FP16 attention composing dataflow MMA, elementwise, softmax | `0`/`-1` status; fills `tu_attention_stats_t` | stats struct with compute/DMA/total cycles and utilization |
| Pipeline controller | `tu_pipeline_submit_tile`/`advance`/`get_stats` | bounded multi-tile state machine | stats accessor with `sequential_total`, `cycles_saved`, `total_stalls` | controller ledger, not an engine metric |

The four dialects are real in the code, not a taxonomist's convenience. Softmax and normalization both return “stall cycles,” yet they count different subsets of the same events (14.2–14.4). Pooling returns a number that is not derived from SRAM budget consumption at all (14.6). Convolution's functional path returns nothing and its estimate path is a separate call (14.7). Attention's struct mixes two cycle domains — compute and DMA — under one `total_cycles`, with a utilization ratio derived from them (14.8).

**The no-sum rule.** A total “engine latency” formed by adding softmax's 96, normalization's 80, elementwise's 40, pooling's 18, convolution's 69, and attention's 147 mixes read+write stalls, write-only stalls, refilled-budget write-labeled events, an analytical equation, a separate estimate API, and a struct's compute+DMA total. Each quantity answers a different question; their sum answers none.

---

## 14.2 The metric census: three returns under one workload label

The census is the chapter's central experiment: the identical 40-element in-place FP32 workload, staged with raw pointers (so staging itself consumes no bank budget), on a fresh default SRAM region. The pinned budget model (Chapter 9, `tu_sram.{h,c}`) fixes:

- 32 banks, bank width 4 bytes, initial budget one word per bank, one word per cycle;
- `tu_sram_bank_index = (addr / 4) % 32`;
- a stall penalty of 2 cycles per exhausted-budget access;
- budget refill only through `tu_sram_advance_cycle` (per-bank `words_available` reset by refill window);
- `tu_sram_read`/`tu_sram_write` copy `bank_width` (4) bytes regardless of the caller's element size.

The three accounting paths produce:

| Engine | Load stalls counted | Store stalls counted | Census return | Why |
|---|---:|---:|---:|---|
| Softmax | yes | yes | **96** | 40 loads: 32 served on fresh banks, 8 stall (banks 0–7 touched twice) → 16; 40 stores: every bank exhausted → 80 |
| Normalization | **no** (discarded) | yes | **80** | loads consume budget but their returned stalls are dropped (`uint64_t s = 0;` never assigned); 40 stores stall → 80 |
| Elementwise | n/a (no API access) | n/a (post-hoc) | **40** | `tu_sram_advance_cycle(40)` refills every bank (refill is window-gated); in-place metering touches elements 0–19 twice each via the `i/2` index (20 served + 20 stalled, all labeled *write*) |

Two details deserve emphasis. First, normalization's 80 is *not* “softmax minus the 16 read stalls.” The loads still exhaust bank budget, so the store stalls are identical in both engines; what differs is whether the load-stall component (16) is reported. Second, elementwise's 40 is not 40 real accesses: in-place mode meters `words = elem_count` iterations but indexes `off += (i/2)·4`, so only elements 0..19 are metered, each twice (20 served, 20 stalled). The engine's own comment intends “2 words per element (read + write)”; the `i/2` indexing makes the in-place branch half-count. The value 40 is therefore a property of the accounting code, not of 40 physical SRAM accesses. Note also that the engines' actual access stream is one load plus one store per element — softmax's “two passes” and LayerNorm's “two passes” operate on the host row buffer, not by re-reading SRAM — so the census counts exactly 40 loads and 40 stores per engine.

The same engines on their smallest probed rows return 8 (softmax zeros row), 8 (LayerNorm on four ones), and 2 (a three-element fused chain) — small cases cannot reveal an accounting path; the census can.

---

## 14.3 Softmax: two-pass semantics and read+write stall accounting

`tu_softmax_execute` validates its descriptor, then runs each row through `softmax_row_two_pass` (standard mode) or `softmax_row_online` (online mode, which keeps running row statistics in one pass instead of the two-pass max-shift). The two-pass path implements the textbook max-shift: subtract the row maximum, exponentiate with `expf`, accumulate the sum in double precision, divide. When the sum is exactly zero (a row of `-inf` after masking), the engine emits the uniform distribution `1/N` — matching the “all -inf → uniform” convention the attention engine relies on.

The probe's canonical cases:

- **Zeros row.** `[0,0,0,0]` → `[0.25, 0.25, 0.25, 0.25]`, `max_out = 0.0`, returned stalls **8** (4 loads served on fresh banks; 4 stores stall at 2 cycles each).
- **Census.** 40-element row → returned stalls **96** (the derivation in 14.2).
- **Invalid descriptor** (`data_sram = NULL`) → `UINT64_MAX`, the engine's failure sentinel.

The return value counts `tu_sram_read` **and** `tu_sram_write` returns — both helpers in `softmax_engine.c` accumulate their per-access stall returns. Softmax is the only engine in the census whose return is a full read+write stall ledger for its own accesses. That ledger is still an analytical model of bank-budget exhaustion, not a measured time.

---

## 14.4 Normalization: LayerNorm/RMSNorm and the discarded read return

`tu_norm_execute` implements two normalizers. LayerNorm is the two-pass textbook algorithm — `mean = Σx/N`, `var = Σ(x−mean)²/N`, `y = (x−mean)/√(var+ε)·γ + β` — and RMSNorm is `rms² = Σx²/N`, `y = x/√(rms²+ε)·γ` with β ignored. Both operate on SRAM regions with optional gamma/beta regions and in-place or out-of-place output.

The probe's canonical cases:

- **LayerNorm** on `[1,1,1,1]`, ε=1e−5 → `[0,0,0,0]`, `mean_out = 1.0`, `var_out = 0.0`, returned stalls **8**.
- **RMSNorm** on the same row → `0.999995` each (`1/√(1+1e−5)`), `var_out = 1.0`, returned stalls **8**.
- **Census** → returned stalls **80**.

The census number is the chapter's first accounting lesson. The load helper `sram_load_floats` in `normalization_engine.c` declares `uint64_t s = 0;` and calls `tu_sram_read(sram, off, &out[i]);` **without assigning the return** — `total_stall += s` adds zero. The store helper accumulates `tu_sram_write` returns normally. The reads therefore still consume bank budget (which is why the stores stall identically to softmax's), but their stall component is silently dropped from the returned total. A reader who sees “normalization: 80 stall cycles” and compares it with “softmax: 96 stall cycles” is comparing a partial ledger with a complete one.

---

## 14.5 Elementwise: fused chains and post-hoc accounting

`tu_ew_execute` applies a fused chain of up to 8 operations to each element (17 opcodes), including GELU via the tanh approximation `0.5x·(1 + tanh(0.7978845608·(x + 0.044715x³)))`, SiLU `x/(1+e⁻ˣ)`, and the binary ADD/MUL/SUB/DIV/MIN/MAX. The semantics are defensive: DIV by zero yields 0.0, SQRT of a negative yields 0.0, LOG of non-positive yields −inf.

The probe's canonical cases:

- **Chain** `[ADD 2, RELU]` on `[-3, 1, 5]` → `[0, 3, 7]`, returned **2** — one exhausted-bank hit (element 0 metered twice, second hit stalls) × the 2-cycle penalty.
- **Census** → returned **40**.

Elementwise is the third accounting dialect. It never calls `tu_sram_read`/`tu_sram_write` for its data path (raw pointers), and its accounting block runs **after** the computation: it calls `tu_sram_advance_cycle(sram, elem_count)` — which resets each bank's budget when the refill window (4 cycles) has elapsed, so `advance_cycle(40)` refills every bank — then walks a `words`-long loop that labels every served word as a *write* (`writes_served++`) and every exhausted-budget access as a write stall (`write_stalls++`). The loop returns a raw event count (served + stalled events, unweighted: stalled events add the penalty but served events add zero), not a bandwidth-derived quantity — “estimate” only in the sense that the code estimates its own activity after the fact. Because the refill precedes the accounting, the returned number describes a region whose budget was just reset, not the state the engine actually worked in. And as shown in 14.2, the in-place `i/2` indexing meters only half the elements (each twice). The 40 is best read as “the accounting code's write-labeled event count after a refill,” which is neither stall cycles in the softmax/norm sense nor a per-element cost.

---

## 14.6 Pooling: an analytical cycle count with a different meaning

`tu_pool_execute` implements MaxPool2D and AvgPool2D with an explicitly different return contract. Its functional semantics: MaxPool ignores padded windows unless the whole window is padding (then it emits `pad_value`); AvgPool divides by the count of **valid** (non-padded) elements, so edge windows are not distorted by padding zeros.

The probe's canonical cases (4×4 input, 2×2 kernel, stride 2, no padding):

- **MaxPool** → `[6, 8; 14, 16]`, returned cycles **18**.
- **AvgPool** → `[3.5, 5.5; 11.5, 13.5]`, returned cycles **34**.

The returned value is `total_cycles = Σ_{batch,channel} (spatial_out · kh · kw · ops_per_elem) + kh`, where `ops_per_elem` is 1 for max and 2 for average (the average's extra add). For the probe case: 4 output windows × 4 elements × 1 = 16, plus the `kh = 2` drain term → 18; the average doubles the per-element term → 32 + 2 = 34. This is an analytical equation evaluated in the engine, not SRAM budget accounting: the pooling engine's return is a cycle estimate with a different producer and a different meaning from softmax's stalls. Validation rejects `elem_size` outside 1..8, unknown `pool_type`, and null regions.

---

## 14.7 Convolution: functional references, im2col+GEMM, and a separate estimate API

`tu_conv_compute_dims` derives the output geometry (OH/OW) and the im2col matrix shape; the probe case (all-ones 1×3×3 input, 2×3×1×1 kernel, weight `w[k][c] = c+1`) yields `oh=3, ow=3, im2col_rows=3, im2col_cols=9`. Two functional paths exist: the direct FP32 references (`tu_conv2d_direct_nchw_fp32`, `tu_conv2d_direct_nhwc_fp32`) and the im2col+GEMM pipeline (`tu_conv2d_im2col_gemm`). For the probe case both produce `6.000000` at every output position (each output = Σ_c (c+1) over the 3 channels). One format caveat: the im2col+GEMM path ignores `input_format` and always runs the NHWC arrangement — the descriptor field is decorative on that path, so “NCHW support” must not be claimed from the descriptor alone.

Convolution's cycle surface is a **separate** API, `tu_conv_estimate_cycles(desc, pe_rows, pe_cols)`, which returns 69 for the probe case from the pinned equation:

```text
estimate = ceil(C·H·W·4/32)                     im2col staging words (4 B per input element,
                                                 32 B per DMA cycle)
         + Σ_groups mt·nt·kt·(pipeline_depth·pe_cols + pe_cols)
                                                  per-tile GEMM work: mt/nt/kt = per-group
                                                 tile dims (1 for a 1×1 kernel),
                                                 pipeline_depth·pe_cols = fill/drain column
                                                 work, pe_cols = execute column work
         + K·im2col_n                            weight-plane work: K = kernel volume,
                                                 im2col_n = im2col matrix width
```

The probe case (1×3×3 input, 2×3×1×1 kernel, 16×16 PE, pipeline depth 2) evaluates each term: `3·3·3·4/32 = 3` (staging), `1·1·1·(2·16 + 16) = 48` (one group, mt = nt = kt = 1), `K·im2col_n = 2·9 = 18`, total **69**. That number is an analytical estimate of im2col and GEMM work — the same evidence class as Chapter 13's decoder equations: deterministic, uncalibrated, and not interchangeable with the stall-return dialect.

---

## 14.8 Attention: the composition point, its stats struct, and the FP16 SRAM staging defect

Attention is the only engine that composes the others: `tu_attention_execute` stages FP16 host tensors (Q/K/V) into SRAM tiles, calls the pluggable dataflow MMA for the Q·Kᵀ and P·V products, the elementwise pipeline for scale/mask-add, and the softmax engine (standard mode, in-place) for row normalization. Its contract is FlashAttention-style tiling (the [DAO22] reference supplies the algorithm vocabulary; it does not validate Tusim's equations).

**Stats struct.** `tu_attention_stats_t` carries `dma_bytes`, `mma_tiles`, `mma_flops`, `compute_cycles`, `dma_cycles`, `total_cycles`, and `utilization`. Throughout this section, **M = number of query rows, N = number of key/value rows, d = head dimension** (Q is M×d, K and V are N×d, output O is M×d). For the tiny case M=1, N=1, d=2, scale 1.0 on fresh state, the sealed probe returns `rc=0`, `dma=16 B, tiles=2, flops=8, compute=145, dma=2, total=147, util=0.9864`. Every field is hand-derivable:

- `dma_bytes = 16`: Q 4 + K 4 + V 4 + O-out 4 (FP16, 2 bytes each);
- `mma_tiles = 2`: one Q·Kᵀ tile plus one P·V tile;
- `mma_flops = 8`: `2·MACs` with MACs = (1·1·2) for Q·Kᵀ (M×d times d×N) + (1·2·1) for P·V (M×N times N×d) = 4 — each product is an M·N·d = 2 MACs, and the two factor orders are the same M·N·d product viewed from each operand's shape;
- `compute_cycles = 145`: transpose 4 + ew-scale 2 + softmax 4 + fp32→fp16 4 + MMA1 66 + MMA2 65, where each MMA = fill `pipeline_depth·tile_n` = 2·16 = 32, execute `k_count` (2 then 1), drain 32 (WS plugin equations); the four small terms are bank-conflict stall series during the tiny case's staging on near-exhausted banks (`attention_engine.c` stat accounting; each term re-derived in the audit);
- `dma_cycles = 2`: the S (score) region zero-init stalls on bank 0 after the O (output) region zero-init consumed it; the O zero-init hits fresh banks;
- `total_cycles = 147`, `utilization = 145/147 = 0.9864`.

The stats are deterministic **on fresh state**; a back-to-back second execute on the same global state inherits exhausted SRAM bank budgets and reports different DMA/compute totals, so “the stats” of an attention call depend on what ran before it in the process.

**Auto-tiling.** `tu_attention_auto_tile` caps tile sizes to the sequence lengths **before** aligning up to PE multiples and forcing a 16 minimum — the cap is undone by the later steps (M=2 logs `tile_m=16`). Execution counts are re-capped per tile, so the logged tile is a claim about the descriptor, not about the executed tiling. This is the same cap-then-align ordering defect family as Chapter 4's configuration-ladder gaps: a function that claims to bound a quantity must be checked for the order of its cap and its align/max steps.

**The staging defect (the chapter's central negative finding).** `fp32_to_fp16_in_sram` and `transpose_fp16_in_sram` stage 2-byte FP16 values through `tu_sram_read`/`tu_sram_write`, which copy `bank_width` = 4 bytes regardless of element size. The in-place FP32→FP16 conversion loop walks indices in reverse (`dst = offset + idx·2`) and writes 4-byte chunks at 2-byte offsets. Each write fully overwrites the 2-byte FP16 element written in the previous iteration with two garbage bytes, and the same 4-byte read misaligns the unconverted FP32 sources still in the region — the isolated reproduction converts `[1..6]` in place and reads back all zeros. The corrupted magnitudes are **undefined-behavior-dependent**: the 4-byte copies read past 2-byte locals into stack garbage, so the exact errors vary between builds and even between runs (observed max errors ≈0.53–0.68 for M=2,N=3,d=8, plus inf values when garbage bits decode as FP16 infinities). Two consequences follow:

1. **The attention suite never passes 9/9.** At the pin it runs 6–8/9 with rc=1; the failing subset varies by build (canonical v3: 6/9 with `test_identity`, `test_deterministic_small`, `test_causal`; canonical v2: 8/9 with `test_scale` — “same output for different scales, err=0.000000”; another build: 7/9 with `test_deterministic_small` + `test_causal`). The chapter gates the invariants — rc=1, at least one FAIL, never 9/9 — and labels the suite `ATTENTIONSUITEQUALIFIED`, never green.
2. **Arbitrary-input FP16 attention correctness is a rejected claim at this pin.** The differential check against a naive FP32 golden confirms the engine deviates far beyond the suite's 0.25–1.5 tolerances (`deviates=1`) while its outputs are byte-identical across scales (`scales_equal=1`) — the failure `test_scale` records. The M=1,N=1,d=2 case matches the golden exactly because a single P element has no adjacent element to corrupt.

The defect is confined to the FP16 **staging helpers**, not the softmax or MMA composition: the engine's internal softmax runs on the FP32 S (score) tile — 4-byte elements, bank-aligned — so it is not exposed to the 4-byte-copy-on-2-byte-element misalignment; only the FP16 staging paths (the fp32→fp16 conversion and the transpose of the Q/K tiles) move 2-byte elements through `tu_sram_read/write`. Any engine routing sub-`bank_width` elements through those APIs inherits the same class of corruption.

---

## 14.9 The pipeline controller: byte-proportional overlap, not flag-commanded

`tu_pipeline_controller.c` implements a bounded multi-tile state machine: 1–8 tile slots, stages IDLE → DMA_PRELOAD → COMPUTE → DMA_STORE → DONE, with `sequential_total` accumulating load+compute+store per tile (a tile without a descriptor charges the default **1** cycle for load and store). The sealed probe's canonical cases:

- **Depth 1** (no overlap possible): two descriptor-free tiles, compute 100 → `sequential_total = 204` = 2 × (1 + 100 + 1), `saved = 0`, `stalls = 0`.
- **Depth 2 with 3200-byte load descriptors** (load window = 3200/32 = 100 cycles at the 256-bit DMA bus's 32 B/cycle), compute 100, `enable_load_overlap = true`, store/triple overlap off → `sequential_total = 402` = 2 × (100 + 100 + 1), `saved = 200`, `stalls = 0`: both preload→compute transitions occur while `active_count == 2`, so the 100-cycle load window is credited twice (`overlapped_load_cycles`).

The decisive finding is that overlap credit is **byte-proportional to load descriptors**: descriptor-free tiles accrue zero overlap even with `enable_load_overlap = true`. The flag alone does nothing; the overlap is a property of the tile's DMA descriptor byte count. A reader must never infer “pipelining is on” from configuration — only from the descriptor-carrying tiles and the resulting `cycles_saved`. Backpressure, when retries are exhausted, returns −1 and counts a stall.

---

## 14.10 Integration map and test provenance

**Who can call an engine.** Non-test library callers, grepped across `tu_cmodel/` at the pin:

| Engine | Non-test library callers | |
|---|---|---|
| Elementwise | command queue (`tu_cmdq_submit_elementwise`, `TU_CMD_ELEMENTWISE`, `tu_cmodel.c:354`); DPI (`tu_dpi_elementwise`) | reachable |
| Softmax | DPI (`tu_dpi_softmax`) | reachable |
| Normalization | **none** — `tu_dpi.c` includes `normalization_engine.h` but never calls any `tu_norm_*` symbol | include-only gap |
| Attention | none (internally composes softmax/elementwise/dataflow MMA) | standalone |
| Convolution | none | standalone |
| Pooling | none | standalone |
| Pipeline controller | none | standalone |

The include-only gap is a reachability fact, not a link: a DPI file that *includes* a header and never calls its symbols exposes nothing. The chapter proves the negative case directly (grep for `tu_norm_*` callers outside the module and its tests) rather than inferring reachability from the include.

**Test provenance.** `make test` aggregates six engine suites — `test-elementwise`, `test-norm`, `test-conv`, `test-attention`, `test-pool`, `test-pipeline` — while **`test-softmax` has no Makefile rule at all**: the name appears only in `.PHONY` and `clean`, never as a target (the only softmax targets are the two sweeps). The canonical runner compiles `tests/test_softmax.c` directly — the same source-present-no-target pattern as Chapter 13's `test_int8_sweep.c`. All sweeps are standalone. The sealed canonical run's suite results:

| Suite | Result in canonical run | Aggregate `make test`? |
|---|---:|---|
| `test-elementwise` | 16/16 | yes |
| `test-norm` | 11/11 | yes |
| `test-convolution` | 12/12 | yes |
| `test-attention` | 6–8/9, rc=1 (failing subset UB-dependent) | yes — **qualified, never green** |
| `test-pooling` | 14/14 | yes |
| `test-pipeline` | 11/11 | yes |
| `test-softmax` | 15/15 | no — no Makefile rule; run by the runner directly |

A forced mutation of one softmax expected-value comparison (`0.25f → 0.5f` in the zero-input test) drops the runner-compiled suite to `14/15 passed, 1 failed` with a nonzero exit — proving the harness gate rather than assuming it. Aggregate membership is a reachability fact, not a correctness certificate: `test-attention`'s membership in `make test` means the aggregate target itself exits nonzero at this pin, which is precisely why the chapter reports the suite as qualified rather than green.

---

## 14.11 Trade-offs across the engine family

| Engine | When its functional model is trustworthy | Return-value caveat | Integration cost | Verification posture |
|---|---|---|---|---|
| Softmax | standard two-pass, finite rows | return = read+write stalls (both counted) | DPI-reachable | green suite 15/15; standalone target |
| Normalization | LayerNorm/RMSNorm formulas, ε > 0 | return = write stalls only (read return discarded) | include-only gap in DPI | green suite 11/11 |
| Elementwise | fused chains, defensive edge semantics | return = post-hoc write-labeled events after a refill; `i/2` in-place half-metering | queue- and DPI-reachable (the only queue-wired engine) | green suite 16/16 |
| Pooling | max/avg with valid-element averaging | return = analytical cycle count (18/34), different dialect | standalone | green suite 14/14 |
| Convolution | direct and im2col+GEMM agree on FP32 cases | cycle surface is a separate estimate API (69); `input_format` decorative on im2col path | standalone | green suite 12/12 |
| Attention | M=1,N=1,d=2 and stats fields; **not** arbitrary FP16 inputs | stats struct; compute+DMA totals are separate domains under one `total_cycles` | standalone (internally composes three engines) | qualified 6–8/9, rc=1 — never green |
| Pipeline controller | bounded tile state machine, descriptor-carrying tiles | overlap credit byte-proportional to load descriptors | standalone | green suite 11/11 |

Across the family, the accuracy/verification trade is dominated by the attention staging defect: its functional contract is broken for sub-`bank_width` elements, so any design that routes FP16 through attention at this pin must budget for corrupted staging, not for the defect being absent. Every other engine's returned metric is an analytical model of its own accounting path; none is calibrated, and none may be added to another engine's metric.

---

## 14.12 Fidelity box: what remains unknown

The sealed evidence establishes functional byte effects and deterministic analytical estimates per engine. It does not establish:

- measured latency, throughput, or calibrated timing for any engine metric;
- an integrated operator dispatch path (config → runtime → engine selection): the elementwise queue command is the only config-adjacent integration, and it is a direct API call, not engine selection by configuration;
- a whole-pipeline operator execution model (there is no config → runtime → operator dispatch path at the pin);
- arbitrary-input FP16 attention correctness (rejected: the SRAM access-width defect corrupts staging with UB-dependent magnitudes);
- that `enable_load_overlap` (or any overlap flag) produces overlap without descriptor-carrying tiles;
- that attention's stats describe a standalone call (they depend on prior global state);
- cross-engine cycle summation (prohibited by the no-sum rule);
- or behavior of any engine beyond the tested shapes and value domains (engine equations are unguarded at extreme dimensions).

A reader who needs any of these must find evidence outside this snapshot.

---

## 14.13 Failure modes

1. **Summing heterogeneous returns.** Adding softmax 96 + norm 80 + ew 40 + pool 18 + conv 69 + attention 147 into a “pipeline total,” each number from its own probe workload; the dialects are incompatible by construction.
2. **Reading stalls as latency.** Interpreting any stall/cycle return as elapsed time; all are analytical models of budget exhaustion or equation evaluation.
3. **Comparing partial ledgers.** Using normalization's 80 against softmax's 96 as “norm is cheaper”; norm discards its read-stall component while the reads still consumed budget.
4. **Trusting elementwise's 40 as a per-element cost.** The in-place `i/2` indexing meters half the elements twice, and the pre-accounting refill resets the budget the number describes.
5. **Trusting attention FP16 outputs.** Any M,N,d > tiny case routes corrupted staging; the suite's own failures are UB-dependent, so a passing subset on one build proves nothing about another.
6. **Assuming overlap from configuration.** `enable_load_overlap = true` without load descriptors yields `saved = 0`; overlap is byte-proportional to descriptors.
7. **Quoting auto-tile bounds.** `tu_attention_auto_tile` caps before aligning, so the logged `tile_m` can exceed the sequence length it was meant to bound.
8. **Assuming aggregate membership.** `test-softmax` is standalone; quoting “make test passes” without noting the qualified attention suite (rc=1) misrepresents the aggregate.

---

## 14.14 Summary

The operator engine family in Tusim is seven modules, four return-value dialects, and a partial integration map — not one operator runtime. The chapter's central lessons are:

1. **Return values are accounting, not latency.** Softmax counts read+write stalls (96 for the 40-element census), normalization counts write stalls only (80), elementwise counts post-refill write-labeled events with half-metering (40), pooling returns an analytical equation (18/34), convolution exposes a separate estimate API (69), and attention fills a stats struct (145/2/147, util 0.9864 for the tiny case).
2. **The no-sum rule is operational.** Heterogeneous cycle domains cannot be added; the census makes the rule visible in three engines sharing one SRAM model.
3. **Attention is the composition point with a broken FP16 staging path.** The 4-byte-copies-on-2-byte-elements defect corrupts outputs with UB-dependent magnitudes; the suite never passes 9/9 (6–8/9, rc=1), and arbitrary-input FP16 correctness is a rejected claim.
4. **Overlap is byte-proportional, not flag-commanded.** Depth-2 with 3200-B descriptors saves 200 cycles; descriptor-free tiles save zero even with `enable_load_overlap = true`.
5. **Integration is narrow.** Queue → elementwise; DPI → softmax + elementwise; normalization is include-only; conv/attention/pooling/pipeline are standalone.
6. **Test provenance matters.** Six suites are aggregated; `test-softmax` has no Makefile rule (runner-compiled); `test-attention` is qualified (never green), and the softmax mutation (14/15) proves the gates are real. For a future edition, the natural hardening step is extending the source-audit script with per-engine equation predicates (the value layer is currently enforced by the probe and runner greps — see the [skeptical-review dispositions](../../notes/chapter-14-skeptical-review-dispositions.md), R9).

---

## Review questions

1. The same 40-element in-place workload returns 96 from softmax, 80 from normalization, and 40 from elementwise. Derive each number from the pinned SRAM budget model (32 banks × 4 B, penalty 2), and name the single most important accounting difference between the three engines.
2. Why is “normalization costs 80 cycles” an incomplete sentence, even though the number is correct?
3. Elementwise returns 40 for the 40-element census. Show why this is not “one stall per element” and name the two code-level reasons.
4. Derive the tiny-case attention stats: `dma_bytes`, `mma_tiles`, `mma_flops`, and `utilization` for M=1,N=1,d=2, scale 1.0.
5. Why does the attention test suite never pass 9/9, and why is the *specific* failing test not a stable claim at this pin?
6. Which engines are reachable from non-test library code, and what is the include-only gap in `tu_dpi.c`?
7. A colleague sets `enable_load_overlap = true` and observes `saved = 0`. Explain what is missing, and give the depth-2 probe numbers that show overlap working.
8. What does pooling's 18-cycle return count, and why must it never be added to softmax's stall return?
9. Which engine suites are in aggregate `make test`, which has no Makefile rule at all, and what does the canonical run report for the attention suite?
10. What is the evidence class of every engine metric in this chapter, and what would be required before any of them becomes a physical design recommendation?

### Review-question answer key

1. Softmax: 40 loads — 32 served fresh, 8 stall (banks 0–7 twice) → 16; 40 stores — all banks exhausted → 80; total 96. Normalization: loads consume the same budget but their returned stalls are discarded (`uint64_t s = 0;` never assigned) → stores only → 80. Elementwise: `tu_sram_advance_cycle` refills every bank, then the in-place `i/2` loop meters elements 0–19 twice (20 served + 20 stalled, all labeled writes) → 40. The key difference: which stall components the engine's own code chooses to count.
2. The 80 counts write stalls only; the load stalls (16) were discarded while the loads still consumed bank budget. It is a partial ledger, comparable only with other write-only returns.
3. The in-place branch computes `words = elem_count` but indexes `off += (i/2)·4`, so only elements 0..19 are metered (each twice); and the accounting runs after `tu_sram_advance_cycle(elem_count)` refills all budgets, labeling every served word a write. The returned 40 stall cycles = 20 exhausted-bank hits × 2-cycle penalty (served events add zero); it is not 40 physical accesses.
4. `dma_bytes = 16` (Q 4 + K 4 + V 4 + O 4, FP16); `mma_tiles = 2`; `mma_flops = 2·(1·1·2 + 1·2·1) = 8`; `compute_cycles = 145` (transpose 4 + ew-scale 2 + softmax 4 + fp32→fp16 4 + MMA1 66 + MMA2 65); `dma_cycles = 2`; `total = 147`; `util = 145/147 = 0.9864`.
5. The SRAM access-width defect (`tu_sram_read/write` copy 4 bytes on 2-byte FP16; the reverse-order in-place conversion clobbers high bytes) corrupts staging with UB-dependent magnitudes that vary with stack garbage, so which tests fail (6–8/9 observed: `test_scale`, `test_deterministic_small`, `test_causal` in various combinations) varies by build. The stable claims are rc=1, at least one FAIL, never 9/9.
6. Queue → elementwise (`TU_CMD_ELEMENTWISE`); DPI → elementwise and softmax. `tu_dpi.c` includes `normalization_engine.h` but never calls any `tu_norm_*` symbol — include-only, a reachability gap. Conv/attention/pooling/pipeline have no non-test library caller.
7. Overlap credit is byte-proportional to load descriptors. With 3200-B loads (100-cycle window), compute 100, depth 2: `sequential_total = 402`, `saved = 200` (both preload→compute transitions credit the window). Descriptor-free tiles accrue zero overlap despite the flag.
8. `total_cycles = Σ(spatial_out · kh · kw · ops_per_elem) + kh` with `ops_per_elem` 1 (max) / 2 (avg): 16 + 2 = 18 for the probe. It is an analytical equation, not SRAM stall accounting — a different cycle domain.
9. `make test` aggregates elementwise, norm, conv, attention, pool, pipeline; `test-softmax` has no Makefile rule (only `.PHONY` and `clean` mention the name) and is compiled directly by the runner. Canonical: attention 6–8/9 rc=1 — reported as qualified (`ATTENTIONSUITEQUALIFIED`), never green.
10. Deterministic analytical estimates from pinned equations (stall accounting, equation evaluation) plus one UB-dependent defect outcome; nothing is calibrated against RTL, FPGA, or silicon. A physical recommendation needs a calibrated model of the relevant cost, a named workload, and a validated integration path.

---

## Design exercises

1. **Census re-derivation.** Using `tu_sram.{h,c}` at the pin, hand-derive softmax's 96 and normalization's 80 for the 40-element census; then write a small C program that prints both engines' returns and confirms your arithmetic.
2. **Elementwise half-metering.** Call `tu_ew_execute` with `elem_count = 40` in place on a fresh region and print the returned stalls; then modify the accounting loop's index in your own copy (do not modify the pinned tree) and explain what the number becomes and why.
3. **Attention defect repro.** Reproduce the isolated `fp32_to_fp16_in_sram` corruption with `[1..6]`; then run the attention suite twice in the same process state and record which tests fail in each run, confirming the UB-dependence of the failing subset. Then confirm the auto-tile cap-then-align order: call `tu_attention_auto_tile` on an M=2, N=3, d=8 descriptor and verify the logged `tile_m` is 16 (the cap is undone by alignment), while the executed tile counts are re-capped per tile.
4. **Stats re-derivation.** For the tiny attention case, compute `dma_bytes`, `mma_flops`, and `compute_cycles` by hand from the pinned WS-plugin equations, then compare with the sealed probe line `ATTN tiny rc=0 ... dma=16 tiles=2 flops=8 cc=145 dc=2 tc=147 u=0.9864`.
5. **Overlap sweep.** With `enable_load_overlap = true`, submit depth-2 tiles with load descriptors of 0, 800, 1600, and 3200 bytes and report `cycles_saved` for each; state the relationship between descriptor bytes and saved cycles.
6. **Integration map.** Grep `tu_cmodel/` at the pin for every caller of `tu_ew_`, `tu_softmax_`, `tu_norm_`, `tu_conv2d_`, `tu_pool_`, `tu_attention_`, and `tu_pipeline_` symbols outside `tests/`, and classify each engine as reachable or standalone. Confirm `normalization_engine.h` appears in `tu_dpi.c` with zero `tu_norm_*` calls.
7. **Membership map.** From the pinned Makefile, list which engine suites are in `make test`, which are standalone, and what the canonical run reports for each; explain what the attention suite's aggregate membership implies for `make test`'s exit status.
8. **Fidelity labeling.** Take the three census numbers (96/80/40) and rewrite them as sentences that name the accounting path, the cycle domain, the modeled and omitted costs, and the calibration status, per the style guide's quantitative writing rules.

---

## Primary references

- [DAO22] Dao, Fu, Ermon, Rudra, and Ré, “FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness,” NeurIPS 2022 — tiled attention with on-chip staging and online row statistics; vocabulary for why attention engines tile Q/K/V/P and why tile geometry interacts with SRAM capacity. It does not validate Tusim's cycle equations or its FP16 staging defect. Full entry in [references/foundations.md](../../references/foundations.md#dao22-flashattention).
- [CHE16] Chen, Emer, and Sze, “Eyeriss: A Spatial Architecture for Energy-Efficient Dataflow for Convolutional Neural Networks,” ISCA 2016 — convolution dataflow and on-chip reuse as design context for the conv/im2col paths; no numeric transfer to Tusim. Full entry in [references/foundations.md](../../references/foundations.md#che16-eyeriss).
- [PAR19] Parashar et al., “Timeloop: A Systematic Approach to DNN Accelerator Evaluation,” ISPASS 2019 — separating workload shape, architecture, mapping, and constraints; model-based estimates are not silicon-equivalent, the same discipline this chapter applies to engine metrics. Full entry in [references/foundations.md](../../references/foundations.md#par19-timeloop).
- [SAM18] Samajdar et al., “SCALE-Sim: Systolic CNN Accelerator Simulator,” arXiv 2018 — configurable accelerator simulation framing for operator-level cycle modeling; its “cycle accurate” description is bounded by its modeled abstraction. Full entry in [references/foundations.md](../../references/foundations.md#sam18-scale-sim).
- [BAN02] Banakar et al., “Scratchpad Memory: A Design Alternative for Cache On-chip memory in Embedded Systems,” CODES 2002 — why explicit on-chip scratchpad/region staging (as the engines' SRAM regions model) differs from caches in control and predictability. Full entry in [references/foundations.md](../../references/foundations.md#ban02-scratchpad-memory).
- [WAT09] Williams, Waterman, and Patterson, “Roofline: An Insightful Visual Performance Model for Multicore Architectures,” CACM 2009 — operational-intensity vocabulary for framing the census's stall-accounting distinctions as bandwidth-bound behavior. Full entry in [references/foundations.md](../../references/foundations.md#wat09-roofline-model).

All Tusim-specific claims in this chapter are sourced from the pinned commit and the sealed canonical-v3 evidence run; the references above supply vocabulary and design obligations only.
