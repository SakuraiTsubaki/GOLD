#!/usr/bin/env python3
"""Expand supported original Pokémon Gold ROM/SAV files for GOLD.

Stage 0 expands the original MBC3 layout to an MBC30-class 4 MiB ROM / 64 KiB
SRAM target while retaining RTC semantics.

Stage 1 seeds the canonical 16-bit GOLDREG registries in ROM bank $80, initializes
GOLD_SAVE_V2 high-byte sidecars in SRAM banks 4..7, and redirects the two
well-understood central legacy lookup paths (GetBaseData and GetItemAttr) to
GOLDREG without changing their legacy 8-bit ID semantics yet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

ROM_TARGET = 4 * 1024 * 1024
ROM_SIZE_CODE_4MIB = 0x07
RAM_SIZE_CODE_64KIB = 0x05
CART_MBC3_RTC_RAM_BATTERY = 0x10
SRAM_32K = 0x8000
SRAM_64K = 0x10000
RTC_TRAILER = 0x2C
BANKSWITCH_SIGNATURE = bytes.fromhex("e0 9f ea 00 20 c9")

SAVE_V2_MAGIC = b"GOLDV2\0\0"
SAVE_V2_FORMAT_VERSION = 2
SAVE_V2_SCHEMA_VERSION = 1
SAVE_V2_HEADER_SIZE = 0x20
SAVE_V2_DIRECTORY_OFFSET = 0x20
SAVE_V2_DIRECTORY_ENTRY_SIZE = 12
SAVE_V2_MON_HIGH_OFFSET = 0x100
SAVE_V2_MON_SLOTS = 288
SAVE_V2_MON_HIGH_BYTES_PER_SLOT = 6
SAVE_V2_MON_HIGH_LENGTH = SAVE_V2_MON_SLOTS * SAVE_V2_MON_HIGH_BYTES_PER_SLOT
SAVE_V2_INV_HIGH_OFFSET = 0x800
SAVE_V2_INV_HIGH_LENGTH = 20 + 50 + 12 + 25
BLOCK_MON_ID_HIGH = 1
BLOCK_INVENTORY_ITEM_HIGH = 2

REGISTRY_BANK = 0x80
REGISTRY_PHYS = REGISTRY_BANK * 0x4000
REGISTRY_MAGIC = b"GOLDREG\0"
REGISTRY_DIRECTORY_OFFSET = 0x40
REGISTRY_ENTRY_SIZE = 16
REGISTRY_DATA_OFFSET = 0x100
REGISTRY_SPECIES = 1
REGISTRY_MOVES = 2
REGISTRY_ITEMS = 3

BASE_DATA_SIZE = 251 * 32
MOVES_DATA_SIZE = 251 * 7
ITEM_DATA_SIZE = 256 * 7

REGISTRY_BASE_ADDR = 0x4000 + REGISTRY_DATA_OFFSET
REGISTRY_MOVES_ADDR = REGISTRY_BASE_ADDR + BASE_DATA_SIZE
REGISTRY_ITEMS_ADDR = REGISTRY_MOVES_ADDR + MOVES_DATA_SIZE

BASE_DATA_SHA256 = "dccd0f065a1ccba8ee1a1b7dbee960574499262a2739f46f67fa2f7e686654ac"
MOVES_SHA256 = "e84da1c005921f4352d9bbd83bd5a5885a12b0bbdcfd9ddc14c8ceb50c42670e"
ITEM_ATTRIBUTES_SHA256 = "34ef5e76d33d6a92dfc85d55afbefc9bedd5d79c5de4feac1b5001f1d14a74d5"

BASE_LOOKUP_PATTERN = [
    0xC5, 0xD5, 0xE5, 0xF0, None, 0xF5, 0x3E, None, 0xD7,
    0xFA, None, None, 0xFE, 0xFD, 0x28, None, 0x3D, 0x01, 0x20,
    0x00, 0x21, None, None, 0xCD, None, None, 0x11, None, None,
    0x01, 0x20, 0x00, 0xCD, None, None,
]
ITEM_LOOKUP_PATTERN = [
    0xE5, 0xC5, 0x21, None, None, 0x4F, 0x06, 0x00, 0x09, 0xAF,
    0xEA, None, None, 0xFA, None, None, 0x3D, 0x4F, 0x3E, 0x07,
    0xCD, None, None, 0x3E, 0x01, 0xCD, None, None, 0xC1, 0xE1,
    0xC9,
]
MOVE_PREFIX = bytes([1, 0, 40, 0, 255, 35, 0, 2, 0, 50, 1, 255, 25, 0])

RELEASES = {
    "8814f1039450a5d3684b1389f588ccd7ee7c3436": {
        "id": "japan_v0", "profile_id": 1, "rom_bytes": 0x100000,
        "save_sha1": "ecdd363a4c4e64c956a483547f6b1a5ef1bc8ec4",
        "sram_sha1": "c05322715b9b204590ade3637a471446907afffb",
    },
    "a222402235d484ee8e39f3f31bae57cf13daf585": {
        "id": "japan_rev_a", "profile_id": 2, "rom_bytes": 0x100000,
        "save_sha1": "3fc59f3d4bcbbfc1a0ff385a658ef434951289c8",
        "sram_sha1": "290973b7d6561b0d4cc457feaf5b150efd368e62",
    },
    "c0ff3999e1093e1af59ef3eea3f1bfd7c1f18a65": {
        "id": "korea", "profile_id": 3, "rom_bytes": 0x200000,
        "save_sha1": "7a00c2f8a10a456ea22262ccd7d150703712d41e",
        "sram_sha1": "a5d57a4236c83e003445b8c401f3e0399816a23d",
        "patches": [{
            "offset": 0x317C, "before": 0x04, "after": 0x08,
            "reason": "OpenSRAM bank bound 4->8 for MBC30 SRAM banks",
        }],
    },
    "d8b8a3600a465308c9953dfa04f0081c05bdcb94": {
        "id": "usa_europe", "profile_id": 4, "rom_bytes": 0x200000,
        "save_sha1": "6fbf7312c9c0257857f5a5819325116b5cf7d063",
        "sram_sha1": "04667489b08e8532632a178f2677ac01089a2ff1",
    },
    "9254195d461ea942eaaa08cc4b83de3cf82aea0d": {
        "id": "germany", "profile_id": 5, "rom_bytes": 0x200000,
        "save_sha1": "54872724841b6d6bbede97b3315ca4efd2af123a",
        "sram_sha1": "b5ec4a3de2dd37cddbbd182bdd5366ee8ce5de02",
    },
    "c147c0d8c2b71b7628a7233436f5c052b5b17081": {
        "id": "france", "profile_id": 6, "rom_bytes": 0x200000,
        "save_sha1": "9d9cf301dbaac80c7903e1bf12295ee9cc3598f9",
        "sram_sha1": "0f316f58fa0b142d8e24a239b0dda487d3cef4dd",
    },
    "032608fe8947b627584a4a0eccc7bf9ad3588426": {
        "id": "italy", "profile_id": 7, "rom_bytes": 0x200000,
        "save_sha1": "d7584c6021cebb6b4d5fd100008361cb6b44a11b",
        "sram_sha1": "3b427b3bf452c17d4e4ed081df4307961215f8a5",
    },
    "162ea54c6a3cff374642e6dd842f9bffac847e7b": {
        "id": "spain", "profile_id": 8, "rom_bytes": 0x200000,
        "save_sha1": "602be21c5e85f164dc759af576b4cff21cf5082a",
        "sram_sha1": "531ca2fe4e6248e88ffe9518cb74ea41fd28fbca",
    },
}
SAVE_RELEASES = {p["save_sha1"]: p for p in RELEASES.values()}
SRAM_RELEASES = {p["sram_sha1"]: p for p in RELEASES.values()}


def sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def find_wild(data: bytes, pattern: list[int | None]) -> list[int]:
    return [
        i for i in range(len(data) - len(pattern) + 1)
        if all(value is None or data[i + j] == value for j, value in enumerate(pattern))
    ]


def header_checksum(data: bytes) -> int:
    value = 0
    for byte in data[0x134:0x14D]:
        value = (value - byte - 1) & 0xFF
    return value


def global_checksum(data: bytes) -> int:
    return (sum(data[:0x14E]) + sum(data[0x150:])) & 0xFFFF


def validate_header(data: bytes) -> None:
    if header_checksum(data) != data[0x14D]:
        raise ValueError("bad input header checksum")
    if global_checksum(data) != int.from_bytes(data[0x14E:0x150], "big"):
        raise ValueError("bad input global checksum")


def fix_checksums(buf: bytearray) -> None:
    buf[0x14D] = header_checksum(buf)
    buf[0x14E:0x150] = b"\0\0"
    buf[0x14E:0x150] = global_checksum(buf).to_bytes(2, "big")


def identify_rom(data: bytes) -> dict:
    digest = sha1(data)
    if digest not in RELEASES:
        raise ValueError(f"unsupported Gold ROM SHA-1: {digest}")
    return dict(RELEASES[digest], sha1=digest)


def identify_save(data: bytes) -> dict:
    full_digest = sha1(data)
    sram_digest = sha1(data[:SRAM_32K])
    profile = SAVE_RELEASES.get(full_digest) or SRAM_RELEASES.get(sram_digest)
    if not profile:
        raise ValueError(
            f"unsupported Gold SAVE (full={full_digest}, sram={sram_digest})"
        )
    return profile


def make_directory_entry(
    block_type: int,
    version: int,
    offset: int,
    length: int,
    payload: bytes,
    flags: int = 0,
) -> bytes:
    return struct.pack(
        "<HHHHHH",
        block_type,
        version,
        offset,
        length,
        crc16_ccitt(payload),
        flags,
    )


def build_save_v2_extension(profile_id: int, legacy_sram: bytes) -> bytes:
    ext = bytearray(0x8000)
    mon = bytes(SAVE_V2_MON_HIGH_LENGTH)
    inventory = bytes(SAVE_V2_INV_HIGH_LENGTH)

    ext[SAVE_V2_MON_HIGH_OFFSET:SAVE_V2_MON_HIGH_OFFSET + len(mon)] = mon
    ext[SAVE_V2_INV_HIGH_OFFSET:SAVE_V2_INV_HIGH_OFFSET + len(inventory)] = inventory

    directory = b"".join([
        make_directory_entry(
            BLOCK_MON_ID_HIGH,
            1,
            SAVE_V2_MON_HIGH_OFFSET,
            len(mon),
            mon,
        ),
        make_directory_entry(
            BLOCK_INVENTORY_ITEM_HIGH,
            1,
            SAVE_V2_INV_HIGH_OFFSET,
            len(inventory),
            inventory,
        ),
    ])
    ext[SAVE_V2_DIRECTORY_OFFSET:SAVE_V2_DIRECTORY_OFFSET + len(directory)] = directory

    struct.pack_into(
        "<8sHHHHHHHH",
        ext,
        0,
        SAVE_V2_MAGIC,
        SAVE_V2_FORMAT_VERSION,
        SAVE_V2_SCHEMA_VERSION,
        profile_id,
        2,
        SAVE_V2_DIRECTORY_OFFSET,
        0x8000,
        crc16_ccitt(legacy_sram),
        0,
    )

    header = bytearray(ext[:SAVE_V2_HEADER_SIZE])
    header[22:24] = b"\0\0"
    struct.pack_into("<H", ext, 22, crc16_ccitt(header))
    return bytes(ext)


def parse_save_v2_extension(ext: bytes) -> dict:
    if len(ext) < 0x8000:
        raise ValueError("extension too small")

    (
        magic,
        format_version,
        schema_version,
        profile_id,
        directory_count,
        directory_offset,
        extension_bytes,
        legacy_crc,
        header_crc,
    ) = struct.unpack_from("<8sHHHHHHHH", ext, 0)

    header = bytearray(ext[:SAVE_V2_HEADER_SIZE])
    header[22:24] = b"\0\0"

    if magic != SAVE_V2_MAGIC or crc16_ccitt(header) != header_crc:
        raise ValueError("invalid GOLD_SAVE_V2 header")

    entries = []
    for index in range(directory_count):
        offset = directory_offset + index * SAVE_V2_DIRECTORY_ENTRY_SIZE
        block_type, version, payload_offset, payload_length, payload_crc, flags = (
            struct.unpack_from("<HHHHHH", ext, offset)
        )
        payload = ext[payload_offset:payload_offset + payload_length]
        entries.append({
            "type": block_type,
            "version": version,
            "offset": payload_offset,
            "length": payload_length,
            "crc16": payload_crc,
            "crc_ok": crc16_ccitt(payload) == payload_crc,
            "flags": flags,
        })

    return {
        "format_version": format_version,
        "schema_version": schema_version,
        "profile_id": profile_id,
        "directory_count": directory_count,
        "extension_bytes": extension_bytes,
        "legacy_crc16": legacy_crc,
        "header_crc16": header_crc,
        "entries": entries,
    }


def locate_item_attributes(source: bytes) -> int:
    candidates = []
    for pos in range(len(source) - 35):
        valid = True
        for index, price in enumerate((0, 1200, 10, 600, 200)):
            if source[pos + index * 7:pos + index * 7 + 2] != price.to_bytes(2, "little"):
                valid = False
                break
        if valid:
            candidates.append(pos)
    if len(candidates) != 1:
        raise ValueError(f"expected one ItemAttributes candidate, found {len(candidates)}")
    return candidates[0]


def build_registry_seed(source: bytes, profile: dict) -> tuple[bytes, dict]:
    base_prefix = bytes.fromhex("012d31312d414116032d400000")
    base = source.find(base_prefix)
    moves = source.find(MOVE_PREFIX)
    items = locate_item_attributes(source)

    if base < 0 or moves < 0:
        raise ValueError("cannot locate legacy registry tables")

    base_blob = source[base:base + BASE_DATA_SIZE]
    move_blob = source[moves:moves + MOVES_DATA_SIZE]
    item_blob = source[items:items + ITEM_DATA_SIZE]

    if sha256(base_blob) != BASE_DATA_SHA256:
        raise ValueError("BaseData hash mismatch")
    if sha256(move_blob) != MOVES_SHA256:
        raise ValueError("Moves hash mismatch")
    if sha256(item_blob) != ITEM_ATTRIBUTES_SHA256:
        raise ValueError("ItemAttributes hash mismatch")

    bank = bytearray(b"\xFF" * 0x4000)
    struct.pack_into(
        "<8sHHHHHH",
        bank,
        0,
        REGISTRY_MAGIC,
        1,
        profile["profile_id"],
        3,
        REGISTRY_DIRECTORY_OFFSET,
        REGISTRY_DATA_OFFSET,
        16,
    )

    cursor = REGISTRY_DATA_OFFSET
    entries = []
    for registry_type, entry_size, count, blob in (
        (REGISTRY_SPECIES, 32, 251, base_blob),
        (REGISTRY_MOVES, 7, 251, move_blob),
        (REGISTRY_ITEMS, 7, 256, item_blob),
    ):
        entries.append((
            registry_type,
            1,
            entry_size,
            16,
            cursor,
            count,
            len(blob),
            0,
        ))
        bank[cursor:cursor + len(blob)] = blob
        cursor += len(blob)

    for index, entry in enumerate(entries):
        struct.pack_into(
            "<HHHHHHHH",
            bank,
            REGISTRY_DIRECTORY_OFFSET + index * REGISTRY_ENTRY_SIZE,
            *entry,
        )

    return bytes(bank), {
        "base_data_physical_offset": base,
        "moves_physical_offset": moves,
        "item_attributes_physical_offset": items,
    }


def patch_legacy_lookup_hooks(out: bytearray, original: bytes) -> dict:
    base_hits = find_wild(original, BASE_LOOKUP_PATTERN)
    item_hits = find_wild(original, ITEM_LOOKUP_PATTERN)

    if len(base_hits) != 1:
        raise ValueError(f"expected one GetBaseData signature, found {len(base_hits)}")
    if len(item_hits) != 1:
        raise ValueError(f"expected one GetItemAttr signature, found {len(item_hits)}")

    base = base_hits[0]
    item = item_hits[0]

    if out[base + 6] != 0x3E or out[base + 7] != 0x14 or out[base + 20] != 0x21:
        raise ValueError("GetBaseData patch precondition failed")
    original_base_address = out[base + 21] | (out[base + 22] << 8)

    out[base + 7] = REGISTRY_BANK
    out[base + 21] = REGISTRY_BASE_ADDR & 0xFF
    out[base + 22] = REGISTRY_BASE_ADDR >> 8

    if out[item + 2] != 0x21 or out[item + 23] != 0x3E or out[item + 24] != 0x01:
        raise ValueError("GetItemAttr patch precondition failed")
    original_item_address = out[item + 3] | (out[item + 4] << 8)

    out[item + 3] = REGISTRY_ITEMS_ADDR & 0xFF
    out[item + 4] = REGISTRY_ITEMS_ADDR >> 8
    out[item + 24] = REGISTRY_BANK

    return {
        "get_base_data": {
            "routine_offset": base,
            "bank_immediate_offset": base + 7,
            "address_immediate_offset": base + 21,
            "original_bank": 0x14,
            "original_address": original_base_address,
            "target_bank": REGISTRY_BANK,
            "target_address": REGISTRY_BASE_ADDR,
        },
        "get_item_attr": {
            "routine_offset": item,
            "address_immediate_offset": item + 3,
            "bank_immediate_offset": item + 24,
            "original_bank": 0x01,
            "original_address": original_item_address,
            "target_bank": REGISTRY_BANK,
            "target_address": REGISTRY_ITEMS_ADDR,
        },
    }


def verify_registry_legacy_parity(
    output: bytes,
    original: bytes,
    source_offsets: dict,
) -> None:
    for species in (1, 25, 151, 251):
        old_start = source_offsets["base_data_physical_offset"] + (species - 1) * 32
        new_start = REGISTRY_PHYS + REGISTRY_DATA_OFFSET + (species - 1) * 32
        if output[new_start:new_start + 32] != original[old_start:old_start + 32]:
            raise ValueError(f"BaseData parity failed for species {species}")

    for item in (1, 100, 191, 255):
        old_start = source_offsets["item_attributes_physical_offset"] + (item - 1) * 7
        new_start = REGISTRY_PHYS + (REGISTRY_ITEMS_ADDR - 0x4000) + (item - 1) * 7
        if output[new_start:new_start + 7] != original[old_start:old_start + 7]:
            raise ValueError(f"ItemAttributes parity failed for item {item}")



def bank_addr(physical: int) -> tuple[int, int]:
    return physical // 0x4000, 0x4000 + (physical % 0x4000)


def cpu_addr_to_phys(current_bank: int, address: int) -> int:
    if address < 0x4000:
        return address
    return current_bank * 0x4000 + (address - 0x4000)


def ld_hl_refs(data: bytes, address: int, width: int) -> list[tuple[int, int]]:
    refs = []
    for field_offset in range(width):
        target = address + field_offset
        signature = bytes((0x21, target & 0xFF, target >> 8))
        pos = 0
        while True:
            hit = data.find(signature, pos)
            if hit < 0:
                break
            refs.append((hit, field_offset))
            pos = hit + 1
    return sorted(refs)


def classify_move_refs(original: bytes) -> tuple[int, list[dict], list[dict], list[int]]:
    move_phys = original.find(MOVE_PREFIX)
    if move_phys < 0:
        raise ValueError("Moves table not found")
    _, move_address = bank_addr(move_phys)
    refs = ld_hl_refs(original, move_address, 7)

    real_refs = []
    excluded = []
    bank_offsets = set()

    for offset, field_offset in refs:
        window = original[offset:offset + 48]

        # Korean localization has one byte-pattern collision: the three bytes that
        # equal Moves+MOVE_POWER are actually a FarCall function address.
        if len(window) >= 6 and window[3] == 0x3E and window[5] == 0xCF:
            excluded.append({
                "offset": offset,
                "field_offset": field_offset,
                "reason": "farcall_function_pointer",
            })
            continue

        direct_bank_offsets = []
        for index in range(3, min(32, len(window) - 1)):
            if window[index] == 0x3E and window[index + 1] == 0x10:
                direct_bank_offsets.append(offset + index + 1)

        if direct_bank_offsets:
            real_refs.append({
                "offset": offset,
                "field_offset": field_offset,
                "kind": "direct",
            })
            bank_offsets.update(direct_bank_offsets)
            continue

        if len(window) >= 6 and window[3] == 0xCD:
            current_bank = offset // 0x4000
            helper_address = window[4] | (window[5] << 8)
            helper_phys = cpu_addr_to_phys(current_bank, helper_address)
            helper = original[helper_phys:helper_phys + 32]
            helper_bank_offsets = []

            for index in range(0, min(20, len(helper) - 1)):
                if helper[index] == 0x3E and helper[index + 1] == 0x10:
                    helper_bank_offsets.append(helper_phys + index + 1)

            for index in range(0, min(16, len(helper) - 2)):
                if helper[index] != 0xCD:
                    continue
                nested_address = helper[index + 1] | (helper[index + 2] << 8)
                nested_phys = cpu_addr_to_phys(current_bank, nested_address)
                nested = original[nested_phys:nested_phys + 12]
                for nested_index in range(0, min(8, len(nested) - 1)):
                    if nested[nested_index] == 0x3E and nested[nested_index + 1] == 0x10:
                        helper_bank_offsets.append(nested_phys + nested_index + 1)

            if helper_bank_offsets:
                real_refs.append({
                    "offset": offset,
                    "field_offset": field_offset,
                    "kind": "helper",
                })
                bank_offsets.update(helper_bank_offsets)
                continue

        raise ValueError(f"unclassified Moves reference at {offset:#x}")

    if len(real_refs) != 22:
        raise ValueError(f"expected 22 real Moves references, found {len(real_refs)}")
    if len(bank_offsets) != 15:
        raise ValueError(f"expected 15 Moves bank immediates, found {len(bank_offsets)}")

    return move_address, real_refs, excluded, sorted(bank_offsets)


def patch_move_lookup_hooks(out: bytearray, original: bytes) -> dict:
    original_move_address, refs, excluded, bank_offsets = classify_move_refs(original)

    for ref in refs:
        offset = ref["offset"]
        field_offset = ref["field_offset"]
        if out[offset] != 0x21:
            raise ValueError(f"Moves pointer opcode precondition failed at {offset:#x}")
        current_address = out[offset + 1] | (out[offset + 2] << 8)
        if current_address != original_move_address + field_offset:
            raise ValueError(f"Moves pointer precondition failed at {offset:#x}")
        target = REGISTRY_MOVES_ADDR + field_offset
        out[offset + 1] = target & 0xFF
        out[offset + 2] = target >> 8

    for offset in bank_offsets:
        if out[offset - 1] != 0x3E or out[offset] != 0x10:
            raise ValueError(f"Moves bank precondition failed at {offset:#x}")
        out[offset] = REGISTRY_BANK

    return {
        "target_bank": REGISTRY_BANK,
        "target_address": REGISTRY_MOVES_ADDR,
        "pointer_count": len(refs),
        "bank_immediate_count": len(bank_offsets),
        "pointer_offsets": [ref["offset"] for ref in refs],
        "bank_immediate_offsets": bank_offsets,
        "excluded_candidates": excluded,
    }


def expand_rom(data: bytes) -> tuple[bytes, dict]:
    profile = identify_rom(data)

    if len(data) != profile["rom_bytes"]:
        raise ValueError("ROM size differs from fingerprint profile")
    validate_header(data)

    if data[0x147] != CART_MBC3_RTC_RAM_BATTERY:
        raise ValueError("expected cartridge type 0x10")
    if data[0x149] != 0x03:
        raise ValueError("expected original 32 KiB RAM size code 0x03")
    if data[0x10:0x16] != BANKSWITCH_SIGNATURE:
        raise ValueError("unexpected bank switch entry at ROM offset 0x0010")

    out = bytearray(data)
    applied = []

    for patch in profile.get("patches", []):
        offset = patch["offset"]
        if out[offset] != patch["before"]:
            raise ValueError(f"patch precondition failed at {offset:#x}")
        out[offset] = patch["after"]
        applied.append(patch)

    out.extend(b"\xFF" * (ROM_TARGET - len(out)))

    registry, source_offsets = build_registry_seed(data, profile)
    out[REGISTRY_PHYS:REGISTRY_PHYS + 0x4000] = registry

    lookup_hooks = patch_legacy_lookup_hooks(out, data)
    move_hooks = patch_move_lookup_hooks(out, data)

    out[0x147] = CART_MBC3_RTC_RAM_BATTERY
    out[0x148] = ROM_SIZE_CODE_4MIB
    out[0x149] = RAM_SIZE_CODE_64KIB
    fix_checksums(out)
    validate_header(out)
    verify_registry_legacy_parity(bytes(out), data, source_offsets)

    return bytes(out), {
        "release": profile["id"],
        "profile_id": profile["profile_id"],
        "input_sha1": profile["sha1"],
        "input_bytes": len(data),
        "output_bytes": len(out),
        "output_sha1": sha1(out),
        "output_sha256": sha256(out),
        "rom_banks": 256,
        "sram_banks": 8,
        "registry_bank": REGISTRY_BANK,
        "registry_physical_offset": REGISTRY_PHYS,
        "registry_magic": REGISTRY_MAGIC.decode("ascii", "ignore").rstrip("\0"),
        "lookup_hooks": lookup_hooks,
        "move_hooks": move_hooks,
        "applied_release_patches": applied,
    }


def expand_save(data: bytes) -> tuple[bytes, dict]:
    if len(data) not in (SRAM_32K, SRAM_32K + RTC_TRAILER):
        raise ValueError(
            f"expected 32 KiB SRAM plus optional 44-byte RTC trailer, got {len(data):#x}"
        )

    profile = identify_save(data)
    legacy = data[:SRAM_32K]
    trailer = data[SRAM_32K:]

    extension = build_save_v2_extension(profile["profile_id"], legacy)
    parsed = parse_save_v2_extension(extension)
    out = legacy + extension + trailer

    return out, {
        "release": profile["id"],
        "profile_id": profile["profile_id"],
        "input_bytes": len(data),
        "output_bytes": len(out),
        "legacy_sram_bytes_preserved": SRAM_32K,
        "extension_sram_bytes": len(extension),
        "rtc_trailer_bytes": len(trailer),
        "save_v2": parsed,
        "input_sha1": sha1(data),
        "output_sha1": sha1(out),
        "output_sha256": sha256(out),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="kind", required=True)

    for kind in ("rom", "save"):
        command = sub.add_parser(kind)
        command.add_argument("input", type=Path)
        command.add_argument("output", type=Path)

    args = parser.parse_args()
    data = args.input.read_bytes()

    output, report = expand_rom(data) if args.kind == "rom" else expand_save(data)
    args.output.write_bytes(output)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
