"""
detect_assets.py — figure/table 캡션 좌표 + 이미지/벡터 영역 자동 검출.

크롭 좌표를 손으로 추측하지 말 것. 먼저 이 도구를 돌려 각 캡션의 실제 PDF
point 좌표(멀티라인 캡션은 블록 전체)와 이미지/드로잉 bbox를 뽑은 뒤, 그
근거로 _crop.py의 rect를 캡션 anchor 기반으로 잡는다. (rules/parsing_rules.md §4-A)

사용:
    python tools/detect_assets.py "rawpaper/Some Paper.pdf"
    python tools/detect_assets.py "rawpaper/Some Paper.pdf" --pages 3,4,8

출력(페이지별):
    CAP Figure 2  block_y=[438.8, 472.1]  x=[306,504]  lines=3  | Figure 2: ...
    images(n=...): [(x0,y0,x1,y1), ...]
    drawings_bbox: (x0,y0,x1,y1)

규약 요약:
  - Figure: 캡션 아래(BELOW). crop y_top = 이미지 top(>=60pt, header 제외),
            y_bot = 캡션 block_y[1] + 4~8pt.  ← block 끝(마지막 줄)이지 첫 줄이 아님!
  - Table : 캡션 위(ABOVE). crop y_top = block_y[0] - 3pt,
            y_bot = 표 데이터 마지막 행 + 4pt.
  - column x: full(≈48..564) / left(≈48..302) / right(≈304..564). 캡션 x중심·이미지 x로 판별.
  - 생성 후 PNG를 반드시 눈으로 검증, 4~8pt 단위로 미세 조정.
"""
import re
import sys
import fitz

CAP = re.compile(r"^(Figure|Table)\s+(\d+)\s*[:.]", re.I)


def detect(pdf_path, only_pages=None):
    doc = fitz.open(pdf_path)
    print(f"pages={len(doc)}  page_size={doc[0].rect}")
    for pno in range(len(doc)):
        if only_pages and (pno + 1) not in only_pages:
            continue
        page = doc[pno]
        d = page.get_text("dict")
        caps = []
        for blk in d.get("blocks", []):
            lines = blk.get("lines", [])
            for i, line in enumerate(lines):
                txt = "".join(s["text"] for s in line.get("spans", [])).strip()
                if not CAP.match(txt):
                    continue
                # 멀티라인 캡션: 같은 블록의 나머지 줄을 캡션 끝으로 본다
                y0 = line["bbox"][1]
                y1 = line["bbox"][3]
                x0 = line["bbox"][0]
                x1 = line["bbox"][2]
                nlines = 1
                for nxt in lines[i + 1:]:
                    ny0, ny1 = nxt["bbox"][1], nxt["bbox"][3]
                    if ny0 - y1 <= 7:  # 줄 간격 <=7pt면 같은 캡션
                        y1 = ny1
                        x1 = max(x1, nxt["bbox"][2])
                        nlines += 1
                    else:
                        break
                caps.append((txt[:2], txt, round(y0, 1), round(y1, 1),
                             round(x0), round(x1), nlines))
        if not caps:
            continue
        imgs = []
        for info in page.get_images(full=True):
            try:
                for r in page.get_image_rects(info[0]):
                    imgs.append((round(r.x0), round(r.y0), round(r.x1), round(r.y1)))
            except Exception:
                pass
        dr = page.get_drawings()
        if dr:
            xs = [p for g in dr for p in (g["rect"].x0, g["rect"].x1)]
            ys = [p for g in dr for p in (g["rect"].y0, g["rect"].y1)]
            draw_bbox = (round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys)))
        else:
            draw_bbox = None
        print(f"\n--- page {pno + 1} ---")
        for _, txt, by0, by1, x0, x1, n in caps:
            kind = "Figure" if txt.lower().startswith("f") else "Table"
            print(f"  CAP {kind:6} block_y=[{by0}, {by1}]  x=[{x0},{x1}]  lines={n}  | {txt[:52]}")
        print(f"  images(n={len(imgs)}): {imgs[:8]}")
        print(f"  drawings_bbox: {draw_bbox}  (n_paths={len(dr)})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sys.stdout.reconfigure(encoding="utf-8")
    pages = None
    if "--pages" in sys.argv:
        idx = sys.argv.index("--pages")
        pages = {int(x) for x in sys.argv[idx + 1].split(",")}
    detect(sys.argv[1], pages)
