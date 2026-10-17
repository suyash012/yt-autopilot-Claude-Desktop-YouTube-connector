@echo off
title Sign in to YouTube
set T=%LOCALAPPDATA%\yt-autopilot
if exist "%T%\data\token.json" del "%T%\data\token.json"
"%T%\.venv\Scripts\python.exe" "%T%\server.py" --auth
pause
