#!/usr/bin/env python3
"""Optimization-safe manuscript and release validation for Chapter 19."""
from pathlib import Path
import ast
import hashlib
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "manuscript/part-2-core/19-static-scheduling-and-scratchpad-allocation.md"
RUN_ID = "20260810-ch19-postreview-v3"
RUN_REL = Path("experiments/runs/ch19-static-transforms") / RUN_ID
RUN = ROOT / RUN_REL
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
INPUT_COMMIT = "8d2e459257a6b340ad98f66c82a396a430d69441"
PROBE_SHA256 = "31bdec1f8eea818f463e1f32163e1a2b786b85647f4de6edae340875fc92e598"
SNAPSHOT = ROOT / "notes/chapter-19-reviewed-snapshot.txt"
REVIEW_MODE = os.environ.get("CH19_MANUSCRIPT_REVIEW_MODE") == "1"
TUSIM = Path("/home/zxy/Workplace/projects/tusim")
BIND_PATHS = {
    "manuscript_blob": "manuscript/part-2-core/19-static-scheduling-and-scratchpad-allocation.md",
    "validator_blob": "experiments/ch19_manuscript_validate.py",
    "runner_blob": "experiments/run_ch19_manuscript_validation.sh",
    "ledger_blob": "notes/chapter-19-source-and-claim-ledger.md",
}
INPUTS = {
    "PLAN.md", "style-guide.md", "edition.yaml", "fidelity-matrix.md", "source-audit.md",
    "manuscript/part-2-core/11-instruction-surfaces-and-command-queue-ordering.md",
    "notes/chapter-19-framing-and-evidence-plan.md",
    "notes/chapter-19-source-and-claim-ledger.md",
    "notes/chapter-19-skeptical-review-dispositions.md",
    "experiments/ch19_framing_reproduce.sh", "experiments/ch19_source_audit.py",
    "experiments/ch19_static_transform_probe.c", "experiments/ch19_ubsan_probe.c",
    "experiments/ch19_predraft_validate.py", "experiments/run_ch19_static_transform_audit.sh",
}
ARTIFACTS = {
    "artifacts/input-commit.txt", "artifacts/source-pin.txt", "artifacts/toolchain.txt",
    "artifacts/source-ignored-before.sha256", "artifacts/source-ignored-after.sha256",
    "artifacts/archive-members.txt", "artifacts/negative-control-status.txt", "artifacts/ubsan-status.txt",
}
LOGS = {
    "logs/01-source-audit.log", "logs/02-source-pin-control.log", "logs/03-source-hash-control.log",
    "logs/04-source-restored.log", "logs/05-build.log", "logs/06-focused-scheduler.log",
    "logs/07-focused-liveness.log", "logs/08-scheduler-sweep.log",
    "logs/09-focused-scheduler-readelf.log", "logs/10-focused-liveness-readelf.log",
    "logs/11-scheduler-sweep-readelf.log", "logs/12-static-transform-probe.log",
    "logs/13-ubsan-scheduler.log", "logs/14-ubsan-liveness.log",
    "logs/15-control-scheduler-suite.log", "logs/16-control-liveness-suite.log",
    "logs/17-control-scheduler-identity.log", "logs/18-control-liveness-opcode.log",
    "logs/19-control-spill-accounting.log", "logs/20-validator-control-normal.log",
    "logs/21-validator-control-optimized.log",
}
BODY_MEMBERS = {"INPUT_SHA256SUMS", "REPORT.md"} | ARTIFACTS | LOGS | {"inputs/" + x for x in INPUTS}
OUTER_MEMBERS = {"SHA256SUMS", "manifest-check.log", "finalization.log", "validator-normal.log", "validator-optimized.log"}
FINAL_INVENTORY = BODY_MEMBERS | {"SHA256SUMS", "manifest-check.log", "finalization.log",
                                  "validator-normal.log", "validator-optimized.log",
                                  "BUNDLE_SHA256SUMS", "bundle-check.log"}

class ValidationError(Exception):
    pass

def require(condition, message):
    if not condition:
        raise ValidationError(message)

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def sha(path):
    return sha_bytes(path.read_bytes())

def run_checked(args, cwd=ROOT, env=None, timeout=180):
    result = subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=timeout)
    require(result.returncode == 0, f"command failed {' '.join(map(str, args))}: {result.stdout[-800:]}")
    return result.stdout

def parse_manifest(path, expected, member_root):
    require(path.is_file(), f"missing manifest {path.relative_to(ROOT)}")
    entries = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (?:\./)?([^\s]+)", line)
        require(match is not None, f"malformed manifest line {path.name}:{number}")
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

def validate_links(text):
    unfenced = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    links = re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", unfenced)
    require(len(links) >= 10, "sufficient manuscript links")
    primary = text.split("## Primary references", 1)
    require(len(primary) == 2 and len(re.findall(r"\]\(", primary[1])) >= 6, "primary-reference links")
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

def validate_text(text):
    require(text.startswith("# Chapter 19 — Static Scheduling and Scratchpad Allocation\n"), "title")
    require(PIN in text, "edition pin")
    words = len(re.findall(r"\b[\w'’-]+\b", text))
    require(6200 <= words <= 8000, f"word count {words}")
    required = [
        "Learning objectives", "Prerequisite graph", "Opening architecture question", "Theory",
        "Source map and public surfaces", "Implementation walk-through", "Policy selection", "Value construction",
        "Capacity and placement", "Spill accounting", "Worked reproducible authorization ledger",
        "architecture alternatives", "Verification evidence", "Common failure modes",
        "Fidelity box", "Development questions", "Summary", "Review questions",
        "Review-question answer key", "Design exercises", "Exercise answer sketches", "Primary references",
    ]
    actual = [m.group(1).lower() for m in re.finditer(r"^#{2,6}\s+(.+)$", text, re.MULTILINE)]
    for heading in required:
        require(any(heading.lower() in item for item in actual), f"heading {heading}")
    require(len(re.findall(r"^\d+\. ", text.split("## Review questions", 1)[1].split("### Review-question", 1)[0], re.MULTILINE)) == 10, "review-question count")
    require(len(re.findall(r"^\d+\. ", text.split("### Review-question answer key", 1)[1].split("## Design exercises", 1)[0], re.MULTILINE)) == 10, "answer count")
    require(len(re.findall(r"^\d+\. \*\*", text.split("## Design exercises", 1)[1].split("### Exercise answer sketches", 1)[0], re.MULTILINE)) == 10, "exercise count")
    phrases = [
        "sole predraft authority", RUN_ID, INPUT_COMMIT, "hashes=24 predicates=158 checks=182",
        "focused scheduler `14/14` and liveness `12/12`", "128 numeric-opcode rows",
        "46-entry body manifest and five-entry outer bundle manifest", "final validation under normal and optimized Python",
        "scheduler public APIs: 9; external non-test callers: 0",
        "liveness public APIs: 7; external non-test callers: 0", "scheduler → liveness call bridge: absent",
        "SCHED_POLICY", "asap=NOP,DMA.LOAD", "balanced=DMA.LOAD,NOP", "cycles=5/5/5",
        "SCHED_BARRIER_DIRECTION store_then_compute=1 compute_then_store=0",
        "SCHED_VALIDATE reversed_dependency accepted=1", "SCHED_FANOUT intended=17 producer_succs=16 last_preds=0 first=DMA.LOAD",
        "SCHED_VALIDATE unmatched accepted=1 graph_nodes=2 result_nodes=2",
        "CROSS_STRIDED sched_writes=0/1/0 live_vregs=2", "LIVE_VREG_LIMIT input_defs=129 rc=0 retained=128",
        "LIVE_CAP_UNDERFLOW", "capacity=16 margin=32 valid=1 peak=100 out_n=1 off=0",
        "LIVE_NO_SPILL offsets=0,0 colored=1 spills=0", "LIVE_REBUILD nodes=2->4 matrix_replaced=1 edges=2",
        "LIVE_SPILL_ACCOUNTING", "spilled=1 num_spills=2 spill_bytes=32 colored=0 offset=4294967295",
        "LIVE_PROVENANCE rc=0 valid=1 opcode=RELU dim0=77",
        "LIVE_OUTPUT_LIMIT input=301 rc=0 valid=1 output=512 last_opcode=NOP",
        "do **not** establish an ONNX-to-scheduler-to-allocator-to-runtime pipeline",
        "No bridge converts one representation into the other", "serial source-local estimate",
        "not a DAG critical path", "one value can be counted twice without a backing slot",
        "semantic equivalence between original and transformed sequences", "calibrated latency, throughput, bandwidth, energy, or area",
        "tu_cmodel/isa/tu_scheduler.h", "tu_cmodel/isa/tu_liveness.h", "tests/test_scheduler.c",
        "Executable local composition", "Representation adjacency only",
        "Common representation semantics, complete intended dependencies, a legal order with bijective validation",
    ]
    for phrase in phrases:
        require(phrase.lower() in text.lower(), f"claim-critical phrase {phrase}")
    unsafe = [
        "Tusim provides an integrated compiler/runtime scheduling pipeline.",
        "The scheduler and allocator form an end-to-end compiler path.",
        "valid=true proves semantic equivalence.", "Scheduler barriers are complete fences.",
        "Synthetic DMA operations provide a legal backing store.", "The scheduler estimate is calibrated latency.",
        "Chapter 19 liveness directly supplies Chapter 18 LIVE prefixes.",
        "Spill bytes count distinct transferred bytes.",
        "Integrated only within named local paths",
    ]
    for statement in unsafe:
        require(statement.lower() not in text.lower(), f"unsafe affirmative claim {statement}")

def mutation_tests(original):
    mutations = [
        ("hashes=24 predicates=158 checks=182", "hashes=23 predicates=158 checks=182"),
        ("hashes=24 predicates=158 checks=182", "hashes=24 predicates=157 checks=182"),
        ("hashes=24 predicates=158 checks=182", "hashes=24 predicates=158 checks=181"),
        ("focused scheduler `14/14` and liveness `12/12`", "focused scheduler `13/14` and liveness `12/12`"),
        ("128 numeric-opcode rows", "127 numeric-opcode rows"),
        ("46-entry body manifest and five-entry outer bundle manifest", "45-entry body manifest and five-entry outer bundle manifest"),
        ("scheduler public APIs: 9; external non-test callers: 0", "scheduler public APIs: 8; external non-test callers: 0"),
        ("liveness public APIs: 7; external non-test callers: 0", "liveness public APIs: 6; external non-test callers: 0"),
        ("cycles=5/5/5", "cycles=5/5/6"),
        ("store_then_compute=1 compute_then_store=0", "store_then_compute=1 compute_then_store=1"),
        ("accepted=1 graph_nodes=2 result_nodes=2", "accepted=0 graph_nodes=2 result_nodes=2"),
        ("sched_writes=0/1/0 live_vregs=2", "sched_writes=1/0/0 live_vregs=2"),
        ("input_defs=129 rc=0 retained=128", "input_defs=129 rc=1 retained=128"),
        ("capacity=16 margin=32 valid=1 peak=100 out_n=1 off=0", "capacity=16 margin=32 valid=0 peak=100 out_n=1 off=0"),
        ("offsets=0,0 colored=1 spills=0", "offsets=0,16 colored=1 spills=0"),
        ("nodes=2->4 matrix_replaced=1 edges=2", "nodes=2->2 matrix_replaced=1 edges=2"),
        ("spilled=1 num_spills=2 spill_bytes=32 colored=0 offset=4294967295", "spilled=1 num_spills=1 spill_bytes=16 colored=0 offset=4294967295"),
        ("rc=0 valid=1 opcode=RELU dim0=77", "rc=1 valid=0 opcode=RELU dim0=77"),
        ("input=301 rc=0 valid=1 output=512 last_opcode=NOP", "input=301 rc=1 valid=0 output=512 last_opcode=NOP"),
        ("**Executable local composition**", "**Integrated only within named local paths**"),
        ("Common representation semantics, complete intended dependencies, a legal order with bijective validation", "Checked capacity and widths"),
        ("## 19.13 Fidelity box", "## 19.13 Fidelity notes"),
    ]
    for old, new in mutations:
        require(old in original, f"mutation source absent {old}")
        try:
            validate_text(original.replace(old, new))
        except ValidationError:
            continue
        raise ValidationError(f"manuscript mutation survived: {old}")
    overclaim = original + "\nTusim provides an integrated compiler/runtime scheduling pipeline.\n"
    try:
        validate_text(overclaim)
    except ValidationError:
        return len(mutations) + 1
    raise ValidationError("overclaim mutation survived")

def validate_evidence():
    require(RUN.is_dir(), "canonical post-review v3 run directory")
    input_entries = parse_manifest(RUN / "INPUT_SHA256SUMS", INPUTS, RUN / "inputs")
    body_entries = parse_manifest(RUN / "SHA256SUMS", BODY_MEMBERS, RUN)
    parse_manifest(RUN / "BUNDLE_SHA256SUMS", OUTER_MEMBERS, RUN)
    files = {str(path.relative_to(RUN)) for path in RUN.rglob("*") if path.is_file()}
    require(files == FINAL_INVENTORY, "exact post-review v3 inventory")
    require(len(input_entries) == 15 and len(body_entries) == 46 and len(files) == 53, "manifest counts")
    require(len((RUN / "manifest-check.log").read_text().splitlines()) == 46, "body manifest check log")
    require(len((RUN / "bundle-check.log").read_text().splitlines()) == 5, "outer manifest check log")
    run_checked(["sha256sum", "-c", "SHA256SUMS"], cwd=RUN)
    run_checked(["sha256sum", "-c", "BUNDLE_SHA256SUMS"], cwd=RUN)
    require((RUN / "artifacts/input-commit.txt").read_text().strip() == INPUT_COMMIT, "input commit")
    require((RUN / "artifacts/source-pin.txt").read_text().strip() == PIN, "source pin")
    for rel, digest in input_entries.items():
        retained = RUN / "inputs" / rel
        blob = subprocess.run(["git", "show", f"{INPUT_COMMIT}:{rel}"], cwd=ROOT,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        require(blob.returncode == 0 and blob.stdout == retained.read_bytes(), f"input commit binding {rel}")
        require(sha(retained) == digest, f"input digest {rel}")
    expected_final = (f"FINALIZED_RUN run={RUN_REL} input_commit={INPUT_COMMIT} "
                      f"body_sha256={sha(RUN / 'SHA256SUMS')}")
    require((RUN / "finalization.log").read_text().strip() == expected_final, "finalization binding")
    predraft = (f"CH19_PREDRAFT_VALIDATION PASS stage=pre run={RUN_REL} input_commit={INPUT_COMMIT} "
                f"pin={PIN} inputs=15 body=46 opcode_rows=128 source_checks=182")
    require((RUN / "validator-normal.log").read_text().strip() == predraft, "retained normal validation")
    require((RUN / "validator-optimized.log").read_text().strip() == predraft, "retained optimized validation")
    probe = (RUN / "logs/12-static-transform-probe.log").read_text()
    require(sha(RUN / "logs/12-static-transform-probe.log") == PROBE_SHA256, "complete canonical probe digest")
    require(len(re.findall(r"(?m)^OPCODE_CENSUS op=0x[0-9a-f]{2} ", probe)) == 128, "complete opcode census")
    require("CH19_PROBE SUMMARY failures=0" in probe and "CHECK_FAIL" not in probe, "probe closure")
    env = os.environ.copy()
    env["CH19_RUN_ID"] = RUN_ID
    env["CH19_VALIDATION_STAGE"] = "final"
    run_checked(["python3", str(ROOT / "experiments/ch19_predraft_validate.py")], env=env)
    run_checked(["python3", "-O", str(ROOT / "experiments/ch19_predraft_validate.py")], env=env)

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
        key, value = match.groups()
        require(key not in entries, f"duplicate reviewed snapshot key {key}")
        entries[key] = value
    require(set(entries) == {"claim_commit", *BIND_PATHS}, "reviewed snapshot keys")
    claim = entries["claim_commit"]
    run_checked(["git", "merge-base", "--is-ancestor", claim, head])
    for key, rel in BIND_PATHS.items():
        blob = subprocess.run(["git", "show", f"{claim}:{rel}"], cwd=ROOT,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        require(blob.returncode == 0, f"reviewed claim path {rel}")
        require(sha_bytes(blob.stdout) == entries[key], f"reviewed blob marker {rel}")
        require(blob.stdout == (ROOT / rel).read_bytes(), f"current blob matches reviewed claim {rel}")
    return claim

def main():
    source = Path(__file__).read_text(encoding="utf-8")
    try:
        parsed = ast.parse(source)
    except SyntaxError as error:
        raise ValidationError(f"invalid validator source: {error}")
    require(not any(isinstance(node, ast.Assert) for node in ast.walk(parsed)),
            "optimizer-removable assertion in validator")
    require(CHAPTER.is_file(), "chapter file")
    text = CHAPTER.read_text(encoding="utf-8")
    validate_text(text)
    validate_links(text)
    validate_evidence()
    mutation_count = mutation_tests(text)
    claim = validate_repository_state()
    words = len(re.findall(r"\b[\w'’-]+\b", text))
    mode = "review" if REVIEW_MODE else "release"
    print(f"CH19_MANUSCRIPT_VALIDATION PASS run={RUN_REL} words={words} inputs=15 body=46 outer=5 "
          f"opcode_rows=128 source_checks=182 probe_digest=yes mutations={mutation_count} optimization_safe=yes "
          f"mode={mode} claim_commit={claim}")

if __name__ == "__main__":
    try:
        main()
    except ValidationError as error:
        raise SystemExit(f"CH19_MANUSCRIPT_VALIDATION FAIL: {error}")
