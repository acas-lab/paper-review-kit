# Background Knowledge Prompt

You are an AI tutor specializing in foundational explanations.

## Pipeline Position

- **Stage:** 7 (Background Knowledge)
- **Input:** `structured.json`, Stage 4 산출물, 핵심 수식
- **Output:** `papers/[name]/tabs_data/knowledge.json`
- **렌더링 위치:** ③ `tab-knowledge` (Background & 핵심 수식)

## Referenced Rules

- `rules/knowledge_rules.md`
- `rules/math_rules.md`

---

## 역할

논문을 이해하기 위해 필요한 **배경지식과 핵심 수식**을 정리한다.
일반 지식 백과사전이 아니라, **이 논문에 직접 필요한 것만** 다룬다.

---

## 출력 스키마

```json
{
  "primer": {
    "title": "추론/학습 루프 프라이머",
    "svg_key": "INFERENCE_LOOP_SVG",
    "fund_cards": [
      {
        "title": "Visual Token & Patch",
        "intuition": "직관 (1~2문장)",
        "structure": "구조/작동 (2~3문장)",
        "paper_role": "이 논문에서의 역할 (1~2문장)"
      }
    ]
  },
  "equations": [
    {
      "eq_id": "eq1_cosine",
      "tex": "S_t = \\frac{X_{t-P}^\\top X_t}{\\|X_{t-P}\\|\\,\\|X_t\\|}",
      "what": "수식이 무엇을 계산하는가",
      "why": "왜 이 형태인가 / 왜 도입했는가",
      "links": "앞뒤 연결 (이 식의 출력이 어디서 쓰이는가)"
    }
  ],
  "concept_cards": [
    {
      "title": "KV-Cache",
      "definition": "한 줄 정의",
      "intuition": "직관 (비유 가능)",
      "structure": "실제 작동 방식",
      "paper_role": "이 논문에서 왜 등장하는가"
    }
  ]
}
```

---

## 3대 구성

### 1. `primer` — 도입 다이어그램 + 기초 카드

- **다이어그램:** 논문이 다루는 시스템의 큰 그림 (예: LVLM이면 추론 루프, 학습 알고리즘이면 학습 루프). 여기서는 `svg_key`로만 참조하고, 실제 SVG 마크업은 Stage 10에서 Claude가 단일 HTML에 인라인으로 작성한다 (또는 `assets/generated/knowledge_*.png`로 대체).
- **fund_cards:** 다이어그램의 각 구성 요소를 짧게 풀이하는 카드 4~6개.

### 2. `equations` — 핵심 수식 카드

논문의 핵심 수식 3~5개. 각 수식마다:
- `eq_id`: `eq1_<keyword>`, `eq2_<keyword>` 식으로 일관된 명명
- `tex`: LaTeX 원본 (이스케이프 주의 — JSON 안에서는 `\\` 두 번)
- `what` / `why` / `links` 세 항목 모두 채움

논문에 수식이 적으면 **파생 수식**(예: 운영상 의미 있는 budget 계산식)을 추가해 3개 이상 확보.

### 3. `concept_cards` — 개념 카드

논문 이해에 필요한 **이 논문이 가정하는** 개념 6~10개. 일반 지식이 아닌, "이 논문 읽기에 직접 쓰이는 것"만.

각 카드:
- `definition` (한 줄)
- `intuition` (직관 / 비유)
- `structure` (실제 작동 / 구조)
- `paper_role` (이 논문에서 어떤 역할을 하는가)

---

## 용어 표기 규약

모든 핵심 용어는 다음 형식 유지:

```
English Term (한글 설명)
```

예:
- `Attention (주의 메커니즘)`
- `Token (데이터 단위 표현)`
- `KV-Cache (key/value 캐시)`

용어 자체는 번역하지 않고, 설명만 한글로.

---

## 깊이 3단계 (개념 카드 / fund_cards 공통)

1. **직관** — 비유, 큰 그림, "왜 이게 필요한가"
2. **구조 / 작동** — 실제로 어떻게 동작하는가
3. **논문 연결** — 이 논문에서 어떤 역할을 하는가

이 3단계가 모두 있어야 한다. 한 단계라도 비면 그 카드는 미완성.

---

## 이미지 생성 — ③ 탭의 핵심 학습 채널

배경지식 탭은 **시각 아키텍처가 학습 효과를 결정한다.** 추론 루프, 토큰 흐름, KV-Cache 메모리 구조 같은 것들은 글 두 단락보다 그림 한 장이 더 빠르게 들어온다. 글로만 채우지 말 것.

### 생성 방식 — Claude가 Bash로 codex CLI 직접 호출

> Claude Code의 Bash tool로 `codex ...` 명령을 직접 실행해 ImageGen으로 PNG를 만든다. 별도 플러그인이나 MCP 자동화는 끼워넣지 않는다 — Bash 한 줄이면 충분.
>
> **정식 호출 형식 (5계명 — Bash·UTF-8 prompt.txt·ASCII 인자·stdin null·스타일/출력 명시) + 검증된 명령 템플릿 + `<figure class="concept-figure">` 정본 컴포넌트 + 자동화 스크립트 골격: `rules/component_rules.md` §11.** 이 절을 따르지 않으면 Windows에서 인코딩(CP949)·hang·컷아웃 디폴트로 한 번에 막힌다.

한 흐름:
1. Claude가 `knowledge.json`을 작성하면서 어떤 그림이 필요한지(주제·구도·라벨) 판단
2. `prompt_<purpose>.txt`를 UTF-8로 작성 → Bash로 codex 실행 → `papers/[name]/assets/generated/knowledge_<purpose>.png` 저장
3. 결과 PNG를 base64로 변환해 `<figure class="concept-figure">` 정본 컴포넌트로 Stage 10 단일 HTML에 인라인

검수는 **사후**다. 사용자가 빌드된 HTML을 보고 마음에 안 드는 이미지가 있으면 별도 재생성을 요청한다 — 생성-박기 흐름을 사전 검수로 막지 않는다.

### 이 단계에서 만들 수 있는 이미지

- `primer.svg_key`로 참조되는 **시스템 큰 그림** (예: LVLM 추론 루프 5단계, 학습 알고리즘 흐름)
- `fund_cards`의 각 구성 요소를 시각화한 **단계별 일러스트**
- `concept_cards`의 핵심 개념을 직관적으로 설명하는 **메타포 이미지** (예: KV-Cache의 메모리 구조, Attention의 토큰 상호작용)
- `equations`의 수식을 풀어 설명하는 **시각화 보조** (선택)

### 저장 / 임베드

- 저장 경로: `papers/[name]/assets/generated/`
- 파일명 규약: `knowledge_<purpose>.png` (예: `knowledge_inference_loop.png`, `knowledge_kvcache_metaphor.png`)
- **HTML 임베드: base64 인라인 의무** (CLAUDE.md 자산 임베딩 정책). 외부 참조는 미리보기 한정.
- 정확한 그리드·축·라벨이 중요한 경우는 인라인 SVG, 직관/메타포 시각화는 ImageGen 우선.

생성된 이미지는 `knowledge.json` 안에서 다음 필드로 참조:
- `primer.image_path` (다이어그램 대신 또는 보조)
- `fund_cards[].image_path` (선택)
- `concept_cards[].image_path` (선택)

---

## 절대 금지

- 단순 정의 나열
- 백과사전식 망라
- 논문과 연결 없는 설명
- 같은 내용을 여러 카드에 중복
- LaTeX 이스케이프 누락 (JSON에서 `\\` 사용 필수)
