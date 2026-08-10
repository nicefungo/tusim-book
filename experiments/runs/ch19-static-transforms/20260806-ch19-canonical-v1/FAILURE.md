# Chapter 19 canonical predraft audit — failed v1

- Run ID: `20260806-ch19-canonical-v1`
- Source pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Book input commit: `fe0384490e801c26e4c1f94245dad2ea22f55ff6`
- Status: **FAILED; retained as immutable historical evidence; not drafting authority.**

## Completed before failure

- Source audit passed: 24 hashes, 149 predicates, 173 checks.
- Focused suites passed: scheduler 14/14; liveness 12/12.
- Scheduler sweep completed.
- Static-transform probe reported `CH19_PROBE SUMMARY failures=0`.
- Scheduler and liveness maximum-dimension UBSan fixtures both rejected signed integer overflow.
- Focused-suite assertion mutations were rejected: scheduler 13/14 and liveness 11/12.

## Failure

The runner stopped before executable semantic mutations because its Python source-replacement guard expected the scheduler validator identity expression to span different source lines. The pinned source places `dim1` and `flags` on one line, so the guard raised `AssertionError`.

The run did not produce semantic-mutation logs, `artifacts/mutation-status.txt`, `REPORT.md`, a completed outer manifest, or a terminal canonical PASS marker. It therefore cannot authorize skeptical review or manuscript drafting.

## Recovery boundary

The runner repair was made only after this run failed and is not part of this run's frozen inputs. The next attempt must use a new run ID from a clean committed input state. Do not overwrite or resume this directory.
