"""
runner.py — Claude Code 글루 (검증된 verify_glue.py 기반).

WebSocket 연결 1개당 ChatSession 1개. claude-agent-sdk의 ClaudeSDKClient로
멀티턴 대화를 유지하고, 들어오는 메시지를 WebSocket용 dict 이벤트로 변환한다.

인증: ANTHROPIC_API_KEY를 제거해 로그인된 Claude 구독(OAuth)으로 폴백.
환경: venv의 Scripts/bin을 PATH 앞에 두어, Claude의 Bash 도구가 부르는
      `python`/`codex`가 이 webapp venv를 쓰도록 한다 (PyMuPDF 등 자기완결).
"""
from __future__ import annotations

import json
import os
import time
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
    "Task",                              # 병렬 서브에이전트 — CLI처럼 번역/분석 fan-out (속도)
    "Bash(python *)", "Bash(python3 *)", "Bash(py *)", "Bash(codex *)",
    "Bash(pip *)",                       # 의존성 설치(PyMuPDF 등) — CLI 패리티
    "Bash(mkdir *)", "Bash(cp *)", "Bash(mv *)",  # 폴더 생성·자산 백업/이동
    "Bash(ls *)", "Bash(cat *)", "Bash(echo *)",
    "Bash(type *)", "Bash(find *)",
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
    "- JSON(번역·분석)을 고친 뒤 HTML에 반영하려면 해당 논문 폴더의 `_build.py`를 다시 실행해야 한다.\n"
    "- 🔴 web↔CLI 결과 통일성: 기계적·구조적 단계는 **반드시 정본 도구를 그대로 사용**한다 — "
    "본문 구조화는 `python tools/structure_paper.py <pdf> <out structured.json>`(전 본문 1:1 캡처), "
    "figure/표 크롭은 `python tools/autocrop_assets.py <pdf> <assets>` + `--verify`, "
    "조립은 폴더의 `_build.py`. 손으로 좌표·문장을 추측하거나 본문 일부만 담지 말 것. "
    "이 도구들은 같은 입력에 같은 출력을 내므로 CLI와 결과가 일치한다. 자세한 정책: CLAUDE.md "
    "§web↔CLI 결과 통일성.\n"
    "- 사용자 메시지 앞에 `[이미지 생성 모드: codex|claude_svg]` 태그가 붙어 온다. "
    "이는 학습 보조 이미지(② ~ ⑥) 생성 방식을 지정한다 — `codex`면 codex CLI ImageGen(PNG), "
    "`claude_svg`면 외부 도구 없이 인라인 `<svg>` 도식을 직접 작성. 규약 정본은 "
    "`rules/component_rules.md` §11.8. codex 모드인데 codex 호출이 실패하면 그 자산만 SVG로 폴백한다.\n"
    "- ⚡ 속도: 번역(전 본문)·분석 카드처럼 양이 많고 독립적인 작업은 **Task 도구로 서브에이전트를 "
    "병렬 fan-out** 해서 처리한다(CLI와 동일한 방식). 한 컨텍스트에서 수백 문장을 순차 처리하지 말 것."
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


PAPERS_DIR = PROJECT_DIR / "papers"


def _latest_summary(since: float):
    """Find the most recently written dissection.json (after `since`) and pull its
    핵심 관찰(diss-observe) + 방법론(diss-logic) cards for the floating live-summary panel.
    Returns a dict or None."""
    best = None
    if not PAPERS_DIR.exists():
        return None
    for dj in PAPERS_DIR.glob("*/tabs_data/dissection.json"):
        try:
            mt = dj.stat().st_mtime
        except OSError:
            continue
        if mt < since - 2:
            continue
        if best is None or mt > best[0]:
            best = (mt, dj)
    if not best:
        return None
    try:
        data = json.loads(best[1].read_text(encoding="utf-8"))
    except Exception:
        return None
    folder = best[1].parents[1].name

    def card(cls):
        for c in data.get("cards", []):
            if c.get("cls") == cls:
                return [{"tag": r.get("tag", ""), "body": r.get("body", "")} for r in c.get("rows", [])]
        return []

    observe, method = card("diss-observe"), card("diss-logic")
    if not observe and not method:
        return None
    return {"type": "summary", "paper": folder, "observe": observe, "method": method}


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
        self.started_at: float = 0.0

    async def start(self) -> None:
        self.started_at = time.time()
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
                # surface the live paper summary (핵심 관찰/방법론) as it gets written
                summary = _latest_summary(self.started_at)
                if summary:
                    await emit(summary)
            elif isinstance(msg, ResultMessage):
                self.session_id = getattr(msg, "session_id", None)
                # duration: SDK reports duration_ms; this run uses the logged-in Claude
                # subscription (no ANTHROPIC_API_KEY) so there is NO per-token billing —
                # we report TIME, not the SDK's hypothetical USD-equivalent.
                dur = getattr(msg, "duration_ms", None)
                await emit({
                    "type": "result",
                    "session_id": self.session_id,
                    "is_error": getattr(msg, "is_error", False),
                    "duration_ms": dur,
                })
                final = _latest_summary(self.started_at)
                if final:
                    await emit(final)

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
