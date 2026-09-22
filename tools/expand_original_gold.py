#!/usr/bin/env python3
"""Expand supported original Pokémon Gold ROM/SAV files for GOLD.

ROM target: MBC30-class 4 MiB ROM + 64 KiB SRAM while retaining RTC semantics.
The tool refuses ROMs that do not exactly match one of the eight measured releases.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROM_TARGET = 4 * 1024 * 1024
ROM_SIZE_CODE_4MIB = 0x07
RAM_SIZE_CODE_64KIB = 0x05
CART_MBC3_RTC_RAM_BATTERY = 0x10
SRAM_32K = 0x8000
SRAM_64K = 0x10000
RTC_TRAILER = 0x2C
BANKSWITCH_SIGNATURE = bytes.fromhex("e0 9f ea 00 20 c9")

RELEASES = {
    "8814f1039450a5d3684b1389f588ccd7ee7c3436": {
        "id": "japan_v0", "rom_bytes": 0x100000,
    },
    "a222402235d484ee8e39f3f31bae57cf13daf585": {
        "id": "japan_rev_a", "rom_bytes": 0x100000,
    },
    "c0ff3999e1093e1af59ef3eea3f1bfd7c1f18a65": {
        "id": "korea", "rom_bytes": 0x200000,
        "patches": [{
            "offset": 0x317C, "before": 0x04, "after": 0x08,
            "reason": "OpenSRAM bank bound 4->8 for MBC30 SRAM banks",
        }],
    },
    "d8b8a3600a465308c9953dfa04f0081c05bdcb94": {
        "id": "usa_europe", "rom_bytes": 0x200000,
    },
    "9254195d461ea942eaaa08cc4b83de3cf82aea0d": {
        "id": "germany", "rom_bytes": 0x200000,
    },
    "c147c0d8c2b71b7628a7233436f5c052b5b17081": {
        "id": "france", "rom_bytes": 0x200000,
    },
    "032608fe8947b627584a4a0eccc7bf9ad3588426": {
        "id": "italy", "rom_bytes": 0x200000,
    },
    "162ea54c6a3cff374642e6dd842f9bffac847e7b": {
        "id": "spain", "rom_bytes": 0x200000,
    },
}


def sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
    buf[0x14E:0x150] = b"\x00\x00"
    buf[0x14E:0x150] = global_checksum(buf).to_bytes(2, "big")


def identify(data: bytes) -> dict:
    digest = sha1(data)
    if digest not in RELEASES:
        raise ValueError(f"unsupported Gold ROM SHA-1: {digest}")
    return dict(RELEASES[digest], sha1=digest)


def expand_rom(data: bytes) -> tuple[bytes, dict]:
    profile = identify(data)

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
    out[0x147] = CART_MBC3_RTC_RAM_BATTERY
    out[0x148] = ROM_SIZE_CODE_4MIB
    out[0x149] = RAM_SIZE_CODE_64KIB
    fix_checksums(out)
    validate_header(out)

    return bytes(out), {
        "release": profile["id"],
        "input_sha1": profile["sha1"],
        "input_bytes": len(data),
        "output_bytes": len(out),
        "output_sha1": sha1(out),
        "output_sha256": sha256(out),
        "rom_banks": len(out) // 0x4000,
        "sram_banks": 8,
        "header": {
            "cartridge_type": out[0x147],
            "rom_size_code": out[0x148],
            "ram_size_code": out[0x149],
        },
        "applied_release_patches": applied,
    }


def expand_save(data: bytes) -> tuple[bytes, dict]:
    if len(data) not in (SRAM_32K, SRAM_32K + RTC_TRAILER):
        raise ValueError(
            f"expected 32 KiB SRAM plus optional 44-byte RTC trailer, got {len(data):#x}"
        )

    legacy = data[:SRAM_32K]
    trailer = data[SRAM_32K:]
    out = legacy + bytes(SRAM_64K - SRAM_32K) + trailer

    return out, {
        "input_bytes": len(data),
        "output_bytes": len(out),
        "legacy_sram_bytes_preserved": SRAM_32K,
        "extension_sram_bytes": SRAM_32K,
        "rtc_trailer_bytes": len(trailer),
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

    if args.kind == "rom":
        output, report = expand_rom(data)
    else:
        output, report = expand_save(data)

    args.output.write_bytes(output)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
