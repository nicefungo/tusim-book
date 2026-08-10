#!/usr/bin/env bash
set -euo pipefail

PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
TUSIM_ROOT=${TUSIM_ROOT:-/home/zxy/Workplace/projects/tusim}
TMP=$(mktemp -d /tmp/ch19-framing-reproduce-XXXXXX)
trap 'rm -rf "$TMP"' EXIT

printf 'CH19_FRAMING_REPRODUCTION_V1\n'
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
  tu_cmodel/isa/tu_isa.h \
  tu_cmodel/isa/tu_scheduler.c \
  tu_cmodel/isa/tu_scheduler.h \
  tu_cmodel/isa/tu_liveness.c \
  tu_cmodel/isa/tu_liveness.h \
  tests/test_scheduler.c \
  tests/test_scheduler_sweep.c \
  tests/test_liveness.c \
  docs/compiler-scheduling-pass.md \
  docs/liveness-allocation.md \
  docs/exploration/scheduler-policy-sweep.md \
  compiler/onnx_to_tu.py \
  tu_cmodel/command_queue.c \
  tu_cmodel/tu_asm.c
 do
  hash=$(git -C "$TUSIM_ROOT" show "$PIN:$rel" | sha256sum)
  printf '%s  %s\n' "${hash%% *}" "$rel"
 done
printf 'source_file_hashes_end\n'

git -C "$TUSIM_ROOT" archive "$PIN" | tar -x -C "$TMP"
make -s -C "$TMP" libtucmodel.a >"$TMP/build.log" 2>&1
make -s -C "$TMP" test-scheduler >"$TMP/scheduler.log" 2>&1
make -s -C "$TMP" test-liveness >"$TMP/liveness.log" 2>&1
make -s -C "$TMP" test-scheduler-sweep >"$TMP/scheduler-sweep.log" 2>&1

python3 - "$TMP" <<'PY'
from pathlib import Path
import re, sys
root = Path(sys.argv[1])
checks = [
    (root/'scheduler.log', 'Results: 14/14 passed'),
    (root/'liveness.log', 'Results: 12/12 passed'),
]
for path, needle in checks:
    text = path.read_text(errors='replace')
    if needle not in text:
        raise SystemExit(f'missing {needle} in {path}')
print('focused_tests=scheduler_14_of_14 liveness_12_of_12')

by = {}
for line in (root/'scheduler-sweep.log').read_text(errors='replace').splitlines():
    m = re.fullmatch(r'\s*([A-Za-z-]+)\s+(ASAP|ALAP|BALANCED)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*', line)
    if m:
        by.setdefault(m.group(1), []).append(tuple(int(m.group(i)) for i in range(3, 7)))
if len(by) != 5 or any(len(v) != 3 or len(set(v)) != 1 for v in by.values()):
    raise SystemExit(f'scheduler policy invariance failed: {by}')
want = (28, 0, 0, 13)
if by.get('Pipeline-Tiles') != [want, want, want]:
    raise SystemExit(f'pipeline row mismatch: {by.get("Pipeline-Tiles")}')
print('scheduler_policy_invariance=PASS topologies=5 pipeline_tiles=28,0,0,13')

makefile = (root/'Makefile').read_text(errors='replace').replace('\\\n', ' ')
if '$(TU_DIR)/isa/tu_scheduler.o' not in makefile or '$(TU_DIR)/isa/tu_liveness.o' not in makefile:
    raise SystemExit('scheduler/liveness archive membership missing')
m = re.search(r'^test:(.*?)(?:\n\t|\n[^ \t])', makefile, re.M | re.S)
if not m or 'test-scheduler' not in m.group(1) or 'test-liveness' not in m.group(1):
    raise SystemExit('scheduler/liveness aggregate membership missing')
print('build_reachability=archive_membership_PASS aggregate_test_membership_PASS')

headers = {
    'scheduler': root/'tu_cmodel/isa/tu_scheduler.h',
    'liveness': root/'tu_cmodel/isa/tu_liveness.h',
}
patterns = {
    'scheduler': re.compile(r'\b(tu_sched_[A-Za-z0-9_]+)\s*\('),
    'liveness': re.compile(r'\b(tu_live_[A-Za-z0-9_]+)\s*\('),
}
expected_counts = {'scheduler': 9, 'liveness': 7}
own = {
    'scheduler': {'tu_cmodel/isa/tu_scheduler.c', 'tu_cmodel/isa/tu_scheduler.h'},
    'liveness': {'tu_cmodel/isa/tu_liveness.c', 'tu_cmodel/isa/tu_liveness.h'},
}
for name, header in headers.items():
    public = sorted(set(patterns[name].findall(header.read_text(errors='replace'))))
    if len(public) != expected_counts[name]:
        raise SystemExit(f'{name} public API mismatch: {public}')
    callers = []
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix not in {'.c', '.h', '.cc', '.cpp', '.py'}:
            continue
        rel = p.relative_to(root).as_posix()
        if rel.startswith(('tests/', 'docs/')) or rel in own[name]:
            continue
        text = p.read_text(errors='ignore')
        if any(re.search(rf'\b{re.escape(sym)}\s*\(', text) for sym in public):
            callers.append(rel)
    print(f'public_apis_{name}={len(public)}')
    print(f'non_test_external_callers_{name}={len(callers)} paths={";".join(sorted(callers)) or "NONE"}')
    if callers:
        raise SystemExit(f'unexpected {name} non-test callers: {callers}')

liveness_c = (root/'tu_cmodel/isa/tu_liveness.c').read_text(errors='replace')
if re.search(r'\btu_sched_[A-Za-z0-9_]+\s*\(', liveness_c):
    raise SystemExit('unexpected scheduler call from liveness implementation')
scheduler_c = (root/'tu_cmodel/isa/tu_scheduler.c').read_text(errors='replace')
if re.search(r'\btu_live_[A-Za-z0-9_]+\s*\(', scheduler_c):
    raise SystemExit('unexpected liveness call from scheduler implementation')
print('scheduler_liveness_call_bridge=ABSENT')

for rel in ('config/tu_config.json', 'config/tu_config.yaml'):
    text = (root/rel).read_text(errors='replace').lower()
    hits = sorted(set(re.findall(r'scheduler|liveness|spill|alloc_strategy|max_hoist|max_window|pipeline_tiles', text)))
    if hits:
        raise SystemExit(f'unexpected shipped config controls in {rel}: {hits}')
print('shipped_json_yaml_controls=NONE')
PY

test "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" = "$PIN"
test -z "$(git -C "$TUSIM_ROOT" branch --show-current)"
test -z "$(git -C "$TUSIM_ROOT" status --porcelain=v1 --untracked-files=all)"
printf 'source_after_detached_clean=PASS\n'
printf 'CH19_FRAMING_REPRODUCTION_PASS\n'
