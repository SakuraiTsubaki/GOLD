# GOLD Save Format V2 contract

Status: design contract for implementation.

## Goals

- Decode every extensible identity to a 16-bit master ID.
- Keep future additions appendable.
- Avoid making the legacy 32-byte BoxMon layout the permanent modern schema.
- Permit compact SRAM encoding without leaking compact IDs into gameplay logic.
- Detect incompatible or corrupted extension blocks.

## Header

A Save V2 implementation must carry at least:

```text
magic
format_version
schema_version
feature_flags
directory_offset
directory_count
payload_checksum
```

Exact byte offsets are assigned when the source save layout is imported and measured.

## Extension directory

Each extension block is described by:

```text
block_type      u16
block_version   u16
offset          u16/u24 build-dependent
length          u16
checksum        u16
flags           u16
```

Unknown optional blocks are skipped by length.
Unknown required blocks make the save incompatible instead of being silently ignored.

## Pokémon identity

The canonical record exposes:

```text
species_id      u16
variety_id      u16
form_id         u16
held_item_id    u16
move_id[4]      u16 each
ability_id      u16
```

Nature, modern IV/EV data, ribbons/marks, origin metadata, and later mechanics live in
versioned blocks or canonical fields as their source implementations are verified.

## Compact SRAM encoding

Serialized records may replace repeated 16-bit IDs with local dictionary indices.

Rules:

1. dictionary entries map to 16-bit master IDs;
2. index 0 is NONE unless a block explicitly defines otherwise;
3. dictionaries are save-local and never become global engine IDs;
4. loading always resolves to canonical master IDs;
5. dictionary overflow falls back to a wider block version rather than renumbering data.

## Legacy import

Original Gold saves are treated as import sources.

Legacy 8-bit Species/Move/Item values are translated into canonical IDs through an
explicit compatibility table. Legacy sentinels such as EGG are translated to state
flags, not retained as fake Species IDs.

Save V2 is allowed to differ physically from the original save layout. Compatibility
is provided by import/export code, not by freezing the engine to 1999-era field widths.
