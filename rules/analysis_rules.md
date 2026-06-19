# Analysis Rules

## 적용 단계

- Stage 4 — Research Analysis (`tabs_data/dissection.json` + `analysis.json#callouts`)
- Stage 5 — Coaching (`tabs_data/questions.json`)
- Stage 6 — Figure Interpretation (`analysis.json#interpretations` + `#beginner_notes`)

---

## 핵심 원칙

분석은 **저자의 사고 과정을 복원**해야 한다. 단순 내용 재진술이 아니다.

## Required Logic

항상 다음 인과 사슬을 추적:

```
observation → dissatisfaction with prior work → new idea → implementation → validation → limits
```

각 단계는 다른 단계와 명시적으로 연결되어야 한다. "왜 이 관찰이 이 아이디어로 이어졌는가"가 핵심.

## 근거 매핑

모든 주요 주장은 다음 중 하나와 연결되어야 한다:

- 본문 문단 ID (`p3`, `p20`)
- Figure / Table ID (`fig_2`, `table_1`)
- 구체적 수치 (예: "C=30%에서 2.4%p 하락")

## Output Discipline

각 산출물의 스키마/클래스명은 정본이며 변경 금지:

| 산출물 | 정본 키/클래스 |
|---|---|
| Dissection 카드 7종 | `diss-motivation / -observe / -compare / -logic / -verify / -risk / -extend` |
| Coaching 카드 4종 | `q-hidden / q-myth / q-critic / q-extend` |
| Callout 타입 2종 | `warn`, `key` |
| Figure 해석 두 층 | `interpretations` (전문가) + `beginner_notes` (초보자) |

CSS와 직접 결합되어 있으므로 클래스명을 임의로 바꾸면 렌더가 깨진다.

---

## Forbidden

- shallow summary (섹션 단위 요약)
- generic praise ("이 방법은 흥미롭다")
- unsupported speculation (논문 또는 통상 도메인 지식 외 추측)
- repeating abstract only
- 카드/콜아웃 클래스명 변형
- 수치 없는 비교 ("더 좋다", "훨씬 빠르다" 등)
- **기본 전문용어의 무리한 한국어 직역** — dissection 카드·callout·figure interpretation·beginner note 모든 한국어 prose에 동일 적용. 정본 규칙·안티패턴 표: `prompts/03_translation.md § 🔴 무리한 한국어 변환 금지`. 의심 시 영문 그대로 두는 것이 직역보다 거의 항상 낫다.

---

## Priority

1. author's motivation (왜 이 일을 했는가)
2. key observation (저자가 직접 본 것)
3. difference from prior work (무엇이 다른가)
4. execution logic (아이디어 → 메서드)
5. evidence (실험이 무엇을 증명하는가)
6. limitations (어디서 무너지는가)
