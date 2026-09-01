import sys
from loguru import logger


logger.remove()

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

logger.add(
    sys.stdout,
    format=LOG_FORMAT,
    level="INFO",
    colorize=True,
    backtrace=True, 
    diagnose=True,   
)

logger.add(
    "logs/app.log",
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="10 MB",
    retention="7 days", 
    compression="zip",   
    encoding="utf-8",
)

__all__ = ["logger"]
