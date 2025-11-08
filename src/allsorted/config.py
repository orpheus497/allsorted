"""
Configuration management for allsorted.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from allsorted.models import ConflictResolution, OrganizationStrategy


# Default classification rules based on file extensions
DEFAULT_CLASSIFICATION_RULES: Dict[str, Dict[str, List[str]]] = {
    "Docs": {
        "Word": [".doc", ".docx", ".odt"],
        "PDFs": [".pdf"],
        "Text": [".txt", ".rtf", ".md", ".log"],
        "Sheets": [".xls", ".xlsx", ".csv", ".ods"],
        "Presentations": [".ppt", ".pptx", ".odp"],
        "Ebooks": [".epub", ".mobi", ".azw", ".azw3"],
    },
    "Audio": {
        "Music": [".mp3", ".flac", ".ogg", ".wav", ".wma", ".m4a", ".aac", ".opus"],
        "Podcasts": [".m4b"],
        "VoiceMemos": [".amr", ".3ga"],
    },
    "Pics": {
        "Photos": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".heic", ".webp", ".avif", ".jxl"],
        "Vector": [".svg", ".ai", ".eps"],
        "Raw": [".cr2", ".nef", ".dng", ".arw", ".raw"],
        "Icons": [".ico"],
    },
    "Vids": {
        "Movies": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
        "Clips": [".3gp", ".m4v"],
    },
    "Programs": {
        "Windows": [".exe", ".msi", ".dll", ".bat", ".cmd"],
        "Mac": [".dmg", ".pkg", ".app"],
        "Linux": [".deb", ".rpm", ".appimage", ".snap"],
        "Android": [".apk", ".apkm", ".xapk"],
    },
    "Code": {
        "Web": [".html", ".htm", ".css", ".js", ".jsx", ".ts", ".tsx", ".vue", ".mjs", ".wasm"],
        "Python": [".py", ".pyw", ".pyx", ".ipynb"],
        "C": [".c", ".h", ".cpp", ".hpp", ".cc", ".cxx"],
        "Shell": [".sh", ".bash", ".zsh", ".fish"],
        "Java": [".java", ".jar", ".class"],
        "Go": [".go", ".mod", ".sum"],
        "Ruby": [".rb", ".rake"],
        "PHP": [".php"],
        "Rust": [".rs", ".toml"],
        "Swift": [".swift"],
        "Kotlin": [".kt", ".kts"],
        "Zig": [".zig"],
    },
    "Archives": {
        "Compressed": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".lz", ".lzma"],
        "Disk": [".iso", ".img", ".dmg"],
    },
    "System": {
        "Images": [".iso", ".img"],
        "Models": [".gguf", ".bin", ".pt", ".pth", ".onnx"],
        "Libraries": [".dll", ".so", ".dylib"],
        "Cabinets": [".cab"],
        "Fonts": [".ttf", ".otf", ".woff", ".woff2"],
    },
    "Apps": {
        "Ableton": [".asd", ".alc", ".als"],
        "SPSS": [".sav", ".sps"],
        "Gameboy": [".gbc", ".gba", ".gb"],
        "OfficeThemes": [".thmx"],
        "Calendar": [".ics"],
        "Database": [".db", ".sqlite", ".sqlite3", ".mdb", ".accdb"],
    },
    "Web": {
        "Images": [".webp"],
        "Documents": [".htm"],
        "Links": [".url", ".webloc"],
        "Data": [".json", ".xml", ".yaml", ".yml"],
    },
    "Misc": {
        "Temporary": [".crdownload", ".tmp", ".temp", ".cache"],
        "Generic": [".xml", ".dat"],
        "Unsorted": [],  # Catch-all for unclassified files
    },
}


@dataclass
class Config:
    """Configuration for allsorted operations."""

    # Classification rules
    classification_rules: Dict[str, Dict[str, List[str]]] = field(
        default_factory=lambda: DEFAULT_CLASSIFICATION_RULES.copy()
    )

    # Organization settings
    strategy: OrganizationStrategy = OrganizationStrategy.BY_EXTENSION
    conflict_resolution: ConflictResolution = ConflictResolution.RENAME

    # File handling
    follow_symlinks: bool = False
    ignore_hidden: bool = True
    ignore_patterns: List[str] = field(default_factory=lambda: ["**/.devAI/**", "**/.git/**", "**/node_modules/**", "**/__pycache__/**"])

    # Duplicate handling
    detect_duplicates: bool = True
    isolate_duplicates: bool = True

    # Performance
    hash_algorithm: str = "sha256"  # Options: sha256 (secure), xxhash (fast)
    hash_block_size: int = 65536  # 64KB blocks for hashing
    parallel_processing: bool = False
    max_workers: int = 4  # Number of parallel workers
    use_async: bool = False  # Use async I/O for better performance

    # Safety
    require_confirmation: bool = False
    create_backup: bool = False
    verify_integrity: bool = False  # Verify file hash after moving

    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_directory: str = ".devAI"

    # Directories
    directory_prefix: str = "all_"  # Prefix for all created directories
    duplicates_folder: str = "Duplicates"
    folders_folder: str = "Folders"

    # Metadata-based organization
    use_metadata: bool = False  # Enable metadata extraction
    metadata_strategy: str = "auto"  # Options: auto, exif-date, id3-artist, etc.
    perceptual_dedup: bool = False  # Enable perceptual duplicate detection
    perceptual_threshold: int = 5  # Similarity threshold (0-10)

    # Magic number classification
    use_magic: bool = False  # Use file content detection instead of extension

    # Watch mode
    watch_interval: float = 1.0  # Seconds between file system checks
    watch_recursive: bool = True  # Watch subdirectories
    watch_auto_organize: bool = True  # Automatically organize new files

    # Archive handling
    scan_archives: bool = False  # Scan inside archive files
    auto_extract: bool = False  # Auto-extract archives before organizing

    # Size thresholds for by-size strategy (in MB)
    size_thresholds: Dict[str, int] = field(default_factory=lambda: {
        "small_max": 1,
        "medium_min": 1,
        "medium_max": 100,
        "large_min": 100,
    })

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """
        Create Config from dictionary.

        Args:
            data: Dictionary of configuration values

        Returns:
            Config instance
        """
        # Handle enum conversions
        if "strategy" in data and isinstance(data["strategy"], str):
            data["strategy"] = OrganizationStrategy(data["strategy"])
        if "conflict_resolution" in data and isinstance(data["conflict_resolution"], str):
            data["conflict_resolution"] = ConflictResolution(data["conflict_resolution"])

        # Handle nested classification rules
        if "classification_rules" in data:
            rules = DEFAULT_CLASSIFICATION_RULES.copy()
            rules.update(data["classification_rules"])
            data["classification_rules"] = rules

        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Config to dictionary.

        Returns:
            Dictionary representation
        """
        result: Dict[str, Any] = {}
        for key, value in self.__dict__.items():
            if isinstance(value, (OrganizationStrategy, ConflictResolution)):
                result[key] = value.value
            else:
                result[key] = value
        return result

    def get_category_for_extension(self, extension: str) -> tuple[str, str]:
        """
        Get category and subcategory for a file extension.

        Args:
            extension: File extension (with or without dot)

        Returns:
            Tuple of (category, subcategory)
        """
        if not extension.startswith("."):
            extension = f".{extension}"
        extension = extension.lower()

        for category, subcategories in self.classification_rules.items():
            for subcategory, extensions in subcategories.items():
                if extension in extensions:
                    return (category, subcategory)

        return ("Misc", "Unsorted")

    def add_classification_rule(
        self, category: str, subcategory: str, extensions: List[str]
    ) -> None:
        """
        Add or update a classification rule.

        Args:
            category: Top-level category
            subcategory: Subcategory within the category
            extensions: List of file extensions (with dots)
        """
        if category not in self.classification_rules:
            self.classification_rules[category] = {}
        self.classification_rules[category][subcategory] = extensions

    def get_all_categories(self) -> List[str]:
        """
        Get list of all top-level categories.

        Returns:
            List of category names
        """
        return list(self.classification_rules.keys())

    def is_managed_directory(self, path: Path) -> bool:
        """
        Check if a directory was created by allsorted (has the prefix).

        Args:
            path: Path to check

        Returns:
            True if directory has the allsorted prefix
        """
        return path.name.startswith(self.directory_prefix)

    def get_managed_name(self, base_name: str) -> str:
        """
        Get the managed directory name with prefix.

        Args:
            base_name: Base directory name

        Returns:
            Prefixed directory name
        """
        return f"{self.directory_prefix}{base_name}"


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from YAML file, falling back to defaults.

    Args:
        config_path: Path to config file. If None, checks default locations.

    Returns:
        Config instance
    """
    default_config = Config()

    # If no path specified, try default locations
    if config_path is None:
        possible_paths = [
            Path.home() / ".config" / "allsorted" / "config.yaml",
            Path.home() / ".allsorted.yaml",
            Path.cwd() / ".allsorted.yaml",
        ]
        config_path = next((p for p in possible_paths if p.exists()), None)

    if config_path is None or not config_path.exists():
        return default_config

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
            if data is None:
                return default_config
            return Config.from_dict(data)
    except (yaml.YAMLError, OSError, ValueError) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not load config from {config_path}: {e}")
        logger.info("Using default configuration.")
        return default_config


def save_config(config: Config, config_path: Path) -> None:
    """
    Save configuration to YAML file.

    Args:
        config: Config instance to save
        config_path: Path where to save the config

    Raises:
        OSError: If file cannot be written
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.safe_dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)


def get_default_config_path() -> Path:
    """
    Get the default configuration file path.

    Returns:
        Path to default config location
    """
    config_dir = Path.home() / ".config" / "allsorted"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.yaml"
