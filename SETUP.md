# SETUP — 설치 + 첫 논문 따라하기

이 문서대로 따라 하면, 자기 컴퓨터에서 논문 PDF 한 편을 v4 대시보드 8탭 학습 HTML로 만들 수 있습니다.
**빌드 자동화는 없습니다.** Claude Code와 *대화하면서* 한 단계씩 만듭니다.
이 킷은 특정 분야(AI/ML)에 묶이지 않습니다 — 자연과학·공학·AI/CS·의학·인문사회 어느 분야의 논문이든 같은 절차로 만듭니다.

---

## 0. 가장 쉬운 방법 — `setup/` 폴더의 bat 파일을 0→1→2→3→4 순서로 더블클릭 (Windows)

터미널 명령을 쳐 본 적이 없다면 이 방법을 쓰세요. `setup/` 폴더의 파일을 **번호 순서대로, 한 번에 하나씩** 더블클릭하면 아래 1절의 설치가 모두 끝납니다. 각 창은 끝날 때 `[OK]` / `[FAIL]` 한 줄과 "다음에 누를 파일"을 알려 주고, 이미 설치된 것은 건너뜁니다. 한 단계가 끝나면 **창을 닫고** 다음 번호를 누르세요. 그림이 있는 자세한 안내는 `GUIDE.html`, 파일별 설명은 `setup/README.md`.

| 파일 | 하는 일 | 언제 |
|---|---|---|
| `setup/0_check.bat` | 설치 없이 python / node / npm / claude / codex / git / winget 유무·버전 점검 + 남은 단계 번호 표시 | 처음 + 막힐 때 |
| `setup/1_install_python.bat` | Python 3.12 설치 (winget, PATH 자동) — 3.10+ 있으면 건너뜀 | 처음 한 번 |
| `setup/2_install_node_and_claude.bat` | Node.js LTS 설치 → `npm install -g @anthropic-ai/claude-code` (Node 를 방금 깔았으면 창 닫고 한 번 더) | 처음 한 번 |
| `setup/3_login_claude.bat` | `claude` 실행 → 브라우저에서 구독 계정 로그인 → `/exit` | 처음 한 번 |
| `setup/4_install_kit_packages.bat` | CLI 도구용 `pymupdf` · `playwright` + Chromium (웹 모드는 자기 venv 를 따로 만듦) | 처음 한 번 |
| `setup/5_start_web.bat` | 웹 대시보드 매일 실행기 (= `webapp/win_start.bat`) | 매일 |
| `setup/6_start_cli.bat` | CLI 매일 실행기 (킷 루트에서 `claude`) | 매일 |
| `setup/7_install_codex_optional.bat` | (선택) `npm install -g @openai/codex` — 이미지 모드 A 전용, 없으면 SVG 모드 B 로 대체 | 필요할 때만 |
| `setup/8_install_video.bat` | 소개 영상(Stage 13) 도구 — `skills/motion-broll` → `.claude/skills/motion-broll` 복사(스킬 설치) · ffmpeg · node 패키지 · Chromium · (선택) TTS 환경 수 GB · `doctor` 결과 출력. 건너뛰어도 첫 영상 때 자동 설치 | 영상을 만들기 전 한 번 |

mac / Linux 는 `setup/README.md` 끝의 명령 목록을 터미널에서 순서대로 실행하세요. 아래 1절은 같은 내용을 손으로 할 때의 설명입니다.

---

## 1. 필요한 것 설치

### (필수) Claude Code
이 키트의 "엔진"입니다. Claude 계정/구독(또는 API 키)이 필요합니다.

- 설치·로그인 방법: 공식 문서 https://docs.claude.com/claude-code 참고
- 설치 확인: 터미널에서 `claude --version`

### (필수) Python 3
PDF에서 텍스트와 그림/표를 뽑고, 최종 HTML을 조립할 때 씁니다.

```bash
python --version        # 3.10+ 권장
```

> **PyMuPDF는 따로 설치하지 않아도 됩니다.** `tools/`의 도구들이 첫 실행 때 없으면
> 스스로 `pip install` 합니다(웹앱은 런처 `win_start.bat`/`linux_start.sh`가 venv에 자동 설치). 즉 **Python 본체만**
> 있으면 됩니다. (수동으로 미리 깔고 싶다면 `pip install pymupdf` — import 이름은 `fitz`.)

### (영상용) 소개 영상 도구 — 자동 설치
기본 빌드는 HTML 뒤에 10~15분 소개 영상(Stage 13)도 만듭니다. 필요한 것(motion-broll 스킬 · ffmpeg · Node 패키지 · Chromium · Python 3.12 TTS 환경과 모델 수 GB)은 `tools/video/make_video.py`가 처음 실행 때 스스로 설치합니다. NVIDIA GPU가 있으면 음성 합성이 빠르고, 없으면 CPU로 느리게 돕니다. 미리 점검·설치하려면:

```bash
python tools/video/make_video.py - doctor     # 빠진 것 표시 + motion-broll 스킬(.claude/skills/motion-broll) 설치
python tools/video/make_video.py - setup      # 스킬 · 파이썬 패키지 · ffmpeg · node_modules · Chromium
python tools/video/make_video.py - setup-tts  # TTS 환경 (수 GB)
```
영상이 필요 없으면 빌드를 요청할 때 "영상은 빼줘"라고 하면 됩니다. 규칙: `rules/video_rules.md`.

### (선택) codex CLI
②~⑥ 탭의 학습 보조 일러스트를 생성할 때만 필요합니다. 없으면 그 단계만 건너뛰면 됩니다.
설치 방법은 codex CLI 공식 안내를 따르세요.

---

## 2. 키트 받기

```bash
git clone https://github.com/acas-lab/paper-review-kit.git
cd paper-review-kit
```

또는 GitHub의 **"Use this template"** / **"Download ZIP"** 으로 받아도 됩니다.

> 자기 작업은 이 폴더를 복사해 쓰거나, 자기 GitHub 저장소로 따로 관리하길 권합니다.

---

## 3. 먼저 견본을 열어 본다 (목표 이미지 잡기)

브라우저로 아래 파일을 열어 "완성형"이 어떤 모습인지 먼저 봅니다.

- `samples/cares/` — **v4 8탭 정본**(CARES 논문 전체: 데이터+빌더+산출물, Paper Study 포함). 신규 논문의 빌더는 `templates/paper_base/_build.py`를 복사하고, 데이터 형식·디자인은 이 예제를 보고 맞춥니다.
- (1~3세대 SAFE/FrameFusion/SGL 인터랙션은 CARES가 흡수 — 견본 HTML은 배포본 미포함)
- `samples/cares/CARES_output.html` — 방법을 실제 논문(CARES, ACL 2026 · arXiv 2510.19496)에 적용한 완성 예시

---

## 4. 첫 논문 빌드 (대화형 흐름)

### 4-1. 논문 PDF 준비
`rawpaper/` 폴더를 만들고(없으면) 자기 PDF를 넣습니다. 그리고 작업 폴더를 하나 만듭니다.

논문 폴더 명명 규약: **`N. shortname`** (숫자 + 마침표 + 공백 + 소문자_언더스코어 이름).
예: `papers/1. my_paper/` (첫 논문은 1번, 다음은 2번 …). (경로에 공백·마침표가 있으니, 명령에서 **항상 큰따옴표**로 감싸세요.)

### 4-2. Claude Code 실행
이 키트 폴더에서:

```bash
claude
```

폴더 안의 `CLAUDE.md`가 자동으로 로드되어, Claude가 이 프로젝트의 규칙(v4 디자인 토큰, 8탭 구조, 번역 정책 등)을 모두 알고 시작합니다.

### 4-3. 대화로 단계 진행
Claude에게 이렇게 시작하세요:

> "`rawpaper/내논문.pdf`를 `workflow.md`의 기본 빌드(Stage 0~7 → 11 → 10)에 따라 v4 대시보드 8탭 학습 HTML로 만들어줘.
> 빌더는 `templates/paper_base/_build.py`를 복사해 `TODO_PAPER`만 채우고(`_build.py` 조립 → `tools/restyle_dash_v4.py` 변환),
> 학습 인터랙션·데이터 형식은 `samples/cares/` 정본을 따르고, ⑤⑥은 셸만 만들어줘.
> HTML이 끝나면 `rules/video_rules.md`에 따라 소개 영상(Stage 13)도 만들어줘."

그러면 Claude가 대략 이 순서로 진행합니다 (`workflow.md` 기본 빌드 Stage 0~7 → 11 → 10 → 13 — Stage 번호와 `prompts/` 파일 번호의 대응표는 `workflow.md` 머리에 있습니다):

1. **PDF → 텍스트/자산** — 본문 구조화(`tools/structure_paper.py`) + Figure/Table 자동 크롭(`tools/autocrop_assets.py` +`--verify`)
2. **구조화** — 섹션/문단/문장 단위 `structured.json` (원문 1:1 보존)
3. **번역** — 문장 단위 영한 매핑 (`translations/manual.json`) + 캡션 KR(`config#captions`)/EN(`config#captions_en`)
4. **분석 데이터** — `config.json`, `analysis.json`, `tabs_data/*.json`(dissection·knowledge·questions·**study**)
5. **HTML 조립** — `templates/paper_base/_build.py` 복사본으로 v3 조립 → `tools/restyle_dash_v4.py`로 v4 8탭 변환 → 주입기(`tools/memo_layer_fix.py` → `qa_button_inject.py` · `study_review_inject.py` · `reader_asset_chip.py`), 그림은 base64 인라인
6. **검증** — `tools/check_html_escape.py`(수식 이스케이프) · `tools/check_study_refs.py`(Paper Study ref·캡션 KR) · `tools/tone_lint.py`(문체) · `tools/check_memo_layer.py`(메모 레이어, playwright 필요) · `tools/check_paper_structure.py`(8탭·카드·자산 순서·주입 구조·영상 입력)
7. **소개 영상 (Stage 13)** — `python tools/video/make_video.py "papers/N. name" new` → 원고 `video/기획안.md` → `check-script` → `tts` → `animatic` → 클립 → `base-render` → `final` → `check` (`rules/video_rules.md` 10절)

### 4-4. 결과 확인
완성된 `{ShortName}_output.html`을 브라우저로 열고, 같은 폴더의 `{ShortName}_video.mp4`(소개 영상)를 먼저 보면 흐름을 잡기 쉽습니다. 마음에 안 드는 부분(이미지·해석·번역)은 그 자리에서 "여기 다시" 하고 다시 요청하면 됩니다.

---

## 5. 자주 막히는 곳

- **그림이 잘리거나 헤더가 섞임** → `tools/autocrop_assets.py`로 자동 크롭 후 `--verify`로 잘림 점검(`rules/parsing_rules.md` §4-A). 어긋나는 자산만 PNG를 직접 열어 수동 보정.
- **번역이 어색한 한자 조어로 나옴** → `CLAUDE.md`의 "무리한 한국어 변환 금지" 정책을 Claude에게 다시 상기시키세요.
- **codex 이미지가 안 만들어짐(Windows)** → `rules/component_rules.md` §11 의 "6계명"(Bash 사용, UTF-8 prompt.txt, `< /dev/null`, 마지막 줄 `NO paper title …` 등) 확인. codex가 없으면 이미지는 모드 B(Claude가 직접 그리는 SVG)로 대신합니다.
- **영상 단계에서 설치가 막힘** → `python tools/video/make_video.py - doctor`로 빠진 항목과 채울 명령을 확인. TTS 환경은 수 GB라 디스크·인터넷이 필요합니다.
- **이미지가 HTML에 안 박힘** → 최종 산출물은 반드시 base64 인라인. `CLAUDE.md`의 "자산 임베딩 정책" 참고.

---

## 6. 더 깊이

- `workflow.md` — 전체 흐름 개요 (Stage 0~13 — 기본 빌드는 Stage 0~7 → 11 → 10 → 13, 8·9는 요청 시, 12는 빌드 밖 연구 멘토 세션)
- `prompts/01~13_*.md` — 각 단계 프롬프트 정본 (11 = Paper Study, 12 = 빌드 완료 논문의 정립·연구 멘토 세션, 13 = 소개 영상)
- `rules/video_rules.md` · `tools/video/` — 소개 영상 규칙과 파이프라인 (클립 엔진 `skills/motion-broll/`)
- `rules/` — 파싱/분석/코칭/지식/수식/컴포넌트 + `design_v4_dashboard.md` 세부 규약
- `CLAUDE.md` — 이 모든 것을 묶는 운영 규칙 (가장 중요) · 상세 근거는 `rules/project_policies.md`, 빌드 교훈은 `rules/build_lessons.md`
- `templates/paper_base/` — 신규 논문이 복사해 쓰는 기준 빌더

막히면 Claude에게 "지금 어느 단계인지, 다음에 뭘 하면 되는지" 물어보세요. `CLAUDE.md`를 알고 있으므로 안내해 줍니다.
