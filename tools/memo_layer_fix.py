# -*- coding: utf-8 -*-
"""학습 메모를 '항상 쓸 수 있는' 최상위 레이어로 승격 + 다른 오버레이와의 겹침 해소.

배경 (2026-09-02 발견)
---------------------
2026-07-09 규약은 메모 z-index 를 1650 으로 못박았지만, 그 수정은 **빌드된 HTML 에만**
적용되고 `_build.py` 템플릿에는 반영되지 않았다. 그 결과 CARES(26) 이후 `_build.py` 를
복사해 만든 papers 27~35 는 전부 `memo-fab: z-index 205 / memo-drawer: 300` 으로 회귀했다.
이 값은 라이트박스(2000) · 노트 선택(1700) · 학습 가이드 드로어(1600) · 자산 뷰어(1500) ·
플로팅 리더(1450) 아래라, 그 중 하나라도 열리면 메모 버튼이 사라진다.

z-index 를 올리는 것만으로는 부족하다. 학습 가이드 드로어와 메모 드로어는 둘 다
`right:0` 이라 세로로 겹치고, 라이트박스류는 `inset:0` 으로 화면을 덮는다. 그래서
**세로 순서(z) + 가로 자리(right)** 를 함께 정리한다.

v5 (2026-09-02) - 좁은 화면에서 자리 배분이 무너지던 문제
--------------------------------------------------------
v4 는 "메모가 열리면 오버레이를 메모+가이드 폭만큼 좁힌다"를 **상한 없이** 적용했다.
1600px 에서는 문제가 없지만 1080px 에서 가이드(440) + 메모(380) 가 함께 열리면
오버레이에 260px 만 남아 자산 뷰어가 세로 한 줄로 뭉개진다(내부 `.av-panel` 은
`calc(95vw - 820px)` = 206px). `@media (min-width:1000px)` 게이트는 1080px 을
통과시키므로 방어가 되지 않았다.

v5 는 축소량을 **남는 폭 기준으로 판정**한다.
  - 가이드 옆에 메모가 나란히 서는 것은 `vw - 메모 - 가이드` 가 읽을 수 있을 때만.
    자리가 없으면 메모는 가이드 **위에** 뜬다(z 2400 > 1600).
  - 오버레이 축소도 `0.95·vw - 예약폭 >= 560px` 일 때만 한다. 가이드 몫을 빼면
    들어가는 경우에는 메모 폭만 예약하고, 그것마저 안 되면 축소를 포기해 메모가
    오버레이 위에 뜬다(`mlx-float`). 좁혀서 못 읽게 만드는 것보다 낫고, 메모를
    닫으면 오버레이는 즉시 원래 폭으로 돌아온다.
  - CSS 의 각 `calc()` 에 `max()` 로 하한을 박아, JS 판정이 한 프레임 늦어도 패널이
    하한 아래로 찌그러지지 않는다.

이 도구가 하는 일
-----------------
1. `.memo-fab` / `.memo-drawer` 를 z-index 2400 으로 올린다 (라이트박스 2000 위).
2. 학습 가이드 드로어가 열리면 메모 버튼·드로어를 그 **왼쪽으로 비켜** 나란히 놓는다
   (자리가 있을 때만 - 좁으면 위로 겹쳐 띄운다).
3. 메모 드로어가 열리면 전체화면 오버레이(라이트박스·자산 뷰어·플로팅 리더·노트 선택)의
   `right` 를 메모 폭만큼 좁혀 **메모와 겹치지 않게** 한다. 단 남는 폭이 하한 미만이면
   축소하지 않는다.
4. 메모에 포커스가 있는 동안의 키 입력을 가둔다 - ESC 는 메모만 닫고, 화살표·문자키가
   플로팅 리더/라이트박스 단축키로 새지 않는다.
5. 메모 **바깥을 두 번 연속 클릭**하면 메모를 닫는다(한 번 클릭으로는 닫지 않는다 -
   그림·문장·가이드를 클릭하며 읽는 도중에 메모가 저절로 사라지면 안 되기 때문).

v6 (2026-09-02) - 가이드가 메모 뒤로 사라지던 문제 + 이미지 전용 모드
--------------------------------------------------------------------
v5 는 자리가 부족하면 메모를 가이드 **위에** 띄웠는데, 그러면 정작 가이드가 안 보인다.
1080px 에서 가이드(440) + 메모(380) 가 그 경우였다. v6 은 **좁은 화면에서 두 드로어를
함께 줄여**(가이드 `clamp(300, 36vw, 440)` · 메모 `clamp(280, 32vw, 380)`) 나란히 서는
구간을 넓히고, 동시에 **학습 가이드를 열면 자산 뷰어를 이미지 전용으로 전환**한다 -
원문 캡션·번역(`.av-text`)은 가이드가 대신하므로 감추고, 그만큼 이미지를 키운다
(`.av-img img{max-height:82vh}`). 이미지만 남으면 필요한 폭이 작아지므로(560 → 260)
세 패널이 1080px 에서도 공존한다. 가이드를 닫으면 캡션·번역이 그대로 돌아온다.

additive · idempotent · 업데이터(구버전 블록 제거 후 재주입). 기존 마크업·콘텐츠 무변경.

사용법:
    python tools/memo_layer_fix.py "papers/N. shortname"
    python tools/memo_layer_fix.py --all
"""
import re
import sys
from pathlib import Path

VERSION = "v6"
BEGIN = f"<!-- MEMO-LAYER-FIX {VERSION} (tools/memo_layer_fix.py) -->"
END = "<!-- /MEMO-LAYER-FIX -->"
# 구버전까지 싹 지우기 위한 범용 패턴
STRIP_RE = re.compile(
    r"<!-- MEMO-LAYER-FIX .*?-->.*?<!-- /MEMO-LAYER-FIX -->\s*",
    re.S,
)

CSS = """
<style>
/* ---- 메모를 최상위 레이어로: 라이트박스(2000)·노트선택(1700)·학습가이드(1600)·자산뷰어(1500)·리더(1450) 위 ---- */
:root{--memo-w:380px;--sd-w:440px;--memo-gap:26px;--overlay-right:0px}
.memo-fab{z-index:2400 !important;transition:right 200ms ease}
.memo-drawer{z-index:2400 !important;transition:transform 240ms ease,right 200ms ease}

/* ---- 학습 가이드 드로어 옆에 나란히 선다 - 자리가 있을 때만 (JS 가 판정해 클래스를 붙인다) ---- */
body.mlx-sd .memo-fab{right:calc(var(--memo-gap) + var(--sd-w))}
body.mlx-sd-side .memo-drawer{right:var(--sd-w);box-shadow:-12px 0 30px rgba(30,34,46,0.12)}

/* ---- 메모가 열리면 전체화면 오버레이를 그만큼 좁힌다 - 남는 폭이 읽을 수 있을 때만 ---- */
body.mlx-memo.mlx-shrink .img-lightbox,
body.mlx-memo.mlx-shrink .asset-viewer,
body.mlx-memo.mlx-shrink .para-reader,
body.mlx-memo.mlx-shrink .notes-picker,
/* .study-modal 이라도 실제로는 440px 사이드 드로어인 세대(papers 24 계열)가 있다.
   그런 요소는 JS 가 .mlx-side 로 표시하며, 옆자리를 이미 배정받았으므로 축소 대상에서 뺀다. */
body.mlx-memo.mlx-shrink .study-modal:not(.mlx-side){right:var(--overlay-right)}
body.mlx-memo.mlx-shrink .asset-viewer.av-shift{padding-right:22px;justify-content:center}
body.mlx-memo.mlx-shrink .img-lightbox-stage{max-width:max(520px,calc(96vw - var(--overlay-right)))}
body.mlx-memo.mlx-shrink .img-lightbox img{max-width:min(100%,max(520px,calc(96vw - var(--overlay-right))))}
body.mlx-memo.mlx-shrink .img-lightbox-caption{max-width:max(340px,calc(80vw - var(--overlay-right)))}
/* 오버레이 안이지만 position:fixed 라 뷰포트에 붙어 있는 조각(구세대 라이트박스 닫기 버튼·힌트)은 직접 밀어준다 */
body.mlx-memo.mlx-shrink .mlx-shift-x{margin-right:var(--overlay-right)}
body.mlx-memo.mlx-shrink .mlx-shift-half{margin-left:calc(-1 * var(--overlay-right) / 2)}
body.mlx-memo.mlx-shrink .pr-panel{width:min(1080px,max(540px,calc(95vw - var(--overlay-right))))}
body.mlx-memo.mlx-shrink .np-panel{width:min(520px,max(340px,calc(94vw - var(--overlay-right))))}
body.mlx-memo.mlx-shrink .av-panel{max-width:min(1240px,max(540px,calc(95vw - var(--overlay-right))))}

/* ---- 좁은 화면에서는 두 드로어를 함께 줄여 가운데에 볼 자리를 만든다 (메모가 가이드를 덮지 않도록) ---- */
body.mlx-narrow .study-drawer,
body.mlx-narrow .mlx-side{width:var(--sd-w)}
body.mlx-narrow .memo-drawer{width:var(--memo-w)}

/* ---- 학습 가이드를 열면 자산 뷰어는 이미지 전용이 된다 - 원문 캡션·번역은 가이드가 대신한다 ---- */
body.mlx-guided .asset-viewer .av-text{display:none}
body.mlx-guided .asset-viewer .av-body{flex-direction:column}
body.mlx-guided .asset-viewer .av-img{flex:1 1 auto;padding:10px;align-items:center}
body.mlx-guided .asset-viewer .av-img img{max-height:82vh;max-width:100%}
body.mlx-guided .asset-viewer .av-panel{width:min(1240px,max(260px,calc(95vw - var(--overlay-right))));max-width:none}
/* 가이드가 열려 있으면 뷰어를 그 폭만큼 왼쪽으로 - 논문 자체 규칙(470px 고정)을 실제 폭으로 교정 */
body.mlx-sd .asset-viewer.av-shift{padding-right:calc(var(--sd-w) + 22px)}

/* ---- 좁아서 축소를 포기한 경우: 메모가 오버레이 위에 뜬다 (찌그러뜨리는 것보다 낫다) ---- */
body.mlx-memo.mlx-float .memo-drawer{box-shadow:-20px 0 48px rgba(20,22,30,0.34)}
@media print{.memo-fab,.memo-drawer{display:none !important}}
</style>
"""

JS = """
<script>
/* ==== 메모 상시 접근 레이어 (memo_layer_fix.py v5) - 열린 오버레이를 감지해 자리를 배분 ==== */
(function(){
  var SEL = '.memo-drawer,.study-drawer,.study-modal,.img-lightbox,.asset-viewer,.para-reader,.notes-picker';
  var OVER = '.img-lightbox.open,.asset-viewer.open,.para-reader.open,.notes-picker.open';
  var MIN_OVER = 560;   // 오버레이 패널이 읽을 수 있는 최소 폭
  var MIN_PAGE = 360;   // 오버레이가 없을 때 본문에 남겨 둘 최소 폭
  var MIN_IMG  = 260;   // 이미지 전용 모드(가이드가 캡션을 대신)일 때의 최소 폭
  var raf = 0;

  function clamp(lo, v, hi){ return Math.max(lo, Math.min(v, hi)); }

  function sync(){
    raf = 0;
    var body = document.body;
    if (!body) return;
    var vw = window.innerWidth || document.documentElement.clientWidth || 0;

    var memo = document.querySelector('.memo-drawer');
    var memoOpen = !!(memo && memo.classList.contains('open'));

    // 열린 학습 가이드가 "옆에 설 수 있는 사이드 드로어"인지, 화면을 덮는 모달(구세대 SGL)인지 구분한다.
    // 모달이면 옆자리가 없으므로 전체화면 오버레이와 같은 취급을 한다.
    var cand = document.querySelector('.study-drawer.open, .study-modal.open');
    var sd = null, modal = null;
    if (cand){
      var cw = cand.offsetWidth || 0;
      if (cw > 0 && cw <= vw * 0.6) sd = cand;
      else if (cw > 0) modal = cand;
    }
    // 사이드 드로어로 취급하기로 한 요소를 표시해 둔다 - 클래스가 .study-modal 이어도(papers 24 계열)
    // 옆자리를 배정받은 이상 오버레이 축소 대상에서 빠져야 한다.
    var prevSide = document.querySelector('.mlx-side');
    if (prevSide && prevSide !== sd) prevSide.classList.remove('mlx-side');
    if (sd) sd.classList.add('mlx-side');

    var over = document.querySelector(OVER) || modal;
    var viewer = document.querySelector('.asset-viewer.open');
    // 가이드 + 자산 뷰어 = 이미지 전용 모드. 원문 캡션·번역은 가이드가 대신하므로 감추고 이미지를 키운다.
    var guided = !!(sd && viewer);

    // 좁은 화면에서는 두 드로어를 함께 줄여, 메모가 가이드를 덮지 않고도 가운데에 볼 자리가 남게 한다.
    var narrow = vw < 1200;
    var sdW = sd ? (narrow ? clamp(300, Math.round(vw * 0.36), 440) : (sd.offsetWidth || 440)) : 0;
    var memoW = memoOpen ? (narrow ? clamp(280, Math.round(vw * 0.32), 380) : (memo.offsetWidth || 380)) : 0;

    // 남는 폭이 읽을 수 있는가 - 오버레이 패널은 vw 기준 95% 안에서 다시 좁아지므로 그것까지 감안한다.
    function fits(reserve){
      if (!over) return vw - reserve >= MIN_PAGE;
      if (guided) return vw - reserve >= MIN_IMG;
      return vw * 0.95 - reserve >= MIN_OVER;
    }

    // 1) 메모 드로어가 가이드 옆에 나란히 설 자리가 있는가. 없으면 메모가 가이드 위에 뜬다.
    var sideBySide = !!sd && memoOpen && fits(memoW + sdW);
    // 2) 가이드만 열렸을 때 메모 버튼을 그 왼쪽에 둘 자리가 있는가.
    var fabAside = !!sd && (vw - sdW >= 300);

    // 3) 오버레이를 좁힐 수 있는가 - 좁히고 남는 폭이 하한 미만이면 축소를 포기한다.
    //    나란히 서면 두 폭의 합, 겹쳐 뜨면 둘 중 넓은 쪽이 오른쪽에 예약해야 할 띠의 폭이다.
    var reserve = sideBySide ? (memoW + sdW) : Math.max(memoW, sd ? sdW : 0);
    var shrink = memoOpen && !!over && fits(reserve);
    if (memoOpen && over && !shrink && reserve !== memoW && fits(memoW)){
      reserve = memoW;          // 가이드 몫을 포기하면 들어가는 경우
      shrink = true;
    }
    if (!shrink) reserve = 0;

    body.classList.toggle('mlx-memo', memoOpen);
    body.classList.toggle('mlx-sd', fabAside);
    body.classList.toggle('mlx-sd-side', sideBySide);
    body.classList.toggle('mlx-shrink', shrink);
    body.classList.toggle('mlx-float', memoOpen && !!over && !shrink);
    body.classList.toggle('mlx-narrow', narrow);
    body.classList.toggle('mlx-guided', guided);

    var root = document.documentElement;
    if (sd) root.style.setProperty('--sd-w', sdW + 'px');
    root.style.setProperty('--memo-w', (narrow ? clamp(280, Math.round(vw * 0.32), 380) : 380) + 'px');
    root.style.setProperty('--overlay-right', reserve + 'px');
  }
  function schedule(){ if (!raf) raf = requestAnimationFrame(sync); }

  // 오버레이 폭을 좁히면 그 안의 position:fixed 자식은 여전히 뷰포트 기준이라 따라오지 않는다.
  // 세대마다 닫기 버튼이 absolute(신)/fixed(구)로 갈리므로 계산된 스타일로 판별해 표시만 해 둔다.
  function markFixed(el){
    if (el.__mlxfx) return;
    el.__mlxfx = 1;
    var kids = el.querySelectorAll('*');
    for (var j = 0; j < kids.length; j++){
      var cs = getComputedStyle(kids[j]);
      if (cs.position !== 'fixed') continue;
      if (cs.left === 'auto' && cs.right !== 'auto') kids[j].classList.add('mlx-shift-x');
      else if (cs.right === 'auto' && cs.left !== 'auto' && cs.transform !== 'none') kids[j].classList.add('mlx-shift-half');
    }
  }

  // 구세대 자산 해설(.study-modal)은 "바깥 클릭이면 닫는다"를 document 에 걸어 둔다.
  // 그 바깥에는 메모 버튼·드로어도 포함되므로, 메모를 누르면 해설이 닫혀 버린다.
  // 메모 UI 안에서 시작한 클릭은 document 까지 올려보내지 않아 그 오작동을 막는다.
  function sealClicks(el){
    if (el.__mlxseal) return;
    el.__mlxseal = 1;
    el.addEventListener('click', function(e){ e.stopPropagation(); });
    el.addEventListener('mousedown', function(e){ e.stopPropagation(); });
  }

  function attach(){
    var n = document.querySelectorAll(SEL);
    for (var i = 0; i < n.length; i++){
      if (!n[i].__mlx){
        n[i].__mlx = 1;
        new MutationObserver(schedule).observe(n[i], {attributes:true, attributeFilter:['class','style']});
      }
      if (n[i].className.indexOf('memo-drawer') < 0) markFixed(n[i]);
    }
    var mf = document.querySelector('.memo-fab');
    if (mf) sealClicks(mf);
    var mdEl = document.querySelector('.memo-drawer');
    if (mdEl) sealClicks(mdEl);
  }

  function boot(){
    if (!document.body) return;
    attach();
    schedule();
    new MutationObserver(function(){ attach(); schedule(); })
      .observe(document.body, {childList:true});
    window.addEventListener('resize', schedule);
    window.addEventListener('orientationchange', schedule);

    // 메모 바깥을 두 번 연속 클릭하면 메모를 닫는다. 한 번 클릭으로 닫지 않는 이유는
    // 그림·문장·가이드를 클릭하며 읽는 도중에 메모가 저절로 사라지면 안 되기 때문이다.
    document.addEventListener('dblclick', function(e){
      var d = document.querySelector('.memo-drawer');
      if (!d || !d.classList.contains('open')) return;
      var t = e.target;
      if (t && t.closest && t.closest('.memo-drawer,.memo-fab')) return;
      var b = d.querySelector('.memo-close');
      if (b) b.click();
    }, true);

    // 메모에 포커스가 있는 동안의 키는 페이지 단축키로 새지 않게 가둔다.
    // ESC = 메모만 닫기(뒤의 라이트박스·드로어는 그대로), 화살표·문자키는 리더 이동에 쓰이지 않게.
    window.addEventListener('keydown', function(e){
      var t = e.target;
      if (!t || !t.closest || !t.closest('.memo-drawer')) return;
      if (e.key === 'Escape'){
        var b = document.querySelector('.memo-drawer .memo-close');
        if (b) b.click();
      }
      e.stopPropagation();
    }, true);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  // 메모/드로어가 뒤늦게 생성되는 구현(papers 1~3의 자립형 주입)까지 붙잡는다
  var tries = 0;
  var iv = setInterval(function(){ attach(); schedule(); if (++tries > 40) clearInterval(iv); }, 150);
})();
</script>
"""

BLOCK = BEGIN + CSS + JS + END + "\n"


def patch(folder: Path) -> str:
    htmls = list(folder.glob("*_output.html"))
    if len(htmls) != 1:
        return f"[SKIP] {folder.name}: *_output.html {len(htmls)}개"
    html = htmls[0]
    text = html.read_text(encoding="utf-8")

    if "memo-fab" not in text:
        return f"[SKIP] {html.name}: memo-fab 없음 (메모 미주입 논문)"
    if text.count("</body>") != 1:
        return f"[FAIL] {html.name}: </body> 개수 {text.count('</body>')}"

    had = "MEMO-LAYER-FIX" in text
    text = STRIP_RE.sub("", text)
    text = text.replace("</body>", BLOCK + "</body>", 1)
    html.write_text(text, encoding="utf-8")

    check = html.read_text(encoding="utf-8")
    assert check.count(BEGIN) == 1, "블록 1회 주입 실패"
    for old in ("MEMO-LAYER-FIX v4", "MEMO-LAYER-FIX v5"):
        assert old not in check, f"구버전({old}) 블록 잔존"
    assert check.count("z-index:2400 !important") == 2, "z-index 승격 누락"
    for cls in ("mlx-memo", "mlx-sd-side", "mlx-shrink", "mlx-float", "mlx-narrow", "mlx-guided"):
        assert cls in check, f"body 상태 클래스 누락: {cls}"
    verb = "갱신" if had else "주입"
    return f"[OK]   {html.name}: 메모 레이어 {verb} (z=2400 · 자리 배분 · 이미지 전용 · 더블클릭 닫기)"


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage: python tools/memo_layer_fix.py "papers/N. name" | --all')
    root = Path(__file__).resolve().parent.parent
    if sys.argv[1] == "--all":
        targets = sorted(
            (p for p in (root / "papers").iterdir() if p.is_dir()),
            key=lambda p: int(re.match(r"(\d+)", p.name).group(1)) if re.match(r"\d+", p.name) else 999,
        )
    else:
        targets = [Path(sys.argv[1])]

    fails = 0
    for t in targets:
        line = patch(t)
        if line.startswith("[FAIL]"):
            fails += 1
        print(line)
    if fails:
        raise SystemExit(f"\n{fails}건 실패")


if __name__ == "__main__":
    main()
