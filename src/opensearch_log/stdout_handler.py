"""JSON logging to stdout."""
import logging
from typing import Any, Optional

from opensearch_log import json_log
from opensearch_log.base_handler import BaseHandler
from opensearch_log.json_log import get_json_formatter


class StdoutHandler(BaseHandler):
    """Handler to send json log to stdout."""

    def __init__(self) -> None:
        """Initialize the handler."""
        super().__init__()

    def send_message(self, message: Optional[str], record: logging.LogRecord) -> None:
        """Send the log message to stdout."""
        print(message)


def get_logger(
    application: Optional[str] = None,
    branch: Optional[str] = None,
    *,
    level: int = logging.INFO,
    clear_handlers: bool = False,
    **values: Any,
) -> logging.Logger:
    """Get a logger to send JSON logs to stdout."""
    return json_log.get_logger(
        application=application,
        branch=branch,
        level=level,
        log_handler=StdoutHandler(),
        clear_handlers=clear_handlers,
        **values,
    )


def add_stdout_json_handler(logger: logging.Logger) -> None:
    """Add a stdout handler to the logger."""
    stdout_handler = StdoutHandler()
    stdout_handler.setFormatter(get_json_formatter())
    logger.addHandler(stdout_handler)
