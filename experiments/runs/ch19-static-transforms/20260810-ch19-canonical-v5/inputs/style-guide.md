# Tusim Book Style and Evidence Guide

## Purpose

This manuscript is a technical/academic reference book, not an expanded README. Its job is to build a coherent knowledge system that connects computer-architecture fundamentals, accelerator design methods, executable Tusim mechanisms, verification, and design-space exploration.

## Expository order

Each topic follows this sequence:

1. the architectural problem;
2. the minimum theory and vocabulary needed to reason about it;
3. a hardware-neutral model;
4. Tusim's executable contract and implementation;
5. a worked, reproducible example;
6. alternatives and multi-objective trade-offs;
7. verification evidence;
8. fidelity limits and unsafe conclusions;
9. implications for future model or hardware development.

Do not introduce a Tusim structure before the reader knows why it exists.

## Source standard

Prefer primary sources: original papers, standards, official specifications, and executable repository evidence. Surveys and textbooks may supply context but should not be the sole support for a technical claim.

Bibliographic metadata must be verified against a DOI record, publisher page, arXiv record, or official project publication. Search results are discovery aids, not evidence.

Repository claims use this precedence:

1. behavior reproduced at the pinned commit;
2. focused tests;
3. public headers and live config/runtime paths;
4. current docs;
5. historical docs.

## Claim labels

- **Executable:** linked into the library and exercised by a runnable test.
- **Integrated:** reachable through the public/config/runtime path.
- **Functional model:** semantics are modeled; timing equivalence is not claimed.
- **Analytical model:** equations estimate behavior without executing the modeled microarchitecture.
- **Deterministic lower bound:** an optimistic minimum proved against an explicitly defined execution model and assumptions; omitting queues, arbitration, or backpressure alone does not establish a bound.
- **Estimated:** not calibrated against RTL or silicon.
- **Calibrated:** compared against a named reference with method and error reported.
- **Historical:** rationale that may not match the pinned code.
- **Future work:** absent from the pinned edition.

## Quantitative writing rules

Every numerical result states:

- source revision and configuration;
- workload and tensor shapes;
- units and clock assumption;
- formula or counter origin;
- whether the value is measured, simulated, or analytically estimated;
- modeled and omitted costs;
- calibration status;
- uncertainty or safe interpretation.

Never add counters from incompatible cycle domains. Never convert payload reduction directly into latency or energy improvement without a model for decoding, storage, and data movement.

## Trade-off rules

A recommendation must state its regime and evaluate, where relevant:

- throughput and latency;
- utilization and traffic;
- area and power/energy implications;
- numerical accuracy;
- control complexity;
- compiler/runtime effects;
- verification cost;
- model fidelity.

“Faster,” “better,” and “optimal” are incomplete without conditions and costs.

## Notation

- Define matrix orientation before using `M`, `N`, and `K`.
- Distinguish mathematical matrices from Tusim's W/A/O SRAM regions.
- Distinguish operations, MACs, and FLOPs.
- Distinguish peak throughput, achieved throughput, active utilization, and MAC efficiency.
- Distinguish capacity, bandwidth, latency, traffic, and operational intensity.
- Use binary units for byte capacities when the code uses powers of two; state the convention.

## Chapter contract

Each technical chapter includes:

- learning objectives;
- prerequisite graph;
- opening architecture question;
- theory and terminology;
- source map;
- implementation walk-through;
- runnable example or reproducible derivation;
- trade-off table;
- verification section;
- fidelity box;
- failure modes;
- summary;
- review questions and design exercises;
- primary references.

## Code and diagrams

Code excerpts should be short and annotated, with exact source paths and edition commit. Long interfaces belong in appendices. Diagrams must preserve the implementation's data orientation and explicitly distinguish logical flow from physical timing.

## Development feedback

When literature or textbook reasoning exposes a model blind spot, record it as an evidence-backed research question rather than silently changing the book's claims. A code change should follow only after the architecture question, expected fidelity, alternatives, and verification strategy are clear.

## Cross-session writing protocol

The general, transferable session-boundary procedure is defined in [`/home/zxy/Workplace/agent-principles/session-boundary-and-handoff.md`](/home/zxy/Workplace/agent-principles/session-boundary-and-handoff.md). This section is the Tusim-book overlay: it adds chapter boundaries, academic evidence requirements, and editorial checks without weakening the general handoff principle.

Chat history is supporting context, not the source of truth. At the start of a new session, read the general principle, this guide, `edition.yaml`, `README.md`, the preceding chapter’s handoff, the current chapter file, its source ledger, and its experiment record before drafting.

### Default session granularity

Use **up to two tightly related chapters per session when context allows**. Use only one when a chapter is research-heavy, requires substantial source auditing or experiments, or would leave insufficient room for independent verification and handoff.

Two chapters may share a session only when all of the following hold:

1. they share the same conceptual, literature, and implementation context;
2. the second chapter depends directly on the first or forms a natural pedagogical pair;
3. each still receives independent executable verification and skeptical review;
4. the context budget leaves room for revision and a durable handoff rather than merely first-draft generation;
5. the agent can finish at a clean chapter boundary.

Do not draft three substantive chapters in one session. If context pressure rises, finish and validate the current chapter, write its handoff record, and recommend `/new` instead of reducing evidence quality.

### Chapter lifecycle

Each chapter proceeds through explicit stages:

1. **Orient:** read the book contract, edition manifest, neighboring chapter summaries, and current status.
2. **Frame:** state the reader decision, prerequisites, opening question, chapter boundary, and claims the chapter must not make.
3. **Audit:** inspect live Tusim source, build linkage, configuration reachability, tests, and historical documentation.
4. **Research:** construct a primary-source map with verified metadata and conservative claim scopes.
5. **Draft:** follow the expository order defined above; keep evidence labels visible.
6. **Execute:** run every cited example or derivation that can be executed; preserve exact commands and observed output in `experiments/`.
7. **Challenge:** search for alternative explanations, incompatible cycle domains, no-op configuration, counter-definition defects, hidden physical assumptions, and overgeneralization.
8. **Revise:** resolve the challenge findings in prose, fidelity boxes, experiment notes, and development questions.
9. **Validate:** check citations, links, notation, units, local consistency, prerequisite coverage, and repository cleanliness.
10. **Handoff:** update status and write enough durable context for another session to continue without reconstructing the work from chat.

A chapter is not “complete” merely because prose exists. Completion requires passed validation or an explicit list of unresolved blockers.

### Durable continuity artifacts

The standalone book directory maintains:

- `README.md`: chapter status and navigation;
- `edition.yaml`: pinned source snapshot and reproducibility environment;
- `style-guide.md`: this permanent editorial contract;
- `references/`: verified bibliographic metadata and safe claim scopes;
- `experiments/`: exact commands, observed output, assumptions, and interpretations;
- `notes/`: chapter research ledgers, source maps, open questions, and handoff records;
- `figures/`: source diagrams and generation notes;
- `manuscript/`: chapter prose only.

Temporary reasoning, copied search results, and unverified bibliographic guesses do not belong in the manuscript. A future session should be able to determine what is known, reproduced, uncertain, and pending by reading these artifacts alone.

### Required chapter handoff

At the end of each chapter session, record:

- chapter status and word count;
- edition commit used;
- source files and tests inspected;
- commands actually run and their outcomes;
- references added or rejected;
- central claims and fidelity labels;
- unresolved technical or pedagogical questions;
- development implications discovered;
- exact recommended starting point for the next session.

Do not use the handoff as a diary. Preserve decisions, evidence, and unresolved risks—not transient task narration.

### Context-budget discipline

Reserve context for synthesis and correction. Prefer targeted source reads, filtered searches, compact experiment logs, and durable ledgers over repeatedly loading whole files. Research subagents may collect literature or challenge logic, but their reports are inputs: bibliographic facts and technical claims must be checked before entering the manuscript.

When approximately one quarter of the usable session remains, stop opening new chapter-scale work. Spend the remainder validating, revising, and writing the handoff. This protects later sections from the common failure mode in which early material is researched carefully and late material is rushed.

### Professional consistency checks

Before closing a chapter session, confirm that:

- terms agree with earlier chapters and the terminology ledger;
- symbols and tensor orientation have not drifted;
- source names do not substitute for evidence labels;
- enum names such as `CYCLE_ACCURATE` are not repeated as validated fidelity claims;
- reported percentages have defined denominators and intervals;
- causal language is supported by controlled comparisons;
- recommendations name regimes, costs, and rejected alternatives;
- future-work proposals are clearly separated from stable-snapshot behavior;
- prose remains readable as a textbook even when repository details are removed.
