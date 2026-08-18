#!/usr/bin/env python3
"""Fail-closed, bundle-local validator for Chapter 21 post-review evidence."""
from __future__ import annotations
import ast,hashlib,json,os,re,subprocess,sys
from pathlib import Path
BOOK=Path(__file__).resolve().parents[1]
RUNS=(BOOK/"experiments/runs").resolve()
PIN="e918c80b6fce833cd1fcae97730fa841c2176f25"
DEFAULT_RUN="20260818-ch21-postreview-v1"
RID_RE=re.compile(r"^20260818-ch21-postreview-v[1-9][0-9]*$")
INPUTS=[
"edition.yaml","notes/chapter-21-framing-and-evidence-plan.md","notes/chapter-21-framing-review-dispositions.md",
"notes/chapter-21-source-and-claim-ledger.md","notes/chapter-21-limitation-register.md","notes/chapter-21-worked-decision-schema.json",
"notes/chapter-21-metric-fidelity-register.json","notes/chapter-21-predraft-audit-report.md","notes/chapter-21-skeptical-predraft-review-dispositions.md",
"references/ch21-sweep-method-primary-sources.md","references/ch21-primary-source-verification-ledger.json",
"experiments/ch21_source_audit.py","experiments/ch21_boundary_audit.py","experiments/ch21_sweep_probe.c","experiments/ch21_formula_probe.py",
"experiments/run_ch21_sweep_evidence_audit.sh","experiments/ch21_predraft_validate.py"]
BASE=["archive-members.log","aspect-raw.log","aspect-rows.csv","body-validation-normal.log","body-validation-optimized.log","boundary-audit.log",
"boundary-mutation.log","build.log","commands.txt","decision-schema-check.log","environment.txt","failure-early.log","failure-early-summary.log",
"formula-mutation.log","formula-results.json","formula.log","input-hashes.txt","input_commit","inventory.json","manifest-hierarchy-mutations.log",
"metric-register.json","probe-O0-dynamic.log","probe-O0.log","probe-O0.stderr.log","probe-O2-dynamic.log","probe-O2.log","probe-O2.stderr.log",
"probe-route-mutation.log","relation-mutation.log","report-role-mutation.log","sensitivity-rows.csv","source-audit-hash-mutation.log","source-audit-restored.log",
"source-audit.log","source-state-expected.txt","source_pin","status-mutation.log","transcript.log","validator-assert-mutation-normal.log",
"validator-assert-mutation-optimized.log","validator-input-mutation-normal.log","validator-input-mutation-optimized.log"]
ROOTS=["retained-files.txt","sha256-retained.txt","manifest-check.log","finalization.log","predraft-validation-normal.log","predraft-validation-optimized.log",
"bundle-sha256.txt","bundle-check.log","closure-validation-normal.log","closure-validation-optimized.log"]
REPORT_COUNTS={"question":35,"hypothesis":30,"method":30,"explicit_harness":13,"repro_command":16,"manifest":0}
PROBE=[
"DATAFLOW_ROUTE requested_label=output_stationary process_global_before=1 core_snapshot_before=0 core_snapshot_after=0 effective_core=weight_stationary",
"DATAFLOW_EXEC tag=labeled_os active=weight_stationary delta=67 output=58,64,139,154",
"DATAFLOW_EXEC tag=active_os active=output_stationary delta=4 output=58,64,139,154",
"DATAFLOW_EXEC tag=active_rs active=row_stationary delta=36 output=58,64,139,154",
"ROUNDING_AXIS value=1.0007 rne=0x3c01 rtz=0x3c00 same_seed_equal=1 changed_seed_diff=1 seed12345_fnv=99a9ff040fc80ca3 seed54321_fnv=283bd184c961bcc2",
"RANDOMNESS_SCOPE fixed_seed_replay=1 changed_seed_vector=1 independent_application_samples=0 application_accuracy=0",
"ROUNDING_ORDER stable_case_seed_permutation_equal=1 single_seed_permutation_diff=1",
"CONTEXT_EXEC full256=16484 live25_256=4196 control256=100 full256_bw16=32868 full256_bw64=8292 producer=linked_estimator",
"CH21_SWEEP_PROBE SUMMARY failures=0"]
FORMULA=["ASPECT_MATRIX rows=120 M_set=12 N_set=10 K=128 producer=local_formula",
"ASPECT_BOUNDARY M20N16_util=62.5 M40N16_util=83.3 M20N16_total=570 symmetry_16x256_256x16=1",
"COUNTEREXAMPLE report_nonzero_remainder_le_3.8=0 M40_remainder8_waste=16.7",
"ASPECT_TRANSITION totals=404,543,570,606,669,678 tie_M16_M24=1 padding20to32_reverses=1 duplicated_20x48=1382_vs_1376",
"DATAFLOW_REPORT_SENSITIVITY K_points=1,16,32,64,256,1024 R_points=8,16,32 fixed_formula_delta=32 decreasing_fraction=1 producer=report_prose",
"DATAFLOW_PRODUCERS sweep_local=26624,22528,24640 report_local=21536,21504 linked_plugin=81920,20480,50176 incomparable=1",
"ASPECT_TWO_AXIS workload_M=16,17,20,24,31,32 architecture_pd_bus=1_32,2_32,4_32,2_16,2_64",
"CONTEXT_CROSSOVER budget10000_bw52=10183 bw53=9993 full128_live32_tie=4196 control_reversal_reload_gt=16384",
"PRODUCER_CLASSES executable=1 linked_estimator=1 local_formula=1 report_prose=1 heterogeneous_sum=0","CH21_FORMULA_PROBE PASS"]
def fail(m): print("CH21_PREDRAFT_VALIDATION FAIL "+m);raise SystemExit(1)
def need(x,m):
 if not x: fail(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse_manifest(p):
 d={}
 for line in p.read_text().splitlines():
  z=line.split("  ",1);need(len(z)==2 and re.fullmatch(r"[0-9a-f]{64}",z[0]) is not None,"manifest-line")
  rel=z[1];need(rel not in d,"manifest-duplicate:"+rel);need(not Path(rel).is_absolute() and ".." not in Path(rel).parts,"manifest-path:"+rel);d[rel]=z[0]
 return d
def safe_regular(root,rel):
 p=root/rel;need(p.exists() and p.is_file() and not p.is_symlink(),"regular:"+rel);need(p.resolve().is_relative_to(root.resolve()),"containment:"+rel);return p
def verify_manifest(root,mf,expected):
 d=parse_manifest(safe_regular(root,mf));need(set(d)==set(expected),"manifest-set:"+mf)
 for rel,digest in d.items():need(sha(safe_regular(root,rel))==digest,"manifest-hash:"+rel)
def recursive_files(root):
 out=[]
 for p in root.rglob("*"):
  need(not p.is_symlink(),"symlink:"+str(p.relative_to(root)))
  if p.is_file():out.append(p.relative_to(root).as_posix())
 return sorted(out)
def run_id():
 rid=os.environ.get("CH21_RUN_ID",DEFAULT_RUN);need(RID_RE.fullmatch(rid) is not None,"run-id")
 run=RUNS/rid;need(run.parent.resolve()==RUNS,"run-parent");return rid,run
def check_input_bundle(run):
 lines=[]
 for rel in INPUTS:
  p=safe_regular(run,"inputs/"+rel);lines.append(f"{sha(p)}  {rel}")
 need(safe_regular(run,"input-hashes.txt").read_text().splitlines()==lines,"input-hashes")
def check_governance(run):
 ledger=safe_regular(run,"inputs/notes/chapter-21-source-and-claim-ledger.md").read_text()
 reg=safe_regular(run,"inputs/notes/chapter-21-limitation-register.md").read_text()
 review=safe_regular(run,"inputs/notes/chapter-21-skeptical-predraft-review-dispositions.md").read_text()
 report=safe_regular(run,"inputs/notes/chapter-21-predraft-audit-report.md").read_text()
 sections=re.split(r"^### ",ledger,flags=re.M)[1:]
 entries=[]
 for sec in sections:
  ident=re.match(r"(C21\.\d+)\b",sec);status=re.search(r"^- \*\*Status:\*\* ([a-z]+)\.$",sec,re.M);limitation=re.search(r"^- \*\*Limitation wording:\*\* (.+)$",sec,re.M)
  need(ident is not None and status is not None and limitation is not None,"claim-structure");entries.append((ident.group(1),status.group(1),limitation.group(1)))
 need([x[0] for x in entries]==[f"C21.{i}" for i in range(1,13)],"claim-ids")
 need(all(s in {"verified","qualified","rejected","blocked"} for _,s,_ in entries),"claim-status")
 need(dict((i,s) for i,s,_ in entries)["C21.11"]=="verified","c21.11")
 lim=dict(re.findall(r"^- \*\*(C21\.\d+):\*\* (.+)$",reg,re.M));need(set(lim)=={f"C21.{i}" for i in range(1,13)},"limitation-ids")
 need(all(lim[i]==text for i,_,text in entries),"limitation-verbatim")
 need("Disposition: **PASS for post-review reseal" in review and "Unresolved findings: **0**" in review and "R1-1" in review and "R3-8" in review,"review-pass")
 marker="post-review evidence authorized";need(marker in ledger and marker in report,"authorization-convergence")
def check_body(run,rid):
 check_input_bundle(run);need(safe_regular(run,"source_pin").read_text().strip()==PIN,"source-pin")
 transcript=safe_regular(run,"transcript.log").read_text()
 for g in ["CH21_SOURCE_AUDIT PASS pin="+PIN,"CH21_BOUNDARY_AUDIT PASS pin="+PIN,"RELATION_MUTATION count_preserved=22 rejected=1","REPORT_ROLE_MUTATION rejected=1","BOUNDARY_MUTATION rejected=1","FORMULA_MUTATION stale_axis_rejected=1","STATUS_MUTATION upstream_zero_mismatch_rejected=1","BOOK_INPUTS unchanged=1 head="]:
  need(g in transcript,"transcript-gate:"+g)
 probe=safe_regular(run,"probe-O0.log").read_text();need(probe==safe_regular(run,"probe-O2.log").read_text(),"probe-opt")
 for x in PROBE:need(x in probe,"probe-line:"+x)
 form=safe_regular(run,"formula.log").read_text()
 for x in FORMULA:need(x in form,"formula-line:"+x)
 inv=json.loads(safe_regular(run,"inventory.json").read_text());need(len(inv["source_target_pairs"])==22 and len(inv["reports"])==46,"inventory-size")
 for k,v in REPORT_COUNTS.items():need(sum(bool(r[k]) for r in inv["reports"])==v,"report-count:"+k)
 required={"parameter_matrix","equation_markers","output_row_count","conclusion","ci_member","producer_class","actual_executed_command"};need(all(required<=set(r) for r in inv["reports"]),"report-fields")
 dec=json.loads(safe_regular(run,"inputs/notes/chapter-21-worked-decision-schema.json").read_text());need(len(dec["worked_cases"])==4 and all(set(dec["required_fields"])<=set(c) for c in dec["worked_cases"]),"decision-schema")
 met=json.loads(safe_regular(run,"metric-register.json").read_text());need(met==json.loads(safe_regular(run,"inputs/notes/chapter-21-metric-fidelity-register.json").read_text()),"metric-copy");need(len(met["rows"])>=9 and all(set(met["required_fields"])<=set(r) for r in met["rows"]),"metric-shape")
 src=json.loads(safe_regular(run,"inputs/references/ch21-primary-source-verification-ledger.json").read_text());need(len(src["sources"])==10 and all({"doi","url","source_type","inspected_surface","status","metadata_sha256"}<=set(r) and re.fullmatch(r"[0-9a-f]{64}",r["metadata_sha256"]) for r in src["sources"]),"research-ledger")
 check_governance(run)
def check_failures(run):
 expected=safe_regular(run,"source-state-expected.txt").read_text().strip();need(expected.startswith("SOURCE_STATE after head="+PIN+" detached=1 dirty_entries=0 ignored_hash="),"expected-source-state")
 for name,diag in [("failure-early.log","INJECT early-inventory-failure"),("validator-input-mutation-normal.log","input-hashes"),("validator-input-mutation-optimized.log","input-hashes"),("validator-assert-mutation-normal.log","validator-contains-assert"),("validator-assert-mutation-optimized.log","validator-contains-assert")]:
  t=safe_regular(run,name).read_text();need(t.count(expected)==1 and diag in t,"failure-proof:"+name)
 m=safe_regular(run,"manifest-hierarchy-mutations.log").read_text();need("normal_cases=6 optimized_cases=6 all_rejected=1" in m,"manifest-mutations")
def fixture_mode(args):
 need(len(args)==4,"fixture-arguments");root=Path(args[1]).resolve();mf=args[2];expected=args[3].split(",") if args[3] else []
 need(root.is_dir(),"fixture-root");verify_manifest(root,mf,expected);need(recursive_files(root)==sorted(set(expected)|{mf}),"fixture-exact-set");print("CH21_MANIFEST_FIXTURE PASS");return 0
def git_run(args):return subprocess.run(["git",*args],cwd=BOOK,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def postseal(run,rid):
 need(git_run(["status","--porcelain=v1"]).stdout=="","git-clean")
 head=git_run(["rev-parse","HEAD"]).stdout.strip();parents=git_run(["show","-s","--format=%P",head]).stdout.strip().split();need(len(parents)==1,"seal-parent-count")
 input_commit=safe_regular(run,"input_commit").read_text().strip();need(parents[0]==input_commit,"seal-parent")
 changed=git_run(["diff-tree","--no-commit-id","--name-only","-r",head]).stdout.splitlines();prefix=f"experiments/runs/{rid}/";need(changed and all(p.startswith(prefix) for p in changed),"seal-run-only")
 need((BOOK/prefix).resolve()==run.resolve(),"seal-direct-child")
 print(f"CH21_POSTSEAL PASS run={rid} head={head} parent={input_commit} changed={len(changed)}")
def main():
 tree=ast.parse(Path(__file__).read_text());need(not any(isinstance(n,ast.Assert) for n in ast.walk(tree)),"validator-contains-assert")
 args=sys.argv[1:]
 if args and args[0]=="--manifest-fixture":return fixture_mode(args)
 rid,run=run_id();need(run.is_dir() and not run.is_symlink(),"run-missing");mode=args[0] if args else "--default";need(mode in {"--body","--default","--outer","--postseal"} and len(args)<=1,"arguments")
 check_body(run,rid)
 if mode=="--body":print(f"CH21_PREDRAFT_BODY_VALIDATION PASS run={rid}");return 0
 check_failures(run)
 retained=sorted(["inputs/"+r for r in INPUTS]+BASE);need(safe_regular(run,"retained-files.txt").read_text().splitlines()==retained,"retained-list")
 verify_manifest(run,"sha256-retained.txt",retained+["retained-files.txt"])
 need(all(x.endswith(": OK") for x in safe_regular(run,"manifest-check.log").read_text().splitlines()),"manifest-check")
 if mode in {"--outer","--postseal"}:
  verify_manifest(run,"bundle-sha256.txt",["sha256-retained.txt","manifest-check.log","finalization.log","predraft-validation-normal.log","predraft-validation-optimized.log"])
  need(all(x.endswith(": OK") for x in safe_regular(run,"bundle-check.log").read_text().splitlines()),"bundle-check")
 if mode in {"--outer","--postseal"}:
  want=sorted(["inputs/"+r for r in INPUTS]+BASE+ROOTS);need(recursive_files(run)==want,"run-exact-set")
 if mode=="--postseal":postseal(run,rid);return 0
 print(f"CH21_PREDRAFT_VALIDATION PASS run={rid} mode={mode}");return 0
if __name__=="__main__":raise SystemExit(main())
