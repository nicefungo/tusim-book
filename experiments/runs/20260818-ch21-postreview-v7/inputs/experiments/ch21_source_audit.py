#!/usr/bin/env python3
"""Fail-closed Chapter 21 audit of sweep relations and worked evidence surfaces."""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
HASHES = {
    "Makefile": "5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
    "scripts/sweep_aspect_ratio.py": "7e4f8207c3ec3854f3efb3a3caa02bbd48856d9ea5608198f596c11d79948db2",
    "tests/test_dataflow_sweep.c": "4b3dc2da732f4efa25ec250bfb76e3507bd07168a73a703350150228077f57e6",
    "tests/test_rounding_sweep.c": "f53a5de4a2ff210b156f21c6b03b3a0f077bac6182774456d58135a51cb0e3f2",
    "tests/test_context_switch_sweep.c": "a6c50ea702490df03dcbe653b3f82601fc05807cbee8b5d068fb03c0dccae76a",
    "tests/test_int8_sweep.c": "fa4db1454b4fd24dc2c36d30b1268805d97216f55cb2641924cf0cded3ab2bf2",
    "tests/test_interconnect_topology_sweep.c": "1222f166b8bf45248e8ed8ca57cbd47452471dad994bda754558089b4bdb24ee",
    "tests/test_mma_activation_sweep.c": "67ee510868c6ec13b78d45e261fbd1be4c56bc57e58a30679cc653897bb7da72",
    "tu_cmodel/tu_core.c": "0e4b3c6e206465748ae2d3d2e9871f3a6542a61cd1ddcddfff6886b9ed1f0eeb",
    "tu_cmodel/compute/dataflow/dataflow_dispatcher.c": "f09af46670bc8a3bee49be6c639bc27a432a085109684e0f4f73b4f471b9a6f4",
    "tu_cmodel/tu_cmodel.c": "542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
    "tu_cmodel/rounding.c": "585fa23d2e7ec80499f2607fc4c389001e5dc1d84c818b651c74b1ed65388128",
    "tu_cmodel/tu_precision.c": "d3180406590791d775911ea16960d54974b43abfee1f3b63a6c12a00066d50c7",
    "tu_cmodel/infra/tu_context.c": "ecd0f8258183a9dca0649ca8ed446bee23978571a201fa3464317f31a46762b0",
    "docs/exploration/aspect-ratio-alignment-sweep.md": "05739576b3f6f98b194122c569abf78aa18d7d3cb23f55590ffa9d8cbaf448ed",
    "docs/exploration/dataflow-comparison-gemm128.md": "5884c943eadf6b92021c901d8c694be66ba89bd5f1e2190a33d6fdede0a2646d",
    "docs/exploration/rounding-mode-accuracy-sweep.md": "0e91d7d02835c88abf7157b1f729c6f20539bcd7fcb8fc9cd4a20602096d1dad",
    "docs/exploration/context-switch-state-scope.md": "ae8b49e3b31e0172f69869d406c70996609f295f584357107847186259c80230",
}
PAIRS = {
("tests/test_attention_sweep.c","test-attention-sweep"),("tests/test_benchmark.c","test-bench"),
("tests/test_context_switch_sweep.c","test-context-switch-sweep"),("tests/test_conv_groups_sweep.c","test-conv-groups-sweep"),
("tests/test_conv_pool_cascade.c","test-conv-pool-cascade"),("tests/test_conv_sweep.c","test-conv-sweep"),
("tests/test_dataflow_sweep.c","test-dataflow-sweep"),("tests/test_interconnect_contention_sweep.c","test-interconnect-contention-sweep"),
("tests/test_interconnect_routing_sweep.c","test-interconnect-routing-sweep"),("tests/test_interconnect_switching_sweep.c","test-interconnect-switching-sweep"),
("tests/test_interconnect_topology_sweep.c","test-interconnect-topology-sweep"),("tests/test_mma_activation_sweep.c","test-mma-activation-sweep"),
("tests/test_multicore_scaling_sweep.c","test-multicore-sweep"),("tests/test_norm_attention_sweep.c","test-norm-attention-sweep"),
("tests/test_norm_sweep.c","test-norm-sweep"),("tests/test_pooling_sweep.c","test-pooling-sweep"),
("tests/test_rounding_sweep.c","test-rounding-sweep"),("tests/test_scheduler_sweep.c","test-scheduler-sweep"),
("tests/test_softmax_attention_sweep.c","test-softmax-attention-sweep"),("tests/test_softmax_sweep.c","test-softmax-sweep"),
("tests/test_sparsity_sweep.c","test-sparsity-sweep"),("tests/test_weight_compression_sweep.c","test-weight-compression-sweep"),
}

def rules(text: str) -> dict[str,str]:
    flat=text.replace("\\\n"," ")
    return {m.group(1):m.group(2) for m in re.finditer(r"(?m)^([A-Za-z0-9_.-]+)\s*:\s*([^\n]*)$",flat)}

def check(name: str, ok: bool, failures: list[str]) -> None:
    print(f"CHECK {name}={'PASS' if ok else 'FAIL'}")
    if not ok: failures.append(name)

def main() -> int:
    if len(sys.argv) not in (3,4):
        print("usage: ch21_source_audit.py ARCHIVE PIN [INVENTORY_JSON]",file=sys.stderr); return 2
    root=Path(sys.argv[1]); pin=sys.argv[2]; failures=[]; checks=0
    check("pin",pin==PIN,failures); checks+=1
    for rel,want in HASHES.items():
        p=root/rel; got=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "MISSING"
        check("hash:"+rel,got==want,failures); checks+=1
    make=(root/"Makefile").read_text(); rr=rules(make)
    tracked=[p.relative_to(root).as_posix() for p in (root/"tests").glob("test_*sweep*.c")]
    sweep_sources=sorted(tracked)
    source_to_targets={}
    for target,dep in rr.items():
        for src in re.findall(r"tests/(test_[A-Za-z0-9_]+\.c)",dep):
            source_to_targets.setdefault("tests/"+src,[]).append(target)
    inventory=sorted(sweep_sources+["tests/test_benchmark.c","tests/test_conv_pool_cascade.c"])
    pairs={(s,t) for s in inventory for t in source_to_targets.get(s,[])}
    agg={x for x in rr["test"].split() if x.startswith("test-")}
    reports=sorted((root/"docs/exploration").glob("*.md"))
    reports=[p for p in reports if p.name!="IMPLEMENTATION_BACKLOG.md"]
    data=(root/"tests/test_dataflow_sweep.c").read_text(); rnd=(root/"tests/test_rounding_sweep.c").read_text()
    dispatcher=(root/"tu_cmodel/compute/dataflow/dataflow_dispatcher.c").read_text()
    dataflow_report=(root/"docs/exploration/dataflow-comparison-gemm128.md").read_text()
    core=(root/"tu_cmodel/tu_core.c").read_text(); ctx=(root/"tu_cmodel/infra/tu_context.c").read_text()
    aspect=(root/"scripts/sweep_aspect_ratio.py").read_text(); aspect_report=(root/"docs/exploration/aspect-ratio-alignment-sweep.md").read_text()
    predicates={
      "exact-21-sweep-token-sources":len(sweep_sources)==21,
      "exact-22-source-target-pairs":pairs==PAIRS,
      "manual-no-rule-singleton":sorted(s for s in sweep_sources if s not in source_to_targets)==["tests/test_int8_sweep.c"],
      "exploration-targets-not-aggregate":not ({t for _,t in PAIRS}&agg),
      "exact-46-report-set":len(reports)==46,
      "no-source-manifest":not any("manifest" in p.relative_to(root).as_posix().lower() for p in root.rglob("*") if p.is_file()),
      "dataflow-label-set-before-core-call":"tu_set_dataflow(df_id);" in data and "tu_core_mma(core" in data,
      "core-operation-swaps-snapshot-in":"core_swap_in(core, &saved);" in core[core.index("void tu_core_mma"):core.index("/* ---- Stats ---- */")],
      "dataflow-sweep-unconditional-success":data.rstrip().endswith("return 0;\n}"),
      "dataflow-analytical-formula-local":"ws_cyc += (pd * nc) + K_WORKLOAD + (pd * mc);" in data,
      "dataflow-sweep-all-three-cycle-formulas":all(x in data for x in ("ws_cyc += (pd * nc) + K_WORKLOAD + (pd * mc);","os_cyc += K_WORKLOAD;","rs_cyc += ((pd - 1) * nc + 1) + K_WORKLOAD + ((pd - 1) * mc);")),
      "dataflow-report-shape-level-formulas":all(x in dataflow_report for x in ("WS total = fill + compute + drain + dma","fill   = pdepth × ceil(N / cols)","compute = ceil(M / rows) × ceil(N / cols) × K","drain  = pdepth × ceil(M / rows)","OS total = compute + dma")),
      "dataflow-dispatcher-cycle-composition":all(x in dispatcher for x in ("plugin->get_fill_cycles(plugin, tile_n, tile_k)","plugin->execute_tile(","total_cycles += tile_cycles;","plugin->get_drain_cycles(plugin, tile_m)")),
      "rounding-mode-affects-conversion":"tu_set_rounding_mode(mode);" in rnd and rnd.index("tu_set_rounding_mode(mode);") < rnd.index("tu_fp32_to_fp16"),
      "rounding-first-stochastic-unseeded":"run_gemm_with_rounding(TU_ROUND_STOCHASTIC, \"Stochastic\");" in rnd and rnd.index("run_gemm_with_rounding(TU_ROUND_STOCHASTIC, \"Stochastic\");") < rnd.index("tu_stochastic_set_seed"),
      "rounding-only-one-explicit-seed":"tu_stochastic_set_seed(0xDEADBEEF);" in rnd and rnd.count("tu_stochastic_set_seed(")==1,
      "context-transfer-equation":"pending_save_bytes + ctx->saved_sram_bytes" in ctx and "switch_fixed_cycles + transfer_cycles" in ctx,
      "context-sweep-three-scopes":all(x in (root/"tests/test_context_switch_sweep.c").read_text() for x in ("TU_CTX_SAVE_FULL_SRAM","TU_CTX_SAVE_LIVE_SRAM","TU_CTX_SAVE_CONTROL_ONLY")),
      "aspect-exact-axis-lists":"for M in [16, 20, 32, 40, 64, 80, 96, 128, 160, 192, 200, 256]" in aspect and "for N in [16, 32, 48, 64, 80, 96, 128, 160, 192, 256]" in aspect,
      "aspect-script-two-different-fill-drain-formulas":"fill = pipeline_depth * tiles_n" in aspect and "total = 2*pipeline_depth + tiles_m*tiles_n*K" in aspect,
      "aspect-report-compiler-action-unsupported":"For the ONNX compiler's tiling strategy" in aspect_report,
      "aspect-report-global-remainder-overclaim":"≤ 3.8% overhead for any non-zero remainder" in aspect_report,
      "producer-classes-separated":all((root/p).is_file() for p in ("tests/test_dataflow_sweep.c","tests/test_context_switch_sweep.c","scripts/sweep_aspect_ratio.py","docs/exploration/dataflow-comparison-gemm128.md")),
    }
    for name,ok in predicates.items(): check("predicate:"+name,ok,failures); checks+=1
    if len(sys.argv)==4 and not failures:
        report_rows=[]
        for p in reports:
            text=p.read_text(errors="replace")
            harnesses=sorted(set(re.findall(r"tests/test_[A-Za-z0-9_]+\.c|scripts/sweep_[A-Za-z0-9_./-]+\.py",text)))
            commands=sorted(set(re.findall(r"make\s+test-[A-Za-z0-9-]+|python3?\s+scripts/[A-Za-z0-9_./-]+",text)))
            q=bool(re.search(r"(?im)^\*\*Question:\*\*|^##?\s+Question",text))
            h=bool(re.search(r"(?im)^\*\*Hypothesis:\*\*|^##?\s+Hypothesis",text))
            m=bool(re.search(r"(?im)^##?\s+(Method|Methodology|Cycle Model|Test Harness|Sweep Harness)",text))
            table_rows=sum(1 for line in text.splitlines() if re.match(r"^\|\s*[-+0-9]",line) and not re.match(r"^\|[- :|]+$",line))
            report_rows.append({
                "path":p.relative_to(root).as_posix(),"question":q,"hypothesis":h,"method":m,
                "parameter_matrix":{"declared":bool(re.search(r"(?i)matrix|configurations tested|sweep",text)),"table_data_rows":table_rows},
                "explicit_harness":bool(harnesses),"harness_paths":harnesses,"equation_markers":sorted(set(re.findall(r"(?i)ceil\(|cycles\s*=|cycle model|equation",text))),
                "output_row_count":table_rows,"conclusion":bool(re.search(r"(?im)^##?\s+(Conclusion|Recommendation|Summary|Result)",text)),
                "repro_command":bool(commands),"actual_executed_command":commands,"manifest":bool(re.search(r"\bmanifest\b",text,re.I)),"ci_member":False,
                "producer_class":"mixed" if harnesses and bool(re.search(r"(?i)analytical|equation|cycle model",text)) else ("linked_or_executable" if harnesses else "report_prose"),
            })
        counts={"question":sum(r["question"] for r in report_rows),"hypothesis":sum(r["hypothesis"] for r in report_rows),"method":sum(r["method"] for r in report_rows),"explicit_harness":sum(r["explicit_harness"] for r in report_rows),"repro_command":sum(r["repro_command"] for r in report_rows),"manifest":sum(r["manifest"] for r in report_rows)}
        check("report-field-counts",counts=={"question":35,"hypothesis":30,"method":30,"explicit_harness":13,"repro_command":16,"manifest":0},failures)
        source_rows=[]
        for s,t in sorted(PAIRS): source_rows.append({"source":s,"make_target":t,"aggregate_or_ci":False,"actual_command":"make "+t,"source_sha256":hashlib.sha256((root/s).read_bytes()).hexdigest(),"producer_class":"local_formula" if not re.search(r"\btu_[A-Za-z0-9_]+\s*\(",(root/s).read_text()) else "linked_or_executable"})
        source_rows.append({"source":"tests/test_int8_sweep.c","make_target":None,"aggregate_or_ci":False,"actual_command":"cc tests/test_int8_sweep.c libtucmodel.a -lm","source_sha256":hashlib.sha256((root/"tests/test_int8_sweep.c").read_bytes()).hexdigest(),"producer_class":"linked_or_executable"})
        payload={"pin":PIN,"source_target_pairs":source_rows,"report_relation_counts":counts,"reports":report_rows}
        Path(sys.argv[3]).write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n")
    print(f"CH21_SOURCE_AUDIT {'PASS' if not failures else 'FAIL'} pin={pin} hashes={len(HASHES)} predicates={len(predicates)} checks={checks}")
    if failures: print("FAILURES "+" ".join(failures))
    return 0 if not failures else 1
if __name__=="__main__": raise SystemExit(main())
