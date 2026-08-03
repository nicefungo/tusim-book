# Chapter 2 Experiment — Audit of Tusim’s Standalone Cycle Model

- **Date:** 2026-07-25
- **Tusim source snapshot:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Host:** AArch64 Linux
- **Compiler:** GCC 11.4.0
- **Purpose:** distinguish source-level availability, standalone testability, build integration, configuration reachability, and justified fidelity labels.

## Source evidence

At the pinned snapshot:

1. `tu_cmodel/perf/cycle_model.c` implements functional, estimated, and a mode named `TU_CYCLE_MODEL_CYCLE_ACCURATE`.
2. `tests/test_cycle_model.c` contains 21 checks for pipeline-helper behavior, bank budgets, DRAM row states, synthetic DMA-arbitration state, and the three cycle-accounting modes.
3. `Makefile` does **not** include `tu_cmodel/perf/cycle_model.o` in `TU_OBJS`.
4. `Makefile` has no `test-cycle-model` target and its aggregate test targets do not compile `tests/test_cycle_model.c`.
5. `config/tu_config.json` requests `"cycle_model": "cycle_accurate"`.
6. `tu_cmodel/tu_config.h` sets `TU_CYCLE_MODEL` to `0`, documented there as functional mode.
7. Searches outside the standalone implementation and test found no calls that create or execute this cycle model in the library’s main runtime path.

These facts show why “implemented,” “tested in isolation,” “linked,” “configured,” and “reachable from normal execution” must be separate ledger fields.

## Direct test command

```sh
cc -O2 -Wall -Wextra -std=c11 -fPIC -I. -Itu_cmodel \
  -o /tmp/tusim-test-cycle-model \
  tests/test_cycle_model.c \
  tu_cmodel/perf/cycle_model.c \
  tu_cmodel/perf/performance_counters.c \
  -lm
/tmp/tusim-test-cycle-model
```

## Direct test result

The standalone test completed successfully:

```text
Tests: 21 run, 21 passed, 0 failed
```

For its `16×16×64` tile, the test report included:

```text
Model fidelity: CYCLE_ACCURATE
Total cycles: 2619
SRAM Reads: 1024
SRAM Writes: 256
Bank stalls: 1277 cycles
Bank conflicts: 3
Avg utilization: 4000.0%
DRAM Accesses: 0
Data transferred: 0 bytes
Eff. bandwidth: 40.0 GB/s
```

The 21 passing tests verify the assertions encoded by that test program. They do not establish integration with the main library, calibration against RTL, or physical timing accuracy.

## Three-mode probe

The preserved probe source is [`ch02_cycle_model_probe.c`](ch02_cycle_model_probe.c). It invokes one tile with `M=N=16`, `K=64`, and addresses `W=0x100`, `A=0x200`, `O=0x300` through each standalone mode.

From the Tusim repository root, it was built and run with:

```sh
cc -O2 -Wall -Wextra -std=c11 -fPIC -I. -Itu_cmodel \
  -o /tmp/tusim-ch02-probe \
  /home/zxy/Workplace/books/tusim-book/experiments/ch02_cycle_model_probe.c \
  tu_cmodel/perf/cycle_model.c \
  tu_cmodel/perf/performance_counters.c \
  -lm
/tmp/tusim-ch02-probe
```

Raw output:

```text
constants: pe=16x16 depth=2 banks=32 bank_width=4 words_per_cycle=1 window=4 penalty=2
mode=functional returned_cycles=0 current_cycle=0
mode=estimated returned_cycles=128 current_cycle=128
mode=named-cycle-accurate returned_cycles=2619 current_cycle=2619 bank_reads=1024 bank_writes=256 shortfall_words=1277 conflicts=3 reported_util=40.000
```

### Reconstructing the estimated result

For `m=n=16`, `k=64`, and pipeline depth 2, the source computes:

```text
fill    = depth × n = 2 × 16 = 32
compute = k         = 64
drain   = depth × m = 2 × 16 = 32
total               = 128 cycles
```

This is a deterministic formula result under the source’s assumptions. It is not a measured latency.

### Reconstructing the named-cycle-accurate result

The source maps all three supplied addresses to bank 0 because it computes `address % 32`. With a four-byte bank width:

```text
weight words     = 16 × 64 × 2 / 4 = 512
activation words = 64 × 16 × 2 / 4 = 512
output words     = 16 × 16 × 4 / 4 = 256
```

Each aggregate access begins with one available word. The shortfalls are therefore 511, 511, and 255 words, totaling 1277. The implementation charges two cycles per shortfall word, producing 2554 penalty cycles. Adding one decode cycle and 64 compute cycles gives:

```text
1 + 2554 + 64 = 2619 cycles
```

This exactly reconstructs the returned value. It does **not** show completion of a bank-service schedule: the bank API says a caller should stall and retry, but the top-level tile path charges one aggregate penalty and does not retry denied words. The result is a shortfall heuristic, not a demonstrated duration for servicing all 1280 words under the refill budget.

## Findings

### What is supported

- The standalone cycle-model source compiles when explicitly linked with its dependencies.
- Its dedicated tests pass on the recorded host.
- The cycle-accounting return values of the modes named `FUNCTIONAL`, `ESTIMATED`, and `CYCLE_ACCURATE` are reproducible. The first establishes only zero-cycle accounting in this module; it does not execute or verify GEMM arithmetic.
- The `2619` result is reproducible and explainable from the encoded bank-budget heuristic.

### What is not supported

- The main Tusim build does not integrate this module at the pinned snapshot.
- The JSON setting is not evidence that the runtime executes this model.
- No RTL, FPGA, or silicon calibration evidence was found for the `2619` result.
- The implementation does not model every cycle-relevant state transition of a specified hardware design.
- Pipeline entries do not step through the declared stages in the top-level tile path, which issues and then completes one entry serially. Direct hazard tests exercise helper state and fallback latency rather than sustained multi-tile pipeline evolution.
- The DMA arbitration test creates contention by manually injecting future-looking helper state. Normal DMA execution stores cumulative durations in the same array, while arbitration reads those values as if they were completion timestamps; end-to-end DMA contention is therefore not established.
- The label `CYCLE_ACCURATE` is therefore not a defensible external evidence label for this result.

### Counter-semantic defects exposed by the run

1. `tu_bank_model_get_stats` returns an access count normalized only by `num_banks × max_accesses_per_cycle`, without a time interval. The resulting `40.0` is printed as `4000.0%`, so it is not a bounded time-average utilization.
2. The bank statistic named `total_stalls` sums shortfall words, while the report labels it “cycles.” The execution path multiplies those shortfalls by a two-cycle penalty; hence the report prints `1277 cycles` while execution added `2554` cycles.
3. When there are no DRAM accesses, `tu_cycle_dram_get_stats` does not assign the hit-rate or bandwidth outputs. The report then prints uninitialized caller variables; the observed `40.0 GB/s` is not evidence of DRAM performance.
4. `conflict_count` increments for any nonzero access after the available-word count falls below capacity, including an ordinary first access. It should not automatically be interpreted as the number of simultaneous bank conflicts.
5. The address-to-bank rule uses `byte_address % num_banks` rather than dividing by bank width before bank selection. For four-byte-aligned addresses and 32 banks, this can collapse expected bank diversity.
6. The top-level tile path does not retry denied bank words, so the returned penalty does not establish that the modeled request completed under the refill/service contract.
7. Pipeline stage state does not advance cycle by cycle through the declared stages in ordinary top-level tile execution.
8. DMA arbitration is tested with synthetic state that does not match the meaning assigned to the same fields by normal transfer execution.

## Safe conclusion

> At snapshot `e918c80`, Tusim contains a standalone serial aggregate timing heuristic with separately testable pipeline, bank, DRAM, and arbitration helpers. Its dedicated 21-test program passes when compiled manually, and the cycle-accounting return values of source modes named `FUNCTIONAL`, `ESTIMATED`, and `CYCLE_ACCURATE` are reproducible. The first mode only returns zero timing in this module; it is not a functional GEMM oracle. The module is absent from the normal library/runtime path, its top-level execution does not evolve a multi-entry pipeline or complete denied bank requests through retries, and it is uncalibrated. It should not be presented as integrated cycle-accurate evidence.

## Development implications

A future integration should require:

1. one authoritative runtime configuration path;
2. explicit inclusion in the library and test graph;
3. definitions and units for every counter;
4. interval-aware, bounded utilization metrics;
5. separate shortfall-event and stall-cycle counters;
6. initialized outputs for empty-statistics cases;
7. word-address-aware bank mapping;
8. trace-based validation against a named RTL or other reference;
9. residual/error reporting across a workload suite;
10. fidelity labels derived from validated contracts rather than enum names.
