#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, collections, copy, hashlib, json, re
from pathlib import Path
PIN='e918c80b6fce833cd1fcae97730fa841c2176f25'
STATUSES={'retained','qualified','superseded','rejected','blocked'}
OBJ={'quantified','directional','unknown'}
REQ={'id','stable_suffix','report_path','source_commit','source_sha256','source_locator_text','canonical_disposition','manifest_disposition_text','evidence_class','objective_classifications','metric_domain','mechanism_family','materially_distinct_alternatives','missing_decisive_dimensions','safe_replacement','limitation','open_or_reversal_condition','current_evidence_owner','decision_outcome','local_dominance_eligible','reviewed_manifest'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def add(e,x):e.append(x)
def parse_sched(log):
 pat=re.compile(r'^\s{2}(.+?)\s{2,}(ASAP|ALAP|BALANCED)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$',re.M)
 return [{'topology':m.group(1).strip(),'policy':m.group(2),'cycles':int(m.group(3)),'barrier':int(m.group(4)),'hoist':int(m.group(5)),'length':int(m.group(6))} for m in pat.finditer(log)]
def validate(C,D,R,I,source,claims_path,book):
 e=[];source=Path(source);book=Path(book);claims_path=Path(claims_path)
 invr=I.get('reports',[]);ex=I.get('excluded_nonreport',[]);ipaths=[r.get('path') for r in invr]
 universe={f'docs/exploration/{p.name}' for p in source.glob('*.md')}
 if I.get('source_commit')!=PIN or I.get('report_count')!=46 or len(invr)!=46 or len(ipaths)!=len(set(ipaths)) or universe!={r.get('path') for r in invr+ex}:add(e,'inventory-universe')
 for r in invr+ex:
  p=source/Path(r.get('path','')).name
  if not p.is_file() or r.get('sha256')!=sha(p) or ('lines' in r and r.get('lines')!=len(p.read_text().splitlines())):add(e,'inventory-binding')
 if C.get('schema')!='ch22-reviewed-semantic-claim-register-v3' or C.get('source_commit')!=PIN or set(C.get('canonical_disposition_enum',[]))!=STATUSES:add(e,'claim-schema')
 claims=C.get('claims',[]);reports=C.get('reports',[]);ids=[c.get('id') for c in claims];byid={c.get('id'):c for c in claims};rby={r.get('path'):r for r in reports}
 if len(claims)!=249 or C.get('selection_rule',{}).get('claim_count')!=249 or len(ids)!=len(set(ids)):add(e,'claim-completeness')
 if set(rby)!=set(ipaths) or len(reports)!=46 or C.get('selection_rule',{}).get('zero_claim_reports')!=[]:add(e,'report-universe')
 for c in claims:
  if REQ-set(c):add(e,'decision-card-fields');continue
  rp=c['report_path'];src=source/Path(rp).name;mf=c['reviewed_manifest'];mp=book/mf.get('path','')
  if not src.is_file() or c['source_commit']!=PIN or c['source_sha256']!=sha(src):add(e,'evidence-hash')
  if not mp.is_file() or mf.get('sha256')!=sha(mp):add(e,'manifest-hash')
  else:
   ls=mp.read_text().splitlines();n=mf.get('line')
   if not isinstance(n,int) or n<1 or n>len(ls) or ls[n-1]!=mf.get('exact_excerpt'):add(e,'manifest-locator')
   else:
    row=ls[n-1];dm=re.search(r'(?:Domain `|domain=`)([^`]+)`',row)
    expected_md=dm.group(1) if dm else None
    if expected_md is None and rp in rby and len(rby[rp].get('metric_domains',[]))==1:expected_md=rby[rp]['metric_domains'][0]
    if expected_md is not None and c.get('metric_domain',{}).get('id')!=expected_md:add(e,'metric-boundary')
  if c['canonical_disposition'] not in STATUSES:add(e,'disposition-binding')
  if c['decision_outcome']!='open' or c['local_dominance_eligible'] is not False:add(e,'mandatory-open')
  if not set(c['objective_classifications'])<=OBJ or not c['objective_classifications']:add(e,'objective-tags')
  md=c['metric_domain']
  if md.get('noncomposable') is not True or md.get('composable_with')!=[] or not md.get('id') or not md.get('producer_units_state'):add(e,'metric-boundary')
  for k in ('materially_distinct_alternatives','missing_decisive_dimensions','safe_replacement','limitation','open_or_reversal_condition','current_evidence_owner'):
   v=c[k]
   if not isinstance(v,dict) or not v.get('binding') or v.get('mandatory') is False:add(e,'decision-semantic-binding')
  if c['mechanism_family'] not in {f.get('id') for f in C.get('family_bound',{}).get('families',[])}:add(e,'mechanism-binding')
 for path,r in rby.items():
  bound=[c for c in claims if c.get('report_path')==path];src=source/Path(path).name
  if not bound or r.get('sha256')!=sha(src) or r.get('line_count')!=len(src.read_text().splitlines()) or r.get('claim_ids')!=[c['id'] for c in bound] or r.get('claim_count')!=len(bound) or r.get('metric_domains')!=sorted({c['metric_domain']['id'] for c in bound}) or r.get('mechanisms')!=sorted({c['mechanism_family'] for c in bound}):add(e,'report-binding')
  mp=book/r.get('reviewed_manifest_path','');sec=r.get('reviewed_manifest_section',{})
  if not mp.is_file() or not isinstance(sec.get('start_line'),int) or sec.get('end_line',0)<sec.get('start_line',1):add(e,'report-context')
 fams=C.get('family_bound',{});fl=fams.get('families',[])
 if fams.get('actual')!=7 or not 5<=len(fl)<=7 or len({f.get('id') for f in fl})!=7:add(e,'family-bound')
 for f in fl:
  cs=[c for c in claims if c.get('mechanism_family')==f.get('id')];domains=sorted({rby[c['report_path']]['portfolio_domain'] for c in cs if c.get('report_path') in rby})
  if not cs or len(domains)<2 or f.get('claim_ids')!=[c['id'] for c in cs] or f.get('independent_portfolio_domains')!=domains:add(e,'family-binding')
 if D.get('schema')!='ch22-predraft-registers-v3' or D.get('source_commit')!=PIN or D.get('constraint_first') is not True or D.get('dispositions_are_evidence_filters_not_spine') is not True:add(e,'derived-framing')
 if D.get('claim_register_sha256')!=sha(claims_path):add(e,'derived-claim-hash')
 closure=D.get('mandatory_contradiction_closure_matrix',[])
 if len(closure)!=11 or len({x.get('mandatory_class') for x in closure})!=11 or any(x.get('all_nonaffirmative') is not True or x.get('outcome')!='open' or not x.get('claim_ids') for x in closure):add(e,'mandatory-contradiction-closure')
 for x in closure:
  if any(cid not in byid for cid in x.get('claim_ids',[])) or x.get('canonical_dispositions')!=[byid[cid]['canonical_disposition'] for cid in x.get('claim_ids',[])]:add(e,'mandatory-contradiction-closure')
 stale=D.get('stale_conclusion_register',[]);neg=D.get('negative_evidence_register',[]);rev=collections.defaultdict(lambda:{'stale':[],'negative':[]})
 for x in stale:
  cid=x.get('prior_claim_id')
  if cid not in byid or x.get('canonical_disposition')!=byid[cid]['canonical_disposition'] or x.get('outcome')!='open':add(e,'stale-binding')
  else:rev[cid]['stale'].append(x.get('id'))
 for x in neg:
  if x.get('outcome')!='open' or not x.get('claim_links'):add(e,'negative-binding')
  for cid in x.get('claim_links',[]):
   if cid not in byid:add(e,'negative-binding')
   else:rev[cid]['negative'].append(x.get('id'))
 if D.get('conflict_reverse_index')!=dict(sorted(rev.items())):add(e,'conflict-reverse-link')
 rr=D.get('recurring_regime_register',[]);ar=D.get('alternatives_tradeoff_register',[])
 if len(rr)!=7 or len(ar)!=7 or {x.get('mechanism_family') for x in rr}!={f['id'] for f in fl}:add(e,'recurring-register')
 for x in rr:
  cs=[c for c in claims if c['mechanism_family']==x.get('mechanism_family')]
  if x.get('claim_ids')!=[c['id'] for c in cs] or len(x.get('independent_portfolio_domains',[]))<2 or x.get('decision_outcome')!='open':add(e,'recurring-register')
 if any(x.get('outcome')!='open' or x.get('noncomposable_across_metric_domains') is not True or not x.get('claim_alternative_bindings') for x in ar):add(e,'alternatives-register')
 lim=D.get('limitation_register',[])
 if {x.get('metric_domain') for x in lim}!={c['metric_domain']['id'] for c in claims} or any(x.get('mandatory_outcome')!='open' for x in lim):add(e,'limitation-register')
 matrix=D.get('reconciliation_matrix',[]);mr={'id','conceptual_domain','producer','units','state_history','evidence_rung','modeled_costs','omitted_costs','behavior_class','evidence'}
 if len(matrix)!=8 or any(mr-set(x) or not x['modeled_costs'] or not x['omitted_costs'] for x in matrix):add(e,'reconciliation-matrix')
 ext=D.get('external_stale_conclusion',{});ep=book/ext.get('path','')
 if not ep.is_file() or ext.get('sha256')!=sha(ep) or ext.get('line')!=62 or ext.get('status')!='superseded':add(e,'external-evidence')
 if R.get('schema')!='ch22-focused-reconciliation-v3' or R.get('tusim_commit')!=PIN or R.get('all_checks_passed') is not True or R.get('tusim_source_preserved_after') is not True or set(R.get('domains',{}))!={'geometry','memory_overlap','numerics_representation','operators','sharing_topology','runtime_static_policy'}:add(e,'reconciliation')
 recon_path=Path(D.get('mandatory_contradiction_closure_matrix',[{}])[0].get('reconciliation',{}).get('reconciliation_path',''))
 runbase=(book/recon_path).parent if recon_path else None
 if runbase and runbase.is_dir():
  for key,d in R.get('domains',{}).items():
   lp=runbase/d.get('log','')
   if not lp.is_file() or d.get('log_sha256')!=sha(lp):add(e,'reconciliation-log-hash')
   aux=d.get('auxiliary_evidence')
   if aux:
    ap=runbase/aux.get('log','')
    if not ap.is_file() or aux.get('log_sha256')!=sha(ap):add(e,'reconciliation-log-hash')
  bp=runbase/'source-state-before.json';ap=runbase/'source-state-after.json'
  if not bp.is_file() or not ap.is_file() or R.get('source_state_before_sha256')!=sha(bp) or R.get('source_state_after_sha256')!=sha(ap) or bp.read_bytes()!=ap.read_bytes():add(e,'source-preservation')
  op=(runbase/'operators.log').read_text() if (runbase/'operators.log').is_file() else '';parts=re.split(r'^=== repeat \d+/3 ===\n',op,flags=re.M)[1:]
  if len(parts)!=3 or any(not re.search(r'ATTN diff golden_err=[0-9.]+ deviates=1 scales_equal=1',p) or 'PIPE depth2 sequential_total=402 saved=200' not in p or 'CH14_PROBE SUMMARY failures=0' not in p for p in parts):add(e,'operator-repeat-contract')
  sched=(runbase/'runtime_static_policy.log').read_text() if (runbase/'runtime_static_policy.log').is_file() else '';rows=parse_sched(sched)
  if R.get('observations',{}).get('scheduler_matrix')!=rows or len(rows)!=15:add(e,'scheduler-matrix')
 else:add(e,'reconciliation-evidence-path')
 if any(not x.get('passed') for xs in R.get('checks',{}).values() for x in xs):add(e,'reconciliation-checks')
 return sorted(set(e))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--claims',required=True);ap.add_argument('--derived',required=True);ap.add_argument('--recon',required=True);ap.add_argument('--source',required=True);ap.add_argument('--inventory',required=True);ap.add_argument('--book-root',required=True);ap.add_argument('--mutation-out',required=True);a=ap.parse_args()
 C=json.load(open(a.claims));D=json.load(open(a.derived));R=json.load(open(a.recon));I=json.load(open(a.inventory));base=validate(C,D,R,I,a.source,a.claims,a.book_root);cases=[]
 def test(name,mut,expected):
  c=copy.deepcopy(C);d=copy.deepcopy(D);r=copy.deepcopy(R);i=copy.deepcopy(I);mut(c,d,r,i);errs=validate(c,d,r,i,a.source,a.claims,a.book_root);cases.append({'name':name,'expected_error':expected,'detected':expected in errs,'errors':errs})
 test('drop-semantic-claim',lambda c,d,r,i:c['claims'].pop(),'claim-completeness')
 test('drop-report',lambda c,d,r,i:c['reports'].pop(),'report-universe')
 test('corrupt-inventory-hash',lambda c,d,r,i:i['reports'][0].__setitem__('sha256','0'*64),'inventory-binding')
 test('count-preserving-inventory-substitution',lambda c,d,r,i:i['reports'][0].__setitem__('path',i['excluded_nonreport'][0]['path']),'inventory-universe')
 test('corrupt-source-hash',lambda c,d,r,i:c['claims'][0].__setitem__('source_sha256','0'*64),'evidence-hash')
 test('corrupt-manifest-hash',lambda c,d,r,i:c['claims'][0]['reviewed_manifest'].__setitem__('sha256','0'*64),'manifest-hash')
 test('corrupt-manifest-locator',lambda c,d,r,i:c['claims'][0]['reviewed_manifest'].__setitem__('line',1),'manifest-locator')
 test('invalid-disposition',lambda c,d,r,i:c['claims'][0].__setitem__('canonical_disposition','unreviewed'),'disposition-binding')
 test('garbage-objective',lambda c,d,r,i:c['claims'][0].__setitem__('objective_classifications',['garbage']),'objective-tags')
 test('compose-metric-domains',lambda c,d,r,i:c['claims'][0]['metric_domain'].__setitem__('composable_with',['other']),'metric-boundary')
 test('count-preserving-domain-reassign',lambda c,d,r,i:c['claims'][0]['metric_domain'].__setitem__('id',next(x['metric_domain']['id'] for x in c['claims'] if x['metric_domain']['id']!=c['claims'][0]['metric_domain']['id'])),'metric-boundary')
 test('close-open-outcome',lambda c,d,r,i:c['claims'][0].__setitem__('decision_outcome','selected'),'mandatory-open')
 test('manufacture-local-dominance',lambda c,d,r,i:c['claims'][0].__setitem__('local_dominance_eligible',True),'mandatory-open')
 test('erase-alternative-binding',lambda c,d,r,i:c['claims'][0]['materially_distinct_alternatives'].__setitem__('binding',''),'decision-semantic-binding')
 test('erase-missing-dimension-binding',lambda c,d,r,i:c['claims'][0]['missing_decisive_dimensions'].__setitem__('binding',''),'decision-semantic-binding')
 test('erase-safe-replacement',lambda c,d,r,i:c['claims'][0]['safe_replacement'].__setitem__('binding',''),'decision-semantic-binding')
 test('erase-limitation',lambda c,d,r,i:c['claims'][0]['limitation'].__setitem__('binding',''),'decision-semantic-binding')
 test('eight-families',lambda c,d,r,i:c['family_bound'].__setitem__('actual',8),'family-bound')
 test('break-report-claim-membership',lambda c,d,r,i:c['reports'][0]['claim_ids'].pop(),'report-binding')
 test('drop-mandatory-contradiction',lambda c,d,r,i:d['mandatory_contradiction_closure_matrix'].pop(),'mandatory-contradiction-closure')
 test('reaffirm-mandatory-contradiction',lambda c,d,r,i:d['mandatory_contradiction_closure_matrix'][0]['canonical_dispositions'].__setitem__(0,'retained'),'mandatory-contradiction-closure')
 test('break-conflict-reverse',lambda c,d,r,i:d['conflict_reverse_index'].pop(next(iter(d['conflict_reverse_index']))),'conflict-reverse-link')
 test('close-derived-register',lambda c,d,r,i:d['recurring_regime_register'][0].__setitem__('decision_outcome','selected'),'recurring-register')
 test('drop-reconciliation-row',lambda c,d,r,i:d['reconciliation_matrix'].pop(),'reconciliation-matrix')
 test('drop-reconciliation-domain',lambda c,d,r,i:r['domains'].pop('geometry'),'reconciliation')
 test('corrupt-log-hash',lambda c,d,r,i:r['domains']['geometry'].__setitem__('log_sha256','0'*64),'reconciliation-log-hash')
 test('mutate-scheduler-observation',lambda c,d,r,i:r['observations']['scheduler_matrix'][0].__setitem__('cycles',999),'scheduler-matrix')
 test('lose-source-preservation',lambda c,d,r,i:r.__setitem__('tusim_source_preserved_after',False),'reconciliation')
 tree=ast.parse(Path(__file__).read_text());assert_nodes=[x for x in ast.walk(tree) if isinstance(x,ast.Assert)]
 if assert_nodes:base.append('validator-contains-assert')
 result={'schema':'ch22-predraft-mutation-v3','baseline_errors':sorted(set(base)),'baseline_passed':not base,'cases':cases,'detected':sum(x['detected'] for x in cases),'total':len(cases)};result['passed']=result['baseline_passed'] and result['detected']==result['total']
 Path(a.mutation_out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'baseline_errors':result['baseline_errors'],'mutations':f"{result['detected']}/{result['total']}",'passed':result['passed']},sort_keys=True));raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__':main()
