# Chapter 9 Source and Claim Ledger — Memory Hierarchy and Banked Scratchpads

- **Pinned source:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Status:** executed and independently reviewed; each claim below states its evidence boundary
- **Evidence precedence:** executed pinned behavior → focused tests → live headers/runtime path → current docs → historical rationale

## Claim ledger

| ID | Planned claim | Current basis | Required closure evidence | Scope guard / risk | State |
|---|---|---|---|---|---|
| C9.1 | Capacity, bank mapping, service budget, latency, and integration are separate contracts. | architecture theory; split source structures | derivation plus probe families | do not collapse returned stalls into end-to-end latency | verified |
| C9.2 | Direct W/A/O regions are software-managed byte arrays with compiled default capacities and bank mapping `(addr / bank_width) % bank_count`. | `tu_config.h`, `tu_sram.h` | hash audit + map probe | direct operation uses typed views over raw bytes | verified |
| C9.3 | Default W/A/O capacities are 128/64/64 KiB and direct MMA requires whole W/A/O images to fit. | `tu_config.h`; Chapter 6 | cross-link Chapter 6 + live constructor probe | internal compute tiling is not operand streaming | verified |
| C9.4 | The SRAM budget is per bank and refills only after explicit cycle advancement. | `tu_sram.c` | same-bank/different-bank/refill probe | `words_per_cycle` naming may not match effective per-window throughput | verified |
| C9.5 | An exhausted budget still performs the copy immediately and returns a penalty; it does not model a waiting request. | `tu_sram.c` | functional-copy-on-stall probe | call it deterministic accounting, not queue simulation | verified |
| C9.6 | `arb_mode` is stored but does not select different arbitration behavior; `conflicts` is printed but not incremented by live SRAM accesses. | source inspection | enforced call/field audit + A/B probe where safe | absence claim is snapshot-specific | verified |
| C9.7 | SRAM base read/write latency constants and hierarchy latency fields are not charged by the modeled SRAM access path. | headers and implementation | source-consumer audit + exact probe accounting | DRAM has a separate domain | verified |
| C9.8 | `tu_sram_raw_ptr()` bypasses bank access counters and bandwidth budgets; direct MMA obtains W/A/O through this path. | `tu_sram.c`, `tu_cmodel.c` | before/after counter probe | some compute engines use modeled APIs; do not generalize to all operators | verified |
| C9.9 | The four-level hierarchy API is library-linked and focused-tested but not called by direct cmodel/core execution. | Makefile and call-site search | archive symbols, static link gate, enforced exact call-site set | linked is weaker than integrated | verified |
| C9.10 | RegFile is an activity abstraction: reads zero-fill and writes do not retain data. | `memory_hierarchy.c` | write/read discriminating probe | not a register-file functional store | verified |
| C9.11 | GBuf “hits” mean an in-range access, not cache-tag lookup; there is no allocation/replacement policy. | `memory_hierarchy.c` | in-range/out-of-range static/executable checks | unsafe out-of-range behavior must not be executed | verified |
| C9.12 | `tu_mem_hierarchy_tick()` advances hierarchy/DRAM time but does not advance GBuf SRAM refill time. | `memory_hierarchy.c` | GBuf pre/post-tick budget probe | keep cycle domains separate | verified |
| C9.13 | `tu_mem_hierarchy_set_level_config()` does not provide the documented pre-init override because initialization zeroes the object and reinstalls defaults. | header comment versus implementation | discriminating pre-init override probe | describe pinned behavior, not intended API | verified |
| C9.14 | JSON SRAM capacities reach `tu_runtime_config_t`, while parsed bank count/width and hierarchy/GBuf fields do not construct direct W/A/O banking at global initialization. | `infra/config.c`; Chapter 4 | parse-to-active probe + constructor inspection | specialized consumers elsewhere must be audited before broad absence claims | verified |
| C9.15 | GBuf initialization overwrites bank count/width after the generic SRAM constructor; allocation/state provenance must be checked separately. | `memory_hierarchy.c`, `tu_sram.c` | source audit + safe state probe | do not infer memory corruption without evidence | verified |
| C9.16 | Focused hierarchy tests validate ordinary aligned accesses and counters but do not prove direct-MMA integration, arbitration policy, latency charging, config effect, partial-word safety, or bounds failure-atomicity. | `tests/test_memory_hierarchy.c` | assertion inventory | passing test count has a precise denominator | verified |
| C9.17 | Bounds reporting in low-level SRAM access does not stop the subsequent copy. | `tu_sram.c` | static control-flow finding only | never execute the undefined access | verified |
| C9.18 | Partial-word handling has path-specific assumptions and requires static review before being advertised as general byte-granular safety. | hierarchy/SRAM implementation | static audit plus safe in-bounds canary probes if possible | avoid intentionally triggering host-buffer overflow | verified |
| C9.19 | Tusim can compare selected deterministic bank-budget alternatives, but current evidence does not establish physical SRAM timing, area, energy, or calibrated end-to-end speed. | fidelity matrix and implementation | fidelity box + review | no silicon/RTL calibration | verified |
| C9.20 | Memory choice is multi-objective: capacity, bandwidth, reuse, latency, area/energy, compiler placement, control, and verification costs vary by workload and mapping. | BAN02/WAT09/JOU17/CHE16/PAR19/KWO19 | bounded literature synthesis | no universal optimum | verified |
| C9.21 | A separate cycle/performance bank model uses byte-address modulo bank count, produces conflicts, and is source-present but absent from `TU_OBJS` and direct MMA. | `perf/cycle_model.[ch]`, Makefile | 24-file enforced audit | incompatible with generic SRAM mapping | verified |
| C9.22 | Config's 20/20 successful transcript is not a fail-closed regression gate because `CHECK` can return from `main` without `test_exit()`. | `tests/test_config.c`; independent forced-failure probe | source review and reviewer execution | report successful run, not gate strength | verified |
| C9.23 | Hierarchy reset preserves GlobalBuf refill/budget/per-bank state while zeroing hierarchy time. | implementation + revised probe | discriminating reset probe | split clock/reset domain | verified |
| C9.24 | Generic SRAM utilization omits the initial service window and clips over-one results. | implementation + revised probe | per-bank served/report snapshot | unsafe comparative metric | verified |

## Evidence labels

- **Executable:** low-level SRAM storage/budget APIs and standalone hierarchy APIs exercised in the archive.
- **Integrated:** only paths shown reachable from public/global operation execution; library membership alone is insufficient.
- **Functional model:** byte movement and selected counters without physical SRAM timing equivalence.
- **Functional model / estimated:** budget exhaustion returns fixed uncalibrated penalties without modeling queued request service or establishing a physical bound direction.
- **Historical:** repository docs when they disagree with pinned execution.
- **Estimated / uncalibrated:** all timing interpretations lacking named RTL/silicon comparison.

## Review disposition table

Populate after independent skeptical review.

| Finding | Reviewer | Disposition | Primary evidence | Artifacts changed |
|---|---|---|---|---|
| omitted third cycle-model bank surface | architecture | accepted | `perf/cycle_model.[ch]`, Makefile, 24-file audit | manuscript, audit, source audit, ledger |
| whole-image fit and capacity activation overstated | architecture/editorial/repository | accepted | `tu_cmodel.c`, allocation probe | manuscript, audit, ledger |
| partitioned placement equations absent | architecture | accepted | W/A/O independent regions and offsets | manuscript |
| aligned-only bank equation scope | architecture | accepted | bulk-loop source | manuscript, audit |
| utilization initial-window denominator defect | architecture | accepted | source + revised probe | manuscript, audit, ledger |
| config test harness not fail-closed | repository | accepted | `tests/test_config.c`; reviewer forced failure | manuscript, audit, README wording |
| custom GBuf allocation/count mismatch | repository/editorial | accepted static-only | constructor/allocation order | manuscript, audit, ledger |
| reset preserves GBuf refill state | repository | accepted | source + revised probe | manuscript, audit, ledger |
| GBuf canonical JSON described as merely dropped | repository | accepted and corrected | parser block inspection | manuscript, audit |
| reproduction machine-specific | repository/editorial | qualified | script now derives book root and accepts path overrides; detached clean pin remains intentional | reproduction script, manuscript note |
| undefined evidence label | editorial | accepted | style guide | manuscript |
| source map and explicit OI decision method missing | editorial/architecture | accepted | style guide and Roofline scope | manuscript |
