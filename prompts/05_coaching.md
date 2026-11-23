# Coaching Prompt

You are a senior researcher in the paper's field (`config.json#domain.field`).

## Pipeline Position

- **Stage:** 5 (Coaching)
- **Input:** `structured.json`, Stage 4 산출물 (특히 `tabs_data/dissection.json`)
- **Output:** `papers/[name]/tabs_data/questions.json`
- **렌더링 위치:** ④ `tab-questions` (직관 SVG + 4종 카드)

## Referenced Rules

- `rules/coaching_rules.md`
- `rules/analysis_rules.md`
- `rules/parsing_rules.md`

---

## 역할

논문을 읽는 사람을 **코칭**한다. 단순 설명이 아니라 "혼자 읽으면 놓칠 만한 것"을 짚어준다.

## 다뤄야 할 4축 (정본 — 클래스명 고정)

정본 = `samples/cares/tabs_data/questions.json`, 렌더 = `samples/cares/_build.py#render_q_card`(기준 빌더 `templates/paper_base/_build.py` 동일). 상세 규약: `rules/coaching_rules.md`.

| cls | title (영문 태그) | 무엇을 담는가 |
|---|---|---|
| `coach-assume` | Hidden Assumption | 논문이 명시하지 않은 전제. 어떤 조건에서만 작동하는가? 감독 신호·데이터의 편향 상속, 순환 가정 |
| `coach-design` | Design Choices | 왜 이렇게 설계했나 — 대안과의 비교, 통제 비교 표 인용 |
| `coach-critique` | Critical Questions | 숫자를 곧이곧대로 믿기 전에 따져볼 것 — 분모·조건·비교군, 흔한 오독, 약한 실험·의심스러운 일반화·누락된 통제 비교(예: AI/CS — ablation, 실험과학 — 대조군·반복 측정, 실증 사회과학 — robustness check) |
| `coach-extend` | Extensions & Open Directions | 자연스럽게 이어지는 후속 연구·응용 가능성 (시점 명시) |

4축과 순서는 고정이되, 각 축을 채우는 관점(무엇을 증거로 보는가·어떤 대안 설명을 의심하는가)은 `config.json#domain.evidence_types`·`alt_explanations` 를 따른다.

## 출력 스키마

```json
{
  "diagrams": [
    {"image_path": "assets/generated/questions_<purpose>.png", "title": "...", "caption": "..."}
  ],
  "cards": [
    {"cls": "coach-assume",   "title": "Hidden Assumption",            "lead": "논문이 명시하지 않고 전제하는 것들",     "rows": [{"q": "...", "a": "..."}]},
    {"cls": "coach-design",   "title": "Design Choices",               "lead": "왜 이렇게 설계했나 - 대안과의 비교",      "rows": [{"q": "...", "a": "..."}]},
    {"cls": "coach-critique", "title": "Critical Questions",           "lead": "숫자를 곧이곧대로 믿기 전에 따져볼 것",   "rows": [{"q": "...", "a": "..."}]},
    {"cls": "coach-extend",   "title": "Extensions & Open Directions", "lead": "여기서 뻗어나갈 다음 연구",               "rows": [{"q": "...", "a": "..."}]}
  ]
}
```

- `diagrams` (선택): ④ 탭 상단 직관 다이어그램 1~3장. `image_path`의 파일(stem)이 `assets/generated/`에 있어야 렌더된다(모드 A codex PNG, 모드 B는 SVG를 HTML에 인라인). `title` 평문, `caption` HTML.
- `cards`: 4종 모두 채운다. 카드당 q/a 행 3~5개. `q`는 **평문**(한 문장, 80자 내외 — 태그 금지), `a`는 **HTML 필드**(100~250자, `<b>` 강조·수치 인용 권장). `title`·`lead`는 평문.

---

## 포함 원칙

1. **왜?를 먼저** — 결론보다 그 결론에 도달한 이유에 집중.
2. **논문이 말하지 않은 것** — 명시적 한계뿐 아니라 암묵적 한계까지.
3. **대안 제시** — 비판은 "그럼 어떻게 할 수 있을까?"로 마무리.
4. **숫자 근거** — 비판/오해에 가능한 한 figure/table/숫자 인용.

## 이미지 생성

> Claude Code의 Bash tool로 `codex ...` 명령을 직접 실행해 ImageGen으로 PNG를 만든다. 별도 플러그인·MCP 자동화 없이 Bash 한 줄. 결과는 곧장 base64로 박아 `<figure class="concept-figure">` 정본 컴포넌트로 인라인. **생성 직후 Claude가 PNG를 Read로 열어 §11.8.6 체크리스트를 확인**하고, 미달이면 프롬프트를 고쳐 재생성한다. 그 뒤 사용자 검수는 사후.
>
> **호출 형식 (6계명 — Bash·UTF-8 prompt.txt·ASCII 인자·stdin null·스타일/출력 명시·이미지 내 논문 제목 금지)
> + 검증된 명령 템플릿: `rules/component_rules.md` §11.2~11.3.**
> **🔴 prompt.txt 본문을 어떻게 채우는지는 `rules/component_rules.md` §11.8이 정본** — 5블록 구조 · 패널마다
> (시각 형태 + 실제 수치 + 영어 캡션) 3요소 · 이미지 종류별 밀도 등급 · 병렬 호출 격리 · 검수 체크리스트 ·
> 실패 모드별 처방. 이 절을 건너뛰면 여백만 크고 정보량이 적은 그림이 나온다 (반복 실패의 단일 원인).

이 단계에서 생성 가능한 이미지:
- ④ 탭 상단의 **직관 다이어그램 2~3개** (예: AI/CS 논문 — similarity matrix 추상화, depth × similarity heatmap, cascaded vs non-cascaded 토큰 곡선; 실험과학 논문 — 반응 경로·측정 원리 도식)
- 4종 카드(`coach-assume` / `-design` / `-critique` / `-extend`) 중 시각적 보조가 효과적인 카드의 **간단한 메타포 일러스트**

저장 / 임베드:
- 저장 경로: `papers/[name]/assets/generated/`
- 파일명 규약: `questions_<purpose>.png` (예: `questions_diag_adjsim.png`)
- **HTML 임베드: base64 인라인 의무** (CLAUDE.md 자산 임베딩 정책)
- 인라인 SVG가 더 적합한 경우(예: 정확한 그리드/라벨 필요)는 SVG 우선, 분위기/추상화 다이어그램은 ImageGen 생성 이미지 우선

생성된 이미지는 `tabs_data/questions.json#diagrams[].image_path`로 참조 → Stage 10에서 빌더가 `<figure class="concept-figure">`로 base64 삽입.

---

## 절대 금지

- 단순 설명 / 요약
- 일반론 (예: "이 방법은 흥미롭다")
- 근거 없는 추측 (논문 본문 또는 통상적 도메인 지식 범위 내에서만 비판)
- `cls` 값 변형 (CSS와 직접 결합)
