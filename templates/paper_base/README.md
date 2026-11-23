# 기준 빌더 (templates/paper_base)

신규 논문은 이 폴더의 `_build.py`를 논문 폴더로 복사해 시작한다. 특정 논문에 묶이지 않는 고정 기준이다. 실제 데이터로 채운 워크드 예제는 `samples/cares/`(`_build.py` + 데이터 + 산출물)이고, 이 빌더는 그 빌더에서 논문별 문구를 `TODO_PAPER` 표시로 비워 둔 판이다.

## 쓰는 법

1. `_build.py`를 `papers/N. shortname/`으로 복사한다. 이 폴더의 파일은 직접 빌드하지 않는다.
2. `TODO_PAPER`로 표시된 곳을 모두 채운다. 그 밖의 코드는 고치지 않는다.
3. `python "papers/N. shortname/_build.py"` → `python tools/restyle_dash_v4.py "papers/N. shortname"` → 주입·검사 체인(`workflow.md` Stage 10).
4. 논문 하나에서만 필요한 렌더링 규칙이 생기면 그 논문의 복사본만 고친다.
5. 모든 논문에 해당하는 결함이면 이 폴더의 파일을 고친다. 다음 논문부터 적용된다. 기존 논문은 재빌드로 덮어쓰면 산출물에만 있는 수정이 사라질 수 있으므로, 재빌드 결과와 현재 산출물을 비교한 뒤 고친다.

`TODO_PAPER`가 남아 있으면 `tools/check_paper_structure.py`가 FAIL을 낸다. `tabs_data/study.json`(Stage 11, ①′ Paper Study)도 필수다 — 빌더는 study.json이 없으면 ①′를 자동 셸로 그리지만 그것은 개발 중 "작성 전" 임시 상태일 뿐 산출물이 아니며, 같은 검사가 FAIL로 잡는다.

## `_mk_corpus.py` (선택)

본문 구조화(Stage 2)의 정본은 `tools/structure_paper.py`다(결정적 · web↔CLI 동일). `_mk_corpus.py`는 (영문, 번역) 쌍을 한 파일에 적어 `structured.json` + `translations/manual.json` + `labels.json`(run-in 소제목)을 함께 쓰는 선택 도구다. `structure_paper.py` 산출을 그대로 옮긴 뒤 run-in 소제목·display 수식·번역을 한 파일에서 다룰 때만 복사한다. 복사했다면 그 파일의 `TODO_PAPER`도 모두 채운다. 문장을 합치거나 빼지 않는다(`CLAUDE.md` § Stage 2 완전성).

## 채울 곳 (`_build.py`)

| 자리 | 내용 |
|---|---|
| 파일 머리 주석 | 논문 이름, 학회·저널, 소속 |
| `FN_HEAD` | 각주 문단이 있을 때만 |
| 판정 카드 `저자의 주장 (...)` | 저자 주장을 가져온 절 |
| overview `alt`, figcaption | 짧은 이름, 그림에 담은 수치와 주의점 |
| ② ③ ④ `tab-intro` | 탭별 소개 문장 |
| 수식 패널 제목과 부제, 개념 패널 부제 | 수식 수, 수식의 연결 순서, 개념 요약 |
| footer | 제목, 학회·저널, 소속, 한 문장 |

## summary 카드 `overview` (codex PNG가 없을 때)

`assets/generated/dissection_overview.png`(모드 A)나 `.svg`(모드 B)가 없으면, 빌더(`_overview_svg`)가 `tabs_data/dissection.json`의 summary 카드(`"cls": "diss-summary"`)에 있는 `overview`로 5단 SVG를 그린다. `samples/cares/`는 PNG를 쓰므로 이 필드가 없다. 최소 예:

```json
{
  "id": 8,
  "cls": "diss-summary",
  "title": "논문 총정리 - 한 장 요약",
  "lead": "이 카드 하나로 논문 전체를 정리한다",
  "rows": [
    {"tag": "한 줄 요약", "body": "..."},
    {"tag": "이게 왜 문제인가 (Problem)", "body": "..."}
  ],
  "overview": [
    ["PROBLEM",     "고해상도 입력은 시각 토큰 수를 4배로 늘려 prefill 연산이 커진다"],
    ["OBSERVATION", "질의의 62%는 336px 입력으로도 같은 답을 낸다"],
    ["METHOD",      "350M 예측기가 질의마다 최소 해상도를 고른다"],
    ["NOVELTY",     "대상 모델을 바꾸지 않는 plug-in 방식"],
    ["RESULTS",     "정확도 유지, prefill 연산 최대 78% 감소"]
  ]
}
```

- 항목은 `[label, text]` 쌍 또는 `{"label": "...", "text": "..."}` 객체, 보통 5개(PROBLEM → OBSERVATION → METHOD → NOVELTY → RESULTS). 위 문장·수치는 형식 예시일 뿐이며 논문의 실제 수치로 쓴다.
- `text`는 단마다 한두 문장(약 120자 이하 — SVG는 한 줄 20자, 6줄까지 그리고 나머지는 잘린다). 태그는 벗겨서 그린다.
- `rows`는 9행(태그는 `prompts/04_research_analysis.md` 표 그대로)을 모두 채운다. 위 예에서는 2행만 보였다.
- PNG나 SVG 파일이 있으면 그것이 우선한다. 정본 설명: `prompts/04_research_analysis.md` "8번 카드".

## `video/` (Stage 13 소개 영상 뼈대)

`기획안.md`(원고 = 컷 표) · `spec.py`(자막 표기·TTS 읽기·인용 위치·장면 이미지) · `scenes.js`(캔버스 장면) · `clipspec.py`(motion 클립 명세) · `CREDITS.md`. 손으로 복사하지 않는다 — `python tools/video/make_video.py "papers/N. shortname" new`가 `papers/N. shortname/video/`로 복사하며 `{{PAPER}}`·`{{SHORT}}`·`{{TITLE}}`·`{{VENUE}}`를 채우고, `assets/sources.json`을 만든다. 그 뒤 `TODO_PAPER`를 모두 채운다(남아 있으면 `check_video.py` G0와 `check_paper_structure.py`가 FAIL). 규칙: `rules/video_rules.md`.

## 함께 쓰는 기준

- 디자인: `samples/cares/CARES_output.html`, `tools/restyle_dash_v4.py`, `rules/design_v4_dashboard.md`
- 인터랙션·데이터 예제: `samples/cares/`
- 구조 검사: `tools/check_paper_structure.py`
