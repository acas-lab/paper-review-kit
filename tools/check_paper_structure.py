# -*- coding: utf-8 -*-
"""check_paper_structure.py - 논문 폴더와 산출물이 표준 구조인지 검사한다.

검사 항목
  폴더   이름 규약, 필수 파일(tabs_data/study.json 포함), 산출물 1개
  탭     8탭의 id·순서, 라벨에 숫자 없음, 해시 라우팅
  자산   외부 이미지 0, id 규약, 번호 단조 증가, 자산 가이드 버튼
  문장   data-pair 영·한 쌍
  카드   summary 9행 태그, overview 이미지, 카드 8장
  수식   수식 카드는 Mathematics 탭에만, ⑤⑥ 탭 존재
  주입   메모 레이어, Q&A 버튼, Study 검토, 리더 자산 칩
  빈칸   기준 빌더(templates/paper_base)의 TODO_PAPER 미작성 0
  영상   video/ 입력 파일, TODO_PAPER 0, {ShortName}_video.mp4 (Stage 13 — papers/ 아래만. samples/ 정본은 영상이 없어도 된다)
  문자   &lt;b&gt;·&amp;lt; 누출 0, 교차 참조 0, v4 토큰

사용법
  python tools/check_paper_structure.py "papers/N. name"
  python tools/check_paper_structure.py "samples/cares"
  python tools/check_paper_structure.py --all        # papers/* + samples/* (산출물이 있는 폴더)
FAIL 이 있으면 종료 코드 1.
overview 이미지는 codex PNG(모드 A) 또는 빌더의 결정적 인라인 SVG(모드 B) 둘 다 허용한다.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABS = ["tab-reading", "tab-study", "tab-dissection", "tab-knowledge",
        "tab-math", "tab-questions", "tab-simulator", "tab-qa"]
SUMMARY_TAGS = ["한 줄", "이게 왜 문제인가 (Problem)", "저자의 핵심 관찰 (Observation)",
                "기존 방법은 왜 부족한가 (Gap)", "어떻게 해결했나 (Method)",
                "다른 논문과 무엇이 다른가 (Novelty)", "효과 - 숫자 (Results)",
                "한계와 의미 (Limitations & Implication)", "30초 요약 (For Beginners)"]
REQUIRED = ["config.json", "analysis.json", "structured.json", "translations/manual.json",
            "tabs_data/dissection.json", "tabs_data/knowledge.json", "tabs_data/questions.json"]
# summary 1행 태그는 "한 줄"이 정본 표기이고 "한 줄 요약"(samples/cares)도 같은 행으로 본다
TAG_ALIAS = {"한 줄 요약": "한 줄"}
CROSS = re.compile(r"[A-Za-z][A-Za-z0-9-]+\((?:papers )?[0-9]{1,2}\)")


def segment(html, tab):
    """탭 하나의 HTML 구간. 다음 탭 시작 전까지 자른다."""
    m = re.search(r'id="%s"' % tab, html)
    if not m:
        return ""
    rest = [x.start() for x in re.finditer(r'<section\b[^>]*\bid="tab-[a-z]+"', html) if x.start() > m.start()]
    end = rest[0] if rest else html.find("</main>", m.start())
    return html[m.start(): end if end > 0 else len(html)]


def check(paper):
    fails, warns = [], []
    legacy = False  # 배포본에는 구세대 논문이 없다 - 모든 차이를 FAIL 로 본다
    soft = fails

    # 폴더 이름 규약은 papers/ 아래에만 적용한다 (samples/cares 같은 정본은 예외)
    if paper.parent.name == "papers" and not re.fullmatch(r"\d+\. [a-z0-9_]+", paper.name):
        fails.append("폴더 이름 규약 위반")
    gen = paper / "assets" / "generated"
    if not (gen / "dissection_overview.png").exists() and not (gen / "dissection_overview.svg").exists():
        warns.append("overview PNG 없음 - 빌더의 인라인 SVG 폴백(모드 B)이면 정상")
    for rel in REQUIRED:
        if not (paper / rel).exists():
            soft.append("필수 파일 없음: %s" % rel)
    # study.json 은 기본 빌드 필수다(CLAUDE.md § 기본 빌드 범위). 빌더의 자동 셸은 개발 중 '작성 전'
    # 상태일 뿐 산출물이 아니다 - Study 검토 버튼(study_review_inject)도 study.json 을 기준 분석으로 쓴다.
    if not (paper / "tabs_data" / "study.json").exists():
        fails.append("필수 파일 없음: tabs_data/study.json - Stage 11(prompts/11_paper_study.md) 미완, "
                     "①′ Paper Study 셸은 산출물이 아니다")
    outs = sorted(paper.glob("*_output.html"))
    if len(outs) != 1:
        fails.append("산출물 HTML 수 = %d" % len(outs))
        return fails, warns
    html = re.sub(r"base64,[A-Za-z0-9+/=]+", "base64,", outs[0].read_text(encoding="utf-8"))

    # 탭
    panes = re.findall(r'<section\b[^>]*\bid="(tab-[a-z]+)"[^>]*class="[^"]*tab-pane', html)
    panes = [p for p in panes if p in TABS]
    if panes != TABS:
        fails.append("탭 구성·순서 불일치: %s" % panes)
    labels = re.findall(r'<button[^>]*class="tab-btn[^"]*"[^>]*data-tab="tab-[a-z]+"[^>]*>(.*?)</button>', html, re.S)
    if len(labels) != 8:
        fails.append("탭 버튼 수 = %d" % len(labels))
    if any(re.search(r"[0-9①-⑨]", re.sub(r"<[^>]+>", "", x)) for x in labels):
        fails.append("탭 라벨에 숫자")
    if "location.hash" not in html:
        fails.append("해시 라우팅 없음")

    # 이미지
    srcs = re.findall(r'<img\b[^>]*\bsrc="([^"]*)"', html)
    ext = [s[:60] for s in srcs if s and not s.startswith("data:")]
    if ext:
        fails.append("외부 이미지 %d개: %s" % (len(ext), ext[:2]))

    # 자산
    reading = segment(html, "tab-reading")
    ids = re.findall(r'<(?:figure|article|div)\b[^>]*\b(?:id|data-asset-id)="((?:fig|table|box)_[A-Za-z0-9_]+)"', reading)
    seen = list(dict.fromkeys(ids))
    bad = [x for x in seen if not re.fullmatch(r"(fig|table|box)_\d+", x)]
    if bad:
        soft.append("자산 id 규약 위반: %s" % bad[:4])
    note = ""
    try:
        cfg = json.loads((paper / "config.json").read_text(encoding="utf-8"))
        note = (cfg.get("meta") or {}).get("asset_order_note", "")
    except Exception:
        fails.append("config.json 읽기 실패")
    for kind in ("fig", "table", "box"):
        nums = [int(x.split("_")[1]) for x in seen if re.fullmatch(r"%s_\d+" % kind, x)]
        if nums != sorted(nums):
            (warns if note or legacy else fails).append("%s 번호 역행: %s%s" % (kind, nums, " (asset_order_note 있음)" if note else ""))
    fabs = len(re.findall(r'class="study-fab"', reading))
    if fabs < len(seen):
        soft.append("학습 가이드 버튼 %d < 자산 %d" % (fabs, len(seen)))

    # 문장 쌍
    pairs = {}
    for sid in re.findall(r'data-pair="([^"]+)"', reading):
        pairs[sid] = pairs.get(sid, 0) + 1
    odd = [k for k, v in pairs.items() if v % 2]
    if not pairs:
        fails.append("data-pair 없음")
    if odd:
        soft.append("영·한 쌍이 맞지 않는 문장 %d개: %s" % (len(odd), odd[:4]))

    # summary 카드
    diss = segment(html, "tab-dissection")
    cards = len(re.findall(r'<article\b[^>]*class="diss-card\b', diss))
    if cards != 8:
        soft.append("dissection 카드 수 = %d" % cards)
    sm = re.search(r'<article\b[^>]*class="diss-card diss-summary".*?</article>', diss, re.S)
    if not sm:
        fails.append("diss-summary 카드 없음")
    else:
        tags = [re.sub(r"^[①-⑨]\s*", "", re.sub(r"\s+", " ", t).strip()).replace("&amp;", "&") for t in
                re.findall(r'class="diss-(?:row-)?tag">(.*?)</', sm.group(0), re.S)]
        tags = [TAG_ALIAS.get(t, t).replace("—", "-").replace("–", "-") for t in tags]  # 대시 변형은 같은 태그
        if len(tags) != 9:
            fails.append("summary 행 수 = %d" % len(tags))
        elif tags != SUMMARY_TAGS:
            fails.append("summary 태그 차이: %s" % [t for t in tags if t not in SUMMARY_TAGS][:3])
        if 'class="diss-overview-figure"' not in sm.group(0) and "<svg" not in sm.group(0):
            fails.append("overview 이미지 없음")
        if CROSS.search(re.sub(r"<[^>]+>", "", sm.group(0))):
            fails.append("summary 에 교차 참조: %s" % CROSS.search(re.sub(r"<[^>]+>", "", sm.group(0))).group(0))

    # 수식
    k_eq = segment(html, "tab-knowledge").count('class="eq-card"')
    m_seg = segment(html, "tab-math")
    if k_eq:
        fails.append("수식 카드 %d장이 Background 탭에 있음" % k_eq)
    if "수식 카드가 없는" in m_seg and html.count('class="eq-card"'):
        fails.append("Mathematics 탭이 비어 있음")

    # ①′ Paper Study 는 셸이면 안 된다 (study.json 은 있는데 빌드가 오래된 경우 포함)
    if "section-empty-note" in segment(html, "tab-study"):
        fails.append("①′ Paper Study 가 셸 상태 - study.json 작성 후 _build.py 재실행")

    # ⑤⑥ 패널
    for tab in ("tab-simulator", "tab-qa"):
        if 'class="tab-intro"' not in segment(html, tab):
            fails.append("%s 에 tab-intro 없음" % tab)

    # 주입
    for mark, name in [("memo-drawer", "학습 메모"), ("qa-gen-bar", "Q&A 버튼"),
                       ("study-review-btn", "Study 검토"), ("PR_ASSET_CHIPS_BEGIN", "리더 자산 칩")]:
        if mark not in html:
            soft.append("주입 누락: %s" % name)
    if not re.search(r"\.memo-(?:fab|drawer)[^{]*\{[^}]*z-index:\s*2400", html):
        fails.append("메모 z-index 2400 아님")

    # 기준 빌더의 빈칸
    # 빈칸 표시는 TODO_PAPER_<이름> 형식이다. 빌더 머리 주석의 설명 문구("TODO_PAPER 표시 전부")는
    # 빈칸이 아니므로 밑줄까지 맞춰 본다(밑줄 없이 찾으면 다 채운 복사본도 항상 FAIL).
    left = [n for n in ("_build.py", "_mk_corpus.py") if (paper / n).exists()
            and "TODO_PAPER_" in (paper / n).read_text(encoding="utf-8")]
    if left or "TODO_PAPER_" in html:
        fails.append("TODO_PAPER 미작성: %s" % (left or "산출물"))

    # 영상 (Stage 13, rules/video_rules.md): video/ 입력 + HTML 옆 {ShortName}_video.mp4
    vd = paper / "video"
    if vd.is_dir():
        miss = [n for n in ("기획안.md", "spec.py", "scenes.js") if not (vd / n).exists()]
        if miss:
            fails.append("영상 입력 누락: video/%s" % ", video/".join(miss))
        todo = [n for n in ("기획안.md", "spec.py", "clipspec.py") if (vd / n).exists()
                and "TODO_PAPER" in (vd / n).read_text(encoding="utf-8")]
        if todo:
            fails.append("영상 TODO_PAPER 미작성: %s" % todo)
        if not list(paper.glob("*_video.mp4")):
            warns.append("영상 산출물 없음({ShortName}_video.mp4) - python tools/video/make_video.py \"%s\" status" % relpath(paper))
    elif paper.parent.name == "papers":
        warns.append("영상 없음(video/) - python tools/video/make_video.py \"%s\" new (사용자가 영상을 빼라고 했으면 무시)" % relpath(paper))

    # 문자
    for bad_s in ("&lt;b&gt;", "&amp;lt;"):
        c = html.count(bad_s)
        if c:
            fails.append("%s 누출 %d건" % (bad_s, c))
    if "--accent:#5e6488" not in html.replace(" ", ""):
        soft.append("v4 토큰 없음")
    return fails, warns


def relpath(paper):
    try:
        return paper.relative_to(ROOT).as_posix()
    except ValueError:
        return str(paper)


def papers():
    """papers/* (번호 순) + samples/* - 산출물 HTML 이 있는 폴더만. 빈 배포본에서도 정본을 검사한다."""
    out = []
    base = ROOT / "papers"
    if base.is_dir():
        for d in base.iterdir():
            if d.is_dir() and re.match(r"\d+\. ", d.name) and list(d.glob("*_output.html")):
                out.append(d)
    out.sort(key=lambda x: int(x.name.split(".")[0]))
    sm = ROOT / "samples"
    if sm.is_dir():
        out += [d for d in sorted(sm.iterdir()) if d.is_dir() and list(d.glob("*_output.html"))]
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    targets = papers() if sys.argv[1] == "--all" else [Path(sys.argv[1]).resolve()]
    nf = nw = 0
    for p in targets:
        f, w = check(p)
        nf += len(f)
        nw += len(w)
        if f or w:
            print("[%s] %s" % ("FAIL" if f else "warn", p.name))
            for x in f:
                print("  FAIL  " + x)
            for x in w:
                print("  warn  " + x)
        else:
            print("[ok] %s" % p.name)
    print("합계: %d편, FAIL %d, warn %d" % (len(targets), nf, nw))
    sys.exit(1 if nf else 0)


if __name__ == "__main__":
    main()
