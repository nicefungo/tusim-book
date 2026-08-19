# Chapter 22 claim extraction — sharing/topology and runtime/static policy

## Scope and method

- **Source:** detached, clean Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25`.
- **Book:** clean `main` at `88cba9bf9a26b2ae2c3079e6c57446803ab76df0`.
- **Files modified/created:** none.
- **Network:** not used.
- **Disposition vocabulary:** `retained`, `qualified`, `superseded`, `rejected`, `blocked`.
- **Objective tags:** `quantified`, `directional`, `unknown`.
- **Metric domains are deliberately noncomposable.** Every claim below has exactly one.
- **Canonical owners:** Chapter 12 owns multicore/interconnect semantics; Chapter 18 owns runtime context retention; Chapter 19 owns static scheduling; Chapter 22 owns portfolio disposition and bounded preference rules.

### Reusable verbatim limitations

These exact current-book limitations are referenced from individual rows:

- **VL-BCAST — C12.19:** “no multicast tree; non-transactional partial effects can precede a later failure”
- **VL-TRAFFIC — C12.14:** “deterministic heuristic score, not a queue schedule or proved makespan bound”
- **VL-TRANSFER — C12.7:** “deterministic estimated cycles, no queues or calibration”
- **VL-HIST — C12.31:** “retain architecture questions; do not import speedup recommendations”
- **VL-ROUTE — C12.18:** “traffic-specific, not universal”
- **VL-CONTEXT — C18.39:** “Sweep cycles are deterministic model ledger values, not wall-clock memcpy measurements or calibrated preemption latency. They omit context-store allocation/area, queueing, reload, DRAM contention, setup, ECC, dirty scans, and synchronization latency.”
- **VL-CONTROL — C18.21:** “Its smallest model row is not proof of lowest latency or energy.”
- **VL-LIVE — C18.20:** “Isolation is valid only for the retained prefixes plus an external safe-point/reload contract”
- **VL-SCHED — C19.15:** “It is independent of overlap and is not a DAG critical-path result despite the historical scheduler-sweep explanation.”
- **VL-SWEEP — C19.56:** “The scheduler sweep is a report, not a fail-closed test gate”

---

## 1. `broadcast-dma-multicore-scaling.md`

- **SHA-256:** `ef201048b687c5ccb11d0bb808bcb98e633e1da95c6999ae8df4f5884b768fcd`
- **Question:** effect of “broadcast DMA” on multicore GEMM scaling and A-buffer redundancy.
- **Alternatives:** per-core A load versus hypothetical one-load fanout; 16×16 versus 32×32 PE; M-split versus K-split.
- **Workload/axes:** GEMM 128³/256³/512³/1024³; 1–32 cores; two PE sizes; broadcast on/off.
- **Controls:** WS, pipeline depth 2, 256-bit bus, FP16 W/A, 1 GHz; analytical formulas only.
- **Objective:** minimize report-local parallel cycles / maximize speedup and efficiency.
- **Producer/formula/units:** report-prose analytical formula, lines 31–39; cycles, speedup, efficiency %. No executable multicast producer.
- **Metric domain for every claim:** `traffic_heuristic_cycles`.
- **Current owner:** Chapter 12, especially C12.13, C12.19, C12.26, C12.31; Chapter 10 separately owns descriptor multicast semantics.

| ID | Exact heading/line and report quote | Likely disposition / exact owner | Objectives; missing decisive dimensions; alternatives | Safe replacement; verbatim limitation; reversal |
|---|---|---|---|---|
| B1 | **H68/L70–74:** “Broadcast DMA is a hard requirement for multicore at small workloads… 32 cores is slower than 1 core… With broadcast DMA… 14.71× speedup.” | **rejected** for current Tusim; D22F09, C12.19/C12.31 | latency/speedup **quantified**; physical multicast, shared fabric, queues, fanout bandwidth, area/energy **unknown**; sequential sends vs a real multicast tree | Current broadcast cannot support this requirement claim; retain it as a future multicast hypothesis. **VL-BCAST.** Reopen after one executable one-to-many transfer with common elapsed-time accounting. |
| B2 | **H76/L80–83:** “Speedup ratio… 2.87×…1.25×…1.03×…1.00×”; “DMA is <0.5%…39%…3%.” | **qualified** as report-local arithmetic, not current broadcast evidence; C12.26/C12.31 | modeled cycle fractions **quantified**; multicast service, contention, placement **unknown**; replicated loads vs ideal fanout | The local formula predicts diminishing fanout benefit as compute dominates; it does not model Tusim broadcast execution. **VL-HIST.** Reverse if an executable fabric shows fanout or contention scaling differently. |
| B3 | **H85/L87–91:** “16×16…10.34× → 29.66×”; “32×32…0.99× → 14.71×”; larger arrays amplify benefit. | **qualified** only as one hypothetical formula family; C12.31 | speedup **quantified**; PE-area, frequency, supply contention, multicast cost **unknown** | In this formula, faster compute exposes the assumed replicated-load term; no physical large-PE preference follows. **VL-HIST.** Reverse when compute, memory, and fanout share an executable clock/resource model. |
| B4 | **H93/L95:** “Without broadcast… favors K-tiling… With broadcast… M-tiling… becomes viable again.” | **qualified** future hypothesis; no compiler bridge; C12.19/C12.31, Chapter 19 boundary | partition-cycle effect **directional**; reduction cost, legal dependencies, memory capacity, compiler consumer **unknown**; M-, K-, N-/2-D splits | Evaluate M-split and K-split under explicit replicated input and output-reduction equations; do not infer compiler behavior. **VL-BCAST.** Reverse if reduction or capacity cost dominates avoided copies. |
| B5 | **H97/L99:** “Without broadcast DMA, multicore (>4 cores) is only useful for GEMM sizes ≥512×512.” | **rejected** as universal threshold; C12.31 | useful-core threshold **quantified** locally; partition, bus sharing, topology, utilization objective **missing** | At most, the report-local constants produce a crossover between selected 128³–512³ rows. **VL-HIST.** Any alternate bus width, partition, PE geometry, or executable fanout may move/reverse it. |
| B6 | **H97/L99:** “Broadcast DMA expands the multicore-viable workload range by ~64× in FLOPs.” | **rejected** as architecture evidence; bounded endpoint arithmetic is 512³/128³ = 64 | FLOP-range ratio **quantified**; definition of “viable,” execution path, common producer **missing** | The two chosen cubic workloads differ by 64× under the report’s FLOP convention; this is not an observed viable-range expansion. **VL-HIST.** Reopen with a declared viability objective and executable sweep. |
| B7 | **H101/L103:** “Broadcast DMA is not optional for multicore NPUs.” | **rejected**; D22F09/C12.19 | architecture prescription **directional**; cost, workloads, alternatives, multicast implementation **unknown** | Tusim evidence justifies testing a real multicast alternative where repeated input copies bind; it does not make multicast mandatory. **VL-BCAST.** Reverse/open if private memories, partitioning, locality, or compute intensity avoid replication. |
| B8 | **H101/L105:** “32×32 PE + 32 cores is 32× faster per core than 16×16 PE… Without it… slower… (71,284 vs 1,055,744 cycles).” | **rejected; arithmetic contradiction** | cycles **quantified**; area/frequency **unknown**; 16×16 vs 32×32 | `71,284 < 1,055,744`: the cited 32×32 configuration is about **14.81× faster**, not slower; PE count is 4×, not 32×. No safe architecture preference survives. **VL-HIST.** Requires corrected formulas/table and independent recomputation. |
| B9 | **H101/L107:** “The compiler should… prefer M-split… broadcast DMA makes M-split strictly better for most sizes.” | **rejected**; no compiler/runtime bridge; C12.31 and Chapter 19 C19.40 | compiler decision **directional**; legality, capacities, reduction, executable lowering **unknown**; M-/K-/N-/2-D partition | Treat M-split plus physical multicast as one candidate, not a compiler rule or strict dominance result. **VL-BCAST.** Reverse when output reduction, capacity, or route concentration dominates. |
| B10 | **H101/L109:** “a single DMA descriptor with `TU_DMA_XFER_MULTICAST` + `count = n_cores` delivers… in one transfer.” | **rejected** as a description of cluster broadcast; Chapter 10 C10.6/C10.7 versus Chapter 12 C12.19 | functional fanout **directional**; cross-core target type, routing, common fabric timing **missing**; descriptor-local multicast vs cluster sequential send | Descriptor multicast and cluster broadcast are separate APIs. Cluster broadcast performs N−1 immediate sends; descriptor fanout does not establish a NoC multicast route. **VL-BCAST.** Reopen only with an explicit descriptor-to-cluster consumer bridge. |

---

## 2. `interconnect-contention-traffic-matrix.md`

- **SHA-256:** `6e20ca4908446609dbcc265d15c702e3bfa441a812022e24fede2f36b34e629c`
- **Question:** effect of simultaneous shared-link loading and whether topology preference reverses with traffic.
- **Alternatives:** `ideal_parallel` vs `shared_link`; ring vs 2×4/4×4 mesh.
- **Workload/axes:** neighbor, hotspot-to-0, all-to-all; 8/16 cores; 4 KiB simultaneous messages.
- **Controls:** cut-through, 16 B/cycle, 5 cycles/hop, shortest ring routes, mesh XY, directional links.
- **Producer/formula/units:** linked `tu_cluster_estimate_traffic_cycles()`; `max(max_isolated, max_link_serialization + max_route_latency)`; cycles and ratios.
- **Metric domain:** `traffic_heuristic_cycles`.
- **Current owner:** Chapter 12 C12.14–C12.18, C12.32, C12.43; manuscript §§12.7–12.9.

| ID | Exact heading/line and quote | Disposition / evidence | Objectives; missing dimensions; alternatives | Safe replacement; limitation; reversal |
|---|---|---|---|---|
| C1 | **H61/L63:** “No universal topology winner… mesh lowers… all-to-all…55.4%… but…48.6% slower for hotspot…” | **qualified**; C12.32 and manuscript lines 50–60 | heuristic score **quantified**; queues, arbitration, wire/port cost **unknown**; ring vs mesh plus placement | Current linked heuristic reverses by traffic: mesh 4,126 vs ring 9,256 all-to-all; ring 2,088 vs mesh 3,102 hotspot. **VL-TRAFFIC.** Queue policy, alternate roots/routes, or physical costs may reverse it. |
| C2 | **H61/L64:** “Both topologies remain at the ideal bound… ring is 8.7% lower… placement… causes the difference.” | **qualified**; C12.32, manuscript line 474 | heuristic latency **quantified**; representative locality/mappings **missing**; ring vs mesh placement | For this endpoint sequence, wrap `15→0` is one ring hop and six mesh hops; this is mapping plus topology, not intrinsic local-traffic superiority. **VL-TRAFFIC.** Reverses under a mesh-local neighbor mapping. |
| C3 | **H61/L65:** “31.27×… ring all-to-all and 14.43×… mesh.” | **qualified**; exact executable rows, but lower-bound label corrected by C12.43 | ideal/shared ratio **quantified**; legal service order and injection timing **unknown** | The implemented heuristic differs from ideal-parallel by 31.27×/14.43× for the named rows; these are not measured slowdown or proved bounds. **VL-TRAFFIC.** Recompute under queued injection/arbitration. |
| C4 | **H61/L66–71:** sustained throughput, area, energy, router-buffer traffic are unquantified; endpoint bytes/accuracy unchanged. | **qualified** open decision | latency heuristic **quantified**; throughput/area/energy/buffering **unknown**; narrower/wider ring, mesh, alternate collective | Keep ring and mesh materially live because decisive physical objectives are absent. **VL-TRAFFIC.** Close only with injection traces, finite queues, area/link and energy evidence. |
| C5 | **H61/L73:** “Placement and collective selection must be traffic-aware… should not infer that MESH always wins…” | **qualified** bounded prescription; no compiler composition | placement effect **directional**; executable placement/collective lowering **unknown**; alternate roots, trees, route spreading | A compiler study should test traffic-aware placement as a hypothesis; no current compiler/runtime path is established. **VL-TRAFFIC.** Reverse if physical routing or collective implementation removes the observed concentration. |

---

## 3. `interconnect-mesh-routing-order.md`

- **SHA-256:** `fdf869c066d27c77f005d42cc6680ff90e7d9ca4597cadc8b68cac100c585ae6`
- **Question:** effect of deterministic XY vs YX order under asymmetric placement.
- **Alternatives:** fixed XY, fixed YX; adaptive routing explicitly excluded.
- **Workload/axes:** 3×3/4×4; two transposed fan-ins and all-to-all.
- **Controls:** 4 KiB simultaneous messages, cut-through, shared-link heuristic, 16 B/cycle, 5 cycles/hop.
- **Producer/formula/units:** linked traffic estimator; cycles/link serialization.
- **Metric domain:** `traffic_heuristic_cycles`.
- **Current owner:** C12.15, C12.18, C12.32; manuscript route discriminator.

| ID | Exact heading/line and quote | Disposition / evidence | Objectives; missing dimensions; alternatives | Safe replacement; limitation; reversal |
|---|---|---|---|---|
| R1 | **H57/L59:** “YX lowers… by 65.8% (798 vs 2,334)… transposed… XY provides the identical 65.8% reduction.” | **qualified**; C12.18 confirms reversal, though canonical probe uses a different 606/222 fixture | heuristic score **quantified**; queues/physical orientation **unknown**; XY vs YX | Deterministic order can reverse the hotspot under transposed endpoint placement. **VL-ROUTE + VL-TRAFFIC.** Reverse with different endpoints, route adaptivity, or arbitration. |
| R2 | **H57/L59:** “On symmetric all-to-all, both are identical.” | **qualified** for the named 3×3/4×4 matrices | heuristic equality **quantified**; other symmetric workloads/tie rules **missing** | XY and YX both report 1,556 on 3×3 and 4,126 on 4×4 for these all-to-all rows only. **VL-TRAFFIC.** A different tie policy or non-square/irregular mesh can break equality. |
| R3 | **H57/L60:** “No universal route winner… axis order must follow placement and traffic orientation.” | **qualified**; C12.18/C12.32 | placement/routing preference **directional**; runtime route cost and deadlock proof **unknown** | Preserve both fixed orders as traffic-specific hypotheses; do not select one globally. **VL-ROUTE.** Close only after representative traces and physical route/deadlock constraints. |
| R4 | **H57/L67:** compiler can transpose patterns, select route mode, or choose roots. | **qualified** future hypothesis; no executable compiler bridge | software policy **directional**; transform legality, route-mode consumer, queue behavior **unknown** | Test placement/orientation co-design in a bounded compiler-to-estimator experiment; no transformed-runtime benefit is established. **VL-TRAFFIC.** Reverse if hardware hard-wires one order or placement legality prevents transposition. |

---

## 4. `interconnect-switching-modes.md`

- **SHA-256:** `c2a28844527aca8c6afed9111da810e54a6825f82f1362b2b1369f8507dd529b`
- **Question:** when cut-through justifies complexity relative to store-and-forward.
- **Alternatives:** legacy hop-only, cut-through, store-and-forward.
- **Workload/axes:** 64 B/1 KiB/64 KiB; 1/3/7 hops; width 8/16/32 B/cycle.
- **Controls:** 5 cycles/hop; isolated, contention-free messages.
- **Producer/formula/units:** standalone analytical sweep plus linked functional/config tests; cycles and SF/CT ratio.
- **Metric domain:** `traffic_heuristic_cycles`.
- **Current owner:** C12.7, C12.26, C12.34; manuscript §12.5.

| ID | Exact heading/line and quote | Disposition / evidence | Objectives; missing dimensions; alternatives | Safe replacement; limitation; reversal |
|---|---|---|---|---|
| S1 | **H52/L54:** “One-hop traffic is identical in this model.” | **retained**; follows exact equations, C12.7 | isolated estimate **quantified**; physical startup/pipeline details **unknown** | For `h=1`, both equations equal `L+ceil(B/W)`. **VL-TRANSFER.** Different packetization/router pipelines can distinguish them physically. |
| S2 | **H52/L54:** “at 3 hops…29.6% for 64 B and 66.6% for 64 KiB; at 7 hops and 64 KiB…6.95× lower.” | **retained** as isolated-formula arithmetic | isolated cycles **quantified**; contention and implementation cost **unknown** | These percentages are valid outputs of the named equations, not collective throughput. **VL-TRANSFER.** Recompute if serialization cannot pipeline across hops. |
| S3 | **H52/L55:** “Doubling 8→16→32 B/cycle nearly halves both modes… ratio remains near hop count.” | **retained** within serialization-dominated formula | isolated cycles **quantified**; width area/power/frequency **unknown** | Wider links lower the serialization term; they do not erase the formula-level switching difference. **VL-TRANSFER.** Physical frequency loss or buffering cost may reverse width preference. |
| S4 | **H52/L56–60:** cut-through versus packet buffers/VC/credits; store-forward versus packet-size buffering; costs unquantified. | **qualified** open architecture trade-off | latency **quantified**; area/power/control **directional/unknown**; three modes | Retain both physical modes and the legacy compatibility abstraction; no local dominance result exists without implementation cost. **VL-TRANSFER.** Close with router synthesis, queue and energy evidence. |
| S5 | **H52/L61; H79/L81:** software must not treat legacy as physical; “RING and MESH remain runtime alternatives without a universal winner.” | **qualified** | software guidance **directional**; compiler bridge and traffic queues **unknown** | Use the isolated equations only for named point-to-point hypotheses; topology preference requires traffic-specific evidence. **VL-TRANSFER.** Reversal depends on real traffic and finite service. |

---

## 5. `interconnect-topology-sweep.md`

- **SHA-256:** `60754c76d3655835e52869d5da05305a5c8a8dfb185cb0bc4eed396222310315`
- **Question:** ring vs mesh all-reduce latency and crossover.
- **Alternatives:** ring vs best-factor mesh.
- **Workload/axes:** 2–32 cores; 1–256 KiB payloads.
- **Controls:** 5 cycles/hop, 64 GB/s, 1 GHz; report-local store-and-forward-like hop multiplication.
- **Producer/formula/units:** standalone C/report formula; `hops × (latency + payload/BW)`; cycles/speedup.
- **Metric domain:** `traffic_heuristic_cycles`.
- **Current owner:** C12.26, C12.31, C12.32, C12.42; fidelity correction in report lines 7–16.

| ID | Exact heading/line and quote | Disposition / evidence | Objectives; missing dimensions; alternatives | Safe replacement; limitation; reversal |
|---|---|---|---|---|
| T1 | **H75/L79–85:** mesh speedups 1.00/1.50/1.75/2.50/3.10×, invariant to payload. | **superseded** as topology evidence; D22F10/C12.31–32 | local formula speedup **quantified**; routing, contention, collective algorithm **missing** | Retain as hop-formula arithmetic only; current linked evidence reverses by traffic. **VL-HIST.** Recompute with explicit traffic and routing. |
| T2 | **H97/L99:** “MESH topology provides 1.5–3.1× all-reduce speedup… advantage growing as O(N)/O(√N).” | **superseded** | analytical latency **quantified**; actual all-reduce transport absent | The historical formula gives smaller hop totals for selected meshes; it does not model Tusim all-reduce or a routed collective. **VL-HIST.** A real collective/queue model decides the ranking. |
| T3 | **H97/L101–105:** per-core recommendations, culminating in “16 cores… strong requirement” and 254K vs 82K cycles. | **rejected** as hardware prescription | cycles **quantified**; wiring, queueing, algorithm, power **unknown** | Do not select topology by these rows. Preserve ring/mesh as traffic-specific alternatives. **VL-HIST.** Reverse/open under hotspot traffic, physical cost, or alternate collectives. |
| T4 | **H33/L38:** “4… hop count = RING (both 4 hops per step).” | **rejected; internal arithmetic contradiction** | hops **quantified** | The same report’s tables give ring `6` and mesh `4`; its source recommendation also calls 2×2 “identical.” Correct the formula/wording before reuse. **VL-HIST.** |
| T5 | **H117/L121–123:** “≤4 cores: Use RING”; “8 cores: Consider MESH”; “16+ cores: Use MESH.” | **rejected** | topology prescription **directional**; physical complexity unquantified | No core-count-only rule survives current traffic evidence. **VL-HIST.** Reversal occurs with traffic matrix and placement. |
| T6 | **H117/L125:** “crossover at 8 cores holds for ICC bandwidths ≥32 GB/s. Below… topology differences are masked…” | **rejected; formula contradiction** | bandwidth threshold **quantified** | Under the displayed formula both topology totals multiply the same `L+B/W`, so their ratio is bandwidth-independent. No 32 GB/s crossover follows. **VL-HIST.** Requires a different, explicit bandwidth-contention model. |
| T7 | **H127/L129:** mesh would reduce barrier overhead 50–68%. | **superseded/rejected for cluster barrier**; C12.42 | barrier cycles **quantified** locally; executable barrier topology dependence absent | `tu_cluster_barrier()` adds topology-independent `2×hop_latency`; do not transfer hop-table reductions to it. **VL-HIST.** Reopen with a routed rendezvous implementation. |
| T8 | **Fidelity correction L14–16:** “MESH is 55.4% lower… all-to-all, while RING is 32.7% lower for hotspot fan-in.” | **qualified** correction; C12.32 | heuristic score **quantified**; queue-accurate decision **unknown** | Current linked rows establish a traffic-shape reversal, not a final topology winner. The 32.7% figure expresses ring reduction relative to mesh; the contention report’s 48.6% expresses mesh excess relative to ring—different denominators, not a contradiction. **VL-TRAFFIC.** |

---

## 6. `multicore-scaling-gemm256.md`

- **SHA-256:** `7bdf0ddac330db3734df92824106c21976f3e95d192972bb0c8aeb49fcef4682`
- **Question:** where analytical multicore scaling saturates for 256³ GEMM.
- **Alternatives:** 1–32 cores with replicated A; hypothetical broadcast alternative.
- **Workload/axes:** fixed 256³, 16×16 PE, WS, FP16/FP32, ring.
- **Controls:** 1 GHz; measured single-core baseline then local compute/DMA/barrier formula.
- **Producer/formula/units:** `tests/test_multicore_scaling_sweep.c` linked single-core measurement plus hand-authored parallel formula; cycles, TOPS, speedup, efficiency.
- **Metric domain:** `traffic_heuristic_cycles`.
- **Current owner:** C12.26/C12.31; source producer separately identified by Chapter 21.

| ID | Exact heading/line and quote | Disposition / evidence | Objectives; missing dimensions; alternatives | Safe replacement; limitation; reversal |
|---|---|---|---|---|
| M1 | **H63/L65:** “Scaling peaks at 2.73× with 8 cores, then degrades.” | **qualified** report-local result | modeled speedup **quantified**; concurrent execution/shared bus absent | The local formula peaks at 8 cores for this fixed fixture; it is not a multicore run. **VL-HIST.** Core count, bus, partition, or workload changes move the peak. |
| M2 | **H63/L65:** redundant A loads dominate; ~8,192 DMA cycles/additional core. | **qualified** formula attribution | DMA term **quantified**; actual shared DMA service/fanout absent | The formula’s replicated A term eventually exceeds modeled compute savings. **VL-HIST.** Reverse with locality, partitioning, overlap, or physical multicast. |
| M3 | **H63/L67–74:** broadcast predictions: 4/8/16/32 cores = 99,508/53,518/30,523/19,026 cycles and 82.3/76.5/67.1/53.8%. | **qualified** as hypothetical arithmetic, not current broadcast behavior | cycles/efficiency **quantified**; fanout timing **unknown** | Retain as an ideal no-redundant-A sensitivity study only. **VL-BCAST.** Reopen after executable multicast. |
| M4 | **H80/L82:** “4 cores is the sweet spot — 2.62× speedup at 65.5% efficiency.” | **rejected/ambiguous objective** | speedup and efficiency **quantified**; “sweet spot” objective missing | The table’s maximum speedup/TOPS is at 8 cores, while efficiency declines monotonically. Four cores is not selected by a stated scalar or partial-order objective. **VL-HIST.** Define the efficiency/performance/cost objective first. |
| M5 | **H80/L83:** “broadcast DMA is an architectural requirement for >4 cores.” | **rejected**; duplicate of B1/D22F09 | prescription **directional**; real multicast absent | Repeated input movement is a candidate bottleneck in this formula; current Tusim does not establish broadcast as mandatory. **VL-BCAST.** |
| M6 | **H80/L84–85:** “Barrier overhead is negligible (<1%)”; “Larger GEMMs would scale better.” | **qualified** only for the local barrier/formula; not executable cluster-wide scaling | cycle share **quantified**; topology-independent executable barrier and workload implementation **missing** | The report-local ring term is below 1% in the named fixture; increasing useful compute relative to fixed movement is a hypothesis, not measured scaling. **VL-HIST.** Reverse with collective/barrier service, memory capacity, or reduced utilization. |

### Cross-report contradiction

For nominally the same **256³, 16×16, one-core** setting:

- `multicore-scaling-gemm256.md` reports **327,680 cycles**.
- The broadcast report’s 32-core rows and printed speedups imply a one-core baseline of roughly **16.8 million cycles** (`664,684×25.28` and `529,772×31.72`).

That is about a **51× baseline mismatch**. The broadcast report nevertheless says it “confirms” the earlier sweep and uses the same validated baseline. Until producer/formula provenance explains this difference, no cross-report speedup or threshold should be combined.

---

## 7. `context-switch-state-scope.md`

- **SHA-256:** `ae8b49e3b31e0172f69869d406c70996609f295f584357107847186259c80230`
- **Question:** transparent preemption versus retained-state traffic/hardware state.
- **Alternatives:** `FULL_SRAM`, `LIVE_SRAM`, `CONTROL_ONLY`; priority and round-robin remain separate scheduling choices.
- **Workload/axes:** 128/256/512 KiB total SRAM; FULL/LIVE25/CONTROL; 16/32/64 B/cycle sensitivity.
- **Controls:** 100 fixed cycles; W/A/O 50/25/25%; live prefix 25%.
- **Producer/formula/units:** real context manager and sweep; `fixed + ceil((outgoing+incoming bytes)/state_bytes_per_cycle)`; retained bytes and manager-ledger cycles.
- **Metric domain:** `context_ledger_cycles`.
- **Current owner:** Chapter 18 C18.1, C18.17–C18.21, C18.38–C18.40; manuscript §§18.1 and retention alternatives.

| ID | Exact heading/line and quote | Disposition / evidence | Objectives; missing dimensions; alternatives | Safe replacement; limitation; reversal |
|---|---|---|---|---|
| X1 | **H6/L8–14:** “Three materially different designs… No mode is universally preferable.” | **qualified**; D22F15/C18.1 | continuation/isolation **directional**; full-machine retained set and legal boundary partly absent; FULL/LIVE/CONTROL | Preserve all three as alternatives at a caller-established legal boundary, not fidelity levels. **VL-CONTEXT.** Choice reverses with required continuation state and reload contract. |
| X2 | **H16/L28–38:** 128/256/512 KiB rows, including 256 KiB FULL `16,484`, LIVE `4,196`, CONTROL `100`. | **retained** as exact ledger arithmetic; C18.38 | retained bytes/cycles **quantified**; end-to-end handoff **unknown** | Exact source-equation rows are valid manager-ledger results. **VL-CONTEXT.** They do not rank complete preemption latency. |
| X3 | **H16/L40–46:** at 256 KiB FULL, 16/32/64 B/cycle gives 32,868/16,484/8,292 cycles. | **qualified** | ledger transfer term **quantified**; datapath area/power/frequency **unknown** | Wider modeled state bandwidth lowers only the analytical transfer term. **VL-CONTEXT.** Physical cost or queue contention may reverse a width preference. |
| X4 | **H50/L54–62:** FULL strongest transparent behavior/largest interruption; LIVE lower traffic with safe-state obligation; CONTROL lowest modeled interruption but omitted reload. | **qualified**; C18.40 | ledger traffic **quantified**; area/energy **directional**, end-to-end continuation **unknown** | FULL/LIVE/CONTROL shift retained bytes and software obligations; they cannot be globally ranked. **VL-CONTEXT.** |
| X5 | **H50/L58:** “2× full SRAM per switch”; “2× declared live bytes”; CONTROL no context traffic but reload unmodeled. | **qualified**; C18.17–21 | context-store bytes **quantified**; reconstruction traffic **unknown** | Two-way retained traffic belongs to the manager ledger; CONTROL moves—not removes—the continuation obligation. **VL-CONTROL.** Reverse if reload exceeds retained-state transfer. |
| X6 | **H50/L64:** “its 100-cycle row must not be presented as end-to-end superiority.” | **qualified and canonical**; C18.21 | fixed ledger **quantified**; reload/dependency/contention **unknown** | CONTROL’s 100 cycles are fixed-only manager accounting, not end-to-end resume latency or energy. **VL-CONTROL.** |
| X7 | **H75/L77:** obtain compiler traces before adding dirty bitmap/scatter-gather support. | **blocked/open**; no compiler-to-live-prefix bridge, C18.19/C18.40 and Chapter 19 boundary | mechanism prescription **directional**; workload live-set distribution **unknown**; prefixes, dirty bitmap, scatter/gather, full save | Keep richer retained-set encoding open until representative live-state traces and a legal producer contract exist. **VL-LIVE.** Reopen when compiler/runtime traces expose non-prefix live sets and quantify scan/metadata cost. |

---

## 8. `scheduler-policy-sweep.md`

- **SHA-256:** `5709e70e2b0100c30b164503413b002b6e58b1631597d47880d449cbbc0e3baa`
- **Question:** whether ASAP/ALAP/BALANCED change the scheduler’s printed quality metrics.
- **Alternatives:** ASAP, ALAP, BALANCED.
- **Workload/axes:** five synthetic topologies; policy varied.
- **Controls:** default config, DMA hoisting/barrier insertion/pipeline flags enabled.
- **Producer/formula/units:** linked `tests/test_scheduler_sweep.c`; reported cycles/counts/length. Current source shows a **serial emission sum**, not a DAG critical path.
- **Metric domain:** `scheduler_serial_dag_estimate` — retained canonical registry name; semantically, current Chapter 19 corrects it to a serial source-local estimate.
- **Current owner:** Chapter 19 C19.12–C19.15, C19.51, C19.56; manuscript §19.5; `source-audit.md#44`.

| ID | Exact heading/line and quote | Disposition / evidence | Objectives; missing dimensions; alternatives | Safe replacement; limitation; reversal |
|---|---|---|---|---|
| P1 | **H49/L51:** “All three… identical `estimated_cycles`, with zero barriers and zero DMA hoisted across all workloads.” | **retained** as a negative result for printed rows; D22F16/C19.13 | serial estimate/counts **quantified**; exact emitted order and transformed behavior **missing** | The shipped rows are identical for this policy-insensitive serial metric; policies can still reorder output. **VL-SWEEP + VL-SCHED.** Reverse with an order-sensitive objective/probe. |
| P2 | **H49/L53:** “Cycle estimation is DAG-bound… derived from the critical path…” | **rejected; producer contradiction**; C19.15 | cycles **quantified**; actual schedule time absent | Current source sums 1 cycle per DMA-class node and 4 per other emitted node. It is **not** a DAG critical path. **VL-SCHED.** Reopen only after a source change and new producer audit. |
| P3 | **H49/L55:** “DMA hoisting requires explicit barriers… Without explicit barriers… nothing to hoist past.” | **rejected as transformation explanation**; C19.12/C19.51 | candidate counts **quantified**; actual movement/emitted barrier **absent** | `tu_sched_hoist_dma()` and barrier insertion count narrow candidates but do not move nodes or emit barriers; full scheduling resets counts. **VL-SWEEP.** Reverse after a probe shows changed output order/instructions. |
| P4 | **H49/L57:** scheduler needs a schedule-order cycle model; hoisting is “a compiler… concern.” | **qualified** future hypothesis; no compiler/runtime composition | model improvement **directional**; semantic legality, executable consumer, overlap clock **unknown**; serial sum, order-sensitive estimator, runtime execution | An order-sensitive estimator is a plausible next hypothesis, but equivalent transformed behavior and compiler/runtime integration remain unproved. **VL-SCHED.** Reopen with a bounded semantic oracle and consuming execution path. |

---

# Duplicate, contradiction, and coverage flags

## Duplicates/restatements

1. **Broadcast requirement duplicate:** B1/B7/B9 and M5 restate the same unsupported “broadcast is mandatory” conclusion.
2. **Broadcast ideal arithmetic duplicate:** B2–B6 and M2–M3 reuse the same replicated-A versus zero-redundancy premise with different constants.
3. **Topology supersession duplicate:** T8 restates C1; the historical report was amended after the linked contention report.
4. **No universal topology/route winner:** C1/C5, R3/R4, S5, and T8 are related but not identical:
   - ring/mesh depends on traffic and placement;
   - XY/YX depends on orientation;
   - switching-mode equations are a separate decision.
5. **Context no-universal-mode duplicate:** X1 is restated by X4 and X6.
6. **Scheduler equality duplicate:** P1 combines the Summary table and Key Finding; the explanation in P2 is materially distinct and false.
7. **Table/prose repetitions:** numerical table rows were not double-counted when later prose merely repeats the same result without adding a prescription or causal conclusion.

## Arithmetic or semantic contradictions

1. **Broadcast L105:** `71,284` cycles is not slower than `1,055,744`; it is about **14.81× faster**.
2. **Broadcast L105:** a 32×32 PE array has **4×** as many MAC sites as 16×16, not “32× faster per core.”
3. **Broadcast versus multicore baseline:** approximately **16.8M** implied cycles versus **327,680** reported cycles for nominal 256³/16×16/one-core conditions.
4. **Multicore “sweet spot”:** report calls 4 cores the sweet spot although its own maximum speedup/TOPS occurs at 8; no objective justifies 4.
5. **Topology 4-core degeneracy:** prose/source says 2×2 mesh and ring are identical/both four hops, while the table/formula gives ring 6 and mesh 4.
6. **Topology bandwidth crossover:** displayed formula makes ring/mesh speedup independent of bandwidth, contradicting the claimed 32 GB/s crossover.
7. **Topology barrier claim:** historical mesh barrier reduction is unreachable through the topology-independent current barrier estimate.
8. **Scheduler causal explanation:** report calls cycles a DAG critical path; current source/book establishes a serial per-emitted-node sum.
9. **Scheduler “hoisting”:** report describes a transformation opportunity; current source only counts candidates and emits no move/barrier.
10. **“Lower bound” terminology:** contention and routing reports call the combined expression a lower bound. C12.43’s exact counterexample (`isolated=94`, `bottleneck=128`, `estimated=158`, feasible shared-pair term `133`) proves it can exceed a feasible overlapping schedule. It is a **heuristic score**, not a proved lower bound.
11. **Hotspot percentages are not contradictory:** “mesh 48.6% slower than ring” and “ring 32.7% lower than mesh” use different denominators.

## Zero-claim reports

- **None.** All eight reports contain at least one high-salience quantitative or prescriptive conclusion.

# Totals

| Item | Count |
|---|---:|
| Reports inspected | 8 |
| High-salience claims extracted | **49** |
| Retained | **5** |
| Qualified | **25** |
| Superseded | **3** |
| Rejected | **15** |
| Blocked/open | **1** |
| Sharing/topology claims | 38 |
| Runtime/static-policy claims | 11 |
| Reports with arithmetic/semantic contradictions | 5 |
| Explicit contradiction classes | 11 |
| Duplicate/restatement groups | 7 |
| Zero-claim reports | 0 |
| Metric domains used | 3 |
| Files created or modified | **0** |

The decisive Chapter 22 synthesis boundary is consistent across all eight reports: **sequential broadcast copies are not multicast; route-load scores are not queued makespans; context ledgers are not end-to-end continuation; scheduler serial estimates are not transformed behavior or compiler/runtime composition.**