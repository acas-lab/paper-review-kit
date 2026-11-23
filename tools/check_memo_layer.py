# -*- coding: utf-8 -*-
"""메모 레이어 회귀 검사 - 학습 메모가 어떤 오버레이 위에서도 쓰이는지 실제 브라우저로 확인.

`tools/memo_layer_fix.py` 가 보장해야 하는 성질을 헤드리스 Chromium 으로 직접 측정한다.
정적 grep 으로는 z-index 숫자만 볼 수 있고 "실제로 겹치는가"는 볼 수 없어서, 이 검사는
bounding box 교집합 넓이가 0인지를 본다.

검사 항목
  1. 메모 버튼이 우측 상단에 보이고 z-index 2400
  2. 학습 가이드 드로어를 연 뒤에도 메모 버튼이 보이고 드로어와 겹치지 않음
  3. 드로어가 열린 채 메모를 열면 둘이 나란히(겹침 0) 서고, 타이핑해도 드로어가 닫히지 않음
  4. 메모 안 ESC 는 메모만 닫고 뒤의 드로어는 유지
  5. 라이트박스(이미지 확대) 위에서도 메모 버튼이 보이고, 메모를 열면 확대 이미지·닫기
     버튼과 겹치지 않으며, 타이핑·화살표가 페이지 단축키로 새지 않음
  6. 콘솔 JS 오류 0건
  7. **좁은 화면(1080px · 950px)** - 자산 뷰어 + 학습 가이드 + 메모를 동시에 열었을 때
     ① 뷰어가 세로 적층(`body.mlx-av-stack`)으로 바뀌고 캡션·번역이 감춰지지 않으며,
     위→아래 순서가 이미지 → 원문 캡션 → 번역 → 해석 보기, 이미지 폭 >= min(240px, 원본 폭)
     ② 메모 ↔ 가이드 겹침 0, 둘 다 화면 안에 온전히 ③ 오버레이 패널이 260px 아래로
     찌그러지지 않음 ④ 바깥 한 번 클릭으로는 메모가 닫히지 않고, 두 번 클릭이면 메모만 닫힘
     (v4 회귀: 1080px 에서 뷰어에 260px 만 남아 세로 한 줄로 뭉개졌다.
      v5 회귀: 자리가 없으면 메모가 가이드를 덮어 가이드가 안 보였다.
      v6 회귀: 가이드를 열면 캡션·번역·해석이 통째로 사라졌다.)
  8. **1080px, 자산 뷰어 없이 학습 가이드 + 메모** - 겹침 0, 둘 다 화면 안
     (v6 회귀: 본문에 360px 를 남기려다 메모가 가이드를 덮었다.)
  9. **1600px 자산 뷰어** - 세로형 도표는 가로 배치(이미지 | 캡션·번역·해석) 유지,
     메모를 열어도 가로 배치 그대로이고 메모와 겹침 0

전제: `pip install playwright` + `playwright install chromium`. 없으면 skip 으로 빠진다.

사용법:
    python tools/check_memo_layer.py "samples/cares"
    python tools/check_memo_layer.py --all
"""
import re
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("[SKIP] playwright 미설치 - pip install playwright && playwright install chromium")
    raise SystemExit(0)

W, H = 1600, 1000
NARROWS = [(1080, 840), (950, 800)]   # 좁은 화면 회귀 (v4 가 깨지던 폭 · 세 패널이 공존하는 하한 근처)
PW, PH = 1080, 840      # 뷰어 없이 가이드 + 메모 (v6 가 깨지던 폭)
MIN_PANEL = 260         # 오버레이 패널(세로 적층)이 이보다 좁아지면 볼 수 없다
MIN_STACK_IMG = 240     # 세로 적층에서 이미지의 최소 폭 (패널 260 - 여백 20). 원본이 더 작으면 원본 폭
ROW_IMG = 360           # 가로 배치에서 이미지의 최소 폭 (memo_layer_fix.py 의 ROW_IMG 와 같은 값)

VIEW_JS = """() => {
  var v = document.querySelector('.asset-viewer.open');
  if (!v) return null;
  function b(s){
    var e = v.querySelector(s);
    if (!e || getComputedStyle(e).display === 'none') return null;
    var r = e.getBoundingClientRect();
    return {t: r.top, b: r.bottom, l: r.left, r: r.right, w: r.width};
  }
  var im = v.querySelector('.av-img img');
  return {stack: document.body.classList.contains('mlx-av-stack'),
          tall: v.classList.contains('av-tall'),
          nw: im ? im.naturalWidth : 0, nh: im ? im.naturalHeight : 0,
          img: b('.av-img img'), text: b('.av-text'), en: b('.av-en'), kr: b('.av-kr'),
          interp: b('.av-interp'), panel: b('.av-panel')};
}"""


def overlap(a, b):
    if not a or not b:
        return 0.0
    x = max(0, min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"]))
    y = max(0, min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"]))
    return x * y


def run(br, html: Path, verbose=True):
    fails = []

    def ck(name, cond, extra=""):
        if verbose:
            print(("  [ok]   " if cond else "  [FAIL] ") + name + ((" " + extra) if extra else ""))
        if not cond:
            fails.append(name)

    pg = br.new_page(viewport={"width": W, "height": H})
    pg.set_default_timeout(6000)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(html.resolve().as_uri())
    pg.wait_for_timeout(1100)

    fab = pg.locator(".memo-fab")
    if fab.count() == 0:
        pg.close()
        return None  # 메모 미주입 논문

    ck("메모 버튼 표시", fab.is_visible())
    fb = fab.bounding_box()
    ck("우측 상단 배치", bool(fb) and fb["x"] + fb["width"] > W - 120 and fb["y"] < 280,
       f"x={fb['x']:.0f} y={fb['y']:.0f}" if fb else "")
    ck("z-index 2400", pg.evaluate("getComputedStyle(document.querySelector('.memo-fab')).zIndex") == "2400")

    md = pg.locator(".memo-drawer")

    # --- 학습 가이드(자산 해설). 세대에 따라 사이드 드로어(.study-drawer) 또는 모달(.study-modal) ---
    if pg.locator(".study-fab").count():
        try:
            pg.locator(".study-fab").first.click()
        except Exception:
            pg.locator(".study-fab").first.evaluate("el => el.click()")
        pg.wait_for_timeout(800)
        guide = pg.locator(".study-drawer.open, .study-modal.open").first
        opened = guide.count() > 0
        ck("학습 가이드 열림", opened)
        if opened:
            # 화면을 덮는 모달(구세대)이면 컨테이너가 아니라 그 안의 패널과 비교한다 -
            # 전면 백드롭 위에 메모가 뜨는 것은 겹침이 아니라 의도된 동작이다.
            gb = guide.bounding_box()
            if gb and gb["width"] > W * 0.6:
                inner = guide.locator(":scope > *").first
                if inner.count():
                    gb = inner.bounding_box()
            ck("가이드 위에서도 메모 버튼 표시", fab.is_visible())
            ck("메모 버튼 ↔ 가이드 겹침 0", overlap(fab.bounding_box(), gb) == 0)
            fab.click()
            pg.wait_for_timeout(700)
            ck("메모 드로어 열림", "open" in (md.get_attribute("class") or ""))
            still = pg.locator(".study-drawer.open, .study-modal.open").first
            ck("메모를 눌러도 가이드가 닫히지 않음", still.count() > 0)
            if still.count():
                gb2 = still.bounding_box()
                if gb2 and gb2["width"] > W * 0.6:
                    inner = still.locator(":scope > *").first
                    if inner.count():
                        gb2 = inner.bounding_box()
                ck("메모 ↔ 가이드 겹침 0", overlap(md.bounding_box(), gb2) == 0)
            pg.locator(".memo-pad").fill("가이드 옆에서 쓴 메모")
            pg.wait_for_timeout(600)
            ck("타이핑해도 가이드 유지", guide.count() > 0)
            pg.locator(".memo-pad").press("Escape")
            pg.wait_for_timeout(500)
            ck("ESC = 메모만 닫힘", "open" not in (md.get_attribute("class") or "") and guide.count() > 0)
            closer = pg.locator(".study-drawer-close, .study-modal-close").first
            if closer.count():
                closer.click()
                pg.wait_for_timeout(400)
    elif verbose:
        print("  [skip]  이 논문에는 자산 학습 가이드(.study-fab)가 없음")

    # --- 라이트박스 ---
    imgs = pg.locator(".asset-image-wrap img, .diss-overview-figure img, .concept-figure img")
    if pg.locator(".img-lightbox").count() and imgs.count():
        try:
            imgs.first.click()
        except Exception:
            imgs.first.evaluate("el => el.click()")
        pg.wait_for_timeout(700)
        lb = pg.locator(".img-lightbox")
        ck("라이트박스 열림", "open" in (lb.get_attribute("class") or ""))
        ck("라이트박스 위에서도 메모 버튼 표시", fab.is_visible())
        fab.click()
        pg.wait_for_timeout(700)
        ck("메모 클릭이 라이트박스를 닫지 않음", "open" in (lb.get_attribute("class") or ""))
        mb = md.bounding_box()
        ck("메모 ↔ 확대 이미지 겹침 0", overlap(mb, pg.locator(".img-lightbox-stage").bounding_box()) == 0)
        ck("메모가 라이트박스 닫기 버튼을 가리지 않음",
           overlap(mb, pg.locator(".img-lightbox-close").bounding_box()) == 0)
        pg.locator(".memo-pad").fill("확대 이미지 보면서 쓴 메모")
        pg.locator(".memo-pad").press("ArrowLeft")
        pg.locator(".memo-pad").press("ArrowRight")
        pg.wait_for_timeout(400)
        ck("타이핑·화살표가 페이지 단축키로 새지 않음", "open" in (lb.get_attribute("class") or ""))
        pg.locator(".memo-pad").press("Escape")
        pg.wait_for_timeout(400)
        ck("ESC = 메모만 닫힘 (라이트박스 유지)",
           "open" not in (md.get_attribute("class") or "") and "open" in (lb.get_attribute("class") or ""))
    elif verbose:
        print("  [skip]  이 논문에는 라이트박스가 없음")

    ck("JS 오류 0건", len(errs) == 0, "; ".join(errs[:2]))
    pg.close()
    return fails


PANEL_JS = """() => {
  var open = document.querySelector('.img-lightbox.open,.asset-viewer.open,.para-reader.open,.notes-picker.open,.study-modal.open');
  if (!open) return null;
  var p = open.querySelector('.av-panel,.img-lightbox-stage,.pr-panel,.np-panel,.study-modal-card') || open;
  var r = p.getBoundingClientRect();
  return {w: r.width, cls: document.body.className,
          or: getComputedStyle(document.documentElement).getPropertyValue('--overlay-right').trim()};
}"""


def run_pair(br, html: Path, verbose=True):
    """자산 뷰어 없이 학습 가이드 + 메모만 열었을 때 (1080px) - 가이드는 메모에 덮이지 않는다."""
    fails = []

    def ck(name, cond, extra=""):
        if verbose:
            print(("  [ok]   " if cond else "  [FAIL] ") + name + ((" " + extra) if extra else ""))
        if not cond:
            fails.append(name)

    pg = br.new_page(viewport={"width": PW, "height": PH})
    pg.set_default_timeout(6000)
    pg.goto(html.resolve().as_uri())
    pg.wait_for_timeout(1100)
    if pg.locator(".memo-fab").count() == 0 or pg.locator(".study-fab").count() == 0:
        pg.close()
        return fails
    pg.locator(".study-fab").first.evaluate("el => el.click()")
    pg.wait_for_timeout(700)
    guide = pg.locator(".study-drawer.open, .study-modal.open").first
    gb0 = guide.bounding_box() if guide.count() else None
    if not gb0 or gb0["width"] > PW * 0.6:
        if verbose:
            print("  [skip]  사이드 드로어 가이드 없음(풀스크린 모달 세대) - 가이드 + 메모 나란히 서기 대상 아님")
        pg.close()
        return fails
    pg.locator(".memo-fab").evaluate("el => el.click()")
    pg.wait_for_timeout(800)
    md = pg.locator(".memo-drawer").bounding_box()
    gb = guide.bounding_box() if guide.count() else None
    ck(f"{PW}px 가이드+메모(뷰어 없음): 가이드 유지", bool(gb))
    ck(f"{PW}px 가이드+메모(뷰어 없음): 겹침 0", bool(md) and bool(gb) and overlap(md, gb) == 0,
       f"memo x={md['x']:.0f} w={md['width']:.0f} / guide x={gb['x']:.0f} w={gb['width']:.0f}" if md and gb else "")
    ck(f"{PW}px 가이드+메모(뷰어 없음): 둘 다 화면 안",
       bool(md) and bool(gb) and md["x"] >= -1 and gb["x"] + gb["width"] <= PW + 1)
    pg.close()
    return fails


def run_row(br, html: Path, verbose=True):
    """넓은 화면(1600px)에서는 세로형 도표의 자산 뷰어가 가로 배치를 유지한다 (세로 적층 회귀 방지)."""
    fails = []

    def ck(name, cond, extra=""):
        if verbose:
            print(("  [ok]   " if cond else "  [FAIL] ") + name + ((" " + extra) if extra else ""))
        if not cond:
            fails.append(name)

    pg = br.new_page(viewport={"width": W, "height": H})
    pg.set_default_timeout(6000)
    pg.goto(html.resolve().as_uri())
    pg.wait_for_timeout(1100)
    if pg.locator(".memo-fab").count() == 0:
        pg.close()
        return fails
    pg.evaluate("() => { location.hash = '#tab-study'; }")
    pg.wait_for_timeout(500)
    thumbs = pg.locator("[data-thumb-of]")
    info = None
    for i in range(min(thumbs.count(), 12)):
        thumbs.nth(i).evaluate("el => el.click()")
        pg.wait_for_timeout(450)
        v = pg.evaluate(VIEW_JS)
        if v and v["tall"] and v["img"]:
            info = v
            break
        c = pg.locator(".asset-viewer.open .av-close")
        if c.count():
            c.evaluate("el => el.click()")
            pg.wait_for_timeout(150)
    if info is None:
        if verbose:
            print("  [skip]  세로형(av-tall) 도표를 여는 자산 뷰어가 없음 - 가로 배치 검사 생략")
        pg.close()
        return fails

    def row_ok(v):
        return (not v["stack"]) and bool(v["text"]) and bool(v["img"]) and v["text"]["l"] >= v["img"]["r"] - 1

    need = min(ROW_IMG, info["nw"], 0.78 * H * info["nw"] / max(1, info["nh"]))
    ck(f"{W}px 자산 뷰어: 가로 배치(이미지 | 캡션·번역·해석)", row_ok(info),
       f"img_w={info['img']['w']:.0f}")
    ck(f"{W}px 자산 뷰어: 이미지 폭 >= {need:.0f}px", info["img"]["w"] >= need - 2, f"img_w={info['img']['w']:.0f}")
    pg.locator(".memo-fab").evaluate("el => el.click()")
    pg.wait_for_timeout(800)
    v2 = pg.evaluate(VIEW_JS)
    md = pg.locator(".memo-drawer").bounding_box()
    ck(f"{W}px 자산 뷰어 + 메모: 가로 배치 유지", bool(v2) and row_ok(v2),
       f"img_w={v2['img']['w']:.0f}" if v2 and v2["img"] else "")
    ck(f"{W}px 자산 뷰어 + 메모: 겹침 0",
       bool(v2) and bool(md) and bool(v2["panel"]) and v2["panel"]["r"] <= md["x"] + 1)
    pg.close()
    return fails


def run_narrow(br, html: Path, NW=1080, NH=840, verbose=True):
    """좁은 화면에서 자산 뷰어 + 학습 가이드 + 메모를 동시에 열었을 때의 자리 배분."""
    fails = []
    tag = f"{NW}px"

    def ck(name, cond, extra=""):
        name = name.replace("좁은 화면", tag, 1)
        if verbose:
            print(("  [ok]   " if cond else "  [FAIL] ") + name + ((" " + extra) if extra else ""))
        if not cond:
            fails.append(name)

    pg = br.new_page(viewport={"width": NW, "height": NH})
    pg.set_default_timeout(6000)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(html.resolve().as_uri())
    pg.wait_for_timeout(1100)

    if pg.locator(".memo-fab").count() == 0:
        pg.close()
        return None

    # 오버레이를 하나 연다 - Paper Study 탭의 자산 썸네일(자산 뷰어)이 1순위, 없으면 그림 확대
    pg.evaluate("() => { location.hash = '#tab-study'; }")
    pg.wait_for_timeout(500)
    t = pg.locator("[data-thumb-of]").first
    if t.count():
        t.evaluate("el => el.click()")
        pg.wait_for_timeout(600)
    if pg.evaluate(PANEL_JS) is None:
        img = pg.locator(".asset-image-wrap img, .diss-overview-figure img, .concept-figure img").first
        if img.count():
            img.evaluate("el => el.click()")
            pg.wait_for_timeout(600)

    # 학습 가이드도 함께 (뷰어 안 버튼 우선). 자산 뷰어 없이 라이트박스만 열린 경우(study.json 이 없는
    # 논문)에는 가이드를 열지 않는다 - 라이트박스 뒤에 가려진 .study-fab 를 코드로 누르는 것은 UI 로는
    # 만들 수 없는 상태라(라이트박스를 열면 가이드는 닫힌다) 겹침 판정이 거짓 FAIL 이 된다.
    lightbox_only = pg.locator(".asset-viewer.open").count() == 0 and pg.evaluate(PANEL_JS) is not None
    g = pg.locator(".av-guide, .study-fab").first
    if lightbox_only:
        if verbose:
            print("  [skip]  자산 뷰어 없음(study.json 미작성) - 라이트박스 위 가이드 조합은 UI 로 만들 수 없어 생략")
    elif g.count():
        g.evaluate("el => el.click()")
        pg.wait_for_timeout(700)

    guide = pg.locator(".study-drawer.open, .study-modal.open").first
    has_guide = guide.count() > 0
    viewer_open = pg.locator(".asset-viewer.open").count() > 0
    # 화면을 덮는 구세대 모달(모체 papers 3)은 "옆에 나란히"·"세로 적층" 검사 대상이 아니다.
    gb0 = guide.bounding_box() if has_guide else None
    side_guide = bool(gb0) and gb0["width"] <= NW * 0.6
    if has_guide and not side_guide and verbose:
        print("  [skip]  가이드가 풀스크린 모달(구세대) - 나란히 서기·세로 적층 검사 대상 아님")

    pg.locator(".memo-fab").evaluate("el => el.click()")
    pg.wait_for_timeout(800)

    # 자산 뷰어 + 가이드 + 메모 = 세로 적층. 가이드를 열어도 캡션·번역·해석은 감추지 않고 이미지 아래로 내린다.
    if side_guide and viewer_open:
        v = pg.evaluate(VIEW_JS)
        ck("좁은 화면: 자산 뷰어가 세로 적층으로 전환", bool(v) and v["stack"])
        ck("좁은 화면: 캡션·번역이 감춰지지 않음", bool(v) and bool(v["text"]) and bool(v["en"]) and bool(v["kr"]))
        if v and v["img"] and v["en"] and v["kr"]:
            order = v["img"]["b"] <= v["en"]["t"] + 1 and v["en"]["b"] <= v["kr"]["t"] + 1
            if v["interp"]:
                order = order and v["kr"]["b"] <= v["interp"]["t"] + 1
            ck("좁은 화면: 위→아래 = 이미지 → 원문 캡션 → 번역 → 해석", order)
            need = min(MIN_STACK_IMG, v["nw"] or MIN_STACK_IMG)
            ck(f"좁은 화면: 이미지 폭 >= {need}px", v["img"]["w"] >= need - 1, f"img_w={v['img']['w']:.0f}")
            if v["panel"]:
                ck("좁은 화면: 이미지가 패널 안에 온전히",
                   v["img"]["l"] >= v["panel"]["l"] - 1 and v["img"]["r"] <= v["panel"]["r"] + 1)

    md = pg.locator(".memo-drawer").bounding_box()
    ck("좁은 화면: 메모가 화면 안에 온전히", bool(md) and md["x"] >= -1 and md["x"] + md["width"] <= NW + 1,
       f"x={md['x']:.0f} w={md['width']:.0f}" if md else "")

    if side_guide:
        gb = guide.bounding_box()
        ck("좁은 화면: 메모 ↔ 가이드 겹침 0", overlap(md, gb) == 0,
           f"guide x={gb['x']:.0f} w={gb['width']:.0f}" if gb else "")
        ck("좁은 화면: 가이드가 화면 안에 온전히",
           bool(gb) and gb["x"] >= -1 and gb["x"] + gb["width"] <= NW + 1)

    info = pg.evaluate(PANEL_JS)
    if info is None:
        if verbose:
            print("  [skip]  이 논문에는 열 수 있는 전체화면 오버레이가 없음")
    else:
        ck(f"좁은 화면: 오버레이 패널 >= {MIN_PANEL}px", info["w"] >= MIN_PANEL - 1,
           f"w={info['w']:.0f} --overlay-right={info['or']} body='{info['cls']}'")
        try:
            res = float(info["or"].replace("px", "") or 0)
        except ValueError:
            res = 0.0
        ck("좁은 화면: 축소량이 상한을 넘지 않음", NW - res >= MIN_PANEL, f"reserve={res:.0f}")

    # 바깥 두 번 클릭 = 메모가 닫힘. 한 번 클릭으로는 닫히지 않아야 한다.
    # 클릭 지점은 메모(우측) 바깥이 확실한 좌측 가장자리(오버레이의 여백 띠)로 고정한다. 세로 적층 패널은
    # 남는 폭을 다 쓰므로 x=40 은 뷰어 이미지 위가 된다 - 거기서는 클릭마다 라이트박스가 열리고 닫혀
    # 대상 노드가 바뀌므로 브라우저가 더블클릭으로 묶지 않는다(검사 지점의 문제이지 닫기 규약의 문제가 아니다).
    x, y = 8, NH * 0.45
    pg.mouse.click(x, y)
    pg.wait_for_timeout(350)
    ck("좁은 화면: 한 번 클릭으로는 메모가 닫히지 않음",
       "open" in (pg.locator(".memo-drawer").get_attribute("class") or ""))
    # 바깥 클릭이면 가이드를 스스로 닫는 세대(모체 papers 24 계열)가 있다 - 그건 논문 자체 동작이므로
    # 그 경우 "더블클릭이 가이드는 닫지 않음"을 요구하지 않는다.
    guide_survived_single = pg.locator(".study-drawer.open, .study-modal.open").count() > 0
    pg.mouse.dblclick(x, y)
    pg.wait_for_timeout(450)
    closed = "open" not in (pg.locator(".memo-drawer").get_attribute("class") or "")
    ck("좁은 화면: 바깥 더블클릭 = 메모 닫힘", closed)
    if side_guide and guide_survived_single:
        # 사이드 드로어 가이드는 메모를 닫아도 그대로 있어야 한다 (더블클릭이 메모만 겨냥한다).
        ck("좁은 화면: 더블클릭이 가이드는 닫지 않음",
           pg.locator(".study-drawer.open, .study-modal.open").count() > 0)
    elif side_guide and verbose:
        print("  [skip]  이 세대는 바깥 클릭이면 가이드가 스스로 닫힌다 (논문 자체 동작)")

    ck("좁은 화면: JS 오류 0건", len(errs) == 0, "; ".join(errs[:2]))
    pg.close()
    return fails


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage: python tools/check_memo_layer.py "papers/N. name" | --all')
    root = Path(__file__).resolve().parent.parent
    if sys.argv[1] == "--all":
        # papers/* (번호 순) + samples/* - 빈 배포본에서도 정본 samples/cares 를 검사한다
        folders = sorted(
            (p for p in (root / "papers").iterdir() if p.is_dir()),
            key=lambda p: int(re.match(r"(\d+)", p.name).group(1)) if re.match(r"\d+", p.name) else 999,
        ) + sorted(p for p in (root / "samples").iterdir() if p.is_dir())
    else:
        folders = [Path(sys.argv[1])]
    verbose = len(folders) == 1

    total = 0
    with sync_playwright() as p:
        br = p.chromium.launch()
        for d in folders:
            hs = list(d.glob("*_output.html"))
            if not hs:
                continue
            if verbose:
                print(f"=== {d.name}")
            try:
                res = run(br, hs[0], verbose=verbose)
                if res is not None:
                    res = res + run_row(br, hs[0], verbose=verbose)
                    res = res + run_pair(br, hs[0], verbose=verbose)
                    for nw, nh in NARROWS:
                        res = res + (run_narrow(br, hs[0], nw, nh, verbose=verbose) or [])
            except Exception as e:
                total += 1
                print(f"{d.name:24s} :: ERROR {type(e).__name__}: {str(e).splitlines()[0][:90]}")
                continue
            if res is None:
                print(f"[SKIP] {d.name}: 메모 미주입")
                continue
            total += len(res)
            if not verbose:
                mark = "ok" if not res else "FAIL " + " / ".join(res)
                print(f"{d.name:24s} :: {mark}")
        br.close()

    print()
    if total:
        raise SystemExit(f"{total}건 실패")
    print("[ok] 메모 레이어 회귀 검사 통과")


if __name__ == "__main__":
    main()
