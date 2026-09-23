# GOLD legacy ID expansion — Stage 1

This stage continues directly from the 4 MiB ROM / 64 KiB SRAM expansion and is based on all eight supplied original Gold ROM/SAV pairs.

## What the ROM census proved

The legacy persistent Pokémon record is 32 bytes and stores the extensible identities as single bytes:

\`\`\`text
+0 species   u8
+1 item      u8
+2 move 1    u8
+3 move 2    u8
+4 move 3    u8
+5 move 4    u8
\`\`\`

The eight releases have different physical addresses, but the three core data tables are byte-identical across every release:

| Table | Legacy entries | Entry size | Shared SHA-256 |
| --- | ---: | ---: | --- |
| BaseData | 251 | 32 | \`dccd0f065a1ccba8ee1a1b7dbee960574499262a2739f46f67fa2f7e686654ac\` |
| Moves | 251 | 7 | \`e84da1c005921f4352d9bbd83bd5a5885a12b0bbdcfd9ddc14c8ceb50c42670e\` |
| ItemAttributes | 256 | 7 | \`34ef5e76d33d6a92dfc85d55afbefc9bedd5d79c5de4feac1b5001f1d14a74d5\` |

\`research/legacy_id_path_matrix.json\` records, for every release, the exact \`GetBaseData\` and \`GetItemAttr\` offsets, table bank/address/physical offset, and every direct \`LD HL, table+field\` reference found by the binary census. Moves have 22 direct table references in seven releases and 23 in Korea; the BaseData and item direct-reference counts vary by localization.

## GOLDREG ROM registry seed

Stage 1 no longer leaves all new ROM banks as padding. \`tools/expand_original_gold.py\` writes a registry seed into ROM bank \`$80\` (physical offset \`0x200000\`).

\`\`\`text
bank $80
+0000 GOLDREG header
+0040 registry directory
+0100 legacy BaseData copy
      legacy Moves copy
      legacy ItemAttributes copy
\`\`\`

The directory marks each registry as a 16-bit master-ID namespace. The legacy copies are the verified common starting dataset; later records append in expanded banks instead of renumbering the original 1..251/255 identities.

## GOLD_SAVE_V2 high-byte sidecar

The original 32 KiB SRAM in banks 0..3 remains byte-exact. Banks 4..7 contain the versioned extension.

Bank 4 begins with a \`GOLDV2\` header and directory. The first two blocks are:

1. \`MON_ID_HIGH\`: 288 logical persistent-mon slots × 6 bytes = 1,728 bytes. Per slot: species high byte, held-item high byte, move1..move4 high bytes.
2. \`INVENTORY_ITEM_HIGH\`: 107 bytes for the 20 item slots, 50 PC-item slots, 12 ball slots, and 25 key-item slots.

For an original save every high byte is zero, so the canonical identity is initially identical to the original 8-bit ID:

\`\`\`text
canonical_id = legacy_low_byte | (extension_high_byte << 8)
\`\`\`

The 288 mon slots cover the larger localized PC capacity (280) plus party (6) and daycare (2). Japanese PC storage uses 270 of those PC slots and leaves the remaining ten reserved.

Each extension block and header is protected with CRC-16/CCITT. The 44-byte emulator RTC trailer remains outside SRAM and is moved intact behind the expanded 64 KiB SRAM image.

## Next hook slice

The storage is now present, but the original execution paths still read 8-bit IDs. The next binary-patch slice is therefore:

- add 16-bit current Species/Move/Item shadow accessors;
- hook \`GetBaseData\` in all eight release profiles to \`GOLDREG\`;
- replace/direct the 22/23 \`Moves\` references through the extended move accessor;
- hook \`GetItemAttr\` and the remaining direct ItemAttributes references;
- update mon copy/move/save paths so the six high bytes move with the corresponding legacy mon slot;
- add >255 round-trip tests before adding any later-generation dataset.
