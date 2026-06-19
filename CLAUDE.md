# Paper Review HTML Builder

논문 PDF를 **6탭 학습용 HTML**로 변환하는 프로젝트.
**대화형(conversational) 작업 방식** — 빌드 스크립트나 파이프라인 자동화 없이, 사람과 Claude가 한 논문씩 함께 만들어 나간다.
JSON으로 정제된 콘텐츠 + 정본 샘플의 디자인 + 규칙 문서를 입력으로 두고, Claude가 그 자리에서 단일 HTML을 작성한다.

---

## 표준 학습 템플릿

모든 논문은 다음 6개 탭으로 구성된다. **모든 논문은 v3 디자인 토큰(white + lavender)으로 통일**되어 있다 (이전 v2 베이지+마룬 팔레트는 폐기, 2026-05-09).

**정본 레퍼런스 (수정 금지 — 신규 논문이 따라갈 기준)**
- 디자인·인터랙션 정본 — `samples/SAFE_output.html`(1세대 — 셸·토큰·문장 페어링), `samples/FrameFusion_output.html`(2세대 — eq-link cross-tab, fig hotspot, glossary), `samples/SGL_output.html`(3세대 — study-fab 자산 모달, 3-Part Simulator, 대화형 빌드 방식)
- perceptron 빌더 정본 (대화형 빌드 + 외부 데이터 → 단일 HTML 조립 모범) — `papers/4. perceptron/Perceptron_output.html` + `_build.py`

| # | 탭 ID | 라벨 | 내용 | 기본 빌드 |
|---|---|---|---|---|
| ① | `tab-reading` | 원문 / 번역 | 영한 양방향 문장 단위 호버 동기화, 콜아웃, 자산 + 해석 + 초보자 해설 | ✅ 풀 빌드 |
| ② | `tab-dissection` | Paper Dissection | 연구 동기 · 핵심 관찰 · 차별점 · 방법론 · 실험 검증 · 한계 + 논문 총정리 (7+1 = 8 카드) | ✅ 풀 빌드 |
| ③ | `tab-knowledge` | Background & 핵심 수식 | 배경지식, 주요 수식 풀이 | ✅ 풀 빌드 |
| ④ | `tab-questions` | Questions & Diagrams | 비판적 질문, 도식 | ✅ 풀 빌드 |
| ⑤ | `tab-simulator` | Simulator & Code | 핵심 알고리즘 시뮬레이터, 의사코드/코드 | ⏸ **셸만** |
| ⑥ | `tab-qa` | 학습 기초 Q & A | 자가 점검 Q&A | ⏸ **셸만** |

### 기본 빌드 범위 — ⑤ ⑥은 셸만 (사용자 명시 정책)

신규 논문 빌드 시 ⑤ Simulator & Code, ⑥ 학습 기초 Q & A는 **콘텐츠를 작성하지 않는다**. 사용자가 명시적으로 요청할 때만 별도 작업으로 채운다.

**셸만 빌드한다는 것의 의미:**
- 탭 버튼 (`<button data-tab="tab-simulator|tab-qa">`)은 그대로 유지 (네비게이션 일관성)
- `<section id="tab-simulator">`, `<section id="tab-qa">` 패널 element도 그대로 유지
- `<div class="tab-intro">` 표준 안내 헤더 유지 (h2 + 한 문장 설명)
- 본문은 `.section.section-empty` placeholder 한 장 — "이 탭은 별도 요청 시 작성됩니다" 같은 `.section-empty-note` 한 줄

**이 정책의 효과:**
- Stage 8 (Simulator Design) / Stage 9 (QA Design) 산출물(`tabs_data/simulator_spec.md`, `tabs_data/qa.json`)이 없어도 빌드 가능
- 신규 논문은 ① ~ ④까지의 데이터만 준비되면 즉시 6탭 HTML 한 장 조립
- ⑤⑥은 사용자가 그 논문에 대해 깊이 더 들어가고 싶다고 판단했을 때 별도 세션에서 추가

### 디자인 토큰 (정본 — v3, 모든 논문 적용)

흰색 위주 배경 + 부드러운 라벤더/하늘색/더스티 로즈 파스텔. ACAS 로고의 안개 그라디언트 톤이 출처.

```css
:root {
  /* Surface — 흰색 위주, 페이지 전체에 옅은 lavender wash */
  --bg: #fbfaff;           /* near-white + 살짝 보랏빛 — 페이지 배경 */
  --paper: #ffffff;        /* 카드 면 — 순백 */
  --ink: #1f1d24;          /* 본문 글자 — near-black, 살짝 cool */
  --muted: #7a7484;        /* 보조 글자 — lavender-tinted gray */
  --line: #ece8f0;         /* 보더 — 매우 옅은 lavender wash */

  /* Primary — lavender (로고 보라) */
  --accent: #8b75c0;       /* ★ 텍스트·보더·강조선 전용 — box 배경에 깔지 말 것 */
  --accent-soft: #e4d9ff;  /* 카드/콜아웃 배경 tint — 회색 빠진 또렷한 파스텔 */
  --accent-pale: #d2c2f5;  /* 그라디언트 끝점용 — soft보다 한 단계 진함 */

  /* Secondary — soft sky/cyan (로고 청록) */
  --azure: #6b95b3;        /* 텍스트/보더 */
  --azure-soft: #d9ebff;   /* 배경 tint — accent-soft와 동일 밝기 라인 */
  --azure-pale: #c0dcf5;   /* 그라디언트 끝점용 */

  /* Tertiary — dusty rose (빨강 계열, 파스텔) */
  --rose: #b87887;         /* 텍스트/보더 */
  --rose-soft: #ffdde6;    /* 배경 tint — 동일 밝기 라인 */

  /* 카테고리 보조 (이전 --sage/--gold 자리) */
  --mint:  #75ad8e;   --mint-soft:  #e3eee7;
  --amber: #ad8e4e;   --amber-soft: #f3ead4;

  /* Hero 데코 — 로고 같은 청록 → 라벤더 그라디언트 */
  --hero-gradient: linear-gradient(135deg, #c0dcf5 0%, #d2c2f5 100%);
}
```

폰트: `Pretendard Variable`, `Noto Sans KR`

**사용 규칙 (중요 — 색이 탁해 보이지 않도록):**
- `--accent` / `--azure` / `--rose` 같은 **deep tone은 글자·보더·강조선 전용**. box/section/카드 배경에 깔지 말 것.
- box/카드 배경에는 항상 `--accent-soft` / `--azure-soft` / `--rose-soft` (옅은 wash) 또는 `--paper` 사용.
- `--*-pale`과 `--hero-gradient`는 데코 그라디언트·히어로 헤더·로고 자리 한정.
- 본문 글자는 `--ink`, 보조 글자는 `--muted` 고정.

### 디자인 토큰 — v2 폐기 메모 (2026-05-09)

`samples/SAFE_output.html`(1세대), `samples/FrameFusion_output.html`(2세대), `samples/SGL_output.html`(3세대)는 원래 warm beige + maroon 팔레트(v2)로 동결돼 있었으나, **2026-05-09 통일 작업 시점에 모두 v3 팔레트로 리컬러됨**. 마크업·인터랙션은 그대로 보존, CSS 토큰과 hardcoded hex만 swap.

리컬러 스크립트 (이미 실행 완료, historical record — 모두 `_archive/`):
- `_archive/samples_recolor_v3.py` — SAFE/FrameFusion 처리 (당시 `samples/_recolor_v3.py`)
- `_archive/sgl_recolor_v3.py` — SGL 처리 (당시 `papers/3. sgl/_recolor_v3.py`)
- v2 backup: `_archive/v2_backups/*.before_v3` 3편

**v2 → v3 변수 alias 규약** — 마크업이 참조하는 v2 변수명(`--sage`, `--gold`, `--indigo`, `--plum` 등)은 `:root`에 alias로 살려 둠 (예: `--sage: var(--mint)`). 따라서 기존 정본의 마크업을 신규 논문에 베껴 와도 별도 수정 없이 v3 색이 적용된다.

**인터랙션 세대 (기능 진화)** — 1세대(SAFE) → 2세대(FrameFusion) → 3세대(SGL). 신규 논문은 3세대 인터랙션을 베이스로 한다.

### 🔴 무리한 한국어 변환 금지 — 모든 한국어 prose에 적용 (정책, 2026-05-18)

번역(① tab-reading)뿐 아니라 LLM이 직접 한국어 문장을 쓰는 모든 자리(② dissection 카드, ③ knowledge primer/eq/concept, ④ coaching q·a, figure interpretations·beginner_notes·study_modals·callouts)에 동일 적용.

**원칙** — 한국 ML 커뮤니티에 굳어진 표기가 없으면 영문 그대로 둔다. 자체 신조어·음역어를 만들지 않는다. "이게 한국어 학회 발표에서 자주 듣는 표현인가?" 자가 점검을 통과해야 한다.

**대표 안티패턴** (재도입 금지) — `거친 데이터셋`(crude dataset) / `이진 투표`(Binary Polling) / `워밍업 파인튜닝`(warm-up fine-tuning) / `고충실도`(high-fidelity) / `강한 정렬`(strong alignment) / `정보성 있는`(informative) / `노동을 요구하는`(laborious) / `적합성을 높이고`(relevance를 fitness로 오역) / `능력 차원 커버리지`(3-단어 한자 합성) / `순위화`(일본식 한자조어).

**OK인 표기** (한국 ML 표준) — 어텐션·파인튜닝·풀링·임베딩·그래디언트·투영·노름·환각·프루닝·어블레이션·레지스터 토큰·음의 로그우도.

정본 규칙·전체 안티패턴 표·자동 점검 정규식: `prompts/03_translation.md § 🔴 무리한 한국어 변환 금지`. cross-ref: `rules/knowledge_rules.md §2`, `rules/analysis_rules.md § Forbidden`, `rules/coaching_rules.md § 절대 금지`.

> 정본 학습 사례 (실패→복구): `papers/24. geollava8k` 1차 빌드에서 위 안티패턴 다수 사용. 사용자 지적 후 manual.json·analysis.json·dissection.json·knowledge.json·config.json·HTML 18곳 일괄 정리. 동일 실수 재발 방지가 이 정책의 직접 동기.

### 🔴 Stage 2 완전성 — 원문 1:1 보존 (정책)

`structured.json`은 원문을 **요약·압축·합치는 곳이 아니다**. 본문(Abstract → Conclusion)의 모든 섹션·subsection·마침표 단위 문장을 1:1로 보존한다.

- 본문 섹션 누락 금지 — `Related Work`, `Theoretical Analysis`, `Datasets`, `Implementation Details`, `Computational Efficiency` 같은 sub-section도 빠뜨리지 않는다 (학습 가치 판단은 Stage 4 이후의 책임)
- 마침표 단위 문장 병합 금지 — semicolon·em-dash로 두 문장을 한 sentence_id에 묶지 않는다
- Contribution bullet은 도입 한 줄 + 각 bullet 각각 별도 sentence_id
- 짧은 메타 문장도 보존 ("More cases are in Appendix H.", "Our code is available at …")
- 부록(Appendix A, B, …) / Acknowledgments / References만 의도적 제외 가능

structured.json 작성 후 **반드시 fulltext.txt와 섹션 수·subsection 수·paragraph별 문장 수를 대조**한다. 자세한 검증 절차·금지 패턴·정본 사례: `prompts/02_structuring.md` § 🔴 CRITICAL 완전성 규칙.

> 정본 학습 사례 (실패→복구): `papers/20. sparse_vlm`은 1차 빌드에서 본문 70문장으로 압축됐다가 사용자 지적 후 163문장으로 재작성된 케이스. Related Work 전체·3.4 Theoretical Analysis가 누락됐었다. 동일 실수 재발 방지가 이 정책의 직접 동기.

### 🔴 Study Modal — 자산별 학습 가이드 모달 (정책)

각 figure/table 카드의 `.study-fab` 버튼을 누르면 열리는 모달은 **카드 하단의 `interpretation` / `beginner_note`와 다른 정보**를 담는다. 단순 복제는 모달 무용지물.

정본 = `samples/SGL_output.html` fig_1 모달의 **4-섹션 정형**:
- `s-look` (어디를 먼저 볼까) — 시선 동선 + (다이어그램이면) 박스/화살표/N×/Encoder·Decoder 등 모든 시각 요소의 의미 풀이
- `s-num` (결정적 숫자) — `.study-num-row` ≥3개. 단순 수치 인용이 아니라 그 숫자의 정치적·실용적 함의 한 줄
- `s-author` (저자가 말하는 것) — 이 그림으로 못 박는 명제 1~3개
- `s-check` (학습 체크포인트) — `<ul>` 2~4개. 다시 볼 때 가장 먼저 확인할 부분 / 이 그림이 논문 전체의 무엇을 압축하는지

데이터는 `analysis.json#study_modals[aid] = {title, look, nums≥3, author, check≥2}`. 마크업·CSS·JS 정본: `rules/component_rules.md` §12. 작성 가이드: `prompts/06_figure_interpretation.md` § Layer 3.

**UX — 오른쪽 사이드 드로어 (정책, 2026-05-19 갱신)**: 학습 가이드는 풀스크린 모달(어두운 백드롭 + 중앙 카드)이 **아니라** 오른쪽에서 슬라이드-인되는 폭 ~440px 드로어로 연다. 학습자가 가이드 4섹션을 읽는 동안 정작 봐야 할 figure가 가려지면 안 되기 때문 (24. geollava8k 학습 중 사용자 직접 지적). 드로어 열린 상태에서 figure·문장·lightbox 모두 사용 가능. 닫기는 ① ×버튼 ② ESC ③ 드로어 바깥 클릭 (단 다른 `.study-fab` 클릭은 예외 — 내용 전환 시 깜빡임 방지). CSS·JS 정본 = `rules/component_rules.md` §12.5 / §12.6. `samples/SGL_output.html`은 historical reference로 동결 — 그 안의 풀스크린 모달 CSS는 더 이상 복사하지 않음.

> 안티패턴 (정본이 아닌 잘못된 관성): papers 4~19의 일부 빌드에서 모달이 "캡션 + 전문가 해석 + 초보자 해설" 3-block으로 채워져 figure 하단 내용과 거의 동일했던 경우. 신규 빌드는 4-섹션 정형으로 깊이 분해.

### 🔴 Vector PDF 자산 크롭 — 캡션 좌표 anchor 정본 (정책)

자산(figure / table) PNG는 **PDF 텍스트 좌표를 anchor로** 잘라낸다. 현대 ML/CV 논문은 한 figure가 수십 개의 image object로 분해되어 잡히므로 `page.get_image_bbox()` 단독 사용은 실패. 대신:

- 캡션 첫 줄을 `^Figure N\. ` / `^Table N\. ` 정규식으로 검출 → PDF point 좌표(612×792pt) 획득
- Figure: 캡션 **아래** 컨벤션 → `y_top = 60~64pt(header 제외), y_bot = caption_bottom + 4~8pt 패딩`
- Table: 캡션 **위** 컨벤션 → `y_top = caption_top − 3pt 패딩, y_bot = 표 데이터 마지막 행 + 4pt 패딩`
- Page running header(논문 제목, y≈47~56pt)는 항상 **y_top ≥ 64pt**로 제외
- Column band x: full-width(48..564) / 좌측(48..302) / 우측(304..564)
- PDF pt → pixel: `pixel = pt × (DPI/72)` (200dpi 기준 × 2.7778)
- **시각 검증 의무** — 각 PNG를 직접 열어 헤더 누수·캡션 잘림·아래 본문 텍스트 섞임 확인. 조정은 4~8pt 단위로 한 자리 수씩.

정본 구현 = `papers/20. sparse_vlm/_crop.py`. 자세한 절차·검출 코드·column 좌표 표·자산 유형별 컨벤션: `rules/parsing_rules.md` §4-A "vector PDF — 캡션 좌표 기반 bbox 검출".

> 정본 학습 사례 (실패→복구): SparseVLM 초기 크롭이 페이지 픽셀 좌표만 하드코딩한 결과, Figure 3·4·5·6 캡션이 잘리고 Table 3에 아래 본문이 섞이고 Figure 5는 위치 자체가 어긋났다. PDF 좌표 + 캡션 anchor 기반으로 재크롭 후 11개 자산 모두 본체+캡션 깨끗 + 누수 0건 달성.

### 🔴 자산 등장 순서 — 번호 순(numerical order) 정본 (정책)

① 원문/번역 탭에서 figure/table이 등장하는 순서는 **원본 논문의 번호 순서를 따른다.** `fig_1 → fig_2 → … → fig_N`, `table_1 → … → table_N`. 번호 점프(예: `fig_3 → fig_7 → fig_4`)는 학습자에게 "왜 갑자기?"라는 의문을 만들므로 금지.

- **Appendix figure**(본문 fig_1~N 뒤에 오는 appendix의 figure)는 **본문 마지막 figure 뒤**에 배치 — 자연스러운 자리는 마지막 분석/시각화 문단(보통 5.x Qualitative 류). "개념적 관련성"이 본문 중간 문단에 더 가까워 보여도, 번호 점프를 만들지 않는다.
- **개념 정합성과 충돌 시**: 번호 순서 우선. 개념 cross-reference는 `analysis.json#interpretations` / `beginner_notes` / `study_modals`에서 풀어주면 충분 — 자산 자체를 옮기지 않는다.
- 자세한 검증 스크립트와 정본 사례: `rules/parsing_rules.md` §3-2-bis.

> 정본 학습 사례 (실패→복구): SparseVLM 초기 빌드는 fig_7(Appendix A redundancy diagram)이 "개념적으로 p8 rank-기반 redundancy에 어울린다"는 이유로 p8에 붙어 등장 순서가 `1→2→3→7→4→5→6`이 됐다. 사용자 지적 후 fig_7을 p12_vis(5.4 Qualitative 끝)로 이동해 `1→2→3→4→5→6→7` 자연 순서 회복.

### 🔴 Dissection Summary 카드 — 9-row 정형 + 한 장 overview 이미지 (정책)

② Paper Dissection 탭의 마지막 카드 `diss-summary`는 **9-row 정형 + 한 장 인포그래픽** 동봉이 정본이다 (2026-05-12 갱신). 기존 4-row(관찰/방법/차별/결과) 카드는 점진 마이그레이션 권장.

- **9 rows**: ① 한 줄 ② 이게 왜 문제인가(Problem) ③ 저자의 핵심 관찰(Observation) ④ 기존 방법은 왜 부족한가(Gap) ⑤ 어떻게 해결했나(Method) ⑥ 다른 논문과 무엇이 다른가(Novelty) ⑦ 효과 — 숫자(Results) ⑧ 한계와 의미(Limitations & Implication) ⑨ 30초 요약(For Beginners)
- **깊이 기준**: \"<em>논문 안 읽은 사람도 이 카드 한 장만 보고 충분히 이해</em>\". 각 row 본문 300~600자, `<strong>`·`<em>` 강조 활용
- **한 장 overview 이미지**: `assets/generated/dissection_overview.png` (1536×864, 5단 PROBLEM→OBSERVATION→METHOD→NOVELTY→RESULTS 가로 인포그래픽). codex 6계명으로 생성. summary 카드 헤더 아래·rows 위에 `<figure class="diss-overview-figure">`로 base64 인라인
- 자세한 규약: `prompts/04_research_analysis.md` Stage 4 / `rules/component_rules.md` §14
- 정본 사례: `papers/21. lv_pruning`

### 🔴 Dissection 카드 레이아웃 — 수직 적층 + tag 위·body 아래 (정책, 2026-05-13)

② Paper Dissection 탭의 카드는 **단일 컬럼으로 위에서 아래로 쌓고**, 각 카드 안의 row는 **태그 한 줄 위 / 본문 한 단락 아래** 형태로 표시한다. (좌우 2-column grid + tag↔body 옆 배치는 가독성을 떨어뜨리므로 폐기.)

- **`.diss-grid`**: `display:grid; grid-template-columns:1fr; gap:18px` — **단일 컬럼** (이전 `repeat(2, minmax(0,1fr))` 폐기)
- **`.diss-row`**: `display:flex; flex-direction:column; gap:8px; align-items:flex-start` — **tag block + body block 상하 적층** (이전 `display:grid; grid-template-columns:auto 1fr` 폐기)
- **`<dl class="diss-rows">`**: `<dt class="diss-tag">` + `<dd class="diss-body">` 마크업은 그대로 유지. CSS만 변경
- **`dd.diss-body`**: 브라우저 기본 `margin-left`를 0으로 — `dd.diss-body { margin-left: 0 }` 명시
- **`.diss-tag`**: §15의 5속성(`align-self:start` / `justify-self:start` / `width:max-content` / `white-space:nowrap` / `line-height:1.4`)은 그대로 유지 — flex column 안에서도 pill 모양 보장에 필수
- **렌더 결과**: 한 row가 이렇게 표시 — `[태그 pill, 한 줄]` / `[본문 한 단락, 그 아래]`. 화면이 좁든 넓든 동일 패턴

**원래 9-row summary 카드뿐 아니라 모든 dissection 카드(motivation/observe/compare/logic/verify/risk/extend/summary)에 동일 적용**.

- 정본 사례: `papers/22. free/_build.py`
- 자세한 CSS: `rules/component_rules.md` §16

> 안티패턴 (이전 정본의 잘못된 관성): papers 4~21까지의 빌드는 2-column grid + tag-body 옆 배치였다. 카드 텍스트가 길어질수록 좌우로 흐름이 끊겨 \"한 카드를 한 호흡에 읽기\"가 깨졌다. 사용자 지적 후 22. free에서 수직 적층으로 재작성.

### 🔴 Image Lightbox — 모든 콘텐츠 이미지 비율 유지 확대 (정책)

학습 자료의 **모든 콘텐츠 이미지**(① 자산·② summary overview·③ 학습 보조)는 클릭 시 비율 유지 lightbox로 확대 가능해야 한다.

- **셀렉터**: `.asset-image-wrap img`, `.diss-overview-figure img`, `.concept-figure img`에 `cursor: zoom-in` + 클릭 핸들러
- **lightbox 모달**: BODY 끝에 `.img-lightbox` 컨테이너 한 번. 어두운 배경 + 비율 유지(`object-fit: contain` + `max-height: calc(100vh - 80px)`) + 휠 줌(0.5x~8x) + 드래그 pan(확대 상태) + 더블클릭 토글(1x↔2.5x) + ESC 닫기 + `+`/`-`/`0` 키
- **study-fab 충돌 회피**: study-fab 클릭 핸들러에 `e.stopPropagation() + e.preventDefault()` 필수. 없으면 버튼 누를 때 모달 + lightbox 동시 열림 버그
- **`@media print`**: lightbox·study-modal·to-top 모두 `display: none`
- 마크업·CSS·JS 정본: `rules/component_rules.md` §13
- 정본 사례: `papers/21. lv_pruning/_build.py`

### 🔴 codex ImageGen 6계명 — 마지막 한 줄에 \"NO title text\" 명시 (정책)

codex CLI로 학습 보조 이미지를 생성할 때 prompt.txt 마지막에 **반드시** \"<em>NO paper title at top, NO standalone header, NO author names</em>\"를 박는다 (2026-05-12 추가, 6번째 계명). 이 한 줄이 빠지면 imagegen이 그림 상단에 \"<short_name>\" 같은 타이틀을 박아 학습 카드의 시각 통일성을 해친다. 자세한 형식: `rules/component_rules.md` §11.2.

### 자산 임베딩 정책 — 모든 이미지는 HTML 안에 박힌다 (의무)

**원본 figure/table + ImageGen으로 만든 학습 보조 이미지 — 모두 예외 없이 base64 인라인.**

- `<img src="data:image/png;base64,...">` 형태로 단일 HTML 안에 박는다. 결과 파일 한 장만 다른 PC·모바일·USB·이메일로 옮겨도 모든 그림이 그대로 뜬다 (self-contained).
- 동기: 이 산출물은 배포용 웹 페이지가 아니라 **사용자 개인 학습 아티팩트**다. 휴대성이 용량보다 절대 우선.
- 결과 크기 가이드: 작은 논문 1.5MB대 (SAFE) → 평균 2~3MB대 (FrameFusion) → 자산이 많으면 15MB 이상도 허용 (SGL 16.5MB). 용량을 이유로 외부 참조로 되돌리지 않는다.
- 외부 참조(`<img src="assets/...">` / `<img src="assets/generated/...">`)는 **개발 중 미리보기에서만** 허용. 최종 산출물에는 반드시 인라인.

### 학습 보조 이미지 생성 (② ~ ⑥ 탭, ① 번역 탭 제외)

논문 학습에서 시각적 아키텍처(시스템 다이어그램·단계별 일러스트·개념 메타포)는 **사용자 이해의 핵심 채널**이다. 배경지식 카드(③), Dissection 카드(②), 직관 다이어그램(④), 시뮬레이터(⑤), QA(⑥)에서 글만으로 부족한 부분은 보조 이미지로 보완한다.

**생성 방식 — Claude가 Bash로 codex CLI 직접 호출** (별도 플러그인·MCP 자동화 없음, Bash 한 줄):

> 정식 호출 형식·검증된 명령 템플릿·`<figure class="concept-figure">` 컴포넌트·자동화 스크립트 골격: **`rules/component_rules.md` §11**. 신규 논문 빌드 전 반드시 통독.

**5계명 — Windows에서 한 번에 통과시키는 형식** (생략 시 인코딩/hang/컷아웃으로 막힘):
1. **Bash 툴 사용** — PowerShell 5.1은 native exe로 한글을 CP949로 깨뜨림.
2. **prompt.txt를 UTF-8로 작성**, codex 인자는 **ASCII 한 줄**로 그 파일을 읽으라는 지시만.
3. **stdin은 `< /dev/null`** — codex가 stdin 입력 대기로 hang하는 것 차단.
4. **스타일 명시** — 프롬프트에 "풀 블리드 일러스트 / 사진, 배경 가득, NOT a transparent cutout" 박아두기. imagegen 기본값이 컷아웃.
5. **출력 경로 + 해상도 명시** — 절대 경로 + WxH (예: `1024x1024`).

**저장**: `papers/[name]/assets/generated/` (prompt 파일·원본 PNG 둘 다 재생성·디버깅용으로 보존).
**최종 HTML 임베드**: 위의 자산 임베딩 정책에 따라 **base64 인라인 의무**. 정본 컴포넌트 = `<figure class="concept-figure">` (§11.5).
**검수**: 사후. 결과 HTML 보고 마음에 안 드는 이미지 있으면 별도 재생성 요청 — 사전 검수로 흐름 막지 않음.

---

## 학습 인터랙션 세대 (1 → 2 → 3)

| 세대 | 대표 논문 | 추가된 특징 | 신규 논문에서의 권장 |
|---|---|---|---|
| 1세대 | SAFE | 6탭 골격, 디자인 토큰, 문장 페어링(문단 단위), 의사코드+슬라이더 시뮬레이터 | 최소 베이스라인 |
| 2세대 | FrameFusion | 문장 단위 페어링, `.eq-link` 수식↔본문 cross-tab 점프, `.fig-hotspot` 그림 핫스팟, `.glossary` 호버 툴팁, `#ff-toc` 사이드바 TOC | 기본 적용 |
| 3세대 | SGL | `study-fab` + `study-modal` 자산별 전문가 해설 모달, ⑤ Simulator 3-Part 정형(의사코드 → 인터랙티브 슬라이더 → 좌우 코드 비교), 빌더 없이 대화형으로 직접 작성 | **신규 논문은 여기를 따른다** |

신규 논문은 SGL의 인터랙션·구성 관성을 따르되, 셸/토큰/마이크로 디자인은 SAFE·FrameFusion 정본을 그대로 사용한다.

---

## 디렉토리 구조

```
Paper_review_html/
├── papers/                ← 논문별 데이터 + 자산. 폴더명 = `N. shortname`
│   ├── 1. safe_learning/  · NAACL 2025 (SAFE)            — 1세대
│   ├── 2. frame_fusion/   · ICCV 2025 (FrameFusion)      — 2세대
│   ├── 3. sgl/            · CVPR 2025 (SGL, A Stitch …)  — 3세대 작업 데이터 (정본 HTML은 `samples/SGL_output.html`)
│   └── 4. perceptron/     · Psych. Review 1958
├── prompts/               ← LLM 단계별 프롬프트 (10단계 — workflow.md 참조)
├── rules/                 ← 디자인 / 분석 / 컴포넌트 규약
├── rawpaper/              ← 원본 PDF
├── samples/               ← 정본 HTML (수정 금지) — SAFE(1세대), FrameFusion(2세대), SGL(3세대)
├── tools/                 ← 재사용 도구 (crop_assets.py, gen_tab_reading.py, reparse_pdf.py)
└── workflow.md            ← 10단계 작업 흐름
```

### `papers/[name]/` 표준 레이아웃
```
papers/[name]/
├── config.json            · 메타데이터, asset_layout, wide_assets
├── analysis.json          · callouts, interpretations, beginner_notes, quizzes, hotspots
├── structured.json        · 섹션/문단 단위 본문
├── translated.json        · 문장 단위 원문/번역 매핑 (선택, 편의용)
├── assets/                · 그림/표 PNG (fig_N.png, table_N.png)
│   └── generated/         · ImageGen으로 생성한 학습 보조 이미지
├── tabs_data/             · 탭별 분석 콘텐츠 JSON
│   ├── dissection.json    · ② 7-카드
│   ├── knowledge.json     · ③ primer + 수식 + 개념 카드
│   ├── questions.json     · ④ 다이어그램 + 4-카드
│   ├── qa.json            · ⑥ 카테고리 + 질문 (선택)
│   └── hotspots.json      · 핫스팟 sentence_id 배열 (선택)
└── translations/          · 번역 원본 (manual.json, refined.json)
```

---

## 새 논문 추가 — 대화형 흐름

> 빌드 스크립트가 없으므로 명령어 한 줄 빌드는 불가능하다.
> 대신 **Claude와 대화하며 한 단계씩** 콘텐츠를 만들고, 마지막에 HTML 한 장으로 조립한다.

### 폴더 명명 규약 (필수)

논문 폴더는 **`N. shortname`** 형식으로 만든다 — 숫자 + 마침표 + 공백 + 짧은 이름.

- `N` = `rawpaper/`의 PDF 번호 + 4 (배경 학습용 PDF 0~10번이 papers의 4~14에 해당. 현재 1~14 사용 중). 정본 3편(1~3)과 역사 커리큘럼(4~14)을 합쳐 신규 = 가장 큰 N에 1.
- `shortname` = lowercase + underscore (`safe_learning`, `frame_fusion`, `sgl`, `perceptron`처럼). 공백·대문자·하이픈 금지.
- 출력 HTML 파일명은 폴더와 별개로 짧게: `{ShortName}_output.html` (예: `5. flash_attn/FlashAttn_output.html`).
- 경로에 공백·마침표가 들어가므로 **모든 경로 문자열은 큰따옴표로 감싸야 한다** (`Path("papers/5. shortname")`, `cd "papers/5. shortname"`).
- 헬퍼 스크립트(`_recrop.py`, `_reembed.py` 등)는 폴더 이름이 바뀌어도 동작하도록 항상 `Path(__file__).parent` 기준 상대 경로를 쓴다 — 절대 경로 하드코딩 금지.

### 단계

1. **PDF → 텍스트 / 자산** — Claude에게 PDF를 주고 텍스트 추출 + Figure/Table PNG 크롭을 요청한다 (PyMuPDF 등). 결과를 `papers/N. shortname/assets/`로 가져옴. OCR'd 스캔본은 `tools/crop_assets.py` 3-pass 알고리즘 사용 — `rules/parsing_rules.md` §4-A 참조, 정본 사례 `papers/4. perceptron/_recrop.py`.
2. **구조화** — `prompts/02_structuring.md` 가이드에 따라 `structured.json` 작성. 섹션/문단 ID 부여.
3. **번역** — `prompts/03_translation.md`에 따라 sentence_id 단위 번역 → `translations/manual.json`. 필요 시 직접 또는 Claude 도움으로.
4. **분석 데이터 작성**
   - `config.json` — 메타데이터, `asset_layout`, `wide_assets`
   - `analysis.json` — callouts, interpretations, beginner_notes, quizzes, hotspots
   - `tabs_data/*.json` — 각 탭의 콘텐츠 (dissection / knowledge / questions / qa)
5. **HTML 생성** — Claude에게 위 입력 일체와 함께
   - **셸·토큰·문장 페어링·인터랙션·시뮬레이터·자산 모달 패턴** = `samples/`의 정본 3편 (SAFE 1세대 / FrameFusion 2세대 / SGL 3세대)

   을 정본으로 가리키며 6탭 HTML 작성을 요청한다. 자산은 base64 인라인. `prompts/08_html_generation.md`와 `rules/component_rules.md`가 디자인 정합 가이드.

---

## 참고 문서

- `workflow.md` — 10단계 작업 흐름 (Cleaning → Structuring → Translation → Research Analysis → Coaching → Figure Interpretation → Background Knowledge → Simulator Design → QA Design → HTML Generation)
- `prompts/01~10_*.md` — 각 단계별 프롬프트 정본
- `rules/` — 파싱 / 분석 / 코칭 / 지식 / 수식 / 컴포넌트 규약 (특히 `rules/component_rules.md`가 SAFE↔FrameFusion 마이크로 차이의 정식 결정을 담는다)
- `samples/` — 정본 (수정 금지) — SAFE(1세대), FrameFusion(2세대), SGL(3세대)
