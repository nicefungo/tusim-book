#!/usr/bin/env python3
"""Fail-closed Chapter 22 framing reconnaissance.

This read-only framing artifact inventories the exact exploration portfolio,
checks selected claim-level dispositions against hash-bound book evidence,
validates cross-domain regime candidates semantically, and assigns every
sample claim to an explicit noncomposable metric domain. It is not the later
complete Chapter 22 claim register or predraft evidence seal.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys

PIN = "e918c80b6fce833cd1fcae97730fa841c2176f25"
BOOK_BASE_HEAD = "9cfedfad3d78190972f6481857ad56d9019fbf19"
SOURCE = Path("/home/zxy/Workplace/projects/tusim")
BOOK = Path("/home/zxy/Workplace/books/tusim-book")
REPORT_ROOT = SOURCE / "docs/exploration"
CANONICAL_STATUSES = {"retained", "qualified", "superseded", "rejected", "blocked"}

DOMAINS = {
    "geometry_balance": {
        "aspect-ratio-alignment-sweep.md", "bus-width-sweep-gemm128.md",
        "dataflow-comparison-gemm128.md", "dataflow-pe-interaction.md",
        "dataflow-rs-comparison-gemm128.md", "k-sweep-dma-crossover.md",
        "mac-density-dma-bound.md", "pe-array-sweep-gemm128.md",
        "pipeline-depth-dataflow-interaction.md", "pipeline-depth-sweep-gemm128.md",
        "pipeline-depth-workload-interaction.md", "rs-pipeline-depth-sweep.md",
        "workload-scaling-pe-optimal.md",
    },
    "memory_movement": {
        "db-pe-size-goldilocks.md", "dma-channel-queue-sweep.md",
        "double-buffer-mtiling-recovery.md", "dram-type-clock-sweep.md",
        "gbuf-sizing-sweep.md", "sram-arbitration-sweep.md",
        "sram-obuffer-tiling-threshold.md", "sram-wa-buffer-sizing.md",
    },
    "numerics_weight_representation": {
        "bitmap-weight-compression.md", "int8-quantization-throughput.md",
        "precision-sweep-gemm128.md", "rounding-mode-accuracy-sweep.md",
        "structured-2of4-sweep.md", "weight-compression-rle-sweep.md",
        "weight-decoder-throughput.md",
    },
    "operator_irregularity": {
        "attention-engine-sweep.md", "conv-group-sweep.md", "conv-pool-cascade.md",
        "convolution-kernel-stride-sweep.md", "mma-fused-activation-overhead.md",
        "norm-after-attention-pipeline.md", "norm-mode-comparison.md",
        "pooling-config-sweep.md", "softmax-after-attention-pipeline.md",
        "softmax-mode-comparison.md",
    },
    "sharing_topology": {
        "broadcast-dma-multicore-scaling.md", "interconnect-contention-traffic-matrix.md",
        "interconnect-mesh-routing-order.md", "interconnect-switching-modes.md",
        "interconnect-topology-sweep.md", "multicore-scaling-gemm256.md",
    },
    "runtime_static_policy": {
        "context-switch-state-scope.md", "scheduler-policy-sweep.md",
    },
}

# Each candidate must span at least two inventory domains, carry an explicit
# producer boundary, and name a break case. These are structural analogies,
# never a license to compare or add their quantities.
REGIMES = {
    "fixed_cost_amortization": {
        "members": {"k-sweep-dma-crossover.md", "pipeline-depth-workload-interaction.md",
                    "mma-fused-activation-overhead.md", "conv-pool-cascade.md"},
        "boundary": "Compare only setup/output-pass dominance shapes; preserve each local formula producer.",
        "break": "A capacity-triggered extra pass is discontinuous rather than an amortized fixed term.",
    },
    "resource_threshold_or_discrete_cliff": {
        "members": {"gbuf-sizing-sweep.md", "sram-obuffer-tiling-threshold.md",
                    "structured-2of4-sweep.md", "weight-decoder-throughput.md"},
        "boundary": "Capacity pass-count and decoder-provision knees remain different equations and units.",
        "break": "A smooth bus-width balance point need not contain a discrete resource cliff.",
    },
    "bandwidth_compute_balance": {
        "members": {"bus-width-sweep-gemm128.md", "mac-density-dma-bound.md",
                    "workload-scaling-pe-optimal.md", "int8-quantization-throughput.md"},
        "boundary": "Balance only within one named workload and producer; no calibrated physical roofline is claimed.",
        "break": "A correctness defect or distribution-sensitive codec can dominate independently of this balance.",
    },
    "distribution_or_placement_not_scalar_rate": {
        "members": {"bitmap-weight-compression.md", "weight-compression-rle-sweep.md",
                    "structured-2of4-sweep.md", "interconnect-contention-traffic-matrix.md"},
        "boundary": "Sparse placement and traffic placement are analogous sensitivities, not comparable rates or costs.",
        "break": "Uniform fixed-cost amortization can be insensitive to placement at a fixed work count.",
    },
    "shape_or_placement_reversal": {
        "members": {"aspect-ratio-alignment-sweep.md", "dataflow-pe-interaction.md",
                    "interconnect-mesh-routing-order.md", "interconnect-topology-sweep.md"},
        "boundary": "Geometry and traffic-route reversals retain separate producers and objective functions.",
        "break": "Broadcast sequential-copy evidence contains no endpoint-placement winner reversal.",
    },
    "retained_or_buffered_state_scope_shifts_obligations": {
        "members": {"context-switch-state-scope.md", "db-pe-size-goldilocks.md",
                    "double-buffer-mtiling-recovery.md"},
        "boundary": "Context retention and ping-pong buffering shift different ownership/reload obligations.",
        "break": "DMA channel count changes concurrency without changing retained-state scope.",
    },
    "local_formula_or_metric_dialect_hazard": {
        "members": {"dataflow-comparison-gemm128.md", "dram-type-clock-sweep.md",
                    "precision-sweep-gemm128.md", "softmax-after-attention-pipeline.md"},
        "boundary": "Only the hazard recurs; formulas, error metrics, stalls, and cycle estimates remain noncomposable.",
        "break": "Exact encoded byte counts are comparable within one codec fixture without becoming elapsed time.",
    },
}

EVIDENCE_HASHES = {
    "notes/chapter-07-source-and-claim-ledger.md": "cca1607b8b9db51f9e49fbade01905766e69d2c49b4eabcce5ebb4317f3153dd",
    "notes/chapter-08-source-and-claim-ledger.md": "dffa83a5d604b7dc5201bc8f4d7c92ebffb1fb4f1b1aaad70a40e8ca398dd3a5",
    "notes/chapter-12-source-and-claim-ledger.md": "df50740956956fb43e1219911f47f918eac73cc4b228ded4b6ac6bc26d88d95e",
    "notes/chapter-13-source-and-claim-ledger.md": "1ab6edad3c89e82659e6939dd0931ee74f529c114193f19def403545a0f293ca",
    "notes/chapter-14-source-and-claim-ledger.md": "06812b971eea1347ef8ee29791f4b09494116e04c09dbfde7c573b52fa390be6",
    "notes/chapter-15-source-and-claim-ledger.md": "74274b21a1fa3bc40f9563698e35c8ea48945a0a4d135c1f595db9104f5ef596",
    "notes/chapter-16-source-and-claim-ledger.md": "b2a329459123b238a0bca536423070488818f7e0b074ffac678af45bb128ac5b",
    "notes/chapter-18-source-and-claim-ledger.md": "cdf5e538ef768eaddfa4c4df1471385e8acf7721751c4e1c9d0481a5e0c2ad1e",
    "notes/chapter-21-predraft-audit-report.md": "be6b74bbd04ecf6ad03b4a4654cee11f464a9ff1fa378d2df696fc5dcb19e171",
    "notes/chapter-21-source-and-claim-ledger.md": "57a29749614d59b5fe5f58e5202563fb000d4f112aeffdfc6532cd1904f4a416",
    "source-audit.md": "bf558f6f869b864a9265b7484fb1cb4cda914170c39cebf7c531d425048471e8",
}

# id, report, report anchor, canonical status, reason, evidence file,
# structured evidence reference, evidence anchor, metric domain, safe wording
DISPOSITIONS = [
    ("D22F01", "aspect-ratio-alignment-sweep.md", "When sizing PE arrays, prefer divisors", "rejected", "global-bound-counterexample",
     "notes/chapter-21-source-and-claim-ledger.md", "C21.7", "### C21.7 — Historical aspect prose contains a counterexample", "local_formula_cycles",
     "Reject the global remainder bound and compiler-padding recommendation; tested-grid arithmetic remains separate evidence."),
    ("D22F02", "dataflow-comparison-gemm128.md", "Do not optimize for dataflow choice", "rejected", "ineffective-route-and-producer-split",
     "notes/chapter-21-source-and-claim-ledger.md", "C21.3", "### C21.3 — Dataflow labels do not prove the effective route", "local_formula_cycles",
     "Reject the report recommendation; labels, functional route, handwritten equations, and linked estimators are separate producers."),
    ("D22F03", "dataflow-pe-interaction.md", "Dataflow choice is irrelevant for throughput", "rejected", "logical-not-physical-movement",
     "notes/chapter-07-source-and-claim-ledger.md", "claim-table:physical-movement", "WS/OS/RS implement distinct physical movement", "noncycle_functional_or_structure",
     "Functional equivalence on bounded values does not establish physical movement or universal throughput irrelevance."),
    ("D22F04", "dataflow-rs-comparison-gemm128.md", "OS gives 20% faster throughput than WS", "rejected", "incompatible-formula-producers",
     "notes/chapter-21-predraft-audit-report.md", "metric-table:linked-dataflow-plugins", "linked dataflow plugins", "linked_plugin_cycles",
     "No report percentage is a calibrated physical ranking; the three formula producers remain separate."),
    ("D22F05", "pipeline-depth-sweep-gemm128.md", "hardware-accurate spatial-tile accounting", "rejected", "unvalidated-formula",
     "notes/chapter-07-source-and-claim-ledger.md", "claim-table:pinned-WS-cycles", "pinned WS cycles are", "local_formula_cycles",
     "Reject hardware-accurate wording; retain the report equation only as a local alternative hypothesis."),
    ("D22F06", "dram-type-clock-sweep.md", "DRAM type is a don't-care", "rejected", "arithmetic-contradiction",
     "notes/chapter-15-source-and-claim-ledger.md", "C15.23", "C15.23 (rejected as decision evidence)", "local_formula_cycles",
     "Reject the arithmetic conclusion and device recommendation; the bandwidth-balance question remains open."),
    ("D22F07", "db-pe-size-goldilocks.md", "Double-buffering is most architecturally valuable", "blocked", "ordinary-overlap-unestablished",
     "notes/chapter-16-source-and-claim-ledger.md", "C16.27", "C16.27 (rejected pending recomputation)", "db_ideal_overlap_formula_cycles",
     "No executable ordinary-operation evidence can rank the Goldilocks alternative at this pin."),
    ("D22F08", "double-buffer-mtiling-recovery.md", "single highest-leverage architectural feature", "rejected", "recommendation-exceeds-evidence",
     "notes/chapter-16-source-and-claim-ledger.md", "C16.27", "general recommendations such as “single highest-leverage,”", "db_ideal_overlap_formula_cycles",
     "Reject recovery and highest-leverage claims until target, byte visibility, dependency, ownership, and common-clock bridges execute."),
    ("D22F09", "broadcast-dma-multicore-scaling.md", "Broadcast DMA is a hard requirement", "rejected", "sequential-copy-not-multicast",
     "notes/chapter-12-source-and-claim-ledger.md", "C12.19", "C12.19 | For bounded, in-range inputs", "traffic_heuristic_cycles",
     "Reject the current hard-requirement claim: broadcast performs N-1 sequential immediate copies, not one multicast transfer."),
    ("D22F10", "interconnect-topology-sweep.md", "Its 1.5–3.1× MESH figures", "superseded", "current-linked-traffic-reversal",
     "notes/chapter-12-source-and-claim-ledger.md", "C12.31/C12.32", "Historical topology/all-reduce and multicore-scaling scripts", "traffic_heuristic_cycles",
     "Supersede the standalone figures with current linked traffic-specific heuristic reversals; no universal topology winner follows."),
    ("D22F11", "precision-sweep-gemm128.md", "FP8_E4M3 is the unambiguous throughput champion", "rejected", "no-precision-specific-MMA-route",
     "source-audit.md", "source-audit#32", "direct MMA hardcodes FP16 W/A and FP32 psum/O", "local_formula_cycles",
     "Element-width spreadsheet rows do not establish an FP8 MMA throughput path, numerical acceptability, or runtime selection."),
    ("D22F12", "rounding-mode-accuracy-sweep.md", "RTZ is 2.6× worse than RNE", "qualified", "bounded-conversion-fixture-only",
     "notes/chapter-21-source-and-claim-ledger.md", "C21.4", "### C21.4 — Rounding and seed reach conversion", "precision_conversion_error_metric",
     "Retain only the bounded converted-input fixture; no application-accuracy or accumulation-rounding conclusion follows."),
    ("D22F13", "structured-2of4-sweep.md", "2:4 is not universally faster", "qualified", "analytical-estimator-only",
     "notes/chapter-13-source-and-claim-ledger.md", "C13.15", "C13.15 | The estimator computes", "codec_byte_and_estimator_cycles",
     "Retain decoder-width and aspect-ratio regimes as estimator results; accuracy, area/power, and integration remain unknown."),
    ("D22F14", "weight-compression-rle-sweep.md", "Adaptive is not universally", "qualified", "exact-bytes-not-end-to-end-cost",
     "notes/chapter-13-source-and-claim-ledger.md", "C13.20", "C13.20 | Adaptive selection compares", "codec_byte_and_estimator_cycles",
     "Retain distribution-sensitive codec alternatives and exact bytes; do not infer end-to-end latency or energy."),
    ("D22F15", "context-switch-state-scope.md", "No mode is universally preferable", "qualified", "legal-boundary-and-omitted-reload",
     "notes/chapter-18-source-and-claim-ledger.md", "C18.1", "C18.1 (verified)", "context_ledger_cycles",
     "Retain FULL/LIVE/CONTROL alternatives at a legal boundary; omitted continuation costs prevent end-to-end ranking."),
    ("D22F16", "scheduler-policy-sweep.md", "identical `estimated_cycles`", "retained", "metric-is-policy-insensitive",
     "source-audit.md", "source-audit#44", "Exact probes preserve policy-dependent order with the same serial estimate", "scheduler_serial_dag_estimate",
     "Retain the negative result for this serial estimate; it does not imply equivalent transformed behavior or compiler composition."),
    ("D22F17", "attention-engine-sweep.md", "OS dataflow wins universally.", "blocked", "attention-correctness-defect",
     "notes/chapter-14-source-and-claim-ledger.md", "C14.8/C14.9", "The attention test suite at the pin never passes 9/9", "operator_analytical_cycles",
     "Arbitrary-input performance preferences are blocked while FP16 SRAM staging is defective."),
    ("D22F18", "softmax-after-attention-pipeline.md", "Softmax overhead is substantial", "rejected", "heterogeneous-metric-composition",
     "notes/chapter-14-source-and-claim-ledger.md", "C14.2", "C14.2 (verified)", "sram_stall_returns",
     "Reject the pipeline percentage: softmax stall returns and attention analytical totals are incompatible metric domains."),
]

CYCLE_DOMAINS = {
    "linked_plugin_cycles": "linked dataflow callback estimators",
    "local_formula_cycles": "standalone report-local geometry/dataflow/DRAM/precision formulas",
    "db_ideal_overlap_formula_cycles": "ideal analytical overlap formulas",
    "db_controller_ledger_cycles": "caller-fed pipeline-controller overlap ledgers and controller clock",
    "sram_stall_returns": "softmax/normalization SRAM API return values",
    "operator_analytical_cycles": "pool/conv/attention engine-local equations",
    "dram_caller_ticked_cycles": "standalone stateful DRAM caller-ticked accounting",
    "traffic_heuristic_cycles": "isolated/shared-link interconnect heuristic estimates",
    "context_ledger_cycles": "caller-invoked retained-state transfer ledger",
    "scheduler_serial_dag_estimate": "scheduler DAG critical-path/serial estimate",
    "codec_byte_and_estimator_cycles": "codec bytes plus separately modeled DMA/decode equations",
    "precision_conversion_error_metric": "bounded numeric conversion error, not cycles",
    "noncycle_functional_or_structure": "functional/structural evidence with no elapsed-time quantity",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> tuple[int, str]:
    e = {**os.environ, "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1"}
    if env:
        e.update(env)
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, env=e, timeout=180)
    return p.returncode, p.stdout


def source_state(label: str) -> None:
    rc, out = run(["git", "status", "--porcelain=v1", "--branch"], SOURCE)
    if rc:
        raise RuntimeError(f"git status failed at {label}: {out}")
    head = run(["git", "rev-parse", "HEAD"], SOURCE)[1].strip()
    branch_rc, _ = run(["git", "symbolic-ref", "-q", "--short", "HEAD"], SOURCE)
    dirty = out.splitlines()[1:]
    print(f"SOURCE_STATE {label} head={head} detached={int(branch_rc != 0)} dirty_entries={len(dirty)}")
    if head != PIN or branch_rc == 0 or dirty:
        raise RuntimeError(f"unsafe source state at {label}: {out}")


def book_state() -> None:
    head = run(["git", "rev-parse", "HEAD"], BOOK)[1].strip()
    branch = run(["git", "symbolic-ref", "-q", "--short", "HEAD"], BOOK)[1].strip()
    tracked = run(["git", "status", "--porcelain=v1", "--untracked-files=no"], BOOK)[1].splitlines()
    print(f"BOOK_STATE head={head} branch={branch} tracked_dirty_entries={len(tracked)}")
    if head != BOOK_BASE_HEAD or branch != "main" or tracked:
        raise RuntimeError("book evidence base revision/state drifted")


def unique(text: str, anchor: str, label: str) -> None:
    count = text.count(anchor)
    if count != 1:
        raise RuntimeError(f"anchor count for {label}: expected 1 got {count}")


def inventory() -> None:
    reports = sorted(p.name for p in REPORT_ROOT.glob("*.md") if p.name != "IMPLEMENTATION_BACKLOG.md")
    report_set = set(reports)
    expected = set().union(*DOMAINS.values())
    if report_set != expected or len(reports) != 46 or sum(len(v) for v in DOMAINS.values()) != 46:
        raise RuntimeError("exact 46-report domain partition drifted")
    report_text = {name: (REPORT_ROOT / name).read_text(errors="replace") for name in reports}
    aggregate = hashlib.sha256(b"".join(
        name.encode() + b"\0" + bytes.fromhex(sha(REPORT_ROOT / name)) for name in reports
    )).hexdigest()

    print(f"PIN {PIN}")
    print(f"SCRIPT_HASH {sha(Path(__file__))} {Path(__file__).name}")
    print(f"REPORT_INVENTORY total=46 domain_count={len(DOMAINS)} exact_partition=1 aggregate_sha256={aggregate}")
    for domain, members in DOMAINS.items():
        print(f"DOMAIN {domain} count={len(members)} members={' '.join(sorted(members))}")

    report_to_domain = {member: domain for domain, members in DOMAINS.items() for member in members}
    for regime, record in REGIMES.items():
        members = record["members"]
        missing = members - report_set
        domains = {report_to_domain[x] for x in members}
        if missing or len(members) < 2 or len(domains) < 2 or not record["boundary"] or not record["break"]:
            raise RuntimeError(f"regime semantic gate failed: {regime}")
        print(f"REGIME {regime} count={len(members)} domain_count={len(domains)} members={' '.join(sorted(members))}")
        print(f"REGIME_BOUNDARY {regime} text={record['boundary']}")
        print(f"REGIME_BREAK {regime} text={record['break']}")

    high_claim = re.compile(r"(?i)\b(optimal|unambiguous|hard requirement|highest-leverage|sweet spot|strictly better|should|must|never|always|universal(?:ly)?|don't-care)\b")
    broad_composition = re.compile(r"(?i)\b(compiler|runtime|ONNX)\b")
    high_reports = sorted(name for name, text in report_text.items() if high_claim.search(text))
    composition_reports = sorted(name for name, text in report_text.items() if broad_composition.search(text))
    if len(high_reports) != 41 or len(composition_reports) != 22:
        raise RuntimeError("risk-marker inventory drifted")
    print(f"RISK_MARKERS high_recommendation_reports=41 broad_compiler_runtime_reports=22")
    print("HIGH_RECOMMENDATION_REPORTS " + " ".join(high_reports))
    print("BROAD_COMPILER_RUNTIME_REPORTS " + " ".join(composition_reports))

    evidence_texts = {}
    for rel, expected_hash in EVIDENCE_HASHES.items():
        path = BOOK / rel
        actual = sha(path)
        if actual != expected_hash:
            raise RuntimeError(f"evidence hash drift: {rel}: {actual}")
        evidence_texts[rel] = path.read_text(errors="replace")
        print(f"EVIDENCE_HASH {expected_hash} {rel}")

    statuses = {x: 0 for x in sorted(CANONICAL_STATUSES)}
    ids, report_claim_pairs = set(), set()
    used_metric_domains = set()
    for claim_id, report, report_anchor, status, reason, evidence_rel, evidence_ref, evidence_anchor, metric_domain, safe in DISPOSITIONS:
        if claim_id in ids or (report, report_anchor) in report_claim_pairs:
            raise RuntimeError(f"duplicate disposition identity: {claim_id}")
        if status not in CANONICAL_STATUSES or metric_domain not in CYCLE_DOMAINS:
            raise RuntimeError(f"uncontrolled disposition field: {claim_id}")
        unique(report_text[report], report_anchor, f"report:{claim_id}")
        unique(evidence_texts[evidence_rel], evidence_anchor, f"evidence:{claim_id}:{evidence_ref}")
        ids.add(claim_id); report_claim_pairs.add((report, report_anchor)); used_metric_domains.add(metric_domain)
        statuses[status] += 1
        print(f"DISPOSITION id={claim_id} report={report} status={status} reason={reason} evidence={evidence_rel} ref={evidence_ref} metric_domain={metric_domain} safe={safe}")

    print("DISPOSITION_STATUS_COUNTS " + " ".join(f"{k}={v}" for k, v in statuses.items()))
    print(f"DISPOSITION_COVERAGE claim_rows={len(DISPOSITIONS)} reports={len({x[1] for x in DISPOSITIONS})} evidence_surfaces={len(EVIDENCE_HASHES)} complete_claim_register=0")
    print(f"CYCLE_DOMAIN_REGISTER count={len(CYCLE_DOMAINS)} composition_allowed=0 exact_claim_mapping=1")
    for key, owner in CYCLE_DOMAINS.items():
        print(f"CYCLE_DOMAIN {key} owner={owner}")
    for claim_id, *rest in DISPOSITIONS:
        print(f"CLAIM_DOMAIN id={claim_id} metric_domain={rest[7]}")

    gates = {
        "all_reports_classified_once": report_set == expected and sum(len(v) for v in DOMAINS.values()) == 46,
        "evidence_hashes_exact": len(evidence_texts) == len(EVIDENCE_HASHES),
        "disposition_claim_ids_exact": len(ids) == len(DISPOSITIONS) == 18,
        "canonical_status_vocabulary": set(statuses) == CANONICAL_STATUSES,
        "regime_semantics_cross_domain": all(len({report_to_domain[x] for x in r["members"]}) >= 2 for r in REGIMES.values()),
        "claim_metric_domains_exact": len(used_metric_domains) >= 10 and all(x[8] in CYCLE_DOMAINS for x in DISPOSITIONS),
        "broad_compiler_runtime_risk_exact": len(composition_reports) == 22,
    }
    if os.environ.get("CH22_FRAMING_INJECT_FAILURE") == "inventory":
        gates["injected_inventory_predicate"] = False
    for name, ok in gates.items():
        print(f"PREDICATE {name}={'PASS' if ok else 'FAIL'}")
    if not all(gates.values()):
        raise RuntimeError("Chapter 22 framing predicate failed: " + ",".join(k for k, v in gates.items() if not v))


def failure_path_control() -> None:
    if os.environ.get("CH22_FRAMING_CHILD") == "1":
        return
    rc, out = run([sys.executable, str(Path(__file__).resolve())], BOOK,
                  env={"CH22_FRAMING_INJECT_FAILURE": "inventory", "CH22_FRAMING_CHILD": "1"})
    diagnostic = "Chapter 22 framing predicate failed: injected_inventory_predicate"
    after = f"SOURCE_STATE after head={PIN} detached=1 dirty_entries=0"
    ok = rc != 0 and diagnostic in out and out.count(after) == 1
    print(f"FAILURE_PATH_CONTROL inventory_predicate rc_nonzero={int(rc != 0)} diagnostic={int(diagnostic in out)} source_after_unique={int(out.count(after) == 1)} rejected={int(ok)}")
    if not ok:
        raise RuntimeError("failure-path source-preservation control failed")


def main() -> int:
    source_state("before")
    result = 1
    try:
        book_state()
        inventory()
        failure_path_control()
        result = 0
    finally:
        source_state("after")
    if result == 0:
        print("CH22_FRAMING_RECON PASS")
    return result


if __name__ == "__main__":
    sys.exit(main())
