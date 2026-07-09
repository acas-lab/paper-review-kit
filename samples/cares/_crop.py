# -*- coding: utf-8 -*-
"""CARES (ACL 2026 camera-ready, arXiv v3 2026-05-31) asset cropper — 캡션 anchor.

Page: A4 595x842pt, ACL 2단. 좌 71–291 / 우 306–526 / full 71–526.
이 논문은 figure·table 모두 캡션이 float **아래**에 붙는다.
  → y_bot = 캡션 bbox bottom + 4pt (자동 검출), y_top = 자산별 수동 지정.
220dpi 렌더 → assets/fig_N.png / table_N.png.

v1(arXiv 2025-10) 크롭 계획을 camera-ready 페이지/번호 체계로 재작성 (2026-07-02):
fig_1(토큰 지배율)·fig_5(cross-teacher confusion)가 신규, 구 fig_1→fig_2 등 번호 밀림.
"""
import re
import sys
from pathlib import Path

import fitz

HERE = Path(__file__).parent
PDF = HERE.parent.parent / "rawpaper" / "CARES Context-Aware Resolution Selector for VLMs.pdf"
OUT = HERE / "assets"
DPI = 220

# 컬럼 x 밴드 (여백 포함)
L = (64, 298)    # 좌측 컬럼
R = (299, 532)   # 우측 컬럼
F = (64, 532)    # full-width

# (asset, page(1-base), (x0,x1), y_top, caption regex)
PLAN = [
    ("fig_1",   1, R, 178, r"^Figure 1:"),   # visual token dominance (우측 상단 차트) — 178 미만이면 소속/프로젝트 링크 누수
    ("fig_2",   2, F, 64,  r"^Figure 2:"),   # CARES overview (full-width 다이어그램)
    ("fig_3",   6, R, 259, r"^Figure 3:"),   # accuracy vs TTFT — 259 미만이면 위 문단 마지막 줄 조각 누수
    ("fig_4",   6, R, 481, r"^Figure 4:"),   # predicted resolution histogram (OCRBench)
    ("fig_5",   8, L, 70,  r"^Figure 5:"),   # cross-teacher confusion matrix
    ("table_1", 5, F, 60,  r"^Table 1:"),    # labeling pipeline (예시 이미지 포함)
    ("table_2", 7, F, 64,  r"^Table 2:"),    # main results (9 benchmarks + CARES-AR)
    ("table_3", 8, R, 70,  r"^Table 3:"),    # feature extractor ablation
    ("table_4", 8, R, 395, r"^Table 4:"),    # binary vs ternary
    ("table_5", 9, L, 157, r"^Table 5:"),    # discrete vs continuous
    ("table_6", 9, L, 648, r"^Table 6:"),    # label smoothing
]


def caption_bbox(page, pattern):
    for b in page.get_text("blocks"):
        if b[6] != 0:
            continue
        txt = re.sub(r"\s+", " ", b[4]).strip()
        if re.match(pattern, txt):
            return fitz.Rect(b[0], b[1], b[2], b[3])
    raise SystemExit(f"[FAIL] caption not found: {pattern} on p{page.number + 1}")


def main():
    doc = fitz.open(str(PDF))
    OUT.mkdir(exist_ok=True)
    zoom = DPI / 72
    for name, pno, (x0, x1), y_top, pat in PLAN:
        page = doc[pno - 1]
        cap = caption_bbox(page, pat)
        clip = fitz.Rect(x0, y_top, x1, cap.y1 + 4)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip)
        out = OUT / f"{name}.png"
        pix.save(str(out))
        print(f"[ok] {name}: p{pno} clip=({x0},{y_top},{x1},{cap.y1 + 4:.0f}) -> {pix.width}x{pix.height}")
    print("[done]")


if __name__ == "__main__":
    sys.exit(main())
