# Chapter 5 ownership and lifecycle audit — 2026-07-25

## Scope and provenance

- Tusim source: `/home/zxy/Workplace/projects/tusim`
- pinned revision: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- source checkout remained read-only and clean
- execution root: `/tmp/tusim-ch05-audit-e918c80`, materialized with `git archive`
- probe source: `experiments/ch05_lifecycle_probe.c`
- environment: aarch64, GCC 11.4.0, GNU Make 4.3
- calibration: none; lifecycle observations are software behavior, not RTL/silicon timing

The archive initially contained six historically tracked object files. It was therefore cleaned before rebuilding.

## Exact build and focused-test sequence

```bash
SRC=/home/zxy/Workplace/projects/tusim
TMP=/tmp/tusim-ch05-audit-e918c80
mkdir -p "$TMP"
git -C "$SRC" archive e918c80b6fce833cd1fcae97730fa841c2176f25 | tar -x -C "$TMP"
cd "$TMP"
make clean
make -j2
for target in test-cmodel test-cmdq test-asm test-multicore test-errors; do
  make "$target"
done
cc -O2 -Wall -Wextra -std=c11 -I. -Itu_cmodel \
  -o /tmp/ch05_lifecycle_probe \
  /home/zxy/Workplace/books/tusim-book/experiments/ch05_lifecycle_probe.c \
  ./libtucmodel.a -lm
/tmp/ch05_lifecycle_probe >/tmp/ch05_probe.stdout 2>/tmp/ch05_probe.stderr
```

## Observed results

Clean static/shared build: exit 0. Pre-existing warnings included unused `comp_names`, unused `parse_opt_uint`, missing `label` initializers in the cmodel test, and unused variables in the multicore test.

Focused tests:

```text
test-cmodel:   19/19 pass
test-cmdq:      9/9 pass
test-asm:       identity smoke test pass
test-multicore: 16/16 pass
test-errors:    9/9 pass
```

Literal probe stdout (pointer values are run-specific):

```text
global_reinit: first_cmdq=0xaaab1e43d800 second_cmdq=0xaaab1e43e210 replaced=true initialized=true
async_queue: submit_rc=1 id=1 status=2 depth_after_completed=1
global_after_core_create: initialized=false cmdq=(nil)
core_ownership: separate_sram=true c1_state_bytes=2 c2_state_bytes=2 c1_embedded_dma_bytes=0 c2_embedded_dma_bytes=0 global_dma_delta=2/4
core_asm_lifecycle: rc=0 pe_before=4x8 pe_after=16x16 marker_after=0x00
void_error_path: last_error=30 accounted_bytes=131073 requested_bytes=131073
probe: PASS
```

The stderr stream contained normal initialization/destruction logs plus the intentional rejected transfer:

```text
MEM ERROR W-buf overflow: offset=0 size=131073 max=131072
TU_ERR_SRAM_OVERFLOW reported by check_sram_bounds
DMA load overflow: ch=0 off=0 size=131073/131072
TU_ERR_DMA_OVERFLOW reported by tu_dma_load
```

## Claim matrix

| Claim | Source evidence | Reproduced evidence | Counter-interpretation / safe scope |
|---|---|---|---|
| Legacy initialization owns process-global `g_tu`. | `tu_cmodel/tu_cmodel.c:31-109` | two successful initializations replace the exposed queue pointer | Pointer replacement alone does not measure leaked bytes; source shows the old queue is not destroyed. |
| Reinitialization destroys only three SRAM regions before zeroing `g_tu`. | `tu_cmodel/tu_cmodel.c:73-80`; queue destructor at `command_queue.c:175-184` | replacement queue observed | Dataflow registry deliberately preserves shared plugins; this does not justify omitting queue teardown. |
| There is no public legacy shutdown API. | `tu_cmodel/tu_cmodel.h:108-131`; repository search | source-only | Process exit still reclaims OS resources; the issue matters for embedding and repeated lifecycle tests. |
| Async queue completion and retirement accounting diverge. | `command_queue.c:326-359`; decrement is guarded by `cq->synchronous` although async mode calls `tick` | NOP status is COMPLETED while depth remains 1 | The focused test suite uses the synchronous default and does not exercise `sync` on this state. Calling `tu_cmdq_sync` would loop while count remains nonzero, so the probe does not invoke it. |
| Core SRAM allocations and wrapper counters are per-instance. | `tu_core.c:109-117,171-209` | distinct SRAM pointers and per-core `total_dma_bytes=2` | This is partial state isolation, not proof that every subsystem is instance-owned. |
| Core creation cannot coexist transparently with a live legacy `g_tu`. | `tu_core.c:23-36`; `tu_init_with_config` tears down live global SRAM | after two core creations, `g_tu.initialized=false` and `cmdq=NULL` | The API may be used in separate modes, but docs claim backward-compatible coexistence without stating this transition. |
| DMA execution is process-global, not owned by each core snapshot. | `dma_descriptor.c:23-43,564-573,685-725`; core getter returns `state.dma` at `tu_core.c:153-155` | embedded DMA counters remain zero while `g_tu_dma` rises after operations on two cores | SRAM contents remain separate. The negative claim is specifically about DMA engine state/accounting and concurrency. |
| Core ASM execution resets the selected core to global defaults. | `tu_core.c:121-133`; `tu_asm.c:200-208` | custom 4x8 core becomes 16x16 and SRAM marker becomes zero after empty program | A standalone `tu_run_asm` intentionally starts fresh; the surprising behavior is its reuse under the instance wrapper. |
| Error reporting is not equivalent to propagation. | void bounds helper/callers at `tu_cmodel.c:151-188`; legacy DMA return at `dma_descriptor.c:685-716` | rejected 131073-byte request records error 30 but increments wrapper byte count by 131073 | No out-of-bounds copy occurs in this path because the nested DMA function returns. Accounting and return-channel semantics remain wrong for callers. |
| The last-error facility is global despite a thread-safe header claim. | claim at `tu_status.h:122-126`; globals at `tu_status.c:55-60`; no TLS/mutex/atomic usage | source-proven only | Single-threaded callers are unaffected. Multi-threaded safety is not established by current tests. |
| ASM borrows host buffers and embedded weights only for the call. | `tu_cmodel.h:264-281`; `tu_asm.c:34-41,86-100,265-270` | focused ASM identity passes | Command-queue descriptors retain raw host pointers until execution; async users need a longer lifetime than ASM's synchronous call boundary. |

## Existing-gate interpretation

- `test-cmodel` establishes direct functional behavior and repeated reinitialization survival, but does not assert teardown completeness.
- `test-cmdq` passes because synchronous commands remain resident until capacity and the overflow test treats that saturation as expected. It does not run the async drain path.
- `test-multicore` proves SRAM separation and selected wrapper behavior. Its nominal SPMD test never calls `tu_cluster_spmd_execute`; it performs two direct `tu_core_mma` calls (`tests/test_multicore.c:563-604`).
- `test-errors` exercises framework mechanics, but its injection test explicitly acknowledges that injection did not fire and still passes (`tests/test_error_handling.c:183-210`). It does not test concurrent last-error state or caller-visible propagation through void public APIs.
- `test-errors` is not included in aggregate `make test` (`Makefile:524-528`), although it has a focused target at `Makefile:489-492`.

## Independent skeptical-review resolution

Three read-only reviewers returned 30+ candidate observations. Each material item was checked against pinned source; overlapping findings were consolidated as follows.

1. **Accepted — incomplete destruction:** global reinit loses the old command queue; `tu_core_init()` and `tu_core_destroy()` use raw `free(cmdq)` instead of `tu_cmdq_destroy()`, leaking nested arrays. Core reinit also frees `icc_buffer` without clearing it, creating a later double-free risk.
2. **Accepted — split state:** operational DMA is `g_tu_dma`, not `tu_state_t.dma`; dataflow plugin state, rounding/PRNG, subnormal mode, logging, status, and injection state are also process-global.
3. **Accepted — destructive layering:** core creation/reinit and core ASM interfere with legacy/global state; `g_default_core` is a second singleton and does not forward legacy calls.
4. **Accepted — queue contract drift:** generic submit returns a positive ID rather than documented zero; unknown/retired IDs are treated as completed rather than documented not-found; sync and async completed commands retain capacity; low-level faults through void APIs still become completed commands.
5. **Accepted — error hazards:** helper-only bounds returns permit MMA and low-level SRAM access to continue out of bounds; counters may record rejected work; `tu_status_str()` lacks a nonnegative check; claimed TLS is absent.
6. **Accepted — API/documentation drift:** invalid dataflow IDs normally fall back to WS instead of returning `-1`; cluster SPMD is serial; Doxygen excludes several implementation files; config documentation is manually emitted rather than introspected; warning-only documentation recipes are not gates.
7. **Accepted — gate gaps:** status and context tests are outside `make test` and CI; multicore is outside the CI runner; the nominal SPMD and injection tests do not exercise their named behavior.
8. **Qualified:** registry plugin objects are intentionally shared and stable, but mutable plugin counters mean that stable ownership does not imply per-core isolation.
9. **Qualified:** the rejected direct-DMA probe does not itself perform an out-of-bounds copy because the nested legacy DMA function returns; MMA and low-level SRAM paths remain source-proven unsafe because their callers continue after helper return.
10. **Rejected as closure evidence:** a review worker's first sanitizer run touched the source checkout. Its numerical result was not used until independently reproduced in a fresh archive.

### Independently reproduced leak evidence

A fresh `git archive` was built with AddressSanitizer/LeakSanitizer using:

```bash
ASAN_OPTIONS=detect_leaks=1:halt_on_error=0 make \
  CFLAGS='-O1 -g -Wall -Wextra -std=c11 -fPIC -fsanitize=address -fno-omit-frame-pointer' \
  LDFLAGS='-fsanitize=address -lm' test-cmodel
```

Observed summary:

```text
ERROR: LeakSanitizer: detected memory leaks
SUMMARY: AddressSanitizer: 23584 byte(s) leaked in 33 allocation(s).
```

The Make invocation returned zero despite the leak report, so process status alone is not a leak gate. Stack traces identify `tu_cmdq_create()` allocations reached through repeated `tu_init_with_config()`.

## Current conclusions

1. Tusim has three different ownership stories: process-global legacy state, swap-mediated core snapshots, and cluster-owned arrays of core pointers.
2. `tu_core_t` provides real SRAM/counter separation, but not a fully instance-pure execution engine; global DMA, registry, logging, status, and swap operations remain shared.
3. Public wrappers expose borrowed pointers and many `void` operations, so errors often become side-channel diagnostics rather than composable status returns.
4. Passing focused tests does not establish reentrant, concurrent, or teardown-complete behavior.
5. Chapter 5 must teach an ownership matrix and lifecycle state machine rather than repeating API names as guarantees.
