# Chapter 9 Framing and Evidence Plan — Memory Hierarchy and Banked Scratchpads

- **Edition:** Tusim `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Book workspace:** `/home/zxy/Workplace/books/tusim-book`
- **Source checkout policy:** read-only, detached, pinned, and clean
- **Status:** framing complete; manuscript drafting must not begin until the source/claim ledger and executable gates below exist

## Authoritative title decision

**Chapter 9 — Memory Hierarchy and Banked Scratchpads**

This title is derived from the live edition rather than an unverified roadmap:

1. Chapters 6–8 establish tensor geometry, dataflow, and stored numerical representations, but deliberately leave physical data movement and coherent memory timing unresolved.
2. The pinned repository's top-level architecture identifies `memory/` immediately after precision, compute, and dataflow, and names banked SRAM, hierarchy, DRAM, and double buffering as distinct components.
3. `source-audit.md` classifies banked SRAM and the memory hierarchy as independently executable, while DMA, DRAM, and double buffering have separate APIs, tests, and fidelity limits.
4. `docs/memory-hierarchy.md` calls the hierarchy foundational and explicitly treats double buffering, address generation, and multicore sharing as subsequent work built on it.
5. The live implementation shows that the four-level hierarchy is standalone: `tu_mem_hierarchy_*` is called only by its implementation and focused test, not by `tu_cmodel.c` or `tu_core.c`.

The chapter therefore teaches the storage-level and banking contract first. Detailed descriptor DMA, DRAM timing, address generation, and overlap belong to a later data-movement chapter. DRAM delegation and DMA/raw-pointer bypass appear only as boundary evidence.

## Reader decision

After reading Chapter 9, a reader should be able to decide:

> Given a tensor working set and byte-address access pattern, which capacity, memory level, bank mapping, and bandwidth-budget alternatives can Tusim actually compare at the pinned revision—and which apparent hierarchy or stall results are disconnected from the direct MMA path and therefore unsafe to use as end-to-end performance evidence?

This is a decision about **model applicability**, not a request to select one universally optimal memory organization.

## Opening architecture question

A tensor fits in on-chip bytes. Does that prove it can be supplied at the required rate?

The chapter separates five contracts that are often collapsed:

1. capacity and placement;
2. byte-to-bank mapping;
3. port or budget service;
4. latency/stall accounting and cycle advancement;
5. integration into the operation being evaluated.

## Scope

### In scope

- software-managed scratchpads versus caches at the conceptual level;
- working-set capacity, traffic boundary, reuse, and operational intensity;
- W/A/O byte footprints inherited from Chapters 6 and 8;
- `tu_sram_region_t`, bank mapping, bandwidth meters, refills, stalls, statistics, raw-pointer bypass, and double-buffer pointer selection only where it changes access semantics;
- standalone `tu_memory_hierarchy_t`: RegFile, LocalSPAD, GlobalBuf, and DRAM delegation;
- configuration authority and effective values for capacities, bank count, bank width, and hierarchy defaults;
- focused tests, archive-only static linkage, and discriminating custom probes;
- fidelity limits and design alternatives across performance, area/power, compiler responsibility, complexity, and verification.

### Explicitly out of scope

- detailed DRAM timing/preset correctness;
- descriptor/channel/scatter-gather DMA semantics;
- double-buffer overlap and pipeline scheduling;
- address-generation semantics;
- cache coherence, NoC contention, IOMMU, or host-memory behavior;
- physical SRAM compiler timing, area, or energy;
- calibrated end-to-end DMA+MMA latency;
- repairing Tusim defects or modifying the source checkout.

## Source map

### Normative and primary background

| Source | Authority | Safe use | Scope guard |
|---|---|---|---|
| [BAN02](../references/foundations.md#ban02-scratchpad-memory) | primary architecture paper | software-managed scratchpad/cache distinction and placement responsibility | old-node quantitative results do not transfer to Tusim |
| [WAT09](../references/foundations.md#wat09-roofline-model) | primary analytical model | compute/bandwidth upper-bound reasoning with an explicit byte boundary | not a latency simulator and not a Tusim calibration |
| [JOU17](../references/foundations.md#jou17-production-tpu-analysis) | primary silicon/system study | on-chip storage, workload mix, and software affect achieved performance | TPU measurements do not transfer numerically |
| [CHE16](../references/foundations.md#che16-eyeriss) | primary accelerator paper | hierarchy and data reuse are jointly designed | row stationary is not universally optimal |
| [PAR19](../references/foundations.md#par19-timeloop) | primary modeling paper/project | architecture, mapping, workload, and constraints must be distinct | model output is not automatically RTL/silicon truth |
| [KWO19](../references/foundations.md#kwo19-maestro) | primary analytical model | data-centric mappings expose reuse, occupancy, and traffic questions | arbitrary queueing/backpressure is not implied |

### Pinned repository authorities

| Source | Claim family | Authority boundary |
|---|---|---|
| `tu_cmodel/tu_sram.[ch]` | byte storage, banks, budgets, refills, stalls, stats, raw access | active SRAM implementation; comments do not upgrade unused fields |
| `tu_cmodel/memory/memory_hierarchy.[ch]` | four named levels, counters, GBuf, RegFile abstraction, DRAM delegation | standalone hierarchy API, not direct-MMA integration |
| `tu_cmodel/tu_config.h` | compiled capacities and default banking constants | effective for constructors that read these macros |
| `tu_cmodel/infra/config.[ch]` | parsed memory fields and runtime conversion | parser presence is weaker than propagation/consumption |
| `tu_cmodel/tu_cmodel.c`, `tu_cmodel/tu_core.[ch]` | W/A/O allocation and direct-operation reachability | authoritative for whether hierarchy counters affect direct MMA |
| `tu_cmodel/dma_descriptor.c` | SRAM API consumer at a boundary | referenced only to distinguish modeled access from raw/direct bypass |
| `tests/test_memory_hierarchy.c`, `tests/test_cmodel.c`, `tests/test_config.c` | focused asserted behavior | test names/comments do not prove unasserted timing or integration |
| `Makefile` | library membership and test linkage | target presence does not prove static archive selection without a link gate |
| `docs/memory-hierarchy.md`, `docs/bandwidth-modeling.md`, `docs/configurable-pe-and-banking.md` | intended behavior and historical rationale | subordinate to executable behavior; conflicts must remain visible |

## Executable evidence plan

All builds and probes must run in a disposable archive of the pinned commit, never in `/home/zxy/Workplace/projects/tusim`.

1. **Pinned-source audit**
   - enforce full commit equality;
   - SHA-256-pin every inspected source, test, Makefile, and chapter script;
   - verify exact call-site sets for `tu_mem_hierarchy_*`, modeled SRAM APIs, and `tu_sram_raw_ptr()`;
   - fail on unexpected integration drift.
2. **Archive and linkage**
   - create a deterministic `git archive` from the pinned commit;
   - build cleanly in `/tmp/tusim-ch09-reproduction`;
   - statically link focused tests and the custom probe against the archive-built `libtucmodel.a`;
   - reject dynamic resolution of `libtucmodel.so` with `ldd` gates.
3. **Focused suites**
   - run `test-memhier`, `test-cmodel`, and `test-config` in archive-only mode;
   - preserve complete counts and literal output.
4. **Bank-map and budget probe**
   - distinguish sequential addresses across banks from repeated same-bank addresses;
   - assert exact served/stalled counts and refill behavior;
   - show that a reported stall charges accounting but does not defer the functional copy.
5. **Parameter-effect probe**
   - vary constructor budget, stall penalty, arbitration enum, and refill window;
   - prove which parameters affect results;
   - compare requested parsed banking values with constructed W/A/O bank count and width.
6. **Hierarchy-effect probe**
   - test RegFile zero-fill/no-storage semantics, LocalSPAD and GBuf data movement, counters, and DRAM delegation boundary;
   - prove whether `tu_mem_hierarchy_tick()` refills GBuf budgets;
   - prove whether `tu_mem_hierarchy_set_level_config()` survives initialization.
7. **Integration/bypass probe**
   - sample W/A/O SRAM counters around direct DMA and MMA;
   - distinguish bulk SRAM accounting from `tu_sram_raw_ptr()` compute bypass;
   - show that standalone hierarchy counters are not updated by direct MMA.
8. **Static safety findings**
   - inspect bounds-failure control flow, partial-word handling, bank allocation/config consistency, unused arbitration/conflict/latency fields, and counter reset completeness;
   - do not execute undefined or out-of-bounds behavior.
9. **Validation**
   - validate chapter contract sections, local links, citations, source-path references, quantitative denominators, evidence labels, transcript gates, and artifact hashes;
   - run shell/Python/C syntax checks and `git diff --check`.

## Skeptical-review gates

The chapter cannot close until all gates pass:

1. **Architecture reviewer:** challenge capacity/bandwidth/latency distinctions, bank equations, operational-intensity boundaries, and trade-off regimes.
2. **Repository reviewer:** challenge source reachability, config propagation, raw-pointer bypass, cycle/refill domains, unused fields, and test coverage.
3. **Methodology/editorial reviewer:** challenge every number, denominator, label, citation scope, unsafe causal statement, and textbook readability.
4. Treat every finding as a hypothesis; verify against the pinned source or executable probe before editing.
5. Record accepted, qualified, and rejected findings with rationale.
6. Rerun all affected probes and validators after revisions.
7. Verify Tusim HEAD/status and ignored inventory before and after execution.
8. Require README, source audit, fidelity matrix, ledger, manuscript, experiment report, and handoff to agree.
9. Use a two-commit closure: content commit first, then a separate handoff commit naming the immutable content revision.
10. Do not push and do not add a remote.

## Claims the chapter must not make

- that bank-count or hierarchy configuration parsed from JSON is behaviorally active without a discriminating probe;
- that the standalone hierarchy is used by direct MMA merely because it is library-linked;
- that `arb_mode` names imply implemented arbitration state;
- that a stall return value represents a queued or delayed access;
- that `conflicts`, utilization, and stalls are interchangeable metrics;
- that hierarchy base-latency fields are charged merely because they exist;
- that GBuf “hit” means cache-tag lookup or reuse;
- that RegFile reads return stored data;
- that a clean Git status proves archive-only linkage;
- that any result is calibrated to physical SRAM, RTL, or silicon.
