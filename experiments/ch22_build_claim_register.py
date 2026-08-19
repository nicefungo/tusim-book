#!/usr/bin/env python3
"""Build the Chapter 22 canonical index from three frozen, independently reviewed semantic manifests."""
from __future__ import annotations
import argparse, collections, hashlib, json, re
from pathlib import Path
PIN="e918c80b6fce833cd1fcae97730fa841c2176f25"
STATUSES=("retained","qualified","superseded","rejected","blocked")
PRIORITY=("blocked","rejected","superseded","qualified","retained")
MANIFEST_NAMES=(
 "chapter-22-reviewed-claim-manifest-geometry-memory.md",
 "chapter-22-reviewed-claim-manifest-numerics-operators.md",
 "chapter-22-reviewed-claim-manifest-sharing-policy.md",
)
MECHANISMS={
 "M1-fixed-cost-amortization":"Fixed-cost amortization",
 "M2-resource-thresholds":"Resource thresholds and discrete cliffs",
 "M3-bandwidth-compute-balance":"Bandwidth/compute balance",
 "M4-distribution-placement":"Distribution or placement, not a scalar rate",
 "M5-shape-placement-reversal":"Shape- or placement-dependent reversals",
 "M6-state-scope-obligations":"Retained or buffered state scope shifts obligations",
 "M7-producer-metric-hazards":"Producer and metric-dialect hazards",
}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def domain(name):
 if any(k in name for k in ("interconnect","multicore","broadcast")):return "sharing-topology"
 if any(k in name for k in ("precision","rounding","int8","compression","decoder","structured-2of4","bitmap")):return "numerics-representation"
 if any(k in name for k in ("attention","conv","pool","norm","softmax","activation")):return "operators"
 if any(k in name for k in ("context","scheduler")):return "runtime-static-policy"
 if any(k in name for k in ("dma","dram","sram","gbuf","double-buffer")):return "memory-movement"
 return "geometry-balance"
def mechanism(name,row):
 x=row.lower();rules=[
 ("M7-producer-metric-hazards",r'producer|metric|equation|analytical|heuristic|linked|correctness|golden|unmodeled|unquantified|invalid|arithmetic contradiction|compiler|runtime|onnx'),
 ("M6-state-scope-obligations",r'context|save/restore|live state|retained|double.buffer|ping.pong|ownership|visibility|preempt|continuation'),
 ("M4-distribution-placement",r'distribution|placement|sparse|compression|bitmap|decoder|metadata|traffic matrix|routing|mesh|ring|topology|contention|broadcast'),
 ("M5-shape-placement-reversal",r'shape|aspect|alignment|dataflow|stationary|utilization|pe array|reversal|transpose'),
 ("M2-resource-thresholds",r'capacity|threshold|cliff|knee|passes|tile count|buffer size|sram|decoder width|spill'),
 ("M3-bandwidth-compute-balance",r'bandwidth|dma|dram|bus width|bytes/cycle|compute.bound|memory.bound|stall|throughput|tops|balance'),
 ("M1-fixed-cost-amortization",r'setup|fill/drain|fixed cost|amortiz|overhead|small workload|pipeline|fusion|fused')]
 for m,p in rules:
  if re.search(p,x):return m
 return {"operators":"M1-fixed-cost-amortization","runtime-static-policy":"M6-state-scope-obligations","memory-movement":"M2-resource-thresholds","sharing-topology":"M4-distribution-placement","numerics-representation":"M4-distribution-placement","geometry-balance":"M5-shape-placement-reversal"}[domain(name)]
def canonical_status(text):
 low=text.lower(); hits=[]
 for s in STATUSES:
  m=re.search(rf'\b{s}\b',low)
  if m:hits.append((m.start(),s))
 if not hits:raise ValueError(f"no canonical disposition in: {text[:200]}")
 return min(hits)[1]
def objective_classes(row):
 low=row.lower();out=[]
 if "quantified" in low or re.search(r'(?<![a-z])q=',low) or re.search(r'(?<![a-z]):q\b',low):out.append("quantified")
 if "directional" in low or re.search(r'(?<![a-z])d=',low) or re.search(r'(?<![a-z]):d\b',low):out.append("directional")
 if "unknown" in low or re.search(r'(?<![a-z])u=',low) or re.search(r'(?<![a-z]):u\b',low):out.append("unknown")
 return out or ["directional"]
def parse_manifest(path,source):
 lines=path.read_text().splitlines(); kind=("geometry" if "geometry-memory" in path.name else "numerics" if "numerics-operators" in path.name else "sharing")
 heads=[]
 for i,l in enumerate(lines,1):
  pats=[r'^### \d+\. `([^`]+\.md)`',r'^### [A-Z]\d+\. `([^`]+\.md)`',r'^## \d+\. `([^`]+\.md)`']
  for p in pats:
   m=re.match(p,l)
   if m:heads.append((i,m.group(1)));break
 claims=[];reports=[]
 for hi,(start,name) in enumerate(heads):
  end=(heads[hi+1][0]-1 if hi+1<len(heads) else len(lines)); block=lines[start-1:end]
  src=source/name
  if not src.is_file():raise ValueError(f"missing source {name}")
  source_hash=sha(src); declared=None
  for l in block[:14]:
   m=re.search(r'`([0-9a-f]{64})`',l)
   if m:declared=m.group(1);break
  if declared is None:
   for l in block[:14]:
    m=re.search(r'— `([0-9a-f]{64})`',l)
    if m:declared=m.group(1);break
  if declared!=source_hash:raise ValueError(f"hash mismatch {name}: {declared} != {source_hash}")
  ctx=[]
  for j,l in enumerate(block[:20],start):
   if any(k in l.lower() for k in ("question","q/alt/wl/axes/ctl","context:","decision context","alternatives","workload/axes","controls","objective","producer","obj/prod","owner","lim","binding limitation","metric domain")):
    ctx.append({"manifest_line":j,"exact_excerpt":l})
  rclaims=[];tracked_domain=None
  for j,l in enumerate(block,start):
   dm=re.search(r'(?:Metric domain(?: for every claim)?|domain).*?`([^`]+)`',l,re.I)
   if dm and not (re.match(r'^- \*\*`',l) or re.match(r'^\d+\. \*\*',l)):tracked_domain=dm.group(1)
   claim_id=None;disp_text="";metric=None
   if kind=="geometry":
    m=re.match(r'^- \*\*`([^`]+)`\*\* — Quote',l)
    if m:
     claim_id=m.group(1);dm=re.search(r'Domain `([^`]+)`',l);metric=dm.group(1) if dm else None
     tm=re.search(r'Type `[^`]+`; (.*?)(?: Domain `| Tags `| Tags )',l);disp_text=tm.group(1) if tm else l
   elif kind=="numerics":
    m=re.match(r'^\d+\. \*\*([A-Z]\d+\.\d+) —',l)
    if m:
     claim_id=m.group(1);dm=re.search(r'domain=`([^`]+)`',l,re.I);metric=dm.group(1) if dm else None
     tm=re.search(r'\*\*Disposition:\*\* (.*?); owner',l,re.I);disp_text=tm.group(1) if tm else l
   else:
    m=re.match(r'^\| ([A-Z]+\d+) \|',l)
    if m:
     claim_id=m.group(1);metric=tracked_domain
     cells=[x.strip() for x in l.strip().strip('|').split('|')];disp_text=cells[2] if len(cells)>2 else l
   if not claim_id:continue
   if not metric:raise ValueError(f"missing metric domain {path.name}:{j}")
   status=canonical_status(disp_text);mid=mechanism(name,l);rid=f"C22R-{claim_id}"
   rec={"id":rid,"stable_suffix":claim_id,"report_path":f"docs/exploration/{name}","source_commit":PIN,"source_sha256":source_hash,"source_locator_text":"embedded verbatim in reviewed manifest row","canonical_disposition":status,"manifest_disposition_text":disp_text,"evidence_class":"independently reviewed semantic conclusion","objective_classifications":objective_classes(l),"metric_domain":{"id":metric,"noncomposable":True,"composable_with":[],"producer_units_state":"bound by the exact reviewed manifest row and inherited report context"},"mechanism_family":mid,"materially_distinct_alternatives":{"binding":"exact claim row plus inherited report context","manifest_line":j},"missing_decisive_dimensions":{"binding":"exact claim row","mandatory":True},"safe_replacement":{"binding":"exact claim row","mandatory":True},"limitation":{"binding":"exact claim row plus inherited verbatim limitation","mandatory":True},"open_or_reversal_condition":{"binding":"exact claim row","mandatory":True},"current_evidence_owner":{"binding":"exact claim row and inherited owner context","mandatory":True},"decision_outcome":"open","local_dominance_eligible":False,"reviewed_manifest":{"path":f"notes/{path.name}","sha256":sha(path),"line":j,"exact_excerpt":l,"report_context":ctx}}
   claims.append(rec);rclaims.append(rid)
  reports.append({"path":f"docs/exploration/{name}","sha256":source_hash,"line_count":len(src.read_text().splitlines()),"portfolio_domain":domain(name),"claim_ids":rclaims,"claim_count":len(rclaims),"metric_domains":sorted({c['metric_domain']['id'] for c in claims if c['report_path'].endswith(name)}),"mechanisms":sorted({c['mechanism_family'] for c in claims if c['report_path'].endswith(name)}),"reviewed_manifest_path":f"notes/{path.name}","reviewed_manifest_section":{"start_line":start,"end_line":end},"report_context":ctx})
 return reports,claims

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--inventory',required=True);ap.add_argument('--manifest-dir',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 source=Path(a.source);mdir=Path(a.manifest_dir);inv=json.loads(Path(a.inventory).read_text())
 if inv.get('source_commit')!=PIN or inv.get('report_count')!=46:raise SystemExit('inventory pin/count mismatch')
 reports=[];claims=[]
 for n in MANIFEST_NAMES:
  rs,cs=parse_manifest(mdir/n,source);reports+=rs;claims+=cs
 invpaths={r['path'] for r in inv['reports']};rpaths={r['path'] for r in reports}
 if len(reports)!=46 or rpaths!=invpaths or any(not r['claim_ids'] for r in reports):raise SystemExit('semantic manifest report coverage failure')
 ids=[c['id'] for c in claims]
 if len(ids)!=len(set(ids)):raise SystemExit('duplicate semantic claim id')
 statuses=collections.Counter(c['canonical_disposition'] for c in claims)
 families=[]
 for mid,name in MECHANISMS.items():
  cs=[c for c in claims if c['mechanism_family']==mid];domains=sorted({next(r['portfolio_domain'] for r in reports if r['path']==c['report_path']) for c in cs})
  if len(domains)<2:raise SystemExit(f'mechanism lacks independent domains: {mid}: {domains}')
  families.append({"id":mid,"name":name,"independent_portfolio_domains":domains,"claim_ids":[c['id'] for c in cs]})
 doc={"schema":"ch22-reviewed-semantic-claim-register-v3","source_commit":PIN,"authority":"Three frozen independent read-only extractions covering 21+17+8 reports; exact manifest rows are the complete binding records.","selection_rule":{"type":"independently reviewed per-report semantic manifest","claim_count":len(claims),"report_count":len(reports),"zero_claim_reports":[],"not_a_regex_line_inventory":True},"canonical_disposition_enum":list(STATUSES),"closed_framing":{"constraint_first":True,"dispositions_are_filters_not_spine":True,"forbidden":["Chapter 21 sweep tutorial","report chronology","cross-domain scalarization","portfolio-wide Pareto frontier","uncalibrated physical metrics","compiler/runtime/ONNX composition"]},"family_bound":{"min":5,"max":7,"actual":7,"families":families},"reports":sorted(reports,key=lambda x:x['path']),"claims":claims,"summary":{"report_count":len(reports),"claim_count":len(claims),"status_counts":dict(sorted(statuses.items())),"metric_domain_count":len({c['metric_domain']['id'] for c in claims}),"all_decisions_open":all(c['decision_outcome']=='open' for c in claims),"all_local_dominance_ineligible":all(not c['local_dominance_eligible'] for c in claims)}}
 Path(a.out).write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n');print(json.dumps(doc['summary'],sort_keys=True))
if __name__=='__main__':main()
