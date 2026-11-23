# -*- coding: utf-8 -*-
"""최종 합성: 기본 화면 구간 + motion 클립 → 정확한 프레임 수로 이어 붙이기 → ASS 자막 → 내레이션(2-pass loudnorm -16 LUFS).

python tools/video/finish.py "papers/N. name" ass     → work/subs.ass
python tools/video/finish.py "papers/N. name" final   → papers/N. name/{ShortName}_video.mp4, work/final.json(측정값)
"""
import json, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Paper, FF, FPS, FONTS
import base_render

# 자막 글꼴: Noto Sans KR 가변 글꼴의 기본 굵기는 Thin(100)이라 libass가 가장 얇게 그린다 → 700 고정 판(fonts/NotoSansKR-Sub700.ttf)
FONT = "Noto Sans KR Sub"
FONT_FILE = FONTS / "NotoSansKR-Sub700.ttf"
SUB_SIZE = 54
LINE_W = 1480            # 한 줄 최대 폭(px, 1920 화면). 한 자막은 최대 2줄
DISCLAIMER = "본 영상은 논문을 바탕으로 재구성한 영상입니다."


def _tokens(s, keep=()):
    """띄어쓰기 단위로 나누되 괄호 안과 keep의 구(용어 표기 "Base image(기본 이미지)", 이름 "Spot the Difference")는
    한 덩어리로 묶는다: 용어가 줄·자막 경계에서 갈리지 않게."""
    for k in sorted(keep, key=len, reverse=True):
        if " " in k: s = s.replace(k, k.replace(" ", " "))
    out, depth = [], 0
    for w in s.split(" "):
        if not w: continue
        w = w.replace(" ", " ")
        if depth > 0: out[-1] += " " + w
        else: out.append(w)
        depth += w.count("(") - w.count(")")
        depth = max(depth, 0)
    return out


def split_sub(text, keep=()):
    """문장 → 자막 묶음 [[줄1, 줄2?], …]. 각 줄 ≤ LINE_W, 묶음당 2줄 이하, 쉼표·연결어미 뒤에서 끊기를 선호, 줄 폭은 균형 있게."""
    from PIL import ImageFont
    font = ImageFont.truetype(str(FONT_FILE), SUB_SIZE)
    toks = _tokens(text, keep); n = len(toks)
    wid = lambda a, b: font.getlength(" ".join(toks[a:b]))
    # 끊으면 안 되는 자리: 관형어·수 표현 뒤("약 | 200개", "한 | 장"), 의존명사·보조용언 앞("공개할 | 수", "학습하지 | 않고")
    HEAD = ("약", "한", "두", "세", "네", "이", "그", "저", "각", "더", "잘", "안", "못", "총", "최대", "최소")
    hard = lambda i: 0 < i < n and (toks[i - 1] in HEAD or re.match(r"(수|것|않|못|때|등|만큼|뿐|중|개|장|번|배)(\s|$|[이을를은는가도의에으로과와만])", toks[i]) is not None
                                    or re.search(r"(할|을|는|은|한|지)$", toks[i - 1]) is not None and re.match(r"(수|것|않|때|만큼|뿐)", toks[i]) is not None)
    soft = lambda i: 0 < i < n and (toks[i - 1].endswith((",", "·")) or re.search(r"(고|며|면|서|지만|는데|니다\.|다\.)$", toks[i - 1]) is not None)

    def lines(a, b):                                   # 한 묶음을 1~2줄로: 가장 균형 잡힌 끊김
        if wid(a, b) <= LINE_W: return [(a, b)]
        best = None
        for k in range(a + 1, b):
            w1, w2 = wid(a, k), wid(k, b)
            if w1 > LINE_W or w2 > LINE_W: continue
            sc = max(w1, w2) - (90 if soft(k) else 0) + (400 if hard(k) else 0)
            if best is None or sc < best[0]: best = (sc, k)
        return None if best is None else [(a, best[1]), (best[1], b)]

    # 동적 계획: 묶음 수를 최소로, 같은 수면 묶음 폭이 고르고 쉼표·어미에서 끊긴 쪽
    INF = float("inf"); dp = [(INF, None)] * (n + 1); dp[0] = (0, None)
    for b in range(1, n + 1):
        for a in range(b):
            if dp[a][0] == INF or lines(a, b) is None: continue
            w = wid(a, b); sc = dp[a][0] + 10000 + (2 * LINE_W - w) ** 2 / 2000 - (120 if soft(a) else 0) + (3000 if hard(a) else 0)
            if sc < dp[b][0]: dp[b] = (sc, a)
    cuts, b = [], n
    while b > 0: a = dp[b][1]; cuts.append((a, b)); b = a
    return [[" ".join(toks[x:y]) for x, y in lines(a, b)] for a, b in reversed(cuts)]


def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def esc(s): return s.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def _bg(cat, a, b):
    """자막 자리(화면 아래 가운데) 뒤 배경: (평균 밝기 0~255, 복잡도 = 밝기 표준편차의 최댓값). 자막이 나오는 동안 세 시점을 본다."""
    mean, sd = [], []
    for f in (.2, .5, .8):
        r = subprocess.run([FF, "-loglevel", "error", "-ss", f"{max(a + (b - a) * f, 0):.2f}", "-i", str(cat), "-frames:v", "1",
                            "-vf", "crop=1320:170:300:870,scale=330:43,format=gray", "-f", "rawvideo", "-"], capture_output=True)
        px = r.stdout
        if not px: continue
        m = sum(px) / len(px); mean.append(m); sd.append((sum((x - m) ** 2 for x in px) / len(px)) ** .5)
    return (sum(mean) / len(mean), max(sd)) if mean else (255, 0)


BUSY = 22          # 이 이상이면 자막 뒤에 표·논문 그림·사진 같은 시각 자료가 깔린 것으로 본다
GRAD = r"{\an7\pos(0,0)\p1\bord0\shad0\1c&H000000&\1a&H62&\blur70\fad(300,300)}m -200 830 l 2120 830 2120 1300 -200 1300{\p0}"


def ass(P, cat=None):
    d = json.loads((P.work / "subs.json").read_text(encoding="utf-8")); T = d["total"]; spec = P.spec()
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{FONT},{SUB_SIZE},&H00FFFFFF,&H00FFFFFF,&H30181818,&H00000000,0,0,0,0,100,100,0,0,1,1.2,0,2,200,200,64,1
Style: SubD,{FONT},{SUB_SIZE},&H0033231F,&H0033231F,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,200,200,64,1
Style: Grad,{FONT},20,&H62000000,&H62000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: ChN,{FONT},32,&H001A70B5,&H001A70B5,&H00000000,&H00000000,0,0,0,0,100,100,3,0,1,0,0,7,77,0,62,1
Style: ChT,{FONT},68,&H0033231F,&H0033231F,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,77,0,112,1
Style: Cred,{FONT},22,&H4075625D,&H4075625D,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,1,42,0,26,1
Style: Disc,{FONT},24,&H4075625D,&H4075625D,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,3,0,42,22,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = [f"Dialogue: 0,{ts(0)},{ts(T)},Disc,,0,0,0,,{DISCLAIMER}"]
    cuts0 = {c["id"]: c for c in d["cuts"]}
    for text, a_id, b_id in getattr(spec, "CREDITS", []):     # 외부 자료 출처(사진 라이선스 등): 그 자료가 나오는 컷에 표기
        a0 = cuts0[a_id]["t0"]; b0 = cuts0[b_id]["t0"] + cuts0[b_id]["dur"]
        ev.append(f"Dialogue: 0,{ts(a0)},{ts(b0)},Cred,,0,0,0,,{text}")
    cuts = d["cuts"]; subs = []
    keep = [f"{en}({ko})" for ko, en in getattr(spec, "TERMS", [])] + [en for _, en in getattr(spec, "NAMES", [])] + [ko for ko, _ in getattr(spec, "TERMS", [])]
    for c in cuts:
        if c["sp"] == "—" or not c.get("sents"): continue
        end_cut = c["t0"] + c["dur"]
        for k, s in enumerate(c["sents"]):
            a = s["t0"] - .12; b = (c["sents"][k + 1]["t0"] - .12) if k + 1 < len(c["sents"]) else end_cut - .05
            groups = split_sub(s["text"], keep)              # 한 문장이 2줄을 넘으면 글자 수 비율로 시간을 나눠 여러 자막으로
            tot = sum(len("".join(g).replace(" ", "")) for g in groups); t = a
            for g in groups:
                dt = (b - a) * len("".join(g).replace(" ", "")) / tot
                txt = "\\N".join(esc(x) for x in g)
                if c["sp"] == "Q": txt = "{\\fs30}저자 · 논문 인용{\\r}\\N" + txt
                subs.append([t, t + dt, txt]); t += dt
    subs.sort(key=lambda x: x[0])
    for i in range(len(subs) - 1):                      # 문장 자막이 겹치지 않게
        subs[i][1] = min(subs[i][1], subs[i + 1][0] - 0.02)
    # 자막 장식(사용자 피드백 2026-11-19): 띠·그림자 없음.
    #  - 뒤에 표·논문·사진이 깔린 자막: 아래쪽 어두운 그라데이션 + 흰 글자(Sub)
    #  - 빈 밝은 화면: 진한 글자(SubD) / 빈 어두운 화면: 흰 글자(Sub)
    # 그라데이션은 이어지는 자막 구간을 하나로 합쳐 한 장만 그린다(겹쳐 그리면 겹친 곳만 진해지고 경계가 생긴다).
    bg = [_bg(cat, a, b) if cat else (0, 0) for a, b, _ in subs]
    busy = [sd >= BUSY for _, sd in bg]
    spans = []
    for (a, b, _), z in zip(subs, busy):
        if not z: continue
        if spans and a - spans[-1][1] < 0.8: spans[-1][1] = b
        else: spans.append([a, b])
    for a, b in spans:
        ev.append(f"Dialogue: 0,{ts(max(a - .15, 0))},{ts(b + .15)},Grad,,0,0,0,,{GRAD}")
    for (a, b, t), z, (m, _) in zip(subs, busy, bg):
        ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},{'Sub' if z or m <= 150 else 'SubD'},,0,0,0,,{t}")
    print("자막", len(subs), "· 그라데이션 구간", len(spans), "· 덮인 자막", sum(busy))
    for k, ch in enumerate(d["chapters"]):              # 장 제목: 프롤로그와 인용으로 시작하는 장은 생략
        if ch["label"] == "프롤로그": continue
        first = next(c for c in cuts if c["ch"] == k)
        if first["sp"] == "Q": continue
        a, b = ch["t0"], ch["t0"] + 4.2
        ev.append(f"Dialogue: 2,{ts(a)},{ts(b)},ChN,,0,0,0,,{{\\fad(600,600)}}{esc(ch['label'])}")
        if ch["title"] != ch["label"]:                 # "### 에필로그"처럼 제목 없는 장은 라벨만(같은 말 두 번 방지)
            ev.append(f"Dialogue: 2,{ts(a)},{ts(b)},ChT,,0,0,0,,{{\\fad(600,600)}}{esc(ch['title'])}")
    (P.work / "subs.ass").write_text(head + "\n".join(ev) + "\n", encoding="utf-8-sig")
    print("subs.ass", len(ev), "events")


def final(P):
    """1) 타임라인 순서의 [기본 화면 구간 | motion 클립]을 각각 정확한 프레임 수로 인코딩(경계 = round(시각×30), 짧으면 마지막 프레임 유지)
    2) concat demuxer로 이어 붙이기 3) 자막 입히기 + 내레이션. 구간이 많아도 영상과 음성이 어긋나지 않는다."""
    B = P.build
    missing = [k for k, _, _ in base_render.chunks(P) if not (B / f"part_{k:02d}.ok").exists()]
    if missing: raise SystemExit(f"기본 화면 구간이 덜 렌더됐다: {missing}")
    segs = [(s, str(B / f"part_{k:02d}.mp4")) for k, s, e in base_render.chunks(P)] + [(c["t0"], str(P.work / c["file"])) for c in P.clips()]
    segs.sort(); T = P.timeline()["total"]
    hold = segs[0][0] > 1e-3                           # 첫 컷이 클립이면 앞 무음(0.6초)은 기본 구간이 없다(모체 사례): 첫 프레임을 멈춰 채운다
    if hold:
        if segs[0][0] > 1.6: raise SystemExit("타임라인 0초에 시작하는 구간이 없다")
        segs.insert(0, (0.0, segs[0][1]))
    S = B / "segs"; S.mkdir(exist_ok=True); files = []
    for f in S.glob("seg_*.mp4"): f.unlink()
    for i, (s, f) in enumerate(segs):
        nxt = segs[i + 1][0] if i + 1 < len(segs) else T
        n = round(nxt * FPS) - round(s * FPS); o = S / f"seg_{i:02d}.mp4"
        pre = "trim=end_frame=1," if (hold and i == 0) else ""
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", f, "-vf", pre + "fps=30,scale=1920:1080,setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration=3",
                        "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", "-r", "30", str(o)], check=True)
        files.append(o)
    lst = S / "list.txt"; lst.write_text("\n".join(f"file '{x.as_posix()}'" for x in files) + "\n", encoding="utf-8")
    cat = B / "cat.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(cat)], check=True)
    ass(P, cat)                                        # 자막 색은 이어 붙인 화면의 밝기를 보고 고른다
    sub = (P.work / "subs.ass").as_posix().replace(":", r"\:")
    fdir = FONTS.as_posix().replace(":", r"\:")       # 저장소 글꼴(tools/video/fonts): 시스템에 Noto Sans KR이 없어도 같은 자막
    vf = f"subtitles=filename='{sub}':fontsdir='{fdir}'"
    nar = P.work / "narration.wav"
    r = subprocess.run([FF, "-hide_banner", "-i", str(nar), "-af", "loudnorm=I=-16:TP=-2.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    js = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"loudnorm=I=-16:TP=-2.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,aresample=48000")
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(cat), "-i", str(nar), "-vf", vf, "-af", af, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(P.out)], check=True)
    m = subprocess.run([FF, "-hide_banner", "-i", str(P.out), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    j2 = json.loads(m.stderr[m.stderr.rfind("{"):m.stderr.rfind("}") + 1])
    v = subprocess.run([FF, "-hide_banner", "-i", str(P.out), "-map", "0:v", "-c", "copy", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    fr = re.findall(r"frame=\s*(\d+)", v)
    res = {"out": str(P.out), "mb": round(P.out.stat().st_size / 1e6, 1), "lufs": float(j2["input_i"]), "tp": float(j2["input_tp"]),
           "frames": int(fr[-1]) if fr else None, "expected": round(T * FPS), "total": T}
    (P.work / "final.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("OUT", res)


if __name__ == "__main__":
    {"ass": ass, "final": final}[sys.argv[2]](Paper(sys.argv[1]))
