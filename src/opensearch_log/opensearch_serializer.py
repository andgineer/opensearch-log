"""JSON serializer for OpenSearch."""
from typing import Any

from opensearchpy.serializer import JSONSerializer


class OpenSearchSerializer(JSONSerializer):
    """JSON serializer inherited from the OpenSearch JSON serializer.

    Ignore serialization errors.
    """

    def default(self, data: Any) -> Any:
        """Transform unknown types into strings."""
        try:
            return super().default(data)
        except TypeError:
            return str(data)
