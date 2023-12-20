import json
import logging

import boto3

from opensearch_log import Logging, json_log
from tests.conftest import MockLogRecord, capture_logs
from opensearch_log.stdout_handler import add_stdout_json_handler


def test_cloudwatch_logging_existing_group_and_stream(cloudwatch_handler):
    logger = json_log.get_logger(
        component="-fake-component-",
        log_handler=cloudwatch_handler,
    )
    test_message = "Test Message for Existing Group and Stream"
    logger.info(test_message)
    cloudwatch_handler.flush()

    # Check if CloudWatch put_log_events was called
    client = boto3.client('logs')
    response = client.get_log_events(
        logGroupName='test-log-group',
        logStreamName='test-log-stream'
    )
    messages = [event['message'] for event in response['events']]
    assert test_message == json.loads(messages[0])["message"]


def test_cloudwatch_emit(cloudwatch_handler):
    message = 'Test log message'
    record = MockLogRecord(
        name='test_logger',
        level=logging.INFO,
        filename='test.py',
        lineno=10,
        message=message,
        args=None,
        exc_info=None
    )

    cloudwatch_handler.emit(record)

    assert len(cloudwatch_handler._buffer) == 1
    assert cloudwatch_handler._buffer[0]['message'] == message


def test_cloudwatch_flush(cloudwatch_handler):
    record = MockLogRecord(
        name='test_logger',
        level=logging.INFO,
        filename='test.py',
        lineno=10,
        message='Test log message',
        args=None,
        exc_info=None
    )

    cloudwatch_handler.emit(record)
    assert len(cloudwatch_handler._buffer) == 1

    cloudwatch_handler.flush()

    assert len(cloudwatch_handler._buffer) == 0


def test_cloudwatch_close(cloudwatch_handler):
    record = MockLogRecord(
        name='test_logger',
        level=logging.INFO,
        filename='test.py',
        lineno=10,
        message='Test log message',
        args=None,
        exc_info=None
    )

    cloudwatch_handler.emit(record)
    assert len(cloudwatch_handler._buffer) == 1
    cloudwatch_handler.close()

    assert len(cloudwatch_handler._buffer) == 0


def test_cloudwatch_handler(cloudwatch_handler):
    logger = json_log.get_logger(
        component="-fake-component-",
        log_handler=cloudwatch_handler,
    )
    with Logging(image_id="-fake-image-"):
        message = "Test log message"
        logger.info(message)
        cloudwatch_handler.flush()

        # Check if CloudWatch put_log_events was called
        client = boto3.client('logs')
        response = client.describe_log_streams(logGroupName='test-log-group')

        # Check if the log stream exists and has stored events
        assert len(response['logStreams']) > 0
        assert 'firstEventTimestamp' in response['logStreams'][0]

        # Check if the specific message was logged
        response = client.get_log_events(
            logGroupName='test-log-group',
            logStreamName='test-log-stream'
        )
        messages = [event['message'] for event in response['events']]
        assert message == json.loads(messages[0])["message"]


def test_cloudwatch_logger_echo_stdout(cloudwatch_handler):
    logger = json_log.get_logger(
        component="-fake-component-",
        log_handler=cloudwatch_handler,
        clear_handlers=True,
    )
    add_stdout_json_handler(logger)

    with capture_logs(logger) as logs:
        logger.info("Test message")

        log_contents = logs.getvalue().strip()
        log_data = json.loads(log_contents.split("\n")[0])

        assert log_data["message"] == "Test message"
        assert log_data["component"] == "-fake-component-"


def test_cloudwatch_logger_do_not_echo_stdout(cloudwatch_handler):
    logger = json_log.get_logger(
        component="-fake-component-",
        log_handler=cloudwatch_handler,
        clear_handlers=True,
    )

    with capture_logs(logger) as logs:
        logger.info("Test message")

        log_contents = logs.getvalue().strip()
        assert log_contents == ''
