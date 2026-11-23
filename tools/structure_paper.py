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
  Also writes fulltext.txt (raw page text) next to structured.json if it does not exist —
  the source the Stage-2 completeness check (prompts/02 C-4) compares against.
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


_HYPH_KEEP: set = set()   # "a-b" compounds seen un-broken somewhere in the paper (structure() fills it)


def _join_hyphen(m) -> str:
    a, b = m.group(1), m.group(2)
    # keep a real compound hyphen: next part starts uppercase/digit ("ConvNeXT-XXL",
    # "Qwen2-0.5B") or the paper writes the same pair with a hyphen elsewhere
    # ("convolutional-transformer"); otherwise it is a line-break split ("as-sociated").
    head = re.search(r"[A-Za-z0-9]+$", a).group(0)
    tail = re.match(r"[A-Za-z0-9]+", b).group(0)
    if b[:1].isupper() or b[:1].isdigit() or f"{head}-{tail}".lower() in _HYPH_KEEP:
        return f"{a}-{b}"
    return f"{a}{b}"


def _dehyphen(text: str) -> str:
    text = _norm(text)
    text = re.sub(r"(\w+)[­\-]\s*\n\s*(\w+)", _join_hyphen, text)  # hyphen at a line break
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


RUNIN = re.compile(r"^[A-Z][A-Za-z0-9\-]*(?: [A-Za-z0-9&\-]+){0,5}\.$")


def _prose_sents(text: str):
    """Sentences kept for the body. A short run-in paragraph title at the start
    ("Training Setup." / "Evaluation.") is kept as its own sentence — _is_prose alone
    dropped it (fewer than 3 words), losing the label from the body (Stage 2 1:1)."""
    out = []
    for i, s in enumerate(_split_sentences(text)):
        if _is_prose(s) or (i == 0 and RUNIN.match(s)):
            out.append(s)
    return out


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


_AC = None   # autocrop_assets module, loaded once (False = unavailable)


def _asset_boxes(page, W, H):
    """Figure/table rects from the asset-crop tool (caption-anchored, same logic that
    makes assets/*.png). Booktabs tables have only thin rules, so _figure_boxes cannot
    see them and their header row ("Image Input #Visual GQA ...") leaked into the body
    as prose (FastVLM Tab.1-5). A text block lying wholly inside an asset crop is part of
    that asset, not body text (see the guards in _columns)."""
    global _AC
    if _AC is None:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "_autocrop_assets", Path(__file__).with_name("autocrop_assets.py"))
            _AC = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_AC)
        except Exception:
            _AC = False
    if not _AC:
        return []
    ac = _AC
    caps = ac._captions(page)
    if not caps:
        return []
    elems = ac._graphic_elements(page, W, H)
    bands = ac._bands(W)
    out = []
    for cap in caps:
        try:
            r, _safe = ac._bbox_for_caption(cap, elems, caps, bands, W, H)
        except Exception:
            continue
        out.append([r.x0, r.y0, r.x1, r.y1])
    return out


def _columns(page):
    """Return reading-ordered (x-band) text blocks, excluding headers/footers/captions
    and figure-internal labels (text whose centre sits inside a figure box)."""
    W, H = page.rect.width, page.rect.height
    fboxes = _figure_boxes(page, W, H)
    aboxes = _asset_boxes(page, W, H)
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
        # whole block inside an asset crop -> table header / figure text. A header line or
        # multi-sentence prose is kept even then, so a too-wide crop (Rethinking Fig.1
        # spans into the Abstract column) can never delete body text.
        if (any(bx0 - 3 <= x0 and x1 <= bx2 + 3 and by0 - 3 <= y0 and y1 <= by3 + 3
                for bx0, by0, bx2, by3 in aboxes)
                and not _is_header(txt.strip().split("\n")[0])
                and len(re.findall(r"[a-z]{2}[.!?]\s+[A-Z]", txt)) < 2):
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
            # don't end after an abbreviation, an initial ("J. Smith"), or a bare list
            # number ("1. The ...") — but a version/number that closes a sentence
            # ("... in LLaVA-1.5. For", "... v0.2.2. We", "... in Tab. 6. We") IS an end.
            tail = re.split(r"[\s(]", last)[-1].rstrip(".").lower()
            if (tail in ABBR or re.search(r"(?:^|[\s(])[A-Z]\.$", last)
                    or re.fullmatch(r"\(?\d{1,2}\.", last)):
                merged[-1] = prev + " " + p
                continue
        merged.append(p)
    return [s.strip() for s in merged if s.strip()]


def _terminated(raw: str) -> bool:
    """Block ends a sentence (., !, ?, : — optionally followed by a closing quote/bracket)."""
    return bool(re.search(r"[.!?:][\"')\]]*\s*$", _norm(raw).strip()))


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
    _HYPH_KEEP.clear()
    for pg in doc:   # hyphenated compounds written on one line somewhere in the paper
        _HYPH_KEEP.update(m.lower() for m in re.findall(r"[A-Za-z0-9]+-[A-Za-z0-9]+", _norm(pg.get_text())))
    lines = []
    for pno in range(doc.page_count):
        for block in _columns(doc[pno]):
            lines.append(block)
    sections, cur = [], None
    sec_i = para_i = 0
    pending_subtitle = None
    stopped = False
    open_para = None          # (section, paragraph, raw text) of an unterminated paragraph
    for block in lines:
        first = block.strip().split("\n")[0]
        if STOP.match(first):
            stopped = True
            break
        # peel a leading header off the block (handles 'N\nTITLE\npara' ICLR blocks)
        head, block = _peel_header(block)
        if head:
            open_para = None
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
        sents = _prose_sents(text)
        if not sents:
            continue
        # A paragraph that broke at a column/page end (previous block stops without
        # terminal punctuation: "... model fam-" | "ily [80] ...") continues here —
        # same paragraph_id, re-split as one text, instead of a new fragment paragraph.
        if not head and open_para is not None and open_para[0] is cur:
            raw = open_para[2].rstrip() + "\n" + block.lstrip()
            sents2 = _prose_sents(_dehyphen(raw))
            para = open_para[1]
            para["sentences"] = [{"sentence_id": f"{para['paragraph_id']}_s{j+1}", "text": s}
                                 for j, s in enumerate(sents2)]
            open_para = (cur, para, raw) if not _terminated(raw) else None
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
        open_para = (cur, para, block) if not _terminated(block) else None
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
        # fulltext.txt = the comparison source for the Stage-2 completeness check
        # (prompts/02_structuring.md C-4) and captions_en (prompts/11). Written once;
        # a hand-cleaned fulltext.txt (Stage 1) is never overwritten.
        ft = Path(out_json).with_name("fulltext.txt")
        if not ft.exists():
            ft.write_text("\n".join(_norm(pg.get_text()) for pg in doc), encoding="utf-8")
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
