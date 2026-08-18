# Chapter 21 — Primary Sources for Trustworthy Architecture Sweeps

- Verification date: 2026-08-18
- Scope: Chapter 21 experiment construction, sensitivity, workload selection, aggregation, multiobjective qualification, and reproducible packaging
- Method: exact metadata checked against Crossref/OpenAlex; each DOI resolved to its publisher record; publisher abstract or primary text inspected where accessible; RFC 8493 and Sandve et al. inspected directly

The sources below support method claims only. They do not validate Tusim semantics, calibrate its estimates, or authorize a portfolio conclusion.

## Experimental design and sensitivity

1. Engin İpek, Sally A. McKee, Karan Singh, Rich Caruana, Bronis R. de Supinski, and Martin Schulz, “Efficient architectural design space exploration via predictive modeling,” *ACM Transactions on Architecture and Code Optimization* 4(4), 2008, 1–34. DOI: [10.1145/1328195.1328196](https://doi.org/10.1145/1328195.1328196).
   - **Supports:** sampled architecture spaces and predictive models require validation; sampling, sensitivity, and prediction error are experiment properties.
   - **Limitation:** reported errors are study-specific. They do not authorize Tusim accuracy, arbitrary extrapolation, or substitution of a surrogate for boundary and counterexample runs.

2. Benjamin C. Lee and David M. Brooks, “Accurate and efficient regression modeling for microarchitectural performance and power prediction,” *ASPLOS XII*, 2006, 185–194. DOI: [10.1145/1168857.1168881](https://doi.org/10.1145/1168857.1168881).
   - **Supports:** explicit parameter selection, interactions, held-out validation, and sensitivity rather than one-factor storytelling.
   - **Limitation:** a fitted model approximates its sampled domain. Coefficients are not causal proof, and prediction does not prove mechanism reachability.

## Multiobjective and Pareto qualification

3. Kalyanmoy Deb, Amrit Pratap, Sameer Agarwal, and T. Meyarivan, “A fast and elitist multiobjective genetic algorithm: NSGA-II,” *IEEE Transactions on Evolutionary Computation* 6(2), 2002, 182–197. DOI: [10.1109/4235.996017](https://doi.org/10.1109/4235.996017).
   - **Supports:** conflicting objectives should retain a diverse nondominated set and state the preference rule separately.
   - **Limitation:** an algorithm does not prove estimated points accurate, feasible, representative, or reachable. “Nondominated” is only within the declared matrix, objectives, constraints, workloads, and fidelity.

## Workload representativeness and measurement pitfalls

4. Lieven Eeckhout, Hans Vandierendonck, and Koen De Bosschere, “Designing computer architecture research workloads,” *Computer* 36(2), 2003, 65–71. DOI: [10.1109/MC.2003.1178050](https://doi.org/10.1109/MC.2003.1178050).
   - **Supports:** select workloads by measured behavioral diversity and declare the dimensions intended to vary.
   - **Limitation:** characterization represents only selected features and source population, not omitted applications, inputs, phases, metrics, or future systems.

5. Aashish Phansalkar, Ajay Joshi, and Lizy K. John, “Analysis of redundancy and application balance in the SPEC CPU2006 benchmark suite,” *ISCA 2007*, 412–423. DOI: [10.1145/1250662.1250713](https://doi.org/10.1145/1250662.1250713).
   - **Supports:** established suites can contain redundancy and imbalance; state the workload denominator and test ranking survival across materially different cases.
   - **Limitation:** SPEC CPU2006 findings do not directly classify Tusim workloads or prove a subset preserves every ranking.

6. Philip J. Fleming and John J. Wallace, “How not to lie with statistics: the correct way to summarize benchmark results,” *Communications of the ACM* 29(3), 1986, 218–221. DOI: [10.1145/5666.5673](https://doi.org/10.1145/5666.5673).
   - **Supports:** retain per-workload rows and name the aggregation rule and denominator; arithmetic means of normalized ratios can mislead.
   - **Limitation:** the geometric mean is not universal and does not automatically apply to absolute time, energy, additive counts, differences, zeros, signed values, or heterogeneous metrics.

7. Todd Mytkowicz, Amer Diwan, Matthias Hauswirth, and Peter F. Sweeney, “Producing wrong data without doing anything obviously wrong!” *ASPLOS XIV*, 2009, 265–276. DOI: [10.1145/1508244.1508275](https://doi.org/10.1145/1508244.1508275).
   - **Supports:** record environment and toolchain, repeat or permute order where appropriate, and control hidden state.
   - **Limitation:** software-performance confounders do not prove every deterministic simulator has identical hazards and do not validate simulator semantics or metric ownership.

## Reproducible workflows and manifests

8. Geir Kjetil Sandve, Anton Nekrutenko, James Taylor, and Eivind Hovig, “Ten Simple Rules for Reproducible Computational Research,” *PLoS Computational Biology* 9(10), 2013, e1003285. DOI: [10.1371/journal.pcbi.1003285](https://doi.org/10.1371/journal.pcbi.1003285).
   - **Supports:** retain how results were produced, exact external-program versions, parameters, random seeds, intermediate results, and links from claims to results.
   - **Limitation:** these are general workflow rules, not a checksum-manifest format or proof that rerunning validates interpretation.

9. Victoria Stodden et al., “Enhancing reproducibility for computational methods,” *Science* 354(6317), 2016, 1240–1241. DOI: [10.1126/science.aah6168](https://doi.org/10.1126/science.aah6168).
   - **Supports:** identify and disclose data, code, workflow, and computational methods as separate evidence objects.
   - **Limitation:** availability and citation do not prove execution, numerical reproduction, mechanism reachability, or sufficiency for an architecture conclusion.

10. John Kunze, John Littman, Elizabeth Madden, John Scancella, and Carl Adams, *The BagIt File Packaging Format (V1.0)*, RFC 8493, 2018. DOI: [10.17487/RFC8493](https://doi.org/10.17487/RFC8493); official text: [RFC 8493](https://www.rfc-editor.org/rfc/rfc8493.html).
    - **Supports:** Sections 2.1.3, 2.2.1, and 3 distinguish complete payload manifests, tag manifests, completeness, and validity; this supports exact member sets and inner/outer integrity checks.
    - **Limitation:** RFC 8493 is Informational, not Standards Track. BagIt checks opaque octets: integrity is not scientific correctness, semantic provenance, active-attack security, reproducibility, or evidence sufficiency.

## Binding chapter allocation

- Chapter 17 owns producer identity, intervals, units, reset/clock assumptions, and metric fidelity.
- Chapter 20 defines evidence-authorization requirements; Chapter 21 constructs a sweep-specific package that applies them but cannot independently redefine or relax authorization.
- Chapter 21 owns controlled matrices, workload/alternative selection, sensitivity, counterexamples, and reproducible sweep packaging. Multiobjective/Pareto method qualification is introduced but not exercised in the retained worked cases.
- Chapter 22 alone owns preference rules, Pareto selection across the portfolio, and portfolio-wide conclusions about preferable Tusim architecture regimes.
- None of these sources supplies the missing executable compiler/runtime composition bridge.
