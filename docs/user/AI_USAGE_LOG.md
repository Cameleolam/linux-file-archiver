# General ai usage log
Logging ai usage in this project
I used Claude as a coding assistant throughout this project.
My rule: use AI for acceleration, not for thinking.
Every line of code in this repo is code I understand and can explain.

## 31/03/2026

### Claude Code
- Shared project details, asked for subjects to explore and read about
- Sketched architecture & flow
- Explored best way to containerize dependencies and dev modules needed
- Iterated over architecture questions raised from reading docs (file locking, debian packaging, etc.)
- Generated ADRs 002-006 after showing ADR 001 as example and iterating over questions

## 01/04/2026

### Claude Code
- Guidance on implementing locking.py: explained fcntl.flock, context managers, BlockingIOError
- Reviewed my code and pointed out bugs (file lifetime, flock signature)
- Generated test boilerplate for test_locking.py, I filled in and corrected
- Ran Codex adversarial review on locking - flagged EACCES/errno concern, determined irrelevant for Linux-only flock(2)

## 06/04/2026

### Claude Code
- Discussed dataclass vs NamedTuple vs dict for Config (asked Codex for comparison)
- Guidance on config.py structure: dataclass fields, load_config, merge_configs
- Wrote merge_configs loop logic (path fields + bool/str fields), I structured the function and wrote load_config
- Generated test boilerplate for test_config.py, wrote first two tests, I filled some in
- Improved docstrings for load_config and merge_configs
- Ran Codex adversarial review on config - flagged missing schema validation, deferred as low priority
- Discussed optparse vs argparse (optparse deprecated since 3.2)
- Discussed `from __future__ import annotations` and Python 3.13 GIL changes

## 08-10/04/2026

### Claude Code
- Wrote together function signatures, docstrings and TODOs for archiver.py
- Discussed ArchiveResult dataclass and where to compute exit codes (archive_group returns data, cli.py decides)
- Generated test fixtures in conftest.py (tmp_home, tmp_archive, sample_config)
- Generated test_archiver.py with tests for: should_exclude, archive_file, get_group_members, get_user_home, archive_user
- Everything was ok, except the monkeypatch target
- Identified critical tests to understand:
  - `test_nested_directory`: fnmatch `*` doesn't match `/`, need prefix matching for directory patterns
  - `test_primary_and_secondary_deduplicated`: grp.gr_mem only has secondary members, need pwd.getpwall() for primary
  - `test_skips_symlinks`: is_symlink() must come before is_file() because symlinks to files return True for both
- Reviewed the archiver.py code

## 10/04/2026

### Claude Code
- Reviewed cli.py code:
  - Reviewed parse_args: pointed out required=True on optional args, action="store_true" for flags, metavar for help text
  - Explained vars(args) and explicit config detection
  - Fixed setup_logging order (stderr handler before file handler so warnings are visible)
- Filled tests boilerplate on test_cli.py
- Fixed linting and typing warning from ruff and mypy
- Explored codebase for debian packaging readiness (Explore agent)
- Planned debian packaging approach (Plan agent)
- Wrote ADR 007 for packaging decisions
- Renamed all file-archiver -> archiver across codebase
- Generated all 7 debian packaging files (control, rules, changelog, copyright, install, postinst, source/format)
- Wrote MIT LICENSE
- Updated README with install/usage/test sections
- Guided integration test with fake users (alice, bob): dry-run then real run, verified all behaviors