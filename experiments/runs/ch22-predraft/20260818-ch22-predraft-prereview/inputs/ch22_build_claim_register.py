#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
PIN="e918c80b6fce833cd1fcae97730fa841c2176f25"
FAMILY_META={
"F1-shape-fit":{"name":"Shape fit and useful work","objectives":["linked_estimated_cycles","modeled_utilization","modeled_dma_fraction"],"missing":["calibrated_frequency","area","power","full-workload_distribution","layout_constraints"],"reversal":"Reopen if linked execution, a changed shape distribution, or calibrated implementation cost changes the local ordering.","alts":[("small-or-square-array","better edge fit and lower fill/drain exposure","lower peak parallelism"),("larger-or-asymmetric-array","higher peak work on fitting shapes","more idle lanes, fill/drain, area and verification cost"),("dataflow-or-tiling-switch","can recover utilization without resizing","control, buffering, routing and validation complexity")]},
"F2-supply-visibility":{"name":"Supply, storage, overlap, and visibility","objectives":["linked_estimated_cycles","modeled_dma_cycles","modeled_stall_cycles","modeled_storage_bytes"],"missing":["physical_SRAM_timing","bank_port_cost","DRAM_controller_calibration","FIFO_backpressure","area","power"],"reversal":"Reopen if calibrated memory timing, banking, finite queues, or corrected overlap visibility changes the bottleneck or ordering.","alts":[("provision-bandwidth-or-capacity","reduces modeled supply pressure","area, power, floorplan and leakage cost"),("overlap-or-double-buffer","can hide supply latency","extra storage, stale-state risk and lifecycle complexity"),("retile-or-reorder","reduces live set or transfers","compiler/runtime policy and verification cost") ]},
"F3-representation":{"name":"Representation, compression, and numerical fidelity","objectives":["payload_bytes","linked_estimated_cycles","decoder_cycles","local_numerical_error"],"missing":["application_accuracy","calibrated_decoder_area","decoder_energy","finite_FIFO_backpressure","direct_compressed_feed_cost"],"reversal":"Reopen if application accuracy, decoder throughput/cost, value distribution, or exact rounding scope differs from the measured regime.","alts":[("raw-or-wide","simple exact transport and compute","higher traffic, storage, and compute cost"),("quantized-or-low-precision","lower traffic and potentially higher throughput","accuracy, calibration and accumulator risk"),("compressed-or-structured-sparse","reduces payload/work in suitable distributions","decoder, metadata, irregularity and verification cost") ]},
"F4-operator":{"name":"Operator semantics and working-set irregularity","objectives":["linked_estimated_cycles","modeled_stall_cycles","local_output_error","working_set_bytes"],"missing":["model_level_accuracy","calibrated_special_function_cost","layout_transform_cost","end_to_end_operator_fusion","area","power"],"reversal":"Reopen if functional correctness, layout, fused boundaries, workload shapes, or calibrated special-function cost changes.","alts":[("dedicated-operator-engine","high modeled throughput in target regime","area, power, inflexibility and verification"),("shared-array-lowering","reuses datapath","tiling, scratch, fill/drain and control cost"),("hybrid-or-fused-path","can avoid intermediate traffic","larger coupled validation surface and scheduling complexity") ]},
"F5-sharing":{"name":"Sharing, topology, and contention","objectives":["linked_estimated_cycles","modeled_message_cycles","modeled_contention_cycles","modeled_scaling_efficiency"],"missing":["physical_NoC_timing","router_buffering","coherence_or_consistency","real_traffic_distribution","area","power"],"reversal":"Reopen if traffic shape, placement, routing order, synchronization, or calibrated network cost changes.","alts":[("shared-fabric-or-ring","low implementation cost at small scale","serialization and contention"),("mesh-or-richer-topology","more path diversity and scale","router/link area, power and routing complexity"),("broadcast-or-local-replication","can reduce repeated traffic","storage, consistency and invalidation cost") ]},
"F6-policy-boundary":{"name":"Static/runtime policy and state boundaries","objectives":["linked_estimated_cycles","modeled_switch_cycles","saved_state_bytes","schedule_length"],"missing":["compiler_integration","runtime_arrival_distribution","preemption_safety","state_completeness","physical_context_bandwidth"],"reversal":"Reopen if ownership boundaries, saved-state coverage, runtime arrivals, or compiler/runtime integration is implemented and measured.","alts":[("static-specialization","simple predictable execution","less adaptability and code/config proliferation"),("runtime-policy","adapts to arrivals and local state","state, control and validation complexity"),("hybrid-guarded-policy","retains static defaults with selected adaptation","boundary contracts and reversal testing burden") ]},
}

def family(n):
 if any(k in n for k in ["interconnect","multicore","broadcast"]): return "F5-sharing"
 if any(k in n for k in ["precision","rounding","int8","compression","decoder","structured-2of4","bitmap"]): return "F3-representation"
 if any(k in n for k in ["attention","conv","pool","norm","softmax","fused-activation"]): return "F4-operator"
 if any(k in n for k in ["context","scheduler"]): return "F6-policy-boundary"
 if any(k in n for k in ["dma","dram","sram","gbuf","double-buffer","pipeline-depth","db-pe"]): return "F2-supply-visibility"
 return "F1-shape-fit"

def disposition(s):
 x=s.lower()
 if re.search(r'\b(stale|retire|invalidated|superseded|no longer valid|replaced by)\b',x): return "retire-stale"
 if re.search(r'(no benefit|no additional|not improve|slower|worse|fails?|cannot|invalid|erases|negative)',x): return "retain-negative-evidence"
 if re.search(r'(should|must|prefer|recommend|use as|default|avoid|design implication|actionable)',x): return "retain-design-option"
 if re.search(r'(wins?|strictly faster|best|optimal|outperform|dominates)',x): return "retain-local-dominance"
 return "retain-local-observation"

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--inventory',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 source=Path(a.source); inv=json.loads(Path(a.inventory).read_text())
 names=[Path(r['path']).name for r in inv['reports']]
 if inv.get('source_commit')!=PIN or len(names)!=46: raise SystemExit('inventory pin/count mismatch')
 hi=re.compile(r'(?i)(result|finding|conclusion|actionable|recommend|implication|decision|trade.?off|takeaway|analysis|interpretation|summary|bottleneck|crossover|comparison|limitation|negative|what this means|why|observations?)')
 claimkw=re.compile(r'(?i)(should|must|prefer|recommend|use |avoid|winner|wins|faster|slower|speedup|bottleneck|optimal|sweet spot|break.?even|crossover|dominates|strictly|never|retire|stale|invalid|unmodeled|unquantified|limitation|reversal|overhead|penalty|gain|improvement|reduc|increas|saturat|no benefit|no additional|not improve|competitive|worth|best|worse|erases|outperform|bound|scal|only|default|trade.?off)')
 num=re.compile(r'(\d+(?:\.\d+)?\s*%|\d+(?:\.\d+)?\s*[×x]|\d[\d,]*(?:\.\d+)?\s*(?:cycles?|B/cycle|bytes?|KB|MB|TOPS|MFLOPs?|MACs?|GB/s|ops/cycle))',re.I)
 reports=[]; claims=[]
 for name in names:
  p=source/name; raw=p.read_bytes(); lines=raw.decode().splitlines(); fam=family(name); meta=FAMILY_META[fam]
  reports.append({"path":f"docs/exploration/{name}","sha256":hashlib.sha256(raw).hexdigest(),"lines":len(lines),"family":fam,"metric_domain_id":"MD:"+name[:-3],"claim_ids":[]})
  active=False; level=99
  for lineno,line in enumerate(lines,1):
   m=re.match(r'^(#{1,6})\s+(.*)',line)
   if m:
    lvl=len(m.group(1)); title=m.group(2)
    if lvl<=level: active=False; level=99
    if lvl>=2 and hi.search(title): active=True; level=lvl
    continue
   s=line.strip()
   if not s or re.match(r'^\|?\s*:?-{3}',s) or s.startswith('```') or s.startswith('<!--') or re.match(r'(?i)^\*\*(question|hypothesis|configs? tested)',s) or re.match(r'(?i)^(next candidates|future work|follow-up experiment)',s): continue
   is_table=s.startswith('|') and s.count('|')>=3
   if is_table and not re.search(r'\d',s): continue
   prose=not s.startswith('|')
   eligible=(active and (is_table or claimkw.search(s) or num.search(s))) or (prose and claimkw.search(s) and (num.search(s) or re.search(r'(?i)(should|must|prefer|recommend|avoid|default|unmodeled|unquantified|limitation|wins|winner|bottleneck|optimal|no benefit)',s)))
   if not eligible: continue
   cid=f"C22-{len(claims)+1:04d}"; disp=disposition(s)
   missing=list(meta['missing'])
   local_eligible=disp=="retain-local-dominance" and bool(num.search(s))
   record={"id":cid,"claim_text":s,"source_kind":"exploration-report-local","provenance_class":"source-claim","canonical_disposition":disp,"decision_outcome":"open" if missing else ("local" if local_eligible else "open"),"regime":{"report_local":name[:-3],"validity_conditions":["Exact pinned report and line.","Only the report's stated workload, configuration, equations, and modeled counters.","Functional or linked measurements do not authorize unmeasured physical metrics."]},"conflict_links":[],"evidence":{"commit":PIN,"path":f"docs/exploration/{name}","sha256":reports[-1]['sha256'],"line_start":lineno,"line_end":lineno,"exact_excerpt":line},"metric_domain":{"id":"MD:"+name[:-3],"noncomposable":True,"composable_with":[],"boundary":"Only the report's stated workload, configuration, equations, and modeled counters; no cross-report scalarization."},"family":fam,"objective_tags":meta['objectives'],"materially_distinct_alternatives":[{"option":o,"gain_regime":g,"costs":c} for o,g,c in meta['alts']],"missing_decisive_dimensions":missing,"open_or_reversal_condition":meta['reversal'],"local_dominance_eligible":local_eligible,"scope_guards":["No portfolio-wide Pareto claim.","No inferred physical timing, area, power, energy, or application accuracy.","No compiler/runtime/ONNX composition implied."]}
   claims.append(record); reports[-1]['claim_ids'].append(cid)
 doc={"schema":"ch22-claim-register-v1","source_commit":PIN,"selection_rule":{"description":"Conservative atomization of every numeric table row or quantitative/prescriptive sentence under result/finding/conclusion/analysis/implication/trade-off/limitation sections, plus explicit quantitative or prescriptive conclusions elsewhere.","overinclusion_policy":"Keep ambiguous candidates as open report-local observations; do not silently drop them.","exclusions":["questions","hypotheses","pure setup/configuration","headings","table headers and separators","future-work prompts without a conclusion"]},"closed_framing":{"organization":"constraint-first","dispositions_are_filters_not_spine":True,"forbidden":["Chapter 21 sweep-construction tutorial","report chronology","cross-domain scalarization","portfolio-wide Pareto frontier","uncalibrated physical metrics","compiler/runtime/ONNX composition"]},"family_bound":{"min":5,"max":7,"actual":len(FAMILY_META),"families":[{"id":k,**v} for k,v in FAMILY_META.items()]},"reports":reports,"claims":claims,"summary":{"report_count":len(reports),"claim_count":len(claims),"reports_without_claims":sum(not r['claim_ids'] for r in reports),"metric_domain_count":len(reports),"all_decisions_open_where_dimensions_missing":all(c['decision_outcome']=='open' for c in claims if c['missing_decisive_dimensions'])}}
 Path(a.out).write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n")
 print(json.dumps(doc['summary'],sort_keys=True))
if __name__=='__main__':main()
