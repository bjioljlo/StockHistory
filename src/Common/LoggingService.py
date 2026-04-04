import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional
from enum import Enum

from src.Common.ConfigService import get_config


class LogLevel(Enum):
    """Log levels enumeration"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LoggingService:
    """
    Unified logging service for the application.
    Provides centralized logging configuration with both console and file outputs.
    """
    _instance: Optional['LoggingService'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls) -> 'LoggingService':
        if cls._instance is None:
            cls._instance = super(LoggingService, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing purposes)"""
        cls._instance = None
        cls._logger = None

    def _initialize_logger(self) -> None:
        """Initialize logger with configuration from ConfigService"""
        config = get_config()
        
        self._logger = logging.getLogger('stockhistory')
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False
        
        # Clear existing handlers
        if self._logger.handlers:
            self._logger.handlers.clear()
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_level = config.get('logging.console_level', 'INFO')
        console_handler.setLevel(getattr(logging, console_level.upper(), logging.INFO))
        self._logger.addHandler(console_handler)
        
        # File handler (rotating)
        log_file = config.get('logging.file_path', 'logs/stockhistory.log')
        max_bytes = config.get('logging.max_file_size', 10 * 1024 * 1024)  # 10MB
        backup_count = config.get('logging.backup_count', 5)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        file_level = config.get('logging.file_level', 'DEBUG')
        file_handler.setLevel(getattr(logging, file_level.upper(), logging.DEBUG))
        self._logger.addHandler(file_handler)

    def log(self, level: LogLevel, message: str, *args, **kwargs) -> None:
        """Log a message with specified level"""
        if self._logger is not None:
            self._logger.log(level.value, message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message"""
        self.log(LogLevel.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message"""
        self.log(LogLevel.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message"""
        self.log(LogLevel.WARNING, message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message"""
        self.log(LogLevel.ERROR, message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message"""
        self.log(LogLevel.CRITICAL, message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> None:
        """Log exception with traceback"""
        if self._logger is not None:
            self._logger.exception(message, *args, **kwargs)

    def get_logger(self) -> logging.Logger:
        """Get underlying logger instance"""
        return self._logger


# Convenience functions for easy import and usage
def get_logger() -> LoggingService:
    return LoggingService()


def debug(message: str, *args, **kwargs) -> None:
    get_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs) -> None:
    get_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs) -> None:
    get_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs) -> None:
    get_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs) -> None:
    get_logger().critical(message, *args, **kwargs)


def exception(message: str, *args, **kwargs) -> None:
    get_logger().exception(message, *args, **kwargs)
