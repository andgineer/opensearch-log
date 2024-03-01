import logging
import pytest
import requests
from opensearch_log.opensearch_handler import OpensearchHandler, restore_logger
from opensearch_log import json_log
from opensearch_log import Logging
from testcontainers.elasticsearch import ElasticSearchContainer


INDEX_NAME = "myindex"



@pytest.fixture(scope="module")
def opensearch_container():
    # Spin up an Elasticsearch container using testcontainers
    with ElasticSearchContainer("docker.elastic.co/elasticsearch/elasticsearch:7.15.2") as es_container:
        yield es_container


@pytest.fixture
def opensearch_handler(opensearch_container):
    # Get the Elasticsearch container's IP address and port
    es_ip = opensearch_container.get_container_host_ip()
    es_port = opensearch_container.get_docker_client().port(  # to work inside CI Docker
        opensearch_container._container.id, 9200  # pylint: disable=protected-access
    )

    # Check if the Elasticsearch container is ready
    try:
        requests.get(f"http://{es_ip}:{es_port}")
    except requests.ConnectionError:
        pytest.fail("Could not connect to OpenSearch container")

    # Initialize OpensearchHandler with the address of the OpenSearch container
    handler = OpensearchHandler(
        opensearch_host=f"http://{es_ip}:{es_port}",
        index_name=INDEX_NAME,
    )
    yield handler


def test_wth_opensearch(opensearch_handler):
    logger = json_log.get_logger(
        application="-mock-component-",
        log_handler=opensearch_handler,
    )
    print("#"*50, "before log")
    with Logging(my_field="-mock-my-field-"):
        logger.info("Mock log message")
        restore_logger()
    print("#"*50, "after log")
    es_ip = opensearch_handler.opensearch_host.split(":")[1].replace("//", "")
    es_port = opensearch_handler.opensearch_host.split(":")[2]

    requests.post(f"http://{es_ip}:{es_port}/{INDEX_NAME}-*/_refresh")
    query = {
        "query": {
            "match_all": {}
            # "match": {
            #     "message": "Mock log message"
            # }
        }
    }
    response = requests.post(f"http://{es_ip}:{es_port}/{INDEX_NAME}-*/_search", json=query)

    assert response.status_code == 200
    response_data = response.json()
    print("#" * 50, "query")
    import pprint
    pprint.pprint(response_data)
    assert response_data["hits"]["total"]["value"] == 1

