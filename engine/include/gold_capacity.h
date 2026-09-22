#ifndef GUARD_GOLD_CAPACITY_H
#define GUARD_GOLD_CAPACITY_H

// GOLD remake capacity policy.
// No unreleased Generation 10 content IDs are assigned here.

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

// Phase 1: consumes only existing unused bits.
#define GOLD_BOX_ITEM_BITS_TARGET 16
#define GOLD_BOX_ITEM_MAX_TARGET  0xFFFF
#define GOLD_BOX_BALL_BITS_TARGET  8
#define GOLD_BOX_BALL_MAX_TARGET   0xFF

// Phase 2 runtime target.
#define GOLD_SPECIES_RUNTIME_BITS_TARGET 16
#define GOLD_MOVE_RUNTIME_BITS_TARGET    16

// Audited persistent geometry.
#define GOLD_BOX_COUNT             14
#define GOLD_MONS_PER_BOX          30
#define GOLD_PC_MON_SLOTS          (GOLD_BOX_COUNT * GOLD_MONS_PER_BOX)
#define GOLD_PARTY_MON_SLOTS        6
#define GOLD_DAYCARE_MON_SLOTS      2
#define GOLD_FUSION_MON_SLOTS       4
#define GOLD_PERSISTENT_MON_SLOTS  (GOLD_PC_MON_SLOTS + GOLD_PARTY_MON_SLOTS + GOLD_DAYCARE_MON_SLOTS + GOLD_FUSION_MON_SLOTS)
#define GOLD_UPSTREAM_BOXMON_SIZE  80

// Bits displaced from BoxPokemon by the planned in-place Species/Move widening:
// tera type 5 + evolution trackers 10 + hyper-training flags 6.
#define GOLD_AUX_BITS_PER_MON      21
#define GOLD_AUX_PAYLOAD_BYTES    ((GOLD_PERSISTENT_MON_SLOTS * GOLD_AUX_BITS_PER_MON + 7) / 8)
#define GOLD_AUX_HEADER_BYTES      12
#define GOLD_AUX_SIDECAR_BYTES    (GOLD_AUX_HEADER_BYTES + GOLD_AUX_PAYLOAD_BYTES)

#endif // GUARD_GOLD_CAPACITY_H
