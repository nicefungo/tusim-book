#!/usr/bin/env python3
"""Fail-closed validation for a frozen Chapter 15 pre-draft evidence bundle."""
from pathlib import Path
import hashlib, os, re, subprocess

ROOT = Path(__file__).resolve().parents[1]
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
TITLE = "DRAM Service Models and Bandwidth Claims"
RUN_ID = os.environ.get("CH15_RUN_ID", "20260804-ch15-canonical")
RUN_REL = Path("experiments/runs/ch15-dram") / RUN_ID
RUN = ROOT / RUN_REL
INPUTS = [Path(x) for x in (
    "edition.yaml", "PLAN.md", "experiments/ch15_source_audit.py",
    "experiments/ch15_dram_probe.c", "experiments/run_ch15_dram_audit.sh",
    "experiments/ch15_predraft_validate.py", "experiments/ch15-dram-audit-2026-08-04.md",
    "notes/chapter-15-framing-and-evidence-plan.md",
    "notes/chapter-15-source-and-claim-ledger.md",
    "notes/whole-book-replanning-2026-08-04.md", "references/foundations.md")]
assert RUN.is_dir(), RUN
transcript = (RUN / "transcript.log").read_text()
m = re.search(r"^book_head=([0-9a-f]{40})$", transcript, re.M); assert m
commit = m.group(1)

def blob(rel):
    return subprocess.run(["git","show",f"{commit}:{rel.as_posix()}"],cwd=ROOT,
                          check=True,stdout=subprocess.PIPE).stdout
for rel in INPUTS:
    assert (RUN/"inputs"/rel).read_bytes() == blob(rel), rel
framing=(RUN/"inputs"/INPUTS[7]).read_text(); ledger=(RUN/"inputs"/INPUTS[8]).read_text()
report=(RUN/"inputs"/INPUTS[6]).read_text(); plan=(RUN/"inputs"/INPUTS[1]).read_text()
for body in (framing,ledger,report): assert TITLE in body and PIN in body
for phrase in ("Ranked scope candidates","Reader decision","Explicitly out of scope","Claims the chapter must not make"):
    assert phrase in framing, phrase
for status in ("verified","qualified","rejected","blocked"): assert status in ledger
assert "C15.1" in ledger and "C15.28" in ledger
assert "21 chapters plus appendices" in plan
for gate in (
    f"CH15_SOURCE_AUDIT PASS pin={PIN} hashes=15 predicates=39 checks=54",
    "SOURCE_AUDIT_MUTATION PASS", "ARCHIVE_MEMBER PASS dram_model.o",
    "ARCHIVE_MEMBER PASS memory_hierarchy.o", "STATIC_LINK_PASS ch15-test-dram",
    "STATIC_LINK_PASS ch15-probe", "FOCUSED_TEST PASS 12/12",
    "FOCUSED_TEST_MUTATION PASS expected=11/12", "PROBE PASS",
    f"TUSIM_POST PASS head={PIN}", "ignored_inventory_unchanged=yes",
    "BOOK_POST PASS", "remote_unchanged=yes no_push_performed=yes",
    "CH15_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS"):
    assert gate in transcript, gate
probe_log = (RUN/"ch15-probe.log").read_text()
for gate in (
    "ESTIMATE hbm2_read64=51 hbm3_read819=41",
    "ACCESS first cycles=50 stall=1000 current=0 budget=0",
    "REFILL cycle=1000 cycles=50 stall=0 budget=255936 pending_r=64",
    "ROW read_cycles=60 read_stall=1000 write_cycles=50 write_stall=1060 conflicts=1",
    "STATS cycle=0 read_bw=1024.0 util=4.0 peak=256.0",
    "HIER type=1 rc=0 stall=1000 marker=0x5a dram_cycle=0",
    "CONFIG rc=0 type=3 bw=777.0 row=1 rlat=33 wlat=44 manual_bw=819.0 manual_row=0",
    "CH15_PROBE SUMMARY failures=0"):
    assert gate in probe_log, gate
assert "=== Results: 11/12 passed ===" in (RUN/"test-dram-mutation.log").read_text()
subprocess.run(["sha256sum","-c","sha256-retained.txt"],cwd=RUN,check=True,stdout=subprocess.DEVNULL)
manifest={(line.split(None,1)[1]) for line in (RUN/"sha256-retained.txt").read_text().splitlines()}
expected={f"inputs/{x.as_posix()}" for x in INPUTS}|{
 "source-archive-sha256.txt","source-audit.log","source-audit-mutation.log",
 "archive-members.txt","input-hashes.txt","build.log","test-dram.log",
 "test-dram-mutation.log","ch15-probe.log","transcript.log"}
assert manifest==expected, sorted(manifest^expected)
fin=(RUN/"finalization.log").read_text(); digest=hashlib.sha256((RUN/"transcript.log").read_bytes()).hexdigest()
assert "FINALIZED_RUN PASS" in fin and f"transcript_sha256={digest}" in fin
print(f"CH15_PREDRAFT_VALIDATION PASS files={len(INPUTS)} run={RUN_REL} input_commit={commit}")
