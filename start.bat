@echo off
setlocal enabledelayedexpansion
REM ============================================================================
REM  MockMentor launcher (self-bootstrapping)
REM  Double-click, or run from cmd. On first run it sets everything up for you:
REM    1. Creates the virtual environment if it's missing.
REM    2. Installs Python dependencies if any are missing.
REM    3. Warns (doesn't crash) if the ChromaDB store or Ollama aren't ready.
REM    4. Starts the Flask web app -> http://localhost:5000
REM
REM  Two things this script CAN'T install for you (external to Python):
REM    - Ollama, with qwen3:8b pulled   (https://ollama.com  then: ollama pull qwen3:8b)
REM    - data\raw\ostep.pdf             (gitignored for copyright; see data\raw\README.md)
REM ============================================================================

cd /d "%~dp0"

REM --- 1. Make sure we have a Python to build the venv with --------------------
where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo [MockMentor] Python was not found on your PATH.
    echo Install Python 3.11+ from https://www.python.org/downloads/
    echo ^(tick "Add Python to PATH" in the installer^), then run this again.
    echo.
    pause
    exit /b 1
)

REM --- 2. Create the virtual environment if it doesn't exist -------------------
if not exist "venv\Scripts\python.exe" (
    echo.
    echo [MockMentor] No virtual environment found - creating one at .\venv ...
    python -m venv venv
    if errorlevel 1 (
        echo [MockMentor] Failed to create the virtual environment.
        pause
        exit /b 1
    )
    echo [MockMentor] Virtual environment created.
)

set "VENV_PY=venv\Scripts\python.exe"

REM --- 3. Install dependencies only if something is missing --------------------
REM Quick import probe of the core packages. If any fail, (re)install from
REM requirements.txt. This keeps normal runs fast (no reinstall every launch).
"%VENV_PY%" -c "import flask, chromadb, sentence_transformers, pypdf, ollama" >nul 2>nul
if errorlevel 1 (
    echo.
    echo [MockMentor] Installing dependencies from requirements.txt ...
    echo             ^(first run only - this can take a few minutes^)
    "%VENV_PY%" -m pip install --upgrade pip >nul
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [MockMentor] Dependency install failed. Check the messages above.
        pause
        exit /b 1
    )
    echo [MockMentor] Dependencies installed.
)

REM --- 4. Non-fatal readiness checks ------------------------------------------
REM 4a. Vector store built? The app needs chroma_db/ (run embed_store.py once).
if not exist "chroma_db" (
    echo.
    echo [MockMentor] NOTE: no chroma_db\ found - the vector store isn't built yet.
    echo             Build it once with:  "%VENV_PY%" src\embed_store.py
    echo             ^(the OS subject needs data\raw\ostep.pdf in place first^)
    echo             The app will still start, but grading won't work until this is done.
    echo.
)

REM 4b. Ollama reachable? Warn if the command isn't even installed.
where ollama >nul 2>nul
if errorlevel 1 (
    echo.
    echo [MockMentor] NOTE: 'ollama' not found on PATH. Grading needs Ollama running
    echo             with qwen3:8b pulled. Install: https://ollama.com  then: ollama pull qwen3:8b
    echo.
)

REM --- 5. Launch ---------------------------------------------------------------
echo.
echo ============================================
echo   Starting MockMentor  ^-^>  http://localhost:5000
echo   ^(Ctrl+C to stop^)
echo ============================================
echo.
echo [MockMentor] Loading the embedding model - this takes ~10-15 seconds on
echo             the first start. Your browser will open automatically when the
echo             server is ready. Please wait...
echo.

REM Open the browser automatically once the server has had time to load the
REM model and start listening. This runs in a detached child so it fires while
REM the (blocking) server call below keeps the window alive. If the page shows
REM "can't connect" for a second, just refresh - the server is still loading.
start "" /b cmd /c "timeout /t 15 >nul & start "" http://localhost:5000"

"%VENV_PY%" src\server.py

pause
endlocal
