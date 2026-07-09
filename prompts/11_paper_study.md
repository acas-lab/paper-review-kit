# Stage 11 — Paper Study (3-Phase 비판적 읽기 워크북)

`tabs_data/study.json`을 작성하는 단계. 산출물은 `tab-study` 탭(Translation과 Paper Dissection 사이)의
콘텐츠가 된다. 탭 등록·라우팅 규약 = `rules/design_v4_dashboard.md` §3-bis, 컴포넌트 정본 =
`rules/component_rules.md` §17, 구현 정본 = `samples/cares/_build.py` + `samples/cares/tabs_data/study.json` (배포본에 동봉된 실제 v4 8탭 정본).

## 이 탭의 성격 — 다른 탭과 무엇이 다른가

Dissection·Background·Diagrams는 Claude의 **완성된 해설**이다. Paper Study는 **사용자가 직접 쓰는
워크북**이고, Claude의 분석은 "내가 쓴 뒤 비교하는 대상"으로만 존재한다. 따라서:

- Claude 분석은 항상 잠금 토글 뒤에 숨는다 (기본 접힘 + 내 답 최소 글자 수 전 비활성).
- 분석의 목적은 "가르치기"가 아니라 **"대조 상대 되기"** — 사용자가 자기 답과 견줄 수 있도록
  구체적 판단과 그 근거(원문 위치)를 명시한다.
- Step 4(방법론 평가)·Step 5(내 결론)는 사용자가 AI 없이 직접 수행하는 것이 원칙이며,
  UI가 이를 소프트하게 강제한다.

## 읽기 방법론 원형 (7-Step)

1. **Phase 1 · Aerial View** — ① Abstract와 그림/표부터 훑기 ② 서론 끝에서 연구 질문 찾기
   ③ 알려진 것 / 빈틈 / 채우는 방식 파악
2. **Phase 2 · Interrogation** — ④ 방법론 평가(연구 질문에 맞는 도구인가)
   ⑤ Discussion을 읽기 전에 결과 섹션·그래프만 보고 내 결론 먼저 내리기
3. **Phase 3 · Verdict** — ⑥ Discussion을 읽으며 저자 해석이 데이터와 일치하는지 대조
   ⑦ 다른 무언가가 이 결과를 설명할 수 있지 않은지 대안 탐색

## study.json 스키마

```jsonc
{
  "phase1": {
    "scan": {            // Step 1 — 서술칸 없음, 체크리스트형. 안내 문구(guide) 없음 (2026-07-08 삭제)
      "title": "...",
      "checklist": ["...", "...", "..."],          // 2~4개, 이 논문 맞춤 (범용 문구 금지)
      "assets": ["fig_1", "..."],                  // 전체 자산, 반드시 번호 순 — 클릭 시 도표 뷰어
      "evidence": [{"label": "...", "ref": "p_abs_1_s1"}]
    },
    "rq": {              // Step 2 — 지시 문구 대신 read 패널(단락 칩)로 원문 안내
      "title",
      "read": [{"sec": "s_abs", "label": "Abstract"},
               {"sec": "s_intro", "label": "§1 Introduction"}],
      "placeholder", "min_chars": 30, "claude_html", "evidence"
    },
    "gap": {             // Step 3 — 서술칸 3분할 (합산 글자 수로 잠금 해제)
      "title", "read": [/* 서론(Step 2와 체크 공유)·Related Work */],
      "fields": [
        {"key": "gap_known", "label": "① 이미 알려진 것",  "placeholder": "..."},
        {"key": "gap_hole",  "label": "② 빈틈 — 기존 방법이 못 하는 것", "placeholder": "..."},
        {"key": "gap_fill",  "label": "③ 이 논문의 답",    "placeholder": "..."}
      ],
      "min_chars": 30, "claude_html", "evidence"
    }
  },
  "phase2": {
    "method": {          // Step 4
      "title", "prompt",
      "read": [{"sec": "s_method", "label": "§3 …"},
               {"sec": "s_results", "label": "§4.1 실험 설정", "pids": ["p_r_data", "..."]}],
      "guide_questions": [                          // 3~4개 — 답을 주지 않는 열린 질문 + 단락 리더 버튼
        {"q": "...", "ref": "p_m_label", "label": "§3.2 보기"}   // ref = paragraph id → 플로팅 리더
      ],
      "placeholder", "min_chars": 80, "claude_html", "evidence"
    },
    "conclusion": {      // Step 5 — prompt 없음 (지시문 금지, read 패널이 대신)
      "title",
      "read": [{"sec": "s_results", "label": "§4.2~ 결과", "pids": [/* 4.2 이후만 */]}],
      "result_assets": ["table_2", "..."],         // §4(결과)의 자산만 — 클릭 시 도표 뷰어
      "placeholder", "min_chars": 80, "claude_html", "evidence"
    }
  },
  "phase3": {
    "verdict": {         // Step 6 — 3열 대조 (서술칸·guide 없음)
      "title", "read": [/* §5 Discussion */],
      "claude_dataonly_summary": "<p>…</p>",       // Step 5 claude_html의 3~5문장 압축
      "author_claims": [
        { "match": "support | partial | beyond",   // 데이터 일치 / 부분 일치 / 데이터 너머
          "claim": "...", "note": "...", "evidence": [...] }
      ]
    },
    "alternatives": {    // Step 7 — prompt 없음
      "title", "read": [/* §5(Step 6과 체크 공유)·Limitations */],
      "placeholder", "min_chars": 30,
      "claude_items": [{ "title": "...", "body": "...", "evidence": [...] }]   // 3~5개
    }
  }
}
```

빌더(`guide_p()`)는 prompt/guide가 없으면 지시문 단락을 렌더하지 않는다 — **Step 4의 prompt(가이드
질문 사용법 한 줄)만 유일한 예외**로 유지하고, 나머지 Step은 지시문 없이 read 패널 + placeholder로
말한다.

## 🔴 제목·문구 스타일 (2026-07-08 사용자 확정)

부수적인 설명 텍스트를 넣지 않는다 — 탭 인트로는 h2 한 줄, Phase 밴드는 태그+제목 한 줄, Step은
제목+기능 요소만. 정본 문구 (builder `_build.py`에 고정):

| 위치 | 정본 문구 |
|---|---|
| Phase 1 밴드 | 전체 조망: 논문 흐름 파악하기 |
| Phase 2 밴드 | 심층분석: 방법론과 데이터 파악하기 |
| Phase 3 밴드 | 대조 분석하기 |
| Step 4 제목 | 방법론 평가: 연구도구 파악 |
| Step 5 제목 | 결론 도출하기: Results 분석 |
| Step 6 제목 | 결론 대조 |
| Step 7 제목 | 대안 설명: 다른 설명 찾아보기 |

- Step 제목은 **"핵심어: 부연"** 콜론 형식 (긴 대시-부연 금지). Step 1~3 제목(훑어보기 — Abstract와
  그림/표부터 / 핵심 연구 질문(Research Question) 찾기 / Gap 파악)은 study.json에서 논문마다 동일 유지.
- read 그룹 라벨은 **섹션명만** ("§1 Introduction", "§2 Related Work") — "— RQ는 여기서" 같은 꼬리표 금지.
- 잠금 토글 버튼 라벨은 전 Step 공통 **"분석 비교하기"**.

## 학습 메모 → Q&A 연계 (런타임 기능 — 데이터 준비물 아님)

플로팅 메모·노트 내보내기는 빌더가 자동 생성하는 런타임 기능이므로 study.json에 준비할 것이 없다.
단, 이 Stage의 산출물에 **`papers/[name]/study/` 폴더 생성**(+.gitkeep)이 포함된다 — 노트 내보내기의
권장 저장 위치. 사용자가 메모에 남긴 질문은 ⑥ Q&A 작성 시 1순위 재료가 된다 (`prompts/10_qa.md`
§ 사용자 학습 메모 반영). 단락 읽음 체크(read:*)는 **세션 한정**(sessionStorage) — 노트 파일에만 보존.

### `read` — 본문 보기 패널 (단락 플로팅 리더)

각 Step의 `read: [{sec, label, pids?}]`가 "본문 보기" 패널이 된다. 빌더가 structured.json에서
해당 섹션의 단락을 자동 전개해 **단락 칩**을 만들고, 클릭 시 플로팅 리더(EN·KR 페어 + 콜아웃)가
열린다. 읽은 단락은 ✓ + 그룹 진행률로 표시(**sessionStorage — 세션 한정**, 파일 재오픈 시 초기화,
노트 내보내기/가져오기로만 보존), **같은 pid는 Step 간 체크 공유**.

- `pids`를 생략하면 섹션 전체. 섹션 일부만 필요하면(예: §4에서 4.1만) pids로 지정.
- `sec`는 **structured.json의 실제 section_id**. 서론은 `s_intro` 관례 필수 — Translation 탭의
  "Paper Study로 돌아가기" 버튼이 이 id를 anchor로 삽입된다.
- Step별 표준 배정: Step 2 = Abstract + 서론 / Step 3 = 서론(공유) + Related Work /
  Step 4 = 방법 + 실험 설정 / Step 5 = 결과·어블레이션 / Step 6 = Discussion /
  Step 7 = Discussion(공유) + Limitations.
- **읽기 강도 설계 의도**: 리더가 "그 Step에서 읽어야 할 범위"를 명시하므로, 장황한 지시
  문구 없이도 학습자가 어디까지 읽고 답을 쓰면 되는지 알 수 있다.

`evidence[].ref`는 네 종류 — sentence_id(`p_intro_2_s5` → Translation 문장
amber 하이라이트 3.6초), 자산 id(`fig_3`/`table_2` → 자산 카드 플래시), paragraph id(`p_m_label` →
문단 블록 플래시), **section id**(`s_intro`/`s_method` → 섹션 상단 스크롤 + 헤더 플래시).
모든 점프는 하단 중앙 **"↩ Paper Study로 돌아가기" 플로팅 버튼**을 활성화한다.
**작성 후 모든 ref가 structured.json/asset_layout에 실존하는지 전수 검증할 것** (빌드 후
`data-ev`/`data-read-pid` 대상 존재 체크 — component_rules §17 체크리스트).

### 도표 뷰어용 원문 캡션 — `config.json#captions_en` (의무)

Step 1·5 썸네일 클릭 시 열리는 도표 뷰어는 **이미지 + 원문 캡션(EN) + 번역(KR) + 해석 토글**
4요소를 보여준다. 해석은 `analysis.json#interpretations`를 재사용하고, 두 캡션 필드를 준비한다:
- **`config.json#captions_en` = 영어 원문 캡션** (뷰어 "원문 캡션"). fulltext.txt에서 추출하되,
  PDF 열 흐름이 섞이므로 캡션의 자연스러운 끝에서 수동으로 잘라내고 하이픈 분절(`num- ber`)을 복원.
- **`config.json#captions` = 한국어 번역 캡션** (뷰어 "번역"). 🔴 **기존 `captions`가 영어면 반드시 한국어로
  번역**한다 — 구세대 논문(4~19, 21)은 `parsing_rules.md`의 옛 정의("원문 캡션") 탓에 여기에 영어가 들어
  있다(정본 사례: 21. lv_pruning). 영어 그대로 두면 뷰어 "번역"에 원문이 노출된다. 번역은 `prompts/03`의
  무리한 한국어 변환 금지 정책 적용(ML 표준 용어는 영문 유지). 정정된 규약: `rules/parsing_rules.md` §3-2.
- **검증**: `python tools/check_study_refs.py "papers/N. name"` — 캡션이 순수 영문이면 FAIL.

## 🔴 작성 규칙

### 1. Step 5 "Claude의 데이터-only 결론" — Discussion 인용 절대 금지

이 텍스트는 사용자와 **같은 조건**(결과 표·그림만 본 상태)의 공정한 비교 상대다.

- §5 Discussion/Conclusion의 문장·표현·프레임을 인용하거나 바꿔 쓰지 않는다.
- 근거는 오직 §4의 표·그림 번호. 첫머리에 "Discussion을 인용하지 않고 §4만 근거로 내린
  결론"임을 이탤릭 한 줄로 명시한다.
- 숫자가 지지하는 것과 지지하지 않는 것을 구분한다 — "이 표만으로 말할 수 없는 것"을
  최소 1개 포함 (증거의 한계 명시가 비판적 읽기의 모범).
- 저자가 명시하지 않은 독립 관찰(예: 지표 역전, 비대칭 구조)이 있으면 적극 포함 —
  사용자가 "나도 봤는데" / "이건 못 봤네"를 경험하는 것이 학습 효과의 핵심.

### 2. Step 4 방법론 평가 — 강점·약점 균형 의무

- 구조: 도구–질문 정합성 → 실험 설계의 강점(번호 목록) → 약점과 열린 의문(번호 목록).
- 약점은 **최소 3개**, 각각 "왜 문제인지 + 논문의 어느 부분이 근거인지"까지. 뭉뚱그린
  칭찬("실험이 충분하다")이나 뭉뚱그린 비판("일반화가 부족하다")은 금지 — 반드시 특정
  표/절/수치를 짚는다.
- 저자 스스로 인정한 한계(Limitations)와 Claude가 독자적으로 짚는 약점을 구분해서 쓴다.

### 3. Step 6 author_claims — match 판정 기준

- `support`(데이터 일치): 본문 표·그림이 주장을 정면으로 지지. note에 어느 표가 어떻게.
- `partial`(부분 일치): 주장의 핵심은 지지되나 일부가 측정 밖(설계 속성에서의 추론 등).
- `beyond`(데이터 너머): 실험 수치가 뒷받침하지 않는 전망·확장 주장. 논문 비판이 아니라
  "여기부터는 데이터가 아니라 저자의 해석"이라는 경계 표시다.
- claims는 §5 Discussion(및 Key Takeaways)에서 3~6개 추출, 각각 §5 원문 sentence_id +
  지지/반박 표·그림을 evidence로 단다.

### 4. Step 7 대안 설명 — 흔한 유형 4가지에서 출발하되 논문 맞춤으로

벤치마크/데이터 구성 효과 · 평가 지표의 선택 효과 · 상관의 다른 원인(공유 관행 등) ·
효과의 다른 메커니즘(주장한 이유가 아닌 다른 이유로 같은 결과). 각 항목은 "그 경우 저자의
결론이 어떻게 약화/재해석되는가"까지 한 줄.

### 5. guide_questions·prompt — 답을 흘리지 않는다

Step 4의 가이드 질문은 사용자가 스스로 평가하도록 방향만 가리킨다. "τ=0.85는 임의적이다"
(판정 제공 ✗)가 아니라 "τ=0.85라는 정의는 임의적이지 않은가?"(질문 ✓). placeholder도
문형 힌트만 ("이 방법론의 강점은 … / 약점은 …").

### 6. HTML 이스케이프

claude_html·note·body 안의 수식 표기에서 `<`+영문자 금지 — `&lt;` 사용
(`rules/math_rules.md` § 부등호·꺾쇠). 작성 후 `tools/check_html_escape.py` 실행.

### 7. 한국어 표기

`prompts/03_translation.md` § 🔴 무리한 한국어 변환 금지 전면 적용. supervision·rollout·
ablation·baseline·plug-in 같은 용어는 한국 ML 커뮤니티 표준 표기 그대로.

### 8. 감성 온도 0 · 논리 최대

claude_html·claude_items·note·author_claims 등 모든 분석 서술은 CLAUDE.md "🔴 감성 온도 0 ·
논리 최대" 적용. 감탄·평가·응원·과장 수사(흥미롭게도·훌륭한·우아한·보기 드문·정말·매우 남발 등)
금지 — 근거→함의 논리 사슬만. Step 5 데이터-only 결론과 Step 6 판정 note도 동일.

## 분량 가이드

- rq/gap claude_html: 문단 2~3개 (각 200~400자)
- method claude_html: 문단 3개 (정합성/강점/약점), 합계 900~1500자
- conclusion claude_html: 번호 명제 4~6개, 합계 900~1500자
- author_claims: 3~6개, note 각 100~200자
- alternatives: 3~5개, body 각 150~300자

## 정본 사례

`samples/cares/tabs_data/study.json` (2026-07-08, 이 탭의 첫 적용).
