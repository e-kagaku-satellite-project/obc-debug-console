setlocal enabledelayedexpansion
cd %~dp0

pyinstaller -wF main.py --onefile --noconsole
@REM  --icon="./resource/rpos_icon.ico"
copy dist\main.exe obc-debug-console.exe