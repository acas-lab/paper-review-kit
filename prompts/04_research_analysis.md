# Research Analysis Prompt

You are a research paper analyst.

Your role is **NOT to summarize** the paper.
Your role is to **reconstruct the author's research thinking process**.

## Pipeline Position

- **Stage:** 4 (Research Analysis)
- **Input:** `papers/[name]/structured.json`, 자산 PNG, 가능하면 Stage 3 산출물 일부
- **Output (두 갈래):**
  1. `papers/[name]/tabs_data/dissection.json` — **7+1 = 8 카드 구조** (② Paper Dissection 탭). 7-카드(motivation~extend) + 마지막 1-카드(summary, 논문 총정리)
  2. `papers/[name]/analysis.json#callouts` — 문단 단위 강조 박스 (① reading 탭에 인라인)

## Referenced Rules

- `rules/analysis_rules.md`
- `rules/parsing_rules.md`

---

## Goal

다음 6가지 질문에 대해 **저자의 사고 흐름**을 복원한다:

1. What did the author observe?
2. Why did they think prior methods were insufficient?
3. What different idea did they introduce?
4. How did they turn that idea into an actual method?
5. How do experiments validate the claim?
6. What limitations and follow-up questions remain?

기본 인과 사슬:
**observation → dissatisfaction with prior work → new idea → implementation → validation → limits**

---

## Output 1: `tabs_data/dissection.json`

**7+1 = 8 카드 정본 구조.** 1~7번은 사고 흐름 분해, 8번은 그 흐름 전체를 한 카드에 압축한 "논문 총정리"다. 각 카드는 `id`, `cls`, `title`, `lead`(한 줄 요지), `rows`(`{tag, body}` 배열)로 구성된다.

### 카드 8종 (정본 — 클래스명·순서 변경 금지)

| id | cls | title | 핵심 질문 |
|---|---|---|---|
| 1 | `diss-motivation` | Research Motivation | 어떤 문제가 이 연구를 촉발했는가? 왜 이 문제가 중요한가? |
| 2 | `diss-observe` | Author's Key Observations | 저자가 직접 본 현상/병목은 무엇인가? 어느 Figure/Table이 근거인가? |
| 3 | `diss-compare` | Difference from Prior Work | 기존 연구의 가정/방식과 무엇이 다른가? |
| 4 | `diss-logic` | Execution Logic | 핵심 아이디어를 어떻게 메서드로 구현했는가? 컴포넌트별 존재 이유는? |
| 5 | `diss-verify` | Validation Logic | 실험은 정확히 무엇을 증명하려 하는가? 어느 수치가 가장 중요한가? |
| 6 | `diss-risk` | Hidden Assumptions and Risks | 메서드가 작동하려면 어떤 전제가 필요한가? 어디서 무너질 수 있는가? |
| 7 | `diss-extend` | Research Expansion | 자연스럽게 이어지는 후속 질문은? |
| **8** | **`diss-summary`** | **논문 총정리** | **위 1~7을 한 카드에 압축. 9-row 정형 + 한 장 overview 이미지** |

### 8번 카드 — `diss-summary` 세부 규약 (5세대 정본 = `papers/21. lv_pruning`)

> **갱신 정책 (2026-05-12)**: 기존 4-row(관찰/방법/차별/결과) 정형은 **9-row 정형**으로 확장. \"<em>논문 안 읽은 사람도 이 카드 한 장만 보고 충분히 이해할 수 있는 깊이</em>\"가 기준. 기존 4-row paper(SAFE/FrameFusion/SGL/SparseVLM 등)는 점진적 마이그레이션 권장.

마지막 카드는 다른 카드들과 같은 마크업 구조(`diss-card diss-summary` + `diss-step "08"` + `diss-head` + `diss-rows`)를 쓰되, **rows는 다음 9개를 모두 포함**한다.

| # | tag | 내용 |
|---|---|---|
| 1 | **한 줄** | LVPruning이 무엇이고 어떤 효과인가의 단일 명제. 통상 `<strong>...</strong>`로 핵심 한 문장을 박는다. |
| 2 | **이게 왜 문제인가 (Problem)** | 도메인이 처한 상황·왜 이 문제가 중요한가. 정량적 출발 수치를 같이(예: \"576 vision tokens vs 30 text tokens → quadratic attention\"). |
| 3 | **저자의 핵심 관찰 (Observation)** | 본 논문의 출발이 된 통찰 1~3개. 인지과학·이전 연구의 단편을 인용해도 OK. ②번 카드와 중복돼 보이지만 여기는 \"<em>여러 관찰을 하나의 흐름으로</em>\". |
| 4 | **기존 방법은 왜 부족한가 (Gap)** | 비교 대상 갈래(A/B/C)별로 무엇이 부족한지. 단순 단점 나열이 아닌 \"<em>아무도 X+Y를 동시에 안 했다</em>\"의 구조적 빈자리 명시. |
| 5 | **어떻게 해결했나 (Method)** | 핵심 메커니즘을 단계(① → ② → ③)로 나열. 수식 번호·변수·핵심 트릭(예: Gumbel-Softmax, attention masking)을 그대로. 가정/제약(training-free 여부 등) 한 줄. |
| 6 | **다른 논문과 무엇이 다른가 (Novelty)** | 1~3개 차별점을 굵게. \"<em>축이 다르다</em>\" 식의 구조적 차이를 잡는다 — \"layer 진행 중 점진 가지치기 + cross-modal 가이드 + plug-and-play\". |
| 7 | **효과 — 숫자 (Results)** | ① 핵심 절감/정량 수치 ② 비교 baseline 대비 격차 ③ 추가 trade-off 옵션 ④ 자체 overhead. 모든 숫자에 단위 표기 (TFLOPs / %p / × / +N.Np). |
| 8 | **한계와 의미 (Limitations & Implication)** | ablation 부재·단일 base model·real-world 미검증 등 구체적 한계 + \"그럼에도 의미\"의 시사점 한 줄. |
| 9 | **30초 요약 (For Beginners)** | 전혀 모르는 사람을 위한 한 단락. 비유·일상어로 풀어쓰며 학술 용어는 괄호 병기. 다른 row들이 학자 대상이라면 이건 일반인 대상. |

각 row의 `body`는 `<strong>`/`<em>` 활용해 sub-claim을 강조하며 **300~600자**의 풍부한 단락. 다른 7장 카드보다 밀도·길이 모두 높은 종합 글.

**렌더 위치:** 다른 7장과 같은 `diss-grid` 안 마지막 자리(`grid-column:1/-1`로 full-width). 다른 색 카테고리 클래스 없이 `diss-summary` 단독.

### 8번 카드 — 한 장 overview 이미지 의무 (정본 `dissection_overview.png`)

summary 카드 헤더 바로 아래·rows 위에 **반드시 한 장 인포그래픽**을 동봉한다. 이 이미지가 본 논문의 모든 메시지를 5단으로 시각화 — \"<em>이 그림만 봐도 흐름 파악</em>\" 수준.

- **파일명**: `papers/[name]/assets/generated/dissection_overview.png`
- **사이즈**: 1536×864 (16:9 widescreen) 권장
- **5단 구성**: **PROBLEM → KEY OBSERVATIONS → METHOD → WHAT'S NEW → RESULTS** (좌→우)
- **컴포넌트**: `<figure class="diss-overview-figure">` (정본 마크업·CSS = `rules/component_rules.md` §13/§14)
- **임베드**: HTML 빌드 시 base64 인라인. `_build.py`의 `render_diss()`에서 `c["id"] == "summary"` 분기로 헤더 아래·rows 위에 삽입

생성 방법은 다음 \"## 이미지 생성\" 절 참조 (codex CLI, 6계명).

### 스키마

```json
{
  "cards": [
    {
      "id": 1,
      "cls": "diss-motivation",
      "title": "Research Motivation",
      "lead": "한 줄 요지 (1~2문장)",
      "rows": [
        {"tag": "문제", "body": "..."},
        {"tag": "이유", "body": "..."},
        {"tag": "재정의", "body": "..."}
      ]
    }
  ]
}
```

`tag`는 카드별 자유 명명 (예: `Observation 1/2/3`, `Step A/B/C`, `가정 1`, `Q1` 등). 카드 내 일관성 유지.

---

## Output 2: `analysis.json#callouts`

본문을 읽으며 즉시 환기시켜야 할 문단 단위 강조.

```json
{
  "callouts": {
    "p5":  [["warn", "직관에 반하는 핵심 수치 또는 흔한 함정"]],
    "p8":  [["key",  "방법론의 핵심 트릭 또는 결정적 인사이트"]],
    "p20": [["warn", "..."], ["key", "..."]]
  }
}
```

- 키: `paragraph_id` (`p5`, `p8`, …)
- 값: `[type, message]` 배열의 배열. 한 문단에 여러 콜아웃 허용.
- `type`은 정확히 `"warn"` 또는 `"key"`. 다른 값 금지.

콜아웃은 ① `tab-reading`에서 해당 문단 바로 아래 박스로 렌더된다.

---

## Output 3 (선택): `analysis.json#quizzes`

섹션 끝에 표시되는 자가 점검 질문.

```json
{
  "quizzes": {
    "s3": [
      {"q": "...", "a": "..."}
    ]
  }
}
```

- 키: `section_id`
- 값: `{q, a}` 객체 배열
- 양: 섹션당 1~2개 권장 (전체 논문에서 5~8개)

---

## 이미지 생성

> Claude Code의 Bash tool로 `codex ...` 명령을 직접 실행해 ImageGen으로 PNG를 만든다. 별도 플러그인·MCP 자동화 없이 Bash 한 줄. 결과는 곧장 base64로 박아 `<figure class="concept-figure">` 또는 `<figure class="diss-overview-figure">` 정본 컴포넌트로 인라인 — 검수는 사후.
>
> **정식 호출 형식 (6계명 — Bash·UTF-8 prompt.txt·ASCII 인자·stdin null·스타일/출력 명시·이미지 내 제목 금지) + 검증된 명령 템플릿: `rules/component_rules.md` §11.** 이 절을 따르지 않으면 인코딩(CP949)·hang·컷아웃·이미지 내 paper 제목 잔존으로 한 번에 막힌다.

이 단계에서 생성 가능한 이미지:
- **summary 카드용 한 장 overview** — `dissection_overview.png`, 1536×864, 5단(PROBLEM → KEY OBSERVATIONS → METHOD → WHAT'S NEW → RESULTS) 가로 인포그래픽. **summary 카드에 반드시 동봉** (위의 \"8번 카드\" 규약 참조).
- ② 탭 상단 3-stage flow diagram (예: Merging → Pruning → 결과)
- 7-카드 중 시각적 보조가 필요한 카드의 컨셉 일러스트 (예: `diss-observe`의 관찰 현상 도식)
- 메서드 흐름을 한 장으로 요약하는 Execution Logic 인포그래픽

저장 / 임베드:
- 저장 경로: `papers/[name]/assets/generated/`
- 파일명 규약: `dissection_<purpose>.png` (예: `dissection_overview.png`, `dissection_flow_3stage.png`)
- **HTML 임베드: base64 인라인 의무** (CLAUDE.md 자산 임베딩 정책 — 단일 파일 자족·휴대성 우선). 외부 참조는 개발 미리보기 한정.

`dissection_overview.png`는 `_build.py`의 `render_diss()`가 `c["id"] == "summary"` 분기 시 자동 임베드. 기타 보조 이미지는 `cards[].image` 필드로 참조 가능.

### overview prompt 작성 가이드 (정본)

`papers/[name]/assets/generated/prompt_dissection_overview.txt` (UTF-8) 안에 포함할 표준 구성 — 5단 좌→우 흐름:

```
교육용 학술 인포그래픽. 가로 직사각형 1536x864.

주제: \"<논문 short_name> 한 장 정리\"

전체 레이아웃: 가로 5단 구조, 각 단마다 영어 헤더 + 시각 아이콘 + 짧은 설명.

[1단 PROBLEM] <문제 상황을 시각화 — 데이터·규모 + 통계 라벨>
[2단 KEY OBSERVATIONS] <저자가 발견한 핵심 통찰 2~3개를 아이콘 박스로>
[3단 METHOD] <메서드 구조의 핵심 다이어그램 — 가장 큰 패널>
[4단 WHAT'S NEW] <기존 방법 vs 본 논문 비교 — 빨간 X와 녹색 체크>
[5단 RESULTS] <핵심 수치 1~3개를 큰 통계 박스로 + 작은 Pareto/scatter 아이콘>

색상 팔레트: v3 흰색-아이보리 배경 + lavender(#8b75c0) + amber(#ad8e4e) + mint(#75ad8e) + rose(#b87887) + azure(#6b95b3).

스타일 지시:
- 풀 블리드 인포그래픽, 배경 가득 (NOT a transparent cutout)
- Scientific American / Nature graphics 스타일
- 모든 라벨 영어 (PROBLEM, METHOD 등)
- 1536x864 가로 직사각형 (16:9)

절대 금지 (6번째 계명):
- 논문 제목 텍스트
- \"<short_name>\" 단독 헤더
- 저자명
- \"Figure N\" 라벨

NO paper title at top, NO standalone header, NO author names. Only the 5-stage flow with English section headers.
```

---

## Critical Rules

- 섹션 단위 단순 요약 금지
- 인과 흐름 우선: observation → idea → method → evidence → limits
- 모든 주장은 논문에 근거를 둔다 (figure/table/문단 ID로 추적 가능해야 함)
- 카드 클래스명(`diss-*`) 임의 변경 금지 — CSS와 직접 결합되어 있음
- callout type은 `warn` / `key` 두 가지만 사용
