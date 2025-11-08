"""
Tests for utility functions.

Created by orpheus497
"""

from pathlib import Path

import pytest

from allsorted.utils import (
    calculate_directory_size,
    ensure_dir,
    format_duration,
    format_size,
    get_available_space,
    get_unique_path,
    is_hidden,
    is_same_filesystem,
    safe_path_resolve,
    sanitize_filename,
    truncate_path,
)


class TestFormatting:
    """Test formatting functions."""

    def test_format_size_bytes(self) -> None:
        """Test formatting bytes."""
        assert "B" in format_size(500)

    def test_format_size_kilobytes(self) -> None:
        """Test formatting kilobytes."""
        result = format_size(2048)
        assert "KB" in result

    def test_format_size_megabytes(self) -> None:
        """Test formatting megabytes."""
        result = format_size(1024 * 1024 * 5)
        assert "MB" in result

    def test_format_size_gigabytes(self) -> None:
        """Test formatting gigabytes."""
        result = format_size(1024 * 1024 * 1024 * 2)
        assert "GB" in result

    def test_format_duration_seconds(self) -> None:
        """Test formatting short duration."""
        result = format_duration(45.3)
        assert "s" in result

    def test_format_duration_minutes(self) -> None:
        """Test formatting minutes."""
        result = format_duration(125)
        assert "m" in result

    def test_format_duration_hours(self) -> None:
        """Test formatting hours."""
        result = format_duration(3665)
        assert "h" in result


class TestPathOperations:
    """Test path operation functions."""

    def test_ensure_dir_creates_directory(self, temp_dir: Path) -> None:
        """Test directory creation."""
        new_dir = temp_dir / "new" / "nested" / "dir"
        ensure_dir(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_dir_existing(self, temp_dir: Path) -> None:
        """Test ensure_dir on existing directory."""
        temp_dir.mkdir(exist_ok=True)
        ensure_dir(temp_dir)  # Should not raise

        assert temp_dir.exists()

    def test_get_unique_path_nonexistent(self, temp_dir: Path) -> None:
        """Test get_unique_path for non-existent file."""
        path = temp_dir / "file.txt"
        result = get_unique_path(path)

        assert result == path

    def test_get_unique_path_existing(self, temp_dir: Path) -> None:
        """Test get_unique_path for existing file."""
        path = temp_dir / "file.txt"
        path.write_text("content")

        result = get_unique_path(path)

        assert result != path
        assert result.parent == path.parent
        assert result.suffix == path.suffix
        assert "_1" in result.stem

    def test_get_unique_path_multiple(self, temp_dir: Path) -> None:
        """Test get_unique_path with multiple existing files."""
        path = temp_dir / "file.txt"
        path.write_text("content")
        (temp_dir / "file_1.txt").write_text("content")
        (temp_dir / "file_2.txt").write_text("content")

        result = get_unique_path(path)

        assert "_3" in result.stem

    def test_truncate_path_short(self) -> None:
        """Test truncating a short path."""
        path = Path("/short/path/file.txt")
        result = truncate_path(path, max_length=100)

        assert str(path) == result

    def test_truncate_path_long(self) -> None:
        """Test truncating a long path."""
        path = Path("/very/long/path/with/many/nested/directories/and/subdirectories/file.txt")
        result = truncate_path(path, max_length=50)

        assert len(result) <= 50
        assert "..." in result

    def test_is_hidden_unix(self, temp_dir: Path) -> None:
        """Test hidden file detection (Unix-style)."""
        hidden_file = temp_dir / ".hidden"
        hidden_file.touch()

        assert is_hidden(hidden_file)

    def test_is_hidden_normal(self, temp_dir: Path) -> None:
        """Test normal file is not hidden."""
        normal_file = temp_dir / "normal.txt"
        normal_file.touch()

        assert not is_hidden(normal_file)


class TestFilesystemOperations:
    """Test filesystem operation functions."""

    def test_calculate_directory_size(self, temp_dir: Path) -> None:
        """Test calculating directory size."""
        (temp_dir / "file1.txt").write_text("a" * 100)
        (temp_dir / "file2.txt").write_text("b" * 200)

        size = calculate_directory_size(temp_dir)

        assert size >= 300

    def test_calculate_directory_size_nested(self, temp_dir: Path) -> None:
        """Test calculating size of nested directories."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (temp_dir / "file1.txt").write_text("a" * 100)
        (subdir / "file2.txt").write_text("b" * 200)

        size = calculate_directory_size(temp_dir)

        assert size >= 300

    def test_get_available_space(self, temp_dir: Path) -> None:
        """Test getting available disk space."""
        space = get_available_space(temp_dir)

        assert space > 0

    def test_is_same_filesystem(self, temp_dir: Path) -> None:
        """Test filesystem comparison."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.touch()
        file2.touch()

        assert is_same_filesystem(file1, file2)


class TestSecurityFunctions:
    """Test security-related functions."""

    def test_sanitize_filename_normal(self) -> None:
        """Test sanitizing normal filename."""
        filename = "normal_file.txt"
        result = sanitize_filename(filename)

        assert result == filename

    def test_sanitize_filename_with_newlines(self) -> None:
        """Test sanitizing filename with newlines."""
        filename = "file\nwith\nnewlines.txt"
        result = sanitize_filename(filename)

        assert "\n" not in result
        assert "_" in result

    def test_sanitize_filename_with_control_chars(self) -> None:
        """Test sanitizing filename with control characters."""
        filename = "file\x00with\x01control.txt"
        result = sanitize_filename(filename)

        assert "\x00" not in result
        assert "\x01" not in result

    def test_safe_path_resolve(self, temp_dir: Path) -> None:
        """Test safe path resolution."""
        file_path = temp_dir / "file.txt"
        file_path.touch()

        result = safe_path_resolve(file_path, temp_dir)

        assert result.is_absolute()
        assert temp_dir in result.parents or result.parent == temp_dir

    def test_safe_path_resolve_escape_attempt(self, temp_dir: Path) -> None:
        """Test safe path resolution blocks escape attempts."""
        # Try to escape the base directory
        with pytest.raises(ValueError):
            safe_path_resolve(Path("../../etc/passwd"), temp_dir)

    def test_safe_path_resolve_relative(self, temp_dir: Path) -> None:
        """Test safe path resolution with relative path."""
        result = safe_path_resolve(Path("subdir/file.txt"), temp_dir)

        assert result.is_absolute()
