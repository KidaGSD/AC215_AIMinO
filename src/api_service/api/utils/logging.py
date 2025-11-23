from __future__ import annotations

import json
import logging
import os
import sys
import time


def write_jsonl(path: str, payload: dict) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        ts = time.time()
        print(json.dumps({"ts": ts, **payload}), file=sys.stdout)


def configure_logging(level: str | None = None) -> logging.Logger:
    lvl = getattr(logging, (level or os.getenv("AIMINO_LOG_LEVEL", "INFO")).upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )
    logger = logging.getLogger("aimino.api")
    logger.setLevel(lvl)
    return logger
