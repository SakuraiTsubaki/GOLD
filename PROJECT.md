# GOLD Project

## Canonical direction

ポケットモンスター 金을 원전으로 전수조사하고, GOLD 자체의 확장 가능한 데이터/세이브/리소스 구조를 먼저 구축한다.

최종 리메이크 실행 대상은 Game Boy Advance일 수 있지만, **10세대 대비 용량/ID/세이브 설계의 정본은 GOLD 자체**다. Emerald 또는 pokeemerald-expansion을 GOLD의 확장 런타임 기준으로 사용하지 않는다.

## Original baseline

- `Pocket Monsters Kin (Japan).gbc`
- `Pocket Monsters Kin (Japan) (Rev A).gbc`
- 각 지역 Gold ROM/SAV는 독립 프로필로 조사한다.

원본 조사 저장소: `SakuraiTsubaki/PocketMonsters-Kin-Disassembly`

ROM과 SAVE는 서로 다른 증거 계층으로 다룬다.

## Generation 10-ready expansion baseline

- Master IDs: 16-bit
- Species / variety / form / move / item / ability / type / evolution method / resource / feature registries are append-only
- Save: versioned `GOLD_SAVE_V2`
- Legacy Gold saves are imported through release-specific decoders
- Resource addressing is mapper-independent
- 미출시/미검증 10세대 콘텐츠는 추측하지 않는다.

## GBA remake references

Generation III engines, Emerald, FireRed/LeafGreen and other GBA projects may be used later as **implementation or asset/reference donors only**. They do not define GOLD's canonical IDs, save capacity, or expansion contract.

원작의 지역·스토리·이벤트·NPC·버전 고유성은 보존한다.
