# -*- coding: utf-8 -*-
"""논문 영상 QC 게이트 (rules/video_rules.md 10절).

python tools/video/check_video.py "papers/N. name" [script|assets|final|all]   (기본 all: 있는 산출물까지 검사)
  script : 기획안.md 원고만 검사(TTS 전에 돌린다)
  assets : 예시 이미지(video/assets) 검사 - 사진 프롬프트(codex 호출 전), sources.json, "예시 사진" 표기, 도형 대체 의심
  final  : 음성 타임라인·최종 mp4 측정값까지 검사
FAIL이 하나라도 있으면 종료 코드 1.
"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Paper, ROOT, LEN_MIN, LEN_MAX, FPS, parse_script, sentences, load

CPS_N, CPS_Q, PAD = 5.6, 5.0, 0.6          # 추정 속도(모체 사례 실측: 3,768자 → 12:02)
_HK = r"에이치\s*(?:원|투|쓰리|포|일|이|삼|사|\d)"            # 원고는 TTS 읽기로 쓰므로 "H1"이 "에이치원"으로 적힌다
FORBID = [r"가설\s*H\d", r"\bH\d\s*가설", rf"가설\s*{_HK}", rf"{_HK}\s*가설", r"우리\s*연구", r"시사점", r"저희\s*연구실"]   # 사용자 자신의 연구 가설·시사점 금지.
# "H2" 같은 기호 단독은 막지 않는다(분야 일반: 화학식·가설 번호를 구분할 수 없다)
MAX_NUM_PER_CUT = 2                         # 학부생 눈높이: 컷당 말로 읽는 숫자 2개 이하


class R:
    def __init__(self): self.rows = []
    def add(self, lv, gate, msg): self.rows.append((lv, gate, msg))
    def fail(self, g, m): self.add("FAIL", g, m)
    def warn(self, g, m): self.add("WARN", g, m)
    def ok(self, g, m): self.add("OK", g, m)


def spoken_numbers(s):
    """말로 읽는 숫자 덩어리: 아라비아 숫자, 그리고 '일점오'·'삼백삼십육'·'이천이십육' 같은 한자어 수 읽기(2글자 이상).
    한자어 수 뒤에는 단위·조사가 붙을 수 있다('칠십팔퍼센트', '오백칠십육개', '삼백이')."""
    n = len(re.findall(r"\d+(?:[.,]\d+)*", s))
    for m in re.finditer(r"(?<![가-힣\d])[영일이삼사오육칠팔구십백천만억점]{2,}", s):
        run, after = m.group(0), s[m.end():]
        if run == "이점이": continue                                   # "이점이 있다"(장점)
        if not _SINO.fullmatch(run) and run[-1] in "이" and _SINO.fullmatch(run[:-1]): run, after = run[:-1], "이"
        if _SINO.fullmatch(run) and (not after or not re.match(r"[가-힣]", after) or re.match(_UNIT, after)): n += 1
    return n


_D = "[일이삼사오육칠팔구]"
_G4 = rf"(?:{_D}?천)?(?:{_D}?백)?(?:{_D}?십)?{_D}?"
_INT = rf"(?:{_G4}억)?(?:{_G4}만)?{_G4}"
# 정수는 자리 글자(십·백·천·만·억)가 있어야 한다("이", "삼" 한 글자나 "일이"는 수로 세지 않는다). 소수는 "일점오"·"영점구"
_SINO = re.compile(rf"(?=.*[십백천만억]){_INT}|(?:{_INT}|영)점[영일이삼사오육칠팔구]+")
_UNIT = r"퍼센트|프로|배|개|픽셀|번|초|분|시간|장|층|단계|년|명|점|위|차원|토큰|은|는|이|가|을|를|의|에|과|와|으로|로|까지|부터|도"


def check_script(P, r):
    text = P.script.read_text(encoding="utf-8"); chs = parse_script(text)
    cuts = [c for ch in chs for c in ch["cuts"]]
    if not cuts: r.fail("G0 원고", "기획안.md에서 컷 표를 읽지 못했다(### 장 · 제목 + | cNN | N | 말 | 출처 | 형식)"); return
    if "TODO_PAPER" in text: r.fail("G0 원고", "TODO_PAPER가 남아 있다")
    ids = [c["id"] for c in cuts]
    if len(ids) != len(set(ids)): r.fail("G0 원고", "컷 id 중복")
    # G1 출처
    nosrc = [c["id"] for c in cuts if c["sp"] != "—" and not c["src"].strip()]
    (r.fail if nosrc else r.ok)("G1 출처", f"출처 없는 컷 {nosrc}" if nosrc else f"{len(cuts)}컷 모두 출처 칸 있음")
    # G2 길이(추정)
    est = sum((4.5 if c["sp"] == "—" else len(re.sub(r"\s", "", c["say"])) / (CPS_Q if c["sp"] == "Q" else CPS_N) + PAD) for c in cuts) + 0.9 * (len(chs) - 1)
    lv = r.ok if LEN_MIN <= est <= LEN_MAX else r.fail
    lv("G2 길이", f"원고 추정 {est / 60:.1f}분 (기준 {LEN_MIN // 60}~{LEN_MAX // 60}분, 공백 제외 {sum(len(re.sub(chr(32), '', c['say'])) for c in cuts):,}자)")
    # G3 구조: 프롤로그 · 장 · 에필로그, 장 수
    labels = [ch["label"] for ch in chs]
    if labels[0] != "프롤로그" or labels[-1] != "에필로그": r.fail("G3 구조", f"첫 장은 프롤로그, 마지막은 에필로그여야 한다: {labels[0]} … {labels[-1]}")
    else: r.ok("G3 구조", f"장 {len(chs) - 2}개 + 프롤로그·에필로그")
    if not (6 <= len(chs) - 2 <= 10): r.warn("G3 구조", f"본 장 수 {len(chs) - 2} (권장 6~9)")
    q = [c for c in cuts if c["sp"] == "Q"]
    if not (3 <= len(q) <= 9): r.warn("G3 구조", f"저자 인용 {len(q)}개 (권장 4~8)")
    last = chs[-1]["cuts"][-1]["say"]
    if not re.search(r"학습 페이지|탭|HTML", last): r.warn("G3 구조", "마지막 컷이 학습 HTML 길잡이가 아니다")
    # G4 금지어(가설·시사점) + 문체
    tl = load(ROOT / "tools" / "tone_lint.py", "tone_lint")
    bad, tone = [], []
    for c in cuts:
        for rx in FORBID:
            if re.search(rx, c["say"]): bad.append(f"{c['id']}:{rx}")
        if c["sp"] == "N":
            tone += [f"{c['id']}:{h[1]}" for h in tl.scan_text(c["say"])]
            if "!" in c["say"]: tone.append(f"{c['id']}:느낌표")
    (r.fail if bad else r.ok)("G4 금지", f"사용자 연구 가설·시사점 표현 {bad}" if bad else "사용자 연구 가설·시사점 없음")
    (r.fail if tone else r.ok)("G4 문체", f"tone_lint {tone}" if tone else "감성 수사 없음(tone_lint)")
    # G5 인용 = 번역본 문장
    man = P.dir / "translations" / "manual.json"
    if man.exists():
        tr = {s["sentence_id"]: s.get("translation", "") for s in json.loads(man.read_text(encoding="utf-8"))["sentences"]}
        norm = lambda s: re.sub(r"[\s\"'“”‘’.,?]", "", s)
        miss = []
        def shown(s):                                                # 자막과 같게: TTS 읽기("브이엘엠")를 spec.NAMES로 번역본 표기("VLM")로
            for a, b in getattr(P.spec(), "NAMES", []): s = s.replace(a, b)
            return s
        for c in q:
            sids = [x.strip() for x in c["src"].split(",")]
            if not any(norm(shown(c["say"])) in norm(tr.get(s, "")) for s in sids): miss.append(c["id"])
        (r.warn if miss else r.ok)("G5 인용", f"번역본과 글자가 다른 인용 {miss} (TTS 읽기로 바꾼 표기면 무시)" if miss else f"인용 {len(q)}개 모두 번역본 문장")
    # G6 학부생 눈높이: 컷당 숫자, 식 풀이, 문장 길이
    names = [a for a, _ in getattr(P.spec(), "NAMES", [])]          # 모델·벤치마크 이름 속 숫자(엘라바 일점오 등)는 세지 않는다
    def nnum(s):
        for a in sorted(names, key=len, reverse=True): s = s.replace(a, " ")
        return spoken_numbers(s)
    many = [f"{c['id']}({nnum(c['say'])})" for c in cuts if c["sp"] == "N" and nnum(c["say"]) > MAX_NUM_PER_CUT]
    (r.warn if many else r.ok)("G6 눈높이", f"말로 읽는 숫자가 {MAX_NUM_PER_CUT}개를 넘는 컷 {many} (화면으로 옮길 것)" if many else "컷당 숫자 2개 이하")
    long_s = [c["id"] for c in cuts if c["sp"] == "N" for s in sentences(c["say"]) if len(s) > 95]
    if long_s: r.warn("G6 눈높이", f"95자 넘는 문장이 있는 컷 {sorted(set(long_s))}")
    if not any(re.search(r"이 식은|식 \d|식은", c["say"]) for c in cuts): r.warn("G6 눈높이", "핵심 식을 말로 푸는 컷이 없다(식 1개를 기호마다 읽고 '이 식은 ~라는 뜻'으로 닫는다)")
    eng = sorted({w for c in cuts if c["sp"] != "—" for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]+", c["say"])})
    eng_cuts = sorted({c["id"] for c in cuts if c["sp"] != "—" and re.search(r"[A-Za-z][A-Za-z0-9\-]+", c["say"])})
    if eng: r.warn("G7 읽기", f"원고에 영문이 남음 {eng_cuts}: {eng[:12]} - spec.READ_WORDS·tts 공통 표에 없는 영문이 남으면 tts가 멈춘다(한국어 읽기로 고치거나 READ_WORDS에 넣는다)")
    r.ok("G0 원고", f"{len(cuts)}컷 · 장 {len(chs)}개 · 인용 {len(q)}개")


IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
SRC_KINDS = ("paper", "codex", "dataset", "derived")   # rules/video_rules.md 2절 예시 이미지 우선순위 ①②③ + 그 크롭
EXAMPLE_KINDS = ("codex", "dataset")                    # 화면에 "예시 사진"을 달아야 하는 출처
SHAPE_HINT = r"실제 사진 아님|추상 장면|회색 톤|도형으로 (그린|대신)"          # 명세가 사진 자리를 도형으로 지시한 흔적(48 v1)
PHOTO_HINT = r"사진|입력 이미지|이미지 카드"


def check_photo_prompt(f):
    """영상 예시 사진 프롬프트(video/assets/prompt_*.txt). codex 6계명 + 사진 전용 항목. 반환 (fails, warns)."""
    try: t = f.read_text(encoding="utf-8")
    except UnicodeDecodeError: return [f"{f.name}: UTF-8이 아니다(6계명 ②)"], []
    fails, warns = [], []
    lines = [l.strip() for l in t.splitlines() if l.strip()]
    if "NOT a transparent cutout" not in t: fails.append(f"{f.name}: 'NOT a transparent cutout' 없음(6계명 ④ 풀 블리드)")
    if not re.search(r"\d{3,4}\s*[x×]\s*\d{3,4}", t): fails.append(f"{f.name}: 해상도(예: 1536x1024) 없음(6계명 ⑤)")
    if not re.search(r"저장 경로|save (it )?(to|as)|\.png", t, re.I): fails.append(f"{f.name}: 출력 경로 없음(6계명 ⑤)")
    if not lines or not lines[-1].startswith("NO paper title at top, NO standalone header, NO author names."):
        fails.append(f"{f.name}: 마지막 줄이 'NO paper title at top, NO standalone header, NO author names.'로 시작하지 않는다(6계명 ⑥)")
    if not re.search(r"사실적인 사진|photo", t, re.I): warns.append(f"{f.name}: 사진 스타일(사실적인 사진·자연광·초점) 명시 없음")
    if not re.search(r"(다른|그 밖의|외에는).{0,30}(글자|문자|텍스트|로고|브랜드)|no other (text|writing|logo)", t, re.I):
        warns.append(f"{f.name}: 사진 안 글자·로고·브랜드 통제 문구 없음(필요한 글자만 정확히 적고 나머지는 없다고 쓴다)")
    if not re.search(r"사람 없음|사람이 없|사람은 없|no (people|person|humans?)", t, re.I): warns.append(f"{f.name}: '사람 없음' 명시 없음(실존 인물·얼굴 금지)")
    if re.search(r"확대|zoom|crop", t, re.I) and not re.search(r"\d+\s*%", t):
        warns.append(f"{f.name}: 확대할 대상의 위치·크기를 사진 대비 %로 적지 않았다(원래 크기에서 작고 확대하면 읽혀야 한다)")
    return fails, warns


def check_assets(P, r):
    ad = P.video / "assets"
    imgs = sorted(p.name for p in ad.iterdir() if p.suffix.lower() in IMG_EXT) if ad.is_dir() else []
    prompts = sorted(ad.glob("prompt_*.txt")) if ad.is_dir() else []
    # G11 사진 프롬프트
    pf, pw = [], []
    for f in prompts:
        a, b = check_photo_prompt(f); pf += a; pw += b
    if prompts: (r.fail if pf else r.ok)("G11 사진 프롬프트", "; ".join(pf) if pf else f"{len(prompts)}개 6계명 통과")
    for w in pw: r.warn("G11 사진 프롬프트", w)
    # G12 출처 목록 sources.json
    texts = {f.name: f.read_text(encoding="utf-8") for f in sorted((P.video / "clips").glob("*.html"))} if (P.video / "clips").is_dir() else {}
    if (P.video / "scenes.js").exists(): texts["scenes.js"] = (P.video / "scenes.js").read_text(encoding="utf-8")
    mf = ad / "sources.json"
    if not imgs and not mf.exists(): r.ok("G12 예시 이미지", "video/assets에 이미지 없음")
    elif not mf.exists():
        r.warn("G12 예시 이미지", f"video/assets/sources.json 없음 - 이미지 {len(imgs)}장의 출처 종류(paper·codex·dataset·derived)를 적는다(2절)")
    else:
        try: src = json.loads(mf.read_text(encoding="utf-8"))
        except Exception as e: r.fail("G12 예시 이미지", f"sources.json을 읽지 못했다: {e}"); src = None
        if src is not None:
            bad = [f"목록에 없는 이미지 {n}" for n in imgs if n not in src]
            credits = (P.video / "CREDITS.md").read_text(encoding="utf-8") if (P.video / "CREDITS.md").exists() else ""
            for n, e in src.items():
                k = e.get("kind")
                if k not in SRC_KINDS: bad.append(f"{n}: kind '{k}'는 {SRC_KINDS} 중 하나여야 한다"); continue
                if not (ad / n).exists(): r.warn("G12 예시 이미지", f"{n}: 목록에 있지만 파일이 아직 없다(생성 전이면 무시)")
                if k == "paper" and not e.get("ref"): bad.append(f"{n}: paper는 ref(fig_N·table_N·쪽)가 필요하다")
                if k == "codex" and not (e.get("prompt") and (ad / e["prompt"]).exists()): bad.append(f"{n}: codex는 같은 폴더의 prompt 파일이 필요하다")
                if k == "dataset" and not (e.get("credit") and e["credit"] in credits): bad.append(f"{n}: dataset은 credit 문자열이 video/CREDITS.md에 있어야 한다")
                if k == "derived" and not (e.get("from") in src and e.get("how")): bad.append(f"{n}: derived는 목록 안의 from과 how(자른 좌표 등)가 필요하다")
            def root(n, seen=()):
                e = src.get(n, {})
                return root(e["from"], seen + (n,)) if e.get("kind") == "derived" and e.get("from") in src and e["from"] not in seen else e.get("kind")
            # "예시 사진" 표기: codex·dataset에서 나온 이미지를 쓰는 화면 파일
            ex = [n for n in src if root(n) in EXAMPLE_KINDS]
            nolabel = sorted({fn for fn, t in texts.items() for n in ex if n in t and "예시 사진" not in t})
            if nolabel: bad.append(f"예시 사진(codex·데이터셋)을 쓰는데 '예시 사진' 표기가 없는 파일 {nolabel}")
            (r.fail if bad else r.ok)("G12 예시 이미지", "; ".join(bad) if bad else f"이미지 {len(src)}장 출처 기록, 예시 사진 {len(ex)}장 표기 확인")
    # G12 도형 대체 의심: 명세가 사진을 말하는데 클립이 이미지를 쓰지 않음
    cs = P.clipspec(); sus = []
    for c in (getattr(cs, "CLIPS", []) if cs else []):
        spec_t = c.get("spec", ""); fn = f"{c['id']}-{c['name']}.html"
        if re.search(SHAPE_HINT, spec_t): sus.append(f"{fn}(명세가 도형 장면을 지시)")
        elif re.search(PHOTO_HINT, spec_t) and fn in texts and "assets/" not in texts[fn] and "<img" not in texts[fn]: sus.append(f"{fn}(명세에 사진이 있는데 이미지 참조 없음)")
    if sus: r.warn("G12 도형 대체", f"사진 자리를 도형으로 그렸을 수 있다: {sus} - 논문 자료 → codex 예시 사진 → 데이터셋 순서(2절)")


def check_final(P, r):
    tlf = P.work / "timeline.json"
    if not tlf.exists(): r.warn("G8 음성", "work/timeline.json 없음(TTS 전)"); return
    T = P.timeline()["total"]
    (r.ok if LEN_MIN <= T <= LEN_MAX else r.fail)("G8 길이", f"실제 음성 길이 {int(T // 60)}:{int(T % 60):02d} (기준 10:00~15:00)")
    spec = P.spec()
    if getattr(spec, "CREDITS", None) and not (P.video / "CREDITS.md").exists(): r.fail("G9 출처", "spec.CREDITS가 있는데 video/CREDITS.md가 없다")
    clips = P.clips()
    if clips:
        cover = sum(c["dur"] for c in clips) / T
        r.ok("G9 클립", f"motion 클립 {len(clips)}개, 영상의 {cover:.0%}")
    fj = P.work / "final.json"
    if not fj.exists() or not P.out.exists(): r.warn("G10 최종", f"{P.out.name} 없음(합성 전)"); return
    f = json.loads(fj.read_text(encoding="utf-8"))
    (r.ok if f["frames"] == f["expected"] else r.fail)("G10 프레임", f"영상 프레임 {f['frames']} / 기대 {f['expected']} (음성과 어긋남 없음)" if f["frames"] == f["expected"] else f"영상 프레임 {f['frames']} ≠ 기대 {f['expected']}")
    (r.ok if abs(f["lufs"] + 16) <= 1.0 and f["tp"] <= -1.0 else r.fail)("G10 음량", f"{f['lufs']} LUFS, TP {f['tp']} (기준 -16±1, TP ≤ -1)")
    if P.out.stat().st_mtime < max(x.stat().st_mtime for x in [P.script, P.video / "scenes.js", P.video / "spec.py"]):
        r.warn("G10 최종", "원고·장면·명세가 최종 영상보다 새것이다(다시 합성 필요)")


def main():
    if len(sys.argv) < 2 or sys.argv[2:3] and sys.argv[2] not in ("script", "assets", "final", "all"): raise SystemExit(__doc__)
    P = Paper(sys.argv[1]); mode = sys.argv[2] if len(sys.argv) > 2 else "all"; r = R()
    if mode in ("script", "all"): check_script(P, r)
    if mode in ("assets", "all"): check_assets(P, r)
    if mode in ("final", "all"): check_final(P, r)
    for lv, g, m in r.rows: print(f"[{lv}] {g}: {m}")
    nf = sum(1 for x in r.rows if x[0] == "FAIL")
    print(f"\n{P.dir.name}: FAIL {nf} · WARN {sum(1 for x in r.rows if x[0] == 'WARN')}")
    sys.exit(1 if nf else 0)


if __name__ == "__main__":
    main()
