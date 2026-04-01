"""Tests for file locking."""

import multiprocessing
import time

import pytest

from archiver.locking import FileLock, LockAcquisitionError


class TestFileLock:
    """Tests for FileLock context manager."""

    def test_lock_acquires_and_releases(self, tmp_path):
        """Happy path: lock acquired, used, released without error."""
        lock_file = tmp_path / "test.lock"
        # TODO: use FileLock as context manager, assert no exception
        with FileLock(lock_file):
            pass

    def test_lock_released_after_exit(self, tmp_path):
        """Lock can be re-acquired after the with block exits."""
        lock_file = tmp_path / "test.lock"
        with FileLock(lock_file):
            pass
        with FileLock(lock_file):
            pass

    def test_lock_contention_raises(self, tmp_path):
        """Second process cannot acquire a held lock."""
        lock_file = tmp_path / "test.lock"
        def _hold_lock(path, ready_event):
            with FileLock(path):
                ready_event.set()
                time.sleep(2)

        ready = multiprocessing.Event()
        child = multiprocessing.Process(target=_hold_lock, args=(lock_file, ready))
        child.start()
        ready.wait()
        with pytest.raises(LockAcquisitionError), FileLock(lock_file):
            pass
        child.join()

    def test_lock_creates_file(self, tmp_path):
        """Lock file is created if it doesn't exist."""
        lock_file = tmp_path / "test.lock"
        assert not lock_file.exists()
        with FileLock(lock_file):
            assert lock_file.exists()

    def test_lock_missing_parent_directory(self, tmp_path):
        """Lock file with nonexistent parent directory raises."""
        lock_file = tmp_path / "nonexistent" / "test.lock"
        with pytest.raises(FileNotFoundError), FileLock(lock_file):
            pass
