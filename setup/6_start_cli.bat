@echo off
setlocal EnableExtensions
title Paper Review Kit - Claude Code (CLI)
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
rem ------------------------------------------------------------------
rem  Everyday launcher for CLI mode: opens Claude Code in the kit root
rem  so CLAUDE.md / rules / prompts are loaded automatically.
rem  ASCII-only on purpose (cmd.exe parses .bat in the OEM code page).
rem ------------------------------------------------------------------
echo.
echo === Paper Review Kit - start Claude Code (CLI) ===
echo Kit root: %CD%
echo.

where claude >nul 2>nul
if errorlevel 1 (
  if exist "%USERPROFILE%\.local\bin\claude.exe" set "PATH=%USERPROFILE%\.local\bin;%PATH%"
  if exist "%APPDATA%\npm\claude.cmd" set "PATH=%APPDATA%\npm;%PATH%"
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

echo Paste the prompt from GUIDE.html section 4, then press Enter.
echo ^(to quit Claude later: type  /exit  and press Enter^)
echo.
call claude
echo.
echo [OK] Claude Code session ended. Double-click 6_start_cli.bat to start again.
echo.
pause
exit /b 0
