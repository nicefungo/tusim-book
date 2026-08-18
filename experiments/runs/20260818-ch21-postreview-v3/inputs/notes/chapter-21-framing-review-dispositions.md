# Chapter 21 framing review dispositions

- Date: 2026-08-18
- Scope: Chapter 21 framing gate and required predraft evidence plan
- Tusim source pin: `e918c80b6fce833cd1fcae97730fa841c2176f25`
- Final verdict: **PASS — BLOCK 0, MAJOR 0, MINOR 0, NIT 0**
- Manuscript status: **drafting remains blocked**

## Review sequence

### Initial skeptical review — REVISE

The review confirmed that the selected reader decision, four-candidate ranking, Chapter 17/20/21/22 ownership split, sensitivity plan, and negative compiler/runtime-composition boundary were sound. It reported five valid defects.

| Severity | Finding | Disposition |
|---|---|---|
| MAJOR | The report regex treated any `scripts/*.py` reference as an explicit sweep harness and therefore misclassified `scripts/gen_config.py`. | **Resolved.** The classifier now admits test C paths or `scripts/sweep_*.py`; the exact report set is 13, and the plan names configuration-generator provenance separately. |
| MAJOR | Source preservation was checked only on the green path; no failure-path control proved that `finally` still checked the pinned source after an early gate failure. | **Resolved.** The runner injects an early inventory-predicate failure, requires nonzero status and the intended diagnostic, and requires one pinned/detached/clean `SOURCE_STATE after` marker. The predraft plan requires analogous manifest- and validator-failure controls. |
| MINOR | Candidate 2 retained the stale 17/4 producer count after adjacent exploration harnesses expanded the inventory. | **Resolved.** Candidate 2 now states 19 linked-call versus four local-formula sources in the 23-source inventory. |
| MINOR | Source-to-target checks compared names/counts rather than the exact relation set. | **Resolved.** The runner binds the literal 22 source→target pairs, keeps manual INT8 as the exact no-rule singleton, and rejects a count-preserving benchmark/cascade prerequisite swap. |
| MINOR | Manifest closure did not define an exact bundle member set. | **Resolved.** E21.7 now names the literal required member classes, verifies both manifest layers, and rejects missing, extra, duplicate, or externally referenced mutable inputs. |

### Focused re-review — REVISE

The first amendments correctly fixed harness classification and added a real aspect-ratio source mutation, but the re-review found that failure-path source preservation, relation-exact membership, and exact manifest closure were still incomplete. Those findings produced the final amendments listed above.

### Final exact-current re-review — PASS

The final reviewer independently:

- re-ran `experiments/ch21_framing_recon.py` to a reviewer-owned disposable output;
- obtained exit status zero and byte identity with `notes/chapter-21-framing-reproduction.log`;
- verified the script hash bound in the log;
- verified the 22-pair relation set and count-preserving swap rejection;
- verified the aspect-ratio source mutation and injected failure-path source-state control;
- verified the expanded manifest/failure-control plan;
- verified the book remained on `main` with only the intended framing changes; and
- verified Tusim remained detached, clean, and pinned at `e918c80b6fce833cd1fcae97730fa841c2176f25`.

Final reviewed hashes before administrative gate-closure edits:

| Artifact | SHA-256 |
|---|---|
| `experiments/ch21_framing_recon.py` | `baccc087537a3ab558203e4a06321df2719b5583aecf2403ea99d79afa5d1e3e` |
| `notes/chapter-21-framing-reproduction.log` | `1d045370ac16b587c8914d843a538166e14668938f586518022240a00da58b4c` |
| `notes/chapter-21-framing-and-evidence-plan.md` | `af00f42aa8793cb39c82fa02c53fa2c68ca5ff737a74b164a9257bceffa5d25d` |

## Gate disposition

The independent skeptical framing-review requirement is closed. Chapter 21 may proceed to the predraft evidence work defined in E21.1–E21.8.

This does **not** authorize manuscript drafting. Drafting remains blocked until the source-and-claim ledger, fail-closed predraft audit and focused probes, skeptical predraft review, and post-review evidence seal are complete.
