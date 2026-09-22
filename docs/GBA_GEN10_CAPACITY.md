# GOLD GBA Generation 10+ capacity audit

Pinned core:

```text
rh-hideout/pokeemerald-expansion
75b806a3ab57a81ff1eb6179288981f0b3cc3050
```

This is a storage/API capacity project, not a prediction of unreleased content.

## Current packed limits

At the pinned commit:

| Persistent field | Packed width | Max | Current audited registry |
| --- | ---: | ---: | ---: |
| Species | 11 bits | 2047 | NUM_SPECIES = 1573 |
| Move | 11 bits | 2047 | MOVES_COUNT_ALL = 935 |
| Held Item | 10 bits | 1023 | ITEMS_COUNT = 874 |
| Tera Type | 5 bits | 31 | retained |
| Poké Ball | 6 bits | 63 | retained |

The core has 14 boxes x 30 slots = 420 boxed Pokémon and an 80-byte BoxPokemon.

## Phase 1 — implemented patch

`0001-expand-boxmon-item-ball-capacity.patch` changes:

- held Item: 10 -> 16 bits by consuming the adjacent 6 unused bits;
- Poké Ball: 6 -> 8 bits by consuming the adjacent 2 unused bits.

This causes **zero BoxPokemon size growth**.

## Phase 2 — SaveBlock3 sidecar reserved

The pinned save format provides `SAVE_BLOCK_3_CHUNK_SIZE=116` bytes in each of
14 sectors, so SaveBlock3 has a hard maximum of:

```text
116 * 14 = 1624 bytes
```

With the pinned default configuration, optional SaveBlock3 consumers are disabled
(fake RTC, followers, first-time item-description flags, DexNav search levels), and
`APRICORN_TREE_COUNT=0`. The always-present `dexNavChain` remains.

To widen Species and four Move IDs in-place, GOLD plans to move these existing fields
out of BoxPokemon:

```text
tera type               5 bits
evolution tracker 1     5 bits
evolution tracker 2     5 bits
hyper-training flags    6 bits
                       -------
                       21 bits / persistent mon
```

Persistent slots are budgeted conservatively as:

```text
PC storage      420
party             6
daycare           2
fusion storage    4
                ---
                432
```

Therefore:

```text
432 * 21 bits = 9072 bits = 1134 payload bytes
sidecar header                         12 bytes
                                      ----------
sidecar total                        1146 bytes
SaveBlock3 hard ceiling              1624 bytes
remaining before other fields         478 bytes
```

`0002-reserve-saveblock3-boxmon-sidecar.patch` adds that versioned 1,146-byte
sidecar and relies on upstream's existing compile-time SaveBlock3 size assertion to
reject incompatible feature combinations.

### Sidecar v1 bit layout

Each logical 21-bit entry is:

- bits 0..4: tera type
- bits 5..9: evolution tracker 1
- bits 10..14: evolution tracker 2
- bits 15..20: six hyper-training flags

The sidecar reservation is implemented now. **Species and Move fields are not widened
until accessor/copy/migration hooks are connected**, so no save can silently lose the
displaced metadata.

## Runtime build path

GOLD does not copy an untracked upstream snapshot into the repository.

`scripts/prepare_runtime.sh`:

1. clones/checks out the exact pinned upstream commit;
2. hard-resets the generated runtime tree to that commit;
3. applies GOLD patches in `patches/pokeemerald-expansion/series`;
4. runs the capacity guard.

`scripts/build_runtime.sh` then builds the patched core with `make all`.

The GitHub Actions workflow `GOLD Gen10 Capacity` performs the same process on every
relevant main-branch change.

## Runtime validation

The pinned runtime plus patches 0001 and 0002 builds successfully with `make all` in the GOLD Gen10 Capacity workflow.

Patch 0003 adds the sidecar pack/unpack API, payload CRC, bounds checks, and keeps the packed sidecar at the front of SaveBlock3 so its multi-byte header starts aligned.

## Next implementation slice

1. define stable persistent slot indices and copy/swap hooks;
2. migrate tera/evolution/hyper metadata into the sidecar;
3. widen BoxPokemon Species to 16 bits;
4. widen all four Move IDs to 16 bits;
5. add save-version migration tests;
6. add explicit overflow tests above 2047.

At no point is an unreleased Generation 10 species, move, item or mechanic invented.
