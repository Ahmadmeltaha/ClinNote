"""
Shared Utilities: Logging Configuration

Sets up consistent logging across all ClinNote pipeline stages.
Logs are written to both the console and a rotating file in outputs/logs/.

Usage:
    from src.utils.logger import setup_logger
    logger = setup_logger(__name__)
    logger.info("Stage 1: Loading data ...")
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from configs.paths import PATHS
from configs.pipeline_config import PIPELINE_CFG


def setup_logger(
    name: str,
    level: str = PIPELINE_CFG.logging.level,
    log_to_file: bool = PIPELINE_CFG.logging.log_to_file,
    log_filename: str = PIPELINE_CFG.logging.log_filename,
) -> logging.Logger:
    """
    Create and configure a named logger with console and file handlers.

    Parameters
    ----------
    name : str
        Logger name, typically __name__ of the calling module.
    level : str
        Log level: "DEBUG", "INFO", "WARNING", "ERROR".
    log_to_file : bool
        Whether to also write logs to a rotating file.
    log_filename : str
        Filename for the log file (written to outputs/logs/).

    Returns
    -------
    logging.Logger
        Configured logger instance.

    Example
    -------
    >>> logger = setup_logger(__name__)
    >>> logger.info("Pipeline started.")
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid adding duplicate handlers if the logger already exists
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (rotating, max 10MB per file, keep 5 backups)
    if log_to_file:
        PATHS.ensure_output_dirs()
        log_path = PATHS.logs_dir / log_filename
        file_handler = RotatingFileHandler(
            log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
