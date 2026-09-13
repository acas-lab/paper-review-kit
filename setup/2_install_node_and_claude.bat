@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Paper Review Kit - Step 2 (Node.js + Claude Code)
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
rem ------------------------------------------------------------------
rem  Step 2 : install Node.js LTS (if missing), then Claude Code CLI
rem           via  npm install -g @anthropic-ai/claude-code
rem  Safe to run again: already-installed parts are skipped.
rem  ASCII-only on purpose (cmd.exe parses .bat in the OEM code page).
rem
rem  PATH NOTE: a PATH entry added by an installer is written to the
rem  registry, but a cmd window that is ALREADY open keeps its old PATH.
rem  After installing Node we therefore (a) re-read the user + machine
rem  PATH from the registry and (b) add the standard Node folders directly.
rem  If node is still not visible, we ask the user to close this window and
rem  double-click this same file again - the second run then does npm.
rem ------------------------------------------------------------------
echo.
echo === Step 2/4: Install Node.js and Claude Code ===
echo.

set "NODE_URL=https://nodejs.org/"
set "CLAUDE_URL=https://claude.com/claude-code"

rem ======================= part A : Node.js ==============================
where node >nul 2>nul
if not errorlevel 1 (
  for /f "tokens=*" %%v in ('node --version 2^>nul') do set "NODEV=%%v"
  echo [OK] Node.js already installed: !NODEV!
  goto :part_b
)

echo Node.js not found. Installing Node.js LTS with winget...
where winget >nul 2>nul
if errorlevel 1 (
  echo [FAIL] winget is not available, so Node.js cannot be installed automatically.
  echo.
  echo   Manual install:
  echo     1. Open  %NODE_URL%  and download the "LTS" Windows installer ^(.msi^).
  echo     2. Run it with the default options ^(Next, Next, ..., Install^).
  echo     3. Close this window, then double-click THIS file ^(2_install_node_and_claude.bat^)
  echo        again - it will skip Node and install Claude Code.
  echo.
  pause
  exit /b 1
)
echo ^(Windows may ask for permission - click "Yes".^)
echo.
call winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements --silent
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo [FAIL] winget returned error code %RC% while installing Node.js.
  echo.
  echo   Manual install:
  echo     1. Open  %NODE_URL%  and download the "LTS" Windows installer ^(.msi^).
  echo     2. Run it with the default options.
  echo     3. Close this window, then double-click THIS file again.
  echo.
  pause
  exit /b 1
)
echo Node.js installer finished. Refreshing PATH for this window...
call :refresh_path
where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo [OK] Node.js is installed, but this window cannot see it yet.
  echo      CLOSE this window, then double-click THIS SAME file
  echo      ^(2_install_node_and_claude.bat^) once more to install Claude Code.
  echo.
  pause
  exit /b 0
)
for /f "tokens=*" %%v in ('node --version 2^>nul') do set "NODEV=%%v"
echo [OK] Node.js installed: !NODEV!

rem ======================= part B : Claude Code ==========================
:part_b
echo.
where npm >nul 2>nul
if errorlevel 1 call :refresh_path
where npm >nul 2>nul
if errorlevel 1 (
  echo [FAIL] npm was not found even though Node.js is installed.
  echo      CLOSE this window, then double-click THIS SAME file again.
  echo      If it still fails, reinstall Node.js from  %NODE_URL%
  echo.
  pause
  exit /b 1
)

where claude >nul 2>nul
if not errorlevel 1 (
  for /f "tokens=*" %%v in ('call claude --version 2^>nul') do set "CLV=%%v"
  echo [OK] Claude Code already installed: !CLV!
  echo      Next: double-click 3_login_claude.bat
  echo.
  pause
  exit /b 0
)

echo Installing Claude Code:  npm install -g @anthropic-ai/claude-code
echo ^(this downloads a few MB - please wait^)
echo.
call npm install -g @anthropic-ai/claude-code
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo [FAIL] npm returned error code %RC%.
  echo      Check your internet connection and run this file again.
  echo      Alternative installer / docs:  %CLAUDE_URL%
  echo.
  pause
  exit /b 1
)

rem npm puts global commands in %APPDATA%\npm - make sure this window sees it
if exist "%APPDATA%\npm" set "PATH=%APPDATA%\npm;%PATH%"
where claude >nul 2>nul
if errorlevel 1 (
  echo [OK] npm finished. Claude Code should now be installed.
  echo      CLOSE this window, then double-click 0_check.bat to confirm,
  echo      and continue with 3_login_claude.bat
  echo.
  pause
  exit /b 0
)
for /f "tokens=*" %%v in ('call claude --version 2^>nul') do set "CLV=%%v"
echo [OK] Claude Code installed: !CLV!
echo      Next: CLOSE this window, then double-click 3_login_claude.bat
echo.
pause
exit /b 0

rem ======================================================================
:refresh_path
rem  Re-read PATH from the registry (machine + user) and append it to the
rem  PATH of this window, then add the standard Node / npm / Claude folders.
rem  "call set" is used so that %SystemRoot%-style entries stored in the
rem  registry (REG_EXPAND_SZ) get expanded a second time.
set "REG_SYS="
set "REG_USR="
for /f "skip=2 tokens=1,2,*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do if /i "%%a"=="Path" set "REG_SYS=%%c"
for /f "skip=2 tokens=1,2,*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do if /i "%%a"=="Path" set "REG_USR=%%c"
if defined REG_SYS call set "PATH=%%PATH%%;%%REG_SYS%%"
if defined REG_USR call set "PATH=%%PATH%%;%%REG_USR%%"
rem  one more pass so %SystemRoot%-style entries inside the value get expanded
call set "PATH=%PATH%"
if exist "%ProgramFiles%\nodejs\node.exe" set "PATH=%ProgramFiles%\nodejs;%PATH%"
if exist "%APPDATA%\npm" set "PATH=%APPDATA%\npm;%PATH%"
if exist "%USERPROFILE%\.local\bin" set "PATH=%USERPROFILE%\.local\bin;%PATH%"
goto :eof
