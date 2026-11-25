# Chapter 21 — Designing a Trustworthy Sweep

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-21)

On a 16×16 PE array, a 31×19×17 matrix multiply costs 88 estimated MMA cycles with output-stationary selected and 276 with row-stationary selected. Change only the pipeline depth from two to one. Output-stationary still costs 88; row-stationary now costs 68. Both still produce the right matrix. If the proposed conclusion was “output-stationary always wins,” there is no need to run a larger sweep: the public single-state rows already refute it. If the question was whether a hardware team should build a row-stationary array, neither row answers it.

This chapter uses the public Tusim pin `7a094ff6c5527eff8e4318de676f0c0221c448b4`. The distinction that matters is between **which implementation ran**, **whether it computed the right values**, and **what its cost counter measures**. A different observation can disprove each claim.

## Learning objectives

- Specify a sweep as a decision with a disproof condition, rather than a list of knobs.
- Trace the selected mode to the state that executes MMA. Tell a comparison against peers from a comparison against an independently constructed answer.
- Predict a live counter difference from valid tile extents, then find a case where the ranking changes.
- Read a failed row, diagnostic and process exit together. Decide which rows can be compared without inventing an elapsed time.

## 21.1 Write the decision before the loop

[Chapter 4](04-configuration-as-the-architecture-contract.md) follows a request into runtime state; [Chapter 7](07-pluggable-dataflows.md) follows the selected plug-in into a tile. Chapter 20 asks what a test actually reached and which observations would make it fail. For a sweep we need that answer **for each row**, including uninteresting ties and cases that disagree with the hypothesis.

| Decision field | Contract for the worked comparison |
|---|---|
| Question | For the same GEMM and array, which supported mode incurs the fewest callback-estimated cycles across one MMA, subject to correct output? Does the ordering survive a depth change? |
| Alternatives | Weight-stationary (WS, ID 0), output-stationary (OS, 1), row-stationary (RS, 2). No-local-reuse (NLR) is an unsupported request, not a fourth performance point. |
| Workload axes | Compare modes within a shape. Include a partial spatial edge with a second K tile, an aligned square, and a wide/tall pair. |
| Controls | For each comparison hold input words, initial O, geometry and call boundary fixed. For the depth experiment also hold shape fixed. Inputs are deterministic, not independent random samples. |
| Reject a row | Wrong active selection, wrong output, or a live delta inconsistent with the expected tile sum. A missing or failed arm does not become a cheap configuration. |
| Report | Retain each shape and depth, minimize the delta only among passing comparable rows, preserve exact ties. No cross-workload weights, mean speedup or portfolio ranking. |

A filename containing `sweep` identifies a candidate, not an experiment. A Make target can exist without belonging to an aggregate; even a selected target need not reach its final check. Here the command ledger identifies the two public targets **and** the separate invocations of the resulting binaries. Their output and exit files establish execution. The first edition’s sweep-file, target and report counts describe its own source pin; they are not a census of this edition.

## 21.2 Follow the selector to the executing state

In the first edition (`e918c80b6fce833cd1fcae97730fa841c2176f25`), the dataflow sweep selected a mode on the process-global state and then executed a core. Swapping in the core restored its own selection. An OS label could therefore run WS and still return a correct matrix. The harness also printed a separate cycle formula, and a printed mismatch need not fail the process. Reproducing that table reproduced the defect. The old handwritten DMA-inclusive estimates, report equations and `mTOPS` label are not columns in the public live-MMA result.

There are two ways to reach an executing state in the revised comparison:

1. **Direct state.** The single-state test sets `cfg.dataflow_mode` and `cfg.pe_pipeline_depth`, calls `tu_init_with_config`, then checks `g_tu.dataflow->id` and `tu_get_dataflow_name()` before calling `tu_mma`. The state whose identity it checks owns the SRAM and the counter it reads. This is a runtime-struct test, not a JSON parser test.
2. **Core snapshot.** The three-core test uses `tu_core_set_dataflow` on each core, reads its ID, calls `tu_core_mma`, then reads its ID again. The registry supplies shared plug-in objects; each core retains its own selected pointer. Setting one global mode and hoping it survives a core swap is not a substitute for setting the core. The test also asks the OS core for NLR and requires rejection with OS retained.

For a question about **file ingress**, start one step earlier. The shared Chapter 4 fixture [runtime-request.json](../../examples/runtime-request.json) requests OS. Its OS capture and the matched WS capture show parsed and converted modes, effective names, 45 checked output words per arm, and MMA deltas of 52 and 432 respectively at 4×8 PEs and depth 7. The deliberately wrong expected label fails at the configuration check; it is not the output-bit mutation below. Do not substitute either ingress row for a public sweep row.

## 21.3 Read the public rows by what they check

The two executables use the same four primary **shapes**, not the same input generator. Shape order throughout is **M×N×K**: `O[M,N] += W[M,K] × A[K,N]`. On the direct path the test installs FP16 W and A in SRAM, clears FP32 O, samples `g_tu.estimated_cycles`, executes one MMA, and samples again. On the core path the W/A DMA loads occur **before** the first sample and the O store **after** the second. Neither table includes DMA time.

| Public single-state workload | M×N×K | Depth | WS | OS | RS |
|---|---|---:|---:|---:|---:|
| edge-multik | 31×19×17 | 2 | 468 | 88 | 276 |
| square | 64×64×64 | 2 | 5120 | 1280 | 3136 |
| wide-smallk | 32×128×16 | 2 | 1280 | 320 | 784 |
| tall-smallk | 128×32×16 | 2 | 1280 | 320 | 784 |
| pipeline-sensitivity | 31×19×17 | 1 | 268 | 88 | 68 |
| pipeline-sensitivity | 31×19×17 | 2 | 468 | 88 | 276 |
| pipeline-sensitivity | 31×19×17 | 4 | 868 | 88 | 676 |

Each cost cell is one observed model-counter delta, not the number the test predicted. The single-state transcript contains 21 passing rows: 12 workload rows plus nine depth rows. The depth-two edge recurs by design; it is not a new shape or a statistical replicate. The numerical oracle computes a separate dot product in FP32, with one partial sum per valid K tile then an addition to O, and compares FP32 **bits**. It does not ask WS to certify the other modes. It *does* call Tusim’s canonical FP16 converter, so a decoder error shared with the plug-ins could escape. A separate test-side loop predicts the cost from the extents; the observation remains the counter difference.

The public multicore transcript has four workload lines, each with three core deltas. They match the first four lines of the table above. Its `exact` has a different meaning: `memcmp` found the WS output byte-identical to both peers on that workload. The executable gates selection, cross-core equality and NLR rejection. It prints the three deltas but **does not compare them to a cycle oracle**. If all three produced the same wrong output, the equality test could pass. If all three deltas were wrong, that fact alone would not fail this test. Sequential core calls demonstrate retained state, not simultaneous execution or a three-core speedup.

## 21.4 Predict the counter before reading it

Let the PE array have `R` rows, `C` columns and runtime depth `d`. An MMA tile spans at most `R×C×C` in M,N,K order. At origin `(i,j,t)`, take `m=min(R,M−i)`, `n=min(C,N−j)`, `k=min(C,K−t)`. In particular K advances by **C**, not R. For positive depths in the experiment the callback contracts are:

| Mode | Charge for one valid `(m,n,k)` tile |
|---|---|
| WS | `d*n + k + d*m` |
| OS | `k + ceil(k/4)` |
| RS, d = 1 | `k` |
| RS, d > 1 | `(d−1)*n + 1 + k + (d−1)*m` |

Sum over **every** spatial tile and every K tile. Do not charge fill/drain just once for a whole dot product or replace valid edge sizes with nominal sizes. OS’s quarter-K surcharge is a term in its estimator, not a measured count of operand fetches. The pinned source route is `tu_mma` → `tu_dataflow_execute_mma` in `tu_cmodel/compute/dataflow/dataflow_dispatcher.c` → selected plug-in callbacks. [Chapter 7](07-pluggable-dataflows.md) maps those producers; `expected_cycles` in the public test is the comparator, not the producer.

**Work the 31×19×17 edge.** On 16×16 PEs the valid lengths are `[16,15]`, `[16,3]`, `[16,1]`. The last tile is `(15,3,1)`; at depth two it costs WS `6+1+30=37`, OS `1+1=2`, RS `3+1+1+15=20`. There are eight tile calls, not eight copies of this last one. Across the four spatial tiles, `sum(m+n) = 2*31 + 2*19 = 100`; both K tiles incur it, giving 200. The K work sums to `4*(16+1)=68`. OS rounds separately, so the surcharge is `4*(4+1)=20`. Thus:

```text
WS = 68 + 2*200     = 468
OS = 68 + 20        =  88
RS = 68 + 1*200 + 8 = 276
```

The arithmetic explains the reversal in the opening example. At depth one, the RS branch drops **both** the spatial charge and the per-call one: 68. At depth four it pays `68+3*200+8=676`. OS is depth-independent here. Wide and tall also tie mode-for-mode at depth two: both have sixteen full spatial tiles and a single full K tile. That tie says something about this equation’s symmetry on a square array, not about the cost of transposing a layout on a machine.

## 21.5 Give the implementations a chance to disagree with the reference

The separate S4 probe changes both the geometry and the source of the answer. Its fixture generator uses Python to emit literal half words and expected FP32 words without Tusim conversions. On the edge case the products and seeded sums are exact small integers. Two cores get opposite-sign initial O patterns, so accidentally using the other core’s state can change a result even though the W and A words agree. In the smaller identity case, multiplying by the identity must preserve an input as small as the binary16 subnormal `2^-24`: the expected first FP32 word is `33800000`. That is one decoder discriminator, not a floating-point conformance suite.

| Independent probe, 4×8 PEs, depth 2 | Valid lengths along M; N; K | Calls observed | Expected and observed WS / OS / RS deltas |
|---|---|---|---|
| 9×10×9 edge | 4,4,1; 8,2; 8,1 | six core, three direct | 246 / 72 / 162 |
| 2×3×2 identity | 2; 3; 2 | six core | 12 / 3 / 8 |

Here is a cycle oracle that does not call any plug-in. For the edge, K work is `3*2*9=54`; the spatial span across both K blocks is `2*(2*9+3*10)=96`; there are `3*2*2=12` callbacks. Predict WS `54+2*96=246`, OS `54+6*(ceil(8/4)+ceil(1/4))=72`, RS `54+96+12=162`. In the word and counter transcript, core 0 executes the edge with WS from counter 0 to 246, then identity from 246 to 258. Reading 258 as the cost of identity would attribute the previous call to the new one.

The probe rotates `(core 0, core 1, direct)` through `(WS,OS,RS)`, `(OS,RS,WS)`, `(RS,WS,OS)`. It checks the requested ID, the selected object and name, the live delta and every FP32 word. Between core calls it checks that the idle peer retained its ID and counter and that the direct selection survived the swap. Both direct and core setters reject NLR without replacing the selected mode. The 15 calls yield `9*90 + 6*6 = 846` observed/expected word pairs. This establishes independent numeric and cycle checks on **these fixtures**; it does not retroactively add either oracle to the public multicore executable.

## 21.6 Make a bad row fail for the intended reason

Suppose a harness prints the requested name, runs WS every time, compares all results to the first matrix and prints costs from a lookup table keyed by name. All three output comparisons can pass and the cost columns can differ. Looking at more shapes would miss the problem if the three mappings are supposed to compute the same answer. Checking the executing state and reading its actual counter would expose the substitution.

The editor tested the route check directly. In a fresh scratch copy, a one-row change initialized the depth-four OS edge as WS but left the expected mode and printed label at OS. The diagnostic says `requested mode 1 but active=weight_stationary`. The failed row prints **0**: the identity gate returned before MMA, leaving the caller’s zero placeholder. No zero-cycle MMA was measured. The other 20 rows passed. The command and exit ledger records exit 1 for the mutation and 0 for the unmodified control, whose 21-row output matches S4 byte for byte.

A numerical negative control tests a different failure path.

S4 took a copy of the public single-state translation unit and changed one bit of the **expected** first output word on just the first WS edge row. It linked against the same static archive. The raw row still reports 468 cycles but now says `FAIL`. The diagnostic identifies `output[0] bits 3fa10000 != oracle 3fa10001` and counts one failed row. The other 20 pass, including the repeated depth-two edge. The binary exits 1; the unmodified single-state binary exits 0. This is a mismatch propagated by the executable itself, not a parser rescuing a zero exit. A driver that *expects* the negative child to fail can correctly finish with zero. An unrelated crash would not demonstrate this control.

For a new experiment keep `case key → expected observation → actual observation → child status` together. Check that the full set of keys is present: a truncated file of passing rows must not pass as a complete sweep. Key by experiment as well as shape, depth and mode so the intentional repeated edge does not overwrite a row. Preserve diagnostics and the command that produced them. A checksum detects a changed file, not a wrong prediction shared by test and implementation.

## 21.7 Decide whether another metric belongs in the table

Before joining two rows, write down what increments each number, which state owns it, the interval, numerator, denominator and clock (if any). A live observation can be an observation **of an estimate**. The MMA interval is one call; its clock is not a measured hardware frequency. The following worked comparisons keep their own producers.

| Evidence | What actually varied and what the number means | Conclusion the sweep must refuse |
|---|---|---|
| S9 payload | Two requests total 96 useful bytes over 128 explicit ticks at 1 GHz. Exact vs per-request rounded occupancy is 96 vs 192 B. Useful rate stays 0.75 GB/s; occupied rate goes from 0.75 to 1.5 GB/s. | Doubling the occupied rate did not double useful throughput. Returned DRAM service and stalls are not the rate denominator; the caller did not wait out the stalls. |
| S9 power | At fixed 7 nm, event counts and 8192 supplied cycles, 750→2500 MHz gives modeled total energy 0.588289→0.448848 µJ but average power 53.859→136.977 mW. The leakage interval shortens. | Lower energy is not lower average power or measured DVFS. Do not attach either estimate to an MMA row without matched events and a time basis. |
| S11 normalization and softmax | For two two-wide rows, LayerNorm returns 18 vs 22 SRAM penalty cycles with parameter regions separate vs shared. The number is the invocation’s penalty, not arithmetic latency. In the softmax overlap matrix, a rejected forced direction performs zero accesses. | A smaller stall count is not a faster whole operator. Zero work on rejection is infeasible, not a winning schedule. Require admissibility and a numerical result before comparing cost. |
| S12 placement | Mixed routes have isolated maximum 94 and busiest directed-link load 128. The combined shared-link score is 158; a collision-free schedule finishes by 133. The busiest link and longest route need not belong to the same message. | Link load supplies a necessary service bound under the slot assumptions; the combined score is **not** a makespan lower bound. A `tu_cluster_send` endpoint copy and its isolated charge are a different operation again, not an observed packet arrival. |

The same rule applies to a **pipeline sweep**. MMA pipeline *depth* in §21.4 is an input to the tile callbacks; it does not establish DMA/compute overlap. At this pin the four-channel setup is legal, and the public pipeline suite passed 11/11. Yet a swap-time check found a sentinel where the consumer needed the next tile despite a reported 2.05×. Check the data when it is consumed; a later overwrite or a successful status cannot validate an earlier transfer of ownership. [Chapter 14](14-operator-compute-engines-functional-semantics-and-engine-metrics.md) distinguishes those pipeline controls from standalone engine numerics and counters. Neither the old backing-capacity objection nor a passing numerical suite decides whether a pipeline is ready at swap.

## 21.8 Choose the next cases, not the next decimal place

A boundary suite is economical when one counterexample settles the question. A factorial grid is useful when two axes interact: the depth-one RS result is precisely what a shape-only depth-two grid misses. Neither design supplies a workload distribution. For a stochastic experiment define the seed and reset point per case, permute case order, and distinguish replay of one vector from independent workload sampling. For a deterministic estimator, test an interaction or a transition before averaging a column of repeated values.

Three examples from the first edition remain useful **as design methods**, not newly executed v2 results:

- Rounding: discriminate at conversion with an input between representable values. Changing a seed can change a conversion vector; it says nothing by itself about inference accuracy. Keep conversion and FP32 accumulation separate.
- Retention: a fixed charge plus transferred bytes divided by state bandwidth predicts a model-local switch cost. A control-only policy can omit the very reload needed to continue correctly. Use [Chapter 18’s retention boundary](18-runtime-context-retention-and-preemption-boundaries.md) before declaring a feasible alternative.
- Aspect ratio: in a nominal 16×16 tile-utilization formula, M=40 and N=16 use only `40/48` of the slots. The unused fraction, about 16.7%, already exceeds the historical report’s proposed 3.8% global remainder bound. This is a counterexample *inside a formula*, not a runtime measurement or an instruction to pad a compiled workload.

For a physical WS/OS/RS decision, the missing experiment has a different dependent variable. Define a storage boundary (for example, W words crossing SRAM to the array), count transfers at that boundary for fixed useful work, specify ports and buffering, and check which transfers and MACs can coexist in a schedule. Compare with a mapped external trace before interpreting a cycle difference as a physical speedup. No such operand-traffic record is emitted by these sweep rows. A portfolio preference among latency, energy and area belongs to Chapter 22, after those objectives have producers and the feasible set is known.

## Review questions and answers

1. **Why isn’t an OS label followed by the correct matrix enough?** WS should compute the same matrix. Check the ID/name on the executing direct state or the retained ID on the core, then compare the live MMA delta with the selected mode’s predicted charge.
2. **What does `exact` mean in the public three-core output?** The three FP32 output buffers agree byte-for-byte. It does not mean independent reference agreement or assertion of the printed cycle totals. The single-state test and the separate probe supply different checks.
3. **Why retain the 68-cycle row?** At depth one, RS has no spatial or per-call surcharge. On this fixture 68 is below OS’s 88, refuting a depth-independent ranking without suggesting that either plug-in moves fewer physical bytes.
4. **What would still pass if all plug-ins shared a faulty decoder?** Cross-mode equality could pass, and a public arithmetic reference using the same decoder could agree. A literal input and externally constructed output that exercise the fault can expose it. A passing literal fixture covers only the values it tests.
5. **What is the strongest timing claim supported here?** Given these modes, geometry, inputs and depth, one MMA advanced the selected state’s counter by the reported number, consistent with its per-tile callback contract. No elapsed hardware time, energy, concurrent-core schedule or compiler choice follows.

## Design exercises

1. For the public 31×19 edge on 16×16 PEs at depth two, predict the WS/OS/RS charges at K=15 and K=16. Compare with the recorded K=17 row. Mark which rows are predictions, not executions.
2. Design a false-green multicore sweep with correct peer agreement but a wrong result. Add a check that detects it without borrowing WS as the reference. What second check would detect stale cost columns?
3. An automated importer keeps rows with `live_mma_cycles > 0` and returns success if any row passes. Use the S4 mismatch to explain exactly what it would admit. Specify a replacement acceptance rule for the positive run and for the deliberate negative.
4. A placement report proposes a 158-cycle minimum and a bandwidth report proposes a twofold useful speedup. Identify one observation that disproves each statement. Can either report be added to the public edge MMA delta to obtain job latency?

### Exercise answers

1. Below and at the boundary there are four spatial tiles and one K tile, with total `m+n=100`. At K=15, K work is 60, OS surcharge 16: WS/OS/RS = **260/76/164**. At K=16 they are **264/80/168** (K work 64, same surcharge). These are derived predictions. At K=17 a second K tile repeats the spatial charge, adding four callbacks: **468/88/276** is both predicted and observed. One extra K position does not have a constant marginal cost.
2. Suppose each mode silently zeroed O instead of computing the dot products. All peer buffers could agree. Use nonzero, nonsymmetric inputs, optionally seed O, and compare every word to an externally formed `O_initial + WA` vector. Separately record the chosen ID and the owning state’s pre/post MMA counter; compare the difference with a valid-extent sum. Looking up a number under a printed name tests neither execution nor accounting.
3. The mutated WS edge has a perfectly plausible positive cost, 468, and 20 peers pass. Dropping its `FAIL` would admit a known numerical disagreement. For a positive run require the expected matrix of case keys, all passing observations, completion and exit zero. For this negative require exactly the targeted row failure, the actual/expected first words `3fa10000`/`3fa10001`, and child exit **1**. Do not count a missing process or arbitrary nonzero as a successful mutation test.
4. One legal 133-cycle schedule defeats 158 as a minimum. Holding useful work and interval fixed gives 0.75 GB/s useful in both arms; only occupied bandwidth doubles. Neither quantity shares the MMA counter’s interval or producer. A job-latency claim needs a common schedule, including dependencies, transfers and overlap.

## Conclusion

For the four depth-two public shapes, OS has the lowest live MMA estimate among three modes that pass the single-state functional gate. The same edge shape at depth one selects RS under that objective. The result worth carrying forward is the condition on that choice: it holds for a particular estimator, at a specified depth, after checking the executing state and the output. Keep those conditions with the number whenever it leaves the sweep table.

[Next: Chapter 22 — Lessons from the Exploration Portfolio](22-lessons-from-the-exploration-portfolio.md)
