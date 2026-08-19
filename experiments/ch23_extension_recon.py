#!/usr/bin/env python3
"""Fail-closed Chapter 23 exact-pin extension-path reconnaissance."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, re, shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
IGNORED_BASELINE_SHA256 = "55cee6bf897c58ee52931706ac6be61adacb18d4d7b3b12f388952a9f79a0485"
EXPECTED = {
"Makefile":"5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
"tu_cmodel/infra/config.h":"723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
"tu_cmodel/infra/config.c":"17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
"tu_cmodel/tu_cmodel.c":"542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
"tu_cmodel/compute/dataflow/dataflow_interface.h":"141bdd26c5e436d38095296e824a93761ac4b74edaed9b7482ef7c8eca5ebf77",
"tu_cmodel/compute/dataflow/dataflow_registry.c":"56b4fcab5e736eb1fd55a02cdeaefd20504a708a7cea6012c8c819e25bc24d27",
"tu_cmodel/compute/dataflow/dataflow_dispatcher.c":"f09af46670bc8a3bee49be6c639bc27a432a085109684e0f4f73b4f471b9a6f4",
"tu_cmodel/compute/dataflow/weight_stationary.c":"c421bd0845da1847b4e48a97c55f45dbbb058dc3a5af0e448d5fab422bd5b7e8",
"tu_cmodel/compute/dataflow/output_stationary.c":"fa3a00c9b649b69dc8e92d562f044c49b129096c753ba169a855ba2e075dfaa0",
"tu_cmodel/compute/dataflow/row_stationary.c":"ea86233c36fa1f076e0852204880f8d903bf546728478816df66b091e56feeaf",
"tests/test_config.c":"e2bf7d9a1bbac06863e3b8c372fa1cb854927fc1aeb73a08c79e08cd3f1db821",
"tests/test_dataflow.c":"c26b74c35e50e5231c193835f4d3ccc00146bc08548e3e52d6a50f50f6c9db43",
"tu_cmodel/isa/tu_isa.h":"8efd760c3485492de68b6093d9fa617cdebc2f75de3453310ed3f207b4d16456",
"tu_cmodel/isa/tu_isa.c":"53bdf44cd720a933da174da55ab1180f8056de9fb2aaa5b9b534adb7af4c387f",
"tu_cmodel/command_queue.h":"cf1f06164d7b3353158c3b70c0667d29b6e94a2ca90a08620232546023363135",
"tu_cmodel/command_queue.c":"e8e24987b1cadb61d23bee76085ca7f11b37b7d387eb075033a1651f8a72a389",
"tests/test_isa.c":"1f20a476d30d73485473adf532848d7af3d372167b969d40f9fce9279d93d2d0",
"tests/test_command_queue.c":"f15c088772c5ac1eeedd25ceeeb8592f60f6b5386f5a854b5394f1d65e934237",
"compiler/onnx_to_tu.py":"9308a86a6c7a986c9fa6cfae6f1b147724de5a78cabaf34656e15de4e4713e2b",
"bindings/python/tu_bindings.py":"74562a1c19a47ab8c16e5d92c363a3c3a885c566250eb2fa29434a20851e6740",
"docs/runtime-configuration.md":"2dbf98ea56733f35ecd099c58ff443bdc5897f3462fdf77689f8e722fcb15d63",
"docs/TU_DATAFLOW.md":"179042cac05ab8e74ac8c258078683b9e444029a99f37b4fb4951b9381b7f777",
"docs/expanded-isa.md":"046be507f11d82ba26f262c7a69ce9d662f636fbfe0c20e1762871ae38db0107",
"docs/python-bindings.md":"93dbb67b0bca961f5e122a68c0d282ea389c17d5727f9336e13470bbd2a5c940",
"examples/single_linear.onnx":"370633753b23aa41407848974cc17183a1841050ceb4a9b84582004cd8f641dc",
"examples/tiny_mlp.onnx":"c60559b718d0f698156e7b0b6ed0f26b292e2dbff10c746b16f41c67bb2e71e3",
"tu_cmodel/perf/cycle_model.c":"b197a6ab411f5ab2d152a99ae233bb25abb2d1912d1f4fa8a94a88e7e1879fec",
"tu_cmodel/perf/cycle_model.h":"0f0301d824be11f2fb4cfc96fd53ae9b64db841de6fb15d989e4f42d846b7101",
"tests/test_cycle_model.c":"606e4325ca31e71c19cc05101ccf76db95a2be95d1bbb57fef7e19ca9d398ca9",
"tests/test_dataflow_sweep.c":"4b3dc2da732f4efa25ec250bfb76e3507bd07168a73a703350150228077f57e6",
"docs/exploration/rs-pipeline-depth-sweep.md":"2105d56dbb84e92f23b2b12b5d118538342e3a55e1e80651e45e842a2f26137f",
"tu_cmodel/isa/tu_scheduler.c":"b76afa350cc6229fe981e4c188bdc7b8026df4ae74725b3106c624afee9c8893",
"tu_cmodel/isa/tu_liveness.c":"78949f02c43c3c7711033644cb87c5e0441edff0f4d1931d47ba104a67e9b239",
"tu_cmodel/compute/attention_engine.c":"73f291d886fe9bfe730a71c7af9ea913789003cea28be75464e42ff55c87b74e",
}

def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
class EvidenceError(RuntimeError): pass
def require(condition, message):
    if not condition: raise EvidenceError(message)
def run(cmd, cwd, env=None, timeout=180):
    p=subprocess.run(cmd,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    return p.returncode,p.stdout

def source_state(src: Path, label: str):
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=src,text=True).strip()
    branch=subprocess.check_output(["git","branch","--show-current"],cwd=src,text=True).strip()
    tracked=subprocess.check_output(["git","status","--short","--untracked-files=all"],cwd=src,text=True)
    ignored=subprocess.check_output(["git","status","--ignored","--short"],cwd=src,text=True)
    require(head==PIN and branch=="" and tracked=="", f"source state drift head={head} branch={branch!r} tracked={tracked!r}")
    digest=hashlib.sha256(ignored.encode()).hexdigest()
    require(digest==IGNORED_BASELINE_SHA256, f"ignored inventory drift {digest}")
    print(f"SOURCE_STATE {label} pin={head} detached=1 tracked_dirty=0 ignored_entries={len(ignored.splitlines())} ignored_sha256={digest}")
    return digest

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--source",required=True); ap.add_argument("--output",required=True); a=ap.parse_args()
    src=Path(a.source).resolve(); out=Path(a.output).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    lines=[]
    class Capture:
        def write(self,s): lines.append(s); return len(s)
        def flush(self): pass
    old=sys.stdout; sys.stdout=Capture()
    first=None
    try:
        first=source_state(src,"before")
        for rel,d in EXPECTED.items(): require(sha(src/rel)==d, f"hash drift {rel}")
        print(f"HASH_SET PASS files={len(EXPECTED)}")
        texts={p:(src/p).read_text(errors="replace") for p in EXPECTED if not p.endswith('.onnx')}
        cfg_h=texts["tu_cmodel/infra/config.h"]; cfg_c=texts["tu_cmodel/infra/config.c"]
        conv=cfg_c[cfg_c.index("tu_runtime_config_t tu_config_to_runtime"):cfg_c.index("/* ---- Load from JSON string ----")]
        require(all(x in conv for x in ["rt.pe_rows", "rt.pe_cols", "rt.sram_w_size", "rt.sram_a_size", "rt.sram_o_size"]), "geometry conversion edge missing")
        require("dataflow_mode" not in conv and "pe_pipeline_depth" not in conv and "dma_bus_width_bits" not in conv, "expected conversion omission changed")
        require('parse_dataflow_str' in cfg_c and 'cfg->dataflow_mode = parse_dataflow_str' in cfg_c, "dataflow parser edge missing")
        print("PATH_CONFIG geometry=complete_to_runtime dataflow=parsed_then_dropped pipeline=parsed_then_dropped dma_width=parsed_then_dropped")
        iface=texts["tu_cmodel/compute/dataflow/dataflow_interface.h"]; model=texts["tu_cmodel/tu_cmodel.c"]
        enums=re.findall(r"TU_DATAFLOW_[A-Z_]+\s*=\s*\d+",iface)
        regs=re.findall(r"tu_dataflow_register\(tu_dataflow_([a-z]+)_create\(\)\)",model)
        require(len(enums)==4 and regs==["ws","os","rs"] and "tu_dataflow_nlr_create" not in model, "plugin declaration/registration census changed")
        require("TU_DATAFLOW_MAX_PLUGINS 8" in texts["tu_cmodel/compute/dataflow/dataflow_registry.c"], "registry capacity changed")
        require("plugin->execute_tile" in texts["tu_cmodel/compute/dataflow/dataflow_dispatcher.c"], "dispatcher helper consumer missing")
        attention=texts["tu_cmodel/compute/attention_engine.c"]
        require("g_tu.dataflow && g_tu.dataflow->execute_tile" in model and "tu_dataflow_execute_mma(" in model, "production tu_mma to dispatcher path missing")
        call_sites=model.count("tu_dataflow_execute_mma(")+attention.count("tu_dataflow_execute_mma(")
        require(call_sites==3, f"dispatcher production call-site census changed {call_sites}")
        require("falling back to WS" in model and "if (!plugin) return -1;" in model and "return 0;" in model[model.index("int tu_set_dataflow"):model.index("const char *tu_get_dataflow_name")], "unregistered fallback semantics changed")
        registry=texts["tu_cmodel/compute/dataflow/dataflow_registry.c"]
        require("discard the equivalent newly-created instance" in registry and "if (plugin->impl_data) free(plugin->impl_data);" in registry and "free(plugin);" in registry, "duplicate registry ownership changed")
        require("if (g_registry_count >= TU_DATAFLOW_MAX_PLUGINS) return;" in registry, "registry capacity status changed")
        require(all(f"compute/dataflow/{n}.o" in texts["Makefile"] for n in ["weight_stationary","output_stationary","row_stationary"]), "plugin build ownership changed")
        print("PATH_PLUGIN declared_ids=4 linked_registered_consumed=3 missing_registered_id=no_local_reuse registry_capacity=8 ownership=global_registry_core_pointer duplicate_policy=keep_first_free_new capacity_overflow=silent_return_without_free production_consumer=tu_mma_and_attention_to_dispatcher_to_vtable production_call_files=2 production_call_sites=3 production_callers=tu_cmodel.c,attention_engine.c unregistered_fallback=weight_stationary success_status=1")
        isa=texts["tu_cmodel/isa/tu_isa.h"]; cq=texts["tu_cmodel/command_queue.c"]
        declared=len(re.findall(r"^\s*TU_ISA_[A-Z0-9_]+\s*=",isa,re.M))
        dispatch=sorted(set(re.findall(r"case (TU_CMD_[A-Z0-9_]+):",cq[cq.index("static void execute_command"):cq.index("/* ================================================================\n * Public API")])) )
        require(declared==59 and dispatch==["TU_CMD_BARRIER","TU_CMD_DMA_LOAD","TU_CMD_DMA_STORE","TU_CMD_ELEMENTWISE","TU_CMD_HALT","TU_CMD_MMA","TU_CMD_NOP","TU_CMD_SYNC"], "opcode/dispatch census changed")
        require("TU_CMD_POOL" in texts["tu_cmodel/command_queue.h"] and "TU_CMD_POOL" not in dispatch, "pool alias boundary changed")
        require("TU_ISA_POOL_MAX" in texts["tu_cmodel/isa/tu_scheduler.c"] and "TU_ISA_POOL_MAX" in texts["tu_cmodel/isa/tu_liveness.c"], "adjacent static-analysis consumers changed")
        print(f"PATH_OPCODE declared_explicit={declared} queue_dispatch={len(dispatch)} dispatch_set={','.join(dispatch)} pool_alias_without_dispatch=1 adjacent_analysis_consumers=scheduler,liveness composed_execution=0")
        mk=texts["Makefile"]
        require("tu_cmodel/perf/cycle_model.o" not in mk.split("libtucmodel.a:",1)[0], "cycle model entered library")
        require("test_cycle_model.c" not in mk, "cycle model obtained Make ownership")
        tracked=subprocess.check_output(["git","ls-files","*.c","*.h"],cwd=src,text=True).splitlines()
        external=[]
        for rel in tracked:
            if rel in ("tu_cmodel/perf/cycle_model.c","tu_cmodel/perf/cycle_model.h","tests/test_cycle_model.c"): continue
            if "tu_cycle_" in (src/rel).read_text(errors="replace"): external.append(rel)
        require(external==[], f"cycle-model external callers changed {external}")
        print("PATH_MODULE cycle_model_source=1 library_member=0 make_rule=0 focused_source=1 production_reachability=0 exhaustive_external_non_test_call_files=0")
        sweep=texts["tests/test_dataflow_sweep.c"]
        require("test-dataflow-sweep: tests/test_dataflow_sweep.c libtucmodel.a" in mk, "sweep target missing")
        aggregate=mk[mk.index("test: test-cmodel"):mk.index("# Quick smoke test")]
        require("test-dataflow-sweep" not in aggregate, "sweep aggregate ownership changed")
        require("check_identical(g_O_ws, g_O_os" in sweep and "check_identical(g_O_ws, g_O_rs" in sweep, "sweep comparison edge missing")
        require("return 0;" in sweep[sweep.index("int main(void)"):] and "tests_failed" not in sweep, "sweep status semantics changed")
        require("Analytical cycle model" in sweep and "Validated against:" in texts["docs/exploration/rs-pipeline-depth-sweep.md"], "sweep documentation edge missing")
        require("tu_set_dataflow(df_id);" in sweep and "tu_core_mma(core," in sweep and sweep.count("tu_core_create(&cfg)")==3, "sweep routing structure changed")
        print("PATH_SWEEP source=1 make_target=1 aggregate_owner=0 fixed_workload=1 fixed_seed=1 local_formula=1 mismatch_changes_status=0 docs_claim_validation=1 effective_core_routes=WS,WS,WS labeled_routes=WS,OS,RS")
        py=texts["bindings/python/tu_bindings.py"]
        require("self._config_path = config_path" in py and "tu_init_from_file" not in py and "self._lib.tu_init()" in py, "binding config boundary changed")
        require('return "Performance counters: use C API' in py and 'return "Power model: use C API' in py, "binding report stubs changed")
        print("PATH_BINDING python_source=1 config_path_stored_not_consumed=1 direct_ctypes_mma=1 perf_stub=1 power_stub=1 make_ci_owner=0")
        comp=texts["compiler/onnx_to_tu.py"]
        require("host_{op.lower()}(/* TODO: wire up */);" in comp and "|| true" in mk[mk.index("test-full:"):mk.index("# ---- Test: MMA")], "compiler fail-open boundary changed")
        require("examples/single_linear.onnx" not in mk and "examples/tiny_mlp.onnx" not in mk, "contained model ownership changed")
        require(not any(k in comp for k in ["onnxruntime.InferenceSession","ReferenceEvaluator("]), "far-boundary oracle appeared; re-audit trigger")
        print("COMPILER_TRIGGER contained_models=2 generator=1 generated_link_status_suppressed=1 far_boundary_oracle=0 nontrivial_link_run_verify=0 boundary=negative")
        print("COMPILER_PROMOTION_GATE compile=0 link=0 run=0 independent_oracle=0 full=0 required_full=1")
        print("DOC_CONFLICT runtime_config_claims_all_parameters=1 conversion_subset=1 dataflow_docs_ids=4 registered=3 expanded_isa_declared=59 queue_dispatch=8")
        with tempfile.TemporaryDirectory(prefix="ch23-ext-") as td:
            td=Path(td); archive=td/"src.tar"
            with archive.open("wb") as f: subprocess.run(["git","archive",PIN],cwd=src,stdout=f,check=True)
            tree=td/"tree"; tree.mkdir()
            with tarfile.open(archive) as tf: tf.extractall(tree)
            env=os.environ.copy(); env["LD_LIBRARY_PATH"]=str(tree); env["LC_ALL"]="C"
            rc,log=run(["make","-j2","all"],tree,env,240); require(rc==0, log[-4000:])
            print("ARCHIVE_BUILD rc=0")
            expected={"test-dataflow":"9 passed, 0 failed","test-isa":"9/9 passed","test-cmdq":"9/9 tests passed"}
            rc,log=run(["make","test-config"],tree,env,180)
            # Fresh exact-pin run currently aborts after initialization; retain this as a finding.
            require(rc != 0 and "stack smashing detected" in log, f"test-config changed rc={rc} tail={log[-1000:]}")
            print(f"FOCUSED test-config rc={rc} classification=red stack_smashing=1 reproducibility=layout_sensitive_root_cause_open")
            for target,marker in expected.items():
                rc,log=run(["make",target],tree,env,180); require(rc==0 and marker in log, f"{target} rc={rc} tail={log[-1000:]}")
                print(f"FOCUSED {target} rc=0 classification=green marker={marker.replace(' ','_')}")
            rc,log=run(["make","test-dataflow-sweep"],tree,env,240)
            require(rc==0 and "--- Key Finding ---" in log and "MISMATCH" in texts["tests/test_dataflow_sweep.c"], "sweep dynamic path changed")
            print("FOCUSED test-dataflow-sweep rc=0 classification=green_status_but_fail_open_oracle fixed_rows=1")
            rc,log=run([sys.executable,"bindings/python/tu_bindings.py"],tree,env,180)
            require(rc==0 and "Identity GEMM: PASS" in log, f"binding smoke rc={rc} tail={log[-1000:]}")
            print("FOCUSED python-binding rc=0 identity_gemm=PASS config_path_exercised=0 reports_exercised=0")
            # Active Python lacks NumPy at this host; this is an environment observation, not source proof.
            rc,log=run([sys.executable,"compiler/onnx_to_tu.py","examples/single_linear.onnx","--output",str(td/"generated.c"),"--name","single"],tree,env,60)
            compiler_class="executed" if rc==0 else "environment_blocked"
            print(f"COMPILER_SMOKE status={compiler_class} rc={rc} generated={int((td/'generated.c').exists())}")
        print("READER_DECISION require_contract_card=declaration,ingress,retention,consumer,observable,verification,ownership,documentation weakest_missing_edge_blocks_integrated_claim=1")
        print(f"TOOLCHAIN machine={platform.machine()} python={platform.python_version()} make={shutil.which('make') is not None} cc={shutil.which('cc') is not None}")
        second=source_state(src,"after"); require(second==first, "source ignored inventory changed during run")
        print("CH23_EXTENSION_RECON PASS hashes=34 path_families=7 focused_green=5 focused_red=1 compiler_boundary=negative")
    except Exception as e:
        try: source_state(src,"after_failure")
        except Exception as se: lines.append(f"SOURCE_STATE after_failure ERROR {se}\n")
        lines.append(f"CH23_EXTENSION_RECON FAIL {type(e).__name__}: {e}\n")
        rc=1
    else: rc=0
    finally:
        sys.stdout=old; out.write_text(''.join(lines)); print(''.join(lines),end='')
    return rc
if __name__=="__main__": raise SystemExit(main())
