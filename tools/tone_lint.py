# -*- coding: utf-8 -*-
"""tone_lint.py — "감성 온도 0 · 논리 최대" 정책(CLAUDE.md, 2026-07-09) 위반 탐지.

Claude 가 직접 쓴 한국어 서술 prose 에서 감성·감탄·응원·과장 수사를 찾아낸다.
번역(① manual.json/refined.json)은 원문 충실성이 우선이라 **검사 대상에서 제외**한다.

검사 대상 파일(논문 폴더 내):
  analysis.json · tabs_data/*.json(qa/dissection/knowledge/questions/study) · config.json
  그리고 *_output.html 의 텍스트 노드(대략적 — 태그/스크립트 제외).

사용법:
  python tools/tone_lint.py "samples/cares"      # 단일 논문 리포트
  python tools/tone_lint.py --all                   # 전체 논문 요약 리포트
  python tools/tone_lint.py "samples/cares" --fix # 안전 치환만 자동 적용(JSON 한정)

--fix 는 **문법적으로 안전한 치환/삭제**만 한다(아래 SAFE_FIX). 미묘한 재작성은
사람/Claude 가 직접 Edit 하도록 리포트만 남긴다(오탐/문법 파괴 방지).

정본: papers 1~26 (2026-07-09).
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (카테고리, 정규식, 설명) — 근거→함의 논리에 불필요한 감성 수사
PATTERNS = [
    ("감탄·평가", r"흥미롭게도|흥미로[운움]|흥미롭다|흥미로웠|놀랍게도|놀라운|경이로[운움]|인상적(?:인|이다|으로|이었)|압도적(?:인|이다|으로)|주목할\s*만한|눈길을\s*끄는"),
    ("평가 형용사", r"우아(?:한|하게|함|하다)|훌륭(?:한|하다|합니다|해요|히)|매력적(?:인|이다|이었)|아름다[운움]|보기\s*드[문물]|기발한|절묘한|영리(?:한|하게)"),
    ("응원·친근체", r"살펴봅시다|알아봅시다|해\s*봅시다|함께\s*살펴|걱정\s*마세요|걱정하지\s*마|잘\s*하고\s*있|훌륭해요|어렵지\s*않아요|쉽게\s*생각하면"),
    ("과장 강조", r"정말(?![가-힣])|굉장히|엄청(?:난|나게|)|대단히|무척|어마어마"),
    ("감성 강조부사", r"그저|단순히\s*아름|마법(?:처럼|같)|환상적"),
]
COMPILED = [(c, re.compile(p), p) for c, p in PATTERNS]

# 문법적으로 안전한 자동 치환(JSON 문자열 값 한정). 명사 수식어 삭제·문두 부사 삭제 등
# 앞뒤 맥락을 파괴하지 않는 것만. 술어("특히 흥미롭다") 삭제나 의미 있는 부사("정말"→상황별)는
# 문법·의미 파괴 위험이 있어 제외 — 리포트만 남기고 사람/Claude 가 직접 Edit.
SAFE_FIX = [
    (re.compile(r"흥미롭게도,?\s*"), ""),             # 문두 감성 부사 → 삭제
    (re.compile(r"놀랍게도,?\s*"), ""),
    (re.compile(r"흥미로운\s+부산물"), "부산물"),     # 명사 수식어 삭제
    (re.compile(r"보기\s*드문\s*"), ""),              # 명사 앞 평가 수식어 삭제
    (re.compile(r"주목할\s*만한\s*"), ""),
    (re.compile(r"눈길을\s*끄는\s*"), ""),
    (re.compile(r"매우\s+매우"), "매우"),
]

# HTML 에서 태그/스크립트/스타일 제거하고 텍스트만 (대략)
_TAG = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
_ANGLE = re.compile(r"<[^>]+>")
# 번역(① tab-reading)은 원문 충실성이 우선이라 감성 정책 대상에서 제외 (CLAUDE.md).
# 리딩 탭 내부에 이른 </section> 이 있을 수 있어, 다음 <section id= 직전(또는 문서 끝)까지 통째로 제거.
_READING = re.compile(r'<section id="tab-reading".*?(?=<section id="tab-|\Z)', re.S)


def scan_text(text):
    hits = []
    for cat, rx, _ in COMPILED:
        for m in rx.finditer(text):
            s = max(0, m.start() - 30)
            e = min(len(text), m.end() + 30)
            ctx = text[s:e].replace("\n", " ")
            hits.append((cat, m.group(0), ctx))
    return hits


def target_files(folder):
    files = []
    for name in ["analysis.json", "config.json"]:
        p = folder / name
        if p.exists():
            files.append(p)
    td = folder / "tabs_data"
    if td.is_dir():
        files += sorted(td.glob("*.json"))
    files += sorted(folder.glob("*_output.html"))
    return files


def scan_file(p):
    raw = p.read_text(encoding="utf-8")
    if p.suffix == ".html":
        t = _READING.sub(" ", raw)  # 번역 탭 제외 (정책 범위 밖)
        t = _TAG.sub(" ", t)
        t = _ANGLE.sub(" ", t)
    else:
        t = raw
    return scan_text(t)


def apply_fix(folder):
    changed = []
    for p in target_files(folder):
        if p.suffix != ".json":
            continue  # 자동 치환은 JSON 값 한정(HTML 은 리포트만)
        raw = p.read_text(encoding="utf-8")
        new = raw
        for rx, rep in SAFE_FIX:
            new = rx.sub(rep, new)
        if new != raw:
            # JSON 유효성 확인 후 저장
            try:
                json.loads(new)
            except Exception as e:
                print(f"  [skip-fix] {p.name}: 치환 후 JSON 깨짐 ({e}) — 수동 확인 필요")
                continue
            p.write_text(new, encoding="utf-8")
            changed.append(p.name)
    return changed


def report_folder(folder, verbose=True):
    total = 0
    per = {}
    for p in target_files(folder):
        hits = scan_file(p)
        if hits:
            per[p.name] = hits
            total += len(hits)
    if verbose:
        print(f"\n=== {folder.name} — 감성 안티패턴 {total}건 ===")
        for name, hits in per.items():
            print(f"  [{name}] {len(hits)}건")
            for cat, word, ctx in hits[:40]:
                print(f"    · ({cat}) '{word}'  …{ctx}…")
    return total


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="감성 온도 0 정책 린터")
    ap.add_argument("folder", nargs="?", help='"papers/N. name"')
    ap.add_argument("--all", action="store_true", help="papers 전체 요약")
    ap.add_argument("--fix", action="store_true", help="안전 치환 자동 적용(JSON)")
    args = ap.parse_args()

    if args.all:
        base = ROOT / "papers"
        grand = 0
        rows = []
        for d in sorted(base.iterdir()):
            if d.is_dir() and list(d.glob("*_output.html")):
                n = report_folder(d, verbose=False)
                rows.append((d.name, n))
                grand += n
        print("=== 전체 감성 안티패턴 요약 ===")
        for name, n in sorted(rows, key=lambda x: -x[1]):
            flag = "  ⚠" if n else ""
            print(f"  {n:4d}  {name}{flag}")
        print(f"  ----\n  {grand:4d}  합계")
        return

    if not args.folder:
        raise SystemExit('usage: python tools/tone_lint.py "papers/N. name" [--fix] | --all')
    folder = Path(args.folder)
    if not folder.is_absolute():
        folder = ROOT / folder
    if args.fix:
        changed = apply_fix(folder)
        print(f"[fix] 안전 치환 적용: {changed if changed else '(변경 없음)'}")
    report_folder(folder)


if __name__ == "__main__":
    main()
