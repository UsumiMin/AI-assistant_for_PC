@echo off
taskkill /F /IM python.exe /T
taskkill /F /IM electron.exe /T
echo All processes stopped
pause