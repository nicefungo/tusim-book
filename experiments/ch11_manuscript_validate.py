#!/usr/bin/env python3
"""Fail-closed structural and evidence checks for the Chapter 11 manuscript."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "manuscript/part-2-core/11-instruction-surfaces-and-command-queue-ordering.md"
RUN = ROOT / "experiments/runs/ch11-instruction-contracts/20260728-ch11-canonical"
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
s = CHAPTER.read_text()

assert s.startswith("# Chapter 11 — Instruction Surfaces and Command-Queue Ordering\n")
assert PIN in s
word_count = len(re.findall(r"\b[\w'’-]+\b", s))
assert 4500 <= word_count <= 6500, word_count

required_headings = [
    "## Learning objectives",
    "## Prerequisite graph",
    "## Opening architecture question: when is an instruction an instruction?",
    "## 11.1 A lifecycle vocabulary that prevents false integration",
    "## 11.2 Source map: adjacent surfaces, not one stack",
    "## 11.3 The expanded ISA defines packed representation and metadata, not a runtime binary",
    "## 11.4 Legacy text ASM is a separate direct interpreter",
    "## 11.5 The command queue is an opcode-alias transport with a small dispatcher",
    "## 11.6 Dependency IDs: absent, faulted, and reset are different cases",
    "## 11.7 Completion, signaling, and reclamation are independent contracts",
    "## 11.8 A barrier name does not create fence semantics",
    "## 11.9 Reset creates a new state but not a complete ID epoch",
    "## 11.10 The compiler scheduler is a separate analytical surface",
    "## 11.11 Configuration names do not prove active control",
    "## 11.12 Worked lifecycle trace and reproducible evidence",
    "## 11.13 Multi-objective instruction-transport choices",
    "## 11.14 Failure modes and safety boundaries",
    "## 11.15 Fidelity box",
    "## Development questions",
    "## Summary",
    "## Review questions",
    "### Review-question answer key",
    "## Design exercises",
    "## Primary references",
]
for heading in required_headings:
    assert heading in s, heading

required_phrases = [
    "declared opcode\n    != portable binary encoding",
    "59 explicit operation enumerators",
    "68 non-`UNKNOWN` slots",
    "ISA native_bytes=10 a5 22 11 44 33 66 55 aa 99 88 77",
    "ASM expanded_mnemonic_rc=-1",
    "CONV2D` value reaches the default branch and becomes `FAULTED`",
    "synchronous mode**, submission executes immediately",
    "Missing ID:** lookup treats it as already completed",
    "Known faulted ID:** the record is found but is not equal to `COMPLETED`",
    "ELEMENTWISE_BOUNDARY count=9 status=2 completed=1 faulted=0",
    "signal_count=0",
    "Completion does not reclaim capacity",
    "ASYNC_BARRIER fault=3 pre=0 barrier=2 post=2 count=4 cycle=6",
    "RESET_IDS old_cmd=1 new_cmd=1 old_signal=1 new_signal=5",
    "SCHED_POSITIVE_INSERT direct=1 run=0 input_nodes=2 output_nodes=2",
    "SCHED_POSITIVE_HOIST direct=1 run=0 input_nodes=3 output_nodes=3",
    "SCHED_DENSE_BARRIER prior=17 retained_preds=16 max_deps=16",
    "declared != defaulted != parsed != converted != consumed != effective",
    "hashes=26 predicates=96 checks=122",
    "CH11_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
    "snapshot conformance, not a green correctness certificate",
    "queue-epoch-local numbers",
    "liveness allocator (qualified adjacent surface)",
    "`PENDING`, `ISSUED`, `COMPLETED`, and `FAULTED`",
    "The queue increments `current_cycle` once per tick",
    "gives the barrier no implicit dependencies on prior commands",
    "fixed per-class node costs: one for DMA and four for every other emitted node",
    "waiting on an unknown ID reports success",
    'CH11_RUN_ID="repro-$(date -u +%Y%m%dT%H%M%SZ)"',
    "no retirement, no reclamation, and no handle invalidation",
]
for phrase in required_phrases:
    assert phrase in s, phrase

for bad in [
    "The expanded ISA is a portable binary encoding.",
    "Legacy ASM decodes `tu_instruction_t`.",
    "All declared opcodes execute through the command queue.",
    "Synchronous submission honors dependencies.",
    "A missing command ID proves that command retired.",
    "`COMPLETED` proves successful effects.",
    "The queue barrier is a full fence.",
    "Signal allocation proves signal delivery.",
    "The scheduler is the command queue issue engine.",
    "DMA hoisting moves graph nodes.",
    "The scheduler cycle count is calibrated hardware time.",
    "The nine-operation elementwise path overreads the operation array.",
    "`PENDING`, `RUNNING`, `COMPLETED`, and `FAULTED`",
    "Fixed cycle costs are accumulated in the queue model.",
    "Tusim's queue barrier depends on the queue's `last_barrier_id`",
    "fixed per-opcode costs",
    "simple capacity reclamation and stale-handle policy",
]:
    assert bad not in s, bad

links = re.findall(r"\[[^]]+\]\(([^)]+)\)", s)
for link in links:
    if link.startswith(("http://", "https://", "#", "/")):
        continue
    target = link.split("#", 1)[0]
    assert (CHAPTER.parent / target).resolve().exists(), link

questions = s[s.index("## Review questions"):s.index("### Review-question answer key")]
answers = s[s.index("### Review-question answer key"):s.index("## Design exercises")]
exercises = s[s.index("## Design exercises"):s.index("## Primary references")]
assert len(re.findall(r"^\d+\. ", questions, re.M)) == 10
assert len(re.findall(r"^\d+\. ", answers, re.M)) == 10
assert len(re.findall(r"^\d+\. \*\*", exercises, re.M)) == 10

subprocess.run(
    ["sha256sum", "-c", "sha256-retained.txt"],
    cwd=RUN,
    check=True,
    stdout=subprocess.DEVNULL,
)
closure = (ROOT / "notes/chapter-11-predraft-gate-closure.md").read_text()
assert "Final verdict: Drafting approved" in closure
assert "architecture/methodology: **PASS**" in closure
assert "repository/reproducibility: **PASS**" in closure

print(f"CH11_MANUSCRIPT_VALIDATION PASS words={word_count} links={len(links)}")
