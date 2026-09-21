# GOLD save migration contract

Status: active design boundary.

There are **two unrelated save formats** involved in GOLD and they must not be
conflated.

## 1. Original Gold source saves

These are import inputs from Generation II.

Measured supplied files contain:

```text
0x8000 cartridge SRAM
0x002C observed RTC trailer
```

Japanese and localized releases use different PC storage geometry:

- Japan: 9 boxes x 30, stride 0x54A
- Korean/western: 14 boxes x 20, stride 0x450

The loader selects a legacy profile, decodes it, then produces canonical import
records. The RTC trailer is not free SRAM.

## 2. GOLD GBA runtime saves

The final remake uses the Generation III-derived GBA save architecture from the pinned
pokeemerald-expansion core: 4 KiB flash sectors, two recovery slots, and dedicated
Pokémon-storage sectors.

The current packed BoxPokemon format is an implementation input, not a permanent
future-generation limit.

## Phase 1

Held Item 10 -> 16 bits and Poké Ball 6 -> 8 bits consume existing unused bits and do
not change BoxPokemon size or save-sector allocation.

## Phase 2 / Save V2

Species and Move persistent IDs require a versioned storage migration because simply
growing every BoxPokemon can overflow the current storage-sector budget.

Save V2 requirements:

- canonical Species and Move runtime IDs at least 16 bits;
- all 420 boxed slots preserved;
- dual-save corruption recovery preserved;
- checksums/encryption explicitly versioned;
- old GBA GOLD saves migratable;
- original Gen II Gold saves imported through their own decoder;
- unknown future official content can append IDs without renumbering existing data;
- no silent truncation.

The physical encoding is intentionally not frozen until sector-budget tests pass.
