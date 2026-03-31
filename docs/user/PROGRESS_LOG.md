# General progress log
Logging hours spent and actions done.
Consciously logging anything to keep track of my progress and questions

## 31/03/2026: 5 hours

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
# commit docs and architecture
```

#### Iterated with Claude (chat) about questions on the architecture

Generated :
[Robustness decisions](../adr/002-robustness.md)
[User & Groups handling decisions](../adr/003-user-group-handling.md)
[File operations decisions](../adr/004-file-operations.md)
[CLI Logging config decisions](../adr/005-cli-logging-config.md)
[Testing strategy decisions](../adr/006-testing-strategy.md)