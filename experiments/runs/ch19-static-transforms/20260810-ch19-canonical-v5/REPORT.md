# Chapter 19 canonical predraft audit — v1

- Source pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Book input commit: `48fb45f2c1be3b7c292e25b581dd7fbcb12ca7bd`
- Status: **PASS as a predraft evidence run; manuscript drafting remains blocked pending skeptical review and a post-review seal.**

## Reproduced gates

- Structural source audit: 24 hashes, 149 predicates, 173 checks.
- Focused suites: scheduler 14/14; liveness 12/12; scheduler sweep reproduced.
- Static-transform probe: zero internal failures.
- UBSan: scheduler and liveness maximum-dimension fixtures both rejected signed overflow.
- Mutations: both focused-suite assertion mutations and both executable semantic mutations were rejected.
- Source checkout was detached, clean, and read-only. All builds used a disposable exact-pin archive.

## Authority boundary

This run authorizes only the recorded source, structural, and bounded-probe observations. It does not establish a composed compiler/runtime path or semantic equivalence of scheduler or allocator output. Chapter 11 retains queue/ISA lifecycle ownership.
