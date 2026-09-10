# -*- coding: utf-8 -*-
"""PreToolUse(Bash) 훅 - codex 호출 전에 prompt_*.txt 밀도 게이트를 강제한다.

stdin 으로 들어온 Bash tool_input.command 를 보고:
  · `codex` 가 없는 명령이면 그냥 통과 (아무것도 출력하지 않음)
  · 있으면 명령문에서 `prompt_<purpose>.txt` 이름과 `--cd <경로>` 를 뽑아
    **codex 가 실제로 읽을 파일**(= <cd>/<name>)을 check_image_prompts 로 검사
  · `--cd` 를 못 찾으면 `papers/*/assets/generated/` 에서 찾되, 같은 파일명이
    여러 논문에 있으므로 **후보가 정확히 1개일 때만** 검사한다 (오탐 방지)
  · FAIL 이 있으면 PreToolUse permissionDecision=deny 로 **호출 자체를 차단**

설계 원칙 - 게이트가 작업을 잘못 막는 쪽이 더 나쁘다:
  · stdin 파싱 실패 · 프롬프트 파일 못 찾음 · 검사기 예외 → 전부 **통과**
  · 차단은 "밀도 기준 위반이 확실할 때"만

정본: rules/component_rules.md §11.8 / 설정: .claude/settings.json hooks.PreToolUse
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def emit(obj):
    """Windows 콘솔 인코딩과 무관하게 UTF-8 JSON 한 줄을 내보낸다."""
    sys.stdout.buffer.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")


def deny(reason):
    emit({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    })


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    cmd = ((data.get("tool_input") or {}).get("command")) or ""
    if "codex" not in cmd:
        return

    names = list(dict.fromkeys(re.findall(r"prompt_[A-Za-z0-9_]+\.txt", cmd)))
    if not names:
        return

    try:
        sys.path.insert(0, str(REPO / "tools"))
        import check_image_prompts as C
    except Exception:
        return

    # codex 가 읽을 작업 디렉토리 - `--cd "<path>"` / `--cd <path>`
    cd = None
    m = re.search(r'--cd\s+"([^"]+)"', cmd) or re.search(r"--cd\s+'([^']+)'", cmd) \
        or re.search(r"--cd\s+(\S+)", cmd)
    if m:
        cd = Path(m.group(1))

    blocks, checked = [], 0
    for name in names:
        p = None
        if cd is not None:
            cand = cd / name
            if cand.is_file():
                p = cand
        if p is None:
            # 같은 파일명이 여러 논문에 존재 - 유일할 때만 검사한다
            cands = sorted((REPO / "papers").glob(f"*/assets/generated/{name}"))
            if len(cands) == 1:
                p = cands[0]
        if p is None:
            continue
        try:
            fails, _warns, stats = C.check_prompt(p)
        except Exception:
            continue
        checked += 1
        if fails:
            head = f"{p}  (패널 {stats[0]} · 수치 {stats[1]} · {stats[2]}B)"
            blocks.append(head + "\n" + "\n".join(f"  - {msg}" for msg in fails))

    if not blocks:
        return

    deny(
        "🔴 프롬프트 밀도 게이트 실패 - codex 호출을 막았습니다.\n\n"
        + "\n\n".join(blocks)
        + "\n\n성긴 프롬프트는 여백만 크고 정보량이 적은 그림으로 돌아옵니다.\n"
          "`rules/component_rules.md` §11.8 대로 prompt.txt 를 고친 뒤 다시 호출하세요.\n"
          "(단마다 서브패널 3~4개 · 패널마다 시각 형태 + 실제 수치 + 영어 캡션)\n"
          "재확인: python tools/check_image_prompts.py \"<위 경로>\""
    )


if __name__ == "__main__":
    main()
