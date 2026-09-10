# -*- coding: utf-8 -*-
"""그룹 C(5.backprop, 6.lenet) bespoke Paper Study 포트.
구식 빌더: single-brace raw CSS · JS_TEMPLATE raw · 함수형 render_tab_reading() · fragment BODY · __STUDY_DATA__.
"""
import ast, re, sys
from pathlib import Path

try:  # Windows cp949 콘솔에서도 한글·기호(—·→…) 출력이 깨지거나 죽지 않도록
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent  # 저장소 루트 - 절대 경로 하드코딩 금지


def _load_source() -> str:
    """Paper Study 정본 빌더 텍스트 (배포본: samples/cares, 모체: papers/26. cares)."""
    for cand in (REPO / "samples/cares/_build.py",
                 REPO / "papers/26. cares/_build.py"):
        if cand.exists():
            return cand.read_text(encoding="utf-8")
    raise SystemExit("[FAIL] Paper Study 정본 빌더를 찾을 수 없습니다 "
                     "(samples/cares/_build.py 또는 papers/26. cares/_build.py).")


SRC = _load_source()


def _ex(src, start, end):
    i = src.index(start); j = src.index(end, i); return src[i:j]


REGION_A = _ex(SRC, "# ----------------------------------------------------------------\n# Tab 1.5 - Paper Study",
               "\n# ----------------------------------------------------------------\n# Tab 2 - Dissection")
DRAWER_CSS_D = (_ex(SRC, ".study-drawer{{position:fixed;top:0;right:0;", "@media (max-width: 520px){{")
                + "@media (max-width: 520px){{\n  .study-drawer-body .study-num-row{{grid-template-columns:1fr}}\n}}\n"
                + ".study-drawer-backdrop{{position:fixed;inset:0;background:transparent;z-index:1590;display:none}}\n"
                + ".study-drawer-backdrop.open{{display:block}}")
DRAWER_CSS = DRAWER_CSS_D.replace("{{", "{").replace("}}", "}")  # f-string CSS → single-brace raw
DRAWER_JS = _ex(SRC, "  // Study guide - right-side slide-in drawer",
                "\n\n  const lb = document.querySelector('.img-lightbox');").replace("STUDY_GUIDES_PLACEHOLDER", "__STUDY_DATA__")
MODULE_JS = _ex(SRC, "  // ---- Paper Study tab (tab-study): 서술칸 자동 저장 + 잠금 토글 + 근거 점프 ----", "\n})();\n</script>")
VIEWER_MARKUP = _ex(SRC, '<div class="para-reader" role="dialog"', '<div class="img-lightbox" role="dialog"')

HOVER_NEW = """  // 문장 호버 페어링 - 위임 방식 (리더 복제 문장 대응)
  document.addEventListener('mouseover', (e) => {
    const el = e.target.closest('.sent[data-pair]');
    if (!el) return;
    document.querySelectorAll('.sent[data-pair="'+el.dataset.pair+'"]').forEach(s => s.classList.add('pair-active'));
  });
  document.addEventListener('mouseout', (e) => {
    const el = e.target.closest('.sent[data-pair]');
    if (!el) return;
    document.querySelectorAll('.sent[data-pair="'+el.dataset.pair+'"]').forEach(s => s.classList.remove('pair-active'));
  });"""
HOVER_RE = re.compile(r" *document\.querySelectorAll\('\.sent\[data-pair\]'\)\.forEach\(el => \{\s*"
                      r"el\.addEventListener\('mouseenter'.*?el\.addEventListener\('mouseleave'.*?\n  \}\);", re.S)

FOOTER = "footer.foot{text-align:center;margin-top:40px;color:var(--muted);font-size:12.5px}"
MOBILE = ".knw-grid,.coach-grid,.fund-grid,.diss-grid,.eq-grid{grid-template-columns:1fr}"
MODAL_CSS_START = ".study-modal{position:fixed;inset:0;z-index:300;"

# main() 앞에 삽입할 Python 블록 (alias + Region A + CSS 주입)
INSERT_BLOCK = (
    "\n# ===== Paper Study (group C bespoke port) =====\n"
    "struct = structured\n"
    "TD = ROOT / \"tabs_data\"\n"
    "CAP = config.get(\"captions\", {})\n"
    "INTERPS = analysis.get(\"interpretations\", {})\n"
    "ASSET_DATAURI = {e[0]: \"data:image/png;base64,\" + base64.b64encode((ROOT / \"assets\" / (e[0] + \".png\")).read_bytes()).decode() for e in config.get(\"asset_layout\", []) if (ROOT / \"assets\" / (e[0] + \".png\")).exists()}\n"
    "GEN_DATAURI = {}\n"
    "tab_reading = render_tab_reading()\n\n"
    + REGION_A +
    "\n# STUDY_CSS 주입 (single-brace raw CSS)\n"
    "CSS = CSS.replace(" + repr(FOOTER) + ", STUDY_CSS + " + repr(FOOTER) + ")\n"
    "CSS = CSS.replace(" + repr(MOBILE) + ", " + repr(MOBILE) +
    " + \"\\n  .verdict-grid{grid-template-columns:1fr}\\n  .study-thumbs{grid-template-columns:repeat(2,minmax(0,1fr))}\\n  .study-toolbar{flex-direction:column;align-items:flex-start}\")\n\n"
)


def port(rel):
    p = REPO / rel
    t = p.read_text(encoding="utf-8")
    assert "group C bespoke" not in t, f"{rel}: 이미 이식됨"

    def sub1(old, new, label):
        nonlocal t
        assert t.count(old) == 1, f"[FAIL] {rel} {label}: found {t.count(old)}"
        t = t.replace(old, new)

    # ---- main() 앞에 alias + Region A + CSS 주입 블록 삽입 ----
    sub1("\n\ndef main():\n", "\n\n" + INSERT_BLOCK + "\ndef main():\n", "insert block")

    # ---- CSS (raw string 내부) ----
    # print 규칙 먼저 (single-brace)
    sub1("  nav.tabs,.to-top,.study-fab,.study-modal{display:none !important}",
         "  nav.tabs,.to-top,.study-fab,.study-drawer,.study-drawer-backdrop{display:none !important}", "print rule")
    # DRAWER_CSS 삽입 (첫 모달 규칙 앞) + 모든 .study-modal 규칙 제거 (single-brace)
    pos = t.index(MODAL_CSS_START)
    t = t[:pos] + DRAWER_CSS + "\n" + t[pos:]
    t, nrm = re.subn(r'\.study-modal[^{}\n]*\{[^{}]*\}', '', t)
    assert nrm >= 3, f"[FAIL] {rel} 모달 CSS 제거 {nrm}건"

    # ---- JS_TEMPLATE (raw string 내부) ----
    # 모달 JS → 드로어 JS
    js_s = "  const modal = document.createElement('div');"
    js_e = ("      if (window.MathJax && window.MathJax.typesetPromise) window.MathJax.typesetPromise([modalBody]).catch(()=>{});\n"
            "    });\n  });")
    i = t.index(js_s); j = t.index(js_e, i) + len(js_e)
    t = t[:i] + DRAWER_JS + t[j:]
    # studyNav (tabs.forEach 뒤)
    sub1("  tabs.forEach(t => t.addEventListener('click', () => activate(t.dataset.tab)));",
         "  tabs.forEach(t => t.addEventListener('click', () => activate(t.dataset.tab)));\n\n"
         "  function studyNav(tab){ activate(tab); } /*STUDY-NAV*/", "studyNav")
    # 호버 위임
    assert len(HOVER_RE.findall(t)) == 1, f"[FAIL] {rel} hover {len(HOVER_RE.findall(t))}"
    t = HOVER_RE.sub(lambda m: HOVER_NEW, t, count=1)
    # autoLink 셀렉터 확장
    t, k = re.subn(r"(querySelectorAll\('\.tab-pane \.col p[^']*)'\)",
                   r"\1, .study-claude-body p, .study-guide, .study-qlist li, .v-claim, .v-note, .alt-card p, .v-claude-body p')", t, count=1)
    assert k == 1, f"[FAIL] {rel} autoLink"
    # MODULE_JS를 JS_TEMPLATE 마지막 })(); 앞에 삽입 (아직 })(); 유일할 때)
    sub1("})();\n\"\"\"", "\n" + MODULE_JS + "\n})();\n\"\"\"", "module JS (JS_TEMPLATE close)")

    # ---- main() 편집 ----
    # nav 버튼
    sub1("'<button class=\"tab-btn active\" data-tab=\"tab-reading\">① 원문 / 번역</button>'",
         "'<button class=\"tab-btn active\" data-tab=\"tab-reading\">① 원문 / 번역</button>'\n"
         "        '<button class=\"tab-btn\" data-tab=\"tab-study\">①′ Paper Study</button>'", "nav button")
    # panes: render_tab_reading() → tab_reading + study pane
    sub1("    panes = (\n        render_tab_reading()\n",
         "    panes = (\n        tab_reading\n"
         "        + '<section id=\"tab-study\" class=\"tab-pane\">' + tab_study + '</section>'\n", "panes study")
    # body: </main> 뒤에 viewer 마크업
    sub1("        '</main>'\n", "        '</main>'\n        + " + repr(VIEWER_MARKUP) + "\n", "viewer markup")
    # js replace 체인
    sub1('    js = JS_TEMPLATE.replace("__STUDY_DATA__", render_study_data())',
         '    js = (JS_TEMPLATE.replace("__STUDY_DATA__", render_study_data())\n'
         '          .replace("STUDY_SHORT_PLACEHOLDER", json.dumps(md["short_name"], ensure_ascii=False))\n'
         '          .replace("AV_DATA_PLACEHOLDER", json.dumps(AV_DATA, ensure_ascii=False)))', "js chain")

    ast.parse(t)
    p.write_text(t, encoding="utf-8")
    print(f"[ok] {rel}  (group C bespoke, syntax ok)")


if __name__ == "__main__":
    for rel in sys.argv[1:]:
        port(rel if rel.endswith("_build.py") else rel.rstrip("/\\") + "/_build.py")
