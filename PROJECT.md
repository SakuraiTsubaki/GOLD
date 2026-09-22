# GOLD Project

## Canonical direction

GOLD는 **원본 Pokémon Gold / Pocket Monsters Kin·Geum GBC ROM 자체를 확장**하는 프로젝트다.

10세대 대비 확장은 GBA 이식이나 Emerald 계열 런타임을 기준으로 하지 않는다.
각 원본 Gold ROM과 대응 SAVE를 직접 측정하고, 릴리스별 차이를 보존한 상태에서
공통 확장 계층을 원본 엔진에 추가한다.

## First-class source releases

다음 8개 ROM과 대응 SAVE를 모두 독립 입력으로 취급한다.

1. Pocket Monsters Kin (Japan)
2. Pocket Monsters Kin (Japan) (Rev A)
3. Pocket Monsters Geum (Korea)
4. Pokémon Gold Version (USA, Europe)
5. Pokémon Goldene Edition (Germany)
6. Pokémon Version Or (France)
7. Pokémon Versione Oro (Italy)
8. Pokémon Edición Oro (Spain)

일본판만 구현하고 나머지를 번역 파생판으로 처리하지 않는다.
공통 로직은 공유하되 주소·빈 뱅크·SAVE geometry·릴리스별 패치는 각각 기록한다.

## Original-ROM expansion target

현재 검증된 Stage 0 목표는 **MBC30-class** 확장이다.

- ROM: 4 MiB / 256 x 16 KiB banks
- SRAM: 64 KiB / 8 x 8 KiB banks
- RTC: 유지
- 기존 cartridge type: 0x10 유지
- ROM size code: 0x07
- RAM size code: 0x05

8개 ROM 모두 bank-switch entry가 ROM offset 0x0010에서 8-bit bank 값을 그대로
$2000에 기록하는 형태임을 실측했다. 따라서 MBC30의 bank $80..$FF를 위한
기본 bank number 폭은 이미 맞는다.

한국판은 OpenSRAM에 bank < 4 검사가 있어 MBC30 SRAM banks 4..7 접근을 위해
릴리스 전용 1-byte patch가 필요하다.

## Generation 10 readiness

물리 용량 확장은 시작점이다. 논리 ID는 별도로 확장한다.

- Species / Variety / Form: 16-bit master ID
- Move / Item / Ability / Type: 16-bit master ID
- Evolution method / resource / feature: 16-bit master ID
- append-only namespace
- 기존 8-bit 원본 레이아웃은 compatibility decoder로 취급
- SAVE 확장 banks 4..7에는 versioned GOLD extension blocks 사용

미출시 10세대 데이터의 이름·개수·메커니즘은 추측하지 않는다.

ROM/SAV 바이너리는 저장소에 커밋하지 않는다.
