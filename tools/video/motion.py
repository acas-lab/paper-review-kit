# -*- coding: utf-8 -*-
"""motion-broll 클립: 단어 시각 → 클립 명세서(brief) → 빌드 → 정지 화면 점검 → 렌더.

python tools/video/motion.py "papers/N. name" words            → work/words.json (narration.wav 단어 시각, faster-whisper CPU int8)
python tools/video/motion.py "papers/N. name" briefs           → work/briefs/NN-name.md, work/clips.json (clipspec.CLIPS + 타임라인)
python tools/video/motion.py "papers/N. name" build            → work/dist/NN-name.html (+ dist/assets ← video/assets)
python tools/video/motion.py "papers/N. name" beats NN t1 t2 … → work/beats/NN.png (정지 화면 묶음, 직접 열어 본다)
python tools/video/motion.py "papers/N. name" render [budget=420] → work/out/NN-name.mp4 (길이가 맞는 클립은 건너뜀, 포그라운드로 반복 실행)
클립 조각(video/clips/NN-name.html)은 motion-broll 스킬 형식이고, 작성 규칙은 rules/video_rules.md 8절.
"""
import json, os, shutil, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Paper, SKILL, FF, FONTS, node_env, probe_dur

DEFAULT_STYLE = """\
- 밝은 팔레트(학습 HTML v4 계열, tools/video/theme.py LIGHT): canvas `#F3F2F7`, 카드 `#FFFFFF`(테두리 `#CFCCDC` 1.5px, 그림자 옅게),
  보조 면 `#ECEBF3`, 선 `#CFCCDC`, 글자 `#1F2333`, 보조 글자 `#464B5E`, 흐린 글자 `#5D6275`, 강조(하나) 진한 주황 `#B5701A`,
  보조 의미색: 배경(0) 파랑 `#3F67A8`, 잡음·하락 장미색 `#B0506A`, 통과 초록 `#2F8A63`. 면과 카드는 테두리로 구분한다(밝은 바탕에 밝은 카드만 두지 않는다).
- 글꼴: 한글은 `'Noto Sans KR'`(시스템 설치, 없으면 clips-build가 tools/video/fonts 글꼴을 넣는다), 숫자·영문은 Geist(엔진 내장). `font-family:'Geist','Noto Sans KR',sans-serif` 형태로 둔다. 코드·기호는 Geist Mono.
- 화면 하단 25%(y > 810)에는 나중에 자막이 입혀진다. 중요한 내용과 커서는 y 120~780 안에 둔다. 왼쪽 위 (60~600, 40~160)는 장 제목이 잠깐 뜨는 자리이니 장 첫 컷이면 첫 4초는 비워 둔다.
- 1920×1080, 30fps. 클립 길이 T는 아래 duration과 정확히 같게 한다(합성 시 그 구간을 통째로 덮는다).
- 숫자는 명세에 적힌 논문 값만 쓴다. 명세에 "예시"라고 된 것은 화면에도 작게 "예시"를 붙인다. 새 숫자·인용·결과를 만들지 않는다.
- 사진·입력 이미지 자리는 도형(회색 사각형·추상 물체)으로 그리지 않는다. 명세에 적힌 `assets/` 이미지를 `<img>`로 쓰고, codex·데이터셋 사진이면 화면에 작게 "예시 사진"을 단다. 명세에 사진이 필요한데 쓸 이미지가 없으면 직접 그리지 말고 리드에게 요청한다(rules/video_rules.md 2절). 이미지 위 좌표·상자는 `assets/sources.json`의 실제 픽셀 좌표에 맞춘다.
- 상태 변화는 해당 단어 시각(clip-local = 단어 시각 − 클립 시작)에 맞춘다. 한 변화 간격 0.4~1.2초.
- 금지(스킬 규칙): 튀는 easing, 파티클, 글로우, UI 크롬의 그라데이션, 템플릿 같은 모양, 지어낸 데이터."""


def words(P):
    from faster_whisper import WhisperModel      # GTX 1080 Ti는 float16 미지원, CUDA DLL 문제 → CPU int8
    m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=8)
    segs, _ = m.transcribe(str(P.work / "narration.wav"), language="ko", word_timestamps=True, vad_filter=False, beam_size=5)
    W = [{"w": w.word.strip(), "t0": round(w.start, 2), "t1": round(w.end, 2)} for s in segs for w in s.words]
    (P.work / "words.json").write_text(json.dumps(W, ensure_ascii=False), encoding="utf-8"); print(len(W), "words")


def briefs(P):
    cs_mod = P.clipspec()
    if cs_mod is None: raise SystemExit("video/clipspec.py가 없다")
    STYLE = getattr(cs_mod, "STYLE", DEFAULT_STYLE)
    subs = json.loads((P.work / "subs.json").read_text(encoding="utf-8")); W = json.loads((P.work / "words.json").read_text(encoding="utf-8"))
    cuts = {c["id"]: c for c in subs["cuts"]}; out = []; bd = P.work / "briefs"; bd.mkdir(exist_ok=True)
    rel = P.video.relative_to(P.dir.parents[1]).as_posix()
    for cl in cs_mod.CLIPS:
        cs = [cuts[i] for i in cl["cuts"]]; t0 = cs[0]["t0"]; t1 = cs[-1]["t0"] + cs[-1]["dur"]; T = round(t1 - t0, 3)
        lines = []
        for c in cs:
            lines.append(f"\n#### 컷 {c['id']}  (clip-local {c['t0'] - t0:.2f}~{c['t0'] + c['dur'] - t0:.2f}s)")
            for s in c["sents"]:
                ws = [w for w in W if s["t0"] - .05 <= w["t0"] < s["t1"] + .05]
                lines.append(f"- [{s['t0'] - t0:.2f}~{s['t1'] - t0:.2f}] {s['text']}")
                if ws: lines.append("  - 단어: " + " ".join(f"{w['w']}@{w['t0'] - t0:.2f}" for w in ws))
        name = f"{cl['id']}-{cl['name']}"
        md = f"""# 클립 {cl['id']} · {cl['name']}

- 덮는 컷: {', '.join(cl['cuts'])}
- 영상 타임라인 구간: {t0:.3f}s ~ {t1:.3f}s
- **duration T = {T}** (M.scene의 T에 정확히 이 값)
- 조각: `{rel}/clips/{name}.html` → `python tools/video/motion.py "{P.dir.name}" build` → `{rel}/work/dist/{name}.html`
- 점검: `python tools/video/motion.py "{P.dir.name}" beats {cl['id']} <초> <초> …` → `{rel}/work/beats/{cl['id']}.png`
- 이미지: `{rel}/assets/` 의 파일을 `assets/파일명`으로 참조한다(빌드 때 dist/assets로 복사됨)

## 무엇을 보여 주나
{cl['spec']}

## 스타일 규칙
{STYLE}

## 내레이션과 단어 시각 (clip-local 초, faster-whisper 추정 ±0.2s)
{''.join(l + chr(10) for l in lines)}"""
        (bd / f"{name}.md").write_text(md, encoding="utf-8")
        out.append({"id": cl["id"], "name": cl["name"], "file": f"out/{name}.mp4", "t0": round(t0, 3), "dur": T, "cuts": cl["cuts"]})
    out.sort(key=lambda c: c["t0"])
    for a, b in zip(out, out[1:]):
        if a["t0"] + a["dur"] > b["t0"] + 0.02: raise SystemExit(f"클립 구간이 겹친다: {a['id']} · {b['id']}")
    (P.work / "clips.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(out), "briefs, total clip seconds", round(sum(c["dur"] for c in out), 1))


def build(P, ids=None):
    dist = P.work / "dist"; dist.mkdir(exist_ok=True)
    if (P.video / "assets").exists(): shutil.copytree(P.video / "assets", dist / "assets", dirs_exist_ok=True)
    src = sorted((P.video / "clips").glob("*.html"))
    if ids: src = [s for s in src if s.name.split("-")[0] in ids]
    subprocess.run([sys.executable, str(SKILL / "engine" / "build.py"), str(dist)] + [str(s) for s in src], check=True)
    if not noto_installed():                    # 시스템에 Noto Sans KR이 없는 컴퓨터: 저장소 글꼴을 클립 HTML에 넣는다
        import base64
        face = "@font-face{font-family:'Noto Sans KR';font-weight:100 900;src:url(data:font/ttf;base64,%s) format('truetype')}" %                base64.b64encode((FONTS / "NotoSansKR-VF.ttf").read_bytes()).decode()
        for f in src:
            d = dist / f"{f.stem}.html"; d.write_text(d.read_text(encoding="utf-8").replace("<style>", "<style>" + face, 1), encoding="utf-8")
        print("Noto Sans KR 미설치 → tools/video/fonts 글꼴을 클립에 넣음")


def noto_installed():
    import glob
    dirs = [os.environ.get("WINDIR", "C:/Windows") + "/Fonts", os.environ.get("LOCALAPPDATA", "") + "/Microsoft/Windows/Fonts",
            os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "/usr/share/fonts", os.path.expanduser("~/.local/share/fonts")]
    return any(glob.glob(f"{d}/**/NotoSansKR*", recursive=True) for d in dirs if d and os.path.isdir(d))


def beats(P, cid, times):
    html = next((P.work / "dist").glob(f"{cid}-*.html")); out = P.work / "beats"; out.mkdir(exist_ok=True)
    subprocess.run(["node", str(SKILL / "engine" / "beats.js"), str(html), str(out / f"{cid}.png")] + times, cwd=P.work, env=node_env(), check=True)
    print(out / f"{cid}.png")


def render(P, budget=420):
    """한 편씩 순서대로 렌더한다. 백그라운드·다수 병렬은 메모리 부족으로 강제 종료되므로 포그라운드에서 budget초 단위로 반복 실행."""
    clips = P.clips(); t0 = time.time(); (P.work / "out").mkdir(exist_ok=True)
    ok = lambda c: (lambda d: d is not None and abs(d - c["dur"]) < 0.06)(probe_dur(P.work / c["file"]))
    left = [c for c in clips if not ok(c) and c["id"] not in os.environ.get("SKIP", "").split(",")]
    print(f"남은 클립 {len(left)}/{len(clips)}", flush=True)
    for c in left:
        if time.time() - t0 > budget: break
        out = P.work / c["file"]; html = P.work / "dist" / f"{c['id']}-{c['name']}.html"
        if out.exists(): out.unlink()
        s = time.time()
        r = subprocess.run(["node", str(SKILL / "engine" / "render.js"), str(html), str(out), "30"], cwd=P.work, env=node_env(),
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(f"{c['id']}-{c['name']} T={c['dur']} → {probe_dur(out)} {'완료' if ok(c) else '실패 ' + r.stderr[-300:]} ({time.time() - s:.0f}s)", flush=True)
    left2 = [c for c in clips if not ok(c)]
    print("ALL CLIPS DONE" if not left2 else f"남은 클립 {len(left2)}: " + ", ".join(c["id"] for c in left2), flush=True)
    return not left2


if __name__ == "__main__":
    P = Paper(sys.argv[1]); cmd = sys.argv[2]; rest = sys.argv[3:]
    if cmd == "words": words(P)
    elif cmd == "briefs": briefs(P)
    elif cmd == "build": build(P, rest or None)
    elif cmd == "beats": beats(P, rest[0], rest[1:])
    elif cmd == "render": render(P, float(rest[0]) if rest else 420)
    else: raise SystemExit(__doc__)
