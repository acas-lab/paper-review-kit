# -*- coding: utf-8 -*-
"""overview_inject.py - 구세대 산출물의 summary 카드를 9행 + 한 장 overview 이미지로 교체.

배경: summary 카드 9행 + dissection_overview.png 규칙(2026-05-12) 이전에 만든 산출물은
카드가 4행이거나 카드 자체가 없다(모체 papers 1~15 소급에 쓰인 도구 — 모체 사례, 배포본 미포함).
배포본에서는 빌더 없이 만든 산출물이나 이미지 분기가 없는 구세대 빌더 산출물에 쓴다.
templates/paper_base · samples/cares 빌더는 summary 9행 + overview 를 스스로 렌더하므로 필요 없다.
이 도구는 산출물 HTML 을 직접 고친다. 빌더 유무와 무관하게 같은 경로로 처리한다.
⚠ 빌더에 이미지 분기가 없는 논문은 재빌드하면 카드가 덮어써진다 → 재빌드 후 이 도구를 다시 돌린다.

입력 (논문 폴더 기준)
  tabs_data/dissection.json        cards[] 중 cls == "diss-summary" 카드. rows 는 정확히 9개.
                                   body 는 HTML 필드(raw 삽입), **x** 는 <b>x</b> 로 변환.
  assets/generated/dissection_overview.png

처리
  1. #tab-dissection 의 summary <article> 을 교체한다. 없으면 마지막 카드 뒤에 새로 넣는다.
     마크업 방언(dl/dt/dd 대 div/span/p 대 diss-row-tag), 단계 번호 형식(07 대 7), 카드 id 유무는
     같은 탭의 기존 카드에서 읽어 맞춘다.
  2. CSS·라이트박스 JS 를 헤더 id 로 식별해 제거 후 재주입한다(idempotent · 업데이터).
     구세대 HTML 은 공용 라이트박스가 없거나 세대마다 달라 자립형으로 싣는다.
     클래스에 img-lightbox 를 포함해 memo_layer_fix 의 자리 배분 대상이 되게 한다.
  3. tab-intro 의 "4행 요약" 문구를 갱신한다.

사용법: python tools/overview_inject.py "papers/N. shortname"   (additive · idempotent · 업데이터)
정본 규약: rules/component_rules.md §14, prompts/04_research_analysis.md § 8번 카드
"""
import base64
import json
import os
import re
import sys
from pathlib import Path

try:  # Windows cp949 콘솔에서도 한글 출력이 깨지지 않도록
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

CSS_ID = "overview-inject-css"
JS_ID = "overview-inject-js"

CSS = """<style id="%s">
.diss-card.diss-summary{grid-column:1/-1;background:linear-gradient(180deg,#ffffff,#f3f4f9)}
.diss-card.diss-summary .diss-step{background:#e6e8f2;color:#494e6e}
.diss-card.diss-summary .diss-tag,.diss-card.diss-summary .diss-row-tag{background:#494e6e;color:#fff}
.diss-overview-figure{margin:18px 0 22px;padding:14px;background:#ffffff;border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow)}
.diss-overview-figure img{display:block;width:100%%;height:auto;border-radius:10px;cursor:zoom-in}
.diss-overview-figure figcaption{margin-top:10px;font-size:13.5px;color:var(--muted);line-height:1.55;font-style:italic}
.ovx-lb{position:fixed;inset:0;z-index:2000;display:none;align-items:center;justify-content:center;background:rgba(20,22,30,.86);overflow:hidden}
.ovx-lb.open{display:flex}
.ovx-lb img{max-width:96vw;max-height:calc(100vh - 80px);object-fit:contain;border-radius:8px;background:#fff;cursor:grab;user-select:none;transform-origin:center center}
.ovx-lb img.drag{cursor:grabbing}
.ovx-lb-x{position:absolute;top:14px;right:18px;width:38px;height:38px;border:0;border-radius:50%%;background:rgba(255,255,255,.16);color:#fff;font-size:22px;line-height:1;cursor:pointer}
@media print{.ovx-lb{display:none!important}}
</style>
""" % CSS_ID

JS = """<script id="%s">
(function(){
  var lb,im,s=1,x=0,y=0,drag=null;
  function apply(){im.style.transform='translate('+x+'px,'+y+'px) scale('+s+')';}
  function reset(){s=1;x=0;y=0;apply();}
  function close(){lb.classList.remove('open');}
  function build(){
    lb=document.createElement('div');lb.className='ovx-lb img-lightbox';
    lb.innerHTML='<button type="button" class="ovx-lb-x" aria-label="닫기">&times;</button><img alt="">';
    document.body.appendChild(lb);im=lb.querySelector('img');
    lb.querySelector('.ovx-lb-x').addEventListener('click',close);
    lb.addEventListener('click',function(e){if(e.target===lb)close();});
    lb.addEventListener('wheel',function(e){e.preventDefault();s=Math.min(8,Math.max(.5,s*(e.deltaY<0?1.15:1/1.15)));apply();},{passive:false});
    im.addEventListener('dblclick',function(){if(s>1){reset();}else{s=2.5;apply();}});
    im.addEventListener('mousedown',function(e){e.preventDefault();drag={px:e.clientX,py:e.clientY,x:x,y:y};im.classList.add('drag');});
    window.addEventListener('mousemove',function(e){if(!drag)return;x=drag.x+e.clientX-drag.px;y=drag.y+e.clientY-drag.py;apply();});
    window.addEventListener('mouseup',function(){drag=null;im.classList.remove('drag');});
    /* 메모 안 ESC 는 메모만 닫는다. 닫힌 뒤 포커스가 드로어에 남으면 다음 ESC 까지 메모 입력으로 오인되므로 비운다. */
    var md=document.querySelector('.memo-drawer');
    if(md)new MutationObserver(function(){
      if(md.classList.contains('open'))return;
      var a=document.activeElement;
      if(a&&md.contains(a))setTimeout(function(){a.blur();},0);
    }).observe(md,{attributes:true,attributeFilter:['class']});
    window.addEventListener('keydown',function(e){
      if(!lb.classList.contains('open'))return;
      if(e.target&&e.target.closest&&e.target.closest('.memo-drawer'))return;
      var k=e.key,hit=true;
      if(k==='Escape')close();
      else if(k==='+'||k==='=')s=Math.min(8,s*1.15);
      else if(k==='-')s=Math.max(.5,s/1.15);
      else if(k==='0'){s=1;x=0;y=0;}
      else hit=false;
      if(hit){apply();e.stopImmediatePropagation();e.preventDefault();}
    },true);
  }
  document.addEventListener('click',function(e){
    var t=e.target;
    if(!t||!t.matches||!t.matches('.diss-overview-figure img, img.ovx-zoom'))return;
    e.preventDefault();e.stopImmediatePropagation();
    if(!lb)build();
    im.src=t.src;im.alt=t.alt||'';reset();lb.classList.add('open');
  },true);
})();
</script>
""" % JS_ID

CAPTION = ("PROBLEM &rarr; OBSERVATION &rarr; METHOD &rarr; NOVELTY &rarr; RESULTS - "
           "5단 가로 흐름으로 본 %s. 아래 9행과 같은 내용의 시각 요약.")


def fail(msg):
    sys.exit("[overview_inject] FAIL: " + msg)


def load_card(paper):
    p = paper / "tabs_data" / "dissection.json"
    if not p.exists():
        fail("%s 없음" % p)
    data = json.loads(p.read_text(encoding="utf-8"))
    cards = data["cards"] if isinstance(data, dict) else data
    hits = [c for c in cards if c.get("cls") == "diss-summary"]
    if len(hits) != 1:
        fail("diss-summary 카드 수 = %d" % len(hits))
    card = hits[0]
    rows = card.get("rows") or []
    if len(rows) != 9:
        fail("summary rows = %d (9 필요)" % len(rows))
    if not card.get("title") or not card.get("lead"):
        fail("title/lead 없음")
    return card


def body_html(s):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s, flags=re.S)


def tab_span(html):
    i = html.find('id="tab-dissection"')
    if i < 0:
        fail("#tab-dissection 없음")
    m = re.compile(r'<section\b[^>]*id="tab-(?!dissection)').search(html, i)
    return i, (m.start() if m else len(html))


def render(card, seg, png_b64, short):
    """같은 탭의 기존 카드에서 마크업 방언을 읽어 summary 카드를 만든다."""
    row_tag = 'class="diss-row-tag"' in seg   # 1세대 수작업 방언(모체 papers 1~2): div.diss-body > div.diss-row > span.diss-row-tag + p
    dl = '<dl class="diss-rows"' in seg
    steps = re.findall(r'class="diss-step">([^<]+)<', seg)
    pad = bool(steps) and steps[0].strip().startswith("0")
    span_step = '<span class="diss-step"' in seg
    with_id = re.search(r'<article class="diss-card diss-motivation" id="', seg) is not None

    step = "08" if pad else "8"
    step_html = ('<span class="diss-step">%s</span>' if span_step else '<div class="diss-step">%s</div>') % step
    rows = []
    for r in card["rows"]:
        tag = r.get("tag") or r.get("label")
        if not tag or not r.get("body"):
            fail("row 에 tag/body 없음")
        body = body_html(r["body"])
        if row_tag:
            rows.append('<div class="diss-row"><span class="diss-row-tag">%s</span><p>%s</p></div>' % (tag, body))
        elif dl:
            rows.append('<div class="diss-row"><dt class="diss-tag">%s</dt><dd class="diss-body">%s</dd></div>' % (tag, body))
        else:
            rows.append('<div class="diss-row"><span class="diss-tag">%s</span><p class="diss-body">%s</p></div>' % (tag, body))
    if row_tag:
        wrap = '<div class="diss-body">%s</div>' % "".join(rows)
    else:
        wrap = ('<dl class="diss-rows">%s</dl>' if dl else '<div class="diss-rows">%s</div>') % "".join(rows)
    fig = ('<figure class="diss-overview-figure"><img src="data:image/png;base64,%s" alt="%s 한 장 정리" />'
           '<figcaption>%s</figcaption></figure>') % (png_b64, short, CAPTION % short)
    return ('<article class="diss-card diss-summary"%s>%s'
            '<div class="diss-head"><h3>%s</h3><p class="diss-lead">%s</p></div>%s%s</article>') % (
        ' id="diss-summary"' if with_id else "", step_html, card["title"], card["lead"], fig, wrap)


def inject_block(html, block, tag, bid, anchor):
    html = re.sub(r'<%s id="%s">.*?</%s>\s*' % (tag, bid, tag), "", html, flags=re.S)
    k = html.rfind(anchor)
    if k < 0:
        fail("%s 없음" % anchor)
    return html[:k] + block + html[k:]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    paper = Path(sys.argv[1])
    outs = sorted(paper.glob("*_output.html"))
    if len(outs) != 1:
        fail("산출물 HTML 수 = %d" % len(outs))
    out = outs[0]
    png = paper / "assets" / "generated" / "dissection_overview.png"
    if not png.exists():
        fail("%s 없음" % png)
    card = load_card(paper)
    short = out.name[: -len("_output.html")]
    png_b64 = base64.b64encode(png.read_bytes()).decode("ascii")

    with open(out, encoding="utf-8", newline="") as f:
        html = f.read()
    a, b = tab_span(html)
    seg = html[a:b]
    new = render(card, seg, png_b64, short)

    m = re.search(r'<article class="diss-card diss-summary"', seg)
    if m:
        s = a + m.start()
        e = html.find("</article>", s) + len("</article>")
        html = html[:s] + new + html[e:]
        action = "교체"
    else:
        e = seg.rfind("</article>")
        if e < 0:
            fail("탭 안에 카드 없음")
        e = a + e + len("</article>")
        html = html[:e] + new + html[e:]
        action = "신규"

    html = html.replace("마지막 카드는 4행 요약.", "마지막 카드는 한 장 정리 이미지와 9행 요약.")
    html = inject_block(html, CSS, "style", CSS_ID, "</head>")
    html = inject_block(html, JS, "script", JS_ID, "</body>")

    tmp = out.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(html)
    os.replace(tmp, out)
    print("[overview_inject] ok %s - summary %s, %d행, png %dKB, html %dKB" % (
        paper.name, action, len(card["rows"]), png.stat().st_size // 1024, out.stat().st_size // 1024))


if __name__ == "__main__":
    main()
