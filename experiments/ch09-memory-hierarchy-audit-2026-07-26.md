# Chapter 9 Memory-Hierarchy Audit — 2026-07-26

## Scope and provenance

This audit supports Chapter 9, **Memory Hierarchy and Banked Scratchpads**, against Tusim commit `e918c80b6fce833cd1fcae97730fa841c2176f25`. Execution occurred only in `/tmp/tusim-ch09-reproduction`, extracted with `git archive`. The source checkout remained detached, clean, and unchanged; its ignored-file inventory was identical before and after.

Reproduce from the book root:

```bash
bash experiments/ch09_reproduce.sh
```

The complete literal transcript is `experiments/ch09-reproduction-2026-07-26.log` and ends with `REPRODUCTION: PASS`.

## Environment

- AArch64 Linux 5.15.148-tegra
- GCC 11.4.0
- GNU Make 4.3
- Python 3.11.15
- deterministic source archive SHA-256: `fb023fe79a0e7dafbf334848756e44127101f5fdb75c1004e2ed2712318b708f`

## Enforced source audit

`ch09_memory_audit.py` checks the full revision marker and 24 SHA-256-pinned inputs. It also fails closed if:

- SRAM, hierarchy, or DRAM objects leave `TU_OBJS`;
- `test-memhier` leaves the aggregate test target;
- parsed memory-field propagation changes;
- bank geometry stops being compiled into the generic SRAM constructor;
- arbitration gains an executable consumer or the conflict counter gains a producer;
- hierarchy call sites extend beyond its implementation and focused test;
- hierarchy tick begins advancing SRAM refill time;
- direct MMA stops using raw SRAM pointers.
- the separate source-present cycle-model bank mapping, conflict producer, or non-integration state changes.

Observed result:

```text
SOURCE_AUDIT: PASS (24/24 hashes)
LIBRARY: SRAM+hierarchy+DRAM objects present; test-memhier aggregate-listed
CONFIG: capacities+banking parse; capacities propagate; banking/DRAM drop at runtime conversion; GBuf defaults are not parsed by canonical JSON
INTEGRATION: hierarchy call sites limited to implementation+focused test; direct MMA uses raw SRAM pointers
STATIC_LIMITS: low-level SRAM arbitration stored/no consumer; low-level conflicts no producer; hierarchy tick does not refill SRAM
THIRD_SURFACE: cycle-model bank engine source-present, conflict-producing, byte-address-modulo mapped, not TU_OBJS-integrated
```

## Focused execution

Archive-built static execution produced:

| Target | Result | Safe interpretation |
|---|---:|---|
| `test-memhier` | 10/10 | ordinary hierarchy lifecycle, aligned access, counters, delegation, reset/tick, and print smoke assertions pass |
| `test-cmodel` | 19/19 | direct cmodel functional cases pass; does not prove hierarchy integration |
| `test-config` | 20/20 reported in this successful run | parser, validation, selected runtime conversion, and one initialized MMA path pass; its bare-`return` failure macro makes the executable non-fail-closed |

All four binaries—three focused tests and the custom probe—resolved no `libtucmodel.so`. They used the archive-built static library.

## Discriminating probe

### Bank mapping and budget

With compiled generic SRAM geometry, bank mapping is:

```text
bank(addr) = floor(addr / 4) mod 32
```

A custom constructor used one available word per bank, a four-cycle refill window, and a three-cycle stall penalty. Writes to addresses `0`, `0`, and `4` returned stalls `0,3,0`: the repeated address exhausted bank 0, while address 4 selected bank 1.

The second write still replaced the stored value with `0x22222222`. A returned stall is therefore deterministic accounting attached to an immediately completed copy, not a queued request whose data movement waits for service.

After further bank-0 accesses, advancing three cycles did not refill; crossing the four-cycle boundary did. The `conflicts` counter remained zero. A direct raw-pointer store changed no reads, writes, or stall counters.

### Arbitration names

Identical write/write/read sequences under `TU_SRAM_ARB_NONE`, `TU_SRAM_ARB_ROUND_ROBIN`, and `TU_SRAM_ARB_PRIORITY` each returned ten total stall cycles. The enum is retained in state, but the pinned consumer implements no arbitration-dependent branch or requester order.

### Standalone hierarchy

A pre-initialization GlobalBuf override requested 2 KiB, two banks, four-byte words, and custom latency/budget fields. `tu_mem_hierarchy_init()` zeroed the object and restored compiled defaults. Active GlobalBuf state was 1 MiB, 16 banks, and eight-byte words.

Two same-address writes exhausted the GlobalBuf bank budget. Advancing the hierarchy by four cycles did not refill it; calling `tu_sram_advance_cycle()` directly on the GlobalBuf did. `tu_mem_hierarchy_tick()` advances the hierarchy counter and DRAM, not SRAM clocks.

A RegFile write followed by a read returned zero. The level records activity but has no retained backing store. Four in-range GlobalBuf accesses produced four “hits”; this is an address-range classification, not a cache tag, allocation, replacement, or reuse test.

### Configuration and direct MMA

The JSON fixture requested:

- W/A/O capacities 16/8/12 KiB;
- eight banks;
- eight-byte bank words.

Parsing retained all requests. Runtime conversion and initialized direct buffers retained the capacities, but active banking was the compiled 32 banks × four-byte words. The direct MMA then changed none of the W/A/O SRAM read/write counters sampled immediately around the call. Its raw-pointer access bypasses the modeled SRAM API.

Observed compact output:

```text
SRAM_BUDGET bank_count=32 bank_width=4 sequence=0,3,0 refill=3,3,0 stalled_copy=22222222 conflicts=0 raw_bypass=PASS
ARBITRATION none=10 round_robin=10 priority=10 behavior=identical
UTILIZATION bank0_served=2 reported=1.0 initial_window_omitted_and_clipped=yes
HIERARCHY preinit_override=erased gbuf=1048576B/16banks/8Bword tick_refill=no direct_refill=yes reset_refill_state=preserved regfile_storage=no hits_before_reset=4
CONFIG requested_banks=8x8B active_banks=32x4B capacities=16384/8192/12288 mma_sram_counter_delta=0/0/0 hierarchy_integration=absent
SUMMARY: PASS failures=0
```

## Static safety and fidelity findings

1. Low-level SRAM and direct DMA/MMA bounds helpers report errors but callers continue. The hierarchy's documented `-1` bounds status is not implemented, and addition-based range checks can wrap. These paths were not executed because doing so could invoke undefined memory access.
2. Non-word-multiple GlobalBuf transfers perform full-word accesses against caller buffers and can cross host-buffer bounds. LocalSPAD partial writes use a fixed temporary buffer and direct primary backing-store read. Evidence is aligned-only.
3. `read_latency`, `write_latency`, `double_buffered`, and arbitration fields exist in hierarchy configuration, but presence is not consumption.
4. `conflicts`, budget stalls, utilization, and base latency are distinct metrics. At the pinned revision, conflict count has no live producer in `tu_sram.c`.
5. Generic SRAM utilization divides served words by bank count, configured budget, and elapsed refill periods. It is a model-defined ratio, not measured physical port utilization.
6. Direct MMA and several operator paths use raw pointers. Other engines call accounted SRAM APIs. Memory fidelity is therefore operation-specific.
7. The source-present `perf/cycle_model.[ch]` implements a third, incompatible bank domain: starting byte address modulo bank count, its own conflict producer and clock, and whole-tile charging. It is absent from `TU_OBJS` and direct MMA.
8. `tu_gbuf_init()` allocates meter state at the compiled generic count before overwriting the active bank count; custom counts above 32 can make later indexing exceed the allocation.
9. Utilization omits the initial service window from its denominator and clips results above one; distinct histories can collapse to 100%.
10. Hierarchy reset leaves GlobalBuf SRAM clock, refill, budget, and per-bank state intact.
11. No evidence here calibrates physical SRAM latency, area, power, energy, or end-to-end DMA+MMA performance.

## Conclusion

Tusim has executable low-level SRAM storage/budget APIs and an executable standalone four-level hierarchy API. It can support controlled studies of its exact deterministic bank-budget formula when the path under study calls those APIs. It does not support treating the hierarchy counters as direct-MMA memory traffic, treating arbitration names as implemented requester scheduling, or interpreting its stalls as calibrated physical latency.
