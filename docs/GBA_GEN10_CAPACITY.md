# GOLD GBA Generation 10+ capacity audit

Pinned core:

```text
rh-hideout/pokeemerald-expansion
75b806a3ab57a81ff1eb6179288981f0b3cc3050
```

This audit is about **storage capacity**, not guessed Generation 10 content.

## Measured current core

At the pinned commit:

| Persistent field | Packed width | Max value | Current dataset |
| --- | ---: | ---: | ---: |
| BoxPokemon species | 11 bits | 2047 | NUM_SPECIES = 1573 |
| BoxPokemon move | 11 bits each | 2047 | MOVES_COUNT_ALL = 935 |
| BoxPokemon held item | 10 bits | 1023 | ITEMS_COUNT = 874 |
| BoxPokemon tera type | 5 bits | 31 | core comment: 30 types |
| BoxPokemon Poké Ball | 6 bits | 63 | n/a |

The species namespace already contains forms and modern variants, so National Dex
species count alone is not a valid capacity test.

The closest current persistent-ID ceiling is held items: the highest current normal
item is 873 and the 10-bit field ends at 1023.

## Storage geometry

The pinned core uses:

```text
TOTAL_BOXES_COUNT = 14
IN_BOX_COUNT      = 30
boxed Pokémon     = 420
sizeof(BoxPokemon)= 80 bytes at the audited layout
```

The box array alone is 33,600 bytes. The storage struct reaches approximately
`0x8432` before the optional fusion storage that follows it.

Emerald's save system uses 4 KiB flash sectors and nine sectors for Pokémon storage.
Growing every BoxPokemon by 16 bytes would cost:

```text
420 * 16 = 6,720 additional bytes
```

That does not fit into the current Pokémon-storage sector budget without redesigning
the save layout. Therefore "make every packed ID u16" is not a safe first patch.

## Phase 1: zero-size-growth expansion

Two fields can be widened without changing `sizeof(BoxPokemon)`.

### Held item

Current:

```c
enum Item heldItem:10;
u16 unused_02:6;
```

GOLD target:

```c
u16 heldItem;
```

The adjacent six unused bits are consumed. Persistent held-item capacity becomes
0..65535 with no Pokémon save-size increase.

### Poké Ball

Current:

```c
u16 pokeball:6;
u16 nickname12:8;
u16 unused_0A:2;
```

GOLD target:

```c
u16 pokeball:8;
u16 nickname12:8;
```

The two unused bits are consumed. Capacity rises from 63 to 255 with no size increase.

The repository patch in
`patches/pokeemerald-expansion/0001-expand-boxmon-item-ball-capacity.patch`
implements this first safe step against the pinned core.

## Phase 2: Species and Move

Species and four move slots cannot all be widened to 16 bits in place without either:

1. increasing BoxPokemon and reallocating save sectors; or
2. defining a new compact persistent encoding while keeping a wider runtime identity.

GOLD will not guess which future IDs are needed. Instead the new format must satisfy:

- runtime Species/Move identifiers can reach at least 16 bits;
- saved IDs remain append-only;
- all 420 box slots remain representable;
- dual-save recovery is preserved;
- checksum/encryption migration is explicit;
- old pokeemerald-expansion saves can be upgraded;
- original Gold saves are imported through the separate Gen II decoder.

No Gen 10 species/move counts are reserved before verified official data exists.

## Capacity gates

Build/import tooling must fail loudly before an ID exceeds a packed field. Silent
truncation is forbidden.

Current warning thresholds:

```text
species >= 1900   investigate before 2048
moves   >= 1900   investigate before 2048
items   >= 1000   Phase 1 patch is mandatory before 1024
```

These thresholds are engineering alarms, not content predictions.
