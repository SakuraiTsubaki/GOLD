# GOLD original ROM / save baseline

Status: measured source evidence for GOLD-native expansion.

The files measured here are original Gold inputs. ROM and SAVE are separate evidence
layers. They define release fingerprints, original limits and compatibility requirements;
they do not make another game's engine the GOLD capacity authority.

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

These measurements are used to design GOLD's own resource-directory and mapper/storage
abstractions. They are not replaced by a Generation III save layout.

## Save container measurement

Every supplied Gold save file is exactly:

```text
0x8000 bytes  cartridge SRAM
0x002C bytes  RTC trailer
0x802C bytes  total file
```

The 44-byte trailer parses as eleven little-endian u32 values: five live MBC3 RTC
register values, five latched values, and one timestamp. It is emulator/transport
metadata outside cartridge SRAM.

## Japanese save profile

```text
boxes          9
mons/box      30
box stride    0x54A
SRAM bank 2    6 boxes = 0x1FBC bytes
bank 2 spare   0x0044 bytes
SRAM bank 3    remaining 3 boxes + other data
```

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

Therefore there is no single byte-identical Gold save layout. The decoder selects a
release profile before interpreting PC storage.

## Expansion boundary

```text
original Gold ROM
  -> release fingerprint / disassembly evidence
  -> canonical GOLD registries

original Gold SAVE
  -> release-specific decoder
  -> canonical GOLD save model
  -> GOLD_SAVE_V2
```

Generation III / Emerald-derived projects may later be consulted for GBA implementation,
but they do not define GOLD's master IDs or Save V2 capacity.

See `docs/GEN10_EXPANSION_ARCHITECTURE.md` and `docs/SAVE_FORMAT_V2.md`.
