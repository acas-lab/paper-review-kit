# Coaching Rules

## 적용 단계

- Stage 5 — Coaching (`tabs_data/questions.json` → ④ `tab-questions`)

---

## 4축 구조 (정본 — 클래스명 고정)

정본 = `samples/cares/tabs_data/questions.json` + `samples/cares/_build.py#render_q_card`(`templates/paper_base/_build.py`도 같은 렌더). q/a 페어로 자가 점검을 유도한다. `cls`는 CSS(`.coach-card.coach-*`)와 직접 결합하므로 바꾸지 않는다. 카드 순서도 아래 순서 그대로.

| cls | title (영문 태그) | lead 예 | 다루는 것 |
|---|---|---|---|
| `coach-assume` | Hidden Assumption | 논문이 명시하지 않고 전제하는 것들 | 어떤 조건에서만 작동하는가, 순환 가정·데이터/감독 신호의 편향 상속 |
| `coach-design` | Design Choices | 왜 이렇게 설계했나 - 대안과의 비교 | 설계 결정의 근거와 대안 — ablation·통제 비교 표 인용 |
| `coach-critique` | Critical Questions | 숫자를 곧이곧대로 믿기 전에 따져볼 것 | 수치는 정확히 어디서 왔는가(분모·조건·비교군), 흔한 오독, 약한 실험·일반화 |
| `coach-extend` | Extensions & Open Directions | 여기서 뻗어나갈 다음 연구 | 이 논문이 못 한 것 → 후속 연구·응용 (시점 명시 필수) |

렌더: `title` → `.coach-tag`(pill), `lead` → `<h3>`, `rows[*]` → `<details class="recall-item"><summary>{q}</summary><div class="recall-answer"><p>{a}</p></div></details>`.

---

## questions.json 정본 형식

```json
{
  "diagrams": [
    {
      "image_path": "assets/generated/query_resolution.png",
      "title": "같은 이미지, 다른 질의 → 다른 해상도",
      "caption": "핵심 직관 한두 문장 (HTML 허용)"
    }
  ],
  "cards": [
    {
      "cls": "coach-assume",
      "title": "Hidden Assumption",
      "lead": "논문이 명시하지 않고 전제하는 것들",
      "rows": [
        {
          "q": "저해상도 패스의 특징만으로 '고해상도가 필요한지'를 알 수 있다는 가정은 타당한가?",
          "a": "순환 위험이 있다: 미세한 단서는 저해상도에서 <b>애초에 보이지 않으므로</b> ... (근거 표·절 인용)"
        },
        { "q": "...", "a": "..." }
      ]
    },
    { "cls": "coach-design",   "title": "Design Choices",               "lead": "...", "rows": [ ... ] },
    { "cls": "coach-critique", "title": "Critical Questions",           "lead": "...", "rows": [ ... ] },
    { "cls": "coach-extend",   "title": "Extensions & Open Directions", "lead": "...", "rows": [ ... ] }
  ]
}
```

**필수 키**:
- 카드: `cls`, `title`, `lead`, `rows` (`title`·`lead`는 평문 — esc 적용)
- 행: `q`(질문 한 줄, **평문** — 태그 금지), `a`(답변, **HTML 필드** — `<b>` 강조 허용, 수치 인용 권장)
- 다이어그램: `image_path`, `title`(평문), `caption`(HTML). `image_path`의 파일 이름(stem)이 `assets/generated/`에 있어야 렌더된다.

**선택 키**:
- `diagrams[]` — ④ 탭 상단에 핵심 메커니즘 도식 1~3장(모드 A codex PNG 또는 모드 B SVG).

---

## 코칭 원칙

1. **항상 \"왜?\"부터** — 결론보다 결론에 도달한 이유.
2. **논문이 말하지 않은 것** — 명시적 한계뿐 아니라 암묵적 한계까지 포함.
3. **대안 제시** — 비판은 \"그럼 어떻게 할 수 있을까?\"로 마무리.
4. **숫자로 근거** — 가능한 한 figure / table / 수치 인용. 질문·코칭의 평가 축(비교군·지표·재현성)은 `config.json#domain.evidence_types`·`metric_conventions` 기준으로 잡는다 (정본: `rules/domain_profile.md`).
5. **숨겨진 의미 강조** — 행간(implications), 저자가 의도적으로 흐릿하게 둔 부분.
6. **시점 분리 (coach-extend)** — \"본 논문 이후 X로 이어진다\"는 명확한 시간 표기 필수. \"이 논문이 X를 했다\"로 오인되지 않게 분리. 후속 연구 인용 시 연도 명시 권장(예: AI/CS — \"DETR(2020, Carion)\", \"MAE(2021, He)\").

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
- coach-extend에서 후대 모델을 \"본 논문이 X를 입증/측정/달성했다\"로 적기 — 시간 분리 필수
- **기본 전문용어의 무리한 한국어 직역** — q·a 모든 한국어 prose에 동일 적용. 정본 규칙·안티패턴 표: `prompts/03_translation.md § 🔴 무리한 한국어 변환 금지`. 해당 분야의 한국 학계에 굳어진 표기(`config.json#domain.term_style`)가 없으면 영문 그대로 두는 것이 직역보다 거의 항상 낫다.

---

## Deprecated (모체 구세대 형식 — 신규 논문에 쓰지 않는다)

모체 작업 폴더의 과거 빌드에는 두 형식이 남아 있다(모체 사례 — 배포본 미포함). 배포본의 빌더(`samples/cares`·`templates/paper_base`)는 위 `coach-*` 형식만 렌더하므로, 아래 `cls`를 쓰면 카드 색·태그가 정본과 달라진다.

| 구세대 cls | 형식 | 현재 정본으로의 대응 |
|---|---|---|
| `q-hidden` / `q-myth` / `q-critic` / `q-extend` + `bullets[]` | 4세대 글머리 리스트 | `coach-assume` / `coach-critique`(오해·수치 출처) / `coach-critique` / `coach-extend` + `rows[{q,a}]` |
| `q-myth` / `q-design` / `q-followup` / `q-mental` + `rows[{q,a}]` | 5세대 q/a (모체 12번 이후) | `coach-critique` / `coach-design` / `coach-extend` / (큰 그림 정리는 `coach-assume`·dissection summary로) |

고전·기초 논문(분야 창시 논문, 이론 정립 논문)은 현대 실험 논문과 다른 질문 축이 필요할 수 있다 — 축의 내용은 `config.json#domain`에 맞게 정하되 `cls` 4종은 그대로 쓴다.
