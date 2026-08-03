#!/usr/bin/env python3
"""Fail-closed validation for the Chapter 11 pre-draft evidence bundle."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
TITLE = "Instruction Surfaces and Command-Queue Ordering"
RUN_REL = Path("experiments/runs/ch11-instruction-contracts/20260728-ch11-canonical")
RUN = ROOT / RUN_REL

input_rels = [
    Path("experiments/ch11_source_audit.py"),
    Path("experiments/ch11_instruction_contract_probe.c"),
    Path("experiments/run_ch11_instruction_contract_audit.sh"),
    Path("experiments/ch11_predraft_validate.py"),
    Path("experiments/ch11-instruction-contract-audit-2026-07-28.md"),
    Path("notes/chapter-11-framing-and-evidence-plan.md"),
    Path("notes/chapter-11-source-and-claim-ledger.md"),
    Path("notes/chapter-11-skeptical-review-dispositions.md"),
    Path("references/foundations.md"),
]
for rel in input_rels:
    assert (ROOT / rel).is_file(), rel

framing = (ROOT / input_rels[5]).read_text()
ledger = (ROOT / input_rels[6]).read_text()
dispositions = (ROOT / input_rels[7]).read_text()
report = (ROOT / input_rels[4]).read_text()
for body in (framing, ledger, report, dispositions):
    assert TITLE in body
    assert PIN in body
assert str(RUN_REL) in report
assert "Ranked candidate boundaries" in framing
assert "Reader decision" in framing
assert "Explicitly deferred" in framing
assert "Drafting remains blocked" in framing
for status in ("verified", "qualified", "rejected", "blocked"):
    assert status in ledger
assert "C11.1" in ledger and "C11.43" in ledger
assert "C11.44" not in ledger
for phrase in (
    "59 explicit operation enumerators",
    "68 non-`UNKNOWN` slots",
    "storage retired",
    "next signal ID",
    "queue-epoch-local",
    "num_ops <= 8",
    "only 16 predecessor edges",
):
    assert phrase in ledger or phrase in report, phrase
assert "Final verdict:** **PASS for canonical evidence execution" in dispositions
assert "Drafting is not yet approved" in dispositions

# Filled after all execution inputs are frozen. These pin the complete probe and
# the two scripts that control source acceptance and retained execution.
expected_hashes = {
    "experiments/ch11_instruction_contract_probe.c": "6157ff32f9b444180553f1b44f84e6fbf633c2a3f8d7a541a9efb2fa1b1a9c9d",
    "experiments/ch11_source_audit.py": "21bb1c0a32bd4a44bdc7bab713d618d73963d463c6392c400fa78857902e5012",
    "experiments/run_ch11_instruction_contract_audit.sh": "2bf3f823a84ed7fbf145a459ea5a6dbccad33319aa008859b3fe08c571311894",
}
for rel, expected in expected_hashes.items():
    actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
    assert actual == expected, (rel, actual)

probe = (ROOT / "experiments/ch11_instruction_contract_probe.c").read_text()
async_block = probe[probe.index("static void probe_async_queue"):
                    probe.index("static void probe_queue_barrier")]
barrier_block = probe[probe.index("static void probe_queue_barrier"):
                      probe.index("static void probe_elementwise_count_boundary")]

def safe_probe_shape(async_text: str, barrier_text: str) -> bool:
    return (
        "tu_cmdq_sync" not in async_text
        and "tu_cmdq_sync" not in barrier_text
        and "while (" not in async_text
        and "while (" not in barrier_text
        and "tu_cmdq_wait(cq, pre_id, 2)" in barrier_text
    )

assert safe_probe_shape(async_block, barrier_block)
# Mutation controls prove the semantic guard rejects the two prohibited drain insertions.
assert not safe_probe_shape(async_block + "\ntu_cmdq_sync(cq);", barrier_block)
assert not safe_probe_shape(async_block, barrier_block + "\ntu_cmdq_sync(cq);")
assert "ew.num_ops = 9;" in probe
assert "downstream fused helper rejects count above eight" in probe
assert "RESET_IDS old_cmd=%u new_cmd=%u old_signal=%u new_signal=%u" in probe
assert "post-barrier command completes before earlier pending command" in probe
assert "SCHED_DENSE_BARRIER prior=17" in probe

runner = (ROOT / "experiments/run_ch11_instruction_contract_audit.sh").read_text()
for phrase in (
    '[[ ! -e "$RUN_DIR" ]]',
    'mkdir "$RUN_DIR"',
    'BUNDLED_INPUTS=()',
    'cp "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel"',
    'run timeout 30s "$WORK/ch11-probe"',
    'NEEDED.*libtucmodel',
    'sha256sum transcript.log >> sha256-retained.txt',
    'FINALIZED_RUN PASS',
    'CH11_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS',
):
    assert phrase in runner, phrase
assert "make -C \"$WORK\" clean" not in runner
assert 'cd "$RUN_DIR"' in runner

transcript = (RUN / "transcript.log").read_text()
for gate in (
    f"CH11_SOURCE_AUDIT PASS pin={PIN} hashes=26 predicates=96 checks=122",
    "STATIC_LINK_PASS ch11-probe",
    "9/9 tests passed",
    "Results: 9/9 passed",
    "identity smoke test: PASS",
    "Results: 14/14 passed",
    "ISA sizeof=12 opcode_count_sentinel=128 named_slots=68 unknown_slots=60",
    "SYNC_QUEUE count=4 submitted=4 completed=3 faulted=1 signal_count=0 current_cycle=0",
    "RESET_IDS old_cmd=1 new_cmd=1 old_signal=1 new_signal=5",
    "ASYNC_QUEUE count=2 submitted=2 completed=2 faulted=0 signal_count=0 current_cycle=3",
    "ASYNC_BARRIER fault=3 pre=0 barrier=2 post=2 count=4 cycle=6",
    "ELEMENTWISE_BOUNDARY count=9 status=2 completed=1 faulted=0",
    "SCHED_BARRIER output=DMA.LOAD,NOP,BARRIER valid=1 hoisted=0 inserted=0 cycles=9",
    "SCHED_POSITIVE_INSERT direct=1 run=0 input_nodes=2 output_nodes=2",
    "SCHED_POSITIVE_HOIST direct=1 run=0 input_nodes=3 output_nodes=3",
    "SCHED_DENSE_BARRIER prior=17 retained_preds=16 max_deps=16",
    "ASM expanded_mnemonic_rc=-1",
    "CH11_PROBE SUMMARY failures=0",
    f"TUSIM_POST PASS head={PIN}",
    "ignored_inventory_unchanged=yes",
    "BOOK_POST PASS",
    "inputs_unchanged=yes status_unchanged_outside_run=yes remotes=0",
    "CH11_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
):
    assert gate in transcript, gate
assert "CH11_AUDIT PASS" not in transcript
assert not list(RUN.glob("*.tar"))
assert not (RUN / "worktree").exists()

subprocess.run(
    ["sha256sum", "-c", "sha256-retained.txt"],
    cwd=RUN,
    check=True,
    stdout=subprocess.DEVNULL,
)
manifest = (RUN / "sha256-retained.txt").read_text()
assert "transcript.log" in manifest
for entry in manifest.splitlines():
    rel = entry.split(None, 1)[1]
    assert not rel.startswith("/"), rel
    assert not rel.startswith("../"), rel
for rel in input_rels:
    bundled = RUN / "inputs" / rel
    assert bundled.is_file(), bundled
    assert bundled.read_bytes() == (ROOT / rel).read_bytes(), rel
    assert f"inputs/{rel.as_posix()}" in manifest
finalization = (RUN / "finalization.log").read_text()
assert f"FINALIZED_RUN PASS run_dir={RUN}" in finalization
assert "transcript.log: OK" in finalization

# Local relative Markdown links in pre-draft records must resolve.
for rel in input_rels[4:8]:
    path = ROOT / rel
    body = path.read_text()
    for link in re.findall(r"\[[^]]+\]\(([^)]+)\)", body):
        if link.startswith(("http://", "https://", "#", "/")):
            continue
        target = link.split("#", 1)[0]
        assert (path.parent / target).resolve().exists(), f"broken link {path}: {link}"

print(f"CH11_PREDRAFT_VALIDATION PASS files={len(input_rels)} run={RUN_REL}")
