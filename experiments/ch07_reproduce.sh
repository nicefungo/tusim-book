#!/usr/bin/env bash
set -euo pipefail

PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
ARCHIVE_SHA=fb023fe79a0e7dafbf334848756e44127101f5fdb75c1004e2ed2712318b708f
BOOK=/home/zxy/Workplace/books/tusim-book
SOURCE_REPO=${1:-/home/zxy/Workplace/projects/tusim}
WORK=${2:-/tmp/tusim-ch07-reproduction}
LOG=$BOOK/experiments/ch07-reproduction-2026-07-25.log
TAR=/tmp/tusim-ch07-e918c80.tar

exec > >(tee "$LOG") 2>&1
set -x

test -z "$(git -C "$SOURCE_REPO" status --porcelain=v1)"
test "$(git -C "$SOURCE_REPO" rev-parse HEAD)" = "$PIN"
rm -rf "$WORK" "$TAR"
git -C "$SOURCE_REPO" archive --format=tar "$PIN" > "$TAR"
test "$(sha256sum "$TAR" | cut -d' ' -f1)" = "$ARCHIVE_SHA"
mkdir -p "$WORK"
tar -xf "$TAR" -C "$WORK"
printf '%s\n' "$ARCHIVE_SHA" > "$WORK/.tusim-archive-sha256"

cd "$WORK"
printf '%s\n' '=== TOOLCHAIN ==='
cc --version
make --version
ldd --version
python3 --version
uname -a

make clean
make -j2 libtucmodel.a
make test-dataflow
make test-config
make test-multicore
make test-dpi
make test-dataflow-sweep

cp "$BOOK/experiments/ch07_dataflow_probe.c" .
cc -O2 -Wall -Wextra -std=c11 -I. -Itu_cmodel \
   -o ch07_dataflow_probe ch07_dataflow_probe.c ./libtucmodel.a -lm
./ch07_dataflow_probe
python3 "$BOOK/experiments/ch07_dataflow_audit.py" . "$PIN"

printf '%s\n' '=== DYNAMIC-DEPENDENCY CHECKS ==='
for binary in test-dataflow test-config test-multicore test-dpi test-dataflow-sweep ch07_dataflow_probe; do
    deps=$(ldd "./$binary")
    printf '%s\n' "--- $binary" "$deps"
    case "$deps" in
        *libtucmodel.so*) printf 'FAIL: %s dynamically resolves libtucmodel.so\n' "$binary" >&2; exit 1 ;;
    esac
done

printf '%s\n' '=== ARTIFACT HASHES ==='
sha256sum \
    "$TAR" \
    "$BOOK/experiments/ch07_dataflow_probe.c" \
    "$BOOK/experiments/ch07_dataflow_audit.py" \
    "$BOOK/experiments/ch07_reproduce.sh" \
    libtucmodel.a test-dataflow test-config test-multicore test-dpi \
    test-dataflow-sweep ch07_dataflow_probe

test -z "$(git -C "$SOURCE_REPO" status --porcelain=v1)"
printf 'REPRODUCTION: PASS\n'
