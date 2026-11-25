# Chapter 2 — How an Executable Model Earns Trust

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-2)

> **Historical case study.** All Tusim source, build and execution observations below refer to July 25, 2026 (`e918c80`), including the standalone 2,619-cycle result. Neither build membership nor that result was retested here on the November 18 edition pin (`7a094ff`).

## Opening question

Suppose a simulator prints `2619 cycles` beneath the label `CYCLE_ACCURATE`. What, exactly, has been established?

The number may have been computed deterministically. A unit test may reproduce it. The source may contain structures named pipeline, bank, row buffer, and arbiter. None of those facts alone proves that `2619` predicts a hardware implementation, corresponds to the main runtime path, or can be compared fairly with a cycle count from another subsystem.

This chapter develops the discipline needed to interpret such a result. The central principle is:

> **Every model result is a conditional claim about a defined workload, configuration family, accounting boundary, and model contract—not a fact about accelerators in general.**

Tusim is most useful when treated as a family of executable architectural hypotheses. Trust does not come from implementation volume, realism-sounding names, or a fidelity enum. It is earned by making contracts explicit, testing internal correctness, comparing against appropriate references, exposing uncertainty, and restricting conclusions to decisions the evidence can support.

## Learning objectives

After completing this chapter, readers should be able to:

1. define a model contract in terms of boundary, semantics, state, transitions, observables, assumptions, and invariants;
2. distinguish functional, analytical, transaction-level, cycle-estimate, RTL, FPGA, and silicon evidence;
3. treat fidelity as multidimensional rather than as one ladder from “low” to “high”;
4. separate verification, validation, and calibration;
5. use dimensional analysis, conservation laws, limiting cases, and analytical bounds to test a model;
6. identify parameter, workload, and model-form uncertainty;
7. determine when subsystem timing estimates may be added, overlapped, or not composed at all;
8. design experiments that support causal explanations rather than mere correlations;
9. compare alternatives using constraints and Pareto trade-offs;
10. audit whether a Tusim feature is present, linked, configured, reachable, tested, and calibrated.

## 2.1 A model is an argument about a decision

A model is not trustworthy in isolation. It is trustworthy *for a purpose*.

Consider four stakeholders:

- an architect choosing between 16×16 and 32×32 PE arrays;
- a compiler engineer selecting tiles and dataflow;
- a verification engineer checking numerical and ordering semantics;
- a product engineer estimating whether a latency target is feasible.

The same executable program may provide useful evidence to one stakeholder and inadequate evidence to another. A functional CModel can expose an incorrect accumulation order or layout mismatch, but it cannot determine timing closure. An analytical traffic model can reject a configuration that exceeds a bandwidth roof, but it cannot prove the absence of queueing stalls. RTL can establish cycle behavior under its interface contract, but pre-layout RTL does not establish final clock frequency or silicon energy.

The correct first question is therefore not “How detailed is this simulator?” It is:

> **Which decision is being made, and what evidence would change that decision?**

A decision question should identify:

1. the alternatives;
2. the workload regime;
3. the constraints;
4. the metrics;
5. the model boundary;
6. the evidence threshold;
7. the rejection conditions.

For example:

> For GEMMs sampled from a named transformer prefill workload, under fixed SRAM capacity and external bandwidth, does a 32×16 array reduce estimated service latency relative to 16×16 without pushing occupancy below 70% or increasing required SRAM ports beyond the allowed design?

This question is stronger than “Is a larger array faster?” It fixes a regime, exposes constraints, and permits a negative answer.

### Models as executable hypotheses

An executable architecture model can be understood as a hypothesis with five layers:

```text
claim about a design
    ↕
metric and accounting definition
    ↕
modeled mechanisms and state transitions
    ↕
workload, mapping, and environmental assumptions
    ↕
implementation, tests, and calibration evidence
```

If any layer is implicit, two users can run the same code and draw incompatible conclusions without either noticing that they answered different questions.

---

## 2.3 Fidelity is a vector, not a rank

It is tempting to arrange models on one ladder:

```text
functional < analytical < cycle-level < RTL < silicon
```

That ordering is misleading. Fidelity has multiple dimensions:

| Dimension | Question |
|---|---|
| Numerical | Are datatype, accumulation, rounding, exceptional values, and output semantics represented? |
| Ordering | Are dependencies, barriers, visibility, and completion order represented? |
| Traffic | Are transfers counted at the correct hierarchy boundaries under the actual mapping? |
| Timing | Are durations and state transitions modeled at the required temporal resolution? |
| Contention | Do shared resources, arbitration, queues, and backpressure interact? |
| Area/energy | Are physical costs connected to a technology and calibrated component model? |
| System context | Are host, runtime, operating-system, and neighboring accelerator effects represented? |
| Workload | Does the benchmark distribution represent the intended deployment regime? |

A functional reference may have high numerical fidelity and zero timing fidelity. A cycle simulator may model arbitration carefully but use simplified numerical operations. An RTL block may have exact local timing while being evaluated with unrealistic memory responses. A silicon measurement is physically real but may not generalize beyond its process, voltage, frequency, software, or workload.

### A useful fidelity vector

For a claim `C`, write:

$$
F(C) = (F_n, F_o, F_{tr}, F_{time}, F_c, F_e, F_s, F_w),
$$

where the components represent numerical, ordering, traffic, timing, contention, energy, system, and workload fidelity. The notation is conceptual; the components need not be reduced to scores. Its purpose is to force the author to ask *which* fidelity matters.

More detail can reduce trust if it introduces untested assumptions. A simple compulsory-traffic lower bound may be more defensible than an elaborate event model whose queue semantics are inconsistent.

---

## 2.4 Defensible evidence labels

The following labels are used throughout this book.

| Label | What it supports | What it does not support |
|---|---|---|
| **Functional model** | Results follow declared numerical, layout, and command semantics | Timing accuracy |
| **Analytical model** | Named equations estimate aggregate operations, traffic, cycles, area, or energy | Arbitrary event interaction |
| **Deterministic lower bound** | An optimistic minimum under explicit idealizations | Realized latency |
| **Cycle estimate** | Cycles follow declared schedules and resource assumptions | RTL equivalence |
| **Transaction/event model** | Transactions or events obey explicit ordering and contention rules | Accuracy below represented events |
| **Cycle-accurate model** | Declared state, interface, and ordering observables correspond at cycle indices to a named reference over a stated validation suite and acceptance criteria | Unlisted state, excluded mechanisms, behavior outside the suite, or final silicon frequency |
| **RTL behavior** | Register-transfer behavior under a specified clock, reset, and interface contract | Post-layout frequency, power, or product performance |
| **FPGA prototype** | Behavior of the mapped prototype on a named FPGA implementation | ASIC area, timing, or energy without translation models |
| **Silicon measurement** | Behavior of a fabricated device under stated operating conditions | Transfer to another design or environment |
| **Calibrated estimate** | Error against a named reference is measured over a stated suite | Universal accuracy outside that suite |

A C enum named `CYCLE_ACCURATE` is an implementation mode name. It becomes an evidence label only after the model contract and validation justify it.

### Comparison with established frameworks

Different frameworks answer different questions:

- **Aladdin** models pre-RTL accelerator behavior from dynamic dependence graphs and resource constraints, with validation against synthesized designs [SHA14].
- **Timeloop** separates workload, architecture, mapping, and constraints to evaluate data movement and mapping choices [PAR19].
- **MAESTRO** uses a data-centric mapping description to analyze reuse, bandwidth, buffer requirements, and performance [KWO19].
- **SCALE-Sim** models systolic-array execution and memory traffic under specified array and dataflow assumptions [SAM18].
- **Accelergy** separates action counts from technology-dependent energy estimation through component models and plug-ins [WU19].
- **Gemmini** demonstrates why full-stack effects matter when evaluating accelerator generators [GEN21].

None is simply “more accurate” than the others. Each has a different contract and validation scope.

---

## 2.6 Bounds and sanity checks

Before trusting a detailed result, compute simpler bounds.

### Compute roof

If a design has `R×C` PEs, one MAC per PE per cycle, and clock frequency `f`, then:

$$
P_{\text{peak,MAC}} = R C f.
$$

If one MAC is counted as two arithmetic operations:

$$
P_{\text{peak,ops}} = 2 R C f.
$$

An achieved useful-operation rate above this roof indicates inconsistent operation counting, clock assumptions, or concurrency.

### Bandwidth roof

At a named boundary with bandwidth `B` and operational intensity `I`:

$$
P \leq B I.
$$

This is the Roofline bandwidth bound [WAT09], not a queue simulation. Its simplicity makes it valuable: a detailed model exceeding the bound under the same accounting convention is suspect.

### Compulsory traffic

For `W[M,K]A[K,N]=O[M,N]`, a simplified minimum payload under a **dense, materialized-tensor, cold-boundary contract**—both inputs cross the boundary once and one FP32 output crosses it once—is:

$$
Q_{\min} = 2MK + 2KN + 4MN \quad \text{bytes}.
$$

Real traffic can be higher because of tiling, partial-sum spills, metadata, alignment, and repeated fetches. A lower value requires changing the stated contract—for example through compression, sparsity, pre-resident or generated operands, omitted output writeback, different representation, or a different accounting boundary.

### Fill, steady state, and drain

A regular pipeline often admits a lower-bound decomposition:

$$
T \geq T_{\text{fill}} + T_{\text{steady}} + T_{\text{drain}}.
$$

The exact terms depend on dataflow and geometry. Treating this equation as universal cycle accuracy would be wrong; using it to check order of magnitude is appropriate.

### Conservation and dimensional checks

Useful checks include:

- cycles × bytes/cycle = bytes;
- accesses × bytes/access = traffic;
- MACs = `MNK` under dense GEMM semantics;
- FLOPs = `2MNK` only when the two-operation convention is declared;
- energy/action × action count = energy;
- occupancy never exceeds queue capacity;
- a percentage defined as a fraction remains between zero and one.

A model that violates a simple invariant should not be rescued by its complexity.

---

## 2.8 When cycle estimates compose

Suppose compute time is `T_c` and data-transfer time is `T_d`. Three common formulas appear:

$$
T = T_c + T_d,
$$

$$
T = \max(T_c,T_d),
$$

and

$$
T = T_c + T_d - T_{\text{overlap}}.
$$

None is universally correct.

### Addition

Use addition when phases are serialized by dependency or shared resources. Examples include loading an input before compute starts and storing an output after completion when no double buffering exists.

### Maximum

Use the maximum only when the architecture and schedule permit full overlap after startup. Required mechanisms may include:

- independent DMA and compute engines;
- separate or sufficiently ported buffers;
- double buffering;
- legal dependencies;
- queue capacity;
- bandwidth to sustain both activities;
- explicit startup and drain treatment.

The existence of two engines does not prove overlap.

### Joint schedule

When compute, DMA, and other engines share SRAM ports, buses, queues, or dependencies, neither sum nor maximum may be correct. A joint event/resource model is needed.

### Incompatible cycle domains

Two counters cannot be added merely because both use the unit “cycles.” They must share:

- a clock definition;
- a start and end boundary;
- overlap semantics;
- stall attribution;
- resource state;
- event ordering.

Tusim’s stable snapshot contains several accounting domains. The main `g_tu.estimated_cycles` path uses aggregate DMA/MMA formulas. Elementwise operations also maintain SRAM bank stall cycles. The standalone cycle-model prototype maintains another `current_cycle`. Adding all three would double-count some costs and combine incompatible assumptions.

A useful ledger for each metric records:

| Field | Example |
|---|---|
| Clock | TU core cycles at assumed 1 GHz |
| Boundary | one tile from issue to local writeback |
| Included | decode, encoded bank penalty, MAC loop |
| Excluded | host, main runtime queue, physical SRAM delay |
| Overlap | none in sequential function call |
| Stall attribution | shortfall words × fixed penalty |
| Calibration | none |

Only metrics with compatible ledgers may be composed.

---

## 2.13 A practical claim-audit checklist

Before publishing any Tusim result, answer:

### Decision

- What decision could this result change?
- What alternatives and constraints are in scope?

### Workload

- Which shapes, operators, layouts, precisions, dependencies, and service constraints are represented?
- Is the suite representative of the claimed regime?

### Execution path

- Does the source exist?
- Is it compiled and linked?
- Is it reachable from the public/runtime path?
- Does the stated configuration propagate to the consuming mechanism?
- Is the exact path exercised by focused and aggregate tests?

### Metrics

- What is directly observed?
- What is derived?
- Are units, boundaries, denominators, intervals, and clock domains defined?
- Can the metric compose with other reported values?

### Evidence

- Is the result functional, analytical, a lower bound, a cycle estimate, calibrated, RTL, or silicon?
- Against which reference was it validated?
- What error was observed across which suite?

### Conclusion

- Which costs and alternatives were evaluated?
- What remains unmodeled?
- What alternative explanations survive?
- What evidence is needed before a hardware recommendation?

[Next: Chapter 3 — Repository Tour and First Execution](03-repository-tour-and-first-execution.md)
