#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "japan_v0", "japan_rev_a", "korea", "usa_europe",
    "germany", "france", "italy", "spain",
}


def main() -> int:
    config = json.loads((ROOT / "config/original_rom_expansion.json").read_text())
    releases = json.loads((ROOT / "research/gold_release_matrix.json").read_text())
    paths = json.loads((ROOT / "research/legacy_id_path_matrix.json").read_text())
    hooks = json.loads((ROOT / "research/legacy_lookup_hook_profiles.json").read_text())
    move_hooks = json.loads((ROOT / "research/legacy_move_hook_profiles.json").read_text())
    validation = json.loads((ROOT / "research/mbc30_expansion_validation.json").read_text())

    assert config["scope"] == "original-gbc-rom"
    assert config["stage0"]["rom_banks"] == 256
    assert config["stage0"]["sram_banks"] == 8
    assert config["stage1"]["registry_seed"]["bank"] == 0x80
    assert config["stage1"]["registry_seed"]["master_id_bits"] == 16
    assert config["stage1"]["registry_seed"]["base_data_address"] == 0x4100
    assert config["stage1"]["registry_seed"]["moves_address"] == 0x6060
    assert config["stage1"]["registry_seed"]["item_attributes_address"] == 0x673D
    assert config["stage1"]["lookup_hooks"]["GetBaseData"] == "implemented-all-8"
    assert config["stage1"]["lookup_hooks"]["GetItemAttr"] == "implemented-all-8"
    assert config["stage1"]["save_v2"]["mon_slots"] == 288
    assert config["stage1"]["save_v2"]["mon_high_payload_bytes"] == 1728
    assert config["stage1"]["save_v2"]["inventory_high_payload_bytes"] == 107

    assert {r["id"] for r in releases["releases"]} == EXPECTED
    assert {r["id"] for r in paths["releases"]} == EXPECTED
    assert {r["id"] for r in hooks["releases"]} == EXPECTED
    assert {r["id"] for r in move_hooks["releases"]} == EXPECTED

    assert len(paths["shared_table_hashes"]["base_data"]) == 1
    assert len(paths["shared_table_hashes"]["moves"]) == 1
    assert len(paths["shared_table_hashes"]["item_attributes"]) == 1

    for row in paths["releases"]:
        assert row["base_data"]["entry_size"] == 32
        assert row["base_data"]["entry_count"] == 251
        assert row["moves"]["entry_size"] == 7
        assert row["moves"]["entry_count"] == 251
        assert row["item_attributes"]["entry_size"] == 7
        assert row["item_attributes"]["entry_count"] == 256
        assert row["get_base_data_offset"] >= 0
        assert row["get_item_attr_offset"] >= 0

    for hook in hooks["releases"]:
        assert hook["get_base_data"]["original_bank"] == 0x14
        assert hook["get_base_data"]["target_bank"] == 0x80
        assert hook["get_base_data"]["target_address"] == 0x4100
        assert hook["get_item_attr"]["original_bank"] == 0x01
        assert hook["get_item_attr"]["target_bank"] == 0x80
        assert hook["get_item_attr"]["target_address"] == 0x673D
        assert len(hook["output_sha1"]) == 40
        assert len(hook["output_sha256"]) == 64

    for hook in move_hooks["releases"]:
        assert hook["move_refs_patched"] == 22
        assert hook["move_bank_immediates_patched"] == 15
        if hook["id"] == "korea":
            assert len(hook["excluded_candidates"]) == 1
            assert hook["excluded_candidates"][0]["reason"] == "farcall_function_pointer"
        else:
            assert hook["excluded_candidates"] == []

    assert len(validation["results"]) == 8
    assert validation["rom_transform"]["registry_bank"] == 0x80
    assert validation["rom_transform"]["central_lookup_hooks"] == [
        "GetBaseData", "GetItemAttr", "MovesDirectPaths"
    ]
    assert validation["save_transform"]["mon_id_high_payload_bytes"] == 1728

    print("GOLD original-ROM Gen10 expansion: OK")
    print("release profiles: 8/8")
    print("Stage 1 legacy lookup hooks: Species + Moves + Items -> GOLDREG")
    print("Moves paths: 22/22 per release; Korea FarCall collision excluded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
