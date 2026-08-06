#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)
VALIDATOR="$ROOT/experiments/ch18_manuscript_validate.py"
WORK=$(mktemp -d /tmp/ch18-manuscript-validator-XXXXXX)
trap 'rm -rf "$WORK"' EXIT
unset CH18_REVIEW_MODE

if [[ "${1:-}" == "--review-candidate" ]]; then
  export CH18_REVIEW_MODE=1
elif [[ $# -ne 0 ]]; then
  printf 'usage: %s [--review-candidate]\n' "$0" >&2
  exit 2
fi

timeout 180 python3 "$VALIDATOR"
timeout 180 python3 -O "$VALIDATOR"

cp "$VALIDATOR" "$WORK/ch18_manuscript_validate.py"
printf '\nassert(False)\n' >> "$WORK/ch18_manuscript_validate.py"
set +e
timeout 180 python3 "$WORK/ch18_manuscript_validate.py" >"$WORK/normal.log" 2>&1
normal_rc=$?
timeout 180 python3 -O "$WORK/ch18_manuscript_validate.py" >"$WORK/optimized.log" 2>&1
optimized_rc=$?
set -e
[[ $normal_rc -ne 0 && $optimized_rc -ne 0 ]]
grep -Fx 'CH18_MANUSCRIPT_VALIDATION FAIL: optimizer-removable assertion in validator' "$WORK/normal.log"
grep -Fx 'CH18_MANUSCRIPT_VALIDATION FAIL: optimizer-removable assertion in validator' "$WORK/optimized.log"
printf 'CH18_MANUSCRIPT_VALIDATOR_MUTATION PASS normal_rc=%s optimized_rc=%s reader_claim_mutations=25\n' "$normal_rc" "$optimized_rc"
