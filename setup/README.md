# setup/ — 더블클릭 설치 스크립트 (Windows)

프로그래밍을 해 본 적이 없어도 되는 설치 순서입니다. 각 `.bat` 파일을 **번호 순서대로, 한 번에 하나씩** 더블클릭하세요.
창이 끝날 때 `[OK]` 또는 `[FAIL]` 한 줄과 "다음에 무엇을 누를지"가 나옵니다. 화면 설명은 영어지만 짧습니다(한국어 풀이는 `GUIDE.html`).

> 어떤 파일이 무엇을 하는지 자세한 그림 설명은 킷 루트의 **`GUIDE.html`** 을 브라우저로 여세요.

## 파일 목록

| 파일 | 하는 일 | 언제 |
|---|---|---|
| `0_check.bat` | 설치는 하지 않고, python / node / npm / claude / codex / git / winget 이 있는지와 버전만 출력. 마지막에 "아직 돌려야 할 단계 번호"를 알려줌 | 처음 + 막힐 때마다 |
| `1_install_python.bat` | winget 으로 Python 3.12 설치(PATH 자동 등록). 3.10 이상이 이미 있으면 건너뜀. winget 이 없으면 python.org 수동 설치 안내 | 처음 한 번 |
| `2_install_node_and_claude.bat` | Node.js LTS 설치(있으면 건너뜀) → `npm install -g @anthropic-ai/claude-code` 로 Claude Code 설치. Node 를 방금 깔았으면 **창을 닫고 같은 파일을 한 번 더** 더블클릭하라고 안내할 수 있음 | 처음 한 번 |
| `3_login_claude.bat` | `claude` 를 실행해 브라우저에서 **본인 Claude 구독 계정**으로 로그인. 프롬프트가 뜨면 `/exit` 입력. 끝나면 로그인 파일 존재 여부로 OK / NOT logged in 판정 | 처음 한 번 |
| `4_install_kit_packages.bat` | CLI 도구(`tools/*.py`)가 쓰는 `pymupdf`·`playwright` + Chromium 을 시스템 Python 에 설치. (웹 모드는 첫 실행 때 자기 venv 를 따로 만들므로 이 단계 없이도 동작하지만, 해 두면 무해) | 처음 한 번 |
| `5_start_web.bat` | **웹 모드 매일 실행기** — `webapp/win_start.bat` 을 호출. 첫 실행 때 `webapp/.venv` 생성 + 패키지 설치(몇 분) 후 브라우저가 `http://127.0.0.1:8765` 를 엶 | 매일 |
| `6_start_cli.bat` | **CLI 모드 매일 실행기** — 킷 루트에서 `claude` 를 열어 줌. `GUIDE.html` 4절의 프롬프트를 붙여 넣고 시작 | 매일 |
| `7_install_codex_optional.bat` | **선택** — `npm install -g @openai/codex`. 학습 보조 이미지를 PNG 로 그리는 모드 A 에만 필요(없으면 Claude 가 SVG 로 그리는 모드 B 로 자동 대체). 설치 후 `codex login` 은 직접 실행 | 필요할 때만 |

## 순서

1. **처음 한 번**: `0` → `1` → `2` → `3` → `4`
   - 각 단계가 끝나면 **창을 닫고** 다음 번호를 더블클릭합니다. (설치 프로그램이 PATH 에 추가한 명령은 이미 열려 있던 창에서는 안 보이기 때문입니다.)
   - 이미 설치된 단계는 `[OK] already installed` 만 찍고 끝나므로, 다시 눌러도 안전합니다.
2. **매일**: `5_start_web.bat`(브라우저에서 작업) 또는 `6_start_cli.bat`(터미널에서 Claude 와 대화) 중 하나
3. `7` 은 codex 이미지 생성을 쓰고 싶을 때만

막히면 `0_check.bat` 을 다시 눌러 어느 번호가 남았는지 확인하세요.

## mac / Linux 사용자

`.bat` 은 Windows 전용입니다. 터미널에서 같은 일을 이렇게 합니다.

```bash
# 1. Python 3.10+  (mac: brew install python@3.12 / Ubuntu: sudo apt install python3 python3-venv python3-pip)
python3 --version

# 2. Node.js LTS (https://nodejs.org) 설치 후 Claude Code
npm install -g @anthropic-ai/claude-code

# 3. 로그인 (브라우저가 열림 - 구독 계정) → 프롬프트에서 /exit
claude

# 4. CLI 도구용 패키지 (웹 모드만 쓸 거면 생략 가능)
python3 -m pip install --upgrade pip pymupdf playwright
python3 -m playwright install chromium

# 5. 웹 모드 매일 실행 (처음 한 번 chmod +x webapp/linux_start.sh)
./webapp/linux_start.sh

# 6. CLI 모드 매일 실행 (킷 루트에서)
claude

# 7. (선택) codex
npm install -g @openai/codex && codex login
```
