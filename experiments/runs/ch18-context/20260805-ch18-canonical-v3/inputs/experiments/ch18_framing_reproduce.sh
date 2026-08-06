#!/usr/bin/env bash
set -euo pipefail

PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
TUSIM_ROOT=${TUSIM_ROOT:-/home/zxy/Workplace/projects/tusim}
TMP=$(mktemp -d /tmp/ch18-framing-reproduce-XXXXXX)
trap 'rm -rf "$TMP"' EXIT

printf 'CH18_FRAMING_REPRODUCTION_V1\n'
printf 'pin=%s\n' "$PIN"
printf 'source_head=%s\n' "$(git -C "$TUSIM_ROOT" rev-parse HEAD)"
test "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" = "$PIN"
test -z "$(git -C "$TUSIM_ROOT" branch --show-current)"
test -z "$(git -C "$TUSIM_ROOT" status --porcelain=v1 --untracked-files=all)"
printf 'source_detached_clean=PASS\n'
printf 'cc=%s\n' "$(cc --version | python3 -c 'import sys; print(sys.stdin.readline().rstrip())')"
printf 'make=%s\n' "$(make --version | python3 -c 'import sys; print(sys.stdin.readline().rstrip())')"
printf 'python=%s\n' "$(python3 --version 2>&1)"
printf 'source_file_hashes_begin\n'
for rel in \
  Makefile \
  tu_cmodel/infra/tu_context.c \
  tu_cmodel/infra/tu_context.h \
  tu_cmodel/tu_core.c \
  tu_cmodel/tu_core.h \
  tu_cmodel/isa/tu_scheduler.c \
  tu_cmodel/isa/tu_scheduler.h \
  tu_cmodel/isa/tu_liveness.c \
  tu_cmodel/isa/tu_liveness.h \
  tests/test_context.c \
  tests/test_context_switch_sweep.c \
  tests/test_scheduler.c \
  tests/test_scheduler_sweep.c \
  tests/test_liveness.c
 do
  hash=$(git -C "$TUSIM_ROOT" show "$PIN:$rel" | sha256sum)
  printf '%s  %s\n' "${hash%% *}" "$rel"
 done
printf 'source_file_hashes_end\n'

git -C "$TUSIM_ROOT" archive "$PIN" | tar -x -C "$TMP"
make -s -C "$TMP" libtucmodel.a
cc -O2 -Wall -Wextra -std=c11 -fPIC -I"$TMP" -I"$TMP/tu_cmodel" \
  -o "$TMP/test-context" "$TMP/tests/test_context.c" "$TMP/libtucmodel.a" -lm

printf 'focused_tests_begin\n'
"$TMP/test-context" 2>&1 | tee "$TMP/context.log"
make -s -C "$TMP" test-scheduler 2>&1 | tee "$TMP/scheduler.log"
make -s -C "$TMP" test-liveness 2>&1 | tee "$TMP/liveness.log"
python3 - "$TMP/context.log" "$TMP/scheduler.log" "$TMP/liveness.log" <<'PY'
from pathlib import Path
import sys
expected=('15/15 tests passed','Results: 14/14 passed','Results: 12/12 passed')
for path,needle in zip(sys.argv[1:],expected):
    if needle not in Path(path).read_text(): raise SystemExit(f'missing {needle} in {path}')
PY
printf 'focused_tests_summary=context_15_of_15 scheduler_14_of_14 liveness_12_of_12\n'
printf 'focused_tests_end\n'

printf 'context_sweep_begin\n'
make -s -C "$TMP" test-context-switch-sweep 2>&1 | tee "$TMP/context-sweep.log"
python3 - "$TMP/context-sweep.log" <<'PY'
from pathlib import Path
import re,sys
rows={}
for line in Path(sys.argv[1]).read_text().splitlines():
    m=re.fullmatch(r'\s*(\d+)\s+(full|live25|control)\s+(\d+)\s+(\d+)\s*',line)
    if m: rows[(int(m.group(1)),m.group(2))]=(int(m.group(3)),int(m.group(4)))
expected={(256,'full'):(262144,16484),(256,'live25'):(65536,4196),(256,'control'):(0,100)}
if any(rows.get(k)!=v for k,v in expected.items()): raise SystemExit(f'context sweep mismatch: {rows}')
PY
printf 'context_sweep_selected_rows=PASS\n'
printf 'context_sweep_end\n'

printf 'scheduler_sweep_begin\n'
make -s -C "$TMP" test-scheduler-sweep 2>&1 | tee "$TMP/scheduler-sweep.log"
python3 - "$TMP/scheduler-sweep.log" <<'PY'
from pathlib import Path
import re,sys
by={}
for line in Path(sys.argv[1]).read_text().splitlines():
    m=re.fullmatch(r'\s*([A-Za-z-]+)\s+(ASAP|ALAP|BALANCED)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*',line)
    if m:
        by.setdefault(m.group(1),[]).append(tuple(int(m.group(i)) for i in range(3,7)))
if len(by)!=5 or any(len(v)!=3 or len(set(v))!=1 for v in by.values()):
    raise SystemExit(f'scheduler policy invariance failed: {by}')
want=(28,0,0,13)
if by.get('Pipeline-Tiles') != [want,want,want]: raise SystemExit(f'pipeline row mismatch: {by.get("Pipeline-Tiles")}')
print('scheduler_policy_invariance=PASS topologies='+str(len(by)))
PY
printf 'scheduler_sweep_end\n'

python3 - "$TMP" <<'PY'
from pathlib import Path
import re, sys
root=Path(sys.argv[1])
symbols={
 'context': re.compile(r'\btu_ctx_[A-Za-z0-9_]+\s*\('),
 'scheduler': re.compile(r'\btu_sched_[A-Za-z0-9_]+\s*\('),
 'liveness': re.compile(r'\btu_live_[A-Za-z0-9_]+\s*\('),
}
own_parts={
 'context':{'tu_cmodel/infra/tu_context.c','tu_cmodel/infra/tu_context.h'},
 'scheduler':{'tu_cmodel/isa/tu_scheduler.c','tu_cmodel/isa/tu_scheduler.h'},
 'liveness':{'tu_cmodel/isa/tu_liveness.c','tu_cmodel/isa/tu_liveness.h'},
}
for name,pat in symbols.items():
    hits=[]
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix not in {'.c','.h','.cc','.cpp','.py'}: continue
        rel=p.relative_to(root).as_posix()
        if rel.startswith(('tests/','docs/')) or rel in own_parts[name]: continue
        try: text=p.read_text(errors='ignore')
        except OSError: continue
        if pat.search(text): hits.append(rel)
    print(f'non_test_external_callers_{name}={len(hits)} paths={";".join(sorted(hits)) or "NONE"}')
    if hits: raise SystemExit(f'unexpected non-test external callers for {name}')
print('caller_inventory=PASS')
PY

test "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" = "$PIN"
test -z "$(git -C "$TUSIM_ROOT" branch --show-current)"
test -z "$(git -C "$TUSIM_ROOT" status --porcelain=v1 --untracked-files=all)"
printf 'source_after_detached_clean=PASS\n'
printf 'CH18_FRAMING_REPRODUCTION_PASS\n'
