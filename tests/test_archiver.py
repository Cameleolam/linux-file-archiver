"""Tests for the core archiver logic.

Test strategy:
- Mock system calls (grp, pwd) for group/user resolution
- Use real filesystem (tmp_path) for file operations
- Test each edge case from DESIGN.md

QUESTION FOR YOU: Do you test every function individually (unit)
or test archive_group end-to-end (integration)? Both.
Unit tests for should_exclude, archive_file (these are pure-ish).
Integration test for archive_group with mocked system calls and real files.
"""