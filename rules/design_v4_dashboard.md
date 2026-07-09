# Design v4 — Dashboard 스타일 (정본: cares)

**2026-07-02부터 모든 신규 논문 HTML이 따라갈 디자인 정본.** 연구실 실험 대시보드
(`D:/2. 실험/Server/Geollava_Test/실험_대시보드_v3.html`, ACAS GeoLLaVA 관찰연구)의 디자인 체계를
논문 학습 HTML에 이식한 것. 기존 v3(white + lavender, hero 카드 + 숫자 pill 6탭)는 폐기.

> 🔵 **배포 툴킷 참고**: 이 배포본은 **CARES 논문 전체를 `samples/cares/`에 정본으로 동봉**한다
> (실제 데이터·빌더·8탭 산출물 — 유일한 v4 워크드 정본). v4 빌드 경로 = `samples/cares/_build.py`로
> v3 조립 → `tools/restyle_dash_v4.py`로 v4 변환의 2단(§6). 신규 논문은 `samples/cares/`를 복사
> 출발점으로 삼는다.

**정본 파일 (수정 금지 기준, 복사 출발점)**
- 최종 산출물 정본 — `samples/cares/CARES_output.html` (4세대 · v4 8탭 + Paper Study) ✅ 이 툴킷에 동봉
- **빌더 정본 — `samples/cares/_build.py`** (실제 데이터로 8탭+Paper Study 렌더) ✅ 이 툴킷에 동봉
- **변환 도구 정본 — `tools/restyle_dash_v4.py` (범용 · 논문별 수정 0곳)** ✅ 이 툴킷에 포함
  v3 템플릿 `_build.py` 산출물 → v4 변환 (토큰 스왑·topbar·8탭 분리·해시 라우팅 일체).
  헤더 내용은 전부 `config.json#meta`에서 읽는다. (모체의 CARES 전용 `_restyle_dash_v3.py`는
  historical 원형으로 배포본에는 미포함 — 범용 `tools/restyle_dash_v4.py`만 사용한다.)
- 로고 — `samples/design/acas-logo.png` (base64 인라인. 외부 경로 의존 금지 — 도구가 자동 임베드) ✅ 이 툴킷에 포함

---

## 1. 디자인 토큰 (v4 — 저채도 grey-lavender)

대시보드 원칙 그대로: **채도/명도 과하지 않게(쨍한 색 금지), near-white 배경 + 소프트 파스텔
악센트, 여백·라운드.** deep tone은 글자·보더 전용, 배경엔 soft만.

```css
:root {
  --bg: #fafbfc; --paper: #ffffff; --ink: #32363f; --ink-soft: #5e6470;
  --muted: #9aa0ac; --line: #ecedf2;
  --accent: #5e6488;      /* 글자·보더·강조 — indigo-slate */
  --accent-mid: #9398b9;  /* 활성 탭 밑줄 인디케이터 전용 */
  --accent-soft: #f1f2f8; --accent-pale: #d9dce9;
  --azure: #7191ab; --azure-soft: #eaf1f7; --azure-pale: #d5e2ec;
  --rose: #ab8290;  --rose-soft: #f6edf0;
  --mint: #74ad97;  --mint-soft: #edf4f1;
  --amber: #ab8a55; --amber-soft: #f6f1e6;
  --radius: 14px;
  --shadow: 0 1px 2px rgba(48,53,66,.03),0 1px 6px rgba(48,53,66,.03);
  --hero-gradient: linear-gradient(135deg, #eceff5 0%, #e9e7f1 100%);
}
```

폰트: `-apple-system,BlinkMacSystemFont,"Segoe UI","Pretendard Variable","Noto Sans KR","Apple SD Gothic Neo","Malgun Gothic",sans-serif` · 본문 15.5px/1.66 · `word-break:keep-all`.
**Georgia 등 serif 제목 금지** (구 v3의 serif h1~h4는 전부 sans로).

v3 → v4 hex 대응표(구 빌드 변환용)는 `tools/restyle_dash_v4.py`의 스왑 리스트가 정본.

## 2. Topbar — 헤더+탭 단일 응집 상단 바

hero 카드 폐기. 대시보드처럼 **로고 + 3줄 텍스트 + 우측 메타 + 밑줄 탭이 한 덩어리로 sticky**.

```html
<div class="topbar">
  <div class="hdr">
    <div class="brand"><img src="data:image/png;base64,…acas-logo…" alt="ACAS">
      <div>
        <div class="bt">{논문 제목 원문}</div>                <!-- 1줄: 굵게 -->
        <div class="bs">{대표 키워드 · 주제 한 줄}</div>       <!-- 2줄: 작게 -->
        <div class="bs2">{저자 전원 — 소속 기관}</div>         <!-- 3줄: 가장 작게 -->
      </div>
    </div>
    <div class="brand-meta">
      <b>{학회}</b> ({트랙}) · <b>{Oral/Poster 등 상태}</b> · arXiv {id} · 등재 {YYYY-MM-DD}<br>
      코드 <a href="{repo}" target="_blank" rel="noopener">{repo 축약}</a><br>
      생성일 {YYYY-MM-DD}
    </div>
  </div>
  <div class="tabs-row"><nav class="tabs" role="tablist">…8 버튼…</nav></div>
</div>
<main class="app">…</main>
```

- `.topbar{position:sticky;top:0;z-index:60;background:var(--bg);border-bottom:1px solid var(--line)}`
- 활성 탭 = `font-weight:800` + 바 하단 밑줄 인디케이터(`--accent-mid`, 2.5px). 탭 사이 1px 구분선.
- 미채택 논문이면 우측 1줄은 `arXiv preprint {id} · {YYYY-MM} 투고` 형태.
- CSS 전문은 `tools/restyle_dash_v4.py`의 `NEW_TOPBAR_CSS` 블록이 정본.

## 3. 탭 구조 — 숫자 없는 8탭 (Paper Study 포함)

| 탭 ID | 라벨 | 내용 | 기본 빌드 |
|---|---|---|---|
| `tab-reading` | Translation | 원문↔번역 문장 페어링 + 자산 + 학습 가이드 | ✅ 풀 빌드 |
| `tab-study` | Paper Study | 3-Phase 비판적 읽기 워크북 (서술칸·잠금 토글·단락 리더·도표 뷰어·메모) | ✅ 풀 빌드 (2026-07-08 신설) |
| `tab-dissection` | Paper Dissection | 7+1 카드 분석 | ✅ 풀 빌드 |
| `tab-knowledge` | Background | 배경지식 빌딩 블록 + 개념 카드 | ✅ 풀 빌드 |
| `tab-math` | Mathematics | 핵심 수식 (구 ③에서 eq-panel 분리) | ✅ 풀 빌드 |
| `tab-questions` | Diagrams | 비판적 질문 + 도식 | ✅ 풀 빌드 |
| `tab-simulator` | Code | 시뮬레이터·코드 | ⏸ 셸만 |
| `tab-qa` | Q & A | 자가 점검 Q&A | ⏸ 셸만 |

- 라벨에 ①② 같은 **숫자·이모지 붙이지 않는다.**
- 구 ③ "Background & 핵심 수식"은 **Background(빌딩 블록+개념 카드) / Mathematics(eq-panel)로 분리.**
  eq-link 점프 대상도 `tab-math`로 (`targetTabFor('Eq') → 'tab-math'`).
- ⑤⑥ 셸 정책(CLAUDE.md "기본 빌드 범위")은 그대로 유지.

### 3-bis. Paper Study 탭 (2026-07-08 신설 — 정본: cares)

Translation과 Paper Dissection 사이에 놓이는 **자기주도 비판적 읽기 워크북**. 3-Phase 구성:
Phase 1 Aerial View(훑어보기·RQ 찾기·Gap 파악) → Phase 2 Interrogation(방법론 평가·데이터만 보고
내 결론) → Phase 3 Verdict(내 결론 vs Claude 데이터-only 결론 vs 저자 주장 3열 대조·대안 설명).

- **핵심 원칙**: Claude의 분석은 기본 접힘 + 소프트 잠금(내 답 최소 글자 수 전 비활성, "그래도 열기" 우회).
  버튼 라벨은 전 Step 공통 "분석 비교하기", Gap(Step 3)은 서술칸 3분할(합산 글자 수로 잠금 판정).
  Step 4·5(방법론·내 결론)는 AI 없이 직접 쓰는 것이 이 탭의 존재 이유 — 잠금이 이를 소프트하게 강제한다
  (설명 문구·`.ai-note`는 두지 않는다 — 부수 텍스트 금지, 2026-07-08).
- **문장 형광펜**: 리더·Translation에서 문장 클릭으로 하이라이트 토글(EN·KR 쌍 동기, 영구 저장,
  내보내기 포함).
- **본문 보기(read 패널)**: 각 Step 서술칸 직전에 그 Step이 읽을 파트의 단락 칩 — 클릭 시
  탭을 떠나지 않고 플로팅 리더(EN·KR 페어)가 열리고, 읽은 단락은 ✓ + 진행률(n/m)로 기록.
  같은 단락은 Step 간 체크 공유. **체크는 세션 한정**(sessionStorage) — 파일을 다시 열면 초기화,
  노트 내보내기/가져오기로만 보존.
- **근거 점프**: 모든 Claude 분석·저자 주장에 `.ev-chip`(sentence_id/자산 id) — 해시 라우팅(`go()`)
  경유. 점프 후 하단 중앙 `.study-return` 플로팅 버튼 + 서론 끝 `.study-goto` 버튼으로 복귀
  (scrollMem이 위치 기억). 문장 점프는 `.ev-hl` amber 하이라이트(EN·KR 동시).
- **도표 뷰어**: Step 1·5 썸네일 클릭 → 이미지 + 원문 캡션 + 번역 + 해석 토글 플로팅 창
  (`config#captions_en` 필요, 비율 따라 텍스트 하단/우측 자동 배치). 헤더의 `학습 가이드` 버튼으로
  Translation과 동일한 우측 study-drawer 4-섹션 가이드 열람 (뷰어는 왼쪽으로 시프트).
- **학습 메모(플로팅)**: 우측 상단 플로팅 "메모" 버튼(to-top의 x · topbar 바로 아래 y, JS가 위치 계산)
  → 자유 서식 메모장 드로어. 쓰는 대로 자동 저장, 내보내기 `notes.memo`에 포함 — ⑥ Q&A 작성의
  1순위 재료 (`prompts/10_qa.md`).
- **노트 지속성**: 서술칸·메모는 localStorage(`prstudy:{short_name}:*`) 자동 저장. **내보내기 =
  최초 1회 폴더 지정(`study/` 권장, IndexedDB에 핸들 기억) 후 무다이얼로그 파일 저장**
  (`{Short}_study_notes_{YYMMDD}.json`), **가져오기 = 페이지 안 노트 목록 선택창**. 툴바 좌측
  "저장 위치 변경" 텍스트 링크로 폴더 재지정.
- **위치가 dissection 앞인 이유**: Dissection·Diagrams는 Claude의 완성 해석이므로, 스스로 결론을 세우는
  워크북이 그보다 앞에 서야 한다 (스포일러 차단 학습 동선).
- 데이터 = `tabs_data/study.json` (스키마·작성 규칙 = `prompts/11_paper_study.md`).
  study.json이 없으면 `_build.py`가 자동으로 `.section-empty` 셸을 렌더 — 탭 자체는 항상 존재.
- 컴포넌트 상세 = `rules/component_rules.md` §17. 변환 도구는 `tab-study` pane 존재를 감지해
  7↔8탭을 자동 처리(`tools/restyle_dash_v4.py` — study 탭 버튼 삽입 + `studyNav → go` 전환).

## 4. 해시 라우팅 — 마우스 뒤로/앞으로 버튼 지원 (의무)

탭 전환은 `location.hash`를 경유해 브라우저 히스토리에 기록한다. 직접 `activate()` 호출 금지.

```js
const PANE_IDS = Array.prototype.map.call(panes, p => p.id);
function go(tab){
  if (PANE_IDS.indexOf(tab) < 0) tab = 'tab-reading';
  if (('#' + tab) === location.hash) activate(tab);
  else location.hash = tab;            // → hashchange → route() → activate()
}
function route(){
  const id = (location.hash || '#tab-reading').slice(1);
  activate(PANE_IDS.indexOf(id) >= 0 ? id : 'tab-reading');
}
buttons.forEach(b => b.addEventListener('click', () => go(b.dataset.tab)));
window.addEventListener('hashchange', route);
route();
```

- eq/fig/table 크로스탭 점프(`autoLink`)도 `go()` 경유 — 참조 따라간 뒤 뒤로 가기로 복귀 가능.
- 부수 효과: `…html#tab-math` 형태의 탭 딥링크·북마크 가능.
- 탭별 스크롤 메모리(scrollMem)는 기존 그대로 유지.

## 5. 컴포넌트 톤 규칙

- 카드 라운드 22/18px → **`var(--radius)`(14px)**, 큰 보라 그림자 → **`var(--shadow)`**.
- eq-display 다크 블록(#1f1814) 금지 → **밝은 회색**(`#f1f2f7` + `--ink`, 대시보드 `.pipe` 톤).
- 카테고리 색 구분(diss/coach/callout의 mint·amber·rose·azure)은 유지하되 §1의 탈색 값 사용.
- study-drawer·lightbox·to-top·hotspot·recall 등 3세대 인터랙션 컴포넌트는 **기능 그대로**,
  색·라운드·그림자만 v4 토큰으로.
- `@media print`에서 `.topbar` 숨김 (구 `nav.tabs` 대신).

## 6. 빌드 경로

**신규 논문 (권장)** — v3 템플릿 조립 + 범용 변환 도구의 2단:
1. 빌더 `_build.py`를 복사해 데이터(JSON·assets)를 조립한다 (복사 출발점 = `samples/cares/_build.py`).
   **_build.py에서 논문별로 바꿀 곳**: ①~④ 탭의 `tab-intro` 문구(dissection/knowledge/questions),
   footer 한 줄. 출력 파일명은 `meta.short_name`에서 자동 유도(영숫자만 — GeoLLaVA-8K → GeoLLaVA8K_output.html). ③ knowledge intro에는 수식 언급을 넣지 않는다(수식은 Mathematics 탭 — 분리는 도구가).
2. `config.json#meta`에 topbar 필드를 채운다 (도구가 여기서 헤더를 생성):
   `title` `short_name` `authors` `affiliation` (필수) +
   `keyword`(2줄째) · `venue_short` · `status`(Oral 등) · `arxiv` · `listed`(등재일) · `code` · `generated`(생성일).
   미채택 논문은 venue_short~listed를 비우면 `venue` 문자열로 대체된다.
2-bis. **Paper Study 준비물** — `tabs_data/study.json`(Stage 11, `prompts/11_paper_study.md`) +
   `config.json#captions_en`(도표 뷰어용 원문 캡션) + `study/` 폴더(+.gitkeep). study.json이 없으면
   빌더가 ①′를 자동 셸 렌더하므로 빌드 자체는 막히지 않는다.
3. 실행: `python _build.py && python ../../tools/restyle_dash_v4.py "papers/N. shortname"`
   — **논문별 스크립트 수정 0곳.** 도구가 이미 v4인 파일에는 실행을 거부한다(이중 적용 방지).
   ⚠️ `_build.py`만 단독 재실행하면 v3 raw로 돌아간다 — 반드시 변환까지 페어로 실행.

**기존 논문 마이그레이션** — 산출물이 v3 표준 템플릿이면 위 2·3단계만으로 끝
(config meta 필드 보강 → 도구 실행). 앵커가 어긋나는 오래된 빌드(papers 4~19 일부)는
도구의 sub1 실패 지점을 보고 해당 논문의 CSS/마크업을 v3 표준으로 맞춘 뒤 재시도.

**Paper Study 탭 소급 (이미 v4인 논문)** — **범용 도구 `tools/paper_study_retrofit.py "papers/N. name"`**
한 줄로 이식한다(정본 빌더 `samples/cares/_build.py`에서 블록 추출 → 앵커 기반 주입 — 배포본·모체 모두에서 동작). 도구가 **빌더 세대를 자동 감지**한다:
- **GEN B** — CARES 호환(JS-created 학습가이드 modal · `STUDY_GUIDES_PLACEHOLDER` · `JS_FINAL` 조립 · `lb`/`lbCloseFn` lightbox). 예: 22. free, 23. adaptinfer, 25. visiondrop.
- **GEN A** — 구세대(BODY 배치 modal · `__STUDY_JSON__`/`STUDY_DATA` · `lightbox`/`lbOpen`/`lbClose`). 예: 20. sparse_vlm, 21. lv_pruning.

도구 수행: ① 학습가이드 **풀스크린 모달 → CARES 우측 드로어 승격**(CSS+JS+print, 세대별)
② 호버 페어링 요소별 바인딩 → **문서 위임**(리더 복제 문장 대응) ③ Paper Study 12단계(Region A·STUDY_CSS·
모듈 JS·뷰어/리더 마크업·nav·pane·조립 체인, 세대별 앵커) ④ **세대별 변수명 셤**(ASSET_DATA↔ASSET_DATAURI·CAP·INTERPS).

이식 후: Stage 11 데이터(study.json·captions_en·study/) 준비 → `_build.py`+변환 페어 → check_study_refs·check_html_escape.

⚠️ **v3-dict-format config 논문**(asset_layout이 `{aid:{caption,wide}}` dict): study.json 도입 전 config를
v4 list-format으로 마이그레이션(asset_layout 리스트화 + captions 톱레벨 dict화)하고, 빌더의 캡션 조회를
top-level `captions`에서 읽도록 1줄 수정한다(정본 사례: 20. sparse_vlm — `CAPS_KR = config.get("captions",{})`).

정본 소급 사례(모두 2026-07-08): `24. geollava8k`·`25. visiondrop`(드로어 승격), 그리고
`20. sparse_vlm`·`21. lv_pruning`(GEN A) + `22. free`·`23. adaptinfer`(GEN B) — 4편 일괄, 세대 자동 감지.
추가 소급(2026-07-08): papers **4·7~19**(GEN A/B, `paper_study_retrofit.py`) + **5·6 backprop·lenet**
(single-brace 구식 빌더 — raw CSS·함수형 tab_reading·fragment BODY·`__STUDY_DATA__`, 전용 도구
`tools/paper_study_retrofit_groupc.py`로 bespoke 이식). **결과: v4 논문 4~26 전부(23편) Paper Study 완비 + 캡션 KR.**

## 7. 검증 체크리스트 (빌드 후 의무)

1. 인벤토리 자동 검증 통과 — 도구가 **변환 전후 상대 비교**(모든 콘텐츠 수 보존 + 탭 +1: 6→7,
   Paper Study 포함 시 7→8)로 확인.
2. headless 스크린샷: 데스크톱(1440px) + 모바일(400px) — 로고·3줄 헤더·우측 메타·8탭·겹침 없음.
3. `…html#tab-math`·`…html#tab-study`로 직접 열어 해시 라우팅 확인.
4. 임베딩 이미지 ↔ `assets/*.png` 해시 전수 일치.
5. 원문 텍스트 보존: git 이전 버전 대비 문장 샘플 대조 (누락 0).
6. **Paper Study 동작 검증** (`rules/component_rules.md` §17 체크리스트) — 근거·단락 칩 전수
   점프 대상 실존(`data-ev`/`data-read-pid` ↔ `id`/`data-pair`), 서술칸 자동 저장·잠금 해제,
   도표 뷰어(원문 캡션 표시), 플로팅 메모 자동 저장, 노트 내보내기/가져오기 왕복.

> 정본 학습 사례: 이 디자인의 첫 적용이 `samples/cares`(2026-07-02). 같은 세션에서
> ACL 2026 camera-ready(arXiv v3) 콘텐츠 갱신까지 수행 — diff 분석 → 재크롭 → structured/번역
> 증분 갱신 → 재빌드의 전체 사이클이 `_update_aclv3*.py`에 기록돼 있다.
