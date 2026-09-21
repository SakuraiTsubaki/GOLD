# GOLD Generation 10+ expansion architecture

Status: active GBA remake architecture.

## Boundary

GOLD is a Generation III-derived **GBA remake**. Original Game Boy / Game Boy Color
ROM banks, MBC3 mapper behavior and SRAM offsets are source-analysis/import concerns,
not the final runtime architecture.

The original binaries are measured first because they define what must be faithfully
imported. Runtime expansion is then performed against the pinned
`pokeemerald-expansion` core.

## No guessed Generation 10 data

"Generation 10-ready" means the storage/API design must not require a rewrite merely
because verified official registries grow. It does not mean inventing unreleased
species, moves, items, forms, abilities or mechanics.

## Current hard limits

The pinned core stores BoxPokemon fields more narrowly than their runtime enums:

- Species: 11 bits (0..2047)
- each Move: 11 bits (0..2047)
- held Item: 10 bits (0..1023)
- Tera Type: 5 bits
- Poké Ball: 6 bits

Current audited registries are `NUM_SPECIES=1573`,
`MOVES_COUNT_ALL=935`, and `ITEMS_COUNT=874`.

## Expansion order

1. **No-size-growth fields first.** Consume existing unused bits to make held Item
   16-bit and Poké Ball 8-bit without changing BoxPokemon size.
2. **Guard every packed field.** Builds/importers must fail before silent truncation.
3. **Species/Move Save V2.** Design a persistent encoding with 16-bit runtime IDs while
   preserving all 420 box slots and dual-save recovery.
4. **Migrate, do not reinterpret.** Existing Generation III-derived saves need an
   explicit versioned migration path.
5. **Original Gold import stays separate.** Japanese 9x30 and localized 14x20 save
   profiles decode into canonical records before entering the GBA runtime.

See `docs/GBA_GEN10_CAPACITY.md` for the measured storage arithmetic.

## Why not widen everything immediately?

At the audited layout BoxPokemon is 80 bytes and there are 420 boxed slots. If a
redesign raises the record to 96 bytes, boxes alone grow by 6,720 bytes. Pokémon
storage currently occupies nine 4 KiB save sectors, so record growth must be solved
together with sector allocation, checksums, encryption and save migration.

GOLD therefore treats runtime ID width and persistent encoding as separate contracts.
