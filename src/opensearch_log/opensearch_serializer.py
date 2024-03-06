"""JSON serializer."""

from typing import Any

try:
    from opensearchpy.serializer import JSONSerializer
except ImportError as e:
    raise ImportError(
        "To use OpensearchHandler please install with this feature: "
        "`pip install opensearch-log[opensearch]`."
    ) from e


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
