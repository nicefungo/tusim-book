#!/usr/bin/env python3
"""Semantic/payload validator for retained Chapter 23 predraft evidence."""
import argparse, ast, hashlib, json, re, sys
from pathlib import Path
PIN='e918c80b6fce833cd1fcae97730fa841c2176f25'
REQUIRED_IDS=('R23-FINAL-01','R23-FINAL-02','R23-FINAL-03','R23-FINAL-04')
BASE_PRE={
 'chapter-23-framing-and-evidence-plan.md','chapter-23-source-claim-ledger.md',
 'ch23_extension_recon.py','validate_ch23_predraft.py','test_ch23_evidence_controls.py',
 'run_ch23_predraft_seal.sh','verify_ch23_predraft_seal.py','test_ch23_seal_controls.py',
 'recon.log','controls.log'
}
POST={'independent-review.md','review-reconciliation.md','reviewed-provisional-seal.json','reviewed-provisional-retained.sha256','reviewed-provisional-run.txt'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--run-dir',required=True); ap.add_argument('--mode',choices=['provisional','postreview'],required=True); a=ap.parse_args(); d=Path(a.run_dir); errors=[]
 expected=BASE_PRE | (POST if a.mode=='postreview' else set())
 for n in expected|{'payload.sha256'}:
  if not (d/n).is_file(): errors.append(f'missing {n}')
 if errors: print('\n'.join(errors)); return 1
 listed={}
 try:
  for line in (d/'payload.sha256').read_text().splitlines():
   digest,name=line.split('  ',1)
   if name in listed: errors.append(f'duplicate payload member {name}')
   listed[name]=digest
 except Exception as e: errors.append(f'payload parse {e}')
 if set(listed)!=expected: errors.append(f'payload member set mismatch missing={sorted(expected-set(listed))} extra={sorted(set(listed)-expected)}')
 for n in expected:
  if listed.get(n)!=sha(d/n): errors.append(f'payload hash mismatch {n}')
 for n in ['ch23_extension_recon.py','validate_ch23_predraft.py','test_ch23_evidence_controls.py','verify_ch23_predraft_seal.py','test_ch23_seal_controls.py']:
  if any(isinstance(node,ast.Assert) for node in ast.walk(ast.parse((d/n).read_text()))): errors.append(f'ast.Assert present {n}')
 log=(d/'recon.log').read_text(); lines=log.splitlines()
 markers=[
  'HASH_SET PASS files=34','PATH_CONFIG geometry=complete_to_runtime dataflow=parsed_then_dropped',
  'PATH_PLUGIN declared_ids=4 linked_registered_consumed=3',
  'ownership=global_registry_core_pointer duplicate_policy=keep_first_free_new capacity_overflow=silent_return_without_free',
  'production_call_files=2 production_call_sites=3 production_callers=tu_cmodel.c,attention_engine.c',
  'unregistered_fallback=weight_stationary success_status=1',
  'PATH_OPCODE declared_explicit=59 queue_dispatch=8','adjacent_analysis_consumers=scheduler,liveness composed_execution=0',
  'PATH_MODULE cycle_model_source=1 library_member=0 make_rule=0 focused_source=1 production_reachability=0 exhaustive_external_non_test_call_files=0',
  'PATH_SWEEP source=1 make_target=1 aggregate_owner=0','effective_core_routes=WS,WS,WS labeled_routes=WS,OS,RS',
  'PATH_BINDING python_source=1 config_path_stored_not_consumed=1',
  'COMPILER_TRIGGER contained_models=2 generator=1 generated_link_status_suppressed=1 far_boundary_oracle=0 nontrivial_link_run_verify=0 boundary=negative',
  'COMPILER_PROMOTION_GATE compile=0 link=0 run=0 independent_oracle=0 full=0 required_full=1',
  'COMPILER_SMOKE status=environment_blocked rc=1 generated=0',
  'FOCUSED test-config rc=2 classification=red stack_smashing=1 reproducibility=layout_sensitive_root_cause_open',
  'FOCUSED test-dataflow rc=0 classification=green','FOCUSED test-isa rc=0 classification=green','FOCUSED test-cmdq rc=0 classification=green',
  'FOCUSED test-dataflow-sweep rc=0 classification=green_status_but_fail_open_oracle',
  'FOCUSED python-binding rc=0 identity_gemm=PASS config_path_exercised=0 reports_exercised=0','compiler_boundary=negative']
 for m in markers:
  if m not in log: errors.append(f'missing marker: {m}')
 exact={
  'COMPILER_TRIGGER ':'COMPILER_TRIGGER contained_models=2 generator=1 generated_link_status_suppressed=1 far_boundary_oracle=0 nontrivial_link_run_verify=0 boundary=negative',
  'COMPILER_PROMOTION_GATE ':'COMPILER_PROMOTION_GATE compile=0 link=0 run=0 independent_oracle=0 full=0 required_full=1',
  'COMPILER_SMOKE ':'COMPILER_SMOKE status=environment_blocked rc=1 generated=0',
  'CH23_EXTENSION_RECON ':'CH23_EXTENSION_RECON PASS hashes=34 path_families=7 focused_green=5 focused_red=1 compiler_boundary=negative'}
 for prefix,want in exact.items():
  found=[x for x in lines if x.startswith(prefix)]
  if found!=[want]: errors.append(f'non-unique or contradictory line {prefix.strip()}: {found}')
 if any('CH23_EXTENSION_RECON FAIL' in x for x in lines): errors.append('failure line present')
 if 'SOURCE_STATE before pin=' not in log or 'SOURCE_STATE after pin=' not in log: errors.append('missing source bookends')
 controls=(d/'controls.log').read_text()
 for m in ['AST_ASSERT_CONTROL PASS count=0','POSITIVE_CONTROL mode=normal rc=0 marker=1','POSITIVE_CONTROL mode=optimized rc=0 marker=1','SOURCE_MUTATION_CONTROL mode=normal rejected=1','SOURCE_MUTATION_CONTROL mode=optimized rejected=1','CH23_EVIDENCE_CONTROLS PASS positive=2 mutation=2 ast_assert=0']:
  if m not in controls: errors.append(f'missing control marker {m}')
 plan=(d/'chapter-23-framing-and-evidence-plan.md').read_text(); ledger=(d/'chapter-23-source-claim-ledger.md').read_text()
 for text,label in [(plan,'plan'),(ledger,'ledger')]:
  if PIN not in text: errors.append(f'{label} lacks exact pin')
  if 'compiler/runtime/ONNX' not in text: errors.append(f'{label} lacks negative boundary')
 if '| 1 | **Extension contracts:' not in plan or 'What contract am I promising' not in plan: errors.append('ranked decision absent')
 if '| Runtime geometry |' not in plan or '**Partial/qualified**: propagation reaches the runtime' not in plan or 'Integrated path' in plan: errors.append('runtime geometry must remain partial/qualified')
 registry_contract='duplicate IDs retain the first pointer and free the newly supplied duplicate; capacity overflow returns silently without freeing the submitted pointer or reporting status'
 if registry_contract not in plan or 'replacement/lifetime hazards' in plan: errors.append('registry ownership wording changed or became generic')
 geometry_ledger='| C23-02 | Core geometry has a live config-to-runtime conversion path. | `tu_cmodel/infra/config.h`; `tu_cmodel/infra/config.c` `tu_config_to_runtime()`; `tu_cmodel/tu_cmodel.c` initialization. | Canonical disposable `make test-config` aborts with stack smashing, while independent layouts have passed; root cause is unresolved and layout-sensitive. | qualified |'
 if geometry_ledger not in ledger: errors.append('ledger runtime geometry must remain qualified with exact counterevidence')
 registry_ledger='duplicate registration retains the first stable pointer and frees the newly created instance; capacity overflow returns silently without freeing the submitted pointer or reporting status'
 if registry_ledger not in ledger or 'replacement/lifetime hazards' in ledger: errors.append('ledger registry ownership wording changed or became generic')
 if len(re.findall(r'\| C23-\d+ \|',ledger))<16: errors.append('ledger too short')
 if a.mode=='postreview':
  try:
   rseal=json.loads((d/'reviewed-provisional-seal.json').read_text()); rmanifest=d/'reviewed-provisional-retained.sha256'; run=(d/'reviewed-provisional-run.txt').read_text().strip()
   if rseal.get('mode')!='provisional' or rseal.get('source_pin')!=PIN or rseal.get('validation')!='PASS' or rseal.get('compiler_runtime_onnx_boundary')!='negative': errors.append('reviewed provisional seal fields invalid')
   if sha(rmanifest)!=rseal.get('retained_manifest_sha256'): errors.append('reviewed provisional manifest digest mismatch')
   review=(d/'independent-review.md').read_text(); review_lines=review.splitlines()
   decisions=[x for x in review_lines if x.startswith('REVIEW DECISION:')]
   if len(decisions)!=1 or decisions[0] not in ('REVIEW DECISION: ACCEPT','REVIEW DECISION: ACCEPT WITH REQUIRED RECONCILIATION'): errors.append('review decision must be one exact accepting line')
   exact_bind={'REVIEWED_PROVISIONAL_RUN':run,'REVIEWED_MANIFEST_SHA256':rseal['retained_manifest_sha256'],'REVIEWED_SOURCE_PIN':PIN}
   for key,val in exact_bind.items():
    lines=[x for x in review_lines if x.startswith(key+':')]
    if lines != [f'{key}: {val}']: errors.append(f'review binding must be one exact line {key}')
   unexpected=[x for x in review_lines if x.startswith('REVIEWED_') and x.split(':',1)[0] not in exact_bind]
   if unexpected: errors.append('unexpected REVIEWED_ binding lines')
   review_ids=[x.split(':',1)[1].strip() for x in review_lines if x.startswith('REQUIRED_RECONCILIATION_ID:')]
   if sorted(review_ids)!=sorted(REQUIRED_IDS) or len(review_ids)!=len(set(review_ids)): errors.append('review required-ID set mismatch or duplicate')
  except Exception as e: errors.append(f'postreview binding parse {e}')
  rec_lines=(d/'review-reconciliation.md').read_text().splitlines(); statuses=[x for x in rec_lines if x.startswith('RECONCILIATION STATUS:')]
  if statuses != ['RECONCILIATION STATUS: COMPLETE']: errors.append('reconciliation requires one exact COMPLETE line')
  row_ids=[]
  for line in rec_lines:
   m=re.match(r'^\| (R23-FINAL-\d{2}) \| ([^|]+) \|',line)
   if m:
    row_ids.append(m.group(1))
    if m.group(2).strip()!='resolved': errors.append(f'unresolved reconciliation {m.group(1)}')
  if sorted(row_ids)!=sorted(REQUIRED_IDS) or len(row_ids)!=len(set(row_ids)): errors.append('reconciliation required-ID rows missing, duplicate, or unexpected')
 print(f"CH23_PREDRAFT_VALIDATION {'PASS' if not errors else 'FAIL'} mode={a.mode} checks={18 + (8 if a.mode=='postreview' else 0)}")
 for e in errors: print('ERROR '+e)
 return 1 if errors else 0
if __name__=='__main__': raise SystemExit(main())
