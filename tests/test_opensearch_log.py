import json
import logging
from datetime import datetime, timezone
from time import sleep

import pytest

from opensearch_log.opensearch_serializer import OpenSearchSerializer
from unittest.mock import MagicMock, patch

from opensearch_log.opensearch_handler import OpensearchHandler, INDEX_DATE_FORMAT, DEFAULT_INDEX_NAME
from opensearch_log.stdout_handler import add_stdout_json_handler
from opensearch_log import json_log
from opensearch_log import Logging
from tests.conftest import MockLogRecord, opensearch_handler, capture_logs
import opensearchpy.exceptions


def test_emit(opensearch_handler):
    record = MockLogRecord(
        name='test_logger',
        level=logging.INFO,
        filename='test.py',
        lineno=10,
        message='Test log message',
        args=None,
        exc_info=None
    )

    opensearch_handler.emit(record)

    assert len(opensearch_handler._buffer) == 1
    assert opensearch_handler._buffer[0]['message'] == 'Test log message'
    assert opensearch_handler._buffer[0]['filename'] == 'test.py'


def test_flush(opensearch_handler):
    record = MockLogRecord(
        name='test_logger',
        level=logging.INFO,
        filename='test.py',
        lineno=10,
        message='Test log message',
        args=None,
        exc_info=None
    )

    opensearch_handler.emit(record)

    opensearch_handler.flush()

    # Assert that the buffer is empty after flushing
    assert len(opensearch_handler._buffer) == 0


def test_close(opensearch_handler):
    record = MockLogRecord(
        name='test_logger',
        level=logging.INFO,
        filename='test.py',
        lineno=10,
        message='Test log message',
        args=None,
        exc_info=None
    )

    opensearch_handler.emit(record)

    opensearch_handler.close()

    # Assert that the buffer is empty after closing
    assert len(opensearch_handler._buffer) == 0


def test_index_naming(opensearch_handler):
    opensearch_handler.index_rotate = OpensearchHandler.MONTHLY
    index_name = opensearch_handler._get_index_name()

    # Check the prefix
    assert index_name.startswith(DEFAULT_INDEX_NAME)

    # Check the date part of the index name
    current_date = datetime.now(timezone.utc).replace(day=1)
    expected_date_str = current_date.strftime(INDEX_DATE_FORMAT)
    assert index_name.endswith(expected_date_str)

    opensearch_handler.index_rotate = OpensearchHandler.DAILY
    index_name = opensearch_handler._get_index_name()

    # Check the prefix
    assert index_name.startswith(DEFAULT_INDEX_NAME)

    # Check the date part of the index name
    current_date = datetime.now(timezone.utc)
    expected_date_str = current_date.strftime(INDEX_DATE_FORMAT)
    assert index_name.endswith(expected_date_str)


def test_get_opensearch_datetime_str(opensearch_handler):
    timestamp = 1634616000.123  # October 19, 2021, 12:00:00.123 UTC

    # Calculate the expected UTC datetime based on the timestamp
    expected_datetime = datetime.utcfromtimestamp(timestamp)

    # Get the datetime_str from the method
    datetime_str = opensearch_handler._get_opensearch_datetime_str(timestamp)

    # Parse the datetime_str to a datetime object
    actual_datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%fZ')

    assert actual_datetime == expected_datetime


def test_test_opensearch_connection(opensearch_handler):
    mock_opensearch_client = MagicMock()

    with patch.object(mock_opensearch_client, 'ping', return_value=True):
        assert opensearch_handler.is_connected() is True


def test_opensearch_handler_ping_called():
    mock_opensearch_client = MagicMock()

    with patch(
            'opensearch_log.opensearch_handler.OpensearchHandler._get_opensearch_client',
            return_value=mock_opensearch_client):
        OpensearchHandler()
        mock_opensearch_client.ping.assert_called_once()


def test_opensearch_log(opensearch_handler):
    logger = json_log.get_logger(
        application="-mock-component-",
        log_handler=opensearch_handler,
    )
    with Logging(my_field="-mock-my-field-"):
        logger.info("Mock log message")
        opensearch_handler.flush()

    mock_client = opensearch_handler._get_opensearch_client()

    assert len(mock_client.bulk_calls) == 1
    kwargs = mock_client.bulk_calls[0]


    assert kwargs["actions"][0]["_index"] == opensearch_handler._get_index_name()
    assert kwargs["actions"][0]["_source"]["message"] == "Mock log message"
    assert kwargs["actions"][0]["_source"]["my_field"] == "-mock-my-field-"
    assert kwargs["actions"][0]["_source"]["application"] == "-mock-component-"
    assert kwargs["actions"][0]["_source"]["levelname"] == "INFO"


def test_opensearch_log_echo_stdout(opensearch_handler):
    logger = json_log.get_logger(
        application="-mock-component-",
        log_handler=opensearch_handler,
        clear_handlers=True,
    )
    add_stdout_json_handler(logger)

    with capture_logs(logger) as logs:
        logger.info("Mock message")

        log_contents = logs.getvalue().strip()
        log_data = json.loads(log_contents.split("\n")[0])  # pytest add handlers that duplicate log messages

        assert log_data["message"] == "Mock message"
        assert log_data["application"] == "-mock-component-"


def test_opensearch_log_not_echo_stdout(opensearch_handler):
    logger = json_log.get_logger(
        application="-mock-component-",
        log_handler=opensearch_handler,
        echo_stdout=False,
        clear_handlers=True,
    )

    with capture_logs(logger) as logs:
        logger.info("Mock message")

        log_contents = logs.getvalue().strip()
        assert log_contents == ''


def test_opensearch_log_context_unserializable(opensearch_handler):
    """If default OpenSearch serialization fails we catch the exception and use default serialization."""
    class UnSerializable:
        pass

    logger = json_log.get_logger(
        application="-mock-component-",
        log_handler=opensearch_handler,
        echo_stdout=False,
        clear_handlers=True,
    )

    with Logging(field=UnSerializable()):
        logger.info("Mock message")
        logger.info("Mock message2")


def test_opensearch_log_unserializable(opensearch_handler):

    class UnSerializable:
        pass

    assert "UnSerializable" in OpenSearchSerializer().dumps({"field": UnSerializable()})


def test_opensearch_log_flush_exception(opensearch_handler):
    record = MockLogRecord(
        name='test_logger',
        level=logging.INFO,
        filename='test.py',
        lineno=10,
        message='Test log message',
        args=None,
        exc_info=None
    )

    opensearch_handler.flush_seconds = 0.001
    opensearch_handler.flush()
    opensearch_handler._get_opensearch_client().mock_bulk_exception = True
    opensearch_handler._get_opensearch_client().bulk_calls = []
    opensearch_handler.emit(record)
    sleep(0.1)  # wait for timer to call flush()

    assert len(opensearch_handler._get_opensearch_client().bulk_calls) == 2  # exc and retry
    assert len(opensearch_handler._buffer) == 0  # we managed to send in retry

    opensearch_handler.flush_seconds = 100
    opensearch_handler.emit(record)
    assert len(opensearch_handler._buffer) == 1
    opensearch_handler.close()
    assert len(opensearch_handler._buffer) == 0


def test_opensearch_log_bulk_size(opensearch_handler):
    with patch.object(opensearch_handler, 'buffer_size', 1):
        logger = json_log.get_logger(
            application="-mock-component-",
            log_handler=opensearch_handler,
            echo_stdout=False,
            clear_handlers=True,
        )
        logger.info("Mock message")
        logger.info("Mock message2")
        opensearch_handler.flush()
        assert len(opensearch_handler._get_opensearch_client().bulk_calls) == 2

    opensearch_handler._get_opensearch_client().bulk_calls = []

    with patch.object(opensearch_handler, 'buffer_size', 2):
        logger = json_log.get_logger(
            application="-mock-component-",
            log_handler=opensearch_handler,
            echo_stdout=False,
            clear_handlers=True,
        )
        logger.info("Mock message")
        logger.info("Mock message2")
        opensearch_handler.flush()
        assert len(opensearch_handler._get_opensearch_client().bulk_calls) == 1
