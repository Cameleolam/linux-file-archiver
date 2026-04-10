"""Tests for CLI entry point."""

import pytest

from archiver.archiver import ArchiveResult
from archiver.cli import DEFAULT_CONFIG_PATH, main, parse_args


class TestParseArgs:
    """Test argument parsing."""

    def test_group_required(self):
        """Missing --group should cause SystemExit."""
        with pytest.raises(SystemExit):
            parse_args([])

    def test_group_only(self):
        """--group is sufficient, everything else has defaults."""
        args = parse_args(["--group", "testgroup"])
        assert args.group == "testgroup"
        assert args.config == DEFAULT_CONFIG_PATH
        assert args.dry_run is False
        assert args.verbose is False
        assert args.report is None
        assert args.archive_dir is None

    def test_all_args(self):
        """All arguments parsed correctly."""
        args = parse_args([
            "--group", "testgroup",
            "--archive-dir", "/tmp/archive",
            "--config", "/tmp/config.toml",
            "--dry-run",
            "--report", "json",
            "--verbose",
        ])
        assert args.group == "testgroup"
        assert args.archive_dir == "/tmp/archive"
        assert args.config == "/tmp/config.toml"
        assert args.dry_run is True
        assert args.report == "json"
        assert args.verbose is True

    def test_invalid_report_format(self):
        """Invalid --report value should cause SystemExit."""
        with pytest.raises(SystemExit):
            parse_args(["--group", "test", "--report", "xml"])


class TestMainExitCodes:
    """Test exit code logic in main().

    Mocks archive_group to return known results,
    then checks the exit code.
    """

    def test_exit_0_success(self, monkeypatch, tmp_path):
        """All files moved, no errors -> exit 0."""
        result = ArchiveResult(
            username="alice", home_dir=tmp_path,
            files_moved=5, files_skipped=0, errors=0,
        )
        monkeypatch.setattr(
            "archiver.cli.archive_group", lambda config: [result]
        )
        monkeypatch.setattr(
            "archiver.cli.load_config", lambda path, explicit: {}
        )
        monkeypatch.setattr(
            "archiver.cli.FileLock.__enter__", lambda self: self
        )
        monkeypatch.setattr(
            "archiver.cli.FileLock.__exit__",
            lambda self, *args: None,
        )
        code = main([
            "--group", "testgroup",
            "--config", str(tmp_path / "config.toml"),
        ])
        assert code == 0

    def test_exit_1_no_results(self, monkeypatch, tmp_path):
        """No results (group not found) -> exit 1."""
        monkeypatch.setattr(
            "archiver.cli.archive_group", lambda config: []
        )
        monkeypatch.setattr(
            "archiver.cli.load_config", lambda path, explicit: {}
        )
        monkeypatch.setattr(
            "archiver.cli.FileLock.__enter__", lambda self: self
        )
        monkeypatch.setattr(
            "archiver.cli.FileLock.__exit__",
            lambda self, *args: None,
        )
        code = main([
            "--group", "testgroup",
            "--config", str(tmp_path / "config.toml"),
        ])
        assert code == 1

    def test_exit_2_partial(self, monkeypatch, tmp_path):
        """Some moved, some errors -> exit 2."""
        result = ArchiveResult(
            username="alice", home_dir=tmp_path,
            files_moved=3, files_skipped=0, errors=2,
        )
        monkeypatch.setattr(
            "archiver.cli.archive_group", lambda config: [result]
        )
        monkeypatch.setattr(
            "archiver.cli.load_config", lambda path, explicit: {}
        )
        monkeypatch.setattr(
            "archiver.cli.FileLock.__enter__", lambda self: self
        )
        monkeypatch.setattr(
            "archiver.cli.FileLock.__exit__",
            lambda self, *args: None,
        )
        code = main([
            "--group", "testgroup",
            "--config", str(tmp_path / "config.toml"),
        ])
        assert code == 2
