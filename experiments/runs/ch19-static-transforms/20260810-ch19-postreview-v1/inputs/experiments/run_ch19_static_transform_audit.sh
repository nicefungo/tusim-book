#!/usr/bin/env bash
set -euo pipefail

PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
BOOK_ROOT=$(git rev-parse --show-toplevel)
TUSIM_ROOT=${TUSIM_ROOT:-/home/zxy/Workplace/projects/tusim}
RUN_ID=${CH19_RUN_ID:-20260810-ch19-postreview-v1}
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
  notes/chapter-19-skeptical-review-dispositions.md \
  experiments/ch19_framing_reproduce.sh \
  experiments/ch19_source_audit.py \
  experiments/ch19_static_transform_probe.c \
  experiments/ch19_ubsan_probe.c \
  experiments/ch19_predraft_validate.py \
  experiments/run_ch19_static_transform_audit.sh; do
  mkdir -p "$RUN_DIR/inputs/$(dirname "$rel")"
  cp "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel"
done
(
  cd "$RUN_DIR/inputs"
  find . -type f -print0 | sort -z | xargs -0 sha256sum > ../INPUT_SHA256SUMS
)

(
  cd "$TUSIM_ROOT"
  git ls-files --others --ignored --exclude-standard -z | sort -z | xargs -0 -r sha256sum
) > "$RUN_DIR/artifacts/source-ignored-before.sha256"

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
set +e
python3 "$BOOK_ROOT/experiments/ch19_source_audit.py" "$ARCHIVE" 0000000000000000000000000000000000000000 \
  > "$RUN_DIR/logs/02-source-pin-control.log" 2>&1
PIN_CONTROL_RC=$?
set -e
[ "$PIN_CONTROL_RC" -ne 0 ] || fail "source pin control survived"
cp "$ARCHIVE/tu_cmodel/isa/tu_scheduler.c" "$TMP/tu_scheduler.original.c"
printf '\n/* CH19 source-hash control */\n' >> "$ARCHIVE/tu_cmodel/isa/tu_scheduler.c"
set +e
python3 "$BOOK_ROOT/experiments/ch19_source_audit.py" "$ARCHIVE" "$PIN" \
  > "$RUN_DIR/logs/03-source-hash-control.log" 2>&1
HASH_CONTROL_RC=$?
set -e
[ "$HASH_CONTROL_RC" -ne 0 ] || fail "source hash control survived"
cp "$TMP/tu_scheduler.original.c" "$ARCHIVE/tu_cmodel/isa/tu_scheduler.c"
python3 "$BOOK_ROOT/experiments/ch19_source_audit.py" "$ARCHIVE" "$PIN" \
  > "$RUN_DIR/logs/04-source-restored.log" 2>&1

make -s -C "$ARCHIVE" libtucmodel.a > "$RUN_DIR/logs/05-build.log" 2>&1
ar t "$ARCHIVE/libtucmodel.a" > "$RUN_DIR/artifacts/archive-members.txt"
cc -std=c11 -O2 -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" \
  -o "$TMP/focused-scheduler" "$ARCHIVE/tests/test_scheduler.c" "$ARCHIVE/libtucmodel.a" -lm
cc -std=c11 -O2 -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" \
  -o "$TMP/focused-liveness" "$ARCHIVE/tests/test_liveness.c" "$ARCHIVE/libtucmodel.a" -lm
cc -std=c11 -O2 -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" \
  -o "$TMP/scheduler-sweep" "$ARCHIVE/tests/test_scheduler_sweep.c" "$ARCHIVE/libtucmodel.a" -lm
readelf -d "$TMP/focused-scheduler" > "$RUN_DIR/logs/09-focused-scheduler-readelf.log"
readelf -d "$TMP/focused-liveness" > "$RUN_DIR/logs/10-focused-liveness-readelf.log"
readelf -d "$TMP/scheduler-sweep" > "$RUN_DIR/logs/11-scheduler-sweep-readelf.log"
! grep -q 'libtucmodel' "$RUN_DIR/logs/09-focused-scheduler-readelf.log"
! grep -q 'libtucmodel' "$RUN_DIR/logs/10-focused-liveness-readelf.log"
! grep -q 'libtucmodel' "$RUN_DIR/logs/11-scheduler-sweep-readelf.log"
timeout 60s "$TMP/focused-scheduler" > "$RUN_DIR/logs/06-focused-scheduler.log" 2>&1
timeout 60s "$TMP/focused-liveness" > "$RUN_DIR/logs/07-focused-liveness.log" 2>&1
timeout 60s "$TMP/scheduler-sweep" > "$RUN_DIR/logs/08-scheduler-sweep.log" 2>&1

cc -std=c11 -O0 -g -Wall -Wextra -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" \
  -o "$TMP/ch19-probe" "$BOOK_ROOT/experiments/ch19_static_transform_probe.c" \
  "$ARCHIVE/libtucmodel.a" -lm
timeout 60s "$TMP/ch19-probe" > "$RUN_DIR/logs/12-static-transform-probe.log" 2>&1
grep -qx 'CH19_PROBE SUMMARY failures=0' "$RUN_DIR/logs/12-static-transform-probe.log"

cc -std=c11 -O1 -g -fsanitize=undefined -fno-sanitize-recover=undefined \
  -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" -o "$TMP/ch19-ubsan" \
  "$BOOK_ROOT/experiments/ch19_ubsan_probe.c" \
  "$ARCHIVE/tu_cmodel/isa/tu_scheduler.c" "$ARCHIVE/tu_cmodel/isa/tu_liveness.c" \
  "$ARCHIVE/tu_cmodel/isa/tu_isa.c" -lm
set +e
timeout 60s "$TMP/ch19-ubsan" scheduler > "$RUN_DIR/logs/13-ubsan-scheduler.log" 2>&1
SCHED_UB_RC=$?
timeout 60s "$TMP/ch19-ubsan" liveness > "$RUN_DIR/logs/14-ubsan-liveness.log" 2>&1
LIVE_UB_RC=$?
set -e
[ "$SCHED_UB_RC" -ne 0 ] || fail "scheduler UBSan fixture did not reject"
[ "$LIVE_UB_RC" -ne 0 ] || fail "liveness UBSan fixture did not reject"
grep -q 'runtime error: signed integer overflow' "$RUN_DIR/logs/13-ubsan-scheduler.log"
grep -q 'runtime error: signed integer overflow' "$RUN_DIR/logs/14-ubsan-liveness.log"
printf 'scheduler_rc=%s\nliveness_rc=%s\n' "$SCHED_UB_RC" "$LIVE_UB_RC" \
  > "$RUN_DIR/artifacts/ubsan-status.txt"

python3 - "$ARCHIVE/tests/test_scheduler.c" "$TMP/test_scheduler_control.c" <<'PY'
from pathlib import Path
import sys
s = Path(sys.argv[1]).read_text()
old = 'ASSERT_EQ(rc, -1, "empty sequence returns error");'
if s.count(old) != 1:
    raise SystemExit("scheduler control pattern mismatch")
Path(sys.argv[2]).write_text(s.replace(old, 'ASSERT_EQ(rc, 0, "MUTATION empty should succeed");'))
PY
cc -std=c11 -O2 -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" -o "$TMP/focused-scheduler-control" \
  "$TMP/test_scheduler_control.c" "$ARCHIVE/libtucmodel.a" -lm
set +e
timeout 60s "$TMP/focused-scheduler-control" > "$RUN_DIR/logs/15-control-scheduler-suite.log" 2>&1
SCHED_SUITE_RC=$?
set -e
[ "$SCHED_SUITE_RC" -ne 0 ] || fail "scheduler suite control survived"
grep -q 'MUTATION empty should succeed' "$RUN_DIR/logs/15-control-scheduler-suite.log"

python3 - "$ARCHIVE/tests/test_liveness.c" "$TMP/test_liveness_control.c" <<'PY'
from pathlib import Path
import sys
s = Path(sys.argv[1]).read_text()
old = 'ASSERT_EQ(rc, -1, "empty returns error");'
if s.count(old) != 1:
    raise SystemExit("liveness control pattern mismatch")
Path(sys.argv[2]).write_text(s.replace(old, 'ASSERT_EQ(rc, 0, "MUTATION empty should succeed");'))
PY
cc -std=c11 -O2 -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" -o "$TMP/focused-liveness-control" \
  "$TMP/test_liveness_control.c" "$ARCHIVE/libtucmodel.a" -lm
set +e
timeout 60s "$TMP/focused-liveness-control" > "$RUN_DIR/logs/16-control-liveness-suite.log" 2>&1
LIVE_SUITE_RC=$?
set -e
[ "$LIVE_SUITE_RC" -ne 0 ] || fail "liveness suite control survived"
grep -q 'MUTATION empty should succeed' "$RUN_DIR/logs/16-control-liveness-suite.log"

cp "$ARCHIVE/tu_cmodel/isa/tu_scheduler.c" "$TMP/tu_scheduler_identity_control.c"
python3 - "$TMP/tu_scheduler_identity_control.c" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
old = '&& si->dim1 == oi->dim1 && si->flags == oi->flags'
new = '&& si->dim1 == oi->dim1 && si->dim2 == oi->dim2\n                && si->immediates == oi->immediates && si->flags == oi->flags'
if s.count(old) != 1:
    raise SystemExit("scheduler identity control pattern mismatch")
p.write_text(s.replace(old, new))
PY
cc -std=c11 -O0 -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" -I"$ARCHIVE/tu_cmodel/isa" \
  -o "$TMP/probe-scheduler-identity-control" \
  "$BOOK_ROOT/experiments/ch19_static_transform_probe.c" "$TMP/tu_scheduler_identity_control.c" \
  "$ARCHIVE/tu_cmodel/isa/tu_liveness.c" "$ARCHIVE/tu_cmodel/isa/tu_isa.c" -lm
set +e
timeout 60s "$TMP/probe-scheduler-identity-control" > "$RUN_DIR/logs/17-control-scheduler-identity.log" 2>&1
SCHED_IDENTITY_RC=$?
set -e
[ "$SCHED_IDENTITY_RC" -ne 0 ] || fail "scheduler identity control survived"
grep -q 'CHECK_FAIL weak identity accepts reversed dependency' "$RUN_DIR/logs/17-control-scheduler-identity.log"

cp "$ARCHIVE/tu_cmodel/isa/tu_liveness.c" "$TMP/tu_liveness_opcode_control.c"
python3 - "$TMP/tu_liveness_opcode_control.c" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
old = '|| instr->opcode >= TU_ISA_LAYER_NORM)'
new = '|| (instr->opcode >= TU_ISA_LAYER_NORM && instr->opcode <= TU_ISA_BATCH_NORM))'
if s.count(old) != 2:
    raise SystemExit("liveness opcode control pattern mismatch")
p.write_text(s.replace(old, new))
PY
cc -std=c11 -O0 -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" -I"$ARCHIVE/tu_cmodel/isa" \
  -o "$TMP/probe-liveness-opcode-control" \
  "$BOOK_ROOT/experiments/ch19_static_transform_probe.c" "$ARCHIVE/tu_cmodel/isa/tu_scheduler.c" \
  "$TMP/tu_liveness_opcode_control.c" "$ARCHIVE/tu_cmodel/isa/tu_isa.c" -lm
set +e
timeout 60s "$TMP/probe-liveness-opcode-control" > "$RUN_DIR/logs/18-control-liveness-opcode.log" 2>&1
LIVE_OPCODE_RC=$?
set -e
[ "$LIVE_OPCODE_RC" -ne 0 ] || fail "liveness opcode control survived"
grep -q 'CHECK_FAIL two W, repeated implicit A, O definitions' "$RUN_DIR/logs/18-control-liveness-opcode.log"

cp "$ARCHIVE/tu_cmodel/isa/tu_liveness.c" "$TMP/tu_liveness_spill_control.c"
python3 - "$TMP/tu_liveness_spill_control.c" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
old = '''g->vregs[victim]->spilled = true;
                        result->num_spills++;
                        result->spill_bytes += g->vregs[victim]->size_bytes;'''
new = '''g->vregs[victim]->spilled = true;
                        /* Negative control: do not count the first marking event. */'''
if s.count(old) != 1:
    raise SystemExit("spill accounting control pattern mismatch")
p.write_text(s.replace(old, new))
PY
cc -std=c11 -O0 -I"$ARCHIVE" -I"$ARCHIVE/tu_cmodel" -I"$ARCHIVE/tu_cmodel/isa" \
  -o "$TMP/probe-spill-accounting-control" \
  "$BOOK_ROOT/experiments/ch19_static_transform_probe.c" "$ARCHIVE/tu_cmodel/isa/tu_scheduler.c" \
  "$TMP/tu_liveness_spill_control.c" "$ARCHIVE/tu_cmodel/isa/tu_isa.c" -lm
set +e
timeout 60s "$TMP/probe-spill-accounting-control" > "$RUN_DIR/logs/19-control-spill-accounting.log" 2>&1
SPILL_ACCOUNTING_RC=$?
set -e
[ "$SPILL_ACCOUNTING_RC" -ne 0 ] || fail "spill accounting control survived"
grep -q 'CHECK_FAIL one unplaced value is counted twice' "$RUN_DIR/logs/19-control-spill-accounting.log"

printf 'scheduler_suite_rc=%s\nliveness_suite_rc=%s\nscheduler_identity_rc=%s\nliveness_opcode_rc=%s\nspill_accounting_rc=%s\n' \
  "$SCHED_SUITE_RC" "$LIVE_SUITE_RC" "$SCHED_IDENTITY_RC" "$LIVE_OPCODE_RC" "$SPILL_ACCOUNTING_RC" \
  > "$RUN_DIR/artifacts/negative-control-status.txt"

cp "$BOOK_ROOT/experiments/ch19_predraft_validate.py" "$TMP/ch19_validator_control.py"
python3 - "$TMP/ch19_validator_control.py" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
anchor = 'import ast\n'
if s.count(anchor) != 1:
    raise SystemExit("validator control pattern mismatch")
p.write_text(s.replace(anchor, anchor + 'assert False\n'))
PY
set +e
python3 "$TMP/ch19_validator_control.py" > "$RUN_DIR/logs/20-validator-control-normal.log" 2>&1
VALIDATOR_NORMAL_RC=$?
python3 -O "$TMP/ch19_validator_control.py" > "$RUN_DIR/logs/21-validator-control-optimized.log" 2>&1
VALIDATOR_OPT_RC=$?
set -e
[ "$VALIDATOR_NORMAL_RC" -ne 0 ] || fail "validator normal control survived"
[ "$VALIDATOR_OPT_RC" -ne 0 ] || fail "validator optimized control survived"
grep -q 'optimizer-removable assertion in validator' "$RUN_DIR/logs/20-validator-control-normal.log"
grep -q 'optimizer-removable assertion in validator' "$RUN_DIR/logs/21-validator-control-optimized.log"

(
  cd "$TUSIM_ROOT"
  git ls-files --others --ignored --exclude-standard -z | sort -z | xargs -0 -r sha256sum
) > "$RUN_DIR/artifacts/source-ignored-after.sha256"
cmp -s "$RUN_DIR/artifacts/source-ignored-before.sha256" "$RUN_DIR/artifacts/source-ignored-after.sha256" \
  || fail "source ignored-file inventory changed"
[ -z "$(git -C "$TUSIM_ROOT" status --porcelain=v1 --untracked-files=all)" ] || fail "source dirty after run"

python3 - "$RUN_DIR/REPORT.md" "$RUN_ID" "$PIN" "$INPUT_COMMIT" <<'PY'
from pathlib import Path
import sys
path, run_id, pin, commit = sys.argv[1:]
Path(path).write_text(f'''# Chapter 19 canonical predraft audit — {run_id}

- Source pin: `{pin}`
- Book input commit: `{commit}`
- Status: **PASS as a candidate post-review drafting authority; the closure validator and outer bundle determine final authorization.**

## Reproduced gates

- Structural source audit: 24 hashes, 158 predicates, 182 checks.
- Source controls: wrong pin and changed copied source both rejected; restored source passed.
- Focused suites: scheduler 14/14 and liveness 12/12, linked to the exact rebuilt archive; scheduler sweep retained as a report.
- Static-transform probe: zero internal failures and a complete 128-row numeric-opcode census.
- Bounded arithmetic checks: scheduler and liveness maximum-dimension fixtures both produced the expected UBSan diagnostic.
- Negative controls: focused scheduler/liveness expectations, scheduler identity, liveness opcode range, spill accounting, and validator assertion safety all rejected.
- Source checkout was detached, clean, and read-only. All builds used a disposable exact-pin archive.

## Authority boundary

This run authorizes only the recorded source, structural, and bounded-probe observations. It does not establish a composed compiler/runtime path or semantic equivalence of scheduler or allocator output. Chapter 11 retains queue/ISA lifecycle ownership.
''')
PY

(
  cd "$RUN_DIR"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
  sha256sum -c SHA256SUMS > manifest-check.log
)
printf 'FINALIZED_RUN run=%s input_commit=%s body_sha256=%s\n' \
  "$RUN_REL" "$INPUT_COMMIT" "$(sha256sum "$RUN_DIR/SHA256SUMS" | cut -d' ' -f1)" \
  > "$RUN_DIR/finalization.log"
CH19_VALIDATION_STAGE=pre CH19_RUN_ID="$RUN_ID" \
  python3 "$BOOK_ROOT/experiments/ch19_predraft_validate.py" > "$RUN_DIR/validator-normal.log"
CH19_VALIDATION_STAGE=pre CH19_RUN_ID="$RUN_ID" \
  python3 -O "$BOOK_ROOT/experiments/ch19_predraft_validate.py" > "$RUN_DIR/validator-optimized.log"
(
  cd "$RUN_DIR"
  sha256sum SHA256SUMS manifest-check.log finalization.log validator-normal.log validator-optimized.log \
    > BUNDLE_SHA256SUMS
  sha256sum -c BUNDLE_SHA256SUMS > bundle-check.log
)
CH19_VALIDATION_STAGE=final CH19_RUN_ID="$RUN_ID" \
  python3 "$BOOK_ROOT/experiments/ch19_predraft_validate.py"
CH19_VALIDATION_STAGE=final CH19_RUN_ID="$RUN_ID" \
  python3 -O "$BOOK_ROOT/experiments/ch19_predraft_validate.py"
git diff --quiet || fail "tracked book files changed during run"
git diff --cached --quiet || fail "index changed during run"
python3 - "$BOOK_ROOT" "$RUN_REL" <<'PY'
from pathlib import Path
import subprocess
import sys
root = Path(sys.argv[1])
prefix = "?? " + sys.argv[2] + "/"
lines = subprocess.check_output(
    ["git", "status", "--porcelain=v1", "--untracked-files=all"],
    cwd=root,
    text=True,
).splitlines()
if not lines or any(not line.startswith(prefix) for line in lines):
    raise SystemExit("unexpected book status after run: " + repr(lines[:10]))
PY
printf 'CH19_CANONICAL PASS run=%s input_commit=%s pin=%s\n' "$RUN_REL" "$INPUT_COMMIT" "$PIN"
