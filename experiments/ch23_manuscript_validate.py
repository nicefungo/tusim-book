#!/usr/bin/env python3
"""Optimization-safe manuscript and release validation for Chapter 23."""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "manuscript/part-3-practice/23-extending-tusim-without-breaking-its-contract.md"
PLAN = ROOT / "notes/chapter-23-framing-and-evidence-plan.md"
LEDGER = ROOT / "notes/chapter-23-source-claim-ledger.md"
RUN_REL = Path("results/ch23-predraft/20260819T084945Z-postreview")
RUN = ROOT / RUN_REL
SEAL = RUN / "seal.json"
PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
RETAINED_SHA = "598ec9ace364d75be687c255526ddb49c7158bd2043741b94a19806a33da1fb9"
TUSIM = Path("/home/zxy/Workplace/projects/tusim")
SNAPSHOT = ROOT / "notes/chapter-23-reviewed-snapshot.txt"
REVIEW_MODE = os.environ.get("CH23_MANUSCRIPT_REVIEW_MODE") == "1"
SELFTEST_CHILD = os.environ.get("CH23_VALIDATOR_SELFTEST_CHILD") == "1"

BIND_PATHS = {
    "manuscript_blob": "manuscript/part-3-practice/23-extending-tusim-without-breaking-its-contract.md",
    "validator_blob": "experiments/ch23_manuscript_validate.py",
    "runner_blob": "experiments/run_ch23_manuscript_validation.sh",
    "plan_blob": "notes/chapter-23-framing-and-evidence-plan.md",
    "ledger_blob": "notes/chapter-23-source-claim-ledger.md",
}

CARD_CLAIMS = (
    ("runtime configuration", ("C23-02", "C23-03")),
    ("dataflow plug-ins and registry ownership", ("C23-04", "C23-05", "C23-06")),
    ("ISA catalog and command-queue execution", ("C23-07", "C23-08", "C23-09")),
    ("a cycle-model source island", ("C23-10",)),
    ("a sweep as an extension surface", ("C23-17",)),
    ("Python binding promises", ("C23-11", "C23-12", "C23-13")),
    ("compiler/runtime/ONNX remains a negative boundary", ("C23-15", "C23-16")),
)

BOUNDARY_LINES = (
    "1. `C23-01`: extension readiness is a chapter-defined conjunction, not a repository guarantee or weighted maturity score.",
    "2. `C23-02`: runtime geometry propagation is partial/qualified until the layout-sensitive stack-smashing failure is root-caused and a repeated discriminating downstream observable is green.",
    "3. `C23-03`: parsed dataflow, pipeline-depth, and DMA-width values are omitted by the audited runtime conversion path; other direct or compile-time ingress paths remain separate.",
    "4. `C23-04`: direct WS/OS/RS selection is production-consumed, but global registry/core ownership and config-selection gaps bound the claim.",
    "5. `C23-05`: NLR is declared but unregistered; selection falls back to WS while returning success and is not NLR execution.",
    "6. `C23-06`: duplicate registry IDs retain the first pointer and free the new duplicate; capacity overflow silently returns without freeing the submitted pointer or reporting status.",
    "7. `C23-07`: 59 is the exact count of explicit assigned opcode members under the sealed syntactic definition; it is not an execution count.",
    "8. `C23-08`: the command queue has eight source dispatch cases; focused execution covers its bounded suite, not the expanded ISA catalog.",
    "9. `C23-09`: aliases, metadata, and adjacent static-analysis consumers do not prove queue/runtime execution or compiler composition.",
    "10. `C23-10`: cycle-model source and focused-test presence do not establish archive linkage, release ownership, or production reachability.",
    "11. `C23-11`: the Python identity GEMM smoke supports a bounded direct ctypes path only; it does not exercise constructor configuration, reports, packaging, or general numeric correctness.",
    "12. `C23-12`: Python stores `config_path` but does not pass it to a live C initializer at this pin.",
    "13. `C23-13`: Python performance and power report methods are advisory stubs, not live report bindings.",
    "14. `C23-14`: documentation is an audited claim source and cannot override contradictory executable behavior.",
    "15. `C23-15`: source models, a generator, and named Make targets do not establish a nontrivial compile-link-run-oracle path when statuses are suppressed and the far-boundary oracle is absent.",
    "16. `C23-16`: compiler/runtime/ONNX integration remains blocked until one contained nontrivial fixture fails closed through compile, link, run, and independent comparison.",
    "17. `C23-17`: the shipped dataflow sweep is standalone and fail-open on mismatch; its WS/OS/RS labels effectively execute WS/WS/WS and its local formulas are separate producers.",
)

KEY_MUTATIONS = {
    "34 exact-pin source, test, build, documentation, and model input hashes":
        "33 exact-pin source, test, build, documentation, and model input hashes",
    "exact 19-member non-symlink closure": "exact 18-member non-symlink closure",
    "The package passed 13 mutation families": "The package passed 12 mutation families",
    "two production files and three dispatcher call sites": "two production files and two dispatcher call sites",
    "59 explicit members and the queue eight dispatch cases": "59 explicit members and the queue nine dispatch cases",
    "compile=0 link=0 run=0 independent_oracle=0 full=0": "compile=1 link=1 run=1 independent_oracle=1 full=1",
    "compiler/runtime/ONNX remains a negative boundary": "compiler/runtime/ONNX is integrated",
}


# Exact reader-facing claim matrix. These are semantic restatements outside
# the binding register; each occurrence is frozen independently so an intact
# register row cannot mask a contradictory card, promotion trigger, summary,
# fidelity box, or answer-key statement.
CLAIM_MATRIX_LINES = (
    ("L31", '2. trace declaration/identity, ingress, retention with lifetime/ownership, production consumption/dispatch, observable effect, fail-closed verification, build/CI/package/release ownership, and behavior-matching documentation as eight separate edges;'),
    ("L143", '| runtime configuration | `tu_config_t`, JSON/default parser | `tu_config_to_runtime()`, `tu_runtime_config_t`, initialization | focused config run and downstream structure/effect | partial/qualified for geometry; no-op/fallback for selected runtime-conversion fields |'),
    ("L144", '| dataflow/plugin | enum, direct setter, config string | global registry pointer, core snapshot, dispatcher, vtable | output, active name, plug-in statistics, linked objects/tests | integrated for direct WS/OS/RS; no-op/fallback for config ingress and NLR/unknown selection |'),
    ("L145", '| ISA/command queue | explicit opcode enum, aliases, metadata | submitted command descriptor and `execute_command()` | eight source dispatch cases, queue status/tests | partial/qualified bounded queue; tested subset only; unsupported aliases fault rather than fall back |'),
    ("L146", '| cycle-model module | source/header/API | isolated caller-created object | focused source exists; no archive member, Make rule, or production caller | standalone source island |'),
    ("L147", '| dataflow sweep | fixed workload/seed and WS/OS/RS labels | core-wrapper calls plus local formulas | printed rows, dedicated target, exploration prose | standalone and fail-open; effective WS/WS/WS routes |'),
    ("L148", '| Python binding | Python constructor and ctypes signatures | Python `_config_path`, C library handle, direct operations | identity GEMM, stub reports, no Make/CI owner | standalone bounded direct ctypes route; no-op/fallback constructor config/report promises; supported-package promise partial/qualified |'),
    ("L149", '| compiler/runtime/ONNX | two contained models and generator | generated C and host fallbacks | suppressed build/run statuses; no far-boundary oracle | standalone generator/model components; no-op/fallback `test-full` failure handling; positive composition claim remains ledger-blocked |'),
    ("L188", '| Current classification | **Partial/qualified** for geometry; **no-op/fallback** at runtime conversion for the audited dataflow, pipeline-depth, and DMA-width requests. |'),
    ("L192", '| Stop evidence | Canonical `test-config` aborts with stack smashing; other independent layouts have passed. Dataflow, pipeline depth, and DMA width are parsed but omitted by conversion. |'),
    ("L194", '| Promotion trigger | In fresh processes, run literal JSON A/B configs `{"tu":{"compute":{"pe_array":{"rows":8,"cols":16}}}}` and `{"tu":{"compute":{"pe_array":{"rows":16,"cols":16}}}}` on `M×N×K=17×16×16`, with zero-based `A[i,k]=((7i+3k+1) mod 11)-5` and `B[k,j]=((5k+2j+3) mod 13)-6`; require active geometries `8×16` and `16×16`, exact tile counts 3 and 2, outputs equal to an independent integer-loop oracle, and nonzero status if either geometry or tile receipt differs. |'),
    ("L215", '| Current classification | **Integrated** for direct WS/OS/RS; **no-op/fallback** for config ingress and NLR/unknown selection, whose active route becomes WS while status remains success. |'),
    ("L219", '| Stop evidence | Config conversion drops the mode; core snapshots can overwrite global selection; unregistered IDs fall back to WS while returning success. |'),
    ("L221", '| Promotion trigger | Run three fresh `17×13×11` cores over zero-based `A[i,k]=((7i+3k+1) mod 11)-5`, `B[k,j]=((5k+2j+3) mod 13)-6`: direct WS baseline, direct OS, and literal JSON `{"tu":{"compute":{"pe_array":{"rows":16,"cols":16,"dataflow":"output_stationary"}}}}`; require active names `weight_stationary/output_stationary/output_stationary`, both OS vtable pointers equal `tu_dataflow_lookup(OS)` and differ from `tu_dataflow_lookup(WS)`, all outputs equal an independent integer-loop oracle, and an NLR request or any identity/vtable mismatch to return nonzero. |'),
    ("L245", '| Current classification | **Partial/qualified** for bounded queue execution: eight source cases exist, but complete per-case behavioral evidence does not. Unsupported aliases such as pool are rejected/faulted (`tu_cmdq_wait()=-3`), not fallback execution. |'),
    ("L249", '| Stop evidence | Aliases and metadata do not create queue cases. Unknown commands fault; scheduler/liveness are adjacent analysis consumers, not composed execution. |'),
    ("L251", '| Promotion trigger | First reconcile `tu_cmdq_submit()` to the explicit assigned-positive-ID contract implemented at this pin. Add `tu_cmd_pool_desc_t {input_offset,output_offset,input_h,input_w,channels,kernel_h,kernel_w,stride_h,stride_w,pool_type}` and a retained `pool` union member; on a fresh synchronous queue submit A-SRAM offset 0→O-SRAM offset 0, `3×4×1`, kernel `2×2`, stride `1×1`, `TU_POOL_MAX`, and `[[1,7,2,0],[3,4,9,5],[-1,6,8,2]]`. Require submit return = captured ID = 1, retained fields byte-equal the descriptor, pool-dispatch count 1, `wait(captured,0)=0`, captured status `TU_CMD_COMPLETED`, and output `[[7,9,9],[6,9,9]]`; replacing captured ID with reserved 0, removing retention/handler, or using `kernel_h=4>input_h=3` must make the governed process nonzero even if the underlying not-found wait/status APIs report completion. |'),
    ("L272", '| Current classification | Standalone source island. |'),
    ("L276", '| Stop evidence | The module is absent from `TU_OBJS`, has no Make rule, and exhaustive tracked C/H scanning finds no external non-test `tu_cycle_*` caller. |'),
    ("L278", '| Promotion trigger | Link one production-owned caller to a tracker of capacity 4; call `tu_cycle_pipeline_issue()` at cycle 0 first with tile `(0,16,0,16,0,16)`, sources `{100,200}`, destination `{300}`, then with tile `(1,16,1,16,1,16)`, sources `{300,400}`, destination `{500}`; require stalls `0,96`, `total_issues=2`, `total_stall_cycles=96`, utilization `0.5`, reset to all zeros, and nonzero test status when the second source is mutated from 300 to 301 and the required 96-cycle RAW receipt disappears. |'),
    ("L291", '| Current classification | Standalone non-aggregate harness with fail-open mismatch semantics. |'),
    ("L295", '| Stop evidence | Core snapshot restoration makes the three labeled executions effectively WS/WS/WS; local formulas are separate producers; mismatch text does not change exit status. |'),
    ("L297", '| Promotion trigger | Run fresh WS, OS, and RS cores at default `16×16` on `128×128×256`. Generate row-major W then A with separate unsigned-32 states seeded 42 and 99: emit the post-transition state after `x^=x<<13; x^=x>>17; x^=x<<5`, masking to 32 bits after each left shift; map `q=(x&2047)-1024` to exact binary16 `q/1024` using round-to-nearest, ties-to-even and store little-endian. The first W/A words are `00ad4528,a90a34ac,1c67af03,d970c3c0` / `01806cc5,8f0193e9,12e147b7,78e0ed3c`; require W/A byte hashes `0b322defeb00b00648e0e1523df10566b5835684bdadc47b332d1a3130dce359` / `9efef3fcb57e9f8a888f8fe40c74205c1266a43d0cdf9567d1642749220a11bc`. Require active names `weight_stationary/output_stationary/row_stationary`, selected vtable pointers equal their lookups and pairwise differ, every output to match an independent exact-integer-sum oracle rounded once to little-endian binary32 whose hash is `164c2afd507482c03584910fcabe08d32b99ca920561dfc89dc7baa013c8e0fe`, retained raw rows, and nonzero status for any WS restoration or hash/identity/oracle mismatch. |'),
    ("L312", '| Current classification | **Standalone** for the bounded direct ctypes route; constructor config/report promises are **no-op/fallback**; the supported-package promise is **partial/qualified**. |'),
    ("L316", '| Stop evidence | `config_path` is stored only in Python and constructor calls `tu_init()`; performance and power report methods return advisory stub strings; no Make/CI owner exists. |'),
    ("L318", '| Promotion trigger | Install the package in a clean environment and construct two fresh instances with literal JSON F `{"tu":{"compute":{"pe_array":{"rows":8,"cols":16}},"performance":{"counters":{"enabled":false}}}}` and T `{"tu":{"compute":{"pe_array":{"rows":8,"cols":16}},"performance":{"counters":{"enabled":true}}}}`. Multiply `[[1,2,3],[4,5,6]]` by `[[7,8],[9,10],[11,12]]` once per instance; require both active geometries `8×16` and output `[[58,64],[139,154]]` from an independent Python-loop oracle. F must report `enabled=false` and zero counter/power deltas matching a direct C snapshot; T must report `enabled=true`, `total_macs=12`, `total_flops=24`, `op_mma_fp16=1`, power fields in pJ, and `energy_total_pj` equal to the component sum, all field-for-field equal to its direct C snapshot. A dropped/misnested counter field, old stub string, report/C mismatch, or numeric mismatch must return nonzero. |'),
    ("L333", '| Current classification | Generator/model components are **standalone**; governed `test-full` failure handling is **no-op/fallback**; the positive composition claim remains ledger-`block`. |'),
    ("L337", '| Stop evidence | `test-full` suppresses generated build/run failures with `|| true`; no contained far-boundary oracle exists; the active compiler smoke is blocked by missing NumPy. |'),
    ("L339", '| Promotion trigger | Add one contained `ch23_linear_1x4.onnx` fixture computing `[2,-1,3,4] × [[1,-1],[-2,4],[3,0],[0.5,2]] = [15,2]`; require generated TU work rather than host fallback, unsuppressed compile/link/run statuses, exact independent-oracle output, retained logs, and nonzero status when the TU operation is removed or the output is changed. |'),
    ("L229", 'Ownership is equally specific. The registry has eight slots. Duplicate IDs keep the first pointer and free the new duplicate. Capacity overflow returns silently without freeing the submitted pointer or reporting status. Those are two different lifetime outcomes. Summarizing both as a generic “replacement hazard” would hide which object remains live and who leaks on overflow.'),
    ("L397", '- source state is detached and tracked-clean at the exact pin before and after;'),
    ("L398", '- runtime geometry reaches runtime, while dataflow, pipeline, and DMA width are parsed then dropped;'),
    ("L399", '- four dataflow IDs are declared and three are linked/registered/consumed;'),
    ("L400", '- production dispatch enters from two files and three call sites;'),
    ("L401", '- unregistered selection falls back to WS with success;'),
    ("L402", '- the ISA has 59 explicit members and the queue eight dispatch cases;'),
    ("L403", '- the cycle model has no library membership, Make rule, production reachability, or external non-test call file;'),
    ("L404", "- the sweep's labeled routes are WS/OS/RS but effective routes are WS/WS/WS;"),
    ("L405", '- Python stores but does not consume config path and leaves two report stubs;'),
    ("L406", '- compiler promotion remains `compile=0 link=0 run=0 independent_oracle=0 full=0`;'),
    ("L407", '- the canonical config focus is red and layout-sensitive, while dataflow, ISA, command queue, sweep process, and binding smoke return green within their stated scopes.'),
    ("L447", '> **Established:** a reviewed eight-edge extension contract; seven exact-pin whole-path families; 34 source, test, build, documentation, and model input hashes; direct WS/OS/RS production consumption; exact registry duplicate and overflow behavior; 59 explicit ISA members versus eight queue cases; source-island, sweep, binding, and compiler boundaries; an exact 19-member non-symlink postreview closure; normal/optimized verification; and 13 mutation families.'),
    ("L449", '> **Qualified:** runtime geometry propagation reaches initialization, but canonical verification aborts with a layout-sensitive stack-smashing result whose root cause remains open; direct dataflow selection works for WS/OS/RS, but JSON selection does not; Python direct operations work for a bounded identity smoke, but constructor configuration, reports, packaging, and broad numeric correctness are not established.'),
    ("L451", '> **Not established:** NLR execution; an open dynamic plug-in ABI; execution of every declared ISA opcode; scheduler/liveness-to-queue composition; cycle-model production integration; three effective routes in the shipped dataflow sweep; live Python config/report support; or compiler/runtime/ONNX composition.'),
    ("L546", 'An extension is a promise, not an artifact. The promise must name its required declaration/identity, ingress, retention with lifetime/ownership, production consumer, observable effect, fail-closed verification, build/release ownership, and behavior-matching documentation. Integration is conjunctive, so the weakest missing edge determines the strongest safe claim.'),
    ("L548", "Tusim's runtime geometry reaches initialization but remains partial/qualified because canonical verification is layout-sensitive and red. Parsed dataflow, pipeline-depth, and DMA-width settings stop at conversion. Direct WS/OS/RS selection reaches production consumers, while NLR and unknown IDs fall back to WS with success."),
    ("L550", 'Registry semantics must be exact: duplicates keep the first pointer and free the new one; overflow silently returns without freeing the submitted pointer or reporting status. These behaviors constrain any claim of an open dynamic ABI.'),
    ("L552", 'The 59-member explicit ISA catalog and eight-case command queue are different surfaces. Scheduler and liveness are adjacent analysis consumers, not an execution bridge. The cycle model is a standalone source island. The dataflow sweep is owned by a dedicated target but effectively routes WS/WS/WS and fails open on mismatches. The Python binding has a bounded direct path but stores rather than consumes `config_path` and returns report stubs.'),
    ("L554", 'Finally, no compiler/runtime/ONNX composition is established. Promotion requires one contained nontrivial fixture whose compile, link, run, and independent comparison all fail closed. Until then, source presence, documentation, and suppressed targets remain evidence of intent and gaps—not integration.'),
    ("L576", '1. A score permits strong documentation or test count to compensate for a missing consumer, correctness, ownership, or status edge; a conjunction does not.'),
    ("L577", '2. Partial/qualified has a real portion of the promised path but a missing/red required edge. Standalone has an intentionally isolated executable or analytical contract without the broader production reachability claim.'),
    ("L578", '3. The canonical focused run aborts with stack smashing and independent layouts disagree; root cause and a repeated discriminating downstream matrix are still missing.'),
    ("L579", '4. The full config retains the parsed value, but `tu_config_to_runtime()` omits it and initialization therefore does not consume that ingress.'),
    ("L580", '5. It establishes linked registration and direct production dispatch for three implementations. It does not establish JSON selection, per-core/global lifecycle coherence, NLR, physical movement, or calibration.'),
    ("L581", '6. A duplicate keeps the first pointer and frees the new duplicate. Overflow returns silently without freeing the submitted pointer or returning failure status.'),
    ("L582", '7. Declarations and metadata do not manufacture operand retention, dispatch cases, semantic effects, negative behavior, or differential tests.'),
    ("L583", '8. They consume adjacent representations for analysis but no source path composes their output into queue/runtime execution.'),
    ("L584", '9. It is absent from `TU_OBJS`, has no Make rule, and has no external non-test caller, despite source/header/focused-test presence.'),
    ("L585", '10. Its labeled core routes are effectively WS/WS/WS, and mismatch text does not change process status.'),
    ("L586", '11. It proves a bounded ctypes/library/direct-operation route for one easy fixture. It does not prove config consumption, live reports, packaging, broad ABI compatibility, or general numeric correctness.'),
    ("L587", '12. Missing NumPy affects the compiler import path; the direct binding smoke is a different route and ran independently.'),
    ("L588", '13. Unsuppressed compile, generated-code link, execution, and independent far-boundary output comparison for one contained nontrivial fixture.'),
    ("L589", '14. Documentation can state intended behavior and expose divergence, but it does not execute, retain state, produce an observable, or propagate status.'),
    ("L590", '15. Set a nondefault or malformed case that distinguishes the intended mechanism, observe the exact consumer/effect, and require the specific wrong path to return nonzero.'),
)

TARGETED_REVIEW_MUTATIONS = {
    "The registry has eight slots.": "The registry has nine slots.",
    "Capacity overflow returns silently without freeing the submitted pointer or reporting status.":
        "Capacity overflow returns silently after freeing the submitted pointer, without reporting status.",
    "6. A duplicate keeps the first pointer and frees the new duplicate. Overflow returns silently without freeing the submitted pointer or returning failure status.":
        "6. A duplicate frees the first pointer and keeps the new duplicate. Overflow returns silently without freeing the submitted pointer or returning failure status.",
    "Selecting NLR—or another unregistered ID—falls back to WS and returns success.":
        "Selecting NLR—or another unregistered ID—falls back to OS and returns success.",
    "WS, OS, and RS are linked and registered; direct selection reaches `tu_mma()` and attention through `tu_dataflow_execute_mma()` and the selected vtable.":
        "NLR, WS, OS, and RS are linked and registered; direct selection reaches `tu_mma()` and attention through `tu_dataflow_execute_mma()` and the selected vtable.",
}

# Exact occurrence/location inventory for the complete manuscript. Semantic
# tables provide readable gates for core claims; these per-line digests make
# every remaining body paragraph, card field, failure mode, question, answer,
# and exercise fail closed with a precise source-line diagnostic.
MANUSCRIPT_LINE_SHA256 = (
    "c0414dc6a20c058f88ca32cf343c983dbecc0ede4012998f2c067bb8a27ffdf3",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "d6a4a6179b3a1a37cf2b7886cc04e060456a89e88f543a7b157f834703522a6c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "b9fb7f411c010c561e672cabc1cc6544ebc20b33834fb8e9da0ccd2a5068490f",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "8f3ae4e48a32f161569e6512b9d91e89197960a2b0b9945d6581abee433e5c15",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "f0c2a02c6c7b92c815ea297b96e22cab629284b6a2ba409c3cfce32fcf1a4749",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "211ff31505a6f33dd546d8fb451dd179620c984442eb86983e0dd534c609404e",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "b4a313791c1fbca2c1410d1d5b1190af4087723ec1b6c1c4ba776298d6dd6228",
    "2e2b99dcb2d7447b304f875c365b33d571744e94cfa4aecf89700cd21cae023b",
    "f142fffb4b61d8ed2fa1c6adc93174113de78bf02bae94f9fa3044f3e7055e98",
    "554022e3f5d3751f2d4911e4725e975edf2050b6e085691da7eb7d1e92028c85",
    "4b9b3190efa05c96e367c8f94c71ea3e48b5e7405c61a95acb1cc991cc358863",
    "3052f07a6ea8e4af37878045ec6fa01ea028fed543e952040e56d065cf310b48",
    "0f175576f569a988b1c61b506e759a0c602f62ce52cd010cd94bef822fbef0bf",
    "e5e15e858ba5c0fb2fc3a7912c09d3a98683e9a544c7fda85db57d4f63fb8d03",
    "1afefe3012fdb4258ac7e1e3898529089fbf2d73ddba837ae989e26c734cf491",
    "f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "4c4459e03d3beb2fd5201ed7260f1865b75b907e1ce208c407553f00cbb49741",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "1a53f4c3fa61c3a797ca43ab583b3c36a41683372323060a66cbc7dca466fe16",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "9f797af7a02b731dcf734db873f65a4c6ebb9ca043580730e69a3100ffd26682",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "d7fd80fb2a42db1e2887a29bcc775bd565706e37769e5c68d15f2332c9442cca",
    "2e69980cbfba0e2f287ec8c950d45fe245c13b6fc5a7c2b8b5df3a4ab7399f1a",
    "cbb1bd5c26fe4ed5fa83bb752a131161bc16e7416cc2515630c80ee1e055e1d3",
    "d0dcd9d52c4236c72537e80a085a0f5ab7d81ba6f4a85d9e531513c35e0c04e2",
    "98391bdc2e059d1c031ee2633e6bb6272c129c15dfd142784ff39df0ec1366ba",
    "44c055e4e4ad9aeb6ff634669b0ddeb9f176ab3c17533c3d76c6e92139c510d6",
    "fc8851aefa08932c8e28aee1524f1377865d1e4efc0ba456edf1cd37fcfa7e57",
    "4d4d4f51267f9e1e96d2aa15e251b9d2dbeedcbf97b601fc2c2589d9743aaec0",
    "fdbcb8acf2de1d5d942a4fa5d9ce7065435437bbd3f03f1f1a12e3a24dfdbba0",
    "38673eda471cd8b3cac10845e9142b1b170036fbe04452cf8591ae3a8cfb1559",
    "56482416d414228a542ee15f6083547b0718763b6086c70405d2e3d16c75bcec",
    "10c1ca9ab8d5e774098a753fc3ca3e9b6eb99c692070e38de8056490993e0a23",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "1c00715e8d02520119bc656a56b764bae1e9333d3c3a81ca6950f382b709e995",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "b4a313791c1fbca2c1410d1d5b1190af4087723ec1b6c1c4ba776298d6dd6228",
    "ba8fd9f2f168fc12357bb9c4cdefe0bd15a4b3bd56a1cca0c527bd5014e354a8",
    "29108228397a648901df4383dea10a996459a702dc0a148f1c8fe6b5b5a04322",
    "a43614a5e54d4313b229141c378ce4f59b9b01f81d5641b392e44b0cee1c9723",
    "56bb762e08f3201e7633d53f7cebd2e100546e14cd34682698e027c6e2b4f734",
    "a42400376f4e8272c6f61bd8e4e56b113c25657e5703ab5ac106cb417e4a2140",
    "c0ff242c260f823b78b2c5a353c0ad612b91d12e728b59752ee209d9d193ab1a",
    "7e214791ec740e5755b41ea896384f576d90256b978dbb5ba7564b49055290a6",
    "2adbe22f50dd716148abdb6912b5da717768eea9e8214832e719c237778558d4",
    "7a2618b39f38189521c1287111d9d8d0ef6cd99b3611b1b768c7f5736f371ac9",
    "f7f78e25b3d833c0a36a4921524a142b72eb5c87e5977ec1c49c2d05a5a924f8",
    "aaa30b602b0e40da096b546e728802110e1021baa9ae258be4fbae6d9a87b60f",
    "f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "34483f151fc66584f2cc2240026a76b05ed827fae8b2b38306e7ad90bf32f39c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a524fe4b32dafe6698c3fab8d241f5a7d972db33b1b8c78fad0e022978763b15",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "8945a1831a79db33f62b2e273fc5e8d45b5823de650824422a44598c78160524",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "db8c4c01e4a52fcc1569cbaef67ff81d3d46efabe88905b1750cd82e3f28fece",
    "08c85ca1758d01d368be49dea045cb86ef2bf5f2c65db9e8134c5bd82d34edf4",
    "b2cfb9075f8f4f6c1e8e888167b848c9a61e017b14678b2ee92db57f0ba47da1",
    "eef5c78aec8afde2fa55061a15fd6fb315b806e3abd5b6e7320bfe25cdc41a6f",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "878c0a34a2bd74422a637dae539a2a6c092245b3f5a74bf2e2ef751776e677a7",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "4f0424a6d3192577d0655ee86ad7d98b22c5e853f2c4512516434b189ebebec1",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "9c3fd1222fdbcb73e6015a5b08f3978a3c8c81c3a3b6f7a61b88811e96bd8a1b",
    "0c81c7c7cf3f59d17149e151ade8acd2832bb000f8ee894690dc05ce69ffa66e",
    "d31da9ac2ba0d7adc32e67017bd761218c4b92cc99cec6e0cc483df90fffa37d",
    "e0756aeb94068d18eadcca982089178fb2f973838a3b5442c38b2bdbce000f8a",
    "2c1909c16e13d259e2de15fb5a380677e0a5d8acdb6910952f5a4510f56c441e",
    "93ada9087d5aab3988c4b29a217f877b42abd4119945e23e7e7c61a1879da837",
    "29916bf5470857026fb99d2db0b463dde0d01b4e8ec14a73f630d4988b12f030",
    "1b07bf141223aef04608f19f1a70fe9ee2ee77d8ad5fe94fde4a04c35836ae3b",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "d97a393cb1b0891fab60f58ccce345175f06fad00fcf1289aee44b3a1ea7fb17",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "cb3f91d54eee30e53e35b2b99905f70f169ed549fd78909d3dac2defc9ed8d3b",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "4d4734d1b425fa0d7d6e2529595e97f2e29f3e97d995c6229f041b3715ee0922",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "b58480196c3c2a738751b1920f25c7b68e98d9ee776231a3857c1cb3a0be9468",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "fd61a9009da5acfe604e20ea26dbbd0feba7d2ed6126c5321cfbbe81f4f6da5c",
    "39f5185bc5780450994f11f91090fa62cdd8b752ba7fe133e66487ecc30280b5",
    "9d8916a98ef5ed60738b85dd4fbb652be6cc1479a86170075b68d366f0f625c0",
    "d9e0c754af99f52a25e835c03e3dd9f05c6cab94180543934c6132a96acb2a8b",
    "9865a41c42f0c996f1c84972f8b66147c751cfe0b42727621208a5d78019e8fa",
    "b67c78670196805943acb593d3ae8efb68e661f57a1413279aced1b4ff20b008",
    "ca9e8d79eb00be1f6111b0f3a8cae8749b4c780449afb8034c7f949deb9e9fa8",
    "b1d89dea8bfeace526b3e4da1a1e3222396b90dbdda4fc60c8f8ca1642ba7b01",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "4f062458579a7c2939ac7bb5b040f2916e3fe3419c9005ce112a7dda931bb988",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "8b1f60fade5d66c6281a3b1d4c1f7c45e9a22ef0ffd1177ddcb1b0e6e4ab7f8e",
    "7b2efbd4e6534b60624bcdb69e0de756224b2d10ca08f540e885bee9dbb13f6f",
    "c9d6fcd1d11b34248eaac74a6b1e0e733115ce9d55f05ec4bbad2e29618d1ff6",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "42d76db9a8e601da7481e9318ad2cf7eca1a855efcaa68daf4a1e03c9890617d",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "fd64c8a6f2d3c35c1ede9547f1ebd32881bd24e7d6cc48a96ff6e4057a65707b",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "2043810a47d5b7cd73acb7382066051fcbd92047855dd567985fe741d274fe5b",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "e86ece9bd43403799f7a1df3b8e429669606a3e0e05e6ec72a8f4e926aa3e0dd",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "87c5171c8db4825c98c346511adb7a50067233e80a775f8160f895543643e9b5",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "3819d630cd448cf133d305393dde3c0fcde1374673ed0aedc53dc9fd9b2eac1a",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "3ade83f864db4182fd7d9b2471a1b824a6a91ce7e56ea5af4ab3d156f2270b4f",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "b09e722a6dcb8e5fca8a3b92a43c072d6c6d8a74d7f2ff89a87aeae941ab4ff9",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "e62793c8d3d01993b72231a5a30f1b9a2b04a8434e5a0be6c494d680f4133545",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "d3ec959849363426da7aa1409259b7fe612c321c7c1cafef14ea351809222fb2",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "e5b2a16b23638459c65cc49df122155bad4ac81461bcb9ba9fb6bcbbfa3d4892",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "8ee1145da2177ad00b56a06edb1040bca27b8e2791a76d5b707a40c4b7e8fb0d",
    "f842bee6d81feb748e7ef2a2ae2061338044dbac97e5b35848ffc083de2eaf87",
    "259df1b54150021d18a5a286aecc72119677488fd9251f0430c5482385fedf63",
    "d51c64088fb9986b30a91db4361eb73b3598829e3d988e00677ef558033effc2",
    "c53b3d6b29ff5339d57d80a5a18d674e101749564143e5476c4e3c68cd4b7646",
    "f9744340fb950f02c0986feec7f76a401073ebba0d7d9ac3940b5a9364f79c35",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "22ef6a1d4fdab9d49da5a0a870179e068756e33b67ebea5b61a63711ba56e5e6",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "0313e38d3979b94efa72030576703b91fe324ef62acdb472558dc0e0c10460ab",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "81e09d38a42f19846650eaf5b1dde6eadc92542ee1e79ede8424f591a22ca0a7",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "4ec48077c7146efee33a894c70ae9091425c61bb8e330ce2ea4ed40718c65f42",
    "12af00ef4beed04e98324a76d971f94419a92b77311cf21629020e3449b8f457",
    "9e6fe943b0f22d383327f5d15f956a4cdf0877a6acc9c858f544e1ee2355dd59",
    "5fafea9099ab2584dcc0c53d84fb1c1455ef0337485340dce9e5366be9c5dafa",
    "dd3234dfd2fc2b5fea65b9116b83837dd4388fcd43df16086b029364e494aa1f",
    "d3ad86f27966cf0b2f4efbd5d4eeb98c249efc2a4edd1a287b5d771763c9bad0",
    "c2c3edfc7ad3dd9cae1ee0399b825908defb9cc85f07bb4ebe25038d8d1366a0",
    "3e6c5f51dd8d6d224435ae1f818fd97cf3b00c53dd05163048f456bca83a99b6",
    "2496c0ac8269764c7e798e3de27e036e1d9fed641081a717b876ad5095c6fe9c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "4df524629e100506b4e4a4e6101a7d184fc2c7422033e7d0118487be15bf222a",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "9d2fc7cf9c69f88a54eaee1c8ebb84c32a5a85302c3ee32e27b2b15950e48fe9",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "83c6042cfaadea034977e8a955d6c6f00be2702d95ccafedc4a1d20b0485c242",
    "124781f0dad08f4000cc9e2533d5f8d0cea4771fc7678a18c898affde7caf70b",
    "5082c5207856b5d67ac5bf7901eca51c2155ff9167a8b2d9f02cfb228e39ce3f",
    "f3a98e1c48f1a6b0553d73c6d5d75aa9a16871964d1034f0ea4cb01a47bf06e1",
    "fe8b7af72c5c7dbf3c97b9b4a81e04d4d579e463ca68b00dc9f27009fd5165ae",
    "5142e36c9de6f91e5e224a16ce1a179f8c33d9f9027df20635989bfb9b86dc8f",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "c15ef967e365324caea2d3df62d5017211fb3043630d1c2c4d326d0ecba3338c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "9f59e8f2a8bb2ec1da8e6fead44f921e83a88f0fd570738e1d2955fa1705e047",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "7d1ad7187eed08ad35f5c03e6977752891a9b362edd370c9c1009022fd8a326a",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "142a354a66f965cb13dbbb6e10c6d9520ebc3243d0274e816366a7debf78b7bd",
    "4199ba454d6d3ae83657120c2bb6bd674eefc0dd7d3cd4cc844171dc6725135b",
    "78ef744f5c45f06efd9610a2042dba2f841d8e51af8c1dcd54a29a5d47d50c3f",
    "a86474ba3a3feb5aacadfc6eb7584935debedb2b256deadf18c54efee6fd16d9",
    "6dc4d9ecc39049ff7f7073cab03922eef81aabee6b024da34d8cd3b07411b07b",
    "b6770d015347594601077641b56937722084b3b0ce12aeb4983dd17130ca5ee2",
    "81c3364a0cd4ea9356952fe9340c86da14e5fd585ed507acb44c9af9af1ab665",
    "c334c9a96050336fc77de3eb817260e38f33a1506ead770a9be69a694ee02d79",
    "8ebddd417346e5cc373980c07bc90aeda8485695dabc1fa01e39589517abd475",
    "60c3430e18b90bb9f2a857bbb078dee321384b67c1ec5ebe2556c76f08745673",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "c073d8306e9de394feae5597d1e8b4ce62fdeac2e9bc937f6cf65844e231d9e0",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "ac8946a5ea83cafd6fb8f6a116a59521dbe98e2a8093ec8d3217e4479e4cfc33",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "90158b7b46d677fdb5c421b8b82ae31edbd87c1b589e076d188f6f8752dc71c9",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a8f106e1d125b2d4966f14a816ac0449258ffd5e182f19d6b499f6d1db4581e0",
    "4199ba454d6d3ae83657120c2bb6bd674eefc0dd7d3cd4cc844171dc6725135b",
    "9a5ed9c02fda333112d43ed5a8599a11118fe4dd3f37013f121e940b420e414b",
    "0fc1c3cbbef1dba22f4cb8785f54c0502df421b75e49488d8605083dd69677d4",
    "f750fb2ec0ba4dc208ce0ea2007e67b775256b4b906d14f4adb978e876c427bf",
    "50c87703cd75a07316f23b99ebf9fff3520d797f8a2b341f30d79e0300309baa",
    "98d8b27aed0f8c6ae2ba94a6c5503d4b23d84ec1abefdc44a975220fef6093f2",
    "ae54b63a0c4a2b221702fc6c4185589291ab37f285ca5996fa362696f4337e5d",
    "6d41b650ce8335e837a76577043010166f229da984b19d0d62e52f330effb8ea",
    "ba803f9b87af21606b679ff4190ed6be834eec5a113b918f97bc99c81b7d124c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "496f66743ae6ef13381563759ec9685445b43f0461431daad92964d914c37ab4",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "be39250631c8b9841471e8a62e7740d00c618f1b4f44ff7a56bedaf6ca296087",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "8db2665cb62ba52c091a471a2bab977beeb7ee7d430a8a67226d6b97346a6f0b",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "159abce483f2bbdb6b09f3e38df39d25006e93636a164e664d4146fdbe6e705b",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "f36e64416f7e15196d633214790a470916662809d8709ab2f58879566a7b9f2a",
    "f92eeb195c9d025012422a1b489f78ad7c2f17431e143ebe017ef6b8fbd13da0",
    "159a94a31fce612669e2da74d63060a8dab215122f7152f96c01da434267f744",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "f58ddf2bdcbd62e65f100059404f407235d60721840883f002a75afebb0a4dc1",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "909ccd9cc179dcca5a4e2c4b1775cb1dbbdfcb3adcc75dfa5c1af3f5ad8a145e",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a8f106e1d125b2d4966f14a816ac0449258ffd5e182f19d6b499f6d1db4581e0",
    "4199ba454d6d3ae83657120c2bb6bd674eefc0dd7d3cd4cc844171dc6725135b",
    "543f5f032c8c78e8eab3a46aca50ddb256a72e049cb2afa8fddaa3477846a3a0",
    "62a5499b13e5c7c98924c8ded6a28ea596f3fbca42685b0e6d686eb8bf49c1f8",
    "2e6904e0cb7073314807573793cc89755490328289bd83476d7b5211df2fb97f",
    "1aba4b4fe244f1b548b71d5be5384576e9bdc94877a92fe82778a21385feb26d",
    "0491518a83c0d5990fa9f633ddb61edc1947798738e9498585a53acd191c3f05",
    "97e1698873fbb88128c48f1a6dd433a7f6c2efbb450a375bb62e0b4b29a23dfe",
    "dc1232fea4bd54c9c44028355561b8e522e86912486e07033597b1bd80a80e8f",
    "05b177651ad82a6c022bef3a8fb8532a54b79d6b9f0a878d4d9ed56a11d94896",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "af6d468d44be939798e625f07ef87a44af0af8d9a1272d8b0bda232c4dd8aa92",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "31a6b46a9b8a909990486794e341eebce2315afb609ea73249e97c44149a5738",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "b146bacdaf29efc1f0e44724a7d7327b0d80e4ee1647c57b13a5754182a63ee3",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "f1bca3e2c220269b06af934b9d4494b420df9b53347c34ec09211eeb6b440804",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "2057ea4c0d2eab8df1779d4fa8a2e3cd954b8baf5b341c95c7d9db4f9ef88084",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "0aae91508692deb36d85c09edb44b5400b22084f5924fb4d244948553af706c9",
    "6986f373c2db3c3a3c5ed5cf96b1b778964c2a5871795b83320867a09dc99d50",
    "435ac1ead6b90acf9bf0db4b20a81bac9e7e38bdcde56ff2c0ec273f67e06ded",
    "170afc2e434eb93e00dc1afdc1ba2f17125db924db821ecc9ed08efcadec1703",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "ae0e2d282907b72589edf20d715ab2a296639e92a8e272841630c519b2f08879",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "720b68d39391056f74365a5ddcfde6b54fd5c2a654a6f9424d3a790a8d065196",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a8f106e1d125b2d4966f14a816ac0449258ffd5e182f19d6b499f6d1db4581e0",
    "4199ba454d6d3ae83657120c2bb6bd674eefc0dd7d3cd4cc844171dc6725135b",
    "2d5e4f8b4e1e91e665c8053584fcfb16b9c2ff23239020023be22ccccc6d94d2",
    "5053b748f02bbdcc1b0f344a11bf953d1b9e1ad08befba90d97c746e1b2e7a63",
    "ebc727dbc41a1a4818af81b9d8e68c699ae294b28c9fe3e2bc224a9fd149c07e",
    "54916e239b8595826e09f13e7d5773c73efb5dabbbd890506baccb364f0f915f",
    "880625955d368b24c0e6eccbc3135dc70430d45e9a8d7ac2440a6443b6cce0bd",
    "29a14d5d5cdc1b92282f47fc02cc8a77c48d31512627ea972b8542fa3f74266a",
    "65b578a70fa24a4d5040ed8e764738a8a14abaa60f4a9471eeb3c4be6d7250b7",
    "b5f744de3cdb390bdc783259710d70c82b2dfda67a5582ba3a741640b4a786e5",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "ef9e9fca2712b3de12d03ef68dcdce17badec6b539971db537e936a5fddfd854",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a7b9f08c252f8192b957af15f5aa56ac863aa4184391d8dde471b545a5d6e2e8",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "5f31dab6a0ac5521e71f6eb45f6ef33d30c99171bf675b86b810e2cc90622f1e",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "4ffc89debf38a6a4a65252e6c7b64049bdb7315f3415510b4106964e63eaff1b",
    "bdde951564c7ff54c7ae21c41293d964fd8f20b7e1a89aa3634d8b8bafef674c",
    "7cb8c992170eee144e57e73f15317f7159c92491b0cb4e28e2be41727af63c89",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a2526227b7110e575d9a7049a014cc45bc848f796af3fc4b91106f89610a557d",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "2c14c6294b391c90937a42755543825b53ae9a97f5a41196ef765658e0da897c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "0baae98f9f55f3b610f2000d3ecd88f50ea22604ba1058dd98f6d1223b818218",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a8f106e1d125b2d4966f14a816ac0449258ffd5e182f19d6b499f6d1db4581e0",
    "4199ba454d6d3ae83657120c2bb6bd674eefc0dd7d3cd4cc844171dc6725135b",
    "e9472f4922a3dadfd3cc4efeb38557d2bd6f43e1150f4ef73396f719d1692bae",
    "a7af89c359d75d433305e359aaaead67940eb23b6c0a1d5a2888b50e5cf53f2c",
    "e3b44dbf2223de9c94dc43497b179fe8f99c3d73e29287fedc0b8dd832ed6fa4",
    "d53303e07a14b4441c304cdf1db1cb24ed70f5199971aac76d238a5b61d7443e",
    "21428ff6c50a0ec2f151bd7eaba9dfb0ea141487ba58cd787abf4722a3bbf25e",
    "9b946b2aeeb70ab98aee4ad43a6db6feec93fa96748aca3f3937072492fd1ece",
    "1208490505eb6d56f829007062fac6f83a46eecb115fcc7bd532be0a4be413f1",
    "a6d1f0e144862be8fa627d1e0925e323c44dfe16710b5a8d703c7cd937afac82",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "938e312213026781177da86fe8e7972f65989d303e0f02f2d427ad6210d6fc84",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "27cfa57b63d793b580282808cd60b3482aa39f756b623c43e5705f2129da08c7",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "b90179d0d0aee82097c814a869bb6b4a7c44cfa0825b292b7a1d345a3372f491",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "4fc795333ab120ef420a5284903f2e827285e809e23745d2ffce261873b40ec1",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a8f106e1d125b2d4966f14a816ac0449258ffd5e182f19d6b499f6d1db4581e0",
    "4199ba454d6d3ae83657120c2bb6bd674eefc0dd7d3cd4cc844171dc6725135b",
    "62858297171f10ffbec3f88a34d42d1a528399335d6ed0638d201d29bda24f2d",
    "11ab5eb74e5c86e20d6caa724d350082ae309e796b10ab9312a17281ad15b35c",
    "e9fbd4e5a66dfa1cd24cb9e1b3314437da7b25771d46d2736edbefbb5369abb1",
    "fa129955f188ed4f7cd5030eaee890ba1c738214a4f52b8568ea43cbc7946460",
    "6c49adff3ddfa980b996f729462f3c1ffb6538638a79de9c0ebc7097d87438eb",
    "b7382b390fd0c9d184ba401bedc6f4482d1881d6a168e59b55be2d67a51106f1",
    "106f4f86f2beefe69517ade8eaed1eaf37fc32dc41b6ba680b37975acb990de7",
    "587be30a6103c2da6676e007a1b76d6dc460be085c2f45d7bf2dacd8f20726bf",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "3e279eb7a58b7451affb9f175d35e3a9389e0af277b6f1045d753e88b97b434b",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "542a485812b8e1c0ec86e05ceb2eeaff47d30e725eb4b27b3ee7698e7cb5b24f",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "5ca2ab1546476d72c8878d1c7b88e99a5108c903b6be5a36747d0f9dd0e71b44",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "b1b8bd899be6c358cc6611486bfa9d4aee6f954e0e7cd4f3c0e70865a7e7aa53",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "0452ec72a3e83b112c47393470571f772b2f6ebb596e3e96840184b48b5bacbd",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a8f106e1d125b2d4966f14a816ac0449258ffd5e182f19d6b499f6d1db4581e0",
    "4199ba454d6d3ae83657120c2bb6bd674eefc0dd7d3cd4cc844171dc6725135b",
    "3c71e190a8cb936789e7f8e54bb167cbd1dae917c9b8908b7ea6978257b8a2b1",
    "b3512180a8be2c2ed2682fccde8dbf6c4840493697c64ca78ee20c0cd400b0bd",
    "240c6b910bcb0077d7e6c7657b2ebce101748270d795576851d47b858b51472b",
    "b356475415e29edb745724f7828cbc7714ddf71c388e29d70b5b002f58b9c928",
    "77ebb053fd56d2d02d7bff3a20a44f6e62605a6bc9bb77c589fa1f7c1a0f6533",
    "49cfd37d20caa3542038f77f1ada86fc98a8793e64a232c87828295241c56d08",
    "bc1433b2a404d3d3400ccf35799752ebfe0a3eec2591926ec2fc03389d5fbefc",
    "da10a2a1988c768c05421118de7d438f7536e9c3c68e8c9643b7a81199fd1b24",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "bce36f207d70161a36de854bd97051ecb28deaa3493c0c06525f058792789d57",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "7b69de78bdd79c4359b84cc6129f7ba556efa7ea6ee3218e19a06202bf9569d1",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "ae5efa5ddb09da910a3c70450d455ff944a8c11fe57552f07eaf85c05089cc53",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "90871dc245028bb77316dcfc347dbd117c4971a57067660873456e1fd7f9dd11",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "779b93722e9b1ce9f31d9afe39d9c8576e8dd08b5ba169bdd413e5e79f532e6c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a8f106e1d125b2d4966f14a816ac0449258ffd5e182f19d6b499f6d1db4581e0",
    "4199ba454d6d3ae83657120c2bb6bd674eefc0dd7d3cd4cc844171dc6725135b",
    "d1dfc55777b0ef0df355c7e855f9ca0e65f3a66f6a589ba1fc1585b47374574e",
    "84cf308dfff15dfaf19e1a5ed05060aa09775eb4d002fe4eebd71e60f8f3abb6",
    "4ad2ea04af841d36da1e03a58f0f0e3afb7bca7b5d4d0d34650783a206b507ae",
    "310d759d30755b2a29825d67e09e6f70a244b0abdb2ea0ebdaf34c68253ea4e1",
    "45243663abbe59b7bc55562531946f5798c3929787d11afa9e87e6b8ab44d044",
    "3a644168f23409f2e643c7494957622573707bd79d4ad337d2b2eded5e087ccd",
    "8603952fb3545752185582c797ddb9dd18a946022d74379a1ccd3b9db2e89f76",
    "59ebb7a1b6b821b88ccd1633ce1fd871eb3a3465181c0f62d64d5fe63e73330c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "7b7fc41946361cd674efb695122e2a9f2653ed56d9e024f5ecf6c05d6f7b379f",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "cf5cc1ae892dd2cf3c665fbdc5b9b0dde6f24277265ea98122e556c753678b20",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "41935471369442f2d4b11af08a8b379d9133772166bae123072d93af8ddbf6a4",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "ac6afce9bbaf5e6d106352f152f2595239e1f7463fc8481d975351b5d8438cc1",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "85c01854c5481d99a83dc3cae05b6e78b8896887750fac9a497ca8270052ad17",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "4cf4b10ee52d837107f627560cdfb3b0fe24d231739044a5b9cebc71816940a0",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "e7bc2d3b4d23a9b22e22349d59d8246e0b0990e6a82aad44e4ea0435816daea8",
    "4da1ec6f47782090102dc16bda978efb5655fbf2ddce0f84ecf1faf79a930f2d",
    "4830705b21d38b5e020dad28bdcbfe08e37e12d0385882b849371923bef9cf79",
    "140f79c18354f44263dee3638b6e7ccd581c2c3582a87ddc045e19e85ac8dd3f",
    "6a7c72fe198dd122ccd23f2db515ea82c0494c074c4d2566f5f4b49215942881",
    "33f96837740c7f12b368ead69d3756a379f5eead897ba5d0927626a2230a91a8",
    "2d3a5e7ef9c7d1a4ae3a7335839b7236636011ee09961d2407bb7c35ee827121",
    "5cb5a76470f0e68ab6f52a5ab1bca67e21e78a476053afa2e838489dc7f8e53e",
    "1f39cce43e200bacd6f24e344dd5c6a70a8b9b634b722fb6867ca1356324e34d",
    "990840b418f337b570726314f1bdd68f286183a2084b7304cfb15e2a699e3093",
    "abe6e0789cdafb9046a626d494a36b00c2f2b31c6ad0b25d6bfb9e71020c124f",
    "0b43c6834a0d2ad75a355f076339b7c8c00ce5d03402cf4ebadd814bad991bce",
    "1707e304e28cab6dc18a12e51d57a9780a72c859a53ec4dba2e8e87f28010eb8",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "d8001dd24c5d7489ca27a495c8c1652332b5ccbf3dc1654bd7becde93c0ebb0e",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "fb09058014edf715980b4fd8f40ffa5188cf622839e6241267f2bd44878da615",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "cde8fe751dd4de95f10d6e20ef107b0c2af55c254b4ee9dd66debcc00865dd5f",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "1fc2012982e9eb551a10e22ececa13fe9b93a035701c58c88c03f911121b3b5f",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "ad332335cfaa348c5bd715c3479844622270d5f7389ae070b81b135d521a221a",
    "0fcbc49ac1b151190c88aa8b1e20acc8c7f61daa7a6b4f8c877142dd2979e701",
    "baf75e443f317ac25720cb4b0d11342a6234388914c34b3012c6325e5c7b4486",
    "671a50a4dee3d7d2b80756eb470bf4f9c810ad42ffa7a46e91b6f5f2fe734050",
    "64c1eeaefbac7a0ad95ab47f45141b167708e9650a77afe8ab5dc38638bbdc45",
    "f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "21462797e4a700627c8e3601638cdd4bb8293eb7e18c8808f637786a71b345cc",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "b4a313791c1fbca2c1410d1d5b1190af4087723ec1b6c1c4ba776298d6dd6228",
    "caf42be0fcd1ba390ed1c07eab6a0abd12b7da306eb91183d55a6a631a710907",
    "caf42be0fcd1ba390ed1c07eab6a0abd12b7da306eb91183d55a6a631a710907",
    "f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "5d01f5dea001a81d179fef90165437468f0c197d627b4ba2e36f67059dd304b5",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "ad332335cfaa348c5bd715c3479844622270d5f7389ae070b81b135d521a221a",
    "1898da5d4be47b5ecf3ed0d308a7e7f03d612f5b877e6c337884bc6eec55eff1",
    "f1b901847390b0ed7e374e7c1e464ec17b46a427c487a5ad6cbd2906405083d5",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "110d4c86aef752d380a150bcbc2c33461774c7aa2899a3cfea6cca2686714c90",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "41d9b88afc1bada095b74c877efff95a4de601b7b186d2e4a09ad8ed0efcee09",
    "3b5b6d0e764e67b0f320fa21c339083bced789ca2bce387b95f4f9720564ad3f",
    "c3d55f5afd84f122ddb2149ea123db4546ac23c963193087c59abeaa41a382ad",
    "84265885d213db5e429dcda32c4502d0fe8738ff5c01cfe91b5e61b646035a37",
    "a9b292c0a355552cf6906fbb270b254948af5a9353c58911f26e378def473c3c",
    "c7d1c2755ccf05ff9d3dd438e36f127054fadb51e9274839efa3edc134e22eb2",
    "f5b31b5d374ba2c5009dc6ac78c523771994f218a78386eb777a3a967382bec8",
    "18cb05fe2c675b35c13910ed3cffdb2ceefbad3177c00c15a722d4290d33ba47",
    "6caa8c095a21f578ead67554a2df1f37885de6674e9ca20e16061ae59f2757b6",
    "e1cacce554dc837d2d85d749218c89c8035acf256c21d3c5c1ba5c4c974150ee",
    "532582c29dd7447bc3b64c7aff65669c1b11b252a8b96e4d4bfa8192f1a3f974",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a961a728ab4dd21f990d550d699ef607631c63b464806416ba34aa22d1055346",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "044b602892db0f6f8f32b5143c647b8d9eb40a424ae36d2fc73ea7c060e73ac8",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "44c4d9f8a611bc170d67fb1cb81755c2d0296043a02922f950f29e62b5ed0c93",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "278ed7aa09a3b796034d9a58590631bc3cfedff03c9833d2ec2a83a72f9e3262",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "aa0e8afe781c60740cb2b1660b88d084cf509e0fa229c715649c14fc36cb5b96",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "f6fa5f36f2751a76b38df3e1ebb22f7a86d42038a4f35ebf88b2162cfe76f599",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "bd900feae01b69a1e19c72d5c29e202ca3a39b5ffe615573554a626d79661f87",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "c1537754dc2901254ad34063f665f1b3aa272da2b2cede41f873ca64ada2ea41",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "43545c66e1f328fe9afd59aa872d3f71de7cc2a9f7ee370b479016c8ca0ab90a",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "641e441fd53bad9bd80ca4d6fd3c046466d006d00be9d674fb3fa5a585ea85ad",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "178c946bc14073f304a669ca6df65e6909357a768be451cdc6b09ecba0b64407",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "fe23c068a0843cef00d362b66a1f404f4afcbae5293a115fd4e7c4170bf575ab",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "be25c99fb8fc25c37cf7c35128085e9aad17ed752410c458fb95c725839c0546",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "9d3ac292aedd2d34a8a11937911789e06d01bdbae70dad87686dd2bc8d24408b",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "079f86f351735d8b222f8e741891d9c347ed5eeefce0c538bcba453e5757092d",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "5b63bf9a4cbce685fbf8d48177b2a884edd2e5f6c0df176934aaa35a2ebeec02",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "eaf0d2bbd776bd483530a10efbd2c7f99b07fc4f4151baa36bb4052826d2fde2",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "95b514ddb67bd9340206c2ac50757dded759915afc9e2fbd43905cbef2afb891",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "25765b76be47eb42942f30330bec32563d8bfc144165c9e048a49837276cea58",
    "62b67e1f685b7fef51102005dddd27774be3fee38c42965c53aab035d0b6b221",
    "11a060abe65b7dc6ecbbf00780cddbefd530b4581cf7fd9823ff45c0ae98d86b",
    "62b67e1f685b7fef51102005dddd27774be3fee38c42965c53aab035d0b6b221",
    "d398aa0f05b98dce2f894d443d941e9c58381d89725359b2772b5ab7f621c9de",
    "62b67e1f685b7fef51102005dddd27774be3fee38c42965c53aab035d0b6b221",
    "c701fd7f777a3485a1fecac437f477c10333a36a46245bf22420b76cb30011fc",
    "62b67e1f685b7fef51102005dddd27774be3fee38c42965c53aab035d0b6b221",
    "96676ddd29b1023cddf8643711a3be06e3e10d18cc49c8915a802476935c6aa7",
    "62b67e1f685b7fef51102005dddd27774be3fee38c42965c53aab035d0b6b221",
    "d2a310cd1a338a42c1303544a881086a021afcffd6d317aba596a261ef831dc0",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "e9a1d845c98ef8f554af74ab5a67d1796366be9a9a587d079b111d77b7b46c2c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "7c4e0ebead9509e3161ba6b6465b023165427c3f5fa371e94d9655e882898808",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a9b26df496250907705c774c0368d95d9a508f4c784ac99664ee06ac901e8dc0",
    "c4f4e66ac13a98239abe625b6e10c469255126ba715c5e1d715d22758f34a9c8",
    "466a0ea5f1e5854b445c1a7428e78adb4e3b217f4a183ce8a96c3986ee663d7d",
    "c1856768416cb8f2a07b1d2fce8cba345a30763684cab8a87a7dbbeaa5d286d3",
    "ca41a26a2ed26ba24c9d5d3909c35ef27813ed9135fee6cb462a8d4f2bb4081a",
    "518cacf4ac2f713657c070504403c5fa0041b445b550b8797e8ac7e57aed7fb1",
    "619dbb7c8cb5be6f47a9faf02f45170ae028c23e412e6cadbfa02e0345e1ec3b",
    "2ad28ff896074670a82b47e82d820e4e84d19ac4188da159803a63a6fda3b6f2",
    "203e11e4d8af3928cec9d4837fe50622ded694f19552a2338111a8985f93f453",
    "40d8b296797a181137e722bb9e63baa44d77067c077526a694894be771d328bf",
    "5d0338e5856cc6062f5a57a17ecab99d8e2dfc727b2834aa110cecba8d9a40a7",
    "87fa42f8f3c5232b9196ad8b82630ba392d2e7154c4d9151fa537483c2919c83",
    "a8c16f7885adc07c0514d8c2b3e500f323245f54666cce5788edd0e74bbc202a",
    "f0193ad76ef9f6a4e1dd158be64e2abed014b6861b5ade5ad6c31b911d7744f0",
    "14d44a3edd5539915bcbb420d5aa00cf9b48f4fab404c67a97263a7bfd54bf22",
    "997dd6bf2d5b1764fc9f5d824d0a95d67ebe038ecbfcd5ed6c3a35895fe031be",
    "bf3f106a8daf4f3505b467d7069a7887916b3c127703b2ae2b10c44b91d98e7c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "7ec05b5e689e4ff676c857f8466d4fb38e456397ab825aff3e196e9cc0e48184",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "99fff2ba110e62b958e295d65b9ebaae185f8b367dd852d63a20a3c4e215744c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "6fec93661f9c98e5ffb60c7562fd851176d617898ee432315029a90c36b85ed9",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "7ddc7fbe5329b316a87e18ab54fd400598cde0d983141bea31ff676dd0a73ed2",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "79c77d3e4c924196bfff4fd62cf32629d7b069cf1fa5a61f1445dfc2471fffd1",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "7df6b6a3851e37f808e832d9aecd6d2db18438dfe41be3b32ab0ae193ccf64ec",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "c808c560be6bc16d475946efab5b140244df309a0c525463f7884b2699f0b0ae",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "12fc98961ca6b8e3e724b447bd7726e640df71a5ecf93e666d7532fbff1c01cd",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "f479945ebf96ccb30792c3f7781eaa34aa1148e0d597f77f15e70095a25ad81d",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "519141b71a25aab6d41199e92921c49d203b57d83e733aef3e2baaf1994a195c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "efb3488a5c502e88ea72bef2ba1dc1c385768573cfcc5ee32a88649f34d55d2c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "6a92892c1a1203c82134ad9e14da27da9cfa6f281bcc14677999cdf81b182c10",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "9186629c28e7326087531cebb0103d11b63e75df98bed53e6196307bf89c1b0c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "d883626cf635853cb7a1c9d2db7b051b4692a89e03afc553c2d0bc2621f42a1e",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "80625c99b8ba0f831fb2e3ad1bec58c4e2b6c019f974713da93cb3fbf92d61d6",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "8001ed6b68d70e388cb003e368aac68716c80136f8be229d39174613f4996f7a",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "017770c7a0e972c6b4cb35727d5ed897d47b364affe50554c9036e53d30733b7",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a2e5e623a95a356911d6f093cce60912f9646355c48b5f55901a87ca08c2c9eb",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "b7bbbbbf1337559d5a92856d0821005984e9c1e333e3048950fa942829b1aebc",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "868ffc300ce3a24494cc415961b97c70fc11abae936765680d2d08cb294ad3b8",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "fe769b2ca3bc96061faae9f22aeae32699f8886c7b570722831b9665e2c8859b",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "87270f911206c660ccb541d77f9d9693fedd97aca7c3f502efe7d6625246ca82",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "c38c2793da7ae82aa36e2ff93e1068192c2ce51e5a978a400554e2e0a7ae463c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "1c0c8a025fd5101e605ce54ec7bc54ad8f0676190ca68aaa3e41b8a9b1f2b93c",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "6c9601566c22bbd622d31fc9299830b4c4a6f97a17194fb14dea4a6a857d3b3b",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "0b362a88d895cb628ae10b5a8bb35977476800ec9521171c49108919afb43395",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "ecf16e20ccd8cc6733642c68a69b01e650b0a5a57da7df5c9427b59535620575",
    "b06dfc57b74fc79f465ca7aa35523559f76b4f4f8786c7e1352a14c146de4911",
    "fd6041814f7b78ebf4feb27c9d205b40c0adee480f0ca7a4699c7e502019ae05",
    "00a1246fd6c5961c235930e6ade0a0a6aefd40ac928529ffac57cf9bd7695dde",
    "4bc0afc3ef708fe028fa8a4825e1518474b139817d9a0fd286f2b91ab395978c",
    "f50ec6d41a80014cc570cbe7dad885ce0e7c6351475528947ad165b244b96f36",
    "9d033e8b80425711ecfab500af80623cb67d26991b5d0929e1c53ba5fa3fb4b6",
    "21d2647a291a7aef62ec274ff0ea716cc4096a7f32f121c0f3bba4fea6da3b4a",
    "7ab997597d8b64e88351cd86dcba45ff763f867e178c55f36c304cac77aee36a",
    "8c178cdf29f6cbd83e29f9c89b7b6ab1d572a8968275f5c90380c55f5b0c915c",
    "fbbc60ab7c608f6bdb6e4325b28fb42e41f64f7920bef51fb78f4aa95a95499a",
    "e42fb9eb8c9182c90fda4728c5a78e38c8ce1054e425ca1ea232502cf69be1e9",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "30ac03ff33731529441be8fbe52a3bd0d4c5ec830e806d54692168ebb7f98ada",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "3daff360876b0c551b9fc65d77d83b395f1273aaa9806e77deb8f46f1edfcb11",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "bcb824b69e25df1ad7383809f5de31c4ac1b3703920ea265948de051aba66982",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "f3de744d7f78a453d77661618de03d58329807e33ae45bc565f63554aa69bdcd",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "0837b13b9d2bbd6420e326532e3e94f46e96f93448138ea4925afc40d839a672",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "bc853e11d5d6301fed70cb69a7327eb7b8978c0f566a91cf09b0545398429cf5",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "f7fc45ffcd17898684a82a2b05f6a3dcaa5bfc999334ae2d655e5506fc7ecbbc",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "8595ce2acb14ac537fd488152836c8375460eb7487f1b1d5dff3a4573518b816",
    "3ee1e768e6d63b795f5c9d879fa0cf2e51a562ad2437494d8948d9cda2c9cf54",
    "695b75f54a60bbe96d7ec53d14f0c18d94e325482c2e0b7d29e816abef37f5fa",
    "b57a84c034b10aad7534254727c8284c8408ba194f152b25d1b7960676fee8d9",
    "ad728991c80e138124c1aa41ced04e4b933bd6e1e605c5a09719d97d8fad7984",
    "df4f8be5449b214832d9041a8b264259774c89a78aaff3555f65f46180607c8b",
    "e5f0446c0d57d6c8251558d28e2a8ba93bed9bcac4a72b919a1269e93545a6ac",
    "af0f98bd55742bc4f893952b2c2c754866d0dbe2e2bc3a1db789de6886749193",
    "e260102d19fee52d39c1ef1767dbb48354192e409546c656ccb25c0526bfcff5",
    "703f3740d80d7aa42a0f1d02f5a915e67376cde1747a1b3c4d19f1237009e66f",
    "fdfded3fd47bf87065e780690833d65b2b9dcee9ed35243e07a144a44ae7b853",
    "534a0f213d32adf740ef7c2742c4b745511d61924ce3c4f58ba6056d434b4ec1",
    "4b9a7170d957958164e7bd3e78deef751852b15ed8546959199a9432e9e753fb",
    "88478637141657a15a2bc6f370af901271f9f4abf60bff315fd219e277c50d2a",
    "85c13871643247ef4c0c7886dd772cf5dfd10e7a1850c38a29d486dba38ca4c2",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "6c2ff442c2f6b33d0571f5ee0cc04317f8d7cb128b57a20bda1cde69d8569026",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "af6e6533a5442cfa9f6b7d25f8494b9e95fddb278137024ac8e2f58af4d383a4",
    "cc04492ffa1278ea387f1b0452b0d3ccb61669c6c782da37e4ea858c731db17b",
    "bab63499603a7e4880d9339b15aafa5712fb1dc5031e266808f205e4e42c76b2",
    "43d1192d1686bcee26f748065271ac81ece5c3376ad2522988ec425d4209beb7",
    "1300f67157bb8520e3caf2e17a7e3d4a21145e7c6fc50dc8e043e271799a9f9d",
    "8aa8e953e26cb0bae0eb5188e14372aa6647e6c70430346c98ceb8a61dbc373f",
    "6f9033c0b5b4b258b14d2bbc94c7c4ff4d2722c70acf2a4496bb0362fff47cb5",
    "6dcdeb0cb8904559c96b1e08cb6d2070d747366f9e649f2803626f8b361c70ee",
    "9a9617d99daaac40090880dd99a411a6b64b619f74f0b6bc9c131a3f96ec39a2",
    "59976f53cd97cdd07b8f9a55216fd4a06310d5d136a4eabc4292c8a97d03746e",
    "53a04437d5b7d80414ff5fc6ef7ef322da21ad8ce73da949c7abafa61a478de9",
    "d3f1d2ab7fdf8e0e3039acefdce13221c5df902ceed621bdcb53dbfe7f30752e",
    "e5073ad6afb03090696c32c08194eb98cd94f9b6641998f23f443b68d855726f",
    "b3b240411b753cabb381f5979797902ea590581665114be11b1e6c7646615bf1",
    "63121313f43c065343ba02d14d168d2cf53f091bbddaa89bc43dc8be3810968e",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "44556f7a3f6cf9632719bc15e4ad0913e5686d49168be9470135b808c367a724",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "737dfcc8857ed277cfa6424d6cea9e219b28b8fdf953f1d549f9ef3b8c09f667",
    "0768265e424a551b05429fbfe68ceb45369cd629c6ccebff7cbdd4df5d0bbf56",
    "e77d73a44107c91f1ca54570bccbaa3583a4b82c388f5ad352a857dec6c85cae",
    "cb19190f9af8c2cf706caf5544b5623c162b56edd2ec3d7911cd24c1b137c521",
    "7789747c54a415a2cd4f0c922f35b507af900f10ffef5c81e49a7485c660ad96",
    "dc52f20180c9eb4ccd9d5254948160f56c680268774470c2dc79ef83cf358f65",
    "e180f5b4ecb5ca3a0fdbf594e518adb594db2375d1a0d8b2aafeac7eee8db8e1",
    "2f40342a4fb5ffb757b53288a9d94608c1848f8cd451a6bc637b0bcf41d33736",
    "4519574ae62abe51e407ad4a965bbbcc064f310f14bc8e238bda336f759493eb",
    "69a26ad3f0a2db97b3d5ed814494f9aa39ebe49d86e516f03d6bccbff1892cee",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "b0b0ceb6a2698e773e0dc32e551c7079d91bc1d7d305835fcf983dcf934956f9",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "bab14be9f278e34d947203d52a4fa26cbd25937337f33fb311b2679d33512473",
    "28f1d3a4941c4d3ce9ae30698afea3a56a3b65dcde779125cbd353de91275301",
    "b339819d3c6be660ad9b81b2349229dac71eea956042fa8d6cde7205ac8f2ed6",
    "3741c716662770bed8992cc466b2af49a3551c81f9c05f54da6f83499523ecf5",
    "f41ca0383f479dae0dd1ff1bfa47941886248bd3d9151feba24f30aca351d7b9",
    "137e088942f507bf3811de07fbebd793475e4e272f5ad6ff1f58c16d05d6d601",
    "2bd4371ba4169f942538e35c97736fbcc671dac330663ffd5299452787b80c1d",
    "d165e62e53b57a962115ed8ef691b52b391561cd868744e44e44b8adc27e4a23",
    "99605ae23a5c9520d9fde70243062d26bd4d6ca188494234dc001ea85c2102b9",
    "ee92d6e97d70633b09fe72e0b51af852ed6417c8d621188f5dad4c0f1ea50018",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "9fe6ac073c8b4a42c9543851b7854402bba3c4498b1d0cc870f5cce2461c382e",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "3a7832f212daf50793600b0f1f43c164bee6175003711bd021857652b34cb42e",
    "f7f30d499efa7b376a962ea9fca9f5e525c423aaa598eceddd13537de0cf4c35",
    "cbdca512a95dbbaea9bffc9557d4e0da134379020cedb027544dd423a7a363b5",
    "c45eeaee33f3081da6d0cd1e8d29f5d9cd93cffba1ac87c9231b822ad3284580",
    "8d71107cdd0ee2573a92474a408cab18c2112bd601d23441b9c3605ef1d1c761",
    "be85e66c2441750b3c7317b239e1ede285edac2e8cbdd3104b1d0af3c604123b",
    "51acd293789f6007b67bec7f8f692e760f54ec4c1ef9375087604893e5aa7032",
    "289f230c43bd18db909c58bb163eeb3eecff9d48b6da707fb817340a1f3dded6",
)

REQUIRED_HEADINGS = (
    "Learning objectives", "Prerequisite graph", "Opening architecture question",
    "Theory", "Source map", "How to use an extension contract card",
    "Alternatives and trade-offs", "Reproducible evidence walk-through",
    "Verification", "Fidelity box", "Binding claim-boundary register",
    "Common failure modes", "Development questions", "Summary", "Review questions",
    "Review-question answer key", "Design exercises", "Exercise answer sketches",
    "Primary references",
)

REQUIRED_EXTERNAL_URLS = (
    "https://doi.org/10.1109/DAC18074.2021.9586216",
    "https://www.usenix.org/conference/osdi18/presentation/chen",
)


class ValidationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def run(args: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None,
        timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=timeout)


def checked(args: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None,
            timeout: int = 180) -> str:
    result = run(args, cwd=cwd, env=env, timeout=timeout)
    require(result.returncode == 0,
            f"command failed {' '.join(args)}: {result.stdout[-1600:]}")
    return result.stdout


def git(args: list[str], cwd: Path = ROOT) -> str:
    return checked(["git", *args], cwd=cwd).strip()


def slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return re.sub(r"[ -]+", "-", text).strip("-")


def heading_ids(path: Path) -> set[str]:
    found: set[str] = set()
    counts: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        base = slug(match.group(1))
        count = counts.get(base, 0)
        found.add(base if count == 0 else f"{base}-{count}")
        counts[base] = count + 1
    return found


def validate_links(text: str) -> int:
    unfenced = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    links = re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", unfenced)
    require(len(links) >= 14, f"link count {len(links)}")
    for url in REQUIRED_EXTERNAL_URLS:
        require(text.count(url) == 1, f"primary-source URL/count {url}")
    for raw in links:
        target = raw.strip().split()[0].strip("<>")
        if target.startswith(("https://", "http://")):
            continue
        require(not target.startswith("/"), f"absolute local link {target}")
        file_part, marker = target.split("#", 1) if "#" in target else (target, "")
        resolved = (CHAPTER.parent / file_part).resolve() if file_part else CHAPTER.resolve()
        require(resolved == ROOT or ROOT in resolved.parents, f"link escapes repository {target}")
        require(resolved.is_file(), f"missing link target {target}")
        if marker:
            require(marker in heading_ids(resolved), f"invalid anchor {target}")
    return len(links)


def validate_cards(text: str) -> int:
    matches = list(re.finditer(r"(?m)^## 23\.\d+ Contract card \d+: ([^\n]+)$", text))
    require(len(matches) == 7, f"contract-card count {len(matches)}")
    fields = ("Promised contract", "Current classification", "Exact claim IDs",
              "Weakest required edge", "Positive evidence", "Stop evidence",
              "Alternatives and trade-offs", "Promotion trigger")
    for index, match in enumerate(matches):
        name, claim_ids = CARD_CLAIMS[index]
        require(match.group(1) == name, f"contract-card {index + 1} identity")
        next_heading = re.search(r"(?m)^## 23\.\d+ ", text[match.end():])
        end = match.end() + next_heading.start() if next_heading else len(text)
        section = text[match.start():end]
        for field in fields:
            require(section.count(f"| {field} |") == 1,
                    f"contract-card {index + 1} field/count {field}")
        for claim_id in claim_ids:
            require(f"`{claim_id}`" in section, f"contract-card {index + 1} claim {claim_id}")
    return len(matches)


def validate_text(text: str) -> tuple[int, int, int]:
    require(text.startswith("# Chapter 23 — Extending Tusim Without Breaking Its Contract\n"),
            "title")
    require(PIN in text and RETAINED_SHA in text and RUN_REL.as_posix() in text,
            "edition and seal binding")
    words = len(re.findall(r"\b[\w’'-]+\b", text))
    require(6800 <= words <= 9500, f"word count {words}")
    actual = [m.group(1).lower() for m in re.finditer(r"(?m)^#{2,6}\s+(.+)$", text)]
    for required_heading in REQUIRED_HEADINGS:
        require(any(required_heading.lower() in item for item in actual),
                f"heading {required_heading}")
    cards = validate_cards(text)
    for line in BOUNDARY_LINES:
        require(text.count(line) == 1, f"binding boundary line {line[:38]}")
    require(tuple(re.findall(r"(?m)^\d+\. `(C23-\d\d)`:", text)) ==
            tuple(f"C23-{index:02d}" for index in range(1, 18)),
            "complete ordered boundary IDs")
    for phrase in KEY_MUTATIONS:
        require(text.count(phrase) == 1, f"key phrase/count {phrase}")
    for label, line in CLAIM_MATRIX_LINES:
        require(text.count(line) == 1, f"claim matrix line/count {label}")
    require(text.endswith("\n"), "manuscript final newline")
    manuscript_lines = text.splitlines()
    require(len(manuscript_lines) == len(MANUSCRIPT_LINE_SHA256),
            f"manuscript exact line count {len(manuscript_lines)}")
    for line_number, (line, expected) in enumerate(
            zip(manuscript_lines, MANUSCRIPT_LINE_SHA256), 1):
        require(sha_bytes(line.encode("utf-8")) == expected,
                f"manuscript exact line L{line_number}")
    forbidden = (
        "Tusim has an integrated ONNX/compiler/runtime path.",
        "NLR executes through the dataflow dispatcher.",
        "All 59 opcodes execute through the command queue.",
        "The cycle model is production integrated.",
        "Python config_path configures the C runtime.",
        "The dataflow sweep executes WS, OS, and RS routes.",
    )
    for statement in forbidden:
        require(statement.lower() not in text.lower(), f"unsafe affirmative claim {statement}")
    require(not re.search(r"(?m)^\|\|", text), "malformed markdown table row")
    require(not any(line.rstrip() != line for line in text.splitlines()),
            "trailing whitespace")
    links = validate_links(text)
    return words, cards, links


def validate_evidence() -> None:
    require(RUN.is_dir() and not RUN.is_symlink(), "postreview run directory")
    seal = json.loads(SEAL.read_text(encoding="utf-8"))
    require(seal == {
        "compiler_runtime_onnx_boundary": "negative",
        "decision": "extension-contract-card/weakest-missing-edge",
        "mode": "postreview",
        "retained_manifest_sha256": RETAINED_SHA,
        "schema": "tusim-book/ch23-predraft-seal/v1",
        "source_pin": PIN,
        "validation": "PASS",
    }, "exact postreview seal")
    require(sha(RUN / "retained.sha256") == RETAINED_SHA, "retained manifest digest")
    require(PLAN.read_bytes() == (RUN / "chapter-23-framing-and-evidence-plan.md").read_bytes(),
            "live framing equals retained authority")
    require(LEDGER.read_bytes() == (RUN / "chapter-23-source-claim-ledger.md").read_bytes(),
            "live ledger equals retained authority")
    for prefix in ([sys.executable], [sys.executable, "-O"]):
        output = checked([*prefix, str(RUN / "verify_ch23_predraft_seal.py"),
                          "--run-dir", str(RUN)])
        require("CH23_SEAL_VERIFY PASS mode=postreview members=19 boundary=negative" in output,
                f"postreview verifier {' '.join(prefix)}")
    ledger_text = LEDGER.read_text(encoding="utf-8")
    rows = re.findall(r"(?m)^\| (C23-\d\d) \|.*\| (allow|qualified|block) \|$", ledger_text)
    require([row[0] for row in rows] == [f"C23-{i:02d}" for i in range(1, 18)],
            "ledger exact claim set")
    require(dict(rows) == {
        "C23-01": "allow", "C23-02": "qualified", "C23-03": "allow",
        "C23-04": "qualified", "C23-05": "block", "C23-06": "block",
        "C23-07": "qualified", "C23-08": "allow", "C23-09": "block",
        "C23-10": "block", "C23-11": "qualified", "C23-12": "block",
        "C23-13": "block", "C23-14": "block", "C23-15": "block",
        "C23-16": "block", "C23-17": "block",
    }, "ledger exact states")


def mutation_tests(original: str) -> int:
    mutations = {line: line.replace("not ", "", 1) if "not " in line
                 else line.replace(":", ": MUTATED", 1)
                 for line in BOUNDARY_LINES}
    mutations.update(KEY_MUTATIONS)
    detected = 0
    for old, new in mutations.items():
        require(original.count(old) == 1, f"mutation source/count {old[:50]}")
        try:
            validate_text(original.replace(old, new, 1))
        except ValidationError:
            detected += 1
        else:
            raise ValidationError(f"manuscript mutation survived: {old[:60]}")
    for url in REQUIRED_EXTERNAL_URLS:
        try:
            validate_text(original.replace(url, "https://invalid.example/changed", 1))
        except ValidationError:
            detected += 1
        else:
            raise ValidationError(f"citation mutation survived: {url}")
    for label, line in CLAIM_MATRIX_LINES:
        require(original.count(line) == 1, f"claim matrix mutation source/count {label}")
        mutated_line = line[:-1] + ("?" if line[-1] != "?" else "!")
        try:
            validate_text(original.replace(line, mutated_line, 1))
        except ValidationError:
            detected += 1
        else:
            raise ValidationError(f"claim matrix mutation survived: {label}")
    for old, new in TARGETED_REVIEW_MUTATIONS.items():
        require(original.count(old) == 1, f"targeted mutation source/count {old[:50]}")
        try:
            validate_text(original.replace(old, new, 1))
        except ValidationError:
            detected += 1
        else:
            raise ValidationError(f"targeted review mutation survived: {old[:60]}")
    return detected


def validate_self_mutation() -> None:
    if SELFTEST_CHILD:
        return
    source = Path(__file__).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="ch23-validator-") as temp:
        mutated = Path(temp) / "ch23_manuscript_validate.py"
        mutated.write_text(source + "\nassert(False)\n", encoding="utf-8")
        env = os.environ.copy()
        env["CH23_VALIDATOR_SELFTEST_CHILD"] = "1"
        env["CH23_MANUSCRIPT_REVIEW_MODE"] = "1"
        for prefix in ([sys.executable], [sys.executable, "-O"]):
            result = run([*prefix, str(mutated)], env=env)
            require(result.returncode != 0 and
                    "optimizer-removable assertion in validator" in result.stdout,
                    f"validator assertion mutation {' '.join(prefix)}")


def git_blob(commit: str, rel: str) -> bytes:
    result = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    require(result.returncode == 0, f"git blob {commit}:{rel}")
    return result.stdout


def validate_repository_state() -> str:
    require(git(["branch", "--show-current"]) == "main", "book branch main")
    require(git(["rev-parse", "HEAD"], cwd=TUSIM) == PIN, "Tusim source pin")
    require(git(["branch", "--show-current"], cwd=TUSIM) == "", "Tusim detached")
    require(git(["status", "--porcelain", "--untracked-files=all"], cwd=TUSIM) == "",
            "Tusim tracked clean")
    head = git(["rev-parse", "HEAD"])
    require(git(["status", "--porcelain", "--untracked-files=all"]) == "",
            "clean book worktree")
    if REVIEW_MODE:
        return head
    require(SNAPSHOT.is_file(), "reviewed snapshot marker")
    entries: dict[str, str] = {}
    for line in SNAPSHOT.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([a-z_]+)=([0-9a-f]{40}|[0-9a-f]{64})", line)
        require(match is not None, "reviewed snapshot syntax")
        if match is None:
            raise ValidationError("reviewed snapshot syntax")
        key, value = match.groups()
        require(key not in entries, f"duplicate snapshot key {key}")
        entries[key] = value
    require(set(entries) == {"claim_commit", *BIND_PATHS}, "reviewed snapshot keys")
    claim = entries["claim_commit"]
    checked(["git", "merge-base", "--is-ancestor", claim, head])
    for key, rel in BIND_PATHS.items():
        blob = git_blob(claim, rel)
        require(sha_bytes(blob) == entries[key], f"reviewed marker hash {rel}")
        require(blob == (ROOT / rel).read_bytes(), f"current blob matches reviewed claim {rel}")
    return claim


def main() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    try:
        parsed = ast.parse(source)
    except SyntaxError as error:
        raise ValidationError(f"invalid validator source: {error}")
    require(not any(isinstance(node, ast.Assert) for node in ast.walk(parsed)),
            "optimizer-removable assertion in validator")
    require(CHAPTER.is_file() and PLAN.is_file() and LEDGER.is_file(),
            "manuscript and authority inputs")
    validate_evidence()
    text = CHAPTER.read_text(encoding="utf-8")
    words, cards, links = validate_text(text)
    mutations = mutation_tests(text)
    validate_self_mutation()
    claim = validate_repository_state()
    mode = "review" if REVIEW_MODE else "release"
    print(f"CH23_MANUSCRIPT_VALIDATION PASS run={RUN_REL} words={words} cards={cards} "
          f"claims=17 members=19 evidence_mutations=13 reader_mutations={mutations} "
          f"links={links} optimization_safe=yes mode={mode} claim_commit={claim}")


if __name__ == "__main__":
    try:
        main()
    except ValidationError as error:
        raise SystemExit(f"CH23_MANUSCRIPT_VALIDATION FAIL: {error}")
