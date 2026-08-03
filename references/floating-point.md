# Floating-Point Primary Sources

These entries support Chapter 8. Standards and papers define vocabulary, formats, or evaluated designs; none proves Tusim conformance.

## [IEEE19] IEEE 754-2019

IEEE, *IEEE Standard for Floating-Point Arithmetic*, IEEE Std 754-2019, 2019. DOI: [10.1109/IEEESTD.2019.8766229](https://doi.org/10.1109/IEEESTD.2019.8766229).

**Metadata check:** Crossref returned the title “IEEE Standard for Floating-Point Arithmetic,” publisher IEEE, and DOI `10.1109/ieeestd.2019.8766229` on 2026-07-25.

**Safe use:** binary interchange representation, rounding directions, signed zero, subnormals, infinity, NaN, and exception vocabulary. The standard does not show that Tusim implements these semantics.

## [KAL19] BFLOAT16 study

Dhiraj Kalamkar et al., “A Study of BFLOAT16 for Deep Learning Training,” arXiv:1905.12322, 2019. [Immutable arXiv record](https://arxiv.org/abs/1905.12322).

**Safe use:** BF16 motivation, range/precision trade-offs, and the paper's evaluated training setting. Do not transfer its accuracy results to Tusim or treat a BF16-to-FP16 bridge as BF16 execution.

## [GTPU] Google Cloud TPU bfloat16 behavior

Google Cloud, “Improve your model's performance with bfloat16.” [Official documentation](https://cloud.google.com/tpu/docs/bfloat16).

**Safe use:** TPU-specific BF16 operand/FP32-accumulation behavior, RNE conversion, and TPU BF16 subnormal flushing. These implementation choices are not universal properties of every BF16 implementation.

## [MIC22] FP8 formats

Paulius Micikevicius et al., “FP8 Formats for Deep Learning,” arXiv:2209.05433, 2022. [Immutable arXiv record](https://arxiv.org/abs/2209.05433).

**Safe use:** E4M3/E5M2 motivation, scaling context, and the paper's evaluated format choices. Exact encoding and overflow claims must name the selected standard variant.

## [OCP23] OCP 8-bit Floating Point (OFP8)

Open Compute Project, *OCP 8-bit Floating Point Specification (OFP8)*, Revision 1.0, approved 20 June 2023. [OCP catalog record](https://www.opencompute.org/documents/ocp-8-bit-floating-point-specification-ofp8-revision-1-0-2023-06-20-pdf); [official repository](https://github.com/opencomputeproject/FP8).

**Safe use:** normative E4M3/E5M2 scalar encodings, extrema, RNE conversion, and saturating/non-saturating overflow policy. Tusim's pinned E4M3 behavior disagrees at exponent-15 encodings and must not be called conformant.

## [OCP-MX23] OCP microscaling formats

Open Compute Project, *OCP Microscaling Formats (MX) Specification*, Version 1.0, 2023. [Official specification](https://www.opencompute.org/documents/ocp-microscaling-formats-mx-v1-0-spec-final-pdf).

**Safe use:** block-shared scaling and the distinction between OFP8 scalar elements and MXFP8 composite values. The chapter does not claim Tusim implements block scaling.

## [NVI20] NVIDIA A100 and TF32

NVIDIA, *NVIDIA A100 Tensor Core GPU Architecture*, 2020. [Official white paper](https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/nvidia-ampere-architecture-whitepaper.pdf); [CUDA Programming Guide TF32 section](https://docs.nvidia.com/cuda/cuda-programming-guide/index.html#tf32).

**Safe use:** official TF32 product/architecture context and motivation for reduced-precision products with FP32-range inputs/accumulation. NVIDIA implementation claims and quantitative results do not transfer to Tusim.

## [MIC18] Mixed-precision training

Paulius Micikevicius et al., “Mixed Precision Training,” ICLR 2018, arXiv:1710.03740. [Immutable arXiv record](https://arxiv.org/abs/1710.03740).

**Safe use:** FP16 training techniques, loss scaling, and FP32 accumulation/master-weight motivation in the evaluated setting. It is not a universal model-accuracy guarantee.
