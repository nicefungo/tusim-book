# Chapter 17 — Skeptical Review Dispositions

## Review provenance and verdict

An independent read-only reviewer inspected the full pinned measurement source, tests, config, Makefile, and documents at `e918c80b6fce833cd1fcae97730fa841c2176f25`. It did not trust framing labels or focused-green results. Its findings were reconciled into the live ledger and fail-closed predicates before the canonical run.

**Verdict:** canonical v1 received **REVISE**. Its arithmetic and manifests were verified, but incomplete configuration/lifecycle gates, optimizer-removable validator checks, and stale framing status blocked drafting. R15–R18 describe the v2 repairs. Drafting remains blocked until canonical v2 passes and an exact post-v2 re-review accepts it.

## Dispositions

1. **R1 — producer separation: RESOLVED.** Legacy state, newer perf counters, event-trace context, logging trace, cycle model, embedded perf energy, standalone power, and benchmark remain distinct claim families. No common interval or clock is inferred.
2. **R2 — perf reset wording: QUALIFIED.** Review found that reset preserves the entire power substructure, including accumulated energy, not merely parameters. C17.11 and the `PERF_RESET` probe now require this limitation.
3. **R3 — incomplete diff/merge algebra: QUALIFIED.** Review identified omitted WS/OS cycles, GBuf conflicts, DRAM row hit/miss fields, utilization fields, wall time/config, and cached energy total. C17.10, structural predicates, and omission sentinels now bound the API.
4. **R4 — first event tick: QUALIFIED.** Review confirmed the first context tick discards its delta and pending changes remain dirty. C17.15 and the exact two-step trace probe enforce this.
5. **R5 — claimed EOF marker: NEW FINDING, RESOLVED.** Close emits no dedicated EOF record; the focused test's `$end` search is vacuous because headers contain `$end`. C17.15a and a source predicate reject the stronger claim.
6. **R6 — cycle-model hazard/arbitration reachability: QUALIFIED.** Top-level tile calls complete their entry inside one serial call, and focused hazard/arbitration tests synthesize internal state. C17.23a prevents those tests from becoming ordinary overlapping-pipeline evidence.
7. **R7 — cycle/perf duplicate accounting: RESOLVED.** Attached perf recorders advance their own ledger; explicit model advance also ticks perf. The exact write-direction and bridge probe keeps private model time and perf time visible separately.
8. **R8 — DMA direction: NEW FINDING, RESOLVED.** A modeled write calls the perf read recorder. C17.25 and `CYCLE_WRITE` gate 32 read bytes and zero write bytes.
9. **R9 — power total cache: NEW FINDING, RESOLVED.** Standalone total energy is cached and can become stale after later actions. C17.32a requires recomputation after the last action.
10. **R10 — decorative power parameters: NEW FINDING, RESOLVED.** Several table fields have no retained total-energy consumer. C17.32b and a predicate prevent table presence from implying action coverage.
11. **R11 — snapshot ordering hazards: RESOLVED.** Perf integers clamp decreasing snapshots while perf energy can go negative; standalone power uses raw unsigned subtraction and wraps. The probe gates the latter with exact wrapped values and negative energy.
12. **R12 — calibration language: RESOLVED.** IEEE VCD, Horowitz, HPE CACTI, and vendor PMU sources are bounded in a separate primary-source ledger. No source transfers calibration to Tusim.
13. **R13 — benchmark interpretation: RESOLVED.** The benchmark manually authors inputs, double-ticks compute, and has no fail-closed result count. It is a forensic consumer, not measured application performance.
14. **R14 — chapter boundary: RESOLVED.** The planned prose remains metric-provenance work. Mutation/CI/evidence-selection methodology stays in Chapter 19.
15. **R15 — decorative measurement configuration: NEW FINDING, RESOLVED FOR V2.** The post-v1 reviewer found shipped-but-unparsed power and trace-format fields, default-only `trace_max_events`, and retained-but-unconsumed `detailed_stalls`. C17.37a–c and four dedicated predicates now disposition each path.
16. **R16 — representative rather than field-complete lifecycle gates: NEW FINDING, RESOLVED FOR V2.** The probe now gives nondefault sentinels to every diff/merge omission named by C17.10, and the source audit checks all omitted fields. The additive-time probe and predicates now cover op, idle, SPAD-stall, DRAM-stall, GBuf, request-file, and pipeline-bubble behavior.
17. **R17 — optimizer-removable predraft validation: NEW FINDING, RESOLVED FOR V2.** All Python `assert` statements were replaced by unconditional `require()` failures. The validator rejects a bundled validator containing `assert`, and the runner executes it under both normal Python and `python3 -O`.
18. **R18 — stale framing status: NIT, RESOLVED FOR V2.** The framing status now identifies itself as a historical stage snapshot rather than claiming that later work has not begun.

## Hand recomputation record

- Perf additive time: `(10+2)+(5+1)=18`; duplicate explicit tick `18+6=24`.
- Estimated tile: pipeline depth 2 gives fill `2*3=6`, compute `4`, drain `2*2=4`, total 14.
- Named-cycle direct 32-byte write with fresh bank: one transfer cycle plus seven-word shortfall at penalty two gives `1+14=15`; implementation sends all 15 as perf read active cycles.
- Metrics: 10 cycles at 1000 MHz = 10 ns; `100 B / 10 ns = 10 GB/s`; `10 MAC / 10 ns = 0.001 TOPS`.
- 7-nm area: `(256*160 + (64+256)*2400)*1.30/1e6 = 1.051648 mm²`.
- Standalone energy: MAC 2.0 + SPAD 0.4 + DRAM read/activate 370 + DMA 0.64 + clock 0.1 + leakage 52.5824 = 425.7224 pJ; divided by 10 ns gives 42.57224 mW.

The canonical transcript, not this prose alone, must reproduce all values with `CH17_PROBE SUMMARY failures=0`.
