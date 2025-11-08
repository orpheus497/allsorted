"""
Tests for configuration management.

Created by orpheus497
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from allsorted.config import (
    Config,
    load_config,
    save_config,
    get_default_config_path,
    DEFAULT_CLASSIFICATION_RULES,
)
from allsorted.models import ConflictResolution, OrganizationStrategy


class TestConfig:
    """Test Config dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = Config()

        assert config.strategy == OrganizationStrategy.BY_EXTENSION
        assert config.conflict_resolution == ConflictResolution.RENAME
        assert config.detect_duplicates is True
        assert config.isolate_duplicates is True
        assert config.follow_symlinks is False
        assert config.ignore_hidden is True
        assert config.hash_algorithm == "sha256"
        assert config.hash_block_size == 65536
        assert config.directory_prefix == "all_"
        assert config.duplicates_folder == "Duplicates"
        assert config.folders_folder == "Folders"

    def test_ignore_patterns_include_nested(self) -> None:
        """Test that ignore patterns properly match nested paths."""
        config = Config()

        # Should include glob patterns for nested matching
        assert any("**/" in pattern for pattern in config.ignore_patterns)
        assert "**/.devAI/**" in config.ignore_patterns
        assert "**/.git/**" in config.ignore_patterns
        assert "**/node_modules/**" in config.ignore_patterns

    def test_modern_file_extensions(self) -> None:
        """Test that modern file extensions are included."""
        config = Config()

        # Check modern image formats
        pics_extensions = []
        for exts in config.classification_rules["Pics"].values():
            pics_extensions.extend(exts)
        assert ".avif" in pics_extensions
        assert ".jxl" in pics_extensions

        # Check modern audio formats
        audio_extensions = []
        for exts in config.classification_rules["Audio"].values():
            audio_extensions.extend(exts)
        assert ".opus" in audio_extensions

        # Check modern web formats
        code_extensions = []
        for exts in config.classification_rules["Code"].values():
            code_extensions.extend(exts)
        assert ".mjs" in code_extensions
        assert ".wasm" in code_extensions

    def test_get_category_for_extension(self) -> None:
        """Test extension to category mapping."""
        config = Config()

        # Test various extensions
        assert config.get_category_for_extension(".pdf") == ("Docs", "PDFs")
        assert config.get_category_for_extension(".jpg") == ("Pics", "Photos")
        assert config.get_category_for_extension(".mp3") == ("Audio", "Music")
        assert config.get_category_for_extension(".mp4") == ("Vids", "Movies")
        assert config.get_category_for_extension(".py") == ("Code", "Python")
        assert config.get_category_for_extension(".zip") == ("Archives", "Compressed")

        # Test extension without dot
        assert config.get_category_for_extension("pdf") == ("Docs", "PDFs")

        # Test unknown extension
        assert config.get_category_for_extension(".unknown") == ("Misc", "Unsorted")

    def test_add_classification_rule(self) -> None:
        """Test adding custom classification rules."""
        config = Config()

        config.add_classification_rule("Code", "Rust", [".rs", ".toml"])

        category, subcategory = config.get_category_for_extension(".rs")
        assert category == "Code"
        assert subcategory == "Rust"

    def test_is_managed_directory(self) -> None:
        """Test managed directory detection."""
        config = Config()

        assert config.is_managed_directory(Path("all_Docs"))
        assert config.is_managed_directory(Path("all_Pics"))
        assert not config.is_managed_directory(Path("MyFolder"))
        assert not config.is_managed_directory(Path("Documents"))

    def test_get_managed_name(self) -> None:
        """Test managed directory name generation."""
        config = Config()

        assert config.get_managed_name("Docs") == "all_Docs"
        assert config.get_managed_name("Duplicates") == "all_Duplicates"

    def test_to_dict(self) -> None:
        """Test configuration serialization to dictionary."""
        config = Config()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["strategy"] == "by-extension"
        assert config_dict["conflict_resolution"] == "rename"
        assert config_dict["detect_duplicates"] is True
        assert config_dict["hash_algorithm"] == "sha256"

    def test_from_dict(self) -> None:
        """Test configuration deserialization from dictionary."""
        data = {
            "strategy": "by-date",
            "conflict_resolution": "skip",
            "detect_duplicates": False,
            "hash_algorithm": "xxhash",
            "use_metadata": True,
        }

        config = Config.from_dict(data)

        assert config.strategy == OrganizationStrategy.BY_DATE
        assert config.conflict_resolution == ConflictResolution.SKIP
        assert config.detect_duplicates is False
        assert config.hash_algorithm == "xxhash"
        assert config.use_metadata is True

    def test_new_configuration_options(self) -> None:
        """Test new configuration options are available."""
        config = Config()

        # Performance options
        assert hasattr(config, "hash_algorithm")
        assert hasattr(config, "max_workers")
        assert hasattr(config, "use_async")

        # Metadata options
        assert hasattr(config, "use_metadata")
        assert hasattr(config, "metadata_strategy")
        assert hasattr(config, "perceptual_dedup")
        assert hasattr(config, "perceptual_threshold")

        # Magic classification
        assert hasattr(config, "use_magic")

        # Watch mode
        assert hasattr(config, "watch_interval")
        assert hasattr(config, "watch_recursive")

        # Safety
        assert hasattr(config, "verify_integrity")


class TestConfigFileOperations:
    """Test configuration file loading and saving."""

    def test_save_and_load_config(self, temp_dir: Path) -> None:
        """Test saving and loading configuration from file."""
        config_path = temp_dir / "config.yaml"

        # Create and save config
        original_config = Config()
        original_config.detect_duplicates = False
        original_config.hash_algorithm = "xxhash"
        save_config(original_config, config_path)

        # Load and verify
        loaded_config = load_config(config_path)
        assert loaded_config.detect_duplicates is False
        assert loaded_config.hash_algorithm == "xxhash"

    def test_load_nonexistent_config(self) -> None:
        """Test loading config when file doesn't exist returns defaults."""
        config = load_config(Path("/nonexistent/config.yaml"))

        assert config.strategy == OrganizationStrategy.BY_EXTENSION
        assert config.detect_duplicates is True

    def test_load_invalid_yaml(self, temp_dir: Path) -> None:
        """Test loading invalid YAML returns defaults with warning."""
        config_path = temp_dir / "invalid.yaml"
        config_path.write_text("invalid: yaml: content: :")

        config = load_config(config_path)

        # Should fall back to defaults
        assert config.strategy == OrganizationStrategy.BY_EXTENSION

    def test_get_default_config_path(self) -> None:
        """Test default config path generation."""
        config_path = get_default_config_path()

        assert config_path.name == "config.yaml"
        assert "allsorted" in str(config_path)
        assert config_path.parent.exists()  # Should create directory
