"""
Utility functions for allsorted.
"""

import os
from pathlib import Path
from typing import Optional


def format_size(bytes_count: int) -> str:
    """
    Format byte count into human-readable string.

    Args:
        bytes_count: Number of bytes

    Returns:
        Formatted string (e.g., "1.5 MB", "3.2 GB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2.5s", "1m 30s", "1h 5m")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def safe_path_resolve(path: Path, base_dir: Optional[Path] = None) -> Path:
    """
    Safely resolve a path, handling symlinks and relative paths with validation.

    Args:
        path: Path to resolve
        base_dir: Base directory to validate against (defaults to cwd)

    Returns:
        Resolved absolute path

    Raises:
        ValueError: If path contains suspicious patterns or escapes base directory
    """
    try:
        # Resolve the path fully
        resolved = path.resolve(strict=False)

        # If symlink, validate the target
        if path.is_symlink():
            try:
                # Ensure symlink doesn't create a loop
                target = path.readlink()
                if target.is_absolute():
                    # Absolute symlinks must point within base_dir
                    if base_dir and not str(target).startswith(str(base_dir.resolve())):
                        raise ValueError(f"Symlink points outside base directory: {path}")
            except (OSError, RuntimeError) as e:
                raise ValueError(f"Invalid symlink: {path}") from e

        # Validate against base directory if provided
        if base_dir:
            try:
                base_resolved = base_dir.resolve()
                resolved.relative_to(base_resolved)
            except ValueError:
                raise ValueError(
                    f"Path escapes base directory: {path} -> {resolved} (base: {base_dir})"
                )

        return resolved
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Cannot resolve path {path}: {e}") from e


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent log injection and filesystem issues.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for logging and filesystem operations
    """
    # First, replace problematic characters
    replacements = {
        "\n": "_",
        "\r": "_",
        "\t": "_",
        "\x00": "",
    }

    sanitized = filename
    for old, new in replacements.items():
        sanitized = sanitized.replace(old, new)

    # Then remove any remaining control characters
    sanitized = "".join(char for char in sanitized if ord(char) >= 32 or char in ("\t",))

    return sanitized


def is_hidden(path: Path) -> bool:
    """
    Check if a path is hidden (starts with dot on Unix, has hidden attribute on Windows).

    Args:
        path: Path to check

    Returns:
        True if hidden, False otherwise
    """
    # Unix-style hidden files
    if path.name.startswith("."):
        return True

    # Windows hidden attribute
    if os.name == "nt":
        try:
            import ctypes

            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            return bool(attrs & 2)  # FILE_ATTRIBUTE_HIDDEN = 2
        except (AttributeError, OSError):
            pass

    return False


def ensure_dir(path: Path) -> None:
    """
    Ensure a directory exists, creating it and parents if necessary.

    Args:
        path: Directory path to create

    Raises:
        OSError: If directory cannot be created
    """
    path.mkdir(parents=True, exist_ok=True)


def get_unique_path(path: Path) -> Path:
    """
    Get a unique file path by appending numbers if the file exists.

    Args:
        path: Desired path

    Returns:
        Unique path (may be the same as input if it doesn't exist)

    Example:
        /path/to/file.txt -> /path/to/file_1.txt if file.txt exists
    """
    if not path.exists():
        return path

    counter = 1
    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def calculate_directory_size(directory: Path) -> int:
    """
    Calculate total size of all files in a directory recursively.

    Args:
        directory: Directory to measure

    Returns:
        Total size in bytes
    """
    total = 0
    try:
        for entry in directory.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except OSError:
                    pass  # Skip files we can't access
    except OSError:
        pass  # Directory might be inaccessible

    return total


def get_available_space(path: Path) -> int:
    """
    Get available disk space for a given path.

    Args:
        path: Path to check

    Returns:
        Available bytes on the filesystem
    """
    import shutil

    stat = shutil.disk_usage(path)
    return stat.free


def is_same_filesystem(path1: Path, path2: Path) -> bool:
    """
    Check if two paths are on the same filesystem.

    Args:
        path1: First path
        path2: Second path

    Returns:
        True if on same filesystem, False otherwise
    """
    try:
        return path1.stat().st_dev == path2.stat().st_dev
    except OSError:
        return False


def truncate_path(path: Path, max_length: int = 80) -> str:
    """
    Truncate a path string to fit within max_length by abbreviating middle parts.

    Args:
        path: Path to truncate
        max_length: Maximum length of output string

    Returns:
        Truncated path string with ... in the middle if needed
    """
    path_str = str(path)
    if len(path_str) <= max_length:
        return path_str

    # Calculate how much space we have for each end
    ellipsis = "..."
    available = max_length - len(ellipsis)
    start_len = available // 2
    end_len = available - start_len

    return f"{path_str[:start_len]}{ellipsis}{path_str[-end_len:]}"
