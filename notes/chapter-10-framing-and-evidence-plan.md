# Chapter 10 Framing and Evidence Plan — DMA Descriptor Contracts and Tick-Driven Execution

- **Edition:** Tusim `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Book workspace:** `/home/zxy/Workplace/books/tusim-book`
- **Source workspace:** `/home/zxy/Workplace/projects/tusim` (detached, clean, read-only)
- **Status:** evidence revision after blocked skeptical review; drafting remains blocked until re-review clears the revised bundle

## Prerequisite graph and why this chapter follows Chapter 9

Chapter 9 established storage surfaces, bank mapping, bandwidth budgets, and raw-pointer bypass. Chapter 10 asks a different question: what transfer contract can describe movement into or out of those surfaces, and what state transitions are observable in Tusim?

This sequence does not follow a deferred-topic list. It follows a dependency:

```text
Chapter 4: configuration parsing and runtime propagation
        ↓
Chapter 5: public APIs, singleton ownership, lifecycle, and reset
        ↓
Chapter 6: MMA geometry and tiling
        ↓
Chapter 9: storage surfaces and access semantics
        ↓
Chapter 10: transfer representation, tick-driven execution, and lifecycle evidence
```

ISA dependency scheduling, address-generation mathematics, DRAM calibration, double buffering, and compute/transfer overlap remain outside the reader decision.

## Ranked candidate boundaries

| Rank | Candidate | Reader-decision coherence | Consumers/clocks/counters | Testability | Disposition |
|---:|---|---|---|---|---|
| 1 | **DMA Descriptor Contracts and Tick-Driven Execution** | selects representable transfer form and safe caller-managed lifecycle | one descriptor engine; explicitly contrasts legacy wrappers and inactive adjacent modules | exact constructors, executor, queue/tick probes, and call-site audit | **selected** |
| 2 | DMA Descriptors and Asynchronous Data Movement | similar contract, but “asynchronous” can imply stronger concurrency, dependency visibility, or physical transfer overlap than the pin provides | descriptor engine only | testable with heavy qualification | rejected as title; retained as one mode inside the chapter |
| 3 | Data Movement: DMA, Address Generation, and Overlap | too many decisions: transfer geometry, address production, buffering, scheduling, and performance | separate APIs, clocks, counters, and reachability | focused tests do not establish one integrated path | rejected and split |
| 4 | Memory-System Timing and Bandwidth | asks calibration/contestion questions not answered by descriptor execution | descriptor estimates and standalone DRAM/hierarchy differ | would require separate calibration evidence | deferred |

## Reader decision

> Given a transfer pattern and caller-managed ordering requirement, which Tusim transfer representation is expressible at the pinned revision, which object lifetimes and queue states are safe to rely on, and which functional, lifecycle, timing, and integration conclusions are supported by the executed path?

The chapter must leave the reader able to reject unsupported conclusions—not merely choose an API.

## In scope

1. Linear, 2D, 3D, scatter, gather, and multicast descriptor geometry.
2. Distinct byte quantities: source payload, requested/delivered fanout bytes, accounted transfer bytes, unique bytes touched, and addressed span.
3. Borrowed versus copied descriptor metadata and buffer lifetimes.
4. Lifecycle predicates: constructed, accepted, pending/reachable, selected into executor, executor returned, bytes directly host-observable, flag set, timestamp eligible, channel retired, and storage safely reusable.
5. Synchronous submission, tick-driven mode, channel slots, pending-head capacity, and flush.
6. Non-composability of descriptor chains and queue linkage at the pin.
7. Path-specific service estimates, queue wait, occupancy, and aggregate counters.
8. Legacy W/A load and O-store wrappers, O-load bypass, command-queue routing, and split counter domains.
9. Parsed versus active DMA configuration.
10. Exact integration/fidelity labels and safe design regimes.

## Explicitly deferred

- Full address-generator mathematics and iterator correctness.
- Standalone DRAM/hierarchy calibration and physical memory traffic.
- Double-buffer design and valid DMA-to-shadow integration.
- Compute/DMA overlap, software-pipeline throughput, or speedup.
- ISA descriptor encoding and dependency scheduling.
- Sparse-operator/compiler integration.
- Coherence, virtual memory, cache maintenance, interrupts, RTL, FPGA, silicon, area, power, and energy.

Boundary probes may demonstrate why a topic is deferred. They do not pull that topic into scope.

## Source map

### Pinned implementation

| Surface | Authoritative files | Safe question |
|---|---|---|
| Descriptor API/state | `tu_cmodel/dma_descriptor.h` | fields, types, counters, ownership surfaces |
| Constructors/executor/queue/tick | `tu_cmodel/dma_descriptor.c` | actual geometry, copy, accounting, lifecycle, linkage |
| Compatibility API | `tu_cmodel/tu_dma.[ch]` | implementation location and legacy contract |
| Public wrappers | `tu_cmodel/tu_cmodel.[ch]` | W/A/O reachability and counter sampling |
| Command queue | `tu_cmodel/command_queue.[ch]` | fixed operation routing and separate signal registry |
| Configuration | `tu_cmodel/infra/config.[ch]`, `tu_cmodel/tu_config.h`, `config/tu_config.{json,yaml}` | parsed, converted, and compile-time fields |
| DRAM/hierarchy boundary | `tu_cmodel/memory/{dram_model,memory_hierarchy}.[ch]` | exact consumers; no inferred descriptor integration |
| Address/double-buffer/pipeline boundary | `tu_cmodel/memory/{address_generator,double_buffer}.[ch]`, `tu_cmodel/compute/pipeline_controller.[ch]` | focused/linkage boundary and unsafe integration evidence |
| Build and tests | `Makefile`, `tests/test_{dma,scatter_gather,multicast,address_gen,double_buffer,pipeline,command_queue,cmodel,config}.c` | archive membership, target membership, focused cases, harness quality |

### External primary sources

| Source | Safe use | Scope guard |
|---|---|---|
| [SMI84](../references/foundations.md#smi84-decoupled-accessexecute) | queue-connected access/execute motivates capacity, synchronization, and loss-of-decoupling questions | not a modern descriptor or tensor-accelerator contract |
| [GEN21](../references/foundations.md#gen21-gemmini) | full-stack movement/execute integration shows why reachability matters | one architecture; no numerical transfer to Tusim |
| [JOU17](../references/foundations.md#jou17-production-tpu-analysis) | explicit movement and software-managed storage are architectural concerns | no undocumented Tusim mechanism inference |
| [PAR19](../references/foundations.md#par19-timeloop) | separates workload, architecture, mapping, and constraints before deriving movement | not a queue/completion protocol |

## Executable evidence plan

Canonical runner: `experiments/run_ch10_data_movement_audit.sh`

Canonical revised run: `experiments/runs/ch10-dma-contracts/20260727T223000Z-hashguard/`

### Fail-closed gates

1. Verify exact Tusim pin, detached state, clean tracked/nonignored state, and unchanged ignored inventory before/after.
2. Verify book HEAD/branch/status and zero remotes before/after.
3. Export with `git archive`; clean/build only the disposable tree.
4. Enforce 33 source/test/config SHA-256 values and 32 structural/reachability predicates through `experiments/ch10_source_audit.py` (65 checks total), including destructive reinitialization and the fixed channel-array boundary.
5. Enforce required archive members and explicit static linkage; reject shared `libtucmodel` resolution.
6. Require both custom probes to return nonzero on any failed check and end with zero failures.
7. Preserve a self-verifying relative-path manifest for all retained evidence inputs/logs, including the final transcript hash.
8. Remove disposable source/archive automatically through an EXIT trap.

Pinned focused harnesses are **observations**, not the fail-closed correctness gate. `test_config.c` has a weak failure-return contract; the address-generator harness has one expected failure; the unsafe four-channel pipeline harness is statically skipped.

### Discriminating probes

- Tick-by-tick 64-byte linear lifecycle.
- Same-tick two-channel dispatch.
- Pending-head admission and synchronous-chain underflow.
- Chain-plus-queue structural corruption before and after selection; no destructive traversal of corrupted graphs.
- Bus-width boundaries at 0, 1, 31, 32, 33, 64, and 65 bytes.
- Descriptor-store producer formula.
- Nonsymmetric 2D/3D canary oracles and span equations.
- Duplicate-index scatter and multicast payload/fanout taxonomy.
- Borrowed source/index mutation before execution.
- SRAM bandwidth modeling on/off and shared/separate-region comparison.
- Non-default config path versus direct DMA initialization.
- Legacy-wrapper counter split.
- Bounded address-generator and pipeline probes that justify deferral.

## Skeptical-review gates

### Architecture/methodology

- Are chain and queue linkage composable? If not, is the safe subset explicit?
- Are lifecycle predicates observable and non-overlapping?
- Are ownership and reuse rules stated per object and outcome?
- Are byte quantities and addressed spans separated?
- Are service estimate, waiting, occupancy, and aggregate sums distinct?
- Are decision regimes limited to representability, metadata/lifetime burden, safety, pending-head capacity, synchronization, and verification effort?

### Repository/reachability

- Are exact hashes/call sites/archive members enforced rather than printed?
- Which public operations call legacy wrappers, bypass them, or reach descriptors?
- Which configuration values parse but do not activate?
- Are static-link and unsafe-skip gates fail-closed?
- Is evidence reproducible without touching Tusim?

### Editorial/evidence

- Does every number name producer, units, formula, configuration, and evidence class?
- Is `completed` restricted by transfer/path and distinguished from success/retirement?
- Are known failures and skips visible?
- Are source identities and scope guards precise?
- Do fidelity labels use the style guide verbatim?

Drafting begins only after an independent re-review clears this revised bundle.
