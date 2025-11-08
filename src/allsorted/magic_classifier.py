"""
Content-based file classification using magic numbers (file signatures).

This module provides more accurate classification than extension-based methods
by reading the actual file content to determine the true file type.

Created by orpheus497

Dependencies:
    - python-magic (MIT License) by Adam Hupp
"""

from pathlib import Path
from typing import Optional, Tuple

try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

from allsorted.logging_config import get_logger

logger = get_logger(__name__)


class MagicClassifier:
    """Classifies files by analyzing file content using magic numbers."""

    def __init__(self) -> None:
        """Initialize magic classifier."""
        if not MAGIC_AVAILABLE:
            logger.warning(
                "python-magic not available. Magic classification disabled. "
                "Install with: pip install python-magic"
            )
            self.magic = None
        else:
            try:
                self.magic = magic.Magic(mime=True)
                logger.debug("Magic classifier initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize magic classifier: {e}")
                self.magic = None

    def is_available(self) -> bool:
        """Check if magic classification is available."""
        return self.magic is not None

    def get_mime_type(self, file_path: Path) -> Optional[str]:
        """
        Get MIME type of a file by reading its content.

        Args:
            file_path: Path to file

        Returns:
            MIME type string (e.g., "image/jpeg") or None if detection fails
        """
        if not self.is_available():
            return None

        try:
            mime_type = self.magic.from_file(str(file_path))
            logger.debug(f"Detected MIME type for {file_path.name}: {mime_type}")
            return mime_type
        except Exception as e:
            logger.debug(f"Failed to detect MIME type for {file_path}: {e}")
            return None

    def classify_by_mime(self, mime_type: str) -> Tuple[str, str]:
        """
        Classify file into category/subcategory based on MIME type.

        Args:
            mime_type: MIME type string (e.g., "image/jpeg")

        Returns:
            Tuple of (category, subcategory)
        """
        # Split MIME type into major/minor
        parts = mime_type.lower().split("/")
        if len(parts) != 2:
            return ("Misc", "Unsorted")

        major, minor = parts

        # Image files
        if major == "image":
            if minor in ("jpeg", "jpg", "png", "gif", "bmp", "tiff", "webp"):
                return ("Pics", "Photos")
            elif minor in ("svg+xml", "x-eps"):
                return ("Pics", "Vector")
            elif minor in ("x-canon-cr2", "x-nikon-nef", "x-adobe-dng"):
                return ("Pics", "Raw")
            elif minor == "x-icon":
                return ("Pics", "Icons")
            else:
                return ("Pics", "Photos")

        # Audio files
        elif major == "audio":
            if minor in ("mpeg", "mp3", "flac", "ogg", "wav", "x-wav") or minor in ("x-m4a", "mp4", "aac"):
                return ("Audio", "Music")
            elif minor == "x-m4b":
                return ("Audio", "Podcasts")
            else:
                return ("Audio", "Music")

        # Video files
        elif major == "video":
            if minor in ("mp4", "x-matroska", "x-msvideo", "quicktime", "webm"):
                return ("Vids", "Movies")
            elif minor in ("3gpp", "x-m4v"):
                return ("Vids", "Clips")
            else:
                return ("Vids", "Movies")

        # Documents
        elif major == "application":
            if minor == "pdf":
                return ("Docs", "PDFs")
            elif minor in ("msword", "vnd.openxmlformats-officedocument.wordprocessingml.document"):
                return ("Docs", "Word")
            elif minor in (
                "vnd.ms-excel",
                "vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "vnd.oasis.opendocument.spreadsheet",
            ):
                return ("Docs", "Sheets")
            elif minor in (
                "vnd.ms-powerpoint",
                "vnd.openxmlformats-officedocument.presentationml.presentation",
            ):
                return ("Docs", "Presentations")
            elif minor == "epub+zip":
                return ("Docs", "Ebooks")
            elif minor in ("zip", "x-rar", "x-7z-compressed", "gzip", "x-bzip2", "x-xz"):
                return ("Archives", "Compressed")
            elif minor in ("x-iso9660-image", "x-apple-diskimage"):
                return ("Archives", "Disk")
            elif minor in ("x-msdownload", "x-dosexec", "x-msi"):
                return ("Programs", "Windows")
            elif minor in ("x-debian-package", "x-rpm") or minor in ("x-executable", "x-sharedlib"):
                return ("Programs", "Linux")
            elif minor == "x-sqlite3":
                return ("Apps", "Database")
            elif minor in ("json", "xml", "yaml"):
                return ("Web", "Data")
            else:
                return ("Misc", "Unsorted")

        # Text files
        elif major == "text":
            if minor in ("html", "xml"):
                return ("Web", "Documents")
            elif minor in ("x-python", "x-script.python"):
                return ("Code", "Python")
            elif minor in ("x-shellscript", "x-sh"):
                return ("Code", "Shell")
            elif minor in ("x-c", "x-c++"):
                return ("Code", "C")
            elif minor in ("x-java-source", "x-java"):
                return ("Code", "Java")
            elif minor in ("plain", "x-log", "markdown"):
                return ("Docs", "Text")
            else:
                return ("Docs", "Text")

        # Fallback
        return ("Misc", "Unsorted")

    def classify_file(self, file_path: Path) -> Optional[Tuple[str, str]]:
        """
        Classify a file using magic number detection.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (category, subcategory) or None if detection fails
        """
        mime_type = self.get_mime_type(file_path)
        if mime_type:
            return self.classify_by_mime(mime_type)
        return None
