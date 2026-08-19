#!/usr/bin/env python3
from __future__ import annotations
import argparse,copy,hashlib,json,re
from pathlib import Path
PIN='e918c80b6fce833cd1fcae97730fa841c2176f25'
REQ={'id','claim_text','source_kind','provenance_class','canonical_disposition','decision_outcome','regime','conflict_links','evidence','metric_domain','family','objective_tags','materially_distinct_alternatives','missing_decisive_dimensions','open_or_reversal_condition','local_dominance_eligible','scope_guards'}
NUM=re.compile(r'(\d+(?:\.\d+)?\s*%|\d+(?:\.\d+)?\s*[×x]|\d[\d,]*(?:\.\d+)?\s*(?:cycles?|B/cycle|bytes?|KB|MB|TOPS|MFLOPs?|MACs?|GB/s|ops/cycle))',re.I)
HI=re.compile(r'(?i)(result|finding|conclusion|actionable|recommend|implication|decision|trade.?off|takeaway|analysis|interpretation|summary|bottleneck|crossover|comparison|limitation|negative|what this means|why|observations?)')
KW=re.compile(r'(?i)(should|must|prefer|recommend|use |avoid|winner|wins|faster|slower|speedup|bottleneck|optimal|sweet spot|break.?even|crossover|dominates|strictly|never|retire|stale|invalid|unmodeled|unquantified|limitation|reversal|overhead|penalty|gain|improvement|reduc|increas|saturat|no benefit|no additional|not improve|competitive|worth|best|worse|erases|outperform|bound|scal|only|default|trade.?off)')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def names(inventory):
 inv=json.loads(Path(inventory).read_text())
 return [Path(r['path']).name for r in inv['reports']]
def eligible(source,nms):
 out=set()
 for name in nms:
  lines=(Path(source)/name).read_text().splitlines();active=False;level=99
  for no,line in enumerate(lines,1):
   m=re.match(r'^(#{1,6})\s+(.*)',line)
   if m:
    lvl=len(m.group(1)); title=m.group(2)
    if lvl<=level:active=False;level=99
    if lvl>=2 and HI.search(title):active=True;level=lvl
    continue
   s=line.strip()
   if not s or re.match(r'^\|?\s*:?-{3}',s) or s.startswith(('```','<!--')) or re.match(r'(?i)^\*\*(question|hypothesis|configs? tested)',s) or re.match(r'(?i)^(next candidates|future work|follow-up experiment)',s):continue
   table=s.startswith('|') and s.count('|')>=3
   if table and not re.search(r'\d',s):continue
   prose=not table
   ok=(active and (table or KW.search(s) or NUM.search(s))) or (prose and KW.search(s) and (NUM.search(s) or re.search(r'(?i)(should|must|prefer|recommend|avoid|default|unmodeled|unquantified|limitation|wins|winner|bottleneck|optimal|no benefit)',s)))
   if ok:out.add((f'docs/exploration/{name}',no))
 return out
def validate(C,D,R,source,inventory,claims_path):
 e=[]; inv=json.loads(Path(inventory).read_text()); nms=names(inventory); report_by={r.get('path'):r for r in C.get('reports',[])}; expected_paths={f'docs/exploration/{n}' for n in nms}
 if inv.get('source_commit')!=PIN or inv.get('report_count')!=46 or len(nms)!=46:e.append('inventory')
 if C.get('source_commit')!=PIN:e.append('source-pin')
 if set(report_by)!=expected_paths or len(report_by)!=46:e.append('report-universe')
 claims=C.get('claims',[]);ids=[c.get('id') for c in claims]
 if len(ids)!=len(set(ids)):e.append('claim-id-unique')
 got=set()
 for c in claims:
  miss=REQ-set(c)
  if miss:e.append('decision-card-fields');continue
  ev=c['evidence']; path=ev.get('path'); line=ev.get('line_start'); got.add((path,line))
  p=Path(source)/(path.removeprefix('docs/exploration/') if path else '')
  if not p.is_file() or ev.get('commit')!=PIN or ev.get('sha256')!=sha(p):e.append('evidence-hash')
  else:
   lines=p.read_text().splitlines()
   if not isinstance(line,int) or line<1 or line>len(lines) or ev.get('line_end')!=line or ev.get('exact_excerpt')!=lines[line-1]:e.append('evidence-locator')
  md=c['metric_domain']
  if md.get('noncomposable') is not True or md.get('composable_with')!=[] or not md.get('boundary'):e.append('metric-boundary')
  if not c['objective_tags'] or len(c['materially_distinct_alternatives'])<3 or any(not {'option','gain_regime','costs'}<=set(x) for x in c['materially_distinct_alternatives']):e.append('decision-card-content')
  if not c['regime'].get('validity_conditions') or not c['open_or_reversal_condition'] or len(c['scope_guards'])<3:e.append('decision-card-content')
  if c['missing_decisive_dimensions'] and c['decision_outcome']!='open':e.append('mandatory-open')
  expected_local=c['canonical_disposition']=='retain-local-dominance' and bool(NUM.search(c['claim_text']))
  if c['local_dominance_eligible']!=expected_local:e.append('local-dominance-eligibility')
 exp=eligible(source,nms)
 if got!=exp:e.append('claim-completeness')
 fb=C.get('family_bound',{}); actual=fb.get('actual'); fams=fb.get('families',[])
 if not isinstance(actual,int) or not 5<=actual<=7 or actual!=len(fams) or len({f.get('id') for f in fams})!=actual:e.append('family-bound')
 if {r.get('metric_domain_id') for r in C.get('reports',[])}!={c.get('metric_domain',{}).get('id') for c in claims}:e.append('metric-domain-coverage')
 for path,r in report_by.items():
  p=Path(source)/path.removeprefix('docs/exploration/')
  if r.get('sha256')!=sha(p) or not r.get('claim_ids'):e.append('report-binding')
 if D.get('source_commit')!=PIN or D.get('constraint_first') is not True or D.get('dispositions_are_evidence_filters_not_spine') is not True:e.append('derived-framing')
 bookroot=Path(claims_path).resolve().parent.parent
 if D.get('claim_register_sha256')!=sha(claims_path):e.append('derived-claim-hash')
 for x in D.get('stale_conclusion_register',[]):
  ce=x.get('counterevidence')
  if ce:
   p=bookroot/ce.get('path','')
   if not p.is_file() or ce.get('sha256')!=sha(p):e.append('derived-evidence')
  ext=x.get('prior_claim_external')
  if ext:
   p=bookroot/ext.get('path','')
   if not p.is_file() or ext.get('sha256')!=sha(p):e.append('derived-external-evidence')
   else:
    lines=p.read_text().splitlines(); no=ext.get('line')
    if not isinstance(no,int) or no<1 or no>len(lines) or lines[no-1]!=ext.get('text'):e.append('derived-external-evidence')
 for x in D.get('negative_evidence_register',[]):
  ce=x.get('evidence',{}); p=bookroot/ce.get('path','')
  if not p.is_file() or ce.get('sha256')!=sha(p):e.append('derived-evidence')
 rr=D.get('recurring_regime_register',[]); ar=D.get('alternatives_tradeoff_register',[])
 assigned=[p for x in rr for p in x.get('reports',[])]
 if sorted(assigned)!=sorted(expected_paths) or len(assigned)!=len(set(assigned)):e.append('recurring-register')
 if len(rr)!=actual or len(ar)!=actual or any(x.get('decision_outcome')!='open' for x in rr) or any(x.get('outcome')!='open' or x.get('noncomposable_across_domains') is not True for x in ar):e.append('register-open-boundary')
 if len(D.get('stale_conclusion_register',[]))<7 or len(D.get('negative_evidence_register',[]))<8 or len(D.get('limitation_register',[]))<8:e.append('derived-register-completeness')
 if R.get('tusim_commit')!=PIN or R.get('tusim_source_clean') is not True or R.get('all_checks_passed') is not True or len(R.get('checks',{}))!=6:e.append('reconciliation')
 return sorted(set(e))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--claims',required=True);ap.add_argument('--derived',required=True);ap.add_argument('--recon',required=True);ap.add_argument('--source',required=True);ap.add_argument('--inventory',required=True);ap.add_argument('--mutation-out',required=True);a=ap.parse_args()
 C=json.load(open(a.claims));D=json.load(open(a.derived));R=json.load(open(a.recon));base=validate(C,D,R,a.source,a.inventory,a.claims)
 cases=[]
 def test(name,mut,expected):
  c=copy.deepcopy(C);d=copy.deepcopy(D);r=copy.deepcopy(R);mut(c,d,r);errs=validate(c,d,r,a.source,a.inventory,a.claims);cases.append({'name':name,'detected':expected in errs,'expected_error':expected,'errors':errs})
 test('drop-eligible-claim',lambda c,d,r:c['claims'].pop(), 'claim-completeness')
 test('remove-decision-card-regime',lambda c,d,r:c['claims'][0].pop('regime'), 'decision-card-fields')
 test('remove-alternatives',lambda c,d,r:c['claims'][0].__setitem__('materially_distinct_alternatives',[]),'decision-card-content')
 test('compose-incompatible-domain',lambda c,d,r:c['claims'][0]['metric_domain'].__setitem__('composable_with',['MD:other']),'metric-boundary')
 test('close-with-missing-dimension',lambda c,d,r:c['claims'][0].__setitem__('decision_outcome','selected'),'mandatory-open')
 idx=next(i for i,x in enumerate(C['claims']) if x['canonical_disposition']!='retain-local-dominance')
 test('false-local-dominance-eligibility',lambda c,d,r:c['claims'][idx].__setitem__('local_dominance_eligible',True),'local-dominance-eligibility')
 test('eight-family-manuscript',lambda c,d,r:(c['family_bound'].__setitem__('actual',8),c['family_bound']['families'].extend([{'id':'fake-a'},{'id':'fake-b'}])),'family-bound')
 test('drop-report',lambda c,d,r:c['reports'].pop(),'report-universe')
 test('corrupt-evidence-hash',lambda c,d,r:c['claims'][0]['evidence'].__setitem__('sha256','0'*64),'evidence-hash')
 test('close-register-outcome',lambda c,d,r:d['recurring_regime_register'][0].__setitem__('decision_outcome','selected'),'register-open-boundary')
 result={'schema':'ch22-predraft-mutation-v1','baseline_errors':base,'baseline_passed':not base,'cases':cases,'passed':not base and all(x['detected'] for x in cases),'detected':sum(x['detected'] for x in cases),'total':len(cases)}
 Path(a.mutation_out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'baseline_errors':base,'mutations':f"{result['detected']}/{result['total']}",'passed':result['passed']},sort_keys=True));raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__':main()
