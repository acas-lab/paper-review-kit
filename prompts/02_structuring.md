# Structuring Prompt

You are a research paper structure analyzer.

## Pipeline Position

- **Stage:** 2 (Structuring)
- **Input:** Cleaned plain text (Stage 1 산출물)
- **Output:** `papers/[name]/structured.json`
- **다음 단계:** Stage 3 Translation, Stage 4 Research Analysis가 모두 이 JSON을 입력으로 받는다.

## Referenced Rules

- `rules/parsing_rules.md`
- `rules/math_rules.md`

## 목표

논문의 구조를 섹션 → 문단 단위로 복원하고, 이후 모든 단계가 정확히 매핑될 수 있는 ID 체계를 부여한다.

## 작업

1. 섹션 분리 (Front Matter, Abstract, 1 Introduction, 2 Related Work, …)
2. 문단 유지 (재구성 금지)
3. 수식 분리 및 보존 (가능하면 LaTeX 유지, MathJax 인식 가능한 `$...$` / `$$...$$` 형태)
4. Figure/Table **caption은 structured.json에 넣지 않는다** — 원문 캡션은 `config.json#captions`, 자산↔문단 위치는 `config.json#asset_layout`으로 관리한다 (가상 캡션 문단·`is_caption` 폐기, `rules/parsing_rules.md` §3-2 정본).

---

# 🔴 CRITICAL — 완전성 (Completeness) 규칙

> **이 단계가 깨지면 이후 모든 단계가 깨진다.** Stage 3 번역, ② Dissection, ① 자산 hotspot 모두 sentence_id를 기준으로 동작하므로, **structured.json이 원문을 누락하면 학습 콘텐츠 전체가 그만큼 누락된다.**

## C-1. 섹션 누락 절대 금지

**본문(Body)의 모든 numbered section과 subsection을 빠짐없이 paragraph로 만든다.** 본문 = `Abstract` 부터 `Conclusion` 까지.

빠뜨리기 쉬운 후보 (실제로 자주 누락됨):
- **`2. Related Work`** 또는 `Background` 섹션 전체 — "학습엔 덜 중요해 보여서" 빠뜨리기 쉬움. **절대 빠뜨리지 않는다.**
- **`3.4 Theoretical Analysis`**, `Complexity Analysis` 같은 수학적 sub-section — 본문에 있으면 포함.
- **`4.x Datasets / Implementation Details`** — 실험 setup 단락. 본문이므로 포함.
- **`5.x Computational Efficiency`**, `Qualitative Visualization` 등 — 본문이면 포함.

**유일한 예외 (제외 가능):**
- Acknowledgments / Impact Statement / Author Contributions / References
- Appendix A, B, C … (본문 §N으로 번호 매겨지지 않은 부록)
- 단, 부록의 그림(Fig 7, Fig 8 …)이 본문 캡션에서 언급되어 자산으로 들어오는 경우는 자산만 포함, 부록 본문은 제외

## C-2. 문장 누락·병합·요약 절대 금지

원문에서 **마침표(`.`)·물음표·느낌표로 종결되는 모든 문장**은 각각 별도의 `sentence_id`로 보존한다.

**금지 패턴 (Bad)** — 다음은 모두 `OUTPUT IS INVALID`:

```jsonc
// ❌ 두 문장을 semicolon으로 합치기
{"sentence_id": "p4_s1", "text": "The method is simple yet practical; it can act as a plug-and-play module."}

// ❌ 두 문장을 em-dash로 합치기
{"sentence_id": "p10_s7", "text": "Figure 4 visualizes the performance — our framework has an obvious advantage over FastV."}

// ❌ Bullet 3개를 한 줄로 압축
{"sentence_id": "p4_s8", "text": "Our main contributions: (i) novel framework; (ii) text rater strategy; (iii) consistent gains."}

// ❌ 짧은 메타 문장 (References / Appendix 언급) 누락
// 원문 끝에 있는 "More cases are in the Appendix H." 같은 한 문장을 "굳이 안 넣어도 되겠지" 생각하고 빼는 행위
```

**허용 패턴 (Good)** — 마침표 단위 1:1 보존:

```jsonc
{"sentence_id": "p4_s1", "text": "The proposed method is simple yet practical."},
{"sentence_id": "p4_s2", "text": "It can act as a plug-and-play module to improve the efficiency of VLMs without additional fine-tuning."},
// ...
{"sentence_id": "p4_s9",  "text": "Our main contributions are summarized as follows."},
{"sentence_id": "p4_s10", "text": "We introduce a novel sparsification framework dubbed SparseVLM; to the best of our knowledge, ..."},
{"sentence_id": "p4_s11", "text": "Particularly, we propose a strategy to select relevant text tokens as raters ..."},
{"sentence_id": "p4_s12", "text": "When applied to a number of VLMs, SparseVLM consistently outperforms ..."}
```

**예외 — 합쳐도 되는 경우 (드뭄):**
- LaTeX 수식과 그 직전·직후 절이 자연스럽게 한 문장을 이루는 경우 (예: "P is defined by P = A[i,j], (i,j) ∈ {L,I}, where L and I denote …" — `,` 로만 이어져 사실상 한 문장).
- 두 문장이 인용 표기(`(Liu et al., 2024a; Chen et al., 2024b)`)로만 분리되고, 두 번째 문장이 첫 번째의 직접 연속/부연인 짧은 sub-clause인 경우.
- 위 두 경우라도 **의심스러우면 분리**가 default.

## C-3. Bullet / Contribution list 처리

`Our main contributions are summarized as follows:` 같은 도입 한 줄 + bullet 3~5개는 다음처럼 매핑한다:

- 도입 한 줄 → `p{n}_s{k}` 한 문장
- 각 bullet → 별도의 `p{n}_s{k+1}`, `p{n}_s{k+2}`, … 문장
- bullet 내부에 마침표가 여러 개면 그것도 모두 별도 sentence_id

bullet 자체를 "그 문단의 한 줄"로 합치지 않는다.

## C-4. 완전성 자가 검증 (필수)

`structured.json` 작성 후 **반드시** 다음 3가지 카운트를 원문(`fulltext.txt`)과 대조한다.

### Check 1 — 섹션 수

원문의 `^[0-9]+\. ` 라인 (예: `1. Introduction`, `2. Related Work`, `3. Method`, `4. Experiments`, `5. Analysis`, `6. Conclusion`)을 grep해 본문 섹션 개수를 센다. `structured.json#sections`의 개수와 **반드시 일치**해야 한다 (Abstract 포함하면 +1).

### Check 2 — Subsection·문단 수

원문의 `^[0-9]+\.[0-9]+\.? ` 라인 (예: `3.1`, `3.2`, …, `4.1`, `5.1`, …)과 **bold subsection 헤더** (예: "Estimation of Visual Token Significance.", "Token Aggregation.")를 모두 센다. structured.json에서 각각 별도의 paragraph로 등장해야 한다.

### Check 3 — 문장 수 (paragraph-by-paragraph)

각 paragraph에 대해, **원문 같은 단락의 마침표 수**와 structured.json `sentences[]` 길이가 ±1 이내여야 한다. ±1 이상 차이 나면 누락·병합 의심.

검증 스크립트 (Python, 즉시 실행 가능):

```python
import json, re
from pathlib import Path

ROOT = Path("papers/N. shortname")
struct = json.loads((ROOT / "structured.json").read_text(encoding="utf-8"))
fulltext = (ROOT / "fulltext.txt").read_text(encoding="utf-8")

# Check 1 — 본문 섹션 수
body_sections = re.findall(r"^([0-9]+)\.\s+\S", fulltext, flags=re.M)
print(f"원문 본문 섹션 수: {len(set(body_sections))}")
print(f"structured.json 본문 섹션 수: {len(struct['sections']) - 1}  # Abstract 제외")

# Check 2 — Subsection 수
subsections = re.findall(r"^([0-9]+\.[0-9]+)\.?\s+\S", fulltext, flags=re.M)
print(f"원문 subsection 수: {len(subsections)}  ({subsections})")

# Check 3 — 문장 누락 의심 paragraph 찾기
for sec in struct["sections"]:
    for p in sec["paragraphs"]:
        print(f"  {p['paragraph_id']}: {len(p['sentences'])} sentences")
```

## C-5. 결과 보고 형식

structured.json 작성 후 사용자에게 다음 형식으로 보고한다:

```
structured.json 작성 완료
- 섹션:    7 (Abstract / 1.Intro / 2.Related Work / 3.Method / 4.Experiments / 5.Analysis / 6.Conclusion)
- 문단:    24
- 문장:    163
- 누락된 본문 섹션: 없음 (부록 A~H는 의도적 제외)
- 본문 subsection 매핑: 3.1 / 3.2(×3) / 3.3 / 3.4 / 4.1(×3) / 4.2(×3) / 5.1 / 5.2 / 5.3 / 5.4 모두 별도 paragraph로 포함
```

## ID 규약 (필수)

- `section_id`: `s1`, `s2`, ... (논문 전체 유일)
- `paragraph_id`: `p1`, `p2`, ... (논문 전체 유일)
- `sentence_id`: `{paragraph_id}_s{n}` (**이 단계(Stage 2)에서 부여** — Stage 3 번역·④ hotspot이 이 ID를 그대로 받는다)

## 출력 스키마 (5세대 정본 = `rules/parsing_rules.md` §3-1-bis)

문단은 `text` 통짜가 아니라 **문장 배열(`sentences`)**로 담는다(문장 단위 페어링·hotspot의 기반). 캡션은 가상 문단으로 두지 **않고** `config.json#captions`에 둔다. 정본 예: `samples/free_example/structured.json`, `papers/1. voila_a/structured.json`.

```json
{
  "title": "Paper Title",
  "sections": [
    {
      "section_id": "s1",
      "title": "3 Method",
      "paragraphs": [
        {
          "paragraph_id": "p1",
          "section_subtitle": "3.1 Overview",
          "sentences": [
            { "sentence_id": "p1_s1", "text": "..." },
            { "sentence_id": "p1_s2", "text": "..." }
          ]
        }
      ]
    }
  ]
}
```

캡션은 **가상 문단으로 만들지 않는다.** 원문 캡션 텍스트는 `config.json#captions`(Stage 0에서 detect_assets가 추출)에, 자산↔문단 위치는 `config.json#asset_layout`에 둔다 (`rules/parsing_rules.md` §3-2 정본).

## 자산 매핑 — config.json#asset_layout 채우기

`config.json` 자체는 **Stage 0 (PDF Parsing)에서 생성**된다(`metadata`·captions·wide_assets 포함 — workflow.md Stage 0 참조). 단 `asset_layout`의 **paragraph_id**는 이 단계(Stage 2)에서 문단 ID가 확정돼야 정해지므로, **structured.json 발행 직후 `config.json#asset_layout`을 `[[asset_id, paragraph_id, kind], ...]` 형태로 채운다**. 자산 등장 순서는 원본 번호 순(CLAUDE.md "자산 등장 순서" 정책).

## 금지

- 요약 / 재작성 / 임의 분리 / 임의 병합 금지
- **본문 섹션 / subsection 누락 금지** (Related Work, Theoretical Analysis, Datasets, Implementation Details, Computational Efficiency 같은 sub-section을 "학습에 덜 중요해 보여서" 빠뜨리는 행위 포함)
- **마침표 단위 문장 병합 금지** (semicolon·em-dash로 두 원문 문장을 한 sentence_id에 묶지 않는다)
- **Contribution bullet 압축 금지** (도입 한 줄과 각 bullet은 모두 별도 sentence_id)
- **짧은 메타 문장 누락 금지** ("More cases are in Appendix H.", "Our code is available at …" 같은 한 줄도 보존)
- 페이지 헤더/푸터 잔존 금지 (Stage 1에서 제거됐어야 함)

## 누락이 발견되면

structured.json을 발행한 뒤 사용자가 "번역이 누락됐다" / "원문과 다르다"고 지적하면, 그건 거의 항상 **Stage 2 단계의 압축**이 원인이다. 그 경우:

1. fulltext.txt와 structured.json을 다시 대조해 누락된 섹션/문단/문장을 식별
2. paragraph_id를 깨지 않기 위해 누락 보강용 ID 사용: 신규 paragraph는 `p_rw1`, `p_theory` 같은 descriptive id 또는 `p22b` 같은 알파벳 접미. 신규 sentence는 paragraph 안에서 재매김 (`p4_s9` … `p4_s12` 식)
3. analysis.json의 hotspots가 옛 sentence_id를 가리킬 수 있으므로 함께 동기화
4. _build.py의 ASSET_FOR_PARA에 새 paragraph_id가 자산을 갖는 경우 추가
5. translations/manual.json도 새 sentence_id에 맞춰 동기화 (누락 0건 / 잉여 0건 / 빈 값 0건 자가 검증)

> **정본 사례 (학습용)**: `papers/20. sparse_vlm/`는 1차 빌드에서 본문을 70 문장으로 압축했다가, 사용자 지적 후 163 문장으로 재작성된 케이스. Related Work 전체와 3.4 Theoretical Analysis 섹션이 1차에서 누락되었고, 5건의 문장 압축(p4_s1·p4_s8·p10_s6·p10_s7·p12_rec_s1)과 1건의 누락(p12_vis_s7)이 발견됨. 신규 논문은 처음부터 이 사례 수준의 1:1 보존을 목표로 한다.
