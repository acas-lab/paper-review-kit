"""
Generate the inner content of <section id="tab-reading"> for a paper's
[ShortName].html.

USAGE:
  python tools/gen_tab_reading.py <paper_name>            # → papers/<name>/_tab_reading.html
  python tools/gen_tab_reading.py <paper_name> --stdout   # → write to stdout

INPUTS (read from papers/<name>/):
  structured.json
  translations/manual.json
  analysis.json              (callouts, interpretations, beginner_notes, quizzes)
  tabs_data/hotspots.json
  config.json                (asset_layout, wide_assets)

OUTPUT
  Just the body of the tab-reading section — splice into [ShortName].html
  between `<section id="tab-reading" ...>` and its closing `</section>`.

CONVENTIONS (matched to samples/SAFE.html and existing v2 outputs)
  - bracketed numeric citations like [3, 20, 49] stripped from EN display
  - hotspot sentences carry `sent hotspot` classes
  - figures: <figure class="asset-card[ asset-wide]" id="fig_N">
  - tables : <figure class="asset-card[ asset-wide]" id="table_N">
  - empty section → <section class="section section-empty" id="sN">
  - quizzes: <aside class="recall-card"> rendered just before </section>
"""
import argparse
import html
import io
import json
import re
import sys
from pathlib import Path


def strip_citations(text):
    text = re.sub(r"\s*\[[\d\s,\-–]+\]", "", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def esc(s):
    return html.escape(s, quote=False)


def render_sentence(sentence_id, original, translation, hotspot, lang):
    cls = "sent hotspot" if hotspot else "sent"
    text = original if lang == "en" else translation
    if lang == "en":
        text = strip_citations(text)
    return f'<span class="{cls}" data-pair="{sentence_id}">{esc(text)}</span>'


def render_bilingual(paragraph, trans_by_id, hotspot_set):
    en_parts, kr_parts = [], []
    for sent in paragraph["sentences"]:
        sid = sent["sentence_id"]
        kr = trans_by_id.get(sid, {}).get("translation", "")
        is_hot = sid in hotspot_set
        en_parts.append(render_sentence(sid, sent["original"], kr, is_hot, "en"))
        kr_parts.append(render_sentence(sid, sent["original"], kr, is_hot, "kr"))
    en_html = " ".join(en_parts)
    kr_html = " ".join(kr_parts)
    return (
        '  <div class="bilingual">\n'
        f'    <div class="col col-en"><div class="col-label">English</div><p class="english">{en_html}</p></div>\n'
        f'    <div class="col col-kr"><div class="col-label">한국어</div><p class="korean">{kr_html}</p></div>\n'
        '  </div>'
    )


def render_callouts(callouts):
    if not callouts:
        return ""
    parts = []
    for kind, body in callouts:
        parts.append(f'<aside class="callout callout-{kind}"><p>{esc(body)}</p></aside>')
    return f'<div class="callout-stack">{"".join(parts)}</div>'


def render_asset(asset_id, asset_kind, interpretations, beginner_notes, wide_set):
    n = asset_id.split("_")[-1]
    label = f"FIG {n}" if asset_kind == "figure" else f"TABLE {n}"
    src = f"assets/{asset_id}.png"
    wide = " asset-wide" if asset_id in wide_set else ""
    interp = interpretations.get(asset_id, "")
    beginner = beginner_notes.get(asset_id, "")

    interp_html = (
        '    <div class="interpretation">\n'
        '      <h4>해석 — Reviewer 노트</h4>\n'
        f'      <p>{esc(interp)}</p>\n'
        '    </div>'
    ) if interp else ""

    beginner_html = (
        '    <details class="beginner-note">\n'
        '      <summary>처음 보는 사람에게 — 한 번 더 풀어쓰기</summary>\n'
        f'      <div class="beginner-body">{esc(beginner)}</div>\n'
        '    </details>'
    ) if beginner else ""

    figcaption_inner = "\n".join(filter(None, [
        f'    <span class="asset-label">{label}</span>',
        interp_html,
        beginner_html,
    ]))

    return (
        f'<figure class="asset-card{wide}" id="{asset_id}">\n'
        f'  <div class="asset-image-wrap"><img src="{src}" alt="{label}" /></div>\n'
        f'  <figcaption>\n{figcaption_inner}\n  </figcaption>\n'
        f'</figure>'
    )


def render_asset_stack(assets, interpretations, beginner_notes, wide_set):
    if not assets:
        return ""
    rendered = "\n".join(
        render_asset(aid, akind, interpretations, beginner_notes, wide_set)
        for aid, akind in assets
    )
    return f'<div class="asset-stack">\n{rendered}\n</div>'


def render_recall(quizzes):
    if not quizzes:
        return ""
    items = []
    for i, qz in enumerate(quizzes, 1):
        items.append(
            f'  <details class="recall-item"><summary>Q{i}. {esc(qz["q"])}</summary>\n'
            f'    <div class="recall-answer"><p>{esc(qz["a"])}</p></div>\n'
            f'  </details>'
        )
    return (
        '<aside class="recall-card">\n'
        '  <div class="recall-head"><span class="recall-tag">자가 점검</span></div>\n'
        '  <h4>이 섹션을 덮고 답해 보자</h4>\n'
        + "\n".join(items) + "\n"
        + '</aside>'
    )


def render_paragraph(paragraph, trans_by_id, hotspot_set, callouts_by_pid,
                     asset_layout, interpretations, beginner_notes, wide_set):
    pid = paragraph["paragraph_id"]
    parts = [
        f'<article class="paragraph-block" id="{pid}">',
        f'  <span class="pid-tag">{pid}</span>',
        render_bilingual(paragraph, trans_by_id, hotspot_set),
    ]
    callouts = render_callouts(callouts_by_pid.get(pid, []))
    if callouts:
        parts.append(callouts)
    assets = render_asset_stack(asset_layout.get(pid, []), interpretations, beginner_notes, wide_set)
    if assets:
        parts.append(assets)
    parts.append('</article>')
    return "\n".join(parts)


def build_tab_reading(paper_dir):
    struct = json.loads((paper_dir / "structured.json").read_text(encoding="utf-8"))
    trans = json.loads((paper_dir / "translations" / "manual.json").read_text(encoding="utf-8"))
    analysis = json.loads((paper_dir / "analysis.json").read_text(encoding="utf-8"))
    hot = json.loads((paper_dir / "tabs_data" / "hotspots.json").read_text(encoding="utf-8"))
    cfg = json.loads((paper_dir / "config.json").read_text(encoding="utf-8"))

    trans_by_id = {e["sentence_id"]: e for e in trans}
    hotspot_set = {sid for arr in hot.get("hotspots", {}).values() for sid in arr}
    callouts_by_pid = analysis.get("callouts", {})
    asset_layout = cfg.get("asset_layout", {})
    wide_set = set(cfg.get("wide_assets", []))
    interpretations = analysis.get("interpretations", {})
    beginner_notes = analysis.get("beginner_notes", {})
    quizzes_by_sec = analysis.get("quizzes", {})

    chunks = [
        '    <div class="tab-intro">\n'
        '      <h2>원문 ↔ 번역 정렬 뷰</h2>\n'
        '      <p>문장 단위 hover로 원문과 번역이 짝을 이룬다. 도표 아래 해석/초보자 토글, 섹션 끝의 자가 점검 카드가 함께 묶여 있다.</p>\n'
        '    </div>'
    ]

    for sec in struct["sections"]:
        sid = sec["section_id"]
        title = sec["title"]
        if not sec["paragraphs"]:
            chunks.append(
                f'<section class="section section-empty" id="{sid}">\n'
                f'  <div class="section-header"><h2 class="section-title-en">{esc(title)}</h2></div>\n'
                f'  <p class="section-empty-note">이 섹션은 본문 없이 하위 섹션으로 이어진다.</p>\n'
                f'</section>'
            )
            continue
        body = [
            f'<section class="section" id="{sid}">',
            f'  <div class="section-header"><h2 class="section-title-en">{esc(title)}</h2></div>',
        ]
        for p in sec["paragraphs"]:
            body.append(render_paragraph(
                p, trans_by_id, hotspot_set, callouts_by_pid,
                asset_layout, interpretations, beginner_notes, wide_set,
            ))
        recall = render_recall(quizzes_by_sec.get(sid, []))
        if recall:
            body.append(recall)
        body.append('</section>')
        chunks.append("\n".join(body))

    n_para = sum(len(s["paragraphs"]) for s in struct["sections"])
    n_sent = sum(len(p["sentences"]) for s in struct["sections"] for p in s["paragraphs"])
    n_hot = sum(1 for s in struct["sections"] for p in s["paragraphs"]
                for sent in p["sentences"] if sent["sentence_id"] in hotspot_set)
    n_callout = sum(len(v) for v in callouts_by_pid.values())
    n_asset = sum(len(v) for v in asset_layout.values())
    n_recall = sum(len(v) for v in quizzes_by_sec.values())
    stats = (n_para, n_sent, n_hot, n_callout, n_asset, n_recall)
    return "\n".join(chunks), stats


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paper_name", help="paper directory under papers/, e.g. 'sgl'")
    ap.add_argument("--stdout", action="store_true",
                    help="write to stdout instead of papers/<name>/_tab_reading.html")
    args = ap.parse_args()

    paper_dir = Path("papers") / args.paper_name
    if not paper_dir.exists():
        sys.exit(f"papers/{args.paper_name} not found")

    body, (n_para, n_sent, n_hot, n_callout, n_asset, n_recall) = build_tab_reading(paper_dir)

    if args.stdout:
        sys.stdout.write(body)
    else:
        out = paper_dir / "_tab_reading.html"
        out.write_text(body, encoding="utf-8")
        print(f"wrote {out}: {n_para} paragraphs, {n_sent} sentences ({n_hot} hotspots), "
              f"{n_callout} callouts, {n_asset} assets, {n_recall} quiz items")


if __name__ == "__main__":
    main()
