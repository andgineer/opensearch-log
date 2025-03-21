"""JSON logging."""

import contextvars
import logging
import sys
from functools import wraps
from typing import Any, Optional

from pythonjsonlogger import jsonlogger

from opensearch_log.base_handler import BaseHandler

_logger: Optional[logging.Logger] = None
_logger_params: Optional[dict[str, Optional[str]]] = None
_log_fields: contextvars.ContextVar[Optional[dict[str, object]]] = contextvars.ContextVar(
    "log_fields",
    default=None,
)


def set_record_factory() -> None:
    """Set a log record factory."""
    original_factory = logging.getLogRecordFactory()

    def _record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = original_factory(*args, **kwargs)
        fields = _log_fields.get()
        if fields:
            for field, value in fields.items():
                setattr(record, field, value)
        return record

    logging.setLogRecordFactory(_record_factory)


def create_logger(
    log_handler_instance: BaseHandler,
    level: int,
    clear_handlers: bool = False,
) -> logging.Logger:
    """Create a logger that stream logs in JSON format with additional fields."""
    result = logging.getLogger()
    if clear_handlers:
        remove_handlers(result)
    formatter = get_json_formatter()
    log_handler_instance.setFormatter(formatter)
    result.addHandler(log_handler_instance)
    result.setLevel(level)
    return result


def get_json_formatter() -> jsonlogger.JsonFormatter:
    """Get a JSON formatter."""
    return jsonlogger.JsonFormatter(  # type: ignore
        "%(message)%(levelname)%(name)%(application)%(filename)",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def replace_logger_fields(fields_to_log: dict[str, Any]) -> None:
    """Update logger with new fields to log."""
    global _logger_params  # noqa: PLW0603
    if _logger_params == fields_to_log or (fields_to_log["application"] is None):
        return
    assert _logger_params is not None, (
        "The method should be called only if the logger have been created before"
    )
    remove_log_fields(*_logger_params.keys())
    add_log_fields(**fields_to_log)
    _logger_params = fields_to_log


def remove_handlers(_logger: logging.Logger) -> None:
    """Remove any default handlers."""
    if _logger.handlers:
        for handler in _logger.handlers:
            _logger.removeHandler(handler)


def add_log_fields(**values: Any) -> list[str]:
    """Include fields to all log records."""
    current_fields = _log_fields.get()
    if current_fields is None:
        current_fields = {}
        _log_fields.set(current_fields)
    current_fields.update(values)
    return list(values.keys())


def remove_log_fields(*fields: str) -> None:
    """Remove logged fields."""
    current_fields = _log_fields.get()
    if current_fields is not None:
        for key in fields:
            current_fields.pop(key, None)


class Logging:
    """Context manager to add fields to log records."""

    def __init__(self, **values: Any) -> None:
        """Initialize the context manager with fields to add to log records."""
        self.values = values
        self.added_fields: list[str] = []

    def __enter__(self) -> "Logging":
        """Enter the context: add fields to log records."""
        self.added_fields = add_log_fields(**self.values)
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[Any],
    ) -> None:
        """Exit the context: remove the added fields from log records."""
        remove_log_fields(*self.added_fields)


def log_fields(func: Optional[Any] = None, **values: Any) -> Any:
    """Decorate to include fields `values` to all log records."""

    def decorate(func: Any) -> Any:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            added_fields = add_log_fields(**values)
            try:
                return func(*args, **kwargs)
            finally:
                remove_log_fields(*added_fields)

        return wrapper

    return decorate(func) if callable(func) else decorate


def get_logger(
    application: Optional[str] = sys.argv[0],
    *,
    log_handler: BaseHandler,
    level: int = logging.INFO,
    clear_handlers: bool = False,
    **values: Any,
) -> logging.Logger:
    """Get a JSON logger."""
    global _logger, _logger_params  # noqa: PLW0603

    if _logger is not None:
        replace_logger_fields({"application": application, **values})
        return _logger

    _logger_params = {"application": application, **values}
    _logger = create_logger(
        log_handler_instance=log_handler,
        level=level,
        clear_handlers=clear_handlers,
    )
    add_log_fields(**_logger_params)
    set_record_factory()
    return _logger
