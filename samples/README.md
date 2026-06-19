# 정본 (Reference Templates) — 수정 금지

신규 논문은 이 셋의 마크업·CSS·인터랙션을 베껴 시작한다.

| 파일 | 세대 | 추가된 패턴 |
|---|---|---|
| `SAFE_output.html` | 1세대 | 6탭 골격, v3 디자인 토큰, 문장 페어링(문단 단위), 의사코드+슬라이더 시뮬레이터 |
| `FrameFusion_output.html` | 2세대 | 문장 단위 페어링, `.eq-link` 수식↔본문 cross-tab 점프, `.fig-hotspot` 그림 핫스팟, `.glossary` 호버 툴팁, `#ff-toc` 사이드바 TOC |
| `SGL_output.html` | 3세대 | `study-fab` + `study-modal` 자산별 전문가 해설 모달, ⑤ Simulator 3-Part 정형(의사코드 → 인터랙티브 슬라이더 → 좌우 코드 비교), 빌더 없이 대화형으로 직접 작성 |

신규 논문은 **3세대(SGL) 인터랙션을 베이스**로 하되, 셸·토큰·마이크로 디자인은 1·2세대 정본을 그대로 사용한다.

---

## 함께 있는 파일

- `design/` — 로고 등 디자인 자산 (acas-logo.png 외).

## 관련 자료의 보관 위치

- v2(beige+maroon) 백업 `*.before_v3` 3편 — `_archive/v2_backups/` (회복용 historical record)
- 리컬러 스크립트 `_recolor_v3.py` — `_archive/`의 `samples_recolor_v3.py`, `sgl_recolor_v3.py` (실행 완료)
- pre-SAFE 시기 디자인 영감 자료 (Focus_analysis, VLA-Cache_analysis_v3) — `_archive/personal_study/`

## 작업 데이터는 어디?

각 정본 논문의 원본 PDF·구조화 JSON·번역·자산 등 빌드 데이터는 `papers/[N. shortname]/`에 보관:

- `papers/1. safe_learning/`
- `papers/2. frame_fusion/`
- `papers/3. sgl/`

여기 `samples/`의 HTML은 **그 결과물의 동결된 사본**이다. 데이터를 다시 다듬어 재빌드하더라도, 정본은 명시적 결정 없이는 갱신되지 않는다.
