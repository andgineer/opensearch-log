import datetime
import json

from opensearch_log import get_json_logger, LogFields, log_fields
from tests.conftest import capture_logs


def test_get_logger_with_same_component(caplog, log):
    log1 = get_json_logger()
    log2 = get_json_logger()

    assert log1 is log2
    assert log1 is log

    log.info("This is an info message inside context manager.")

    assert len(caplog.records) == 1

    record = caplog.records[0]
    assert record.msg == "This is an info message inside context manager."
    assert getattr(record, "component") == "TestComponent"


def test_get_logger_with_different_component(caplog):
    log = get_json_logger("AnotherComponent")
    log.info("This is an info message inside context manager.")

    assert len(caplog.records) == 1

    record = caplog.records[0]
    assert record.msg == "This is an info message inside context manager."
    assert getattr(record, "component") == "AnotherComponent"


def test_log_var_decorator_with_value(caplog, log):
    @log_fields(explicit_field="ExplicitValue")
    def log_message():
        log.info("This is an info message from decorated function with explicit value.")

    log_message()

    assert len(caplog.records) == 1

    record = caplog.records[0]
    assert record.msg == "This is an info message from decorated function with explicit value."
    assert getattr(record, "explicit_field") == "ExplicitValue"


def test_log_ctx_with_values(caplog, log):
    with LogFields(explicit_field_ctx="ExplicitValueCtx", field2="Value2"):
        log.info("This is an info message inside context manager with explicit value.")

    assert len(caplog.records) == 1

    record = caplog.records[0]
    assert record.msg == "This is an info message inside context manager with explicit value."
    assert getattr(record, "explicit_field_ctx") == "ExplicitValueCtx"
    assert getattr(record, "field2") == "Value2"


def test_nested_log_var_decorator(caplog, log):
    @log_fields(image_id="Value1InDecorator")
    @log_fields(var2_field="Value2InDecorator")
    @log_fields(var3_field=datetime.datetime.now())
    def log_message():
        log.info("This is an info message from decorated function with a list of LogVars.")

    log_message()

    assert len(caplog.records) == 1

    record = caplog.records[0]
    assert record.msg == "This is an info message from decorated function with a list of LogVars."
    assert getattr(record, "image_id") == "Value1InDecorator"
    assert getattr(record, "var2_field") == "Value2InDecorator"


def test_logger_output_json(log):
    with capture_logs(log) as logs:
        log.info("Mock message")

        log_contents = logs.getvalue().strip()
        log_data = json.loads(log_contents.split("\n")[0])  # pytest add handlers that duplicate log messages

        assert log_data["message"] == "Mock message"
        assert log_data["component"] == "TestComponent"


def test_default_logger_is_changed(log):
    with capture_logs(log) as logs:
        log.info("Mock message2")

        log_contents = logs.getvalue().strip()
        log_data = json.loads(log_contents.split("\n")[0])  # pytest add handlers that duplicate log messages

        assert log_data["message"] == "Mock message2"
        assert log_data["component"] == "TestComponent"


def test_get_logger_reinit(log):
    with capture_logs(log) as logs:
        _logger = None

        log = get_json_logger("AnotherComponent")
        log.info("Reinited.")

        log_contents = logs.getvalue().strip()
        log_data = json.loads(log_contents.split("\n")[0])  # pytest add handlers that duplicate log messages

        assert log_data["message"] == "Reinited."
        assert log_data["component"] == "AnotherComponent"


def test_get_logger_fields(caplog):
    log1 = get_json_logger(component="test", branch="master", key1="value1", key2="value2")
    log1.info("Hello")
    record = caplog.records[0]
    assert record.msg == "Hello"
    assert getattr(record, "component") == "test"
    assert getattr(record, "branch") == "master"
    assert getattr(record, "key1") == "value1"
    assert getattr(record, "key2") == "value2"

    log2 = get_json_logger(component="test2", branch="master2", key1="new_value1", key3="value3")
    log2.info("Hello2")
    record = caplog.records[1]
    assert record.msg == "Hello2"
    assert getattr(record, "component") == "test2"
    assert getattr(record, "branch") == "master2"
    assert getattr(record, "key1") == "new_value1"
    assert getattr(record, "key3") == "value3"
    assert not hasattr(record, "key2")
