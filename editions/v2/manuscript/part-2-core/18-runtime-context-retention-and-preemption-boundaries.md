# Chapter 18 — Runtime Context Retention and Preemption Boundaries

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-18)

Context 0 spends its last SRAM grant. Its next read returns the right four bytes and a penalty of two. Now insert a visit to context 1 between the same two reads. Context 0 comes back at the same SRAM cycle, reads the same bytes, and pays **zero**. What did the manager restore, and what kept running on the core?

**Chapter contract.** A manager can save and restore selected state on one core. A successful switch is not a certificate of arbitrary preemption.

**Learning objectives.** Identify the caller's obligations at suspension; distinguish descriptor ownership from core dispatch; predict which bytes and counters survive each retention policy; and reconcile a returned bank penalty with a manager cost ledger without adding the two. Chapter 9 supplies the bank and word vocabulary; [Chapter 7](07-pluggable-dataflows.md) supplies the distinction between plug-in selection and plug-in ownership.

## 18.1 Start with the continuation, not the copy

Suppose the next instruction will accumulate into a partial sum in O. Saving the weights but not that sum will not suffice, unless software can reconstruct it. Saving all of O **before** its last producer finishes will not suffice either. Four questions must have answers: **Where may execution stop? Which state is still needed? Who owns the core on return? Who completes, shares or reconstructs everything not in the descriptor?** Only then is it meaningful to compare the costs of two role exchanges.

A safe point is a boundary at which earlier effects are complete or their ownership has been transferred. A C function entry is a place to invoke code. They coincide only by caller contract. In the experiment the caller issues one synchronous scalar operation at a time, launches no work on another engine, and explicitly chooses each switch. It is not interrupting a running kernel.

## 18.2 Two operations often called a “context switch”

| Question | Manager save/restore | Per-core dispatch |
|---|---|---|
| What is selected? | A descriptor in a manager attached to **one** `tu_core_t`. | A `tu_core_t` on which a wrapper will execute an operation. |
| What is moved? | `tu_ctx_save` takes a selective snapshot including separate retained SRAM byte arrays; `tu_ctx_restore` copies back into the core's existing regions. | `core_swap_in` temporarily copies `core->state` into `g_tu`; `core_swap_out` writes it back and restores the previous global struct. These are struct copies, not new SRAM allocations. |
| How does dataflow selection work? | Save/restore carries `state.dataflow`, a pointer, not a private copy of its target. | `tu_core_set_dataflow` looks up the registry entry and writes `core->state.dataflow`; `tu_core_mma` dispatches with that state installed. The registry object is still shared. |
| Which was exercised here? | Explicit `tu_ctx_switch(m,1)` then `tu_ctx_switch(m,0)`; ordinary save calls core sync. | Save uses the core swap wrapper for queue sync. There is no second core, dataflow change or MMA in this experiment. |

Read `tu_cmodel/infra/tu_context.c:127–148,225–246,398–470` alongside `tu_cmodel/tu_core.c:110–147,201–235`. The same word *swap* can mean “temporarily install the state for this call” or “resume a descriptor after restoring retained bytes.” Only the latter exercises the retention scopes. The manager is a C API; neither these wrappers nor a configured dataflow mode supply a scheduler or a compiler-produced safe point.

## 18.6 Retained SRAM: a byte policy and a meter policy are different things

| Scope | Saved primary W/A/O bytes | Obligation before the next use |
|---|---|---|
| FULL | The complete capacity of each region | Handle non-primary and in-flight state separately. |
| LIVE-prefix | One caller-specified prefix per region | Prove the omitted tails dead, or reload them. Size validation is not liveness analysis. |
| CONTROL-only | None | Reconstruct every required SRAM value. No copy does not mean no resume work. |

*Historical illustration.* With a one-float W prefix, v1 saved `[1.0, 2.0]`, let another context leave `[10.0, 20.0]`, and restored `[1.0, 20.0]`. The second element did not come from the snapshot. The parallel question about **meter state** remains even when FULL eliminates all unretained primary bytes.

The manager restores the region clock and aggregate access counts, but the physical bank keeps its grant and service history. In the FULL control, a second same-region access cost two penalty cycles. After a peer advanced five ticks and the original context resumed, the same access cost zero. The returned bytes agreed. The two paths differ in meter state, not in useful payload.

## 18.8 What does a switch cost?

The restore routine charges the manager a fixed cost `F` plus `ceil((pending outgoing bytes + target saved bytes) / W)` for positive state bandwidth `W`; at zero bandwidth it charges only `F`. The pending byte count is set by save. Do not automatically double the incoming byte count for a restore with no matching save.

In this fixture each FULL image retains `64 + 64 + 64 = 192 B`. An ordinary equal-size switch moves 384 primary bytes in the ledger, so `F=7` and `W=32 B/cycle` give `7 + 12 = 19`. The two switches report a cumulative **38**; the control reports zero. These 384 bytes are not the application's four-byte payload. Nor do those 19 cycles advance the A-region clock. Adding 38 to a bank penalty would not give elapsed time.

*Historical comparison, not rerun.* V1's LIVE example kept four bytes in each region. With `F=7`, `W=8`, its 12 retained bytes gave `7 + ceil(24/8) = 10` per ordinary switch. In v1's separate 256-KiB sweep (`F=100`, `W=32`), FULL, 25%-prefix and CONTROL gave 16,484, 4,196 and 100 ledger cycles. That ordering follows from counted bytes, not measured end-to-end performance; it prices neither dead-tail proof nor software reload.

## 18.9 Which state should own time?

One possible contract is **context-local meter time**: retain grants, timestamps, phase and counters with the region clock. On that contract the resumed context should still have its spent grant. This requires more descriptor storage and a decision about which control bytes count in the switch ledger. Another is **shared SRAM service**: keep both the meter and its clock monotonic on the core, and account for a task's private time separately. Then intervening service can affect the next grant by design. A third contract drains or resets the meter at a defined, charged boundary; an uncharged reset on each switch would need its own capacity argument. These are designs to compare, not implemented refill modes inferred from the trace.

Restoring a data image alone does not specify what happens to queue entries, timers or shared meters. State which ones the continuation needs before calling a switch transparent.

[Next: Chapter 19 — Static Scheduling and Scratchpad Allocation](19-static-scheduling-and-scratchpad-allocation.md)
