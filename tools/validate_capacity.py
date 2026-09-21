#!/usr/bin/env python3
"""Validate GOLD's future-generation capacity contract."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "engine_capacity.json"
REQUIRED_REGISTRIES = {
    "species",
    "variety",
    "form",
    "move",
    "item",
    "ability",
    "type",
    "evolution_method",
    "resource",
    "feature",
}


def fail(message: str) -> None:
    raise SystemExit(f"capacity validation failed: {message}")


def main() -> int:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))

    if data.get("target_generation", 0) < 10:
        fail("target_generation must be at least 10")

    policy = data.get("policy", {})
    if not policy.get("append_only_ids"):
        fail("append-only IDs must remain enabled")
    if policy.get("guess_unreleased_content"):
        fail("unreleased content must not be guessed")

    master = data.get("master_id", {})
    if master.get("bits") != 16:
        fail("master IDs must be 16-bit")
    if master.get("min_normal") != 1 or master.get("max_normal") != 65535:
        fail("normal master ID range must remain 1..65535")

    registries = data.get("registries", {})
    missing = REQUIRED_REGISTRIES - set(registries)
    if missing:
        fail(f"missing registries: {', '.join(sorted(missing))}")

    for name in sorted(REQUIRED_REGISTRIES):
        spec = registries[name]
        if spec.get("bits") != 16:
            fail(f"{name} must use a 16-bit master ID")
        if not spec.get("append_only"):
            fail(f"{name} must be append-only")

    resource = data.get("resource_directory", {})
    if resource.get("resource_id_bits") != 16:
        fail("resource IDs must be 16-bit")
    if resource.get("bank_field_bits", 0) < 16:
        fail("resource bank field must be at least 16-bit")
    if not resource.get("mapper_agnostic"):
        fail("resource directory must stay mapper-agnostic")

    save = data.get("save", {})
    if not save.get("versioned_blocks"):
        fail("save format must use versioned blocks")
    if not save.get("legacy_import_required"):
        fail("legacy save import path is required")

    print("GOLD capacity contract: OK")
    print("Generation target: 10+")
    print("Master ID space: 16-bit / 1..65535")
    print("Registries:", ", ".join(sorted(REQUIRED_REGISTRIES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
