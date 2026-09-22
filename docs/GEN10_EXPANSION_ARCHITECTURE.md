# Generation 10-ready expansion architecture

Status: **ACTIVE — Phase 0**

This document defines GOLD's expansion contract before game-source import.

## 1. Goal

Generation 10 readiness means **capacity and architecture readiness**, not guessing
unreleased content.

GOLD must accept verified future records without renumbering older data or replacing
the save/resource architecture again.

## 2. Master ID rule

Every registry that can realistically grow across generations uses a 16-bit master ID.

| Registry | Runtime width | Reserved zero |
| --- | ---: | --- |
| Species | 16-bit | NONE |
| Variety / battle profile | 16-bit | NONE |
| Form / appearance | 16-bit | NONE |
| Move | 16-bit | NONE |
| Item | 16-bit | NONE |
| Ability | 16-bit | NONE |
| Type | 16-bit | NONE |
| Evolution method | 16-bit | NONE |
| Resource | 16-bit | NONE |
| Feature / mechanic | 16-bit | NONE |

Valid normal ID space is `1..65535`.

The width is an engine contract, not a promise that every ID will be populated.

## 3. Append-only namespace

Registries are append-only.

- Existing IDs never move when a new generation is imported.
- Deletions become tombstones/aliases when compatibility requires them.
- Generation boundaries are metadata, not numeric hard partitions.
- No fixed "Generation 10 starts at X" constant is created before verified data exists.

For Species, official National Pokédex numbers are preserved whenever the source data
has such an identity. EGG is not a Species ID.

## 4. Species, variety, and form are separate

GOLD uses three layers:

```text
Species
  -> Variety / battle profile
       -> Form / appearance
```

**Species** is the stable creature identity.

**Variety** carries battle-relevant variation such as base stats, type combinations,
ability sets, or rules that differ between regional/alternate battle profiles.

**Form** describes selectable or derived appearance/state records. A form may point to
a variety, graphics, palette, cry/resource overrides, and transition rules.

This prevents a future form mechanic from consuming or renumbering Species IDs.

## 5. Moves, items, abilities, and types

Gen II's original 8-bit namespaces are not retained as the master representation.

All engine APIs that cross subsystem boundaries must exchange 16-bit master IDs.
A subsystem may use a compact local dictionary internally, but it must decode to the
same master ID before game logic uses the value.

This rule specifically prevents the old failure mode where Species is widened but
Move/Item later force a second save-format rewrite.

## 6. Save architecture

Runtime width and storage width are separate concerns.

GOLD Save V2 uses:

- a versioned header;
- feature flags;
- extension blocks;
- per-block lengths and checksums;
- dictionary/side-table encoding where it saves SRAM;
- a legacy import path rather than pretending a modern record is still an untouched
  Gen II BoxMon.

The decoded in-memory representation always exposes 16-bit master IDs.

See `SAVE_FORMAT_V2.md`.

## 7. Resource and ROM-bank abstraction

Game code must not bake a content table's physical ROM bank into gameplay logic.

Use:

```text
ResourceId (u16)
  -> ResourceDirectory
       -> mapper-specific bank/address
```

The resource directory accepts a 16-bit bank field even when the first mapper target
uses fewer bank bits. This allows a later ROM/mapper expansion to replace the mapper
backend instead of rewriting every content consumer.

The mapper choice is therefore a build target, not an identity-system limit.

## 8. Feature registry for future mechanics

Unknown future mechanics are represented by a feature registry and data-driven
descriptors.

Examples of subsystems that may attach feature data:

- battle transformations;
- form transitions;
- field actions;
- encounter rules;
- evolution methods;
- held-item effects;
- move behavior flags;
- save blocks.

Do not reserve guessed Generation 10 mechanic names or numeric IDs.

## 9. Compatibility layers

GOLD distinguishes three formats:

1. **Legacy source format** — original Gold structures and 8-bit fields.
2. **Canonical runtime format** — 16-bit IDs and modern extensible records.
3. **Serialized Save V2 format** — compact/versioned representation.

Importers perform legacy -> canonical conversion.
Serializers perform canonical <-> Save V2 conversion.

Gameplay code should not depend on legacy byte layouts.

## 10. Phase order

Phase 0 is complete when the capacity contract, ID include, save contract, validator,
and mapper-independent resource contract exist.

Next phases:

1. import/verify the Japanese Gold baseline;
2. establish canonical registry manifests;
3. convert Species/Move/Item accessors to 16-bit-safe APIs;
4. introduce generic Variety/Form access;
5. introduce Save V2 serializer/importer;
6. route graphics/text/audio through the resource directory;
7. append verified later-generation datasets.

The key rule is simple: **expand the architecture first; populate it second.**
