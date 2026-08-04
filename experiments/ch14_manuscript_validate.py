#!/usr/bin/env python3
"""Fail-closed structural, evidence, and repository-closure checks for Chapter 14."""
from __future__ import annotations

from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CHAPTER_REL = Path("manuscript/part-2-core/14-operator-compute-engines-functional-semantics-and-engine-metrics.md")
CHAPTER = ROOT / CHAPTER_REL
RUN_REL = Path("experiments/runs/ch14-compute-engines/20260804-ch14-canonical-v3")
RUN = ROOT / RUN_REL
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
s = CHAPTER.read_text()

assert s.startswith("# Chapter 14 — Operator Compute Engines: Functional Semantics and Engine Metrics\n")
assert PIN in s
word_count = len(re.findall(r"\b[\w'’-]+\b", s))
assert 5000 <= word_count <= 7500, word_count
required_headings = [
    "## Learning objectives", "## Prerequisite graph",
    "## Opening architecture question: when can you trust an operator engine's return value?",
    "### Source map", "## 14.1 Seven engines, four return-value dialects",
    "## 14.2 The metric census: three returns under one workload label",
    "## 14.3 Softmax: two-pass semantics and read+write stall accounting",
    "## 14.4 Normalization: LayerNorm/RMSNorm and the discarded read return",
    "## 14.5 Elementwise: fused chains and post-hoc accounting",
    "## 14.6 Pooling: an analytical cycle count with a different meaning",
    "## 14.7 Convolution: functional references, im2col+GEMM, and a separate estimate API",
    "## 14.8 Attention: the composition point, its stats struct, and the FP16 SRAM staging defect",
    "## 14.9 The pipeline controller: byte-proportional overlap, not flag-commanded",
    "## 14.10 Integration map and test provenance",
    "## 14.11 Trade-offs across the engine family",
    "## 14.12 Fidelity box: what remains unknown", "## 14.13 Failure modes",
    "## 14.14 Summary", "## Review questions", "### Review-question answer key",
    "## Design exercises", "## Primary references",
]
for heading in required_headings:
    assert heading in s, heading
required_phrases = [
    "96", "80", "40", "never sum", "stall cycles", "UINT64_MAX",
    "0.25, 0.25, 0.25, 0.25", "0.999995", "0.5x·(1 + tanh(0.7978845608·(x + 0.044715x³)))",
    "3.5, 5.5; 11.5, 13.5", "returned cycles **18**", "returned cycles **34**", "estimate_cycles",
    "69", "im2col_rows=3, im2col_cols=9", "6.000000",
    "dma=16 B, tiles=2, flops=8, compute=145, dma=2, total=147, util=0.9864",
    "utilization = 145/147 = 0.9864", "0.53–0.68",
    "SRAM access-width defect", "4-byte copies on 2-byte elements", "garbage",
    "undefined-behavior-dependent", "never passes 9/9", "6–8/9",
    "ATTENTIONSUITEQUALIFIED", "include-only",
    "standalone", "byte-proportional", "configured-but-ineffective",
    "sequential_total = 204", "sequential_total = 402", "saved = 200",
    "cap-then-align", "TU_CMD_ELEMENTWISE", "tu_conv2d_direct_nchw_fp32",
    "tu_attention_stats_t", "words_available", "i/2", "write-labeled",
    "none is calibrated", "no-sum rule", "rejected claim",
]
for phrase in required_phrases:
    assert phrase in s, phrase
for bad in [
    "Attention outputs are correct for arbitrary FP16 inputs.",
    "The engines form one integrated operator dispatch path.",
    "Softmax is cheaper than normalization at this workload.",
    "Summing the engine returns gives the pipeline latency.",
    "`enable_load_overlap` alone creates overlap.",
    "The attention suite passed 9/9.",
    "Engine metrics are calibrated against silicon.",
    "Normalization counts read stalls.",
]:
    assert bad not in s, bad


def slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return re.sub(r"[ -]+", "-", text).strip("-")


links = re.findall(r"\[[^]]+\]\(([^)]+)\)", s)
for link in links:
    if link.startswith(("http://", "https://", "/")):
        continue
    target_text, _, fragment = link.partition("#")
    target = CHAPTER if not target_text else (CHAPTER.parent / target_text).resolve()
    assert target.exists(), link
    if fragment:
        headings = re.findall(r"^#{1,6}\s+(.+?)\s*$", target.read_text(), re.M)
        assert fragment in {slug(h) for h in headings}, f"broken anchor {link}"

questions = s[s.index("## Review questions"):s.index("### Review-question answer key")]
answers = s[s.index("### Review-question answer key"):s.index("## Design exercises")]
exercises = s[s.index("## Design exercises"):s.index("## Primary references")]
assert len(re.findall(r"^\d+\. ", questions, re.M)) == 10
assert len(re.findall(r"^\d+\. ", answers, re.M)) == 10
assert len(re.findall(r"^\d+\. \*\*", exercises, re.M)) == 8

assert subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout == b""
assert subprocess.run(["git", "remote"], cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout != b""
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
assert RUN.is_dir()
for manifest in ("sha256-retained.txt", "bundle-sha256.txt"):
    subprocess.run(["sha256sum", "-c", manifest], cwd=RUN, check=True, stdout=subprocess.DEVNULL)

inner_members = {line.split(None, 1)[1] for line in (RUN / "sha256-retained.txt").read_text().splitlines()}
bundled_inputs = {p.relative_to(RUN).as_posix() for p in (RUN / "inputs").rglob("*") if p.is_file()}
expected_inner = bundled_inputs | {
    "source-archive-sha256.txt", "source-audit.log", "source-audit-mutation.log",
    "archive-members.txt", "input-hashes.txt", "build.log", "test-elementwise.log",
    "test-normalization.log", "test-convolution.log", "test-attention.log",
    "test-pooling.log", "test-pipeline.log", "test-softmax.log",
    "test-softmax-mutation.log", "ch14-probe.log", "transcript.log",
}
assert inner_members == expected_inner, sorted(inner_members ^ expected_inner)
outer_members = {line.split(None, 1)[1] for line in (RUN / "bundle-sha256.txt").read_text().splitlines()}
assert outer_members == {"sha256-retained.txt", "finalization.log", "predraft-validation.log"}

transcript = (RUN / "transcript.log").read_text()
for gate in [
    f"CH14_SOURCE_AUDIT PASS pin={PIN} hashes=28 predicates=46 checks=74",
    "ATTENTIONSUITEQUALIFIED PASS rc=1",
    "=== Results: 15/15 passed, 0 failed ===",
    "FOCUSED_TEST_MUTATION PASS",
    "16/16 tests passed", "11/11 tests passed", "12/12 tests passed",
    "14/14 tests passed", "Results: 11/11 passed",
    "CH14_PROBE SUMMARY failures=0", "TUSIM_POST PASS", "BOOK_POST PASS",
    "CH14_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
]:
    assert gate in transcript, gate
assert "CH14_PREDRAFT_VALIDATION PASS" in (RUN / "predraft-validation.log").read_text()
assert "=== Results: 14/15 passed, 1 failed ===" in (RUN / "test-softmax-mutation.log").read_text()
assert "FINALIZED_RUN PASS" in (RUN / "finalization.log").read_text()
finalization = (RUN / "finalization.log").read_text()
m_final = re.search(r"FINALIZED_RUN PASS run_dir=(\S+) manifest=(\S+) transcript_sha256=([0-9a-f]{64})", finalization)
assert m_final
assert Path(m_final.group(1)).name == RUN.name
assert Path(m_final.group(2)).name == "sha256-retained.txt"
assert Path(m_final.group(2)).parent.name == RUN.name
input_commit_match = re.search(r"^book_head=([0-9a-f]{40})$", transcript, re.M)
assert input_commit_match
input_commit = input_commit_match.group(1)
for bundled in (RUN / "inputs").rglob("*"):
    if bundled.is_file():
        rel = bundled.relative_to(RUN / "inputs")
        frozen = subprocess.run(["git", "show", f"{input_commit}:{rel.as_posix()}"], cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout
        assert bundled.read_bytes() == frozen, rel

retained_pass = (RUN / "predraft-validation.log").read_text().strip()
assert retained_pass.startswith("CH14_PREDRAFT_VALIDATION PASS")

ledger = (ROOT / "notes/chapter-14-source-and-claim-ledger.md").read_text()
dispositions = (ROOT / "notes/chapter-14-skeptical-review-dispositions.md").read_text()
gate = (ROOT / "notes/chapter-14-predraft-gate-closure.md").read_text()
framing = (ROOT / "notes/chapter-14-framing-and-evidence-plan.md").read_text()
report = (ROOT / "experiments/ch14-compute-engines-audit-2026-08-04.md").read_text()
assert "Draft gate:** pending" not in ledger
assert "C14.30" in ledger
assert "Current verdict:** **PASS" in dispositions
assert "**CLOSED**" in gate
assert "Drafting and closure are approved" in gate
assert "20260804-ch14-canonical-v3" in report
assert "14-operator-compute-engines-functional-semantics-and-engine-metrics.md" in (ROOT / "README.md").read_text()

print(f"CH14_MANUSCRIPT_VALIDATION PASS words={word_count} links={len(links)} run={RUN_REL} input_commit={input_commit} head={head}")
