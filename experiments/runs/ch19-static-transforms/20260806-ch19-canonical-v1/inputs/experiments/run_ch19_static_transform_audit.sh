#!/usr/bin/env bash
set -euo pipefail

PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
BOOK_ROOT=$(git rev-parse --show-toplevel)
TUSIM_ROOT=${TUSIM_ROOT:-/home/zxy/Workplace/projects/tusim}
RUN_ID=${CH19_RUN_ID:-20260806-ch19-canonical-v1}
RUN_REL=experiments/runs/ch19-static-transforms/$RUN_ID
RUN_DIR=$BOOK_ROOT/$RUN_REL
INPUT_COMMIT=$(git rev-parse HEAD)
TMP=$(mktemp -d /tmp/ch19-canonical-XXXXXX)
trap 'rm -rf "$TMP"' EXIT

fail() { printf 'CH19_CANONICAL FAIL %s\n' "$*" >&2; exit 1; }
[ "$(git branch --show-current)" = main ] || fail "book not on main"
[ -z "$(git status --porcelain=v1 --untracked-files=all)" ] || fail "book dirty before run"
[ "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" = "$PIN" ] || fail "source pin mismatch"
[ -z "$(git -C "$TUSIM_ROOT" branch --show-current)" ] || fail "source not detached"
[ -z "$(git -C "$TUSIM_ROOT" status --porcelain=v1 --untracked-files=all)" ] || fail "source dirty"
[ ! -e "$RUN_DIR" ] || fail "run directory exists: $RUN_REL"

mkdir -p "$RUN_DIR"/{inputs,logs,artifacts}
for rel in \
  PLAN.md style-guide.md edition.yaml fidelity-matrix.md source-audit.md \
  manuscript/part-2-core/11-instruction-surfaces-and-command-queue-ordering.md \
  notes/chapter-19-framing-and-evidence-plan.md \
  notes/chapter-19-source-and-claim-ledger.md \
  experiments/ch19_framing_reproduce.sh \
  experiments/ch19_source_audit.py \
  experiments/ch19_static_transform_probe.c \
  experiments/ch19_ubsan_probe.c \
  experiments/run_ch19_static_transform_audit.sh; do
  mkdir -p "$RUN_DIR/inputs/$(dirname "$rel")"
  cp "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel"
done
(
  cd "$RUN_DIR/inputs"
  find . -type f -print0 | sort -z | xargs -0 sha256sum > ../INPUT_SHA256SUMS
)

ARCHIVE=$TMP/tusim
mkdir -p "$ARCHIVE"
git -C "$TUSIM_ROOT" archive "$PIN" | tar -x -C "$ARCHIVE"
printf '%s\n' "$PIN" > "$RUN_DIR/artifacts/source-pin.txt"
printf '%s\n' "$INPUT_COMMIT" > "$RUN_DIR/artifacts/input-commit.txt"
{
  cc --version | sed -n '1p'
  make --version | sed -n '1p'
  python3 --version
  uname -a
} > "$RUN_DIR/artifacts/toolchain.txt"

python3 "$BOOK_ROOT/experiments/ch19_source_audit.py" "$ARCHIVE" "$PIN" \
  > "$RUN_DIR/logs/01-source-audit.log" 2>&1
make -s -C "$ARCHIVE" libtucmodel.a > "$RUN_DIR/logs/02-build.log" 2>&1
make -s -C "$ARCHIVE" test-scheduler > "$RUN_DIR/logs/03-focused-scheduler.log" 2>&1
make -s -C "$ARCHIVE" test-liveness > "$RUN_DIR/logs/04-focused-liveness.log" 2>&1
make -s -C "$ARCHIVE" test-scheduler-sweep > "$RUN_DIR/logs/05-scheduler-sweep.log" 2>&1

cc -std=c11 -O0 -g -Wall -Wextra -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" \
  -o "$TMP/ch19-probe" "$BOOK_ROOT/experiments/ch19_static_transform_probe.c" \
  "$ARCHIVE/libtucmodel.a" -lm
"$TMP/ch19-probe" > "$RUN_DIR/logs/06-static-transform-probe.log" 2>&1
grep -qx 'CH19_PROBE SUMMARY failures=0' "$RUN_DIR/logs/06-static-transform-probe.log"

cc -std=c11 -O1 -g -fsanitize=undefined -fno-sanitize-recover=undefined \
  -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" -o "$TMP/ch19-ubsan" \
  "$BOOK_ROOT/experiments/ch19_ubsan_probe.c" \
  "$ARCHIVE/tu_cmodel/isa/tu_scheduler.c" "$ARCHIVE/tu_cmodel/isa/tu_liveness.c" \
  "$ARCHIVE/tu_cmodel/isa/tu_isa.c" -lm
set +e
"$TMP/ch19-ubsan" scheduler > "$RUN_DIR/logs/07-ubsan-scheduler.log" 2>&1
SCHED_UB_RC=$?
"$TMP/ch19-ubsan" liveness > "$RUN_DIR/logs/08-ubsan-liveness.log" 2>&1
LIVE_UB_RC=$?
set -e
[ "$SCHED_UB_RC" -ne 0 ] || fail "scheduler UBSan fixture did not reject"
[ "$LIVE_UB_RC" -ne 0 ] || fail "liveness UBSan fixture did not reject"
grep -q 'runtime error: signed integer overflow' "$RUN_DIR/logs/07-ubsan-scheduler.log"
grep -q 'runtime error: signed integer overflow' "$RUN_DIR/logs/08-ubsan-liveness.log"
printf 'scheduler_rc=%s\nliveness_rc=%s\n' "$SCHED_UB_RC" "$LIVE_UB_RC" \
  > "$RUN_DIR/artifacts/ubsan-status.txt"

# Real focused-suite assertion mutations: each copied suite must reject a wrong expectation.
python3 - "$ARCHIVE/tests/test_scheduler.c" "$TMP/test_scheduler_mut.c" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
old='ASSERT_EQ(rc, -1, "empty sequence returns error");'
assert s.count(old)==1
Path(sys.argv[2]).write_text(s.replace(old,'ASSERT_EQ(rc, 0, "MUTATION empty should succeed");'))
PY
cc -std=c11 -O2 -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" -o "$TMP/test-scheduler-mut" \
  "$TMP/test_scheduler_mut.c" "$ARCHIVE/libtucmodel.a" -lm
set +e
"$TMP/test-scheduler-mut" > "$RUN_DIR/logs/09-mutation-scheduler-suite.log" 2>&1
MS_RC=$?
set -e
[ "$MS_RC" -ne 0 ] || fail "scheduler suite mutation survived"
grep -q 'MUTATION empty should succeed' "$RUN_DIR/logs/09-mutation-scheduler-suite.log"

python3 - "$ARCHIVE/tests/test_liveness.c" "$TMP/test_liveness_mut.c" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
old='ASSERT_EQ(rc, -1, "empty returns error");'
assert s.count(old)==1
Path(sys.argv[2]).write_text(s.replace(old,'ASSERT_EQ(rc, 0, "MUTATION empty should succeed");'))
PY
cc -std=c11 -O2 -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" -o "$TMP/test-liveness-mut" \
  "$TMP/test_liveness_mut.c" "$ARCHIVE/libtucmodel.a" -lm
set +e
"$TMP/test-liveness-mut" > "$RUN_DIR/logs/10-mutation-liveness-suite.log" 2>&1
ML_RC=$?
set -e
[ "$ML_RC" -ne 0 ] || fail "liveness suite mutation survived"
grep -q 'MUTATION empty should succeed' "$RUN_DIR/logs/10-mutation-liveness-suite.log"

# Semantic mutations must alter executable source and make the retained probe reject.
cp "$ARCHIVE/tu_cmodel/isa/tu_scheduler.c" "$TMP/tu_scheduler_mut.c"
python3 - "$TMP/tu_scheduler_mut.c" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
old='&& si->dim1 == oi->dim1\n                && si->flags == oi->flags'
new='&& si->dim1 == oi->dim1\n                && si->dim2 == oi->dim2\n                && si->immediates == oi->immediates\n                && si->flags == oi->flags'
assert s.count(old)==1
p.write_text(s.replace(old,new))
PY
cc -std=c11 -O0 -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" -o "$TMP/probe-sched-mut" \
  "$BOOK_ROOT/experiments/ch19_static_transform_probe.c" "$TMP/tu_scheduler_mut.c" \
  "$ARCHIVE/tu_cmodel/isa/tu_liveness.c" "$ARCHIVE/tu_cmodel/isa/tu_isa.c" -lm
set +e
"$TMP/probe-sched-mut" > "$RUN_DIR/logs/11-mutation-scheduler-identity.log" 2>&1
MSI_RC=$?
set -e
[ "$MSI_RC" -ne 0 ] || fail "scheduler identity mutation survived"
grep -q 'CHECK_FAIL weak identity accepts reversed dependency' "$RUN_DIR/logs/11-mutation-scheduler-identity.log"

cp "$ARCHIVE/tu_cmodel/isa/tu_liveness.c" "$TMP/tu_liveness_mut.c"
python3 - "$TMP/tu_liveness_mut.c" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
old='|| instr->opcode >= TU_ISA_LAYER_NORM)'
new='|| (instr->opcode >= TU_ISA_LAYER_NORM && instr->opcode <= TU_ISA_BATCH_NORM))'
assert s.count(old)==2
p.write_text(s.replace(old,new))
PY
cc -std=c11 -O0 -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" -o "$TMP/probe-live-mut" \
  "$BOOK_ROOT/experiments/ch19_static_transform_probe.c" "$ARCHIVE/tu_cmodel/isa/tu_scheduler.c" \
  "$TMP/tu_liveness_mut.c" "$ARCHIVE/tu_cmodel/isa/tu_isa.c" -lm
set +e
"$TMP/probe-live-mut" > "$RUN_DIR/logs/12-mutation-liveness-opcode.log" 2>&1
MLO_RC=$?
set -e
[ "$MLO_RC" -ne 0 ] || fail "liveness opcode mutation survived"
grep -q 'CHECK_FAIL repeated implicit A' "$RUN_DIR/logs/12-mutation-liveness-opcode.log"
printf 'scheduler_suite_rc=%s\nliveness_suite_rc=%s\nscheduler_identity_rc=%s\nliveness_opcode_rc=%s\n' \
  "$MS_RC" "$ML_RC" "$MSI_RC" "$MLO_RC" > "$RUN_DIR/artifacts/mutation-status.txt"

cat > "$RUN_DIR/REPORT.md" <<EOF
# Chapter 19 canonical predraft audit — v1

- Source pin: \`$PIN\`
- Book input commit: \`$INPUT_COMMIT\`
- Status: **PASS as a predraft evidence run; manuscript drafting remains blocked pending skeptical review and a post-review seal.**

## Reproduced gates

- Structural source audit: 24 hashes, 149 predicates, 173 checks.
- Focused suites: scheduler 14/14; liveness 12/12; scheduler sweep reproduced.
- Static-transform probe: zero internal failures.
- UBSan: scheduler and liveness maximum-dimension fixtures both rejected signed overflow.
- Mutations: both focused-suite assertion mutations and both executable semantic mutations were rejected.
- Source checkout was detached, clean, and read-only. All builds used a disposable exact-pin archive.

## Authority boundary

This run authorizes only the recorded source, structural, and bounded-probe observations. It does not establish a composed compiler/runtime path or semantic equivalence of scheduler or allocator output. Chapter 11 retains queue/ISA lifecycle ownership.
EOF

(
  cd "$RUN_DIR"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
  sha256sum -c SHA256SUMS >/dev/null
  sha256sum -c INPUT_SHA256SUMS >/dev/null
)
printf 'CH19_CANONICAL PASS run=%s input_commit=%s pin=%s\n' "$RUN_REL" "$INPUT_COMMIT" "$PIN"
