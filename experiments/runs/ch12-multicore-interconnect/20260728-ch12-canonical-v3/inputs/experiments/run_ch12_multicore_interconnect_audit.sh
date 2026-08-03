#!/usr/bin/env bash
set -euo pipefail

BOOK_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TUSIM_ROOT=${TUSIM_ROOT:-/home/zxy/Workplace/projects/tusim}
PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
RUN_BASE="$BOOK_ROOT/experiments/runs/ch12-multicore-interconnect"
RUN_ID=${CH12_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}
RUN_DIR="$RUN_BASE/$RUN_ID"
RUN_REL=${RUN_DIR#"$BOOK_ROOT"/}
ARCHIVE=$(mktemp /tmp/tusim-ch12-archive.XXXXXX.tar)
WORK=$(mktemp -d /tmp/tusim-ch12-work.XXXXXX)
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
    edition.yaml
    experiments/ch12_source_audit.py
    experiments/ch12_multicore_interconnect_probe.c
    experiments/run_ch12_multicore_interconnect_audit.sh
    experiments/ch12_predraft_validate.py
    experiments/ch12-multicore-interconnect-audit-2026-07-28.md
    notes/chapter-12-framing-and-evidence-plan.md
    notes/chapter-12-source-and-claim-ledger.md
    notes/chapter-12-skeptical-review-dispositions.md
    references/foundations.md
)
BUNDLED_INPUTS=()

# Canonical input commits are intentionally clean before the run. The run itself
# is the only allowed new book path during phase one.
[[ -z "$(cat "$BOOK_STATUS_BEFORE")" ]]

body() {
    section "provenance before"
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'book_root=%s\nbook_head=%s\nbook_branch=%s\nbook_remotes=0\n' \
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
    run python3 "$BOOK_ROOT/experiments/ch12_source_audit.py" "$WORK" "$PIN" \
        2>&1 | tee "$RUN_DIR/source-audit.log"
    grep -Fq "CH12_SOURCE_AUDIT PASS pin=$PIN hashes=28 predicates=149 checks=177" \
        "$RUN_DIR/source-audit.log"

    section "source-audit mutation control"
    cp "$WORK/tu_cmodel/tu_cluster.c" "$WORK/tu_cmodel/tu_cluster.c.audit-original"
    printf '\n' >> "$WORK/tu_cmodel/tu_cluster.c"
    set +e
    python3 "$BOOK_ROOT/experiments/ch12_source_audit.py" "$WORK" "$PIN" \
        > "$RUN_DIR/source-audit-mutation.log" 2>&1
    MUTATION_RC=$?
    set -e
    [[ $MUTATION_RC -ne 0 ]]
    grep -Fq "hash mismatch tu_cmodel/tu_cluster.c" "$RUN_DIR/source-audit-mutation.log"
    mv "$WORK/tu_cmodel/tu_cluster.c.audit-original" "$WORK/tu_cmodel/tu_cluster.c"
    run python3 "$BOOK_ROOT/experiments/ch12_source_audit.py" "$WORK" "$PIN" \
        >/dev/null
    printf 'SOURCE_AUDIT_MUTATION PASS rc=%s restored=yes\n' "$MUTATION_RC"

    section "contained static archive build"
    run make -C "$WORK" -j2 libtucmodel.a 2>&1 | tee "$RUN_DIR/build.log"
    ar t "$WORK/libtucmodel.a" | sort | tee "$RUN_DIR/archive-members.txt"
    for member in tu_core.o tu_cluster.o config.o; do
        grep -qx "$member" "$RUN_DIR/archive-members.txt"
        printf 'ARCHIVE_MEMBER PASS %s\n' "$member"
    done
    [[ ! -e "$WORK/libtucmodel.so" ]]

    CFLAGS=(-O2 -Wall -Wextra -std=c11 -fPIC -I"$WORK" -I"$WORK/tu_cmodel")
    run cc "${CFLAGS[@]}" -o "$WORK/ch12-probe" \
        "$BOOK_ROOT/experiments/ch12_multicore_interconnect_probe.c" "$WORK/libtucmodel.a" -lm
    run cc "${CFLAGS[@]}" -o "$WORK/ch12-test-multicore" \
        "$WORK/tests/test_multicore.c" "$WORK/libtucmodel.a" -lm
    run cc "${CFLAGS[@]}" -o "$WORK/ch12-test-config" \
        "$WORK/tests/test_config.c" "$WORK/libtucmodel.a" -lm
    run cc "${CFLAGS[@]}" -o "$WORK/ch12-contention-sweep" \
        "$WORK/tests/test_interconnect_contention_sweep.c" "$WORK/libtucmodel.a" -lm
    run cc "${CFLAGS[@]}" -o "$WORK/ch12-routing-sweep" \
        "$WORK/tests/test_interconnect_routing_sweep.c" "$WORK/libtucmodel.a" -lm

    for binary in ch12-probe ch12-test-multicore ch12-test-config ch12-contention-sweep ch12-routing-sweep; do
        if readelf -d "$WORK/$binary" | grep -q 'NEEDED.*libtucmodel'; then
            printf 'STATIC_LINK_FAIL %s\n' "$binary"
            return 1
        fi
        printf 'STATIC_LINK_PASS %s\n' "$binary"
    done

    section "focused test and mutation observation"
    run timeout 90s "$WORK/ch12-test-multicore" 2>&1 | tee "$RUN_DIR/test-multicore.log"
    grep -Fq '=== Results: 16/16 passed, 0 failed ===' "$RUN_DIR/test-multicore.log"

    python3 - "$WORK/tests/test_multicore.c" "$WORK/test_multicore_mutant.c" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text()
old = '== 15,\n          "legacy must preserve hop-only latency"'
new = '== 14,\n          "legacy must preserve hop-only latency"'
assert src.count(old) == 1
Path(sys.argv[2]).write_text(src.replace(old, new))
PY
    run cc "${CFLAGS[@]}" -o "$WORK/ch12-test-multicore-mutant" \
        "$WORK/test_multicore_mutant.c" "$WORK/libtucmodel.a" -lm
    set +e
    timeout 90s "$WORK/ch12-test-multicore-mutant" \
        > "$RUN_DIR/test-multicore-mutation.log" 2>&1
    MUTANT_RC=$?
    set -e
    [[ $MUTANT_RC -ne 0 ]]
    grep -Fq '=== Results: 15/16 passed, 1 failed ===' "$RUN_DIR/test-multicore-mutation.log"
    printf 'FOCUSED_TEST_MUTATION PASS rc=%s expected_failure=15/16\n' "$MUTANT_RC"

    section "configuration-suite qualification"
    # The exact-pin process passes its ICC parse/conversion case, then aborts in
    # a later TU-init/MMA case. Preserve that non-passing suite honestly; the
    # custom probe is the fail-closed consumer-effect gate for selected fields.
    set +e
    (ulimit -c 0; cd "$WORK" && stdbuf -o0 -e0 timeout 90s ./ch12-test-config) \
        > "$RUN_DIR/test-config.log" 2>&1
    CONFIG_RC=$?
    set -e
    [[ $CONFIG_RC -ne 0 ]]
    grep -Fq 'Config: interconnect switching parse + validation      PASS' "$RUN_DIR/test-config.log"
    grep -Fq 'Config: TU init from config + MMA' "$RUN_DIR/test-config.log"
    printf 'CONFIG_SUITE_QUALIFIED nonzero_rc=%s icc_case_passed=yes later_init_mma_case_did_not_complete=yes\n' "$CONFIG_RC"

    section "linked sweep observations"
    run timeout 60s "$WORK/ch12-contention-sweep" 2>&1 | tee "$RUN_DIR/contention-sweep.log"
    grep -Fq '16    RING  all-to-all 240   296     9256' "$RUN_DIR/contention-sweep.log"
    grep -Fq '16    MESH  all-to-all 240   286     4126' "$RUN_DIR/contention-sweep.log"
    run timeout 60s "$WORK/ch12-routing-sweep" 2>&1 | tee "$RUN_DIR/routing-sweep.log"
    grep -Fq '4   x4    top-row->left-col  XY 9     2334    2304' "$RUN_DIR/routing-sweep.log"
    grep -Fq '4   x4    left-col->bottom   YX 9     2334    2304' "$RUN_DIR/routing-sweep.log"
    grep -Fq '4   x4    all-to-all         YX 240   4126    4096' "$RUN_DIR/routing-sweep.log"

    section "fail-closed custom probe"
    run timeout 90s "$WORK/ch12-probe" 2>&1 | tee "$RUN_DIR/ch12-probe.log"
    for gate in \
        'CONFIG parsed_enabled=1 parsed_cores=8 parsed_topology=2 cluster_cores=4 cluster_topology=1 sw=2 contention=1 route=1 link=32 router=7' \
        'EQUATIONS legacy=15 cut=79 store=207' \
        'SEND blocking=0 descriptor_latency=999 stats_messages=1 stats_bytes=16 stats_cycles=15 dst_delta=15' \
        'TRAFFIC same=133 disjoint=69 ideal=69 bottleneck=128 link=0->1' \
        'HEURISTIC_COUNTEREXAMPLE isolated=94 bottleneck=128 estimated=158 shared_pair_term=133 link=0->1' \
        'ROUTES patternA_XY=606 patternA_YX=222 patternB_XY=222 patternB_YX=606' \
        'COLLECTIVES broadcast_messages=3 broadcast_bytes=24 broadcast_cycles=23 allreduce_message_delta=3 allreduce_byte_delta=36 allreduce_cycle_delta=0 barrier_delta=10 barrier_state=0' \
        'CH12_PROBE SUMMARY failures=0'; do
        grep -Fq "$gate" "$RUN_DIR/ch12-probe.log"
        printf 'EXPECTED_FINDING MATCH %s\n' "$gate"
    done

    section "retained artifact manifest phase one"
    (cd "$RUN_DIR" && sha256sum "${BUNDLED_INPUTS[@]}" \
        source-archive-sha256.txt source-audit.log source-audit-mutation.log \
        archive-members.txt input-hashes.txt build.log test-multicore.log \
        test-multicore-mutation.log test-config.log contention-sweep.log \
        routing-sweep.log ch12-probe.log) > "$RUN_DIR/sha256-retained.txt"
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
    printf 'CH12_AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS run_dir=%s\n' "$RUN_DIR"
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
