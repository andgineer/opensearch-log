"""A Python logging handler for efficient and reliable direct log transmission to OpenSearch."""
from opensearch_log.json_log import Logging, add_log_fields, log_fields, remove_log_fields

__all__ = ["Logging", "add_log_fields", "log_fields", "remove_log_fields"]
