#!/usr/bin/env python3
"""Optimization-safe manuscript and release validation for Chapter 22."""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "manuscript/part-2-core/22-lessons-from-the-exploration-portfolio.md"
CLAIMS = ROOT / "notes/chapter-22-claim-register.json"
REGISTERS = ROOT / "notes/chapter-22-predraft-registers.json"
SEAL = ROOT / "notes/chapter-22-postreview-seal.json"
RUN_ID = "20260818-ch22-predraft-postreview-v3"
RUN_REL = Path("experiments/runs/ch22-predraft") / RUN_ID
RUN = ROOT / RUN_REL
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
INPUT_COMMIT = "16ab0c21f6cca2d6c6a87589e034acb82f5dafd8"
BUNDLE_COMMIT = "0a3355c2cf88da4c2694d6691f55fc8cdfdd2a73"
BUNDLE_TREE = "022ad6b0107d87b23b6b28b04d717c1f18e2d27f"
TUSIM = Path("/home/zxy/Workplace/projects/tusim")
SNAPSHOT = ROOT / "notes/chapter-22-reviewed-snapshot.txt"
REVIEW_MODE = os.environ.get("CH22_MANUSCRIPT_REVIEW_MODE") == "1"
SELFTEST_CHILD = os.environ.get("CH22_VALIDATOR_SELFTEST_CHILD") == "1"
BIND_PATHS = {
    "manuscript_blob": "manuscript/part-2-core/22-lessons-from-the-exploration-portfolio.md",
    "validator_blob": "experiments/ch22_manuscript_validate.py",
    "runner_blob": "experiments/run_ch22_manuscript_validation.sh",
    "claims_blob": "notes/chapter-22-claim-register.json",
    "registers_blob": "notes/chapter-22-predraft-registers.json",
    "seal_blob": "notes/chapter-22-postreview-seal.json",
}

# Exact reader-visible anchors. Each is independently replaced by the mutation
# control, so repeated or paraphrased conclusions cannot hide a changed site.
CLAIM_MUTATIONS = {
    "46 pinned exploration reports": "45 pinned exploration reports",
    "249 independently reviewed semantic claims": "248 independently reviewed semantic claims",
    "18 retained, 113 qualified, 8 superseded, 76 rejected, and 34 blocked":
        "18 retained, 112 qualified, 8 superseded, 77 rejected, and 34 blocked",
    "eleven noncomposable metric domains": "ten noncomposable metric domains",
    "seven recurring mechanism families": "six recurring mechanism families",
    "eleven mandatory contradiction classes": "ten mandatory contradiction classes",
    "six reconciliation axes and eight producer/units/state rows":
        "five reconciliation axes and eight producer/units/state rows",
    "28 semantic mutations": "27 semantic mutations",
    "81,920/20,480/50,176 linked estimated cycles":
        "81,920/20,481/50,176 linked estimated cycles",
    "58,64,139,154": "58,64,139,155",
    "K=128 requires 64 KiB while K=256 requires 128 KiB":
        "K=128 requires 64 KiB while K=256 requires 64 KiB",
    "160 encoded bytes and 7,811 linked estimated cycles":
        "160 encoded bytes and 7,812 linked estimated cycles",
    "96/80/40": "96/80/41",
    "1.511, 2.001, and 0.536": "1.511, 2.001, and 0.000",
    "606/222 and 222/606": "606/222 and 222/605",
    "five topologies by three policies": "five topologies by two policies",
    "All 249 decisions remain open": "All 249 decisions are closed",
    "No portfolio-wide Pareto frontier exists": "A portfolio-wide Pareto frontier exists",
    "No compiler/runtime/ONNX composition is established":
        "A compiler/runtime/ONNX composition is established",
    "| geometry/balance | 12 | 58 |": "| geometry/balance | 12 | 57 |",
    "| memory/movement | 9 | 52 |": "| memory/movement | 8 | 52 |",
    "covers 21 reports;": "covers 20 reports;",
    "covers 17 reports;": "covers 16 reports;",
    "covers 8 reports.": "covers 7 reports.",
    "| 64 | 32,768 B | 64 KiB |": "| 64 | 32,769 B | 64 KiB |",
    "| 128 | 65,536 B | 64 KiB |": "| 128 | 65,536 B | 128 KiB |",
    "| 256 | 131,072 B | 128 KiB |": "| 256 | 131,072 B | 64 KiB |",
    "| 512 | 262,144 B | 256 KiB |": "| 512 | 262,144 B | 128 KiB |",
    "| 1,024 | 524,288 B | 512 KiB |": "| 1,024 | 524,288 B | 256 KiB |",
    "| 2,048 | 1,048,576 B | 1,024 KiB |": "| 2,048 | 1,048,576 B | 512 KiB |",
    "| 4,096 | 2,097,152 B | 2,048 KiB |": "| 4,096 | 2,097,152 B | 1,024 KiB |",
    "| 8,192 | 4,194,304 B | 4,096 KiB |": "| 8,192 | 4,194,304 B | 2,048 KiB |",
    "DDR4 0.8, DDR5 1.6, and HBM2 8.0 GHz": "DDR4 0.8, DDR5 1.6, and HBM2 4.0 GHz",
    "pattern A: XY=606, YX=222\npattern B: XY=222, YX=606":
        "pattern A: XY=606, YX=223\npattern B: XY=222, YX=606",
    "isolated=94, bottleneck=128, estimated=158":
        "isolated=94, bottleneck=128, estimated=128",
    "FULL=16,484, LIVE25=4,196, and CONTROL=100":
        "FULL=16,484, LIVE25=4,196, and CONTROL=0",
    "FULL becomes 32,868 and 8,292": "FULL becomes 32,868 and 8,291",
    "M=200 has 96.2% useful-slot utilization: only 3.8% local slot waste":
        "M=200 has 92.2% useful-slot utilization: only 3.8% local slot waste",
    "mislabeled execution has delta 67, while an explicitly active OS execution has delta 4 and RS has delta 36":
        "mislabeled execution has delta 67, while an explicitly active OS execution has delta 67 and RS has delta 36",
    "PIPE_LEDGER        seq=8 piped=7 saved=0 speedup=1.142857":
        "PIPE_LEDGER        seq=8 piped=7 saved=1 speedup=1.142857",
    "PIPE_DEPTH1_LEDGER seq=5 piped=3 saved=0 speedup=1.666667":
        "PIPE_DEPTH1_LEDGER seq=5 piped=3 saved=2 speedup=1.666667",
    "PIPE_EMPTY         seq=7 piped=0 saved=0 speedup=inf":
        "PIPE_EMPTY         seq=7 piped=0 saved=7 speedup=inf",
    "softmax stall return       96\nnormalization stall return 80\n elementwise return         40":
        "softmax stall return       95\nnormalization stall return 80\n elementwise return         40",
    "| All-Independent | 16 | 0 | 0 | 4 | ASAP = ALAP = BALANCED |":
        "| All-Independent | 15 | 0 | 0 | 4 | ASAP = ALAP = BALANCED |",
    "| Serial-Chain | 10 | 0 | 0 | 4 | ASAP = ALAP = BALANCED |":
        "| Serial-Chain | 11 | 0 | 0 | 4 | ASAP = ALAP = BALANCED |",
    "| Fan-Out | 21 | 0 | 0 | 6 | ASAP = ALAP = BALANCED |":
        "| Fan-Out | 20 | 0 | 0 | 6 | ASAP = ALAP = BALANCED |",
    "| Fan-In | 12 | 0 | 0 | 6 | ASAP = ALAP = BALANCED |":
        "| Fan-In | 13 | 0 | 0 | 6 | ASAP = ALAP = BALANCED |",
    "| Pipeline-Tiles | 28 | 0 | 0 | 13 | ASAP = ALAP = BALANCED |":
        "| Pipeline-Tiles | 27 | 0 | 0 | 13 | ASAP = ALAP = BALANCED |",
    "RNE produces FP16 bits `0x3c01` and RTZ `0x3c00`":
        "RNE produces FP16 bits `0x3c00` and RTZ `0x3c00`",
    "A hash proves which bytes were reviewed. It cannot prove that a local equation represents silicon.":
        "A hash proves both reviewed bytes and physical silicon accuracy.",
    "They do not select the opposite alternative.": "They select the opposite alternative.",
    "A global frontier would encode arbitrary normalization rather than evidence.":
        "A global frontier is authorized by the current objectives.",
    "Route both at-fit and above-fit capacities through the same executable hierarchy and tiler.":
        "Assume above-fit capacity is always better.",
    "Use a dependency graph where legal reorderings change a declared order-sensitive objective":
        "Use the existing policy-insensitive serial sum",
    "Attention performance remains blocked after arithmetic repair until arbitrary-input output correctness is restored.":
        "Attention performance is authorized before output correctness is restored.",
    "Anchored historical producer: standalone topology report formula `hops × (latency + payload/BW)` in `traffic_heuristic_cycles`":
        "Anchored historical producer: current barrier owner in `traffic_heuristic_cycles`",
    "eight exact reported rows": "eight exact threshold rows",
    "K=64, the 32 KiB arithmetic footprint falls below the sweep's 64 KiB floor":
        "K=64 exactly fits the sweep's 64 KiB floor",
    "claim `C22R-R1`; canonically `qualified` in M7 producer/metric hazards":
        "claim `C22R-C1`; canonically `qualified` in M7 producer/metric hazards",
    "claims `C22R-N5.1` (`retained`, M6), `C22R-N5.2` (`qualified`, M4), and `C22R-N5.3` (`qualified`, M7)":
        "claim `C22R-N5.3` (`qualified`, M7)",
    "claims `C22R-X2` (`retained`, M7), `C22R-X3` (`qualified`, M7), and `C22R-X6` (`qualified`, M4)":
        "claim `C22R-X6` (`qualified`, M4)",
    "claims `C22R-O10.1` (`qualified`, M6) and `C22R-O10.2` (`rejected`, M2)":
        "claim `C22R-O10.1` (`qualified`, M6)",
    "O10.2 remains assigned to M2 and is used here only as a cross-family qualification; it is not reassigned to M6":
        "O10.2 is reassigned to M6",
    "exact footprint arithmetic; seven grid-exposed thresholds plus one K=64 floor-censored row":
        "exact fixture fit thresholds",
    "The GBUF footprint boundary is exact under its byte equation, but a minimum reported capacity can be floor-censored, as K=64 is in this sweep":
        "A GBUF fit threshold is exact under its byte equation",
    "the minimum tested capacity is not always the arithmetic boundary: K=64 is floor-censored at the sweep's 64 KiB minimum":
        "the tested capacity is always the exact arithmetic boundary",
    "eight GBUF reported rows, with K=64 floor-censored by the 64 KiB sweep minimum":
        "eight GBUF reported rows, with K=64 exactly fitting the 64 KiB arithmetic boundary",
}

REQUIRED_EXTERNAL_URLS = (
    "https://doi.org/10.1145/1498765.1498785",
    "https://doi.org/10.1109/4235.996017",
    "https://doi.org/10.1371/journal.pcbi.1003285",
    "https://www.rfc-editor.org/rfc/rfc8493",
    "https://doi.org/10.1109/MC.2003.1178050",
    "https://doi.org/10.1145/1508244.1508275",
    "https://doi.org/10.1145/5666.5673",
)

ANCHOR_CARDS = (
    ("C22R-pddf-keep-depth-low", "qualified", "M1-fixed-cost-amortization"),
    ("C22R-obuf-threshold64", "qualified", "M2-resource-thresholds"),
    ("C22R-dmaq-third-channel-zero", "qualified", "M3-bandwidth-compute-balance"),
    ("C22R-T7", "superseded", "M4-distribution-placement"),
    ("C22R-aspect-m200-near-aligned", "qualified", "M5-shape-placement-reversal"),
    ("C22R-O10.1", "qualified", "M6-state-scope-obligations"),
    ("C22R-P1", "retained", "M7-producer-metric-hazards"),
)

SECONDARY_CLAIMS = (
    ("C22R-N5.1", "retained", "M6-state-scope-obligations"),
    ("C22R-N5.2", "qualified", "M4-distribution-placement"),
    ("C22R-N5.3", "qualified", "M7-producer-metric-hazards"),
    ("C22R-R1", "qualified", "M7-producer-metric-hazards"),
    ("C22R-X2", "retained", "M7-producer-metric-hazards"),
    ("C22R-X3", "qualified", "M7-producer-metric-hazards"),
    ("C22R-X6", "qualified", "M4-distribution-placement"),
    ("C22R-O10.1", "qualified", "M6-state-scope-obligations"),
    ("C22R-O10.2", "rejected", "M2-resource-thresholds"),
)

REQUIRED_HEADINGS = (
    "Learning objectives", "Prerequisite graph", "Opening architecture question",
    "Theory", "Source map", "Portfolio evidence gate", "Worked family",
    "Alternatives and trade-offs", "Stale conclusions and negative evidence",
    "Verification evidence", "Fidelity box", "Common failure modes",
    "Development questions", "Summary", "Review questions",
    "Review-question answer key", "Design exercises", "Exercise answer sketches",
    "Primary references",
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
    result = subprocess.run(args, cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=timeout)
    require(result.returncode == 0,
            f"command failed {' '.join(map(str, args))}: {result.stdout[-1600:]}")
    return result.stdout


def git_output(args, cwd=ROOT) -> str:
    return run_checked(["git", *args], cwd=cwd).strip()


def git_blob(commit: str, rel: str) -> bytes:
    result = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=30)
    require(result.returncode == 0, f"git blob {commit}:{rel}")
    return result.stdout


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


def validate_links(text: str) -> None:
    unfenced = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    links = re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", unfenced)
    require(len(links) >= 18, "sufficient manuscript links")
    for required in REQUIRED_EXTERNAL_URLS:
        require(text.count(required) == 3, f"primary-source URL/count {required}")
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


def validate_worked_families(text: str) -> int:
    matches = list(re.finditer(r"(?m)^## 22\.\d+ Worked family \d+[^\n]*$", text))
    require(5 <= len(matches) <= 7, f"worked-family count {len(matches)}")
    for index, match in enumerate(matches):
        next_heading = re.search(r"(?m)^## 22\.\d+ ", text[match.end():])
        end = match.end() + next_heading.start() if next_heading else len(text)
        section = text[match.start():end]
        for field in ("Workload and correctness/continuation contract", "Local objective",
                      "Exact evidence label", "Producer, metric, units, and initial state",
                      "Binding modeled constraint", "Canonical disposition", "Alternatives",
                      "Gains and sacrifices", "Decisive unknowns", "Open outcome",
                      "Reversal condition"):
            require(section.count(field) == 1,
                    f"worked-family {index + 1} field/count {field}")
        claim_id, disposition, _family = ANCHOR_CARDS[index]
        require(f"| Exact evidence label | `{claim_id}`" in section,
                f"worked-family {index + 1} anchor claim")
        require(f"| Canonical disposition | `{disposition}`" in section,
                f"worked-family {index + 1} anchor disposition")
    return len(matches)


def validate_text(text: str) -> tuple[int, int]:
    require(text.startswith("# Chapter 22 — Lessons from the Exploration Portfolio\n"), "title")
    require(PIN in text and INPUT_COMMIT in text and BUNDLE_COMMIT in text, "edition and seal binding")
    words = len(re.findall(r"\b[\w’'-]+\b", text))
    require(6800 <= words <= 9500, f"word count {words}")
    actual = [m.group(1).lower() for m in re.finditer(r"(?m)^#{2,6}\s+(.+)$", text)]
    for heading in REQUIRED_HEADINGS:
        require(any(heading.lower() in item for item in actual), f"heading {heading}")
    families = validate_worked_families(text)
    for old in CLAIM_MUTATIONS:
        require(text.count(old) == 1, f"mutation-gated phrase/count {old}")
    require(not re.search(r"canonically\s+`?(?:retained|qualified|superseded|rejected|blocked)/",
                          text, flags=re.IGNORECASE), "no slash-combined canonical disposition")
    forbidden = (
        "Tusim proves the optimal architecture portfolio.",
        "The report cycles share one common timeline.",
        "The estimates are calibrated to silicon.",
        "Tusim provides an integrated ONNX/compiler/runtime path.",
        "CONTROL is end-to-end fastest.",
        "The fused activation path delivers a 2–7× speedup.",
    )
    for statement in forbidden:
        require(statement.lower() not in text.lower(), f"unsafe affirmative claim {statement}")
    require(not re.search(r"(?m)^\|\|", text), "malformed markdown table row")
    require(not any(line.rstrip() != line for line in text.splitlines()), "trailing whitespace")
    return words, families


def mutation_tests(original: str) -> int:
    detected = 0
    for old, new in CLAIM_MUTATIONS.items():
        require(original.count(old) == 1, f"mutation source {old}")
        try:
            mutated = original.replace(old, new, 1)
            validate_text(mutated)
            validate_links(mutated)
        except ValidationError:
            detected += 1
        else:
            raise ValidationError(f"manuscript mutation survived: {old}")
    for url in REQUIRED_EXTERNAL_URLS:
        mutated = original.replace(url, "https://invalid.example/changed")
        try:
            validate_text(mutated)
            validate_links(mutated)
        except ValidationError:
            detected += 1
        else:
            raise ValidationError(f"citation mutation survived: {url}")
    return detected


def validate_evidence() -> tuple[dict, dict]:
    require(RUN.is_dir() and not RUN.is_symlink(), "canonical postreview-v3 run")
    seal = json.loads(SEAL.read_text(encoding="utf-8"))
    require(seal == {
        "authorization_scope": "Chapter 22 manuscript drafting under the closed constraint-first framing; evidence changes require a new seal.",
        "bundle_commit": BUNDLE_COMMIT,
        "bundle_tree": BUNDLE_TREE,
        "claim_register_sha256": "a1a7c63a11458830e8dc33d176bbca2e18f267eb7d93753afc551daa3736c8ae",
        "inner_manifest_sha256": "c93d55e369902fb8737cb3e7de4a3fc28501e1fb366cc02fea213bd7b7f75746",
        "input_book_commit": INPUT_COMMIT,
        "predraft_registers_sha256": "181d2a3ab5cc108b64e063d564a2313b709b7ff292a9f1de49d0136b6139b5bf",
        "prose_authorized": True,
        "review_dispositions_sha256": "6e33fdbb18922fcf76b2332b440d942dfe08e953007fbdbd2f310c1c21c68650",
        "run_id": RUN_ID,
        "schema": "ch22-postreview-outer-seal-v1",
        "sha256sums_sha256": "6dc37f5d4b61b43eacb89b7954d4e9ef3def5eb1b441e930615dda0b8304cab7",
        "status": "green",
        "tusim_commit": PIN,
    }, "exact outer seal")
    require(sha(CLAIMS) == seal["claim_register_sha256"], "live claim register hash")
    require(sha(REGISTERS) == seal["predraft_registers_sha256"], "live predraft register hash")
    require(git_output(["rev-parse", f"{BUNDLE_COMMIT}:{RUN_REL.as_posix()}"]) == BUNDLE_TREE,
            "bundle commit tree")
    require(git_output(["rev-parse", f"HEAD:{RUN_REL.as_posix()}"]) == BUNDLE_TREE,
            "current immutable bundle tree")
    verification = run_checked([str(ROOT / "experiments/run_ch22_predraft_evidence_audit.sh"),
                                "verify", RUN_ID])
    receipt = json.loads(verification.strip().splitlines()[-1])
    require(receipt == {"outer_seal": True, "payload_members": 38,
                        "run": str(RUN_REL), "verify": "PASS"},
            "side-effect-free predraft verification receipt")
    claims = json.loads(CLAIMS.read_text(encoding="utf-8"))
    registers = json.loads(REGISTERS.read_text(encoding="utf-8"))
    require(claims["summary"] == {
        "all_decisions_open": True,
        "all_local_dominance_ineligible": True,
        "claim_count": 249,
        "metric_domain_count": 11,
        "report_count": 46,
        "status_counts": {"blocked": 34, "qualified": 113, "rejected": 76,
                          "retained": 18, "superseded": 8},
    }, "exact claim summary")
    require(registers["summary"]["mandatory_contradiction_classes"] == 11,
            "contradiction count")
    require(registers["summary"]["reconciliation_rows"] == 8,
            "reconciliation row count")
    require(len(registers["recurring_regime_register"]) == 7, "recurring family count")
    claim_by_id = {claim["id"]: claim for claim in claims["claims"]}
    for claim_id, disposition, family in (*ANCHOR_CARDS, *SECONDARY_CLAIMS):
        require(claim_id in claim_by_id, f"anchor claim exists {claim_id}")
        row = claim_by_id[claim_id]
        require(row["canonical_disposition"] == disposition,
                f"anchor disposition {claim_id}")
        require(row["mechanism_family"] == family, f"anchor family {claim_id}")
    return claims, registers


def validate_self_mutation() -> None:
    if SELFTEST_CHILD:
        return
    source = Path(__file__).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="ch22-validator-") as temp:
        mutated = Path(temp) / "ch22_manuscript_validate.py"
        mutated.write_text(source + "\nassert(False)\n", encoding="utf-8")
        env = os.environ.copy()
        env["CH22_VALIDATOR_SELFTEST_CHILD"] = "1"
        env["CH22_MANUSCRIPT_REVIEW_MODE"] = "1"
        for prefix in (["python3"], ["python3", "-O"]):
            result = subprocess.run([*prefix, str(mutated)], cwd=ROOT, env=env,
                                    text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=90)
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
    require(git_output(["status", "--porcelain", "--untracked-files=all"]) == "",
            "clean book worktree")
    if REVIEW_MODE:
        return head
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
    require(CHAPTER.is_file() and CLAIMS.is_file() and REGISTERS.is_file() and SEAL.is_file(),
            "chapter and evidence inputs")
    validate_evidence()
    text = CHAPTER.read_text(encoding="utf-8")
    words, families = validate_text(text)
    validate_links(text)
    mutations = mutation_tests(text)
    validate_self_mutation()
    claim = validate_repository_state()
    mode = "review" if REVIEW_MODE else "release"
    print(f"CH22_MANUSCRIPT_VALIDATION PASS run={RUN_REL} words={words} families={families} "
          f"reports=46 claims=249 metric_domains=11 contradictions=11 evidence_mutations=28 "
          f"reader_mutations={mutations} optimization_safe=yes mode={mode} claim_commit={claim}")


if __name__ == "__main__":
    try:
        main()
    except ValidationError as error:
        raise SystemExit(f"CH22_MANUSCRIPT_VALIDATION FAIL: {error}")
