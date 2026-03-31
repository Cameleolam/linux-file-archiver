"""Tests for file locking.

QUESTION FOR YOU: How do you test that two processes can't hold the lock
simultaneously? Options:
1. multiprocessing: spawn a child that holds the lock, try to acquire in parent
2. threading: similar but same process (fcntl locks are per-process, not per-thread!)
3. subprocess: cleanest - run a separate Python process that holds the lock

fcntl.flock is per-process, so threading won't work for testing contention.
Use multiprocessing or subprocess.
"""