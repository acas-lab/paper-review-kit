@echo off
rem Launcher invoked by the qabridge:// protocol.
rem When the HTML button detects the bridge is off, it opens qabridge://start and
rem Windows runs this .bat to start the bridge. Arg %1 (the qabridge:// URL) is ignored.
rem If port 8787 is already in use, the bridge instance exits by itself.
rem Interpreter: "python" (3.10+) on PATH, else the "py -3" launcher (python.org installer default).
rem NOTE: ASCII-only on purpose (cmd parses .bat in the OEM codepage).
cd /d "%~dp0.."
rem Run a real version check, not "where": the Microsoft Store "python" stub is on
rem PATH but only opens the Store, so "where python" alone picks a broken interpreter.
python -c "import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
if %errorlevel%==0 (
  start "QA Bridge (close this window to stop)" python "tools\qa_bridge.py" --port 8787
  goto :eof
)
py -3 -c "import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
if %errorlevel%==0 (
  start "QA Bridge (close this window to stop)" py -3 "tools\qa_bridge.py" --port 8787
  goto :eof
)
echo [qa_bridge] Python not found. Install Python 3 or run setup\1_install_python.bat
pause
