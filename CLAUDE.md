# Paper Review HTML Builder

논문 PDF를 **8탭 학습용 HTML**(v4 대시보드 디자인, Paper Study 탭 포함)로 변환하는 배포 툴킷. 사람과 Claude가 한 논문씩 대화하며 만든다. 콘텐츠는 대화로 정제하고(생성적 단계), 본문 구조화·자산 크롭·HTML 조립은 정본 도구와 논문 폴더의 `_build.py`로 고정한다(결정적 단계). "명령어 한 줄로 끝나는 빌드"는 없지만, 조립 자체는 `_build.py` → `tools/restyle_dash_v4.py` 2단 빌드다.

이 킷은 특정 분야에 묶이지 않는다. 자연과학·공학·AI/CS·의학·인문사회 논문을 같은 절차로 만든다. 분야에 따라 달라지는 것(용어 표기 관행·증거의 종류·대안 설명 축·배경지식 단위·학회/저널 메타)은 `config.json#domain`(정본: `rules/domain_profile.md`)에서 읽는다. 문서 안의 ML 논문 예시는 **예시일 뿐** 규칙이 아니다.

**이 파일은 매 세션 자동으로 읽힌다. 실행할 규칙만 짧게 두고, 정책의 근거·상세는 `rules/project_policies.md`(같은 제목), 사고·측정값·실패 사례는 `rules/build_lessons.md`에 쓴다.**

## 기본 동작

- `rawpaper/`에 PDF가 있고 "이 논문 학습 도와줘 / 정리해줘 / HTML 만들어줘" 같은 요청이 오면 아래 "신규 논문 빌드 절차"를 끝까지 한다. 산출물은 `papers/N. shortname/`의 `{ShortName}_output.html`(8탭)과 HTML 앞에 보는 10~15분 소개 영상 `{ShortName}_video.mp4`(Stage 13) 두 개다. 사용자가 빼라고 하지 않으면 영상도 만든다. 영상 도구(ffmpeg·Node·Chromium·TTS 수 GB)는 `make_video.py` 단계가 처음 실행 때 스스로 설치하고, 막히면 HTML까지 마치고 빠진 것을 보고한다.
- 중간에 승인을 기다리지 않는다. 예외는 Stage 1의 `config.json#domain` 확인 1회와, 사용자가 단계별 검토를 요청한 경우다. 끝난 뒤 산출물 경로, 검사 결과, 직접 확인하지 못한 부분을 보고한다. 사용자에게 보이는 글은 한국어로 쓴다.

## 작업 전에 읽을 문서

| 작업 | 먼저 읽을 문서 |
|---|---|
| 신규 논문 빌드 (필수) | `workflow.md`, `rules/build_lessons.md`의 "빌드 전 점검", 해당 Stage의 `prompts/NN_*.md` (파일 번호 ≠ Stage 번호 — 대응표는 `workflow.md` 머리) |
| 논문 소개 영상 (Stage 13) | `rules/video_rules.md`, `prompts/13_video.md`, 뼈대 `templates/paper_base/video/` |
| 정책의 상세 근거 | `rules/project_policies.md` (이 파일의 규칙 제목과 같은 제목) |
| 분야 프로파일 · 연구 멘토 | `rules/domain_profile.md`, `prompts/12_research_mentor.md` |
| 디자인·탭·토큰 · 마크업·CSS·JS | `rules/design_v4_dashboard.md`, `rules/component_rules.md` |
| PDF 파싱·자산 크롭 · 수식·부등호 | `rules/parsing_rules.md`, `rules/math_rules.md` |
| 분석·코칭·배경지식 | `rules/analysis_rules.md`, `rules/coaching_rules.md`, `rules/knowledge_rules.md` |
| ⑤ ⑥ 탭 (요청 시에만) | `prompts/09_simulator.md`, `prompts/10_qa.md` |

## 표준 학습 템플릿

모든 논문은 아래 8탭으로 구성하고 v4 대시보드 디자인(저채도 grey-lavender · topbar · 해시 라우팅)을 따른다. v3(white+lavender, hero+6탭)·v2(베이지+마룬)는 폐기.

| # | 탭 ID | 라벨 | 내용 | 기본 빌드 |
|---|---|---|---|---|
| ① | `tab-reading` | Translation | 영한 문장 단위 호버 동기화, 콜아웃, 자산 + 해석 + 초보자 해설 | ✅ |
| ①′ | `tab-study` | Paper Study | 3-Phase 비판적 읽기 워크북 (Aerial View → Interrogation → Verdict) | ✅ |
| ② | `tab-dissection` | Paper Dissection | 7 + 1 = 8 카드 (마지막은 논문 총정리) | ✅ |
| ③ | `tab-knowledge` | Background | 배경지식 빌딩 블록 + 개념 카드 | ✅ |
| ③′ | `tab-math` | Mathematics | 핵심 수식 (③의 eq-panel을 restyle이 분리) | ✅ |
| ④ | `tab-questions` | Diagrams | 비판적 질문 4카드, 도식 | ✅ |
| ⑤ | `tab-simulator` | Code | 시뮬레이터, 코드 | ⏸ 셸만 |
| ⑥ | `tab-qa` | Q & A | 자가 점검 Q&A | ⏸ 셸만 |

탭 라벨에 숫자·이모지를 붙이지 않는다. 헤더는 hero 카드가 아니라 로고 + 3줄 텍스트 + 우측 메타 + 탭이 한 덩어리로 sticky되는 topbar다. 탭 전환은 해시 라우팅(뒤로/앞으로·딥링크)이다.

**기준 (수정 금지 — 모든 논문 공통):**

- 빌더 복사 기준: `templates/paper_base/_build.py` (특정 논문에 묶이지 않는 고정 기준. 공통 결함은 여기서 고친다. `_mk_corpus.py`는 선택)
- 디자인·인터랙션·데이터 워크드 예제: `samples/cares/` (`_build.py` + 전체 데이터 + `CARES_output.html`) + `tools/restyle_dash_v4.py` + `rules/design_v4_dashboard.md`
- 인터랙션 세대: 1세대 SAFE → 2세대 FrameFusion → 3세대 SGL의 기능(문장 페어링·hotspot·ref-link·study-fab·lightbox)은 모두 **4세대 CARES 정본에 흡수**돼 있다. 신규 논문은 인터랙션도 셸·토큰도 CARES(v4)를 따른다. 1~3세대 견본 HTML은 배포본에 없다(개념 히스토리: `samples/README.md`).
- 구조 검사: `tools/check_paper_structure.py`

## 신규 논문 빌드 절차

1. 폴더를 `papers/N. shortname`으로 만든다. N은 `papers/`의 가장 큰 번호 + 1(빈 배포본의 첫 논문 = `1. shortname`).
2. `workflow.md` 순서대로 Stage 0~7과 11의 산출물을 만든다(Stage 8·9는 요청 시에만, 12는 빌드 밖). 결정적 단계는 정본 도구로만 한다:
   - Stage 0 자산 크롭: `python tools/autocrop_assets.py "rawpaper/<논문>.pdf" "papers/N. name/assets"` → `--verify` → PNG를 모두 직접 연다.
   - Stage 2 구조화: `python tools/structure_paper.py "rawpaper/<논문>.pdf" "papers/N. name/structured.json"` → fulltext와 섹션·문장 수 대조.
3. `templates/paper_base/_build.py`를 논문 폴더로 복사하고 `TODO_PAPER` 표시만 채운다(머리 주석 · 판정 카드 절 · overview alt/figcaption · ②③④ tab-intro · 수식/개념 패널 부제 · footer). 한 논문에서만 필요한 규칙은 그 복사본만, 모든 논문에 해당하는 결함은 `templates/paper_base/`를 고친다.
4. 조립·주입 체인(순서 고정): `python "papers/N. name/_build.py"` → `restyle_dash_v4.py` → `memo_layer_fix.py` → `qa_button_inject.py` · `study_review_inject.py` · `reader_asset_chip.py`.
5. 검사: `check_html_escape.py` → 산출물 `grep '&lt;b&gt;'`, `grep '&amp;lt;'` = 0 → `check_study_refs.py` → `tone_lint.py` → `check_memo_layer.py`(playwright 없으면 skip) → **`check_paper_structure.py`**. 생성 이미지 프롬프트는 codex 호출 **전에** `check_image_prompts.py`.
6. `workflow.md`의 Definition of Done을 확인한다. 자산 PNG와 생성 이미지는 직접 열어 본다.
7. **영상(Stage 13):** `python tools/video/make_video.py "papers/N. name" new`로 `video/` 뼈대를 만들고 `rules/video_rules.md` 10절 순서(원고 → check-script → tts → animatic → 클립 → base-render → final → check)로 `{ShortName}_video.mp4`를 만든다. 입력은 모두 `video/`에 둔다.

산출물만 고치지 않는다. 빌더가 있는 논문은 빌더까지 고쳐야 재빌드와 다음 논문에서 결함이 되살아나지 않는다.

## 고정 규칙

아래는 모두 **상세 근거가 `rules/project_policies.md`의 같은 제목에 있다.**

### 기본 빌드 범위

⑤ ⑥은 사용자가 요청할 때만 채운다. 기본은 탭 버튼, 패널(`<section id="tab-simulator|tab-qa">`), `tab-intro`(h2 + 한 문장), `.section.section-empty` placeholder 한 장("이 탭은 별도 요청 시 작성됩니다")이다. `simulator_spec.md`, `qa.json` 없이 빌드할 수 있어야 한다. ①′ Paper Study의 `tabs_data/study.json`(Stage 11)은 **기본 빌드 필수**다. study.json이 없을 때 빌더가 그리는 자동 셸은 개발 중 "작성 전" 임시 상태일 뿐 산출물이 아니다(`tools/check_paper_structure.py`가 FAIL).

### 디자인 토큰

v4 토큰 정본은 `rules/design_v4_dashboard.md`다(`--bg:#fafbfc`, `--accent:#5e6488` 등). near-white 배경에 소프트 파스텔을 쓰고, deep tone(`--accent`·`--azure`·`--rose`)은 글자·보더 전용이며 box 배경에는 `*-soft`나 `--paper`를 쓴다. 폰트는 시스템 sans 스택(`-apple-system,…,"Malgun Gothic"`)이고 serif(Georgia) 제목은 금지, 수식 블록은 밝은 회색(`#f1f2f7`)이다. 로고는 `samples/design/acas-logo.png` base64. v3 토큰은 `_build.py`의 중간 산물에만 남고 restyle 후 최종 산출물에 남으면 안 된다.

### 무리한 한국어 변환 금지

번역과 Claude가 쓰는 모든 한국어 prose에 적용한다. 해당 분야 한국 학계에 굳어진 표기(`config.json#domain.term_style`)가 없으면 영문 그대로 둔다. 신조어·음역어를 만들지 않는다. 금지 예: `거친 데이터셋`, `이진 투표`, `워밍업 파인튜닝`, `고충실도`, `강한 정렬`, `순위화`. 허용 예(AI/CS): 어텐션, 파인튜닝, 임베딩, 그래디언트, 프루닝, 어블레이션. 자가 점검: "이게 그 분야 한국어 발표에서 자주 듣는 표현인가?" 전체 표·정규식: `prompts/03_translation.md`.

### 감성 온도 0 · 논리 최대

번역을 제외한 Claude의 모든 한국어 서술(②③④ 카드, study.json, 해석·초보자 해설·학습 가이드·콜아웃, ⑤⑥, 메모 Q&A, Study 검토)에 적용한다. 근거 → 함의의 논리 사슬로 쓰고, 감탄·평가 수식어(`흥미롭게도`, `놀랍게도`, `인상적인`, `우아한`, `훌륭한`, `압도적인`), 응원체(`~해봅시다`, `걱정 마세요`), 과장 부사(`정말`, `굉장히`, `엄청난`), prose 내 이모지·느낌표를 쓰지 않는다. 분석적 형용사(비대칭·준최적·직교·단조)는 유지한다. 검사: `tools/tone_lint.py`(`--fix`는 안전 치환만).

### 평문 필드와 HTML 필드

빌더는 필드마다 이스케이프 여부가 다르다. **태그는 HTML 필드에만 쓴다.** 평문(esc 적용): `quizzes[*].q`, `questions.cards[*].rows[*].q`, `study_modals[*].title`, `study_modals[*].nums[*]`, 카드류 `title`/`lead`/`tag`/`label`/`caption`, `evidence[*].label`, 문장 `original`. HTML(raw 삽입): `body`, `a`, `intuition`, `where`, `interpretations`, `beginner_notes`, `study_modals[*].{look,author,check[*]}`, `callouts[*].text`, diagrams `caption`, 그리고 CARES 계보 빌더의 `translation`. 평문에 엔티티를 쓰면 이중 이스케이프된다. 원문 꺾쇠 기호는 HTML 필드에서 `&lt;…&gt;`, tex 부등호는 `\lt`(`rules/math_rules.md`).

### Paper Study 탭

`tabs_data/study.json`(필수, 작성 규칙 `prompts/11_paper_study.md`, 컴포넌트 `rules/component_rules.md` §17)으로 만드는 7-Step 워크북이다. Claude 분석은 소프트 잠금("분석 비교하기")으로 접어 두고, Step 4·5는 사용자가 먼저 쓴다(설명 문구는 두지 않는다). Step 5의 Claude 분석은 Discussion을 인용하지 않는 데이터-only 결론이고, 저자 주장은 Step 6에서 support/partial/beyond로 판정한다. 모든 주장에 `.ev-chip` 근거(sentence_id·자산 id)를 단다. `phase2.method.claude_html`, `phase2.conclusion.claude_html`은 필수다. 메모·서술은 localStorage + 내보내기(`study/`), 형광펜(`hl:*`)은 영구, 단락 읽음(`read:*`)은 세션 한정.

### 메모 상시 접근 레이어

학습 메모(`.memo-fab`·`.memo-drawer`, z-index 2400)는 라이트박스(2000)·노트 선택(1700)·학습 가이드 드로어(1600)·자산 뷰어(1500)·플로팅 리더(1450) 위에서도 쓸 수 있어야 한다. z만 올리지 않고 가로 자리도 배분하되, 남는 폭이 읽을 수 있을 때만 좁힌다. 가이드와 메모는 뷰포트 700px까지 나란히 서고(가이드는 메모에 덮이지 않는다), 자산 뷰어는 이미지 칸이 `min(360px, 이미지 필요 폭)`보다 좁아지면 세로 적층(이미지 → 캡션·번역 → 해석)으로 바뀐다(v7 — 캡션을 감추던 이미지 전용 모드 폐기). 닫기는 ×·ESC·메모 바깥 두 번 클릭. 키·클릭은 메모 안에 가둔다. 도구 `memo_layer_fix.py`(restyle 이후), 검사 `check_memo_layer.py`(1600·1080·950px).

### 메모 → ⑥ Q&A 생성 · Study 답변 검토 (로컬 브릿지)

메모 드로어의 "Q&A 생성" 버튼과 Paper Study의 "검토 결과 파악하기" 버튼은 로컬 브릿지 `tools/qa_bridge.py`(127.0.0.1:8787, 헤드리스 `claude -p`)를 거친다. 버튼은 빌드 후 `qa_button_inject.py`·`study_review_inject.py`로 주입하고, ⑥ 실제 채움은 사용자가 누를 때 온디맨드다. Q&A 카드 수 상한은 없고 관련 메모 항목을 한 카드로 묶는다(정본 `prompts/10_qa.md` § 군집화). 메모 원문은 어떤 경우에도 지우지 않는다. 브릿지 자동 시작은 `qabridge://`(최초 1회 `python tools/qa_bridge_register.py`).

### Stage 2 완전성

`structured.json`은 원문을 요약하지 않는다. 본문(Abstract → Conclusion)의 모든 섹션·subsection·마침표 단위 문장을 1:1로 보존한다(Related Work·Implementation Details·짧은 메타 문장 포함, 두 문장을 한 sentence_id에 묶지 않음, contribution bullet은 각각 별도 id). 의도적 제외는 부록(인용하지 않을 때)·Acknowledgments·References뿐이다. 정본 도구 `tools/structure_paper.py`로 만들고 fulltext와 섹션·subsection·문장 수를 대조한다(`prompts/02_structuring.md`). 영문과 번역은 sentence_id 1:1이며, 근거 칩·형광펜이 붙은 뒤에는 sentence_id를 바꾸지 않는다.

### Study Modal

자산마다 `.study-fab` 버튼이 오른쪽 사이드 드로어(폭 약 440px, 풀스크린 모달 아님)를 연다. `analysis.json#study_modals[aid]` = `{title, look, nums(3개 이상), author, check(2개 이상)}`의 4섹션(s-look·s-num·s-author·s-check)이고, `nums` 항목은 `{label, value, note?}` 객체 또는 `[label, value]` 쌍이다(문자열은 `"label: value"`로만 받는다). 카드 하단의 해석·초보자 해설을 복제하지 않는다. study-fab 클릭은 `stopPropagation + preventDefault`로 라이트박스와 분리한다. 정본: `rules/component_rules.md` §12.

### Vector PDF 자산 크롭

자산 PNG는 `tools/autocrop_assets.py`로 자동 크롭하고 `--verify`로 잘림을 점검한다. 좌표를 손으로 추측·하드코딩하지 않는다. 캡션 위치는 학회 이름으로 추정하지 않고 자산마다 확인하며, 표의 zero-thickness ruling line도 콘텐츠로 보존한다. 자른 PNG를 모두 직접 열어 헤더 누수·캡션 잘림·sub-panel 누락·본문 섞임을 확인하고, 어긋나는 자산만 수동 보정한다. OCR 스캔본은 `tools/crop_assets.py`. 자산 id는 `fig_N`, `table_N`, `box_N`만 쓴다. 알고리즘: `rules/parsing_rules.md` §4-A.

### 자산 등장 순서

① 탭의 자산은 원본 번호 순서로 놓는다(`fig_1 → … → fig_N`). 부록 그림은 본문 마지막 그림 뒤에 둔다. 개념적 관련성과 충돌하면 번호 순서가 우선이고 cross-reference는 해석·학습 가이드에서 푼다. 예외는 `config.json#meta.asset_order_note`에 이유를 남긴다(`rules/parsing_rules.md` §3-2-bis).

### Dissection Summary 카드

마지막 카드 `diss-summary`는 9행(한 줄 · 이게 왜 문제인가(Problem) · 저자의 핵심 관찰(Observation) · 기존 방법은 왜 부족한가(Gap) · 어떻게 해결했나(Method) · 다른 논문과 무엇이 다른가(Novelty) · 효과 - 숫자(Results) · 한계와 의미(Limitations & Implication) · 30초 요약(For Beginners), 태그 표기는 `prompts/04_research_analysis.md` 표 그대로)과 헤더 아래 한 장 인포그래픽으로 구성한다. 기준은 "논문을 안 읽은 사람도 이 카드 한 장으로 이해"(행당 300~600자). 이미지는 `assets/generated/dissection_overview.png`(1536×864, 5단)이고, codex를 쓰지 않으면 기준 빌더가 summary 카드의 `overview` 데이터로 결정적 SVG를 그린다. 빌더에 이미지 분기가 없는 구세대 산출물은 `tools/overview_inject.py`(재빌드 후 다시 실행).

### Dissection 카드 레이아웃

모든 dissection 카드는 단일 컬럼(`.diss-grid{grid-template-columns:1fr}`)으로 쌓고, row는 태그 위·본문 아래로 적층한다(`.diss-row{display:flex;flex-direction:column}`, `dd.diss-body{margin-left:0}`). `.diss-tag`는 pill 5속성(`align-self:start`·`justify-self:start`·`width:max-content`·`white-space:nowrap`·`line-height:1.4`)을 유지한다. 정본: `rules/component_rules.md` §15·§16.

### Image Lightbox

모든 콘텐츠 이미지(`.asset-image-wrap img`, `.diss-overview-figure img`, `.concept-figure img`)는 클릭하면 비율을 유지해 확대된다(BODY 끝 `.img-lightbox` 하나, 휠 줌 0.5~8x, 확대 시 드래그, 더블클릭 1x↔2.5x, ESC, `+`/`-`/`0`). `@media print`에서 lightbox·드로어·to-top은 숨긴다. 정본: `rules/component_rules.md` §13.

### 자산 임베딩 정책

원본 그림·표와 생성 이미지를 예외 없이 base64로 HTML에 넣는다. 파일 한 장으로 어디서든 열려야 하며, 용량(15MB 이상 포함)을 이유로 외부 참조로 바꾸지 않는다. 외부 참조는 개발 중 미리보기에서만 허용한다.

### 이미지 생성 모드 (A codex PNG / B Claude SVG)

학습 보조 이미지(② ~ ⑥ 탭, ① 제외)는 두 모드 중 하나로 만든다. 모드 A = Claude가 Bash로 codex CLI ImageGen을 호출해 PNG(기본, codex 설치·로그인 전제). 모드 B = Claude가 외부 도구 없이 인라인 `<svg>`를 직접 작성(codex 미설치 폴백 또는 벡터 도식이 더 맞을 때, v4 토큰 사용). CLI는 사용자 지시("codex로"/"SVG로")를 따르고 지시가 없으면 codex 가용 시 A, 없으면 B로 폴백한다. 웹은 매 메시지의 `[이미지 생성 모드: codex|claude_svg]` 태그를 따른다. 저장은 `assets/generated/`(prompt·원본 보존), 임베드는 `<figure class="concept-figure">`. 정본: `rules/component_rules.md` §11.9.

### codex ImageGen 6계명

모드 A 호출 형식: ① Bash 툴 사용(PowerShell 5.1은 한글을 CP949로 깨뜨림) ② prompt.txt는 UTF-8, codex 인자는 그 파일을 읽으라는 ASCII 한 줄 ③ stdin은 `< /dev/null` ④ 풀 블리드 명시, "NOT a transparent cutout" ⑤ 출력 절대 경로와 해상도(WxH) 명시 ⑥ 마지막 줄에 `NO paper title at top, NO standalone header, NO author names.` 병렬 호출은 `--cd`로 디렉토리를 격리하고, 프로세스 종료 후 수거해 md5로 대조한다. 호출 형식: `rules/component_rules.md` §11.

### prompt.txt 본문

그림의 정보량은 프롬프트 본문이 결정한다. 필수 5블록(캔버스·레이아웃·패널 명세·팔레트·스타일+6계명), 패널마다 시각 형태·실제 수치·영어 캡션 3요소, 표의 셀 값은 행별로 전부 나열한다. 밀도 등급: overview 15~20 패널, 개념도(1024×1024) 5~9 패널, qa 3~5 패널. `check_image_prompts.py`를 호출 전에 돌린다(선택: `.claude/settings.json` PreToolUse 훅 + `tools/hook_precheck_codex.py`로 자동 차단 — 키트는 훅 스크립트만 동봉). 생성 직후 PNG를 Read로 열어 §11.8.6 체크리스트를 확인하고, 미달이면 프롬프트를 고쳐 재생성한다(같은 프롬프트 재시도 금지, 재생성 전 최선본 백업). 사용자 검수는 사후다. 정본: `rules/component_rules.md` §11.8, 밀도 예: `samples/cares/assets/generated/prompt_dissection_overview.txt`.

### web↔CLI 결과 통일성

같은 논문을 CLI와 웹 대시보드(`webapp/`)에서 빌드해도 구조가 같아야 한다. 결정적 단계는 반드시 정본 도구를 그대로 호출한다: 구조화 `structure_paper.py`, 크롭 `autocrop_assets.py`, 조립 `_build.py`(기준 `templates/paper_base/`) → `restyle_dash_v4.py` → 주입 체인, overview는 codex PNG를 커밋하거나 빌더의 결정적 SVG. 생성적 단계는 같은 sentence_id 집합 전체를 1:1로 채우고 같은 카드 스키마·규칙을 따른다(차이는 prose wording에 한정). 웹 런처(`webapp/backend/runner.py#WEBAPP_APPEND`)도 같은 도구를 강제한다.

### 논문 소개 영상

연구 다큐멘터리형: 내레이터 한 명(`tools/video/voices/f_narrator_high_calm.mp3`)이 3인칭으로 설명하고, 저자 목소리(`m_quote_mid_calm.mp3`)는 번역본 문장 인용으로만 나온다. 프롤로그(주인공 예시의 실패) → 본 장 6~9개 → 에필로그(HTML 길잡이), **10:00~15:00, 학부 3~4학년 눈높이**(식 1개, 컷당 숫자 2개 이하, 용어 첫 등장 풀이). 영상은 그 논문만 다루고 사용자 자신의 연구 가설·시사점을 넣지 않는다. 도형 설명은 motion-broll 클립, 실제 자료는 최고 해상도 원본, 입력 이미지는 논문 자료 → codex 예시 사진 → 샘플 데이터셋 순서(도형 대체 금지, "예시 사진" 표기). **Stage 13 전에 `.claude/skills/motion-broll/SKILL.md`가 없으면 `skills/motion-broll/`을 `.claude/skills/motion-broll/`로 복사해 설치한다**(`make_video.py - doctor`가 자동으로 한다). 검사 `tools/video/check_video.py`. 정본: `rules/video_rules.md`.

### 코퍼스 내 교차 참조 금지

각 논문은 그 논문의 표와 수치로 완결한다. 다른 논문을 폴더 번호로 끌어오지 않는다(예외: 그 논문이 직접 인용하는 연구명, 사용자가 명시한 후속 연구 안내). 검출: `grep -E "[A-Za-z][A-Za-z0-9-]+\((papers )?[0-9]{1,2}\)"`(`check_paper_structure.py`가 summary 카드에서 잡는다).

## 디렉토리 구조

```
paper-review-kit/
├── papers/        논문별 데이터 + 자산 + 산출물 (폴더명 = N. shortname, 배포본은 비어 있음)
├── prompts/       단계별 프롬프트 01~13 (파일 번호 ≠ Stage 번호 — workflow.md 머리의 대응표)
├── rules/         디자인·분석·컴포넌트 규약, domain_profile.md, project_policies.md(정책 상세), build_lessons.md(빌드 교훈)
├── templates/     기준 빌더 paper_base/ (_build.py · _mk_corpus.py · README.md · video/ 영상 뼈대 — 신규 논문은 여기서 복사)
├── samples/       정본 (수정 금지) — cares/(v4 8탭 + Paper Study 워크드 예제) + design/(로고) + README.md(세대 히스토리)
├── tools/         도구 31개 .py + qa_bridge_start.bat (순서는 workflow.md Stage 10) · video/ 영상 파이프라인(.py 9 · .mjs 2 · fonts/ · voices/)
├── skills/        motion-broll/ 스킬 배포본 (영상 클립 엔진, MIT) → 설치 위치 .claude/skills/motion-broll/ (git 제외)
├── webapp/        웹 대시보드 (backend/runner.py가 CLI와 같은 빌드 규칙을 프롬프트로 강제)
├── setup/         Windows 더블클릭 설치·실행 스크립트 (0_check ~ 8_install_video)
├── rawpaper/      원본 PDF (저작권상 저장소 제외, 빈 폴더만 포함)
├── docs/          demo/ 예시 영상 발췌(README용)
├── workflow.md    단계별 작업 흐름 (Stage 0~13)
├── research_profile.example.json   Stage 12 템플릿 → 킷 루트 research_profile.json (git 제외)
└── README.md · SETUP.md · GUIDE.html · NOTICE.md · ANNOUNCEMENT.md · requirements.txt
```

### `papers/[name]/` 표준 레이아웃

```
papers/[name]/
├── {ShortName}_output.html  최종 산출물 (8탭, 자산 base64)
├── {ShortName}_video.mp4    소개 영상 (Stage 13) — 입력은 video/ (기획안.md·spec.py·scenes.js·clipspec.py·clips/·assets/, work/는 생성물)
├── _build.py             templates/paper_base 복사본 (+ 선택 _mk_corpus.py, _crop.py)
├── config.json           meta, domain(분야 프로파일), asset_layout, wide_assets, captions(KR), captions_en(EN)
├── analysis.json         callouts, interpretations, beginner_notes, study_modals, quizzes, hotspots
├── structured.json       섹션/문단/문장 단위 본문 (structure_paper.py)
├── translations/         manual.json (sentence_id 1:1 번역), refined.json(선택) · translated.json(선택, 편의용 통합 매핑)
├── assets/               fig_N.png, table_N.png, box_N.png
│   └── generated/        학습 보조 이미지 + prompt_*.txt (또는 *.svg)
├── study/                Paper Study 노트 내보내기 (사용자 파일)
└── tabs_data/            dissection, knowledge, questions, study (+ 선택 hotspots.json, 요청 시 qa.json, simulator_spec.md)
```

### 폴더 명명 규약

- `N. shortname`: 숫자 + 마침표 + 공백 + lowercase_underscore(예: `1. flash_attn`, 공백·대문자·하이픈 금지). N은 `papers/` 안에서 1부터 순차 증가하고, `samples/`는 번호를 차지하지 않는다. 출력 파일은 `{ShortName}_output.html`로 짧게 쓴다(예: `FlashAttn_output.html`).
- 경로에 공백·마침표가 있으므로 항상 큰따옴표로 감싼다. 헬퍼 스크립트는 `Path(__file__).parent` 기준 상대 경로를 쓰고 절대 경로를 하드코딩하지 않는다.

## 이 파일을 고칠 때

- 새 교훈은 여기 쓰지 말고 `rules/build_lessons.md`에 쓴다. 모든 논문에 적용되는 규칙이 될 때만 "빌드 전 점검"에 올리고, 규칙 자체가 바뀌면 이 파일의 요약과 `rules/project_policies.md`를 함께 고친다.
- 웹 빌드 규칙(`webapp/backend/runner.py#WEBAPP_APPEND`, `webapp/frontend/app.js` 기본 빌드 프롬프트)도 같은 내용인지 확인한다. 큰 문서를 스크립트로 덮어쓰지 않는다(Edit 툴).
