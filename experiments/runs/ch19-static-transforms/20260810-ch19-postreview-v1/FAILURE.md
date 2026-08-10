# Chapter 19 post-review audit — failed v1

- Run ID: `20260810-ch19-postreview-v1`
- Source pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Book input commit: `500537b3cc455eafdf8e10b9e986c563d4b86589`
- Status: **FAILED — retained, not drafting authority**

## Completed stages

The source audit and its pin/hash controls passed, exact-archive focused binaries ran, the 128-row opcode census completed with zero probe failures, both bounded arithmetic checks produced the expected diagnostics, and all five transform/test negative controls rejected.

## Failure

The validator source control inserted a top-level Python `assert`. Normal Python executed that statement before the validator could inspect its own AST, so the retained normal-control log contains an `AssertionError`; optimized Python removed the statement and the AST guard then rejected it as intended. The runner stopped before source after-inventory, report generation, manifests, finalization, or closure validation.

## Resolution

The next input revision places the test assertion inside an uncalled function. The statement remains present in the source AST under both normal and optimized Python without executing before the validator's own fail-closed check. A fresh run ID is required.
