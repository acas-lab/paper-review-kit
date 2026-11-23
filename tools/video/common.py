# -*- coding: utf-8 -*-
"""논문 영상 파이프라인 공통: 경로, 논문 명세(spec.py) 불러오기, ffmpeg 위치.

논문 폴더 레이아웃 (rules/video_rules.md 4절)
  papers/N. name/
    {ShortName}_output.html      학습 HTML
    {ShortName}_video.mp4        최종 영상 (이 파이프라인의 산출물)
    video/
      기획안.md                  원고(컷 표) = TTS·자막·애니매틱의 정본
      spec.py                    논문별 값(자막 표기, TTS 읽기, 인용 위치, 출처, 장면 이미지)
      scenes.js                  캔버스 장면(컷 id → 그리기 함수)
      clipspec.py                motion 클립 명세(STYLE, CLIPS)
      clips/NN-name.html         motion 클립 조각(motion-broll 형식)
      assets/                    클립이 쓰는 이미지(사진 원본, 크롭)
      CREDITS.md                 외부 자료 출처
      기획안.html                 애니매틱 미리보기(생성물)
      work/                      생성물(음성 조각, 타임라인, 렌더 구간, 클립 mp4) — git 제외
"""
import filecmp, importlib.util, json, os, shutil, sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):              # cp949 콘솔에서 한글·기호 출력이 깨지지 않게
    try: _s.reconfigure(encoding="utf-8")
    except Exception: pass

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[1]                       # 킷 루트 (tools/video/의 두 단계 위)
EXE = ".exe" if os.name == "nt" else ""
FF = str(TOOLS / "bin" / f"ffmpeg{EXE}") if (TOOLS / "bin" / f"ffmpeg{EXE}").exists() else (shutil.which("ffmpeg") or "ffmpeg")
# motion-broll 엔진: 킷은 skills/motion-broll/(git 추적)로 배포하고, 쓰는 위치는 프로젝트 스킬 폴더 .claude/skills/motion-broll/다.
# 없으면 install_skill()이 복사해 설치한다(make_video.py doctor·setup·클립 단계). 환경변수 MOTION_BROLL로 위치를 바꾸면 설치하지 않는다
SKILL_SRC = ROOT / "skills" / "motion-broll"
SKILL = Path(os.environ.get("MOTION_BROLL", ROOT / ".claude" / "skills" / "motion-broll"))
def _venv_py(env):
    return Path(env) / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _long_paths_enabled():
    """Windows 레지스트리 LongPathsEnabled=1 이면 260자 제한이 풀려 있다."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem") as k:
            return winreg.QueryValueEx(k, "LongPathsEnabled")[0] == 1
    except Exception:
        return False


TTS_ENV_KIT = TOOLS / "tts_env"                 # 기본 위치(킷 안)
TTS_ENV_SHORT = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "paper-review-kit" / "tts_env"   # Windows 긴 경로 회피용
TTS_PATH_MAX = 60                               # tts_env 폴더 경로가 이보다 길면 torch 설치 중 260자 제한에 걸릴 수 있다


def tts_python():
    """TTS 파이썬 위치. 순서: 환경변수 TTS_PY → 이미 설치된 킷 안 tools/video/tts_env → 이미 설치된 짧은 위치
    → (Windows, 킷 경로가 길고 LongPathsEnabled가 꺼져 있으면) %LOCALAPPDATA%/paper-review-kit/tts_env → 킷 안 기본 위치.
    make_video.py(setup-tts·doctor·tts)와 setup/0_check.bat이 같은 순서로 찾는다."""
    if os.environ.get("TTS_PY"): return os.environ["TTS_PY"]
    for env in (TTS_ENV_KIT, TTS_ENV_SHORT):
        if _venv_py(env).exists(): return str(_venv_py(env))
    if os.name == "nt" and len(str(TTS_ENV_KIT)) > TTS_PATH_MAX and not _long_paths_enabled():
        return str(_venv_py(TTS_ENV_SHORT))
    return str(_venv_py(TTS_ENV_KIT))


TTS_PY = tts_python()
FONTS = TOOLS / "fonts"                        # 한글 글꼴 Noto Sans KR(OFL, 라이선스 OFL-NotoSansKR.txt; libass가 폴더의 모든 파일을 읽으므로 ttf만 둔다). 자막(ASS)과 클립이 시스템 설치 여부와 무관하게 쓴다
FPS = 30
LEN_MIN, LEN_MAX = 600, 900                    # 영상 길이 기준(초): 10~15분


class Paper:
    def __init__(self, arg):
        p = Path(arg)
        if not p.is_absolute():
            p = (ROOT / arg) if (ROOT / arg).exists() else (ROOT / "papers" / arg)
        self.dir = p.resolve()
        if not (self.dir / "config.json").exists():
            raise SystemExit(f"논문 폴더가 아니다(config.json 없음): {self.dir}")
        self.video = self.dir / "video"
        self.work = self.video / "work"; self.work.mkdir(parents=True, exist_ok=True)
        self.build = self.work / "build"
        self.script = self.video / "기획안.md"
        self.config = json.loads((self.dir / "config.json").read_text(encoding="utf-8"))
        outs = sorted(self.dir.glob("*_output.html"))
        self.short = outs[0].name[:-len("_output.html")] if outs else self.dir.name.split(". ", 1)[-1]
        self.out = self.dir / f"{self.short}_video.mp4"
        name = self.config["meta"].get("source_pdf", "")   # rawpaper/ 기준 파일 이름(킷 규약). 루트 기준 경로·논문 폴더 안 PDF도 받는다
        self.pdf = next((c for c in (ROOT / "rawpaper" / name, ROOT / name, self.dir / name) if name and c.is_file()), ROOT / "rawpaper" / name)

    def need_pdf(self):
        """원본 PDF가 필요한 단계(animatic: 인용 지면·400 DPI 크롭)에서 부른다. 없으면 어디에 두는지 알려 준다."""
        if not self.pdf.is_file():
            raise SystemExit(f"원본 PDF가 없다: {self.pdf} (config.json#meta.source_pdf 파일을 rawpaper/에 둔다)")
        return self.pdf

    def spec(self):
        return load(self.video / "spec.py", "paper_spec")

    def clipspec(self):
        f = self.video / "clipspec.py"
        return load(f, "paper_clipspec") if f.exists() else None

    def timeline(self):
        return json.loads((self.work / "timeline.json").read_text(encoding="utf-8"))

    def clips(self):
        f = self.work / "clips.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def skill_state():
    """motion-broll 설치 상태: 'ok'(skills/motion-broll과 같음) · 'diff'(설치됐지만 배포본과 다름) · 'missing' · 'external'(MOTION_BROLL 지정)."""
    if os.environ.get("MOTION_BROLL"): return "external" if (SKILL / "engine" / "build.py").exists() else "missing"
    if not (SKILL / "SKILL.md").exists() or not (SKILL / "engine" / "build.py").exists(): return "missing"
    if not SKILL_SRC.is_dir(): return "ok"
    def same(a, b):
        c = filecmp.dircmp(a, b, ignore=["__pycache__"])
        if c.left_only or c.diff_files or c.funny_files: return False
        if filecmp.cmpfiles(a, b, c.common_files, shallow=False)[1]: return False
        return all(same(Path(a) / d, Path(b) / d) for d in c.common_dirs)
    return "ok" if same(SKILL_SRC, SKILL) else "diff"


def install_skill(force=False):
    """skills/motion-broll/ → .claude/skills/motion-broll/ (프로젝트 스킬 폴더). 없을 때만, force면 배포본으로 덮어쓴다."""
    st = skill_state()
    if st == "external" or (st == "ok") or (st == "diff" and not force): return st
    if not SKILL_SRC.is_dir():
        raise SystemExit(f"motion-broll 배포본이 없다: {SKILL_SRC} (킷을 다시 받거나 git pull)")
    SKILL.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SKILL_SRC, SKILL, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    print(f"[자동 준비] motion-broll 스킬 설치: {SKILL_SRC.relative_to(ROOT)} → {SKILL.relative_to(ROOT)}", flush=True)
    return skill_state()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def find_chrome():
    """puppeteer-core가 쓸 Chrome. 환경변수 CHROME → 흔한 설치 위치 → 없으면 None(render.mjs가 playwright Chromium을 쓴다)."""
    if os.environ.get("CHROME") and Path(os.environ["CHROME"]).exists(): return os.environ["CHROME"]
    cands = [Path(os.environ.get(k, "")) / "Google/Chrome/Application/chrome.exe" for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
    cands += [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")] + [Path(shutil.which(n) or "-") for n in ("google-chrome", "chromium", "chromium-browser")]
    return next((str(c) for c in cands if c.is_file()), None)


def node_env():
    env = dict(os.environ, NODE_PATH=str(TOOLS / "node_modules"), FFMPEG=FF,
               PATH=str(TOOLS / "bin") + os.pathsep + os.environ["PATH"])
    if find_chrome(): env["CHROME"] = find_chrome()
    return env


def probe_dur(path):
    import re, subprocess
    p = Path(path)
    if not p.exists() or p.stat().st_size < 50_000: return None
    r = subprocess.run([FF, "-hide_banner", "-i", str(p)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None


def parse_script(text):
    """기획안.md → 장 목록. '### 장 제목' 아래 '| cNN | N|Q|— | 말 | 출처 |' 표 행을 컷으로 읽는다. '## '이 나오면 원고 끝."""
    import re
    chapters, cur, started = [], None, False
    for line in text.splitlines():
        m = re.match(r"### (.+)$", line)
        if m:
            name = m.group(1).strip(); num = re.match(r"(\d+)장 · (.+)", name)
            cur = {"name": name, "label": (f"{num.group(1)}장" if num else name.split(" · ")[0]),
                   "title": (num.group(2) if num else name.split(" · ")[-1]), "cuts": []}
            chapters.append(cur); started = True; continue
        if line.startswith("## ") and started:
            cur = None; continue
        m = re.match(r"\| (c\d\d[a-z]?) \| (N|Q|—) \| (.+?) \| (.+?) \|$", line)
        if m and cur is not None:
            cur["cuts"].append({"id": m.group(1), "sp": m.group(2), "say": m.group(3), "src": m.group(4)})
    return [c for c in chapters if c["cuts"]]


def sentences(s):
    import re
    return [x for x in re.split(r"(?<=[.?])\s+", s) if x]
