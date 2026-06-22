# Paper Review 대시보드 — 연구실 사용 안내

논문 PDF를 **브라우저에서** 6탭 학습 HTML로 만드는 로컬 웹앱.
각자 자기 PC에서 실행하고, **각자 본인의 Claude 구독**으로 동작합니다 (별도 API 키·비용 없음).

---

## 처음 한 번만 — 준비물

1. **Claude Code 설치 + 로그인** ← 이게 이용 자격입니다
   - 설치: https://claude.com/claude-code
   - 터미널에 `claude` 한 번 입력 → 본인 구독(Pro/Max) 계정으로 로그인
2. **Python 3.10 이상** — https://www.python.org (설치 시 "Add Python to PATH" 체크)
3. (선택) **codex CLI** — 학습 보조 이미지 생성용. 없으면 이미지 단계만 자동 스킵.

> API 키는 필요 없습니다. 오히려 `ANTHROPIC_API_KEY` 환경변수가 설정돼 있으면
> 구독 대신 그 키로 과금되니, 구독으로 쓰려면 지워 두세요 (런처가 경고해 줍니다).

---

## 실행

- **Windows**: `webapp/start.bat` 더블클릭
- **macOS/Linux/수동**: 터미널에서 `python webapp/start.py`

처음 실행하면 가상환경(venv)을 만들고 의존성을 설치합니다(몇 분). 끝나면
브라우저가 자동으로 `http://127.0.0.1:8765` 를 엽니다. 종료는 창에서 `Ctrl+C`.

---

## 쓰는 법

1. 오른쪽 **① PDF 업로드** 에 논문 PDF를 끌어다 놓기
2. 채팅 입력칸에 자동으로 요청 문장이 채워짐 → 다듬어서 전송
   (예: *"이 논문으로 papers 폴더 만들고 6탭 HTML 만들어줘. 디자인 SGL 정본, ⑤⑥은 셸만."*)
3. 진행이 채팅에 실시간으로 흐름 (🔧 도구 사용 배지 포함). 중간에 *"그림 다시"*,
   *"이 번역 어색해"* 처럼 교정 요청 가능
4. 완성되면 오른쪽 **② 논문 목록**에서 결과 HTML 클릭 → **③ 미리보기**, 또는 새 탭으로 열기

결과는 그림이 모두 박힌 **단일 HTML 한 장**(self-contained)이라, 그 파일만 옮겨도 어디서나 열립니다.

---

## 안 될 때

| 증상 | 해결 |
|---|---|
| "Claude 로그인 필요" | 터미널에 `claude` 입력 후 로그인하고 다시 실행 |
| "API 키가 설정됨" 경고 | 구독으로 쓰려면 `ANTHROPIC_API_KEY` 환경변수 삭제 |
| 이미지가 안 생김 | codex CLI 미설치 — 선택사항이라 나머지는 정상 진행 |
| 글루만 따로 점검 | `webapp/.venv/Scripts/python webapp/verify_glue.py` |

권한: 파일 편집은 자동 승인, Bash는 화이트리스트(`python`/`codex`/`mkdir`…)만 허용,
`rm`·`sudo`·`git push` 등 파괴적 명령은 차단합니다.
