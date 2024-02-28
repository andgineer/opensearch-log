"""Structured logger that sends logs to AWS CloudWatch."""

import contextlib
import logging
import time
from threading import Lock, Timer
from typing import Any, Dict, List, Optional

import boto3
import botocore.errorfactory
import botocore.exceptions

from opensearch_log import json_log
from opensearch_log.base_handler import BaseHandler
from opensearch_log.stdout_handler import add_stdout_json_handler

BUFFER_SIZE = 100
FLUSH_SECONDS = 3.0
RETRY_NUM = 3


class CloudwatchHandler(BaseHandler):  # pylint: disable=too-many-instance-attributes
    """Handler that sends log records to AWS CloudWatch."""

    def __init__(self, *args: Any, log_group: str, log_stream: str, **kwargs: Any) -> None:
        """Initialize the handler."""
        super().__init__(*args, **kwargs)
        self._log_client = None
        self.log_group = log_group
        self.log_stream = log_stream
        self.buffer_size = BUFFER_SIZE
        self.flush_seconds = FLUSH_SECONDS
        self._buffer: List[Dict[str, Any]] = []
        self._buffer_lock: Lock = Lock()
        self._timer: Optional[Timer] = None

        self._initialize_log_group()
        self._initialize_log_stream()

    def _initialize_log_stream(self) -> None:
        """Create the log stream if it doesn't already exist."""
        with contextlib.suppress(self.log_client.exceptions.ResourceAlreadyExistsException):
            self.log_client.create_log_stream(
                logGroupName=self.log_group, logStreamName=self.log_stream
            )

    def _initialize_log_group(self) -> None:
        """Create the log group if it doesn't already exist.

        Ignore access deny just in case the group really exists,
        but we do not have permission to create it and so the command will fail.
        If the group does not exist, and we fail to create it, in posting log messages we get
        more understandable error "The specified log group does not exist".
        """
        try:
            self.log_client.create_log_group(logGroupName=self.log_group)
        except self.log_client.exceptions.ResourceAlreadyExistsException:
            # Log group already exists. No action needed.
            pass
        except botocore.exceptions.ClientError as exc:
            # Check if the error is access denied error
            if exc.response["Error"]["Code"] != "AccessDeniedException":
                # Reraise the exception if it's not an AccessDeniedException
                raise

    @property
    def log_client(self) -> boto3.client:
        """Get the boto3 client for CloudWatch logs."""
        if self._log_client is None:
            # Disable boto's built-in logging to avoid recursion
            boto3.set_stream_logger("boto3", logging.CRITICAL)
            boto3.set_stream_logger("botocore", logging.CRITICAL)

            self._log_client = boto3.client("logs")
        return self._log_client

    def send_message(self, message: Optional[str], record: logging.LogRecord) -> None:
        """Buffer the log message and flush if necessary."""
        timestamp = int(round(time.time() * 1000))
        log_event = {"timestamp": timestamp, "message": message}

        with self._buffer_lock:
            self._buffer.append(log_event)

        if len(self._buffer) >= self.buffer_size:
            self.flush()
        else:
            self._schedule_flush()

    def flush(self) -> None:
        """Flush the buffer to CloudWatch.

        Could run from Timer's thread or from the main thread.
        So we should not use json_formatter's routines that access ThreadLocal variables.
        """
        if hasattr(self, "_timer") and self._timer is not None and self._timer.is_alive():
            self._timer.cancel()
        self._timer = None

        if not self._buffer:
            return

        with self._buffer_lock:
            logs_buffer = self._buffer
            self._buffer = []

        retries = 0
        while retries < RETRY_NUM:
            try:
                self.log_client.put_log_events(
                    logGroupName=self.log_group,
                    logStreamName=self.log_stream,
                    logEvents=logs_buffer,
                )
                break
            except botocore.exceptions.ClientError as e:
                retries += 1
                print(f"Retry {retries}: Could not send logs to CloudWatch: {e}")
                if retries >= RETRY_NUM:
                    print("Exhausted retries. Lost logs:\n", logs_buffer)

    def _schedule_flush(self) -> None:
        """Schedule a flush operation."""
        if self._timer is None:
            self._timer = Timer(self.flush_seconds, self.flush)
            self._timer.daemon = True
            self._timer.start()

    def close(self) -> None:
        """Flush the buffer and release any outstanding resource."""
        self.flush()
        super().close()


def get_logger(
    *args: Any,
    echo_stdout: bool = False,
    log_group: str,
    log_stream: str,
    log_handler: Optional[BaseHandler] = None,
    **kwargs: Any,
) -> logging.Logger:
    """Create a logger that stream logs to CloudWatch."""
    assert log_handler is None, "log_handler should not be specified"
    logger = json_log.get_logger(
        *args,
        log_handler=CloudwatchHandler(log_group=log_group, log_stream=log_stream),
        **kwargs,
    )
    if echo_stdout:
        add_stdout_json_handler(logger)
    return logger
