# Chapter 20 framing review dispositions

- Date: 2026-08-16
- Source pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Scope: Chapter 20 framing, whole-tree verification-surface reconnaissance, and predraft evidence-gate requirements
- Current verdict: **CLOSED-PASS — no BLOCK, HIGH, or MEDIUM finding remains**
- Framing content commit: `9b9953094a5d65e526eeacf688694b6b52392c37`
- Drafting status: **blocked** pending the source/claim ledger, fail-closed predraft audit, skeptical predraft review, and post-review evidence seal

This is the durable disposition record. Delegated process transcripts are review provenance, not book authority. Every promoted finding below was reconciled against the current script, canonical reproduction, framing plan, pinned Tusim source, and final exact-current review.

## Durable reproduction

- Script: `experiments/ch20_framing_recon.py`
- Canonical output: `notes/chapter-20-framing-reproduction.log`
- Script SHA-256: `e3fa6f31d4d0c91608fbb94b86bfbd92f1d0aed1718ee6ab9e88182e8b47e229`
- Output SHA-256: `a6f32a27694b413de2a8b538d4e110fb3147f5f170f4ac4cfb4cbdd5b5cc6730`
- Completion marker: `CH20_FRAMING_RECON PASS`
- Command:

```bash
python3 experiments/ch20_framing_recon.py > notes/chapter-20-framing-reproduction.log 2>&1
```

An independent exact-current rerun exited `0`, produced 10,124 bytes, and compared byte-for-byte equal to the canonical log.

The first failed run and an earlier successful but superseded run are retained as:

- `notes/chapter-20-framing-reproduction-failed-v1.log`;
- `notes/chapter-20-framing-reproduction-superseded-v2.log`.

They are historical provenance, not current framing authority.

## Review rounds and dispositions

### R0 — broad skeptical correctness review (`deleg_bd241e55`)

Verdict: **REVISE**.

1. **Binding observation accepted failure and crash statuses.** Resolved first by requiring successful status and explicit success/failure markers, then superseded by a stronger direct discriminator: import the archived binding, execute a nonsymmetric `2×2` GEMM, independently specify `[[19,22],[43,50]]`, and gate shape plus residual.
2. **“Sweep/non-sweep” labels overclaimed semantic categories.** Resolved by describing only a mechanical filename-token partition: 43 filenames without `sweep`, 21 with it. The plan explicitly notes that `test_conv_pool_cascade.c` describes itself as a sweep despite lacking the token.
3. **Printed inventory observations were insufficiently fail-closed.** Resolved by exact count and membership predicates for the 64 source files, five source files lacking source-linked prerequisites, and 13 no-`sweep`-token aggregate omissions.

### R1 — intermediate focused reproducibility review (`deleg_caf9d7e2`)

Verdict on that intermediate snapshot: **PASS**. It verified script/log binding, successful status, source guards, exact inventory, and byte-identical reproduction. That snapshot was later superseded when broader review identified host-global temporary-path exposure; it is not the final authority.

### R2 — exact-current isolation review (`deleg_8e8e0cc0`)

Verdict: **REVISE**.

**Finding:** executing `test-quick`, `test-full`, the compiler path, CI runner, or `clean` could create, overwrite, execute, or delete fixed host-global `/tmp/test_asm` and `/tmp/gpt_block_tu*` paths even from a disposable source archive.

**Disposition:** resolved. The canonical program no longer invokes those targets or scripts. They remain static-only evidence. Every selected Make invocation is expanded with `make -n`; any expansion containing `/tmp/` or `rm -f /tmp` is rejected before execution. The selected live targets build and run only inside the disposable archive.

### R3 — focused fail-closed review (`deleg_77affdd5`)

Verdict: **REVISE**.

1. **CLI text-marker binding gate could accept duplicated PASS text without semantic completion.** Resolved by removing the CLI marker as the oracle and replacing it with the independently recomputed nonsymmetric GEMM discriminator.
2. **Failure paths returned before the source-after guard.** Resolved by an unconditional `finally` path. An exact inventory mutation exits `2`; an expected-binding-result mutation exits `3`; both print `SOURCE_STATE after` and omit the completion marker.

### R4 — final exact-current closure review (`deleg_e2587e0d`)

Verdict: **PASS — no BLOCK, HIGH, or MEDIUM findings remain**.

The reviewer independently confirmed:

- exact script and log hashes;
- exit `0` and byte-identical rerun;
- exactly one before and after source-state record on success;
- after-state records and absent completion marker on both mutations;
- independently recomputed nonsymmetric binding output with zero residual;
- exact inventory counts and membership sets;
- no selected or expanded Make recipe touching fixed host-global `/tmp` paths;
- no host-global fixed temporary artifact remaining;
- Tusim detached and clean at the exact pin;
- coherent Chapter 17/21/23 ownership boundaries;
- no Chapter 20 manuscript and no invented ONNX/compiler/runtime composition.

## Selected scope and retained boundaries

Chapter 20 is framed around **claim-to-evidence authorization and safe interpretation of green gates**. Given a unit, aggregate, CI, report, replay/debug, DPI, or binding result, the reader must decide the strongest claim that result authorizes and what remains unsupported.

Retained boundaries:

- Chapter 17 owns metric producer, interval, unit, and fidelity questions.
- Chapter 21 owns trustworthy sweep construction and methodology.
- Chapter 23 owns extension procedure.
- Chapter 20 does not infer an ONNX/compiler/runtime composition absent an executable bridge.
- Chapter 19 remains closed.
- No manuscript prose may be drafted from this framing record alone.

## Gate outcome and next work unit

The **framing gate is closed** at content commit `9b9953094a5d65e526eeacf688694b6b52392c37`. The **predraft evidence gate is not closed**. The next session must create the Chapter 20 source/claim ledger, fail-closed executable audit and focused discriminators, obtain skeptical predraft review, resolve its findings, and seal post-review evidence before drafting any manuscript prose.
