# Chapter 6 — PE Arrays, MMA Semantics, and Tiling

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-6)

Two multiplications visit the same twelve tiles on the same 4×8 weight-stationary array. One adds 234 to the MMA cycle estimate; the other adds 384. The difference is not a change of clock or instruction. One workload ends with a tile containing a single useful multiply-accumulate; the other fills every tile. To predict the counter, we need to know what reaches the tile callback, not just how many times it runs.

**Edition and scope.** The worked example uses the direct, single-state `tu_mma` path at public Tusim commit `7a094ff6c5527eff8e4318de676f0c0221c448b4`. An MMA cycle below is a counter increment across that call. The executable audit keeps the observations, an independent per-tile calculation and every returned FP32 word. The July 25 first-edition run at `e918c80b6fce833cd1fcae97730fa841c2176f25` is historical; its outputs are not acceptance criteria for this edition.

## Learning objectives

- Trace `O += W × A` from row-major matrices to the work of one valid tile.
- Separate configured capacity, useful operations and a plug-in's cycle estimate.
- Predict the fill, compute and drain terms for a rectangular array, including all three edge dimensions and the active pipeline depth.
- Use a full-tile control, an independent numerical oracle and separate DMA counters to test that prediction.
- Decide when an array mapping also needs a memory-tiling or packing schedule.

## 6.1 Matrix contract: which dimension is the reduction?

The direct call takes logical dimensions `(M,N,K)` and **byte offsets** into three separate SRAM regions. It expects dense row-major images, without transpose flags or caller-supplied strides:

```text
W: M rows × K columns, FP16       W[m*K + k]
A: K rows × N columns, FP16       A[k*N + n]
O: M rows × N columns, FP32       O[m*N + n]

O[m,n] ← O[m,n] + Σ_k W[m,k] A[k,n]
```

The equation states the intended arithmetic, not an instruction-by-instruction rounding rule. The WS implementation computes a `float` partial sum for each valid K block and adds it to the accumulator. Without bias, **O is not cleared by the call**. Use zero for a fresh product or seed O with a previous contribution. A second call on unchanged inputs adds the product again.

For example, multiply the rows `[1,2]`, `[3,4]` of W by the rows `[5,6,7]`, `[8,9,10]` of A. The first output row is `[21,24,27]`; the second is `[47,54,61]`. A previous value of 1 in `O[0,0]` becomes 22, not 21. The v1 probe used this nonsymmetric example to test orientation, repeated accumulation and a separate packed-bias case. Those tests were not rerun here. An all-ones test is better for something else: one can predict **every** output from K alone, even on an edge. That is why we keep the original all-ones fixture for the edition comparison rather than changing its data to make a new test.

## 6.2 From geometry to a tile envelope

In this mapping, `R=pe_rows` bounds M; `C=pe_cols` bounds **both** N and K. One invocation can cover `R×C×C` MAC positions. K depth is not independently configurable here. For positive dimensions let

```text
T_M = ceil(M/R)       T_N = ceil(N/C)       T_K = ceil(K/C)
T   = T_M T_N T_K     (number of plug-in invocations, not MMA API calls)
```

At a tile origin `(i,j,h)` the valid extents are `m=min(R,M−i)`, `n=min(C,N−j)`, `k=min(C,K−h)`. The dispatcher visits M outermost, then N, then K. The functional loops execute `m n k` multiply-accumulates, not `R C²` padded ones. Across all invocations this partitions the product into exactly `MNK` useful MACs. The field `g_tu.total_mma_flops` counts **two operations per useful MAC**; its stats label is not a MAC count or a rate.

An internal tile is a computation over portions of **already resident** operands. The dispatcher changes index ranges, not which image is in SRAM. It does not pack an activation panel, reload a weight block or spill a partial sum to host memory. These are separate decisions for the caller.

## 6.3 Read the call path before choosing a counter

| Pinned source | What to follow |
|---|---|
| `tu_cmodel/tu_config.h` | `tu_runtime_config_default()` supplies geometry, pipeline depth, mode, SRAM and DMA defaults. |
| `tu_cmodel/tu_cmodel.c` | `tu_init_with_config` selects the plug-in. `tu_mma` builds tensor views over SRAM and calls `tu_dataflow_execute_mma` with `(R,C,C,g_tu.rt_cfg.pe_pipeline_depth)`. |
| `tu_cmodel/compute/dataflow/dataflow_dispatcher.c` | The three loops compute valid extents. Inside the innermost loop, fill receives `(n,k,p)`, execution receives offsets and valid extents, and drain receives `(m,p)`. |
| `tu_cmodel/compute/dataflow/weight_stationary.c` | WS uses `p*n` for fill, executes the arithmetic and **returns `k`** for compute, then uses `p*m` for drain. Read the arguments and returns, not the nominal tile names in comments. |
| `tu_cmodel/dma_descriptor.c` and `tu_cmodel/tu_cmodel.c` | The compatibility W/A loads and O store count service in the DMA engine; the direct wrappers maintain their own byte count. Sample both sides. |

The dispatcher accumulates tile and operation counts and returns the sum of the three cycle terms over the entire call. `tu_mma` adds that sum to `g_tu.estimated_cycles`. We also read the selected plug-in's cumulative `total_cycles`; equality of the two **deltas** helps distinguish a live plug-in result from an accidentally matching top-level total. The three terms are not three independently instrumented hardware timers.

## 6.4 What runs inside a tile?

For a tile starting at `(i,j,h)`, WS visits each of the `m×n` outputs and computes a partial sum using `k` pairs of FP16 inputs. The byte strides supplied by `tu_mma` are `2K`, `2N` and `4N` for W, A and O respectively; the plug-in converts those strides to element indices. The last tile uses the original row strides even when only one column remains. A short K tile contributes to the same FP32 O image as the preceding K tile.

`weight_stationary.c` uses the shared `tu_fp16_to_fp32` conversion. The v1 report that raw `0x0001` produced `2^-14` rather than `2^-24` described a private decoder at the old pin, not the implementation now executing. This chapter tests normal finite ones and exact small integer sums, not general binary16 conversion or rounding. Chapter 7 separates arithmetic from mode selection; Chapter 8 treats numerical coverage as a separate question.

The name *weight-stationary* does not itself demonstrate a stationary weight register. This code walks scalar arrays and returns an estimate; it does not instantiate physical PEs, record their activity or time the propagation of a partial sum between neighbors.

## 6.5 Worked experiment: the historical 9³ setup and two full-tile controls

Start with `tu_runtime_config_default()`; override **only** rows to 4 and columns to 8. The active mode is `weight_stationary` (ID 0) and the runtime depth is 2. In a freshly initialized state, fill host W and A with `fp32_to_fp16(1.0f)`. Direct-load W then A at offset zero, call `tu_mma(9,9,9,0,0,0,false)` once, then direct-store the full FP32 O image from offset zero. **Do not load O:** fresh SRAM supplies zero accumulators. Adding an O preload, enabling bias, changing the initial depth or putting the store inside the MMA bracket would not reproduce v1's `run_ones` setup.

The partitions along M, N and K are `[4,4,1]`, `[8,1]` and `[8,1]`: six spatial tiles, two reduction blocks per spatial tile. The following ledger groups the two identical full M blocks; the ungrouped ledger lists all twelve origins. Each charge and MAC count in a row is **per invocation**, before multiplication by copies.

| Valid `(m,n,k)` | Copies | Fill `2n` | Compute `k` | Drain `2m` | Useful MACs |
|---|---:|---:|---:|---:|---:|
| 4,8,8 | 2 | 16 | 8 | 8 | 256 |
| 4,8,1 | 2 | 16 | 1 | 8 | 32 |
| 4,1,8 | 2 | 2 | 8 | 8 | 32 |
| 4,1,1 | 2 | 2 | 1 | 8 | 4 |
| 1,8,8 | 1 | 16 | 8 | 2 | 64 |
| 1,8,1 | 1 | 16 | 1 | 2 | 8 |
| 1,1,8 | 1 | 2 | 8 | 2 | 8 |
| 1,1,1 | 1 | 2 | 1 | 2 | 1 |
| **Weighted sum** | **12** | **108** | **54** | **72** | **729** |

The predicted MMA increment is `108+54+72 = 234`. Holding data, route, offsets and transfer sequence fixed, change the shape first to one full `4×8×8` tile, then to `12×16×16`: the **same 3×2×2 grid** as 9³ but with no remainders. Finally repeat 9³ changing only the runtime depth to 5. Below, fill/compute/drain are independently calculated; the next column is read from the executable. The DMA column comes from a different counter.

| `(M,N,K)`; depth | Tiles | Fill + compute + drain | Observed MMA Δ | Useful MACs / counted ops | DMA payload B / engine cycles | Output words checked |
|---|---:|---:|---:|---:|---:|---:|
| 9,9,9; 2 | 12 | 108 + 54 + 72 | **234** | 729 / 1,458 | 648 / 173 | 81 × `0x41100000` |
| 4,8,8; 2 | 1 | 16 + 8 + 8 | **32** | 256 / 512 | 320 / 160 | 32 × `0x41000000` |
| 12,16,16; 2 | 12 | 192 + 96 + 96 | **384** | 3,072 / 6,144 | 1,664 / 202 | 192 × `0x41800000` |
| 9,9,9; 5 | 12 | 270 + 54 + 180 | **504** | 729 / 1,458 | 648 / 173 | 81 × `0x41100000` |

One full tile alone cannot distinguish a formula using valid extents from one using configured capacity: the arguments coincide. The full **grid** shows what paying for twelve full tiles looks like. Conversely, the depth pair isolates a change in cost with **identical partitions, outputs, operations and transfers**. A depth stuck at 2 would pass the full-tile tests at depth 2 but fail the last row.

The numerical oracle starts from the fixture, not from a plug-in: each output is `0 + K × (1 × 1)`, exactly representable as FP32 for these K values. It compares the bit pattern and index of every returned word, including the last row and column. Agreement of two plug-ins, a checksum, or checking only the first output would answer a weaker question.

## 6.6 Edge utilization has a denominator; it is not the timing equation

Define a **slot** as one potential MAC position within the nominal tile envelope. The slot fraction factors into independent edge fractions:

```text
U_slot = MNK / (T R C²)
       = [M/(T_M R)] [N/(T_N C)] [K/(T_K C)]
```

The first two factors describe output-edge fit; the last describes reduction-edge fit. For 9³ there are `12×4×8×8 = 3,072` possible positions but only 729 useful MACs: about **23.73%**. The full-grid control has the same denominator and uses all of it. It does more work **and** has a larger MMA estimate. Meanwhile changing only depth takes 234 to 504 with no change in slot fraction. Neither the tile count nor the fraction alone determines cycles.

Slot utilization is a mapping calculation, not measured active PE time. It includes no pipeline bubbles or memory stalls, makes no assertion that padded MACs were executed, and cannot tell us whether unused lanes were clock-gated.

## 6.7 Aspect ratio: choosing which dimensions receive capacity

For `4×32×16`, compare two arrays with 64 PEs. The 8×8 array needs `1×4×2` invocations; half its nominal rows correspond to no output. The 4×16 array needs `1×2×1`, with no remainder. At depth 2, the valid-extent equation predicts `8×(16+8+8) = 256` versus `2×(32+16+8) = 112`. These are **formula applications**, not additional S5 runs. The v1 values 320 and 112 used nominal fill and drain; agreement on the wide case is precisely what one should expect for full tiles.

Another useful paper comparison is `9×9×8`. The slot fraction drops from 31.64% (8×8) to 15.82% (16×16), yet the depth-2 WS prediction drops from 104 to 44 because four invocations become one. For `16³` on 16×16, 32×32 and 64×64 the slot fractions are 100%, 12.5% and 1.5625%, but now **all three predict 80**: one valid `(16,16,16)` block each time. The historical 80/144/272 was an effect of charging unused configured rows and columns. It is not a reason to predict an oversized-array slowdown at this pin.

The useful design question is which array suits a *distribution* of shapes. Width helps N but also increases nominal K capacity, whether K can use it or not. Equal PE counts need not imply equal wire length, banking, multicast cost or frequency. Even a convincing advantage in model cycles on one shape is not a physical area, latency or energy result.

## 6.8 Derive the estimate, then locate DMA on its own counter

Write `p` for the runtime pipeline depth. Inside the K loop, each WS call charges `p n + k + p m`. The N extents sum to N, once for every M and K block; the K extents sum to K, once for every M and N block; the M extents sum to M, once for every N and K block. Thus the tile ledger has a second, closed-form check:

```text
fill    = p T_M T_K N
compute =   T_M T_N K
drain   = p T_N T_K M
```

For 9³, that is `p×3×2×9 + 3×2×9 + p×2×2×9`. At depth 2 it gives 234; at depth 5 it gives 504. First-edition WS instead used `T_M T_N [T_K × 2(C+R) + K]`: `3×2×[2×24+9] = 342`. The default depth happens to be 2 in both fixtures. **The 342→234 change at fixed depth is due to valid extent charging**, not a shorter pipeline. The depth-5 pair is the separate evidence that depth now propagates. Do not substitute Chapter 7's 246: its worked shape is `9×10×9`.

Which counter moved? Here are the literal cumulative readings for the depth-2 edge run. The byte counter is the direct wrapper's `g_tu.total_dma_bytes`; the engine's `total_bytes` matched at every sample. The plug-in cycle count also matched the MMA increment. All counts start at zero.

| After | `g_tu.estimated_cycles` | `g_tu_dma.estimated_cycles` | DMA bytes | Engine transfers |
|---|---:|---:|---:|---:|
| Init | 0 | 0 | 0 | 0 |
| W load | 0 | 56 | 162 | 1 |
| A load | 0 | 112 | 324 | 2 |
| MMA | 234 | 112 | 324 | 2 |
| O store | 234 | 173 | 648 | 3 |

For these three fitting, linear transfers, the initialized width is 32 bytes, read and write latencies are each 50, and burst issue adds zero. The engine charges `50+ceil(bytes/32)` per transfer: `56+56+61 = 173`. The wrappers inspect and clear `g_tu.dma.estimated_cycles`, **not** `g_tu_dma.estimated_cycles`; the former stays zero here. A zero top-level DMA increment therefore does not mean a free transfer. Nor is `234+173` a measured completion time. There is no descriptor retirement, overlap measurement, direct O preload or wall-clock timing in this experiment. Other helpers and configurations need their own accounting.

## 6.13 Design exercises and checks

1. For `(M,N,K)=(23,35,17)` on 8×16 at depth 2, derive the tile grid, useful MACs, operations, slot fraction and WS estimate. **Check:** `3×3×2`, 13,685 MACs, 27,370 operations, about 37.12% slot fit, 849 estimated MMA cycles. Explain why the last two numbers have different denominators.
2. Give the first and last tile costs of the 9³ experiment. **Check:** `(4,8,8)` costs `16+8+8`; `(1,1,1)` costs `2+1+2`. Why would a run consisting only of the first tile fail to detect the v1 formula?
3. In a counterfactual model, pay fill and drain only once per spatial tile and keep compute unchanged. Predict the depth-2 9³ delta. **Check:** `54+54+36=144`, not 234. Design a K-aligned single-block case that cannot distinguish the models, then add a second K block that can.
4. A student adds an explicit all-zero FP32 O preload and still obtains 81 nines. Which result remains valid and which experiment has changed? Identify the added payload and the helper whose counter path needs to be checked before quoting DMA service.
5. Design a selector for `4×16`, `8×8` and `16×4`. Hold PE count and depth fixed, reject shapes whose resident images do not fit, and report tile count, slot fraction and estimated MMA cycles separately. What memory, frequency and layout evidence would you need to turn the result into a hardware recommendation?

**Takeaway.** Geometry sets the capacity of a tile. Valid extents determine useful work. The selected WS implementation prices each visit using those extents and the runtime depth. None of these alone tells us how long a physical array would take to move the operands. [Chapter 7](07-pluggable-dataflows.md) holds the tiling contract fixed and asks what changes when the plug-in changes.

[Next: Chapter 7 — Pluggable Dataflows](07-pluggable-dataflows.md)
