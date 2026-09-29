# GOLD legacy ID expansion — Stage 1

This stage continues directly from the 4 MiB ROM / 64 KiB SRAM expansion and is based on all eight supplied original Gold ROM/SAV pairs.

## Verified common data

The persistent Pokémon record stores the extensible identities as single bytes:

```text
+0 species   u8
+1 item      u8
+2 move 1    u8
+3 move 2    u8
+4 move 3    u8
+5 move 4    u8
```

The eight releases use different physical addresses, but BaseData, Moves and ItemAttributes are byte-identical across every release. Their shared SHA-256 values and all measured direct references are committed in `research/legacy_id_path_matrix.json`.

## GOLDREG

ROM bank `$80` contains a versioned `GOLDREG` header/directory plus the verified legacy tables.

```text
$80:4000  GOLDREG header
$80:4040  registry directory
$80:4100  BaseData       (251 x 32)
$80:6060  Moves          (251 x 7)
$80:673D  ItemAttributes (256 x 7)
```

The directory declares 16-bit master-ID namespaces. Original IDs are not renumbered.

## Central lookup hooks — implemented

The ROM transformer now patches both central lookup functions in all eight releases.

**GetBaseData**
- table bank immediate: `$14 -> $80`
- table base address: release-specific original address -> `$4100`

**GetItemAttr**
- table bank immediate: `$01 -> $80`
- table base address: release-specific original address -> `$673D`

Every patch is guarded by an exact routine signature and immediate-value precondition. An unknown or altered ROM is rejected rather than patched.

This slice deliberately preserves the original 8-bit ID behavior. It proves that normal species base-data and item-attribute reads can run from expanded ROM bank `$80` before the high byte is enabled. The transformed tables were compared against the original entries on all eight project ROMs before the output hashes were recorded in `research/legacy_lookup_hook_profiles.json`.

## GOLD_SAVE_V2

Original SRAM banks 0..3 remain byte-exact. Banks 4..7 contain the versioned extension.

The first blocks are:

1. `MON_ID_HIGH`: 288 persistent-mon slots × 6 bytes = 1,728 bytes. Per slot: species high byte, held-item high byte, move1..move4 high bytes.
2. `INVENTORY_ITEM_HIGH`: 107 bytes for 20 item slots, 50 PC-item slots, 12 ball slots and 25 key-item slots.

For an original save all high bytes begin at zero:

```text
canonical_id = legacy_low_byte | (extension_high_byte << 8)
```

## Current boundary / next slice

The following is **not yet claimed complete**:

- the 16-bit high byte is not yet consumed by GetBaseData/GetItemAttr;
- direct Moves lookup sites still reference the legacy Moves table;
- party/box/daycare copy paths do not yet move the six high bytes with each mon;
- inventory high-byte slots are allocated but not yet connected to bag/PC operations.

The next implementation slice is the Moves path classifier/hooker across all eight releases, followed by the mon/save synchronization hooks and >255 round-trip tests.
