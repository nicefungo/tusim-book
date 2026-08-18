#!/usr/bin/env bash
set -euo pipefail

BOOK_ROOT=$(git rev-parse --show-toplevel)
TUSIM_ROOT=/home/zxy/Workplace/projects/tusim
PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
RUN_ID=${CH20_RUN_ID:-20260816-ch20-canonical-v1}
RUN_DIR="$BOOK_ROOT/experiments/runs/$RUN_ID"
WORK_PARENT=$(mktemp -d /tmp/ch20-audit-XXXXXX)
WORK="$WORK_PARENT/src"
TRANSCRIPT="$RUN_DIR/transcript.log"
INPUT_COMMIT=$(git rev-parse HEAD)
BOOK_BRANCH=$(git branch --show-current)
SOURCE_IGNORED_BEFORE=$(git -C "$TUSIM_ROOT" status --porcelain=v1 --ignored | sha256sum | cut -d' ' -f1)
SOURCE_STATE_AFTER_DONE=0

INPUTS=(
  edition.yaml
  notes/chapter-20-framing-and-evidence-plan.md
  notes/chapter-20-framing-review-dispositions.md
  notes/chapter-20-source-and-claim-ledger.md
  notes/chapter-20-predraft-audit-report.md
  experiments/ch20_source_audit.py
  experiments/ch20_claim_authorization_probe.c
  experiments/ch20_boundary_checks.py
  experiments/run_ch20_claim_authorization_audit.sh
  experiments/ch20_predraft_validate.py
)

source_state() {
  local label=$1 head branch status ignored
  head=$(git -C "$TUSIM_ROOT" rev-parse HEAD)
  branch=$(git -C "$TUSIM_ROOT" symbolic-ref -q --short HEAD || true)
  status=$(git -C "$TUSIM_ROOT" status --porcelain=v1)
  ignored=$(git -C "$TUSIM_ROOT" status --porcelain=v1 --ignored | sha256sum | cut -d' ' -f1)
  printf 'SOURCE_STATE %s head=%s detached=%s dirty_entries=%s ignored_hash=%s\n' "$label" "$head" "$([[ -z $branch ]] && echo 1 || echo 0)" "$([[ -z $status ]] && echo 0 || printf '%s\n' "$status" | wc -l)" "$ignored"
  [[ $head == "$PIN" && -z $branch && -z $status && $ignored == "$SOURCE_IGNORED_BEFORE" ]]
}

cleanup() {
  local rc=$?
  if [[ $SOURCE_STATE_AFTER_DONE -eq 0 ]]; then
    source_state after || rc=1
  fi
  rm -rf "$WORK_PARENT"
  exit "$rc"
}
trap cleanup EXIT

[[ $BOOK_BRANCH == main ]]
[[ -z $(git status --porcelain=v1) ]]
[[ ! -e $RUN_DIR ]]
[[ $(git -C "$TUSIM_ROOT" rev-parse HEAD) == "$PIN" ]]
[[ -z $(git -C "$TUSIM_ROOT" symbolic-ref -q --short HEAD || true) ]]
[[ -z $(git -C "$TUSIM_ROOT" status --porcelain=v1) ]]
mkdir -p "$RUN_DIR/inputs" "$WORK"
printf '%s\n' "$INPUT_COMMIT" > "$RUN_DIR/input_commit"
printf '%s\n' "$PIN" > "$RUN_DIR/source_pin"
for rel in "${INPUTS[@]}"; do
  mkdir -p "$RUN_DIR/inputs/$(dirname "$rel")"
  cp "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel"
done
(
  cd "$BOOK_ROOT"
  sha256sum "${INPUTS[@]}"
) > "$RUN_DIR/input-hashes.txt"

git -C "$TUSIM_ROOT" archive --format=tar --output="$WORK_PARENT/tusim.tar" "$PIN"
tar -xf "$WORK_PARENT/tusim.tar" -C "$WORK"

body() {
  source_state before
  printf 'BOOK_STATE head=%s branch=%s clean_before=1\n' "$INPUT_COMMIT" "$BOOK_BRANCH"
  printf 'TOOLCHAIN host=%s cc=%s make=%s python=%s\n' "$(uname -m)" "$(cc --version | head -1)" "$(make --version | head -1)" "$(python3 --version)"
  printf 'ARCHIVE disposable=1 path=%s\n' "$WORK"

  python3 "$BOOK_ROOT/experiments/ch20_source_audit.py" "$WORK" "$PIN" | tee "$RUN_DIR/source-audit.log"
  grep -Fx "CH20_SOURCE_AUDIT PASS pin=$PIN hashes=19 predicates=37 checks=57" "$RUN_DIR/source-audit.log"

  cp "$WORK/tu_cmodel/infra/tu_debug.c" "$WORK_PARENT/tu_debug.c.original"
  printf '\n' >> "$WORK/tu_cmodel/infra/tu_debug.c"
  set +e
  python3 "$BOOK_ROOT/experiments/ch20_source_audit.py" "$WORK" "$PIN" > "$RUN_DIR/source-audit-mutation.log" 2>&1
  local src_mut_rc=$?
  set -e
  [[ $src_mut_rc -ne 0 ]]
  grep -F "CHECK hash:tu_cmodel/infra/tu_debug.c=FAIL" "$RUN_DIR/source-audit-mutation.log"
  cp "$WORK_PARENT/tu_debug.c.original" "$WORK/tu_cmodel/infra/tu_debug.c"
  python3 "$BOOK_ROOT/experiments/ch20_source_audit.py" "$WORK" "$PIN" > "$RUN_DIR/source-audit-restored.log"
  grep -Fx "CH20_SOURCE_AUDIT PASS pin=$PIN hashes=19 predicates=37 checks=57" "$RUN_DIR/source-audit-restored.log"
  printf 'SOURCE_AUDIT_MUTATION rejected_rc=%d restored=PASS\n' "$src_mut_rc"

  make -C "$WORK" -j2 libtucmodel.a > "$RUN_DIR/build.log" 2>&1
  ar t "$WORK/libtucmodel.a" > "$RUN_DIR/archive-members.log"
  grep -Fx 'tu_debug.o' "$RUN_DIR/archive-members.log"
  grep -Fx 'tu_dpi.o' "$RUN_DIR/archive-members.log"

  for opt in O0 O2; do
    cc "-${opt}" -g -Wall -Wextra -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" \
      -o "$WORK_PARENT/ch20-probe-${opt}" "$BOOK_ROOT/experiments/ch20_claim_authorization_probe.c" "$WORK/libtucmodel.a" -lm
    readelf -d "$WORK_PARENT/ch20-probe-${opt}" > "$RUN_DIR/probe-${opt}-dynamic.log"
    ! grep -Eq 'NEEDED.*libtucmodel' "$RUN_DIR/probe-${opt}-dynamic.log"
    "$WORK_PARENT/ch20-probe-${opt}" > "$RUN_DIR/probe-${opt}.log" 2> "$RUN_DIR/probe-${opt}.stderr.log"
  done
  cmp -s "$RUN_DIR/probe-O0.log" "$RUN_DIR/probe-O2.log"
  grep -Fx 'ORACLE_NAN shared_accept=1 strict_accept=0 shared_pass=1 shared_fail=0' "$RUN_DIR/probe-O0.log"
  grep -Fx 'CONFIG_EFFECT parse_rc=0 parsed_df=1 rt_rows=8 rt_cols=4 active=weight_stationary' "$RUN_DIR/probe-O0.log"
  grep -Fx 'DUMP_SIZE reported=0 actual=338' "$RUN_DIR/probe-O0.log"
  grep -Fx 'REPLAY_NOOP arbitrary_opcode=0xFE mismatches_equal=0 mismatches_mutated=1 output_bytes=69' "$RUN_DIR/probe-O0.log"
  grep -Fx 'BOUNDS_WRAP wrapped_accept=1 ordinary_accept=0' "$RUN_DIR/probe-O0.log"
  grep -Fx 'CH20_PROBE SUMMARY failures=0' "$RUN_DIR/probe-O0.log"
  printf 'PROBE_OPT_STABILITY byte_identical=1\n'

  cc -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" \
    -o "$WORK_PARENT/ch20-probe-san" "$BOOK_ROOT/experiments/ch20_claim_authorization_probe.c" "$WORK/libtucmodel.a" -lm
  ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=halt_on_error=1 "$WORK_PARENT/ch20-probe-san" > "$RUN_DIR/probe-sanitizer.log" 2> "$RUN_DIR/probe-sanitizer.stderr.log"
  grep -Fx 'CH20_PROBE SUMMARY failures=0' "$RUN_DIR/probe-sanitizer.log"
  ! grep -Eq 'ERROR: AddressSanitizer|runtime error:' "$RUN_DIR/probe-sanitizer.stderr.log"
  printf 'PROBE_SANITIZERS address_undefined=PASS leak_check=excluded_global_singleton\n'

  cc -O0 -g -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/test-debug" "$WORK/tests/test_debug.c" "$WORK/libtucmodel.a" -lm
  "$WORK_PARENT/test-debug" > "$RUN_DIR/test-debug.log" 2>&1
  grep -Fx '=== Results: 25/25 passed, 0 failed ===' "$RUN_DIR/test-debug.log"
  cp "$WORK/tests/test_debug.c" "$WORK_PARENT/test-debug-mut.c"
  python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(); old="CHECK(n >= 0, \"dump returned negative\")"; assert s.count(old)==2; p.write_text(s.replace(old,"CHECK(n > 0, \"dump must report bytes\")"))' "$WORK_PARENT/test-debug-mut.c"
  cc -O0 -g -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/test-debug-mut" "$WORK_PARENT/test-debug-mut.c" "$WORK/libtucmodel.a" -lm
  set +e; "$WORK_PARENT/test-debug-mut" > "$RUN_DIR/test-debug-mutation.log" 2>&1; local debug_mut_rc=$?; set -e
  [[ $debug_mut_rc -ne 0 ]]; grep -Fx '=== Results: 23/25 passed, 2 failed ===' "$RUN_DIR/test-debug-mutation.log"
  printf 'DEBUG_MUTATION meaningful_size_gate_rejected_rc=%d\n' "$debug_mut_rc"

  cc -O0 -g -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/test-errors" "$WORK/tests/test_error_handling.c" "$WORK/libtucmodel.a" -lm
  "$WORK_PARENT/test-errors" > "$RUN_DIR/test-errors.log" 2>&1
  grep -Fx '=== Results: 9/9 passed, 0 failed ===' "$RUN_DIR/test-errors.log"
  cp "$WORK/tests/test_error_handling.c" "$WORK_PARENT/test-errors-mut.c"
  python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(); old="tu_error_inject_disable_all();\n\n    tu_clear_error();"; assert s.count(old)==1; p.write_text(s.replace(old,"tu_error_inject_disable_all();\n    CHECK(rc == TU_ERR_DMA_TIMEOUT, \"injection must be reached\");\n\n    tu_clear_error();"))' "$WORK_PARENT/test-errors-mut.c"
  cc -O0 -g -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/test-errors-mut" "$WORK_PARENT/test-errors-mut.c" "$WORK/libtucmodel.a" -lm
  set +e; "$WORK_PARENT/test-errors-mut" > "$RUN_DIR/test-errors-mutation.log" 2>&1; local err_mut_rc=$?; set -e
  [[ $err_mut_rc -ne 0 ]]; grep -Fx '=== Results: 8/9 passed, 1 failed ===' "$RUN_DIR/test-errors-mutation.log"
  printf 'ERROR_INJECTION_MUTATION reached_requirement_rejected_rc=%d\n' "$err_mut_rc"

  cc -O0 -g -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/test-golden" "$WORK/tests/test_golden.c" "$WORK/libtucmodel.a" -lm
  "$WORK_PARENT/test-golden" --quick > "$RUN_DIR/test-golden.log" 2>&1
  grep -Fx '  11/11 tests passed' "$RUN_DIR/test-golden.log"
  cp "$WORK/tests/test_golden.c" "$WORK_PARENT/test-golden-mut.c"
  python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(); old="O[m * N + n] = sum;"; assert s.count(old)==1; p.write_text(s.replace(old,"O[m * N + n] = sum + 1.0f;"))' "$WORK_PARENT/test-golden-mut.c"
  cc -O0 -g -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/test-golden-mut" "$WORK_PARENT/test-golden-mut.c" "$WORK/libtucmodel.a" -lm
  set +e; "$WORK_PARENT/test-golden-mut" --quick > "$RUN_DIR/test-golden-mutation.log" 2>&1; local golden_mut_rc=$?; set -e
  [[ $golden_mut_rc -ne 0 ]]; grep -Fx '  2/11 tests passed' "$RUN_DIR/test-golden-mutation.log"
  printf 'GOLDEN_MUTATION independent_equation_rejected_rc=%d\n' "$golden_mut_rc"

  cc -shared -o "$WORK/libtucmodel.so" -Wl,--whole-archive "$WORK/libtucmodel.a" -Wl,--no-whole-archive -lm
  python3 "$BOOK_ROOT/experiments/ch20_boundary_checks.py" "$WORK" | tee "$RUN_DIR/boundary-checks.log"
  grep -Fx 'CH20_BOUNDARY_CHECKS PASS' "$RUN_DIR/boundary-checks.log"
  set +e; CH20_MUTATE_BINDING_EXPECTED=1 python3 "$BOOK_ROOT/experiments/ch20_boundary_checks.py" "$WORK" > "$RUN_DIR/boundary-checks-mutation.log" 2>&1; local boundary_mut_rc=$?; set -e
  [[ $boundary_mut_rc -eq 4 ]]; grep -Fx 'CH20_BOUNDARY_CHECKS REJECT' "$RUN_DIR/boundary-checks-mutation.log"; ! grep -Fxq 'CH20_BOUNDARY_CHECKS PASS' "$RUN_DIR/boundary-checks-mutation.log"
  printf 'BOUNDARY_MUTATION expected_value_rejected_rc=%d\n' "$boundary_mut_rc"

  source_state after
  SOURCE_STATE_AFTER_DONE=1
  [[ $(git rev-parse HEAD) == "$INPUT_COMMIT" ]]
  [[ $(git branch --show-current) == "$BOOK_BRANCH" ]]
  for rel in "${INPUTS[@]}"; do cmp -s "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel"; done
  local unexpected
  unexpected=$(git status --porcelain=v1 | grep -v "^?? experiments/runs/$RUN_ID/" || true)
  [[ -z $unexpected ]]
  printf 'BOOK_INPUTS unchanged=1 head=%s\n' "$INPUT_COMMIT"
}

set +e
set -o pipefail
body 2>&1 | tee "$TRANSCRIPT"
body_rc=${PIPESTATUS[0]}
set -e
[[ $body_rc -eq 0 ]]

CH20_RUN_ID="$RUN_ID" python3 "$BOOK_ROOT/experiments/ch20_predraft_validate.py" --body > "$RUN_DIR/body-validation.log"
CH20_RUN_ID="$RUN_ID" python3 -O "$BOOK_ROOT/experiments/ch20_predraft_validate.py" --body > "$RUN_DIR/body-validation-optimized.log"
cmp -s "$RUN_DIR/body-validation.log" "$RUN_DIR/body-validation-optimized.log"
cp "$BOOK_ROOT/experiments/ch20_predraft_validate.py" "$WORK_PARENT/ch20_predraft_validate_mutant.py"
printf '\nassert(False)\n' >> "$WORK_PARENT/ch20_predraft_validate_mutant.py"
for label in normal optimized; do
  set +e
  if [[ $label == normal ]]; then
    CH20_RUN_ID="$RUN_ID" python3 "$WORK_PARENT/ch20_predraft_validate_mutant.py" --body > "$RUN_DIR/validator-assert-mutation-$label.log" 2>&1
  else
    CH20_RUN_ID="$RUN_ID" python3 -O "$WORK_PARENT/ch20_predraft_validate_mutant.py" --body > "$RUN_DIR/validator-assert-mutation-$label.log" 2>&1
  fi
  validator_mut_rc=$?
  set -e
  [[ $validator_mut_rc -ne 0 ]]
  grep -Fx 'CH20_PREDRAFT_VALIDATION FAIL validator-contains-assert' "$RUN_DIR/validator-assert-mutation-$label.log"
done

{
  cd "$RUN_DIR"
  {
    find inputs -type f -print
    printf '%s\n' archive-members.log boundary-checks-mutation.log boundary-checks.log body-validation-optimized.log body-validation.log build.log input-hashes.txt input_commit probe-O0-dynamic.log probe-O0.log probe-O0.stderr.log probe-O2-dynamic.log probe-O2.log probe-O2.stderr.log probe-sanitizer.log probe-sanitizer.stderr.log source-audit-mutation.log source-audit-restored.log source-audit.log source_pin test-debug-mutation.log test-debug.log test-errors-mutation.log test-errors.log test-golden-mutation.log test-golden.log transcript.log validator-assert-mutation-normal.log validator-assert-mutation-optimized.log
  } | LC_ALL=C sort
} > "$RUN_DIR/retained-files.txt"
(
  cd "$RUN_DIR"
  while IFS= read -r rel; do sha256sum "$rel"; done < retained-files.txt
  sha256sum retained-files.txt
) > "$RUN_DIR/sha256-retained.txt"
(cd "$RUN_DIR" && sha256sum -c sha256-retained.txt) > "$RUN_DIR/manifest-check.log"
TRANSCRIPT_SHA=$(sha256sum "$TRANSCRIPT" | cut -d' ' -f1)
printf 'FINALIZED_RUN run=%s transcript_sha256=%s input_commit=%s\n' "$RUN_ID" "$TRANSCRIPT_SHA" "$INPUT_COMMIT" > "$RUN_DIR/finalization.log"
CH20_RUN_ID="$RUN_ID" python3 "$BOOK_ROOT/experiments/ch20_predraft_validate.py" > "$RUN_DIR/predraft-validation.log"
(
  cd "$RUN_DIR"
  sha256sum sha256-retained.txt manifest-check.log finalization.log predraft-validation.log > bundle-sha256.txt
  sha256sum -c bundle-sha256.txt > bundle-check.log
)
CH20_RUN_ID="$RUN_ID" python3 "$BOOK_ROOT/experiments/ch20_predraft_validate.py" --outer > "$RUN_DIR/closure-validation.log"
grep -Fx "CH20_PREDRAFT_VALIDATION PASS run=$RUN_ID input_commit=$INPUT_COMMIT outer=1" "$RUN_DIR/closure-validation.log"

SOURCE_STATE_AFTER_DONE=1
trap - EXIT
rm -rf "$WORK_PARENT"
