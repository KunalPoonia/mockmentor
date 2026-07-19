"""
Shared pytest setup for MockMentor tests.

The project uses flat imports inside src/ (e.g. `from embed_store import ...`),
which resolve when a script is run from src/. For pytest we put src/ on
sys.path here so tests can do the same flat imports.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
