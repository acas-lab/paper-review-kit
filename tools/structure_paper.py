"""
structure_paper.py — deterministic full-body structuring: PDF -> structured.json.

Captures the WHOLE paper body (Abstract -> Conclusion), 1:1 at the sentence level
(Stage-2 policy), so the ① 원문/번역 tab covers everything and the result is the same
whether run from CLI or the web dashboard (no per-run LLM judgement in this step).

What it does:
  * column-aware reading order (2-column papers: left column top->bottom, then right)
  * de-hyphenate line-break splits, join intra-paragraph line breaks
  * detect numbered ("3.1 Model Design") and word ("Abstract"/"Introduction") headers
  * stop at References / Acknowledgments / Appendix / Supplementary
  * drop running headers, footers/page numbers, and figure/table caption blocks
  * split paragraphs into sentences, protecting abbreviations, decimals and citations

Output schema = rules/parsing_rules.md §3-1-bis:
  {"sections":[{"section_id","title","paragraphs":[{"paragraph_id",
    "section_subtitle"?, "sentences":[{"sentence_id","text"}]}]}]}

USAGE:
  python tools/structure_paper.py "rawpaper/Paper.pdf" "papers/N. name/structured.json"
  # library: from tools.structure_paper import structure; structure(pdf, out_json)
The output is a COMPLETE first pass — eyeball it and fix any rare split glitch by hand.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ModuleNotFoundError:  # 첫 실행 시 자동 설치 (CLI도 webapp venv와 동일한 경험)
    import subprocess as _sp
    _sp.run([sys.executable, "-m", "pip", "install", "-q", "PyMuPDF>=1.24"], check=True)
    import fitz  # PyMuPDF

HEADER_Y = 52.0
FOOTER_Y = 760.0
CAP = re.compile(r"^\s*(Figure|Table|Fig\.|Algorithm)\s*\d+\s*[:.]", re.I)
STOP = re.compile(r"^\s*(References|Acknowledge?ments?|Appendix|Appendices|"
                  r"Supplementary|Bibliography|Impact Statement|Author Contributions|Broader Impact)\b", re.I)
NUM_HEAD = re.compile(r"^\s*(\d{1,2}(?:\.\d{1,2}){0,3})\.?\s+([A-Za-z][\w].{1,68})$")
WORD_HEAD = re.compile(r"^\s*(Abstract|Introduction|Related Works?|Background|Method(?:s|ology)?|"
                       r"Approach|Experiments?|Results?|Discussion|Conclusions?|Limitations?|"
                       r"Data Collection|Model Design)\s*$", re.I)
# standalone ALL-CAPS heading line, e.g. VOILA's "INTRODUCTION" / "MODEL DESIGN"
ALLCAPS_HEAD = re.compile(r"^\s*[A-Z][A-Z0-9][A-Z0-9 &/:,'\-]{1,42}$")
# abbreviations after which a period does NOT end a sentence
ABBR = {"e.g", "i.e", "et al", "vs", "cf", "fig", "figs", "eq", "eqs", "tab", "sec",
        "no", "approx", "etc", "al", "dr", "mr", "ms", "prof", "inc", "ltd", "resp",
        "w.r.t", "ref", "refs", "app", "st", "nd", "rd", "th"}


LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "ft", "ﬆ": "st",
             "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "—", " ": " "}


def _norm(text: str) -> str:
    for k, v in LIGATURES.items():
        text = text.replace(k, v)
    # some PDF fonts map the multiplication sign '×' to '→'; restore it (academic
    # '3.2×' / '1152×1152' / '85× faster'). Keep spacing readable.
    text = re.sub(r"(\d[\d.]*)\s*→\s*(?=\d)", r"\1x", text)        # 1152→1152 -> 1152x1152
    text = re.sub(r"(\d[\d.]*)\s*→\s*(?=[A-Za-z])", r"\1x ", text)  # 85→faster -> 85x faster
    text = re.sub(r"→\s*(?=\d)", "x", text)                          # →1152 -> x1152
    return text


def _dehyphen(text: str) -> str:
    text = _norm(text)
    text = re.sub(r"(\w)[­\-]\n(\w)", r"\1\2", text)  # word-break hyphen across lines
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_prose(sent: str) -> bool:
    """True if the string looks like a real sentence, not a figure axis label / number row."""
    letters = sum(c.isalpha() for c in sent)
    digits = sum(c.isdigit() for c in sent)
    words = re.findall(r"[A-Za-z]{3,}", sent)
    if letters < 8 or len(words) < 3:
        return False
    if digits > letters:                       # mostly numbers (axis ticks)
        return False
    if re.match(r"^\(?[a-z]\)\s", sent):        # "(a) Qwen2-0.5B" subplot label
        return False
    return True


def _is_header(line: str):
    s = line.strip()
    m = NUM_HEAD.match(s)
    if m and len(s) < 80 and int(m.group(1).split(".")[0]) <= 20:  # reject "100 Seed Sample"
        return f"{m.group(1)} {m.group(2).strip()}"
    if WORD_HEAD.match(s):
        return s
    # ALL-CAPS standalone heading, e.g. "MODEL DESIGN" — require >=4 letters and either
    # a space or length>=6 so acronyms ("VLM", "GPT-4") aren't mistaken for headings.
    if (ALLCAPS_HEAD.match(s) and sum(c.isalpha() for c in s) >= 4
            and (" " in s or len(s) >= 6) and not s.endswith((".", ","))):
        return s.title() if s.isupper() else s
    return None


def _figure_boxes(page, W, H):
    """2D bounding boxes of figure graphic clusters, so text whose CENTRE sits inside a
    figure (its internal labels) can be excluded — without dropping body text in the
    other column at the same height (that text is outside the figure's x-range)."""
    rects = []
    for g in page.get_drawings():
        r = g["rect"]
        w, h = r.x1 - r.x0, r.y1 - r.y0
        if (w < 2 and h < 2) or (w > 0.8 * W and h > 0.9 * H):
            continue
        rects.append([r.x0, r.y0, r.x1, r.y1])
    # merge rects that overlap or nearly touch (<=14pt) into clusters
    boxes = []
    for r in sorted(rects, key=lambda r: (r[1], r[0])):
        merged = False
        for b in boxes:
            if (r[0] <= b[2] + 14 and r[2] >= b[0] - 14
                    and r[1] <= b[3] + 14 and r[3] >= b[1] - 14):
                b[0], b[1] = min(b[0], r[0]), min(b[1], r[1])
                b[2], b[3] = max(b[2], r[2]), max(b[3], r[3])
                merged = True
                break
        if not merged:
            boxes.append(list(r))
    # keep only real figures (sizable area)
    return [b for b in boxes if (b[2] - b[0]) > 50 and (b[3] - b[1]) > 30]


def _columns(page):
    """Return reading-ordered (x-band) text blocks, excluding headers/footers/captions
    and figure-internal labels (text whose centre sits inside a figure box)."""
    W, H = page.rect.width, page.rect.height
    fboxes = _figure_boxes(page, W, H)
    blocks = [b for b in page.get_text("blocks") if (b[4] or "").strip()]
    keep = []
    for x0, y0, x1, y1, txt, *_ in blocks:
        if y1 < HEADER_Y or y0 > FOOTER_Y:
            continue
        if CAP.match(txt):
            continue
        if re.fullmatch(r"\s*\d+\s*", txt):  # page number
            continue
        cxc, cyc = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        # drop blocks whose centre sits inside (or just outside) a figure box — the +18pt
        # margin catches axis labels / subplot captions that hug the plot edge
        if any(bx0 - 18 <= cxc <= bx2 + 18 and by0 - 18 <= cyc <= by3 + 18
               for bx0, by0, bx2, by3 in fboxes):
            continue
        keep.append((x0, y0, x1, y1, txt))
    # two-column if most blocks sit clearly in one half
    mid = W / 2.0
    left = [b for b in keep if (b[0] + b[2]) / 2 < mid]
    right = [b for b in keep if (b[0] + b[2]) / 2 >= mid]
    two_col = len(left) >= 2 and len(right) >= 2 and all((b[2] - b[0]) < 0.6 * W for b in keep)
    if two_col:
        left.sort(key=lambda b: b[1]); right.sort(key=lambda b: b[1])
        ordered = left + right
    else:
        keep.sort(key=lambda b: b[1]); ordered = keep
    return [b[4] for b in ordered]


def _split_sentences(text: str):
    # protect decimals (3.2), citations ([12].) handled by lookahead; protect abbrev periods
    out, buf = [], []
    tokens = re.split(r"(\s+)", text)
    i = 0
    sent = ""
    # simpler: regex split on . ! ? followed by space + (capital/quote/[), guarding abbrev/decimal
    parts = re.split(r"(?<=[.!?])\s+(?=[\"'(\[A-Z])", text)
    merged = []
    for p in parts:
        if merged:
            prev = merged[-1]
            last = prev.rstrip()
            # don't end after an abbreviation, a single capital letter, or a digit-dot (decimal/enum)
            tail = re.split(r"[\s(]", last)[-1].rstrip(".").lower()
            if tail in ABBR or re.search(r"\b[A-Z]\.$", last) or re.search(r"\d\.$", last):
                merged[-1] = prev + " " + p
                continue
        merged.append(p)
    return [s.strip() for s in merged if s.strip()]


def _peel_header(block):
    """If a block STARTS with a section header (possibly 'N' on its own line then the
    TITLE on the next, as in ICLR papers), return (header, remaining_text); else
    (None, block). Handles headers merged with the following paragraph in one block."""
    ls = [l for l in block.split("\n")]
    s0 = ls[0].strip()
    h = _is_header(s0)
    if h:
        return h, "\n".join(ls[1:])
    # "N" / "N.M" alone on line 1, TITLE on line 2
    if len(ls) >= 2 and re.fullmatch(r"\d{1,2}(?:\.\d{1,2}){0,3}", s0) and int(s0.split(".")[0]) <= 20:
        t1 = ls[1].strip()
        if 2 <= len(t1) <= 60 and (t1.isupper() or re.match(r"^[A-Z][A-Za-z]", t1)) and not t1.endswith("."):
            return f"{s0} {t1.title() if t1.isupper() else t1}", "\n".join(ls[2:])
    return None, block


def structure(pdf_path, out_json=None, title=None):
    doc = fitz.open(str(pdf_path))
    lines = []
    for pno in range(doc.page_count):
        for block in _columns(doc[pno]):
            lines.append(block)
    sections, cur = [], None
    sec_i = para_i = 0
    pending_subtitle = None
    stopped = False
    for block in lines:
        first = block.strip().split("\n")[0]
        if STOP.match(first):
            stopped = True
            break
        # peel a leading header off the block (handles 'N\nTITLE\npara' ICLR blocks)
        head, block = _peel_header(block)
        if head:
            if re.match(r"^\d+\.\d", head):       # subsection x.y -> subtitle
                pending_subtitle = head
            else:                                  # top-level / word header -> new section
                sec_i += 1
                cur = {"section_id": f"s{sec_i}", "title": head, "paragraphs": []}
                sections.append(cur)
                pending_subtitle = None
            if not block.strip():
                continue
        if cur is None:  # text before any header (title page etc.)
            sec_i += 1
            cur = {"section_id": f"s{sec_i}", "title": "Body", "paragraphs": []}
            sections.append(cur)
        text = _dehyphen(block)
        if len(text) < 2:
            continue
        sents = [s for s in _split_sentences(text) if _is_prose(s)]
        if not sents:
            continue
        para_i += 1
        pid = f"p{para_i}"
        para = {"paragraph_id": pid}
        if pending_subtitle:
            para["section_subtitle"] = pending_subtitle
            pending_subtitle = None
        para["sentences"] = [{"sentence_id": f"{pid}_s{j+1}", "text": s}
                             for j, s in enumerate(sents)]
        cur["paragraphs"].append(para)
    # drop empty sections
    sections = [s for s in sections if s["paragraphs"]]
    # drop a tiny leading title-page section (title/authors/emails) when real sections follow
    if len(sections) >= 3:
        s0 = sections[0]
        n0 = sum(len(p["sentences"]) for p in s0["paragraphs"])
        if n0 < 6 and not WORD_HEAD.match(s0["title"]) and not re.match(r"^\d", s0["title"]):
            sections.pop(0)
    result = {"sections": sections}
    if title:
        result = {"title": title, **result}
    if out_json:
        Path(out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    sys.stdout.reconfigure(encoding="utf-8")
    out = sys.argv[2] if len(sys.argv) > 2 else None
    r = structure(sys.argv[1], out)
    nsent = sum(len(p["sentences"]) for s in r["sections"] for p in s["paragraphs"])
    print(f"sections={len(r['sections'])} paragraphs="
          f"{sum(len(s['paragraphs']) for s in r['sections'])} sentences={nsent}")
    for s in r["sections"]:
        print(f"  [{s['section_id']}] {s['title'][:50]} ({sum(len(p['sentences']) for p in s['paragraphs'])} sent)")
    if out:
        print(f"-> {out}")
