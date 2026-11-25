# What the second edition verified

[Contents](README.md) · [Evidence by chapter](evidence-matrix.md)

The first run illustrates why a second edition was needed. At the first-edition pin the small matrix returned the right four numbers with weight-stationary active. At the second-edition pin the same mathematical answer came from output-stationary, and the bracketed counter advanced by four. Correct output, correct route and a correctly attributed cost are three separate claims.

## Which source?

| Item | Identity and scope |
|---|---|
| Simulator tested | `nicefungo/tusim`, commit `7a094ff6c5527eff8e4318de676f0c0221c448b4` (November 18, 2026), tree `0268ced732412fd878b8d0ddd9916a3d8216a236`. The configuration string `2.0-dev` is not a release tag. No unpublished overlay. |
| Source used in the independent check | Git archive SHA-256 `64a184cd8335db2537396704c5b35059c9c6342c267b84cc6d3b697b65f32510`. S16 fetched the public commit into a fresh object store; it did not reuse an old executable. |
| First edition | Book `71835c69a0d7bbf806f5be81f57c217062d31e69` (August 19, 2026); simulator `e918c80b6fce833cd1fcae97730fa841c2176f25` (July 25 freeze). In particular, Chapters 2, 11 and 19 retain historical cases. |
| Manuscript basis | S15 sealed the integrated candidate on November 25, 2026. Its archive SHA-256 is `5653de4ec86f37ad57f4811465517af7912ce16768d9eb13d63b55dc6bd346be`; that hash identifies the original, **not** this edited Markdown edition. |

## How the evidence developed

| Stage | What changed for the reader |
|---|---|
| S1–S3 | Engineering work preceded the book audit. S3 chose the public source rather than later local changes and retained 23 chapters: four arguments could stand, thirteen chapters needed factual corrections and six needed new material. |
| S4–S6 | Matched file settings and active callbacks replaced labels as evidence. Partial tiles explained why twelve visits could cost either 234 or 384 cycles. Independent bit checks covered finite nonzero half inputs; byte, bank-grant and context controls separated copying from metering. |
| S7–S8 | A pending transfer was distinguished from a canceled one, and 130 descriptor ranges were checked in order. Moving the same work between queues changed independent-channel retirement time, not shared serial time. The pipeline score did not establish that the next tile was ready. |
| S9 | DRAM service, useful bytes, occupied bytes and supplied ticks were compared separately. A fixed-process calculation explained how modeled energy could fall while average power rose. |
| S10–S11 | Split and whole attention rows were checked against numerically distinct value patterns. Tile fit was separated from minimum traffic. Normalization accounting, reduction axes and the small winning log-softmax value were checked independently. |
| S12–S13 | A feasible 133-cycle mesh schedule disproved a claimed 158-cycle minimum. Build membership, completed launches, active route and the ability of a check to detect a wrong result were counted separately. |
| S14 | Chapters 22–23 compared newer route and attention evidence with historical claims. A changed reason to investigate a design was not a change to its original disposition. |
| S15 | The 23 chapters were integrated; the reader setup, roof arithmetic, weight estimator, evidence matrix and historical registers were checked together. |
| S16 | An independent local reproduction used the sealed book and the named public source. The following results are from that reproduction, not new simulator runs made while editing this public projection. |

## What S16 reproduced

| Check | Observed result | Limit |
|---|---|---|
| Reader cases | Three arithmetic roofs agreed. Four smoke targets completed (19/19, 9/9, 15/15, ASM identity PASS); active OS, four MMA cycles, output `[[58,64],[139,154]]`. Six estimator controls matched expected streams and exits. | The roofs are arithmetic, not measured throughput. Old codec runs were not repeated. |
| S4–S6 | 143/143 child exits matched; 290/297 raw comparisons were byte-identical. All 190,458 finite nonzero half input/route combinations agreed for the identity product. | The seven raw differences involved paths, interpreter version or the identified precision runner, not changed result words. |
| S7–S9 | 77/77 exits matched, 170/171 byte comparisons were exact, and 22/22 available product or fixture identities matched. At buffer swap the newly active allocation still lacked its tile. | The differing traceback contained a path. Reproducing the pipeline defect is not correcting it or demonstrating legal overlap. |
| S10–S13 | 42/42 expected exits, including 28 live checks. Attention staging and KV comparisons matched 720 and 2,565 numerical rows. The placement counterexample held. A comparator accepted NaN; a report parser returned PASS despite a failed row. | Some exits were expected rejections. Neither a matching exit nor a PASS label establishes correctness outside its oracle. |
| Rendering of the sealed candidate only | 36/36 HTML pages matched byte-for-byte; 23 chapters, 633 local rendered link occurrences (32 fragments), 70 MathML expressions. Two Firefox viewports matched pixel-for-pixel. | Not all pages were pixel-compared. This projection ships **no HTML** and does not inherit that render result. |

**Historical registers.** Across 46 reports, all 249 design decisions remain open: **18 retained, 113 qualified, 34 blocked, 76 rejected and 8 superseded**. Those dispositions describe claims, not selected designs. The register spans 11 metric domains, seven mechanism families and 11 contradiction classes; it identifies 25 stale and nine negative entries. All 17 extension statements were accounted for. Compiler/runtime/ONNX integration remains a negative boundary. This was a register check, not a portfolio replay or reclassification.

**Not established.** S16 checked aggregate membership against the live pin but did not run `test` or `test-quick`; launch evidence belongs to S13. Admission/bounds and mixed extreme-descriptor cases, superseded setup attempts, v1 runs, historical codecs, device calibration, external URL availability and a recovery drill were not new passes. There were no unexpected failures among the selected S16 checks.

## What changed for public readers

This is an abridged reader projection of S15, with S16 results added. It keeps the original chapter sequence and section identifiers, worked derivations, representative tables, comparisons and their evidence limits. It shortens historical audits, supplies a small source-only first run, and replaces links to unshipped evidence with a labeled summary in each chapter. A summary reports what was observed; it is not a downloadable transcript or an independently runnable substitute for the omitted probe.

The first edition remains in place. No second copy of its evidence tree is needed. Private working records, raw run directories, diagnostic reproductions, boundary recipes, tools, executables, archives, offline renderer and dependency wheels are excluded. No package redistribution rights are assumed. The two editions share Git ancestry through the public v1 baseline rather than replacing its chapter paths.
