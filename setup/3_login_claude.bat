@echo off
setlocal EnableExtensions
title Paper Review Kit - Step 3 (Claude login)
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
rem ------------------------------------------------------------------
rem  Step 3 : log in to Claude Code once (subscription account).
rem  Runs "claude" interactively in the kit root, then checks that the
rem  credentials file exists.
rem  ASCII-only on purpose (cmd.exe parses .bat in the OEM code page).
rem ------------------------------------------------------------------
echo.
echo === Step 3/4: Log in to Claude Code ===
echo.

set "CREDS=%USERPROFILE%\.claude\.credentials.json"

where claude >nul 2>nul
if errorlevel 1 (
  if exist "%USERPROFILE%\.local\bin\claude.exe" set "PATH=%USERPROFILE%\.local\bin;%PATH%"
  if exist "%APPDATA%\npm\claude.cmd" set "PATH=%APPDATA%\npm;%PATH%"
)
where claude >nul 2>nul
if errorlevel 1 (
  echo [FAIL] "claude" command not found.
  echo      Double-click 2_install_node_and_claude.bat first
  echo      ^(if you just ran it, CLOSE that window and open this file again^).
  echo.
  pause
  exit /b 1
)

if exist "%CREDS%" (
  echo [OK] already logged in ^(credentials file found^).
  echo      If you want to switch accounts, type  /login  inside Claude.
  echo.
  echo      Next: double-click 4_install_kit_packages.bat
  echo.
  pause
  exit /b 0
)

echo A browser window will open. Log in with your Claude subscription account.
echo When you see the Claude prompt in this window, type  /exit  and press Enter.
echo.
echo   ^(If a theme / trust question appears first, just press Enter.^)
echo.
pause

call claude
echo.

if exist "%CREDS%" (
  echo [OK] Logged in - credentials file found.
  echo      Next: double-click 4_install_kit_packages.bat
) else (
  echo [FAIL] NOT logged in - credentials file was not created.
  echo      Double-click this file again and complete the browser login,
  echo      then type  /exit  in the Claude prompt.
  echo.
  pause
  exit /b 1
)
echo.
pause
exit /b 0
