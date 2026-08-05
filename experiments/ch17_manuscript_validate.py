#!/usr/bin/env python3
"""Fail-closed manuscript/evidence/link checks for Chapter 17."""
from pathlib import Path
import ast,os,re,subprocess

ROOT=Path(__file__).resolve().parents[1]
CHAPTER=ROOT/"manuscript/part-2-core/17-measurement-surfaces-counters-tracing-cycle-models-and-energy.md"
RUN_ID="20260805-ch17-canonical-v4"
RUN=ROOT/"experiments/runs/ch17-measurement"/RUN_ID
PIN="e918c80b6fce833cd1fcae97730fa841c2176f25"
TUSIM=Path("/home/zxy/Workplace/projects/tusim")

def require(c,m):
    if not c: raise SystemExit(f"CH17_MANUSCRIPT_VALIDATION FAIL: {m}")
def has_assert(source):
    try: return any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(source)))
    except SyntaxError as e: raise SystemExit(f"CH17_MANUSCRIPT_VALIDATION FAIL: invalid validator source: {e}")
def slug(x):
    x=re.sub(r"<[^>]+>","",x).strip().lower()
    x=re.sub(r"[^\w\- ]","",x,flags=re.UNICODE)
    return re.sub(r"[ -]+","-",x).strip("-")

def validate_text(s):
    require(s.startswith("# Chapter 17 — Measurement Surfaces: Counters, Tracing, Cycle Models, and Energy\n"),"title")
    require(PIN in s,"pin")
    words=len(re.findall(r"\b[\w'’-]+\b",s))
    require(4500 <= words <= 8000,f"word count {words}")
    low=s.lower()
    required=["Learning objectives","Prerequisite graph","Opening architecture question","Theory",
              "Source map","Implementation","Worked example","Trade-offs","Verification","Fidelity box",
              "Common failure modes","Summary","Review questions","answer key","Design exercises","Primary references"]
    for x in required: require(x.lower() in low,x)
    phrases=[
      "canonical v4","31 source/config/test/document hashes","96 structural predicates","127 total checks",
      "12/12","31/31","7/7","20/20","21/21","11/12","failures=0",
      "producer","event_or_action","interval_start_and_end","clock_or_timestamp_owner","fidelity",
      "perf_additive total=18","after_explicit_tick=24","internal dma adds active cycles","descriptor helper",
      "perf_reset enabled=1 freq=777 energy_mac=99.0 total=0",
      "destination's clock and enable state","bandwidth_gb/s","mac_throughput_tops","mac efficiency",
      "energy_per_mac","spad hit rate","reported_power_mw=1000.0 physical_power_mw=1.0",
      "event-trace","logging trace","first_cycle=0 dirty=1 enabled=0","65,536","strict increase",
      "absent from `tu_objs`","cycle_est tile=14","cycle_write cycles=15","cycle_bridge cm=20 perf=20",
      "isolated_stall=0 reads=1 conflicts=1","read_arg=21 write_arg=28",
      "1.051648 mm²","425.7224 pj","42.57224 mw","18446744073709551606",
      "trace_max_events","detailed_stalls","default-only","retained-only","decorative",
      "100 b / 10 ns = 10 gb/s","0.001 tmac/s","0.002 tops","two operations per mac",
      "2.0000 pj","0.4000 pj","370.0000 pj","0.6400 pj","0.1000 pj","52.5824 pj",
      "hbm2e, hbm3, ddr4, ddr5, and lpddr5","1800, 3200, or 1600 mhz","estimated","not integrated","no integrated common timeline","assert(false)",
      "returned pass with no block, major, minor, or nit findings","the public descriptor helper composes dma time with optional spad-stall time",
    ]
    for x in phrases: require(x.lower() in low,x)
    claim_lines=[
      "PERF_ADDITIVE total=18 wall_ns=18 dma_read=64 dma_stall=2 compute=6 macs=8 leak=0.018",
      "PERF_DUPLICATE after_explicit_tick=24 compute=6",
      "PERF_RESET enabled=1 freq=777 energy_mac=99.0 total=0",
      "PERF_METRICS dma_gbps=10.000 tops=0.001000 efficiency=0.003906250 util=0.500 hit=1.000",
      "PERF_UNBOUNDED efficiency=2.0 hit=-1.0 reported_power_mw=1000.0 physical_power_mw=1.0 cached_total=0.0",
      "TRACE_CONTEXT first_cycle=0 dirty=1 enabled=0","TRACE_CONTEXT second_cycle=3 dirty=0",
      "TRACE_LOG count=2 first=0 second=9 global=9",
      "CYCLE_EST tile=14 current=14",
      "CYCLE_WRITE cycles=15 cm=15 perf=15 read_bytes=32 write_bytes=0 read_cycles=15 write_cycles=0",
      "CYCLE_BRIDGE cm=20 perf=20",
      "CYCLE_BANK isolated_stall=0 reads=1 conflicts=1 utilization=0.500",
      "CYCLE_DMA_DIRECTION read_arg=21 write_arg=28 write_perf_read=4 write_perf_write=0",
      "POWER_TABLE area=1.051648 mac=2.000 spad=0.400 dram=370.000 dma=0.640 clock=0.100 leak=52.5824 total=425.7224 avg_mw=42.5722",
      "POWER_DECREASING_DIFF cycles=18446744073709551606 macs=18446744073709551606 energy_mac=-2.000",
    ]
    for x in claim_lines: require(x in s,"claim line: "+x)
    banned=[
      "therefore tusim has one unified cycle counter","the cycle_accurate enum proves calibration",
      "the vcd timescale proves physical nanoseconds","all shipped measurement configuration fields affect execution",
      "the power tables are cacti-calibrated","the benchmark validates application performance",
      "perf reset preserves the disabled state","all derived metrics use cycles and frequency as one common denominator",
      "the two trace apis are one shared stream","ordinary workloads integrate the standalone cycle model",
    ]
    for x in banned: require(x.lower() not in low,f"banned: {x}")
    q=s[low.index("## review questions"):]
    require(len(re.findall(r"^\d+\. ",q,re.M))>=14,"review questions")
    d=s[low.index("## design exercises"):]
    require(len(re.findall(r"^\d+\. \*\*",d,re.M))>=8,"design exercises")
    return words

def validate_links(s):
    for link in re.findall(r"\[[^]]+\]\(([^)]+)\)",s):
        if link.startswith(("http://","https://","/")): continue
        target_text,_,frag=link.partition("#")
        target=CHAPTER if not target_text else (CHAPTER.parent/target_text).resolve()
        require(target.exists(),f"link {link}")
        if frag:
            hs=re.findall(r"^#{1,6}\s+(.+?)\s*$",target.read_text(),re.M)
            require(frag in {slug(h) for h in hs},f"anchor {link}")

require(not has_assert(Path(__file__).read_text()),"optimizer-removable assertion in validator")
require(CHAPTER.is_file(),CHAPTER)
s=CHAPTER.read_text(); words=validate_text(s); validate_links(s)
mutations=[
 ("PERF_ADDITIVE total=18","PERF_ADDITIVE total=19"),
 ("after_explicit_tick=24","after_explicit_tick=23"),
 ("PERF_RESET enabled=1 freq=777 energy_mac=99.0 total=0","PERF_RESET enabled=0 freq=777 energy_mac=99.0 total=0"),
 ("reported_power_mw=1000.0 physical_power_mw=1.0","reported_power_mw=1.0 physical_power_mw=1.0"),
 ("100 B / 10 ns = 10 GB/s","100 B / 10 ns = 11 GB/s"),
 ("0.001 TMAC/s","0.009 TMAC/s"),
 ("0.002 TOPS","0.009 TOPS"),
 ("0.00390625","0.00300000"),
 ("1.051648 mm²","1.151648 mm²"),
 ("2.0000 pJ","2.1000 pJ"),
 ("0.4000 pJ","0.5000 pJ"),
 ("370.0000 pJ","371.0000 pJ"),
 ("0.6400 pJ","0.7400 pJ"),
 ("0.1000 pJ","0.2000 pJ"),
 ("52.5824 pJ","53.5824 pJ"),
 ("read_arg=21 write_arg=28","read_arg=28 write_arg=21"),
 ("425.7224 pJ","425.0000 pJ"),
 ("42.57224 mW","41.57224 mW"),
 ("18446744073709551606","18446744073709551605"),
 ("## Summary","## Conclusion"),
]
for old,new in mutations:
    require(old in s,f"mutation source {old}")
    try: validate_text(s.replace(old,new))
    except SystemExit: pass
    else: raise SystemExit(f"CH17_MANUSCRIPT_VALIDATION FAIL: mutation survived {old}")
require(RUN.is_dir(),RUN)
subprocess.run(["sha256sum","-c","sha256-retained.txt"],cwd=RUN,check=True,stdout=subprocess.DEVNULL)
bundle=[]
for line in (RUN/"bundle-sha256.txt").read_text().splitlines():
    _,rel=line.split(None,1); bundle.append(rel.strip())
expected_bundle={"sha256-retained.txt","manifest-check.log","finalization.log","predraft-validation.log"}
require(len(bundle)==4 and set(bundle)==expected_bundle,"outer bundle member set")
subprocess.run(["sha256sum","-c","bundle-sha256.txt"],cwd=RUN,check=True,stdout=subprocess.DEVNULL)
for mode in ([],["-O"]):
    subprocess.run(["python3",*mode,str(ROOT/"experiments/ch17_predraft_validate.py")],cwd=ROOT,check=True,
                   env={**os.environ,"CH17_RUN_ID":RUN_ID},stdout=subprocess.DEVNULL)
require(subprocess.run(["git","rev-parse","HEAD"],cwd=TUSIM,check=True,stdout=subprocess.PIPE,text=True).stdout.strip()==PIN,"Tusim pin")
require(subprocess.run(["git","symbolic-ref","-q","HEAD"],cwd=TUSIM,stdout=subprocess.DEVNULL).returncode!=0,"Tusim detached")
require(subprocess.run(["git","status","--porcelain=v1","--untracked-files=all"],cwd=TUSIM,check=True,stdout=subprocess.PIPE).stdout==b"","Tusim dirty")
require(subprocess.run(["git","branch","--show-current"],cwd=ROOT,check=True,stdout=subprocess.PIPE,text=True).stdout.strip()=="main","book branch")
snapshot=ROOT/"notes/chapter-17-reviewed-snapshot.txt"
if snapshot.exists():
    m=re.search(r"^commit=([0-9a-f]{40})$",snapshot.read_text(),re.M)
    if m is None: raise SystemExit("CH17_MANUSCRIPT_VALIDATION FAIL: review snapshot commit")
    reviewed=m.group(1)
    reviewed_paths=[
      "manuscript/part-2-core/17-measurement-surfaces-counters-tracing-cycle-models-and-energy.md",
      "experiments/ch17_manuscript_validate.py",
      "notes/chapter-17-manuscript-review-dispositions.md",
      "README.md","PLAN.md","fidelity-matrix.md","source-audit.md",
    ]
    for rel in reviewed_paths:
        blob=subprocess.run(["git","show",f"{reviewed}:{rel}"],cwd=ROOT,check=True,stdout=subprocess.PIPE).stdout
        require((ROOT/rel).read_bytes()==blob,f"reviewed snapshot drift: {rel}")
print(f"CH17_MANUSCRIPT_VALIDATION PASS words={words} run=experiments/runs/ch17-measurement/{RUN_ID}")