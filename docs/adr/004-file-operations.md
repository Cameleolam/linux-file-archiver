# 004 - File Operations & Traversal

## Context
The core operation is walking user home directories and moving files to an archive
while preserving directory structure. Several subtle decisions affect correctness
and performance.

## Questions & Answers

### Q: shutil.move vs Path.rename?
**A: shutil.move.** `Path.rename` fails with OSError if source and destination are
on different filesystems (different partitions). Since `/home` and `/var/archive`
could easily be on different partitions, `shutil.move` is the safe choice.

`shutil.move` handles cross-filesystem transparently: same filesystem = rename
(instant, atomic), different filesystem = copy + delete (slower, non-atomic but
protected by our file lock).

### Q: home.rglob("*") vs os.walk?
**A: os.walk with directory pruning.** `os.walk` lets us skip entire excluded
directories without entering them:

```python
for dirpath, dirnames, filenames in os.walk(home):
    # Remove excluded dirs IN PLACE to prevent descending
    dirnames[:] = [d for d in dirnames if not is_excluded_dir(d)]
    for filename in filenames:
        ...
```

With `rglob("*")`, we'd visit every file inside `.cache/` (potentially thousands)
only to skip them all. For a user with 10GB of cache, that's wasted I/O.

Trade-off: `os.walk` is slightly more verbose than `rglob`. Worth it for performance
on real home directories.

### Q: Symlink check order - why is_symlink() before is_file()?
**A: Because is_file() follows symlinks.** A symlink pointing to a regular file
returns True for BOTH `is_symlink()` and `is_file()`. If you check `is_file()`
first and process the file, you're silently following the symlink and moving the
target - potentially a file outside the home directory.

Check order must be:
1. `is_symlink()` → skip and log WARNING
2. `is_file()` → process normally
3. Everything else (dirs, special files) → skip

### Q: fnmatch doesn't match nested paths. How to handle exclude patterns?
**A: Two-strategy matching.** `fnmatch(".cache/deep/file.txt", ".cache/*")` returns
False because `*` doesn't match `/`. We need two checks:

```python
def should_exclude(relative_path: Path, patterns: list[str]) -> bool:
    path_str = str(relative_path)
    for pattern in patterns:
        # Directory patterns: check if path is under excluded prefix
        prefix = pattern.rstrip("/*")
        if path_str == prefix or path_str.startswith(prefix + "/"):
            return True
        # Filename patterns: match against just the filename
        if fnmatch.fnmatch(relative_path.name, pattern):
            return True
    return False
```

This handles both `.cache/*` (directory pattern matching nested files) and
`*.tmp` (filename glob matching at any depth). Simple, correct, no external deps.

### Q: Preserve file permissions and timestamps?
**A: Yes, automatically.** `shutil.move` preserves permissions, ownership, and
timestamps. No extra code needed. If running as root, archived files keep their
original owner/group - correct behavior for a restore scenario.

Future extension: write archive metadata (file list, timestamps, checksums) to a
manifest file per user. Not implementing now.

### Q: Move vs copy - the spec says "move"?
**A: Move.** The task explicitly says "move files from user home directories."
Move means originals are gone. That's the purpose: clean up home directories,
archive files safely elsewhere.

Also: move on same filesystem is instant (inode rename). Copy would read/write
every byte then require a separate delete pass. Move is the correct and
performant operation.

### Q: Very large home directories?
**A: No special handling needed.** `os.walk` streams entries, doesn't load
everything into memory. `shutil.move` on same filesystem is instant per file.
Log file counts per user so operators can see progress. Path length limit on
Linux is 4096 chars, rarely a concern.

## Decision

### File Traversal
- `os.walk` with in-place directory pruning for excluded directories
- Check order per path: symlink → file → skip anything else
- Relative path preserved: `/home/alice/docs/report.txt` → `/var/archive/alice/docs/report.txt`

### File Operations
- `shutil.move` for all file moves (cross-filesystem safe)
- Create destination parent directories with `mkdir(parents=True, exist_ok=True)`
- Never overwrite: if destination exists, skip and log INFO
- PermissionError: log ERROR, continue to next file

### Exclude Pattern Matching
- Two-strategy: prefix match for directory patterns, fnmatch on filename for globs
- Applied during traversal: excluded directories are pruned from os.walk (never entered)
- Excluded files are skipped individually

### Symlink Handling
- All symlinks are skipped and logged as WARNING
- Future: follow symlinks that resolve within /home boundary