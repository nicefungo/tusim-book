# Chapter 10 Source and Claim Ledger — DMA Descriptor Contracts and Tick-Driven Execution

- **Pinned source:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Canonical revised run:** `experiments/runs/ch10-dma-contracts/20260727T223000Z-hashguard/`
- **Status vocabulary:** `verified`, `qualified`, `rejected`, `blocked`
- **Draft gate:** pending independent re-review of this revised ledger and evidence bundle

## Claim ledger

| ID | Claim | Evidence | Status | Required wording / limitation |
|---|---|---|---|---|
| C10.1 | The descriptor API represents linear, 2D, 3D, scatter, gather, and multicast forms. | `dma_descriptor.[ch]`; focused cases | verified | representability, not public-operation reachability |
| C10.2 | Constructors encode direction, region/base, host pointer, dimensions, strides, element size, channel, and byte count. | constructor source; source audit hashes | verified | exact pinned fields only |
| C10.3 | `total_bytes` has transfer-specific meaning rather than one universal payload meaning. | constructors; extended geometry oracle | verified | use byte taxonomy below |
| C10.4 | 2D/3D functional copying follows nonsymmetric host/SRAM strides for the canary cases. | extended probe | verified | named in-bounds cases; bounds validation is weaker than span |
| C10.5 | Scatter/gather index entries are byte offsets and may duplicate/overlap. | executor; duplicate-index probe | verified | transferred events differ from unique bytes touched |
| C10.6 | Multicast `total_bytes` is requested aggregate fanout; invalid targets can be skipped while full accounting and `completed` still occur. | executor; focused overflow case; fanout oracle | verified | `completed` is not all-target success |
| C10.7 | Linear/strided host pointers, index lists, and SRAM-region objects are borrowed; multicast copies its arrays but borrows region pointers and source data. | constructors/destructor; mutation probe | verified | caller lifetime must extend through executor use |
| C10.8 | Synchronous submission selects and executes the chain in the submit call. | submit loop; probe | verified | it does not automatically reclaim successful descriptors |
| C10.9 | In tick-driven mode, accepted submission is pending until a tick selects a descriptor. | 64-byte timeline | verified | “selected” replaces unobservable sub-tick “issued” |
| C10.10 | For the valid, successfully accounted, in-bounds 64-byte linear case, bytes and `completed` are directly host-observable after selection at engine cycle 1, while channel retirement occurs at cycle 53. | custom timeline | qualified | direct host observation only; not modeled dependency visibility |
| C10.11 | On successfully accounted descriptors, `cycles_issued` remains zero and `cycles_completed` is a future eligibility timestamp, not the instant bytes become visible. Failed executor paths leave both timestamp and flag zero. | source audit; timing and error probes | verified | distinguish successful timestamp eligibility from outcome-blind channel retirement |
| C10.12 | `completed` is path-dependent and not a universal success predicate. | linear timeline, multicast overflow, executor error returns | verified | never use unqualified “completion” |
| C10.13 | Queue admission capacity counts submitted heads. | submit source; queue probe | verified | not descriptor nodes, executable work, or guaranteed reachability |
| C10.14 | A three-node synchronous chain increments submission once, executes/completes three nodes, and underflows depth to `2^32-2`. | custom probe | verified | derive as `1-3 mod 2^32` |
| C10.15 | Chain linkage and queue linkage share `next` and are not composable with multiple queued heads at the pin. | source audit; two structural probes | verified | treat chains plus additional same-channel submissions as unsafe |
| C10.16 | A later head can disconnect a chain node; submission while chain head is active can make the new head unreachable from pending `head`. | structural probes | verified | do not flush/destroy corrupted graphs in evidence |
| C10.17 | Rejection destroys a submitted chain, accepted execution does not reliably reclaim it, and engine destruction can double-free active-chain aliases. | source audit; static ownership review | verified | no general “engine owns submitted descriptors” claim |
| C10.18 | Descriptor service estimate is `50 + ceil(total_bytes/32)` model cycles plus selected SRAM-budget penalties at the pin. | source; 0/1/31/32/33/64/65 sweep | verified | analytical model + estimated + uncalibrated; not elapsed time |
| C10.19 | Descriptor stores use the read-latency macro; read and write constants both equal 50 at the pin. | source; store probe; constants | verified | name producer even though current numbers coincide |
| C10.20 | With bandwidth modeling on, a 1024-byte case reports 530 service cycles; off reports 82. Shared and separate regions both report equal per-channel estimates in the tested setup. | extended resource sweep | qualified | no physical contention or independence inference |
| C10.21 | Two channels can be selected into the executor in one tick. | cross-channel probe | qualified | parallel executor dispatch only; no shared-fabric bandwidth claim |
| C10.22 | `estimated_cycles` is an aggregate sum of per-transfer estimates, not elapsed time; queue waiting is excluded from descriptor service. | executor/counters | verified | name counter unit and update event |
| C10.23 | Descriptor execution does not call the standalone DRAM model. | fail-closed source audit | verified | library membership is not integration |
| C10.24 | Public W/A loads and O store use legacy raw-copy helpers; public O load bypasses legacy DMA; command-queue DMA operations route through fixed wrappers. | fail-closed source audit | verified | general descriptors are not ordinary operation operands |
| C10.25 | Public wrapper bytes update while top-level cycle accumulation samples inactive embedded `g_tu.dma`; live estimates accrue in `g_tu_dma`. | counter probe | verified | byte and cycle domains diverge |
| C10.26 | Non-default DMA config fields parse but do not reach top-level DMA initialization; direct initializer values do activate. | source audit; config A/B probe | verified | compile-time bus width remains 256 bits |
| C10.27 | Descriptor `priority`, `signal_id`, and `cycles_issued` lack engine consumers/assignment at the pin. | source audit | verified | command queue has a different signal registry |
| C10.28 | Address-generator transposed focused case fails (`0x10c` versus `0x110`), and its range helper can return a logical count beyond storage capacity. | focused log; bounded probe; static helper | qualified | boundary evidence; detailed address generation deferred |
| C10.29 | Valid DMA-to-shadow overlap is not established: bounded pipeline probe writes old active storage, swaps, and exposes stale active data. | one-channel boundary probe | rejected | reject overlap correctness/speedup at this pin |
| C10.30 | The unmodified pipeline suite is safe to execute. | source audit: requests four channels against three-entry array | blocked | suite intentionally skipped; bounded probe is not replacement coverage |
| C10.31 | One global descriptor engine provides independent per-core DMA state. | singleton `g_tu_dma`; top-level state split | rejected | process-global ownership limits multi-instance claims |
| C10.32 | Physical throughput, best-descriptor performance, compute overlap speedup, area, power, and energy can be inferred. | absent calibration/integration | rejected | unavailable from this chapter’s evidence |
| C10.33 | Channel `total_completed` proves successful data delivery. | controlled sync/async/flush bounds-error probes | rejected | all three paths increment it after executor failure; async retires the zero-timestamp descriptor on the next tick |
| C10.34 | Reinitializing the singleton descriptor engine safely disposes pending and active descriptors. | `tu_dma_init_full()` source predicate | rejected | unconditional `memset` drops engine references without teardown; descriptors and descriptor-owned arrays can leak |
| C10.35 | Every public channel count accepted by the initializer's 1–8 clamp is safe. | fixed array declaration; initializer source predicate | rejected | safe effective count is `<= TU_DMA_CHANNELS` (3); zero maps to 3, while requests 4–8 index beyond the array |

## Byte taxonomy and span equations

For element count/index count `n`, multicast target count `m`, element size `e`, columns `c`, rows `r`, depth `d`, row stride `s_r`, and depth stride `s_d`:

- **Linear source payload / accounted bytes:** `n e`.
- **2D logical copied/accounted bytes:** `r c e`.
- **2D addressed span for a side:** `0` when `r=0` or `c=0`; otherwise `(r-1)s_r + c e`.
- **3D logical copied/accounted bytes:** `d r c e`.
- **3D addressed span for a side:** `0` when `d=0`, `r=0`, or `c=0`; otherwise `(d-1)s_d + (r-1)s_r + c e`.
- **Scatter/gather accounted bytes:** `n e`; for `n=0`, the addressed envelope is empty with span zero; otherwise unique bytes touched can be smaller with duplicate/overlapping indices and the envelope follows minimum/maximum index plus `e`.
- **Multicast source payload:** `n e`; requested fanout/accounted bytes: `m n e` for `m` targets; successful delivered bytes can be smaller because invalid targets are skipped.

These equations assume nonnegative mathematical integers and no arithmetic overflow. The implementation stores products, bases, strides, indices, and sums in `uint32_t` without checked arithmetic. At the pin, linear/strided bounds compare base plus `total_bytes`, not maximum addressed span. The chapter therefore treats overflow, span, and index safety as caller verification obligations.

## Lifecycle predicates

| Predicate | Operational meaning at the pin |
|---|---|
| constructed | descriptor object and borrowed/copy metadata initialized |
| accepted | `tu_dma_submit_desc` returns nonzero; rejection destroys the submitted chain |
| pending/reachable | node can be reached from channel `head` through the overloaded `next` graph |
| selected | tick removes current `head`, assigns `active`, and invokes executor in the same call |
| executor returned | copy/accounting function returned; errors may return without setting flag |
| executor rejected/error | bounds, null-pointer, direction, or type check returned before accounting; no explicit descriptor error field is set |
| directly observable | external host inspection of model memory sees copied bytes after executor return |
| flag set | `desc->completed == true`; not universal all-target success |
| timestamp eligible | engine cycle reaches `cycles_completed` |
| channel retired | active slot clears and async channel completed counter increments |
| safely reusable/freeable | caller has proven object is neither pending, active, nor aliased through a corrupted chain/queue graph |
| reinitialized | `tu_dma_init_full()` zeroes the singleton without teardown; pending/active references are orphaned and nested descriptor-owned arrays can leak |

No modeled dependency consumer uses descriptor `signal_id`; direct host observation must not be generalized to command readiness or coherent memory visibility.

## Ownership matrix

| Object/state | Construction | Rejection | Accepted pending/active | After successful sync or retirement | Engine destroy |
|---|---|---|---|---|---|
| descriptor object/`next` chain | caller holds allocation | submit recursively destroys chain | caller must not free; engine links/uses but does not promise reclamation | caller cleanup is required only after proving no queue/active alias | unsafe for active chains that still point into pending nodes |
| linear/strided host buffer | borrowed | caller retains buffer | must remain valid through executor return | caller may reuse after required direct observation/lifecycle proof | never owned by engine |
| scatter/gather index list | borrowed | caller retains list | must remain valid through executor return | caller may reuse afterward | never owned by engine |
| SRAM region object/storage | borrowed | caller retains region | must remain initialized and stable | caller-managed | never owned by descriptor |
| multicast source | borrowed | caller retains source | must remain valid through executor return | caller-managed | never owned by descriptor |
| multicast region/offset arrays | copied into descriptor-owned arrays | freed by recursive descriptor destroy | descriptor owns copies; region objects remain borrowed | freed only when descriptor is explicitly destroyed | pending raw-free path leaks nested arrays |
| engine singleton during reinit | existing global state | not applicable | reinit abandons pending/active references without destruction | reinit is not a cleanup mechanism | call explicit safe cleanup only after quiescence |

**Safe subset at the pin:** independent, unchained descriptors with caller-held borrowed objects; no caller destruction or engine reinitialization while work is pending/active; explicit post-retirement descriptor destruction; and effective direct-initializer channel count no greater than `TU_DMA_CHANNELS`. A zero request maps to the compiled default of three. Requests 4–8 are unsafe despite the initializer's clamp to eight. Descriptor chains must not be mixed with another same-channel submission. Even this subset carries process-global engine and error-reporting limitations.

## Counter units

| Counter/field | Unit | Update event |
|---|---|---|
| channel `queue_depth` | submitted heads on enqueue; decremented per traversed node | inconsistent for chains |
| channel `total_submitted` | accepted submitted heads | once per submit call |
| channel `total_completed` | synchronous/flush traversed nodes; async retired active nodes | outcome-blind and mode/path dependent; increments after controlled executor errors |
| engine `total_transfers` | executor-accounted descriptors | after executor accounting, including multicast partial delivery |
| engine/channel `total_bytes` | descriptor `total_bytes` | after executor accounting |
| engine `estimated_cycles` | sum of per-descriptor service estimates | not elapsed time |
| descriptor `cycles_completed` | engine-cycle timestamp eligibility | executor accounting |
| descriptor `cycles_issued` | inert field | never assigned at pin |

Submission/completion ratios are not meaningful for chains. Queue pressure and throughput must not be inferred from mixed counter units.

## Evidence labels

- **Functional model:** host-memory/SRAM byte effects.
- **Executable:** named static-linked focused cases and fail-closed custom probes.
- **Analytical model:** source formulas reconstructed from constants and fields.
- **Estimated:** descriptor service and pipeline formula fields are not calibrated against RTL or silicon.
- **Integrated:** ordinary operations integrate fixed legacy wrapper paths; general descriptors, descriptor-to-DRAM timing, address-generator operation routing, and valid overlap are not integrated at the pin.

## Review dispositions

The first skeptical review blocked drafting. This revision addresses its required dispositions by:

1. changing the title and preserving ranked candidate boundaries;
2. enforcing 33 source hashes and 65 source/reachability checks;
3. adding exact ownership, lifecycle, byte, span, and counter taxonomies;
4. adding queue-corruption, geometry, lifetime, timing, bandwidth, and config probes;
5. renaming the runner result to snapshot conformance;
6. separating focused observations from fail-closed gates;
7. preserving a self-verifying retained manifest and automatic cleanup;
8. retaining known failure/skip visibility and precise evidence labels.

Drafting remains blocked until independent re-review clears these dispositions.
