# Translation Prompt

## Pipeline Position

- **Stage:** 3 (Translation)
- **Input:** `papers/[name]/structured.json`
- **Output:** `papers/[name]/translations/manual.json` (1차) → (선택) `translations/refined.json` (2차)
- **편의용:** sentence_id ↔ 원문 ↔ 번역을 한 파일로 합친 `translated.json`을 만들어 두면 Stage 10에서 참조하기 편하다 (선택)
- **렌더링 위치:** ① `tab-reading` (좌-원문 / 우-번역 양방향 호버)

## Referenced Rules

- `rules/math_rules.md`
- `rules/knowledge_rules.md`

---

# CRITICAL RULE (최상위 규칙)

You MUST preserve 100% of the original content.

- DO NOT summarize
- DO NOT paraphrase
- DO NOT remove any sentence
- DO NOT merge sentences

Each sentence MUST appear in output. If any sentence is skipped → OUTPUT IS INVALID.

## Stage 2 산출물 사전 검증 (필수)

번역 시작 전, **`structured.json` 자체가 원문을 누락하고 있는지** 먼저 확인한다. 번역 단계의 "100% 보존"은 structured.json을 기준으로 하므로, structured가 압축되어 있으면 번역만 잘해도 본문이 누락된다.

검증 절차 (Python 한 토막):

```python
import json, re
from pathlib import Path
ROOT = Path("papers/N. shortname")
struct = json.loads((ROOT / "structured.json").read_text(encoding="utf-8"))
fulltext = (ROOT / "fulltext.txt").read_text(encoding="utf-8")

# 본문 섹션 수 (Abstract 포함하면 +1)
print(len(struct["sections"]), "vs", len(set(re.findall(r"^([0-9]+)\.\s+\S", fulltext, flags=re.M))))

# Subsection 수
print(re.findall(r"^([0-9]+\.[0-9]+)\.?\s+\S", fulltext, flags=re.M))

# 각 paragraph의 sentence count
for sec in struct["sections"]:
    for p in sec["paragraphs"]:
        print(f"  {p['paragraph_id']}: {len(p['sentences'])}")
```

대조해서 누락된 본문 섹션 / subsection / 짧은 메타 문장이 있으면 **Stage 2로 돌아가 보완한 뒤** 번역을 시작한다. 자세한 검증 기준: `prompts/02_structuring.md` § 🔴 CRITICAL 완전성 규칙.

---

## OUTPUT FORMAT

`translations/manual.json`의 정식 스키마 (사람과 Claude가 직접 작성한다 - 별도 변환 스크립트는 없다):

```json
{
  "sentence_id": "p3_s1",
  "original": "원문 그대로",
  "translation": "한국어 번역 (직역 우선)",
  "interpretation": "(선택) 학습자용 의역 또는 의미 풀이"
}
```

JSON 배열로 묶어 `translations/manual.json` 또는 `translations/refined.json`에 저장한다.

`sentence_id`는 `{paragraph_id}_s{문장순번}` 형식 (예: `p3_s2`). **누락은 0건**이어야 한다.

---

## 번역 원칙

- **직역 우선:** 의역은 별도 `interpretation` 필드에서 한다.
- **기술 용어 유지:** `Attention`, `KV-cache`, `Token` 등은 영문 그대로. 처음 등장 시 `Attention (주의 메커니즘)` 식으로 한글 풀이를 괄호 병기 (이후엔 영문만).
- **수식 보존:** `$...$`, `$$...$$`는 LaTeX 그대로 옮긴다. 수식 안의 변수/심볼은 번역하지 않는다.
- **인용/각주/Equation 참조:** `Eq. 1`, `Fig. 2`, `Table 3` 같은 표기는 그대로 유지 (탭 간 ref-link 자동 anchor가 이 패턴을 인식).

---

## 🔴 부등호·수식 표기 이스케이프 (정책, 2026-07-08)

**번역문(translation)은 빌더가 HTML에 raw 삽입한다** (원문 original은 esc() 자동 이스케이프 —
번역문은 아니다). 따라서 번역문 안의 `<`+영문자(`X_{a<i}`, `y_<t`, `0.1<IOU<0.5` 류)는 태그로
파싱되어 문서 뒷부분 전체를 깨뜨린다. 수식·부등호를 옮길 때 `&lt;`/`&gt;`로 쓸 것.
정본 규칙·검사 도구: `rules/math_rules.md` § 부등호·꺾쇠 (`tools/check_html_escape.py`).

## 🔴 em-dash 금지 (정책, 2026-09-10)

한국어 prose(번역문·② ~ ⑥ 탭 서술·캡션 번역·study.json 분석 등 Claude가 직접 쓰는 모든 한국어 문장)에서는 em-dash(`—`, U+2014) 대신 하이픈(`-`)을 쓴다. 영어 원문(`original`·`structured.json`의 `text`·`captions_en`)의 em-dash는 저자 텍스트이므로 그대로 보존한다. 일괄 교정 도구: `tools/fix_hl_and_dash.py`.

## 🔴 무리한 한국어 변환 금지 (정책)

기본 전문용어·일반 영어 표현을 **자력으로 한국어 신조어로 옮기지 않는다.** "한국어로 옮길 수 있다"와 "한국어로 옮겨야 한다"는 다르다. 한국 ML 커뮤니티에서 굳어진 표기가 없으면 영문을 그대로 둔다. 직역하면 "사전적으로는 맞지만 한국어로는 어색"한 경우가 가장 흔한 실패 모드.

### 의사결정 순서 (각 영어 표현마다)

1. 한국 ML 학계·커뮤니티에 굳어진 표기가 있는가? → 있으면 그것을 쓴다 (예: attention → 어텐션, fine-tuning → 파인튜닝, pooling → 풀링, hallucination → 환각, embedding → 임베딩, gradient → 그래디언트, projection → 투영, norm → 노름).
2. 없으면 **영문 그대로** 쓴다. 음역도 만들지 않는다.
3. 의미가 안 통할 우려가 있으면 **첫 등장에만** 괄호로 짧은 한글 풀이를 병기 (이후엔 영문만).

### 안티패턴 — 다음 변환은 만들지 말 것

| 안 좋은 한국어 변환 | 권장 | 이유 |
|---|---|---|
| 거친 데이터셋 (crude dataset) | `crude dataset` | "거친"은 surface texture 뉘앙스 — ML의 "정제 전" 의미가 안 살아남 |
| 이진 투표 (Binary Polling) | `Binary Polling` | Polling은 모델에 yes/no 질의하는 행위 — "투표"와 작동 방식 다름 |
| 워밍업 파인튜닝 (warm-up fine-tuning) | `warm-up fine-tuning` | "워밍업"이 운동 비유로 읽혀 ML 맥락과 부조화 |
| 고충실도 (high-fidelity) | `high-fidelity` | 오디오 맥락 음역어 — 이미지 이해에는 부조화 |
| 강한 정렬을 보임 (strong alignment) | "잘 들어맞음" / "잘 부합" | "정렬"은 ML 표준이지만 "강한 정렬"은 비유로 어색 |
| 정보성 있는 객체 (informative) | "정보가 풍부한 객체" | "정보성"은 한국어 자연어가 아님 |
| 노동을 요구하는 (laborious) | "노동집약적인" | 영어 술어 구조의 직역 |
| 적합성을 높이고 (relevance) | "관련성을 높이고" | relevance ≠ fitness — "적합성"은 fitness 뉘앙스 |
| 능력 차원 커버리지 (capability dimensional coverage) | "능력 차원 분포" | 3-단어 한자어 합성은 거의 항상 어색 |
| 순위화해 보존 (rank and retain) | "순위를 매겨 보존" | "순위화"는 일본식 한자조어 |
| 정보성 토큰 / 정보성이 풍부한 | "정보가 풍부한 토큰" | 동일 |

### 추가 점검 — 의심 패턴 자동 감지

번역 완료 후 다음 정규식으로 자가 검토:

```python
import re, json
sus_patterns = [
    r"거친 [가-힣]",        # 거친 데이터셋·거친 학습셋 류
    r"^.{0,40}성 있는 ",     # 정보성 있는·실용성 있는 등 N성+있는
    r"화해 ",                # 순위화해·정량화해 — "X화해 Y한다" 패턴 의심
    r"노동을 요구",          # laborious 직역
    r"이진 투표",            # binary polling 오역
    r"워밍업 [가-힣]",       # warm-up X 류
    r"고충실도",             # high-fidelity 음역
    r"강한 정렬",            # strong alignment 직역
    r"능력 차원 커버리지",   # capability dimensional coverage
]
mj = json.loads(open("translations/manual.json", encoding="utf-8").read())
for s in mj["sentences"]:
    for p in sus_patterns:
        if re.search(p, s["translation"]):
            print(s["sentence_id"], "—", s["translation"][:80])
```

매칭이 있으면 위 표를 참조해 수정한다.

### 자연스러움 자가 점검

번역문을 **소리 내어 한 번 읽어 보고** 다음 중 하나라도 해당하면 손본다:
- "이게 한국어로 자주 쓰는 표현인가?" → No
- "ML 학회 발표에서 사용자가 이렇게 말할까?" → No
- "원문보다 더 어색하게 들리는가?" → Yes

영문 그대로 두는 것이 직역보다 거의 항상 낫다 — 학습자도 어차피 영어 학회 발표·논문 PDF를 다시 읽기 때문이다.

---

## 금지

- 문장 누락
- 임의 병합 / 분리
- 백과사전식 부연 설명 (그건 Stage 6/7의 역할)
- 위 안티패턴 표의 직역 형태 재도입
