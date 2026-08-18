#!/usr/bin/env python3
"""Independent Chapter 21 formula, sensitivity, crossover, and counterexample probe."""
from __future__ import annotations
import csv, json, math, os, sys
from pathlib import Path

def need(ok: bool, msg: str) -> None:
    if not ok:
        print(f"CH21_FORMULA_PROBE REJECT {msg}")
        raise SystemExit(4)

def aspect(M:int,N:int,K:int=128,rows:int=16,cols:int=16,pd:int=2,bus:int=32):
    tm=math.ceil(M/rows); tn=math.ceil(N/cols)
    macs=M*N*K; capacity=tm*tn*rows*cols*K
    fill=pd*tn; compute=tm*tn*K; drain=pd*tm
    dma=math.ceil((M*K+K*N+M*N)*2/bus)
    total=fill+compute+drain+dma
    return dict(M=M,N=N,tiles=tm*tn,util=macs/capacity,fill=fill,compute=compute,drain=drain,dma=dma,total=total,tops=macs*2/total*1e-3)

def dataflow(K:int,M:int=128,N:int=128,R:int=16,C:int=16,pd:int=2,bus:int=32):
    tm=math.ceil(M/R); tn=math.ceil(N/C)
    dma=math.ceil((M*K+K*N+M*N)*2/bus)
    ws=pd*tn+tm*tn*K+pd*tm+dma
    os=tm*tn*K+dma
    return dict(K=K,ws=ws,os=os,overhead=(ws-os)/ws)

def context(total:int,scope:str,bw:int=32,fixed:int=100):
    saved={"full":total,"live25":total//4,"control":0}[scope]
    return dict(total_bytes=total,scope=scope,saved_bytes=saved,bw=bw,cycles=fixed+math.ceil(2*saved/bw))

def main() -> int:
    need(len(sys.argv)==2,"usage-output-dir")
    out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for M in [16,20,32,40,64,80,96,128,160,192,200,256]:
      for N in [16,32,48,64,80,96,128,160,192,256]: rows.append(aspect(M,N))
    need(len(rows)==120,"aspect-count")
    selected={(r["M"],r["N"]):r for r in rows}
    need(round(selected[(20,16)]["util"]*100,1)==62.5,"aspect-20x16-util")
    need(round(selected[(40,16)]["util"]*100,1)==83.3,"aspect-40x16-util")
    need(selected[(16,256)]["total"]==selected[(256,16)]["total"],"aspect-symmetry")
    need(selected[(20,16)]["total"]==570,"aspect-20x16-total")
    # The report claims every nonzero remainder has <=3.8% overhead; M=40 gives 16.7% waste.
    need(100*(1-selected[(40,16)]["util"])>3.8,"remainder-counterexample")
    focused=[aspect(m,16) for m in (16,17,20,24,31,32)]
    need([r["total"] for r in focused]==[404,543,570,606,669,678],"aspect-transition")
    need(focused[0]["tops"]==focused[3]["tops"],"aspect-tie")
    canonical_20x48=selected[(20,48)]["total"]
    second_20x48=2*2+selected[(20,48)]["compute"]+selected[(20,48)]["dma"]
    need(canonical_20x48==1382 and second_20x48==1376,"aspect-duplicate-formula")
    padded_useful_tops=2*(20*16*128)/selected[(32,16)]["total"]*1e-3
    need(padded_useful_tops < selected[(20,16)]["tops"],"padding-counterexample")
    dfs=[dataflow(k) for k in (1,16,32,64,256,1024)]
    need(dfs[0]["ws"]==dfs[0]["os"]+32,"dataflow-fixed-overhead")
    need(dfs[0]["overhead"]>dfs[-1]["overhead"],"dataflow-sensitivity")
    ctx=[context(t,s,b) for t in (128*1024,256*1024,512*1024) for s in ("full","live25","control") for b in (32,)]
    ctx += [context(256*1024,"full",b) for b in (16,64)]
    expected={(r["total_bytes"],r["scope"],r["bw"]):r["cycles"] for r in ctx}
    need(expected[(256*1024,"full",32)]==16484,"context-full-256")
    need(expected[(256*1024,"live25",32)]==4196,"context-live-256")
    need(expected[(256*1024,"control",32)]==100,"context-control-256")
    need(expected[(256*1024,"full",16)]==32868 and expected[(256*1024,"full",64)]==8292,"context-bandwidth")
    cross52=context(256*1024,"full",52)["cycles"];cross53=context(256*1024,"full",53)["cycles"]
    need(cross52==10183 and cross53==9993,"context-budget-crossover")
    need(context(256*1024,"full",128)["cycles"]==context(256*1024,"live25",32)["cycles"]==4196,"context-tie")
    # Local-formula evidence is not a runtime measurement and control-only omits reload.
    payload={"aspect":rows,"aspect_focused":focused,"dataflow":dfs,"context":ctx,"context_crossovers":{"bw52":cross52,"bw53":cross53,"full128_live32_tie":4196},"classes":{"dataflow_route":"executable","context_cost":"linked_estimator","aspect_ratio":"local_formula","historical_reports":"report_prose"}}
    (out/"formula-results.json").write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n")
    with (out/"aspect-rows.csv").open("w",newline="") as f:
      w=csv.writer(f,lineterminator="\n"); w.writerow(["M","N","tiles","util","fill","compute","drain","dma","total","tops"])
      for r in rows: w.writerow([r[k] for k in ("M","N","tiles","util","fill","compute","drain","dma","total","tops")])
    with (out/"sensitivity-rows.csv").open("w",newline="") as f:
      w=csv.writer(f,lineterminator="\n"); w.writerow(["family","axis","alternative","value","metric","producer_class"])
      for r in dfs:
        w.writerow(["dataflow",r["K"],"WS",r["ws"],"formula_cycles","local_formula"]); w.writerow(["dataflow",r["K"],"OS",r["os"],"formula_cycles","local_formula"])
      for r in ctx: w.writerow(["retention",r["total_bytes"],f"{r['scope']}@{r['bw']}Bpc",r["cycles"],"model_cycles","linked_estimator"])
    print("ASPECT_MATRIX rows=120 M_set=12 N_set=10 K=128 producer=local_formula")
    print("ASPECT_BOUNDARY M20N16_util=62.5 M40N16_util=83.3 M20N16_total=570 symmetry_16x256_256x16=1")
    print("COUNTEREXAMPLE report_nonzero_remainder_le_3.8=0 M40_remainder8_waste=16.7")
    print("ASPECT_TRANSITION totals=404,543,570,606,669,678 tie_M16_M24=1 padding20to32_reverses=1 duplicated_20x48=1382_vs_1376")
    print("DATAFLOW_SENSITIVITY K_points=1,16,32,64,256,1024 fixed_formula_delta=32 decreasing_fraction=1 producer=local_formula")
    print("CONTEXT_ROWS full256=16484 live25_256=4196 control256=100 full256_bw16=32868 full256_bw64=8292 producer=linked_estimator")
    print("CONTEXT_CROSSOVER budget10000_bw52=10183 bw53=9993 full128_live32_tie=4196 control_reversal_reload_gt=16384")
    print("PRODUCER_CLASSES executable=1 linked_estimator=1 local_formula=1 report_prose=1 heterogeneous_sum=0")
    print("LIMIT_BOUNDARY control100_excludes_reload=1 aspect_not_runtime=1 dataflow_formula_not_effective_route=1 portfolio_conclusion=0 compiler_runtime_composition=0")
    print("CH21_FORMULA_PROBE PASS")
    return 0
if __name__=="__main__": raise SystemExit(main())
