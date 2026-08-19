# Chapter 22 read-only claim extraction

## Conventions

Each claim inherits its report header’s exact `Path/SHA`, question (`Q`), alternatives (`Alt`), workload (`WL`), varied axes (`Axes`), controls (`Ctl`), objective (`Obj`), producer/formula/units (`Prod`), current evidence owner (`Owner`), and verbatim report limitation (`Lim`) unless overridden.

- **Type:** `quant` quantitative; `dir` directional; `presc` prescriptive; `func` functional.
- **Disposition:** `retained`, `qualified`, `superseded`, `rejected`, `blocked`.
- **Tags:** `Q=` quantified objectives; `D=` directional objectives; `U=` unknown decisive objectives.
- **Domain:** exactly one metric domain per claim.
- **Missing:** decisive dimensions absent from the report.
- **Safe:** safe replacement.
- **Reverse:** evidence or condition that could reverse/open the conclusion.
- “Owner: none exact” means no claim-specific current book owner was discoverable; the Chapter 22 framing requirement remains the nearest current reference.

---

## Geometry and balance

### 1. `aspect-ratio-alignment-sweep.md` — **6 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/aspect-ratio-alignment-sweep.md` — `05739576b3f6f98b194122c569abf78aa18d7d3cb23f55590ffa9d8cbaf448ed`  
**Q/Alt/WL/Axes/Ctl:** alignment/aspect-ratio effect; alternative M/N shapes and padding/PE widths; GEMM, K=128; M,N; fixed 16×16 WS, depth 2, FP16 W/A, stated 32 B/cycle.  
**Obj/Prod:** useful-slot utilization, report TOPS, local cycles; Python/report-local formulas at lines 109–115; cycles, utilization %, TOPS.  
**Owner:** `notes/chapter-21-source-and-claim-ledger.md`, **C21.6–C21.7**; `notes/chapter-21-limitation-register.md`, C21.6–C21.7.  
**Lim (verbatim owner):** “the aspect-ratio rows execute Python formulas, not Tusim runtime workloads, and their two output sections use different fill/drain expressions.”

- **`aspect-alignment-step-penalty`** — Quote, **§Key Findings 1, lines 66–77:** “The PE utilization penalty for misaligned dimensions follows a step function based on the remainder modulo 16”. Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=slot-utilization`; `D=none`; `U=elapsed runtime, energy`. Missing: executable route, second-axis sensitivity, edge-cost definition. Alt: aligned versus remainder 4/8/12. Safe: tested-grid local arithmetic gives 62.5%, 83.3%, and 95.8% slot occupancy for the stated rows. Reverse: a linked implementation with edge-gated MACs or different tiling.
- **`aspect-shape-symmetry`** — Quote, **§Key Findings 2, lines 79–81:** “For perfectly aligned dimensions, a 16×256 and 256×16 matrix have identical cycle counts and TOPS”. Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=local cycles,TOPS`; `U=physical traffic`. Missing: nonsymmetric W/A placement and route. Alt: tall-skinny versus short-wide. Safe: the report’s symmetric formula gives equal values for those two rows. Reverse: producer with operand-specific movement or asymmetric PE geometry.
- **`aspect-dma-amortization`** — Quote, **§Key Findings 3, lines 85–88:** “For 16×16 output: DMA = 67.3% of total cycles … For 256×256 output: DMA = 20.0%”. Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=cycle shares`; `U=linked DMA timing`. Missing: executable DMA producer and overlap. Alt: small versus large output. Safe: the local serialized formula’s DMA share falls over these tested rows. Reverse: capacity tiling, overlap, or different byte accounting.
- **`aspect-m200-near-aligned`** — Quote, **§Key Findings 4, lines 90–92:** “M=200 (12.5 tile rows) wastes only 3.8% of throughput.” Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=slot waste`; `U=real-layer representativeness`. Missing: N sensitivity and actual model traces. Alt: M=200 versus aligned M=192/208. Safe: local useful-slot utilization is 96.2% for the tested geometry. Reverse: another N, PE shape, or edge execution policy.
- **`aspect-prefer-common-divisors`** — Quote, **§Actionable Conclusion, lines 94–96:** “When sizing PE arrays, prefer divisors of common layer dimensions.” Type `presc`; **rejected**. Domain `local_formula_cycles`. Tags `Q=local utilization`; `D=architecture preference`; `U=area,power,frequency,workload distribution`. Missing: global workload mix and physical costs. Alt: widths 16, 12, 10, other shapes. Safe: evaluate candidate widths against an explicit workload distribution; no universal width follows. Reverse: representative traces plus comparable cost evidence.
- **`aspect-pad-to-multiple-16`** — Quote, **§Actionable Conclusion, lines 98–101:** “Pad input dimensions to multiples of 16 to avoid edge-tile waste (≤ 3.8% overhead for any non-zero remainder, ≤ 37.5% for remainder=4)”. Type `presc`; **rejected**. Domain `local_formula_cycles`. Tags `Q=claimed overhead`; `D=compiler policy`; `U=padding compute,correctness`. Missing: executable compiler/runtime bridge. Alt: partial tiles versus zero padding. Safe: padding remains an untested compiler hypothesis. Reverse: an executable padding comparison preserving useful-work semantics.

**Flags:** duplicate of the same alignment preference at lines 96 and 103. **Arithmetic/logical contradiction:** “≤3.8% … for any non-zero remainder” conflicts with its own remainder-4 value of 37.5%; C21.7 rejects the global bound.

---

### 2. `bus-width-sweep-gemm128.md` — **5 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/bus-width-sweep-gemm128.md` — `d3e6c490e78c52d647b90749d819da5a8f8b87882cdaa2f41a96eba785d16de1`  
**Q/Alt/WL/Axes/Ctl:** 16×16 versus 32×32 under bus widths 32–1024 bits; GEMM 128×128×256; bus width and PE size; WS, depth 2, 1 GHz, FP16 W/A and FP32 O.  
**Obj/Prod:** throughput/utilization and area proxy; report-local serialized compute+DMA formula, lines 101–106; cycles, TOPS, percentages.  
**Owner:** `notes/chapter-07-source-and-claim-ledger.md:54–59` and `notes/chapter-10-source-and-claim-ledger.md`, C10.18/C10.22/C10.26/C10.32.  
**Lim:** “analytical cycle model validated against cmodel output” (lines 97–99); current owner limits linked estimates to deterministic, uncalibrated producer-local cycles.

- **`bus-32pe-half-util-crossover`** — Quote, **§Key Findings 1, lines 57–61:** “The exact crossover point (50% util) is at ~360 bits (45 B/cycle), producing ~1.0 TOPS.” Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=utilization,TOPS`; `U=real bus service`. Missing: discrete realizable widths and active config reachability. Alt: 256 versus 512 bits. Safe: the report formula crosses 50% between those sampled widths. Reverse: linked timing or changed byte model.
- **`bus-dma-gates-pe-scaling`** — Quote, **§Key Findings 2, lines 63–65:** “The 32×32 array has 4× the MACs of 16×16 but only achieves 2.20× the throughput at 256-bit.” Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=throughput`; `D=balance`; `U=area/frequency`. Missing: calibrated DMA and PE cost. Alt: 16×16 versus 32×32. Safe: local serialized formula shows sublinear speedup at fixed 256-bit width. Reverse: overlap, wider active DMA, or changed producer.
- **`bus-16pe-saturates-first`** — Quote, **§Key Findings 3, line 76:** “16×16 at 1024-bit achieves 91.3% utilization … But 32×32 at 1024-bit still has 27.2% DMA overhead”. Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=utilization,DMA share`; `U=physical saturation`. Missing: SRAM-side bandwidth and frequency. Alt: two arrays at 1024 bits. Safe: the local formula’s smaller array approaches its formula peak sooner. Reverse: internal movement limits or linked estimator.
- **`bus-32pe-area-poor-below512`** — Quote, **§Key Findings 4, lines 78–85:** “A 32×32 array with a 256-bit bus is a poor architectural choice — you pay 4× for 2.2×.” Type `presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=throughput ratio`; `D=area efficiency`; `U=actual area,power,frequency`. Missing: physical cost model. Alt: 16×16/256 versus 32×32/256–512. Safe: 32×32/256 is less throughput-per-assumed-MAC-area under this proxy; architecture choice remains open. Reverse: calibrated area or workload value of absolute throughput.
- **`bus-16bits-per-row-rule`** — Quote, **§Actionable Conclusion, lines 89–95:** “The optimal bus width per PE row scales roughly linearly … 16 bits/PE-row.” Type `presc`; **rejected**. Domain `local_formula_cycles`. Tags `Q=two sampled points`; `D=rule`; `U=64×64 evidence,cost`. Missing: validation beyond two unequal-utilization points. Alt: proportional versus workload-specific bus scaling. Safe: treat 16 bits/row as a report-local hypothesis, not an optimum. Reverse: multi-workload linked sweep with cost objectives.

**Flags:** duplicates bandwidth-balance conclusions in `dataflow-pe-interaction`, `pe-array-sweep`, and `workload-scaling-pe-optimal`.

---

### 3. `dataflow-comparison-gemm128.md` — **4 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/dataflow-comparison-gemm128.md` — `5884c943eadf6b92021c901d8c694be66ba89bd5f1e2190a33d6fdede0a2646d`  
**Q/Alt/WL/Axes/Ctl:** WS versus OS; GEMM 128×128×K; K and secondary PE shape; 16×16 primary, depth 2, stated 32 B/cycle.  
**Obj/Prod:** report-local WS/OS formulas at lines 23–32; cycles, overhead %, speedup.  
**Owner:** Chapter 21 **C21.3**; Chapter 7 ledger lines 54–62.  
**Lim (verbatim report):** “The TU cmodel's output-stationary plugin has an initialization segfault in the current build — OS cycle counts here are analytical.” (lines 89–91)

- **`dfcomp-negligible-k256`** — Quote, **§Key Finding, lines 67–71:** “For K=256, the fill+drain overhead is only 0.2% … For any K ≥ 64, the overhead drops below 1%.” Type `quant`; **rejected** as current dataflow evidence. Domain `local_formula_cycles`. Tags `Q=local overhead`; `U=linked route`. Missing: effective selector and linked equations. Alt: WS/OS. Safe: only this handwritten formula family makes the gap sub-1%. Reverse: linked WS/OS estimates or corrected active-route sweep.
- **`dfcomp-smallk-boundaries`** — Quote, **§When does dataflow choice matter?, lines 73–76:** “Small K (< 32): Overhead reaches 3.1% at K=16.” Type `quant`; **qualified** only as local sensitivity. Domain `local_formula_cycles`. Tags `Q=overhead`; `U=attention/depthwise mapping`. Missing: executable layer route. Alt: K=16/32/64+. Safe: local fixed-overhead fraction grows as K falls. Reverse: route-specific producer with per-K-tile terms.
- **`dfcomp-dma-dominant`** — Quote, **§Actionable Conclusion, line 80:** “The dominant bottleneck is DMA bandwidth (5,120 cycles for 160 KB at 32 B/cycle), not dataflow pipeline latency.” Type `dir`; **qualified**. Domain `local_formula_cycles`. Tags `Q=local cycles`; `D=bottleneck`; `U=overlap/linked DMA`. Missing: common producer for DMA and dataflow. Alt: optimize DMA versus dataflow. Safe: serialized report arithmetic assigns more cycles to DMA than its shape-level fill/drain term. Reverse: executable integrated producer.
- **`dfcomp-defer-dataflow`** — Quote, **§Actionable Conclusion, lines 78–87:** “Do not optimize for dataflow choice at this stage … Defer this decision until those workloads are measured on real traces.” Type `presc`; **rejected** in its universal premise, with the final deferral retained. Domain `local_formula_cycles`. Tags `D=design priority`; `U=traffic,area,frequency,correct route`. Missing: physical movement and active selection. Alt: WS/OS and defer/open. Safe: keep the decision open pending effective-route, producer-specific evidence. Reverse: representative executable traces.

**Flags:** conflicts materially with `dataflow-rs-comparison-gemm128.md` and pipeline/dataflow reports; Chapter 21 C21.3 proves distinct producers and ineffective labeled route.

---

### 4. `dataflow-pe-interaction.md` — **5 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/dataflow-pe-interaction.md` — `87a728d00ec60ce988878f26708a25a20f415f811c8c3d43b4d17800e6119968`  
**Q/Alt/WL/Axes/Ctl:** WS/OS/RS × 8–64 square PE; GEMM 128×128×256; dataflow and PE size; depth 2, 256-bit bus.  
**Obj/Prod:** shape-level local formulas lines 25–29; cycles, TOPS, utilization.  
**Owner:** Chapter 21 C21.3; Chapter 7 ledger lines 54–62.  
**Lim:** “analytical cycle model” (line 20); current owner: functional rows, effective route, local equations, and linked estimators are separate.

- **`dfpe-subpoint1-gap`** — Quote, **§Key Finding, line 55:** “The fill/drain overhead is <0.1% of total cycles at all PE sizes. OS wins by at most 64 cycles out of 71,744”. Type `quant`; **rejected** as current physical ranking. Domain `local_formula_cycles`. Tags `Q=local gap`; `U=linked timing`. Missing: active route and current equations. Alt: WS/OS/RS. Safe: this formula family gives a small gap for K=256. Reverse: linked producer.
- **`dfpe-os-local-winner`** — Quote, **§Best dataflow, lines 59–62:** “Best dataflow = OS” for all four PE sizes. Type `quant`; **rejected**. Domain `local_formula_cycles`. Tags `Q=local TOPS`; `D=winner`; `U=bandwidth/traffic`. Missing: OS cost and effective selection. Alt: three dataflows. Safe: OS is algebraically lowest only in this local equation. Reverse: linked route or movement costs.
- **`dfpe-dma-share-rises`** — Quote, **§The real bottleneck, line 75:** “At 8×8 PE, DMA is … 8.6% … At 64×64 PE … 85.6%”. Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=cycle share`; `D=balance`; `U=integrated DMA`. Missing: common elapsed-time producer. Alt: PE sizes. Safe: fixed serialized DMA increasingly dominates this local formula as compute falls. Reverse: bus/overlap changes.
- **`dfpe-dataflow-second-order`** — Quote, **§Architectural implications, line 86:** “Dataflow is a second-order concern for K≥64 … pick whatever dataflow is simpler”. Type `presc`; **rejected**. Domain `local_formula_cycles`. Tags `D=simplicity preference`; `U=physical movement,area,frequency`. Missing: distinct dataflow costs. Alt: WS/OS/RS. Safe: no universal dataflow preference follows. Reverse: calibrated physical trade-off.
- **`dfpe-compute-dma-knee`** — Quote, **§Architectural implications, line 90:** “The crossover is between 16×16 and 32×32”. Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=compute/DMA ratio`; `U=cost objective`. Missing: workload sensitivity. Alt: 16×16 versus 32×32. Safe: local serialized terms cross between those points. Reverse: bus width, workload, or active estimator.

---

### 5. `dataflow-rs-comparison-gemm128.md` — **4 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/dataflow-rs-comparison-gemm128.md` — `a2e0824dd548540e5df6021296fe41f3203f8081f133cf4ab62bbecb84041e00`  
**Q/Alt/WL/Axes/Ctl:** WS/OS/RS; GEMM 128×128×256; dataflow; 16×16, depth 2, 256-bit, 1 GHz.  
**Obj/Prod:** functional cmodel outputs plus separate per-tile handwritten cycle formula; max error and cycles/TOPS/utilization.  
**Owner:** Chapter 7 ledger lines 53–62; Chapter 21 C21.3.  
**Lim:** “analytical cycle model … functional correctness verified via cmodel” (line 19): two producer classes.

- **`dfrs-bit-identical-fixture`** — Quote, **§Functional Correctness, line 23:** “All three dataflows produce bit-identical results (max error < 1e-5 vs WS baseline)”. Type `func`; **qualified**. Domain `noncycle_functional_or_structure`. Tags `Q=fixture error`; `U=general correctness`. Missing: nonsymmetric and subnormal discriminators; Chapter 7 finds shared FP16 subnormal defect. Alt: three labeled executions. Safe: bounded displayed values match; no physical-movement conclusion. Reverse: discriminating fixtures.
- **`dfrs-20-10-percent`** — Quote, **§Key Finding, line 56:** “OS gives 20% faster throughput than WS … RS gives 10%.” Type `quant`; **rejected**. Domain `local_formula_cycles`. Tags `Q=report speedup`; `U=linked producer`. Missing: local/linked equation reconciliation. Alt: all three. Safe: these percentages belong only to this report formula. Reverse: current linked estimates.
- **`dfrs-os-rs-ws-ranking`** — Quote, **§Key Finding, lines 60–65:** “OS is best … RS is a practical compromise … WS is the simplest”. Type `presc`; **rejected**. Domain `local_formula_cycles`. Tags `Q=local utilization`; `D=bandwidth/simplicity`; `U=actual movement/area`. Missing: quantified bandwidth and physical design. Alt: OS, RS, WS. Safe: retain the alternatives, not the winner. Reverse: comparable route-specific traffic/cost evidence.
- **`dfrs-ranking-converges-k`** — Quote, **line 65:** “all three dataflows converge as K→∞, but for finite K … OS > RS > WS.” Type `dir`; **superseded**. Domain `local_formula_cycles`. Tags `D=asymptotic ranking`; `U=current formula`. Missing: pinned per-K-tile estimator terms. Alt: three formulas. Safe: the statement describes this handwritten algebra only. Reverse: revised equation.

**Flags:** direct arithmetic contradiction with `dataflow-comparison-gemm128.md` (approximately equal) and `dataflow-pe-interaction.md` (<0.1%); all are different local formulas.

---

### 6. `k-sweep-dma-crossover.md` — **6 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/k-sweep-dma-crossover.md` — `df60e89b51b934011e1ed0ea24add7fc726e4f77f1a1c479eb49ee85349f0be5`  
**Q/Alt/WL/Axes/Ctl:** K=16–4096; GEMM M=N=128; K; 16×16 WS, depth 2, 256-bit.  
**Obj/Prod:** serialized local compute+DMA formula lines 24–30; cycles, TOPS, utilization.  
**Owner:** Chapter 7 ledger line 54; Chapter 10 C10.18/C10.22/C10.26; Chapter 22 framing E22.5.  
**Lim:** “analytical cycle model validated against cmodel perf reports” (line 19); no integrated/common-clock proof.

- **`k-crossover-64`** — Quote, **§Key Findings 1, line 58:** “At K=64, compute cycles (56.9%) first exceed DMA cycles (42.7%).” Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=cycle shares`; `U=linked balance`. Missing: active route and overlap. Alt: K<64 versus K≥64. Safe: local serialized formula crosses between K=32 and 64. Reverse: byte accounting or producer change.
- **`k-asymptotic-20pct`** — Quote, **§Key Findings 2, lines 80–85:** “DMA_W_A grows linearly with K, just like compute … practical ceiling of ~80% utilization”. Type `quant`; **qualified** after correcting attribution. Domain `local_formula_cycles`. Tags `Q=asymptote`; `U=physical roofline`. Missing: calibrated bandwidth. Alt: finite K and K→∞. Safe: the local formula tends to roughly 80% because W/A DMA and compute both scale with K. Reverse: wider bus or reuse.
- **`k-obuffer-floor-misattribution`** — Quote, **heading/line 67 and line 69:** “Utilization saturates at ~80% due to O-buffer DMA floor”. Type `dir`; **rejected**. Domain `local_formula_cycles`. Tags `D=causal attribution`; `U=none`. Missing: arithmetic consistency. Alt: fixed O term versus linear W/A terms. Safe: O-buffer share tends to zero; the nonzero asymptote comes from W/A traffic. Reverse: none under the printed formula—this is internally disproved.
- **`k-diminishing-after256`** — Quote, **§Key Findings 3, line 100:** “Beyond K=256 … each doubling of K yields <5% throughput improvement.” Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=local TOPS gain`; `U=other workloads`. Missing: M/N and capacity variation. Alt: K doublings. Safe: true for the listed local rows. Reverse: different M/N/bus/reuse.
- **`k-smallk-fusion-benefit`** — Quote, **§Actionable Conclusion, line 134:** “Fusing the output DMA … would recover 15-30% throughput”. Type `presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=hypothetical gain`; `D=fusion`; `U=correctness,compiler bridge`. Missing: fused path. Alt: round-trip versus fusion. Safe: eliminating the modeled O transfer is a bounded hypothesis. Reverse: executable fusion with dependency/capacity evidence.
- **`k-viable-above64`** — Quote, **§Actionable Conclusion, line 130:** “For GEMM workloads with K ≥ 64 … compute-bound enough to be viable.” Type `presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=local utilization`; `D=viability`; `U=area,power,latency targets`. Missing: viability objective. Alt: same hardware across K. Safe: report arithmetic moves from DMA-majority to compute-majority at K=64; viability remains open. Reverse: explicit product constraints.

**Flags:** internal contradiction resolved by lines 80–82: the fixed O-buffer cannot cause the nonzero K→∞ DMA fraction.

---

### 7. `mac-density-dma-bound.md` — **5 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/mac-density-dma-bound.md` — `5d47403633d6db10f0158d9c1782edfee29d114b416e7c645b5b943fcd44135b`  
**Q/Alt/WL/Axes/Ctl:** 1–64/∞ MACs per PE; cubic 64/128/256 GEMMs; MAC density and workload K; 16×16 WS, depth 2, 256-bit.  
**Obj/Prod:** local cycles with compute divided by MAC density; cycles, TOPS, speedup, efficiency.  
**Owner:** Chapter 7 line 54; Chapter 10 C10.22/C10.32; no exact report owner.  
**Lim:** “analytical cycle model” (line 20); area and bandwidth are proxies, not physical results.

- **`mac-asymptotic-speedup-bounds`** — Quote, **results lines 47, 62, 77:** “Asymptotic max speedup” is 1.97×, 2.98×, and 4.99× for K=64/128/256. Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=local speedup bound`; `U=physical MAC scaling`. Missing: frequency/area effects. Alt: finite versus infinite compute. Safe: these are lower-cycle bounds of the printed formula. Reverse: overlap or different memory model.
- **`mac-sweetspot-depends-k`** — Quote, **§Key Finding, line 81:** “The MAC-density sweet spot depends on K-dimension, not M or N.” Type `dir`; **rejected** beyond tested cubic cases. Domain `local_formula_cycles`. Tags `D=sensitivity`; `U=M/N shapes`. Missing: independent M/N sweep. Alt: K=64/128/256. Safe: tested cubic rows show different diminishing-return points; no M/N independence follows. Reverse: nonsquare sweep.
- **`mac-attention-one-two`** — Quote, **§Architectural implications, line 113:** “For attention-heavy accelerators (small K): 1-2 MACs/PE is optimal.” Type `presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=local speedup`; `D=area`; `U=actual area,power,attention mapping`. Missing: cost model. Alt: 1/2/4+ MACs. Safe: local throughput-per-added-MAC diminishes quickly at K=64. Reverse: calibrated cost or wider DMA.
- **`mac-gemm-four-eight`** — Quote, **line 115:** “For GEMM-dominated accelerators (large K): 4-8 MACs/PE is justifiable.” Type `presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=local speedup efficiency`; `D=area worth`; `U=frequency,power`. Missing: physical implementation. Alt: 4/8/16. Safe: report arithmetic gives diminishing gains after 8 at K=256. Reverse: cost/frequency evidence.
- **`mac-dma-hard-floor`** — Quote, **§Conclusion, line 128:** “The DMA bus width sets a hard floor on cycle count.” Type `dir`; **qualified** within the serialized formula. Domain `local_formula_cycles`. Tags `Q=cycle floor`; `D=balance`; `U=overlap/integration`. Missing: concurrency. Alt: denser compute versus wider DMA. Safe: fixed DMA term is a floor in this non-overlapped model. Reverse: overlap or on-chip reuse removing transfers.

---

### 8. `pe-array-sweep-gemm128.md` — **3 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/pe-array-sweep-gemm128.md` — `de4bd331639c6fa5c4392d15ff1d016182201c9e3bb55ceadbb607a0b82e2e51`  
**Q/Alt/WL/Axes/Ctl:** PE shapes 4–128, aspect ≤8:1; GEMM 128×128×256; PE rows/cols; WS, depth 2, 32 B/cycle.  
**Obj/Prod:** local cycles/TOPS/utilization formula lines 65–69.  
**Owner:** `notes/chapter-06-source-and-claim-ledger.md:41–43`; Chapter 7 line 54.  
**Lim:** deterministic analytical model; no stochastic variation (line 71).

- **`pe-knee-16-32`** — Quote, **§Key Finding, lines 42–48:** “DMA transfer time dominates at PE arrays larger than ~16×16”. Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=cycle shares`; `U=active DMA`. Missing: cost/overlap. Alt: PE sizes. Safe: fixed serialized DMA exceeds compute at 32×32 in this fixture. Reverse: workload/bus change.
- **`pe-diminishing-beyond32`** — Quote, **lines 50–53:** “32×32 → 64×64: 4× PE area → 1.43× throughput”. Type `quant`; **blocked** as area conclusion. Domain `local_formula_cycles`. Tags `Q=throughput`; `D=assumed area`; `U=actual area/frequency`. Missing: area model. Alt: 32/64/128. Safe: throughput grows sublinearly with MAC count under local timing. Reverse: physical implementation.
- **`pe-sweetspot-16to32`** — Quote, **§Actionable Conclusion, line 57:** “a 16×16 to 32×32 PE array is the sweet spot.” Type `presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=local throughput`; `D=area efficiency`; `U=objective weights`. Missing: explicit objective and broader workload set. Alt: 16×16, 32×32, larger. Safe: no universal optimum; preserve both as local hypotheses. Reverse: workload/cost evidence.

---

### 9. `pipeline-depth-dataflow-interaction.md` — **5 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/pipeline-depth-dataflow-interaction.md` — `5738dc7daf6d269072c10361d06166a1fe88d49b2d72de6d00a2539ad55bc6e0`  
**Q/Alt/WL/Axes/Ctl:** WS/OS × depth 1/2/4/8; GEMM 128×128×256; dataflow and depth; 16×16, 256-bit.  
**Obj/Prod:** per-spatial-tile local formula that multiplies shape terms across 64 tiles; cycles/TOPS/utilization.  
**Owner:** Chapter 7 lines 54–62; Chapter 21 C21.3.  
**Lim:** “within 10% … due to DMA transfer granularity differences” (lines 103–105).

- **`pddf-os-zero-sensitivity`** — Quote, **§OS Sensitivity, line 64:** “OS shows zero sensitivity — all pipeline depths produce identical 21,504 cycles”. Type `quant`; **superseded**. Domain `local_formula_cycles`. Tags `Q=local cycles`; `U=linked OS equation`. Missing: pinned OS per-K overhead. Alt: depth values. Safe: pipeline depth is absent from this report’s OS equation only. Reverse: current linked producer.
- **`pddf-ws-linear-gap`** — Quote, **§Key Findings 2, line 77:** “At pdepth=8, OS is 38.1% faster … Every unit … adds ~4.8%”. Type `quant`; **rejected** as current ranking. Domain `local_formula_cycles`. Tags `Q=local gap`; `U=effective depth`. Missing: config reachability and formula reconciliation. Alt: WS/OS across depth. Safe: local formula gap grows linearly. Reverse: linked equations.
- **`pddf-spatial-compounding`** — Quote, **§Key Findings 3, line 83:** “The interaction is multiplicative: `overhead ∝ pdepth × tiles_m × tiles_n`.” Type `dir`; **superseded**. Domain `local_formula_cycles`. Tags `D=formula scaling`; `U=current linked composition`. Missing: actual fill/drain placement. Alt: tile counts/depths. Safe: describes this per-tile report formula. Reverse: source-defined per-K-tile accounting.
- **`pddf-keep-depth-low`** — Quote, **§Actionable Conclusion, line 97:** “keep pipeline depth as low as the physical design allows.” Type `presc`; **qualified** as directional only. Domain `local_formula_cycles`. Tags `D=cycle reduction`; `U=frequency,timing closure`. Missing: depth-frequency relation. Alt: shallow/deep. Safe: lower depth reduces this formula’s overhead at fixed clock. Reverse: higher frequency from deeper pipeline.
- **`pddf-always-os-tiled`** — Quote, **line 101:** “Always prefer OS dataflow for tiled workloads where tiles_m × tiles_n > 16.” Type `presc`; **rejected**. Domain `local_formula_cycles`. Tags `D=compiler choice`; `U=route,traffic,software bridge`. Missing: compiler path and physical costs. Alt: OS/WS. Safe: no universal compiler rule follows. Reverse: active route plus common-cost comparison.

---

### 10. `pipeline-depth-sweep-gemm128.md` — **5 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/pipeline-depth-sweep-gemm128.md` — `584a995330409269d37244ab24120c6bd54db4f58b2016db054f1288dc590f65`  
**Q/Alt/WL/Axes/Ctl:** depth 1–8 × PE 8/16/32; GEMM 128×128×256; depth and PE size; WS, 256-bit.  
**Obj/Prod:** report’s “hardware-accurate spatial-tile” formula; cycles/TOPS/utilization.  
**Owner:** Chapter 7 lines 54/59/62; Chapter 6 line 42.  
**Lim:** report itself identifies dispatcher disagreement at lines 77–81.

- **`pdsweep-small-array-absolute-loss`** — Quote, **§Key Findings 1, line 59:** “8×8 … drops utilization … a 23.8pp loss … 32×32 … 14.2pp”. Type `quant`; **qualified** only for local formula. Domain `local_formula_cycles`. Tags `Q=local utilization`; `U=linked depth behavior`. Missing: effective depth. Alt: PE sizes/depths. Safe: local table shows these changes. Reverse: linked producer.
- **`pdsweep-depth2-compromise`** — Quote, **§Key Findings 2, line 65:** “Default pdepth=2 is a reasonable compromise”. Type `presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=cycle difference`; `D=clock headroom`; `U=frequency evidence`. Missing: depth→clock data. Alt: depth 1/2/4. Safe: depth 2 is a historical default, not a proved optimum. Reverse: physical timing.
- **`pdsweep-marginal-cost`** — Quote, **§Key Findings 3, line 75:** “Each doubling of pdepth adds … a constant marginal cost in cycles.” Type `quant`; **qualified** within formula. Domain `local_formula_cycles`. Tags `Q=cycles`; `U=linked accounting`. Missing: current source composition. Alt: depth doublings. Safe: local algebra is linear in depth. Reverse: non-linear pipeline implementation.
- **`pdsweep-dispatcher-overcounts16x`** — Quote, **§Discrepancy, lines 79–81:** “dispatcher overcounts fill/drain by 16× … a bug”. Type `presc`; **rejected** as an established defect characterization. Domain `linked_plugin_cycles`. Tags `Q=claimed multiplier`; `D=hardware expectation`; `U=calibration`. Missing: specification proving desired placement. Alt: per-K-tile versus per-spatial-tile accounting. Safe: pinned dispatcher and report formula are distinct timing hypotheses. Reverse: normative timing contract.
- **`pdsweep-fix-dispatcher`** — Quote, **§Recommendation, lines 85–89:** “Fix the dispatcher — move fill/drain accounting outside the K-loop”. Type `presc`; **rejected**. Domain `linked_plugin_cycles`. Tags `D=implementation change`; `U=correct timing contract`. Missing: validated replacement semantics. Alt: preserve source, move terms, explicit state model. Safe: first specify and validate fill/drain ownership. Reverse: approved architecture timing model.

---

### 11. `pipeline-depth-workload-interaction.md` — **5 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/pipeline-depth-workload-interaction.md` — `57ab0041897ccb1be487a9b0dbaa5a5cd961063e313833bfb5e8dcf99063d9a1`  
**Q/Alt/WL/Axes/Ctl:** depth 1–8 × three GEMMs; workload size/K and depth; 16×16 WS, 256-bit.  
**Obj/Prod:** per-tile local formula lines 24–29; cycles, TOPS, utilization.  
**Owner:** Chapter 7 lines 54/59/62; no exact report owner.  
**Lim:** analytical model, medium workload cross-referenced from another report (line 19).

- **`pdwl-amortized-by-k`** — Quote, **§Key Findings 1, lines 76–86:** “Pdepth penalty is a fixed per-tile tax — amortized by K, not by M×N”. Type `dir`; **qualified** only for local formula. Domain `local_formula_cycles`. Tags `Q=per-tile fraction`; `D=amortization`; `U=linked accounting`. Missing: current source composition. Alt: K=64/256/1024. Safe: this report’s per-tile term becomes a smaller fraction as K rises. Reverse: per-K-tile producer.
- **`pdwl-five-percent-threshold`** — Quote, **§Key Findings 2, lines 90–101:** “`K ≥ pd × 640`” for ≤5% overhead. Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=threshold`; `U=runtime relevance`. Missing: definition uses compute-only denominator and fixed PE. Alt: depth values. Safe: threshold belongs to stated 16×16 local equation. Reverse: denominator/PE change.
- **`pdwl-small-v-large-loss`** — Quote, result summaries lines 46/59/72: pd=1→8 loss is 58.2%, 36.9%, and 16.3%. Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=utilization loss`; `U=linked timing`. Missing: objective beyond utilization. Alt: three workloads. Safe: local sensitivity decreases with larger K. Reverse: workload shape or linked producer.
- **`pdwl-optimize-dma-v-mac`** — Quote, **§Key Findings 3, line 115:** “for attention heads, optimize DMA bandwidth; for LLM layers, optimize MAC throughput.” Type `presc`; **blocked**. Domain `local_formula_cycles`. Tags `D=optimization target`; `U=real traces,cost`. Missing: representative operator mapping. Alt: DMA versus compute investments. Safe: treat as workload-specific hypotheses. Reverse: measured traces.
- **`pdwl-runtime-depth-register`** — Quote, **§Implications, lines 123–125:** “should expose pdepth as a runtime register”. Type `presc`; **rejected** at current pin. Domain `noncycle_functional_or_structure`. Tags `D=configurability`; `U=hardware feasibility`. Missing: current conversion drops depth and plugin fallback is 2. Alt: static versus runtime depth. Safe: runtime depth is a future extension requiring full reachability. Reverse: implemented parser→runtime→consumer path.

---

### 12. `rs-pipeline-depth-sweep.md` — **5 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/rs-pipeline-depth-sweep.md` — `2105d56dbb84e92f23b2b12b5d118538342e3a55e1e80651e45e842a2f26137f`  
**Q/Alt/WL/Axes/Ctl:** WS/RS/OS × depth 1–8; GEMM 128×128×256; dataflow/depth; 16×16, 256-bit.  
**Obj/Prod:** test-derived handwritten per-tile formulas; cycles/TOPS/utilization.  
**Owner:** Chapter 7 lines 54–62; Chapter 21 C21.3.  
**Lim:** “All other pdepth values are analytical extrapolations” (lines 107–111).

- **`rspd-constant-1984-saving`** — Quote, **§Key Findings 1, lines 71–75:** “1,984 cycles regardless of pdepth”. Type `quant`; **qualified** as local algebra. Domain `local_formula_cycles`. Tags `Q=cycles`; `U=linked RS timing`. Missing: current producer reconciliation. Alt: RS versus WS. Safe: difference is constant under this report’s equations. Reverse: source equation change.
- **`rspd-rs-near-os-depth1`** — Quote, **§Key Findings 2, line 79:** “only 0.3% overhead vs OS”. Type `quant`; **rejected** as physical comparison. Domain `local_formula_cycles`. Tags `Q=local cycles`; `U=movement/route`. Missing: linked estimates and physical costs. Alt: RS/OS depth1. Safe: local formulas nearly tie. Reverse: linked route.
- **`rspd-rs-optimal-systolic`** — Quote, **line 81:** “RS at pdepth=1 is the optimal systolic configuration”. Type `presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=local TOPS`; `D=regularity`; `U=frequency,area`. Missing: physical design. Alt: WS/RS/OS. Safe: RS depth1 is a local formula hypothesis. Reverse: timing closure or traffic data.
- **`rspd-ranking-invariant`** — Quote, **§Key Findings 4, line 95:** “For all pipeline depths 1-8: OS > RS > WS.” Type `dir`; **superseded**. Domain `local_formula_cycles`. Tags `D=ranking`; `U=current linked equations`. Missing: active route. Alt: all three. Safe: ranking is algebraically forced by this report family. Reverse: linked producer.
- **`rspd-switch-os-deep`** — Quote, **§Actionable Conclusions, line 101:** “If pdepth cannot be kept shallow, switch to OS.” Type `presc`; **rejected**. Domain `local_formula_cycles`. Tags `D=dataflow choice`; `U=software/traffic/area`. Missing: effective selector and comparable costs. Alt: deep RS/WS versus OS. Safe: keep decision open. Reverse: route-specific evidence.

---

### 13. `workload-scaling-pe-optimal.md` — **5 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/workload-scaling-pe-optimal.md` — `7926f8c6b4f17355fe276c8e0ab41eef47a765f7ffb86dd02452c8c0283c4816`  
**Q/Alt/WL/Axes/Ctl:** PE 8–64 × four GEMMs; workload scale and PE size; WS depth2, 256-bit.  
**Obj/Prod:** local cycles/TOPS/utilization plus TOPS/MAC area proxy.  
**Owner:** Chapter 6 lines 41–43; Chapter 7 line 54; no exact report owner.  
**Lim:** analytical WS formula, no real traces; report itself asks for end-to-end traces at lines 154–159.

- **`wlpe-objective-split`** — Quote, **§Key Findings 1, lines 50–57:** “Best util PE” is 8×8 while “Best TOPS PE” is 64×64 for every row. Type `quant`; **retained** as an objective-conflict observation within the table. Domain `local_formula_cycles`. Tags `Q=utilization,TOPS`; `U=area/power`. Missing: objective selection. Alt: small efficient versus large fast array. Safe: different objectives select different alternatives. Reverse: adding cost constraints.
- **`wlpe-30x-flops-rule`** — Quote, **§Key Findings 2, line 70:** “Each 4× increase in PE area requires ~30× more FLOPs to maintain >50% utilization.” Type `dir`; **rejected** as general rule. Domain `local_formula_cycles`. Tags `Q=four sampled points`; `U=other shapes/buses`. Missing: regression/boundary validation. Alt: PE sizes. Safe: threshold moves upward in the sampled fixture; no universal factor follows. Reverse: denser sweep.
- **`wlpe-small-always-area-efficient`** — Quote, **§Key Findings 3, line 83:** “TOPS-per-MAC declines with PE size for all workloads”. Type `quant`; **qualified** as proxy. Domain `local_formula_cycles`. Tags `Q=TOPS/MAC`; `D=area proxy`; `U=actual area`. Missing: non-MAC area and frequency. Alt: PE sizes. Safe: report-local throughput per MAC declines. Reverse: physical cost.
- **`wlpe-tiered-pe-prescriptions`** — Quote, **§Actionable Conclusion, lines 127–133:** edge 8/16, medium 16, LLM 32; 64×64 considered above ~1B FLOPs. Type `presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=local utilization`; `D=target segmentation`; `U=real traces,cost`. Missing: representative workload distribution. Alt: multiple PE tiers. Safe: use these only as candidate configurations. Reverse: model traces and cost.
- **`wlpe-compiler-multiple-targets`** — Quote, **line 135:** “The compiler should be parameterized for multiple PE configurations”. Type `presc`; **blocked**. Domain `noncycle_functional_or_structure`. Tags `D=software policy`; `U=compiler/runtime bridge`. Missing: implemented target-selection path. Alt: fixed versus multi-target compiler. Safe: future design hypothesis. Reverse: implemented extension and validation.

**Flag:** title says “optimal,” but the report has incompatible winners for utilization, absolute TOPS, and proxy area efficiency; no single objective is defined.

---

## Memory and movement

### 14. `db-pe-size-goldilocks.md` — **6 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/db-pe-size-goldilocks.md` — `81a9f6edc4e6bb2405470d3ff07215fa768dae399dca9419e66b2bf86a3c4b02`  
**Q/Alt/WL/Axes/Ctl:** ideal DB on/off × PE 8–128; GEMM 128×128×256 with 32 KiB O-buffer; PE size and DB; WS depth2, 256-bit, two M tiles.  
**Obj/Prod:** ideal overlap formula lines 43–45; cycles/GFLOPS/speedup and assumed area.  
**Owner:** Chapter 16 C16.25–C16.28/C16.31/C16.36; Chapter 22 D22F07.  
**Lim (verbatim report):** “Double-buffering overlap assumes dual-port or banked SRAM enabling concurrent DMA and compute access.” (lines 170–174)

- **`dbpe-speedup-peaks32`** — Quote, **§Key Findings 1, line 62:** “DB speedup follows a ∩-shaped curve — peaks at 32×32 PE”. Type `quant`; **qualified** as ideal formula. Domain `db_ideal_overlap_formula_cycles`. Tags `Q=ideal speedup`; `U=executable overlap`. Missing: byte visibility and shared-resource cap. Alt: five PE sizes. Safe: ideal model’s maximum sampled speedup is 1.332× at 32×32. Reverse: executable controller or shared-port model.
- **`dbpe-32db-matches64`** — Quote, **§Key Findings 2, line 92:** “32×32 … with double-buffering delivers the same throughput as a 64×64 … without DB”. Type `quant`; **qualified** as ideal arithmetic. Domain `db_ideal_overlap_formula_cycles`. Tags `Q=GFLOPS equality`; `U=implementation correctness`. Missing: ordinary DB reachability. Alt: 32+DB versus 64 no-DB. Safe: ideal formula rows nearly tie, 0.908 versus 0.909. Reverse: executable overlap.
- **`dbpe-38pct-area`** — Quote, **line 92:** “DB delivers 64×64-class throughput at ~38% of the silicon area.” Type `quant`; **rejected**. Domain `db_ideal_overlap_formula_cycles`. Tags `Q=assumed area`; `U=real SRAM,DMA,control area`. Missing: area model and 2× allocation. Alt: two architectures. Safe: no area ratio is established. Reverse: synthesized area.
- **`dbpe-goldilocks-formula`** — Quote, **§Key Findings 4, lines 108–126:** “compute_per_tile ≈ DMA_inter_tile” and “between 0.5× and 2× … gives >25% DB speedup.” Type `dir`; **qualified** as heuristic, with generalized `pe_optimal` formula **rejected**. Domain `db_ideal_overlap_formula_cycles`. Tags `Q=sampled overlap`; `D=balance heuristic`; `U=dimensional generality`. Missing: dimensional validation and workload sweep. Alt: compute≫/≈/≪DMA. Safe: overlap is locally largest near balanced windows. Reverse: broader recomputation.
- **`dbpe-must-have16-32`** — Quote, **§Actionable Conclusion, lines 156–160:** “DB is a must-have feature” for 16×16 or 32×32. Type `presc`; **rejected**. Domain `db_ideal_overlap_formula_cycles`. Tags `Q=ideal 20–33%`; `D=priority`; `U=correctness,area,power`. Missing: current controller exposes stale data. Alt: no DB, DB, partitioned banking. Safe: no executable evidence ranks DB at this pin. Reverse: correct ordinary-operation bridge.
- **`dbpe-compiler-emits-db`** — Quote, **line 168:** “The compiler should emit double-buffered DMA instructions when tiling is active … overhead … is zero”. Type `presc`; **rejected**. Domain `db_ideal_overlap_formula_cycles`. Tags `D=compiler scheduling`; `U=bridge,dependency,control cost`. Missing: compiler path and valid DMA-to-shadow semantics. Alt: serialized, DB, event-driven schedule. Safe: future compiler hypothesis only. Reverse: executable end-to-end schedule.

---

### 15. `dma-channel-queue-sweep.md` — **7 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/dma-channel-queue-sweep.md` — `bfb6861be4b2425e97c80cad5c31f76fb28c8bbe86825f084c2d924cc00bb271`  
**Q/Alt/WL/Axes/Ctl:** 1/2/3 channels × queue 1/4/8/16; single and two-pass GEMM 128×128×256; channel count, queue depth, secondary bus/DB; 16×16 WS.  
**Obj/Prod:** report-local pipelining formulas lines 201–206; cycles/TOPS/speedup.  
**Owner:** Chapter 10 C10.13–C10.22/C10.29/C10.32/C10.35; Chapter 16 C16.11–C16.17/C16.36.  
**Lim:** “Analytical cycle model with pipelining formulas.” (line 19)

- **`dmaq-two-ch-single-tile`** — Quote, **§Key Findings 1, lines 156–160:** “Two channels is the sweet spot for single-tile workloads … 10.5%”. Type `quant/presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=analytical speedup`; `D=channel choice`; `U=elapsed parallelism`. Missing: actual shared-fabric timing. Alt: 1/2/3. Safe: report formula gives 2=3 channels for this single tile; no hardware optimum. Reverse: executable elapsed-time producer.
- **`dmaq-third-channel-zero`** — Quote, **lines 111 and 158:** “Channel 3 … provides zero benefit for single-tile GEMM.” Type `quant`; **qualified** only as local formula. Domain `local_formula_cycles`. Tags `Q=zero delta`; `U=other schedules`. Missing: real overlap semantics. Alt: 2 versus 3 channels. Safe: the report’s serialized schedule gives equal totals. Reverse: concurrent next-operation preload/store.
- **`dmaq-three-ch-tiled`** — Quote, **§Key Findings 2, lines 162–169:** “Three channels matter for tiled workloads … Net benefit: 17%”. Type `quant/presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=analytical speedup`; `D=dedicated O channel`; `U=valid tiling/overlap`. Missing: current stale-active-data defect. Alt: 1/2/3 channels. Safe: future schedule hypothesis. Reverse: correct byte-visibility bridge.
- **`dmaq-depth4-sufficient`** — Quote, **§Key Findings 3, lines 171–175:** “Queue depth > 4 is unnecessary … 4-entry descriptor queues … sufficient”. Type `presc`; **rejected**. Domain `local_formula_cycles`. Tags `Q=table plateau`; `U=actual queue semantics`. Missing: descriptor-chain corruption and real descriptor count. Alt: 1/4/8/16. Safe: local table plateaus at four; current engine queue semantics do not validate it. Reverse: safe executable queue sweep.
- **`dmaq-benefit-inverse-bus`** — Quote, **§Key Findings 4, lines 177–181:** “At 128-bit bus, 3 channels save 23% … at 1024-bit, only 3%.” Type `quant`; **qualified** as formula sensitivity. Domain `local_formula_cycles`. Tags `Q=local speedup`; `U=shared bandwidth`. Missing: real per-channel contention. Alt: bus widths. Safe: formula benefit shrinks as serialized DMA terms shrink. Reverse: shared-fabric model.
- **`dmaq-db-complementary`** — Quote, **§Key Findings 5, lines 183–187:** “Channel count and double-buffering are complementary, not redundant … implement both.” Type `presc`; **rejected**. Domain `db_ideal_overlap_formula_cycles`. Tags `Q=analytical combined speedup`; `D=architecture`; `U=correctness,area,power`. Missing: valid DB bridge and common resource cap. Alt: either/both/neither. Safe: the mechanisms are conceptually distinct; combined preference remains open. Reverse: integrated comparison.
- **`dmaq-default-three-depth4`** — Quote, **§Actionable Conclusions, lines 191–195:** “Default of 3 channels is well-motivated” and “Queue depth of 4 is right-sized.” Type `presc`; **rejected**. Domain `local_formula_cycles`. Tags `D=defaults`; `U=workload mix,safety`. Missing: current safe channel bound is ≤3, but no measured optimum. Alt: 2/3 channels and queue sizes. Safe: retain current defaults as implementation facts, not optimality claims. Reverse: safe multi-workload executable study.

**Flags:** claim that O store “cannot overlap” at lines 44–47 conflicts with later prose saying it “fits entirely within the compute window”; formulas and narrative use different overlap concepts. Current `estimated_cycles` is additive service, not elapsed time (C10.22).

---

### 16. `double-buffer-mtiling-recovery.md` — **7 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/double-buffer-mtiling-recovery.md` — `19b3a5b97e3b0dcc869f353e3b2e16fbf2e712643b8bbed372f977cfbb16b9a1`  
**Q/Alt/WL/Axes/Ctl:** DB on/off × O-buffer 16–128 KiB; GEMM 128×128×256; DB and O capacity; 16×16 WS depth2, ideal independent access.  
**Obj/Prod:** ideal overlap formula lines 26–39; cycles/TOPS/speedup.  
**Owner:** Chapter 16 C16.25–C16.28a/C16.31/C16.36; Chapter 22 D22F08.  
**Lim (verbatim report):** “If DMA and compute share a single SRAM port, the overlap is zero” (line 138).

- **`dbmt-16beats64`** — Quote, **§Key Findings 1, line 65:** “0.429 TOPS (16 KB + DB) > 0.372 TOPS (64 KB, no DB)”. Type `quant`; **qualified** as ideal arithmetic. Domain `db_ideal_overlap_formula_cycles`. Tags `Q=TOPS,ideal speedup`; `U=executable overlap`. Missing: physical 2× allocation and byte visibility. Alt: 16 KiB ping-pong versus 64 KiB single. Safe: ideal report formula ranks these rows; no runtime ranking follows. Reverse: valid controller/port model.
- **`dbmt-flat32to56`** — Quote, **§Key Findings 2, line 71:** “From 32 KB to 56 KB, all DB configurations achieve 0.409 TOPS”. Type `quant`; **qualified**. Domain `db_ideal_overlap_formula_cycles`. Tags `Q=local TOPS`; `U=real contention`. Missing: capacity/ownership implementation. Alt: O sizes. Safe: report formula gives a two-tile plateau. Reverse: executable resource model.
- **`dbmt-smallest-compute-dense`** — Quote, **§Key Findings 3, lines 75–85:** “optimal strategy is the smallest O-buffer that creates compute-dense tiles”. Type `presc`; **blocked**. Domain `db_ideal_overlap_formula_cycles`. Tags `Q=ideal TOPS`; `D=capacity policy`; `U=area/control/correctness`. Missing: physical doubled allocation and ordinary reachability. Alt: largest single buffer versus smaller ping-pong. Safe: preserve both alternatives; optimum open. Reverse: integrated cost model.
- **`dbmt-areload-100pct-hidden`** — Quote, **§Key Findings 4, lines 91–97:** “Hidden by overlap … 100%”. Type `quant`; **qualified** only under independent resources. Domain `db_ideal_overlap_formula_cycles`. Tags `Q=ideal hidden cycles`; `U=shared-resource behavior`. Missing: combined preload/store cap. Alt: serialized versus ideal overlap. Safe: ideal windows can cover the printed A terms. Reverse: shared port or invalid shadow targeting.
- **`dbmt-two-bank-three-percent`** — Quote, **§Bandwidth Constraints, line 144:** “use banked SRAM with at least 2 banks per buffer … ~3% additional SRAM area”. Type `presc`; **rejected**. Domain `db_ideal_overlap_formula_cycles`. Tags `D=banking choice`; `Q=claimed area`; `U=synthesis/conflicts`. Missing: area source and arbitration behavior. Alt: dual-port, banked, shadow buffers. Safe: these are distinct implementation alternatives with unknown cost. Reverse: synthesized banked design.
- **`dbmt-highest-leverage`** — Quote, **§Actionable Conclusion, line 148:** “single highest-leverage architectural feature … 4× SRAM savings with 15% throughput improvement.” Type `presc`; **rejected**. Domain `db_ideal_overlap_formula_cycles`. Tags `Q=ideal throughput/capacity`; `D=priority`; `U=correctness,area,power`. Missing: physical allocation and current stale-data defect. Alt: larger buffer, DB, banking, wider DMA. Safe: report-local ideal result, not architecture priority. Reverse: executable, costed comparison.
- **`dbmt-compiler-prefers-mtiling`** — Quote, **line 162:** “The compiler should prefer M-tiling with DB over single-tile execution.” Type `presc`; **rejected**. Domain `db_ideal_overlap_formula_cycles`. Tags `D=compiler policy`; `U=compiler bridge,continuation correctness`. Missing: valid software/hardware path. Alt: single tile versus 2–4 DB tiles. Safe: future tiling hypothesis only. Reverse: end-to-end executable scheduling.

**Flags:** Chapter 16 **C16.28a** disproves the report’s generalized threshold: report says `m_per_tile ≥20`; exact tile-dependent recomputation finds continuous 18.2857 and first ceiling-aware passing integer 17. Claims of “16 KB savings” must account for 32 KiB physical ping-pong allocation (C16.26).

---

### 17. `dram-type-clock-sweep.md` — **6 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/dram-type-clock-sweep.md` — `5b706f0146bbd9323776b8273922b8ee64158727f91d68fa25e954e148780065`  
**Q/Alt/WL/Axes/Ctl:** seven DRAM types × 0.25–8 GHz; GEMM 128×128×256; DRAM type/clock, secondary 512-bit extrapolation; 16×16 WS, 256-bit.  
**Obj/Prod:** standalone `min(bus B/cycle, GB/s/clock)` formula; cycles/TOPS/loss.  
**Owner:** Chapter 15 **C15.23–C15.24**; Chapter 22 D22F06.  
**Lim:** report is analytical and does not call `dram_model.c` (current owner C15.23).

- **`dram-crossover-map`** — Quote, **§Key Findings 1, lines 90–99:** crossovers DDR4 0.8, DDR5 1.6, HBM2 8.0 GHz. Type `quant`; **qualified** as direct algebraic thresholds. Domain `local_formula_cycles`. Tags `Q=bandwidth crossover`; `U=physical sustained BW`. Missing: latency/access/window state. Alt: device types. Safe: these are thresholds of the printed bandwidth-only formula. Reverse: calibrated bandwidth or bus width.
- **`dram-hbm-wasted256`** — Quote, **§Key Findings 2, line 108:** “HBM's bandwidth advantage is entirely wasted on a 256-bit bus at realistic clock speeds.” Type `dir`; **qualified** only within bandwidth-only assumptions. Domain `local_formula_cycles`. Tags `Q=bus cap`; `D=device equivalence`; `U=latency/energy`. Missing: device latency and physical interface. Alt: HBM versus DDR. Safe: ≥256 GB/s presets are bus-capped in the local formula through 8 GHz. Reverse: wider bus or non-bandwidth costs.
- **`dram-ddr4-adequate1ghz`** — Quote, **§Key Findings 3, line 119:** “DDR4 costs only 6.5% throughput vs ideal DRAM.” Type `quant`; **qualified** after recomputation (~6.37%). Domain `local_formula_cycles`. Tags `Q=local loss`; `U=calibration`. Missing: standalone DRAM behavior and physical traffic. Alt: DDR4 versus ideal. Safe: formula predicts about 6.4% loss, not equality. Reverse: calibrated model.
- **`dram-hbm-zero-improvement`** — Quote, **line 119:** “Upgrading to HBM would yield zero improvement”. Type `presc`; **rejected** because it is paired with nonzero DDR4 loss. Domain `local_formula_cycles`. Tags `Q=claimed zero`; `D=device choice`; `U=cost/latency`. Missing: internal consistency and device costs. Alt: DDR4/HBM. Safe: formula gives HBM the ideal 0.372 versus DDR4 about 0.348 TOPS at 1 GHz. Reverse: none needed; printed constants disprove zero.
- **`dram-ddr5-hbm-transition`** — Quote, **§Key Findings 4, lines 121–123:** “DDR5→HBM transition point: ~4 GHz at 256-bit, ~2 GHz at 512-bit”. Type `presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=local throughput gap`; `D=device justification`; `U=cost,power,latency`. Missing: selection objective. Alt: DDR5/HBM. Safe: bandwidth loss grows beyond the algebraic crossover; device choice remains open. Reverse: cost/calibration.
- **`dram-dont-care-ddr4`** — Quote, **§Actionable Conclusion, line 127:** “DDR4, DDR5, and HBM all deliver identical performance.” Type `quant/presc`; **rejected**. Domain `local_formula_cycles`. Tags `Q=claimed equality`; `D=stick with DDR4`; `U=physical costs`. Missing: arithmetic consistency. Alt: device types. Safe: at 1 GHz the printed formula makes DDR5/HBM bus-limited and DDR4 about 6.4% slower. Reverse: DDR4 bandwidth ≥32 GB/s at 1 GHz or changed bus.

**Arithmetic contradictions, independently recomputed from printed constants:** at 8 GHz HBM2 **2.975**, DDR5 **1.424**, DDR4 **0.862 TOPS**, not 2.839/0.776/0.435. At 1 GHz DDR4 loses ~6.37%, contradicting “identical performance.” This exactly matches C15.23.

---

### 18. `gbuf-sizing-sweep.md` — **4 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/gbuf-sizing-sweep.md` — `e7255f53d149cbc5a1383603d283f08b428420d7ecd973c350862268cb7fdb1f`  
**Q/Alt/WL/Axes/Ctl:** GBUF 64 KiB–8 MiB × K64–8192; GEMM M=N=256; GBUF/K; 16×16, 128-bit, fixed SPADs.  
**Obj/Prod:** standalone C analytical hierarchy formula; DMA cycles/speedup/bytes.  
**Owner:** Chapter 9 **C9.8/C9.11/C9.14/C9.16/C9.19**; Chapter 15 **C15.32**; Chapter 22 framing line 221.  
**Lim (verbatim report):** “Analytical sweep (standalone C, no cmodel dependency)” (line 5).

- **`gbuf-weight-fit-threshold`** — Quote, **§Key Finding, lines 68–70:** “GBUF sizing is a binary threshold determined by weight footprint.” Type `quant`; **qualified** as standalone arithmetic. Domain `local_formula_cycles`. Tags `Q=DMA cycles,bytes`; `U=ordinary execution`. Missing: cache allocation/replacement and direct-MMA integration. Alt: below/at/above fit. Safe: standalone formula has a weight-fit threshold; current hierarchy does not establish this direct-MMA behavior. Reverse: integrated hierarchy producer.
- **`gbuf-k8192-twentyfold`** — Quote, **line 71:** “21.5M DMA cycles … 1.06M — 20× more DMA traffic”. Type `quant`; **qualified** for the raw cycle table, but conflicts with speedup table. Domain `local_formula_cycles`. Tags `Q=DMA-cycle ratio`; `U=end-to-end speed`. Missing: formula audit of speedup table. Alt: 64 KiB versus 8 MiB. Safe: raw table ratio is 20.2×. Reverse: corrected producer output.
- **`gbuf-size-to-footprint`** — Quote, **§Recommendations, line 76:** “Size GBUF to the weight footprint of the target workload.” Type `presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=standalone traffic`; `D=capacity sizing`; `U=area,power,real reuse`. Missing: integrated caller and workload distribution. Alt: fit/undersize/oversize. Safe: weight footprint is one candidate threshold, not a silicon-sizing rule. Reverse: integrated/costed evidence.
- **`gbuf-oversize-zero-benefit`** — Quote, **line 77:** “Oversizing GBUF beyond weight-fit yields zero DMA benefit. The extra silicon area is wasted”. Type `presc`; **rejected** beyond the local formula. Domain `local_formula_cycles`. Tags `Q=local DMA plateau`; `D=area`; `U=other data/contexts`. Missing: alternative GBUF uses and physical area. Alt: larger GBUF versus SRAM/PEs. Safe: no additional weight-reload reduction occurs in this standalone fixture. Reverse: other workloads/state uses.

**Arithmetic contradictions:** speedup table reports only 1.00× at K=128 although raw cycles are 94,208/32,768 = **2.875×**; at K=8192 it caps at 4.30× although raw ratio is **20.2×**. The prose’s 20× agrees with raw cycles, not the speedup table.

---

### 19. `sram-arbitration-sweep.md` — **4 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/sram-arbitration-sweep.md` — `f003fdbd73a32b42f8932b17c880dcb904d8daff05e3efe3cced2ec027df00d3`  
**Q/Alt/WL/Axes/Ctl:** NONE/RR/PRIORITY; synthetic balanced/read-heavy accesses; arbitration, active banks, operation count; 32 banks, one word/window, penalty 2.  
**Obj/Prod:** standalone C stall calculation; stall-return counts/cycles as labeled.  
**Owner:** Chapter 9 **C9.4–C9.6/C9.19**; Chapter 22 framing line 220.  
**Lim:** “Analytical sweep (standalone C, no cmodel dependency)” (line 4).

- **`sramarb-none-rr-equal`** — Quote, **§Key Findings 1, line 50:** “NONE and RR produce identical stall counts”. Type `quant`; **rejected** as evidence of live arbitration selection; retained only as table equality. Domain `sram_stall_returns`. Tags `Q=stall returns`; `U=live arb effect`. Missing: `arb_mode` consumer; C9.6 says none exists. Alt: NONE/RR. Safe: synthetic producer prints equal rows; live SRAM arbitration mode has no behavioral effect at the pin. Reverse: implemented selector.
- **`sramarb-priority-penalty`** — Quote, **§Key Findings 2, lines 56–58:** “+48% stalls … +20% stalls”. Type `quant`; **rejected** as current cmodel arbitration behavior. Domain `sram_stall_returns`. Tags `Q=synthetic stalls`; `U=live contention`. Missing: source reachability. Alt: PRIORITY versus NONE. Safe: standalone arithmetic applies an extra write penalty; current `arb_mode` does not select it. Reverse: linked implementation.
- **`sramarb-refill-dominates`** — Quote, **§Key Findings 3, line 64:** “dominant factor … is the 4-cycle bandwidth refill window, not the arbitration policy.” Type `dir`; **qualified** for exercised sequential bank-budget paths. Domain `sram_stall_returns`. Tags `Q=stall counts`; `D=bottleneck`; `U=physical timing`. Missing: concurrent same-bank requests. Alt: refill versus arbitration. Safe: deterministic budget refill dominates these synthetic sequential traces. Reverse: simultaneous-port workload.
- **`sramarb-rr-default`** — Quote, **line 66:** “RR is the safe default. PRIORITY should be considered for dual-ported SRAM designs”. Type `presc`; **rejected** for current implementation. Domain `sram_stall_returns`. Tags `D=policy`; `U=dual-port behavior`. Missing: active arb logic and physical model. Alt: NONE/RR/PRIORITY. Safe: policy choice remains future work. Reverse: implemented dual-port arbitration sweep.

---

### 20. `sram-obuffer-tiling-threshold.md` — **7 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/sram-obuffer-tiling-threshold.md` — `b55a3418a7f2913b7d64089c6b4c6869fb3266f34c5532cbce59214f634e502d`  
**Q/Alt/WL/Axes/Ctl:** O-buffer 16–128 KiB; GEMM 128×128×256; O capacity; fixed W/A, 16×16 WS, 256-bit.  
**Obj/Prod:** conservative report-local M-tiling formula lines 118–132; cycles/TOPS/utilization.  
**Owner:** Chapter 9 **C9.3/C9.8/C9.14/C9.19**; Chapter 6 whole-image requirement; Chapter 16 C16.25–C16.27 for DB claims.  
**Lim (verbatim report):** “Conservative assumption (A-reload per M-tile)” and optimistic no-reload would make the effect “3-4% … rather than 8-22%.” (line 135)

- **`obuf-threshold64`** — Quote, **§Key Findings 1, lines 53–68:** “O-buffer tiling threshold is exactly 64 KB”. Type `quant`; **qualified** as capacity arithmetic. Domain `local_formula_cycles`. Tags `Q=bytes,tile count`; `U=integrated tiling`. Missing: direct MMA requires whole images and does not stream. Alt: below/above 64 KiB. Safe: 128×128 FP32 output occupies 64 KiB; report tiling is hypothetical. Reverse: executable capacity-tiling path.
- **`obuf-step-function`** — Quote, **§Key Findings 2, lines 72–76:** “The throughput penalty is NOT gradual … 32 KB to 56 KB … 0.341 TOPS”. Type `quant`; **qualified** within conservative formula. Domain `local_formula_cycles`. Tags `Q=local TOPS`; `U=residency`. Missing: whether A must reload. Alt: capacities yielding equal tile count. Safe: local integer tile count creates plateaus. Reverse: partial residency or overlap.
- **`obuf-above64-zero`** — Quote, **§Key Findings 3, lines 78–82:** “Increasing O-buffer to 80, 96, or 128 KB changes nothing”. Type `quant`; **qualified** for fixture. Domain `local_formula_cycles`. Tags `Q=local cycles`; `U=other uses`. Missing: DB/multicontext/larger workloads. Alt: 64–128 KiB. Safe: no local single-GEMM reduction above fit. Reverse: larger output or additional use.
- **`obuf-fp32-doubles`** — Quote, **§Key Findings 4, line 89:** “FP16 … threshold would be 32 KB instead of 64 KB”. Type `quant`; **retained** as byte arithmetic. Domain `noncycle_functional_or_structure`. Tags `Q=capacity bytes`; `U=numerical acceptability`. Missing: actual FP16 accumulator/store path and accuracy. Alt: FP32 versus FP16 output storage. Safe: element width halves required bytes; no precision recommendation follows. Reverse: format/path change.
- **`obuf-min-nonnegotiable64`** — Quote, **§Actionable Conclusion, line 101:** “64 KB O-buffer is the minimum non-negotiable SRAM budget.” Type `presc`; **rejected**. Domain `local_formula_cycles`. Tags `Q=local throughput`; `D=budget`; `U=other workloads/cost`. Missing: direct path and alternative tiling. Alt: 16–128 KiB. Safe: 64 KiB is the no-tiling footprint for this fixture only. Reverse: DB/tiling/format.
- **`obuf-threshold-scales-mn`** — Quote, **line 107:** “M=256 at N=128 needs 128 KB … 256×256 … 256 KB”. Type `quant`; **retained** as byte formula. Domain `noncycle_functional_or_structure`. Tags `Q=capacity`; `U=execution`. Missing: practical tiling behavior. Alt: output sizes. Safe: FP32 output bytes scale as 4MN. Reverse: compressed/lower-width storage.
- **`obuf-db-and-fp16-recovery`** — Quote, **lines 109–111:** DB would “approximately halv[e]” tiling overhead; FP16 output is a “compiler optimization target”. Type `presc`; **rejected/blocked**, split here as two materially related alternatives but not composed. Domain `db_ideal_overlap_formula_cycles`. Tags `Q=hypothetical recovery`; `D=DB/FP16`; `U=correctness,accuracy,bridge`. Missing: valid DB and FP16 route. Alt: ping-pong, residency, FP16 store. Safe: both remain separate future hypotheses. Reverse: executable evidence.

**Flag:** line 101 says tiling overhead “increases linearly with tile count,” while lines 72–76 correctly describe a discrete step function; linear wording is unsafe.

---

### 21. `sram-wa-buffer-sizing.md` — **6 claims**

**Path/SHA:** `/home/zxy/Workplace/projects/tusim/docs/exploration/sram-wa-buffer-sizing.md` — `ff8de6c0ace93c6f0dd82c7b090238aa2038b5aa1982d3f72a1cfbd780027527`  
**Q/Alt/WL/Axes/Ctl:** W/A capacity separately and jointly; GEMM 128×128×256; W and A size; 16×16 WS depth2.  
**Obj/Prod:** report-local pass/tiling formula; cycles/TOPS/utilization/DMA share.  
**Owner:** Chapter 9 **C9.3/C9.8/C9.14/C9.19**; Chapter 6 whole-image-fit claim.  
**Lim:** “analytical cycle model, validated against cmodel at baseline” (line 18); baseline validation does not validate undersized tiling.

- **`wa-w-cliff64`** — Quote, **§Key Findings 1, lines 56–60:** “At 48 KB … throughput drops 8.4% … W-buffer should never be smaller than the W matrix.” Type `quant/presc`; arithmetic **qualified**, prescription **rejected**. Domain `local_formula_cycles`. Tags `Q=local throughput`; `D=W sizing`; `U=integrated tiling`. Missing: direct MMA does not internally tile undersized operands. Alt: 48/64/128 KiB. Safe: W footprint is 64 KiB; report’s undersized passes are hypothetical. Reverse: executable tiling.
- **`wa-a-eightfold-under1`** — Quote, **§Key Findings 2, lines 62–70:** “64 KB to 8 KB … only costs 224 cycles — a 1.0% throughput penalty.” Type `quant`; **qualified** as local formula. Domain `local_formula_cycles`. Tags `Q=cycles,TOPS`; `U=actual K-tiling`. Missing: executable capacity path. Alt: A sizes. Safe: local pass formula is insensitive to A reduction. Reverse: real refill/reload producer.
- **`wa-combined-multiplicative`** — Quote, **§Key Findings 3, lines 72–79:** “32/32 … 8.5%; 16/16 … 22.2%; 8/8 … 40.7%”. Type `quant`; **qualified**. Domain `local_formula_cycles`. Tags `Q=local penalties`; `U=integrated pass product`. Missing: common executable producer. Alt: joint sizes. Safe: report formula compounds M×K pass counts. Reverse: reuse/overlap.
- **`wa-balanced64plus8`** — Quote, **§Key Findings 4, line 89:** “64 KB W + 8 KB A — saving 120 KB of SRAM (47% of total) with <1% throughput loss.” Type `presc`; **blocked**. Domain `local_formula_cycles`. Tags `Q=capacity/local loss`; `D=allocation`; `U=actual path,area`. Missing: denominator includes what total, and direct MMA fit requirement. Alt: defaults versus asymmetric split. Safe: candidate allocation for an analytical tiling design only. Reverse: executable capacity test.
- **`wa-no-symmetric-allocation`** — Quote, **§Actionable Conclusions, line 97:** “Don't allocate SRAM symmetrically.” Type `presc`; **qualified** as a design question, not rule. Domain `local_formula_cycles`. Tags `D=allocation`; `U=workload distribution,area/power`. Missing: fixed total-budget optimization. Alt: symmetric/asymmetric W/A/O. Safe: sensitivities can differ; optimize under explicit workloads and costs. Reverse: different workload mix.
- **`wa-test-larger-workloads`** — Quote, **line 99:** “Test with larger workloads … threshold shifts.” Type `presc`; **retained** as an open/reversal condition. Domain `noncycle_functional_or_structure`. Tags `D=evidence requirement`; `U=scaling`. Missing: larger sweep. Alt: retain local rule versus reopen. Safe: all sizing conclusions remain local until scaled. Reverse: exactly the requested larger-workload evidence.

---

## Duplicate and contradiction register

### Cross-report duplicate families

1. **DMA/compute knee and PE sweet spot:** `bus-*`, `dfpe-compute-dma-knee`, `pe-*`, `wlpe-*`, `mac-*`. These reuse the same serialized local balance pattern, not independent executable confirmation.
2. **“Dataflow negligible” family:** `dfcomp-negligible-k256`, `dfpe-subpoint1-gap`, and the conclusion of `dataflow-pe-interaction`.
3. **Pipeline depth/dataflow ranking:** `pddf-*`, `pdsweep-*`, `pdwl-*`, `rspd-*`; several repeat conclusions using mutually incompatible formulas.
4. **O-buffer capacity/DB family:** `obuf-*`, `dbmt-*`, `dbpe-*`; capacity arithmetic, ideal overlap, and executable controller evidence must remain separate.
5. **Compiler prescriptions:** aspect padding, dataflow selection, runtime depth, PE-target selection, DB scheduling, and FP16 storage all lack a demonstrated compiler/runtime composition bridge.

### Material arithmetic or semantic contradictions

- **Aspect ratio:** global nonzero-remainder bound contradicts its own remainder-4 row; two report sections use different fill/drain formulas.
- **Dataflow:** one report says WS/OS are nearly identical, another says OS is 20% faster, and pipeline reports claim up to 38–73%; Chapter 21/7 establish distinct formula producers and ineffective labeled routes.
- **K sweep:** the O-buffer is incorrectly blamed for a nonzero asymptotic DMA floor even though its own later derivation shows the fixed O share tends to zero.
- **Pipeline-depth sweep:** calls report-local spatial accounting “hardware-accurate” and source per-K accounting a bug without a validated normative timing contract.
- **DMA channels:** O-store is described both as unable to overlap and as entirely fitting in compute; service estimates are not elapsed time.
- **Double buffer:** generalized threshold and area/savings claims fail current Chapter 16 recomputation or omit physical ping-pong allocation.
- **DRAM:** multiple 8 GHz TOPS rows and the 1 GHz “identical” conclusion contradict the printed formula and constants.
- **GBUF:** speedup table contradicts raw-cycle ratios at K=128 and K=8192.
- **O-buffer:** “linear” degradation conflicts with the report’s own discrete step-function conclusion.
- **Workload/PE “optimality”:** utilization, absolute TOPS, and TOPS/MAC choose different winners; no single objective exists.

## Totals

| Report | Claims |
|---|---:|
| aspect-ratio-alignment-sweep.md | 6 |
| bus-width-sweep-gemm128.md | 5 |
| dataflow-comparison-gemm128.md | 4 |
| dataflow-pe-interaction.md | 5 |
| dataflow-rs-comparison-gemm128.md | 4 |
| k-sweep-dma-crossover.md | 6 |
| mac-density-dma-bound.md | 5 |
| pe-array-sweep-gemm128.md | 3 |
| pipeline-depth-dataflow-interaction.md | 5 |
| pipeline-depth-sweep-gemm128.md | 5 |
| pipeline-depth-workload-interaction.md | 5 |
| rs-pipeline-depth-sweep.md | 5 |
| workload-scaling-pe-optimal.md | 5 |
| db-pe-size-goldilocks.md | 6 |
| dma-channel-queue-sweep.md | 7 |
| double-buffer-mtiling-recovery.md | 7 |
| dram-type-clock-sweep.md | 6 |
| gbuf-sizing-sweep.md | 4 |
| sram-arbitration-sweep.md | 4 |
| sram-obuffer-tiling-threshold.md | 7 |
| sram-wa-buffer-sizing.md | 6 |
| **Total** | **110** |

**Zero-claim reports:** none.

## Completion summary

- Extracted **110** split high-salience claims from all **21/21** requested reports.
- Assigned each claim a stable suffix, exact report hash/path, verbatim anchor, disposition, owner/reference, one metric domain, objective tags, alternatives, limitation, safe replacement, and reversal condition.
- Flagged duplicate families and the principal arithmetic/semantic contradictions.
- Independently recomputed the GBUF and DRAM contradictions from the reports’ printed constants.
- **Files created or modified:** none.
- **Repository state after review:** Tusim remained detached/clean; Tusim Book remained clean on `main`.
- **Issues:** several reports have no claim-specific current-book owner; those are explicitly tied to the nearest chapter ledger or Chapter 22 framing requirement rather than inventing an owner.