"""
Metadata extraction from various file types.

Extracts EXIF data from images, ID3 tags from audio files, and metadata from PDFs
to enable smart organization by photo date, music artist, document author, etc.

Created by orpheus497

Dependencies:
    - Pillow (HPND License) by Jeffrey A. Clark (Alex Clark)
    - mutagen (GPL-2.0 License) by Joe Wreschnig, Michael Urman
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from PIL import Image
    from PIL.ExifTags import TAGS

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from mutagen import File as MutagenFile
    from mutagen.easyid3 import EasyID3
    from mutagen.flac import FLAC
    from mutagen.mp3 import MP3

    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

from allsorted.logging_config import get_logger

logger = get_logger(__name__)


class MetadataExtractor:
    """Extracts metadata from various file types."""

    def __init__(self) -> None:
        """Initialize metadata extractor."""
        self.pil_available = PIL_AVAILABLE
        self.mutagen_available = MUTAGEN_AVAILABLE

        if not self.pil_available:
            logger.debug("Pillow not available. Image metadata extraction disabled.")
        if not self.mutagen_available:
            logger.debug("Mutagen not available. Audio metadata extraction disabled.")

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract all available metadata from a file.

        Args:
            file_path: Path to file

        Returns:
            Dictionary of metadata (empty if extraction fails)
        """
        extension = file_path.suffix.lower()

        # Try image metadata
        if extension in (".jpg", ".jpeg", ".png", ".tiff", ".webp", ".heic"):
            return self.extract_image_metadata(file_path)

        # Try audio metadata
        if extension in (".mp3", ".flac", ".m4a", ".ogg", ".wav"):
            return self.extract_audio_metadata(file_path)

        # No metadata available
        return {}

    def extract_image_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract EXIF metadata from image files.

        Args:
            file_path: Path to image file

        Returns:
            Dictionary with keys: date_taken, camera_make, camera_model, etc.
        """
        if not self.pil_available:
            return {}

        try:
            with Image.open(file_path) as img:
                exif_data = img.getexif()
                if not exif_data:
                    return {}

                metadata: Dict[str, Any] = {}

                # Extract relevant EXIF tags
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)

                    # Date/time tags
                    if tag_name == "DateTime":
                        try:
                            metadata["date_taken"] = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        except ValueError:
                            pass
                    elif tag_name == "DateTimeOriginal":
                        try:
                            metadata["date_original"] = datetime.strptime(
                                value, "%Y:%m:%d %H:%M:%S"
                            )
                        except ValueError:
                            pass

                    # Camera info
                    elif tag_name == "Make":
                        metadata["camera_make"] = str(value).strip()
                    elif tag_name == "Model":
                        metadata["camera_model"] = str(value).strip()

                    # Technical details
                    elif tag_name == "ImageWidth":
                        metadata["width"] = int(value)
                    elif tag_name == "ImageLength":
                        metadata["height"] = int(value)
                    elif tag_name == "Orientation":
                        metadata["orientation"] = int(value)

                logger.debug(f"Extracted image metadata from {file_path.name}: {metadata}")
                return metadata

        except Exception as e:
            logger.debug(f"Failed to extract image metadata from {file_path}: {e}")
            return {}

    def extract_audio_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract ID3/metadata from audio files.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with keys: artist, album, title, genre, year, etc.
        """
        if not self.mutagen_available:
            return {}

        try:
            audio = MutagenFile(file_path, easy=True)
            if audio is None:
                return {}

            metadata: Dict[str, Any] = {}

            # Extract common tags
            tag_mapping = {
                "artist": "artist",
                "album": "album",
                "title": "title",
                "genre": "genre",
                "date": "year",
                "albumartist": "album_artist",
                "composer": "composer",
            }

            for mutagen_tag, our_tag in tag_mapping.items():
                if mutagen_tag in audio:
                    value = audio[mutagen_tag]
                    if isinstance(value, list) and value:
                        metadata[our_tag] = value[0]
                    elif value:
                        metadata[our_tag] = str(value)

            # Get audio properties
            if audio.info:
                metadata["length_seconds"] = int(audio.info.length)
                if hasattr(audio.info, "bitrate"):
                    metadata["bitrate"] = int(audio.info.bitrate)
                if hasattr(audio.info, "sample_rate"):
                    metadata["sample_rate"] = int(audio.info.sample_rate)

            logger.debug(f"Extracted audio metadata from {file_path.name}: {metadata}")
            return metadata

        except Exception as e:
            logger.debug(f"Failed to extract audio metadata from {file_path}: {e}")
            return {}

    def get_organization_key(self, metadata: Dict[str, Any], strategy: str) -> Optional[str]:
        """
        Get an organization key from metadata based on strategy.

        Args:
            metadata: Extracted metadata dictionary
            strategy: Organization strategy (exif-date, id3-artist, etc.)

        Returns:
            String key for organizing, or None if not available
        """
        if strategy == "exif-date":
            # Use photo date for organization
            if "date_original" in metadata:
                dt = metadata["date_original"]
                return f"{dt.year}/{dt.month:02d}-{dt.day:02d}"
            elif "date_taken" in metadata:
                dt = metadata["date_taken"]
                return f"{dt.year}/{dt.month:02d}-{dt.day:02d}"

        elif strategy == "id3-artist":
            # Use music artist for organization
            if "artist" in metadata:
                return str(metadata["artist"])
            elif "album_artist" in metadata:
                return str(metadata["album_artist"])

        elif strategy == "id3-album":
            # Use album for organization
            if "album" in metadata:
                return str(metadata["album"])

        elif strategy == "id3-genre":
            # Use genre for organization
            if "genre" in metadata:
                return str(metadata["genre"])

        elif strategy == "camera-make":
            # Use camera make for organization
            if "camera_make" in metadata:
                return str(metadata["camera_make"])

        return None
