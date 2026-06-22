# Component Rules — 탭 횡단 공용 컴포넌트

## 목적

SAFE와 FrameFusion 정본 두 파일의 **마이크로 차이를 봉합**하고, 6탭 모두에 걸쳐 등장하는 공용 컴포넌트의 정식 규약을 정한다.

이 문서는 Stage 10에서 Claude가 단일 HTML을 작성할 때 따라야 할 마크업·CSS 규약이다.

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
- 6탭 모두 `.tab-intro` 1개씩 (예외 없음)
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
- 좌측에 4px 골드 stripe (`border-left: 4px solid var(--gold)`)
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

신규 논문은 `sim-*` 사용. SAFE를 v2로 재빌드할 때 `csim-*`도 마이그레이션.

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

```
교육용 학술 일러스트레이션. 정사각형 1024x1024.

주제: "<한 줄 핵심 메시지>"

구성:
[좌/상 패널] <설명>
[우/하 패널] <설명>
- 라벨: <영문 라벨 1~3개>

색상 팔레트: v3 흰색-아이보리 배경 + lavender(#8b75c0) / azure(#6b95b3) / amber(#ad8e4e) / rose(#b87887) 강조.

스타일 지시 (중요):
- 풀 블리드 일러스트 — 배경 가득
- 절대로 투명 배경 컷아웃이 아닐 것 (NOT a transparent cutout)
- Scientific American / 학술 교과서 표지 스타일
- 텍스트 라벨은 영어로 깔끔하게 (3-4개만)
- 1024x1024 정사각형
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
- 검수는 사후 — 사용자가 결과 HTML을 보고 수정이 필요한 이미지가 있으면 별도 재생성 요청. 생성-박기 흐름을 사전 검수로 막지 않는다.

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

## 12. Study Modal — 자산별 학습 가이드 모달 (3세대 정본)

각 figure/table 카드 우상단에 떠 있는 `<button class="study-fab">` 버튼을 누르면, 그 자산 전용 깊이 분해 모달이 열린다. 정본 = `samples/SGL_output.html` (특히 fig_1 모달, 라인 1054~1078).

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
    <p class="asset-cap">...원문 캡션...</p>

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

> **변경 이력**: 원래 풀스크린 dim + 중앙 정렬 모달이었으나, 학습자가 가이드를 읽는 동안 정작 봐야 할 figure를 가리는 문제가 있어 **오른쪽 슬라이드-인 드로어**로 전환. 사용자 직접 지적(24. geollava8k 학습 중, 2026-05-19). `samples/SGL_output.html`은 historical reference로 동결 — CSS는 SGL을 복사하지 말고 아래 정본을 사용. cross-ref: `[[feedback_study_modal_drawer]]`.

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

- `papers/1. voila_a/_build.py` — CSS·JS·BODY 컨테이너 통합 정본
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

- 정본 사례: `papers/1. voila_a/assets/generated/dissection_overview.png` (1536×1024, 한글 5단 라벨)
- 생성 방법: codex CLI 6계명 (§11.2). prompt 표준 구성은 `prompts/04_research_analysis.md` 참조.
- summary 카드 9-row 정형과 한 셋트 (Stage 4 정본 갱신, 2026-05-12)

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

정본 사례 = `samples/free_example/_build.py`.

> 안티패턴 (이전 정본의 잘못된 관성): 과거 빌드는 2-column + tag-옆 본문이었다. 사용자 지적(2026-05-13)에 따라 수직 적층으로 재작성. 신규 논문은 `samples/free_example` 또는 `papers/1. voila_a`의 CSS를 베이스로 한다.

---

## 검증 체크리스트 (빌드 후)

- [ ] `<header class="hero">` 존재 + 메타데이터 4종 채움
- [ ] 6탭 모두 `.tab-intro` 1개씩
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

이 16개 항목 모두 통과 = 정본 일치.
