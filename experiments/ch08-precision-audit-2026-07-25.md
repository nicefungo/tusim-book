# Chapter 8 Precision Audit — 2026-07-25

- **Tusim edition:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Execution tree:** `/tmp/tusim-ch08-reproduction`, extracted from verified `git archive`
- **Archive SHA-256:** `fb023fe79a0e7dafbf334848756e44127101f5fdb75c1004e2ed2712318b708f`
- **Calibration:** none; results are host-executed functional/conversion evidence on AArch64 GCC 11.4.0

## Audit question

Do Tusim's canonical and engine-local paths implement one coherent floating-point contract across representation, conversion, arithmetic, accumulation, storage, rounding, special values, and subnormal policy?

**Answer:** no. Several individually executable contracts coexist. Their agreements and disagreements must be reported separately.

## Reproduction

```bash
cd /home/zxy/Workplace/books/tusim-book
bash experiments/ch08_reproduce.sh
```

The script verifies detached/clean source state and exact revision, records the ignored-file inventory, validates the tracked external symlink while leaving it unused, creates and hashes a deterministic archive, extracts to `/tmp`, writes a provenance marker, checks 17 claim-critical hashes and structural contracts, builds only in the extraction, runs focused suites and the chapter probe, rejects shared Tusim linkage, hashes evidence artifacts, and rechecks tracked/nonignored state plus ignored inventory. Complete stdout/stderr is preserved in `ch08-reproduction-2026-07-25.log`.

## Observed gates

- enforced source audit: 17/17 hashes pass;
- clean static archive build: pass with two pre-existing unused-symbol warnings;
- `test-cmodel`: 19/19;
- `test-config`: 20/20;
- `test-bf16`: 12/12;
- `test-rounding`: 14/14;
- `test-fp8`: 21/21;
- `test-tf32`: 25/25;
- `test-dataflow`: 9/9;
- `test-golden --quick`: 11/11, maximum reported error 0.002702;
- raw-bit probe: `SUMMARY: PASS failures=0`;
- nine `ldd` gates in an archive-only tree: no `libtucmodel.so` dependency;
- source checkout remained clean and detached;
- final transcript line: `REPRODUCTION: PASS`.

## Raw-bit probe stdout

The probe combines independent conformance checks with a pinned `KNOWN_DEFECT_SNAPSHOT`. The latter is regression/snapshot-closed, not correctness-closed: a repair is expected to fail until the recorded snapshot and prose are deliberately updated.

```text
FP16_DECODE canonical_exhaustive=65536 mismatches=0 pos_zero=00000000 neg_zero=80000000 min_sub=33800000 max_sub=387fc000 min_norm=38800000 max_norm=477fe000 pos_inf=7f800000 qnan=7fc00000 snan=7fa00000
KNOWN_DEFECT_SNAPSHOT name=weight_stationary finite_vectors=63486 mismatches=1982 subnormal_mismatches=1982 normal_mismatches=0 min_sub_got=38800000 second_sub_got=38000000 min_sub_expected=33800000 second_sub_expected=34000000 nonmonotonic=1 digest=d56431612d444f4d
KNOWN_DEFECT_SNAPSHOT name=output_stationary finite_vectors=63486 mismatches=1982 subnormal_mismatches=1982 normal_mismatches=0 min_sub_got=38800000 second_sub_got=38000000 min_sub_expected=33800000 second_sub_expected=34000000 nonmonotonic=1 digest=d56431612d444f4d
KNOWN_DEFECT_SNAPSHOT name=row_stationary finite_vectors=63486 mismatches=1982 subnormal_mismatches=1982 normal_mismatches=0 min_sub_got=38800000 second_sub_got=38000000 min_sub_expected=33800000 second_sub_expected=34000000 nonmonotonic=1 digest=d56431612d444f4d
FP16_ENCODE rne_tie=3c00 overflow_tie=7c00 full_min_sub=0200 full_max_sub=0200 full_half_min=0200 full_above_half=0200 full_below_normal_mid=0200 full_mid_normal=0200 full_above_normal_mid=0200 ftz_mid_normal=0000 rtz_70000=7c00 neg_nan=7e00
BF16 decode_min_sub=00010000 encode_min_sub=0000 boundary_mid=0080 tie=3f80 qnan=7fc0 low_payload_snan=7f80
FP8 exhaustive_raw=256 e4_ofp8_decode_mismatches=14 e5_decode_mismatches=0 e4_decode_78_isnan=1 e4_encode_240=7f e4_encode_448=7f e4_tie=39 e4_half_min=01 e4_subnormal_normal_mid=07 e5_max=7b e5_overflow=7c e5_rtz_overflow=7c e5_tie=3d e5_half_min=01 e5_subnormal_normal_mid=03
TF32 neg_zero=80000000 tie=3f800000 min_sub=00002000 half_min=00000000 qnan=7fc00000 low_payload_snan=7f800000 masked_decode=3f800000
REGISTRY builtin_count=8 ordered_entries=PASS execution_dispatch_not_implied=1
CONFIG_EXEC parsed_bf16=1 parsed_fp8_e5m2=1 parsed_rounding=RTZ parsed_subnormal=FULL parsed_saturate=1 runtime_rounding=RNE runtime_subnormal=FLUSH precision_dispatch_absent=1
SUMMARY: PASS failures=0
```

## Interpretation by contract

### Representation and conversion

The canonical FP16 decoder exactly reproduces an independent bit-construction oracle for every input code. This does not extend to narrowing: default FTZ removes values based on the pre-round source region, and optional full mode collapses the expanded half-minimum through normal-boundary matrix to `0x0200`.

BF16 widening is exact left-shift representation. BF16 narrowing flushes all subnormal outputs independently of FP16 mode. FP8 and TF32 use their own local narrowing logic. There is no universal converter policy.

### Engine-local disagreement

The probe exercises each plug-in's actual `execute_tile` callback with one operand set to raw binary16 codes and the other to one. It excludes zero and exponent-all-ones codes from the finite exact comparison because the subsequent multiply/add has separate signed-zero and NaN behavior. Each plug-in disagrees for 1,982 of 2,046 nonzero signed subnormals and for no normal code. A full-domain digest covers every input/actual/expected tuple, so a different defect set with the same count fails the snapshot. The 64 agreeing subnormal codes are accidental properties of the local formula. The mapping is non-monotonic: raw `0x0001` decodes as `2^-14`, while larger `0x0002` decodes as `2^-15`.

### Rounding

Canonical FP16, BF16, and TF32 selected even- and odd-retained-bit midpoint vectors reproduce RNE tie-to-even. FP8 uses `+0.5` then truncation and rounds selected ordinary and half-minimum halfway vectors upward; its subnormal/normal midpoint clamps below the boundary instead of carrying. RTZ is not a complete overflow policy: canonical FP16 maps finite 70,000 to infinity before mode-specific rounding, and E5M2 maps 60,000 to infinity under RTZ.

### Special values

Canonical FP16 narrowing canonicalizes all NaNs to positive `0x7e00`, losing sign and payload. BF16 and TF32 mask/copy high bits, so a signaling NaN with payload only in discarded bits becomes infinity. The model exposes no coherent exception flags. E4M3 uses NaN as overflow and treats all exponent-15 codes as NaN.

### Arithmetic, accumulation, and storage

The direct plug-ins widen W/A, evaluate host `float` product/add expressions, accumulate a local FP32 psum, and add it to FP32 O. K tiling defines grouping. No explicit target product-width, FMA-contraction, exception, or denormal-control model exists. O DMA is raw FP32 storage, not implicit FP16 conversion.

### Selection and configuration

The precision registry has eight correctly ordered descriptors and conversion callbacks. Direct MMA has no precision selector and hardcodes FP16 W/A plus host-`float` O. The probe executes a nondefault JSON fixture: BF16/E5M2 selection, RTZ, full subnormal, and saturation parse canonically, while runtime initialization leaves global RNE/flush active. Static inspection explains this by showing the fields absent from `tu_config_to_runtime`. TF32's focused target exists but is omitted from aggregate `make test`.

## Existing-test challenge

All focused suites pass, but several assertions are too weak for broad claims:

- floating equality cannot distinguish signed zeros, and several `ASSERT_NEAR` implementations accept NaN as success;
- BF16 tests omit raw subnormal narrowing;
- FP16 full-mode tests check only a loose positive range;
- FP8 max-normal testing allows broad ambiguity;
- FP8 stochastic testing uses exactly representable 1.5 with a wide tolerance;
- ordinary `NAN` does not test signaling/payload boundaries;
- random golden vectors do not enumerate raw encodings;
- aggregate test omission leaves TF32 dependent on explicit execution;
- `test-full` is not a superset and suppresses generated-code failures.

These tests remain useful for ordinary-path regression. The Chapter 8 matrix adds a different gate rather than replacing them.

## Safe conclusion

At the pinned revision and audited AArch64/GCC build, Tusim has executable precision conversion modules and an FP16-storage/host-`float`-arithmetic/host-`float`-storage direct MMA path. It does not have one unified floating-point policy or generic multi-precision MMA. Canonical FP16 widening is strong; several narrowing, subnormal, FP8, signaling-NaN, selection, and configuration contracts disagree. No RTL/silicon calibration or precision-dependent performance, area, power, or energy evidence is established.
