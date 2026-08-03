# Chapter 11 Skeptical Review Dispositions

- **Date:** 2026-07-28
- **Chapter:** **Instruction Surfaces and Command-Queue Ordering**
- **Tusim pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Reviews:** architecture/methodology and repository/reproducibility pre-draft reviews
- **Original verdicts:** `BLOCK`, `BLOCK`
- **Final verdict:** **PASS for canonical evidence execution**
- **Draft gate:** still blocked until the corrected execution-input commit is used for the canonical retained run and `ch11_predraft_validate.py` passes

This document converts every skeptical finding into a correction, a bounded rejection, a static safety precondition, or an explicit deferral. It does not retroactively validate the stale initial retained run.

## Resolution rules

1. A source declaration is not promoted into runtime behavior without a call edge or probe.
2. A focused test pass is retained as an observation, not a correctness certificate.
3. Unsafe or potentially nonterminating paths remain static unless a bounded probe can discriminate the behavior safely.
4. The initial run `20260728T030000Z-initial` is development history only. It must not be cited as canonical evidence.
5. The corrected inputs are committed before the canonical run; the run then copies those inputs into a self-contained bundle.

## Architecture/methodology review

| Priority | Finding | Disposition | Resolution |
|---|---|---|---|
| P0 | The retained initial bundle is stale and its live-input manifest no longer verifies. | accepted | The canonical runner now refuses an existing run ID, copies all claim-critical inputs into the bundle, produces a run-relative manifest, hashes the closed transcript, and targets `20260728-ch11-canonical`. The initial run is excluded from evidence claims. |
| P0 | Queue barrier behavior was the largest unprobed ordering defect. | accepted and closed | The probe now constructs `FAULTED → dependent PENDING → BARRIER → independent NOP`. A bounded wait first times out on the pending dependent; the barrier and later NOP then complete while the earlier command remains pending. |
| P1 | Faulted dependencies and terminal-state behavior were missing. | accepted and bounded | Missing IDs are probed fail-open; retained faults are probed fail-stuck with a two-cycle wait timeout; reset-ID reuse is probed. A genuinely retired ID cannot be produced by normal pinned paths, so the chapter states that limitation rather than fabricating a retired case. |
| P1 | Reset wording incorrectly said all IDs restart. | accepted and closed | The ledger now states that command IDs restart while signal IDs continue. The reset probe records command-ID reuse and stale-handle aliasing. |
| P1 | `pipeline_tiles` and `max_window` wording was broader than the exact occurrence audit. | accepted and closed | The claim is narrowed to occurrences within `tu_scheduler.c`; declarations and tests are explicitly distinguished from implementation consumers. |
| P1 | Scheduler fan-in truncation and barrier boundaries were not discriminated. | accepted and closed for the chapter boundary | A barrier after 17 ordinary nodes now demonstrates silent retention of only 16 predecessor edges. The existing independent post-barrier DMA case already discriminates the missing outgoing barrier edge. Additional multi-barrier patterns are deferred because they do not change the established boundary. |
| P1 | Barrier-insertion/count-reset evidence was nondiscriminating because the direct count was zero. | accepted and closed | A two-node hazard now produces direct insertion count one without adding a node; the full scheduler returns zero inserted barriers and the same output count. |
| P1 | DMA hoisting was not shown to be report-only. | accepted and closed | A three-node input now produces direct hoist count one while graph IDs remain unchanged; the full scheduler returns zero. The ledger attributes actual reordering to list-scheduler priority, not the named hoist pass. |
| P1 | Negative reachability claims and config claims were too broad for the fail-closed audit. | accepted and closed | The source audit now hashes config, elementwise, core, cluster, DPI, scheduler-sweep, config-test, elementwise-test, and shipped-JSON inputs. It checks exact whole-tree C caller sets for scheduler, ASM, and queue surfaces and qualifies the binary-consumer claim as bounded to the audited inventory. |
| P1 | Runner provenance, collision handling, containment, and retention were weaker than planned. | accepted and closed | Provenance runs before durable output; source must be detached and clean; run-directory creation is exclusive; ignored inventory is compared; each executable has an external timeout; bundled inputs and outputs are checked with run-relative hashes; transcript finalization occurs after closure. |
| P2 | Exact ISA counts, native bytes, and scheduler sequence were printed but not all asserted. | accepted and closed | The probe asserts 128/68/60 exactly, asserts the little-endian host and exact native byte vector, and checks the complete three-op scheduler order through expected retained output. The source audit independently enforces 59 explicit enum declarations and 68 name-table entries. |
| P2 | Unsafe low-level dependency and ASM boundaries should not be run uncontrolled. | accepted as static safety boundary | `num_deps > 0` with null IDs, allocation failures, the 17th weight binding, and unchecked host extents remain static qualified findings. The canonical runner does not execute them. |
| P2 | The title may understate lifecycle and scheduler boundaries. | considered; original title retained | The earlier independent framing review ranked **Instruction Surfaces and Command-Queue Ordering** first. Queue lifecycle is the mechanism by which ordering claims are evaluated; scheduler treatment remains subordinate and explicitly non-integrated. Expanding the title would overstate scheduler scope. |

## Repository/reproducibility review

| Priority | Finding | Disposition | Resolution |
|---|---|---|---|
| Critical | Initial retained bundle no longer verifies. | accepted | Superseded by a fresh canonical bundle produced only after corrected inputs are committed. |
| High | Retention used mutable live paths and omitted claim-critical inputs. | accepted | The runner copies probe, audit, runner, validator, report, framing, ledger, dispositions, and bibliography into `inputs/` under the run and hashes them relative to the run root. |
| High | Config integration was not fail-closed. | accepted | The audit now traces instruction width, queue depth, dependency switch, and cycle model through shipped JSON, defaults, parser, converter omissions, compile-time constants, and queue construction. |
| High | Exact ISA count and byte claims were observations rather than gates. | accepted | Exact assertions and retained expected-output gates were added. |
| Medium | Real core/cluster/DPI and test consumers were missing from reachability inventory. | accepted | Exact whole-tree caller sets now cover core, cluster, DPI, scheduler sweep, and elementwise tests. |
| Medium | DMA hoisting was report-only. | accepted | Source predicates and positive direct/full-run probes now distinguish report generation from output order. |
| Medium | Provenance predicates did not match the framing plan. | accepted | The runner asserts detached source, exact pin, clean tracked/untracked state, unchanged ignored inventory, exclusive run ID, exact source-audit totals, unchanged committed inputs, and unchanged book state outside the new run. |

## Elementwise correction discovered during disposition

The pre-review ledger called `num_ops > 8` unsafe. A deeper trace found that `tu_ew_apply_fused()` rejects the oversized count before copying operations or touching SRAM. The corrected bounded conclusion is:

- the public wrapper's local clamp does not change the descriptor's stored count;
- queue execution forwards the stored count;
- the fused helper rejects counts above eight safely in this path;
- the queue ignores that rejection and still marks the command `COMPLETED`.

A nine-operation bounded probe now captures that distinction. The chapter must not retain the earlier “unsafe read” wording.

## Primary-source disposition

External sources are used only for vocabulary and comparison:

- RISC-V for explicit instruction-format and scoped fence contracts;
- Smith–Sohi for separating issue, execution, completion, and retirement;
- Tomasulo and OpenCL for dependency/readiness and command-event examples;
- Smith's decoupled access/execute work for finite queues and synchronization;
- Gemmini for a concrete full-stack integration comparison.

None proves Tusim behavior. Every Tusim-specific claim remains pinned-source/test/probe evidence.

## Final evidence gates

Canonical execution may proceed only if all of the following hold:

- source audit reports exactly `hashes=26 predicates=96 checks=122`;
- all five audited executables are statically linked against the rebuilt archive and finish under timeout;
- focused observations remain queue 9/9, ISA 9/9, ASM smoke PASS, scheduler 14/14;
- the probe reports zero failures and exact queue, barrier, elementwise, scheduler, reset, and ASM lines;
- all execution inputs remain unchanged from the execution-input commit;
- the canonical run has copied inputs, a closed transcript, and a run-relative verified manifest;
- the pre-draft validator passes after the run.

**Final verdict:** **PASS for canonical evidence execution. Drafting is not yet approved by this document alone.**
