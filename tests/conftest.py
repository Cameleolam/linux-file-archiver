"""Shared test fixtures for file-archiver tests.

QUESTION FOR YOU: How do you test a tool that reads /etc/group and /etc/passwd?
You can't create real Linux users in CI. Two approaches:

1. Mock grp.getgrnam and pwd.getpwnam (unit tests, fast, no root needed)
2. Use tmp_path to create fake directory structures (integration tests)

We do both. Mock the system calls, use real filesystems for file operations.

QUESTION FOR YOU: conftest.py is automatically loaded by pytest for all tests
in this directory. Fixtures defined here are available to every test file
without importing. This is where shared setup goes.
"""