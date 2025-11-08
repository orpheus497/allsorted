"""
Tests for file analyzer module.

Created by orpheus497
"""

import hashlib
from pathlib import Path

import pytest

from allsorted.analyzer import FileAnalyzer
from allsorted.config import Config


class TestFileAnalyzer:
    """Test FileAnalyzer class."""

    def test_init(self, temp_dir: Path) -> None:
        """Test analyzer initialization."""
        config = Config()
        analyzer = FileAnalyzer(config)

        assert analyzer.config == config
        assert analyzer.all_files == []
        assert analyzer.file_hashes == {}

    def test_analyze_empty_directory(self, temp_dir: Path) -> None:
        """Test analyzing an empty directory."""
        config = Config()
        analyzer = FileAnalyzer(config)
        analyzer.analyze_directory(temp_dir)

        assert analyzer.get_total_files() == 0
        assert len(analyzer.get_duplicate_sets()) == 0

    def test_analyze_directory_with_files(self, temp_dir: Path) -> None:
        """Test analyzing directory with files."""
        # Create test files
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "file2.pdf").write_text("document")
        (temp_dir / "file3.jpg").write_bytes(b"image data")

        config = Config()
        analyzer = FileAnalyzer(config)
        analyzer.analyze_directory(temp_dir)

        assert analyzer.get_total_files() == 3

    def test_duplicate_detection(self, temp_dir: Path) -> None:
        """Test duplicate file detection."""
        content = "duplicate content"
        (temp_dir / "file1.txt").write_text(content)
        (temp_dir / "file2.txt").write_text(content)
        (temp_dir / "file3.txt").write_text("different")

        config = Config()
        analyzer = FileAnalyzer(config)
        analyzer.analyze_directory(temp_dir)

        duplicates = analyzer.get_duplicate_sets()
        assert len(duplicates) == 1
        assert duplicates[0].count == 2

    def test_ignore_hidden_files(self, temp_dir: Path) -> None:
        """Test ignoring hidden files."""
        (temp_dir / "normal.txt").write_text("content")
        (temp_dir / ".hidden").write_text("hidden")

        config = Config()
        config.ignore_hidden = True
        analyzer = FileAnalyzer(config)
        analyzer.analyze_directory(temp_dir)

        assert analyzer.get_total_files() == 1
        assert len(analyzer.ignored_files) >= 1

    def test_ignore_patterns(self, temp_dir: Path) -> None:
        """Test file ignoring based on patterns."""
        (temp_dir / "normal.txt").write_text("content")
        git_dir = temp_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config")

        config = Config()
        analyzer = FileAnalyzer(config)
        analyzer.analyze_directory(temp_dir)

        assert analyzer.get_total_files() == 1

    def test_managed_directory_recursion(self, temp_dir: Path) -> None:
        """Test recursive scanning of managed directories."""
        # Create managed directory
        managed = temp_dir / "all_Docs"
        managed.mkdir()
        subdir = managed / "PDFs"
        subdir.mkdir()
        (subdir / "document.pdf").write_text("pdf content")

        # Create non-managed directory
        nonmanaged = temp_dir / "MyFolder"
        nonmanaged.mkdir()
        (nonmanaged / "file.txt").write_text("should not scan")

        config = Config()
        analyzer = FileAnalyzer(config)
        analyzer.analyze_directory(temp_dir)

        # Should find file in managed dir, not in non-managed
        assert analyzer.get_total_files() == 1
        assert len(analyzer.directories) == 1
        assert analyzer.directories[0].name == "MyFolder"

    def test_analyze_single_file(self, temp_dir: Path) -> None:
        """Test analyzing a single file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        config = Config()
        analyzer = FileAnalyzer(config)
        file_info = analyzer.analyze_single_file(test_file)

        assert file_info is not None
        assert file_info.path == test_file
        assert file_info.size_bytes > 0
        assert file_info.hash is not None

    def test_xxhash_algorithm(self, temp_dir: Path) -> None:
        """Test xxHash algorithm support."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content for hashing")

        config = Config()
        config.hash_algorithm = "xxhash"
        analyzer = FileAnalyzer(config)
        file_info = analyzer.analyze_single_file(test_file)

        # Should work even if xxhash not available (fallback to sha256)
        assert file_info is not None
        assert file_info.hash is not None

    def test_sha256_algorithm(self, temp_dir: Path) -> None:
        """Test SHA256 algorithm (default)."""
        test_file = temp_dir / "test.txt"
        content = b"test content for hashing"
        test_file.write_bytes(content)

        config = Config()
        config.hash_algorithm = "sha256"
        analyzer = FileAnalyzer(config)
        file_info = analyzer.analyze_single_file(test_file)

        # Verify hash matches expected
        expected_hash = hashlib.sha256(content).hexdigest()
        assert file_info is not None
        assert file_info.hash == expected_hash

    def test_symlink_handling(self, temp_dir: Path) -> None:
        """Test symlink detection."""
        real_file = temp_dir / "real.txt"
        real_file.write_text("real content")

        symlink = temp_dir / "link.txt"
        try:
            symlink.symlink_to(real_file)
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks not supported on this system")

        config = Config()
        config.follow_symlinks = False
        analyzer = FileAnalyzer(config)
        file_info = analyzer.analyze_single_file(symlink)

        assert file_info is not None
        assert file_info.is_symlink is True

    def test_glob_pattern_matching(self, temp_dir: Path) -> None:
        """Test glob pattern matching for nested paths."""
        # Create nested structure
        nested = temp_dir / "level1" / "level2"
        nested.mkdir(parents=True)
        (nested / "file.txt").write_text("nested file")
        (temp_dir / "root.txt").write_text("root file")

        config = Config()
        # Add pattern that should match nested paths
        config.ignore_patterns.append("**/level2/**")
        analyzer = FileAnalyzer(config)
        analyzer.analyze_directory(temp_dir)

        # Should only find root file, not nested file
        assert analyzer.get_total_files() == 1

    def test_get_unique_files(self, temp_dir: Path) -> None:
        """Test getting only unique files (no duplicates)."""
        (temp_dir / "unique1.txt").write_text("unique content 1")
        (temp_dir / "unique2.txt").write_text("unique content 2")
        (temp_dir / "dup1.txt").write_text("duplicate")
        (temp_dir / "dup2.txt").write_text("duplicate")

        config = Config()
        analyzer = FileAnalyzer(config)
        analyzer.analyze_directory(temp_dir)

        unique_files = analyzer.get_unique_files()
        assert len(unique_files) == 2

    def test_hash_collision_detection(self, temp_dir: Path) -> None:
        """Test that identical content is properly detected as duplicates."""
        content = "identical content" * 1000  # Make it substantial
        (temp_dir / "file1.txt").write_text(content)
        (temp_dir / "file2.doc").write_text(content)
        (temp_dir / "file3.pdf").write_text(content)

        config = Config()
        analyzer = FileAnalyzer(config)
        analyzer.analyze_directory(temp_dir)

        duplicates = analyzer.get_duplicate_sets()
        assert len(duplicates) == 1
        assert duplicates[0].count == 3
