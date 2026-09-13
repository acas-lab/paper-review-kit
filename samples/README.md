# 정본 (Reference Templates) — 수정 금지

## 최종 정본 — v4 대시보드 8탭 (신규 논문 기준)

**`cares/`** — CARES 논문(ACL 2026) 전체를 담은 **유일한 v4 워크드 정본**. 실제 데이터(config·structured·
translations·analysis·tabs_data(+study.json)·assets) + 빌더 `_build.py` + 완성 산출물 `CARES_output.html`.
**신규 논문의 셸·헤더·8탭·Paper Study·디자인 토큰은 모두 여기를 복사 출발점으로 한다.**

- 빌드: `python samples/cares/_build.py` (v3 조립) → `python tools/restyle_dash_v4.py "samples/cares"` (v4 변환).
  그 뒤 주입기 4개를 같은 자리에서 돌린다 - `tools/memo_layer_fix.py` (메모 레이어 z=2400·자리 배분) → `tools/qa_button_inject.py` (메모 Q&A 버튼) · `tools/study_review_inject.py` (Study 검토 버튼) · `tools/reader_asset_chip.py` (리더 자산 칩). 모두 인자는 "samples/cares", additive·idempotent 라 여러 번 돌려도 같다.
- 8탭: Translation · Paper Study · Paper Dissection · Background · Mathematics · Diagrams · Code · Q&A.
- 규약 정본: `rules/design_v4_dashboard.md`, Paper Study 컴포넌트 = `rules/component_rules.md` §17.

## 인터랙션 historical 정본 (세대 진화 참고)

인터랙션은 4세대에 걸쳐 진화했고, **`cares/`(4세대)가 이전 세대의 패턴을 모두 흡수**했다.
1~3세대 견본 HTML(SAFE/FrameFusion/SGL)은 배포본에 포함하지 않는다 — 아래는 개념 히스토리다.

| 세대 | 추가된 패턴 | 배포본 |
|---|---|---|
| 1세대 SAFE | 6탭 골격, 문장 페어링(문단 단위), 의사코드+슬라이더 시뮬레이터 | 미포함 |
| 2세대 FrameFusion | 문장 단위 페어링, `.eq-link`(→`ref-link`) 수식↔본문 cross-tab 점프, 그림 핫스팟, `.glossary` 호버 툴팁, 사이드바 TOC | 미포함 |
| 3세대 SGL | `study-fab` 자산 가이드 모달(→우측 드로어), ⑤ Simulator 3-Part 정형, 대화형 직접 작성 | 미포함 |
| **4세대 CARES** | 대시보드 topbar·숫자 없는 8탭(Paper Study·Background/Mathematics 분리)·해시 라우팅·저채도 v4 팔레트 + 위 인터랙션 흡수 | **✅ `cares/`** |

---

## 함께 있는 파일

- `design/` — 로고 등 디자인 자산 (acas-logo.png — 빌더가 v4 topbar에 base64 임베드).

## 작업 데이터는 어디?

셸·인터랙션·데이터 정본은 모두 **`cares/`** 하나로 통일됐다(1~3세대 견본 HTML은 미포함). **빌드 데이터 → HTML 조립의 실제 전 과정**이
필요하면 **`cares/`**(실제 데이터 + 빌더 + 산출물)를 본다 — 신규 논문의 코드/CSS/JS는 이걸 베이스로 한다.

> ⚠️ `cares/`의 그림·원문은 원저작자 저작권(교육·예시 목적 동봉). 재배포·상업적 이용 금지 — `NOTICE.md` 참조.
