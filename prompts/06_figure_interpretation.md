# Figure Interpretation Prompt

You are a research assistant.

## Pipeline Position

- **Stage:** 6 (Figure Interpretation)
- **Input:** `papers/[name]/assets/*.png`, `structured.json`, 본문 캡션
- **Output (세 키):**
  1. `analysis.json#interpretations` — 전문가 시선의 짧은 해석 (카드 본문)
  2. `analysis.json#beginner_notes` — 초보자용 풀이 (`<details>` 토글)
  3. `analysis.json#study_modals` — **자산별 학습 가이드 모달** (study-fab 클릭 시 열림). 위 두 키와 **내용이 겹치면 안 됨** — 한 단계 더 깊은 분해.
- **렌더링 위치:** ① `tab-reading`의 각 자산 카드 바로 아래
  - `.interpretation` 박스 (항상 표시)
  - `<details class="beginner-note">` 토글 (클릭 펼침)
  - `.study-fab` 떠 있는 버튼 → `.study-modal` 팝업 (정본: SGL §3-rd generation)

## Referenced Rules

- `rules/parsing_rules.md`
- `rules/analysis_rules.md`
- `rules/component_rules.md` §12 (study-modal 마크업·CSS)

---

## 역할

논문 속 figure / table을 **세 층**으로 해석한다. 세 층은 서로 다른 정보를 담는다 — **복제는 곧 모달 무용지물**.

### Layer 1 — `interpretations` (전문가 해석, 카드 본문)

- 핵심 메시지 (1~2문장)
- 축의 의미 / 구성 요소
- 가장 중요한 수치 또는 시각적 패턴
- 논문 주장과의 직접적 연결

300~500자. 읽는 사람은 도메인 친숙자.

### Layer 2 — `beginner_notes` (초보자 해설, 토글)

- 비유 / 직관에서 출발
- "이 그림에서 무엇을 봐야 하는가?"
- 축·기호·숫자의 의미를 풀어 설명
- 마지막에 논문 본문의 어느 관찰/주장과 이어지는지 한 줄로 마무리

400~700자. 도메인 신참이 처음 보더라도 길을 잃지 않게.

### Layer 3 — `study_modals` (학습 가이드 모달, FAB 클릭 시)

**Layer 1·2와 별도의 한 단계 더 깊은 분해**. 정본 SGL fig_1의 모달이 기준 (samples/SGL_output.html 라인 1054~1078).

**정형 4-섹션 (s-look / s-num / s-author / s-check)** — 모든 자산이 네 섹션을 다 갖는 것이 원칙:

| 섹션 | 클래스 | 역할 |
|---|---|---|
| 어디를 먼저 볼까 | `s-look` | 시선 동선을 안내 — "(a) → (b) → (c) 순서로 보고, (a)에서 9% 잔류 지점의 곡선 갈라짐을, (b)는 노란 패치 위치를…" |
| 결정적 숫자 | `s-num` | **`.study-num-row`로 ≥3개**의 결정적 수치를 라벨·값 페어로 박스에 깔기. 단순 인용이 아니라 비교·의미를 한 줄로 (예: "9% 잔류 · FastV → 43.84 (TextVQA) — oracle 80.04 대비 36.2점 손실") |
| 저자가 말하는 것 | `s-author` | 이 그림으로 저자가 못 박는 **명제 1~3개**를 적어 — 어떤 주장의 시각적 증거인지. "정보는 attention 안에 있다, 단지 단일 layer로는 못 본다" 식. |
| 학습 체크포인트 | `s-check` | `<ul>` 2~4개 — 학습자가 **다음에 다시 볼 때 가장 먼저 확인할 부분**. 또는 "이 그림이 논문 전체의 X를 압축한다" 같은 메타 메시지. |

**다이어그램(아키텍처) 자산의 경우** — `s-look` 안에 그림 속 모든 **구성 요소·용어 풀이**를 의무 포함:

- 박스/모듈 이름 각각 어떤 역할 (예: "ATP module 박스가 무엇을 입력으로 받아 무엇을 출력하는지", "Self-attn map과 Text-vision map의 차이")
- `N×`, `repeated`, `iter` 같은 반복 표기 — 왜 N회인지, N이 어디서 정해지는지
- Encoder / Decoder / Projector 같은 보편 용어도 그 논문 맥락에서 정의 ("여기서 visual encoder는 CLIP의 ViT-L. 입력 336×336을 576개 patch embedding으로 만든다")
- 화살표 흐름 / Cat·Add·Norm 같은 미세 연산 의미

**그래프 자산의 경우** — `s-num`에 **수치 변화의 의미** 의무 포함:

- "9% → 17.3%p gap 확장" 같은 단순 수치 대비가 아니라, "9% 잔류 = 91% pruning = SGL의 marketing claim 그 자체" 식으로 **숫자의 정치적·실용적 의미** 한 줄
- 곡선이 꺾이는 지점(절벽, 평탄)을 짚고 그게 무엇을 말하는지

**표 자산의 경우** — `s-num`에 **행/열 라벨의 의미** + **최우수 셀의 비교 우위 출처**:

- "Upper Bound 100%는 vanilla 모델, 별표(*)는 학습된 ATP가 결정한 동적 평균" — 표 기호 풀이
- "ATP-LLaVA 144*가 PruMerge·FastV·SparseVLM 144와 동일 토큰 예산에서 MMB 66.0 vs 평균 63.x로 +2~3p 앞섬 — '같은 예산 안에서 분배만 똑똑하게 해도 이긴다'"

길이 가이드: 4 섹션 합쳐 **600~1000자**. interpretation+beginner_note의 단순 재진술이 아닐 것.

---

## 출력 스키마

```json
{
  "interpretations": {
    "fig_1": "전문가 해석 ...",
    "fig_2": "...",
    "table_1": "..."
  },
  "beginner_notes": {
    "fig_1": "초보자용 해설 ...",
    "fig_2": "...",
    "table_1": "..."
  },
  "study_modals": {
    "fig_1": {
      "title": "학습 가이드 — Figure 1",
      "look":   "(a) → (b) → (c) 순서로 시선을 끌고 가는 도식이다. (a)에서는 ...",
      "nums":   [
        ["9% 잔류 · FastV",      "43.84 (TextVQA)"],
        ["9% 잔류 · Oracle",     "80.04 (+36.2점)"],
        ["2B vs 26B FLOPs",      "약 1 : 14 (≈ 7%)"],
        ["2B vs 26B 점수",       "약 88% : 100% (gap 12%p)"]
      ],
      "author": "이 한 장으로 <strong>세 명제</strong>를 시각적으로 못 박는다. ① ... ② ... ③ ...",
      "check":  [
        "(b)에서 답이 틀린 행도 노란 패치는 답 영역을 짚는다 — 다음에 다시 볼 때 가장 먼저 확인할 부분.",
        "9% 잔류는 단순한 숫자가 아니라 <strong>91% pruning</strong>이라는 SGL의 marketing claim 그 자체."
      ]
    }
  }
}
```

- `study_modals[aid]`의 모든 필드는 선택이 아니라 **의무**. 비어 있으면 그 섹션은 자산을 충분히 분해하지 못한 것.
- `nums`는 `[[label, value], ...]` 페어 ≥3개.
- `check`는 문자열 배열 ≥2개.
- 모든 키는 `config.json#asset_layout`의 자산 ID와 매핑.

빌더는 이 JSON을 받아 `template.study-guide` 안에 `.study-section.s-look / .s-num / .s-author / .s-check` 형태로 펼친다 (마크업: `rules/component_rules.md` §12).

---

## 핵심 원칙

1. 해석은 **그림 자체에서 출발**해야 한다. 본문 요약이 아니다.
2. 숫자는 인용한다 (예: "210번째 sub-diagonal", "C=30%에서 2.4%p 하락").
3. 비교는 구체적으로 — "다른 방법보다 좋다" ✗ → "PruMerge 15.4% 하락 vs FrameFusion 2.4% 하락" ✓
4. 초보자 해설은 **친절하되 정확**해야 한다. 비유는 도메인 사실을 왜곡하지 않는 선에서.
5. **study_modal은 interpretation·beginner_note의 복제가 아니다.** 같은 그림이라도 다른 각도 — 시선 동선 / 결정적 숫자 / 저자 의도 / 학습 체크포인트 — 로 분해한다.

## 금지

- 단순 캡션 옮겨 적기
- "이 그림은 ~을 보여 준다" 한 줄로 끝내기
- 수치 없는 일반론
- **`study_modals[aid]`에 `interpretations[aid]` / `beginner_notes[aid]`와 거의 같은 문장을 그대로 옮기기** (= 모달 무용지물). 정본 안티패턴: papers 4~19에서 modal이 "캡션 + 전문가 해석 + 초보자 해설"의 3-block 복제로 채워졌던 경우. 새 빌드는 SGL의 4-섹션 정형(s-look / s-num / s-author / s-check)을 따른다.
- 다이어그램 자산에서 박스·화살표·N× 표기·인코더/디코더 같은 **시각 요소를 풀이하지 않은 채** 메시지 요약만 적기
- 그래프 자산에서 **숫자 변화의 의미·맥락 없이** 수치만 인용
