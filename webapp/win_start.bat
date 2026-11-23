@echo off
REM Paper Review dashboard - double-click launcher (Windows only).
REM ASCII-only on purpose: a UTF-8 Korean comment here made cmd run a stray fragment ("'...' is not recognized").
chcp 65001 >nul 2>&1
cd /d "%~dp0"
setlocal
REM Pick the interpreter once: "py -3" if the launcher finds a Python 3, else "python".
REM (the old "py ... || python ..." restarted the server with python after Ctrl+C or an error)
set "PYCMD=python"
py -3 -c "import sys" >nul 2>nul
if not errorlevel 1 set "PYCMD=py -3"
%PYCMD% start.py
REM setup\5_start_web.bat sets PRK_NO_PAUSE because it pauses itself
if not defined PRK_NO_PAUSE pause
endlocal
