"""
autocrop_assets.py — content-aware figure/table cropping (no hand-tuned coords).

CRITERIA (why this is robust):
  A figure/table's true extent is defined by its GRAPHIC CONTENT — vector drawing
  paths (plot axes, arrows, table ruling lines) and raster images — NOT by guessed
  pixel rows. Body text contributes no drawings, so it can never inflate the crop.

ALGORITHM (per caption "Figure N." / "Table N."):
  1. Caption bbox + COLUMN BAND from its x-span: full / left / right.
  2. Collect graphic elements (page.get_drawings() rects + get_image_rects()),
     clipped to the page, dropping: full-page backgrounds, header (y<HEADER) /
     footer (y>FOOTER) artifacts, and near-zero-area slivers. Keep those whose
     horizontal span overlaps the caption's band.
  3. Decide the figure SIDE (above/below the caption) = whichever side has graphic
     content adjacent to the caption (figures: caption usually below; tables: vary).
  4. From the caption edge, grow a RUN of graphic elements on that side: add the
     next-nearest element while the vertical gap <= GAP (bridges multi-panel figures
     and stacked table rules); stop at a gap > GAP, another caption, or the margin.
  5. Decide full-width vs single-column from CORE content (substantial elements minus
     background panels — a localized wide rect that *contains* other elements, e.g. a
     pipeline's rounded backdrop, must not vote for full-width). Full only if core
     content covers points just left AND right of the page midline.
  6. PIXEL-TRUE MARGIN PASS (_refine_rect): render the vector rect padded, then per
     edge find the real CONTENT boundary in pixels and leave a uniform MARGIN_PX of
     whitespace. This fixes the "slightly clipped" problem the vector bbox leaves
     (anti-aliasing, glyph ascenders, plot markers, axis labels the drawing bbox
     under-reports) AND guarantees a clean margin on every side. Outward growth is
     bounded (mid-gutter for column figures, page margin for full-width; neighbour
     caption / header-footer gap vertically) so it never crosses into the other
     column's prose or a neighbouring figure.

This captures the WHOLE figure/table (all sub-panels + labels + caption) with a clean
margin, in one shot. Verify with `--verify`; eyeball the PNGs for unusual layouts.

USAGE (library):
  from tools.autocrop_assets import autocrop
  autocrop("rawpaper/Paper.pdf", out_dir="papers/N. name/assets", dpi=200)
USAGE (cli):
  python tools/autocrop_assets.py "rawpaper/Paper.pdf" "papers/1. fastvlm/assets"
  python tools/autocrop_assets.py --verify "papers/1. fastvlm/assets"   # margin check
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

CAP = re.compile(r"^(Figure|Table)\s+(\d+)\s*[:.]", re.I)

# Tunables (PDF points; defaults for 612x792 two-column papers).
HEADER_Y = 56.0      # exclude running header / top rule above this y
FOOTER_Y = 745.0     # exclude footer / page number below this y
TIGHT = 22.0         # gap to fuse raw elements into one tight cluster (a panel / a table)
SMALL_GAP = 26.0     # always bridge clusters this close (within-panel spacing)
GAP = 66.0           # bridge a larger gap ONLY to a substantial panel (see MIN_PANEL_H).
                     # Sized to span the label gap between stacked sub-panels
                     # (e.g. "(a)…"/"(b)…" plots ~53pt apart).
MIN_PANEL_H = 34.0   # a cluster across a >SMALL_GAP gap must be at least this tall to be
                     # treated as another panel — blocks thin stray strokes / text rules
                     # in the body region from extending the crop into prose.
ADJ = 96.0           # max caption->graphics distance to treat a side as "the figure side"
PAD = 7.0            # padding around the final crop
MIN_AREA = 12.0      # drop near-zero-area drawing slivers (pt^2)


def _bands(W):
    """x-ranges for full / left / right columns of a 2-column page."""
    mid = W / 2.0
    return {
        "full": (0.04 * W, 0.96 * W),
        "left": (0.04 * W, mid - 4),
        "right": (mid + 4, 0.96 * W),
    }


def _classify_band(cx0, cx1, W, bands):
    width = cx1 - cx0
    if width > 0.5 * W:
        return bands["full"]
    center = (cx0 + cx1) / 2.0
    return bands["left"] if center < W / 2.0 else bands["right"]


def _decide_band(cap, other_caps, lo, hi, W, bands):
    """Full-width unless another figure shares this vertical region in the OTHER
    column. A wide caption is always full. Otherwise, only confine to a sub-column
    when a competing caption proves the page is split left/right at this height —
    so a full-width diagram with a left-aligned caption (e.g. Voila Fig.4) is not
    sliced in half, while genuine side-by-side figures stay separated."""
    if (cap["x1"] - cap["x0"]) > 0.5 * W:
        return bands["full"]
    cx = (cap["x0"] + cap["x1"]) / 2.0
    my = "left" if cx < W / 2.0 else "right"
    opp = "right" if my == "left" else "left"
    for oc in other_caps:
        if oc is cap:
            continue
        ocx = (oc["x0"] + oc["x1"]) / 2.0
        oc_col = "left" if ocx < W / 2.0 else "right"
        if oc_col == opp and oc["y0"] < hi and oc["y1"] > lo:
            return bands[my]      # opposite-column figure shares this band -> confine
    return bands["full"]


def _overlaps_band(x0, x1, band):
    bx0, bx1 = band
    ov = min(x1, bx1) - max(x0, bx0)
    w = x1 - x0
    if w < 2:                      # vertical line / column separator: in-band iff its x sits inside
        return ov >= -1.0
    return ov > 0.4 * w            # real-width element: >40% inside the band


def _graphic_elements(page, W, H):
    """Drawing-path rects + image rects, clipped & filtered to real content."""
    elems = []
    for g in page.get_drawings():
        r = g["rect"]
        x0, y0 = max(0, r.x0), max(0, r.y0)
        x1, y1 = min(W, r.x1), min(H, r.y1)
        if x1 < x0 or y1 < y0:
            continue  # truly inverted
        w, h = x1 - x0, y1 - y0
        # KEEP zero-thickness lines: booktabs table rules are horizontal strokes
        # (h==0) and column separators are vertical strokes (w==0). Dropping these
        # would erase borderless/stroke-only tables entirely.
        if w < 2 and h < 2:
            continue  # point/dot artifact, not real content
        if w > 0.8 * W and h > 0.9 * H:
            continue  # full-page background
        if y1 < HEADER_Y or y0 > FOOTER_Y:
            continue
        elems.append((x0, y0, x1, y1))
    for info in page.get_images(full=True):
        try:
            for r in page.get_image_rects(info[0]):
                x0, y0 = max(0, r.x0), max(0, r.y0)
                x1, y1 = min(W, r.x1), min(H, r.y1)
                if x1 > x0 and y1 > y0 and y1 >= HEADER_Y and y0 <= FOOTER_Y:
                    elems.append((x0, y0, x1, y1))
        except Exception:
            pass
    return elems


_SECTION_HEAD = re.compile(r"^\d+(\.\d+)*\s*$|^\d+(\.\d+)*\s+[A-Z]|^[A-Z][A-Z][A-Z ]{2,}$")


def _captions(page):
    """Caption bbox from line-level grouping. A caption starts at a "Figure N:" /
    "Table N:" line and extends over following lines ONLY while they are close
    (<=7pt) and are NOT a section header — so a heading like "4.3 MODEL DESIGN"
    sitting right under a caption is never merged into (and never inflates) it."""
    caps = []
    d = page.get_text("dict")
    for blk in d.get("blocks", []):
        lines = blk.get("lines", [])
        i = 0
        while i < len(lines):
            txt = "".join(s["text"] for s in lines[i].get("spans", [])).strip()
            m = CAP.match(txt)
            if not m:
                i += 1
                continue
            bx = lines[i]["bbox"]
            x0, y0, x1, y1 = bx[0], bx[1], bx[2], bx[3]
            full = txt
            j = i + 1
            while j < len(lines):
                nt = "".join(s["text"] for s in lines[j].get("spans", [])).strip()
                nb = lines[j]["bbox"]
                if nb[1] - y1 > 7:
                    break                         # vertical gap -> caption ended
                if _SECTION_HEAD.match(nt):
                    break                         # next block is a section heading
                y1 = nb[3]; x1 = max(x1, nb[2])
                full += " " + nt
                j += 1
            caps.append({
                "kind": m.group(1).lower(), "num": int(m.group(2)),
                "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                "text": full[:70],
            })
            i = j
    return caps


def _cluster(elems):
    """Fuse elements into tight clusters (panels / a table) by TIGHT vertical gap.
    Returns clusters as [y0, y1, x0, x1] sorted by y0."""
    if not elems:
        return []
    es = sorted(elems, key=lambda e: e[1])
    clusters = [list(es[0])]  # [x0,y0,x1,y1] order from elems -> normalize below
    clusters = [[es[0][1], es[0][3], es[0][0], es[0][2]]]
    for x0, y0, x1, y1 in es[1:]:
        c = clusters[-1]
        if y0 - c[1] <= TIGHT:
            c[1] = max(c[1], y1)
            c[0] = min(c[0], y0)
            c[2] = min(c[2], x0)
            c[3] = max(c[3], x1)
        else:
            clusters.append([y0, y1, x0, x1])
    return clusters


def _grow_run(side_elems, anchor_edge, ascending, W):
    """Grow a run of CLUSTERS from the caption edge outward.
    Always bridge gaps <= SMALL_GAP. Bridge a gap in (SMALL_GAP, GAP] only to a
    cluster that is either a substantial PANEL (height >= MIN_PANEL_H) or WIDE
    (>0.25*W) — the latter keeps thin-but-wide TABLE ROW BANDS (rules + short cells,
    height < MIN_PANEL_H) connected, while still rejecting thin narrow strays in prose.
    Returns the chosen clusters as element-style (x0,y0,x1,y1) tuples."""
    clusters = _cluster(side_elems)  # [y0,y1,x0,x1]
    if not clusters:
        return []
    # order clusters from the caption outward
    clusters.sort(key=lambda c: c[0], reverse=not ascending)
    frontier, run, prev_wide = anchor_edge, [], False
    for c in clusters:
        cy0, cy1, cx0, cx1 = c
        gap = (cy0 - frontier) if ascending else (frontier - cy1)
        if gap < 0:  # overlapping the frontier -> definitely same figure
            gap = 0
        wide = (cx1 - cx0) > 0.25 * W
        substantial = (cy1 - cy0) >= MIN_PANEL_H or wide
        if not run:
            within = gap <= GAP  # first cluster: just needs to be on this side / reachable
        elif gap <= SMALL_GAP:
            within = True
        elif gap <= GAP and substantial:
            within = True
        elif gap <= TABLE_GAP and wide and prev_wide:
            within = True       # body of a borderless table between two ruling lines
        else:
            within = False
        if not within:
            break
        run.append((cx0, cy0, cx1, cy1))
        frontier = max(frontier, cy1) if ascending else min(frontier, cy0)
        prev_wide = wide
    return run


def _bbox_for_caption(cap, elems, other_caps, bands, W, H):
    cy0, cy1 = cap["y0"], cap["y1"]

    # 1) This caption OWNS only the vertical region between the nearest captions
    #    whose CAPTION x-range overlaps its own (a full-width caption bounds
    #    sub-column figures; two opposite-column captions don't bound each other).
    #    Band-independent so we can decide the band from this region next.
    bounds_lo, bounds_hi = HEADER_Y, FOOTER_Y
    for oc in other_caps:
        if oc is cap:
            continue
        if min(oc["x1"], cap["x1"]) - max(oc["x0"], cap["x0"]) <= 0:
            continue
        if oc["y1"] <= cy0 and oc["y1"] > bounds_lo:
            bounds_lo = oc["y1"]      # nearest caption above -> floor
        if oc["y0"] >= cy1 and oc["y0"] < bounds_hi:
            bounds_hi = oc["y0"]      # nearest caption below -> ceiling

    # 1b) Decide the column band from the region (full-width unless a competing
    #     opposite-column figure shares this height).
    band = _decide_band(cap, other_caps, bounds_lo, bounds_hi, W, bands)

    # 2) Candidates: graphic elements in this band AND whose CENTER falls inside this
    #    caption's region. Center-membership (not edge-overlap) assigns a tall element
    #    that straddles a caption boundary to the single figure it actually belongs to,
    #    so a neighbour's diagram can't drag this crop into the prose between them.
    in_band = [e for e in elems
               if _overlaps_band(e[0], e[2], band)
               and bounds_lo - 2 <= (e[1] + e[3]) / 2.0 <= bounds_hi + 2]
    above = [e for e in in_band if e[3] <= cy0 + 4]
    below = [e for e in in_band if e[1] >= cy1 - 4]

    def nearest_dist(side, asc):
        if not side:
            return 1e9
        return min((e[1] - cy1) if asc else (cy0 - e[3]) for e in side)

    d_above, d_below = nearest_dist(above, False), nearest_dist(below, True)
    # choose the side whose graphics are adjacent to the caption
    if d_above <= d_below and d_above <= ADJ:
        run = _grow_run(above, cy0, False, W)
    elif d_below <= ADJ:
        run = _grow_run(below, cy1, True, W)
    else:
        run = above if d_above <= d_below else below  # fallback: take what we have

    # Effective horizontal span: full width only if SUBSTANTIAL graphic content
    # (an element wider than 25pt) reaches well into BOTH halves — true full-width
    # figures (Voila Fig.4, FastVLM Fig.2 / Table.6) qualify, while a right-column
    # figure with only a thin gutter stray stays in its column, so the other
    # column's body text never bleeds in. Thin strays (<25pt wide) are ignored.
    ys0 = [cy0] + [e[1] for e in run]
    ys1 = [cy1] + [e[3] for e in run]
    gy0, gy1 = min(ys0), max(ys1)

    mid = W / 2.0
    SUB = 25.0
    # Work from the INDIVIDUAL elements inside the figure's y-span (run holds merged
    # cluster boxes, which would hide the inner boxes inside a background panel).
    fig_el = [e for e in in_band if e[1] < gy1 and e[3] > gy0]
    sub = [e for e in fig_el if (e[2] - e[0]) > SUB]
    # CORE = substantial elements minus BACKGROUND PANELS. A background panel is a wide
    # element that horizontally CONTAINS several others (e.g. the rounded panel behind
    # Voila Fig.3's pipeline). Its bbox bleeds across the gutter and overlaps the
    # adjacent text column, so it must drive neither the band decision nor the crop
    # x-extent — the real content is the boxes/plots it holds.
    def is_bg(e):
        held = sum(1 for o in sub if o is not e and e[0] <= o[0] + 2 and o[2] <= e[2] + 2)
        # localized container (covers ~one column, not the full page) that holds others
        return held >= 2 and 0.28 * W < (e[2] - e[0]) < 0.7 * W
    core = [e for e in sub if not is_bg(e)] or sub

    if not core:
        eff = band
    else:
        # Full-width only if CORE content covers points just left AND right of the page
        # midline (robust for multi-panel figures whose panels straddle the centre,
        # without misfiring on a column figure whose background panel bleeds across the
        # gutter or that has a thin connector poking across).
        def covers(xp):
            return any(e[0] <= xp <= e[2] for e in core)
        spans_left = covers(mid - 16)
        spans_right = covers(mid + 16)
        if spans_left and spans_right:
            eff = bands["full"]            # true full-width (incl. multi-panel) figure
        elif spans_right and not spans_left:
            eff = bands["right"]
        elif spans_left and not spans_right:
            eff = bands["left"]
        else:
            eff = band                     # centred narrow content -> caption-derived band

    # x-extent from CORE (background-panel-free) so the crop anchor lands in the gutter,
    # never inside an adjacent prose column.
    cx_src = core if core else run
    cx_lo = min(e[0] for e in cx_src) if cx_src else cap["x0"]
    cx_hi = max(e[2] for e in cx_src) if cx_src else cap["x1"]
    cap_x0 = min(max(cap["x0"], eff[0]), eff[1])
    cap_x1 = min(max(cap["x1"], eff[0]), eff[1])
    x0 = max(eff[0] - 2, min(cx_lo, cap_x0) - PAD)
    x1 = min(eff[1] + 2, max(cx_hi, cap_x1) + PAD)
    y0 = max(HEADER_Y, max(bounds_lo, gy0) - PAD)
    y1 = min(FOOTER_Y, min(bounds_hi, gy1) + PAD)
    rect = fitz.Rect(x0, y0, x1, y1)
    # Limits the pixel-refinement pass may grow into. Permissive enough to reach the
    # whitespace that gives a clean margin (gutter, header/footer gap), but never into
    # the OTHER column or a neighbouring figure/caption:
    #  - vertical: a real neighbour caption (bounds_lo/hi away from the page margin)
    #    is a hard stop; otherwise allow a little past the conservative header/footer.
    #  - horizontal: sub-column figures may reach the page mid-gutter but not cross it;
    #    full-width figures may reach the page side margins.
    s_top = bounds_lo if bounds_lo > HEADER_Y + 1 else 30.0
    s_bot = bounds_hi if bounds_hi < FOOTER_Y - 1 else (H - 26.0)
    # HORIZONTAL refine bound: a full-width figure may grow into the page side margins;
    # a single-column figure may grow only to the mid-gutter (never across it into the
    # other column's text). The mid-gutter still gives a clean whitespace margin because
    # body text stops short of the page centre.
    if eff is bands["full"]:
        s_x0, s_x1 = 22.0, W - 22.0
    elif eff is bands["right"]:
        s_x0, s_x1 = W * 0.5 - 4.0, W - 16.0
    else:  # left
        s_x0, s_x1 = 16.0, W * 0.5 + 4.0
    safe = (s_x0, s_top, s_x1, s_bot)
    return rect, safe


WHITE = 244        # >= this on all RGB channels counts as background (anti-alias safe)
MARGIN_PX = 6      # clean whitespace margin to leave on every edge
GROW_PT = 32.0     # max a clipped edge may grow outward (points), capped by safe region
TABLE_GAP = 380.0  # max gap to bridge between two WIDE ruling lines (a tall borderless
                   # table body — many rows of text with no rules — between two rules).
                   # Generous because the run is already bounded by neighbour captions;
                   # body text never has wide rules, so this can't run past a table.


def _row_white(s, st, n, y, x0, x1, step):
    base = y * st
    for x in range(x0, x1, step):
        p = base + x * n
        if s[p] < WHITE or s[p + 1] < WHITE or s[p + 2] < WHITE:
            return False
    return True


def _col_white(s, st, n, x, y0, y1, step):
    xn = x * n
    for y in range(y0, y1, step):
        p = y * st + xn
        if s[p] < WHITE or s[p + 1] < WHITE or s[p + 2] < WHITE:
            return False
    return True


def _refine_rect(page, rect, safe, scale):
    """Pixel-true edge refinement (the '1px-margin' idea).

    Render the vector rect padded by GROW_PT (clamped to the safe region), then per
    edge: if content touches the boundary -> grow outward until a fully-white line is
    found (uncovers content the vector bbox under-reported); if the boundary already
    has whitespace -> trim inward to a uniform MARGIN_PX. Result: every real pixel is
    inside the crop AND a thin even margin surrounds it. Bounded by `safe`, so it can
    never spill into a neighbouring figure/caption."""
    sx0, sy0, sx1, sy1 = safe
    cx0 = max(sx0, rect.x0 - GROW_PT)               # padded clip origin (PDF points)
    cy0 = max(sy0, rect.y0 - GROW_PT)
    clip = fitz.Rect(cx0, cy0, min(sx1, rect.x1 + GROW_PT), min(sy1, rect.y1 + GROW_PT))
    px = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip)
    if px.n >= 4:
        px = fitz.Pixmap(fitz.csRGB, px)            # drop alpha
    s, st, n, w, h = px.samples, px.stride, px.n, px.width, px.height
    if w < 3 or h < 3:
        return rect
    # pixmap pixel (0,0) == padded-clip top-left (cx0, cy0). Anchor at the CONTENT
    # boundary (vector rect inset by its PAD), so each scan starts inside known content
    # rather than in the PAD overshoot — which for a caption-above table with body text
    # ~PAD below would otherwise start the bottom scan inside that prose.
    ax0 = max(0, min(w - 1, round((rect.x0 + PAD - cx0) * scale)))
    ay0 = max(0, min(h - 1, round((rect.y0 + PAD - cy0) * scale)))
    ax1 = max(1, min(w, round((rect.x1 - PAD - cx0) * scale)))
    ay1 = max(1, min(h, round((rect.y1 - PAD - cy0) * scale)))
    if ax1 <= ax0:
        ax1 = min(w, ax0 + 1)
    if ay1 <= ay0:
        ay1 = min(h, ay0 + 1)
    step = 2
    xr0, xr1 = max(0, ax0), min(w, ax1)

    # For each edge find the figure's true CONTENT boundary (anchored at the vector
    # edge: if the anchor sits on whitespace, scan inward to the first content; if it
    # sits on content, scan outward to where content ends), then leave MARGIN_PX of
    # whitespace. Outward scans are bounded by the padded canvas (= the safe region),
    # so they stop at the gutter / header gap and never reach a neighbour.
    # TOP content boundary
    y = max(0, min(ay0, h - 1))
    if _row_white(s, st, n, y, xr0, xr1, step):
        while y < h - 1 and _row_white(s, st, n, y, xr0, xr1, step):
            y += 1
        c_top = y
    else:
        while y > 0 and not _row_white(s, st, n, y, xr0, xr1, step):
            y -= 1
        c_top = y + (0 if y == 0 else 1)
    # BOTTOM content boundary
    y = max(0, min(ay1 - 1, h - 1))
    if _row_white(s, st, n, y, xr0, xr1, step):
        while y > 0 and _row_white(s, st, n, y, xr0, xr1, step):
            y -= 1
        c_bot = y + 1
    else:
        while y < h - 1 and not _row_white(s, st, n, y, xr0, xr1, step):
            y += 1
        c_bot = y if y == h - 1 else y
    yr0, yr1 = max(0, c_top), min(h, c_bot)
    # Margin extends only through WHITESPACE, capped at MARGIN_PX — so when adjacent
    # content (e.g. body text just below a table) sits closer than MARGIN_PX, the crop
    # stops at the available gap instead of bleeding into that content.
    top = c_top
    while top > 0 and (c_top - top) < MARGIN_PX and _row_white(s, st, n, top - 1, xr0, xr1, step):
        top -= 1
    bot = c_bot
    while bot < h and (bot - c_bot) < MARGIN_PX and _row_white(s, st, n, bot, xr0, xr1, step):
        bot += 1

    # LEFT content boundary
    x = max(0, min(ax0, w - 1))
    if _col_white(s, st, n, x, yr0, yr1, step):
        while x < w - 1 and _col_white(s, st, n, x, yr0, yr1, step):
            x += 1
        c_left = x
    else:
        while x > 0 and not _col_white(s, st, n, x, yr0, yr1, step):
            x -= 1
        c_left = x + (0 if x == 0 else 1)
    # RIGHT content boundary
    x = max(0, min(ax1 - 1, w - 1))
    if _col_white(s, st, n, x, yr0, yr1, step):
        while x > 0 and _col_white(s, st, n, x, yr0, yr1, step):
            x -= 1
        c_right = x + 1
    else:
        while x < w - 1 and not _col_white(s, st, n, x, yr0, yr1, step):
            x += 1
        c_right = x if x == w - 1 else x
    left = c_left
    while left > 0 and (c_left - left) < MARGIN_PX and _col_white(s, st, n, left - 1, yr0, yr1, step):
        left -= 1
    right = c_right
    while right < w and (right - c_right) < MARGIN_PX and _col_white(s, st, n, right, yr0, yr1, step):
        right += 1

    return fitz.Rect(cx0 + left / scale, cy0 + top / scale,
                     cx0 + right / scale, cy0 + bot / scale)


def autocrop(pdf_path, out_dir, dpi=200, pages=None, name_map=None):
    """Crop every Figure/Table to <out_dir>/(fig|table)_<N>.png. Returns list of dicts."""
    doc = fitz.open(str(pdf_path))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scale = dpi / 72.0
    results = []
    for pno in range(len(doc)):
        if pages and (pno + 1) not in pages:
            continue
        page = doc[pno]
        W, H = page.rect.width, page.rect.height
        bands = _bands(W)
        caps = _captions(page)
        if not caps:
            continue
        elems = _graphic_elements(page, W, H)
        for cap in caps:
            rect, safe = _bbox_for_caption(cap, elems, caps, bands, W, H)
            rect = _refine_rect(page, rect, safe, scale)   # pixel-true edge margins
            stem = ("fig" if cap["kind"] == "figure" else "table") + f"_{cap['num']}"
            if name_map and stem in name_map:
                stem = name_map[stem]
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect)
            dest = out_dir / f"{stem}.png"
            pix.save(str(dest))
            results.append({"stem": stem, "page": pno + 1, "rect": [round(v, 1) for v in rect],
                            "px": f"{pix.width}x{pix.height}", "cap": cap["text"]})
    return results


def edge_clipped(png_path, ring=2, thr=242):
    """Return the clipped edges of a saved crop as a string of T/B/L/R (empty = clean).
    A crop is 'clipped' on an edge if non-background ink touches the outer `ring` px —
    i.e. there is no whitespace margin there. Used to verify the 1px-margin guarantee."""
    px = fitz.Pixmap(str(png_path))
    if px.n >= 4:
        px = fitz.Pixmap(fitz.csRGB, px)
    s, st, n, w, h = px.samples, px.stride, px.n, px.width, px.height

    def ink(x, y):
        o = y * st + x * n
        return any(s[o + c] < thr for c in range(3))
    flags = {
        "T": any(ink(x, y) for y in range(ring) for x in range(0, w, 2)),
        "B": any(ink(x, y) for y in range(h - ring, h) for x in range(0, w, 2)),
        "L": any(ink(x, y) for x in range(ring) for y in range(0, h, 2)),
        "R": any(ink(x, y) for x in range(w - ring, w) for y in range(0, h, 2)),
    }
    return "".join(k for k, v in flags.items() if v)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    # Verify mode: python tools/autocrop_assets.py --verify "papers/N. name/assets"
    if len(sys.argv) >= 3 and sys.argv[1] == "--verify":
        from pathlib import Path as _P
        bad = 0
        for png in sorted(_P(sys.argv[2]).glob("*.png")):
            c = edge_clipped(png)
            print(f"  {png.name:14} clipped: {c or 'none'}")
            bad += bool(c)
        print(f"\n{'OK — all crops have margins' if not bad else str(bad)+' crop(s) clipped'}")
        sys.exit(1 if bad else 0)
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    pg = None
    if "--pages" in sys.argv:
        i = sys.argv.index("--pages")
        pg = {int(x) for x in sys.argv[i + 1].split(",")}
    res = autocrop(sys.argv[1], sys.argv[2], pages=pg)
    for r in res:
        print(f"  {r['stem']:10} p{r['page']} {r['px']:>10}  rect={r['rect']}  | {r['cap']}")
    print(f"\n{len(res)} assets -> {sys.argv[2]}")
