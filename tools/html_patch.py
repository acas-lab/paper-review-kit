# -*- coding: utf-8 -*-
"""html_patch.py - 재빌드 없이 산출물 HTML 과 원천 데이터를 함께 고친다.

구세대 HTML 은 빌드 후 교정이 산출물에만 들어간 경우가 있어 재빌드가 그 교정을 되돌릴 수 있다.
이 도구는 지정한 문자열만 바꾸고, 대상에 없으면 아무것도 쓰지 않고 실패한다.

사용법
  python tools/html_patch.py "papers/N. name" asset fig_3 table_1 ...   (정본은 "samples/cares")
      assets/<id>.png 의 HEAD 판 base64 를 현재 판 base64 로 교체한다(PNG 를 먼저 교체해 둘 것).
      --old <path> 로 교체 전 PNG 를 직접 지정할 수 있다(자산 1개일 때만).
  python tools/html_patch.py "papers/N. name" text patches.json [--dry-run]
      patches.json = [{"old": "...", "new": "...", "files": ["tabs_data/dissection.json"], "html": 1}]
      old 는 JSON 안에서도 HTML 안에서도 정확히 일치해야 한다. 표기가 다르면 항목을 나눈다.
      files 는 논문 폴더 기준 상대 경로(없으면 생략), html 은 산출물에서 기대하는 등장 횟수
      (기본 1, 0 이면 산출물은 건드리지 않음). files 안에서는 1회 이상이면 전부 바꾼다.
"""
import base64
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:  # Windows cp949 콘솔에서도 한글 출력이 깨지지 않도록
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def fail(msg):
    sys.exit("[html_patch] FAIL: " + msg)


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def write(p, s):
    tmp = str(p) + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(s)
    os.replace(tmp, p)


def head_bytes(path):
    # 저장소 루트 기준 상대 경로로 바꿔 어느 작업 디렉토리에서 실행해도 같은 판을 읽는다
    try:
        rel = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        rel = path.as_posix()
    r = subprocess.run(["git", "show", "HEAD:" + rel], capture_output=True, cwd=ROOT)
    if r.returncode != 0:
        fail("HEAD 에 %s 없음 - --old 로 지정" % rel)
    return r.stdout


def cmd_asset(paper, out, args):
    old_file = None
    if "--old" in args:
        i = args.index("--old")
        old_file = Path(args[i + 1])
        del args[i:i + 2]
        if len(args) != 1:
            fail("--old 는 자산 1개일 때만")
    html = read(out)
    for aid in args:
        png = paper / "assets" / (aid + ".png")
        if not png.exists():
            fail("%s 없음" % png)
        old = old_file.read_bytes() if old_file else head_bytes(png)
        new = png.read_bytes()
        if old == new:
            fail("%s: 교체 전후가 같음" % aid)
        o, n = base64.b64encode(old).decode(), base64.b64encode(new).decode()
        c = html.count(o)
        if c == 0:
            fail("%s: 산출물에 이전 판 base64 없음" % aid)
        html = html.replace(o, n)
        print("[html_patch] asset %s: %d곳, %dKB -> %dKB" % (aid, c, len(old) // 1024, len(new) // 1024))
    write(out, html)


def cmd_text(paper, out, args):
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    patches = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    html = read(out)
    files = {}
    errs = []
    for i, p in enumerate(patches):
        old, new = p["old"], p["new"]
        want = p.get("html", 1)
        got = html.count(old)
        if got != want:
            errs.append("#%d html 등장 %d (기대 %d): %s" % (i, got, want, old[:70]))
        elif want:
            html = html.replace(old, new)
        for rel in p.get("files", []):
            if rel not in files:
                files[rel] = read(paper / rel)
            # JSON 파일 안에서는 JSON 문자열 이스케이프 형태도 찾는다
            forms = [(old, new)]
            if rel.endswith(".json"):
                forms.append((json.dumps(old, ensure_ascii=False)[1:-1], json.dumps(new, ensure_ascii=False)[1:-1]))
            for fo, fn in forms:
                if fo in files[rel]:
                    files[rel] = files[rel].replace(fo, fn)
                    break
            else:
                errs.append("#%d %s 에 없음: %s" % (i, rel, old[:70]))
    if errs:
        fail("\n  " + "\n  ".join(errs))
    for rel, s in files.items():
        if rel.endswith(".json"):
            json.loads(s)
    if dry:
        print("[html_patch] dry-run ok: %d건" % len(patches))
        return
    for rel, s in files.items():
        write(paper / rel, s)
    write(out, html)
    print("[html_patch] text ok: %d건, 원천 %d개" % (len(patches), len(files)))


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    paper = Path(sys.argv[1])
    outs = sorted(paper.glob("*_output.html"))
    if len(outs) != 1:
        fail("산출물 HTML 수 = %d" % len(outs))
    {"asset": cmd_asset, "text": cmd_text}[sys.argv[2]](paper, outs[0], sys.argv[3:])


if __name__ == "__main__":
    main()
