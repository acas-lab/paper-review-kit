"""
main.py — FastAPI 백엔드.

  GET  /              대시보드 (frontend/index.html)
  GET  /api/auth      인증/도구 상태 (claude 로그인·API키·codex)
  GET  /api/papers    papers/ 목록 + 결과 HTML
  POST /api/upload    PDF 업로드 → rawpaper/ 저장
  WS   /ws            채팅 (멀티턴 스트리밍)
  /papers/*           결과 HTML·자산 정적 서빙 (미리보기)
  /static/*           프론트 정적 파일
"""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from runner import ChatSession, PROJECT_DIR

WEBAPP_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = WEBAPP_DIR / "frontend"
RAWPAPER_DIR = PROJECT_DIR / "rawpaper"
PAPERS_DIR = PROJECT_DIR / "papers"

app = FastAPI(title="Paper Review Dashboard")


@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/auth")
async def auth_status():
    creds = Path.home() / ".claude" / ".credentials.json"
    return {
        "claude_logged_in": creds.exists(),
        "api_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "codex_available": shutil.which("codex") is not None,
    }


@app.get("/api/papers")
async def list_papers():
    out = []
    if PAPERS_DIR.exists():
        for d in sorted(PAPERS_DIR.iterdir()):
            if d.is_dir():
                outputs = sorted(h.name for h in d.glob("*_output.html"))
                out.append({"folder": d.name, "outputs": outputs})
    return out


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        return JSONResponse({"error": "PDF 파일만 업로드할 수 있어요."}, status_code=400)
    RAWPAPER_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.\-]+", "_", file.filename)
    dest = RAWPAPER_DIR / safe
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"saved": dest.relative_to(PROJECT_DIR).as_posix()}


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    session = ChatSession()

    async def emit(ev: dict) -> None:
        await websocket.send_text(json.dumps(ev, ensure_ascii=False))

    try:
        await session.start()
        await emit({"type": "ready"})
    except Exception as e:  # 글루 시작 실패 (로그인 안 됨 등)
        await emit({"type": "error", "message": f"Claude 세션 시작 실패: {e}"})
        await websocket.close()
        return

    try:
        while True:
            data = json.loads(await websocket.receive_text())
            kind = data.get("type")
            if kind == "user":
                text = (data.get("text") or "").strip()
                if not text:
                    continue
                try:
                    await session.send(text, emit)
                except Exception as e:
                    await emit({"type": "error", "message": str(e)})
                finally:
                    await emit({"type": "turn_end"})
            elif kind == "interrupt":
                await session.interrupt()
    except WebSocketDisconnect:
        pass
    finally:
        await session.close()


# 미리보기·정적 — papers/ 가 없을 수도 있으니 보장
PAPERS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/papers", StaticFiles(directory=str(PAPERS_DIR)), name="papers")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
