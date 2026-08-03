# Chapter 8 Source and Claim Ledger

- **Edition:** Tusim `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Manuscript:** [`../manuscript/part-2-core/08-floating-point-foundations.md`](../manuscript/part-2-core/08-floating-point-foundations.md)
- **Audit:** [`../experiments/ch08-precision-audit-2026-07-25.md`](../experiments/ch08-precision-audit-2026-07-25.md)
- **Probe:** [`../experiments/ch08_precision_probe.c`](../experiments/ch08_precision_probe.c)
- **Enforced source audit:** [`../experiments/ch08_precision_audit.py`](../experiments/ch08_precision_audit.py)
- **Reproducer/transcript:** [`../experiments/ch08_reproduce.sh`](../experiments/ch08_reproduce.sh), [`../experiments/ch08-reproduction-2026-07-25.log`](../experiments/ch08-reproduction-2026-07-25.log)
- **References:** [`../references/floating-point.md`](../references/floating-point.md)

## Reader decision

Given a precision label, determine the executable representation, conversion, arithmetic, accumulation, storage, rounding, special-value, subnormal, overflow/saturation, and selection contracts before making numerical or hardware claims.

## Contract ledger

| Contract | Pinned direct-MMA behavior | Unsafe inference |
|---|---|---|
| representation | W/A raw 16-bit binary16-intended; O four-byte host `float` (binary32 on audited build) | every registry format is accepted by MMA |
| conversion | canonical FP16 decoder plus three local copies | one global conversion policy |
| arithmetic | host C `float` multiply/add after widening | explicit target product/FMA semantics |
| accumulation | host-`float` local psum plus host-`float` O update per K tile | FP16 accumulation, target-hardware FMA, or one rounding interval |
| storage | W/A 2 bytes, O 4 bytes; DMA raw copies | FP16 output because operation is named FP16 |
| rounding | setters affect selected converters | JSON or one mode controls all paths |
| special values | path-specific canonicalization/masking | payload/sign/exception preservation |
| subnormals | default FP16 FTZ; defective full path; local decoder disagreement | IEEE gradual underflow everywhere |
| overflow/saturation | path-specific; parsed saturation is dropped | one active saturation policy |
| selection | registry callbacks and direct APIs | engine precision dispatch |

## Claim ledger

| Claim | Evidence | Label and safe boundary |
|---|---|---|
| canonical FP16 decoding is exact | independent exhaustive 65,536-code oracle | executable conversion result only |
| WS/OS/RS use canonical FP16 decoding | contradicted by source and exhaustive probe | rejected |
| local decoders agree for arbitrary finite FP16 | 1,982/63,486 finite-nonzero mismatches versus oracle per plug-in | rejected; normal codes audited with zero mismatch |
| `TU_SUBNORMAL_FULL` provides full FP16 support | nine boundary vectors collapse to `0x0200` | rejected; executable defect |
| one subnormal mode controls BF16/FP8/TF32/MMA | source/state audit | rejected |
| BF16 conversion is executable | focused test, registry, probe | executable conversion; no BF16 MMA |
| FP8 modules conform to one OCP policy | exhaustive 256-code decoder census: 14 E4M3 OFP8 disagreements, zero E5M2 disagreements; encoder boundaries | rejected for E4M3; E5M2 decode only established exhaustively |
| FP8 RNE is tie-to-even | raw halfway vectors | rejected; tested ties round upward |
| FP8 subnormal rounding carries into minimum normal | E4M3/E5M2 boundary midpoints | rejected; result clamps below boundary |
| E5M2 RTZ overflow retains max finite | 60,000 under RTZ | rejected; returns infinity |
| TF32 is executable | focused conversion test and registry | conversion only; no TF32 multiply path |
| NaNs are preserved | low-payload signaling NaNs become infinity in BF16/TF32 | qualified/rejected as universal claim |
| precision JSON controls execution | executed nondefault parse/init fixture plus parser-to-runtime audit | rejected; fields parse and are dropped |
| focused precision tests are aggregate-covered | Makefile audit | BF16/rounding/FP8 yes; TF32 no |
| direct MMA stores FP16 output | source byte widths and Chapter 6 evidence | rejected; O is FP32 raw storage |
| precision registry rejects every invalid enum | source guard inspection | rejected for negative values; not executed because current path invokes undefined behavior |

## Exact raw-bit results

- canonical FP16 decode: 65,536 vectors, zero mismatches;
- each local WS/OS/RS path: 63,486 finite nonzero vectors, 1,982 mismatches, all in subnormal codes; 0 normal mismatches; digest `d56431612d444f4d` over every input/actual/expected tuple;
- raw FP16 `0x0001`: canonical `0x33800000` (`2^-24`), local `0x38800000` (`2^-14`);
- FP16 full-mode min/max tested subnormal encodes: both `0x0200`;
- FP16 half-minimum tie, one-bit-above tie, `2^-16`, and the below/mid/above subnormal-normal midpoint vectors all encode `0x0200`; FTZ maps all three boundary-neighbor vectors to zero before two can round to normal;
- BF16 representable minimum subnormal narrows to zero; the subnormal-normal midpoint carries to `0x0080`; low-payload sNaN narrows to infinity;
- E4M3 `0x78` decodes NaN; 240 and 448 encode `0x7f`; midpoint 1.0625 encodes `0x39`; subnormal/normal midpoint encodes `0x07` rather than `0x08`;
- E5M2 maximum 57,344 encodes `0x7b`; 60,000 encodes infinity under RNE and RTZ; midpoint 1.125 encodes `0x3d`; subnormal/normal midpoint encodes `0x03` rather than `0x04`;
- TF32 minimum retained subnormal raw input `0x00002000` survives; half-minimum ties to zero; low-payload sNaN becomes infinity.

## Primary-source scopes

- **[IEEE19]:** representation, rounding, subnormal, infinity, NaN, and exception vocabulary; not evidence of Tusim conformance.
- **[KAL19]:** BF16 motivation and evaluated training context; not Tusim engine evidence.
- **[MIC22]/[OCP23]:** FP8 motivations and normative OFP8 scalar contracts; Tusim's E4M3 disagreement must remain visible. **[OCP-MX23]** is separate block-scaling context.
- **[NVI20]:** TF32 hardware/product context; does not validate Tusim conversion or arithmetic.
- **[MIC18]:** mixed-precision training methods; not a universal accuracy guarantee.

## Open development questions

1. How should operation descriptors separately select storage, product, accumulator, and output precision?
2. Should every engine call one canonical converter?
3. Which exact FP8 variants should be explicit alternatives?
4. How should numerical policy propagate from config to cores, DPI, command queues, and compiler output?
5. What host-independent arithmetic oracle and floating-status model are appropriate?
6. What stochastic-state scope provides reproducibility without unrealistic lane correlation?
