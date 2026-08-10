# Chapter 19 canonical predraft audit — failed v3

- Run ID: `20260810-ch19-canonical-v3`
- Source pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Book input commit: `b026957af7c105c8c4a81826fafe8c36c3b7b488`
- Status: **FAILED; retained as immutable historical evidence; not drafting authority.**

## Completed before failure

All structural, focused-suite, sweep, bounded-probe, UBSan, focused-suite mutation, and executable semantic-mutation programs completed. The scheduler identity mutation produced one expected probe failure and exited nonzero. The liveness opcode mutation produced two expected probe failures and exited nonzero.

## Failure

The runner's final grep expected the substring `CHECK_FAIL repeated implicit A`, but the probe's actual retained diagnostic was:

```text
CHECK_FAIL two W, repeated implicit A, O definitions
```

Because the expected words were not contiguous in the actual diagnostic, the guard failed after both semantic mutations had already behaved correctly. The run did not produce `artifacts/mutation-status.txt`, `REPORT.md`, a complete outer manifest, or a terminal canonical PASS marker.

## Recovery boundary

The guard was corrected to match the exact retained diagnostic only after this run failed. The next attempt must use a new run ID from a clean committed input state. Do not overwrite or resume this directory.
