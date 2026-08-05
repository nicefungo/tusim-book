#!/usr/bin/env python3
"""Fail-closed manuscript/evidence/link checks for Chapter 16."""
from pathlib import Path
import re, subprocess

ROOT=Path(__file__).resolve().parents[1]
CHAPTER=ROOT/"manuscript/part-2-core/16-double-buffering-and-legal-overlap.md"
RUN_ID="20260804-ch16-canonical-v4"
RUN=ROOT/"experiments/runs/ch16-double-buffer"/RUN_ID
PIN="e918c80b6fce833cd1fcae97730fa841c2176f25"
TUSIM=Path("/home/zxy/Workplace/projects/tusim")

def require(c,m):
    if not c: raise SystemExit(f"CH16_MANUSCRIPT_VALIDATION FAIL: {m}")
def slug(x):
    x=re.sub(r"<[^>]+>","",x).strip().lower()
    x=re.sub(r"[^\w\- ]","",x,flags=re.UNICODE)
    return re.sub(r"[ -]+","-",x).strip("-")
def validate_text(s):
    require(s.startswith("# Chapter 16 — Double Buffering and Legal Overlap\n"),"title")
    require(PIN in s,"pin")
    words=len(re.findall(r"\b[\w'’-]+\b",s))
    require(4500 <= words <= 8000,f"word count {words}")
    required=["Learning objectives","Prerequisite graph","Opening architecture question",
              "Source map","Trade-off","Verification","Fidelity","Failure modes","Summary",
              "Review questions","answer key","Design exercises","Primary references"]
    low=s.lower()
    for x in required: require(x.lower() in low,x)
    phrases=["canonical v4","31","60","91","10/10","9/10","active","shadow",
             "shadow_dirty","not a valid bit","descriptor","pipeline controller","no non-test caller",
             "active=22","shadow=7a","desc_cycles=53","8/7","1.142857","saved=0",
             "5/3","1.666667","infinite","17","18.285714","20","32 KiB","64 KiB",
             "1,024 B/cycle","Analytical","uncalibrated","single buffer","ping-pong",
             "bank","triple","event","context","common clock","SRAM_REINIT",
             "CTX_RESTORE","wraparound","shared_cap=100","AddressSanitizer","fail-fast"]
    for x in phrases: require(x.lower() in low,x)
    review_repairs = [
      "integrated legal-overlap path: none at this pin",
      "supersedes chapter 14's **evidentiary interpretation**",
      "returns `void`",
      "tu-to-tu copies have no equivalent bounds gate",
      "scatter indices are not individually bounded",
      "no observable behavioral effect",
      "does not assert the advertised relative cross-tile ordering",
      "pe-array pipeline depth 2",
      "counts two operations per mac",
      "tops=operations/cycles/1000",
      "detect_leaks=0",
      "enable_load_overlap=true",
      "produced 31/51/82",
      "selected worked design-exercise answers (exercises 1–3)",
      "exercises 4–9 are open-ended projects",
    ]
    for x in review_repairs: require(x in low,"review repair: "+x)
    banned=["integrated Tusim pipeline is validated","descriptor DMA writes the shadow buffer correctly",
            "shadow_dirty proves completion","controller speedup measures latency hiding",
            "context switching preserves double-buffer state","double buffering is always beneficial",
            "swap authorization:***"]
    for x in banned: require(x.lower() not in low,f"banned: {x}")
    require(len(re.findall(r"^\d+\. ",s[s.lower().index("review questions"):],re.M))>=8,"review questions")
    require(len(re.findall(r"^\d+\. \*\*",s[s.lower().index("design exercises"):],re.M))>=3,"design exercises")
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

require(CHAPTER.is_file(),CHAPTER)
s=CHAPTER.read_text(); words=validate_text(s); validate_links(s)
for old,new in [("active=22","active=7a"),("desc_cycles=53","desc_cycles=52"),
                ("18.285714","20.000000"),("## Summary","## Conclusion")]:
    if old in s:
        try: validate_text(s.replace(old,new))
        except SystemExit: pass
        else: raise SystemExit(f"CH16_MANUSCRIPT_VALIDATION FAIL: mutation survived {old}")
require(RUN.is_dir(),RUN)
subprocess.run(["sha256sum","-c","sha256-retained.txt"],cwd=RUN,check=True,stdout=subprocess.DEVNULL)
subprocess.run(["python3",str(ROOT/"experiments/ch16_predraft_validate.py")],cwd=ROOT,check=True,
               env={**__import__('os').environ,"CH16_RUN_ID":RUN_ID},stdout=subprocess.DEVNULL)
require(subprocess.run(["git","rev-parse","HEAD"],cwd=TUSIM,check=True,stdout=subprocess.PIPE,text=True).stdout.strip()==PIN,"Tusim pin")
require(subprocess.run(["git","symbolic-ref","-q","HEAD"],cwd=TUSIM,stdout=subprocess.DEVNULL).returncode!=0,"Tusim detached")
require(subprocess.run(["git","status","--porcelain=v1","--untracked-files=all"],cwd=TUSIM,check=True,stdout=subprocess.PIPE).stdout==b"","Tusim dirty")
require(subprocess.run(["git","branch","--show-current"],cwd=ROOT,check=True,stdout=subprocess.PIPE,text=True).stdout.strip()=="main","book branch")
snapshot=ROOT/"notes/chapter-16-reviewed-snapshot.txt"
if snapshot.exists():
    m=re.search(r"^commit=([0-9a-f]{40})$",snapshot.read_text(),re.M)
    if m is None: raise SystemExit("CH16_MANUSCRIPT_VALIDATION FAIL: review snapshot commit")
    reviewed=m.group(1)
    reviewed_paths=[
      "manuscript/part-2-core/16-double-buffering-and-legal-overlap.md",
      "experiments/ch16_manuscript_validate.py",
      "notes/chapter-16-manuscript-review-dispositions.md",
      "README.md","fidelity-matrix.md","source-audit.md",
    ]
    for rel in reviewed_paths:
        blob=subprocess.run(["git","show",f"{reviewed}:{rel}"],cwd=ROOT,check=True,stdout=subprocess.PIPE).stdout
        require((ROOT/rel).read_bytes()==blob,f"reviewed snapshot drift: {rel}")
print(f"CH16_MANUSCRIPT_VALIDATION PASS words={words} run=experiments/runs/ch16-double-buffer/{RUN_ID}")
