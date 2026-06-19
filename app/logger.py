import logging

from rich.console import Console
from rich.logging import RichHandler


def get_logger_for_crawler(name: str) -> logging.Logger:
    # Configure logging to use stderr
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        stderr_console = Console(stderr=True)
        handler = RichHandler(console=stderr_console, rich_tracebacks=True)
        logger.addHandler(handler)
    return logger


def get_logger_for_mcp_server(name: str) -> logging.Logger:
    # Configure logging to use stderr
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        stderr_console = Console(stderr=True)
        handler = RichHandler(console=stderr_console, rich_tracebacks=True)
        logger.addHandler(handler)
    return logger


def get_logging_for_fastapi() -> logging.Logger:
    # logging.getLogger("uvicorn.access").disabled = True
    logger = logging.getLogger("fastapi")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = RichHandler(rich_tracebacks=True)
        logger.addHandler(handler)
    return logger
