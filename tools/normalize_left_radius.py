# -*- coding: utf-8 -*-
"""
normalize_left_radius.py - 좌측 바 제거의 잔재 정리.

배경
  tools/strip_left_bars.py 가 저장소 전체에서 좌측 색상 바(border-left 3~5px)를 제거했다.
  바가 있던 시절 왼쪽 두 모서리만 직각으로 준 규칙(`border-radius:0 8px 8px 0`)이 남아
  바 없는 상태에서 왼쪽만 각져 보인다. 이 도구가 그 잔재를 정리한다.

패스 A - 좌측만 0 인 border-radius 정규화
  대상 = shorthand 축약 전 형태(4값/3값/2값)와 개별 속성(border-top-left-radius,
         border-bottom-left-radius)을 모두 해석해 "좌측 두 모서리만 0" 인 선언.
  조건 = 같은 규칙 블록에 border-left 계열 선언이 없어야 한다.
         (`.paper-caption` 처럼 1px/3px var(--line) 바를 아직 유지하는 규칙은 좌측 직각이
          의도된 디자인이므로 건드리지 않는다.)
  동작 = 우측 값을 기준으로 네 모서리를 같은 값으로 만든다. `0 8px 8px 0` -> `8px`.

패스 B - 스타일 없는 qa-* leaf 클래스 보강
  papers/1(수작업 1세대 ⑥ Q&A)에서 CSS 정의 없이 렌더되는 leaf 클래스 2종을 보강한다.
  `.qa-ref-text`        - 외부 참조(비클릭) 인용 제목. 내부 참조는 `<a>` 라 `.qa-ref a` 를
                          받지만 외부는 `<span>` 이라 아무 규칙도 받지 않는다.
  `.qa-list-item-plain` - `.qa-list-item` 과 달리 marker/body 자식 쌍이 없는 평문 항목.
                          `.qa-list-item` 로 치환하면 36px marker 컬럼이 빈 칸으로 남으므로
                          같은 세로 리듬만 재현하는 별도 규칙을 준다.
  파이썬 튜플 repr 이 그대로 새어 나온 `(&#x27;라벨&#x27;, &#x27;본문&#x27;)` 항목은
  `<strong>라벨</strong>본문` 으로 편다(정보 손실 0). --no-unwrap 으로 끌 수 있다.

성질
  additive 아님(치환) · idempotent(두 번 돌려 0바이트 변화) · dry-run 지원.
  좌측 색상 바를 되살리지 않는다 - 이 도구는 border-left 를 한 글자도 쓰지 않는다.

사용
  python tools/normalize_left_radius.py --all
  python tools/normalize_left_radius.py --all --root "D:/1. 논문/paper-review-kit"
  python tools/normalize_left_radius.py "papers/1. safe_learning" --dry-run
  python tools/normalize_left_radius.py --all --dry-run --verbose
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 패스 A - border-radius
# ---------------------------------------------------------------------------

RADIUS_RE = re.compile(
    r"(?P<prop>border-radius|border-top-left-radius|border-bottom-left-radius)"
    r"(?P<gap>\s*:\s*)(?P<val>[^;}\n]{1,90})(?=[;}])",
    re.IGNORECASE,
)

ZERO = ("0", "0px", "0%", "0em", "0rem")


def _is_zero(tok: str) -> bool:
    return tok.lower() in ZERO


def normalized_value(prop: str, val: str):
    """좌측만 0 이면 정규화된 값을, 아니면 None 을 돌려준다."""
    v = " ".join(val.split())
    if not v or "/" in v:
        return None
    parts = v.split()
    if any("var(" in p or "calc(" in p for p in parts):
        return None
    prop = prop.lower()
    if prop != "border-radius":
        # 개별 좌측 속성은 여기서 판정하지 않는다(대응 우측 값을 알 수 없다).
        return None
    if len(parts) == 4:  # tl tr br bl
        tl, tr, br, bl = parts
        if _is_zero(tl) and _is_zero(bl) and not (_is_zero(tr) and _is_zero(br)):
            return tr if tr == br else f"{tr} {tr} {br} {br}"
        return None
    if len(parts) == 3:  # tl (tr,bl) br
        tl, trbl, br = parts
        if _is_zero(tl) and _is_zero(trbl) and not _is_zero(br):
            return br
        return None
    if len(parts) == 2:  # (tl,br) (tr,bl)
        a, b = parts
        if _is_zero(a) and not _is_zero(b):
            return b
        return None
    return None


def _rule_block(text: str, at: int):
    """선언 위치를 감싸는 규칙 블록의 (본문, 선택자)."""
    open_i = text.rfind("{", 0, at)
    if open_i < 0:
        return "", ""
    close_i = text.find("}", at)
    if close_i < 0:
        close_i = len(text)
    body = text[open_i + 1 : close_i]
    prev_end = max(text.rfind("}", 0, open_i), text.rfind(";", 0, open_i))
    sel = " ".join(text[prev_end + 1 : open_i].split())
    return body, sel


LEFT_BAR_RE = re.compile(r"border-left(?:-color|-width|-style)?\s*:", re.IGNORECASE)


def pass_radius(text: str, hits: list, verbose: bool = False) -> str:
    out = []
    last = 0
    for m in RADIUS_RE.finditer(text):
        new = normalized_value(m.group("prop"), m.group("val"))
        if new is None:
            continue
        body, sel = _rule_block(text, m.start())
        if LEFT_BAR_RE.search(body):
            hits.append(("keep", sel, " ".join(m.group("val").split()), None))
            continue
        hits.append(("fix", sel, " ".join(m.group("val").split()), new))
        out.append(text[last : m.start()])
        out.append(m.group("prop") + m.group("gap") + new)
        last = m.end()
    out.append(text[last:])
    return "".join(out)


# ---------------------------------------------------------------------------
# 패스 B - 스타일 없는 qa-* leaf 클래스
# ---------------------------------------------------------------------------

ORPHAN_MARK = "/* normalize_left_radius.py: orphan qa-* leaf classes v1 */"

ORPHAN_CSS = (
    ORPHAN_MARK
    + "\n"
    ".qa-ref-text{color:var(--ink-soft,var(--muted))}\n"
    ".qa-list-item-plain{padding:10px 0;border-bottom:1px dashed var(--line);"
    "font-size:13px;line-height:1.65;color:var(--ink)}\n"
    ".qa-list-item-plain:last-child{border-bottom:none}\n"
    ".qa-list-item-plain strong{display:block;color:var(--accent);"
    "font-size:13.5px;margin-bottom:4px}\n"
)

# `(&#x27;라벨&#x27;, &#x27;본문&#x27;)` -> `<strong>라벨</strong>본문`
TUPLE_RE = re.compile(
    r'(<li class="qa-list-item-plain">)'
    r"\(&#x27;(?P<label>[^&]{0,120}?)&#x27;,\s*&#x27;(?P<body>.*?)&#x27;\)"
    r"(</li>)",
    re.DOTALL,
)


def _class_used(text: str, cls: str) -> bool:
    return re.search(r'class="[^"]*\b' + re.escape(cls) + r'\b', text) is not None


def _class_styled(text: str, cls: str) -> bool:
    return re.search(r"\." + re.escape(cls) + r"\s*[{,:>+~]", text) is not None


def pass_orphans(text: str, notes: list, unwrap: bool = True) -> str:
    targets = ("qa-ref-text", "qa-list-item-plain")
    needed = [c for c in targets if _class_used(text, c) and not _class_styled(text, c)]
    if ORPHAN_MARK in text:
        needed = []  # 이미 주입됨 (idempotent)
    if needed:
        # `.qa-list-item` 를 정의한 <style> 블록의 끝에 붙인다. 없으면 마지막 </style>.
        anchor = text.find(".qa-list-item")
        end = text.find("</style>", anchor) if anchor >= 0 else -1
        if end < 0:
            end = text.rfind("</style>")
        if end < 0:
            notes.append(("orphan-skip", "no <style> block", None))
        else:
            text = text[:end] + ORPHAN_CSS + text[end:]
            notes.append(("orphan-css", ", ".join(needed), len(ORPHAN_CSS)))

    if unwrap:
        n = len(TUPLE_RE.findall(text))
        if n:
            text = TUPLE_RE.sub(
                lambda m: m.group(1)
                + "<strong>"
                + m.group("label")
                + "</strong>"
                + m.group("body")
                + m.group(4),
                text,
            )
            notes.append(("tuple-unwrap", "qa-list-item-plain", n))
    return text


# ---------------------------------------------------------------------------
# 드라이버
# ---------------------------------------------------------------------------

TARGET_GLOBS = ("*_output.html", "_build.py")


def targets_for(root: Path, arg: str | None):
    """처리 대상 파일 목록."""
    files: list[Path] = []
    if arg:
        p = (root / arg) if not Path(arg).is_absolute() else Path(arg)
        if p.is_file():
            return [p]
        if not p.is_dir():
            print(f"[err] not found: {p}", file=sys.stderr)
            return []
        dirs = [p]
    else:
        dirs = []
        for base in ("papers", "samples"):
            b = root / base
            if b.is_dir():
                dirs += [d for d in sorted(b.iterdir()) if d.is_dir()]
    for d in dirs:
        for g in TARGET_GLOBS:
            files += sorted(d.glob(g))
    return files


# 정본(수정 금지) - samples/ 아래 1~3세대 동결본. 좌측 바가 아직 살아 있어 좌측 직각도 의도.
FROZEN = ("SAFE_output.html", "FrameFusion_output.html", "SGL_output.html")


def process(path: Path, dry: bool, verbose: bool, unwrap: bool) -> bool:
    try:
        src = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        src = path.read_text(encoding="cp949")
    if path.parent.name == "samples" and path.name in FROZEN:
        if verbose:
            print(f"[skip] frozen canonical: {path}")
        return False

    hits: list = []
    text = pass_radius(src, hits, verbose)
    notes: list = []
    text = pass_orphans(text, notes, unwrap=unwrap)

    fixed = [h for h in hits if h[0] == "fix"]
    kept = [h for h in hits if h[0] == "keep"]
    if not fixed and not notes:
        if verbose and kept:
            for _, sel, val, _n in kept:
                print(f"  [keep] {path.name} {sel} :: {val} (border-left alive)")
        return False

    rel = path
    print(f"[{'dry' if dry else 'fix'}] {rel}")
    for _, sel, val, new in fixed:
        print(f"       radius  {sel or '?'} :: {val} -> {new}")
    for kind, what, n in notes:
        print(f"       {kind:<13} {what}" + (f" (x{n})" if n else ""))
    if verbose:
        for _, sel, val, _n in kept:
            print(f"       [keep]  {sel or '?'} :: {val} (border-left alive)")
    if not dry and text != src:
        path.write_text(text, encoding="utf-8", newline="")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("target", nargs="?", help='"papers/N. name" 또는 파일 경로')
    ap.add_argument("--all", action="store_true", help="papers/ + samples/ 전체")
    ap.add_argument("--root", default=None, help="저장소 루트 (기본: 이 파일의 상위)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--no-unwrap", action="store_true", help="튜플 repr 펴기 생략")
    a = ap.parse_args(argv)
    if not a.all and not a.target:
        ap.error("--all 또는 대상 하나를 지정하라")

    root = Path(a.root) if a.root else Path(__file__).resolve().parent.parent
    files = targets_for(root, None if a.all else a.target)
    changed = 0
    for f in files:
        if process(f, a.dry_run, a.verbose, not a.no_unwrap):
            changed += 1
    print(f"\n[done] scanned {len(files)} file(s), touched {changed}"
          + (" (dry-run)" if a.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
