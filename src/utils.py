"""Utility functions and helpers for the Tessie MCP server.

This module provides logging setup, formatting helpers, and other utility
functions used throughout the application.
"""

import logging
import sys
from typing import Optional

from .constants import LOG_FORMAT, LOG_DATE_FORMAT


def setup_logging(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """Configure and return a logger with consistent formatting.

    Args:
        name: Logger name (typically __name__ from the calling module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging(__name__)
        >>> logger.info("Server started")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def format_timestamp(timestamp: int) -> str:
    """Format a Unix timestamp as a human-readable date string.

    Args:
        timestamp: Unix timestamp (seconds since epoch)

    Returns:
        Formatted date string in YYYY-MM-DD HH:MM:SS format

    Example:
        >>> format_timestamp(1710785350)
        '2024-03-18 15:15:50'
    """
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def validate_vin(vin: str) -> bool:
    """Validate that a VIN appears to be in the correct format.

    VINs are 17 characters long and contain only alphanumeric characters
    (excluding I, O, and Q to avoid confusion with 1 and 0).

    Args:
        vin: Vehicle Identification Number to validate

    Returns:
        True if VIN appears valid, False otherwise

    Example:
        >>> validate_vin("5YJ3E1EA1KF123456")
        True
        >>> validate_vin("INVALID")
        False
    """
    if not isinstance(vin, str):
        return False

    if len(vin) != 17:
        return False

    # VINs should only contain alphanumeric characters
    # (excluding I, O, Q, but we'll be lenient)
    return vin.isalnum()


def sanitize_vin_for_logging(vin: str) -> str:
    """Sanitize VIN for logging to protect privacy.

    Shows first 5 and last 4 characters, masks the middle.

    Args:
        vin: Vehicle Identification Number

    Returns:
        Sanitized VIN suitable for logging

    Example:
        >>> sanitize_vin_for_logging("5YJ3E1EA1KF123456")
        '5YJ3E****3456'
    """
    if not vin or len(vin) < 9:
        return "***INVALID_VIN***"

    return f"{vin[:5]}****{vin[-4:]}"


def format_duration(minutes: float) -> str:
    """Format a duration in minutes as a human-readable string.

    Args:
        minutes: Duration in minutes

    Returns:
        Formatted duration string

    Example:
        >>> format_duration(125.5)
        '2h 5m'
        >>> format_duration(45)
        '45m'
    """
    if minutes == 0:
        return "0m"

    hours = int(minutes // 60)
    mins = int(minutes % 60)

    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def get_compass_direction(heading: int) -> str:
    """Convert a heading in degrees to a compass direction.

    Args:
        heading: Heading in degrees (0-359, where 0 is North)

    Returns:
        Compass direction (N, NE, E, SE, S, SW, W, NW)

    Example:
        >>> get_compass_direction(45)
        'NE'
        >>> get_compass_direction(180)
        'S'
    """
    from .constants import COMPASS_DIRECTIONS, DEGREES_PER_DIRECTION

    idx = round(heading / DEGREES_PER_DIRECTION) % len(COMPASS_DIRECTIONS)
    return COMPASS_DIRECTIONS[idx]


def safe_get(data: dict, *keys, default=None):
    """Safely get a nested value from a dictionary.

    Args:
        data: Dictionary to search
        *keys: Sequence of keys to traverse
        default: Default value if key path doesn't exist

    Returns:
        Value at the key path, or default if not found

    Example:
        >>> data = {"a": {"b": {"c": 123}}}
        >>> safe_get(data, "a", "b", "c")
        123
        >>> safe_get(data, "a", "x", "y", default=0)
        0
    """
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data
