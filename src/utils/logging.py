import sys
from loguru import logger
from ..config.settings import config


def setup_logging():
    """Cấu hình logging cho hệ thống"""

    # Remove default handler
    logger.remove()

    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=config.LOG_LEVEL,
        colorize=True
    )

    # File handler
    logger.add(
        config.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=config.LOG_LEVEL,
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )

    logger.info("Logging system initialized")


def get_logger(name: str):
    """Lấy logger instance cho module"""
    return logger.bind(name=name)
