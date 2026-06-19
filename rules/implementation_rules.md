# Implementation Rules

## 목적

대화형 HTML 생성을 일관된 방식으로 진행하기 위한 기술 선택 기준.

자동화 빌드 파이프라인은 사용하지 않는다. Stage 10에서 Claude가 단일 HTML을 직접 작성한다.

> 탭 횡단 공용 컴포넌트(hero, tab-intro, ref-link, hotspot, to-top, @media print/mobile, 시뮬레이터·QA 클래스 통일 등)의 정식 결정은 `rules/component_rules.md` 참조.

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
├── config.json          # 메타데이터, asset_layout, wide_assets
├── structured.json      # 섹션/문단 단위 본문
├── translated.json      # 문장 단위 원문/번역 매핑 (선택, 편의용)
├── analysis.json        # callouts, interpretations, beginner_notes, quizzes, hotspots
└── tabs_data/
    ├── dissection.json
    ├── knowledge.json
    ├── questions.json
    ├── qa.json
    └── simulator_spec.md   # ⑤ 결정 사항 문서 (markdown)
```

**식별자 일관성:** `section_id`, `paragraph_id`, `sentence_id`, `asset_id`는 모든 JSON에서 동일하게 매핑.

---

## 4. LLM Processing — 단계별 작업

- **단계별 진행** (Stage 1 ~ 10) — 한 번에 모두 처리하지 않는다
- 각 단계의 입출력 파일이 명확하므로, 단계 간 의존성을 JSON 파일로 전달
- Stage 10(HTML 생성) 전에 1~9가 모두 완료되어 있어야 한다 (단, Stage 8 시뮬레이터와 9 QA는 분량에 따라 1~7과 병렬 진행 가능)

권장 순서:

```
1.  cleaning
2.  structuring
3.  translation
4.  research analysis      → tabs_data/dissection.json + analysis.json#callouts
5.  coaching               → tabs_data/questions.json
6.  figure interpretation  → analysis.json#interpretations + #beginner_notes
7.  background knowledge   → tabs_data/knowledge.json
8.  simulator design       → tabs_data/simulator_spec.md
9.  qa design              → tabs_data/qa.json
10. html generation        → Claude가 단일 HTML 직접 작성
```

---

## 5. HTML Rendering — Stage 10 직접 작성

### 6탭 구조 (정본)

| # | Tab ID | 입력 데이터 |
|---|---|---|
| ① | `tab-reading` | translated.json + analysis.json |
| ② | `tab-dissection` | tabs_data/dissection.json |
| ③ | `tab-knowledge` | tabs_data/knowledge.json |
| ④ | `tab-questions` | tabs_data/questions.json |
| ⑤ | `tab-simulator` | tabs_data/simulator_spec.md |
| ⑥ | `tab-qa` | tabs_data/qa.json |

### 작성 원칙

- **정본 모방:**
  - 디자인 셸·토큰·문장 페어링은 `samples/SAFE_output.html` 또는 `samples/FrameFusion_output.html`의 마크업/CSS를 골격으로 가져온다
  - 학습 인터랙션(자산 모달, ⑤ Simulator 3-Part, eq-link / fig-hotspot 등)은 `samples/SGL_output.html`을 정본으로 한다 (3세대 — 신규 논문 기본 적용 대상)
- **단일 파일:** 모든 CSS는 `<style>`, 모든 JS는 `<script>` 인라인 (외부 분리 금지)
- **외부 의존성 최소:** MathJax 3 (CDN)만 사용. 외부 JS/CSS 라이브러리 추가 금지
- **자산:** **base64 인라인이 기본** (`<img src="data:image/png;base64,...">`). 그림/표/생성 이미지를 모두 인라인. 외부 참조는 개발 미리보기 한정 — 최종 산출물에는 반드시 인라인. 동기는 휴대성 (CLAUDE.md 자산 임베딩 정책 참조).

### CSS / JS

- 디자인 토큰: **`CLAUDE.md`의 "디자인 토큰 (정본 — v3)" 블록**을 정본으로 (흰색 + 라벤더/하늘색/로즈 파스텔). `samples/SAFE_output.html`의 `:root`는 v2 동결분이므로 색 정본으로 사용하지 말 것 — 마크업 셸만 가져온다.
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

- 6 탭 버튼 존재, 클릭 시 패널 전환 (HTML 구조 검증만이라도)
- ① 좌(원문) ↔ 우(번역) `data-pair` 호버 동기화 작동
- 번역 누락 0건 (`<span class="sent">` 안의 빈 텍스트 검출)
- 콜아웃 / 자산 / 해석 / 초보자 노트 위치 검증
- MathJax 렌더 (`mjx-container` 요소 존재)
- ⑤ 시뮬레이터 슬라이더 input 이벤트 → canvas 갱신 코드 포함
- `@media print` + `@media (max-width: 640px)` 두 미디어쿼리 포함
- `<header class="hero">`, `.tab-intro` 6개 (`rules/component_rules.md` §1, §2)

---

## ❗ 금지 사항

- 외부 JS/CSS 라이브러리 추가 (MathJax 외)
- 파이프라인 단계 생략 (Stage 1~9 누락 후 10 직행)
- 6탭 외 탭 추가 / 제거
- 디자인 토큰 임의 변경
- 최종 산출물에 외부 자산 참조 잔존 (반드시 base64 인라인 — 휴대성 정책)
- `samples/`의 정본 파일 (SAFE/FrameFusion/SGL) 수정
- 빌드 스크립트나 자동화 도구 재도입 (의도적 제거된 영역 — 빌더는 모두 삭제됐다)
