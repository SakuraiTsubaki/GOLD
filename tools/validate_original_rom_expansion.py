#!/usr/bin/env python3
"""Validate GOLD original-ROM expansion metadata without requiring copyrighted ROMs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "original_rom_expansion.json"
MATRIX = ROOT / "research" / "gold_release_matrix.json"

EXPECTED_RELEASES = {
    "japan_v0", "japan_rev_a", "korea", "usa_europe",
    "germany", "france", "italy", "spain",
}


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    assert config["scope"] == "original-gbc-rom"
    assert config["stage0"]["rom_bytes"] == 4 * 1024 * 1024
    assert config["stage0"]["rom_banks"] == 256
    assert config["stage0"]["sram_bytes"] == 64 * 1024
    assert config["stage0"]["sram_banks"] == 8
    assert config["stage0"]["rtc_preserved"] is True
    assert config["logical_ids"]["bits"] == 16

    ids = {release["id"] for release in matrix["releases"]}
    assert ids == EXPECTED_RELEASES
    assert matrix["release_count"] == 8

    for release in matrix["releases"]:
        assert release["bank_switch_offset"] == 0x10
        assert release["rom_sha1"]
        assert release["rom_sha256"]
        assert release["save_sha1"]
        assert release["save_sha256"]

    korea = next(r for r in matrix["releases"] if r["id"] == "korea")
    assert korea["mbc30_patch"]["offset"] == 0x317C
    assert korea["mbc30_patch"]["before"] == 4
    assert korea["mbc30_patch"]["after"] == 8

    print("GOLD original-ROM expansion metadata: OK")
    print("release profiles: 8/8")
    print("Stage 0: MBC30-class 4 MiB ROM / 64 KiB SRAM / RTC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
