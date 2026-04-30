"""Vercel serverless entry point.

Vercel detects the `app` symbol and routes all matching requests to it.
The actual Flask app lives in `web/server.py`; this file just makes it
importable from the conventional `api/` directory.
"""

import sys
from pathlib import Path

# Make the project root importable from the serverless function.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web.server import app  # noqa: E402,F401
