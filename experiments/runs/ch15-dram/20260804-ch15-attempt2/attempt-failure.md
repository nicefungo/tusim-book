# Chapter 15 canonical-audit attempt 2

The run passed every source, mutation, build, link, focused-test, probe, Tusim post-state, book post-state, and manifest-finalization gate. Predraft validation then failed because detailed probe lines were correctly retained in `ch15-probe.log`, while the validator incorrectly searched for them in the summary-only `transcript.log`. The validator was corrected to check each finding in its owning log. This directory is retained as a non-canonical validation failure.
