# -*- coding: utf-8 -*-
"""논문 소개 영상 파이프라인 (Stage 13, rules/video_rules.md).

python tools/video/make_video.py "papers/N. name" <단계> [인자…]

  new                 video/ 뼈대를 templates/paper_base/video/에서 복사 (있는 파일은 덮지 않음)
  status              단계별 완료 여부와 다음 할 일
  check-script        원고 QC (G1~G7)
  check-assets        예시 이미지 QC (G11 사진 프롬프트 · G12 sources.json · "예시 사진" 표기 · 도형 대체 의심). codex 호출 전과 클립 작성 뒤
  tts                 내레이션 (tools/video/tts_env 파이썬으로 실행, 목소리는 tools/video/voices/ — rules/video_rules.md 6절)
  animatic            애니매틱 HTML + 자막 데이터
  words | briefs      motion 클립용 단어 시각 / 명세서
  clips-build [NN…]   클립 조각 → dist HTML
  beats NN t1 t2 …    클립 정지 화면 시트 → work/beats/NN.png
  clips-render [초]   클립 렌더 (포그라운드 반복 실행)
  base-render [동시=2] [초=420] [--redo]   기본 화면 구간 렌더 (반복 실행)
  final               합성 → {ShortName}_video.mp4
  check               전체 QC (원고 + 산출물)
  frames t1 t2 …      최종 영상의 그 시각 프레임 → work/frames/ (육안 점검)
  gapcheck            장 경계 틈 직전·직후 프레임 시트 → work/frames/gaps.jpg

python tools/video/make_video.py - doctor      새 컴퓨터 점검: 빠진 것과 채울 명령 (motion-broll 스킬이 없으면 이때 설치)
python tools/video/make_video.py - setup       파이썬 패키지·ffmpeg·node_modules·Chromium·motion-broll 스킬 설치(최초 1회)
python tools/video/make_video.py - setup-tts   TTS 환경 tools/video/tts_env (Python 3.12 venv, torch, qwen-tts) 설치(최초 1회)

자동 준비: 단계 명령을 실행하면 그 단계에 필요한 것이 없을 때 먼저 스스로 설치한다(ensure). Node.js·Python 3.12가 없으면
Windows는 winget, macOS는 brew로 설치한다. TTS 모델(Qwen3-TTS 0.6B)은 첫 tts 때 tools/video/tts_env/hf로 내려받는다.
motion-broll 스킬(클립 엔진)은 킷의 skills/motion-broll/을 프로젝트 스킬 폴더 .claude/skills/motion-broll/로 복사해 설치한다.
끄려면 환경변수 VIDEO_NO_AUTOSETUP=1.
"""
import json, os, shutil, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Paper, ROOT, TOOLS, TTS_PY, FF, EXE, probe_dur, install_skill, skill_state

TPL = ROOT / "templates" / "paper_base" / "video"


def setup():
    """새 컴퓨터 최초 1회: motion-broll 스킬, 호스트 파이썬 패키지, ffmpeg, node_modules(puppeteer-core, playwright + Chromium)."""
    install_skill(force=True)                  # 배포본(skills/motion-broll)과 다르면 덮어쓴다
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(TOOLS / "requirements.txt")], check=True)
    (TOOLS / "bin").mkdir(exist_ok=True)
    if not (TOOLS / "bin" / f"ffmpeg{EXE}").exists():
        import imageio_ffmpeg
        shutil.copy(imageio_ffmpeg.get_ffmpeg_exe(), TOOLS / "bin" / f"ffmpeg{EXE}")
    (TOOLS / "bin" / "python3").write_text('#!/usr/bin/env bash\nexec python "$@"\n')
    if not _node(): _pkg("OpenJS.NodeJS.LTS", "node"); _node()
    if not (TOOLS / "node_modules" / "puppeteer-core").exists() or not (TOOLS / "node_modules" / "playwright").exists():
        subprocess.run("npm install --no-save --prefix . puppeteer-core playwright", cwd=TOOLS, shell=True, check=True)
    subprocess.run("npx playwright install chromium", cwd=TOOLS, shell=True, check=True)
    print("setup ok:", TOOLS / "bin", TOOLS / "node_modules")


def _pkg(win_id, brew):
    """시스템 프로그램 설치: Windows winget / macOS brew. 실패하면 직접 설치할 주소를 알려 준다."""
    if os.name == "nt" and shutil.which("winget"):
        cmd = ["winget", "install", "-e", "--id", win_id, "--silent", "--accept-package-agreements", "--accept-source-agreements"]
    elif shutil.which("brew"): cmd = ["brew", "install", brew]
    else: raise SystemExit(f"{win_id} 를 자동 설치할 수 없다(winget/brew 없음). 직접 설치한 뒤 다시 실행한다.")
    print("설치:", " ".join(cmd), flush=True); subprocess.run(cmd)


def _node():
    if shutil.which("node"): return True
    for d in (os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "nodejs"), "/opt/homebrew/bin", "/usr/local/bin"):      # 방금 설치해 PATH에 아직 없을 때
        if (Path(d) / f"node{EXE}").exists(): os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]; return True
    return False


def _py312():
    if os.name == "nt" and shutil.which("py"):
        return subprocess.run(["py", "-3.12", "-c", "0"], capture_output=True).returncode == 0
    return bool(shutil.which("python3.12"))


def _torch_index():
    """GPU에 맞는 torch 휠: RTX 50xx(Blackwell)는 cu128, 그 밖의 NVIDIA는 cu126, GPU 없으면 cpu. TORCH_INDEX가 있으면 그것."""
    if os.environ.get("TORCH_INDEX"): return os.environ["TORCH_INDEX"]
    if not shutil.which("nvidia-smi"): return "https://download.pytorch.org/whl/cpu"
    name = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True).stdout
    return "https://download.pytorch.org/whl/" + ("cu128" if "RTX 50" in name or "Blackwell" in name else "cu126")


def ensure(cmd):
    """단계 명령 전에 필요한 환경을 확인하고 없으면 설치한다(새 컴퓨터에서 바로 돌아가게)."""
    if cmd in ("clips-build", "beats", "clips-render") and skill_state() == "missing":   # 로컬 복사라 VIDEO_NO_AUTOSETUP과 무관
        install_skill()
    if os.environ.get("VIDEO_NO_AUTOSETUP") or cmd in ("new", "status", "check-script", "check-assets"): return
    import importlib.util
    from common import find_chrome
    base_ok = all(importlib.util.find_spec(m) for m in ("fitz", "PIL", "numpy", "imageio_ffmpeg", "faster_whisper")) and (Path(FF).exists() or bool(shutil.which(FF)))
    web = cmd in ("animatic", "clips-build", "beats", "clips-render", "base-render", "final")
    web_ok = _node() and (TOOLS / "node_modules" / "playwright").exists() and (TOOLS / "node_modules" / "puppeteer-core").exists() and (
        bool(find_chrome()) or any((Path.home() / p).exists() for p in ("AppData/Local/ms-playwright", ".cache/ms-playwright", "Library/Caches/ms-playwright")))
    if web and not _node():
        _pkg("OpenJS.NodeJS.LTS", "node")
        if not _node(): raise SystemExit("Node.js 설치 후에도 node를 찾지 못했다. 터미널을 새로 열고 다시 실행한다.")
    if not base_ok or (web and not web_ok):
        print("[자동 준비] 영상 도구 설치(최초 1회)", flush=True); setup()
    if cmd == "tts" and not Path(TTS_PY).exists():
        print("[자동 준비] TTS 환경 설치(최초 1회, 수 GB)", flush=True); setup_tts()


def setup_tts():
    """TTS 환경 tools/video/tts_env: Python 3.12 venv + torch + qwen-tts. torch 휠은 환경변수 TORCH_INDEX로 바꾼다
    (기본 cu126: GTX 10xx~RTX 40xx. RTX 50xx는 https://download.pytorch.org/whl/cu128, GPU 없으면 .../whl/cpu)."""
    py = Path(TTS_PY); env = py.parents[1]          # 기본 tools/video/tts_env. 환경변수 TTS_PY로 다른 위치(예: 다른 드라이브)에 만들 수 있다
    if not py.exists() and not _py312(): _pkg("Python.Python.3.12", "python@3.12")
    if not py.exists():
        mk = ["py", "-3.12", "-m", "venv"] if shutil.which("py") else [shutil.which("python3.12") or "python3.12", "-m", "venv"]
        subprocess.run(mk + [str(env)], check=True)
    idx = _torch_index(); print("torch 휠:", idx, flush=True)
    pip = [str(py), "-m", "pip", "install", "-q"]
    subprocess.run(pip + ["--upgrade", "pip"], check=True)
    subprocess.run(pip + ["torch", "torchaudio", "--index-url", idx], check=True)
    subprocess.run(pip + ["qwen-tts", "soundfile", "scipy", "numpy"], check=True)
    subprocess.run([str(py), "-c", "import torch, qwen_tts; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"], check=True)
    print("setup-tts ok:", env, f"(모델은 첫 tts 실행 때 {env / 'hf'}로 내려받는다)")


def doctor():
    """새 컴퓨터 점검: 영상 파이프라인에 필요한 것이 다 있는지, 없으면 무엇을 실행할지."""
    import importlib.util
    from common import SKILL, FONTS, find_chrome
    sk = install_skill()                       # 없으면 skills/motion-broll/에서 설치(로컬 복사, 인터넷 불필요)
    vn, vq = (Path(os.environ.get(k) or d).stem for k, d in (("VOICE_N", "f_narrator_high_calm"), ("VOICE_Q", "m_quote_mid_calm")))   # tts.py와 같은 규칙
    rows = [("Python 패키지(PyMuPDF·Pillow·numpy·imageio-ffmpeg·faster-whisper)", all(importlib.util.find_spec(m) for m in ("fitz", "PIL", "numpy", "imageio_ffmpeg", "faster_whisper")), "- setup"),
            ("ffmpeg (tools/video/bin)", Path(FF).exists() or bool(shutil.which(FF)), "- setup"),
            ("node", bool(shutil.which("node")), "Node.js LTS 설치(https://nodejs.org)"),
            ("node_modules (puppeteer-core, playwright)", (TOOLS / "node_modules" / "puppeteer-core").exists() and (TOOLS / "node_modules" / "playwright").exists(), "- setup"),
            ("Chrome 또는 playwright Chromium", bool(find_chrome()) or any((Path.home() / p).exists() for p in ("AppData/Local/ms-playwright", ".cache/ms-playwright", "Library/Caches/ms-playwright")), "- setup"),
            ("motion-broll 스킬 (.claude/skills/motion-broll ← skills/motion-broll)" + (" — 배포본과 다름" if sk == "diff" else ""), sk in ("ok", "external"), "- setup" if sk == "diff" else "git pull (skills/motion-broll 포함)"),
            ("한글 글꼴 (tools/video/fonts: VF + 자막용 Sub700)", (FONTS / "NotoSansKR-VF.ttf").exists() and (FONTS / "NotoSansKR-Sub700.ttf").exists(), "git pull (저장소에 포함)"),
            (f"목소리 원본 (tools/video/voices: 내레이터 {vn} · 인용 {vq})", all((TOOLS / "voices" / f"{v}.mp3").exists() for v in (vn, vq)),
             "git pull (저장소에 포함) 또는 VOICE_N·VOICE_Q를 voices/에 있는 이름으로"),
            ("TTS 환경 (tools/video/tts_env)", Path(TTS_PY).exists(), "- setup-tts")]
    for name, ok, fix in rows: print(f"  {'ok ' if ok else '없음'}  {name}" + ("" if ok else f"  →  {fix if not fix.startswith('-') else 'python tools/video/make_video.py ' + fix}"), flush=True)
    if Path(TTS_PY).exists():
        subprocess.run([TTS_PY, "-c", "import torch; print('  TTS torch', torch.__version__, '| GPU', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '없음(CPU, 느림)')"])
    print("모두 ok면 논문 영상을 만들 수 있다." if all(r[1] for r in rows) else "없음 항목을 위 명령으로 채운다.")


def new(P):
    P.video.mkdir(exist_ok=True); (P.video / "clips").mkdir(exist_ok=True); (P.video / "assets").mkdir(exist_ok=True)
    for f in TPL.iterdir():
        if f.is_file() and not (P.video / f.name).exists():
            text = f.read_text(encoding="utf-8").replace("{{PAPER}}", P.dir.name).replace("{{SHORT}}", P.short)
            text = text.replace("{{TITLE}}", P.config["meta"].get("title", "")).replace("{{VENUE}}", P.config["meta"].get("venue_short", P.config["meta"].get("venue", "")))
            (P.video / f.name).write_text(text, encoding="utf-8"); print("  +", f.name)
    src = P.video / "assets" / "sources.json"                  # 예시 이미지 출처 목록(rules/video_rules.md 2절, check-assets G12)
    if not src.exists(): src.write_text("{}\n", encoding="utf-8"); print("  + assets/sources.json")
    print("뼈대:", P.video, "→ 기획안.md부터 채운다 (rules/video_rules.md 3·5절). 입력 이미지는 논문 자료 → codex 예시 사진 → 데이터셋 순서")


def status(P):
    W = P.work; clips = P.clips()
    import base_render
    rows = [
        ("원고 기획안.md", P.script.exists() and "TODO_PAPER" not in P.script.read_text(encoding="utf-8")),
        ("음성 timeline.json", (W / "timeline.json").exists()),
        ("애니매틱 build/index.html", (P.build / "index.html").exists()),
        ("단어 시각 words.json", (W / "words.json").exists()),
        ("클립 명세 clips.json", bool(clips)),
        ("클립 조각 clips/*.html", bool(clips) and all((P.video / "clips" / f"{c['id']}-{c['name']}.html").exists() for c in clips)),
        ("클립 렌더 out/*.mp4", bool(clips) and all((lambda d: d is not None and abs(d - c["dur"]) < .06)(probe_dur(W / c["file"])) for c in clips)),
        ("기본 화면 part_*.ok", (W / "timeline.json").exists() and all((P.build / f"part_{k:02d}.ok").exists() for k, _, _ in base_render.chunks(P))),
        (f"최종 {P.out.name}", P.out.exists()),
    ]
    nxt = None
    for name, ok in rows:
        print(f"  [{'x' if ok else ' '}] {name}")
        if not ok and nxt is None: nxt = name
    if (W / "timeline.json").exists():
        T = P.timeline()["total"]; print(f"  음성 길이 {int(T // 60)}:{int(T % 60):02d}")
    print("다음:", nxt or "완료 (check로 QC)")


def run(mod, *args):
    r = subprocess.run([sys.executable, str(TOOLS / mod)] + [str(a) for a in args])
    if r.returncode: sys.exit(r.returncode)


def frames(P, times, name=None):
    out = P.work / "frames"; out.mkdir(exist_ok=True); files = []
    for t in times:
        f = out / f"f_{float(t):08.2f}.jpg"
        subprocess.run([FF, "-y", "-loglevel", "error", "-ss", str(t), "-i", str(P.out), "-frames:v", "1", "-vf", "scale=640:-1", str(f)], check=True)
        files.append(f)
    if name:
        from PIL import Image, ImageDraw
        ims = [Image.open(f) for f in files]; w, h = ims[0].size; cols = 2; rows = (len(ims) + 1) // 2
        sheet = Image.new("RGB", (w * cols, (h + 24) * rows), "white"); d = ImageDraw.Draw(sheet)
        for i, (im, t) in enumerate(zip(ims, times)):
            x, y = (i % cols) * w, (i // cols) * (h + 24); sheet.paste(im, (x, y + 24)); d.text((x + 6, y + 4), f"{float(t):.2f}s", fill="black")
        sheet.save(out / name, quality=85); print(out / name)
    else:
        print("\n".join(map(str, files)))


def gapcheck(P):
    """장 경계 무음 틈마다 틈 직전(앞 컷 끝 −0.05초)과 직후(다음 컷 시작 −0.05초) 프레임. 두 장이 같은 장면이어야 한다."""
    cuts = P.timeline()["cuts"]; ts = []
    for a, b in zip(cuts, cuts[1:]):
        gap = b["t0"] - (a["t0"] + a["dur"])
        if gap > 0.3: ts += [round(a["t0"] + a["dur"] - 0.05, 2), round(b["t0"] - 0.05, 2)]
    print(f"틈 {len(ts) // 2}곳"); frames(P, ts, "gaps.jpg")


def main():
    if len(sys.argv) < 3: raise SystemExit(__doc__)
    if sys.argv[2] == "setup": return setup()
    if sys.argv[2] == "setup-tts": return setup_tts()
    if sys.argv[2] == "doctor": return doctor()
    P = Paper(sys.argv[1]); cmd, rest = sys.argv[2], sys.argv[3:]
    ensure(cmd)
    if cmd == "new": new(P)
    elif cmd == "status": status(P)
    elif cmd == "check-script": run("check_video.py", P.dir, "script")
    elif cmd == "check-assets": run("check_video.py", P.dir, "assets")
    elif cmd == "check": run("check_video.py", P.dir, "all")
    elif cmd == "tts": sys.exit(subprocess.run([TTS_PY, str(TOOLS / "tts.py"), str(P.dir)] + rest).returncode)
    elif cmd == "animatic": run("animatic.py", P.dir)
    elif cmd in ("words", "briefs"): run("motion.py", P.dir, cmd)
    elif cmd == "clips-build": run("motion.py", P.dir, "build", *rest)
    elif cmd == "beats": run("motion.py", P.dir, "beats", *rest)
    elif cmd == "clips-render": run("motion.py", P.dir, "render", *rest)
    elif cmd == "base-render":
        if "--redo" in rest:
            import base_render; base_render.invalidate(P); rest = [r for r in rest if r != "--redo"]
        run("base_render.py", P.dir, *rest)
    elif cmd == "final": run("finish.py", P.dir, "final")
    elif cmd == "frames": frames(P, rest)
    elif cmd == "gapcheck": gapcheck(P)
    else: raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
