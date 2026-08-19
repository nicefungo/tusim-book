#!/usr/bin/env python3
"""Mutation controls for Chapter 23 outer seals."""
import argparse, hashlib, json, shutil, subprocess, sys, tempfile
from pathlib import Path

def run(verifier,d,opt=False):
 cmd=[sys.executable]
 if opt: cmd.append('-O')
 cmd += [str(verifier),'--run-dir',str(d)]
 return subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
def reseal_after_semantic_mutation(d):
 payload=d/'payload.sha256'; names=[line.split('  ',1)[1] for line in payload.read_text().splitlines()]
 payload.write_text(''.join(f"{hashlib.sha256((d/n).read_bytes()).hexdigest()}  {n}\n" for n in names))
 retained_names=sorted(p.name for p in d.iterdir() if p.is_file() and p.name not in ('seal.json','retained.sha256'))
 manifest=''.join(f"{hashlib.sha256((d/n).read_bytes()).hexdigest()}  {n}\n" for n in retained_names)
 (d/'retained.sha256').write_text(manifest)
 seal=json.loads((d/'seal.json').read_text()); seal['retained_manifest_sha256']=hashlib.sha256(manifest.encode()).hexdigest(); (d/'seal.json').write_text(json.dumps(seal,sort_keys=True,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--run-dir',required=True); a=ap.parse_args(); src=Path(a.run_dir); verifier=src/'verify_ch23_predraft_seal.py'
 for opt in (False,True):
  cp=run(verifier,src,opt)
  if cp.returncode or 'CH23_SEAL_VERIFY PASS' not in cp.stdout: print(cp.stdout); return 1
  print(f'SEAL_POSITIVE_CONTROL mode={"optimized" if opt else "normal"} rc=0')
 mutations={}
 def extra(d): (d/'UNMANIFESTED').write_text('x')
 mutations['extra-member']=extra
 def extra_dir(d): (d/'UNMANIFESTED_DIR').mkdir()
 mutations['extra-directory']=extra_dir
 def symlink_member(d):
  p=d/'recon.log'; p.unlink(); p.symlink_to('/etc/hosts')
 mutations['symlink-member']=symlink_member
 def seal_boundary(d):
  p=d/'seal.json'; x=json.loads(p.read_text()); x['compiler_runtime_onnx_boundary']='positive'; p.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
 mutations['seal-boundary-reversal']=seal_boundary
 def retained(d):
  p=d/'retained.sha256'; p.write_text(p.read_text()+'0'*64+'  ghost\n')
 mutations['retained-tamper']=retained
 def recon(d):
  p=d/'recon.log'; t=p.read_text(); old='COMPILER_PROMOTION_GATE compile=0 link=0 run=0 independent_oracle=0 full=0 required_full=1'; p.write_text(t.replace(old,'COMPILER_PROMOTION_GATE compile=1 link=1 run=1 independent_oracle=1 full=1 required_full=1'))
 mutations['compiler-promotion-reversal']=recon
 if (src/'independent-review.md').is_file():
  def binding(d):
   p=d/'independent-review.md'; t=p.read_text(); key='REVIEWED_MANIFEST_SHA256: '; i=t.index(key)+len(key); p.write_text(t[:i]+'0'*64+t[i+64:])
  mutations['review-binding']=binding
  def binding_collision(d):
   p=d/'independent-review.md'; p.write_text(p.read_text()+'REVIEWED_MANIFEST_SHA256: '+'0'*64+'\n'); reseal_after_semantic_mutation(d)
  mutations['review-binding-collision-fully-resealed']=binding_collision
  def missing_reconciliation(d):
   p=d/'review-reconciliation.md'; lines=[x for x in p.read_text().splitlines() if not x.startswith('| R23-FINAL-04 |')]; p.write_text('\n'.join(lines)+'\n'); reseal_after_semantic_mutation(d)
  mutations['reconciliation-row-missing-fully-resealed']=missing_reconciliation
  def geometry_promotion(d):
   p=d/'chapter-23-framing-and-evidence-plan.md'; p.write_text(p.read_text().replace('**Partial/qualified**: propagation reaches the runtime','Integrated path: propagation reaches the runtime')); reseal_after_semantic_mutation(d)
  mutations['runtime-geometry-promotion-fully-resealed']=geometry_promotion
  def generic_registry(d):
   p=d/'chapter-23-framing-and-evidence-plan.md'; old='duplicate IDs retain the first pointer and free the newly supplied duplicate; capacity overflow returns silently without freeing the submitted pointer or reporting status'; p.write_text(p.read_text().replace(old,'replacement/lifetime hazards')); reseal_after_semantic_mutation(d)
  mutations['registry-contract-generic-fully-resealed']=generic_registry
  def ledger_geometry_promotion(d):
   p=d/'chapter-23-source-claim-ledger.md'; p.write_text(p.read_text().replace('| qualified |','| allow |',1)); reseal_after_semantic_mutation(d)
  mutations['ledger-runtime-geometry-promotion-fully-resealed']=ledger_geometry_promotion
  def ledger_generic_registry(d):
   p=d/'chapter-23-source-claim-ledger.md'; old='duplicate registration retains the first stable pointer and frees the newly created instance; capacity overflow returns silently without freeing the submitted pointer or reporting status'; p.write_text(p.read_text().replace(old,'replacement/lifetime hazards')); reseal_after_semantic_mutation(d)
  mutations['ledger-registry-contract-generic-fully-resealed']=ledger_generic_registry
 with tempfile.TemporaryDirectory(prefix='ch23-seal-controls-') as td:
  root=Path(td)
  for name,mutate in mutations.items():
   d=root/name; shutil.copytree(src,d); mutate(d)
   for opt in (False,True):
    cp=run(d/'verify_ch23_predraft_seal.py',d,opt)
    if cp.returncode==0: print(f'SEAL_MUTATION_CONTROL FAIL mutation={name} mode={"optimized" if opt else "normal"}'); return 1
   print(f'SEAL_MUTATION_CONTROL PASS mutation={name} normal_rejected=1 optimized_rejected=1')
 print(f'CH23_SEAL_CONTROLS PASS positive=2 mutations={len(mutations)}')
 return 0
if __name__=='__main__': raise SystemExit(main())
