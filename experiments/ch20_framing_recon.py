#!/usr/bin/env python3
"""Chapter 20 framing-only whole-tree verification-surface reconnaissance.

Reads the detached pinned Tusim checkout, executes only in a disposable git
archive, and emits a deterministic-enough evidence inventory plus bounded live
results. It does not draft or seal Chapter 20 evidence.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
SOURCE = Path("/home/zxy/Workplace/projects/tusim")
KEY_FILES = [
    "Makefile",
    ".github/workflows/ci.yml",
    "tools/ci_runner.sh",
    "tools/test_report.py",
    "tests/test_framework.h",
    "tests/test_golden.c",
    "tests/test_random.c",
    "tests/test_debug.c",
    "tests/test_error_handling.c",
    "tests/test_dpi.c",
    "docs/differential-testing.md",
    "bindings/python/tu_bindings.py",
]


def run(cmd: list[str], cwd: Path, timeout: int = 240) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=timeout,
                       env={**os.environ, "LC_ALL": "C"})
    return p.returncode, p.stdout


def git_state(label: str) -> None:
    rc, out = run(["git", "status", "--porcelain=v1", "--branch"], SOURCE)
    if rc != 0:
        raise SystemExit(f"{label}: git status failed rc={rc}\n{out}")
    head = run(["git", "rev-parse", "HEAD"], SOURCE)[1].strip()
    branch_rc, branch = run(["git", "symbolic-ref", "-q", "--short", "HEAD"], SOURCE)
    lines = out.splitlines()
    dirty = lines[1:]
    detached = branch_rc != 0
    print(f"SOURCE_STATE {label} head={head} detached={int(detached)} dirty_entries={len(dirty)}")
    if head != PIN or not detached or dirty:
        raise SystemExit(f"unsafe source state at {label}: {out}")


def flatten_make(text: str) -> str:
    return text.replace("\\\n", " ")


def rule_map(make: str) -> dict[str, str]:
    flat = flatten_make(make)
    rules: dict[str, str] = {}
    for m in re.finditer(r"(?m)^([A-Za-z0-9_.-]+)\s*:\s*([^\n]*)$", flat):
        rules[m.group(1)] = m.group(2).strip()
    return rules


def deps(rules: dict[str, str], target: str) -> list[str]:
    return [x for x in rules.get(target, "").split() if x.startswith("test-")]


def normalize_output(text: str, archive: Path) -> str:
    text = text.replace(str(archive), "<ARCHIVE>")
    text = re.sub(r"summary_[0-9]{8}_[0-9]{6}\.md", "summary_<TIMESTAMP>.md", text)
    return text


def run_framing_recon() -> int:
    print(f"PIN {PIN}")
    print(f"SCRIPT_HASH {hashlib.sha256(Path(__file__).read_bytes()).hexdigest()} {Path(__file__).name}")
    for rel in KEY_FILES:
        data = (SOURCE / rel).read_bytes()
        print(f"HASH {hashlib.sha256(data).hexdigest()} {rel}")

    make = (SOURCE / "Makefile").read_text()
    ci = (SOURCE / "tools/ci_runner.sh").read_text()
    report = (SOURCE / "tools/test_report.py").read_text()
    debug = (SOURCE / "tests/test_debug.c").read_text()
    errors = (SOURCE / "tests/test_error_handling.c").read_text()
    binding = (SOURCE / "bindings/python/tu_bindings.py").read_text()
    rules = rule_map(make)

    test_sources = sorted((SOURCE / "tests").glob("test_*.c"))
    # This is intentionally a filename-token classification, not a semantic
    # claim: e.g. test_conv_pool_cascade.c describes itself as a sweep.
    sweep_token_sources = [p for p in test_sources if "sweep" in p.stem]
    no_sweep_token_sources = [p for p in test_sources if p not in sweep_token_sources]
    source_to_target: dict[str, list[str]] = {}
    for target, prerequisites in rules.items():
        for src in re.findall(r"tests/(test_[A-Za-z0-9_]+\.c)", prerequisites):
            source_to_target.setdefault(src, []).append(target)
    no_rule = [p.name for p in test_sources if p.name not in source_to_target]
    aggregate = deps(rules, "test")
    quick = deps(rules, "test-quick")
    agg_sources = {
        src for src, targets in source_to_target.items()
        if any(t in aggregate for t in targets)
    }
    omitted_no_sweep_token = [p.name for p in no_sweep_token_sources if p.name not in agg_sources]

    ci_quick_block = re.search(r'if \[ "\$QUICK_MODE" = true \]; then\s*TEST_TARGETS=\((.*?)\)\s*else', ci, re.S)
    ci_full_block = re.search(r'else\s*TEST_TARGETS=\((.*?)\)\s*fi', ci, re.S)
    ci_quick = re.findall(r'"(test-[A-Za-z0-9-]+):', ci_quick_block.group(1)) if ci_quick_block else []
    ci_full = re.findall(r'"(test-[A-Za-z0-9-]+):', ci_full_block.group(1)) if ci_full_block else []

    print(f"INVENTORY test_c_sources={len(test_sources)} no_sweep_token={len(no_sweep_token_sources)} sweep_token={len(sweep_token_sources)} make_source_rules={len(source_to_target)} aggregate_deps={len(aggregate)} quick_deps={len(quick)}")
    print("AGGREGATE " + " ".join(aggregate))
    print("QUICK " + " ".join(quick))
    print("NO_SOURCE_LINKED_RULE " + (" ".join(no_rule) if no_rule else "none"))
    print("NO_SWEEP_TOKEN_OMITTED_FROM_AGGREGATE " + " ".join(omitted_no_sweep_token))
    print(f"CI_TARGETS quick={len(ci_quick)} full={len(ci_full)}")
    print("CI_QUICK " + " ".join(ci_quick))
    print("CI_FULL " + " ".join(ci_full))

    expected_no_rule = [
        "test_asm.c", "test_cycle_model.c", "test_double_buffer.c",
        "test_int8_sweep.c", "test_softmax.c",
    ]
    expected_omitted_no_sweep_token = [
        "test_asm.c", "test_benchmark.c", "test_compress.c", "test_context.c",
        "test_conv_pool_cascade.c", "test_cycle_model.c", "test_debug.c",
        "test_double_buffer.c", "test_error_handling.c", "test_power_model.c",
        "test_random.c", "test_softmax.c", "test_tf32.c",
    ]
    expected_ci_quick = ["test-cmodel", "test-cmdq", "test-dma", "test-golden"]
    expected_ci_full = [
        "test-cmodel", "test-cmdq", "test-dma", "test-dram", "test-isa",
        "test-golden", "test-elementwise", "test-bf16", "test-memhier",
        "test-norm", "test-dataflow", "test-logging", "test-int-quant", "test-conv",
    ]

    predicates = {
        "inventory_test_sources_exact": len(test_sources) == 64,
        "inventory_filename_partition_exact": len(no_sweep_token_sources) == 43 and len(sweep_token_sources) == 21,
        "inventory_source_linked_rules_exact": len(source_to_target) == 59,
        "inventory_aggregate_and_quick_exact": len(aggregate) == 31 and len(quick) == 4,
        "inventory_unlinked_sources_exact": no_rule == expected_no_rule,
        "inventory_no_sweep_token_omissions_exact": omitted_no_sweep_token == expected_omitted_no_sweep_token,
        "inventory_ci_lists_exact": ci_quick == expected_ci_quick and ci_full == expected_ci_full,
        "make_full_suppresses_compile": "/tmp/gpt_block_tu.c" in make and "2>&1 || true" in make,
        "make_full_suppresses_run": "/tmp/gpt_block_tu 2>&1 || true" in make,
        "make_fixed_host_global_tmp_surfaces": (
            "-o /tmp/test_asm" in make
            and "-o /tmp/gpt_block_tu.c" in make
            and "rm -f /tmp/gpt_block_tu /tmp/gpt_block_tu.c /tmp/test_asm" in make
        ),
        "ci_report_dir_created_before_clean": ci.index('mkdir -p "$REPORT_DIR" "$LOG_DIR"') < ci.index("make clean"),
        "clean_removes_ci_report_dir": "rm -rf build/ci_reports" in make,
        "ci_quick_golden_discards_status": 'test-golden > "$local_log" 2>&1 || true' in ci,
        "ci_quick_golden_accepts_pass_substring": 'grep -q "PASS" "$local_log"' in ci,
        "ci_coverage_unconditional_pass_after_suppression": 'gcov -r tu_cmodel/*.c tu_cmodel/*/*.c > "$LOG_DIR/coverage.log" 2>&1 || true' in ci and 'record_result "Coverage report" "PASS"' in ci,
        "report_never_receives_exit_code": '"exit_code": -1' in report and 'result["exit_code"] =' not in report,
        "report_tail_pass_precedes_any_fail": 'if "PASS" in content[-200:] or "passed" in content[-200:].lower()' in report,
        "debug_unsigned_nonnegative_tautology": debug.count('CHECK(n >= 0, "dump returned negative")') == 2,
        "debug_checksum_tautology": 'CHECK(cs != 0 || cs == 0' in debug,
        "error_injection_test_never_requires_injection": "this won't match" in errors and "tu_error_inject_disable_all();" in errors,
        "python_binding_has_no_make_rule": "test-python" not in rules,
        "python_binding_claims_full_api_but_has_stubs": "exposes the full TU core API" in binding and "For now, return stub" in binding,
    }
    for name, ok in predicates.items():
        print(f"PREDICATE {name}={'PASS' if ok else 'FAIL'}")
    if not all(predicates.values()):
        return 2

    with tempfile.TemporaryDirectory(prefix="ch20-framing-") as td:
        archive = Path(td) / "src"
        archive.mkdir()
        tar_path = Path(td) / "tusim.tar"
        with tar_path.open("wb") as f:
            p = subprocess.run(["git", "archive", "--format=tar", PIN], cwd=SOURCE, stdout=f)
        if p.returncode:
            raise SystemExit("git archive failed")
        rc, out = run(["tar", "-xf", str(tar_path), "-C", str(archive)], SOURCE)
        if rc:
            raise SystemExit(f"archive extraction failed: {out}")
        print(f"ARCHIVE disposable=yes source_pin={PIN}")

        commands = [
            ("build_libs", ["make", "-j2", "all", "libtucmodel.so"], 300),
            # Do not invoke test-quick: its test-asm prerequisite uses a fixed
            # /tmp/test_asm path. Exercise its three archive-local C targets;
            # retain test-asm only as static inventory evidence.
            ("quick_archive_local", ["make", "test-cmodel", "test-cmdq", "test-dma"], 300),
            ("test_debug", ["make", "test-debug"], 300),
            ("test_errors", ["make", "test-errors"], 300),
            ("test_dpi", ["make", "test-dpi"], 300),
            ("test_random_buildrun", ["make", "test-random"], 600),
        ]
        results: dict[str, tuple[int, str]] = {}
        for label, cmd, timeout in commands:
            if cmd[0] == "make":
                dry_cmd = ["make", "-n", *cmd[1:]]
                dry_rc, dry_out = run(dry_cmd, cwd=archive, timeout=timeout)
                unsafe = "/tmp/" in dry_out or "rm -f /tmp" in dry_out
                print(f"DRY_RUN {label} rc={dry_rc} host_global_tmp={int(unsafe)}")
                if dry_rc != 0 or unsafe:
                    return 3
            rc, out = run(cmd, cwd=archive, timeout=timeout)
            results[label] = (rc, out)
            tail = " | ".join(normalize_output(out, archive).splitlines()[-8:])
            print(f"EXEC {label} rc={rc} tail={tail}")

        # Exercise the report parser against a log whose last line says PASS
        # after an earlier failure; process status is not part of its schema.
        synthetic = archive / "synthetic-fail-then-pass.log"
        synthetic.write_text("  case_a  FAIL\ncleanup PASS\n")
        import importlib.util
        spec = importlib.util.spec_from_file_location("ch20_test_report", archive / "tools/test_report.py")
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load disposable test_report.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        parsed = module.parse_test_log(str(synthetic))
        print(f"EXEC report_fail_then_pass status={parsed['status']} failed={parsed['failed']} exit_code={parsed['exit_code']}")

        # Exercise the binding below its self-reported CLI PASS marker. Use a
        # nonsymmetric matrix pair and independently recompute every output.
        binding_spec = importlib.util.spec_from_file_location(
            "ch20_tu_bindings", archive / "bindings/python/tu_bindings.py"
        )
        if binding_spec is None or binding_spec.loader is None:
            raise RuntimeError("cannot load disposable tu_bindings.py")
        binding_module = importlib.util.module_from_spec(binding_spec)
        prior_cwd = Path.cwd()
        try:
            os.chdir(archive)
            binding_spec.loader.exec_module(binding_module)
            a = [[1.0, 2.0], [3.0, 4.0]]
            b = [[5.0, 6.0], [7.0, 8.0]]
            observed = binding_module.quick_gemm(a, b)
        finally:
            os.chdir(prior_cwd)
        expected = [[19.0, 22.0], [43.0, 50.0]]
        binding_shape_ok = len(observed) == 2 and all(len(row) == 2 for row in observed)
        binding_max_abs = (
            max(abs(observed[i][j] - expected[i][j]) for i in range(2) for j in range(2))
            if binding_shape_ok else float("inf")
        )
        print(f"EXEC binding_nonsymmetric shape_ok={int(binding_shape_ok)} max_abs={binding_max_abs:.9g}")

        # Exact bounded live observations. The aggregate test-quick, test-full,
        # ci_runner, and clean paths are intentionally static-only because their
        # pinned recipes use or delete fixed host-global /tmp names.
        live = {
            "build_green": results["build_libs"][0] == 0,
            "quick_archive_local_green": results["quick_archive_local"][0] == 0,
            "debug_green": results["test_debug"][0] == 0 and "25/25 passed" in results["test_debug"][1],
            "errors_green": results["test_errors"][0] == 0 and "9/9 passed" in results["test_errors"][1],
            "dpi_green": results["test_dpi"][0] == 0 and "13 passed, 0 failed" in results["test_dpi"][1],
            "random_green": results["test_random_buildrun"][0] == 0 and "9/9 tests passed" in results["test_random_buildrun"][1],
            "binding_nonsymmetric_discriminator_green": binding_shape_ok and binding_max_abs <= 1e-6,
            "report_fail_then_pass_is_green": parsed["status"] == "PASS" and parsed["exit_code"] == -1,
        }
        for name, ok in live.items():
            print(f"LIVE_GATE {name}={'PASS' if ok else 'FAIL'}")
        if not all(live.values()):
            return 3

    return 0


def main() -> int:
    git_state("before")
    try:
        rc = run_framing_recon()
    finally:
        git_state("after")
    if rc == 0:
        print("CH20_FRAMING_RECON PASS")
    return rc


if __name__ == "__main__":
    sys.exit(main())
