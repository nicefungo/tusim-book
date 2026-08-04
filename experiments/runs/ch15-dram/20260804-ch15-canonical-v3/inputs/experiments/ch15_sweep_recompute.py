#!/usr/bin/env python3
"""Recompute selected claims in the pinned historical DRAM type×clock report."""
from pathlib import Path
import math, sys

if len(sys.argv) != 2:
    raise SystemExit("usage: ch15_sweep_recompute.py <dram-type-clock-sweep.md>")
report = Path(sys.argv[1]).read_text()
bytes_total = 196_608
compute_cycles = 16_416
ops = 8_388_608
bus_bpc = 32.0
bws = {"HBM2": 256.0, "DDR5": 51.2, "DDR4": 25.6}

def calc(bw, ghz):
    eff = min(bus_bpc, bw / ghz)
    dma = bytes_total / eff
    total = compute_cycles + dma
    tops = ops * ghz / total / 1000.0  # ops and GHz -> 1e9 / 1e12
    ideal_total = compute_cycles + bytes_total / bus_bpc
    ideal_tops = ops * ghz / ideal_total / 1000.0
    loss = (ideal_tops - tops) / ideal_tops * 100.0
    share = dma / total * 100.0
    return eff, dma, total, tops, loss, share

expected_strings = {
    "HBM2": "| HBM2      | 0.093    | 0.186   | 0.372   | 0.744   | 1.487   | **2.839** |",
    "DDR5": "| DDR5      | 0.093    | 0.186   | 0.372   | **0.696** | **1.056** | **0.776** |",
    "DDR4": "| DDR4      | 0.093    | 0.186   | **0.348** | **0.528** | **0.712** | **0.435** |",
}
for name, needle in expected_strings.items():
    assert needle in report, f"pinned report row drift: {name}"

values = {}
for name, bw in bws.items():
    values[name] = calc(bw, 8.0)
    eff, dma, total, tops, loss, share = values[name]
    print(f"RECOMPUTE {name} 8GHz eff={eff:.1f} dma={dma:.0f} total={total:.0f} tops={tops:.3f} loss={loss:.1f}% dma_share={share:.1f}%")

# Table claims are materially inconsistent with its own stated formula/constants.
assert math.isclose(values["HBM2"][3], 2.9749, rel_tol=2e-4)
assert math.isclose(values["DDR5"][3], 1.4239, rel_tol=2e-4)
assert math.isclose(values["DDR4"][3], 0.8620, rel_tol=2e-4)
assert "DRAM type is a don't-care — DDR4, DDR5, and HBM all deliver identical performance" in report
_, _, _, ddr4_1_tops, ddr4_1_loss, _ = calc(bws["DDR4"], 1.0)
print(f"RECOMPUTE DDR4 1GHz tops={ddr4_1_tops:.3f} loss={ddr4_1_loss:.1f}% conclusion_identical=false")
assert ddr4_1_loss > 6.0
print("SWEEP_RECOMPUTE PASS contradictions=4 historical_report_not_decision_evidence=yes")
