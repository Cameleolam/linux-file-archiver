"""Tests for the core archiver logic.

Test strategy:
- Mock system calls (grp, pwd) for group/user resolution
- Use real filesystem (tmp_path) for file operations
"""

import grp
import pwd
from pathlib import Path

import pytest

from archiver.archiver import (
    archive_file,
    archive_group,
    archive_user,
    get_group_members,
    get_user_home,
    should_exclude,
)
from archiver.config import Config

# --- Unit tests: should_exclude (pure function) ---


class TestShouldExclude:
    """Test file exclusion pattern matching."""

    def test_matches_simple_glob(self):
        """*.tmp should match any .tmp file at any depth."""
        assert should_exclude(Path("documents/report.tmp"), ["*.tmp"]) is True

    def test_matches_directory_glob(self):
        """.ssh/* should match files inside .ssh/."""
        assert should_exclude(Path(".ssh/id_rsa"), [".ssh/*"]) is True

    def test_no_match(self):
        """Regular file should not be excluded."""
        assert should_exclude(Path("documents/report.txt"), ["*.tmp"]) is False

    def test_exact_filename_match(self):
        """.bashrc should match exactly."""
        assert should_exclude(Path(".bashrc"), [".bashrc"]) is True

    def test_nested_directory(self):
        """.cache/* should match deeply nested files too."""
        assert should_exclude(
            Path(".cache/deep/nested/file.txt"), [".cache/*"]
        ) is True

    def test_multiple_patterns(self):
        """File matching any one pattern is excluded."""
        assert should_exclude(Path(".ssh/key"), ["*.tmp", ".ssh/*"]) is True

    def test_non_excluded_in_nested_dir(self):
        """File in a non-excluded directory is not excluded."""
        assert should_exclude(Path("docs/notes.txt"), [".cache/*"]) is False

    def test_empty_patterns(self):
        """No patterns means nothing is excluded."""
        assert should_exclude(Path("anything.txt"), []) is False


# --- Unit tests: archive_file (real filesystem) ---


class TestArchiveFile:
    """Test single file archival."""

    def test_moves_file(self, tmp_path):
        """File should be moved from src to dest."""
        src = tmp_path / "source" / "file.txt"
        src.parent.mkdir()
        src.write_text("content")
        dest = tmp_path / "archive" / "file.txt"
        result = archive_file(src, dest)
        assert result is True
        assert not src.exists()
        assert dest.exists()
        assert dest.read_text() == "content"

    def test_creates_parent_directories(self, tmp_path):
        """Dest parent dirs should be created automatically."""
        src = tmp_path / "source" / "file.txt"
        src.parent.mkdir()
        src.write_text("content")
        dest = tmp_path / "archive" / "deep" / "nested" / "file.txt"
        result = archive_file(src, dest)
        assert result is True
        assert dest.exists()

    def test_skips_existing_dest(self, tmp_path):
        """If dest already exists, skip (never overwrite)."""
        src = tmp_path / "source" / "file.txt"
        src.parent.mkdir()
        src.write_text("new version")
        dest = tmp_path / "archive" / "file.txt"
        dest.parent.mkdir()
        dest.write_text("old version")
        result = archive_file(src, dest)
        assert result is False
        assert src.exists()  # source not moved
        assert dest.read_text() == "old version"  # not overwritten

    def test_dry_run_doesnt_move(self, tmp_path):
        """Dry run should log but not move the file."""
        src = tmp_path / "source" / "file.txt"
        src.parent.mkdir()
        src.write_text("content")
        dest = tmp_path / "archive" / "file.txt"
        result = archive_file(src, dest, dry_run=True)
        assert result is True
        assert src.exists()  # source still there
        assert not dest.exists()  # dest not created


# --- Unit tests: get_group_members (mocked) ---


class TestGetGroupMembers:
    """Test group member resolution."""

    def test_secondary_members(self, monkeypatch):
        """Returns secondary group members from gr_mem."""
        fake_group = grp.struct_group(
            ("testgroup", "x", 1000, ["alice", "bob"])
        )
        monkeypatch.setattr("archiver.archiver.grp.getgrnam", lambda name: fake_group)
        monkeypatch.setattr("archiver.archiver.pwd.getpwall", lambda: [])
        result = get_group_members("testgroup")
        assert "alice" in result
        assert "bob" in result

    def test_primary_members(self, monkeypatch):
        """Finds users whose primary GID matches the group."""
        fake_group = grp.struct_group(("testgroup", "x", 1000, []))
        fake_user = pwd.struct_passwd(
            ("charlie", "x", 1001, 1000, "", "/home/charlie", "/bin/bash")
        )
        monkeypatch.setattr("archiver.archiver.grp.getgrnam", lambda name: fake_group)
        monkeypatch.setattr("archiver.archiver.pwd.getpwall", lambda: [fake_user])
        result = get_group_members("testgroup")
        assert "charlie" in result

    def test_primary_and_secondary_deduplicated(self, monkeypatch):
        """Both primary and secondary members returned, no duplicates."""
        # alice is in both gr_mem AND has primary gid=1000
        fake_group = grp.struct_group(
            ("testgroup", "x", 1000, ["alice", "bob"])
        )
        fake_alice = pwd.struct_passwd(
            ("alice", "x", 1000, 1000, "", "/home/alice", "/bin/bash")
        )
        fake_other = pwd.struct_passwd(
            ("other", "x", 1002, 9999, "", "/home/other", "/bin/bash")
        )
        monkeypatch.setattr("archiver.archiver.grp.getgrnam", lambda name: fake_group)
        monkeypatch.setattr("archiver.archiver.pwd.getpwall",
                            lambda: [fake_alice, fake_other])
        result = get_group_members("testgroup")
        assert sorted(result) == ["alice", "bob"]
        assert len(result) == len(set(result))  # no duplicates

    def test_group_not_found(self, monkeypatch):
        """Nonexistent group raises KeyError."""
        monkeypatch.setattr(
            "grp.getgrnam", lambda name: (_ for _ in ()).throw(KeyError(name))
        )
        with pytest.raises(KeyError):
            get_group_members("nonexistent")

    def test_empty_group(self, monkeypatch):
        """Group with no members returns empty list."""
        fake_group = grp.struct_group(("emptygroup", "x", 2000, []))
        monkeypatch.setattr("archiver.archiver.grp.getgrnam", lambda name: fake_group)
        monkeypatch.setattr("archiver.archiver.pwd.getpwall", lambda: [])
        result = get_group_members("emptygroup")
        assert result == []


# --- Unit tests: get_user_home (mocked) ---


class TestGetUserHome:

    def test_user_with_home(self, monkeypatch, tmp_path):
        """Returns home path when user and home exist."""
        home = tmp_path / "alice"
        home.mkdir()
        fake_user = pwd.struct_passwd(
            ("alice", "x", 1000, 1000, "", str(home), "/bin/bash")
        )
        monkeypatch.setattr("archiver.archiver.pwd.getpwnam", lambda name: fake_user)
        result = get_user_home("alice")
        assert result == home

    def test_user_home_missing(self, monkeypatch, tmp_path):
        """Returns None when home directory doesn't exist on disk."""
        fake_user = pwd.struct_passwd(
            ("alice", "x", 1000, 1000, "", "/nonexistent/home", "/bin/bash")
        )
        monkeypatch.setattr("archiver.archiver.pwd.getpwnam", lambda name: fake_user)
        result = get_user_home("alice")
        assert result is None

    def test_user_not_found(self, monkeypatch):
        """Returns None when user doesn't exist."""
        monkeypatch.setattr(
            "pwd.getpwnam",
            lambda name: (_ for _ in ()).throw(KeyError(name)),
        )
        result = get_user_home("ghost")
        assert result is None


# --- Integration tests: archive_user (real filesystem) ---


class TestArchiveUser:
    """Test archiving all files for a single user."""

    def test_archives_regular_files(self, tmp_home, tmp_archive):
        """Regular files moved to archive preserving structure."""
        result = archive_user(
            "alice", tmp_home, tmp_archive, exclude_patterns=[]
        )
        # report.txt should be in archive
        assert (tmp_archive / "alice" / "documents" / "report.txt").exists()
        assert (tmp_archive / "alice" / "photos" / "vacation.jpg").exists()
        # source should be gone
        assert not (tmp_home / "documents" / "report.txt").exists()
        assert result.files_moved > 0

    def test_preserves_content(self, tmp_home, tmp_archive):
        """Archived files have the same content."""
        archive_user("alice", tmp_home, tmp_archive, exclude_patterns=[])
        dest = tmp_archive / "alice" / "documents" / "report.txt"
        assert dest.read_text() == "report content"

    def test_skips_symlinks(self, tmp_home, tmp_archive):
        """Symlinks are skipped, not followed."""
        result = archive_user(
            "alice", tmp_home, tmp_archive, exclude_patterns=[]
        )
        assert not (tmp_archive / "alice" / "link.txt").exists()
        assert result.files_skipped > 0

    def test_skips_excluded_patterns(self, tmp_home, tmp_archive):
        """Files matching exclude patterns are not moved."""
        result = archive_user(
            "alice",
            tmp_home,
            tmp_archive,
            exclude_patterns=[".ssh/*", ".bashrc", ".cache/*"],
        )
        assert result.files_skipped > 0
        # excluded files stay in home
        assert (tmp_home / ".ssh" / "id_rsa").exists()
        assert (tmp_home / ".bashrc").exists()
        assert (tmp_home / ".cache" / "deep" / "cached.dat").exists()
        # non-excluded files are archived
        assert (tmp_archive / "alice" / "documents" / "report.txt").exists()

    def test_skip_existing_in_archive(self, tmp_home, tmp_archive):
        """Already-archived file is not overwritten."""
        dest = tmp_archive / "alice" / "documents" / "report.txt"
        dest.parent.mkdir(parents=True)
        dest.write_text("old version")
        archive_user("alice", tmp_home, tmp_archive, exclude_patterns=[])
        assert dest.read_text() == "old version"

    def test_excluded_directory_pruned(self, tmp_home, tmp_archive):
        """Excluded directories: nested files not archived."""
        archive_user(
            "alice",
            tmp_home,
            tmp_archive,
            exclude_patterns=[".cache/*"],
        )
        assert not (tmp_archive / "alice" / ".cache").exists()

    def test_empty_home(self, tmp_path):
        """Empty home dir returns zero counts."""
        home = tmp_path / "empty_user"
        home.mkdir()
        archive = tmp_path / "archive"
        result = archive_user(
            "empty_user", home, archive, exclude_patterns=[]
        )
        assert result.files_moved == 0
        assert result.errors == 0

    def test_dry_run(self, tmp_home, tmp_archive):
        """Dry run logs but doesn't move files."""
        result = archive_user(
            "alice",
            tmp_home,
            tmp_archive,
            exclude_patterns=[],
            dry_run=True,
        )
        # files still in home
        assert (tmp_home / "documents" / "report.txt").exists()
        # nothing in archive
        assert not (tmp_archive / "alice").exists() or not any(
            (tmp_archive / "alice").rglob("*")
        )
        assert result.files_moved > 0  # counted as "would move"


# --- Integration test: archive_group (mocked grp/pwd, real filesystem) ---


class TestArchiveGroup:
    """End-to-end test for the full archive workflow."""

    def test_full_workflow(self, monkeypatch, tmp_path):
        """Mock group/user, real files, verify archive."""
        # Setup fake home
        home = tmp_path / "home" / "alice"
        (home / "documents").mkdir(parents=True)
        (home / "documents" / "report.txt").write_text("report")
        (home / ".ssh").mkdir()
        (home / ".ssh" / "id_rsa").write_text("key")

        archive = tmp_path / "archive"

        # Mock group resolution
        fake_group = grp.struct_group(
            ("testgroup", "x", 1000, ["alice"])
        )
        monkeypatch.setattr(
            "archiver.archiver.grp.getgrnam", lambda name: fake_group
        )
        monkeypatch.setattr("archiver.archiver.pwd.getpwall", lambda: [])

        # Mock user home lookup
        fake_user = pwd.struct_passwd(
            ("alice", "x", 1000, 1000, "", str(home), "/bin/bash")
        )
        monkeypatch.setattr(
            "archiver.archiver.pwd.getpwnam", lambda name: fake_user
        )

        config = Config(
            group="testgroup",
            archive_dir=archive,
            exclude_patterns=[".ssh/*"],
        )
        results = archive_group(config)

        assert len(results) == 1
        assert results[0].username == "alice"
        assert results[0].files_moved >= 1
        # report.txt archived
        assert (archive / "alice" / "documents" / "report.txt").exists()
        # .ssh excluded
        assert not (archive / "alice" / ".ssh").exists()
        # source moved
        assert not (home / "documents" / "report.txt").exists()
        # excluded file stays
        assert (home / ".ssh" / "id_rsa").exists()

    def test_group_not_found(self, monkeypatch):
        """Nonexistent group returns empty results."""
        monkeypatch.setattr(
            "archiver.archiver.grp.getgrnam",
            lambda name: (_ for _ in ()).throw(KeyError(name)),
        )
        config = Config(
            group="nonexistent",
            archive_dir=Path("/tmp/archive"),
        )
        results = archive_group(config)
        assert results == []

    def test_user_home_missing(self, monkeypatch, tmp_path):
        """User with no home directory gets empty ArchiveResult."""
        fake_group = grp.struct_group(
            ("testgroup", "x", 1000, ["ghost"])
        )
        monkeypatch.setattr(
            "archiver.archiver.grp.getgrnam", lambda name: fake_group
        )
        monkeypatch.setattr("archiver.archiver.pwd.getpwall", lambda: [])

        fake_user = pwd.struct_passwd(
            ("ghost", "x", 1001, 1000, "", "/nonexistent/home", "/bin/bash")
        )
        monkeypatch.setattr(
            "archiver.archiver.pwd.getpwnam", lambda name: fake_user
        )

        config = Config(
            group="testgroup",
            archive_dir=tmp_path / "archive",
        )
        results = archive_group(config)
        assert len(results) == 1
        assert results[0].username == "ghost"
        assert results[0].home_dir is None
        assert results[0].files_moved == 0
