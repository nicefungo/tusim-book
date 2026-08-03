#!/usr/bin/env python3
"""Fail-closed structural, evidence, and repository-closure checks for Chapter 12."""
from __future__ import annotations

from pathlib import Path
import hashlib
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CHAPTER_REL = Path("manuscript/part-2-core/12-multi-core-clusters-and-interconnect-heuristics.md")
CHAPTER = ROOT / CHAPTER_REL
RUN_REL = Path("experiments/runs/ch12-multicore-interconnect/20260728-ch12-canonical-v5")
RUN = ROOT / RUN_REL
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
s = CHAPTER.read_text()

assert s.startswith("# Chapter 12 — Multi-Core Clusters and Interconnect Heuristic Estimates\n")
assert PIN in s
word_count = len(re.findall(r"\b[\w'’-]+\b", s))
assert 5000 <= word_count <= 7000, word_count
required_headings = [
    "## Learning objectives", "## Prerequisite graph",
    "## Opening architecture question: when does a topology estimate distinguish a design?",
    "### Source map", "## 12.1 The decision begins with four different contracts",
    "## 12.2 A cluster owns snapshots, not concurrent hardware instances",
    "## 12.3 Configuration has two ladders, not one",
    "## 12.4 Topology supplies geometry, not a router",
    "## 12.5 Three isolated transfer equations preserve three architecture alternatives",
    "## 12.6 Point-to-point send is immediate endpoint behavior",
    "## 12.7 Simultaneous traffic adds a route-load heuristic",
    "## 12.8 Route order couples placement to the bottleneck",
    "## 12.9 Ring versus mesh is a traffic-regime decision",
    "## 12.10 Collectives do not share one timing contract",
    "## 12.11 Counters must name their producer and interval",
    "## 12.12 What the test suite proves—and what it does not",
    "## 12.13 An architecture workflow for using the model safely",
    "## 12.14 Fidelity box: what remains unknown", "## 12.15 Closing checklist",
    "## Summary", "## Review questions", "### Review-question answer key",
    "## Design exercises", "## Primary references",
]
for heading in required_headings:
    assert heading in s, heading
required_phrases = [
    "adjacent APIs at different evidence rungs", "global-state-swapping facade",
    "exercised sequentially", "inter-core communication (ICC)",
    "single program, multiple data (SPMD)", "network-on-chip (NoC)",
    "neighbor sequence `i→(i+1) mod 16`",
    "`tu_cmodel/infra/config.{h,c}`", "`tu_cmodel/tu_config.h`",
    "`{1,2,3} × {4,8,12}`", "`{0,4,8} × {13,14,15}`",
    "90-degree counterclockwise rotation",
    "`h == 0` or `B == 0` returns zero", "unsupported mode returns `UINT64_MAX`",
    "`hop_latency <= UINT32_MAX / 2`", "wrap before widening",
    "`mesh_rows` so `num_cores + mesh_rows - 1 <= UINT32_MAX`",
    "`offset <= capacity - size`", "C_ell = sum over messages i using ell of ceil(B_i / W)",
    "max_ell(C_ell) + max_i(h_i L)",
    "one-field-at-a-time parse→convert→construct→effect A/B chain", "process status 134",
    "EQUATIONS legacy=15 cut=79 store=207",
    "SEND blocking=0 descriptor_latency=999 stats_messages=1 stats_bytes=16 stats_cycles=15 dst_delta=15",
    "TRAFFIC same=133 disjoint=69 ideal=69 bottleneck=128 link=0->1",
    "HEURISTIC_COUNTEREXAMPLE isolated=94 bottleneck=128 estimated=158 shared_pair_term=133 link=0->1",
    "not a proved service bound or makespan bound",
    "later addition of `bottleneck_link_cycles + max_route_cycles` is unchecked",
    "ROUTES patternA_XY=606 patternA_YX=222 patternB_XY=222 patternB_YX=606",
    "non-transactional", "broadcast_messages=3 broadcast_bytes=24 broadcast_cycles=23",
    "allreduce_message_delta=3 allreduce_byte_delta=36 allreduce_cycle_delta=0",
    "barrier_delta=10 barrier_state=0", "subsequent bulk `memcpy`",
    "implementation-only and serial",
    "28 exact source, configuration, generator, SRAM, test, and report hashes",
    "155 structural and reachability predicates, 183 checks including hashes",
    "CH12_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
    "snapshot conformance, not a green physical-correctness certificate",
    'CH12_RUN_ID="repro-$(date -u +%Y%m%dT%H%M%SZ)"', "no single integrated NoC model",
]
for phrase in required_phrases:
    assert phrase in s, phrase
for bad in [
    "The shared-link result is a makespan lower bound.", "The traffic estimator constructs a legal schedule.",
    "Core wrappers are thread-safe.", "SPMD launches all cores concurrently.",
    "The barrier implements rendezvous.", "All-reduce is a routed collective.",
    "Broadcast is failure-atomic.", "The config suite passes 20/20.",
    "A valid full configuration automatically creates a cluster.",
    "`total_icc_cycles` is elapsed cluster time.", "Mesh is universally better than ring.",
    "Tusim predicts physical NoC latency.", "The send helper checks 32-bit wraparound",
    "directed-link accumulator also performs unchecked",
    "an asymmetric mesh pattern and its transpose",
]:
    assert bad not in s, bad
assert "transpose" not in (ROOT / "experiments/ch12_multicore_interconnect_probe.c").read_text()


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
assert subprocess.run(["git", "remote"], cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout == b""
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
assert RUN.is_dir()
for manifest in ("sha256-retained.txt", "bundle-sha256.txt"):
    subprocess.run(["sha256sum", "-c", manifest], cwd=RUN, check=True, stdout=subprocess.DEVNULL)

inner_members = {line.split(None, 1)[1] for line in (RUN / "sha256-retained.txt").read_text().splitlines()}
bundled_inputs = {p.relative_to(RUN).as_posix() for p in (RUN / "inputs").rglob("*") if p.is_file()}
expected_inner = bundled_inputs | {
    "source-archive-sha256.txt", "source-audit.log", "source-audit-mutation.log",
    "archive-members.txt", "input-hashes.txt", "build.log", "test-multicore.log",
    "test-multicore-mutation.log", "test-config.log", "contention-sweep.log",
    "routing-sweep.log", "ch12-probe.log", "transcript.log",
}
assert inner_members == expected_inner, sorted(inner_members ^ expected_inner)
outer_members = {line.split(None, 1)[1] for line in (RUN / "bundle-sha256.txt").read_text().splitlines()}
assert outer_members == {"sha256-retained.txt", "finalization.log", "predraft-validation.log"}

transcript = (RUN / "transcript.log").read_text()
for gate in [
    f"CH12_SOURCE_AUDIT PASS pin={PIN} hashes=28 predicates=155 checks=183",
    "=== Results: 16/16 passed, 0 failed ===", "FOCUSED_TEST_MUTATION PASS rc=1 expected_failure=15/16",
    "CONFIG_SUITE_QUALIFIED nonzero_rc=134",
    "HEURISTIC_COUNTEREXAMPLE isolated=94 bottleneck=128 estimated=158 shared_pair_term=133 link=0->1",
    "CH12_PROBE SUMMARY failures=0", "TUSIM_POST PASS", "BOOK_POST PASS",
    "CH12_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
]:
    assert gate in transcript, gate
finalization = (RUN / "finalization.log").read_text()
m_final = re.search(r"FINALIZED_RUN PASS run_dir=(\S+) manifest=(\S+) transcript_sha256=([0-9a-f]{64})", finalization)
assert m_final
assert Path(m_final.group(1)).name == RUN.name
assert Path(m_final.group(2)).name == "sha256-retained.txt"
assert Path(m_final.group(2)).parent.name == RUN.name
transcript_digest = hashlib.sha256((RUN / "transcript.log").read_bytes()).hexdigest()
assert f"transcript_sha256={transcript_digest}" in finalization
assert "Config: interconnect switching parse + validation      PASS" in (RUN / "test-config.log").read_text()
assert "stack smashing detected" in (RUN / "test-config.log").read_text()

input_commit_match = re.search(r"^book_head=([0-9a-f]{40})$", transcript, re.M)
assert input_commit_match
input_commit = input_commit_match.group(1)
for bundled in (RUN / "inputs").rglob("*"):
    if bundled.is_file():
        rel = bundled.relative_to(RUN / "inputs")
        frozen = subprocess.run(["git", "show", f"{input_commit}:{rel.as_posix()}"], cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout
        assert bundled.read_bytes() == frozen, rel

retained_pass = (RUN / "predraft-validation.log").read_text().strip()
assert retained_pass == f"CH12_PREDRAFT_VALIDATION PASS files={len(bundled_inputs)} run={RUN_REL} input_commit={input_commit}"
env = dict(os.environ, CH12_RUN_ID=RUN.name)
rerun = subprocess.run(["python3", "experiments/ch12_predraft_validate.py"], cwd=ROOT, env=env, check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
assert rerun == retained_pass

for rel in [CHAPTER_REL, Path("experiments/ch12_manuscript_validate.py"), RUN_REL / "sha256-retained.txt", RUN_REL / "bundle-sha256.txt", RUN_REL / "finalization.log", RUN_REL / "predraft-validation.log"]:
    committed = subprocess.run(["git", "show", f"HEAD:{rel.as_posix()}"], cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout
    assert (ROOT / rel).read_bytes() == committed, rel

ledger = (ROOT / "notes/chapter-12-source-and-claim-ledger.md").read_text()
dispositions = (ROOT / "notes/chapter-12-skeptical-review-dispositions.md").read_text()
review_dispositions = (ROOT / "notes/chapter-12-independent-manuscript-review-dispositions.md").read_text()
framing = (ROOT / "notes/chapter-12-framing-and-evidence-plan.md").read_text()
report = (ROOT / "experiments/ch12-multicore-interconnect-audit-2026-07-28.md").read_text()
assert "Draft gate:** closed after canonical-v5" in ledger
assert "C12.47" in ledger and "| verified |" in ledger[ledger.index("C12.47"):ledger.index("C12.47") + 500]
assert "Current verdict:** **PASS after canonical-v5" in dispositions
assert "**PASS after canonical-v5 and clean re-review.**" in review_dispositions
assert "Drafting and closure are approved after canonical-v5" in framing
assert "Canonical-v5 completed with runner exit 0" in report
assert "transpose" not in report.lower()
assert "transpose" not in framing.lower()
assert "transpose" not in dispositions.lower()
assert "omitting queues, arbitration, or backpressure alone does not establish a bound" in (ROOT / "style-guide.md").read_text()
assert "12-multi-core-clusters-and-interconnect-heuristics.md" in (ROOT / "README.md").read_text()
assert "Chapter 24 will audit those specialized consumers" not in (ROOT / "manuscript/part-2-core/04-configuration-as-the-architecture-contract.md").read_text()
assert "Chapter 24: multicore and contexts" not in (ROOT / "manuscript/part-2-core/05-state-lifecycle-and-public-apis.md").read_text()
assert "proved traffic makespan bound" in (ROOT / "fidelity-matrix.md").read_text()
assert "Chapter 12 separates adjacent multicore surfaces" in (ROOT / "source-audit.md").read_text()

print(f"CH12_MANUSCRIPT_VALIDATION PASS words={word_count} links={len(links)} run={RUN_REL} input_commit={input_commit} head={head}")
