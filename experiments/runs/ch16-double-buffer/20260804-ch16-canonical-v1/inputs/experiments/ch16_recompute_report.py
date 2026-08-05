#!/usr/bin/env python3
from math import ceil
M = N = 128
K = 256
PE = 16
PDEPTH = 2
BUS = 32
OPS = 2 * M * N * K
expected = {
    16:(28752,9216,19536), 24:(26688,6912,19776),
    32:(24624,4096,20528), 40:(24624,4096,20528),
    48:(24624,4096,20528), 56:(24624,4096,20528),
    64:(22560,0,22560), 80:(22560,0,22560),
    96:(22560,0,22560), 128:(22560,0,22560),
}
for okb, exp in expected.items():
    max_m = okb * 1024 // (N * 4)
    chunks=[]; remaining=M
    while remaining:
        c=min(max_m,remaining); chunks.append(c); remaining-=c
    fill=sum(PDEPTH*ceil(N/PE) for _ in chunks)
    drain=sum(PDEPTH*ceil(c/PE) for c in chunks)
    compute=sum(ceil(c/PE)*ceil(N/PE)*K for c in chunks)
    dma=sum(ceil((c*K*2 + K*N*2 + c*N*4)/BUS) for c in chunks)
    overlap=0
    for i,c in enumerate(chunks):
        comp=ceil(c/PE)*ceil(N/PE)*K
        if i+1 < len(chunks):
            n=chunks[i+1]
            overlap += min(comp, ceil((n*K*2 + K*N*2)/BUS))
        if i:
            p=chunks[i-1]
            overlap += min(comp, ceil((p*N*4)/BUS))
    total=fill+drain+compute+dma
    db=total-overlap
    assert (total,overlap,db)==exp
    print(f"CH16_SWEEP okb={okb} chunks={','.join(map(str,chunks))} total={total} overlap={overlap} db={db} tops={OPS/total/1000:.3f} dbtops={OPS/db/1000:.3f} speedup={total/db:.3f}")
assert 2*16 == 32 and 64//32 == 2
assert 256*2*2 == 1024
print("CH16_SWEEP_CAPACITY single64_kib=64 double16_physical_kib=32 ratio=2.0")
print("CH16_SWEEP_PORT_CHECK independent_256pe_two_fp16_bytes_per_cycle=1024 report_claim=512")
print("CH16_SWEEP SUMMARY failures=0 rows=10")
