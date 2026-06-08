#!/usr/bin/env python3
"""Фоновый worker export-задач (production: EXPORT_INLINE=false)."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.services.exports.export_service import ExportService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("export-worker")

POLL_SECONDS = 2


def main() -> None:
    settings = get_settings()
    if settings.export_inline:
        logger.error("EXPORT_INLINE=true — worker не нужен, выход")
        raise SystemExit(1)
    if not settings.redis_url:
        logger.error("REDIS_URL обязателен для export-worker")
        raise SystemExit(1)

    logger.info("Export worker started (poll=%ss)", POLL_SECONDS)
    while True:
        try:
            n = ExportService.process_pending(limit=5)
            if n:
                logger.info("Dispatched %s task(s)", n)
        except Exception:
            logger.exception("Worker loop error")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
