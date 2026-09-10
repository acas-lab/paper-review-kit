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
  7. **좁은 화면(1080px)** - 자산 뷰어 + 학습 가이드 + 메모를 동시에 열었을 때
     ① 가이드를 열면 캡션·번역이 감춰져 이미지 전용이 되고 ② 메모 ↔ 가이드 겹침 0,
     둘 다 화면 안에 온전히 ③ 오버레이 패널이 260px 아래로 찌그러지지 않음
     ④ 바깥 한 번 클릭으로는 메모가 닫히지 않고, 두 번 클릭이면 메모만 닫힘
     (v4 회귀: 1080px 에서 뷰어에 260px 만 남아 세로 한 줄로 뭉개졌다.
      v5 회귀: 자리가 없으면 메모가 가이드를 덮어 가이드가 안 보였다.)

전제: `pip install playwright` + `playwright install chromium`. 없으면 skip 으로 빠진다.

사용법:
    python tools/check_memo_layer.py "papers/33. visor"
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
NW, NH = 1080, 840      # 좁은 화면 회귀 (v4 가 깨지던 폭)
MIN_PANEL = 260         # 오버레이 패널(이미지 전용 모드)이 이보다 좁아지면 볼 수 없다


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


def run_narrow(br, html: Path, verbose=True):
    """좁은 화면에서 자산 뷰어 + 학습 가이드 + 메모를 동시에 열었을 때의 자리 배분."""
    fails = []

    def ck(name, cond, extra=""):
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

    # 학습 가이드도 함께 (뷰어 안 버튼 우선)
    g = pg.locator(".av-guide, .study-fab").first
    if g.count():
        g.evaluate("el => el.click()")
        pg.wait_for_timeout(700)

    guide = pg.locator(".study-drawer.open, .study-modal.open").first
    has_guide = guide.count() > 0
    viewer_open = pg.locator(".asset-viewer.open").count() > 0
    # 화면을 덮는 구세대 모달(papers 3)은 "옆에 나란히"·"이미지 전용" 대상이 아니다.
    gb0 = guide.bounding_box() if has_guide else None
    side_guide = bool(gb0) and gb0["width"] <= NW * 0.6
    if has_guide and not side_guide and verbose:
        print("  [skip]  가이드가 풀스크린 모달(구세대) - 나란히 서기·이미지 전용 대상 아님")

    # 가이드 + 자산 뷰어 = 이미지 전용 모드. 원문 캡션·번역은 가이드가 대신하므로 감춘다.
    if side_guide and viewer_open:
        hidden = pg.evaluate(
            "() => { var t = document.querySelector('.asset-viewer .av-text');"
            " return t ? getComputedStyle(t).display === 'none' : null; }")
        img_before = pg.evaluate(
            "() => { var i = document.querySelector('.asset-viewer.open .av-img img');"
            " return i ? i.getBoundingClientRect().width : 0; }")
        ck("좁은 화면: 가이드를 열면 캡션·번역이 감춰짐(이미지 전용)", hidden is True, f"img_w={img_before:.0f}")

    pg.locator(".memo-fab").evaluate("el => el.click()")
    pg.wait_for_timeout(800)

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
        ck(f"좁은 화면: 오버레이 패널 >= {MIN_PANEL}px", info["w"] >= MIN_PANEL,
           f"w={info['w']:.0f} --overlay-right={info['or']} body='{info['cls']}'")
        try:
            res = float(info["or"].replace("px", "") or 0)
        except ValueError:
            res = 0.0
        ck("좁은 화면: 축소량이 상한을 넘지 않음", NW - res >= MIN_PANEL, f"reserve={res:.0f}")

    # 바깥 두 번 클릭 = 메모가 닫힘. 한 번 클릭으로는 닫히지 않아야 한다.
    # 클릭 지점은 메모(우측) 바깥이 확실한 좌측 상단부로 고정한다.
    x, y = 40, NH * 0.45
    pg.mouse.click(x, y)
    pg.wait_for_timeout(350)
    ck("좁은 화면: 한 번 클릭으로는 메모가 닫히지 않음",
       "open" in (pg.locator(".memo-drawer").get_attribute("class") or ""))
    # 바깥 클릭이면 가이드를 스스로 닫는 세대(papers 24 계열)가 있다 - 그건 논문 자체 동작이므로
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
        folders = sorted(
            (p for p in (root / "papers").iterdir() if p.is_dir()),
            key=lambda p: int(re.match(r"(\d+)", p.name).group(1)) if re.match(r"\d+", p.name) else 999,
        )
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
                    res = res + (run_narrow(br, hs[0], verbose=verbose) or [])
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
