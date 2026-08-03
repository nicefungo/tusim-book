#!/usr/bin/env bash
set -euo pipefail
PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
ARCHIVE_SHA=fb023fe79a0e7dafbf334848756e44127101f5fdb75c1004e2ed2712318b708f
SRC=${TUSIM_SRC:-/home/zxy/Workplace/projects/tusim}
BOOK=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TREE=${CH09_TREE:-/tmp/tusim-ch09-reproduction}
TAR=${CH09_TAR:-/tmp/tusim-e918c80-ch09.tar}
LOG=${CH09_LOG:-"$BOOK/experiments/ch09-reproduction-2026-07-26.log"}
exec > >(sed 's/[[:space:]]*$//' | tee "$LOG") 2>&1
fail(){ echo "REPRODUCTION: FAIL: $*" >&2; exit 1; }
clean(){ [[ -z "$(git -C "$SRC" status --porcelain)" ]]; }
BEFORE=/tmp/tusim-ch09-ignored-before.txt; AFTER=/tmp/tusim-ch09-ignored-after.txt
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$PIN" ]] || fail revision
[[ -z "$(git -C "$SRC" branch --show-current)" ]] || fail detached
clean || fail "source dirty before"
git -C "$SRC" status --short --ignored > "$BEFORE"
rm -rf "$TREE" "$TAR"
git -C "$SRC" archive --format=tar --output="$TAR" "$PIN"
sha=$(sha256sum "$TAR"|cut -d' ' -f1); [[ "$sha" == "$ARCHIVE_SHA" ]] || fail "archive $sha"
mkdir -p "$TREE"; tar -xf "$TAR" -C "$TREE"; printf '%s\n' "$PIN" > "$TREE/.chapter-source-revision"
printf 'CHAPTER=9 Memory Hierarchy and Banked Scratchpads\nPIN=%s\nARCHIVE_SHA256=%s\nTREE=%s\n' "$PIN" "$sha" "$TREE"
printf 'KERNEL=%s\nCC=%s\nMAKE=%s\nPYTHON=%s\n' "$(uname -a)" "$(cc --version|sed -n '1p')" "$(make --version|sed -n '1p')" "$(python3 --version 2>&1)"
printf 'SOURCE_IGNORED_INVENTORY_SHA256=%s\n' "$(sha256sum "$BEFORE"|cut -d' ' -f1)"
python3 "$BOOK/experiments/ch09_memory_audit.py" "$TREE" "$PIN"
make -C "$TREE" clean
make -C "$TREE" libtucmodel.a
for t in test-memhier test-cmodel test-config; do printf '\n===== %s =====\n' "$t"; make -C "$TREE" "$t"; done
cc -O2 -g -Wall -Wextra -std=c11 -I"$TREE" -I"$TREE/tu_cmodel" -o "$TREE/ch09_memory_probe" "$BOOK/experiments/ch09_memory_probe.c" "$TREE/libtucmodel.a" -lm
printf '\n===== ch09_memory_probe =====\n'; "$TREE/ch09_memory_probe"
printf '\n===== static-link gates =====\n'
[[ ! -e "$TREE/libtucmodel.so" ]] || fail shared
for b in test-memhier test-cmodel test-config ch09_memory_probe; do deps=$(ldd "$TREE/$b"); printf '[%s]\n%s\n' "$b" "$deps"; ! grep -q 'libtucmodel.so' <<<"$deps" || fail "$b shared"; done
printf '\n===== artifact hashes =====\n'
sha256sum "$TAR" "$BOOK/experiments/ch09_memory_probe.c" "$BOOK/experiments/ch09_memory_audit.py" "$BOOK/experiments/ch09_reproduce.sh" "$TREE/libtucmodel.a" "$TREE/ch09_memory_probe"
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$PIN" ]] || fail "revision changed"
[[ -z "$(git -C "$SRC" branch --show-current)" ]] || fail "branch changed"
clean || fail "source dirty after"
git -C "$SRC" status --short --ignored > "$AFTER"; cmp -s "$BEFORE" "$AFTER" || fail "ignored inventory changed"
echo 'SOURCE_STATE: no tracked/nonignored changes; ignored inventory unchanged'
echo 'REPRODUCTION: PASS'
