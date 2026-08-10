# Chapter 19 canonical predraft audit — failed v4

- Run ID: `20260810-ch19-canonical-v4`
- Source pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Book input commit: `88b320d2225603fd7f7daec3d68cd4c7d1fcac1d`
- Status: **FAILED; retained as immutable historical evidence; not drafting authority.**

## Completed before failure

Every substantive source, focused-suite, sweep, bounded-probe, UBSan, focused-suite mutation, and executable semantic-mutation gate completed successfully. `artifacts/mutation-status.txt` and `REPORT.md` were produced, and the outer `SHA256SUMS` file was generated.

## Failure

The runner verified `INPUT_SHA256SUMS` from the run-directory root even though that manifest's members are relative to `inputs/`. Verification therefore reported thirteen missing paths and the runner exited before printing its canonical PASS marker.

A manual path-correct verification subsequently confirmed both manifests pass when the input manifest is checked from `inputs/`. This confirms the retained files are internally consistent, but it does not retroactively turn the failed runner invocation into drafting authority.

## Recovery boundary

The runner was corrected to verify the input manifest from its defining directory. The next attempt must use a new run ID from a clean committed input state. Do not overwrite or resume this directory.
