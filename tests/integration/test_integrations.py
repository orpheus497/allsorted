"""
Tests for integrated features (magic, metadata, perceptual, watch).

Created by orpheus497
"""

from pathlib import Path

import pytest

from allsorted.analyzer import FileAnalyzer, IMAGEHASH_AVAILABLE
from allsorted.classifier import FileClassifier
from allsorted.config import Config


class TestMagicClassifierIntegration:
    """Test magic classifier integration with FileClassifier."""

    def test_magic_classifier_disabled_by_default(self) -> None:
        """Test that magic classifier is not initialized when disabled."""
        config = Config()
        assert not config.use_magic

        classifier = FileClassifier(config)
        assert classifier._magic_classifier is None

    def test_magic_classifier_enabled(self) -> None:
        """Test that magic classifier is initialized when enabled."""
        config = Config()
        config.use_magic = True

        classifier = FileClassifier(config)
        # Magic classifier should be initialized if python-magic is available
        # If not available, it should be None (graceful degradation)
        # Either way, the classifier should work


class TestMetadataExtractorIntegration:
    """Test metadata extractor integration with FileClassifier."""

    def test_metadata_extractor_disabled_by_default(self) -> None:
        """Test that metadata extractor is not initialized when disabled."""
        config = Config()
        assert not config.use_metadata

        classifier = FileClassifier(config)
        assert classifier._metadata_extractor is None

    def test_metadata_extractor_enabled(self) -> None:
        """Test that metadata extractor is initialized when enabled."""
        config = Config()
        config.use_metadata = True

        classifier = FileClassifier(config)
        # Metadata extractor should be initialized if PIL/mutagen are available


class TestPerceptualDuplicateIntegration:
    """Test perceptual duplicate detection integration."""

    def test_perceptual_dedup_disabled_by_default(self) -> None:
        """Test that perceptual dedup is disabled by default."""
        config = Config()
        assert not config.perceptual_dedup

    @pytest.mark.skipif(not IMAGEHASH_AVAILABLE, reason="imagehash not available")
    def test_perceptual_dedup_enabled(self, temp_dir: Path) -> None:
        """Test perceptual dedup when enabled and imagehash is available."""
        config = Config()
        config.perceptual_dedup = True
        config.perceptual_threshold = 5

        analyzer = FileAnalyzer(config)
        # Create some test files (not real images, so won't produce duplicates)
        (temp_dir / "file1.txt").write_text("content")
        analyzer.analyze_directory(temp_dir)

        # Should not raise errors even when enabled
        duplicates = analyzer.get_duplicate_sets()
        assert isinstance(duplicates, list)

    def test_image_extensions_defined(self) -> None:
        """Test that image extensions for perceptual hashing are defined."""
        from allsorted.analyzer import IMAGE_EXTENSIONS

        assert ".jpg" in IMAGE_EXTENSIONS
        assert ".jpeg" in IMAGE_EXTENSIONS
        assert ".png" in IMAGE_EXTENSIONS


class TestWatcherIntegration:
    """Test watcher integration."""

    def test_watcher_import(self) -> None:
        """Test that watcher module can be imported."""
        from allsorted.watcher import DirectoryWatcher, WATCHDOG_AVAILABLE

        assert DirectoryWatcher is not None
        # WATCHDOG_AVAILABLE should be True since we installed dependencies
        assert WATCHDOG_AVAILABLE is True

    def test_watcher_creation(self, temp_dir: Path) -> None:
        """Test creating a DirectoryWatcher."""
        from allsorted.watcher import DirectoryWatcher

        config = Config()
        watcher = DirectoryWatcher(temp_dir, config)

        assert watcher.root_dir == temp_dir
        assert watcher.config == config
        assert not watcher.is_running()
