setlocal enabledelayedexpansion
cd %~dp0

pyinstaller -wF main.py --onefile --noconsole --icon="./img/icon.ico"

copy dist\main.exe obc-debug-console.exe

paused