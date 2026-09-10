# Paper Review HTML Builder

논문 PDF를 **8탭 학습용 HTML**(v4 대시보드 디자인 — Paper Study 탭 포함)로 변환하는 프로젝트.
**대화형(conversational) 작업 방식** — 빌드 스크립트나 파이프라인 자동화 없이, 사람과 Claude가 한 논문씩 함께 만들어 나간다.
JSON으로 정제된 콘텐츠 + 정본 샘플의 디자인 + 규칙 문서를 입력으로 두고, Claude가 그 자리에서 단일 HTML을 작성한다.

---

## 표준 학습 템플릿

모든 논문은 다음 8개 탭으로 구성된다. **신규 논문은 v4 대시보드 디자인(저채도 grey-lavender · topbar · 숫자 없는 8탭 · 해시 라우팅)을 따른다** (정본·전체 규약 = `rules/design_v4_dashboard.md`, 2026-07-02 제정). 이전 v3(white+lavender, hero+6탭)·v2(베이지+마룬)는 폐기. (이 배포 툴킷은 논문 데이터를 포함하지 않는다 — 셸·토큰·인터랙션 정본은 `samples/`에, 빌드/변환 도구는 `tools/`에 있다. 모체 작업 폴더는 papers 1~35 전부 v4 + Paper Study + 학습 메모 완비·캡션 KR(2026-09-02).) 기존 v4 논문에 Paper Study 소급: `tools/paper_study_retrofit.py`(세대 자동 감지 — GEN A/B + lightbox 유무), `tools/paper_study_retrofit_groupc.py`(single-brace 구식 빌더 전용 bespoke). **`_build.py`가 없는 대화형·수작업 빌드**(빌더 기반 소급 불가)에는 빌더리스 직접 주입: `tools/study_inject.py`(CARES Region A 렌더 이식 + 자산 id 소급 + nav/패널/뷰어 주입) + `tools/study_runtime.py`(자립형 런타임 — 근거 점프·플로팅 리더·도표 뷰어·노트 내보내기·형광펜) + `tools/memo_inject.py`(자립형 학습 메모). Stage 11 데이터 + 캡션 번역 후 검증: `tools/check_study_refs.py`(ref 실존 + 캡션 KR — 단, 문장이 structured.json이 아닌 translations/manual.json에 있는 구세대 논문에서는 DOM ref 대조로 대체) · `tools/check_html_escape.py`. LLM 서술 톤 점검: `tools/tone_lint.py`(감성 온도 0 안티패턴 탐지·`--fix`).

**정본 레퍼런스 (수정 금지 — 신규 논문이 따라갈 기준)**
- **디자인 정본 (v4, 신규 논문 기준)** — `samples/cares/CARES_output.html`(4세대 — 대시보드 topbar·숫자 없는 8탭(Paper Study 포함)·해시 라우팅·저채도 팔레트) + **범용 변환 도구 `tools/restyle_dash_v4.py`**(config#meta 기반 — 논문별 수정 0곳). 전체 규약: `rules/design_v4_dashboard.md`
- 인터랙션 세대 (개념 히스토리 — 견본 HTML은 배포본 미포함, `samples/cares/`가 모두 흡수): 1세대 SAFE(셸·문장 페어링) → 2세대 FrameFusion(eq-link cross-tab·hotspot·glossary·사이드바 TOC) → 3세대 SGL(study-fab 자산 모달·3-Part Simulator) → **4세대 CARES = `samples/cares/`가 v4 8탭 + Paper Study로 흡수한 정본**
- 빌더 정본 (대화형 빌드 + 외부 데이터 → 단일 HTML 조립 모범) — `samples/cares/_build.py` + `samples/cares/CARES_output.html` (실제 데이터·8탭·Paper Study 포함 — 배포본 동봉)

| # | 탭 ID | 라벨 (v4 — 숫자 없이 표기) | 내용 | 기본 빌드 |
|---|---|---|---|---|
| ① | `tab-reading` | Translation | 영한 양방향 문장 단위 호버 동기화, 콜아웃, 자산 + 해석 + 초보자 해설 | ✅ 풀 빌드 |
| ①′ | `tab-study` | Paper Study | 3-Phase 비판적 읽기 워크북 (Aerial View → Interrogation → Verdict) — 서술칸 + 잠금 토글 + 근거 점프 | ✅ 풀 빌드 (2026-07-08 신설) |
| ② | `tab-dissection` | Paper Dissection | 연구 동기 · 핵심 관찰 · 차별점 · 방법론 · 실험 검증 · 한계 + 논문 총정리 (7+1 = 8 카드) | ✅ 풀 빌드 |
| ③ | `tab-knowledge` | Background | 배경지식 빌딩 블록 + 개념 카드 | ✅ 풀 빌드 |
| ③′ | `tab-math` | Mathematics | 핵심 수식 (v4에서 ③의 eq-panel을 분리) | ✅ 풀 빌드 |
| ④ | `tab-questions` | Diagrams | 비판적 질문, 도식 | ✅ 풀 빌드 |
| ⑤ | `tab-simulator` | Code | 핵심 알고리즘 시뮬레이터, 의사코드/코드 | ⏸ **셸만** |
| ⑥ | `tab-qa` | Q & A | 자가 점검 Q&A | ⏸ **셸만** |

**v4 탭 규칙** — 탭 라벨에 ①② 같은 숫자·이모지를 붙이지 않는다. 헤더는 hero 카드가 아니라 **로고+3줄 텍스트+우측 메타+탭이 한 덩어리로 sticky되는 topbar**. 탭 전환은 **해시 라우팅**(마우스 뒤로/앞으로 버튼·딥링크 지원). 상세: `rules/design_v4_dashboard.md` §2~4.

### 🔴 Paper Study 탭 — 3-Phase 비판적 읽기 워크북 (정책, 2026-07-08 신설)

Translation과 Paper Dissection 사이의 `tab-study`. 논문을 소설처럼 읽지 않고, **저자(그리고 Claude)의 해석을 보기 전에 내 결론을 먼저 세우는** 자기주도 워크북. Phase 1 Aerial View(훑어보기·RQ·Gap) → Phase 2 Interrogation(방법론 평가·데이터만 보고 내 결론) → Phase 3 Verdict(3열 결론 대조·대안 설명)의 7-Step.

- **잠금 토글("분석 비교하기")**: Claude 분석은 기본 접힘 + 소프트 잠금 — 내 서술칸이 최소 글자 수를 넘어야 버튼 활성("그래도 열기" 우회 링크 존재). Step 4·5는 AI 없이 직접 쓰는 것이 원칙이고 이 잠금이 그것을 소프트하게 강제한다 (설명 문구는 두지 않는다 — 2026-07-08 간소화).
- **Step 5의 Claude 분석은 "데이터-only 결론"** — Discussion을 인용하지 않고 §4 표·그림만 근거로 작성 (사용자와 같은 조건의 공정한 비교 상대). 저자 주장은 Step 6에서 support/partial/beyond 판정 태그와 함께 별도 등장.
- **근거 점프**: 모든 분석·주장에 `.ev-chip` — sentence_id/자산 id로 Translation 탭 해당 위치로 점프 + 하이라이트, 해시 라우팅이라 뒤로 가기로 복귀.
- **메모 지속성**: localStorage 자동 저장 + 내보내기/가져오기 (단일 HTML 특성상 노트는 파일이 아닌 브라우저에 남으므로). 내보내기는 최초 1회 폴더 지정 후 `papers/[name]/study/`에 무다이얼로그 저장.
- **문장 형광펜**: 플로팅 리더·Translation 탭에서 문장 클릭 = 하이라이트 토글 (영·한 쌍 동기, localStorage `hl:*` 영구 저장, 노트 내보내기 포함). 단락 읽음 체크(read:*)는 반대로 **세션 한정** — 파일 재오픈 시 초기화, 노트 파일로만 보존.
- **학습 메모(플로팅)**: 우측 상단 플로팅 "메모" 버튼(to-top의 x · topbar 바로 아래 y) → 자유 서식 메모장 드로어. **어떤 오버레이가 열려 있어도 항상 쓸 수 있어야 한다** (아래 § 메모 상시 접근 레이어). 쓰는 대로 자동 저장(localStorage), 내보내기 JSON의 `notes.memo`(plain text)에 포함되며, **⑥ Q&A 탭을 작성할 때 이 메모의 질문들이 1순위 재료가 된다** (전용 카테고리 "내가 남긴 질문" — 정본 규칙: `prompts/10_qa.md` § 사용자 학습 메모 반영).
- 데이터 = `tabs_data/study.json` (작성 규칙 `prompts/11_paper_study.md`), 컴포넌트 = `rules/component_rules.md` §17, 탭 규약 = `rules/design_v4_dashboard.md` §3-bis. study.json이 없으면 빌더가 자동으로 셸 렌더.
- 정본 사례: `samples/cares` (첫 적용, 2026-07-08).

### 🔴 메모 → ⑥ Q&A 온디맨드 생성 (로컬 브릿지, 2026-07-09 신설)

학습 중 메모 드로어에 남긴 질문으로 **그 자리에서 ⑥ Q&A 카드를 증분 생성**하는 기능. 메모 드로어 안 **"🤖 Q&A 생성" 버튼**(amber `.qa-gen-bar`). 브라우저는 CLI를 직접 못 부르므로 **로컬 다리 서버**를 경유한다.

- **브릿지 `tools/qa_bridge.py`** (사용자가 미리 `python tools/qa_bridge.py` 실행, 기본 `127.0.0.1:8787`, stdlib만): 버튼 → `POST /gen-qa {short, memo}` → 헤드리스 `claude -p`(`--permission-mode acceptEdits --allowedTools Bash Edit MultiEdit Write Read Glob Grep`) spawn → **Stage 9+10 자동 수행**(prompts/10_qa.md 지침대로 qa.json 카테고리 M "내가 남긴 질문"에 append + `<section id="tab-qa">`에 `.qa-mem-card` 주입 + 필요 시 codex 보조 이미지 base64 인라인). 모델 지정 `QA_BRIDGE_MODEL=sonnet`, 권한 우회 `QA_BRIDGE_SKIP_PERMS=1`.
- **증분 + 중복 방지**: `study/.qa_state.json`에 (a) 마지막 메모 sha256 (b) 이미 생성한 질문 원문 목록 기록. 동일 해시면 claude 미실행 `nochange`. 다르면 이미 생성한 질문 목록을 프롬프트로 넘겨 **의미 겹침 dedup + 새 질문만 append**. HTML `data-qid` 레벨에서도 중복 카드 방지. 클라이언트도 djb2 해시로 선차단(+'그래도 다시 생성' 우회). 장부는 카드가 아니라 **메모 항목 단위**로 남긴다(`QA_RESULT.new_cards[].covers` 평탄화 → `generated_questions`).
- 🔴 **카드 수 상한 없음 + 군집화 (2026-09-10, 브릿지 v1.2)**: 이전 프롬프트의 "한 번에 최대 6개" 상한은 성공 시 메모 **전체** 해시가 `processed_hash`로 봉인되는 구조와 결합해, 미뤄진 질문을 **영구히 생성 불가**로 만들었다(papers 26·30이 정확히 6개에서 멈춰 있었다). 상한을 없애고 대신 **관련 있는 메모 항목을 한 카드로 묶어 연결된 설명**으로 답한다 — 한 질문의 답이 다음 질문의 전제가 되도록 논리 사슬로 잇고, 카드가 답하는 메모 원문 질문은 `<ul class="qa-mem-covers">`로 헤더 아래 표시한다(하위 질문 1개면 생략). 억지 병합 금지, 한 묶음이 5개를 넘으면 논리적으로 쪼갠다. 카드 수는 메모의 주제 수가 결정한다. 정본: `prompts/10_qa.md` § 군집화.
- 🔴 **해시 봉인 규칙 — 영구 차단 경로 제거**: `ok`+`deferred==0`이면 `processed_hash` 갱신, `ok`+`deferred>0`(남긴 질문 있음)이면 **갱신하지 않는다**(같은 메모로 다시 눌러 이어받기). `noop`(새 질문 없음 판정)은 `processed_hash` 대신 **`noop_hash`**에만 기록하고, 게이트는 둘 중 하나라도 맞으면 `nochange`를 돌려주되 `reason`으로 구분해 noop 쪽은 '그래도 다시 생성' 우회를 노출한다 — claude의 오판이 그 메모를 영구 차단하지 못하게.
- **자동 JSON 저장**: 생성 직전 메모를 `study/{Short}_study_notes_YYMMDD.json`으로 저장(Stage 9 입력 형식).
- **내용 무손실 + 우아한 실패**: 메모 textarea/localStorage는 절대 비우지 않고 새로고침 전에도 확정 저장. 브릿지가 꺼져 있고 자동 시작도 실패하면 실행 방법 안내(다른 PC의 self-contained HTML에서도 버튼만 무해하게 존재).
- **버튼 클릭 = 브릿지 자동 시작 (`qabridge://` 프로토콜, 2026-07-09)**: 브라우저는 CLI를 직접 못 켜므로, 버튼이 `/ping` 실패를 감지하면 숨김 iframe 으로 `qabridge://start` 를 열고 → Windows 가 `tools/qa_bridge_start.bat`(ASCII 전용 런처)을 실행 → 브릿지 기동 → 클라이언트가 최대 16초 폴링 후 진행. 공용 헬퍼 `window.__qaBridgeEnsure(onReady,onStatus)`(두 주입 스크립트가 가드로 1회 정의)가 담당. **최초 1회 등록**: `python tools/qa_bridge_register.py`(HKCU\Software\Classes\qabridge, 관리자 불필요 · `--unregister`/`--status`). 브릿지는 프로토콜 재실행·URL 인자(`parse_known_args`)·포트 사용중(graceful exit)에 견딤.
- **버튼 주입기 `tools/qa_button_inject.py`**: `.memo-drawer`(자립형·CARES-통합형 공통 DOM)에 런타임 JS로 버튼 + `.qa-mem-*` 카드 CSS를 additive 주입. 헤더 주석으로 구버전 블록을 식별해 **제거 후 재주입(업데이터)** — `--all`로 일괄 갱신. z-index는 드로어(2400) 상속.
- 정본 사례: `samples/cares` (버튼 주입 완료). 배포 킷은 논문 데이터를 포함하지 않으므로, 신규 논문은 빌드 후 `python tools/qa_button_inject.py "papers/N. name"`로 주입. ⑥ 실제 채움은 사용자가 버튼을 눌러 온디맨드.

### 기본 빌드 범위 — ⑤ ⑥은 셸만 (사용자 명시 정책)

신규 논문 빌드 시 ⑤ Simulator & Code, ⑥ 학습 기초 Q & A는 **콘텐츠를 작성하지 않는다**. 사용자가 명시적으로 요청할 때만 별도 작업으로 채운다.

**셸만 빌드한다는 것의 의미:**
- 탭 버튼 (`<button data-tab="tab-simulator|tab-qa">`)은 그대로 유지 (네비게이션 일관성)
- `<section id="tab-simulator">`, `<section id="tab-qa">` 패널 element도 그대로 유지
- `<div class="tab-intro">` 표준 안내 헤더 유지 (h2 + 한 문장 설명)
- 본문은 `.section.section-empty` placeholder 한 장 — "이 탭은 별도 요청 시 작성됩니다" 같은 `.section-empty-note` 한 줄

**이 정책의 효과:**
- Stage 8 (Simulator Design) / Stage 9 (QA Design) 산출물(`tabs_data/simulator_spec.md`, `tabs_data/qa.json`)이 없어도 빌드 가능
- 신규 논문은 ① ~ ④ + ①′(study.json·captions_en)의 데이터가 준비되면 즉시 8탭 HTML 한 장 조립 (Mathematics는 ③ 데이터의 eq-panel 분리라 별도 준비물 없음. study.json이 아직 없으면 ①′는 자동 셸)
- ⑤⑥은 사용자가 그 논문에 대해 깊이 더 들어가고 싶다고 판단했을 때 별도 세션에서 추가

### 디자인 토큰 (정본 — v4 대시보드, 신규 논문 적용)

연구실 실험 대시보드의 저채도 grey-lavender 체계. **쨍한 색 금지, near-white 배경 + 소프트 파스텔 악센트, deep tone은 글자·보더 전용.** 토큰 전문·topbar·8탭·해시 라우팅 규약 = `rules/design_v4_dashboard.md` (정본). 로고 = `samples/design/acas-logo.png` base64 인라인.

```css
:root {
  --bg:#fafbfc; --paper:#ffffff; --ink:#32363f; --ink-soft:#5e6470; --muted:#9aa0ac; --line:#ecedf2;
  --accent:#5e6488; --accent-mid:#9398b9; --accent-soft:#f1f2f8; --accent-pale:#d9dce9;
  --azure:#7191ab; --azure-soft:#eaf1f7; --azure-pale:#d5e2ec;
  --rose:#ab8290; --rose-soft:#f6edf0;  --mint:#74ad97; --mint-soft:#edf4f1;
  --amber:#ab8a55; --amber-soft:#f6f1e6;
  --radius:14px; --shadow:0 1px 2px rgba(48,53,66,.03),0 1px 6px rgba(48,53,66,.03);
}
```

폰트: 시스템 sans 스택(`-apple-system,…,"Malgun Gothic"`) — **serif(Georgia) 제목 금지**. 수식 블록은 다크가 아닌 밝은 회색(`#f1f2f7`).

### 디자인 토큰 — v3 폐기 메모 (2026-07-02)

아래 v3 토큰(white + lavender)은 **빌더 템플릿(`_build.py`류)의 중간 산물 전용**으로만 남는다 — v3로 조립한 뒤 `tools/restyle_dash_v4.py`로 v4 변환하는 2단 파이프라인이기 때문. 최종 산출물에 v3 색이 남으면 안 된다.

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

#### (참고) v2 폐기 메모 (2026-05-09)

(개념 기록 — 견본 HTML은 배포본 미포함) SAFE(1세대)·FrameFusion(2세대)·SGL(3세대)은 원래 warm beige + maroon 팔레트(v2)였고 이후 v3 → v4로 리컬러됐다. 현재 배포본의 색 정본은 v4(`rules/design_v4_dashboard.md`)뿐이다.

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

### 🔴 감성 온도 0 · 논리 최대 — 모든 LLM 서술 prose에 적용 (정책, 2026-07-09 신설)

번역(①)을 제외하고 **Claude가 직접 한국어를 쓰는 모든 자리**(② dissection · ③ knowledge · ④ coaching · ①′ study.json 분석 · figure interpretations · beginner_notes · study_modals · callouts · ⑤⑥ 콘텐츠 · 메모 Q&A · Study 검토 피드백)에 적용. **감성 온도 = 0, 논리적 사고 = 최대.**

**원칙** — 문장은 근거 → 함의의 논리 사슬로만 진행한다. 사실·수치·인과·조건·한계만 남기고, 필자의 감정·감탄·평가적 수사는 제거한다. "이 문장에서 형용사/부사를 빼도 논리가 그대로인가? 그렇다면 뺀다."

**제거 대상 (감성 안티패턴)**
- 감탄·평가 수식어: `흥미롭게도`, `흥미로운`, `놀랍게도`, `인상적인`, `인상적이다`, `우아한`, `우아하게`, `훌륭한`, `강력한`(강조용), `매력적인`, `아름다운`, `보기 드문`, `특히 흥미롭다`, `주목할 만한`, `눈길을 끄는`, `압도적인`
- 응원·친근체: `~해봅시다`, `함께 ~`, `살펴봅시다`, `알아봅시다`, `잘 하고 있어요`, `훌륭해요`, `좋습니다`, `걱정 마세요`
- 과장 강조 부사: `정말`, `매우`(남용), `굉장히`, `엄청난`, `대단히`, `무척`
- prose 내 이모지·느낌표 남발

**유지 대상 (논리 어휘)** — `따라서`, `즉`, `반면`, `그러나`, `조건부로`, `~에 한해`, `~인 한`, `전제`, `귀결`, `반례`, `필요·충분`, `상관 대 인과`. 분석적 내용을 담은 형용사는 감성이 아니므로 유지: `비대칭(구조)`, `준최적`, `직교(적)`, `단조(증가)`.

- **적용 범위**: 신규 논문 생성(위 모든 Stage)에 기본 적용. 정본 사례 `samples/cares`는 이 정책으로 정리 완료(tone_lint 0건).
- 교차 참조: `prompts/03_translation.md`, `rules/analysis_rules.md`, `rules/coaching_rules.md`, `rules/knowledge_rules.md`, `prompts/10_qa.md`, `prompts/11_paper_study.md`.
- 검출·수정 도구: `tools/tone_lint.py "papers/N. name"`(단일) / `--all`(전체 리포트) / `--fix`(안전한 치환만 자동 적용).

### 🔴 메모 상시 접근 레이어 — 어떤 오버레이 위에서도 메모 가능 (정책, 2026-09-02 신설)

학습 메모는 **읽는 도중에 떠오른 것을 그 자리에서 적는** 도구다. 그림을 확대해 놓고, 자산 학습 가이드를 펼쳐 놓고, 플로팅 리더로 문단을 읽는 **그 순간**이 메모가 가장 필요한 순간이므로, 메모는 다른 UI 뒤로 숨거나 그것과 겹쳐서는 안 된다.

- **세로(z-index) 규약**: `.memo-fab` · `.memo-drawer` = **2400** — 라이트박스(2000) · 노트 선택(1700) · 학습 가이드 드로어(1600) · 자산 뷰어(1500) · 플로팅 리더(1450) **위**. (이전 규약 1650은 라이트박스·노트 선택 아래라 불충분했다.)
- **가로(자리) 규약**: z만 올리면 겹쳐 가린다. 그래서 자리도 배분한다 — ① 학습 가이드 **사이드 드로어**가 열리면 메모 버튼·드로어를 그 **왼쪽에 나란히** 세운다. ② 메모가 열리면 전체화면 오버레이(라이트박스·자산 뷰어·플로팅 리더·노트 선택·구세대 `.study-modal`)의 `right` 를 메모 폭만큼 좁혀 겹침을 0으로 만든다(내부 vw 기반 폭도 함께 축소 → 가운데 정렬 유지).
- 🔴 **가로 규약의 상한 — 겹침 0보다 읽을 수 있음이 먼저다 (2026-09-02 추가, v5)**: 위 ①②를 **상한 없이** 적용하면 좁은 화면에서 정작 봐야 할 것이 사라진다. 1080px 에서 가이드(440) + 메모(380) 를 함께 열면 자산 뷰어에 260px 만 남아 내부 `.av-panel` 이 `calc(95vw − 820px)` = 206px 로 뭉개졌다(세로 한 줄). `@media (min-width:1000px)` 게이트는 1080px 을 통과시키므로 방어가 되지 않는다. **뷰포트 폭 상수로 가르지 말고, 남는 폭을 계산해 판정한다.**
  - **판정 기준**: 오버레이가 열려 있으면 `0.95·vw − 예약폭 ≥ 560px`, 없으면 `vw − 예약폭 ≥ 360px`. (오버레이 내부 패널이 vw 의 95% 안에서 다시 좁아지므로 그 몫까지 빼고 본다.)
  - **예약폭**: 나란히 서면 `메모 + 가이드`, 겹쳐 뜨면 `max(메모, 가이드)` — 겹쳐 뜰 때 넓은 쪽(가이드 440)으로 잡아야 가이드가 오버레이 위로 삐져나오지 않는다.
  - **3단 강등**: 나란히 → (자리 없으면) 메모가 가이드 **위에** 뜨고 오버레이는 예약폭만큼만 축소 → (그것도 안 되면) **축소를 포기**하고 메모가 오버레이 위에 뜬다(`body.mlx-float`). 좁혀서 못 읽게 만드는 것보다 낫고, 메모를 닫으면 즉시 원래 폭으로 돌아온다.
  - **CSS 하한**: 모든 `calc(… − var(--overlay-right))` 에 `max(540px, …)`(캡션류 340px) 를 씌워, JS 판정이 한 프레임 늦어도 패널이 하한 아래로 찌그러지지 않게 한다.
  - 측정값(papers 30 · 자산 뷰어 + 가이드 + 메모 동시): 1600px 나란히·뷰어 780 / 1440~1080px 겹침·뷰어 1000~640 / 900px 이하 `mlx-float`·뷰어 전폭. **v4 는 1080px 에서 뷰어 260px 이었다.**
- 🔴 **가이드는 메모에 덮이지 않는다 + 이미지 전용 모드 (2026-09-02 추가, v6)**: v5 는 자리가 부족하면 메모를 가이드 **위에** 띄웠는데, 그러면 정작 학습 가이드가 안 보인다(1080px 에서 가이드 440 + 메모 380 이 그 경우). 두 가지로 푼다.
  - **좁은 화면에서 두 드로어를 함께 줄인다** — 가이드 `clamp(300px, 36vw, 440px)` · 메모 `clamp(280px, 32vw, 380px)` (`vw < 1200` 에서만; 그 위에서는 clamp 상한에 걸려 원래 폭). 나란히 서는 구간이 1440px → 950px 까지 내려간다.
  - **학습 가이드를 열면 자산 뷰어는 이미지 전용이 된다** (`body.mlx-guided`) — 원문 캡션·번역(`.av-text`)을 감추고 `.av-img img{max-height:82vh}` 로 이미지를 키운다. 캡션·번역은 가이드가 이미 담고 있으므로 중복이고, 이미지만 남으면 필요한 폭이 560 → 260px 로 줄어 세 패널이 1080px 에서도 공존한다. **가이드를 닫으면 캡션·번역이 그대로 돌아온다.**
  - 뷰어를 왼쪽으로 미는 논문 자체 규칙(`.av-shift{padding-right:470px}` 고정값)은 실제 가이드 폭(`calc(var(--sd-w) + 22px)`)으로 교정한다.
  - 측정값(papers 30 · 셋 다 열림): 1600px 이미지 647 → **681**(가이드 열면 오히려 커진다) / 1080px 겹침 0 · 패널 291 / 950px 겹침 0 · 패널 260.
- **닫기 규약**: ① × 버튼 ② 메모 안 ESC ③ **메모 바깥 두 번 연속 클릭**(2026-09-02 추가). 한 번 클릭으로는 닫지 않는다 — 그림·문장·가이드를 클릭하며 읽는 도중에 메모가 저절로 사라지면 안 되기 때문. 더블클릭은 `document` capture 에서 받되 `.memo-drawer`/`.memo-fab` 안에서 난 것은 제외하고, 뒤의 가이드·뷰어는 그대로 둔다.
- **키 입력 격리**: 메모에 포커스가 있는 동안 keydown 을 window capture 에서 가둔다. ESC 는 **메모만** 닫고(뒤의 라이트박스·드로어는 유지), 화살표·문자키가 플로팅 리더 이동이나 라이트박스 단축키로 새지 않는다.
- **클릭 격리**: 구세대 자산 해설(`.study-modal`, papers 3·24 계열)은 `document` 에 "바깥 클릭이면 닫는다"를 걸어 두는데 그 바깥에 메모도 포함돼, **메모 버튼을 누르면 해설이 닫혀** 버렸다. 메모 UI 안에서 시작한 click·mousedown 은 `document` 까지 올려보내지 않는다.
- **도구**: `tools/memo_layer_fix.py "papers/N. name"` (견본은 "samples/cares") / `--all` (additive · idempotent · 업데이터). **`restyle_dash_v4.py` 이후, 다른 주입기들과 같은 자리에서 돌린다.**
- **검사**: `tools/check_memo_layer.py "papers/N. name"` (견본은 "samples/cares") / `--all` — 헤드리스 Chromium 으로 bounding box 교집합이 실제로 0인지 측정한다(정적 grep 은 z-index 숫자만 볼 수 있어 "겹치는가"를 못 본다). **1600px(겹침 0) 과 1080px(자리 배분) 두 뷰포트를 모두 돈다** — 좁은 화면 항목은 자산 뷰어 + 가이드 + 메모를 동시에 열고 ① 캡션·번역이 감춰졌는지 ② 메모 ↔ 가이드 겹침 0 · 둘 다 화면 안 ③ 패널 ≥ 260px ④ 한 번 클릭으로는 안 닫히고 두 번 클릭이면 메모만 닫히는지를 확인한다. playwright 없으면 skip.
- **세대 차이 주의**: 자산 학습 가이드가 papers 4~35 는 사이드 드로어(`.study-drawer`)지만 papers 3(SGL)은 **화면을 덮는 `.study-modal`** 이고, papers 1~2 는 아예 없다. 라이트박스 닫기 버튼도 papers 4~25 는 `position:fixed`(뷰포트 기준이라 컨테이너를 좁혀도 안 따라옴), 26~35 는 `absolute`(자동으로 따라옴)로 갈린다. 그래서 도구는 **폭이 뷰포트의 60% 이하일 때만 사이드 드로어로 취급**하고, `position:fixed` 자식은 계산된 스타일로 찾아 직접 밀어준다.

> 🔴 **정본 학습 사례 (회귀의 원인)**: 2026-07-09 의 z-index 1650 수정은 **빌드된 HTML 에만** 적용되고 `_build.py` 템플릿에는 반영되지 않았다. 그 결과 CARES(26) 의 `_build.py` 를 복사해 만든 **papers 27~35 전부가 205/300 으로 회귀**했다(2026-09-02 발견). 교훈: **산출물만 고치고 빌더를 안 고치면 다음 논문에서 그대로 되살아난다.** 이번에 papers 26~35 의 `_build.py` 10개와 `tools/memo_inject.py` 를 함께 고쳐 원천을 막았다.

### 🔴 Study 답변 검토 + 보완 학습 (로컬 브릿지, 2026-07-09 신설)

Paper Study 탭에서 학습자가 쓴 답변(skey: rq·gap_*·method·conclusion·alt)을 study.json 의 Claude 분석과 대조해 **정합도·놓친 관점**을 그 탭 위에서 피드백하고, 약한 부분을 ⑥ Q&A 에 **보완 학습 카드**로 보충하는 기능.

- **버튼**: Paper Study 툴바의 "검토 결과 파악하기"(`#study-review-btn`). 클릭 → `.study-write[data-skey]` 값 수집 → 브릿지 `POST /review-study`.
- **브릿지 `tools/qa_bridge.py`**(`/review-study`): 헤드리스 `claude -p` 가 각 답변을 대응 Claude 분석과 비교 → 단계별 `{match(정합도 0~100), aligned, misread(관점+근거), missing, verdict}` 피드백 JSON 산출 + 약한 skey 에 대해 ⑥ tab-qa 에 카테고리 **W "보완 학습"** 카드를 `data-review-supp` 컨테이너에 **교체 주입**(누적 아님). 마커 `STUDY_REVIEW_RESULT: {...}`.
- **렌더**: 피드백은 `#tab-study` 상단 패널에 즉시 렌더(파일 재작성 없이) + `prstudy:{SHORT}:study_review` localStorage 저장(재오픈 시 복원). 근거는 기존 `.ev-chip`(data-ev) 재사용 → Translation 점프.
- **주입기 `tools/study_review_inject.py`**: 버튼 + 패널 + `.sr-*` CSS 를 additive·idempotent 주입(#tab-study·study-write 있는 논문 대상). 문체는 위 "감성 온도 0" 정책을 따른다.
- 정본 사례: `samples/cares` (첫 적용, 2026-07-09).

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

정본 = `samples/cares/CARES_output.html`의 study-drawer **4-섹션 정형**:
- `s-look` (어디를 먼저 볼까) — 시선 동선 + (다이어그램이면) 박스/화살표/N×/Encoder·Decoder 등 모든 시각 요소의 의미 풀이
- `s-num` (결정적 숫자) — `.study-num-row` ≥3개. 단순 수치 인용이 아니라 그 숫자의 정치적·실용적 함의 한 줄
- `s-author` (저자가 말하는 것) — 이 그림으로 못 박는 명제 1~3개
- `s-check` (학습 체크포인트) — `<ul>` 2~4개. 다시 볼 때 가장 먼저 확인할 부분 / 이 그림이 논문 전체의 무엇을 압축하는지

데이터는 `analysis.json#study_modals[aid] = {title, look, nums≥3, author, check≥2}`. 마크업·CSS·JS 정본: `rules/component_rules.md` §12. 작성 가이드: `prompts/06_figure_interpretation.md` § Layer 3.

**UX — 오른쪽 사이드 드로어 (정책, 2026-05-19 갱신)**: 학습 가이드는 풀스크린 모달(어두운 백드롭 + 중앙 카드)이 **아니라** 오른쪽에서 슬라이드-인되는 폭 ~440px 드로어로 연다. 학습자가 가이드 4섹션을 읽는 동안 정작 봐야 할 figure가 가려지면 안 되기 때문 (24. geollava8k 학습 중 사용자 직접 지적). 드로어 열린 상태에서 figure·문장·lightbox 모두 사용 가능. 닫기는 ① ×버튼 ② ESC ③ 드로어 바깥 클릭 (단 다른 `.study-fab` 클릭은 예외 — 내용 전환 시 깜빡임 방지). CSS·JS 정본 = `rules/component_rules.md` §12.5 / §12.6. 이전 세대(SGL)의 풀스크린 모달 CSS는 폐기됐다 — 현재 정본은 아래 우측 드로어다 (SGL 견본 HTML은 배포본 미포함).

> 안티패턴 (정본이 아닌 잘못된 관성): papers 4~19의 일부 빌드에서 모달이 "캡션 + 전문가 해석 + 초보자 해설" 3-block으로 채워져 figure 하단 내용과 거의 동일했던 경우. 신규 빌드는 4-섹션 정형으로 깊이 분해.

### 🔴 Vector PDF 자산 크롭 — 콘텐츠 인식 자동 bbox 정본 (정책, 2026-06-29 갱신)

자산(figure / table) PNG는 **`tools/autocrop_assets.py`로 자동 크롭**한다. 좌표를 손으로 추측·하드코딩하지 말 것. 한 figure가 수십 개 image object로 분해되는 현대 ML/CV 논문에서 `page.get_image_bbox()` 단독은 실패하므로, 캡션 + **실제 벡터 드로잉(plot 축·화살표·표 ruling line)과 raster image**로 진짜 경계를 계산해 **한 번에 figure·도표 전체**(모든 sub-panel + 라벨 + 캡션)를 잡는다.

```bash
python tools/autocrop_assets.py "rawpaper/<논문>.pdf" "papers/N. name/assets"
python tools/autocrop_assets.py --verify "papers/N. name/assets"   # 여백(잘림) 자동 점검
```

크롭 뒤에는 **반드시 `--verify`로 잘림(여백 없음)을 점검**한다. 도구는 vector bbox로 1차 경계를 잡은 뒤 **픽셀 여백 패스**로 각 변의 실제 콘텐츠 경계를 찾아 균일한 여백을 남긴다(미세 잘림·축 라벨·anti-aliasing 보정). full/single-column 판정은 **배경 패널을 제외한 CORE 콘텐츠**로 한다(국소 배경 패널이 gutter를 넘어 옆 단 본문을 끌어오는 것 방지). 핵심 규칙 (자세한 7단계 알고리즘은 `rules/parsing_rules.md` §4-A):
- 캡션 x-span으로 **column band**(full/left/right) 판별. 캡션 위/아래 어느 쪽에 그래픽이 있는지로 crop 방향 자동 결정 (Figure=아래, Table=위는 관행일 뿐 — FastVLM은 표 캡션이 데이터 아래; 유형으로 단정 금지).
- 표의 **zero-thickness ruling line(가로 rule·세로 separator)도 콘텐츠로 보존** — 버리면 borderless 표가 통째로 사라짐.
- full-width 그림 그래픽이 옆 단 자산으로 누수되지 않도록 캡션 소유 구간 + 중심 y 귀속으로 격리. 적층 sub-panel은 잇고 본문 속 stray는 안 잇는다(패널 높이 임계).
- Page running header(y<56)/footer(y>745) 제외. PDF pt → pixel: `pixel = pt × (DPI/72)`.
- **시각 검증 의무** — 각 PNG를 직접 열어 헤더 누수·캡션 잘림·sub-panel 누락·본문 섞임 확인. 어긋나는 자산만 수동 보정.

정본 구현 = `tools/autocrop_assets.py`. 진단 보조: `tools/detect_assets.py`. 적용 사례: `papers/1. fastvlm/_crop.py`(autocrop 호출 + 사용 자산 선별). 수동 fallback 예시: `samples/cares/_crop.py`.

> 정본 학습 사례 (실패→복구): FastVLM(CVPR 2025) 1차 빌드에서 좌표를 손으로 잡아 **fig_1 위쪽 subplot 잘림 / table_6 캡션만 / table_3 마지막 행만** 잡혔다(적층 패널 gap·zero-thickness rule 탈락·full-width 누수). `autocrop_assets.py`로 12개 figure/table 전부 본체+캡션 완전 캡처. (그 이전 SparseVLM 사례: 페이지 픽셀 좌표 하드코딩 → Figure/Table 다수 잘림·본문 섞임 → 캡션 anchor 재크롭으로 복구.)

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

#### 🔴 이미지 생성 모드 — 두 방식 중 선택 (정본, 2026-06-29)

학습 보조 이미지는 **두 모드 중 하나**로 만든다. 이 선택은 **CLI(터미널)와 웹 대시보드에서 동일하게 작동**한다.
- **모드 A — codex PNG (기본)**: Claude가 Bash로 codex CLI ImageGen 직접 호출 → 래스터 PNG. 아래 6계명을 따른다. 전제: `codex` CLI 설치·로그인.
- **모드 B — Claude SVG (대체·자체 생성)**: Claude가 **외부 도구 없이 인라인 `<svg>` 도식을 직접 작성**. codex 미설치 환경의 폴백이자, 벡터 도식이 더 적합할 때의 선택지. v3 토큰(`fill="var(--accent-soft)"` 등)으로 테마 일관.

**선택 방법** — CLI: 사용자가 "codex로" / "SVG로(자체 생성)"로 지시(무지시 시 codex 가용하면 codex, 없으면 claude_svg 자동 폴백). 웹: 상단 토글에서 선택 → 매 메시지에 `[이미지 생성 모드: codex|claude_svg]` 태그가 붙어 전달됨. 두 모드의 전체 규약·SVG 작성 규칙·공통 임베드(`<figure class="concept-figure">`): **`rules/component_rules.md` §11.9**.

아래 6계명은 **모드 A(codex)** 에만 적용된다 (모드 B는 §11.9의 SVG 규약).

**생성 방식 — Claude가 Bash로 codex CLI 직접 호출** (별도 플러그인·MCP 자동화 없음, Bash 한 줄):

> 정식 호출 형식·검증된 명령 템플릿·`<figure class="concept-figure">` 컴포넌트·자동화 스크립트 골격: **`rules/component_rules.md` §11**. 신규 논문 빌드 전 반드시 통독.

**6계명 — Windows에서 한 번에 통과시키는 *호출* 형식** (생략 시 인코딩/hang/컷아웃/제목 잔존으로 막힘):
1. **Bash 툴 사용** — PowerShell 5.1은 native exe로 한글을 CP949로 깨뜨림.
2. **prompt.txt를 UTF-8로 작성**, codex 인자는 **ASCII 한 줄**로 그 파일을 읽으라는 지시만.
3. **stdin은 `< /dev/null`** — codex가 stdin 입력 대기로 hang하는 것 차단.
4. **스타일 명시** — 프롬프트에 "풀 블리드 일러스트 / 사진, 배경 가득, NOT a transparent cutout" 박아두기. imagegen 기본값이 컷아웃.
5. **출력 경로 + 해상도 명시** — 절대 경로 + WxH (예: `1024x1024`).
6. **이미지 내 논문 제목·헤더·저자명 금지** — prompt.txt 마지막 줄에 `NO paper title at top, NO standalone header, NO author names.`

### 🔴 prompt.txt 본문 작성 = 이미지 품질의 단일 변수 (정책, 2026-08-01)

위 6계명은 **호출**을 안정화할 뿐, 그림의 정보량은 **prompt.txt 본문**이 100% 결정한다. imagegen은 쓰지 않은 것을 채워 넣지 않는다 — 안 적은 패널은 여백이 되고, 안 적은 숫자는 나오지 않는다. 프롬프트는 그려 달라는 요청이 아니라 **완성된 그림을 글로 옮겨 적는 기술(記述)** 이다. 자가 점검: "이 글만 보고 내가 손으로 그릴 수 있는가?"

- **정본 = `rules/component_rules.md` §11.8** — 필수 5블록 구조(캔버스·레이아웃·패널 명세·팔레트·스타일+6계명) / 패널마다 **(시각 형태 + 실제 수치 + 영어 캡션) 3요소** 의무 / 이미지 종류별 밀도 등급 / 병렬 호출 시 `--cd` 격리 / 생성 후 검수 체크리스트 / 실패 모드→처방 표.
- **밀도 등급**: `dissection_overview`(1536×864)는 5단 × 서브패널 3~4개 = **15~20 패널로 최대 밀도**, 개념도(`knowledge_*`/`questions_*`, 1024×1024)는 **논점 하나 · 5~9 패널**, `qa_*`는 3~5 패널. 개념도에 overview 밀도를 넣으면 글자가 뭉개진다.
- **숫자 의무**: "성능이 향상된다" 금지 → 논문 표·그림에서 읽은 실제 값(`12.5% -> 5.1% at L = 192`, `33,000 -> 14,000 -> 3,600`).
- **기계 게이트 (선택)**: 키트에는 훅 스크립트만 들어 있고 `.claude/` 설정은 배포되지 않는다 - 각자 `.claude/settings.json` 에 PreToolUse(Bash) 훅을 걸면 그 훅이 `codex` 호출을 가로채 `tools/hook_precheck_codex.py` → `tools/check_image_prompts.py` 로 프롬프트를 검사하고, FAIL이 있으면 **호출을 차단**한다. 수동 확인은 `python tools/check_image_prompts.py "papers/N. name"` (훅 없이 그냥 돌려도 된다). 캔버스·5단 헤더·본문 수치 개수·분량 하한·`NOT a transparent cutout`·6계명·한자 이물을 기계적으로 잡는다.
- **검수 2단**: ① 생성 직후 Claude가 PNG를 Read로 열어 §11.8.6 체크리스트 확인 → 미달이면 **프롬프트를 고쳐** 재생성(같은 프롬프트 재시도 금지). ② 사용자 검수는 사후.
- 밀도 정본: `samples/cares/assets/generated/prompt_dissection_overview.txt`.

> 정본 학습 사례 (실패→복구): `papers/27. lupi` 1차 생성 시 §11.3의 얇은 스켈레톤을 그대로 따라 단마다 요소를 1~2개만 적어 헐거운 그림이 나왔고, 병렬 호출이 작업 디렉토리를 공유해 다른 프롬프트의 그림이 저장되는 사고도 함께 발생. §11.8 신설·§11.3 스켈레톤 교체·Stage 4 템플릿 교체가 그 직접 결과물이다 (2026-08-01).

**저장**: `papers/[name]/assets/generated/` (prompt 파일·원본 PNG 둘 다 재생성·디버깅용으로 보존).
**최종 HTML 임베드**: 위의 자산 임베딩 정책에 따라 **base64 인라인 의무**. 정본 컴포넌트 = `<figure class="concept-figure">` (§11.5).
**검수**: 2단 — ① Claude 자체(의무): 생성 직후 PNG를 Read로 열어 §11.8.6 체크리스트 확인, 미달이면 프롬프트를 고쳐 재생성. ② 사용자: 사후 — 결과 HTML 보고 마음에 안 드는 이미지 있으면 별도 재생성 요청. **사용자** 사전 검수로 흐름을 막지는 않는다.

---

## 학습 인터랙션 세대 (1 → 2 → 3)

| 세대 | 대표 논문 | 추가된 특징 | 신규 논문에서의 권장 |
|---|---|---|---|
| 1세대 | SAFE | 6탭 골격, 디자인 토큰, 문장 페어링(문단 단위), 의사코드+슬라이더 시뮬레이터 | 최소 베이스라인 |
| 2세대 | FrameFusion | 문장 단위 페어링, `.eq-link` 수식↔본문 cross-tab 점프, `.fig-hotspot` 그림 핫스팟, `.glossary` 호버 툴팁, `#ff-toc` 사이드바 TOC | 기본 적용 |
| 3세대 | SGL | `study-fab` + `study-modal` 자산별 전문가 해설 모달, ⑤ Simulator 3-Part 정형(의사코드 → 인터랙티브 슬라이더 → 좌우 코드 비교), 빌더 없이 대화형으로 직접 작성 | 인터랙션 베이스 |
| **4세대** | **CARES** | 대시보드 topbar(로고+3줄+우측 메타), 숫자 없는 8탭(Background/Mathematics 분리 + Paper Study 워크북), 해시 라우팅(뒤로/앞으로·딥링크), 저채도 v4 팔레트, `_build.py` 조립 → `tools/restyle_dash_v4.py` 변환 2단 빌드 | **신규 논문은 여기를 따른다** |

신규 논문은 3세대(SGL)의 학습 인터랙션(study-drawer·lightbox·hotspot 등)을 유지하면서, 셸/토큰/헤더/탭은 **4세대(CARES) = `rules/design_v4_dashboard.md`**를 따른다.

---

## 디렉토리 구조

```
Paper_review_html/
├── papers/                ← 논문별 데이터 + 자산. 폴더명 = `N. shortname`
│   ├── 1. safe_learning/  · NAACL 2025 (SAFE)            — 1세대
│   ├── 2. frame_fusion/   · ICCV 2025 (FrameFusion)      — 2세대
│   ├── 3. sgl/            · CVPR 2025 (SGL, A Stitch …)  — 3세대 인터랙션 (견본 HTML은 배포본 미포함 — 개념 기록)
│   └── 4. perceptron/     · Psych. Review 1958
├── prompts/               ← LLM 단계별 프롬프트 (Stage 0~12 — workflow.md 참조)
├── rules/                 ← 디자인 / 분석 / 컴포넌트 규약
├── rawpaper/              ← 원본 PDF
├── samples/               ← 정본 HTML (수정 금지) — SAFE(1세대), FrameFusion(2세대), SGL(3세대)
├── tools/                 ← 재사용 도구 (.py 25 + .bat 1 - 주요: crop_assets.py, restyle_dash_v4.py, memo_layer_fix.py, check_html_escape.py, tone_lint.py; 실행 순서는 workflow.md Stage 10 체인)
└── workflow.md            ← 단계별 작업 흐름 (Stage 0~12)
```

### `papers/[name]/` 표준 레이아웃
```
papers/[name]/
├── config.json            · 메타데이터, asset_layout, wide_assets, captions(캡션 번역/KR — 뷰어 "번역"·asset-cap), captions_en(영어 원문/EN — 뷰어 "원문 캡션")
├── analysis.json          · callouts, interpretations, beginner_notes, quizzes, hotspots
├── structured.json        · 섹션/문단 단위 본문
├── translated.json        · 문장 단위 원문/번역 매핑 (선택, 편의용)
├── assets/                · 그림/표 PNG (fig_N.png, table_N.png)
│   └── generated/         · ImageGen으로 생성한 학습 보조 이미지
├── study/                 · Paper Study 노트 내보내기 저장소 ({Short}_study_notes_YYMMDD.json — 사용자 파일)
├── tabs_data/             · 탭별 분석 콘텐츠 JSON
│   ├── dissection.json    · ② 7-카드
│   ├── knowledge.json     · ③ primer + 수식 + 개념 카드
│   ├── questions.json     · ④ 다이어그램 + 4-카드
│   ├── study.json         · ①′ Paper Study 7-Step (RQ/Gap/방법론/데이터-only 결론/판정/대안 + read 배정)
│   ├── qa.json            · ⑥ 카테고리 + 질문 (선택)
│   └── hotspots.json      · 핫스팟 sentence_id 배열 (선택)
└── translations/          · 번역 원본 (manual.json, refined.json)
```

---

## 🔴 web↔CLI 결과 통일성 (정책, 2026-06-29)

같은 논문을 **CLI(터미널에서 Claude Code 직접)** 와 **웹 대시보드(`webapp/`)** 에서 각각 새로 빌드해도 결과가 어긋나지 않도록, 빌드를 **결정적(deterministic) 단계**와 **생성적(LLM) 단계**로 나누고 전자는 정본 도구로 고정한다.

**결정적 단계 = 반드시 정본 도구를 그대로 호출** (같은 입력 → 같은 출력, CLI·웹 동일):
- **본문 구조화(Stage 2)** = `python tools/structure_paper.py "<pdf>" "papers/N. name/structured.json"` — 본문(Abstract→Conclusion) 전체를 컬럼 순서로 1:1 캡처(de-hyphenate·문장 분할·figure 내부 라벨 제외·References/Appendix 중단). **손으로 본문 일부만 담거나 문장을 합치지 말 것** — 이게 "번역 본문 찾기 문제"의 근본 해결.
- **figure/표 크롭** = `python tools/autocrop_assets.py "<pdf>" "papers/N. name/assets"` → `--verify`로 여백(잘림) 점검. 좌표 하드코딩 금지(§Vector PDF 자산 크롭).
- **HTML 조립** = 폴더의 `_build.py`. (정본 = `samples/cares/_build.py`.)
- **dissection 총정리 오버뷰 이미지** = codex로 1회 생성해 `assets/generated/dissection_overview.png`로 **커밋**(그 PNG를 양쪽이 그대로 임베드 → 통일). codex 미사용/실패 시 빌더가 `overview` 데이터로 **결정적 인라인 SVG**를 렌더(§14 / §11.9 mode B).

**생성적 단계 = 공유 규칙으로 구조는 동일하게** (문장 wording은 run마다 다를 수 있음 — LLM 본질, byte 동일은 불가):
- 번역(`translations/manual.json`)은 `structure_paper.py`가 만든 **동일한 sentence_id 전체**를 1:1로 채운다 → 커버리지·구조가 양쪽 동일.
- ② ~ ④ 카드(dissection/knowledge/questions)·analysis는 `prompts/`·`rules/`의 공유 규칙과 무리한 한국어 금지 정책을 따른다 → 카드 스키마·깊이가 동일.

**왜 통일되는가**: 결정적 단계는 byte-identical(이전 검증: 같은 빌드를 웹엔진으로 재실행 시 sha256 일치). 생성적 단계는 같은 sentence_id 집합·같은 카드 스키마를 공유하므로 **구조적으로 동일**하고 차이는 prose wording에 한정된다. 웹 런처(`runner.WEBAPP_APPEND`)도 이 도구 사용을 강제한다.

> 통일성 점검 절차: 같은 PDF로 `structure_paper`·`autocrop_assets`를 양쪽에서 돌려 structured.json 문장 수·자산 PNG가 일치하는지 확인. `_build.py` 출력 HTML의 결정적 부분(셸·CSS·자산 base64)은 동일해야 한다.

---

## 새 논문 추가 — 대화형 흐름

> 빌드 스크립트가 없으므로 명령어 한 줄 빌드는 불가능하다.
> 대신 **Claude와 대화하며 한 단계씩** 콘텐츠를 만들고, 마지막에 HTML 한 장으로 조립한다.

### 폴더 명명 규약 (필수)

논문 폴더는 **`N. shortname`** 형식으로 만든다 — 숫자 + 마침표 + 공백 + 짧은 이름.

- `N` = `papers/` 안에서 **1부터 순차 증가**. 새 논문 = 현재 `papers/`에 있는 가장 큰 N + 1 (배포본은 `papers/`가 비어 있으므로 **첫 논문 = `1. shortname`**). 정본 샘플·워크드 예제(`samples/cares/` 등)는 `samples/`에 있어 papers 번호를 차지하지 않는다.
- `shortname` = lowercase + underscore (`safe_learning`, `frame_fusion`, `sgl`, `perceptron`처럼). 공백·대문자·하이픈 금지.
- 출력 HTML 파일명은 폴더와 별개로 짧게: `{ShortName}_output.html` (예: `5. flash_attn/FlashAttn_output.html`).
- 경로에 공백·마침표가 들어가므로 **모든 경로 문자열은 큰따옴표로 감싸야 한다** (`Path("papers/5. shortname")`, `cd "papers/5. shortname"`).
- 헬퍼 스크립트(`_recrop.py`, `_reembed.py` 등)는 폴더 이름이 바뀌어도 동작하도록 항상 `Path(__file__).parent` 기준 상대 경로를 쓴다 — 절대 경로 하드코딩 금지.

### 단계

1. **PDF → 텍스트 / 자산** — Claude에게 PDF를 주고 텍스트 추출 + Figure/Table PNG 크롭을 요청한다 (PyMuPDF 등). 결과를 `papers/N. shortname/assets/`로 가져옴. OCR'd 스캔본은 `tools/crop_assets.py` 3-pass 알고리즘 사용 — `rules/parsing_rules.md` §4-A 참조, 정본 사례 `papers/4. perceptron/_recrop.py`.
2. **구조화** — `prompts/02_structuring.md` 가이드에 따라 `structured.json` 작성. 섹션/문단 ID 부여.
3. **번역** — `prompts/03_translation.md`에 따라 sentence_id 단위 번역 → `translations/manual.json`. 필요 시 직접 또는 Claude 도움으로.
4. **분석 데이터 작성**
   - `config.json` — 메타데이터, `asset_layout`, `wide_assets`, `captions`(캡션 한국어 번역), `captions_en`(영어 원문)
   - `analysis.json` — callouts, interpretations, beginner_notes, quizzes, hotspots
   - `tabs_data/*.json` — 각 탭의 콘텐츠 (dissection / knowledge / questions / **study** / qa)
5. **HTML 생성** — Claude에게 위 입력 일체와 함께
   - **셸·토큰·문장 페어링·인터랙션·시뮬레이터·자산 모달 패턴** = `samples/`의 정본 3편 (SAFE 1세대 / FrameFusion 2세대 / SGL 3세대)

   을 정본으로 가리키며 8탭 HTML 작성을 요청한다 (최종 디자인 = `rules/design_v4_dashboard.md`, 권장 경로 = `_build.py` 복사 조립 → `tools/restyle_dash_v4.py` 변환). 자산은 base64 인라인. `prompts/08_html_generation.md`와 `rules/component_rules.md`가 디자인 정합 가이드.

---

## 참고 문서

- `workflow.md` — 단계별 작업 흐름 (Cleaning → Structuring → Translation → Research Analysis → Coaching → Figure Interpretation → Background Knowledge → Simulator Design → QA Design → HTML Generation + Stage 11 Paper Study)
- `prompts/01~12_*.md` — 각 단계별 프롬프트 정본 (11 = Paper Study 탭 study.json 작성, 12 = 빌드 완료 논문의 정립·연구 멘토 세션 - 빌드 밖)
- `rules/` — 파싱 / 분석 / 코칭 / 지식 / 수식 / 컴포넌트 규약 (특히 `rules/component_rules.md`가 탭 횡단 공용 컴포넌트 규약을 담는다)
- `samples/` — 정본 (수정 금지) — SAFE(1세대), FrameFusion(2세대), SGL(3세대)
