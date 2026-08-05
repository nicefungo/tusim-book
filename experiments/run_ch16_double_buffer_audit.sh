#!/usr/bin/env bash
set -euo pipefail

PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
BOOK_ROOT=$(git rev-parse --show-toplevel)
TUSIM_ROOT=${TUSIM_ROOT:-/home/zxy/Workplace/projects/tusim}
RUN_ID=${CH16_RUN_ID:-20260804-ch16-canonical-v4}
RUN_REL=experiments/runs/ch16-double-buffer/$RUN_ID
RUN_DIR=$BOOK_ROOT/$RUN_REL
INPUT_COMMIT=$(git rev-parse HEAD)
BRANCH=$(git branch --show-current)

[[ "$BRANCH" == main ]]
[[ -z "$(git status --porcelain)" ]]
[[ ! -e "$RUN_DIR" ]]
[[ "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" == "$PIN" ]]
! git -C "$TUSIM_ROOT" symbolic-ref -q HEAD >/dev/null
[[ -z "$(git -C "$TUSIM_ROOT" status --porcelain --untracked-files=all)" ]]

mkdir -p "$RUN_DIR/inputs"
TRANSCRIPT=$RUN_DIR/transcript.log
WORK=$(mktemp -d /tmp/ch16-audit-XXXXXX)
trap 'rm -rf "$WORK"' EXIT

INPUTS=(
  edition.yaml PLAN.md style-guide.md fidelity-matrix.md source-audit.md
  notes/chapter-16-framing-and-evidence-plan.md
  notes/chapter-16-source-and-claim-ledger.md
  notes/chapter-16-predraft-source-audit-report.md
  notes/chapter-16-skeptical-review-dispositions.md
  experiments/ch16_source_audit.py
  experiments/ch16_double_buffer_probe.c
  experiments/ch16_recompute_report.py
  experiments/ch16_predraft_validate.py
  experiments/run_ch16_double_buffer_audit.sh
)
for f in "${INPUTS[@]}"; do
  mkdir -p "$RUN_DIR/inputs/$(dirname "$f")"
  cp "$BOOK_ROOT/$f" "$RUN_DIR/inputs/$f"
done
( cd "$BOOK_ROOT" && sha256sum "${INPUTS[@]}" ) > "$RUN_DIR/input-hashes.txt"
printf '%s\n' "$INPUT_COMMIT" > "$RUN_DIR/input_commit"
printf '%s\n' "$PIN" > "$RUN_DIR/source_pin"

git -C "$TUSIM_ROOT" status --ignored --short --untracked-files=all | sha256sum > "$RUN_DIR/tusim-ignored-before.sha256"

git -C "$TUSIM_ROOT" archive "$PIN" | tar -x -C "$WORK"

body() {
  echo "CH16_AUDIT_START run=$RUN_REL input_commit=$INPUT_COMMIT pin=$PIN"
  echo "TOOLCHAIN host=$(uname -m) cc=$(cc -dumpfullversion -dumpversion) make=$(make --version | head -1) python=$(python3 --version 2>&1) gdb=$(gdb --version | head -1)"

  python3 "$BOOK_ROOT/experiments/ch16_source_audit.py" "$WORK" "$PIN" | tee "$RUN_DIR/source-audit.log"
  grep -F "CH16_SOURCE_AUDIT PASS pin=$PIN hashes=31 predicates=60 checks=91" "$RUN_DIR/source-audit.log"

  cp "$WORK/tu_cmodel/memory/double_buffer.c" "$WORK/double_buffer.c.orig"
  printf '\n' >> "$WORK/tu_cmodel/memory/double_buffer.c"
  set +e
  python3 "$BOOK_ROOT/experiments/ch16_source_audit.py" "$WORK" "$PIN" > "$RUN_DIR/source-audit-mutation.log" 2>&1
  src_mut_rc=$?
  set -e
  [[ $src_mut_rc -ne 0 ]]
  grep -F "hash mismatch tu_cmodel/memory/double_buffer.c" "$RUN_DIR/source-audit-mutation.log"
  mv "$WORK/double_buffer.c.orig" "$WORK/tu_cmodel/memory/double_buffer.c"
  python3 "$BOOK_ROOT/experiments/ch16_source_audit.py" "$WORK" "$PIN" > "$RUN_DIR/source-audit-restored.log"
  grep -F "CH16_SOURCE_AUDIT PASS" "$RUN_DIR/source-audit-restored.log"
  echo "SOURCE_HASH_MUTATION PASS rc=$src_mut_rc"

  make -C "$WORK" -j2 libtucmodel.a > "$RUN_DIR/build.log" 2>&1
  ar t "$WORK/libtucmodel.a" > "$RUN_DIR/archive-members.log"
  grep -Fx double_buffer.o "$RUN_DIR/archive-members.log"
  grep -Fx pipeline_controller.o "$RUN_DIR/archive-members.log"

  cc -std=c11 -O0 -g -Wall -Wextra -I"$WORK" -I"$WORK/tu_cmodel" \
    -o "$WORK/test-double" "$WORK/tests/test_double_buffer.c" "$WORK/libtucmodel.a" -lm
  cc -std=c11 -O0 -g -Wall -Wextra -I"$WORK" -I"$WORK/tu_cmodel" \
    -o "$WORK/ch16-probe" "$BOOK_ROOT/experiments/ch16_double_buffer_probe.c" "$WORK/libtucmodel.a" -lm
  readelf -d "$WORK/test-double" > "$RUN_DIR/test-double-readelf.log"
  readelf -d "$WORK/ch16-probe" > "$RUN_DIR/probe-readelf.log"
  ! grep -Eq 'NEEDED.*libtucmodel' "$RUN_DIR/test-double-readelf.log"
  ! grep -Eq 'NEEDED.*libtucmodel' "$RUN_DIR/probe-readelf.log"
  echo "STATIC_LINK PASS binaries=2"

  gdb -q -batch -ex run --args "$WORK/test-double" > "$RUN_DIR/test-double.log" 2>&1
  grep -F "=== Results: 10/10 passed, 0 failed ===" "$RUN_DIR/test-double.log"
  grep -F "exited normally" "$RUN_DIR/test-double.log"
  echo "FOCUSED_DOUBLE_BUFFER PASS tests=10"

  cp "$WORK/tests/test_double_buffer.c" "$WORK/tests/test_double_buffer.mut.c"
  python3 - "$WORK/tests/test_double_buffer.mut.c" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
old='ASSERT_EQ(stats.dma_to_shadow_bytes, 1024UL, "bytes should match");'
new='ASSERT_EQ(stats.dma_to_shadow_bytes, 1025UL, "bytes should match");'
assert s.count(old)==1
p.write_text(s.replace(old,new))
PY
  cc -std=c11 -O0 -g -Wall -Wextra -I"$WORK" -I"$WORK/tu_cmodel" \
    -o "$WORK/test-double-mut" "$WORK/tests/test_double_buffer.mut.c" "$WORK/libtucmodel.a" -lm
  set +e
  gdb -q -batch -ex run --args "$WORK/test-double-mut" > "$RUN_DIR/test-double-mutation.log" 2>&1
  gdb_mut_rc=$?
  set -e
  grep -F "=== Results: 9/10 passed, 1 failed ===" "$RUN_DIR/test-double-mutation.log"
  grep -F "exited with code 01" "$RUN_DIR/test-double-mutation.log"
  echo "FOCUSED_MUTATION PASS gdb_rc=$gdb_mut_rc inferior=01"

  gdb -q -batch -ex run --args "$WORK/ch16-probe" > "$RUN_DIR/probe.log" 2>&1
  grep -F "DB_CLEAN_SWAP count=1 active_idx=1 active=00 shadow=11 dirty=0" "$RUN_DIR/probe.log"
  grep -F "DB_NOTIFY_ONLY shadow_before=00 shadow_after=00 dirty=1 bytes=1016 dma_cycles=82" "$RUN_DIR/probe.log"
  grep -F "DB_SHARED_METER first=0 second=2 active_value=00000000 bank0_words=0" "$RUN_DIR/probe.log"
  grep -F "DB_DISABLE enabled=0 primary=44 db_null=1" "$RUN_DIR/probe.log"
  grep -F "PIPE_AFTER stage=2 completed=1 desc_cycles=53 pipe_cycle=0 dma_cycle=1 active=22 shadow=7a swapped=1 dirty=1" "$RUN_DIR/probe.log"
  grep -F "PIPE_LEDGER tiles=1 load=2 compute=5 seq=8 piped=7 saved=0 speedup=1.142857 pipe_cycle=6" "$RUN_DIR/probe.log"
  grep -F "PIPE_DEPTH1_NOLOAD tid=0 active=00 shadow=55 swaps=1 dirty=0 stage=2" "$RUN_DIR/probe.log"
  grep -F "PIPE_DEPTH1_LEDGER seq=5 piped=3 saved=0 speedup=1.666667" "$RUN_DIR/probe.log"
  grep -F "PIPE_EMPTY tid=0 seq=7 piped=0 saved=0 speedup=inf overlap_load=0 overlap_store=0" "$RUN_DIR/probe.log"
  grep -F "PIPE_RESET initialized=0 depth=2 slots_null=1 free_slots=1" "$RUN_DIR/probe.log"
  grep -F "PIPE_AFTER_RESET_SUBMIT tid=0 depth=1 initialized=1 stored_cmd=123" "$RUN_DIR/probe.log"
  grep -F "SRAM_REINIT primary_replaced=1 meter_replaced=1 db_lost=1 new_size=32" "$RUN_DIR/probe.log"
  grep -F "CTX_RESTORE ids=0,1 save_rc=0 restore_rc=0 db_lost=1 primary_live=1" "$RUN_DIR/probe.log"
  grep -F "CH16_PROBE SUMMARY failures=0" "$RUN_DIR/probe.log"
  grep -F "exited normally" "$RUN_DIR/probe.log"
  echo "BOUNDED_PROBE PASS"

  python3 "$BOOK_ROOT/experiments/ch16_recompute_report.py" | tee "$RUN_DIR/report-recompute.log"
  grep -F "CH16_SWEEP SUMMARY failures=0 rows=10" "$RUN_DIR/report-recompute.log"
  grep -F "CH16_SWEEP_CAPACITY single64_kib=64 double16_physical_kib=32 ratio=2.0" "$RUN_DIR/report-recompute.log"
  grep -F "CH16_SWEEP_PORT_CHECK independent_256pe_two_fp16_bytes_per_cycle=1024 report_claim=512" "$RUN_DIR/report-recompute.log"
  grep -F "CH16_SWEEP_THRESHOLD report=20 exact=17 continuous=18.285714" "$RUN_DIR/report-recompute.log"
  grep -F "CH16_SWEEP_RESOURCE_GUARD C=100 P=80 S=80 uncapped=160 shared_cap=100" "$RUN_DIR/report-recompute.log"
  echo "REPORT_RECOMPUTE PASS"

  make -C "$WORK" clean > /dev/null
  make -C "$WORK" -j2 CFLAGS='-O1 -g -std=c11 -Wall -Wextra -fsanitize=address -fno-omit-frame-pointer' libtucmodel.a > "$RUN_DIR/asan-build.log" 2>&1
  cc -O1 -g -std=c11 -Wall -Wextra -fsanitize=address -fno-omit-frame-pointer \
    -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK/ch16-probe-asan" \
    "$BOOK_ROOT/experiments/ch16_double_buffer_probe.c" "$WORK/libtucmodel.a" -lm
  gdb -q -batch -ex 'set environment ASAN_OPTIONS detect_leaks=0' -ex run \
    --args "$WORK/ch16-probe-asan" > "$RUN_DIR/asan-probe.log" 2>&1
  grep -F "SRAM_REINIT primary_replaced=1 meter_replaced=1 db_lost=1 new_size=32" "$RUN_DIR/asan-probe.log"
  grep -F "CTX_RESTORE ids=0,1 save_rc=0 restore_rc=0 db_lost=1 primary_live=1" "$RUN_DIR/asan-probe.log"
  grep -F "CH16_PROBE SUMMARY failures=0" "$RUN_DIR/asan-probe.log"
  grep -F "exited normally" "$RUN_DIR/asan-probe.log"
  ! grep -F "ERROR: AddressSanitizer" "$RUN_DIR/asan-probe.log"
  echo "ASAN_LIFECYCLE PASS detect_leaks=0 isolated_context_child=yes"

  echo "PIPELINE_SUITE_QUALIFIED not_executed=fixed_channels_3_requested_4"
  echo "CH16_AUDIT_BODY_COMPLETE"
}

set +e
set -o pipefail
body 2>&1 | tee "$TRANSCRIPT"
rc=${PIPESTATUS[0]}
set -e
[[ $rc -eq 0 ]]

[[ "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" == "$PIN" ]]
! git -C "$TUSIM_ROOT" symbolic-ref -q HEAD >/dev/null
[[ -z "$(git -C "$TUSIM_ROOT" status --porcelain --untracked-files=all)" ]]
git -C "$TUSIM_ROOT" status --ignored --short --untracked-files=all | sha256sum > "$RUN_DIR/tusim-ignored-after.sha256"
cmp -s "$RUN_DIR/tusim-ignored-before.sha256" "$RUN_DIR/tusim-ignored-after.sha256"
[[ "$(git -C "$BOOK_ROOT" rev-parse HEAD)" == "$INPUT_COMMIT" ]]
for f in "${INPUTS[@]}"; do cmp -s "$BOOK_ROOT/$f" "$RUN_DIR/inputs/$f"; done

(
  cd "$RUN_DIR"
  find inputs -type f -print0 | sort -z | xargs -0 sha256sum
  sha256sum input-hashes.txt input_commit source_pin tusim-ignored-before.sha256 tusim-ignored-after.sha256 \
    source-audit.log source-audit-mutation.log source-audit-restored.log build.log archive-members.log \
    test-double-readelf.log probe-readelf.log test-double.log test-double-mutation.log probe.log report-recompute.log \
    asan-build.log asan-probe.log transcript.log
) > "$RUN_DIR/sha256-retained.txt"
( cd "$RUN_DIR" && sha256sum -c sha256-retained.txt ) > "$RUN_DIR/manifest-check.log"
printf 'FINALIZED_RUN run=%s input_commit=%s transcript_sha256=%s\n' \
  "$RUN_REL" "$INPUT_COMMIT" "$(sha256sum "$TRANSCRIPT" | cut -d' ' -f1)" > "$RUN_DIR/finalization.log"
CH16_RUN_ID="$RUN_ID" python3 "$BOOK_ROOT/experiments/ch16_predraft_validate.py" | tee "$RUN_DIR/predraft-validation.log"
(
  cd "$RUN_DIR"
  sha256sum sha256-retained.txt manifest-check.log finalization.log predraft-validation.log
) > "$RUN_DIR/bundle-sha256.txt"
( cd "$RUN_DIR" && sha256sum -c bundle-sha256.txt ) > "$RUN_DIR/bundle-check.log"
echo "CH16_RUN_COMPLETE run=$RUN_REL"
