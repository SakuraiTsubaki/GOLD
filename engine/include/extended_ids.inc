; GOLD Generation 10-ready ID contract
; RGBDS-compatible constants/macros.
;
; All cross-subsystem identities are 16-bit master IDs.
; Compact on-disk/on-save encodings must be decoded before gameplay logic.

DEF GOLD_MASTER_ID_BITS EQU 16
DEF GOLD_MASTER_ID_SIZE EQU 2
DEF GOLD_ID_NONE        EQU 0
DEF GOLD_ID_MIN         EQU 1
DEF GOLD_ID_MAX         EQU $ffff

DEF GOLD_SPECIES_ID_SIZE          EQU 2
DEF GOLD_VARIETY_ID_SIZE          EQU 2
DEF GOLD_FORM_ID_SIZE             EQU 2
DEF GOLD_MOVE_ID_SIZE             EQU 2
DEF GOLD_ITEM_ID_SIZE             EQU 2
DEF GOLD_ABILITY_ID_SIZE          EQU 2
DEF GOLD_TYPE_ID_SIZE             EQU 2
DEF GOLD_EVOLUTION_METHOD_ID_SIZE EQU 2
DEF GOLD_RESOURCE_ID_SIZE         EQU 2
DEF GOLD_FEATURE_ID_SIZE          EQU 2

; Store a canonical master ID in ROM/RAM structures that use native IDs.
MACRO gold_id
    dw \1
ENDM

; Assert a literal ID is inside the canonical namespace.
MACRO gold_assert_id
    ASSERT (\1) >= GOLD_ID_NONE
    ASSERT (\1) <= GOLD_ID_MAX
ENDM
