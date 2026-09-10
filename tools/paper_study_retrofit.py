# -*- coding: utf-8 -*-
"""이미 v4인 논문의 _build.py에 Paper Study 탭을 소급 이식 (범용 · 세대 자동 감지).

정본(`samples/cares/_build.py` · 모체는 `papers/26. cares/_build.py`)에서 블록을 추출해 대상 빌더에 앵커 기반으로 주입한다.
빌더 세대 자동 감지:
  GEN B - CARES 호환 (JS-created 학습가이드 modal · STUDY_GUIDES_PLACEHOLDER · JS_FINAL 조립 · lb/lbCloseFn lightbox)
  GEN A - 구세대 (BODY 배치 modal · __STUDY_JSON__/STUDY_DATA · lightbox/lbOpen/lbClose)

수행 내용:
  1. 학습 가이드 풀스크린 모달 → CARES 우측 드로어 승격 (CSS+JS+print, 세대별)
  2. 호버 페어링 요소별 바인딩 → 문서 위임 (리더 복제 문장 대응)
  3. Paper Study 12단계 (Region A 빌더 블록 · STUDY_CSS · 모듈 JS · 뷰어/리더 마크업 · nav · pane · 조립 체인)
  4. 세대별 변수명 차이 흡수 셤 (ASSET_DATA↔ASSET_DATAURI · CAP · INTERPS)

사용법: python tools/paper_study_retrofit.py "papers/N. shortname"

이식 후 필수:
  - Stage 11 데이터: tabs_data/study.json + config.json#captions_en + study/ 폴더 (prompts/11)
  - 빌드+변환 페어: python _build.py && python tools/restyle_dash_v4.py "papers/N. shortname"
  - 검증: tools/check_study_refs.py · tools/check_html_escape.py

⚠️ v3-dict-format config 논문(asset_layout이 dict): study.json 도입 전 config를 v4 list-format으로
   마이그레이션해야 한다(asset_layout 리스트화 + captions 톱레벨화). 이 경우 빌더의 캡션 조회도
   top-level captions에서 읽도록 1줄 수정 필요 (정본 사례: 20. sparse_vlm).

정본 소급 사례: 20~25 (2026-07-08).
"""
import ast
import re
import sys
from pathlib import Path

try:  # Windows cp949 콘솔에서도 한글·기호(—·→…) 출력이 깨지거나 죽지 않도록
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO = Path(__file__).parent.parent


def _load_source() -> str:
    """Paper Study 정본 빌더 텍스트. 배포 툴킷은 samples/cares/_build.py,
    모체 작업 폴더는 papers/26. cares/_build.py 를 소스로 쓴다 (같은 도구가 양쪽에서 동작)."""
    for cand in (REPO / "samples/cares/_build.py",
                 REPO / "papers/26. cares/_build.py"):
        if cand.exists():
            return cand.read_text(encoding="utf-8")
    raise SystemExit(
        "[FAIL] Paper Study 정본 빌더를 찾을 수 없습니다 - "
        "samples/cares/_build.py 또는 papers/26. cares/_build.py 필요.")


SRC = _load_source()


def _ex(src, start, end):
    i = src.index(start); j = src.index(end, i); return src[i:j]


DRAWER_CSS = (_ex(SRC, ".study-drawer{{position:fixed;top:0;right:0;", "@media (max-width: 520px){{")
              + "@media (max-width: 520px){{\n  .study-drawer-body .study-num-row{{grid-template-columns:1fr}}\n}}\n"
              + ".study-drawer-backdrop{{position:fixed;inset:0;background:transparent;z-index:1590;display:none}}\n"
              + ".study-drawer-backdrop.open{{display:block}}")
DRAWER_JS = _ex(SRC, "  // Study guide - right-side slide-in drawer",
                "\n\n  const lb = document.querySelector('.img-lightbox');")
REGION_A = _ex(SRC, "# ----------------------------------------------------------------\n# Tab 1.5 - Paper Study",
               "\n# ----------------------------------------------------------------\n# Tab 2 - Dissection")
MODULE_JS = _ex(SRC, "  // ---- Paper Study tab (tab-study): 서술칸 자동 저장 + 잠금 토글 + 근거 점프 ----",
                "\n})();\n</script>")
VIEWER_MARKUP = _ex(SRC, '<div class="para-reader" role="dialog"', '<div class="img-lightbox" role="dialog"')

SHIM = ("# Paper Study 호환 alias - 빌더 세대별 변수명 차이 흡수 (ASSET_DATA vs ASSET_DATAURI 등)\n"
        "try:\n    ASSET_DATAURI\nexcept NameError:\n    ASSET_DATAURI = ASSET_DATA\n"
        "try:\n    CAP\nexcept NameError:\n    CAP = config.get(\"captions\", {})\n"
        "try:\n    INTERPS\nexcept NameError:\n    INTERPS = analysis.get(\"interpretations\", {})\n\n")

HOVER_NEW = """  // 문장 호버 페어링 - 위임 방식: 플로팅 리더의 복제 문장에서도 동일하게 동작
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
HOVER_RE = re.compile(
    r" *document\.querySelectorAll\('\.sent\[data-pair\]'\)\.forEach\(el => \{\s*"
    r"el\.addEventListener\('mouseenter'.*?el\.addEventListener\('mouseleave'.*?\n  \}\);", re.S)


def retrofit(rel):
    p = REPO / rel
    t = p.read_text(encoding="utf-8")
    assert "STUDY_CSS" not in t and "para-reader" not in t, f"{rel}: 이미 이식됨"

    def sub1(old, new, label):
        nonlocal t
        assert t.count(old) == 1, f"[FAIL] {rel} {label}: found {t.count(old)}"
        t = t.replace(old, new)

    def opt(old, new, label):
        nonlocal t
        n = t.count(old)
        if n == 1:
            t = t.replace(old, new)
        elif n:
            raise AssertionError(f"[FAIL] {rel} {label}: found {n}")

    GEN = "B" if "  const modal = document.createElement(" in t else "A"
    HAS_LB = '<div class="img-lightbox" role="dialog"' in t  # 이미지 확대 lightbox 컴포넌트 유무

    # 1. 학습 가이드 모달 → 드로어
    # (1a) print 규칙 먼저 - 선택자 안의 .study-modal → .study-drawer (아래 정규식 제거가 print 규칙을 깨지 않게)
    opt("@media print {{.img-lightbox,.study-modal,.to-top{{display:none !important}}}}",
        "@media print {{.img-lightbox,.study-drawer,.study-drawer-backdrop,.to-top{{display:none !important}}}}", "print1")
    opt("  nav.tabs,.to-top,.study-fab,.study-modal{{display:none !important}}",
        "  nav.tabs,.to-top,.study-fab,.study-drawer,.study-drawer-backdrop{{display:none !important}}", "print2B")
    opt("  nav.tabs,.to-top,.study-fab,.study-modal,.img-lightbox{{display:none !important}}",
        "  nav.tabs,.to-top,.study-fab,.study-drawer,.study-drawer-backdrop,.img-lightbox{{display:none !important}}", "print2A")
    # (1b) DRAWER_CSS를 첫 .study-modal 규칙 앞에 삽입한 뒤, 남은 모든 .study-modal 규칙을 제거
    #      (세대별로 모달 CSS 블록 경계가 제각각 → 정확한 끝 문자열 대신 규칙 단위 정규식 제거가 견고)
    css_start = ".study-modal{{position:fixed;inset:0;z-index:300;"
    pos = t.index(css_start)
    t = t[:pos] + DRAWER_CSS + "\n" + t[pos:]
    t, nrm = re.subn(r'\.study-modal[^{}\n]*\{\{[^{}]*\}\}', '', t)
    assert nrm >= 3, f"[FAIL] {rel} 모달 CSS 규칙 제거 {nrm}건 (예상 ≥3)"
    if GEN == "B":
        js_s = "  const modal = document.createElement('div');"
        js_e = "      if (window.MathJax && window.MathJax.typesetPromise) window.MathJax.typesetPromise([modalBody]).catch(()=>{});\n    });\n  });"
        i = t.index(js_s); j = t.index(js_e, i) + len(js_e)
        t = t[:i] + DRAWER_JS + t[j:]
    else:
        js_s = "  const modal = document.querySelector('.study-modal');"
        js_e = ("  if (modal){\n    modal.addEventListener('click', e => {\n"
                "      if (e.target === modal || e.target.classList.contains('study-modal-close')) closeModal();\n    });\n  }")
        i = t.index(js_s); j = t.index(js_e, i) + len(js_e)
        t = t[:i] + DRAWER_JS.replace("STUDY_GUIDES_PLACEHOLDER", "STUDY_DATA") + t[j:]
        sub1('<div class="study-modal" role="dialog" aria-modal="true" aria-labelledby="study-modal-title">\n'
             '  <div class="study-modal-card">\n    <div class="study-modal-head">\n'
             '      <h3 class="study-modal-title" id="study-modal-title">학습 가이드</h3>\n'
             '      <button class="study-modal-close" type="button" aria-label="닫기">×</button>\n'
             '    </div>\n    <div class="study-modal-body"></div>\n  </div>\n</div>\n', "", "BODY modal 제거")

    # 2. 호환 셤 + Region A
    mark = "# ----------------------------------------------------------------\n# Tab 1.5 - Paper Study"
    anchor = 'tab_reading = "\\n".join(render_section(s) for s in struct["sections"])'
    sub1(anchor, anchor + "\n\n" + SHIM + REGION_A, "region A + shim")
    # 3. STUDY_CSS / 모바일
    foot = "footer.foot{{text-align:center;margin-top:40px;color:var(--muted);font-size:12.5px}}"
    sub1(foot, "{STUDY_CSS}\n" + foot, "STUDY_CSS")
    mob = ".knw-grid,.coach-grid,.fund-grid,.diss-grid,.eq-grid{{grid-template-columns:1fr}}"
    sub1(mob, mob + "\n  .verdict-grid{{grid-template-columns:1fr}}\n  .study-thumbs{{grid-template-columns:repeat(2,minmax(0,1fr))}}\n  .study-toolbar{{flex-direction:column;align-items:flex-start}}", "mobile")
    # 4. 호버 위임
    assert len(HOVER_RE.findall(t)) == 1, f"[FAIL] {rel} hover"
    t = HOVER_RE.sub(lambda m: HOVER_NEW, t, count=1)
    # 5. studyNav
    btn = "  buttons.forEach(b => b.addEventListener('click', () => activate(b.dataset.tab)));"
    sub1(btn, btn + "\n\n  function studyNav(tab){ activate(tab); } /*STUDY-NAV*/", "studyNav")
    # 6. autoLink 셀렉터 확장
    t, k = re.subn(r"(querySelectorAll\('\.tab-pane \.col p[^']*)'\)",
                   r"\1, .study-claude-body p, .study-guide, .study-qlist li, .v-claim, .v-note, .alt-card p, .v-claude-body p')", t, count=1)
    assert k == 1, f"[FAIL] {rel} autoLink"
    # 7. lightbox 훅 (lightbox 있는 논문만 - 뷰어 이미지 클릭 시 확대. 없으면 window.__lbOpen 미정의 → no-op)
    if HAS_LB and GEN == "B":
        sub1("      lb.classList.remove('open');\n      document.body.style.overflow = '';\n    }",
             "      lb.classList.remove('open');\n      var avOpen = document.querySelector('.asset-viewer.open');\n"
             "      document.body.style.overflow = avOpen ? 'hidden' : '';\n    }\n    window.__lbOpen = lbOpen;", "lbCloseFn B")
    elif HAS_LB:  # GEN A + lightbox
        sub1("    lightbox.classList.add('open');\n    document.body.style.overflow = 'hidden';\n  }",
             "    lightbox.classList.add('open');\n    document.body.style.overflow = 'hidden';\n  }\n  window.__lbOpen = lbOpen;", "lbOpen A")
        sub1("  function lbClose(){\n    if (!lightbox) return;\n    lightbox.classList.remove('open');\n"
             "    document.body.style.overflow = '';\n    lbReset();\n  }",
             "  function lbClose(){\n    if (!lightbox) return;\n    lightbox.classList.remove('open');\n"
             "    document.body.style.overflow = document.querySelector('.asset-viewer.open') ? 'hidden' : '';\n    lbReset();\n  }", "lbClose A")
    # 8~11. 모듈 JS / 마크업 / nav / pane
    sub1("})();\n</script>", MODULE_JS + "\n})();\n</script>", "module JS")
    if HAS_LB:
        sub1('<div class="img-lightbox" role="dialog"', VIEWER_MARKUP + '<div class="img-lightbox" role="dialog"', "viewer markup")
    else:  # lightbox 없는 논문: 뷰어/리더 마크업을 JS 조립 직전(BODY 끝)에 삽입
        anchor = "{JS_FINAL}" if "{JS_FINAL}" in t else "{JS}"
        sub1(anchor, VIEWER_MARKUP + anchor, "viewer markup (no-lb)")
    sub1('<button class="tab-btn active" data-tab="tab-reading">① 원문 / 번역</button>',
         '<button class="tab-btn active" data-tab="tab-reading">① 원문 / 번역</button>\n    <button class="tab-btn" data-tab="tab-study">①′ Paper Study</button>', "nav")
    sub1("{tab_reading}\n  </section>",
         "{tab_reading}\n  </section>\n  <section id=\"tab-study\" class=\"tab-pane\">\n{tab_study}\n  </section>", "pane")
    # 12. 조립 체인
    if GEN == "B":
        sub1('JS_FINAL = JS.replace("STUDY_GUIDES_PLACEHOLDER", study_json)',
             'meta_early = config.get("metadata") or config.get("meta")\n'
             'JS_FINAL = (JS.replace("STUDY_GUIDES_PLACEHOLDER", study_json)\n'
             '              .replace("STUDY_SHORT_PLACEHOLDER", json.dumps(meta_early["short_name"], ensure_ascii=False))\n'
             '              .replace("AV_DATA_PLACEHOLDER", json.dumps(AV_DATA, ensure_ascii=False)))', "chain B")
    else:
        sub1('JS = JS.replace("__STUDY_JSON__", STUDY_JSON)',
             'JS = JS.replace("__STUDY_JSON__", STUDY_JSON)'
             '.replace("STUDY_SHORT_PLACEHOLDER", json.dumps(meta["short_name"], ensure_ascii=False))'
             '.replace("AV_DATA_PLACEHOLDER", json.dumps(AV_DATA, ensure_ascii=False))', "chain A")

    ast.parse(t)
    p.write_text(t, encoding="utf-8")
    print(f"[ok] {rel}  (GEN {GEN}, syntax ok)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    retrofit(sys.argv[1] if sys.argv[1].endswith("_build.py") else sys.argv[1].rstrip("/\\") + "/_build.py")
