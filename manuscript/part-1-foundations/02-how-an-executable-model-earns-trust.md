# Chapter 2 — How an Executable Model Earns Trust

> **Edition scope:** Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25`  
> **Evidence status:** concepts supported by primary literature; Tusim case study reproduced from pinned source; no RTL or silicon calibration is claimed

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

## Prerequisite graph

Chapter 1 introduced architecture questions, workload shape, operational intensity, dataflow, precision, system boundaries, and the distinction between observables and derived metrics. This chapter depends on those concepts in the following order:

```text
architectural decision
    ↓
workload + system boundary + numerical contract
    ↓
model state and transition contract
    ↓
observables and derived metrics
    ↓
verification, validation, and calibration
    ↓
controlled experiment + uncertainty
    ↓
conditional architectural conclusion
```

Readers do not yet need Tusim’s internal APIs. They do need matrix multiplication, introductory computer architecture, and the ability to distinguish a mathematical operation from its implementation schedule.

---

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

## 2.2 The model contract

A **model contract** states what the model accepts, what it represents, what it reports, and what it deliberately omits. The contract is the basis for every fidelity claim.

### 2.2.1 Boundary

The boundary names the modeled subsystem and its environment. For a tensor-unit study, possibilities include:

- only the PE array;
- PE array plus local register files;
- compute plus banked scratchpad;
- tensor core plus DMA and command queue;
- a cluster with interconnect;
- a full SoC execution path;
- an application service including host and software overhead.

A byte crossing the PE-local boundary is not necessarily a byte crossing DRAM. A stall inside an SRAM model is not automatically an end-to-end stall. Every traffic and latency metric must name its boundary.

A software-managed scratchpad also moves placement and lifetime responsibility from hardware replacement policy into the compiler or program contract [BAN02]. A model that counts scratchpad traffic but assumes perfect placement must state that assumption.

### 2.2.2 Workload and numerical semantics

The contract must define:

- tensor shapes, layouts, and strides;
- mathematical orientation of `M`, `N`, and `K`;
- precision of inputs, products, accumulators, and outputs;
- rounding, saturation, overflow, and subnormal behavior;
- sparsity and metadata semantics;
- operation counting convention;
- required functional tolerance or bit-exactness.

Without this layer, two cycle results can describe different computations. A faster FP16 path that accumulates differently from the required oracle may not be a valid alternative.

### 2.2.3 State and transition rules

State may include:

- PE pipeline occupancy;
- register dependencies;
- scratchpad contents and bank budgets;
- open DRAM rows;
- queue entries and command dependencies;
- DMA channels;
- partial sums;
- interconnect links and buffers;
- global and per-domain clocks.

For each transition, the contract asks:

- what event enables it;
- which resources it consumes;
- how long it occupies them;
- which state becomes visible afterward;
- what may overlap;
- how conflicts are resolved;
- whether ordering is deterministic.

A source file may contain structs for all these concepts yet update them only through aggregate formulas. The names do not establish temporal fidelity; transition semantics do.

### 2.2.4 Observables and derived metrics

An **observable** is recorded directly by the modeled execution: bytes, operations, issued commands, bank requests, stall events, or completed tiles. A **derived metric** combines observables under an equation.

For utilization,

\[
U = \frac{\text{used capacity over an interval}}
         {\text{available capacity over the same interval}}.
\]

The denominator must include the relevant resources *and time interval*. Dividing total accesses by the number of banks but not by elapsed cycles is not a time-average utilization. The resulting value may exceed one because it is an access density with a mislabeled denominator.

Likewise, a counter named `stall` may represent:

- stall events;
- denied words;
- blocked requests;
- cycles during which one requester waits;
- global cycles in which no useful work occurs.

These quantities are not interchangeable. Counter names are not definitions.

### 2.2.5 Invariants and omissions

A model contract should list properties that must always hold:

- nonnegative cycles and traffic;
- queue occupancy within capacity;
- reads and writes within storage bounds;
- completed work never exceeding issued work;
- utilization within `[0,1]` when defined as a fraction;
- operation and byte conservation under declared semantics;
- deterministic reproduction when randomness is disabled.

It should also list omissions such as:

- finite queues;
- arbitration details;
- physical wire delay;
- SRAM timing closure;
- clock-domain crossing;
- coherence;
- host scheduling;
- compiler suboptimality;
- layout conversion;
- leakage and thermal behavior.

Omissions are not defects when they match the decision. Hidden omissions are defects in the evidence contract.

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

\[
F(C) = (F_n, F_o, F_{tr}, F_{time}, F_c, F_e, F_s, F_w),
\]

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

## 2.5 Verification, validation, and calibration

These terms answer different questions. Unless a cited methodology is named, the distinctions below are this book’s operational definitions for organizing evidence; they are not a claim that all verification communities use identical terminology.

### Verification: did we implement our model correctly?

Verification checks conformance to the stated contract. Methods include:

- unit tests for state transitions;
- golden functional comparison;
- randomized differential testing;
- property and invariant checks;
- dimensional analysis;
- conservation of operations and bytes;
- known limiting cases;
- deterministic replay;
- source-to-counter reconstruction.

A test proving that a bank request incurs the configured penalty verifies a rule. It does not establish that the rule matches hardware.

### Validation: is this model suitable for the intended question?

Validation compares the modeled abstraction with the target phenomenon. Questions include:

- Are the dominant mechanisms inside the boundary?
- Are omitted mechanisms negligible in the target regime?
- Does the workload exercise the relevant behavior?
- Does the model preserve ordering and contention needed for the decision?
- Does the error remain acceptable across the intended configuration family?

A model can be verified but invalid for a decision. For example, a fill–compute–drain equation may be implemented perfectly yet omit memory stalls that dominate the deployment.

### Calibration: which values were fitted to which reference?

Calibration selects parameters using evidence such as:

- RTL traces;
- FPGA counters;
- synthesized SRAM timing;
- CACTI or vendor memory estimates;
- post-layout reports;
- silicon microbenchmarks.

A calibration report should include:

1. reference identity and version;
2. fitting suite;
3. parameters fitted;
4. objective or loss function;
5. residual/error distribution;
6. held-out validation suite;
7. regimes where error grows;
8. whether the calibration transfers across configurations.

“Uses realistic constants” is not calibration.

### The evidence ladder is not automatic

Passing unit tests is necessary but does not promote a functional model to a timing model. Matching one RTL trace does not prove generality. Validation should proceed through increasing diversity:

```text
formula and unit checks
    → focused integration tests
    → randomized/property tests
    → cross-model or analytical comparison
    → trace comparison to RTL/FPGA
    → calibrated residuals on held-out workloads
    → silicon comparison under named conditions
```

Each step supports stronger claims only within its boundary.

---

## 2.6 Bounds and sanity checks

Before trusting a detailed result, compute simpler bounds.

### Compute roof

If a design has `R×C` PEs, one MAC per PE per cycle, and clock frequency `f`, then:

\[
P_{\text{peak,MAC}} = R C f.
\]

If one MAC is counted as two arithmetic operations:

\[
P_{\text{peak,ops}} = 2 R C f.
\]

An achieved useful-operation rate above this roof indicates inconsistent operation counting, clock assumptions, or concurrency.

### Bandwidth roof

At a named boundary with bandwidth `B` and operational intensity `I`:

\[
P \leq B I.
\]

This is the Roofline bandwidth bound [WAT09], not a queue simulation. Its simplicity makes it valuable: a detailed model exceeding the bound under the same accounting convention is suspect.

### Compulsory traffic

For `W[M,K]A[K,N]=O[M,N]`, a simplified minimum payload under a **dense, materialized-tensor, cold-boundary contract**—both inputs cross the boundary once and one FP32 output crosses it once—is:

\[
Q_{\min} = 2MK + 2KN + 4MN \quad \text{bytes}.
\]

Real traffic can be higher because of tiling, partial-sum spills, metadata, alignment, and repeated fetches. A lower value requires changing the stated contract—for example through compression, sparsity, pre-resident or generated operands, omitted output writeback, different representation, or a different accounting boundary.

### Fill, steady state, and drain

A regular pipeline often admits a lower-bound decomposition:

\[
T \geq T_{\text{fill}} + T_{\text{steady}} + T_{\text{drain}}.
\]

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

## 2.7 Uncertainty and sensitivity

A deterministic program can produce an uncertain architectural prediction. Determinism describes reproducibility under inputs; uncertainty describes how well those inputs and equations represent the target.

### Parameter uncertainty

Examples include:

- achievable clock frequency;
- SRAM access time and energy;
- DRAM efficiency;
- router latency;
- arbitration penalties;
- leakage per cycle.

Represent uncertain parameters with ranges or distributions and report sensitivity. If the architecture ranking reverses inside a plausible range, the decision is not robust.

### Workload uncertainty

A benchmark suite may omit:

- decode-like narrow matrices;
- edge tiles;
- small reductions;
- long-tail service behavior;
- layout conversions;
- mixed operator pipelines;
- realistic dependency structures.

Report workload coverage and avoid treating one square GEMM as representative of an application.

### Model-form uncertainty

Model-form uncertainty arises when relevant mechanisms are absent or simplified:

- refill budgets instead of port-level arbitration;
- fixed penalties instead of queue state;
- ideal overlap instead of joint scheduling;
- hop count instead of finite network flow;
- payload bytes without decoder throughput;
- energy tables without physical implementation.

Unlike parameter uncertainty, model-form uncertainty cannot always be handled by sweeping a constant. A missing mechanism may require a different model.

### Sensitivity as a design result

If an option wins only when DRAM efficiency exceeds 90%, that threshold is itself useful. Architecture exploration should report:

- robust regions where rankings do not change;
- crossover points;
- uncertain regions requiring higher-fidelity evidence;
- parameters with little decision influence.

The purpose is not to manufacture one winner. It is to identify what must be known before committing.

---

## 2.8 When cycle estimates compose

Suppose compute time is `T_c` and data-transfer time is `T_d`. Three common formulas appear:

\[
T = T_c + T_d,
\]

\[
T = \max(T_c,T_d),
\]

and

\[
T = T_c + T_d - T_{\text{overlap}}.
\]

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

## 2.9 Controlled experiments and causal claims

A parameter sweep shows how outputs change when inputs change. It does not automatically establish why.

### Experimental contract

A defensible architecture experiment states:

1. decision question;
2. falsifiable hypothesis;
3. independent variables;
4. controlled variables;
5. workload suite;
6. observables and derived metrics;
7. invariants and sanity checks;
8. model boundary and fidelity;
9. alternative explanations;
10. rejection criteria.

### Confounding in accelerator studies

Changing PE count may also change:

- tile shape;
- compiler schedule;
- SRAM pressure;
- edge occupancy;
- assumed clock;
- required fanout or reduction;
- number of DMA descriptors.

If these effects change together, “more PEs caused the speedup” may be too strong. Use counterfactuals:

- fixed PE count with different aspect ratios;
- fixed tile schedule across arrays where legal;
- ideal bandwidth versus bounded bandwidth;
- conflicts disabled versus enabled;
- equal payload with different decoder assumptions;
- same hardware under multiple compiler mappings.

### Factorial reasoning

When two mechanisms may interact, evaluate combinations:

| Buffering | Bandwidth | Outcome purpose |
|---|---|---|
| single | low | baseline bottleneck |
| double | low | tests whether overlap helps when bandwidth remains scarce |
| single | high | isolates bandwidth effect |
| double | high | exposes interaction and upper regime |

The interaction term may matter more than either isolated change.

### Reproducibility

Preserve:

- exact source revision;
- configuration files;
- workload inputs or generators;
- build command and toolchain;
- run command;
- raw compact output;
- derivation script;
- interpretation and rejected claims.

An experiment report should make it possible to reproduce the number *and* understand why the number is not stronger evidence than it is.

---

## 2.10 Multi-objective decisions

Architectures are not ordered by one scalar metric. Alternatives may trade:

- throughput;
- median and tail latency;
- area;
- dynamic and leakage energy;
- SRAM and interconnect pressure;
- numerical quality;
- compiler complexity;
- runtime flexibility;
- verification burden;
- physical-design risk;
- product schedule.

### Constraints before objectives

First reject infeasible designs:

- output does not fit storage;
- required bandwidth exceeds a credible interface;
- numerical error violates quality requirements;
- queue or descriptor counts exceed capacity;
- clock or port assumptions are physically implausible.

Then compare feasible designs.

### Pareto dominance

Alternative `A` dominates `B` when `A` is no worse on every relevant objective and strictly better on at least one. Non-dominated options form the Pareto frontier.

A pre-spec CModel should preserve materially distinct options on that frontier. It should not delete a slower mode if that mode reduces storage, power, control, or verification cost in a useful regime.

### Energy accounting

Accelergy’s separation between action counts and action energy illustrates an important contract [WU19]:

\[
E = \sum_i N_i e_i,
\]

where `N_i` is an action count and `e_i` is an energy estimate for a component/technology context. Tusim may count MACs, reads, writes, and DMA bytes functionally, while the `e_i` values remain estimated or uncalibrated. The action ledger and physical energy model should not be conflated.

---

## 2.11 Worked Tusim claim audit

We now return to the opening result: `2619 cycles` under a mode named `CYCLE_ACCURATE`.

The complete reproducibility record is in [the Chapter 2 cycle-model audit](../../experiments/ch02-cycle-model-audit-2026-07-25.md).

### Source map and top-level execution sequence

Readers do not need prior Tusim API knowledge, but the worked case requires a compact map:

| Source | Role in this audit |
|---|---|
| `cycle_model.h` | mode enum, model state, helper contracts, and statistics structures |
| `cycle_model.c` | top-level tile accounting plus pipeline, bank, DRAM, and DMA helpers |
| `test_cycle_model.c` | 21 direct tests, including helper-level tests and three-mode checks |
| `Makefile` | establishes whether the source and tests participate in normal builds |
| `tu_config.json` / `tu_config.h` | expose a configuration string and a compile-time default, whose runtime reachability must be proved separately |

For one top-level tile call, the implemented control flow is approximately:

```text
create model
  → charge decode
  → issue one pipeline-helper entry
  → call aggregate bank-budget helpers for W, A, and O
  → add a K-based compute increment
  → mark the same entry complete
  → return aggregate cycles
```

The top-level path does not advance an entry through pipeline stages on successive cycles, sustain multiple in-flight tiles, or retry denied bank words until service completes. Names and comments describe intended concepts; this sequence describes the behavior exercised here.

> **Fidelity box — worked audit.** The case provides source-reconstructable cycle-accounting values and helper-level tests. It provides no GEMM functional oracle in this module, no integrated runtime timing path, no completed request schedule for denied bank words, no cycle-indexed pipeline trace, and no RTL/FPGA/silicon calibration.

| Evidence form | Mechanisms represented | Safe use | Missing before a stronger claim |
|---|---|---|---|
| Estimated formula | fill/compute/drain arithmetic | deterministic order-of-magnitude check under encoded geometry | memory interaction and validation |
| Source mode named `CYCLE_ACCURATE` | serial aggregate penalties plus separately tested helpers | reconstructing assumptions and detecting counter-contract defects | joint event schedule, retries, in-flight progression, integration, calibration |
| Future transaction/event model | explicit requests, resources, arbitration, retries, and overlap | causal contention and schedule analysis within its declared boundary | reference comparison and error criteria |
| RTL evidence | cycle-indexed state/interface behavior of a specified design | validation reference for the corresponding bounded contract | post-layout frequency, energy, and system context |

### 2.11.1 Provenance

At snapshot `e918c80`:

- `tu_cmodel/perf/cycle_model.c` defines modes named `FUNCTIONAL`, `ESTIMATED`, and `CYCLE_ACCURATE`; this book uses “detailed heuristic” as a conservative alias for the third;
- `tests/test_cycle_model.c` defines 21 tests;
- `config/tu_config.json` requests `"cycle_model": "cycle_accurate"`;
- `tu_cmodel/tu_config.h` defaults `TU_CYCLE_MODEL` to functional mode;
- `Makefile` does not include `perf/cycle_model.o` in `TU_OBJS`;
- `Makefile` does not define a target for `tests/test_cycle_model.c`;
- searches found no normal runtime caller that creates and executes this standalone model.

These facts establish five different states:

| Property | Finding |
|---|---|
| Source exists | yes |
| Compiles directly | yes |
| Dedicated tests pass when manually built | yes, 21/21 |
| Linked into the normal Tusim library | no |
| Reachable through shipped runtime configuration | not established; evidence indicates no |
| Calibrated against RTL/FPGA/silicon | no evidence found |

A JSON value is not proof of configuration reachability. A source file is not proof of integration.

### 2.11.2 Reproduced modes

The direct probe produced:

```text
constants: pe=16x16 depth=2 banks=32 bank_width=4 words_per_cycle=1 window=4 penalty=2
mode=functional returned_cycles=0 current_cycle=0
mode=estimated returned_cycles=128 current_cycle=128
mode=named-cycle-accurate returned_cycles=2619 current_cycle=2619 bank_reads=1024 bank_writes=256 shortfall_words=1277 conflicts=3 reported_util=40.000
```

The tile dimensions were `M=N=16`, `K=64`; the preserved probe uses addresses `W=0x100`, `A=0x200`, and `O=0x300`.

### 2.11.3 Estimated result

The estimated source path computes:

\[
T_{\text{est}} = dN + K + dM,
\]

where `d=2` is pipeline depth. Therefore:

\[
T_{\text{est}} = 2\cdot16 + 64 + 2\cdot16 = 128.
\]

This is a verified deterministic formula under the encoded assumptions. It is not measured hardware latency.

### 2.11.4 Detailed heuristic result

The detailed source path maps the supplied addresses through `address % 32`, causing the weight, activation, and output accesses in this probe to use bank 0. With four-byte bank width:

\[
W_{words} = \frac{16\cdot64\cdot2}{4}=512,
\]

\[
A_{words} = \frac{64\cdot16\cdot2}{4}=512,
\]

\[
O_{words} = \frac{16\cdot16\cdot4}{4}=256.
\]

Each aggregate access begins with one available word. Shortfalls are `511`, `511`, and `255`, totaling `1277`. The implementation charges a fixed penalty of two cycles per shortfall word:

\[
T_{bank}=2\cdot1277=2554.
\]

Adding one decode cycle and 64 compute cycles:

\[
T_{detail}=1+2554+64=2619.
\]

The returned value is therefore internally reconstructable. It is not a completed SRAM request schedule: the bank helper contract says the caller should stall and retry, whereas the top-level tile path charges the aggregate shortfall once and never retries denied words. The `2554` term is an encoded shortfall penalty, not a demonstrated transfer duration under the refill budget.

### 2.11.5 Why the label is too strong

The implementation comment calls this mode production-grade and cycle-accurate. The available evidence supports a narrower statement:

> The snapshot contains a standalone serial aggregate timing heuristic with separately testable pipeline, bank, DRAM, and arbitration helpers.

The evidence does not establish:

- normal runtime integration;
- every-cycle correspondence to a specified hardware design;
- calibrated bank, DRAM, or arbitration timing;
- correct cross-subsystem composition;
- cycle-by-cycle pipeline-stage progression or sustained multiple in-flight tiles through the top-level call;
- completion of denied bank requests through retry and refill;
- end-to-end DMA contention under state produced by normal DMA execution;
- RTL, FPGA, or silicon prediction error.

The source enum remains `CYCLE_ACCURATE`. The book calls the executed path a **standalone serial aggregate timing heuristic** or **source mode named `CYCLE_ACCURATE`**, not validated cycle-accurate evidence.

### 2.11.6 Failure modes exposed by reproduction

The run revealed several issues that passing tests did not reject.

#### Unbounded “utilization”

The statistics function divides total accesses by:

\[
\text{banks} \times \text{max accesses per cycle},
\]

but omits elapsed cycles. For `1280` accesses, `32` banks, and one access per cycle:

\[
1280/(32\cdot1)=40,
\]

printed as `4000%`. This is not time-average utilization.

#### Shortfall words labeled as cycles

The statistic named total stalls sums denied/shortfall words: `1277`. Execution multiplies them by a two-cycle penalty, adding `2554` cycles. The report labels `1277` as cycles. The event quantity and time quantity are conflated.

#### Uninitialized empty DRAM statistics

When there are no DRAM accesses, the getter does not assign output hit-rate or bandwidth variables. The report printed `40.0 GB/s` despite zero accesses and zero bytes. That value is undefined caller state, not performance evidence.

#### Conflict semantics

`conflict_count` increments for any nonzero access after available capacity falls below its maximum. This does not necessarily represent simultaneous requests contending for one bank.

#### Bank mapping semantics

The model selects a bank using a byte address modulo bank count, without first converting to a word index. For aligned accesses, this can collapse bank diversity.

#### Shortfall penalty without request completion

The bank helper returns denied words and instructs the caller to stall and retry. The top-level tile path instead converts the shortfall to a one-time penalty and does not retry. Its result cannot establish that all requested words were serviced under the modeled refill rule.

#### Pipeline helpers without top-level stage evolution

Pipeline entries do not advance through the declared stages during the top-level tile call. One entry is issued and then marked complete serially. Hazard tests exercise helper state directly and use fallback latency; they do not establish sustained overlapping tile progression.

#### Synthetic DMA arbitration state

The arbitration test manually assigns future-looking values to `dma_bus_cycles`. Normal DMA execution stores cumulative durations in those fields, while arbitration compares them to `current_cycle` as though they were completion timestamps. The helper assertion passes, but end-to-end contention semantics are not established.

These are model-contract failures: the code executes, but some reported observables and derived metrics do not mean what their labels imply.

### 2.11.7 Safe conclusion

A defensible conclusion is:

> At snapshot `e918c80`, Tusim contains a standalone serial aggregate timing heuristic with separately testable pipeline, bank, DRAM, and arbitration helpers. Its dedicated 21-test program passes when compiled manually. The cycle-accounting return values of modes named `FUNCTIONAL`, `ESTIMATED`, and `CYCLE_ACCURATE` are reproducible; `FUNCTIONAL` establishes only zero-cycle accounting in this module, not GEMM functional correctness. The `2619` result is an uncalibrated deterministic value dominated by a one-time shortfall penalty rather than a completed bank-service schedule. The module is not linked into the normal library or proven reachable through shipped runtime configuration, and it does not evolve a multi-entry pipeline in its top-level path. It must not be presented as integrated cycle-accurate hardware evidence.

This conclusion is useful. It preserves the prototype as a source of mechanisms and test cases while preventing an unjustified hardware claim.

---

## 2.12 Development implications

The audit suggests a staged improvement path rather than a demand for immediate maximal detail.

### Stage 1: integration truth

- Choose one authoritative configuration path.
- Add the module to the library only if an active architecture question requires it.
- Add a focused build target and aggregate test coverage.
- Prove that changing runtime configuration changes reachable behavior.
- Expose the model through a documented API or command path.

### Stage 2: counter contracts

For every counter, document:

- name and unit;
- increment event;
- scope and reset behavior;
- clock domain;
- whether it is an event, quantity, or duration;
- denominator for ratios;
- legal range;
- composition rules.

Separate shortfall words, conflict events, local blocked-request cycles, and global idle cycles.

### Stage 3: temporal semantics

- Define pipeline completion rather than using fallback constants for unfinished entries.
- Define bank ports, request timing, refill, arbitration, and retry behavior.
- Use word-address-aware banking.
- Initialize empty statistics deterministically.
- Define joint DMA/compute/SRAM overlap.
- Add invariants that reject percentages outside their defined range.

### Stage 4: validation

- Select a named RTL or trusted reference model.
- Align boundaries, clocks, commands, layouts, and datatypes.
- Compare traces for focused microbenchmarks.
- Expand to randomized sequences and workload suites.
- Report residuals and failure regimes.
- Reserve the term cycle-accurate for the validated boundary.

The correct stopping point depends on the decision. A pre-spec study may need only a verified analytical bound. Building a full event simulator before the architecture question requires it can add complexity without decision value.

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

---

## Summary

1. A model earns trust relative to a decision, not through detail alone.
2. The model contract defines boundary, semantics, state, transitions, observables, invariants, omissions, and decision scope.
3. Fidelity is multidimensional. Numerical, timing, contention, energy, system, and workload fidelity can differ.
4. Verification checks implementation of the contract; validation checks suitability for the question; calibration fits parameters to named evidence.
5. Simple bounds and conservation laws remain essential even when detailed models exist.
6. Deterministic output can still carry substantial parameter, workload, and model-form uncertainty.
7. Cycle values compose only when their boundaries, clocks, overlap, resource state, and attribution rules are compatible.
8. A sweep supports causality only when confounders and alternative explanations are controlled.
9. Architecture decisions are multi-objective and regime-specific.
10. Tusim’s standalone serial aggregate timing heuristic is reproducible but not integrated or calibrated; its fidelity enum must not be mistaken for an evidence label.

## Review questions

1. Why is “How detailed is the simulator?” the wrong first question?
2. Define a model contract for a single GEMM tile, including at least three omissions.
3. Give an example of a model with high numerical fidelity and low timing fidelity.
4. What additional evidence is needed to promote a cycle estimate to cycle-accurate evidence?
5. Why can a deterministic output still be uncertain?
6. Give one parameter uncertainty and one model-form uncertainty for an SRAM model.
7. Under what conditions may DMA and compute time be combined with `max()`?
8. Why can two counters measured in cycles still be incompatible?
9. What does a passing unit test establish, and what does it not establish?
10. Why is a JSON setting insufficient evidence that a feature is active?
11. Reconstruct the `128`-cycle estimated tile result.
12. Reconstruct the `2619`-cycle detailed prototype result.
13. Why is `4000%` a model-contract warning rather than evidence of extreme performance?
14. What distinction is lost when denied words are reported as stall cycles?
15. State the strongest safe conclusion supported by the standalone cycle-model audit.

## Design exercises

### Exercise 1 — Fidelity vector

Choose one Tusim subsystem and assess its numerical, ordering, traffic, timing, contention, energy, system, and workload fidelity. Do not reduce the assessment to one score.

### Exercise 2 — Counter dictionary

Design a counter dictionary for a banked SRAM. Include event definitions, units, scopes, reset rules, legal ranges, and formulas for derived utilization.

### Exercise 3 — Composition test

Given separate DMA, MMA, and elementwise cycle counters, write the conditions required before they may be combined. Construct one example where addition double-counts stalls and one where `max()` assumes impossible overlap.

### Exercise 4 — Validation plan

Design an RTL validation suite for the standalone timing prototype. Include microbenchmarks for pipeline hazards, bank mapping, row hits/misses, arbitration, overlap, and reset. Define error metrics and held-out tests.

### Exercise 5 — Robust decision

Compare two hypothetical array configurations under uncertain clock, DRAM efficiency, and compiler occupancy. Identify robust regions, crossover thresholds, and the evidence most valuable to collect next.

### Exercise 6 — Integration ledger

Audit a Tusim feature using separate columns for source existence, build membership, public API, configuration propagation, runtime reachability, focused tests, aggregate tests, and calibration. Explain why a single “implemented” column is insufficient.

---

## Primary references

- [WAT09] S. Williams, A. Waterman, and D. Patterson, “Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures,” 2009. DOI: https://doi.org/10.1145/1498765.1498785
- [SHA14] Y. S. Shao et al., “Aladdin: A Pre-RTL, Power-Performance Accelerator Simulator Enabling Large Design Space Exploration of Customized Architectures,” 2014. DOI: https://doi.org/10.1109/ISCA.2014.6853196
- [SAM18] A. Samajdar et al., “SCALE-Sim: Systolic CNN Accelerator Simulator,” arXiv:1811.02883v2
- [PAR19] A. Parashar et al., “Timeloop: A Systematic Approach to DNN Accelerator Evaluation,” 2019. DOI: https://doi.org/10.1109/ISPASS.2019.00042
- [KWO19] H. Kwon et al., “Understanding Reuse, Performance, and Hardware Cost of DNN Dataflow,” 2019. DOI: https://doi.org/10.1145/3352460.3358252
- [WU19] Y. N. Wu et al., “Accelergy: An Architecture-Level Energy Estimation Methodology for Accelerator Designs,” 2019. DOI: https://doi.org/10.1109/ICCAD45719.2019.8942149
- [GEN21] H. Genc et al., “Gemmini: Enabling Systematic Deep-Learning Architecture Evaluation via Full-Stack Integration,” 2021. DOI: https://doi.org/10.1109/DAC18074.2021.9586216
- [BAN02] R. Banakar et al., “Scratchpad Memory: A Design Alternative for Cache On-Chip Memory in Embedded Systems,” 2002. DOI: https://doi.org/10.1109/CODES.2002.1003604

Verified metadata and conservative claim scopes are maintained in [the foundation reference ledger](../../references/foundations.md).
