"""
Re-parse a CVPR-style two-column PDF into papers/<name>/structured.json.

USAGE:
  python tools/reparse_pdf.py <paper_name>           # → writes structured.json
  python tools/reparse_pdf.py <paper_name> --dry     # → writes structured.json.new

INPUTS:
  papers/<name>/config.json         (reads metadata.source_pdf)
  papers/<name>/_parse_config.py    (paper-specific section patterns + page range)

OUTPUTS:
  papers/<name>/structured.json     (or structured.json.new with --dry)

DESIGN
  Strategy: PyMuPDF dict-blocks + font-size filtering.
    - body text blocks: majority span size in [9.7, 10.3] pt
    - section headers: lines with max span size >= 10.5 pt
    - figure / table captions (~8.9-9.0 pt): drop
    - figure-internal labels (~7.3 pt): drop
    - page numbers: drop
  Reading order: page → column (left x<page_w*0.45 vs right) → top y.
  Paragraphs inside one block are split on indent (~12pt).
  Fragments (blocks not ending in .!?(N)) are merged with the next block to
  reattach equation continuations and column-break sentences.

SUPPORTING A NEW PAPER
  1. Drop the source PDF into rawpaper/ and reference it from
     papers/<name>/config.json metadata.source_pdf.
  2. Author papers/<name>/_parse_config.py with PAGES_BODY, SECTION_PATTERNS,
     FRONT_MATTER_SENTENCES (see papers/3. sgl/_parse_config.py for an example).
  3. Run this script. Inspect structured.json. Iterate on the patterns until
     section/paragraph/sentence counts look right.

Layouts other than CVPR-style two-column 10pt body may need the BODY_LO/HI and
HEADER_MIN constants tuned, or a new tool entirely.
"""
import argparse
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

import fitz


BODY_LO, BODY_HI = 9.7, 10.3
HEADER_MIN = 10.5  # subsection headers render as 11pt but raw size ~10.96


# ---------- block classification + line helpers ----------

def block_lines(block):
    for line in block["lines"]:
        spans = line["spans"]
        if not spans:
            continue
        sizes = [s["size"] for s in spans]
        text = "".join(s["text"] for s in spans)
        yield max(sizes), text


def classify_block(block):
    """One of: 'body', 'header', 'caption', 'fig_inner', 'pagenum', 'other'."""
    lines = list(block_lines(block))
    if not lines:
        return "other"
    sizes = [sz for sz, _ in lines]
    text_joined = " ".join(t for _, t in lines).strip()

    if re.fullmatch(r"\s*\d{4,6}\s*", text_joined):
        return "pagenum"

    max_size = max(sizes)
    first_size = sizes[0]
    if first_size >= HEADER_MIN:
        return "header"
    if text_joined.lstrip().startswith(("Figure ", "Table ")) and max_size < 9.5:
        return "caption"

    body_count = sum(1 for sz in sizes if BODY_LO <= sz <= BODY_HI)
    if body_count / len(sizes) > 0.5:
        return "body"
    if max_size < 9.5:
        return "fig_inner"
    return "other"


def split_lines_by_indent(lines, block_x0):
    """Split a list of PyMuPDF line dicts into [paragraph_text, ...] using indent."""
    INDENT_THRESHOLD = block_x0 + 5
    paragraphs, current = [], []
    for line in lines:
        spans = line["spans"]
        if not spans:
            continue
        line_x0 = line["bbox"][0]
        line_text = "".join(s["text"] for s in spans)
        if line_x0 > INDENT_THRESHOLD and current:
            paragraphs.append("\n".join(current))
            current = [line_text]
        else:
            current.append(line_text)
    if current:
        paragraphs.append("\n".join(current))
    return paragraphs


def split_body_by_indent(block):
    return split_lines_by_indent(block["lines"], block["bbox"][0])


def reading_order_key(block, page_w):
    bbox = block["bbox"]
    x0, y0, x1, _ = bbox
    if x0 < page_w * 0.45 and x1 > page_w * 0.55:
        col = 0  # full-width
    elif x0 < page_w * 0.45:
        col = 1  # left
    else:
        col = 2  # right
    return (col, y0, x0)


# ---------- text cleanup + sentence splitting ----------

def fix_text(text):
    """Dehyphenate, normalize whitespace."""
    text = text.replace("­", "")          # soft hyphen
    text = text.replace("‐", "-").replace("‑", "-")
    text = re.sub(r"([A-Za-z])-\n([a-z])", r"\1\2", text)  # "to-\nken" → "token"
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    return text


ABBREV = {
    "e.g", "i.e", "et al", "cf", "etc", "Fig", "Eq", "Sec", "Ref",
    "Eqs", "Figs", "Refs", "vs", "approx", "Tab", "Tabs", "App", "No",
}
ABBREV_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(a) for a in ABBREV) + r")\.\s",
    re.IGNORECASE,
)


def split_sentences(text):
    if not text:
        return []
    SENTINEL = "\x00"
    protected = ABBREV_RE.sub(lambda m: m.group(0).replace(".", SENTINEL), text)
    protected = re.sub(r"(\d)\.(\d)", lambda m: m.group(1) + SENTINEL + m.group(2), protected)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"\(])", protected)
    parts = [p.replace(SENTINEL, ".").strip() for p in parts]
    return [p for p in parts if p]


# ---------- paragraph fragment merging ----------

SENT_END = re.compile(r"(?:[.!?]|\(\d+\))\s*$")
EQ_LABEL = re.compile(r"^\(\d+\)\.?$")


def merge_fragments(paras):
    """Glue paragraphs that don't end with sentence-final punctuation onto the next."""
    if not paras:
        return paras
    # Pass 1: lone "(N)" labels fold into previous
    step1 = []
    for p in paras:
        txt = p.get("raw", "").strip()
        if EQ_LABEL.match(txt) and step1:
            step1[-1]["raw"] = (step1[-1]["raw"].rstrip() + " " + txt).strip()
        else:
            step1.append(p.copy())
    # Pass 2: incomplete trailers merge into the next
    merged = [step1[0]]
    for p in step1[1:]:
        prev = merged[-1]
        if not SENT_END.search(prev.get("raw", "")):
            prev["raw"] = (prev["raw"].rstrip() + " " + p.get("raw", "")).strip()
            prev["page_end"] = p.get("page", prev.get("page"))
        else:
            merged.append(p)
    return merged


# ---------- main parser pipeline ----------

def load_paper_config(paper_dir):
    """Import papers/<name>/_parse_config.py and return its module."""
    cfg_path = paper_dir / "_parse_config.py"
    if not cfg_path.exists():
        sys.exit(f"missing {cfg_path}; see papers/3. sgl/_parse_config.py for the template")
    spec = importlib.util.spec_from_file_location("paper_parse_config", cfg_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_pdf(pdf_path, paper_cfg):
    doc = fitz.open(str(pdf_path))

    items = []
    for pi in paper_cfg.PAGES_BODY:
        page = doc[pi]
        page_w = page.rect.width
        blocks = [b for b in page.get_text("dict")["blocks"] if b.get("type") == 0]
        blocks.sort(key=lambda b: reading_order_key(b, page_w))
        for b in blocks:
            kind = classify_block(b)
            if kind in ("body", "header"):
                items.append((pi + 1, kind, b))

    sections = []

    # Front matter
    sections.append({
        "section_id": "s1",
        "title": "Front Matter",
        "paragraphs": [{
            "page": 1,
            "sentences_raw": list(paper_cfg.FRONT_MATTER_SENTENCES),
        }],
    })

    def normalize_header(line):
        line = line.strip()
        for pat, canon in paper_cfg.SECTION_PATTERNS:
            if re.match(pat, line, re.IGNORECASE):
                return canon
        return None

    cur_section = None
    cur_paragraphs = []
    section_id_counter = 2  # s1 used for Front Matter

    for page_num, kind, block in items:
        if kind == "header":
            lines = block["lines"]
            header_line = "".join(s["text"] for s in lines[0]["spans"]).strip() if lines else ""
            canon = normalize_header(header_line)
            if not canon:
                continue
            if cur_section is not None:
                cur_section["paragraphs"] = cur_paragraphs
                sections.append(cur_section)
            cur_section = {
                "section_id": f"s{section_id_counter}",
                "title": canon,
                "paragraphs": [],
            }
            cur_paragraphs = []
            section_id_counter += 1
            if len(lines) > 1:
                for sp in split_lines_by_indent(lines[1:], block["bbox"][0]):
                    sp_text = fix_text(sp)
                    if sp_text:
                        cur_paragraphs.append({"page": page_num, "raw": sp_text})
        else:  # body
            if cur_section is None:
                continue
            for sp in split_body_by_indent(block):
                text = fix_text(sp)
                if text:
                    cur_paragraphs.append({"page": page_num, "raw": text})

    if cur_section is not None:
        cur_section["paragraphs"] = cur_paragraphs
        sections.append(cur_section)

    # Merge fragments
    for sec in sections:
        sec["paragraphs"] = merge_fragments(sec["paragraphs"])

    # Final structure with IDs + sentence splitting
    final_sections = []
    para_counter = 1
    for sec in sections:
        out_paras = []
        for p in sec["paragraphs"]:
            paragraph_id = f"p{para_counter}"
            page = p.get("page", 1)
            sents = p["sentences_raw"] if "sentences_raw" in p else split_sentences(p["raw"])
            sentences = [
                {"sentence_id": f"{paragraph_id}_s{i+1}", "original": s}
                for i, s in enumerate(sents)
            ]
            out_paras.append({
                "paragraph_id": paragraph_id,
                "page": page,
                "sentences": sentences,
            })
            para_counter += 1
        final_sections.append({
            "section_id": sec["section_id"],
            "title": sec["title"],
            "paragraphs": out_paras,
        })

    return final_sections


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paper_name", help="paper directory under papers/, e.g. 'sgl'")
    ap.add_argument("--dry", action="store_true",
                    help="write to structured.json.new instead of overwriting structured.json")
    args = ap.parse_args()

    paper_dir = Path("papers") / args.paper_name
    if not paper_dir.exists():
        sys.exit(f"papers/{args.paper_name} not found")

    cfg = json.loads((paper_dir / "config.json").read_text(encoding="utf-8"))
    pdf_rel = cfg["metadata"]["source_pdf"]
    pdf_path = Path(pdf_rel)
    if not pdf_path.exists():
        sys.exit(f"PDF not found: {pdf_path}")

    paper_cfg = load_paper_config(paper_dir)
    sections = parse_pdf(pdf_path, paper_cfg)

    output = {
        "source_pdf": str(pdf_path).replace("\\", "/"),
        "chunking_mode": "section_paragraph",
        "paragraph_id_scheme": "p1, p2, p3, ...",
        "sections": sections,
    }

    out_name = "structured.json.new" if args.dry else "structured.json"
    out_path = paper_dir / out_name
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    n_paras = sum(len(s["paragraphs"]) for s in sections)
    n_sents = sum(len(p["sentences"]) for s in sections for p in s["paragraphs"])
    print(f"wrote {out_path}: {len(sections)} sections, {n_paras} paragraphs, {n_sents} sentences")
    for s in sections:
        cnt = sum(len(p["sentences"]) for p in s["paragraphs"])
        print(f"  {s['section_id']:>4}  paras={len(s['paragraphs']):>2}  sents={cnt:>3}  | {s['title']}")


if __name__ == "__main__":
    main()
