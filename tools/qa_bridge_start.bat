@echo off
rem Launcher invoked by the qabridge:// protocol.
rem When the HTML button detects the bridge is off, it opens qabridge://start and
rem Windows runs this .bat to start the bridge. Arg %1 (the qabridge:// URL) is ignored.
rem If port 8787 is already in use, the bridge instance exits by itself.
rem NOTE: ASCII-only on purpose (cmd parses .bat in the OEM codepage).
cd /d "%~dp0.."
start "QA Bridge (close this window to stop)" python "tools\qa_bridge.py" --port 8787
