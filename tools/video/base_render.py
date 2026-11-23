# -*- coding: utf-8 -*-
"""애니매틱(work/build/index.html)의 기본 화면 렌더: motion 클립이 덮지 않는 구간만, 30초 단위로.

python tools/video/base_render.py "papers/N. name" [동시 개수=2] [시작 허용 초=420]
  → work/build/part_KK.mp4 (+ .ok 완료 표시). 반복 실행하면 남은 구간만 이어서 렌더한다.
자막은 넣지 않는다(?clean=1&nosub=1). 자막은 finish.py가 ASS로 입힌다.
"""
import subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Paper, TOOLS, FPS, node_env

CHUNK = 30.0   # 초. 구간마다 완료 표시(.ok)를 남겨, 중단돼도 이어서 렌더한다


def gaps(P):
    """클립 밖 구간. 장 경계 무음(0.9초) 같은 1.5초 이하 틈은 앞 장면(클립 마지막 프레임)으로 채우고,
    클립 바로 뒤 기본 구간은 다음 컷 시작부터 잡는다(앞 컷 장면이 잠깐 비치는 오류 방지)."""
    tl = P.timeline(); T = tl["total"]
    cl = sorted((c["t0"], c["t0"] + c["dur"]) for c in P.clips())
    starts = sorted(c["t0"] for c in tl["cuts"])
    nxt_cut = lambda t: next((x for x in starts if x >= t - 0.1), t)   # 클립 끝이 다음 컷 시작보다 몇 ms 늦을 수 있다(반올림, 모체 사례에서 한 컷이 통째로 빠짐)
    out, t = [], 0.0
    for a, b in cl:
        if t > 0: t = min(nxt_cut(t), a)
        if a - t > 1.5: out.append((t, a))
        t = max(t, b)
    if T - t > 1.5: out.append((t, T))
    return out


def chunks(P):
    out = []
    for a, b in gaps(P):
        n = int(-(-(b - a) // CHUNK))
        for i in range(n): out.append((a + i * (b - a) / n, a + (i + 1) * (b - a) / n))
    return [(k, s, e) for k, (s, e) in enumerate(out)]


def render(P, par=2, budget=420):
    B = P.build; html = B / "index.html"
    if not html.exists(): raise SystemExit("work/build/index.html이 없다. animatic을 먼저 만든다")
    sig = B / "chunks.txt"; cur = "\n".join(f"{k} {s:.4f} {e:.4f}" for k, s, e in chunks(P))
    if sig.exists() and sig.read_text() != cur:            # 구간이 바뀌면: 시작·끝이 같은 구간은 새 번호로 옮겨 살리고 나머지는 무효화
        old = {tuple(l.split()[1:]): int(l.split()[0]) for l in sig.read_text().splitlines() if l.strip()}
        keep = {}
        for k, s, e in chunks(P):
            j = old.get((f"{s:.4f}", f"{e:.4f}"))
            if j is not None and (B / f"part_{j:02d}.ok").exists(): keep[k] = j
        for j in set(keep.values()): (B / f"part_{j:02d}.mp4").replace(B / f"keep_{j:02d}.mp4")
        for f in B.glob("part_*.ok"): f.unlink()
        for k, j in keep.items():
            (B / f"keep_{j:02d}.mp4").replace(B / f"part_{k:02d}.mp4"); (B / f"part_{k:02d}.ok").write_text("ok")
        print(f"구간 변경: {len(keep)}개 유지, {len(chunks(P)) - len(keep)}개 다시 렌더", flush=True)
    sig.write_text(cur)
    env = dict(node_env(), QS="?clean=1&nosub=1")
    start = time.time(); todo = [c for c in chunks(P) if not (B / f"part_{c[0]:02d}.ok").exists()]
    print(f"남은 구간 {len(todo)}/{len(chunks(P))}", flush=True); running = []
    while todo or running:
        while todo and len(running) < par and time.time() - start < budget:
            k, s, e = todo.pop(0); out = B / f"part_{k:02d}.mp4"
            log = open(B / f"part_{k:02d}.log", "w", encoding="utf-8")
            running.append((k, subprocess.Popen(["node", str(TOOLS / "render.mjs"), str(html), str(FPS), f"{s:.4f}", f"{e:.4f}", str(out)],
                                                cwd=B, env=env, stdout=log, stderr=subprocess.STDOUT)))
        if not running: break
        time.sleep(2)
        for k, p in list(running):
            if p.poll() is not None:
                running.remove((k, p))
                if p.returncode == 0: (B / f"part_{k:02d}.ok").write_text("ok")
                print(f"구간 {k:02d} {'완료' if p.returncode == 0 else '실패'} ({time.time() - start:.0f}s)", flush=True)
    left = [c for c in chunks(P) if not (B / f"part_{c[0]:02d}.ok").exists()]
    print("ALL CHUNKS DONE" if not left else f"남은 구간 {len(left)}", flush=True)
    return not left


def invalidate(P):
    """애니매틱(scenes.js·spec.py)을 고친 뒤 기본 화면을 전부 다시 렌더하게 한다."""
    for f in P.build.glob("part_*.ok"): f.unlink()


if __name__ == "__main__":
    render(Paper(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 2, float(sys.argv[3]) if len(sys.argv) > 3 else 420)
