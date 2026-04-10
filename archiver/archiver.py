"""Core archival logic.

Resolves group members, walks home directories, moves files to archive
preserving the original directory structure.

Design principle: functions are pure where possible (take inputs, return results).
Side effects (file moves, logging) are explicit and contained.
"""

from __future__ import annotations

import fnmatch
import grp
import logging
import os
import pwd
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from archiver.config import Config

logger = logging.getLogger(__name__)


@dataclass
class ArchiveResult:
    """Result of archiving a single user's files."""

    username: str
    home_dir: Path | None
    files_moved: int = 0
    files_skipped: int = 0
    errors: int = 0
    error_messages: list[str] = field(default_factory=list)


def get_group_members(group_name: str) -> list[str]:
    """Get all members of a Linux group (primary + secondary).

    Args:
        group_name: The Linux group name to resolve.

    Returns:
        Deduplicated list of usernames belonging to the group.

    Raises:
        KeyError: If the group does not exist.

    grp.getgrnam only returns secondary members (gr_mem).
    Primary group members found via pwd.getpwall() GID scan.
    KeyError propagates if group doesn't exist - caller handles it.
    """
    group_info = grp.getgrnam(group_name)
    gid = group_info.gr_gid
    secondary_members = list(group_info.gr_mem)

    # Scan all users for those whose primary GID matches
    primary_members = [
        u.pw_name for u in pwd.getpwall() if u.pw_gid == gid
    ]

    # Merge + deduplicate, preserving order
    seen = set()
    members = []
    for name in secondary_members + primary_members:
        if name not in seen:
            seen.add(name)
            members.append(name)

    return members


def get_user_home(username: str) -> Path | None:
    """Get a user's home directory, or None if unavailable.

    Args:
        username: The Linux username.

    Returns:
        Path to home directory, or None if user not found or home missing.

    Home in /etc/passwd might not exist on disk (--no-create-home).
    Checks Path.exists() here and logs the specific reason.
    """
    try:
        pw = pwd.getpwnam(username)
    except KeyError:
        logger.warning(f"User '{username}' not found in system")
        return None

    home = Path(pw.pw_dir)
    if not home.exists():
        logger.warning(
            f"User '{username}' home directory {home} does not exist"
        )
        return None

    return home


def should_exclude(relative_path: Path, patterns: list[str]) -> bool:
    """Check if a file should be excluded from archival.

    Two-strategy matching (ADR 004):
    - Directory patterns (e.g. ".cache/*"): strip "/*", check startswith
    - Filename patterns (e.g. "*.tmp"): fnmatch on filename only

    Args:
        relative_path: Path relative to user's home directory.
        patterns: List of exclude patterns from config.

    Returns:
        True if the file should be skipped.

    fnmatch doesn't recurse: .cache/* won't match .cache/deep/file.txt.
    So we use prefix matching for directory patterns and fnmatch for filenames.
    """
    path_str = str(relative_path)
    for pattern in patterns:
        # Directory patterns: .cache/* -> check if path is under .cache/
        prefix = pattern.rstrip("/*")
        if path_str == prefix or path_str.startswith(prefix + "/"):
            return True
        # Filename patterns: *.tmp -> match against just the filename
        if fnmatch.fnmatch(relative_path.name, pattern):
            return True
    return False


def archive_file(
    src: Path,
    dest: Path,
    dry_run: bool = False,
) -> bool:
    """Move a single file from src to dest, creating parent dirs.

    Uses shutil.move for cross-filesystem safety. Never overwrites.

    Args:
        src: Source file path.
        dest: Destination file path.
        dry_run: If True, log but don't move.

    Returns:
        True if moved (or would move in dry_run), False if skipped.

    shutil.move over Path.rename for cross-filesystem safety.
    Preserves permissions, ownership, and timestamps.
    """
    if dest.exists():
        logger.info(f"Skipping {src}: already exists at {dest}")
        return False

    if dry_run:
        logger.info(f"Would move: {src} -> {dest}")
        return True

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    logger.info(f"Moved: {src} -> {dest}")
    return True


def archive_user(
    username: str,
    home: Path,
    archive_dir: Path,
    exclude_patterns: list[str],
    dry_run: bool = False,
) -> ArchiveResult:
    """Archive all files from a user's home directory.

    Walks home with os.walk, prunes excluded dirs, skips symlinks,
    moves files with shutil.move.

    Args:
        username: The user whose files are being archived.
        home: Path to user's home directory.
        archive_dir: Base archive directory (user subdir created inside).
        exclude_patterns: Glob patterns to skip.
        dry_run: If True, log but don't move.

    Returns:
        ArchiveResult with counts and any error messages.

    os.walk chosen over rglob for directory pruning (ADR 004).
    Symlink check before is_file() - symlinks to files return True for both.
    """
    result = ArchiveResult(username=username, home_dir=home)

    for dirpath_str, dirnames, filenames in os.walk(home):
        dirpath = Path(dirpath_str)

        # Prune excluded directories in-place to avoid descending
        dirnames[:] = [
            d for d in dirnames
            if not should_exclude(
                Path(dirpath / d).relative_to(home), exclude_patterns
            )
        ]

        for filename in filenames:
            filepath = dirpath / filename
            relative_path = filepath.relative_to(home)

            # Symlinks: check BEFORE is_file()
            if filepath.is_symlink():
                logger.warning(f"Skipping symlink: {filepath}")
                result.files_skipped += 1
                continue

            if not filepath.is_file():
                continue

            if should_exclude(relative_path, exclude_patterns):
                result.files_skipped += 1
                continue

            dest = archive_dir / username / relative_path

            try:
                if archive_file(filepath, dest, dry_run):
                    result.files_moved += 1
                else:
                    result.files_skipped += 1
            except PermissionError as e:
                logger.error(f"Permission denied: {filepath}: {e}")
                result.errors += 1
                result.error_messages.append(str(e))
            except OSError as e:
                logger.error(f"Error archiving {filepath}: {e}")
                result.errors += 1
                result.error_messages.append(str(e))

    return result


def archive_group(config: Config) -> list[ArchiveResult]:
    """Archive files for all members of a group. Main entry point for cli.py.

    Args:
        config: Validated Config instance.

    Returns:
        List of ArchiveResult, one per group member.
        cli.py computes exit code (0/1/2) from this.

    archive_dir creation happens here - the archiver owns the concept.
    """
    results: list[ArchiveResult] = []

    try:
        members = get_group_members(config.group)
    except KeyError:
        logger.error(f"Group '{config.group}' not found")
        return results

    if not members:
        logger.info(f"Group '{config.group}' has no members")
        return results

    logger.info(
        f"Group '{config.group}' has {len(members)} members: "
        f"{', '.join(members)}"
    )

    config.archive_dir.mkdir(parents=True, exist_ok=True)

    for username in members:
        home = get_user_home(username)
        if home is None:
            results.append(
                ArchiveResult(username=username, home_dir=None)
            )
            continue

        logger.info(f"Archiving user '{username}' from {home}")
        result = archive_user(
            username,
            home,
            config.archive_dir,
            config.exclude_patterns,
            config.dry_run,
        )
        logger.info(
            f"User '{username}': moved={result.files_moved}, "
            f"skipped={result.files_skipped}, errors={result.errors}"
        )
        results.append(result)

    total_moved = sum(r.files_moved for r in results)
    total_errors = sum(r.errors for r in results)
    logger.info(
        f"Archive complete. Total moved={total_moved}, errors={total_errors}"
    )

    return results
