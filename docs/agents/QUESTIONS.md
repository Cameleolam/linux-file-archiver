# Architecture Questions - Closed

All questions raised during design, with final answers.
These are the questions the Univention dev will probe in the tech interview.

---

## config.py

**1. Dataclass vs NamedTuple vs dict for Config?**
→ Dataclass. Typed, default values, mutable during construction. NamedTuple is immutable (awkward for merging). Dict has no type safety.

**2. Missing config file: error or silent?**
→ Explicit `--config /bad/path` → error, exit 1. Default path missing → use defaults, INFO log.

**3. Invalid TOML: how to handle?**
→ Catch `tomllib.TOMLDecodeError`, wrap with filename for friendly message. Checked at startup.

**4. Nested [exclude] section from TOML?**
→ Navigate the dict: `data.get("exclude", {}).get("patterns", [])`. No flattening.

**5. Type coercion (str to Path): where?**
→ In `merge_config`. Single place. Returns fully typed Config with Paths.

---

## locking.py

**6. Advisory vs mandatory locking?**
→ Advisory (`fcntl.flock`). Standard for CLI tools. Cooperative. Rogue processes are out of scope - document as known limitation.

**7. What happens on crash?**
→ Lock auto-released. `fcntl.flock` tied to FD. Kernel closes FDs on process death. No stale locks. Key advantage over PID files.

**8. Context manager class vs contextlib?**
→ Class. Stores FD state explicitly between `__enter__` and `__exit__`.

**9. LOCK_EX | LOCK_NB?**
→ Yes. Exclusive + non-blocking. Try lock, fail immediately if locked, exit 0.

**10. Delete lock file on exit?**
→ No. One file, reused forever. Deleting creates race condition. Lock is on the FD, not the file's existence.

**11. File open mode?**
→ "a" (append). Contents don't matter, just need an FD. "w" truncates unnecessarily.

---

## archiver.py

**12. Handle primary group members?**
→ Yes. `grp.getgrnam` only returns secondary members. Also iterate `pwd.getpwall()` to find users with matching primary `pw_gid`. Merge and deduplicate. Shows Linux systems knowledge.

**13. Home dir doesn't exist on disk?**
→ Skip with WARNING. Separate log messages for "user not found" vs "home doesn't exist."

**14. fnmatch doesn't match nested paths?**
→ Two-strategy matching: prefix match for directory patterns (`.cache/*` → startswith), fnmatch on filename for globs (`*.tmp`). No PurePath, just string operations.

**15. shutil.move vs Path.rename?**
→ `shutil.move`. Cross-filesystem safe. `/home` and `/var/archive` may be different partitions.

**16. Symlink check order?**
→ `is_symlink()` BEFORE `is_file()`. `is_file()` follows symlinks - a symlink to a file returns True for both. Wrong order = silently following symlinks.

**17. rglob vs os.walk?**
→ `os.walk` with directory pruning. Skip excluded directories entirely instead of visiting every file inside them. More code, better performance on real home directories.

**18. Preserve permissions/timestamps?**
→ Yes, automatically. `shutil.move` preserves all. No extra code needed. Future: manifest file with metadata per user.

---

## cli.py

**19. Logs to stdout or stderr?**
→ stderr for logs, stdout for `--report` only. Unix convention enables clean piping.

**20. Log file dir not writable?**
→ Checked at startup. Fall back to stderr-only with WARNING. Don't crash.

**21. Return int vs sys.exit()?**
→ Return int from `main()`. Testable: `assert main(["--group", "test"]) == 0`. `sys.exit()` only in `if __name__ == "__main__"`.

**22. parse_args accepts argv?**
→ Yes. For testing: `parse_args(["--group", "testgroup"])` without monkeypatching sys.argv.

---

## tests

**23. monkeypatch vs mock.patch?**
→ monkeypatch. More pytest-idiomatic. Consistent throughout.

**24. Concurrent lock test?**
→ multiprocessing. `fcntl.flock` is per-process, not per-thread. Threads in same process share PID, both get the lock. Need separate PIDs.

**25. How thorough?**
→ Prioritize: file move, symlinks, exclude patterns, lock contention, group not found, permission error, primary group members. Stub the rest.

---

## General

**26. Require root?**
→ No. Handle PermissionError per file. Works as root (all homes) or non-root (own files). Document service account recommendation in README.

**27. Large home directories?**
→ No special handling. `os.walk` streams. Log file counts for progress visibility. Path length (4096) rarely a concern.

**28. Move vs copy?**
→ Move. Spec says "move." Originals gone from home. Move on same filesystem = instant rename. Lock protects concurrent access, not individual file operations.