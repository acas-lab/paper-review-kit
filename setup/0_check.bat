@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Paper Review Kit - Step 0 (check only)
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
rem ------------------------------------------------------------------
rem  Step 0 : check which tools are installed. Installs NOTHING.
rem  ASCII-only on purpose (cmd.exe parses .bat in the OEM code page).
rem ------------------------------------------------------------------
echo.
echo === Step 0: Check what is installed (nothing is installed here) ===
echo Kit root: %CD%
echo.

set "NEED1=0"
set "NEED2=0"
set "NEED3=0"
set "NEED4=0"
set "PYCMD="

rem ---- winget --------------------------------------------------------
where winget >nul 2>nul
if errorlevel 1 (
  echo [ -- ] winget      : not found  ^(installers will show manual download URLs^)
) else (
  for /f "tokens=*" %%v in ('winget --version 2^>nul') do set "WGV=%%v"
  echo [ OK ] winget      : !WGV!
)

rem ---- git (optional) ------------------------------------------------
where git >nul 2>nul
if errorlevel 1 (
  echo [ -- ] git         : not found  ^(optional - only needed for "git clone"^)
) else (
  for /f "tokens=*" %%v in ('git --version 2^>nul') do set "GITV=%%v"
  echo [ OK ] git         : !GITV!
)

rem ---- python ----------------------------------------------------------
rem  "python -c" is used instead of "python --version" because the Windows
rem  Store stub python.exe prints a message and fails - "-c" catches that.
python -c "import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
if not errorlevel 1 (
  set "PYCMD=python"
) else (
  py -3 -c "import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
  if not errorlevel 1 set "PYCMD=py -3"
)
if defined PYCMD (
  for /f "tokens=*" %%v in ('%PYCMD% --version 2^>^&1') do set "PYV=%%v"
  echo [ OK ] python      : !PYV!  ^(command: %PYCMD%^)
) else (
  echo [ NO ] python      : not found or older than 3.10  --^> run 1_install_python.bat
  set "NEED1=1"
)

rem ---- node / npm ------------------------------------------------------
where node >nul 2>nul
if errorlevel 1 (
  echo [ NO ] node        : not found  --^> run 2_install_node_and_claude.bat
  set "NEED2=1"
) else (
  for /f "tokens=*" %%v in ('node --version 2^>nul') do set "NODEV=%%v"
  echo [ OK ] node        : !NODEV!
)
where npm >nul 2>nul
if errorlevel 1 (
  echo [ NO ] npm         : not found  --^> run 2_install_node_and_claude.bat
  set "NEED2=1"
) else (
  for /f "tokens=*" %%v in ('call npm --version 2^>nul') do set "NPMV=%%v"
  echo [ OK ] npm         : !NPMV!
)

rem ---- claude ----------------------------------------------------------
where claude >nul 2>nul
if errorlevel 1 (
  echo [ NO ] claude      : not found  --^> run 2_install_node_and_claude.bat
  set "NEED2=1"
  set "NEED3=1"
) else (
  for /f "tokens=*" %%v in ('call claude --version 2^>nul') do set "CLV=%%v"
  echo [ OK ] claude      : !CLV!
  if exist "%USERPROFILE%\.claude\.credentials.json" (
    echo [ OK ] claude login: credentials file found
  ) else (
    echo [ NO ] claude login: NOT logged in  --^> run 3_login_claude.bat
    set "NEED3=1"
  )
)

rem ---- kit python packages (CLI mode) -----------------------------------
if defined PYCMD (
  %PYCMD% -c "import fitz" >nul 2>nul
  if errorlevel 1 (
    echo [ NO ] pymupdf     : not installed  --^> run 4_install_kit_packages.bat
    set "NEED4=1"
  ) else (
    echo [ OK ] pymupdf     : installed
  )
  %PYCMD% -c "import playwright" >nul 2>nul
  if errorlevel 1 (
    echo [ NO ] playwright  : not installed  --^> run 4_install_kit_packages.bat
    set "NEED4=1"
  ) else (
    echo [ OK ] playwright  : installed
  )
) else (
  echo [ NO ] pymupdf     : skipped ^(python missing^)  --^> run 4_install_kit_packages.bat after step 1
  echo [ NO ] playwright  : skipped ^(python missing^)  --^> run 4_install_kit_packages.bat after step 1
  set "NEED4=1"
)

rem ---- codex (optional) -------------------------------------------------
where codex >nul 2>nul
if errorlevel 1 (
  echo [ -- ] codex       : not found  ^(OPTIONAL - image mode A; 7_install_codex_optional.bat^)
) else (
  for /f "tokens=*" %%v in ('call codex --version 2^>nul') do set "CXV=%%v"
  echo [ OK ] codex       : !CXV!  ^(optional^)
)

rem ---- summary -----------------------------------------------------------
echo.
echo ------------------------------------------------------------------
set "TODO="
if "%NEED1%"=="1" set "TODO=%TODO% 1"
if "%NEED2%"=="1" set "TODO=%TODO% 2"
if "%NEED3%"=="1" set "TODO=%TODO% 3"
if "%NEED4%"=="1" set "TODO=%TODO% 4"
if defined TODO (
  echo [TODO] Steps still to run, in this order:%TODO%
  echo        ^(double-click  N_*.bat  for each number above, one at a time^)
) else (
  echo [OK] Everything required is installed.
  echo      Every day: 5_start_web.bat ^(web^)  or  6_start_cli.bat ^(CLI^)
)
echo ------------------------------------------------------------------
echo.
pause
endlocal
exit /b 0
