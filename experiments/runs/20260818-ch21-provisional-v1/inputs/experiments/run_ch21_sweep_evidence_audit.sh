#!/usr/bin/env bash
set -euo pipefail
BOOK_ROOT=$(git rev-parse --show-toplevel)
TUSIM_ROOT=/home/zxy/Workplace/projects/tusim
PIN=e918c80b6fce833cd1fcae97730fa841c2176f25
RUN_ID=${CH21_RUN_ID:-20260818-ch21-provisional-v1}
RUN_DIR="$BOOK_ROOT/experiments/runs/$RUN_ID"
INPUT_COMMIT=$(git rev-parse HEAD)
BOOK_BRANCH=$(git branch --show-current)
WORK_PARENT=$(mktemp -d /tmp/ch21-audit-XXXXXX)
WORK="$WORK_PARENT/src"
TRANSCRIPT="$RUN_DIR/transcript.log"
SOURCE_IGNORED_BEFORE=$(git -C "$TUSIM_ROOT" status --porcelain=v1 --ignored | sha256sum | cut -d' ' -f1)
AFTER_DONE=0
INPUTS=(edition.yaml notes/chapter-21-framing-and-evidence-plan.md notes/chapter-21-framing-review-dispositions.md notes/chapter-21-source-and-claim-ledger.md notes/chapter-21-limitation-register.md notes/chapter-21-worked-decision-schema.json notes/chapter-21-metric-fidelity-register.json notes/chapter-21-predraft-audit-report.md notes/chapter-21-skeptical-predraft-review-dispositions.md references/ch21-sweep-method-primary-sources.md experiments/ch21_source_audit.py experiments/ch21_sweep_probe.c experiments/ch21_formula_probe.py experiments/run_ch21_sweep_evidence_audit.sh experiments/ch21_predraft_validate.py)
source_state(){ local label=$1 head branch status ignored; head=$(git -C "$TUSIM_ROOT" rev-parse HEAD); branch=$(git -C "$TUSIM_ROOT" symbolic-ref -q --short HEAD||true); status=$(git -C "$TUSIM_ROOT" status --porcelain=v1); ignored=$(git -C "$TUSIM_ROOT" status --porcelain=v1 --ignored|sha256sum|cut -d' ' -f1); printf 'SOURCE_STATE %s head=%s detached=%s dirty_entries=%s ignored_hash=%s\n' "$label" "$head" "$([[ -z $branch ]]&&echo 1||echo 0)" "$([[ -z $status ]]&&echo 0||printf '%s\n' "$status"|wc -l)" "$ignored"; [[ $head == "$PIN" && -z $branch && -z $status && $ignored == "$SOURCE_IGNORED_BEFORE" ]]; }
cleanup(){ local rc=$?; if [[ $AFTER_DONE -eq 0 ]];then source_state after||rc=1;fi; rm -rf "$WORK_PARENT"; exit "$rc"; }
trap cleanup EXIT
[[ $BOOK_BRANCH == main ]]; [[ -z $(git status --porcelain=v1) ]]; [[ ! -e $RUN_DIR ]]
source_state preflight >/dev/null
mkdir -p "$RUN_DIR/inputs" "$WORK"
printf '%s\n' "$INPUT_COMMIT" >"$RUN_DIR/input_commit"; printf '%s\n' "$PIN" >"$RUN_DIR/source_pin"
for rel in "${INPUTS[@]}";do mkdir -p "$RUN_DIR/inputs/$(dirname "$rel")";cp "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel";done
(cd "$BOOK_ROOT"&&sha256sum "${INPUTS[@]}") >"$RUN_DIR/input-hashes.txt"
# Early fail-fast control with unconditional source check.
set +e
( set -euo pipefail; source_state before; printf 'INJECT early-inventory-failure\n'; false; printf 'SURVIVED\n' ) >"$RUN_DIR/failure-early.log" 2>&1
rc=$?
source_state after >>"$RUN_DIR/failure-early.log" 2>&1
set -e
[[ $rc -ne 0 ]]; ! grep -Fq SURVIVED "$RUN_DIR/failure-early.log"; [[ $(grep -c '^SOURCE_STATE after ' "$RUN_DIR/failure-early.log") -eq 1 ]]
printf 'FAILURE_EARLY rejected_rc=%d source_after_unique=1\n' "$rc" >"$RUN_DIR/failure-early-summary.log"
git -C "$TUSIM_ROOT" archive --format=tar --output="$WORK_PARENT/tusim.tar" "$PIN";tar -xf "$WORK_PARENT/tusim.tar" -C "$WORK"
body(){
 source_state before
 printf 'BOOK_STATE head=%s branch=%s clean=1\n' "$INPUT_COMMIT" "$BOOK_BRANCH"
 printf 'TOOLCHAIN host=%s cc=%s make=%s python=%s locale=%s\n' "$(uname -m)" "$(cc --version|head -1)" "$(make --version|head -1)" "$(python3 --version)" "${LC_ALL:-C}"
 printf '%s\n' "git archive $PIN" "make -j2 libtucmodel.a" "cc -O0/-O2 ch21_sweep_probe.c libtucmodel.a -lm" "python3 scripts/sweep_aspect_ratio.py" "python3 ch21_formula_probe.py" >"$RUN_DIR/commands.txt"
 printf 'host=%s\ncc=%s\nmake=%s\npython=%s\nlocale=C\nsource_pin=%s\n' "$(uname -m)" "$(cc --version|head -1)" "$(make --version|head -1)" "$(python3 --version)" "$PIN" >"$RUN_DIR/environment.txt"
 python3 "$BOOK_ROOT/experiments/ch21_source_audit.py" "$WORK" "$PIN" "$RUN_DIR/inventory.json" | tee "$RUN_DIR/source-audit.log"
 grep -Fx "CH21_SOURCE_AUDIT PASS pin=$PIN hashes=17 predicates=20 checks=38" "$RUN_DIR/source-audit.log"
 cp "$WORK/tu_cmodel/tu_core.c" "$WORK_PARENT/core.orig";printf '\n' >>"$WORK/tu_cmodel/tu_core.c"
 set +e;python3 "$BOOK_ROOT/experiments/ch21_source_audit.py" "$WORK" "$PIN" >"$RUN_DIR/source-audit-hash-mutation.log" 2>&1;local hrc=$?;set -e
 [[ $hrc -ne 0 ]];grep -F 'CHECK hash:tu_cmodel/tu_core.c=FAIL' "$RUN_DIR/source-audit-hash-mutation.log";cp "$WORK_PARENT/core.orig" "$WORK/tu_cmodel/tu_core.c"
 python3 "$BOOK_ROOT/experiments/ch21_source_audit.py" "$WORK" "$PIN" >"$RUN_DIR/source-audit-restored.log";grep -Fx "CH21_SOURCE_AUDIT PASS pin=$PIN hashes=17 predicates=20 checks=38" "$RUN_DIR/source-audit-restored.log";printf 'SOURCE_HASH_MUTATION rejected=1 restored=1\n'
 # Same-count source/target rewire with rebound Make hash.
 local rel="$WORK_PARENT/relation";mkdir "$rel";tar -xf "$WORK_PARENT/tusim.tar" -C "$rel"
 python3 -c 'from pathlib import Path;import sys;p=Path(sys.argv[1]);s=p.read_text();a="test-bench: tests/test_benchmark.c libtucmodel.a";b="test-conv-pool-cascade: tests/test_conv_pool_cascade.c libtucmodel.a";assert s.count(a)==s.count(b)==1;p.write_text(s.replace(a,"test-bench: tests/test_conv_pool_cascade.c libtucmodel.a").replace(b,"test-conv-pool-cascade: tests/test_benchmark.c libtucmodel.a"))' "$rel/Makefile"
 local mh;mh=$(sha256sum "$rel/Makefile"|cut -d' ' -f1);cp "$BOOK_ROOT/experiments/ch21_source_audit.py" "$WORK_PARENT/rel-audit.py";python3 -c 'from pathlib import Path;import sys;p=Path(sys.argv[1]);s=p.read_text();old=sys.argv[2];new=sys.argv[3];assert s.count(old)==1;p.write_text(s.replace(old,new))' "$WORK_PARENT/rel-audit.py" 5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2 "$mh"
 set +e;python3 "$WORK_PARENT/rel-audit.py" "$rel" "$PIN" >"$RUN_DIR/relation-mutation.log" 2>&1;local rrc=$?;set -e
 [[ $rrc -ne 0 ]];grep -F 'CHECK predicate:exact-22-source-target-pairs=FAIL' "$RUN_DIR/relation-mutation.log";printf 'RELATION_MUTATION count_preserved=22 rejected=1\n'
 make -C "$WORK" -j2 libtucmodel.a >"$RUN_DIR/build.log" 2>&1;ar t "$WORK/libtucmodel.a" >"$RUN_DIR/archive-members.log";[[ $(wc -l <"$RUN_DIR/archive-members.log") -eq 44 ]]
 for opt in O0 O2;do cc -"$opt" -g -Wall -Wextra -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/probe-$opt" "$BOOK_ROOT/experiments/ch21_sweep_probe.c" "$WORK/libtucmodel.a" -lm;readelf -d "$WORK_PARENT/probe-$opt" >"$RUN_DIR/probe-$opt-dynamic.log";! grep -Eq 'NEEDED.*libtucmodel' "$RUN_DIR/probe-$opt-dynamic.log";"$WORK_PARENT/probe-$opt" >"$RUN_DIR/probe-$opt.log" 2>"$RUN_DIR/probe-$opt.stderr.log";done
 cmp -s "$RUN_DIR/probe-O0.log" "$RUN_DIR/probe-O2.log";grep -Fx 'CH21_SWEEP_PROBE SUMMARY failures=0' "$RUN_DIR/probe-O0.log";printf 'PROBE_OPT_STABILITY byte_identical=1\n'
 cp "$BOOK_ROOT/experiments/ch21_sweep_probe.c" "$WORK_PARENT/route-mut.c";python3 -c 'from pathlib import Path;import sys;p=Path(sys.argv[1]);s=p.read_text();old="requested_label=output_stationary";assert s.count(old)==1;p.write_text(s.replace(old,"requested_label=row_stationary"))' "$WORK_PARENT/route-mut.c";cc -O0 -std=c11 -I"$WORK" -I"$WORK/tu_cmodel" -o "$WORK_PARENT/route-mut" "$WORK_PARENT/route-mut.c" "$WORK/libtucmodel.a" -lm;"$WORK_PARENT/route-mut" >"$RUN_DIR/probe-route-mutation.log" 2>&1;! grep -Fxq 'DATAFLOW_ROUTE requested_label=output_stationary process_global_before=1 core_snapshot_before=0 core_snapshot_after=0 effective_core=weight_stationary' "$RUN_DIR/probe-route-mutation.log";printf 'ROUTE_MUTATION requested_label_permutation_rejected=1\n'
 python3 "$WORK/scripts/sweep_aspect_ratio.py" >"$RUN_DIR/aspect-raw.log";grep -Fx '**Configs tested:** 120' "$RUN_DIR/aspect-raw.log";[[ $(grep -Ec '^\| [0-9]+ \| [0-9]+ \| [0-9]+ \|' "$RUN_DIR/aspect-raw.log") -eq 120 ]];[[ $(grep -Ec '^\| [0-9]+ \| [0-9]+ \| [0-9]+×[0-9]+ \|' "$RUN_DIR/aspect-raw.log") -eq 8 ]]
 python3 "$BOOK_ROOT/experiments/ch21_formula_probe.py" "$WORK_PARENT/formula" | tee "$RUN_DIR/formula.log";cp "$WORK_PARENT/formula/"* "$RUN_DIR/"
 printf 'ASPECT_REPRO raw_rows=120 stale_report_counterexample=1\n'
 cp "$BOOK_ROOT/experiments/ch21_formula_probe.py" "$WORK_PARENT/formula-mut.py";python3 -c 'from pathlib import Path;import sys;p=Path(sys.argv[1]);s=p.read_text();old="dma=math.ceil((M*K+K*N+M*N)*2/bus)";assert s.count(old)==2;p.write_text(s.replace(old,old+"+1",1))' "$WORK_PARENT/formula-mut.py";set +e;python3 "$WORK_PARENT/formula-mut.py" "$WORK_PARENT/fmut" >"$RUN_DIR/formula-mutation.log" 2>&1;local frc=$?;set -e;[[ $frc -ne 0 ]];grep -F 'CH21_FORMULA_PROBE REJECT' "$RUN_DIR/formula-mutation.log";printf 'FORMULA_MUTATION stale_axis_rejected=1\n'
 cp "$RUN_DIR/formula.log" "$WORK_PARENT/status-mut";python3 -c 'from pathlib import Path;import sys;p=Path(sys.argv[1]);s=p.read_text();p.write_text(s.replace("CH21_FORMULA_PROBE PASS\n",""))' "$WORK_PARENT/status-mut";set +e;grep -Fx 'CH21_FORMULA_PROBE PASS' "$WORK_PARENT/status-mut" >"$RUN_DIR/status-mutation.log" 2>&1;local src=$?;set -e;[[ $src -ne 0 ]];printf 'STATUS_MUTATION missing_completion_rejected=1\n'
 python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));r=d["required_fields"];c=d["worked_cases"];assert len(r)==13 and len(c)==4 and all(set(r)<=set(x) for x in c);print("DECISION_SCHEMA cases=4 required_fields=13")' "$BOOK_ROOT/notes/chapter-21-worked-decision-schema.json" | tee "$RUN_DIR/decision-schema-check.log"
 cp "$BOOK_ROOT/notes/chapter-21-metric-fidelity-register.json" "$RUN_DIR/metric-register.json"
 source_state after_body
 [[ $(git rev-parse HEAD) == "$INPUT_COMMIT" && $(git branch --show-current) == main ]];for rel in "${INPUTS[@]}";do cmp -s "$BOOK_ROOT/$rel" "$RUN_DIR/inputs/$rel";done;local unexpected;unexpected=$(git status --porcelain=v1|grep -v "^?? experiments/runs/$RUN_ID/"||true);[[ -z $unexpected ]];printf 'BOOK_INPUTS unchanged=1 head=%s\n' "$INPUT_COMMIT"
}
set +e;(set -euo pipefail;body) >"$TRANSCRIPT" 2>&1;body_rc=$?;set -e;tee /dev/null <"$TRANSCRIPT";[[ $body_rc -eq 0 ]]
CH21_RUN_ID="$RUN_ID" python3 experiments/ch21_predraft_validate.py --body >"$RUN_DIR/body-validation-normal.log";CH21_RUN_ID="$RUN_ID" python3 -O experiments/ch21_predraft_validate.py --body >"$RUN_DIR/body-validation-optimized.log";cmp -s "$RUN_DIR/body-validation-normal.log" "$RUN_DIR/body-validation-optimized.log"
# Frozen-input and validator-AST controls, each with source-state proof after failure.
cp "$RUN_DIR/inputs/notes/chapter-21-source-and-claim-ledger.md" "$WORK_PARENT/ledger";printf '\nMUTATION\n' >>"$RUN_DIR/inputs/notes/chapter-21-source-and-claim-ledger.md"
for mode in normal optimized;do set +e;if [[ $mode == normal ]];then CH21_RUN_ID="$RUN_ID" python3 experiments/ch21_predraft_validate.py --body >"$RUN_DIR/validator-input-mutation-$mode.log" 2>&1;else CH21_RUN_ID="$RUN_ID" python3 -O experiments/ch21_predraft_validate.py --body >"$RUN_DIR/validator-input-mutation-$mode.log" 2>&1;fi;vrc=$?;set -e;[[ $vrc -ne 0 ]];source_state after >>"$RUN_DIR/validator-input-mutation-$mode.log";done;cp "$WORK_PARENT/ledger" "$RUN_DIR/inputs/notes/chapter-21-source-and-claim-ledger.md"
cp experiments/ch21_predraft_validate.py "$WORK_PARENT/validator-mut.py";printf '\nassert(False)\n' >>"$WORK_PARENT/validator-mut.py"
for mode in normal optimized;do set +e;if [[ $mode == normal ]];then CH21_RUN_ID="$RUN_ID" python3 "$WORK_PARENT/validator-mut.py" --body >"$RUN_DIR/validator-assert-mutation-$mode.log" 2>&1;else CH21_RUN_ID="$RUN_ID" python3 -O "$WORK_PARENT/validator-mut.py" --body >"$RUN_DIR/validator-assert-mutation-$mode.log" 2>&1;fi;vrc=$?;set -e;[[ $vrc -ne 0 ]];grep -F 'CH21_PREDRAFT_VALIDATION FAIL validator-contains-assert' "$RUN_DIR/validator-assert-mutation-$mode.log";source_state after >>"$RUN_DIR/validator-assert-mutation-$mode.log";done
# Inject a checksum-manifest failure before sealing and prove source state afterward.
printf '%064d  source_pin\n' 0 >"$WORK_PARENT/bad-manifest";set +e;(cd "$RUN_DIR"&&sha256sum -c "$WORK_PARENT/bad-manifest") >"$RUN_DIR/manifest-failure.log" 2>&1;mrc=$?;set -e;[[ $mrc -ne 0 ]];source_state after >>"$RUN_DIR/manifest-failure.log";grep -F 'FAILED' "$RUN_DIR/manifest-failure.log"
{ for rel in "${INPUTS[@]}";do printf 'inputs/%s\n' "$rel";done;printf '%s\n' archive-members.log aspect-raw.log aspect-rows.csv body-validation-normal.log body-validation-optimized.log build.log commands.txt decision-schema-check.log environment.txt failure-early.log failure-early-summary.log formula-mutation.log formula-results.json formula.log input-hashes.txt input_commit inventory.json manifest-failure.log metric-register.json probe-O0-dynamic.log probe-O0.log probe-O0.stderr.log probe-O2-dynamic.log probe-O2.log probe-O2.stderr.log probe-route-mutation.log relation-mutation.log sensitivity-rows.csv source-audit-hash-mutation.log source-audit-restored.log source-audit.log source_pin status-mutation.log transcript.log validator-assert-mutation-normal.log validator-assert-mutation-optimized.log validator-input-mutation-normal.log validator-input-mutation-optimized.log; }|LC_ALL=C sort >"$RUN_DIR/retained-files.txt"
(cd "$RUN_DIR";while read -r rel;do sha256sum "$rel";done <retained-files.txt;sha256sum retained-files.txt)>"$RUN_DIR/sha256-retained.txt";(cd "$RUN_DIR"&&sha256sum -c sha256-retained.txt)>"$RUN_DIR/manifest-check.log"
printf 'FINALIZED_RUN run=%s transcript_sha256=%s input_commit=%s trust=inner-manifest,outer-root,derived-checks,git-seal\n' "$RUN_ID" "$(sha256sum "$TRANSCRIPT"|cut -d' ' -f1)" "$INPUT_COMMIT" >"$RUN_DIR/finalization.log"
CH21_RUN_ID="$RUN_ID" python3 experiments/ch21_predraft_validate.py >"$RUN_DIR/predraft-validation-normal.log";CH21_RUN_ID="$RUN_ID" python3 -O experiments/ch21_predraft_validate.py >"$RUN_DIR/predraft-validation-optimized.log";cmp -s "$RUN_DIR/predraft-validation-normal.log" "$RUN_DIR/predraft-validation-optimized.log"
(cd "$RUN_DIR";sha256sum sha256-retained.txt manifest-check.log finalization.log predraft-validation-normal.log predraft-validation-optimized.log >bundle-sha256.txt;sha256sum -c bundle-sha256.txt >bundle-check.log)
CH21_RUN_ID="$RUN_ID" python3 experiments/ch21_predraft_validate.py --outer >"$RUN_DIR/closure-validation-normal.log";CH21_RUN_ID="$RUN_ID" python3 -O experiments/ch21_predraft_validate.py --outer >"$RUN_DIR/closure-validation-optimized.log";cmp -s "$RUN_DIR/closure-validation-normal.log" "$RUN_DIR/closure-validation-optimized.log"
source_state after_closure;AFTER_DONE=1;trap - EXIT;rm -rf "$WORK_PARENT"
