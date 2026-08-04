# Chapter 15 canonical-audit attempt 1

The run reached and passed the source/hash gate, source mutation, static archive membership, static-link gates, focused `12/12`, focused-test mutation `11/12`, custom probe, and Tusim post-state check. It then failed before transcript finalization because the runner's book post-state check counted its own newly created untracked run directory as external book dirt. The runner was corrected to filter only the current run directory while continuing to reject every other change. This directory is retained as failed-run evidence and is not canonical.
