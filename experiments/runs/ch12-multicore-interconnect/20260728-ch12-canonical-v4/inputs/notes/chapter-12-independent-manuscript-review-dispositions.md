# Chapter 12 Independent Manuscript Review Dispositions

- **Frozen review commit:** `0da34318c477039c4c5def78d2d9bf10436c2d2c`
- **Tusim pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Review batch:** `deleg_e9501126`
- **Review verdicts:** technical **BLOCK**; editorial **BLOCK**; reproducibility **BLOCK**
- **Replacement canonical target:** `experiments/runs/ch12-multicore-interconnect/20260728-ch12-canonical-v4/`
- **Current closure status:** blocked pending canonical-v4 and clean re-review

Full reviewer records:

- `/home/zxy/.hermes/cache/delegation/subagent-summary-0-20260728_144533_126959.txt`
- `/home/zxy/.hermes/cache/delegation/subagent-summary-1-20260728_144533_127657.txt`
- `/home/zxy/.hermes/cache/delegation/subagent-summary-2-20260728_144533_128152.txt`

The absolute cache paths preserve provenance but are not repository evidence. This file records every finding and its repository disposition.

## Technical/architecture findings

### T1 — Send does not check 32-bit span wraparound

**Finding:** the manuscript said send checks wraparound. Source compares `offset + size` with capacity in 32-bit arithmetic, so a wrapped sum can appear in range.

**Disposition:** accepted. Manuscript and ledger now require trusted callers to establish `size <= capacity` and `offset <= capacity - size` for both endpoints. Canonical-v4 must seal source predicates for the absent overflow-safe checks. Unsafe cases remain unexecuted.

### T2 — Overflow was attributed to the wrong addition

**Finding:** declared 32-bit message count and size widths bound any one directed-link service sum below `UINT64_MAX`. The unchecked risk is the later `bottleneck_link_cycles + max_route_cycles` addition.

**Disposition:** accepted. Manuscript, ledger, source audit, and skeptical-review record now state the type-width proof and final-addition risk. Canonical-v4 must seal both predicates without executing overflow.

### T3 — Mesh-column ceiling expression can wrap

**Finding:** `(num_cores + mesh_rows - 1) / mesh_rows` can overflow its 32-bit numerator for a sufficiently large nonzero row count and produce zero columns before later division/modulo.

**Disposition:** accepted. Manuscript and ledger now state the safe arithmetic precondition and the overflow-safe alternative `1 + (num_cores - 1) / mesh_rows`. Canonical-v4 must seal constructor predicates; the unsafe downstream case remains unexecuted.

### T4 — Shared-link service rounds each message separately

**Finding:** source computes `C_ell = sum_i ceil(B_i/W)`, not `ceil(sum_i B_i/W)`.

**Disposition:** accepted. The central equation now defines per-message rounding and uses cycle units. The aligned 1 KiB worked example explicitly notes why the aggregate ceiling happens to agree there.

### T5 — Primary references were misattributed and anchors were broken

**Finding:** DT01 and DS87 were named as different books and linked to nonexistent fragments.

**Disposition:** accepted. The reference list now matches the canonical Dally–Towles 2001 and Dally–Seitz 1987 entries and their existing anchors. Anchor-aware validation is required before closure.

## Editorial/pedagogy findings

### E1 — Central equation mixed byte and cycle wording

**Disposition:** accepted with T4. `C_ell` is explicitly defined in service cycles before the combined heuristic equation.

### E2 — Residual “bound” labels described heuristic scores

**Disposition:** accepted. The prerequisite graph, same/disjoint example, and route-order comparison now use “heuristic estimate,” “returned score,” or “heuristic score.” Carefully scoped rejections and individual necessary terms retain mathematically meaningful bound/floor wording.

### E3 — Required source map was absent

**Disposition:** accepted. A compact source map now links each contract to exact pinned source/config/test paths.

### E4 — Opening neighbor traffic was underspecified

**Disposition:** accepted. The chapter now defines neighbor traffic as `i→(i+1) mod N` and explains the `15→0` ring/mesh mapping difference.

### E5 — ICC, SPMD, and NoC appeared before expansion

**Disposition:** accepted. First uses now expand inter-core communication, single program/multiple data, and network-on-chip.

### E6 — Fidelity warnings repeat

**Disposition:** qualified, nonblocking. Repetition is retained where it protects distinctions among adjacent APIs and repairs the prior lower-bound overclaim. Final editorial re-review will determine whether any sentence can be removed without weakening those boundaries.

## Reproducibility/repository findings

### R1 — Historical pre-draft PASS was not reproducible from the final tree

**Finding:** the old validator asserted the pre-run BLOCK wording against post-run live files, and no retained pass log existed.

**Disposition:** accepted. The v4 validator reconstructs claim-bearing inputs from the transcript-recorded input commit, compares those blobs with bundled inputs, validates the finalized run, and is executed by the runner. Its PASS output must be retained as `predraft-validation.log`.

### R2 — Finalization and manifest trust root were not closed as documented

**Disposition:** accepted. Canonical-v4 uses an inner manifest for all audit inputs/logs including the transcript, then an outer `bundle-sha256.txt` over the inner manifest, `finalization.log`, and retained pre-draft validation result. The later local evidence-seal commit authenticates the outer manifest; no file is claimed to self-authenticate.

### R3 — Manuscript validator could accept consistently rewritten evidence

**Disposition:** accepted. The closure validator must enforce exact inner/outer member sets, transcript digest consistency, direct config-log qualification, clean Git state, and byte equality with committed blobs. These checks become mandatory after canonical-v4 is committed.

### R4 — Live documents retained stale canonical-v2/v3 anchors

**Disposition:** accepted. Current status surfaces now target canonical-v4; references to v1–v3 remain only where explicitly labeled immutable historical evidence.

## Gate decision

**BLOCK pending canonical-v4 and clean re-review.** No reviewer PASS is carried forward across the corrected evidence snapshot.