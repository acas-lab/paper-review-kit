# Implementation Rules

## 목적

대화형 HTML 생성을 일관된 방식으로 진행하기 위한 기술 선택 기준.

자동화 빌드 파이프라인은 사용하지 않는다. Stage 10에서 Claude가 단일 HTML을 직접 작성한다.

> 탭 횡단 공용 컴포넌트(v4 topbar, tab-intro, ref-link, hotspot, to-top, study-drawer, @media print/mobile, 시뮬레이터·QA 클래스 통일 등)의 정식 결정은 `rules/component_rules.md` 참조. 셸·헤더·탭·토큰은 `rules/design_v4_dashboard.md`.

---

## 1. PDF Parsing

- **권장 도구:** PyMuPDF (`fitz`) 또는 동등 도구
- 텍스트는 페이지별 블록 단위로 추출 → 다단(2-column) 순서 복원
- Figure / Table은 bbox로 잘라 PNG 저장 (`papers/[name]/assets/fig_N.png`, `table_N.png`)
- 수동 bbox 보정 권장 (자동 추출만으로는 잘림이 흔하다)

---

## 2. Text Processing

- 줄바꿈 / 하이픈 줄바꿈 / 깨진 단어 복원 필수
- 페이지 헤더 / 푸터 제거
- 수식·인용·각주는 보존
- 자세한 규약: `rules/parsing_rules.md`

---

## 3. Data Structure (JSON)

모든 콘텐츠는 JSON으로 보존. 스키마는 `workflow.md`의 각 Stage 정의를 따른다.

표준 파일 구성:

```
papers/[name]/
├── config.json          # 메타데이터(meta), asset_layout, wide_assets, captions(KR), captions_en(EN)
├── structured.json      # 섹션/문단/문장 단위 본문 (tools/structure_paper.py 산출)
├── translated.json      # 문장 단위 원문/번역 매핑 (선택, 편의용)
├── analysis.json        # callouts, interpretations, beginner_notes, quizzes, hotspots, study_modals
├── study/               # ①′ Paper Study 노트 내보내기 저장소 (+.gitkeep)
└── tabs_data/
    ├── dissection.json
    ├── knowledge.json
    ├── questions.json
    ├── study.json          # ①′ Paper Study 7-Step (Stage 11)
    ├── qa.json             # ⑥ (on-demand)
    └── simulator_spec.md   # ⑤ 결정 사항 문서 (on-demand)
```

**식별자 일관성:** `section_id`, `paragraph_id`, `sentence_id`, `asset_id`는 모든 JSON에서 동일하게 매핑.

---

## 4. LLM Processing — 단계별 작업

- **단계별 진행** (Stage 0 ~ 11) — 한 번에 모두 처리하지 않는다
- 각 단계의 입출력 파일이 명확하므로, 단계 간 의존성을 JSON 파일로 전달
- Stage 10(HTML 생성) 전에 0~7 + 11이 완료되어 있어야 한다 (⑤ Stage 8 · ⑥ Stage 9는 **on-demand** — 기본 빌드 제외, 셸만)

권장 순서 (실행 순서 = 파일 번호와 다름, `workflow.md` 참조):

```
0.  pdf parsing            → structured.json 초안 (tools/structure_paper.py) + assets (tools/autocrop_assets.py)
1.  cleaning
2.  structuring            → structured.json (섹션/문단/문장)
3.  translation            → translations/manual.json + config#captions(KR)/captions_en(EN)
4.  research analysis      → tabs_data/dissection.json + analysis.json#callouts
5.  coaching               → tabs_data/questions.json
6.  figure interpretation  → analysis.json#interpretations + #beginner_notes + #study_modals
7.  background knowledge   → tabs_data/knowledge.json (Background + Mathematics 공용)
11. paper study            → tabs_data/study.json (①′ — 기본 빌드 포함)
8.  simulator design ⏸     → tabs_data/simulator_spec.md (on-demand)
9.  qa design ⏸            → tabs_data/qa.json (on-demand)
10. html generation        → _build.py 조립 → tools/restyle_dash_v4.py 변환 (v4 8탭)
```

---

## 5. HTML Rendering — Stage 10 직접 작성

### 8탭 구조 (정본 — v4 대시보드)

셸·헤더·탭·토큰은 `rules/design_v4_dashboard.md`가 정본 (숫자 없는 8탭 · topbar · 해시 라우팅).

| # | Tab ID | 라벨 | 입력 데이터 |
|---|---|---|---|
| ① | `tab-reading` | Translation | translated.json + analysis.json |
| ①′ | `tab-study` | Paper Study | tabs_data/study.json (+ config#captions_en) |
| ② | `tab-dissection` | Paper Dissection | tabs_data/dissection.json |
| ③ | `tab-knowledge` | Background | tabs_data/knowledge.json (개념 카드) |
| ③′ | `tab-math` | Mathematics | tabs_data/knowledge.json (eq-panel 분리) |
| ④ | `tab-questions` | Diagrams | tabs_data/questions.json |
| ⑤ | `tab-simulator` | Code | tabs_data/simulator_spec.md (셸만) |
| ⑥ | `tab-qa` | Q & A | tabs_data/qa.json (셸만) |

Mathematics는 knowledge.json의 eq-panel을 `tools/restyle_dash_v4.py`가 분리해 만든다 (별도 준비물 없음). Paper Study는 study.json이 없으면 자동 셸.

### 작성 원칙

- **정본 모방:**
  - 셸·헤더·탭·디자인 토큰은 **v4 대시보드**(`rules/design_v4_dashboard.md`) — `_build.py` 조립 후 `tools/restyle_dash_v4.py`로 변환
  - 학습 인터랙션(자산 모달·study-drawer, ⑤ Simulator 3-Part, eq-link / fig-hotspot, Paper Study 등)은 `samples/cares/CARES_output.html`을 인터랙션 정본으로 한다 (3세대 베이스 — v4 셸 위에 얹음)
- **단일 파일:** 모든 CSS는 `<style>`, 모든 JS는 `<script>` 인라인 (외부 분리 금지)
- **외부 의존성 최소:** MathJax 3 (CDN)만 사용. 외부 JS/CSS 라이브러리 추가 금지
- **자산:** **base64 인라인이 기본** (`<img src="data:image/png;base64,...">`). 그림/표/생성 이미지를 모두 인라인. 외부 참조는 개발 미리보기 한정 — 최종 산출물에는 반드시 인라인. 동기는 휴대성 (CLAUDE.md 자산 임베딩 정책 참조).

### CSS / JS

- 디자인 토큰: **`rules/design_v4_dashboard.md` §1 (v4 저채도 grey-lavender)** 이 최종 정본. 빌더 템플릿은 `CLAUDE.md`의 v3 토큰으로 조립한 뒤 `tools/restyle_dash_v4.py`가 v4로 스왑한다(2단). 빌더 템플릿의 v3 `:root`는 중간 산물이므로 최종 색 정본으로 쓰지 말 것 — 변환 뒤 v4 색이 정본.
- 탭 셸: `<nav class="tabs">` + `<section id="tab-XXX" class="tab-pane">` 패턴
- 탭 전환 JS는 `<body>` 끝에 인라인
- ⑤ 시뮬레이터 위젯은 vanilla JS (canvas API)

---

## 6. Math Handling

- LaTeX 유지 (`$...$` 인라인, `$$...$$` display)
- MathJax 3 (CDN): `https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js` 또는 `tex-chtml.js`
- 탭 전환 시 `MathJax.typesetPromise()` 재호출 필수
- 자세한 규칙: `rules/math_rules.md`

---

## 7. 검증 (Stage 10 후 자체 점검)

Claude가 HTML을 작성한 뒤 자체 점검:

- 8 탭 버튼 존재(`tab-reading`·`tab-study`·`tab-dissection`·`tab-knowledge`·`tab-math`·`tab-questions`·`tab-simulator`·`tab-qa`), 해시 라우팅 전환
- ① 좌(원문) ↔ 우(번역) `data-pair` 호버 동기화 작동
- 번역 누락 0건 (`<span class="sent">` 안의 빈 텍스트 검출)
- 콜아웃 / 자산 / 해석 / 초보자 노트 위치 검증
- MathJax 렌더 (`mjx-container` 요소 존재)
- ①′ Paper Study 동작 + `python tools/check_study_refs.py`·`check_html_escape.py` 통과 (§17 · `workflow.md` Stage 10 체크리스트)
- `@media print` + `@media (max-width: 640px)` 두 미디어쿼리 포함
- v4 **`.topbar`**(hero 카드 아님), `.tab-intro` 8개 (`rules/design_v4_dashboard.md` §2 · `rules/component_rules.md` §2)

---

## ❗ 금지 사항

- 외부 JS/CSS 라이브러리 추가 (MathJax 외)
- 파이프라인 단계 생략 (Stage 0~7 + 11 누락 후 10 직행)
- 8탭 외 탭 추가 / 제거
- 디자인 토큰 임의 변경 (v4 정본 = `rules/design_v4_dashboard.md` §1)
- 최종 산출물에 외부 자산 참조 잔존 (반드시 base64 인라인 — 휴대성 정책)
- `samples/`의 정본(`samples/cares/`) 수정
- 결정적 단계를 손으로 대체 (본문 구조화 = `tools/structure_paper.py`, 자산 크롭 = `tools/autocrop_assets.py`, v4 변환 = `tools/restyle_dash_v4.py` — CLAUDE.md §web↔CLI 통일성). 단, **범용 자동화 빌드 파이프라인은 재도입하지 않는다** — 논문별 `_build.py` 조립은 대화형으로.
