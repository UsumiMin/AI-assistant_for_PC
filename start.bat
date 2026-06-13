@echo off
TITLE AI Assistant Quick Launch
cd /d "%~dp0"

echo ====================================================
echo          Launching AI Assistant (Fast Run)
echo ====================================================
echo.

:: 1. Запуск Python бэкенда в отдельном окне
echo [LAUNCH] Starting Python Server...
start "Python Server" cmd /k "venv\Scripts\activate && python main_core.py"

:: Короткая пауза, чтобы сервер успел занять порт 8080
timeout /t 3 /nobreak > nul

:: 2. Запуск Electron фронтенда в отдельном окне
echo [LAUNCH] Starting Electron UI...
start "Electron App" cmd /k "npm start"

echo.
echo [SUCCESS] Both modules triggered! Closing launcher...
timeout /t 2 > nul
exit