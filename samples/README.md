# 정본 (Reference Templates) — 수정 금지

신규 논문은 이 셋의 마크업·CSS·인터랙션을 베껴 시작한다.

| 파일 | 세대 | 추가된 패턴 |
|---|---|---|
| `SAFE.html` | 1세대 | 6탭 골격, v3 디자인 토큰, 문장 페어링(문단 단위), 의사코드+슬라이더 시뮬레이터 |
| `FrameFusion.html` | 2세대 | 문장 단위 페어링, `.eq-link` 수식↔본문 cross-tab 점프, `.fig-hotspot` 그림 핫스팟, `.glossary` 호버 툴팁, `#ff-toc` 사이드바 TOC |
| `SGL.html` | 3세대 | `study-fab` + `study-modal` 자산별 전문가 해설 모달, ⑤ Simulator 3-Part 정형(의사코드 → 인터랙티브 슬라이더 → 좌우 코드 비교), 빌더 없이 대화형으로 직접 작성 |

신규 논문은 **3세대(SGL) 인터랙션을 베이스**로 하되, 셸·토큰·마이크로 디자인은 1·2세대 정본을 그대로 사용한다.

---

## 함께 있는 파일

- `design/` — 로고 등 디자인 자산 (acas-logo.png 외).
- `free_example/` — 완성 **워크드 예제**(FREE 논문). 입력 JSON(config/structured/analysis/tabs_data) → `_build.py` → 단일 HTML 조립의 전 과정을 담은 유일한 빌드-데이터 예제.

## 작업 데이터는 어디?

`SAFE.html` / `FrameFusion.html` / `SGL.html` 세 견본은 **결과물의 동결된 사본**이며, 그 원본 빌드 데이터(PDF·구조화 JSON 등)는 이 배포본에 포함하지 않는다(디자인·인터랙션을 베끼는 기준으로만 사용).

빌드 데이터 → HTML 조립의 실제 예시가 필요하면 **`free_example/`**(완성 워크드 예제)를 본다. 신규 논문의 코드/CSS/JS는 이걸 베이스로 한다.
