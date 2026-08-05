# Chapter 17 — Measurement Primary-Source Ledger

This ledger supplies external context only. Pinned Tusim source and retained executable evidence remain authoritative for Tusim behavior.

## IEEE VCD

- **Source:** IEEE Std 1800-2023, *IEEE Standard for SystemVerilog—Unified Hardware Design, Specification, and Verification Language*, clause 21.7, “Value change dump (VCD) files.” IEEE publication record: https://ieeexplore.ieee.org/document/10458102 ; DOI: https://doi.org/10.1109/IEEESTD.2024.10458102 .
- **Authority:** normative standard. IEEE 1800-2023 is the current consolidated SystemVerilog standard; Tusim's source label “IEEE 1364-2001” names an older Verilog edition rather than the latest normative record.
- **Bounded support:** clause 21.7 defines VCD as an ASCII representation of selected simulation variables, with declaration commands, simulation time values, and value changes. The grammar uses `#` followed by an unsigned time number; dump commands and value changes are ordered in the file. A `$timescale` declaration defines the file time unit.
- **Scope guard:** syntactic VCD conformance does not establish that a producer observed complete hardware state, that its integer tick corresponds to physical nanoseconds, or that two VCD producers share a clock. Tusim's first-tick behavior, schemas, omissions, and caller ownership remain implementation questions.
- **Verification path:** IEEE/Crossref metadata plus inspection of clause 21.7 in an IEEE 1800-2023 copy. Do not cite an unrelated mirror as the authority; use the IEEE record above.

## Horowitz ISSCC energy examples

- **Source:** Mark Horowitz, “1.1 Computing's energy problem (and what we can do about it),” *2014 IEEE International Solid-State Circuits Conference Digest of Technical Papers*, pp. 10–14. DOI: https://doi.org/10.1109/ISSCC.2014.6757323 ; IEEE record: https://ieeexplore.ieee.org/document/6757323 .
- **Authority:** primary invited/plenary conference paper.
- **Bounded support:** the paper presents order-of-magnitude energy comparisons for arithmetic, memory access, communication, and voltage/process choices under the paper's stated assumptions. It supports the architectural lesson that data movement can dominate arithmetic and that operation energy is technology/design dependent.
- **Scope guard:** the paper does not calibrate Tusim's FP16 MAC, SRAM, DRAM, DMA, node-scaling, area, leakage, or clock tables. A cited 32-bit operation at a stated node cannot be relabeled as a Tusim FP16 MAC parameter without a documented transformation and validation record.

## CACTI 7.x first-party artifact

- **Source:** Hewlett Packard Enterprise's CACTI repository: https://github.com/HewlettPackard/cacti . The first-party `version_cacti.h` on `master` declares `VER_MAJOR_CACTI 7`, `VER_MINOR_CACTI 0`, `VER_COMMENT_CACTI "3DD Prerelease"`, and `VER_UPDATE_CACTI "Aug, 2012"`: https://github.com/HewlettPackard/cacti/blob/master/version_cacti.h .
- **Authority:** first-party implementation repository, not a normative standard.
- **Bounded support:** CACTI is a cache/memory access-time, cycle-time, area, leakage, and dynamic-power modeling tool with explicit configuration inputs. Its existence supports a reproducible characterization workflow when exact version, inputs, outputs, and mapping are retained.
- **Scope guard:** a source comment saying “CACTI-derived” is not a reproducible CACTI result. The Tusim tree contains no retained CACTI invocation, configuration, raw output, table-generation script, or row-by-row mapping to `tech_node_table`; therefore the pinned constants are hardcoded estimates of undocumented provenance. The first-party repository also labels this 7.0 header a prerelease, which makes an unqualified “CACTI 7.0 calibration” claim especially unsafe.

## Performance-counter interval semantics

- **Optional vendor context:** Arm Architecture Reference Manual for A-profile architecture, Performance Monitors Extension / PMU chapters, official landing page: https://developer.arm.com/documentation/ddi0487/latest/ .
- **Authority:** vendor architecture specification for Arm PMUs only.
- **Bounded support:** hardware event counters have selected event definitions, enable/filter state, width/overflow behavior, and explicit counting intervals; software must read/configure them consistently before comparing rates.
- **Scope guard:** Arm PMU events do not define Tusim events, clocks, reset semantics, or fidelity. This source is useful only for the general discipline that a counter value is inseparable from event and interval configuration.

## Safe chapter use

1. Use IEEE 1800 only for VCD syntax/semantics, not Tusim timing fidelity.
2. Use Horowitz only for architecture-level energy motivation and uncertainty, not parameter transfer.
3. Use the HPE CACTI repository to define what reproducible characterization would require, while explicitly recording that Tusim retains no such artifact.
4. Use vendor PMU documentation only as vendor-scoped background for event/interval contracts.
5. Every Tusim number still requires its pinned producer, caller, interval, unit, clock, and executable limitation.
