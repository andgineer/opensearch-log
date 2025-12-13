# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Setup

Run `source ./activate.sh` to set up the development environment. This creates a Python virtual environment using uv and installs dependencies.

**IMPORTANT**: Always activate the virtual environment before running any commands. Use `source ./activate.sh` before each command.

## Common Commands

### Development
- `source ./activate.sh && make help` - Show all available make targets
- `source ./activate.sh && make reqs` - Upgrade requirements including pre-commit hooks
- `source ./activate.sh && uv pip install -r requirements.dev.txt` - Install development dependencies

### Testing
- `source ./activate.sh && python -m pytest` - Run all tests with doctest modules enabled
- `source ./activate.sh && python -m pytest -m docker` - Run tests that require Docker (testcontainers)
- `source ./activate.sh && python -m pytest -m opensearch` - Run tests that use OpenSearch

**Note**: Always use `python -m pytest` instead of just `pytest` to ensure proper Python path setup for imports.

### Linting and Formatting
- `source ./activate.sh && pre-commit run --all-files` - Run all pre-commit hooks (includes ruff and mypy)

**IMPORTANT**: Always use `pre-commit run --all-files` for code quality checks. Never run ruff or mypy directly.

### Documentation
- `source ./activate.sh && make docs` - Preview English documentation
- `source ./activate.sh && make docs-ru` - Preview Russian documentation

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
