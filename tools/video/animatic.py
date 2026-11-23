# -*- coding: utf-8 -*-
"""기획안.md + spec.py + scenes.js → 애니매틱 HTML(재생 가능한 컷 화면 + 장별 컷 목록).

python tools/video/animatic.py "papers/N. name"
  → video/기획안.html        (단독 실행 미리보기, 파일 하나)
  → video/work/build/index.html  (렌더용 같은 페이지, ?clean=1&nosub=1 로 1920×1080 화면만)
  → video/work/subs.json     (자막용 표시 문장·장 시각; 음성 타임라인이 있을 때만)
work/timeline.json(TTS 결과)이 있으면 실제 음성 길이로 컷 시각을 정하고, 없으면 글자 수로 추정한다.
"""
import base64, io, json, re, sys
from pathlib import Path
from types import SimpleNamespace
import fitz
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Paper, TOOLS, parse_script, sentences

CPS_N, CPS_Q = 5.0, 4.6        # 음성이 없을 때의 추정 속도(공백 제외 자/초)
PAD = 0.7


def b64(im, fmt="JPEG", q=86):
    buf = io.BytesIO()
    if fmt == "JPEG": im.convert("RGB").save(buf, "JPEG", quality=q, optimize=True)
    else: im.save(buf, "PNG", optimize=True)
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(buf.getvalue()).decode()


def toolkit(P):
    """spec.images()에 넘기는 도구: PDF 내장 이미지(xref), 자산 크롭 영역을 400 DPI로 다시 렌더."""
    doc = fitz.open(P.need_pdf()); HI, LO = 400 / 72, 200 / 72
    specs = {}
    if (P.dir / "_crop.py").exists():
        from common import load
        try: specs = {a: (p, x, y0, y1) for a, p, x, y0, y1 in load(P.dir / "_crop.py", "paper_crop").SPECS}
        except Exception: specs = {}   # 빌더마다 _crop.py 형식이 달라 좌표를 못 읽으면 자산 PNG로 대신한다(crop 참고)

    def embedded(xref):
        pix = fitz.Pixmap(doc, xref)
        if pix.alpha: pix = fitz.Pixmap(pix, 0)
        if pix.n > 3: pix = fitz.Pixmap(fitz.csRGB, pix)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    def crop(name, box):
        """box는 200 DPI 자산 PNG(assets/name.png) 기준 좌표. 같은 영역을 PDF에서 400 DPI로 렌더해 자른다."""
        sp = specs.get(name)
        if not sp or not all(isinstance(v, (int, float)) for v in (sp[2], sp[3])):
            # _crop.py가 좌표 대신 캡션 라벨로 영역을 정하거나 _crop.py가 없는 논문(킷 autocrop_assets.py): 200 DPI 자산 PNG를 그대로 자른다
            return Image.open(P.dir / "assets" / f"{name}.png").convert("RGB").crop(box)
        pno, (x0, x1), y0, y1 = sp
        clip = fitz.Rect(x0 + box[0] / LO, y0 + box[1] / LO, x0 + box[2] / LO, y0 + box[3] / LO)
        pix = doc[pno].get_pixmap(matrix=fitz.Matrix(HI, HI), clip=clip)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    return SimpleNamespace(b64=b64, crop=crop, embedded=embedded, Image=Image, doc=doc, video_dir=P.video, paper_dir=P.dir)


def _norm(s): return re.sub(r"[^0-9a-z]", "", s.lower())


def locate_quote(doc, text, K=40):
    """영어 원문 문장의 PDF 위치 → (0부터 센 쪽, 줄마다 [x0, y0, x1, y1] pt). 하이픈 줄바꿈·수식 기호는 영숫자만 비교해 넘긴다.
    전체 일치 → 앞 K자 + 뒤 K자 일치(가운데 수식) → 앞부분만 일치(쪽이 넘어가는 문장) 순서로 찾는다."""
    target = _norm(text)
    for pno, page in enumerate(doc):
        ws = page.get_text("words"); owner = []
        for i, w in enumerate(ws): owner += [i] * len(_norm(w[4]))
        S = "".join(_norm(w[4]) for w in ws)
        a = S.find(target); b = a + len(target)
        if a < 0:
            a = S.find(target[:K])
            if a < 0: continue
            pb = S.find(target[-K:], a)
            if pb >= 0 and pb + K - a <= len(target) * 1.5 + 20: b = pb + K
            else:
                L = 0
                while a + L < len(S) and L < len(target) and S[a + L] == target[L]: L += 1
                b = a + L
        lines = []
        for w in ws[owner[a]:owner[b - 1] + 1]:               # 같은 높이의 단어를 한 줄로 묶는다
            yc = (w[1] + w[3]) / 2; ln = next((l for l in lines if abs(l["yc"] - yc) < 4), None)
            if ln is None: lines.append({"yc": yc, "r": list(w[:4])})
            else: r = ln["r"]; ln["r"] = [min(r[0], w[0]), min(r[1], w[1]), max(r[2], w[2]), max(r[3], w[3])]
        return pno, [tuple(round(v) for v in l["r"]) for l in lines]
    return None


def quote_specs(P, spec):
    """spec.QUOTES(수동 좌표)에 없는 인용 컷의 출처 문장은 원문에서 자동으로 찾는다."""
    quotes = dict(getattr(spec, "QUOTES", {}) or {})
    man = P.dir / "translations" / "manual.json"
    orig = {s["sentence_id"]: s["original"] for s in json.loads(man.read_text(encoding="utf-8"))["sentences"]} if man.exists() else {}
    doc = fitz.open(P.need_pdf())
    for ch in parse_script(P.script.read_text(encoding="utf-8")):
        for c in ch["cuts"]:
            if c["sp"] != "Q": continue
            for sid in [x.strip() for x in c["src"].split(",")]:
                if sid in quotes or sid not in orig: continue
                hit = locate_quote(doc, orig[sid])
                if hit: quotes[sid] = hit
                else: print(f"  인용 위치를 찾지 못함: {c['id']} {sid} (spec.QUOTES에 직접 적는다)")
    return quotes


def pdf_quotes(P, quotes):
    doc = fitz.open(P.need_pdf()); out = {}
    for sid, (pg, rects) in quotes.items():
        y0 = min(r[1] for r in rects) - 70; y1 = max(r[3] for r in rects) + 70
        w = doc[pg].rect
        clip = fitz.Rect(96, max(0, y0), min(w.width, 516), min(w.height, y1))
        pix = doc[pg].get_pixmap(matrix=fitz.Matrix(3, 3), clip=clip)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        hl = [[(r[0] - clip.x0) / clip.width, (r[1] - clip.y0) / clip.height, (r[2] - clip.x0) / clip.width, (r[3] - clip.y0) / clip.height] for r in rects]
        out[sid] = {"img": b64(im, q=88), "hl": hl, "page": pg + 1}
    return out


def disp_factory(spec):
    names, terms = getattr(spec, "NAMES", []), getattr(spec, "TERMS", [])

    def disp(text, seen):
        for a, b in names: text = text.replace(a, b)
        for ko, en in terms:
            i = text.find(ko)
            if i < 0 or ko in seen: continue
            seen.add(ko); text = text[:i] + f"{en}({ko})" + text[i + len(ko):]
        return text
    return disp


def build(P):
    spec = P.spec(); disp = disp_factory(spec)
    chapters = parse_script(P.script.read_text(encoding="utf-8"))
    t = 0.0
    for ch in chapters:                       # 추정 시각
        ch["t0"] = t
        for c in ch["cuts"]:
            n = len(re.sub(r"\s", "", c["say"]))
            d = 4.5 if c["sp"] == "—" else n / (CPS_Q if c["sp"] == "Q" else CPS_N) + PAD + (0.8 if c["sp"] == "Q" else 0)
            c["t0"], c["dur"], c["chars"] = round(t, 2), round(d, 2), n; t += d
        ch["t1"] = t
    total = t
    tlf = P.work / "timeline.json"; real = tlf.exists()
    if real:                                  # 실제 음성 길이로 덮어쓴다
        tl = json.loads(tlf.read_text(encoding="utf-8")); T = {c["id"]: c for c in tl["cuts"]}
        for ch in chapters:
            for c in ch["cuts"]:
                c["t0"], c["dur"], c["sents"] = T[c["id"]]["t0"], T[c["id"]]["dur"], T[c["id"]]["sents"]
            ch["t0"], ch["t1"] = ch["cuts"][0]["t0"], ch["cuts"][-1]["t0"] + ch["cuts"][-1]["dur"]
        chapters[0]["t0"] = 0.0; total = tl["total"]
    for ch in chapters:                       # 장마다 전문용어 첫 등장만 "English(한국어)", 인용(Q)은 번역본 그대로
        seen = set()
        for c in ch["cuts"]:
            if c["sp"] == "Q":                # 인용: 용어 풀이는 붙이지 않고, TTS 읽기("브이엘엠")만 spec.NAMES로 번역본 표기("VLM")로 되돌린다
                for x in c.get("sents") or []: x["text"] = disp(x["text"], {ko for ko, _ in getattr(spec, "TERMS", [])})
                if c.get("sents"): c["say"] = " ".join(x["text"] for x in c["sents"])
                continue
            if c.get("sents"):
                for x in c["sents"]: x["text"] = disp(x["text"], seen)
                c["say"] = " ".join(x["text"] for x in c["sents"])
            else:
                c["say"] = " ".join(disp(x, seen) for x in sentences(c["say"]))
    arc, log = getattr(spec, "ARC", {}), getattr(spec, "LOGLINE", {})
    data = {
        "chapters": [{"label": c["label"], "title": c["title"], "t0": round(c["t0"], 2), "t1": round(c["t1"], 2),
                      "arc": arc.get(c["label"], ("hook", .5))[0], "h": arc.get(c["label"], ("hook", .5))[1],
                      "log": log.get(c["label"], "")} for c in chapters],
        "cuts": [dict(c, ch=i) for i, ch in enumerate(chapters) for c in ch["cuts"]],
        "total": round(total, 2),
    }
    nchar = sum(c["chars"] for c in data["cuts"])
    if real:
        (P.work / "subs.json").write_text(json.dumps(
            {"chapters": data["chapters"], "cuts": [{k: c.get(k) for k in ("id", "sp", "t0", "dur", "sents", "ch")} for c in data["cuts"]], "total": data["total"]},
            ensure_ascii=False, indent=1), encoding="utf-8")
    page = (TOOLS / "engine" / "player.html").read_text(encoding="utf-8")
    page = page.replace("/*__SCENES__*/", (P.video / "scenes.js").read_text(encoding="utf-8").rstrip("\n"))
    page = page.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False))
    page = page.replace("/*__IMGS__*/null", json.dumps(spec.images(toolkit(P))))
    page = page.replace("/*__QUOTES__*/null", json.dumps(pdf_quotes(P, quote_specs(P, spec))))
    pg = spec.PAGE
    for k, v in (("{{PAGE_TITLE}}", pg["title"]), ("{{EYEBROW}}", pg["eyebrow"]), ("{{H1}}", pg["h1"]), ("{{LEAD}}", pg["lead"]), ("{{NOTES}}", pg["notes_html"])):
        page = page.replace(k, v)
    page = page.replace("{{TOTAL}}", f"{int(total // 60)}:{int(total % 60):02d}").replace("{{NCH}}", str(len(chapters)))
    page = page.replace("{{NCHAR}}", f"{nchar:,}").replace("{{NCUTS}}", str(len(data["cuts"])))
    page = page.replace("{{NQUOTE}}", str(sum(1 for c in data["cuts"] if c["sp"] == "Q")))
    head = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')
    page = head + page.replace('<div class="wrap">', '</head>\n<body>\n<div class="wrap">', 1) + '\n</body>\n</html>\n'
    (P.video / "기획안.html").write_text(page, encoding="utf-8")
    P.build.mkdir(parents=True, exist_ok=True); (P.build / "index.html").write_text(page, encoding="utf-8")
    print("animatic", f"{len(page) / 1e6:.2f} MB", "total", f"{total:.0f}s", "(음성 기준)" if real else "(추정)", "chars", nchar, "cuts", len(data["cuts"]))
    return data


if __name__ == "__main__":
    build(Paper(sys.argv[1]))
