#!/usr/bin/env bash
set -euo pipefail

BOOK_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TUSIM_ROOT=${TUSIM_ROOT:-/home/zxy/Workplace/projects/tusim}
PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
RUN_BASE="$BOOK_ROOT/experiments/runs/ch13-weight-streams"
RUN_ID=${CH13_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}
RUN_DIR="$RUN_BASE/$RUN_ID"
RUN_REL=${RUN_DIR#"$BOOK_ROOT"/}
ARCHIVE=$(mktemp /tmp/tusim-ch13-archive.XXXXXX.tar)
WORK=$(mktemp -d /tmp/tusim-ch13-work.XXXXXX)
IGNORED_BEFORE=$(mktemp)
IGNORED_AFTER=$(mktemp)
BOOK_STATUS_BEFORE=$(mktemp)
BOOK_STATUS_AFTER=$(mktemp)
REMOTE_BEFORE=$(mktemp)
REMOTE_AFTER=$(mktemp)
TRANSCRIPT="$RUN_DIR/transcript.log"

cleanup() {
    rc=$?
    rm -f "$ARCHIVE" "$IGNORED_BEFORE" "$IGNORED_AFTER" \
        "$BOOK_STATUS_BEFORE" "$BOOK_STATUS_AFTER" "$REMOTE_BEFORE" "$REMOTE_AFTER"
    rm -rf "$WORK"
    trap - EXIT
    exit "$rc"
}
trap cleanup EXIT

run() {
    printf '+ '
    printf '%q ' "$@"
    printf '\n'
    "$@"
}
section() { printf '\n===== %s =====\n' "$*"; }

TUSIM_HEAD=$(git -C "$TUSIM_ROOT" rev-parse HEAD)
TUSIM_BRANCH=$(git -C "$TUSIM_ROOT" symbolic-ref -q --short HEAD || true)
TUSIM_STATUS=$(git -C "$TUSIM_ROOT" status --porcelain=v1 --untracked-files=all)
BOOK_HEAD=$(git -C "$BOOK_ROOT" rev-parse HEAD)
BOOK_BRANCH=$(git -C "$BOOK_ROOT" branch --show-current)
[[ "$TUSIM_HEAD" == "$PIN" && -z "$TUSIM_BRANCH" && -z "$TUSIM_STATUS" ]]
# The book now has a configured remote (origin -> github.com-tusim/tusim-book).
# The run asserts the remote set is unchanged and never pushes.
git -C "$BOOK_ROOT" remote -v > "$REMOTE_BEFORE"
grep -q 'github.com-tusim' "$REMOTE_BEFORE"
grep -q 'tusim-book.git' "$REMOTE_BEFORE"
[[ "$BOOK_BRANCH" == "main" ]]
[[ ! -e "$RUN_DIR" ]]
mkdir -p "$RUN_BASE"
mkdir "$RUN_DIR"
git -C "$BOOK_ROOT" status --porcelain=v1 --untracked-files=all > "$BOOK_STATUS_BEFORE"

INPUTS=(
    edition.yaml
    experiments/ch13_source_audit.py
    experiments/ch13_weight_stream_probe.c
    experiments/run_ch13_weight_stream_audit.sh
    experiments/ch13_predraft_validate.py
    experiments/ch13-weight-streams-audit-2026-08-03.md
    notes/chapter-13-framing-and-evidence-plan.md
    notes/chapter-13-source-and-claim-ledger.md
    references/foundations.md
)
BUNDLED_INPUTS=()

# Canonical input commits are intentionally clean before the run. The run itself
# is the only allowed new book path during phase one.
[[ -z "$(cat "$BOOK_STATUS_BEFORE")" ]]

body() {
    section "provenance before"
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'book_root=%s\nbook_head=%s\nbook_branch=%s\n' \
        "$BOOK_ROOT" "$BOOK_HEAD" "$BOOK_BRANCH"
    printf 'tusim_root=%s\ntusim_head=%s\ntusim_branch=DETACHED\ntusim_status_bytes=%s\n' \
        "$TUSIM_ROOT" "$TUSIM_HEAD" "${#TUSIM_STATUS}"
    git -C "$TUSIM_ROOT" status --ignored --porcelain=v1 --untracked-files=all > "$IGNORED_BEFORE"
    printf 'tusim_ignored_inventory_sha256=%s\n' \
        "$(sha256sum "$IGNORED_BEFORE" | cut -d' ' -f1)"

    section "create pinned disposable source"
    run git -C "$TUSIM_ROOT" archive --format=tar --output="$ARCHIVE" "$PIN"
    printf '%s  source-at-pin.tar\n' "$(sha256sum "$ARCHIVE" | cut -d' ' -f1)" \
        | tee "$RUN_DIR/source-archive-sha256.txt"
    run tar -xf "$ARCHIVE" -C "$WORK"

    section "source and artifact input hashes"
    (cd "$BOOK_ROOT" && sha256sum "${INPUTS[@]}") | tee "$RUN_DIR/input-hashes.txt"
    for rel in "${INPUTS[@]}"; do
        mkdir -p "$RUN_DIR/inputs/$(dirname "$rel")"
        cp "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel"
        BUNDLED_INPUTS+=("inputs/$rel")
    done

    section "fail-closed source audit"
    run python3 "$BOOK_ROOT/experiments/ch13_source_audit.py" "$WORK" "$PIN" \
        2>&1 | tee "$RUN_DIR/source-audit.log"
    grep -Fq "CH13_SOURCE_AUDIT PASS pin=$PIN hashes=25 predicates=138 checks=163" \
        "$RUN_DIR/source-audit.log"

    section "source-audit mutation control"
    cp "$WORK/tu_cmodel/memory/weight_compress.c" "$WORK/tu_cmodel/memory/weight_compress.c.audit-original"
    printf '\n' >> "$WORK/tu_cmodel/memory/weight_compress.c"
    set +e
    python3 "$BOOK_ROOT/experiments/ch13_source_audit.py" "$WORK" "$PIN" \
        > "$RUN_DIR/source-audit-mutation.log" 2>&1
    MUTATION_RC=$?
    set -e
    [[ $MUTATION_RC -ne 0 ]]
    grep -Fq "hash mismatch tu_cmodel/memory/weight_compress.c" "$RUN_DIR/source-audit-mutation.log"
    mv "$WORK/tu_cmodel/memory/weight_compress.c.audit-original" "$WORK/tu_cmodel/memory/weight_compress.c"
    run python3 "$BOOK_ROOT/experiments/ch13_source_audit.py" "$WORK" "$PIN" \
        >/dev/null
    printf 'SOURCE_AUDIT_MUTATION PASS rc=%s restored=yes\n' "$MUTATION_RC"

    section "contained static archive build"
    run make -C "$WORK" -j2 libtucmodel.a 2>&1 | tee "$RUN_DIR/build.log"
    ar t "$WORK/libtucmodel.a" | sort | tee "$RUN_DIR/archive-members.txt"
    for member in tu_int_quant.o structured_2of4.o weight_compress.o; do
        grep -qx "$member" "$RUN_DIR/archive-members.txt"
        printf 'ARCHIVE_MEMBER PASS %s\n' "$member"
    done
    [[ ! -e "$WORK/libtucmodel.so" ]]

    CFLAGS=(-O2 -Wall -Wextra -std=c11 -fPIC -I"$WORK" -I"$WORK/tu_cmodel")
    run cc "${CFLAGS[@]}" -o "$WORK/ch13-probe" \
        "$BOOK_ROOT/experiments/ch13_weight_stream_probe.c" "$WORK/libtucmodel.a" -lm
    run cc "${CFLAGS[@]}" -o "$WORK/ch13-test-int-quant" \
        "$WORK/tests/test_int_quant.c" "$WORK/libtucmodel.a" -lm
    run cc "${CFLAGS[@]}" -o "$WORK/ch13-test-sparsity" \
        "$WORK/tests/test_sparsity.c" "$WORK/libtucmodel.a" -lm
    run cc "${CFLAGS[@]}" -o "$WORK/ch13-test-compress" \
        "$WORK/tests/test_compress.c" "$WORK/libtucmodel.a" -lm
    run cc "${CFLAGS[@]}" -o "$WORK/ch13-weight-sweep" \
        "$WORK/tests/test_weight_compression_sweep.c" "$WORK/libtucmodel.a" -lm
    run cc "${CFLAGS[@]}" -o "$WORK/ch13-sparsity-sweep" \
        "$WORK/tests/test_sparsity_sweep.c" "$WORK/libtucmodel.a" -lm

    for binary in ch13-probe ch13-test-int-quant ch13-test-sparsity ch13-test-compress \
                  ch13-weight-sweep ch13-sparsity-sweep; do
        if readelf -d "$WORK/$binary" | grep -q 'NEEDED.*libtucmodel'; then
            printf 'STATIC_LINK_FAIL %s\n' "$binary"
            return 1
        fi
        printf 'STATIC_LINK_PASS %s\n' "$binary"
    done

    section "focused test and mutation observation"
    run timeout 90s "$WORK/ch13-test-int-quant" 2>&1 | tee "$RUN_DIR/test-int-quant.log"
    grep -Fq '14/14 tests passed' "$RUN_DIR/test-int-quant.log"
    run timeout 90s "$WORK/ch13-test-sparsity" 2>&1 | tee "$RUN_DIR/test-sparsity.log"
    grep -Fq 'Tests: 27 run, 27 passed, 0 failed' "$RUN_DIR/test-sparsity.log"
    run timeout 90s "$WORK/ch13-test-compress" 2>&1 | tee "$RUN_DIR/test-compress.log"
    grep -Fq '24/24 tests passed' "$RUN_DIR/test-compress.log"

    # Mutate one discriminating sparsity assertion: decoder bottleneck must be a
    # strict comparison; flipping it must fail.
    python3 - "$WORK/tests/test_sparsity.c" "$WORK/test_sparsity_mutant.c" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text()
old = 'slow.sparse_total_cycles > fast.sparse_total_cycles'
new = 'slow.sparse_total_cycles < fast.sparse_total_cycles'
assert src.count(old) == 1
Path(sys.argv[2]).write_text(src.replace(old, new))
PY
    run cc "${CFLAGS[@]}" -o "$WORK/ch13-test-sparsity-mutant" \
        "$WORK/test_sparsity_mutant.c" "$WORK/libtucmodel.a" -lm
    set +e
    timeout 90s "$WORK/ch13-test-sparsity-mutant" \
        > "$RUN_DIR/test-sparsity-mutation.log" 2>&1
    MUTANT_RC=$?
    set -e
    [[ $MUTANT_RC -ne 0 ]]
    grep -Fq 'Tests: 26 run, 25 passed, 1 failed' "$RUN_DIR/test-sparsity-mutation.log"
    printf 'FOCUSED_TEST_MUTATION PASS rc=%s expected_failure=26/27\n' "$MUTANT_RC"

    section "linked sweep observations"
    run timeout 90s "$WORK/ch13-weight-sweep" 2>&1 | tee "$RUN_DIR/weight-sweep.log"
    grep -Fq 'workload             profile  outW rleW bmpW' "$RUN_DIR/weight-sweep.log"
    grep -Fq 'alternating' "$RUN_DIR/weight-sweep.log"
    run timeout 90s "$WORK/ch13-sparsity-sweep" 2>&1 | tee "$RUN_DIR/sparsity-sweep.log"
    grep -Fq 'Dense vs 2:4 Structured Sparsity Sweep' "$RUN_DIR/sparsity-sweep.log"
    grep -Fq 'small projection' "$RUN_DIR/sparsity-sweep.log"

    section "fail-closed custom probe"
    run timeout 90s "$WORK/ch13-probe" 2>&1 | tee "$RUN_DIR/ch13-probe.log"
    for gate in \
        'INTQ default_scale=0.007874016 default_zp=0 qmin=-128 qmax=127' \
        'INTQ sym_calib scale=1.000000000 zp=0' \
        'INTQ nibble byte=0x5A low=10 high=5' \
        'INTQ dot=32' \
        'INTQ mma o00=19 o01=22 o10=43 o11=50' \
        'SPARSITY valid_masks=6' \
        'SPARSITY prune groups=2 masks=0x5,0x9' \
        'SPARSITY packed_fp16_128=160' \
        'SPARSITY est128 dense_total=12291 sparse_total=7811 selected=7811 macs=2097152/1048576 wbytes=32768/20480 decode=4096' \
        'SPARSITY estNarrow dense_total=34307 sparse_total=77312 decode=65536' \
        'SPARSITY estWide sparse_total=19971 decode=4096' \
        'COMPRESS rle_allzero_size=14' \
        'COMPRESS rle_alt_size=776 raw=256' \
        'COMPRESS bitmap_size=110 nnz=43' \
        'COMPRESS adaptive_sparse_codec=2 size=126' \
        'COMPRESS corrupt_rejected=1' \
        'COMPRESS est_rle dma=1 decode=128 total=128 bound=1' \
        'COMPRESS est_wide decode=8 total=8' \
        'COMPRESS est_serial total=9' \
        'COMPRESS cfgmap type=4 enabled=1 decoder=1' \
        'CONFIG parsed compression=1 type=4 decoder=1 sparsity=1 two4=1 decgroups=4' \
        'CONFIG validation rejections=4' \
        'CONFIG runtime pe_rows=16 pe_cols=16 dma_bits=256' \
        'CH13_PROBE SUMMARY failures=0'; do
        grep -Fq "$gate" "$RUN_DIR/ch13-probe.log"
        printf 'EXPECTED_FINDING MATCH %s\n' "$gate"
    done

    section "retained artifact manifest phase one"
    (cd "$RUN_DIR" && sha256sum "${BUNDLED_INPUTS[@]}" \
        source-archive-sha256.txt source-audit.log source-audit-mutation.log \
        archive-members.txt input-hashes.txt build.log test-int-quant.log \
        test-sparsity.log test-compress.log test-sparsity-mutation.log \
        weight-sweep.log sparsity-sweep.log ch13-probe.log) > "$RUN_DIR/sha256-retained.txt"
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
    git -C "$BOOK_ROOT" remote -v > "$REMOTE_AFTER"
    cmp "$REMOTE_BEFORE" "$REMOTE_AFTER"
    (cd "$BOOK_ROOT" && sha256sum -c "$RUN_REL/input-hashes.txt")
    git -C "$BOOK_ROOT" status --porcelain=v1 --untracked-files=all \
        | grep -v -F "?? $RUN_REL/" > "$BOOK_STATUS_AFTER" || true
    cmp "$BOOK_STATUS_BEFORE" "$BOOK_STATUS_AFTER"
    printf 'BOOK_POST PASS head=%s branch=%s inputs_unchanged=yes status_unchanged_outside_run=yes remote_unchanged=yes no_push_performed=yes\n' \
        "$BOOK_HEAD" "$BOOK_BRANCH"

    section "result"
    printf 'CH13_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS run_dir=%s\n' "$RUN_DIR"
}

set +e
body > >(tee "$TRANSCRIPT") 2>&1
AUDIT_RC=$?
wait
set -e
[[ $AUDIT_RC -eq 0 ]]

(cd "$RUN_DIR" && sha256sum transcript.log >> sha256-retained.txt && \
    sha256sum -c sha256-retained.txt) > "$RUN_DIR/finalization.log"
grep -Fq 'transcript.log: OK' "$RUN_DIR/finalization.log"
printf 'FINALIZED_RUN PASS run_dir=%s manifest=%s transcript_sha256=%s\n' \
    "$RUN_DIR" "$RUN_DIR/sha256-retained.txt" \
    "$(sha256sum "$TRANSCRIPT" | cut -d' ' -f1)" | tee -a "$RUN_DIR/finalization.log"

CH13_RUN_ID="$RUN_ID" python3 "$BOOK_ROOT/experiments/ch13_predraft_validate.py" \
    | tee "$RUN_DIR/predraft-validation.log"
grep -Fq "CH13_PREDRAFT_VALIDATION PASS" "$RUN_DIR/predraft-validation.log"

(cd "$RUN_DIR" && \
    sha256sum sha256-retained.txt finalization.log predraft-validation.log \
        > bundle-sha256.txt && \
    sha256sum -c bundle-sha256.txt)
printf 'BUNDLE_FINALIZED PASS run_dir=%s outer_manifest=%s\n' \
    "$RUN_DIR" "$RUN_DIR/bundle-sha256.txt"
