"""
CARES (ACL 2026 Long Papers · Oral, arXiv 2510.19496v3) - single-file HTML builder.
※ v4 정본 빌더 - 신규 논문은 이 파일을 복사해 조립한 뒤 tools/restyle_dash_v4.py로 변환한다.

Reads structured.json + translations/manual.json + analysis.json + tabs_data/*.json
+ config.json + assets/, emits a single self-contained HTML with v3 tokens and
3rd-gen interactions (study-fab side-drawer, eq-link, lightbox). All raster assets
are base64-inlined. Tab 5 / 6 are shells (per project policy).

Paper Study 탭(tab-study, rules/component_rules.md §17):
- tabs_data/study.json이 있으면 3-Phase 워크북 풀 빌드, 없으면 자동 셸.
- read 패널(단락 리더·세션 한정 체크) / 잠금 토글 / 근거 점프 / 도표 뷰어(config#captions_en 필요)
  / 플로팅 메모 / 노트 내보내기(폴더 기억)·가져오기 - 전부 이 파일이 자동 생성 (논문별 수정 0곳).
- 논문별로 바꿀 곳: ②③④ tab-intro 문구 · footer 한 줄 (Paper Study 쪽은 없음).
- 출력 파일명은 meta.short_name에서 자동 유도 - 코드 수정 불필요.
"""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).parent
ASSETS = ROOT / "assets"
TR = ROOT / "translations"
TD = ROOT / "tabs_data"

config   = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
struct   = json.loads((ROOT / "structured.json").read_text(encoding="utf-8"))
analysis = json.loads((ROOT / "analysis.json").read_text(encoding="utf-8"))
tr       = json.loads((TR / "manual.json").read_text(encoding="utf-8"))
diss     = json.loads((TD / "dissection.json").read_text(encoding="utf-8"))
know     = json.loads((TD / "knowledge.json").read_text(encoding="utf-8"))
ques     = json.loads((TD / "questions.json").read_text(encoding="utf-8"))

T = {s["sentence_id"]: s for s in tr["sentences"]}

asset_for_para = {}
for aid, pid, kind in config["asset_layout"]:
    asset_for_para.setdefault(pid, []).append((aid, kind))
WIDE = set(config["wide_assets"])
CAP  = config["captions"]

def b64img(name):
    p = ASSETS / name
    return f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"

ASSET_DATAURI = {n.stem: b64img(n.name) for n in ASSETS.glob("*.png") if not n.name.startswith("_")}

GEN_DIR = ASSETS / "generated"
GEN_DATAURI = {}
if GEN_DIR.exists():
    for n in GEN_DIR.glob("*.png"):
        raw = n.read_bytes()
        GEN_DATAURI[n.stem] = f"data:image/png;base64,{base64.b64encode(raw).decode()}"

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ----------------------------------------------------------------
# Tab 1 - sentence pairs + assets bound to paragraphs
# ----------------------------------------------------------------
HOTSPOTS = analysis.get("hotspots", {})
CALLOUTS = analysis.get("callouts", {})
INTERPS  = analysis.get("interpretations", {})
BEGINS   = analysis.get("beginner_notes", {})
QUIZZES  = analysis.get("quizzes", {})

def render_paragraph(p):
    pid = p["paragraph_id"]
    en_parts, kr_parts = [], []
    hot = set(HOTSPOTS.get(pid, []))
    for s in p["sentences"]:
        sid = s["sentence_id"]
        info = T.get(sid, {"original": s["text"], "translation": ""})
        cls = "sent hotspot" if sid in hot else "sent"
        en_parts.append(f'<span class="{cls}" data-pair="{sid}">{esc(info["original"])}</span>')
        kr_parts.append(f'<span class="{cls}" data-pair="{sid}">{info["translation"]}</span>')
    en_html = " ".join(en_parts)
    kr_html = " ".join(kr_parts)

    co_html = ""
    if pid in CALLOUTS:
        items = []
        for c in CALLOUTS[pid]:
            if isinstance(c, dict):
                c_type = c.get("variant", "key")
                c_text = c.get("text", "")
            else:
                c_type, c_text = c
            klass = "callout-key" if c_type == "key" else "callout-warn"
            items.append(f'<div class="callout {klass}"><p>{c_text}</p></div>')
        co_html = '<div class="callout-stack">' + "".join(items) + '</div>'

    sub = p.get("section_subtitle", "")
    sub_html = f'<p class="paragraph-subtitle">{esc(sub)}</p>' if sub else ""

    asset_html = ""
    for aid, kind in asset_for_para.get(pid, []):
        if aid not in ASSET_DATAURI: continue
        wide = " asset-wide" if aid in WIDE else ""
        cap = CAP.get(aid, "")
        interp = INTERPS.get(aid, "")
        beginner = BEGINS.get(aid, "")
        label = aid.replace("_", " ").upper()
        interp_html = f'<div class="interpretation"><h4>해석</h4><p>{interp}</p></div>' if interp else ""
        beginner_html = ""
        if beginner:
            beginner_html = (
                '<details class="beginner-note">'
                '<summary>초보자를 위한 설명</summary>'
                f'<div class="beginner-body">{beginner}</div>'
                '</details>'
            )
        fab_html = (
            f'<button class="study-fab" data-asset="{aid}" type="button">'
            '<span class="study-fab-glyph">?</span>학습 가이드</button>'
        )
        asset_html += (
            f'<figure class="asset-card{wide}" id="{aid}">'
            f'<div class="asset-image-wrap">'
            f'{fab_html}'
            f'<img src="{ASSET_DATAURI[aid]}" alt="{label}" />'
            '</div>'
            '<figcaption>'
            f'<span class="asset-label">{label}</span>'
            f'<p class="asset-cap">{esc(cap)}</p>'
            f'{interp_html}'
            f'{beginner_html}'
            '</figcaption>'
            '</figure>'
        )
    if asset_html:
        asset_html = f'<div class="asset-stack">{asset_html}</div>'

    return (
        f'<article class="paragraph-block" id="{pid}">'
        f'<span class="pid-tag">{pid}</span>'
        f'{sub_html}'
        '<div class="bilingual">'
        '<div class="col col-en"><div class="col-label">English</div>'
        f'<p class="english">{en_html}</p></div>'
        '<div class="col col-kr"><div class="col-label">한국어</div>'
        f'<p class="korean">{kr_html}</p></div>'
        '</div>'
        f'{co_html}'
        f'{asset_html}'
        '</article>'
    )

def render_section(sec):
    sid = sec["section_id"]
    paras_html = "\n".join(render_paragraph(p) for p in sec["paragraphs"])
    quiz_html = ""
    if sid in QUIZZES:
        items = []
        for q in QUIZZES[sid]:
            items.append(
                '<details class="recall-item">'
                f'<summary>{esc(q["q"])}</summary>'
                f'<div class="recall-answer"><p>{q["a"]}</p></div>'
                '</details>'
            )
        quiz_html = (
            '<aside class="recall-card">'
            '<span class="recall-tag">자가 점검</span>'
            '<h4>이 섹션 자가 점검</h4>'
            + "".join(items) + '</aside>'
        )
    return (
        f'<section class="section" id="{sid}">'
        '<div class="section-header">'
        f'<h2 class="section-title-en">{esc(sec["title"])}</h2>'
        '</div>'
        f'{paras_html}'
        f'{quiz_html}'
        '</section>'
    )

tab_reading = "\n".join(render_section(s) for s in struct["sections"])

# ----------------------------------------------------------------
# Tab 1.5 - Paper Study: 3-Phase critical-reading workbook
# (Aerial View → Interrogation → Verdict; 서술칸은 localStorage 저장,
#  Claude 분석은 잠금 토글, 근거 칩은 Translation 탭 문장/자산으로 점프)
# ----------------------------------------------------------------
STUDY_PATH = TD / "study.json"
studyd = json.loads(STUDY_PATH.read_text(encoding="utf-8")) if STUDY_PATH.exists() else None

def ev_chips(evs):
    if not evs:
        return ""
    chips = "".join(
        f'<button class="ev-chip" type="button" data-ev="{e["ref"]}">{esc(e["label"])}</button>'
        for e in evs
    )
    return f'<div class="ev-row"><span class="ev-row-label">근거</span>{chips}</div>'

SEC_BY_ID = {s["section_id"]: s for s in struct["sections"]}

def read_panel(read_cfg):
    # "본문 보기" 패널 - 해당 파트의 단락을 하나씩 플로팅 리더로 읽고 체크(✓)해 나간다
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
    return ('<div class="read-panel">'
            '<span class="read-panel-tag">본문 보기</span>'
            + "".join(groups) + '</div>')

def study_thumbs(aids):
    # 썸네일은 base64를 중복 임베드하지 않는다 - JS가 Translation 탭의 동일 자산에서 src를 복사
    figs = "".join(
        f'<figure><img data-thumb-of="{aid}" alt="{aid}" />'
        f'<figcaption>{aid.replace("_", " ").upper()}</figcaption></figure>'
        for aid in aids if aid in ASSET_DATAURI
    )
    return f'<div class="study-thumbs">{figs}</div>'

def study_write(skey, placeholder, label="내 답 - 직접 써보기", small=False):
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
        f'<span class="srb-lock">잠김 - 내 답 {min_chars}자 이상이면 열립니다</span></button>'
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

if studyd:
    p1, p2, p3 = studyd["phase1"], studyd["phase2"], studyd["phase3"]
    scan, rq, gap = p1["scan"], p1["rq"], p1["gap"]
    checks = "".join(
        f'<label><input type="checkbox" class="study-checkbox" data-ckey="p1c{i}" /><span>{c}</span></label>'
        for i, c in enumerate(scan["checklist"])
    )
    step1 = study_step(1, scan["title"],
        study_thumbs(scan["assets"])
        + f'<div class="study-check">{checks}</div>'
        + ev_chips(scan.get("evidence")))
    step2 = study_step(2, rq["title"],
        read_panel(rq.get("read"))
        + study_write("rq", rq["placeholder"])
        + study_reveal("rq", rq["min_chars"], claude_panel(rq["claude_html"], rq.get("evidence"))))
    gap_writes = "".join(
        study_write(f["key"], f["placeholder"], label=f["label"], small=True)
        for f in gap["fields"]
    )
    gap_keys = ",".join(f["key"] for f in gap["fields"])
    step3 = study_step(3, gap["title"],
        read_panel(gap.get("read"))
        + gap_writes
        + study_reveal(gap_keys, gap["min_chars"], claude_panel(gap["claude_html"], gap.get("evidence"))))

    met, conc = p2["method"], p2["conclusion"]
    qlist = "".join(
        f'<li><span class="ql-q">{q["q"]}</span>'
        f'<button class="view-chip view-chip-sm" type="button" data-read-pid="{q["ref"]}">{esc(q["label"])}</button></li>'
        for q in met["guide_questions"]
    )
    step4 = study_step(4, met["title"],
        guide_p(met.get("prompt"))
        + read_panel(met.get("read"))
        + f'<ul class="study-qlist">{qlist}</ul>'
        + study_write("method", met["placeholder"])
        + study_reveal("method", met["min_chars"],
                       claude_panel(met["claude_html"], met.get("evidence"), "Claude의 방법론 평가")))
    step5 = study_step(5, conc["title"],
        guide_p(conc.get("prompt"))
        + read_panel(conc.get("read"))
        + study_thumbs(conc["result_assets"])
        + study_write("conclusion", conc["placeholder"])
        + study_reveal("conclusion", conc["min_chars"],
                       claude_panel(conc["claude_html"], conc.get("evidence"), "Claude의 데이터-only 결론")))

    ver, alts = p3["verdict"], p3["alternatives"]
    MATCH_LABEL = {"support": "데이터 일치", "partial": "부분 일치", "beyond": "데이터 너머"}
    claims = "".join(
        f'<li class="match-{c["match"]}"><span class="match-tag">{MATCH_LABEL.get(c["match"], c["match"])}</span>'
        f'<p class="v-claim">{c["claim"]}</p><p class="v-note">{c["note"]}</p>{ev_chips(c.get("evidence"))}</li>'
        for c in ver["author_claims"]
    )
    step6 = study_step(6, ver["title"],
        guide_p(ver.get("guide"))
        + read_panel(ver.get("read"))
        + '<details class="verdict-details"><summary>결론 대조 열기 - Step 5를 마친 뒤 펼치세요</summary>'
        '<div class="verdict-grid">'
        '<div class="verdict-col v-mine"><h4>내 결론 (Step 5)</h4><div class="v-mine-body" data-mirror="conclusion"></div></div>'
        f'<div class="verdict-col v-claude"><h4>Claude의 데이터-only 결론</h4><div class="v-claude-body">{ver["claude_dataonly_summary"]}</div></div>'
        f'<div class="verdict-col v-author"><h4>저자의 주장 (§5 Discussion)</h4><ul class="v-claims">{claims}</ul></div>'
        '</div></details>')
    alt_cards = "".join(
        f'<div class="alt-card"><h5>{esc(a["title"])}</h5><p>{a["body"]}</p>{ev_chips(a.get("evidence"))}</div>'
        for a in alts["claude_items"]
    )
    step7 = study_step(7, alts["title"],
        guide_p(alts.get("prompt"))
        + read_panel(alts.get("read"))
        + study_write("alt", alts["placeholder"])
        + study_reveal("alt", alts["min_chars"],
                       f'<span class="study-claude-tag">Claude의 대안 가설</span>{alt_cards}'))

    tab_study = (
        '<div class="tab-intro">'
        '<h2>Paper Study - 3-Phase 비판적 읽기</h2>'
        '</div>'
        '<div class="study-toolbar">'
        '<div class="study-toolbar-note">메모는 이 브라우저에 자동 저장 · 파일 보관은 내보내기'
        ' <button class="study-loc-link" id="study-setdir" type="button">저장 위치 변경</button></div>'
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
else:
    tab_study = (
        '<div class="tab-intro">'
        '<h2>Paper Study - 3-Phase 비판적 읽기</h2>'
        '<p>Aerial View → Interrogation → Verdict 순서의 자기주도 워크북이 들어갈 자리입니다.</p>'
        '</div>'
        '<section class="section section-empty">'
        '<p class="section-empty-note">이 탭은 tabs_data/study.json이 준비되면 채워집니다.</p>'
        '</section>'
    )

# 서론 섹션 끝에 "Paper Study로 돌아가기" 버튼 - RQ 찾기 동선의 복귀 지점
# 서론 section_id를 study.json rq.read의 마지막 항목(=서론)에서 도출 → 모든 관례 커버
# (s_intro / intro / sec-intro / s2 등 숫자식 무관). 없으면 관례 목록으로 폴백.
if studyd:
    _cands = []
    try:
        _cands = [r["sec"] for r in reversed(studyd["phase1"]["rq"].get("read", []))]
    except Exception:
        pass
    _cands += ["s_intro", "intro", "sec-intro", "s2"]
    _i = -1
    for _sid in _cands:
        _i = tab_reading.find(f'<section class="section" id="{_sid}"')
        if _i >= 0:
            break
    if _i >= 0:
        _j = tab_reading.find('</section>', _i)
        _goto = ('<div class="study-goto-row">'
                 '<button class="study-goto" type="button">서론 끝 - Paper Study로 돌아가기 ↩</button>'
                 '</div>')
        tab_reading = tab_reading[:_j] + _goto + tab_reading[_j:]

# 도표 뷰어 데이터 - 원문 캡션(config#captions_en) + 번역(config#captions) + 해석(analysis#interpretations)
AV_DATA = {}
if studyd:
    _caps_en = config.get("captions_en", {})
    for _aid in ASSET_DATAURI:
        AV_DATA[_aid] = {
            "label": _aid.replace("_", " ").upper(),
            "en": _caps_en.get(_aid, ""),
            "kr": CAP.get(_aid, ""),
            "interp": INTERPS.get(_aid, ""),
        }

STUDY_CSS = """
/* ---- Paper Study tab (tab-study) ---- */
.study-toolbar{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:12px 18px;margin-bottom:18px}
.study-toolbar-note{font-size:12.5px;color:var(--muted);max-width:640px}
.study-toolbar-btns{display:flex;gap:8px;flex-wrap:wrap}
.study-btn{font:inherit;font-size:12.5px;font-weight:700;color:var(--accent);background:var(--accent-soft);border:1px solid var(--accent-pale);border-radius:999px;padding:6px 14px;cursor:pointer}
.study-btn:hover{background:var(--accent-pale)}
.study-btn-danger{color:var(--rose);background:var(--rose-soft);border-color:var(--rose)}
.study-loc-link{font:inherit;font-size:11.5px;color:var(--muted);background:none;border:0;padding:0;margin-left:8px;text-decoration:underline dotted;text-underline-offset:3px;cursor:pointer}
.study-loc-link:hover{color:var(--accent)}
.phase-band{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:16px 20px;margin:26px 0 14px}
.phase-band.phase-p2{}
.phase-band.phase-p3{}
.phase-tag{display:inline-block;font-size:11px;font-weight:800;letter-spacing:0.07em;text-transform:uppercase;background:var(--accent-soft);color:var(--accent);padding:3px 10px;border-radius:999px}
.phase-band.phase-p2 .phase-tag{background:var(--amber-soft);color:var(--amber)}
.phase-band.phase-p3 .phase-tag{background:var(--rose-soft);color:var(--rose)}
.phase-band h3{margin:8px 0 4px;font-size:17px;color:var(--ink)}
.phase-band p{margin:0;font-size:13.5px;color:var(--muted)}
.ai-note{margin-top:10px;font-size:13px;color:var(--rose);background:var(--rose-soft);border-radius:10px;padding:9px 12px;font-weight:600}
.study-step{position:relative;background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:22px 24px;margin-bottom:16px;box-shadow:0 6px 20px rgba(80,60,140,0.05)}
.study-step-head{display:flex;align-items:center;gap:12px;margin-bottom:8px}
.study-step-no{flex-shrink:0;width:34px;height:34px;border-radius:10px;background:var(--accent-soft);color:var(--accent);font-weight:800;font-size:16px;display:flex;align-items:center;justify-content:center}
.study-step-head h3{margin:0;font-size:17px;color:var(--ink)}
.study-guide{margin:0 0 12px;font-size:14px;color:var(--muted);line-height:1.7}
.study-qlist{margin:0 0 12px;padding-left:0;list-style:none;display:grid;gap:8px}
.study-qlist li{background:#fbfaff;border:1px solid var(--line);border-radius:10px;padding:9px 12px;font-size:13.5px;color:var(--ink)}
.study-check{display:grid;gap:8px;margin:12px 0}
.study-check label{display:flex;gap:10px;align-items:flex-start;font-size:13.5px;background:#fbfaff;border:1px solid var(--line);border-radius:10px;padding:10px 12px;cursor:pointer;line-height:1.6}
.study-check input{margin-top:3px;accent-color:var(--accent)}
.study-thumbs{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:12px 0}
.study-thumbs figure{margin:0;border:1px solid var(--line);border-radius:10px;padding:6px;background:#ffffff}
.study-thumbs img{width:100%;height:104px;object-fit:contain;display:block;cursor:zoom-in;background:#fbfaff}
.study-thumbs figcaption{font-size:10.5px;font-weight:700;color:var(--muted);text-align:center;margin-top:4px;letter-spacing:0.04em}
.study-write-wrap{margin-top:6px}
.study-write-label{display:inline-block;font-size:11px;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;color:var(--accent);background:var(--accent-soft);padding:3px 10px;border-radius:999px;margin-bottom:8px}
.study-write{width:100%;min-height:132px;resize:vertical;font:inherit;font-size:14.5px;line-height:1.7;color:var(--ink);background:#fbfaff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;box-sizing:border-box}
.study-write:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.study-write-status{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-top:6px}
.study-reveal{margin-top:12px}
.study-reveal-bar{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.study-reveal-btn{font:inherit;font-size:13.5px;font-weight:700;color:#ffffff;background:var(--accent);border:0;border-radius:999px;padding:9px 18px;cursor:pointer;display:inline-flex;align-items:center;gap:10px}
.study-reveal-btn:hover:not(:disabled){filter:brightness(1.08)}
.study-reveal-btn:disabled{background:var(--accent-soft);color:var(--muted);cursor:not-allowed}
.study-reveal-btn .srb-lock{font-size:11.5px;font-weight:600;opacity:0.85}
.study-skip{font:inherit;font-size:12px;color:var(--muted);background:none;border:0;text-decoration:underline dotted;text-underline-offset:3px;cursor:pointer;padding:0}
.study-claude{margin-top:12px;background:#f8f3ff;border:1px dashed var(--accent-pale);border-radius:12px;padding:14px 16px}
.study-claude-tag{display:inline-block;font-size:11px;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;color:var(--accent);background:#ffffff;border:1px solid var(--accent-pale);padding:3px 10px;border-radius:999px;margin-bottom:8px}
.study-claude-body{font-size:14px;line-height:1.72;color:var(--ink)}
.study-claude-body p{margin:0 0 10px}
.study-claude-body p:last-child{margin-bottom:0}
.ev-row{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px;align-items:center}
.ev-row-label{font-size:11px;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;color:var(--muted)}
.ev-chip{font:inherit;font-size:12px;font-weight:700;color:var(--azure);background:var(--azure-soft);border:1px solid var(--azure-pale);border-radius:999px;padding:4px 11px;cursor:pointer}
.ev-chip:hover{background:var(--azure-pale)}
.verdict-details{margin-top:8px}
.verdict-details > summary{cursor:pointer;font-weight:700;color:var(--accent);font-size:14px;list-style:none;background:var(--accent-soft);border-radius:10px;padding:10px 14px}
.verdict-details > summary::-webkit-details-marker{display:none}
.verdict-details > summary::before{content:"▶";display:inline-block;margin-right:8px;font-size:0.8em;transition:transform 0.15s ease}
.verdict-details[open] > summary::before{transform:rotate(90deg)}
.verdict-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:14px}
.verdict-col{background:#fbfaff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;min-width:0}
.verdict-col h4{margin:0 0 10px;font-size:13.5px;color:var(--ink)}
.v-mine{border-top:3px solid var(--accent)}
.v-claude{border-top:3px solid var(--azure)}
.v-author{border-top:3px solid var(--rose)}
.v-mine-body{white-space:pre-wrap;font-size:13.5px;line-height:1.7;color:var(--ink)}
.v-mine-body.v-empty{color:var(--muted)}
.v-claude-body{font-size:13.5px;line-height:1.7;color:var(--ink)}
.v-claude-body p{margin:0}
.v-claims{list-style:none;margin:0;padding:0}
.v-claims li{background:#ffffff;border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin-bottom:10px;font-size:13px;line-height:1.65}
.match-tag{display:inline-block;font-size:10.5px;font-weight:800;border-radius:999px;padding:2px 9px;margin-bottom:6px}
.match-support .match-tag{background:var(--mint-soft);color:var(--mint)}
.match-partial .match-tag{background:var(--amber-soft);color:var(--amber)}
.match-beyond .match-tag{background:var(--rose-soft);color:var(--rose)}
.v-claim{margin:0 0 6px;font-weight:700;color:var(--ink)}
.v-note{margin:0;color:var(--muted);font-size:12.5px}
.alt-card{background:#fbfaff;border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:10px}
.alt-card h5{margin:0 0 6px;font-size:14px;color:var(--ink)}
.alt-card p{margin:0;font-size:13.5px;line-height:1.7;color:var(--ink)}
.view-chip{font:inherit;font-size:12.5px;font-weight:700;color:#ffffff;background:var(--azure);border:0;border-radius:999px;padding:6px 14px;cursor:pointer;display:inline-flex;align-items:center;gap:6px}
.view-chip::before{content:"→"}
.view-chip:hover{filter:brightness(1.08)}
.view-chip-sm{font-size:11px;padding:3px 10px;margin-left:8px;vertical-align:1px;background:var(--azure-soft);color:var(--azure);border:1px solid var(--azure-pale)}
.study-qlist li{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
.study-qlist .ql-q{flex:1 1 320px;min-width:0}
.study-qlist .view-chip-sm{flex-shrink:0;margin-left:0}
.sent.ev-hl{background:var(--amber-soft);box-shadow:0 0 0 2px var(--amber);border-radius:4px;transition:background 200ms ease,box-shadow 200ms ease}
.study-return{position:fixed;bottom:26px;left:50%;transform:translateX(-50%) translateY(10px);z-index:210;font:inherit;font-size:13.5px;font-weight:800;color:#ffffff;background:var(--accent);border:0;border-radius:999px;padding:11px 22px;cursor:pointer;box-shadow:0 10px 26px rgba(48,53,66,0.3);opacity:0;pointer-events:none;transition:opacity 200ms ease,transform 200ms ease}
.study-return.visible{opacity:1;transform:translateX(-50%) translateY(0);pointer-events:auto}
.study-return:hover{filter:brightness(1.1)}
.study-goto-row{display:flex;justify-content:center;margin-top:18px}
.study-goto{font:inherit;font-size:13.5px;font-weight:700;color:var(--accent);background:var(--accent-soft);border:1px dashed var(--accent-pale);border-radius:999px;padding:10px 22px;cursor:pointer}
.study-goto:hover{background:var(--accent-pale)}
.study-write-sm{min-height:76px}
#tab-reading .section,#tab-reading .paragraph-block,#tab-reading .asset-card{scroll-margin-top:130px}
#tab-reading .sent{scroll-margin-top:120px}
/* ---- 본문 보기 패널: 단락 칩 + 읽음 체크 ---- */
.read-panel{background:#fbfaff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:2px 0 14px}
.read-panel-tag{display:inline-block;font-size:11px;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;color:var(--muted)}
.read-group{margin-top:10px}
.read-group-head{display:flex;align-items:center;gap:10px}
.read-group-label{font-weight:800;font-size:13px;color:var(--ink)}
.read-progress{font-size:11.5px;font-weight:700;color:var(--muted);background:var(--paper);border:1px solid var(--line);border-radius:999px;padding:2px 9px}
.read-progress.all-done{color:var(--mint);border-color:var(--mint);background:var(--mint-soft)}
.read-chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:8px}
.read-chip{font:inherit;font-size:12.5px;font-weight:700;color:var(--accent);background:var(--paper);border:1px solid var(--accent-pale);border-radius:999px;padding:5px 13px;cursor:pointer;display:inline-flex;align-items:center;gap:6px}
.read-chip:hover{background:var(--accent-soft)}
.read-chip.read-done{color:var(--mint);border-color:var(--mint);background:var(--mint-soft)}
.read-chip.read-done::after{content:"✓";font-weight:900}
/* ---- 단락 플로팅 리더 ---- */
.para-reader{position:fixed;inset:0;background:rgba(30,28,40,0.55);display:none;align-items:center;justify-content:center;z-index:1450;padding:22px}
.para-reader.open{display:flex}
.pr-panel{background:var(--bg);border-radius:16px;box-shadow:0 24px 64px rgba(20,18,35,0.35);width:min(1080px,95vw);max-height:90vh;display:flex;flex-direction:column;overflow:hidden}
.pr-head{display:flex;align-items:center;gap:10px;padding:12px 18px;border-bottom:1px solid var(--line);background:var(--paper);flex-shrink:0}
.pr-title{display:inline-block;font-weight:800;font-size:12.5px;color:var(--accent);background:var(--accent-soft);padding:3px 12px;border-radius:999px}
.pr-pos{margin-left:auto;font-size:12px;font-weight:700;color:var(--muted)}
.pr-close{border:1px solid var(--line);background:#ffffff;border-radius:50%;width:32px;height:32px;font-size:17px;line-height:1;color:var(--muted);cursor:pointer;flex-shrink:0}
.pr-close:hover{color:var(--accent);border-color:var(--accent)}
.pr-body{padding:18px 20px;overflow-y:auto;min-height:0}
.pr-body .paragraph-block{margin-bottom:0}
.pr-foot{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 18px;border-top:1px solid var(--line);background:var(--paper);flex-shrink:0;flex-wrap:wrap}
.pr-nav{display:flex;gap:8px}
.pr-prev,.pr-next{font:inherit;font-size:13px;font-weight:700;color:var(--accent);background:var(--accent-soft);border:1px solid var(--accent-pale);border-radius:999px;padding:7px 16px;cursor:pointer}
.pr-prev:hover:not(:disabled),.pr-next:hover:not(:disabled){background:var(--accent-pale)}
.pr-prev:disabled,.pr-next:disabled{opacity:0.4;cursor:not-allowed}
.pr-open-translation{font:inherit;font-size:12px;color:var(--muted);background:none;border:0;text-decoration:underline dotted;text-underline-offset:3px;cursor:pointer}
/* ---- 학습 메모: 플로팅 버튼(우측 상단, to-top의 x · 탭 제목의 y) + 자유 서식 메모장 드로어 ---- */
.memo-fab{position:fixed;right:26px;top:150px;z-index:2400;font:inherit;font-size:13px;font-weight:800;color:var(--amber);background:var(--amber-soft);border:1px solid var(--amber);border-radius:999px;padding:9px 18px;cursor:pointer;box-shadow:0 6px 18px rgba(48,53,66,0.14);display:inline-flex;align-items:center;gap:7px}
.memo-fab:hover{color:#ffffff;background:var(--amber)}
.memo-fab .memo-dot{width:8px;height:8px;border-radius:50%;background:var(--amber);flex-shrink:0}
.memo-fab:hover .memo-dot{background:#ffffff}
.memo-drawer{position:fixed;top:0;right:0;height:100vh;width:380px;max-width:92vw;background:var(--paper);border-left:1px solid var(--line);box-shadow:-12px 0 36px rgba(30,34,46,0.14);transform:translateX(100%);transition:transform 240ms ease;z-index:2400;display:flex;flex-direction:column}
.memo-drawer.open{transform:translateX(0)}
.memo-head{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:16px 18px 8px}
.memo-title{font-weight:800;font-size:14px;color:var(--amber)}
.memo-close{border:1px solid var(--line);background:#ffffff;border-radius:50%;width:30px;height:30px;font-size:16px;line-height:1;color:var(--muted);cursor:pointer;flex-shrink:0}
.memo-close:hover{color:var(--amber);border-color:var(--amber)}
.memo-hint{margin:0 18px 10px;font-size:11.5px;color:var(--muted);line-height:1.6}
.memo-pad{flex:1;margin:0 18px;font:inherit;font-size:13.5px;line-height:1.7;border:1px solid var(--line);border-radius:10px;padding:12px;resize:none;background:#fbfaff;color:var(--ink)}
.memo-pad:focus{outline:none;border-color:var(--amber);box-shadow:0 0 0 3px var(--amber-soft)}
.memo-status{display:flex;justify-content:space-between;padding:8px 18px 14px;font-size:11px;color:var(--muted)}
/* ---- 문장 형광펜 (사용자 하이라이트 - 문장 클릭 토글, 리더·Translation 동기) ---- */
.sent.user-hl{background:#f5e8b8;border-radius:4px;padding:0 2px;box-decoration-break:clone;-webkit-box-decoration-break:clone}
#tab-reading .sent, .pr-body .sent{cursor:pointer}
.pr-hint{font-size:11px;color:var(--muted)}
/* ---- 노트 불러오기 선택창 ---- */
.notes-picker{position:fixed;inset:0;background:rgba(30,28,40,0.5);display:none;align-items:center;justify-content:center;z-index:1700;padding:22px}
.notes-picker.open{display:flex}
.np-panel{background:var(--paper);border-radius:14px;box-shadow:0 24px 64px rgba(20,18,35,0.35);width:min(520px,94vw);max-height:80vh;display:flex;flex-direction:column;overflow:hidden}
.np-head{display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--line)}
.np-title{font-weight:800;font-size:14px;color:var(--ink)}
.np-dir{font-size:11.5px;color:var(--muted);margin-left:auto}
.np-close{border:1px solid var(--line);background:#ffffff;border-radius:50%;width:30px;height:30px;font-size:16px;line-height:1;color:var(--muted);cursor:pointer;flex-shrink:0}
.np-close:hover{color:var(--accent);border-color:var(--accent)}
.np-list{overflow-y:auto;padding:10px 14px;display:grid;gap:8px}
.np-item{font:inherit;text-align:left;display:flex;align-items:center;justify-content:space-between;gap:10px;background:#fbfaff;border:1px solid var(--line);border-radius:10px;padding:10px 13px;cursor:pointer}
.np-item:hover{border-color:var(--accent);background:var(--accent-soft)}
.np-item b{font-size:13px;color:var(--ink);font-weight:700;word-break:break-all}
.np-item span{font-size:11.5px;color:var(--muted);flex-shrink:0}
.np-foot{padding:10px 14px;border-top:1px solid var(--line);display:flex;justify-content:flex-end}
.np-file{font:inherit;font-size:12px;color:var(--muted);background:none;border:0;text-decoration:underline dotted;text-underline-offset:3px;cursor:pointer}
/* ---- 도표 뷰어: 이미지 + 원문 캡션 + 번역 + 해석 토글 ---- */
.asset-viewer{position:fixed;inset:0;background:rgba(30,28,40,0.55);display:none;align-items:center;justify-content:center;z-index:1500;padding:22px}
.asset-viewer.open{display:flex}
.av-panel{background:var(--paper);border-radius:16px;box-shadow:0 24px 64px rgba(20,18,35,0.35);max-width:min(1240px,95vw);max-height:92vh;display:flex;flex-direction:column;overflow:hidden}
.av-head{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 18px;border-bottom:1px solid var(--line);flex-shrink:0}
.av-label{display:inline-block;font-weight:800;font-size:12px;color:var(--accent);background:var(--accent-soft);padding:3px 12px;border-radius:999px;letter-spacing:0.06em}
.av-hint{font-size:11.5px;color:var(--muted)}
.av-close{border:1px solid var(--line);background:#ffffff;border-radius:50%;width:32px;height:32px;font-size:17px;line-height:1;color:var(--muted);cursor:pointer;flex-shrink:0}
.av-close:hover{color:var(--accent);border-color:var(--accent)}
.av-head .study-fab{position:static;box-shadow:none;flex-shrink:0}
.asset-viewer{transition:padding 240ms ease}
.asset-viewer.av-shift{justify-content:flex-start;padding-right:470px}
@media (max-width: 1100px){.asset-viewer.av-shift{padding-right:22px}}
.av-body{display:flex;overflow:auto;min-height:0}
.asset-viewer.av-tall .av-body{flex-direction:row}
.asset-viewer.av-wide .av-body{flex-direction:column}
.av-img{display:flex;align-items:center;justify-content:center;background:#fbfaff;padding:14px;min-width:0;min-height:0}
.asset-viewer.av-tall .av-img{flex:1 1 62%}
.av-img img{max-width:100%;height:auto;display:block;cursor:zoom-in}
.asset-viewer.av-tall .av-img img{max-height:78vh}
.asset-viewer.av-wide .av-img img{max-height:50vh}
.av-text{padding:14px 20px 18px;overflow-y:auto;flex-shrink:0}
.asset-viewer.av-tall .av-text{flex:0 0 400px;border-left:1px solid var(--line)}
.asset-viewer.av-wide .av-text{border-top:1px solid var(--line);max-height:36vh}
.av-sec{margin-bottom:12px}
.av-sec h5{margin:0 0 5px;font-size:11px;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;color:var(--muted)}
.av-en h5{color:var(--accent)}
.av-kr h5{color:var(--azure)}
.av-sec p{margin:0;font-size:13.5px;line-height:1.7;color:var(--ink)}
details.av-interp{background:#f8f3ff;border:1px dashed var(--accent-pale);border-radius:10px;padding:9px 13px}
details.av-interp > summary{cursor:pointer;font-weight:700;color:var(--accent);font-size:13px;list-style:none}
details.av-interp > summary::-webkit-details-marker{display:none}
details.av-interp > summary::before{content:"▶";display:inline-block;margin-right:7px;font-size:0.8em;transition:transform 0.15s ease}
details.av-interp[open] > summary::before{transform:rotate(90deg)}
details.av-interp .av-interp-body{margin-top:8px;font-size:13.5px;line-height:1.7;color:var(--ink)}
@media (max-width: 760px){
  .asset-viewer{padding:10px}
  .asset-viewer .av-body{flex-direction:column !important}
  .asset-viewer .av-text{flex:0 0 auto !important;border-left:0 !important;border-top:1px solid var(--line);max-height:40vh}
  .asset-viewer .av-img img{max-height:44vh !important}
}
@media print{.study-toolbar-btns,.study-reveal-bar,.study-return,.asset-viewer,.study-goto-row,.memo-drawer,.memo-fab,.notes-picker,.para-reader{display:none !important}.study-claude[hidden]{display:block}}
"""

# ----------------------------------------------------------------
# Tab 2 - Dissection 7+1
# ----------------------------------------------------------------
def render_diss_card(c):
    rows = "".join(
        f'<div class="diss-row"><dt class="diss-tag">{esc(r["tag"])}</dt>'
        f'<dd class="diss-body">{r["body"]}</dd></div>'
        for r in c["rows"]
    )
    overview_html = ""
    if c.get("cls") == "diss-summary" and "dissection_overview" in GEN_DATAURI:
        overview_html = (
            '<figure class="diss-overview-figure">'
            f'<img src="{GEN_DATAURI["dissection_overview"]}" alt="CARES 한 장 정리" />'
            '<figcaption>PROBLEM &rarr; OBSERVATION &rarr; METHOD &rarr; NOVELTY &rarr; RESULTS - 5단 가로 흐름으로 본 CARES. 본문 9-row와 동일 내용의 시각 요약.</figcaption>'
            '</figure>'
        )
    return (
        f'<article class="diss-card {c["cls"]}">'
        f'<div class="diss-step">{c["id"]:02d}</div>'
        '<div class="diss-head">'
        f'<h3>{esc(c["title"])}</h3>'
        f'<p class="diss-lead">{esc(c["lead"])}</p>'
        '</div>'
        + overview_html
        + f'<dl class="diss-rows">{rows}</dl>'
        + '</article>'
    )

tab_dissection = (
    '<div class="tab-intro">'
    '<h2>Paper Dissection - 7+1 카드 분석</h2>'
    '<p>CARES의 사고 흐름을 동기(prefill 최대 99% 토큰 낭비) → 관찰(필요 해상도는 질의가 결정) → 차별(토큰화 이전 vs 이후) → 방법(3단계 파이프라인·수렴 규칙·이산→연속) → 검증 → 위험 → 확장 7단계로 분해하고, 마지막 카드에 9-row + 한 장 인포그래픽으로 압축한다.</p>'
    '</div>'
    '<div class="diss-grid">'
    + "".join(render_diss_card(c) for c in diss["cards"])
    + '</div>'
)

# ----------------------------------------------------------------
# Tab 3 - Knowledge: primer + fund cards + equations + concepts
# ----------------------------------------------------------------
primer = know["primer"]
fund_cards_html = "".join(
    f'<div class="fund-card">'
    f'<div class="fund-step">{i+1}</div>'
    f'<span class="fund-label-tag">{esc(fc.get("label",""))}</span>'
    f'<h4>{esc(fc["title"])}</h4>'
    f'<p class="fund-body">{fc["body"]}</p>'
    '</div>'
    for i, fc in enumerate(primer["fund_cards"])
)

eq_cards_html = ""
for eq in know["equations"]:
    eq_cards_html += (
        f'<div class="eq-card" id="{eq["eq_id"]}">'
        '<div class="eq-head">'
        f'<span class="eq-label">{esc(eq["label"])}</span>'
        '</div>'
        f'<div class="eq-display">$$ {eq["tex"]} $$</div>'
        '<div class="eq-meta">'
        f'<div class="eq-section"><h5>기호 의미</h5><p>{eq["where"]}</p></div>'
        f'<div class="eq-section"><h5>직관·연결</h5><p>{eq["intuition"]}</p></div>'
        '</div>'
        '</div>'
    )

concept_cards_html = "".join(
    '<div class="knw-card">'
    f'<span class="knw-label-tag">{esc(cc.get("label",""))}</span>'
    f'<h3>{esc(cc["title"])}</h3>'
    f'<div class="knw-body">{cc["body"]}</div>'
    '</div>'
    for cc in know["concept_cards"]
)

tab_knowledge = (
    '<div class="tab-intro">'
    '<h2>Background - 배경지식</h2>'
    '<p>CARES를 이해하기 위한 6개 빌딩 블록 + 8개 개념 카드 (핵심 수식 6개는 Mathematics 탭). 해상도→토큰→연산의 사슬 / 시각 토큰 최대 99% / ANLS 지표 / 대상·프록시 VLM 라인업 / 중간 레이어 표현 / 이산 분류→연속 해상도 → 그 위에 본 논문이 정립한 과제·수렴 규칙·plug-in 직교성.</p>'
    '</div>'
    '<section class="fund-panel">'
    f'<h3 class="panel-title">{esc(primer["title"])}</h3>'
    f'<p class="panel-sub">{esc(primer["caption"])}</p>'
    f'<div class="fund-grid">{fund_cards_html}</div>'
    '</section>'
    '<section class="eq-panel">'
    '<h3 class="panel-title">핵심 수식 6개</h3>'
    '<p class="panel-sub">해상도별 ANLS(Eq.1) · 충분 해상도 수렴 규칙(Eq.2) · 분류기 softmax · 연속 해상도 기댓값(Eq.3) · 교차 엔트로피 목적식 · 리사이즈↔토큰 수 - CARES의 정량 골격 여섯 줄.</p>'
    f'<div class="eq-grid eq-grid-detailed">{eq_cards_html}</div>'
    '</section>'
    '<section class="fund-panel">'
    '<h3 class="panel-title">개념 카드</h3>'
    '<p class="panel-sub">본 논문이 정립·도입한 8개 핵심 개념 - Context-Aware Resolution Selection 과제 · Sufficiency 수렴 규칙 · Multi-Resolution Rollout · Discrete-to-Continuous 기댓값 · Frozen Proxy + 중간 레이어 · Pre/Post-tokenization 축 · Query-conditioned Routing · Plug-and-Play 직교성.</p>'
    f'<div class="knw-grid">{concept_cards_html}</div>'
    '</section>'
)

# ----------------------------------------------------------------
# Tab 4 - Questions: q/a rows + diagrams
# ----------------------------------------------------------------
def render_q_card(c):
    rows = "".join(
        '<details class="recall-item">'
        f'<summary>{esc(r["q"])}</summary>'
        f'<div class="recall-answer"><p>{r["a"]}</p></div>'
        '</details>'
        for r in c["rows"]
    )
    return (
        f'<article class="coach-card {c["cls"]}">'
        f'<span class="coach-tag">{esc(c["title"])}</span>'
        f'<h3>{esc(c["lead"])}</h3>'
        f'<div class="q-rows">{rows}</div>'
        '</article>'
    )

ques_diagrams_html = ""
for d in ques.get("diagrams", []):
    stem = Path(d["image_path"]).stem
    if stem in GEN_DATAURI:
        ques_diagrams_html += (
            '<figure class="concept-figure">'
            f'<img src="{GEN_DATAURI[stem]}" alt="{stem}" />'
            '<figcaption>'
            '<span class="cf-label">학습 보조 · 다이어그램</span>'
            f'<h4>{esc(d["title"])}</h4>'
            f'<p>{d["caption"]}</p>'
            '</figcaption>'
            '</figure>'
        )

tab_questions = (
    '<div class="tab-intro">'
    '<h2>Questions &amp; Diagrams</h2>'
    '<p>본문이 명시하지 않은 가정·설계 근거·비판적 질문·확장 가능성을 4개 카드로 분해. 저해상도 특징으로 필요 해상도를 알 수 있다는 순환 가정 · {384,768,1024} 메뉴와 16번 레이어 선택의 근거 · prefill 기준 절감률과 CARES 자체 오버헤드 · region/video/멀티턴 확장까지.</p>'
    '</div>'
    f'{ques_diagrams_html}'
    '<div class="coach-grid">'
    + "".join(render_q_card(c) for c in ques["cards"])
    + '</div>'
)

# ----------------------------------------------------------------
# Tab 5 / 6 - shells only
# ----------------------------------------------------------------
tab_simulator = (
    '<div class="tab-intro">'
    '<h2>Simulator &amp; Code</h2>'
    '<p>핵심 알고리즘 시뮬레이터·의사코드·코드 비교가 들어갈 자리입니다.</p>'
    '</div>'
    '<section class="section section-empty">'
    '<p class="section-empty-note">이 탭은 별도 요청 시 작성됩니다.</p>'
    '</section>'
)
tab_qa = (
    '<div class="tab-intro">'
    '<h2>학습 기초 Q &amp; A</h2>'
    '<p>자가 점검을 위한 카테고리별 Q&amp;A가 들어갈 자리입니다.</p>'
    '</div>'
    '<section class="section section-empty">'
    '<p class="section-empty-note">이 탭은 별도 요청 시 작성됩니다.</p>'
    '</section>'
)

# ----------------------------------------------------------------
# Page assembly
# ----------------------------------------------------------------
meta = config.get("metadata") or config.get("meta")
HEAD = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(meta["short_name"])}: {esc(meta["title"])}</title>
<script>
  MathJax = {{
    tex: {{ inlineMath: [['$', '$'], ['\\\\(', '\\\\)']], displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']], processEscapes: true }},
    options: {{ skipHtmlTags: ['script','noscript','style','textarea','pre','code'] }}
  }};
</script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<style>
:root {{
  --bg: #fbfaff; --paper: #ffffff; --ink: #1f1d24; --muted: #7a7484; --line: #ece8f0;
  --accent: #8b75c0; --accent-soft: #e4d9ff; --accent-pale: #d2c2f5;
  --azure: #6b95b3; --azure-soft: #d9ebff; --azure-pale: #c0dcf5;
  --rose: #b87887;  --rose-soft: #ffdde6;
  --mint: #75ad8e; --mint-soft: #e3eee7;
  --amber: #ad8e4e; --amber-soft: #f3ead4;
  --hero-gradient: linear-gradient(135deg, #c0dcf5 0%, #d2c2f5 100%);
}}
*{{box-sizing:border-box}} html,body{{margin:0;padding:0}}
body{{font-family:"Pretendard Variable","Noto Sans KR","Segoe UI",Tahoma,sans-serif;background:var(--bg);color:var(--ink);line-height:1.72}}
.app{{max-width:1280px;margin:0 auto;padding:28px 26px 90px}}
.brand-tag{{display:inline-block;padding:5px 11px;border-radius:999px;background:var(--accent-soft);color:var(--accent);font-weight:700;font-size:12px;letter-spacing:0.06em;text-transform:uppercase}}
header.hero{{background:var(--paper);border:1px solid var(--line);border-radius:22px;padding:28px 32px;box-shadow:0 12px 32px rgba(60,40,90,0.07);margin-bottom:22px;background-image:linear-gradient(180deg,#ffffff 60%,#fbf8ff 100%)}}
header.hero h1{{margin:12px 0 6px;font-family:Georgia,"Times New Roman",serif;font-size:30px;line-height:1.22;color:var(--ink)}}
header.hero .subtitle{{margin:0 0 14px;color:var(--muted)}}
header.hero .meta{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;font-size:13px;color:var(--muted)}}
header.hero .meta .meta-item strong{{display:block;color:var(--ink);font-size:11px;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:3px}}
nav.tabs{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px;position:sticky;top:0;z-index:50;background:rgba(251,250,255,0.94);backdrop-filter:blur(6px);padding:10px 6px;border-radius:14px;border:1px solid var(--line)}}
.tab-btn{{flex:1 1 auto;min-width:170px;padding:10px 14px;border-radius:10px;border:1px solid transparent;background:transparent;font:inherit;font-weight:600;color:var(--muted);cursor:pointer}}
.tab-btn:hover{{color:var(--accent)}}
.tab-btn.active{{background:var(--paper);color:var(--accent);border-color:var(--line);box-shadow:0 4px 14px rgba(80,60,140,0.06)}}
.tab-pane{{display:none}} .tab-pane.active{{display:block}}
.tab-intro{{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:18px 22px;margin-bottom:18px}}
.tab-intro h2{{margin:0 0 6px;font-family:Georgia,"Times New Roman",serif;color:var(--accent);font-size:22px}}
.tab-intro p{{margin:0;color:var(--muted);font-size:14px}}
.section{{background:var(--paper);border:1px solid var(--line);border-radius:22px;padding:26px 28px 28px;margin-bottom:22px;box-shadow:0 8px 24px rgba(80,60,140,0.05)}}
.section.section-empty{{padding-bottom:16px}}
.section-header{{border-bottom:1px solid var(--line);padding-bottom:12px;margin-bottom:18px}}
.section-title-en{{margin:0;font-family:Georgia,"Times New Roman",serif;font-size:22px;color:var(--accent)}}
.section-empty-note{{color:var(--muted);font-size:14px;font-style:italic}}
.paragraph-block{{position:relative;background:linear-gradient(180deg,#ffffff,#faf8ff);border:1px solid #ece8f0;border-radius:18px;padding:20px 22px 22px;margin-bottom:20px}}
.pid-tag{{position:absolute;top:-10px;left:18px;background:var(--accent);color:#fff;font-size:11px;font-weight:700;letter-spacing:0.08em;padding:4px 10px;border-radius:999px;text-transform:uppercase}}
.paragraph-subtitle{{margin:0 0 12px;font-family:Georgia,serif;font-style:italic;color:var(--accent);font-size:14px;font-weight:600}}
.bilingual{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.col{{background:rgba(255,255,255,0.85);border-radius:12px;padding:14px 16px;border:1px solid var(--line)}}
.col-en{{background:var(--accent-soft)}} .col-kr{{background:var(--azure-soft)}}
.col-label{{font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}}
.col p{{margin:0;font-size:15px;color:var(--ink)}}
.col p.english{{font-family:Georgia,"Times New Roman",serif}}
.col p.korean{{font-size:15.5px}}
.col p .sent{{display:inline;border-radius:4px;padding:0 2px;transition:background 130ms ease,box-shadow 130ms ease}}
.col p .sent.pair-active{{background:var(--amber-soft);box-shadow:0 0 0 1px var(--amber)}}
.col p .sent.hotspot{{background:#fff4d6;padding:1px 4px;border-radius:4px}}
/*PR-HLP v1 - 사용자 형광펜이 호버보다 우선*/.col .sent.user-hl,.col .sent.user-hl.pair-active,.col .sent.hotspot.user-hl,.col .sent.hotspot.user-hl.pair-active{{background:#f5e8b8}}
.col p .sent.hotspot.pair-active{{background:#ffe4a1;box-shadow:0 0 0 1px var(--amber)}}
.callout-stack{{margin-top:14px;display:grid;gap:10px}}
.callout{{position:relative;padding:14px 16px 14px 20px;border-radius:10px;font-size:14.5px}}
.callout p{{margin:0}}
.callout::before{{display:inline-block;content:attr(data-label);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;padding:3px 9px;border-radius:999px;margin-right:10px;vertical-align:1px}}
.callout-key{{background:var(--amber-soft);border-color:var(--amber);color:#5a4716}}
.callout-key::before{{content:"★ 핵심 포인트";background:var(--amber);color:#fff}}
.callout-warn{{background:var(--rose-soft);border-color:var(--rose);color:#6c2c3a}}
.callout-warn::before{{content:"주의 / 흔한 오해";background:var(--rose);color:#fff}}
.asset-stack{{margin-top:18px;display:grid;gap:16px}}
.asset-card{{background:#ffffff;border:1px solid var(--line);border-radius:16px;padding:14px 16px 16px;margin:0;position:relative}}
.asset-card.asset-wide{{margin-left:-12px;margin-right:-12px}}
.asset-image-wrap{{position:relative;background:#fbfaff;border:1px solid var(--line);border-radius:12px;padding:10px;display:flex;justify-content:center}}
.asset-image-wrap img{{max-width:100%;height:auto;display:block;cursor:zoom-in}}
.asset-card figcaption{{padding-top:12px}}
.asset-label{{display:inline-block;font-weight:700;font-size:12px;color:var(--accent);background:var(--accent-soft);padding:3px 10px;border-radius:999px;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:8px}}
.asset-cap{{font-size:14px;color:var(--ink);margin:4px 0 10px}}
.interpretation{{background:#f8f3ff;border:1px dashed var(--accent-pale);border-radius:12px;padding:12px 16px;margin-top:10px}}
.interpretation h4{{margin:0 0 6px;font-size:12px;letter-spacing:0.06em;text-transform:uppercase;color:var(--accent)}}
.interpretation p{{margin:0;font-size:14px;line-height:1.7;color:var(--ink)}}
details.beginner-note{{margin-top:10px;background:#f0f6ff;border:1px solid var(--azure-pale);border-radius:12px;padding:10px 14px}}
details.beginner-note > summary{{cursor:pointer;font-weight:700;color:var(--azure);font-size:13px;list-style:none}}
details.beginner-note > summary::-webkit-details-marker{{display:none}}
details.beginner-note > summary::before{{content:"▶";display:inline-block;margin-right:8px;transition:transform 0.15s ease;font-size:0.8em}}
details.beginner-note[open] > summary::before{{transform:rotate(90deg)}}
details.beginner-note .beginner-body{{margin-top:10px;font-size:13.5px;line-height:1.7}}
.recall-card{{background:var(--mint-soft);border:1px solid #b8d0c0;border-radius:14px;padding:18px 22px 14px;margin:22px 0 4px}}
.recall-tag{{display:inline-block;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;background:var(--mint);color:#fff;padding:3px 10px;border-radius:999px}}
.recall-card h4{{margin:8px 0 4px;font-family:Georgia,serif;font-size:17px;color:#1f3d31}}
.recall-item{{background:#ffffff;border:1px solid #cfe0d4;border-radius:10px;padding:10px 14px;margin-top:10px}}
.recall-item summary{{cursor:pointer;font-weight:600;color:#1f3d31;list-style:none;font-size:14.5px}}
.recall-item summary::-webkit-details-marker{{display:none}}
.recall-item summary::before{{content:"▸";display:inline-block;margin-right:6px;color:var(--mint);transition:transform 150ms ease}}
.recall-item[open] summary::before{{transform:rotate(90deg)}}
.recall-answer{{margin-top:10px;padding:12px 14px;background:#f5fbf6;border-radius:8px}}
.recall-answer p{{margin:0;font-size:14px;line-height:1.65}}
.ref-link{{color:var(--accent);text-decoration:underline dotted;text-decoration-thickness:1px;text-underline-offset:2px;cursor:pointer;font-weight:600}}
.ref-link:hover{{background:var(--accent-soft);border-radius:4px}}
@keyframes flash-target{{0%{{box-shadow:0 0 0 4px var(--accent)}}60%{{box-shadow:0 0 0 4px var(--accent-soft)}}100%{{box-shadow:0 0 0 0 transparent}}}}
.flash-target{{animation:flash-target 1.6s ease-out;border-radius:14px}}
.diss-grid{{display:grid;grid-template-columns:1fr;gap:18px}}
.diss-card{{position:relative;background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:22px 24px 22px 78px;box-shadow:0 6px 20px rgba(80,60,140,0.05)}}
.diss-card.diss-motivation{{}}
.diss-card.diss-observe{{}}
.diss-card.diss-compare{{}}
.diss-card.diss-logic{{}}
.diss-card.diss-verify{{}}
.diss-card.diss-risk{{}}
.diss-card.diss-extend{{}}
.diss-card.diss-summary{{grid-column:1/-1;background:linear-gradient(180deg,#ffffff,#f5edff)}}
.diss-overview-figure{{margin:18px 0 22px;padding:14px;background:#ffffff;border:1px solid var(--line);border-radius:14px;box-shadow:0 6px 18px rgba(80,60,140,0.06)}}
.diss-overview-figure img{{display:block;width:100%;height:auto;border-radius:10px;cursor:zoom-in}}
.diss-overview-figure figcaption{{margin-top:10px;font-size:13.5px;color:var(--muted);line-height:1.55;font-style:italic}}
.diss-step{{position:absolute;top:22px;left:22px;width:42px;height:42px;border-radius:12px;background:var(--accent-soft);color:var(--accent);font-family:Georgia,serif;font-weight:700;font-size:18px;display:flex;align-items:center;justify-content:center}}
.diss-card.diss-observe .diss-step{{background:var(--mint-soft);color:var(--mint)}}
.diss-card.diss-compare .diss-step{{background:var(--amber-soft);color:var(--amber)}}
.diss-card.diss-logic .diss-step{{background:var(--azure-soft);color:var(--azure)}}
.diss-card.diss-verify .diss-step{{background:#ece2f8;color:#7a5db5}}
.diss-card.diss-risk .diss-step{{background:var(--rose-soft);color:var(--rose)}}
.diss-card.diss-extend .diss-step{{background:#dceee8;color:#3aa185}}
.diss-card.diss-summary .diss-step{{background:#e4d9ff;color:#3d2a5e}}
.diss-head h3{{margin:0 0 4px;font-family:Georgia,serif;font-size:18px;color:var(--ink)}}
.diss-lead{{margin:0 0 14px;color:var(--muted);font-size:13.5px;font-style:italic}}
.diss-rows{{margin:0}}
.diss-row{{margin-top:12px;padding:12px 14px;background:rgba(251,250,255,0.7);border-radius:10px;display:flex;flex-direction:column;gap:8px;align-items:flex-start}}
.diss-tag{{align-self:start;justify-self:start;width:max-content;white-space:nowrap;line-height:1.4;display:inline-block;background:var(--accent);color:#fff;font-size:11px;font-weight:700;letter-spacing:0.05em;padding:3px 9px;border-radius:999px;margin-bottom:6px}}
.diss-card.diss-observe .diss-tag{{background:var(--mint)}}
.diss-card.diss-compare .diss-tag{{background:var(--amber)}}
.diss-card.diss-logic .diss-tag{{background:var(--azure)}}
.diss-card.diss-verify .diss-tag{{background:#7a5db5}}
.diss-card.diss-risk .diss-tag{{background:var(--rose)}}
.diss-card.diss-extend .diss-tag{{background:#3aa185}}
.diss-card.diss-summary .diss-tag{{background:#3d2a5e}}
.diss-body{{margin:0;font-size:14.5px;line-height:1.7;color:var(--ink)}}
.diss-rows dd.diss-body{{margin-left:0}}
.fund-panel,.eq-panel,.diagram-panel{{background:var(--paper);border:1px solid var(--line);border-radius:22px;padding:26px 28px;margin-bottom:22px;box-shadow:0 8px 24px rgba(80,60,140,0.05)}}
.panel-title{{margin:0 0 6px;font-family:Georgia,serif;color:var(--accent);font-size:22px}}
.panel-sub{{margin:0 0 16px;color:var(--muted);font-size:14px}}
.fund-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:22px}}
.fund-card{{position:relative;background:#fefcff;border:1px solid var(--line);border-radius:14px;padding:18px 20px 16px}}
.fund-card:nth-child(1){{}}
.fund-card:nth-child(2){{}}
.fund-card:nth-child(3){{}}
.fund-card:nth-child(4){{}}
.fund-card:nth-child(5){{}}
.fund-step{{position:absolute;top:14px;right:16px;font-family:Georgia,serif;font-size:26px;color:var(--muted);opacity:0.45}}
.fund-card h4{{margin:0 0 10px;font-family:Georgia,serif;font-size:17px;color:var(--ink);padding-right:36px}}
.fund-label-tag{{display:inline-block;background:var(--accent-soft);color:var(--accent);font-weight:700;font-size:11px;letter-spacing:0.06em;text-transform:uppercase;padding:3px 9px;border-radius:999px;margin-bottom:6px}}
.fund-body{{margin:0;font-size:14px;line-height:1.72;color:var(--ink)}}
.eq-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:4px}}
.eq-card{{background:linear-gradient(180deg,#fefcff,#f3edff);border:1px solid var(--line);border-radius:16px;padding:18px 20px;box-shadow:0 6px 18px rgba(80,60,140,0.05);min-width:0}}
.eq-head{{display:flex;align-items:center;gap:10px}}
.eq-label{{display:inline-block;background:var(--accent);color:#fff;font-size:11px;font-weight:700;padding:4px 10px;border-radius:999px;letter-spacing:0.06em}}
.eq-display{{margin:14px 0 12px;background:#1f1814;color:#fff5dc;padding:18px 14px;border-radius:12px;font-size:18px;overflow-x:auto}}
.eq-display mjx-container{{color:#fff5dc !important}}
.eq-meta{{display:grid;gap:10px}}
.eq-section{{background:#fefcff;border-radius:10px;padding:10px 12px;border:1px solid #e8def8}}
.eq-section h5{{margin:0 0 4px;font-size:11px;letter-spacing:0.06em;text-transform:uppercase;color:var(--accent)}}
.eq-section p{{margin:0;font-size:13.5px;color:var(--ink);line-height:1.65}}
.eq-grid-detailed{{grid-template-columns:1fr;gap:22px}}
.eq-grid-detailed .eq-display{{font-size:19px;padding:22px 16px}}
.knw-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}
.knw-card{{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:22px 24px;box-shadow:0 6px 20px rgba(80,60,140,0.05)}}
.knw-card h3{{margin:0 0 14px;font-family:Georgia,serif;font-size:18px;color:var(--accent)}}
.knw-label-tag{{display:inline-block;background:var(--accent-soft);color:var(--accent);font-weight:700;font-size:11px;letter-spacing:0.06em;text-transform:uppercase;padding:3px 9px;border-radius:999px;margin-bottom:6px}}
.knw-body{{font-size:14px;line-height:1.72;color:var(--ink)}}
.coach-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}
.coach-card{{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:22px 24px;box-shadow:0 6px 20px rgba(80,60,140,0.05);border-top:4px solid var(--accent)}}
.coach-card.coach-assume{{border-top-color:var(--accent)}}
.coach-card.coach-design{{border-top-color:var(--amber)}}
.coach-card.coach-critique{{border-top-color:var(--rose)}}
.coach-card.coach-extend{{border-top-color:var(--mint)}}
.coach-tag{{display:inline-block;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;padding:3px 10px;border-radius:999px;margin-bottom:8px;background:var(--accent-soft);color:var(--accent)}}
.coach-card.coach-design .coach-tag{{background:var(--amber-soft);color:var(--amber)}}
.coach-card.coach-critique .coach-tag{{background:var(--rose-soft);color:var(--rose)}}
.coach-card.coach-extend .coach-tag{{background:var(--mint-soft);color:var(--mint)}}
.coach-card h3{{margin:0 0 12px;font-family:Georgia,serif;font-size:17px;color:var(--ink)}}
.q-rows{{display:grid;gap:8px}}
.q-rows .recall-item{{margin-top:0}}
.to-top{{position:fixed;bottom:26px;right:26px;width:48px;height:48px;border-radius:50%;background:var(--accent);color:#fff;border:none;cursor:pointer;font-size:22px;line-height:1;font-weight:700;box-shadow:0 8px 22px rgba(80,60,140,0.32);opacity:0;transform:translateY(8px);pointer-events:none;transition:opacity 220ms ease,transform 220ms ease,background 160ms ease;z-index:200}}
.to-top.visible{{opacity:1;transform:translateY(0);pointer-events:auto}}
.to-top:hover{{background:#6e54a3}}
.study-fab{{position:absolute;top:14px;right:14px;display:inline-flex;align-items:center;gap:6px;padding:7px 13px 7px 11px;border-radius:999px;background:rgba(139,117,192,0.94);color:#ffffff;border:1px solid rgba(255,255,255,0.4);font:inherit;font-size:12.5px;font-weight:700;letter-spacing:0.04em;cursor:pointer;box-shadow:0 6px 18px rgba(80,60,140,0.32);backdrop-filter:blur(2px);transition:transform 140ms ease,background 140ms ease;z-index:5}}
.study-fab:hover{{transform:translateY(-1px);background:var(--accent);box-shadow:0 10px 22px rgba(80,60,140,0.42)}}
.study-fab .study-fab-glyph{{display:inline-block;width:18px;height:18px;line-height:18px;border-radius:50%;background:#ffffff;color:var(--accent);font-size:12px;text-align:center;font-weight:800}}
.study-drawer{{position:fixed;top:0;right:0;height:100vh;width:440px;max-width:92vw;background:var(--paper);border-left:1px solid var(--line);box-shadow:-14px 0 40px rgba(20,10,30,0.18);transform:translateX(100%);transition:transform 260ms cubic-bezier(.4,0,.2,1);z-index:1600;display:flex;flex-direction:column}}
.study-drawer.open{{transform:translateX(0)}}
.study-drawer-head{{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;padding:20px 22px 14px;border-bottom:1px solid var(--line)}}
.study-drawer-head .study-label{{display:inline-block;font-size:11px;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;color:var(--accent);background:var(--accent-soft);padding:3px 10px;border-radius:999px;margin-bottom:8px}}
.study-drawer-title{{margin:0;font-family:Georgia,serif;font-size:18px;color:var(--accent);line-height:1.35}}
.study-drawer-close{{border:1px solid var(--line);background:#fff;border-radius:50%;width:34px;height:34px;font-size:18px;line-height:1;color:var(--muted);cursor:pointer;flex-shrink:0}}
.study-drawer-close:hover{{color:var(--accent);border-color:var(--accent)}}
.study-drawer-body{{padding:18px 22px 28px;overflow-y:auto;font-size:14px;line-height:1.7;color:var(--ink)}}
.study-drawer-body .study-section{{margin-bottom:16px}} .study-drawer-body .study-section:last-child{{margin-bottom:0}}
.study-drawer-body .study-label{{display:inline-block;font-size:11px;font-weight:800;letter-spacing:0.06em;text-transform:uppercase;margin:0 0 6px;padding:3px 10px;border-radius:999px}}
.study-drawer-body .s-look .study-label{{background:var(--accent-soft);color:var(--accent)}}
.study-drawer-body .s-num .study-label{{background:var(--amber-soft);color:var(--amber)}}
.study-drawer-body .s-author .study-label{{background:var(--rose-soft);color:var(--rose)}}
.study-drawer-body .s-check .study-label{{background:var(--mint-soft);color:var(--mint)}}
.study-drawer-body .study-section p{{margin:4px 0 0}}
.study-drawer-body .study-section ul{{margin:6px 0 0;padding-left:20px}}
.study-drawer-body .study-section li{{margin-bottom:6px}}
.study-drawer-body .study-section strong{{color:var(--accent)}}
.study-drawer-body .study-num-row{{display:grid;grid-template-columns:minmax(120px,max-content) 1fr;gap:6px 14px;margin-top:8px;padding:10px 12px;background:#fbfaff;border:1px dashed var(--line);border-radius:10px;font-size:13.5px}}
.study-drawer-body .study-num-row > b{{font-family:"Consolas","Courier New",monospace;color:var(--accent);font-weight:800}}
@media (max-width: 520px){{
  .study-drawer-body .study-num-row{{grid-template-columns:1fr}}
}}
.concept-figure{{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:18px 20px;margin:0 0 22px;box-shadow:0 6px 18px rgba(80,60,140,0.05)}}
.concept-figure img{{display:block;max-width:760px;width:100%;height:auto;margin:0 auto;border-radius:12px;border:1px solid var(--line);background:#fbfaff;cursor:zoom-in}}
.concept-figure figcaption{{margin-top:12px;text-align:center}}
.concept-figure figcaption .cf-label{{display:inline-block;font-size:11px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:var(--accent);background:var(--accent-soft);padding:3px 10px;border-radius:999px;margin-bottom:6px}}
.concept-figure figcaption h4{{margin:4px 0 6px;font-family:Georgia,serif;font-size:17px;color:var(--ink)}}
.concept-figure figcaption p{{margin:0;font-size:13.5px;color:var(--muted);line-height:1.65;max-width:640px;margin-left:auto;margin-right:auto}}
{STUDY_CSS}
footer.foot{{text-align:center;margin-top:40px;color:var(--muted);font-size:12.5px}}
@media print{{
  body{{background:white}}
  nav.tabs,.to-top,.study-fab,.study-drawer,.study-drawer-backdrop{{display:none !important}}
  .tab-pane{{display:none !important}} .tab-pane.active{{display:block !important}}
  .paragraph-block,.diss-card,.knw-card,.eq-card,.coach-card,.fund-card,.concept-figure{{break-inside:avoid}}
  .sent.pair-active{{background:transparent;box-shadow:none}}
  canvas,svg{{break-inside:avoid}}
  .eq-display{{background:#f4eeff;color:#1f1814}} .eq-display mjx-container{{color:#1f1814 !important}}
}}
@media (max-width: 640px){{
  .app{{padding:16px 12px 60px}}
  nav.tabs{{flex-wrap:wrap}}
  .tab-btn{{flex:1 1 45%;font-size:13px;padding:8px 6px;min-width:0}}
  .bilingual{{grid-template-columns:1fr}}
  header.hero .meta{{grid-template-columns:1fr}}
  .knw-grid,.coach-grid,.fund-grid,.diss-grid,.eq-grid{{grid-template-columns:1fr}}
  .verdict-grid{{grid-template-columns:1fr}}
  .study-thumbs{{grid-template-columns:repeat(2,minmax(0,1fr))}}
  .study-toolbar{{flex-direction:column;align-items:flex-start}}
  table{{font-size:12px}}
  .tab-pane table{{overflow-x:auto;display:block}}
  svg{{max-width:100%;height:auto;overflow-x:auto}}
}}
.diagram-svg{{cursor:zoom-in}}
.study-drawer-backdrop{{position:fixed;inset:0;background:transparent;z-index:1590;display:none}}
.study-drawer-backdrop.open{{display:block}}
.img-lightbox{{position:fixed;inset:0;background:rgba(20,15,30,0.86);display:none;align-items:center;justify-content:center;z-index:2000;cursor:zoom-out;overflow:hidden}}
.img-lightbox.open{{display:flex}}
.img-lightbox-stage{{position:relative;width:96vw;height:96vh;display:flex;align-items:center;justify-content:center;overflow:hidden}}
.img-lightbox img{{max-width:96vw;max-height:96vh;width:auto;height:auto;display:block;user-select:none;transform-origin:center center;transition:transform 0.18s ease;border-radius:6px;box-shadow:0 12px 48px rgba(0,0,0,0.5)}}
.img-lightbox.dragging img{{transition:none;cursor:grabbing}}
.img-lightbox-caption{{position:absolute;left:50%;bottom:18px;transform:translateX(-50%);max-width:80vw;padding:8px 16px;background:rgba(0,0,0,0.6);color:#fff;font-size:13px;border-radius:999px;text-align:center;pointer-events:none}}
.img-lightbox-close{{position:absolute;top:18px;right:24px;background:rgba(255,255,255,0.12);color:#fff;border:0;font-size:28px;width:42px;height:42px;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center}}
.img-lightbox-close:hover{{background:rgba(255,255,255,0.22)}}
.img-lightbox-hint{{position:absolute;top:18px;left:24px;color:rgba(255,255,255,0.7);font-size:12px;background:rgba(0,0,0,0.4);padding:6px 12px;border-radius:999px;pointer-events:none}}
@media print {{.img-lightbox,.study-drawer,.study-drawer-backdrop,.to-top{{display:none !important}}}}
</style>
</head>
'''

JS = r'''
<script>
(function(){
  const buttons = document.querySelectorAll('.tab-btn');
  const panes = document.querySelectorAll('.tab-pane');
  const scrollMem = {};
  function activate(tab){
    if (document.querySelector('.tab-pane.active')){
      const cur = document.querySelector('.tab-pane.active').id;
      scrollMem[cur] = window.scrollY;
    }
    buttons.forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    panes.forEach(p => p.classList.toggle('active', p.id === tab));
    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise().catch(()=>{});
    }
    window.scrollTo({top: scrollMem[tab] || 0, behavior: 'instant'});
  }
  buttons.forEach(b => b.addEventListener('click', () => activate(b.dataset.tab)));

  function studyNav(tab){ activate(tab); } /*STUDY-NAV*/

  // 문장 호버 페어링 - 위임 방식: 플로팅 리더의 복제 문장에서도 동일하게 동작
  document.addEventListener('mouseover', (e) => {
    const el = e.target.closest('.sent[data-pair]');
    if (!el) return;
    document.querySelectorAll('.sent[data-pair="'+el.dataset.pair+'"]').forEach(s => s.classList.add('pair-active'));
  });
  document.addEventListener('mouseout', (e) => {
    const el = e.target.closest('.sent[data-pair]');
    if (!el) return;
    document.querySelectorAll('.sent[data-pair="'+el.dataset.pair+'"]').forEach(s => s.classList.remove('pair-active'));
  });

  function autoLink(){
    const targetTabFor = (kind) => kind === 'Eq' ? 'tab-knowledge' : 'tab-reading';
    const re = /\b(Eq\.?|Equation|Fig\.?|Figure|Table)\s*(\d+)/g;
    document.querySelectorAll('.tab-pane .col p, .diss-body, .knw-card p, .knw-body, .coach-card li, .coach-card .recall-answer p, .fund-body, .eq-section p, .study-claude-body p, .study-guide, .study-qlist li, .v-claim, .v-note, .alt-card p, .v-claude-body p').forEach(p => {
      const walker = document.createTreeWalker(p, NodeFilter.SHOW_TEXT);
      const texts = [];
      while(walker.nextNode()) texts.push(walker.currentNode);
      texts.forEach(node => {
        if (node.parentNode.tagName === 'A') return;
        const txt = node.nodeValue;
        if (!re.test(txt)) return;
        re.lastIndex = 0;
        const frag = document.createDocumentFragment();
        let last = 0, m;
        while((m = re.exec(txt)) !== null){
          frag.appendChild(document.createTextNode(txt.slice(last, m.index)));
          const a = document.createElement('a');
          a.className = 'ref-link';
          const kind = m[1].startsWith('Eq') || m[1].startsWith('Equation') ? 'Eq' : (m[1].startsWith('T') ? 'Table' : 'Fig');
          a.dataset.targetTab = targetTabFor(kind);
          if (kind === 'Fig') a.dataset.targetId = 'fig_' + m[2];
          else if (kind === 'Table') a.dataset.targetId = 'table_' + m[2];
          else a.dataset.targetId = '';
          a.textContent = m[0];
          a.addEventListener('click', (e) => {
            e.preventDefault();
            activate(a.dataset.targetTab);
            const id = a.dataset.targetId;
            if (id){
              const el = document.getElementById(id);
              if (el){
                setTimeout(()=>{
                  el.scrollIntoView({behavior:'smooth', block:'center'});
                  el.classList.add('flash-target');
                  setTimeout(()=>el.classList.remove('flash-target'), 1700);
                }, 50);
              }
            }
          });
          frag.appendChild(a);
          last = m.index + m[0].length;
        }
        frag.appendChild(document.createTextNode(txt.slice(last)));
        node.parentNode.replaceChild(frag, node);
      });
    });
  }
  autoLink();

  const toTop = document.createElement('button');
  toTop.className = 'to-top';
  toTop.setAttribute('aria-label', '맨 위로');
  toTop.textContent = '↑';
  document.body.appendChild(toTop);
  window.addEventListener('scroll', () => {
    toTop.classList.toggle('visible', window.scrollY > 360);
  });
  toTop.addEventListener('click', () => {
    const cur = document.querySelector('.tab-pane.active');
    if (cur) scrollMem[cur.id] = 0;
    window.scrollTo({top: 0, behavior: 'smooth'});
  });

  // Study guide - right-side slide-in drawer (per §12.5/§12.6 policy)
  const backdrop = document.createElement('div');
  backdrop.className = 'study-drawer-backdrop';
  document.body.appendChild(backdrop);
  const drawer = document.createElement('div');
  drawer.className = 'study-drawer';
  drawer.innerHTML =
    '<div class="study-drawer-head">' +
      '<div><span class="study-label">학습 가이드</span><h3 class="study-drawer-title"></h3></div>' +
      '<button class="study-drawer-close" aria-label="닫기">×</button>' +
    '</div>' +
    '<div class="study-drawer-body"></div>';
  document.body.appendChild(drawer);
  const drawerTitle = drawer.querySelector('.study-drawer-title');
  const drawerBody = drawer.querySelector('.study-drawer-body');
  function closeDrawer(){ drawer.classList.remove('open'); backdrop.classList.remove('open'); }
  drawer.querySelector('.study-drawer-close').addEventListener('click', closeDrawer);
  backdrop.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', e => { if(e.key === 'Escape') closeDrawer(); });

  const STUDY = STUDY_GUIDES_PLACEHOLDER;
  document.querySelectorAll('.study-fab').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const aid = btn.dataset.asset;
      const data = STUDY[aid] || {title:'학습 가이드', html:'<p>이 자산에 대한 가이드는 곧 추가됩니다.</p>'};
      drawerTitle.textContent = data.title;
      drawerBody.innerHTML = data.html;
      drawerBody.scrollTop = 0;
      drawer.classList.add('open');
      backdrop.classList.add('open');
      if (window.MathJax && window.MathJax.typesetPromise) window.MathJax.typesetPromise([drawerBody]).catch(()=>{});
    });
  });

  const lb = document.querySelector('.img-lightbox');
  if (lb) {
    const lbImg = lb.querySelector('img');
    const lbCap = lb.querySelector('.img-lightbox-caption');
    const lbClose = lb.querySelector('.img-lightbox-close');
    let scale = 1, tx = 0, ty = 0, dragging = false, sx = 0, sy = 0;
    function apply(){ lbImg.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')'; }
    function reset(){ scale = 1; tx = 0; ty = 0; apply(); }
    function lbOpen(src, alt){
      lbImg.src = src;
      lbCap.textContent = alt || '';
      reset();
      lb.classList.add('open');
      document.body.style.overflow = 'hidden';
    }
    function lbCloseFn(){
      lb.classList.remove('open');
      var avOpen = document.querySelector('.asset-viewer.open');
      document.body.style.overflow = avOpen ? 'hidden' : '';
    }
    window.__lbOpen = lbOpen;
    lbClose.addEventListener('click', (e) => { e.stopPropagation(); lbCloseFn(); });
    lb.addEventListener('click', (e) => { if (e.target === lb || e.target.classList.contains('img-lightbox-stage')) lbCloseFn(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && lb.classList.contains('open')) lbCloseFn(); });
    lb.addEventListener('wheel', (e) => {
      if (!lb.classList.contains('open')) return;
      e.preventDefault();
      const delta = -e.deltaY * 0.0015;
      const next = Math.max(0.3, Math.min(8, scale * (1 + delta)));
      scale = next;
      apply();
    }, {passive:false});
    lbImg.addEventListener('mousedown', (e) => {
      if (scale <= 1) return;
      e.preventDefault();
      dragging = true;
      sx = e.clientX - tx;
      sy = e.clientY - ty;
      lb.classList.add('dragging');
    });
    window.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      tx = e.clientX - sx;
      ty = e.clientY - sy;
      apply();
    });
    window.addEventListener('mouseup', () => {
      if (!dragging) return;
      dragging = false;
      lb.classList.remove('dragging');
    });
    lbImg.addEventListener('dblclick', () => { scale = scale > 1 ? 1 : 2.5; apply(); });
    document.querySelectorAll('.asset-image-wrap img, .concept-figure img, .diss-overview-figure img, .diagram-svg').forEach(img => {
      img.addEventListener('click', (e) => {
        if (img.closest('.img-lightbox')) return;
        e.preventDefault();
        const src = img.tagName === 'IMG' ? img.src : (img.dataset.src || '');
        const alt = img.alt || img.getAttribute('aria-label') || '';
        if (src) lbOpen(src, alt);
      });
    });
  }

  // ---- Paper Study tab (tab-study): 서술칸 자동 저장 + 잠금 토글 + 근거 점프 ----
  (function(){
    var pane = document.getElementById('tab-study');
    if (!pane) return;
    var SHORT = STUDY_SHORT_PLACEHOLDER;
    var PREFIX = 'prstudy:' + SHORT + ':';
    // 단락 읽음 체크(read:*)는 세션 한정 - 파일을 다시 열면 초기화, 내보내기/가져오기로만 보존
    function storeFor(k){ return k.indexOf('read:') === 0 ? sessionStorage : localStorage; }
    function sget(k){ try { return storeFor(k).getItem(PREFIX + k) || ''; } catch(e){ return ''; } }
    function sset(k, v){ try { storeFor(k).setItem(PREFIX + k, v); } catch(e){} }

    // ---- 도표 뷰어: 썸네일 클릭 → 이미지 + 원문 캡션 + 번역 + 해석 토글 ----
    var AV = AV_DATA_PLACEHOLDER;
    var av = document.querySelector('.asset-viewer');
    function avClose(){
      if (!av) return;
      av.classList.remove('open');
      document.body.style.overflow = '';
    }
    function avOpen(aid){
      if (!av) return;
      var srcEl = document.querySelector('#' + aid + ' img');
      var d = AV[aid] || {};
      var img = av.querySelector('.av-img img');
      img.src = srcEl ? srcEl.src : '';
      img.alt = d.label || aid;
      av.querySelector('.av-label').textContent = d.label || aid.toUpperCase();
      var gbtn = av.querySelector('.av-guide');
      if (gbtn) gbtn.dataset.asset = aid;
      av.querySelector('.av-en p').textContent = d.en || '(원문 캡션 없음)';
      av.querySelector('.av-kr p').textContent = d.kr || '';
      var interp = av.querySelector('details.av-interp');
      if (d.interp){
        interp.style.display = '';
        interp.removeAttribute('open');
        av.querySelector('.av-interp-body').innerHTML = d.interp;
      } else {
        interp.style.display = 'none';
      }
      // 도표 비율에 따라 레이아웃 결정 - 가로형은 텍스트를 아래, 세로/정방형은 우측에
      function setLayout(){
        var wide = img.naturalWidth > 0 && (img.naturalWidth / img.naturalHeight) >= 1.45;
        av.classList.toggle('av-wide', wide);
        av.classList.toggle('av-tall', !wide);
      }
      if (img.complete && img.naturalWidth) setLayout();
      else img.onload = setLayout;
      av.classList.add('open');
      document.body.style.overflow = 'hidden';
    }
    if (av){
      av.querySelector('.av-close').addEventListener('click', avClose);
      av.addEventListener('click', function(e){ if (e.target === av) avClose(); });
      // capture 단계에서 검사 - lightbox·학습 가이드 드로어가 위에 열려 있으면 그 ESC는 그쪽 몫 (한 번에 다 닫힘 방지)
      document.addEventListener('keydown', function(e){
        if (e.key !== 'Escape' || !av.classList.contains('open')) return;
        var lbEl = document.querySelector('.img-lightbox');
        if (lbEl && lbEl.classList.contains('open')) return;
        if (document.querySelector('.study-drawer.open, .study-modal.open')) return;
        avClose();
      }, true);
      // 뷰어 안 이미지 클릭 → 기존 lightbox로 휠 줌/드래그 확대
      av.querySelector('.av-img img').addEventListener('click', function(){
        if (window.__lbOpen && this.src) window.__lbOpen(this.src, av.querySelector('.av-label').textContent);
      });
      // 학습 가이드 드로어(.study-drawer 또는 구세대 .study-modal)가 우측에 열리면 뷰어를 왼쪽으로 비킴
      var drawerEl = document.querySelector('.study-drawer, .study-modal');
      if (drawerEl){
        new MutationObserver(function(){
          av.classList.toggle('av-shift', drawerEl.classList.contains('open') && av.classList.contains('open'));
        }).observe(drawerEl, {attributes: true, attributeFilter: ['class']});
      }
    }

    // 썸네일: Translation 탭에 이미 임베드된 동일 자산에서 src 복사 (중복 임베드 방지) + 클릭 시 뷰어
    pane.querySelectorAll('img[data-thumb-of]').forEach(function(im){
      var srcEl = document.querySelector('#' + im.dataset.thumbOf + ' img');
      if (srcEl) im.src = srcEl.src;
      im.addEventListener('click', function(){ avOpen(im.dataset.thumbOf); });
    });

    // ---- 단락 플로팅 리더: 본문 보기 칩 → 단락을 하나씩 읽고 체크(✓) ----
    var reader = document.querySelector('.para-reader');
    var readerList = [], readerIdx = -1, readerTitle = '';
    function refreshReadChips(){
      pane.querySelectorAll('.read-group').forEach(function(g){
        var chips = g.querySelectorAll('.read-chip'), done = 0;
        chips.forEach(function(c){
          var ok = sget('read:' + c.dataset.readPid) === '1';
          c.classList.toggle('read-done', ok);
          if (ok) done++;
        });
        var prog = g.querySelector('.read-progress');
        if (prog){
          prog.textContent = done + '/' + chips.length;
          prog.classList.toggle('all-done', chips.length > 0 && done === chips.length);
        }
      });
    }
    /* ==== PR_ASSET_CHIPS_BEGIN v1 (tools/reader_asset_chip.py) ==== */
    /* 리더는 .asset-stack 을 화면에 싣지 않는다(좁은 패널 + base64 이미지).
       대신 그 자리에 자산 칩을 남기고, 칩을 누르면 Translation 탭의 원본 카드로 점프한다. */
    (function(){
      if (document.getElementById('pr-asset-chip-style')) return;
      var st = document.createElement('style');
      st.id = 'pr-asset-chip-style';
      st.textContent = ".pr-asset-chips{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 4px}"
        + ".pr-asset-chip{display:inline-flex;align-items:center;gap:6px;max-width:100%;padding:4px 11px;"
        + "border:1px solid var(--line,#ecedf2);border-radius:999px;background:var(--accent-soft,#f1f2f8);"
        + "color:var(--accent,#5e6488);font-family:inherit;font-size:12px;line-height:1.45;cursor:pointer;text-align:left}"
        + ".pr-asset-chip:hover{border-color:var(--accent,#5e6488)}"
        + ".pr-asset-chip:focus-visible{outline:2px solid var(--accent,#5e6488);outline-offset:2px}"
        + ".pr-asset-chip .prac-name{font-weight:700;white-space:nowrap}"
        + ".pr-asset-chip .prac-cap{color:var(--muted,#9aa0ac);max-width:220px;overflow:hidden;"
        + "text-overflow:ellipsis;white-space:nowrap}"
        + "@media print{.pr-asset-chips{display:none}}";
      (document.head || document.documentElement).appendChild(st);
    })();
    /* 알려진 자산 접두사만 칩으로 만든다. 저장소 실측 접두사는 fig_ / table_ / algo_ / box_ 이고,
       나머지는 표기 흔들림에 대비한 여유분이다. 모르는 접두사면 '' 를 돌려 칩을 만들지 않는다
       (단락 id 'p10' 같은 것이 자산으로 오인되는 것을 막는다). */
    function prAssetLabel(aid){
      var m = String(aid || '').match(/^([A-Za-z]+)[ _-]*([0-9]+[A-Za-z]?)$/);
      if (!m) return '';
      var map = {fig:'Figure', figure:'Figure', table:'Table', tab:'Table', tbl:'Table',
                 alg:'Algorithm', algo:'Algorithm', algorithm:'Algorithm', box:'Box',
                 eq:'Equation', equation:'Equation', chart:'Chart'};
      var name = map[m[1].toLowerCase()];
      if (!name) return '';
      return name + ' ' + m[2];
    }
    function prAssetCap(scope){
      if (!scope || !scope.querySelector) return '';
      /* 쉼표 셀렉터는 문서 순서로 뽑히므로(figcaption 이 .asset-cap 을 감싸는 세대가 있다)
         우선순위대로 하나씩 조회한다. */
      var sels = ['.asset-cap', '.asset-cap-kr', '.asset-cap-en', '.asset-caption', 'figcaption'];
      var el = null;
      for (var s = 0; s < sels.length; s++){ el = scope.querySelector(sels[s]); if (el) break; }
      if (!el) return '';
      var cp = el.cloneNode(true);
      var labs = cp.querySelectorAll('.asset-label, .study-fab');   /* "FIG 1" 배지·버튼 텍스트 제외 */
      for (var q = 0; q < labs.length; q++){ if (labs[q].parentNode) labs[q].parentNode.removeChild(labs[q]); }
      var t = cp.textContent || '';
      t = t.replace(/\s+/g, ' ').trim();
      t = t.replace(/^(figure|fig\.?|table|algorithm|alg\.?|box|equation|그림|표)\s*[0-9]+[A-Za-z]?\s*[:.\-]?\s*/i, '');
      if (/^[A-Za-z]+[ _-]*[0-9]+[A-Za-z]?$/.test(t)) return '';   // figcaption 이 자산 id 그대로인 세대
      if (t.length > 30) t = t.slice(0, 30) + '…';
      return t;
    }
    function prAssetChipify(root){
      if (!root || !root.querySelectorAll) return;
      var stacks = root.querySelectorAll('.asset-stack');
      for (var i = 0; i < stacks.length; i++){
        var stack = stacks[i];
        if (!stack.parentNode) continue;
        var seen = {}, items = [];
        var cands = stack.querySelectorAll('[data-asset-id],[data-asset],[id]');
        for (var j = 0; j < cands.length; j++){
          var el = cands[j];
          var aid = el.getAttribute('data-asset-id') || el.getAttribute('data-asset') || el.getAttribute('id') || '';
          var lab = prAssetLabel(aid);
          if (!lab) continue;
          if (seen[aid]) continue;
          if (!document.getElementById(aid)) continue;            // Translation 탭에 점프 대상이 있어야 칩을 만든다
          seen[aid] = 1;
          var scope = (el.closest && (el.closest('figure') || el.closest('.asset-card'))) || el.parentNode || el;
          items.push({aid: aid, lab: lab, scope: scope});
        }
        if (!items.length){ stack.parentNode.removeChild(stack); continue; }
        var wrap = document.createElement('div');
        wrap.className = 'pr-asset-chips';
        for (var k = 0; k < items.length; k++){
          var lab = items[k].lab;
          var cap = prAssetCap(items[k].scope);
          var b = document.createElement('button');
          b.type = 'button';
          b.className = 'pr-asset-chip';
          b.setAttribute('data-pr-asset', items[k].aid);
          b.setAttribute('aria-label', lab + ' - Translation 탭에서 보기');
          b.setAttribute('title', lab + ' - Translation 탭에서 보기');
          var sn = document.createElement('span');
          sn.className = 'prac-name';
          sn.textContent = lab;
          b.appendChild(sn);
          if (cap){
            var sc = document.createElement('span');
            sc.className = 'prac-cap';
            sc.textContent = cap;
            b.appendChild(sc);
          }
          wrap.appendChild(b);
        }
        stack.parentNode.replaceChild(wrap, stack);
      }
    }
    document.addEventListener('click', function(e){
      var t = e.target, chip = null;
      while (t && t.nodeType === 1){
        if (t.classList && t.classList.contains('pr-asset-chip')){ chip = t; break; }
        t = t.parentNode;
      }
      if (!chip) return;
      var aid = chip.getAttribute('data-pr-asset');
      if (!aid) return;
      e.preventDefault();
      e.stopPropagation();
      readerClose();
      jumpToRef(aid);
    }, true);
    /* ==== PR_ASSET_CHIPS_END ==== */
    function readerRender(){
      var pid = readerList[readerIdx];
      var body = reader.querySelector('.pr-body');
      var src = document.getElementById(pid);
      if (!src){ body.innerHTML = '<p>단락을 찾을 수 없습니다.</p>'; return; }
      var clone = src.cloneNode(true);
      clone.removeAttribute('id');
      clone.querySelectorAll('.pid-tag').forEach(function(n){ n.remove(); });
      prAssetChipify(clone);
      clone.querySelectorAll('[id]').forEach(function(n){ n.removeAttribute('id'); });
      body.innerHTML = '';
      body.appendChild(clone);
      body.scrollTop = 0;
      reader.querySelector('.pr-title').textContent = readerTitle;
      reader.querySelector('.pr-pos').textContent = '단락 ' + (readerIdx + 1) + ' / ' + readerList.length;
      reader.querySelector('.pr-prev').disabled = readerIdx <= 0;
      reader.querySelector('.pr-next').disabled = readerIdx >= readerList.length - 1;
      if (window.MathJax && window.MathJax.typesetPromise) window.MathJax.typesetPromise([body]).catch(function(){});
      sset('read:' + pid, '1');
      refreshReadChips();
      hlApply();
    }
    function readerOpen(pid, list, title){
      if (!reader) return;
      readerList = (list && list.length) ? list : [pid];
      readerIdx = Math.max(0, readerList.indexOf(pid));
      readerTitle = title || '본문';
      reader.classList.add('open');
      document.body.style.overflow = 'hidden';
      readerRender();
    }
    function readerClose(){
      if (!reader) return;
      reader.classList.remove('open');
      document.body.style.overflow = document.querySelector('.asset-viewer.open') ? 'hidden' : '';
    }
    if (reader){
      reader.querySelector('.pr-close').addEventListener('click', readerClose);
      reader.addEventListener('click', function(e){ if (e.target === reader) readerClose(); });
      reader.querySelector('.pr-prev').addEventListener('click', function(){
        if (readerIdx > 0){ readerIdx--; readerRender(); }
      });
      reader.querySelector('.pr-next').addEventListener('click', function(){
        if (readerIdx < readerList.length - 1){ readerIdx++; readerRender(); }
      });
      reader.querySelector('.pr-open-translation').addEventListener('click', function(){
        var pid = readerList[readerIdx];
        readerClose();
        jumpToRef(pid);
      });
      document.addEventListener('keydown', function(e){
        if (!reader.classList.contains('open')) return;
        var lbEl = document.querySelector('.img-lightbox');
        if (lbEl && lbEl.classList.contains('open')) return;
        if (e.key === 'Escape') readerClose();
        else if (e.key === 'ArrowLeft' && readerIdx > 0){ readerIdx--; readerRender(); }
        else if (e.key === 'ArrowRight' && readerIdx < readerList.length - 1){ readerIdx++; readerRender(); }
      }, true);
    }
    pane.querySelectorAll('[data-read-pid]').forEach(function(chip){
      chip.addEventListener('click', function(){
        var pid = chip.dataset.readPid;
        var group = chip.closest('.read-group');
        if (!group){
          var scopes = [chip.closest('.study-step'), pane];
          scopes.forEach(function(scope){
            if (group || !scope) return;
            scope.querySelectorAll('.read-group').forEach(function(g){
              if (!group && g.querySelector('.read-chip[data-read-pid="' + pid + '"]')) group = g;
            });
          });
        }
        var list = [pid], title = '';
        if (group){
          list = Array.prototype.map.call(group.querySelectorAll('.read-chip'), function(c){ return c.dataset.readPid; });
          title = group.querySelector('.read-group-label').textContent;
        }
        readerOpen(pid, list, title);
      });
    });
    refreshReadChips();


    // ---- 문장 형광펜: 문장 클릭으로 하이라이트 토글 - 리더·Translation 공통, 내보내기에 포함 ----
    function hlApply(){
      document.querySelectorAll('.sent[data-pair]').forEach(function(s){
        s.classList.toggle('user-hl', sget('hl:' + s.dataset.pair) === '1');
      });
    }
    document.addEventListener('click', function(e){
      var s = e.target.closest('.sent[data-pair]');
      if (!s) return;
      if (e.target.closest('a, button')) return;           // ref-link 등 클릭은 링크 우선
      var selObj = window.getSelection();
      if (selObj && !selObj.isCollapsed) return;            // 텍스트 드래그 선택 중이면 무시
      var sid = s.dataset.pair;
      var on = sget('hl:' + sid) !== '1';
      try {
        if (on) localStorage.setItem(PREFIX + 'hl:' + sid, '1');
        else localStorage.removeItem(PREFIX + 'hl:' + sid);
      } catch(err){}
      hlApply();
    });
    hlApply();

    // ---- 돌아가기 버튼: 원문으로 점프한 뒤 하단 중앙에 나타난다 ----
    var ret = document.createElement('button');
    ret.className = 'study-return';
    ret.type = 'button';
    ret.textContent = '↩ Paper Study로 돌아가기';
    document.body.appendChild(ret);
    function showReturn(){ ret.classList.add('visible'); }
    function hideReturn(){ ret.classList.remove('visible'); }
    ret.addEventListener('click', function(){ hideReturn(); studyNav('tab-study'); });
    window.addEventListener('hashchange', function(){ if (location.hash === '#tab-study') hideReturn(); });
    document.querySelectorAll('.tab-btn').forEach(function(b){
      b.addEventListener('click', function(){ if (b.dataset.tab === 'tab-study') hideReturn(); });
    });

    // ---- 통합 점프: 근거 칩(data-ev) + 위치 보기 칩(data-view) → Translation 탭 + 하이라이트 ----
    function jumpToRef(ref){
      var el = document.getElementById(ref);
      var isSent = false;
      if (!el){
        el = document.querySelector('#tab-reading .sent[data-pair="' + ref + '"]');
        isSent = true;
      }
      if (!el) return;
      studyNav('tab-reading');
      showReturn();
      setTimeout(function(){
        var isSection = !isSent && el.classList.contains('section');
        el.scrollIntoView({behavior:'smooth', block: isSection ? 'start' : 'center'});
        if (isSent){
          var twins = document.querySelectorAll('.sent[data-pair="' + ref + '"]');
          twins.forEach(function(s){ s.classList.add('ev-hl'); });
          setTimeout(function(){ twins.forEach(function(s){ s.classList.remove('ev-hl'); }); }, 3600);
        } else if (isSection){
          var head = el.querySelector('.section-header') || el;
          head.classList.add('flash-target');
          setTimeout(function(){ head.classList.remove('flash-target'); }, 1700);
        } else {
          el.classList.add('flash-target');
          setTimeout(function(){ el.classList.remove('flash-target'); }, 1700);
        }
      }, 120);
    }
    pane.querySelectorAll('[data-ev]').forEach(function(chip){
      chip.addEventListener('click', function(){ jumpToRef(chip.dataset.ev); });
    });

    // 서론 끝 "Paper Study로 돌아가기" 버튼 (Translation 탭 안)
    document.querySelectorAll('.study-goto').forEach(function(b){
      b.addEventListener('click', function(){ hideReturn(); studyNav('tab-study'); });
    });

    // data-skey는 쉼표 목록 가능 (예: Gap의 3분할 서술칸) - 합산 글자 수로 잠금 판단
    function refreshReveal(skey){
      pane.querySelectorAll('.study-reveal').forEach(function(box){
        var keys = box.dataset.skey.split(',');
        if (keys.indexOf(skey) < 0) return;
        var btn = box.querySelector('.study-reveal-btn');
        var min = parseInt(box.dataset.min || '0', 10);
        var total = keys.reduce(function(n, k){ return n + sget(k).trim().length; }, 0);
        var ok = total >= min;
        btn.disabled = !ok;
        var lock = btn.querySelector('.srb-lock');
        if (lock) lock.style.display = ok ? 'none' : '';
      });
    }
    function refreshMirrors(){
      pane.querySelectorAll('[data-mirror]').forEach(function(m){
        var v = sget(m.dataset.mirror).trim();
        if (v){ m.textContent = v; m.classList.remove('v-empty'); }
        else { m.innerHTML = '<em>Step 5의 서술칸에 결론을 쓰면 여기 자동으로 나타납니다.</em>'; m.classList.add('v-empty'); }
      });
    }
    var saveTimers = {};
    pane.querySelectorAll('.study-write').forEach(function(ta){
      var skey = ta.dataset.skey;
      ta.value = sget(skey);
      var wrap = ta.closest('.study-write-wrap');
      var cnt = wrap.querySelector('.sw-count');
      var savedEl = wrap.querySelector('.sw-saved');
      function paint(){ cnt.textContent = ta.value.trim().length + '자'; }
      paint();
      refreshReveal(skey);
      ta.addEventListener('input', function(){
        paint();
        clearTimeout(saveTimers[skey]);
        saveTimers[skey] = setTimeout(function(){
          sset(skey, ta.value);
          var d = new Date();
          savedEl.textContent = '저장됨 ' + d.getHours() + ':' + ('0' + d.getMinutes()).slice(-2);
          refreshReveal(skey);
          refreshMirrors();
        }, 400);
      });
    });
    refreshMirrors();

    pane.querySelectorAll('.study-reveal').forEach(function(box){
      var btn = box.querySelector('.study-reveal-btn');
      var panel = box.querySelector('.study-claude');
      function toggle(force){
        var show = (force !== undefined) ? force : panel.hidden;
        panel.hidden = !show;
        box.classList.toggle('open', show);
        if (show && window.MathJax && window.MathJax.typesetPromise) window.MathJax.typesetPromise([panel]).catch(function(){});
      }
      btn.addEventListener('click', function(){ toggle(); });
      var skip = box.querySelector('.study-skip');
      if (skip) skip.addEventListener('click', function(){ toggle(true); });
    });

    pane.querySelectorAll('.study-checkbox').forEach(function(cb){
      var k = 'chk:' + cb.dataset.ckey;
      cb.checked = sget(k) === '1';
      cb.addEventListener('change', function(){ sset(k, cb.checked ? '1' : '0'); });
    });

    function allNotes(){
      var out = {};
      [localStorage, sessionStorage].forEach(function(st){
        for (var i = 0; i < st.length; i++){
          var k = st.key(i);
          if (k && k.indexOf(PREFIX) === 0) out[k.slice(PREFIX.length)] = st.getItem(k);
        }
      });
      return out;
    }
    // ---- 학습 메모: 플로팅 버튼 + 자유 서식 메모장 (쓰는 대로 자동 저장 → 내보내기에 포함, Q&A 재료) ----
    var memoFab = document.createElement('button');
    memoFab.className = 'memo-fab';
    memoFab.type = 'button';
    memoFab.innerHTML = '메모<span class="memo-dot" hidden></span>';
    document.body.appendChild(memoFab);
    function placeMemoFab(){
      var tb = document.querySelector('.topbar') || document.querySelector('nav.tabs');
      var y = tb ? tb.getBoundingClientRect().bottom + 18 : 150;
      memoFab.style.top = y + 'px';
    }
    placeMemoFab();
    window.addEventListener('resize', placeMemoFab);

    var md = document.createElement('div');
    md.className = 'memo-drawer';
    md.innerHTML =
      '<div class="memo-head"><span class="memo-title">학습 메모</span>' +
      '<button class="memo-close" type="button" aria-label="닫기">×</button></div>' +
      '<p class="memo-hint">자유롭게 적는 메모장 - 쓰는 대로 자동 저장됩니다. 내 노트 내보내기 시 파일에 함께 담기고, 여기 남긴 질문들은 나중에 Q &amp; A 탭을 만들 때 재료가 됩니다.</p>' +
      '<textarea class="memo-pad" placeholder="궁금한 것, 이해 안 되는 것, 나중에 확인할 것…"></textarea>' +
      '<div class="memo-status"><span class="memo-len">0자</span><span class="memo-saved"></span></div>';
    document.body.appendChild(md);
    var memoPad = md.querySelector('.memo-pad');
    var memoLen = md.querySelector('.memo-len');
    var memoSaved = md.querySelector('.memo-saved');
    var memoDot = memoFab.querySelector('.memo-dot');
    function memoPaint(){
      memoLen.textContent = memoPad.value.trim().length + '자';
      memoDot.hidden = memoPad.value.trim().length === 0;
    }
    (function memoLoad(){
      var v = sget('memo');
      if (v && v.charAt(0) === '['){ // 구버전(항목 배열) → 텍스트 마이그레이션
        try {
          var arr = JSON.parse(v);
          if (Array.isArray(arr)){
            v = arr.map(function(m){ return m.q; }).join('\n\n');
            sset('memo', v);
          }
        } catch(e){}
      }
      memoPad.value = v || '';
      memoPaint();
    })();
    var memoTimer;
    memoPad.addEventListener('input', function(){
      memoPaint();
      clearTimeout(memoTimer);
      memoTimer = setTimeout(function(){
        sset('memo', memoPad.value);
        var d = new Date();
        memoSaved.textContent = '자동 저장됨 ' + d.getHours() + ':' + ('0' + d.getMinutes()).slice(-2);
      }, 400);
    });
    function memoOpen(open){
      md.classList.toggle('open', open);
      memoFab.style.display = open ? 'none' : '';
      if (open) memoPad.focus();
    }
    memoFab.addEventListener('click', function(){ memoOpen(true); });
    md.querySelector('.memo-close').addEventListener('click', function(){ memoOpen(false); });

    // ---- 노트 파일 저장/불러오기 - 지정 폴더(study/) 핸들을 IndexedDB에 기억해 다이얼로그 최소화 ----
    function idbOpen(){
      return new Promise(function(res, rej){
        var r = indexedDB.open('prstudy-fs', 1);
        r.onupgradeneeded = function(){ r.result.createObjectStore('handles'); };
        r.onsuccess = function(){ res(r.result); };
        r.onerror = function(){ rej(r.error); };
      });
    }
    function idbGet(k){
      return idbOpen().then(function(db){
        return new Promise(function(res, rej){
          var t = db.transaction('handles').objectStore('handles').get(k);
          t.onsuccess = function(){ res(t.result || null); };
          t.onerror = function(){ rej(t.error); };
        });
      });
    }
    function idbSet(k, v){
      return idbOpen().then(function(db){
        return new Promise(function(res, rej){
          var t = db.transaction('handles', 'readwrite').objectStore('handles').put(v, k);
          t.onsuccess = function(){ res(); };
          t.onerror = function(){ rej(t.error); };
        });
      });
    }
    function ensurePerm(h, mode){
      if (!h.queryPermission) return Promise.resolve(true);
      return h.queryPermission({mode: mode}).then(function(p){
        if (p === 'granted') return true;
        return h.requestPermission({mode: mode}).then(function(p2){ return p2 === 'granted'; });
      });
    }
    function getDir(){ return idbGet('dir:' + SHORT).catch(function(){ return null; }); }
    function pickDir(){
      return window.showDirectoryPicker({mode: 'readwrite'}).then(function(dir){
        return idbSet('dir:' + SHORT, dir).then(function(){ return dir; });
      });
    }
    function applyNotes(text){
      try {
        var data = JSON.parse(text);
        if (data.paper && data.paper !== SHORT && !confirm('이 파일은 "' + data.paper + '" 논문의 노트입니다. 그래도 불러올까요?')) return;
        var notes = data.notes || data;
        Object.keys(notes).forEach(function(k){ sset(k, String(notes[k])); });
        location.reload();
      } catch(e){ alert('JSON을 읽을 수 없습니다: ' + e.message); }
    }

    var exBtn = document.getElementById('study-export');
    function exFlash(msg){
      if (!exBtn) return;
      exBtn.textContent = msg;
      setTimeout(function(){ exBtn.textContent = '내 노트 내보내기'; }, 3200);
    }
    if (exBtn) exBtn.addEventListener('click', async function(){
      var d = new Date();
      var ymd = String(d.getFullYear()).slice(2) + ('0' + (d.getMonth() + 1)).slice(-2) + ('0' + d.getDate()).slice(-2);
      var fname = SHORT + '_study_notes_' + ymd + '.json';
      var payload = JSON.stringify({paper: SHORT, exported: d.toISOString(), notes: allNotes()}, null, 2);
      // 1순위: 기억된 폴더에 바로 저장 (최초 1회만 폴더 지정)
      try {
        var dir = await getDir();
        if (!dir && window.showDirectoryPicker) dir = await pickDir();
        if (dir && await ensurePerm(dir, 'readwrite')){
          var fh = await dir.getFileHandle(fname, {create: true});
          var w = await fh.createWritable();
          await w.write(payload);
          await w.close();
          exFlash('저장됨 - ' + (dir.name ? dir.name + '/' : '') + fname);
          return;
        }
      } catch(e){ if (e && e.name === 'AbortError') return; }
      // 폴백: 다운로드 폴더
      var blob = new Blob([payload], {type: 'application/json'});
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = fname;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function(){ URL.revokeObjectURL(a.href); }, 4000);
      exFlash('다운로드 폴더에 저장됨 - ' + fname);
    });

    // 저장 위치 (재)지정
    var sdBtn = document.getElementById('study-setdir');
    if (sdBtn) sdBtn.addEventListener('click', async function(){
      if (!window.showDirectoryPicker){ alert('이 브라우저는 폴더 지정을 지원하지 않습니다 - Chrome/Edge를 권장합니다.'); return; }
      try {
        var dir = await pickDir();
        sdBtn.textContent = '지정됨 - ' + dir.name;
        setTimeout(function(){ sdBtn.textContent = '저장 위치 변경'; }, 3200);
      } catch(e){}
    });

    // 가져오기 - 기억된 폴더의 노트 목록을 페이지 안 선택창으로 (없으면 파일 선택 폴백)
    var fileIn = document.createElement('input');
    fileIn.type = 'file';
    fileIn.accept = '.json,application/json';
    fileIn.style.display = 'none';
    document.body.appendChild(fileIn);
    fileIn.addEventListener('change', function(){
      var f = fileIn.files && fileIn.files[0];
      if (!f) return;
      var r = new FileReader();
      r.onload = function(){ applyNotes(r.result); };
      r.readAsText(f);
    });
    var np = document.createElement('div');
    np.className = 'notes-picker';
    np.innerHTML =
      '<div class="np-panel">' +
        '<div class="np-head"><span class="np-title">노트 불러오기</span><span class="np-dir"></span>' +
        '<button class="np-close" type="button" aria-label="닫기">×</button></div>' +
        '<div class="np-list"></div>' +
        '<div class="np-foot"><button class="np-file" type="button">다른 파일 선택…</button></div>' +
      '</div>';
    document.body.appendChild(np);
    function npClose(){ np.classList.remove('open'); }
    np.querySelector('.np-close').addEventListener('click', npClose);
    np.addEventListener('click', function(e){ if (e.target === np) npClose(); });
    np.querySelector('.np-file').addEventListener('click', function(){ npClose(); fileIn.value = ''; fileIn.click(); });
    document.addEventListener('keydown', function(e){
      if (e.key === 'Escape' && np.classList.contains('open')) npClose();
    }, true);
    async function listNotes(dir){
      var files = [];
      for await (var entry of dir.values()){
        if (entry.kind === 'file' && /\.json$/i.test(entry.name)){
          var f = await entry.getFile();
          files.push({name: entry.name, mtime: f.lastModified, handle: entry});
        }
      }
      files.sort(function(a, b){ return a.name < b.name ? 1 : -1; });
      return files;
    }
    var imBtn = document.getElementById('study-import');
    if (imBtn) imBtn.addEventListener('click', async function(){
      try {
        var dir = await getDir();
        if (dir && await ensurePerm(dir, 'read')){
          var files = await listNotes(dir);
          if (files.length){
            np.querySelector('.np-dir').textContent = (dir.name || '') + ' · ' + files.length + '개';
            var list = np.querySelector('.np-list');
            list.innerHTML = '';
            files.forEach(function(f){
              var btn = document.createElement('button');
              btn.className = 'np-item';
              btn.type = 'button';
              var dt = new Date(f.mtime);
              btn.innerHTML = '<b>' + f.name + '</b><span>' + dt.toLocaleString() + '</span>';
              btn.addEventListener('click', function(){
                f.handle.getFile().then(function(file){ return file.text(); }).then(function(text){
                  npClose();
                  applyNotes(text);
                });
              });
              list.appendChild(btn);
            });
            np.classList.add('open');
            return;
          }
        }
      } catch(e){}
      fileIn.value = '';
      fileIn.click();
    });
    var clBtn = document.getElementById('study-clear');
    if (clBtn) clBtn.addEventListener('click', function(){
      if (!confirm('이 논문의 Paper Study 메모를 모두 지울까요? 되돌릴 수 없습니다.')) return;
      Object.keys(allNotes()).forEach(function(k){
        try { localStorage.removeItem(PREFIX + k); sessionStorage.removeItem(PREFIX + k); } catch(e){}
      });
      location.reload();
    });
  })();
})();
</script>
'''

STUDY_MODALS = analysis.get("study_modals", {})

def _render_study_html(sm: dict) -> str:
    rows = []
    for item in sm.get("nums", []):
        if isinstance(item, dict):
            lbl = item.get("label", "")
            val = item.get("value", "")
            note = item.get("note", "")
            note_html = f' <em>{esc(note)}</em>' if note else ""
            rows.append(f'<div class="study-num-row"><b>{esc(lbl)}</b><span>{esc(val)}{note_html}</span></div>')
        else:
            lbl, val = item[0], item[1]
            rows.append(f'<div class="study-num-row"><b>{esc(lbl)}</b><span>{esc(val)}</span></div>')
    nums_html = "".join(rows)
    check_html = "".join(f"<li>{c}</li>" for c in sm.get("check", []))
    return (
        '<div class="study-section s-look">'
        '<span class="study-label">▸ 어디를 먼저 볼까</span>'
        f'<p>{sm.get("look", "")}</p>'
        '</div>'
        '<div class="study-section s-num">'
        '<span class="study-label">▸ 결정적 숫자</span>'
        f'{nums_html}'
        '</div>'
        '<div class="study-section s-author">'
        '<span class="study-label">▸ 저자가 말하는 것</span>'
        f'<p>{sm.get("author", "")}</p>'
        '</div>'
        '<div class="study-section s-check">'
        '<span class="study-label">▸ 학습 체크포인트</span>'
        f'<ul>{check_html}</ul>'
        '</div>'
    )

study = {}
for aid in ASSET_DATAURI:
    label = aid.replace("_", " ").upper()
    sm = STUDY_MODALS.get(aid)
    if sm:
        study[aid] = {"title": sm.get("title", f"학습 가이드 - {label}"),
                       "html": _render_study_html(sm)}
    else:
        study[aid] = {"title": f"학습 가이드 - {label}",
                       "html": '<div class="study-section s-look"><span class="study-label">▸ 준비 중</span><p>이 자산의 학습 가이드는 곧 추가됩니다.</p></div>'}

study_json = json.dumps(study, ensure_ascii=False)
meta_early = config.get("metadata") or config.get("meta")
JS_FINAL = (JS.replace("STUDY_GUIDES_PLACEHOLDER", study_json)
              .replace("STUDY_SHORT_PLACEHOLDER", json.dumps(meta_early["short_name"], ensure_ascii=False))
              .replace("AV_DATA_PLACEHOLDER", json.dumps(AV_DATA, ensure_ascii=False)))

BODY = f'''<body>
<main class="app">
  <header class="hero">
    <span class="brand-tag">Paper Review · v3</span>
    <h1>{esc(meta["title"])}</h1>
    <p class="subtitle">{esc(meta["short_name"])} - {esc(meta["venue"])} ({meta["year"]})</p>
    <div class="meta">
      <span class="meta-item"><strong>Authors</strong>{esc(meta["authors"])}</span>
      <span class="meta-item"><strong>Affiliation</strong>{esc(meta["affiliation"])}</span>
      <span class="meta-item"><strong>Source</strong>{esc(meta["source_pdf"])}</span>
    </div>
  </header>
  <nav class="tabs" role="tablist">
    <button class="tab-btn active" data-tab="tab-reading">① 원문 / 번역</button>
    <button class="tab-btn" data-tab="tab-study">①′ Paper Study</button>
    <button class="tab-btn" data-tab="tab-dissection">② Paper Dissection</button>
    <button class="tab-btn" data-tab="tab-knowledge">③ Background &amp; 핵심 수식</button>
    <button class="tab-btn" data-tab="tab-questions">④ Questions &amp; Diagrams</button>
    <button class="tab-btn" data-tab="tab-simulator">⑤ Simulator &amp; Code</button>
    <button class="tab-btn" data-tab="tab-qa">⑥ 학습 기초 Q &amp; A</button>
  </nav>
  <section id="tab-reading" class="tab-pane active">
    <div class="tab-intro">
      <h2>원문 ↔ 번역 정렬 뷰</h2>
      <p>문장 단위 hover로 원문과 번역이 짝을 이룬다. 도표 아래 해석/초보자 토글, 우측 슬라이드 학습 가이드가 함께 묶여 있다.</p>
    </div>
{tab_reading}
  </section>
  <section id="tab-study" class="tab-pane">
{tab_study}
  </section>
  <section id="tab-dissection" class="tab-pane">
{tab_dissection}
  </section>
  <section id="tab-knowledge" class="tab-pane">
{tab_knowledge}
  </section>
  <section id="tab-questions" class="tab-pane">
{tab_questions}
  </section>
  <section id="tab-simulator" class="tab-pane">
{tab_simulator}
  </section>
  <section id="tab-qa" class="tab-pane">
{tab_qa}
  </section>
  <footer class="foot">
    <p>Paper Review HTML · v3 · CARES (ACL 2026 Long Papers · Oral · arXiv 2510.19496 · 2026-05-31) - 질의 조건부로 입력 해상도를 토큰화 이전에 골라, VLM 동결 plug-in으로 정확도 유지 + prefill 연산 평균 최대 78% 절감 · 코드 github.com/mkimhi/CARES</p>
  </footer>
</main>
<div class="para-reader" role="dialog" aria-label="본문 단락 읽기" aria-hidden="true">
  <div class="pr-panel">
    <div class="pr-head">
      <span class="pr-title"></span>
      <span class="pr-pos"></span>
      <button class="pr-close" type="button" aria-label="닫기">×</button>
    </div>
    <div class="pr-body"></div>
    <div class="pr-foot">
      <div class="pr-nav">
        <button class="pr-prev" type="button">← 이전 단락</button>
        <button class="pr-next" type="button">다음 단락 →</button>
      </div>
      <span class="pr-hint">문장 클릭 = 형광펜</span><button class="pr-open-translation" type="button">Translation 탭에서 이 단락 보기</button>
    </div>
  </div>
</div>
<div class="asset-viewer" role="dialog" aria-label="도표 상세 보기" aria-hidden="true">
  <div class="av-panel">
    <div class="av-head">
      <span class="av-label"></span>
      <span class="av-hint">이미지 클릭: 확대 · ESC/바깥 클릭: 닫기</span>
      <button class="study-fab av-guide" data-asset="" type="button"><span class="study-fab-glyph">?</span>학습 가이드</button>
      <button class="av-close" type="button" aria-label="닫기">×</button>
    </div>
    <div class="av-body">
      <div class="av-img"><img src="" alt="" /></div>
      <div class="av-text">
        <div class="av-sec av-en"><h5>원문 캡션</h5><p></p></div>
        <div class="av-sec av-kr"><h5>번역</h5><p></p></div>
        <details class="av-interp"><summary>해석 보기</summary><div class="av-interp-body"></div></details>
      </div>
    </div>
  </div>
</div>
<div class="img-lightbox" role="dialog" aria-label="이미지 확대보기" aria-hidden="true">
  <div class="img-lightbox-hint">휠: 확대/축소 · 드래그: 이동 · 더블클릭: 원본 · ESC: 닫기</div>
  <button class="img-lightbox-close" type="button" aria-label="닫기">×</button>
  <div class="img-lightbox-stage"><img src="" alt="" /></div>
  <div class="img-lightbox-caption"></div>
</div>
{JS_FINAL}
</body>
</html>
'''

# 출력 파일명은 meta.short_name에서 자동 유도 - {ShortName}_output.html (영숫자만, 예: GeoLLaVA-8K → GeoLLaVA8K)
OUT_HTML = ROOT / ("".join(ch for ch in meta["short_name"] if ch.isalnum()) + "_output.html")
OUT_HTML.write_text(HEAD + BODY, encoding="utf-8")
size_mb = OUT_HTML.stat().st_size / (1024*1024)
print(f"=== {OUT_HTML.name} built: {size_mb:.2f} MB ===")
print(f"  asset images embedded: {len(ASSET_DATAURI)}")
print(f"  generated images embedded: {len(GEN_DATAURI)} -> {sorted(GEN_DATAURI)}")
