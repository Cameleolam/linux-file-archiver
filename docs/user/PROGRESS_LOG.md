# General progress log
Logging hours spent and actions done.
Consciously logging anything to keep track of my progress and questions

## 31/03/2026: 6 hours

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

## 01/04/2026: 1 hour

#### Wrote locking.py
[Context manager](https://docs.python.org/3/reference/datamodel.html#with-statement-context-managers)
[fnctl.flock](https://docs.python.org/3/library/fcntl.html#fcntl.flock)
[BlockingIOError](https://docs.python.org/3/library/exceptions.html#BlockingIOError)

Wrote first pass, then corrected with claude.