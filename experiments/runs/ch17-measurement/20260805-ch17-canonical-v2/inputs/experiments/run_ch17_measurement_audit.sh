#!/usr/bin/env bash
set -euo pipefail
PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
BOOK_ROOT=$(git rev-parse --show-toplevel)
TUSIM_ROOT=${TUSIM_ROOT:-/home/zxy/Workplace/projects/tusim}
RUN_ID=${CH17_RUN_ID:-20260805-ch17-canonical-v2}
RUN_REL=experiments/runs/ch17-measurement/$RUN_ID
RUN_DIR=$BOOK_ROOT/$RUN_REL
INPUT_COMMIT=$(git rev-parse HEAD); BRANCH=$(git branch --show-current)
[[ "$BRANCH" == main ]]; [[ -z "$(git status --porcelain)" ]]; [[ ! -e "$RUN_DIR" ]]
[[ "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" == "$PIN" ]]; ! git -C "$TUSIM_ROOT" symbolic-ref -q HEAD >/dev/null
[[ -z "$(git -C "$TUSIM_ROOT" status --porcelain --untracked-files=all)" ]]
mkdir -p "$RUN_DIR/inputs"; TRANSCRIPT=$RUN_DIR/transcript.log; WORK=$(mktemp -d /tmp/ch17-audit-XXXXXX); trap 'rm -rf "$WORK"' EXIT
INPUTS=(edition.yaml PLAN.md style-guide.md fidelity-matrix.md source-audit.md references/ch17-measurement-primary-sources.md notes/chapter-17-framing-and-evidence-plan.md notes/chapter-17-source-and-claim-ledger.md notes/chapter-17-predraft-source-audit-report.md notes/chapter-17-skeptical-review-dispositions.md experiments/ch17_source_audit.py experiments/ch17_measurement_probe.c experiments/ch17_predraft_validate.py experiments/run_ch17_measurement_audit.sh)
for f in "${INPUTS[@]}"; do mkdir -p "$RUN_DIR/inputs/$(dirname "$f")"; cp "$BOOK_ROOT/$f" "$RUN_DIR/inputs/$f"; done
( cd "$BOOK_ROOT" && sha256sum "${INPUTS[@]}" ) > "$RUN_DIR/input-hashes.txt"
printf '%s\n' "$INPUT_COMMIT" > "$RUN_DIR/input_commit"; printf '%s\n' "$PIN" > "$RUN_DIR/source_pin"
git -C "$TUSIM_ROOT" status --ignored --short --untracked-files=all | sha256sum > "$RUN_DIR/tusim-ignored-before.sha256"
git -C "$TUSIM_ROOT" archive "$PIN" | tar -x -C "$WORK"
body(){
 echo "CH17_AUDIT_START run=$RUN_REL input_commit=$INPUT_COMMIT pin=$PIN"
 echo "TOOLCHAIN host=$(uname -m) cc=$(cc -dumpfullversion -dumpversion) make=$(make --version | head -1) python=$(python3 --version 2>&1)"
 python3 "$BOOK_ROOT/experiments/ch17_source_audit.py" "$WORK" "$PIN" | tee "$RUN_DIR/source-audit.log"
 grep -F "CH17_SOURCE_AUDIT PASS pin=$PIN hashes=31 predicates=80 checks=111" "$RUN_DIR/source-audit.log"
 set +e; python3 "$BOOK_ROOT/experiments/ch17_source_audit.py" "$WORK" 0000000000000000000000000000000000000000 > "$RUN_DIR/source-audit-pin-mutation.log" 2>&1; pin_rc=$?; set -e
 [[ $pin_rc -ne 0 ]]; grep -F "CH17_SOURCE_AUDIT FAIL pin expected=$PIN got=0000000000000000000000000000000000000000" "$RUN_DIR/source-audit-pin-mutation.log"; echo "SOURCE_PIN_MUTATION PASS rc=$pin_rc"
 cp "$WORK/tu_cmodel/perf/performance_counters.c" "$WORK/perf.orig"; printf '\n' >> "$WORK/tu_cmodel/perf/performance_counters.c"
 set +e; python3 "$BOOK_ROOT/experiments/ch17_source_audit.py" "$WORK" "$PIN" > "$RUN_DIR/source-audit-mutation.log" 2>&1; src_rc=$?; set -e
 [[ $src_rc -ne 0 ]]; grep -F "hash mismatch tu_cmodel/perf/performance_counters.c" "$RUN_DIR/source-audit-mutation.log"; mv "$WORK/perf.orig" "$WORK/tu_cmodel/perf/performance_counters.c"
 python3 "$BOOK_ROOT/experiments/ch17_source_audit.py" "$WORK" "$PIN" > "$RUN_DIR/source-audit-restored.log"; grep -F "CH17_SOURCE_AUDIT PASS" "$RUN_DIR/source-audit-restored.log"; echo "SOURCE_HASH_MUTATION PASS rc=$src_rc"
 make -C "$WORK" -j2 libtucmodel.a > "$RUN_DIR/build.log" 2>&1; ar t "$WORK/libtucmodel.a" > "$RUN_DIR/archive-members.log"
 for o in performance_counters.o event_trace.o power_model.o logging.o; do grep -Fx "$o" "$RUN_DIR/archive-members.log"; done; ! grep -Fx cycle_model.o "$RUN_DIR/archive-members.log"
 C=(-std=c11 -O0 -g -Wall -Wextra -I"$WORK" -I"$WORK/tu_cmodel"); cc "${C[@]}" -I"$WORK/tests" -o "$WORK/test-perf" "$WORK/tests/test_perf_counters.c" "$WORK/libtucmodel.a" -lm
 cc "${C[@]}" -o "$WORK/test-trace" "$WORK/tests/test_trace.c" "$WORK/libtucmodel.a" -lm
 cc "${C[@]}" -o "$WORK/test-logging" "$WORK/tests/test_logging.c" "$WORK/libtucmodel.a" -lm
 cc "${C[@]}" -o "$WORK/test-power" "$WORK/tests/test_power_model.c" "$WORK/libtucmodel.a" -lm
 cc "${C[@]}" -o "$WORK/test-cycle" "$WORK/tests/test_cycle_model.c" "$WORK/tu_cmodel/perf/cycle_model.c" "$WORK/libtucmodel.a" -lm
 cc "${C[@]}" -o "$WORK/ch17-probe" "$BOOK_ROOT/experiments/ch17_measurement_probe.c" "$WORK/tu_cmodel/perf/cycle_model.c" "$WORK/libtucmodel.a" -lm
 cc "${C[@]}" -o "$WORK/test-bench" "$WORK/tests/test_benchmark.c" "$WORK/libtucmodel.a" -lm
 for b in test-perf test-trace test-logging test-power test-cycle ch17-probe test-bench; do readelf -d "$WORK/$b" > "$RUN_DIR/$b-readelf.log"; ! grep -Eq 'NEEDED.*libtucmodel' "$RUN_DIR/$b-readelf.log"; done; echo "STATIC_LINK PASS binaries=7"
 "$WORK/test-perf" > "$RUN_DIR/test-perf.log" 2>&1; grep -F "12/12 tests passed" "$RUN_DIR/test-perf.log"; echo "FOCUSED_PERF PASS tests=12"
 "$WORK/test-trace" > "$RUN_DIR/test-trace.log" 2>&1; grep -F "=== Results: 31/31 passed ===" "$RUN_DIR/test-trace.log"; echo "FOCUSED_TRACE PASS tests=31"
 "$WORK/test-logging" > "$RUN_DIR/test-logging.log" 2>&1; grep -F "=== Results: 7 passed, 0 failed ===" "$RUN_DIR/test-logging.log"; echo "FOCUSED_LOGGING PASS tests=7"
 "$WORK/test-power" > "$RUN_DIR/test-power.log" 2>&1; grep -F "Results: 20/20 tests passed" "$RUN_DIR/test-power.log"; echo "FOCUSED_POWER PASS tests=20"
 "$WORK/test-cycle" > "$RUN_DIR/test-cycle.log" 2>&1; grep -F "Tests: 21 run, 21 passed, 0 failed" "$RUN_DIR/test-cycle.log"; echo "FOCUSED_CYCLE PASS tests=21"
 cp "$WORK/tests/test_perf_counters.c" "$WORK/tests/test_perf_counters.mut.c"
 python3 - "$WORK/tests/test_perf_counters.mut.c" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(); old='CHECK(c.total_cycles == 0, "Total cycles should start at 0");'; new='CHECK(c.total_cycles == 1, "Total cycles should start at 0");'; assert s.count(old)==1; p.write_text(s.replace(old,new))
PY
 cc "${C[@]}" -I"$WORK/tests" -o "$WORK/test-perf-mut" "$WORK/tests/test_perf_counters.mut.c" "$WORK/libtucmodel.a" -lm
 set +e; "$WORK/test-perf-mut" > "$RUN_DIR/test-perf-mutation.log" 2>&1; mut_rc=$?; set -e; [[ $mut_rc -ne 0 ]]; grep -F "11/12 tests passed" "$RUN_DIR/test-perf-mutation.log"; echo "FOCUSED_MUTATION PASS tests=11/12 rc=$mut_rc"
 timeout 120 "$WORK/test-bench" > "$RUN_DIR/test-bench.log" 2>&1; grep -F "Benchmark complete." "$RUN_DIR/test-bench.log"; echo "BENCHMARK_QUALIFIED rc=0 no_fail_closed_count=yes"
 "$WORK/ch17-probe" | tee "$RUN_DIR/probe.log"
 grep -F "CH17_PROBE SUMMARY failures=0" "$RUN_DIR/probe.log"
 set +e
 CH17_VALIDATOR_MUTATION=assert-source python3 "$BOOK_ROOT/experiments/ch17_predraft_validate.py" > "$RUN_DIR/validator-mutation-normal.log" 2>&1; vmn_rc=$?
 CH17_VALIDATOR_MUTATION=assert-source python3 -O "$BOOK_ROOT/experiments/ch17_predraft_validate.py" > "$RUN_DIR/validator-mutation-optimized.log" 2>&1; vmo_rc=$?
 set -e
 [[ $vmn_rc -ne 0 && $vmo_rc -ne 0 ]]
 grep -F "CH17_PREDRAFT_VALIDATION FAIL: optimizer-removable assertion in validator" "$RUN_DIR/validator-mutation-normal.log"
 grep -F "CH17_PREDRAFT_VALIDATION FAIL: optimizer-removable assertion in validator" "$RUN_DIR/validator-mutation-optimized.log"
 echo "VALIDATOR_MUTATION PASS normal_rc=$vmn_rc optimized_rc=$vmo_rc"
 echo "CH17_AUDIT_BODY_COMPLETE"
}
set +e; set -o pipefail; body 2>&1 | tee "$TRANSCRIPT"; rc=${PIPESTATUS[0]}; set -e; [[ $rc -eq 0 ]]
[[ "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" == "$PIN" ]]; ! git -C "$TUSIM_ROOT" symbolic-ref -q HEAD >/dev/null; [[ -z "$(git -C "$TUSIM_ROOT" status --porcelain --untracked-files=all)" ]]
git -C "$TUSIM_ROOT" status --ignored --short --untracked-files=all | sha256sum > "$RUN_DIR/tusim-ignored-after.sha256"; cmp -s "$RUN_DIR/tusim-ignored-before.sha256" "$RUN_DIR/tusim-ignored-after.sha256"
[[ "$(git -C "$BOOK_ROOT" rev-parse HEAD)" == "$INPUT_COMMIT" ]]; for f in "${INPUTS[@]}"; do cmp -s "$BOOK_ROOT/$f" "$RUN_DIR/inputs/$f"; done
( cd "$RUN_DIR"; find inputs -type f -print0 | sort -z | xargs -0 sha256sum; sha256sum input-hashes.txt input_commit source_pin tusim-ignored-before.sha256 tusim-ignored-after.sha256 source-audit.log source-audit-pin-mutation.log source-audit-mutation.log source-audit-restored.log build.log archive-members.log *-readelf.log test-perf.log test-trace.log test-logging.log test-power.log test-cycle.log test-perf-mutation.log test-bench.log probe.log validator-mutation-normal.log validator-mutation-optimized.log transcript.log ) > "$RUN_DIR/sha256-retained.txt"
( cd "$RUN_DIR" && sha256sum -c sha256-retained.txt ) > "$RUN_DIR/manifest-check.log"
printf 'FINALIZED_RUN run=%s input_commit=%s transcript_sha256=%s\n' "$RUN_REL" "$INPUT_COMMIT" "$(sha256sum "$TRANSCRIPT"|cut -d' ' -f1)" > "$RUN_DIR/finalization.log"
CH17_RUN_ID="$RUN_ID" python3 "$BOOK_ROOT/experiments/ch17_predraft_validate.py" | tee "$RUN_DIR/predraft-validation.log"
CH17_RUN_ID="$RUN_ID" python3 -O "$BOOK_ROOT/experiments/ch17_predraft_validate.py" | tee -a "$RUN_DIR/predraft-validation.log"
( cd "$RUN_DIR" && sha256sum sha256-retained.txt manifest-check.log finalization.log predraft-validation.log ) > "$RUN_DIR/bundle-sha256.txt"; ( cd "$RUN_DIR" && sha256sum -c bundle-sha256.txt ) > "$RUN_DIR/bundle-check.log"
echo "CH17_RUN_COMPLETE run=$RUN_REL"
