# Coaching Rules

## 적용 단계

- Stage 5 — Coaching (`tabs_data/questions.json` → ④ `tab-questions`)

---

## 4축 구조 (5세대 정본 — 클래스명 고정)

12. deep_compression 이후 정본. q/a 페어로 자가 점검을 유도하는 구조.

| cls | title 한 줄 형식 | 다루는 것 |
|---|---|---|
| `q-myth` | 오해와 진실 | 흔한 잘못된 통설·\"수치는 정확히 어디서 왔는가\" |
| `q-design` | 설계 결정 비판적 검토 | 왜 그렇게 했나, 다르게 했다면 — ablation 표 인용 |
| `q-followup` | 후속 연구로 이어지는 질문 | 이 논문이 못 한 것 → 다음 누가 풀었나 (시점 명시 필수) |
| `q-mental` | 직관 점검 | 큰 그림 정리 — 한 줄 메시지·강점/약점·왜 중요한가 |

---

## questions.json 정본 형식 (5세대)

```json
{
  "diagrams": [
    {
      "id": "diag_overview",
      "title": "Transformer 한 장 요약",
      "image_path": "assets/generated/tx_overview.png",
      "caption": "..."
    }
  ],
  "cards": [
    {
      "id": "q-myth",
      "cls": "q-myth",
      "title": "오해와 진실",
      "lead": "수치는 정확히 어디서 왔는가",
      "rows": [
        {
          "q": "\"Transformer 28.4 BLEU\" — 단일 모델이 앙상블을 이긴 게 맞나?",
          "a": "맞다. <b>Transformer (big) 단일 모델</b>이 EN-DE에서 28.4 BLEU. 종전 최고 앙상블은 ConvS2S Ensemble 26.36..."
        },
        { "q": "...", "a": "..." }
      ]
    }
  ]
}
```

**필수 키**:
- 카드: `id`, `cls`, `title`, `lead`, `rows`
- 행: `q`(질문 한 줄), `a`(답변 — `<b>` 강조 허용, 수치 인용 권장)
- 다이어그램: `id`, `title`, `image_path`, `caption`

**선택 키**:
- `diagrams[]` — Q탭 상단에 핵심 메커니즘 도식 1~3장. ImageGen으로 생성한 보조 이미지를 가리킨다.

---

## 코칭 원칙

1. **항상 \"왜?\"부터** — 결론보다 결론에 도달한 이유.
2. **논문이 말하지 않은 것** — 명시적 한계뿐 아니라 암묵적 한계까지 포함.
3. **대안 제시** — 비판은 \"그럼 어떻게 할 수 있을까?\"로 마무리.
4. **숫자로 근거** — 가능한 한 figure / table / 수치 인용.
5. **숨겨진 의미 강조** — 행간(implications), 저자가 의도적으로 흐릿하게 둔 부분.
6. **시점 분리 (q-followup)** — \"본 논문 이후 X로 이어진다\"는 명확한 시간 표기 필수. \"이 논문이 X를 했다\"로 오인되지 않게 분리. 후대 모델 인용 시 연도 명시 권장(\"DETR(2020, Carion)\", \"MAE(2021, He)\").

---

## 양 / 형식

- 카드 4종 모두 채움 (어느 한 종도 비우지 않는다)
- 카드당 q/a 행 3~5개
- 답변(`a`)당 100~250자 — 수치 포함 시 길어져도 OK
- 질문(`q`)은 한 문장, 80자 내외

---

## 절대 금지

- 단순 설명 / 요약
- 일반론 (\"흥미로운 연구입니다\")
- 근거 없는 추측 (논문 + 통상 도메인 지식 범위 내에서만 비판)
- `cls` 값 변형 (CSS와 직접 결합)
- q-followup에서 후대 모델을 \"본 논문이 X를 입증/측정/달성했다\"로 적기 — 시간 분리 필수
- **기본 전문용어의 무리한 한국어 직역** — q·a 모든 한국어 prose에 동일 적용. 정본 규칙·안티패턴 표: `prompts/03_translation.md § 🔴 무리한 한국어 변환 금지`. 한국 ML 커뮤니티 표준 표기가 없으면 영문 그대로 두는 것이 직역보다 거의 항상 낫다.

---

## Deprecated (4세대 이전 형식)

11. mobilenets 이전 논문(perceptron, alexnet, vgg, resnet, yolo 등)은 다른 4축을 사용한다:

| cls (4세대) | title | 비고 |
|---|---|---|
| `q-hidden` | 가려진 가정 | 5세대에서는 `q-design`에 흡수 |
| `q-myth` | 흔한 오해 | 5세대에서도 유지 |
| `q-critic` | 비판적 질문 | 5세대에서는 `q-design`·`q-mental`로 분산 |
| `q-extend` | 확장 아이디어 | 5세대에서는 `q-followup`으로 재명명 |

또한 4세대는 `bullets[]`(단순 글머리 리스트) 형식. 5세대 q/a 페어 형식이 자가 점검 학습성에 더 적합하다고 판단되어 12. deep_compression 이후 채택.

**기존 4세대 논문은 그대로 둔다** (마이그레이션 불필요). **신규 논문은 반드시 5세대 형식 사용**.
