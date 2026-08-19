#!/usr/bin/env bash
set -euo pipefail
umask 022
BOOK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="/home/zxy/Workplace/projects/tusim"
MODE="provisional"; REVIEW=""; RECONCILIATION=""; REVIEWED_PROVISIONAL=""
while [[ $# -gt 0 ]]; do
 case "$1" in
  --source) SOURCE="$2"; shift 2;;
  --mode) MODE="$2"; shift 2;;
  --review) REVIEW="$2"; shift 2;;
  --reconciliation) RECONCILIATION="$2"; shift 2;;
  --reviewed-provisional) REVIEWED_PROVISIONAL="$2"; shift 2;;
  *) echo "unknown argument: $1" >&2; exit 2;;
 esac
done
[[ "$MODE" == provisional || "$MODE" == postreview ]] || { echo "bad mode" >&2; exit 2; }
if [[ "$MODE" == postreview ]]; then
 [[ -f "$REVIEW" && -f "$RECONCILIATION" && -d "$REVIEWED_PROVISIONAL" ]] || { echo "postreview requires --review, --reconciliation, --reviewed-provisional" >&2; exit 2; }
 python3 "$REVIEWED_PROVISIONAL/verify_ch23_predraft_seal.py" --run-dir "$REVIEWED_PROVISIONAL" >/dev/null
fi
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-${MODE}"
BASE="$BOOK_ROOT/results/ch23-predraft"; mkdir -p "$BASE"
FINAL="$BASE/$RUN_ID"; [[ ! -e "$FINAL" ]] || { echo "destination collision: $FINAL" >&2; exit 3; }
TMP="$(mktemp -d "$BASE/.${RUN_ID}.XXXXXX")"
cleanup(){ [[ -d "$TMP" ]] && rm -rf "$TMP"; }; trap cleanup EXIT
for f in \
 notes/chapter-23-framing-and-evidence-plan.md \
 notes/chapter-23-source-claim-ledger.md \
 experiments/ch23_extension_recon.py \
 experiments/validate_ch23_predraft.py \
 experiments/test_ch23_evidence_controls.py \
 experiments/run_ch23_predraft_seal.sh \
 experiments/verify_ch23_predraft_seal.py \
 experiments/test_ch23_seal_controls.py; do cp "$BOOK_ROOT/$f" "$TMP/"; done
if [[ "$MODE" == postreview ]]; then
 cp "$REVIEW" "$TMP/independent-review.md"
 cp "$RECONCILIATION" "$TMP/review-reconciliation.md"
 cp "$REVIEWED_PROVISIONAL/seal.json" "$TMP/reviewed-provisional-seal.json"
 cp "$REVIEWED_PROVISIONAL/retained.sha256" "$TMP/reviewed-provisional-retained.sha256"
 basename "$REVIEWED_PROVISIONAL" > "$TMP/reviewed-provisional-run.txt"
fi
python3 "$TMP/ch23_extension_recon.py" --source "$SOURCE" --output "$TMP/recon.log" >/dev/null
python3 "$TMP/test_ch23_evidence_controls.py" --recon "$TMP/ch23_extension_recon.py" --source "$SOURCE" > "$TMP/controls.log"
python3 - "$TMP" <<'PY'
from pathlib import Path
import hashlib,sys
p=Path(sys.argv[1]); names=sorted(x.name for x in p.iterdir() if x.is_file())
(p/'payload.sha256').write_text(''.join(f"{hashlib.sha256((p/n).read_bytes()).hexdigest()}  {n}\n" for n in names))
PY
python3 "$TMP/validate_ch23_predraft.py" --run-dir "$TMP" --mode "$MODE" | tee "$TMP/validation.log"
python3 - "$TMP" "$MODE" <<'PY'
from pathlib import Path
import hashlib,json,sys
p=Path(sys.argv[1]); mode=sys.argv[2]
names=sorted(x.name for x in p.iterdir() if x.is_file() and x.name not in ('seal.json','retained.sha256'))
manifest=''.join(f"{hashlib.sha256((p/n).read_bytes()).hexdigest()}  {n}\n" for n in names)
(p/'retained.sha256').write_text(manifest)
seal={'schema':'tusim-book/ch23-predraft-seal/v1','mode':mode,'source_pin':'e918c80b6fce833cd1fcae97730fa841c2176f25','decision':'extension-contract-card/weakest-missing-edge','compiler_runtime_onnx_boundary':'negative','validation':'PASS','retained_manifest_sha256':hashlib.sha256(manifest.encode()).hexdigest()}
(p/'seal.json').write_text(json.dumps(seal,indent=2,sort_keys=True)+'\n')
PY
python3 "$TMP/verify_ch23_predraft_seal.py" --run-dir "$TMP"
[[ ! -e "$FINAL" ]] || { echo "destination collision before finalization: $FINAL" >&2; exit 3; }
mv -T "$TMP" "$FINAL"; trap - EXIT
python3 "$FINAL/verify_ch23_predraft_seal.py" --run-dir "$FINAL"
python3 "$FINAL/test_ch23_seal_controls.py" --run-dir "$FINAL"
printf '%s\n' "$FINAL"
