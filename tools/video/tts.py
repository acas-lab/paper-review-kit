# -*- coding: utf-8 -*-
"""논문 영상 내레이션 생성 (Qwen3-TTS 0.6B Base, x-vector 단일 화자).
실행: tools/video/tts_env/Scripts/python.exe tools/video/tts.py "papers/N. name" [--dry]
  (make_video.py tts 가 이 명령을 대신 부른다)
입력: video/기획안.md, video/spec.py(READ_WORDS)  /  출력: video/work/seg/*.wav, work/timeline.json, work/narration.wav
음성: 내레이터 N = voices/f_narrator_high_calm.mp3(여성·높은 음역·느린 속도) 원본 1개,
      저자 인용 Q = voices/m_quote_mid_calm.mp3(남성·중간 음역·느린 속도) 원본 1개 (rules/video_rules.md 6절). 혼합·atempo 없음.
      바꾸려면 환경변수 VOICE_N / VOICE_Q에 voices/의 다른 파일 이름(확장자 제외)을 준다.
"""
import hashlib, json, os, re, sys
from pathlib import Path
import numpy as np, soundfile as sf
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Paper, parse_script, sentences

PAPER = Paper(next(a for a in sys.argv[1:] if not a.startswith("--")))
SEG = PAPER.work / "seg"; SEG.mkdir(exist_ok=True)
HERE = Path(__file__).resolve().parent
TTS = Path(sys.prefix) if sys.prefix != sys.base_prefix else HERE / "tts_env"   # 이 파이썬의 venv(기본 tools/video/tts_env, TTS_PY로 바꿀 수 있다) = venv + hf 모델 캐시 + ref24 변환본 (git 제외, make_video.py - setup-tts)
VOICES = HERE / "voices"               # 목소리 원본 mp3 (git 추적)
os.environ.setdefault("HF_HOME", str(TTS / "hf"))   # transformers import 전에 정한다
SR = 24000
SIM_OK = 0.80   # 기준 화자 임베딩과의 코사인 유사도. 낮으면 다시 생성(목소리 흔들림 방지)
DRY = "--dry" in sys.argv
VOICE = {sp: Path(os.environ.get(f"VOICE_{sp}") or d).stem for sp, d in (("N", "f_narrator_high_calm"), ("Q", "m_quote_mid_calm"))}   # voices/<이름>.mp3 (확장자를 붙여 줘도 된다)
for _sp, _v in VOICE.items():
    if not (VOICES / f"{_v}.mp3").is_file():
        raise SystemExit(f"목소리 원본이 없다: {VOICES / (_v + '.mp3')} (VOICE_{_sp}). 쓸 수 있는 이름: {sorted(p.stem for p in VOICES.glob('*.mp3'))}")
SILENT = 4.5    # 화자 '—' 컷(무음) 길이, 초 (check_video·animatic 추정과 같다)

# ---------------------------------------------------------------- 읽기 변환
D = "영일이삼사오육칠팔구"
def sino(n):
    if n == 0: return "영"
    out, units = "", [(10**8, "억"), (10**4, "만")]
    for u, name in units:
        if n >= u:
            q = n // u; out += ("" if (q == 1 and name == "만") else sino4(q)) + name; n %= u
    return out + sino4(n)
def sino4(n):
    s = ""
    for u, name in [(1000, "천"), (100, "백"), (10, "십")]:
        q = n // u
        if q: s += ("" if q == 1 else D[q]) + name
        n %= u
    return s + (D[n] if n else "")
def num(m):
    t = m.group(0).replace(",", "")
    if "." in t:
        a, b = t.split(".")
        return sino(int(a)) + " 점 " + " ".join(D[int(ch)] for ch in b)
    return sino(int(t))
# 공통 읽기 표. 논문별 표기는 spec.READ_WORDS가 먼저 적용된다. 원고는 원칙적으로 한국어 읽기로 쓰고, 이 표는 남은 영문을 잡는 안전망이다.
# 아래 항목은 AI/CS 논문 예시다(모체 사례). 다른 분야의 약어·기호 읽기는 논문의 spec.READ_WORDS에 둔다
WORDS = list(getattr(PAPER.spec(), "READ_WORDS", [])) + [
         ("auto-regressive", "오토리그레시브"), ("forward pass", "포워드 패스"), ("grounding", "그라운딩"), ("baseline", "베이스라인"),
         ("MLLM", "엠엘엘엠"), ("VLM", "브이엘엠"), ("LLM", "엘엘엠"), ("RoI", "알오아이"), ("GQA", "지큐에이")]
def reading(s):
    for a, b in WORDS: s = s.replace(a, b)
    LET = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", ["에이", "비", "씨", "디", "이", "에프", "지", "에이치", "아이", "제이", "케이", "엘", "엠", "엔", "오", "피", "큐", "알", "에스", "티", "유", "브이", "더블유", "엑스", "와이", "제트"]))
    s = re.sub(r"(?<![A-Za-z])([A-Z])(?![A-Za-z])", lambda m: LET[m.group(1)] + " ", s)
    s = re.sub(r"(?<![\d.])1만", "만", s)
    s = re.sub(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", num, s)
    left = re.findall(r"[A-Za-z0-9]+", s)
    if left: raise SystemExit(f"읽기 변환 후 영문·숫자 남음: {left} in {s}")
    return s

# ---------------------------------------------------------------- 원고
def parse():
    cuts = []
    for ch in parse_script(PAPER.script.read_text(encoding="utf-8")):
        for c in ch["cuts"]: cuts.append(dict(c, ch=ch["name"]))
    return cuts

# ---------------------------------------------------------------- 합성
model = None; EMB = {}
def ref24(name):
    """voices/<name>.mp3 → tts_env/ref24/<name>.wav (24 kHz 모노). 원본이 바뀌면 다시 변환한다."""
    import subprocess
    from common import FF
    src = VOICES / f"{name}.mp3"; out = TTS / "ref24" / f"{name}.wav"; out.parent.mkdir(exist_ok=True)
    if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", str(SR), str(out)], check=True)
    return out
def load():
    global model
    import torch
    from qwen_tts import Qwen3TTSModel
    model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-0.6B-Base", device_map="cuda:0" if torch.cuda.is_available() else "cpu", dtype=torch.float32)   # GPU 없으면 CPU(느림)
    E = {}
    def mix(w):
        for k in w:
            if k not in E:
                a, _ = sf.read(str(ref24(k)), dtype="float32"); E[k] = model.model.extract_speaker_embedding(audio=a, sr=SR).float()
        m = sum(v * E[k] for k, v in w.items()); return m / m.norm() * np.mean([E[k].norm().item() for k in w])
    # 2026-11-18 사용자: 인용 외에는 한 사람 목소리로 → 원본 음원 단일 화자(혼합 없음)
    for sp, name in VOICE.items(): EMB[sp] = mix({name: 1.0})
def db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
TAIL = " 아."    # 문장 끝에 붙여 읽힌 뒤 잘라내는 꼬리. 문장 끝 음절("~다.")이 먹히지 않게 한다(2026-11-19 사용자 지시)
def cut_tail(x):
    """꼬리 " 아." 앞의 무음(≥0.1초) 한가운데서 자른다. 자른 자리는 무음이므로 문장 끝 음절을 깎지 않는다.
    마지막 무음 뒤 소리(= "아")가 0.06~0.8초가 아니면 꼬리를 못 찾은 것으로 보고 실패(False)를 돌려준다."""
    fr = int(.01 * SR); e = np.array([db(x[i:i + fr]) for i in range(0, len(x) - fr, fr)]); quiet = e < -45; gaps = []; i = 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            if j - i >= 10 and j < len(quiet): gaps.append((i, j))
            i = j
        else: i += 1
    if not gaps: return x, False
    g0, g1 = gaps[-1]; voiced = np.where(~quiet[g1:])[0]
    tail = (voiced[-1] + 1) / 100 if len(voiced) else 0
    if not .06 <= tail <= .8: return x, False
    return x[:(g0 + min((g1 - g0) // 2, 12)) * fr], True
def tidy(x):
    k = np.where(np.abs(x) > 10 ** (-50 / 20))[0]; x = x[max(k[0] - int(.02 * SR), 0):] if len(k) else x
    fi, fo = int(.02 * SR), int(.03 * SR); x = x.copy(); x[:fi] *= np.linspace(0, 1, fi); x[-fo:] *= np.linspace(1, 0, fo); return x   # 페이드아웃은 무음 구간 안에서만
def synth(sp, text, target=None):
    """target(초)이 있으면 그 길이에 가장 가까운 결과를 고른다(타이밍 유지 재생성 --keep-timing)."""
    import torch
    key = hashlib.md5(f"v3|{sp}|{VOICE[sp]}|{text}".encode()).hexdigest()[:12]; f = SEG / f"{key}.wav"   # 목소리를 바꾸면 다시 생성
    if f.exists():
        x, _ = sf.read(f, dtype="float32"); return x
    if model is None: load()
    P = dict(ref_code=[None], ref_spk_embedding=[EMB[sp]], x_vector_only_mode=[True], icl_mode=[False])
    n = len(re.sub(r"\s", "", text)); best = None
    cap = int((n / 3.5 + 3) * 13)   # 코덱 약 12.5토큰/초. 끝을 못 내고 계속 말하는 생성(48 c32, 기본 상한 2048 = 약 160초)을 끊는다 → 꼬리 없음 → 다음 시드
    for tr in range(8 if target else 4):
        torch.manual_seed(int(hashlib.md5(f"{text}|{tr}".encode()).hexdigest()[:8], 16))
        w, _ = model.generate_voice_clone(text=text + TAIL, language="korean", voice_clone_prompt=P, max_new_tokens=cap); torch.cuda.empty_cache()
        x, ok = cut_tail(w[0].astype(np.float32)); x = tidy(x); cps = n / (len(x) / SR)
        e = model.model.extract_speaker_embedding(audio=x, sr=SR).float(); sim = float((e @ EMB[sp]) / (e.norm() * EMB[sp].norm()))
        fit = abs(len(x) / SR - target) / target * 20 if target else 0
        score = abs(cps - 5.5) + (0 if ok else 5) + (1 - sim) * 10 + fit
        if best is None or score < best[0]: best = (score, x, cps, ok, sim)
        if ok and 4.9 <= cps <= 6.2 and sim >= SIM_OK and (not target or abs(len(x) / SR - target) <= .06 * target): break
    _, x, cps, ok, sim = best
    print(f"  {sp} {cps:.2f}자/초 sim={sim:.3f} cut={ok} tries={tr + 1} {text[:30]}", flush=True)
    sf.write(f, x, SR); return x

def room(y, rng=np.random.default_rng(7)):
    from scipy.signal import lfilter
    n = int(.35 * SR); t = np.arange(n) / SR; ir = rng.standard_normal(n).astype(np.float32) * np.exp(-6.9 * t / .3); ir[:int(.004 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum())
    wet = np.convolve(y, ir)[:len(y)]; out = y + .14 * wet
    w = rng.standard_normal(len(y)).astype(np.float32)
    pink = lfilter([0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400], w)
    pink = pink / np.sqrt(np.mean(pink ** 2)) * 10 ** (-62 / 20); return (out + pink).astype(np.float32)

GAP_SENT, PAD_END, Q_LEAD, Q_END, CH_GAP, TITLE_HOLD = .32, .55, .45, .75, .9, 0
def main():
    cuts = parse(); print(len(cuts), "cuts", flush=True)
    if DRY:
        print("목소리:", VOICE)
        for c in cuts:
            for s in ([] if c["sp"] == "—" else sentences(c["say"])): print(c["id"], c["sp"], reading(s))
        return
    track, t, prev_ch, tl = [], 0.0, None, []
    def put(x):
        nonlocal t; track.append(x); t += len(x) / SR
    def sil(d): put(np.zeros(int(d * SR), np.float32))
    sil(.6)
    for c in cuts:
        if prev_ch and c["ch"] != prev_ch: sil(CH_GAP)
        prev_ch = c["ch"]; t0 = t; sents = []
        if c["sp"] == "—":                                  # 무음 컷: 말 칸은 읽지 않는다(rules/video_rules.md 5절)
            sil(SILENT); tl.append({"id": c["id"], "t0": round(t0, 3), "dur": round(t - t0, 3), "sents": []}); continue
        if c["sp"] == "Q": sil(Q_LEAD)
        for k, s in enumerate(sentences(c["say"])):
            if k: sil(GAP_SENT)
            x = synth(c["sp"], reading(s)); a = t; put(x); sents.append({"t0": round(a, 3), "t1": round(t, 3), "text": s})
        sil(Q_END if c["sp"] == "Q" else PAD_END)
        tl.append({"id": c["id"], "t0": round(t0, 3), "dur": round(t - t0, 3), "sents": sents})
    sil(1.5)
    y = room(np.concatenate(track)); y *= .89 / np.max(np.abs(y))
    sf.write(PAPER.work / "narration.wav", y, SR)
    (PAPER.work / "timeline.json").write_text(json.dumps({"total": round(t, 3), "cuts": tl}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"DONE total {t:.1f}s", flush=True)

def keep_timing():
    """이미 렌더한 영상의 내레이션만 다시 만든다. timeline.json의 문장 시작 시각을 그대로 두고, 문장마다 옛 길이에 가장 가까운
    새 음성을 골라 같은 자리에 놓는다(클립·자막 타이밍 불변). 다음 문장 시작을 넘으면 자르고 경고한다."""
    cuts = parse(); old = json.loads((PAPER.work / "timeline.json").read_text(encoding="utf-8"))
    T = old["total"]; y = np.zeros(int(T * SR) + SR, np.float32)
    starts = sorted(s["t0"] for c in old["cuts"] for s in c["sents"]) + [T]; warn = []
    for c, oc in zip(cuts, old["cuts"]):
        assert c["id"] == oc["id"], (c["id"], oc["id"])
        for s, os_ in zip(sentences(c["say"]), oc["sents"]):
            assert s == os_["text"], (s, os_["text"])
            x = synth(c["sp"], reading(s), target=os_["t1"] - os_["t0"])
            a = int(os_["t0"] * SR); nxt = starts[starts.index(os_["t0"]) + 1]
            room_ = nxt - os_["t0"] - .02                 # 다음 문장 직전까지 쓸 수 있다(새 음성 끝은 무음이라 겹쳐도 소리는 안 겹친다)
            if len(x) / SR > room_: warn.append((c["id"], round(len(x) / SR - room_, 2), s[:20])); x = x[:int(room_ * SR)]; x[-int(.03 * SR):] *= np.linspace(1, 0, int(.03 * SR))
            y[a:a + len(x)] += x
    y = room(y[:int(T * SR)]); y *= .89 / np.max(np.abs(y))
    sf.write(PAPER.work / "narration.wav", y, SR)
    print("DONE keep-timing", f"{T:.1f}s", "넘침:", warn, flush=True)

if __name__ == "__main__":
    keep_timing() if "--keep-timing" in sys.argv else main()
