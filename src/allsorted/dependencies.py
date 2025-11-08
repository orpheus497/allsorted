"""
Dependency availability checking and user warnings for allsorted.

This module provides centralized checking for optional dependencies and
clear user-facing warnings when features are requested but dependencies are missing.

Created by orpheus497
"""

import logging
import sys
from typing import Dict, List, Tuple

from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


# Dependency availability flags (set on module import)
PYTHON_MAGIC_AVAILABLE = False
PILLOW_AVAILABLE = False
MUTAGEN_AVAILABLE = False
WATCHDOG_AVAILABLE = False
IMAGEHASH_AVAILABLE = False
AIOFILES_AVAILABLE = False
XXHASH_AVAILABLE = False

# Check dependencies on import
try:
    import magic  # noqa: F401

    PYTHON_MAGIC_AVAILABLE = True
except ImportError:
    pass

try:
    from PIL import Image  # noqa: F401

    PILLOW_AVAILABLE = True
except ImportError:
    pass

try:
    import mutagen  # noqa: F401

    MUTAGEN_AVAILABLE = True
except ImportError:
    pass

try:
    from watchdog.observers import Observer  # noqa: F401

    WATCHDOG_AVAILABLE = True
except ImportError:
    pass

try:
    import imagehash  # noqa: F401

    IMAGEHASH_AVAILABLE = True
except ImportError:
    pass

try:
    import aiofiles  # noqa: F401

    AIOFILES_AVAILABLE = True
except ImportError:
    pass

try:
    import xxhash  # noqa: F401

    XXHASH_AVAILABLE = True
except ImportError:
    pass


def check_all_dependencies() -> Tuple[List[str], List[str]]:
    """
    Check which optional dependencies are available.

    Returns:
        Tuple of (available, missing) dependency names
    """
    dependencies: Dict[str, bool] = {
        "python-magic": PYTHON_MAGIC_AVAILABLE,
        "Pillow": PILLOW_AVAILABLE,
        "mutagen": MUTAGEN_AVAILABLE,
        "watchdog": WATCHDOG_AVAILABLE,
        "imagehash": IMAGEHASH_AVAILABLE,
        "aiofiles": AIOFILES_AVAILABLE,
        "xxhash": XXHASH_AVAILABLE,
    }

    available = [name for name, is_available in dependencies.items() if is_available]
    missing = [name for name, is_available in dependencies.items() if not is_available]

    return available, missing


def print_dependency_status() -> None:
    """Print status of all optional dependencies to console."""
    available, missing = check_all_dependencies()

    console.print("\n[bold cyan]Optional Dependency Status:[/bold cyan]")

    if available:
        console.print("\n[bold green]Available:[/bold green]")
        for dep in available:
            console.print(f"  ✓ {dep}")

    if missing:
        console.print("\n[bold yellow]Missing (features will be disabled):[/bold yellow]")
        for dep in missing:
            console.print(f"  ✗ {dep}")

    console.print("\n[dim]Install all optional dependencies with:[/dim]")
    console.print("[dim]  pip install allsorted[full][/dim]\n")


def warn_if_feature_unavailable(feature: str, show_warning: bool = True) -> bool:
    """
    Check if a feature is available and warn user if dependencies are missing.

    Args:
        feature: Feature name to check
        show_warning: Whether to show warning message to user

    Returns:
        True if feature is available, False otherwise
    """
    feature_deps: Dict[str, Tuple[bool, str, str]] = {
        "magic": (
            PYTHON_MAGIC_AVAILABLE,
            "python-magic",
            "Magic file classification (content-based type detection)",
        ),
        "metadata": (
            PILLOW_AVAILABLE and MUTAGEN_AVAILABLE,
            "Pillow and mutagen",
            "Metadata extraction (EXIF, ID3 tags)",
        ),
        "exif": (PILLOW_AVAILABLE, "Pillow", "EXIF data extraction from images"),
        "id3": (MUTAGEN_AVAILABLE, "mutagen", "ID3 tag extraction from audio files"),
        "watch": (WATCHDOG_AVAILABLE, "watchdog", "File system watch mode"),
        "perceptual": (
            IMAGEHASH_AVAILABLE,
            "imagehash",
            "Perceptual duplicate detection for images",
        ),
        "async": (AIOFILES_AVAILABLE, "aiofiles", "Async file I/O"),
        "xxhash": (XXHASH_AVAILABLE, "xxhash", "Fast xxHash algorithm"),
    }

    if feature not in feature_deps:
        logger.warning(f"Unknown feature check: {feature}")
        return False

    available, dep_name, feature_desc = feature_deps[feature]

    if not available and show_warning:
        console.print(
            f"[yellow]Warning:[/yellow] {feature_desc} requires {dep_name}.\n"
            f"Install with: [cyan]pip install {dep_name}[/cyan]\n"
            f"Feature will be disabled.\n"
        )
        logger.warning(f"{feature_desc} unavailable - {dep_name} not installed")

    return available


def require_dependency(feature: str, dependency_name: str) -> None:
    """
    Require a dependency for a feature or exit with error.

    Args:
        feature: Feature name requiring the dependency
        dependency_name: Name of the required dependency

    Raises:
        SystemExit: If dependency is not available
    """
    available = warn_if_feature_unavailable(feature, show_warning=False)

    if not available:
        console.print(
            f"[bold red]Error:[/bold red] {feature} requires {dependency_name}.\n"
            f"Install with: [cyan]pip install {dependency_name}[/cyan]\n"
        )
        sys.exit(1)


def get_missing_dependencies_for_config(config: "Config") -> List[str]:  # type: ignore[name-defined]
    """
    Get list of missing dependencies based on enabled config options.

    Args:
        config: Configuration instance

    Returns:
        List of missing dependency names
    """
    missing = []

    if config.use_magic and not PYTHON_MAGIC_AVAILABLE:
        missing.append("python-magic")

    if config.use_metadata:
        if not PILLOW_AVAILABLE:
            missing.append("Pillow")
        if not MUTAGEN_AVAILABLE:
            missing.append("mutagen")

    if config.perceptual_dedup and not IMAGEHASH_AVAILABLE:
        missing.append("imagehash")

    if config.use_async and not AIOFILES_AVAILABLE:
        missing.append("aiofiles")

    if config.hash_algorithm == "xxhash" and not XXHASH_AVAILABLE:
        missing.append("xxhash")

    return missing


def warn_about_config_dependencies(config: "Config") -> None:  # type: ignore[name-defined]
    """
    Warn user about any missing dependencies for enabled config options.

    Args:
        config: Configuration instance
    """
    missing = get_missing_dependencies_for_config(config)

    if missing:
        console.print("\n[bold yellow]Configuration Warning:[/bold yellow]")
        console.print("The following features are enabled but dependencies are missing:\n")
        for dep in missing:
            console.print(f"  ✗ {dep}")

        console.print("\n[dim]Install missing dependencies with:[/dim]")
        for dep in missing:
            console.print(f"[dim]  pip install {dep}[/dim]")
        console.print()
