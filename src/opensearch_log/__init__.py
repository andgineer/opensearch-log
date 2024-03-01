"""A Python logging handler for efficient and reliable direct log transmission to OpenSearch."""

import logging
from opensearch_log.json_log import Logging, add_log_fields, log_fields, remove_log_fields

__all__ = ["Logging", "add_log_fields", "log_fields", "remove_log_fields"]

urllib3_logger = logging.getLogger("opensearch")
urllib3_logger.setLevel(logging.WARNING)
