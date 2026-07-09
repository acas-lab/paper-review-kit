# -*- coding: utf-8 -*-
"""자립형 학습 메모(플로팅 버튼 + 드로어)를 v4 논문에 주입.

대상: 이미 v4 대시보드지만 Paper Study 모듈(sget/sset·notes 시스템)이 없어
`paper_study_retrofit.py`(빌더 필요)를 못 쓰는 논문 — 특히 _build.py가 없는
papers 1~3 (SAFE / FrameFusion / SGL, 대화형·수작업 빌드).

정본 CARES의 메모는 Paper Study 모듈 JS 안에 통합돼 있어(sget/sset 의존) 그대로
떼어낼 수 없다. 이 도구는 **자체 localStorage 키(`prstudy:{SHORT}:memo`)** 를 가진
자립형 IIFE + CSS를 `</body>` 직전에 additive 로 주입한다 (기존 마크업·콘텐츠 무변경).

- z-index 1650 (본문 리더·자산 뷰어·자산 학습 드로어 위, 라이트박스 아래) — 2026-07-09 규약
- 저장: `prstudy:{SHORT}:memo` plain text, 400ms 디바운스 자동 저장
- 버튼 위치: topbar 하단 +18px (리사이즈 대응), 드로어 열리면 버튼 숨김

사용법: python tools/memo_inject.py "papers/N. shortname"
검증: 재실행 시 이미 있으면 skip (idempotent).

정본 사례: papers 1~3 (2026-07-09).
"""
import re
import sys
from pathlib import Path

MEMO_CSS = """
/* ==== 자립형 학습 메모 (memo_inject.py, z-index 1650) ==== */
.memo-fab{position:fixed;right:26px;top:150px;z-index:1650;font:inherit;font-size:13px;font-weight:800;color:var(--amber);background:var(--amber-soft);border:1px solid var(--amber);border-radius:999px;padding:9px 18px;cursor:pointer;box-shadow:0 6px 18px rgba(48,53,66,0.14);display:inline-flex;align-items:center;gap:7px}
.memo-fab:hover{color:#ffffff;background:var(--amber)}
.memo-fab .memo-dot{width:8px;height:8px;border-radius:50%;background:var(--amber);flex-shrink:0}
.memo-fab:hover .memo-dot{background:#ffffff}
.memo-drawer{position:fixed;top:0;right:0;height:100vh;width:380px;max-width:92vw;background:var(--paper);border-left:1px solid var(--line);box-shadow:-12px 0 36px rgba(30,34,46,0.14);transform:translateX(100%);transition:transform 240ms ease;z-index:1650;display:flex;flex-direction:column}
.memo-drawer.open{transform:translateX(0)}
.memo-head{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:16px 18px 8px}
.memo-title{font-weight:800;font-size:14px;color:var(--amber)}
.memo-close{border:1px solid var(--line);background:#ffffff;border-radius:50%;width:30px;height:30px;font-size:16px;line-height:1;color:var(--muted);cursor:pointer;flex-shrink:0}
.memo-close:hover{color:var(--amber);border-color:var(--amber)}
.memo-hint{margin:0 18px 10px;font-size:11.5px;color:var(--muted);line-height:1.6}
.memo-pad{flex:1;margin:0 18px;font:inherit;font-size:13.5px;line-height:1.7;border:1px solid var(--line);border-radius:10px;padding:12px;resize:none;background:#fafbfc;color:var(--ink)}
.memo-pad:focus{outline:none;border-color:var(--amber);box-shadow:0 0 0 3px var(--amber-soft)}
.memo-status{display:flex;justify-content:space-between;padding:8px 18px 14px;font-size:11px;color:var(--muted)}
@media print{.memo-drawer,.memo-fab{display:none !important}}
"""

# {SHORT} 자리표시자를 실제 short 로 치환해 주입
MEMO_JS = """
<script>
/* ==== 자립형 학습 메모 (memo_inject.py) — 자체 localStorage 키, Paper Study 모듈 비의존 ==== */
(function(){
  var SHORT = "__SHORT__";
  var KEY = "prstudy:" + SHORT + ":memo";
  function mget(){ try { return localStorage.getItem(KEY) || ""; } catch(e){ return ""; } }
  function mset(v){ try { localStorage.setItem(KEY, v); } catch(e){} }

  var memoFab = document.createElement('button');
  memoFab.className = 'memo-fab';
  memoFab.type = 'button';
  memoFab.innerHTML = '\\uBA54\\uBAA8<span class="memo-dot" hidden></span>';
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
    '<div class="memo-head"><span class="memo-title">\\uD559\\uC2B5 \\uBA54\\uBAA8</span>' +
    '<button class="memo-close" type="button" aria-label="\\uB2EB\\uAE30">\\u00D7</button></div>' +
    '<p class="memo-hint">\\uC790\\uC720\\uB86D\\uAC8C \\uC801\\uB294 \\uBA54\\uBAA8\\uC7A5 \\u2014 \\uC4F0\\uB294 \\uB300\\uB85C \\uC790\\uB3D9 \\uC800\\uC7A5\\uB429\\uB2C8\\uB2E4.</p>' +
    '<textarea class="memo-pad" placeholder="\\uAD81\\uAE08\\uD55C \\uAC83, \\uC774\\uD574 \\uC548 \\uB418\\uB294 \\uAC83, \\uB098\\uC911\\uC5D0 \\uD655\\uC778\\uD560 \\uAC83\\u2026"></textarea>' +
    '<div class="memo-status"><span class="memo-len">0\\uC790</span><span class="memo-saved"></span></div>';
  document.body.appendChild(md);
  var memoPad = md.querySelector('.memo-pad');
  var memoLen = md.querySelector('.memo-len');
  var memoSaved = md.querySelector('.memo-saved');
  var memoDot = memoFab.querySelector('.memo-dot');
  function memoPaint(){
    memoLen.textContent = memoPad.value.trim().length + '\\uC790';
    memoDot.hidden = memoPad.value.trim().length === 0;
  }
  (function memoLoad(){
    var v = mget();
    if (v && v.charAt(0) === '['){ // \\uAD6C\\uBC84\\uC804(\\uD56D\\uBAA9 \\uBC30\\uC5F4) \\u2192 \\uD14D\\uC2A4\\uD2B8 \\uB9C8\\uC774\\uADF8\\uB808\\uC774\\uC158
      try { var arr = JSON.parse(v); if (Array.isArray(arr)){ v = arr.map(function(m){ return m.q; }).join('\\n\\n'); mset(v); } } catch(e){}
    }
    memoPad.value = v || '';
    memoPaint();
  })();
  var memoTimer;
  memoPad.addEventListener('input', function(){
    memoPaint();
    clearTimeout(memoTimer);
    memoTimer = setTimeout(function(){
      mset(memoPad.value);
      var d = new Date();
      memoSaved.textContent = '\\uC790\\uB3D9 \\uC800\\uC7A5\\uB428 ' + d.getHours() + ':' + ('0' + d.getMinutes()).slice(-2);
    }, 400);
  });
  function memoOpen(open){
    md.classList.toggle('open', open);
    memoFab.style.display = open ? 'none' : '';
    if (open) memoPad.focus();
  }
  memoFab.addEventListener('click', function(){ memoOpen(true); });
  md.querySelector('.memo-close').addEventListener('click', function(){ memoOpen(false); });
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && md.classList.contains('open')) memoOpen(false); });
})();
</script>
"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: python tools/memo_inject.py \"papers/N. shortname\"")
    folder = Path(sys.argv[1])
    htmls = list(folder.glob("*_output.html"))
    if len(htmls) != 1:
        raise SystemExit(f"[FAIL] expected 1 *_output.html in {folder}, found {len(htmls)}")
    html = htmls[0]
    short = html.name.replace("_output.html", "")
    text = html.read_text(encoding="utf-8")

    if "memo-fab" in text:
        print(f"[SKIP] {html.name}: memo-fab already present")
        return
    if text.count("</body>") != 1:
        raise SystemExit(f"[FAIL] {html.name}: expected exactly 1 </body>")
    if "--amber" not in text:
        raise SystemExit(f"[FAIL] {html.name}: --amber CSS var missing (not v4?)")

    block = "<style>" + MEMO_CSS + "</style>\n" + MEMO_JS.replace("__SHORT__", short)
    text = text.replace("</body>", block + "\n</body>", 1)
    html.write_text(text, encoding="utf-8")

    # verify
    check = html.read_text(encoding="utf-8")
    assert check.count(".memo-fab{") >= 1, "memo CSS not injected"
    assert 'var SHORT = "' + short + '"' in check, "memo JS SHORT not injected"
    assert 'KEY = "prstudy:" + SHORT + ":memo"' in check, "memo JS key builder not injected"
    assert check.count("z-index:1650") >= 2, "z-index 1650 not present twice"
    print(f"[OK]   {html.name}: memo injected (SHORT={short}, key=prstudy:{short}:memo)")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
