#!/usr/bin/env python3
"""Optimization-safe manuscript and release validation for Chapter 21."""
from __future__ import annotations

import ast
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "manuscript/part-2-core/21-designing-a-trustworthy-sweep.md"
LEDGER = ROOT / "notes/chapter-21-source-and-claim-ledger.md"
LIMIT_REGISTER = ROOT / "notes/chapter-21-limitation-register.md"
AUDIT_REPORT = ROOT / "notes/chapter-21-predraft-audit-report.md"
RUN_ID = "20260818-ch21-postreview-v8"
RUN_REL = Path("experiments/runs") / RUN_ID
RUN = ROOT / RUN_REL
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
INPUT_COMMIT = "3e8ec2bbf64f9a85b8ffbfd9ca12ce2ccdef3379"
SEAL_COMMIT = "f37e8582746f4159a2ed418b7f3eceba9e0847eb"
TUSIM = Path("/home/zxy/Workplace/projects/tusim")
SNAPSHOT = ROOT / "notes/chapter-21-reviewed-snapshot.txt"
REVIEW_MODE = os.environ.get("CH21_MANUSCRIPT_REVIEW_MODE") == "1"
SELFTEST_CHILD = os.environ.get("CH21_VALIDATOR_SELFTEST_CHILD") == "1"
BIND_PATHS = {
    "manuscript_blob": "manuscript/part-2-core/21-designing-a-trustworthy-sweep.md",
    "validator_blob": "experiments/ch21_manuscript_validate.py",
    "runner_blob": "experiments/run_ch21_manuscript_validation.sh",
    "ledger_blob": "notes/chapter-21-source-and-claim-ledger.md",
    "limitations_blob": "notes/chapter-21-limitation-register.md",
    "audit_report_blob": "notes/chapter-21-predraft-audit-report.md",
}
OUTER_MEMBERS = {
    "sha256-retained.txt",
    "manifest-check.log",
    "finalization.log",
    "predraft-validation-normal.log",
    "predraft-validation-optimized.log",
}
DERIVED_MEMBERS = {
    "bundle-sha256.txt",
    "bundle-check.log",
    "closure-validation-normal.log",
    "closure-validation-optimized.log",
}
PROBE_LINES = [
    "DATAFLOW_ROUTE requested_label=output_stationary process_global_before=1 core_snapshot_before=0 core_snapshot_after=0 effective_core=weight_stationary",
    "DATAFLOW_EXEC tag=labeled_os active=weight_stationary delta=67 output=58,64,139,154",
    "DATAFLOW_EXEC tag=active_os active=output_stationary delta=4 output=58,64,139,154",
    "DATAFLOW_EXEC tag=active_rs active=row_stationary delta=36 output=58,64,139,154",
    "DATAFLOW_LINKED_EXEC active=weight_stationary M=128 N=128 K=256 tile=16x16x16 cycles=81920",
    "DATAFLOW_LINKED_EXEC active=output_stationary M=128 N=128 K=256 tile=16x16x16 cycles=20480",
    "DATAFLOW_LINKED_EXEC active=row_stationary M=128 N=128 K=256 tile=16x16x16 cycles=50176",
    "ROUNDING_AXIS value=1.0007 rne=0x3c01 rtz=0x3c00 same_seed_equal=1 changed_seed_diff=1 seed12345_fnv=99a9ff040fc80ca3 seed54321_fnv=283bd184c961bcc2",
    "RANDOMNESS_SCOPE fixed_seed_replay=1 changed_seed_vector=1 independent_application_samples=0 application_accuracy=0",
    "ROUNDING_ORDER stable_case_seed_permutation_equal=1 single_seed_permutation_diff=1 stable_fnv=33c857eecbbc9f2f",
    "CONTEXT_EXEC full256=16484 live25_256=4196 control256=100 full256_bw16=32868 full256_bw64=8292 producer=linked_estimator",
    "CH21_SWEEP_PROBE SUMMARY failures=0",
]
FORMULA_LINES = [
    "ASPECT_MATRIX rows=120 M_set=12 N_set=10 K=128 producer=local_formula",
    "ASPECT_BOUNDARY M20N16_util=62.5 M40N16_util=83.3 M20N16_total=570 symmetry_16x256_256x16=1",
    "COUNTEREXAMPLE report_nonzero_remainder_le_3.8=0 M40_remainder8_waste=16.7",
    "ASPECT_TRANSITION totals=404,543,570,606,669,678 tie_M16_M24=1 padding20to32_reverses=1 duplicated_20x48=1382_vs_1376",
    "DATAFLOW_REPORT_SENSITIVITY K_points=1,16,32,64,256,1024 R_points=8,16,32 fixed_formula_delta=32 decreasing_fraction=1 producer=report_prose",
    "DATAFLOW_PRODUCERS sweep_local=26624,22528,24640 report_local=21536,21504 linked_plugin=81920,20480,50176 incomparable=1",
    "ASPECT_TWO_AXIS workload_M=16,17,20,24,31,32 architecture_pd_bus=1_32,2_32,4_32,2_16,2_64",
    "CONTEXT_CROSSOVER budget10000_bw52=10183 bw53=9993 full128_live32_tie=4196 control_reversal_reload_gt=16384",
    "PRODUCER_CLASSES executable=1 linked_estimator=1 local_formula=1 report_prose=1 heterogeneous_sum=0",
    "CH21_FORMULA_PROBE PASS",
]
REQUIRED_PHRASES = [
    "21 C files with `sweep` in the filename",
    "two adjacent semantic or comparative harnesses",
    "22 literal source-to-Make-target relations",
    "one no-rule singleton",
    "46 exploration reports",
    "21 selected source hashes",
    "CH21_SOURCE_AUDIT PASS pin=" + PIN + " hashes=21 predicates=26 checks=48",
    "requested_label=output_stationary process_global_before=1 core_snapshot_before=0 core_snapshot_after=0 effective_core=weight_stationary",
    "[58,64,139,154]",
    "plugin deltas 67/4/36",
    "rne=0x3c01 rtz=0x3c00",
    "same_seed_equal=1 changed_seed_diff=1",
    "FULL      16,484 model cycles",
    "LIVE25     4,196 model cycles",
    "CONTROL      100 model cycles",
    "32,868 and 8,292",
    "26,624 | 22,528 | 24,640",
    "21,536 | 21,504",
    "81,920 | 20,480 | 50,176",
    "0.2048 TMAC/s, or 0.4096 TOPS",
    "404, 543, 570, 606, 669, 678",
    "10,183 and 9,993",
    "1,382 and 1,376",
    "waste is 16.7% for remainder 8",
    "61 retained payload members",
    "six normal plus six optimized manifest-hierarchy rejection cases",
    "Chapter 17 remains authoritative",
    "Chapter 20 defines what evidence is required to authorize a claim",
    "Chapter 22 alone owns preference rules, Pareto selection, and conclusions across the exploration portfolio",
    "Chapters 19 and 20 remain closed",
]
CLAIM_MUTATIONS = {
    "21 C files with `sweep` in the filename": (1, "20 C files with `sweep` in the filename"),
    "22 literal source-to-Make-target relations": (1, "23 literal source-to-Make-target relations"),
    "46 exploration reports": (1, "45 exploration reports"),
    "21 selected source hashes": (1, "20 selected source hashes"),
    "plugin deltas 67/4/36": (1, "plugin deltas 67/5/36"),
    "[58,64,139,154]": (3, "[58,64,139,155]"),
    "delta=67": (1, "delta=68"),
    "exactly 120 rows": (1, "exactly 119 rows"),
    "a 120-row matrix": (1, "a 119-row matrix"),
    "120-row aspect matrix": (1, "119-row aspect matrix"),
    "RNE/RTZ conversion codes": (1, "application-level RNE/RTZ accuracy"),
    "26,624/22,528/24,640": (1, "26,624/22,529/24,640"),
    "21,536/21,504": (1, "21,536/21,505"),
    "81,920/20,480/50,176": (1, "81,920/20,481/50,176"),
    "10,183 and 9,993": (1, "10,182 and 9,993"),
    "FULL at 128 B/cycle ties LIVE25 at 32 B/cycle at 4,196 model cycles": (1, "FULL at 128 B/cycle ties LIVE25 at 32 B/cycle at 4,197 model cycles"),
    "1,382 and 1,376": (2, "1,382 and 1,377"),
    "waste is 16.7% for remainder 8": (2, "waste is 3.8% for remainder 8"),
    "Chapter 17 retains metric semantics": (1, "Chapter 21 redefines metric semantics"),
    "Chapter 20 evidence authorization": (1, "Chapter 21 evidence authorization"),
    "Chapter 22 portfolio preference and synthesis": (1, "Chapter 21 portfolio preference and synthesis"),
    "No compiler/runtime composition": (1, "A compiler/runtime composition"),
    "produce the same bounded matrix output": (1, "produce different bounded matrix output"),
    "The canonical run has 61 retained payload members": (1, "The canonical run has 60 retained payload members"),
    "complete 71-file final run tree": (1, "complete 70-file final run tree"),
    "CH21_SOURCE_AUDIT PASS pin=" + PIN + " hashes=21 predicates=26 checks=48": (1, "CH21_SOURCE_AUDIT PASS pin=" + PIN + " hashes=21 predicates=25 checks=47"),
    "CH21_POSTSEAL PASS run=20260818-ch21-postreview-v8 head=" + SEAL_COMMIT + " parent=" + INPUT_COMMIT + " changed=71": (1, "CH21_POSTSEAL PASS run=20260818-ch21-postreview-v8 head=" + SEAL_COMMIT + " parent=" + INPUT_COMMIT + " changed=70"),
}

EXTERNAL_LINK_COUNTS = {
    "https://doi.org/10.1109/4235.996017": 2,
    "https://doi.org/10.1109/MC.2003.1178050": 2,
    "https://doi.org/10.1126/science.aah6168": 2,
    "https://doi.org/10.1145/1168857.1168881": 2,
    "https://doi.org/10.1145/1250662.1250713": 2,
    "https://doi.org/10.1145/1328195.1328196": 2,
    "https://doi.org/10.1145/1508244.1508275": 2,
    "https://doi.org/10.1145/5666.5673": 2,
    "https://doi.org/10.1371/journal.pcbi.1003285": 2,
    "https://doi.org/10.17487/RFC8493": 1,
    "https://www.rfc-editor.org/rfc/rfc8493.html": 1,
}
ANSWER_SKETCHES = (
    "1. Keep the decision local and name what result would falsify it; a report heading or preferred row is not a disproof condition.",
    "2. Represent every relation literally and mutate one member while preserving count so the semantic set gate, not only a hash or cardinality gate, is exercised.",
    "3. Use nonsymmetric data, active implementation identity, implementation-specific state or counters, and a direct positive control; equal output alone is insufficient.",
    "4. Do not accept a field name as units or fidelity; compare only rows with the same producer contract or a proved common timeline.",
    "5. Reseed each case, require same-seed identity, changed-seed difference, and forward/reverse equality under per-case reset; report unique vectors separately from invocations.",
    "6. Include below, exact, and above-boundary points and perturb one second architecture parameter so a single-axis formula cannot define the entire conclusion.",
    "7. Preserve the counterexample, narrow the conclusion to the tested grid or equation, and remove downstream recommendations that require an unexercised compiler/runtime route.",
    "8. Preserve producer status and parsed observations separately; any nonzero, mismatch, missing output, timeout, or contradiction is non-pass.",
    "9. Retain per-workload rows first; use only a mathematically appropriate summary, disclose all exclusions, and preserve exact ties instead of hidden tie-breaking.",
    "10. Nondominance depends on the declared matrix, objectives, constraints, workloads, and fidelity; preference and portfolio ranking remain a separate decision.",
    "11. Require exact regular contained members, reject missing/extra/duplicate/symlink/traversal cases, verify hashes, mutation-test the validator, and bind the reviewed final tree.",
    "12. Use the same workload and mapping, name both producers and clocks, define synchronization and uncertainty, test several regimes, and report error rather than transferring calibration globally.",
)


class ValidationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def run_checked(args, cwd=ROOT, env=None, timeout=240) -> str:
    result = subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=timeout)
    require(result.returncode == 0,
            f"command failed {' '.join(map(str, args))}: {result.stdout[-1200:]}")
    return result.stdout


def git_output(args, cwd=ROOT) -> str:
    return run_checked(["git", *args], cwd=cwd).strip()


def git_blob(commit: str, rel: str) -> bytes:
    result = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    require(result.returncode == 0, f"git blob {commit}:{rel}")
    return result.stdout


def parse_manifest(path: Path, expected: set[str], member_root: Path) -> dict[str, str]:
    require(path.is_file() and not path.is_symlink(), f"missing/unsafe manifest {path.name}")
    entries: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (?:\./)?([^\s]+)", line)
        require(match is not None, f"malformed manifest line {path.name}:{number}")
        if match is None:
            raise ValidationError(f"malformed manifest line {path.name}:{number}")
        digest, member = match.groups()
        require(member not in entries, f"duplicate manifest member {path.name}:{member}")
        pure = Path(member)
        require(not pure.is_absolute() and ".." not in pure.parts, f"unsafe manifest member {member}")
        entries[member] = digest
    require(set(entries) == expected, f"exact member set {path.name}")
    root_resolved = member_root.resolve()
    for member, digest in entries.items():
        target = member_root / member
        require(target.is_file() and not target.is_symlink(), f"manifest regular member {member}")
        require(target.resolve().is_relative_to(root_resolved), f"manifest contained member {member}")
        require(sha(target) == digest, f"manifest digest {member}")
    return entries


def slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return re.sub(r"[ -]+", "-", text).strip("-")


def headings(path: Path) -> set[str]:
    found: set[str] = set()
    counts: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            base = slug(match.group(1))
            count = counts.get(base, 0)
            found.add(base if count == 0 else f"{base}-{count}")
            counts[base] = count + 1
    return found


def parse_limitations(text: str) -> dict[str, str]:
    result = dict(re.findall(r"(?m)^- \*\*(C21\.\d+):\*\* (.+)$", text))
    require(set(result) == {f"C21.{number}" for number in range(1, 13)},
            "exact C21.1-C21.12 limitation set")
    return result


def validate_links(text: str) -> None:
    unfenced = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    links = re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", unfenced)
    require(len(links) >= 20, "sufficient manuscript links")
    primary = text.split("## Primary references", 1)
    require(len(primary) == 2 and len(re.findall(r"\]\(", primary[1])) >= 10,
            "primary-reference links")
    external = [raw.strip().split()[0].strip("<>") for raw in links
                if raw.strip().split()[0].strip("<>").startswith(("https://", "http://"))]
    for target, count in EXTERNAL_LINK_COUNTS.items():
        require(external.count(target) == count, f"external citation destination/count {target}")
    require(set(external) == set(EXTERNAL_LINK_COUNTS), "exact external citation destination set")
    for raw in links:
        target = raw.strip().split()[0].strip("<>")
        if target.startswith(("https://", "http://")):
            continue
        require(not target.startswith("/"), f"absolute local link {target}")
        file_part, marker = target.split("#", 1) if "#" in target else (target, "")
        resolved = (CHAPTER.parent / file_part).resolve() if file_part else CHAPTER.resolve()
        require(resolved == ROOT or ROOT in resolved.parents, f"link escapes repository {target}")
        require(resolved.is_file(), f"missing link target {target}")
        if marker:
            require(marker in headings(resolved), f"invalid anchor {target}")


def section_numbered_count(text: str, start: str, end: str) -> int:
    return len(re.findall(r"(?m)^\d+\. ", text.split(start, 1)[1].split(end, 1)[0]))


def validate_text(text: str, limitations: dict[str, str]) -> None:
    require(text.startswith("# Chapter 21 — Designing a Trustworthy Sweep\n"), "title")
    require(PIN in text and INPUT_COMMIT in text and SEAL_COMMIT in text, "edition and seal binding")
    words = len(re.findall(r"\b[\w’'-]+\b", text))
    require(7400 <= words <= 9000, f"word count {words}")
    required_headings = [
        "Learning objectives", "Prerequisite graph", "Opening architecture question",
        "Theory", "Source map", "Construct the question", "Prove that each axis",
        "Bind producer", "Controls and fail-closed status", "Sensitivity",
        "Worked chain-of-custody decisions", "Reproducibility", "Alternatives and trade-offs",
        "Verification evidence and canonical authority", "Common failure modes", "Fidelity box",
        "Sealed limitation register", "Development questions", "Summary", "Review questions",
        "Review-question answer key", "Design exercises", "Exercise answer sketches", "Primary references",
    ]
    actual = [m.group(1).lower() for m in re.finditer(r"(?m)^#{2,6}\s+(.+)$", text)]
    for heading in required_headings:
        require(any(heading.lower() in item for item in actual), f"heading {heading}")
    require(section_numbered_count(text, "## Review questions", "### Review-question answer key") == 15,
            "review-question count")
    require(section_numbered_count(text, "### Review-question answer key", "## Design exercises") == 15,
            "review-answer count")
    require(section_numbered_count(text, "## Design exercises", "### Exercise answer sketches") == 12,
            "exercise count")
    require(section_numbered_count(text, "### Exercise answer sketches", "## Primary references") == 12,
            "exercise-answer count")
    answer_section = text.split("### Exercise answer sketches", 1)[1].split("## Primary references", 1)[0]
    for answer in ANSWER_SKETCHES:
        require(answer_section.count(answer) == 1, f"exercise-answer content {answer.split('.', 1)[0]}")
    for claim_id, sentence in limitations.items():
        require(text.count(f"| {claim_id} | {sentence} |") == 1,
                f"verbatim limitation row {claim_id}")
        require(text.count(sentence) == 1, f"unique limitation wording {claim_id}")
    for phrase in REQUIRED_PHRASES:
        require(phrase.lower() in text.lower(), f"claim-critical phrase {phrase}")
    for phrase, (count, _) in CLAIM_MUTATIONS.items():
        require(text.count(phrase) == count, f"mutation-gated phrase/count {phrase}")
    unsafe = [
        "The labeled OS row executes output-stationary.",
        "The aspect-ratio script runs a Tusim workload.",
        "CONTROL is end-to-end fastest.",
        "Changed stochastic seeds are independent workload samples.",
        "Chapter 21 selects the optimal architecture portfolio.",
        "Tusim provides an integrated ONNX/compiler/runtime path.",
    ]
    for statement in unsafe:
        require(statement.lower() not in text.lower(), f"unsafe affirmative claim {statement}")
    require(not re.search(r"(?m)^\|\|", text), "malformed markdown table row")
    require(not any(line.rstrip() != line for line in text.splitlines()), "trailing whitespace")


def replace_nth(text: str, old: str, new: str, occurrence: int) -> str:
    start = -1
    for _ in range(occurrence + 1):
        start = text.find(old, start + 1)
        require(start >= 0, f"mutation occurrence absent {old}:{occurrence}")
    return text[:start] + new + text[start + len(old):]


def mutation_tests(original: str, limitations: dict[str, str]) -> tuple[int, int]:
    reader_count = 0
    for old, (count, new) in CLAIM_MUTATIONS.items():
        require(original.count(old) == count, f"mutation source {old}")
        for occurrence in range(count):
            try:
                mutated = replace_nth(original, old, new, occurrence)
                validate_text(mutated, limitations)
                validate_links(mutated)
            except ValidationError:
                reader_count += 1
            else:
                raise ValidationError(f"manuscript mutation survived: {old}:{occurrence}")
    for answer in ANSWER_SKETCHES:
        replacement = answer.split(".", 1)[0] + ". [deleted]"
        try:
            validate_text(original.replace(answer, replacement, 1), limitations)
        except ValidationError:
            reader_count += 1
        else:
            raise ValidationError(f"answer mutation survived: {replacement}")
    for claim_id, sentence in limitations.items():
        try:
            validate_text(original.replace(sentence, sentence + " Broader authority is implied.", 1), limitations)
        except ValidationError:
            continue
        raise ValidationError(f"limitation mutation survived: {claim_id}")
    for old, count in EXTERNAL_LINK_COUNTS.items():
        require(original.count(old) == count, f"external mutation source {old}")
        for occurrence in range(count):
            try:
                mutated = replace_nth(original, old, old + "-mutated", occurrence)
                validate_text(mutated, limitations)
                validate_links(mutated)
            except ValidationError:
                reader_count += 1
            else:
                raise ValidationError(f"external citation mutation survived: {old}:{occurrence}")
    return reader_count, len(limitations)


def validate_evidence() -> None:
    require(RUN.is_dir() and not RUN.is_symlink(), "canonical postreview-v8 run")
    retained = (RUN / "retained-files.txt").read_text(encoding="utf-8").splitlines()
    require(retained == sorted(retained) and len(retained) == 61, "retained inventory order/count")
    inner_expected = set(retained) | {"retained-files.txt"}
    inner = parse_manifest(RUN / "sha256-retained.txt", inner_expected, RUN)
    parse_manifest(RUN / "bundle-sha256.txt", OUTER_MEMBERS, RUN)
    final_expected = inner_expected | {"sha256-retained.txt"} | OUTER_MEMBERS | DERIVED_MEMBERS
    files = {str(path.relative_to(RUN)) for path in RUN.rglob("*") if path.is_file()}
    require(files == final_expected and len(files) == 71, "exact sealed run inventory")
    require(len(inner) == 62, "inner manifest count")
    require(len((RUN / "manifest-check.log").read_text().splitlines()) == 62,
            "inner manifest check count")
    require(len((RUN / "bundle-check.log").read_text().splitlines()) == 5,
            "outer manifest check count")
    run_checked(["sha256sum", "-c", "sha256-retained.txt"], cwd=RUN)
    run_checked(["sha256sum", "-c", "bundle-sha256.txt"], cwd=RUN)
    require((RUN / "input_commit").read_text().strip() == INPUT_COMMIT, "input commit")
    require((RUN / "source_pin").read_text().strip() == PIN, "source pin")
    probe = (RUN / "probe-O0.log").read_text()
    require((RUN / "probe-O0.log").read_bytes() == (RUN / "probe-O2.log").read_bytes(),
            "probe optimization identity")
    for line in PROBE_LINES:
        require(line in probe, f"complete probe line {line}")
    formula = (RUN / "formula.log").read_text()
    for line in FORMULA_LINES:
        require(line in formula, f"complete formula line {line}")
    require("normal_cases=6 optimized_cases=6 all_rejected=1" in
            (RUN / "manifest-hierarchy-mutations.log").read_text(), "manifest mutations")
    require("CH21_FORMULA_PROBE REJECT dataflow-linked" in
            (RUN / "formula-mutation.log").read_text(), "linked formula mutation")
    env = os.environ.copy()
    env["CH21_RUN_ID"] = RUN_ID
    predraft = str(ROOT / "experiments/ch21_predraft_validate.py")
    for prefix in (["python3"], ["python3", "-O"]):
        run_checked([*prefix, predraft, "--outer"], env=env)
    parents = git_output(["show", "-s", "--format=%P", SEAL_COMMIT]).split()
    require(parents == [INPUT_COMMIT], "evidence seal parent")
    changed = git_output(["diff-tree", "--no-commit-id", "--name-only", "-r", SEAL_COMMIT]).splitlines()
    prefix = f"{RUN_REL.as_posix()}/"
    require(len(changed) == 71 and all(path.startswith(prefix) for path in changed),
            "evidence seal run-only shape")


def validate_self_mutation() -> None:
    if SELFTEST_CHILD:
        return
    source = Path(__file__).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="ch21-validator-") as temp:
        mutated = Path(temp) / "ch21_manuscript_validate.py"
        mutated.write_text(source + "\nassert(False)\n", encoding="utf-8")
        env = os.environ.copy()
        env["CH21_VALIDATOR_SELFTEST_CHILD"] = "1"
        env["CH21_MANUSCRIPT_REVIEW_MODE"] = "1"
        for prefix in (["python3"], ["python3", "-O"]):
            result = subprocess.run([*prefix, str(mutated)], cwd=ROOT, env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
            require(result.returncode != 0 and
                    "optimizer-removable assertion in validator" in result.stdout,
                    f"validator assertion mutation {' '.join(prefix)}")


def validate_repository_state() -> str:
    require(git_output(["branch", "--show-current"]) == "main", "book branch main")
    require(git_output(["rev-parse", "HEAD"], cwd=TUSIM) == PIN, "Tusim source pin")
    require(git_output(["branch", "--show-current"], cwd=TUSIM) == "", "Tusim detached")
    require(git_output(["status", "--porcelain", "--untracked-files=all"], cwd=TUSIM) == "",
            "Tusim clean")
    head = git_output(["rev-parse", "HEAD"])
    if REVIEW_MODE:
        return head
    require(git_output(["status", "--porcelain", "--untracked-files=all"]) == "", "clean book worktree")
    require(SNAPSHOT.is_file(), "reviewed snapshot marker")
    entries: dict[str, str] = {}
    for line in SNAPSHOT.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([a-z_]+)=([0-9a-f]{40}|[0-9a-f]{64})", line)
        require(match is not None, "reviewed snapshot syntax")
        if match is None:
            raise ValidationError("reviewed snapshot syntax")
        key, value = match.groups()
        require(key not in entries, f"duplicate snapshot key {key}")
        entries[key] = value
    require(set(entries) == {"claim_commit", *BIND_PATHS}, "reviewed snapshot keys")
    claim = entries["claim_commit"]
    run_checked(["git", "merge-base", "--is-ancestor", claim, head])
    for key, rel in BIND_PATHS.items():
        blob = git_blob(claim, rel)
        require(sha_bytes(blob) == entries[key], f"reviewed marker hash {rel}")
        require(blob == (ROOT / rel).read_bytes(), f"current blob matches reviewed claim {rel}")
    return claim


def main() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    try:
        parsed = ast.parse(source)
    except SyntaxError as error:
        raise ValidationError(f"invalid validator source: {error}")
    require(not any(isinstance(node, ast.Assert) for node in ast.walk(parsed)),
            "optimizer-removable assertion in validator")
    require(CHAPTER.is_file() and LEDGER.is_file() and LIMIT_REGISTER.is_file() and AUDIT_REPORT.is_file(),
            "chapter and governance inputs")
    live = parse_limitations(LIMIT_REGISTER.read_text(encoding="utf-8"))
    frozen = parse_limitations((RUN / "inputs/notes/chapter-21-limitation-register.md").read_text(encoding="utf-8"))
    require(live == frozen, "live limitations match sealed limitations")
    text = CHAPTER.read_text(encoding="utf-8")
    audit_report = AUDIT_REPORT.read_text(encoding="utf-8")
    require("The corrected postreview-v8 runner binds those records" in audit_report and
            "Drafting/closure authority exists only when v8 passes" in audit_report and
            "corrected postreview-v7 runner" not in audit_report,
            "live v8 audit-report authority")
    validate_text(text, frozen)
    validate_links(text)
    validate_evidence()
    reader_mutations, limitation_mutations = mutation_tests(text, frozen)
    validate_self_mutation()
    claim = validate_repository_state()
    words = len(re.findall(r"\b[\w’'-]+\b", text))
    mode = "review" if REVIEW_MODE else "release"
    print(f"CH21_MANUSCRIPT_VALIDATION PASS run={RUN_REL} words={words} inner=62 outer=5 total=71 "
          f"source_checks=48 limitations=12 reader_mutations={reader_mutations} "
          f"limitation_mutations={limitation_mutations} total_mutations={reader_mutations + limitation_mutations} "
          f"optimization_safe=yes mode={mode} claim_commit={claim}")


if __name__ == "__main__":
    try:
        main()
    except ValidationError as error:
        raise SystemExit(f"CH21_MANUSCRIPT_VALIDATION FAIL: {error}")
