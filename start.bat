@echo off
REM MockMentor launcher - double-click (or run from cmd) to start the web app.
REM Activates the venv's Python and runs the Flask server, then open
REM http://localhost:5000 in your browser.
REM
REM Requires: venv created (python -m venv venv) with deps installed
REM (pip install -r requirements.txt), Ollama running with qwen3:8b pulled,
REM and a built chroma_db/ (python src\embed_store.py once).

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
echo   Starting MockMentor  ^-^>  http://localhost:5000
echo ============================================
echo.

venv\Scripts\python.exe src\server.py

pause
