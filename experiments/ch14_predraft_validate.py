#!/usr/bin/env python3
"""Fail-closed validation for a frozen Chapter 14 pre-draft evidence bundle."""
from __future__ import annotations

from pathlib import Path
import hashlib
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
TITLE = "Operator Compute Engines: Functional Semantics and Engine Metrics"
RUN_ID = os.environ.get("CH14_RUN_ID", "20260804-ch14-canonical")
RUN_REL = Path("experiments/runs/ch14-compute-engines") / RUN_ID
RUN = ROOT / RUN_REL

input_rels = [
    Path("edition.yaml"),
    Path("experiments/ch14_source_audit.py"),
    Path("experiments/ch14_compute_engines_probe.c"),
    Path("experiments/run_ch14_compute_engines_audit.sh"),
    Path("experiments/ch14_predraft_validate.py"),
    Path("experiments/ch14-compute-engines-audit-2026-08-04.md"),
    Path("notes/chapter-14-framing-and-evidence-plan.md"),
    Path("notes/chapter-14-source-and-claim-ledger.md"),
    Path("references/foundations.md"),
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
foundations = frozen[input_rels[8]].decode()
for body in (report, framing, ledger):
    assert TITLE in body
    assert PIN in body
assert "experiments/runs/ch14-compute-engines/" in report
assert "run_ch14_compute_engines_audit.sh" in report
for phrase in ("Ranked scope candidates", "Reader decision",
               "Inclusions", "Exclusions", "Continuity trade-offs",
               "What this chapter must NOT claim"):
    assert phrase in framing
for status in ("verified", "qualified", "rejected", "blocked"):
    assert status in ledger
assert "C14.1" in ledger and "C14.30" in ledger
for phrase in (
    "SRAM access-width defect",
    "discards the read return",
    "include-only",
    "configured-but-ineffective",
    "never sum",
    "source-present-no-target",
):
    assert phrase in ledger or phrase in report, phrase

probe = frozen[input_rels[2]].decode()
for line in (
    "CH14_PROBE start",
    "CONV estimate_cycles=",
    "SOFTMAX census40 stall=",
    "SOFTMAX invalid=",
    "NORM census40 stall=",
    "EW census40 stall=",
    "POOL max ",
    "ATTN tiny rc=",
    "ATTN corrupt ",
    "ATTN diff golden_err=",
    "deviates=1 scales_equal=1",
    "PIPE depth1 sequential_total=",
    "PIPE depth2 sequential_total=",
    "CH14_PROBE SUMMARY failures=%d",
):
    assert line in probe, line

source_audit = frozen[input_rels[1]].decode()
for phrase in (
    '"tu_cmodel/compute/convolution_engine.c": "abaab2bf',
    '"tu_cmodel/compute/attention_engine.c": "73f291d8',
    '"tests/test_softmax.c": "f03990db',
    "attention-auto-tile",
    "norm-read-stall-discard",
    "reach-dpi-norm-include-only",
    "test-softmax must be standalone-only",
    "predicates={predicates} checks={checks}",
):
    assert phrase in source_audit, phrase

runner = frozen[input_rels[3]].decode()
for phrase in (
    '[[ ! -e "$RUN_DIR" ]]',
    '[[ -z "$(cat "$BOOK_STATUS_BEFORE")" ]]',
    'cp "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel"',
    "SOURCE_AUDIT_MUTATION PASS", "FOCUSED_TEST_MUTATION PASS",
    "ATTENTIONSUITEQUALIFIED PASS",
    'run timeout 90s "$WORK/ch14-probe"',
    "NEEDED.*libtucmodel", "hashes=28 predicates=46 checks=74",
    "sha256sum transcript.log >> sha256-retained.txt",
    "FINALIZED_RUN PASS", "predraft-validation.log", "bundle-sha256.txt",
    "CH14_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
    "remote_unchanged=yes no_push_performed=yes",
):
    assert phrase in runner, phrase
assert "make -C \\\"$WORK\\\" clean" not in runner

for gate in (
    f"CH14_SOURCE_AUDIT PASS pin={PIN} hashes=28 predicates=46 checks=74",
    "SOURCE_AUDIT_MUTATION PASS", "ARCHIVE_MEMBER PASS convolution_engine.o",
    "ARCHIVE_MEMBER PASS softmax_engine.o", "ARCHIVE_MEMBER PASS attention_engine.o",
    "ARCHIVE_MEMBER PASS normalization_engine.o", "ARCHIVE_MEMBER PASS pooling_engine.o",
    "ARCHIVE_MEMBER PASS elementwise_pipeline.o",
    "ARCHIVE_MEMBER PASS pipeline_controller.o",
    "STATIC_LINK_PASS ch14-probe", "STATIC_LINK_PASS ch14-test-elementwise",
    "STATIC_LINK_PASS ch14-test-normalization", "STATIC_LINK_PASS ch14-test-convolution",
    "STATIC_LINK_PASS ch14-test-attention", "STATIC_LINK_PASS ch14-test-pooling",
    "STATIC_LINK_PASS ch14-test-pipeline", "STATIC_LINK_PASS ch14-test-softmax",
    "16/16 tests passed", "11/11 tests passed", "12/12 tests passed",
    "14/14 tests passed", "Results: 11/11 passed",
    "ATTENTIONSUITEQUALIFIED PASS rc=1", "=== Results: 15/15 passed, 0 failed ===",
    "FOCUSED_TEST_MUTATION PASS",
    "CONV estimate_cycles=69",
    "SOFTMAX zeros 0.250000 0.250000 0.250000 0.250000 max=0.000000 stall=8",
    "SOFTMAX census40 stall=96", "SOFTMAX invalid=18446744073709551615",
    "NORM layernorm 0.000000 0.000000 0.000000 0.000000 mean=1.000000 var=0.000000 stall=8",
    "NORM rmsnorm 0.999995 0.999995 0.999995 0.999995 var=1.000000 stall=8",
    "NORM census40 stall=80",
    "EW chain 0.000000 3.000000 7.000000 stall=2", "EW census40 stall=40",
    "POOL max 6.000000 8.000000 14.000000 16.000000 cycles=18",
    "POOL avg 3.500000 5.500000 11.500000 13.500000 cycles=34",
    "ATTN tiny rc=0 out=0.099976 0.199951 dma=16 tiles=2 flops=8 cc=145 dc=2 tc=147 u=0.9864",
    "ATTN corrupt 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000",
    "ATTN diff golden_err=", "deviates=1 scales_equal=1",
    "PIPE depth1 sequential_total=204 saved=0 stalls=0",
    "PIPE depth2 sequential_total=402 saved=200 stalls=0 active=0",
    "CH14_PROBE SUMMARY failures=0", f"TUSIM_POST PASS head={PIN}",
    "ignored_inventory_unchanged=yes", "BOOK_POST PASS",
    "inputs_unchanged=yes status_unchanged_outside_run=yes remote_unchanged=yes no_push_performed=yes",
    "CH14_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
):
    assert gate in transcript, gate
assert "=== Results: 14/15 passed, 1 failed ===" in (RUN / "test-softmax-mutation.log").read_text()
assert "CH14_AUDIT PASS" not in transcript
for pattern in ("*.tar", "*.o", "core*"):
    assert not list(RUN.glob(pattern))
assert not (RUN / "worktree").exists()

subprocess.run(["sha256sum", "-c", "sha256-retained.txt"], cwd=RUN, check=True, stdout=subprocess.DEVNULL)
manifest_lines = (RUN / "sha256-retained.txt").read_text().splitlines()
manifest_members = {line.split(None, 1)[1] for line in manifest_lines}
expected_members = {f"inputs/{rel.as_posix()}" for rel in input_rels} | {
    "source-archive-sha256.txt", "source-audit.log", "source-audit-mutation.log",
    "archive-members.txt", "input-hashes.txt", "build.log", "test-elementwise.log",
    "test-normalization.log", "test-convolution.log", "test-attention.log",
    "test-pooling.log", "test-pipeline.log", "test-softmax.log",
    "test-softmax-mutation.log", "ch14-probe.log", "transcript.log",
}
assert manifest_members == expected_members, sorted(manifest_members ^ expected_members)
for rel in manifest_members:
    assert not rel.startswith(("/", "../")), rel

finalization = (RUN / "finalization.log").read_text()
m_final = re.search(r"FINALIZED_RUN PASS run_dir=(\S+) manifest=(\S+) transcript_sha256=([0-9a-f]{64})", finalization)
assert m_final
assert Path(m_final.group(1)).name == RUN_ID
assert Path(m_final.group(2)).name == "sha256-retained.txt"
assert Path(m_final.group(2)).parent.name == RUN_ID
transcript_digest = hashlib.sha256((RUN / "transcript.log").read_bytes()).hexdigest()
assert f"transcript_sha256={transcript_digest}" in finalization
assert "transcript.log: OK" in finalization

print(f"CH14_PREDRAFT_VALIDATION PASS files={len(input_rels)} run={RUN_REL} input_commit={input_commit}")
