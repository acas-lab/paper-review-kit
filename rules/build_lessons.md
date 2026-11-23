# 빌드 교훈

> 앞부분 "빌드 전 점검"은 신규 논문을 빌드하기 전에 읽는다. 뒷부분 "정본 학습 사례"는 `CLAUDE.md`에 쌓여 있던 실패→복구 기록과 측정값을 옮긴 것으로, 비슷한 상황을 만났을 때 찾아본다.
> 새 교훈은 "정본 학습 사례" 맨 위에 쓰고, 모든 논문에 적용될 때만 "빌드 전 점검"에 한 줄을 올린다.
> 문서 안의 "papers N"·논문 이름은 모체 작업 폴더의 사례다(모체 사례 — 배포본 미포함). 배포본에서 직접 열어 볼 수 있는 예제는 `samples/cares` 하나다.

## 빌드 전 점검

### 시작할 때

- `_build.py`는 `templates/paper_base/`에서 복사하고 `TODO_PAPER` 표시만 채운다(`_mk_corpus.py`는 선택). 직전 논문의 빌더를 복사해 몇 곳을 고치는 방식은 이 기준을 만들기 전의 방식이다 — 그 방식에서는 한 논문에서 고친 결함이 다음 논문에 이어지지 않았다.
- 산출물만 고치지 않는다. 빌더가 있는 논문은 빌더까지 고쳐야 재빌드와 다음 논문에서 결함이 되살아나지 않는다. 모든 논문에 해당하는 결함은 `templates/paper_base/`를 고친다.
- 다른 세션의 중간 산출물을 이어받으면 그대로 믿지 않는다. 아래 "이어받은 산출물 결함"을 확인한다.
- 본문 구조화는 `tools/structure_paper.py`, 자산 크롭은 `tools/autocrop_assets.py`(+ `--verify`)로 한다. 손으로 본문 일부만 담거나 좌표를 하드코딩하지 않는다.
- 부록을 뺄지는 "거기 있는 사실을 내가 인용하는가"로 정한다. 인용하면 Stage 2에 포함한다. "논문이 밝히지 않는다"고 쓰기 전에 PDF 끝까지 확인한다. 부록이 PDF에 없어 검증할 수 없으면 그 사실을 분석에 명시한다.
- 구세대 논문의 `structured.json`은 완전하다고 가정하지 않는다. PDF 산문 블록과 역대조한다.
- 구세대 논문을 재빌드하기 전에 현재 산출물과 비교한다. 산출물에만 들어간 교정(`html_patch.py`·`overview_inject.py` 등)이 되돌아갈 수 있다.
- 메모로 Q&A를 생성한 논문을 재빌드하면 ⑥ 탭의 해당 카드가 사라질 수 있다. 재빌드 전에 ⑥ 탭을 비교한다.
- HTML이 끝나면 소개 영상(Stage 13)을 만든다(사용자가 빼라고 하지 않으면). `make_video.py <논문> new`로 시작하고 `rules/video_rules.md`를 따른다. 영상 도구의 공통 결함은 논문 `video/`가 아니라 `tools/video/`(클립 엔진은 `skills/motion-broll/` 후 `- setup`으로 재설치)에서 고친다.

### 자산 크롭

- 캡션 위치는 학회·저널 이름으로 추정하지 않는다. 같은 학회, 같은 논문 안에서도 다르다(Figure 아래·Table 위가 흔하지만 둘 다 아래인 논문, 표마다 다른 논문이 있다). 자산마다 블록 좌표를 확인한다.
- 나란히 놓인 자산은 컬럼 밴드를 나눠 자른다. 캡션·데이터·본문이 한 블록으로 묶이면 줄 단위 좌표로 자른다.
- MuPDF가 이미지를 검게 뭉개면 raster/vector 2층으로 재합성한다(이미지별 `fitz.Pixmap` + 이미지 제거 사본의 벡터 렌더 합성).
- 표 번호가 건너뛰면 의도적 제외가 아니라 크롭 누락이나 부록 통째 제외일 수 있으니 확인한다.
- 자산 id는 `fig_N`, `table_N`, `box_N`만 쓴다. 다른 접두사는 `reader_asset_chip`이 못 알아본다.
- `--verify`는 여백(잘림)만 본다. 캡션이 위아래 그래픽 사이에 끼면 이웃 그림을 잘라 올 수 있다(FastVLM Fig.5가 Fig.6 그래프를 가져가던 사례 - 도구 수정됨). 크롭 출력에 `WARN … overlap`이 나오면 두 PNG를 반드시 열어 본다.

### 자산 순서

- 빌드 후 asset_layout을 문단 순서로 정렬해 번호가 단조 증가하는지 스크립트로 확인한다(`check_paper_structure.py`가 함께 잡는다).
- 번호 순과 서술 순이 충돌하면 본문 표는 번호 순을 지키고, 이유를 `config.json#meta.asset_order_note`에 남긴다. 부록은 인용 문단 순을 허용한다.
- 한 문단이 표 여러 개를 설명하면 `asset_layout`에 같은 paragraph_id를 여러 번 넣는다.

### 데이터 스키마

- `knowledge.json`은 현재 스키마를 쓴다: `primer{title, caption, image_path, image_caption, fund_cards[{label, title, body}]}`, `equations[{eq_id, label, tex, where, intuition, refs}]`, `concept_cards[{label, title, body}]`. 구세대 키(`what/why/links`, `definition/intuition/structure/paper_role`)는 기준 빌더가 값을 이어 붙여 본문으로 렌더한다(소제목 구분이 사라지므로 쓰지 않는다).
- `questions.json`은 `samples/cares/tabs_data/questions.json` 스키마를 쓴다: `diagrams[{image_path, title, caption}]` + `cards[{cls, title, lead, rows[{q, a}]}]`, `cls` = `coach-assume`·`coach-design`·`coach-critique`·`coach-extend`(`rules/coaching_rules.md`).
- 문단 소제목 키는 `section_subtitle`이다. `subtitle`이면 소제목이 사라진다.
- `callouts`, `hotspots`는 키가 있어도 비어 있을 수 있다. `len()`으로 확인한다.
- `config.json#meta.code`는 그대로 topbar 링크 `href`가 된다. URL이 없으면 "공개 예정" 같은 서술 대신 키를 뺀다.
- `study.json`의 `phase2.method.claude_html`, `phase2.conclusion.claude_html`은 필수다(빠지면 빌더가 KeyError).
- 문단 첫머리 run-in 제목은 데이터를 쪼개지 말고 `_build.py#LABEL_PARAS`나 `labels.json`(`_mk_corpus.py`의 `RUNIN`)으로 소제목에 올린다.

### 이스케이프

- 평문 필드에 `<b>`를 쓰면 화면에 글자로 나온다. 평문 필드에 `&lt;image&gt;`를 쓰면 `&amp;lt;`로 이중 이스케이프된다. 평문에는 `<image>`를 리터럴로 쓴다.
- HTML 필드의 `<NUM1>`류 원문 기호는 `&lt;NUM1&gt;`로 쓴다. tex의 부등호는 `\lt`를 쓴다(`rules/math_rules.md`).
- 빌더 계보를 확인한다. CARES 계보(`samples/cares/_build.py`·`templates/paper_base/_build.py`)는 `original`만 `esc()`하고 translation은 raw로 넣는다 — 번역문이 HTML 필드다. 양쪽을 다 이스케이프하는 계보(모체 일부 빌더)에서는 번역문에 태그를 쓰면 글자로 보이므로 꺾쇠 없이 태그명만 쓴다.
- 검사 도구가 필드 구분을 못 잡으므로 산출물 `grep '&lt;b&gt;'`, `grep '&amp;lt;'`이 최종 방어선이다(`check_paper_structure.py`도 같은 문자열을 잡는다).

### 내용

- 본표 수치가 어느 하이퍼파라미터·설정에서 왔는지 표끼리 대조한다.
- 확장판 논문은 표의 첨자(baseline 대비) 대신 선행판 행과 최종 행을 직접 뺀다.
- 페이지에 싣는 코드는 실제로 실행해 확인한다.
- 다른 논문을 번호로 끌어오지 않는다. 각 논문은 그 논문의 표와 수치로 완결한다. 예외는 그 논문이 직접 인용하는 연구명과 사용자가 명시한 후속 연구 안내다.

### 생성 이미지

- 생성 이미지의 사실 오류는 대개 프롬프트에서 나온다. 수치·셀 값은 "그대로 쓸 것, 지어내지 말 것"과 함께 행별로 나열한다.
- 대문자 강조 단어는 철자가 흐트러지니 소문자 + 이탤릭을 쓴다.
- 철자·정확성 요구는 프롬프트 본문이 아니라 codex 호출문에 넣는다. 스타일 블록에 항목을 더하면 레이아웃이 무너질 수 있다. 본문에는 "빈 공간·장식 아이콘 금지, 라벨 잘림 금지"를 쓴다.
- 재생성은 흠을 옮길 수 있다. 재생성 전에 현재 PNG를 scratchpad에 복사해 최선본을 백업하고, 사소한 철자 깨짐은 figcaption에 명시한다.
- 스케일이 다른 계열은 패널과 축을 나눈다. 산점도는 점 위치를 믿지 않는다. "데이터 없음"은 "선 없이 빈 상자 + 라벨"로 지시한다.
- codex 결과는 파일 존재가 아니라 프로세스 종료(백그라운드 태스크 완료 알림) 후 수거하고 md5로 대조한다 — codex는 파일을 쓴 뒤에도 해상도를 맞춰 다시 저장할 수 있다.
- 병렬 호출은 `--cd`로 작업 디렉토리를 격리한다(`rules/component_rules.md` §11.8.5).

### 도구 사용

- 주입기를 여러 논문에 동시에 돌리면 `OSError 22`가 간헐적으로 날 수 있다. 재시도하고, 헤더 주석 개수로 중복 주입이 없는지 확인한다.
- `check_memo_layer.py`는 playwright가 기대하는 chromium 빌드가 없으면 `executable_path`를 덮어쓰는 래퍼로 실행한다.
- `CLAUDE.md`와 큰 문서는 스크립트로 덮어쓰지 않는다. Edit 툴을 쓴다(모체에서 Python `write_text`가 surrogate 이스케이프로 UnicodeEncodeError를 내며 파일을 0바이트로 자른 적이 있다). 이모지는 리터럴이나 `\U0001F534` 형식으로 쓴다.
- `restyle_dash_v4.py`는 `<section class="eq-panel">`만 Mathematics 탭으로 옮긴다. 패널 마크업을 바꾸지 않는다(수식 카드가 있는데 패널을 못 찾으면 FAIL로 멈춘다).

### 이어받은 산출물 결함

1. `knowledge.json` 구세대 스키마
2. `subtitle`과 `section_subtitle` 혼동
3. 비어 있는 `callouts`, `hotspots`
4. 평문 필드의 엔티티 이중 이스케이프
5. 본문 누락: 캡션과 1pt 미만 간격이면 한 블록으로 묶여 캡션 필터가 문단을 삼킨다. 글로 된 figure가 본문에 섞인다. 숫자 비율 필터가 목록 항목을 버린다.
6. 표 번호 점프
7. 잘못된 자산 id 접두사
8. 코퍼스 내 교차 참조
9. run-in 제목이 문장에 붙어 있음

---

## 정본 학습 사례 (모체 사례 — 배포본 미포함)

### 한 컬럼에 쌓인 figure 크롭 (2026-11)

> 모체 사례 — 배포본 미포함: `papers/25. visiondrop`(Rethinking Visual Token Reduction, p3). 상단 full-width Fig.2 아래 왼쪽 단에 Fig.3·Fig.4가 세로로 쌓인 배치에서 `autocrop_assets.py`가 Fig.2 자리에 Fig.3 이미지를, Fig.3 자리에 Fig.4 상단을 잘라 왔다(`WARN fig_3 / fig_4 overlap 57%`). 원인은 각 sub-figure 뒤에 깔린 **보이지 않는 흰 배경 rect**(y=193..333, 354..498, 컬럼 밖까지 번짐)가 Fig.3·Fig.4 캡션을 가로질러 "캡션 사이 그래픽은 아래 캡션의 것" 소유권 사슬을 끊은 것. 흰색만 칠하고 캡션과 겹치는 path를 제외하자 Fig.2~4가 모체의 수동 좌표(`_crop.py`)와 일치했고, 같은 원인으로 오른쪽 단 Fig.1이 왼쪽 단 본문까지, 왼쪽 단 Fig.6이 페이지 전폭으로 잘리던 것도 함께 고쳐졌다. 모체는 이 논문을 처음부터 수동 pt 좌표로 잘랐다 — 도구로 일반화가 안 될 때의 fallback 절차는 `rules/parsing_rules.md` §4-A.

### 무리한 한국어 변환 금지

(정책 본문: `rules/project_policies.md` § 무리한 한국어 변환 금지)

> 정본 학습 사례 (실패→복구): `papers/24. geollava8k`(모체 사례 — 배포본 미포함) 1차 빌드에서 위 안티패턴 다수 사용. 사용자 지적 후 manual.json·analysis.json·dissection.json·knowledge.json·config.json·HTML 18곳 일괄 정리. 동일 실수 재발 방지가 이 정책의 직접 동기.

### 메모 상시 접근 레이어

(정책 본문: `rules/project_policies.md` § 메모 상시 접근 레이어)

- 측정값(papers 30 · 모체 사례 — 배포본 미포함 · 자산 뷰어 + 가이드 + 메모 동시): 1600px 나란히·뷰어 780 / 1440~1080px 겹침·뷰어 1000~640 / 900px 이하 `mlx-float`·뷰어 전폭. **v4 는 1080px 에서 뷰어 260px 이었다.**

- 측정값(papers 30 · 셋 다 열림): 1600px 이미지 647 → **681**(가이드 열면 오히려 커진다) / 1080px 겹침 0 · 패널 291 / 950px 겹침 0 · 패널 260.

> 🔴 **정본 학습 사례 (회귀의 원인, 모체 사례 — 배포본 미포함)**: 2026-07-09 의 z-index 1650 수정은 **빌드된 HTML 에만** 적용되고 `_build.py` 템플릿에는 반영되지 않았다. 그 결과 CARES(26) 의 `_build.py` 를 복사해 만든 **papers 27~35 전부가 205/300 으로 회귀**했다(2026-09-02 발견). 교훈: **산출물만 고치고 빌더를 안 고치면 다음 논문에서 그대로 되살아난다.** 이번에 papers 26~35 의 `_build.py` 10개와 `tools/memo_inject.py` 를 함께 고쳐 원천을 막았다.

### Stage 2 완전성

(정책 본문: `rules/project_policies.md` § Stage 2 완전성)

> 정본 학습 사례 (실패→복구): `papers/20. sparse_vlm`(모체 사례 — 배포본 미포함)은 1차 빌드에서 본문 70문장으로 압축됐다가 사용자 지적 후 163문장으로 재작성된 케이스. Related Work 전체·3.4 Theoretical Analysis가 누락됐었다. 동일 실수 재발 방지가 이 정책의 직접 동기.

### Study Modal

(정책 본문: `rules/project_policies.md` § Study Modal)

> 안티패턴 (정본이 아닌 잘못된 관성, 모체 사례 — 배포본 미포함): papers 4~19의 일부 빌드에서 모달이 "캡션 + 전문가 해석 + 초보자 해설" 3-block으로 채워져 figure 하단 내용과 거의 동일했던 경우. 신규 빌드는 4-섹션 정형으로 깊이 분해.

### Vector PDF 자산 크롭

(정책 본문: `rules/project_policies.md` § Vector PDF 자산 크롭)

> 정본 학습 사례 (실패→복구, 모체 사례 — 배포본 미포함): FastVLM(CVPR 2025) 1차 빌드에서 좌표를 손으로 잡아 **fig_1 위쪽 subplot 잘림 / table_6 캡션만 / table_3 마지막 행만** 잡혔다(적층 패널 gap·zero-thickness rule 탈락·full-width 누수). `autocrop_assets.py`로 12개 figure/table 전부 본체+캡션 완전 캡처. (그 이전 SparseVLM 사례: 페이지 픽셀 좌표 하드코딩 → Figure/Table 다수 잘림·본문 섞임 → 캡션 anchor 재크롭으로 복구.)

### 자산 등장 순서

(정책 본문: `rules/project_policies.md` § 자산 등장 순서)

> 정본 학습 사례 (실패→복구): SparseVLM(모체 사례 — 배포본 미포함) 초기 빌드는 fig_7(Appendix A redundancy diagram)이 "개념적으로 p8 rank-기반 redundancy에 어울린다"는 이유로 p8에 붙어 등장 순서가 `1→2→3→7→4→5→6`이 됐다. 사용자 지적 후 fig_7을 p12_vis(5.4 Qualitative 끝)로 이동해 `1→2→3→4→5→6→7` 자연 순서 회복.

### Dissection 카드 레이아웃

(정책 본문: `rules/project_policies.md` § Dissection 카드 레이아웃)

> 안티패턴 (이전 정본의 잘못된 관성, 모체 사례 — 배포본 미포함): papers 4~21까지의 빌드는 2-column grid + tag-body 옆 배치였다. 카드 텍스트가 길어질수록 좌우로 흐름이 끊겨 \"한 카드를 한 호흡에 읽기\"가 깨졌다. 사용자 지적 후 모체 papers 22(free)에서 수직 적층으로 재작성.

### prompt.txt 본문 작성 = 이미지 품질의 단일 변수 (정책, 2026-08-01)

(정책 본문: `rules/project_policies.md` § prompt.txt 본문 작성 = 이미지 품질의 단일 변수 (정책, 2026-08-01))

> 정본 학습 사례 (실패→복구): `papers/27. lupi`(모체 사례 — 배포본 미포함) 1차 생성 시 §11.3의 얇은 스켈레톤을 그대로 따라 단마다 요소를 1~2개만 적어 헐거운 그림이 나왔고, 병렬 호출이 작업 디렉토리를 공유해 다른 프롬프트의 그림이 저장되는 사고도 함께 발생. §11.8 신설·§11.3 스켈레톤 교체·Stage 4 템플릿 교체가 그 직접 결과물이다 (2026-08-01).
