# Component Rules — 탭 횡단 공용 컴포넌트

## 목적

모든 탭에 걸쳐 등장하는 공용 컴포넌트의 정식 규약을 정한다 (세대별 마이크로 차이를 봉합한 결과 — 현재 정본은 `samples/cares/`의 v4 8탭).

이 문서는 Stage 10에서 Claude가 단일 HTML을 작성할 때 따라야 할 마크업·CSS 규약이다.

> **🔴 v4 디자인 우선 (2026-07-02)** — 셸(헤더·탭·토큰·라운드·그림자·폰트)은
> **`rules/design_v4_dashboard.md`**가 이 문서보다 우선한다: hero 카드 → topbar, 숫자 pill 6탭 →
> 숫자 없는 8탭(Paper Study·Background/Mathematics 분리) + 해시 라우팅, v3 팔레트 → v4 저채도
> grey-lavender, serif 제목 → sans. 이 문서의 학습 인터랙션 규약(§11 concept-figure, §12 study-drawer,
> §13 lightbox, §14 diss-summary, §15~16 diss 레이아웃, §17 Paper Study)은 v4에서도 그대로 유효하다
> (색·라운드만 v4 토큰). 빌드 경로 = `_build.py`(v3 조립) → `tools/restyle_dash_v4.py`(v4 변환) 2단.

---

## SAFE ↔ FrameFusion 차이의 정식 결정

자동 비교에서 드러난 두 정본의 어긋남을 다음과 같이 통일한다.

| 컴포넌트 | SAFE | FrameFusion | **정식 결정** |
|---|---|---|---|
| `<header class="hero">` | ✓ | ✗ | **모든 논문 필수** |
| `.brand-tag` | ✓ | ✗ | **모든 논문 필수 (hero 내부)** |
| `.tab-intro` | △ | ✓ (6탭) | **모든 탭 필수** |
| `.ref-link` | ✓ 16회 | ✓ 1회 | **자동 anchor — 인라인 JS의 `autoLink()`가 패턴 스캔으로 처리** |
| `.to-top` 버튼 | ✗ | ✗ (DOM 없음) | **인라인 JS가 동적 생성 — 모든 논문** |
| `@media print` | ✗ | ✓ | **모든 논문 필수** |
| `@media (max-width: 640px)` | △ | △ | **모든 논문 필수 — 단일 HTML의 `<style>`에 포함** |
| Simulator 클래스 prefix | `csim-*` (구버전) | `sim-*` (신버전) | **`sim-*` 정식, `csim-*` deprecate** |
| QA callout block 변종 | `qa-callout-block` 8회 | `qa-callout-{key|warn|safe}` 변종 | **`qa-callout-block` + `variant` 속성으로 통일** |
| Hotspot 클래스 | `.sent.hotspot` (119회) | `.sent.hotspot` (66회) | **`.sent.hotspot` 정식 (paragraph_id → sentence_id 배열로 매핑)** |

---

## 1. Hero Header (`<header class="hero">`)

문서 최상단에 노출되는 논문 메타데이터 박스.

### 마크업

```html
<header class="hero">
  <span class="brand-tag">Paper Review · v2</span>
  <h1>{metadata.title}</h1>
  <p class="subtitle">{metadata.short_name} — {metadata.conference}</p>
  <div class="meta">
    <span class="meta-item"><strong>Authors</strong>{metadata.authors}</span>
    <span class="meta-item"><strong>Affiliation</strong>{metadata.affiliation}</span>
    <span class="meta-item"><strong>Source</strong>{metadata.source_pdf}</span>
  </div>
</header>
```

### 데이터 소스
- `papers/[name]/config.json#metadata` 모든 필드

### 위치
- `<main class="app">` 직후, `<nav class="tabs">` 직전

### 스타일 (정본 토큰)
- 배경: `var(--paper)`
- 보더: `1px solid var(--line)`
- 라운드: `22px`
- 그림자: `0 12px 32px rgba(60, 40, 22, 0.07)`

---

## 2. Tab Intro (`.tab-intro`)

각 탭의 첫 자식. 학습자에게 이 탭에서 무엇을 보게 될지 한 줄로 안내.

### 마크업

```html
<section id="tab-XXX" class="tab-pane">
  <div class="tab-intro">
    <h2>탭 제목 (예: 원문 ↔ 번역 정렬 뷰)</h2>
    <p>한 줄 안내 (1~2문장).</p>
  </div>
  <!-- 이후 실제 탭 콘텐츠 -->
</section>
```

### 의무
- 8탭 모두 `.tab-intro` 1개씩 (예외 없음 — Paper Study·Mathematics 포함)
- `<h2>`와 `<p>` 모두 채울 것
- `<p>`는 100자 이내, 학습 목표를 동사로 시작 (예: "문장 단위 hover 로 ...", "저자의 사고 흐름을 ...")

---

## 3. Ref-Link 자동 Anchor

본문/번역의 `Eq. N`, `Fig. N`, `Table N` 패턴을 자동으로 다른 탭으로 점프하는 링크로 감싼다.

### 동작
- `<body>` 끝 인라인 JS의 `autoLink()` 함수가 텍스트 노드 스캔
- 매칭된 패턴을 `<a class="ref-link" data-target-tab="...">`로 wrap
- 클릭 시 → 대상 탭 활성화 → `scrollIntoView` → `flash-target` 클래스 펄스

### 패턴 → 점프 대상

| 패턴 | data-target-tab | 추가 anchor |
|---|---|---|
| `Eq. N` / `Equation N` | `tab-knowledge` | `#eq{N}_*` (eq_id 첫 매치) |
| `Fig. N` / `Figure N` | `tab-reading` | `#fig_{N}` (asset_layout) |
| `Table N` | `tab-reading` | `#table_{N}` |
| (확장) | (필요 시 추가) | — |

### 스타일
- 기본: `color: var(--accent)`, 점선 underline
- 호버: 배경 `var(--accent-soft)` + cursor pointer
- `flash-target` 펄스: 0.6s 동안 `box-shadow: 0 0 0 4px var(--accent-soft)` 페이드

---

## 4. Hotspot — 문장 단위 강조

논문 본문에서 특히 주의 깊게 읽어야 할 문장을 시각적으로 표시.

### 데이터 소스 — `analysis.json#hotspots`

```json
{
  "hotspots": {
    "p2": ["p2_s5", "p2_s8"],
    "p29": ["p29_s1"]
  }
}
```

키는 `paragraph_id`, 값은 강조할 `sentence_id` 배열.

### 마크업

```html
<span class="sent hotspot" data-pair="p2_s5">...</span>
```

### 스타일 (정본)
- 배경: 미세한 노란빛 (`#fff6d6` 또는 `var(--gold-soft)`)
- 좌측 색상 바는 두지 않는다 (2026-09-10 정책: 카드/콜아웃/패널의 `border-left` 색 띠 전면 폐지 - `tools/strip_left_bars.py`. 바 제거 후 남는 "왼쪽만 0 인 border-radius" 잔재는 `tools/normalize_left_radius.py` 로 네 모서리 동일 값으로 정규화한다 - 둘 다 빌더와 산출물을 함께 고치는 저장소 전체 패스)
- 호버 시 다른 `data-pair` 짝과 함께 더 진한 강조

### 양 가이드
- 한 논문당 5~15 문장 (너무 많으면 강조 의미 상실)
- 보통 `Stage 4 Research Analysis`에서 도출

---

## 5. To-Top 버튼

화면 우하단 부동 버튼. 인라인 JS가 동적으로 생성.

### 동작
- DOM에 버튼 없으면 JS가 `<body>`에 추가
- `window.scrollY > 360` 일 때 visible
- 클릭 시 smooth scroll to top + 현재 탭의 scroll memory 0으로 리셋

### 마크업 (JS가 주입)
```html
<button class="to-top" aria-label="맨 위로">↑</button>
```

### 스타일
- `position: fixed; right: 24px; bottom: 24px;`
- 원형 (50% radius), `var(--paper)` 배경, `var(--line)` 보더
- z-index 50

---

## 6. `@media print`

활성 탭만 인쇄. 다른 탭, 탭 버튼, to-top 버튼, 시뮬레이터 컨트롤은 숨김.

### 정본 CSS
```css
@media print {
  .tabs, .to-top, .sim-controls { display: none !important; }
  .tab-pane { display: none !important; }
  .tab-pane.active { display: block !important; }
  .code-block { background: white !important; color: black !important; }
  canvas, svg { break-inside: avoid; }
  .paragraph-block, .diss-card, .knw-card, .qa-card { break-inside: avoid; }
}
```

이 블록은 단일 HTML의 `<style>` 안에 항상 포함.

---

## 7. `@media (max-width: 640px)` — 모바일

좁은 화면 대응. 단일 HTML의 `<style>` 안에 항상 포함.

### 정본 규약 (단일 HTML의 `<style>` 안에 항상 포함)
```css
@media (max-width: 640px) {
  .app { padding: 16px 12px 60px; }
  .tabs { flex-wrap: wrap; }
  .tab-btn { flex: 1 1 45%; font-size: 13px; padding: 8px 6px; }

  .bilingual { grid-template-columns: 1fr; }   /* 좌우 → 위아래 */
  .meta { grid-template-columns: 1fr; }
  .knw-grid, .coach-grid, .sim-controls { grid-template-columns: 1fr; }

  table { font-size: 12px; }
  .tab-pane table, .qa-block-table { overflow-x: auto; display: block; }

  svg { max-width: 100%; height: auto; overflow-x: auto; }
}
```

### 검증
- 빌드 후 Chrome DevTools 모바일 뷰(375px / 414px)에서 직접 확인
- 탭 버튼 줄바꿈 / 표 가로 스크롤 / SVG 수평 스크롤 정상

---

## 8. 시뮬레이터 클래스 prefix 통일

| 구버전 (SAFE) | **신버전 (정본)** |
|---|---|
| `csim-controls` | `sim-controls` |
| `csim-canvas-wrap` | `sim-canvas-wrap` |
| `csim-bar` / `csim-bar-fill` | `sim-bar` / `sim-bar-fill` |
| `csim-stat` | `sim-stat` |
| `csim-code-col` | `cmp-card` (좌우 비교는 `cmp-grid > .cmp-card`) |
| `csim-layout` | (제거 — 그리드 직접 사용) |

신규 논문은 `sim-*` 사용. SAFE를 v2로 재빌드할 때 `csim-*`도 마이그레이션. (⑤는 기본 빌드에서 셸만 생성되므로 이 선택자들은 ⑤를 명시 요청한 논문에만 나타난다.)

---

## 9. QA Callout — `variant` 속성으로 통일

기존: `qa-callout-key`, `qa-callout-warn`, `qa-callout-safe` 3가지 클래스 변종.
**정본**: `qa-callout-block` 하나 + `data-variant` 속성.

### 마크업
```html
<div class="qa-callout-block" data-variant="key">
  <p>핵심 인사이트 ...</p>
</div>
```

`data-variant`: `key` / `warn` / `safe` 3종 고정 (`prompts/10_qa.md`와 일치).

### 스타일 매핑
- `[data-variant="key"]`: 좌측 4px stripe `var(--sage)`, 배경 `var(--sage-soft)`
- `[data-variant="warn"]`: stripe `var(--accent)`, 배경 `var(--accent-soft)`
- `[data-variant="safe"]`: stripe `var(--muted)`, 배경 미세 베이지 (`#faf6ec`)

---

## 10. 커스텀 위젯 네이밍

논문별 시뮬레이터/QA에 들어가는 일회성 위젯은 **논문 prefix**로 격리한다.

### 명명 규약
- FrameFusion의 Q1 애니메이션: `q1-patch`, `q1-token`, `q1-stepper`
- SAFE의 GPU 메모리 시각화: `qa-gpu-sm-row`, `qa-arch-layer` (레거시 — 신규 논문은 paper prefix 사용)
- 신규 논문 X의 Q1 위젯: `x-q1-*` 또는 논문 약자 prefix

### 의무
- 위젯 클래스는 절대 디자인 토큰 클래스(`sim-*`, `qa-*`, `diss-*` 등)와 충돌 금지
- 위젯 스타일은 단일 HTML의 `<style>` 안 별도 섹션에서 정의 (정본 토큰 오염 금지)

---

## 정리 — 단일 HTML의 `<style>` 정본 책임

Stage 10에서 작성하는 단일 HTML의 `<style>` 블록에 **반드시** 포함되어야 하는 영역:

1. `:root` 디자인 토큰 (CLAUDE.md 정본 토큰과 동일)
2. 탭 셸 — `.tabs`, `.tab-btn`, `.tab-pane`, `.tab-intro`
3. 탭 ① 본문 — `.section`, `.paragraph-block`, `.bilingual`, `.sent`, `.callout`, `.asset-stack`, `.interpretation`, `.beginner-note`, `.recall-card`, `.sent.hotspot`
4. 탭 ② Dissection — `.diss-card`, `.diss-step`, `.diss-head`, `.diss-rows`, `.diss-tag`, `.diss-body`, `.diss-{motivation|observe|compare|logic|verify|risk|extend}`
5. 탭 ③ Knowledge — `.fund-card`, `.knw-card`, `.knw-grid`, `.knw-row`, `.knw-label`, `.eq-card`, `.eq-section`
6. 탭 ④ Questions — `.coach-card`, `.coach-grid`, `.coach-tag`, `.diagram-card`, `.q-{hidden|myth|critic|extend}`
7. 탭 ⑤ Simulator — `.sim-controls`, `.sim-canvas-wrap`, `.sim-stat`, `.sim-bar`, `.cmp-grid`, `.cmp-card`
8. 탭 ⑥ QA — `.qa-category`, `.qa-card`, `.qa-block`, `.qa-callout-block`, `.qa-block-{html|table|math|callout}`
9. 헤더 — `.hero`, `.brand-tag`, `.meta`, `.meta-item`
10. Cross-cutting — `.ref-link`, `.flash-target`, `.to-top`
11. 미디어 쿼리 — `@media print`, `@media (max-width: 640px)`

이 11개 영역을 모두 갖추지 못하면 정본 일치라 부르지 않는다.

> 단서: ⑤⑥ 탭은 기본 빌드에서 셸만 생성되므로(CLAUDE.md "기본 빌드 범위") 7·8 영역의 선택자(`.sim-*`·`.cmp-*`·`.qa-category`·`.qa-card`·`.qa-block*`, §6~§8 의 `.code-block` 포함)는 사용자가 ⑤⑥을 명시 요청한 논문에만 나타난다. v4 정본 CARES 에 이들이 없는 것은 누락이 아니다.

---

## 11. 생성된 이미지 (`assets/generated/`) — codex ImageGen 정본

ImageGen으로 만든 학습 보조 이미지의 정식 위치·명명·**호출 형식**·임베드 마크업. 이 절이 정본 — 다른 문서는 모두 이쪽을 가리킨다.

### 11.1 적용 단계 (① 번역 탭 제외)

- ② Stage 4 — Research Analysis : `dissection_<purpose>.png`
- ④ Stage 5 — Coaching : `questions_<purpose>.png`
- ③ Stage 7 — Background Knowledge : `knowledge_<purpose>.png`
- ⑤ Stage 8 — Simulator : `simulator_<purpose>.png`
- ⑥ Stage 9 — QA : `qa_<qid>_<purpose>.png`

① `tab-reading`은 원문/번역 정렬과 paper 원본 figure/table만 다룬다. 학습 보조용 생성 이미지는 ② ~ ⑥에만 사용.

### 11.2 codex 호출 6계명 — 한 번에 통과시키는 정식 형식

Windows에서 codex exec로 ImageGen을 부를 때 **다음 6가지를 모두 명시**해야 한 번에 통과한다. 하나라도 빠지면 인코딩(CP949)·hang(stdin 대기)·컷아웃 디폴트·이미지 내 논문 제목 잔존으로 막힌다.

| # | 항목 | 명시 안 하면 막히는 이유 |
|---|---|---|
| 1 | **Bash 툴 사용** (PowerShell 금지) | PS 5.1이 native exe로 한글을 CP949로 깨뜨림 |
| 2 | **prompt.txt를 UTF-8로 만들고, codex 인자는 ASCII 한 줄로 그 파일을 읽으라는 지시만** | 셸 인코딩 무관하게 한글 프롬프트 그대로 전달 |
| 3 | **stdin은 `< /dev/null`** | codex가 stdin 입력을 기다리며 hang 차단 |
| 4 | **스타일 명시** ("풀 블리드 일러스트 / 사진, 배경 가득, NOT a transparent cutout") | imagegen 기본값이 투명 배경 컷아웃 |
| 5 | **출력 경로 + 해상도 절대 명시** (절대 경로 + WxH) | codex가 임의 위치·임의 크기로 저장 방지 |
| **6** | **이미지 안에 논문 제목·헤더·저자명 금지 명시** ("NO paper title at top, NO standalone header, NO author names") | imagegen이 기본으로 그림 상단에 \"LVPruning\" 같은 타이틀을 박아 학습 카드의 시각 통일성을 해침 |

**6번째 계명 — 정본 prompt 마지막 한 줄**:

```
NO paper title at top, NO standalone header, NO author names. Only the <설명: 다이어그램/도식/플롯> content with English section labels.
```

이 한 줄을 prompt.txt 끝에 항상 추가한다. 이미지가 \"콘텐츠\"만 담고 \"메타데이터\"는 안 박는 게 학습 자료 일관성의 핵심.

### 11.3 검증된 호출 템플릿

**Step A — UTF-8 prompt 파일 작성** (Claude는 Write 툴로 직접 생성):

`papers/[name]/assets/generated/prompt_<purpose>.txt`

> ⚠️ **본문을 어떻게 채우는지가 이 절의 범위를 넘어선다 — 반드시 §11.8을 먼저 읽는다.**
> 아래는 최소 골격일 뿐이고, `<...>` 자리를 §11.8.3의 패널 명세 규칙대로 채우지 않으면
> 여백 크고 정보량 적은 그림이 나온다 (반복 실패의 단일 원인).

```
교육용 학술 일러스트레이션. 정사각형 1024x1024.

주제: "<한 줄 핵심 메시지 — 이 그림이 증명하려는 명제>"

전체 레이아웃: <몇 개의 블록을 어떤 방향으로 배치하는지> 정보 밀도를 높게, 빈 공간을 남기지 말 것.

[블록 1 — <영문 헤더>]
 1) <시각 형태> + <그 안의 라벨·실제 수치> — 캡션 "<영어 한 줄>"
 2) <시각 형태> + <라벨·수치> — 캡션 "<영어 한 줄>"
 3) <시각 형태> + <라벨·수치> — 캡션 "<영어 한 줄>"

[블록 2 — <영문 헤더>]
 1) ...  2) ...  3) ...

색상 팔레트: 흰색-아이보리 배경 + lavender(#8b75c0) / azure(#6b95b3) / mint(#75ad8e)
/ amber(#ad8e4e) / rose(#b87887) 강조, 텍스트는 dark ink(#1f1d24). 저채도, 쨍한 원색 금지.

스타일 지시 (중요):
- 풀 블리드 일러스트 — 배경 가득
- 절대로 투명 배경 컷아웃이 아닐 것 (NOT a transparent cutout)
- Scientific American / 학술 교과서 도해 스타일, 평면적 벡터 느낌
- 모든 라벨과 수식은 영어·ASCII로만
- 1024x1024 정사각형

NO paper title at top, NO standalone header, NO author names. Only the <다이어그램 종류> content with English section labels.
```

**Step B — codex 호출** (Bash 툴, 절대 PowerShell 금지):

```bash
codex exec \
  --skip-git-repo-check \
  --dangerously-bypass-approvals-and-sandbox \
  --cd "<absolute path to assets/generated>" \
  "Read the file prompt_<purpose>.txt in the current directory using UTF-8. It contains a Korean image generation request. Use your image generation tool to create a 1024x1024 PNG that follows the description. Save the output as <purpose>.png in the current directory. The image must have a full background (NOT a transparent cutout). Generate exactly one image. Do not modify any other files. Reply with just the saved file path." \
  < /dev/null
```

- **codex 인자 한 줄은 ASCII만** — 한글이 절대 들어가면 안 된다.
- `~/.codex/config.toml`에 `image_generation = true`가 켜져 있어야 한다 (ImageGen 활성화).
- 한 호출 평균 토큰 사용량 ~25k. timeout 300000ms 권장.
- 여러 이미지 동시 생성 시 Bash `run_in_background`로 병렬 호출.

### 11.4 저장·임베드 규약

- 저장 경로: `papers/[name]/assets/generated/` (paper별 격리, 원본 파일 보존)
- **HTML 임베드: base64 인라인 의무** — `<img src="data:image/png;base64,...">`. 원본 figure/table과 동일 정책. 단일 파일 자족·휴대성 우선.
- 외부 참조(`<img src="assets/generated/...">`)는 개발 미리보기 한정. **최종 산출물에 외부 참조 잔존 = 빌드 불합격.**
- `config.json#asset_layout`에는 등록하지 않음 (이건 paper의 원본 figure/table 전용).
- 검수는 2단 — **① Claude 자체 검수(의무): 생성 직후 PNG를 Read로 열어 §11.8.6 체크리스트 확인, 미달 시 프롬프트 수정 후 재생성.** ② 사용자 검수는 사후: 결과 HTML을 보고 수정이 필요하면 별도 재생성 요청. 생성-박기 흐름을 사용자 사전 검수로 막지는 않는다.

### 11.5 정본 임베드 컴포넌트 — `<figure class="concept-figure">`

학습 보조 이미지를 박는 표준 마크업. 4. perceptron에서 검증.

```html
<figure class="concept-figure">
  <img src="data:image/png;base64,..." alt="..." />
  <figcaption>
    <span class="cf-label">학습 보조 · <카테고리></span>
    <h4><한 줄 제목></h4>
    <p><무엇을 보면 되는지 1~2 문장 안내. 본문이 명시 안 한 시각 메타포면 그 의미를 풀어 준다.</p>
  </figcaption>
</figure>
```

CSS (정본 — `<style>` 블록에 추가):

```css
.concept-figure{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:18px 20px;margin:0 0 22px;box-shadow:0 6px 18px rgba(80,60,140,0.05)}
.concept-figure img{display:block;max-width:760px;width:100%;height:auto;margin:0 auto;border-radius:12px;border:1px solid var(--line);background:#fbfaff}
.concept-figure figcaption{margin-top:12px;text-align:center}
.concept-figure figcaption .cf-label{display:inline-block;font-size:11px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:var(--accent);background:var(--accent-soft);padding:3px 10px;border-radius:999px;margin-bottom:6px}
.concept-figure figcaption h4{margin:4px 0 6px;font-family:Georgia,serif;font-size:17px;color:var(--ink)}
.concept-figure figcaption p{margin:0;font-size:13.5px;color:var(--muted);line-height:1.65;max-width:640px;margin-left:auto;margin-right:auto}
```

배치 자리 (그리드 레이아웃을 깨지 않게):
- **탭 히어로** — `tab-intro` 직후, 메인 그리드(`diss-grid` / `coach-grid` / `kn-grid`) 직전.
- **탭 푸터** — 메인 그리드 닫힘 직후, `</section>` 직전.
- 그리드 안에 끼워 넣으려면 `style="grid-column:1/-1"` 명시.

### 11.6 base64 임베드 + 마크업 삽입 자동화 — `_inject_concept_figures.py`

빌드 후 PNG를 base64로 변환해 figure 마크업과 함께 정확한 자리에 삽입하는 정본 스크립트 패턴. 4. perceptron 폴더의 `_inject_concept_figures.py` 참조 (재실행 가능, 백업 자동 생성).

핵심 골격:

```python
import base64
from pathlib import Path

ROOT = Path(__file__).parent
HTML = ROOT / "<ShortName>_output.html"
GEN = ROOT / "assets" / "generated"

def b64(png: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode("ascii")

text = HTML.read_text(encoding="utf-8")

# 1) CSS — </style> 직전에 .concept-figure 규칙 한 번만 추가
# 2) figure 마크업 — anchor 문자열로 정확한 위치 찾아 삽입
# 3) 검증: count() 로 figure 개수·anchor 개수 확인 (중복 삽입 방지)

HTML.write_text(text, encoding="utf-8")
```

호출 전에 `Perceptron_output.html.before_concept_figures` 같은 백업을 남긴다 (Bash `cp` 한 줄).

### 11.7 파일명 규약 정리

```
papers/[name]/assets/generated/
├── prompt_<purpose>.txt              # codex 입력 (UTF-8 한글)
├── dissection_<purpose>.png          # ② 탭 보조 (히어로/푸터/카드)
├── questions_<purpose>.png           # ④ 직관 다이어그램
├── knowledge_<purpose>.png           # ③ primer / fund / concept
├── simulator_<purpose>.png           # ⑤ 도입 / 단계 시각화
└── qa_<qid>_<purpose>.png            # ⑥ 질문별 보조
```

prompt 파일은 **재생성·디버깅용으로 같이 보존**한다 (지우지 않는다).


---

### 11.8 🔴 프롬프트 본문 작성 정본 — 밀도·구조·검수 (정책, 2026-08-01)

§11.2가 **어떻게 호출하는가**(인코딩·hang·컷아웃 방지)라면, 이 절은 **prompt.txt 안에 무엇을 쓰는가**이다.
호출은 6계명으로 이미 안정화됐고, 남은 반복 실패는 전부 본문 쪽에서 났다. 이미지 생성 전 이 절을 통독한다.

#### 11.8.1 대전제 — 프롬프트의 정보량이 곧 이미지의 정보량

imagegen은 **쓰지 않은 것을 채워 넣지 않는다.** 안 적은 패널은 여백이 되고, 안 적은 숫자는 나오지 않으며,
"핵심을 잘 보여 주는 도식" 같은 위임형 문장은 장식적인 아이콘 한두 개로 돌아온다.

따라서 프롬프트는 *그려 달라는 요청*이 아니라 **이미 완성된 그림을 글로 옮겨 적는 기술(記述)** 로 쓴다.
초안을 쓴 뒤 자가 점검: **"이 글만 보고 내가 손으로 그 그림을 그릴 수 있는가?"** 없으면 아직 덜 쓴 것이다.

#### 11.8.2 필수 5블록 구조

모든 prompt.txt는 아래 5블록을 이 순서로 갖는다. 하나라도 빠지면 실패 모드가 하나씩 열린다(§11.8.7).

| # | 블록 | 내용 | 빠뜨리면 |
|---|---|---|---|
| ① | **캔버스 선언** | 한 줄. `교육용 학술 인포그래픽. 가로 직사각형 1536x864.` | 임의 비율·저해상도 |
| ② | **전체 레이아웃** | 블록/단의 개수·배치 방향·연결선·헤더 처리 + `정보 밀도를 높게, 빈 공간을 남기지 말 것` | 요소가 흩어지고 여백 과다 |
| ③ | **패널 명세 (본체)** | §11.8.3. 분량의 80~90%를 여기에 쓴다 | 헐거운 그림 — 최다 실패 원인 |
| ④ | **색상 팔레트** | v4 저채도 hex 나열 + `쨍한 원색 금지` | 형광색·톤 불일치 |
| ⑤ | **스타일 지시 + 6번째 계명** | 풀 블리드 / NOT a transparent cutout / 학술 도해 스타일 / 영어·ASCII 라벨 / 해상도 재확인 + 마지막 줄 `NO paper title at top, NO standalone header, NO author names.` | 컷아웃·논문 제목 박힘 |

#### 11.8.3 패널 명세 작성 규칙 (본체 — 여기가 전부)

**패널마다 번호를 붙이고, 각 패널에 아래 3요소를 빠짐없이 적는다.**

1. **(a) 시각 형태** — 무엇으로 그릴지. 아래 어휘집에서 고른다.
2. **(b) 그 안의 라벨과 실제 수치** — 축 이름, 계열 이름, 값, 모델명, 데이터셋 크기.
3. **(c) 한 줄 캡션** — 이 패널이 말하는 명제. 영어.

**시각 형태 어휘집** (imagegen이 안정적으로 그려내는 것들):
좌표축 곡선 · 그룹 막대그래프 · 가로 막대 비교 · 파이/도넛 · 저울(balance) · 정사각 히트맵 행렬 ·
산점도+회귀선 · 등고선 타일 · 토큰/패치 그리드 · 파이프라인 박스열(→ 화살표) · 말풍선 ·
큰 숫자 통계 타일 · 체크(✓)·엑스(✗) 비교 박스 · 수식 박스 · 단면도(방·문) · 아이콘+라벨 카드

**숫자 의무** — 논문의 표·그림에서 **직접 읽은 값**을 그대로 박는다.
`성능이 향상된다` ✗ → `12.5% -> 5.1% at L = 192` ✓ / `토큰이 줄어든다` ✗ → `33,000 -> 14,000 -> 3,600` ✓
(원본 figure의 막대값을 쓰려면 그 PNG를 Read로 열어 눈으로 읽고 적는다.)

**텍스트 규칙**
- 이미지에 들어갈 **라벨·수식은 영어 ASCII로만** 적는다. 한글 라벨은 이미지에서 깨지고, 프롬프트 본문에 섞인
  비ASCII 이물(중국어·이모지 등)도 그대로 그려지는 사고가 있다 — 작성 후 라벨 부분을 한 번 훑는다.
- LaTeX 대신 ASCII 근사: `sum` `sqrt` `<=` `>=` `->` `alpha` `Delta` `x*` `phi_k` `O*(1/L)`.
- **패널당 라벨 1~6개**. 그 이상 넣으면 글자가 뭉개지고 철자가 깨진다.

#### 11.8.4 이미지 종류별 밀도 등급 — 조밀함이 항상 정답은 아니다

| 파일 | 캔버스 | 블록/단 | 패널 총수 | prompt 분량 | 성격 |
|---|---|---|---|---|---|
| `dissection_overview.png` | 1536×864 | 5단 고정 | **15~20** | 3.5~4.5 KB | 논문 전체를 한 장에 — **최대 밀도** |
| `questions_*.png` / `knowledge_*.png` | 1024×1024 | 2~3 블록 | 5~9 | 1.5~2.5 KB | 개념도 — **한 가지 논점만** |
| `simulator_*.png` | 1024×1024 | 단계 수만큼 | 4~8 | 1.5~2.5 KB | 알고리즘 단계 시각화 |
| `qa_<qid>_*.png` | 1024×1024 | 1~2 블록 | 3~5 | 1~1.5 KB | 질문 하나의 보조 — **최소 밀도** |

- overview는 **조밀할수록 좋다**. 정본 3편(§11.8.9)이 기준선이고, 그보다 성기면 미달이다.
- 반대로 **개념도에 overview 밀도를 넣으면 실패한다** — 1024×1024에 15개 패널을 넣으면 글자가 읽히지 않는다.
  개념도는 "한 문장으로 말할 수 있는 논점 하나"를 2~3블록으로 나눠 크게 그린다.

#### 11.8.5 병렬 생성 시 작업 디렉토리 격리 (필수)

여러 이미지를 `run_in_background`로 동시에 만들 때 **모든 호출이 같은 `--cd`를 공유하면 안 된다.**
codex는 작업 디렉토리 전체를 읽을 수 있어, 동시 실행 중인 형제 프로세스가 방금 만든 PNG를
"이미 있는 결과"로 오인·복제하는 사고가 실제로 발생했다.

- 호출마다 `scratchpad/img_<purpose>/` 같은 **격리 디렉토리**를 만들고 해당 prompt 파일 **하나만** 복사해 넣는다.
- 경로에 한글이 있어도 codex는 동작하지만, ASCII scratchpad에서 생성한 뒤
  `papers/N. name/assets/generated/`로 복사하는 편이 인코딩 사고를 원천 차단한다.
- **파일 해시 비교로는 이 사고가 안 잡힌다** (재인코딩되어 md5가 달라짐). 반드시 눈으로 확인(§11.8.6).

#### 11.8.6 검수 체크리스트 — 기계 검사 → PNG 육안 확인

**0단계 (codex 호출 전, 자동)** — 이 저장소에는 **PreToolUse(Bash) 훅**이 걸려 있어
`codex` 가 포함된 Bash 호출을 가로채 `--cd` 로 지정된 prompt.txt를 자동 검사하고,
FAIL이 있으면 **호출 자체를 차단**한다 (`.claude/settings.json` → `tools/hook_precheck_codex.py`).
훅이 없는 환경(다른 PC·CI)에서는 아래를 손으로 돌린다.

```bash
python tools/check_image_prompts.py "papers/N. shortname"      # 논문 전체
python tools/check_image_prompts.py <prompt 파일 경로>          # 파일 하나
```

이 스크립트가 검사하는 것: 캔버스 선언 · 5단 헤더(overview) · 패널 수 · **본문 수치 개수** ·
팔레트 hex · `NOT a transparent cutout` · 6번째 계명 · 한자 이물 · **분량 하한** · 짝 PNG 존재.
하드 실패는 서식에 강건한 항목만(수치·분량·헤더·금칙어), 패널 수 등은 참고용 warn이다.

> 훅의 안전 설계 — 게이트가 작업을 잘못 막는 쪽이 더 나쁘므로, stdin 파싱 실패·프롬프트 파일 미발견·
> 검사기 예외는 **전부 통과**시킨다. 같은 파일명이 여러 논문에 있으므로 `--cd` 로 실제 파일을 특정하고,
> 특정에 실패하면 후보가 정확히 1개일 때만 검사한다.

**1단계 (생성 후, 의무)** — PNG를 Read로 연다. "검수는 사후"란 **사용자에게 넘기기 전에 Claude가 확인한다**는 뜻이지, 확인을 생략한다는 뜻이 아니다.

- [ ] 프롬프트에 적은 **패널이 전부 있는가** (누락·병합 없음)
- [ ] **여백이 과도하지 않은가** (§11.8.4 밀도 등급 대비)
- [ ] **수치가 논문 값과 일치하는가** (막대 높이·라벨 오기)
- [ ] 라벨이 **영어이고 철자가 깨지지 않았는가**
- [ ] 상단에 **논문 제목·저자명이 박히지 않았는가** (6번째 계명)
- [ ] 배경이 **불투명한 풀 블리드**인가 (컷아웃 아님)
- [ ] **요청한 프롬프트의 내용이 맞는가** (§11.8.5 혼선 여부)

#### 11.8.7 실패 모드 → 처방

| 증상 | 원인 | 처방 |
|---|---|---|
| 여백 크고 요소가 적음 | ③ 패널 명세가 성김 | 단마다 패널 3~4개로 늘리고 각 패널에 (a)(b)(c) 3요소 명시 |
| 다른 프롬프트의 그림이 저장됨 | 병렬 호출이 `--cd` 공유 | §11.8.5 격리 디렉토리로 재생성 |
| 글자 뭉개짐·철자 깨짐 | 패널당 라벨 과다 / 캔버스 대비 밀도 초과 | 라벨을 패널당 6개 이하로, 또는 밀도 등급을 한 단계 낮춤 |
| 상단에 논문 제목·저자명 | ⑤ 6번째 계명 누락 | 마지막 줄 `NO paper title at top…` 추가 |
| 투명 배경 컷아웃 | ⑤ 스타일 지시 누락 | `풀 블리드` + `NOT a transparent cutout` 명시 |
| 수치가 논문과 다름 | 프롬프트에 값을 안 적음 | 표·그림에서 읽은 실제 값을 (b)에 박아 재생성 |
| 이미지에 한글/이물 문자 | 프롬프트 라벨이 비ASCII | 라벨을 영어 ASCII로 고쳐 재생성 |
| CP949 깨짐·hang | PowerShell 사용 / stdin 미차단 | §11.2 — Bash + `< /dev/null` |

위 증상 중 ①③④⑥⑦⑧은 `tools/check_image_prompts.py`가 **생성 전에** 잡아낸다 — 먼저 돌린다.

#### 11.8.8 재생성 루프

1차 결과가 기준 미달이면 **프롬프트를 고쳐서** 재생성한다.
**같은 프롬프트로 재시도하지 않는다** — 밀도가 같으면 결과 밀도도 같다.
무엇을 더 써야 할지 모르겠으면 밀도 정본을 열어 자기 프롬프트와 나란히 비교한다.

#### 11.8.9 밀도 정본 (열어서 보고 따라 쓸 것)

- `papers/20. sparse_vlm/assets/generated/prompt_dissection_overview.txt` (+ 결과 PNG)
- `papers/24. geollava8k/assets/generated/prompt_dissection_overview.txt` (+ 결과 PNG)
- `papers/25. visiondrop/assets/generated/prompt_dissection_overview.txt` (+ 결과 PNG)
- `papers/27. lupi/assets/generated/prompt_dissection_overview.txt` — 이론 논문(자산 figure 1장) 적용례

> 정본 학습 사례 (실패→복구): `papers/27. lupi` 1차 생성 시 §11.3의 얇은 스켈레톤(`[좌/상 패널] <설명>`)을
> 그대로 따라 단마다 요소를 1~2개만 적었고, 여백이 크고 정보량이 적은 그림이 나왔다.
> 사용자가 20·24번과 비교 지적 → 프롬프트를 2.9 KB → 4.4 KB로 재작성해 재생성.
> 같은 세션에서 병렬 호출 `--cd` 공유로 `knowledge_convergence.png`가 다른 그림으로 저장되는 사고도 발생.
> 이 절(11.8)과 §14.5, `prompts/04_research_analysis.md`의 템플릿 교체가 그 직접 결과물이다.

---

### 11.9 🔴 이미지 생성 모드 선택 — codex PNG vs Claude SVG (정본, 2026-06-29)

학습 보조 이미지(② ~ ⑥ 탭)는 **두 가지 모드 중 하나**로 만든다. 이 선택은 CLI(터미널에서 Claude Code 직접 호출)와 웹 대시보드(`webapp/`)에서 **동일하게 작동**해야 한다 — 같은 산출물·같은 임베드 마크업·같은 품질 기준.

| 모드 | 키 | 생성 주체 | 산출 | 전제조건 | 임베드 |
|---|---|---|---|---|---|
| **A. codex PNG** (기본·정본) | `codex` | codex CLI ImageGen (외부 터미널 호출) | 래스터 `.png` (full-bleed 일러스트/인포그래픽) | `codex` CLI 설치·로그인 + `image_generation = true` | base64 `<img>` 인라인 |
| **B. Claude SVG** (codex 미설치/대체) | `claude_svg` | **Claude가 직접 `<svg>` 마크업 작성** (외부 도구 없음) | 인라인 벡터 `<svg>` 도식 | 없음 (Claude 자체 능력) | `<svg>` 인라인 직접 |

**모드 선택 방법 (CLI·웹 공통):**
- **CLI**: 사용자가 자연어로 지시 — "이미지는 codex로" / "이미지는 SVG로 그려줘(자체 생성)". 지시가 없으면 `codex` 가용 시 codex, 미설치면 자동으로 `claude_svg`로 폴백.
- **웹**: 상단 토글(`codex 터미널` ↔ `Claude 자체`)에서 선택. 프론트가 매 메시지에 `[이미지 생성 모드: codex|claude_svg]` 태그를 붙여 전달한다. codex 미설치 시 토글은 `claude_svg` 로 잠긴다(`/api/auth#codex_available`).
- **공통 폴백**: `codex` 모드인데 호출이 실패하거나 CLI가 없으면 그 자산만 `claude_svg`로 graceful degrade. 전체 빌드를 멈추지 않는다(§11.4 사후 검수 원칙과 동일).

#### 모드 B — Claude SVG 작성 규약 (정본)

Claude는 래스터 이미지를 직접 렌더할 수 없으므로, "자체 생성"은 **손으로 작성하는 인라인 SVG 도식**을 뜻한다. 학습 보조 이미지의 본질이 *개념 도식·아키텍처 다이어그램·단계 일러스트*이므로 벡터 SVG가 오히려 더 또렷하고 휴대성이 좋다.

- **6계명 대응** — codex 6계명 중 모드 B에 살아있는 원칙: ④ 풀 블리드(배경 `<rect>`로 캔버스 가득, 투명 컷아웃 금지) / ⑥ 이미지 안에 논문 제목·저자명 금지(콘텐츠 라벨만). 인코딩·stdin·해상도 계명은 외부 호출이 없으므로 불필요.
- **v3 토큰 사용** — `<svg>` 안의 색은 CSS 변수 직접 참조 가능: `fill="var(--accent-soft)"`, `stroke="var(--accent)"`, 텍스트 `fill="var(--ink)"`. 다크/라이트 무관하게 테마와 일관.
- **viewBox 고정** — `viewBox="0 0 1024 576"` 같은 고정 비율. `width:100%; height:auto`로 반응형.
- **라벨은 영문 1~4개** — codex 모드와 동일하게 한글 신조어 금지(§ CLAUDE.md 무리한 한국어 변환 금지). 본문 라벨은 영문 용어 그대로.
- **저장** — SVG는 외부 파일로 빼지 않고 **HTML에 바로 인라인**한다. 단, 재생성·디버깅용으로 소스를 `assets/generated/<purpose>.svg`에 같이 저장해 두는 것을 권장(codex의 prompt.txt 보존과 대칭).

#### 공통 임베드 — `<figure class="concept-figure">`

두 모드 모두 §11.5의 `<figure class="concept-figure">`로 감싼다. 모드 A는 `<img src="data:image/png;base64,…">`, 모드 B는 `<svg>…</svg>`를 `<img>` 자리에 그대로 넣는다. figcaption(`.cf-label` / `h4` / `p`)은 동일.

```html
<!-- 모드 B (Claude SVG) 예시 -->
<figure class="concept-figure">
  <svg viewBox="0 0 1024 576" role="img" aria-label="...">
    <rect width="1024" height="576" fill="var(--paper)"/>
    <!-- … 도식 콘텐츠: rect / path / text 영문 라벨 … -->
  </svg>
  <figcaption>
    <span class="cf-label">학습 보조 · <카테고리></span>
    <h4><한 줄 제목></h4>
    <p><무엇을 보면 되는지 1~2 문장 안내.></p>
  </figcaption>
</figure>
```

> SVG도 `.concept-figure img` CSS의 영향을 받도록, SVG 루트에 `class="cf-svg"`를 주고 `.concept-figure .cf-svg{display:block;max-width:760px;width:100%;height:auto;margin:0 auto;border-radius:12px;border:1px solid var(--line);background:#fbfaff}`를 §11.5 CSS 옆에 추가한다 (img 규칙과 동일 시각).

---

### 11.8 🔴 프롬프트 본문 작성 정본 — 밀도·구조·검수 (정책, 2026-08-01)

§11.2가 **어떻게 호출하는가**(인코딩·hang·컷아웃 방지)라면, 이 절은 **prompt.txt 안에 무엇을 쓰는가**이다.
호출은 6계명으로 이미 안정화됐고, 남은 반복 실패는 전부 본문 쪽에서 났다. 이미지 생성 전 이 절을 통독한다.

#### 11.8.1 대전제 — 프롬프트의 정보량이 곧 이미지의 정보량

imagegen은 **쓰지 않은 것을 채워 넣지 않는다.** 안 적은 패널은 여백이 되고, 안 적은 숫자는 나오지 않으며,
"핵심을 잘 보여 주는 도식" 같은 위임형 문장은 장식적인 아이콘 한두 개로 돌아온다.

따라서 프롬프트는 *그려 달라는 요청*이 아니라 **이미 완성된 그림을 글로 옮겨 적는 기술(記述)** 로 쓴다.
초안을 쓴 뒤 자가 점검: **"이 글만 보고 내가 손으로 그 그림을 그릴 수 있는가?"** 없으면 아직 덜 쓴 것이다.

#### 11.8.2 필수 5블록 구조

모든 prompt.txt는 아래 5블록을 이 순서로 갖는다. 하나라도 빠지면 실패 모드가 하나씩 열린다(§11.8.7).

| # | 블록 | 내용 | 빠뜨리면 |
|---|---|---|---|
| ① | **캔버스 선언** | 한 줄. `교육용 학술 인포그래픽. 가로 직사각형 1536x864.` | 임의 비율·저해상도 |
| ② | **전체 레이아웃** | 블록/단의 개수·배치 방향·연결선·헤더 처리 + `정보 밀도를 높게, 빈 공간을 남기지 말 것` | 요소가 흩어지고 여백 과다 |
| ③ | **패널 명세 (본체)** | §11.8.3. 분량의 80~90%를 여기에 쓴다 | 헐거운 그림 — 최다 실패 원인 |
| ④ | **색상 팔레트** | v4 저채도 hex 나열 + `쨍한 원색 금지` | 형광색·톤 불일치 |
| ⑤ | **스타일 지시 + 6번째 계명** | 풀 블리드 / NOT a transparent cutout / 학술 도해 스타일 / 영어·ASCII 라벨 / 해상도 재확인 + 마지막 줄 `NO paper title at top, NO standalone header, NO author names.` | 컷아웃·논문 제목 박힘 |

#### 11.8.3 패널 명세 작성 규칙 (본체 — 여기가 전부)

**패널마다 번호를 붙이고, 각 패널에 아래 3요소를 빠짐없이 적는다.**

1. **(a) 시각 형태** — 무엇으로 그릴지. 아래 어휘집에서 고른다.
2. **(b) 그 안의 라벨과 실제 수치** — 축 이름, 계열 이름, 값, 모델명, 데이터셋 크기.
3. **(c) 한 줄 캡션** — 이 패널이 말하는 명제. 영어.

**시각 형태 어휘집** (imagegen이 안정적으로 그려내는 것들):
좌표축 곡선 · 그룹 막대그래프 · 가로 막대 비교 · 파이/도넛 · 저울(balance) · 정사각 히트맵 행렬 ·
산점도+회귀선 · 등고선 타일 · 토큰/패치 그리드 · 파이프라인 박스열(→ 화살표) · 말풍선 ·
큰 숫자 통계 타일 · 체크(✓)·엑스(✗) 비교 박스 · 수식 박스 · 단면도(방·문) · 아이콘+라벨 카드

**숫자 의무** — 논문의 표·그림에서 **직접 읽은 값**을 그대로 박는다.
`성능이 향상된다` ✗ → `12.5% -> 5.1% at L = 192` ✓ / `토큰이 줄어든다` ✗ → `33,000 -> 14,000 -> 3,600` ✓
(원본 figure의 막대값을 쓰려면 그 PNG를 Read로 열어 눈으로 읽고 적는다.)

**텍스트 규칙**
- 이미지에 들어갈 **라벨·수식은 영어 ASCII로만** 적는다. 한글 라벨은 이미지에서 깨지고, 프롬프트 본문에 섞인
  비ASCII 이물(중국어·이모지 등)도 그대로 그려지는 사고가 있다 — 작성 후 라벨 부분을 한 번 훑는다.
- LaTeX 대신 ASCII 근사: `sum` `sqrt` `<=` `>=` `->` `alpha` `Delta` `x*` `phi_k` `O*(1/L)`.
- **패널당 라벨 1~6개**. 그 이상 넣으면 글자가 뭉개지고 철자가 깨진다.

#### 11.8.4 이미지 종류별 밀도 등급 — 조밀함이 항상 정답은 아니다

| 파일 | 캔버스 | 블록/단 | 패널 총수 | prompt 분량 | 성격 |
|---|---|---|---|---|---|
| `dissection_overview.png` | 1536×864 | 5단 고정 | **15~20** | 3.5~4.5 KB | 논문 전체를 한 장에 — **최대 밀도** |
| `questions_*.png` / `knowledge_*.png` | 1024×1024 | 2~3 블록 | 5~9 | 1.5~2.5 KB | 개념도 — **한 가지 논점만** |
| `simulator_*.png` | 1024×1024 | 단계 수만큼 | 4~8 | 1.5~2.5 KB | 알고리즘 단계 시각화 |
| `qa_<qid>_*.png` | 1024×1024 | 1~2 블록 | 3~5 | 1~1.5 KB | 질문 하나의 보조 — **최소 밀도** |

- overview는 **조밀할수록 좋다**. 정본 3편(§11.8.9)이 기준선이고, 그보다 성기면 미달이다.
- 반대로 **개념도에 overview 밀도를 넣으면 실패한다** — 1024×1024에 15개 패널을 넣으면 글자가 읽히지 않는다.
  개념도는 "한 문장으로 말할 수 있는 논점 하나"를 2~3블록으로 나눠 크게 그린다.

#### 11.8.5 병렬 생성 시 작업 디렉토리 격리 (필수)

여러 이미지를 `run_in_background`로 동시에 만들 때 **모든 호출이 같은 `--cd`를 공유하면 안 된다.**
codex는 작업 디렉토리 전체를 읽을 수 있어, 동시 실행 중인 형제 프로세스가 방금 만든 PNG를
"이미 있는 결과"로 오인·복제하는 사고가 실제로 발생했다.

- 호출마다 `scratchpad/img_<purpose>/` 같은 **격리 디렉토리**를 만들고 해당 prompt 파일 **하나만** 복사해 넣는다.
- 경로에 한글이 있어도 codex는 동작하지만, ASCII scratchpad에서 생성한 뒤
  `papers/N. name/assets/generated/`로 복사하는 편이 인코딩 사고를 원천 차단한다.
- **파일 해시 비교로는 이 사고가 안 잡힌다** (재인코딩되어 md5가 달라짐). 반드시 눈으로 확인(§11.8.6).

#### 11.8.6 검수 체크리스트 — 기계 검사 → PNG 육안 확인

**0단계 (codex 호출 전, 자동)** — 이 저장소에는 **PreToolUse(Bash) 훅**이 걸려 있어
`codex` 가 포함된 Bash 호출을 가로채 `--cd` 로 지정된 prompt.txt를 자동 검사하고,
FAIL이 있으면 **호출 자체를 차단**한다 (`.claude/settings.json` → `tools/hook_precheck_codex.py`).
훅이 없는 환경(다른 PC·CI)에서는 아래를 손으로 돌린다.

```bash
python tools/check_image_prompts.py "papers/N. shortname"      # 논문 전체
python tools/check_image_prompts.py <prompt 파일 경로>          # 파일 하나
```

이 스크립트가 검사하는 것: 캔버스 선언 · 5단 헤더(overview) · 패널 수 · **본문 수치 개수** ·
팔레트 hex · `NOT a transparent cutout` · 6번째 계명 · 한자 이물 · **분량 하한** · 짝 PNG 존재.
하드 실패는 서식에 강건한 항목만(수치·분량·헤더·금칙어), 패널 수 등은 참고용 warn이다.

> 훅의 안전 설계 — 게이트가 작업을 잘못 막는 쪽이 더 나쁘므로, stdin 파싱 실패·프롬프트 파일 미발견·
> 검사기 예외는 **전부 통과**시킨다. 같은 파일명이 여러 논문에 있으므로 `--cd` 로 실제 파일을 특정하고,
> 특정에 실패하면 후보가 정확히 1개일 때만 검사한다.

**1단계 (생성 후, 의무)** — PNG를 Read로 연다. "검수는 사후"란 **사용자에게 넘기기 전에 Claude가 확인한다**는 뜻이지, 확인을 생략한다는 뜻이 아니다.

- [ ] 프롬프트에 적은 **패널이 전부 있는가** (누락·병합 없음)
- [ ] **여백이 과도하지 않은가** (§11.8.4 밀도 등급 대비)
- [ ] **수치가 논문 값과 일치하는가** (막대 높이·라벨 오기)
- [ ] 라벨이 **영어이고 철자가 깨지지 않았는가**
- [ ] 상단에 **논문 제목·저자명이 박히지 않았는가** (6번째 계명)
- [ ] 배경이 **불투명한 풀 블리드**인가 (컷아웃 아님)
- [ ] **요청한 프롬프트의 내용이 맞는가** (§11.8.5 혼선 여부)

#### 11.8.7 실패 모드 → 처방

| 증상 | 원인 | 처방 |
|---|---|---|
| 여백 크고 요소가 적음 | ③ 패널 명세가 성김 | 단마다 패널 3~4개로 늘리고 각 패널에 (a)(b)(c) 3요소 명시 |
| 다른 프롬프트의 그림이 저장됨 | 병렬 호출이 `--cd` 공유 | §11.8.5 격리 디렉토리로 재생성 |
| 글자 뭉개짐·철자 깨짐 | 패널당 라벨 과다 / 캔버스 대비 밀도 초과 | 라벨을 패널당 6개 이하로, 또는 밀도 등급을 한 단계 낮춤 |
| 상단에 논문 제목·저자명 | ⑤ 6번째 계명 누락 | 마지막 줄 `NO paper title at top…` 추가 |
| 투명 배경 컷아웃 | ⑤ 스타일 지시 누락 | `풀 블리드` + `NOT a transparent cutout` 명시 |
| 수치가 논문과 다름 | 프롬프트에 값을 안 적음 | 표·그림에서 읽은 실제 값을 (b)에 박아 재생성 |
| 이미지에 한글/이물 문자 | 프롬프트 라벨이 비ASCII | 라벨을 영어 ASCII로 고쳐 재생성 |
| CP949 깨짐·hang | PowerShell 사용 / stdin 미차단 | §11.2 — Bash + `< /dev/null` |

위 증상 중 ①③④⑥⑦⑧은 `tools/check_image_prompts.py`가 **생성 전에** 잡아낸다 — 먼저 돌린다.

#### 11.8.8 재생성 루프

1차 결과가 기준 미달이면 **프롬프트를 고쳐서** 재생성한다.
**같은 프롬프트로 재시도하지 않는다** — 밀도가 같으면 결과 밀도도 같다.
무엇을 더 써야 할지 모르겠으면 밀도 정본을 열어 자기 프롬프트와 나란히 비교한다.

#### 11.8.9 밀도 정본 (열어서 보고 따라 쓸 것)

- `papers/20. sparse_vlm/assets/generated/prompt_dissection_overview.txt` (+ 결과 PNG)
- `papers/24. geollava8k/assets/generated/prompt_dissection_overview.txt` (+ 결과 PNG)
- `papers/25. visiondrop/assets/generated/prompt_dissection_overview.txt` (+ 결과 PNG)
- `papers/27. lupi/assets/generated/prompt_dissection_overview.txt` — 이론 논문(자산 figure 1장) 적용례

> 정본 학습 사례 (실패→복구): `papers/27. lupi` 1차 생성 시 §11.3의 얇은 스켈레톤(`[좌/상 패널] <설명>`)을
> 그대로 따라 단마다 요소를 1~2개만 적었고, 여백이 크고 정보량이 적은 그림이 나왔다.
> 사용자가 20·24번과 비교 지적 → 프롬프트를 2.9 KB → 4.4 KB로 재작성해 재생성.
> 같은 세션에서 병렬 호출 `--cd` 공유로 `knowledge_convergence.png`가 다른 그림으로 저장되는 사고도 발생.
> 이 절(11.8)과 §14.5, `prompts/04_research_analysis.md`의 템플릿 교체가 그 직접 결과물이다.

---

## 12. Study Modal — 자산별 학습 가이드 모달 (3세대 정본)

각 figure/table 카드 우상단에 떠 있는 `<button class="study-fab">` 버튼을 누르면, 그 자산 전용 깊이 분해 모달이 열린다. 정본 = `samples/cares/CARES_output.html`의 study-fab → 우측 study-drawer (§12.5/§12.6).

### 12.1 무엇이 들어가는가 (정형 4-섹션)

**`<template class="study-guide">` 안에 항상 네 섹션이 들어간다.** 어느 섹션도 비어 있으면 안 된다.

| 섹션 클래스 | 라벨 | 역할 |
|---|---|---|
| `s-look` | "어디를 먼저 볼까" | 시선 동선 + (다이어그램이면) 모든 박스·화살표·N×·인코더/디코더 등 **모든 구성 요소의 의미 풀이** |
| `s-num` | "결정적 숫자" | `.study-num-row` ≥3개 — label·value 페어로 결정적 수치를 박스에 깔고, 그 숫자의 **의미 한 줄** |
| `s-author` | "저자가 말하는 것" | 이 그림으로 저자가 못 박는 **명제 1~3개** — 시각적 증거가 어떤 주장과 연결되는지 |
| `s-check` | "학습 체크포인트" | `<ul>` 2~4개 — 다음에 다시 볼 때 가장 먼저 확인할 부분 / 이 그림이 논문 전체의 무엇을 압축하는지 |

### 12.2 ❌ 안티패턴 (정본이 아닌 잘못된 패턴)

다음은 papers 4~19에서 누적된 **잘못된 관성** — 새 빌드에서 따르지 않는다:

```html
<!-- ❌ BAD — modal이 figure 하단의 interpretation/beginner-note의 단순 복제 -->
<template class="study-guide">
  <div class="study-section"><span class="study-label">캡션</span><p>(원문 캡션 그대로)</p></div>
  <div class="study-section s-look"><span class="study-label">전문가 해석</span><p>(interpretations[aid]와 거의 같은 문장)</p></div>
  <div class="study-section s-author"><span class="study-label">초보자 해설</span><p>(beginner_notes[aid]와 거의 같은 문장)</p></div>
</template>
```

**왜 잘못인가**: figure 카드 바로 아래에 이미 `.interpretation`과 `<details class="beginner-note">`가 표시되므로, 모달이 같은 내용을 다시 보여주면 사용자가 두 번째로 클릭할 이유가 없다. **모달 무용지물**.

### 12.3 ✅ 정본 마크업 (SGL fig_1 패턴)

```html
<figure class="asset-card" id="fig_1">
  <div class="asset-image-wrap">
    <img src="data:image/png;base64,..." alt="FIG 1" />
    <button class="study-fab" data-asset="fig_1" aria-label="학습 가이드 열기">
      <span class="study-fab-glyph">?</span> 학습 가이드
    </button>
  </div>
  <figcaption>
    <span class="asset-label">FIG 1</span>
    <p class="asset-cap">...캡션(한국어 번역 — config#captions · 원문은 config#captions_en)...</p>

    <template class="study-guide">
      <div class="study-section s-look">
        <span class="study-label">▸ 어디를 먼저 볼까</span>
        <p>3-패널을 <strong>(a) → (b) → (c)</strong> 순서로 시선을 끌고 가는 도식이다. (a)에서는 <em>9% 잔류 지점에서 4 곡선이 갈라지는 폭</em>을 먼저 본다. ...</p>
      </div>
      <div class="study-section s-num">
        <span class="study-label">▸ 결정적 숫자</span>
        <div class="study-num-row"><b>9% 잔류 · FastV</b><span>43.84 (TextVQA)</span></div>
        <div class="study-num-row"><b>9% 잔류 · Oracle</b><span>80.04 (+36.2점)</span></div>
        <div class="study-num-row"><b>2B vs 26B FLOPs</b><span>약 1 : 14 (≈ 7%)</span></div>
      </div>
      <div class="study-section s-author">
        <span class="study-label">▸ 저자가 말하는 것</span>
        <p>이 한 장으로 <strong>세 명제</strong>를 시각적으로 못 박는다. ① "정보는 attention 안에 있다, 단지 단일 layer로는 못 본다" ...</p>
      </div>
      <div class="study-section s-check">
        <span class="study-label">▸ 학습 체크포인트</span>
        <ul>
          <li>(b)에서 <strong>답이 틀린 행</strong>도 노란 패치는 답 영역을 짚는다 — 다음에 다시 볼 때 가장 먼저 확인할 부분.</li>
          <li>9% 잔류는 단순한 숫자가 아니라 <strong>91% pruning</strong>이라는 SGL의 marketing claim 그 자체.</li>
        </ul>
      </div>
    </template>
  </figcaption>
</figure>
```

### 12.4 자산 유형별 깊이 의무

- **다이어그램(아키텍처/파이프라인) 자산**: `s-look`에 그림 속 **모든 박스 이름·화살표 흐름·반복 표기(N×, iter)·인코더/디코더/projector 같은 보편 용어**의 그 논문 맥락 풀이가 들어가야 함. "Encoder는 무엇을 입력받아 무엇을 출력하는지" / "N× 반복은 왜 N회인지, N은 어디서 정해지는지" 까지.
- **그래프 자산**: `s-num`에 **숫자 변화의 의미** — 단순 수치 대비가 아니라 "9% 잔류 = 91% pruning = marketing claim 그 자체" 식으로 숫자의 정치적·실용적 함의.
- **표 자산**: `s-num`에 **행/열 라벨·기호(* † ↓ ↑ Δ)의 의미** + **최우수 셀의 비교 우위 출처** ("같은 토큰 예산에서 +2~3p 앞섬 — 분배만 똑똑하게 해도 이긴다").

### 12.5 CSS 정본 — 오른쪽 사이드 드로어 (2026-05-19 갱신)

> **변경 이력**: 원래 풀스크린 dim + 중앙 정렬 모달이었으나, 학습자가 가이드를 읽는 동안 정작 봐야 할 figure를 가리는 문제가 있어 **오른쪽 슬라이드-인 드로어**로 전환. 사용자 직접 지적(24. geollava8k 학습 중, 2026-05-19). 이전 세대(SGL) 풀스크린 모달은 폐기 — 아래 우측 드로어 정본을 사용(SGL 견본 HTML은 배포본 미포함). cross-ref: `[[feedback_study_modal_drawer]]`.

핵심 동작:
- 폭 `min(440px, 100vw)` 오른쪽 고정 드로어. 백드롭 dim 없음 — 왼쪽의 figure/문장이 항상 보임
- 페이지 인터랙션(이미지 lightbox 클릭·문장 호버·스크롤) 드로어 열린 상태에서 모두 살아 있음 — `pointer-events:none` 기본 + 카드 영역만 `auto`
- `document.body.style.overflow`를 잠그지 말 것 (lightbox와 다름)

```css
.study-fab{position:absolute;top:14px;right:14px;display:inline-flex;align-items:center;gap:6px;padding:7px 13px 7px 11px;border-radius:999px;background:rgba(139,117,192,0.94);color:#ffffff;border:1px solid rgba(255,255,255,0.4);font:inherit;font-size:12.5px;font-weight:700;letter-spacing:0.04em;cursor:pointer;box-shadow:0 6px 18px rgba(80,60,140,0.32);backdrop-filter:blur(2px);transition:transform 140ms ease,background 140ms ease;z-index:5}
.study-fab:hover{transform:translateY(-1px);background:var(--accent);box-shadow:0 10px 22px rgba(80,60,140,0.42)}
.study-fab .study-fab-glyph{display:inline-block;width:18px;height:18px;line-height:18px;border-radius:50%;background:#ffffff;color:var(--accent);font-size:12px;text-align:center;font-weight:800}

.study-modal{position:fixed;top:0;right:0;bottom:0;width:min(440px,100vw);z-index:300;display:none;background:transparent;pointer-events:none}
.study-modal.open{display:block;pointer-events:auto}
.study-modal-card{position:relative;width:100%;height:100%;max-width:none;background:var(--paper);border:1px solid var(--line);border-right:none;border-radius:18px 0 0 18px;padding:22px 24px 24px;box-shadow:-14px 0 36px rgba(20,10,30,0.18);animation:study-slide-in 220ms ease-out;overflow-y:auto;box-sizing:border-box}
@keyframes study-slide-in{0%{transform:translateX(100%)}100%{transform:translateX(0)}}

.study-modal-head{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-bottom:12px;margin-bottom:14px;border-bottom:1px solid var(--line)}
.study-modal-title{margin:0;font-family:Georgia,serif;font-size:19px;color:var(--accent)}
.study-modal-close{border:1px solid var(--line);background:#ffffff;border-radius:50%;width:34px;height:34px;font-size:18px;line-height:1;color:var(--muted);cursor:pointer;flex-shrink:0}
.study-modal-close:hover{color:var(--accent);border-color:var(--accent)}
.study-modal-body{font-size:14px;line-height:1.7;color:var(--ink)}
.study-modal-body .study-section{margin-bottom:16px}
.study-modal-body .study-section:last-child{margin-bottom:0}
.study-modal-body .study-label{display:inline-block;font-size:11px;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;margin:0 0 6px;padding:3px 10px;border-radius:999px}
.study-modal-body .s-look   .study-label{background:var(--accent-soft);color:var(--accent)}
.study-modal-body .s-num    .study-label{background:var(--amber-soft);color:var(--amber)}
.study-modal-body .s-author .study-label{background:var(--rose-soft);color:var(--rose)}
.study-modal-body .s-check  .study-label{background:var(--mint-soft);color:var(--mint)}
.study-modal-body .study-num-row{display:grid;grid-template-columns:minmax(160px,max-content) 1fr;gap:6px 14px;margin-top:8px;padding:10px 12px;background:#fbfaff;border:1px dashed var(--line);border-radius:10px;font-size:13.5px}
.study-modal-body .study-num-row > b{font-family:"Consolas","Courier New",monospace;color:var(--accent);font-weight:800}
@media (max-width: 640px){
  .study-modal-body .study-num-row{grid-template-columns:1fr}
}

@media print{.study-fab,.study-modal{display:none !important}}
```

클래스 책임 요약:

```
.study-fab            /* 우상단 떠 있는 라벤더 버튼 (asset-image-wrap 자식) */
.study-fab-glyph      /* 버튼 안의 ? 글리프 */
.study-modal          /* 오른쪽 고정 드로어 컨테이너 — pointer-events 게이트 */
.study-modal.open     /* 활성 상태 (display:block + pointer-events:auto) */
.study-modal-card     /* 드로어 카드 — 100% 폭·100% 높이, 슬라이드-인 애니메이션 */
.study-modal-head     /* 제목 + 닫기 버튼 */
.study-modal-title    /* 모달 제목 */
.study-modal-close    /* 우상단 × */
.study-modal-body     /* 본문 — .study-section을 감쌈 */
.study-section.s-look | .s-num | .s-author | .s-check
.study-num-row        /* label·value 페어 grid */
```

### 12.6 JS — 데이터 주입 + 3-way 닫기 (2026-05-19 갱신)

빌더는 `analysis.json#study_modals`를 받아 페이지 끝에 다음 형태의 `<script>`를 인라인한다. **닫기 트리거 3가지** — ① ×버튼 ② ESC 키 ③ 드로어 바깥(페이지 어느 곳이든) 클릭. 단 ③의 예외: `.study-fab` 클릭은 닫기 대상에서 제외(다른 figure로 내용 전환 시 깜빡임 방지).

```js
(function () {
  const modal     = document.querySelector('.study-modal');
  const modalTitle = modal.querySelector('.study-modal-title');
  const modalBody  = modal.querySelector('.study-modal-body');

  const STUDY = {
    "fig_1": {
      title: "학습 가이드 — Figure 1",
      html: /* template.study-guide 안의 4 섹션 HTML 그대로 */
    },
    // ...
  };

  document.querySelectorAll('.study-fab').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();              // §13.5: lightbox 트리거 차단
      const aid = btn.dataset.asset;
      const data = STUDY[aid];
      modalTitle.textContent = data.title;
      modalBody.innerHTML = data.html;
      modal.classList.add('open');
      if (window.MathJax?.typesetPromise) window.MathJax.typesetPromise([modalBody]).catch(()=>{});
    });
  });

  // 닫기 ① ×버튼
  modal.querySelector('.study-modal-close')
       .addEventListener('click', () => modal.classList.remove('open'));

  // 닫기 ② ESC 키
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && modal.classList.contains('open')) {
      modal.classList.remove('open');
    }
  });

  // 닫기 ③ 드로어 바깥 클릭 (단, .study-fab 클릭은 제외)
  document.addEventListener('click', e => {
    if (!modal.classList.contains('open')) return;
    if (modal.contains(e.target)) return;
    if (e.target.closest('.study-fab')) return;
    modal.classList.remove('open');
  });
})();
```

**❌ 폐기된 닫기 패턴** (재도입 금지):

```js
// ❌ 풀스크린 모달 시절의 backdrop 클릭 — 드로어에는 backdrop이 없으므로 무의미
modal.addEventListener('click', e => {
  if (e.target === modal || e.target.classList.contains('study-modal-close')) {
    modal.classList.remove('open');
  }
});
```

### 12.7 데이터 소스 — `analysis.json#study_modals`

스키마와 작성 가이드: `prompts/06_figure_interpretation.md` § Layer 3.

```json
"study_modals": {
  "fig_1": {
    "title": "학습 가이드 — Figure 1",
    "look":   "...",
    "nums":   [["label", "value"], ...],   // ≥3
    "author": "...",
    "check":  ["...", "..."]               // ≥2
  }
}
```

### 12.8 빌더 헬퍼

`_build.py`에서 study modal 마크업을 한 번에 만드는 헬퍼 정형:

```python
def render_study_modal(aid: str, sm: dict) -> str:
    nums_html = "".join(
        f'<div class="study-num-row"><b>{esc(lbl)}</b><span>{esc(val)}</span></div>'
        for lbl, val in sm.get("nums", [])
    )
    check_html = "".join(f'<li>{c}</li>' for c in sm.get("check", []))
    return (
        '<template class="study-guide">'
        '<div class="study-section s-look"><span class="study-label">▸ 어디를 먼저 볼까</span>'
        f'<p>{sm["look"]}</p></div>'
        '<div class="study-section s-num"><span class="study-label">▸ 결정적 숫자</span>'
        f'{nums_html}</div>'
        '<div class="study-section s-author"><span class="study-label">▸ 저자가 말하는 것</span>'
        f'<p>{sm["author"]}</p></div>'
        '<div class="study-section s-check"><span class="study-label">▸ 학습 체크포인트</span>'
        f'<ul>{check_html}</ul></div>'
        '</template>'
    )
```

자산 카드 안에는 `<button class="study-fab" data-asset="{aid}">…</button>`을 `.asset-image-wrap` 자식으로 항상 추가, 그리고 페이지 끝에 `STUDY` 객체와 클릭 핸들러를 한 번만 주입.

---

## 13. Image Lightbox — 모든 콘텐츠 이미지의 비율 유지 확대 (정본, 2026-05-12)

학습 자료의 모든 콘텐츠 이미지(① 자산·② summary overview·③ 학습 보조)는 클릭 시 **비율 유지 lightbox**로 확대 가능해야 한다. 인쇄·작은 화면·세부 디테일 확인을 위한 표준 UX.

### 13.1 대상 이미지

| 셀렉터 | 위치 | 개수 |
|---|---|---|
| `.asset-image-wrap img` | ① tab-reading의 figure/table crops | 자산 수만큼 |
| `.diss-overview-figure img` | ② tab-dissection의 summary 카드 overview | 0 또는 1 |
| `.concept-figure img` | ③ tab-knowledge / ② / ④ 등의 학습 보조 | 0 ~ 다수 |

위 셀렉터의 img 태그는 모두 `cursor: zoom-in` + 클릭 시 lightbox 모달 열림. **lightbox 내부 img 자체는 제외** (`img.closest('.img-lightbox')` 체크).

### 13.2 정본 마크업 (BODY 끝에 한 번만)

```html
<div class="img-lightbox" role="dialog" aria-modal="true" aria-label="이미지 확대 보기">
  <button class="img-lightbox-close" type="button" aria-label="닫기">×</button>
  <div class="img-lightbox-stage"><img alt="" /></div>
  <div class="img-lightbox-hint">클릭 또는 ESC: 닫기 · 휠/+/−: 확대·축소 · 드래그: 이동</div>
</div>
```

### 13.3 정본 CSS

```css
.asset-image-wrap img,
.concept-figure img,
.diss-overview-figure img { cursor: zoom-in; transition: opacity 140ms ease; }
.asset-image-wrap img:hover,
.concept-figure img:hover,
.diss-overview-figure img:hover { opacity: 0.92; }

.img-lightbox { position:fixed; inset:0; z-index:400; display:none; align-items:center; justify-content:center; background:rgba(20,18,30,0.92); padding:32px; cursor:zoom-out; }
.img-lightbox.open { display:flex; animation:lightbox-fade 180ms ease-out; }
@keyframes lightbox-fade { 0%{opacity:0} 100%{opacity:1} }
.img-lightbox-stage { position:relative; max-width:100%; max-height:100%; display:flex; align-items:center; justify-content:center; overflow:hidden; }
.img-lightbox img { display:block; max-width:100%; max-height:calc(100vh - 80px); width:auto; height:auto; object-fit:contain; border-radius:8px; box-shadow:0 24px 60px rgba(0,0,0,0.5); transition:transform 200ms ease; transform-origin:center center; }
.img-lightbox.zoomed { cursor:grab; }
.img-lightbox.zoomed img { cursor:grab; transition:transform 80ms ease-out; }
.img-lightbox.grabbing, .img-lightbox.grabbing img { cursor:grabbing; }
.img-lightbox-close { position:fixed; top:18px; right:22px; background:rgba(255,255,255,0.92); color:#1f1d24; border:none; border-radius:50%; width:42px; height:42px; font-size:22px; font-weight:700; line-height:1; cursor:pointer; box-shadow:0 6px 18px rgba(0,0,0,0.35); z-index:401; }
.img-lightbox-close:hover { background:#fff; }
.img-lightbox-hint { position:fixed; bottom:18px; left:50%; transform:translateX(-50%); color:rgba(255,255,255,0.78); font-size:12.5px; letter-spacing:0.04em; background:rgba(31,29,36,0.62); padding:6px 14px; border-radius:999px; pointer-events:none; }

@media (max-width: 640px) {
  .img-lightbox { padding:14px; }
  .img-lightbox-close { top:10px; right:12px; width:36px; height:36px; font-size:18px; }
  .img-lightbox-hint { font-size:11px; bottom:10px; }
}
@media print {
  .img-lightbox { display:none !important; }
}
```

### 13.4 정본 JS — lightbox 열기·닫기·zoom·pan

```js
// Image lightbox — 비율 유지 확대·축소
const lightbox = document.querySelector('.img-lightbox');
const lbImg    = lightbox?.querySelector('.img-lightbox-stage img');
let lbScale = 1, lbTx = 0, lbTy = 0, lbDragging = false, lbDragStart = null;

function lbApply(){
  if (!lbImg) return;
  lbImg.style.transform = `translate(${lbTx}px, ${lbTy}px) scale(${lbScale})`;
  lightbox.classList.toggle('zoomed', lbScale > 1.02);
}
function lbReset(){ lbScale = 1; lbTx = 0; lbTy = 0; lbApply(); }
function lbOpen(src, alt){
  if (!lightbox || !lbImg) return;
  lbImg.src = src; lbImg.alt = alt || ''; lbReset();
  lightbox.classList.add('open');
  document.body.style.overflow = 'hidden';
}
function lbClose(){
  if (!lightbox) return;
  lightbox.classList.remove('open');
  document.body.style.overflow = '';
  lbReset();
}
// 모든 콘텐츠 이미지 클릭 → lightbox
document.querySelectorAll('.asset-image-wrap img, .concept-figure img, .diss-overview-figure img').forEach(img => {
  img.addEventListener('click', e => {
    if (img.closest('.img-lightbox')) return;
    e.preventDefault();
    lbOpen(img.src, img.alt);
  });
});
// 바깥/× 클릭 닫기
lightbox?.addEventListener('click', e => {
  if (e.target === lightbox || e.target.classList.contains('img-lightbox-close')) lbClose();
});
lbImg?.addEventListener('click', e => e.stopPropagation());
// 휠 줌
lightbox?.addEventListener('wheel', e => {
  e.preventDefault();
  const delta = e.deltaY < 0 ? 1.12 : 1/1.12;
  lbScale = Math.max(0.5, Math.min(8, lbScale * delta));
  if (lbScale <= 1.02) { lbTx = 0; lbTy = 0; lbScale = 1; }
  lbApply();
}, {passive:false});
// 더블클릭 1x ↔ 2.5x
lbImg?.addEventListener('dblclick', e => {
  e.stopPropagation();
  if (lbScale > 1.5) lbReset();
  else { lbScale = 2.5; lbApply(); }
});
// 드래그 pan
lbImg?.addEventListener('mousedown', e => {
  if (lbScale <= 1.02) return;
  e.preventDefault();
  lbDragging = true;
  lbDragStart = { x: e.clientX - lbTx, y: e.clientY - lbTy };
  lightbox.classList.add('grabbing');
});
document.addEventListener('mousemove', e => {
  if (!lbDragging) return;
  lbTx = e.clientX - lbDragStart.x;
  lbTy = e.clientY - lbDragStart.y;
  lbApply();
});
document.addEventListener('mouseup', () => {
  lbDragging = false;
  lightbox?.classList.remove('grabbing');
});
// 키보드: ESC / + − / 0
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && lightbox?.classList.contains('open')) { lbClose(); return; }
  if (!lightbox?.classList.contains('open')) return;
  if (e.key === '+' || e.key === '=') { lbScale = Math.min(8, lbScale * 1.2); lbApply(); }
  else if (e.key === '-' || e.key === '_') { lbScale = Math.max(0.5, lbScale / 1.2); if (lbScale <= 1.02){lbTx=0;lbTy=0;lbScale=1;} lbApply(); }
  else if (e.key === '0') lbReset();
});
```

### 13.5 study-fab과의 충돌 회피 (중요)

`.asset-image-wrap` 안에 `.study-fab` 버튼이 있을 때 — 버튼 클릭이 이미지 클릭으로 bubbling되어 lightbox가 함께 열리면 안 됨. **study-fab 클릭 핸들러 첫 줄에**:

```js
btn.addEventListener('click', e => {
  e.preventDefault();
  e.stopPropagation();   // ← lightbox 트리거 차단
  // ... study modal 열기
});
```

이 한 줄이 빠지면 \"버튼 누르면 모달 + lightbox 동시에 열림\"의 버그.

### 13.6 정본 사례

- `samples/cares/_build.py` — CSS·JS·BODY 컨테이너 통합 정본
- 적용 대상: 모든 신규 빌드 + 기존 paper도 점진적 마이그레이션 권장

---

## 14. `.diss-overview-figure` — Summary 카드 한 장 정리 이미지 (정본, 2026-05-12)

② Paper Dissection 탭의 `diss-summary` 카드 헤더 아래·rows 위에 **한 장 인포그래픽**을 동봉하는 컴포넌트. 본 논문의 전체 메시지를 5단(PROBLEM → KEY OBSERVATIONS → METHOD → WHAT'S NEW → RESULTS)으로 시각화.

### 14.1 정본 마크업

```html
<figure class="diss-overview-figure">
  <img src="data:image/png;base64,..." alt="<short_name> 한 장 정리" />
  <figcaption>
    <span class="cf-label">학습 보조 · 한 장 정리</span>
    <h4>문제 → 관찰 → 방법 → 차별 → 결과 — 5단 흐름</h4>
    <p>이 다이어그램이 본 논문의 모든 핵심 메시지를 시각화한다. 좌→우로 따라가며 어떤 문제를, 어떤 관찰로, 어떤 방법으로, 어떻게 차별화해서, 어떤 효과로 풀었는지를 한눈에.</p>
  </figcaption>
</figure>
```

### 14.2 정본 CSS

```css
.diss-overview-figure { background:#fefcff; border:1px solid var(--line); border-radius:14px; padding:16px 18px; margin:0 0 16px; box-shadow:0 4px 14px rgba(80,60,140,0.05); }
.diss-overview-figure img { display:block; width:100%; max-width:1100px; height:auto; margin:0 auto; border-radius:10px; border:1px solid var(--line); background:#fbfaff; cursor:zoom-in; transition:opacity 140ms ease; }
.diss-overview-figure img:hover { opacity:0.92; }
.diss-overview-figure figcaption { margin-top:12px; text-align:center; }
.diss-overview-figure figcaption .cf-label { display:inline-block; font-size:11px; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; color:#3d2a5e; background:#ece2f8; padding:3px 10px; border-radius:999px; margin-bottom:6px; }
.diss-overview-figure figcaption h4 { margin:4px 0 6px; font-family:Georgia,serif; font-size:16px; color:var(--ink); }
.diss-overview-figure figcaption p { margin:0; font-size:13px; color:var(--muted); line-height:1.65; max-width:800px; margin-left:auto; margin-right:auto; }
```

### 14.3 빌더 헬퍼 — summary 카드 분기

`_build.py`의 `render_diss(c, idx)` 안에서 `c["id"] == "summary"` 분기 시:

```python
overview_html = ""
if c["id"] == "summary" and "dissection_overview" in GEN_DATA:
    overview_html = (
        '<figure class="diss-overview-figure">'
        f'<img src="{GEN_DATA["dissection_overview"]}" alt="한 장 정리" />'
        '<figcaption>'
        '<span class="cf-label">학습 보조 · 한 장 정리</span>'
        '<h4>문제 → 관찰 → 방법 → 차별 → 결과 — 5단 흐름</h4>'
        '<p>이 다이어그램이 본 논문의 모든 핵심 메시지를 시각화한다. ...</p>'
        '</figcaption>'
        '</figure>'
    )
return (
    f'<article class="diss-card {CARD_CLS.get(c["id"], "")}">'
    f'<div class="diss-step">{idx:02d}</div>'
    '<div class="diss-head">...</div>'
    f'{overview_html}'   # ← 헤더와 rows 사이
    f'<div class="diss-rows">{rows_html}</div>'
    '</article>'
)
```

### 14.4 정본 사례·데이터 소스

- 정본 사례: `samples/cares/assets/generated/dissection_overview.png` (1536×864, 한글 5단 라벨)
- 생성 방법: codex CLI 6계명 (§11.2). prompt 표준 구성은 아래 §14.5.
- summary 카드 9-row 정형과 한 셋트 (Stage 4 정본 갱신, 2026-05-12)

### 14.5 🔴 overview 전용 밀도 규약 (정책, 2026-08-01)

> 프롬프트 작성의 일반 규칙(5블록 구조·패널 3요소·검수·실패 처방)은 **§11.8이 정본**이다. 이 절은 그중
> `dissection_overview.png`에만 적용되는 추가 제약만 적는다.

- **5단 고정** — PROBLEM / OBSERVATION / METHOD / NOVELTY / RESULTS. 단 이름과 순서를 바꾸지 않는다.
- **단마다 번호 붙인 서브패널 3~4개** (전체 15~20개). 이것이 20·24·25번과 그 이하를 가르는 유일한 변수다.
- **METHOD 단이 가장 넓다.** 메커니즘이 둘 이상이면 (A)/(B) 서브블록으로 쪼개고, 파이프라인은 단계 박스 +
  단계 사이 수치 변화(예: `33,000 -> 14,000 -> 3,600`)를 라벨로 박는다.
- **NOVELTY 단은 4줄 고정** — 선행 연구 이름 + 왜 부족한가 + 빨간 X를 3줄, 마지막 1줄만 본 논문 + 녹색 체크.
- **RESULTS 단 = 작은 차트 1개 + 큰 숫자 통계 박스 3~4개**. 한계가 있으면 맨 아래 회색 테두리 주의 박스 한 장
  (예: `One private dataset - no error bars - SVM-Delta-Plus never tested`).
- 단 헤더에 색 띠, 단 사이 가로 화살표.
- codex 인자 끝에 한 줄 덧붙인다:
  `Follow every sub-panel it lists - do not simplify or omit panels, and do not leave large empty areas.`

작성 템플릿 전문은 `prompts/04_research_analysis.md` § overview prompt 작성 가이드, 밀도 정본은 §11.8.9.

**codex 미사용 시**: 빌더가 `dissection.json` summary 카드의 `overview`(5×[label,text]) 데이터로 결정적 인라인 SVG를 렌더(§ `_overview_svg` · §11.9 mode B). codex PNG가 있으면 PNG 우선, 없으면 SVG 폴백 — 어느 쪽이든 오버뷰가 항상 표시된다(web↔CLI 통일).

---

## 15. `.diss-tag` grid stretch 버그 — 정본 수정 (필수, 2026-05-12)

② Dissection 카드의 row 라벨(`.diss-tag`)은 `.diss-row { display:grid; grid-template-columns:minmax(80px, max-content) 1fr }` 안에 위치한다. 단순 `display:inline-block`만 두면 **grid cell이 본문 텍스트 높이에 맞춰 세로 stretch**되고, `border-radius:999px`와 결합해 큰 타원·이상한 모양이 된다.

### 15.1 정본 수정 CSS

```css
.diss-row {
  display: grid;
  grid-template-columns: minmax(80px, max-content) 1fr;
  gap: 10px 14px;
  margin-bottom: 10px;
  align-items: start;          /* ← 추가: row 자체 top 정렬 */
}
.diss-tag {
  align-self: start;            /* ← 추가: 세로 stretch 차단 */
  justify-self: start;          /* ← 추가: 가로 stretch 차단 */
  width: max-content;           /* ← 추가: 텍스트 폭만 */
  white-space: nowrap;          /* ← 추가: 라벨 줄바꿈 차단 */
  line-height: 1.4;             /* ← 추가: 세로 padding 일관 */
  display: inline-block;
  font-size: 11px; font-weight: 700; color: #fff;
  background: var(--accent);
  padding: 3px 9px; border-radius: 999px;
  letter-spacing: 0.04em; text-transform: uppercase;
}
```

5개 추가 속성(`align-self:start`, `justify-self:start`, `width:max-content`, `white-space:nowrap`, `line-height:1.4`)이 결정적. 어느 하나 빠져도 paper/화면 폭에 따라 큰 타원이 다시 나타날 수 있음.

### 15.2 적용 대상

- **모든 paper 4~20의 `_build.py`**에 즉시 동기화 권장 (sed-style 일괄 갱신 가능)
- 신규 빌드는 의무

### 15.3 검증

빌드 후 ② Dissection 탭의 8장 카드를 열어, 각 row의 라벨 pill이 **본문 글자 한 줄 높이의 작은 작은 알약 모양**인지 시각 확인. 큰 타원·세로로 늘어진 모양이 보이면 위 정본 CSS가 누락된 것.

---

## 16. Dissection 카드 수직 적층 + tag 위 / body 아래 (정본 갱신, 2026-05-13)

② Dissection 탭 전체 레이아웃 정본. 이전 \"2-column grid + tag↔body 옆\" 패턴은 폐기되고, **모든 카드를 단일 컬럼으로 위에서 아래로 쌓고 각 row를 tag 한 줄 + body 한 단락의 상하 적층**으로 표시한다.

### 16.1 동기

- **카드 좌우 배치의 문제**: 한 카드의 텍스트가 길어지면 좌우로 흐름이 끊기고, 좁은 화면에서는 한 줄이 짧아 읽기 리듬이 깨진다.
- **tag↔body 옆 배치의 문제**: `grid-template-columns:auto 1fr`는 tag가 길어지면 본문 폭이 변동되고, 첫 줄만 tag 옆에 정렬돼 시각적 일관성이 떨어진다.
- **새 정본**: 모든 row를 \"태그(한 줄 pill) → 본문(한 단락)\"의 같은 패턴으로 통일. 카드를 위에서 아래로 한 호흡에 읽게 한다.

### 16.2 정본 CSS

```css
.diss-grid {
  display: grid;
  grid-template-columns: 1fr;    /* ← 단일 컬럼 (이전 repeat(2,minmax(0,1fr)) 폐기) */
  gap: 18px;
}

.diss-row {
  margin-top: 12px;
  padding: 12px 14px;
  background: rgba(251, 250, 255, 0.7);
  border-radius: 10px;
  display: flex;                  /* ← flex로 (이전 grid auto/1fr 폐기) */
  flex-direction: column;         /* ← 세로 적층 */
  gap: 8px;
  align-items: flex-start;
}

.diss-body {
  margin: 0;
  font-size: 14.5px;
  line-height: 1.7;
  color: var(--ink);
}

/* <dd> 기본 left margin 제거 — flex column 안에서 들여쓰기 차단 */
.diss-rows dd.diss-body { margin-left: 0; }

/* §15 정본 5속성은 그대로 유지 — flex 안에서도 pill 모양 보장에 필수 */
.diss-tag {
  align-self: start;
  justify-self: start;
  width: max-content;
  white-space: nowrap;
  line-height: 1.4;
  display: inline-block;
  background: var(--accent);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 3px 9px;
  border-radius: 999px;
}
```

### 16.3 마크업 (변경 없음)

기존 `<dl class="diss-rows">` + `<dt class="diss-tag">` + `<dd class="diss-body">` 마크업은 그대로 사용. CSS만 변경하므로 빌드 스크립트 렌더 코드 수정 불필요.

### 16.4 모바일

`@media (max-width: 760px)`의 `.diss-grid { grid-template-columns: 1fr }` 라인은 이제 데스크탑 기본과 동일하므로 중복이지만 — 굳이 제거할 필요 없음(다른 grid들과 함께 모바일 폴백 한 묶음 유지).

### 16.5 검증

빌드 후 ② Dissection 탭에서 확인:
- 카드 8장이 **한 컬럼**으로 위에서 아래로 적층
- 각 카드 안의 row가 **`[태그 pill, 한 줄]` → `[본문, 그 아래]`** 패턴
- 본문 들여쓰기 0 (`<dd>` 기본 margin이 제거된 상태)

정본 사례 = `samples/cares/_build.py`.

> 안티패턴 (이전 정본의 잘못된 관성): 과거 빌드는 2-column + tag-옆 본문이었다. 사용자 지적(2026-05-13)에 따라 수직 적층으로 재작성. 신규 논문은 `samples/cares`의 CSS를 베이스로 한다.

---

## 17. Paper Study 탭 — 3-Phase 비판적 읽기 워크북 (정본, 2026-07-08)

Translation과 Paper Dissection 사이의 `tab-study`. **사용자가 직접 쓰는 워크북**이라는 점에서
다른 탭(Claude의 완성 해설)과 역할이 다르다. 콘텐츠 규약·데이터 스키마 = `prompts/11_paper_study.md`,
탭 등록·라우팅 = `rules/design_v4_dashboard.md` §3-bis. **마크업·CSS·JS 정본 = `samples/cares/_build.py`** (배포본에 실제 데이터와 함께 동봉된 v4 8탭 정본)
(STUDY_CSS 블록 + `study_write`/`study_reveal`/`ev_chips` 렌더 함수 + Paper Study JS 모듈).

핵심 컴포넌트 11종과 불변 규칙 (2026-07-08 사용자 피드백 3차 반영):

0. **`.memo-fab` + `.memo-drawer` 학습 메모** — **플로팅 버튼**: to-top과 같은 x(`right:26px`),
   y는 JS가 topbar 하단 +18px로 계산(리사이즈 대응). 내용이 있으면 점 배지 표시, 드로어 열리면 버튼 숨김.
   드로어(**z 2400 — 라이트박스 2000·노트 선택 1700·자산 학습 드로어 1600·자산 뷰어 1500·본문 리더 1450 전부 위**.
   2026-07-09 1차 피드백 = 본문 리더 위로(1650), **2026-09-02 2차 피드백 = 라이트박스·해설 드로어 위로 + 겹치지 않게**(2400).
   z 만으로는 가림이 남으므로 가로 자리도 배분한다 — 사이드 드로어가 열리면 메모는 그 왼쪽에 나란히, 메모가 열리면
   전체화면 오버레이의 `right` 를 메모 폭만큼 축소. **단 축소에는 상한이 있다** (v5, 2026-09-02): 남는 폭이
   `0.95·vw − 예약폭 ≥ 560px` 를 만족할 때만 좁히고, 못 만족하면 나란히 서기를 포기(메모가 가이드 위로)하고,
   그래도 안 되면 축소 자체를 포기해 메모가 오버레이 위에 뜬다(`body.mlx-float`). 1080px 에서 가이드+메모를
   함께 열면 뷰어가 260px 로 뭉개지던 회귀를 막는 규칙이다. **v6 (2026-09-02)**: 가이드가 메모에 덮이지 않도록
   좁은 화면에서 두 드로어를 함께 줄이고(가이드 `clamp(300,36vw,440)` · 메모 `clamp(280,32vw,380)`),
   **학습 가이드를 열면 자산 뷰어는 이미지 전용**(`body.mlx-guided` — `.av-text` 숨김 + `.av-img img{max-height:82vh}`)
   이 되어 필요한 폭이 260px 로 줄어든다. 닫기는 × · ESC · **바깥 두 번 연속 클릭**(한 번으로는 닫지 않는다).
   구현·검사 = `tools/memo_layer_fix.py` · `tools/check_memo_layer.py`,
   정책 = CLAUDE.md § 메모 상시 접근 레이어)는 **자유 서식 메모장 textarea 하나** — 추가 버튼 없이 쓰는 대로
   자동 저장(400ms 디바운스, 글자 수·저장 시각 표시). 저장은 localStorage `prstudy:{SHORT}:memo`에
   **plain text** — 토글을 닫아도·브라우저를 닫아도 유지되고, 내보내기 파일의 `notes.memo`에 자동 포함.
   (구버전 JSON 배열 값은 로드 시 텍스트로 자동 마이그레이션.) **⑥ Q&A 작성 시 이 메모의 질문들이
   1순위 재료** (전용 카테고리 M "내가 남긴 질문" — `prompts/10_qa.md` § 사용자 학습 메모 반영이 정본).

1. **`.study-write` 서술칸** — textarea. `localStorage` 키 `prstudy:{short_name}:{skey}`에 자동 저장(400ms 디바운스),
   글자 수·저장 시각 표시. 탭 상단 `.study-toolbar`에 **내보내기/가져오기/모두 지우기** 3버튼 의무.
   **내보내기 = 기억된 폴더에 무다이얼로그 저장** (2026-07-08 2차 갱신): 최초 1회 `showDirectoryPicker`로
   논문 폴더의 **`study/`**(표준 레이아웃 포함)를 지정하면 디렉터리 핸들이 IndexedDB(`prstudy-fs`,
   키 `dir:{SHORT}`)에 저장되어, 이후 클릭 즉시 `{SHORT}_study_notes_{YYMMDD}.json`이 그 폴더에 생성/갱신된다
   (같은 날짜는 덮어쓰기 = 최신 스냅샷). 세션 첫 저장 시 브라우저가 권한 재확인을 한 번 요구할 수 있다
   (`ensurePerm`이 queryPermission→requestPermission 처리). **가져오기 = 페이지 안 노트 선택창**
   (`.notes-picker`) — 기억된 폴더의 *.json 목록(파일명+수정시각, 최신순)에서 클릭으로 복원, "다른 파일
   선택…"으로 OS 파일 다이얼로그 폴백. 다른 논문의 노트면 confirm으로 경고. 툴바의 **저장 위치** 버튼으로
   폴더 재지정. API 미지원 브라우저는 다운로드 폴더/파일 선택 다이얼로그로 자동 폴백.
   **Gap(Step 3)은 3분할** — `fields[]`로 ①알려진 것/②빈틈/③이 논문의 답 각각 라벨 붙은 작은 칸(`study-write-sm`).
2. **`.study-reveal` 잠금 토글** — Claude 분석은 기본 `hidden`. 버튼 라벨은 **"분석 비교하기"**. 내 답이 `data-min`
   글자 수 이상일 때만 버튼 활성(**소프트 잠금**), `.study-skip`("그래도 열기")으로 우회 가능. `data-skey`는
   **쉼표 목록 허용** (Gap 3칸 = 합산 글자 수로 판정). 열릴 때 MathJax typeset.
3. **`.read-panel` 본문 보기 패널 + `.para-reader` 단락 플로팅 리더** — 각 Step 서술칸 직전에
   그 Step이 읽어야 할 파트의 **단락 칩 목록**(`data-read-pid`). 클릭 시 탭을 떠나지 않고 플로팅
   리더가 열려 해당 단락의 EN·KR 페어(+콜아웃)를 보여준다 — **Translation 탭 DOM에서 clone**
   (`.asset-stack`·`.pid-tag`·중복 id 제거, 콘텐츠 중복 임베드 금지 - 제거된 `.asset-stack` 자리에는 도표로 가는 진입 칩을 남긴다: `tools/reader_asset_chip.py`, 클릭 = 리더 닫기 + `jumpToRef` 재사용). 이전/다음 단락·←/→ 키 내비게이션,
   읽은 단락은 **sessionStorage** `read:{pid}`에 기록되어 칩에 **✓ + 그룹 진행률(n/m)** 표시 —
   **세션 한정**(2026-07-08 정책): 파일을 닫았다 다시 열면 체크가 초기화된다(새로고침은 유지).
   단, 내보내기 파일에는 read:* 키가 포함되어 가져오기로 복원 가능. 같은 pid는
   Step 간 체크 공유(서론을 Step 2에서 읽으면 Step 3에도 ✓). 데이터는 study.json 각 step의
   `read: [{sec, label, pids?}]` — 빌더가 structured.json에서 단락을 자동 전개(subtitle 있으면 칩
   라벨로, 없으면 ¶N). 리더 푸터의 "Translation 탭에서 이 단락 보기"로 원문 컨텍스트 점프 가능.
   Step 4 가이드 질문의 `.view-chip-sm`도 리더를 연다(다른 Step의 read-group에 있는 pid면 그 그룹
   리스트를 폴백 탐색) — **위치만 안내하고 답은 노출하지 않는다.**
3-bis. **`.sent.user-hl` 문장 형광펜** — 플로팅 리더·Translation 탭 공통으로 **문장 클릭 = 하이라이트
   토글** (텍스트 드래그 선택 중·링크 클릭은 제외). data-pair 기반이라 EN·KR 쌍이 동시에 칠해지고
   양쪽 어디서든 해제 가능. localStorage `hl:{sentence_id}` — 영구 저장 + 내보내기 포함, 리더 재렌더
   시 `hlApply()`로 재적용. 색은 저채도 마커(#f5e8b8) — hotspot(amber-soft)·ev-hl(점프 플래시)과 구분.
   리더 푸터에 "문장 클릭 = 형광펜" 힌트. **호버 페어링(pair-active)은 문서 위임(delegation) 방식
   의무** — 요소별 바인딩이면 리더의 복제 문장에서 호버 동기화가 죽는다 (2026-07-08 수정).
3-ter. **`.ev-chip` 근거 점프** — `data-ev`에 sentence_id·자산 id·문단 id·섹션 id. 공용 `jumpToRef()`:
   문장은 `.ev-hl`(amber 하이라이트 3.6초, EN·KR 동시), 자산/문단은 `flash-target`, 섹션은 상단
   스크롤 + 헤더 플래시. `#tab-reading` 요소에 `scroll-margin-top`(sticky topbar 가림 방지) 의무.
   `studyNav`는 v3에서 `activate()`, v4 변환 후 `go()`(해시 라우팅 — 마우스 뒤로 가기로도 복귀).
   `/*STUDY-NAV*/` 마커 주석은 변환 도구의 앵커이므로 제거 금지.
4. **`.study-return` 플로팅 돌아가기 버튼** — 점프 직후 하단 중앙에 "↩ Paper Study로 돌아가기" 표시.
   클릭 시 Study 탭 복귀(탭별 scrollMem으로 스크롤 위치 복원), tab-study 도착 시 자동 숨김.
5. **`.study-goto` 서론 끝 복귀 버튼** — Translation 탭의 서론(s_intro) 섹션 끝에 "서론 끝 — Paper Study로
   돌아가기 ↩" 버튼을 빌드 시 주입 (RQ 찾기 동선의 자연 복귀 지점). **서론의 section_id는 `s_intro`
   관례를 따를 것** — 다른 id면 버튼이 조용히 생략된다(빌드는 성공). 최근 논문들의 semantic id 관례:
   `s_abs`/`s_intro`/`s_related`/`s_method`/`s_exp`/`s_conc`.
6. **`.asset-viewer` 도표 뷰어** — Step 1·5 썸네일 클릭 시 열리는 플로팅 창: **이미지 + 원문 캡션(EN) +
   번역(KR) + `해석 보기` 토글**. 데이터는 `config#captions_en` + `config#captions` + `analysis#interpretations`.
   레이아웃은 도표 비율로 자동 결정 — 가로형(비율≥1.45)은 텍스트 하단(`av-wide`), 세로/정방형은 우측
   400px(`av-tall`), 모바일(≤760px)은 항상 상하. 뷰어 안 이미지 클릭 → 기존 lightbox(휠 줌) 중첩.
   **헤더에 `학습 가이드` 버튼(`.study-fab.av-guide`)** — 클릭 시 Translation과 동일한 우측 study-drawer가
   4-섹션 가이드로 열리고, 뷰어는 `av-shift`로 왼쪽으로 비켜 도표가 가려지지 않는다(MutationObserver로
   드로어 open 클래스 감시). 이를 위해 drawer z-index는 1600(> 뷰어 1500, < lightbox 2000).
   ESC 중첩 처리: lightbox·드로어가 위에 열려 있으면 그 ESC는 그쪽 몫 (capture 단계 검사) — 단계적으로 닫힌다.
7. **`.study-thumbs` 썸네일** — `<img data-thumb-of="fig_N">`에 JS가 Translation 탭의 동일 자산에서
   src를 복사한다. **base64 중복 임베드 금지** (파일 크기 2배 방지). 클릭은 lightbox가 아니라 **도표 뷰어**.
8. **`.verdict-grid` 3열 대조** — 내 결론(`data-mirror`로 Step 5 저장분 자동 표시) | Claude 데이터-only 결론 |
   저자 주장(`match-support`/`match-partial`/`match-beyond` 판정 태그). `<details class="verdict-details">`로
   기본 접힘 — Step 5 스포일러 방지.

부수 설명 문구 전면 금지 (2026-07-08 사용자 지적: "문구 삭제. 의미 없음") — 탭 인트로는 h2 한 줄,
Phase 밴드는 태그+제목 한 줄(구 `.ai-note` 포함 설명 문단 전부 제거), Step 지시문은 Step 4의 한 줄만
예외. 지시는 read 패널·placeholder가 대신한다. 제목·밴드 정본 문구 표 = `prompts/11_paper_study.md`
§ 제목·문구 스타일.

---

## 검증 체크리스트 (빌드 후)

- [ ] `<header class="hero">` 존재 + 메타데이터 4종 채움
- [ ] 8탭 모두 `.tab-intro` 1개씩 (Paper Study·Mathematics 포함)
- [ ] 본문에 `Eq. N` / `Fig. N` / `Table N` 텍스트가 있으면 `<a class="ref-link">`로 자동 wrap
- [ ] 핫스팟이 정의되었으면 해당 `<span class="sent hotspot">` 렌더 + 스타일 적용
- [ ] To-top 버튼이 스크롤 시 노출
- [ ] 인쇄 미리보기에서 활성 탭만 보임
- [ ] 375px 모바일 뷰에서 탭 줄바꿈 / 표 overflow / 그리드 단일 컬럼
- [ ] 시뮬레이터 클래스가 `sim-*` (csim-* 0건)
- [ ] QA callout이 `qa-callout-block + data-variant` 형식
- [ ] **모든 figure/table에 `.study-fab` 버튼이 있고, 클릭 시 4-섹션(`s-look`/`s-num`/`s-author`/`s-check`) 정형 모달이 열림** — interpretation/beginner-note의 단순 복제가 아닌 깊이 분해 (§12 정본 SGL 패턴 일치)
- [ ] **학습 가이드가 오른쪽 사이드 드로어**로 열림 (풀스크린 모달 ✗) — `position:fixed;top:0;right:0;bottom:0;width:min(440px,100vw)` + 백드롭 dim 없음 + 드로어 열린 상태에서 figure·문장·lightbox 모두 사용 가능 (§12.5)
- [ ] 학습 가이드 닫기 트리거 **3가지 모두 동작** — ① ×버튼 ② ESC 키 ③ 드로어 바깥 클릭 (단 `.study-fab` 클릭 예외). 풀스크린 시절의 `if (e.target === modal)` backdrop 클릭 핸들러는 ✗ (§12.6)
- [ ] `analysis.json#study_modals[aid]`의 `nums` ≥3개, `check` ≥2개
- [ ] **모든 콘텐츠 이미지(① 자산·② summary overview·③ 학습 보조)에 `cursor:zoom-in` + 클릭 시 비율 유지 lightbox 열림** (§13 정본 패턴) — 휠 줌·드래그 pan·ESC 닫기 동작 확인
- [ ] **`.img-lightbox` 컨테이너 BODY 끝에 한 번만 존재**, study-fab 클릭은 `e.stopPropagation()` + `e.preventDefault()`로 lightbox 트리거 차단
- [ ] **② Dissection의 summary 카드가 9-row 정형** (한 줄 / 문제 / 관찰 / Gap / 방법 / 차별 / 효과 / 한계 / 30초 요약) + **한 장 overview 이미지(`dissection_overview.png`)가 헤더 아래·rows 위에 임베드** (§14, `prompts/04_research_analysis.md` Stage 4 정본)
- [ ] **`.diss-tag` pill이 작은 알약 모양** — 큰 타원·세로로 늘어진 모양이 안 보임. 정본 CSS(§15) 5개 속성(`align-self:start` / `justify-self:start` / `width:max-content` / `white-space:nowrap` / `line-height:1.4`) 모두 적용 확인
- [ ] **② Dissection 카드가 단일 컬럼으로 수직 적층** + **각 row가 `[태그 pill, 한 줄]` → `[본문, 그 아래]` 패턴**으로 표시 (§16 정본). `.diss-grid` = `grid-template-columns:1fr` / `.diss-row` = `display:flex; flex-direction:column` / `dd.diss-body { margin-left:0 }` 모두 적용
- [ ] **Paper Study ref 실존** — `python tools/check_study_refs.py "papers/N. name"` 통과 (study.json의 evidence/read/guide_questions ref가 모두 문장·섹션·문단·자산 id로 존재 + `captions`가 순수 영문이 아님=KR)
- [ ] **Paper Study 탭(§17)** — 서술칸 localStorage 자동 저장 + 잠금 토글("분석 비교하기", Gap 3분할 합산) + 근거·단락 칩 전수 점프 확인(모든 `data-ev`/`data-read-pid` 대상이 `id` 또는 `data-pair`로 존재) + 단락 리더 ✓ 세션 한정 + 도표 뷰어(원문 캡션·번역·해석 + 학습 가이드 드로어) + 플로팅 메모 자동 저장 + 노트 내보내기/가져오기 왕복 + 썸네일 base64 중복 임베드 0건 + `study/` 폴더 존재
- [ ] **콘텐츠 JSON에 이스케이프 안 된 `<`+영문자 없음** — `python tools/check_html_escape.py "papers/N. name"` 통과(FAIL 0건). 수식 표기(`X_{a<i}`, `y_<t`, `0.1<IOU<0.5` 류)가 HTML 태그로 파싱되면 그 지점 이후 문서 전체가 태그 수프가 된다. tex 안은 `\lt`, 일반 텍스트는 `&lt;`로

이 19개 항목 모두 통과 = 정본 일치.
