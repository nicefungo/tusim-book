#!/usr/bin/env python3
"""Mechanical validation for Tusim Book Chapter 9 artifacts."""
from pathlib import Path
import hashlib, re
ROOT=Path(__file__).resolve().parents[1]
CH=ROOT/"manuscript/part-2-core/09-memory-hierarchy-and-banked-scratchpads.md"
t=CH.read_text()
required=["## Learning objectives","## Prerequisite graph","## Opening architecture question",
"## 9.3 Tusim's three memory surfaces","## 9.9 Raw-pointer bypass","## 9.12 Multi-objective memory choices",
"## 9.13 Fidelity box","## 9.14 Common failure modes","## Summary","## Review questions",
"## Design exercises","## Primary references"]
for h in required: assert h in t,h
words=len(re.findall(r"\b\w[\w'’-]*\b",t)); assert 3500<=words<=7000,words
for s in ["e918c80b6fce833cd1fcae97730fa841c2176f25","32 banks","four-byte","8×8 B",
          "zero read/write-counter deltas","estimated and uncalibrated"]: assert s in t,s
arts=["experiments/ch09_memory_probe.c","experiments/ch09_memory_audit.py","experiments/ch09_reproduce.sh",
"experiments/ch09-reproduction-2026-07-26.log","experiments/ch09-memory-hierarchy-audit-2026-07-26.md",
"notes/chapter-09-framing-and-evidence-plan.md","notes/chapter-09-source-and-claim-ledger.md"]
for a in arts: assert (ROOT/a).is_file(),a
for md in [CH,ROOT/"experiments/ch09-memory-hierarchy-audit-2026-07-26.md",ROOT/"notes/chapter-09-framing-and-evidence-plan.md",ROOT/"notes/chapter-09-source-and-claim-ledger.md"]:
    body=md.read_text()
    for link in re.findall(r"\[[^]]+\]\(([^)]+)\)",body):
        if link.startswith(("http://","https://","#","/")): continue
        target=link.split("#",1)[0]
        assert (md.parent/target).resolve().exists(),f"broken {md}: {link}"
log=(ROOT/"experiments/ch09-reproduction-2026-07-26.log").read_text()
assert log.rstrip().endswith("REPRODUCTION: PASS")
for gate in ["SOURCE_AUDIT: PASS (24/24 hashes)","10/10 tests passed","19/19 tests passed","20/20 tests passed",
"SRAM_BUDGET bank_count=32 bank_width=4 sequence=0,3,0","ARBITRATION none=10 round_robin=10 priority=10",
"initial_window_omitted_and_clipped=yes","THIRD_SURFACE: cycle-model bank engine source-present",
"preinit_override=erased","tick_refill=no direct_refill=yes reset_refill_state=preserved","requested_banks=8x8B active_banks=32x4B",
"mma_sram_counter_delta=0/0/0","SUMMARY: PASS failures=0",
"SOURCE_STATE: no tracked/nonignored changes; ignored inventory unchanged"]: assert gate in log,gate
assert "libtucmodel.so =>" not in log
for rel in ["experiments/ch09_memory_probe.c","experiments/ch09_memory_audit.py","experiments/ch09_reproduce.sh"]:
    p=ROOT/rel; d=hashlib.sha256(p.read_bytes()).hexdigest(); assert f"{d}  {p}" in log,f"stale hash {rel}"
print(f"CH09_VALIDATION: PASS words={words} artifacts={len(arts)}")
