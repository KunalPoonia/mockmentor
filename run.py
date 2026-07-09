"""
MockMentor launcher - the "switch" between the two front ends.

There are two UIs over the *same* local RAG pipeline (retrieve -> grade ->
follow-up):

  1) Streamlit UI      (src/app.py)     - clean, classic dashboard look
  2) Liquid-glass web  (src/server.py)  - the custom Flask single-page app

Pick whichever you want to show. Usage from the project root (inside the venv):

    python run.py                 # interactive menu - pick 1 or 2
    python run.py streamlit       # go straight to the Streamlit UI
    python run.py web             # go straight to the liquid-glass web UI

Only one runs at a time. To switch, stop it (Ctrl+C) and run this again.
Both need Ollama running (qwen3:8b) and a built chroma_db/.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable  # the venv's python, so imports/streamlit resolve correctly

STREAMLIT_ALIASES = {"1", "streamlit", "st", "app"}
WEB_ALIASES = {"2", "web", "flask", "glass", "server"}


def run_streamlit():
    print("\n-> Starting the Streamlit UI  (http://localhost:8501)\n")
    subprocess.run([PY, "-m", "streamlit", "run", str(ROOT / "src" / "app.py")])


def run_web():
    print("\n-> Starting the liquid-glass web UI  (http://localhost:5000)\n")
    subprocess.run([PY, str(ROOT / "src" / "server.py")])


def choose_interactively():
    print("=" * 52)
    print("  MockMentor - which UI do you want to start?")
    print("=" * 52)
    print("  1) Streamlit UI       (classic dashboard)")
    print("  2) Liquid-glass web   (custom Flask single-page app)")
    print("-" * 52)
    return input("Enter 1 or 2 (or 'q' to quit): ").strip().lower()


def main():
    # Accept the choice from the command line, or ask for it.
    choice = sys.argv[1].strip().lower() if len(sys.argv) > 1 else choose_interactively()

    if choice in {"q", "quit", "exit"}:
        return
    if choice in STREAMLIT_ALIASES:
        run_streamlit()
    elif choice in WEB_ALIASES:
        run_web()
    else:
        print(f"Unknown option: {choice!r}. Use 1/streamlit or 2/web.")
        sys.exit(1)


if __name__ == "__main__":
    main()
