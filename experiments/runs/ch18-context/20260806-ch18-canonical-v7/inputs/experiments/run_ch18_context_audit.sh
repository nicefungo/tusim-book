#!/usr/bin/env bash
set -euo pipefail
PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
BOOK_ROOT=$(git rev-parse --show-toplevel)
TUSIM_ROOT=${TUSIM_ROOT:-/home/zxy/Workplace/projects/tusim}
RUN_ID=${CH18_RUN_ID:-20260805-ch18-canonical-v5}
RUN_REL=experiments/runs/ch18-context/$RUN_ID
RUN_DIR=$BOOK_ROOT/$RUN_REL
INPUT_COMMIT=$(git rev-parse HEAD)
BRANCH=$(git branch --show-current)
[[ "$BRANCH" == main ]]
[[ -z "$(git status --porcelain --untracked-files=all)" ]]
[[ ! -e "$RUN_DIR" ]]
[[ "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" == "$PIN" ]]
! git -C "$TUSIM_ROOT" symbolic-ref -q HEAD >/dev/null
[[ -z "$(git -C "$TUSIM_ROOT" status --porcelain --untracked-files=all)" ]]
mkdir -p "$RUN_DIR/inputs"
TRANSCRIPT=$RUN_DIR/transcript.log
WORK=$(mktemp -d /tmp/ch18-audit-XXXXXX)
trap 'rm -rf "$WORK"' EXIT
INPUTS=(edition.yaml PLAN.md style-guide.md fidelity-matrix.md source-audit.md notes/chapter-18-framing-and-evidence-plan.md notes/chapter-18-framing-review-dispositions.md experiments/ch18_framing_reproduce.sh notes/chapter-18-framing-reproduction.log notes/chapter-18-source-and-claim-ledger.md notes/chapter-18-predraft-source-audit-report.md notes/chapter-18-skeptical-review-dispositions.md experiments/ch18_source_audit.py experiments/ch18_context_probe.c experiments/ch18_predraft_validate.py experiments/run_ch18_context_audit.sh)
for f in "${INPUTS[@]}"; do mkdir -p "$RUN_DIR/inputs/$(dirname "$f")"; cp "$BOOK_ROOT/$f" "$RUN_DIR/inputs/$f"; done
( cd "$BOOK_ROOT" && sha256sum "${INPUTS[@]}" ) > "$RUN_DIR/input-hashes.txt"
printf '%s\n' "$INPUT_COMMIT" > "$RUN_DIR/input_commit"
printf '%s\n' "$PIN" > "$RUN_DIR/source_pin"
git -C "$TUSIM_ROOT" status --ignored --short --untracked-files=all | sha256sum > "$RUN_DIR/tusim-ignored-before.sha256"
git -C "$TUSIM_ROOT" archive --format=tar --output="$WORK/source.tar" "$PIN"
tar -xf "$WORK/source.tar" -C "$WORK"
rm "$WORK/source.tar"
body(){
 echo "CH18_AUDIT_START run=$RUN_REL input_commit=$INPUT_COMMIT pin=$PIN"
 ccver=$(cc --version | python3 -c 'import sys; print(sys.stdin.readline().strip())')
 mkver=$(make --version | python3 -c 'import sys; print(sys.stdin.readline().strip())')
 echo "TOOLCHAIN host=$(uname -m) cc=$ccver make=$mkver python=$(python3 --version 2>&1)"
 python3 "$BOOK_ROOT/experiments/ch18_source_audit.py" "$WORK" "$PIN" | tee "$RUN_DIR/source-audit.log"
 grep -F "CH18_SOURCE_AUDIT PASS pin=$PIN hashes=39 predicates=171 checks=210" "$RUN_DIR/source-audit.log"
 set +e
 python3 "$BOOK_ROOT/experiments/ch18_source_audit.py" "$WORK" 0000000000000000000000000000000000000000 > "$RUN_DIR/source-audit-pin-mutation.log" 2>&1
 pin_rc=$?
 set -e
 [[ $pin_rc -ne 0 ]]
 grep -F "CH18_SOURCE_AUDIT FAIL pin expected=$PIN got=0000000000000000000000000000000000000000" "$RUN_DIR/source-audit-pin-mutation.log"
 echo "SOURCE_PIN_MUTATION PASS rc=$pin_rc"
 cp "$WORK/tu_cmodel/infra/tu_context.c" "$WORK/tu_context.orig"
 printf '\n' >> "$WORK/tu_cmodel/infra/tu_context.c"
 set +e
 python3 "$BOOK_ROOT/experiments/ch18_source_audit.py" "$WORK" "$PIN" > "$RUN_DIR/source-audit-mutation.log" 2>&1
 src_rc=$?
 set -e
 [[ $src_rc -ne 0 ]]
 grep -F "hash mismatch tu_cmodel/infra/tu_context.c" "$RUN_DIR/source-audit-mutation.log"
 mv "$WORK/tu_context.orig" "$WORK/tu_cmodel/infra/tu_context.c"
 python3 "$BOOK_ROOT/experiments/ch18_source_audit.py" "$WORK" "$PIN" > "$RUN_DIR/source-audit-restored.log"
 grep -F "CH18_SOURCE_AUDIT PASS" "$RUN_DIR/source-audit-restored.log"
 echo "SOURCE_HASH_MUTATION PASS rc=$src_rc"
 make -C "$WORK" -j2 libtucmodel.a > "$RUN_DIR/build.log" 2>&1
 ar t "$WORK/libtucmodel.a" > "$RUN_DIR/archive-members.log"
 grep -Fx "tu_context.o" "$RUN_DIR/archive-members.log"
 C=(-std=c11 -O0 -g -Wall -Wextra -I"$WORK" -I"$WORK/tu_cmodel" -I"$WORK/tests")
 cc "${C[@]}" -o "$WORK/test-context" "$WORK/tests/test_context.c" "$WORK/libtucmodel.a" -lm
 cc "${C[@]}" -o "$WORK/test-context-sweep" "$WORK/tests/test_context_switch_sweep.c" "$WORK/libtucmodel.a" -lm
 cc "${C[@]}" -o "$WORK/ch18-probe" "$BOOK_ROOT/experiments/ch18_context_probe.c" "$WORK/libtucmodel.a" -Wl,--wrap=malloc -lm
 cc -std=c11 -O2 -Wall -Wextra -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK/ch18-probe-o2" "$BOOK_ROOT/experiments/ch18_context_probe.c" "$WORK/libtucmodel.a" -Wl,--wrap=malloc -lm
 cc -std=c11 -O1 -g -Wall -Wextra -fsanitize=address,undefined -fno-omit-frame-pointer -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK/ch18-probe-san" "$BOOK_ROOT/experiments/ch18_context_probe.c" "$WORK/libtucmodel.a" -Wl,--wrap=malloc -lm
 cp "$WORK/tests/test_context.c" "$WORK/tests/test_context.mut.c"
 python3 - "$WORK/tests/test_context.mut.c" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
old='CHECK(g_mgr != NULL, "ctx manager should be created");'
new='CHECK(g_mgr == NULL, "MUTATION: ctx manager should be absent");'
if s.count(old)!=1: raise SystemExit('focused mutation anchor mismatch')
p.write_text(s.replace(old,new))
PY
 cc "${C[@]}" -o "$WORK/test-context-mut" "$WORK/tests/test_context.mut.c" "$WORK/libtucmodel.a" -lm
 for b in test-context test-context-mut test-context-sweep ch18-probe ch18-probe-o2 ch18-probe-san; do
   readelf -d "$WORK/$b" > "$RUN_DIR/$b-readelf.log"
   ! grep -Eq 'NEEDED.*libtucmodel' "$RUN_DIR/$b-readelf.log"
 done
 echo "STATIC_LINK PASS binaries=6"
 timeout 30s "$WORK/test-context" > "$RUN_DIR/test-context.log" 2>&1
 grep -F "15/15 tests passed" "$RUN_DIR/test-context.log"
 echo "FOCUSED_CONTEXT PASS tests=15"
 set +e
 timeout 30s "$WORK/test-context-mut" > "$RUN_DIR/test-context-mutation.log" 2>&1
 mut_rc=$?
 set -e
 [[ $mut_rc -ne 0 ]]
 grep -F "14/15 tests passed" "$RUN_DIR/test-context-mutation.log"
 echo "FOCUSED_MUTATION PASS tests=14/15 rc=$mut_rc"
 timeout 30s "$WORK/test-context-sweep" > "$RUN_DIR/test-context-sweep.log" 2>&1
 for row in '128 full      131072          8292' '128 live25     32768          2148' '128 control        0           100' '256 full      262144         16484' '256 live25     65536          4196' '256 control        0           100' '512 full      524288         32868' '512 live25    131072          8292' '512 control        0           100' '16         32868' '32         16484' '64          8292'; do grep -F "$row" "$RUN_DIR/test-context-sweep.log"; done
 echo "SWEEP PASS rows=12"
 timeout 30s "$WORK/ch18-probe" > "$RUN_DIR/probe.log" 2>"$RUN_DIR/probe.stderr.log"
 timeout 30s "$WORK/ch18-probe-o2" > "$RUN_DIR/probe-o2.log" 2>"$RUN_DIR/probe-o2.stderr.log"
 ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 timeout 30s "$WORK/ch18-probe-san" > "$RUN_DIR/probe-san.log" 2> "$RUN_DIR/sanitizer.log"
 grep -F "CH18_PROBE SUMMARY failures=0" "$RUN_DIR/probe.log"
 grep -F "CH18_PROBE SUMMARY failures=0" "$RUN_DIR/probe-o2.log"
 cmp -s "$RUN_DIR/probe.log" "$RUN_DIR/probe-o2.log"
 cmp -s "$RUN_DIR/probe.log" "$RUN_DIR/probe-san.log"
 ! grep -Eq 'ERROR: AddressSanitizer|SUMMARY: AddressSanitizer|runtime error:' "$RUN_DIR/sanitizer.log"
 echo "PROBE PASS failures=0 probe_translation_unit_O0_O2_match=yes sanitizer_clean=yes bounded=yes"
 cp "$BOOK_ROOT/experiments/ch18_predraft_validate.py" "$WORK/ch18-predraft-validator-mutated.py"
 printf '\nassert(False)\n' >> "$WORK/ch18-predraft-validator-mutated.py"
 set +e
 python3 "$WORK/ch18-predraft-validator-mutated.py" > "$RUN_DIR/validator-mutation-normal.log" 2>&1
 vmn_rc=$?
 python3 -O "$WORK/ch18-predraft-validator-mutated.py" > "$RUN_DIR/validator-mutation-optimized.log" 2>&1
 vmo_rc=$?
 set -e
 [[ $vmn_rc -ne 0 && $vmo_rc -ne 0 ]]
 grep -F "CH18_PREDRAFT_VALIDATION FAIL: optimizer-removable assertion in validator" "$RUN_DIR/validator-mutation-normal.log"
 grep -F "CH18_PREDRAFT_VALIDATION FAIL: optimizer-removable assertion in validator" "$RUN_DIR/validator-mutation-optimized.log"
 echo "VALIDATOR_MUTATION PASS normal_rc=$vmn_rc optimized_rc=$vmo_rc"
 echo "CH18_AUDIT_BODY_COMPLETE"
}
set +e
set -o pipefail
body 2>&1 | tee "$TRANSCRIPT"
rc=${PIPESTATUS[0]}
set -e
[[ $rc -eq 0 ]]
[[ "$(git -C "$TUSIM_ROOT" rev-parse HEAD)" == "$PIN" ]]
! git -C "$TUSIM_ROOT" symbolic-ref -q HEAD >/dev/null
[[ -z "$(git -C "$TUSIM_ROOT" status --porcelain --untracked-files=all)" ]]
git -C "$TUSIM_ROOT" status --ignored --short --untracked-files=all | sha256sum > "$RUN_DIR/tusim-ignored-after.sha256"
cmp -s "$RUN_DIR/tusim-ignored-before.sha256" "$RUN_DIR/tusim-ignored-after.sha256"
[[ "$(git -C "$BOOK_ROOT" rev-parse HEAD)" == "$INPUT_COMMIT" ]]
for f in "${INPUTS[@]}"; do cmp -s "$BOOK_ROOT/$f" "$RUN_DIR/inputs/$f"; done
python3 - "$BOOK_ROOT" "$RUN_REL" <<'PY'
import subprocess,sys
root,run=sys.argv[1:]
lines=subprocess.run(['git','-C',root,'status','--porcelain','--untracked-files=all'],capture_output=True,text=True,check=True).stdout.splitlines()
bad=[x for x in lines if not x[3:].startswith(run+'/')]
if bad: raise SystemExit('book changed outside run: '+repr(bad))
PY
python3 - "$RUN_DIR" "${INPUTS[@]}" <<'PY' > "$RUN_DIR/sha256-retained.txt"
from pathlib import Path
import hashlib,sys
run=Path(sys.argv[1]); inputs=sys.argv[2:]
rels=['inputs/'+x for x in inputs]
rels += ['input-hashes.txt','input_commit','source_pin','tusim-ignored-before.sha256','tusim-ignored-after.sha256','source-audit.log','source-audit-pin-mutation.log','source-audit-mutation.log','source-audit-restored.log','build.log','archive-members.log','test-context-readelf.log','test-context-mut-readelf.log','test-context-sweep-readelf.log','ch18-probe-readelf.log','ch18-probe-o2-readelf.log','ch18-probe-san-readelf.log','test-context.log','test-context-mutation.log','test-context-sweep.log','probe.log','probe-o2.log','probe-san.log','probe.stderr.log','probe-o2.stderr.log','sanitizer.log','validator-mutation-normal.log','validator-mutation-optimized.log','transcript.log']
for rel in rels:
 p=run/rel
 if not p.is_file(): raise SystemExit('missing retained '+rel)
 print(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+rel)
PY
( cd "$RUN_DIR" && sha256sum -c sha256-retained.txt ) > "$RUN_DIR/manifest-check.log"
printf 'FINALIZED_RUN run=%s input_commit=%s transcript_sha256=%s\n' "$RUN_REL" "$INPUT_COMMIT" "$(sha256sum "$TRANSCRIPT"|cut -d' ' -f1)" > "$RUN_DIR/finalization.log"
CH18_RUN_ID="$RUN_ID" python3 "$BOOK_ROOT/experiments/ch18_predraft_validate.py" | tee "$RUN_DIR/predraft-validation.log"
CH18_RUN_ID="$RUN_ID" python3 -O "$BOOK_ROOT/experiments/ch18_predraft_validate.py" | tee -a "$RUN_DIR/predraft-validation.log"
( cd "$RUN_DIR" && sha256sum sha256-retained.txt manifest-check.log finalization.log predraft-validation.log ) > "$RUN_DIR/bundle-sha256.txt"
( cd "$RUN_DIR" && sha256sum -c bundle-sha256.txt ) > "$RUN_DIR/bundle-check.log"
echo "CH18_RUN_COMPLETE run=$RUN_REL"
