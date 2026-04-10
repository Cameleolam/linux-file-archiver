# File Archiving Script for Linux Systems
>Small project done for an interview take home task

## Important documentation

[Full task description here](TASK.md)
<br/>
[Progress log here](./docs/user/PROGRESS_LOG.md)
<br/>
[AI Usage log here](./docs/user/AI_USAGE_LOG.md)

## Overview

A CLI tool that archives files owned by members of a specified Linux group. Moves files from user home directories to a configurable archive folder, preserving directory structure. Uses advisory file locking for concurrent run safety.

## Install

### From .deb package

```bash
sudo dpkg -i archiver_0.1.0_all.deb
```

### Build from source

```bash
# Install build dependencies
sudo apt install debhelper dh-python pybuild-plugin-pyproject python3-all python3-poetry-core

# Build
dpkg-buildpackage -us -uc -b

# Install
sudo dpkg -i ../archiver_0.1.0_all.deb
```

### Verify installation

```bash
archiver --help
cat /etc/archiver/config.toml
ls -d /var/archive/
```

## Usage

```bash
archiver --group <groupname>
archiver --group <groupname> --dry-run
archiver --group <groupname> --report json
archiver --group <groupname> --verbose
```

Configuration: `/etc/archiver/config.toml` (see `config.example.toml` for reference).

## Tests

```bash
poetry install
poetry run pytest
poetry run ruff check .
poetry run mypy archiver/
```