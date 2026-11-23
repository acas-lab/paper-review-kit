"""
main.py — FastAPI 백엔드.

  GET  /              대시보드 (frontend/index.html)
  GET  /api/auth      인증/도구 상태 (claude 로그인·API키·codex)
  GET  /api/papers    papers/ 목록 + 결과 HTML
  POST /api/upload    PDF 업로드 → rawpaper/ 저장
  WS   /ws            채팅 (멀티턴 스트리밍)
  /papers/*           결과 HTML·자산 정적 서빙 (미리보기)
  /static/*           프론트 정적 파일

보안: /ws 는 acceptEdits 권한의 Claude 세션을 연다. 그래서 모든 요청에 대해
  - Host 헤더가 127.0.0.1:PORT / localhost:PORT 인지 검사(DNS rebinding 차단),
  - WebSocket 은 Origin 이 http://127.0.0.1:PORT / http://localhost:PORT 일 때만 수락
    (Cross-Site WebSocket Hijacking 차단 — 브라우저는 WS 에 CORS 를 적용하지 않는다),
  - 그 외 HTTP 요청도 Origin 이 있으면 같은 목록과 대조한다.
PORT 는 환경변수 PAPER_REVIEW_PORT(기본 8765, start.py 가 설정)에서 읽는다.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from runner import ChatSession, PROJECT_DIR

WEBAPP_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = WEBAPP_DIR / "frontend"
RAWPAPER_DIR = PROJECT_DIR / "rawpaper"
PAPERS_DIR = PROJECT_DIR / "papers"

PORT = int(os.environ.get("PAPER_REVIEW_PORT", "8765") or 8765)
ALLOWED_HOSTS = frozenset({f"127.0.0.1:{PORT}", f"localhost:{PORT}"})
ALLOWED_ORIGINS = frozenset({f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"})
MAX_UPLOAD = 100 * 1024 * 1024  # 100MB


class LocalOnlyMiddleware:
    """Host·Origin 검사 (HTTP + WebSocket 공통, 순수 ASGI)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        host = headers.get("host", "").strip().lower()
        origin = headers.get("origin")
        ok = host in ALLOWED_HOSTS
        if ok and scope["type"] == "websocket":
            ok = origin is not None and origin.strip().lower() in ALLOWED_ORIGINS
        elif ok and origin is not None:
            ok = origin.strip().lower() in ALLOWED_ORIGINS
        status, msg = 403, "forbidden (host/origin)"
        if ok and scope["type"] == "http" and scope.get("path") == "/api/upload":
            # multipart 파서가 본문 전체를 받기 전에 Content-Length 로 먼저 거른다(여유 1MB = 폼 경계)
            try:
                cl = int(headers.get("content-length", "0") or 0)
            except ValueError:
                cl = 0
            if cl > MAX_UPLOAD + 1024 * 1024:
                ok, status, msg = False, 413, "upload too large"
        if ok:
            return await self.app(scope, receive, send)
        if scope["type"] == "websocket":
            await receive()  # websocket.connect
            await send({"type": "websocket.close", "code": 1008})
            return
        body = json.dumps({"error": msg}).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
        })
        await send({"type": "http.response.body", "body": body})


app = FastAPI(title="Paper Review Dashboard")
app.add_middleware(LocalOnlyMiddleware)


@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


def _claude_logged_in():
    """True/False, 또는 확인 불가면 None.
    Windows·Linux 는 ~/.claude/.credentials.json, macOS 는 키체인에 저장되므로 파일이 없어도 로그인일 수 있다."""
    creds = Path.home() / ".claude" / ".credentials.json"
    if creds.exists():
        return True
    if sys.platform == "darwin":
        return None
    return False


@app.get("/api/auth")
async def auth_status():
    return {
        "claude_logged_in": _claude_logged_in(),
        "api_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "codex_available": shutil.which("codex") is not None,
    }


@app.get("/api/papers")
async def list_papers():
    out = []
    if PAPERS_DIR.exists():
        for d in sorted(PAPERS_DIR.iterdir()):
            if d.is_dir():
                outputs = sorted(h.name for h in d.glob("*.html"))
                out.append({"folder": d.name, "outputs": outputs})
    return out


def _safe_pdf_name(raw: str):
    """업로드 파일명 → rawpaper/ 안의 안전한 basename (.pdf 만). 부적합하면 None."""
    name = (raw or "").replace("\\", "/").split("/")[-1]  # 경로 성분 제거
    if not name.lower().endswith(".pdf"):
        return None
    stem = re.sub(r"[^\w.\-]+", "_", name[:-4]).strip("._") or "paper"
    return stem[:120] + ".pdf"


def _unique_dest(name: str) -> Path:
    dest = RAWPAPER_DIR / name
    stem, n = dest.stem, 1
    while dest.exists():
        dest = RAWPAPER_DIR / f"{stem}_{n}.pdf"
        n += 1
    return dest


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    safe = _safe_pdf_name(file.filename or "")
    if not safe:
        return JSONResponse({"error": "PDF 파일만 업로드할 수 있어요."}, status_code=400)
    head = await file.read(5)
    if head != b"%PDF-":
        return JSONResponse({"error": "PDF 형식이 아닙니다."}, status_code=400)
    RAWPAPER_DIR.mkdir(parents=True, exist_ok=True)
    dest = _unique_dest(safe)
    if dest.resolve().parent != RAWPAPER_DIR.resolve():
        return JSONResponse({"error": "잘못된 파일명입니다."}, status_code=400)
    size = len(head)
    too_big = False
    with dest.open("xb") as f:  # x = 기존 파일 덮어쓰기 금지
        f.write(head)
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD:
                too_big = True
                break
            f.write(chunk)
    if too_big:
        dest.unlink(missing_ok=True)
        return JSONResponse({"error": f"파일이 너무 커요 (상한 {MAX_UPLOAD // (1024 * 1024)}MB)."}, status_code=413)
    return {"saved": dest.relative_to(PROJECT_DIR).as_posix()}


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    # Origin·Host 는 LocalOnlyMiddleware 가 이미 검사했다.
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
