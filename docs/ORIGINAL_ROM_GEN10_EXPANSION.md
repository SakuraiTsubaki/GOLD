# Original Gold ROM Generation 10+ Expansion

## Measured baseline

모든 제공 Gold ROM의 cartridge type은 0x10 (MBC3 + RTC + RAM + battery)이다.
일본판/Rev A는 1 MiB, 나머지 6개 지역판은 2 MiB다. 모든 SAVE의 cartridge SRAM
부분은 32 KiB이며, 제공된 save container에는 그 뒤에 44-byte RTC trailer가 있다.

## Why MBC30 first

일반 MBC3는 2 MiB ROM / 32 KiB SRAM / RTC 조합이 한계다.
MBC30-class는 같은 MBC3 계열 RTC 모델을 유지하면서 ROM bank를 256개,
SRAM bank를 8개로 늘릴 수 있어 Gold 원본 엔진을 확장하는 첫 단계로 적합하다.

Stage 0 header target:

```text
0x0147 cartridge type = 0x10
0x0148 ROM size       = 0x07  (4 MiB)
0x0149 RAM size       = 0x05  (64 KiB)
```

## ROM bank switching census

8개 ROM 모두 ROM offset `0x0010`에 다음 sequence가 있다.

```text
E0 9F       LDH [hROMBank], A
EA 00 20    LD [$2000], A
C9          RET
```

bank number를 7-bit로 mask하지 않고 A 전체를 기록하므로 MBC30 target에서
`$80..$FF` bank 번호를 전달할 수 있다.

## SRAM banking difference

Japan/Rev A/USA-Europe/Germany/France/Italy/Spain의 OpenSRAM 루틴은 전달된 bank를
그대로 `$4000`에 기록한다.

Korea만 함수 진입부에서:

```text
CP $04
JR C, ...
```

검사를 한다. MBC30의 SRAM banks 0..7을 허용하기 위해 해당 immediate를
`$04 -> $08`로 바꾼다. SHA-1이 정확히 한국판으로 확인된 경우에만 적용한다.

## Physical transformation

`tools/expand_original_gold.py rom`:

1. SHA-1로 8개 지원 릴리스를 식별한다.
2. 원본 header/global checksum과 header fields를 검증한다.
3. release-specific precondition을 검증한다.
4. 필요한 release patch를 적용한다.
5. ROM을 4 MiB까지 0xFF로 pad한다.
6. ROM/RAM size header를 MBC30 target으로 갱신한다.
7. 두 checksum을 다시 계산한다.

`tools/expand_original_gold.py save`:

1. 기존 0x8000 SRAM bytes를 byte-exact 보존한다.
2. 새 SRAM banks 4..7용 0x8000 bytes를 추가한다.
3. 입력에 44-byte RTC trailer가 있으면 새 SRAM 뒤로 그대로 이동/보존한다.

결과 save container는 RTC trailer가 있는 경우 `0x1002C` bytes다.

## Next ID expansion

Stage 0이 bank와 persistent space를 만든다. 다음 단계는 원본 ROM의 실제
Species/Move/Item table과 access sites를 8개 릴리스에서 전수조사하여 다음 계층으로
옮기는 것이다.

```text
legacy u8 ID <-> compatibility map <-> canonical u16 master ID
```

Species/Form/Move/Item/Ability 등은 서로 독립된 16-bit registry로 만들고,
새 ROM banks에는 registry directory와 expanded tables를 배치한다.
