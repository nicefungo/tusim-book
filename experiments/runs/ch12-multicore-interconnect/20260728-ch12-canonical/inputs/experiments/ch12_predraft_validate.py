#!/usr/bin/env python3
"""Fail-closed validation for the Chapter 12 pre-draft evidence bundle."""
from __future__ import annotations

from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
TITLE = "Multi-Core Clusters and Interconnect Lower Bounds"
RUN_REL = Path("experiments/runs/ch12-multicore-interconnect/20260728-ch12-canonical")
RUN = ROOT / RUN_REL

input_rels = [
    Path("edition.yaml"),
    Path("experiments/ch12_source_audit.py"),
    Path("experiments/ch12_multicore_interconnect_probe.c"),
    Path("experiments/run_ch12_multicore_interconnect_audit.sh"),
    Path("experiments/ch12_predraft_validate.py"),
    Path("experiments/ch12-multicore-interconnect-audit-2026-07-28.md"),
    Path("notes/chapter-12-framing-and-evidence-plan.md"),
    Path("notes/chapter-12-source-and-claim-ledger.md"),
    Path("notes/chapter-12-skeptical-review-dispositions.md"),
    Path("references/foundations.md"),
]
for rel in input_rels:
    assert (ROOT / rel).is_file(), rel

report = (ROOT / input_rels[5]).read_text()
framing = (ROOT / input_rels[6]).read_text()
ledger = (ROOT / input_rels[7]).read_text()
dispositions = (ROOT / input_rels[8]).read_text()
foundations = (ROOT / input_rels[9]).read_text()
for body in (report, framing, ledger, dispositions):
    assert TITLE in body
    assert PIN in body
assert str(RUN_REL) in report
assert "Ranked candidate boundaries" in framing
assert "Independent scope-panel disposition" in framing
assert "Reader decision" in framing
assert "Explicitly deferred" in framing
assert "Drafting remains blocked" in framing
for status in ("verified", "qualified", "rejected", "blocked"):
    assert status in ledger
assert "C12.1" in ledger and "C12.42" in ledger
assert "C12.43" not in ledger
for phrase in (
    "serialized facade",
    "deterministic lower bound",
    "barrier_counter",
    "implementation-only",
    "trusted callers",
    "not a passing configuration-suite gate",
):
    assert phrase in ledger or phrase in report, phrase
for key in ("[DT01]", "[DS87]", "[PY09]"):
    assert key in foundations
assert "Final verdict:** **PASS for canonical evidence execution" in dispositions
assert "Drafting is not yet approved" in dispositions
assert 'CH12_RUN_ID="repro-$(date -u +%Y%m%dT%H%M%SZ)"' in report
assert "CH12_RUN_ID=20260728-ch12-canonical" not in report
assert "sha256sum -c sha256-retained.txt" in report

probe = (ROOT / "experiments/ch12_multicore_interconnect_probe.c").read_text()
send_block = probe[probe.index("static void probe_send"):probe.index("static void probe_traffic")]
collective_block = probe[probe.index("static void probe_collectives"):probe.index("int main")]


def safe_probe_shape(send: str, collectives: str, whole: str) -> bool:
    return (
        "pthread_" not in whole
        and "tu_cluster_spmd_execute" not in whole
        and "UINT32_MAX" not in send
        and ".blocking=false" in send
        and "barrier_counter==0" in collectives
        and "allreduce_cycle_delta=%\" PRIu64" in collectives
    )


assert safe_probe_shape(send_block, collective_block, probe)
assert not safe_probe_shape(send_block + "\nmsg.src_offset=UINT32_MAX;", collective_block, probe)
assert not safe_probe_shape(send_block, collective_block.replace("barrier_counter==0", "barrier_counter==1"), probe)
for line in (
    "CONFIG parsed_enabled=1",
    "EQUATIONS legacy=%",
    "SEND blocking=%d",
    "TRAFFIC same=%",
    "ROUTES patternA_XY=%",
    "COLLECTIVES broadcast_messages=3",
    "CH12_PROBE SUMMARY failures=%d",
):
    assert line in probe, line

source_audit = (ROOT / "experiments/ch12_source_audit.py").read_text()
for phrase in (
    '"tu_cmodel/tu_cluster.c": "7c968e95',
    "whole-tree-spmd-implementation-only",
    "constructor-no-topology-upper-bound-check",
    "allreduce-no-explicit-region-bounds",
    "focused-multicore-16-distinct-test-calls",
    "predicates={PREDICATES}",
):
    assert phrase in source_audit, phrase

runner = (ROOT / "experiments/run_ch12_multicore_interconnect_audit.sh").read_text()
for phrase in (
    '[[ ! -e "$RUN_DIR" ]]',
    '[[ -z "$(cat "$BOOK_STATUS_BEFORE")" ]]',
    'cp "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel"',
    "SOURCE_AUDIT_MUTATION PASS",
    "FOCUSED_TEST_MUTATION PASS",
    "CONFIG_SUITE_QUALIFIED",
    'run timeout 90s "$WORK/ch12-probe"',
    "NEEDED.*libtucmodel",
    "predicates=116 checks=141",
    "sha256sum transcript.log >> sha256-retained.txt",
    "FINALIZED_RUN PASS",
    "CH12_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
):
    assert phrase in runner, phrase
assert "make -C \"$WORK\" clean" not in runner
assert 'ulimit -c 0' in runner
assert 'cd "$RUN_DIR"' in runner

transcript = (RUN / "transcript.log").read_text()
for gate in (
    f"CH12_SOURCE_AUDIT PASS pin={PIN} hashes=25 predicates=116 checks=141",
    "SOURCE_AUDIT_MUTATION PASS",
    "ARCHIVE_MEMBER PASS tu_core.o",
    "ARCHIVE_MEMBER PASS tu_cluster.o",
    "STATIC_LINK_PASS ch12-probe",
    "STATIC_LINK_PASS ch12-test-multicore",
    "=== Results: 16/16 passed, 0 failed ===",
    "FOCUSED_TEST_MUTATION PASS",
    "CONFIG_SUITE_QUALIFIED",
    "CONFIG parsed_enabled=1 parsed_cores=8 parsed_topology=2 cluster_cores=4 cluster_topology=1 sw=2 contention=1 route=1 link=32 router=7",
    "EQUATIONS legacy=15 cut=79 store=207",
    "SEND blocking=0 descriptor_latency=999 stats_messages=1 stats_bytes=16 stats_cycles=15 dst_delta=15",
    "TRAFFIC same=133 disjoint=69 ideal=69 bottleneck=128 link=0->1",
    "ROUTES patternA_XY=606 patternA_YX=222 patternB_XY=222 patternB_YX=606",
    "allreduce_cycle_delta=0 barrier_delta=10 barrier_state=0",
    "CH12_PROBE SUMMARY failures=0",
    f"TUSIM_POST PASS head={PIN}",
    "ignored_inventory_unchanged=yes",
    "BOOK_POST PASS",
    "inputs_unchanged=yes status_unchanged_outside_run=yes remotes=0",
    "CH12_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
):
    assert gate in transcript, gate
assert "CH12_AUDIT PASS" not in transcript
assert not list(RUN.glob("*.tar"))
assert not list(RUN.glob("*.o"))
assert not list(RUN.glob("core*"))
assert not (RUN / "worktree").exists()

subprocess.run(
    ["sha256sum", "-c", "sha256-retained.txt"], cwd=RUN,
    check=True, stdout=subprocess.DEVNULL,
)
manifest = (RUN / "sha256-retained.txt").read_text()
assert "transcript.log" in manifest
for entry in manifest.splitlines():
    rel = entry.split(None, 1)[1]
    assert not rel.startswith("/"), rel
    assert not rel.startswith("../"), rel

book_head_match = re.search(r"^book_head=([0-9a-f]{40})$", transcript, re.MULTILINE)
assert book_head_match
input_commit = book_head_match.group(1)
for rel in input_rels:
    bundled = RUN / "inputs" / rel
    assert bundled.is_file(), bundled
    frozen = subprocess.run(
        ["git", "show", f"{input_commit}:{rel.as_posix()}"],
        cwd=ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout
    assert bundled.read_bytes() == frozen, rel
    assert (ROOT / rel).read_bytes() == frozen, rel
    assert f"inputs/{rel.as_posix()}" in manifest

finalization = (RUN / "finalization.log").read_text()
assert f"FINALIZED_RUN PASS run_dir={RUN}" in finalization
assert "transcript.log: OK" in finalization

for rel in input_rels[5:10]:
    path = ROOT / rel
    body = path.read_text()
    for link in re.findall(r"\[[^]]+\]\(([^)]+)\)", body):
        if link.startswith(("http://", "https://", "#", "/")):
            continue
        target = link.split("#", 1)[0]
        assert (path.parent / target).resolve().exists(), f"broken link {path}: {link}"

print(f"CH12_PREDRAFT_VALIDATION PASS files={len(input_rels)} run={RUN_REL} input_commit={input_commit}")
