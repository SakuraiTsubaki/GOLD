# GOLD original ROM / save baseline

Status: measured source/import evidence for the GBA remake.

The files measured here are original Gold inputs. They are **not** the final GOLD
runtime format. GOLD imports their behavior and data into the Generation III-derived
GBA runtime defined by `PROJECT.md`.

## ROM measurements

| Release | Size | ROM banks | Cart | SRAM | Version |
| --- | ---: | ---: | --- | ---: | ---: |
| Pocket Monsters Kin (Japan) | 1 MiB | 64 | MBC3 + RTC + RAM + battery | 32 KiB | 0 |
| Pocket Monsters Kin (Japan) Rev A | 1 MiB | 64 | MBC3 + RTC + RAM + battery | 32 KiB | 1 |
| Pocket Monsters Geum (Korea) | 2 MiB | 128 | MBC3 + RTC + RAM + battery | 32 KiB | 0 |
| Gold USA/Europe | 2 MiB | 128 | MBC3 + RTC + RAM + battery | 32 KiB | 0 |
| German/French/Italian/Spanish Gold | 2 MiB | 128 | MBC3 + RTC + RAM + battery | 32 KiB | 0 |

The two Japanese ROMs have no completely zero-filled 16 KiB bank. The localized
2 MiB releases have release-specific blank banks. Twenty blank banks are common to
all measured 2 MiB releases:

```text
13 22 28 29 2C 2D 2F 34 35 63
67 6F 73 74 75 76 77 7C 7D 7E
```

This ROM-bank information is provenance/reverse-engineering evidence only. The final
remake runs on GBA and does not inherit the MBC3 address space.

## Save container measurement

Every supplied Gold save file is exactly:

```text
0x8000 bytes  cartridge SRAM
0x002C bytes  RTC trailer
0x802C bytes  total file
```

The 44-byte trailer parses as eleven little-endian u32 values: five live MBC3 RTC
register values, five latched values, and one timestamp. It is emulator/transport
metadata outside cartridge SRAM. Import code must split it from the first 32 KiB.

## Japanese save profile

The Japanese saves use the compact Japanese PC layout:

```text
boxes          9
mons/box      30
box stride    0x54A
SRAM bank 2    6 boxes = 0x1FBC bytes
bank 2 spare   0x0044 bytes
SRAM bank 3    remaining 3 boxes + other data
```

The `0x54A` stride and boundaries are visible in the supplied saves.

## Localized save profile

Korean, English, German, French, Italian and Spanish samples use:

```text
boxes         14
mons/box      20
box stride    0x450
SRAM bank 2    7 boxes = 0x1E30 bytes
bank 2 spare   0x01D0 bytes
SRAM bank 3    remaining 7 boxes + other data
```

Therefore there is no single byte-identical "Gold legacy save layout". GOLD must select
a release profile before decoding PC storage.

## Import boundary

The remake load/import path is:

```text
original ROM/save
  -> release fingerprint
  -> release-specific Gold decoder
  -> canonical GOLD import record
  -> GBA/Generation III-derived runtime
```

Do not expose original MBC3 SRAM addresses or box strides to gameplay code.

## Consequence for Generation 10 readiness

The original Gold limits are useful for faithful import, but they are **not** the
capacity target. Capacity work belongs in the pinned GBA core. See
`docs/GBA_GEN10_CAPACITY.md`.
