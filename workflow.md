# Workflow — 10단계 대화형 작업 흐름

> 한 편의 논문 PDF를 **6탭 학습용 HTML**로 변환하는 단계별 흐름.
> **자동화 빌드 없이** — Claude와 대화하며 한 단계씩 콘텐츠를 정제하고, 마지막 단계에서 HTML 한 장으로 조립한다.
>
> 정본 레퍼런스: `samples/`의 3편 — SAFE(1세대 — 셸·토큰·문장 페어링), FrameFusion(2세대 — eq-link, fig-hotspot, glossary), SGL(3세대 — study-fab 모달, 3-Part Simulator)
>
> 표준 템플릿/디자인 토큰/디렉토리 규약: `CLAUDE.md` 참조
>
> ⚠️ **프롬프트 파일 번호 ≠ 스테이지 번호** (역사적 이유). 매핑:
> Stage 1→`prompts/01_cleaning`, 2→`02_structuring`, 3→`03_translation`, 4→`04_research_analysis`,
> 5→`05_coaching`, 6→`06_figure_interpretation`, 7→`07_background_knowledge`,
> **Stage 8 Simulator→`prompts/09_simulator`**, **Stage 9 QA→`prompts/10_qa`**, **Stage 10 HTML→`prompts/08_html_generation`**.

---

## Stage 0 — PDF Parsing

**도구:** PyMuPDF (fitz) 또는 동등 도구

**폴더 명명 규약:** 신규 논문 폴더는 **`N. shortname`** 형식 (예: `5. flash_attn`). 자세한 규칙은 `CLAUDE.md` "새 논문 추가 — 폴더 명명 규약" 참조. 이 문서에서 `papers/[name]/`은 `papers/N. shortname/`을 가리킨다.

**목표:**
- 텍스트 위치 정보(블록 좌표)를 보존해 다단(2-column) 순서를 정확히 복원
- Figure / Table을 PNG로 크롭

**산출물:**
- 정제된 plain text 또는 페이지별 블록 텍스트 → `papers/[name]/fulltext.txt`
- `papers/[name]/assets/fig_N.png`, `assets/table_N.png`
- 🔴 **`papers/[name]/config.json`** — 이 단계에서 **생성한다** (Stage 10 HTML 생성이 필수로 요구하는데 다른 단계가 안 만들므로 여기서 책임진다). 4개 키:
  - `metadata` — title / short_name / venue / year / authors / affiliation / source_pdf (PDF 첫 페이지에서). 키 이름은 `metadata` (정본; `_build.py`가 `config.get("metadata")` 우선. 일부 구 예제는 `meta` — 신규는 `metadata`로 통일)
  - `asset_layout` — `[[asset_id, paragraph_id, kind], ...]` 자산↔문단 매핑. paragraph_id는 Stage 2 산출 후 확정되므로, **Stage 2 완료 시점에 이 키를 채워 넣는다** (자산 등장 순서는 번호 순 — CLAUDE.md "자산 등장 순서" 정책)
  - `captions` — `{asset_id: 원문 캡션}` (detect_assets.py가 뽑은 캡션 텍스트)
  - `wide_assets` — 본문폭을 꽉 채우는(full-width) 자산 id 배열

**자산 크롭 — PDF 종류별:**
- **vector PDF** (현대 ML/CV 논문 대부분): **캡션 좌표 기반 bbox 검출**이 정본. 먼저 `python tools/detect_assets.py "<pdf>"`로 각 캡션의 `block_y`(멀티라인 블록 전체)·이미지/드로잉 bbox를 뽑은 뒤, 그 좌표를 anchor로 crop rect를 계산한다 — **좌표 하드코딩 금지**. `page.get_image_bbox()` 단독 사용은 composite figure(다이어그램·여러 sub-panel)에서 한 그림이 수십 개 image object로 분해돼 실패. 🔴 **"Figure=캡션 아래 / Table=캡션 위"는 관행일 뿐 자산 유형으로 단정하지 말 것** — 표 데이터가 위·캡션이 아래인 논문도 흔하다(FastVLM). 반드시 좌표로 캡션-본체 상대 위치를 자산별 판별. 정본 구현: `samples/free_example/_crop.py`. **시각 검증 의무** — 페이지 running header 누수(y_top ≥ 64), 멀티라인 캡션 잘림, 옆 단/표 아래 본문 누수를 PNG 직접 열어 확인. 자세히: `rules/parsing_rules.md` §4-A.
- **OCR'd 스캔본** (페이지 전체가 한 비트맵): **3-pass 자동 알고리즘** 사용 — `rules/parsing_rules.md` §4-A. 정본 도구 `tools/crop_assets.py` (이 배포본엔 OCR 예제 논문 미포함, 도구만 제공)
- per-paper 진입점은 `papers/[name]/_crop.py` 또는 `_recrop.py` 한 장. 일회성 헬퍼 정책

**참조 규칙:** `rules/parsing_rules.md` (§4-A — vector PDF 캡션 좌표 정본 + OCR'd 스캔본 3-pass)

---

## Stage 1 — Cleaning

**프롬프트:** `prompts/01_cleaning.md`

**목표:**
- 줄바꿈으로 끊긴 문장 복원
- 깨진 단어 복구 (예: `con￾tinuity` → `continuity`)
- 페이지 헤더/푸터 제거
- 수식·인용·각주는 보존

**산출물:** 정제된 plain text

**참조 규칙:** `rules/parsing_rules.md`, `rules/math_rules.md`

---

## Stage 2 — Structuring

**프롬프트:** `prompts/02_structuring.md`

**목표:** 섹션/문단/문장 단위로 본문을 구조화하고, 자산을 본문 문단에 매핑.

**산출물:** `papers/[name]/structured.json`

**핵심 스키마** (5세대 정본 = `rules/parsing_rules.md` §3-1-bis — 문단은 `sentences[]`, 캡션은 structured에 넣지 않고 `config.json#captions`):
```json
{
  "title": "Paper Title",
  "sections": [
    {
      "section_id": "s1",
      "title": "3 Method",
      "paragraphs": [
        {
          "paragraph_id": "p1",
          "section_subtitle": "3.1 Overview",
          "sentences": [
            { "sentence_id": "p1_s1", "text": "..." }
          ]
        }
      ]
    }
  ]
}
```

**식별자 규약:**
- `section_id`: `s1`, `s2`, ...
- `paragraph_id`: `p1`, `p2`, ...
- `sentence_id`: `{paragraph_id}_s{n}` (**Stage 2에서 부여**)

**출력 탭:** ① `tab-reading`

**참조 규칙:** `rules/parsing_rules.md`, `rules/math_rules.md`

### 🔴 완전성 자가 검증 (필수)

`structured.json` 발행 전 반드시 원문(`fulltext.txt`)과 다음 3가지를 대조한다 — 누락된 1단계가 모든 후속 단계를 깨뜨린다.

- **섹션 수**: 원문 `^[0-9]+\. ` 본문 섹션 수와 `structured.json#sections` 길이가 일치 (Abstract 포함하면 +1)
- **Subsection 수**: 원문 `^[0-9]+\.[0-9]+ ` 및 bold subsection 헤더(예: "Token Aggregation.")가 모두 별도 paragraph로 존재
- **문장 수**: 각 paragraph의 `sentences[]` 길이가 원문 같은 단락의 마침표 수와 ±1 이내

**빠뜨리기 쉬운 후보 (실제 누락 사례 있음)**:
- `2. Related Work` / `Background` 전체
- `3.x Theoretical Analysis` / `Complexity Analysis` 같은 수학적 sub-section
- `4.x Datasets` / `Implementation Details` setup 단락
- `5.x Computational Efficiency` / `Qualitative Visualization`
- bullet contribution list (도입 한 줄 + 각 bullet 각각 별도 sentence_id)
- 짧은 메타 문장 ("More cases are in Appendix H.", "Our code is available at …")

자세한 검증 스크립트·금지 패턴·정본 사례: `prompts/02_structuring.md` § 🔴 CRITICAL 완전성 규칙.

---

## Stage 3 — Translation

**프롬프트:** `prompts/03_translation.md`

**목표:** 모든 문장을 직역 + (선택) 의역 쌍으로 번역. 100% 보존.

**산출물:**
- `papers/[name]/translations/manual.json` — 1차 번역 (sentence_id 매핑)
- `papers/[name]/translations/refined.json` — (선택) 표현 다듬기 / 용어 통일
- `papers/[name]/translated.json` — (선택) 편의용 통합 매핑 파일

**핵심 스키마:**
```json
{ "sentence_id": "p3_s1", "original": "...", "translation": "...", "interpretation": "..." }
```

**출력 탭:** ① `tab-reading` (좌-원문 / 우-번역, `data-pair`로 호버 동기화)

**참조 규칙:** `rules/math_rules.md`, `rules/knowledge_rules.md`

---

## Stage 4 — Research Analysis

**프롬프트:** `prompts/04_research_analysis.md`

**목표:** 논문을 요약하지 말고, 저자의 사고 흐름(observation → idea → method → evidence)을 복원.

**산출물 — 두 갈래로 분기:**

1. **`tabs_data/dissection.json`** — **7+1 = 8 카드 구조**

   카드 8종 (정본 — 순서/클래스 변경 금지):
   - `diss-motivation` Research Motivation
   - `diss-observe` Author's Key Observations
   - `diss-compare` Difference from Prior Work
   - `diss-logic` Execution Logic
   - `diss-verify` Validation Logic
   - `diss-risk` Hidden Assumptions and Risks
   - `diss-extend` Research Expansion
   - **`diss-summary` 논문 총정리** — 마지막 1장. **9-row 정형 (2026-05-12 갱신)**: ① 한 줄 ② 이게 왜 문제인가(Problem) ③ 저자의 핵심 관찰(Observation) ④ 기존 방법은 왜 부족한가(Gap) ⑤ 어떻게 해결했나(Method) ⑥ 다른 논문과 무엇이 다른가(Novelty) ⑦ 효과 — 숫자(Results) ⑧ 한계와 의미(Limitations & Implication) ⑨ 30초 요약(For Beginners). 깊이 기준: \"<em>논문 안 읽은 사람도 이 카드 한 장만 보고 충분히 이해</em>\". 자세한 규약: `prompts/04_research_analysis.md`. 정본: `samples/free_example`.

   **summary 카드 한 장 overview 이미지 의무**: summary 카드 헤더 아래에 `assets/generated/dissection_overview.png` (가로 와이드 ~1536×1024, 5단 **문제→관찰→방법→차별→결과** 인포그래픽, 한글 라벨)를 `<figure class="diss-overview-figure">`로 동봉. codex ImageGen 6계명으로 생성. 마크업·CSS·빌더 헬퍼: `rules/component_rules.md` §14.

2. **`analysis.json#callouts`** — 문단 단위 강조 (`warn` / `key`)

**시각 보조 이미지** (필수+선택):
- **필수**: `dissection_overview.png` — summary 카드용 한 장 정리 (위)
- 선택: 흐름 도식·관찰 일러스트·메서드 인포그래픽 — `<figure class="concept-figure">`로 base64 인라인

**정식 호출 형식 (6계명 — 마지막 한 줄에 \"NO paper title at top, NO standalone header, NO author names\" 의무) + 검증된 명령 템플릿 + overview prompt 표준 구성: `rules/component_rules.md` §11 + `prompts/04_research_analysis.md`**.

**출력 탭:** ② `tab-dissection`, 콜아웃은 ① `tab-reading`에 인라인

**참조 규칙:** `rules/analysis_rules.md`, `rules/parsing_rules.md`

---

## Stage 5 — Coaching

**프롬프트:** `prompts/05_coaching.md`

**목표:** 논문이 명시하지 않은 가정·오해·비판·확장 가능성을 학습자에게 짚어준다.

**산출물:** `tabs_data/questions.json`

**4 카드 (정본):**
- `q-hidden` 가려진 가정
- `q-myth` 흔한 오해
- `q-critic` 비판적 질문
- `q-extend` 확장 아이디어

**시각 보조 이미지** (선택): Bash로 codex 직접 호출해 `assets/generated/questions_<purpose>.png` 생성 → `<figure class="concept-figure">` 정본 컴포넌트로 base64 인라인. ④ 탭 상단의 직관 다이어그램 2~3개가 카드 글머리보다 빠르게 이해를 잡아 준다. **정식 호출 형식 (5계명 + 검증된 명령 템플릿): `rules/component_rules.md` §11**. 자세한 의도: `prompts/05_coaching.md`.

**출력 탭:** ④ `tab-questions`

**참조 규칙:** `rules/coaching_rules.md`, `rules/analysis_rules.md`

---

## Stage 6 — Figure Interpretation

**프롬프트:** `prompts/06_figure_interpretation.md`

**목표:** 각 그림/표를 **세 층**으로 설명한다 — 세 층은 서로 다른 정보를 담고, **복제는 곧 모달 무용지물**.
- (a) 전문가 시선의 짧은 해석 (카드 본문)
- (b) 초보자용 친절한 풀이 (`<details>` 토글)
- (c) **자산별 학습 가이드 모달** (study-fab 클릭 시) — 정본 4-섹션 정형: 어디 볼지 / 결정적 숫자 / 저자 의도 / 학습 체크포인트

**산출물 — `analysis.json` 세 키:**
- `interpretations` (전문가, 카드 본문)
- `beginner_notes` (초보자, 토글)
- `study_modals` (학습 가이드 모달) — `{title, look, nums≥3, author, check≥2}` 형식. 마크업·CSS·JS 정본 = `rules/component_rules.md` §12.5/§12.6 (오른쪽 사이드 드로어). SGL은 historical reference로만.

> 🔴 **`analysis.json`은 Stage 4가 먼저 쓴다** (`callouts`·`quizzes`). Stage 6은 위 세 키를 **기존 파일에 병합(merge)** 해야 한다 — 통째로 덮어쓰면 Stage 4의 callouts/quizzes가 사라진다. (파일 읽기 → 키 추가 → 저장)

**렌더 위치:** ① `tab-reading`의 각 자산 카드 바로 아래 + study-fab 클릭 시 떠오르는 `.study-modal`

**자산 유형별 깊이 의무 (`study_modals`):**
- 다이어그램: 박스/화살표/N×/Encoder·Decoder 등 모든 시각 요소의 의미 풀이 (`s-look`)
- 그래프: 숫자 변화의 정치적·실용적 함의 (`s-num`)
- 표: 행/열 라벨·기호 의미 + 최우수 셀의 비교 우위 출처 (`s-num`)

**참조 규칙:** `rules/parsing_rules.md`, `rules/analysis_rules.md`, `rules/component_rules.md` §12 (study-modal 마크업·CSS·JS 정본)

---

## Stage 7 — Background Knowledge

**프롬프트:** `prompts/07_background_knowledge.md`

**목표:** 논문 이해에 필요한 전제 지식과 핵심 수식 정리.

**산출물:** `tabs_data/knowledge.json`

**3대 구성:**
- `primer` — 도입 다이어그램 + fund_cards
- `equations` — 핵심 수식 카드 3~5개
- `concept_cards` — 개념 카드 6~10개

**용어 표기:** `English Term (한글 설명)`
**개념 깊이:** 직관 → 구조 → 논문 연결 (3단계)

**시각 보조 이미지 (학습 효과의 핵심):**
배경지식 탭은 글만으로 채우지 않는다. 시스템 큰 그림·개념 메타포·단계별 일러스트는 **Claude가 Bash로 codex CLI를 직접 호출**해 ImageGen으로 생성한다 (별도 플러그인·MCP 자동화 없음, Bash 한 줄). 결과 PNG는 `papers/[name]/assets/generated/knowledge_<purpose>.png`로 저장 → `<figure class="concept-figure">` 정본 컴포넌트로 base64 인라인. 검수는 사후 (사용자가 결과 보고 재생성 요청). **정식 호출 형식 (5계명 — Bash·UTF-8 prompt.txt·ASCII 인자·stdin null·스타일 명시·출력 경로) 및 검증된 명령 템플릿: `rules/component_rules.md` §11**. 자세한 의도: `prompts/07_background_knowledge.md`.

**출력 탭:** ③ `tab-knowledge`

**참조 규칙:** `rules/knowledge_rules.md`, `rules/math_rules.md`, `rules/component_rules.md` §11 (생성 이미지)

---

## Stage 8 — Simulator Content Design ⏸ **on-demand only**

> **신규 논문 기본 빌드 범위에서 제외됨.** 이 단계는 사용자가 ⑤ 탭 콘텐츠 작성을 명시적으로 요청할 때만 실행한다 (CLAUDE.md "기본 빌드 범위" 정책 참조). 기본 빌드에서는 ⑤ 탭 본문이 `.section-empty` placeholder로 비워져 있다.

**프롬프트:** `prompts/09_simulator.md`

**목표:** 논문의 핵심 알고리즘을 학습용 시뮬레이터로 변환할 결정 사항 문서를 작성.

**산출물:** `papers/[name]/tabs_data/simulator_spec.md`

**3대 파트:**
1. Pseudocode — 30~80줄, 한국어 주석
2. Interactive Widget — 슬라이더 4~6개 + 시각화 + 비교 baseline
3. Code Comparison — prior method ↔ 본 논문 좌우 비교

**시각 보조 이미지** (선택): ⑤ 명시 요청 빌드일 때, Bash로 codex 직접 호출해 `assets/generated/simulator_<purpose>.png` 생성 → `<figure class="concept-figure">` 정본 컴포넌트로 base64 인라인. 도입 일러스트·의사코드 단계 시각화·코드 비교 개념도. 인터랙티브 위젯(canvas/슬라이더)은 JS, 정적 보조만 ImageGen. **정식 호출 형식 (5계명 + 검증된 명령 템플릿): `rules/component_rules.md` §11**. 자세한 의도: `prompts/09_simulator.md`.

**출력 탭:** ⑤ `tab-simulator`

**참조 규칙:** `rules/analysis_rules.md`, `rules/math_rules.md`, `rules/component_rules.md`

---

## Stage 9 — QA Content Design ⏸ **on-demand only**

> **신규 논문 기본 빌드 범위에서 제외됨.** 이 단계는 사용자가 ⑥ 탭 콘텐츠 작성을 명시적으로 요청할 때만 실행한다 (CLAUDE.md "기본 빌드 범위" 정책 참조). 기본 빌드에서는 ⑥ 탭 본문이 `.section-empty` placeholder로 비워져 있다.

**프롬프트:** `prompts/10_qa.md`

**목표:** 학습자가 논문을 다 읽은 뒤 자가 점검할 수 있는 Q&A 세트 설계.

**산출물:** `papers/[name]/tabs_data/qa.json`

**표준 카테고리 3종 (정본):**
- A — 기초 지식 / 지형도
- B — 메커니즘
- C — 실험 해석

각 카테고리당 2~3 질문, 전체 6~10. 질문당 2~5 블록 (`html` / `table` / `math` / `callout`).

**시각 보조 이미지** (선택): ⑥ 명시 요청 빌드일 때, Bash로 codex 직접 호출해 `assets/generated/qa_<qid>_<purpose>.png` 생성 → `<figure class="concept-figure">` 정본 컴포넌트로 base64 인라인. 카테고리 도입 일러스트·TL;DR 보조·표 해석 이미지. 질문당 0~1개. 인터랙티브 stepper는 JS. **정식 호출 형식 (5계명 + 검증된 명령 템플릿): `rules/component_rules.md` §11**. 자세한 의도: `prompts/10_qa.md`.

**출력 탭:** ⑥ `tab-qa`

**참조 규칙:** `rules/knowledge_rules.md`, `rules/analysis_rules.md`, `rules/math_rules.md`, `rules/component_rules.md`

---

## Stage 10 — HTML Generation (대화형)

**프롬프트:** `prompts/08_html_generation.md`

**목표:** Stage 1~7의 산출물을 입력으로 두고 Claude가 단일 6탭 HTML을 작성한다. 빌드 스크립트는 사용하지 않는다. ⑤ ⑥ 탭은 셸만 생성(콘텐츠 placeholder) — Stage 8/9는 on-demand.

**입력 일체:**
- `papers/[name]/structured.json`, `translated.json` (또는 `translations/`)
- `papers/[name]/config.json`, `analysis.json`
- `papers/[name]/tabs_data/{dissection,knowledge,questions}.json` (① ~ ④ 빌드용)
- `papers/[name]/tabs_data/{simulator_spec.md, qa.json}` — **선택 입력**. 사용자가 ⑤ ⑥을 명시 요청하지 않은 빌드에서는 사용 안 함.
- `papers/[name]/assets/`, `assets/generated/`
- 정본 레퍼런스: `samples/`의 3편 — SAFE(1세대), FrameFusion(2세대), SGL(3세대 — 인터랙션·시뮬레이터 3-Part·자산 모달)
- 디자인 컨벤션: `rules/component_rules.md`, `rules/implementation_rules.md`

**출력:** `papers/[name]/[ShortName].html` — 단일 HTML

**핵심 원칙:**
- 정본 두 파일의 마크업/CSS/탭 셸을 따른다 (디자인 토큰 정확히, 클래스명 임의 변경 금지)
- 6탭 구조 고정 (`tab-reading`, `tab-dissection`, `tab-knowledge`, `tab-questions`, `tab-simulator`, `tab-qa`)
- **모든 자산은 base64 인라인 의무** — `assets/`의 원본 figure/table + `assets/generated/`의 학습 보조 이미지 모두 `<img src="data:image/png;base64,...">`로 박는다. HTML 한 장만 다른 PC·모바일·USB로 옮겨도 그림이 그대로 떠야 한다. 외부 참조 잔존 = 빌드 불합격
- MathJax 3 (CDN), 탭 전환 시 `MathJax.typesetPromise()` 재호출
- 시뮬레이터 / QA 위젯 JS는 인라인 (외부 라이브러리 의존 없음)

**참조 규칙:** `rules/parsing_rules.md`, `rules/knowledge_rules.md`, `rules/math_rules.md`, `rules/component_rules.md`, `rules/implementation_rules.md`

---

## 산출물 매트릭스 (Stage ↔ 파일 ↔ 탭)

| Stage | 입력 | 산출 | 출력 탭 |
|---|---|---|---|
| 0 | PDF | raw text + `assets/*.png` | — |
| 1 | raw text | clean text | — |
| 2 | clean text | `structured.json` | ① reading |
| 3 | structured.json | `translations/*.json` (+ `translated.json`) | ① reading |
| 4 | structured.json + 도표 | `tabs_data/dissection.json` + `analysis.json#callouts` | ② dissection (① 콜아웃) |
| 5 | structured.json + Stage 4 | `tabs_data/questions.json` | ④ questions |
| 6 | assets + 본문 | `analysis.json#interpretations` + `#beginner_notes` | ① reading |
| 7 | structured.json + Stage 4 | `tabs_data/knowledge.json` | ③ knowledge |
| 8 ⏸ | structured.json + Stage 4 | `tabs_data/simulator_spec.md` | ⑤ simulator (on-demand만) |
| 9 ⏸ | structured.json + Stage 4/7 | `tabs_data/qa.json` | ⑥ qa (on-demand만) |
| 10 | Stage 1~7 산출 (+ 8/9는 요청 시) | 단일 HTML (Claude 작성) | 전체 — ⑤⑥은 셸만 placeholder |

---

## Definition of Done

`papers/[name]/[ShortName].html`이 다음을 모두 만족할 때 완료:

- 6개 탭 버튼이 보이고 클릭 시 패널만 활성화
- ① 좌(원문) ↔ 우(번역) `data-pair` 호버 동기화 작동
- 모든 figure/table이 의도한 문단 근처에 배치 (`asset_layout` 매핑 확인)
- **각 자산 PNG가 본체 + 캡션을 모두 포함하고 누수 0건** — 페이지 헤더·다음 섹션 헤더·아래 본문 텍스트가 섞이지 않고, 캡션이 잘리지 않음 (PNG 직접 열어 시각 검증)
- **자산 등장 순서가 원본 번호 순서대로** — ① 탭에서 fig_1→fig_2→…→fig_N, table_1→…→table_N 점프 없음 (Appendix figure는 본문 끝에 부착, `parsing_rules.md` §3-2-bis 자가 검증 스크립트로 확인)
- **structured.json이 원문 본문(Abstract → Conclusion)의 모든 섹션/subsection을 누락 없이 포함** (Related Work, Theoretical Analysis, Datasets/Implementation Details 등 — Stage 2 완전성 자가 검증 통과)
- **structured ↔ translations sentence_id 1:1 매칭** (missing 0 / extra 0 / 빈 값 0 / 중복 0 — Python 검증 스크립트로 확인)
- 번역 누락 0건 (회색 placeholder / `—` 미발견)
- 콜아웃/퀴즈/해석/초보자 노트가 의도한 위치에 표시
- **모든 figure/table에 `.study-fab` 버튼 + 4-섹션 정형(s-look·s-num·s-author·s-check) 학습 가이드 모달** (interpretation/beginner-note의 단순 복제 ✗ — 한 단계 더 깊은 분해. §12 정본 SGL 패턴)
- **② Dissection의 `diss-summary` 카드가 9-row 정형** (한 줄 / 문제 / 관찰 / Gap / 방법 / 차별 / 효과 / 한계 / 30초 요약) + **`dissection_overview.png` 한 장 인포그래픽이 헤더 아래·rows 위에 base64 인라인** (`rules/component_rules.md` §14, 정본 = `samples/free_example`)
- **`.diss-tag` pill이 본문 한 줄 높이의 작은 알약 모양** — grid cell의 세로 stretch로 큰 타원·이상한 모양이 안 보임. 5개 속성 필수: `align-self:start` / `justify-self:start` / `width:max-content` / `white-space:nowrap` / `line-height:1.4` (`rules/component_rules.md` §15)
- **② Dissection 카드가 단일 컬럼으로 수직 적층 + 각 row가 `[태그 pill, 한 줄]` → `[본문, 그 아래]` 상하 적층** — `.diss-grid` = `grid-template-columns:1fr` / `.diss-row` = `display:flex; flex-direction:column` / `dd.diss-body { margin-left:0 }` 모두 적용 (`rules/component_rules.md` §16, 정본 = `samples/free_example`, 2026-05-13 갱신)
- **모든 콘텐츠 이미지(① 자산·② summary overview·③ 학습 보조)에 비율 유지 lightbox 동작** — `cursor:zoom-in` hover, 클릭 시 어두운 배경 모달에 비율 유지하며 확대, 휠/+/− 줌·드래그 pan·더블클릭 토글·ESC 닫기. `study-fab` 클릭은 `e.stopPropagation() + e.preventDefault()`로 lightbox 트리거 차단 (`rules/component_rules.md` §13)
- ② ③ ④ 탭 콘텐츠가 비어 있지 않음
- ⑤ ⑥ 탭은 셸만 — `tab-intro` + `.section-empty` placeholder ("이 탭은 별도 요청 시 작성됩니다") 표시
- MathJax가 ① 본문 + ③ 수식 카드를 렌더 (탭 전환 후 재렌더 포함)
- 모바일(< 640px)에서 탭 줄바꿈, 표 overflow-scroll 정상
- **모든 `<img>` 태그가 `data:image/png;base64,...` 형태** — 외부 참조(`src="assets/..."`, `src="./..."`, `src="http..."`) 잔존 0건
- **codex로 생성한 학습 보조 이미지에 논문 제목·헤더·저자명이 박혀 있지 않음** — 6번째 계명(`rules/component_rules.md` §11.2) 통과. 콘텐츠와 영어 섹션 라벨만

(⑤ 시뮬레이터 슬라이더 / ⑥ Q&A 콘텐츠 작동은 사용자가 별도 요청 시에만 추가 검증 항목으로 활성화)

---

## 참고 문서

- `CLAUDE.md` — 프로젝트 개요, 표준 템플릿, 디자인 토큰, 디렉토리 규약
- `prompts/01~10_*.md` — 각 단계별 프롬프트 정본
- `rules/` — 파싱 / 분석 / 코칭 / 지식 / 수식 / 컴포넌트 / 구현 규약
- `samples/` — 정본 HTML (수정 금지) — SAFE(1세대), FrameFusion(2세대), SGL(3세대). README + design/ 자산만 함께 보관 (pre-SAFE 시기 개인 학습 자료는 `_archive/personal_study/`로 분리됨)
