# opensearch-log

opensearch-log is a Python logging handler for direct and efficient log transmission to 
OpenSearch. 

It integrates with Python's standard logging framework to send logs to an OpenSearch 
cluster, offering a blend of efficiency, reliability, and ease of use.

Also includes a specialized logging formatter that enables stdout logs to be 
formatted  in JSON. 

## Key Features

- **Efficient Logging**: Designed for minimal impact on application performance.
- **Reliable Transmission**: Ensures consistent delivery of logs to OpenSearch.
- **Easy Integration**: Simple setup with Python's standard logging system.
- **Flexible Configuration**: Adaptable to various logging and OpenSearch setups.
- **Asynchronous Support**: Handles log transmission asynchronously for enhanced performance.

Ideal for applications ranging from small-scale projects to large enterprise systems, 
OpenSearchLogHandler provides a robust and straightforward solution for managing logs 
with OpenSearch.


## TL;DR

```python
from opensearch_log import Fields
from opensearch_log.opensearch_handler import get_logger

logger = get_logger(index_name = "myindex", echo_stdout=True)
with Fields(my_log_field="From Python"):
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