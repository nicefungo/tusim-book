# Chapter 16 — Predraft Gate Closure

**Title:** Double Buffering and Legal Overlap

**Edition pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`

**Drafting authority:** `experiments/runs/ch16-double-buffer/20260804-ch16-canonical-v4`

**Sealing input commit:** `abf3278561fdf9263bcc8a92b4f5af1c61b74c9c`

**Status:** closed

## Verdict

**PASS — drafting is authorized only from canonical v4.**

Canonical v1 is provisional, v2 is validator-blocked, and v3 is superseded because its runner did not fail fast on stale grep gates and because the complete skeptical-review result added lifecycle, bounds, and shared-resource requirements. All three are retained as historical evidence; none authorizes drafting.

## Closed gates

Canonical v4 completed successfully and retained:

- exact detached, clean Tusim pin verification;
- 31 pinned-source hashes;
- 60 structural predicates and 91 total source checks;
- a source-hash mutation that failed as required;
- static archive membership for the standalone DB and controller objects;
- direct standalone double-buffer execution: 10/10 passed;
- a focused assertion mutation: 9/10 passed, 1 failed;
- exact bounded state, DMA, controller-ledger, no-load, reset, live-reinit, and context-restore probe lines;
- analytical recomputation of ten historical rows, the 17/18.285714/20 threshold conflict, 1,024-versus-512 B/cycle premise check, physical doubling, and a shared-resource overlap discriminator;
- an AddressSanitizer-instrumented lifecycle run with no AddressSanitizer error. Leak detection was disabled only for the isolated context child because the implementation behavior under test intentionally discards live DB ownership;
- a fail-fast runner using `pipefail` and `PIPESTATUS[0]`;
- retained-input, manifest, bundle, source-cleanliness, and input-commit verification;
- fail-closed validation that does not rely on removable Python assertions.

## Binding claim boundary

The manuscript may teach:

1. the standalone SRAM active/shadow state machine and its observed local semantics;
2. the stronger ownership, validity, completion, swap, reset, and lifecycle protocol required for legal overlap;
3. descriptor DMA as a separate transfer/completion surface;
4. the standalone pipeline controller as a separate, workload-unreachable accounting surface with known bridge and ledger defects;
5. scheduler and exploration models as separate analytical abstractions;
6. ideal overlap equations and alternatives, with explicit clock, resource, and capacity assumptions.

It must not claim that descriptor DMA legally fills the standalone shadow allocation, that the controller is reached by ordinary workloads, that scheduler naming establishes object ownership, that all surfaces share a clock, or that documentation diagrams prove runtime composition.

## Required manuscript qualifications

- `shadow_dirty` is notification/accounting state, not freshness, byte coverage, completion, or validity proof.
- A clean swap is source-legal; caller-enforced preconditions are required.
- Live reinitialization and context restore discard DB ownership and are not safe lifecycle bridges.
- General SRAM and descriptor range checks are not overflow-safe for arbitrary 32-bit inputs.
- Controller speedups may be artifacts of absent-DMA baseline asymmetry or omitted compute accounting; they are not overlap evidence.
- Analytical capacity and timing results are reconstructed, not measured integrated-runtime performance.
- Independent preload/store credits require independent resources; shared resources require a combined cap.

Drafting may now proceed from canonical v4 and these constraints. No push or publication is authorized.
