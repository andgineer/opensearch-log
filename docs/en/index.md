# opensearch-log

opensearch-log is a Python logging handler for direct and efficient log transmission to
OpenSearch or AWS CloudWatch.

It can also be used for local JSON logging to stdout.

Utilizing a context manager or function decorator, additional fields can be seamlessly 
added to log messages.

## Installation

```bash
pip install opensearch-log
```

## Setup logger
To configure the logger globally, utilize the appropriate `get_logger` function based on your 
logging destination. 

This function not only returns a customized logger but also configures the default logger, 
ensuring that subsequent calls to `logging.getLogger()` yield the same logger instance.

### Sending logs to OpenSearch

```python
from opensearch_log import Logging
from opensearch_log.opensearch_handler import get_logger

logger = get_logger(index_name="myindex", echo_stdout=True)
with Logging(my_log_field="From Python"):
    logger.info("Hello World")
```

This will transmit a log entry to OpenSearch that looks like this (output cleaned for readability):
```json
{
  "_index": "myindex-2023.12.16",
  "_source": {
    "@timestamp": "2023-12-16T06:39:19.479Z",
    "msg": "Hello World",
    "my_log_field": "From Python"
  }
}
```

Simultaneously, it will print the following on the terminal (output cleaned for readability):
```json
{
  "message": "Hello World",
  "name": "root",
  "my_log_field": "From Python"
}
```

### Sending logs to AWS CloudWatch
For logging to AWS CloudWatch, the setup involves the `get_logger` function from `cloudwatch_handler`:

```python
from opensearch_log.cloudwatch_handler import get_logger

logger = get_logger(index_name="myindex", echo_stdout=True)
```

### JSON logging to stdout
For applications requiring only JSON logging without the need to transmit logs to OpenSearch 
or AWS CloudWatch, use `get_logger` from `stdout_handler`:

```python
from opensearch_log.stdout_handler import get_logger

logger = get_logger(index_name="myindex", echo_stdout=True)
```

## Adding fields to logs 
Enhancing logs with additional fields can be accomplished using a function decorator, 
context manager, or straightforward function calls. 

Once applied, these fields will be included in all emitted log messages.

### Context manager

```python
from opensearch_log import Logging

with Logging(my_log_field="From Python"):
    logger.info("Hello World")
```

### Function decorator

```python
from opensearch_log import log_fields

@log_fields(my_log_field="From Python")
def my_func():
    logger.info("Hello World")
```

### Simple functions

```python
from opensearch_log import add_log_fields, remove_log_fields

added_fields = add_log_fields(my_log_field="From Python")
try:
    logger.info("Hello World")
finally:
    remove_log_fields(*added_fields)
```
