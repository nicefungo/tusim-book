#!/usr/bin/env python3
"""Chapter 22 focused six-domain reconciliation against an immutable Tusim archive."""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, tarfile, tempfile
from pathlib import Path

PIN="e918c80b6fce833cd1fcae97730fa841c2176f25"
DOMAINS={
 "geometry": ("ch21_sweep_probe.c", [r"DATAFLOW_LINKED_EXEC active=weight_stationary .* cycles=81920", r"active=output_stationary .* cycles=20480", r"active=row_stationary .* cycles=50176"]),
 "memory_overlap": ("ch16_double_buffer_probe.c", [r"PIPE_LEDGER .* seq=8 piped=7 saved=0", r"PIPE_DEPTH1_LEDGER seq=5 piped=3 saved=0", r"CH16_PROBE SUMMARY failures=0"]),
 "numerics_representation": ("ch13_weight_stream_probe.c", [r"SPARSITY est128 .* selected=7811", r"SPARSITY estNarrow dense_total=34307 sparse_total=77312", r"CH13_PROBE SUMMARY failures=0"]),
 "operators": ("ch14_compute_engines_probe.c", [r"ATTN diff golden_err=0\.[0-9]+ deviates=1 scales_equal=1", r"PIPE depth2 sequential_total=402 saved=200", r"CH14_PROBE SUMMARY failures=0"]),
 "sharing_topology": ("ch12_multicore_interconnect_probe.c", [r"ROUTES patternA_XY=606 patternA_YX=222 patternB_XY=222 patternB_YX=606", r"HEURISTIC_COUNTEREXAMPLE isolated=94 bottleneck=128 estimated=158", r"CH12_PROBE SUMMARY failures=0"]),
 "runtime_static_policy": ("test_scheduler_sweep.c", [r"All-Independent", r"Serial-Chain", r"Pipeline-Tiles", r"Sweep Complete"]),
}

def run(cmd, *, cwd=None, timeout=180):
    p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    if p.returncode: raise RuntimeError(f"command failed ({p.returncode}): {' '.join(map(str,cmd))}\n{p.stdout[-8000:]}")
    return p.stdout

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--book-root",required=True); ap.add_argument("--tusim-root",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
    book=Path(a.book_root).resolve(); tusim=Path(a.tusim_root).resolve(); out=Path(a.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    head=run(["git","rev-parse","HEAD"],cwd=tusim).strip(); status=run(["git","status","--porcelain"],cwd=tusim)
    if head!=PIN or status: raise RuntimeError(f"Tusim pin/state violation: head={head} dirty={bool(status)}")
    with tempfile.TemporaryDirectory(prefix="ch22-recon-") as td:
        work=Path(td)/"src"; work.mkdir()
        archive=Path(td)/"src.tar"
        with archive.open("wb") as f:
            p=subprocess.run(["git","archive","--format=tar",PIN],cwd=tusim,stdout=f)
            if p.returncode: raise RuntimeError("git archive failed")
        # Exact pinned archive is a trusted local source; preserve repository symlinks.
        with tarfile.open(archive) as tf: tf.extractall(work,filter="fully_trusted")
        run(["make","-j2","libtucmodel.a"],cwd=work,timeout=300)
        logs={}; checks={}
        probes=book/"experiments"
        for domain,(src_name,patterns) in DOMAINS.items():
            src=(work/"tests"/src_name) if src_name=="test_scheduler_sweep.c" else probes/src_name
            exe=Path(td)/domain
            cmd=["cc","-O2","-Wall","-Wextra","-std=c11",f"-I{work}",f"-I{work/'tu_cmodel'}","-o",str(exe),str(src),str(work/"libtucmodel.a"),"-lm"]
            run(cmd,timeout=180)
            repeats=3 if domain=="operators" else 1
            chunks=[]
            for rep in range(1,repeats+1):
                chunks.append(f"=== repeat {rep}/{repeats} ===\n"+run(["timeout","120s",str(exe)],timeout=140))
            log="".join(chunks)
            (out/f"{domain}.log").write_text(log)
            logs[domain]={"source":str(src.relative_to(book) if book in src.parents else src.relative_to(work)),"source_sha256":sha(src),"log":f"{domain}.log","log_sha256":sha(out/f"{domain}.log"),"repeats":repeats}
            checks[domain]=[{"pattern":pat,"matched":bool(re.search(pat,log,re.M))} for pat in patterns]
        # The Chapter 21 discriminator also directly reconciles numerical and context axes.
        ch21=(out/"geometry.log").read_text()
        extra={
          "numerics_representation":[r"ROUNDING_AXIS .* rne=0x3c01 rtz=0x3c00 .* changed_seed_diff=1",r"ROUNDING_ORDER stable_case_seed_permutation_equal=1 single_seed_permutation_diff=1"],
          "runtime_static_policy":[r"CONTEXT_EXEC full256=16484 live25_256=4196 control256=100 full256_bw16=32868 full256_bw64=8292"],
        }
        for d,pats in extra.items(): checks[d].extend({"pattern":p,"matched":bool(re.search(p,ch21,re.M)),"log":"geometry.log"} for p in pats)
        failed=[(d,c["pattern"]) for d,cs in checks.items() for c in cs if not c["matched"]]
        operator_errors=[float(x) for x in re.findall(r"ATTN diff golden_err=([0-9.]+)", (out/"operators.log").read_text())]
        observations={
          "operator_attention_golden_errors":operator_errors,
          "operator_repeat_count":len(operator_errors),
          "operator_error_repeat_stable":len(set(operator_errors))<=1,
          "scope":"Differences across repeats are retained as negative reproducibility evidence, not averaged.",
        }
        result={"schema":"ch22-focused-reconciliation-v1","tusim_commit":head,"tusim_source_clean":not bool(status),"archive_method":"git archive exact pin","domains":logs,"checks":checks,"observations":observations,"all_checks_passed":not failed,"failed_checks":failed}
        (out/"reconciliation.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"all_checks_passed":not failed,"domains":len(logs),"failed":failed},sort_keys=True))
        if failed: raise SystemExit(1)
if __name__=="__main__": main()
