# -*- coding: utf-8 -*-
"""플로팅 리더(.para-reader) 안에서 도표로 가는 진입 경로를 만든다.

문제: readerRender()가 단락을 복제하면서 `.asset-stack`을 통째로 제거하므로,
리더 안에는 그림·표가 존재하지 않는다. 리더는 좁은 패널이고 base64 이미지가
크므로 제거 판단 자체는 유지하되, 그 자리에 클릭 가능한 칩을 남긴다.
칩 클릭 = 리더 닫기 + 기존 점프 함수(jumpToRef / jumpTo) 재사용 -> Translation 탭.

적용 대상 (모체·킷 공통, 파일 내용으로 세대를 판별한다):
  - papers/*/_build.py, samples/*/_build.py      : readerRender + readerClose + jumpToRef
  - papers/*/*_output.html, samples/*/*_output.html
  - tools/study_runtime.py                        : renderReader + jumpTo (papers 1~3 자립형 런타임)

성질: additive · idempotent · 업데이터(구버전 블록을 제거한 뒤 재주입).

사용법:
  python tools/reader_asset_chip.py --all
  python tools/reader_asset_chip.py "papers/20. sparse_vlm"
  python tools/reader_asset_chip.py "samples/cares"
  python tools/reader_asset_chip.py --check            # 주입 여부만 보고(무수정)
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

VERSION = "v1"
BEGIN = "/* ==== PR_ASSET_CHIPS_BEGIN %s (tools/reader_asset_chip.py) ==== */" % VERSION
BEGIN_RE = re.compile(r"[ \t]*/\* ==== PR_ASSET_CHIPS_BEGIN .*?PR_ASSET_CHIPS_END ==== \*/\n", re.S)

# ---------------------------------------------------------------- 주입 JS
# __CLOSE__ / __JUMP__ 는 세대별 함수명으로 치환된다.
JS_BODY = r"""/* 리더는 .asset-stack 을 화면에 싣지 않는다(좁은 패널 + base64 이미지).
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
  __CLOSE__;
  __JUMP__;
}, true);"""


def _block(close_stmt, jump_stmt, indent):
    body = JS_BODY.replace("__CLOSE__", close_stmt).replace("__JUMP__", jump_stmt)
    lines = [BEGIN] + body.split("\n") + ["/* ==== PR_ASSET_CHIPS_END ==== */"]
    return "".join((indent + ln).rstrip() + "\n" for ln in lines)


# ------------------------------------------------- 세대 A: papers 4~35 (빌더/산출물)
A_ANCHOR = "    function readerRender(){\n"
A_OLD = "      clone.querySelectorAll('.asset-stack, .pid-tag').forEach(function(n){ n.remove(); });"
A_NEW = ("      clone.querySelectorAll('.pid-tag').forEach(function(n){ n.remove(); });\n"
         "      prAssetChipify(clone);")

# ------------------------------------------------- 세대 B: tools/study_runtime.py (papers 1~3)
B_ANCHOR = "  function renderReader(){\n"
B_OLD = ("      var clone = block.cloneNode(true);\n"
         "      clone.removeAttribute('id');\n"
         "      prBody.appendChild(clone);")
B_NEW = ("      var clone = block.cloneNode(true);\n"
         "      clone.removeAttribute('id');\n"
         "      clone.querySelectorAll('.pid-tag').forEach(function(n){ n.remove(); });\n"
         "      prAssetChipify(clone);\n"
         "      clone.querySelectorAll('[id]').forEach(function(n){ n.removeAttribute('id'); });\n"
         "      prBody.appendChild(clone);")


def _revert(text):
    """이전 회차 주입을 되돌려 원본 형태로 만든다(업데이터 · 멱등성의 기반)."""
    text = BEGIN_RE.sub("", text)
    # B_NEW 안에 A_NEW 가 부분 문자열로 들어 있다. B 를 먼저 되돌려야 A 치환이 B 를 깨지 않는다.
    text = text.replace(B_NEW, B_OLD)
    text = text.replace(A_NEW, A_OLD)
    return text


def patch(text):
    """(new_text, generation) - 대상이 아니면 (text, None)."""
    base = _revert(text)
    if A_OLD in base and A_ANCHOR in base:
        out = base.replace(A_OLD, A_NEW, 1)
        blk = _block("readerClose()", "jumpToRef(aid)", "    ")
        out = out.replace(A_ANCHOR, blk + A_ANCHOR, 1)
        return out, "A"
    if B_OLD in base and B_ANCHOR in base:
        out = base.replace(B_OLD, B_NEW, 1)
        blk = _block("reader.classList.remove('open')", "jumpTo(aid)", "  ")
        out = out.replace(B_ANCHOR, blk + B_ANCHOR, 1)
        return out, "B"
    return text, None


# ---------------------------------------------------------------- 대상 수집
def targets(argv):
    """인자가 없거나 --all 이면 저장소 전체. 폴더 인자면 그 폴더 안의 _build.py + *_output.html."""
    out = []
    folders = [a for a in argv if not a.startswith("--")]
    if folders:
        for f in folders:
            d = Path(f)
            if not d.is_absolute():
                d = REPO / f
            if d.is_file():
                out.append(d)
                continue
            out += sorted(d.glob("_build.py")) + sorted(d.glob("*_output.html"))
    else:
        for root in ("papers", "samples"):
            base = REPO / root
            if not base.is_dir():
                continue
            for d in sorted(base.iterdir()):
                if not d.is_dir():
                    continue
                out += sorted(d.glob("_build.py")) + sorted(d.glob("*_output.html"))
        rt = REPO / "tools" / "study_runtime.py"
        if rt.exists():
            out.append(rt)
    return out


def main():
    argv = sys.argv[1:]
    check_only = "--check" in argv
    files = targets(argv)
    done, skipped, already = [], [], []
    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            skipped.append((p, "read: %s" % exc))
            continue
        new, gen = patch(text)
        rel = p.relative_to(REPO).as_posix() if str(p).startswith(str(REPO)) else str(p)
        if gen is None:
            skipped.append((rel, "리더 없음"))
            continue
        if new == text:
            already.append((rel, gen))
            continue
        if not check_only:
            p.write_text(new, encoding="utf-8")
        done.append((rel, gen, "이미 최신" if BEGIN in text else "주입"))
    for rel, gen, how in done:
        print("  [%s] %s  (%s)" % (gen, rel, how))
    for rel, gen in already:
        print("  [%s] %s  (변화 없음)" % (gen, rel))
    for rel, why in skipped:
        print("  [-] %s  (%s)" % (rel, why))
    print("=== %s: %d 갱신 / %d 변화없음 / %d 제외 ===" %
          ("check" if check_only else "reader_asset_chip", len(done), len(already), len(skipped)))


if __name__ == "__main__":
    main()
