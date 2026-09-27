@echo off
rem Version_07: start the local bridge (page <-> windows.json) on http://localhost:8765 and open the WWR tool
cd /d "%~dp0"
python server.py
pause
