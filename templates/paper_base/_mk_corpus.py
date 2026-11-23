# -*- coding: utf-8 -*-
r"""
structured.json + translations/manual.json + labels.json 동시 생성기.

⚠ 배포본의 Stage 2 정본은 tools/structure_paper.py 다(결정적 · web↔CLI 동일). 이 파일은 선택 도구다 -
  structure_paper.py 산출을 그대로 옮겨 적고 run-in 소제목·display 수식·번역을 한 파일에서 손볼 때만 쓴다.
  문장을 합치거나 빼지 않는다(CLAUDE.md § Stage 2 완전성). 번역·근거 칩이 붙은 뒤에는 sentence_id 를 바꾸지 않는다.

TODO_PAPER_제목 (학회 연도 · 소속).
범위: TODO_PAPER_포함_범위 (부록은 인용하면 포함한다).

문장은 (영문, 번역) 쌍으로 쓴다. 수식 등 추가 필드는 세 번째 값 dict로 넘긴다.
run-in 소제목("Label Assignment. ..." 처럼 문단 첫 문장에 붙은 제목)은 RUNIN에 적으면
labels.json으로 나가고 _build.py가 소제목으로 올린다. 번역문도 같은 영문 라벨로 시작하게 쓴다.
tex 안의 부등호는 rules/math_rules.md 규약대로 \lt / \gt 로 쓴다.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent

# run-in 소제목: pid -> (영문 라벨, 한국어 병기)
RUNIN = {}

SECTIONS = [
("s_abs", "Abstract", [
 ("p_abs_1", "", [
  ("TODO_PAPER_영문_문장", "TODO_PAPER_번역_문장"),
 ]),
]),
]


def main():
    sections, sentences = [], []
    for sid, title, paras in SECTIONS:
        out_paras = []
        for para in paras:
            pid, subtitle, pairs = para[0], para[1], para[2]
            extra = para[3] if len(para) > 3 else {}
            sents = []
            for i, item in enumerate(pairs, 1):
                en, ko = item[0], item[1]
                opts = item[2] if len(item) > 2 else {}
                s_id = f"{pid}_s{i}"
                node = {"sentence_id": s_id, "text": en}
                node.update(opts)
                sents.append(node)
                sentences.append({"sentence_id": s_id, "original": en, "translation": ko})
            p = {"paragraph_id": pid, "sentences": sents}
            if subtitle:
                p["section_subtitle"] = subtitle
            p.update(extra)
            out_paras.append(p)
        sections.append({"section_id": sid, "title": title, "paragraphs": out_paras})

    structured = {
        "paper_id": "TODO_PAPER_id",
        "title": "TODO_PAPER_제목",
        "venue": "TODO_PAPER_학회",
        "sections": sections,
    }
    (ROOT / "structured.json").write_text(
        json.dumps(structured, ensure_ascii=False, indent=1), encoding="utf-8")

    tr_dir = ROOT / "translations"
    tr_dir.mkdir(exist_ok=True)
    (tr_dir / "manual.json").write_text(
        json.dumps({"paper_id": "TODO_PAPER_id", "sentences": sentences},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    labels = {}
    for pid, (en, ko) in RUNIN.items():
        labels[pid] = {"label": f"{en} · {ko}", "strip": r"^" + __import__("re").escape(en) + r"\.\s*"}
    (ROOT / "labels.json").write_text(json.dumps(labels, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"sections={len(sections)}  paragraphs={sum(len(s['paragraphs']) for s in sections)}"
          f"  sentences={len(sentences)}  runin={len(labels)}")


if __name__ == "__main__":
    main()
