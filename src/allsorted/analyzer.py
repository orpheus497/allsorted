"""
File analysis and duplicate detection for allsorted.
"""

import hashlib
import logging
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Dict, List, Optional

try:
    import xxhash

    XXHASH_AVAILABLE = True
except ImportError:
    XXHASH_AVAILABLE = False

try:
    import aiofiles

    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

try:
    import imagehash
    from PIL import Image

    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False

from allsorted.config import Config
from allsorted.models import DuplicateSet, FileInfo
from allsorted.utils import is_hidden

logger = logging.getLogger(__name__)

# Image extensions for perceptual hashing
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".heic"}


class FileAnalyzer:
    """Analyzes directories to identify files and duplicates."""

    def __init__(self, config: Config):
        """
        Initialize file analyzer.

        Args:
            config: Configuration instance
        """
        self.config = config
        self.files_by_hash: Dict[str, List[FileInfo]] = defaultdict(list)
        self.all_files: List[FileInfo] = []
        self.ignored_files: List[Path] = []
        self.directories: List[Path] = []
        self.errors: List[tuple[Path, str]] = []
        # Track perceptual hashes for image duplicate detection
        self.perceptual_hashes: Dict[str, List[FileInfo]] = defaultdict(list)

    def analyze_directory(
        self,
        root_dir: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """
        Analyze a directory and all its contents.

        Args:
            root_dir: Root directory to analyze
            progress_callback: Optional callback function(current, total) for progress updates

        Raises:
            ValueError: If root_dir doesn't exist or isn't a directory
        """
        if not root_dir.exists():
            raise ValueError(f"Directory does not exist: {root_dir}")
        if not root_dir.is_dir():
            raise ValueError(f"Path is not a directory: {root_dir}")

        logger.info(f"Starting analysis of directory: {root_dir}")

        # First pass: count files
        file_paths = self._collect_file_paths(root_dir)
        total_files = len(file_paths)
        logger.info(f"Found {total_files} files to analyze")

        # Second pass: analyze each file
        for idx, file_path in enumerate(file_paths, 1):
            if progress_callback:
                progress_callback(idx, total_files)

            try:
                file_info = self._analyze_file(file_path)
                if file_info:
                    self.all_files.append(file_info)
                    self.files_by_hash[file_info.hash].append(file_info)
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
                self.errors.append((file_path, str(e)))

        logger.info(
            f"Analysis complete. Processed {len(self.all_files)} files, "
            f"ignored {len(self.ignored_files)}, "
            f"errors {len(self.errors)}"
        )

    def _collect_file_paths(self, root_dir: Path) -> List[Path]:
        """
        Collect all file paths that should be analyzed.
        Only scans current directory, but recursively scans managed (all_*) directories.

        Args:
            root_dir: Root directory to scan

        Returns:
            List of file paths to analyze
        """
        file_paths: List[Path] = []

        # Only iterate through items in the current directory (not recursive)
        for path in root_dir.iterdir():
            # Handle directories
            if path.is_dir():
                if self._should_ignore_path(path, root_dir):
                    logger.debug(f"Ignoring directory: {path}")
                    continue

                # If it's a managed directory (starts with all_), scan it recursively
                if self.config.is_managed_directory(path):
                    logger.debug(f"Scanning managed directory recursively: {path}")
                    file_paths.extend(self._collect_from_managed_dir(path, root_dir))
                else:
                    # Track non-managed directories for moving to Folders
                    self.directories.append(path)
                    logger.debug(f"Found directory to organize: {path}")
                continue

            # Handle files
            if path.is_file():
                if self._should_ignore_path(path, root_dir):
                    self.ignored_files.append(path)
                    logger.debug(f"Ignoring file: {path}")
                    continue

                # Skip symlinks if configured
                if path.is_symlink() and not self.config.follow_symlinks:
                    self.ignored_files.append(path)
                    logger.debug(f"Skipping symlink: {path}")
                    continue

                file_paths.append(path)

        return file_paths

    def _collect_from_managed_dir(self, managed_dir: Path, root_dir: Path) -> List[Path]:
        """
        Recursively collect files from a managed directory.

        Args:
            managed_dir: Managed directory to scan
            root_dir: Root directory (for ignore patterns)

        Returns:
            List of file paths
        """
        file_paths: List[Path] = []

        for path in managed_dir.rglob("*"):
            # Skip directories
            if path.is_dir():
                continue

            # Check if file should be ignored
            if path.is_file():
                if self._should_ignore_path(path, root_dir):
                    self.ignored_files.append(path)
                    logger.debug(f"Ignoring file in managed dir: {path}")
                    continue

                # Skip symlinks if configured
                if path.is_symlink() and not self.config.follow_symlinks:
                    self.ignored_files.append(path)
                    logger.debug(f"Skipping symlink in managed dir: {path}")
                    continue

                file_paths.append(path)

        return file_paths

    def _should_ignore_path(self, path: Path, root_dir: Path) -> bool:
        """
        Check if a path should be ignored based on configuration.

        Args:
            path: Path to check
            root_dir: Root directory being analyzed

        Returns:
            True if path should be ignored
        """
        # Check hidden files/directories
        if self.config.ignore_hidden and is_hidden(path):
            return True

        # Check ignore patterns
        for pattern in self.config.ignore_patterns:
            # Use Path.match() for proper glob pattern support (including **)
            try:
                if path.match(pattern):
                    return True
                # Also check just the filename for simple patterns
                if Path(path.name).match(pattern):
                    return True
                # Check relative path for directory patterns
                relative_path = path.relative_to(root_dir)
                if relative_path.match(pattern):
                    return True
            except ValueError:
                # If match fails, fall back to simple name comparison
                if path.name == pattern:
                    return True

        return False

    def _analyze_file(self, file_path: Path) -> Optional[FileInfo]:
        """
        Analyze a single file.

        Args:
            file_path: Path to file

        Returns:
            FileInfo instance or None if file cannot be analyzed

        Raises:
            OSError: If file cannot be read
        """
        try:
            stat = file_path.stat()

            # Calculate hash
            file_hash = self._calculate_hash(file_path)
            if file_hash is None:
                return None

            return FileInfo(
                path=file_path,
                size_bytes=stat.st_size,
                hash=file_hash,
                modified_time=stat.st_mtime,
                is_symlink=file_path.is_symlink(),
            )

        except OSError as e:
            logger.warning(f"Cannot access file {file_path}: {e}")
            raise

    def analyze_single_file(self, file_path: Path) -> Optional[FileInfo]:
        """
        Analyze a single file (public API).

        This is the public method for analyzing individual files, useful for
        watch mode and other single-file operations.

        Args:
            file_path: Path to file to analyze

        Returns:
            FileInfo instance or None if file cannot be analyzed
        """
        return self._analyze_file(file_path)

    def _calculate_hash(self, file_path: Path) -> Optional[str]:
        """
        Calculate hash of a file using configured algorithm.

        Supports SHA256 (cryptographically secure) and xxHash (fast).

        Args:
            file_path: Path to file

        Returns:
            Hex digest of hash or None if file cannot be read
        """
        algorithm = self.config.hash_algorithm

        # Initialize hasher based on algorithm
        if algorithm == "xxhash":
            if not XXHASH_AVAILABLE:
                logger.warning(
                    "xxhash not available, falling back to sha256. "
                    "Install with: pip install xxhash"
                )
                hasher = hashlib.sha256()
            else:
                hasher = xxhash.xxh64()
        elif algorithm == "sha256":
            hasher = hashlib.sha256()
        else:
            logger.warning(f"Unknown hash algorithm '{algorithm}', using sha256")
            hasher = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                while True:
                    block = f.read(self.config.hash_block_size)
                    if not block:
                        break
                    hasher.update(block)

            return hasher.hexdigest()

        except OSError as e:
            logger.warning(f"Cannot read file {file_path} for hashing: {e}")
            return None

    async def _calculate_hash_async(self, file_path: Path) -> Optional[str]:
        """
        Calculate hash of a file asynchronously using aiofiles.

        This provides better performance for network paths and I/O-bound operations.

        Args:
            file_path: Path to file

        Returns:
            Hex digest of hash or None if file cannot be read
        """
        if not AIOFILES_AVAILABLE:
            logger.debug("aiofiles not available, using sync hash calculation")
            return self._calculate_hash(file_path)

        algorithm = self.config.hash_algorithm

        # Initialize hasher based on algorithm
        if algorithm == "xxhash":
            if not XXHASH_AVAILABLE:
                hasher = hashlib.sha256()
            else:
                hasher = xxhash.xxh64()
        elif algorithm == "sha256":
            hasher = hashlib.sha256()
        else:
            hasher = hashlib.sha256()

        try:
            async with aiofiles.open(file_path, "rb") as f:
                while True:
                    block = await f.read(self.config.hash_block_size)
                    if not block:
                        break
                    hasher.update(block)

            return hasher.hexdigest()

        except OSError as e:
            logger.warning(f"Cannot read file {file_path} for async hashing: {e}")
            return None

    def _calculate_hash_parallel(self, file_paths: List[Path]) -> Dict[Path, Optional[str]]:
        """
        Calculate hashes for multiple files in parallel using process pool.

        This utilizes multiple CPU cores for faster processing of many files.

        Args:
            file_paths: List of file paths to hash

        Returns:
            Dictionary mapping file paths to their hashes
        """
        if not self.config.parallel_processing or len(file_paths) < 2:
            # Fall back to sequential processing
            return {fp: self._calculate_hash(fp) for fp in file_paths}

        max_workers = getattr(self.config, "max_workers", 4)
        logger.info(f"Hashing {len(file_paths)} files in parallel with {max_workers} workers")

        results: Dict[Path, Optional[str]] = {}

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all hash jobs
            future_to_path = {
                executor.submit(
                    self._hash_file_worker,
                    fp,
                    self.config.hash_algorithm,
                    self.config.hash_block_size,
                ): fp
                for fp in file_paths
            }

            # Collect results as they complete
            for future in as_completed(future_to_path):
                file_path = future_to_path[future]
                try:
                    file_hash = future.result()
                    results[file_path] = file_hash
                except Exception as e:
                    logger.error(f"Parallel hashing failed for {file_path}: {e}")
                    results[file_path] = None

        logger.info(f"Parallel hashing complete: {len(results)} files processed")
        return results

    @staticmethod
    def _hash_file_worker(file_path: Path, algorithm: str, block_size: int) -> Optional[str]:
        """
        Worker function for parallel hashing (must be static for multiprocessing).

        Args:
            file_path: Path to file
            algorithm: Hash algorithm to use
            block_size: Block size for reading

        Returns:
            Hex digest of hash or None if error
        """
        # Initialize hasher
        if algorithm == "xxhash":
            try:
                import xxhash

                hasher = xxhash.xxh64()
            except ImportError:
                hasher = hashlib.sha256()
        else:
            hasher = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                while True:
                    block = f.read(block_size)
                    if not block:
                        break
                    hasher.update(block)

            return hasher.hexdigest()

        except OSError:
            return None

    def _calculate_perceptual_hash(self, file_path: Path) -> Optional[str]:
        """
        Calculate perceptual hash of an image file for visual similarity detection.

        This allows detection of visually similar images even if they have
        different sizes, compressions, or minor modifications.

        Args:
            file_path: Path to image file

        Returns:
            Hex string of perceptual hash or None if not an image or error
        """
        if not IMAGEHASH_AVAILABLE:
            return None

        # Only process image files
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            return None

        try:
            with Image.open(file_path) as img:
                # Use average hash (fast and effective)
                phash = imagehash.average_hash(img)
                return str(phash)
        except Exception as e:
            logger.debug(f"Could not calculate perceptual hash for {file_path}: {e}")
            return None

    def _find_perceptual_duplicates(self) -> List[DuplicateSet]:
        """
        Find visually similar images using perceptual hashing.

        Returns:
            List of DuplicateSet instances for perceptually similar images
        """
        if not IMAGEHASH_AVAILABLE:
            logger.warning(
                "Perceptual duplicate detection requested but imagehash not available. "
                "Install with: pip install imagehash"
            )
            return []

        threshold = self.config.perceptual_threshold
        logger.info(f"Finding perceptual duplicates with threshold {threshold}")

        # Calculate perceptual hashes for all image files
        image_hashes: Dict[str, List[FileInfo]] = defaultdict(list)

        for file_info in self.all_files:
            if file_info.extension.lower() in IMAGE_EXTENSIONS:
                phash = self._calculate_perceptual_hash(file_info.path)
                if phash:
                    image_hashes[phash].append(file_info)

        # Find groups of similar images
        duplicate_sets = []
        processed_hashes: set = set()

        for phash, files in image_hashes.items():
            if phash in processed_hashes:
                continue

            # Find all similar hashes
            similar_files = list(files)

            for other_hash, other_files in image_hashes.items():
                if other_hash == phash or other_hash in processed_hashes:
                    continue

                try:
                    # Calculate hash distance
                    hash1 = imagehash.hex_to_hash(phash)
                    hash2 = imagehash.hex_to_hash(other_hash)
                    distance = hash1 - hash2

                    if distance <= threshold:
                        similar_files.extend(other_files)
                        processed_hashes.add(other_hash)
                except Exception as e:
                    logger.debug(f"Error comparing hashes: {e}")

            processed_hashes.add(phash)

            if len(similar_files) > 1:
                try:
                    duplicate_set = DuplicateSet(
                        hash=f"perceptual_{phash}",
                        files=similar_files
                    )
                    duplicate_sets.append(duplicate_set)
                except ValueError as e:
                    logger.warning(f"Error creating perceptual duplicate set: {e}")

        logger.info(f"Found {len(duplicate_sets)} sets of perceptually similar images")
        return duplicate_sets

    def get_duplicate_sets(self) -> List[DuplicateSet]:
        """
        Get all sets of duplicate files.
        Includes both content-based and perceptual duplicates if enabled.

        Returns:
            List of DuplicateSet instances
        """
        if not self.config.detect_duplicates:
            return []

        duplicate_sets = []

        # Content-based duplicates (exact match)
        for file_hash, files in self.files_by_hash.items():
            if len(files) > 1:
                try:
                    duplicate_set = DuplicateSet(hash=file_hash, files=files)
                    duplicate_sets.append(duplicate_set)
                except ValueError as e:
                    logger.warning(f"Error creating duplicate set for hash {file_hash}: {e}")

        # Perceptual duplicates (visually similar images) if enabled
        if self.config.perceptual_dedup:
            perceptual_dups = self._find_perceptual_duplicates()
            duplicate_sets.extend(perceptual_dups)

        logger.info(f"Found {len(duplicate_sets)} sets of duplicate files")
        return duplicate_sets

    def get_unique_files(self) -> List[FileInfo]:
        """
        Get all files that have no duplicates.

        Returns:
            List of FileInfo instances
        """
        unique_files = []
        for file_hash, files in self.files_by_hash.items():
            if len(files) == 1:
                unique_files.append(files[0])

        return unique_files

    def get_total_files(self) -> int:
        """
        Get total number of files analyzed.

        Returns:
            Number of files
        """
        return len(self.all_files)

    def get_total_size(self) -> int:
        """
        Get total size of all analyzed files in bytes.

        Returns:
            Total size in bytes
        """
        return sum(f.size_bytes for f in self.all_files)

    def get_duplicate_waste(self) -> int:
        """
        Calculate total space wasted by duplicate files.

        Returns:
            Total wasted bytes
        """
        total_waste = 0
        for files in self.files_by_hash.values():
            if len(files) > 1:
                file_size = files[0].size_bytes
                total_waste += file_size * (len(files) - 1)

        return total_waste

    def reset(self) -> None:
        """Reset the analyzer to process a new directory."""
        self.files_by_hash.clear()
        self.all_files.clear()
        self.ignored_files.clear()
        self.directories.clear()
        self.errors.clear()
        self.perceptual_hashes.clear()
