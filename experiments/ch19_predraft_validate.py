#!/usr/bin/env python3
import ast
import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import NoReturn

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
RUN_ID = os.environ.get("CH19_RUN_ID", "20260810-ch19-postreview-v1")
STAGE = os.environ.get("CH19_VALIDATION_STAGE", "final")
ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "experiments/runs/ch19-static-transforms" / RUN_ID

INPUTS = {
    "PLAN.md",
    "style-guide.md",
    "edition.yaml",
    "fidelity-matrix.md",
    "source-audit.md",
    "manuscript/part-2-core/11-instruction-surfaces-and-command-queue-ordering.md",
    "notes/chapter-19-framing-and-evidence-plan.md",
    "notes/chapter-19-source-and-claim-ledger.md",
    "notes/chapter-19-skeptical-review-dispositions.md",
    "experiments/ch19_framing_reproduce.sh",
    "experiments/ch19_source_audit.py",
    "experiments/ch19_static_transform_probe.c",
    "experiments/ch19_ubsan_probe.c",
    "experiments/ch19_predraft_validate.py",
    "experiments/run_ch19_static_transform_audit.sh",
}
ARTIFACTS = {
    "artifacts/input-commit.txt",
    "artifacts/source-pin.txt",
    "artifacts/toolchain.txt",
    "artifacts/source-ignored-before.sha256",
    "artifacts/source-ignored-after.sha256",
    "artifacts/archive-members.txt",
    "artifacts/negative-control-status.txt",
    "artifacts/ubsan-status.txt",
}
LOGS = {
    "logs/01-source-audit.log",
    "logs/02-source-pin-control.log",
    "logs/03-source-hash-control.log",
    "logs/04-source-restored.log",
    "logs/05-build.log",
    "logs/06-focused-scheduler.log",
    "logs/07-focused-liveness.log",
    "logs/08-scheduler-sweep.log",
    "logs/09-focused-scheduler-readelf.log",
    "logs/10-focused-liveness-readelf.log",
    "logs/11-scheduler-sweep-readelf.log",
    "logs/12-static-transform-probe.log",
    "logs/13-ubsan-scheduler.log",
    "logs/14-ubsan-liveness.log",
    "logs/15-control-scheduler-suite.log",
    "logs/16-control-liveness-suite.log",
    "logs/17-control-scheduler-identity.log",
    "logs/18-control-liveness-opcode.log",
    "logs/19-control-spill-accounting.log",
    "logs/20-validator-control-normal.log",
    "logs/21-validator-control-optimized.log",
}


def fail(message: str) -> NoReturn:
    print("CH19_PREDRAFT_VALIDATION FAIL: " + message)
    raise SystemExit(1)


def need(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def text(path: Path) -> str:
    if not path.is_file():
        fail("missing " + str(path))
    return path.read_text(errors="replace")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_manifest(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text(path).splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            fail("malformed manifest line in " + path.name)
        rel = match.group(2)
        if rel.startswith("./"):
            rel = rel[2:]
        if rel in result:
            fail("duplicate manifest entry " + rel)
        result[rel] = match.group(1)
    return result


source = Path(__file__).read_text()
try:
    tree = ast.parse(source)
except SyntaxError as exc:
    fail("invalid validator source: " + str(exc))
need(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
     "optimizer-removable assertion in validator")
need(STAGE in {"pre", "final"}, "invalid validation stage")
need(RUN.is_dir(), "missing run directory " + str(RUN))

input_manifest = read_manifest(RUN / "INPUT_SHA256SUMS")
need(set(input_manifest) == INPUTS, "input manifest set mismatch")
for rel in sorted(INPUTS):
    retained = RUN / "inputs" / rel
    need(retained.is_file(), "missing retained input " + rel)
    need(digest(retained) == input_manifest[rel], "retained input hash mismatch " + rel)

commit = text(RUN / "artifacts/input-commit.txt").strip()
need(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "invalid input commit")
for rel in sorted(INPUTS):
    try:
        blob = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{commit}:{rel}"])
    except subprocess.CalledProcessError:
        fail("input absent from input commit " + rel)
    need(blob == (RUN / "inputs" / rel).read_bytes(), "input commit drift " + rel)
need(text(RUN / "artifacts/source-pin.txt").strip() == PIN, "source pin mismatch")
need(text(RUN / "artifacts/source-ignored-before.sha256") ==
     text(RUN / "artifacts/source-ignored-after.sha256"),
     "source ignored-file inventory changed")

body_manifest = read_manifest(RUN / "SHA256SUMS")
body_expected = ({"INPUT_SHA256SUMS", "REPORT.md"} | ARTIFACTS | LOGS |
                 {"inputs/" + rel for rel in INPUTS})
need(set(body_manifest) == body_expected, "body manifest set mismatch")
for rel, expected in body_manifest.items():
    path = RUN / rel
    need(path.is_file(), "missing retained body file " + rel)
    need(digest(path) == expected, "body hash mismatch " + rel)

source_log = text(RUN / "logs/01-source-audit.log")
need(f"CH19_SOURCE_AUDIT PASS pin={PIN} hashes=24 predicates=158 checks=182" in source_log,
     "source audit authority line")
need("CH19_SCHED_PUBLIC_APIS count=9" in source_log and
     "CH19_LIVE_PUBLIC_APIS count=7" in source_log and
     "CH19_CALLERS scheduler=none liveness=none" in source_log,
     "API or caller census")
need("CH19_SOURCE_AUDIT FAIL pin expected=" in text(RUN / "logs/02-source-pin-control.log"),
     "source pin control did not reject")
need("hash mismatch tu_cmodel/isa/tu_scheduler.c" in
     text(RUN / "logs/03-source-hash-control.log"),
     "source hash control did not reject")
need("CH19_SOURCE_AUDIT PASS" in text(RUN / "logs/04-source-restored.log"),
     "source audit did not recover")

archive_members = text(RUN / "artifacts/archive-members.txt")
need("tu_scheduler.o" in archive_members and "tu_liveness.o" in archive_members,
     "scheduler or liveness object absent from archive")
need("Results: 14/14 passed" in text(RUN / "logs/06-focused-scheduler.log"),
     "focused scheduler suite")
need("Results: 12/12 passed" in text(RUN / "logs/07-focused-liveness.log"),
     "focused liveness suite")
for rel in [
    "logs/09-focused-scheduler-readelf.log",
    "logs/10-focused-liveness-readelf.log",
    "logs/11-scheduler-sweep-readelf.log",
]:
    need("libtucmodel" not in text(RUN / rel), "dynamic libcmodel dependency " + rel)

probe = text(RUN / "logs/12-static-transform-probe.log")
need("CHECK_FAIL" not in probe and "CH19_PROBE SUMMARY failures=0" in probe,
     "static-transform probe summary")
for marker in [
    "SCHED_POLICY asap=NOP,DMA.LOAD alap=NOP,DMA.LOAD balanced=DMA.LOAD,NOP cycles=5/5/5",
    "SCHED_BARRIER_DIRECTION store_then_compute=1 compute_then_store=0",
    "SCHED_VALIDATE reversed_dependency accepted=1",
    "SCHED_FANOUT intended=17 producer_succs=16 last_preds=0 first=DMA.LOAD",
    "SCHED_VALIDATE unmatched accepted=1 graph_nodes=2 result_nodes=2",
    "CROSS_STRIDED sched_writes=0/1/0 live_vregs=2",
    "OPCODE_CENSUS_SUMMARY rows=128",
    "LIVE_VREG_LIMIT input_defs=129 rc=0 retained=128",
    "LIVE_CAP_UNDERFLOW capacity=16 margin=32 valid=1",
    "LIVE_NO_SPILL offsets=0,0 colored=1 spills=0",
    "LIVE_REBUILD nodes=2->4 matrix_replaced=1 edges=2",
    "LIVE_PROVENANCE rc=0 valid=1 opcode=RELU dim0=77",
    "LIVE_SPILL_ACCOUNTING spilled=1 num_spills=2 spill_bytes=32 colored=0 offset=4294967295",
    "LIVE_INVALID_ENUM alloc=99 offset=0 colored=1",
    "LIVE_OUTPUT_LIMIT input=301 rc=0 valid=1 output=512",
]:
    need(marker in probe, "missing probe marker " + marker)
need(len(re.findall(r"(?m)^OPCODE_CENSUS op=0x[0-9a-f]{2} ", probe)) == 128,
     "incomplete numeric opcode census")

for rel in ["logs/13-ubsan-scheduler.log", "logs/14-ubsan-liveness.log"]:
    need("runtime error: signed integer overflow" in text(RUN / rel),
         "missing bounded overflow observation " + rel)
status = text(RUN / "artifacts/negative-control-status.txt")
for name in [
    "scheduler_suite_rc", "liveness_suite_rc", "scheduler_identity_rc",
    "liveness_opcode_rc", "spill_accounting_rc",
]:
    match = re.search(rf"(?m)^{name}=([0-9]+)$", status)
    need(match is not None and int(match.group(1)) != 0, "control status " + name)
need("MUTATION empty should succeed" in text(RUN / "logs/15-control-scheduler-suite.log"),
     "scheduler suite control")
need("MUTATION empty should succeed" in text(RUN / "logs/16-control-liveness-suite.log"),
     "liveness suite control")
need("CHECK_FAIL weak identity accepts reversed dependency" in
     text(RUN / "logs/17-control-scheduler-identity.log"),
     "scheduler identity control")
need("CHECK_FAIL two W, repeated implicit A, O definitions" in
     text(RUN / "logs/18-control-liveness-opcode.log"),
     "liveness opcode control")
need("CHECK_FAIL one unplaced value is counted twice" in
     text(RUN / "logs/19-control-spill-accounting.log"),
     "spill accounting control")
for rel in ["logs/20-validator-control-normal.log", "logs/21-validator-control-optimized.log"]:
    need("CH19_PREDRAFT_VALIDATION FAIL: optimizer-removable assertion in validator" in
         text(RUN / rel), "validator control " + rel)

report = text(RUN / "REPORT.md")
need(RUN_ID in report and commit in report and
     "candidate post-review drafting authority" in report and
     "does not establish a composed compiler/runtime path" in report,
     "report identity or authority boundary")
manifest_check = text(RUN / "manifest-check.log").splitlines()
need(len(manifest_check) == len(body_manifest) and
     all(line.endswith(": OK") for line in manifest_check),
     "body manifest verification log")
finalization = text(RUN / "finalization.log").strip()
match = re.fullmatch(
    r"FINALIZED_RUN run=(\S+) input_commit=([0-9a-f]{40}) body_sha256=([0-9a-f]{64})",
    finalization,
)
need(match is not None and match.group(1) ==
     f"experiments/runs/ch19-static-transforms/{RUN_ID}" and
     match.group(2) == commit and match.group(3) == digest(RUN / "SHA256SUMS"),
     "finalization binding")
need(not list(RUN.rglob("*.o")) and not list(RUN.rglob("*.a")),
     "unretained build artifact")

if STAGE == "final":
    bundle_manifest = read_manifest(RUN / "BUNDLE_SHA256SUMS")
    bundle_expected = {
        "SHA256SUMS", "manifest-check.log", "finalization.log",
        "validator-normal.log", "validator-optimized.log",
    }
    need(set(bundle_manifest) == bundle_expected, "bundle manifest set mismatch")
    for rel, expected in bundle_manifest.items():
        need(digest(RUN / rel) == expected, "bundle hash mismatch " + rel)
    bundle_check = text(RUN / "bundle-check.log").splitlines()
    need(len(bundle_check) == len(bundle_manifest) and
         all(line.endswith(": OK") for line in bundle_check),
         "bundle verification log")
    actual = {str(path.relative_to(RUN)) for path in RUN.rglob("*") if path.is_file()}
    expected_actual = (body_expected | {
        "SHA256SUMS", "manifest-check.log", "finalization.log",
        "validator-normal.log", "validator-optimized.log",
        "BUNDLE_SHA256SUMS", "bundle-check.log",
    })
    need(actual == expected_actual, "exact run inventory mismatch")

print(
    "CH19_PREDRAFT_VALIDATION PASS "
    f"stage={STAGE} run=experiments/runs/ch19-static-transforms/{RUN_ID} "
    f"input_commit={commit} pin={PIN} inputs={len(INPUTS)} "
    f"body={len(body_manifest)} opcode_rows=128 source_checks=182"
)
