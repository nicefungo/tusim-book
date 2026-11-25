# Chapter 3 — Repository Tour and First Execution

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-3)

> **Edition boundary.** The first run uses the November 18 public source. The repository-tour observations are historical (first-edition pin `e918c80`).

## 3.1 Opening architecture question: what path did the experiment exercise?

Suppose a reader quotes the July 25, 2026 audit without naming its pin:

> “Tusim built successfully, the test passed, and the simulator reported 19 cycles.”

That sentence can conceal several different situations:

- a source file exists but is not compiled;
- an object is archived but no executable references it;
- an executable links a stale shared library;
- a unit test calls an internal helper that the public runtime never reaches;
- a frontend writes C text, but the text does not link;
- a target returns success after suppressing a failed command;
- a functional result is correct, while its printed counters come from incompatible accounting paths.

None of these possibilities makes the repository useless. They make the execution boundary important.

The architectural question for this chapter is therefore:

> **How do we establish a reproducible path from the pinned source snapshot to a named behavior, while preserving the distinctions among built, linked, reachable, tested, and validated?**

The answer is not “run every target.” A repository with many models, tests, generators, and experiments needs a staged inspection method. The useful result is a chain of evidence that can be repeated and challenged.

---

## 3.2 The execution ladder

A binary feature does not become real in one step. Use the following ladder.

| Level | Question | Typical evidence |
|---|---|---|
| **Present** | Does the source or declaration exist? | tracked file, symbol declaration |
| **Compiled** | Does the source compile under the selected flags? | object file, successful compile command |
| **Library member** | Is the object included in the named library? | `ar t`, shared-link command |
| **Linked** | Does the executable resolve the symbol from that library? | linker command, `readelf`, `nm` |
| **Reachable** | Can the public/config/runtime path invoke it? | call path, configured integration run |
| **Focused-tested** | Does a targeted test exercise its contract? | named test and assertions |
| **Aggregate-tested** | Is that test enforced by a broader target or CI gate? | dependency graph and nonzero failure propagation |
| **Validated** | Does behavior match an independent reference at the claimed boundary? | golden, RTL, FPGA, or silicon comparison |

These levels are cumulative only when evidence connects them. A source file can be compiled manually yet excluded from the normal library. A library member can remain unreachable. A focused test can pass while an aggregate target omits it. A target can print a linker failure and still return zero.

This ladder operationalizes Chapter 2's integration ledger. It also changes how to read a repository tour: directories tell you where to look, but build and execution evidence tell you what happened.

---

## 3.6 First execution through the public C API

A useful first program should be small enough to verify by inspection but broad enough to prove a public path. The preserved example uses:

```text
JSON file
   │
   ▼
tu_init_from_file
   │ parse, validate, convert, initialize
   ▼
tu_dma_load_w + tu_dma_load_a
   │
   ▼
tu_mma(2, 2, 3, ...)
   │
   ▼
tu_dma_store_o
   │
   ├──► exact functional check
   └──► tu_print_stats
```

The C driver and JSON fixture are the inputs for this example.

### 3.6.1 Workload and orientation

The API defines:

$$
O_{M\times N} \mathrel{+}= W_{M\times K} A_{K\times N}.
$$

The example uses:

$$
W = \begin{bmatrix}1&2&3\\4&5&6\end{bmatrix},\qquad
A = \begin{bmatrix}7&8\\9&10\\11&12\end{bmatrix}.
$$

Therefore:

$$
O = \begin{bmatrix}
1\cdot7+2\cdot9+3\cdot11 & 1\cdot8+2\cdot10+3\cdot12\\
4\cdot7+5\cdot9+6\cdot11 & 4\cdot8+5\cdot10+6\cdot12
\end{bmatrix}
= \begin{bmatrix}58&64\\139&154\end{bmatrix}.
$$

These integer values are exactly representable in FP16 inputs and FP32 accumulation, so the driver compares all four FP32 output words exactly.

### 3.6.2 Minimal JSON contract

The configuration requests a 4×4 PE array, output-stationary dataflow, and three 8 KiB SRAM regions:

```json
{
  "tu": {
    "compute": {
      "pe_array": {
        "rows": 4,
        "cols": 4,
        "dataflow": "output_stationary"
      }
    },
    "memory": {
      "sram": {
        "w_buffer_kb": 8,
        "a_buffer_kb": 8,
        "o_buffer_kb": 8
      }
    }
  }
}
```

The driver checks the initialized geometry and all three capacities. It also reads the active dataflow by name. The same mathematical output could come from either OS or WS; it would not, by itself, establish that the request reached the dispatcher.

### 3.6.3 Link and check the route

To try this example, use a fresh disposable extraction of the **simulator**, not the book checkout. From the repository root of this book, set `TUSIM_REPO` to a local simulator clone containing the named commit, then run the following in Bash on Linux. The extraction keeps build products away from both repositories. The shared-library check matters: a correct answer from another installed library would not test this pin.

```bash
set -euo pipefail
book="$PWD/editions/v2/examples"
run=$(mktemp -d)
git -C "${TUSIM_REPO:?set this to the simulator clone}" archive 7a094ff6c5527eff8e4318de676f0c0221c448b4 |
  tar --exclude=examples/gpt_block.onnx -xf - -C "$run"
cd "$run"
export LC_ALL=C LD_LIBRARY_PATH="$PWD"
unset MAKEFLAGS MFLAGS CFLAGS LDFLAGS CC
make -j2 all
cc -O2 -Wall -Wextra -std=c11 -I. "$book/first-run.c" -o first-run -L. -ltucmodel -lm
ldd ./first-run | grep -F "libtucmodel.so => $PWD/libtucmodel.so"
./first-run "$book/first-run.json"
make test-cmodel test-cmdq test-dma test-asm
```

The recorded smoke completions, in order, were **19/19**, **9/9**, **15/15** and **ASM identity PASS**. They are not an aggregate run. For one valid reduction tile OS charges `3 + ceil(3/4) = 4` model cycles. The driver brackets only `tu_mma`; neither DMA load nor the store belongs in that delta. Look for these three lines:

```text
requested dataflow = output_stationary; active dataflow = output_stationary
MMA-only model cycles = 4 (expected 4)
O = [[58, 64], [139, 154]]
```

The July 25, 2026 run (`e918c80`) instead reported active WS and 19 estimated cycles. The matrix did not change; the selected route did. See Chapter 4 for the paired configuration control.

[Next: Chapter 4 — Configuration as the Architecture Contract](../part-2-core/04-configuration-as-the-architecture-contract.md)
