# Chapter 13 — Weight Streams: Quantization, Structured Sparsity, and Compression

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-13)

Public edition: `7a094ff6c5527eff8e4318de676f0c0221c448b4`. The public-pin check covers the two JSON members, their full-config consumers and the named 2:4 estimates. Unless explicitly identified as public-pin results, the codec, quantization, suite and sweep observations below are historical (`e918c80b6fce833cd1fcae97730fa841c2176f25`).

## Opening architecture question: when does a smaller weight stream actually save time?

A compiler team must store a 128×128 FP16 weight matrix and stream it to the MMA once per inference. Three representations are on the table: plain FP16, an RLE codec for zeros, and a 2:4-structured sparse format that keeps two of every four elements. The naive analysis looks one-dimensional:

> The sparse format stores 62.5% of the dense bytes, and the RLE stream of 128 all-zero FP16 elements is 14 bytes instead of 256. Smaller payloads must mean faster loads.

That conclusion is premature in both directions. The 2:4 format does not halve end-to-end latency by itself: the packed weights must be reconstructed through a metadata decoder before the MMA can consume them, and the decoder's throughput is a configured assumption. With 2:4 explicitly enabled on the public pin, the standalone estimator gives these totals for a 512×16×512 GEMM on the default 16×16 PE array with a 256-bit DMA bus:

| Decoder provisioning | Dense FP16 total | 2:4 total | Direction |
|---|---:|---:|---|
| 1 group per cycle | 34,307 cycles | 77,312 cycles | 2:4 is **2.25× slower** |
| 16 groups per cycle | 34,307 cycles | 19,971 cycles | 2:4 is 1.72× faster |

The same format, same workload, same byte savings — but the direction of the result flips with a single configuration field. A decoder narrower than the DMA bus becomes the bottleneck and can erase the traffic advantage entirely; a decoder wide enough to keep up converts byte savings into cycle savings.

RLE has the mirror problem in the other direction. An alternating 128-element tensor expands to 776 bytes (8 header bytes plus 128 runs of 6 bytes each) versus 256 bytes raw, while the all-zero tensor compresses to 14 bytes. Whether RLE helps is a property of the tensor's run structure, not of the codec's name.

This chapter develops the disciplined alternative. It shows how to decide:

1. which weight representation Tusim executes functionally and which bytes it produces;
2. which configuration fields reach the codec, the sparse estimator, or nothing at all;
3. whether a reported cycle count is a payload-DMA estimate, a decoder-throughput estimate, an overlap assumption, or absent;
4. which INT8, UINT4, RLE, bitmap, adaptive, and 2:4 alternatives remain plausible in different regimes; and
5. what additional evidence is required before any of those alternatives becomes a physical weight-delivery recommendation.

### Source map

| Contract | Exact pinned source or test |
|---|---|
| INT8/UINT4 quantization, calibration, dot product, INT8 MMA tile | `tu_cmodel/tu_int_quant.{h,c}` |
| 2:4 masks, pruning, encode/decode, MMA helpers, cycle estimator | `tu_cmodel/sparsity/structured_2of4.{h,c}` |
| RLE/adaptive/bitmap codecs, frame format, DMA entry points, cycle estimator | `tu_cmodel/memory/weight_compress.{h,c}` |
| full-config parse, validation, and runtime conversion boundary | `tu_cmodel/infra/config.{h,c}`, `tu_cmodel/tu_config.h`, `config/tu_config.json`, `config/tu_config.yaml` |
| focused tests | `tests/test_int_quant.c`, `tests/test_sparsity.c`, `tests/test_compress.c` |
| linked sweeps | `tests/test_weight_compression_sweep.c`, `tests/test_sparsity_sweep.c` |
| source-present analytical report (no Makefile target) | `tests/test_int8_sweep.c` |
| historical exploration | `docs/exploration/weight-decoder-throughput.md`, `docs/exploration/bitmap-weight-compression.md`, `docs/exploration/structured-2of4-sweep.md`, `docs/exploration/weight-compression-rle-sweep.md`, `docs/exploration/int8-quantization-throughput.md` |

This source map describes the v1 audit. The audit record gives exact hashes and reachability predicates rather than treating filenames as evidence by themselves.

---

## 13.1 The decision begins with four different contracts

“Does Tusim support compressed weights?” is too coarse to be useful. The weight path exposes at least four contracts that must be audited separately.

| Contract | Question it can answer | What it cannot establish |
|---|---|---|
| **numeric conversion** | Can FP32 tensors be converted to INT8 or packed UINT4 with affine parameters, and can INT8 MACs accumulate in INT32? | an integrated INT8 MMA engine, precision-config dispatch, or accuracy-loss behavior |
| **byte-format codec** | What exact bytes do RLE, bitmap, and adaptive streams produce, and do the tested streams round-trip at zero merge tolerance? | measured decode latency, decoder area/power, or calibrated speedup |
| **structured sparsity** | What bytes does 2:4 packing produce, what MACs does sparse MMA count, and what do the analytical cycle equations return under named decoder provisioning? | a shared execution path with dense MMA, physical sparse-lane steering, or a universal 2× speedup |
| **configuration contract** | Which fields parse, validate, and reach which consumer — and which fields are dead or dropped at the runtime boundary? | runtime-config reachability for weight-path fields (there is none) |

The distinctions matter because the producers differ. `tu_int8_mma_tile()` accumulates INT32 in host memory. `tu_compress_rle()` writes a packed byte stream. `tu_sparsity_2of4_mma_fp16()` counts useful MACs on packed 2:4 data. `tu_config_to_runtime()` copies none of the weight-path fields. A correct chapter preserves these seams rather than smoothing them into a single “weight compression engine” story.

A useful evidence ladder is:

```text
source declaration
    -> parsed field
    -> validated field
    -> full-config consumer (codec mapper / sparse estimator)
    -> runtime-config retention (absent for the weight path)
    -> byte effect (encoded size, round trip)
    -> analytical estimate (payload DMA, decode, totals)
    -> physical decoder / silicon measurement
```

Tusim reaches different rungs for different APIs. A claim may move up the ladder only when its own producer and test justify the move.

---

## 13.2 The three surfaces are adjacent, not one pipeline

The header files share a “Gap” vocabulary — `tu_int_quant.h` says “Gap D2,” `structured_2of4.h` says “Gap P2.1,” and `weight_compress.h` documents stream formats; these are the modules' own gap-tracker identifiers, not evidence labels. Shared numbering is not shared integration — these are three adjacent surfaces, not one integrated pipeline. Three facts keep the surfaces separate at this pin:

1. **No direct-MMA caller.** The exact C-caller inventory in the audit proves `tu_int8_mma_tile`, `tu_int8_dot_product`, `tu_sparsity_2of4_mma_fp16`, `tu_sparsity_2of4_mma_tiled`, and `tu_compress_for_dma` are called only by their own implementation and focused tests. `tu_cmodel/tu_cmodel.c` — the direct MMA path — calls none of them (enforced by a negative audit predicate).
2. **No shared encoding.** The 2:4 compressor and the RLE/bitmap codecs use different wire formats; neither feeds the other, and no module consumes a packed stream directly as MMA operands. The implementation backlog marks a unified codec→decoder→sparse-MMA feed as **BLOCKED** on an architecture contract.
3. **Different consumers.** The compression fields reach `tu_compress_config_from_tu_config()`; the sparsity fields reach `tu_sparsity_2of4_estimate_cycles()`. These are separate full-config consumers with separate structs.

The practical consequence: choosing a 2:4 format and choosing an RLE codec are independent architecture decisions, and neither implies the other is active.

---

## 13.4 Structured 2:4 sparsity is a byte format with a configurable decoder

2:4 structured sparsity keeps exactly two non-zero values in every contiguous group of four elements. The valid masks are the six 4-bit patterns with exactly two bits set (`3, 5, 6, 9, 10, 12`); `tu_sparsity_2of4_mask_is_valid`, `mask_popcount`, and `mask_nth_bit` implement that contract. Magnitude-based pruning keeps the two largest-|value| elements per group and emits one mask per group (`prune_with_masks_fp32`; the sealed probe prunes 8 elements into 2 groups with masks `0x5` and `0x9`). The FP32 pattern verifier (`verify_pattern`) checks that every group has exactly two values above an epsilon, and `verify_against_dense` returns the maximum absolute difference between sparse and dense outputs — a numerical check, not a timing claim.

**Packed size.** The 2:4 packed format stores two values plus one metadata byte per group. For FP16, 128 elements form 32 groups and pack to `32 × (2×2 + 1) = 160` bytes versus 256 dense — a 37.5% byte reduction. `tu_sparsity_2of4_packed_size` inlines this formula for a caller element size (FP16/BF16 = 2 bytes, FP32 = 4, INT8 = 1), so the byte claim is parameterizable: the same 128-element tensor packs to `32 × (2×1 + 1) = 96` bytes at INT8 element size (a 25% cut from 128 dense bytes) and to `32 × (2×4 + 1) = 288` bytes at FP32 (a 43.75% cut from 512 dense bytes).

**Functional helpers.** `tu_sparsity_2of4_compress`/`decompress` and the per-group `encode_group`/`decode_group` move bytes between dense and packed forms with capacity checks. The dense-versus-2:4 MMA helpers (`mma_fp16`, `mma_tiled`) count useful MACs — dense `M×N×K` versus `M×N×K/2` — but they are standalone functional helpers with no direct-MMA caller, exactly like the INT8 tile. They return MAC-style counts and exercise the packed layout; they do not stream operands from SRAM or interact with the DMA path.

**The cycle estimator.** `tu_sparsity_2of4_estimate_cycles` is the analytical surface that actually consumes configuration. It requires nonzero M/N/K, `K` divisible by four, nonzero PE geometry, DMA width ≥ 8 bits, and a nonzero decoder rate; it rejects invalid inputs with `false` (the focused test confirms `K=15` is rejected). The estimator's orientation is fixed: the dense MAC count is `M×N×K`, the **M×K operand is the 2:4-packed stream** (so `groups = M·K/4` and packed weight bytes are `groups × (2·elem_size + 1)`), and the activation/output bytes are `K×N` and `M×N` FP16/FP32 respectively. Compute cycles use `ceil(macs / (pe_rows·pe_cols)) + (2·pipeline_depth − 1)`, where the constant term is the fill/drain overhead of the depth-2 pipeline (`2·2 − 1 = 3`). Under default configuration (16×16 PE, pipeline depth 2, 256-bit DMA = 32 bytes/cycle) it computes, for a square 128³ GEMM:

| Quantity | Dense | 2:4 |
|---|---:|---:|
| useful MACs | 2,097,152 | 1,048,576 |
| weight bytes | 32,768 | 20,480 |
| DMA cycles (weights + activation + output) | 4,096 | 3,712 |
| compute cycles (`ceil(macs/256) + 3`) | 8,195 | 4,099 |
| decode cycles (`ceil(groups/rate)`) | — | 4,096 at rate 1 |
| **total cycles** | **12,291** | **7,811** |

The sparse total is `sparse_dma + max(sparse_compute, decode)`: the `max` models metadata decode overlapping compute, an assumption, not a queue or schedule. The same equation on the narrow-N workload (512×16×512) demonstrates the decoder regime flip from the chapter's opening question — at one group per cycle the decode term (65,536) dominates and 2:4 loses (77,312 vs 34,307); at 16 groups per cycle the decode term shrinks to 4,096 and 2:4 wins (19,971 vs 34,307). The narrow-N numbers derive from the M×K orientation: `groups = 512·512/4 = 65,536`, packed weight bytes `65,536 × 5 = 327,680`, sparse DMA `ceil((327,680 + 16,384 + 32,768)/32) = 11,776`, and compute `ceil(2,097,152/256) + 3 = 8,195` — had the 16×512 activation been packed instead, the decode term would collapse to 2,048 and the flip would vanish, which is precisely why the operand choice is part of the model. Selection follows `cfg->sparsity_enabled && cfg->sparsity_2of4`; when either is false the estimator returns the dense totals.

The estimator's cycle counts are deterministic analytical estimates. They include DMA serialization and a decode-overlap assumption; they omit metadata-fetch alignment, sparse-lane imbalance, pruning accuracy loss, decoder area/power, and compiler packing overhead. None of the quantities are calibrated.

---

## 13.6 Configuration has one ladder for the weight path, and it stops at the full config

The full config declares both blocks: `weight_compression` (enabled, type string→enum, `rle_epsilon`, `decoder_enabled`, `decoder_overlap_dma`, `decoder_elements_per_cycle`, `rle_runs_per_cycle`, `bitmap_elements_per_cycle`) and `sparsity` (enabled, `structured_2of4`, `unstructured`, `metadata_format`, `decoder_groups_per_cycle`). Validation rejects unknown compression types, unstructured sparsity (not implemented), `enabled` without 2:4, `structured_2of4` without `enabled`, and zero decoder groups — the sealed probe exercises the four sparsity rejection classes (unstructured, `enabled` without 2:4, `structured_2of4` without `enabled`, zero groups), while the unknown-compression-type rejection is covered by source audit.

On the public pin, `tu_config_to_runtime()` carries PE pipeline depth and DMA bus width, among other settings, but not the fields of these two weight blocks. The codec mapper and the sparse estimator take `tu_config_t`, not `tu_runtime_config_t`. Their results below are not evidence that ordinary MMA decodes weights. The shipped JSON declares compression disabled/`none` with the decoder disabled, overlap true, and unit widths; sparsity is fully disabled with one group per cycle. The shipped YAML carries the sparsity defaults but has **no `weight_compression` block at all** — JSON and YAML are not synchronized on the compression surface.

Field-level reachability is uneven within the full config:

- all **eight** compression fields reach `tu_compress_config_from_tu_config()`;
- of the **five** sparsity fields, exactly three — `sparsity_enabled`, `sparsity_2of4`, `sparsity_decoder_groups_per_cycle` — reach `tu_sparsity_2of4_estimate_cycles()`;
- `sparsity_unstructured` is read only by `tu_config_validate()` (to reject it);
- `sparsity_metadata_format` is initialized to 0 and exposed by configuration documentation. The loader does not parse the JSON member; the estimator does not consult it. Seeing 0 after loading `"bitmask"` therefore does not establish a parser mapping.

The public probe compares C defaults, the complete shipped JSON and the wrapped members. All three leave compression and 2:4 off and select the dense estimate (34,307 cycles for 512×16×512). Enabling adaptive compression changes the mapped codec to type 4. With 2:4 enabled at the same narrow shape, changing only groups/cycle from 1 to 16 changes the selected estimate from 77,312 to 19,971. The estimator takes the full config directly: the effect does not pass through runtime conversion or through MMA.

## 13.8 A workflow for choosing a weight representation

1. **Name the byte effect first.** Compute or probe the exact encoded size for the actual tensor: raw `2n` bytes, RLE by run structure, bitmap by zero count, 2:4 by `(n/4)×(2·elem_size + 1)`, INT8 `n` bytes, UINT4 `ceil(n/2)` bytes.
2. **Add the decoder, not just the payload.** Ask whether a finite decoder must reconstruct dense values before the MMA. Use `tu_compress_estimate_cycles` and `tu_sparsity_2of4_estimate_cycles` with explicit decoder widths and the overlap flag; never convert a byte saving directly into a latency saving.
3. **Check the regime, not the name.** RLE wins on clustered zeros, expands on alternating data, and bitmap wins on scattered zeros; 2:4 helps only when the decoder keeps up. Report the workload, the shapes, and the decoder provisioning with every number.
4. **Trace the configuration ladder.** Confirm which fields parse, validate, reach which full-config consumer, and which are dead (`sparsity_metadata_format`) or dropped (`all` at the runtime boundary).
5. **State the evidence rung.** Label each quantity: byte effect, deterministic analytical estimate, overlap assumption, or historical analytical report. Nothing here is calibrated.

---

## 13.9 Trade-offs across the family

| Alternative | Performance regime | Area/power expectation | Control and verification | Accuracy effect |
|---|---|---|---|---|
| dense FP16 (default) | accuracy-sensitive, irregular weights, no decoder hardware | baseline; no decode logic | none beyond the default path | none |
| INT8 / UINT4 | numerical budget allows integer representation | negligible per-conversion logic; packer for UINT4 | unsaturating INT32 accumulation; conversion-before-clamp UB outside caller range; standalone tile only | unquantified at the pin; calibration is caller-provided |
| RLE | long zero/value runs (clustered or block-pruned tensors) | run parser; expands on alternating/random data | run metadata; validation required; metadata runs share the decode rate | lossless |
| bitmap | scattered zeros with placement-independent metadata | bitmap scanner and packer | bitmap scan/merge cost; variable-rate output | lossless |
| adaptive (raw/RLE/bitmap) | heterogeneous tensors with bounded fallback | two or three decode paths + frame logic | 16-byte frame; version/codec state; strict-smaller selection | lossless; raw fallback is exact |
| 2:4 structured | prunable weights with a decoder wide enough to keep up | metadata byte per group; decode lanes provisioned by rate | 37.5% FP16 byte cut and halved MACs, but decode-provisioning dependent; pruning is magnitude-only | pruning accuracy loss unquantified |

The full-config switches discussed here select a codec configuration or an estimator total. They do not dispatch INT8, UINT4 or sparse arithmetic in ordinary MMA. Physical decoder area/power, FIFO depth, SRAM conflicts during decode, ISA auto-dispatch of 2:4, and silicon calibration remain unmodeled.

---

## 13.10 Fidelity box: what remains unknown

The sealed evidence establishes byte effects and deterministic analytical estimates. It does not establish:

- measured decode latency, decoder area/power, or FIFO behavior;
- an integrated codec→decoder→sparse-MMA feed (BLOCKED in the implementation backlog);
- accuracy-loss results from pruning or quantization (no trained-model evidence at the pin);
- runtime-config reachability for weight-path fields (there is none by design);
- a calibrated speedup for any representation;
- behavior of the INT8 conversion at out-of-range or non-finite scaled values (excluded as undefined);
- extreme-dimension estimator totals (unguarded uint64 arithmetic beyond the tested shapes);
- or any claim that a smaller stream is automatically faster.

A reader who needs any of these must find evidence outside this snapshot.

[Next: Chapter 14 — Operator Compute Engines: Functional Semantics and Engine Metrics](14-operator-compute-engines-functional-semantics-and-engine-metrics.md)
