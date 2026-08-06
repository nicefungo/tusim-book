#!/usr/bin/env python3
"""Optimization-safe release validation for the Chapter 18 manuscript."""
from pathlib import Path
import ast
import hashlib
import os
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "manuscript/part-2-core/18-runtime-context-retention-and-preemption-boundaries.md"
RUN_ID = "20260806-ch18-canonical-v7"
RUN_REL = Path("experiments/runs/ch18-context") / RUN_ID
RUN = ROOT / RUN_REL
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
INPUT_COMMIT = (RUN / "input_commit").read_text(encoding="utf-8").strip() if (RUN / "input_commit").is_file() else ""
PROBE_SHA256 = "88f455134a981e14cead25dc342045e9f96adc47c1314136ec92f71146c9f079"
SNAPSHOT = ROOT / "notes/chapter-18-reviewed-snapshot.txt"
REVIEW_MODE = os.environ.get("CH18_REVIEW_MODE") == "1"
BIND_PATHS = {
    "manuscript_blob": "manuscript/part-2-core/18-runtime-context-retention-and-preemption-boundaries.md",
    "validator_blob": "experiments/ch18_manuscript_validate.py",
    "runner_blob": "experiments/run_ch18_manuscript_validation.sh",
    "ledger_blob": "notes/chapter-18-source-and-claim-ledger.md",
}

INPUT_MEMBERS = {
    "edition.yaml", "PLAN.md", "style-guide.md", "fidelity-matrix.md", "source-audit.md",
    "notes/chapter-18-framing-and-evidence-plan.md",
    "notes/chapter-18-framing-review-dispositions.md",
    "experiments/ch18_framing_reproduce.sh",
    "notes/chapter-18-framing-reproduction.log",
    "notes/chapter-18-source-and-claim-ledger.md",
    "notes/chapter-18-predraft-source-audit-report.md",
    "notes/chapter-18-skeptical-review-dispositions.md",
    "experiments/ch18_source_audit.py", "experiments/ch18_context_probe.c",
    "experiments/ch18_predraft_validate.py", "experiments/run_ch18_context_audit.sh",
}
NON_INPUT_RETAINED = {
    "input-hashes.txt", "input_commit", "source_pin", "tusim-ignored-before.sha256",
    "tusim-ignored-after.sha256", "source-audit.log", "source-audit-pin-mutation.log",
    "source-audit-mutation.log", "source-audit-restored.log", "build.log", "archive-members.log",
    "test-context-readelf.log", "test-context-mut-readelf.log", "test-context-sweep-readelf.log",
    "ch18-probe-readelf.log", "ch18-probe-o2-readelf.log", "ch18-probe-san-readelf.log",
    "test-context.log", "test-context-mutation.log", "test-context-sweep.log", "probe.log",
    "probe-o2.log", "probe-san.log", "probe.stderr.log", "probe-o2.stderr.log", "sanitizer.log",
    "validator-mutation-normal.log", "validator-mutation-optimized.log", "transcript.log",
}
RETAINED_MEMBERS = {"inputs/" + x for x in INPUT_MEMBERS} | NON_INPUT_RETAINED
OUTER_MEMBERS = {"sha256-retained.txt", "manifest-check.log", "finalization.log", "predraft-validation.log"}
FINAL_INVENTORY = RETAINED_MEMBERS | OUTER_MEMBERS | {"sha256-retained.txt", "bundle-sha256.txt", "bundle-check.log"}

COMPACT_PROBE_LINES = [
    "ROW null_api RESULT create=0 alloc=-1 get=0 save=-1 restore=-1 switch=-1 request=-1 schedule=-1 slice=0 block=-1 unblock=-1 getters=0/0",
    "ROW create_invalid RESULT valid=0 null_core=-1 null_cfg=-1 zero=-1 policy=-1 scope=-1 live=-1",
    "ROW allocation_clone RESULT ids=0/1 bytes=31/42 dma=31/42 estimated=100/105 last=0/0",
    "ROW schedule_priority_repeat RESULT first=1 second=1",
    "ROW slice_thresholds RESULT initial=0 c9=0 c10=1 c11=1 reset=0 m2=0 m3=1 m4=1",
    "ROW notify_wrap RESULT cmds=0 cycles=0 expired=0",
    "ROW unblock_all_states RESULT active=0 blocked=0 ready=0 idle=0 completed=0 invalid=-1",
    "ROW malloc_fail_w RESULT calls=1 sizes=64/0/0",
    "ROW malloc_fail_a RESULT calls=2 sizes=64/64/0",
    "ROW malloc_fail_o RESULT calls=3 sizes=64/64/64",
    "ROW malloc_fail_resave RESULT calls=2 sizes=64/64/0",
    "ROW rounding_prng_global RESULT a=0.60181281637875705 b=0.77984955054230642 ref=0.60181281637875705/0.77984955054230642 mode=1 subnormal=0",
    "ROW getters_status RESULT count=0 overhead=0 null=0/0 status_bytes=940",
    "CH18_PROBE SUMMARY failures=0",
]
SWEEP_LINES = [
    "128 full      131072          8292", "128 live25     32768          2148",
    "128 control        0           100", "256 full      262144         16484",
    "256 live25     65536          4196", "256 control        0           100",
    "512 full      524288         32868", "512 live25    131072          8292",
    "512 control        0           100", "16         32868", "32         16484", "64          8292",
]

class ValidationError(Exception):
    pass

def require(condition, message):
    if not condition:
        raise ValidationError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def parse_manifest(path, expected, member_root=RUN):
    require(path.is_file(), f"missing manifest {path.relative_to(ROOT)}")
    entries = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\s]+)", line)
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

def run_checked(args, cwd=ROOT, env=None):
    result = subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=120)
    require(result.returncode == 0, f"command failed {' '.join(args)}: {result.stdout[-500:]}")
    return result.stdout

def slug(text):
    text = re.sub(r"<[^>]+>", "", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return re.sub(r"[ -]+", "-", text).strip("-")

def headings(path):
    found = set()
    counts = {}
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
    require(len(links) >= 15, "sufficient manuscript links")
    primary = text.split("## Primary references", 1)
    require(len(primary) == 2 and len(re.findall(r"\]\(", primary[1])) >= 9, "primary-reference links")
    for raw in links:
        target = raw.strip().split()[0].strip("<>")
        if target.startswith(("https://", "http://")):
            continue
        require(not target.startswith("/"), f"absolute local link {target}")
        file_part, marker = (target.split("#", 1) + [""])[:2] if "#" in target else (target, "")
        resolved = (CHAPTER.parent / file_part).resolve() if file_part else CHAPTER.resolve()
        require(resolved == ROOT or ROOT in resolved.parents, f"link escapes repository {target}")
        require(resolved.is_file(), f"missing link target {target}")
        if "#" in target:
            require(marker != "" and marker in headings(resolved), f"invalid anchor {target}")

def validate_text(text):
    require(text.startswith("# Chapter 18 — Runtime Context Retention and Preemption Boundaries\n"), "title")
    require(PIN in text, "edition pin")
    words = len(re.findall(r"\b[\w'’-]+\b", text))
    require(7500 <= words <= 9000, f"word count {words}")
    required_headings = [
        "Learning objectives", "Prerequisite graph", "Opening architecture question",
        "Theory and terminology", "Source map", "Implementation walk-through",
        "Worked reproducible derivation", "Architecture alternatives and trade-offs",
        "Verification evidence", "Fidelity box", "Common failure modes", "Summary",
        "Review questions", "Review-question answer key", "Design exercises",
        "Exercise answer sketches", "Primary references",
    ]
    actual = [m.group(1).lower() for m in re.finditer(r"^#{2,6}\s+(.+)$", text, re.MULTILINE)]
    for heading in required_headings:
        require(any(heading.lower() in item for item in actual), f"heading {heading}")
    require(len(re.findall(r"^\d+\. ", text.split("## Review questions", 1)[1].split("## Review-question", 1)[0], re.MULTILINE)) == 22, "review-question count")
    require(len(re.findall(r"^\d+\. ", text.split("## Review-question answer key", 1)[1].split("## Design exercises", 1)[0], re.MULTILINE)) == 22, "answer count")
    require(len(re.findall(r"^\d+\. \*\*", text.split("## Design exercises", 1)[1].split("## Exercise answer sketches", 1)[0], re.MULTILINE)) == 10, "exercise count")

    phrases = [
        "corrected canonical v7", "v5 and v6 are retained superseded history", "39 implementation/header/test/config/document hashes",
        "171 structural predicates", "210 source checks", "exactly 19 public APIs",
        "zero external non-test callers", "focused suite `15/15`", "real assertion mutation `14/15`",
        "all 12 sweep rows", "45 lifecycle/ownership/accounting transition labels",
        "CH18_PROBE SUMMARY failures=0", "probe translation unit", "leak-clean ASan/UBSan",
        "caller-established legal boundary", "autonomous or arbitrary-boundary preemption",
        "tu_ctx_request_switch()", "immediately", "does not make it deferred", "active_ctx_id",
        "active_count", "two ACTIVE descriptors", "rejected switching is not failure-atomic",
        "free ACTIVE:             mgr=1/0/0/4 pending=192",
        "free IDLE:               mgr=0/0/1/4",
        "reuse after ACTIVE free: mgr=2/0/0/4 pending=192",
        "direct restore:          mgr=2/1/2/4 switches=1/13",
        "already-ACTIVE reject:   mgr=2/1/1/4 pending=192",
        "ids=0/1 bytes=31/42 dma=31/42 estimated=100/105 last=0/0",
        "18446744073709551611", "first=1 second=1", "9/10/11 -> false/true/true",
        "2/3/4 -> false/true/true", "cmds=0 cycles=0 expired=0", "manager counters to `5/5`",
        "B=B_W+B_A+B_O", "P+B_{in}", "F+\\left\\lceil\\dfrac{2B}{W}",
        "switches=2/20", "switches=2/14", "W as `22/22`", "fixed_switch_cycles=7", "state_bytes_per_cycle=0",
        "`total_size` is saved and restored", "saved per-bank `bw_banks` state is not retained",
        "tu_context.c:122–125", "lines `187`, `204`, and `221` restore",
        "0.60181281637875705", "0.77984955054230642", "process-global `g_tu_dma`",
        "save_dram_state", "has_config_override", "config_override", "user_data",
        "Exactly three retained-copy calls exist", "Under the 64-byte fixture", "64/0/0", "64/64/0", "64/64/64",
        "call-history analytical ledger", "not elapsed switch time", "estimated and uncalibrated",
        "21. Why was v5's `total_size` omission claim false despite passing gates?",
        "default priority `128`", "three 64-byte regions", "B=4+4+4=12",
        "`7+ceil(24/8)=10`", "A synchronous queue returns immediately",
        "not an aggregate `make test` prerequisite", "four-byte W/A/O prefixes",
    ]
    for phrase in phrases:
        require(phrase.lower() in text.lower(), f"claim-critical phrase {phrase}")

    table_rows = [
        "| 128 KiB | FULL | `131072 B` | `100 + ceil(262144/32)` | `8292 cycles` |",
        "| 128 KiB | LIVE25 | `32768 B` | `100 + ceil(65536/32)` | `2148 cycles` |",
        "| 128 KiB | CONTROL | `0 B` | `100 + 0` | `100 cycles` |",
        "| 256 KiB | FULL | `262144 B` | `100 + ceil(524288/32)` | `16484 cycles` |",
        "| 256 KiB | LIVE25 | `65536 B` | `100 + ceil(131072/32)` | `4196 cycles` |",
        "| 256 KiB | CONTROL | `0 B` | `100 + 0` | `100 cycles` |",
        "| 512 KiB | FULL | `524288 B` | `100 + ceil(1048576/32)` | `32868 cycles` |",
        "| 512 KiB | LIVE25 | `131072 B` | `100 + ceil(262144/32)` | `8292 cycles` |",
        "| 512 KiB | CONTROL | `0 B` | `100 + 0` | `100 cycles` |",
        "| `16 B/cycle` | `100 + ceil(524288/16)` | `32868 cycles` |",
        "| `32 B/cycle` | `100 + ceil(524288/32)` | `16484 cycles` |",
        "| `64 B/cycle` | `100 + ceil(524288/64)` | `8292 cycles` |",
    ]
    for row in table_rows:
        require(row in text, f"quantitative table row {row}")

    unsafe = [
        "Tusim supports arbitrary preemption.", "The manager automatically time-slices contexts.",
        "Switch requests execute at the next safe point.", "FULL provides complete tenant isolation.",
        "CONTROL is universally fastest.", "total_cycles_stolen measures elapsed context-switch latency.",
        "SRAM total_size is omitted from save.", "Round-robin guarantees fairness.",
        "Corrected canonical v6 is the sole drafting authority",
        "Canonical v6 establishes these pin-specific claims",
        "Canonical v6 supersedes v5", "v6 establishes bounded pin-specific",
    ]
    for statement in unsafe:
        require(statement.lower() not in text.lower(), f"unsafe affirmative claim {statement}")

def mutation_tests(original):
    mutations = [
        ("39 implementation/header/test/config/document hashes", "38 implementation/header/test/config/document hashes"),
        ("171 structural predicates", "170 structural predicates"),
        ("210 source checks", "209 source checks"), ("exactly 19 public APIs", "exactly 18 public APIs"),
        ("focused suite `15/15`", "focused suite `14/15`"),
        ("real assertion mutation `14/15`", "real assertion mutation `13/15`"),
        ("45 lifecycle/ownership/accounting transition labels", "44 lifecycle/ownership/accounting transition labels"),
        ("| 256 KiB | FULL | `262144 B` | `100 + ceil(524288/32)` | `16484 cycles` |",
         "| 256 KiB | FULL | `262145 B` | `100 + ceil(524288/32)` | `16484 cycles` |"),
        ("| 256 KiB | LIVE25 | `65536 B` | `100 + ceil(131072/32)` | `4196 cycles` |",
         "| 256 KiB | LIVE25 | `65536 B` | `100 + ceil(131072/32)` | `4197 cycles` |"),
        ("free ACTIVE:             mgr=1/0/0/4 pending=192", "free ACTIVE:             mgr=1/0/1/4 pending=192"),
        ("first=1 second=1", "first=1 second=2"),
        ("ids=0/1 bytes=31/42 dma=31/42 estimated=100/105 last=0/0",
         "ids=0/1 bytes=31/43 dma=31/42 estimated=100/105 last=0/0"),
        ("18446744073709551611", "18446744073709551610"),
        ("`total_size` is saved and restored", "`total_size` is not saved or restored"),
        ("saved per-bank `bw_banks` state is not retained", "saved per-bank `bw_banks` state is retained"),
        ("## Fidelity box", "## Fidelity notes"),
        ("21. Why was v5's `total_size` omission claim false despite passing gates?",
         "21. Why was v5's `total_size` omission claim correct despite passing gates?"),
        ("default priority `128`", "default priority `129`"),
        ("three 64-byte regions", "three 65-byte regions"),
        ("B=4+4+4=12", "B=4+4+4=13"),
        ("`7+ceil(24/8)=10`", "`7+ceil(24/8)=11`"),
        ("A synchronous queue returns immediately", "A synchronous queue does not return immediately"),
        ("not an aggregate `make test` prerequisite", "is an aggregate `make test` prerequisite"),
        ("four-byte W/A/O prefixes", "five-byte W/A/O prefixes"),
    ]
    for old, new in mutations:
        require(old in original, f"mutation source absent {old}")
        mutated = original.replace(old, new)
        try:
            validate_text(mutated)
        except ValidationError:
            continue
        raise ValidationError(f"manuscript mutation survived: {old}")
    overclaim = original + "\nTusim supports arbitrary preemption.\n"
    try:
        validate_text(overclaim)
    except ValidationError:
        return len(mutations) + 1
    raise ValidationError("overclaim mutation survived")

def validate_evidence():
    require(RUN.is_dir(), "canonical v7 run directory")
    require((RUN / "input_commit").read_text().strip() == INPUT_COMMIT, "input commit")
    require((RUN / "source_pin").read_text().strip() == PIN, "source pin")
    input_entries = parse_manifest(RUN / "input-hashes.txt", INPUT_MEMBERS, RUN / "inputs")
    retained_entries = parse_manifest(RUN / "sha256-retained.txt", RETAINED_MEMBERS)
    parse_manifest(RUN / "bundle-sha256.txt", OUTER_MEMBERS)
    files = {str(path.relative_to(RUN)) for path in RUN.rglob("*") if path.is_file()}
    require(files == FINAL_INVENTORY, "exact canonical v7 inventory")
    require(len(input_entries) == 16 and len(retained_entries) == 45 and len(files) == 51, "manifest counts")
    require((RUN / "manifest-check.log").read_text().count(": OK\n") == 45, "inner manifest check log")
    require((RUN / "bundle-check.log").read_text().count(": OK\n") == 4, "outer manifest check log")
    run_checked(["sha256sum", "-c", "sha256-retained.txt"], cwd=RUN)
    run_checked(["sha256sum", "-c", "bundle-sha256.txt"], cwd=RUN)
    for member, digest in input_entries.items():
        retained = RUN / "inputs" / member
        require(sha(retained) == digest, f"input digest {member}")
        blob = subprocess.run(["git", "show", f"{INPUT_COMMIT}:{member}"], cwd=ROOT,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        require(blob.returncode == 0 and blob.stdout == retained.read_bytes(), f"input commit binding {member}")
    transcript_digest = sha(RUN / "transcript.log")
    expected_final = (f"FINALIZED_RUN run={RUN_REL} input_commit={INPUT_COMMIT} "
                      f"transcript_sha256={transcript_digest}\n")
    require((RUN / "finalization.log").read_text() == expected_final, "finalization transcript binding")
    predraft_line = (f"CH18_PREDRAFT_VALIDATION PASS run={RUN_REL} input_commit={INPUT_COMMIT} pin={PIN} "
                     "inputs=16 retained=45 apis=19 source_checks=210 focused=15 mutation=14/15 probe_rows=45")
    require((RUN / "predraft-validation.log").read_text().splitlines() == [predraft_line, predraft_line],
            "normal and optimized predraft log")
    probe_lines = set((RUN / "probe.log").read_text().splitlines())
    for probe_name in ["probe.log", "probe-o2.log", "probe-san.log"]:
        require(sha(RUN / probe_name) == PROBE_SHA256, f"complete canonical probe digest {probe_name}")
    for line in COMPACT_PROBE_LINES:
        require(line in probe_lines, f"complete canonical probe line {line}")
    sweep = (RUN / "test-context-sweep.log").read_text()
    for line in SWEEP_LINES:
        require(line in sweep, f"canonical sweep line {line}")
    transcript = (RUN / "transcript.log").read_text()
    for line in [
        "CH18_SOURCE_AUDIT PASS pin=" + PIN + " hashes=39 predicates=171 checks=210",
        "CH18_CALLERS external_nontest=none", "FOCUSED_CONTEXT PASS tests=15",
        "FOCUSED_MUTATION PASS tests=14/15 rc=1", "SWEEP PASS rows=12",
        "PROBE PASS failures=0 probe_translation_unit_O0_O2_match=yes sanitizer_clean=yes bounded=yes",
        "VALIDATOR_MUTATION PASS normal_rc=1 optimized_rc=1",
    ]:
        require(line in transcript, f"canonical transcript line {line}")
    env = os.environ.copy()
    env["CH18_RUN_ID"] = RUN_ID
    run_checked(["python3", str(ROOT / "experiments/ch18_predraft_validate.py")], env=env)
    run_checked(["python3", "-O", str(ROOT / "experiments/ch18_predraft_validate.py")], env=env)

def validate_repository_state():
    branch = run_checked(["git", "branch", "--show-current"]).strip()
    require(branch == "main", "book branch main")
    dirty = run_checked(["git", "status", "--porcelain", "--untracked-files=all"]).strip()
    require(dirty == "", "clean book worktree")
    head = run_checked(["git", "rev-parse", "HEAD"]).strip()
    if REVIEW_MODE:
        return head
    require(SNAPSHOT.is_file(), "reviewed snapshot marker")
    entries = {}
    for line in SNAPSHOT.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([a-z_]+)=([0-9a-f]{40}|[0-9a-f]{64})", line)
        if match is None:
            raise ValidationError("reviewed snapshot syntax")
        key, value = match.groups()
        require(key not in entries, f"duplicate reviewed snapshot key {key}")
        entries[key] = value
    require(set(entries) == {"claim_commit", *BIND_PATHS}, "reviewed snapshot keys")
    claim_commit = entries["claim_commit"]
    require(run_checked(["git", "merge-base", "--is-ancestor", claim_commit, head]) == "",
            "reviewed claim commit ancestry")
    for key, rel in BIND_PATHS.items():
        blob = subprocess.run(["git", "show", f"{claim_commit}:{rel}"], cwd=ROOT,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        require(blob.returncode == 0, f"reviewed claim path {rel}")
        require(hashlib.sha256(blob.stdout).hexdigest() == entries[key], f"reviewed blob marker {rel}")
        require(blob.stdout == (ROOT / rel).read_bytes(), f"current blob matches reviewed claim {rel}")
    return claim_commit

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
    claim_commit = validate_repository_state()
    words = len(re.findall(r"\b[\w'’-]+\b", text))
    mode = "review" if REVIEW_MODE else "release"
    print(f"CH18_MANUSCRIPT_VALIDATION PASS run={RUN_REL} words={words} inputs=16 retained=45 outer=4 "
          f"probe_rows=45 probe_digest=yes mutations={mutation_count} optimization_safe=yes "
          f"mode={mode} claim_commit={claim_commit}")

if __name__ == "__main__":
    try:
        main()
    except ValidationError as error:
        raise SystemExit(f"CH18_MANUSCRIPT_VALIDATION FAIL: {error}")
