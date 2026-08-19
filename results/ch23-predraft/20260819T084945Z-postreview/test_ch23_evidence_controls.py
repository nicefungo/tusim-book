#!/usr/bin/env python3
"""Positive and source-mutation controls for Chapter 23 evidence tooling."""
import argparse, ast, hashlib, os, shutil, subprocess, sys, tempfile
from pathlib import Path

def run(cmd,cwd=None,timeout=420):
    return subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
def check_no_assert(path):
    tree=ast.parse(path.read_text(),filename=str(path))
    if any(isinstance(n,ast.Assert) for n in ast.walk(tree)): raise RuntimeError(f"ast.Assert present in {path}")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--recon',required=True); ap.add_argument('--source',required=True); a=ap.parse_args()
    recon=Path(a.recon).resolve(); source=Path(a.source).resolve(); check_no_assert(recon); check_no_assert(Path(__file__).resolve())
    print("AST_ASSERT_CONTROL PASS count=0")
    with tempfile.TemporaryDirectory(prefix='ch23-controls-') as td:
        td=Path(td)
        for opt in (False,True):
            out=td/f"positive-{'opt' if opt else 'normal'}.log"; cmd=[sys.executable]+(['-O'] if opt else [])+[str(recon),'--source',str(source),'--output',str(out)]
            p=run(cmd); marker='CH23_EXTENSION_RECON PASS' in out.read_text() if out.exists() else False
            if p.returncode!=0 or not marker: raise RuntimeError(f"positive opt={opt} rc={p.returncode} tail={p.stdout[-1000:]}")
            print(f"POSITIVE_CONTROL mode={'optimized' if opt else 'normal'} rc=0 marker=1")
        clone=td/'mutated-source'; p=run(['git','clone','--quiet','--no-hardlinks',str(source),str(clone)],timeout=120)
        if p.returncode: raise RuntimeError(p.stdout)
        p=run(['git','checkout','--quiet','e918c80b6fce833cd1fcae97730fa841c2176f25'],clone);
        if p.returncode: raise RuntimeError(p.stdout)
        ignored=subprocess.check_output(['git','status','--ignored','--short'],cwd=clone,text=True)
        clone_baseline=hashlib.sha256(ignored.encode()).hexdigest()
        mut_recon=td/'mutation-recon.py'
        mut_recon.write_text(recon.read_text().replace('55cee6bf897c58ee52931706ac6be61adacb18d4d7b3b12f388952a9f79a0485',clone_baseline))
        check_no_assert(mut_recon)
        target=clone/'tu_cmodel/command_queue.c'; target.write_text(target.read_text().replace('case TU_CMD_ELEMENTWISE:', 'case TU_CMD_POOL:\n    case TU_CMD_ELEMENTWISE:',1))
        for opt in (False,True):
            out=td/f"mutation-{'opt' if opt else 'normal'}.log"; cmd=[sys.executable]+(['-O'] if opt else [])+[str(mut_recon),'--source',str(clone),'--output',str(out)]
            p=run(cmd); text=out.read_text() if out.exists() else ''
            if p.returncode==0 or 'CH23_EXTENSION_RECON FAIL' not in text: raise RuntimeError(f"mutation escaped opt={opt} rc={p.returncode}")
            print(f"SOURCE_MUTATION_CONTROL mode={'optimized' if opt else 'normal'} rejected=1")
    print("CH23_EVIDENCE_CONTROLS PASS positive=2 mutation=2 ast_assert=0")
    return 0
if __name__=='__main__': raise SystemExit(main())
