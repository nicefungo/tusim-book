#!/usr/bin/env python3
"""Verify outer closure and rerun semantic validation for a Chapter 23 predraft seal."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
PIN='e918c80b6fce833cd1fcae97730fa841c2176f25'
BASE={
 'chapter-23-framing-and-evidence-plan.md','chapter-23-source-claim-ledger.md',
 'ch23_extension_recon.py','validate_ch23_predraft.py','test_ch23_evidence_controls.py',
 'run_ch23_predraft_seal.sh','verify_ch23_predraft_seal.py','test_ch23_seal_controls.py',
 'recon.log','controls.log','payload.sha256','validation.log','retained.sha256','seal.json'
}
POST={'independent-review.md','review-reconciliation.md','reviewed-provisional-seal.json','reviewed-provisional-retained.sha256','reviewed-provisional-run.txt'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fail(msg): print('CH23_SEAL_VERIFY FAIL '+msg); return 1
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--run-dir',required=True); a=ap.parse_args(); d=Path(a.run_dir)
 try: seal=json.loads((d/'seal.json').read_text())
 except Exception as e: return fail(f'seal unreadable {e}')
 mode=seal.get('mode'); expected=BASE | (POST if mode=='postreview' else set())
 if mode not in ('provisional','postreview'): return fail('bad mode')
 actual={p.name for p in d.iterdir()}
 if actual!=expected: return fail(f'member set mismatch missing={sorted(expected-actual)} extra={sorted(actual-expected)}')
 for name in expected:
  p=d/name
  if not p.is_file() or p.is_symlink(): return fail(f'member is not regular non-symlink file {name}')
 if seal!={
  'schema':'tusim-book/ch23-predraft-seal/v1','mode':mode,'source_pin':PIN,
  'decision':'extension-contract-card/weakest-missing-edge',
  'compiler_runtime_onnx_boundary':'negative','validation':'PASS',
  'retained_manifest_sha256':seal.get('retained_manifest_sha256')}: return fail('seal fields mismatch')
 manifest=(d/'retained.sha256').read_text()
 if sha(d/'retained.sha256')!=seal['retained_manifest_sha256']: return fail('seal-to-retained digest mismatch')
 listed={}
 for line in manifest.splitlines():
  digest,name=line.split('  ',1)
  if name in listed: return fail(f'duplicate retained member {name}')
  listed[name]=digest
 expected_listed=expected-{'seal.json','retained.sha256'}
 if set(listed)!=expected_listed: return fail(f'retained names mismatch missing={sorted(expected_listed-set(listed))} extra={sorted(set(listed)-expected_listed)}')
 for name,digest in listed.items():
  if sha(d/name)!=digest: return fail(f'retained hash mismatch {name}')
 cp=subprocess.run([sys.executable,str(d/'validate_ch23_predraft.py'),'--run-dir',str(d),'--mode',mode],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if cp.returncode or 'CH23_PREDRAFT_VALIDATION PASS' not in cp.stdout: return fail('semantic revalidation failed: '+cp.stdout.strip())
 print(f'CH23_SEAL_VERIFY PASS mode={mode} members={len(expected)} boundary=negative')
 return 0
if __name__=='__main__': raise SystemExit(main())
