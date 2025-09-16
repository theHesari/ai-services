"""
Centralized logging configuration for the Content Writer Agent project.
Provides structured logging with different levels and handlers for different components.
"""

import logging
import logging.handlers
import os
import sys
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional


# Utility function for safe Unicode handling
def safe_unicode(text: str) -> str:
    """Ensure text is safe for Windows console output"""
    if platform.system() == "Windows":
        # Replace common emojis with ASCII alternatives
        emoji_replacements = {
            "🚀": "[START]",
            "📝": "[STEP]",
            "🏁": "[END]",
            "🤖": "[AGENT]",
            "🌐": "[API]",
            "✅": "[OK]",
            "❌": "[ERROR]",
            "💥": "[ERROR]",
            "⏱️": "[PERF]",
            "🎉": "[SUCCESS]",
            "🧪": "[TEST]",
            "📊": "[METRICS]",
            "🎯": "[TARGET]",
            "💡": "[INFO]",
        }

        for emoji, replacement in emoji_replacements.items():
            text = text.replace(emoji, replacement)

    return text


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    # Color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        # Add color to the level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"

        return super().format(record)


class SafeFormatter(logging.Formatter):
    """Safe formatter that handles Unicode characters for Windows compatibility"""

    def format(self, record):
        # Replace Unicode emojis with ASCII alternatives for Windows compatibility
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = safe_unicode(record.msg)

        return super().format(record)


class ContentWriterLogger:
    """Centralized logger configuration for the Content Writer Agent"""

    def __init__(
        self,
        log_level: str = "INFO",
        log_dir: str = "logs",
        enable_console: bool = True,
        enable_file: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        safe_unicode: bool = None,
    ):
        """
        Initialize the logging configuration

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory to store log files
            enable_console: Whether to enable console logging
            enable_file: Whether to enable file logging
            max_file_size: Maximum size of log files before rotation
            backup_count: Number of backup files to keep
            safe_unicode: Whether to use safe Unicode handling (auto-detect if None)
        """
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_dir = Path(log_dir)
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.max_file_size = max_file_size
        self.backup_count = backup_count

        # Auto-detect safe Unicode handling for Windows
        if safe_unicode is None:
            self.safe_unicode = platform.system() == "Windows"
        else:
            self.safe_unicode = safe_unicode

        # Create log directory if it doesn't exist
        if self.enable_file:
            self.log_dir.mkdir(exist_ok=True)

        # Configure root logger
        self._configure_root_logger()

        # Configure component-specific loggers
        self._configure_component_loggers()

    def _configure_root_logger(self):
        """Configure the root logger"""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)

            # Use safe formatter for Windows compatibility, colored for others
            if self.safe_unicode:
                console_formatter = SafeFormatter(
                    fmt="%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            else:
                console_formatter = ColoredFormatter(
                    fmt="%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

        # File handler
        if self.enable_file:
            # Main application log
            app_log_file = (
                self.log_dir / f"content_writer_{datetime.now().strftime('%Y%m%d')}.log"
            )
            app_handler = logging.handlers.RotatingFileHandler(
                app_log_file, maxBytes=self.max_file_size, backupCount=self.backup_count
            )
            app_handler.setLevel(self.log_level)

            # Detailed formatter for file (use safe formatter for consistency)
            file_formatter = SafeFormatter(
                fmt="%(asctime)s | %(name)-20s | %(levelname)-8s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            app_handler.setFormatter(file_formatter)
            root_logger.addHandler(app_handler)

            # Error log file
            error_log_file = (
                self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
            )
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            root_logger.addHandler(error_handler)

    def _configure_component_loggers(self):
        """Configure specific loggers for different components"""

        # Component-specific log levels
        component_levels = {
            "content_writer.agents": logging.INFO,
            "content_writer.workflows": logging.INFO,
            "content_writer.tools": logging.DEBUG,
            "content_writer.integrations": logging.INFO,
            "content_writer.memory": logging.DEBUG,
            "content_writer.models": logging.DEBUG,
        }

        for component, level in component_levels.items():
            logger = logging.getLogger(component)
            logger.setLevel(level)

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance for a specific component

        Args:
            name: Logger name (typically __name__)

        Returns:
            Configured logger instance
        """
        return logging.getLogger(name)

    def log_pipeline_start(self, request_id: str, topic: str, content_type: str):
        """Log the start of a content pipeline process"""
        logger = logging.getLogger("content_writer.workflows")
        logger.info(
            f"🚀 Pipeline started | Request ID: {request_id} | Topic: {topic} | Type: {content_type}"
        )

    def log_pipeline_step(self, step: str, request_id: str, details: str = ""):
        """Log a pipeline step"""
        logger = logging.getLogger("content_writer.workflows")
        logger.info(f"📝 {step} | Request ID: {request_id} | {details}")

    def log_pipeline_complete(
        self, request_id: str, success: bool, quality_score: Optional[float] = None
    ):
        """Log pipeline completion"""
        logger = logging.getLogger("content_writer.workflows")
        status = "✅ SUCCESS" if success else "❌ FAILED"
        quality_info = f" | Quality Score: {quality_score}" if quality_score else ""
        logger.info(
            f"🏁 Pipeline completed | Request ID: {request_id} | {status}{quality_info}"
        )

    def log_agent_action(
        self, agent_name: str, action: str, request_id: str, details: str = ""
    ):
        """Log agent actions"""
        logger = logging.getLogger(f"content_writer.agents.{agent_name.lower()}")
        logger.info(
            f"🤖 {agent_name} | {action} | Request ID: {request_id} | {details}"
        )

    def log_api_request(
        self, endpoint: str, method: str, request_id: Optional[str] = None
    ):
        """Log API requests"""
        logger = logging.getLogger("content_writer.api")
        request_info = f" | Request ID: {request_id}" if request_id else ""
        logger.info(f"🌐 API Request | {method} {endpoint}{request_info}")

    def log_api_response(
        self,
        endpoint: str,
        status_code: int,
        response_time: float,
        request_id: Optional[str] = None,
    ):
        """Log API responses"""
        logger = logging.getLogger("content_writer.api")
        request_info = f" | Request ID: {request_id}" if request_id else ""
        status_emoji = "✅" if 200 <= status_code < 300 else "❌"
        logger.info(
            f"🌐 API Response | {status_emoji} {status_code} | {endpoint} | {response_time:.3f}s{request_info}"
        )

    def log_error(
        self,
        component: str,
        error: Exception,
        request_id: Optional[str] = None,
        context: str = "",
    ):
        """Log errors with context"""
        logger = logging.getLogger(f"content_writer.{component}")
        request_info = f" | Request ID: {request_id}" if request_id else ""
        context_info = f" | Context: {context}" if context else ""
        logger.error(
            f"💥 Error in {component} | {type(error).__name__}: {str(error)}{request_info}{context_info}",
            exc_info=True,
        )

    def log_performance(
        self,
        operation: str,
        duration: float,
        request_id: Optional[str] = None,
        details: str = "",
    ):
        """Log performance metrics"""
        logger = logging.getLogger("content_writer.performance")
        request_info = f" | Request ID: {request_id}" if request_id else ""
        details_info = f" | {details}" if details else ""
        logger.info(
            f"⏱️ Performance | {operation} | {duration:.3f}s{request_info}{details_info}"
        )


# Global logger instance
_logger_instance: Optional[ContentWriterLogger] = None


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance. Initializes the global logger if not already done.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    global _logger_instance

    if _logger_instance is None:
        # Initialize with environment variables or defaults
        log_level = os.getenv("LOG_LEVEL", "INFO")
        log_dir = os.getenv("LOG_DIR", "logs")
        enable_console = os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower() == "true"
        enable_file = os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"
        safe_unicode = os.getenv("SAFE_UNICODE", "auto").lower()

        # Handle safe_unicode setting
        if safe_unicode == "auto":
            safe_unicode_setting = None  # Auto-detect
        elif safe_unicode == "true":
            safe_unicode_setting = True
        else:
            safe_unicode_setting = False

        _logger_instance = ContentWriterLogger(
            log_level=log_level,
            log_dir=log_dir,
            enable_console=enable_console,
            enable_file=enable_file,
            safe_unicode=safe_unicode_setting,
        )

    return _logger_instance.get_logger(name)


def get_pipeline_logger() -> ContentWriterLogger:
    """
    Get the pipeline logger instance for structured logging

    Returns:
        ContentWriterLogger instance
    """
    global _logger_instance

    if _logger_instance is None:
        get_logger(__name__)  # Initialize if needed

    return _logger_instance


# Convenience functions for common logging patterns
def log_pipeline_start(request_id: str, topic: str, content_type: str):
    """Log pipeline start"""
    get_pipeline_logger().log_pipeline_start(request_id, topic, content_type)


def log_pipeline_step(step: str, request_id: str, details: str = ""):
    """Log pipeline step"""
    get_pipeline_logger().log_pipeline_step(step, request_id, details)


def log_pipeline_complete(
    request_id: str, success: bool, quality_score: Optional[float] = None
):
    """Log pipeline completion"""
    get_pipeline_logger().log_pipeline_complete(request_id, success, quality_score)


def log_agent_action(agent_name: str, action: str, request_id: str, details: str = ""):
    """Log agent action"""
    get_pipeline_logger().log_agent_action(agent_name, action, request_id, details)


def log_error(
    component: str,
    error: Exception,
    request_id: Optional[str] = None,
    context: str = "",
):
    """Log error"""
    get_pipeline_logger().log_error(component, error, request_id, context)


def log_performance(
    operation: str, duration: float, request_id: Optional[str] = None, details: str = ""
):
    """Log performance"""
    get_pipeline_logger().log_performance(operation, duration, request_id, details)
