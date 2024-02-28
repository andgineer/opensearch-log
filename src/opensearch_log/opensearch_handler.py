"""Structured logger that sends logs to AWS OpenSearch."""

import logging
import traceback
from datetime import datetime, timezone
from enum import Enum
from threading import Lock, Timer
from typing import Any, Dict, List, Optional, Union

import boto3
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection, helpers

from opensearch_log import json_log
from opensearch_log.base_handler import BaseHandler
from opensearch_log.opensearch_serializer import OpenSearchSerializer
from opensearch_log.stdout_handler import add_stdout_json_handler


class IndexRotation(Enum):
    """Index rotation frequency."""

    DAILY = 0
    MONTHLY = 10


DEFAULT_OPENSEARCH_HOST = "localhost"
DEFAULT_INDEX_NAME = "myindex"
BUFFER_SIZE = 200  # number of records to buffer before sending to OpenSearch
BULK_SIZE = 15  # number of records to send to OpenSearch in one bulk
FLUSH_SECONDS = 0.8  # number of seconds to wait before flushing the buffer
RETRY_NUM = 3  # number of retries to send logs to OpenSearch
INDEX_DATE_FORMAT = "%Y.%m.%d"
IGNORED_LOG_RECORD_FIELDS = [
    "args",
    "levelno",
    "pathname",
    "relativeCreated",
    "msecs",
    "exc_text",
]


class OpensearchHandler(BaseHandler):  # pylint: disable=too-many-instance-attributes
    """Handler to send log records to AWS OpenSearch."""

    DAILY = IndexRotation.DAILY
    MONTHLY = IndexRotation.MONTHLY

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *args: Any,
        opensearch_host: str = DEFAULT_OPENSEARCH_HOST,
        index_name: str = DEFAULT_INDEX_NAME,
        index_rotate: Union[IndexRotation, str] = IndexRotation.DAILY,
        buffer_size: int = BUFFER_SIZE,
        flush_seconds: float = FLUSH_SECONDS,
        **kwargs: Any,
    ) -> None:
        """Initialize the handler."""
        super().__init__(*args, **kwargs)

        # Opensearch
        self.opensearch_host = opensearch_host
        self.index_name = index_name
        if isinstance(index_rotate, str):
            self.index_rotate = IndexRotation[index_rotate]
        else:
            self.index_rotate = index_rotate

        # Bulk settings
        self.buffer_size = buffer_size
        self.flush_seconds = flush_seconds

        # Internals
        self._client: Optional[OpenSearch] = None
        self._buffer: List[Dict[str, Any]] = []
        self._buffer_lock: Lock = Lock()
        self._timer: Optional[Timer] = None

        if self.is_connected():
            print("Connected to OpenSearch")
        else:
            print("Could not connect to OpenSearch instance")

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a logging record in a processed format."""
        self.send_message(None, record)

    def send_message(self, message: Optional[str], record: logging.LogRecord) -> None:
        """Send the log message to OpenSearch."""
        doc = self._convert_log_record_to_opensearch_doc(record)
        with self._buffer_lock:
            self._buffer.append(doc)

        if len(self._buffer) >= self.buffer_size:
            self.flush()
        else:
            self._schedule_flush()

    def is_connected(self) -> bool:
        """Return True if we can ping the OpenSearch."""
        if self._get_opensearch_client() is None:
            return True  # test mode?
        return self._get_opensearch_client().ping()  # type: ignore

    def flush(self) -> None:
        """Flush the buffer."""
        if hasattr(self, "_timer") and self._timer is not None and self._timer.is_alive():
            self._timer.cancel()
        self._timer = None

        if not self._buffer:
            return

        with self._buffer_lock:
            logs_buffer = self._buffer
            self._buffer = []

        index = self._get_index_name()
        actions = [{"_index": index, "_source": record} for record in logs_buffer]

        if self._get_opensearch_client() is None:
            print(
                "Mock MODE: would NOT send to OpenSearch"
            )  # do not use logger here, to avoid recursion
        else:
            for i in range(0, len(actions), BULK_SIZE):
                retries = 0
                while retries < RETRY_NUM:
                    try:
                        helpers.bulk(
                            client=self._get_opensearch_client(),
                            actions=actions[i : i + BULK_SIZE],
                            stats_only=True,
                        )
                        break
                    except Exception as exception:  # pylint: disable=broad-except
                        retries += 1  # Increment retry count
                        print(f"Retry {retries}: Could not send logs to OpenSearch: {exception}")
                        if retries >= RETRY_NUM:
                            print("Exhausted retries. Lost logs:\n", logs_buffer)
                            print(
                                f"\n-- opensearch.bulk() --\n{traceback.format_exc()}-- end --\n"
                            )

    def close(self) -> None:
        """Flush the buffer on close."""
        self.flush()

    def _get_opensearch_client(self) -> Optional[OpenSearch]:
        if self._client is None:
            print(f"Connecting to OpenSearch instance: {self.opensearch_host}...")
            credentials = boto3.Session().get_credentials()
            region = boto3.Session().region_name
            if region is None:
                raise ValueError(
                    "AWS region is not set.\n"
                    "Please set the AWS_REGION environment variable or `region=` in AWS config."
                )
            awsauth = AWSV4SignerAuth(credentials, region, "es")
            verify = self.opensearch_host.startswith("https")
            self._client = OpenSearch(
                [self.opensearch_host],
                http_auth=awsauth,
                use_ssl=verify,
                verify_certs=verify,
                connection_class=RequestsHttpConnection,
                serializer=OpenSearchSerializer(),
            )
            if not self._client.ping():
                print(f"Could not connect to OpenSearch instance at: {self.opensearch_host}...")
            else:
                print(f"Connected to OpenSearch instance at: {self.opensearch_host}...")
        return self._client

    def _schedule_flush(self) -> None:
        if self._timer is None:
            self._timer = Timer(self.flush_seconds, self.flush)
            self._timer.daemon = True
            self._timer.start()

    def _get_index_name(self) -> str:
        if IndexRotation.DAILY == self.index_rotate:
            return self._get_index_name_daily()
        if IndexRotation.MONTHLY == self.index_rotate:
            return self._get_index_name_monthly()
        raise ValueError(f"Unknown index rotation: {self.index_rotate}")

    def _convert_log_record_to_opensearch_doc(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Convert logging.LogRecord to OpenSearch doc."""
        print(f"record: {record.msg}, {record.__dict__}")
        log_record_dict = record.__dict__.copy()
        doc = {
            "@timestamp": self._get_opensearch_datetime_str(
                datetime.now(timezone.utc).timestamp()
            ),
        }
        for key, value in log_record_dict.items():
            if key not in IGNORED_LOG_RECORD_FIELDS:
                doc[key] = "" if value is None else value
        return doc

    def _get_index_name_daily(self, current_date: Optional[datetime] = None) -> str:
        if current_date is None:
            current_date = datetime.now(tz=timezone.utc)  # pragma: no cover
        return f"{self.index_name}-{current_date.strftime(INDEX_DATE_FORMAT)}"

    def _get_index_name_monthly(self, current_date: Optional[datetime] = None) -> str:
        if current_date is None:
            current_date = datetime.now(tz=timezone.utc)  # pragma: no cover
        first_date_of_month = datetime(current_date.year, current_date.month, 1)
        return f"{self.index_name}-{first_date_of_month.strftime(INDEX_DATE_FORMAT)}"

    @staticmethod
    def _get_opensearch_datetime_str(timestamp: float) -> str:
        datetime_utc = datetime.utcfromtimestamp(timestamp)
        fmt = "%Y-%m-%dT%H:%M:%S"
        return f"{datetime_utc.strftime(fmt)}.{int(datetime_utc.microsecond / 1000):03d}Z"


def get_logger(  # pylint: disable=too-many-arguments
    *args: Any,
    opensearch_host: str = DEFAULT_OPENSEARCH_HOST,
    index_name: str = DEFAULT_INDEX_NAME,
    index_rotate: Union[IndexRotation, str] = IndexRotation.DAILY,
    echo_stdout: bool = False,
    buffer_size: int = BUFFER_SIZE,
    flush_seconds: float = FLUSH_SECONDS,
    log_handler: Optional[BaseHandler] = None,
    **kwargs: Any,
) -> logging.Logger:
    """Create a logger that stream logs to OpenSearch."""
    assert log_handler is None, "log_handler should not be specified"
    result = json_log.get_logger(
        *args,
        log_handler=OpensearchHandler(
            opensearch_host=opensearch_host,
            index_name=index_name,
            index_rotate=index_rotate,
            buffer_size=buffer_size,
            flush_seconds=flush_seconds,
        ),
        **kwargs,
    )
    if echo_stdout:
        add_stdout_json_handler(result)
    logging.getLogger("opensearch").setLevel(logging.WARNING)  # suppress HTTP tracing
    return result


if __name__ == "__main__":
    from opensearch_log import Logging

    # from stdout_handler import get_logger

    logger = get_logger(echo_stdout=True)
    with Logging(my_log_field="From Python"):
        logger.info("Hello World")
