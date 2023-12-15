"""A Python logging handler for efficient and reliable direct log transmission to OpenSearch."""
from opensearch_log.json_formatter import LogFields, add_log_fields, log_fields, remove_log_fields
from opensearch_log.stdout_handler import get_json_logger
