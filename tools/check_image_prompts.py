# -*- coding: utf-8 -*-
"""codex ImageGen prompt_*.txt 밀도·구조 검사 (이미지 생성 전 의무 - component_rules.md §11.8).

이미지 품질의 단일 변수는 prompt.txt 본문의 정보량이다. imagegen은 쓰지 않은 것을
채워 넣지 않으므로, 성긴 프롬프트는 반드시 여백 크고 정보량 적은 그림으로 돌아온다
(정본 학습 사례: 27. lupi 1차 dissection_overview, 2026-08-01).

이 스크립트는 §11.8.2(필수 5블록) · §11.8.3(패널 3요소) · §11.8.4(밀도 등급)를
기계적으로 검사한다. **codex를 호출하기 전에** 돌려서 FAIL이 0인지 확인한다.

검사 항목:
  ① 캔버스 선언 (WxH) - overview는 1536x864 고정
  ② 레이아웃 블록 + 밀도 지시("빈 공간을 남기지 말 것")
  ③ 패널 수 - 종류별 최소치 (overview 12 / concept 4 / qa 3)
  ④ 실제 수치 - 팔레트·해상도를 제외한 본문의 숫자 리터럴 최소 개수
  ⑤ 색상 팔레트 hex ≥3
  ⑥ 스타일 지시 "NOT a transparent cutout"
  ⑦ 6번째 계명 "NO paper title at top"
  ⑧ 비ASCII 이물 (한중일 한자 등) - 이미지에 그대로 그려지는 사고 방지
  ⑨ 분량 하한 (종류별)
  ⑩ 짝이 되는 PNG 존재 여부 (정보성 warn)

사용법:
    python tools/check_image_prompts.py "papers/N. shortname"   # 한 논문
    python tools/check_image_prompts.py --all                    # papers/ 전체
    python tools/check_image_prompts.py <prompt 파일 경로>        # 파일 하나

하드 실패(FAIL) = 캔버스·5단 헤더·overview 수치/분량·컷아웃·6계명·한자 이물.
경고(warn) = 패널 수·팔레트·레이아웃 문구·개념도 수치·PNG 부재 (서식 의존이 커 참고용).
papers 5~9·20·24 등 2026-05-12(6계명 도입) 이전 프롬프트는 ⑦에서 FAIL이 나는 것이 정상이다 -
이 게이트는 지금 만들고 있는 논문에 적용한다.

정본: rules/component_rules.md §11.8 (+ overview 전용 §14.5)
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent

# 종류별 밀도 등급 (§11.8.4) - (라벨, 최소 패널, 최소 수치, 최소 바이트, 고정 해상도)
GRADES = {
    "overview": ("dissection_overview", 12, 8, 3000, "1536x864"),
    "concept":  ("knowledge_/questions_/dissection_/simulator_", 4, 3, 1200, None),
    "qa":       ("qa_", 3, 2, 800, None),
}


def grade_of(stem: str) -> str:
    """prompt_<purpose>.txt 의 purpose 로부터 밀도 등급을 판정."""
    if stem == "dissection_overview":
        return "overview"
    if stem.startswith("qa_"):
        return "qa"
    return "concept"


# 패널로 인정하는 줄 - "1)" / "- " / "· " / "[1단 - ...]" / "[블록 N]"
RE_NUMBERED = re.compile(r"(?m)^\s*\d+\)\s*\S")
RE_BULLET = re.compile(r"(?m)^[ 	]*(?:[-·•*]|\(\S+?\)|위:|아래:|중앙:|좌:|우:)\s*\S")
RE_SECTION = re.compile(r"(?m)^\s*\[[^\]]+\]")
# 팔레트/해상도 줄은 수치 집계에서 제외
RE_HEX = re.compile(r"#[0-9a-fA-F]{6}")
RE_CANVAS = re.compile(r"\b(\d{3,4})\s*[xX×]\s*(\d{3,4})\b")
# 한중일 한자 (한글·가나 제외) - 프롬프트에 섞이면 이미지에 그대로 그려진 사례 있음
RE_HAN = re.compile(r"[一-鿿]")


def count_numbers(body: str) -> int:
    """팔레트 hex·캔버스 선언·패널 번호를 뺀 뒤 남는 숫자 리터럴 개수 (실제 수치의 대리 지표)."""
    t = RE_HEX.sub(" ", body)
    t = RE_CANVAS.sub(" ", t)
    t = RE_NUMBERED.sub(" ", t)
    t = re.sub(r"(?m)^\s*\[\d+단[^\]]*\]", " ", t)
    return len(re.findall(r"\d[\d,\.]*", t))


def check_prompt(path: Path):
    fails, warns = [], []
    body = path.read_text(encoding="utf-8")
    stem = path.stem[len("prompt_"):] if path.stem.startswith("prompt_") else path.stem
    g = grade_of(stem)
    label, min_panels, min_nums, min_bytes, fixed_res = GRADES[g]

    # ① 캔버스 선언
    m = RE_CANVAS.search(body)
    if not m:
        fails.append("① 캔버스 선언 없음 - 첫 줄에 `... 1024x1024.` 형태로 해상도를 박을 것 (§11.8.2)")
    elif fixed_res and f"{m.group(1)}x{m.group(2)}" != fixed_res:
        fails.append(f"① 해상도 {m.group(1)}x{m.group(2)} - {label}은 {fixed_res} 고정 (§14.5)")

    # ② 레이아웃 + 밀도 지시
    if not re.search(r"레이아웃|전체 구성|구성:", body):
        warns.append("② 전체 레이아웃 블록이 안 보임 - 블록 개수·배치 방향을 명시 (§11.8.2)")
    if g == "overview" and not re.search(r"빈 공간|정보 밀도|밀도를 높게|가득", body):
        warns.append("② 밀도 지시 문구 없음 - `정보 밀도를 높게 - 빈 공간을 남기지 말 것` 권장 (§11.8.2)")

    # ③ 패널 수 - 팔레트/스타일 지시 구간의 불릿은 밀도가 아니므로 제외
    spec = re.split(r"(?m)^\s*(?:색상 팔레트|스타일 지시)", body)[0]
    n_panel = len(RE_NUMBERED.findall(spec)) + len(RE_BULLET.findall(spec))
    n_section = len(RE_SECTION.findall(spec))
    if n_panel < min_panels:
        warns.append(
            f"③ 패널 명세 {n_panel}개 (권장 {min_panels}+) - 패널마다 번호를 붙이고 "
            f"(시각 형태 + 실제 수치 + 영어 캡션) 3요소를 적을 것 (§11.8.3)"
        )
    if g == "overview" and n_section < 5:
        fails.append(f"③ 단 헤더 {n_section}개 - PROBLEM/OBSERVATION/METHOD/NOVELTY/RESULTS 5단 고정 (§14.5)")

    # ④ 실제 수치
    n_num = count_numbers(body)
    if n_num < min_nums:
        msg = (f"④ 본문 수치 {n_num}개 (최소 {min_nums}) - '성능이 향상된다' 대신 논문 표·그림에서 "
               f"읽은 실제 값을 박을 것 (§11.8.3)")
        # 순수 개념도는 수치가 없는 것이 정상 - overview 에서만 하드 실패
        (fails if g == "overview" else warns).append(msg)

    # ⑤ 팔레트
    if len(set(RE_HEX.findall(body))) < 3:
        warns.append("⑤ 색상 팔레트 hex 3개 미만 - v4 저채도 토큰을 나열 (§11.8.2)")

    # ⑥ 컷아웃 방지
    if "NOT a transparent cutout" not in body:
        fails.append("⑥ `NOT a transparent cutout` 누락 - imagegen 기본값이 컷아웃 (§11.2 4계명)")

    # ⑦ 6번째 계명
    if "NO paper title at top" not in body:
        fails.append("⑦ `NO paper title at top, NO standalone header, NO author names.` 누락 (§11.2 6계명)")

    # ⑧ 비ASCII 이물
    han = sorted(set(RE_HAN.findall(body)))
    if han:
        fails.append(f"⑧ 한자 이물 {''.join(han)} - 이미지에 그대로 그려진다. 한글/영어로 교체 (§11.8.3)")

    # ⑨ 분량 하한
    size = len(body.encode("utf-8"))
    if size < min_bytes:
        msg = f"⑨ 분량 {size}B (하한 {min_bytes}B) - {label} 밀도 등급 미달 (§11.8.4)"
        (fails if g == "overview" else warns).append(msg)

    # ⑩ 결과 PNG
    if not (path.parent / f"{stem}.png").exists():
        warns.append(f"⑩ {stem}.png 없음 - 아직 생성 전이거나 파일명 불일치")

    return fails, warns, (n_panel, n_num, size)


def check_paper(paper: Path):
    gen = paper / "assets" / "generated"
    if not gen.is_dir():
        return 0, 0, 0
    n_fail = n_warn = n_file = 0
    for f in sorted(gen.glob("prompt_*.txt")):
        fails, warns, stats = check_prompt(f)
        n_file += 1
        if fails or warns:
            print(f"  {f.name}  (패널 {stats[0]} · 수치 {stats[1]} · {stats[2]}B)")
        for msg in fails:
            print(f"    [FAIL] {msg}")
            n_fail += 1
        for msg in warns:
            print(f"    [warn] {msg}")
            n_warn += 1
    return n_fail, n_warn, n_file


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    arg = sys.argv[1]

    if arg.endswith(".txt"):
        p = Path(arg)
        fails, warns, stats = check_prompt(p)
        print(f"{p.name}  (패널 {stats[0]} · 수치 {stats[1]} · {stats[2]}B)")
        for m in fails:
            print(f"  [FAIL] {m}")
        for m in warns:
            print(f"  [warn] {m}")
        if fails:
            raise SystemExit(f"\n[FAIL] {len(fails)}건 - rules/component_rules.md §11.8 참조")
        print("\n[ok] 프롬프트 밀도·구조 통과")
        return

    papers = (sorted(p for p in (REPO / "papers").iterdir() if p.is_dir())
              if arg == "--all" else [Path(arg)])
    total_fail = 0
    for paper in papers:
        n_fail, n_warn, n_file = check_paper(paper)
        if n_file == 0:
            continue
        status = "FAIL" if n_fail else ("warn" if n_warn else "ok")
        print(f"[{status}] {paper.name}: prompts={n_file} fail={n_fail} warn={n_warn}")
        total_fail += n_fail
    if total_fail:
        raise SystemExit(
            f"\n[FAIL] 프롬프트 밀도·구조 위반 {total_fail}건 - "
            f"rules/component_rules.md §11.8 대로 고친 뒤 codex를 호출하세요."
        )
    print("\n[ok] 프롬프트 밀도·구조 위반 0건")


if __name__ == "__main__":
    main()
