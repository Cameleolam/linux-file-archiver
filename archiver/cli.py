"""CLI entry point for file-archiver.

Handles argument parsing, config loading, logging setup, and orchestration.
This module is the glue - it doesn't contain business logic.

Entry point defined in pyproject.toml:
    [tool.poetry.scripts]
    file-archiver = "file_archiver.cli:main"
"""