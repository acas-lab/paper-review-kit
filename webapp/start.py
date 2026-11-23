#!/usr/bin/env python3
"""
start.py — 원클릭 런처 (비개발자용).

하는 일:
  1) 전제조건 점검 (Python 버전 · Claude 로그인 · codex · API키 안내)
  2) webapp/.venv 가상환경 자동 생성 + 의존성 설치
  3) 백엔드(FastAPI) 기동 + 브라우저 자동 오픈

사용:  이 파일을 더블클릭하거나,  python webapp/start.py
"""
import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

WEBAPP = Path(__file__).resolve().parent
VENV = WEBAPP / ".venv"
BIN = VENV / ("Scripts" if os.name == "nt" else "bin")
PYEXE = BIN / ("python.exe" if os.name == "nt" else "python")
REQ = WEBAPP / "backend" / "requirements.txt"
PORT = 8765
URL = f"http://127.0.0.1:{PORT}"

C_OK, C_WARN, C_ERR, C_DIM, C_END = "\033[92m", "\033[93m", "\033[91m", "\033[90m", "\033[0m"


def say(msg, c=""):
    print(f"{c}{msg}{C_END}")


def fail(msg, fix=""):
    say(f"\n  ✗ {msg}", C_ERR)
    if fix:
        say(f"    → {fix}", C_WARN)
    say("\n  (이 창을 닫고, 문제를 해결한 뒤 다시 실행하세요.)\n", C_DIM)
    try:
        input("  Enter 키를 누르면 종료합니다… ")
    except EOFError:
        pass
    sys.exit(1)


def claude_login_state(claude_bin):
    """True(로그인 확인) / False(미로그인 확인) / None(확인 불가).

    Windows·Linux 는 ~/.claude/.credentials.json 파일로 바로 판정한다. macOS 는 자격 증명이
    키체인에 있어 파일이 없으므로 `claude auth status`(JSON, loggedIn) 로 한 번 더 묻는다.
    """
    if (Path.home() / ".claude" / ".credentials.json").exists():
        return True
    try:
        r = subprocess.run([claude_bin, "auth", "status"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=20, stdin=subprocess.DEVNULL)
    except Exception:
        return None
    out = (r.stdout or "").strip()
    try:
        import json
        data = json.loads(out[out.find("{"):]) if "{" in out else {}
        if "loggedIn" in data:
            return bool(data["loggedIn"])
    except Exception:
        pass
    return None


def main():
    if os.name == "nt":
        os.system("")                       # ANSI 색 활성화
        os.system("chcp 65001 >nul 2>&1")   # 콘솔 UTF-8 (한국어 Windows의 CP949에서 이모지/한글 출력 크래시 방지)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    say("\n  Paper Review 대시보드 — 시작 준비\n", C_OK)

    # 1) Python 버전
    if sys.version_info < (3, 10):
        fail(f"Python 3.10 이상이 필요해요 (현재 {sys.version.split()[0]}).",
             "python.org 에서 최신 Python을 설치하세요.")
    say(f"  ✓ Python {sys.version.split()[0]}", C_DIM)

    # 2) Claude Code 설치 + 로그인
    if shutil.which("claude") is None:
        fail("Claude Code(claude 명령)를 찾을 수 없어요.",
             "Claude Code를 설치하세요: https://claude.com/claude-code")
    login = claude_login_state(shutil.which("claude"))
    if login is True:
        say("  ✓ Claude Code 로그인 확인", C_DIM)
    elif login is False:
        # 하드 차단하지 않는다 — 판정이 틀릴 수 있고(다른 인증 방식), 세션 시작 시 실제 오류가 다시 보인다.
        say("  ⚠ Claude 로그인이 확인되지 않아요.", C_WARN)
        say("    터미널에 `claude` 를 입력해 한 번 로그인(구독 계정)하세요. 그대로 계속 진행합니다.", C_DIM)
    else:
        say("  · Claude 로그인 상태를 미리 확인하지 못했어요 (macOS 키체인 등). 세션 시작 시 확인됩니다.", C_DIM)

    # 3) API 키 안내 — 대시보드는 이 키를 쓰지 않는다 (아래 6단계와 runner.py 가 환경에서 제거)
    if os.environ.get("ANTHROPIC_API_KEY"):
        say("  · ANTHROPIC_API_KEY 가 설정돼 있지만 대시보드는 이 키를 무시하고 구독 로그인(OAuth)을 사용해요.", C_DIM)

    # 4) codex (선택)
    if shutil.which("codex"):
        say("  ✓ codex CLI 확인 (학습 보조 이미지 생성 가능)", C_DIM)
    else:
        say("  · codex 없음 — 이미지 생성 단계는 자동 스킵됩니다.", C_DIM)

    # 5) venv 생성 + 의존성 설치
    if not PYEXE.exists():
        say("\n  가상환경(venv) 생성 중… (처음 한 번)", C_OK)
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    say("  의존성 확인/설치 중… (처음엔 몇 분 걸릴 수 있어요)", C_OK)
    r = subprocess.run([str(PYEXE), "-m", "pip", "install", "-q",
                        "--disable-pip-version-check", "-r", str(REQ)])
    if r.returncode != 0:
        fail("의존성 설치에 실패했어요.",
             f"인터넷 연결 확인 후 다시 실행하거나, 수동 설치: {PYEXE} -m pip install -r {REQ}")
    say("  ✓ 준비 완료", C_OK)

    # 6) 서버 기동 + 브라우저
    say(f"\n  >> 대시보드 시작 → {URL}", C_OK)
    say("     (종료: 이 창에서 Ctrl+C)\n", C_DIM)
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)  # OAuth 폴백 보장 (키 과금 방지)
    env["PAPER_REVIEW_PORT"] = str(PORT)  # main.py 의 Host/Origin 검사가 같은 포트를 쓰도록
    proc = subprocess.Popen(
        [str(PYEXE), "-m", "uvicorn", "main:app",
         "--app-dir", str(WEBAPP / "backend"),
         "--host", "127.0.0.1", "--port", str(PORT)],
        env=env,
    )
    time.sleep(2.5)
    try:
        webbrowser.open(URL)
    except Exception:
        pass
    try:
        proc.wait()
    except KeyboardInterrupt:
        say("\n  종료합니다…", C_DIM)
        proc.terminate()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        fail(f"실행 중 오류: {e}")
