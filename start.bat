@echo off
TITLE AI Assistant

echo Starting AI Assistant...
echo Starting Python server...
start "Python Server" cmd /k "venv\Scripts\activate && python main_core.py"
timeout /t 2 /nobreak > nul
echo Starting Electron app...
start "Electron App" cmd /k "npm start"
echo.
echo Both processes started!
echo.
pause