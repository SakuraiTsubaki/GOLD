#!/usr/bin/env python3
"""Read-only structural probe for original Pokémon Gold ROM/save inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

ROM_BANK = 0x4000
SRAM_BYTES = 0x8000
SRAM_BANK = 0x2000
RTC_TRAILER_BYTES = 0x2C


def hashes(data: bytes) -> dict[str, str]:
    return {
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def probe_rom(data: bytes) -> dict:
    if len(data) < 0x150 or len(data) % ROM_BANK:
        raise ValueError("not a bank-aligned Game Boy ROM")

    header_calc = 0
    for value in data[0x134:0x14D]:
        header_calc = (header_calc - value - 1) & 0xFF
    global_calc = (sum(data[:0x14E]) + sum(data[0x150:])) & 0xFFFF

    zero_banks = [
        bank for bank in range(len(data) // ROM_BANK)
        if not any(data[bank * ROM_BANK:(bank + 1) * ROM_BANK])
    ]

    return {
        "kind": "rom",
        "bytes": len(data),
        "rom_banks": len(data) // ROM_BANK,
        **hashes(data),
        "header": {
            "cgb_flag": data[0x143],
            "sgb_flag": data[0x146],
            "cartridge_type": data[0x147],
            "rom_size_code": data[0x148],
            "ram_size_code": data[0x149],
            "destination_code": data[0x14A],
            "version": data[0x14C],
            "header_checksum": data[0x14D],
            "global_checksum": int.from_bytes(data[0x14E:0x150], "big"),
        },
        "header_checksum_ok": header_calc == data[0x14D],
        "global_checksum_ok": global_calc == int.from_bytes(data[0x14E:0x150], "big"),
        "zero_banks": zero_banks,
    }


def probe_save(data: bytes) -> dict:
    if len(data) not in (SRAM_BYTES, SRAM_BYTES + RTC_TRAILER_BYTES):
        raise ValueError(
            f"expected 0x8000 SRAM bytes, optionally plus 0x2c RTC trailer; got {len(data):#x}"
        )

    trailer = data[SRAM_BYTES:]
    result = {
        "kind": "save",
        "bytes": len(data),
        **hashes(data),
        "cartridge_sram_bytes": SRAM_BYTES,
        "rtc_trailer_bytes": len(trailer),
    }

    if trailer:
        values = list(struct.unpack("<11I", trailer))
        result["rtc_live"] = dict(zip(
            ("seconds", "minutes", "hours", "day_low", "day_high_control"),
            values[:5],
        ))
        result["rtc_latched"] = dict(zip(
            ("seconds", "minutes", "hours", "day_low", "day_high_control"),
            values[5:10],
        ))
        result["rtc_timestamp"] = values[10]

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    data = args.input.read_bytes()

    if args.input.suffix.lower() in {".gb", ".gbc"}:
        result = probe_rom(data)
    elif args.input.suffix.lower() == ".sav":
        result = probe_save(data)
    else:
        raise SystemExit("input must be .gb/.gbc or .sav")

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
