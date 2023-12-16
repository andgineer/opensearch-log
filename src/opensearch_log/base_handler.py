"""Base logger for structured logging."""
import logging
from typing import Optional


# Common Parent
class BaseHandler(logging.Handler):
    """Abstract base handler for structured logging."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a logging record in a processed format."""
        message = self.format(record)
        self.send_message(message, record)

    def send_message(self, message: Optional[str], record: logging.LogRecord) -> None:
        """Send the log message. This method should be implemented by subclasses."""
        raise NotImplementedError("This method should be implemented in subclasses.")
