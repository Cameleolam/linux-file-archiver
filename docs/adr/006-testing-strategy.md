# 006 - Testing Strategy

## Context
The tool interacts with Linux system APIs (grp, pwd, fcntl) and the filesystem.
Testing requires mocking system calls while using real filesystem operations.

## Questions & Answers

### Q: monkeypatch vs unittest.mock.patch?
**A: monkeypatch.** More pytest-idiomatic. Cleaner syntax for replacing
module-level functions:
```python
def test_group_members(monkeypatch):
    fake = grp.struct_group(("testgroup", "x", 1000, ["alice", "bob"]))
    monkeypatch.setattr("grp.getgrnam", lambda name: fake)
```
Consistent throughout test suite. No mixing of mock styles.

### Q: How to test concurrent lock acquisition?
**A: multiprocessing, not threading.** `fcntl.flock` is per-process. Two threads
in the same process share the same PID, so both acquire the lock (kernel sees
same process). Multiprocessing spawns a child with a separate PID:
```python
def hold_lock(path, ready_event):
    with FileLock(path):
        ready_event.set()
        time.sleep(2)

ready = multiprocessing.Event()
p = multiprocessing.Process(target=hold_lock, args=(lock_path, ready))
p.start()
ready.wait()
# Parent tries to lock - should fail
```

### Q: How thorough should tests be?
**A: Prioritize.** Implement tests for the critical paths. Have stubs with
descriptive names for edge cases that time didn't allow.

## Decision

### Test Approach
- **Unit tests**: mock system calls (grp, pwd), test pure logic (should_exclude, config merging)
- **Integration tests**: real filesystem (tmp_path), real file moves, real directory structures
- **Concurrency test**: multiprocessing for lock contention

### Priority Tests (implement)
1. File move works and preserves structure
2. Symlinks are skipped
3. Exclude patterns work (including nested directories)
4. Lock contention (second instance exits cleanly)
5. Group not found → exit 1
6. Permission denied on file → logged, continues
7. Already-archived file → skipped
8. Primary + secondary group members both found

### Lower Priority (stub only if time allows)
9. Disk full during move
10. File deleted during walk
11. Very large directory traversal
12. Cross-filesystem move
13. Config file missing vs explicitly requested

### Fixtures
- `tmp_path` (pytest built-in): unique temp dir per test, auto-cleaned
- `tmp_home`: fake home directory with files, symlinks, dotfiles
- `tmp_archive`: empty archive destination
- `sample_config`: Config pointing to temp directories (no root needed)

### Mocking Strategy
- `grp.getgrnam` → fake struct_group with test members
- `pwd.getpwnam` → fake struct_passwd with home in tmp_path
- `pwd.getpwall` → list of fake users for primary group detection
- NO mocking of filesystem operations: use real files in tmp_path