#!/usr/bin/env python3
"""Fail-closed validator for Chapter 21 predraft evidence bundles."""
from __future__ import annotations
import ast, hashlib, json, os, subprocess, sys
from pathlib import Path
BOOK=Path(__file__).resolve().parents[1]
PIN="e918c80b6fce833cd1fcae97730fa841c2176f25"
DEFAULT_RUN="20260818-ch21-provisional-v1"
INPUTS=[
"edition.yaml","notes/chapter-21-framing-and-evidence-plan.md","notes/chapter-21-framing-review-dispositions.md",
"notes/chapter-21-source-and-claim-ledger.md","notes/chapter-21-limitation-register.md","notes/chapter-21-worked-decision-schema.json","notes/chapter-21-metric-fidelity-register.json",
"notes/chapter-21-predraft-audit-report.md","notes/chapter-21-skeptical-predraft-review-dispositions.md",
"references/ch21-sweep-method-primary-sources.md","experiments/ch21_source_audit.py","experiments/ch21_sweep_probe.c",
"experiments/ch21_formula_probe.py","experiments/run_ch21_sweep_evidence_audit.sh","experiments/ch21_predraft_validate.py"]
BASE=["archive-members.log","aspect-raw.log","aspect-rows.csv","body-validation-normal.log","body-validation-optimized.log",
"build.log","commands.txt","decision-schema-check.log","environment.txt","failure-early.log","failure-early-summary.log",
"formula-mutation.log","formula-results.json","formula.log","input-hashes.txt","input_commit","inventory.json","manifest-failure.log","metric-register.json",
"probe-O0-dynamic.log","probe-O0.log","probe-O0.stderr.log","probe-O2-dynamic.log","probe-O2.log","probe-O2.stderr.log",
"probe-route-mutation.log","relation-mutation.log","sensitivity-rows.csv","source-audit-hash-mutation.log","source-audit-restored.log",
"source-audit.log","source_pin","status-mutation.log","transcript.log","validator-assert-mutation-normal.log",
"validator-assert-mutation-optimized.log","validator-input-mutation-normal.log","validator-input-mutation-optimized.log"]
GATES=[
"CH21_SOURCE_AUDIT PASS pin="+PIN+" hashes=17 predicates=20 checks=38",
"RELATION_MUTATION count_preserved=22 rejected=1","SOURCE_HASH_MUTATION rejected=1 restored=1",
"PROBE_OPT_STABILITY byte_identical=1","ROUTE_MUTATION requested_label_permutation_rejected=1",
"FORMULA_MUTATION stale_axis_rejected=1","STATUS_MUTATION missing_completion_rejected=1",
"ASPECT_REPRO raw_rows=120 stale_report_counterexample=1","DECISION_SCHEMA cases=4 required_fields=13",
"BOOK_INPUTS unchanged=1 head="]
PROBE=[
"DATAFLOW_ROUTE requested_label=output_stationary process_global_before=1 core_snapshot_before=0 core_snapshot_after=0 effective_core=weight_stationary",
"DATAFLOW_EXEC tag=labeled_os active=weight_stationary delta=67 output=58,64,139,154",
"DATAFLOW_EXEC tag=active_os active=output_stationary delta=4 output=58,64,139,154",
"DATAFLOW_EXEC tag=active_rs active=row_stationary delta=36 output=58,64,139,154",
"ROUNDING_AXIS value=1.0007 rne=0x3c01 rtz=0x3c00 same_seed_equal=1 changed_seed_diff=1 seed12345_fnv=99a9ff040fc80ca3 seed54321_fnv=283bd184c961bcc2",
"RANDOMNESS_SCOPE fixed_seed_replay=1 changed_seed_vector=1 independent_application_samples=0 application_accuracy=0",
"CONTEXT_EXEC full256=16484 live25_256=4196 control256=100 full256_bw16=32868 full256_bw64=8292 producer=linked_estimator",
"CH21_SWEEP_PROBE SUMMARY failures=0"]
FORMULA=["ASPECT_MATRIX rows=120 M_set=12 N_set=10 K=128 producer=local_formula",
"ASPECT_BOUNDARY M20N16_util=62.5 M40N16_util=83.3 M20N16_total=570 symmetry_16x256_256x16=1",
"COUNTEREXAMPLE report_nonzero_remainder_le_3.8=0 M40_remainder8_waste=16.7",
"ASPECT_TRANSITION totals=404,543,570,606,669,678 tie_M16_M24=1 padding20to32_reverses=1 duplicated_20x48=1382_vs_1376",
"CONTEXT_CROSSOVER budget10000_bw52=10183 bw53=9993 full128_live32_tie=4196 control_reversal_reload_gt=16384",
"CONTEXT_ROWS full256=16484 live25_256=4196 control256=100 full256_bw16=32868 full256_bw64=8292 producer=linked_estimator",
"PRODUCER_CLASSES executable=1 linked_estimator=1 local_formula=1 report_prose=1 heterogeneous_sum=0","CH21_FORMULA_PROBE PASS"]
def fail(m): print("CH21_PREDRAFT_VALIDATION FAIL "+m); raise SystemExit(1)
def need(x,m):
 if not x: fail(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git(args): return subprocess.run(["git",*args],cwd=BOOK,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def show(c,r):
 p=git(["show",f"{c}:{r}"]); need(p.returncode==0,"git-show:"+r); return p.stdout
def manifest(p):
 d={}
 for line in p.read_text().splitlines():
  z=line.split("  ",1); need(len(z)==2,"manifest-line"); need(z[1] not in d,"manifest-duplicate:"+z[1]); d[z[1]]=z[0]
 return d
def main():
 tree=ast.parse(Path(__file__).read_text()); need(not any(isinstance(n,ast.Assert) for n in ast.walk(tree)),"validator-contains-assert")
 args=sys.argv[1:]; body=args==["--body"]; outer=args==["--outer"]; need(not args or body or outer,"arguments")
 rid=os.environ.get("CH21_RUN_ID",DEFAULT_RUN); run=BOOK/"experiments/runs"/rid; need(run.is_dir(),"run-missing")
 commit=(run/"input_commit").read_text().strip(); need((run/"source_pin").read_text().strip()==PIN,"source-pin")
 expected=[]
 for rel in INPUTS:
  frozen=run/"inputs"/rel; need(frozen.is_file(),"frozen-input:"+rel); b=show(commit,rel); need(frozen.read_bytes()==b,"frozen-vs-commit:"+rel); expected.append(f"{hashlib.sha256(b).hexdigest()}  {rel}")
 need((run/"input-hashes.txt").read_text().splitlines()==expected,"input-hashes")
 transcript=(run/"transcript.log").read_text()
 for g in GATES: need(g in transcript,"transcript-gate:"+g)
 probe=(run/"probe-O0.log").read_text(); need(probe==(run/"probe-O2.log").read_text(),"probe-opt")
 for x in PROBE: need(x in probe,"probe-line:"+x)
 form=(run/"formula.log").read_text()
 for x in FORMULA: need(x in form,"formula-line:"+x)
 inv=json.loads((run/"inventory.json").read_text()); need(len(inv["source_target_pairs"])==22 and len(inv["reports"])==46,"inventory-json")
 dec=json.loads((run/"inputs/notes/chapter-21-worked-decision-schema.json").read_text()); need(len(dec["required_fields"])==13 and len(dec["worked_cases"])==4,"decision-schema")
 for case in dec["worked_cases"]: need(set(dec["required_fields"])<=set(case),"decision-case:"+case.get("id","?"))
 metric=json.loads((run/"metric-register.json").read_text()); need(metric==json.loads((run/"inputs/notes/chapter-21-metric-fidelity-register.json").read_text()),"metric-register-copy"); need(len(metric["rows"])==6 and not metric["heterogeneous_sum_allowed"],"metric-register-shape"); need(all(set(metric["required_fields"])<=set(row) for row in metric["rows"]),"metric-register-fields")
 if body: print(f"CH21_PREDRAFT_BODY_VALIDATION PASS run={rid} input_commit={commit}"); return 0
 need((run/"failure-early.log").read_text().count("SOURCE_STATE after ")==1,"early-source-after")
 need((run/"manifest-failure.log").read_text().count("SOURCE_STATE after ")==1 and "FAILED" in (run/"manifest-failure.log").read_text(),"manifest-failure-source-after")
 for name in ("validator-input-mutation-normal.log","validator-input-mutation-optimized.log","validator-assert-mutation-normal.log","validator-assert-mutation-optimized.log"):
  txt=(run/name).read_text(); need("SOURCE_STATE after " in txt,"mutation-source-after:"+name)
 forbidden=[p for p in run.rglob("*") if p.is_file() and (p.suffix in {".tar",".o"} or p.name.startswith("core"))]; need(not forbidden,"forbidden-artifacts")
 retained=(run/"retained-files.txt").read_text().splitlines(); expected_ret=sorted([f"inputs/{r}" for r in INPUTS]+BASE)
 need(retained==expected_ret,"retained-exact-set")
 inner=manifest(run/"sha256-retained.txt"); need(set(inner)==set(retained)|{"retained-files.txt"},"inner-set")
 for rel,d in inner.items(): need(sha(run/rel)==d,"inner-hash:"+rel)
 need(all(x.endswith(": OK") for x in (run/"manifest-check.log").read_text().splitlines()),"inner-check")
 final=(run/"finalization.log").read_text(); need(f"run={rid}" in final and f"input_commit={commit}" in final and f"transcript_sha256={sha(run/'transcript.log')}" in final,"finalization")
 if outer:
  bundle=manifest(run/"bundle-sha256.txt"); want={"sha256-retained.txt","manifest-check.log","finalization.log","predraft-validation-normal.log","predraft-validation-optimized.log"}; need(set(bundle)==want,"outer-set")
  for rel,d in bundle.items(): need(sha(run/rel)==d,"outer-hash:"+rel)
  need(all(x.endswith(": OK") for x in (run/"bundle-check.log").read_text().splitlines()),"outer-check")
 print(f"CH21_PREDRAFT_VALIDATION PASS run={rid} input_commit={commit} outer={int(outer)}")
 return 0
if __name__=="__main__": raise SystemExit(main())
