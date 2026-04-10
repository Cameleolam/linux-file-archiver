# 005 - CLI, Logging & Configuration

## Context
The program needs a clean CLI interface, structured logging, and a flexible
configuration system. These are the user-facing aspects of the tool.

## Questions & Answers

### Q: Dataclass vs NamedTuple vs dict for Config?
**A: Dataclass.** Type hints, default values, easy to extend. NamedTuple has typing
but is immutable (awkward during construction when merging CLI + file + defaults).
Dict has no type safety and typo-prone keys. Dataclass is the lightest typed option
that supports mutable construction and read-only usage.

### Q: Missing config file - error or silent?
**A: Depends on who asked for it.**
- User passes `--config /bad/path` explicitly → ERROR, exit 1
- No `--config` flag and default `/etc/archiver/config.toml` doesn't exist → use defaults, log INFO

Config is optional. CLI args are always sufficient. But if you explicitly point to
a config file that doesn't exist, that's a user error.

### Q: Invalid TOML - let error propagate?
**A: Catch and wrap.** `tomllib.TOMLDecodeError` gives a raw parse error. Wrap it
with the filename for a friendlier message:
`"Failed to parse config: /etc/archiver/config.toml: {original error}"`
Checked at startup before any archival begins.

### Q: Nested [exclude] section - how to handle?
**A: Navigate the dict.** TOML parses to nested dicts. Just reach in:
```python
data = tomllib.load(f)
patterns = data.get("exclude", {}).get("patterns", [])
```
No flattening needed.

### Q: Type coercion (str to Path) - where?
**A: In merge_config, before anything runs.** Single place for type coercion.
`merge_config` returns a fully typed `Config` with `Path` objects, not strings.
Everything downstream gets clean types. Dry-run and normal run both need the
same typed config.

### Q: Logs to stdout or stderr?
**A: stderr for logs, stdout for --report only.**
```bash
# Clean JSON
archiver --group foo --report json 2>/dev/null
# Logs only
archiver --group foo
# Both
archiver --group foo --report json
```
Standard Unix convention. Machine-readable output on stdout, human-readable
logs on stderr. Enables piping and redirection.

### Q: Log file directory doesn't exist or not writable?
**A: Checked before running. Fall back gracefully.** If `/var/log/` isn't writable
(non-root run), fall back to stderr-only and log WARNING. Don't crash because
the log file can't be created. The archival itself is more important than
the log file destination.

### Q: Return int from main() vs sys.exit()?
**A: Return int.** Testability. `assert main(["--group", "test"]) == 0` is clean.
`sys.exit()` in tests requires catching SystemExit. Lock release and cleanup
happen in context managers, not in exit logic.

Only place for sys.exit:
```python
if __name__ == "__main__":
    sys.exit(main())
```

### Q: parse_args accepts argv parameter?
**A: Yes.** For testing. `parse_args(["--group", "testgroup"])` without
monkeypatching `sys.argv`. Default `None` falls through to `sys.argv` in
production. Standard pattern.

## Decision

### Config Precedence
```
Defaults (in Config dataclass)
  ↓ overridden by
Config file (/etc/archiver/config.toml)
  ↓ overridden by
CLI arguments (--archive-dir, --verbose, etc.)
```

### Config Validation at Startup
Before any archival:
1. Parse CLI args
2. Load config file (if exists or if explicitly requested)
3. Validate: group exists, archive dir is writable (or creatable)
4. If validation fails → clear error message, exit 1

### CLI Interface
```
archiver --group GROUP              (required)
              --archive-dir DIR          (override archive location)
              --config PATH              (config file path)
              --dry-run                  (preview without moving)
              --report json              (machine-readable output to stdout)
              --verbose                  (DEBUG level logging)
```

### Logging
- stderr: human-readable logs (INFO/WARNING/ERROR)
- stdout: reserved for `--report json` output only
- File: configured path, fallback to stderr-only if not writable
- Format: `%(asctime)s %(levelname)-5s [archiver] %(message)s`
- Level: INFO default, DEBUG with --verbose