# -*- coding: utf-8 -*-
"""
strip_left_bars.py - 카드/콜아웃/패널 좌측 색상 바(border-left) 일괄 제거.

배경
  v2~v4 를 거치며 거의 모든 블록 컴포넌트에 `border-left:3~5px solid var(--accent)`
  류의 굵은 색 띠가 붙었다. 사용자 지시로 이 띠를 전부 없앤다.
  배경 tint / 1px 경계선 / 라운딩 / 패딩 등 나머지 시각 요소는 유지한다.

판정 규칙
  제거 = 폭 >= 2px 이고 색이 var(--line) / transparent 가 아닌 border-left 계열 선언.
         shorthand(`border-left:`) 뿐 아니라 개별 속성(`border-left-color/-width/-style`)도 포함.
         `.callout{border-left:4px solid}` 처럼 색 없이 폭만 준 base 와, 그 변형이
         `border-left-color:` 로 색만 주는 패턴을 함께 정리한다.
  보존 = var(--line) / transparent 색, 폭 0~1px, `border-left:0 !important`,
         `#ff-toc a.active{border-left-color:...}` (TOC 현재 위치 표시자).

부수 정리 (기본 OFF - `--pad` 로만 켠다)
  바를 보정하려고 붙은 좌우 비대칭 패딩을 오른쪽 값에 맞추는 기능. 차이가 6px 이하면 무시.
  실측 결과 이 저장소에서 좌우 차이가 6px 를 넘는 유일한 규칙은 `.diss-card`
  (`padding:22px 24px 22px 78px`) 인데, 그 78px 는 바 보정이 아니라 절대 배치된
  번호 배지 `.diss-step`(left:22px · width:42px) 자리다. 줄이면 배지와 본문이 겹친다.
  따라서 기본값은 OFF 이고, 다른 저장소에서 진짜 보정 패딩을 만났을 때만 켠다.

성질
  additive 아님(삭제 전용) · idempotent(두 번 돌리면 0바이트 변화) · dry-run 지원.

사용
  python tools/strip_left_bars.py --all
  python tools/strip_left_bars.py --all --root "<킷 루트>"
  python tools/strip_left_bars.py "papers/1. shortname" --dry-run
  python tools/strip_left_bars.py --all --dry-run --verbose
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

# ----------------------------------------------------------------------------
# 판정
# ----------------------------------------------------------------------------

DECL_RE = re.compile(
    r"border-left(?P<sub>-color|-width|-style)?\s*:\s*(?P<val>[^;}]*?)\s*(?=[;}])",
    re.IGNORECASE,
)

KEEP_COLORS = ("var(--line)", "transparent")
_NUM_RE = re.compile(r"^(0|\d+(?:\.\d+)?)\s*(px|rem|em)?\b")


def _width_of(val: str):
    """값 앞머리의 폭 토큰을 px 로 환산. 없으면 None."""
    m = _NUM_RE.match(val)
    if not m:
        return None
    n = float(m.group(1))
    unit = (m.group(2) or "px").lower()
    return n * (16.0 if unit in ("rem", "em") else 1.0)


def should_keep(prop: str, val: str, selector: str) -> bool:
    v = " ".join(val.lower().split())
    if v.startswith("none") or v.startswith("inherit") or v.startswith("initial"):
        return True

    if prop == "border-left-color":
        if any(c in v for c in KEEP_COLORS):
            return True
        # TOC 현재 위치 표시자는 블록 장식이 아니라 내비게이션 어포던스
        if "#ff-toc" in selector:
            return True
        return False

    if prop == "border-left-style":
        return False

    # shorthand 또는 -width
    w = _width_of(v)
    if w is not None and w < 2:
        return True
    if prop == "border-left-width":
        return False
    # shorthand: 색이 중립이면 패널 경계선
    if any(c in v for c in KEEP_COLORS):
        return True
    return False


def selector_of(text: str, pos: int) -> str:
    """pos 를 감싸는 CSS 규칙의 셀렉터(근사)."""
    b = text.rfind("{", 0, pos)
    if b < 0:
        return ""
    start = max(
        text.rfind("}", 0, b),
        text.rfind(";", 0, b),
        text.rfind("\n", 0, b),
        text.rfind('"', 0, b),
        text.rfind("'", 0, b),
    )
    return " ".join(text[start + 1 : b].split())


# ----------------------------------------------------------------------------
# 삭제 구간 계산
# ----------------------------------------------------------------------------

def _cut_span(text: str, s: int, e: int):
    """선언 [s,e) 를 지울 때 실제로 잘라낼 구간. 세미콜론/여백/빈 줄까지 흡수."""
    j = e
    while j < len(text) and text[j] in " \t":
        j += 1
    if j < len(text) and text[j] == ";":
        e = j + 1
        while e < len(text) and text[e] in " \t":
            e += 1
    else:
        # 블록 마지막 선언 - 앞의 세미콜론을 대신 흡수
        i = s
        while i > 0 and text[i - 1] in " \t\r\n":
            i -= 1
        if i > 0 and text[i - 1] == ";":
            s = i - 1

    ls = text.rfind("\n", 0, s) + 1
    if text[ls:s].strip() == "":
        if e >= len(text):
            return ls, e
        if text[e] == "\n":
            return ls, e + 1
        if text[e] == "\r" and e + 1 < len(text) and text[e + 1] == "\n":
            return ls, e + 2
    return s, e


# ----------------------------------------------------------------------------
# 패딩 보정
# ----------------------------------------------------------------------------

PAD_GAP = 6.0  # 이 값 이하의 좌우 차이는 그대로 둔다

_PAD_SHORT_RE = re.compile(r"(?<![-\w])padding\s*:\s*([^;}]+)")
_PAD_LEFT_RE = re.compile(r"(?<![-\w])padding-left\s*:\s*([^;}]+)")
_PAD_RIGHT_RE = re.compile(r"(?<![-\w])padding-right\s*:\s*([^;}]+)")
_MARGIN_LEFT_RE = re.compile(r"(?<![-\w])margin-left\s*:\s*(-[^;}]+)")


def _px(tok: str):
    m = _NUM_RE.match(tok.strip())
    if not m:
        return None
    n = float(m.group(1))
    unit = (m.group(2) or "px").lower()
    return n * (16.0 if unit in ("rem", "em") else 1.0)


def _block_bounds(text: str, pos: int):
    b = text.rfind("{", 0, pos)
    if b < 0:
        return None
    e = text.find("}", pos)
    if e < 0:
        return None
    return b + 1, e


def pad_edit(text: str, block: tuple, selector: str):
    """바 폭만큼 더 준 좌측 패딩을 우측 값에 맞추는 편집. 차이 <= PAD_GAP 이면 None."""
    bs, be = block
    body = text[bs:be]

    m = _PAD_LEFT_RE.search(body)
    if m:
        r = _PAD_RIGHT_RE.search(body)
        left = _px(m.group(1))
        right = _px(r.group(1)) if r else None
        if left is not None and right is not None and left - right > PAD_GAP:
            s = bs + m.start(1)
            e = bs + m.end(1)
            return (s, e, _fmt(right), "pad", selector,
                    f"padding-left {_fmt(left)} -> {_fmt(right)}")
        return None

    m = _PAD_SHORT_RE.search(body)
    if m:
        parts = m.group(1).split()
        if len(parts) == 4:
            vals = [_px(x) for x in parts]
            if None not in vals and vals[3] - vals[1] > PAD_GAP:
                parts[3] = _fmt(vals[1])
                s = bs + m.start(1)
                e = bs + m.end(1)
                return (s, e, " ".join(parts), "pad", selector,
                        f"padding {m.group(1).strip()} -> {' '.join(parts)}")
    return None


def _fmt(v: float) -> str:
    return f"{int(v)}px" if float(v).is_integer() else f"{v}px"


# ----------------------------------------------------------------------------
# 파일 처리
# ----------------------------------------------------------------------------

def process_text(text: str, pad: bool = False):
    """(new_text, removed, padlog) - removed = [(selector, decl_text)]"""
    edits = []
    pad_seen = set()

    for m in DECL_RE.finditer(text):
        prop = ("border-left" + (m.group("sub") or "")).lower()
        val = m.group("val")
        sel = selector_of(text, m.start())
        if should_keep(prop, val, sel):
            continue
        s, e = _cut_span(text, m.start(), m.end())
        edits.append((s, e, "", "decl", sel, f"{prop}: {' '.join(val.split())}"))
        if pad:
            bb = _block_bounds(text, m.start())
            if bb and bb[0] not in pad_seen:
                pad_seen.add(bb[0])
                pe_ = pad_edit(text, bb, sel)
                if pe_:
                    edits.append(pe_)

    removed = [(e[4], e[5]) for e in edits if e[3] == "decl"]
    padlog = [(e[4], e[5]) for e in edits if e[3] == "pad"]

    out = text
    last = len(text) + 1
    for s, e, repl, kind, sel, info in sorted(edits, key=lambda x: -x[0]):
        if e > last:          # 앞선 편집과 겹치면 건너뛴다
            continue
        out = out[:s] + repl + out[e:]
        last = s

    return out, removed, padlog


def process_file(path: Path, dry: bool, pad: bool, verbose: bool):
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp949")
    new, removed, padlog = process_text(text, pad=pad)
    if not removed and not padlog:
        return 0, 0, []
    if not dry:
        if path.suffix == ".py":
            try:
                ast.parse(new)
            except SyntaxError as exc:
                raise SystemExit(f"[FAIL] {path}: 수정 후 ast.parse 실패 - {exc}")
        path.write_text(new, encoding="utf-8", newline="")
    if verbose:
        for sel, decl in removed[:200]:
            print(f"    - {sel or '(?)'} {{ {decl} }}")
        for sel, chg in padlog:
            print(f"    ~ {sel or '(?)'} {{ {chg} }}")
    return len(removed), len(padlog), removed


# ----------------------------------------------------------------------------
# 대상 수집
# ----------------------------------------------------------------------------

def discover(root: Path):
    seen = []
    for pat in ("papers/*/_build.py", "papers/*/*_output.html",
                "samples/cares/_build.py", "samples/cares/*_output.html",
                "tools/*.py"):
        for p in sorted(root.glob(pat)):
            if p.name == Path(__file__).name:
                continue
            if p not in seen:
                seen.append(p)
    return seen


def collect(arg: Path):
    if arg.is_file():
        return [arg]
    out = []
    for pat in ("_build.py", "*_output.html", "*.py", "*.html"):
        for p in sorted(arg.glob(pat)):
            if p not in out and p.name != Path(__file__).name:
                out.append(p)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="좌측 색상 바(border-left) 일괄 제거")
    ap.add_argument("targets", nargs="*", help="논문 폴더 또는 파일")
    ap.add_argument("--all", action="store_true", help="저장소 전체 대상")
    ap.add_argument("--root", default=None, help="저장소 루트 (기본: 이 스크립트의 상위)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pad", action="store_true",
                    help="좌우 비대칭 패딩 정규화 (기본 OFF - 모듈 docstring 참조)")
    ap.add_argument("--verbose", "-v", action="store_true")
    a = ap.parse_args(argv)

    root = Path(a.root).resolve() if a.root else Path(__file__).resolve().parent.parent

    files = []
    if a.all:
        files += discover(root)
    for t in a.targets:
        p = Path(t)
        if not p.is_absolute():
            p = root / t
        files += [f for f in collect(p) if f not in files]
    if not files:
        ap.error("대상이 없다. --all 또는 폴더/파일 인자를 준다.")

    tot_decl = tot_pad = 0
    touched = 0
    selectors = {}
    for f in files:
        n, np_, removed = process_file(f, a.dry_run, a.pad, a.verbose)
        if n or np_:
            touched += 1
            tot_decl += n
            tot_pad += np_
            for sel, _d in removed:
                selectors[sel] = selectors.get(sel, 0) + 1
            print(f"  {'[dry] ' if a.dry_run else ''}{f.relative_to(root) if root in f.parents or f.is_relative_to(root) else f}"
                  f"  선언 {n}건" + (f" · 패딩 {np_}건" if np_ else ""))

    print(f"\n대상 {len(files)}개 중 {touched}개 수정 · 제거 선언 {tot_decl}건 · "
          f"패딩 정규화 {tot_pad}건 · 셀렉터 {len(selectors)}종")
    if a.verbose:
        for sel, c in sorted(selectors.items(), key=lambda x: -x[1])[:60]:
            print(f"    {c:4d}  {sel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
