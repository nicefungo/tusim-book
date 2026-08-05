#!/usr/bin/env python3
import ast,hashlib,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def require(condition,message):
 if not condition: raise SystemExit(f'CH17_PREDRAFT_VALIDATION FAIL: {message}')
def has_assert(source):
 try: return any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(source)))
 except SyntaxError as e: raise SystemExit(f'CH17_PREDRAFT_VALIDATION FAIL: invalid validator source: {e}')
require(not has_assert(Path(__file__).read_text()),'optimizer-removable assertion in validator')
run_id=os.environ.get('CH17_RUN_ID','20260805-ch17-canonical-v4')
run=ROOT/'experiments/runs/ch17-measurement'/run_id
require(run.is_dir(),run)
trans=(run/'transcript.log').read_text()
input_commit=(run/'input_commit').read_text().strip()
required=[
'CH17_SOURCE_AUDIT PASS pin=e918c80b6fce833cd1fcae97730fa841c2176f25 hashes=31 predicates=96 checks=127',
'SOURCE_PIN_MUTATION PASS','SOURCE_HASH_MUTATION PASS','STATIC_LINK PASS binaries=7','FOCUSED_PERF PASS tests=12',
'FOCUSED_TRACE PASS tests=31','FOCUSED_LOGGING PASS tests=7','FOCUSED_POWER PASS tests=20',
'FOCUSED_CYCLE PASS tests=21','FOCUSED_MUTATION PASS tests=11/12','BENCHMARK_QUALIFIED rc=0 no_fail_closed_count=yes',
'PERF_ADDITIVE total=18 wall_ns=18 dma_read=64 dma_stall=2 compute=6 macs=8 leak=0.018',
'PERF_DUPLICATE after_explicit_tick=24 compute=6',
'PERF_TIME_MAP op=5 idle=2 spad=3 dram=4 internal=2 timed=16 after_no_time=16 descriptor=13',
'PERF_DIFF_OMISSIONS ws=0 os=0 gbuf=0 hits=0 misses=0 bw=0.0/0.0/0.0 wall=0 params=0/0/0/0/0/0 enabled=0',
'PERF_MERGE_OMISSIONS ws=0 os=0 gbuf=0 hits=0 misses=0 bw=0.0/0.0/0.0 wall=0 total=0.0 params=1.00/0.50/0.50/20.0/0.050/0.001 power_enabled=0 freq=1000 enabled=0',
'PERF_RESET enabled=1 freq=777 energy_mac=99.0 total=0','PERF_METRICS dma_gbps=10.000 tops=0.001000 efficiency=0.003906250 util=0.500 hit=1.000',
'PERF_UNBOUNDED efficiency=2.0 hit=-1.0 reported_power_mw=1000.0 physical_power_mw=1.0 cached_total=0.0',
'CYCLE_EST tile=14 current=14','CYCLE_WRITE cycles=15 cm=15 perf=15 read_bytes=32 write_bytes=0 read_cycles=15 write_cycles=0',
'CYCLE_BRIDGE cm=20 perf=20','CYCLE_BANK isolated_stall=0 reads=1 conflicts=1 utilization=0.500',
'CYCLE_DMA_DIRECTION read_arg=21 write_arg=28 write_perf_read=4 write_perf_write=0',
'TRACE_CONTEXT first_cycle=0 dirty=1 enabled=0','TRACE_CONTEXT second_cycle=3 dirty=0',
'TRACE_LOG count=2 first=0 second=9 global=9',
'POWER_TABLE area=1.051648 mac=2.000 spad=0.400 dram=370.000 dma=0.640 clock=0.100 leak=52.5824 total=425.7224 avg_mw=42.5722',
'POWER_DECREASING_DIFF cycles=18446744073709551606 macs=18446744073709551606 energy_mac=-2.000',
'CH17_PROBE SUMMARY failures=0','VALIDATOR_MUTATION PASS normal_rc=1 optimized_rc=1','CH17_AUDIT_BODY_COMPLETE']
for x in required: require(x in trans,x)
require('CH17_AUDIT PASS' not in trans,'self-authored pass marker in transcript')
inputs=[]
for line in (run/'input-hashes.txt').read_text().splitlines():
 h,rel=line.split(None,1); rel=rel.strip(); inputs.append(rel)
 p=run/'inputs'/rel; require(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h,f'input hash {rel}')
 blob=subprocess.check_output(['git','show',f'{input_commit}:{rel}'],cwd=ROOT)
 require(blob==p.read_bytes(),f'input commit drift {rel}')
manifest=(run/'sha256-retained.txt').read_text().splitlines(); require(bool(manifest),'empty retained manifest')
validator_source=(run/'inputs/experiments/ch17_predraft_validate.py').read_text()
require(not has_assert(validator_source),'optimizer-removable assertion in validator')
for line in manifest:
 h,rel=line.split(None,1); p=run/rel.strip(); require(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h,f'retained hash {rel.strip()}')
require(not list(run.rglob('*.o')) and not list(run.rglob('*.tar')),'unretained build/archive artifact')
fin=(run/'finalization.log').read_text(); th=hashlib.sha256((run/'transcript.log').read_bytes()).hexdigest(); require(th in fin,'transcript finalization hash')
print(f'CH17_PREDRAFT_VALIDATION PASS files={len(inputs)} run={run.relative_to(ROOT)} input_commit={input_commit}')
