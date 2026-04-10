# Architecture

## Config format
### Interrogations
- YAML
    - python3-yaml needed
    - heavier install
    - can break or have vulnerability
- TOML
    - tomllib included in python 3.11+
    - better than .env files
### Decision
TOML : matches our needs, and if installed on a server, the fewer dependencies the better

## Symlinks
### Interrogations
Should we follow symlinks on file moving?
### Decision
- Symlinks should not be followed for now, could archive files outside of /home
    - skip and flag them for now
    - future improvements : follow symlinks till they leave home. if they do : skip/log them

## Files moving : which files
### Interrogations
Should we move all files including dotfiles?
Some dotfiles may contain sensitive informations we cannot archive
Some may contain informations we'd like to keep (configs etc)
### Decision
- Default behaviour should archive everything
- Exclude system dotfiles with an exclude_pattern

Example exclude pattern

```toml
[exclude]
patterns = [
    ".ssh/*",
    ".gnupg/*",
    ".bash_history",
    "*.tmp",
    ".cache/*",
]
```

## Robustness

### Interrogations
- file locking (parallel runs collision)
    - `python3-filelock`
    - `flock` with context manager ?
    - `lslocks`
- handling files that are already archived
- handling missing directories
- handling permissions issues gracefully

Idempotent:
- If a file was already archived (exists in archive, not in home), skip it.
- If a file exists in both (partial previous run that crashed), compare and decide (overwrite? skip? log warning?)


Edge cases examples :
- user has no home directory
- home directory is empty
- permission denied on a file
- symlinks (follow or skip?)
- file modified during archival
- archive directory doesn't exist (create it)
- user deleted from group between group lookup and file access

### Decision
Requires its own ADR

## Usage
### Interface
- CLI
    - Installs a CLI script
    - Checks before start if config files are filled
    - Ask before starting the script if parameters are valid
    - Flags
        - `group` default parameter asked in the task
        - `report` optional parameter to output summary in JSON
        - `dry-run` optional/future parameter to log everything without moving anything
        - `user` optional/future parameter to select a specific user in the group
- Dojo UI ?? ;)

### Decision
Will skip UI for now, CLI is good enough : CLI + flags

<br/>
usage example :

```bash
archiver --group testarchive --report json
```

report example :
```json
{
    "group": "testarchive",
    "users": 2,
    "files_moved": 15,
    "files_skipped": 3,
    "errors": 0,
    "duration_seconds": 1.2
}
```

## Logging
### Interrogations
File / stdout ?
### Decision

Logging example :
```sh
2026-04-01 10:30:01 INFO  Starting archive for group 'testarchive'
2026-04-01 10:30:01 INFO  Lock acquired: /var/lock/archiver.lock
2026-04-01 10:30:01 INFO  Group 'testarchive' has 2 members: alice, bob
2026-04-01 10:30:01 INFO  Archiving user 'alice' from /home/alice
2026-04-01 10:30:01 INFO  Moved: /home/alice/documents/report.txt → /var/archive/alice/documents/report.txt
2026-04-01 10:30:01 WARN  Permission denied: /home/alice/.ssh/id_rsa (skipped)
2026-04-01 10:30:02 INFO  Archiving user 'bob' from /home/bob
2026-04-01 10:30:02 INFO  Moved: /home/bob/projects/src/main.py → /var/archive/bob/projects/src/main.py
2026-04-01 10:30:02 INFO  Archive complete. Moved: 2, Skipped: 1, Errors: 0
```

Both to file and stdout. Python `logging` module with a formatter.