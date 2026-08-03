#!/usr/bin/env python3
"""Report and optionally enforce Chapter 4's pinned Tusim config-surface audit."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
import re
import subprocess
import tempfile
from pathlib import Path

PINNED_COMMIT = "e918c80b6fce833cd1fcae97730fa841c2176f25"
EXPECTED_HASHES = {
    "config/tu_config.yaml": "9fb4d87753139a5857107a6fdf56006fcb5adbe95ad30e9f8430c2e5c145910e",
    "config/tu_config.json": "6f9d292696b1ca5fa38ad3298e7f3a04c43095c0950f71dbe0c3c68b1f15f4db",
    "scripts/gen_config.py": "5eab235067eaf6d5785352e48ef00417a18f5b0d05b25f40a82719e11bf8634a",
    "tu_cmodel/tu_config.h": "129d55ad55409bcd4b5dcae5007faa297c087d48a150a4a85073d66e49cbb45d",
    "tu_cmodel/infra/config.h": "723deb631e83705ab80143dd251761c3b98ca692c5d1eefb243d47aca551913b",
    "tu_cmodel/infra/config.c": "17b7919392d4a315022a129ce5bbdff301a2d3405af3163756b430b2b36dd12a",
    "docs/CONFIG_REFERENCE.md": "040b4918247e9a98a3c10ca44f3b32b1c9893ce741f93f6a4d78863b6c921ecc",
}
EXPECTED_GENERATED_HASH = "e41dcf622c43a7898d0e21d83d870d884f3e781bd207fa8828f8788e7cf1051a"
EXPECTED_UNDOCUMENTED = {
    "dram_latency_read", "dram_latency_write", "gbuf_bank_width", "log_level", "trace_file"
}
EXPECTED_JSON_ONLY = {
    "tu.dma.multicast_enabled",
    "tu.weight_compression.enabled",
    "tu.weight_compression.type",
    "tu.weight_compression.rle_epsilon",
    "tu.weight_compression.decoder_enabled",
    "tu.weight_compression.decoder_overlap_dma",
    "tu.weight_compression.decoder_elements_per_cycle",
    "tu.weight_compression.rle_runs_per_cycle",
    "tu.weight_compression.bitmap_elements_per_cycle",
}


def flatten(value, prefix=""):
    out = {}
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            out.update(flatten(child, path))
    elif isinstance(value, list):
        out[prefix] = tuple(value)
    else:
        out[prefix] = value
    return out


def empty_mappings(value, prefix=""):
    out = []
    if isinstance(value, dict):
        if prefix and not value:
            out.append(prefix)
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            out.extend(empty_mappings(child, path))
    return out


def quoted_empty_scalar_paths(text: str):
    """Recover quoted empty scalars that Tusim's ad-hoc parser turns into mappings."""
    stack: list[tuple[int, str]] = []
    paths: list[str] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        match = re.match(r"^(\s*)([^:#]+):\s*(.*)$", raw)
        if not match:
            continue
        indent = len(match.group(1))
        key = match.group(2).strip()
        value = match.group(3).split("#", 1)[0].strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        path = ".".join([item[1] for item in stack] + [key])
        if value in {'""', "''"}:
            paths.append(path)
        elif value == "":
            stack.append((indent, key))
    return paths


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str, failures: list[str]):
    if not condition:
        failures.append(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tusim_root", type=Path)
    parser.add_argument("--check", action="store_true", help="enforce the pinned snapshot's expected report")
    args = parser.parse_args()
    root = args.tusim_root.resolve()

    generator_path = root / "scripts/gen_config.py"
    spec = importlib.util.spec_from_file_location("tusim_gen_config", generator_path)
    assert spec and spec.loader
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    yaml_path = root / "config/tu_config.yaml"
    json_path = root / "config/tu_config.json"
    header_path = root / "tu_cmodel/tu_config.h"
    config_h_path = root / "tu_cmodel/infra/config.h"
    config_c_path = root / "tu_cmodel/infra/config.c"
    docs_path = root / "docs/CONFIG_REFERENCE.md"

    yaml_text = yaml_path.read_text()
    yaml_parsed = generator.load_yaml_simple(yaml_path)
    yaml_parser_flat = flatten(yaml_parsed)
    yaml_empty_mappings = empty_mappings(yaml_parsed)
    quoted_empty = quoted_empty_scalar_paths(yaml_text)
    yaml_textual_flat = dict(yaml_parser_flat)
    for key in quoted_empty:
        yaml_textual_flat[key] = ""

    json_flat = flatten(json.loads(json_path.read_text()))
    yaml_only = sorted(set(yaml_textual_flat) - set(json_flat))
    json_only = sorted(set(json_flat) - set(yaml_textual_flat))
    different = sorted(
        key for key in set(yaml_textual_flat) & set(json_flat)
        if yaml_textual_flat[key] != json_flat[key]
    )

    config_h = config_h_path.read_text()
    struct_match = re.search(r"typedef struct tu_config_t \{(.*?)\n\} tu_config_t;", config_h, re.S)
    assert struct_match
    full_fields = re.findall(
        r"^\s*(?:bool|int|double|uint8_t|uint16_t|uint32_t|uint64_t|char)\s+([A-Za-z_]\w*)",
        struct_match.group(1), re.M,
    )

    config_c = config_c_path.read_text()
    conversion_match = re.search(r"tu_config_to_runtime\([^)]*\) \{(.*?)\n\}", config_c, re.S)
    assert conversion_match
    converted_sources = re.findall(r"rt\.\w+\s*=\s*cfg->(\w+)", conversion_match.group(1))
    converted_sources.extend(re.findall(r"memcpy\([^;]*cfg->(\w+)", conversion_match.group(1)))
    dropped = sorted(set(full_fields) - set(converted_sources))

    doc_fields = set(re.findall(r"^\| `([A-Za-z_]\w*)` \|", docs_path.read_text(), re.M))
    undocumented = set(full_fields) - doc_fields

    with tempfile.TemporaryDirectory(prefix="tusim-ch04-") as tmp:
        generated = Path(tmp) / "tu_config.h"
        generator.generate_header(generator.load_yaml_simple(yaml_path), generated)
        tracked_lines = header_path.read_text().splitlines()
        generated_lines = generated.read_text().splitlines()
        diff = list(difflib.unified_diff(generated_lines, tracked_lines))
        generated_hash = sha256(generated)

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True
    ).stdout.strip()

    print(f"source_commit={commit}")
    print(f"yaml_parser_visible_leaf_fields={len(yaml_parser_flat)}")
    print(f"yaml_textual_leaf_fields={len(yaml_textual_flat)}")
    print(f"yaml_parser_empty_mappings={len(yaml_empty_mappings)}")
    for key in yaml_empty_mappings:
        print(f"  YAML_EMPTY_MAPPING {key}")
    print(f"yaml_quoted_empty_scalars={len(quoted_empty)}")
    for key in quoted_empty:
        print(f"  YAML_QUOTED_EMPTY {key}")
    print(f"json_leaf_fields={len(json_flat)}")
    print(f"yaml_only={len(yaml_only)}")
    for key in yaml_only:
        print(f"  YAML_ONLY {key}={yaml_textual_flat[key]!r}")
    print(f"json_only={len(json_only)}")
    for key in json_only:
        print(f"  JSON_ONLY {key}={json_flat[key]!r}")
    print(f"different_shared_values={len(different)}")
    for key in different:
        print(f"  VALUE_DIFF {key}: yaml={yaml_textual_flat[key]!r} json={json_flat[key]!r}")
    print(f"tu_config_t_fields={len(full_fields)}")
    print(f"conversion_source_fields={len(set(converted_sources))}")
    print(f"dropped_before_tu_runtime_config={len(dropped)}")
    print("  DROPPED " + ", ".join(dropped))
    print(f"documented_struct_fields={len(doc_fields)}")
    print(f"undocumented_struct_fields={len(undocumented)}")
    print("  UNDOCUMENTED " + ", ".join(sorted(undocumented)))
    print(f"tracked_header_sha256={sha256(header_path)}")
    print(f"generated_header_sha256={generated_hash}")
    print(f"generated_header_matches_tracked={not diff}")
    print(f"generated_vs_tracked_diff_lines={len(diff)}")

    if not args.check:
        return 0

    failures: list[str] = []
    require(commit == PINNED_COMMIT, f"commit: expected {PINNED_COMMIT}, got {commit}", failures)
    for relative, expected in EXPECTED_HASHES.items():
        actual = sha256(root / relative)
        require(actual == expected, f"hash {relative}: expected {expected}, got {actual}", failures)
    require(len(yaml_parser_flat) == 65, "generator parser-visible YAML leaf count changed", failures)
    require(len(yaml_textual_flat) == 66, "textual YAML leaf count changed", failures)
    require(set(yaml_empty_mappings) == {"tu.performance.tracing.output_file"}, "empty-mapping defect set changed", failures)
    require(set(quoted_empty) == {"tu.performance.tracing.output_file"}, "quoted-empty YAML set changed", failures)
    require(len(json_flat) == 75, "JSON leaf count changed", failures)
    require(set(yaml_only) == set(), "unexpected YAML-only fields", failures)
    require(set(json_only) == EXPECTED_JSON_ONLY, "JSON-only field set changed", failures)
    require(different == ["tu.performance.cycle_model"], "shared-value conflict set changed", failures)
    require(len(full_fields) == 76 and len(set(full_fields)) == 76, "tu_config_t field extraction changed", failures)
    require(len(set(converted_sources)) == 16, "conversion source-field count changed", failures)
    require(len(dropped) == 60, "dropped source-field count changed", failures)
    require(len(doc_fields) == 71, "documented field count changed", failures)
    require(undocumented == EXPECTED_UNDOCUMENTED, "undocumented field set changed", failures)
    require(generated_hash == EXPECTED_GENERATED_HASH, "fresh generated-header hash changed", failures)
    require(len(diff) == 181 and bool(diff), "expected generated/tracked header mismatch changed", failures)

    if failures:
        for failure in failures:
            print(f"CHECK_FAIL {failure}")
        return 1
    print("check_status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
