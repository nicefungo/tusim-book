#!/usr/bin/env python3
"""Optimization-safe manuscript and release validation for Chapter 20."""
from pathlib import Path
import ast
import hashlib
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "manuscript/part-2-core/20-verification-as-an-architectural-feature.md"
LEDGER = ROOT / "notes/chapter-20-source-and-claim-ledger.md"
RUN_ID = "20260816-ch20-postreview-v2"
RUN_REL = Path("experiments/runs") / RUN_ID
RUN = ROOT / RUN_REL
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
INPUT_COMMIT = "e5dd99715300c78d9e08d9b1df4bec909bc03982"
SEAL_COMMIT = "c37c49a73180de2b435f345a2cc963c924403c22"
PROBE_SHA256 = "12c59a42056f92fc27b531e3e933860c11c125c72c089f8893fb5d355cb7691e"
SNAPSHOT = ROOT / "notes/chapter-20-reviewed-snapshot.txt"
REVIEW_MODE = os.environ.get("CH20_MANUSCRIPT_REVIEW_MODE") == "1"
TUSIM = Path("/home/zxy/Workplace/projects/tusim")
BIND_PATHS = {
    "manuscript_blob": "manuscript/part-2-core/20-verification-as-an-architectural-feature.md",
    "validator_blob": "experiments/ch20_manuscript_validate.py",
    "runner_blob": "experiments/run_ch20_manuscript_validation.sh",
    "ledger_blob": "notes/chapter-20-source-and-claim-ledger.md",
}
OUTER_MEMBERS = {
    "sha256-retained.txt", "manifest-check.log", "finalization.log",
    "predraft-validation-normal.log", "predraft-validation-optimized.log",
}
DERIVED_MEMBERS = {
    "bundle-sha256.txt", "bundle-check.log",
    "closure-validation-normal.log", "closure-validation-optimized.log",
}
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
CLAIM_OCCURRENCES = {
    "exactly 31 prerequisite targets": (3, "exactly 64 prerequisite targets"),
    "make test` has exactly 31 prerequisite targets": (1, "make test` has exactly 64 prerequisite targets"),
    "make test prerequisite targets             31": (1, "make test prerequisite targets             64"),
    "all 64 source-present programs": (1, "all 63 source-present programs"),
    "64 C test sources": (1, "63 C test sources"),
    "59 are named by rule prerequisites": (1, "58 are named by rule prerequisites"),
    "four quick or 14 full targets": (2, "five quick or 14 full targets"),
    "Fixed seeds `42`, `99`, `777`, and `888`": (1, "Fixed seeds `43`, `99`, `777`, and `888`"),
    "Seeds 42, 99, 777, and 888": (1, "Seeds 43, 99, 777, and 888"),
    "8×4": (6, "8×5"),
    "16×16": (6, "16×15"),
    "created_bytes=336 reinitialized_bytes=338": (2, "created_bytes=338 reinitialized_bytes=336"),
    "reported=0 actual=338": (2, "reported=338 actual=338"),
    "native C-to-C wrapper evidence": (3, "HDL simulator boundary evidence"),
    "No HDL simulator boundary is exercised": (1, "An HDL simulator boundary is exercised"),
    "serialization and checksum comparison are executable": (1, "serialization and instruction execution are executable"),
    "deterministic instruction re-execution and behavioral replay are rejected": (2, "deterministic instruction re-execution and behavioral replay are established"),
    "recording an in-memory entry and invoking checksum-comparison replay are executable": (1, "serializing and executing an instruction are established"),
    "It records an in-memory trace entry and invokes checksum-comparison replay": (1, "It serializes and executes the trace entry"),
    "Serialization round-trip is separate focused-suite evidence": (1, "Serialization round-trip occurs in this fixture"),
    "Chapter 17 remains authoritative": (2, "Chapter 17 is merely informative"),
    "Chapter 21 owns sweep construction": (2, "Chapter 20 owns sweep construction"),
    "Chapter 23 owns extension procedure": (2, "Chapter 20 owns extension procedure"),
    "Chapter 19 remains closed": (3, "Chapter 19 is reopened"),
    "No ONNX/compiler/scheduler/allocator/queue/runtime composition is authorized": (1, "An ONNX/compiler/scheduler/allocator/queue/runtime composition is authorized"),
    "No result in this chapter composes an ONNX/compiler/runtime path": (1, "A result in this chapter composes an ONNX/compiler/runtime path"),
    "Chapter 17 retains quantitative-producer semantics": (1, "Chapter 20 takes quantitative-producer semantics"),
    "Chapter 21 sweep construction": (1, "Chapter 20 takes sweep construction"),
    "Chapter 23 extension procedure": (1, "Chapter 20 takes extension procedure"),
}
ANSWER_SKETCHES = (
    "1. Keep every field claim-specific; a source path or pass count is not a substitute for the route or disproof condition.",
    "2. Use explicit many-to-many edges and record whether each edge is declared, compiled, selected, executed, or interpreted; do not infer one relation from another.",
    "3. Reject non-finite mismatches explicitly, compare matched infinities by sign, state signed-zero policy, define finite absolute/relative tolerance, and use raw bits only where the numerical contract requires them.",
    "4. Select inputs whose consumers produce different observable outputs, gate both branches, and mutate the consumer selection while preserving parsing.",
    "5. Examples include exactly one active owner, bounded occupancy, unchanged ownership on rejection, and reset restoring a named state; verify after every call, not only at suite end.",
    "6. Bind complete initial state, issue each recorded instruction through the real consumer, define visibility/completion, compare far-boundary state, and reject corruption, truncation, unsupported opcodes, and checksum-only no-ops.",
    "7. Use unequal nonsymmetric operands and verify the full output independently at the far boundary; add a one-value mutation and a stale-buffer negative.",
    "8. Treat any nonzero, timeout, missing required output, counted failure, or parser error as non-pass; preserve producer and parser statuses separately and reject contradictions.",
    "9. Rebinding bypasses the identity gate so the semantic set gate itself is exercised; otherwise rejection proves only hash drift.",
    "10. Bind exact inputs and body evidence, bind the manifest and validation layers, mutation-test the validator under normal and optimized execution, review an exact commit, and verify the sealing commit’s parent, paths, member set, and blobs.",
    "11. Unit and mutation controls are cheap and targeted; sanitizers catch reached C memory/UB defects; integration reaches more contracts; RTL comparison addresses lower-level implementation correspondence at much higher cost. None replaces a mismatched claim boundary.",
    "12. Name producer, action, interval, units, clock, reset, formula, and fidelity first; then prove route, input, expected equation, semantic mutation, status, denominator, and provenance without composing incompatible producers.",
)


class ValidationError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return sha_bytes(path.read_bytes())


def run_checked(args, cwd=ROOT, env=None, timeout=240):
    result = subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=timeout)
    require(result.returncode == 0,
            f"command failed {' '.join(map(str, args))}: {result.stdout[-1200:]}")
    return result.stdout


def git_blob(commit, rel):
    result = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    require(result.returncode == 0, f"git blob {commit}:{rel}")
    return result.stdout


def parse_manifest(path, expected, member_root):
    require(path.is_file(), f"missing manifest {path.relative_to(ROOT)}")
    entries = {}
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
    for member, digest in entries.items():
        target = member_root / member
        require(target.is_file(), f"manifest member regular file {member}")
        require(sha(target) == digest, f"manifest digest {member}")
    return entries


def slug(text):
    text = re.sub(r"<[^>]+>", "", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return re.sub(r"[ -]+", "-", text).strip("-")


def headings(path):
    found, counts = set(), {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            base = slug(match.group(1))
            count = counts.get(base, 0)
            found.add(base if count == 0 else f"{base}-{count}")
            counts[base] = count + 1
    return found


def parse_limitations(text):
    blocks = re.split(r"(?m)^### (C20\.\d+) — ", text)[1:]
    result = {}
    for index in range(0, len(blocks), 2):
        claim_id = blocks[index]
        body = blocks[index + 1]
        match = re.search(r"(?m)^- \*\*Limitation wording:\*\* (.+)$", body)
        require(match is not None, f"limitation wording {claim_id}")
        if match is None:
            raise ValidationError(f"limitation wording {claim_id}")
        require(claim_id not in result, f"duplicate limitation {claim_id}")
        result[claim_id] = match.group(1)
    expected = {f"C20.{number}" for number in range(1, 24)}
    require(set(result) == expected, "exact C20.1-C20.23 limitation set")
    return result


def validate_links(text):
    unfenced = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    links = re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", unfenced)
    require(len(links) >= 6, "sufficient manuscript links")
    primary = text.split("## Primary references", 1)
    require(len(primary) == 2 and len(re.findall(r"\]\(", primary[1])) >= 6,
            "primary-reference links")
    for raw in links:
        target = raw.strip().split()[0].strip("<>")
        if target.startswith(("https://", "http://")):
            continue
        require(not target.startswith("/"), f"absolute local link {target}")
        if "#" in target:
            file_part, marker = target.split("#", 1)
        else:
            file_part, marker = target, ""
        resolved = (CHAPTER.parent / file_part).resolve() if file_part else CHAPTER.resolve()
        require(resolved == ROOT or ROOT in resolved.parents, f"link escapes repository {target}")
        require(resolved.is_file(), f"missing link target {target}")
        if marker:
            require(marker in headings(resolved), f"invalid anchor {target}")


def validate_text(text, limitations):
    require(text.startswith("# Chapter 20 — Verification as an Architectural Feature\n"), "title")
    require(PIN in text and INPUT_COMMIT in text and SEAL_COMMIT in text, "edition and seal binding")
    words = len(re.findall(r"\b[\w’'-]+\b", text))
    require(8000 <= words <= 9500, f"word count {words}")
    required_headings = [
        "Learning objectives", "Prerequisite graph", "Opening architecture question",
        "Theory", "Source map", "Coverage is a relation", "Oracle independence",
        "Configuration effect", "Vacuous assertions", "Serialization is not behavioral replay",
        "External boundaries", "Regression delivery", "Worked claim-authorization ledgers",
        "Quantitative claims import Chapter 17", "Preserving evidence",
        "Verification architecture alternatives and trade-offs", "Verification evidence and canonical authority",
        "Common failure modes", "Fidelity box", "Sealed limitation register", "Development questions",
        "Summary", "Review questions", "Review-question answer key", "Design exercises",
        "Exercise answer sketches", "Primary references",
    ]
    actual = [m.group(1).lower() for m in re.finditer(r"^#{2,6}\s+(.+)$", text, re.MULTILINE)]
    for heading in required_headings:
        require(any(heading.lower() in item for item in actual), f"heading {heading}")
    require(len(re.findall(r"^\d+\. ", text.split("## Review questions", 1)[1].split("### Review-question", 1)[0], re.MULTILINE)) == 15,
            "review-question count")
    require(len(re.findall(r"^\d+\. ", text.split("### Review-question answer key", 1)[1].split("## Design exercises", 1)[0], re.MULTILINE)) == 15,
            "answer count")
    require(len(re.findall(r"^\d+\. \*\*", text.split("## Design exercises", 1)[1].split("### Exercise answer sketches", 1)[0], re.MULTILINE)) == 12,
            "exercise count")
    answer_section = text.split("### Exercise answer sketches", 1)[1].split("## Primary references", 1)[0]
    require(len(re.findall(r"^\d+\. ", answer_section, re.MULTILINE)) == 12,
            "exercise-answer-sketch count")
    for answer in ANSWER_SKETCHES:
        require(answer_section.count(answer) == 1, f"exercise-answer content {answer.split('.', 1)[0]}")
    for claim_id, sentence in limitations.items():
        require(text.count(f"| {claim_id} | {sentence} |") == 1,
                f"verbatim limitation register row {claim_id}")
        require(text.count(sentence) == 1, f"unique limitation wording {claim_id}")
    phrases = [
        "Sixty-four C test sources exist", "exactly 31 prerequisite targets",
        "make test prerequisite targets             31",
        "sources named by Make rule prerequisites   59", "CI quick selected targets                    4",
        "CI full selected targets                    14", "source-to-prerequisite omissions             5",
        "hashes=22 predicates=52 checks=75", "fixed seeds `42`, `99`, `777`, and `888`",
        "CONFIG_AB ws_parse=0 os_parse=0 ws_df=0 os_df=1 rt_rows=8 rt_cols=4 ws_active=weight_stationary os_active=weight_stationary direct_os=output_stationary",
        "created_8x4=1 reinitialized_16x16=1 created_bytes=336 reinitialized_bytes=338",
        "DUMP_SIZE fixture=post_reinit_16x16 reported=0 actual=338",
        "REPLAY_NOOP arbitrary_opcode=0xFE mismatches_equal=0 mismatches_mutated=1 output_bytes=69",
        "REPORT_FALSE_GREEN status=PASS passed=0 failed=1 exit_code=-1",
        "native C-to-C wrapper evidence", "No HDL simulator boundary is exercised",
        "no ONNX/compiler/scheduler/allocator/queue/runtime composition is authorized",
        "Chapter 19 remains closed", "Chapter 17 remains authoritative",
        "Chapter 21 owns sweep construction", "Chapter 23 owns extension procedure",
        "debug `25/25` versus meaningful-size mutation `23/25`",
        "error `9/9` versus reached-injection requirement `8/9`",
        "golden `11/11` versus local-equation mutation `2/11`",
        "a fully ASan/UBSan-instrumented archive plus probe",
        "one normal-value 2×2 case does not establish full API coverage",
        "two process executions are one deterministic vector set per fixed seed",
        "serialization and checksum comparison are executable; deterministic instruction re-execution and behavioral replay are rejected",
        "a green result is evidence for a named relation, not a subsystem-wide certificate",
    ]
    for phrase in phrases:
        require(phrase.lower() in text.lower(), f"claim-critical phrase {phrase}")
    unsafe = [
        "Tusim provides an integrated ONNX/compiler/runtime path.",
        "The Python binding proves full API coverage.",
        "The DPI test exercises an HDL simulator.",
        "Recorded traces behaviorally replay instructions.",
        "make test verifies all 64 C test sources.",
        "Chapter 20 redefines the metric producers.",
        "Chapter 20 owns sweep construction.",
        "Chapter 20 owns extension procedure.",
    ]
    for statement in unsafe:
        require(statement.lower() not in text.lower(), f"unsafe affirmative claim {statement}")
    for phrase, (count, _) in CLAIM_OCCURRENCES.items():
        require(text.count(phrase) == count, f"claim occurrence count {phrase}")
    require(not re.search(r"(?m)^\|\|", text), "malformed markdown table row")
    require(not any(line.rstrip() != line for line in text.splitlines()), "trailing whitespace")


def replace_nth(text, old, new, occurrence):
    start = -1
    for _ in range(occurrence + 1):
        start = text.find(old, start + 1)
        require(start >= 0, f"mutation occurrence absent {old}:{occurrence}")
    return text[:start] + new + text[start + len(old):]


def mutation_tests(original, limitations):
    reader_count = 0
    for old, (count, new) in CLAIM_OCCURRENCES.items():
        require(original.count(old) == count, f"mutation source count {old}")
        for occurrence in range(count):
            try:
                validate_text(replace_nth(original, old, new, occurrence), limitations)
            except ValidationError:
                reader_count += 1
                continue
            raise ValidationError(f"manuscript mutation survived: {old}:{occurrence}")
    for answer in ANSWER_SKETCHES:
        replacement = answer.split(".", 1)[0] + ". [deleted]"
        try:
            validate_text(original.replace(answer, replacement, 1), limitations)
        except ValidationError:
            reader_count += 1
            continue
        raise ValidationError(f"exercise-answer mutation survived: {replacement}")
    for claim_id, sentence in limitations.items():
        require(sentence in original, f"limitation mutation source absent {claim_id}")
        try:
            validate_text(original.replace(sentence, sentence + " Broader authority is implied.", 1), limitations)
        except ValidationError:
            continue
        raise ValidationError(f"limitation mutation survived: {claim_id}")
    return reader_count, len(limitations)


def validate_evidence():
    require(RUN.is_dir(), "canonical post-review v2 run directory")
    retained = (RUN / "retained-files.txt").read_text(encoding="utf-8").splitlines()
    require(retained == sorted(retained) and len(retained) == 53, "retained inventory order/count")
    inner_expected = set(retained) | {"retained-files.txt"}
    inner_entries = parse_manifest(RUN / "sha256-retained.txt", inner_expected, RUN)
    parse_manifest(RUN / "bundle-sha256.txt", OUTER_MEMBERS, RUN)
    final_expected = inner_expected | {"sha256-retained.txt", "manifest-check.log", "finalization.log",
                                       "predraft-validation-normal.log", "predraft-validation-optimized.log"} | DERIVED_MEMBERS
    files = {str(path.relative_to(RUN)) for path in RUN.rglob("*") if path.is_file()}
    require(files == final_expected and len(files) == 63, "exact sealed run inventory")
    require(len(inner_entries) == 54, "inner manifest count")
    require(len((RUN / "manifest-check.log").read_text().splitlines()) == 54, "inner manifest check count")
    require(len((RUN / "bundle-check.log").read_text().splitlines()) == 5, "outer manifest check count")
    run_checked(["sha256sum", "-c", "sha256-retained.txt"], cwd=RUN)
    run_checked(["sha256sum", "-c", "bundle-sha256.txt"], cwd=RUN)
    require((RUN / "input_commit").read_text().strip() == INPUT_COMMIT, "input commit")
    require((RUN / "source_pin").read_text().strip() == PIN, "source pin")
    require(sha(RUN / "probe-O0.log") == PROBE_SHA256, "complete canonical probe digest")
    require((RUN / "probe-O0.log").read_bytes() == (RUN / "probe-O2.log").read_bytes(), "probe optimization identity")
    probe = (RUN / "probe-O0.log").read_text()
    for line in PROBE_LINES:
        require(line in probe, f"complete probe line {line}")
    expected_closure = f"CH20_PREDRAFT_VALIDATION PASS run={RUN_ID} input_commit={INPUT_COMMIT} outer=1\n"
    require((RUN / "closure-validation-normal.log").read_text() == expected_closure, "normal closure log")
    require((RUN / "closure-validation-optimized.log").read_text() == expected_closure, "optimized closure log")
    env = os.environ.copy()
    env["CH20_RUN_ID"] = RUN_ID
    validator = str(ROOT / "experiments/ch20_predraft_validate.py")
    for prefix in (["python3"], ["python3", "-O"]):
        run_checked([*prefix, validator, "--outer"], env=env)
        run_checked([*prefix, validator, "--sealed-at", SEAL_COMMIT], env=env)


def validate_repository_state():
    require(run_checked(["git", "branch", "--show-current"]).strip() == "main", "book branch main")
    require(run_checked(["git", "status", "--porcelain", "--untracked-files=all"]).strip() == "", "clean book worktree")
    head = run_checked(["git", "rev-parse", "HEAD"]).strip()
    require(run_checked(["git", "rev-parse", "HEAD"], cwd=TUSIM).strip() == PIN, "Tusim source pin")
    require(run_checked(["git", "branch", "--show-current"], cwd=TUSIM).strip() == "", "Tusim detached")
    require(run_checked(["git", "status", "--porcelain", "--untracked-files=all"], cwd=TUSIM).strip() == "", "Tusim clean")
    if REVIEW_MODE:
        return head
    require(SNAPSHOT.is_file(), "reviewed snapshot marker")
    entries = {}
    for line in SNAPSHOT.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([a-z_]+)=([0-9a-f]{40}|[0-9a-f]{64})", line)
        require(match is not None, "reviewed snapshot syntax")
        if match is None:
            raise ValidationError("reviewed snapshot syntax")
        key, value = match.groups()
        require(key not in entries, f"duplicate reviewed snapshot key {key}")
        entries[key] = value
    require(set(entries) == {"claim_commit", *BIND_PATHS}, "reviewed snapshot keys")
    claim = entries["claim_commit"]
    run_checked(["git", "merge-base", "--is-ancestor", claim, head])
    for key, rel in BIND_PATHS.items():
        blob = git_blob(claim, rel)
        require(sha_bytes(blob) == entries[key], f"reviewed blob marker {rel}")
        require(blob == (ROOT / rel).read_bytes(), f"current blob matches reviewed claim {rel}")
    return claim


def main():
    source = Path(__file__).read_text(encoding="utf-8")
    try:
        parsed = ast.parse(source)
    except SyntaxError as error:
        raise ValidationError(f"invalid validator source: {error}")
    require(not any(isinstance(node, ast.Assert) for node in ast.walk(parsed)),
            "optimizer-removable assertion in validator")
    require(CHAPTER.is_file() and LEDGER.is_file(), "chapter and ledger files")
    live_limitations = parse_limitations(LEDGER.read_text(encoding="utf-8"))
    frozen_limitations = parse_limitations((RUN / "inputs/notes/chapter-20-source-and-claim-ledger.md").read_text(encoding="utf-8"))
    require(live_limitations == frozen_limitations, "live limitations match sealed ledger")
    text = CHAPTER.read_text(encoding="utf-8")
    validate_text(text, frozen_limitations)
    validate_links(text)
    validate_evidence()
    reader_mutations, limitation_mutations = mutation_tests(text, frozen_limitations)
    claim = validate_repository_state()
    words = len(re.findall(r"\b[\w’'-]+\b", text))
    mode = "review" if REVIEW_MODE else "release"
    print(f"CH20_MANUSCRIPT_VALIDATION PASS run={RUN_REL} words={words} inner=54 outer=5 total=63 "
          f"source_checks=75 probe_digest=yes limitations=23 reader_mutations={reader_mutations} "
          f"limitation_mutations={limitation_mutations} total_mutations={reader_mutations + limitation_mutations} optimization_safe=yes "
          f"mode={mode} claim_commit={claim}")


if __name__ == "__main__":
    try:
        main()
    except ValidationError as error:
        raise SystemExit(f"CH20_MANUSCRIPT_VALIDATION FAIL: {error}")
