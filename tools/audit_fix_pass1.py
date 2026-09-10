# -*- coding: utf-8 -*-
"""
audit_fix_pass1.py - 전면 감사 1차 수정 (CSS / JS / 빌더 코드 전용)

빌더(`papers/*/_build.py`)와 산출물 HTML(`papers/*/*_output.html`)을 **함께** 고친다.
산출물만 고치면 다음 빌드에서 되살아난다는 이 저장소의 정본 교훈에 따라, 모든 항목은
빌더 쪽 원천과 산출물 양쪽에 동일하게 적용된다.

작업 항목
  1 hl      사용자 형광펜(user-hl)이 호버(pair-active)를 특이도로 이긴다.
  2 col     .col 사방 테두리 + .col-en / .col-kr 배경 wash 복구 (좌측 바는 되살리지 않는다).
  3 esc     HTML 필드(quizzes[*].a · beginner_notes)의 esc() 제거 - 빌더 raw 삽입 + 산출물 역이스케이프.
  4 eqcard  .eq-card{min-width:0} - grid item 의 min-width:auto 때문에 수식이 페이지를 밀어내는 문제.
  5 lbz     .img-lightbox z-index 400 -> 2000 (규약: 메모 2400 > 라이트박스 2000 > 노트 1700 ...).
  6 esckey  ReferenceError: closeModal is not defined - 죽은 else 분기 제거.
  7 hover   .sent.hotspot.pair-active 가 base 와 동일해 호버 피드백이 없는 문제.
  8 fundknw .fund-label-tag / .fund-body / .knw-label-tag / .knw-body 미정의 보완.

성질: additive · idempotent (두 번 돌리면 0바이트 변화).
사용법:
    python tools/audit_fix_pass1.py --all [--dry-run]
    python tools/audit_fix_pass1.py "papers/9. resnet" [--dry-run]
    python tools/audit_fix_pass1.py --all --only hl,col
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------- 공통 헬퍼

def dbl(css):
    """CSS 조각을 f-string 안에서 쓰이는 이중 중괄호 형태로 바꾼다."""
    return css.replace("{", "{{").replace("}", "}}")


# ---------------------------------------------------------------- 1. 형광펜 우선
#
# 문제: `.col p .sent.hotspot.user-hl`(0,4,1) 과 `.col p .sent.hotspot.pair-active`(0,4,1) 이
#       특이도가 같고 pair-active 가 뒤에 와서 호버가 형광펜을 덮는다. 일반 문장도
#       `.col p .sent.pair-active`(0,3,1) 이 `.sent.user-hl`(0,2,0) 을 순서와 무관하게 이긴다.
# 해법: 형광펜 규칙을 pair-active 조합까지 포함한 선택자 목록으로 바꿔 특이도로 이기게 한다.
#       호버 피드백은 box-shadow 링이 그대로 담당한다.

MARK_HL = "PR-HLP v1"
HL_SELECTORS = (
    ".col .sent.user-hl,"                       # (0,3,0) > .col p .sent.pair-active 는 아래 줄이 담당
    ".col .sent.user-hl.pair-active,"           # (0,4,0) > .col p .sent.pair-active (0,3,1)
    ".col .sent.hotspot.user-hl,"               # (0,4,0) > .col .sent.hotspot (0,3,0)
    ".col .sent.hotspot.user-hl.pair-active"    # (0,5,0) > .col p .sent.hotspot.pair-active (0,4,1)
)
HL_RULE = "/*" + MARK_HL + " - 사용자 형광펜이 호버보다 우선*/" + HL_SELECTORS + "{background:#f5e8b8}"

HL_OLD_PREFIXES = (".col p ", ".col ", "")   # 긴 접두사부터
HL_ANCHOR = (
    ".sent.user-hl{background:#f5e8b8;border-radius:4px;padding:0 2px;"
    "box-decoration-break:clone;-webkit-box-decoration-break:clone}"
)


def op_hl(text, is_builder):
    if MARK_HL in text:
        return text, 0, "already"
    for pre in HL_OLD_PREFIXES:
        base = pre + ".sent.hotspot.user-hl{background:#f5e8b8}"
        for old, new in ((base, HL_RULE), (dbl(base), dbl(HL_RULE))):
            if old in text:
                return text.replace(old, new), text.count(old), "replaced"
    # 핫스팟 전용 규칙이 없는 세대(papers 1·2) - .sent.user-hl 규칙 뒤에 붙인다.
    for anchor, rule in ((HL_ANCHOR, HL_RULE), (dbl(HL_ANCHOR), dbl(HL_RULE))):
        if anchor in text:
            return text.replace(anchor, anchor + "\n" + rule, 1), 1, "appended"
    return text, 0, "no-anchor"


# ---------------------------------------------------------------- 2. EN/KR 컬럼 구분

COL_EN_RE = re.compile(r"(\.col-en\s*)(\{\{|\{)(\s*)(\}\}|\})")
COL_KR_RE = re.compile(r"(\.col-kr\s*)(\{\{|\{)(\s*)(\}\}|\})")
COL_BASE_RE = re.compile(
    r"(\.col\s*(?:\{\{|\{)\s*background:\s*rgba\(255,\s*255,\s*255,\s*0\.\d+\)\s*;"
    r"\s*border-radius:\s*12px\s*;\s*padding:\s*14px 16px)"
)
COL_BORDER = "border:1px solid var(--line)"


def _fill_empty(m, compact, pretty):
    sel, ob, inner, cb = m.group(1), m.group(2), m.group(3), m.group(4)
    if inner != "":            # `.col-en { }` 처럼 사이에 공백이 있던 구세대 포맷
        return sel + ob + " " + pretty + " " + cb
    return sel + ob + compact + cb


def op_col(text, is_builder):
    if ".col-en" not in text:
        return text, 0, "n/a"
    n = 0
    text, k = COL_EN_RE.subn(
        lambda m: _fill_empty(m, "background:var(--accent-soft)", "background: var(--accent-soft);"), text)
    n += k
    text, k = COL_KR_RE.subn(
        lambda m: _fill_empty(m, "background:var(--azure-soft)", "background: var(--azure-soft);"), text)
    n += k

    src = text

    def add_border(m):
        tail = src[m.end():m.end() + 90]
        if COL_BORDER.replace(" ", "") in tail.replace(" ", ""):
            return m.group(1)
        return m.group(1) + ";" + COL_BORDER

    new, k = COL_BASE_RE.subn(add_border, text)
    if new != text:
        text = new
        n += k
    return text, n, "ok" if n else "already"


# ---------------------------------------------------------------- 3. esc() 결함

MARK_ESC = "PR_ESCFIX v1"

# 빌더 소스에 들어 있는 리터럴:  beg_safe = esc(beginner).replace("\n", "<br>")
_BEG_SAFE_SRC = 'beg_safe = esc(beginner).replace("' + chr(92) + 'n", "<br>")'
_BEG_RAW_SRC = 'beg_raw = beginner.replace("' + chr(92) + 'n", "<br>")'
BEG_SAFE_LINE_RE = re.compile(r"([ \t]*)" + re.escape(_BEG_SAFE_SRC) + r"(\r?\n)")

RECALL_BLOCK_RE = re.compile(r'(<div class="recall-answer"><p>)(.*?)(</p></div>)', re.S)
BEG_BLOCK_RE = re.compile(r'(<div class="beginner-body">)(.*?)(</div>)', re.S)


def unesc(s):
    """빌더 esc() 의 정확한 역함수. esc 는 & -> &amp;, < -> &lt;, > -> &gt; 순이므로 역순으로 되돌린다."""
    return s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def op_esc_builder(text, is_builder):
    n = 0
    # (a) quizzes[*].a - CLAUDE.md 가 HTML 필드로 규정한 자리인데 esc() 되어 있다
    if '{esc(q["a"])}' in text:
        n += text.count('{esc(q["a"])}')
        text = text.replace('{esc(q["a"])}', '{q["a"]}')
    # (b) beginner_notes - 같은 이유. 줄바꿈 -> <br> 변환은 유지해야 하므로 이름만 바꿔 raw 로 만든다.
    if "{beg_safe}" in text:
        n += text.count("{beg_safe}")
        text = text.replace("{beg_safe}", "{beg_raw}")
        text, k = BEG_SAFE_LINE_RE.subn(lambda m: m.group(1) + _BEG_RAW_SRC + m.group(2), text, count=1)
    else:
        # 죽은 beg_safe 변수(정본 papers 26 계열은 계산만 하고 {beginner} 를 삽입한다) 정리
        text, k = BEG_SAFE_LINE_RE.subn("", text)
        n += k
    # (c) 자산 학습 가이드에 들어가는 초보자 해설도 같은 HTML 필드다 (papers 15)
    if "beg_html = esc(beginner)" in text:
        n += text.count("beg_html = esc(beginner)")
        text = text.replace("beg_html = esc(beginner)", "beg_html = beginner")
    return text, n, "ok" if n else "n/a"


def op_esc_output(text, fix_recall, fix_beg):
    if MARK_ESC in text:
        return text, 0, "already"
    if not (fix_recall or fix_beg):
        return text, 0, "n/a"
    stat = [0]

    def rep(m):
        body = unesc(m.group(2))
        if body != m.group(2):
            stat[0] += 1
        return m.group(1) + body + m.group(3)

    if fix_recall:
        text = RECALL_BLOCK_RE.sub(rep, text)
    if fix_beg:
        text = BEG_BLOCK_RE.sub(rep, text)
    i = text.rfind("</body>")
    if i >= 0:
        text = text[:i] + "<!-- " + MARK_ESC + " -->\n" + text[i:]
    return text, stat[0], "ok"


# ---------------------------------------------------------------- 4. .eq-card min-width
#
# .eq-grid 는 grid, .eq-card 는 그 item. item 의 min-width 가 auto 라 수식의 min-content
# 폭 아래로 줄지 않아 좁은 화면에서 body 가 가로로 밀린다. min-width:0 을 주면
# .eq-display{overflow-x:auto} 안에서 스크롤된다.

EQCARD_RE = re.compile(r"(\.eq-card\s*(?:\{\{|\{)\s*background:[^{}]{0,400}?)(\}\}|\})")
EQGRID_RE = re.compile(r"(\.eq-grid\s*(?:\{\{|\{)\s*display:\s*grid[^{}]{0,300}?)(\}\}|\})")


def op_eqcard(text, is_builder):
    def add(m):
        g = m.group(1)
        if "min-width" in g:
            return m.group(0)
        sep = "" if g.rstrip().endswith(";") else ";"
        return g + sep + "min-width:0" + m.group(2)

    new, k = EQCARD_RE.subn(add, text)
    if new != text:
        return new, k, "extended"
    if EQCARD_RE.search(text):
        return text, 0, "already"
    # .eq-card 기본 규칙 자체가 없는 세대(papers 1~3) - .eq-grid 규칙 뒤에 독립 규칙을 넣는다.
    if ".eq-card{min-width:0}" in text or ".eq-card{{min-width:0}}" in text:
        return text, 0, "already"
    m = EQGRID_RE.search(text)
    if not m:
        return text, 0, "n/a"
    rule = ".eq-card{min-width:0}"
    if m.group(2) == "}}":
        rule = dbl(rule)
    return text[:m.end()] + "\n" + rule + text[m.end():], 1, "inserted"


# ---------------------------------------------------------------- 5. 라이트박스 z-index

LBZ_OLD = ".img-lightbox{position:fixed;inset:0;z-index:400;"
LBZ_NEW = ".img-lightbox{position:fixed;inset:0;z-index:2000;"


def op_lbz(text, is_builder):
    n = 0
    for old, new in ((LBZ_OLD, LBZ_NEW), (dbl(LBZ_OLD), dbl(LBZ_NEW))):
        if old in text:
            n += text.count(old)
            text = text.replace(old, new)
    return text, n, "ok" if n else "n/a"


# ---------------------------------------------------------------- 6. closeModal 미정의
#
# papers 20·21 의 라이트박스 keydown 핸들러가 정의되지 않은 closeModal() 을 부른다.
# 같은 세대(19·22~35)의 대응 코드는 else 분기 자체가 없고, 학습 가이드 드로어는
# 자기 자신의 keydown 리스너로 이미 ESC 를 처리한다. 따라서 죽은 분기를 제거한다.

CLOSEMODAL_RE = re.compile(
    r"(if \(lightbox && lightbox\.classList\.contains\('open'\)\) lbClose\(\);\r?\n)"
    r"[ \t]*else closeModal\(\);\r?\n"
)


def op_esckey(text, is_builder):
    new, k = CLOSEMODAL_RE.subn(lambda m: m.group(1), text)
    return new, k, "ok" if k else "n/a"


# ---------------------------------------------------------------- 7. 핫스팟 호버 피드백
#
# papers 3·20·21 은 pair-active 배경이 base 와 바이트 동일이라 호버해도 색이 안 변한다.
# 다수파 값으로 통일한다. 빌더는 v3 색으로 쓰고 restyle_dash_v4 가 변환하므로
# #fff4d6 -> #ffe4a1 (변환 후 #f6f1e6 -> #eee3c8) 로 맞춘다.

HOVER_RE = re.compile(r"(\.sent\.hotspot\.pair-active\s*(?:\{\{|\{)\s*background:\s*)(#[0-9a-fA-F]{6})")
HOVER_MAP = {"#f6f1e6": "#eee3c8", "#fff4d6": "#ffe4a1"}


def op_hover(text, is_builder):
    def rep(m):
        v = m.group(2).lower()
        return m.group(1) + HOVER_MAP[v] if v in HOVER_MAP else m.group(0)

    new, k = HOVER_RE.subn(rep, text)
    if new == text:
        return text, 0, "n/a"
    return new, k, "ok"


# ---------------------------------------------------------------- 8. fund / knw 라벨

PILL = ("display:inline-block;background:var(--accent-soft);color:var(--accent);font-weight:700;"
        "font-size:11px;letter-spacing:0.06em;text-transform:uppercase;padding:3px 9px;"
        "border-radius:999px;margin-bottom:6px")
BODY = "font-size:14px;line-height:1.72;color:var(--ink)"

FUND_ANCHOR_RE = re.compile(r"(\.fund-card h4\s*(?:\{\{|\{)[^{}]{0,220}?)(\}\}|\})")
KNW_ANCHOR_RE = re.compile(r"(\.knw-card h3\s*(?:\{\{|\{)[^{}]{0,220}?)(\}\}|\})")


def _has_rule(text, sel):
    return (sel + "{") in text or (sel + "{{") in text


def _insert_after(text, anchor_re, rules):
    m = anchor_re.search(text)
    if not m:
        return text, 0
    blob = "\n" + "\n".join(rules)
    if m.group(2) == "}}":
        blob = dbl(blob)
    return text[:m.end()] + blob + text[m.end():], len(rules)


def op_fundknw(text, is_builder):
    n = 0
    if "fund-label-tag" in text or "fund-body" in text:
        add = []
        if "fund-label-tag" in text and not _has_rule(text, ".fund-label-tag"):
            add.append(".fund-label-tag{" + PILL + "}")
        if "fund-body" in text and not _has_rule(text, ".fund-body"):
            add.append(".fund-body{margin:0;" + BODY + "}")
        if add:
            text, k = _insert_after(text, FUND_ANCHOR_RE, add)
            n += k
    if "knw-label-tag" in text or "knw-body" in text:
        add = []
        if "knw-label-tag" in text and not _has_rule(text, ".knw-label-tag"):
            add.append(".knw-label-tag{" + PILL + "}")
        if "knw-body" in text and not _has_rule(text, ".knw-body"):
            add.append(".knw-body{" + BODY + "}")
        if add:
            text, k = _insert_after(text, KNW_ANCHOR_RE, add)
            n += k
    return text, n, "ok" if n else "n/a"


# ---------------------------------------------------------------- 실행기

ALL_OPS = ["hl", "col", "esc", "eqcard", "lbz", "esckey", "hover", "fundknw"]
OPS = {
    "hl": op_hl, "col": op_col, "esc": op_esc_builder, "eqcard": op_eqcard,
    "lbz": op_lbz, "esckey": op_esckey, "hover": op_hover, "fundknw": op_fundknw,
}


def read(p):
    with open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def process_paper(pdir, only, dry):
    name = os.path.basename(pdir.rstrip("/\\"))
    htmls = sorted(glob.glob(os.path.join(pdir, "*_output.html")))
    builder = os.path.join(pdir, "_build.py")
    log = {}

    # 산출물 역이스케이프 여부는 "빌더가 그 필드를 esc 하고 있었는가" 로 정한다.
    fix_recall = fix_beg = False
    if os.path.exists(builder):
        bt = read(builder)
        fix_recall = '{esc(q["a"])}' in bt
        fix_beg = "{beg_safe}" in bt

    if os.path.exists(builder):
        t0 = read(builder)
        t = t0
        for op in ALL_OPS:
            if only and op not in only:
                continue
            t, k, note = OPS[op](t, True)
            if k:
                log.setdefault("_build.py", []).append("%s:%d(%s)" % (op, k, note))
        if t != t0 and not dry:
            write(builder, t)

    for h in htmls:
        t0 = read(h)
        t = t0
        for op in ALL_OPS:
            if only and op not in only:
                continue
            if op == "esc":
                t, k, note = op_esc_output(t, fix_recall, fix_beg)
            else:
                t, k, note = OPS[op](t, False)
            if k:
                log.setdefault(os.path.basename(h), []).append("%s:%d(%s)" % (op, k, note))
        if t != t0 and not dry:
            write(h, t)

    return name, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()

    only = set(x.strip() for x in a.only.split(",") if x.strip())
    bad = only - set(ALL_OPS)
    if bad:
        print("unknown op:", bad)
        return 2

    if a.all:
        cand = [d for d in glob.glob(os.path.join(ROOT, "papers", "*")) if os.path.isdir(d)]

        def key(p):
            m = re.match(r"(\d+)", os.path.basename(p))
            return int(m.group(1)) if m else 999
        dirs = sorted(cand, key=key)
    else:
        dirs = [d if os.path.isabs(d) else os.path.join(ROOT, d) for d in a.targets]
    if not dirs:
        ap.error("give paper dir(s) or --all")

    total = 0
    for d in dirs:
        name, log = process_paper(d, only, a.dry_run)
        if log:
            for f, items in sorted(log.items()):
                print("%-22s %-26s %s" % (name, f, " ".join(items)))
                total += sum(int(x.split(":")[1].split("(")[0]) for x in items)
        else:
            print("%-22s %-26s -" % (name, ""))
    print("---- total edits:", total, "(dry-run)" if a.dry_run else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
