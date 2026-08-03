#!/usr/bin/env python3
"""Fail-closed validation for the Chapter 10 pre-draft evidence bundle."""
from pathlib import Path
import hashlib
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
TITLE = "DMA Descriptor Contracts and Tick-Driven Execution"
RUN_REL = Path("experiments/runs/ch10-dma-contracts/20260727T223000Z-hashguard")
RUN = ROOT / RUN_REL
files = [
    ROOT / "notes/chapter-10-framing-and-evidence-plan.md",
    ROOT / "notes/chapter-10-source-and-claim-ledger.md",
    ROOT / "notes/chapter-10-skeptical-review-dispositions.md",
    ROOT / "experiments/ch10-dma-descriptor-audit-2026-07-27.md",
    ROOT / "experiments/ch10_source_audit.py",
    ROOT / "experiments/ch10_data_movement_probe.c",
    ROOT / "experiments/ch10_extended_probe.c",
    ROOT / "experiments/run_ch10_data_movement_audit.sh",
    ROOT / "references/foundations.md",
]
for p in files:
    assert p.is_file(), p

framing, ledger, dispositions, report = [p.read_text() for p in files[:4]]
for body in (framing, ledger, report):
    assert TITLE in body
    assert PIN in body
    assert str(RUN_REL) in body
assert "Ranked candidate boundaries" in framing
assert "Prerequisite" in framing or "prerequisite" in framing
assert "Drafting begins only after" in framing
assert "| verified |" in ledger and "| qualified |" in ledger
assert "| rejected |" in ledger and "| blocked |" in ledger
assert "| planned |" not in ledger
assert "C10.35" in ledger
assert "reinitialization" in ledger.lower()
assert "Requests 4–8 are unsafe" in ledger
probe = (ROOT / "experiments/ch10_extended_probe.c").read_text()
assert hashlib.sha256(probe.encode()).hexdigest() == \
       "46b154556e201fa1d84468afe382813f1e0fb69b3d86b3555c9b25c5f606c10d"
for start, end in (("static void chain_then_head_child", "static void submit_while_active_child"),
                   ("static void submit_while_active_child", "static void run_corruption_child")):
    block = probe[probe.index(start):probe.index(end)]
    assert block.count("tu_dma_init_full(") == 1
    assert block.index("tu_dma_init_full(") < block.index("tu_dma_submit_desc(")
    for forbidden in ("tu_dma_flush", "tu_dma_desc_destroy", "tu_dma_destroy",
                      "while (", "while(", "for (", "for(", "do {"):
        assert forbidden not in block, f"unsafe corruption-child operation: {forbidden}"
chain_block = probe[probe.index("static void chain_then_head_child"):
                    probe.index("static void submit_while_active_child")]
assert "tu_dma_tick(" not in chain_block
active_block = probe[probe.index("static void submit_while_active_child"):
                     probe.index("static void run_corruption_child")]
assert active_block.count("tu_dma_tick(") == 1
assert active_block.index("tu_dma_tick(") < active_block.rindex("tu_dma_submit_desc(")
runner_block = probe[probe.index("static void run_corruption_child"):
                     probe.index("static void queue_link_corruption")]
assert "pid_t pid=fork();" in runner_block
child_branch = runner_block[runner_block.index("if (pid==0)"):runner_block.index("CHECK(true")]
assert re.fullmatch(
    r"if \(pid==0\) \{\s*int before=failures;\s*body\(\);\s*"
    r"fflush\(NULL\);\s*_exit\(failures==before \? 0 : 1\);\s*\}\s*",
    child_branch,
)
for section in ("Byte taxonomy and span equations", "Lifecycle predicates",
                "Ownership matrix", "Counter units", "Evidence labels"):
    assert section in ledger, section
assert "First verdict:** blocked" in dispositions
assert "Only then may Chapter 10 prose be drafted" in dispositions

transcript = (RUN / "transcript.log").read_text()
for gate in (
    "SOURCE_AUDIT PASS pin=" + PIN + " checks=65 hashes=33",
    "EXPECTED_FINDING MATCH address-generator transposed case fails 12/13",
    "PIPELINE_SUITE_SKIP enforced by SOURCE_AUDIT",
    "SUMMARY failures=0",
    "EXTENDED_SUMMARY failures=0",
    "TUSIM_POST PASS head=" + PIN,
    "ignored_inventory_unchanged=yes",
    "BOOK_POST PASS",
    "inputs_unchanged=yes status_unchanged_outside_run=yes remotes=0",
    "sync_error id=",
    "async_error_after_next_tick active=0 completed_count=1 transfers=0",
    "flush_error flag=0 timestamp=0 completed_count=1 transfers=0",
    "json_parse rc=0 bus_bits=128 burst=32 channels=1 depth=2 async=1 multicast=0",
    "AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
):
    assert gate in transcript, gate
assert "AUDIT_PASS" not in transcript
assert not (RUN / f"tusim-{PIN}.tar").exists()
assert not (RUN / "worktree").exists()

manifest = (RUN / "sha256-retained.txt").read_text()
# Chapter 10's historical manifest named live book paths rather than copying
# every input into the run. Later chapters legitimately extend shared inputs,
# and validator maintenance can change the live scripts. Verify all execution
# inputs against the frozen execution-input commit while checking retained
# outputs at their run paths.
CH10_INPUT_COMMIT = "7f06cb8e59235cb3765793394b144fc0de34b512"
for line in manifest.splitlines():
    expected, rel = line.split(None, 1)
    if rel.startswith("experiments/runs/ch10-dma-contracts/"):
        data = (ROOT / rel).read_bytes()
    else:
        data = subprocess.run(
            ["git", "show", f"{CH10_INPUT_COMMIT}:{rel}"],
            cwd=ROOT, check=True, stdout=subprocess.PIPE,
        ).stdout
    assert hashlib.sha256(data).hexdigest() == expected, rel
assert str(RUN_REL / "transcript.log") in manifest
finalization = (RUN / "finalization.log").read_text()
assert f"FINALIZED_RUN PASS run_dir={RUN}" in finalization
assert f"{RUN_REL}/transcript.log: OK" in finalization

# Local relative Markdown links in pre-draft records must resolve.
for p in files[:4]:
    body = p.read_text()
    for link in re.findall(r"\[[^]]+\]\(([^)]+)\)", body):
        if link.startswith(("http://", "https://", "#", "/")):
            continue
        target = link.split("#", 1)[0]
        assert (p.parent / target).resolve().exists(), f"broken link {p}: {link}"

print(f"CH10_PREDRAFT_VALIDATION PASS files={len(files)} run={RUN_REL}")
