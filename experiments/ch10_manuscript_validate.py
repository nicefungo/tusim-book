#!/usr/bin/env python3
"""Fail-closed structural and evidence checks for the Chapter 10 manuscript."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "manuscript/part-2-core/10-dma-descriptor-contracts-and-tick-driven-execution.md"
RUN = ROOT / "experiments/runs/ch10-dma-contracts/20260727T223000Z-hashguard"
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
s = CHAPTER.read_text()

assert s.startswith("# Chapter 10 — DMA Descriptor Contracts and Tick-Driven Execution\n")
assert PIN in s
assert "AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS" in s
assert "snapshot conformance" in s.lower()
word_count = len(re.findall(r"\b[\w'’-]+\b", s))
assert 4500 <= word_count <= 6500

required_headings = [
    "## Learning objectives", "## Prerequisite graph",
    "## Opening architecture question: submitted is not delivered",
    "## 10.2 Choosing a descriptor geometry", "## 10.4 Ownership and borrowed state",
    "## 10.5 Synchronous and tick-driven lifecycle",
    "## 10.6 Queue heads and descriptor chains do not compose",
    "## 10.7 Service estimates are not elapsed transfer time",
    "## 10.9 Channel and configuration boundaries",
    "## 10.10 Ordinary-operation reachability and split state",
    "## 10.11 Reproduce and interpret the evidence", "## 10.12 Safety boundaries",
    "## 10.13 Multi-objective descriptor choices", "## 10.14 Fidelity box",
    "## Summary", "## Review questions", "### Review-question answer key",
    "## Design exercises", "## Primary references",
]
for heading in required_headings:
    assert heading in s, heading

required_phrases = [
    "linear copied/accounted bytes = n e",
    "(r - 1)s_r + c e",
    "(d - 1)s_d + (r - 1)s_r + c e",
    "multicast requested fanout bytes = m n e",
    "4,294,967,294",
    "C_service = TU_LATENCY_DRAM_READ",
    "C_service,bw = 50 + ceil(1024/32) + 224 × 2",
    "engine cycle 1: selected; bytes copied",
    "engine cycle 53: channel retires descriptor",
    "requests above 8 -> clamp to 8 -> likewise unsafe",
    "process-global singleton `g_tu_dma`",
    "returns `0x10c` where the expected address is `0x110`",
    "swap then exposed stale data as active",
    "33 exact source hashes plus 32 structural predicates",
    "pipeline | not executed",
    "Thus channel `total_completed` is an outcome-blind",
    "Reinitialization is not cleanup",
    "General descriptors, address-generator routing, descriptor-to-DRAM timing",
]
for phrase in required_phrases:
    assert phrase in s, phrase

for evidence_row in [
    "| descriptor DMA | 10/10 reported cases |",
    "| scatter/gather | 15/15 |",
    "| multicast | 10/10 |",
    "| address generator | 12/13 |",
    "| double buffer | 10/10 |",
    "| command queue | 9/9 |",
    "| CModel | 19/19 |",
    "| configuration | 20/20 observed |",
]:
    assert evidence_row in s, evidence_row
assert "on rejection, submission has already destroyed the chain" in s
assert "cleanup only after rejection" not in s

for bad in [
    "Submission transfers ownership to the engine.",
    "`completed` means the transfer succeeded.",
    "Channel `total_completed` proves data delivery.",
    "`estimated_cycles` is elapsed execution time.",
    "The pipeline suite passed",
    "DMA-to-shadow overlap is correct",
    "Descriptor DMA uses the standalone DRAM timing model.",
]:
    assert bad not in s, bad

links = re.findall(r"\[[^]]+\]\(([^)]+)\)", s)
for link in links:
    if link.startswith(("http://", "https://", "#", "/")):
        continue
    target = link.split("#", 1)[0]
    assert (CHAPTER.parent / target).resolve().exists(), link

assert len(re.findall(r"^\d+\. ", s[s.index("## Review questions"):s.index("### Review-question answer key")], re.M)) == 10
assert len(re.findall(r"^\d+\. ", s[s.index("### Review-question answer key"):s.index("## Design exercises")], re.M)) == 10
assert len(re.findall(r"^\d+\. \*\*", s[s.index("## Design exercises"):s.index("## Primary references")], re.M)) == 10

subprocess.run(["python3", str(ROOT / "experiments/ch10_predraft_validate.py")],
               cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
assert (ROOT / "notes/chapter-10-predraft-gate-closure.md").exists()
print(f"CH10_MANUSCRIPT_VALIDATION PASS words={word_count} links={len(links)}")
