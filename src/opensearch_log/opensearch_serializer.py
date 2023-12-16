"""JSON serializer."""
from typing import Any

from opensearchpy.serializer import JSONSerializer


class OpenSearchSerializer(JSONSerializer):
    """Override OpenSearch JSON serializer.

    Ignore serialization errors.
    """

    def default(self, data: Any) -> Any:
        """Catch all serialization fails and fall to __str__."""
        try:
            return super().default(data)
        except TypeError:
            return str(data)
