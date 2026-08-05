# Chapter 17 — Predraft Source Audit Report

## Scope and authority

This report audits Chapter 17's measurement surfaces at Tusim pin `e918c80b6fce833cd1fcae97730fa841c2176f25`. It keeps legacy state, `tu_perf_counters_t`, both trace implementations, the source-present cycle model, both energy producers, and the manual benchmark separate. No value is promoted to measured hardware time or calibrated power.

## Source gate

`experiments/ch17_source_audit.py` pins 31 source/config/test/doc hashes and 65 structural, caller, configuration, linkage, aggregate-membership, and documentation predicates: 96 checks total. It fails closed on pin/hash/predicate drift and inventories non-test callers.

Expected authority line:

```text
CH17_SOURCE_AUDIT PASS pin=e918c80b6fce833cd1fcae97730fa841c2176f25 hashes=31 predicates=65 checks=96
```

The current caller census is:

```text
CH17_CALLERS perf=tu_cmodel/perf/cycle_model.c event=none power=none cycle=none
```

This means only `cycle_model.c` calls the newer performance-counter family from non-test implementation code; the event-trace context, standalone power model, and cycle-model top-level API have no external non-test implementation caller.

## Build and focused controls

The canonical runner exports the pin into a disposable tree, builds `libtucmodel.a`, checks archive membership, links every binary explicitly, rejects dynamic `libtucmodel` dependencies, and runs:

- performance counters: 12/12;
- event trace: 31/31;
- logging trace: 7/7;
- standalone power: 20/20;
- runner-compiled cycle model: 21/21;
- benchmark: rc 0 with `Benchmark complete.`, qualified because no fail-closed result count exists;
- a forced performance-counter assertion mutation: expected 11/12 and nonzero status.

A green focused control proves only the named standalone contract. It does not prove ordinary caller reachability, common clocks, complete field algebra, or external calibration.

## Exact probe discriminators

The custom probe hand-derives and gates:

- additive perf time: DMA 10+2 plus MMA 5+1 gives total 18, while compute owns 6;
- an explicit second tick of 6 raises global perf time to 24 without changing compute time;
- diff/merge omission sentinels for WS cycles, GBuf conflicts, DRAM row hits, and cached total energy;
- reset preservation of accumulated embedded energy;
- 100 bytes over 10 caller cycles at 1 GHz gives 10 GB/s, while 10 MACs gives 0.001 TOPS;
- estimated cycle tile `2×3×4`: `2*3 + 4 + 2*2 = 14`;
- a named-cycle 32-byte modeled write takes 15 source cycles on fresh state and is recorded as 32 perf read bytes, zero write bytes;
- event-trace first tick drops delta 7 and retains a dirty signal, while the second tick advances to 3;
- logging trace stores caller-set cycles 0 and 9 in its separate buffer;
- standalone 7-nm action census and area heuristic: area 1.051648 mm², total 425.7224 pJ, average 42.57224 mW over the caller-authored 10-cycle/1-GHz interval;
- reversed standalone power snapshots wrap unsigned cycles/MACs and produce negative energy.

These values are source-defined deterministic observations, not physical measurements.

## External-source boundary

`references/ch17-measurement-primary-sources.md` verifies IEEE 1800-2023 VCD metadata and clause scope, Horowitz ISSCC 2014 metadata, the first-party HPE CACTI 7.0 prerelease artifact, and vendor-scoped PMU interval context. None transfers validation to Tusim. The absence of retained CACTI inputs/outputs/table generation or RTL/FPGA/silicon comparison requires `estimated`, not `calibrated`.

## Drafting boundary

Drafting is allowed only after the canonical runner seals the exact ledger, report, review dispositions, scripts, probe, and source evidence; the predraft validator must pass. The chapter may explain how to interpret each producer but may not create a unified timeline, total inference energy, measured benchmark, or physically calibrated TOPS/W result.
