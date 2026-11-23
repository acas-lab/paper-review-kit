# -*- coding: utf-8 -*-
"""tabs_data/study.json의 모든 ref가 structured.json / config#asset_layout에 실존하는지 검증.

study.json의 ref 종류 (rules/component_rules.md §17, prompts/11):
  - sentence_id  (p_intro_2_s5)  → structured.json의 문장
  - section_id   (s_intro)       → structured.json의 섹션
  - paragraph_id (p_m_label)     → structured.json의 문단
  - asset_id     (fig_3/table_2) → config.json#asset_layout

검사 대상: read[].sec, evidence[].ref, guide_questions[].ref, author_claims[].evidence[].ref,
          claude_items[].evidence[].ref, result_assets[], assets[].

사용법: python tools/check_study_refs.py "papers/N. shortname"
        python tools/check_study_refs.py --all      # papers/* + samples/* (산출물이 있는 폴더)
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


def collect_ids(paper: Path):
    st = json.loads((paper / "structured.json").read_text(encoding="utf-8"))
    sec, para, sent = set(), set(), set()
    for s in st["sections"]:
        sec.add(s["section_id"])
        for p in s["paragraphs"]:
            para.add(p["paragraph_id"])
            for x in p["sentences"]:
                sent.add(x["sentence_id"])
    cfg = json.loads((paper / "config.json").read_text(encoding="utf-8-sig"))
    al = cfg.get("asset_layout", [])
    # v4 list-format [[aid, pid, type], …] 또는 v3 dict-format {aid: {...}} 양쪽 허용
    assets = set(al.keys()) if isinstance(al, dict) else {a[0] for a in al}
    return sec, para, sent, assets


def walk_refs(study):
    """(ref, kind_hint, path) 목록. kind_hint: 'sec' | 'ref' | 'asset'."""
    out = []

    def ev(lst, path):
        for i, e in enumerate(lst or []):
            out.append((e["ref"], "ref", f"{path}[{i}]"))

    p1 = study["phase1"]
    for a in p1["scan"].get("assets", []):
        out.append((a, "asset", "scan.assets"))
    ev(p1["scan"].get("evidence"), "scan.evidence")
    for key in ("rq", "gap"):
        node = p1[key]
        for i, r in enumerate(node.get("read", [])):
            out.append((r["sec"], "sec", f"{key}.read[{i}]"))
        ev(node.get("evidence"), f"{key}.evidence")

    met = study["phase2"]["method"]
    for i, r in enumerate(met.get("read", [])):
        out.append((r["sec"], "sec", f"method.read[{i}]"))
    for i, q in enumerate(met.get("guide_questions", [])):
        out.append((q["ref"], "ref", f"method.gq[{i}]"))
    ev(met.get("evidence"), "method.evidence")

    conc = study["phase2"]["conclusion"]
    for i, r in enumerate(conc.get("read", [])):
        out.append((r["sec"], "sec", f"conclusion.read[{i}]"))
    for a in conc.get("result_assets", []):
        out.append((a, "asset", "conclusion.result_assets"))
    ev(conc.get("evidence"), "conclusion.evidence")

    ver = study["phase3"]["verdict"]
    for i, r in enumerate(ver.get("read", [])):
        out.append((r["sec"], "sec", f"verdict.read[{i}]"))
    for i, c in enumerate(ver.get("author_claims", [])):
        ev(c.get("evidence"), f"verdict.claims[{i}]")

    alt = study["phase3"]["alternatives"]
    for i, r in enumerate(alt.get("read", [])):
        out.append((r["sec"], "sec", f"alt.read[{i}]"))
    for i, c in enumerate(alt.get("claude_items", [])):
        ev(c.get("evidence"), f"alt.items[{i}]")
    return out


def check_caption_language(paper: Path):
    """Paper Study 논문(captions_en 존재)에서 config#captions(번역/KR)가 순수 영문이면 FAIL -
    도표 뷰어의 '번역' 자리에 원문이 그대로 노출되는 버그 (정본 사례: 21. lv_pruning, 2026-07-08)."""
    cfg = json.loads((paper / "config.json").read_text(encoding="utf-8-sig"))
    if "captions_en" not in cfg:  # Paper Study 미적용 논문은 대상 아님
        return []
    caps = cfg.get("captions", {})
    bad = []
    for aid, txt in caps.items():
        s = str(txt)
        hangul = len(re.findall(r"[가-힣]", s))
        ascii_alpha = len(re.findall(r"[A-Za-z]", s))
        if len(s.strip()) >= 15 and hangul <= 2 and ascii_alpha >= 12:  # 한글 거의 없음 = 미번역
            bad.append(aid)
    return bad


REPO = Path(__file__).resolve().parent.parent


def all_folders():
    """papers/* + samples/* 중 산출물 HTML 이 있는 폴더 - 빈 배포본에서도 정본 samples/cares 를 검사한다."""
    out = []
    for base in ("papers", "samples"):
        b = REPO / base
        if b.is_dir():
            out += [d for d in sorted(b.iterdir()) if d.is_dir() and list(d.glob("*_output.html"))]
    return out


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "--all":
        fails = 0
        for d in all_folders():
            try:
                check_one(d)
            except SystemExit as e:
                if e.code not in (None, 0):
                    print(e.code)
                    fails += 1
        if fails:
            raise SystemExit(f"[FAIL] {fails}편")
        return
    check_one(Path(sys.argv[1]))


def check_one(paper: Path):
    study_path = paper / "tabs_data" / "study.json"
    if not study_path.exists():
        # study.json은 기본 빌드 필수 (CLAUDE.md § 기본 빌드 범위) - 빌더의 자동 셸은 '작성 전' 상태일 뿐
        raise SystemExit(f"[FAIL] {paper.name}: tabs_data/study.json 없음 - Stage 11(prompts/11_paper_study.md) 미완")
    sec, para, sent, assets = collect_ids(paper)
    cap_bad = check_caption_language(paper)
    study = json.loads(study_path.read_text(encoding="utf-8"))
    bad = []
    for ref, hint, path in walk_refs(study):
        if hint == "sec":
            if ref not in sec:
                bad.append((path, ref, f"section_id 없음 (있는 것: {sorted(sec)})"))
        elif hint == "asset":
            if ref not in assets:
                bad.append((path, ref, f"asset 없음 (있는 것: {sorted(assets)})"))
        else:  # ref: sentence/section/paragraph/asset 아무거나 허용
            if ref not in sent and ref not in sec and ref not in para and ref not in assets:
                bad.append((path, ref, "sentence/section/paragraph/asset 어디에도 없음"))
    for aid in cap_bad:
        print(f"  [FAIL] config#captions[{aid!r}] 순수 영문 - 뷰어 '번역'에 원문 노출. 한국어 번역 필요 (원문은 captions_en)")
    if bad:
        for path, ref, msg in bad:
            print(f"  [FAIL] {path}: {ref!r} - {msg}")
    if bad or cap_bad:
        raise SystemExit(f"\n[FAIL] {paper.name}: ref {len(bad)}건 + 미번역 캡션 {len(cap_bad)}건")
    print(f"[ok] {paper.name}: 모든 ref 실존 (문장 {len(sent)} · 섹션 {len(sec)} · 문단 {len(para)} · 자산 {len(assets)}) · 캡션 KR ok")


if __name__ == "__main__":
    main()
