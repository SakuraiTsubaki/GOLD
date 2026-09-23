#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={'japan_v0','japan_rev_a','korea','usa_europe','germany','france','italy','spain'}
def main():
    cfg=json.loads((ROOT/'config/original_rom_expansion.json').read_text())
    releases=json.loads((ROOT/'research/gold_release_matrix.json').read_text())
    paths=json.loads((ROOT/'research/legacy_id_path_matrix.json').read_text())
    val=json.loads((ROOT/'research/mbc30_expansion_validation.json').read_text())
    assert cfg['scope']=='original-gbc-rom'
    assert cfg['stage0']['rom_banks']==256 and cfg['stage0']['sram_banks']==8
    assert cfg['stage1']['registry_seed']['bank']==0x80
    assert cfg['stage1']['registry_seed']['master_id_bits']==16
    assert cfg['stage1']['save_v2']['mon_slots']==288
    assert cfg['stage1']['save_v2']['mon_high_payload_bytes']==1728
    assert cfg['stage1']['save_v2']['inventory_high_payload_bytes']==107
    assert {r['id'] for r in releases['releases']}==EXPECTED
    assert {r['id'] for r in paths['releases']}==EXPECTED
    assert len(paths['shared_table_hashes']['base_data'])==1
    assert len(paths['shared_table_hashes']['moves'])==1
    assert len(paths['shared_table_hashes']['item_attributes'])==1
    for r in paths['releases']:
        assert r['base_data']['entry_size']==32 and r['base_data']['entry_count']==251
        assert r['moves']['entry_size']==7 and r['moves']['entry_count']==251
        assert r['item_attributes']['entry_size']==7 and r['item_attributes']['entry_count']==256
        assert r['get_base_data_offset']>=0 and r['get_item_attr_offset']>=0
    assert len(val['results'])==8
    assert val['rom_transform']['registry_bank']==0x80
    assert val['save_transform']['mon_id_high_payload_bytes']==1728
    print('GOLD original-ROM Gen10 expansion: OK')
    print('release profiles: 8/8')
    print('shared legacy tables: 3/3 byte-identical')
    print('Stage 1: GOLDREG bank $80 + GOLD_SAVE_V2 high-byte sidecars')
    return 0
if __name__=='__main__': raise SystemExit(main())
