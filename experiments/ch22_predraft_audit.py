#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
PIN='e918c80b6fce833cd1fcae97730fa841c2176f25';BASE='88cba9bf9a26b2ae2c3079e6c57446803ab76df0'
FREEZE=[
 'experiments/ch22_predraft_audit.py','experiments/run_ch22_predraft_evidence_audit.sh','experiments/ch22_focused_reconciliation.py','experiments/ch22_build_claim_register.py','experiments/ch22_build_predraft_registers.py','experiments/ch22_predraft_validate.py',
 'experiments/ch21_sweep_probe.c','experiments/ch16_double_buffer_probe.c','experiments/ch13_weight_stream_probe.c','experiments/ch14_compute_engines_probe.c','experiments/ch12_multicore_interconnect_probe.c',
 'notes/chapter-22-report-inventory.json','notes/chapter-22-claim-register.json','notes/chapter-22-reviewed-claim-manifest-geometry-memory.md','notes/chapter-22-reviewed-claim-manifest-numerics-operators.md','notes/chapter-22-reviewed-claim-manifest-sharing-policy.md','notes/chapter-22-skeptical-review-dispositions.md','notes/chapter-22-framing-and-evidence-plan.md','notes/chapter-22-framing-review-dispositions.md',
 'references/ch22-predraft-method-primary-sources.md','references/ch21-sweep-method-primary-sources.md']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(cmd,cwd=None,ok=(0,),timeout=600):
 p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
 if p.returncode not in ok:raise RuntimeError(f"command failed {p.returncode}: {' '.join(map(str,cmd))}\n{p.stdout[-12000:]}")
 return p
def git(root,*args,ok=(0,)):return run(['git','-C',str(root),*args],ok=ok).stdout.strip()
def require_source(tusim):
 if git(tusim,'rev-parse','HEAD')!=PIN or git(tusim,'symbolic-ref','-q','--short','HEAD',ok=(0,1)) or git(tusim,'status','--porcelain=v1','--untracked-files=all'):raise RuntimeError('Tusim must be exact-pin, detached, clean')
def require_book(book,clean=True):
 if git(book,'branch','--show-current')!='main':raise RuntimeError('book must be on main')
 run(['git','-C',str(book),'merge-base','--is-ancestor',BASE,'HEAD'])
 if clean and git(book,'status','--porcelain=v1','--untracked-files=all'):raise RuntimeError('book must be clean')
def py(script,args,cwd,opt=False,ok=(0,)):
 return run([sys.executable]+(['-O'] if opt else [])+[str(script)]+list(map(str,args)),cwd=cwd,ok=ok)
def members(root):return sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() or p.is_symlink())
def reject_paths(root,paths):
 for rel in paths:
  p=root/rel
  if p.is_symlink() or '..' in Path(rel).parts or Path(rel).is_absolute() or not p.is_file():raise RuntimeError(f'unsafe member {rel}')
def write_inner(rd):
 payload=members(rd)
 if 'inner-manifest.json' in payload or 'SHA256SUMS' in payload:raise RuntimeError('premature seal files')
 inner={'schema':'ch22-postreview-inner-manifest-v1','payload_members':payload,'payload_sha256':{x:sha(rd/x) for x in payload}}
 (rd/'inner-manifest.json').write_text(json.dumps(inner,indent=2,sort_keys=True)+'\n')
 allm=payload+['inner-manifest.json'];(rd/'SHA256SUMS').write_text(''.join(f"{sha(rd/x)}  {x}\n" for x in allm))
def check_inner(rd):
 inner=json.loads((rd/'inner-manifest.json').read_text());expected=sorted(inner['payload_members']+['inner-manifest.json','SHA256SUMS']);got=members(rd)
 if got!=expected:raise RuntimeError(f'exact member mismatch: extra={sorted(set(got)-set(expected))} missing={sorted(set(expected)-set(got))}')
 reject_paths(rd,got)
 for rel,h in inner['payload_sha256'].items():
  if sha(rd/rel)!=h:raise RuntimeError(f'payload hash mismatch {rel}')
 sums={}
 for line in (rd/'SHA256SUMS').read_text().splitlines():
  h,rel=line.split('  ',1);sums[rel]=h
 if set(sums)!=set(inner['payload_members'])|{'inner-manifest.json'}:raise RuntimeError('checksum member mismatch')
 for rel,h in sums.items():
  if sha(rd/rel)!=h:raise RuntimeError(f'checksum mismatch {rel}')
 return inner
def validator_args(book,tusim,claims,derived,recon,mut):return ['--claims',claims,'--derived',derived,'--recon',recon,'--source',tusim/'docs/exploration','--inventory',book/'notes/chapter-22-report-inventory.json','--book-root',book,'--mutation-out',mut]
def execute(book,tusim,runid):
 require_book(book);require_source(tusim);commit=git(book,'rev-parse','HEAD');rd=book/'experiments/runs/ch22-predraft'/runid
 if rd.exists():raise RuntimeError('run already exists')
 rd.mkdir(parents=True);inp=rd/'inputs';inp.mkdir()
 frozen=[]
 for rel in FREEZE:
  data=run(['git','-C',str(book),'show',f'{commit}:{rel}']).stdout.encode();dst=inp/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data);frozen.append({'path':rel,'sha256':hashlib.sha256(data).hexdigest()})
 claims=book/'notes/chapter-22-claim-register.json';gen=rd/'generated-claim-register.json'
 py(book/'experiments/ch22_build_claim_register.py',['--source',tusim/'docs/exploration','--inventory',book/'notes/chapter-22-report-inventory.json','--manifest-dir',book/'notes','--out',gen],book)
 if claims.read_bytes()!=gen.read_bytes():raise RuntimeError('canonical claim register not reproducible')
 py(book/'experiments/ch22_focused_reconciliation.py',['--book-root',book,'--tusim-root',tusim,'--out',rd],book)
 der=rd/'candidate-predraft-registers.json';runrel=str(rd.relative_to(book)/'reconciliation.json')
 py(book/'experiments/ch22_build_predraft_registers.py',['--claims',claims,'--recon',rd/'reconciliation.json','--recon-relative',runrel,'--book-root',book,'--out',der],book)
 mut=rd/'mutation-results.json';muto=rd/'mutation-results-opt.json';args=validator_args(book,tusim,claims,der,rd/'reconciliation.json',mut);py(book/'experiments/ch22_predraft_validate.py',args,book);argso=validator_args(book,tusim,claims,der,rd/'reconciliation.json',muto);py(book/'experiments/ch22_predraft_validate.py',argso,book,opt=True)
 if mut.read_bytes()!=muto.read_bytes():raise RuntimeError('normal/optimized validator mismatch')
 with tempfile.TemporaryDirectory(prefix='ch22-controls-') as td:
  td=Path(td);fail=td/'failure';p=py(book/'experiments/ch22_focused_reconciliation.py',['--book-root',book,'--tusim-root',tusim,'--out',fail,'--inject-failure'],book,ok=(1,))
  failure_ok=(fail/'source-state-before.json').is_file() and (fail/'source-state-after.json').is_file() and (fail/'source-state-before.json').read_bytes()==(fail/'source-state-after.json').read_bytes()
  (rd/'failure-path-control.json').write_text(json.dumps({'expected_nonzero':p.returncode,'before_after_identical':failure_ok,'passed':p.returncode!=0 and failure_ok},indent=2,sort_keys=True)+'\n')
  src=(book/'experiments/ch22_predraft_validate.py').read_text();mutated=td/'validator-with-real-assert.py';mutated.write_text(src+"\ndef _real_assertion_mutation_control():\n    assert(False)\n")
  an=py(mutated,args[:-1]+[td/'assert-normal.json'],book,ok=(1,));ao=py(mutated,argso[:-1]+[td/'assert-opt.json'],book,opt=True,ok=(1,));diag='validator-contains-assert'
  (rd/'assertion-control.json').write_text(json.dumps({'normal_returncode':an.returncode,'optimized_returncode':ao.returncode,'normal_ast_diagnostic':diag in an.stdout,'optimized_ast_diagnostic':diag in ao.stdout,'passed':an.returncode!=0 and ao.returncode!=0 and diag in an.stdout and diag in ao.stdout},indent=2,sort_keys=True)+'\n')
 manifest={'schema':'ch22-postreview-run-v1','run_id':runid,'input_book_commit':commit,'book_branch':'main','required_baseline':BASE,'tusim_commit':PIN,'tusim_detached_clean_required':True,'frozen_inputs':frozen,'claim_register_sha256':sha(claims),'generated_claim_register_sha256':sha(gen),'candidate_register_sha256':sha(der),'reconciliation_sha256':sha(rd/'reconciliation.json'),'mutation_sha256':sha(mut),'review_dispositions_sha256':sha(book/'notes/chapter-22-skeptical-review-dispositions.md'),'prose_authorized_at_execute':False}
 (rd/'run-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');write_inner(rd);print(json.dumps({'execute':'PASS','run':str(rd.relative_to(book)),'input_commit':commit},sort_keys=True))
def verify(book,tusim,runid):
 require_book(book,clean=False);require_source(tusim);rd=book/'experiments/runs/ch22-predraft'/runid;inner=check_inner(rd);man=json.loads((rd/'run-manifest.json').read_text());commit=man['input_book_commit']
 for x in man['frozen_inputs']:
  data=run(['git','-C',str(book),'show',f"{commit}:{x['path']}"]).stdout.encode()
  if hashlib.sha256(data).hexdigest()!=x['sha256'] or (rd/'inputs'/x['path']).read_bytes()!=data:raise RuntimeError(f"frozen input mismatch {x['path']}")
 claims=book/'notes/chapter-22-claim-register.json';derived=book/'notes/chapter-22-predraft-registers.json'
 if claims.read_bytes()!=(rd/'generated-claim-register.json').read_bytes() or derived.read_bytes()!=(rd/'candidate-predraft-registers.json').read_bytes():raise RuntimeError('canonical register mismatch')
 with tempfile.TemporaryDirectory(prefix='ch22-verify-') as td:
  td=Path(td);m=td/'mut.json';mo=td/'mut-opt.json';args=validator_args(book,tusim,claims,derived,rd/'reconciliation.json',m);py(book/'experiments/ch22_predraft_validate.py',args,book);py(book/'experiments/ch22_predraft_validate.py',validator_args(book,tusim,claims,derived,rd/'reconciliation.json',mo),book,opt=True)
  if m.read_bytes()!=mo.read_bytes() or m.read_bytes()!=(rd/'mutation-results.json').read_bytes():raise RuntimeError('validator reproduction mismatch')
 outer=book/'notes/chapter-22-postreview-seal.json';outer_matches=False
 if outer.is_file():
  o=json.loads(outer.read_text())
  if o.get('run_id')==runid:
   outer_matches=True;bc=o['bundle_commit'];tree=git(book,'rev-parse',f"{bc}:experiments/runs/ch22-predraft/{runid}")
   if tree!=o['bundle_tree'] or o['inner_manifest_sha256']!=sha(rd/'inner-manifest.json') or o['sha256sums_sha256']!=sha(rd/'SHA256SUMS') or o.get('status')!='green' or o.get('prose_authorized') is not True:raise RuntimeError('outer seal mismatch')
 print(json.dumps({'verify':'PASS','run':str(rd.relative_to(book)),'payload_members':len(inner['payload_members']),'outer_seal':outer_matches},sort_keys=True))
def seal(book,tusim,runid,bundle_commit):
 require_book(book);require_source(tusim);rel=f'experiments/runs/ch22-predraft/{runid}';rd=book/rel;check_inner(rd)
 run(['git','-C',str(book),'cat-file','-e',f'{bundle_commit}^{{commit}}']);tree=git(book,'rev-parse',f'{bundle_commit}:{rel}')
 if tree!=git(book,'rev-parse',f'HEAD:{rel}'):raise RuntimeError('current bundle differs from immutable bundle commit')
 inner_bytes=run(['git','-C',str(book),'show',f'{bundle_commit}:{rel}/inner-manifest.json']).stdout.encode();sum_bytes=run(['git','-C',str(book),'show',f'{bundle_commit}:{rel}/SHA256SUMS']).stdout.encode();man=json.loads(run(['git','-C',str(book),'show',f'{bundle_commit}:{rel}/run-manifest.json']).stdout)
 out={'schema':'ch22-postreview-outer-seal-v1','run_id':runid,'bundle_commit':bundle_commit,'bundle_tree':tree,'input_book_commit':man['input_book_commit'],'tusim_commit':PIN,'inner_manifest_sha256':hashlib.sha256(inner_bytes).hexdigest(),'sha256sums_sha256':hashlib.sha256(sum_bytes).hexdigest(),'claim_register_sha256':sha(book/'notes/chapter-22-claim-register.json'),'predraft_registers_sha256':sha(book/'notes/chapter-22-predraft-registers.json'),'review_dispositions_sha256':sha(book/'notes/chapter-22-skeptical-review-dispositions.md'),'status':'green','prose_authorized':True,'authorization_scope':'Chapter 22 manuscript drafting under the closed constraint-first framing; evidence changes require a new seal.'}
 (book/'notes/chapter-22-postreview-seal.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'seal':'CREATED','bundle_commit':bundle_commit,'bundle_tree':tree},sort_keys=True))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['execute','verify','seal']);ap.add_argument('run_id');ap.add_argument('bundle_commit',nargs='?');ap.add_argument('--book-root',default=str(Path(__file__).resolve().parent.parent));ap.add_argument('--tusim-root',default='/home/zxy/Workplace/projects/tusim');a=ap.parse_args();book=Path(a.book_root).resolve();tusim=Path(a.tusim_root).resolve()
 if a.mode=='execute':execute(book,tusim,a.run_id)
 elif a.mode=='verify':verify(book,tusim,a.run_id)
 else:
  if not a.bundle_commit:raise SystemExit('seal requires bundle commit')
  seal(book,tusim,a.run_id,a.bundle_commit)
if __name__=='__main__':main()
