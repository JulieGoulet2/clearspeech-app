"""
Pytest configuration.

This file adds the project root to sys.path so tests can import local files
such as logic.py and app.py.
"""

import sys
from pathlib import Path

# Project root = parent of the tests folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))