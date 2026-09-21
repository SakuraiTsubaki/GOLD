#!/usr/bin/env python3
"""Audit a pokeemerald-expansion checkout for GOLD persistent-ID limits."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


EXPECTED_REF = "75b806a3ab57a81ff1eb6179288981f0b3cc3050"


def require(pattern: str, text: str, label: str) -> re.Match[str]:
    match = re.search(pattern, text)
    if not match:
        raise SystemExit(f"capacity audit failed: cannot find {label}")
    return match


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkout", type=Path)
    args = parser.parse_args()

    pokemon = (args.checkout / "include/pokemon.h").read_text(encoding="utf-8")
    storage = (args.checkout / "include/pokemon_storage_system.h").read_text(encoding="utf-8")

    species_bits = int(require(r"species:(\d+)", pokemon, "BoxPokemon species width").group(1))
    move_bits = [
        int(x) for x in re.findall(r"enum Move move[1-4]:(\d+)", pokemon)
    ]
    item_match = re.search(r"(?:enum Item|u16) heldItem(?::(\d+))?;", pokemon)
    if not item_match:
        raise SystemExit("capacity audit failed: cannot find heldItem")
    item_bits = int(item_match.group(1)) if item_match.group(1) else 16
    ball_bits = int(require(r"pokeball:(\d+)", pokemon, "Poké Ball width").group(1))

    boxes = int(require(r"#define TOTAL_BOXES_COUNT\s+(\d+)", storage, "box count").group(1))
    rows = int(require(r"#define IN_BOX_ROWS\s+(\d+)", storage, "box rows").group(1))
    cols = int(require(r"#define IN_BOX_COLUMNS\s+(\d+)", storage, "box columns").group(1))

    print(f"species_bits={species_bits}")
    print(f"move_bits={move_bits}")
    print(f"held_item_bits={item_bits}")
    print(f"pokeball_bits={ball_bits}")
    print(f"boxed_slots={boxes * rows * cols}")

    if item_bits < 16:
        print("ACTION: apply GOLD Phase 1 held-item patch")
    if ball_bits < 8:
        print("ACTION: apply GOLD Phase 1 Poké Ball patch")
    if species_bits < 16 or any(bits < 16 for bits in move_bits):
        print("ACTION: Phase 2 serializer/save-sector design still required")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
