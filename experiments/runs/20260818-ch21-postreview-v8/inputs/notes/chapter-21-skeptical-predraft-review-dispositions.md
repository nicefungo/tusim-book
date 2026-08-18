# Chapter 21 — Skeptical Predraft Review Dispositions

- Review target: provisional commit `c77988eb0fce1ea46543dd11a3384754c7b24e4b`
- Provisional run: `experiments/runs/20260818-ch21-provisional-v1/`
- Review batch: `deleg_a023ce20`
- Full summaries reconciled: 3 of 3
- Disposition: **PASS for post-review reseal; provisional run superseded for drafting**
- Severity at review: **BLOCK 3 · MAJOR 11 · MEDIUM 2 · MINOR 5**
- Unresolved findings: **0**

`PASS for post-review reseal` does not itself authorize drafting. Authorization requires a fresh immutable post-review run, normal and optimized bundle-local validation, and a direct-child run-only Git seal.

## Source semantics and numerical review

1. **R1-1 · BLOCK · Report inventory regexes false/incomplete — RESOLVED.** Corrected the escaped heading/path expressions; inventory rows now derive question, hypothesis, method, explicit harness, reproduction command, parameter-matrix, equation, output-row, conclusion, CI-membership, producer class, and actual command fields. Exact classification counts and report-role mutation are validator gates.
2. **R1-2 · BLOCK · Three dataflow formula families conflated — RESOLVED.** C21.3, the report, formula probe, output JSON/CSV, and metric register now distinguish sweep-local 26,624/22,528/24,640, historical-report 21,536/21,504, and linked-plugin 81,920/20,480/50,176 producers.
3. **R1-3 · MAJOR · Metric ownership contract incomplete — RESOLVED.** Metric records are dimensionally singular and include source path, formula, interval/reset, numerator/denominator, units, clock, omissions, calibration, uncertainty, aggregation, objective direction, tie handling, fidelity, and safe use.
4. **R1-4 · MAJOR · Claimed controls not exercised — RESOLVED.** The executable probe now includes stable per-case reseeding and forward/reverse stochastic order controls; the runner mutates real route selection and a real upstream success-status/mismatch path, and requires outer rejection rather than deleting a copied PASS line.
5. **R1-5 · MAJOR · Two-axis sensitivity incomplete — RESOLVED.** Retained dataflow equations vary K and array shape; aspect cases vary M/N and pipeline/bus architecture parameters; context cases vary saved workload bytes/scope and retention bandwidth. Reload remains an explicit omitted counter-hypothesis, not a modeled ranking.
6. **R1-6 · MAJOR · Negative compiler/runtime boundary hard-coded — RESOLVED.** `ch21_boundary_audit.py` hash-locks and searches relevant compiler/runtime surfaces and claim-bearing inputs; an injected unsupported bridge claim must fail.
7. **R1-7 · MINOR · Large linked values absent from numerical evidence — RESOLVED.** The formula probe prints, serializes, and gates all three linked-plugin values.
8. **R1-8 · MINOR · Closure files outside manifests — RESOLVED BY QUALIFICATION.** Governance now distinguishes exact manifest-bound payload, manifest roots, derived verification receipts, and final Git tree seal. It no longer claims recursive checksum self-closure.

## Runner, manifest, and validator review

9. **R2-1 · MAJOR · Symlink and unmanifested-extra acceptance — RESOLVED.** Closure checks require one literal recursive file set, regular non-symlink members, and resolved containment beneath the direct-child run directory. Disposable extra/symlink/path mutations are rejected.
10. **R2-2 · MAJOR · Git seal/direct-child/run-only shape unenforced — RESOLVED.** Post-seal mode requires clean current checkout, one parent equal to `input_commit`, exact direct-child run location, and every sealing-commit path below that run.
11. **R2-3 · MAJOR · Unsafe run-ID path handling — RESOLVED.** Runner and validator accept only `YYYYMMDD-ch21-postreview-vN`-style basename tokens and verify the resolved parent before reads or writes.
12. **R2-4 · MEDIUM · Manifest mutation did not test real hierarchy — RESOLVED.** Disposable mutations target the real retained and outer manifests under normal and optimized Python, including bad digest, missing/extra/duplicate/path/symlink cases.
13. **R2-5 · MEDIUM · Failure source-state lines weakly checked — RESOLVED.** Every retained failure log is gated for one exact detached, clean, pinned state line with the baseline ignored-state digest and the intended fail-closed diagnostic.

## Governance, claims, and primary-source review

14. **R3-1 · BLOCK · Governance closure not parsed — RESOLVED.** The validator requires a non-placeholder PASS disposition, canonical one-word status for exactly C21.1–C21.12, C21.11 `verified`, exact claim-to-limitation equality, and ledger/report/run authorization convergence.
15. **R3-2 · MAJOR · Validation depends on external Git objects — RESOLVED.** Body and outer validation verify bundled inputs against the bundle-local input manifest. Git is used only by explicit post-seal validation of repository history/tree structure.
16. **R3-3 · MAJOR · Metric/aggregation governance ambiguous — RESOLVED.** Singular records and worked cases declare aggregation, denominator, weights, baseline, normalization, missing-case policy, objective direction, and tie handling; per-row cases use explicit `none`/`not_applicable` values.
17. **R3-4 · MAJOR · Pareto wording outruns evidence — RESOLVED BY NARROWING.** Multiobjective/Pareto method qualification is introduced but not exercised. Preference rules, nondominated portfolio selection, and portfolio ranking remain Chapter 22-owned.
18. **R3-5 · MAJOR · Complete-manifest wording overstated — RESOLVED BY LAYERING.** Payload completeness, root manifests, derived receipts, and Git seal are named separately.
19. **R3-6 · MINOR · Status vocabulary ambiguous — RESOLVED.** Each claim now has exactly one canonical status from `verified`, `qualified`, `rejected`, or `blocked`; qualifications remain prose.
20. **R3-7 · MINOR · E21.8 provenance not retained — RESOLVED.** `ch21-primary-source-verification-ledger.json` retains date, verification method, DOI/URL, source type, inspected surface, canonical metadata digest, and per-source status. Full-text-unavailable entries remain `qualified`.
21. **R3-8 · MINOR · Ownership wording insufficiently sharp — RESOLVED.** Chapter 20 defines authorization requirements; Chapter 21 constructs but cannot redefine the sweep-specific evidence package; Chapter 22 retains Pareto preference and portfolio ranking.

## Binding result

Every finding from all three full reviewer summaries has an explicit disposition above. The post-review bundle must contain this file and all amended claim-bearing inputs. A failed reseal, missing mutation, noncanonical status, altered limitation, nonlocal path, external symlink, or Git-shape mismatch blocks drafting.
