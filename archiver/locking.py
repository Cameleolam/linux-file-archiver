"""File-based locking to prevent concurrent runs.

Uses fcntl.flock (advisory lock) on a lock file.
Advisory means: the lock only works if all processes cooperate
by checking the same lock file. A process that ignores the lock
can still access files. This is standard for Linux CLI tools.

QUESTION FOR YOU: advisory vs mandatory locking?
- Advisory (fcntl.flock): cooperative, standard, what cron jobs use
- Mandatory: enforced by kernel, requires special filesystem mount options
  (mand option + setgid bit), almost never used in practice
Advisory is the right choice here.

QUESTION FOR YOU: What happens if the process crashes while holding the lock?
fcntl.flock is automatically released when the file descriptor is closed,
which happens when the process dies (kernel cleans up FDs). So a crash
won't leave a stale lock. This is a key advantage over PID-file based locking.
"""