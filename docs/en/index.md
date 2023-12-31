# opensearch-log

opensearch-log is a Python logging handler for direct and efficient log transmission to
OpenSearch or CloudWatch.

With context manager or function decorator you can add additional fields to log messages.

## Installation

```bash
pip install opensearch-log
```

## TL;DR

```python
from opensearch_log import Logging
from opensearch_log.opensearch_handler import get_logger

logger = get_logger(index_name="myindex", echo_stdout=True)
with Logging(my_log_field="From Python"):
    logger.info("Hello World")
```

Will send to OpenSearch something like (I cleaned up the output for readability):
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

And will print on terminal (cleaned up for readability):
```json
{
  "message": "Hello World",
  "name": "root",
  "my_log_field": "From Python"
}
```

if you need just JSON log import `get_logger` from `opensearch_log.stdout_handler` instead of 
`opensearch_log.opensearch_handler`