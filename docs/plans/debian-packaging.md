# Debian Packaging Plan

## Context

TASK.md requires: "The program should be installable as a Debian package and should be made available for download." Last piece before project completion.

## Decisions (documented in ADR 007)

- **Command name**: `archiver` (short, matches Python package name)
- **Debian package name**: `archiver`
- **System paths**: all use `archiver` (`/etc/archiver/`, `/var/log/archiver.log`, `/var/lock/archiver.lock`)
- **Config install**: Ship config.example.toml to /usr/share/archiver/, postinst copies to /etc/ on first install only
- **License**: MIT
- **Download**: GitHub release with .deb attached
- **Source format**: 3.0 (native) — we are upstream author
- **Build approach**: dh-python with pybuild (standard for PEP 517 Python projects)

## What was done

1. Renamed all `file-archiver` references to `archiver` (code, config, docs, ADRs, .gitignore)
2. Lowered Python version to ^3.11 (tomllib is stdlib since 3.11)
3. Added MIT LICENSE
4. Created 7 debian files (source/format, changelog, control, rules, copyright, install, postinst)
5. Updated README with install/usage/test instructions
6. Added `--lock-file` CLI arg (discovered during integration test)
7. Added `override_dh_auto_test` in rules (pybuild tried unittest, not pytest)
8. Updated .gitignore for pybuild build artifacts

## Build & test commands

```bash
# Build deps
sudo apt install debhelper dh-python pybuild-plugin-pyproject python3-all python3-poetry-core

# Build
dpkg-buildpackage -us -uc -b

# Install & verify
sudo dpkg -i ../archiver_0.1.0_all.deb
archiver --help
cat /etc/archiver/config.toml
ls -d /var/archive/

# Release
gh release create v0.1.0 ../archiver_0.1.0_all.deb --title "v0.1.0" --notes "Initial release"
```

## Issues encountered

- pybuild runs unittest by default, not pytest — fixed with override_dh_auto_test in rules
- Running without sudo only archives files you have read access to (documented in ADR 003)
