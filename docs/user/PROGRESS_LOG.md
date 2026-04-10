# General progress log
Logging hours spent and actions done.
Consciously logging anything to keep track of my progress and questions

## 31/03/2026: 6h

#### General project exploration
- Wrote `task.md` : project task
- Wrote `to_explore.md` : modules/subjects/anything related to the project I need a refresh on or to learn

#### Packages ?
For now, most of the task should be doable with python integrated modules
- `grp`: get groups members
- `pwd`: get home directories
- `pathlib`/`shutil`: move files preserving structure
- `logging`: logging events

#### Read docs on debian user management
Quick reminder but mostly too much informations
[Debian UserAccounts](https://wiki.debian.org/UserAccounts)

#### Read parts of the docs on debian packaging
Never did debian packaging before, should take another look at it later
[Debian Packaging](https://wiki.debian.org/Packaging)
[Python LibraryStyleGuide](https://wiki.debian.org/Python/LibraryStyleGuide)

- PEP 517 compliant
    - `pyproject.toml` or `setup.cfg` file
    - should be installable without modification into a `virtual env`
- Pure python or simple extension module
- Python 3 +
- Upstream-provided test suite
- Has [Sphinx-based documentation](https://wiki.debian.org/SphinxDocumentation)

- `dpkg-buildpackage`
- debian/ directory with control
- rules
- changelog
- ... ?

#### Read docs on file management

[Debian CommandsFileManager](https://wiki.debian.org/CommandsFileManager)

#### Read docs on file lock

[File locking on Linux](https://www.baeldung.com/linux/file-locking)
[filelock library (windows only)](https://py-filelock.readthedocs.io/en/latest/) 

Never did file lock before. Raised questions on robustness. Available [here](../adr/001-architecture.md#Robustness)

#### Wrote ADR 001

[here](../adr/001-architecture.md)

#### Debian distro and tooling installation
```sh
# -- now in windows
wsl --install -d Debian
# -- now in Debian - set root username/pwd
# tooling installation
sudo apt update
sudo apt upgrade -y
sudo apt install python3 python3-venv
sudo apt install pipx #python packager
pipx ensure-path
pipx install poetry #package manager
pipx install ruff #linter/formatter
pipx install mypy #static type checker
mkdir -p ~/projects/archiver
cd ~/projects/archiver
poetry config virtualenvs.in-project true
poetry init
# tweaking the pyproject.toml a bit before the install
poetry install
# claude code installation (curl and node needed)
sudo apt install curl
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash -
sudo apt install -y nodejs
cd
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
npm install -g @anthropic-ai/claude-code
claude --version #ok
# git install
sudo apt-get install git
# configured git
sudo apt install man-db manpages manpages-dev
# read docs and iterated with ai
# commit docs and architecture
```

##### Iterated with Claude (chat) about questions on the architecture

Iterated on architecture questions with AI, validated decisions, wrote ADRs

##### Thought process for ADR 002 - Robustness

"robust with respect to multiple invocations in short time."                                                                                                                                            
   
How do Linux tools typically prevent concurrent runs?
1. PID files - write your PID to a file, check if that PID is alive. Problem: stale PIDs after crashes.pitfalls.                                                                      
2. flock command - man flock. Shell command for this: flock -n /var/lock/mylock mycommand. Kernel has a locking primitive for exactly this use case.
3. fcntl.flock in Python

Docs read :
- `man flock`
- `man 2 flock`
- `man fcntl`


- "I need mutual exclusion between processes" : that's a lock   
- "Linux has this built in?" : man flock, yes
- "Python equivalent?" : fcntl.flock in the stdlib
- "Should I block or fail?" : the second cron job shouldn't queue up : LOCK_NB                                                                                                                            
- "Exclusive or shared?" : only one archiver at a time : LOCK_EX                                                                                                                                       
- "What if it crashes?" : man flock says lock is released on FD close : no stale locks

Wrote ADRs 002 :
[Robustness decisions](../adr/002-robustness.md)

##### Thought process for ADR 003 - User & Group Handling

"archive files owned by members of a specified group"

- "How do I get group members in Python?" : `man group`, `man 3 getgrnam` : Python's `grp` module
- "Wait, `grp.getgrnam("mygroup").gr_mem` doesn't list users whose primary group it is" : primary vs secondary group distinction. `gr_mem` only returns secondary members. Primary group is the `gid` field in `/etc/passwd`.
- "How do I find primary group members?" : `man passwd`, `man 5 passwd` : scan all users and check their `pw_gid`. Python: `pwd.getpwall()`
- "What if a user has no home directory?" : `man useradd` : `--no-create-home` flag exists. `pw_dir` can point to a path that doesn't exist on disk.

Docs read :
- `man 5 group` and `man 5 passwd` (the file formats)
- [grp module](https://docs.python.org/3/library/grp.html)
- [pwd module](https://docs.python.org/3/library/pwd.html)

Try : `python3 -c "import grp; print(grp.getgrnam('sudo'))"` and compare with `getent group sudo`


Wrote ADRs 003 :
[User & Groups handling decisions](../adr/003-user-group-handling.md)

##### Thought process for ADR 004 - File Operations

"move files preserving directory structure"

- "How do I move a file in Python?" : `pathlib.Path.rename()` vs `shutil.move()`. : `Path.rename()` fails if source and dest are on different filesystems. `man 2 rename`: "EXDEV: oldpath and newpath are not on the same mounted filesystem." : `/home` and `/var/archive` could be on different partitions : must use `shutil.move()`
- "How do I walk a directory tree?" : `os.walk()` vs `Path.rglob()`. : `man find` shows the concept of pruning (not descending into directories). `os.walk` lets you modify `dirnames` in-place to prune. `rglob` doesn't.
- "Symlinks - what does `is_file()` do with them?" : `man 2 stat` vs `man 2 lstat`. `stat` follows symlinks, `lstat` doesn't. Python's `is_file()` uses `stat` (follows). `is_symlink()` uses `lstat` (doesn't follow). Check order matters.
- "How does `fnmatch` work?" : `man 7 glob` : `*` doesn't match `/`. So `.cache/*` won't match `.cache/deep/nested/file`. Need prefix matching for directory patterns.

Docs read :
- [shutil.move](https://docs.python.org/3/library/shutil.html#shutil.move)
- [os.walk](https://docs.python.org/3/library/os.html#os.walk)
- [fnmatch](https://docs.python.org/3/library/fnmatch.html)
- `man 2 rename` (the EXDEV error)
- `man 2 stat` vs `man 2 lstat`

Wrote ADRs 004 :
[File operations decisions](../adr/004-file-operations.md)

##### Thought process for ADR 005 - CLI, Logging & Config

"events and results should be available in a log file"

- "How do CLI tools handle config?" : look at tools I use: `ssh` has `~/.ssh/config`, `git` has cascading config (`system : global : local`). Same principle: defaults : file : CLI args.
- "TOML parsing in Python?" : already decided in ADR 001. `tomllib.load()` returns a dict. : How to go from nested dict to typed config? : dataclass with defaults.
- "Where should logs go?" : `man logger`, look at how `cron` and `rsync` do it. Convention: stderr for logs, stdout for data. Enables `archiver --report json 2>/dev/null | jq`.
- "How should `main()` exit?" : `man 3 exit`. `sys.exit()` raises `SystemExit` - awkward in tests. Returning an int from `main()` is testable: `assert main(["--group", "test"]) == 0`.

Docs read :
- [tomllib](https://docs.python.org/3/library/tomllib.html)
- [argparse](https://docs.python.org/3/library/argparse.html)
- [logging](https://docs.python.org/3/library/logging.html)
- [dataclasses](https://docs.python.org/3/library/dataclasses.html)

Wrote ADRs 005 :
[CLI Logging config decisions](../adr/005-cli-logging-config.md)

##### Thought process for ADR 006 - Testing

"how do I test code that touches system APIs and filesystem?"

- "Mock or real filesystem?" : both. Mock `grp`/`pwd` (can't create real Linux users in tests). Real filesystem via `tmp_path` (mocking file operations hides real bugs).
- "How do I test locking?" : `fcntl.flock` is per-process. Threads share the same FD table, so both acquire the lock. : must use `multiprocessing`.
- "How does pytest mocking work?" : monkeypatch is more pytest-idiomatic than `unittest.mock.patch`.

Docs read :
- [pytest tmp_path](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
- [pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- `man 2 flock` (the "per open file description" part explains why threads share locks)

Wrote ADRs 006 :
[Testing strategy decisions](../adr/006-testing-strategy.md)

## 01/04/2026: 1h

#### Wrote locking.py and test_locking.py
[Context manager](https://docs.python.org/3/reference/datamodel.html#with-statement-context-managers)
[fnctl.flock](https://docs.python.org/3/library/fcntl.html#fcntl.flock)
[BlockingIOError](https://docs.python.org/3/library/exceptions.html#BlockingIOError)

Wrote first pass, then corrected with claude. Wrote tests boilerplates, then filled it with claude and corrected it if necessary.

Ran adversarial review with codex
```md
  No-ship: the new lock acquisition path does not reliably classify lock contention, so a second instance can surface as an unhandled OS error instead of the documented clean "already running" exit path.                           
                                                                                                                                                                                                                                      
  Findings:                                                                                                                                                                                                                           
  - [high] Lock contention handling is too narrow and can misclassify a normal concurrent run as a hard failure (archiver/locking.py:38-48)                                                                                         
  fcntl.flock(..., LOCK_EX | LOCK_NB) does not guarantee a BlockingIOError on contention across platforms and emulation paths; the Python and flock(2) behavior allows other OSError variants for the same "would block" condition (commonly EACCES/EAGAIN). This implementation only translates BlockingIOError, so a legitimate second invocation can escape as a different exception instead of the intended "Another instance is running" path. The impact is user-visible: cron or automation that should no-op cleanly can fail noisy or nonzero during ordinary overlap. This is an inference from the documented flock error surface, but it is directly relevant to these lines because they hard-code a single exception class.                                                                                                                                                                                                
  Recommendation: Catch OSError from fcntl.flock, inspect errno, and translate both EAGAIN and EACCES contention cases into LockAcquisitionError while re-raising unrelated I/O errors unchanged. Add a test that simulates or asserts
   the broader errno-based handling so the clean-exit contract is actually locked in.                                                                                                                                               
                                                                                                                                                                                                                                      
  Next steps:
  - Broaden lock contention handling to errno-based OSError checks.                                                                                                                                                                   
  - Add a regression test for non-BlockingIOError contention behavior.  
```
EACCES concern applies to POSIX fcntl() record locks, not flock(). Irrelevant atm for Linux-only.


## 06/04/2026: 2h

#### Wrote config.py and test_config

Read ADR 5 again and necessary documentation (tomlib, argparse etc). Used dataclass over NamedTuple/dict, as decided in the ADR since it's mutable during construction and type safe + comes with defaults built in.
Wrote first pass, then corrected with claude. Wrote tests boilerplates (mostly happy paths), then filled it with claude and corrected it if necessary.

Ran adversarial review with codex
```
No-ship: the new config merge path accepts only the exact happy-path TOML shape and turns other syntactically valid configs into uncaught runtime exceptions instead of a controlled invalid-config failure.                      
                                                                                                                                                                                                                                    
  Findings:                                                                                                                                                                                                                         
  - [high] Malformed-but-valid TOML crashes during merge instead of being rejected cleanly (archiver/config.py:112-128)                                                                                                             
  load_config() only rejects syntax errors, but merge_configs() assumes the parsed object has the exact expected types. In particular, file_config.get("exclude", {}).get("patterns", []) will raise AttributeError if exclude is present but not a table, and Path(file_config[key]) will raise TypeError for non-string path values. This means a valid TOML file with the wrong shape can take the process down with a traceback during startup, which violates the documented invalid config -> exit 1 behavior and makes operator recovery harder. This is an inference from the current code paths; no schema validation exists before the merge.
  Recommendation: Add explicit schema/type validation before merging: verify [exclude] is a table, patterns is a list of strings, path fields are strings/path-like, and boolean/report fields have allowed types/values. Convert any mismatch into a ValueError that includes the offending field, and add regression tests for wrong-shaped but TOML-valid configs.

  Next steps:
  - Add negative tests for semantically invalid TOML shapes, not just parse errors.
  - Handle invalid config values with a controlled error path that surfaces the filename and field name.
```

Codex review flagged missing schema validation in merge_configs, like a valid TOML with wrong shape would crash with AttributeError instead of a clean error. This is a valid concern but low priority. Could be done later if time allows.


## 08-10/04/2026 : 3h

#### Wrote archiver.py and test_archiver (ADR 003 + 004)

Wrote function signatures, docstrings and TODOs for:
- `get_group_members` : primary + secondary group resolution
- `get_user_home` : home path or None
- `should_exclude` : two-strategy pattern matching
- `archive_file` : single file move with shutil.move
- `archive_user` : walk + move for one user
- `archive_group` : orchestrate everything

Added `ArchiveResult` dataclass to track per-user results (files_moved, files_skipped, errors).

Design decision: `archive_group` returns `list[ArchiveResult]`, cli.py computes exit code (0/1/2) from it. Keeps data and decision separate. ADR 002 defines the exit codes but doesn't prescribe where they're computed.

I started by defining the tests (me+ai assistant) since this is core logic and generating it:
- pytest fixtures to create fake home directory/archive and config
- tests boilerplates

I then implemented the core logic and refined with claude (fixed dry run bug, and iterated about the dirnames[:] slice assignment and such)

Added end to end tests (TestArchiveGroup)

## 10/04/2026 : 4h30

#### Wrote cli.py and test_cli.py (ADR 005) 1h30
- Last module: argparse, logging setup, wiring config + lock + archiver, exit codes
- print_report: TODO, optional JSON output to stdout
- Wrote small tests boilerplate on:
  - args parsing (required, default value)
  - exit codes returns on main
- Filled it with ai tools
- Wrote optional print_report in cli.py to write json outputs


-- next : review, debian packaging and tests

Ran `poetry run ruff check .` for linting and `poetry run mypy archiver/` for typing

#### Debian packaging 3h

Read docs:
- [Pybuild](https://wiki.debian.org/Python/Pybuild)
- [Debian New Maintainers' Guide Ch.4](https://www.debian.org/doc/manuals/maint-guide/dreq.en.html)
- `man dh`, `man dh_install`

Decisions (ADR 007):
- Command name: `archiver` (not `file-archiver`: shorter, matches Python package)
- dh-python with pybuild (standard for PEP 517 Python projects)
- Source format: 3.0 (native): we are upstream author
- Config: shipped to /usr/share/, postinst copies to /etc/ on first install only
- MIT license

Steps done:
1. Renamed all `file-archiver` references to `archiver` (code, config, docs, ADRs)
2. Lowered Python version to ^3.11 (tomllib is stdlib since 3.11, matches mypy target)
3. Added MIT LICENSE
4. Created 7 debian files (source/format, changelog, control, rules, copyright, install, postinst)
5. Updated README with install/usage/test instructions


#### Testing

- Step 1: Create test group and users
```sh
sudo groupadd testarchive
sudo useradd -m -G testarchive alice
sudo useradd -m -G testarchive bob
```

- Step 2: Create some files in their homes
```sh
sudo -u alice bash -c 'mkdir -p ~/documents && echo "alice report" > ~/documents/report.txt && echo "alice notes" > ~/documents/notes.txt'
sudo -u bob bash -c 'mkdir -p ~/projects/src && echo "bob code" > ~/projects/src/main.py'
sudo -u alice bash -c 'mkdir -p ~/.cache/deep && echo "cached" > ~/.cache/deep/file.txt'
sudo -u alice bash -c 'ln -s /etc/passwd ~/link.txt'
ls -la /home/alice/documents/ /home/alice/.cache/deep/ /home/alice/link.txt /home/bob/projects/src/ 2>&1

lrwxrwxrwx 1 alice alice   11 Apr 10 15:30 /home/alice/link.txt -> /etc/passwd

/home/alice/.cache/deep/:
total 12
drwxrwxr-x 2 alice alice 4096 Apr 10 15:30 .
drwxrwxr-x 3 alice alice 4096 Apr 10 15:30 ..
-rw-rw-r-- 1 alice alice    7 Apr 10 15:30 file.txt

/home/alice/documents/:
total 16
drwxrwxr-x 2 alice alice 4096 Apr 10 15:30 .
drwx------ 4 alice alice 4096 Apr 10 15:30 ..
-rw-rw-r-- 1 alice alice   12 Apr 10 15:30 notes.txt
-rw-rw-r-- 1 alice alice   13 Apr 10 15:30 report.txt

/home/bob/projects/src/:
total 12
drwxrwxr-x 2 bob bob 4096 Apr 10 15:30 .
drwxrwxr-x 3 bob bob 4096 Apr 10 15:30 ..
-rw-rw-r-- 1 bob bob    9 Apr 10 15:30 main.py
```

- Step 3: Run archiver (dry-run first)
```sh
sudo /home/user/projects/archiver/.venv/bin/python -m archiver.cli --group testarchive --archive-dir /tmp/test-archive --lock-file /tmp/archiver.lock --dry-run --verbose
2026-04-10 15:37:29,250 INFO  [archiver.archiver] Group 'testarchive' has 2 members: alice, bob
2026-04-10 15:37:29,250 INFO  [archiver.archiver] Archiving user 'alice' from /home/alice
2026-04-10 15:37:29,251 WARNING [archiver.archiver] Skipping symlink: /home/alice/link.txt
2026-04-10 15:37:29,251 INFO  [archiver.archiver] Would move: /home/alice/documents/report.txt -> /tmp/test-archive/alice/documents/report.txt
2026-04-10 15:37:29,251 INFO  [archiver.archiver] Would move: /home/alice/documents/notes.txt -> /tmp/test-archive/alice/documents/notes.txt
2026-04-10 15:37:29,252 INFO  [archiver.archiver] User 'alice': moved=2, skipped=4, errors=0
2026-04-10 15:37:29,252 INFO  [archiver.archiver] Archiving user 'bob' from /home/bob
2026-04-10 15:37:29,252 INFO  [archiver.archiver] Would move: /home/bob/projects/src/main.py -> /tmp/test-archive/bob/projects/src/main.py
2026-04-10 15:37:29,252 INFO  [archiver.archiver] User 'bob': moved=1, skipped=3, errors=0
2026-04-10 15:37:29,252 INFO  [archiver.archiver] Archive complete. Total moved=3, errors=0
2026-04-10 15:37:29,252 INFO  [archiver] Done: 3 moved, 7 skipped, 0 errors
```

- Step 4: Run for real
```sh
sudo /home/user/projects/archiver/.venv/bin/python -m archiver.cli --group testarchive --archive-dir /tmp/test-archive --lock-file /tmp/archiver.lock --verbose
2026-04-10 15:44:16,124 INFO  [archiver.archiver] Group 'testarchive' has 2 members: alice, bob
2026-04-10 15:44:16,125 INFO  [archiver.archiver] Archiving user 'alice' from /home/alice
2026-04-10 15:44:16,127 WARNING [archiver.archiver] Skipping symlink: /home/alice/link.txt
2026-04-10 15:44:16,128 INFO  [archiver.archiver] Moved: /home/alice/documents/report.txt -> /tmp/test-archive/alice/documents/report.txt
2026-04-10 15:44:16,129 INFO  [archiver.archiver] Moved: /home/alice/documents/notes.txt -> /tmp/test-archive/alice/documents/notes.txt
2026-04-10 15:44:16,129 INFO  [archiver.archiver] User 'alice': moved=2, skipped=4, errors=0
2026-04-10 15:44:16,131 INFO  [archiver.archiver] Archiving user 'bob' from /home/bob
2026-04-10 15:44:16,132 INFO  [archiver.archiver] Moved: /home/bob/projects/src/main.py -> /tmp/test-archive/bob/projects/src/main.py
2026-04-10 15:44:16,132 INFO  [archiver.archiver] User 'bob': moved=1, skipped=3, errors=0
2026-04-10 15:44:16,132 INFO  [archiver.archiver] Archive complete. Total moved=3, errors=0
2026-04-10 15:44:16,133 INFO  [archiver] Done: 3 moved, 7 skipped, 0 errors
```

- Step 5: Verify
```sh
ls -R /tmp/test-archive/
/tmp/test-archive/:
alice  bob

/tmp/test-archive/alice:
documents

/tmp/test-archive/alice/documents:
notes.txt  report.txt

/tmp/test-archive/bob:
projects

/tmp/test-archive/bob/projects:
src

/tmp/test-archive/bob/projects/src:
main.py

cat /tmp/test-archive/alice/documents/report.txt
alice report

sudo ls /home/alice/documents/  # should be empty
sudo ls /home/alice/.cache/     # should still be there (excluded)
deep
sudo ls /home/alice/link.txt    # should still be there (symlink skipped)
/home/alice/link.tx
```

- Step 6: Cleanup
```sh
sudo userdel -r alice
sudo userdel -r bob
sudo groupdel testarchive
rm -rf /tmp/test-archive
```

All tests passed: files moved, structure preserved, content preserved, excludes respected, symlinks skipped, source files removed.

Note: needed `--lock-file` CLI arg because default `/var/lock/archiver.lock` wasn't writable. Added the option to cli.py — merge_configs already handled `lock_file` in the path fields loop, so only argparse needed the new argument.
