# 002 - Robustness & Concurrency

## Context
The program should be robust with respect to multiple invocations in short time.
Files are being moved from user home directories, which is a destructive operation.
We need to prevent data corruption from concurrent runs, handle partial failures
gracefully, and ensure the tool is idempotent.

## Questions & Answers

### Q: Advisory (fcntl.flock) vs mandatory locking?
**A: Advisory.** Standard for Linux CLI tools. Cooperative: only works if all processes
check the same lock file. A rogue process can bypass it, but that's true of any
user-space tool. We protect against the expected case: two file-archiver instances
running simultaneously (cron overlap, manual + scheduled run).

Known limitation: other tools accessing the same files are not prevented. Documented.

### Q: What happens if the process crashes while holding the lock?
**A: Lock is automatically released.** `fcntl.flock` is tied to the file descriptor.
When the process dies, the kernel closes all FDs, releasing the lock. No stale locks,
no cleanup needed. This is a key advantage over PID-file based locking, where you'd
need to check if the PID is still alive.

### Q: Context manager class or contextlib.contextmanager function?
**A: Class.** We need to store the file descriptor between `__enter__` and `__exit__`.
A class makes the FD lifecycle explicit. The contextlib approach works but hides
state in a generator, which is less readable for this use case.

### Q: LOCK_EX, LOCK_SH, LOCK_NB?
**A: LOCK_EX | LOCK_NB.**
- LOCK_SH: shared lock (for multiple process, and readonly access)
- LOCK_EX: exclusive lock (only one archiver at a time)
- LOCK_NB: non-blocking (if locked, fail immediately instead of waiting)
- Combined EX and NB: try to get exclusive lock, if can't, exit cleanly with code 0

We don't want the second instance to queue up and wait. It should detect
"another instance is running" and exit immediately.

### Q: Delete lock file on exit?
**A: No. Leave it.** The lock is on the file descriptor, not the file's existence.
One lock file (`/var/lock/file-archiver.lock`) is created once and reused forever.
0 bytes, harmless.

Deleting creates a race condition: process A deletes lock file, process B creates
a new one and locks it, process C creates another new one and locks it. Both B and C
hold locks on different files - no mutual exclusion. Leaving the file avoids this.

### Q: File open mode for lock file?
**A: "a" (append).** Contents don't matter, we just need a file descriptor.
"w" truncates (unnecessary side effect). "a" is harmless.

### Q: What about concurrent access to individual files?
The lock prevents two archiver instances from colliding. Individual file operations
(`shutil.move`) are atomic on the same filesystem (kernel-level inode rename).
Cross-filesystem moves are NOT atomic (copy + delete), but the lock prevents
a second archiver from touching the same files during the operation.

## Decision

### Locking Strategy
- Single lock file at configurable path (default: `/var/lock/file-archiver.lock`)
- `fcntl.flock` with `LOCK_EX | LOCK_NB`
- Context manager class wrapping the lock lifecycle
- If lock cannot be acquired: log INFO "Another instance is running", exit 0
- Lock file is never deleted

### Idempotent Behavior
- If file no longer exists in home (already moved or deleted): skip silently
- If file already exists in archive destination: skip, log INFO (never overwrite)
- Each run is safe to repeat: worst case it does nothing and logs "0 files moved"

### Error Handling Strategy
- Per-file errors (PermissionError, OSError): log ERROR, continue to next file
- Per-user errors (home doesn't exist): log WARNING, skip user, continue
- Fatal errors (group not found, invalid config): log ERROR, exit 1
- Partial success (some files moved, some errors): exit 2

### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | Success, or another instance already running |
| 1 | Fatal error (group not found, config invalid, archive dir not writable) |
| 2 | Partial success (some files archived, some errors occurred) |

## Known Limitations
- Advisory locking only: other tools can bypass the lock
- Cross-filesystem moves are not atomic (but are protected by the lock)
- No retry logic: if a file operation fails, it's logged and skipped