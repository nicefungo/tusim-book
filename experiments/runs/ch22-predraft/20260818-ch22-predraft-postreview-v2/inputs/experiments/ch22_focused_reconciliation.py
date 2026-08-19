#!/usr/bin/env python3
"""Focused Chapter 22 reconciliation against an exact, archived Tusim commit."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, tarfile, tempfile, traceback
from pathlib import Path
PIN='e918c80b6fce833cd1fcae97730fa841c2176f25'
DOMAINS={
 'geometry':('ch21_sweep_probe.c',[r'DATAFLOW_LINKED_EXEC active=weight_stationary .* cycles=81920',r'active=output_stationary .* cycles=20480',r'active=row_stationary .* cycles=50176']),
 'memory_overlap':('ch16_double_buffer_probe.c',[r'PIPE_LEDGER .* seq=8 piped=7 saved=0',r'PIPE_DEPTH1_LEDGER seq=5 piped=3 saved=0',r'CH16_PROBE SUMMARY failures=0']),
 'numerics_representation':('ch13_weight_stream_probe.c',[r'SPARSITY est128 .* selected=7811',r'SPARSITY estNarrow dense_total=34307 sparse_total=77312',r'CH13_PROBE SUMMARY failures=0']),
 'operators':('ch14_compute_engines_probe.c',[]),
 'sharing_topology':('ch12_multicore_interconnect_probe.c',[r'ROUTES patternA_XY=606 patternA_YX=222 patternB_XY=222 patternB_YX=606',r'HEURISTIC_COUNTEREXAMPLE isolated=94 bottleneck=128 estimated=158',r'CH12_PROBE SUMMARY failures=0']),
 'runtime_static_policy':('test_scheduler_sweep.c',[]),
}
def run(cmd,cwd=None,timeout=180):
 p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
 if p.returncode:raise RuntimeError(f"command failed ({p.returncode}): {' '.join(map(str,cmd))}\n{p.stdout[-8000:]}")
 return p.stdout
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def capture(root):
 def q(args):return subprocess.run(args,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout
 return {'head':q(['git','rev-parse','HEAD']).strip(),'symbolic_ref':q(['git','symbolic-ref','-q','--short','HEAD']).strip(),'tracked_and_untracked_porcelain':q(['git','status','--porcelain=v1','--untracked-files=all']),'including_ignored_porcelain':q(['git','status','--porcelain=v1','--ignored','--untracked-files=all'])}
def clean_pin(s):return s['head']==PIN and not s['symbolic_ref'] and not s['tracked_and_untracked_porcelain']
def scheduler_matrix(log):
 rows=[]
 pat=re.compile(r'^\s{2}(.+?)\s{2,}(ASAP|ALAP|BALANCED)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$',re.M)
 for m in pat.finditer(log):rows.append({'topology':m.group(1).strip(),'policy':m.group(2),'cycles':int(m.group(3)),'barrier':int(m.group(4)),'hoist':int(m.group(5)),'length':int(m.group(6))})
 return rows
def execute(book,tusim,out):
 with tempfile.TemporaryDirectory(prefix='ch22-recon-') as td:
  td=Path(td);work=td/'src';work.mkdir();archive=td/'src.tar'
  with archive.open('wb') as f:
   p=subprocess.run(['git','archive','--format=tar',PIN],cwd=tusim,stdout=f)
   if p.returncode:raise RuntimeError('git archive failed')
  with tarfile.open(archive) as tf:tf.extractall(work,filter='fully_trusted')
  run(['make','-j2','libtucmodel.a'],cwd=work,timeout=300)
  logs={};checks={};probes=book/'experiments'
  for key,(srcname,patterns) in DOMAINS.items():
   src=work/'tests'/srcname if srcname=='test_scheduler_sweep.c' else probes/srcname;exe=td/key
   run(['cc','-O2','-Wall','-Wextra','-std=c11',f'-I{work}',f'-I{work/"tu_cmodel"}','-o',str(exe),str(src),str(work/'libtucmodel.a'),'-lm'])
   repeats=3 if key=='operators' else 1;chunks=[]
   for rep in range(1,repeats+1):chunks.append(f'=== repeat {rep}/{repeats} ===\n'+run(['timeout','120s',str(exe)],timeout=140))
   log=''.join(chunks);lp=out/f'{key}.log';lp.write_text(log)
   logs[key]={'source':str(src.relative_to(book) if book in src.parents else src.relative_to(work)),'source_sha256':sha(src),'log':lp.name,'log_sha256':sha(lp),'repeats':repeats}
   checks[key]=[{'contract':p,'passed':bool(re.search(p,log,re.M)),'log':lp.name} for p in patterns]
  geometry=(out/'geometry.log').read_text()
  for key,pats in {'numerics_representation':[r'ROUNDING_AXIS .* rne=0x3c01 rtz=0x3c00 .* changed_seed_diff=1',r'ROUNDING_ORDER stable_case_seed_permutation_equal=1 single_seed_permutation_diff=1'],'runtime_static_policy':[r'CONTEXT_EXEC full256=16484 live25_256=4196 control256=100 full256_bw16=32868 full256_bw64=8292']}.items():
   checks[key]+=[{'contract':p,'passed':bool(re.search(p,geometry,re.M)),'log':'geometry.log'} for p in pats]
  # Every operator repeat must independently satisfy every robust invariant.
  op=(out/'operators.log').read_text();parts=re.split(r'^=== repeat \d+/3 ===\n',op,flags=re.M)[1:]
  op_contracts=[r'ATTN diff golden_err=([0-9.]+) deviates=1 scales_equal=1',r'PIPE depth2 sequential_total=402 saved=200',r'CH14_PROBE SUMMARY failures=0']
  checks['operators']=[{'contract':'exactly three delimited repeats','passed':len(parts)==3,'log':'operators.log'}]
  errors=[]
  for i,part in enumerate(parts,1):
   for p in op_contracts:checks['operators'].append({'contract':f'repeat {i}: {p}','passed':bool(re.search(p,part,re.M)),'log':'operators.log'})
   m=re.search(op_contracts[0],part)
   if m:errors.append(float(m.group(1)))
  # Complete five-topology by three-policy matrix, all four output columns.
  sched=(out/'runtime_static_policy.log').read_text();rows=scheduler_matrix(sched)
  expected={'All-Independent':(16,0,0,4),'Serial-Chain':(10,0,0,4),'Fan-Out':(21,0,0,6),'Fan-In':(12,0,0,6),'Pipeline-Tiles':(28,0,0,13)}
  checks['runtime_static_policy'].append({'contract':'exact 5 topology x 3 policy matrix with cycles/barrier/hoist/length','passed':len(rows)==15 and {(r['topology'],r['policy']) for r in rows}=={(t,p) for t in expected for p in ('ASAP','ALAP','BALANCED')} and all((r['cycles'],r['barrier'],r['hoist'],r['length'])==expected[r['topology']] for r in rows),'log':'runtime_static_policy.log'})
  # Capacity is recomputed separately from overlap.
  gsrc=work/'docs/exploration/gbuf-sizing-sweep.md';expected_cap={64:64,128:64,256:128,512:256,1024:512,2048:1024,4096:2048,8192:4096};cap=[]
  for k,want in expected_cap.items():
   got=max(64,(k*256*2)//1024)
   if got!=want:raise RuntimeError(f'GBUF threshold mismatch K={k}')
   cap.append(f'GBUF_THRESHOLD K={k} footprint_bytes={k*256*2} min_gbuf_kb={got}')
  cp=out/'memory_capacity.log';cp.write_text('\n'.join(cap)+'\n')
  logs['memory_overlap']['auxiliary_evidence']={'source':'docs/exploration/gbuf-sizing-sweep.md','source_sha256':sha(gsrc),'log':cp.name,'log_sha256':sha(cp),'producer':'report-local K*N*2 threshold arithmetic'}
  checks['memory_overlap'].append({'contract':'all eight exact GBUF threshold rows','passed':len(cap)==8 and cap[-1]=='GBUF_THRESHOLD K=8192 footprint_bytes=4194304 min_gbuf_kb=4096','log':cp.name})
  failed=[(k,x['contract']) for k,v in checks.items() for x in v if not x['passed']]
  return {'schema':'ch22-focused-reconciliation-v3','tusim_commit':PIN,'archive_method':'git archive exact pin','domains':logs,'checks':checks,'observations':{'operator_attention_golden_errors':errors,'operator_repeat_count':len(parts),'operator_error_repeat_stable':len(set(errors))<=1,'operator_repeat_policy':'Exactly three repeats; every invariant must pass independently; magnitudes retained without averaging.','scheduler_matrix':rows,'gbuf_threshold_formula':'weight_bytes=K*256*2; min_gbuf_kb=max(64, weight_bytes/1024)','gbuf_threshold_rows':cap},'all_checks_passed':not failed,'failed_checks':failed}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--book-root',required=True);ap.add_argument('--tusim-root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--inject-failure',action='store_true');a=ap.parse_args();book=Path(a.book_root).resolve();tusim=Path(a.tusim_root).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 before=capture(tusim);(out/'source-state-before.json').write_text(json.dumps(before,indent=2,sort_keys=True)+'\n')
 result=None;error=None
 try:
  if not clean_pin(before):raise RuntimeError('Tusim pre-state is not exact-pin, detached, and clean')
  if a.inject_failure:raise RuntimeError('injected early failure after before-state capture')
  result=execute(book,tusim,out)
 except BaseException as ex:error=ex
 finally:
  after=capture(tusim);preserved=before==after and clean_pin(after);(out/'source-state-after.json').write_text(json.dumps(after,indent=2,sort_keys=True)+'\n')
  if result is not None:
   result['source_state_before_sha256']=sha(out/'source-state-before.json');result['source_state_after_sha256']=sha(out/'source-state-after.json');result['tusim_source_preserved_after']=preserved
   result['checks']['runtime_static_policy'].append({'contract':'Tusim exact state including ignored inventory preserved before/after','passed':preserved,'log':'source-state-before.json + source-state-after.json'})
   if not preserved:result['failed_checks'].append(('runtime_static_policy','source preservation'));result['all_checks_passed']=False
   (out/'reconciliation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 if error is not None:raise error
 if result is None:raise RuntimeError('reconciliation produced no result')
 print(json.dumps({'all_checks_passed':result['all_checks_passed'],'domains':len(result['domains']),'failed':result['failed_checks']},sort_keys=True))
 if not result['all_checks_passed']:raise SystemExit(1)
if __name__=='__main__':main()
