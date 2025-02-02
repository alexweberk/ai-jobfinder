import logging
import sys
from typing import Optional


def setup_logger(
    name: Optional[str] = None,
    level: int = logging.INFO,
    format_string: str = "%(asctime)s - %(levelname)s - %(message)s",
) -> logging.Logger:
    """
    Set up and return a logger with the specified configuration.

    Args:
        name: The name of the logger. If None, returns the root logger
        level: The logging level to use
        format_string: The format string for the logger

    Returns:
        A configured logger instance
    """
    # Get the logger
    logger = logging.getLogger(name)

    # Only add handler if the logger doesn't already have handlers
    if not logger.handlers:
        # Create handlers
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(format_string))

        # Add handlers to the logger
        logger.addHandler(console_handler)

        # Set the logging level
        logger.setLevel(level)

    return logger


# Create a default logger instance
logger = setup_logger("ai_jobfinder")
