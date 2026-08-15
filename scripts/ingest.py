"""Standalone entry point for indexing: ``python scripts/ingest.py``.

Deliberately empty of logic. It invokes the same command the CLI exposes, so
there is one implementation of indexing and one way its errors are reported —
a second copy here would drift the day one of them gains a flag.
"""

from __future__ import annotations

from assistant.cli import app

if __name__ == "__main__":
    app(["ingest"])
