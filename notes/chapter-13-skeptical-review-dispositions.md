# Chapter 13 Skeptical Review Dispositions

- **Chapter boundary:** Weight Streams: Quantization, Structured Sparsity, and Compression
- **Tusim pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Review stage:** pre-draft evidence/scope gate
- **Method:** adversarial source, caller, configuration, Makefile, probe, and backlog review by an independent reviewer over the sealed canonical-v8 bundle
- **Current canonical target:** `experiments/runs/ch13-weight-streams/20260803-ch13-canonical-v8`

## Gate question

Can a skeptical reader use the planned evidence to distinguish, for the weight-path family, byte effects (encoded sizes, round trips), deterministic analytical estimates (payload DMA cycles, decode cycles, totals), configured-state reachability (which fields reach which consumer, and the `tu_config_to_runtime()` drop), decoder-throughput assumptions, and calibration status — without silently importing stronger claims from headers or exploration docs?

## Dispositions

### R1 — “One integrated weight pipeline” implication

**Finding:** The three adjacent surfaces (quantizer, 2:4 module, codecs) could be read as one coherent codec→decoder→MMA pipeline.

**Disposition:** **Resolved.** C13.33 states the unified feed is not implemented and is BLOCKED in the implementation backlog (verified in `docs/exploration/IMPLEMENTATION_BACKLOG.md`); C13.7/C13.13/C13.25, the framing reader-decision #1, and the audit's `direct-mma-avoids-*` negative gates all reinforce the separation. The C-caller inventories prove the MMA helpers, dot product, and encode entry points have no direct-MMA caller.

### R2 — “Decoder-bound” as physical bottleneck proof

**Finding:** The `decoder_bound` flag could be over-read as a measured hardware bottleneck.

**Disposition:** **Resolved.** C13.23's required wording and the audit fidelity label classify it as an estimate property; the flag is set purely as `decode_cycles > dma_cycles` in `weight_compress.c`. The sweeps print analytical-fidelity disclaimers. Test titles are not claim sources.

### R3 — Byte/DMA reduction as latency or energy improvement

**Finding:** Encoded-size wins could be translated directly into latency or energy gains.

**Disposition:** **Resolved.** C13.34 (“payload reduction ≠ latency reduction”) plus the decoder-doc predicates guard the substitution. The sparsity sweep's speedup column includes decode cycles, and the weight sweep even shows adapt cycles exceeding raw in some regimes — evidence against the substitution, retained in the chapter.

### R4 — Runtime-config reachability overclaim; dead `sparsity_metadata_format` field

**Finding:** The blanket “drops every compression and sparsity field” claim is true, but field-level reachability was not fully enumerated. `sparsity_metadata_format` is declared, defaulted, shipped in JSON, and dumped — but never parsed by `tu_config_load_string()` and never read by any consumer (dead field). `sparsity_unstructured` is read only by validation. Only three of five sparsity fields reach the 2:4 estimator.

**Disposition:** **Resolved by qualification.** C13.27 now carries the full field-level reachability statement; framing in-scope #4 now reads “5 declared, 4 parsed, 3 estimator-consumed, 1 unparsed dead field.” No claim of runtime reachability was made anywhere; the automated gates cover the drop structurally.

### R5 — `test_int8_sweep.c` classification

**Finding:** The analytical sweep could be mistaken for executable cmodel evidence.

**Disposition:** **Resolved.** Verified zero Makefile references (`int8_sweep` appears nowhere in the Makefile), “No cmodel dependency — pure analytical cycle model” in its header, and no cmodel includes. C13.29/C13.30 classify it as source-present historical analytical evidence; the manuscript will phrase it as “no Makefile target; not executed in the canonical run.”

### R6 — Aggregate membership

**Finding:** Could `test-compress` or the sweeps be assumed part of `make test`?

**Disposition:** **Resolved.** Makefile lines 524–528 include `test-int-quant` and `test-sparsity`; `test-compress` and both sweeps are standalone. All audit predicates and the canonical run's 14/14, 27/27, 24/24 focused results match C13.29.

### R7 — Exact probe values vs source equations

**Finding:** Probe values could be stale or mis-derived.

**Disposition:** **Resolved.** The reviewer hand-recomputed every spot check from pinned source; all match the sealed transcript exactly, including `est128 dense_total=12291 sparse_total=7811`, `estNarrow 34307/77312`, `estWide 19971`, `est_rle dma=1 decode=128 total=128 bound=1`, `est_serial total=9`, RLE 14 B, alternating 776 B, bitmap 110 B, adaptive codec=2 size=126, nibble 0x5A, dot 32, MMA tile 19/22/43/50, prune masks 0x5/0x9, packed 160 B. C13.20 upgraded to `verified`.

### R8 — Arithmetic and overflow hazards

**Finding:** `tu_fp32_to_int8`/`tu_fp32_to_uint4_nibble` cast `(int32_t)scaled` before the clamp — C11 UB for out-of-range or non-finite scaled values. `tu_int8_dot_product` is unsaturating INT32 and can overflow on very long vectors. Estimator totals are uint64 and unguarded at extreme uint32 dimensions; `tu_compress_get_ratio` multiplies in uint32 before widening.

**Disposition:** **Resolved by qualification.** C13.4 strengthened: callers must keep `scale` finite, positive, and such that `roundf(v/scale) + zero_point` lies within `int32_t` range; the conversion-before-clamp is stated as UB for out-of-range/non-finite inputs. C13.7 qualified: INT32 accumulation is unsaturating and may overflow on very long vectors. The chapter will keep all executed shapes within tested bounds and state that extreme-dimension totals are unguarded.

### R9 — Framing-plan overclaim precision

**Finding:** In-scope #6 named only three validation rejection classes; the probe and C13.26 exercise four. The audit report's “first sealed attempt is canonical” wording was imprecise given retained v1–v7 attempts.

**Disposition:** **Resolved.** In-scope #6 now lists all four rejection classes (`unstructured sparsity`, `enabled` without 2:4, `structured_2of4` without `enabled`, zero decoder groups). The audit report now names v8 (`ff0bdc10`) as the canonical seal and states all earlier attempts are retained immutable history with reseal only through the same fail-closed gates.

### R10 — Additional observation: sparsity predicate coverage

**Finding:** The source-audit sparsity predicates cover three of five fields; `sparsity_unstructured` and `sparsity_metadata_format` are not directly predicated.

**Disposition:** **Non-blocking, noted.** The blanket drop is enforced structurally by the converter slice and by the runtime-struct exclusion predicates. If a future edition hardens the audit, it should extend the field loops to all eight compression and five sparsity fields; this does not affect the current seal.

## Verdict

**Current verdict:** **PASS.** The gate question answers affirmatively: byte effects, analytical estimates, configured-state reachability (including the dead field), decoder assumptions, and calibration absence are all distinguishable from the sealed evidence without importing stronger claims. All required changes were additive wording qualifications; the sealed canonical-v8 evidence stands unchanged.
