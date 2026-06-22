@echo off
REM Paper Review 대시보드 — 더블클릭 실행 (Windows)
cd /d "%~dp0"
where py >nul 2>nul && (py start.py) || (python start.py)
pause
