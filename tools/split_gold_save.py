#!/usr/bin/env python3
"""Split an original Gold save container into SRAM and observed RTC metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

SRAM_BYTES = 0x8000
RTC_BYTES = 0x2C


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out-prefix", type=Path)
    args = parser.parse_args()

    data = args.input.read_bytes()
    if len(data) not in (SRAM_BYTES, SRAM_BYTES + RTC_BYTES):
        raise SystemExit(f"unsupported save length: {len(data):#x}")

    prefix = args.out_prefix or args.input.with_suffix("")
    sram_path = Path(str(prefix) + ".sram")
    sram_path.write_bytes(data[:SRAM_BYTES])
    print(f"wrote {sram_path} ({SRAM_BYTES:#x} bytes)")

    trailer = data[SRAM_BYTES:]
    if trailer:
        values = list(struct.unpack("<11I", trailer))
        rtc = {
            "format": "observed_mbc3_rtc_trailer_44",
            "live": values[:5],
            "latched": values[5:10],
            "timestamp": values[10],
            "raw_hex": trailer.hex(),
        }
        rtc_path = Path(str(prefix) + ".rtc.json")
        rtc_path.write_text(json.dumps(rtc, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {rtc_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
