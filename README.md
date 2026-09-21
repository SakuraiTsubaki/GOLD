# GOLD

Future-ready modernization workspace for Pokémon Gold.

## Current phase

**Phase 0 — Generation 10-ready expansion architecture**

Before importing game content, GOLD expands the engine contracts that would otherwise
force repeated rewrites as later-generation data is added.

The repository does **not** invent unreleased Generation 10 species, moves, items,
forms, mechanics, counts, or names. It prepares stable capacity and compatibility
rules so official data can be appended when verified.

## Architecture baseline

- 16-bit master IDs for Species, Variety, Form, Move, Item, Ability, Type, and other extensible registries.
- Append-only IDs: existing IDs are never renumbered to make room for a later generation.
- Species identity is separate from battle profile/variety and appearance form.
- Runtime IDs are independent from compact save encoding.
- Versioned save extensions preserve a path for legacy Gen II import while allowing modern metadata.
- Resource lookup is mapper-agnostic: code refers to resource IDs, not hard-coded ROM banks.
- Unknown future mechanics are added through feature/registry descriptors instead of consuming guessed constants.

See [Generation 10 Expansion Architecture](docs/GEN10_EXPANSION_ARCHITECTURE.md).

## First implementation files

- `config/engine_capacity.json` — machine-readable capacity contract.
- `engine/include/extended_ids.inc` — RGBDS constants/macros for 16-bit IDs.
- `tools/validate_capacity.py` — guardrail validator.
- `docs/SAVE_FORMAT_V2.md` — versioned extended-save contract.

Original ROM binaries are never committed.
