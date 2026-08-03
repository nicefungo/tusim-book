#!/usr/bin/env python3
"""Fail-closed validation for a frozen Chapter 13 pre-draft evidence bundle."""
from __future__ import annotations

from pathlib import Path
import hashlib
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
TITLE = "Weight Streams: Quantization, Structured Sparsity, and Compression"
RUN_ID = os.environ.get("CH13_RUN_ID", "20260803-ch13-canonical")
RUN_REL = Path("experiments/runs/ch13-weight-streams") / RUN_ID
RUN = ROOT / RUN_REL

input_rels = [
    Path("edition.yaml"),
    Path("experiments/ch13_source_audit.py"),
    Path("experiments/ch13_weight_stream_probe.c"),
    Path("experiments/run_ch13_weight_stream_audit.sh"),
    Path("experiments/ch13_predraft_validate.py"),
    Path("experiments/ch13-weight-streams-audit-2026-08-03.md"),
    Path("notes/chapter-13-framing-and-evidence-plan.md"),
    Path("notes/chapter-13-source-and-claim-ledger.md"),
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
assert "experiments/runs/ch13-weight-streams/" in report
assert "run_ch13_weight_stream_audit.sh" in report
for phrase in ("Ranked candidate boundaries", "Independent scope-panel disposition",
               "Reader decision", "Explicitly deferred"):
    assert phrase in framing
for status in ("verified", "qualified", "rejected", "blocked"):
    assert status in ledger
assert "C13.1" in ledger and "C13.36" in ledger
for phrase in (
    "tu_config_to_runtime() drops every compression and sparsity field",
    "decoder-bound",
    "raw wins ties",
    "not an integrated pipeline",
    "analytical estimate",
    "source-present with no Makefile target",
):
    assert phrase in ledger or phrase in report, phrase
for key in ("[KWO19]", "[PAR19]", "[CHE16]", "[GEN21]", "[JOU17]"):
    assert key in foundations

probe = frozen[input_rels[2]].decode()
for line in (
    "CH13_WEIGHT_STREAM_PROBE start",
    "SPARSITY est128 dense_total=",
    "SPARSITY estNarrow dense_total=34307 sparse_total=77312",
    "COMPRESS est_rle dma=",
    "COMPRESS est_serial total=",
    "CONFIG parsed compression=",
    "CONFIG validation rejections=4",
    "CH13_PROBE SUMMARY failures=%d",
):
    assert line in probe, line
assert "tu_config_to_runtime(&cfg)" in probe
assert "pthread_" not in probe
assert "UINT32_MAX" not in probe

source_audit = frozen[input_rels[1]].decode()
for phrase in (
    '"tu_cmodel/memory/weight_compress.c": "26fa554d',
    '"tu_cmodel/sparsity/structured_2of4.c": "4111f843',
    '"tu_cmodel/tu_int_quant.c": "7b20c382',
    "runtime-converter-drops-compression_enabled",
    "runtime-converter-drops-sparsity_2of4",
    "yaml-omits-weight-compression-block",
    "no-makefile-target-for-int8-sweep",
    "aggregate-excludes-compress",
    "direct-mma-avoids-tu_compress_",
    "predicates={PREDICATES}",
):
    assert phrase in source_audit, phrase

runner = frozen[input_rels[3]].decode()
for phrase in (
    '[[ ! -e "$RUN_DIR" ]]',
    '[[ -z "$(cat "$BOOK_STATUS_BEFORE")" ]]',
    'cp "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel"',
    "SOURCE_AUDIT_MUTATION PASS", "FOCUSED_TEST_MUTATION PASS",
    'run timeout 90s "$WORK/ch13-probe"',
    "NEEDED.*libtucmodel", "predicates=138 checks=163",
    "sha256sum transcript.log >> sha256-retained.txt",
    "FINALIZED_RUN PASS", "predraft-validation.log", "bundle-sha256.txt",
    "CH13_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
    "remote_unchanged=yes no_push_performed=yes",
):
    assert phrase in runner, phrase
assert "make -C \"$WORK\" clean" not in runner

for gate in (
    f"CH13_SOURCE_AUDIT PASS pin={PIN} hashes=25 predicates=138 checks=163",
    "SOURCE_AUDIT_MUTATION PASS", "ARCHIVE_MEMBER PASS tu_int_quant.o",
    "ARCHIVE_MEMBER PASS structured_2of4.o",
    "ARCHIVE_MEMBER PASS weight_compress.o",
    "STATIC_LINK_PASS ch13-probe", "STATIC_LINK_PASS ch13-test-int-quant",
    "14/14 tests passed", "Tests: 27 run, 27 passed, 0 failed",
    "24/24 tests passed", "FOCUSED_TEST_MUTATION PASS",
    "Tests: 26 run, 25 passed, 1 failed",
    "SPARSITY est128 dense_total=12291 sparse_total=7811 selected=7811 macs=2097152/1048576 wbytes=32768/20480 decode=4096",
    "SPARSITY estNarrow dense_total=34307 sparse_total=77312 decode=65536",
    "SPARSITY estWide sparse_total=19971 decode=4096",
    "COMPRESS rle_allzero_size=14", "COMPRESS rle_alt_size=776 raw=256",
    "COMPRESS bitmap_size=110 nnz=43", "COMPRESS adaptive_sparse_codec=2 size=126",
    "COMPRESS corrupt_rejected=1",
    "COMPRESS est_rle dma=1 decode=128 total=128 bound=1",
    "COMPRESS est_wide decode=8 total=8", "COMPRESS est_serial total=9",
    "CONFIG parsed compression=1 type=4 decoder=1 sparsity=1 two4=1 decgroups=4",
    "CONFIG validation rejections=4",
    "CONFIG runtime pe_rows=16 pe_cols=16 dma_bits=256",
    "CH13_PROBE SUMMARY failures=0", f"TUSIM_POST PASS head={PIN}",
    "ignored_inventory_unchanged=yes", "BOOK_POST PASS",
    "inputs_unchanged=yes status_unchanged_outside_run=yes remote_unchanged=yes no_push_performed=yes",
    "CH13_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS",
):
    assert gate in transcript, gate
assert "CH13_AUDIT PASS" not in transcript
for pattern in ("*.tar", "*.o", "core*"):
    assert not list(RUN.glob(pattern))
assert not (RUN / "worktree").exists()

subprocess.run(["sha256sum", "-c", "sha256-retained.txt"], cwd=RUN, check=True, stdout=subprocess.DEVNULL)
manifest_lines = (RUN / "sha256-retained.txt").read_text().splitlines()
manifest_members = {line.split(None, 1)[1] for line in manifest_lines}
expected_members = {f"inputs/{rel.as_posix()}" for rel in input_rels} | {
    "source-archive-sha256.txt", "source-audit.log", "source-audit-mutation.log",
    "archive-members.txt", "input-hashes.txt", "build.log", "test-int-quant.log",
    "test-sparsity.log", "test-compress.log", "test-sparsity-mutation.log",
    "weight-sweep.log", "sparsity-sweep.log", "ch13-probe.log", "transcript.log",
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

print(f"CH13_PREDRAFT_VALIDATION PASS files={len(input_rels)} run={RUN_REL} input_commit={input_commit}")
