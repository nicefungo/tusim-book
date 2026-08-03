#!/usr/bin/env bash
set -euo pipefail

PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
ARCHIVE_SHA=fb023fe79a0e7dafbf334848756e44127101f5fdb75c1004e2ed2712318b708f
SRC=/home/zxy/Workplace/projects/tusim
BOOK=/home/zxy/Workplace/books/tusim-book
TREE=/tmp/tusim-ch08-reproduction
TAR=/tmp/tusim-e918c80-ch08.tar
LOG="$BOOK/experiments/ch08-reproduction-2026-07-25.log"

exec > >(sed 's/[[:space:]]*$//' | tee "$LOG") 2>&1

fail() { echo "REPRODUCTION: FAIL: $*" >&2; exit 1; }
source_clean() { [[ -z "$(git -C "$SRC" status --porcelain)" ]]; }
IGNORED_BEFORE=/tmp/tusim-ch08-source-status-ignored-before.txt
IGNORED_AFTER=/tmp/tusim-ch08-source-status-ignored-after.txt

[[ "$(git -C "$SRC" rev-parse HEAD)" == "$PIN" ]] || fail "wrong Tusim revision"
[[ -z "$(git -C "$SRC" branch --show-current)" ]] || fail "Tusim is not detached"
source_clean || fail "Tusim source checkout is dirty before archive"
git -C "$SRC" status --short --ignored > "$IGNORED_BEFORE"
[[ "$(git -C "$SRC" show "$PIN:examples/gpt_block.onnx")" == "../../onnx-playground/GPT-block/gpt_block.onnx" ]] || fail "tracked external symlink contract changed"

rm -rf "$TREE" "$TAR"
git -C "$SRC" archive --format=tar --output="$TAR" "$PIN"
actual_archive_sha=$(sha256sum "$TAR" | cut -d' ' -f1)
[[ "$actual_archive_sha" == "$ARCHIVE_SHA" ]] || fail "archive hash $actual_archive_sha"
mkdir -p "$TREE"
tar -xf "$TAR" -C "$TREE"
printf '%s\n' "$PIN" > "$TREE/.chapter-source-revision"

printf 'CHAPTER=8 Floating-Point Foundations\n'
printf 'PIN=%s\nARCHIVE_SHA256=%s\nTREE=%s\n' "$PIN" "$actual_archive_sha" "$TREE"
printf 'KERNEL=%s\n' "$(uname -a)"
printf 'CC=%s\n' "$(cc --version | sed -n '1p')"
printf 'MAKE=%s\n' "$(make --version | sed -n '1p')"
printf 'PYTHON=%s\n' "$(python3 --version 2>&1)"
ldd --version | sed -n '1p'
printf 'SOURCE_IGNORED_INVENTORY_SHA256=%s\n' "$(sha256sum "$IGNORED_BEFORE" | cut -d' ' -f1)"
printf 'EXTERNAL_SYMLINK=examples/gpt_block.onnx UNUSED_BY_CH08=1\n'

python3 "$BOOK/experiments/ch08_precision_audit.py" "$TREE" "$PIN"

make -C "$TREE" clean
make -C "$TREE" libtucmodel.a

for target in test-cmodel test-config test-bf16 test-rounding test-fp8 test-tf32 test-dataflow test-golden; do
    printf '\n===== %s =====\n' "$target"
    make -C "$TREE" "$target"
done

cc -O2 -g -Wall -Wextra -std=c11 \
   -I"$TREE" -I"$TREE/tu_cmodel" \
   -o "$TREE/ch08_precision_probe" \
   "$BOOK/experiments/ch08_precision_probe.c" "$TREE/libtucmodel.a" -lm

printf '\n===== ch08_precision_probe =====\n'
"$TREE/ch08_precision_probe"

printf '\n===== static-link gates =====\n'
[[ ! -e "$TREE/libtucmodel.so" ]] || fail "unexpected Tusim shared library in archive-only build"
for binary in test-cmodel test-config test-bf16 test-rounding test-fp8 test-tf32 test-dataflow test-golden ch08_precision_probe; do
    [[ -x "$TREE/$binary" ]] || fail "missing binary $binary"
    deps=$(ldd "$TREE/$binary")
    printf '%s\n%s\n' "[$binary]" "$deps"
    ! grep -q 'libtucmodel.so' <<<"$deps" || fail "$binary resolved shared Tusim library"
done

printf '\n===== artifact hashes =====\n'
sha256sum "$TAR" \
  "$BOOK/experiments/ch08_precision_probe.c" \
  "$BOOK/experiments/ch08_precision_audit.py" \
  "$BOOK/experiments/ch08_reproduce.sh" \
  "$TREE/libtucmodel.a" \
  "$TREE/ch08_precision_probe"

[[ "$(git -C "$SRC" rev-parse HEAD)" == "$PIN" ]] || fail "source revision changed"
[[ -z "$(git -C "$SRC" branch --show-current)" ]] || fail "source no longer detached"
source_clean || fail "Tusim source checkout dirty after reproduction"
git -C "$SRC" status --short --ignored > "$IGNORED_AFTER"
cmp -s "$IGNORED_BEFORE" "$IGNORED_AFTER" || fail "ignored-file inventory changed"
echo "SOURCE_STATE: no tracked/nonignored changes; ignored inventory unchanged"

echo "REPRODUCTION: PASS"
