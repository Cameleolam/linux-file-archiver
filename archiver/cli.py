"""CLI entry point for file-archiver.

Handles argument parsing, config loading, logging setup, and orchestration.
This module is the glue - it doesn't contain business logic.

Entry point defined in pyproject.toml:
    [tool.poetry.scripts]
    file-archiver = "archiver.cli:main"
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from archiver.archiver import ArchiveResult, archive_group
from archiver.config import Config, load_config, merge_configs
from archiver.locking import FileLock, LockAcquisitionError

# Linux convention for system-wide config. Installed by .deb package.
DEFAULT_CONFIG_PATH = Path("/etc/file-archiver/config.toml")

logger = logging.getLogger("file-archiver")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Arguments:
      --group GROUP        (required) Linux group name to archive
      --archive-dir DIR    Override archive directory
      --config PATH        Config file path (default: /etc/file-archiver/config.toml)
      --dry-run            Log what would happen without moving files
      --report json        Output machine-readable summary to stdout
      --verbose            Enable DEBUG level logging
    """
    parser = argparse.ArgumentParser(
        prog="file-archiver",
        description="Archive files for members of a specified Linux group.",
    )
    parser.add_argument("--group", required=True,
                        help="Linux group name to archive")
    parser.add_argument("--archive-dir", metavar="DIR",
                        help="Override archive directory")
    parser.add_argument("--config", metavar="PATH",
                        default=DEFAULT_CONFIG_PATH,
                        help="Config file path (default: /etc/file-archiver/config.toml)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Log what would happen without moving files")
    parser.add_argument("--report", choices=["json"],
                        help="Output machine-readable summary to stdout")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable DEBUG level logging")

    return parser.parse_args(argv)


def setup_logging(log_file: Path, verbose: bool = False) -> None:
    """Configure logging to stderr and optionally a log file.

    stderr for log messages, stdout reserved for --report output only.
    Falls back to stderr-only if log file path isn't writable.
    """
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-5s [%(name)s] %(message)s"
    )

    # Stream handler (stderr): same level as root logger
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    # File handler: fall back to stderr-only if path isn't writable
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (PermissionError, FileNotFoundError):
        logger.warning(f"Cannot write to {log_file}, logging to stderr only")

def print_report(results: list[ArchiveResult], format: str) -> None:
    """Print machine-readable report to stdout.
    """
    pass


def main(argv: list[str] | None = None) -> int:
    """Main entry point. Returns exit code.

    Args:
        argv: CLI arguments (None defaults to sys.argv, for testing)

    Exit codes:
        0: success
        1: fatal (no results)
        2: partial (some moved, some errors)
    """
    args = parse_args(argv)

    explicit = args.config != DEFAULT_CONFIG_PATH
    file_config = load_config(Path(args.config), explicit)

    config = merge_configs(file_config, vars(args))

    setup_logging(config.log_file, config.verbose)

    try:
        with FileLock(config.lock_file):
            results = archive_group(config)
    except LockAcquisitionError:
        logger.info("Another instance is running. Exiting")
        return 0

    # Aggregate results
    total_moved = sum(r.files_moved for r in results)
    total_skipped = sum(r.files_skipped for r in results)
    total_errors = sum(r.errors for r in results)

    # Log error details
    for r in results:
        for err_msg in r.error_messages:
            logger.warning(f"[{r.username}] {err_msg}")

    # Summary
    logger.info(
        f"Done: {total_moved} moved, {total_skipped} skipped, "
        f"{total_errors} errors"
    )

    # Report if requested
    if args.report:
        print_report(results, args.report)

    # Exit code: 0 = success, 1 = fatal (no results), 2 = partial
    if not results:
        return 1
    if total_errors and total_moved:
        return 2
    if total_errors:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
