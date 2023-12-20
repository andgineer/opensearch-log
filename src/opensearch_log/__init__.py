"""A Python logging handler for efficient and reliable direct log transmission to OpenSearch."""
from opensearch_log.cloudwatch_handler import CloudwatchHandler
from opensearch_log.json_log import Logging, add_log_fields, log_fields, remove_log_fields
