import io
import json
import logging
import os
from contextlib import contextmanager
from typing import Optional, Any, Dict, List, Tuple
from unittest.mock import patch, MagicMock

from opensearch_log.json_formatter import _log_values
from opensearch_log import json_formatter

from opensearch_log import get_json_logger
from opensearch_log.base_handler import BaseStructuredHandler
from opensearch_log.stdout_handler import StructuredStdoutHandler

import pytest

from opensearch_log.opensearch_handler import StructuredOpensearchHandler
from opensearch_log.opensearch_serializer import OpenSearchSerializer
import opensearchpy.exceptions


@pytest.fixture(scope="function")
def log():
    return get_json_logger(component="TestComponent")


@contextmanager
def capture_logs(log):
    """Fixture to temporarily capture output of send_message in log handlers."""
    captured_messages = io.StringIO()

    def new_send_message(self, message: Optional[str], record: logging.LogRecord):
        """Temporary send_message to capture messages."""
        captured_messages.write(message + "\n")  # Added newline for easier parsing later

    handlers_to_patch = [handler for handler in log.handlers if isinstance(handler, StructuredStdoutHandler)]

    original_methods = {}  # Store original methods to restore them later
    for handler in handlers_to_patch:
        original_methods[handler] = handler.send_message
        handler.send_message = new_send_message.__get__(handler)  # Bind method to instance

    try:
        yield captured_messages
    finally:
        # Cleanup: Restore the original send_message methods
        for handler in handlers_to_patch:
            handler.send_message = original_methods[handler]


@pytest.fixture(scope="function")
def cloudwatch():
    json_formatter._logger = None

    with patch.dict(os.environ, {
        'AWS_DEFAULT_REGION': 'us-west-2',
        'AWS_ACCESS_KEY_ID': 'testing',
        'AWS_SECRET_ACCESS_KEY': 'testing'
    }):
        yield

    if json_formatter._logger is not None:
        handlers_to_remove = [
            handler for handler in json_formatter._logger.handlers
            if isinstance(handler, BaseStructuredHandler)
        ]
        for handler in handlers_to_remove:
            json_formatter._logger.removeHandler(handler)
        json_formatter._logger = None


class MockLogRecord(logging.LogRecord):
    def __init__(self, name, level, filename, lineno, message, args, exc_info, func=None, sinfo=None):
        super().__init__(name, level, filename, lineno, message, args, exc_info, func, sinfo)
        self.message = message
        self.args = args
        self.exc_info = exc_info


class MockOpenSearchClient:
    bulk_calls: List[Tuple[List[Any], Dict[str, Any]]] = []

    def __init__(self):
        self.captured_requests = []
        self.mock_bulk_exception = False
        self.bulk_calls = []

    def ping(self):
        return True

    def index(self, *args, **kwargs):
        self.captured_requests.append((args, kwargs))
        return {}

    @property
    def transport(self):
        transport = MagicMock()
        transport.serializer = OpenSearchSerializer()
        return transport

    def bulk(self, *args, **kwargs):
        self.bulk_calls.append({"actions": []})  # type: ignore
        actions_tuple = args or kwargs.get('body', [])
        response_items = []

        actions = actions_tuple[0].split('\n')
        for i in range(0, len(actions), 2):
            if actions[i].strip():
                action = json.loads(actions[i].strip())
                data = json.loads(actions[i + 1].strip())
                self.bulk_calls[-1]["actions"].append({"_source": data})
                if 'index' in action:
                    data['_id'] = data.get('_id', None)
                    response_items.append({"index": {"status": 200}})
                    self.bulk_calls[-1]["actions"][-1]["_index"] = action['index']['_index']
        if self.mock_bulk_exception:
            self.mock_bulk_exception = False
            raise AssertionError("Mocked exception")
        return {
            "took": 1,
            "errors": False,
            "items": response_items
        }


@pytest.fixture(scope="function")
def opensearch_handler():
    json_formatter._logger = None

    with patch(
            'opensearch_log.opensearch_handler.StructuredOpensearchHandler._get_opensearch_client', return_value=MockOpenSearchClient()):
        handler = StructuredOpensearchHandler()
        yield handler
        handler.close()

    if json_formatter._logger is not None:
        handlers_to_remove = [
            handler for handler in json_formatter._logger.handlers
            if isinstance(handler, BaseStructuredHandler)
        ]
        for handler in handlers_to_remove:
            json_formatter._logger.removeHandler(handler)
        json_formatter._logger = None
