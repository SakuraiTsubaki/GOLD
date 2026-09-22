# Original-ROM Expansion Policy

## Scope

GOLD에서 현재 확장 대상은 GBA 리메이크가 아니라 **원본 Gold GBC ROM**이다.

## Release policy

일본판만을 구현 대상으로 삼지 않는다. Japan, Japan Rev A, Korea, USA/Europe,
Germany, France, Italy, Spain 8개 릴리스 모두 first-class profile이다.

공통 패치가 가능하면 공통화하되 다음 항목은 release-specific evidence로 유지한다.

- ROM/SAVE hashes
- ROM 크기와 빈 bank
- bank-switch / OpenSRAM 주소
- 지역별 text/font/data layout
- SAVE box geometry
- revision-specific code differences

## Expansion policy

Stage 0은 RTC를 유지하면서 MBC30-class 4 MiB ROM / 64 KiB SRAM으로 확장한다.

Stage 1 이후에는 원본의 8-bit Species/Move/Item ID를 compatibility representation으로
남기고 게임 로직의 master namespace를 16-bit로 확장한다.

SAVE banks 0..3은 원본 compatibility image로 보존한다.
banks 4..7은 versioned extension directory와 later-generation persistent data에 쓴다.

## Future-content rule

10세대 대비는 capacity와 schema를 미리 넓힌다는 뜻이다.
미출시 종·기술·아이템·특성·메커니즘을 추측하여 채우지 않는다.
