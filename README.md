# GOLD

원본 **Pokémon Gold / Pocket Monsters Gold** GBC ROM을 직접 확장해
10세대 이후 데이터 증가를 받아들일 수 있는 구조를 만드는 저장소입니다.

## 범위

GBA/Emerald 기반 확장이 아닙니다. 아래 8개 원본 ROM + SAVE가 모두 작업 대상입니다.

- Japan
- Japan Rev A
- Korea
- USA/Europe
- Germany
- France
- Italy
- Spain

각 릴리스의 원본 주소와 차이를 보존하면서 공통 확장 구조를 적용합니다.

## 현재 구현

Stage 0 original-ROM capacity expansion:

- MBC3 2 MiB / 32 KiB 한계를 MBC30-class 4 MiB / 64 KiB로 확장
- RTC 유지
- 일본판 1 MiB와 지역판 2 MiB를 모두 4 MiB target으로 정규화
- SAVE의 기존 32 KiB를 그대로 보존하고 추가 SRAM 32 KiB를 banks 4..7로 확보
- emulator RTC trailer 44 bytes는 SRAM과 분리하여 그대로 보존
- 한국판 OpenSRAM의 4-bank guard를 8-bank guard로 릴리스 전용 수정
- 8개 ROM 모두 SHA-1 fingerprint로 식별하며 모르는 ROM은 변환 거부

도구:

```sh
python tools/expand_original_gold.py rom input.gbc output.gbc
python tools/expand_original_gold.py save input.sav output.sav
python tools/validate_original_rom_expansion.py
```

실제 ROM/SAVE 전수조사 결과는 `research/gold_release_matrix.json`과
`research/mbc30_expansion_validation.json`에 기록합니다.

ROM/SAV 바이너리는 GitHub에 커밋하지 않습니다.
