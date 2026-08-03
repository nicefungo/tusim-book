#!/usr/bin/env python3
"""Fail-closed source/linkage/integration audit for Tusim Chapter 9."""
from __future__ import annotations
import hashlib, re, sys
from pathlib import Path
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
HASHES = {
"Makefile":"5249a0e077438a4e6f70c74936c185bb1c30105bb834b3f89ac6a78b32630fd2",
"tu_cmodel/tu_config.h":"129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
"tu_cmodel/tu_sram.c":"5a6ffcdd3f63c9c015bd628b5c44ded951785a128685b413b6db680f5d1753c0",
"tu_cmodel/tu_sram.h":"aa62a942c83bfded4644c26eabf37acb815b7ac2883b53f6b3b8a585df4123d5",
"tu_cmodel/memory/memory_hierarchy.c":"3f5d4a71e0bf107e0b5e7581d5d0cf3f7b2a56ec02e4cc39bcf7923b1901c286",
"tu_cmodel/memory/memory_hierarchy.h":"8df3d23ee14b77433cac070bb541e2efb0ce80d5d1ff9fabb886fff8bac20fe8",
"tu_cmodel/memory/dram_model.c":"c5ce405dbf30d96ffb166895c1df6a871c9aa3198dda15dc903ad6d346de5ed3",
"tu_cmodel/memory/dram_model.h":"4acdec93bc83a0f8d7cf267a55ea5c29e863f20b9024e83a709ba28acbb17602",
"tu_cmodel/infra/config.c":"17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
"tu_cmodel/infra/config.h":"723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
"tu_cmodel/tu_cmodel.c":"542aa16f6f1561f0d55af05920e9922ed3c381a1ad193e6f2ecfca390a8b5059",
"tu_cmodel/tu_cmodel.h":"416a0d20776825498217ff5d4382f07ccb2ac9689bbe6c70cacd1bf13e7725af",
"tu_cmodel/tu_core.c":"0e4b3c6e206465748ae2d3d2e9871f3a6542a61cd1ddcddfff6886b9ed1f0eeb",
"tu_cmodel/tu_core.h":"dc5c22065fb65be4353585ccbfd3bec6c9b9d70e976a51e87169bac79dd164e9",
"tu_cmodel/dma_descriptor.c":"2434c254eef9615b864106de0c453328e64aa6ec49f1e1aff2da5d7e49c8404e",
"tests/test_memory_hierarchy.c":"88589f3e92ffe78b8525f60e6067ebbeba2c4c1f83362bfdb018a9f37f6f64ff",
"tests/test_cmodel.c":"a7609fe22a113c0d9f2807ab3b76c7be29bbc2ed3822a3cfea82c2109862b36c",
"tests/test_config.c":"e2bf7d9a1bbac06863e3b8c372fa1cb854927fc1aeb73a08c79e08cd3f1db821",
"tu_cmodel/perf/cycle_model.c":"b197a6ab411f5ab2d152a99ae233bb25abb2d1912d1f4fa8a94a88e7e1879fec",
"tu_cmodel/perf/cycle_model.h":"0f0301d824be11f2fb4cfc96fd53ae9b64db841de6fb15d989e4f42d846b7101",
"tests/test_cycle_model.c":"606e4325ca31e71c19cc05101ccf76db95a2be95d1bbb57fef7e19ca9d398ca9",
"docs/memory-hierarchy.md":"eab657a93e27d7d6f655d8223956b0b340a5ae1107ee2071c244c6b1b4807559",
"docs/bandwidth-modeling.md":"004cf897a64f008dd98d4d1c76912513cba4b02916a6549ecc0b39eb0de8c1b3",
"docs/configurable-pe-and-banking.md":"75e9fad2e6f40d2194476c06107181d1320dbae9e0f06a4e5b0ea646581ce9ab",
}
def req(x,m):
    if not x: raise SystemExit("FAIL: "+m)
def txt(r,p): return (r/p).read_text()
def main():
    req(len(sys.argv)==3,"usage: audit TREE REVISION")
    r=Path(sys.argv[1]); rev=sys.argv[2]
    req(rev==PIN,"wrong revision")
    req((r/".chapter-source-revision").read_text().strip()==PIN,"marker")
    for p,h in HASHES.items(): req(hashlib.sha256((r/p).read_bytes()).hexdigest()==h,"hash drift "+p)
    make=txt(r,"Makefile")
    block=re.search(r"TU_OBJS\s*=.*?(?=\n\n)",make,re.S).group(0)
    for o in ("tu_sram.o","memory/memory_hierarchy.o","memory/dram_model.o"): req(o in block,"library object "+o)
    agg=re.search(r"^test:.*?(?=\n\n)",make,re.M|re.S).group(0)
    req("test-memhier" in agg,"test-memhier aggregate omission changed")
    cfg=txt(r,"tu_cmodel/infra/config.c")
    conv=re.search(r"tu_runtime_config_t tu_config_to_runtime.*?^}",cfg,re.M|re.S).group(0)
    for f in ("sram_w_size","sram_a_size","sram_o_size"): req(f in conv,"capacity not propagated "+f)
    for f in ("sram_num_banks","sram_bank_width","gbuf_size_kb","gbuf_banks","dram_type","dram_bandwidth_gbps"):
        req(f not in conv,"expected dropped memory field now propagates "+f)
    sram=txt(r,"tu_cmodel/tu_sram.c")
    req("b->bank_count = TU_SRAM_BANKS" in sram and "b->bank_width = TU_SRAM_BANK_WIDTH" in sram,"compiled bank geometry changed")
    req("b->arb_mode = arb_mode" in sram and "if (b->arb_mode" not in sram and "switch (b->arb_mode" not in sram,
        "arbitration gained executable consumer")
    req("conflicts++" not in sram,"conflict counter gained producer")
    req("TU_REPORT_ERR" in sram and re.search(r"static void bounds_check.*?return;.*?}\n",sram,re.S),"bounds reporting shape changed")
    hier=txt(r,"tu_cmodel/memory/memory_hierarchy.c")
    req("memset(h, 0, sizeof(*h))" in hier and "apply_level_config" in hier,"preinit override behavior changed")
    req("tu_sram_advance_cycle" not in hier,"hierarchy now advances SRAM cycles")
    req("h->gbuf.total_hits++" in hier and "addr + bytes <= gr->total_size" in hier,"GBuf hit definition changed")
    # Exact repository call-site boundary: hierarchy API only in its implementation/test.
    cfiles=list(r.rglob("*.c"))
    users=[]
    for p in cfiles:
        if "tu_mem_hierarchy_" in p.read_text(errors="ignore"): users.append(p.relative_to(r).as_posix())
    req(set(users)=={"tests/test_memory_hierarchy.c","tu_cmodel/memory/memory_hierarchy.c"} and len(users)==2,
        "hierarchy call-site set drift: "+repr(users))
    cm=txt(r,"tu_cmodel/tu_cmodel.c")
    req(cm.count("tu_sram_raw_ptr")>=3,"direct MMA raw bypass changed")
    cyc=txt(r,"tu_cmodel/perf/cycle_model.c")
    req("cycle_model.o" not in block,"cycle model unexpectedly library-integrated")
    req("w_sram_addr % cm->bank_model->num_banks" in cyc and
        "a_sram_addr % cm->bank_model->num_banks" in cyc and
        "o_sram_addr % cm->bank_model->num_banks" in cyc,
        "cycle-model starting-address bank mapping changed")
    req("bank->conflict_count++" in cyc,"cycle-model conflict producer changed")
    print(f"SOURCE_AUDIT: PASS ({len(HASHES)}/{len(HASHES)} hashes)")
    print("LIBRARY: SRAM+hierarchy+DRAM objects present; test-memhier aggregate-listed")
    print("CONFIG: capacities+banking parse; capacities propagate; banking/DRAM drop at runtime conversion; GBuf defaults are not parsed by canonical JSON")
    print("INTEGRATION: hierarchy call sites limited to implementation+focused test; direct MMA uses raw SRAM pointers")
    print("STATIC_LIMITS: low-level SRAM arbitration stored/no consumer; low-level conflicts no producer; hierarchy tick does not refill SRAM")
    print("THIRD_SURFACE: cycle-model bank engine source-present, conflict-producing, byte-address-modulo mapped, not TU_OBJS-integrated")
if __name__=="__main__": main()
