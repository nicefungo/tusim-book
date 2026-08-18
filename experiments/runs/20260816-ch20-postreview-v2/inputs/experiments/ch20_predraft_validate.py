#!/usr/bin/env python3
"""Fail-closed validator for the Chapter 20 post-review predraft bundle."""
from __future__ import annotations
import ast
import hashlib
import os
from pathlib import Path
import subprocess
import sys

BOOK = Path(__file__).resolve().parents[1]
DEFAULT_RUN = "20260816-ch20-postreview-v2"
INPUTS = [
    "edition.yaml",
    "notes/chapter-20-framing-and-evidence-plan.md",
    "notes/chapter-20-framing-review-dispositions.md",
    "notes/chapter-20-source-and-claim-ledger.md",
    "notes/chapter-20-predraft-audit-report.md",
    "notes/chapter-20-skeptical-predraft-review-dispositions.md",
    "experiments/ch20_source_audit.py",
    "experiments/ch20_claim_authorization_probe.c",
    "experiments/ch20_boundary_checks.py",
    "experiments/run_ch20_claim_authorization_audit.sh",
    "experiments/ch20_predraft_validate.py",
]
GATES = [
    "CH20_SOURCE_AUDIT PASS pin=e918c80b6fce833cd1fcae97730fa841c2176f25 hashes=22 predicates=52 checks=75",
    "FAILURE_PATH_CONTROL rejected_rc=1 survived=0 source_after=PASS",
    "MEMBERSHIP_SET_MUTATION count_preserved=31 rejected_rc=1",
    "RANDOM_CENSUS_MUTATION seed_42_to_43 rejected_rc=1",
    "SOURCE_AUDIT_MUTATIONS hash_rc=1 membership_rc=1 random_rc=1 restored=PASS",
    "DRY_RUN_BOUNDARY selected=libtucmodel.a fixed_tmp=0 forbidden=test-asm,test-full,test-compiler,clean executed=0",
    "CI_FALLBACK_SYNTHETIC producer_rc=1 propagated_rc=0 unsafe_green=1",
    "PROBE_OPT_STABILITY byte_identical=1",
    "CONFIG_CONSUMER_MUTATION force_os rejected_rc=1",
    "PROBE_SANITIZERS archive_and_probe_address_undefined=PASS leak_check=excluded_global_singleton",
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
    "CONFIG_AB ws_parse=0 os_parse=0 ws_df=0 os_df=1 rt_rows=8 rt_cols=4 ws_active=weight_stationary os_active=weight_stationary direct_os=output_stationary",
    "CORE_REINIT_GEOMETRY created_8x4=1 reinitialized_16x16=1 created_bytes=336 reinitialized_bytes=338",
    "DUMP_SIZE fixture=post_reinit_16x16 reported=0 actual=338",
    "REPLAY_NOOP arbitrary_opcode=0xFE mismatches_equal=0 mismatches_mutated=1 output_bytes=69",
    "BOUNDS_WRAP wrapped_accept=1 ordinary_accept=0",
    "TILE_PE_IGNORED oversized_accept=1 zero_reject=1",
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


def run_git(args: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=BOOK, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def git_show(commit: str, rel: str) -> bytes:
    p = run_git(["show", f"{commit}:{rel}"])
    need(p.returncode == 0, f"git-show:{rel}")
    return p.stdout


def parse_manifest(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text().splitlines():
        parts = line.split("  ", 1)
        need(len(parts) == 2, f"manifest-line:{path.name}")
        digest, rel = parts
        need(rel not in result, f"duplicate-manifest:{rel}")
        result[rel] = digest
    return result


def validate_seal(run: Path, run_id: str, input_commit: str, seal: str) -> int:
    need(len(seal) == 40, "seal-oid-length")
    kind = run_git(["cat-file", "-t", seal])
    need(kind.returncode == 0 and kind.stdout.strip() == b"commit", "seal-oid-type")
    parent = run_git(["rev-parse", f"{seal}^1"])
    need(parent.returncode == 0 and parent.stdout.decode().strip() == input_commit, "seal-first-parent")
    changed = run_git(["diff-tree", "--no-commit-id", "--name-only", "-r", seal])
    need(changed.returncode == 0, "seal-diff-tree")
    paths = [line for line in changed.stdout.decode().splitlines() if line]
    prefix = f"experiments/runs/{run_id}/"
    need(bool(paths) and all(path.startswith(prefix) for path in paths), "seal-changed-path-scope")
    committed = run_git(["ls-tree", "-r", "--name-only", seal, prefix])
    need(committed.returncode == 0, "seal-run-tree")
    committed_paths = sorted(line[len(prefix):] for line in committed.stdout.decode().splitlines())
    live_paths = sorted(path.relative_to(run).as_posix() for path in run.rglob("*") if path.is_file())
    need(committed_paths == live_paths, "seal-run-member-set")
    for rel in live_paths:
        need(git_show(seal, prefix + rel) == (run / rel).read_bytes(), f"seal-run-blob:{rel}")
    print(f"CH20_POSTSEAL_VALIDATION PASS run={run_id} input_commit={input_commit} sealed_at_book_commit={seal}")
    return 0


def main() -> int:
    tree = ast.parse(Path(__file__).read_text())
    if any(isinstance(node, ast.Assert) for node in ast.walk(tree)):
        fail("validator-contains-assert")

    args = sys.argv[1:]
    body_only = args == ["--body"]
    outer = args == ["--outer"]
    seal_mode = len(args) == 2 and args[0] == "--sealed-at"
    need(not args or body_only or outer or seal_mode, "arguments")
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
    failure_control = (run / "failure-path-control.log").read_text()
    need(failure_control.count("SOURCE_STATE after ") == 1, "failure-control-after-count")
    need("SURVIVED_AFTER_FAILED_GATE" not in failure_control, "failure-control-survivor")
    need("CH20_PROBE SUMMARY failures=0" not in (run / "config-consumer-mutation.log").read_text(), "config-mutation-pass")
    need("inventory-exact-31-aggregate=FAIL" in (run / "source-audit-membership-mutation.log").read_text(), "membership-mutation")
    need("random-exact-fixed-seeds=FAIL" in (run / "source-audit-random-mutation.log").read_text(), "random-mutation")
    need("-fsanitize=address,undefined -c" in (run / "build-sanitized.log").read_text(), "sanitized-archive")
    need("/tmp/test_asm" in (run / "make-dry-run-forbidden.log").read_text(), "dry-run-forbidden")
    selected_lines = [line for line in (run / "make-dry-run-selected.log").read_text().splitlines() if not line.startswith("make: ")]
    need(not any("/tmp/" in line for line in selected_lines), "dry-run-selected")
    forbidden = [p for p in run.rglob("*") if p.is_file() and (p.suffix in {".tar", ".o"} or p.name.startswith("core"))]
    need(not forbidden, "forbidden-artifacts")

    if seal_mode:
        return validate_seal(run, run_id, input_commit, args[1])
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
    need("trust=inner-manifest,outer-root,derived-checks,git-seal" in final, "trust-hierarchy")

    if outer:
        bundle = parse_manifest(run / "bundle-sha256.txt")
        expected_bundle = {"sha256-retained.txt", "manifest-check.log", "finalization.log", "predraft-validation-normal.log", "predraft-validation-optimized.log"}
        need(set(bundle) == expected_bundle, "bundle-member-set")
        for rel, digest in bundle.items():
            need(sha(run / rel) == digest, f"bundle-hash:{rel}")
        bundle_check = (run / "bundle-check.log").read_text().splitlines()
        need(len(bundle_check) == len(expected_bundle) and all(line.endswith(": OK") for line in bundle_check), "bundle-check")
        normal = (run / "predraft-validation-normal.log").read_text()
        optimized = (run / "predraft-validation-optimized.log").read_text()
        expected = f"CH20_PREDRAFT_VALIDATION PASS run={run_id} input_commit={input_commit} outer=0"
        need(expected in normal and normal == optimized, "preouter-logs")
    print(f"CH20_PREDRAFT_VALIDATION PASS run={run_id} input_commit={input_commit} outer={int(outer)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
