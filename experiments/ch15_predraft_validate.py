#!/usr/bin/env python3
"""Fail-closed validation for the amended Chapter 15 pre-draft bundle."""
from pathlib import Path
import hashlib
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
TITLE = "DRAM Service Models and Bandwidth Claims"
RUN_ID = os.environ.get("CH15_RUN_ID", "20260804-ch15-canonical-v3")
RUN_REL = Path("experiments/runs/ch15-dram") / RUN_ID
RUN = ROOT / RUN_REL
INPUTS = [Path(x) for x in (
    "edition.yaml", "PLAN.md", "experiments/ch15_source_audit.py",
    "experiments/ch15_dram_probe.c", "experiments/ch15_sweep_recompute.py",
    "experiments/run_ch15_dram_audit.sh", "experiments/ch15_predraft_validate.py",
    "experiments/ch15-dram-audit-2026-08-04.md",
    "notes/chapter-15-framing-and-evidence-plan.md",
    "notes/chapter-15-source-and-claim-ledger.md",
    "notes/chapter-15-skeptical-review-2026-08-04.md",
    "notes/whole-book-replanning-2026-08-04.md", "references/foundations.md")]


def require(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(f"CH15_PREDRAFT_VALIDATION FAIL: {message}")


require(RUN.is_dir(), RUN)
transcript = (RUN / "transcript.log").read_text()
m = re.search(r"^book_head=([0-9a-f]{40})$", transcript, re.M)
if m is None:
    raise SystemExit("CH15_PREDRAFT_VALIDATION FAIL: missing book_head")
commit = m.group(1)


def blob(rel: Path) -> bytes:
    return subprocess.run(["git", "show", f"{commit}:{rel.as_posix()}"], cwd=ROOT,
                          check=True, stdout=subprocess.PIPE).stdout


for rel in INPUTS:
    require((RUN / "inputs" / rel).read_bytes() == blob(rel), f"frozen input mismatch: {rel}")
plan = (RUN / "inputs" / Path("PLAN.md")).read_text()
framing = (RUN / "inputs" / Path("notes/chapter-15-framing-and-evidence-plan.md")).read_text()
ledger = (RUN / "inputs" / Path("notes/chapter-15-source-and-claim-ledger.md")).read_text()
report = (RUN / "inputs" / Path("experiments/ch15-dram-audit-2026-08-04.md")).read_text()
for name, body in (("framing", framing), ("ledger", ledger), ("report", report)):
    require(TITLE in body and PIN in body, f"title/pin missing: {name}")
for phrase in ("Ranked scope candidates", "Reader decision", "Explicitly out of scope",
               "Claims the chapter must not make"):
    require(phrase in framing, phrase)
for status in ("verified", "qualified", "rejected", "blocked"):
    require(status in ledger, status)
for claim in ("C15.1", "C15.28", "C15.29", "C15.30", "C15.31", "C15.32", "C15.33", "C15.34"):
    require(claim in ledger, claim)
require("22 chapters plus appendices" in plan, "plan chapter count")
for gate in (
    f"CH15_SOURCE_AUDIT PASS pin={PIN} hashes=23 predicates=62 checks=85",
    "SOURCE_AUDIT_MUTATION PASS", "ARCHIVE_MEMBER PASS dram_model.o",
    "ARCHIVE_MEMBER PASS memory_hierarchy.o", "STATIC_LINK_PASS ch15-test-dram",
    "STATIC_LINK_PASS ch15-test-memhier", "STATIC_LINK_PASS ch15-test-cycle",
    "STATIC_LINK_PASS ch15-test-power", "STATIC_LINK_PASS ch15-probe",
    "FOCUSED_TEST PASS 12/12", "MEMHIER_TEST PASS 10/10",
    "CYCLE_MODEL_TEST PASS 21/21 source-linked-not-archive-member=yes",
    "POWER_MODEL_TEST PASS 20/20", "FOCUSED_TEST_MUTATION PASS expected=11/12",
    "PROBE PASS", "SWEEP_AUDIT PASS", f"TUSIM_POST PASS head={PIN}",
    "ignored_inventory_unchanged=yes", "BOOK_POST PASS",
    "remote_unchanged=yes no_push_performed=yes",
    "CH15_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS"):
    require(gate in transcript, gate)
probe = (RUN / "ch15-probe.log").read_text()
for gate in (
    "ESTIMATE hbm2_read64=51 hbm3_read819=41",
    "ACCESS first cycles=50 stall=1000 current=0 budget=0",
    "ACCESS overwrite_same_channel cycles=50 stall=1050 ch0_avail=50",
    "REFILL cycle=1000 cycles=50 stall=0 budget=255936 pending_r=64",
    "ROW read_cycles=60 read_stall=1000 write_cycles=50 write_stall=1060 conflicts=1",
    "STATS cycle=0 read_bw=1024.0 util=4.0 peak=256.0",
    "METER first_bw_stall_request=2001 pending=128064 budget=127936 current=1000",
    "RESET stale_start=1000 stale_size=1000 cycles=50 stall=0 budget=255936 current=0",
    "HIER type=1 rc=0 stall=1000 marker=0x5a unchanged64=1 dram_cycle=0",
    "CONFIG rc=0 type=3 bw=777.0 row=1 rlat=33 wlat=44 manual_bw=819.0 manual_row=0",
    "CH15_PROBE SUMMARY failures=0", "exited normally"):
    require(gate in probe, gate)
mutation = (RUN / "test-dram-mutation.log").read_text()
require("=== Results: 11/12 passed ===" in mutation, "mutation count")
require("exited with code 01" in mutation, "mutation inferior status")
for name in ("test-dram.log", "test-memory-hierarchy.log", "test-cycle-model.log", "test-power-model.log"):
    require("exited normally" in (RUN / name).read_text(), name)
sweep = (RUN / "sweep-recompute.log").read_text()
for gate in ("RECOMPUTE HBM2 8GHz", "RECOMPUTE DDR5 8GHz", "RECOMPUTE DDR4 8GHz",
             "RECOMPUTE DDR4 1GHz", "SWEEP_RECOMPUTE PASS contradictions=4"):
    require(gate in sweep, gate)
subprocess.run(["sha256sum", "-c", "sha256-retained.txt"], cwd=RUN, check=True,
               stdout=subprocess.DEVNULL)
manifest = {line.split(None, 1)[1] for line in (RUN / "sha256-retained.txt").read_text().splitlines()}
expected = {f"inputs/{x.as_posix()}" for x in INPUTS} | {
    "source-archive-sha256.txt", "source-audit.log", "source-audit-mutation.log",
    "archive-members.txt", "input-hashes.txt", "build.log", "test-dram.log",
    "test-memory-hierarchy.log", "test-cycle-model.log", "test-power-model.log",
    "test-dram-mutation.log", "ch15-probe.log", "sweep-recompute.log", "transcript.log"}
require(manifest == expected, f"manifest members: {sorted(manifest ^ expected)}")
all_files = {p.relative_to(RUN).as_posix() for p in RUN.rglob("*") if p.is_file()}
require(all_files == expected | {"sha256-retained.txt", "finalization.log", "predraft-validation.log"},
        f"run members: {sorted(all_files ^ (expected | {'sha256-retained.txt', 'finalization.log', 'predraft-validation.log'}))}")
fin = (RUN / "finalization.log").read_text()
digest = hashlib.sha256((RUN / "transcript.log").read_bytes()).hexdigest()
require("FINALIZED_RUN PASS" in fin, "finalization")
require(f"transcript_sha256={digest}" in fin, "transcript digest")
print(f"CH15_PREDRAFT_VALIDATION PASS files={len(INPUTS)} run={RUN_REL} input_commit={commit}")
