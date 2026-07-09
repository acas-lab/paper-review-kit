# -*- coding: utf-8 -*-
"""Paper Study 탭 + 도표 뷰어 + 근거 점프 + 노트/하이라이트를 빌더 없는 v4 논문에 직접 주입.

대상: 이미 v4 대시보드지만 _build.py가 없어 paper_study_retrofit.py(빌더 필요)를 못 쓰는
논문 — papers 1~3 (SAFE / FrameFusion / SGL, 대화형·수작업 빌드).

정본 CARES(_build.py Region A + 런타임 블록)의 로직을 이식해 **기존 output HTML에 직접** 조립한다:
  1. REGION_A 렌더링(ev_chips/read_panel/study_thumbs/study_write/study_reveal/study_step 등)을
     그대로 이식해 study.json → Paper Study 패널 HTML 생성
  2. Paper Study 관련 CSS는 정본 CARES output에서 슬라이스해 재사용(디자인 100% 일치)
  3. 런타임 JS는 자립형(self-contained)으로 신규 작성 — CARES 모놀리식 IIFE에 의존하지 않고
     papers 1~3의 DOM 규약(data-pair="pN_sM" · section id="sN" · .paragraph-block id="pN" ·
     .asset-image-wrap[data-asset-id]) 에 배선. 탭 점프는 각 논문의 nav 버튼 .click()으로 위임.
  4. 자산 요소에 id 소급(data-asset-id="fig_1" → id="fig_1") — 썸네일 src 복사·자산 점프용
  5. 메모는 memo_inject.py가 이미 넣은 자립형을 그대로 두고, 노트 내보내기가 같은
     localStorage 네임스페이스(prstudy:{SHORT}:*)를 공유해 연동

사용법: python tools/study_inject.py "papers/N. shortname"
  - tabs_data/study.json 필수 (없으면 셸 탭만 주입)
  - config.json#captions_en / captions, analysis.json#interpretations 재사용
검증: tools/check_study_refs.py · tools/check_html_escape.py

정본 사례: papers 2 (FrameFusion, 2026-07-09 파일럿).
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent


def _cares_output():
    """정본 CARES output HTML. 배포 툴킷은 samples/cares, 모체 작업 폴더는
    papers/26. cares 를 소스로 쓴다 (같은 도구가 양쪽에서 동작)."""
    for cand in (REPO / "samples" / "cares" / "CARES_output.html",
                 REPO / "papers" / "26. cares" / "CARES_output.html"):
        if cand.exists():
            return cand
    raise SystemExit(
        "[FAIL] CARES 정본 output HTML을 찾지 못함 — "
        "samples/cares/CARES_output.html 또는 papers/26. cares/CARES_output.html 필요.")


CARES = _cares_output()


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_json(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


# ------------------------------------------------------------------
# REGION_A 이식 — study.json → Paper Study 패널 HTML
# (정본: papers/26. cares/_build.py 189~374. 숫자식 id 논문에서도 그대로 동작)
# ------------------------------------------------------------------
def render_study_panel(studyd, struct, asset_ids):
    SEC_BY_ID = {s["section_id"]: s for s in struct["sections"]}

    def ev_chips(evs):
        if not evs:
            return ""
        chips = "".join(
            f'<button class="ev-chip" type="button" data-ev="{e["ref"]}">{esc(e["label"])}</button>'
            for e in evs
        )
        return f'<div class="ev-row"><span class="ev-row-label">근거</span>{chips}</div>'

    def read_panel(read_cfg):
        if not read_cfg:
            return ""
        groups = []
        for g in read_cfg:
            sec = SEC_BY_ID.get(g["sec"])
            if not sec:
                continue
            pmap = {p["paragraph_id"]: p for p in sec["paragraphs"]}
            pids = g.get("pids") or [p["paragraph_id"] for p in sec["paragraphs"]]
            chips = []
            for i, pid in enumerate(pids):
                p = pmap.get(pid)
                if not p:
                    continue
                sub = (p.get("section_subtitle") or "").strip().rstrip(".:")
                label = sub if sub else f"¶{i + 1}"
                if len(label) > 26:
                    label = label[:25] + "…"
                chips.append(f'<button class="read-chip" type="button" data-read-pid="{pid}">{esc(label)}</button>')
            if not chips:
                continue
            title = g.get("label") or sec["title"]
            groups.append(
                '<div class="read-group">'
                f'<div class="read-group-head"><span class="read-group-label">{esc(title)}</span>'
                f'<span class="read-progress">0/{len(chips)}</span></div>'
                f'<div class="read-chips">{"".join(chips)}</div>'
                '</div>'
            )
        if not groups:
            return ""
        return ('<div class="read-panel"><span class="read-panel-tag">본문 보기</span>'
                + "".join(groups) + '</div>')

    def study_thumbs(aids):
        figs = "".join(
            f'<figure><img data-thumb-of="{aid}" alt="{aid}" />'
            f'<figcaption>{aid.replace("_", " ").upper()}</figcaption></figure>'
            for aid in aids if aid in asset_ids
        )
        return f'<div class="study-thumbs">{figs}</div>'

    def study_write(skey, placeholder, label="내 답 — 직접 써보기", small=False):
        cls = "study-write study-write-sm" if small else "study-write"
        return (
            '<div class="study-write-wrap">'
            f'<span class="study-write-label">{esc(label)}</span>'
            f'<textarea class="{cls}" data-skey="{skey}" placeholder="{esc(placeholder)}"></textarea>'
            '<div class="study-write-status"><span class="sw-count">0자</span><span class="sw-saved"></span></div>'
            '</div>'
        )

    def study_reveal(skey, min_chars, inner, btn_label="분석 비교하기"):
        return (
            f'<div class="study-reveal" data-skey="{skey}" data-min="{min_chars}">'
            '<div class="study-reveal-bar">'
            f'<button class="study-reveal-btn" type="button" disabled>{btn_label}'
            f'<span class="srb-lock">잠김 — 내 답 {min_chars}자 이상이면 열립니다</span></button>'
            '<button class="study-skip" type="button">그래도 열기</button>'
            '</div>'
            f'<div class="study-claude" hidden>{inner}</div>'
            '</div>'
        )

    def claude_panel(html, evs, tag="Claude의 분석"):
        return (f'<span class="study-claude-tag">{tag}</span>'
                f'<div class="study-claude-body">{html}</div>{ev_chips(evs)}')

    def guide_p(txt):
        return f'<p class="study-guide">{txt}</p>' if txt else ""

    def study_step(no, title, body):
        return (
            f'<article class="study-step" id="study-step-{no}">'
            f'<div class="study-step-head"><span class="study-step-no">{no}</span><h3>{esc(title)}</h3></div>'
            f'{body}</article>'
        )

    p1, p2, p3 = studyd["phase1"], studyd["phase2"], studyd["phase3"]
    scan, rq, gap = p1["scan"], p1["rq"], p1["gap"]
    checks = "".join(
        f'<label><input type="checkbox" class="study-checkbox" data-ckey="p1c{i}" /><span>{c}</span></label>'
        for i, c in enumerate(scan["checklist"])
    )
    step1 = study_step(1, scan["title"],
        study_thumbs(scan["assets"]) + f'<div class="study-check">{checks}</div>' + ev_chips(scan.get("evidence")))
    step2 = study_step(2, rq["title"],
        read_panel(rq.get("read")) + study_write("rq", rq["placeholder"])
        + study_reveal("rq", rq["min_chars"], claude_panel(rq["claude_html"], rq.get("evidence"))))
    gap_writes = "".join(study_write(f["key"], f["placeholder"], label=f["label"], small=True) for f in gap["fields"])
    gap_keys = ",".join(f["key"] for f in gap["fields"])
    step3 = study_step(3, gap["title"],
        read_panel(gap.get("read")) + gap_writes
        + study_reveal(gap_keys, gap["min_chars"], claude_panel(gap["claude_html"], gap.get("evidence"))))

    met, conc = p2["method"], p2["conclusion"]
    qlist = "".join(
        f'<li><span class="ql-q">{q["q"]}</span>'
        f'<button class="view-chip view-chip-sm" type="button" data-read-pid="{q["ref"]}">{esc(q["label"])}</button></li>'
        for q in met["guide_questions"]
    )
    step4 = study_step(4, met["title"],
        guide_p(met.get("prompt")) + read_panel(met.get("read")) + f'<ul class="study-qlist">{qlist}</ul>'
        + study_write("method", met["placeholder"])
        + study_reveal("method", met["min_chars"], claude_panel(met["claude_html"], met.get("evidence"), "Claude의 방법론 평가")))
    step5 = study_step(5, conc["title"],
        guide_p(conc.get("prompt")) + read_panel(conc.get("read")) + study_thumbs(conc["result_assets"])
        + study_write("conclusion", conc["placeholder"])
        + study_reveal("conclusion", conc["min_chars"], claude_panel(conc["claude_html"], conc.get("evidence"), "Claude의 데이터-only 결론")))

    ver, alts = p3["verdict"], p3["alternatives"]
    MATCH_LABEL = {"support": "데이터 일치", "partial": "부분 일치", "beyond": "데이터 너머"}
    claims = "".join(
        f'<li class="match-{c["match"]}"><span class="match-tag">{MATCH_LABEL.get(c["match"], c["match"])}</span>'
        f'<p class="v-claim">{c["claim"]}</p><p class="v-note">{c["note"]}</p>{ev_chips(c.get("evidence"))}</li>'
        for c in ver["author_claims"]
    )
    step6 = study_step(6, ver["title"],
        guide_p(ver.get("guide")) + read_panel(ver.get("read"))
        + '<details class="verdict-details"><summary>결론 대조 열기 — Step 5를 마친 뒤 펼치세요</summary>'
        '<div class="verdict-grid">'
        '<div class="verdict-col v-mine"><h4>내 결론 (Step 5)</h4><div class="v-mine-body" data-mirror="conclusion"></div></div>'
        f'<div class="verdict-col v-claude"><h4>Claude의 데이터-only 결론</h4><div class="v-claude-body">{ver["claude_dataonly_summary"]}</div></div>'
        f'<div class="verdict-col v-author"><h4>저자의 주장 (§Discussion)</h4><ul class="v-claims">{claims}</ul></div>'
        '</div></details>')
    alt_cards = "".join(
        f'<div class="alt-card"><h5>{esc(a["title"])}</h5><p>{a["body"]}</p>{ev_chips(a.get("evidence"))}</div>'
        for a in alts["claude_items"]
    )
    step7 = study_step(7, alts["title"],
        guide_p(alts.get("prompt")) + read_panel(alts.get("read")) + study_write("alt", alts["placeholder"])
        + study_reveal("alt", alts["min_chars"], f'<span class="study-claude-tag">Claude의 대안 가설</span>{alt_cards}'))

    return (
        '<div class="tab-intro"><h2>Paper Study — 3-Phase 비판적 읽기</h2></div>'
        '<div class="study-toolbar">'
        '<div class="study-toolbar-note">메모는 이 브라우저에 자동 저장 · 파일 보관은 내보내기</div>'
        '<div class="study-toolbar-btns">'
        '<button class="study-btn" id="study-export" type="button">내 노트 내보내기</button>'
        '<button class="study-btn" id="study-import" type="button">가져오기</button>'
        '<button class="study-btn study-btn-danger" id="study-clear" type="button">모두 지우기</button>'
        '</div></div>'
        '<section class="phase-band phase-p1"><span class="phase-tag">Phase 1 · Aerial View</span>'
        '<h3>전체 조망: 논문 흐름 파악하기</h3></section>'
        + step1 + step2 + step3 +
        '<section class="phase-band phase-p2"><span class="phase-tag">Phase 2 · Interrogation</span>'
        '<h3>심층분석: 방법론과 데이터 파악하기</h3></section>'
        + step4 + step5 +
        '<section class="phase-band phase-p3"><span class="phase-tag">Phase 3 · Verdict</span>'
        '<h3>대조 분석하기</h3></section>'
        + step6 + step7
    )


def extract_study_css(cares_text):
    """정본 CARES output에서 Paper Study/reader/viewer/notes CSS 슬라이스."""
    start = cares_text.find(".study-drawer{")
    end = cares_text.find(".img-lightbox{")
    if start < 0 or end < 0 or end <= start:
        raise SystemExit("[FAIL] CARES CSS anchors not found")
    return cares_text[start:end].strip()


# 런타임 JS·뷰어 마크업은 별도 파일(study_runtime.py)에서 import — 가독성
from study_runtime import RUNTIME_JS, VIEWER_MARKUP  # noqa: E402


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage: python tools/study_inject.py "papers/N. shortname"')
    folder = Path(sys.argv[1])
    htmls = [h for h in folder.glob("*_output.html")]
    if len(htmls) != 1:
        raise SystemExit(f"[FAIL] expected 1 *_output.html, found {len(htmls)}")
    html = htmls[0]
    short = html.name.replace("_output.html", "")
    text = html.read_text(encoding="utf-8")

    if 'data-tab="tab-study"' in text:
        print(f"[SKIP] {html.name}: tab-study already present")
        return

    struct = load_json(folder / "structured.json")
    config = load_json(folder / "config.json", {})
    analysis = load_json(folder / "analysis.json", {})
    studyd = load_json(folder / "tabs_data" / "study.json")
    if not studyd:
        raise SystemExit(f"[FAIL] {folder}/tabs_data/study.json missing")

    caps_en = config.get("captions_en", {})
    caps = config.get("captions", {})
    interps = analysis.get("interpretations", {})

    # 존재하는 자산 목록 수집 — 두 규약 지원:
    #   FF 계열: <div class="asset-image-wrap" data-asset-id="fig_1">  (id 소급 필요)
    #   SGL 계열: <figure class="asset-card ..." id="fig_1">           (이미 #fig_1 존재)
    asset_ids = set(re.findall(r'<div class="asset-image-wrap" data-asset-id="([^"]+)"', text))
    asset_ids |= set(re.findall(r'<figure class="asset-card[^"]*" id="((?:fig|table)_\d+)"', text))
    # 소급: FF 계열 wrap에만 id 부여(썸네일 #fig_1 img · 자산 점프용). SGL 계열은 이미 id 보유.
    text = re.sub(r'(<div class="asset-image-wrap") (data-asset-id="([^"]+)")',
                  r'\1 id="\3" \2', text)

    # SAFE 계열: HTML에 자산 id·data-asset-id 전무 → asset_layout(dict) + 단락 문서 위치로 순서 도출,
    # 자산 카드(<figure class="asset-card">)에 문서 순서대로 id 부여. (자산은 단락 바로 뒤 배치 관례)
    if not asset_ids:
        al = config.get("asset_layout")
        if isinstance(al, dict):
            def _norm(v):
                return [v[0]] if (v and isinstance(v[0], str)) else [x[0] for x in v]
            para_pos = {pid: text.find(f'id="{pid}"') for pid in al}
            para_pos = {p: i for p, i in para_pos.items() if i >= 0}
            ordered = []
            for pid in sorted(para_pos, key=lambda p: para_pos[p]):
                ordered.extend(_norm(al[pid]))
            cards = list(re.finditer(r'<figure class="asset-card[^"]*"', text))
            if len(cards) == len(ordered) and ordered:
                for fig_m, aid in reversed(list(zip(cards, ordered))):
                    text = text[:fig_m.end()] + f' id="{aid}"' + text[fig_m.end():]
                asset_ids = set(ordered)
                print(f"[info] SAFE-mode: assigned ids to {len(ordered)} asset cards in doc order")
            else:
                print(f"[WARN] SAFE-mode skipped: {len(cards)} cards vs {len(ordered)} layout assets")

    # 도표 뷰어 데이터
    av = {aid: {"label": aid.replace("_", " ").upper(), "en": caps_en.get(aid, ""),
                "kr": caps.get(aid, ""), "interp": interps.get(aid, "")} for aid in sorted(asset_ids)}

    # 1) Paper Study 패널
    panel = render_study_panel(studyd, struct, asset_ids)
    section_html = f'<section id="tab-study" class="tab-pane">{panel}</section>'

    # 2) nav 버튼 (Translation 뒤)
    nav_old = '<button class="tab-btn active" data-tab="tab-reading">Translation</button>'
    if nav_old not in text:
        nav_old2 = re.search(r'<button class="tab-btn active" data-tab="tab-reading">[^<]*</button>', text)
        if not nav_old2:
            raise SystemExit("[FAIL] Translation nav button not found")
        nav_old = nav_old2.group(0)
    nav_new = nav_old + '<button class="tab-btn" data-tab="tab-study">Paper Study</button>'
    text = text.replace(nav_old, nav_new, 1)

    # 3) tab-study 섹션 (tab-dissection 앞)
    diss = re.search(r'<section id="tab-dissection" class="tab-pane[^"]*">', text)
    if not diss:
        raise SystemExit("[FAIL] tab-dissection section not found")
    text = text[:diss.start()] + section_html + text[diss.start():]

    # 4) 서론 goto 버튼 — study.json rq.read 마지막 sec = 서론
    intro_sid = None
    try:
        reads = studyd["phase1"]["rq"].get("read", [])
        if reads:
            intro_sid = reads[-1]["sec"]
    except Exception:
        pass
    if intro_sid:
        m = re.search(rf'<section class="section" id="{re.escape(intro_sid)}"[^>]*>', text)
        if m:
            j = text.find("</section>", m.end())
            if j >= 0:
                goto = ('<div class="study-goto-row">'
                        '<button class="study-goto" type="button">서론 끝 — Paper Study로 돌아가기 ↩</button>'
                        '</div>')
                text = text[:j] + goto + text[j:]

    # 5) CSS 주입 (+ 근거 점프 flash — CARES 원본 flash 클래스는 추출 범위 밖이라 자체 정의)
    css = extract_study_css(CARES.read_text(encoding="utf-8"))
    flash_css = (
        "\n.ev-flash{animation:ev-flash-kf 3.6s ease}"
        "\n@keyframes ev-flash-kf{0%,100%{background:transparent}10%,55%{background:var(--amber-soft)}}"
        "\n.sent.ev-sent-flash{background:#f5e8b8;border-radius:4px;box-decoration-break:clone;-webkit-box-decoration-break:clone}"
    )
    text = text.replace("</style>", "\n/* ==== Paper Study (study_inject.py) ==== */\n" + css + flash_css + "\n</style>", 1)

    # 6) 뷰어 마크업 + 런타임 JS (</body> 직전)
    runtime = RUNTIME_JS.replace("__SHORT__", short).replace("__AV_JSON__", json.dumps(av, ensure_ascii=False))
    text = text.replace("</body>", VIEWER_MARKUP + "\n" + runtime + "\n</body>", 1)

    html.write_text(text, encoding="utf-8")

    # 검증
    chk = html.read_text(encoding="utf-8")
    assert chk.count('data-tab="tab-study"') == 1
    assert chk.count('<section id="tab-study"') == 1
    assert '.study-step{' in chk or '.study-step ' in chk or 'study-step' in chk
    assert 'prstudy' in chk
    n_ev = chk.count('class="ev-chip"')
    n_thumb = chk.count('data-thumb-of')
    print(f"[OK]   {html.name}: Paper Study injected | assets={len(asset_ids)} ev-chips={n_ev} thumbs={n_thumb} intro={intro_sid}")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
