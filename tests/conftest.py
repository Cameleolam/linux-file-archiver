"""Shared test fixtures for archiver tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from archiver.config import Config


@pytest.fixture
def tmp_home(tmp_path: Path) -> Path:
    """Create a fake home directory with realistic structure.

    Structure:
        tmp_path/
            alice/
                documents/
                    report.txt
                    notes.txt
                photos/
                    vacation.jpg
                .ssh/
                    id_rsa
                .cache/
                    deep/
                        cached.dat
                .bashrc
                link.txt -> ../external.txt  (symlink)
            external.txt  (target for symlink, outside home)
    """
    alice_home = tmp_path / "alice"
    alice_home.mkdir()

    # Regular files in nested dirs
    (alice_home / "documents").mkdir()
    (alice_home / "documents" / "report.txt").write_text("report content")
    (alice_home / "documents" / "notes.txt").write_text("notes content")
    (alice_home / "photos").mkdir()
    (alice_home / "photos" / "vacation.jpg").write_bytes(b"fake jpg")

    # Dotfiles and dotdirs that should be excluded
    (alice_home / ".ssh").mkdir()
    (alice_home / ".ssh" / "id_rsa").write_text("fake key")
    (alice_home / ".cache" / "deep").mkdir(parents=True)
    (alice_home / ".cache" / "deep" / "cached.dat").write_text("cached")
    (alice_home / ".bashrc").write_text("export PATH=...")

    # Symlink pointing outside home
    external = tmp_path / "external.txt"
    external.write_text("external content")
    (alice_home / "link.txt").symlink_to(external)

    return alice_home


@pytest.fixture
def tmp_archive(tmp_path: Path) -> Path:
    """Create a temporary archive directory."""
    archive = tmp_path / "archive"
    archive.mkdir()
    return archive


@pytest.fixture
def sample_config(tmp_home: Path, tmp_archive: Path) -> Config:
    """Config pointing to temporary directories (no root needed)."""
    return Config(
        group="testgroup",
        archive_dir=tmp_archive,
        log_file=tmp_archive / "test.log",
        lock_file=tmp_archive / "test.lock",
        exclude_patterns=[".ssh/*", ".bashrc", "*.tmp", ".cache/*"],
        dry_run=False,
    )
