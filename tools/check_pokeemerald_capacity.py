#!/usr/bin/env python3
"""Audit a pokeemerald-expansion checkout for GOLD persistent-ID limits."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


def require(pattern: str, text: str, label: str) -> re.Match[str]:
    match = re.search(pattern, text)
    if not match:
        raise SystemExit(f"capacity audit failed: cannot find {label}")
    return match


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect-phase1", action="store_true")
    parser.add_argument("checkout", type=Path)
    args = parser.parse_args()

    pokemon = (args.checkout / "include/pokemon.h").read_text(encoding="utf-8")
    storage = (args.checkout / "include/pokemon_storage_system.h").read_text(encoding="utf-8")
    global_h = (args.checkout / "include/global.h").read_text(encoding="utf-8")

    species_bits = int(require(r"species:(\d+)", pokemon, "BoxPokemon species width").group(1))
    move_bits = [int(x) for x in re.findall(r"enum Move move[1-4]:(\d+)", pokemon)]
    if len(move_bits) < 4:
        raise SystemExit("capacity audit failed: expected four packed move fields")

    item_match = re.search(r"(?:enum Item|u16) heldItem(?::(\d+))?;", pokemon)
    if not item_match:
        raise SystemExit("capacity audit failed: cannot find heldItem")
    item_bits = int(item_match.group(1)) if item_match.group(1) else 16

    ball_bits = int(require(r"pokeball:(\d+)", pokemon, "Poké Ball width").group(1))
    boxes = int(require(r"#define TOTAL_BOXES_COUNT\s+(\d+)", storage, "box count").group(1))
    rows = int(require(r"#define IN_BOX_ROWS\s+(\d+)", storage, "box rows").group(1))
    cols = int(require(r"#define IN_BOX_COLUMNS\s+(\d+)", storage, "box columns").group(1))

    sidecar_present = "struct GoldBoxMonSidecar goldBoxMonSidecar;" in global_h

    print(f"species_bits={species_bits}")
    print(f"move_bits={move_bits[:4]}")
    print(f"held_item_bits={item_bits}")
    print(f"pokeball_bits={ball_bits}")
    print(f"boxed_slots={boxes * rows * cols}")
    print(f"gold_sidecar_present={sidecar_present}")

    failures: list[str] = []

    if args.expect_phase1:
        if item_bits != 16:
            failures.append(f"Phase 1 requires 16-bit heldItem, got {item_bits}")
        if ball_bits < 8:
            failures.append(f"Phase 1 requires >=8-bit pokeball, got {ball_bits}")
        if not sidecar_present:
            failures.append("Generation 10 sidecar reservation is missing")

    if species_bits < 16:
        print("NEXT: Species still requires Phase 2 accessor/serialization migration")
    if any(bits < 16 for bits in move_bits[:4]):
        print("NEXT: Move IDs still require Phase 2 accessor/serialization migration")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1

    print("GOLD capacity audit: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
