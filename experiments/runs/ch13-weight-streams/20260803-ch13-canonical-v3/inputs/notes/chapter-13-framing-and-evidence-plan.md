# Chapter 13 Framing and Evidence Plan — Weight Streams: Quantization, Structured Sparsity, and Compression

- **Edition:** Tusim `e918c80b6fce833cd1fcae97730fa841c2176f25`
- **Book workspace:** `/home/zxy/Workplace/books/tusim-book` (branch `main`; full history)
- **Source workspace:** `/home/zxy/Workplace/projects/tusim` (detached, clean, read-only)
- **Status:** scope selected from fresh whole-tree reconnaissance; drafting blocked pending claim audit, canonical execution, skeptical review, and gate closure

## Fresh reconnaissance basis

The selection started from the complete current book status and a fresh inventory of uncovered executable surfaces at the pin, not from Chapter 12's deferred list. The audit compared uncovered pinned surfaces after Chapters 1–12 using six questions:

1. What reader decision would the chapter enable?
2. Does the family teach adjacent mechanisms without implying one integrated execution/timing domain?
3. Which declarations reach a library, test, public/runtime path, and discriminating byte effect?
4. Which configuration fields propagate to the selected consumer, and which stop at the full-config boundary?
5. Can the principal claims be tested safely in a disposable archive?
6. Would combining adjacent modules blur byte effects, analytical estimates, or calibration scope?

## Ranked candidate boundaries

| Rank | Candidate | Reader decision and evidence | Principal risk | Disposition |
|---:|---|---|---|---|
| 1 | **Weight streams: INT/UINT quantization, 2:4 structured sparsity, and RLE/bitmap/adaptive compression with decoder throughput** | decide which weight representation (raw, RLE, bitmap, adaptive, dense 2:4, INT8, UINT4) a design should stream, and which cycle quantity is a byte-derived estimate versus an uncalibrated decoder assumption; linked codecs, prune/encode/decode helpers, sparse MMA, config parse/validation, three test families, two sweeps, and five exploration reports share one weight-path boundary | easy to merge the three adjacent surfaces (numeric conversion, structured sparsity, lossless codec) into one “compression” story or to read decoder throughput as measured hardware | **selected** |
| 2 | Operator engines and heterogeneous return metrics | select elementwise, convolution, pooling, normalization, softmax, or attention API and interpret its return/statistics contract | too many numerical kernels and incompatible return meanings for one coherent evidence domain | split into later operator-family chapters (deferred) |
| 3 | Performance counters and metric provenance | decide which named counter, interval, and producer can support a metric | would require reopening several compute, DMA, memory, and power domains at once; one chapter could encourage invalid aggregation | defer until after remaining producer chapters |
| 4 | DRAM interfaces and timing abstractions | choose between the linked hierarchy DRAM model and source-present cycle-model DRAM channel | Chapter 9 already established the three-memory-surface boundary; a full chapter needs a separate calibration/source study | defer |
| 5 | Multi-context save/restore and preemption estimates | choose retention scope and scheduling policy | narrower systems topic and less foundational before the weight/data-efficiency layer | defer |
| 6 | Cycle model | source present but absent from `TU_OBJS` at this pin | must be described as not library-integrated; negative-evidence chapter with no executable aggregate path | defer; record as a fidelity boundary |

### Independent scope-panel disposition

The selected family is evidence-derived because it is the largest substantial uncovered surface with: three library-linked codec/sparsity/quantization modules in `TU_OBJS`, parsed and validated `weight_compression` and `sparsity` configuration blocks with **exact full-config consumers**, a portable 16-byte frame format, focused tests, linked sweeps, and exploration reports that can be challenged rather than copied. It is not a Chapter 12 deferred topic; Chapter 12 deferred queues, arbitration, coherence, counters, contexts, DRAM calibration, and operator engines.

## Reader decision

> Given a weight tensor, a target traffic budget, and an accuracy constraint, which pinned Tusim weight-stream representation (raw FP16, RLE, bitmap, adaptive, 2:4-structured, INT8, or UINT4) produces which byte effects, which configuration fields reach which consumer, and which reported cycle quantity is a deterministic estimate, a decoder-throughput assumption, or no executable claim at all?

The reader must be able to reject these substitutions:

1. a codec family, a structured-sparsity module, and a numeric quantization API are not one integrated weight pipeline;
2. an encoded-size or payload-DMA-cycle number is not a measured decode latency or a calibrated speedup;
3. a parsed and validated `weight_compression` or `sparsity` block does not automatically reach `tu_runtime_config_t` — `tu_config_to_runtime()` drops every compression and sparsity field;
4. a sparse-MMA helper and a dense-MMA path do not share an execution domain, and a source-present sweep without a Makefile target is not an executable aggregate result.

## In scope

1. `tu_int_quant` (INT8/UINT4): parameter initialization, symmetric/asymmetric calibration, `fp32↔int8` and `fp32↔uint4` conversion, packed-nibble UINT4 layout, buffer conversions, dot product, and the standalone INT8 MMA tile.
2. `structured_2of4`: mask validity/popcount/nth-bit, FP32 pruning and mask-verified pattern checks, compress/decompress, per-group encode/decode, packed size, dense-versus-2:4 MMA helpers (untiled and tiled), speedup ratio, and the config-driven cycle estimator.
3. `weight_compress` (RLE / adaptive RLE / bitmap / adaptive): 16-byte portable frame (magic `0x54555743`, version 1), run encoding, bitmap occupancy maps, adaptive selection, round-trip and corrupt-frame validation, compression ratio, DMA-oriented encode/decode entry points, and the payload-DMA + decoder cycle estimator with overlap flags.
4. Full-config parse, validation, and field-level reachability for `weight_compression` (8 fields) and `sparsity` (5 fields), including the exact boundary where `tu_config_to_runtime()` drops them and the exact consumers that read the full `tu_config_t` instead.
5. Focused and aggregate inclusion: which of `test-int-quant`, `test-sparsity`, `test-compress`, and the sweeps are in aggregate `make test`; the source-present `test_int8_sweep.c` that has no Makefile target.
6. Defaults and shipped config: compression disabled/`none`, sparsity disabled, decoder rates at 1, and the exact validation rejections (unstructured sparsity, enabled-without-2:4, zero decoder groups).

## Explicitly deferred

- A unified codec→decoder→sparse-MMA execution path (dense reconstruction versus direct compressed-domain feed is BLOCKED in the implementation backlog; do not claim an integrated path).
- Physical decoder area/power, FIFO depth, SRAM bank conflicts during decode, ISA auto-dispatch of 2:4, and calibrated hardware throughput or latency.
- Accuracy-loss studies from pruning or quantization (no trained-model or retraining evidence at the pin).
- Repair of `tu_config_to_runtime()` field drops, failure-open checks, or the stale aggregate-target gaps.
- Operator engines, performance counters, DRAM calibration, context switching, and liveness allocation (separate later work units).
- New GEMM speedup predictions from historical analytical scripts (e.g., `docs/exploration/int8-quantization-throughput.md`, `test_int8_sweep.c`) — those are historical analytical reports, not executable cmodel evidence.

## Source map

| Surface | Authoritative pinned files | Safe question |
|---|---|---|
| INT/UINT quantization API | `tu_cmodel/tu_int_quant.{h,c}` | which conversions and calibrations are executable, and which quantized MMA path exists? |
| structured 2:4 sparsity | `tu_cmodel/sparsity/structured_2of4.{h,c}` | what do prune, encode, decode, MMA, and the config-driven estimator actually compute? |
| weight compression codecs | `tu_cmodel/memory/weight_compress.{h,c}` | which formats, frame bytes, round-trip checks, and decoder assumptions are real? |
| config parse/validation | `tu_cmodel/infra/config.{h,c}`, `tu_cmodel/tu_config.h`, `config/tu_config.json`, `config/tu_config.yaml` | which compression/sparsity declarations parse, validate, and reach which consumer? |
| runtime conversion boundary | `tu_cmodel/infra/config.c` (`tu_config_to_runtime`) | which weight-path fields are dropped before runtime and which read the full struct? |
| focused verification | `tests/test_int_quant.c`, `tests/test_sparsity.c`, `tests/test_compress.c` | which assertions gate nonzero, and which aggregate target includes them? |
| sweeps | `tests/test_weight_compression_sweep.c`, `tests/test_sparsity_sweep.c`, `tests/test_int8_sweep.c` | which sweeps are linked cmodel runs versus source-present analytical reports? |
| historical/current docs | `docs/exploration/weight-compression-rle-sweep.md`, `docs/exploration/bitmap-weight-compression.md`, `docs/exploration/structured-2of4-sweep.md`, `docs/exploration/weight-decoder-throughput.md`, `docs/exploration/int8-quantization-throughput.md`, `docs/exploration/IMPLEMENTATION_BACKLOG.md`, `docs/weight-compression.md` (if present), `docs/int8-quantization.md`, `docs/structured-sparsity.md` | rationale, prior claims, corrections, and known drift only |
| external foundations | [KWO19](../references/foundations.md#kwo19-maestro), [PAR19](../references/foundations.md#par19-timeloop), [CHE16](../references/foundations.md#che16-eyeriss), [GEN21](../references/foundations.md#gen21-gemmini), [JOU17](../references/foundations.md#jou17-production-tpu-analysis) | vocabulary and design obligations, never validation of Tusim |

## Evidence ladders

### Codec and sparsity reachability

```text
source present -> TU_OBJS member -> static archive member -> focused-tested
-> public C API reachable -> byte effect observed -> aggregate target included
```

Expected: `tu_int_quant.o`, `structured_2of4.o`, and `weight_compress.o` are archive members; `test-int-quant` and `test-sparsity` are in aggregate `make test`, while `test-compress` and the sweeps are standalone targets; `test_int8_sweep.c` is source-present with no Makefile target.

### Configuration effect

```text
declared -> parsed -> validated -> full-config consumer
-> runtime-conversion retention -> runtime consumer -> discriminating effect -> calibrated
```

Expected: `weight_compression` and `sparsity` fields parse and validate in `tu_config_t` and are consumed by `tu_compress_config_from_tu_config()` and `tu_sparsity_2of4_estimate_cycles()`, but **none** of them cross `tu_config_to_runtime()`; the runtime struct carries only PE/SRAM/counters/trace/verify/ICC fields. No selected field reaches external calibration.

### Cycle semantics

```text
byte effect (encoded size, round trip)
-> payload DMA cycles (size / bus width)
-> decoder cycles (elements per cycle, runs per cycle, bitmap width)
-> overlap handling (serial or overlapped flag)
-> measured hardware latency
```

Expected: the estimator returns deterministic integers under named config; the overlap flag changes the equation, not a queue or schedule; nothing is calibrated.

## Initial executable evidence plan

Canonical runner: `experiments/run_ch13_weight_stream_audit.sh`

Canonical run target: `experiments/runs/ch13-weight-streams/<date>-canonical/` (date decided at run time; the canonical id uses the `YYYYMMDD-ch13-canonical` convention).

Required gates before drafting:

1. source-audit script accepts only the exact pin and enforces exact hashes, predicates, and reachability checks (fail closed on drift);
2. source-audit mutation control returns nonzero when a tracked source hash is altered;
3. static archive build in a disposable extraction; binaries link `libtucmodel.a` and are rejected if they depend on a dynamic `libtucmodel`;
4. focused tests and mutation controls for at least one discriminating assertion per family;
5. config-parse/validation probes proving the exact field ladder including the `tu_config_to_runtime` drop;
6. byte-effect probes (encoded sizes, round-trip equality, corrupt-frame rejection, sparse payload bytes);
7. analytical-estimate probes (payload DMA cycles, decode cycles, overlap) with exact expected integers;
8. provenance before/after: Tusim detached and clean at the pin, book branch/HEAD unchanged, inputs byte-identical, zero remotes configured by the run (remote state asserted, not created);
9. inner retained manifest plus outer bundle manifest, finalization binding, and a retained pre-draft validation result;
10. failed-attempt runs are retained, not rewritten.

## Approval-relevant note for this session

The book repository now has a configured remote (`origin` → `git@github.com-tusim:nicefungo/tusim-book.git`) and an established publish pattern: `main` keeps the full history; the curated `book-publish` branch is pushed to `origin/main` after a milestone. This session will commit the chapter work on `main` and, after the milestone completes and validation passes, will show the exact publish commands and request approval before any push. The canonical runner still verifies it creates no remote and performs no push.
