# -*- coding: utf-8 -*-
"""영상 팔레트: 밝은 테마(기본, 2026-11-19~)와 어두운 테마로 만든 옛 클립·장면을 밝게 바꾸는 변환기.

python tools/video/theme.py "papers/N. name"          video/clips/*.html, video/scenes.js를 밝은 팔레트로 바꾼다(제자리, 백업 work/theme_backup/)
python tools/video/theme.py "papers/N. name" --dry    바꿀 색만 센다

새 논문은 처음부터 LIGHT 팔레트로 쓴다(motion.DEFAULT_STYLE, templates/paper_base/video/scenes.js). 이 변환은 어두운 팔레트로 만든
어두운 팔레트로 만든 옛 영상(모체 사례)을 다시 렌더할 때만 쓴다. 바꾼 뒤 beats·stills로 직접 보고 어긋난 곳은 손으로 고친다.
"""
import colorsys, re, shutil, sys
from pathlib import Path

# 밝은 팔레트(학습 HTML v4와 같은 계열): 이름 → 색
LIGHT = {"canvas": "#F3F2F7", "card": "#FFFFFF", "surface": "#ECEBF3", "surface2": "#E3E1EC", "line": "#CFCCDC", "line2": "#B4B1C4",
         "ink": "#1F2333", "ink2": "#464B5E", "dim": "#5D6275", "faint": "#7A7F93",
         "amber": "#B5701A", "rose": "#B0506A", "blue": "#3F67A8", "mint": "#2F8A63"}

# 어두운 팔레트(옛 영상) → 밝은 팔레트. 표에 없는 색은 _auto가 명도를 뒤집는다
MAP = {"#10131A": "canvas", "#0B0D12": "#E9E8F0", "#0C0E13": "canvas", "#121419": "canvas", "#171B27": "#F7F6FA", "#1A1D24": "#F7F6FA",
       "#1B2030": "card", "#1D2532": "card", "#242A3B": "surface", "#2A3146": "surface2", "#2C3348": "surface2", "#2E354A": "surface2",
       "#2A2E38": "surface2", "#2B2F38": "surface2", "#36415F": "line2", "#3A425A": "line", "#3A4157": "line", "#4A5168": "line2", "#4A5270": "line2",
       "#59607A": "#9A9DB0", "#5A6178": "#9A9DB0", "#5B6170": "#8E92A4", "#5D6475": "faint", "#6F768A": "faint", "#7C8293": "dim", "#8A90A2": "dim",
       "#959BAB": "dim", "#AEB4C6": "ink2", "#B3B8C4": "ink2", "#C9CDE0": "dim", "#E6E7EE": "ink", "#E6E8EE": "ink", "#E9EBF2": "ink",
       "#F4F5F8": "#11141F", "#F7F7F9": "#11141F",
       "#E6B450": "amber", "#A8781C": "#8A5410", "#C98F9F": "rose", "#D29AAA": "#9C3F58", "#A76D7D": "#8E3A51", "#7F9CC4": "blue",
       "#9DB4D3": "#34578F", "#5F7898": "#2F4F80", "#86C3A8": "mint",
       "#2E2228": "#F6E9ED", "#2D2717": "#F7EEDD", "#FBF3E3": "#7A4A0E", "#F7ECEF": "#7E2F45", "#EBF0F6": "#25406B"}

RGBA = [((255, 255, 255), (31, 35, 51), 1), ((233, 235, 242), (31, 35, 51), 1), ((201, 205, 224), (93, 98, 117), 1),
        ((0, 0, 0), (30, 32, 60), .3),                       # 그림자·비네트: 밝은 바탕에서는 옅게
        ((12, 14, 19), (243, 242, 247), 1), ((16, 19, 26), (243, 242, 247), 1), ((27, 32, 48), (255, 255, 255), 1),
        ((230, 180, 80), (181, 112, 26), 1), ((201, 143, 159), (176, 80, 106), 1), ((127, 156, 196), (63, 103, 168), 1),
        ((134, 195, 168), (47, 138, 99), 1)]                 # (240,196,90) 형광펜은 multiply라 그대로 둔다


def _hex(c): c = c.upper(); return "#" + "".join(ch * 2 for ch in c[1:]) if len(c) == 4 else c


def _auto(c):
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)); h, l, s = colorsys.rgb_to_hls(r, g, b)
    if s > .3 and l > .4: l2 = l * .62                     # 강조색: 진하게
    elif l < .3: l2 = .93 - l * .3                         # 어두운 면: 밝은 면
    else: l2 = 1 - l                                       # 회색 글자·선: 명도 뒤집기
    r, g, b = colorsys.hls_to_rgb(h, l2, min(s, .6)); return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def convert(text):
    n = [0]

    def hx(m):
        c = _hex(m.group(0))
        if c in ("#FFFFFF", "#000000"): return m.group(0)      # 순백·순흑(커서, 논문 그림 바탕)은 그대로
        v = MAP.get(c); v = LIGHT.get(v, v) if v else _auto(c); n[0] += 1; return v

    def rg(m):
        rgb = tuple(int(x) for x in m.group(1, 2, 3)); a = float(m.group(4))
        for src, dst, k in RGBA:
            if rgb == src: n[0] += 1; return f"rgba({dst[0]},{dst[1]},{dst[2]},{round(a * k, 3)})"
        return m.group(0)
    def rgt(m):                                             # 알파가 템플릿 식인 rgba(r,g,b,${…})
        rgb = tuple(int(x) for x in m.group(1, 2, 3)); e = m.group(4)
        for src, dst, k in RGBA:
            if rgb == src:
                n[0] += 1; return f"rgba({dst[0]},{dst[1]},{dst[2]},${{{e}}})" if k == 1 else f"rgba({dst[0]},{dst[1]},{dst[2]},${{({e})*{k}}})"
        return m.group(0)
    text = re.sub(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*\$\{([^}]*)\}\s*\)", rgt, text)
    text = re.sub(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b(?![0-9A-Fa-f])", hx, text)
    text = re.sub(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)", rg, text)
    return text, n[0]


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from common import Paper
    P = Paper(sys.argv[1]); dry = "--dry" in sys.argv
    files = sorted((P.video / "clips").glob("*.html")) + [P.video / "scenes.js"]
    bk = P.work / "theme_backup"; bk.mkdir(exist_ok=True)
    for f in files:                                       # 두 번 돌리면 밝은 색이 다시 뒤집히므로 백업(원본)이 있으면 백업에서 변환한다
        if not f.exists(): continue
        src = bk / f.name if (bk / f.name).exists() else f
        t, k = convert(src.read_text(encoding="utf-8"))
        print(f"{f.name}: {k}색")
        if not dry and k:
            if src == f: shutil.copy(f, bk / f.name)
            f.write_text(t, encoding="utf-8")
    print("백업:", bk) if not dry else None
