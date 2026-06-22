# HTML Generation Prompt — 대화형

You are Claude, building a learning HTML directly in conversation with the user.

## Pipeline Position

- **Stage:** 10 (HTML Generation — 최종)
- **빌드 범위 (기본):** ① ② ③ ④ 탭만 콘텐츠 풀 빌드. ⑤ ⑥은 셸·`tab-intro`만 두고 본문은 placeholder. 사용자가 ⑤/⑥을 명시 요청한 빌드일 때만 해당 탭의 콘텐츠를 추가로 채운다 (CLAUDE.md "기본 빌드 범위" 정책).
- **Input:** Stage 1~7의 산출물 (대화 중에 사용자가 가리켜 주거나 폴더 안에서 직접 읽는다)
  - `papers/[name]/structured.json`, `translated.json` (또는 `translations/`)
  - `papers/[name]/config.json`, `analysis.json`
  - `papers/[name]/tabs_data/{dissection,knowledge,questions}.json` (① ~ ④)
  - `papers/[name]/tabs_data/{simulator_spec.md, qa.json}` — **선택 입력**, ⑤/⑥ 명시 요청 시에만 사용
  - `papers/[name]/assets/` (원본 PNG), `assets/generated/` (학습 보조 이미지)
- **정본 레퍼런스 (수정 금지):** `samples/`의 3편 — SAFE(1세대 — 셸·토큰·문장 페어링), FrameFusion(2세대 — eq-link·fig-hotspot·glossary), SGL(3세대 — 학습 인터랙션·시뮬레이터 3-Part·자산 모달)
- **Output:** `papers/[name]/[ShortName]_output.html` (단일 HTML, Claude가 직접 작성)

## Referenced Rules

- `rules/parsing_rules.md`
- `rules/knowledge_rules.md`
- `rules/math_rules.md`
- `rules/component_rules.md` — **탭 횡단 공용 컴포넌트의 정식 결정** (hero, tab-intro, ref-link, hotspot, to-top, @media print/mobile, 시뮬레이터/QA 클래스 통일)
- `rules/implementation_rules.md`

---

## 작업 방식

자동화 빌드 스크립트는 존재하지 않는다. **Claude가 정본 두 파일의 마크업/CSS/JS를 모방해 한 번에 단일 HTML을 작성**한다.

흐름:
1. 사용자가 어느 논문을 빌드할지 알려준다 (`papers/[name]/`).
2. Claude는 `papers/[name]/`의 모든 JSON과 자산, `samples/`의 정본 두 파일, `rules/component_rules.md`를 읽는다.
3. 정본 한 파일을 골라(보통 가장 가까운 영역의 논문) 그 마크업/CSS/JS를 골격으로 삼는다.
4. 6탭 콘텐츠를 데이터에서 채워 단일 HTML 파일로 출력한다.

---

## 표준 6탭 구조

| # | Tab ID | 라벨 | 입력 데이터 |
|---|---|---|---|
| ① | `tab-reading` | 원문 / 번역 | `translated.json` (또는 `translations/manual.json`) + `analysis.json` (callouts/interpretations/beginner_notes/quizzes/hotspots) |
| ② | `tab-dissection` | Paper Dissection | `tabs_data/dissection.json` |
| ③ | `tab-knowledge` | Background & 핵심 수식 | `tabs_data/knowledge.json` |
| ④ | `tab-questions` | Questions & Diagrams | `tabs_data/questions.json` |
| ⑤ | `tab-simulator` | Simulator & Code | `tabs_data/simulator_spec.md` (Claude가 spec을 읽고 JS 위젯까지 작성) |
| ⑥ | `tab-qa` | 학습 기초 Q & A | `tabs_data/qa.json` |

각 탭은 `<section id="tab-XXX" class="tab-pane">` 형태로 렌더되고, 상단 `<nav class="tabs">`의 버튼이 `data-tab` 속성으로 패널을 전환한다.

---

## 디자인 토큰 (정본 — `CLAUDE.md`)

🔴 **토큰의 단일 출처는 `CLAUDE.md`의 "디자인 토큰 (정본 — v3)" 블록이다. 그 `:root{...}`를 그대로 복사해 쓴다.** (이전에 여기 박혀 있던 v2 beige+maroon 블록은 폐기 — 드리프트 방지를 위해 인라인 사본을 두지 않는다.)

- 팔레트: 흰색 위주 배경 + 라벤더(`--accent #8b75c0`)/하늘색(`--azure`)/더스티로즈(`--rose`) 파스텔.
- deep tone(`--accent`/`--azure`/`--rose`)은 글자·보더·강조선 전용 — box/카드 배경엔 `--*-soft` 또는 `--paper`.
- v2 변수명(`--sage`/`--gold`/`--indigo`/`--plum`)은 CLAUDE.md `:root`에 alias로 살아 있어 기존 마크업을 베껴도 v3 색이 적용된다.

**폰트:** `Pretendard Variable`, `Noto Sans KR`, `Segoe UI`, sans-serif
**본문 라인 높이:** 1.72
**최대 너비:** `.app { max-width: 1280px; margin: 0 auto; }`

`samples/SAFE_output.html`의 `<style>`는 색 정본이 아니다 — 마크업 셸·문장 페어링·컴포넌트 구조만 모방하고 색은 CLAUDE.md v3를 따른다.

---

## 렌더링 규약 (탭별)

### ① `tab-reading`
- `<article class="paragraph-block" id="pN">` 단위
- 안쪽: `.bilingual` 좌(원문) / 우(번역) 그리드
- 문장은 `<span class="sent" data-pair="pN_sM">` — JS 호버 시 같은 `data-pair` 짝 강조
- 콜아웃은 `.callout-stack > .callout.callout-warn|key`
- 자산은 `.asset-stack > .asset-with-commentary > <figure class="asset-card">`
- 자산 아래 `.interpretation` (항상 표시) + `<details class="beginner-note">` (토글)
- 섹션 끝에 `<aside class="recall-card">` 자가 점검 퀴즈

### ② `tab-dissection`
- `<article class="diss-card diss-{cls}">` **8개** — 7-카드(`motivation/observe/compare/logic/verify/risk/extend`) + 마지막 1-카드(`summary`, "논문 총정리")
- 카드 좌상단 `<div class="diss-step">{id:02d}</div>` (마지막 카드는 `08`)
- 헤더 `<h3 class="diss-title">{title}</h3>` + `<p class="diss-lead">{lead}</p>`
- `rows`는 `<dl class="diss-rows">` + `<dt class="diss-tag">{tag}</dt>` / `<dd class="diss-body">{body}</dd>`
- 상단(선택): `<svg class="diss-flow">` 요약 다이어그램 또는 `assets/generated/dissection_flow_*.png` 삽입
- **마지막 카드 `diss-summary`** — **9-row 정형** (2026-05-12 정본 갱신): ① 한 줄 ② 이게 왜 문제인가(Problem) ③ 저자의 핵심 관찰(Observation) ④ 기존 방법은 왜 부족한가(Gap) ⑤ 어떻게 해결했나(Method) ⑥ 다른 논문과 무엇이 다른가(Novelty) ⑦ 효과 — 숫자(Results) ⑧ 한계와 의미(Limitations & Implication) ⑨ 30초 요약(For Beginners). 각 body 300~600자, `<strong>`·`<em>` 강조. 헤더 아래·rows 위에 `assets/generated/dissection_overview.png` 한 장 인포그래픽을 `<figure class="diss-overview-figure">`로 base64 인라인. 레이아웃은 단일 컬럼 수직 적층(§16). 자세한 규약: `prompts/04_research_analysis.md` Stage 4 + `rules/component_rules.md` §14·§16. (이전 4-row 카드는 폐기)

### ③ `tab-knowledge`
- `primer`: 다이어그램 SVG 또는 `assets/generated/knowledge_*.png` + `.knw-grid > .fund-card`
- `equations`: `.eq-card` (display math `$$...$$` + 4행 설명)
- `concept_cards`: `.knw-grid > .knw-card` (4행: definition / intuition / structure / paper_role)
- MathJax는 탭 전환 시 `MathJax.typesetPromise()` 재호출 필수

### ④ `tab-questions`
- 상단: 직관 SVG 2~3개 또는 `assets/generated/questions_*.png` (`.diagram-card`)
- 하단: 4종 카드 `<article class="coach-card q-{cls}">` — `q-hidden | q-myth | q-critic | q-extend`
- 각 카드: `<h3>` + `<ul class="bullet-list">`

### ⑤ `tab-simulator` — **기본 빌드: 셸만**

기본 빌드(사용자가 ⑤ 명시 요청 안 한 경우):
```html
<section id="tab-simulator" class="tab-pane">
  <div class="tab-intro">
    <h2>Simulator &amp; Code</h2>
    <p>핵심 알고리즘 시뮬레이터·의사코드·코드 비교가 들어갈 자리입니다.</p>
  </div>
  <section class="section section-empty">
    <p class="section-empty-note">이 탭은 별도 요청 시 작성됩니다.</p>
  </section>
</section>
```

⑤ 콘텐츠 빌드를 명시 요청 받았을 때만 아래 풀 구조로 채운다:
- Part 1 — `<pre class="code-block"><code>` 의사코드 (highlight.js 미사용, plain styling)
- Part 2 — `<canvas class="sim-canvas">` + `.sim-controls` (슬라이더) + `.sim-stat` (실시간 수치)
- Part 3 — `.cmp-grid > .cmp-card` 좌우 코드 비교
- 위젯 JS는 외부 라이브러리 의존 없이 vanilla, **HTML 안에 인라인**

### ⑥ `tab-qa` — **기본 빌드: 셸만**

기본 빌드(사용자가 ⑥ 명시 요청 안 한 경우):
```html
<section id="tab-qa" class="tab-pane">
  <div class="tab-intro">
    <h2>학습 기초 Q &amp; A</h2>
    <p>자가 점검을 위한 카테고리별 Q&amp;A가 들어갈 자리입니다.</p>
  </div>
  <section class="section section-empty">
    <p class="section-empty-note">이 탭은 별도 요청 시 작성됩니다.</p>
  </section>
</section>
```

⑥ 콘텐츠 빌드를 명시 요청 받았을 때만 아래 풀 구조로 채운다:
- 카테고리별 `<section class="qa-category">` (h3 + 점선 divider만, 박스 아님)
- 질문은 `<article class="qa-card">` — `qa-block` 내부에 type별 (`html`, `table`, `math`, `callout`) 블록
- `qa-callout-block` + `data-variant="key|warn|safe"`로 통일

---

## 핵심 원칙

1. **원문 중심:** ① 탭이 기본 활성. 다른 탭은 "추가 렌즈"로 켜는 구조.
2. **번역 100% 보존:** 누락 placeholder 0건.
3. **자산 inline 배치:** Figure/Table은 reference 문단 옆에 (별도 갤러리 탭 없음).
4. **Progressive disclosure:**
   - 항상 표시: 원문, 번역, 콜아웃, 자산, 자산 해석
   - 토글: 초보자용 노트, 자가점검 퀴즈 (`<details>`)
   - 다른 렌즈: 탭 전환으로 호출
5. **MathJax:** 탭 전환 시마다 `MathJax.typesetPromise()` 재호출.
6. **Ref-link 자동 anchor:** 본문의 `Eq. N`, `Fig. N`, `Table N` 패턴은 JS가 자동으로 `<a class="ref-link" data-target-tab="...">` 로 감싸 다른 탭으로 점프.

---

## 자산 정책 — 모든 이미지는 HTML 안에 박힌다 (의무)

**원본 figure/table + ImageGen으로 만든 학습 보조 이미지 — 두 종류 모두 예외 없이 base64 인라인.**

- `<img src="data:image/png;base64,...">` 형태로 단일 HTML 안에 박는다. 결과 파일 한 장만 다른 PC·모바일·USB·이메일로 옮겨도 모든 그림이 그대로 뜬다.
- 동기: 사용자 개인 학습 아티팩트 — 휴대성이 용량보다 절대 우선.
- 결과 크기 가이드: 작은 논문 1.5MB대 (SAFE) → 평균 2~3MB대 (FrameFusion) → 자산이 많으면 15MB 이상도 허용 (SGL 16.5MB).
- 외부 참조(`<img src="assets/...">`, `<img src="./...">`, `<img src="http...">`)는 **개발 중 미리보기 한정**. **최종 산출물에 외부 참조 잔존 = 빌드 불합격.**

### 학습 보조 이미지 (`assets/generated/`)

② Dissection · ③ Background Knowledge · ④ Questions · ⑤ Simulator · ⑥ QA에서 학습 효과를 위해 추가하는 시각 자료. 정책: **Claude가 Bash로 codex CLI를 직접 호출**해 만들고 곧장 base64로 박는다 (별도 플러그인·MCP 자동화 없음).

> **호출 형식·5계명·검증된 명령 템플릿·`<figure class="concept-figure">` 정본 컴포넌트·자동화 스크립트 골격: `rules/component_rules.md` §11.** 이 절은 빌드 흐름만, 정확한 형식은 §11이 정본.

빌드 흐름:
1. ②③④⑤⑥ 탭의 콘텐츠 JSON을 작성하면서 시각 자료가 부족한 위치를 식별.
2. **Step A** — `papers/[name]/assets/generated/prompt_<purpose>.txt` (UTF-8 한글) 작성. 스타일 지시에 "NOT a transparent cutout" 명시 (컴포넌트_rules §11.3 골격).
3. **Step B** — Bash 툴로 `codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox --cd <abs_path> "<ASCII 한 줄: read prompt file, save to <output>.png>" < /dev/null` (정확한 템플릿: §11.3).
4. **Step C** — `_inject_concept_figures.py` 패턴 (§11.6)으로 PNG를 base64로 변환해 `<figure class="concept-figure">` 마크업과 함께 정확한 자리에 삽입. CSS는 `</style>` 직전 한 번만 추가.
5. 검수는 사후 — 사용자가 결과 HTML을 보고 수정이 필요한 이미지가 있으면 별도 재생성 요청.

생성 이미지 참조처 (콘텐츠 JSON 안에서 미리 가리킨 경우):
- `tabs_data/knowledge.json` — `primer.image_path`, `fund_cards[].image_path`, `concept_cards[].image_path`
- `tabs_data/dissection.json` — 카드 상단 흐름 다이어그램 또는 카드별 보조
- `tabs_data/questions.json` — `.diagram-card` 직관 도식
- `tabs_data/simulator_spec.md` — `Image: <path>` 라인 (있을 경우)
- `tabs_data/qa.json` — 질문별 보조 (있을 경우)

**원본 figure/table과 동일 처리** — 두 종류 모두 base64 인라인 의무.

---

## 인쇄 / 모바일

- `@media print`: 활성 탭만 인쇄, 탭 버튼·to-top 버튼 숨김, code-block 흰 배경, `break-inside: avoid` 가드.
- `@media (max-width: 640px)`: 탭 버튼 줄바꿈, 표 `overflow-x: auto`, SVG 수평 스크롤 허용, 그리드 단일 컬럼 fallback.

---

## Claude의 작업 체크리스트

HTML을 작성하기 전에:
- [ ] `samples/`의 정본 한 파일을 골라 `<style>` / `<script>` / 6탭 셸을 동일하게 가져온다
- [ ] `rules/component_rules.md` §1~11을 한 번 통독
- [ ] 모든 입력 JSON의 sentence_id / paragraph_id / asset_id 일관성 확인
- [ ] 자산 layout이 `[[id, kind]]` 2중 배열로 통일됐는지 확인 (아니면 변환)

작성 후 자체 검증:
- [ ] 6 탭 버튼 + 패널 전환 동작 (HTML 구조만이라도 확인)
- [ ] ① `data-pair` 짝이 좌·우 동일 개수
- [ ] 번역 누락 0건
- [ ] ② ~ ⑥ 모든 탭 콘텐츠가 비어 있지 않음 (`section-empty-note` 미발견 — ⑤⑥ 셸만 빌드는 예외)
- [ ] MathJax 설정 + 탭 전환 시 재렌더 코드 포함
- [ ] 시뮬레이터 슬라이더가 canvas/SVG 갱신
- [ ] `@media print` + `@media (max-width: 640px)` 두 미디어쿼리 포함
- [ ] `<header class="hero">`, `.tab-intro` 6개 (`rules/component_rules.md` §1, §2)
- [ ] **모든 `<img>` 태그가 `data:image/png;base64,...` 인라인** — `src="assets/..."` / `src="./..."` / `src="http..."` 잔존 0건 (원본 figure/table + 학습 보조 이미지 모두)

---

## 금지 사항

- 6탭 외 임의 탭 추가 / 제거 금지
- 디자인 토큰 임의 변경 금지
- 최종 산출물에 외부 자산 참조 잔존 금지 (반드시 base64 인라인)
- `samples/`의 정본 파일 (SAFE/FrameFusion/SGL) 수정 금지
- 외부 JS 라이브러리 추가 금지 (MathJax CDN 외)
