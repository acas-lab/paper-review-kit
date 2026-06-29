# Parsing Rules

## 🎯 목적

논문 텍스트를 "읽을 수 있는 형태"가 아니라
**"이후 모든 단계가 정확히 매핑될 수 있는 구조"**로 복원한다.

이 규칙은 Stage 0 (PDF Parsing) ~ Stage 2 (Structuring)에 적용된다.

---

## 1. Sentence Integrity

- 문장은 절대 끊지 않는다 (Stage 1 Cleaning 관점)
- 줄바꿈으로 분리된 문장은 반드시 복원한다
- 단어 깨짐은 반드시 복구한다 (예: `con￾tinuity` → `continuity`)
- 하이픈 줄바꿈(`some-\nthing` → `something`) 처리

### 1-bis. 1:1 Sentence Preservation (Stage 2 관점)

Stage 2 Structuring에서는 반대로 **원문의 마침표 단위 문장을 절대 합치지 않는다.**

- 마침표(`.`)·물음표·느낌표로 종결되는 모든 문장은 별도 `sentence_id`
- semicolon(`;`)·em-dash(`—`)·comma(`,`)로 두 원문 문장을 한 `sentence_id`에 묶는 것 금지
- bullet list 도입부와 각 bullet은 각각 별도 `sentence_id`
- 짧은 메타 문장(`"More cases are in Appendix H."`, `"Our code is available at …"`)도 보존
- 예외 — 합치기 허용: LaTeX 수식 안의 절(예: `where L and I denote …`)이 직전 문장과 자연 연속, 인용 표기로만 분리되는 짧은 sub-clause. 의심스러우면 분리가 default.

> 자세한 검증 절차와 금지 패턴: `prompts/02_structuring.md` § 🔴 CRITICAL 완전성 규칙.

---

## 2. Paragraph Structure

- 문단 단위 구조를 유지한다
- 문단 간 논리 흐름을 보존한다
- 문단을 임의로 병합하거나 분리하지 않는다

### 2-tool. 🔴 정본 구조화 도구 — `tools/structure_paper.py` (2026-06-29)

Stage 2 구조화는 **`python tools/structure_paper.py "<pdf>" "papers/N. name/structured.json"`** 로 시작한다 — 본문 전체(Abstract→Conclusion)를 컬럼 reading order로 1:1 캡처(de-hyphenate·ligature(ﬁ→fi)·× 기호 복원·문장 분할·figure 내부 라벨 2D bbox로 제외·References/Appendix 중단). **손으로 본문 일부만 담거나 문장을 합치지 말 것.** CLI·웹이 같은 도구를 쓰므로 structured.json이 동일 → ① 번역 탭 커버리지가 통일된다(§ CLAUDE.md web↔CLI 통일성). 출력은 완전한 1차 결과이며, 드물게 reading-order로 끊긴 fragment(예: 컬럼 경계에서 잘린 문장)는 사후 가벼운 정리. 정본 사례: `papers/1. fastvlm`(166문장)·`papers/2. voila_a`(189문장) — 손으로 33/28문장만 담았던 1차 빌드의 "번역 본문 찾기 문제"를 이 도구로 전 본문 캡처해 해결.

### 2-bis. 본문 섹션·subsection 완전 보존

- 본문(Abstract → Conclusion)의 모든 numbered section과 subsection을 빠짐없이 paragraph(s)로 만든다
- 빠뜨리기 쉬운 후보 (실제로 누락 사례 발생): `Related Work`, `Theoretical Analysis`, `Complexity Analysis`, `Datasets`, `Implementation Details`, `Computational Efficiency`, `Qualitative Visualization`
- "학습에 덜 중요해 보여서" 같은 판단으로 본문 섹션을 빠뜨리지 않는다 — 그 판단은 Stage 4 이후의 책임
- 유일한 예외: Acknowledgments / Impact Statement / Author Contributions / References / Appendix (본문 §N으로 번호 매겨지지 않은 부록)

> 누락 사례·정본 검증 스크립트: `prompts/02_structuring.md` § C-4 완전성 자가 검증.

---

## 🔥 3. Alignment Rules (핵심)

### 3-1. Section / Paragraph / Sentence ID

식별자 체계 (논문 전체에서 유일):

| 레벨 | 형식 | 부여 단계 | 예시 |
|---|---|---|---|
| Section | `s1`, `s2`, ... | Stage 2 Structuring | `s3` (Introduction) |
| Paragraph | `p1`, `p2`, ... | Stage 2 Structuring | `p20` (캡션 포함) |
| Sentence | `{paragraph_id}_s{n}` | Stage 3 Translation | `p20_s2` |

> **사후 누락 보강용 ID** — 빌드 후 누락된 문단을 추가할 때는 기존 ID를 흐트리지 않기 위해 `p22b`, `p22c` 같은 알파벳 접미 ID를 쓴다. 문장은 `p22b_s1`, `p22b_s2`. 4세대 ViT 빌드의 `p22b "Metrics"` 문단이 정본 사례.

### 3-1-bis. structured.json 키 표준 (5세대 정본)

`papers/[name]/structured.json`은 다음 형식을 따른다 (12. deep_compression 이후 정본):

```json
{
  "title": "Paper title",
  "authors": ["..."],
  "venue": "ICLR 2021",
  "sections": [
    {
      "section_id": "s1",
      "title": "Abstract",
      "paragraphs": [
        {
          "paragraph_id": "p1",
          "section_subtitle": "3.1 Vision Transformer (ViT)",
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

**필수 키**:
- Section: `section_id`, `title`, `paragraphs`
- Paragraph: `paragraph_id`, `sentences`
- Sentence: `sentence_id`, `text`

**선택 키**:
- Paragraph: `section_subtitle` — 한 섹션 안에 여러 sub-section 헤더가 있을 때 그 헤더를 문단에 붙임 (예: \"3.1 Vision Transformer (ViT)\", \"4.2 Comparison to State of the Art\"). 빌더가 paragraph 위에 별도 라인으로 렌더.
- Section: `authors`, `venue` 같은 메타데이터는 `config.json#metadata`로 옮겨도 무방 — `structured.json`은 본문에 집중.

**Deprecated (4세대 이전 형식)**:
- Section의 `title_en` / `title_kr` 두 필드 분리는 더 이상 쓰지 않는다 — `title` 한 필드로 통일.
- Paragraph의 `page` / `text` 필드는 5세대에서 생략 가능 (페이지 정보는 디버깅 용도이며 빌더가 쓰지 않음). 본문은 `sentences[]`로만 표현.

### 3-2. Asset Mapping (5세대 정본)

각 figure / table은 **두 곳에서** 참조된다:

1. **본문 문단의 문장에서 자연스럽게 인용** — `structured.json`
   ```json
   {
     "sentence_id": "p12_s2",
     "text": "Figure 1 shows the model architecture..."
   }
   ```
   별도의 `is_caption` 가상 문단을 두지 않는다 — 캡션 텍스트는 `config.json#captions`에 들어간다.

2. **`config.json#asset_layout`** — 자산을 어느 문단 아래에 표시할지 (**list 형식**)
   ```json
   {
     "asset_layout": [
       ["fig_1",   "p12", "figure"],
       ["fig_2",   "p13", "figure"],
       ["table_1", "p21", "table"],
       ["table_2", "p24", "table"]
     ],
     "wide_assets": ["fig_2", "table_1", "table_2"],
     "captions": {
       "fig_1": "Original caption text from the paper...",
       "table_1": "..."
     }
   }
   ```

   - 형식: `[[asset_id, paragraph_id, kind], ...]`. 한 paragraph에 여러 자산이 붙을 때는 같은 paragraph_id로 여러 줄을 추가.
   - `kind`: `"figure"` 또는 `"table"`.
   - `wide_assets`: 가로로 넓어 `asset-wide` 클래스로 페이지 폭을 살짝 넘게 렌더할 자산 ID 리스트.
   - `captions`: 자산별 원문 캡션 — 빌더가 `<figcaption>`의 `asset-cap`로 렌더.

### 3-2-bis. 🔴 자산 등장 순서 — 번호 순(numerical order) 정본

**원칙**: ① 원문/번역 탭에서 자산이 등장하는 순서는 **원본 논문의 figure/table 번호 순서를 따른다.** `fig_1 → fig_2 → … → fig_N`, `table_1 → table_2 → … → table_N`. 도중에 번호 점프(예: `fig_3 → fig_7 → fig_4`)가 생기면 학습자가 "왜 갑자기?"라고 의아해하므로 금지.

**Appendix figure 처리**: 부록 그림(예: 본문 fig_1~6 다음 appendix A의 fig_7)은 **본문 마지막 figure 뒤**에 둔다 — 가장 자연스러운 자리는 보통 마지막 분석/시각화 문단(5.x Qualitative 류). "개념적 관련성"이 본문 중간 문단에 더 가까워 보여도, 번호 점프를 만들지 않는다.

**개념 정합성과 충돌 시**: 번호 순서 우선. 개념 설명은 `analysis.json#interpretations` / `beginner_notes` / `study_modals`에서 cross-reference로 풀어주면 충분 — 자산 자체를 옮기지 않는다.

**자가 검증**: build 후 다음 Python 한 토막으로 자산 등장 순서를 출력해 확인:

```python
import re
html = open(f"papers/[name]/[Short].html", encoding="utf-8").read()
s = html.find('id="tab-reading"'); e = html.find('id="tab-dissection"')
reading = html[s:e]
order = re.findall(r'<figure class="asset-card[^"]*" id="([a-z_0-9]+)"', reading)
figs = [a for a in order if a.startswith("fig_")]
tabs = [a for a in order if a.startswith("table_")]
assert figs == sorted(figs, key=lambda x: int(x.split("_")[1])), f"figure 번호 점프: {figs}"
assert tabs == sorted(tabs, key=lambda x: int(x.split("_")[1])), f"table 번호 점프: {tabs}"
```

> 정본 학습 사례 (실패→복구): SparseVLM 초기 빌드는 fig_7(Appendix A redundancy diagram)이 "개념적으로 p8(rank-기반 redundancy 메커니즘)에 어울린다"는 이유로 p8에 붙어, 등장 순서가 `fig_1→2→3→**7**→4→5→6`이 됐다. 사용자가 "왜 3 다음 7?"이라 지적 → fig_7을 p12_vis(5.4 Qualitative 끝)로 이동해 `1→2→3→4→5→6→7` 자연 순서 회복. 동일 실수 재발 방지가 이 정책의 직접 동기.

**Deprecated (4세대 이전 형식)**:
- `"asset_layout": { "p20": [["fig_2", "figure"]] }` 같은 dict 형식은 더 이상 쓰지 않는다. 12. deep_compression 이후 모든 빌더는 list 형식을 가정한다.

### 3-3. Content Mapping

모든 생성 콘텐츠는 ID에 정확히 매핑한다:

| 콘텐츠 | 키 | 위치 |
|---|---|---|
| 번역 | `sentence_id` | `translations/*.json` |
| 콜아웃 | `paragraph_id` | `analysis.json#callouts` |
| 핫스팟 | `paragraph_id` → `[sentence_id]` | `analysis.json#hotspots` |
| 자산 해석 | `asset_id` (`fig_N`, `table_N`) | `analysis.json#interpretations` |
| 초보자 노트 | `asset_id` | `analysis.json#beginner_notes` |
| 자가점검 | `section_id` | `analysis.json#quizzes` |

---

## 4. Figure / Table Handling

- Figure / Table은 절대 문맥에서 분리하지 않는다 (별도 갤러리 탭 금지)
- `asset_layout`에 등록된 문단 바로 아래에 inline 렌더
- **자산 등장 순서는 원본 번호 순서 (fig_1→2→…→N, table_1→2→…→N) 보존** — 번호 점프 금지. Appendix figure는 본문 마지막 figure 뒤에 배치 (§3-2-bis)
- caption은 structured.json에 넣지 않고 `config.json#captions`에 둔다 (가상 문단·`is_caption` 폐기 — §3-2 정본)
- 이미지 자산은 `papers/[name]/assets/{fig_N|table_N}.png` 경로 고정

---

## 4-A. Asset Cropping (PDF 종류별)

PDF에서 자산 PNG를 잘라낼 때, 먼저 **PDF가 vector인지 OCR'd 스캔본인지** 확인한 뒤 알고리즘을 고른다.

### 판별
```python
imgs = page.get_images(full=True)
# vector PDF: figure마다 별도 image 객체 → bbox 정확
# 스캔본:    페이지 전체가 한 비트맵, bbox = full page
```

`page.get_image_bbox(item)`이 페이지 전체 크기와 같으면 스캔본 → 3-pass 알고리즘.

### vector PDF — 콘텐츠 인식 자동 bbox (정본, 2026-06-29)

🔴 **정본 도구 = `tools/autocrop_assets.py`.** 좌표를 손으로 추측·하드코딩하지 말 것. 이 도구는 캡션 + **그 페이지의 실제 벡터 드로잉(plot 축·화살표·표 ruling line)과 raster image**로부터 각 figure/table의 진짜 경계를 계산해 한 번에 figure·도표 **전체**(모든 sub-panel + 라벨 + 캡션)를 잡는다.

```bash
python tools/autocrop_assets.py "rawpaper/<논문>.pdf" "papers/N. name/assets"
python tools/autocrop_assets.py --verify "papers/N. name/assets"   # 여백(잘림) 자동 점검
# 라이브러리: from tools.autocrop_assets import autocrop; autocrop(pdf, out_dir, dpi=200)
```

**알고리즘 (캡션 1개당):**
1. 캡션 bbox → x-span으로 **column band**(full / left / right) 분류.
2. **그래픽 요소** 수집 = `get_drawings()` rect + `get_image_rects()`. 클리핑·필터: 풀페이지 배경, header(y<56)/footer(y>745), 점(point) 제거. **단 zero-thickness 선(표의 가로 rule h=0, 세로 separator w=0)은 반드시 보존** — 이걸 버리면 borderless/stroke 표가 통째로 사라진다.
3. 이 캡션이 **소유하는 구간** = x-범위가 겹치는 인접 캡션들 사이. 후보 요소는 중심 y가 이 구간 안에 드는 것만.
4. 캡션에 인접한 쪽(위/아래)에서 그래픽 **클러스터의 run**을 키운다: gap이 작으면 무조건, 중간이면 **충분히 높거나(MIN_PANEL_H) 충분히 넓을 때만**(>0.25W=표 ruling line) 병합 → 적층 sub-panel·thin 표 row band는 잇고 본문 속 얇은 narrow stray는 안 잇는다. **borderless 표**(상·하 rule만 있고 본문은 rule 없는 텍스트 행)는 두 **wide rule** 사이를 최대 TABLE_GAP(380pt)까지 bridge(인접 캡션으로 이미 bound되어 안전). run은 **병합된 클러스터 bbox**라 다음 단계는 run의 y-범위 안 **개별 요소**로 다시 계산한다.
5. **full-width 판정은 CORE 콘텐츠로**: CORE = 충분히 넓은(>25pt) 개별 요소 − **배경 패널**(다른 요소들을 가로로 *포함*하면서 폭이 0.28W~0.7W인 국소 컨테이너 — 예: 파이프라인 그림의 둥근 배경). 배경 패널은 gutter를 가로질러 옆 단 본문과 겹칠 수 있으므로 band 판정·crop x-범위 어디에도 관여시키지 않는다(실제 콘텐츠는 그 안의 box). CORE가 페이지 중앙선 좌·우를 모두 덮을 때만 full-width. crop의 x-범위도 CORE 기준 → anchor가 본문이 아니라 gutter에 떨어진다.
6. 🔴 **픽셀 여백 패스 (`_refine_rect`)**: vector rect를 padding해 렌더한 뒤, **각 가장자리의 실제 콘텐츠 경계를 픽셀로 찾아 MARGIN_PX 여백을 남긴다.** vector bbox가 놓치는 미세 잘림(anti-aliasing·glyph ascender·plot marker·축 라벨)을 보정하고 **모든 변에 깨끗한 여백을 보장**. 세 가지 핵심: ① 스캔 anchor는 **콘텐츠 경계**(vector rect를 PAD만큼 안쪽)에서 시작 → 캡션-위 표 바로 아래 본문이 PAD만큼 가까워도 스캔이 본문 속에서 시작하지 않음. ② 여백은 **흰 픽셀로만, MARGIN_PX까지** 확장 → 표 바로 아래 본문이 MARGIN_PX보다 가까우면 그 gap까지만(본문 안 침범). ③ 바깥 확장은 figure=mid-gutter / full-width=페이지 여백 / 세로=인접 캡션·header-footer gap으로 제한. body text는 드로잉이 없고 스캔은 첫 흰 줄에서 멈추므로 누수 불가.
7. `--verify`로 결과 PNG의 2px 테두리에 잉크가 닿는지(=여백 없음=잘림) 자동 점검. clean이면 OK.

**왜 `page.get_image_bbox` 단독으로는 부족한가**: 현대 ML/CV 논문의 figure는 다이어그램·벡터 그래프·여러 sub-panel이 결합된 composite로 만들어져, PyMuPDF가 한 figure를 수십 개의 image object로 보고하는 경우가 많다. 예: SparseVLM(ICML 2025)의 Figure 2 한 장이 page 4에서 58개 image object로 분해되어 잡힘. 이런 경우 `get_image_bbox`로는 사람이 인식하는 "한 그림"의 경계를 잡을 수 없다.

> 정본 학습 사례 (2026-06-29): ① FastVLM 1차 — 좌표 하드코딩으로 fig_1 상단 subplot 잘림 / table_6 캡션만 / table_3 마지막 행만. ② VOILA-A — 미세 잘림(fig_1 상단·fig_2/5 좌측 라벨·fig_4 우측 절반·fig_3 좌측 본문 bleed): vector bbox가 가장자리 1~2px 못 담음 + 배경 패널 gutter 누수 + full/col 오분류. ③ **전 자산 점검**으로 더 발견 — FastVLM table_2/5 상단 잘림(thin 표 row band가 MIN_PANEL_H에 막힘), VOILA table_3 하단 본문 bleed(표↔본문 gap이 PAD보다 좁음), NAACL table_8/9/11 데이터 행 통째 잘림(borderless 표 본문이 두 rule 사이 GAP 초과). **해결**: 픽셀 여백 패스(anchor 콘텐츠 경계·흰 픽셀 여백) + wide-cluster·wide-to-wide(TABLE_GAP) bridge + CORE 기반 band(배경 패널 제외). **3개 논문(CVPR/ICLR/NAACL, Letter·A4) 48개 figure/table 전부 `--verify` clean.** **CLI·웹 공용 도구라 한쪽을 고치면 양쪽이 고쳐진다.**

#### (참고) 수동 캡션-anchor 방식 — 자동 도구가 빗나갈 때만

**대신 캡션 텍스트 좌표를 anchor로 삼는다** — 캡션은 ML/CV 학회 PDF에서 위치 컨벤션이 명확하므로 안정적 anchor가 된다:

| 자산 유형 | 캡션 위치 (관행) | crop bbox |
|---|---|---|
| Figure | 본체 **아래** | y_top = 본체 top, y_bot = caption_bottom + 4~8pt 패딩 |
| Table | 본체 **위** | y_top = caption_top − 3pt 패딩, y_bot = 표 데이터 마지막 행 + 4pt |

> 🔴 **위 "Figure=아래 / Table=위"는 관행일 뿐, 자산 유형으로 단정하지 말 것.** 논문마다 다르다 — Table 데이터가 위, 캡션이 아래인 경우도 흔하다(FastVLM CVPR2025는 표 6개 전부 이 형태). **반드시 좌표로 캡션-데이터 상대 위치를 자산별로 판별**한다: `detect_assets.py`로 캡션 `block_y`를 얻고, 같은 column band에서 캡션 위/아래 어느 쪽에 본체(이미지·드로잉·표 숫자 라인)가 있는지 확인한 뒤 crop 방향을 정한다. 유형만 믿고 관행대로 자르면 캡션+옆 본문만 담기고 본체를 통째로 놓친다.

**검출 절차 (PyMuPDF)**:

```python
import fitz, re
doc = fitz.open(PDF_PATH)
for pno in range(doc.page_count):
    page = doc[pno]
    for b in page.get_text("dict")["blocks"]:
        if "lines" not in b: continue
        for line in b["lines"]:
            txt = "".join(s["text"] for s in line["spans"])
            m = re.match(r"^\s*(Figure|Table)\s+(\d+)\.\s", txt)
            if m:
                cap_bbox = line["bbox"]  # 첫 줄의 (x0, y0, x1, y1) — PDF point 좌표
                # 다음 줄들이 같은 column에서 ≤7pt gap으로 이어지면 caption 확장
```

각 자산의 캡션 첫 줄을 `^Figure N. ` / `^Table N. ` 정규식으로 정확히 잡고, 이어지는 줄들이 같은 column band(±40pt) 안에서 ≤7pt y-gap으로 이어지면 같은 캡션으로 묶는다. 다음 `(Figure|Table) M.`이 보이거나 큰 gap이 생기면 종료.

**PDF point → pixel 변환**: 페이지 PNG가 200dpi라면 `pixel = pt × (200/72) = pt × 2.7778`. 다른 DPI 사용 시 비율 조정.

**페이지 running header 제외**: ICML/NeurIPS/CVPR 스타일 논문은 매 페이지 상단에 논문 제목 running header가 있다(보통 y=40~58pt). figure y_top은 **y ≥ 60pt** (안전하게 64pt)로 잡아 header와 separator rule을 함께 제외한다.

**Column band x 범위** (612pt wide 2-column 논문 기준):

| 폭 | x 범위 (PDF pt) | 비고 |
|---|---|---|
| full-width | 48..564 | 양 페이지 마진(54pt) 살짝 안쪽 + 캡션 보호 패딩 |
| 좌측 column | 48..302 | gutter는 ~298~306pt |
| 우측 column | 304..564 | |

**자산 본체 y_bot (캡션이 위에 있는 경우, 즉 Table)**: 표 데이터 마지막 행의 y_bottom을 PDF 텍스트 line bbox로 찾는다. `page.get_text("dict")` 결과를 y로 정렬해 표 영역 안의 마지막 숫자 라인을 찾고 +4pt 패딩.

**자산 본체 y_top (캡션이 아래에 있는 경우, 즉 Figure)**: 보통 column top(60~64pt) 또는 직전 figure 캡션의 y_bottom + 10pt 갭. 같은 페이지에 여러 figure가 stack된 경우 직전 자산의 캡션 종료선을 anchor로.

**시각 검증 (필수)**: crop 후 **각 PNG를 직접 열어 본다.** 다음 누수를 잡는다:
- 페이지 running header(논문 제목)가 상단에 보임 → y_top 4~8pt 더 내리기
- 캡션 1~2줄이 잘림 → y_bot 4~8pt 더 내리기
- 표 아래에 다음 본문 문장 한 줄이 섞임 → y_bot 5~10pt 위로 올리기
- "5. Analysis" 같은 다음 section 헤더가 보임 → y_bot 5pt 위로
- 좌측 column 자산에 우측 column 본문이 보임 → x_right를 302pt로 제한

조정은 PDF pt 단위로 한 자리 수씩 (4~8pt). 한 번에 큰 폭으로 조정하지 말 것.

**정본 구현**: `tools/autocrop_assets.py` (콘텐츠 인식 자동 bbox — 신규 빌드 1순위). 진단/디버깅 보조: `tools/detect_assets.py`(캡션 좌표·드로잉 bbox 덤프). 수동 좌표 fallback 예시: `samples/free_example/_crop.py`. 신규 vector PDF는 `autocrop_assets.py`를 먼저 돌리고, 출력 PNG를 눈으로 검증한 뒤 어긋나는 자산만 수동 보정한다. 적용 사례: `papers/1. fastvlm/_crop.py`(autocrop 호출 + 사용 자산만 선별).

**Per-paper 사용 패턴**:

```python
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).parent
PAGES = ROOT / "assets" / "pages"  # 미리 200dpi로 page_NN.png 렌더해 둠
OUT   = ROOT / "assets"
PT_TO_PX = 200 / 72

def pt_box(x0, y0, x1, y1):
    return tuple(int(round(v * PT_TO_PX)) for v in (x0, y0, x1, y1))

CROPS = [
    # (filename, page_1based, PDF-point bbox)
    ("fig_1.png",   2, pt_box(48, 64, 564, 292)),  # figure, caption y=265..285
    ("table_1.png", 6, pt_box(48, 64, 564, 528)),  # table, caption y=71..91 위
    # ...
]
for fn, pno, box in CROPS:
    Image.open(PAGES / f"page_{pno:02d}.png").crop(box).save(OUT / fn)
```

**`get_image_bbox` 사용이 여전히 OK인 경우**: 자산이 단일 image object로 명확히 분리되는 경우 (스크린샷·사진·photoreal figure 한 장 = 한 image). 캡션 좌표 기반이 항상 더 안전하므로, 의심스러우면 캡션 좌표 우선.

#### 🔴 좌표를 손으로 추측하지 말 것 — 먼저 검출 도구를 돌린다 (정책)

`_crop.py`의 rect를 눈대중·하드코딩으로 적으면 거의 항상 빗나간다. **먼저 `tools/detect_assets.py`를 돌려** 각 캡션의 실제 PDF point 좌표와 이미지/드로잉 bbox를 뽑고, 그 숫자를 anchor로 rect를 계산한다.

```
python tools/detect_assets.py "rawpaper/<논문>.pdf" --pages 4,5,8
# → CAP Figure block_y=[438.8, 470.7] x=[306,504] lines=3  | Figure 2: ...
#   images(n=...): [(310,279,500,429), ...]
```

- **멀티라인 캡션 주의**: 캡션 정규식이 매치하는 건 **첫 줄**뿐이다. Figure의 y_bot은 첫 줄 y1이 아니라 **캡션 블록 전체의 끝(`block_y[1]`) + 4~8pt**여야 한다. detect_assets는 같은 블록에서 줄간격 ≤7pt로 이어지는 줄을 묶어 `block_y`로 보고하므로 그 값을 쓴다.
- **이미지 top anchor**: Figure y_top은 `images()`가 보고한 본체 이미지의 y0(헤더 제외 ≥60pt)에서 4~8pt 위. column top 64pt를 무턱대고 쓰면 페이지 중간 figure의 상단이 잘린다.
- **column band**: 캡션 x중심·이미지 x로 full/left/right 판별. 좌/우 단 figure를 full-width로 자르면 옆 단 본문이 섞인다(단, 본문폭을 꽉 채우는 표는 full-width가 정상).

> 정본 학습 사례 (실패→복구): 한 웹앱 빌드에서 위 도구 없이 좌표를 하드코딩한 결과, **figure 상단이 잘리고**(본체 이미지 y0보다 crop y_top을 아래로 잡음), **table 하단에 본문 한 줄이 섞였다**(멀티라인 캡션 끝을 첫 줄로 오인). `detect_assets.py`로 캡션 `block_y`·이미지 bbox를 뽑아 재크롭한 뒤 전 자산 본체+캡션 깨끗. 교훈: 좌표는 추측하지 말고 검출 도구로 anchor.

### OCR'd 스캔본 — 3-pass 알고리즘
정본 도구: `tools/crop_assets.py` (이 배포본에는 OCR 스캔 예제 논문은 미포함, 도구만 제공).

**Pass 1 — figure y-범위 (OCR word density)**
캡션 bbox에서 위(figure ABOVE caption) 또는 아래(table BELOW caption)로 row 단위 스캔.
한 row가 **body 단락**이려면:
- row 내 word 가로 커버리지 ≥ 80% 본문폭
- row 내 word 사이 최대 간격 ≤ 60pt

3행 연속 body 단락이 잡히면 거기를 figure 경계로 확정. 단발성 dense row(표 컬럼 헤더, 그래프 축 레이블)는 무시.

**Pass 2 — figure x-범위 (visual gutter)**
figure y-band를 grayscale 1×로 렌더 → 각 column의 흰 픽셀 비율 계산 (≥ 93% white = empty).
- **내부** gutter (양 끝이 본문 margin과 닿지 않음) 우선, 폭 ≥ 10pt이면 채택
- 내부 gutter 없으면 폭 ≥ 20pt margin gutter만 fallback
- gutter 양쪽 OCR word 수가 3배 이상 차이나면 적은 쪽이 figure side, 그 쪽으로 narrow
- 축 레이블 보존을 위해 figure side로 14pt 패딩

본문이 그림 옆을 wrap하는 inline figure를 좁은 x-범위로 잘 잡는다.

**Pass 3 — axis-line snap (body-text-above 그래프)**
y-범위 안에서 가로 axis line을 검출 (위가 흰색이고 한 row에서 dark 비율 ≥ 45%). 검출된 axis 위에 OCR 단어 ≥ 20개일 때만 snap (잘못된 대규모 점프 방지). fig_top을 axis line 바로 위까지 끌어내려 그래프 위에 끼인 본문/수식 블록 제거.

**캡션 보호:** 모든 pass 후 마지막에 `x_min = min(x_min, cap_x0 - 4)`, `x_max = max(x_max, cap_x1 + 4)`로 캡션 bbox는 항상 풀 가로폭 포함.

### 한계
- wrap-around 본문이 figure 위/아래로 강하게 흐르는 페이지(perceptron fig_7, fig_11 류)는 자동만으로 100% 깔끔하지 못함 → 스펙에 manual y-bbox 오버라이드 추가 가능 (또는 codex/ImageGen으로 학습용 다이어그램 대체).

### Per-paper 사용
`papers/[name]/_recrop.py` 한 장에:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.crop_assets import crop_figures

PDF_PATH = Path(".../rawpaper/<file>.pdf")
OUT_ASSETS = Path(__file__).parent / "assets"
SPECS = [
    # (asset_id, page_1based, caption_regex, orientation)
    ("fig_1",   4, r"FIG\.?\s*1\.\s*Organization", "above"),
    ("table_1", 6, r"TABLE\s*1\b",                 "below"),
    # ...
]

if __name__ == "__main__":
    crop_figures(PDF_PATH, OUT_ASSETS, SPECS)
```

PNG 갱신 후 base64 재임베드는 `papers/[name]/_reembed.py` 패턴 (perceptron 참조). 두 스크립트 모두 일회성 헬퍼로, 재실행만 보장하면 된다.

---

## 5. Math Handling

- 수식은 LaTeX 형태 유지 (`$...$` 인라인, `$$...$$` display)
- `apply_math_latex.py`가 평문 수식을 LaTeX/MathJax 인식 형태로 패치 (idempotent)
- 자세한 수식 규칙: `rules/math_rules.md`

---

## 6. Column Handling

- 다단(2-column) PDF는 좌 → 우, 상 → 하 순서로 복원
- Figure/Table이 컬럼 사이에 섞이지 않도록 분리
- PyMuPDF `page.get_text("blocks")`의 좌표를 이용한 정렬 권장

---

## 7. Noise Removal

**제거:** 페이지 번호, header, footer, 이중 공백
**보존:** 본문 텍스트, 수식, figure caption, 인용·각주 마커

---

## ❗ 금지 사항

- 의미 변경 금지
- 요약 금지
- 문장 재작성 금지
- 문단 재구성 금지
- ID 체계 임의 변경 금지

---

## ✅ 핵심 원칙

이 단계의 목표는 "읽기 좋게 만드는 것"이 아니라

👉 **이후 모든 단계(번역, 분석, 코칭, 지식, 도표 해석)가
정확하게 매핑될 수 있도록 ID 골격을 만드는 것**이다.

ID 골격이 망가지면 v2 빌더는 콜아웃·해석·번역을 잘못된 자리에 렌더한다.
