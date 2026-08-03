# Chapter 13 — Weight Streams: Quantization, Structured Sparsity, and Compression

Tusim edition commit: `e918c80b6fce833cd1fcae97730fa841c2176f25`

## Learning objectives

After this chapter, you should be able to:

1. distinguish byte effects (encoded sizes, round-trip equality), deterministic analytical estimates (payload DMA cycles, decode cycles, totals), configured-state reachability, decoder-throughput assumptions, and calibration status in a weight-stream model;
2. choose among INT8, UINT4, dense FP16, RLE, bitmap, adaptive, and 2:4-structured representations by traffic and decoder regime rather than by name;
3. trace `weight_compression` and `sparsity` configuration from JSON through full-config parse and validation to the exact consumers, and prove that `tu_config_to_runtime()` drops every weight-path field;
4. derive the 2:4 packed-size, DMA-cycle, compute-cycle, and decode-cycle equations under named assumptions;
5. derive the RLE, bitmap, and adaptive encoded sizes and the decoder-bound overlap/serial cycle formulas;
6. explain why payload-only measurements overstate compression and sparsity speedups, and when a decoder becomes the bottleneck;
7. classify the INT8 MMA tile and the 2:4 MMA helpers as standalone functional surfaces with no direct-MMA integration; and
8. audit aggregate membership and sweep provenance before quoting any weight-path number.

## Prerequisite graph

This chapter assumes:

- Chapter 2's evidence ladder and snapshot-conformance discipline;
- Chapter 4's distinction among declared, parsed, converted, consumed, and effective configuration;
- Chapter 6's MMA semantics and MAC counting;
- Chapter 8's FP16/FP32 representation vocabulary;
- Chapter 10's separation of byte effects, service estimates, and elapsed time; and
- Chapter 12's lesson that adjacent APIs at different evidence rungs must not be merged.

```text
Chapter 2 evidence discipline
          │
          ├──── Chapter 4 configuration contracts
          ├──── Chapter 6 MMA and MAC semantics
          ├──── Chapter 8 FP16/FP32 representation
          ├──── Chapter 10 byte effects vs estimates
          └──── Chapter 12 adjacent-surface discipline
                         │
                         ▼
          Chapter 13 weight streams: quantization, sparsity, compression
```

This chapter does not reopen MMA arithmetic, SRAM banking, or DMA descriptor ownership. It asks how a weight tensor can be represented on its way to the MMA, what bytes change, and which cycle quantities are deterministic estimates under named decoder assumptions.

## Opening architecture question: when does a smaller weight stream actually save time?

A compiler team must store a 128×128 FP16 weight matrix and stream it to the MMA once per inference. Three representations are on the table: plain FP16, an RLE codec for zeros, and a 2:4-structured sparse format that keeps two of every four elements. The naive analysis looks one-dimensional:

> The sparse format stores 62.5% of the dense bytes, and the RLE stream of an all-zero tensor is 14 bytes instead of 256. Smaller payloads must mean faster loads.

That conclusion is premature in both directions. The 2:4 format does not halve end-to-end latency by itself: the packed weights must be reconstructed through a metadata decoder before the MMA can consume them, and the decoder's throughput is a configured assumption. At Tusim's pinned snapshot, the linked cycle estimator gives these totals for a 512×16×512 GEMM on the default 16×16 PE array with a 256-bit DMA bus:

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

The source basis is the frozen edition commit `e918c80b6fce833cd1fcae97730fa841c2176f25`. Exact commands, source hashes, mutation controls, logs, and retained manifests are recorded in the [Chapter 13 audit](../../experiments/ch13-weight-streams-audit-2026-08-03.md), and the sealed evidence run is `experiments/runs/ch13-weight-streams/20260803-ch13-canonical-v8/`.

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

All paths refer to the edition commit above. The audit record gives exact hashes and reachability predicates rather than treating filenames as evidence by themselves.

---

## 13.1 The decision begins with four different contracts

“Does Tusim support compressed weights?” is too coarse to be useful. The weight path exposes at least four contracts that must be audited separately.

| Contract | Question it can answer | What it cannot establish |
|---|---|---|
| **numeric conversion** | Can FP32 tensors be converted to INT8 or packed UINT4 with affine parameters, and can INT8 MACs accumulate in INT32? | an integrated INT8 MMA engine, precision-config dispatch, or accuracy-loss behavior |
| **byte-format codec** | What exact bytes do RLE, bitmap, and adaptive streams produce, and do they round-trip? | measured decode latency, decoder area/power, or calibrated speedup |
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

## 13.3 Quantization is a numeric conversion surface, not a compute engine

`tu_int_quant` implements per-tensor affine quantization with the contract `real = (q - zero_point) * scale` for INT8 (`-128..127`) and packed UINT4 (`0..15`, two values per byte, low nibble first).

**Default parameters.** `tu_quant_params_init_int8` sets `scale ≈ 1/127`, `zero_point = 0` (symmetric); `tu_quant_params_init_uint4` sets `scale ≈ 1/15`, `zero_point = 8`.

**Calibration.** Symmetric INT8 calibration computes `scale = max(|data|) / 127` with zero-point 0 and substitutes `amax = 1.0f` for an all-zero buffer. Asymmetric INT8 calibration fits a `[min, max]` range and derives a nonzero zero-point; UINT4 calibration fits `(max - min) / 15` with the zero-point placed at the low end. The sealed probe confirms symmetric calibration of the data `0..127` yields `scale = 1.0`, `zp = 0`.

**Conversion.** `tu_fp32_to_int8` computes `round(v/scale) + zero_point` and clamps to `[qmin, qmax]`. Two qualifications matter. First, the `(int32_t)` conversion happens before the clamp, so a scaled value outside `int32_t` range — or a non-finite one — is undefined behavior; callers must keep `scale` finite, positive, and such that `roundf(v/scale) + zero_point` stays in range. Second, the INT8 dot product and MMA tile accumulate in **unsaturating INT32**; on very long maximal-magnitude vectors the sum can overflow. The probe exercises small, in-range vectors only (`dot=32`, MMA tile `19/22/43/50` for `W=[1 2;3 4]`, `A=[5 6;7 8]`).

**UINT4 packing.** `tu_uint4_pack`/`tu_uint4_unpack` place even indices in the low nibble and odd indices in the high nibble of each byte. The probe packs `10` at index 0 and `5` at index 1, producing byte `0x5A`, and unpacks them back.

**Reachability.** `tu_int_quant.o` is a `TU_OBJS` member and `test-int-quant` is in aggregate `make test` (14/14). But the INT8 MMA tile is standalone: it is not reachable from the direct MMA path, and no precision-config field selects it. The historical `int8-quantization-throughput.md` report and the source-present `test_int8_sweep.c` model INT8 gains analytically (WS fill/compute/drain/DMA) without linking the cmodel; `test_int8_sweep.c` has no Makefile target and was not executed in the canonical run. They are historical analytical orientation, not executable INT8-MMA evidence.

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

## 13.5 Compression codecs are exact byte formats with a decoder-throughput model

`weight_compress` implements five runtime types — NONE, RLE, ADAPTIVE_RLE, BITMAP, ADAPTIVE — with two wire-format families and one estimator.

**RLE.** The stable RLE format is `{element_count u32, run_count u32, then {value u16, count u32} runs}`, with fields copied individually so struct padding never enters the stream. An all-zero 128-element tensor is 14 bytes (8 header + one 6-byte run); an alternating 128-element tensor expands to `8 + 128×6 = 776` bytes versus 256 raw. `tu_compress_validate` rejects malformed streams by run-count and exact-size checks; the sealed probe corrupts the run count and proves rejection.

**Bitmap.** The exact bitmap format is `{element_count u32, nonzero_count u32, ceil(n/8) bitmap bytes, packed FP16 nonzero values}`; a set bit means that position's FP16 pattern is stored. For a 1/3-sparse 128-element tensor (43 nonzeros) this is `8 + 16 + 86 = 110` bytes.

**Adaptive.** `tu_compress_adaptive_rle` compares raw and RLE; `tu_compress_adaptive` compares raw, RLE, and bitmap. Selection picks a codec only when strictly smaller than the current candidate, so raw wins ties and output never exceeds raw plus the fixed 16-byte frame. The sealed probe's 1/3-sparse tensor selects bitmap (`codec=2`, `size=126` = frame + 110).

**Frame.** Adaptive streams are explicitly framed: `magic 0x54555743`, version 1, codec byte, reserved u16, `element_count` u32, `payload_bytes` u32 — a decoder never guesses the codec from payload bytes. The 2:4 compressor and the RLE/bitmap codecs use **different** formats; neither feeds the other.

**The cycle estimator.** `tu_compress_estimate_cycles` computes:

- `payload_bytes` = stream size;
- `dma_cycles = ceil(size / (dma_bus_width_bits / 8))`;
- when the decoder is enabled and the codec is not raw, `decode_cycles = max(ceil(elements / decoder_elements_per_cycle), ceil(metadata_units / run_or_bitmap_width))`;
- `decoder_bound = decode_cycles > dma_cycles`;
- `total_cycles = overlap ? max(dma, decode) : dma + decode` under `decoder_overlap_dma`.

The sealed probe on the 14-byte all-zero RLE stream at 256-bit DMA gives `dma=1`, default decode `128` (`max(ceil(128/1), ceil(1/1))`), `total=128`, `bound=1`; a wide decoder (`16` elements/cycle, `4` runs/cycle) gives `decode=8, total=8`; disabling overlap serializes to `total=9`. The decoder widths are configured assumptions about provisioning — never measured hardware. `decoder_bound` is an estimate classification, not a physical bottleneck proof.

It is worth deriving one decode total by hand to see where the terms come from. The all-zero stream is 14 bytes, so the DMA term is `ceil(14 / 32) = 1` cycle. The stream header reports 128 elements and one run. With the default decoder width of one element per cycle, reconstructing the dense tensor takes `ceil(128 / 1) = 128` cycles; the single run's metadata takes `ceil(1 / 1) = 1` cycle, and the decoder term is the maximum of the two, 128. Because the decode term exceeds the DMA term, the estimator classifies this stream as decoder-bound, and with the default overlap flag the total is `max(1, 128) = 128`. Widening the decoder to 16 elements per cycle and 4 runs per cycle changes the two terms to `ceil(128/16) = 8` and `ceil(1/4) = 1`, so the decoder term falls to 8 and the total becomes `max(1, 8) = 8`; disabling overlap makes it `1 + 8 = 9`. Every number in this derivation is a ratio of configured widths — none of it is a measured time.

**Round trip and config mapping.** `tu_compress_for_dma`/`tu_decompress_for_dma` and the adaptive/bitmap entry points round-trip exactly (verified for all tested patterns), and `tu_compress_config_from_tu_config` maps the full config's compression fields into a codec config (`type=4 enabled=1 decoder=1` in the sealed probe). The codec surface reads the full config struct — never the runtime struct.

---

## 13.6 Configuration has one ladder for the weight path, and it stops at the full config

The full config declares both blocks: `weight_compression` (enabled, type string→enum, `rle_epsilon`, `decoder_enabled`, `decoder_overlap_dma`, `decoder_elements_per_cycle`, `rle_runs_per_cycle`, `bitmap_elements_per_cycle`) and `sparsity` (enabled, `structured_2of4`, `unstructured`, `metadata_format`, `decoder_groups_per_cycle`). Validation rejects unknown compression types, unstructured sparsity (not implemented), `enabled` without 2:4, `structured_2of4` without `enabled`, and zero decoder groups — the sealed probe exercises the four sparsity rejection classes (unstructured, `enabled` without 2:4, `structured_2of4` without `enabled`, zero groups), while the unknown-compression-type rejection is covered by source audit.

The decisive configuration fact is the runtime boundary. `tu_config_to_runtime()` copies PE/SRAM/counters/trace/verify/ICC fields only. It drops **every** compression and sparsity field, so the codec mapper and the sparse estimator read the full `tu_config_t` directly. No weight-path field reaches `tu_runtime_config_t`. The shipped JSON declares compression disabled/`none` with the decoder disabled, overlap true, and unit widths; sparsity is fully disabled with one group per cycle. The shipped YAML carries the sparsity defaults but has **no `weight_compression` block at all** — JSON and YAML are not synchronized on the compression surface.

Field-level reachability is uneven within the full config:

- all **eight** compression fields reach `tu_compress_config_from_tu_config()`;
- of the **five** sparsity fields, exactly three — `sparsity_enabled`, `sparsity_2of4`, `sparsity_decoder_groups_per_cycle` — reach `tu_sparsity_2of4_estimate_cycles()`;
- `sparsity_unstructured` is read only by `tu_config_validate()` (to reject it);
- `sparsity_metadata_format` is declared, defaulted, shipped in JSON, and dumped — but never parsed by `tu_config_load_string()` and never read by any module. It is a **dead configuration field**.

The shipped JSON block for the compression surface is:

```json
"weight_compression": {
  "enabled": false,
  "type": "none",
  "rle_epsilon": 0.0,
  "decoder_enabled": false,
  "decoder_overlap_dma": true,
  "decoder_elements_per_cycle": 1,
  "rle_runs_per_cycle": 1,
  "bitmap_elements_per_cycle": 1
}
```

and the sparsity block is:

```json
"sparsity": {
  "enabled": false,
  "structured_2of4": false,
  "unstructured": false,
  "metadata_format": "bitmask",
  "decoder_groups_per_cycle": 1
}
```

Every field in the first block maps to a codec-config member via `tu_compress_config_from_tu_config()`; of the second block, only `enabled`, `structured_2of4`, and `decoder_groups_per_cycle` are consumed by the estimator, `unstructured` is consumed only by validation, and `metadata_format` is never consumed. The YAML file carries the sparsity defaults but omits the compression block entirely — so JSON and YAML disagree on the compression surface, and the YAML-only reader sees sparsity defaults without any codec setting.

The ladder therefore reads:

```text
declared -> parsed -> validated -> full-config consumer
-> runtime-config retention (absent) -> discriminating effect -> calibrated
```

Tusim reaches the full-config consumer rung for both blocks and stops. There is no runtime-config rung for the weight path.

---

## 13.7 Which tests prove what, and which numbers are historical

The focused tests are fail-closed and their membership differs:

| Test | Result in canonical run | Aggregate `make test`? |
|---|---:|---|
| `test-int-quant` | 14/14 | yes |
| `test-sparsity` | 27/27 | yes |
| `test-compress` | 24/24 | no — standalone |
| `test-weight-compression-sweep` | runs, linked | no — standalone |
| `test-sparsity-sweep` | runs, linked | no — standalone |
| `test_int8_sweep.c` | not executed | no Makefile target at all |

A forced mutation of the sparsity decoder-bottleneck assertion flips the strict comparison and the suite drops from 27 passed to 26 run / 25 passed / 1 failed with a nonzero exit — proving the harness gate rather than assuming it. The linked sweeps execute against the cmodel: the weight-compression sweep prints per-profile raw/RLE/bitmap/adaptive sizes and cycle totals (including the all-zero case where adaptive cycles exceed raw), and the sparsity sweep prints dense-versus-2:4 totals with decode rates 1/4/16.

Historical reports — `int8-quantization-throughput.md`, `test_int8_sweep.c`, and the exploration documents — are analytical or earlier records whose tables must be re-derived from the pinned code rather than quoted as current executable evidence. The audit subjects them to corrective predicates (e.g., “payload-only measurements overstate compression speedups”) instead of copying their numbers.

---

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

All of these are retained as config-selectable alternatives in the pinned code (selected through the full config, never through the runtime struct); none is presented as a universal winner. Physical decoder area/power, FIFO depth, SRAM conflicts during decode, ISA auto-dispatch of 2:4, and silicon calibration remain unmodeled.

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

---

## 13.11 Failure modes

1. **Payload-only reasoning.** Quoting encoded-size reductions as latency improvements without the decoder model; the decoder estimator exists precisely to bound this substitution.
2. **Integrated-pipeline wording.** Describing the quantizer, 2:4 module, and codecs as one weight-compression engine; the caller inventory proves they are separate surfaces.
3. **Runtime-reachability assumption.** Assuming parsed `weight_compression`/`sparsity` fields reach `tu_runtime_config_t`; the conversion function drops all of them.
4. **Dead-field promotion.** Treating `sparsity_metadata_format` as effective configuration; it is never parsed and never read.
5. **Unsaturating accumulation.** Using the INT8 dot product or MMA tile on very long maximal-magnitude vectors and reading the INT32 result as correct.
6. **Decoder-bound as physical proof.** Interpreting `decoder_bound` as a measured bottleneck; it is a comparison of two analytical estimates.
7. **Historical-table import.** Copying sweep tables from exploration reports or `test_int8_sweep.c` instead of re-deriving them from the pinned code.

---

## 13.12 Summary

The weight path in Tusim is three adjacent surfaces — numeric conversion, structured sparsity, and lossless codecs — each with its own byte formats, consumers, and analytical estimators. The chapter's central lessons are:

1. **Byte savings are not latency savings** without a decoder model; the decoder estimator exists precisely to bound that substitution.
2. **The 2:4 advantage is decoder-provisioning-dependent** and can reverse direction (2.25× slower at one group per cycle, 1.72× faster at 16 for the same narrow-N workload).
3. **RLE expands on alternating data** (776 B vs 256 B raw) and bitmap wins on scattered zeros; adaptive selection is strict-smaller with a raw fallback.
4. **`tu_config_to_runtime()` drops every weight-path field**, and one sparsity field (`sparsity_metadata_format`) is dead; all eight compression fields and three of five sparsity fields reach their full-config consumers.
5. **The INT8 and 2:4 MMA helpers are standalone, not integrated**, with no direct-MMA caller and no codec→decoder→MMA feed.
6. **No weight-path quantity is calibrated**; the sealed probe fixes exact bytes and deterministic estimates, and the reader labels every number by its evidence rung.

---

## Review questions

1. A 128-element FP16 tensor is all zeros. Give the dense, RLE, and 2:4 packed byte counts, and say which codec wins. Repeat the packed-size formula for the same tensor at INT8 and UINT4 element sizes.
2. A 128-element FP16 tensor alternates `0,1,0,1,...`. Why does RLE expand, and which adaptive codec would the implementation select?
3. On the default 16×16/256-bit configuration, why does 512×16×512 2:4 at one group per cycle produce 77,312 cycles while 16 groups per cycle produce 19,971?
4. Which `weight_compression` and `sparsity` fields reach `tu_runtime_config_t`, and which sparsity field is never parsed at all?
5. What does `decoder_bound` mean, and what must it never be called?
6. Why are the INT8 MMA tile and the 2:4 MMA helpers not reachable from the direct MMA path, and what are the two arithmetic hazards of the quantizer?
7. Which of `test-int-quant`, `test-sparsity`, `test-compress`, and `test_int8_sweep.c` run in aggregate `make test`, and why does that distinction matter?
8. The weight sweep shows adaptive cycles exceeding raw for all-zero data. Does that contradict the codec's purpose? Explain.
9. A design claims "2:4 makes our GEMM twice as fast." What three pieces of evidence are missing?
10. Why must the 2:4 estimator's `max(sparse_compute, decode)` term be called an assumption rather than a schedule?

### Review-question answer key

1. Dense 256 B; RLE 14 B (8 header + one run); 2:4 `32×5 = 160` B. RLE wins on the all-zero tensor. At INT8 element size the 2:4 pack is `32×(2×1+1) = 96` B (versus 128 dense); at UINT4 the packed-size formula does not apply (UINT4 is a quantization surface, not a 2:4 pack), and the byte count is `ceil(128/2) = 64` B for the packed-nibble buffer.
2. RLE produces 128 runs → `8 + 128×6 = 776` B, larger than raw 256 B; the three-way adaptive selector would pick **bitmap** (152 B = 8 header + 16 bitmap bytes + 64×2 value bytes), strictly smaller than raw. The claim that "bitmap also exceeds raw here" is false: bitmap beats raw for any tensor with up to roughly 115 nonzeros at n=128. The two-way `adaptive_rle` mode is the one that would fall back to raw.
3. Decode cycles are `ceil(groups/rate)`; at rate 1 the 65,536 decode cycles dominate `sparse_dma + max(compute, decode)`, at rate 16 they shrink to 4,096 and compute (8,195) dominates, flipping the direction.
4. None. `tu_config_to_runtime()` copies only PE/SRAM/counters/trace/verify/ICC fields. `sparsity_metadata_format` is never parsed by `tu_config_load_string()` and never read.
5. `decoder_bound = decode_cycles > dma_cycles` — a classification of which analytical term dominates; never a physical bottleneck proof or measured latency.
6. The exact C-caller inventory shows both the INT8 tile and the 2:4 MMA helpers (`mma_fp16`, `mma_tiled`) are called only by their own modules and focused tests; `tu_cmodel.c` never calls any of them. Hazards: `(int32_t)` conversion before clamp (UB out of range / non-finite) and unsaturating INT32 accumulation.
7. `test-int-quant` and `test-sparsity` are in `make test`; `test-compress` and both sweeps are standalone; `test_int8_sweep.c` has no Makefile target. Aggregate membership is a reachability fact, not a correctness certificate.
8. No. Adaptive byte selection minimizes stream size, not cycles; the all-zero row shows the decoder model exposing that a tiny stream can still be decode-bound. It is evidence against payload-only reasoning.
9. The workload and tensor shapes; the decoder provisioning (groups per cycle, overlap) and the resulting cycle totals; and a calibration reference (there is none at this pin).
10. The `max` models decode overlapping compute under a named assumption; it is not a queue, an arbitration result, or a schedule, and omitting queues alone does not establish a bound.

---

## Design exercises

1. **Probe a mixed tensor.** Build a 256-element FP16 tensor with 30% scattered zeros and 20% clustered zeros. Compute RLE, bitmap, and adaptive sizes by hand, then verify with `tu_compress_rle`, `tu_compress_bitmap`, and `tu_compress_adaptive` in a small C program against the pinned library.
2. **Decoder sweep.** Using `tu_sparsity_2of4_estimate_cycles` with a fixed 512×512×512 workload, sweep `decoder_groups_per_cycle` over 1, 4, 16, and 64, and report the crossing point where 2:4 total becomes smaller than dense. State every assumption.
3. **Configuration audit.** Parse a JSON with `weight_compression.type=adaptive` and `sparsity.enabled=true, structured_2of4=true`; confirm the fields land in the full config, then confirm `tu_config_to_runtime()` drops them. Also confirm `sparsity_metadata_format` parses nowhere.
4. **Dead-field check.** Grep the pinned tree for every reader of `sparsity_metadata_format` outside `config.c`, and write one sentence on what the audit would need to add to predicate it (see the additional-observation note in the [skeptical review dispositions](../../notes/chapter-13-skeptical-review-dispositions.md)).
5. **Reject-the-claim.** A colleague says "bitmap always beats RLE." Construct one tensor where RLE wins, one where bitmap wins, and one where raw wins, with exact byte counts.
6. **Aggregate-membership map.** From the pinned Makefile, list which of the chapter's tests and sweeps are in `make test`, which are standalone, and which source file has no target; explain what each category can and cannot prove.
7. **INT8 boundary.** Determine the smallest `|v|/scale` ratio at which `tu_fp32_to_int8`'s conversion-before-clamp can overflow `int32_t` for a positive finite `scale`, and explain why the chapter forbids executing that case.
8. **Fidelity labeling.** Take one row of the weight-compression sweep output and rewrite it as a sentence that names the byte effect, the decoder assumption, and the calibration status.

---

## Primary references

- [KWO19] Kwon, Chatarasi, Pellauer, Parashar, Sarkar, and Krishna, "Understanding Reuse, Performance, and Hardware Cost of DNN Dataflow," MICRO 2019 — data-centric mappings and analytical reuse/cost models; vocabulary for mapping-dependent cost, not validation of Tusim equations. Full entry in [references/foundations.md](../../references/foundations.md#kwo19-maestro).
- [PAR19] Parashar et al., "Timeloop: A Systematic Approach to DNN Accelerator Evaluation," ISPASS 2019 — separating workload shape, architecture, mapping, and constraints; model-based estimates are not silicon-equivalent. Full entry in [references/foundations.md](../../references/foundations.md#par19-timeloop).
- [CHE16] Chen, Emer, and Sze, "Eyeriss: A Spatial Architecture for Energy-Efficient Dataflow for Convolutional Neural Networks," ISCA 2016 — row-stationary dataflow and hierarchical data movement as design context for weight delivery; no numeric transfer to Tusim. Full entry in [references/foundations.md](../../references/foundations.md#che16-eyeriss).
- [GEN21] Genc et al., "Gemmini: Enabling Systematic Deep-Learning Architecture Evaluation via Full-Stack Integration," DAC 2021 — full-stack evaluation context showing that software/runtime choices materially change accelerator performance. Full entry in [references/foundations.md](../../references/foundations.md#gen21-gemmini).
- [JOU17] Jouppi et al., "In-Datacenter Performance Analysis of a Tensor Processing Unit," ISCA 2017 — deterministic host-controlled execution and on-chip storage context; silicon results do not transfer numerically to Tusim. Full entry in [references/foundations.md](../../references/foundations.md#jou17-production-tpu-analysis).

All Tusim-specific claims in this chapter are sourced from the pinned commit and the sealed canonical-v8 evidence run; the references above supply vocabulary and design obligations only.
