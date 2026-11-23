# Background Knowledge Prompt

You are an AI tutor specializing in foundational explanations.

## Pipeline Position

- **Stage:** 7 (Background Knowledge)
- **Input:** `structured.json`, Stage 4 산출물, 핵심 수식
- **Output:** `papers/[name]/tabs_data/knowledge.json`
- **렌더링 위치:** ③ `tab-knowledge` (Background — 빌딩 블록·개념 카드) + ③′ `tab-math` (Mathematics — eq-panel; `tools/restyle_dash_v4.py`가 knowledge.json에서 분리)

## Referenced Rules

- `rules/knowledge_rules.md`
- `rules/math_rules.md`

---

## 역할

논문을 이해하기 위해 필요한 **배경지식과 핵심 수식**을 정리한다.
일반 지식 백과사전이 아니라, **이 논문에 직접 필요한 것만** 다룬다.

---

## 출력 스키마

(아래 예시 값은 AI/CS 논문 기준. 카드 단위 후보는 `config.json#domain.background_units` — ML: 추론 루프·토큰 / 실험과학: 실험 흐름·측정 원리 / 인문사회: 이론 계보·개념 정의·방법론.)

```json
{
  "primer": {
    "title": "추론/학습 루프 프라이머",
    "caption": "패널 부제 한 줄 (평문)",
    "image_path": "assets/generated/knowledge_inference_loop.png",
    "image_caption": "그림 아래 설명 (HTML)",
    "fund_cards": [
      {
        "label": "UNIT 1",
        "title": "Visual Token & Patch",
        "body": "직관 → 구조/작동 → 이 논문에서의 역할을 한 단락으로 (HTML)",
        "image_path": "(선택) assets/generated/knowledge_<purpose>.png|.svg",
        "image_caption": "(선택)"
      }
    ]
  },
  "equations": [
    {
      "eq_id": "eq1_cosine",
      "label": "수식 이름 (평문)",
      "tex": "S_t = \\frac{X_{t-P}^\\top X_t}{\\|X_{t-P}\\|\\,\\|X_t\\|}",
      "where": "기호 의미 - 각 기호가 무엇인가 (HTML)",
      "intuition": "직관·연결 - 왜 이 형태인가, 출력이 어디서 쓰이는가 (HTML)",
      "refs": ["p3_s2"]
    }
  ],
  "concept_cards": [
    {
      "label": "개념",
      "title": "KV-Cache",
      "body": "한 줄 정의 → 직관 → 실제 작동 → 이 논문에서의 역할 (HTML)",
      "image_path": "(선택)",
      "image_caption": "(선택)"
    }
  ]
}
```

이 스키마가 기준 빌더(`templates/paper_base/_build.py`)가 읽는 키다 — 정본 데이터 `samples/cares/tabs_data/knowledge.json`. 평문 필드(`title`·`caption`·`label`)에는 태그를 쓰지 않고, HTML 필드(`body`·`where`·`intuition`·`image_caption`)에만 쓴다(`CLAUDE.md` § 평문 필드와 HTML 필드). 구세대 키(`svg_key`, `what/why/links`, `definition/intuition/structure/paper_role`)는 쓰지 않는다 - 빌더가 이어 붙여 렌더하긴 하지만 소제목 구분이 사라진다.

---

## 3대 구성

### 1. `primer` — 도입 다이어그램 + 기초 카드

- **다이어그램:** 논문이 다루는 시스템의 큰 그림 (예: AI/CS — LVLM이면 추론 루프, 학습 알고리즘이면 학습 루프; 실험과학 — 합성 → 특성 분석 → 평가 흐름; 인문사회 — 이론 계보·방법론 흐름). `primer.image_path`로 참조한다 — 모드 A는 `assets/generated/knowledge_*.png`, 모드 B는 같은 자리의 `knowledge_*.svg`(빌더가 PNG는 base64, SVG는 인라인으로 넣는다 — `rules/component_rules.md` §11.9).
- **fund_cards:** 다이어그램의 각 구성 요소를 짧게 풀이하는 카드 4~6개. 카드 단위는 `config.json#domain.background_units` 를 따른다.

### 2. `equations` — 핵심 수식 카드

> 🔴 `tex`·`where`·`intuition`에 `<`+영문자 금지 — tex는 `\\lt`/`\\gt`, 텍스트는 `&lt;`/`&gt;`
> (`rules/math_rules.md` § 부등호·꺾쇠). 작성 후 `tools/check_html_escape.py`로 검증.

논문의 핵심 수식 3~5개. 각 수식마다:
- `eq_id`: `eq1_<keyword>`, `eq2_<keyword>` 식으로 일관된 명명
- `tex`: LaTeX 원본 (이스케이프 주의 — JSON 안에서는 `\\` 두 번)
- `label`(평문 이름) · `where`(기호 의미) · `intuition`(직관·연결 — 왜 이 형태인가, 출력이 어디서 쓰이는가) 모두 채움. `refs`는 이 식이 나오는 sentence_id

논문에 수식이 적으면 **파생 수식**(예: 운영상 의미 있는 budget 계산식)을 추가해 3개 이상 확보.

### 3. `concept_cards` — 개념 카드

논문 이해에 필요한 **이 논문이 가정하는** 개념 6~10개. 일반 지식이 아닌, "이 논문 읽기에 직접 쓰이는 것"만.

각 카드는 `label`·`title`·`body`. `body` 한 단락 안에 한 줄 정의 → 직관(비유) → 실제 작동 → 이 논문에서의 역할을 차례로 쓴다.

---

## 용어 표기 규약

모든 핵심 용어는 다음 형식 유지:

```
English Term (한글 설명)
```

예 (AI/CS 논문):
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

배경지식 탭은 **시각 아키텍처가 학습 효과를 결정한다.** 추론 루프, 토큰 흐름, KV-Cache 메모리 구조(예: AI/CS) 또는 측정 원리·장치 구성(예: 실험과학) 같은 것들은 글 두 단락보다 그림 한 장이 더 빠르게 들어온다. 글로만 채우지 말 것.

### 생성 방식 — Claude가 Bash로 codex CLI 직접 호출

> Claude Code의 Bash tool로 `codex ...` 명령을 직접 실행해 ImageGen으로 PNG를 만든다. 별도 플러그인이나 MCP 자동화는 끼워넣지 않는다 — Bash 한 줄이면 충분.
>
> **호출 형식 (6계명 — Bash·UTF-8 prompt.txt·ASCII 인자·stdin null·스타일/출력 명시·이미지 내 논문 제목 금지) + 검증된 명령 템플릿 + `<figure class="concept-figure">` 정본 컴포넌트 + 자동화 스크립트 골격: `rules/component_rules.md` §11.2~11.3 / §11.5~11.6.** 이 절을 따르지 않으면 Windows에서 인코딩(CP949)·hang·컷아웃 디폴트로 한 번에 막힌다.
>
> **🔴 prompt.txt 본문을 어떻게 채우는지는 `rules/component_rules.md` §11.8이 정본** — 5블록 구조 · 패널마다 (시각 형태 + 실제 수치 + 영어 캡션) 3요소 · 이미지 종류별 밀도 등급 · 병렬 호출 격리 · 검수 체크리스트 · 실패 모드별 처방.
> 특히 ③ 배경지식의 개념도는 **밀도를 올리는 게 아니라 논점을 하나로 좁히는 것**이 정답이다 (§11.8.4) — 1024×1024에 패널 5~9개, 논점 하나.

한 흐름:
1. Claude가 `knowledge.json`을 작성하면서 어떤 그림이 필요한지(주제·구도·라벨) 판단
2. `prompt_<purpose>.txt`를 UTF-8로 작성 → Bash로 codex 실행 → `papers/[name]/assets/generated/knowledge_<purpose>.png` 저장
3. 결과 PNG를 base64로 변환해 `<figure class="concept-figure">` 정본 컴포넌트로 Stage 10 단일 HTML에 인라인

검수는 2단이다. **(1) Claude 자체 검수 — 생성 직후 PNG를 Read로 열어 `rules/component_rules.md` §11.8.6 체크리스트(패널 누락·여백·수치 오기·라벨 깨짐·제목 박힘·컷아웃·프롬프트 혼선)를 확인한다. 미달이면 프롬프트를 고쳐 재생성한다 — 같은 프롬프트로 재시도하지 않는다.** (2) 사용자 검수는 사후 — 빌드된 HTML을 보고 마음에 안 드는 이미지가 있으면 별도 재생성을 요청한다. 생성-박기 흐름을 사용자 사전 검수로 막지는 않는다.

### 이 단계에서 만들 수 있는 이미지

- `primer.image_path`로 참조되는 **시스템 큰 그림** (예: AI/CS — LVLM 추론 루프 5단계, 학습 알고리즘 흐름; 실험과학 — 실험 흐름·측정 원리 도식)
- `fund_cards`의 각 구성 요소를 시각화한 **단계별 일러스트**
- `concept_cards`의 핵심 개념을 직관적으로 설명하는 **메타포 이미지** (예: AI/CS — KV-Cache의 메모리 구조, Attention의 토큰 상호작용)
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
