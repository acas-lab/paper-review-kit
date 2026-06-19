# SETUP — 설치 + 첫 논문 따라하기

이 문서대로 따라 하면, 자기 컴퓨터에서 논문 PDF 한 편을 6탭 학습 HTML로 만들 수 있습니다.
**빌드 자동화는 없습니다.** Claude Code와 *대화하면서* 한 단계씩 만듭니다.

---

## 1. 필요한 것 설치

### (필수) Claude Code
이 키트의 "엔진"입니다. Claude 계정/구독(또는 API 키)이 필요합니다.

- 설치·로그인 방법: 공식 문서 https://docs.claude.com/claude-code 참고
- 설치 확인: 터미널에서 `claude --version`

### (필수) Python 3 + PyMuPDF
PDF에서 텍스트와 그림/표를 뽑고, 최종 HTML을 조립할 때 씁니다.

```bash
python --version        # 3.9+ 권장
pip install pymupdf      # import 이름은 fitz
```

### (선택) codex CLI
②~⑥ 탭의 학습 보조 일러스트를 생성할 때만 필요합니다. 없으면 그 단계만 건너뛰면 됩니다.
설치 방법은 codex CLI 공식 안내를 따르세요.

---

## 2. 키트 받기

```bash
git clone https://github.com/Edward-Youn/paper-review-kit.git
cd paper-review-kit
```

또는 GitHub의 **"Use this template"** / **"Download ZIP"** 으로 받아도 됩니다.

> 자기 작업은 이 폴더를 복사해 쓰거나, 자기 GitHub 저장소로 따로 관리하길 권합니다.

---

## 3. 먼저 견본을 열어 본다 (목표 이미지 잡기)

브라우저로 아래 파일을 열어 "완성형"이 어떤 모습인지 먼저 봅니다.

- `samples/SGL_output.html` — 가장 최신(3세대) 인터랙션. **신규 논문은 이걸 베이스로 따라갑니다.**
- `samples/SAFE_output.html`, `samples/FrameFusion_output.html` — 1·2세대
- `papers/22. free/FREE_output.html` — 방법을 실제 2025년 논문에 적용한 완성 예시

---

## 4. 첫 논문 빌드 (대화형 흐름)

### 4-1. 논문 PDF 준비
`rawpaper/` 폴더를 만들고(없으면) 자기 PDF를 넣습니다. 그리고 작업 폴더를 하나 만듭니다.

논문 폴더 명명 규약: **`N. shortname`** (숫자 + 마침표 + 공백 + 소문자_언더스코어 이름).
예: `papers/100. my_paper/`. (경로에 공백·마침표가 있으니, 명령에서 **항상 큰따옴표**로 감싸세요.)

### 4-2. Claude Code 실행
이 키트 폴더에서:

```bash
claude
```

폴더 안의 `CLAUDE.md`가 자동으로 로드되어, Claude가 이 프로젝트의 규칙(디자인 토큰, 6탭 구조, 번역 정책 등)을 모두 알고 시작합니다.

### 4-3. 대화로 단계 진행
Claude에게 이렇게 시작하세요:

> "`rawpaper/내논문.pdf`를 `workflow.md` 10단계에 따라 6탭 학습 HTML로 만들어줘.
> 디자인·인터랙션은 `samples/`의 SGL을 정본으로 따라가고, ⑤⑥은 셸만 만들어줘."

그러면 Claude가 대략 이 순서로 진행합니다 (`workflow.md` / `prompts/01~10` 기준):

1. **PDF → 텍스트/자산** — 본문 추출 + Figure/Table PNG 크롭 (`tools/`, PyMuPDF)
2. **구조화** — 섹션/문단/문장 단위 `structured.json` (원문 1:1 보존)
3. **번역** — 문장 단위 영한 매핑 (`translations/manual.json`)
4. **분석 데이터** — `config.json`, `analysis.json`, `tabs_data/*.json`
5. **HTML 조립** — `samples/` 정본 + 위 데이터로 단일 HTML 한 장, 그림은 base64 인라인

### 4-4. 결과 확인
완성된 `{ShortName}_output.html` 한 장을 브라우저로 엽니다. 마음에 안 드는 부분(이미지·해석·번역)은 그 자리에서 "여기 다시" 하고 다시 요청하면 됩니다.

---

## 5. 자주 막히는 곳

- **그림이 잘리거나 헤더가 섞임** → `rules/parsing_rules.md` §4-A (캡션 좌표 기반 크롭). PNG를 직접 열어 보며 4~8pt 단위로 조정.
- **번역이 어색한 한자 조어로 나옴** → `CLAUDE.md`의 "무리한 한국어 변환 금지" 정책을 Claude에게 다시 상기시키세요.
- **codex 이미지가 안 만들어짐(Windows)** → `rules/component_rules.md` §11 의 "5계명"(Bash 사용, UTF-8 prompt.txt, `< /dev/null` 등) 확인.
- **이미지가 HTML에 안 박힘** → 최종 산출물은 반드시 base64 인라인. `CLAUDE.md`의 "자산 임베딩 정책" 참고.

---

## 6. 더 깊이

- `workflow.md` — 10단계 전체 흐름 개요
- `prompts/01~10_*.md` — 각 단계 프롬프트 정본
- `rules/` — 파싱/분석/코칭/지식/수식/컴포넌트 세부 규약
- `CLAUDE.md` — 이 모든 것을 묶는 운영 규칙 (가장 중요)

막히면 Claude에게 "지금 어느 단계인지, 다음에 뭘 하면 되는지" 물어보세요. `CLAUDE.md`를 알고 있으므로 안내해 줍니다.
