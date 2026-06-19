r"""
Auto-crop figures and tables from OCR'd scan PDFs (1 bitmap per page).

For PDFs whose `page.get_images(full=True)` returns a single full-page bitmap
(no separable figure objects), `page.get_image_bbox()` is useless. This module
implements a 3-pass algorithm using OCR word coordinates plus rendered-pixel
analysis. See rules/parsing_rules.md §4-A for the full spec.

Usage (per-paper script `papers/<name>/_recrop.py`):

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.crop_assets import crop_figures

    PDF = Path("rawpaper/...pdf")
    OUT = Path(__file__).parent / "assets"
    SPECS = [
        # (asset_id, page_1based, caption_regex, orientation)
        ("fig_1",   4, r"FIG\.?\s*1\.\s*Organization", "above"),
        ("table_1", 6, r"TABLE\s*1\b",                 "below"),
        ...
    ]

    if __name__ == "__main__":
        crop_figures(PDF, OUT, SPECS)

For vector PDFs (figures as separate image objects), prefer
`page.get_image_bbox(item)` directly — this module is overkill for that case.
"""
import re
from pathlib import Path
from typing import Iterable, Optional, Tuple

import fitz

# --- algorithm parameters -----------------------------------------------------
DPI_SCALE = 2.0
MARGIN = 36
ROW_STEP = 4
BODY_COV_FRAC = 0.80      # body-paragraph row: word x-coverage >= this fraction
MAX_INTRA_GAP = 60        # ... AND no internal word gap wider than this
N_CONSEC = 3              # consecutive body rows to declare boundary
GUTTER_MIN_W = 10         # internal visual gutter must be >= this wide (pt)
GUTTER_EMPTY_FRAC = 0.93  # column qualifies as empty if >= this fraction white
GUTTER_WHITE_LEVEL = 200  # grayscale threshold for "white"
FIG_SIDE_PAD = 14         # padding into gutter on figure side (preserve axis labels)
GAP_PT = 6
HEADER_BAND_PT = 56       # skip top running-head band
AXIS_LINE_FRAC = 0.45     # row dark fraction to qualify as a horizontal axis
AXIS_ABOVE_FRAC = 0.06    # 5 rows above axis must avg <= this (= clean white gap)
AXIS_SNAP_MIN_WORDS = 20  # snap only if this many OCR words sit between fig_top
                          # and axis_y (= we are removing real wrap text/equations)


# --- helpers ------------------------------------------------------------------
_CAP_WORD_RX = re.compile(r'(?i)^(fig[.,]?|table[.,]?|figure)$')


def _detect_columns(page):
    """Detect column boundaries from the OCR word x-distribution.
    Robust to figures that span the column gutter visually — we look at where
    text words actually live. Returns [(x_min, x_max), ...] per column."""
    page_w = page.rect.width
    page_h = page.rect.height
    words = page.get_text("words")
    body_words = [w for w in words
                  if w[1] > HEADER_BAND_PT and w[3] < page_h - 30
                  and w[0] >= MARGIN and w[2] <= page_w - MARGIN]
    if len(body_words) < 30:
        return [(MARGIN, page_w - MARGIN)]
    BIN = 4
    n_bins = int((page_w - 2 * MARGIN) / BIN) + 1
    bin_count = [0] * n_bins
    for w in body_words:
        x0b = max(0, int((w[0] - MARGIN) / BIN))
        x1b = min(n_bins - 1, int((w[2] - MARGIN) / BIN))
        for i in range(x0b, x1b + 1):
            bin_count[i] += 1
    # Empty-bin runs (text-free vertical strips, ≥ 16pt = 4 bins)
    runs = []
    cur = cur_end = None
    MIN_RUN = 4
    for i, c in enumerate(bin_count):
        if c == 0:
            if cur is None:
                cur = i
            cur_end = i
        else:
            if cur is not None and cur_end - cur + 1 >= MIN_RUN:
                runs.append((cur, cur_end))
            cur = None
    if cur is not None and cur_end - cur + 1 >= MIN_RUN:
        runs.append((cur, cur_end))
    # Internal runs only — leading/trailing empty bins are figure/page padding
    internal = [r for r in runs if r[0] > 1 and r[1] < n_bins - 2]
    if not internal:
        return [(MARGIN, page_w - MARGIN)]
    internal.sort(key=lambda r: r[0])
    cols = []
    prev_end = MARGIN
    for r in internal:
        cols.append((prev_end, MARGIN + r[0] * BIN))
        prev_end = MARGIN + (r[1] + 1) * BIN
    cols.append((prev_end, page_w - MARGIN))
    return cols


def _column_for(cap_bbox, columns):
    """Pick the column whose x-range contains the caption's x-center."""
    cap_xc = (cap_bbox[0] + cap_bbox[2]) / 2
    for c in columns:
        if c[0] - 4 <= cap_xc <= c[1] + 4:
            return c
    # Fallback — closest column
    return min(columns, key=lambda c: abs(cap_xc - (c[0] + c[1]) / 2))


def _find_caption(page, pattern: str):
    """Find a caption matching `pattern` in any block text, then return the
    PRECISE caption bbox by locating the matching 'Fig'/'Table' word and
    walking subsequent words until a vertical gap > 18pt (= paragraph break).

    Why word-level: PyMuPDF block bboxes on OCR'd scans often extend far
    beyond the caption (figure-internal labels and body text below get clustered
    into the same block). Trusting block bbox would give wrong fig_bottom.
    """
    rx = re.compile(pattern, re.IGNORECASE)
    for b in page.get_text("blocks"):
        if not rx.search(b[4]):
            continue
        bx0, by0, bx1, by1 = b[:4]
        words = page.get_text("words")
        in_block = sorted(
            [w for w in words
             if w[0] >= bx0 - 1 and w[1] >= by0 - 1
             and w[2] <= bx1 + 1 and w[3] <= by1 + 1
             and _CAP_WORD_RX.match(w[4])],
            key=lambda w: (w[1], w[0])
        )
        if not in_block:
            return tuple(b[:4])  # fall back to block bbox
        cap_word = in_block[0]
        cap_y0 = cap_word[1]
        following = sorted(
            [w for w in words
             if w[1] >= cap_y0 - 1
             and w[0] >= bx0 - 1 and w[2] <= bx1 + 1
             and w[1] <= by1 + 1],
            key=lambda w: w[1]
        )
        cap_y1 = cap_word[3]
        prev_line_y = cap_y0
        for w in following:
            if w[1] - prev_line_y > 18:  # paragraph break
                break
            cap_y1 = max(cap_y1, w[3])
            prev_line_y = w[1]
        return (cap_word[0], cap_y0, bx1, cap_y1)
    return None


def _all_caption_blocks(page):
    """Return precise caption bboxes for every Fig/Table caption on the page,
    using word-level detection (block bboxes are unreliable on OCR'd scans)."""
    words = page.get_text("words")
    blocks = page.get_text("blocks")
    caps = []
    for w in words:
        if not _CAP_WORD_RX.match(w[4]):
            continue
        # Filter inline body-text references like 'Fig.1.' or 'Fig.4'
        # by requiring the word to start a block (= leftmost in its line)
        # within a containing block.
        for b in blocks:
            if (w[0] >= b[0] - 1 and w[1] >= b[1] - 1
                    and w[2] <= b[2] + 1 and w[3] <= b[3] + 1):
                # Match if this word is the leftmost word on its y-line within block.
                same_line = [ww for ww in words
                             if ww[0] >= b[0] - 1 and ww[2] <= b[2] + 1
                             and abs(ww[1] - w[1]) < 3]
                if same_line and min(ww[0] for ww in same_line) == w[0]:
                    cap_y0 = w[1]
                    in_block = sorted(
                        [ww for ww in words
                         if ww[1] >= cap_y0 - 1
                         and ww[0] >= b[0] - 1 and ww[2] <= b[2] + 1
                         and ww[1] <= b[3] + 1],
                        key=lambda ww: ww[1]
                    )
                    cap_y1 = w[3]
                    prev_line_y = cap_y0
                    for ww in in_block:
                        if ww[1] - prev_line_y > 18:
                            break
                        cap_y1 = max(cap_y1, ww[3])
                        prev_line_y = ww[1]
                    caps.append((w[0], cap_y0, b[2], cap_y1))
                break
    return sorted(caps, key=lambda c: c[1])


def _merge_intervals(intervals, tol=4):
    iv = sorted(intervals)
    merged = []
    for x0, x1 in iv:
        if merged and x0 <= merged[-1][1] + tol:
            merged[-1] = (merged[-1][0], max(merged[-1][1], x1))
        else:
            merged.append((x0, x1))
    return merged


def _is_body_row(words_in_row, body_min_x, body_max_x):
    if not words_in_row:
        return False
    merged = _merge_intervals([(w[0], w[2]) for w in words_in_row])
    cov = sum(b - a for a, b in merged)
    body_w = body_max_x - body_min_x
    if cov < BODY_COV_FRAC * body_w:
        return False
    gaps = [merged[i+1][0] - merged[i][1] for i in range(len(merged) - 1)]
    if gaps and max(gaps) > MAX_INTRA_GAP:
        return False
    return True


# --- pass 1: figure y-range via OCR word density ------------------------------
def _find_fig_top(words, cap_y0, upper_bound, body_min_x, body_max_x):
    consec = 0
    first_y = cap_y0
    y = cap_y0 - GAP_PT
    while y > upper_bound:
        rw = [w for w in words
              if w[1] < y and w[3] > y - ROW_STEP
              and w[0] >= body_min_x - 1 and w[2] <= body_max_x + 1]
        if _is_body_row(rw, body_min_x, body_max_x):
            if consec == 0:
                first_y = y
            consec += 1
            if consec >= N_CONSEC:
                return first_y + 2
        else:
            consec = 0
        y -= ROW_STEP
    return upper_bound


def _find_fig_bottom(words, cap_y1, lower_bound, body_min_x, body_max_x):
    consec = 0
    first_y = cap_y1
    y = cap_y1 + GAP_PT
    while y < lower_bound:
        rw = [w for w in words
              if w[1] < y + ROW_STEP and w[3] > y
              and w[0] >= body_min_x - 1 and w[2] <= body_max_x + 1]
        if _is_body_row(rw, body_min_x, body_max_x):
            if consec == 0:
                first_y = y + ROW_STEP
            consec += 1
            if consec >= N_CONSEC:
                return first_y - 2
        else:
            consec = 0
        y += ROW_STEP
    return lower_bound


# --- pass 2: x-range via visual gutter ----------------------------------------
def _find_visual_gutter(page, fig_top, fig_bottom, body_min_x, body_max_x):
    bbox = fitz.Rect(body_min_x, fig_top, body_max_x, fig_bottom)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0), clip=bbox,
                          alpha=False, colorspace=fitz.csGRAY)
    w, h = pix.width, pix.height
    if w <= 0 or h <= 0:
        return None
    samples = pix.samples

    is_empty = [False] * w
    for x in range(w):
        white = sum(1 for y in range(h) if samples[y * w + x] >= GUTTER_WHITE_LEVEL)
        is_empty[x] = (white / h) >= GUTTER_EMPTY_FRAC

    runs = []
    cur = cur_end = None
    for x, e in enumerate(is_empty):
        if e:
            if cur is None:
                cur = x
            cur_end = x
        else:
            if cur is not None:
                runs.append((cur, cur_end))
            cur = None
    if cur is not None:
        runs.append((cur, cur_end))

    runs = [r for r in runs if r[1] - r[0] >= GUTTER_MIN_W]
    if not runs:
        return None
    internal = [r for r in runs if r[0] > 3 and r[1] < w - 4]
    if internal:
        best = max(internal, key=lambda r: r[1] - r[0])
    else:
        # Margin gutters need to be substantial (2x) before they're trusted as splits.
        margin_runs = [r for r in runs if r[1] - r[0] >= GUTTER_MIN_W * 2]
        if not margin_runs:
            return None
        best = max(margin_runs, key=lambda r: r[1] - r[0])
    return body_min_x + best[0], body_min_x + best[1]


def _find_x_range(page, words, fig_top, fig_bottom, body_min_x, body_max_x):
    band = [w for w in words if w[1] < fig_bottom and w[3] > fig_top]
    if len(band) < 6:
        return body_min_x, body_max_x

    gutter = _find_visual_gutter(page, fig_top, fig_bottom, body_min_x, body_max_x)
    if gutter is None:
        return body_min_x, body_max_x
    g_start, g_end = gutter

    left_wc = sum(1 for w in band if w[2] <= g_start)
    right_wc = sum(1 for w in band if w[0] >= g_end)

    side = None
    if g_start <= body_min_x + 4:
        side = "right"
    elif g_end >= body_max_x - 4:
        side = "left"
    elif left_wc >= 6 and left_wc > right_wc * 3:
        side = "right"
    elif right_wc >= 6 and right_wc > left_wc * 3:
        side = "left"
    if side is None:
        return body_min_x, body_max_x

    if side == "right":
        return max(body_min_x, g_end - FIG_SIDE_PAD), body_max_x
    return body_min_x, min(body_max_x, g_start + FIG_SIDE_PAD)


# --- pass 3: axis-line snap ---------------------------------------------------
def _find_top_axis_line(page, search_top, search_bottom, x_min, x_max):
    if search_bottom - search_top < 20 or x_max - x_min < 60:
        return None
    bbox = fitz.Rect(x_min, search_top, x_max, search_bottom)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0), clip=bbox,
                          alpha=False, colorspace=fitz.csGRAY)
    w, h = pix.width, pix.height
    if w <= 0 or h <= 0:
        return None
    samples = pix.samples
    DARK = 100
    rows_dark = []
    for y in range(h):
        off = y * w
        d = sum(1 for x in range(w) if samples[off + x] < DARK) / w
        rows_dark.append(d)
    for y in range(5, h):
        if rows_dark[y] < AXIS_LINE_FRAC:
            continue
        if sum(rows_dark[y - 5:y]) / 5 <= AXIS_ABOVE_FRAC:
            return search_top + y
    return None


# --- public API ---------------------------------------------------------------
def crop_one(pdf, asset_id: str, page_num: int, pattern: str, orient: str,
             out_dir: Path, wide: bool = False) -> Optional[Tuple[float, float, float, float]]:
    """Crop one figure/table to `out_dir/<asset_id>.png`.
    Returns the chosen bbox or None on failure.
    `orient`: "above" (figure ABOVE caption — FIG. ...) or "below" (table BELOW caption).
    `wide`: True when the figure spans across columns (caption sits in one column
    but the figure body extends past the column gutter)."""
    page = pdf[page_num - 1]
    cap = _find_caption(page, pattern)
    if cap is None:
        print(f"  [warn] {asset_id}: caption not found on p{page_num}")
        return None
    cap_x0, cap_y0, cap_x1, cap_y1 = cap
    page_w, page_h = page.rect.width, page.rect.height
    columns = _detect_columns(page)
    if wide:
        body_min_x, body_max_x = MARGIN, page_w - MARGIN
    else:
        col = _column_for(cap, columns)
        body_min_x, body_max_x = col

    def _x_overlap_significant(a, b, frac=0.3):
        ov = max(0, min(a[2], b[2]) - max(a[0], b[0]))
        return ov > min(a[2] - a[0], b[2] - b[0]) * frac

    other_caps = [b for b in _all_caption_blocks(page)
                  if not (abs(b[0] - cap_x0) < 0.5 and abs(b[1] - cap_y0) < 0.5)
                  and (wide or _x_overlap_significant(b, cap))]
    words = page.get_text("words")

    if orient == "above":
        upper = max([b[3] + GAP_PT for b in other_caps if b[3] < cap_y0 - 4]
                    + [HEADER_BAND_PT])
        fig_top = _find_fig_top(words, cap_y0, upper, body_min_x, body_max_x)
        fig_bottom = cap_y1 + GAP_PT
    else:
        lower = min([b[1] - GAP_PT for b in other_caps if b[1] > cap_y1 + 4]
                    + [page_h - HEADER_BAND_PT])
        fig_top = cap_y0 - GAP_PT
        fig_bottom = _find_fig_bottom(words, cap_y1, lower, body_min_x, body_max_x)

    if wide:
        x_min, x_max = body_min_x, body_max_x
    else:
        x_min, x_max = _find_x_range(page, words, fig_top, fig_bottom,
                                     body_min_x, body_max_x)
    # Caption must remain fully visible regardless of figure-side narrowing.
    x_min = max(body_min_x, min(x_min, cap_x0 - 4))
    x_max = min(body_max_x, max(x_max, cap_x1 + 4))

    # Pass 3 — axis-line snap. Only fires when there is real body-paragraph
    # text between fig_top and the candidate axis (= we are stripping wrap
    # text/equations, not figure labels).
    if orient == "above":
        axis_y = _find_top_axis_line(page, fig_top, cap_y0 - 8, x_min, x_max)
        if axis_y is not None and axis_y > fig_top + 30:
            body_rows = 0
            y = fig_top
            while y < axis_y - 2:
                rw = [w for w in words
                      if w[1] < y + ROW_STEP and w[3] > y]
                if _is_body_row(rw, x_min, x_max):
                    body_rows += 1
                y += ROW_STEP
            if body_rows >= 5:
                fig_top = axis_y - 4

    bbox = fitz.Rect(x_min, fig_top, x_max, fig_bottom)
    if bbox.height < 40 or bbox.width < 40:
        print(f"  [warn] {asset_id}: bbox too small {bbox}")
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    pix = page.get_pixmap(matrix=fitz.Matrix(DPI_SCALE, DPI_SCALE),
                          clip=bbox, alpha=False)
    pix.save(str(out_dir / f"{asset_id}.png"))
    print(f"  {asset_id} p{page_num} {orient}  "
          f"bbox=({bbox.x0:.0f},{bbox.y0:.0f},{bbox.x1:.0f},{bbox.y1:.0f}) "
          f"{pix.width}x{pix.height}")
    return (bbox.x0, bbox.y0, bbox.x1, bbox.y1)


def crop_figures(pdf_path: Path, out_dir: Path, specs: Iterable[tuple]) -> None:
    """Each spec is (asset_id, page, caption_pattern, orientation) — or
    (..., wide:bool) if the figure spans across columns."""
    pdf = fitz.open(pdf_path)
    print(f"=== crop_assets: {pdf_path.name} -> {out_dir} ===")
    for spec in specs:
        if len(spec) == 4:
            crop_one(pdf, *spec, out_dir=out_dir)
        else:
            asset_id, page_num, pattern, orient, wide = spec
            crop_one(pdf, asset_id, page_num, pattern, orient,
                     out_dir=out_dir, wide=wide)
