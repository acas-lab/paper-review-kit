# Domain Profile Rules — 논문별 분야 프로파일 (`config.json#domain`) + 사용자 연구 프로파일 (`research_profile.json`)

## 적용 단계

- **작성**: Stage 1 — Cleaning (`prompts/01_cleaning.md`). Claude 가 PDF 의 제목·초록·venue·키워드로 `config.json#domain` 초안을 쓰고, 사용자에게 **한 번** 확인받는다.
- **소비**: Stage 3 이후 모든 Stage (§5 소비자 표). 한 번 확정된 블록은 이후 어떤 Stage 도 다시 묻지 않고 그대로 읽는다.
- **Stage 12 — 연구 멘토**: 킷 루트 `research_profile.json`(사용자 개인 파일). 논문이 아니라 **사용자의 연구**를 기술한다 (§3).

---

## 0. 왜 필요한가

이 킷은 특정 분야(AI/ML)에 묶이지 않는다. 자연과학·공학·AI/CS·의학·인문사회 어느 분야의 논문이든 같은 절차로 만든다. 분야에 따라 달라지는 것(용어 표기 관행·증거의 종류·대안 설명 축·배경지식 단위·학회/저널 메타)은 `config.json#domain`(정본: `rules/domain_profile.md`)에서 읽어 채운다. 문서 안의 ML 논문 예시는 **예시일 뿐** 규칙이 아니다.

절차(Stage 0~12)·셸(8탭)·컴포넌트는 분야와 무관하게 고정이다. 분야에 따라 갈리는 것은 아래 표의 항목(+ Stage 12 멘토 페르소나)뿐이며, 이것을 프롬프트마다 다시 판단하지 않고 **논문당 한 곳(`config.json#domain`)에 적어 두고 모든 Stage 가 읽는다.**

| 갈리는 것 | AI/CS 논문이면 | 실험과학 논문이면 | 인문사회 논문이면 |
|---|---|---|---|
| 용어 표기 관행 | 어텐션·파인튜닝 음역 표준, 고유 명칭 영문 | 학회 표준 용어는 한국어, 약어·시약·장비명 영문 | 학계 정착 번역어 우선, 원어 병기 |
| "데이터"의 실체 | 벤치마크 표·곡선·ablation | 측정 그래프·스펙트럼·현미경 이미지 | 사료·설문·통계표·텍스트 인용 |
| 대안 설명 축 | 벤치마크 구성·평가 지표 선택 | 시료·측정 조건·교란 변수 | 표본·조작화·역인과·선택 편향 |
| 배경지식 단위 | 추론 루프·토큰·손실 함수 | 실험 흐름·측정 원리·물성 정의 | 이론 계보·개념 정의·방법론 |
| 학회/저널 메타 | 학회 + 트랙 + arXiv | 저널 + 권(호) + DOI | 저널/출판사 + 연도 |

---

## 1. 작성 시점과 절차 (Stage 1)

1. Stage 0 에서 뽑은 텍스트의 **제목 · 초록 · venue(학회/저널/프리프린트) · 키워드 · 섹션 제목** 만으로 초안을 쓴다. 본문 전체를 읽고 나서 쓰는 것이 아니다 — 본문 정독은 Stage 2~4 의 일이고, 프로파일은 그 전에 있어야 용어 표기(Stage 3)가 흔들리지 않는다.
2. 초안을 사용자에게 보여 주고 **한 번** 확인받는다. 형식: 블록 전체 + "추정한 필드: …" 한 줄. 사용자가 고치면 그대로 반영, 답이 없으면 초안을 확정으로 본다.
3. 추정으로 채운 필드는 확인 요청에서 **추정임을 밝힌다** (예: "`venue_type` 은 표지에 학회명이 없어 `preprint` 로 추정"). 비워 두지 않는다 — 빈 필드는 이후 Stage 가 각자 다르게 추측하게 만든다.
4. 확정 후에는 다른 Stage 에서 이 블록을 고치지 않는다. 본문을 읽다가 프로파일이 틀렸다고 판단되면(예: 초록만 보고 `journal` 로 적었는데 실은 학회 논문) 사용자에게 알리고 **그 자리에서 한 번 더 확인**받은 뒤 수정한다.

---

## 2. `config.json#domain` 스키마

`"meta"` 바로 다음에 둔다. 빌더(`_build.py`)·변환 도구(`restyle_dash_v4.py`)는 자기가 쓰는 키만 읽으므로 이 블록이 있어도 없어도 조립은 깨지지 않는다 — 읽는 쪽은 프롬프트(LLM)다.

```json
"domain": {
  "field": "재료공학",
  "subfield": "리튬이온 배터리 양극 소재",
  "venue_type": "journal",
  "term_style": "한국재료학회·전기화학회 관행 — 학술 표기가 굳어진 용어는 한국어, 약어·고유 명칭은 영문 유지",
  "keep_english": ["SEI", "CV", "EIS"],
  "evidence_types": ["XRD 패턴", "SEM 이미지", "사이클 수명 곡선", "EIS 스펙트럼"],
  "alt_explanations": ["시료 준비·합성 조건 차이", "측정 조건(온도·전류밀도)", "교란 변수·비교군 불일치", "다른 메커니즘으로도 같은 곡선이 나오는가"],
  "background_units": ["합성 → 특성 분석 → 전기화학 평가 흐름", "핵심 물성 정의", "측정 원리"],
  "metric_conventions": "용량 mAh/g · 쿨롱 효율 % · 사이클 수"
}
```

### 2.1 필드별 의미

| 필드 | 타입 | 의미 | 채우는 기준 |
|---|---|---|---|
| `field` | string | 대분야. 자유 서술 — `자연과학` / `공학` / `AI/CS` / `의학` / `인문사회` 또는 그 하위(`재료공학`, `경제학`). | 학회·저널이 속한 분과. 학제 간 논문은 **방법론이 속한 분야**를 적고 `subfield` 에 응용 분야를 적는다. |
| `subfield` | string | 세부 주제 한 줄. `·` 로 2~3 항목 연결 가능. | 제목 + 키워드에서. 논문이 답하는 문제가 드러나야 한다 ("배터리" 가 아니라 "리튬이온 배터리 양극 소재"). |
| `venue_type` | enum | `"conference"` / `"journal"` / `"preprint"` / `"book"` / `"thesis"`. topbar 메타 형식이 이에 따라 갈린다 (§2.2). | 표지·푸터·헤더의 게재 정보. 학회 채택본이면서 arXiv 에도 있으면 `conference`. arXiv 만 있으면 `preprint`. |
| `term_style` | string | 이 분야의 **한국 학계에 굳어진 표기 관행** 한 줄. Stage 3 번역과 모든 한국어 prose 의 용어 판단 기준. | "어느 학회 발표에서 이 말을 듣는가" 를 답할 수 있게 쓴다. 학회·표준 용어집이 있으면 이름을 적는다 (대한화학회 명명법, 대한의사협회 의학용어집, 한국경제학회 관행 등). |
| `keep_english` | string[] | 번역하지 않고 **영문 그대로 두는 토큰** 목록. 약어·고유 명칭·모델/장비/시약명. | 초록·키워드에 나오는 약어를 우선 넣는다. 5~15개. 본문을 읽으며 늘어날 수 있으나 Stage 1 확정 목록은 고치지 않고 `prompts/03_translation.md` 의 용어집 쪽에 추가한다. |
| `evidence_types` | string[] | 이 논문에서 "데이터" 라고 부를 것의 실체. Paper Study Step 5(데이터-only 결론)·② 9-row ⑦ 결과·⑥ Q&A 가 **근거로 인용할 대상**. | 논문의 표·그림 종류를 나열. ML 이면 벤치마크 표·곡선·ablation, 실험과학이면 측정 그래프·스펙트럼·현미경 이미지, 인문사회면 사료·설문·회귀표·텍스트 인용. 3~6개. |
| `alt_explanations` | string[] | Paper Study Step 7 대안 설명 축. **기본 4축**: ① 표본/측정 구성 효과 ② 지표/평가 기준 선택 효과 ③ 교란 변수 ④ 다른 메커니즘. | 4축을 이 분야 언어로 바꿔 적는다. ML 의 "벤치마크 구성·평가 지표" 는 ①② 의 ML 사례일 뿐이다. 4개 고정 — 분야 특유의 축이 있으면 4축 중 하나를 대체하지 말고 5번째로 추가한다. |
| `background_units` | string[] | ③ Background 개념 카드의 **단위 후보**. Stage 6·7 이 카드를 자를 때의 기준. | ML: 추론 루프·토큰·손실 함수. 실험과학: 실험 흐름·측정 원리·물성 정의. 인문사회: 이론 계보·개념 정의·방법론(식별 전략). 2~5개. |
| `metric_conventions` | string | ② ⑦ 결과 row·④ 질문에서 숫자를 인용할 때의 **단위·표기** 규약 한 줄. | 논문의 주 지표를 단위와 함께. `%` 인지 `pp` 인지, 로그 스케일인지, 표준오차를 함께 적는지까지. |

### 2.2 `venue_type` → topbar 메타 형식

topbar 우측 1줄은 `config.json#meta` 의 `venue_short` · `status` · `arxiv` · `listed` 에서 만들어진다 (`tools/restyle_dash_v4.py` — 네 키가 모두 비면 `meta.venue` 문자열로 대체). arXiv 는 **선택**이며 ML 관행일 뿐이다. `venue_type` 에 따라 `meta` 를 이렇게 채운다.

| `venue_type` | 우측 1줄 형식 | `meta` 채우는 법 |
|---|---|---|
| `conference` | `{학회} ({트랙}) · {Oral/Poster/Spotlight} · {preprint id}` | `venue_short`=학회+트랙, `status`=발표 형식, `arxiv`=있을 때만, `listed`=등재일(있을 때만) |
| `journal` | `{저널} {권(호)} · DOI {doi} · {게재 연월}` | `venue_short`=저널명+권(호), `status`=`"DOI 10.xxxx/…"`(굵게 렌더됨 — 없으면 생략), `arxiv`=**비움**, `listed`=게재 연월. 또는 네 키를 모두 비우고 `venue` 에 전체 문자열 |
| `preprint` | `{arXiv/bioRxiv/SSRN id} · {v}` | `venue_short`=서버명(`arXiv`/`bioRxiv`/`SSRN`), `arxiv`=id(arXiv 가 아니면 `venue` 문자열로 대체), `status`=`v2` 등 버전 |
| `book` | `{출판사} · {연도} · {장/쪽}` | 네 키를 비우고 `venue` 에 전체 문자열 |
| `thesis` | `{대학} · {학위} · {연도}` | 네 키를 비우고 `venue` 에 전체 문자열 |

`meta.code` 는 URL 이 있을 때만 (`rules/design_v4_dashboard.md` §6 빌드 경로). 데이터·시료·사료 공개 저장소(Zenodo·OSF·ICPSR 등)도 URL 이면 `code` 에 넣는다 — 라벨은 "코드" 로 렌더되지만 링크 기능은 동일하다.

### 2.3 필드가 비어 있을 때

Claude 가 논문에서 추정해 채우고, **추정임을 사용자에게 알린다.** 빈 채로 다음 Stage 로 넘기지 않는다. 사용자가 "모르겠다" 고 답한 필드는 Claude 의 추정을 확정값으로 쓰되 `term_style` 끝에 `(추정)` 을 남긴다.

---

## 3. `research_profile.json` — 사용자 연구 프로파일 (Stage 12)

논문이 아니라 **사용자의 연구**를 기술한다. 킷 루트에 두고 `.gitignore` 에 등록한다(개인 파일). 템플릿 = 루트 `research_profile.example.json`(커밋).

```json
{
  "field": "…", "subfield": "…",
  "big_question": "내 연구가 답하려는 큰 질문 한 문장",
  "hypotheses": [{"id": "H1", "text": "…", "status": "open|supported|refuted"}],
  "axes": ["차별성 축 1", "…"],
  "intervention_points": ["개입 지점 1", "…"],
  "corpus": [{"paper": "papers/1. name", "role": "baseline|evidence|counter", "note": "…"}],
  "qa_log": "research/qa_log.json"
}
```

| 필드 | 의미 |
|---|---|
| `field` / `subfield` | 사용자의 전공. Stage 12 멘토 페르소나 = "이 `field`/`subfield` 를 전공한 박사급 지도자". |
| `big_question` | 연구가 답하려는 큰 질문 한 문장. 논문 정립(A)·차별성 매트릭스(D) 가 이 질문을 기준으로 논문을 배치한다. |
| `hypotheses[]` | 사용자 가설. `id` 는 `H1…`, `status` 는 `open` / `supported` / `refuted`. Stage 12 E 단계가 논문을 이 가설의 근거/반례로 판정한다. 가설이 아직 없으면 빈 배열 — 멘토가 첫 세션에서 함께 세운다. |
| `axes[]` | 선행 연구와의 차별성 축. D 단계 매트릭스의 열. |
| `intervention_points[]` | 사용자가 개입하려는 지점(방법·데이터·평가·이론). C 단계 방법론 해부가 이 지점을 기준으로 논문을 자른다. |
| `corpus[]` | 킷의 `papers/` 에 **실제 있는 폴더만**. `role` = `baseline`(비교 기준) / `evidence`(가설 근거) / `counter`(반례). |
| `qa_log` | Stage 12 세션 Q&A 누적 파일. 킷 상대 경로 `research/qa_log.json`. `research/` 도 `.gitignore`. |

**파일이 없으면**: Stage 12 세션 첫머리에서 사용자에게 `field` · `big_question` · 가설 · 차별성 축을 **질문해 함께 작성**한 뒤 진행한다. 빈 값으로 세션을 시작하지 않는다.

---

## 4. 워크드 예시 세 편

### 4.1 AI/CS 학회 논문 (예: CARES — `samples/cares/config.json`)

```json
"domain": {
  "field": "AI/CS",
  "subfield": "비전-언어 모델 추론 효율화 · 해상도 선택",
  "venue_type": "conference",
  "term_style": "한국 ML 커뮤니티 관행 — 어텐션·파인튜닝·토큰 등은 음역 표준, 고유 명칭은 영문",
  "keep_english": ["VLM", "LLM", "ViT", "token budget", "ANLS", "AnyRes", "dynamic-resolution"],
  "evidence_types": ["벤치마크 정확도 표", "토큰 수-정확도 곡선", "ablation 표", "질의별 선택 해상도 분포"],
  "alt_explanations": ["벤치마크 구성(문서형 QA 편중)이 해상도 민감도를 과장하는가", "평가 지표(ANLS 임계) 선택이 '충분 해상도' 라벨을 바꾸는가", "교사 VLM(Granite-Vision)의 편향이 라벨에 유입되는가", "해상도가 아니라 토큰 수 자체가 정확도를 결정하는가"],
  "background_units": ["VLM 추론 루프(인코더→프로젝터→LLM)", "해상도-토큰 수 관계", "지식 증류·라벨 생성 파이프라인"],
  "metric_conventions": "정확도 % · 토큰 수 · FLOPs"
}
```

topbar: `ACL 2026 (Long Papers) · Oral · arXiv 2510.19496 · 등재 2026-05-31`.

### 4.2 재료과학 저널 논문

```json
"domain": {
  "field": "재료공학",
  "subfield": "리튬이온 배터리 양극 소재 · 표면 코팅 안정화",
  "venue_type": "journal",
  "term_style": "한국재료학회·한국전기화학회 관행 — 학술 표기가 굳어진 용어(양극·전해질·용량 유지율)는 한국어, 약어·시약·장비명은 영문 유지",
  "keep_english": ["SEI", "CV", "EIS", "XRD", "SEM", "NCM811", "LiPF6"],
  "evidence_types": ["XRD 패턴", "SEM/TEM 이미지", "사이클 수명 곡선", "EIS 나이퀴스트 플롯", "율속 특성 표"],
  "alt_explanations": ["시료 준비·합성 조건(소성 온도·분위기) 차이", "측정 조건(온도·전류밀도·전압 창) 선택", "교란 변수 — 비교군의 입자 크기·전극 로딩 불일치", "다른 메커니즘(전해질 분해 억제 vs 상전이 억제)으로도 같은 곡선이 나오는가"],
  "background_units": ["합성 → 특성 분석 → 전기화학 평가 흐름", "핵심 물성 정의(비용량·쿨롱 효율·율속)", "측정 원리(XRD·EIS)"],
  "metric_conventions": "비용량 mAh/g · 쿨롱 효율 % · 용량 유지율 %@N cycle · 전류밀도 C-rate"
}
```

topbar: `J. Power Sources 612 · DOI 10.1016/j.jpowsour.2026.xxxxx · 2026-04` (`meta.venue_short`="J. Power Sources 612", `status`="DOI 10.1016/…", `arxiv` 비움, `listed`="2026-04").

### 4.3 경제학·역사학(인문사회) 논문

```json
"domain": {
  "field": "인문사회",
  "subfield": "경제사 · 19세기 철도 부설과 지역 시장 통합",
  "venue_type": "journal",
  "term_style": "한국경제학회·경제사학회 관행 — 정착된 번역어(시장 통합·고정효과·도구변수) 우선, 계량 약어·사료명은 영문/원어 병기",
  "keep_english": ["DID", "IV", "OLS", "market access", "gazetteer"],
  "evidence_types": ["회귀표(계수·표준오차)", "사료 인용(정부 통계 연보·지방지)", "지도·거리 행렬", "시계열 가격 그래프"],
  "alt_explanations": ["표본 구성 — 철도가 놓인 지역이 애초에 달랐는가(선택 편향)", "조작화 — '시장 통합' 을 가격 수렴으로 잰 것이 결과를 좌우하는가", "교란 변수 — 같은 시기의 행정 개편·항구 개항", "역인과 — 시장 통합이 철도 부설을 불렀는가"],
  "background_units": ["이론 계보(시장 통합 가설·신경제사)", "개념 정의(가격 수렴·거래 비용)", "방법론(DID 식별 전략과 가정)"],
  "metric_conventions": "계수 (표준오차) · 유의수준 * ** *** · 가격 변동계수 · 거리 km"
}
```

topbar: `J. Econ. Hist. 86(2) · DOI 10.1017/S0022050726xxxxxx · 2026-06`.

---

## 5. 소비자 표 — 어느 Stage 가 어느 필드를 읽는가

| Stage / 문서 | 읽는 필드 | 쓰임 |
|---|---|---|
| Stage 1 `prompts/01_cleaning.md` | (작성) | 초안 → 사용자 확인 1회 |
| Stage 3 `prompts/03_translation.md` | `term_style`, `keep_english` | 용어 표기 판단. "해당 분야의 한국 학계에 굳어진 표기가 없으면 영문 그대로" 의 **"해당 분야"** 가 이 필드다. 무리한 한국어 변환 금지 정책의 분야 기준. |
| Stage 4 `prompts/04_research_analysis.md` · `rules/analysis_rules.md` | `evidence_types`, `metric_conventions` | ② 9-row ⑦ 결과 row 의 숫자 인용 단위 · "실험 검증" 카드가 근거로 부를 대상 |
| Stage 5 `prompts/05_coaching.md` · `rules/coaching_rules.md` | `alt_explanations`, `metric_conventions` | ④ 비판적 질문의 축 · 숫자 표기 |
| Stage 6 `prompts/06_figure_interpretation.md` | `evidence_types`, `background_units` | 자산 해석의 "이 그림이 어떤 종류의 증거인가" · study_modals `s-num` 의 단위 |
| Stage 7 `prompts/07_background_knowledge.md` · `rules/knowledge_rules.md` | `background_units`, `term_style` | ③ Background 개념 카드 단위 · `English Term (한글 설명)` 표기의 분야 기준 |
| Stage 9/10 `prompts/10_qa.md` | `field`, `subfield`, `evidence_types` | ⑥ Q&A "분야 기초" 카테고리의 범위 · 답변이 인용할 데이터 종류 |
| Stage 11 `prompts/11_paper_study.md` | `evidence_types`, `alt_explanations` | Step 5 데이터-only 결론의 "데이터" 실체 · Step 7 대안 설명 4축 |
| Stage 12 `prompts/12_research_mentor.md` | `research_profile.json` 전체 + 논문별 `field`/`subfield` | 멘토 페르소나 · 가설 좌표 배치 · 코퍼스 차별성 매트릭스 |
| `rules/design_v4_dashboard.md` · `tools/restyle_dash_v4.py` | `venue_type` (→ `meta` 채우는 법, §2.2) | topbar 우측 메타 형식 |
| `tools/tone_lint.py` | — | 분야 무관. 감성 온도 0 정책은 모든 분야 공통. |

---

## 6. 금지

- 프로파일 없이 Stage 3 이후를 진행하는 것. 없으면 Stage 1 로 돌아가 먼저 만든다.
- ML 관행(어텐션 음역·arXiv id·벤치마크 표)을 다른 분야 논문에 그대로 적용하는 것. 문서의 ML 예시는 `field`=`AI/CS` 일 때의 한 사례다.
- `alt_explanations` 를 4축 미만으로 줄이는 것. 축이 이 분야에 안 맞아 보이면 분야 언어로 **번역**해 적는다 (예: "평가 지표 선택" → 인문사회의 "조작화 선택").
- `research_profile.json` 을 커밋하는 것. `corpus[]` 에 킷에 없는 폴더를 적는 것.
