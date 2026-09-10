# -*- coding: utf-8 -*-
"""fix_hl_and_dash.py - 하이라이트 표시 규약 + em-dash 표기 교정을 한 번에 수행한다.

세 가지 작업을 additive · idempotent 하게 적용한다 (두 번 돌려도 결과가 같다).

  A. 핫스팟 좌측 색 막대 제거
     `.sent.hotspot` 규칙에서 `border-left` 와 그것을 보정하려고 붙은
     `margin-left:-4px` · `padding-left:8px` 를 제거한다. 배경색 하이라이트는 유지.
     `box-decoration-break` 는 건드리지 않는다 - 막대가 사라져도 slice(=CSS 기본값)가
     여러 줄 문장의 배경을 한 줄기로 이어 주므로 clone 으로 되돌릴 이유가 없다.

  B. 사용자 형광펜이 핫스팟을 이긴다
     `.col .sent.hotspot` 은 특이도 (0,3,0), `.sent.user-hl` 은 (0,2,0) 이라
     핫스팟 문장을 클릭해도 색이 바뀌지 않았다. 같은 접두사에 `.user-hl` 을 붙인
     오버라이드 규칙을 base 규칙 **바로 뒤**(= `.pair-active` 규칙 앞)에 넣어
     특이도로 해결한다. `!important` 는 쓰지 않는다.
     `.pair-active` 앞에 두는 이유: 호버 동기 색이 이기는 기존 동작을
     일반 문장과 동일하게 유지하기 위해서다.

  C. em-dash(U+2014) -> hyphen(-)
     화면에 나가는 한국어 prose 만 바꾼다. 논문 저자의 영어 원문은 보존한다.
       보존: structured.json 의 text / translations 의 original·en /
             config.json 의 captions_en / HTML 의 `<div class="col col-en">` 컬럼 /
             HTML 자산 뷰어 데이터의 `"en": "..."`
       치환: 그 밖의 모든 한국어 콘텐츠 JSON · HTML 표시 텍스트 ·
             빌더(_build.py)와 주입 도구(tools/*.py)의 문자열
     주변 공백은 건드리지 않고 문자만 1:1 로 바꾼다.

사용:
    python tools/fix_hl_and_dash.py "papers/30. adaptvision"
    python tools/fix_hl_and_dash.py --all
    python tools/fix_hl_and_dash.py --all --dry-run
    python tools/fix_hl_and_dash.py --tools            # tools/*.py 만
    python tools/fix_hl_and_dash.py --all --only dash  # only: hotspot | dash | both
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EM = "—"
HYPHEN = "-"
USER_HL_BG = "#f5e8b8"          # .sent.user-hl 배경 (restyle_dash_v4 스왑 대상 아님)

# ----------------------------------------------------------------- 공통 유틸

JSTR = r'"(?:[^"\\]|\\.)*"'     # JSON 문자열 리터럴 (JSON 문자열에는 raw 개행이 없다)

# 화면에서 em-dash 로 보이는 모든 표기 (문자 + HTML 엔티티)
RE_EM = re.compile(r"—|&mdash;|&#0*8212;|&#[xX]0*2014;")


def em_count(s):
    return len(RE_EM.findall(s))


def merge_spans(spans):
    spans = sorted(spans)
    out = []
    for a, b in spans:
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def replace_outside(text, spans):
    """protected span 바깥의 em-dash 만 하이픈으로 바꾼다. (바뀐 개수, 새 텍스트)"""
    spans = merge_spans(spans)
    parts, pos, n = [], 0, 0
    for a, b in spans:
        chunk = text[pos:a]
        n += em_count(chunk)
        parts.append(RE_EM.sub(HYPHEN, chunk))
        parts.append(text[a:b])
        pos = b
    tail = text[pos:]
    n += em_count(tail)
    parts.append(RE_EM.sub(HYPHEN, tail))
    return n, "".join(parts)


def balanced_tag_end(s, pos, open_tag="<div", close_tag="</div>"):
    """pos(여는 태그의 `>` 다음)에서 시작해 짝이 맞는 닫는 태그의 끝 인덱스를 돌려준다."""
    depth = 1
    i = pos
    while depth > 0:
        no = s.find(open_tag, i)
        nc = s.find(close_tag, i)
        if nc < 0:
            return len(s)
        if 0 <= no < nc:
            depth += 1
            i = no + len(open_tag)
        else:
            depth -= 1
            i = nc + len(close_tag)
    return i


def balanced_brace_end(s, pos):
    """pos = 여는 `{` 의 인덱스. 짝이 맞는 `}` 다음 인덱스. 문자열 리터럴 인식."""
    depth = 0
    i = pos
    while i < len(s):
        c = s[i]
        if c == '"':
            i += 1
            while i < len(s):
                if s[i] == "\\":
                    i += 2
                    continue
                if s[i] == '"':
                    break
                i += 1
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(s)


# ------------------------------------------------- A/B. 핫스팟 CSS 수술

BAR_PROPS = ("border-left", "margin-left", "padding-left")
_SEL_STOP = ("}", "{", "*/", ">")


def _selector_start(s, idx):
    """idx(= `.sent.hotspot` 위치)에서 왼쪽으로 훑어 셀렉터 시작 위치를 찾는다."""
    best = 0
    for stop in _SEL_STOP:
        p = s.rfind(stop, 0, idx)
        if p >= 0:
            best = max(best, p + len(stop))
    return best


def _strip_bar(decls):
    """선언 블록 문자열에서 막대 관련 선언만 제거한다."""
    kept, removed = [], []
    for d in decls.split(";"):
        prop = d.split(":", 1)[0].strip().lower()
        if not d.strip():
            continue
        if prop in BAR_PROPS:
            removed.append(d.strip())
        else:
            kept.append(d.strip())
    return ";".join(kept), removed


def _override_selector(sel):
    """셀렉터 목록에서 `.sent.hotspot` 을 포함한 부분에만 `.user-hl` 을 덧붙인다."""
    parts = [p.strip() for p in sel.split(",")]
    out = [p + ".user-hl" for p in parts if ".sent.hotspot" in p]
    return ", ".join(out)


def fix_hotspot_css(text, doubled_braces_ok=True):
    """(새 텍스트, 리포트dict). doubled_braces_ok: _build.py 의 `{{ }}` 형태도 처리."""
    rep = {"bar_rules": 0, "removed": [], "override_added": 0, "override_present": 0}
    has_override = ".sent.hotspot.user-hl" in text
    if has_override:
        rep["override_present"] = 1

    out = text
    # 오른쪽에서 왼쪽으로 처리해야 인덱스가 밀리지 않는다.
    hits = [m.start() for m in re.finditer(r"\.sent\.hotspot", out)]
    for idx in reversed(hits):
        # 이미 우리가 넣은 오버라이드 규칙이면 건너뛴다
        if out[idx:idx + 22] == ".sent.hotspot.user-hl":
            continue
        bo = out.find("{", idx)
        if bo < 0:
            continue
        between = out[idx:bo]
        if "}" in between or ";" in between or "\n\n" in between:
            continue                      # 선택자 블록이 아니다
        sel = out[_selector_start(out, idx):bo].strip()
        if not sel or ".sent.hotspot" not in sel:
            continue
        if ".user-hl" in sel:
            continue
        doubled = doubled_braces_ok and out[bo:bo + 2] == "{{"
        open_len = 2 if doubled else 1
        close = "}}" if doubled else "}"
        bc = out.find(close, bo + open_len)
        if bc < 0:
            continue
        inner = out[bo + open_len:bc]
        if "{" in inner or "}" in inner:
            continue                      # 중첩 - 안전하게 포기
        end = bc + len(close)

        new_inner = inner
        if ".pair-active" not in sel:
            new_inner, removed = _strip_bar(inner)
            if removed:
                rep["bar_rules"] += 1
                rep["removed"].extend(removed)

        insert = ""
        if ".pair-active" not in sel and not has_override:
            ov_sel = _override_selector(sel)
            if ov_sel:
                ob = "{{" if doubled else "{"
                cb = "}}" if doubled else "}"
                insert = f"\n{ov_sel}{ob}background:{USER_HL_BG}{cb}"
                rep["override_added"] += 1

        out = out[:bo + open_len] + new_inner + out[bc:end] + insert + out[end:]
    return out, rep


# ------------------------------------------------------- C. em-dash 치환

def protected_spans_html(s):
    spans = []
    for m in re.finditer(r'<div class="col col-en"[^>]*>', s):
        spans.append([m.start(), balanced_tag_end(s, m.end())])
    for m in re.finditer(r'"en"\s*:\s*' + JSTR, s):
        spans.append([m.start(), m.end()])
    return spans


def protected_spans_json(path: Path, s: str):
    name = path.name
    parent = path.parent.name
    keys = []
    if name == "structured.json":
        keys = ["text"]
    elif name == "translated.json":
        keys = ["text", "original", "en"]
    elif parent == "translations":
        keys = ["original", "en"]
    spans = []
    for k in keys:
        for m in re.finditer(r'"' + k + r'"\s*:\s*' + JSTR, s):
            spans.append([m.start(), m.end()])
    if name == "config.json":
        m = re.search(r'"captions_en"\s*:\s*\{', s)
        if m:
            spans.append([m.start(), balanced_brace_end(s, m.end() - 1)])
    return spans


def dash_fix(path: Path, text: str):
    suf = path.suffix.lower()
    if suf == ".html":
        spans = protected_spans_html(text)
    elif suf == ".json":
        spans = protected_spans_json(path, text)
    else:                                 # .py - 전면 치환 (문법상 무해)
        spans = []
    return replace_outside(text, spans)


def count_protected(path: Path, text: str):
    suf = path.suffix.lower()
    if suf == ".html":
        spans = protected_spans_html(text)
    elif suf == ".json":
        spans = protected_spans_json(path, text)
    else:
        return 0
    return sum(em_count(text[a:b]) for a, b in merge_spans(spans))


# --------------------------------------------------------------- 파일 처리

def target_files(folder: Path):
    """한 논문 폴더에서 손댈 파일 목록 (사용자 데이터 study/ 는 제외)."""
    files = []
    for p in sorted(folder.glob("*.json")):
        files.append(p)
    for p in sorted(folder.glob("tabs_data/*.json")):
        files.append(p)
    for p in sorted(folder.glob("translations/*.json")):
        files.append(p)
    bp = folder / "_build.py"
    if bp.exists():
        files.append(bp)
    for p in sorted(folder.glob("*_output.html")):
        files.append(p)
    return files


def process_file(path: Path, do_hotspot=True, do_dash=True, dry=False):
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig" if bom else "utf-8")
    orig = text
    info = {"path": path, "dash": 0, "bar_rules": 0, "override_added": 0,
            "protected_before": count_protected(path, text), "protected_after": 0}

    if do_hotspot and path.suffix.lower() in (".html", ".py"):
        text, rep = fix_hotspot_css(text, doubled_braces_ok=(path.suffix.lower() == ".py"))
        info["bar_rules"] = rep["bar_rules"]
        info["override_added"] = rep["override_added"]

    if do_dash:
        n, text = dash_fix(path, text)
        info["dash"] = n

    info["protected_after"] = count_protected(path, text)
    info["changed"] = text != orig
    info["size_delta"] = len(text.encode("utf-8")) - len(orig.encode("utf-8"))

    if info["changed"] and not dry:
        out = text.encode("utf-8")
        if bom:
            out = b"\xef\xbb\xbf" + out
        path.write_bytes(out)
    return info


def verify_json(path: Path):
    try:
        json.loads(path.read_text(encoding="utf-8-sig"))
        return True, ""
    except Exception as e:                # noqa: BLE001
        return False, str(e)


def verify_html(path: Path):
    from html.parser import HTMLParser
    s = path.read_text(encoding="utf-8")
    problems = []
    if s.count("</body>") != 1:
        problems.append(f"</body> x{s.count('</body>')}")
    if s.count("</html>") != 1:
        problems.append(f"</html> x{s.count('</html>')}")
    # `<script ...>` 를 인용한 주석·문자열은 제외한다 (papers 2 의 FF_JS_BLOCK 주석 등)
    op = len(re.findall(r"(?<![`&])<script\b", s))
    cl = s.count("</script>")
    if op != cl:
        problems.append(f"script {op}/{cl}")
    try:
        HTMLParser(convert_charrefs=True).feed(s)
    except Exception as e:                # noqa: BLE001
        problems.append(f"parse: {e}")
    if re.search(r"\.sent\.hotspot(?![.\w-])[^{}]*\{[^}]*border-left", s):
        problems.append("hotspot border-left 잔존")
    return problems


# ----------------------------------------------------------------- 엔트리

def paper_folders():
    out = []
    for p in sorted((ROOT / "papers").iterdir()):
        if not p.is_dir():
            continue
        m = re.match(r"^(\d+)\.", p.name)
        if not m:
            continue
        n = int(m.group(1))
        if n == 0:
            continue                      # papers/0 은 35편 범위 밖 - 명시 지정 시에만
        out.append((n, p))
    return [p for _, p in sorted(out)]


def main():
    ap = argparse.ArgumentParser(description="핫스팟 막대 제거 + 형광펜 우선 + em-dash 하이픈화")
    ap.add_argument("folders", nargs="*", help='"papers/30. adaptvision" 형태')
    ap.add_argument("--all", action="store_true", help="papers 1~35 전부 + tools/*.py")
    ap.add_argument("--tools", action="store_true", help="tools/*.py 만")
    ap.add_argument("--only", choices=["hotspot", "dash", "both"], default="both")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true",
                    help="파일을 고치지 않고 무결성 검사만 돌린다")
    args = ap.parse_args()

    do_hot = args.only in ("hotspot", "both")
    do_dash = args.only in ("dash", "both")

    files = []
    if args.tools or args.all:
        if do_dash:
            files += [p for p in sorted((ROOT / "tools").glob("*.py"))
                      if p.name != "fix_hl_and_dash.py"]
    folders = paper_folders() if args.all else [Path(f) if Path(f).is_absolute() else ROOT / f
                                                for f in args.folders]
    for f in folders:
        if not f.exists():
            print(f"[FAIL] 폴더 없음: {f}")
            return 2
        files += target_files(f)

    if not files:
        ap.print_help()
        return 1

    if args.verify:
        bad = 0
        for p in files:
            if p.suffix == ".json":
                ok, msg = verify_json(p)
                if not ok:
                    print(f"[FAIL] JSON {p.relative_to(ROOT).as_posix()}: {msg}")
                    bad += 1
            elif p.suffix == ".html":
                probs = verify_html(p)
                if probs:
                    print(f"[FAIL] HTML {p.name}: {'; '.join(probs)}")
                    bad += 1
            elif p.suffix == ".py":
                import ast
                try:
                    ast.parse(p.read_text(encoding="utf-8"))
                except SyntaxError as e:
                    print(f"[FAIL] PY {p.relative_to(ROOT).as_posix()}: {e}")
                    bad += 1
        print(f"검사 파일 {len(files)} · 실패 {bad}")
        return 4 if bad else 0

    tot = {"dash": 0, "bar": 0, "ovr": 0, "files": 0}
    rows = []
    for p in files:
        info = process_file(p, do_hot, do_dash, args.dry_run)
        if info["protected_before"] != info["protected_after"]:
            print(f"[FAIL] 영어 원문 보존 실패: {p} "
                  f"{info['protected_before']} -> {info['protected_after']}")
            return 3
        if info["changed"]:
            tot["files"] += 1
            tot["dash"] += info["dash"]
            tot["bar"] += info["bar_rules"]
            tot["ovr"] += info["override_added"]
            rows.append(info)

    for info in rows:
        rel = info["path"].relative_to(ROOT).as_posix()
        bits = []
        if info["dash"]:
            bits.append(f"dash {info['dash']}")
        if info["bar_rules"]:
            bits.append(f"bar {info['bar_rules']}")
        if info["override_added"]:
            bits.append(f"user-hl +{info['override_added']}")
        if info["protected_before"]:
            bits.append(f"영문보존 {info['protected_before']}")
        print(f"  {rel:64s} {' · '.join(bits)}")

    print(f"\n변경 파일 {tot['files']} · em-dash {tot['dash']} · "
          f"막대 제거 {tot['bar']} 규칙 · user-hl 오버라이드 {tot['ovr']}개"
          + ("  [dry-run]" if args.dry_run else ""))

    if not args.dry_run:
        bad = 0
        for info in rows:
            p = info["path"]
            if p.suffix == ".json":
                ok, msg = verify_json(p)
                if not ok:
                    print(f"[FAIL] JSON 깨짐 {p}: {msg}")
                    bad += 1
            elif p.suffix == ".html":
                probs = verify_html(p)
                if probs:
                    print(f"[FAIL] HTML {p.name}: {'; '.join(probs)}")
                    bad += 1
        if bad:
            return 4
        print("검증 통과 (JSON 파싱 · HTML 무결성 · 핫스팟 border-left 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
