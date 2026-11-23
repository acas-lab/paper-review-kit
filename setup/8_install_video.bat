@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Paper Review Kit - Step 8 (intro video tools, Stage 13)
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
rem ------------------------------------------------------------------
rem  Step 8 : tools for the paper intro VIDEO (Stage 13, tools\video\)
rem     a) motion-broll skill : copies  skills\motion-broll  to
rem        .claude\skills\motion-broll  (project skill folder, local copy)
rem     b) make_video.py - setup : python packages (tools\video\requirements.txt),
rem        ffmpeg, node_modules (puppeteer-core, playwright) + Chromium
rem     c) OPTIONAL make_video.py - setup-tts : Python 3.12 venv + torch +
rem        qwen-tts in tools\video\tts_env  (SEVERAL GB, GPU recommended)
rem  make_video.py also installs all of this by itself on first use, so this
rem  file only does it ahead of time. Needs steps 1 and 2 (python, node).
rem  ASCII-only on purpose (cmd.exe parses .bat in the OEM code page).
rem ------------------------------------------------------------------
echo.
echo === Step 8: Install the intro-video tools (Stage 13) ===
echo   ^(motion-broll skill, ffmpeg, node packages, Chromium, then optional TTS^)
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
if exist "%ProgramFiles%\nodejs\node.exe" set "PATH=%ProgramFiles%\nodejs;%PATH%"
for /f "tokens=*" %%v in ('!PYCMD! --version 2^>^&1') do set "PYV=%%v"
echo Using: !PYV!  ^(command: !PYCMD!^)
echo.

rem ---- a + b : skill + base tools -----------------------------------------
echo Installing: motion-broll skill + video base tools ^(a few minutes on first run^)
echo.
!PYCMD! tools\video\make_video.py - setup
set "RC=!ERRORLEVEL!"
echo.
if not "!RC!"=="0" (
  echo [FAIL] make_video.py - setup returned error code !RC!.
  echo      Check your internet connection ^(and that step 2 installed Node.js^),
  echo      then run this file again. Manual command:
  echo        !PYCMD! tools\video\make_video.py - setup
  echo.
  pause
  exit /b 1
)

rem ---- c : TTS (optional, large) ------------------------------------------
echo.
echo The narration voice engine ^(TTS^) needs SEVERAL GB ^(Python 3.12 + torch^).
echo An NVIDIA GPU is recommended; without one it runs on the CPU ^(slow^).
echo If you skip it now, it installs itself the first time a video is made.
choice /c YN /n /m "Install the TTS environment now? [Y/N] "
if errorlevel 2 (
  echo Skipped TTS. Later:  !PYCMD! tools\video\make_video.py - setup-tts
) else (
  !PYCMD! tools\video\make_video.py - setup-tts
  if errorlevel 1 (
    echo [FAIL] setup-tts failed. Retry later:  !PYCMD! tools\video\make_video.py - setup-tts
  )
)

rem ---- report -------------------------------------------------------------
echo.
echo Checking what is in place:
echo.
!PYCMD! tools\video\make_video.py - doctor
echo.
echo [OK] Video tools step finished. Lines marked as missing above show the
echo      command that fills them in.
echo.
pause
exit /b 0
