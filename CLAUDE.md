# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Setup

Run `. ./activate.sh` to set up the development environment. This creates a Python virtual environment using uv and installs dependencies.

## Common Commands

### Development
- `make help` - Show all available make targets
- `make reqs` - Upgrade requirements including pre-commit hooks
- `uv pip install -r requirements.dev.txt` - Install development dependencies

### Testing
- `source activate.sh && python -m pytest` - Run all tests with doctest modules enabled
- `python -m pytest -m docker` - Run tests that require Docker (testcontainers)
- `python -m pytest -m opensearch` - Run tests that use OpenSearch

**Note**: Always use `python -m pytest` instead of just `pytest` to ensure proper Python path setup for imports.

### Linting and Formatting
- `source activate.sh && pre-commit run --all-files` - Run all pre-commit hooks (includes ruff and mypy)

**Note**: Always activate the virtual environment with `source activate.sh` before running pre-commit hooks to ensure proper tool versions.

### Documentation
- `make docs` - Preview English documentation
- `make docs-ru` - Preview Russian documentation

## Architecture

The library provides Python logging handlers for sending logs to OpenSearch or AWS CloudWatch with JSON formatting and structured field support.

### Core Components

- **BaseHandler** (`base_handler.py`) - Abstract base class for all log handlers
- **OpensearchHandler** (`opensearch_handler.py`) - Sends logs to AWS OpenSearch with buffering, bulk operations, and automatic index rotation
- **CloudwatchHandler** (`cloudwatch_handler.py`) - Sends logs to AWS CloudWatch Logs with buffering
- **JSON logging** (`json_log.py`) - Core JSON formatting with context variables for additional fields
- **Context management** - `Logging` context manager and `@log_fields` decorator for adding structured fields

### Key Features

- **Buffered sending** - Both OpenSearch and CloudWatch handlers use buffering with configurable flush intervals
- **Field injection** - Thread-safe context variables allow adding structured fields to log records
- **AWS integration** - Automatic AWS authentication and region handling
- **Index management** - OpenSearch handler supports daily/monthly index rotation
- **Retry logic** - Built-in retry mechanisms for failed log transmissions

### Configuration

The library uses optional dependencies:
- `opensearch-log[opensearch]` for OpenSearch functionality
- `opensearch-log[cloudwatch]` for CloudWatch functionality

Python version: 3.9+ (configured in `activate.sh` and pyproject.toml)
