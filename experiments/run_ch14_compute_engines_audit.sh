#!/usr/bin/env bash
set -euo pipefail

BOOK_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TUSIM_ROOT=${TUSIM_ROOT:-/home/zxy/Workplace/projects/tusim}
PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
RUN_BASE="$BOOK_ROOT/experiments/runs/ch14-compute-engines"
RUN_ID=${CH14_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}
RUN_DIR="$RUN_BASE/$RUN_ID"
RUN_REL=${RUN_DIR#"$BOOK_ROOT"/}
ARCHIVE=$(mktemp /tmp/tusim-ch14-archive.XXXXXX.tar)
WORK=$(mktemp -d /tmp/tusim-ch14-work.XXXXXX)
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
    experiments/ch14_source_audit.py
    experiments/ch14_compute_engines_probe.c
    experiments/run_ch14_compute_engines_audit.sh
    experiments/ch14_predraft_validate.py
    experiments/ch14-compute-engines-audit-2026-08-04.md
    notes/chapter-14-framing-and-evidence-plan.md
    notes/chapter-14-source-and-claim-ledger.md
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
    run python3 "$BOOK_ROOT/experiments/ch14_source_audit.py" "$WORK" "$PIN" \
        2>&1 | tee "$RUN_DIR/source-audit.log"
    grep -Fq "CH14_SOURCE_AUDIT PASS pin=$PIN hashes=28 predicates=46 checks=74" \
        "$RUN_DIR/source-audit.log"

    section "source-audit mutation control"
    cp "$WORK/tu_cmodel/compute/softmax_engine.c" "$WORK/tu_cmodel/compute/softmax_engine.c.audit-original"
    printf '\n' >> "$WORK/tu_cmodel/compute/softmax_engine.c"
    set +e
    python3 "$BOOK_ROOT/experiments/ch14_source_audit.py" "$WORK" "$PIN" \
        > "$RUN_DIR/source-audit-mutation.log" 2>&1
    MUTATION_RC=$?
    set -e
    [[ $MUTATION_RC -ne 0 ]]
    grep -Fq "hash mismatch tu_cmodel/compute/softmax_engine.c" "$RUN_DIR/source-audit-mutation.log"
    mv "$WORK/tu_cmodel/compute/softmax_engine.c.audit-original" "$WORK/tu_cmodel/compute/softmax_engine.c"
    run python3 "$BOOK_ROOT/experiments/ch14_source_audit.py" "$WORK" "$PIN" \
        >/dev/null
    printf 'SOURCE_AUDIT_MUTATION PASS rc=%s restored=yes\n' "$MUTATION_RC"

    section "contained static archive build"
    run make -C "$WORK" -j2 libtucmodel.a 2>&1 | tee "$RUN_DIR/build.log"
    ar t "$WORK/libtucmodel.a" | sort | tee "$RUN_DIR/archive-members.txt"
    for member in convolution_engine.o softmax_engine.o attention_engine.o \
                  normalization_engine.o pooling_engine.o elementwise_pipeline.o \
                  pipeline_controller.o; do
        grep -qx "$member" "$RUN_DIR/archive-members.txt"
        printf 'ARCHIVE_MEMBER PASS %s\n' "$member"
    done
    [[ ! -e "$WORK/libtucmodel.so" ]]

    CFLAGS=(-O2 -Wall -Wextra -std=c11 -fPIC -I"$WORK" -I"$WORK/tu_cmodel")
    run cc "${CFLAGS[@]}" -o "$WORK/ch14-probe" \
        "$BOOK_ROOT/experiments/ch14_compute_engines_probe.c" "$WORK/libtucmodel.a" -lm
    for t in elementwise normalization convolution attention pooling pipeline softmax; do
        run cc "${CFLAGS[@]}" -o "$WORK/ch14-test-$t" \
            "$WORK/tests/test_$t.c" "$WORK/libtucmodel.a" -lm
    done

    for binary in ch14-probe ch14-test-elementwise ch14-test-normalization \
                  ch14-test-convolution ch14-test-attention ch14-test-pooling \
                  ch14-test-pipeline ch14-test-softmax; do
        if readelf -d "$WORK/$binary" | grep -q 'NEEDED.*libtucmodel'; then
            printf 'STATIC_LINK_FAIL %s\n' "$binary"
            return 1
        fi
        printf 'STATIC_LINK_PASS %s\n' "$binary"
    done

    section "engine focused suites (six green, attention qualified)"
    run timeout 90s "$WORK/ch14-test-elementwise" 2>&1 | tee "$RUN_DIR/test-elementwise.log"
    grep -Fq '16/16 tests passed' "$RUN_DIR/test-elementwise.log"
    run timeout 90s "$WORK/ch14-test-normalization" 2>&1 | tee "$RUN_DIR/test-normalization.log"
    grep -Fq '11/11 tests passed' "$RUN_DIR/test-normalization.log"
    run timeout 90s "$WORK/ch14-test-convolution" 2>&1 | tee "$RUN_DIR/test-convolution.log"
    grep -Fq '12/12 tests passed' "$RUN_DIR/test-convolution.log"
    run timeout 90s "$WORK/ch14-test-pooling" 2>&1 | tee "$RUN_DIR/test-pooling.log"
    grep -Fq '14/14 tests passed' "$RUN_DIR/test-pooling.log"
    run timeout 90s "$WORK/ch14-test-pipeline" 2>&1 | tee "$RUN_DIR/test-pipeline.log"
    grep -Fq 'Results: 11/11 passed' "$RUN_DIR/test-pipeline.log"

    # Attention: the SRAM access-width defect (4-byte copies on 2-byte FP16)
    # makes the suite fail 7/9 or 8/9 depending on UB stack garbage. Gate the
    # invariants: rc=1, at least one FAIL, never 9/9. Never present as green.
    set +e
    timeout 90s "$WORK/ch14-test-attention" > "$RUN_DIR/test-attention.log" 2>&1
    ATTN_RC=$?
    set -e
    [[ $ATTN_RC -eq 1 ]]
    grep -Eq '[1-8]/9 tests passed' "$RUN_DIR/test-attention.log"
    grep -Fq 'FAIL' "$RUN_DIR/test-attention.log"
    ! grep -Fq '9/9 tests passed' "$RUN_DIR/test-attention.log"
    ATTN_COUNT=$(grep -Eo '[1-8]/9 tests passed' "$RUN_DIR/test-attention.log" | head -1)
    printf 'ATTENTIONSUITEQUALIFIED PASS rc=%s summary=%s failing_subset_ub_dependent=yes\n' \
        "$ATTN_RC" "$ATTN_COUNT"

    section "softmax standalone suite (make test excludes it)"
    run timeout 90s "$WORK/ch14-test-softmax" 2>&1 | tee "$RUN_DIR/test-softmax.log"
    grep -Fq '=== Results: 15/15 passed, 0 failed ===' "$RUN_DIR/test-softmax.log"

    section "focused-test mutation observation"
    python3 - "$WORK/tests/test_softmax.c" "$WORK/test_softmax_mutant.c" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text()
old = 'ASSERT_FLOAT_EQ(output[i], 0.25f, 1e-6f, "zeros -> 1/N")'
new = 'ASSERT_FLOAT_EQ(output[i], 0.5f, 1e-6f, "zeros -> 1/N")'
assert src.count(old) == 1
Path(sys.argv[2]).write_text(src.replace(old, new))
PY
    run cc "${CFLAGS[@]}" -o "$WORK/ch14-test-softmax-mutant" \
        "$WORK/test_softmax_mutant.c" "$WORK/libtucmodel.a" -lm
    set +e
    timeout 90s "$WORK/ch14-test-softmax-mutant" \
        > "$RUN_DIR/test-softmax-mutation.log" 2>&1
    MUTANT_RC=$?
    set -e
    [[ $MUTANT_RC -ne 0 ]]
    grep -Fq '=== Results: 14/15 passed, 1 failed ===' "$RUN_DIR/test-softmax-mutation.log"
    printf 'FOCUSED_TEST_MUTATION PASS rc=%s expected_failure=14/15\n' "$MUTANT_RC"

    section "fail-closed custom probe"
    run timeout 90s "$WORK/ch14-probe" 2>&1 | tee "$RUN_DIR/ch14-probe.log"
    for gate in \
        'CH14_PROBE start' \
        'CONV dims oh=3 ow=3 im2col_rows=3 im2col_cols=9' \
        'CONV direct out00=6.000000 out01=6.000000 out10=6.000000 out11=6.000000' \
        'CONV im2col_gemm out00=6.000000 out01=6.000000 out10=6.000000 out11=6.000000' \
        'CONV estimate_cycles=69' \
        'SOFTMAX zeros 0.250000 0.250000 0.250000 0.250000 max=0.000000 stall=8' \
        'SOFTMAX census40 stall=96' \
        'SOFTMAX invalid=18446744073709551615' \
        'NORM layernorm 0.000000 0.000000 0.000000 0.000000 mean=1.000000 var=0.000000 stall=8' \
        'NORM rmsnorm 0.999995 0.999995 0.999995 0.999995 var=1.000000 stall=8' \
        'NORM census40 stall=80' \
        'EW chain 0.000000 3.000000 7.000000 stall=2' \
        'EW census40 stall=40' \
        'POOL max 6.000000 8.000000 14.000000 16.000000 cycles=18' \
        'POOL avg 3.500000 5.500000 11.500000 13.500000 cycles=34' \
        'ATTN tiny rc=0 out=0.099976 0.199951 dma=16 tiles=2 flops=8 cc=145 dc=2 tc=147 u=0.9864' \
        'ATTN corrupt 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000' \
        'ATTN diff golden_err=' \
        'deviates=1 scales_equal=1' \
        'PIPE depth1 sequential_total=204 saved=0 stalls=0' \
        'PIPE depth2 sequential_total=402 saved=200 stalls=0 active=0' \
        'CH14_PROBE SUMMARY failures=0'; do
        grep -Fq "$gate" "$RUN_DIR/ch14-probe.log"
        printf 'EXPECTED_FINDING MATCH %s\n' "$gate"
    done

    section "retained artifact manifest phase one"
    (cd "$RUN_DIR" && sha256sum "${BUNDLED_INPUTS[@]}" \
        source-archive-sha256.txt source-audit.log source-audit-mutation.log \
        archive-members.txt input-hashes.txt build.log test-elementwise.log \
        test-normalization.log test-convolution.log test-attention.log \
        test-pooling.log test-pipeline.log test-softmax.log \
        test-softmax-mutation.log ch14-probe.log) > "$RUN_DIR/sha256-retained.txt"
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
    printf 'CH14_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS run_dir=%s\n' "$RUN_DIR"
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

CH14_RUN_ID="$RUN_ID" python3 "$BOOK_ROOT/experiments/ch14_predraft_validate.py" \
    | tee "$RUN_DIR/predraft-validation.log"
grep -Fq "CH14_PREDRAFT_VALIDATION PASS" "$RUN_DIR/predraft-validation.log"

(cd "$RUN_DIR" && \
    sha256sum sha256-retained.txt finalization.log predraft-validation.log \
        > bundle-sha256.txt && \
    sha256sum -c bundle-sha256.txt)
printf 'BUNDLE_FINALIZED PASS run_dir=%s outer_manifest=%s\n' \
    "$RUN_DIR" "$RUN_DIR/bundle-sha256.txt"
