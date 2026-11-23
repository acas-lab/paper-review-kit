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

## `video/` (Stage 13 소개 영상 뼈대)

`기획안.md`(원고 = 컷 표) · `spec.py`(자막 표기·TTS 읽기·인용 위치·장면 이미지) · `scenes.js`(캔버스 장면) · `clipspec.py`(motion 클립 명세) · `CREDITS.md`. 손으로 복사하지 않는다 — `python tools/video/make_video.py "papers/N. shortname" new`가 `papers/N. shortname/video/`로 복사하며 `{{PAPER}}`·`{{SHORT}}`·`{{TITLE}}`·`{{VENUE}}`를 채우고, `assets/sources.json`을 만든다. 그 뒤 `TODO_PAPER`를 모두 채운다(남아 있으면 `check_video.py` G0와 `check_paper_structure.py`가 FAIL). 규칙: `rules/video_rules.md`.

## 함께 쓰는 기준

- 디자인: `samples/cares/CARES_output.html`, `tools/restyle_dash_v4.py`, `rules/design_v4_dashboard.md`
- 인터랙션·데이터 예제: `samples/cares/`
- 구조 검사: `tools/check_paper_structure.py`
