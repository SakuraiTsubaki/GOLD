# GOLD

**ポケットモンスター 金**을 원전으로 조사하고, 10세대 이후까지 버틸 수 있는 확장 구조를 구축하는 저장소입니다.

## 현재 정본 방향

- 일본판 원작과 확인된 revision을 Master Reference로 전수조사합니다.
- ROM과 SAVE를 따로 실측하고 release별 차이를 보존합니다.
- 10세대 대비 확장은 **GOLD 자체의 16-bit master ID, Save V2, resource/ROM-bank abstraction**을 기준으로 진행합니다.
- 미출시·미검증 세대 콘텐츠는 추측하지 않습니다.
- 최종 GBA 리메이크 구현에서 다른 3세대 엔진/맵/자산을 참고할 수 있지만, 그것들이 GOLD의 용량·ID·세이브 정본이 되지는 않습니다.

## 원본 및 조사

- 원본 조사: `SakuraiTsubaki/PocketMonsters-Kin-Disassembly`
- 일본판 원본: `Pocket Monsters Kin (Japan).gbc`, `Pocket Monsters Kin (Japan) (Rev A).gbc`
- 지역별 Gold ROM/SAV는 독립 프로필로 유지합니다.

## 확장 문서

- `PROJECT.md` — 현재 프로젝트 방향
- `config/engine_capacity.json` — 16-bit master ID / Save V2 용량 계약
- `docs/GEN10_EXPANSION_ARCHITECTURE.md` — 10세대 대비 확장 구조
- `docs/SAVE_FORMAT_V2.md` — GOLD 자체 Save V2 계약
- `research/ROM_SAVE_BASELINE.md` — 실제 Gold ROM/SAV 실측

ROM 바이너리는 GitHub에 커밋하지 않습니다.
