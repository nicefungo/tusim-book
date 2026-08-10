# Chapter 19 — Independent predraft review dispositions

**Title:** Static Scheduling and Scratchpad Allocation

**Edition pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`

**Reviewed bundle:** `experiments/runs/ch19-static-transforms/20260810-ch19-canonical-v6`

**Review state:** complete

**Drafting verdict:** **REVISE**

## Review method

Two independent read-only reviews checked the frozen inputs, retained logs, manifests, and pinned C source. Representative scheduler and allocator relations were recomputed directly from the detached source rather than inferred from the canonical transcript. The reviews used neutral correctness-review terminology and made no source-repository changes.

## Accepted blocking findings

### R19.1 — Spill statistics count marking events, not distinct values

Accepted. C19.28 was too weak: one unplaced 16-byte VReg under an 8-byte capacity can be selected as its own spill candidate and counted, then counted again when placement still fails. The observed result is one `spilled` VReg with `num_spills=2` and `spill_bytes=32`. The claim ledger, exact probe, and executable negative control must distinguish marking events from distinct values or transfers.

### R19.2 — Canonical-v6 is evidence, not a closed drafting authority

Accepted. Its 13-entry input manifest and 32-entry retained manifest verify, but it has no optimization-safe closure validator, validator negative-control logs, finalization binding, exact inventory check, retained checksum-verification transcript, or outer bundle manifest. Canonical-v6 remains immutable and superseded.

### R19.3 — Executable negative controls are too narrow

Accepted. The focused-suite controls prove that each test executable can report a changed expectation. The scheduler identity and liveness opcode controls prove two semantic checks. They do not by themselves cover every broad relation in the 56-claim ledger. Post-review evidence must add independent checks for spill accounting, cross-pass strided-DMA interpretation, low-level provenance, repeated interference construction, invalid allocator enums, and asymmetric barrier reporting.

### R19.4 — Focused executable provenance needs a retained proof

Accepted. The Makefile recipes use `-L. -ltucmodel`. A disposable source archive normally contains no shared object, but absence and linkage were not retained in canonical-v6. The replacement runner must compile the focused scheduler, liveness, and sweep binaries against the exact archive path and retain archive-member and dynamic-dependency evidence.

### R19.5 — Source-audit closure needs explicit fail-closed controls

Accepted. Canonical-v6 proves the expected pin and hashes only on the passing path. The replacement runner must retain a wrong-pin rejection, a copied-source hash-change rejection, and restored-source recovery before executing claim-bearing probes.

## Accepted major findings

- Add an exact executable strided-DMA case for the scheduler/liveness region disagreement in C19.42.
- Add low-level cross-sequence cases for the unchecked result/graph provenance boundary in C19.43 and C19.55.
- Add repeated interference construction to demonstrate the non-idempotent public API behavior in C19.45.
- Add invalid liveness placement/spill enum cases for C19.46.
- Add paired positive and negative barrier-reporting cases for C19.51.
- Retain an exhaustive numeric-opcode census before making per-op legality statements for C19.41 and C19.52.
- Treat the scheduler sweep only as a retained report. Exact ordering and failure-sensitive closure must come from the dedicated probe and negative controls, not the sweep exit status.

## Recomputed representative observations

The independent checks reproduced:

- ASAP and ALAP selecting the original-ID NOP before an independent DMA load, while BALANCED selects the DMA load; all three retain the same serial estimate of five;
- a later DMA load crossing an earlier scheduler `BARRIER` in emitted order;
- strided DMA receiving different region interpretations in scheduler and liveness analysis;
- range-insensitive liveness use binding to the most recent same-region definition;
- repeated interference construction increasing graph membership rather than rebuilding from a clean state;
- no-spill capacity pressure assigning offset zero while retaining a successful colored state;
- one spilled value being counted twice by the spill statistics.

## Disposition

Canonical-v6 remains a reproducible provisional evidence bundle. It is not the drafting authority. Drafting remains blocked until the accepted findings are reflected in the ledger and executable probes, a clean post-review run is sealed, and the optimization-safe validator plus complete manifest layering pass under normal and optimized Python.
