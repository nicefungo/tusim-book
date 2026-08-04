#!/usr/bin/env bash
set -euo pipefail

PIN="e918c80b6fce833cd1fcae97730fa841c2176f25"
BOOK_ROOT="${BOOK_ROOT:-/home/zxy/Workplace/books/tusim-book}"
TUSIM_ROOT="${TUSIM_ROOT:-/home/zxy/Workplace/projects/tusim}"
RUN_ID="${CH15_RUN_ID:-20260804-ch15-canonical}"
RUN_ROOT="$BOOK_ROOT/experiments/runs/ch15-dram"
RUN_DIR="$RUN_ROOT/$RUN_ID"
WORK_BASE="$(mktemp -d -t ch15-dram-XXXXXX)"
WORK="$WORK_BASE/work"
ARCHIVE="$WORK_BASE/tusim.tar"
TRANSCRIPT_TMP="$WORK_BASE/transcript.log"
BOOK_STATUS_BEFORE="$WORK_BASE/book-status-before.txt"
TUSIM_STATUS_BEFORE="$WORK_BASE/tusim-status-before.txt"
TUSIM_IGNORED_BEFORE="$WORK_BASE/tusim-ignored-before.txt"
BOOK_REMOTE_BEFORE="$WORK_BASE/book-remotes-before.txt"
trap 'rm -rf "$WORK_BASE"' EXIT
mkdir -p "$WORK" "$RUN_ROOT"
[[ ! -e "$RUN_DIR" ]] || { echo "run exists: $RUN_DIR" >&2; exit 2; }
mkdir -p "$RUN_DIR/inputs"

INPUTS=(
  edition.yaml
  PLAN.md
  experiments/ch15_source_audit.py
  experiments/ch15_dram_probe.c
  experiments/run_ch15_dram_audit.sh
  experiments/ch15_predraft_validate.py
  experiments/ch15-dram-audit-2026-08-04.md
  notes/chapter-15-framing-and-evidence-plan.md
  notes/chapter-15-source-and-claim-ledger.md
  notes/whole-book-replanning-2026-08-04.md
  references/foundations.md
)

ignored_inventory() {
  local repo="$1" out="$2"
  : > "$out"
  while IFS= read -r rel; do
    if [[ -f "$repo/$rel" ]]; then
      printf 'file ' >> "$out"; sha256sum "$repo/$rel" | sed "s#  $repo/#  #" >> "$out"
    elif [[ -d "$repo/$rel" ]]; then
      printf 'dir  %s\n' "$rel" >> "$out"
    else
      printf 'other %s\n' "$rel" >> "$out"
    fi
  done < <(git -C "$repo" ls-files --others -i --exclude-standard | LC_ALL=C sort)
}

run_gdb() {
  local exe="$1" log="$2"
  timeout 90s gdb -q -batch -ex run --args "$exe" > "$log" 2>&1
}

{
  echo "CH15_AUDIT start"
  echo "run_id=$RUN_ID"
  echo "pin=$PIN"
  date -Iseconds

  git -C "$BOOK_ROOT" status --porcelain --untracked-files=all > "$BOOK_STATUS_BEFORE"
  [[ -z "$(cat "$BOOK_STATUS_BEFORE")" ]] || { echo "book dirty"; cat "$BOOK_STATUS_BEFORE"; exit 1; }
  [[ "$(git -C "$BOOK_ROOT" branch --show-current)" == "main" ]] || { echo "book not main"; exit 1; }
  BOOK_HEAD="$(git -C "$BOOK_ROOT" rev-parse HEAD)"
  echo "book_head=$BOOK_HEAD"
  git -C "$BOOK_ROOT" remote -v > "$BOOK_REMOTE_BEFORE"
  grep -q 'github.com-tusim:nicefungo/tusim-book.git' "$BOOK_REMOTE_BEFORE"

  git -C "$TUSIM_ROOT" status --porcelain --untracked-files=all > "$TUSIM_STATUS_BEFORE"
  [[ -z "$(cat "$TUSIM_STATUS_BEFORE")" ]] || { echo "Tusim dirty"; cat "$TUSIM_STATUS_BEFORE"; exit 1; }
  [[ -z "$(git -C "$TUSIM_ROOT" branch --show-current)" ]] || { echo "Tusim not detached"; exit 1; }
  [[ "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" == "$PIN" ]] || { echo "Tusim pin mismatch"; exit 1; }
  ignored_inventory "$TUSIM_ROOT" "$TUSIM_IGNORED_BEFORE"
  echo "TUSIM_PRE PASS head=$PIN"

  for rel in "${INPUTS[@]}"; do
    mkdir -p "$RUN_DIR/inputs/$(dirname "$rel")"
    git -C "$BOOK_ROOT" show "$BOOK_HEAD:$rel" > "$RUN_DIR/inputs/$rel"
  done
  (cd "$RUN_DIR" && find inputs -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum) > "$RUN_DIR/input-hashes.txt"

  git -C "$TUSIM_ROOT" archive --format=tar --output="$ARCHIVE" "$PIN"
  sha256sum "$ARCHIVE" | sed "s#$ARCHIVE#tusim-$PIN.tar#" > "$RUN_DIR/source-archive-sha256.txt"
  tar -xf "$ARCHIVE" -C "$WORK"

  python3 "$RUN_DIR/inputs/experiments/ch15_source_audit.py" "$WORK" "$PIN" | tee "$RUN_DIR/source-audit.log"
  grep -q "CH15_SOURCE_AUDIT PASS pin=$PIN hashes=15 predicates=39 checks=54" "$RUN_DIR/source-audit.log"

  cp "$WORK/tu_cmodel/memory/dram_model.c" "$WORK_BASE/dram_model.c.orig"
  printf '\n/* ch15 mutation */\n' >> "$WORK/tu_cmodel/memory/dram_model.c"
  set +e
  python3 "$RUN_DIR/inputs/experiments/ch15_source_audit.py" "$WORK" "$PIN" > "$RUN_DIR/source-audit-mutation.log" 2>&1
  audit_mut_rc=$?
  set -e
  [[ $audit_mut_rc -ne 0 ]]
  grep -q "hash mismatch tu_cmodel/memory/dram_model.c" "$RUN_DIR/source-audit-mutation.log"
  cp "$WORK_BASE/dram_model.c.orig" "$WORK/tu_cmodel/memory/dram_model.c"
  echo "SOURCE_AUDIT_MUTATION PASS rc=$audit_mut_rc"

  make -C "$WORK" -j2 libtucmodel.a > "$RUN_DIR/build.log" 2>&1
  ar t "$WORK/libtucmodel.a" > "$RUN_DIR/archive-members.txt"
  grep -qx 'dram_model.o' "$RUN_DIR/archive-members.txt"
  grep -qx 'memory_hierarchy.o' "$RUN_DIR/archive-members.txt"
  echo "ARCHIVE_MEMBER PASS dram_model.o"
  echo "ARCHIVE_MEMBER PASS memory_hierarchy.o"

  cc -O2 -Wall -Wextra -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" \
    -o "$WORK/ch15-test-dram" "$WORK/tests/test_dram.c" "$WORK/libtucmodel.a" -lm
  cc -O2 -Wall -Wextra -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" \
    -o "$WORK/ch15-probe" "$RUN_DIR/inputs/experiments/ch15_dram_probe.c" "$WORK/libtucmodel.a" -lm
  for exe in ch15-test-dram ch15-probe; do
    if readelf -d "$WORK/$exe" | grep -q 'NEEDED.*libtucmodel'; then echo "dynamic Tusim dependency: $exe"; exit 1; fi
    echo "STATIC_LINK_PASS $exe"
  done

  run_gdb "$WORK/ch15-test-dram" "$RUN_DIR/test-dram.log"
  grep -q "=== Results: 12/12 passed ===" "$RUN_DIR/test-dram.log"
  echo "FOCUSED_TEST PASS 12/12"

  cp "$WORK/tests/test_dram.c" "$WORK_BASE/test_dram.c.orig"
  python3 - "$WORK/tests/test_dram.c" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
old='dram->params.bandwidth_gbps == 500.0'
assert s.count(old)==1
p.write_text(s.replace(old, 'dram->params.bandwidth_gbps == 501.0'))
PY
  cc -O2 -Wall -Wextra -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" \
    -o "$WORK/ch15-test-dram-mut" "$WORK/tests/test_dram.c" "$WORK/libtucmodel.a" -lm
  run_gdb "$WORK/ch15-test-dram-mut" "$RUN_DIR/test-dram-mutation.log"
  grep -q "=== Results: 11/12 passed ===" "$RUN_DIR/test-dram-mutation.log"
  grep -q "wrong BW" "$RUN_DIR/test-dram-mutation.log"
  cp "$WORK_BASE/test_dram.c.orig" "$WORK/tests/test_dram.c"
  echo "FOCUSED_TEST_MUTATION PASS expected=11/12"

  run_gdb "$WORK/ch15-probe" "$RUN_DIR/ch15-probe.log"
  for line in \
    "ESTIMATE hbm2_read64=51 hbm3_read819=41" \
    "ACCESS first cycles=50 stall=1000 current=0 budget=0" \
    "ACCESS same_channel cycles=50 stall=1050 current=0" \
    "ACCESS next_channel cycles=50 stall=1000 current=0" \
    "REFILL cycle=1000 cycles=50 stall=0 budget=255936 pending_r=64" \
    "ROW read_cycles=60 read_stall=1000 write_cycles=50 write_stall=1060 conflicts=1" \
    "STATS cycle=0 read_bw=1024.0 util=4.0 peak=256.0" \
    "CLOCK peak1=256 peak2=128 estimate_before=51 estimate_after=51" \
    "HIER type=1 rc=0 stall=1000 marker=0x5a dram_cycle=0" \
    "CONFIG rc=0 type=3 bw=777.0 row=1 rlat=33 wlat=44 manual_bw=819.0 manual_row=0" \
    "CH15_PROBE SUMMARY failures=0"; do
      grep -Fq "$line" "$RUN_DIR/ch15-probe.log" || { echo "missing probe line: $line"; exit 1; }
  done
  echo "PROBE PASS"

  [[ "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" == "$PIN" ]]
  [[ -z "$(git -C "$TUSIM_ROOT" status --porcelain --untracked-files=all)" ]]
  ignored_inventory "$TUSIM_ROOT" "$WORK_BASE/tusim-ignored-after.txt"
  cmp -s "$TUSIM_IGNORED_BEFORE" "$WORK_BASE/tusim-ignored-after.txt"
  echo "TUSIM_POST PASS head=$PIN ignored_inventory_unchanged=yes"
  [[ "$(git -C "$BOOK_ROOT" rev-parse HEAD)" == "$BOOK_HEAD" ]]
  git -C "$BOOK_ROOT" status --porcelain --untracked-files=all | \
    grep -v "^?? experiments/runs/ch15-dram/$RUN_ID/" > "$WORK_BASE/book-status-after-filtered.txt" || true
  [[ -z "$(cat "$WORK_BASE/book-status-after-filtered.txt")" ]]
  cmp -s "$BOOK_REMOTE_BEFORE" <(git -C "$BOOK_ROOT" remote -v)
  echo "BOOK_POST PASS inputs_unchanged=yes status_unchanged_outside_run=yes remote_unchanged=yes no_push_performed=yes"
  echo "CH15_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS"
} 2>&1 | tee "$TRANSCRIPT_TMP"

cp "$TRANSCRIPT_TMP" "$RUN_DIR/transcript.log"
(
  cd "$RUN_DIR"
  find inputs -type f -print
  printf '%s\n' source-archive-sha256.txt source-audit.log source-audit-mutation.log \
    archive-members.txt input-hashes.txt build.log test-dram.log test-dram-mutation.log \
    ch15-probe.log transcript.log
) | LC_ALL=C sort | while IFS= read -r rel; do (cd "$RUN_DIR" && sha256sum "$rel"); done > "$RUN_DIR/sha256-retained.txt"
(
  cd "$RUN_DIR"
  sha256sum -c sha256-retained.txt
  printf 'FINALIZED_RUN PASS run_dir=%s manifest=%s transcript_sha256=%s\n' \
    "$RUN_ID" "$RUN_ID/sha256-retained.txt" "$(sha256sum transcript.log | cut -d' ' -f1)"
) > "$RUN_DIR/finalization.log"
CH15_RUN_ID="$RUN_ID" python3 "$BOOK_ROOT/experiments/ch15_predraft_validate.py" | tee "$RUN_DIR/predraft-validation.log"
echo "CH15_CANONICAL_RUN PASS run=$RUN_DIR"
