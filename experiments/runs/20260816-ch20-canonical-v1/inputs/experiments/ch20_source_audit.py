#!/usr/bin/env python3
"""Fail-closed Chapter 20 source audit for claim-to-evidence authorization."""
from __future__ import annotations
import hashlib, re, sys
from pathlib import Path
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
EXPECTED_HASHES = {
    ".github/workflows/ci.yml": "0919e0f56293b270d3f4dfd4547840aeec1d300d08d45700b8976b86cf043d85",
    "Makefile": "5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
    "bindings/python/tu_bindings.py": "74562a1c19a47ab8c16e5d92c363a3c3a885c566250eb2fa29434a20851e6740",
    "docs/differential-testing.md": "89e650cd8fa993429020ca53c589c7624a34e52326d70df5e5b7057e774d941f",
    "tests/test_debug.c": "7412ff49960fa6e1b1aac0329362494f2a0dd6631a61667f777d96ea3b94d9eb",
    "tests/test_dpi.c": "0909af36397c2cfecc9be04ca27753a2e8af228e327071af350d5dedfc30ae05",
    "tests/test_error_handling.c": "1c203189c5fc5d55d101bd8834d531b6e504bc04f4744ffd3dd16aa21bbd867a",
    "tests/test_framework.h": "a8bf7f5e2e5ce9c317f1e089bc28338b4bd298a8bec6c08f40c6a5f12bb979ef",
    "tests/test_golden.c": "3399574368c8d25ba3ec0d908402cc8d34936d49f9ef52504b30da9a78558422",
    "tests/test_random.c": "704c1dbd4a2aa648784f00bda8e69ab7efc4e2bf7aec364721c0cc9baa6e41f3",
    "tools/ci_runner.sh": "288f429d8e9fc567269b490c5fe6f41f81ea76b6278da817188fd56894dce0ba",
    "tools/test_report.py": "efe1f995f0fa4f0167e570712a7c945176402487396fed0b6e58a637e45c9851",
    "tu_cmodel/bindings/tu_dpi.c": "51ccaa58f226ed4d67f8b6c96b35a8ce77237980503de93e88335a0077d74b8a",
    "tu_cmodel/bindings/tu_dpi.h": "2d322616199ac02d49265c37b5b95d4c1be9920cd4db018cf9d6744c012e8495",
    "tu_cmodel/infra/config.c": "17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
    "tu_cmodel/infra/config.h": "723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
    "tu_cmodel/infra/random_tensor.h": "ac1e4a55059a0058716b8c91a90eb081540dd22f9776dcbefab0dbb7fe2d98ff",
    "tu_cmodel/infra/tu_debug.c": "20001ec404295e4a4a2ef497a0ace0bb63c8415d4a58858d3172bcb19213dd8d",
    "tu_cmodel/infra/tu_debug.h": "81b32d8051fd1eea1c8aa93c530c8b780f395e778ffdbb350d0040767fbfaca4"
}

def check(name: str, ok: bool, failures: list[str]) -> None:
    print(f"CHECK {name}={'PASS' if ok else 'FAIL'}")
    if not ok: failures.append(name)

def rules(text: str) -> dict[str,str]:
    flat=text.replace("\\\n", " ")
    return {m.group(1):m.group(2).strip() for m in re.finditer(r"(?m)^([A-Za-z0-9_.-]+)\s*:\s*([^\n]*)$", flat)}

def main() -> int:
    if len(sys.argv)!=3:
        print("usage: ch20_source_audit.py ARCHIVE PIN", file=sys.stderr); return 2
    root=Path(sys.argv[1]); pin=sys.argv[2]; failures=[]; checks=0
    check("pin", pin==PIN, failures); checks+=1
    for rel,want in EXPECTED_HASHES.items():
        p=root/rel; got=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "MISSING"
        check("hash:"+rel, got==want, failures); checks+=1
    make=(root/'Makefile').read_text(); ci=(root/'tools/ci_runner.sh').read_text(); report=(root/'tools/test_report.py').read_text()
    framework=(root/'tests/test_framework.h').read_text(); golden=(root/'tests/test_golden.c').read_text(); random=(root/'tests/test_random.c').read_text()
    debug_t=(root/'tests/test_debug.c').read_text(); err_t=(root/'tests/test_error_handling.c').read_text(); dpi_t=(root/'tests/test_dpi.c').read_text()
    dbg=(root/'tu_cmodel/infra/tu_debug.c').read_text(); dbgh=(root/'tu_cmodel/infra/tu_debug.h').read_text(); cfg=(root/'tu_cmodel/infra/config.c').read_text(); cfgh=(root/'tu_cmodel/infra/config.h').read_text(); bind=(root/'bindings/python/tu_bindings.py').read_text(); workflow=(root/'.github/workflows/ci.yml').read_text(); rt=(root/'tu_cmodel/infra/random_tensor.h').read_text()
    rr=rules(make); test_sources=sorted(p.name for p in (root/'tests').glob('test_*.c'))
    source_to_targets={}
    for target,dep in rr.items():
        for s in re.findall(r"tests/(test_[A-Za-z0-9_]+\.c)",dep): source_to_targets.setdefault(s,[]).append(target)
    agg=[x for x in rr['test'].split() if x.startswith('test-')]; quick=[x for x in rr['test-quick'].split() if x.startswith('test-')]
    no_rule=[s for s in test_sources if s not in source_to_targets]
    ciq=re.search(r'if \[ "\$QUICK_MODE" = true \]; then\s*TEST_TARGETS=\((.*?)\)\s*else',ci,re.S)
    cif=re.search(r'else\s*TEST_TARGETS=\((.*?)\)\s*fi',ci,re.S)
    ci_quick=re.findall(r'"(test-[A-Za-z0-9-]+):',ciq.group(1)); ci_full=re.findall(r'"(test-[A-Za-z0-9-]+):',cif.group(1))
    predicates={
      'inventory-64-sources':len(test_sources)==64,
      'inventory-59-source-prerequisites':len(source_to_targets)==59,
      'inventory-31-aggregate':len(agg)==31,
      'inventory-4-quick':len(quick)==4,
      'inventory-five-relation-omissions':no_rule==['test_asm.c','test_cycle_model.c','test_double_buffer.c','test_int8_sweep.c','test_softmax.c'],
      'ci-four-and-fourteen':len(ci_quick)==4 and len(ci_full)==14,
      'workflow-delegates-runner':workflow.count('bash tools/ci_runner.sh')==4,
      'make-suppresses-generated-compile':'/tmp/gpt_block_tu.c -I. -L. -ltucmodel $(LDFLAGS) 2>&1 || true' in make,
      'make-suppresses-generated-run':'/tmp/gpt_block_tu 2>&1 || true' in make,
      'fixed-host-global-paths':'-o /tmp/test_asm' in make and '/tmp/gpt_block_tu.c' in make and 'rm -f /tmp/gpt_block_tu /tmp/gpt_block_tu.c /tmp/test_asm' in make,
      'ci-clean-after-report-dir':ci.index('mkdir -p "$REPORT_DIR" "$LOG_DIR"') < ci.index('make clean'),
      'clean-removes-report-dir':'rm -rf build/ci_reports' in make,
      'quick-golden-status-suppressed':'test-golden > "$local_log" 2>&1 || true' in ci,
      'quick-golden-text-authority':'grep -q "PASS" "$local_log"' in ci,
      'coverage-status-suppressed':'gcov -r tu_cmodel/*.c tu_cmodel/*/*.c > "$LOG_DIR/coverage.log" 2>&1 || true' in ci,
      'coverage-forced-pass':'record_result "Coverage report" "PASS"' in ci,
      'report-exit-absent':'"exit_code": -1' in report and 'result["exit_code"] =' not in report,
      'report-tail-can-override-failure':'if "PASS" in content[-200:] or "passed" in content[-200:].lower()' in report,
      'shared-comparator-nan-blind':'float err = fabsf(a[i] - b[i]);' in framework and 'if (err > max_err) max_err = err;' in framework,
      'golden-local-oracle':'static void compute_fp32_reference' in golden and 'O[m * N + n] = sum;' in golden,
      'random-repository-oracle':'tu_golden_gemm_fp32' in random and 'tu_golden_softmax' in random and 'tu_golden_gemm_fp32' in rt,
      'config-parses-dataflow':'cfg->dataflow_mode = parse_dataflow_str' in cfg,
      'runtime-conversion-drops-dataflow':'rt.pe_rows' in cfg[cfg.index('tu_config_to_runtime'):cfg.index('/* ---- Load from JSON string ---- */')] and 'dataflow' not in cfg[cfg.index('tu_config_to_runtime'):cfg.index('/* ---- Load from JSON string ---- */')],
      'debug-text-json-return-zero':'size_t total = 0;' in dbg and 'return total;' in dbg,
      'debug-tests-use-vacuous-size':debug_t.count('CHECK(n >= 0, "dump returned negative")')==2,
      'debug-checksum-tautology':'CHECK(cs != 0 || cs == 0' in debug_t,
      'replay-header-claims-reissue':'Each instruction is re-issued in order' in dbgh,
      'replay-executes-no-op':'(void)M; (void)N; (void)K;' in dbg and 'Execute the instruction via the core' in dbg,
      'replay-not-tested-execute':'tu_debug_replay_execute' not in debug_t,
      'bounds-addition-can-wrap':'if (addr + size <= limit) return true;' in dbg,
      'debug-invariants-no-external-callers':all(('tests/test_debug.c' in rel or rel.endswith('tu_debug.c') or rel.endswith('tu_debug.h')) for rel in []),
      'error-injection-never-reached':"this won't match" in err_t and 'tu_error_inject_disable_all();' in err_t,
      'dpi-identity-symmetric':'GEMM identity matrix via DPI' in dpi_t,
      'binding-nonsymmetric-capable':'def quick_gemm' in bind,
      'binding-no-make-owner':'test-python' not in rr,
      'binding-full-api-overclaim':'exposes the full TU core API' in bind and 'For now, return stub' in bind,
      'binding-config-path-unused':'self._config_path = config_path' in bind and 'tu_config_load' not in bind,
    }
    # Replace the vacuous placeholder with a whole-tree caller check.
    callers=[]
    for p in root.rglob('*'):
        if p.is_file() and p.suffix in {'.c','.h'} and p.as_posix().split('/tests/')[-1] != p.as_posix():
            pass
    external=[]
    for p in root.rglob('*.c'):
        rel=p.relative_to(root).as_posix()
        if rel in ('tu_cmodel/infra/tu_debug.c','tests/test_debug.c'): continue
        txt=p.read_text(errors='replace')
        if any(x in txt for x in ('tu_debug_record_instr(','tu_debug_replay_execute(','tu_debug_assert_range(','tu_debug_assert_alignment(','tu_debug_assert_bounds(','tu_debug_assert_tile_dims(','tu_debug_assert_dataflow(')): external.append(rel)
    predicates['debug-replay-invariant-external-callers-zero']=external==[]
    del predicates['debug-invariants-no-external-callers']
    for name,ok in predicates.items(): check('predicate:'+name,ok,failures); checks+=1
    print(f"CH20_SOURCE_AUDIT {'PASS' if not failures else 'FAIL'} pin={pin} hashes={len(EXPECTED_HASHES)} predicates={len(predicates)} checks={checks}")
    if failures: print('FAILURES '+' '.join(failures))
    return 0 if not failures else 1
if __name__=='__main__': raise SystemExit(main())
