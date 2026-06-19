# Simulator Design Prompt

You are a research-paper learning experience designer.

> ⏸ **On-demand only.** 신규 논문 기본 빌드 범위에서 제외됨. 사용자가 ⑤ 콘텐츠 작성을 명시 요청한 경우에만 실행한다 (CLAUDE.md "기본 빌드 범위" 정책).

## Pipeline Position

- **Stage:** 8 (Simulator Content Design — ⑤ `tab-simulator`)
- **Input:** `structured.json`, Stage 4 산출물 (특히 `tabs_data/dissection.json`의 Execution Logic 카드)
- **Output:** `papers/[name]/tabs_data/simulator_spec.md` — Stage 10에서 Claude가 HTML을 직접 작성할 때 참조하는 설계 문서
- **렌더링 위치:** ⑤ `tab-simulator` (의사코드 + 인터랙티브 위젯 + 코드 비교)

## Referenced Rules

- `rules/analysis_rules.md`
- `rules/math_rules.md`
- `rules/component_rules.md`
- `rules/implementation_rules.md`

---

## 역할

논문의 **핵심 알고리즘**을 학습자가 손으로 만질 수 있는 시뮬레이터로 변환하는 설계서를 작성한다.

이 단계는 JS를 직접 작성하는 단계가 아니다. **결정 사항 문서**(어떤 슬라이더, 어떤 시각화, 어떤 baseline)를 markdown으로 정리해 두면, Stage 10(HTML Generation)에서 Claude가 이 spec을 보고 vanilla JS 위젯까지 단일 HTML 안에 인라인으로 작성한다.

---

## 산출 구조

`simulator_spec.md`는 다음 3 파트로 구성된다.

### Part 1 — 의사코드 (Pseudocode)

논문 알고리즘을 학습자가 읽기 쉬운 의사코드로 재작성.

**작성 원칙:**
- 논문 그대로의 수식이 아니라 **변수명에 의미가 보이는** 형태로 풀어쓴다 (`merged_groups`, `cumulative_attention_score`, `tokens_per_frame` 등)
- 핵심 단계마다 한국어 한 줄 주석 추가 (`# -- Merging stage (shallow) --`)
- 파이썬 의사코드(`python-pseudo` 언어 태그)로 통일. 진짜 동작 코드일 필요는 없지만 문법상 읽혀야 한다.
- 30~80줄 수준 (이보다 길면 본질이 흐려진다)

**출력 형식 (markdown 안에서):**

```markdown
## Part 1 — Pseudocode

언어 태그: `python-pseudo`

\`\`\`python
def algorithm_name(X, hyperparams):
    # -- 단계 1: ... --
    ...
    # -- 단계 2: ... --
    ...
    return result
\`\`\`

핵심 트릭 한 줄 요약: ...
```

### Part 2 — 인터랙티브 위젯 (Slider + Visualization)

학습자가 하이퍼파라미터를 움직이면 결과가 실시간으로 바뀌는 위젯 설계.

**결정 항목 (필수):**

| 항목 | 형식 | 예시 (FrameFusion) |
|---|---|---|
| 노출 슬라이더 | `[name, min, max, default, unit]` 4~6개 | `S_threshold` 0.5–0.95 step 0.01 / `N_threshold` 0–200 |
| 입력 프리셋 | 토글 또는 드롭다운 | 초기 토큰 수 `N` 프리셋: 840 / 13440 |
| 계산 로직 | 한국어 의사식 1~2문장 | "층마다 `N_l = max(N_{l-1} - merged_at_l, budget)` 계단형 갱신" |
| 시각화 형태 | canvas 라인차트 / 막대 / SVG | "층 축에서 4개 전략(Dense/StreamingLLM/FastV/Ours) 곡선 overlay + 4-bar prefill FLOPs 비교" |
| 출력 수치 | 실시간 갱신되는 숫자 박스 | "병합 종료 층, 최종 토큰 수, 상대 FLOPs" |
| 비교 baseline | 동시에 그릴 다른 방법 1~3개 | Dense / FastV / StreamingLLM |

**출력 형식:**

```markdown
## Part 2 — Interactive Widget

### Sliders
- `S_threshold` : 0.5 ~ 0.95, default 0.7, step 0.01, unit "유사도"
- `N_threshold` : 0 ~ 200, default 80, step 10, unit "토큰"
- ...

### Preset (선택)
- 초기 토큰 수 N : { "Llava-Video": 840, "Long-video": 13440 }

### 계산 로직
1. 입력 슬라이더 값으로 ...
2. 층마다 ... 계산
3. 최종 ... 산출

### 시각화
- 차트 1: ... (canvas)
- 차트 2: ... (4-bar 막대)

### 실시간 출력 수치
- 병합 종료 층: 정수
- 최종 토큰 수 / 초기 N: 비율
- 상대 prefill FLOPs: 정수 (Dense=100 기준)

### 비교 baseline
- Dense / FastV / StreamingLLM (overlay)
```

### Part 3 — 코드 비교 (Side-by-Side)

논문이 개선하는 **prior method**와 **본 논문**의 핵심 함수를 좌우로 배치한 비교 카드.

**선택 원칙:**
- 본 논문이 가장 직접적으로 비교/대체하는 **하나의 prior method**를 고른다
- 두 코드 모두 30~50줄 의사코드
- 좌우 대응 라인이 시각적으로 맞도록 구조를 정렬 (핵심 차이가 같은 줄 번호 부근에 오도록)
- 주석으로 "여기가 다른 부분" 표시

**출력 형식:**

```markdown
## Part 3 — Code Comparison

### 비교 대상
- Left: `FastV` (또는 prior method 이름)
- Right: `FrameFusion` (또는 본 논문 메서드 이름)

### 핵심 차이 한 줄 요약
prior는 ... 만 하지만, 본 논문은 ... 까지 한다.

### Code (Left)
\`\`\`python
def fastv_forward(X, layers, k):
    ...
\`\`\`

### Code (Right)
\`\`\`python
def framefusion_forward(X, layers, S_thr, N_thr, C):
    ...
\`\`\`

### 같은 줄 번호 대응 포인트
- L7 ↔ R10: prior는 단순 top-k, 본 논문은 cosine similarity 먼저 계산
- L12 ↔ R20: ...
```

---

## 결정 트리 — 무엇을 슬라이더로 노출할까

논문의 모든 하이퍼파라미터를 슬라이더로 만들지 않는다. 다음 기준으로 추린다:

1. **민감도가 높은 것** — 값이 조금만 바뀌어도 결과가 크게 변하는 파라미터 (논문이 ablation으로 보여준 것 우선)
2. **개념적으로 가르치고 싶은 것** — 학습자가 "이 값이 이걸 의미한다"를 손으로 느꼈으면 하는 변수
3. **Trade-off의 dial** — 속도/정확도, 메모리/품질 같은 명시적 trade-off의 단일 손잡이

학습 외 디테일(예: 학습률, 배치 크기, 옵티마이저)은 슬라이더 대상이 아니다.

---

## 결정 트리 — 무엇을 시각화할까

시뮬레이터의 차트는 학습자가 **Stage 4 dissection의 핵심 관찰을 직접 확인**할 수 있어야 한다.

| 논문 유형 | 권장 시각화 |
|---|---|
| 토큰/시퀀스 감축 | 층별 토큰 수 곡선, 상대 FLOPs 막대 |
| 메모리 최적화 | 메모리 사용량 막대 (3 컴포넌트), peak memory 라인 |
| 학습 효율 | 학습 시간/메모리 vs 성능 산점도 |
| 추론 가속 | 모델 크기 × 입력 크기에 따른 speedup 곡선 |
| Trade-off (품질↔비용) | Pareto front (x=cost, y=quality) |

baseline 비교는 **가능한 한 4개 이하** (Dense/Original + 2~3 prior methods + Ours).

---

## 분량 / 형식 가이드

- 의사코드 30~80줄
- 슬라이더 4~6개
- 비교 코드 좌·우 각 30~50줄
- `simulator_spec.md` 전체 길이 250~500줄 (참고용 결정 문서이므로 짧게)

---

## 절대 금지

- 진짜 동작하는 PyTorch/TF 코드를 출력하지 말 것 (이건 학습 도구다)
- 논문 알고리즘과 다른 동작을 시뮬레이트하는 것 금지
- 슬라이더 6개 초과 (학습자가 길을 잃는다)
- "그냥 보여주기 위한" 차트 — 모든 차트는 dissection의 핵심 관찰과 일대일 대응되어야 한다

---

## 이미지 생성

> Claude Code의 Bash tool로 `codex ...` 명령을 직접 실행해 ImageGen으로 PNG를 만든다. 별도 플러그인·MCP 자동화 없이 Bash 한 줄. 결과는 곧장 base64로 박아 `<figure class="concept-figure">` 정본 컴포넌트로 인라인 — 검수는 사후.
>
> **정식 호출 형식 (5계명 — Bash·UTF-8 prompt.txt·ASCII 인자·stdin null·스타일/출력 명시) + 검증된 명령 템플릿: `rules/component_rules.md` §11.**

이 단계에서 생성 가능한 이미지:
- ⑤ 탭 도입부의 **시뮬레이터 도입 일러스트** (학습자가 무엇을 만질 수 있는지 한 장으로 설명)
- 의사코드 핵심 단계의 **단계별 시각화** (예: Merging 단계가 토큰을 어떻게 합치는지의 추상화)
- 코드 비교(Part 3)의 좌·우 차이를 한눈에 보여 주는 **개념 비교 이미지**

저장 / 임베드:
- 저장 경로: `papers/[name]/assets/generated/`
- 파일명 규약: `simulator_<purpose>.png` (예: `simulator_intro.png`, `simulator_merging_step.png`)
- **HTML 임베드: base64 인라인 의무** (CLAUDE.md 자산 임베딩 정책)
- 인터랙티브 위젯 자체(canvas, 슬라이더 → 차트)는 JS로 구현 — ImageGen 대상이 아니다. **정적 보조 시각화에만** 사용.

생성된 이미지는 `simulator_spec.md`의 Part 1/2/3 각각에 `Image: <path>` 라인으로 명시 → Stage 10에서 Claude가 그 자리에 `<img>` 삽입.

---

## 참고 — 기존 정본의 시뮬레이터

- **SAFE**: LoRA 학습 메모리 시뮬레이터. 슬라이더 = (rank, freeze_ratio, ...). 시각화 = `csim-bar` 메모리 막대 + 코드 비교. (구버전 클래스 prefix `csim-*`. 신규 논문은 `sim-*` 사용.)
- **FrameFusion**: 토큰 감축 시뮬레이터. 슬라이더 4개 (`S_thr`, `N_thr`, `C`, `N`). 시각화 = canvas 4-curve overlay + 4-bar FLOPs. 클래스 prefix `sim-*` (정본).

→ 클래스 prefix는 `sim-*`로 통일 (자세한 컴포넌트 규칙: `rules/component_rules.md`).
