"""Structured logging helpers (stub)."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Any


def log(event: str, **fields: Any) -> None:
    rec = {"ts": datetime.utcnow().isoformat() + "Z", "event": event}
    rec.update(fields)
    sys.stdout.write(json.dumps(rec) + "\n")
    sys.stdout.flush()


__all__ = ["log"]

