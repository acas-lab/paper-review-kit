# -*- coding: utf-8 -*-
"""v3 템플릿 산출물 → v4 대시보드 디자인 변환 (범용 도구).

사용법:
    python tools/restyle_dash_v4.py "papers/N. shortname"

입력 요구사항:
- 대상 폴더에 v3 표준 템플릿(_build.py 계열)으로 조립된 `{ShortName}_output.html` 1개
- `config.json#meta`: title / short_name / authors / affiliation (필수)
  + keyword / venue_short / status / arxiv / listed / code / generated (권장 — topbar 우측 메타)
- 로고: `samples/design/acas-logo.png` (저장소 내 — 외부 경로 의존 없음)

변환 내용 (rules/design_v4_dashboard.md 정본 규약):
  ① v3 lavender 토큰 → v4 저채도 grey-lavender  ② hero 카드 → topbar(로고+3줄+우측 메타)
  ③ 숫자 pill 6탭 → 숫자 없는 7탭 (knowledge의 eq-panel을 Mathematics 탭으로 분리)
  ④ 해시 라우팅(뒤로/앞으로 버튼·딥링크)  ⑤ serif 제거·radius 14·--shadow·밝은 수식 블록

검증: 변환 전후 콘텐츠 인벤토리 상대 비교(문장·카드·자산 수 보존 + 탭 +1) — 논문별 수치 하드코딩 없음.
Paper Study 탭(tab-study)이 있는 v3 산출물은 7→8탭, 없으면 6→7탭으로 변환된다.
논문별로 수정할 곳: 없음 (전부 config.json meta에서 읽음).

첫 적용 사례·원형: papers/26. cares/_restyle_dash_v3.py (CARES 전용 historical).
"""
import base64
import json
import re
import sys
from pathlib import Path

try:  # Windows cp949 콘솔에서도 한글·기호(—·→…) 출력이 깨지거나 죽지 않도록
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO = Path(__file__).parent.parent
LOGO_PNG = REPO / "samples" / "design" / "acas-logo.png"


def sub1(old, new, text, label, count=1):
    n = text.count(old)
    if n != count:
        raise SystemExit(f"[FAIL] {label}: expected {count}, found {n}: {old[:80]!r}")
    return text.replace(old, new)


def rsub(pattern, repl, text, label, count=1, optional=False):
    """정규식 치환 — 템플릿 세대 간 변형 흡수용."""
    n = len(re.findall(pattern, text))
    if n != count:
        if optional and n == 0:
            return text
        raise SystemExit(f"[FAIL] {label}: expected {count}, found {n}: {pattern[:80]!r}")
    return re.sub(pattern, repl, text)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inventory(text):
    keys = {
        "sent": r'<span class="sent', "paragraph": r'class="paragraph-block"',
        "asset": r'class="asset-card', "callout": r'class="callout ',
        "recall": r'class="recall-card"', "diss": r'class="diss-card',
        "eq": r'class="eq-card"', "fund": r'class="fund-card"',
        "knw": r'class="knw-card"', "coach": r'class="coach-card',
        "fab": r'class="study-fab"', "concept": r'class="concept-figure"',
        "interp": r'class="interpretation"', "beginner": r'class="beginner-note"',
        "pane": r'class="tab-pane', "btn": r'class="tab-btn',
    }
    return {k: len(re.findall(p, text)) for k, p in keys.items()}


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    paper = Path(sys.argv[1])
    htmls = [p for p in paper.glob("*_output.html")]
    if len(htmls) != 1:
        raise SystemExit(f"[FAIL] expected exactly one *_output.html in {paper}, found {htmls}")
    src = htmls[0]
    cfg = json.loads((paper / "config.json").read_text(encoding="utf-8-sig"))
    meta = cfg.get("meta") or cfg.get("metadata")
    if not meta:
        raise SystemExit("[FAIL] config.json에 meta/metadata 블록이 없습니다")
    if "venue" not in meta and "conference" in meta:
        meta = dict(meta, venue=meta["conference"])
    if "code" not in meta and "code_url" in meta:
        meta = dict(meta, code=meta["code_url"])
    t = src.read_text(encoding="utf-8")
    inv_before = inventory(t)
    if 'class="topbar"' in t:
        raise SystemExit("[FAIL] already v4 (topbar present) — v3 raw 산출물에만 적용하세요 (_build.py 재실행 후).")

    logo = "data:image/png;base64," + base64.b64encode(LOGO_PNG.read_bytes()).decode()

    # ------------------------------------------------------------ 1. title 중복 교정
    short, title = meta["short_name"], meta["title"]
    dup = f"<title>{short}: {title}</title>"
    if dup in t and title.startswith(short + ":"):
        t = t.replace(dup, f"<title>{title}</title>")

    # ------------------------------------------------------------ 2. CSS 토큰
    # :root 의 v3 팔레트(→ --hero-gradient 까지)를 v4 로 교체. minified/pretty 양쪽 허용.
    V4_ROOT_OPEN = """:root {
  /* v4 — 실험_대시보드 팔레트: 저채도 grey-lavender, near-white 배경 */
  --bg: #fafbfc; --paper: #ffffff; --ink: #32363f; --ink-soft: #5e6470; --muted: #9aa0ac; --line: #ecedf2;
  --accent: #5e6488; --accent-mid: #9398b9; --accent-soft: #f1f2f8; --accent-pale: #d9dce9;
  --azure: #7191ab; --azure-soft: #eaf1f7; --azure-pale: #d5e2ec;
  --rose: #ab8290;  --rose-soft: #f6edf0;
  --mint: #74ad97; --mint-soft: #edf4f1;
  --amber: #ab8a55; --amber-soft: #f6f1e6;
  --radius: 14px;
  --shadow: 0 1px 2px rgba(48,53,66,.03),0 1px 6px rgba(48,53,66,.03);
  --hero-gradient: linear-gradient(135deg, #eceff5 0%, #e9e7f1 100%);"""
    t = rsub(r'(?s):root\s*\{.*?--hero-gradient:\s*linear-gradient\(135deg,\s*#c0dcf5\s*0%,\s*#d2c2f5\s*100%\);',
             V4_ROOT_OPEN.replace("\\", "\\\\"), t, "root tokens", count=1)
    # (v2 alias 줄(--sage 등)은 --hero-gradient 뒤에 남아 var() 참조 → v4 색 자동 적용)

    V4_BODY = ('body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Pretendard Variable",'
               '"Noto Sans KR","Apple SD Gothic Neo","Malgun Gothic",sans-serif;background:var(--bg);'
               'color:var(--ink);font-size:15.5px;line-height:1.66;word-break:keep-all;overflow-wrap:break-word}')
    if re.search(r'body\{font-family:"Pretendard Variable"', t):
        t = rsub(r'body\{font-family:"Pretendard Variable"[^}]*\}', V4_BODY.replace("\\", "\\\\"),
                 t, "body font")
    else:  # pretty-printed 샘플: 폰트 없는 body 규칙을 v4 body 로 교체 (첫 규칙만)
        new_t, n = re.subn(r'body\s*\{[^{}]*\}', V4_BODY.replace("\\", "\\\\"), t, count=1)
        if n != 1:
            raise SystemExit("[FAIL] body rule not found (neither Pretendard nor plain)")
        t = new_t
    t = rsub(r'\.app\s*\{\s*max-width:\s*1280px;\s*margin:\s*0 auto;\s*padding:\s*28px 26px 90px;?\s*\}',
             ".app{max-width:1160px;margin:0 auto;padding:26px 30px 90px}", t, "app width",
             count=1, optional=True)

    # ------------------------------------------------------------ 3. hero/nav CSS → topbar CSS
    # .brand-tag ~ .tab-btn.active 전체 스팬을 통째로 교체 (hero 세부는 세대별 변형이 있어 regex)
    NEW_TOPBAR_CSS = """/* ===== 대시보드 v4 topbar — 헤더+탭 단일 응집 상단 바 (Material top app bar + 밑줄 탭) ===== */
.topbar{position:sticky;top:0;z-index:60;background:var(--bg);border-bottom:1px solid var(--line);box-shadow:0 1px 6px rgba(95,106,166,.03)}
.hdr{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:13px 30px 6px}
.tabs-row{padding:0 30px}
.brand{display:flex;align-items:center;gap:12px;margin-right:6px;min-width:0}
.brand img{height:40px;width:auto;display:block;flex-shrink:0}
.brand .bt{font-weight:800;font-size:15px;color:var(--accent);line-height:1.25}
.brand .bs{font-size:12.5px;color:var(--ink-soft);font-weight:700;margin-top:1px;line-height:1.35}
.brand .bs2{font-size:11px;color:var(--muted);font-weight:600;margin-top:2px;line-height:1.35}
.brand-meta{margin-left:auto;font-size:12px;color:var(--muted);padding-bottom:10px;text-align:right;line-height:1.6;flex-shrink:0}
nav.tabs{display:flex;flex-wrap:wrap;align-items:center;gap:0;padding:0;margin:0}
nav.tabs .tab-btn{position:relative;background:none;border:0;border-radius:0;font:inherit;color:var(--ink-soft);font-size:14.5px;font-weight:600;padding:9px 18px 12px;cursor:pointer;transition:.12s;white-space:nowrap;flex:0 0 auto;min-width:0}
nav.tabs .tab-btn:not(:last-child)::after{content:"";position:absolute;right:0;top:9px;bottom:12px;width:1px;background:var(--line)}
nav.tabs .tab-btn:hover{color:var(--accent)}
nav.tabs .tab-btn.active{color:var(--accent);font-weight:800;background:none;border:0;box-shadow:none}
nav.tabs .tab-btn.active::before{content:"";position:absolute;left:14px;right:14px;bottom:-1px;height:2.5px;background:var(--accent-mid);border-radius:2px}"""

    t = rsub(r"(?s)\.brand-tag\s*\{.*?\.tab-btn\.active\s*\{[^}]*\}",
             NEW_TOPBAR_CSS.replace("\\", "\\\\"), t, "hero/nav css")

    # ------------------------------------------------------------ 4. serif 제거 + 그림자/라운드/hex 통일
    css_end = t.find("</style>")
    css, rest = t[:css_end], t[css_end:]
    # serif 폰트 선언 제거 — 트레일링 `;` 는 선택적으로(규칙 마지막 속성이면 `}` 로 끝나 세미콜론이 없음).
    # `}` 는 소비하지 않아 규칙 경계를 보존한다 (구버전은 `;` 필수라 `.col p.english{…serif}` 를 놓쳤다).
    css = re.sub(r'font-family:Georgia[^;}]*;?', '', css)

    for old, new in [
        ("box-shadow:0 8px 24px rgba(80,60,140,0.05)", "box-shadow:var(--shadow)"),
        ("box-shadow:0 6px 20px rgba(80,60,140,0.05)", "box-shadow:var(--shadow)"),
        ("box-shadow:0 6px 18px rgba(80,60,140,0.05)", "box-shadow:var(--shadow)"),
        ("box-shadow:0 6px 18px rgba(80,60,140,0.06)", "box-shadow:var(--shadow)"),
        ("rgba(80,60,140,0.32)", "rgba(48,53,66,0.28)"),
        ("rgba(80,60,140,0.42)", "rgba(48,53,66,0.36)"),
        ("border-radius:22px", "border-radius:var(--radius)"),
        ("border-radius:18px", "border-radius:var(--radius)"),
        ("border-radius:16px", "border-radius:14px"),
        ("#fbfaff", "#fafbfc"), ("#faf8ff", "#fafbfd"), ("#ece8f0", "#ecedf2"),
        ("#fff4d6", "#f6f1e6"), ("#ffe4a1", "#eee3c8"),
        ("#5a4716", "#6b5426"), ("#6c2c3a", "#7a5560"),
        ("#f8f3ff", "#f4f5f9"), ("#f0f6ff", "#eef3f8"),
        ("#b8d0c0", "#cfdfd5"), ("#cfe0d4", "#d7e4dc"), ("#1f3d31", "#3f6a58"), ("#f5fbf6", "#f2f7f4"),
        ("#7a5db5", "#7d7aa0"), ("#ece2f8", "#ececf4"),
        ("#3aa185", "#5d9b85"), ("#dceee8", "#e4efe9"),
        ("#3d2a5e", "#494e6e"), ("#f5edff", "#f3f4f9"), ("#e4d9ff", "#e6e8f2"),
        ("#fefcff", "#fcfcfe"), ("#f3edff", "#f4f5f9"), ("#e8def8", "#e4e6ee"),
        ("#6e54a3", "#4c5273"),
        ("rgba(139,117,192,0.94)", "rgba(94,100,136,0.94)"),
        ("rgba(20,10,30,0.18)", "rgba(30,34,46,0.18)"),
        ("rgba(251,250,255,0.7)", "rgba(250,251,252,0.8)"),
    ]:
        css = css.replace(old, new)

    css = rsub(r"(\.eq-display\{[^}]*?)background:#(?:1f1814|1f1d24);color:#(?:fff5dc|f3ead4)",
               r"\1background:#f1f2f7;color:var(--ink);border:1px solid var(--line)",
               css, "eq-display", optional=True)
    css = rsub(r"\.eq-display mjx-container\{color:#(?:fff5dc|f3ead4) !important\}",
               ".eq-display mjx-container{color:#32363f !important}", css, "eq mjx", optional=True)
    css = rsub(r"\.eq-display\{background:#[0-9a-f]{6};color:#[0-9a-f]{6}\} \.eq-display mjx-container\{color:#[0-9a-f]{6} !important\}",
               ".eq-display{background:#f1f2f7;color:#32363f} .eq-display mjx-container{color:#32363f !important}",
               css, "eq print", optional=True)
    # `.eq-display` 외의 다크-수식 블록(예: `.qa-math`)도 v4 밝은 회색으로 — 다크 색쌍 기준 전면 변환.
    css = re.sub(r"background:#(?:1f1814|1f1d24);color:#(?:fff5dc|f3ead4)",
                 "background:#f1f2f7;color:#32363f", css)
    css = re.sub(r"(mjx-container\{color:)#(?:fff5dc|f3ead4)( ?!important\})",
                 r"\g<1>#32363f\g<2>", css)
    css = rsub(r"\.tab-intro h2\s*\{[^}]*\}",
               ".tab-intro h2{margin:0 0 6px;color:var(--ink);font-size:21px;font-weight:800}",
               css, "tab-intro h2")
    css = rsub(r"nav\.tabs\s*,\s*(\.to-top[^{}]*?)\{[^}]*?display:\s*none[^}]*?\}",
               r".topbar,\1{display:none !important}",
               css, "print rule", optional=True)
    MOBILE_TOPBAR = """  .hdr{padding:10px 14px 4px}
  .brand img{height:32px}
  .brand .bs{font-size:11.5px;white-space:normal}
  .brand .bs2{font-size:10.5px;white-space:normal}
  .brand-meta{display:none}
  .tabs-row{padding:0 8px;overflow-x:auto}
  nav.tabs{flex-wrap:wrap}
  nav.tabs .tab-btn{font-size:13px;padding:8px 12px 11px}"""
    exact_mob = ("  nav.tabs{flex-wrap:wrap}\n"
                 "  .tab-btn{flex:1 1 45%;font-size:13px;padding:8px 6px;min-width:0}")
    if exact_mob in css:
        css = css.replace(exact_mob, MOBILE_TOPBAR, 1)
    else:  # pretty-printed 샘플: 640px 미디어쿼리 여는 직후에 topbar 모바일 규칙 주입
        css, n = re.subn(r'(@media\s*\([^)]*max-width:\s*640px[^)]*\)\s*\{)',
                         r'\1\n' + MOBILE_TOPBAR.replace("\\", "\\\\"), css, count=1)
        if n != 1:  # 640px 브레이크포인트가 없는 구세대(1~2) — 신규 모바일 블록을 </style> 직전에 추가
            css += "\n@media (max-width: 640px){\n" + MOBILE_TOPBAR + "\n}\n"
            print("[warn] 640px 미디어쿼리 없음 — v4 모바일 topbar 블록 신규 추가")
    css = re.sub(r'\n\s*header\.hero .meta\s*\{grid-template-columns:1fr\}', "", css)
    t = css + rest

    # body 영역(인라인 SVG·style 속성)의 잔존 v3 팔레트 hex도 스왑 (base64에는 '#'가 없어 안전)
    i_body = t.find("</style>")
    head_part, body_part = t[:i_body], t[i_body:]
    for old, new in [
        ("#8b75c0", "#5e6488"), ("#e4d9ff", "#e6e8f2"), ("#d2c2f5", "#d9dce9"),
        ("#6b95b3", "#7191ab"), ("#d9ebff", "#eaf1f7"), ("#c0dcf5", "#d5e2ec"),
        ("#b87887", "#ab8290"), ("#ffdde6", "#f6edf0"),
        ("#75ad8e", "#74ad97"), ("#e3eee7", "#edf4f1"),
        ("#ad8e4e", "#ab8a55"), ("#f3ead4", "#f6f1e6"),
        ("#fbfaff", "#fafbfc"), ("#ece8f0", "#ecedf2"), ("#1f1d24", "#32363f"), ("#7a7484", "#9aa0ac"),
    ]:
        body_part = body_part.replace(old, new).replace(old.upper(), new)
    t = head_part + body_part

    # ------------------------------------------------------------ 5. 헤더 마크업 → topbar (config#meta 기반)
    authors = meta["authors"].replace(", ", " · ")
    line3 = f"{authors} — {meta['affiliation']}"
    parts = []
    if meta.get("venue_short"):
        parts.append(f"<b>{esc(meta['venue_short'])}</b>")
    if meta.get("status"):
        parts.append(f"<b>{esc(meta['status'])}</b>")
    if meta.get("arxiv"):
        parts.append(f"arXiv {esc(meta['arxiv'])}")
    if meta.get("listed"):
        parts.append(f"등재 {esc(meta['listed'])}")
    right1 = " · ".join(parts) if parts else esc(meta.get("venue", ""))
    right2 = ""
    if meta.get("code"):
        label = re.sub(r"^https?://", "", meta["code"]).rstrip("/")
        right2 = (f'코드 <a href="{meta["code"]}" target="_blank" rel="noopener" '
                  f'style="color:var(--accent);font-weight:700">{esc(label)}</a><br>')
    gen = meta.get("generated", "")
    right3 = f"생성일 {esc(gen)}" if gen else ""
    # Paper Study 탭(선택) — v3 산출물에 tab-study pane이 있으면 v4 탭 줄에도 노출
    study_tab_btn = ('\n    <button class="tab-btn" data-tab="tab-study">Paper Study</button>'
                     if 'id="tab-study"' in t else '')

    NEW_HEADER = f"""<div class="topbar">
  <div class="hdr">
    <div class="brand"><img src="{logo}" alt="ACAS">
      <div>
        <div class="bt">{esc(meta['title'])}</div>
        <div class="bs">{esc(meta.get('keyword', meta['short_name']))}</div>
        <div class="bs2">{esc(line3)}</div>
      </div>
    </div>
    <div class="brand-meta">{right1}<br>{right2}{right3}</div>
  </div>
  <div class="tabs-row"><nav class="tabs" role="tablist">
    <button class="tab-btn active" data-tab="tab-reading">Translation</button>{study_tab_btn}
    <button class="tab-btn" data-tab="tab-dissection">Paper Dissection</button>
    <button class="tab-btn" data-tab="tab-knowledge">Background</button>
    <button class="tab-btn" data-tab="tab-math">Mathematics</button>
    <button class="tab-btn" data-tab="tab-questions">Diagrams</button>
    <button class="tab-btn" data-tab="tab-simulator">Code</button>
    <button class="tab-btn" data-tab="tab-qa">Q &amp; A</button>
  </nav></div>
</div>
"""

    # 헤더+nav 영역 교체 — 컨테이너 요소는 세대별로 다름 (<main class="app"> / <div class="app"> / <main>)
    m = re.search(r'(<(?:main|div)[^>]*class="app"[^>]*>\s*)?<header.*?</nav>', t, re.S)
    if not m:
        raise SystemExit("[FAIL] header block not found")
    region = m.group(0)
    lead = m.group(1) or ""
    tag = "div" if re.search(r'<div[^>]*class="app"', lead + region[:120]) else "main"
    container = f'<{tag} class="app">'
    t = t[:m.start()] + NEW_HEADER + container + t[m.end():]

    # ------------------------------------------------------------ 6. knowledge → Background + Mathematics 분리
    i_k = t.find('<section id="tab-knowledge"')
    i_q = t.find('<section id="tab-questions"')
    if i_k < 0 or i_q < 0:
        raise SystemExit("[FAIL] knowledge/questions panes not found")
    i_eq = t.find('<section class="eq-panel">', i_k)
    if 0 < i_eq < i_q:
        j_eq = t.find("</section>", i_eq)
        # eq-panel 내부에 중첩 <section>이 없다는 전제 (v3 템플릿 표준)
        if t.count("<section", i_eq, j_eq) != 1:
            raise SystemExit("[FAIL] eq-panel has nested sections — 수동 분리 필요")
        eq_panel = t[i_eq:j_eq + len("</section>")]
        t = t[:i_eq] + t[j_eq + len("</section>"):]
        msub = re.search(r'<p class="panel-sub">(.*?)</p>', eq_panel, re.S)
        intro_p = msub.group(1).strip() if msub else "핵심 수식을 유도·직관·함의와 함께 푸는 탭."
        math_body = eq_panel
    else:
        intro_p = "이 논문의 핵심 수식 탭입니다."
        math_body = '<section class="section section-empty"><p class="section-empty-note">수식 카드가 없는 논문입니다.</p></section>'

    MATH_PANE = f"""  <section id="tab-math" class="tab-pane">
<div class="tab-intro"><h2>Mathematics — 핵심 수식</h2><p>{intro_p}</p></div>
{math_body}
  </section>
"""
    i_q = t.find('<section id="tab-questions"')
    t = t[:i_q] + MATH_PANE + "  " + t[i_q:]
    # 구 v3 지식탭 intro 제목 교정 (있을 때만)
    t = t.replace("<h2>Background &amp; 핵심 수식</h2>", "<h2>Background — 배경지식</h2>")

    # ------------------------------------------------------------ 7. JS: Eq 링크 → tab-math + 해시 라우팅
    if "const targetTabFor" in t:
        t = sub1("const targetTabFor = (kind) => kind === 'Eq' ? 'tab-knowledge' : 'tab-reading';",
                 "const targetTabFor = (kind) => kind === 'Eq' ? 'tab-math' : 'tab-reading';",
                 t, "js eq target")
    else:  # 구세대(20~21): if (/^Eq|^Equation/.test(head)) { tab='tab-knowledge'; …
        t = rsub(r"(/\^Eq\|\^Equation/\.test\(head\)\) \{ tab=)'tab-knowledge'",
                 r"\1'tab-math'", t, "js eq target (legacy)", optional=True)
    # 해시 라우터 골격 — 탭 바인딩 변수명은 세대별로 다르다 (buttons/b vs tabs/t)
    HASH_ROUTER = """  // 해시 라우팅 — 탭 전환을 브라우저 히스토리에 기록해 뒤로/앞으로 버튼 지원 (v4 규약)
  const PANE_IDS = Array.prototype.map.call(panes, p => p.id);
  function go(tab){
    if (PANE_IDS.indexOf(tab) < 0) tab = 'tab-reading';
    if (('#' + tab) === location.hash) activate(tab);
    else location.hash = tab;
  }
  function route(){
    const id = (location.hash || '#tab-reading').slice(1);
    activate(PANE_IDS.indexOf(id) >= 0 ? id : 'tab-reading');
  }
  __VARS__.forEach(__V__ => __V__.addEventListener('click', () => go(__V__.dataset.tab)));
  window.addEventListener('hashchange', route);
  route();"""
    NEW_GEN = "  buttons.forEach(b => b.addEventListener('click', () => activate(b.dataset.tab)));"
    OLD_GEN = "  tabs.forEach(t => t.addEventListener('click', () => activate(t.dataset.tab)));"
    routed_inline = False
    if NEW_GEN in t:
        t = sub1(NEW_GEN, HASH_ROUTER.replace("__VARS__", "buttons").replace("__V__", "b"),
                 t, "hash routing")
        routed_inline = True
    elif OLD_GEN in t:  # 구세대(5~6 curriculum): const tabs / activate(id)
        t = sub1(OLD_GEN, HASH_ROUTER.replace("__VARS__", "tabs").replace("__V__", "t"),
                 t, "hash routing (tabs-gen)")
        routed_inline = True
    else:
        # bespoke JS(예: SGL 3세대 block-body 핸들러) — 내부 코드 손대지 않고 DOM 레벨 hash shim 주입
        SHIM = ("<script>\n(function(){\n"
                "  var btns=document.querySelectorAll('.tab-btn');\n"
                "  function sync(){var id=(location.hash||'#tab-reading').slice(1);\n"
                "    for(var i=0;i<btns.length;i++){if(btns[i].dataset.tab===id){btns[i].click();break;}}}\n"
                "  for(var i=0;i<btns.length;i++){btns[i].addEventListener('click',function(){\n"
                "    var h='#'+this.dataset.tab;if(location.hash!==h)location.hash=h;});}\n"
                "  window.addEventListener('hashchange',sync);\n"
                "  if(location.hash)sync();\n})();\n</script>\n")
        t = rsub(r'</body>', SHIM + '</body>', t, "hash routing (dom shim)", count=1)
        print("[warn] bespoke JS 감지 — DOM 레벨 hash 라우팅 shim 주입 (페이지 자체 탭 핸들러 보존)")
    if routed_inline:
        t = sub1("            activate(a.dataset.targetTab);",
                 "            go(a.dataset.targetTab);",
                 t, "autoLink → go")
        if "/*STUDY-NAV*/" in t:  # Paper Study 근거 점프도 해시 라우팅 경유
            t = sub1("function studyNav(tab){ activate(tab); } /*STUDY-NAV*/",
                     "function studyNav(tab){ go(tab); } /*STUDY-NAV*/",
                     t, "studyNav → go")

    # ------------------------------------------------------------ 7b. 잔존 v3 팔레트 hex 최종 청소 (전역)
    # 구세대 샘플(1~3)의 bespoke 컴포넌트 CSS는 v3 deep-tone을 리터럴로 박아둠 — 표준 스왑 목록이 못 잡음.
    # base64 data URI 에는 '#'가 없어 전역 치환 안전.
    for old, new in [
        ("#8b75c0", "#5e6488"), ("#e4d9ff", "#e6e8f2"), ("#d2c2f5", "#d9dce9"),
        ("#6b95b3", "#7191ab"), ("#d9ebff", "#eaf1f7"), ("#c0dcf5", "#d5e2ec"),
        ("#b87887", "#ab8290"), ("#ffdde6", "#f6edf0"),
        ("#75ad8e", "#74ad97"), ("#e3eee7", "#edf4f1"),
        ("#ad8e4e", "#ab8a55"), ("#f3ead4", "#f6f1e6"),
        ("#fbfaff", "#fafbfc"), ("#ece8f0", "#ecedf2"), ("#1f1d24", "#32363f"), ("#7a7484", "#9aa0ac"),
    ]:
        t = t.replace(old, new).replace(old.upper(), new)

    # ------------------------------------------------------------ 7c. footer 버전 마커 v3 → v4
    # v3 템플릿 footer의 "Paper Review HTML · v3"는 최종 산출물이 v4이므로 v4로 표기 통일.
    t = t.replace("Paper Review HTML · v3", "Paper Review HTML · v4")

    # ------------------------------------------------------------ 8. 검증 — 변환 전후 상대 비교 (콘텐츠 보존)
    inv_after = inventory(t)
    bad = {}
    for k, v in inv_before.items():
        want = v + 1 if k in ("pane", "btn") else v   # 탭만 +1 (Mathematics)
        if inv_after[k] != want:
            bad[k] = (v, inv_after[k])
    if bad:
        raise SystemExit(f"[FAIL] inventory drift (before, after): {bad}")
    want_tabs = 8 if 'id="tab-study"' in t else 7  # Paper Study 탭 포함 시 8탭
    if inv_after["pane"] != want_tabs or inv_after["btn"] != want_tabs:
        raise SystemExit(f"[FAIL] expected {want_tabs} tabs, got pane={inv_after['pane']} btn={inv_after['btn']}")

    src.write_text(t, encoding="utf-8")
    print(f"[ok] inventory preserved: {inv_after}")
    print(f"[done] {src.name} → v4 dashboard design")


if __name__ == "__main__":
    main()
