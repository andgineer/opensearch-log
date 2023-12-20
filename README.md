# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/andgineer/opensearch-log/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                          |    Stmts |     Miss |   Cover |   Missing |
|---------------------------------------------- | -------: | -------: | ------: | --------: |
| src/opensearch\_log/\_\_about\_\_.py          |        1 |        1 |      0% |         1 |
| src/opensearch\_log/base\_handler.py          |        8 |        1 |     88% |        17 |
| src/opensearch\_log/cloudwatch\_handler.py    |       86 |       14 |     84% |60-64, 86, 116-120, 144-152 |
| src/opensearch\_log/json\_log.py              |       73 |        0 |    100% |           |
| src/opensearch\_log/opensearch\_handler.py    |      139 |       30 |     78% |66, 83, 103, 123, 141-142, 151-174, 187, 233-248, 252-258 |
| src/opensearch\_log/opensearch\_serializer.py |        8 |        0 |    100% |           |
| src/opensearch\_log/stdout\_handler.py        |       16 |        0 |    100% |           |
|                                     **TOTAL** |  **331** |   **46** | **86%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/andgineer/opensearch-log/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/andgineer/opensearch-log/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/andgineer/opensearch-log/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/andgineer/opensearch-log/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fandgineer%2Fopensearch-log%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/andgineer/opensearch-log/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.