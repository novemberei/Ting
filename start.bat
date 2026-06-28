@echo off
cd /d "%~dp0"
set "PATH=%~dp0.pixi\envs\default\Library\bin;%PATH%"
start "" ".pixi\envs\default\python.exe" main.py
