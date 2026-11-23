# Workflow — 단계별 대화형 작업 흐름 (Stage 0~13)

> 한 편의 논문 PDF를 **8탭 학습용 HTML**(v4 대시보드 디자인 — `rules/design_v4_dashboard.md`, Paper Study 탭 포함)로 변환하는 단계별 흐름.
> Claude와 대화하며 한 단계씩 콘텐츠를 정제하고(생성적 단계), 본문 구조화·자산 크롭·조립은 정본 도구로 고정한다(결정적 단계). Stage 10에서 `_build.py` 조립 → `tools/restyle_dash_v4.py` 변환으로 HTML 한 장을 만들고, Stage 13에서 그 HTML 앞에 보는 소개 영상(`{ShortName}_video.mp4`)을 만든다.
>
> 정본 레퍼런스: `samples/cares/` — v4 8탭 + Paper Study 워크드 예제(데이터 + `_build.py` + `CARES_output.html`). 빌더 복사 기준은 `templates/paper_base/`. 1~3세대(SAFE·FrameFusion·SGL) 인터랙션은 CARES가 흡수 — 개념 히스토리는 `samples/README.md`
>
> 표준 템플릿/디렉토리 규약: `CLAUDE.md` · 정책 상세: `rules/project_policies.md` · 디자인 토큰: `rules/design_v4_dashboard.md`
>
> **빌드를 시작하기 전에 `rules/build_lessons.md`의 "빌드 전 점검"을 읽는다.**
>
> 이 킷은 특정 분야(AI/ML)에 묶이지 않는다. 자연과학·공학·AI/CS·의학·인문사회 어느 분야의 논문이든 같은 절차로 만든다. 분야에 따라 달라지는 것(용어 표기 관행·증거의 종류·대안 설명 축·배경지식 단위·학회/저널 메타)은 `config.json#domain`(정본: `rules/domain_profile.md`)에서 읽어 채운다. 문서 안의 ML 논문 예시는 **예시일 뿐** 규칙이 아니다.

### Stage 번호와 프롬프트 파일 번호

Stage 번호는 실행 단계, `prompts/NN_*.md`의 NN은 파일 번호다. 둘은 Stage 1~7·11·12·13에서만 같다.

| Stage | 내용 | 프롬프트·규칙 | 기본 빌드 |
|---|---|---|---|
| 0 | PDF Parsing · 자산 크롭 | (프롬프트 없음) `rules/parsing_rules.md` · `tools/autocrop_assets.py` | ✅ |
| 1 | Cleaning + `config.json#domain` | `prompts/01_cleaning.md` | ✅ |
| 2 | Structuring | `prompts/02_structuring.md` · `tools/structure_paper.py` | ✅ |
| 3 | Translation | `prompts/03_translation.md` | ✅ |
| 4 | Research Analysis | `prompts/04_research_analysis.md` | ✅ |
| 5 | Coaching | `prompts/05_coaching.md` | ✅ |
| 6 | Figure Interpretation | `prompts/06_figure_interpretation.md` | ✅ |
| 7 | Background Knowledge | `prompts/07_background_knowledge.md` | ✅ |
| 8 | Simulator Design | `prompts/09_simulator.md` | ⏸ 요청 시 |
| 9 | QA Design | `prompts/10_qa.md` | ⏸ 요청 시 (메모 Q&A는 브릿지 온디맨드) |
| 11 | Paper Study (Stage 7 다음, 10 이전에 실행) | `prompts/11_paper_study.md` | ✅ |
| 10 | HTML Generation (조립·주입·검사) | `prompts/08_html_generation.md` | ✅ |
| 12 | 논문 정립 & 연구 멘토 (빌드 밖) | `prompts/12_research_mentor.md` | — |
| 13 | 논문 소개 영상 (HTML 다음) | `prompts/13_video.md` · `rules/video_rules.md` · `tools/video/make_video.py` | ✅ (사용자가 빼라고 하면 생략) |

기본 빌드 = Stage 0~7 → 11 → 10 → 13. Stage 8·9는 사용자가 요청할 때만, Stage 12는 빌드가 끝난 뒤 별도 세션이다.

---

## Stage 0 — PDF Parsing

**도구:** `tools/autocrop_assets.py`(vector PDF 자산 크롭 정본) · `tools/crop_assets.py`(OCR 스캔본) · PyMuPDF(fitz)

**폴더 명명 규약:** 신규 논문 폴더는 **`N. shortname`** 형식 (예: `5. flash_attn`). 자세한 규칙은 `CLAUDE.md` "폴더 명명 규약" 참조. 이 문서에서 `papers/[name]/`은 `papers/N. shortname/`을 가리킨다.

**목표:**
- 텍스트 위치 정보(블록 좌표)를 보존해 다단(2-column) 순서를 정확히 복원
- Figure / Table을 PNG로 크롭

**산출물:**
- 정제된 plain text 또는 페이지별 블록 텍스트
- `papers/[name]/assets/fig_N.png`, `assets/table_N.png`

**자산 크롭 — PDF 종류별:**
- **vector PDF** (LaTeX 등 벡터 조판 논문 대부분): **`tools/autocrop_assets.py`로 자동 크롭** — 좌표를 손으로 잡지 않는다.
  ```bash
  python tools/autocrop_assets.py "rawpaper/<논문>.pdf" "papers/N. name/assets"
  python tools/autocrop_assets.py --verify "papers/N. name/assets"   # 여백(잘림) 자동 점검
  ```
  도구는 캡션 좌표를 anchor로 column band(full/left/right)를 판별하고, 캡션 위/아래 어느 쪽에 그래픽이 있는지로 crop 방향을 정한 뒤(Figure 아래·Table 위는 관행일 뿐 — 자산마다 다르다), 벡터 드로잉·raster·표 ruling line으로 실제 경계를 잡고 픽셀 여백 패스로 마무리한다. `page.get_image_bbox()` 단독 사용은 composite figure에서 한 그림이 수십 개 image object로 분해돼 실패한다. 적용 사례 `samples/cares/_crop.py`(autocrop 호출 + 사용 자산 선별). **시각 검증 의무** — 페이지 running header 누수, 캡션 잘림, sub-panel 누락, 표 아래 본문 누수를 PNG 직접 열어 확인하고, 어긋나는 자산만 수동 보정. 알고리즘: `rules/parsing_rules.md` §4-A.
- **OCR'd 스캔본** (페이지 전체가 한 비트맵): **3-pass 자동 알고리즘** 사용 — `rules/parsing_rules.md` §4-A. 정본 도구 `tools/crop_assets.py`(사용법은 도구 docstring; 정본 사례 `papers/4. perceptron/_recrop.py` 는 모체 사례 — 배포본 미포함)
- per-paper 진입점은 `papers/[name]/_crop.py` 또는 `_recrop.py` 한 장. 일회성 헬퍼 정책

**참조 규칙:** `rules/parsing_rules.md` (§4-A — vector PDF 자동 크롭 정본 + OCR'd 스캔본 3-pass)

---

## Stage 1 — Cleaning

**프롬프트:** `prompts/01_cleaning.md`

**목표:**
- 줄바꿈으로 끊긴 문장 복원
- 깨진 단어 복구 (예: `con￾tinuity` → `continuity`)
- 페이지 헤더/푸터 제거
- 수식·인용·각주는 보존
- **분야 프로파일**: `config.json#domain` 초안 작성(제목·초록·venue·키워드 기반) → 사용자 확인 1회. 정본 `rules/domain_profile.md`. 이후 모든 Stage 가 이 블록을 읽는다.
- **topbar 메타**: 같은 단계에서 `config.json#meta`(topbar 필드)의 초안을 쓰고(PDF 제목·저자·소속·venue·연도·코드 URL), Stage 10 조립 전에 확정한다. 필드 목록·형식은 `rules/design_v4_dashboard.md` §6 2단계(topbar 필드). 코드 URL이 없으면 `meta.code` 키를 뺀다.

**산출물:** 정제된 plain text + `config.json#domain`(사용자 확인 완료) + `config.json#meta`(초안)

**참조 규칙:** `rules/parsing_rules.md`, `rules/math_rules.md`, `rules/domain_profile.md`

---

## Stage 2 — Structuring

**프롬프트:** `prompts/02_structuring.md`

**목표:** 섹션/문단/문장 단위로 본문을 구조화하고, 자산을 본문 문단에 매핑.

**도구 (필수 — 결정적 단계):**
```bash
python tools/structure_paper.py "rawpaper/<논문>.pdf" "papers/N. name/structured.json"
```
본문(Abstract → Conclusion) 전체를 컬럼 순서로 1:1 캡처한다(de-hyphenate · 문장 분할 · figure·표 내부 텍스트 제외 · 컬럼/페이지 경계에서 끊긴 문단 잇기 · References/Appendix에서 중단). 같은 폴더에 대조용 원문 `fulltext.txt`도 쓴다(이미 있으면 덮어쓰지 않는다 — 아래 완전성 자가 검증과 Stage 11 `captions_en`의 원천). 손으로 본문 일부만 담거나 문장을 합치지 않는다. 출력은 완전한 1차본이므로 드문 분할 오류만 손으로 고친다. 부록을 인용하면(`rules/build_lessons.md` "시작할 때") 부록 섹션을 같은 스키마로 이어 붙인다. 자산-문단 매핑은 `config.json#asset_layout`에 쓴다.

**산출물:** `papers/[name]/structured.json`

**핵심 스키마 (`rules/parsing_rules.md` §3-1-bis):**
```json
{
  "paper_id": "...", "title": "...", "venue": "...",
  "sections": [
    {
      "section_id": "s_intro",
      "title": "1 Introduction",
      "paragraphs": [
        { "paragraph_id": "p_intro_1", "section_subtitle": "(선택)",
          "sentences": [ { "sentence_id": "p_intro_1_s1", "text": "..." } ] }
      ]
    }
  ]
}
```

**식별자 규약:**
- `section_id`·`paragraph_id`: 섹션·문단마다 고유 (structure_paper.py가 부여)
- `sentence_id`: `{paragraph_id}_s{n}` — Stage 2에서 부여되고 Stage 3 번역이 같은 id 전체를 1:1로 채운다. 근거 칩·형광펜이 붙은 뒤에는 바꾸지 않는다.

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
   - **`diss-summary` 논문 총정리** — 마지막 1장. **9-row 정형 (2026-05-12 갱신)**: ① 한 줄 ② 이게 왜 문제인가(Problem) ③ 저자의 핵심 관찰(Observation) ④ 기존 방법은 왜 부족한가(Gap) ⑤ 어떻게 해결했나(Method) ⑥ 다른 논문과 무엇이 다른가(Novelty) ⑦ 효과 - 숫자(Results) ⑧ 한계와 의미(Limitations & Implication) ⑨ 30초 요약(For Beginners). 깊이 기준: \"<em>논문 안 읽은 사람도 이 카드 한 장만 보고 충분히 이해</em>\". 자세한 규약: `prompts/04_research_analysis.md`. 정본: `samples/cares/_build.py` + `CARES_output.html`.

   **summary 카드 한 장 overview 이미지 의무**: summary 카드 헤더 아래에 `assets/generated/dissection_overview.png` (1536×864, 5단 PROBLEM→OBSERVATION→METHOD→NOVELTY→RESULTS 인포그래픽)를 `<figure class="diss-overview-figure">`로 동봉. 마크업·CSS·빌더 헬퍼: `rules/component_rules.md` §14.

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

**목표:** 논문이 명시하지 않은 가정·설계 근거·비판·확장 가능성을 학습자에게 짚어준다.

**산출물:** `tabs_data/questions.json` = `{diagrams:[{image_path, title, caption}], cards:[{cls, title, lead, rows:[{q, a}]}]}` (`q` 평문, `a` HTML — 정본 `samples/cares/tabs_data/questions.json`)

**4 카드 (정본 — 순서·`cls` 변경 금지, `rules/coaching_rules.md`):**
- `coach-assume` Hidden Assumption — 논문이 명시하지 않고 전제하는 것
- `coach-design` Design Choices — 왜 이렇게 설계했나, 대안과의 비교
- `coach-critique` Critical Questions — 숫자를 곧이곧대로 믿기 전에 따져볼 것
- `coach-extend` Extensions & Open Directions — 여기서 뻗어나갈 다음 연구

**시각 보조 이미지** (선택): Bash로 codex 직접 호출해 `assets/generated/questions_<purpose>.png` 생성 → `<figure class="concept-figure">` 정본 컴포넌트로 base64 인라인. ④ 탭 상단의 직관 다이어그램 2~3개가 카드 글머리보다 빠르게 이해를 잡아 준다. **호출 형식(6계명)·명령 템플릿: `rules/component_rules.md` §11.2~11.3 / 🔴 prompt.txt 본문 작성 정본(밀도·패널 명세·검수): 같은 문서 §11.8**. 자세한 의도: `prompts/05_coaching.md`.

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
- `study_modals` (학습 가이드 모달) — `{title, look, nums≥3, author, check≥2}` 형식. 정본 = `samples/cares/CARES_output.html`의 study-drawer.

**렌더 위치:** ① `tab-reading`의 각 자산 카드 바로 아래 + study-fab 클릭 시 오른쪽에서 열리는 학습 가이드 드로어(`.study-drawer`)

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
배경지식 탭은 글만으로 채우지 않는다. 시스템 큰 그림·개념 메타포·단계별 일러스트는 **Claude가 Bash로 codex CLI를 직접 호출**해 ImageGen으로 생성한다 (별도 플러그인·MCP 자동화 없음, Bash 한 줄). 결과 PNG는 `papers/[name]/assets/generated/knowledge_<purpose>.png`로 저장 → `<figure class="concept-figure">` 정본 컴포넌트로 base64 인라인. 검수는 2단 — 생성 직후 Claude가 PNG를 Read로 열어 §11.8.6 체크리스트 확인(미달 시 프롬프트 수정 후 재생성), 사용자 검수는 사후. **호출 형식(6계명) 및 검증된 명령 템플릿: `rules/component_rules.md` §11.2~11.3, 🔴 prompt.txt 본문 작성 정본: 같은 문서 §11.8**. 자세한 의도: `prompts/07_background_knowledge.md`.

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

**시각 보조 이미지** (선택): ⑤ 명시 요청 빌드일 때, Bash로 codex 직접 호출해 `assets/generated/simulator_<purpose>.png` 생성 → `<figure class="concept-figure">` 정본 컴포넌트로 base64 인라인. 도입 일러스트·의사코드 단계 시각화·코드 비교 개념도. 인터랙티브 위젯(canvas/슬라이더)은 JS, 정적 보조만 ImageGen. **호출 형식(6계명)·명령 템플릿: `rules/component_rules.md` §11.2~11.3 / 🔴 prompt.txt 본문 작성 정본(밀도·패널 명세·검수): 같은 문서 §11.8**. 자세한 의도: `prompts/09_simulator.md`.

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

**시각 보조 이미지** (선택): ⑥ 명시 요청 빌드일 때, Bash로 codex 직접 호출해 `assets/generated/qa_<qid>_<purpose>.png` 생성 → `<figure class="concept-figure">` 정본 컴포넌트로 base64 인라인. 카테고리 도입 일러스트·요약 보조·표 해석 이미지. 질문당 0~1개. 인터랙티브 stepper는 JS. **호출 형식(6계명)·명령 템플릿: `rules/component_rules.md` §11.2~11.3 / 🔴 prompt.txt 본문 작성 정본(밀도·패널 명세·검수): 같은 문서 §11.8**. 자세한 의도: `prompts/10_qa.md`.

**출력 탭:** ⑥ `tab-qa`

**참조 규칙:** `rules/knowledge_rules.md`, `rules/analysis_rules.md`, `rules/math_rules.md`, `rules/component_rules.md`

---

## Stage 11 — Paper Study Content Design ✅ 기본 빌드 포함

> 번호는 프롬프트 파일 기준(`prompts/11_paper_study.md`) — **실행 순서는 Stage 7 다음, Stage 10 이전.**
> ⑤⑥과 달리 **기본 빌드 범위에 포함**된다 (①′ `tab-study`는 풀 빌드). **study.json은 필수 산출물**이다 — 없을 때 빌더가 그리는 자동 셸은 개발 중 "작성 전" 임시 상태일 뿐 산출물이 아니며, `check_paper_structure.py`가 FAIL로 잡는다 (Study 검토 버튼도 study.json을 기준 분석으로 쓴다).

**프롬프트:** `prompts/11_paper_study.md`

**목표:** 3-Phase 비판적 읽기 워크북(Aerial View → Interrogation → Verdict)의 콘텐츠 설계.
사용자가 직접 쓰는 서술칸의 대조 상대가 될 Claude 분석 + 근거 sentence_id + 단락 읽기(read) 배정.

**산출물:**
- `papers/[name]/tabs_data/study.json` — 7-Step 콘텐츠 (RQ/Gap/방법론 평가/데이터-only 결론/저자 주장 판정/대안 가설 + read 패널 배정)
- `papers/[name]/config.json#captions_en` — 도표 뷰어용 원문 캡션 (fulltext에서 수동 정제)
- `papers/[name]/study/` 폴더 생성 (노트 내보내기 저장소, `.gitkeep`)

**핵심 규칙 (정본 = prompts/11):**
- Step 5 Claude 분석은 **Discussion 인용 금지** (데이터-only — 사용자와 같은 조건의 비교 상대)
- 방법론 평가는 강점·약점 균형 (약점 최소 3개, 특정 표/절/수치 지목)
- 저자 주장은 support / partial / beyond 판정
- 모든 evidence·read ref가 structured.json/asset_layout에 실존하는지 전수 검증
- 부수 설명 문구 금지 — 지시는 read 패널·placeholder가 대신한다

**출력 탭:** ①′ `tab-study`

**참조 규칙:** `rules/design_v4_dashboard.md` §3-bis, `rules/component_rules.md` §17

---

## Stage 10 — HTML Generation (대화형)

**프롬프트:** `prompts/08_html_generation.md`

**목표:** Stage 1~7 + 11의 산출물을 입력으로 두고 단일 8탭 HTML을 조립한다 (v4: `_build.py` 조립 → `tools/restyle_dash_v4.py` 변환 2단 — 복사 기준 = `templates/paper_base/_build.py`(논문별로 `TODO_PAPER` 표시만 채움), 워크드 예제 = `samples/cares/_build.py`). ⑤ ⑥ 탭은 셸만 생성(콘텐츠 placeholder) — Stage 8/9는 on-demand.

**입력 일체:**
- `papers/[name]/structured.json`, `translated.json` (또는 `translations/`)
- `papers/[name]/config.json` (meta **확정** — Stage 1 초안을 조립 전에 확정 + captions + **captions_en**), `analysis.json`
- `papers/[name]/tabs_data/{dissection,knowledge,questions}.json` (① ~ ④ 빌드용)
- `papers/[name]/tabs_data/study.json` (①′ Paper Study — **필수**. 없으면 빌더가 자동 셸을 그리지만 그것은 개발 중 "작성 전" 상태일 뿐 산출물이 아니다)
- `papers/[name]/tabs_data/{simulator_spec.md, qa.json}` — **선택 입력**. 사용자가 ⑤ ⑥을 명시 요청하지 않은 빌드에서는 사용 안 함.
- `papers/[name]/assets/`, `assets/generated/`
- 정본 레퍼런스: `samples/cares/_build.py` + `samples/cares/CARES_output.html` — 셸·토큰·문장 페어링·study-drawer·lightbox·hotspot·ref-link·Paper Study 모두 포함 (1~3세대 인터랙션 흡수)
- 디자인 컨벤션: `rules/component_rules.md`, `rules/implementation_rules.md`

**출력:** `papers/[name]/[ShortName]_output.html` — 단일 HTML

**핵심 원칙:**
- 기준 빌더(`templates/paper_base/_build.py`)와 정본(`samples/cares/_build.py` + `CARES_output.html`)의 마크업/CSS/탭 셸을 따른다 (디자인 토큰 정확히, 클래스명 임의 변경 금지)
- 8탭 구조 고정 (`tab-reading`, `tab-study`, `tab-dissection`, `tab-knowledge`, `tab-math`, `tab-questions`, `tab-simulator`, `tab-qa`) — 라벨은 숫자 없이 (v4)
- **모든 자산은 base64 인라인 의무** — `assets/`의 원본 figure/table + `assets/generated/`의 학습 보조 이미지 모두 `<img src="data:image/png;base64,...">`로 박는다. HTML 한 장만 다른 PC·모바일·USB로 옮겨도 그림이 그대로 떠야 한다. 외부 참조 잔존 = 빌드 불합격
- MathJax 3 (CDN), 탭 전환 시 `MathJax.typesetPromise()` 재호출
- 시뮬레이터 / QA 위젯 JS는 인라인 (외부 라이브러리 의존 없음)

**조립 → 주입 → 검사 체인 (순서 고정):**
0. `python "papers/N. name/_build.py"` — v3 중간 산물 `{ShortName}_output.html` 조립
1. `python tools/restyle_dash_v4.py "papers/N. name"` — v3 중간 산물 → v4 대시보드 (수식 카드가 있는데 `<section class="eq-panel">`이 없으면 FAIL로 멈춘다)
2. `python tools/memo_layer_fix.py "papers/N. name"` — 메모 상시 접근 레이어(z 2400 + 가로 자리 배분). 빌더에 summary 이미지 분기가 없는 구세대 산출물이면 `python tools/overview_inject.py "papers/N. name"`도 다시 돌린다
3. `python tools/qa_button_inject.py "papers/N. name"` · `python tools/study_review_inject.py "papers/N. name"` · `python tools/reader_asset_chip.py "papers/N. name"`(플로팅 리더 안 도표 진입 칩 - 셋 다 additive·idempotent·업데이터, `--check` 로 주입 여부만 확인 가능)
4. 검사: `check_html_escape.py` → `grep '&lt;b&gt;'`·`grep '&amp;lt;'`(평문/HTML 필드 누출, 둘 다 0건) → `check_study_refs.py` → `tone_lint.py` → `check_memo_layer.py` → `check_paper_structure.py`(폴더·8탭·자산 순서·summary 9행·수식 위치·주입 여부·TODO_PAPER)

재빌드 없이 산출물과 원천 JSON을 함께 고칠 때(빌드 후 교정이 산출물에만 있는 구세대 논문 등): `python tools/html_patch.py "papers/N. name" text patches.json --dry-run` / `asset fig_N` (대상에 없으면 아무것도 쓰지 않고 실패).

체인 밖의 저장소 전체 교정 패스(빌더 `_build.py` 와 산출물을 **함께** 고치므로 새 논문에는 이미 반영돼 있다 - 회귀 의심 시 `--dry-run`/`--check` 로만 확인): `tools/strip_left_bars.py`(좌측 색 띠 제거) → `tools/normalize_left_radius.py`(그 잔재인 좌측만 0 인 border-radius 정규화) · `tools/audit_fix_pass1.py`(감사 결함 8종 - 형광펜 특이도·`.col` 테두리·HTML 필드 esc 제거·`.eq-card{min-width:0}`·라이트박스 z 2000·죽은 `closeModal` 분기·hotspot 호버·`.fund-*`/`.knw-*` 미정의 보완) · `tools/fix_hl_and_dash.py`(핫스팟 막대 제거·형광펜 우선·콘텐츠 em-dash → 하이픈, `prompts/03_translation.md` 문장부호 규칙). 이 도구들의 `--all`은 `papers/*`와 `samples/*`를 함께 돈다.

**참조 규칙:** `rules/parsing_rules.md`, `rules/knowledge_rules.md`, `rules/math_rules.md`, `rules/component_rules.md`, `rules/implementation_rules.md`

---

## Stage 12 - 논문 정립 & 연구 멘토 (빌드 밖 · 별도 세션)

**프롬프트:** `prompts/12_research_mentor.md`

**목표:** 빌드가 끝난 논문을 새 세션에서 다시 정립하는 프롬프트. 멘토 페르소나·가설·차별성 축은 사용자 연구 프로파일 `research_profile.json`(킷 루트 · 템플릿 `research_profile.example.json` · 없으면 첫 세션에서 함께 작성 — `rules/domain_profile.md` §3)에서 읽는다. 빌드 산출물을 만들지 않는다. 대상 논문 파일(`structured.json`·`tabs_data/*.json`·`assets/`)을 직접 읽은 뒤 A 논문 정립(한 줄 정의·문제·핵심 주장·분모를 명시한 결정적 수치 3개·증명하지 못한 것) → B 관찰 요소 → C 방법론 해부(텐서 흐름·개입 지점·학습 신호·비용 구조·제어 손잡이) → D 코퍼스 내 인접 논문 3~5편 차별성 매트릭스 → E 사용자 가설(`research_profile.json#hypotheses`) 좌표 배치(관련될 때만, 근거/반례 판정) → F 회수·판단 질문 3~5개 순으로 출력하고 답을 기다린다. 논문 지정 없이 아이디어만 말하면 선행 연구로 판정하지 않는 아이데이션 모드로 동작한다. 산출물은 선택적으로 `research/qa_log.json`(`research_profile.json#qa_log`) 에 append 한다.

---

## Stage 13 — 논문 소개 영상 ✅ 기본 빌드 포함

**프롬프트:** `prompts/13_video.md` · **규칙:** `rules/video_rules.md` · **도구:** `tools/video/make_video.py` · **뼈대:** `templates/paper_base/video/` · **클립 엔진:** motion-broll 스킬(배포본 `skills/motion-broll/` → 설치 `.claude/skills/motion-broll/`). 완성 영상 예제는 배포본에 없다(모체 사례 — 배포본 미포함).

**목표:** 학습 HTML을 열기 전에 보는 10~15분 연구 다큐멘터리 영상 한 편. 학부 3~4학년 눈높이로 저자의 고민 → 관찰 → 실험 → 성과 → 남은 문제를 이야기로 보여 주고, 마지막에 HTML에서 이어 볼 곳을 짚는다. 분야는 가리지 않는다(사례·증거는 `config.json#domain`의 그 분야 것).

**입력:** Stage 2·3·4·6·7·11 산출물(`structured.json`, `translations/manual.json`, `tabs_data/*.json`, `analysis.json#study_modals`, `assets/`), 원본 PDF(`rawpaper/` — `config.json#meta.source_pdf`).

**순서** (`python tools/video/make_video.py "papers/N. name" <단계>`):
0. (새 컴퓨터) `python tools/video/make_video.py - doctor` — motion-broll 스킬이 없으면 `skills/motion-broll/` → `.claude/skills/motion-broll/` 복사 설치, 빠진 도구와 채울 명령 표시. 나머지 도구는 각 단계가 처음 실행 때 스스로 설치한다(TTS 환경 수 GB)
1. `new` → `video/` 뼈대(기획안.md · spec.py · scenes.js · clipspec.py · CREDITS.md · assets/sources.json)
2. 원고 `video/기획안.md` 작성(대화) → `check-script` FAIL 0 → 사실 검토(원고만 받은 서브에이전트가 표 PNG·원문과 대조). 원고 승인을 기다리지 않고 끝까지 진행한다. 입력 이미지가 나오는 컷은 논문 자료 → codex 예시 사진 → 샘플 데이터셋 순서로 정하고(`video/assets/` + `sources.json`, 사진 프롬프트는 `check-assets` 통과 후 codex 호출)
3. `tts` → `animatic`(브라우저로 `video/기획안.html` 재생해 흐름 확인)
4. `words` → `briefs` → 클립 조각 `video/clips/NN-name.html` 작성(서브에이전트 가능, 렌더 금지) → `clips-build` → `beats` 육안 점검 → `check-assets` FAIL 0 → `clips-render`(반복)
5. `base-render`(반복) → `final` → `check` FAIL 0 → `gapcheck` 시트 육안 점검

**출력:** `papers/N. name/{ShortName}_video.mp4` (HTML과 같은 자리), `video/기획안.html`(애니매틱). 생성물 `video/work/`·`*_video.mp4`는 git 제외.

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
| 9 ⏸ | structured.json + Stage 4/7 + **study/ 최신 노트의 memo** | `tabs_data/qa.json` | ⑥ qa (on-demand만) |
| 11 | structured.json + fulltext + analysis | `tabs_data/study.json` + `config#captions_en` + `study/` 폴더 | ①′ study |
| 10 | Stage 1~7·11 산출 (+ 8/9는 요청 시) | 단일 HTML (Claude 작성) | 전체 — ⑤⑥은 셸만 placeholder |
| 13 | Stage 2~7·11 산출 + PDF | `video/` 입력 + `{ShortName}_video.mp4` | — (HTML 전에 보는 영상) |

---

## Definition of Done

`papers/[name]/[ShortName]_output.html`이 다음을 모두 만족할 때 완료:

- 8개 탭 버튼이 보이고 클릭·해시 라우팅(뒤로/앞으로 버튼 포함)으로 패널 활성화
- ① 좌(원문) ↔ 우(번역) `data-pair` 호버 동기화 작동
- 모든 figure/table이 의도한 문단 근처에 배치 (`asset_layout` 매핑 확인)
- **각 자산 PNG가 본체 + 캡션을 모두 포함하고 누수 0건** — 페이지 헤더·다음 섹션 헤더·아래 본문 텍스트가 섞이지 않고, 캡션이 잘리지 않음 (PNG 직접 열어 시각 검증)
- **자산 등장 순서가 원본 번호 순서대로** — ① 탭에서 fig_1→fig_2→…→fig_N, table_1→…→table_N 점프 없음 (Appendix figure는 본문 끝에 부착, `parsing_rules.md` §3-2-bis 자가 검증 스크립트로 확인)
- **structured.json이 원문 본문(Abstract → Conclusion)의 모든 섹션/subsection을 누락 없이 포함** (Related Work, Theoretical Analysis, Datasets/Implementation Details 등 — Stage 2 완전성 자가 검증 통과)
- **structured ↔ translations sentence_id 1:1 매칭** (missing 0 / extra 0 / 빈 값 0 / 중복 0 — Python 검증 스크립트로 확인)
- 번역 누락 0건 (회색 placeholder / `—` 미발견)
- **`tabs_data/study.json` 존재 + ①′ Paper Study가 셸(`section-empty-note`)이 아님** (`check_paper_structure.py`가 FAIL로 검사)
- **`python tools/check_study_refs.py "papers/N. name"` 통과 (study.json의 모든 ref가 structured/asset에 실존)**
- **`python tools/check_html_escape.py "papers/N. name"` 통과 (태그 수프 위험 0건)** — 번역문·tabs_data의
  이스케이프 안 된 `<`+영문자(수식 표기 류)가 있으면 그 지점 이후 문서 전체가 굵게 깨진다
  (`rules/math_rules.md` § 부등호·꺾쇠, 모체 사례 — 배포본 미포함)
- 콜아웃/퀴즈/해석/초보자 노트가 의도한 위치에 표시
- **모든 figure/table에 `.study-fab` 버튼 + 4-섹션 정형(s-look·s-num·s-author·s-check) 학습 가이드 모달** (interpretation/beginner-note의 단순 복제 ✗ — 한 단계 더 깊은 분해. §12 정본 = `samples/cares/`의 study-drawer)
- **② Dissection의 `diss-summary` 카드가 9-row 정형** (한 줄 / 문제 / 관찰 / Gap / 방법 / 차별 / 효과 / 한계 / 30초 요약) + **`dissection_overview.png` 한 장 인포그래픽(codex 미사용 시 기준 빌더의 결정적 SVG)이 헤더 아래·rows 위에 인라인** (`rules/component_rules.md` §14, 정본 = `samples/cares/_build.py`)
- **`.diss-tag` pill이 본문 한 줄 높이의 작은 알약 모양** — grid cell의 세로 stretch로 큰 타원·이상한 모양이 안 보임. 5개 속성 필수: `align-self:start` / `justify-self:start` / `width:max-content` / `white-space:nowrap` / `line-height:1.4` (`rules/component_rules.md` §15)
- **② Dissection 카드가 단일 컬럼으로 수직 적층 + 각 row가 `[태그 pill, 한 줄]` → `[본문, 그 아래]` 상하 적층** — `.diss-grid` = `grid-template-columns:1fr` / `.diss-row` = `display:flex; flex-direction:column` / `dd.diss-body { margin-left:0 }` 모두 적용 (`rules/component_rules.md` §16, 정본 = `samples/cares/_build.py`, 2026-05-13 갱신)
- **모든 콘텐츠 이미지(① 자산·② summary overview·③ 학습 보조)에 비율 유지 lightbox 동작** — `cursor:zoom-in` hover, 클릭 시 어두운 배경 모달에 비율 유지하며 확대, 휠/+/− 줌·드래그 pan·더블클릭 토글·ESC 닫기. `study-fab` 클릭은 `e.stopPropagation() + e.preventDefault()`로 lightbox 트리거 차단 (`rules/component_rules.md` §13)
- ② ③ ④ 탭 콘텐츠가 비어 있지 않음
- **`python tools/check_paper_structure.py "papers/N. name"` FAIL 0건** (표준 폴더 구조와 탭·카드·주입 구조 검사)
- **`config.json#meta` 확정** — topbar 제목·저자·소속·venue·연도가 PDF와 일치, `code`는 URL일 때만 존재(없으면 키 생략, `rules/design_v4_dashboard.md` §6)
- ⑤ ⑥ 탭은 셸만 — `tab-intro` + `.section-empty` placeholder ("이 탭은 별도 요청 시 작성됩니다") 표시
- **①′ Paper Study 탭 전체 동작** (`rules/component_rules.md` §17 정본): 서술칸 localStorage 자동 저장 + 잠금 토글("분석 비교하기", Gap 3분할 합산) + read 패널 단락 리더(✓ 세션 한정) + 근거 칩 전수 점프(`data-ev`/`data-read-pid` 대상 실존) + 도표 뷰어(원문 캡션·번역·해석 + 학습 가이드 드로어) + 플로팅 메모(자동 저장) + 문장 형광펜(클릭 토글, 영·한 동기, 리더·Translation 공통) + 호버 페어링이 리더 복제 문장에서도 동작(위임 방식) + 노트 내보내기/가져오기(폴더 기억) + 돌아가기 버튼 + `study/` 폴더 존재
- MathJax가 ① 본문 + ③ 수식 카드를 렌더 (탭 전환 후 재렌더 포함)
- 모바일(< 640px)에서 탭 줄바꿈, 표 overflow-scroll 정상
- **모든 `<img>` 태그가 `data:image/png;base64,...` 형태** — 외부 참조(`src="assets/..."`, `src="./..."`, `src="http..."`) 잔존 0건
- **`python tools/check_image_prompts.py "papers/N. name"` 통과 (prompt_*.txt 밀도·구조 위반 0건)** —
  **codex 호출 전**에 돌린다. 성긴 프롬프트는 반드시 여백 크고 정보량 적은 그림으로 돌아오므로,
  이 게이트를 통과하지 못한 프롬프트로는 이미지를 만들지 않는다 (`rules/component_rules.md` §11.8)
- **생성된 이미지가 §11.8.6 육안 체크리스트 통과** — 패널 누락·여백 과다·수치 오기·라벨 깨짐·
  프롬프트 혼선(병렬 호출 시 `--cd` 공유 사고) 0건. 미달이면 프롬프트를 고쳐 재생성 (같은 프롬프트 재시도 금지)
- **codex로 생성한 학습 보조 이미지에 논문 제목·헤더·저자명이 박혀 있지 않음** — 6번째 계명(`rules/component_rules.md` §11.2) 통과. 콘텐츠와 영어 섹션 라벨만

**영상(Stage 13)** — `papers/[name]/[ShortName]_video.mp4`가 다음을 만족할 때 완료 (사용자가 영상을 빼라고 했으면 생략):

- **`python tools/video/check_video.py "papers/N. name"` FAIL 0** — 출처 칸, 길이 10:00~15:00(실제 음성), 프롤로그·본 장 6~9·에필로그, 사용자 연구 가설·시사점 0, tone_lint 0, 프레임 수 = 음성 길이×30, -16±1 LUFS. WARN(컷당 숫자, 긴 문장, 인용 글자 차이)은 하나씩 보고 판단을 남긴다
- 학부생 눈높이 규칙 7개(`rules/video_rules.md` 5절) 반영 — 식 1개를 기호마다 읽고 의미 문장으로 닫음(식이 없는 논문은 알고리즘·절차 단계), 방법 전체 그림이 세부보다 먼저
- 도형 설명 장면은 motion 클립, 실제 자료는 최고 해상도 원본. 외부 자료는 `CREDITS.md` + 화면 출처
- 입력 이미지가 나오는 장면에 도형 대체 없음: 논문 자료 → codex 예시 사진 → 샘플 데이터셋, codex·데이터셋 사진에 "예시 사진" 표기, `video/assets/sources.json` 기록 (`check_video.py` G11·G12)
- `make_video.py … gapcheck` 시트에서 장 경계 틈 전후가 같은 장면, 클립 `beats` 시트에서 잘림·겹침 0
- 자막: 고유명 영문 표기, 전문용어 장마다 첫 등장 `English(한국어)`, 인용 표지, 하단 고정 문구
- `python tools/check_paper_structure.py "papers/N. name"` 영상 항목 통과(video/ 입력, TODO_PAPER 0, mp4 존재)

(⑤ 시뮬레이터 슬라이더 / ⑥ Q&A 콘텐츠 작동은 사용자가 별도 요청 시에만 추가 검증 항목으로 활성화)

---

## 참고 문서

- `CLAUDE.md` — 프로젝트 개요, 표준 템플릿, 빌드 절차, 고정 규칙 요약, 디렉토리 규약
- `rules/project_policies.md` — 정책 상세 · `rules/build_lessons.md` — 빌드 전 점검과 정본 학습 사례
- `templates/paper_base/` — 기준 빌더 (`_build.py` 복사 → `TODO_PAPER` 채움)
- `prompts/01~13_*.md` — 각 단계별 프롬프트 정본 (11 = Paper Study — 기본 빌드 포함, 12 = 논문 정립·연구 멘토 - 빌드 밖 별도 세션, 13 = 논문 소개 영상 — 기본 빌드 포함)
- `rules/video_rules.md` — 영상 형식·원고·음성·화면·자막·QC 규칙, `tools/video/` — 영상 파이프라인, `skills/motion-broll/` — 클립 엔진 스킬 배포본
- `rules/` — 파싱 / 분석 / 코칭 / 지식 / 수식 / 컴포넌트 / 구현 규약 + `domain_profile.md`
- `samples/` — 정본 (수정 금지) — `cares/`(v4 8탭 + Paper Study 워크드 예제) + `design/`(로고) + `README.md`(1~3세대 인터랙션 개념 히스토리)
