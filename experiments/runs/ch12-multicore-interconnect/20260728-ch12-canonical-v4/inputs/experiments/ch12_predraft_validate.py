#!/usr/bin/env python3
"""Fail-closed validation for a frozen Chapter 12 pre-draft evidence bundle."""
from __future__ import annotations

from pathlib import Path
import hashlib
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
TITLE = "Multi-Core Clusters and Interconnect Heuristic Estimates"
RUN_ID = os.environ.get("CH12_RUN_ID", "20260728-ch12-canonical-v4")
RUN_REL = Path("experiments/runs/ch12-multicore-interconnect") / RUN_ID
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
    Path("notes/chapter-12-independent-manuscript-review-dispositions.md"),
]
assert RUN.is_dir(), RUN
transcript = (RUN / "transcript.log").read_text()
book_head_match = re.search(r"^book_head=([0-9a-f]{40})$", transcript, re.MULTILINE)
assert book_head_match
input_commit = book_head_match.group(1)


def git_blob(rel: Path) -> bytes:
    return subprocess.run(
        ["git", "show", f"{input_commit}:{rel.as_posix()}"],
        cwd=ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout


frozen: dict[Path, bytes] = {}
for rel in input_rels:
    bundled = RUN / "inputs" / rel
    assert bundled.is_file(), bundled
    frozen[rel] = git_blob(rel)
    assert bundled.read_bytes() == frozen[rel], rel

report = frozen[input_rels[5]].decode()
framing = frozen[input_rels[6]].decode()
ledger = frozen[input_rels[7]].decode()
dispositions = frozen[input_rels[8]].decode()
foundations = frozen[input_rels[9]].decode()
for body in (report, framing, ledger, dispositions):
    assert TITLE in body
    assert PIN in body
assert str(RUN_REL) in report
for phrase in ("Ranked candidate boundaries", "Independent scope-panel disposition", "Reader decision", "Explicitly deferred"):
    assert phrase in framing
assert "reopened after the independent technical, editorial, and reproducibility reviews returned BLOCK" in framing
for status in ("verified", "qualified", "rejected", "blocked"):
    assert status in ledger
assert "C12.1" in ledger and "C12.47" in ledger
for phrase in (
    "global-state-swapping facade",
    "heuristic score, not a proved bound",
    "barrier_counter",
    "implementation-only",
    "trusted callers",
    "not a passing configuration-suite gate",
    "final `bottleneck_link_cycles + max_route_cycles` addition is unchecked",
    "numerator wrap",
):
    assert phrase in ledger or phrase in report, phrase
for key in ("[DT01]", "[DS87]", "[PY09]"):
    assert key in foundations
assert "Current verdict:** **BLOCK pending canonical-v4" in dispositions
assert "invalid lower-bound classification" in dispositions
assert 'CH12_RUN_ID="repro-$(date -u +%Y%m%dT%H%M%SZ)"' in report
assert f"CH12_RUN_ID={RUN_ID}" not in report
assert "sha256sum -c sha256-retained.txt" in report
assert "sha256sum -c bundle-sha256.txt" in report

probe = frozen[input_rels[2]].decode()
send_block = probe[probe.index("static void probe_send"):probe.index("static void probe_traffic")]
collective_block = probe[probe.index("static void probe_collectives"):probe.index("int main")]


def safe_probe_shape(send: str, collectives: str, whole: str) -> bool:
    return (
        "pthread_" not in whole
        and "tu_cluster_spmd_execute" not in whole
        and "UINT32_MAX" not in send
        and ".blocking=false" in send
        and "memcmp(&msg" not in send
        and "if (rc != 0)" in whole
        and "barrier_counter==0" in collectives
        and "allreduce_cycle_delta=%\" PRIu64" in collectives
    )


assert safe_probe_shape(send_block, collective_block, probe)
assert not safe_probe_shape(send_block + "\nmsg.src_offset=UINT32_MAX;", collective_block, probe)
assert not safe_probe_shape(send_block, collective_block.replace("barrier_counter==0", "barrier_counter==1"), probe)
for line in (
    "CONFIG parsed_enabled=%d parsed_cores=%u parsed_topology=%d",
    "EQUATIONS legacy=%", "SEND blocking=%d", "TRAFFIC same=%",
    "HEURISTIC_COUNTEREXAMPLE isolated=%", "ROUTES patternA_XY=%",
    "COLLECTIVES broadcast_messages=3", "CH12_PROBE SUMMARY failures=%d",
):
    assert line in probe, line

source_audit = frozen[input_rels[1]].decode()
for phrase in (
    '"tu_cmodel/tu_cluster.c": "7c968e95',
    "exact-c-callers-spmd-implementation-only",
    "constructor-no-mesh-rows-upper-bound",
    "constructor-no-overflow-safe-mesh-ceiling",
    "send-no-overflow-safe-source-span-check",
    "shared-score-no-overflow-guard",
    "message-size-u32-bounds-link-load",
    "allreduce-no-explicit-region-bounds",
    "generator-emits-router-latency",
    "bulk-write-proceeds-to-memcpy",
    "focused-multicore-16-distinct-test-calls",
    "predicates={PREDICATES}",
):
    assert phrase in source_audit, phrase

runner = frozen[input_rels[3]].decode()
for phrase in (
    '[[ ! -e "$RUN_DIR" ]]',
    '[[ -z "$(cat "$BOOK_STATUS_BEFORE")" ]]',
    'cp "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel"',
    "SOURCE_AUDIT_MUTATION PASS", "FOCUSED_TEST_MUTATION PASS",
    "CONFIG_SUITE_QUALIFIED", 'run timeout 90s "$WORK/ch12-probe"',
    "NEEDED.*libtucmodel", "predicates=155 checks=183",
    "sha256sum transcript.log >> sha256-retained.txt",
    "FINALIZED_RUN PASS", "predraft-validation.log", "bundle-sha256.txt",
    "CH12_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
):
    assert phrase in runner, phrase
assert "make -C \"$WORK\" clean" not in runner
assert 'ulimit -c 0' in runner
assert 'cd "$RUN_DIR"' in runner

for gate in (
    f"CH12_SOURCE_AUDIT PASS pin={PIN} hashes=28 predicates=155 checks=183",
    "SOURCE_AUDIT_MUTATION PASS", "ARCHIVE_MEMBER PASS tu_core.o",
    "ARCHIVE_MEMBER PASS tu_cluster.o", "STATIC_LINK_PASS ch12-probe",
    "STATIC_LINK_PASS ch12-test-multicore", "=== Results: 16/16 passed, 0 failed ===",
    "FOCUSED_TEST_MUTATION PASS", "CONFIG_SUITE_QUALIFIED",
    "CONFIG parsed_enabled=1 parsed_cores=8 parsed_topology=2 cluster_cores=4 cluster_topology=1 sw=2 contention=1 route=1 link=32 router=7",
    "EQUATIONS legacy=15 cut=79 store=207",
    "SEND blocking=0 descriptor_latency=999 stats_messages=1 stats_bytes=16 stats_cycles=15 dst_delta=15",
    "TRAFFIC same=133 disjoint=69 ideal=69 bottleneck=128 link=0->1",
    "HEURISTIC_COUNTEREXAMPLE isolated=94 bottleneck=128 estimated=158 shared_pair_term=133 link=0->1",
    "ROUTES patternA_XY=606 patternA_YX=222 patternB_XY=222 patternB_YX=606",
    "allreduce_cycle_delta=0 barrier_delta=10 barrier_state=0",
    "CH12_PROBE SUMMARY failures=0", f"TUSIM_POST PASS head={PIN}",
    "ignored_inventory_unchanged=yes", "BOOK_POST PASS",
    "inputs_unchanged=yes status_unchanged_outside_run=yes remotes=0",
    "CH12_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
):
    assert gate in transcript, gate
assert "CH12_AUDIT PASS" not in transcript
for pattern in ("*.tar", "*.o", "core*"):
    assert not list(RUN.glob(pattern))
assert not (RUN / "worktree").exists()

subprocess.run(["sha256sum", "-c", "sha256-retained.txt"], cwd=RUN, check=True, stdout=subprocess.DEVNULL)
manifest_lines = (RUN / "sha256-retained.txt").read_text().splitlines()
manifest_members = {line.split(None, 1)[1] for line in manifest_lines}
expected_members = {f"inputs/{rel.as_posix()}" for rel in input_rels} | {
    "source-archive-sha256.txt", "source-audit.log", "source-audit-mutation.log",
    "archive-members.txt", "input-hashes.txt", "build.log", "test-multicore.log",
    "test-multicore-mutation.log", "test-config.log", "contention-sweep.log",
    "routing-sweep.log", "ch12-probe.log", "transcript.log",
}
assert manifest_members == expected_members, sorted(manifest_members ^ expected_members)
for rel in manifest_members:
    assert not rel.startswith(("/", "../")), rel

finalization = (RUN / "finalization.log").read_text()
assert f"FINALIZED_RUN PASS run_dir={RUN}" in finalization
transcript_digest = hashlib.sha256((RUN / "transcript.log").read_bytes()).hexdigest()
assert f"transcript_sha256={transcript_digest}" in finalization
assert "transcript.log: OK" in finalization
config_log = (RUN / "test-config.log").read_text()
assert "Config: interconnect switching parse + validation      PASS" in config_log
assert "stack smashing detected" in config_log
assert "CONFIG_SUITE_QUALIFIED nonzero_rc=134" in transcript

print(f"CH12_PREDRAFT_VALIDATION PASS files={len(input_rels)} run={RUN_REL} input_commit={input_commit}")
