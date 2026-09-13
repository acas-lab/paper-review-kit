@echo off
setlocal EnableExtensions
title Paper Review Kit - Web dashboard
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
rem ------------------------------------------------------------------
rem  Everyday launcher for WEB mode. Just hands over to webapp\win_start.bat
rem  (which runs webapp\start.py: creates webapp\.venv on first start,
rem  installs requirements, starts the server, opens the browser).
rem  ASCII-only on purpose (cmd.exe parses .bat in the OEM code page).
rem ------------------------------------------------------------------
echo.
echo === Paper Review Kit - start WEB dashboard ===
echo.

rem quick pre-checks so the failure message points at the right step
python -c "import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
if errorlevel 1 (
  py -3 -c "import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
  if errorlevel 1 (
    echo [FAIL] Python 3.10+ not found. Double-click 1_install_python.bat first.
    echo.
    pause
    exit /b 1
  )
)
where claude >nul 2>nul
if errorlevel 1 (
  echo [FAIL] "claude" command not found. Double-click 2_install_node_and_claude.bat first.
  echo.
  pause
  exit /b 1
)
if not exist "%USERPROFILE%\.claude\.credentials.json" (
  echo [FAIL] Not logged in to Claude. Double-click 3_login_claude.bat first.
  echo.
  pause
  exit /b 1
)

echo First start creates webapp\.venv and installs packages ^(a few minutes^).
echo The browser opens at http://127.0.0.1:8765 when ready.
echo To stop the server: press Ctrl+C in this window, or just close it.
echo.
call "%~dp0..\webapp\win_start.bat"
echo.
echo [OK] Web dashboard stopped. Double-click 5_start_web.bat to start it again.
echo.
pause
exit /b 0
