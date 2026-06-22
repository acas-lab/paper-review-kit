"""
runner.py — Claude Code 글루 (검증된 verify_glue.py 기반).

WebSocket 연결 1개당 ChatSession 1개. claude-agent-sdk의 ClaudeSDKClient로
멀티턴 대화를 유지하고, 들어오는 메시지를 WebSocket용 dict 이벤트로 변환한다.

인증: ANTHROPIC_API_KEY를 제거해 로그인된 Claude 구독(OAuth)으로 폴백.
환경: venv의 Scripts/bin을 PATH 앞에 두어, Claude의 Bash 도구가 부르는
      `python`/`codex`가 이 webapp venv를 쓰도록 한다 (PyMuPDF 등 자기완결).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Awaitable, Callable, Optional

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    UserMessage,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ToolResultBlock,
)

# webapp/backend/runner.py → parents[2] = paper-review-kit/
PROJECT_DIR = Path(__file__).resolve().parents[2]
_VENV = Path(__file__).resolve().parents[1] / ".venv"
_VENV_BIN = _VENV / ("Scripts" if os.name == "nt" else "bin")

# 권한: 파일 편집 자동승인 + Bash 화이트리스트. 파괴적 명령은 차단.
ALLOWED_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep",
    "Bash(python *)", "Bash(py *)", "Bash(codex *)",
    "Bash(mkdir *)", "Bash(cp *)", "Bash(ls *)",
    "Bash(cat *)", "Bash(echo *)", "Bash(type *)",
]
DISALLOWED_TOOLS = [
    "Bash(rm *)", "Bash(del *)", "Bash(sudo *)",
    "Bash(curl *)", "Bash(wget *)",
    "Bash(git push *)", "Bash(git commit *)", "Bash(git reset *)",
]

# 웹앱 세션 전용 추가 지침 — Claude Code 기본 프롬프트에 append
WEBAPP_APPEND = (
    "이 세션은 Paper Review 웹 대시보드(로컬)에서 실행된다.\n"
    "- 분석·검수(번역 점검, 카운트 비교 등)는 **임시 스크립트 파일을 만들지 말고** "
    "`python -c \"...\"` 인라인으로 실행한다. `cat > _chk.py` 같은 스크래치 파일 생성 금지.\n"
    "- 부득이 임시 파일이 필요하면 시스템 임시 폴더에 만들고, papers/·samples/ 같은 "
    "콘텐츠 폴더에는 `_chk`·`_tmp`·`_pairs` 등 잔여 파일을 남기지 않는다 "
    "(이 폴더들에서는 rm이 차단되어 정리도 안 된다).\n"
    "- JSON(번역·분석)을 고친 뒤 HTML에 반영하려면 해당 논문 폴더의 `_build.py`를 다시 실행해야 한다."
)

Emit = Callable[[dict], Awaitable[None]]


def _build_env() -> dict:
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)  # OAuth 구독 폴백 강제
    env["PATH"] = str(_VENV_BIN) + os.pathsep + env.get("PATH", "")
    return env


def make_options(resume_session_id: Optional[str] = None) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=str(PROJECT_DIR),
        permission_mode="acceptEdits",
        system_prompt={"type": "preset", "preset": "claude_code", "append": WEBAPP_APPEND},
        allowed_tools=ALLOWED_TOOLS,
        disallowed_tools=DISALLOWED_TOOLS,
        setting_sources=["user", "project", "local"],  # CLAUDE.md/rules 로드 보장
        env=_build_env(),
        resume=resume_session_id,
        include_partial_messages=False,
    )


def _tool_brief(inp) -> str:
    if not isinstance(inp, dict):
        return ""
    for k in ("command", "file_path", "path", "pattern", "prompt"):
        if k in inp and inp[k]:
            v = str(inp[k]).replace("\n", " ")
            return v[:160] + ("…" if len(v) > 160 else "")
    return ""


class ChatSession:
    """WebSocket 연결 1개 = 이 세션 1개. 멀티턴 대화 유지."""

    def __init__(self) -> None:
        self.client: Optional[ClaudeSDKClient] = None
        self.session_id: Optional[str] = None

    async def start(self) -> None:
        self.client = ClaudeSDKClient(options=make_options())
        await self.client.connect()

    async def send(self, text: str, emit: Emit) -> None:
        assert self.client is not None, "session not started"
        await self.client.query(text)
        async for msg in self.client.receive_response():
            if isinstance(msg, AssistantMessage):
                for b in msg.content:
                    if isinstance(b, TextBlock) and b.text.strip():
                        await emit({"type": "text", "text": b.text})
                    elif isinstance(b, ThinkingBlock):
                        await emit({"type": "thinking"})
                    elif isinstance(b, ToolUseBlock):
                        await emit({
                            "type": "tool_use",
                            "name": b.name,
                            "brief": _tool_brief(b.input),
                        })
            elif isinstance(msg, UserMessage):
                for b in (getattr(msg, "content", None) or []):
                    if isinstance(b, ToolResultBlock):
                        await emit({"type": "tool_result"})
            elif isinstance(msg, ResultMessage):
                self.session_id = getattr(msg, "session_id", None)
                await emit({
                    "type": "result",
                    "session_id": self.session_id,
                    "is_error": getattr(msg, "is_error", False),
                    "cost_usd": getattr(msg, "total_cost_usd", None),
                })

    async def interrupt(self) -> None:
        if self.client:
            try:
                await self.client.interrupt()
            except Exception:
                pass

    async def close(self) -> None:
        if self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass
        self.client = None
