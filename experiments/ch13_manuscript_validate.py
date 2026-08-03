#!/usr/bin/env python3
"""Fail-closed structural, evidence, and repository-closure checks for Chapter 13."""
from __future__ import annotations

from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CHAPTER_REL = Path("manuscript/part-2-core/13-weight-streams-quantization-sparsity-compression.md")
CHAPTER = ROOT / CHAPTER_REL
RUN_REL = Path("experiments/runs/ch13-weight-streams/20260803-ch13-canonical-v8")
RUN = ROOT / RUN_REL
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
s = CHAPTER.read_text()

assert s.startswith("# Chapter 13 — Weight Streams: Quantization, Structured Sparsity, and Compression\n")
assert PIN in s
word_count = len(re.findall(r"\b[\w'’-]+\b", s))
assert 5000 <= word_count <= 7500, word_count
required_headings = [
    "## Learning objectives", "## Prerequisite graph",
    "## Opening architecture question: when does a smaller weight stream actually save time?",
    "### Source map", "## 13.1 The decision begins with four different contracts",
    "## 13.2 The three surfaces are adjacent, not one pipeline",
    "## 13.3 Quantization is a numeric conversion surface, not a compute engine",
    "## 13.4 Structured 2:4 sparsity is a byte format with a configurable decoder",
    "## 13.5 Compression codecs are exact byte formats with a decoder-throughput model",
    "## 13.6 Configuration has one ladder for the weight path, and it stops at the full config",
    "## 13.7 Which tests prove what, and which numbers are historical",
    "## 13.8 A workflow for choosing a weight representation",
    "## 13.9 Trade-offs across the family",
    "## 13.10 Fidelity box: what remains unknown", "## 13.11 Failure modes",
    "## 13.12 Summary", "## Review questions", "### Review-question answer key",
    "## Design exercises", "## Primary references",
]
for heading in required_headings:
    assert heading in s, heading
required_phrases = [
    "2.25× slower", "1.72× faster", "77,312 cycles", "19,971 cycles",
    "34,307 cycles", "not one integrated pipeline", "BLOCKED",
    "unsaturating INT32", "conversion-before-clamp", "undefined behavior",
    "dead configuration field", "sparsity_metadata_format",
    "tu_config_to_runtime()", "drops **every** compression and sparsity field",
    "no Makefile target", "not executed in the canonical run",
    "decoder_bound", "estimate classification, not a physical bottleneck proof",
    "payload-only measurements overstate compression speedups",
    "12,291", "7,811", "4,096", "3,712", "8,195", "4,099",
    "mask_popcount", "prune_with_masks_fp32", "0x5", "0x9",
    "32 × (2×2 + 1) = 160", "37.5%", "RLE", "14 bytes", "776 bytes",
    "110", "codec=2", "size=126", "magic 0x54555743",
    "dma=1", "default decode `128`", "total=128", "bound=1",
    "decode=8, total=8", "total=9", "14/14", "27/27", "24/24",
    "test-int-quant", "test-sparsity", "test-compress", "test_int8_sweep.c",
    "no `weight_compression` block", "JSON and YAML are not synchronized",
    "are calibrated", "12,291", "7,811", "4,096", "3,712", "8,195", "4,099",
    "65,536", "max(sparse_compute, decode)",
]
for phrase in required_phrases:
    assert phrase in s, phrase
for bad in [
    "The codecs form one integrated weight pipeline.",
    "The 2:4 format is an unconditional 2× speedup.",
    "Decoder-bound proves a physical bottleneck.",
    "`weight_compression` fields reach `tu_runtime_config_t`.",
    "`sparsity_metadata_format` is effective configuration.",
    "Tusim's weight path is calibrated against silicon.",
    "INT8 accumulation cannot overflow.",
    "The conversion is safe for any finite scale.",
    "`test_int8_sweep.c` is executable cmodel evidence.",
    "A smaller payload is automatically faster.",
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
    "archive-members.txt", "input-hashes.txt", "build.log", "test-int-quant.log",
    "test-sparsity.log", "test-compress.log", "test-sparsity-mutation.log",
    "weight-sweep.log", "sparsity-sweep.log", "ch13-probe.log", "transcript.log",
}
assert inner_members == expected_inner, sorted(inner_members ^ expected_inner)
outer_members = {line.split(None, 1)[1] for line in (RUN / "bundle-sha256.txt").read_text().splitlines()}
assert outer_members == {"sha256-retained.txt", "finalization.log", "predraft-validation.log"}

transcript = (RUN / "transcript.log").read_text()
for gate in [
    f"CH13_SOURCE_AUDIT PASS pin={PIN} hashes=25 predicates=138 checks=163",
    "=== Results: 14/14 tests passed ===" if "Results:" in transcript else "14/14 tests passed",
    "Tests: 27 run, 27 passed, 0 failed", "24/24 tests passed",
    "FOCUSED_TEST_MUTATION PASS rc=1 expected_failure=26/27",
    "CH13_PROBE SUMMARY failures=0", "TUSIM_POST PASS", "BOOK_POST PASS",
    "CH13_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
]:
    assert gate in transcript, gate
assert "CH13_PREDRAFT_VALIDATION PASS" in (RUN / "predraft-validation.log").read_text()
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
assert retained_pass.startswith("CH13_PREDRAFT_VALIDATION PASS")

ledger = (ROOT / "notes/chapter-13-source-and-claim-ledger.md").read_text()
dispositions = (ROOT / "notes/chapter-13-skeptical-review-dispositions.md").read_text()
gate = (ROOT / "notes/chapter-13-predraft-gate-closure.md").read_text()
framing = (ROOT / "notes/chapter-13-framing-and-evidence-plan.md").read_text()
report = (ROOT / "experiments/ch13-weight-streams-audit-2026-08-03.md").read_text()
assert "Draft gate:** pending" not in ledger
assert "C13.36" in ledger
assert "Current verdict:** **PASS" in dispositions
assert "**CLOSED**" in gate
assert "Drafting and closure are approved" in gate
assert "20260803-ch13-canonical-v8" in report
assert "13-weight-streams-quantization-sparsity-compression.md" in (ROOT / "README.md").read_text()

print(f"CH13_MANUSCRIPT_VALIDATION PASS words={word_count} links={len(links)} run={RUN_REL} input_commit={input_commit} head={head}")
