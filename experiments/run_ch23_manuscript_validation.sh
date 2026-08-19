#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Release validation must never inherit the review bypass. Review mode is
# enabled only by the explicit --review argument.
unset CH23_MANUSCRIPT_REVIEW_MODE

if [[ $# -gt 1 || ( $# -eq 1 && -z $1 ) ]]; then
  echo "usage: $0 [--review]" >&2
  exit 2
fi

case "${1:-}" in
  "")
    ;;
  --review)
    export CH23_MANUSCRIPT_REVIEW_MODE=1
    ;;
  *)
    echo "usage: $0 [--review]" >&2
    exit 2
    ;;
esac

python3 experiments/ch23_manuscript_validate.py
python3 -O experiments/ch23_manuscript_validate.py
