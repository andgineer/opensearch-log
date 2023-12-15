"""JSON logging for stdout."""
import logging
from typing import Any, Optional

from opensearch_log import json_formatter
from opensearch_log.base_handler import BaseStructuredHandler
from opensearch_log.json_formatter import get_json_formatter


class StructuredStdoutHandler(BaseStructuredHandler):
    """Handler that sends log records to stdout."""

    def __init__(self) -> None:
        """Initialize the handler."""
        super().__init__()

    def send_message(self, message: Optional[str], record: logging.LogRecord) -> None:
        """Send the log message to stdout."""
        print(message)


def get_json_logger(
    component: Optional[str] = None,
    branch: Optional[str] = None,
    *,
    level: int = logging.INFO,
    clear_handlers: bool = False,
    **values: Any,
) -> logging.Logger:
    """Get a logger that streams logs to stdout in JSON format with additional fields."""
    return json_formatter.get_json_logger(
        component=component,
        branch=branch,
        level=level,
        log_handler=StructuredStdoutHandler(),
        clear_handlers=clear_handlers,
        **values,
    )


def append_stdout_json_handler(logger: logging.Logger) -> None:
    """Append a stdout handler to the logger."""
    stdout_handler = StructuredStdoutHandler()
    stdout_handler.setFormatter(get_json_formatter())
    logger.addHandler(stdout_handler)
