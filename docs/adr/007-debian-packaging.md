# 007 - Debian Packaging

## Context
The task requires the program to be "installable as a Debian package and made available
for download." The tool is pure Python (no compiled extensions), uses only stdlib at
runtime, and has a single CLI entry point.

## Questions & Answers

### Q: Command name — `archiver` or `file-archiver`?
**A: `archiver`.** Shorter, matches the Python package name. All system paths
(`/etc/archiver/`, `/var/log/archiver.log`) follow the same name for consistency.
Trade-off: `archiver` is generic and could clash with other tools. Acceptable
for this project scope.

### Q: Packaging approach — dh-python/pybuild, setuptools, or manual?
**A: dh-python with pybuild.** Standard Debian way for PEP 517 Python projects.
Pybuild understands `pyproject.toml` with poetry-core backend natively.
`debian/rules` stays minimal (~6 lines). Alternative: manual `pip install` in
rules — more work, less standard, teaches less about Debian packaging.

### Q: Source format — native or quilt?
**A: `3.0 (native)`.** We are the upstream author. The `debian/` directory lives
in the same repo. No need for separate upstream tarball + Debian diff.
With `quilt`, we'd need to maintain a separate orig tarball, which adds
complexity for no benefit when upstream = maintainer.

### Q: Config file installation — conffile or postinst copy?
**A: postinst copy.** Ship `config.example.toml` to `/usr/share/archiver/`.
`postinst` copies it to `/etc/archiver/config.toml` on first install only
(if the file doesn't already exist). This avoids dpkg conffile prompts on
upgrades when the user has customized their config. The example is always
available at `/usr/share/archiver/` for reference.

Alternative: install directly to `/etc/archiver/config.toml` and let dpkg
treat it as a conffile. This would prompt the user on every upgrade if they
modified it. Unnecessary friction for a config that's meant to be customized.

### Q: License?
**A: MIT.** Standard for take-home projects. Permissive, no complications.

### Q: "Available for download" — how?
**A: GitHub release.** Build the `.deb` locally, attach it to a GitHub release
with `gh release create`. Simple, meets the requirement. Alternative: CI
pipeline that builds on tag push — more impressive but out of scope.

## Decision

### Naming
- Debian package name: `archiver`
- CLI command: `archiver`
- Config path: `/etc/archiver/config.toml`
- Log file: `/var/log/archiver.log`
- Lock file: `/var/lock/archiver.lock`
- Archive dir: `/var/archive/`

### Build System
- `debian/rules` using `dh` with `--buildsystem=pybuild`
- Build-Depends: debhelper-compat (= 13), dh-python, pybuild-plugin-pyproject,
  python3-all, python3-poetry-core
- Runtime: python3 (>= 3.13) only

### Post-install
- Create `/etc/archiver/` and copy default config on first install
- Create `/var/archive/` directory
- Create `/var/log/archiver.log` with 640 permissions

### Distribution
- GitHub release with `.deb` attached
- Build command: `dpkg-buildpackage -us -uc -b`
