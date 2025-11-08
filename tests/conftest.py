"""
Pytest configuration and fixtures for allsorted tests.

Created by orpheus497
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from allsorted.config import Config


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config() -> Config:
    """Create a test configuration with default settings."""
    return Config()


@pytest.fixture
def sample_files(temp_dir: Path) -> Path:
    """Create sample files for testing."""
    # Create various file types
    (temp_dir / "document.pdf").write_text("PDF content")
    (temp_dir / "image.jpg").write_bytes(b"\xff\xd8\xff")  # JPEG header
    (temp_dir / "audio.mp3").write_bytes(b"ID3")  # MP3 ID3 tag
    (temp_dir / "video.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42")  # MP4 header
    (temp_dir / "code.py").write_text("print('hello')")
    (temp_dir / "archive.zip").write_bytes(b"PK\x03\x04")  # ZIP header
    (temp_dir / "text.txt").write_text("Sample text")

    # Create a subdirectory with files
    subdir = temp_dir / "subfolder"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("Nested file")

    return temp_dir


@pytest.fixture
def duplicate_files(temp_dir: Path) -> Path:
    """Create duplicate files for testing."""
    content = "Duplicate content"

    (temp_dir / "file1.txt").write_text(content)
    (temp_dir / "file2.txt").write_text(content)
    (temp_dir / "file3.txt").write_text(content)
    (temp_dir / "unique.txt").write_text("Unique content")

    return temp_dir
