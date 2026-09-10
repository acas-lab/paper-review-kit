# -*- coding: utf-8 -*-
"""콘텐츠 JSON의 HTML 이스케이프 검사 (빌드 전 의무 - component_rules.md 체크리스트 18번).

수식 표기(`X_{a<i}`, `ℓ<k` 류)의 이스케이프 안 된 `<`가 HTML 태그로 파싱되면, 브라우저의
태그 수프 복구 규칙이 그 지점 이후 문서 전체를 <b>/<i>로 재구성한다 - 문서 뒷부분 전체가
굵게 보이는 버그의 원인 (정본 학습 사례: 24. geollava8k Eq 5, 2026-07-08).

검사 2종:
  ① 잘 정의된 태그를 제거한 뒤 남는 `<`+영문자/`/` → 태그 수프 위험 (FAIL)
  ② 문자열 안 태그 열림/닫힘 불균형 (b/i/em/strong/span/div 등) → 경고 (WARN)

사용법:
    python tools/check_html_escape.py "papers/N. shortname"     # 한 논문
    python tools/check_html_escape.py --all                      # papers/ 전체

수정 규약: tex 안은 `\\lt`/`\\gt`, 일반 텍스트는 `&lt;`/`&gt;` (rules/math_rules.md § 부등호).
"""
import json
import re
import sys
from pathlib import Path

try:  # Windows cp949 콘솔에서도 한글·기호(—·→…) 출력이 깨지거나 죽지 않도록
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO = Path(__file__).parent.parent

# 잘 정의된 태그 (여는/닫는/self-closing, 속성 허용) - 이걸 제거하고 남는 < 가 위험 신호
WELLFORMED = re.compile(r"</?[a-zA-Z][a-zA-Z0-9-]*(\s[^<>]*)?/?>")
DANGLING = re.compile(r"<[a-zA-Z/]")
BALANCE_TAGS = ("b", "i", "em", "strong", "span", "div", "sub", "sup", "code", "u", "mark")

TARGET_GLOBS = ["config.json", "analysis.json", "tabs_data/*.json", "translations/*.json"]


# 빌더가 esc()로 자동 이스케이프하는 필드 - 원문 텍스트는 위험하지 않다
ESCAPED_KEYS = {"original", "text", "title", "caption", "captions", "captions_en"}


def iter_strings(obj, path="", key=None):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from iter_strings(v, f"{path}.{k}", k)
    elif isinstance(obj, list):
        for n, v in enumerate(obj):
            yield from iter_strings(v, f"{path}[{n}]", key)
    elif isinstance(obj, str):
        if key not in ESCAPED_KEYS:
            yield path, obj


def check_string(s):
    """(fails, warns) - fails: 태그 수프 위험 지점 컨텍스트, warns: 태그 불균형."""
    fails = []
    stripped = WELLFORMED.sub("", s)
    for m in DANGLING.finditer(stripped):
        ctx = stripped[max(0, m.start() - 40):m.start() + 30].replace("\n", " ")
        fails.append(f"…{ctx}…")
    warns = []
    for tag in BALANCE_TAGS:
        n_open = len(re.findall(rf"<{tag}(\s[^<>]*)?>", s))
        n_close = len(re.findall(rf"</{tag}>", s))
        if n_open != n_close:
            warns.append(f"<{tag}> {n_open}열림/{n_close}닫힘")
    return fails, warns


def check_paper(paper: Path):
    n_fail = n_warn = 0
    for pattern in TARGET_GLOBS:
        for f in sorted(paper.glob(pattern)):
            if f.name.endswith(".bak"):
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8-sig"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            rel = f.relative_to(paper)
            for path, s in iter_strings(data):
                fails, warns = check_string(s)
                for msg in fails:
                    print(f"  [FAIL] {rel}{path}: {msg}")
                    n_fail += 1
                for msg in warns:
                    print(f"  [warn] {rel}{path}: {msg}")
                    n_warn += 1
    return n_fail, n_warn


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "--all":
        papers = sorted(p for p in (REPO / "papers").iterdir() if p.is_dir())
    else:
        papers = [Path(sys.argv[1])]
    total_fail = 0
    for paper in papers:
        n_fail, n_warn = check_paper(paper)
        status = "FAIL" if n_fail else ("warn" if n_warn else "ok")
        print(f"[{status}] {paper.name}: fail={n_fail} warn={n_warn}")
        total_fail += n_fail
    if total_fail:
        raise SystemExit(f"\n[FAIL] 태그 수프 위험 {total_fail}건 - tex는 \\lt/\\gt, 텍스트는 &lt;/&gt;로 수정하세요.")
    print("\n[ok] 태그 수프 위험 0건")


if __name__ == "__main__":
    main()
