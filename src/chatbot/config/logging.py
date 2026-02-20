import logging
import logging.config
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logging():

    log_filename = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"

    handler = TimedRotatingFileHandler(
        filename=log_filename,
        when="midnight",      # rotate daily
        interval=1,
        backupCount=30,       # keep 30 days logs
        encoding="utf-8"
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
    )

    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Console log also
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
