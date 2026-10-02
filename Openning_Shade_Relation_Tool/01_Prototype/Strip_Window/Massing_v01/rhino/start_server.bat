@echo off
rem Massing_v01: start the local bridge (page <-> state.json) on http://localhost:8768 and open the massing tool
cd /d "%~dp0"
python server.py
pause
