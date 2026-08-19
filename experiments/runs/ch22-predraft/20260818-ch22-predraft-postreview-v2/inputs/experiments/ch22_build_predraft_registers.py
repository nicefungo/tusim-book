#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path
PIN='e918c80b6fce833cd1fcae97730fa841c2176f25'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
MANDATORY={
 'dataflow-route-and-arithmetic': [('dataflow-comparison-gemm128.md','dfcomp-negligible-k256'),('attention-engine-sweep.md','O1.7')],
 'dram-arithmetic-and-device-recommendation': [('dram-type-clock-sweep.md','dram-hbm-zero-improvement'),('dram-type-clock-sweep.md','dram-dont-care-ddr4')],
 'double-buffer-lifecycle-and-speedup': [('double-buffer-mtiling-recovery.md','dbmt-highest-leverage'),('double-buffer-mtiling-recovery.md','dbmt-compiler-prefers-mtiling')],
 'gbuf-threshold-not-universal-sizing': [('gbuf-sizing-sweep.md','gbuf-size-to-footprint'),('gbuf-sizing-sweep.md','gbuf-oversize-zero-benefit')],
 'inert-sram-arbitration-selector': [('sram-arbitration-sweep.md','sramarb-none-rr-equal'),('sram-arbitration-sweep.md','sramarb-rr-default')],
 'precision-and-rounding-causality': [('precision-sweep-gemm128.md','N3.3'),('precision-sweep-gemm128.md','N3.7'),('rounding-mode-accuracy-sweep.md','N4.3'),('rounding-mode-accuracy-sweep.md','N4.5'),('rounding-mode-accuracy-sweep.md','N4.7')],
 'fused-activation-model': [('mma-fused-activation-overhead.md','O5.5')],
 'operator-metric-and-correctness': [('attention-engine-sweep.md','O1.2'),('attention-engine-sweep.md','O1.5')],
 'broadcast-and-topology-story': [('broadcast-dma-multicore-scaling.md','B7'),('broadcast-dma-multicore-scaling.md','B10'),('interconnect-topology-sweep.md','T7')],
 'context-scope-not-continuation': [('context-switch-state-scope.md','X6'),('context-switch-state-scope.md','X7')],
 'scheduler-serial-not-dag-or-compiler': [('scheduler-policy-sweep.md','P2'),('scheduler-policy-sweep.md','P3')],
}
RECON_META=[
 ('RX-geometry','geometry','linked WS/OS/RS estimators plus process-global core route state','linked estimated cycles and route labels','existing core retains creation-time active route',['array/dataflow cycle estimates'],['physical timing','area','power','layout'],'linked estimator, not ordinary runtime'),
 ('RX-memory-capacity','memory_overlap','report-local K*N*2 GBUF threshold equation','bytes and minimum KiB','stateless threshold arithmetic',['weight footprint and fit threshold'],['physical SRAM timing','area/power','queues'],'analytical threshold, not overlap execution'),
 ('RX-memory-overlap','memory_overlap','linked double-buffer controller probe','cycles, bytes, lifecycle flags','bank initialization/active-inactive/context state',['controller counters'],['physical ports','finite backpressure'],'executable model behavior'),
 ('RX-numerics-representation','numerics_representation','linked codec and 2:4 decoder probe','bytes and linked estimated cycles','round trip plus decoder-width regimes',['payload','metadata','decoder estimate'],['direct compressed MMA feed','PPA','application accuracy'],'codec/decoder estimate, no composition bridge'),
 ('RX-numerics-rounding','geometry','linked rounding discriminator','local numeric outputs and invocation-order relation','seed plus process-global invocation order',['local conversion behavior'],['application accuracy','accumulator/store coverage'],'functional local evidence'),
 ('RX-operators','operators','linked attention/compute-engine probe','golden error and report-local counters','three separately delimited repeats',['functional error','pipeline counters'],['calibrated special-function cost','fusion','PPA'],'correctness blocker precedes throughput use'),
 ('RX-sharing','sharing_topology','linked deterministic route/contention heuristic','heuristic cycles/scores','route order and traffic transpose',['route score','isolated/bottleneck terms'],['queued makespan','buffers','physical NoC timing'],'heuristic, not exact network latency'),
 ('RX-runtime-policy','runtime_static_policy','linked context equation plus scheduler matrix','switch cycles, bytes, cycles/barrier/hoist/length','FULL/LIVE/CONTROL and five topologies',['context ledger','serial scheduler matrix'],['safe preemption','runtime arrivals','compiler bridge'],'linked estimator, no compiler/runtime composition'),
]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--claims',required=True);ap.add_argument('--recon',required=True);ap.add_argument('--recon-relative',required=True);ap.add_argument('--book-root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 C=json.load(open(a.claims));R=json.load(open(a.recon));root=Path(a.book_root);runrel=Path(a.recon_relative).parent;by={(Path(c['report_path']).name,c['stable_suffix']):c for c in C['claims']}
 def pick(name,suffix):
  try:return by[(name,suffix)]
  except KeyError:raise SystemExit(f'missing mandatory reviewed claim {name}:{suffix}')
 def ev(c):return {'claim_id':c['id'],'report_path':c['report_path'],'source_sha256':c['source_sha256'],'reviewed_manifest':c['reviewed_manifest']}
 def rev(key,aux=False):
  d=R['domains'][key];x={'reconciliation_path':a.recon_relative,'reconciliation_sha256':sha(a.recon),'log_path':str(runrel/d['log']),'log_sha256':d['log_sha256'],'probe_source':d['source'],'probe_source_sha256':d['source_sha256'],'tusim_commit':R['tusim_commit']}
  if aux and d.get('auxiliary_evidence'):x['auxiliary_evidence']={**d['auxiliary_evidence'],'log_path':str(runrel/d['auxiliary_evidence']['log'])}
  return x
 closure=[];stale=[]
 recon_for={'dataflow-route-and-arithmetic':'geometry','dram-arithmetic-and-device-recommendation':'geometry','double-buffer-lifecycle-and-speedup':'memory_overlap','gbuf-threshold-not-universal-sizing':'memory_overlap','inert-sram-arbitration-selector':'memory_overlap','precision-and-rounding-causality':'numerics_representation','fused-activation-model':'operators','operator-metric-and-correctness':'operators','broadcast-and-topology-story':'sharing_topology','context-scope-not-continuation':'runtime_static_policy','scheduler-serial-not-dag-or-compiler':'runtime_static_policy'}
 for n,pairs in MANDATORY.items():
  cs=[pick(*x) for x in pairs];row={'id':'MC-'+str(len(closure)+1).zfill(2),'mandatory_class':n,'claim_ids':[c['id'] for c in cs],'canonical_dispositions':[c['canonical_disposition'] for c in cs],'all_nonaffirmative':all(c['canonical_disposition'] in {'qualified','superseded','rejected','blocked'} for c in cs),'evidence':[ev(c) for c in cs],'reconciliation':rev(recon_for[n],n=='gbuf-threshold-not-universal-sizing'),'outcome':'open'};closure.append(row)
  for c in cs:stale.append({'id':f"SC-{len(stale)+1:02d}",'prior_claim_id':c['id'],'mandatory_class':n,'canonical_disposition':c['canonical_disposition'],'safe_replacement':c['safe_replacement'],'limitation':c['limitation'],'counterevidence':row['reconciliation'],'outcome':'open'})
 negatives=[
  ('requested dataflow label can differ from creation-time active route','geometry',[pick('dataflow-comparison-gemm128.md','dfcomp-negligible-k256')]),
  ('reported overlap speedup can coexist with saved=0 and an empty case can report infinity','memory_overlap',[pick('double-buffer-mtiling-recovery.md','dbmt-highest-leverage')]),
  ('GBUF fit is a discrete threshold; oversizing preference is not established','memory_overlap',[pick('gbuf-sizing-sweep.md','gbuf-oversize-zero-benefit')]),
  ('narrow decoding can reverse sparse-versus-dense estimates','numerics_representation',[pick('structured-2of4-sweep.md','N5.3')]),
  ('rounding result depends on exact stage, seed, and invocation-order scope','geometry',[pick('rounding-mode-accuracy-sweep.md','N4.5')]),
  ('attention output deviates from local golden while repeat magnitudes are retained separately','operators',[pick('attention-engine-sweep.md','O1.7')]),
  ('route winner reverses under traffic transpose and score is not queued makespan','sharing_topology',[pick('interconnect-contention-traffic-matrix.md','C1')]),
  ('scheduler policy labels are identical in the complete five-by-three focused matrix','runtime_static_policy',[pick('scheduler-policy-sweep.md','P1')]),
  ('context scope changes modeled traffic but does not establish end-to-end continuation','runtime_static_policy',[pick('context-switch-state-scope.md','X6')]),
 ]
 neg=[]
 for i,(finding,key,cs) in enumerate(negatives,1):neg.append({'id':f'NE-{i:02d}','finding':finding,'claim_links':[c['id'] for c in cs],'evidence':rev(key,key=='memory_overlap'),'outcome':'open'})
 reverse=collections.defaultdict(lambda:{'stale':[],'negative':[]})
 for x in stale:reverse[x['prior_claim_id']]['stale'].append(x['id'])
 for x in neg:
  for cid in x['claim_links']:reverse[cid]['negative'].append(x['id'])
 recurring=[];alts=[]
 report_domain={r['path']:r['portfolio_domain'] for r in C['reports']}
 for f in C['family_bound']['families']:
  cs=[c for c in C['claims'] if c['mechanism_family']==f['id']];domains=sorted({report_domain[c['report_path']] for c in cs});reports=sorted({c['report_path'] for c in cs})
  recurring.append({'id':'RR-'+f['id'],'mechanism_family':f['id'],'name':f['name'],'independent_portfolio_domains':domains,'claim_ids':[c['id'] for c in cs],'reports':reports,'producer_separation':'Analogy only; never compose claim metrics, producers, units, or state.','break_case_binding':'Each claim exact reviewed reversal condition.','decision_outcome':'open','manuscript_candidate_family':True})
  alts.append({'mechanism_family':f['id'],'claim_alternative_bindings':[{'claim_id':c['id'],'binding':c['materially_distinct_alternatives']} for c in cs],'objective_classifications':sorted({t for c in cs for t in c['objective_classifications']}),'tradeoff_dimensions':['performance','area_power','accuracy','control','software_contract','verification','fidelity'],'noncomposable_across_metric_domains':True,'outcome':'open'})
 limitations=[]
 for md in sorted({c['metric_domain']['id'] for c in C['claims']}):
  cs=[c for c in C['claims'] if c['metric_domain']['id']==md]
  limitations.append({'id':'LIM-'+str(len(limitations)+1).zfill(2),'metric_domain':md,'claim_ids':[c['id'] for c in cs],'exact_limitations':[{'claim_id':c['id'],'binding':c['limitation']} for c in cs],'effect':'Blocks cross-domain composition and broad decision closure.','mandatory_outcome':'open','closure_test':'Satisfy each reviewed reversal condition using one comparable producer and declared objective.'})
 matrix=[]
 for id,key,producer,units,state,modeled,omitted,behavior in RECON_META:matrix.append({'id':id,'conceptual_domain':key,'producer':producer,'units':units,'state_history':state,'evidence_rung':'exact-pin archive plus frozen book probe','modeled_costs':modeled,'omitted_costs':omitted,'behavior_class':behavior,'evidence':rev(key,id=='RX-memory-capacity')})
 ext='references/ch21-sweep-method-primary-sources.md';external={'path':ext,'sha256':sha(root/ext),'line':62,'status':'superseded','reason':'Portfolio-wide Pareto selection is prohibited; only domain-local comparisons survive.'}
 doc={'schema':'ch22-predraft-registers-v3','source_commit':PIN,'claim_register_sha256':sha(a.claims),'constraint_first':True,'dispositions_are_evidence_filters_not_spine':True,'mandatory_contradiction_closure_matrix':closure,'reconciliation_matrix':matrix,'recurring_regime_register':recurring,'alternatives_tradeoff_register':alts,'stale_conclusion_register':stale,'negative_evidence_register':neg,'conflict_reverse_index':dict(sorted(reverse.items())),'limitation_register':limitations,'external_stale_conclusion':external,'summary':{'reports_covered':len({p for x in recurring for p in x['reports']}),'semantic_claims':len(C['claims']),'manuscript_family_bound':len(recurring),'mandatory_contradiction_classes':len(closure),'mandatory_classes_closed':sum(x['all_nonaffirmative'] for x in closure),'stale_claims':len(stale),'negative_findings':len(neg),'metric_limitations':len(limitations),'reconciliation_rows':len(matrix),'all_register_outcomes_open':all(x.get('outcome',x.get('decision_outcome'))=='open' for x in closure+stale+neg+recurring+alts)}}
 Path(a.out).write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n');print(json.dumps(doc['summary'],sort_keys=True))
if __name__=='__main__':main()
