#!/usr/bin/env python3
import hashlib
import os
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUN_ID=os.environ.get("CH16_RUN_ID","20260804-ch16-canonical-v1")
RUN=ROOT/"experiments/runs/ch16-double-buffer"/RUN_ID
PIN="e918c80b6fce833cd1fcae97730fa841c2176f25"

def require(cond,msg):
    if not cond: raise SystemExit(f"CH16_PREDRAFT_VALIDATION FAIL {msg}")
def text(rel):
    p=RUN/rel; require(p.is_file(),f"missing {rel}"); return p.read_text(errors="replace")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

require(RUN.is_dir(),f"missing run {RUN}")
input_commit=text("input_commit").strip()
require(len(input_commit)==40,"input commit shape")
require(text("source_pin").strip()==PIN,"source pin")
trans=text("transcript.log")
for line in [
 f"CH16_SOURCE_AUDIT PASS pin={PIN} hashes=25 predicates=42 checks=67",
 "SOURCE_HASH_MUTATION PASS rc=1",
 "STATIC_LINK PASS binaries=2",
 "FOCUSED_DOUBLE_BUFFER PASS tests=10",
 "FOCUSED_MUTATION PASS",
 "BOUNDED_PROBE PASS",
 "REPORT_RECOMPUTE PASS",
 "PIPELINE_SUITE_QUALIFIED not_executed=fixed_channels_3_requested_4",
 "CH16_AUDIT_BODY_COMPLETE",
]: require(line in trans,f"transcript gate {line}")
require("CH16_AUDIT PASS" not in trans,"runner whole-audit success forbidden")
require("=== Results: 10/10 passed, 0 failed ===" in text("test-double.log"),"focused count")
require("exited normally" in text("test-double.log"),"focused inferior")
mut=text("test-double-mutation.log")
require("=== Results: 9/10 passed, 1 failed ===" in mut,"mutation count")
require("exited with code 01" in mut,"mutation inferior")
probe=text("probe.log")
for line in [
 "DB_CLEAN_SWAP count=1 active_idx=1 active=00 shadow=11 dirty=0",
 "DB_NOTIFY_ONLY shadow_before=00 shadow_after=00 dirty=1 bytes=1016 dma_cycles=82",
 "DB_SHARED_METER first=0 second=2 active_value=00000000 bank0_words=0",
 "DB_DISABLE enabled=0 primary=44 db_null=1",
 "PIPE_AFTER stage=2 completed=1 desc_cycles=53 pipe_cycle=0 dma_cycle=1 active=22 shadow=7a swapped=1 dirty=1",
 "PIPE_LEDGER tiles=1 load=2 compute=5 seq=8 piped=7 saved=0 speedup=1.142857 pipe_cycle=6",
 "PIPE_DEPTH1_NOLOAD tid=0 active=00 shadow=55 swaps=1 dirty=0 stage=2",
 "PIPE_DEPTH1_LEDGER seq=5 piped=3 saved=0 speedup=1.666667",
 "PIPE_EMPTY tid=0 seq=7 piped=0 saved=0 speedup=inf overlap_load=0 overlap_store=0",
 "PIPE_RESET initialized=0 depth=2 slots_null=1 free_slots=1",
 "PIPE_AFTER_RESET_SUBMIT tid=0 depth=1 initialized=1 stored_cmd=123",
 "CH16_PROBE SUMMARY failures=0",
 "exited normally",
]: require(line in probe,f"probe gate {line}")
recomp=text("report-recompute.log")
require(recomp.count("CH16_SWEEP okb=")==10,"recompute rows")
for line in [
 "CH16_SWEEP_CAPACITY single64_kib=64 double16_physical_kib=32 ratio=2.0",
 "CH16_SWEEP_PORT_CHECK independent_256pe_two_fp16_bytes_per_cycle=1024 report_claim=512",
 "CH16_SWEEP_THRESHOLD report=20 exact=17 continuous=18.285714",
 "CH16_SWEEP SUMMARY failures=0 rows=10",
]: require(line in recomp,f"recompute gate {line}")
require("double_buffer.o" in text("archive-members.log") and "pipeline_controller.o" in text("archive-members.log"),"archive members")
require("libtucmodel" not in ''.join(l for l in text("test-double-readelf.log").splitlines() if "NEEDED" in l),"focused static link")
require("libtucmodel" not in ''.join(l for l in text("probe-readelf.log").splitlines() if "NEEDED" in l),"probe static link")

# Bind every frozen input to the input commit.
for p in sorted((RUN/"inputs").rglob("*")):
    if not p.is_file(): continue
    rel=p.relative_to(RUN/"inputs").as_posix()
    got=subprocess.run(["git","show",f"{input_commit}:{rel}"],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    require(got.returncode==0,f"input not in commit {rel}")
    require(hashlib.sha256(got.stdout).hexdigest()==sha(p),f"input commit mismatch {rel}")

# Verify inner manifest exactly and reject build artifacts.
manifest=text("sha256-retained.txt").splitlines()
for line in manifest:
    digest,rel=line.split("  ",1)
    p=RUN/rel
    require(p.is_file(),f"manifest missing {rel}")
    require(sha(p)==digest,f"manifest hash {rel}")
for pat in ("*.o","*.a","*.so","*.tar","core*"):
    require(not list(RUN.rglob(pat)),f"forbidden artifact {pat}")
require("FINALIZED_RUN" in text("finalization.log"),"finalization marker")
print(f"CH16_PREDRAFT_VALIDATION PASS files={len(manifest)} run={RUN.relative_to(ROOT)} input_commit={input_commit}")
