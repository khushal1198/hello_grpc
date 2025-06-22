#!/usr/bin/env python3
"""
Common logging configuration for the gRPC project.
Provides consistent logging setup across all services.
"""

import logging
import sys
from typing import Optional


def setup_root_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    log_to_file: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    Set up root logging configuration so logging.info(), logging.debug(), etc. can be used directly.
    
    Args:
        level: Logging level (default: INFO)
        format_string: Custom format string for log messages
        log_to_file: Whether to log to file in addition to console
        log_file: Path to log file (if log_to_file is True)
    """
    # Default format if none provided
    if format_string is None:
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=[]
    )
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)
    
    # Add console handler to root logger
    root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file and log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def setup_logging(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    log_to_file: bool = False,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration for a service.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
        format_string: Custom format string for log messages
        log_to_file: Whether to log to file in addition to console
        log_file: Path to log file (if log_to_file is True)
    
    Returns:
        Configured logger instance
    """
    # Default format if none provided
    if format_string is None:
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file and log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    Uses default configuration if not already set up.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger doesn't have handlers, set up default configuration
    if not logger.handlers:
        setup_logging(name)
    
    return logger


# Convenience function for quick debug logging
def debug_log(logger: logging.Logger, message: str, **kwargs):
    """
    Log debug message with optional additional context.
    
    Args:
        logger: Logger instance
        message: Debug message
        **kwargs: Additional context to log
    """
    if kwargs:
        context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        logger.debug(f"{message} | {context_str}")
    else:
        logger.debug(message)


# Convenience function for request logging
def log_request(logger_or_module, method: str, path: str, status_code: int = None, **kwargs):
    """
    Log HTTP request details.
    
    Args:
        logger_or_module: Logger instance or logging module
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: Response status code (if available)
        **kwargs: Additional request details
    """
    base_msg = f"{method} {path}"
    if status_code:
        base_msg += f" -> {status_code}"
    
    if kwargs:
        context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{base_msg} | {context_str}"
    else:
        msg = base_msg
    
    # Handle both logger instance and logging module
    if hasattr(logger_or_module, 'info'):
        # It's a logger instance
        logger_or_module.info(msg)
    else:
        # It's the logging module
        logger_or_module.info(msg) 