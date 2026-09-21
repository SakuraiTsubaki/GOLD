#ifndef GUARD_GOLD_CAPACITY_H
#define GUARD_GOLD_CAPACITY_H

// GOLD remake capacity policy.
// This header documents the intended runtime/persistent limits for the GBA core.
// It does not assign unreleased Generation 10 content IDs.

#define GOLD_CANONICAL_ID_BITS 16
#define GOLD_CANONICAL_ID_MAX  0xFFFF

// Audited pinned pokeemerald-expansion persistent layout.
#define GOLD_UPSTREAM_BOX_SPECIES_BITS 11
#define GOLD_UPSTREAM_BOX_MOVE_BITS    11
#define GOLD_UPSTREAM_BOX_ITEM_BITS    10
#define GOLD_UPSTREAM_BOX_BALL_BITS     6
#define GOLD_UPSTREAM_BOX_TERA_BITS     5

#define GOLD_UPSTREAM_BOX_SPECIES_MAX 2047
#define GOLD_UPSTREAM_BOX_MOVE_MAX    2047
#define GOLD_UPSTREAM_BOX_ITEM_MAX    1023
#define GOLD_UPSTREAM_BOX_BALL_MAX      63

// Phase 1 changes that fit without increasing BoxPokemon.
#define GOLD_BOX_ITEM_BITS_TARGET 16
#define GOLD_BOX_ITEM_MAX_TARGET  0xFFFF
#define GOLD_BOX_BALL_BITS_TARGET  8
#define GOLD_BOX_BALL_MAX_TARGET   0xFF

// Phase 2 contract. Physical serialization is deliberately separate.
#define GOLD_SPECIES_RUNTIME_BITS_TARGET 16
#define GOLD_MOVE_RUNTIME_BITS_TARGET    16

// Audited storage geometry.
#define GOLD_BOX_COUNT            14
#define GOLD_MONS_PER_BOX         30
#define GOLD_TOTAL_BOXED_MONS     (GOLD_BOX_COUNT * GOLD_MONS_PER_BOX)
#define GOLD_UPSTREAM_BOXMON_SIZE 80

#endif // GUARD_GOLD_CAPACITY_H
