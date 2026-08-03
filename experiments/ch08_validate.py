#!/usr/bin/env python3
"""Mechanical validation for Tusim book Chapter 8 artifacts."""
from __future__ import annotations
import re
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CH = ROOT / "manuscript/part-2-core/08-floating-point-foundations.md"
required = [
    "## Learning objectives", "## Prerequisite graph", "## Opening architecture question",
    "## 8.3 Source map", "## 8.11 Multi-objective precision choices",
    "## 8.12 Executable evidence matrix", "## 8.14 Fidelity box",
    "## 8.15 Common failure modes", "## Summary", "## Review questions",
    "## Design exercises", "## Primary references",
]
text = CH.read_text()
for heading in required:
    assert heading in text, f"missing heading: {heading}"
words = len(re.findall(r"\b\w[\w'’-]*\b", text))
assert 4500 <= words <= 7500, words
assert "e918c80b6fce833cd1fcae97730fa841c2176f25" in text
assert "1,982" in text and "2,046" in text and "65,536" in text
assert "0x0200" in text and "0x38800000" in text and "0x33800000" in text
assert "non-monotonic" in text and "OFP8" in text and "test-full" in text

artifacts = [
    "experiments/ch08_precision_probe.c", "experiments/ch08_precision_audit.py",
    "experiments/ch08_reproduce.sh", "experiments/ch08-reproduction-2026-07-25.log",
    "experiments/ch08-precision-audit-2026-07-25.md",
    "notes/chapter-08-source-and-claim-ledger.md", "references/floating-point.md",
]
for rel in artifacts:
    assert (ROOT / rel).is_file(), rel

for md in [CH, ROOT / "notes/chapter-08-source-and-claim-ledger.md",
           ROOT / "experiments/ch08-precision-audit-2026-07-25.md", ROOT / "README.md"]:
    body = md.read_text()
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", body):
        if target.startswith(("http://", "https://", "#", "/")):
            continue
        clean = target.split("#", 1)[0]
        assert (md.parent / clean).resolve().exists(), f"broken link {md}: {target}"

log = (ROOT / "experiments/ch08-reproduction-2026-07-25.log").read_text()
assert log.rstrip().endswith("REPRODUCTION: PASS")
for gate in ["19/19 tests passed", "20/20 tests passed", "12/12 tests passed", "Results: 14/14 passed",
             "Results: 21/21 passed", "Results: 25/25 passed",
             "9 passed, 0 failed", "11/11 tests passed", "SUMMARY: PASS failures=0"]:
    assert gate in log, gate
assert "SOURCE_AUDIT: PASS (17/17 hashes)" in log
for gate in ["KNOWN_DEFECT_SNAPSHOT", "digest=d56431612d444f4d",
             "second_sub_got=38000000", "full_below_normal_mid=0200",
             "full_above_normal_mid=0200", "ftz_mid_normal=0000",
             "exhaustive_raw=256", "e4_ofp8_decode_mismatches=14", "e5_decode_mismatches=0",
             "e4_subnormal_normal_mid=07", "e5_rtz_overflow=7c",
             "e5_subnormal_normal_mid=03", "CONFIG_EXEC", "test-full non-superset/non-gating",
             "SOURCE_STATE: no tracked/nonignored changes; ignored inventory unchanged"]:
    assert gate in log, gate
assert "libtucmodel.so =>" not in log
for rel in ["experiments/ch08_precision_probe.c", "experiments/ch08_precision_audit.py",
            "experiments/ch08_reproduce.sh"]:
    path = ROOT / rel
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert f"{digest}  {path}" in log, f"stale transcript hash: {rel}"
print(f"CH08_VALIDATION: PASS words={words} artifacts={len(artifacts)}")
