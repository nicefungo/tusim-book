#!/usr/bin/env python3
import ast,hashlib,os,re,subprocess,sys
from pathlib import Path
from typing import NoReturn
PIN='e918c80b6fce833cd1fcae97730fa841c2176f25'
RUN_ID=os.environ.get('CH18_RUN_ID','20260805-ch18-canonical-v5')
root=Path(__file__).resolve().parents[1]
run=root/'experiments/runs/ch18-context'/RUN_ID

def fail(msg) -> NoReturn: print('CH18_PREDRAFT_VALIDATION FAIL: '+msg); raise SystemExit(1)
def need(cond,msg):
 if not cond: fail(msg)
def text(p):
 if not p.is_file(): fail('missing '+str(p.relative_to(root) if p.is_relative_to(root) else p))
 return p.read_text(errors='replace')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(p):
 out={}
 for line in text(p).splitlines():
  m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line)
  if not m: fail('malformed manifest line in '+p.name)
  if m.group(2) in out: fail('duplicate manifest entry '+m.group(2))
  out[m.group(2)]=m.group(1)
 return out
# Optimization safety: reject every assert statement in this validator's own AST.
source=Path(__file__).read_text(); tree=ast.parse(source)
if any(isinstance(n,ast.Assert) for n in ast.walk(tree)): fail('optimizer-removable assertion in validator')
need(run.is_dir(),'missing run directory '+str(run))
inputs=['edition.yaml','PLAN.md','style-guide.md','fidelity-matrix.md','source-audit.md',
 'notes/chapter-18-framing-and-evidence-plan.md','notes/chapter-18-framing-review-dispositions.md',
 'experiments/ch18_framing_reproduce.sh','notes/chapter-18-framing-reproduction.log',
 'notes/chapter-18-source-and-claim-ledger.md','notes/chapter-18-predraft-source-audit-report.md',
 'notes/chapter-18-skeptical-review-dispositions.md','experiments/ch18_source_audit.py',
 'experiments/ch18_context_probe.c','experiments/ch18_predraft_validate.py',
 'experiments/run_ch18_context_audit.sh']
# Input set, hash file, retained copies, and commit binding.
ih=manifest(run/'input-hashes.txt')
need(set(ih)==set(inputs),'input-hashes set mismatch')
for rel in inputs:
 q=run/'inputs'/rel
 need(q.is_file(),'missing retained input '+rel)
 need(sha(q)==ih[rel],'retained input hash mismatch '+rel)
commit=text(run/'input_commit').strip(); need(re.fullmatch(r'[0-9a-f]{40}',commit) is not None,'bad input commit')
for rel in inputs:
 try: blob=subprocess.check_output(['git','-C',str(root),'show',commit+':'+rel])
 except subprocess.CalledProcessError: fail('input absent from input commit '+rel)
 need(blob==(run/'inputs'/rel).read_bytes(),'input commit drift '+rel)
need(text(run/'source_pin').strip()==PIN,'source pin mismatch')
# Exact retained manifest set and all digests.
ret=manifest(run/'sha256-retained.txt')
base={'input-hashes.txt','input_commit','source_pin','tusim-ignored-before.sha256','tusim-ignored-after.sha256',
 'source-audit.log','source-audit-pin-mutation.log','source-audit-mutation.log','source-audit-restored.log',
 'build.log','archive-members.log','test-context-readelf.log','test-context-mut-readelf.log',
 'test-context-sweep-readelf.log','ch18-probe-readelf.log','ch18-probe-o2-readelf.log','ch18-probe-san-readelf.log',
 'test-context.log','test-context-mutation.log','test-context-sweep.log','probe.log','probe-o2.log','probe-san.log','probe.stderr.log','probe-o2.stderr.log','sanitizer.log',
 'validator-mutation-normal.log','validator-mutation-optimized.log','transcript.log'}
expected=base|{'inputs/'+x for x in inputs}
need(set(ret)==expected,'retained manifest set mismatch')
for rel,digest in ret.items():
 p=run/rel; need(p.is_file(),'missing retained '+rel); need(sha(p)==digest,'retained hash mismatch '+rel)
need(text(run/'tusim-ignored-before.sha256')==text(run/'tusim-ignored-after.sha256'),'Tusim ignored inventory changed')
# Source gate and fail-closed controls.
sa=text(run/'source-audit.log')
need(f'CH18_SOURCE_AUDIT PASS pin={PIN} hashes=39 predicates=171 checks=210' in sa,'source audit authority line')
need('CH18_PUBLIC_APIS count=19 ' in sa and 'CH18_CALLERS external_nontest=none' in sa,'API/caller census')
need(f'CH18_SOURCE_AUDIT FAIL pin expected={PIN} got=' in text(run/'source-audit-pin-mutation.log'),'pin mutation did not fail closed')
need('hash mismatch tu_cmodel/infra/tu_context.c' in text(run/'source-audit-mutation.log'),'source mutation did not fail closed')
need('CH18_SOURCE_AUDIT PASS' in text(run/'source-audit-restored.log'),'source audit did not recover')
# Build, focused tests, mutation, and sweep.
need(re.search(r'(?m)^tu_context\.o$',text(run/'archive-members.log')) is not None,'context object absent from archive')
for rel in ['test-context-readelf.log','test-context-mut-readelf.log','test-context-sweep-readelf.log','ch18-probe-readelf.log','ch18-probe-o2-readelf.log','ch18-probe-san-readelf.log']:
 need('libtucmodel' not in text(run/rel),'dynamic libcmodel dependency '+rel)
need('15/15 tests passed' in text(run/'test-context.log'),'focused context suite')
mut=text(run/'test-context-mutation.log'); need('14/15 tests passed' in mut and 'FAIL' in mut,'focused mutation sensitivity')
sweep=text(run/'test-context-sweep.log')
for row in ['128 full      131072          8292','128 live25     32768          2148','128 control        0           100','256 full      262144         16484','256 live25     65536          4196','256 control        0           100','512 full      524288         32868','512 live25    131072          8292','512 control        0           100','16         32868','32         16484','64          8292']:
 need(row in sweep,'missing sweep row '+row)
# Probe transition/field rows, optimization stability, and sanitizer closure.
probe=text(run/'probe.log'); need(probe==text(run/'probe-o2.log')==text(run/'probe-san.log'),'probe O0/O2/sanitizer output mismatch')
san=text(run/'sanitizer.log'); need(re.search(r'ERROR: AddressSanitizer|SUMMARY: AddressSanitizer|runtime error:',san) is None,'sanitizer diagnostics')
need('CHECK_FAIL' not in probe and 'CH18_PROBE SUMMARY failures=0' in probe,'probe summary')
required=['null_api','create_invalid','alloc_first','alloc_exhaustion','allocation_clone','free_active','free_ready','free_blocked','free_completed','free_idle','reuse_after_active_free','save_active','restore_direct','switch_already_active','switch_self','switch_invalid','switch_idle','switch_blocked','request_switch','schedule_rr','schedule_priority_tie','schedule_priority_repeat','priority_zero','slice_thresholds','notify_wrap','block_current','unblock_states','unblock_all_states','notify_without_active','malloc_fail_w','malloc_fail_a','malloc_fail_o','malloc_fail_resave','live_scope','control_scope','zero_bandwidth','core_state_retained','cycle_underflow','queue_not_retained','dma_domains','rounding_prng_global','plugin_global','bank_split','dead_controls','getters_status']
for label in required: need(('ROW '+label+' ') in probe,'missing probe row '+label)
for label,phase in re.findall(r'(?m)^ROW (\S+) (PRE|POST) ',probe):
 for tag in ['runtime','W','A','O','queue','c0_identity']:
  need(f'SURFACE {label} {phase} {tag}' in probe,'missing complete surface '+label+'/'+phase+'/'+tag)
need(re.search(r'ROW free_idle POST rc=0 mgr=0/0/1/4',probe) is not None,'IDLE free discriminator')
need(re.search(r'ROW reuse_after_active_free POST rc=0 mgr=2/0/0/4',probe) is not None,'ownerless reuse discriminator')
need(re.search(r'ROW restore_direct POST rc=0 mgr=2/1/2/4',probe) is not None,'double ACTIVE discriminator')
need(re.search(r'ROW switch_already_active POST rc=-1 mgr=2/1/1/4',probe) is not None,'already-ACTIVE target discriminator')
for label in ['switch_invalid','switch_idle','switch_blocked']:
 need(re.search(r'ROW '+label+r' POST rc=-1 mgr=2/0/0/4 .*pending=192',probe) is not None,'failed switch discriminator '+label)
need(re.search(r'ROW live_scope POST .*switches=2/20 .*W=11/22',probe) is not None,'LIVE prefix/cost discriminator')
need(re.search(r'ROW control_scope POST .*switches=2/14 .*W=22/22',probe) is not None,'CONTROL discriminator')
need(re.search(r'ROW zero_bandwidth POST .*switches=2/14 .*fixed=7/0',probe) is not None,'zero-bandwidth discriminator')
need(re.search(r'ROW core_state_retained POST .*core=1,101,102,103,104,105 rt=11,21,101,201',probe) is not None,'retained core-state discriminator')
need(re.search(r'ROW cycle_underflow POST .*c0=2,128,18446744073709551611,',probe) is not None,'cycle-underflow discriminator')
need('ROW allocation_clone RESULT ids=0/1 bytes=31/42 dma=31/42 estimated=100/105 last=0/0' in probe,'allocation-clone discriminator')
need('ROW notify_wrap RESULT cmds=0 cycles=0 expired=0' in probe,'notification-wrap discriminator')
need('ROW slice_thresholds RESULT initial=0 c9=0 c10=1 c11=1 reset=0 m2=0 m3=1 m4=1' in probe,'slice under/exact/over discriminator')
need('ROW schedule_priority_repeat RESULT first=1 second=1' in probe,'repeated tie discriminator')
need('ROW unblock_all_states RESULT active=0 blocked=0 ready=0 idle=0 completed=0 invalid=-1' in probe,'unblock state census')
for label,calls,sizes in [('malloc_fail_w',1,'64/0/0'),('malloc_fail_a',2,'64/64/0'),('malloc_fail_o',3,'64/64/64'),('malloc_fail_resave',2,'64/64/0')]:
 need(f'ROW {label} RESULT calls={calls} sizes={sizes}' in probe,'malloc ordinal '+label)
need(re.search(r'ROW dma_domains POST .*edma=0,0,0,0,0,0,0 gdma=1,1,0,0,0,0,1',probe) is not None,'DMA-domain discriminator')
need(re.search(r'ROW bank_split POST .*W=00/00,64,32,4,11,0,0,1,1,1,2,12,0 bank0=2,0,23',probe) is not None,'bank split discriminator')
r=re.search(r'ROW rounding_prng_global RESULT a=([^ ]+) b=([^ ]+) ref=([^/]+)/([^ ]+) mode=1',probe)
need(r is not None and r.group(1)==r.group(3) and r.group(2)==r.group(4) and 'subnormal=0' in probe,'global PRNG/subnormal discriminator')
need(re.search(r'ROW malloc_fail_resave POST rc=-1 .*c0=1,[^\n]*,0(?: c1=)',probe) is not None,'destructive resave discriminator')
# Claim-bearing artifacts and validator mutation under optimization.
bundled_validator=text(run/'inputs/experiments/ch18_predraft_validate.py')
need(not any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(bundled_validator))),'optimizer-removable assertion in bundled validator')
ledger=text(run/'inputs/notes/chapter-18-source-and-claim-ledger.md'); report=text(run/'inputs/notes/chapter-18-predraft-source-audit-report.md'); review=text(run/'inputs/notes/chapter-18-skeptical-review-dispositions.md')
for phrase in ['exactly 19 public','two ACTIVE descriptors','priority-zero','process-global `g_tu_dma`','stale tails','not failure-atomic','C18.40']:
 need(phrase in ledger,'ledger missing '+phrase)
for phrase in ['39 implementation','171 structural','210 checks','Drafting gate is open','exact model values']:
 need(phrase in report,'report missing '+phrase)
need('Review state: **complete**' in review and 'Drafting verdict: **PASS**' in review,'post-review state/verdict')
for rel in ['validator-mutation-normal.log','validator-mutation-optimized.log']:
 need('CH18_PREDRAFT_VALIDATION FAIL: optimizer-removable assertion in validator' in text(run/rel),'validator mutation '+rel)
trans=text(run/'transcript.log')
for marker in ['SOURCE_PIN_MUTATION PASS','SOURCE_HASH_MUTATION PASS','STATIC_LINK PASS binaries=6','FOCUSED_CONTEXT PASS tests=15','FOCUSED_MUTATION PASS tests=14/15','SWEEP PASS rows=12','PROBE PASS failures=0 probe_translation_unit_O0_O2_match=yes sanitizer_clean=yes bounded=yes','VALIDATOR_MUTATION PASS','CH18_AUDIT_BODY_COMPLETE']:
 need(marker in trans,'missing transcript marker '+marker)
fm=re.fullmatch(r'FINALIZED_RUN run=(\S+) input_commit=([0-9a-f]{40}) transcript_sha256=([0-9a-f]{64})\n?',text(run/'finalization.log'))
need(fm is not None and fm.group(1)==f'experiments/runs/ch18-context/{RUN_ID}' and fm.group(2)==commit and fm.group(3)==sha(run/'transcript.log'),'finalization binding')
mc=text(run/'manifest-check.log').splitlines()
need(len(mc)==len(ret) and all(line.endswith(': OK') for line in mc),'manifest check did not pass')
need(not list(run.rglob('*.o')) and not list(run.rglob('*.tar')),'unretained build/archive artifact')
outer=run/'bundle-sha256.txt'
if outer.is_file():
 bm=manifest(outer); outer_set={'sha256-retained.txt','manifest-check.log','finalization.log','predraft-validation.log'}
 need(set(bm)==outer_set,'bundle manifest set mismatch')
 for rel,digest in bm.items(): need((run/rel).is_file() and sha(run/rel)==digest,'bundle hash mismatch '+rel)
 bc=text(run/'bundle-check.log').splitlines()
 need(len(bc)==len(bm) and all(line.endswith(': OK') for line in bc),'bundle check did not pass')
stage_files=set(ret)|{'sha256-retained.txt','manifest-check.log','finalization.log','predraft-validation.log'}
if outer.is_file(): stage_files|={'bundle-sha256.txt','bundle-check.log'}
actual={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file()}
need(actual==stage_files,'exact run inventory mismatch')
print(f'CH18_PREDRAFT_VALIDATION PASS run=experiments/runs/ch18-context/{RUN_ID} input_commit={commit} pin={PIN} inputs={len(inputs)} retained={len(ret)} apis=19 source_checks=210 focused=15 mutation=14/15 probe_rows={len(required)}')
