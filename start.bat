@echo off
TITLE AI Assistant - First Time Full Setup
cd /d "%~dp0"

echo ====================================================
echo      AI Assistant: Initializing Full Project Setup
echo ====================================================
echo.

:: --- БЛОК 1: ОЧИСТКА И СОЗДАНИЕ PYTHON VENV ---
echo [1/6] Cleaning up old python environments...
if exist .venv rmdir /s /q .venv
if exist venv rmdir /s /q venv
if exist uv.lock del /f /q uv.lock

echo [2/6] Creating clean virtual environment (venv)...
python -m venv venv

echo [3/6] Injecting local llama modules...
if exist "llama_cpp" xcopy /E /I /Y "llama_cpp" "venv\Lib\site-packages\llama_cpp\" >nul
if exist "llama_cpp_python-0.3.24.dist-info" xcopy /E /I /Y "llama_cpp_python-0.3.24.dist-info" "venv\Lib\site-packages\llama_cpp_python-0.3.24.dist-info\" >nul

:: --- БЛОК 2: УСТАНОВКА DEPENDENCIES ДЛЯ БЭКЕНДА ---
echo [4/6] Preparing requirements list...
if exist requirements.txt (
    findstr /V /I "llama-cpp-python llama_cpp_python" requirements.txt > requirements_tmp.txt
) else (
    echo. > requirements_tmp.txt
)

echo [5/6] Installing Python dependencies (PIP)...
call venv\Scripts\activate
pip install -r requirements_tmp.txt
pip install pywin32 vosk sentence_transformers
pip install winsdk-1.0.0b10-cp312-cp312-win_amd64.whl
if exist requirements_tmp.txt del /f /q requirements_tmp.txt

:: --- БЛОК 3: УМНАЯ СБОРКА И ЖЕСТКАЯ ИНЖЕКЦИЯ ELECTRON ---
echo [6/6] Hard rebuilding frontend and Electron binary...
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del /f /q package-lock.json

echo [INFO] Cleaning npm hard cache...
call npm cache clean --force

echo [INFO] Installing all dependencies from package.json...
call npm install

echo [INFO] Installing electron wrapper (ignoring buggy postinstalls)...
call npm install electron --save-dev --ignore-scripts

if not exist node_modules\electron\dist mkdir node_modules\electron\dist

echo [INFO] Downloading clean Electron binary directly from mirror...
curl -L -o electron_tmp.zip "https://npmmirror.com/mirrors/electron/28.2.0/electron-v28.2.0-win32-x64.zip"

echo [INFO] Extracting binary archive...
tar -xf electron_tmp.zip -C node_modules\electron\dist\

echo [INFO] Cleaning up temporary zip...
if exist electron_tmp.zip del /f /q electron_tmp.zip

echo [INFO] Generating clean path.txt without hidden carriage returns...
<nul set /p ="electron.exe" > node_modules\electron\path.txt

:: Финальная проверка сборки
if not exist "node_modules\electron\dist\electron.exe" (
    echo [ERROR] Critical Error: Electron binary injection failed! Check internet connection.
    pause
    exit
)
echo [SUCCESS] Electron is fully injected and ready!

:: --- БЛОК 4: ЗАПУСК ПРИЛОЖЕНИЯ ---
echo.
echo ====================================================
echo          Launching Application Modules
echo ====================================================
echo.

echo [LAUNCH] Starting Python Server...
start "Python Server" cmd /k "venv\Scripts\activate && python main_core.py"

echo Waiting for server stability...
timeout /t 4 /nobreak > nul

echo [LAUNCH] Starting Electron UI...
start "Electron App" cmd /k "npm start"

echo.
echo [SUCCESS] First launch completed successfully!
echo Use your short 'Fast Run' bat script for all subsequent launches.
timeout /t 3 > nul
exit