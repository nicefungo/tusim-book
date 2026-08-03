# Chapter 8 — Floating-Point Foundations

> **Edition scope.** This chapter describes Tusim at commit `e918c80b6fce833cd1fcae97730fa841c2176f25`. It distinguishes bit representations, conversions, arithmetic, accumulation, storage, rounding, special values, and subnormal policy. A precision name or registry entry does not imply that an engine executes that precision.


## Learning objectives

After this chapter, you should be able to:

1. separate a floating-point format from conversion, arithmetic, accumulation, storage, overflow/saturation, and selection contracts;
2. derive normal and subnormal values from sign, exponent, and fraction fields;
3. explain why range, precision, and accumulator width are independent architecture choices;
4. trace Tusim's canonical FP16, BF16, FP8, and TF32 conversion APIs and precision registry;
5. distinguish round-to-nearest-even, round-toward-zero, and stochastic rounding, including tie and overflow behavior;
6. reproduce Tusim's raw-bit behavior for signed zero, subnormal and normal boundaries, infinities, NaNs, ties, overflow, and underflow;
7. identify disagreements between canonical FP16 conversion and the three dataflow-local decoders;
8. explain why parsed precision configuration does not select runtime arithmetic at the pinned revision;
9. evaluate lower precision across throughput, storage, energy, numerical risk, control, compiler, and verification costs;
10. design tests that fail on wrong bits rather than pass on broad numerical tolerances.

## Prerequisite graph

```text
Chapter 4: requested configuration -> active runtime state
                         |
Chapter 5: global state, ownership, and public APIs
                         |
Chapter 6: FP16 W/A -> FP32 O; tiled O += W A
                         |
Chapter 7: canonical versus dataflow-local conversion
                         v
 representation -> conversion -> arithmetic -> accumulation -> storage
       |              |             |              |             |
       +------ rounding, special values, and subnormal policy ---+
                                      |
                                      v
                   defensible mixed-precision contract
```

[Chapter 6](06-pe-arrays-mma-semantics-and-tiling.md) established the direct MMA orientation, and [Chapter 7](07-pluggable-dataflows.md) distinguished canonical from dataflow-local conversion:

```text
O[M,N] += W[M,K] × A[K,N]
```

Chapter 8 does not change that orientation. It asks what the three type labels in that expression actually mean, where rounding occurs, and whether all executable paths agree.

## Opening architecture question: what does “FP16 MMA” mean?

Suppose an instruction is advertised as FP16 matrix multiply-accumulate. At least eight questions remain:

1. Are W and A stored as IEEE binary16 bit patterns?
2. Are subnormal inputs preserved, flushed, or decoded by another rule?
3. Are products formed at binary16, binary32, or a hidden internal precision?
4. Is multiply-add fused, or are multiplication and addition rounded separately?
5. How wide is the partial sum?
6. Is O stored as binary16 or binary32?
7. Which rounding direction applies when data enters or leaves the engine?
8. What happens to signed zero, overflow, infinities, and NaNs?

These choices can produce the same answer for small integers and diverge at boundaries. Ordinary tests pass, yet raw-bit boundary probes expose path-specific disagreements. The rest of the chapter develops the vocabulary and evidence needed to interpret those disagreements safely.

## 8.1 Representation is not arithmetic

A binary floating-point datum has a sign bit `s`, an exponent field `E`, and a fraction field `F`. For a normal binary format with exponent bias `B` and `p-1` explicit fraction bits,

```text
value = (-1)^s × 2^(E-B) × (1 + F / 2^(p-1)).
```

For exponent field zero and nonzero fraction, a subnormal omits the implicit leading one:

```text
value = (-1)^s × 2^(1-B) × (F / 2^(p-1)).
```

This gradual-underflow region closes the gap between zero and the smallest normal. Supporting it adds conversion, arithmetic-datapath, control, and verification cases; flushing it changes numerical behavior near zero. The representation and terminology here follow IEEE 754 binary interchange formats ([IEEE19](../../references/floating-point.md#ieee19-ieee-754-2019)).

In IEEE binary interchange formats, the all-ones exponent encodes infinities when the fraction is zero and NaNs when it is nonzero; finite-only FP8 variants may assign these codes differently. A NaN also carries sign, payload, and a quiet/signaling distinction. Whether conversion preserves those fields, whether arithmetic quiets a signaling NaN, and whether an exception flag is raised are separate questions.

### Format comparison

| Name used here | Storage fields | Nominal finite-range feature | Tusim module | Direct Tusim MMA input? |
|---|---|---|---|---|
| binary16 / FP16 | 1-5-10, 16 bits | narrow range, 11-bit significand precision | `tu_precision.[ch]` | yes, W and A |
| binary32 / FP32 | 1-8-23, 32 bits | wider range and 24-bit significand precision | host `float`, observed as IEEE binary32 on the audited AArch64/GCC build | yes, O/partial sums on that build |
| bfloat16 / BF16 | 1-8-7, 16 bits | binary32 exponent range, shorter significand | `tu_precision.[ch]` | no; conversion API only |
| FP8 E4M3 | 1-4-3, 8 bits | more precision than E5M2, less range | `fp8.[ch]` | no; conversion API only |
| FP8 E5M2 | 1-5-2, 8 bits | more range, less precision | `fp8.[ch]` | no; conversion API only |
| Tusim TF32-like container | 1-8-10 retained fields in 32 bits | binary32 exponent range with ten retained fraction bits | `tf32.[ch]` | no; conversion API only |

“Direct MMA input?” is deliberately stricter than “implemented.” The precision registry has eight ordered descriptors and conversion callbacks. The direct MMA nevertheless sizes W/A using `sizeof(fp16_t)`, interprets their bytes as `uint16_t`, widens them, accumulates into host `float`, and stores O using `sizeof(fp32_t)`.

## 8.2 Ten independent contracts

The following checklist prevents precision claims from collapsing into one label.

| Contract | Question | Pinned direct-MMA answer |
|---|---|---|
| representation | Which bit layout is accepted? | W/A are 16-bit values intended as binary16; O is host `float`, observed as binary32 in the audited build |
| conversion | How are stored bits widened or narrowed? | canonical API and three duplicated local decoders coexist |
| arithmetic | At what precision are products and additions evaluated? | C host `float` expressions after widening |
| accumulation | Where and how often is the partial sum rounded? | source grouping uses one local C `float` psum and one C `float` O update per K tile; exact rounding/contraction is host/compiler-dependent |
| storage | Which bytes cross SRAM/DMA boundaries? | W/A raw FP16 bytes; O raw four-byte host-`float` bytes; DMA does not convert |
| rounding | Which mode applies at narrowing boundaries? | global API mode affects selected converters, not all paths or config initialization |
| special values | How are zero, infinity, and NaN treated? | path-specific; no coherent exception/status model |
| subnormal policy | Are tiny values represented, flushed, or transformed? | path- and format-specific; canonical FP16 default FTZ, optional defective full mode, local MMA decoders use another rule |
| overflow/saturation | Does finite overflow produce maximum finite, infinity, NaN, or another encoding? | path-specific; parsed `saturate` is dropped and no unified active saturation policy exists |
| selection | What instruction, descriptor, or runtime field chooses precision? | registry supports lookup/conversion; it is not an MMA dispatch table |

## 8.3 Source map and integration ladder

| Source | Executable evidence | Boundary |
|---|---|---|
| `tu_precision.[ch]` | canonical FP16/BF16 conversion, subnormal mode, registry | registry is not engine selection |
| `rounding.[ch]` | process-global RNE/RTZ/stochastic mode and PRNG | no validation of invalid enum; global and not thread-safe |
| `fp8.[ch]` | E4M3/E5M2 conversion and bridges through FP32 | implementation disagrees with its OCP OFP8-compatible claim for E4M3 |
| `tf32.[ch]` | 32-bit-container conversion and bridges | no TF32 multiply path |
| `compute/dataflow/{weight,output,row}_stationary.c` | FP16 widening inside all direct plug-ins | three duplicated defective subnormal decoders |
| `tu_cmodel.c` | FP16 W/A, FP32 psum/O, raw byte sizing | no precision descriptor in MMA call |
| `infra/config.c` | parses supported precisions, FP16 rounding/subnormal/saturate | conversion to runtime drops all of these fields |
| `tests/test_bf16_subnormal.c` | 12/12 focused checks | broad tolerances; does not test BF16 subnormal encoding |
| `tests/test_rounding.c` | 14/14 mode checks | does not cover FP8 ties or config effect |
| `tests/test_fp8.c` | 21/21 checks | accepts max-normal ambiguity and weak stochastic case |
| `tests/test_tf32.c` | 25/25 focused checks | omitted from aggregate `make test` |
| `tests/test_golden.c` | 11/11 quick MMA comparisons | selected normal-valued random domain and tolerances |
| `Makefile` | aggregate/focused linkage | `test-full` is not a superset; generated-code failures are suppressed with `|| true` |

The enforced audit confirms `tu_precision.o`, `rounding.o`, `fp8.o`, and `tf32.o` are members of `libtucmodel.a`. This proves linkage. Public headers prove API reachability. Focused tests prove selected behavior. None proves that every compute engine consumes every registry type.

Registry lookup also assumes a nonnegative enum. `tu_precision_get()` checks only `prec < TU_PREC_COUNT` before indexing `builtin_precisions[prec]`; a negative cast can index before the array. The chapter records this statically rather than executing undefined behavior. A future public-API test should require negative and out-of-range values to return `NULL` before any indexing.

### Reproduce this chapter's evidence

From the book root:

```bash
bash experiments/ch08_reproduce.sh
python3 experiments/ch08_validate.py
```

See the [audit report](../../experiments/ch08-precision-audit-2026-07-25.md), [probe source](../../experiments/ch08_precision_probe.c), and [source-and-claim ledger](../../notes/chapter-08-source-and-claim-ledger.md). The recorded run used AArch64 and GCC 11.4.0. It is functional evidence, not RTL or silicon calibration.

## 8.4 Canonical binary16 conversion

### Widening: a strong representation path

`tu_fp16_to_fp32()` handles zero, subnormal, normal, infinity, and NaN by constructing binary32 bits. The Chapter 8 probe independently derives the expected binary32 code for all 65,536 input patterns. Mismatches are zero.

Representative results are:

| binary16 input | Meaning | binary32 output bits |
|---:|---|---:|
| `0x0000` | +0 | `0x00000000` |
| `0x8000` | -0 | `0x80000000` |
| `0x0001` | minimum positive subnormal, `2^-24` | `0x33800000` |
| `0x03ff` | maximum subnormal | `0x387fc000` |
| `0x0400` | minimum normal, `2^-14` | `0x38800000` |
| `0x7bff` | maximum finite, 65,504 | `0x477fe000` |
| `0x7c00` | +infinity | `0x7f800000` |
| `0x7e00` | quiet NaN example | `0x7fc00000` |
| `0x7d00` | signaling NaN example | `0x7fa00000` |

This is an **executable representation-conversion result**, not a claim about subsequent host arithmetic, exception flags, or NaN payload stability after a MAC.

### Narrowing: default FTZ and a defective “full” mode

`tu_fp32_to_fp16()` defaults to `TU_SUBNORMAL_FLUSH`. Tusim performs a pre-round exponent-region flush for FP32 inputs with unbiased exponent at most -15. This removes all FP16 subnormal results and incorrectly flushes part of the region that should round to minimum normal. Normal ties outside that region use the global rounding mode; the probe confirms RNE maps midpoint `1 + 2^-11` to even `0x3c00`.

Switching to `TU_SUBNORMAL_FULL` does not establish correct gradual underflow. The expanded matrix gives:

| exact binary32 source | correct binary16 under RNE | Tusim full-mode result |
|---|---:|---:|
| half minimum subnormal, raw `0x33000000` | `0x0000` | `0x0200` |
| one binary32 step above that tie, raw `0x33000001` | `0x0001` | `0x0200` |
| minimum subnormal `2^-24` | `0x0001` | `0x0200` |
| `2^-16` | `0x0100` | `0x0200` |
| maximum subnormal `2^-14 - 2^-24` | `0x03ff` | `0x0200` |
| one binary32 step below subnormal/normal midpoint, raw `0x387fdfff` | `0x03ff` | `0x0200` |
| subnormal/normal midpoint, raw `0x387fe000` | `0x0400` | `0x0200` |
| one binary32 step above that midpoint, raw `0x387fe001` | `0x0400` | `0x0200` |

The implementation shifts a reconstructed mantissa and then calls a rounding primitive with an incompatible bit alignment; its carry handling replaces the result with `0x0200`. The chapter therefore labels this path an **executable defect**, not full IEEE subnormal support. Default FTZ also checks the source exponent before rounding. Raw `0x387fe000` becomes zero even though RNE would carry it into minimum normal `0x0400`. This is closer to a source-region/DAZ-like cutoff than a precisely specified “flush only subnormal results” contract.

Special-value conversion also has a policy: every FP32 NaN becomes positive canonical binary16 `0x7e00`. Payload and sign are discarded. Infinities preserve sign. Overflow produces infinity. Even RTZ returns infinity for a finite value such as 70,000 because the exponent range check precedes mode-specific rounding; “round toward zero” is therefore not a complete overflow policy.

## 8.5 Engine-local binary16 conversion

The three dataflow plug-ins do not call the canonical decoder. Each contains a static copy using `__builtin_clz(mantissa) - 21` for subnormals. Normal values and the selected special encodings follow the same broad layout, but the subnormal exponent construction differs from the canonical path. `dataflow_interface.h` declares shared `tu_dataflow_fp16_to_fp32()` and `tu_dataflow_fp32_to_fp16()` helpers, yet the pinned tree defines or calls neither symbol; declarations alone do not centralize behavior.

The probe sends every binary16 code through each plug-in's actual scalar multiply path with the other operand equal to one. For the 63,486 finite nonzero codes:

| Plug-in | finite mismatches | subnormal mismatches | normal mismatches | raw `0x0001` result |
|---|---:|---:|---:|---:|
| WS | 1,982 | 1,982 of 2,046 | 0 | `0x38800000` (`2^-14`) |
| OS | 1,982 | 1,982 of 2,046 | 0 | `0x38800000` (`2^-14`) |
| RS | 1,982 | 1,982 of 2,046 | 0 | `0x38800000` (`2^-14`) |

Thus 1,982 of 2,046 nonzero signed subnormal codes disagree (96.87%); 64 agree. Across the 63,486 finite nonzero codes, 1,982 disagree (3.122%). These are exhaustive census ratios for the named probe domain, not statistical estimates. The minimum subnormal is enlarged by a factor of 1,024. The mapping is non-monotonic: local decoding maps `0x0001` to `0x38800000` (`2^-14`) but maps larger `0x0002` to `0x38000000` (`2^-15`).

This result refines Chapter 7. WS/OS/RS agree with one another because they duplicate the same defect. Their equivalence does not imply agreement with the canonical API. Nor does setting canonical FTZ/full mode affect these local decoders: they do not consult `g_subnormal_mode`.

## 8.6 BF16: range retention without an execution path

BF16 stores the upper 16 bits of a binary32-like representation: one sign bit, eight exponent bits, and seven explicit fraction bits. Widening is a left shift and is exact for every BF16 bit pattern. Tusim reproduces this, including BF16 minimum subnormal `0x0001 -> binary32 0x00010000`. BF16 motivation and evaluated training behavior are discussed in [KAL19](../../references/floating-point.md#kal19-bfloat16-study); TPU-specific conversion policy is separately scoped in [GTPU](../../references/floating-point.md#gtpu-google-cloud-tpu-bfloat16-behavior).

Narrowing has a different policy. Normals use the global rounding module, and the RNE midpoint `1 + 2^-8` rounds to even BF16 `0x3f80`. But the converter unconditionally emits signed zero when the resulting BF16 exponent is nonpositive. A binary32 value exactly representing BF16 `0x0001` therefore narrows to `0x0000`. The FP16 subnormal-mode setting does not control BF16.

The special-value fast path copies the upper 16 bits. This often preserves a quiet NaN, but a signaling NaN whose payload exists only in discarded low bits, such as binary32 `0x7f800001`, becomes BF16 `0x7f80`: positive infinity. No invalid-operation flag records the change.

The focused random test called “BF16 MMA” does not execute BF16 operands in MMA. It quantizes FP32 to BF16, widens BF16 to FP32, narrows again to FP16, and feeds the existing FP16 engine. This is useful pipeline testing, but it is not a BF16 multiplier or BF16 storage path in W/A SRAM.

## 8.7 FP8: format names need exact encoding tables

### E4M3 disagreement

Tusim's source says OCP-compatible E4M3 and describes a maximum normal of 448 in one place, but the implementation uses exponent fields 1 through 14 for finite normals, decodes every exponent-15 code as NaN, and treats magnitudes greater than or equal to 240 as NaN on encode.

Consequences include:

```text
decode 0x77 -> 240
encode 240  -> 0x7f (NaN)
decode 0x78 -> NaN
encode 448  -> 0x7f (NaN)
```

The path cannot round-trip its own maximum decoded finite value. This differs from E4M3 in the normative OCP 8-bit Floating Point (OFP8) specification, where exponent-15 contains additional finite values and 448 is representable ([OCP23](../../references/floating-point.md#ocp23-ocp-8-bit-floating-point-ofp8)). The OCP Microscaling specification reuses OFP8 elements inside a block-scaled composite; it is not the scalar encoding's primary source ([OCP-MX23](../../references/floating-point.md#ocp-mx23-ocp-microscaling-formats)). The book therefore calls the pinned behavior **Tusim E4M3-like conversion**, not verified OCP E4M3 or MXFP8 conformance.

### E5M2 boundary

The E5M2 path represents infinity and NaN. It preserves exact maximum normal 57,344 as `0x7b`, then applies `abs(v) > 57344` as an early infinity threshold. Thus tested 60,000 becomes `0x7c` under both RNE and RTZ, whereas OFP8 non-saturating RNE remains below the 61,440 overflow midpoint and should produce `0x7b`; RTZ should also retain maximum finite. The encoder emits subnormal codes rather than globally flushing them, but its subnormal path clamps rounded mantissa overflow instead of carrying into minimum normal.

### RNE is not even at FP8 ties

Both FP8 converters implement nominal RNE with a floating calculation followed by `+0.5` and integer truncation. This rounds ordinary halfway cases upward, irrespective of the retained mantissa's parity:

```text
E4M3: 1.0625 halfway between 1.0 and 1.125 -> 0x39, not even 0x38
E5M2: 1.125  halfway between 1.0 and 1.25  -> 0x3d, not even 0x3c
```

The same rule maps half the minimum subnormal upward instead of tie-to-even zero. A separate carry defect maps the E4M3 subnormal/normal midpoint `15/1024` to `0x07` instead of `0x08`, and the analogous E5M2 midpoint `7/131072` to `0x03` instead of `0x04`. RTZ and stochastic branches are separate. The existing stochastic E4M3 test uses 1.5, which is exactly representable despite a comment calling it halfway; a wide tolerance lets that test pass without proving stochastic choice.

## 8.8 Tusim's TF32-like container

Tusim stores its TF32-like value as a `uint32_t` with the lower 13 binary32 fraction bits zero. Widening masks those bits and reinterprets the result as host `float`. Narrowing implements RNE, RTZ, or stochastic selection over the discarded 13 bits. This 32-bit container and retained-subnormal behavior are Tusim API semantics. NVIDIA TF32 is principally a Tensor Core computational operand interpretation, not a portable interchange/storage format with a universal denormal policy ([NVI20](../../references/floating-point.md#nvi20-nvidia-a100-and-tf32)).

The probe confirms:

- signed zero is preserved;
- the midpoint `1 + 2^-11` rounds to even 1.0;
- raw binary32 `0x00002000` is the minimum nonzero value retained by this storage convention;
- halfway raw `0x00001000` rounds to zero under RNE;
- decoding `0x3f801fff` masks it to `0x3f800000`.

The exponent-all-ones fast path simply masks low bits. A quiet NaN with a high payload bit remains NaN, but low-payload signaling NaN `0x7f800001` becomes infinity `0x7f800000`. As with BF16, “NaN preserved” is true only for a subset of NaN encodings.

TF32 conversion and registry lookup execute. TF32 multiplication does not. No direct MMA descriptor requests TF32, and no test demonstrates a TF32-input/FP32-accumulate engine.

## 8.9 Rounding is a boundary policy

Tusim exposes three global modes:

- **RNE:** nearest value; exact ties should select an even retained least-significant bit;
- **RTZ:** select a representable result no greater in magnitude than the exact value;
- **stochastic:** choose between adjacent encodings using the discarded magnitude fraction; Tusim's sign/magnitude paths increment encoded magnitude as their “up” choice, which is away from zero for negative values.

The xorshift-based stochastic generator can be seeded, making a sequence reproducible. Reproducibility is not the same as an independent statistical validation of unbiasedness, and a process-global PRNG introduces order dependence across tensors, cores, and tests.

More importantly, a mode name applies only where code consults it. At the pinned revision:

| Path | Reads global rounding mode? | Reads FP16 subnormal mode? |
|---|---:|---:|
| canonical FP32 -> FP16 | yes | yes |
| canonical FP32 -> BF16 | yes | no |
| FP32 -> FP8 E4M3/E5M2 | yes, via local logic | no |
| FP32 -> TF32 | yes, via local logic | no |
| FP16 -> FP32 | no rounding needed | no |
| WS/OS/RS local FP16 -> FP32 | no | no |
| host MMA accumulation | host/compiler semantics | no |

Configuration adds another break. JSON parsing recognizes supported precisions, FP16 rounding, subnormal behavior, and saturation. `tu_config_to_runtime()` copies none of these fields. Initialization therefore does not call the rounding/subnormal setters or select a precision arithmetic path. Direct setter calls work; configuration-selected numerical policy does not.

The global rounding and subnormal modes are process-wide mutable state. `tu_state_t` has no numerical-policy field, despite context-layer comments that describe precision and rounding snapshots. Parsed `saturate` and the `TU_FP16_SATURATE` enum also have no conversion consumer; canonical FP16 overflow emits infinity. These are separate propagation and lifecycle defects, not merely missing JSON documentation.

## 8.10 Arithmetic, accumulation, and storage

The direct dataflow plug-ins execute:

```c
float psum = 0.0f;
psum += widened_w * widened_a;
O_fp32[...] += psum;
```

This gives a practical FP16-storage/host-`float`-compute/host-`float`-storage functional path, observed as IEEE binary32 on the audited AArch64/GCC build. It does **not** define a hardware multiplier's internal product width, guard bits, fused multiply-add behavior, denormal mode, exception flags, or per-stage rounding. Those behaviors inherit the C compiler, target ISA, and host floating-point environment. The build does not provide an independent explicit software implementation of binary32 arithmetic.

Accumulation also has two source-level groups. Each K tile forms a local `psum`; the tile result is then added to O. Changing K tiling can change grouping and therefore host evaluation. O is a persistent four-byte host-`float` SRAM region. DMA store is raw `memcpy`; it does not narrow O to FP16. A caller that allocates or interprets O as FP16 violates the storage contract even if the instruction is called FP16 MMA.

Other operator families reinforce the path-specific rule. Attention explicitly narrows selected data through the canonical FP16 converter. Pooling interprets its two-byte floating values as FP16 and cannot distinguish BF16. Softmax, normalization, elementwise, and the current convolution paths use independent FP32 or double implementations. None dynamically specializes from precision-registry lookup. Precision should eventually be explicit in operation descriptors, storage layouts, arithmetic kernels, and output conversion boundaries.

## 8.11 Multi-objective precision choices

| Choice | Potential gain | Numerical cost | Hardware/control cost | Compiler and verification cost |
|---|---|---|---|---|
| binary16 inputs, FP32 accumulate | halves input storage versus FP32 while retaining wider sums | narrow input range; conversion and subnormal policy matter | wider accumulator and conversion logic | calibration, loss scaling or clipping may be needed |
| BF16 inputs, FP32 accumulate | FP32-like exponent range with 16-bit storage | only seven explicit fraction bits | similar storage width to FP16; different multiplier precision | graph export must preserve BF16 rather than silently pass through FP16 |
| E4M3 | better precision per FP8 value | limited range and format-variant ambiguity | scaling metadata and overflow policy | exact encoding table must be selected end to end |
| E5M2 | wider FP8 range and infinities | only two explicit fraction bits | scaling and special-value handling | often different tensor roles from E4M3 |
| TF32-like multiply, FP32 accumulate | FP32 range with smaller multiplier significand | products lose low significand bits | 32-bit storage unless compressed; specialized multiplier | API must distinguish storage from compute precision |
| FTZ | simpler/faster tiny-value handling on some designs | discontinuity and possible loss of small gradients/signals | may reduce normalization/exception complexity | must be explicit and tested at boundaries |
| gradual underflow | smoother behavior near zero | more datapath cases | leading-zero normalization and rounding complexity | larger raw-bit test space |
| stochastic rounding | can reduce systematic narrowing bias | nondeterministic individual results | PRNG state, distribution, lane correlation | seed/order contract and statistical tests required |

No row is universally best. The regime includes tensor distributions, scaling strategy, reduction length, acceptable error, bandwidth boundary, area/power budget, reproducibility requirement, and compiler support. Tusim can expose these alternatives for pre-spec exploration, but only after each alternative reaches executable operation descriptors and discriminating tests.

Mixed-precision training techniques such as loss scaling and FP32 master weights are workload methods, not universal accuracy guarantees ([MIC18](../../references/floating-point.md#mic18-mixed-precision-training)). FP8 format studies similarly motivate alternatives without proving Tusim behavior ([MIC22](../../references/floating-point.md#mic22-fp8-formats)).

## 8.12 Executable evidence matrix

The evidence bundle separates **conformance checks** from a **pinned known-defect snapshot**. Canonical FP16 widening is checked against a separately written exact-bit oracle. All 256 E4M3 and all 256 E5M2 raw decoder codes are checked against OFP8/E5M2 tables; pinned E4M3 has 14 finite-code disagreements and E5M2 has zero. The WS/OS/RS execution result is intentionally a snapshot: a full-domain digest plus named counts and raw vectors must change when the implementation is repaired. Calling the snapshot “standards-conformant” would be wrong; calling it snapshot-closed at the pinned revision is precise.

The recorded AArch64/GCC 11.4.0 run establishes:

| Boundary family | Executed vectors | Main observed result |
|---|---|---|
| FP16 decode | all 65,536 codes | canonical 0 mismatches |
| engine-local FP16 decode | all 63,486 finite nonzero codes per WS/OS/RS plus full-domain digest | 1,982 subnormal mismatches each; no normal mismatches |
| FP8 decode | all 256 raw codes per E4M3/E5M2 | 14 OFP8 E4M3 disagreements; 0 E5M2 disagreements |
| signed zero | selected FP16, BF16, FP8, TF32-like conversions | conversion sign generally preserved; later arithmetic is separate |
| subnormal boundaries | selected half-min, min/max, neighbors, and subnormal/normal midpoints | policies differ; FP16 full mode and FP8 carries defective |
| normal boundaries | selected min normal and max finite | canonical decode exact; E4M3 encode/decode not closed |
| infinities | selected formats that represent them | FP16/E5M2/TF32-like tested; E4M3 overflow maps to NaN |
| NaNs | selected quiet and low-payload signaling examples | payload/sign canonicalization and NaN-to-infinity cases observed |
| ties | selected even/odd retained-bit cases and FP8 ordinary/underflow cases | FP16/BF16/TF32-like selected ties even; FP8 ties upward |
| overflow | selected FP16, E4M3, and E5M2 RNE/RTZ cases | E5M2 60,000 incorrectly overflows under RNE and RTZ |
| configuration | nondefault JSON precision/rounding/subnormal/saturate fixture | canonical fields parse; runtime initialization leaves RNE/flush active |

Outside exhaustive FP16/FP8 decoding, this is a boundary matrix, not exhaustive format conformance. Engine-local execution excludes zeros and exponent-all-ones codes because MAC arithmetic changes signed-zero/NaN questions. Stochastic behavior is covered only by existing suites, not by the chapter probe. Arithmetic grouping, FMA contraction, cancellation, and multi-term K behavior remain source/toolchain interpretations rather than independent Chapter 8 bit-level experiments.

The matrix never calls a NaN payload correct merely because `isnan()` returns true. It checks raw encodings where stable and avoids using normal-value equality to infer subnormal behavior. The FP16 oracle is independent code but not an external SoftFloat/MPFR implementation; that limitation remains explicit.

## 8.13 Why the existing tests pass

Focused tests remain useful, but their claim scopes are narrower than their names. Reported `19/19`, `21/21`, and `11/11` values are program-defined test groups, not comparable coverage units or independent statistical validations.

1. `test-cmodel` checks selected round trips and normal-value MMA cases. Its subnormal case expects default FTZ.
2. `test-bf16` compares signed zeros with floating equality, which cannot distinguish `+0` from `-0`; its BF16 tests omit raw subnormal narrowing.
3. Its “full mode” FP16 test only checks that the result is positive and below a loose threshold, so the wrong `0x0200` passes.
4. `test-rounding` labels `3.00048828125` as halfway around 3.0, but FP16 spacing there is `0.001953125`; the fixture is one-quarter ULP, not a tie.
5. `test-fp8` permits a very broad E4M3 max-normal round trip and encodes the implementation's 240 policy into the test. Its `ASSERT_NEAR` also accepts NaN because an unordered comparison never enters the failure branch.
6. Several FP8 relative-error checks use an absolute-like denominator of one near zero, weakening subnormal discrimination.
7. `test-tf32` checks ordinary NaN but not low-payload signaling NaN; it is also absent from aggregate `make test`.
8. Golden MMA testing compares selected random normals under tolerances. It does not enumerate raw encodings or independently control host arithmetic rounding.
9. `test-full` is not a superset of `test`; generated-code compile and execution commands are made non-gating with `|| true`.

A passing suite proves its assertions, not the comments surrounding them. Raw-bit boundary tables should accompany tolerance-based end-to-end tests.

## 8.14 Fidelity box

> **Executable:** canonical FP16/BF16, Tusim E4M3-like/E5M2, and TF32 conversion APIs; global rounding setters; FP16 subnormal setter; precision registry; direct FP16-input/FP32-accumulate MMA; focused suites and Chapter 8 probe.
>
> **Integrated:** direct precision-specific APIs are publicly reachable. BF16/FP8/TF32 selection and precision JSON policy are **not integrated** into direct MMA.
>
> **Functional model:** multiply and add use C `float`; exact evaluation details are host/compiler-dependent. Tusim does not independently model product width, FMA contraction, floating exception flags, or cycle-by-cycle arithmetic.
>
> **Executable defects:** FP16 full-mode narrowing, engine-local FP16 subnormal widening, E4M3 finite range/closure, FP8 tie/carry/overflow handling, BF16/TF32 low-payload signaling NaNs, and config propagation.
>
> **Calibration:** none against RTL or silicon. Throughput, area, power, and energy consequences of precision choices are not established by these conversion tests.

## 8.15 Common failure modes

1. **One label for many contracts.** “FP16” does not specify input FTZ, product width, accumulator width, output storage, or rounding.
2. **Registry equals execution.** A descriptor callback proves conversion reachability, not engine dispatch.
3. **Pairwise equality equals correctness.** WS/OS/RS share the same local defect.
4. **Tolerance hides boundaries.** A broad relative or absolute threshold can accept the wrong raw code.
5. **Floating equality checks signed zero.** `+0.0 == -0.0`; inspect bits or `signbit`.
6. **`isnan` proves payload preservation.** It does not check sign, quiet/signaling state, or payload.
7. **One global mode controls everything.** Tusim's formats and local helpers consult different state—or none.
8. **Format name implies standard variant.** E4M3 encodings differ; cite the exact table.
9. **Conversion test proves arithmetic.** Widen/narrow callbacks do not exercise a multiplier.
10. **FP16 operation means FP16 output bytes.** Tusim O storage is FP32 and DMA is raw.
11. **Host float equals target hardware.** Compiler contraction, denormal controls, and exception behavior require explicit contracts.
12. **Passing aggregate covers all focused tests.** TF32 is omitted from pinned aggregate `make test`; `test-full` is neither a superset nor fail-closed for generated-code stages.

## 8.16 Development questions exposed by the audit

1. Should every operation descriptor separately name input storage, product, accumulator, and output storage precision?
2. Should one canonical binary16 decoder replace all engine-local copies?
3. Should FP16 full subnormal support be repaired with an exhaustive encode oracle before being advertised?
4. Which exact FP8 standard/variant should Tusim implement, and should alternative E4M3 encodings be explicit modes?
5. Should unsupported precision requests fail rather than fall back through an FP16 bridge?
6. How should rounding, saturation, FTZ, and NaN policy propagate from JSON to runtime, cores, DPI, command queues, and compiler output?
7. Should floating exception/status flags be modeled, ignored explicitly, or exposed as an optional verification mode?
8. Is stochastic state per process, core, tensor, lane, or instruction, and what reproducibility contract should the compiler see?
9. How should the model prevent a BF16-to-FP16 bridge test from being reported as BF16 MMA?
10. Which numerical experiments would reveal accuracy/overflow trade-offs without conflating them with unmodeled throughput or energy?
11. Should precision-registry lookup reject negative enum values before indexing, and which public test should enforce that rule?
12. Should aggregate `make test` include every focused precision suite, and should `test-full` permit any non-gating `|| true` stage?

## Summary

- A format is a representation; it is not an arithmetic pipeline.
- On the audited AArch64/GCC build, Tusim's direct MMA is FP16 W/A storage widened to host `float`, accumulated and stored in four-byte host-`float` O.
- The canonical FP16 decoder is exact over all 65,536 encodings.
- Canonical FP16 narrowing defaults to FTZ; its optional full-subnormal path is defective at audited boundaries.
- All three dataflow-local decoders share another subnormal defect: 1,982 of 2,046 nonzero signed subnormal codes disagree with the oracle.
- BF16, FP8, and Tusim TF32-like conversion APIs execute, but direct MMA does not select those input formats.
- E4M3 encoding semantics, FP8 ties, and BF16/TF32 signaling-NaN handling disagree with broad source comments.
- Precision configuration is parsed but dropped before runtime.
- Existing tests pass because they cover useful ordinary cases but use incomplete raw-bit boundaries or broad tolerances.
- Architecture exploration must compare numerical quality, storage, bandwidth, area, energy, control, compiler impact, and verification burden under an exact precision contract.

## Review questions

1. Two implementations agree on every normal FP16 input but disagree on subnormals. What evidence is required before calling them numerically equivalent?
2. Why can a BF16 registry entry coexist with an FP16-only MMA engine without contradiction?
3. Explain how `+0.0 == -0.0` can let a signed-zero regression pass.
4. Why is `isnan(result)` insufficient for testing NaN conversion?
5. A global mode is named RNE. Which source paths must be audited before claiming all conversions use RNE?
6. Why does FP32 accumulation not by itself define product precision or fused multiply-add behavior?
7. What is unsafe about interpreting a BF16-to-FP16 bridge as BF16 hardware execution?
8. How can all three dataflow plug-ins agree bitwise and still all be wrong?

### Review-question answer key

1. Enumerate the excluded raw domains—especially subnormals and special values—against an independent oracle before claiming equivalence.
2. A registry establishes named conversion reachability; MMA selection is a separate dispatch and storage contract.
3. IEEE comparisons make both zeros equal, so inspect raw sign bits or use `signbit`.
4. `isnan` does not test sign, payload, or quiet/signaling state.
5. Audit every canonical converter, bridge, engine-local helper, special path, and configuration propagation point.
6. Accumulator storage width says nothing about product width, intermediate rounding, contraction, or grouping.
7. The bridge executes BF16 conversion followed by an FP16 engine path; it does not demonstrate BF16 arithmetic.
8. Shared copied code can reproduce the same defect in every plug-in.

## Design exercises

1. **Exhaustive encoder oracle.** Design a binary32-to-binary16 test that samples every transition between adjacent binary16 values under RNE and RTZ. State how you avoid dependence on the implementation under test.
2. **Precision descriptor redesign.** Extend an MMA descriptor with storage, product, accumulator, and output precision. Define rejection rules for unsupported combinations.
3. **FP8 variant contract.** Compare two E4M3 encoding tables. Specify enum names, conversion rules, overflow behavior, and golden vectors that prevent accidental substitution.
4. **Stochastic reproducibility.** Propose per-core and per-instruction PRNG state semantics. Analyze area, parallel-lane correlation, replay, and compiler implications.
5. **Subnormal trade-off study.** Construct tensor distributions where FTZ is harmless, harmful, or beneficial. Keep numerical effects separate from any assumed latency/energy gain.
6. **Mixed-precision reduction.** Compare FP16, BF16, and TF32-like inputs with FP32 accumulation over increasing K. Define error metrics and adversarial cancellation cases.
7. **NaN policy.** Specify payload, sign, signaling/quiet conversion, exception flags, and canonicalization for every format boundary in a proposed accelerator.

## Primary references

- **[IEEE19]** IEEE, *IEEE Standard for Floating-Point Arithmetic*, IEEE Std 754-2019, 2019. DOI: [10.1109/IEEESTD.2019.8766229](https://doi.org/10.1109/IEEESTD.2019.8766229). Use for binary interchange formats, rounding directions, subnormals, infinities, NaNs, and exception concepts; it does not validate Tusim conformance.
- **[KAL19]** Dhiraj Kalamkar et al., “A Study of BFLOAT16 for Deep Learning Training,” arXiv:1905.12322, 2019. <https://arxiv.org/abs/1905.12322>. Use for BF16 motivation and training evidence, not Tusim's conversion policy.
- **[MIC22]** Paulius Micikevicius et al., “FP8 Formats for Deep Learning,” arXiv:2209.05433, 2022. <https://arxiv.org/abs/2209.05433>. Use for E4M3/E5M2 design motivation and evaluated conventions; exact encodings must still be checked against the chosen specification.
- **[GTPU]** Google Cloud, “Improve your model's performance with bfloat16.” [Official documentation](https://cloud.google.com/tpu/docs/bfloat16). Use only for TPU-specific BF16 behavior.
- **[OCP23]** Open Compute Project, *OCP 8-bit Floating Point Specification (OFP8)*, Revision 1.0, 2023. [Official catalog record](https://www.opencompute.org/documents/ocp-8-bit-floating-point-specification-ofp8-revision-1-0-2023-06-20-pdf). Use for scalar OFP8 encodings and conversion policy.
- **[OCP-MX23]** Open Compute Project, *OCP Microscaling Formats (MX) Specification*, Version 1.0, 2023. [Official specification](https://www.opencompute.org/documents/ocp-microscaling-formats-mx-v1-0-spec-final-pdf). Use for block scaling, not as the scalar OFP8 primary source.
- **[NVI20]** NVIDIA, *NVIDIA A100 Tensor Core GPU Architecture*, 2020. [Official white paper](https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/nvidia-ampere-architecture-whitepaper.pdf). Use for the documented TF32 product context and mixed-precision hardware motivation; NVIDIA implementation evidence does not transfer to Tusim.
- **[MIC18]** Paulius Micikevicius et al., “Mixed Precision Training,” ICLR 2018, arXiv:1710.03740. <https://arxiv.org/abs/1710.03740>. Use for FP16 training techniques and FP32 accumulation/master-weight motivation, not as a universal accuracy guarantee.
