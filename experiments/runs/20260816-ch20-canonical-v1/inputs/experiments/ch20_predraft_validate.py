#!/usr/bin/env python3
"""Fail-closed validator for the Chapter 20 predraft evidence bundle."""
from __future__ import annotations
import ast
import hashlib
import os
from pathlib import Path
import subprocess
import sys

BOOK = Path(__file__).resolve().parents[1]
DEFAULT_RUN = "20260816-ch20-canonical-v1"
INPUTS = [
    "edition.yaml",
    "notes/chapter-20-framing-and-evidence-plan.md",
    "notes/chapter-20-framing-review-dispositions.md",
    "notes/chapter-20-source-and-claim-ledger.md",
    "notes/chapter-20-predraft-audit-report.md",
    "experiments/ch20_source_audit.py",
    "experiments/ch20_claim_authorization_probe.c",
    "experiments/ch20_boundary_checks.py",
    "experiments/run_ch20_claim_authorization_audit.sh",
    "experiments/ch20_predraft_validate.py",
]
GATES = [
    "CH20_SOURCE_AUDIT PASS pin=e918c80b6fce833cd1fcae97730fa841c2176f25 hashes=19 predicates=37 checks=57",
    "SOURCE_AUDIT_MUTATION rejected_rc=1 restored=PASS",
    "PROBE_OPT_STABILITY byte_identical=1",
    "PROBE_SANITIZERS address_undefined=PASS leak_check=excluded_global_singleton",
    "DEBUG_MUTATION meaningful_size_gate_rejected_rc=1",
    "ERROR_INJECTION_MUTATION reached_requirement_rejected_rc=1",
    "GOLDEN_MUTATION independent_equation_rejected_rc=1",
    "REPORT_FALSE_GREEN status=PASS passed=0 failed=1 exit_code=-1",
    "CH20_BOUNDARY_CHECKS PASS",
    "BOUNDARY_MUTATION expected_value_rejected_rc=4",
    "BOOK_INPUTS unchanged=1 head=",
]
PROBE_LINES = [
    "ORACLE_NAN shared_accept=1 strict_accept=0 shared_pass=1 shared_fail=0",
    "CONFIG_EFFECT parse_rc=0 parsed_df=1 rt_rows=8 rt_cols=4 active=weight_stationary",
    "DUMP_SIZE reported=0 actual=338",
    "REPLAY_NOOP arbitrary_opcode=0xFE mismatches_equal=0 mismatches_mutated=1 output_bytes=69",
    "BOUNDS_WRAP wrapped_accept=1 ordinary_accept=0",
    "CH20_PROBE SUMMARY failures=0",
]


def fail(message: str) -> None:
    print(f"CH20_PREDRAFT_VALIDATION FAIL {message}")
    raise SystemExit(1)


def need(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_show(commit: str, rel: str) -> bytes:
    p = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=BOOK, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    need(p.returncode == 0, f"git-show:{rel}")
    return p.stdout


def parse_manifest(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text().splitlines():
        digest, rel = line.split("  ", 1)
        need(rel not in result, f"duplicate-manifest:{rel}")
        result[rel] = digest
    return result


def main() -> int:
    tree = ast.parse(Path(__file__).read_text())
    if any(isinstance(node, ast.Assert) for node in ast.walk(tree)):
        fail("validator-contains-assert")

    args = set(sys.argv[1:])
    need(args <= {"--body", "--outer"}, "arguments")
    need(not ({"--body", "--outer"} <= args), "incompatible-modes")
    body_only = "--body" in args
    outer = "--outer" in args
    run_id = os.environ.get("CH20_RUN_ID", DEFAULT_RUN)
    run = BOOK / "experiments" / "runs" / run_id
    need(run.is_dir(), "run-missing")
    input_commit = (run / "input_commit").read_text().strip()
    need(len(input_commit) == 40, "input-commit")
    need((run / "source_pin").read_text().strip() == "e918c80b6fce833cd1fcae97730fa841c2176f25", "source-pin")

    expected_hash_lines = []
    for rel in INPUTS:
        frozen = run / "inputs" / rel
        need(frozen.is_file(), f"frozen-input:{rel}")
        committed = git_show(input_commit, rel)
        need(frozen.read_bytes() == committed, f"frozen-vs-commit:{rel}")
        expected_hash_lines.append(f"{hashlib.sha256(committed).hexdigest()}  {rel}")
    need((run / "input-hashes.txt").read_text().splitlines() == expected_hash_lines, "input-hashes")

    transcript = (run / "transcript.log").read_text()
    for gate in GATES:
        need(gate in transcript, f"transcript-gate:{gate}")
    need("CH20_AUDIT PASS" not in transcript, "forbidden-whole-audit-pass")
    probe = (run / "probe-O0.log").read_text()
    need(probe == (run / "probe-O2.log").read_text(), "probe-opt-drift")
    for line in PROBE_LINES:
        need(line in probe, f"probe-line:{line}")
    need("=== Results: 25/25 passed, 0 failed ===" in (run / "test-debug.log").read_text(), "debug-positive")
    need("=== Results: 23/25 passed, 2 failed ===" in (run / "test-debug-mutation.log").read_text(), "debug-mutation")
    need("=== Results: 9/9 passed, 0 failed ===" in (run / "test-errors.log").read_text(), "errors-positive")
    need("=== Results: 8/9 passed, 1 failed ===" in (run / "test-errors-mutation.log").read_text(), "errors-mutation")
    need("  11/11 tests passed" in (run / "test-golden.log").read_text(), "golden-positive")
    need("  2/11 tests passed" in (run / "test-golden-mutation.log").read_text(), "golden-mutation")
    need("CH20_BOUNDARY_CHECKS REJECT" in (run / "boundary-checks-mutation.log").read_text(), "boundary-mutation")
    need("CH20_BOUNDARY_CHECKS PASS" not in (run / "boundary-checks-mutation.log").read_text(), "boundary-mutation-pass")
    forbidden = [p for p in run.rglob("*") if p.is_file() and (p.suffix in {".tar", ".o"} or p.name.startswith("core"))]
    need(not forbidden, "forbidden-artifacts")

    if body_only:
        print(f"CH20_PREDRAFT_BODY_VALIDATION PASS run={run_id} input_commit={input_commit}")
        return 0

    retained_list = (run / "retained-files.txt").read_text().splitlines()
    need(retained_list == sorted(retained_list), "retained-order")
    inner = parse_manifest(run / "sha256-retained.txt")
    need(set(inner) == set(retained_list) | {"retained-files.txt"}, "inner-member-set")
    for rel, digest in inner.items():
        need(sha(run / rel) == digest, f"inner-hash:{rel}")
    check_lines = (run / "manifest-check.log").read_text().splitlines()
    need(len(check_lines) == len(inner) and all(line.endswith(": OK") for line in check_lines), "inner-check")
    final = (run / "finalization.log").read_text().strip()
    need(f"run={run_id}" in final and f"input_commit={input_commit}" in final, "finalization-fields")
    need(f"transcript_sha256={sha(run / 'transcript.log')}" in final, "finalization-transcript")

    if outer:
        bundle = parse_manifest(run / "bundle-sha256.txt")
        need(set(bundle) == {"sha256-retained.txt", "manifest-check.log", "finalization.log", "predraft-validation.log"}, "bundle-member-set")
        for rel, digest in bundle.items():
            need(sha(run / rel) == digest, f"bundle-hash:{rel}")
        bundle_check = (run / "bundle-check.log").read_text().splitlines()
        need(len(bundle_check) == 4 and all(line.endswith(": OK") for line in bundle_check), "bundle-check")
        need(f"CH20_PREDRAFT_VALIDATION PASS run={run_id} input_commit={input_commit} outer=0" in (run / "predraft-validation.log").read_text(), "preouter-log")
    print(f"CH20_PREDRAFT_VALIDATION PASS run={run_id} input_commit={input_commit} outer={int(outer)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
