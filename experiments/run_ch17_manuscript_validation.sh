#!/usr/bin/env bash
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel)
VALIDATOR=$ROOT/experiments/ch17_manuscript_validate.py
python3 "$VALIDATOR"
python3 -O "$VALIDATOR"
WORK=$(mktemp -d /tmp/ch17-manuscript-validator-XXXXXX)
cp "$VALIDATOR" "$WORK/ch17_manuscript_validate.py"
printf '\nassert(False)\n' >> "$WORK/ch17_manuscript_validate.py"
set +e
python3 "$WORK/ch17_manuscript_validate.py" > "$WORK/normal.log" 2>&1
normal_rc=$?
python3 -O "$WORK/ch17_manuscript_validate.py" > "$WORK/optimized.log" 2>&1
optimized_rc=$?
set -e
[[ $normal_rc -ne 0 && $optimized_rc -ne 0 ]]
grep -F 'CH17_MANUSCRIPT_VALIDATION FAIL: optimizer-removable assertion in validator' "$WORK/normal.log"
grep -F 'CH17_MANUSCRIPT_VALIDATION FAIL: optimizer-removable assertion in validator' "$WORK/optimized.log"
echo "CH17_MANUSCRIPT_VALIDATOR_MUTATION PASS normal_rc=$normal_rc optimized_rc=$optimized_rc"
