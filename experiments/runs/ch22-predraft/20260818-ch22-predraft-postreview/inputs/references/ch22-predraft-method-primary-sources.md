# Chapter 22 predraft method-source map

Verification date: 2026-08-18
Scope: evidence filtering and decision qualification before Chapter 22 prose
Status: source metadata reused from the verified Chapter 21 ledger; no source supplies Tusim-specific numerical results

## Reused verified source surfaces

| Method need | Primary source | Safe use here | Limitation here |
|---|---|---|---|
| Multiobjective qualification | K. Deb et al., “A fast and elitist multiobjective genetic algorithm: NSGA-II,” DOI 10.1109/4235.996017 | A local nondominated statement requires declared objectives, constraints, alternatives, and a preference rule. | The paper does not validate Tusim estimates or permit a frontier across incompatible metric domains. Chapter 22 does **not** build a portfolio-wide Pareto frontier. |
| Workload representativeness | L. Eeckhout et al., “Designing computer architecture research workloads,” DOI 10.1109/MC.2003.1178050 | Keep workload and regime boundaries explicit; do not transfer one report’s ordering to omitted shapes or traffic distributions. | Characterization remains limited to selected features, inputs, phases, and systems. |
| Aggregation discipline | P. Fleming and J. Wallace, “How not to lie with statistics,” DOI 10.1145/5666.5673 | Preserve per-regime evidence and name any denominator. | No mean makes heterogeneous counters commensurate; Chapter 22 performs no cross-domain scalarization. |
| Measurement pitfalls | A. Mytkowicz et al., “Producing wrong data without doing anything obviously wrong!,” DOI 10.1145/1508244.1508275 | Treat uncontrolled state and repeat variation as negative evidence rather than averaging it away. | The paper does not identify Tusim’s specific defects or authorize a causal diagnosis. |
| Reproducible packaging | G. Wilson et al., “Ten Simple Rules for Reproducible Computational Research,” DOI 10.1371/journal.pcbi.1003285; RFC 8493 | Pin source identity, preserve raw logs, hash artifacts, and make verification machine-checkable. | Packaging proves identity and integrity, not physical accuracy or representativeness. |
| Compute/supply boundary | S. Williams, A. Waterman, and D. Patterson, “Roofline,” DOI 10.1145/1498765.1498785 | Use a named byte boundary and compute/supply constraint as an upper-bound interpretation. | Roofline is not a Tusim latency simulator and does not compose arbitrary report counters. |

## Local verification anchors

- `references/ch21-primary-source-verification-ledger.json`, SHA-256 `919c6d945be1efad40730800f68da27ab5fa94bcdf1ac6e9768f488fb1b36866`
- `references/ch21-sweep-method-primary-sources.md`, SHA-256 `018ecdee678256cb1096f2ed6300a8caf82bb8792260688a8abd08c5c6f26cfb`
- `references/foundations.md`, SHA-256 `433cd0eb2d60f98b18de63ebeeba43a1727858329612668132620d0f66500120`

The Chapter 21 source map’s line 62 assigned Chapter 22 portfolio-wide Pareto selection. The closed Chapter 22 framing supersedes that assignment: comparisons remain local to one declared, complete metric domain; missing decisive dimensions force an `open` outcome.

## Boundary

These sources qualify method only. The 46 pinned exploration reports and focused linked probes supply the Tusim evidence. None supplies calibrated silicon timing, area, power, energy, application-level accuracy, or an executable compiler/runtime/ONNX composition bridge.

Sparse-placement sensitivity and NoC traffic-shape reversals are therefore used only as pinned Tusim-local observations under their current chapter ledgers. This package makes no literature-backed universal claim from them; any broader methodological generalization requires dedicated primary sources and a new review.
