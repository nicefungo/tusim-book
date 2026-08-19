# Chapter 23 Predraft Review Reconciliation

RECONCILIATION STATUS: COMPLETE

Scope: framing and evidence planning only. No Chapter 23 manuscript exists.

## Review sequence

1. **Seal falsification review (`deleg_88e08c65`) — REJECT.** The first provisional bundle was checksum-consistent but not fail closed.
2. **Whole-path technical review (`deleg_504241d9`) — ACCEPT WITH REQUIRED RECONCILIATION.** It accepted the constraint-first reader decision but required additional path/boundary qualifications.
3. Corrected candidates were regenerated rather than relabeling stale evidence.
4. The final narrow independent rereview accepted corrected provisional `20260819T084557Z-provisional`, retained-manifest SHA-256 `8567838cddf7dff5bdeb50b37d37d60eadc7c8b1a97fafae19b14cfd1d33a8d0`, at source pin `e918c80b6fce833cd1fcae97730fa841c2176f25`, with the four required IDs below. It confirmed the superseding delta is one removed trailing space plus derived hashes and revalidated all prior controls.

## Dispositions

| Finding | Disposition | Retained evidence |
|---|---|---|
| `assert` checks disappear under `python -O` | Replaced every claim-bearing `assert` with explicit `EvidenceError` checks; AST control rejects `ast.Assert`; positive and source-mutation controls run under normal and optimized Python. | `ch23_extension_recon.py`, `test_ch23_evidence_controls.py`, `controls.log` |
| Runner copied scripts but executed live originals | Runner now executes the copied recon and validator bytes inside the temporary bundle; runner and control script are themselves retained. | `run_ch23_predraft_seal.sh`, `payload.sha256`, `retained.sha256` |
| Compiler boundary could stale-pass on loose phrases | Validator requires unique exact trigger, promotion-gate, smoke, and final lines; contradictory duplicates and any failure line are rejected. Promotion remains `compile=0 link=0 run=0 independent_oracle=0 full=0`. | `recon.log`, `validate_ch23_predraft.py` |
| Review/reconciliation were not bound to the candidate | Postreview validation requires an accepting decision plus exact provisional run, manifest digest, and source-pin markers; reconciliation must be explicitly complete. | `validate_ch23_predraft.py` |
| Sweep extension path was omitted | Added source hash, dedicated-target/aggregate ownership, fixed input, local formula, mismatch-status, documentation, and fresh execution checks. The harness is classified standalone and fail-open on mismatch. | `tests/test_dataflow_sweep.c` hash, `PATH_SWEEP`, focused sweep line, C23-17 |
| Dataflow consumer path needed exact resolution | Bound the complete production route: direct selection → global registry pointer → `tu_mma()` → `tu_dataflow_execute_mma()` → selected vtable. Corrected duplicate ownership: keep the first stable pointer, free the newly-created duplicate; capacity overflow returns without freeing it or reporting status. | `PATH_PLUGIN`, C23-04–06 |
| NLR/unknown selection fallback was omitted | Added the exact fallback-to-WS and success-status hazard; NLR remains blocked as integrated support. | `PATH_PLUGIN`, C23-05, plan limitations |
| Config red result was overinterpreted as stable | Canonical run remains red, but plan/ledger now state that independent layouts have passed and root cause is layout-sensitive/open. Promotion requires root-cause resolution and a repeated-build/path matrix. | `FOCUSED test-config`, C23-02, plan limitations |
| Python binding green identity path was omitted | Added fresh identity-GEMM smoke while preserving that config path and report stubs are not exercised and no Make/CI owner exists. | `FOCUSED python-binding`, C23-11–13 |
| Scheduler/liveness adjacent ISA consumers were omitted | Added both source hashes and classified them as adjacent analysis consumers, not executable queue/compiler composition. | `PATH_OPCODE`, hashes, plan |
| Cycle-model no-caller statement lacked exhaustive support | Added exhaustive tracked C/H `tu_cycle_*` caller scan outside source/header/focused test; result is zero external non-test call files. | `PATH_MODULE` |
| First provisional source inventory was contaminated by newly created ignored artifacts | Moved only the session-created artifacts out of Tusim; restored the bootstrap ignored-inventory digest `55cee6…`; current runner requires this baseline before and after. Tracked source remained clean at the exact pin. | source bookends and ignored SHA in final provisional |
| Documentation labels could be mistaken for behavior | Documentation remains an audited claim source only; conflicts are explicit and positive “production-grade/complete” claims are blocked. | `DOC_CONFLICT`, C23-14 |
| Outer seal accepted corruption or extra files | Added exact all-entry verification, regular non-symlink enforcement, seal-field checks, seal→retained digest binding, retained-name/hash verification, and semantic revalidation. Normal and optimized controls reject an extra file, extra directory, symlink member, seal boundary reversal, retained tamper, and compiler-promotion reversal. | `verify_ch23_predraft_seal.py`, `test_ch23_seal_controls.py` |
| Postreview accepted arbitrary textual binding markers | Postreview now retains the reviewed provisional run name, seal, and manifest; validation compares all three exact review lines to those retained bytes. | runner and postreview validator |
| Dispatcher census omitted attention | Hash-pinned `attention_engine.c`; exact census is two production files and three call sites into the dispatcher. | `PATH_PLUGIN`, C23-04 |
| Sweep labels were mistaken for effective routes | Reconciled labels WS/OS/RS against core-snapshot restoration: all three effective routes are WS. | `PATH_SWEEP`, C23-17 |
| Finalization could collide | Runner checks destination absence both before setup and immediately before `mv -T`; collision exits nonzero. | `run_ch23_predraft_seal.sh` |

## Final required-review dispositions

| Required ID | Status | Disposition | Evidence |
|---|---|---|---|
| R23-FINAL-01 | resolved | Review decisions and each binding key must occur as exactly one exact line; conflicting or unknown `REVIEWED_` lines are rejected. A fully resealed collision mutation is exercised under normal and optimized Python. | `validate_ch23_predraft.py`; `test_ch23_seal_controls.py` |
| R23-FINAL-02 | resolved | Completion now requires this exact one-row-per-ID table. Missing, duplicate, unknown, or non-`resolved` required IDs fail semantic validation; the completion phrase alone is insufficient. | this table; postreview validator; reconciliation-row mutation control |
| R23-FINAL-03 | resolved | Runtime geometry is classified **partial/qualified**, not integrated, until stack-smashing is resolved and a discriminating downstream observable is green. | framing path matrix; C23-02 |
| R23-FINAL-04 | resolved | Generic replacement/lifetime wording was removed. Duplicate IDs retain the first pointer and free the new duplicate; capacity overflow returns without freeing the submitted pointer or returning status. | framing limitations; C23-06; `PATH_PLUGIN` |

## Final gate

**POSTREVIEW AUTHORITY: PASS.** Run `results/ch23-predraft/20260819T084945Z-postreview`, retained-manifest SHA-256 `598ec9ace364d75be687c255526ddb49c7158bd2043741b94a19806a33da1fb9`, passed semantic validation, exact outer closure, normal/optimized verification, and all 13 mutation families. The retained `review-reconciliation.md` inside that immutable run is the reviewed input; this live note records the resulting authority. No manuscript was created in this framing checkpoint.
