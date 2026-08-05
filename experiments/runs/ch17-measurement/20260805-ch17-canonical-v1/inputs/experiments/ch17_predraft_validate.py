#!/usr/bin/env python3
import hashlib,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
run_id=os.environ.get('CH17_RUN_ID','20260805-ch17-canonical-v1')
run=ROOT/'experiments/runs/ch17-measurement'/run_id
assert run.is_dir(),run
trans=(run/'transcript.log').read_text()
input_commit=(run/'input_commit').read_text().strip()
required=[
'CH17_SOURCE_AUDIT PASS pin=e918c80b6fce833cd1fcae97730fa841c2176f25 hashes=31 predicates=65 checks=96',
'SOURCE_HASH_MUTATION PASS','STATIC_LINK PASS binaries=7','FOCUSED_PERF PASS tests=12',
'FOCUSED_TRACE PASS tests=31','FOCUSED_LOGGING PASS tests=7','FOCUSED_POWER PASS tests=20',
'FOCUSED_CYCLE PASS tests=21','FOCUSED_MUTATION PASS tests=11/12','BENCHMARK_QUALIFIED rc=0 no_fail_closed_count=yes',
'PERF_ADDITIVE total=18 wall_ns=18 dma_read=64 dma_stall=2 compute=6 macs=8 leak=0.018',
'PERF_DUPLICATE after_explicit_tick=24 compute=6',
'PERF_OMISSIONS diff_ws=0 diff_gbuf_conf=0 diff_row_hits=0 merge_ws=0 merge_gbuf_conf=0 merge_row_hits=0 merge_energy_total=0.0',
'PERF_RESET energy_mac=99.0 total=0','PERF_METRICS dma_gbps=10.000 tops=0.001000 efficiency=0.003906250 util=0.500 hit=1.000',
'CYCLE_EST tile=14 current=14','CYCLE_WRITE cycles=15 cm=15 perf=15 read_bytes=32 write_bytes=0 read_cycles=15 write_cycles=0',
'CYCLE_BRIDGE cm=20 perf=20','TRACE_CONTEXT first_cycle=0 dirty=1 enabled=0','TRACE_CONTEXT second_cycle=3 dirty=0',
'TRACE_LOG count=2 first=0 second=9 global=9',
'POWER_TABLE area=1.051648 mac=2.000 spad=0.400 dram=370.000 dma=0.640 clock=0.100 leak=52.5824 total=425.7224 avg_mw=42.5722',
'POWER_DECREASING_DIFF cycles=18446744073709551606 macs=18446744073709551606 energy_mac=-2.000',
'CH17_PROBE SUMMARY failures=0','CH17_AUDIT_BODY_COMPLETE']
for x in required: assert x in trans,x
assert 'CH17_AUDIT PASS' not in trans
inputs=[]
for line in (run/'input-hashes.txt').read_text().splitlines():
 h,rel=line.split(None,1); rel=rel.strip(); inputs.append(rel)
 p=run/'inputs'/rel; assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h
 blob=subprocess.check_output(['git','show',f'{input_commit}:{rel}'],cwd=ROOT)
 assert blob==p.read_bytes(),rel
manifest=(run/'sha256-retained.txt').read_text().splitlines(); assert manifest
for line in manifest:
 h,rel=line.split(None,1); p=run/rel.strip(); assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h
assert not list(run.rglob('*.o')) and not list(run.rglob('*.tar'))
fin=(run/'finalization.log').read_text(); th=hashlib.sha256((run/'transcript.log').read_bytes()).hexdigest(); assert th in fin
print(f'CH17_PREDRAFT_VALIDATION PASS files={len(inputs)} run={run.relative_to(ROOT)} input_commit={input_commit}')
