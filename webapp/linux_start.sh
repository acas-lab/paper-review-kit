#!/usr/bin/env bash
# Paper Review 대시보드 — 실행 (Linux / macOS 전용)
# 사용: 터미널에서  ./webapp/linux_start.sh   또는 파일 관리자에서 실행
#  (처음 한 번 실행 권한 필요할 수 있음:  chmod +x webapp/linux_start.sh)
set -e
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "✗ Python을 찾을 수 없습니다. python.org 또는 패키지 매니저로 Python 3.10+ 설치 후 다시 실행하세요." >&2
  exit 1
fi
exec "$PY" start.py
