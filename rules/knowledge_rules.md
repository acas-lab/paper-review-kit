# Knowledge Rules

## 적용 단계

- Stage 7 — Background Knowledge (`tabs_data/knowledge.json` → ③ `tab-knowledge`)

---

## 1. 용어 표기 방식

모든 핵심 용어는 다음 형식 유지:

```
English Term (한글 설명)
```

예시:
- `Attention (주의 메커니즘)`
- `Token (데이터 단위 표현)`
- `KV-Cache (key/value 캐시)`
- `Cumulative Attention Score (누적 어텐션 점수)`

처음 등장 시 풀어 적고, 이후엔 영문만 사용한다.

---

## 2. 번역 규칙

- 용어는 번역하지 않고 영어 유지
- 설명만 한글로 제공
- 수식 안의 변수/심볼은 그대로 유지
- **무리한 한국어 신조어 금지** — 한국 ML 커뮤니티에 굳어진 표기가 없으면 영문 그대로. "거친 데이터셋(crude dataset)", "이진 투표(Binary Polling)", "워밍업 파인튜닝(warm-up fine-tuning)", "고충실도(high-fidelity)" 같은 직역은 사용 금지. 정본 안티패턴 표·자동 점검 정규식: `prompts/03_translation.md § 🔴 무리한 한국어 변환 금지`.

---

## 3. 깊이 3단계

모든 개념 카드(`fund_cards`, `concept_cards`)는 다음 3단계를 모두 포함:

1. **직관 (`intuition`)** — 비유 / 큰 그림 / "왜 필요한가"
2. **구조·작동 (`structure`)** — 실제 메커니즘
3. **논문 연결 (`paper_role`)** — 이 논문에서 어떤 역할을 하는가

한 단계라도 비면 그 카드는 미완성.

---

## 4. 연결성

모든 배경지식은 반드시 **이 논문에서 등장한 이유**와 연결되어야 한다.

일반 백과사전식 정의 금지. "이 논문 이해에 직접 필요한 것만" 다룬다.

---

## 5. 수식 처리

`equations` 배열의 각 항목:

```json
{
  "eq_id": "eq1_<keyword>",
  "tex": "...",            // LaTeX (JSON 안에서 \\ 두 번)
  "what": "수식이 무엇을 계산하는가",
  "why":  "왜 이 형태인가 / 왜 도입했는가",
  "links": "이 식의 출력이 어디서 쓰이는가 (앞뒤 연결)"
}
```

- `eq_id` 명명: `eq1_<keyword>`, `eq2_<keyword>`, ... 일관 유지
- 논문 수식이 적으면 파생 수식(예: budget 공식)을 추가해 3개 이상 확보
- 자세한 수식 표기 규칙: `rules/math_rules.md`

---

## 6. 다이어그램 SVG

`primer.svg_key`로 참조되는 도입 다이어그램은 Stage 10에서 Claude가 단일 HTML에 SVG로 인라인하거나, `assets/generated/knowledge_*.png`를 만들어 base64 인라인한다 (CLAUDE.md 자산 임베딩 정책).

- 외부 라이브러리 의존 없음
- 정적 (애니메이션은 ⑥ `tab-qa`의 위젯에서 사용)
- 색상은 디자인 토큰(`--accent`, `--sage`, `--gold`, `--indigo`, `--plum`) 사용
- FrameFusion이 개입하는 위치 같은 핵심 포인트는 ★ 빨간 배지 등으로 강조

---

## 절대 금지

- 단순 정의 나열
- 백과사전식 망라
- 논문과 무관한 일반 지식 카드
- 같은 개념의 카드 중복
- LaTeX JSON 이스케이프 누락 (`\\` 두 번 필수)
