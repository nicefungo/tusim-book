#!/usr/bin/env bash
set -euo pipefail
MODE=${1:?usage: $0 execute|verify RUN_ID}
RUN_ID=${2:?usage: $0 execute|verify RUN_ID}
BOOK_ROOT=$(cd "$(dirname "$0")/.." && pwd)
TUSIM_ROOT=${TUSIM_ROOT:-/home/zxy/Workplace/projects/tusim}
PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
RUN_REL="experiments/runs/ch22-predraft/$RUN_ID"
RUN_DIR="$BOOK_ROOT/$RUN_REL"
INV="$BOOK_ROOT/notes/chapter-22-report-inventory.json"
CLAIMS="$BOOK_ROOT/notes/chapter-22-claim-register.json"
DERIVED="$BOOK_ROOT/notes/chapter-22-predraft-registers.json"

[[ "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" == "$PIN" ]]
[[ -z "$(git -C "$TUSIM_ROOT" status --porcelain)" ]]
[[ "$(git -C "$TUSIM_ROOT" symbolic-ref -q HEAD || true)" == "" ]]

if [[ "$MODE" == execute ]]; then
  [[ ! -e "$RUN_DIR" ]] || { printf 'refusing existing run: %s\n' "$RUN_DIR" >&2; exit 2; }
  mkdir -p "$RUN_DIR/inputs"
  cp "$INV" "$CLAIMS" \
     "$BOOK_ROOT/experiments/ch22_focused_reconciliation.py" \
     "$BOOK_ROOT/experiments/ch22_build_claim_register.py" \
     "$BOOK_ROOT/experiments/ch22_build_predraft_registers.py" \
     "$BOOK_ROOT/experiments/ch22_predraft_validate.py" \
     "$BOOK_ROOT/experiments/run_ch22_predraft_evidence_audit.sh" \
     "$RUN_DIR/inputs/"
  python3 "$BOOK_ROOT/experiments/ch22_focused_reconciliation.py" \
    --book-root "$BOOK_ROOT" --tusim-root "$TUSIM_ROOT" --out "$RUN_DIR"
  python3 "$BOOK_ROOT/experiments/ch22_build_claim_register.py" \
    --source "$TUSIM_ROOT/docs/exploration" --inventory "$INV" \
    --out "$RUN_DIR/generated-claim-register.json"
  cmp "$CLAIMS" "$RUN_DIR/generated-claim-register.json"
  python3 "$BOOK_ROOT/experiments/ch22_build_predraft_registers.py" \
    --claims "$CLAIMS" --recon "$RUN_DIR/reconciliation.json" \
    --recon-relative "$RUN_REL/reconciliation.json" \
    --out "$RUN_DIR/candidate-predraft-registers.json"
  python3 "$BOOK_ROOT/experiments/ch22_predraft_validate.py" \
    --claims "$CLAIMS" --derived "$RUN_DIR/candidate-predraft-registers.json" \
    --recon "$RUN_DIR/reconciliation.json" --source "$TUSIM_ROOT/docs/exploration" \
    --inventory "$INV" --mutation-out "$RUN_DIR/mutation-results.json"
  (
    cd "$RUN_DIR"
    sha256sum reconciliation.json geometry.log memory_overlap.log \
      numerics_representation.log operators.log sharing_topology.log \
      runtime_static_policy.log generated-claim-register.json \
      candidate-predraft-registers.json mutation-results.json inputs/* \
      > SHA256SUMS
  )
  printf 'CH22_PREDRAFT_EXECUTE PASS run=%s\n' "$RUN_REL"
elif [[ "$MODE" == verify ]]; then
  [[ -d "$RUN_DIR" ]]
  cmp "$DERIVED" "$RUN_DIR/candidate-predraft-registers.json"
  python3 "$BOOK_ROOT/experiments/ch22_predraft_validate.py" \
    --claims "$CLAIMS" --derived "$DERIVED" --recon "$RUN_DIR/reconciliation.json" \
    --source "$TUSIM_ROOT/docs/exploration" --inventory "$INV" \
    --mutation-out "$RUN_DIR/verify-mutation-results.json"
  (
    cd "$RUN_DIR"
    sha256sum --check SHA256SUMS
  )
  printf 'CH22_PREDRAFT_VERIFY PASS run=%s\n' "$RUN_REL"
else
  printf 'unknown mode: %s\n' "$MODE" >&2
  exit 2
fi
