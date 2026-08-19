#!/usr/bin/env python3
import argparse,hashlib,json,re
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--claims',required=True);ap.add_argument('--recon',required=True);ap.add_argument('--recon-relative',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 C=json.load(open(a.claims));R=json.load(open(a.recon)); bookroot=Path(a.claims).resolve().parent.parent; byfam={f['id']:[] for f in C['family_bound']['families']}
 for r in C['reports']:byfam[r['family']].append(r['path'])
 def claim(substr,path=None):
  xs=[c for c in C['claims'] if substr.lower() in c['claim_text'].lower() and (path is None or c['evidence']['path'].endswith(path))]
  if not xs:raise KeyError((substr,path))
  return xs[0]['id']
 famdesc={
  'F1-shape-fit':('alignment, tile-count, fill/drain, and useful-work fit change the preferred geometry by workload shape','Treat geometry or dataflow winners as report-local until linked routing and representative shape distributions are fixed.'),
  'F2-supply-visibility':('bandwidth, capacity, banking, and overlap help only while the named supply or visibility constraint dominates','Do not equate a modeled speedup field with observed overlap; retain counter and lifecycle defects as negative evidence.'),
  'F3-representation':('reduced payload or arithmetic work wins only when decode, metadata, rounding scope, and accuracy remain acceptable','Payload-only and local-error winners remain open without decoder and application-accuracy closure.'),
  'F4-operator':('operator shape, scratch footprint, special functions, and functional correctness can dominate nominal array throughput','No performance ordering survives a failed or non-reproducible functional boundary.'),
  'F5-sharing':('topology and sharing reverse with traffic shape, route order, placement, and scale','No universal topology or sharing winner; compare only within the exact traffic matrix and heuristic domain.'),
  'F6-policy-boundary':('static/runtime choices become visible only when modeled policy changes schedule or state movement','Do not imply compiler/runtime composition; identical counters mean policy preference stays open.'),
 }
 recurring=[]
 for f in C['family_bound']['families']:
  rid=f['id'];reg,rule=famdesc[rid]
  recurring.append({'id':'RR-'+rid,'family':rid,'recurring_regime':reg,'reports':byfam[rid],'evidence_filter':rule,'decision_outcome':'open','reversal_condition':f['reversal']})
 alternatives=[]
 for f in C['family_bound']['families']:
  alternatives.append({'family':f['id'],'metric_domains':[r['metric_domain_id'] for r in C['reports'] if r['family']==f['id']],'noncomposable_across_domains':True,'alternatives':[{'option':o,'gain_regime':g,'costs':cost} for o,g,cost in f['alts']],'missing_decisive_dimensions':f['missing'],'outcome':'open'})
 recon_ev={'path':a.recon_relative,'sha256':sha(a.recon),'tusim_commit':R['tusim_commit']}
 stale=[
 {'id':'SC-01','prior_claim_id':claim('OS dataflow wins universally','attention-engine-sweep.md'),'status':'retired-as-universal','reason':'The linked operator probe produces incorrect attention output and repeat-varying golden error; throughput cannot authorize a universal operator choice.','counterevidence':{**recon_ev,'domain':'operators','observed':R['observations']}},
 {'id':'SC-02','prior_claim_id':claim('Dataflow choice (WS vs OS) has negligible','dataflow-comparison-gemm128.md'),'status':'retired-for-linked-current-model','reason':'The process-global output-stationary request leaves an existing core on weight-stationary, and explicit linked WS/OS/RS execution differs materially.','counterevidence':{**recon_ev,'domain':'geometry','observation':'requested OS; effective core WS; linked WS/OS/RS cycles 81920/20480/50176'}},
 {'id':'SC-03','prior_claim_id':claim('Double-buffering is the single highest-leverage','double-buffer-mtiling-recovery.md'),'status':'narrowed-to-analytical-report-domain','reason':'The focused linked probe reports nonzero speedup but saved=0, an infinite empty-pipeline speedup, and state loss across reinitialization/context restore.','counterevidence':{**recon_ev,'domain':'memory_overlap','observation':'seq/piped 8/7 saved=0; empty speedup=inf; db_lost=1'}},
 {'id':'SC-04','prior_claim_id':claim('payload bytes are not end-to-end latency','bitmap-weight-compression.md'),'status':'superseded-payload-only-ordering','reason':'Retain the follow-up decoder-aware conclusion: narrow decode can reverse payload-only ordering; no end-to-end compression winner follows from bytes.','counterevidence':{**recon_ev,'domain':'numerics_representation','observation':'dense_total=34307 versus sparse_total=77312 in narrow regime'}},
 {'id':'SC-05','prior_claim_id':claim('To make scheduling policy choice visible','scheduler-policy-sweep.md'),'status':'confirmed-open','reason':'All three policies remain exactly identical in cycles, barriers, hoists, and length across all five focused workloads.','counterevidence':{**recon_ev,'domain':'runtime_static_policy','observation':'ASAP=ALAP=BALANCED for every tested topology'}},
 {'id':'SC-06','prior_claim_id':claim('No universal topology winner','interconnect-contention-traffic-matrix.md'),'status':'retained-and-strengthened','reason':'Route-order transpose reverses the winner and a disjoint-route case disproves global-max composition as an exact estimator.','counterevidence':{**recon_ev,'domain':'sharing_topology','observation':'606/222 reverses to 222/606; heuristic estimate 158 versus isolated 94 and bottleneck 128'}},
 {'id':'SC-07','prior_claim_external':{'path':'references/ch21-sweep-method-primary-sources.md','sha256':sha(bookroot/'references/ch21-sweep-method-primary-sources.md'),'line':62,'text':'- Chapter 22 alone owns preference rules, Pareto selection across the portfolio, and portfolio-wide conclusions about preferable Tusim architecture regimes.'},'status':'retired-by-closed-framing','reason':'Chapter 22 may compare only inside explicit compatible metric domains; it will not construct a portfolio-wide Pareto frontier.'},
 ]
 negative=[
 {'id':'NE-01','finding':'A requested dataflow label need not be the linked active route on an already-created core.','claim_links':[stale[1]['prior_claim_id']],'evidence':{**recon_ev,'domain':'geometry'}},
 {'id':'NE-02','finding':'Reported overlap speedup can coexist with saved=0; the empty case can report infinity.','claim_links':[stale[2]['prior_claim_id']],'evidence':{**recon_ev,'domain':'memory_overlap'}},
 {'id':'NE-03','finding':'Structured sparsity is slower than dense under a narrow decoder.','claim_links':[claim('2:4 is not universally faster','structured-2of4-sweep.md')],'evidence':{**recon_ev,'domain':'numerics_representation'}},
 {'id':'NE-04','finding':'Stochastic rounding is seed- and invocation-order-sensitive unless seed scope is made permutation-stable.','claim_links':[claim('stochastic','rounding-mode-accuracy-sweep.md')],'evidence':{**recon_ev,'domain':'numerics_representation'}},
 {'id':'NE-05','finding':'Attention output deviates from the local golden result and the error changes across identical process repeats.','claim_links':[stale[0]['prior_claim_id']],'evidence':{**recon_ev,'domain':'operators'}},
 {'id':'NE-06','finding':'Topology and deterministic routing winners reverse with traffic transpose; the combined heuristic is not an exact network latency.','claim_links':[stale[5]['prior_claim_id']],'evidence':{**recon_ev,'domain':'sharing_topology'}},
 {'id':'NE-07','finding':'Scheduler policy labels produce no metric distinction in the five-workload linked sweep.','claim_links':[stale[4]['prior_claim_id']],'evidence':{**recon_ev,'domain':'runtime_static_policy'}},
 {'id':'NE-08','finding':'Context save scope and state bandwidth change modeled switch cost by orders of magnitude, so a single context cost is not portable.','claim_links':[claim('No mode is universally preferable','context-switch-state-scope.md')],'evidence':{**recon_ev,'domain':'runtime_static_policy'}},
 ]
 limitations=[]
 for f in C['family_bound']['families']:
  limitations.append({'id':'LIM-'+f['id'],'family':f['id'],'missing':f['missing'],'effect':'Blocks cross-domain decision closure and any inferred physical metric.','mandatory_outcome':'open','closure_test':f['reversal']})
 limitations += [
 {'id':'LIM-global-01','family':'global','missing':['calibrated physical timing/area/power/energy','application-level accuracy','representative workload weights'],'effect':'Blocks portfolio scalarization and physical architecture ranking.','mandatory_outcome':'open','closure_test':'Supply calibrated, commensurate objective vectors and declared preference/weighting rules inside one domain.'},
 {'id':'LIM-global-02','family':'global','missing':['executable compiler/runtime/ONNX composition bridge'],'effect':'Blocks composition claims beyond the linked C-model boundaries.','mandatory_outcome':'open','closure_test':'Implement and validate the bridge with exact input/output and ownership boundaries.'},
 ]
 doc={'schema':'ch22-predraft-registers-v1','source_commit':C['source_commit'],'claim_register_sha256':sha(a.claims),'constraint_first':True,'dispositions_are_evidence_filters_not_spine':True,'recurring_regime_register':recurring,'alternatives_tradeoff_register':alternatives,'stale_conclusion_register':stale,'negative_evidence_register':negative,'limitation_register':limitations,'summary':{'recurring_regimes':len(recurring),'families':len(byfam),'reports_assigned_once':sum(len(x) for x in byfam.values()),'alternative_families':len(alternatives),'stale_or_narrowed':len(stale),'negative_findings':len(negative),'limitations':len(limitations),'all_register_outcomes_open':all(x.get('outcome',x.get('decision_outcome','open'))=='open' for x in recurring+alternatives)}}
 Path(a.out).write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n');print(json.dumps(doc['summary'],sort_keys=True))
if __name__=='__main__':main()
