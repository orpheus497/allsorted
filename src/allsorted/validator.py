"""
Validation and safety checks for allsorted operations.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from allsorted.models import MoveOperation, OrganizationPlan
from allsorted.utils import get_available_space

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class OperationValidator:
    """Validates operations before execution for safety."""

    def __init__(self, plan: OrganizationPlan):
        """
        Initialize validator.

        Args:
            plan: Organization plan to validate
        """
        self.plan = plan
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validation checks.

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors.clear()
        self.warnings.clear()

        # Run all validation checks
        self._validate_root_directory()
        self._validate_disk_space()
        self._validate_permissions()
        self._validate_no_circular_dependencies()
        self._validate_no_overwrites()
        self._validate_source_files_exist()

        is_valid = len(self.errors) == 0
        return (is_valid, self.errors.copy(), self.warnings.copy())

    def _validate_root_directory(self) -> None:
        """Validate that root directory exists and is accessible."""
        if not self.plan.root_dir.exists():
            self.errors.append(f"Root directory does not exist: {self.plan.root_dir}")
            return

        if not self.plan.root_dir.is_dir():
            self.errors.append(f"Root path is not a directory: {self.plan.root_dir}")
            return

        try:
            # Try to list directory to check permissions
            list(self.plan.root_dir.iterdir())
        except PermissionError:
            self.errors.append(f"No permission to access root directory: {self.plan.root_dir}")
        except OSError as e:
            self.errors.append(f"Error accessing root directory: {e}")

    def _validate_disk_space(self) -> None:
        """Validate sufficient disk space for operations."""
        if not self.plan.operations:
            return

        try:
            available_bytes = get_available_space(self.plan.root_dir)
            required_bytes = self._estimate_required_space()

            if required_bytes > available_bytes:
                self.errors.append(
                    f"Insufficient disk space. "
                    f"Required: {required_bytes / (1024**3):.2f} GB, "
                    f"Available: {available_bytes / (1024**3):.2f} GB"
                )
            elif required_bytes > available_bytes * 0.9:
                self.warnings.append(
                    f"Disk space is tight. "
                    f"Operation will use {(required_bytes / available_bytes * 100):.1f}% "
                    f"of available space."
                )

        except OSError as e:
            self.warnings.append(f"Could not check disk space: {e}")

    def _estimate_required_space(self) -> int:
        """
        Estimate required disk space for operations.

        Returns:
            Estimated bytes needed (conservative estimate)
        """
        # For moves on same filesystem, no extra space needed
        # For moves across filesystems, need space for all files
        # We'll assume worst case (different filesystem) and add 10% buffer

        total_size = sum(op.file_info.size_bytes for op in self.plan.operations)
        return int(total_size * 0.1)  # 10% buffer for metadata and safety

    def _validate_permissions(self) -> None:
        """Validate write permissions for all destination directories."""
        # Get unique destination directories
        dest_dirs = {op.destination.parent for op in self.plan.operations}

        for dest_dir in dest_dirs:
            # Check if directory exists
            if dest_dir.exists():
                # Check write permission
                if not self._check_write_permission(dest_dir):
                    self.errors.append(f"No write permission for directory: {dest_dir}")
            else:
                # Check if we can create it (check parent permission)
                parent = dest_dir.parent
                while not parent.exists() and parent != parent.parent:
                    parent = parent.parent

                if parent.exists() and not self._check_write_permission(parent):
                    self.errors.append(f"No permission to create directory: {dest_dir}")

    def _check_write_permission(self, directory: Path) -> bool:
        """
        Check if we have write permission for a directory.

        Args:
            directory: Directory to check

        Returns:
            True if writable
        """
        try:
            # Try to create a temporary file
            test_file = directory / ".allsorted_test_write"
            test_file.touch()
            test_file.unlink()
            return True
        except (PermissionError, OSError):
            return False

    def _validate_no_circular_dependencies(self) -> None:
        """Validate no operation moves a file to a subdirectory of itself."""
        for op in self.plan.operations:
            source_resolved = op.source.resolve()
            dest_resolved = op.destination.resolve()

            # Check if destination is under source
            try:
                dest_resolved.relative_to(source_resolved)
                self.errors.append(
                    f"Circular dependency detected: "
                    f"Cannot move {source_resolved} into its own subdirectory"
                )
            except ValueError:
                # relative_to raises ValueError if not relative - that's good
                pass

            # Check for symlink loops
            if op.file_info.is_symlink:
                try:
                    # Resolve symlink fully
                    _ = source_resolved.resolve(strict=True)
                except (RuntimeError, OSError):
                    self.warnings.append(f"Potential symlink loop detected: {op.source}")

    def _validate_no_overwrites(self) -> None:
        """Validate that no operation will overwrite an existing file unexpectedly."""
        # Track destination paths to detect conflicts within the plan
        destinations: dict[Path, MoveOperation] = {}

        for op in self.plan.operations:
            dest = op.destination.resolve()

            # Check if destination exists and is not the source
            if dest.exists() and dest != op.source.resolve():
                self.warnings.append(
                    f"File will be renamed due to existing file: "
                    f"{op.destination} (resolution: {op.conflict_resolution.value})"
                )

            # Check for conflicts within the plan itself
            if dest in destinations:
                previous_op = destinations[dest]
                self.errors.append(
                    f"Multiple operations target same destination: {dest}\n"
                    f"  Source 1: {previous_op.source}\n"
                    f"  Source 2: {op.source}"
                )
            else:
                destinations[dest] = op

    def _validate_source_files_exist(self) -> None:
        """Validate that all source files exist."""
        for op in self.plan.operations:
            if not op.source.exists():
                self.errors.append(f"Source file does not exist: {op.source}")
            elif not op.source.is_file():
                self.errors.append(f"Source is not a file: {op.source}")

    def get_summary(self) -> str:
        """
        Get a summary of validation results.

        Returns:
            Human-readable summary string
        """
        lines = ["Validation Summary:"]
        lines.append(f"  Total operations: {len(self.plan.operations)}")
        lines.append(f"  Errors: {len(self.errors)}")
        lines.append(f"  Warnings: {len(self.warnings)}")

        if self.errors:
            lines.append("\nErrors:")
            for error in self.errors:
                lines.append(f"  ❌ {error}")

        if self.warnings:
            lines.append("\nWarnings:")
            for warning in self.warnings:
                lines.append(f"  ⚠️  {warning}")

        if not self.errors and not self.warnings:
            lines.append("  ✅ All checks passed")

        return "\n".join(lines)
