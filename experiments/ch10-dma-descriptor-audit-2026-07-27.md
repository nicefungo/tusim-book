# Chapter 10 Audit — DMA Descriptor Contracts and Tick-Driven Execution

- **Date:** 2026-07-27
- **Tusim pin:** `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Canonical run:** `experiments/runs/ch10-dma-contracts/20260727T223000Z-hashguard/`
- **Result:** `AUDIT_SNAPSHOT_MATCHED_EXPECTED_FINDINGS`
- **Interpretation:** snapshot conformance, not a green correctness or calibration certificate

## Reproduction

```bash
cd /home/zxy/Workplace/books/tusim-book
bash experiments/run_ch10_data_movement_audit.sh
```

The runner verifies provenance before creating a unique durable run directory, exports the exact pin, builds only in the disposable extraction, runs a fail-closed source audit and custom probes, records focused harness observations, checks final source state, finalizes the completed transcript into that run's retained manifest, verifies that same manifest, and removes the disposable source/archive through an EXIT trap. Its final `FINALIZED_RUN PASS` line names the newly created and verified run.

### Provenance

- Tusim started and ended detached, clean, and unchanged at the exact pin.
- Tusim ignored inventory was unchanged; recorded inventory SHA-256: `bb6aa62e0a80724a77579cdf4ec844acba8d5f59a1d3b4418d0025b4456415ab`.
- Book remotes before and after: zero.
- Deterministic source-archive digest recorded before automatic deletion: `fb023fe79a0e7dafbf334848756e44127101f5fdb75c1004e2ed2712318b708f`.
- The completed transcript SHA-256 is recorded by the runner in `sha256-retained.txt` and reported by its final `FINALIZED_RUN PASS` line.
- `sha256-retained.txt` verifies the runner, both probes, source audit, archive membership, suite logs, and transcript by relative path.

The source audit enforces **33 exact source/test/config hashes** and **32 structural/reachability predicates**, for **65 fail-closed checks**. The archive-member gate separately requires `dma_descriptor.o`, `address_generator.o`, `double_buffer.o`, and `pipeline_controller.o`.

## Focused harness observations

These pinned harnesses are observations rather than the audit’s fail-closed correctness gate.

| Family | Observed result | Qualification |
|---|---:|---|
| descriptor DMA | 10/10 reported cases | named functional and accounting cases |
| scatter/gather | 15/15 | in-bounds focused cases |
| multicast | 10/10 | overflow target is skipped while the harness expects completion |
| address generator | **12/13** | transposed case expects `0x110`, observes `0x10c` |
| double buffer | 10/10 | standalone primitive behavior only |
| command queue | 9/9 | fixed wrapper routing |
| CModel | 19/19 | ordinary functional path |
| configuration | 20/20 | observation only; harness failure return is weak |
| pipeline | **not executed** | harness requests four channels against a three-entry engine array |

The custom one-channel pipeline boundary probe is not replacement coverage for the skipped pipeline suite.

## Lifecycle result

For one valid, in-bounds, 64-byte host-to-SRAM linear descriptor with SRAM bandwidth modeling disabled:

| Observation | Engine cycle | Directly inspected byte | `completed` | active slot | `cycles_completed` | async channel completed count |
|---|---:|---:|---:|---:|---:|---:|
| accepted | 0 | `0x00` | false | empty | 0 | 0 |
| after first tick selects and runs executor | 1 | `0x5a` | true | occupied | 53 | 0 |
| channel retirement | 53 | `0x5a` | true | empty | 53 | 1 |

Operational conclusion:

1. accepted submission becomes pending;
2. one tick selects the head, assigns the active slot, performs the complete host-side copy, and sets the descriptor flag;
3. direct host inspection can see bytes after that tick;
4. the channel remains occupied until the timestamp;
5. `cycles_issued` remains zero.

The evidence cannot separate selection, copy, and flag-setting within the same C function call. It does not establish command dependency visibility, coherent-memory readiness, or an interrupt/signal event. `completed` is not universal success: multicast can skip an invalid destination and still set it and account requested fanout.

### Failed-executor lifecycle

A controlled 8-byte descriptor at offset 60 of a 64-byte SRAM region exercises the executor's bounds rejection without performing an out-of-bounds copy:

| Path | Flag/timestamp after executor | Channel behavior | Engine transfers |
|---|---|---|---:|
| synchronous submit | false / 0 | `total_completed` increments to 1 | 0 |
| tick-driven | false / 0 | remains active after selection, then retires and increments `total_completed` on the next tick because timestamp zero is already eligible | 0 |
| flush | false / 0 | `total_completed` increments to 1 | 0 |

Thus channel “completed” counters count traversal/retirement events, not successful delivery. Successful descriptors alone receive the future eligibility timestamp described above. Public-wrapper overflow was kept static rather than executed because its void bounds reporter is followed by bulk access code whose own bounds helper also returns void; the path is not safe evidence.

## Queue, chain, and ownership result

### Counter divergence

A three-node synchronous chain produced:

- accepted submitted heads: 1;
- executor-accounted transfers: 3;
- synchronous channel completions: 3;
- final unsigned queue depth: `4294967294`.

The last value is `1 - 3 mod 2^32 = 2^32 - 2`. The queue increments once per submitted head and decrements once per traversed chain node.

### Structural corruption

The same `next` pointer represents both a descriptor chain and the channel queue:

```text
submit c0 → c1
head = tail = c0
submit q
c0.next = q          # c1 disconnected
head = c0, tail = q
```

The safe structural probe observed exactly this disconnection. A second case selected `c0`, leaving `head=c1` and stale `tail=c0`; submitting `q` assigned `c0.next=q`, so `q` was unreachable from `head=c1`.

Each corruption case runs in a separate child process. The child performs one safe initialization before submission, records the corrupted graph, and exits; process teardown reclaims its address space. The evidence intentionally does not reinitialize, traverse, flush, or destroy a live corrupted graph. Static source evidence shows why: during async chain execution, `active=c0`, `head=c1`, and `c0.next=c1`; engine destruction can free `c1` from the pending list and then recursively reach it again from `c0`.

### Ownership contract

There is no single safe “engine owns submitted descriptors” rule:

- rejection recursively destroys the submitted descriptor chain;
- accepted synchronous or tick-driven execution does not reliably reclaim it;
- caller destruction while pending/active invalidates engine state;
- pending multicast descriptors can lose nested-array reclamation through raw free;
- engine destruction can double-free active-chain aliases;
- reinitialization is destructive state overwrite, not cleanup: `tu_dma_init_full()` clears the singleton without disposing pending/active descriptors, so references and descriptor-owned arrays can be orphaned.

The bounded safe subset is independent, unchained descriptors with all borrowed objects alive through executor use; no caller destruction or engine reinitialization while pending/active; explicit caller destruction only after proving retirement and absence of aliases. Chains must not be combined with another same-channel submission.

## Transfer geometry result

### Byte taxonomy

`total_bytes` is not one universal payload quantity:

- linear and strided: logical copied bytes;
- scatter/gather: transfer-event bytes, including duplicate indices;
- multicast: requested aggregate fanout bytes.

For 2D geometry, copied bytes are `r c e`, while addressed span is `(r-1)s_r + c e`. For 3D, copied bytes are `d r c e`, while addressed span is `(d-1)s_d + (r-1)s_r + c e`, for nonzero dimensions.

### Executable oracles

- **2D:** two rows × three columns × two bytes; host row stride 11 B, SRAM row stride 13 B. Copied/accounted bytes: 12; source span: 17 B; destination span: 19 B. Both rows and all canaries matched.
- **3D:** two depths × two rows × three columns × one byte; host row/depth strides 5/13 B, SRAM row/depth strides 7/20 B. Copied/accounted bytes: 12; source span: 21 B; destination span: 30 B. All four rows and canaries matched.
- **Scatter duplicates:** three one-byte events at offsets `{4,4,8}` accounted three bytes but touched two unique offsets; the second write won at offset four.
- **Multicast:** four source bytes to two destinations produced eight requested/accounted fanout bytes and eight delivered bytes in the valid case.
- **Borrowed state:** mutating source byte and index list after descriptor construction but before submission changed the executed scatter destination, confirming both are borrowed.

Linear/strided source bounds compare base plus `total_bytes`, not maximum addressed span. Scatter/gather indices are not individually region-checked. Span and index safety remain caller obligations.

## Timing result

For bandwidth modeling disabled, the descriptor service estimate at this pin is

```text
C_service = TU_LATENCY_DRAM_READ + ceil(total_bytes / TU_DMA_BUS_WIDTH_BYTES)
          = 50 + ceil(total_bytes / 32) model cycles.
```

It is an **analytical model**, **estimated**, and **uncalibrated**.

| Bytes | Formula result | Observed descriptor timestamp in synchronous cycle-zero case |
|---:|---:|---:|
| 0 | 50 | 50 |
| 1 | 51 | 51 |
| 31 | 51 | 51 |
| 32 | 51 | 51 |
| 33 | 52 | 52 |
| 64 | 52 | 52 |
| 65 | 53 | 53 |

Descriptor stores use the read-latency macro in this executor. Read and write latency constants both happen to be 50 at the pin; equal numbers do not make the producers interchangeable.

A 1024-byte two-channel resource sweep reported:

| SRAM bandwidth switch | Regions | Channel 0 service | Channel 1 service |
|---|---|---:|---:|
| on | shared | 530 | 530 |
| on | separate | 530 | 530 |
| off | shared | 82 | 82 |

With 32 banks, 4-byte bank words, one available word per bank, and a two-cycle penalty, 1024 bytes correspond to 256 modeled bank words. The loop serves 32 initial words and marks 224 as stalled, so

```text
C_service,bw = 50 + ceil(1024/32) + (256-32)×2
             = 50 + 32 + 448
             = 530 model cycles.
```

The producer is the descriptor executor's contiguous bank-budget loop, not the standalone DRAM model. Thus the selected SRAM budget changes each descriptor estimate in this case, but shared versus separate regions and channel order do not create an observed estimate difference. This is an **Analytical model** and **Estimated** behavior—not evidence of physical independence, contention, sustainable bandwidth, or calibration.

Queue waiting is absent from `C_service`. Active-slot occupancy uses the future timestamp even though bytes were copied at selection. Engine `estimated_cycles` sums service estimates and is not elapsed time.

## Reachability and configuration result

The fail-closed source audit established:

1. Public W/A loads call legacy DMA raw-copy helpers.
2. Public O store calls the legacy store helper.
3. Public O load directly calls `tu_sram_write_bulk` and bypasses legacy DMA.
4. Command-queue fixed DMA operations route through public wrappers.
5. General descriptor submission outside implementation/tests is consumed by the standalone pipeline controller, not ordinary MMA operations.
6. The address-generator descriptor-chain helper has no external consumer.
7. Descriptor execution does not call `tu_dram_read`, `tu_dram_write`, or `tu_dram_estimate_transfer`.
8. `priority` and `signal_id` have no descriptor-engine consumer, and `cycles_issued` has no assignment.
9. Parsed DMA fields are absent from `tu_runtime_config_t` and `tu_config_to_runtime()`.
10. Top-level initialization uses compile-time DMA constants.

The config A/B probe first parsed a JSON string containing 128-bit width, 32-byte burst, one channel, depth two, async enabled, and multicast disabled; all six values were stored in `tu_config_t`. Passing that parsed structure through `tu_init_from_config()` left active state synchronous, three channels, depth four, and compile-time 256-bit width. Direct `tu_dma_init_full(true,1,2)` activated async, one channel, and depth two.

The direct initializer has a separate safety invariant. Its storage is `channels[TU_DMA_CHANNELS]` with `TU_DMA_CHANNELS == 3`; a zero request maps to that compiled default. The implementation clamps positive requests only at eight, then iterates through the effective count. Therefore safe direct initialization requires an effective count no greater than three. Requests 4–8 are unsafe and were source-audited rather than executed. Reinitialization additionally requires a quiescent engine because the initializer does not tear down pending or active descriptors.

A public 64-byte W load increased live `g_tu_dma.estimated_cycles` by 52 and top-level bytes by 64, but changed embedded `g_tu.dma.estimated_cycles` and top-level `g_tu.estimated_cycles` by zero. The wrapper samples the inactive embedded copy while the implementation updates the process-global engine.

## Boundary evidence and deferrals

- Address generator: one focused transposed case fails; range generation can return a logical count larger than caller capacity while the chain helper uses a fixed 128-entry array. Detailed mathematics are deferred.
- Pipeline: the unmodified suite is unsafe at the pin. A bounded one-channel probe shows attempted shadow redirection is ignored by the executor’s non-null destination region: bytes land in the old active buffer, the controller swaps, and stale shadow data becomes active. Valid overlap and speedup are rejected.
- DRAM: descriptor execution has no standalone DRAM-model call. Calibration and physical traffic are deferred.
- Double buffer: archive membership and standalone tests do not establish operation-path integration.

## Supported decisions

The chapter can compare descriptor forms by:

- representability;
- metadata and borrowed-lifetime burden;
- addressed-span/index safety;
- pending-head capacity;
- synchronization/reuse burden;
- verification complexity.

It cannot select a physically fastest descriptor, infer sustainable bandwidth, claim compute overlap, or derive area/power/energy.

## Audit disposition

The revised evidence bundle addresses the first skeptical review’s blocking findings through fail-closed source assertions, expanded safe probes, exact lifecycle/ownership/byte/counter taxonomies, automatic cleanup, and a self-verifying retained manifest.

**Drafting remains blocked until an independent re-review clears the revised bundle.**
