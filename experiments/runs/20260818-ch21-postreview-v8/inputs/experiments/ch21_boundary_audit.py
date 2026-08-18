#!/usr/bin/env python3
"""Fail-closed negative compiler/runtime-composition audit for Chapter 21."""
from __future__ import annotations
import hashlib,re,sys
from pathlib import Path
PIN="e918c80b6fce833cd1fcae97730fa841c2176f25"
HASHES={"compiler/onnx_to_tu.py":"9308a86a6c7a986c9fa6cfae6f1b147724de5a78cabaf34656e15de4e4713e2b","tu_cmodel/tu_cmodel.c":"542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059"}
CLAIMS=["notes/chapter-21-source-and-claim-ledger.md","notes/chapter-21-predraft-audit-report.md","notes/chapter-21-limitation-register.md","notes/chapter-21-worked-decision-schema.json"]
FORBIDDEN=[r"SUPPORTED_BRIDGE",r"compiler\s+(?:lowers|maps|schedules).{0,80}(?:cmodel|runtime)",r"(?:ONNX|compiler).{0,80}(?:executes|runs).{0,40}(?:through|in).{0,20}(?:cmodel|runtime)"]
def need(ok,msg):
 if not ok: print("CH21_BOUNDARY_AUDIT FAIL "+msg);raise SystemExit(1)
def main():
 need(len(sys.argv)==4,"usage SOURCE PIN BOOK_INPUT_ROOT")
 src,pin,book=Path(sys.argv[1]),sys.argv[2],Path(sys.argv[3]);need(pin==PIN,"pin")
 for rel,d in HASHES.items(): need(hashlib.sha256((src/rel).read_bytes()).hexdigest()==d,"hash:"+rel)
 compiler=(src/"compiler/onnx_to_tu.py").read_text(errors="replace"); cmodel=(src/"tu_cmodel/tu_cmodel.c").read_text(errors="replace")
 need(not re.search(r"(?i)sweep_aspect_ratio|aspect-ratio-alignment-sweep|3\.8%|non-zero remainder|remainder recommendation",compiler),"aspect-compiler-bridge")
 need(not re.search(r"(?i)sweep_aspect_ratio|aspect-ratio-alignment-sweep",cmodel),"aspect-runtime-bridge")
 for rel in CLAIMS:
  text=(book/rel).read_text(errors="replace")
  for pat in FORBIDDEN: need(not re.search(pat,text,re.I|re.S),"unsupported-claim:"+rel)
 print(f"CH21_BOUNDARY_AUDIT PASS pin={pin} source_bridges=0 unsupported_claims=0 claim_files={len(CLAIMS)}")
 return 0
if __name__=="__main__":raise SystemExit(main())
