@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Paper Review Kit - Step 7 (codex CLI - OPTIONAL)
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
rem ------------------------------------------------------------------
rem  Step 7 (OPTIONAL) : codex CLI  -  npm install -g @openai/codex
rem  Only needed for image mode A (codex-generated PNG illustrations in
rem  tabs 2-6). Without it the kit falls back to mode B (Claude-drawn SVG),
rem  so you can skip this file entirely.
rem  Requires an OpenAI account for "codex login" afterwards.
rem  ASCII-only on purpose (cmd.exe parses .bat in the OEM code page).
rem ------------------------------------------------------------------
echo.
echo === Step 7 (OPTIONAL): Install codex CLI ===
echo   codex is only used to draw PNG illustrations ^(image mode A^).
echo   If you skip it, Claude draws SVG diagrams instead ^(image mode B^).
echo   You will also need an OpenAI account to run  codex login.
echo.

where codex >nul 2>nul
if not errorlevel 1 (
  for /f "tokens=*" %%v in ('call codex --version 2^>nul') do set "CXV=%%v"
  echo [OK] already installed: !CXV!
  echo      If you have not logged in yet, open a terminal and run:  codex login
  echo.
  pause
  exit /b 0
)

where npm >nul 2>nul
if errorlevel 1 (
  if exist "%ProgramFiles%\nodejs\npm.cmd" set "PATH=%ProgramFiles%\nodejs;%PATH%"
  if exist "%APPDATA%\npm" set "PATH=%APPDATA%\npm;%PATH%"
)
where npm >nul 2>nul
if errorlevel 1 (
  echo [FAIL] npm not found. Double-click 2_install_node_and_claude.bat first
  echo      ^(if you just ran it, CLOSE that window and open this file again^).
  echo.
  pause
  exit /b 1
)

echo Installing:  npm install -g @openai/codex
echo.
call npm install -g @openai/codex
set "RC=!ERRORLEVEL!"
echo.
if not "!RC!"=="0" (
  echo [FAIL] npm returned error code !RC!.
  echo      Check your internet connection and run this file again.
  echo      ^(This step is optional - you can skip it.^)
  echo.
  pause
  exit /b 1
)

if exist "%APPDATA%\npm" set "PATH=%APPDATA%\npm;%PATH%"
where codex >nul 2>nul
if errorlevel 1 (
  echo [OK] npm finished. codex should now be installed.
  echo      CLOSE this window, open a new terminal ^(cmd^) and run:  codex login
) else (
  for /f "tokens=*" %%v in ('call codex --version 2^>nul') do set "CXV=%%v"
  echo [OK] codex installed: !CXV!
  echo      Now log in yourself: open a terminal ^(cmd^) and run:  codex login
  echo      ^(a browser window opens - use your OpenAI account^)
)
echo.
pause
exit /b 0
