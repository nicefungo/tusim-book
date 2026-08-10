#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)
VALIDATOR="$ROOT/experiments/ch19_manuscript_validate.py"
WORK=$(mktemp -d /tmp/ch19-manuscript-validator-XXXXXX)
trap 'rm -rf "$WORK"' EXIT
unset CH19_MANUSCRIPT_REVIEW_MODE

if [[ $# -eq 1 && "$1" == "--review-candidate" ]]; then
  export CH19_MANUSCRIPT_REVIEW_MODE=1
elif [[ $# -ne 0 ]]; then
  printf 'usage: %s [--review-candidate]\n' "$0" >&2
  exit 2
fi

timeout 240 python3 "$VALIDATOR"
timeout 240 python3 -O "$VALIDATOR"

cp "$VALIDATOR" "$WORK/ch19_manuscript_validate.py"
printf '\nassert(False)\n' >> "$WORK/ch19_manuscript_validate.py"
set +e
timeout 240 python3 "$WORK/ch19_manuscript_validate.py" >"$WORK/normal.log" 2>&1
normal_rc=$?
timeout 240 python3 -O "$WORK/ch19_manuscript_validate.py" >"$WORK/optimized.log" 2>&1
optimized_rc=$?
set -e
[[ $normal_rc -ne 0 && $optimized_rc -ne 0 ]]
grep -Fx 'CH19_MANUSCRIPT_VALIDATION FAIL: optimizer-removable assertion in validator' "$WORK/normal.log"
grep -Fx 'CH19_MANUSCRIPT_VALIDATION FAIL: optimizer-removable assertion in validator' "$WORK/optimized.log"
printf 'CH19_MANUSCRIPT_VALIDATOR_MUTATION PASS normal_rc=%s optimized_rc=%s reader_claim_mutations=23\n' "$normal_rc" "$optimized_rc"
