# Chapter 18 framing review dispositions

- Date: 2026-08-05
- Source pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Scope: mandatory split/keep gate, 23-chapter replan, framing evidence, and governance closure
- Current verdict: **CLOSED-PASS — no blocker/high framing finding remains**

This file is the durable review record. Delegated live transcripts are transient process logs and are not treated as book authority. Claims below were reconciled against the pinned source, retained reproduction output, current governance files, and Git state.

## Durable reproduction

- Script: `experiments/ch18_framing_reproduce.sh`
- Output: `notes/chapter-18-framing-reproduction.log`
- Output SHA-256: `3e3935525857e30ad10d64c53d68ee3f2354dbae5636de01016d153975735945`
- Completion marker: `CH18_FRAMING_REPRODUCTION_PASS`
- Execution command:

```bash
experiments/ch18_framing_reproduce.sh > notes/chapter-18-framing-reproduction.log 2>&1
```

The script verifies the exact detached-clean pin before and after execution, archives the pin into a disposable directory, records toolchain and source hashes, builds the library, runs the focused context/scheduler/liveness suites, reproduces both sweeps, independently gates selected rows and scheduler-policy invariance, and performs an exact non-test caller inventory outside subsystem implementations/headers.

Retained outcomes:

```text
context:   15/15 tests passed
scheduler: 14/14 passed
liveness:  12/12 passed
256 KiB full:    262144 B, 16484 cycles
256 KiB live25:   65536 B,  4196 cycles
256 KiB control:      0 B,   100 cycles
pipeline-tiles: 28 cycles, 0 barriers, 0 hoists, length 13 for all three policies
non-test external callers: context=0 scheduler=0 liveness=0
```

## Review rounds

### R0 — subsystem reconnaissance (`deleg_abcfa65c`)

Three independent read-only workers inventoried contexts, scheduler, and liveness.

- Two recommended a split.
- One recommended a conditional keep centered on runtime contexts, but also confirmed that scheduler→liveness and liveness→context bridges are absent.

**Disposition:** split accepted. The conditional keep was rejected because it would make static allocator output appear to drive runtime live-prefix retention. Chapter 18 owns runtime retention/preemption; Chapter 19 owns scheduler/liveness static legality; Chapter 11 keeps scheduler DAG/ordering findings.

### R1 — first framing review (`deleg_6e35a0ad`)

Roles: technical/evidence, governance/editorial, skeptical/reproducibility.

High findings and dispositions:

1. **No durable Chapter 18 framing handoff.** Resolved by `notes/handoffs/2026-08-05-chapter-18-framing.md` and the README link.
2. **Downstream numbering not reconciled.** Resolved in current `PLAN.md` and README. Dated Chapter 17 notes and retained canonical inputs intentionally keep the numbering true when sealed; current PLAN supersedes their historical forward references.
3. **Direct restore and invalid-target failure atomicity missing from the probe gate.** Resolved by adding explicit ownership/accounting state-vector requirements.

### R2 — post-fix framing review (`deleg_6d832047`)

Roles: technical/evidence, governance/editorial, skeptical/reproducibility.

High findings and dispositions:

1. **Transition matrix omitted active free, self-switch, non-READY targets, policy ties, and complete ownership checks.** Resolved by expanding the matrix to all public operation families, relevant states, thresholds, policies, repeated trajectories, and safely injectable failures.
2. **Chapter 17 validator drifts after live governance files change.** Resolved procedurally: commit reviewed Chapter 18 governance content, then advance `notes/chapter-17-reviewed-snapshot.txt` in a marker-only commit and require normal and optimized validator passes. No retained Chapter 17 evidence is rewritten.
3. **Live Chapter 17 input-origin edits could be confused with immutable retained inputs.** Resolved by restoring all Chapter 17 notes unchanged. `experiments/runs/ch17-measurement/20260805-ch17-canonical-v4` remains intact. PLAN/README are live governance files and are handled by the snapshot-marker sequence.
4. **Probe lacked manager-wide transition coverage.** Resolved by requiring manager, descriptor, retained core, queue, embedded/operative DMA, bank, plugin, rounding/PRNG, clock, return, ownership, and accounting vectors before and after every row.

### R3 — high-severity closure review (`deleg_2ea65f69`)

Roles: technical/reproducibility and governance.

Findings and dispositions:

1. **Transition matrix still named too few vector fields.** Resolved by enumerating all manager fields, every descriptor's lifecycle/accounting/control fields, retained SRAM and bank state, queue contents/signals/counters, embedded and operative DMA, runtime config, plugin state, rounding/PRNG discriminator, core counters/clock, and return status.
2. **Framing evidence and review provenance were not durable.** Resolved by the tracked reproduction script, retained output, and this disposition record.
3. **Governance-content/snapshot-marker sequence required proof.** The governance reviewer simulated the exact two-commit sequence in a temporary clone. The marker-only diff contained only `notes/chapter-17-reviewed-snapshot.txt`; Chapter 17 validation passed under normal Python and `python -O`.

### R4 — final provenance/governance review (`deleg_3c7b1cbb`)

The governance reviewer independently reproduced the framing log byte-for-byte, verified the seven-file expected changeset, confirmed no historical Chapter 17 or retained-run diff, and simulated the two-commit sequence successfully.

The technical reviewer found one remaining high issue: the caller-inventory regex used incomplete context names and nonexistent `tu_scheduler_*` / `tu_liveness_*` prefixes. **Resolved:** the script now uses exhaustive call patterns `tu_ctx_[A-Za-z0-9_]+`, `tu_sched_[A-Za-z0-9_]+`, and `tu_live_[A-Za-z0-9_]+`, while excluding only each subsystem's own implementation/header plus tests/docs. The regenerated output is byte-identical at the recorded SHA-256 and still reports zero non-test external callers for all three surfaces.

### R5 — focused caller-inventory re-review (`deleg_a21d5056`)

**PASS.** Exhaustive regexes covered all 19 public `tu_ctx_*`, 9 public `tu_sched_*`, and 7 public `tu_live_*` APIs found in the pinned headers. Independent whole-tree search found no caller outside each subsystem's own implementation/header, tests, or docs. The rerun returned all three zero-caller rows and `caller_inventory=PASS`; its combined-output log was byte-identical to the retained log at SHA-256 `3e3935525857e30ad10d64c53d68ee3f2354dbae5636de01016d153975735945`. No blocker/high finding remained.

## Technical findings that the predraft audit must not lose

The framing review elevated these from comments to required evidence gates:

- copied `tu_state_t.dma` is not the process-global operative `g_tu_dma` descriptor engine;
- `tu_core_sync()` drains the core command queue but not operative global DMA;
- command-queue contents/signals/counters are not context-retained;
- process-global rounding mode and stochastic PRNG are not context-owned;
- dataflow pointer restoration does not restore process-global mutable plugin internals;
- aggregate bank metadata and per-bank bandwidth/arbitration state have different retention behavior;
- direct restore can create two ACTIVE descriptors;
- rejected switches can be non-atomic because outgoing save precedes target restore validation;
- priority zero, completion reachability, dead controls, request timing, and manager-local switch-cost accounting require executable discriminators;
- focused-green suites and sweeps are bounded evidence, not integration proof.

## Closure requirements

Before the framing content commit:

1. a final independent high-severity review must return PASS on the current framing plan, this disposition record, reproduction script/log, PLAN, README, and handoff;
2. `git diff --check` and relative-link checks must pass;
3. pinned Tusim must remain detached and clean;
4. historical Chapter 17 notes and retained run files must have no working-tree diff.

After the framing content commit:

1. update only `commit=` in `notes/chapter-17-reviewed-snapshot.txt` to the framing governance-content commit;
2. run Chapter 17 manuscript validation under normal and optimized Python;
3. commit that marker-only change;
4. do not publish or push.
