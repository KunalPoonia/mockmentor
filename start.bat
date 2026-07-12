@echo off
REM MockMentor launcher - double-click (or run from cmd) to start the project.
REM Activates the venv and hands off to run.py, which lets you pick the UI:
REM   1) Streamlit UI      (classic dashboard)
REM   2) Liquid-glass web  (custom Flask single-page app)
REM
REM Requires: venv already created (python -m venv venv) with dependencies
REM installed (pip install -r requirements.txt), and Ollama running with
REM qwen3:8b pulled.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo.
    echo [MockMentor] Virtual environment not found at venv\Scripts\python.exe
    echo Set it up first:
    echo     python -m venv venv
    echo     venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Starting MockMentor...
echo ============================================
echo.

venv\Scripts\python.exe run.py %*

pause
