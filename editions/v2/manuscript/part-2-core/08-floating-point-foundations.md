# Chapter 8 — Floating-Point Foundations

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-8)

Put `0x0001` in activation SRAM, multiply by half-precision `+1`, and start the accumulator at zero. What should come back? Not the four bytes `0x00000001`: the output is stored in a different format. Not zero, either, even though the simulator's FP16 subnormal setting reads *flush*. On the three direct dataflow routes at this edition's pin, the output word is `0x33800000`. Getting that prediction right requires knowing both the representation and the direction of conversion.

**Edition and scope.** The executable example uses public Tusim `7a094ff6c5527eff8e4318de676f0c0221c448b4`. It checks a one-term MMA for every finite nonzero binary16 activation, not every floating-point operation. Results marked **historical** belong to the first edition's July 25, 2026 simulator pin, `e918c80b6fce833cd1fcae97730fa841c2176f25`; they are not fresh tests of this edition.

## Learning objectives

- Derive a raw binary32 expectation without asking Tusim to decode a binary16 value.
- Trace storage, widening, arithmetic, accumulation and output storage through one real call.
- Distinguish a common converter from an independent reference, and a requested route from an executed one.
- Explain which questions about rounding, subnormals and special values an identity product can settle, and design separate tests for the rest.

**Prerequisites.** [Chapter 4](04-configuration-as-the-architecture-contract.md) distinguishes a request from active state. Chapter 6 gives the orientation `O[M,N] += W[M,K] × A[K,N]`. [Chapter 7](07-pluggable-dataflows.md) follows the selected plug-in into the tile dispatcher. Here we hold the equation fixed and ask what numbers the bytes denote.

## 8.1 Representation is not arithmetic

Let `s`, `E` and `F` be the sign, stored exponent and fraction. In binary16 these fields occupy 1, 5 and 10 bits. A normal value (`1 ≤ E ≤ 30`) is `(-1)^s × (1024 + F) × 2^(E−25)`. The 1024 accounts for the implicit leading one. At `E=0` the rule changes: the value is `(-1)^s × F × 2^-24`. The leading one disappears; the spacing does not jump at the transition to the smallest normal. Thus `0x03ff` denotes `1023 × 2^-24` and `0x0400` denotes `1024 × 2^-24`. A test containing only powers of two would miss errors in constructing the trailing fraction.

`E=0, F=0` gives the two signed zeros. `E=31` gives infinity when `F=0`, otherwise a NaN. NaN class, sign, payload, quieting and exception flags are distinct properties. Checking `isnan` addresses just one. The same exponent-field rule should not be assumed for every format called FP8.

## 8.2 What “FP16 MMA” leaves unspecified

| Boundary | Question | Pinned direct plug-in path |
|---|---|---|
| W/A storage | What bytes does a tile consume? | Two bytes per element, interpreted as binary16 words. Raw copies need not perform a conversion. |
| Widening | Do tiny stored operands survive? | Both operands go through `tu_fp16_to_fp32`. The census below checks the activation side with a fixed weight. |
| Product and accumulation | Where is the dot product evaluated? | The callbacks multiply widened C `float` values and add into a local `float psum` for a K tile. |
| Output | What does the caller read? | `O += psum`, with `sizeof(fp32_t)` bytes per element; the probe reads the four bytes in O SRAM. No narrow-on-store step here. |
| Policy | Where can bits be discarded? | FP32-to-FP16 encoding is a different call. The decoder of an already stored half does not consult its narrowing policy. |
| Selection | Who chooses the implementation? | Dataflow selection changes the callback. A precision descriptor with `to_fp32` / `from_fp32` callbacks is not an MMA instruction selecting that format. |

A hardware contract would also specify product precision, fusion, overflow and saturation, intermediate rounding and exceptions. Reading the size of `O` does not answer those questions.

## 8.3 Follow one word from SRAM to the result

At the edition pin, read these under `tu_cmodel/` in order:

1. `tu_cmodel.c`, `tu_set_dataflow` and `tu_mma`: the setter installs the registry object in `g_tu.dataflow`. The direct call constructs W, A and O tensor descriptors over the SRAM bytes. It passes the active object to `tu_dataflow_execute_mma` when the plug-in path is enabled and a callback is present.
2. `compute/dataflow/dataflow_dispatcher.c`: the dispatcher calls `plugin->execute_tile` with the valid M, N and K extents; it accumulates the plug-in's charges. Seeing a requested name before this branch would not establish that the branch ran.
3. `compute/dataflow/weight_stationary.c`, `output_stationary.c` and `row_stationary.c` in the same directory: the multiply loops call `tu_fp16_to_fp32` on the loaded W and A words. There are three tile callbacks, **not three private binary16 decoders**.
4. `tu_precision.c`: `tu_fp16_to_fp32` constructs a binary32 word; `tu_fp32_to_fp16` narrows in the opposite direction. Follow the function that the loop calls, not a similarly named declaration or an overview comment about a rounded store.

The comparison uses an integer checker independent of Tusim. Agreement between routes alone would not test a shared conversion helper.

## 8.4 An integer oracle for exact widening

For a finite nonzero half, write its unsigned magnitude as `c × 2^q`. For normals use `c=1024+F, q=E−25`; for subnormals use `c=F, q=−24`. If bit `b` is the highest set bit of `c`, the leading one has weight `2^(b+q)`. Binary32 can represent every such value as a *normal* with room to spare. Remove that leading one, place the remaining bits in the binary32 fraction, and attach the sign:

```text
b        = bit_length(c) − 1
exp32    = 127 + b + q
fraction = (c − 2^b) << (23 − b)
word     = (s << 31) | (exp32 << 23) | fraction
```

For `0x8001`, `c=1`, so `b=0`, `exp32=103` and `fraction=0`. Including the sign gives `0xb3800000`. There is no discarded bit on which a tie rule could operate. Multiplication by exactly one and addition to exactly zero leave this finite nonzero value unchanged. That is why a representation formula supplies an oracle for the **final O word** in this particular arithmetic experiment. It would not supply the answer for a general dot product.

The checker is a separate Python program. It uses integers, not a compiler half cast, a host floating calculation or a Tusim API. It computes the word from the independently enumerated input and checks the raw A readback as well as O. This is a check against the stated decoding rule, not certification by an external floating-point reference implementation.

## 8.5 Put every finite nonzero activation through each route

Use the direct state in a fresh process for each mode. Set a 4×8 array, pipeline depth 2, and select the plug-in *after* initialization. Hold W at `0x3c00` (`+1`); fill A from raw encodings and seed O with positive zero before **each** call. Invoke `tu_mma(1,N,1,0,0,0,false)`: no bias, one product per output. Batching up to 1,024 columns amortizes setup without turning the experiment into a reduction. At offset zero, even the largest call needs only 2 / 2,048 / 4,096 bytes in W / A / O respectively. The observed capacities were 131,072 / 65,536 / 65,536 bytes.

There are `30 × 1024 = 30,720` normals and `1023` nonzero subnormals **per sign**. Per route that gives 61,440 normals and 2,046 subnormals. The checker demands exactly the two ordered intervals `0001…7bff` and `8001…fbff`, not merely the right number of lines. Each cell below is **mismatches / checked words** in the retained run.

| Actual plug-in (active ID) | + normal | − normal | + subnormal | − subnormal | All finite nonzero |
|---|---:|---:|---:|---:|---:|
| `weight_stationary` (0) | 0 / 30,720 | 0 / 30,720 | 0 / 1,023 | 0 / 1,023 | 0 / 63,486 |
| `output_stationary` (1) | 0 / 30,720 | 0 / 30,720 | 0 / 1,023 | 0 / 1,023 | 0 / 63,486 |
| `row_stationary` (2) | 0 / 30,720 | 0 / 30,720 | 0 / 1,023 | 0 / 1,023 | 0 / 63,486 |

| Value (magnitude) | Positive A → expected and observed O | Negative A → expected and observed O |
|---|---|---|
| Least subnormal | `0001 → 33800000` | `8001 → b3800000` |
| Next subnormal | `0002 → 34000000` | `8002 → b4000000` |
| Greatest subnormal | `03ff → 387fc000` | `83ff → b87fc000` |
| Least normal | `0400 → 38800000` | `8400 → b8800000` |
| One | `3c00 → 3f800000` | `bc00 → bf800000` |
| Greatest finite | `7bff → 477fe000` | `fbff → c77fe000` |

These are 190,458 checked results, not 190,458 distinct activations or a statistical sample. Raw examples and counts distinguish expected from observed in each route.

**Did three different routes run?** Before and after each call, the fixture checks the active pointer against the registry, the ID and the name. It rejects identical tile callbacks for different registrations. It also requires progress in the selected plug-in's cycle counter equal to the global MMA delta, as well as the expected tile and operation counts. For one valid tile of width `n` at `m=k=1`, the charge is `2n+3` for WS, `2` for OS and `n+3` for RS. Each route completed 62 calls and 7,936 tiles; the respective modeled charges were 150,780, 15,872 and 87,294. These distinguish execution here; they are not measurements of multiplier latency, operand traffic or energy.

**Historical comparison.** The v1 fixture called the individual tile callbacks and counted 1,982 mismatches per plug-in, all among the 2,046 nonzero signed subnormals. Its `0001` came back as `38800000`, the value of the smallest *normal*. The frozen fixture required this defect signature to reproduce the old version. The present result reverses that finding on the same finite identity domain through direct dispatch. Sharing the corrected widening path explains why the implementations agree; checking them against the integer oracle is what makes agreement evidence of correctness here.

## 8.6 BF16: same storage width, different numbers

Binary16 uses five exponent and ten fraction bits. BF16 trades three fraction bits for three exponent bits: its range is closer to binary32, but the spacing near one is coarser. The same two-byte word `0x3c00` that represents one in binary16 is *not* BF16 one (`0x3f80`). Equal element sizes cannot justify substituting formats.

The BF16 descriptor in `tu_precision.c` widens by moving the 16 bits into the high half of a binary32 word. The public focused suite's BF16→FP16 pipeline test converts selected values **through** FP32 and back; it does not issue a BF16 MMA. **Historical boundary:** the v1 audit widened BF16 `0001` to `00010000`, but narrowing that binary32 word returned `0000`. Widening and narrowing need separate tests. The finite FP16 census supplies neither BF16 coverage nor evidence about BF16 execution speed.

## 8.7 FP8: specify the encoding table

E4M3 and E5M2 allocate different numbers of bits to the exponent and fraction. That shorthand alone does not specify how to encode overflow or which top-exponent words are finite. For example, the scalar OFP8 E4M3 table includes 448. A test of a limiting value should name the table, the conversion direction and the overflow rule, not just “FP8”. A block-scaled tensor format adds scale representation and scale selection to the scalar contract.

**Historical boundary:** the v1 E4M3-like converter decoded `77` as 240 but encoded 240 as `7f` (NaN). Its decoder disagreed with the OFP8 reference on 14 of 256 codes; the E5M2 decoder had zero disagreements in that comparison. Even the latter result said nothing about *encoding*: the historical E5M2 encoder sent 60,000 to infinity under RNE. None of these FP8 counts was rerun for this chapter. They illustrate why a round trip and a one-way comparison answer different questions.

## 8.8 TF32-like conversion is not TF32 multiplication

Tusim's TF32-like API uses a 32-bit container with ten retained fraction bits. Dropping thirteen low binary32 fraction bits can change numerical precision without saving one byte of storage. Trace `tf32.c` and the registry adapters separately from the W/A loads in §8.3. A converter can be called without there being a direct-MMA operand selector for its format.

**Historical boundary:** masking `3f801fff` yielded `3f800000` in v1. For a signaling NaN with payload only in the masked region, `7f800001` yielded `7f800000` (infinity). The identity product studied here cannot confirm or overturn either TF32-like observation. The same caution applies when comparing a software container with the operand semantics of a vendor's Tensor Core.

## 8.10 Arithmetic, accumulation and special cases

Read the tile loop as two operations on sums: form a local `psum` over the valid K extent, then add that sum to the existing O word. With more than one K tile, changing the partition can change the grouping of additions. With a nonzero seed, the final O update can itself discard low bits. A single exactly representable term added to zero does not distinguish fused from unfused evaluation, demonstrate cancellation accuracy, or establish a hardware rounding schedule. C `float` expressions and the compiler/host are part of the observed path.

Of 65,536 possible A words, **2,050 are excluded per route**:

- `0000`, `8000` (2 zeros): pure widening has a defined sign bit, but adding a product to positive zero is an arithmetic operation. Numeric equality cannot test the sign of the result.
- `7c00`, `fc00` (2 infinities): infinity is not a finite identity case. A separate infinity check could specify class and sign; the present count includes neither.
- Exponent 31, nonzero fraction (2,046 NaNs): arithmetic may quiet a signaling NaN; preserving sign or payload is a different contract from producing a NaN. There is no expected NaN word in this census.

A standalone decode-only test can legitimately cover all 65,536 codes under a specified representation mapping. **Historical:** the v1 canonical decoder had zero raw mismatches on that full domain. Do not attach that denominator to the v2 MMA result or transfer a representation-only NaN policy through a MAC.

## 8.11 Architecture trade-offs

| Proposed choice | What it could buy | What to measure before choosing |
|---|---|---|
| Binary16 storage, wider accumulation | Smaller W/A payload than binary32 without narrowing each partial sum | Distribution of operands lost during input encoding; overflow and cancellation as K grows |
| BF16 rather than binary16 inputs | Wider exponent range at the same element width | Loss from coarser significand, end-to-end type retention, existence of an actual BF16 path |
| Scaled FP8 tensors | Smaller element payload | Scale bytes, rescaling points, saturation counts and accuracy under the chosen encoding table |
| FTZ rather than gradual underflow | Simpler tiny-value handling in a proposed design | Effect on results near zero; separately obtain implementation evidence for any area, timing or energy saving |
| Stochastic rather than deterministic narrowing | Potential reduction of systematic rounding bias | Error distribution, generator correlation, seed ownership and replay under different lane orders |

For example, storing W/A in half the bytes does not halve O traffic when O remains binary32. It also does not halve elapsed time unless the limiting resource benefits. A precision comparison needs a workload, an accuracy criterion and a named storage or execution boundary.

## 8.14 Fidelity box

**Demonstrated:** the direct WS, OS and RS routes at this pin produce the expected binary32 O word for every finite nonzero binary16 A in the stated identity product. The old 1,982-per-route discrepancy is historical. **Not demonstrated:** arbitrary operand pairs, nonzero initial O, multi-term sums, signed zeros, infinities, NaNs, exception flags, other modes or formats, RTL behavior, or hardware performance. No claim about the correctness of FP32-to-FP16 encoding is needed for this result.

## 8.15 Common mistakes

- **Generate the inputs through the converter you meant to bypass.** Encoding tiny floats under flush can remove the entire class you intended to test. Start from raw words and count them.
- **Compare WS only to OS and RS.** Sharing a converter makes common-mode errors possible. Also compare each selected route to an independent expected word.
- **Print “zero errors” after comparing zero words.** Cardinality is necessary but not sufficient: a duplicate can hide an omission. Require record-by-record input identity as well.
- **Treat the initialization banner as the active selection.** The setter here runs after initialization. Inspect state and account for actual dispatched work.
- **Use a passing defect snapshot as a specification.** A v1 validator that insists on `38800000` for `0001` should fail on the corrected result. Keep the old transcript rather than weakening the new oracle.

## 8.16 Review questions and design exercises

1. Starting only from `h=0x83ff`, derive the binary32 O word. Which operation, if any, needs a rounding decision?
2. A colleague reports 63,486 successful comparisons for each label, but fed exactly the same WS output file to all three comparisons. What independent observations would reject that report? What if they compared no rows?
3. Explain how `TU_SUBNORMAL_FLUSH` and a correct nonzero result for A=`0001` can coexist. What inputs and observation point would actually test the flush threshold?
4. Why is adding the 2,050 excluded encodings to the loop insufficient to establish a special-value contract?
5. Design a test that could reveal a K-grouping effect without changing either operand format. What new oracle would it require?

**Answer sketches.** (1) The magnitude is `1023 × 2^-24`, so `b=9`, the unbiased exponent is −15, and the sign is one: `b87fc000`. No rounding is necessary. (2) The records contain the observed active ID, and before accepting them the producer checks registry identity, distinct callbacks and route-specific charges. The checker separately enforces the ordered domain and the four category counts. (3) Flush is in the *encoder*; test exact binary32 values on either side of the subnormal/normal rounding boundary and inspect the emitted **half word**, under named modes. (4) Specify separate expectations for pure conversion and arithmetic: sign of zero, signed infinity, NaN class, payload, quieting and any flags. (5) Use the same multi-term dot product with different K partitions and a cancellation-sensitive mix of magnitudes. Predict intermediate and final rounded sums under a specified arithmetic model; the widening formula alone cannot predict them.

**Design exercises.** Extend the runner on paper for three separate questions: (a) swap W and A while preserving exact per-word coverage; (b) enumerate the two binary32 neighbors and exact midpoint of each adjacent pair of finite binary16 values for a narrowing test, including carry into minimum normal; (c) design an experiment with a nonzero FP32 O seed that distinguishes raw O storage from half-rounded writeback. For each, state a failing raw vector or control before choosing any tolerance. If proposing BF16 or FP8 MMA, also specify operand layout and a runtime selection gate that rejects unsupported combinations.

[Next: Chapter 9 — Memory Hierarchy and Banked Scratchpads](09-memory-hierarchy-and-banked-scratchpads.md)
