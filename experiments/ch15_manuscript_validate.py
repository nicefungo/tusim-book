#!/usr/bin/env python3
"""Fail-closed manuscript, evidence, link, and repository checks for Chapter 15."""
from __future__ import annotations

from pathlib import Path
import hashlib
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CHAPTER_REL = Path("manuscript/part-2-core/15-dram-service-models-and-bandwidth-claims.md")
CHAPTER = ROOT / CHAPTER_REL
VALIDATOR_REL = Path("experiments/ch15_manuscript_validate.py")
RUN_REL = Path("experiments/runs/ch15-dram/20260804-ch15-canonical-v3")
RUN = ROOT / RUN_REL
TUSIM = Path("/home/zxy/Workplace/projects/tusim")
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
INPUT_COMMIT = "242807fe781be29bf39be76cfa4c2b15ca4876e5"
DRAFT_BASE = "4791eb2f18b91fbc7eadec56144bcf0a9c16c46b"
SNAPSHOT_FILE = ROOT / "notes/chapter-15-review-snapshot.txt"

REQUIRED_HEADINGS = [
    "## Learning objectives", "## Prerequisite graph",
    "## Opening architecture question: what does a number labeled “DRAM cycles” actually mean?",
    "### Source map", "## 15.1 Begin with the producer, not the DRAM label",
    "## 15.2 The stateless estimator answers one narrow question",
    "## 15.3 The stateful access contract separates service fields from time",
    "## 15.4 Two state defects bound every bandwidth claim",
    "## 15.5 Row mode, statistics, and clock controls are narrower than their names",
    "## 15.6 Presets are implemented declarations, not device validation",
    "## 15.7 Configuration is six paths, not one pipeline",
    "## 15.8 Integration stops before ordinary data movement",
    "## 15.9 Historical sweeps are hypotheses until their arithmetic survives",
    "## 15.10 A decision workflow for safe bandwidth claims",
    "## 15.11 Trade-offs among model alternatives",
    "## 15.12 Verification evidence and test provenance",
    "## 15.13 Fidelity box: what remains unknown", "## 15.14 Failure modes",
    "## 15.15 Summary", "## Review questions", "### Review-question answer key",
    "## Design exercises", "## Primary references",
]
REQUIRED_PHRASES = [
    "canonical v3", "sole predraft evidence authority", "23 source/config/test/document hashes",
    "62 structural/reachability predicates (85 checks total)", "12/12", "10/10", "21/21", "20/20",
    "hbm2_read64=51", "hbm3_read819=41", "1,000-cycle", "255,936", "2,001",
    "128,000 prior bytes", "pending=128064", "budget=127936", "history-dependent",
    "1000,1050,1050", "overwritten, not queued", "flat read-only +10 penalty",
    "1,024 GB/s", "utilization `1024/256 = 4.0`", "no-op", "819 GB/s",
    "Runtime conversion drops all DRAM fields", "no non-test caller", "does not call `tu_dram_*`",
    "leaves **every byte unchanged**", "source-present but absent from `TU_OBJS`",
    "2.975", "1.424", "0.862", "approximately 6.4% below ideal",
    "Historical", "rejected as decision evidence", "not live-model evidence",
    "not a faithful token bucket", "No Chapter 15 quantity is calibrated",
    "No such chain exists", "must not be silently promoted", "Analytical model / Estimated",
    "Configuration and caller/runtime obligation", "implementation-dependent portability hazard",
]
CONTEXTUAL_SNIPPETS = [
    "ceil(64/256) + 50 = 1 + 50 = 51 cycles.",
    "ceil(819/819) + 40 = 41 cycles.",
    "cycles_out = 50\nstall_out = 1000\ncurrent_cycle = 0",
    "256 bytes/cycle × 1,000 cycles = 256,000 bytes.",
    "128n <= 256064.",
    "request **2,001** first receives the **bandwidth-window stall**",
    "TOPS = 8,388,608 operations × clock_GHz / total cycles / 1,000.",
    "| HBM2 | 32.0 | 6,144 | 22,560 | **2.975** | 2.839 |",
    "| DDR5 | 6.4 | 30,720 | 47,136 | **1.424** | 0.776 |",
    "| DDR4 | 3.2 | 61,440 | 77,856 | **0.862** | 0.435 |",
    "standalone DRAM implementation reaches the **non-test-caller** rung",
    "hierarchy reaches archive membership and a focused suite but has no external non-test caller",
    "every **non-ideal standalone** read adds ten base cycles",
]
BANNED = [
    "The standalone DRAM model is cycle accurate.",
    "The descriptor DMA queries the standalone DRAM model.",
    "The hierarchy feeds normal execution.",
    "The row model tracks row hits and misses.",
    "The access call advances simulated time.",
    "Returned cycles include returned stall cycles.",
    "The fixed window enforces 256 GB/s.",
    "Reset is equivalent to fresh construction.",
    "The preset parameters are calibrated against silicon.",
    "The historical sweep is executable live-model evidence.",
    "HBM is always faster than DDR.",
]


def require(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(f"CH15_MANUSCRIPT_VALIDATION FAIL: {message}")


def validate_text(s: str) -> tuple[int, int]:
    require(s.startswith("# Chapter 15 — DRAM Service Models and Bandwidth Claims\n"), "title")
    require(PIN in s, "pin")
    words = len(re.findall(r"\b[\w'’-]+\b", s))
    require(5000 <= words <= 7500, f"word count {words}")
    for heading in REQUIRED_HEADINGS:
        require(heading in s, heading)
    for phrase in REQUIRED_PHRASES:
        require(phrase in s, phrase)
    for snippet in CONTEXTUAL_SNIPPETS:
        require(snippet in s, snippet)
    for bad in BANNED:
        require(bad not in s, bad)
    q = s[s.index("## Review questions"):s.index("### Review-question answer key")]
    a = s[s.index("### Review-question answer key"):s.index("## Design exercises")]
    e = s[s.index("## Design exercises"):s.index("## Primary references")]
    require(len(re.findall(r"^\d+\. ", q, re.M)) == 10, "review question count")
    require(len(re.findall(r"^\d+\. ", a, re.M)) == 10, "answer count")
    require(len(re.findall(r"^\d+\. \*\*", e, re.M)) == 8, "exercise count")
    return words, len(re.findall(r"\[[^]]+\]\(([^)]+)\)", s))


def slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return re.sub(r"[ -]+", "-", text).strip("-")


def validate_links(s: str) -> None:
    for link in re.findall(r"\[[^]]+\]\(([^)]+)\)", s):
        if link.startswith(("http://", "https://", "/")):
            continue
        target_text, _, fragment = link.partition("#")
        target = CHAPTER if not target_text else (CHAPTER.parent / target_text).resolve()
        require(target.exists(), link)
        if fragment:
            headings = re.findall(r"^#{1,6}\s+(.+?)\s*$", target.read_text(), re.M)
            require(fragment in {slug(h) for h in headings}, f"broken anchor {link}")


s = CHAPTER.read_text()
word_count, link_count = validate_text(s)
validate_links(s)

# Mutation controls cover a number/equation pair, state threshold, heading, and overclaim.
mutations = [
    ("ceil(64/256) + 50 = 1 + 50 = 51 cycles.", "ceil(64/256) + 50 = 1 + 50 = 52 cycles."),
    ("request **2,001** first receives the **bandwidth-window stall**",
     "request **2,002** first receives the **bandwidth-window stall**"),
    ("TOPS = 8,388,608 operations × clock_GHz / total cycles / 1,000.",
     "TOPS = 8,388,608 operations × clock_GHz / total cycles."),
    ("## 15.8 Integration stops before ordinary data movement", "## 15.8 Integration"),
]
for old, new in mutations:
    require(old in s, f"mutation source missing: {old}")
    try:
        validate_text(s.replace(old, new, 1))
    except SystemExit:
        pass
    else:
        raise SystemExit(f"CH15_MANUSCRIPT_VALIDATION FAIL: mutation survived: {old}")
try:
    validate_text(s + "\nThe descriptor DMA queries the standalone DRAM model.\n")
except SystemExit:
    pass
else:
    raise SystemExit("CH15_MANUSCRIPT_VALIDATION FAIL: overclaim mutation survived")

require(RUN.is_dir(), RUN)
subprocess.run(["sha256sum", "-c", "sha256-retained.txt"], cwd=RUN, check=True,
               stdout=subprocess.DEVNULL)
manifest = {line.split(None, 1)[1] for line in (RUN / "sha256-retained.txt").read_text().splitlines()}
bundled = {p.relative_to(RUN).as_posix() for p in (RUN / "inputs").rglob("*") if p.is_file()}
expected = bundled | {
    "source-archive-sha256.txt", "source-audit.log", "source-audit-mutation.log",
    "archive-members.txt", "input-hashes.txt", "build.log", "test-dram.log",
    "test-memory-hierarchy.log", "test-cycle-model.log", "test-power-model.log",
    "test-dram-mutation.log", "ch15-probe.log", "sweep-recompute.log", "transcript.log",
}
require(manifest == expected, f"manifest members: {sorted(manifest ^ expected)}")
all_run_files = {p.relative_to(RUN).as_posix() for p in RUN.rglob("*") if p.is_file()}
complete_expected = expected | {"sha256-retained.txt", "finalization.log", "predraft-validation.log"}
require(all_run_files == complete_expected, f"run members: {sorted(all_run_files ^ complete_expected)}")

transcript = (RUN / "transcript.log").read_text()
m = re.search(r"^book_head=([0-9a-f]{40})$", transcript, re.M)
if m is None:
    raise SystemExit("CH15_MANUSCRIPT_VALIDATION FAIL: missing input commit")
require(m.group(1) == INPUT_COMMIT, m.group(1))
for frozen in (RUN / "inputs").rglob("*"):
    if frozen.is_file():
        rel = frozen.relative_to(RUN / "inputs")
        blob = subprocess.run(["git", "show", f"{INPUT_COMMIT}:{rel.as_posix()}"], cwd=ROOT,
                              check=True, stdout=subprocess.PIPE).stdout
        require(frozen.read_bytes() == blob, rel)
for gate in (
    f"CH15_SOURCE_AUDIT PASS pin={PIN} hashes=23 predicates=62 checks=85",
    "FOCUSED_TEST PASS 12/12", "MEMHIER_TEST PASS 10/10",
    "CYCLE_MODEL_TEST PASS 21/21 source-linked-not-archive-member=yes",
    "POWER_MODEL_TEST PASS 20/20", "FOCUSED_TEST_MUTATION PASS expected=11/12",
    "PROBE PASS", "SWEEP_AUDIT PASS", "TUSIM_POST PASS", "BOOK_POST PASS",
    "CH15_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS"):
    require(gate in transcript, gate)
probe = (RUN / "ch15-probe.log").read_text()
for gate in (
    "ESTIMATE hbm2_read64=51 hbm3_read819=41",
    "ACCESS overwrite_same_channel cycles=50 stall=1050 ch0_avail=50",
    "REFILL cycle=1000 cycles=50 stall=0 budget=255936 pending_r=64",
    "METER first_bw_stall_request=2001 pending=128064 budget=127936 current=1000",
    "RESET stale_start=1000 stale_size=1000 cycles=50 stall=0 budget=255936 current=0",
    "HIER type=1 rc=0 stall=1000 marker=0x5a unchanged64=1 dram_cycle=0",
    "CH15_PROBE SUMMARY failures=0", "exited normally"):
    require(gate in probe, gate)
mutation = (RUN / "test-dram-mutation.log").read_text()
require("=== Results: 11/12 passed ===" in mutation, "mutation count")
require("exited with code 01" in mutation, "mutation inferior status")
sweep = (RUN / "sweep-recompute.log").read_text()
require("SWEEP_RECOMPUTE PASS contradictions=4 historical_report_not_decision_evidence=yes" in sweep,
        "sweep result")
fin = (RUN / "finalization.log").read_text()
digest = hashlib.sha256((RUN / "transcript.log").read_bytes()).hexdigest()
require("FINALIZED_RUN PASS" in fin and f"transcript_sha256={digest}" in fin, "finalization")
require("CH15_PREDRAFT_VALIDATION PASS files=13" in (RUN / "predraft-validation.log").read_text(),
        "retained predraft validation")

# Live source and book closure state.
require(TUSIM.is_dir(), TUSIM)
tusim_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=TUSIM, check=True,
                            stdout=subprocess.PIPE, text=True).stdout.strip()
require(tusim_head == PIN, f"Tusim head {tusim_head}")
require(subprocess.run(["git", "symbolic-ref", "-q", "HEAD"], cwd=TUSIM,
                       stdout=subprocess.DEVNULL).returncode != 0, "Tusim not detached")
require(subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=TUSIM,
                       check=True, stdout=subprocess.PIPE).stdout == b"", "Tusim dirty")
require(subprocess.run(["git", "branch", "--show-current"], cwd=ROOT, check=True,
                       stdout=subprocess.PIPE, text=True).stdout.strip() == "main", "book branch")
require(subprocess.run(["git", "merge-base", "--is-ancestor", DRAFT_BASE, "HEAD"], cwd=ROOT).returncode == 0,
        "book not descended from reviewed draft base")
require(SNAPSHOT_FILE.is_file(), SNAPSHOT_FILE)
snapshot = SNAPSHOT_FILE.read_text().strip()
require(re.fullmatch(r"[0-9a-f]{40}", snapshot) is not None, "review snapshot format")
require(subprocess.run(["git", "cat-file", "-e", f"{snapshot}^{{commit}}"], cwd=ROOT).returncode == 0,
        "review snapshot commit")
for rel in (CHAPTER_REL, VALIDATOR_REL):
    reviewed = subprocess.run(["git", "show", f"{snapshot}:{rel.as_posix()}"], cwd=ROOT,
                              check=True, stdout=subprocess.PIPE).stdout
    require((ROOT / rel).read_bytes() == reviewed, f"post-review drift: {rel}")

readme = (ROOT / "README.md").read_text()
source_audit = (ROOT / "source-audit.md").read_text()
fidelity = (ROOT / "fidelity-matrix.md").read_text()
plan = (ROOT / "PLAN.md").read_text()
require(CHAPTER_REL.as_posix() in readme, "README chapter link")
require("Chapter 15" in source_audit and "request 2,001" in source_audit, "source audit closure")
require("double-count" in fidelity and "stale" in fidelity, "fidelity closure")
require("Chapter 15" in plan and "complete" in plan, "plan closure")
require((ROOT / "notes/chapter-15-independent-manuscript-review-dispositions.md").is_file(),
        "review dispositions")
require((ROOT / "notes/handoffs/2026-08-04-chapter-15.md").is_file(), "closure handoff")
require(subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT,
                       check=True, stdout=subprocess.PIPE).stdout == b"", "book dirty")
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                      stdout=subprocess.PIPE, text=True).stdout.strip()
print(f"CH15_MANUSCRIPT_VALIDATION PASS words={word_count} links={link_count} "
      f"run={RUN_REL} input_commit={INPUT_COMMIT} review_snapshot={snapshot} head={head}")
