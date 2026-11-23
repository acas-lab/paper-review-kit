@echo off
rem Launcher invoked by the qabridge:// protocol.
rem When the HTML button detects the bridge is off, it opens qabridge://start and
rem Windows runs this .bat to start the bridge. Arg %1 (the qabridge:// URL) is ignored.
rem If port 8787 is already in use, the bridge instance exits by itself.
rem Interpreter: "python" on PATH, else the "py -3" launcher (python.org installer default).
rem NOTE: ASCII-only on purpose (cmd parses .bat in the OEM codepage).
cd /d "%~dp0.."
where python >nul 2>nul
if %errorlevel%==0 (
  start "QA Bridge (close this window to stop)" python "tools\qa_bridge.py" --port 8787
  goto :eof
)
where py >nul 2>nul
if %errorlevel%==0 (
  start "QA Bridge (close this window to stop)" py -3 "tools\qa_bridge.py" --port 8787
  goto :eof
)
echo [qa_bridge] Python not found. Install Python 3 or run setup\1_install_python.bat
pause
