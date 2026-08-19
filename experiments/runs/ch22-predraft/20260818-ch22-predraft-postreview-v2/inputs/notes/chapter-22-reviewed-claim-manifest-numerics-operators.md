# Chapter 22 read-only claim extraction

## Register conventions

- **Disposition:** `retained`, `qualified`, `superseded`, `rejected`, `blocked`.
- **Objective tags:** `q` quantified, `d` directional, `u` unknown.
- **Exactly one metric domain per claim:**
  - `codec_byte_and_estimator_cycles`
  - `precision_conversion_error_metric`
  - `local_formula_cycles`
  - `operator_analytical_cycles`
  - `sram_stall_returns`
  - `noncycle_functional_or_structure`
- **Fields:** `OBJ` objective tags; `MD` missing decisive dimensions; `ALT` materially distinct alternatives; `SAFE` safe replacement; `REV` evidence that would reopen/reverse the disposition.
- Report-level question/workload/axes/controls/producer and binding limitation apply to every claim in that report unless overridden.
- **Current book evidence surfaces:**
  - `E13` = `notes/chapter-13-source-and-claim-ledger.md`, SHA-256 `1ab6edad3c89e82659e6939dd0931ee74f529c114193f19def403545a0f293ca`.
  - `E14` = `notes/chapter-14-source-and-claim-ledger.md`, SHA-256 `06812b971eea1347ef8ee29791f4b09494116e04c09dbfde7c573b52fa390be6`.
  - `E21` = `notes/chapter-21-source-and-claim-ledger.md`, SHA-256 `57a29749614d59b5fe5f58e5202563fb000d4f112aeffdfc6532cd1904f4a416`.
  - `ESA` = `source-audit.md`, SHA-256 `bf558f6f869b864a9265b7484fb1cb4cda914170c39cebf7c531d425048471e8`.

---

## A. Numerics and weight representation

### N1. `bitmap-weight-compression.md`

**Hash:** `5232b44ae6089b8da5e56c90a91747e38ba609edeef2c0e9567bf481526bfc84`  
**Decision context:** Q=which raw/RLE/bitmap/adaptive payload suits FP16 zero placement; ALT=`none`, `rle`, `adaptive_rle`, `bitmap`, `adaptive`; W=4,096 FP16 weights; axes=zero fraction and random/clustered placement; controls=32-B/cycle DMA, epsilon 0, deterministic placement; objective=exact bytes and payload-DMA estimates; producer=linked codec/sweep, bytes plus `ceil(bytes/32)` cycles.  
**Binding limitation:** “payload reduction ≠ latency reduction” (`E13:C13.34`); “byte equality and cycle estimates require separate evidence” (`E13:C13.36`).

1. **N1.1 — Exact bitmap format.** `L41–46`, heading `L35: "## Bitmap wire format"`; quote: “Occupancy bitmap | `ceil(elements / 8)` bytes” and “Packed nonzero FP16 bit patterns | `2 * nonzero_count` bytes.” **Disposition:** retained; owner `E13:C13.19/C13.21`; domain=`codec_byte_and_estimator_cycles`; OBJ traffic:q, correctness:q; MD physical alignment/bursts; ALT raw/RLE; SAFE exact portable byte-format claim only; REV source-format or round-trip failure.
2. **N1.2 — Random-sparse payload benefit.** `L79`, heading `L60: "## Measured trade-off matrix"`; quote: “For random 10–90% zeros, bitmap reduces measured payload cycles by 3.5–82.8% versus raw and by 66.7–76.3% versus RLE.” **Disposition:** qualified; owner `E13:C13.31/C13.32/C13.34`; domain=`codec_byte_and_estimator_cycles`; OBJ traffic:q, latency:u; MD decoder, FIFO, bursts, energy; ALT raw/RLE; SAFE bounded payload-byte/DMA-equation result for the named matrix; REV changed distribution, bus width, framing, or decoder profile.
3. **N1.3 — Placement reversal.** `L79`; quote: “clustered rows strongly favor RLE (6–45 adaptive cycles), and an actually dense, unique tensor selects raw.” **Disposition:** qualified; owner `E13:C13.20/C13.31`; domain=`codec_byte_and_estimator_cycles`; OBJ traffic:q, control:d; MD tensor distributions outside fixture; ALT RLE/raw; SAFE codec choice is placement-dependent under byte-minimum selection; REV different values/runs or profile-aware selection.
4. **N1.4 — Adaptive-frame cost.** `L79`; quote: “The 16-byte adaptive frame occasionally adds one bus beat but prevents selecting a larger candidate.” **Disposition:** retained; owner `E13:C13.17/C13.20`; domain=`codec_byte_and_estimator_cycles`; OBJ traffic:q; MD descriptor/frame-fetch latency; ALT explicit codec without frame; SAFE exact selection/frame bound, not an elapsed-time guarantee; REV format/header or tie policy changes.
5. **N1.5 — Decoder knee.** `L115`, heading `L113: "## Follow-up status and remaining model gap"`; quote: “1–8 output/cycle decoders are slower than raw here, 16/cycle generally breaks even, and 32/cycle is required for measured latency gains.” **Disposition:** qualified; owner `E13:C13.22/C13.23/C13.32`; domain=`codec_byte_and_estimator_cycles`; OBJ estimated latency:q, area/power:u; MD calibration, SRAM ports, backpressure, compute overlap; ALT serial/balanced/wide/extra-wide/raw; SAFE decoder-estimator sensitivity for dense reconstruction; REV calibrated decoder or direct compressed-domain feed.

### N2. `int8-quantization-throughput.md`

**Hash:** `f647f7a2b260133cd789bc049f3076c04a8a05ee2171a795385781a42f001958`  
**Context:** Q=analytical INT8-versus-FP16 GEMM throughput; ALT FP16/INT8; W=listed GEMMs and PE shapes; axes=M/N/K, PE geometry, element width; controls=WS, depth 2, 32 B/cycle; producer=standalone WS formula; units=cycles, speedup, stated TOPS.  
**Binding limitation:** “retain as historical analytical orientation only” (`E13:C13.30`); direct MMA hardcodes FP16 W/A and FP32 psum/O (`ESA#32`).

6. **N2.1 — Reported 3–33% range.** `L30`, heading `L28: "## Key Finding"`; quote: “INT8 quantization delivers ~3–33% speedup over FP16, entirely from DMA bandwidth savings.” **Disposition:** qualified; owner `E13:C13.30`; domain=`local_formula_cycles`; OBJ estimated latency:q; MD executable INT8 route, output conversion, accuracy; ALT FP16; SAFE the local spreadsheet produces 1.03–1.33× from element-byte substitutions; REV linked INT8 execution or different output representation.
7. **N2.2 — Small-K boundary.** `L32`; quote: “The speedup is maximized for small-K workloads (DMA-bound, K ≤ 64)”; **Disposition:** qualified; owner `E13:C13.30/C13.32`; domain=`local_formula_cycles`; OBJ estimated latency:q; MD alternative buses/overlap; ALT FP16; SAFE a grid-local formula trend, not a physical roofline; REV changed DMA width, overlap, or compute path.
8. **N2.3 — PE/aspect sensitivity.** `L54`; quote: “The 128×16 aspect ratio shows the best INT8 speedup (1.32×).” **Disposition:** qualified; owner `E13:C13.30`, `E21:C21.9`; domain=`local_formula_cycles`; OBJ estimated latency:q; MD effective dataflow route, placement, area; ALT six PE shapes; SAFE local formula ordering only; REV linked estimator or route discriminator gives another ordering.
9. **N2.4 — Hardware recommendation.** `L65–68`, heading `L63: "## Recommendation"`; quote: “INT8 quantization is worth implementing in hardware when” followed by the three conditions. **Disposition:** rejected; owner `E13:C13.30/C13.35`; domain=`local_formula_cycles`; OBJ latency:q, accuracy:u, area/power:u; MD integrated path, calibration, accuracy, hardware cost; ALT omit INT8/standalone conversion; SAFE keep as a future hypothesis conditional on those missing dimensions; REV integrated, calibrated INT8 path plus application accuracy and cost.
10. **N2.5 — Transformer default guidance.** `L70`; quote: “INT8 support should NOT be a default requirement. It's a nice-to-have for inference-focused designs targeting transformer FFN layers.” **Disposition:** rejected; owner `E13:C13.30`, `ESA#32`; domain=`local_formula_cycles`; OBJ product choice:d; MD representative workloads and accuracy; ALT default/optional/no INT8; SAFE no default choice follows from this analytical report; REV workload-weighted integrated evaluation.

### N3. `precision-sweep-gemm128.md`

**Hash:** `37bdadfa91fe2148640c0bca430dbb8d477112854914bcde865840e34881fa57`  
**Context:** Q=precision effect on formula GFLOPS; ALT FP16/BF16/INT8/FP8/TF32; W=128×128×K, K=16–4096; controls=16×16 WS, depth 2, 32 B/cycle, 1 GHz; producer=element-width spreadsheet; units=bytes, formula cycles, mislabeled GFLOPS.  
**Binding limitation:** “Element-width spreadsheet rows do not establish an FP8 MMA throughput path, numerical acceptability, or runtime selection” (`D22F11`/`ESA#32`).

11. **N3.1 — INT8 O-buffer lever.** `L30`, heading `L20: "## Element Size Breakdown"`; quote: “INT8's O-buffer stores FP32 accumulators (4 bytes), not INT8 (1 byte).” **Disposition:** qualified; owner `ESA#32`, `E13:C13.30`; domain=`local_formula_cycles`; OBJ traffic:q; MD actual INT8 output/store route; ALT quantized output, FP16/FP8 output; SAFE spreadsheet sensitivity to assumed O-byte width; REV implemented output conversion or different store contract.
12. **N3.2 — INT8 small-K reversal.** `L127`, heading `L125: "## Key Finding"`; quote: “making it slower than both FP16 and FP8 at K ≤ 128.” **Disposition:** qualified; owner `E13:C13.30`; domain=`local_formula_cycles`; OBJ estimated latency:q; MD integrated precision routes; ALT five precisions; SAFE local equation reversal under the report’s byte assignments; REV actual precision-specific MMA/DMA.
13. **N3.3 — FP8 universal champion.** `L129`; quote: “FP8_E4M3 is the unambiguous throughput champion at all K values.” **Disposition:** rejected; owner `ESA#31/#32`; domain=`local_formula_cycles`; OBJ throughput:q, accuracy:u; MD executable FP8 route, numerical fitness, converter defects; ALT all five types; SAFE FP8 has the smallest spreadsheet total on this grid only; REV linked, correct FP8 execution and application-quality evidence.
14. **N3.4 — K=16 spread.** `L132–135`; quote: “Precision spread = 63.8%” and “FP8 is 5.8% faster than FP16.” **Disposition:** qualified; owner `E21:C21.9`, `ESA#32`; domain=`local_formula_cycles`; OBJ estimated latency:q; MD executable route; ALT five rows; SAFE retain exact local cycle comparisons, not the printed GFLOPS unit; REV formula correction or linked execution.
15. **N3.5 — K=4096 asymptote.** `L138–140`; quote: “Precision spread = 33.6%” and “TF32 asymptotes at 33.7% DMA.” **Disposition:** qualified; owner `E21:C21.9`; domain=`local_formula_cycles`; OBJ estimated latency:q; MD overlap/cache/reuse; ALT five precisions; SAFE local byte-term sensitivity; REV changed movement model.
16. **N3.6 — Training versus inference prescription.** `L142`; quote: “For training workloads (K > 256), precision choice should optimize for accuracy, not throughput.” **Disposition:** rejected; owner `ESA#31/#32`; domain=`local_formula_cycles`; OBJ accuracy:u, throughput:q; MD any training/application evidence; ALT precision choices; SAFE no training recommendation follows from element widths; REV end-to-end training-quality and throughput study.
17. **N3.7 — “No additional hardware complexity.”** `L142`; quote: “FP8 provides a meaningful throughput advantage over FP16 with no additional hardware complexity beyond the precision converters already present in the cmodel.” **Disposition:** rejected; owner `ESA#31/#32`; domain=`noncycle_functional_or_structure`; OBJ area/control:u; MD FP8 datapath, accumulators, validation, physical cost; ALT FP16/FP8; SAFE converters alone do not establish an FP8 MMA path or equal complexity; REV integrated hardware design and cost.

**Arithmetic contradiction:** the table’s “GFLOPS at 1 GHz” is off by **1000×**. For K=16 FP8, `2·128·128·16 / 2208 = 237.449` GFLOP/s, not `0.24`; 16×16 peak is **512 GFLOP/s**, not `0.51`. The 63.8% spread is consistent with exact cycle ratio `3616/2208−1`, but not with the rounded displayed `0.24/0.14` values.

### N4. `rounding-mode-accuracy-sweep.md`

**Hash:** `0e91d7d02835c88abf7157b1f729c6f20539bcd7fcb8fc9cd4a20602096d1dad`  
**Context:** Q=RNE/RTZ/stochastic conversion error; W=128×128×256 random fixture; axes=rounding mode and stochastic seed; controls=FP16 W/A conversion, FP64 golden, fixed data seeds; producer=linked sweep; units=max/mean absolute and relative conversion-propagated error.  
**Binding limitation:** “fixed-seed replay is one deterministic conversion vector; changed-seed output is not an independent workload sample, an unbiasedness proof, training evidence, or application-accuracy validation” (`E21:C21.4`).

18. **N4.1 — Exact bounded error rows.** `L22–29`, heading `L20: "## Results"`; quote: “RNE … 5.79×10⁻³”, “RTZ … 1.48×10⁻²”, “Stochastic … 8.08×10⁻³.” **Disposition:** qualified; owner `E21:C21.4`; domain=`precision_conversion_error_metric`; OBJ conversion error:q; MD broader data/workloads; ALT three modes; SAFE exact named-fixture observations; REV corrected harness or different matrix/seed.
19. **N4.2 — RTZ 2.6×.** `L33`, heading `L31: "## Key Finding"`; quote: “RTZ is 2.6× worse than RNE on both max and mean error.” **Disposition:** qualified for ratio, rejected for cause; split here to ratio only; owner `E21:C21.4`; domain=`precision_conversion_error_metric`; OBJ conversion error:q; MD application accuracy; ALT RNE/RTZ; SAFE 2.6× on this converted-input fixture; REV broader fixture reverses ratio.
20. **N4.3 — Accumulation-cause explanation.** `L33`; quote: “The systematic downward bias … compounds across the K=256 accumulation dimension.” **Disposition:** rejected; owner `E21:C21.4`; domain=`noncycle_functional_or_structure`; OBJ causality:d; MD accumulator/store-rounding reachability; ALT input-conversion explanation; SAFE the mode reaches FP32→FP16 W/A conversion, not per-accumulation rounding; REV discriminator proving accumulator-stage mode effect.
21. **N4.4 — Stochastic 1.4× fixture result.** `L35`; quote: “Stochastic rounding is 1.4× worse than RNE but shows variance across seeds.” **Disposition:** qualified; owner `E21:C21.4`; domain=`precision_conversion_error_metric`; OBJ conversion error:q; MD sample distribution; ALT two stochastic seeds/RNE; SAFE bounded seed-specific conversion result; REV statistically powered replay.
22. **N4.5 — Unbiased/convergence/training claims.** `L35`; quote: “it's unbiased in expectation, meaning repeated runs would converge to RNE-level accuracy.” **Disposition:** rejected; owner `E21:C21.4`; domain=`precision_conversion_error_metric`; OBJ bias/accuracy:u; MD expectation experiment and training; ALT stochastic/RNE; SAFE no unbiasedness or convergence proof is present; REV preregistered multi-seed statistics and application study.
23. **N4.6 — No catastrophic error.** `L37`; quote: “No mode produced catastrophic error (>0.5 absolute).” **Disposition:** qualified; owner `E21:C21.4`; domain=`precision_conversion_error_metric`; OBJ conversion error:q; MD adversarial ranges and applications; ALT all modes; SAFE true only for the named random fixture/tolerance; REV counterexample.
24. **N4.7 — RNE inference/stochastic training prescription.** `L41–43`, heading `L39: "## Design Implication"`; quotes: “use RNE” and “stochastic rounding becomes interesting.” **Disposition:** inference recommendation rejected; training decision blocked; owner `E21:C21.4`; domain=`precision_conversion_error_metric`; OBJ application accuracy:u, hardware cost:u; MD application metrics, PRNG cost, statistical evidence; ALT RNE/RTZ/stochastic; SAFE open design decision; REV application-level training/inference evidence.

### N5. `structured-2of4-sweep.md`

**Hash:** `25299480d42a360b1ea20371d220b3bd2536d576fe573e36fbed65c0098dde28`  
**Context:** Q=when 2:4 beats dense and needed decoder width; W=five GEMM shapes; axes=shape and groups/cycle; controls=16×16, FP16 W/A, FP32 O, serialized DMA, decode/compute max; producer=linked analytical estimator; units=bytes and estimated cycles.  
**Binding limitation:** “deterministic analytical equations under named assumptions; DMA serialized; decode overlaps compute” (`E13:C13.15`).

25. **N5.1 — Exact packed weight reduction.** `L21`; quote: “5 bytes per four values versus 8 bytes dense (37.5% reduction, not 2x compression).” **Disposition:** retained; owner `E13:C13.11/C13.15`; domain=`codec_byte_and_estimator_cycles`; OBJ traffic:q; MD alignment/burst waste; ALT dense; SAFE exact packed-format byte ratio; REV format change.
26. **N5.2 — Estimator rows and crossover.** `L25–32`, heading `L23 table`; quote: “512x16x512 … 1 … 0.444x” and at 4/16 “1.218x / 1.718x.” **Disposition:** qualified; owner `E13:C13.15/C13.16`; domain=`codec_byte_and_estimator_cycles`; OBJ estimated latency:q; MD calibration/ports; ALT dense and 1/4/16-group decoders; SAFE named estimator crossover; REV changed decoder or workload.
27. **N5.3 — Not universally faster.** `L36`, heading `L34: "## Findings and costs"`; quote: “2:4 is not universally faster.” **Disposition:** qualified; owner `E13:C13.15/C13.16`; domain=`codec_byte_and_estimator_cycles`; OBJ estimated latency:q; MD integrated sparse route; ALT dense; SAFE decoder-width/aspect-ratio-dependent estimator conclusion; REV linked sparse execution.
28. **N5.4 — Square/wide 1.42–1.83×.** `L36`; quote: “Square and wide-N cases amortize decode and achieve 1.42-1.83x.” **Disposition:** qualified; owner `E13:C13.15/C13.32`; domain=`codec_byte_and_estimator_cycles`; OBJ estimated latency:q; MD queues/metadata traffic; ALT dense; SAFE local upper-bound estimate; REV omitted costs erase gain.
29. **N5.5 — Energy/area implication.** `L37–38`; quotes: “Area is unquantified” and “cycle speedup must not be used as an energy proxy.” **Disposition:** qualified/open; owner `E13:C13.35`; domain=`noncycle_functional_or_structure`; OBJ area:u, energy:u; MD physical implementation; ALT decoder widths/dense; SAFE no dominance result; REV physical PPA.
30. **N5.6 — Accuracy and software obligations.** `L40–43`; quote: “Task-level accuracy and retraining recovery are unquantified” and “ISA-level automatic dispatch is not yet modeled.” **Disposition:** blocked; owner `E13:C13.33/C13.35`; domain=`noncycle_functional_or_structure`; OBJ accuracy:u, software:u; MD task accuracy and dispatch bridge; ALT dense/explicit sparse API; SAFE preserve both alternatives; REV retraining results and integrated dispatch.

### N6. `weight-compression-rle-sweep.md`

**Hash:** `71fcaa2b2ce6079622309a3a7d2b3a1b7d43a6fe8e27779dd49d21da002267b0`  
**Context:** Q=RLE placement sensitivity and bounded raw fallback; ALT raw/RLE/adaptive-RLE; W=4,096 FP16 weights; axes=placement and zero fraction; controls=32 B/cycle, epsilon 0; producer=linked codec exact bytes plus payload equation.  
**Binding limitation:** “sweep tables are historical summaries; the canonical probe is current evidence” (`E13:C13.31`).

31. **N6.1 — Adaptive bound.** `L51–55`, heading `L38: "## Explicit adaptive frame"`; quote: “`adaptive_bytes <= raw_bytes + 16-byte frame`.” **Disposition:** retained; owner `E13:C13.17/C13.20`; domain=`codec_byte_and_estimator_cycles`; OBJ traffic:q; MD frame fetch; ALT raw/RLE; SAFE exact encoded-byte bound; REV format/tie change.
32. **N6.2 — Original eight-row matrix.** `L69–78`, heading `L67: "## Measured trade-off matrix"`; quote includes “Alternating … 24,584 / 769” and “All zero … 14 / 1.” **Disposition:** superseded by the later 12-row bitmap matrix, but exact historical arithmetic remains; owner `E13:C13.20/C13.31`; domain=`codec_byte_and_estimator_cycles`; OBJ traffic:q; MD bitmap alternative; ALT current five codecs; SAFE historical raw/RLE subset only; REV none unless source changes.
33. **N6.3 — Expansion avoidance.** `L80`; quote: “eliminates the prior 1.55–3.00× RLE traffic expansion … paying one extra 32-byte bus beat.” **Disposition:** qualified; owner `E13:C13.20/C13.34`; domain=`codec_byte_and_estimator_cycles`; OBJ traffic:q; MD decoder; ALT explicit raw/RLE; SAFE payload-only result; REV decode/dispatch cost dominates.
34. **N6.4 — Adaptive not universally better.** `L97`, heading `L95: "### Why all modes remain"`; quote: “Adaptive is not universally ‘better.’” **Disposition:** qualified; owner `E13:C13.34/C13.35`; domain=`noncycle_functional_or_structure`; OBJ control:d, area:u, traffic:q; MD PPA; ALT NONE/RLE/adaptive; SAFE preserve all three alternatives; REV quantified hardware cost.
35. **N6.5 — No model-level accuracy result.** `L120`, heading `L118: "## Physical-model limitations"`; quote: “Epsilon mode is functionally available; no model-level accuracy result is claimed.” **Disposition:** qualified/open; owner `E13:C13.35`; domain=`noncycle_functional_or_structure`; OBJ accuracy:u; MD task evaluation; ALT exact epsilon 0/lossy epsilon; SAFE no accuracy authorization; REV model-level accuracy.

### N7. `weight-decoder-throughput.md`

**Hash:** `8300413868c6418ebdb4742b0c7e4ad8d39dea0680f00b969d38ddc60807357e`  
**Context:** Q=finite decoder effect while reconstructing dense FP16; axes=codec, placement, output/run/bitmap widths, overlap/staged; controls=4,096 weights, 32-B/cycle DMA, exact compression; producer=stream parser plus analytical throughput equations; units=bytes and estimated cycles.  
**Binding limitation:** “decoder widths are configured assumptions, not measured” (`E13:C13.22`).

36. **N7.1 — Exact estimator equations.** `L40–46`, heading `L36: "## Cycle model"`; quote: “overlapped total = `max(dma_cycles, decode_cycles)`” and “staged total = `dma_cycles + decode_cycles`.” **Disposition:** retained; owner `E13:C13.22`; domain=`codec_byte_and_estimator_cycles`; OBJ estimated latency:q; MD queue/calibration; ALT overlap/staged; SAFE deterministic estimator equation; REV implementation change.
37. **N7.2 — Narrow reversal.** `L88`, heading `L86: "## Findings: gains and sacrifices"`; quote: “Serial codecs take 4,096 cycles … 16× raw's 256 cycles.” **Disposition:** qualified; owner `E13:C13.22/C13.23`; domain=`codec_byte_and_estimator_cycles`; OBJ estimated latency:q, area:d; MD physical decoder; ALT serial/balanced/raw; SAFE dense-reconstruction estimator reversal; REV direct feed or measured throughput.
38. **N7.3 — Bus-match break-even.** `L89`; quote: “The wide 16-element/cycle decoder reaches 256 cycles … equal to raw.” **Disposition:** qualified; owner `E13:C13.22`; domain=`codec_byte_and_estimator_cycles`; OBJ estimated latency:q, traffic:q; MD metadata-heavy cases; ALT raw/wide; SAFE break-even under max-overlap model; REV staged execution or port stalls.
39. **N7.4 — Extra-wide gain.** `L90`; quote: “adaptive takes 128 cycles … (2× lower latency than raw), 145–248 cycles on less sparse scattered patterns.” **Disposition:** qualified; owner `E13:C13.22/C13.32`; domain=`codec_byte_and_estimator_cycles`; OBJ estimated latency:q, area/power:u; MD PPA/ports; ALT extra-wide/raw; SAFE regime-specific estimator result; REV physical costs or different distribution.
40. **N7.5 — No universal format/width.** `L91`; quote: “No format or decoder width is universally best.” **Disposition:** qualified; owner `E13:C13.34/C13.35`; domain=`noncycle_functional_or_structure`; OBJ multiobjective:d/u; MD complete objective vector; ALT every codec/profile; SAFE open local choice; REV comparable PPA/latency objectives.
41. **N7.6 — Byte-minimum not latency-optimal.** `L92`; quote: “Byte-minimum adaptive selection remains defensible but is not latency-optimal by construction.” **Disposition:** qualified; owner `E13:C13.20/C13.22`; domain=`codec_byte_and_estimator_cycles`; OBJ traffic:q, estimated latency:q; MD profile-aware selector cost; ALT byte-minimum/profile-aware; SAFE current selector minimizes bytes only; REV hardware-aware selector evaluation.
42. **N7.7 — Direct compressed-domain feed.** `L129`, heading `L127: "## Remaining limits and next question"`; quote: “Do not infer that behavior from this dense reconstruction model.” **Disposition:** blocked; owner `E13:C13.33`; domain=`noncycle_functional_or_structure`; OBJ integration:u; MD shared codec+sparsity+MMA contract; ALT dense reconstruction/direct feed; SAFE future question only; REV executable feed and backpressure contract.

---

## B. Operator irregularity

### O1. `attention-engine-sweep.md`

**Hash:** `9ebaf6ab33c507f25e0ff737b3c2bf04d2dcb4cf296e40b3f62245e25407b720`  
**Context:** Q=PE/workload/dataflow effects on attention; axes=5 arrays, WS/OS/RS, prefill/decode shapes; controls=FP16/FP32, scaled SRAM, auto-tiling; producer=attention stats plus internal MMA/softmax/elementwise calls; units=engine analytical totals.  
**Binding limitation:** arbitrary-input FP16 attention correctness is rejected (`E14:C14.25`) because 4-byte SRAM accesses corrupt 2-byte FP16 staging (`E14:C14.8–C14.10`).

43. **O1.1 — 45/105 valid configurations.** `L18`, heading `L7: "## Config Matrix"`; quote: “Valid: 45 (60 dropped due to SRAM capacity failures or W-buffer overflow).” **Disposition:** qualified; owner `E14:C14.12/C14.13`; domain=`noncycle_functional_or_structure`; OBJ capacity:q; MD defect-free staging; ALT rejected/accepted tiles; SAFE structural acceptance result only; REV corrected tiler/layout.
44. **O1.2 — Decode/prefill characterization.** `L47–50`; quote: “Decode is compute-bound (99%+ util), prefill is DMA-bound (82–91% util).” **Disposition:** blocked; owner `E14:C14.8–C14.11`; domain=`operator_analytical_cycles`; OBJ throughput:q; MD correctness and calibration; ALT compute/DMA investment; SAFE no architecture preference while output is corrupted; REV corrected attention with reproduced stats.
45. **O1.3 — OS 5–36% winner.** `L52–55`; quote: “OS dataflow is strictly faster than WS for attention (5–36% fewer cycles)” and “OS dataflow is the clear winner.” **Disposition:** blocked; owner `E14:C14.8/C14.9`, `E21:C21.3`; domain=`operator_analytical_cycles`; OBJ estimated latency:q; MD correctness/effective route; ALT WS/OS/RS; SAFE performance ordering is unauthorised at this pin; REV correct outputs plus route-specific discriminator.
46. **O1.4 — 32×32 adds 2.7%.** `L57–60`; quote: “only 2.7% faster than 16×16, despite 4× more MACs.” **Disposition:** blocked; owner `E14:C14.8–C14.13`; domain=`operator_analytical_cycles`; OBJ estimated latency:q, capacity:q; MD correct staging and matched buffers; ALT 16×16/32×32/scale O-buffer; SAFE retain as stale report arithmetic; REV corrected matched-capacity sweep.
47. **O1.5 — Aspect ratio penalties.** `L64–69`; quote: “WS=1,128,512 vs OS=299,072 (3.77× slower)” and “OS dataflow is mandatory.” **Disposition:** numerical row blocked; prescription rejected; owner `E14:C14.8/C14.9`; domain=`operator_analytical_cycles`; OBJ estimated latency:q; MD correctness/area; ALT square/tall/OS/WS; SAFE no mandatory route follows; REV corrected sweep.
48. **O1.6 — W-buffer overflow hazard.** `L71–74`; quote: “addr=131070 size=4 max=131072” and “The auto-tiler should reduce tile_n by 1 or enforce a 16-byte safety margin.” **Disposition:** qualified; owner `E14:C14.12/C14.13`; domain=`noncycle_functional_or_structure`; OBJ correctness:q, capacity:q; MD proof of proposed margin; ALT reduce tile/add alignment-aware bound; SAFE retain exact overflow symptom, not the unproved fix; REV end-to-end boundary test.
49. **O1.7 — Universal OS default.** `L79`, heading `L76: "## Conclusion"`; quote: “OS dataflow wins universally. Use it as the default.” **Disposition:** blocked; owner `E14:C14.8/C14.9`; domain=`operator_analytical_cycles`; OBJ architecture choice:d; MD correctness and workloads; ALT WS/OS/RS; SAFE no default can be chosen; REV corrected comprehensive sweep.
50. **O1.8 — “16×16 sufficient” versus KV-bound wording.** `L80`; quote: “16×16 PE is sufficient for decode … More MACs don't help when the workload is KV-bandwidth-bound.” **Disposition:** rejected; owner `E14:C14.8–C14.11`; domain=`operator_analytical_cycles`; OBJ sizing:d; MD correctness and consistent bottleneck definition; ALT PE sizes; SAFE report is internally inconsistent with its earlier “decode is compute-bound”; REV corrected bottleneck accounting.

**Arithmetic/internal contradictions:**  
- `L47` calls prefill “DMA-bound” although its own rows attribute only 15–17% to DMA.  
- `L58` says 32×32 cuts compute by “50K”; the shown OS rows are 239,488→231,808, only **7,680** cycles.  
- `L80` calls decode KV-bandwidth-bound after `L47–48` calls it 99%+ compute-bound.

### O2. `conv-group-sweep.md`

**Hash:** `af46ede7e2d1311ad23415eb397b1ae76dc7db598ab8e4ffb294537ebfc1277c`  
**Context:** Q=group-count effect in analytical im2col+GEMM; W=56², 128→128, 3×3; axes=groups 1–128 and PE 8/16/32; producer=`tu_conv_estimate_cycles`; units=analytical cycles/GOPS.  
**Binding limitation:** conv is a separate uncalibrated analytical API (`E14:C14.5/C14.23`); no non-test caller (`E14:C14.20`).

51. **O2.1 — Table trend/peak.** `L20–27`, heading `L16: "## Results"`; quote: groups=8 on 32×32 gives “790,272 | 1,170.3.” **Disposition:** qualified; owner `E14:C14.5/C14.23`; domain=`operator_analytical_cycles`; OBJ formula throughput:q; MD launch/flush/contention; ALT group counts/PEs; SAFE exact estimator row only; REV equation change.
52. **O2.2 — Depthwise “faster.”** `L29–31`; quote: “Depthwise convolution … is modeled as 1.33× faster than standard conv … on a 32×32 PE array.” **Disposition:** rejected as decision evidence; owner `E14:C14.5/C14.23`; domain=`operator_analytical_cycles`; OBJ formula throughput:q; MD omitted per-group costs; ALT standard/depthwise; SAFE stale model artifact, not hardware performance; REV estimator with omitted costs and executable validation.
53. **O2.3 — Modeling blind spot.** `L56–60`; quote: “This is a modeling blind spot, not a real hardware effect.” **Disposition:** qualified; owner `E14:C14.5/C14.20`; domain=`noncycle_functional_or_structure`; OBJ fidelity:d; MD quantified missing terms; ALT current estimator/improved estimator; SAFE report correctly identifies omitted categories but does not quantify them; REV explicit group overhead model.
54. **O2.4 — Sweet spot condition.** `L71`; quote: “The sweet spot is `k_per_g >= pe_rows`.” **Disposition:** qualified hypothesis, not optimum; owner `E14:C14.5/C14.23`; domain=`operator_analytical_cycles`; OBJ utilization:d; MD real utilization, DMA, PPA; ALT group counts; SAFE candidate boundary for a corrected study; REV corrected model gives another knee.
55. **O2.5 — Dedicated depthwise engine.** `L75`; quote: “For depthwise convolutions, skip the systolic array.” **Disposition:** blocked; owner `E14:C14.20/C14.23`; domain=`noncycle_functional_or_structure`; OBJ architecture:d; MD dedicated-engine implementation/PPA; ALT systolic/dedicated; SAFE preserve as future alternative; REV comparable implementations.
56. **O2.6 — Add per-group overhead.** `L77`; quote: “The cycle model should include a per-group overhead term.” **Disposition:** qualified future hypothesis; owner `E14:C14.5`; domain=`operator_analytical_cycles`; OBJ fidelity:d; MD formula/calibration for term; ALT current/corrected models; SAFE recommended model extension, value open; REV discriminating implementation evidence.

**Arithmetic contradictions:** the heading says “faster on 8×8,” but `L31` uses 32×32 values. The derivation says K=9 gives `kt=2`, while its displayed formula gives `ceil(9/32)=1`. Its stated 128×19,008 compute total (**2,433,024**) exceeds the table’s complete 32×32 depthwise total (**1,655,808**).

### O3. `conv-pool-cascade.md`

**Hash:** `c9a766a326cc2d05506be59a962791eb59ce8829ae09ef57f576d6ea14713c90`  
**Context:** Q=pool share after conv; axes=conv kernel, PE size, pool kernel/type; W=56², 64→128; producer=sum of separate conv and pooling analytical returns; units=local formula cycles/percentage.  
**Binding limitation:** no engine metric is calibrated (`E14:C14.23`); conv and pool have no ordinary non-test pipeline caller (`E14:C14.20`).

57. **O3.1 — 1.3–77% range.** `L64–71`; quote: “Pool overhead is workload-dependent: 1.3% to 77%.” **Disposition:** qualified; owner `E14:C14.5/C14.6/C14.23`; domain=`operator_analytical_cycles`; OBJ local formula share:q; MD common timeline/integration; ALT kernels/PEs/pools; SAFE ratio of two named formulas, not measured block latency; REV executable cascade.
58. **O3.2 — PE amplification.** `L73–75`; quote: “pool overhead grows from 50.7% … to 77.0%.” **Disposition:** qualified; owner `E14:C14.5/C14.6`; domain=`operator_analytical_cycles`; OBJ local formula share:q; MD calibrated PE scaling; ALT 8/16/32; SAFE fixed pool equation divided by changing conv equation; REV integrated overlap/fusion.
59. **O3.3 — Exact 2× Max/Avg.** `L86–88`; quote: “AvgPool always costs exactly 2× MaxPool.” **Disposition:** retained as estimator formula; owner `E14:C14.6`; domain=`operator_analytical_cycles`; OBJ formula cycles:q; MD compute implementation; ALT max/avg; SAFE `ops_per_elem=1/2` equation only; REV source equation changes.
60. **O3.4 — 3×3 versus 2×2.** `L90–92`; quote: “The net is ~2.09×.” **Disposition:** qualified; owner `E14:C14.6`; domain=`operator_analytical_cycles`; OBJ formula cycles:q; MD reuse/vectorization; ALT 2×2/3×3; SAFE local sequential-window equation; REV line-buffered implementation.
61. **O3.5 — Fusion prescriptions.** `L98–100`; quotes: “Fused conv-pool hardware,” “Dedicated pooling unit,” and “effectively zero-cost.” **Disposition:** blocked; owner `E14:C14.20/C14.23`; domain=`noncycle_functional_or_structure`; OBJ latency:d, area/power:u; MD implementation, precision, buffering; ALT three proposals plus separate engines; SAFE bounded next hypotheses; REV executable comparable designs.

### O4. `convolution-kernel-stride-sweep.md`

**Hash:** `a4ab7bb03a944c8ee7afbee17d26761b3fea6e8b800781e46236084ab0b1e009`  
**Context:** Q=kernel/stride/PE scaling; W=56², 128→128; axes=1/3/5/7 kernels, strides 1/2, PEs 8/16/32; producer=`tu_conv_estimate_cycles`; units=analytical cycles/GOPS.  
**Limitation:** separate uncalibrated conv equation (`E14:C14.5/C14.23`).

62. **O4.1 — Larger-kernel formula utilization.** `L44–46`; quote: “171 GOPS” versus “643 GOPS — 3.8× better.” **Disposition:** qualified; owner `E14:C14.5`; domain=`operator_analytical_cycles`; OBJ formula throughput:q; MD hardware utilization; ALT kernels; SAFE estimator’s deep-K amortization trend; REV executable PE utilization.
63. **O4.2 — Stride-2 speedup.** `L55`; quote: “Stride=2 gives ~3.8× speedup … close to the theoretical 4×.” **Disposition:** qualified; owner `E14:C14.5`; domain=`operator_analytical_cycles`; OBJ formula cycles:q; MD memory/layout effects; ALT stride 1/2; SAFE named estimator ratio; REV changed im2col or memory model.
64. **O4.3 — 8×8 “always compute-bound.”** `L57`; quote: “8×8 PE is always compute-bound.” **Disposition:** rejected as physical bottleneck claim; owner `E14:C14.23`; domain=`operator_analytical_cycles`; OBJ bottleneck:d; MD calibration/traffic timeline; ALT compute/memory bound; SAFE GOPS plateaus in the report equation only; REV measured or integrated bottleneck evidence.
65. **O4.4 — Pipeline sizing prescription.** `L44–53` implication; quote: “Larger kernels improve PE utilization.” **Disposition:** blocked as sizing guidance; owner `E14:C14.20/C14.23`; domain=`noncycle_functional_or_structure`; OBJ architecture:d; MD workload mix/PPA; ALT PE sizes; SAFE use as a hypothesis for corrected DSE; REV comparable physical objectives.

### O5. `mma-fused-activation-overhead.md`

**Hash:** `a3567ea837004f7bdda20d5c56b908d4bfa0d79505fbefd1c2d3f28b574deb06`  
**Context:** Q=post-GEMM activation cost; axes=PE/workload/activation; producer=standalone formulas, explicitly “analytical, no cmodel dependency”; units=local MMA/EW formula cycles and ratios.  
**Binding limitation:** actual elementwise accounting is a distinct post-refill event-count path (`E14:C14.2/C14.3/C14.16`), not the report’s equation or a common elapsed timeline.

66. **O5.1 — EW formula.** `L29–31`, heading `L19: "## Cycle Model"`; quote: “`total = ceil(elems / 32) × (1 + 32 × 2) ≈ 2.03 × elems`.” **Disposition:** rejected as current elementwise evidence; owner `E14:C14.3`; domain=`local_formula_cycles`; OBJ formula cycles:q; MD actual accounting path; ALT local formula/current elementwise return; SAFE historical standalone equation only; REV linked implementation matching it.
67. **O5.2 — 403–721% claim.** `L62`; quote: “the ReLU pass costs 403-721% of the GEMM itself.” **Disposition:** rejected; owner `E14:C14.2/C14.3/C14.23`; domain=`local_formula_cycles`; OBJ ratio:q; MD common metric/timeline; ALT fused/decoupled; SAFE do not ratio distinct handwritten producers; REV common elapsed producer.
68. **O5.3 — Three K regimes.** `L64–70`; quote: “EW-dominated,” “EW-significant,” “EW-negligible.” **Disposition:** rejected; owner `E14:C14.2/C14.3`; domain=`local_formula_cycles`; OBJ architecture regime:q; MD linked formulas and second-axis sensitivity; ALT K/PE combinations; SAFE unvalidated historical partition; REV corrected linked sweep.
69. **O5.4 — Activations equivalent.** `L74`; quote: “All activations are equivalent” and “compute micro-op is negligible.” **Disposition:** rejected; owner `E14:C14.16/C14.23`; domain=`noncycle_functional_or_structure`; OBJ compute:d; MD activation compute costs/precision; ALT ReLU/GELU/SiLU; SAFE memory pattern alone cannot prove equal elapsed cost; REV cycle-aware opcode implementation.
70. **O5.5 — Fusion saves 2–7×.** `L76`; quote: “saves 2-7× on total cycle count.” **Disposition:** blocked/recommendation rejected; owner `E14:C14.20/C14.23`; domain=`local_formula_cycles`; OBJ latency:q, area/control:u; MD fused implementation and common timeline; ALT separate/fused; SAFE fusion is a high-value hypothesis, no speedup authorized; REV executable fused path.

### O6. `norm-after-attention-pipeline.md`

**Hash:** `65529ebad6e501e66c2ebd5ea601d56e4b1f3acab65e33c639fb62c95a892737`  
**Context:** Q=norm share after attention; axes=PE, M/N/d, LN/RMS; producer=attention analytical stats plus norm SRAM stall returns; units=incompatible “cycles.”  
**Binding limitation:** heterogeneous engine return values cannot be summed into total latency (`E14:C14.2`); attention correctness is broken (`E14:C14.8–C14.10`).

71. **O6.1 — LN/RMS equality.** `L38–40`; quote: “exactly 2.00 cycles per element across all workloads.” **Disposition:** qualified; owner `E14:C14.3/C14.15`; domain=`sram_stall_returns`; OBJ stall return:q; MD compute cost and initial SRAM state; ALT LN/RMS; SAFE bounded norm return equality, not bandwidth or elapsed time; REV discriminating state/compute model.
72. **O6.2 — 8.2–16.5% overhead.** `L42–47`; quote: “norm adds 8.2% to 16.5% to the attention cycle count.” **Disposition:** rejected; owner `E14:C14.2/C14.8–C14.10`; domain=`sram_stall_returns`; OBJ pipeline share:q; MD common timeline and correct attention; ALT standalone/fused; SAFE do not divide norm stall returns by attention totals; REV corrected common-domain pipeline.
73. **O6.3 — PE/head/M trends.** `L49–63`; quotes: “Larger PE arrays increase norm overhead percentage,” “Larger head dimensions amplify,” and “independent of M.” **Disposition:** rejected as pipeline trends; owner `E14:C14.2`; domain=`sram_stall_returns`; OBJ ratio:q; MD common producer; ALT listed geometries; SAFE retain only separate numerator/denominator observations; REV common-domain rerun.
74. **O6.4 — Fusion/quantization guidance.** `L67–70`; quotes: “consider fusing norm” and “eliminating the norm pass entirely.” **Disposition:** blocked; owner `E14:C14.20/C14.24`; domain=`noncycle_functional_or_structure`; OBJ latency:d, software:u; MD fused implementation and precision route; ALT standalone/output-path/quantization fusion; SAFE future hypotheses only; REV executable fused path.

**Cardinality contradiction:** `L17` says 15 attempted and 10 valid, but `L23–34` contains **12** result rows.

### O7. `norm-mode-comparison.md`

**Hash:** `7c08dc30d609a97df140580fcdb1e2ddd4a89bd348535ceb14ff178606f7bcfb`  
**Context:** Q=LN/RMS memory-return difference; axes=mode and N=256–8192; controls=in-place FP32, epsilon 1e-5; producer=normalization stall-return API; units=returned stall cycles.  
**Limitation:** normalization discards read returns and counts writes only (`E14:C14.3`).

75. **O7.1 — Identical 2N rows.** `L38–40`; quote: “Both produce exactly `2.0 × elem_count` stall cycles.” **Disposition:** qualified; owner `E14:C14.3/C14.15`; domain=`sram_stall_returns`; OBJ stall return:q; MD compute and SRAM-history sensitivity; ALT LN/RMS; SAFE exact sweep fixture result; REV fresh-state/census counterexample.
76. **O7.2 — Compute/numerical choice.** `L42–44`; quote: “LayerNorm vs RMSNorm is a compute/numerical decision, not a bandwidth optimization target.” **Disposition:** qualified directionally; owner `E14:C14.3/C14.15`; domain=`sram_stall_returns`; OBJ compute:u, numerics:u; MD compute cycles and application quality; ALT LN/RMS; SAFE equal returned stalls do not decide mode; REV compute/numerical evidence.
77. **O7.3 — Mode prescriptions.** `L43–44`; quotes: “RMSNorm when…” and “LayerNorm when….” **Disposition:** blocked; owner `E14:C14.15/C14.23`; domain=`noncycle_functional_or_structure`; OBJ application quality:u, hardware:u; MD workload correctness/PPA; ALT LN/RMS; SAFE preserve both alternatives without winner; REV application and implementation evidence.

### O8. `pooling-config-sweep.md`

**Hash:** `1a95ce3c4fccd58ffd695c5d27061d82071d9484399a5fbf21661b0f0dc3327f`  
**Context:** Q=pool type/kernel/stride effects; W=56²×64 FP32; axes=max/avg, 2/3/5/7 kernels, stride 1/2; producer=pool analytical return; units=analytical cycles and elements/cycle.  
**Limitation:** exact source equation is `Σ(spatial_out·kh·kw·ops_per_elem)+kh`, not measured time (`E14:C14.6/C14.23`).

78. **O8.1 — Kernel-area dependence.** `L43–45`; quote: “Throughput depends ONLY on kernel area.” **Disposition:** retained only as report-equation behavior; owner `E14:C14.6`; domain=`operator_analytical_cycles`; OBJ formula throughput:q; MD real vectorization/reuse; ALT kernels; SAFE per-output body scales with area, plus drain term; REV source equation change.
79. **O8.2 — Max exactly 2× Avg.** `L49–55`; quote: “MaxPool is exactly 2× faster than AvgPool (per element).” **Disposition:** retained as `ops_per_elem=1/2`; owner `E14:C14.6/C14.17`; domain=`operator_analytical_cycles`; OBJ formula cycles:q; MD actual compare/add/div timing; ALT max/avg; SAFE analytical coefficient ratio only; REV calibrated compute.
80. **O8.3 — Stride-zero elemental effect.** `L72–76`; quote: “Stride has zero effect on elemental throughput.” **Disposition:** retained as equation behavior; owner `E14:C14.6`; domain=`operator_analytical_cycles`; OBJ formula throughput:q; MD cache/window reuse; ALT stride 1/2; SAFE stride changes output count, not the report’s per-window coefficient; REV stride-aware implementation.
81. **O8.4 — MaxPool/performance prescriptions.** `L47`, `L57`, `L76`; quotes: “prefer MaxPool” and “stride can be chosen based on accuracy needs without throughput concerns.” **Disposition:** blocked/rejected as architecture advice; owner `E14:C14.20/C14.23`; domain=`noncycle_functional_or_structure`; OBJ application accuracy:u, latency:d; MD semantics, hardware, integration; ALT modes/strides; SAFE equation alone cannot choose semantically different operators; REV application-equivalent comparison.

**Formula qualification:** `L45` states `cycles = output_elements × … × factor`, but the exact source also adds a `+kh` drain term; the tables visibly include it (for example 774,400+2=774,402).

### O9. `softmax-after-attention-pipeline.md`

**Hash:** `080e9cf0b358fac2cadbbc9bcecf9744b973abc1affe5710097ea64f391f5c67`  
**Context:** Q=standalone softmax share after attention; axes=PE and M/N/d; producer=softmax SRAM returns divided by attention analytical totals; units=incompatible.  
**Binding limitation:** softmax returns read+write stalls; attention totals are a different domain (`E14:C14.2/C14.3`), and attention correctness is blocked.

82. **O9.1 — 4.00 cycles/element.** `L38–40`; quote: “exactly 4.00 cycles per element.” **Disposition:** rejected as universal return formula; owner `E14:C14.3/C14.14`; domain=`sram_stall_returns`; OBJ stall return:q; MD staging/history; ALT standard standalone; SAFE retained rows are state-specific returns; fresh-state probes give 4 elements→8 and 40→96; REV a state-complete invariant proof.
83. **O9.2 — 16.4–32.9% overhead.** `L42–47`; quote: “standalone softmax adds 16.4% to 32.9%.” **Disposition:** rejected; owner `E14:C14.2/C14.8–C14.10`; domain=`sram_stall_returns`; OBJ pipeline share:q; MD common timeline/correct attention; ALT internal/standalone; SAFE no ratio across these producers; REV corrected unified pipeline.
84. **O9.3 — PE/head trends.** `L49–59`; quotes: “Larger PE arrays increase overhead percentage” and “Larger head dimensions disproportionately amplify.” **Disposition:** rejected as pipeline conclusions; owner `E14:C14.2`; domain=`sram_stall_returns`; OBJ ratio:q; MD comparable producer; ALT geometries; SAFE separate values may be listed without composing them; REV common-domain study.
85. **O9.4 — Internal softmax eliminates overhead.** `L70`; quote: “the internal softmax eliminates this 16-33% overhead entirely.” **Disposition:** rejected; owner `E14:C14.7–C14.10`; domain=`noncycle_functional_or_structure`; OBJ integration:d; MD correct attention and counterfactual baseline; ALT internal/standalone; SAFE attention calls internal softmax, but no valid 16–33% elimination follows; REV corrected A/B implementation.
86. **O9.5 — Analytical cross-check.** `L74–80`; quotes: “Total ≈ 6 cycles/elem theoretical” and “The cmodel reports 4.00 because…” **Disposition:** rejected; owner `E14:C14.3/C14.14`; domain=`sram_stall_returns`; OBJ explanatory formula:q; MD exact bank-state derivation; ALT 4/6/state-dependent; SAFE current exact return must be derived from access history, not a constant; REV source-faithful proof.

### O10. `softmax-mode-comparison.md`

**Hash:** `bd90594756c735d556147208681c0c352990b55c09e359a2063306ec005feda6`  
**Context:** Q=Standard/Log/Online SRAM-return differences; axes=mode and matrix shape; producer=softmax return API; units=SRAM stall returns.  
**Limitation:** “`tu_softmax_execute()` returns SRAM stall cycles only, not total compute cycles” (`L40`), consistent with `E14:C14.2`.

87. **O10.1 — Equal retained matrix rows.** `L32`; quote: “All three modes … produce identical SRAM stall cycles for any given element count.” **Disposition:** qualified; owner `E14:C14.2/C14.14`; domain=`sram_stall_returns`; OBJ stall return:q; MD compute and fresh-state sensitivity; ALT Standard/Log/Online; SAFE equality on the sweep fixtures only; REV discriminating state or mode implementation.
88. **O10.2 — Universal `4×N`.** `L34–36`; quote: “`stall_cycles = 4 × elem_count`.” **Disposition:** rejected as universal formula; owner `E14:C14.3/C14.14`; domain=`sram_stall_returns`; OBJ stall return:q; MD input staging/history; ALT state-dependent return; SAFE report matrix had 4N, while fresh-state probes do not; REV proof across initial states.
89. **O10.3 — Mode-selection advice.** `L44`; quote: “Choose Online for streaming … Log for numerical stability … Standard as the default.” **Disposition:** blocked; owner `E14:C14.23/C14.24`; domain=`noncycle_functional_or_structure`; OBJ compute/numerics:u; MD compute cost, accuracy, dispatch; ALT all modes; SAFE equal stall returns do not choose a mode; REV compute/numerical/application study.
90. **O10.4 — “SRAM-bandwidth-bound” and banking prescription.** `L45–46`; quote: “Softmax is SRAM-bandwidth-bound” and “requires SRAM bandwidth optimization.” **Disposition:** rejected as physical conclusion; owner `E14:C14.2/C14.23`; domain=`sram_stall_returns`; OBJ bottleneck:d; MD total compute/calibration; ALT wider SRAM/mode tuning/compute; SAFE API returns stall values only; REV calibrated total-throughput model.

---

## Duplicate and contradiction register

### Material duplicates

1. **RLE → bitmap supersession:** `weight-compression-rle-sweep.md`’s eight-row raw/RLE matrix is a strict historical subset superseded by `bitmap-weight-compression.md`’s current 12-row matrix.
2. **Bitmap decoder summary duplicate:** `bitmap-weight-compression.md:L115` summarizes the detailed decoder conclusions in `weight-decoder-throughput.md:L88–92`; the latter is canonical for estimator knees.
3. **INT8/precision overlap:** both precision reports vary byte widths through report-local WS formulas, but disagree on the same nominal 128³ FP16 total: **12,291** in INT8 versus **11,296** in precision, demonstrating distinct formula assumptions/producers.
4. **Norm duplicate:** `norm-after-attention-pipeline.md` repeats the LN/RMS equality from `norm-mode-comparison.md`; only the standalone stall-return result is locally comparable.
5. **Pooling duplicate:** `conv-pool-cascade.md` reuses pooling coefficients from `pooling-config-sweep.md`; its percentages add a separate conv formula.
6. **Softmax duplicate:** `softmax-after-attention-pipeline.md` repeats `softmax-mode-comparison.md`’s 4N rows and then composes them with attention totals; that composition is rejected.
7. **Attention dependency duplicate:** both after-attention pipeline reports inherit the same defective attention producer; neither can rehabilitate it by using a separate post-operator return.

### Arithmetic/internal contradictions

- **Precision:** GFLOPS are off by 1000×; printed peak `0.51` should be 512 GFLOP/s at 1 GHz.
- **Attention:** prefill called DMA-bound despite 15–17% DMA; stated 50K compute reduction is 7,680 from shown rows; decode is called both compute-bound and KV-bandwidth-bound.
- **Conv groups:** heading references 8×8 while the comparison uses 32×32; K=9/32 is assigned `kt=2` despite the displayed ceiling formula yielding 1; derivation exceeds table total.
- **Norm-after-attention:** claims 10 valid configs but prints 12 rows.
- **Pooling:** prose omits the exact `+kh` drain term.
- **Softmax-after-attention:** its own cross-check derives ≈6 cycles/element while asserting exactly 4; current source proves history-dependent returns rather than either universal constant.

## Totals

- **Reports inspected:** 17/17.
- **High-salience split claims:** **90**.
- **By report set:** numerics/weight representation **42**; operator irregularity **48**.
- **Likely dispositions:** retained **7**; qualified **40**; superseded **1**; rejected **24**; blocked **18**.
- **Reports with zero high-salience claims:** **0**.
- **Duplicate families:** **7**.
- **Explicit arithmetic/internal contradiction groups:** **6**.
- **Cross-domain compositions rejected:** norm→attention and softmax→attention percentages; fused-activation local ratios.
- **Attention correctness-blocked claims:** **6 performance/prescriptive claim groups**, plus two qualified structural observations.
- **Files created or modified:** none.
- **Verification:** source remained detached/clean at `e918c80b6fce833cd1fcae97730fa841c2176f25`; book remained clean `main` at `88cba9bf9a26b2ae2c3079e6c57446803ab76df0`; no network used.