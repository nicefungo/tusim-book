#!/usr/bin/env bash
set -euo pipefail

BOOK_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TUSIM_ROOT=${TUSIM_ROOT:-/home/zxy/Workplace/projects/tusim}
PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
RUN_BASE="$BOOK_ROOT/experiments/runs/ch11-instruction-contracts"
RUN_ID=${CH11_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}
RUN_DIR="$RUN_BASE/$RUN_ID"
RUN_REL=${RUN_DIR#"$BOOK_ROOT"/}
ARCHIVE=$(mktemp /tmp/tusim-ch11-archive.XXXXXX.tar)
WORK=$(mktemp -d /tmp/tusim-ch11-work.XXXXXX)
IGNORED_BEFORE=$(mktemp)
IGNORED_AFTER=$(mktemp)
BOOK_STATUS_BEFORE=$(mktemp)
BOOK_STATUS_AFTER=$(mktemp)
TRANSCRIPT="$RUN_DIR/transcript.log"

cleanup() {
    rc=$?
    rm -f "$ARCHIVE" "$IGNORED_BEFORE" "$IGNORED_AFTER" \
        "$BOOK_STATUS_BEFORE" "$BOOK_STATUS_AFTER"
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

# Fail provenance before creating durable evidence.
TUSIM_HEAD=$(git -C "$TUSIM_ROOT" rev-parse HEAD)
TUSIM_BRANCH=$(git -C "$TUSIM_ROOT" symbolic-ref -q --short HEAD || true)
TUSIM_STATUS=$(git -C "$TUSIM_ROOT" status --porcelain=v1 --untracked-files=all)
BOOK_HEAD=$(git -C "$BOOK_ROOT" rev-parse HEAD)
BOOK_BRANCH=$(git -C "$BOOK_ROOT" branch --show-current)
BOOK_REMOTES=$(git -C "$BOOK_ROOT" remote)
[[ "$TUSIM_HEAD" == "$PIN" && -z "$TUSIM_BRANCH" && -z "$TUSIM_STATUS" ]]
[[ -z "$BOOK_REMOTES" ]]
[[ ! -e "$RUN_DIR" ]]
mkdir -p "$RUN_BASE"
mkdir "$RUN_DIR"
git -C "$BOOK_ROOT" status --porcelain=v1 --untracked-files=all > "$BOOK_STATUS_BEFORE"

INPUTS=(
    experiments/ch11_source_audit.py
    experiments/ch11_instruction_contract_probe.c
    experiments/run_ch11_instruction_contract_audit.sh
    experiments/ch11_predraft_validate.py
    experiments/ch11-instruction-contract-audit-2026-07-28.md
    notes/chapter-11-framing-and-evidence-plan.md
    notes/chapter-11-source-and-claim-ledger.md
    notes/chapter-11-skeptical-review-dispositions.md
    references/foundations.md
)
BUNDLED_INPUTS=()

# Phase one is the complete audit transcript.
audit_body() {
    section "provenance before"
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'book_root=%s\nbook_head=%s\nbook_branch=%s\nbook_remotes=0\n' \
        "$BOOK_ROOT" "$BOOK_HEAD" "$BOOK_BRANCH"
    printf '%s\n' 'BOOK_STATUS_BEFORE_BEGIN'
    cat "$BOOK_STATUS_BEFORE"
    printf '%s\n' 'BOOK_STATUS_BEFORE_END'
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
    (
        cd "$BOOK_ROOT"
        sha256sum "${INPUTS[@]}"
    ) | tee "$RUN_DIR/input-hashes.txt"
    for rel in "${INPUTS[@]}"; do
        mkdir -p "$RUN_DIR/inputs/$(dirname "$rel")"
        cp "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel"
        BUNDLED_INPUTS+=("inputs/$rel")
    done

    section "fail-closed source audit"
    run python3 "$BOOK_ROOT/experiments/ch11_source_audit.py" "$WORK" "$PIN" \
        2>&1 | tee "$RUN_DIR/source-audit.log"
    grep -Fq "CH11_SOURCE_AUDIT PASS pin=$PIN hashes=26 predicates=96 checks=122" \
        "$RUN_DIR/source-audit.log"

    section "contained static archive build"
    # The archive extraction is clean. Do not invoke the pinned Makefile's clean
    # target: it removes process-global /tmp paths outside the extraction.
    run make -C "$WORK" -j2 libtucmodel.a
    ar t "$WORK/libtucmodel.a" | sort | tee "$RUN_DIR/archive-members.txt"
    for member in command_queue.o tu_asm.o tu_isa.o tu_scheduler.o; do
        grep -qx "$member" "$RUN_DIR/archive-members.txt"
        printf 'ARCHIVE_MEMBER PASS %s\n' "$member"
    done
    [[ ! -e "$WORK/libtucmodel.so" ]]

    CFLAGS=(-O2 -Wall -Wextra -std=c11 -fPIC -I"$WORK" -I"$WORK/tu_cmodel")
    run cc "${CFLAGS[@]}" -o "$WORK/ch11-probe" \
        "$BOOK_ROOT/experiments/ch11_instruction_contract_probe.c" "$WORK/libtucmodel.a" -lm
    run cc "${CFLAGS[@]}" -o "$WORK/ch11-test-cmdq" \
        "$WORK/tests/test_command_queue.c" "$WORK/libtucmodel.a" -lm
    run cc "${CFLAGS[@]}" -o "$WORK/ch11-test-isa" \
        "$WORK/tests/test_isa.c" "$WORK/libtucmodel.a" -lm
    run cc "${CFLAGS[@]}" -o "$WORK/ch11-test-asm" \
        "$WORK/tests/test_asm.c" "$WORK/libtucmodel.a" -lm
    run cc "${CFLAGS[@]}" -o "$WORK/ch11-test-scheduler" \
        "$WORK/tests/test_scheduler.c" "$WORK/libtucmodel.a" -lm

    for binary in ch11-probe ch11-test-cmdq ch11-test-isa ch11-test-asm ch11-test-scheduler; do
        if readelf -d "$WORK/$binary" | grep -q 'NEEDED.*libtucmodel'; then
            printf 'STATIC_LINK_FAIL %s\n' "$binary"
            return 1
        fi
        printf 'STATIC_LINK_PASS %s\n' "$binary"
    done

    section "focused harness observations"
    run timeout 30s "$WORK/ch11-test-cmdq" 2>&1 | tee "$RUN_DIR/test-cmdq.log"
    grep -Fq '9/9 tests passed' "$RUN_DIR/test-cmdq.log"
    run timeout 30s "$WORK/ch11-test-isa" 2>&1 | tee "$RUN_DIR/test-isa.log"
    grep -Fq 'Results: 9/9 passed' "$RUN_DIR/test-isa.log"
    run timeout 30s "$WORK/ch11-test-asm" 2>&1 | tee "$RUN_DIR/test-asm.log"
    grep -Fq 'identity smoke test: PASS' "$RUN_DIR/test-asm.log"
    run timeout 30s "$WORK/ch11-test-scheduler" 2>&1 | tee "$RUN_DIR/test-scheduler.log"
    grep -Fq 'Results: 14/14 passed' "$RUN_DIR/test-scheduler.log"
    printf '%s\n' 'HARNESS_QUALIFICATION focused passes do not certify cross-surface integration or the adversarial lifecycle cases.'

    section "fail-closed custom probe"
    run timeout 30s "$WORK/ch11-probe" 2>&1 | tee "$RUN_DIR/ch11-probe.log"
    for gate in \
        'ISA sizeof=12 opcode_count_sentinel=128 named_slots=68 unknown_slots=60' \
        'SYNC_QUEUE count=4 submitted=4 completed=3 faulted=1 signal_count=0 current_cycle=0' \
        'RESET_IDS old_cmd=1 new_cmd=1 old_signal=1 new_signal=5' \
        'ASYNC_QUEUE count=2 submitted=2 completed=2 faulted=0 signal_count=0 current_cycle=3' \
        'ASYNC_BARRIER fault=3 pre=0 barrier=2 post=2 count=4 cycle=6' \
        'ELEMENTWISE_BOUNDARY count=9 status=2 completed=1 faulted=0' \
        'SCHED_BARRIER output=DMA.LOAD,NOP,BARRIER valid=1 hoisted=0 inserted=0 cycles=9' \
        'SCHED_POSITIVE_INSERT direct=1 run=0 input_nodes=2 output_nodes=2' \
        'SCHED_POSITIVE_HOIST direct=1 run=0 input_nodes=3 output_nodes=3' \
        'SCHED_DENSE_BARRIER prior=17 retained_preds=16 max_deps=16' \
        'ASM expanded_mnemonic_rc=-1' \
        'CH11_PROBE SUMMARY failures=0'; do
        grep -Fq "$gate" "$RUN_DIR/ch11-probe.log"
        printf 'EXPECTED_FINDING MATCH %s\n' "$gate"
    done

    section "retained artifact manifest phase one"
    (
        cd "$RUN_DIR"
        sha256sum "${BUNDLED_INPUTS[@]}" \
            source-archive-sha256.txt \
            source-audit.log \
            archive-members.txt \
            input-hashes.txt \
            test-cmdq.log \
            test-isa.log \
            test-asm.log \
            test-scheduler.log \
            ch11-probe.log
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
    printf 'BOOK_POST PASS head=%s branch=%s inputs_unchanged=yes status_unchanged_outside_run=yes remotes=0\n' \
        "$BOOK_HEAD" "$BOOK_BRANCH"

    section "result"
    printf 'CH11_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS run_dir=%s\n' "$RUN_DIR"
}

set +e
audit_body > >(tee "$TRANSCRIPT") 2>&1
AUDIT_RC=$?
wait
set -e
[[ $AUDIT_RC -eq 0 ]]

# Phase two hashes the now-closed transcript and verifies the exact run.
(
    cd "$RUN_DIR"
    sha256sum transcript.log >> sha256-retained.txt
    sha256sum -c sha256-retained.txt
) > "$RUN_DIR/finalization.log"
grep -Fq "transcript.log: OK" "$RUN_DIR/finalization.log"
printf 'FINALIZED_RUN PASS run_dir=%s manifest=%s transcript_sha256=%s\n' \
    "$RUN_DIR" "$RUN_DIR/sha256-retained.txt" \
    "$(sha256sum "$TRANSCRIPT" | cut -d' ' -f1)" | tee -a "$RUN_DIR/finalization.log"
