@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Paper Review Kit - Step 1 (Python)
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
rem ------------------------------------------------------------------
rem  Step 1 : install Python 3.12 (user install, added to PATH).
rem  Skips if a Python >= 3.10 is already usable.
rem  ASCII-only on purpose (cmd.exe parses .bat in the OEM code page).
rem ------------------------------------------------------------------
echo.
echo === Step 1/4: Install Python ===
echo.

set "MANUAL_URL=https://www.python.org/downloads/"

rem ---- already installed? ------------------------------------------------
call :find_python
if defined PYCMD (
  for /f "tokens=*" %%v in ('!PYCMD! --version 2^>^&1') do set "PYV=%%v"
  echo [OK] already installed: !PYV!  ^(command: !PYCMD!^)
  echo      Next: double-click 2_install_node_and_claude.bat
  echo.
  pause
  exit /b 0
)

rem ---- need winget ---------------------------------------------------------
where winget >nul 2>nul
if errorlevel 1 (
  echo [FAIL] winget is not available on this PC, so Python cannot be installed automatically.
  echo.
  echo   Manual install:
  echo     1. Open  %MANUAL_URL%  and download "Python 3.12" for Windows.
  echo     2. Run the installer. On the FIRST screen, CHECK the box
  echo        "Add python.exe to PATH"  before clicking "Install Now".
  echo     3. Close this window, then double-click 0_check.bat to confirm,
  echo        and continue with 2_install_node_and_claude.bat.
  echo.
  pause
  exit /b 1
)

echo Installing Python 3.12 with winget (a progress window may appear)...
echo.
call winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements --override "/passive InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo [FAIL] winget returned error code %RC%.
  echo.
  echo   Manual install:
  echo     1. Open  %MANUAL_URL%  and download "Python 3.12" for Windows.
  echo     2. Run the installer. On the FIRST screen, CHECK the box
  echo        "Add python.exe to PATH"  before clicking "Install Now".
  echo     3. Close this window, then double-click 0_check.bat to confirm.
  echo.
  pause
  exit /b 1
)

rem ---- make the new install visible in THIS window ----------------------
rem  The installer adds Python to the user PATH in the registry, but an
rem  already-open cmd window does not see it. Add the known install folder
rem  directly so we can verify right now.
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
  set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
)
call :find_python
if defined PYCMD (
  for /f "tokens=*" %%v in ('!PYCMD! --version 2^>^&1') do set "PYV=%%v"
  echo [OK] Python installed: !PYV!
  echo      Next: CLOSE this window, then double-click 2_install_node_and_claude.bat
  echo.
  pause
  exit /b 0
)

echo [OK] winget finished. Python should now be installed.
echo      Next: CLOSE this window, then double-click 0_check.bat to confirm,
echo      and continue with 2_install_node_and_claude.bat
echo.
pause
exit /b 0

rem ======================================================================
:find_python
rem  Sets PYCMD to "python" or "py -3" if a Python >= 3.10 is usable.
rem  "-c" is used instead of "--version" because the Windows Store stub
rem  python.exe prints a message and fails - "-c" catches that.
set "PYCMD="
python -c "import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
if not errorlevel 1 (
  set "PYCMD=python"
  goto :eof
)
py -3 -c "import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
if not errorlevel 1 set "PYCMD=py -3"
goto :eof
