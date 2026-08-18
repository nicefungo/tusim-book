#!/usr/bin/env bash
set -euo pipefail

BOOK_ROOT=$(git rev-parse --show-toplevel)
TUSIM_ROOT=/home/zxy/Workplace/projects/tusim
PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
RUN_ID=${CH20_RUN_ID:-20260816-ch20-postreview-v2}
RUN_DIR="$BOOK_ROOT/experiments/runs/$RUN_ID"
INPUT_COMMIT=$(git rev-parse HEAD)
BOOK_BRANCH=$(git branch --show-current)
SOURCE_IGNORED_BEFORE=$(git -C "$TUSIM_ROOT" status --porcelain=v1 --ignored | sha256sum | cut -d' ' -f1)
SOURCE_STATE_AFTER_DONE=0
WORK_PARENT=
WORK=
TRANSCRIPT="$RUN_DIR/transcript.log"

source_state() {
  local label=$1 head branch status ignored
  head=$(git -C "$TUSIM_ROOT" rev-parse HEAD)
  branch=$(git -C "$TUSIM_ROOT" symbolic-ref -q --short HEAD || true)
  status=$(git -C "$TUSIM_ROOT" status --porcelain=v1)
  ignored=$(git -C "$TUSIM_ROOT" status --porcelain=v1 --ignored | sha256sum | cut -d' ' -f1)
  printf 'SOURCE_STATE %s head=%s detached=%s dirty_entries=%s ignored_hash=%s\n' "$label" "$head" "$([[ -z $branch ]] && echo 1 || echo 0)" "$([[ -z $status ]] && echo 0 || printf '%s\n' "$status" | wc -l)" "$ignored"
  [[ $head == "$PIN" && -z $branch && -z $status && $ignored == "$SOURCE_IGNORED_BEFORE" ]]
}

# A child mode exercises the same fail-fast pipeline scaffold without creating
# book artifacts. Its parent retains the complete before/failure/after output.
if [[ ${CH20_FAILURE_CONTROL:-0} == 1 ]]; then
  control_after=0
  control_cleanup() {
    local rc=$?
    if [[ $control_after -eq 0 ]]; then source_state after || rc=1; fi
    exit "$rc"
  }
  control_body() {
    source_state before
    printf 'FAILURE_CONTROL before_failed_gate\n'
    false
    printf 'FAILURE_CONTROL SURVIVED_AFTER_FAILED_GATE\n'
  }
  trap control_cleanup EXIT
  set +e
  ( set -euo pipefail; control_body ) 2>&1
  control_rc=$?
  set -e
  exit "$control_rc"
fi

WORK_PARENT=$(mktemp -d /tmp/ch20-audit-XXXXXX)
WORK="$WORK_PARENT/src"
INPUTS=(
  edition.yaml
  notes/chapter-20-framing-and-evidence-plan.md
  notes/chapter-20-framing-review-dispositions.md
  notes/chapter-20-source-and-claim-ledger.md
  notes/chapter-20-predraft-audit-report.md
  notes/chapter-20-skeptical-predraft-review-dispositions.md
  experiments/ch20_source_audit.py
  experiments/ch20_claim_authorization_probe.c
  experiments/ch20_boundary_checks.py
  experiments/run_ch20_claim_authorization_audit.sh
  experiments/ch20_predraft_validate.py
)

cleanup() {
  local rc=$?
  if [[ $SOURCE_STATE_AFTER_DONE -eq 0 ]]; then source_state after || rc=1; fi
  [[ -z ${WORK_PARENT:-} ]] || rm -rf "$WORK_PARENT"
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

set +e
CH20_FAILURE_CONTROL=1 bash "$BOOK_ROOT/experiments/run_ch20_claim_authorization_audit.sh" > "$RUN_DIR/failure-path-control.log" 2>&1
failure_control_rc=$?
set -e
[[ $failure_control_rc -ne 0 ]]
grep -F "SOURCE_STATE before head=$PIN detached=1 dirty_entries=0 ignored_hash=$SOURCE_IGNORED_BEFORE" "$RUN_DIR/failure-path-control.log"
grep -F "SOURCE_STATE after head=$PIN detached=1 dirty_entries=0 ignored_hash=$SOURCE_IGNORED_BEFORE" "$RUN_DIR/failure-path-control.log"
grep -Fx 'FAILURE_CONTROL before_failed_gate' "$RUN_DIR/failure-path-control.log"
! grep -Fq 'SURVIVED_AFTER_FAILED_GATE' "$RUN_DIR/failure-path-control.log"
printf 'FAILURE_PATH_CONTROL rejected_rc=%d survived=0 source_after=PASS\n' "$failure_control_rc" > "$RUN_DIR/failure-path-summary.log"

git -C "$TUSIM_ROOT" archive --format=tar --output="$WORK_PARENT/tusim.tar" "$PIN"
tar -xf "$WORK_PARENT/tusim.tar" -C "$WORK"

body() {
  source_state before
  printf 'BOOK_STATE head=%s branch=%s clean_before=1\n' "$INPUT_COMMIT" "$BOOK_BRANCH"
  printf 'TOOLCHAIN host=%s cc=%s make=%s python=%s\n' "$(uname -m)" "$(cc --version | head -1)" "$(make --version | head -1)" "$(python3 --version)"
  printf 'ARCHIVE disposable=1 path=%s\n' "$WORK"
  while IFS= read -r line; do printf '%s\n' "$line"; done < "$RUN_DIR/failure-path-summary.log"

  python3 "$BOOK_ROOT/experiments/ch20_source_audit.py" "$WORK" "$PIN" | tee "$RUN_DIR/source-audit.log"
  grep -Fx "CH20_SOURCE_AUDIT PASS pin=$PIN hashes=22 predicates=52 checks=75" "$RUN_DIR/source-audit.log"

  cp "$WORK/tu_cmodel/infra/tu_debug.c" "$WORK_PARENT/tu_debug.c.original"
  printf '\n' >> "$WORK/tu_cmodel/infra/tu_debug.c"
  set +e
  python3 "$BOOK_ROOT/experiments/ch20_source_audit.py" "$WORK" "$PIN" > "$RUN_DIR/source-audit-hash-mutation.log" 2>&1
  local hash_mut_rc=$?
  set -e
  [[ $hash_mut_rc -ne 0 ]]
  grep -F "CHECK hash:tu_cmodel/infra/tu_debug.c=FAIL" "$RUN_DIR/source-audit-hash-mutation.log"
  cp "$WORK_PARENT/tu_debug.c.original" "$WORK/tu_cmodel/infra/tu_debug.c"

  local membership="$WORK_PARENT/membership-mut"
  mkdir "$membership"; tar -xf "$WORK_PARENT/tusim.tar" -C "$membership"
  python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(); old="test-scheduler test-liveness test-dpi"; new="test-scheduler test-liveness test-debug"; sys.exit(3) if s.count(old)!=1 else p.write_text(s.replace(old,new))' "$membership/Makefile"
  local membership_hash; membership_hash=$(sha256sum "$membership/Makefile" | cut -d' ' -f1)
  cp "$BOOK_ROOT/experiments/ch20_source_audit.py" "$WORK_PARENT/source-audit-membership-mut.py"
  python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(); old=sys.argv[2]; new=sys.argv[3]; sys.exit(3) if s.count(old)!=1 else p.write_text(s.replace(old,new))' "$WORK_PARENT/source-audit-membership-mut.py" 5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2 "$membership_hash"
  set +e
  python3 "$WORK_PARENT/source-audit-membership-mut.py" "$membership" "$PIN" > "$RUN_DIR/source-audit-membership-mutation.log" 2>&1
  local membership_rc=$?
  set -e
  [[ $membership_rc -ne 0 ]]
  grep -Fx 'CHECK hash:Makefile=PASS' "$RUN_DIR/source-audit-membership-mutation.log"
  grep -Fx 'CHECK predicate:inventory-exact-31-aggregate=FAIL' "$RUN_DIR/source-audit-membership-mutation.log"
  printf 'MEMBERSHIP_SET_MUTATION count_preserved=31 rejected_rc=%d\n' "$membership_rc"

  local random_mut="$WORK_PARENT/random-mut"
  mkdir "$random_mut"; tar -xf "$WORK_PARENT/tusim.tar" -C "$random_mut"
  python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(); old="tu_random_seed(&rng, 42);"; new="tu_random_seed(&rng, 43);"; sys.exit(3) if s.count(old)!=1 else p.write_text(s.replace(old,new))' "$random_mut/tests/test_random.c"
  local random_hash; random_hash=$(sha256sum "$random_mut/tests/test_random.c" | cut -d' ' -f1)
  cp "$BOOK_ROOT/experiments/ch20_source_audit.py" "$WORK_PARENT/source-audit-random-mut.py"
  python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(); old=sys.argv[2]; new=sys.argv[3]; sys.exit(3) if s.count(old)!=1 else p.write_text(s.replace(old,new))' "$WORK_PARENT/source-audit-random-mut.py" 704c1dbd4a2aa648784f00bda8e69ab7efc4e2bf7aec364721c0cc9baa6e41f3 "$random_hash"
  set +e
  python3 "$WORK_PARENT/source-audit-random-mut.py" "$random_mut" "$PIN" > "$RUN_DIR/source-audit-random-mutation.log" 2>&1
  local random_rc=$?
  set -e
  [[ $random_rc -ne 0 ]]
  grep -Fx 'CHECK hash:tests/test_random.c=PASS' "$RUN_DIR/source-audit-random-mutation.log"
  grep -Fx 'CHECK predicate:random-exact-fixed-seeds=FAIL' "$RUN_DIR/source-audit-random-mutation.log"
  printf 'RANDOM_CENSUS_MUTATION seed_42_to_43 rejected_rc=%d\n' "$random_rc"

  python3 "$BOOK_ROOT/experiments/ch20_source_audit.py" "$WORK" "$PIN" > "$RUN_DIR/source-audit-restored.log"
  grep -Fx "CH20_SOURCE_AUDIT PASS pin=$PIN hashes=22 predicates=52 checks=75" "$RUN_DIR/source-audit-restored.log"
  printf 'SOURCE_AUDIT_MUTATIONS hash_rc=%d membership_rc=%d random_rc=%d restored=PASS\n' "$hash_mut_rc" "$membership_rc" "$random_rc"

  make -C "$WORK" -n libtucmodel.a > "$RUN_DIR/make-dry-run-selected.log"
  python3 -c 'from pathlib import Path; import sys; lines=[line for line in Path(sys.argv[1]).read_text().splitlines() if not line.startswith("make: ")]; sys.exit(1 if any("/tmp/" in line for line in lines) else 0)' "$RUN_DIR/make-dry-run-selected.log"
  make -C "$WORK" -n test-asm test-full test-compiler clean > "$RUN_DIR/make-dry-run-forbidden.log"
  grep -F '/tmp/test_asm' "$RUN_DIR/make-dry-run-forbidden.log"
  grep -F '/tmp/gpt_block_tu.c' "$RUN_DIR/make-dry-run-forbidden.log"
  grep -F 'rm -f /tmp/gpt_block_tu /tmp/gpt_block_tu.c /tmp/test_asm' "$RUN_DIR/make-dry-run-forbidden.log"
  printf 'DRY_RUN_BOUNDARY selected=libtucmodel.a fixed_tmp=0 forbidden=test-asm,test-full,test-compiler,clean executed=0\n'

  set +e; ( false || true ); local fallback_rc=$?; set -e
  [[ $fallback_rc -eq 0 ]]
  printf 'CI_FALLBACK_SYNTHETIC producer_rc=1 propagated_rc=%d unsafe_green=1\n' "$fallback_rc"

  make -C "$WORK" -j2 libtucmodel.a > "$RUN_DIR/build.log" 2>&1
  ar t "$WORK/libtucmodel.a" > "$RUN_DIR/archive-members.log"
  [[ $(wc -l < "$RUN_DIR/archive-members.log") -eq 44 ]]
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
  grep -Fx 'CONFIG_AB ws_parse=0 os_parse=0 ws_df=0 os_df=1 rt_rows=8 rt_cols=4 ws_active=weight_stationary os_active=weight_stationary direct_os=output_stationary' "$RUN_DIR/probe-O0.log"
  grep -Fx 'CORE_REINIT_GEOMETRY created_8x4=1 reinitialized_16x16=1 created_bytes=336 reinitialized_bytes=338' "$RUN_DIR/probe-O0.log"
  grep -Fx 'DUMP_SIZE fixture=post_reinit_16x16 reported=0 actual=338' "$RUN_DIR/probe-O0.log"
  grep -Fx 'REPLAY_NOOP arbitrary_opcode=0xFE mismatches_equal=0 mismatches_mutated=1 output_bytes=69' "$RUN_DIR/probe-O0.log"
  grep -Fx 'BOUNDS_WRAP wrapped_accept=1 ordinary_accept=0' "$RUN_DIR/probe-O0.log"
  grep -Fx 'TILE_PE_IGNORED oversized_accept=1 zero_reject=1' "$RUN_DIR/probe-O0.log"
  grep -Fx 'CH20_PROBE SUMMARY failures=0' "$RUN_DIR/probe-O0.log"
  printf 'PROBE_OPT_STABILITY byte_identical=1\n'

  local config_mut="$WORK_PARENT/config-consumer-mut"
  mkdir "$config_mut"; tar -xf "$WORK_PARENT/tusim.tar" -C "$config_mut"
  python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(); old="tu_set_dataflow(TU_DATAFLOW_MODE);"; new="tu_set_dataflow(TU_DATAFLOW_MODE_OS);"; sys.exit(3) if s.count(old)!=1 else p.write_text(s.replace(old,new))' "$config_mut/tu_cmodel/tu_cmodel.c"
  make -C "$config_mut" -j2 libtucmodel.a > "$RUN_DIR/config-consumer-mutation-build.log" 2>&1
  cc -O0 -g -std=c11 -I"$config_mut" -I"$config_mut/tu_cmodel" -o "$WORK_PARENT/config-mut-probe" "$BOOK_ROOT/experiments/ch20_claim_authorization_probe.c" "$config_mut/libtucmodel.a" -lm
  set +e; "$WORK_PARENT/config-mut-probe" > "$RUN_DIR/config-consumer-mutation.log" 2>&1; local config_mut_rc=$?; set -e
  [[ $config_mut_rc -ne 0 ]]
  grep -F 'os_active=output_stationary' "$RUN_DIR/config-consumer-mutation.log"
  ! grep -Fxq 'CH20_PROBE SUMMARY failures=0' "$RUN_DIR/config-consumer-mutation.log"
  printf 'CONFIG_CONSUMER_MUTATION force_os rejected_rc=%d\n' "$config_mut_rc"

  local san="$WORK_PARENT/sanitized"
  mkdir "$san"; tar -xf "$WORK_PARENT/tusim.tar" -C "$san"
  local sanflags='-O1 -g -Wall -Wextra -std=c11 -fPIC -fno-omit-frame-pointer -fsanitize=address,undefined'
  make -C "$san" -j2 CFLAGS="$sanflags" libtucmodel.a > "$RUN_DIR/build-sanitized.log" 2>&1
  grep -F -- '-fsanitize=address,undefined -c' "$RUN_DIR/build-sanitized.log"
  cc $sanflags -I"$san" -I"$san/tu_cmodel" -o "$WORK_PARENT/ch20-probe-san" "$BOOK_ROOT/experiments/ch20_claim_authorization_probe.c" "$san/libtucmodel.a" -lm
  ASAN_OPTIONS=detect_leaks=0:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 "$WORK_PARENT/ch20-probe-san" > "$RUN_DIR/probe-sanitizer.log" 2> "$RUN_DIR/probe-sanitizer.stderr.log"
  grep -Fx 'CH20_PROBE SUMMARY failures=0' "$RUN_DIR/probe-sanitizer.log"
  ! grep -Eq 'ERROR: AddressSanitizer|runtime error:' "$RUN_DIR/probe-sanitizer.stderr.log"
  printf 'PROBE_SANITIZERS archive_and_probe_address_undefined=PASS leak_check=excluded_global_singleton\n'

  cc -O0 -g -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/test-debug" "$WORK/tests/test_debug.c" "$WORK/libtucmodel.a" -lm
  "$WORK_PARENT/test-debug" > "$RUN_DIR/test-debug.log" 2>&1
  grep -Fx '=== Results: 25/25 passed, 0 failed ===' "$RUN_DIR/test-debug.log"
  cp "$WORK/tests/test_debug.c" "$WORK_PARENT/test-debug-mut.c"
  python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(); old="CHECK(n >= 0, \"dump returned negative\")"; sys.exit(3) if s.count(old)!=2 else p.write_text(s.replace(old,"CHECK(n > 0, \"dump must report bytes\")"))' "$WORK_PARENT/test-debug-mut.c"
  cc -O0 -g -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/test-debug-mut" "$WORK_PARENT/test-debug-mut.c" "$WORK/libtucmodel.a" -lm
  set +e; "$WORK_PARENT/test-debug-mut" > "$RUN_DIR/test-debug-mutation.log" 2>&1; local debug_mut_rc=$?; set -e
  [[ $debug_mut_rc -ne 0 ]]; grep -Fx '=== Results: 23/25 passed, 2 failed ===' "$RUN_DIR/test-debug-mutation.log"
  printf 'DEBUG_MUTATION meaningful_size_gate_rejected_rc=%d\n' "$debug_mut_rc"

  cc -O0 -g -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/test-errors" "$WORK/tests/test_error_handling.c" "$WORK/libtucmodel.a" -lm
  "$WORK_PARENT/test-errors" > "$RUN_DIR/test-errors.log" 2>&1
  grep -Fx '=== Results: 9/9 passed, 0 failed ===' "$RUN_DIR/test-errors.log"
  cp "$WORK/tests/test_error_handling.c" "$WORK_PARENT/test-errors-mut.c"
  python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(); old="tu_error_inject_disable_all();\n\n    tu_clear_error();"; new="tu_error_inject_disable_all();\n    CHECK(rc == TU_ERR_DMA_TIMEOUT, \"injection must be reached\");\n\n    tu_clear_error();"; sys.exit(3) if s.count(old)!=1 else p.write_text(s.replace(old,new))' "$WORK_PARENT/test-errors-mut.c"
  cc -O0 -g -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/test-errors-mut" "$WORK_PARENT/test-errors-mut.c" "$WORK/libtucmodel.a" -lm
  set +e; "$WORK_PARENT/test-errors-mut" > "$RUN_DIR/test-errors-mutation.log" 2>&1; local err_mut_rc=$?; set -e
  [[ $err_mut_rc -ne 0 ]]; grep -Fx '=== Results: 8/9 passed, 1 failed ===' "$RUN_DIR/test-errors-mutation.log"
  printf 'ERROR_INJECTION_MUTATION reached_requirement_rejected_rc=%d\n' "$err_mut_rc"

  cc -O0 -g -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/test-golden" "$WORK/tests/test_golden.c" "$WORK/libtucmodel.a" -lm
  "$WORK_PARENT/test-golden" --quick > "$RUN_DIR/test-golden.log" 2>&1
  grep -Fx '  11/11 tests passed' "$RUN_DIR/test-golden.log"
  cp "$WORK/tests/test_golden.c" "$WORK_PARENT/test-golden-mut.c"
  python3 -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(); old="O[m * N + n] = sum;"; sys.exit(3) if s.count(old)!=1 else p.write_text(s.replace(old,"O[m * N + n] = sum + 1.0f;"))' "$WORK_PARENT/test-golden-mut.c"
  cc -O0 -g -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/test-golden-mut" "$WORK_PARENT/test-golden-mut.c" "$WORK/libtucmodel.a" -lm
  set +e; "$WORK_PARENT/test-golden-mut" --quick > "$RUN_DIR/test-golden-mutation.log" 2>&1; local golden_mut_rc=$?; set -e
  [[ $golden_mut_rc -ne 0 ]]; grep -Fx '  2/11 tests passed' "$RUN_DIR/test-golden-mutation.log"
  printf 'GOLDEN_MUTATION independent_equation_rejected_rc=%d\n' "$golden_mut_rc"

  cc -shared -Wl,-Map="$RUN_DIR/binding-bridge-link.map" -o "$WORK/libtucmodel.so" -Wl,--whole-archive "$WORK/libtucmodel.a" -Wl,--no-whole-archive -lm
  printf 'BINDING_BRIDGE archive_sha256=%s shared_sha256=%s whole_archive=1\n' "$(sha256sum "$WORK/libtucmodel.a"|cut -d' ' -f1)" "$(sha256sum "$WORK/libtucmodel.so"|cut -d' ' -f1)" > "$RUN_DIR/binding-bridge-provenance.log"
  python3 "$BOOK_ROOT/experiments/ch20_boundary_checks.py" "$WORK" | tee "$RUN_DIR/boundary-checks.log"
  grep -Fx 'CH20_BOUNDARY_CHECKS PASS' "$RUN_DIR/boundary-checks.log"
  set +e; CH20_MUTATE_BINDING_EXPECTED=1 python3 "$BOOK_ROOT/experiments/ch20_boundary_checks.py" "$WORK" > "$RUN_DIR/boundary-checks-mutation.log" 2>&1; local boundary_mut_rc=$?; set -e
  [[ $boundary_mut_rc -eq 4 ]]; grep -Fx 'CH20_BOUNDARY_CHECKS REJECT' "$RUN_DIR/boundary-checks-mutation.log"; ! grep -Fxq 'CH20_BOUNDARY_CHECKS PASS' "$RUN_DIR/boundary-checks-mutation.log"
  printf 'BOUNDARY_MUTATION expected_value_rejected_rc=%d\n' "$boundary_mut_rc"

  source_state after_body
  [[ $(git rev-parse HEAD) == "$INPUT_COMMIT" ]]
  [[ $(git branch --show-current) == "$BOOK_BRANCH" ]]
  for rel in "${INPUTS[@]}"; do cmp -s "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel"; done
  local unexpected
  unexpected=$(git status --porcelain=v1 | grep -v "^?? experiments/runs/$RUN_ID/" || true)
  [[ -z $unexpected ]]
  printf 'BOOK_INPUTS unchanged=1 head=%s\n' "$INPUT_COMMIT"
}

set +e
( set -euo pipefail; body ) > "$TRANSCRIPT" 2>&1
body_rc=$?
set -e
tee /dev/null < "$TRANSCRIPT"
[[ $body_rc -eq 0 ]]

CH20_RUN_ID="$RUN_ID" python3 "$BOOK_ROOT/experiments/ch20_predraft_validate.py" --body > "$RUN_DIR/body-validation-normal.log"
CH20_RUN_ID="$RUN_ID" python3 -O "$BOOK_ROOT/experiments/ch20_predraft_validate.py" --body > "$RUN_DIR/body-validation-optimized.log"
cmp -s "$RUN_DIR/body-validation-normal.log" "$RUN_DIR/body-validation-optimized.log"

cp "$RUN_DIR/inputs/notes/chapter-20-source-and-claim-ledger.md" "$WORK_PARENT/frozen-ledger"
printf '\nINPUT_MUTATION\n' >> "$RUN_DIR/inputs/notes/chapter-20-source-and-claim-ledger.md"
for label in normal optimized; do
  set +e
  if [[ $label == normal ]]; then
    CH20_RUN_ID="$RUN_ID" python3 "$BOOK_ROOT/experiments/ch20_predraft_validate.py" --body > "$RUN_DIR/validator-input-mutation-$label.log" 2>&1
  else
    CH20_RUN_ID="$RUN_ID" python3 -O "$BOOK_ROOT/experiments/ch20_predraft_validate.py" --body > "$RUN_DIR/validator-input-mutation-$label.log" 2>&1
  fi
  input_mut_rc=$?
  set -e
  [[ $input_mut_rc -ne 0 ]]
  grep -Fx 'CH20_PREDRAFT_VALIDATION FAIL frozen-vs-commit:notes/chapter-20-source-and-claim-ledger.md' "$RUN_DIR/validator-input-mutation-$label.log"
done
cp "$WORK_PARENT/frozen-ledger" "$RUN_DIR/inputs/notes/chapter-20-source-and-claim-ledger.md"

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
    python3 -c 'from pathlib import Path; print("\n".join(sorted(p.as_posix() for p in Path("inputs").rglob("*") if p.is_file())))'
    printf '%s\n' archive-members.log binding-bridge-link.map binding-bridge-provenance.log body-validation-normal.log body-validation-optimized.log boundary-checks-mutation.log boundary-checks.log build-sanitized.log build.log config-consumer-mutation-build.log config-consumer-mutation.log failure-path-control.log failure-path-summary.log input-hashes.txt input_commit make-dry-run-forbidden.log make-dry-run-selected.log probe-O0-dynamic.log probe-O0.log probe-O0.stderr.log probe-O2-dynamic.log probe-O2.log probe-O2.stderr.log probe-sanitizer.log probe-sanitizer.stderr.log source-audit-hash-mutation.log source-audit-membership-mutation.log source-audit-random-mutation.log source-audit-restored.log source-audit.log source_pin test-debug-mutation.log test-debug.log test-errors-mutation.log test-errors.log test-golden-mutation.log test-golden.log transcript.log validator-assert-mutation-normal.log validator-assert-mutation-optimized.log validator-input-mutation-normal.log validator-input-mutation-optimized.log
  } | LC_ALL=C sort
} > "$RUN_DIR/retained-files.txt"
(
  cd "$RUN_DIR"
  while IFS= read -r rel; do sha256sum "$rel"; done < retained-files.txt
  sha256sum retained-files.txt
) > "$RUN_DIR/sha256-retained.txt"
(cd "$RUN_DIR" && sha256sum -c sha256-retained.txt) > "$RUN_DIR/manifest-check.log"
TRANSCRIPT_SHA=$(sha256sum "$TRANSCRIPT" | cut -d' ' -f1)
printf 'FINALIZED_RUN run=%s transcript_sha256=%s input_commit=%s trust=inner-manifest,outer-root,derived-checks,git-seal\n' "$RUN_ID" "$TRANSCRIPT_SHA" "$INPUT_COMMIT" > "$RUN_DIR/finalization.log"
CH20_RUN_ID="$RUN_ID" python3 "$BOOK_ROOT/experiments/ch20_predraft_validate.py" > "$RUN_DIR/predraft-validation-normal.log"
CH20_RUN_ID="$RUN_ID" python3 -O "$BOOK_ROOT/experiments/ch20_predraft_validate.py" > "$RUN_DIR/predraft-validation-optimized.log"
cmp -s "$RUN_DIR/predraft-validation-normal.log" "$RUN_DIR/predraft-validation-optimized.log"
(
  cd "$RUN_DIR"
  sha256sum sha256-retained.txt manifest-check.log finalization.log predraft-validation-normal.log predraft-validation-optimized.log > bundle-sha256.txt
  sha256sum -c bundle-sha256.txt > bundle-check.log
)
CH20_RUN_ID="$RUN_ID" python3 "$BOOK_ROOT/experiments/ch20_predraft_validate.py" --outer > "$RUN_DIR/closure-validation-normal.log"
CH20_RUN_ID="$RUN_ID" python3 -O "$BOOK_ROOT/experiments/ch20_predraft_validate.py" --outer > "$RUN_DIR/closure-validation-optimized.log"
cmp -s "$RUN_DIR/closure-validation-normal.log" "$RUN_DIR/closure-validation-optimized.log"
grep -Fx "CH20_PREDRAFT_VALIDATION PASS run=$RUN_ID input_commit=$INPUT_COMMIT outer=1" "$RUN_DIR/closure-validation-normal.log"
source_state after_closure
SOURCE_STATE_AFTER_DONE=1
trap - EXIT
rm -rf "$WORK_PARENT"
