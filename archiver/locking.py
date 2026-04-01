"""File-based locking to prevent concurrent runs.

Uses fcntl.flock (advisory lock) on a lock file.
Advisory means: the lock only works if all processes cooperate
by checking the same lock file. A process that ignores the lock
can still access files. This is standard for Linux CLI tools.
"""

from __future__ import annotations

import fcntl
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LockAcquisitionError(Exception):
    """Raised when the lock file cannot be acquired."""

    pass


class FileLock:
    """Context manager for file-based locking
    Advisory locking was chosen for simplicity"""

    def __init__(self, file_path: Path | str):
        """Stores the file path"""
        self.file_path = file_path
        self._file = None

    def __enter__(self):
        """Opens the file in append mode, calls the file lock
        and catches BlockingIOError"""

        self._file = open(file=self.file_path, mode="a")
        try:
            fcntl.flock(
                self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB
            )
        except BlockingIOError as e:
            self._file.close()
            logger.info("Another instance is running")
            raise (
                LockAcquisitionError(
                    f"File lock couldn't be acquired on file {self.file_path}")
            ) from e

        return self

    def __exit__(self, type, value, traceback):
        """Closes the file"""
        self._file.close()
