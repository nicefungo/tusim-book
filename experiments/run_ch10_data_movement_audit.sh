#!/usr/bin/env bash
set -euo pipefail

BOOK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TUSIM_ROOT="${1:-/home/zxy/Workplace/projects/tusim}"
PIN="e918c80b6fce833cd1fcae97730fa841c2176f25"
RUN_BASE="$BOOK_ROOT/experiments/runs/ch10-dma-contracts"
mkdir -p "$RUN_BASE"

# Fail provenance before creating durable evidence.
TUSIM_HEAD=$(git -C "$TUSIM_ROOT" rev-parse HEAD)
TUSIM_BRANCH=$(git -C "$TUSIM_ROOT" symbolic-ref -q --short HEAD || true)
TUSIM_STATUS=$(git -C "$TUSIM_ROOT" status --porcelain=v1 --untracked-files=all)
BOOK_HEAD=$(git -C "$BOOK_ROOT" rev-parse HEAD)
BOOK_BRANCH=$(git -C "$BOOK_ROOT" branch --show-current)
BOOK_REMOTES=$(git -C "$BOOK_ROOT" remote)
[[ "$TUSIM_HEAD" == "$PIN" && -z "$TUSIM_BRANCH" && -z "$TUSIM_STATUS" ]]
[[ -z "$BOOK_REMOTES" ]]

RUN_ID="${CH10_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
RUN_DIR="$RUN_BASE/$RUN_ID"
RUN_REL="${RUN_DIR#$BOOK_ROOT/}"
mkdir "$RUN_DIR"
TRANSCRIPT="$RUN_DIR/transcript.log"
ARCHIVE="$RUN_DIR/tusim-$PIN.tar"
WORK="$RUN_DIR/worktree"
IGNORED_BEFORE=$(mktemp)
IGNORED_AFTER=$(mktemp)
BOOK_STATUS_BEFORE=$(mktemp)
BOOK_STATUS_AFTER=$(mktemp)

cleanup() {
  rc=$?
  rm -rf "$WORK" "$ARCHIVE"
  rm -f "$IGNORED_BEFORE" "$IGNORED_AFTER" "$BOOK_STATUS_BEFORE" "$BOOK_STATUS_AFTER"
  trap - EXIT
  exit "$rc"
}
trap cleanup EXIT

run() { printf '+ '; printf '%q ' "$@"; printf '\n'; "$@"; }
section() { printf '\n===== %s =====\n' "$*"; }

# Snapshot book state before the run directory can affect it.
git -C "$BOOK_ROOT" status --porcelain=v1 --untracked-files=all > "$BOOK_STATUS_BEFORE"

# Everything in audit_body is captured in the finalized transcript.
audit_body() {
  section "provenance before"
  printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'book_root=%s\nbook_head=%s\nbook_branch=%s\nbook_remotes=%s\n' \
    "$BOOK_ROOT" "$BOOK_HEAD" "$BOOK_BRANCH" "$(git -C "$BOOK_ROOT" remote | wc -l)"
  printf '%s\n' 'BOOK_STATUS_BEFORE_BEGIN'
  cat "$BOOK_STATUS_BEFORE"
  printf '%s\n' 'BOOK_STATUS_BEFORE_END'
  printf 'tusim_root=%s\ntusim_head=%s\ntusim_branch=DETACHED\ntusim_status_bytes=%s\n' \
    "$TUSIM_ROOT" "$TUSIM_HEAD" "${#TUSIM_STATUS}"
  git -C "$TUSIM_ROOT" status --ignored --porcelain=v1 --untracked-files=all > "$IGNORED_BEFORE"
  printf 'tusim_ignored_inventory_sha256=%s\n' "$(sha256sum "$IGNORED_BEFORE" | cut -d' ' -f1)"
  printf '%s\n' 'TUSIM_IGNORED_INVENTORY_BEGIN'
  cat "$IGNORED_BEFORE"
  printf '%s\n' 'TUSIM_IGNORED_INVENTORY_END'

  section "create pinned disposable source"
  run git -C "$TUSIM_ROOT" archive --format=tar -o "$ARCHIVE" "$PIN"
  printf 'SOURCE_ARCHIVE_RECORDED_SHA256 %s\n' "$(sha256sum "$ARCHIVE" | cut -d' ' -f1)"
  mkdir "$WORK"
  run tar -xf "$ARCHIVE" -C "$WORK"
  run python3 "$BOOK_ROOT/experiments/ch10_source_audit.py" "$WORK"

  section "source and artifact input hashes"
  (
    cd "$BOOK_ROOT"
    sha256sum \
      experiments/ch10_source_audit.py \
      experiments/ch10_data_movement_probe.c \
      experiments/ch10_extended_probe.c \
      experiments/run_ch10_data_movement_audit.sh \
      experiments/ch10_predraft_validate.py \
      experiments/ch10-dma-descriptor-audit-2026-07-27.md \
      notes/chapter-10-framing-and-evidence-plan.md \
      notes/chapter-10-source-and-claim-ledger.md \
      notes/chapter-10-skeptical-review-dispositions.md \
      references/foundations.md
  ) | tee "$RUN_DIR/input-hashes.txt"

  section "contained static archive build"
  # Do not invoke the pinned Makefile's `clean`: that target removes global /tmp paths.
  # Delete only archived build products, and only beneath the disposable extraction.
  while IFS= read -r rel; do
    case "$rel" in
      *.o|*.a|*.so) rm -f "$WORK/$rel" ;;
    esac
  done < <(git -C "$TUSIM_ROOT" ls-tree -r --name-only "$PIN")
  run make -C "$WORK" -j2 libtucmodel.a
  ar t "$WORK/libtucmodel.a" | sort | tee "$RUN_DIR/archive-members.txt"
  for member in dma_descriptor.o address_generator.o double_buffer.o pipeline_controller.o; do
    grep -qx "$member" "$RUN_DIR/archive-members.txt"
    printf 'ARCHIVE_MEMBER PASS %s\n' "$member"
  done
  [[ ! -e "$WORK/libtucmodel.so" ]]
  cd "$WORK"

  CFLAGS=(-O2 -Wall -Wextra -std=c11 -fPIC -I. -Itu_cmodel)
  LDFLAGS=(./libtucmodel.a -lm)

  section "focused harness observations"
  suites=(
    "ch10-dma:tests/test_dma.c"
    "ch10-scatter-gather:tests/test_scatter_gather.c"
    "ch10-multicast:tests/test_multicast.c"
    "ch10-agen:tests/test_address_gen.c"
    "ch10-double-buffer:tests/test_double_buffer.c"
    "ch10-cmdq:tests/test_command_queue.c"
    "ch10-cmodel:tests/test_cmodel.c"
    "ch10-config:tests/test_config.c"
  )
  for spec in "${suites[@]}"; do
    exe="${spec%%:*}"; src="${spec#*:}"
    run gcc "${CFLAGS[@]}" -o "$exe" "$src" "${LDFLAGS[@]}"
    if ldd "$exe" 2>/dev/null | grep -q 'libtucmodel'; then
      echo "ERROR shared libtucmodel resolution: $exe" >&2; return 1
    fi
    printf '+ ./%s\n' "$exe"
    set +e
    "./$exe" 2>&1 | tee "$RUN_DIR/$exe.log"
    rc=${PIPESTATUS[0]}
    set -e
    if [[ "$exe" == ch10-agen ]]; then
      [[ $rc -eq 1 ]]
      grep -Fq 'Results: 12/13 passed' "$RUN_DIR/$exe.log"
      grep -Fq 'expected 272, got 268' "$RUN_DIR/$exe.log"
      echo 'EXPECTED_FINDING MATCH address-generator transposed case fails 12/13'
    else
      [[ $rc -eq 0 ]]
    fi
  done
  printf '%s\n' 'HARNESS_QUALIFICATION test_config.c is observation-only: its CHECK macro uses bare return in int main; it is not an enforced fail-closed gate.'
  printf '%s\n' 'PIPELINE_SUITE_SKIP enforced by SOURCE_AUDIT: unmodified harness requests 4 channels against a 3-entry array; bounded one-channel probe is not equivalent suite coverage.'

  section "fail-closed custom probes"
  cp "$BOOK_ROOT/experiments/ch10_data_movement_probe.c" tests/ch10_data_movement_probe.c
  run gcc "${CFLAGS[@]}" -o ch10-probe tests/ch10_data_movement_probe.c "${LDFLAGS[@]}"
  run ./ch10-probe | tee "$RUN_DIR/ch10-probe.log"
  grep -Fq 'SUMMARY failures=0' "$RUN_DIR/ch10-probe.log"

  cp "$BOOK_ROOT/experiments/ch10_extended_probe.c" tests/ch10_extended_probe.c
  run gcc "${CFLAGS[@]}" -o ch10-extended tests/ch10_extended_probe.c "${LDFLAGS[@]}"
  run ./ch10-extended | tee "$RUN_DIR/ch10-extended.log"
  grep -Fq 'EXTENDED_SUMMARY failures=0' "$RUN_DIR/ch10-extended.log"

  section "retained artifact manifest phase one"
  (
    cd "$BOOK_ROOT"
    sha256sum \
      experiments/ch10_source_audit.py \
      experiments/ch10_data_movement_probe.c \
      experiments/ch10_extended_probe.c \
      experiments/run_ch10_data_movement_audit.sh \
      experiments/ch10_predraft_validate.py \
      experiments/ch10-dma-descriptor-audit-2026-07-27.md \
      notes/chapter-10-framing-and-evidence-plan.md \
      notes/chapter-10-source-and-claim-ledger.md \
      notes/chapter-10-skeptical-review-dispositions.md \
      references/foundations.md \
      "$RUN_REL/archive-members.txt" \
      "$RUN_REL/input-hashes.txt" \
      "$RUN_REL"/ch10-*.log
  ) > "$RUN_DIR/sha256-retained.txt"
  cat "$RUN_DIR/sha256-retained.txt"

  section "provenance after"
  [[ "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" == "$PIN" ]]
  [[ -z "$(git -C "$TUSIM_ROOT" symbolic-ref -q --short HEAD || true)" ]]
  [[ -z "$(git -C "$TUSIM_ROOT" status --porcelain=v1 --untracked-files=all)" ]]
  git -C "$TUSIM_ROOT" status --ignored --porcelain=v1 --untracked-files=all > "$IGNORED_AFTER"
  cmp "$IGNORED_BEFORE" "$IGNORED_AFTER"
  printf 'TUSIM_POST PASS head=%s detached=yes tracked_and_untracked_clean=yes ignored_inventory_unchanged=yes\n' "$PIN"

  [[ "$(git -C "$BOOK_ROOT" rev-parse HEAD)" == "$BOOK_HEAD" ]]
  [[ "$(git -C "$BOOK_ROOT" branch --show-current)" == "$BOOK_BRANCH" ]]
  [[ -z "$(git -C "$BOOK_ROOT" remote)" ]]
  (cd "$BOOK_ROOT" && sha256sum -c "$RUN_REL/input-hashes.txt")
  git -C "$BOOK_ROOT" status --porcelain=v1 --untracked-files=all \
    | grep -v -F "?? $RUN_REL/" > "$BOOK_STATUS_AFTER" || true
  cmp "$BOOK_STATUS_BEFORE" "$BOOK_STATUS_AFTER"
  printf 'BOOK_POST PASS head=%s branch=%s inputs_unchanged=yes status_unchanged_outside_run=yes remotes=0\n' "$BOOK_HEAD" "$BOOK_BRANCH"

  section "result"
  printf 'AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS run_dir=%s\n' "$RUN_DIR"
}

# Phase one transcript capture. `wait` ensures tee has closed the completed transcript.
set +e
audit_body > >(tee "$TRANSCRIPT") 2>&1
AUDIT_RC=$?
wait
set -e
[[ $AUDIT_RC -eq 0 ]]

# Phase two finalizes and verifies the exact run created above.
(
  cd "$BOOK_ROOT"
  sha256sum "$RUN_REL/transcript.log" >> "$RUN_REL/sha256-retained.txt"
  sha256sum -c "$RUN_REL/sha256-retained.txt"
) > "$RUN_DIR/finalization.log"
grep -Fq "$RUN_REL/transcript.log: OK" "$RUN_DIR/finalization.log"
printf 'FINALIZED_RUN PASS run_dir=%s manifest=%s transcript_sha256=%s\n' \
  "$RUN_DIR" "$RUN_DIR/sha256-retained.txt" \
  "$(sha256sum "$TRANSCRIPT" | cut -d' ' -f1)" | tee -a "$RUN_DIR/finalization.log"
