"""Configuration loading and merging.

Precedence: CLI args > config file > defaults.
Uses tomllib (stdlib since Python 3.11) - zero external dependencies.
"""

from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_ARCHIVE_FOLDER_LOCATION = "/var/archive"
DEFAULT_LOCK_FILE_PATH_LOCATION = "/var/lock/archiver.lock"
DEFAULT_LOG_FILE_LOCATION = "/var/log/archiver.log"

DEFAULT_EXCLUDE_PATTERNS = [
    ".ssh/*",
    ".gnupg/*",
    ".bash_history",
    ".bashrc",
    ".profile",
    ".bash_logout",
    "*.tmp",
    ".cache/*",
    "__pycache__/*",
    ".local/share/Trash/*",
]


@dataclass
class Config:
    """Archiver runtime configuration"""

    group: str
    archive_dir: Path = field(
        default_factory=lambda: Path(DEFAULT_ARCHIVE_FOLDER_LOCATION)
    )
    lock_file: Path = field(
        default_factory=lambda: Path(DEFAULT_LOCK_FILE_PATH_LOCATION)
    )
    log_file: Path = field(
        default_factory=lambda: Path(DEFAULT_LOG_FILE_LOCATION)
    )
    exclude_patterns: list[str]=field(
        default_factory=lambda: list(DEFAULT_EXCLUDE_PATTERNS)
    )
    dry_run: bool = False
    verbose: bool = False
    report_format: str | None = None # None = no report, "json" = JSON to stdout


def load_config(config_path: Path, explicit: bool) -> dict[str, Any]:
    """Load a TOML config file and return its contents as a raw dict.

    Args:
        config_path: Path to the TOML configuration file.
        explicit: Whether the user explicitly passed --config.
            If True and file is missing, raises FileNotFoundError.
            If False and file is missing, returns empty dict (use defaults).

    Raises:
        FileNotFoundError: If explicit is True and config_path doesn't exist.
        tomllib.TOMLDecodeError: If the file contains invalid TOML.
    """

    config: dict[str, Any] = {}
    if not config_path.exists():
        if not explicit:
            logger.info(f"Config file: {config_path!s} does not exist, using defaults \
                        since no explicit --config flag")
            return config
        else:
            logger.error(f"Config file: {config_path!s} does not exist")
            raise FileNotFoundError
    try:
        with open(config_path, mode="rb") as fp:
            config = tomllib.load(fp)
    except tomllib.TOMLDecodeError as e:
        logger.error(f"Failed to parse config: {config_path!s}: {e}")
        raise

    return config


def merge_configs(
    file_config: dict[str, Any],
    cli_args: dict[str, Any],
) -> Config:
    """Merge file config and CLI args into a Config instance.

    Precedence: cli_args > file_config > dataclass defaults.
    Strings are coerced to Path for directory/file fields.

    Args:
        file_config: Raw dict from load_config (may be empty).
        cli_args: Dict from argparse (unset args are None).

    Raises:
        ValueError: If group is not provided in cli_args.
    """
    merged = {}

    # group is required - argparse enforces this, but double check
    if (group := cli_args.get("group")) is None:
        err_msg = "group argument is mandatory"
        logger.error(err_msg)
        raise ValueError(err_msg)
    merged["group"] = group

    # Exclude patterns: nested in TOML, flat in Config
    exclude = file_config.get("exclude", {}).get("patterns", [])
    if exclude:
        merged["exclude_patterns"] = exclude

    # Path fields: cli_args > file_config > dataclass default
    for key in ("archive_dir", "log_file", "lock_file"):
        if cli_args.get(key) is not None:
            merged[key] = Path(cli_args[key])
        elif key in file_config:
            merged[key] = Path(file_config[key])

    # Bool/str fields: cli_args > file_config > dataclass default
    for key in ("dry_run", "verbose", "report_format"):
        if cli_args.get(key) is not None:
            merged[key] = cli_args[key]
        elif key in file_config:
            merged[key] = file_config[key]

    return Config(**merged)

