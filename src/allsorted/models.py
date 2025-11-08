"""
Data models for allsorted using dataclasses for type safety and validation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Set


class ConflictResolution(Enum):
    """Strategy for resolving file name conflicts."""

    RENAME = "rename"  # Rename with incrementing number
    SKIP = "skip"  # Skip the conflicting file
    OVERWRITE = "overwrite"  # Overwrite existing file
    ASK = "ask"  # Prompt user for decision


class OrganizationStrategy(Enum):
    """Strategy for organizing files."""

    BY_EXTENSION = "by-extension"  # Organize by file extension (default)
    BY_DATE = "by-date"  # Organize by modification date (YYYY/MM/DD)
    BY_SIZE = "by-size"  # Organize by file size categories
    HYBRID = "hybrid"  # Combine extension and date


@dataclass
class FileInfo:
    """Information about a single file."""

    path: Path
    size_bytes: int
    hash: str
    modified_time: float
    is_symlink: bool = False

    @property
    def size_mb(self) -> float:
        """File size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        """File size in gigabytes."""
        return self.size_bytes / (1024 * 1024 * 1024)

    @property
    def extension(self) -> str:
        """File extension (lowercase, including dot)."""
        return self.path.suffix.lower()

    @property
    def name(self) -> str:
        """File name without path."""
        return self.path.name

    def __eq__(self, other: object) -> bool:
        """Files are equal if they have the same hash."""
        if not isinstance(other, FileInfo):
            return NotImplemented
        return self.hash == other.hash

    def __hash__(self) -> int:
        """Hash based on file content hash."""
        return hash(self.hash)

    def __repr__(self) -> str:
        """String representation."""
        return f"FileInfo(path={self.path}, size={self.size_mb:.2f}MB, hash={self.hash[:8]}...)"


@dataclass
class DuplicateSet:
    """A set of duplicate files (same content hash)."""

    hash: str
    files: List[FileInfo]
    primary: Optional[FileInfo] = None

    def __post_init__(self) -> None:
        """Validate and select primary file after initialization."""
        if not self.files:
            raise ValueError("DuplicateSet must contain at least one file")
        if self.primary is None:
            self.primary = self._select_primary()

    def _select_primary(self) -> FileInfo:
        """
        Select the primary file to keep based on:
        1. Shortest path (fewer nested directories)
        2. Oldest modification time (tie-breaker)
        """
        return min(
            self.files,
            key=lambda f: (len(str(f.path)), f.modified_time),
        )

    @property
    def extras(self) -> List[FileInfo]:
        """All duplicate files except the primary."""
        return [f for f in self.files if f != self.primary]

    @property
    def count(self) -> int:
        """Total number of duplicate files."""
        return len(self.files)

    @property
    def space_wasted(self) -> int:
        """Bytes wasted by duplicates (size * (count - 1))."""
        if not self.files:
            return 0
        return self.files[0].size_bytes * (len(self.files) - 1)

    def __repr__(self) -> str:
        """String representation."""
        return f"DuplicateSet(hash={self.hash[:8]}..., count={self.count}, primary={self.primary})"


@dataclass
class MoveOperation:
    """A single file move operation."""

    source: Path
    destination: Path
    file_info: FileInfo
    reason: str  # "classify", "duplicate", "organize_folder"
    conflict_resolution: ConflictResolution = ConflictResolution.RENAME

    @property
    def is_duplicate(self) -> bool:
        """Whether this operation moves a duplicate file."""
        return self.reason == "duplicate"

    @property
    def is_classification(self) -> bool:
        """Whether this operation is for classification."""
        return self.reason == "classify"

    def __repr__(self) -> str:
        """String representation."""
        return f"MoveOperation({self.source} -> {self.destination}, reason={self.reason})"


@dataclass
class DirectoryMoveOperation:
    """A single directory move operation."""

    source: Path
    destination: Path
    reason: str = "organize_folder"
    conflict_resolution: ConflictResolution = ConflictResolution.RENAME

    def __repr__(self) -> str:
        """String representation."""
        return f"DirectoryMoveOperation({self.source} -> {self.destination})"


@dataclass
class OrganizationPlan:
    """Complete plan for organizing a directory."""

    root_dir: Path
    operations: List[MoveOperation] = field(default_factory=list)
    directory_operations: List[DirectoryMoveOperation] = field(default_factory=list)
    duplicate_sets: List[DuplicateSet] = field(default_factory=list)
    skipped_files: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)

    @property
    def total_files(self) -> int:
        """Total number of files to be processed."""
        return len(self.operations)

    @property
    def total_duplicates(self) -> int:
        """Total number of duplicate files found."""
        return sum(ds.count - 1 for ds in self.duplicate_sets)

    @property
    def space_recoverable(self) -> int:
        """Total bytes that could be saved by removing duplicates."""
        return sum(ds.space_wasted for ds in self.duplicate_sets)

    @property
    def categories_used(self) -> Set[str]:
        """Set of categories that will be created."""
        categories = set()
        for op in self.operations:
            if op.destination.parent != self.root_dir:
                categories.add(op.destination.parent.name)
        return categories

    def add_operation(self, operation: MoveOperation) -> None:
        """Add a move operation to the plan."""
        self.operations.append(operation)

    def add_directory_operation(self, operation: DirectoryMoveOperation) -> None:
        """Add a directory move operation to the plan."""
        self.directory_operations.append(operation)

    def add_error(self, error: str) -> None:
        """Add an error message to the plan."""
        self.errors.append(error)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"OrganizationPlan(root={self.root_dir}, "
            f"operations={len(self.operations)}, "
            f"duplicates={self.total_duplicates})"
        )


@dataclass
class OrganizationResult:
    """Results after executing an organization plan."""

    plan: OrganizationPlan
    successful_operations: List[MoveOperation] = field(default_factory=list)
    failed_operations: List[tuple[MoveOperation, str]] = field(default_factory=list)
    directories_created: List[Path] = field(default_factory=list)
    directories_removed: List[Path] = field(default_factory=list)
    started: Optional[datetime] = None
    completed: Optional[datetime] = None
    dry_run: bool = False

    @property
    def success_rate(self) -> float:
        """Percentage of successful operations."""
        total = len(self.successful_operations) + len(self.failed_operations)
        if total == 0:
            return 100.0
        return (len(self.successful_operations) / total) * 100

    @property
    def duration_seconds(self) -> float:
        """Duration of the operation in seconds."""
        if self.started and self.completed:
            return (self.completed - self.started).total_seconds()
        return 0.0

    @property
    def files_moved(self) -> int:
        """Number of files successfully moved."""
        return len(self.successful_operations)

    @property
    def files_failed(self) -> int:
        """Number of files that failed to move."""
        return len(self.failed_operations)

    @property
    def is_complete_success(self) -> bool:
        """Whether all operations succeeded."""
        return len(self.failed_operations) == 0

    def __repr__(self) -> str:
        """String representation."""
        status = "DRY RUN" if self.dry_run else "EXECUTED"
        return (
            f"OrganizationResult({status}, "
            f"success={self.files_moved}, "
            f"failed={self.files_failed}, "
            f"success_rate={self.success_rate:.1f}%)"
        )
