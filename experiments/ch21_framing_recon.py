#!/usr/bin/env python3
"""Chapter 21 framing-only reconnaissance of Tusim sweep surfaces.

The pinned checkout is read-only. Static inventory reads it directly; every
build and execution occurs in a disposable git archive. This script frames the
chapter and does not constitute the later predraft evidence seal.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
SOURCE = Path("/home/zxy/Workplace/projects/tusim")
SWEEP_TARGETS = [
    "test-attention-sweep",
    "test-context-switch-sweep",
    "test-conv-groups-sweep",
    "test-conv-sweep",
    "test-dataflow-sweep",
    "test-interconnect-contention-sweep",
    "test-interconnect-routing-sweep",
    "test-interconnect-switching-sweep",
    "test-interconnect-topology-sweep",
    "test-mma-activation-sweep",
    "test-multicore-sweep",
    "test-norm-attention-sweep",
    "test-norm-sweep",
    "test-pooling-sweep",
    "test-rounding-sweep",
    "test-scheduler-sweep",
    "test-softmax-attention-sweep",
    "test-softmax-sweep",
    "test-sparsity-sweep",
    "test-weight-compression-sweep",
]
ADJACENT_EXPLORATION_TARGETS = [
    "test-bench",
    "test-conv-pool-cascade",
]
EXPECTED_SOURCE_TARGET_PAIRS = {
    ("tests/test_attention_sweep.c", "test-attention-sweep"),
    ("tests/test_context_switch_sweep.c", "test-context-switch-sweep"),
    ("tests/test_conv_groups_sweep.c", "test-conv-groups-sweep"),
    ("tests/test_conv_sweep.c", "test-conv-sweep"),
    ("tests/test_dataflow_sweep.c", "test-dataflow-sweep"),
    ("tests/test_interconnect_contention_sweep.c", "test-interconnect-contention-sweep"),
    ("tests/test_interconnect_routing_sweep.c", "test-interconnect-routing-sweep"),
    ("tests/test_interconnect_switching_sweep.c", "test-interconnect-switching-sweep"),
    ("tests/test_interconnect_topology_sweep.c", "test-interconnect-topology-sweep"),
    ("tests/test_mma_activation_sweep.c", "test-mma-activation-sweep"),
    ("tests/test_multicore_scaling_sweep.c", "test-multicore-sweep"),
    ("tests/test_norm_attention_sweep.c", "test-norm-attention-sweep"),
    ("tests/test_norm_sweep.c", "test-norm-sweep"),
    ("tests/test_pooling_sweep.c", "test-pooling-sweep"),
    ("tests/test_rounding_sweep.c", "test-rounding-sweep"),
    ("tests/test_scheduler_sweep.c", "test-scheduler-sweep"),
    ("tests/test_softmax_attention_sweep.c", "test-softmax-attention-sweep"),
    ("tests/test_softmax_sweep.c", "test-softmax-sweep"),
    ("tests/test_sparsity_sweep.c", "test-sparsity-sweep"),
    ("tests/test_weight_compression_sweep.c", "test-weight-compression-sweep"),
    ("tests/test_benchmark.c", "test-bench"),
    ("tests/test_conv_pool_cascade.c", "test-conv-pool-cascade"),
}
KEY_FILES = [
    "Makefile",
    "scripts/sweep_aspect_ratio.py",
    "tests/test_dataflow_sweep.c",
    "tests/test_rounding_sweep.c",
    "tests/test_context_switch_sweep.c",
    "tests/test_interconnect_topology_sweep.c",
    "tests/test_int8_sweep.c",
    "tests/test_benchmark.c",
    "tests/test_conv_pool_cascade.c",
    "docs/exploration/aspect-ratio-alignment-sweep.md",
    "docs/exploration/rounding-mode-accuracy-sweep.md",
    "docs/exploration/context-switch-state-scope.md",
    "docs/exploration/dataflow-comparison-gemm128.md",
]


def run(cmd: list[str], cwd: Path, timeout: int = 300, env: dict[str, str] | None = None) -> tuple[int, str]:
    e = {**os.environ, "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1"}
    if env:
        e.update(env)
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=timeout, env=e)
    return p.returncode, p.stdout


def git_state(label: str) -> None:
    rc, out = run(["git", "status", "--porcelain=v1", "--branch"], SOURCE)
    if rc:
        raise RuntimeError(f"git status failed at {label}: {out}")
    head = run(["git", "rev-parse", "HEAD"], SOURCE)[1].strip()
    branch_rc, _ = run(["git", "symbolic-ref", "-q", "--short", "HEAD"], SOURCE)
    dirty = out.splitlines()[1:]
    detached = branch_rc != 0
    print(f"SOURCE_STATE {label} head={head} detached={int(detached)} dirty_entries={len(dirty)}")
    if head != PIN or not detached or dirty:
        raise RuntimeError(f"unsafe source state at {label}: {out}")


def rules(make: str) -> dict[str, str]:
    flat = make.replace("\\\n", " ")
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"(?m)^([A-Za-z0-9_.-]+)\s*:\s*([^\n]*)$", flat)}


def deps(rule_map: dict[str, str], target: str) -> list[str]:
    return [x for x in rule_map.get(target, "").split() if x.startswith("test-")]


def digest_output(text: str, archive: Path) -> tuple[str, int, str]:
    normalized = text.replace(str(archive), "<ARCHIVE>")
    lines = normalized.splitlines()
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    tail = " | ".join(lines[-3:]).replace("\t", " ")
    return digest, len(lines), tail[:700]


def inventory() -> dict[str, object]:
    tracked = run(["git", "ls-files"], SOURCE)[1].splitlines()
    make = (SOURCE / "Makefile").read_text()
    rule_map = rules(make)
    c_sweeps = sorted(x for x in tracked if x.startswith("tests/test_") and x.endswith(".c") and "sweep" in Path(x).stem)
    adjacent_exploration_sources = ["tests/test_benchmark.c", "tests/test_conv_pool_cascade.c"]
    inventoried_c_exploration = sorted(c_sweeps + adjacent_exploration_sources)
    reports = sorted(x for x in tracked if x.startswith("docs/exploration/") and x.endswith(".md") and not x.endswith("IMPLEMENTATION_BACKLOG.md"))
    manifest_paths = sorted(x for x in tracked if "manifest" in x.lower())
    source_to_targets: dict[str, list[str]] = {}
    for target, prerequisite_text in rule_map.items():
        for source in re.findall(r"tests/(test_[A-Za-z0-9_]+\.c)", prerequisite_text):
            source_to_targets.setdefault("tests/" + source, []).append(target)
    c_sweep_no_rule = sorted(x for x in c_sweeps if x not in source_to_targets)
    source_linked_sweep_targets = sorted(
        target for source in c_sweeps for target in source_to_targets.get(source, [])
    )
    source_target_pairs = {
        (source, target)
        for source in inventoried_c_exploration
        for target in source_to_targets.get(source, [])
    }
    # Count-preserving relation mutation: swap the two adjacent source
    # prerequisites. A set/count-only target predicate would miss this.
    bench_anchor = "test-bench: tests/test_benchmark.c libtucmodel.a"
    cascade_anchor = "test-conv-pool-cascade: tests/test_conv_pool_cascade.c libtucmodel.a"
    if make.count(bench_anchor) != 1 or make.count(cascade_anchor) != 1:
        raise RuntimeError("relation mutation anchors are not unique")
    mutated_make = make.replace(
        bench_anchor, "test-bench: tests/test_conv_pool_cascade.c libtucmodel.a"
    ).replace(
        cascade_anchor, "test-conv-pool-cascade: tests/test_benchmark.c libtucmodel.a"
    )
    mutated_rule_map = rules(mutated_make)
    mutated_source_to_targets: dict[str, list[str]] = {}
    for target, prerequisite_text in mutated_rule_map.items():
        for source in re.findall(r"tests/(test_[A-Za-z0-9_]+\.c)", prerequisite_text):
            mutated_source_to_targets.setdefault("tests/" + source, []).append(target)
    mutated_pairs = {
        (source, target)
        for source in inventoried_c_exploration
        for target in mutated_source_to_targets.get(source, [])
    }
    relation_swap_rejected = (
        len(mutated_pairs) == len(EXPECTED_SOURCE_TARGET_PAIRS)
        and mutated_pairs != EXPECTED_SOURCE_TARGET_PAIRS
    )
    aggregate = deps(rule_map, "test")
    aggregate_sweep_targets = sorted(set(aggregate) & set(SWEEP_TARGETS))
    aggregate_exploration_targets = sorted(
        set(aggregate) & set(SWEEP_TARGETS + ADJACENT_EXPLORATION_TARGETS)
    )

    reports_with_question = []
    reports_with_hypothesis = []
    reports_with_method = []
    reports_with_explicit_harness = []
    reports_with_repro_command = []
    reports_with_manifest_word = []
    for rel in reports:
        text = (SOURCE / rel).read_text(errors="replace")
        if re.search(r"(?im)^\*\*Question:\*\*|^##?\s+Question", text):
            reports_with_question.append(rel)
        if re.search(r"(?im)^\*\*Hypothesis:\*\*|^##?\s+Hypothesis", text):
            reports_with_hypothesis.append(rel)
        if re.search(r"(?im)^##?\s+(Method|Methodology|Cycle Model|Test Harness|Sweep Harness)", text):
            reports_with_method.append(rel)
        if re.search(r"tests/test_[A-Za-z0-9_]+\.c|scripts/sweep_[A-Za-z0-9_./-]+\.py", text):
            reports_with_explicit_harness.append(rel)
        if re.search(r"make\s+test-[A-Za-z0-9-]+|python3?\s+scripts/", text):
            reports_with_repro_command.append(rel)
        if re.search(r"\bmanifest\b", text, re.I):
            reports_with_manifest_word.append(rel)

    # Mechanical producer classes are based on source calls, not filenames.
    linked_call_sources = []
    local_formula_sources = []
    for rel in inventoried_c_exploration:
        text = (SOURCE / rel).read_text(errors="replace")
        calls = set(re.findall(r"\b(tu_[A-Za-z0-9_]+)\s*\(", text))
        defined = set(re.findall(r"(?:static\s+)?(?:[A-Za-z_][A-Za-z0-9_]*\s+)+(?P<n>tu_[A-Za-z0-9_]+)\s*\(", text))
        external = calls - defined
        (linked_call_sources if external else local_formula_sources).append(rel)

    print(f"PIN {PIN}")
    print(f"SCRIPT_HASH {hashlib.sha256(Path(__file__).read_bytes()).hexdigest()} {Path(__file__).name}")
    for rel in KEY_FILES:
        print(f"HASH {hashlib.sha256((SOURCE / rel).read_bytes()).hexdigest()} {rel}")
    print(f"INVENTORY tracked={len(tracked)} c_sweep_token={len(c_sweeps)} adjacent_c_exploration={len(adjacent_exploration_sources)} inventoried_c_exploration={len(inventoried_c_exploration)} sweep_rule_targets={len(source_linked_sweep_targets)} c_sweep_no_rule={len(c_sweep_no_rule)} exploration_reports={len(reports)} tracked_manifest_paths={len(manifest_paths)}")
    print("C_SWEEP_NO_RULE " + (" ".join(c_sweep_no_rule) if c_sweep_no_rule else "none"))
    print("ADJACENT_C_EXPLORATION " + " ".join(adjacent_exploration_sources))
    print("SOURCE_LINKED_SWEEP_TARGETS " + " ".join(source_linked_sweep_targets))
    print("SOURCE_TARGET_PAIRS " + " ".join(f"{s}->{t}" for s, t in sorted(source_target_pairs)))
    print(f"MUTATION source_target_pair_swap rejected={int(relation_swap_rejected)}")
    print("AGGREGATE_SWEEP_TARGETS " + (" ".join(aggregate_sweep_targets) if aggregate_sweep_targets else "none"))
    print("AGGREGATE_EXPLORATION_TARGETS " + (" ".join(aggregate_exploration_targets) if aggregate_exploration_targets else "none"))
    print(f"REPORT_FIELDS question={len(reports_with_question)} hypothesis={len(reports_with_hypothesis)} method={len(reports_with_method)} explicit_harness={len(reports_with_explicit_harness)} repro_command={len(reports_with_repro_command)} manifest_word={len(reports_with_manifest_word)}")
    print("REPORT_EXPLICIT_HARNESS " + (" ".join(reports_with_explicit_harness) if reports_with_explicit_harness else "none"))
    print("REPORT_REPRO_COMMAND " + (" ".join(reports_with_repro_command) if reports_with_repro_command else "none"))
    print(f"PRODUCER_CLASS linked_external_tu_calls={len(linked_call_sources)} local_formula_only={len(local_formula_sources)}")
    print("LINKED_CALL_SWEEPS " + " ".join(linked_call_sources))
    print("LOCAL_FORMULA_SWEEPS " + " ".join(local_formula_sources))

    expected = {
        "inventory_c_sweeps": len(c_sweeps) == 21,
        "inventory_source_target_pairs_exact": source_target_pairs == EXPECTED_SOURCE_TARGET_PAIRS,
        "inventory_single_no_rule": c_sweep_no_rule == ["tests/test_int8_sweep.c"],
        "source_target_pair_swap_rejected": relation_swap_rejected,
        "exploration_targets_absent_from_aggregate": aggregate_exploration_targets == [],
        "inventory_reports": len(reports) == 46,
        "report_field_counts_exact": (
            len(reports_with_question) == 35
            and len(reports_with_hypothesis) == 30
            and len(reports_with_method) == 30
            and len(reports_with_explicit_harness) == 13
            and len(reports_with_repro_command) == 16
            and len(reports_with_manifest_word) == 0
        ),
        "producer_partition_exact": len(linked_call_sources) == 19 and len(local_formula_sources) == 4,
        "source_has_no_tracked_manifest": manifest_paths == [],
        "aspect_script_is_only_sweep_python": [x for x in tracked if x.endswith(".py") and "sweep" in Path(x).stem] == ["scripts/sweep_aspect_ratio.py"],
    }
    if os.environ.get("CH21_FRAMING_INJECT_FAILURE") == "inventory":
        expected["injected_inventory_predicate"] = False
    for name, ok in expected.items():
        print(f"PREDICATE {name}={'PASS' if ok else 'FAIL'}")
    if not all(expected.values()):
        failed = ",".join(name for name, ok in expected.items() if not ok)
        raise RuntimeError(f"static inventory predicate failed: {failed}")
    return {"reports": reports, "c_sweeps": c_sweeps}


def failure_path_source_control() -> None:
    script = Path(__file__).resolve()
    rc, out = run(
        [sys.executable, str(script)],
        script.parent.parent,
        env={"CH21_FRAMING_INJECT_FAILURE": "inventory"},
    )
    diagnostic = "static inventory predicate failed: injected_inventory_predicate"
    after = f"SOURCE_STATE after head={PIN} detached=1 dirty_entries=0"
    rejected = (
        rc != 0
        and diagnostic in out
        and out.count(after) == 1
        and "PREDICATE injected_inventory_predicate=FAIL" in out
    )
    print(
        "FAILURE_PATH_CONTROL inventory_predicate "
        f"rc_nonzero={int(rc != 0)} diagnostic={int(diagnostic in out)} "
        f"source_after_unique={int(out.count(after) == 1)} rejected={int(rejected)}"
    )
    if not rejected:
        raise RuntimeError("failure-path source-preservation control failed")


def execute_archive() -> None:
    with tempfile.TemporaryDirectory(prefix="ch21-framing-") as td:
        root = Path(td)
        archive = root / "src"
        archive.mkdir()
        tar_path = root / "tusim.tar"
        with tar_path.open("wb") as f:
            p = subprocess.run(["git", "archive", "--format=tar", PIN], cwd=SOURCE, stdout=f)
        if p.returncode:
            raise RuntimeError("git archive failed")
        rc, out = run(["tar", "-xf", str(tar_path), "-C", str(archive)], SOURCE)
        if rc:
            raise RuntimeError(f"archive extraction failed: {out}")
        print(f"ARCHIVE disposable=yes source_pin={PIN}")

        rc, out = run(["make", "-j2", "all"], archive, timeout=600)
        d, n, tail = digest_output(out, archive)
        print(f"EXEC build_all rc={rc} lines={n} sha256={d} tail={tail}")
        if rc:
            raise RuntimeError("archive build failed")

        statuses: dict[str, int] = {}
        for target in SWEEP_TARGETS + ADJACENT_EXPLORATION_TARGETS:
            dry_rc, dry = run(["make", "-n", target], archive)
            unsafe = "/tmp/" in dry or "rm -f /tmp" in dry
            print(f"DRY_RUN {target} rc={dry_rc} host_global_tmp={int(unsafe)}")
            if dry_rc or unsafe:
                raise RuntimeError(f"unsafe or invalid target: {target}")
            rc, out = run(["make", target], archive, timeout=600,
                          env={"LD_LIBRARY_PATH": str(archive)})
            statuses[target] = rc
            d, n, tail = digest_output(out, archive)
            print(f"EXEC {target} rc={rc} lines={n} sha256={d} tail={tail}")

        # The sole source-present/no-rule C sweep is analytical and self-contained.
        manual = archive / "ch21-int8-sweep"
        rc, out = run(["cc", "-O2", "-Wall", "-Wextra", "-std=c11", "-o", str(manual),
                       "tests/test_int8_sweep.c", "-lm"], archive)
        print(f"MANUAL_COMPILE test-int8-sweep rc={rc}")
        if rc:
            raise RuntimeError(f"manual INT8 sweep compile failed: {out}")
        rc, out = run([str(manual)], archive)
        statuses["manual-int8-sweep"] = rc
        d, n, tail = digest_output(out, archive)
        print(f"EXEC manual-int8-sweep rc={rc} lines={n} sha256={d} tail={tail}")

        rc, out = run(["python3", "scripts/sweep_aspect_ratio.py"], archive)
        statuses["aspect-ratio-python"] = rc
        d, n, tail = digest_output(out, archive)
        config_match = "**Configs tested:** 120" in out
        print(f"EXEC aspect-ratio-python rc={rc} lines={n} sha256={d} configs120={int(config_match)} tail={tail}")

        # Real source mutation in the disposable archive: a stale/wrong matrix
        # size must be rejected by the same observation predicate used above.
        aspect_path = archive / "scripts/sweep_aspect_ratio.py"
        aspect_source = aspect_path.read_text()
        aspect_old = 'print(f"**Configs tested:** {len(workloads)}")'
        if aspect_source.count(aspect_old) != 1:
            raise RuntimeError("aspect-ratio mutation anchor is not unique")
        aspect_path.write_text(aspect_source.replace(aspect_old, 'print("**Configs tested:** 119")'))
        mutation_rc, mutation_out = run(["python3", "scripts/sweep_aspect_ratio.py"], archive)
        mutation_rejected = (
            mutation_rc == 0
            and "**Configs tested:** 119" in mutation_out
            and "**Configs tested:** 120" not in mutation_out
        )
        print(f"MUTATION aspect_ratio_config_count rc={mutation_rc} rejected={int(mutation_rejected)}")

        print("EXEC_STATUS_VECTOR " + " ".join(f"{k}={v}" for k, v in statuses.items()))
        live = {
            "all_22_make_exploration_targets_exit_zero": len(statuses) == 24 and all(
                statuses[t] == 0 for t in SWEEP_TARGETS + ADJACENT_EXPLORATION_TARGETS
            ),
            "manual_int8_sweep_exit_zero": statuses.get("manual-int8-sweep") == 0,
            "aspect_ratio_harness_exit_zero_and_120_configs": statuses.get("aspect-ratio-python") == 0 and config_match,
            "aspect_ratio_source_mutation_rejected": mutation_rejected,
        }
        for name, ok in live.items():
            print(f"LIVE_GATE {name}={'PASS' if ok else 'FAIL'}")
        if not all(live.values()):
            raise RuntimeError("framing live gate failed")


def main() -> int:
    git_state("before")
    result = 1
    try:
        inventory()
        failure_path_source_control()
        execute_archive()
        result = 0
    finally:
        git_state("after")
    if result == 0:
        print("CH21_FRAMING_RECON PASS")
    return result


if __name__ == "__main__":
    sys.exit(main())
