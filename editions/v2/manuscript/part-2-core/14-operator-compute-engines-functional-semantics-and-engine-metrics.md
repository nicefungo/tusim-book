# Chapter 14 — Operator Compute Engines: Functional Semantics and Engine Metrics

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-14)

## Part A · Attention: what survives a tile boundary?

**Public edition source:** `7a094ff6c5527eff8e4318de676f0c0221c448b4`. This installment covers attention and the interpretation of the pipeline control only. The first edition's August 4, 2026 audit used `e918c80b6fce833cd1fcae97730fa841c2176f25`; its qualified attention result (6–8/9 across builds) and pipeline result are historical, not measurements of the public edition.

### A row is a mathematical unit, not necessarily a resident tile

For one query, give all four keys score zero and set each component of every value vector to ¼. The probabilities must sum to one, so the output must be ¼ however the keys are partitioned. Normalize each pair of keys separately and **add** their results and you get ½ instead. This is why a legal schedule of two matrix products per tile is not yet a legal implementation of attention.

`tu_attention_execute` takes FP16 Q, K and V and emits FP16 output. For each head and query tile it loads Q once. Within the KV loop it stages K and Kᵀ, computes QKᵀ, applies scale and optional mask, packs weights to FP16, replaces K with V and accumulates the weighted values in FP32. Both matrix products use the active global dataflow, not `desc.dataflow`. `tile_n < N` selects streaming state. On a whole row, no mask or a causal mask uses the standard softmax engine; a custom mask uses the attention normalizer without persistent state. See `tu_cmodel/compute/attention_engine.c`, especially `normalize_attention_tile`, `attention_footprint` and `tu_attention_execute` at the edition pin.

| Same four keys, one query, two output components | What is packed before the last weights × V product? | Final output (both components) |
|---|---|---|
| Whole row (`tile_n=4`) | four normalized probabilities ¼ (`3400` hex) | `3400`, `3400` |
| Streaming (`tile_n=2`, two tiles) | two unnormalized weights 1 (`3c00` hex) | `3400`, `3400` |

The whole-row unmasked path scales and normalizes the complete score row before packing it. Streaming keeps three quantities per query row: maximum `m`, weight sum `l`, and weighted-value vector `U`. On a new tile, set `m′ = max(m, max(scores))`; rescale the old `l` and `U` by `exp(m − m′)` (use zero on the first nonempty contribution). Add the new weights `exp(score − m′)` to the sum, and add their weighted values to `U`. Divide **once**, after the final tile. In this fixture each tile adds 2 to `l` and ½ to each component of `U`; `1/4` is the final division, not the per-tile answer to add twice. A zero denominator produces zero. The attention helper rejects NaN and positive-infinite scores and zeros a new weight when the maximum is negative infinity or the shifted score is below −87. The equal-score example does not exercise that cutoff or a changing maximum. Persistent state is FP32; the tile sum uses double before rounding, and the weights used by the MMA are FP16. Partition-invariant mathematics does not promise partition-invariant bits on arbitrary inputs.

Constant V alone would also let an implementation that silently dropped the first tile pass. Change the first pair of values to ¼ and the second pair to ¾, keep Q zero, and tag K's entries 1 through 8. The expected output is now ½, not the final tile's ¾. Both algorithms returned `3800` hex in both positions, with their host output guards intact. Observed output and SRAM words.

### Staging: inspect a byte before trusting a counter

A two-byte FP16 value and a four-byte SRAM word are not the same transfer. At this pin the transpose reads and writes `sizeof(fp16_t)` via bulk operations. The FP32-to-FP16 pack reads a score at byte `4i`, then writes two bytes at `2i`, **in increasing index order**. After the read, the compacted output ends at `2i+2`, before the next unread source at `4i+4`. Reverse order can destroy a source that has not yet been read. O begins after the *full FP32 score reservation*, not after the shorter packed weights; the mask scratch follows O. These are both width and lifetime requirements.

For the tagged test above, the final streaming K tile has rows `(5,6)` and `(7,8)`. Reading the upper half of W after execution gave the FP16 encodings of `(5,7,6,8)` in order; the last halfword ends at byte 16, the exact capacity. The full-row arm used 32 W bytes. The post-call probe also read the packed weights in O SRAM directly, without issuing a metered SRAM read. The unmodified staging matrix checked 720 cases; the KV matrix compared 2,565 cases against its FP64 reference and whole-row control. Maximum absolute error against reference in the latter was 0.000361148989; maximum difference between partitions was 0.00048828125. These are bounds *observed on the fixtures*, not a universal FP16 tolerance.

### Feasibility first; then ask what the tile optimizes

Let `m,n` denote configured tile rows and columns, `N` the complete KV length, and `d` the head dimension. Three reservations must fit separately; unused A cannot pay for missing O:

| Region | Required bytes | What occupies it |
|---|---:|---|
| A | `2md` | Q |
| W | `4nd` | K and Kᵀ; V later reuses the K space |
| O | `8mn + 4md + (n<N ? 8m : 0)` | FP32 score and mask scratch, FP32 output, and (streaming only) one FP32 max and sum per row |

`tu_attention_auto_tile` searches query heights through `min(M,64)` and maximizes the admitted tile area; ties favor smaller `m`. It checks full `N` separately because persistent state disappears there. It does not round an admitted tile up to a PE multiple. No fit yields `0,0`; calling execute with zero fields is **not** a request to run the search. It uses its compatibility defaults and still checks admission. Explicit tiles are not subject to the search's 64-row limit.

For `M=16,N=512,d=64`, default capacities are A/W/O = 65,536/131,072/65,536 bytes. `16×512` needs 69,632 O bytes and does not fit. The selected `15×512` needs only 65,280. Yet a smaller-area explicit tile can move fewer bytes:

| Executed tile | O reserved (B) | Logical DMA (B), one head | Why |
|---|---:|---:|---|
| Auto `15×512` | 65,280 | 266,240 | A second query tile reloads K and V for the last row. |
| Explicit `16×256` | 36,992 | 135,168 | One query tile, two streaming KV tiles. |
| Auto `16×512`, doubled capacities | 69,632 | 135,168 | One query tile and one whole KV row now fit. |

The traffic check is `4Md + 4·ceil(M/m)·Nd` bytes: charge one logical Q read and one FP16 output per element, plus K and V per query tile. The implementation first issues an FP16-sized DMA store from the FP32 accumulator region, then overwrites the host destination with the converted FP16 values using `memcpy`. The counter charges the output once; it does not count physical host writes. All three still do `4MNd` MMA FLOPs. The public autotile test separates an exhaustive candidate oracle on bounded metadata fixtures (90,747 cases) from 69 live cases, including no-fit rejection. Do not count the metadata cases as tensor executions. Nor is `total_cycles = compute_cycles + dma_cycles` measured latency: the component estimates mix MMA charges and SRAM stalls; host exponentials and divisions are not timed functional units. Successful return, correct output, minimum traffic and best latency are four different claims.

## Part B · Normalization and softmax: what defines a row?

A row matters in three different ways: it specifies which numbers share statistics, which values must stay in scratch storage, and which SRAM writes can destroy unread input. The following experiments use the same public pin as Part A, but call the standalone FP32 engines. They do not time attention.

### Normalization: count accesses at the SRAM boundary

`tu_norm_execute` fetches gamma once per column if supplied; it fetches beta once per column **only for LayerNorm**. Then `normalize_row` loads each row once, calculates statistics using the host copy and stores one output per element. Two arithmetic passes for LayerNorm do not mean two SRAM reads. For two rows of two FP32 values, we placed gamma and beta either in separate regions or alongside the data at disjoint offsets. We started each region with one bank, one free word grant, no intervening refill and a two-cycle penalty per excess word. Raw initialization is outside the measurement.

| Mode, both parameters supplied | Reads (data, gamma, beta) | Writes | Penalty, separate regions | Penalty, one shared region |
|---|---:|---:|---:|---:|
| LayerNorm | 4, 2, 2 | 4 | 14 + 2 + 2 = 18 | 22 |
| RMSNorm | 4, 2, 0 | 4 | 14 + 2 + 0 = 16 | 18 |
| BatchNorm label | 4, 2, 0 | 4 | 14 + 2 + 0 = 16 | 18 |

In the separate LayerNorm case, eight data-region accesses cost seven penalties; each two-word parameter vector costs one. In shared SRAM the same twelve accesses compete for **one** free grant, not three. Measured counter deltas agree with those predictions. The return is the penalty incurred by this invocation, not the lifetime meter, a write-only charge or a latency for arithmetic. A historical-counter control starts with two stall cycles already charged by one stalled read: eight more accesses return 16, or zero with bandwidth modeling disabled. These are descriptor measurements; a wrapper staging host parameters can issue extra writes before execution.

### A BatchNorm name does not choose the batch axis

Take two samples with channels as columns: `[[1,10],[3,14]]`. Use row width 2, gamma `[2,0.5]`, beta `[0.25,-0.5]`, and epsilon `0.01` in FP32. LayerNorm centers each **row** (means 5.5 and 8.5) and divides by its population standard deviation with epsilon inside the square root. RMSNorm instead divides by the square root of the row mean square plus epsilon, without centering or adding beta. The accepted BatchNorm descriptor takes the *centered row* path but never loads beta. Equal traffic to RMSNorm in the table does not mean equal outputs.

| Axis-2, beta supplied | Sample 0 | Sample 1 |
|---|---|---|
| BatchNorm label, observed | −1.999506, 0.499877 | −1.999670, 0.499917 |
| Per-channel training reference | −1.740074, −0.999376 | 2.240074, −0.000624 |

The reference reduces **down the columns**: channel means are 2 and 12, population variances 1 and 4. Removing beta leaves the descriptor's output unchanged. The 24-case diagnostic passes precisely because it detects this difference; it is not a BatchNorm conformance pass. Changing row width to zero treats all four elements as one row, not as two channels. Nor does this descriptor take stored channel means and variances for inference. Nothing in this example qualifies wrapper aliasing or optional RMS mean output.

### Log-softmax: the most likely element can still have a negative log probability

For logits `[0,−20]`, the winning probability rounds to 1 in FP32. Taking the log *after* rounding therefore gives zero. The correct winning log probability is `−log1p(exp(−20))`: about **−2.06115362031 × 10⁻⁹**. Instead of adding a small tail to one and then taking its log, LOG excludes exactly one maximum from the exponential sum (other tied maxima still contribute). It takes `log1p` of that residual and subtracts it from each shifted logit. Keeping the shifted logit also avoids reconstructing the losing logit from a possibly underflowed probability.

The gap matrix returned **−2.06115369217 × 10⁻⁹** for the winner (relative error `3.48608 × 10⁻⁸` against `long double`) and `−20` for the loser. The optional FP32 `sum_out` was exactly 1: it is a separate statistic, not the denominator from which to reconstruct LOG. An absolute tolerance of `1e−6` would accept the wrong zero. At gap 88 the default policy discards the exponential tail, and the winning log probability really does come back zero. The gap-20 result is not a relative-error guarantee for every finite gap.

The C descriptor makes two additional choices explicit. With additive bias `b`, scale `s` and no threshold, the default computes `s*(x+b)`; scale-first computes `s*x+b`. Bias units decide which is right. Zero scale means skip; nonzero `mask_fill` is a threshold at the mask stage, not a Boolean exclusion. For exponential range, LEGACY cuts off shifted arguments below −87 except in the ONLINE accumulator; FTZ flushes rounded subnormal **exponentials**, not final outputs; GRADUAL keeps the host `expf` result on a gradual-underflow host. STANDARD and ONLINE emit probabilities, but ONLINE updates the maximum and sum together and still emits from a buffered row. Neither its name nor the SRAM charges rank physical throughput. These choices and the schedule below are descriptor fields, not global JSON settings. Rebuild binary callers against the pinned header `tu_cmodel/compute/softmax_engine.h`.

[Next: Chapter 15 — DRAM Service Models and Bandwidth Claims](15-dram-service-models-and-bandwidth-claims.md)
