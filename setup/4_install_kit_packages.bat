@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Paper Review Kit - Step 4 (Python packages for CLI tools)
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
rem ------------------------------------------------------------------
rem  Step 4 : Python packages used by the CLI tools in  tools\*.py
rem     pymupdf    - PDF text / figure extraction (structure_paper, autocrop)
rem     playwright - headless Chromium for tools\check_memo_layer.py
rem  Installed into the SYSTEM Python. (Web mode does NOT need this:
rem  webapp\start.py creates its own webapp\.venv on first start.)
rem  ASCII-only on purpose (cmd.exe parses .bat in the OEM code page).
rem ------------------------------------------------------------------
echo.
echo === Step 4/4: Install Python packages for the CLI tools ===
echo   ^(pymupdf + playwright + Chromium - needed by tools\*.py in CLI mode.
echo    Web mode installs its own venv on first start, but this step is harmless.^)
echo.

rem ---- find python (system) ----------------------------------------------
set "PYCMD="
python -c "import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
if not errorlevel 1 (
  set "PYCMD=python"
) else (
  py -3 -c "import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
  if not errorlevel 1 set "PYCMD=py -3"
)
if not defined PYCMD (
  if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
    set "PYCMD=python"
  )
)
if not defined PYCMD (
  echo [FAIL] Python 3.10+ not found.
  echo      Double-click 1_install_python.bat first
  echo      ^(if you just ran it, CLOSE that window and open this file again^).
  echo.
  pause
  exit /b 1
)
for /f "tokens=*" %%v in ('!PYCMD! --version 2^>^&1') do set "PYV=%%v"
echo Using: !PYV!  ^(command: !PYCMD!^)
echo.

rem ---- already installed? ------------------------------------------------
set "HAVE_FITZ=0"
set "HAVE_PW=0"
!PYCMD! -c "import fitz" >nul 2>nul
if not errorlevel 1 set "HAVE_FITZ=1"
!PYCMD! -c "import playwright" >nul 2>nul
if not errorlevel 1 set "HAVE_PW=1"
if "!HAVE_FITZ!!HAVE_PW!"=="11" (
  echo [OK] already installed: pymupdf, playwright
  echo      ^(re-checking the Chromium browser for playwright...^)
) else (
  echo Installing: pip pymupdf playwright  ^(a few minutes on first run^)
  echo.
  !PYCMD! -m pip install --upgrade pip pymupdf playwright
  set "RC=!ERRORLEVEL!"
  echo.
  if not "!RC!"=="0" (
    echo [FAIL] pip returned error code !RC!.
    echo      Check your internet connection, then run this file again.
    echo      Manual command:  !PYCMD! -m pip install --upgrade pip pymupdf playwright
    echo.
    pause
    exit /b 1
  )
)

rem ---- playwright browser (Chromium) --------------------------------------
echo.
echo Installing the Chromium browser for playwright ^(about 150 MB, skips if present^)...
echo.
!PYCMD! -m playwright install chromium
set "RC=!ERRORLEVEL!"
echo.
if not "!RC!"=="0" (
  echo [OK] pymupdf + playwright are installed, but the Chromium download FAILED ^(code !RC!^).
  echo      Only tools\check_memo_layer.py will be skipped. Everything else works.
  echo      To retry later:  !PYCMD! -m playwright install chromium
) else (
  echo [OK] All CLI packages installed: pymupdf, playwright, Chromium.
)
echo.
echo      Setup is complete. Every day, double-click:
echo        5_start_web.bat  - web dashboard ^(browser^)
echo        6_start_cli.bat  - Claude Code in the terminal
echo.
pause
exit /b 0
