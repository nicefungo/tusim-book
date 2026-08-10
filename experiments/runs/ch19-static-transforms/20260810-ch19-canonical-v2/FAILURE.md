# Chapter 19 canonical predraft audit — failed v2

- Run ID: `20260810-ch19-canonical-v2`
- Source pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Book input commit: `2a51d4f2f7ef6f48ab67c461c4df85d7ad2009fe`
- Status: **FAILED; retained as immutable historical evidence; not drafting authority.**

## Completed before failure

The structural audit, focused suites, scheduler sweep, bounded probe, both UBSan fixtures, and both focused-suite assertion mutations completed successfully, matching failed-v1 through log 10.

## Failure

The repaired scheduler identity mutation was generated successfully, but compiling its copied source failed because the semantic-mutation compile command omitted the implementation header directory. The copied file in temporary storage could not resolve `tu_scheduler.h`:

```text
fatal error: tu_scheduler.h: No such file or directory
```

The run stopped before semantic-mutation execution and did not produce a complete mutation status, report, outer manifest, or terminal canonical PASS marker. The runner was subsequently amended to add the exact ISA include directory to both copied-source mutation builds.

## Recovery boundary

The include-path repair postdates this run and is not part of its frozen inputs. The next attempt must use a new run ID from a clean committed input state. Do not overwrite or resume this directory.
