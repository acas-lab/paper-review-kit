"""
글루 검증 (PLAN §11-2) — 가장 불확실한 부분 먼저.

확인 항목:
  1. Python에서 로그인된 Claude Code를 헤드리스로 호출 (API 키 없이 OAuth)
  2. 응답이 스트리밍(텍스트 델타)으로 들어오는지
  3. cwd=프로젝트 폴더 → CLAUDE.md/rules 자동 로드되는지

실행:  webapp/.venv/Scripts/python.exe webapp/verify_glue.py
"""
import asyncio
import os
import sys
from pathlib import Path

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent  # paper-review-kit/


async def main() -> int:
    # OAuth 폴백 전제: API 키가 환경에 남아 있으면 경고
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("[!] ANTHROPIC_API_KEY가 설정돼 있습니다 — OAuth 구독 대신 키가 우선됩니다.")

    print(f"[*] cwd = {PROJECT_DIR}")
    print("[*] Claude 헤드리스 호출 시작 (스트리밍)...\n")

    options = ClaudeAgentOptions(
        cwd=str(PROJECT_DIR),
        permission_mode="acceptEdits",
        allowed_tools=["Read", "Glob", "Grep"],  # 검증이라 읽기 도구만
        max_turns=2,
    )

    # CLAUDE.md가 로드됐는지 알 수 있는 질문
    prompt = (
        "이 프로젝트의 CLAUDE.md를 봤다면, 표준 학습 템플릿의 탭 개수와 "
        "기본 빌드에서 셸만 만드는 탭 두 개의 라벨을 한 줄로만 답해줘. "
        "(프로젝트 지침을 읽었다는 증거로)"
    )

    got_text = False
    got_result = False
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    sys.stdout.write(block.text)
                    sys.stdout.flush()
                    got_text = True
        elif isinstance(message, ResultMessage):
            got_result = True
            print("\n\n--- ResultMessage ---")
            print(f"  session_id : {getattr(message, 'session_id', None)}")
            print(f"  is_error   : {getattr(message, 'is_error', None)}")
            cost = getattr(message, "total_cost_usd", None)
            print(f"  cost_usd   : {cost}")

    print("\n=== 검증 결과 ===")
    print(f"  스트리밍 텍스트 수신 : {'OK' if got_text else 'FAIL'}")
    print(f"  ResultMessage 수신   : {'OK' if got_result else 'FAIL'}")
    return 0 if (got_text and got_result) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
