"""Tests for configuration loading and merging."""

import tomllib
from pathlib import Path

import pytest

from archiver.config import (
    DEFAULT_ARCHIVE_FOLDER_LOCATION,
    DEFAULT_EXCLUDE_PATTERNS,
    DEFAULT_LOCK_FILE_PATH_LOCATION,
    DEFAULT_LOG_FILE_LOCATION,
    Config,
    load_config,
    merge_configs,
)


class TestConfig:
    """Tests for Config dataclass."""

    def test_config_defaults(self):
        """Config with only group uses all defaults."""
        cfg = Config(group="testgroup")
        assert cfg.group == "testgroup"
        assert cfg.archive_dir == Path(DEFAULT_ARCHIVE_FOLDER_LOCATION)
        assert cfg.lock_file == Path(DEFAULT_LOCK_FILE_PATH_LOCATION)
        assert cfg.log_file == Path(DEFAULT_LOG_FILE_LOCATION)
        assert cfg.exclude_patterns == DEFAULT_EXCLUDE_PATTERNS
        assert cfg.dry_run is False
        assert cfg.verbose is False
        assert cfg.report_format is None

    def test_config_custom_values(self, tmp_path):
        """Config accepts custom values overriding defaults."""
        cfg = Config(
            group="testgroup",
            archive_dir=tmp_path / "archive",
            dry_run=True,
            verbose=True,
        )
        assert cfg.archive_dir == tmp_path / "archive"
        assert cfg.dry_run is True
        assert cfg.verbose is True
        # non-overridden fields keep defaults
        assert cfg.lock_file == Path(DEFAULT_LOCK_FILE_PATH_LOCATION)
        assert cfg.log_file == Path(DEFAULT_LOG_FILE_LOCATION)


class TestLoadConfig:
    """Tests for TOML config loading."""

    def test_load_valid_toml(self, tmp_path):
        """Loads a valid TOML file and returns a dict."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('archive_dir = "/tmp/archive"\n')
        config = load_config(config_file, explicit=False)
        assert isinstance(config, dict)
        assert config

    def test_load_missing_file_not_explicit(self, tmp_path):
        """Missing file with explicit=False returns empty dict."""
        config_file = tmp_path / "nonexistent.toml"
        result = load_config(config_file, explicit=False)
        assert result == {}

    def test_load_missing_file_explicit(self, tmp_path):
        """Missing file with explicit=True raises FileNotFoundError."""
        config_file = tmp_path / "nonexistent.toml"
        with pytest.raises(FileNotFoundError):
            load_config(config_file, explicit=True)

    def test_load_invalid_toml(self, tmp_path):
        """Invalid TOML raises TOMLDecodeError."""

        config_file = tmp_path / "bad.toml"
        config_file.write_text("not valid [[[toml")
        with pytest.raises(tomllib.TOMLDecodeError):
            load_config(config_file, explicit=False)

    def test_load_exclude_patterns(self, tmp_path):
        """TOML with [exclude] section parses correctly."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[exclude]\npatterns = [".ssh/*", "*.tmp"]\n'
        )
        result = load_config(config_file, explicit=False)
        assert result["exclude"]["patterns"] == [".ssh/*", "*.tmp"]


class TestMergeConfigs:
    """Tests for config merging and precedence."""

    def test_merge_group_required(self):
        """Missing group raises ValueError."""
        with pytest.raises(ValueError):
            merge_configs({}, {})

    def test_merge_defaults_only(self):
        """Empty file_config + only group in cli_args uses defaults."""
        cfg = merge_configs({}, {"group": "test"})
        assert cfg.group == "test"
        assert cfg.archive_dir == Path(DEFAULT_ARCHIVE_FOLDER_LOCATION)
        assert cfg.lock_file == Path(DEFAULT_LOCK_FILE_PATH_LOCATION)
        assert cfg.log_file == Path(DEFAULT_LOG_FILE_LOCATION)
        assert cfg.exclude_patterns == DEFAULT_EXCLUDE_PATTERNS

    def test_merge_file_overrides_defaults(self):
        """file_config values override dataclass defaults."""
        cfg = merge_configs(
            {"archive_dir": "/custom/archive"},
            {"group": "test"},
        )
        assert cfg.archive_dir == Path("/custom/archive")

    def test_merge_cli_overrides_file(self):
        """cli_args take precedence over file_config."""
        cfg = merge_configs(
            {"archive_dir": "/from/file"},
            {"group": "test", "archive_dir": "/from/cli"},
        )
        assert cfg.archive_dir == Path("/from/cli")

    def test_merge_cli_none_skipped(self):
        """None values in cli_args don't override file_config."""
        cfg = merge_configs(
            {"archive_dir": "/from/file"},
            {"group": "test", "archive_dir": None},
        )
        assert cfg.archive_dir == Path("/from/file")

    def test_merge_paths_coerced(self):
        """String paths from TOML/CLI are converted to Path objects."""
        cfg = merge_configs({}, {"group": "test", "archive_dir": "/tmp/test"})
        assert isinstance(cfg.archive_dir, Path)
        assert cfg.archive_dir == Path("/tmp/test")

    def test_merge_exclude_from_toml(self):
        """Exclude patterns extracted from nested TOML structure."""
        cfg = merge_configs(
            {"exclude": {"patterns": [".ssh/*"]}},
            {"group": "test"},
        )
        assert cfg.exclude_patterns == [".ssh/*"]
